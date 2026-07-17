from __future__ import annotations

import asyncio
import hashlib
import hmac
import inspect
import json
import math
import os
import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping

from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError

from models import AdminActionIntent, AdminAudit, Node, User, UserNode
from node_policy import canonical_free_node_code, node_is_free, user_uses_free_pool
from nodes_repo import enabled_nodes
from ru_probe_contract import canonical_json_bytes


ACTION_INTENT_TTL = timedelta(minutes=10)
EXTERNAL_EXECUTION_TIMEOUT_SECONDS = 30.0
EXTERNAL_EXECUTION_STALE_AFTER = timedelta(minutes=5)
# Signed int32 representation of the stable "POKR" lock namespace. The same
# value is embedded in the PostgreSQL user_nodes trigger migration.
NODE_MAPPING_LOCK_NAMESPACE = 1_347_373_906
_HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TARGET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_EXTERNAL_RESULT_CODE_RE = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")
_TERMINAL_STATUSES = frozenset({"completed", "failed", "uncertain"})
_EXTERNAL_RESULT_KEYS = frozenset(
    {"ok", "code", "count", "changed", "failed", "skipped", "job_id"}
)
_EXTERNAL_COUNT_KEYS = ("count", "changed", "failed", "skipped")
_MAX_EXTERNAL_COUNT = 1_000_000
_MAX_EXTERNAL_REFERENCE_LENGTH = 128
_constant_time_compare = hmac.compare_digest


class ActionIntentError(RuntimeError):
    def __init__(
        self,
        code: str,
        *,
        status_code: int,
        message: str,
        intent_id: str | None = None,
        audit_id: int | None = None,
    ) -> None:
        self.code = code
        self.status_code = int(status_code)
        self.message = message
        self.intent_id = str(intent_id) if intent_id else None
        self.audit_id = int(audit_id) if audit_id is not None else None
        super().__init__(code)


@dataclass(frozen=True)
class EntityState:
    entity: Any
    version_snapshot: dict[str, Any]
    public_snapshot: dict[str, Any]
    context: dict[str, Any]


@dataclass(frozen=True)
class ExternalOutcome:
    status: str
    result: dict[str, Any]
    external_error_hash: str | None = None


PayloadNormalizer = Callable[[Mapping[str, Any]], dict[str, Any]]
EntityStateBuilder = Callable[[Any, str, Mapping[str, Any], bool], EntityState]
PreviewBuilder = Callable[[EntityState, Mapping[str, Any]], dict[str, Any]]
ChallengeBuilder = Callable[[EntityState, Mapping[str, Any]], str]
DbExecutor = Callable[[Any, EntityState, Mapping[str, Any]], dict[str, Any]]
ExternalContextBuilder = Callable[[EntityState, Mapping[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class ActionPolicy:
    action: str
    target_type: str
    risk_level: str
    payload_normalizer: PayloadNormalizer
    entity_state_builder: EntityStateBuilder
    preview_builder: PreviewBuilder
    challenge_kind: str
    challenge_builder: ChallengeBuilder
    executor_kind: str
    audit_action: str
    db_executor: DbExecutor | None = None
    external_context_builder: ExternalContextBuilder | None = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _canonical_json(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _semantic_hash(domain: str, value: object) -> str:
    payload = canonical_json_bytes(value)
    return hashlib.sha256(
        f"POKROV:{domain}:v1\n".encode("ascii") + payload
    ).hexdigest()


def confirmation_sha256(value: str) -> str:
    normalized = unicodedata.normalize("NFC", str(value or "")).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def node_resync_recipient_fingerprint(
    *,
    tg_id: int,
    mapping_client_uuid: str,
    mapping_panel_email: str,
    user_uuid: str,
    user_email: str,
    sub_id: str,
) -> str:
    return _semantic_hash(
        "admin-node-resync-recipient",
        {
            "tg_id": int(tg_id),
            "mapping_client_uuid": str(mapping_client_uuid or ""),
            "mapping_panel_email": str(mapping_panel_email or ""),
            "user_uuid": str(user_uuid or ""),
            "user_email": str(user_email or ""),
            "sub_id": str(sub_id or ""),
        },
    )


def _normalize_uuid(value: str, *, code: str) -> str:
    raw = str(value or "").strip().lower()
    try:
        parsed = str(uuid.UUID(raw))
    except (ValueError, AttributeError, TypeError):
        raise ActionIntentError(
            code,
            status_code=422,
            message="Нужен корректный UUID.",
        ) from None
    if parsed != raw:
        raise ActionIntentError(
            code,
            status_code=422,
            message="Нужен UUID в каноническом формате.",
        )
    return parsed


def _normalize_execution_identifiers(
    *,
    session_factory,
    actor_tg_id: int,
    intent_id: str,
    idempotency_key: str,
) -> tuple[str, str]:
    normalized_intent_id = _normalize_uuid(intent_id, code="invalid_intent_id")
    try:
        normalized_idempotency_key = _normalize_uuid(
            idempotency_key,
            code="invalid_idempotency_key",
        )
    except ActionIntentError as error:
        owned_intent_id, audit_id = action_intent_error_identifiers(
            session_factory=session_factory,
            actor_tg_id=actor_tg_id,
            intent_id=normalized_intent_id,
        )
        error.intent_id = owned_intent_id
        error.audit_id = audit_id
        raise
    return normalized_intent_id, normalized_idempotency_key


def action_intent_error_identifiers(
    *,
    session_factory,
    actor_tg_id: int,
    intent_id: str,
) -> tuple[str | None, int | None]:
    """Return only a canonical attempted ID and an actor-owned linked audit ID."""
    try:
        normalized_intent_id = _normalize_uuid(
            intent_id,
            code="invalid_intent_id",
        )
    except ActionIntentError:
        return None, None

    try:
        session = session_factory()
    except Exception:
        return None, None
    result: tuple[str | None, int | None] = (None, None)
    try:
        row = (
            session.query(
                AdminActionIntent.id,
                AdminActionIntent.admin_audit_id,
            )
            .filter(
                AdminActionIntent.id == normalized_intent_id,
                AdminActionIntent.actor_tg_id == int(actor_tg_id),
            )
            .first()
        )
        if row is not None:
            result = (
                str(row[0]),
                int(row[1]) if row[1] is not None else None,
            )
    except Exception:
        try:
            if session.in_transaction():
                session.rollback()
        except Exception:
            pass
        result = (None, None)
    try:
        session.close()
    except Exception:
        return None, None
    return result


def _loaded_action_intent_error_identifiers(
    intent: AdminActionIntent | None,
    *,
    actor_tg_id: int,
) -> tuple[str | None, int | None]:
    try:
        if intent is None or int(intent.actor_tg_id) != int(actor_tg_id):
            return None, None
        return (
            str(intent.id),
            int(intent.admin_audit_id)
            if intent.admin_audit_id is not None
            else None,
        )
    except Exception:
        return None, None


def _normalize_target(
    target: Mapping[str, Any],
    *,
    expected_type: str | None = None,
) -> dict[str, str]:
    target_type = str(target.get("type") or "").strip().lower()
    target_id = str(target.get("id") or "").strip().lower()
    if (
        not target_type
        or not target_id
        or not _TARGET_ID_RE.fullmatch(target_id)
        or (expected_type is not None and target_type != expected_type)
    ):
        raise ActionIntentError(
            "invalid_target",
            status_code=422,
            message="Цель действия указана неверно.",
        )
    return {"type": target_type, "id": target_id}


def _normalize_node_lifecycle_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if set(payload) - {"force"}:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Тело запроса содержит неподдерживаемые поля.",
        )
    force = payload.get("force", False)
    if not isinstance(force, bool):
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Поле force должно быть логическим значением.",
        )
    return {"force": force}


def _normalize_node_resync_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if set(payload) - {"limit", "dry_run"}:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Тело запроса содержит неподдерживаемые поля.",
        )
    limit = payload.get("limit", 100)
    dry_run = payload.get("dry_run", False)
    if type(limit) is not int or not 1 <= int(limit) <= 1000:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Поле limit должно быть целым числом от 1 до 1000.",
        )
    if not isinstance(dry_run, bool):
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Поле dry_run должно быть логическим значением.",
        )
    return {"dry_run": bool(dry_run), "limit": int(limit)}


def _node_entity_state(
    session,
    target_id: str,
    _payload: Mapping[str, Any],
    for_update: bool,
) -> EntityState:
    dialect = str(session.get_bind().dialect.name)
    node = None
    if for_update and dialect == "postgresql":
        node_id = (
            session.query(Node.id)
            .filter(func.lower(Node.code) == target_id)
            .scalar()
        )
        if node_id is not None:
            session.execute(
                text(
                    "SELECT pg_advisory_xact_lock(:lock_namespace, :node_id)"
                ),
                {
                    "lock_namespace": NODE_MAPPING_LOCK_NAMESPACE,
                    "node_id": int(node_id),
                },
            )
            node = (
                session.query(Node)
                .filter(
                    Node.id == int(node_id),
                    func.lower(Node.code) == target_id,
                )
                .with_for_update()
                .first()
            )
    else:
        node = (
            session.query(Node)
            .filter(func.lower(Node.code) == target_id)
            .first()
        )
    if node is None:
        raise ActionIntentError(
            "target_not_found",
            status_code=404,
            message="Нода не найдена.",
        )
    mapped_users = int(
        session.query(func.count(func.distinct(UserNode.tg_id)))
        .filter(UserNode.node_id == int(node.id))
        .scalar()
        or 0
    )
    lifecycle = {
        "enabled": bool(node.enabled),
        "accepting_new_clients": bool(node.accepting_new_clients),
        "is_draining": bool(node.is_draining),
    }
    public_snapshot = {
        "code": str(node.code or target_id).strip().upper(),
        "name": str(node.name or node.code or target_id).strip()[:100],
        **lifecycle,
        "mapped_users": mapped_users,
    }
    version_snapshot = {
        "node_id": int(node.id),
        "code": str(node.code or target_id).strip().lower(),
        **lifecycle,
        "mapped_users": mapped_users,
    }
    return EntityState(
        entity=node,
        version_snapshot=version_snapshot,
        public_snapshot=public_snapshot,
        context={"mapped_users": mapped_users},
    )


def _node_code_base(code: str) -> str:
    normalized = str(code or "").strip().lower()
    for separator in ("_", "-", "."):
        if separator in normalized:
            normalized = normalized.split(separator, 1)[0]
    return normalized


def _resync_excluded_codes() -> set[str]:
    return {
        token.strip().lower()
        for token in str(os.getenv("SUBSCRIPTION_EXCLUDE_NODE_CODES", "") or "").split(",")
        if token.strip()
    }


def _resync_node_accepts_new_clients(node: Any) -> bool:
    return (
        bool(getattr(node, "enabled", True))
        and bool(getattr(node, "accepting_new_clients", True))
        and not bool(getattr(node, "is_draining", False))
    )


def _resync_node_allowed_for_plan(
    user: User,
    node: Any,
    *,
    excluded_codes: set[str],
    free_code: str,
) -> bool:
    code = str(getattr(node, "code", "") or "").strip().lower()
    if not code or code in excluded_codes or _node_code_base(code) in excluded_codes:
        return False
    if user_uses_free_pool(user):
        return bool(free_code) and code == free_code
    return not node_is_free(node)


def _resync_fallback_nodes(user: User, nodes: list[Any]) -> list[Any]:
    if not nodes:
        return []
    excluded_codes = _resync_excluded_codes()
    candidate_nodes = [node for node in nodes if _resync_node_accepts_new_clients(node)]
    if not candidate_nodes:
        return []

    if user_uses_free_pool(user):
        free_code = str(
            canonical_free_node_code(candidate_nodes)
            or canonical_free_node_code(nodes)
            or ""
        ).strip().lower()
        pool = [
            node
            for node in candidate_nodes
            if str(getattr(node, "code", "") or "").strip().lower() == free_code
        ]
    else:
        free_code = str(canonical_free_node_code(nodes) or "").strip().lower()
        pool = [node for node in candidate_nodes if not node_is_free(node)]

    filtered = [
        node
        for node in pool
        if _resync_node_allowed_for_plan(
            user,
            node,
            excluded_codes=excluded_codes,
            free_code=free_code,
        )
    ]
    return filtered


def _resync_target_node_codes(
    session,
    user: User,
    source_code: str,
    nodes: list[Any],
) -> list[str]:
    source = str(source_code or "").strip().lower()
    node_by_id = {
        int(getattr(node, "id", 0) or 0): node
        for node in nodes
        if getattr(node, "id", None) is not None
    }
    excluded_codes = _resync_excluded_codes()
    free_code = str(canonical_free_node_code(nodes) or "").strip().lower()
    out: list[str] = []
    seen: set[str] = set()

    mapped_rows = (
        session.query(UserNode)
        .filter(UserNode.tg_id == int(user.tg_id))
        .order_by(UserNode.created_at.asc(), UserNode.id.asc())
        .all()
    )
    for row in mapped_rows:
        node = node_by_id.get(int(getattr(row, "node_id", 0) or 0))
        if (
            node is None
            or not _resync_node_accepts_new_clients(node)
            or not _resync_node_allowed_for_plan(
                user,
                node,
                excluded_codes=excluded_codes,
                free_code=free_code,
            )
        ):
            continue
        code = str(getattr(node, "code", "") or "").strip().lower()
        if not code or code == source or code in seen:
            continue
        seen.add(code)
        out.append(code)

    for node in _resync_fallback_nodes(user, nodes):
        code = str(getattr(node, "code", "") or "").strip().lower()
        if not code or code == source or code in seen:
            continue
        seen.add(code)
        out.append(code)
    return out


def _node_resync_entity_state(
    session,
    target_id: str,
    payload: Mapping[str, Any],
    for_update: bool,
) -> EntityState:
    base = _node_entity_state(session, target_id, payload, for_update)
    query = (
        session.query(UserNode, User)
        .join(User, User.tg_id == UserNode.tg_id)
        .filter(UserNode.node_id == int(base.entity.id))
        .order_by(UserNode.created_at.asc(), UserNode.id.asc())
        .limit(int(payload["limit"]))
    )
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update(of=UserNode)
    rows = query.all()
    candidate_nodes = enabled_nodes(session)
    node_id_by_code = {
        str(getattr(node, "code", "") or "").strip().lower(): int(getattr(node, "id"))
        for node in candidate_nodes
        if getattr(node, "id", None) is not None
        and str(getattr(node, "code", "") or "").strip()
    }
    selection: list[dict[str, Any]] = []
    selection_version: list[dict[str, Any]] = []
    for source_mapping, user in rows:
        target_codes = _resync_target_node_codes(
            session,
            user,
            target_id,
            candidate_nodes,
        )
        target_nodes = [
            {
                "id": node_id_by_code[code],
                "code": code,
            }
            for code in target_codes
            if code in node_id_by_code
        ]
        recipient_fingerprint = node_resync_recipient_fingerprint(
            tg_id=int(user.tg_id),
            mapping_client_uuid=str(source_mapping.client_uuid or ""),
            mapping_panel_email=str(source_mapping.panel_email or ""),
            user_uuid=str(user.uuid or ""),
            user_email=str(user.email or ""),
            sub_id=str(getattr(user, "sub_token", "") or user.tg_id),
        )
        item = {
            "source_user_node_id": int(source_mapping.id),
            "recipient_fingerprint": recipient_fingerprint,
            "target_nodes": target_nodes,
        }
        selection.append(item)
        selection_version.append(
            {
                "source_user_node_id": int(source_mapping.id),
                "recipient_fingerprint": recipient_fingerprint,
                "target_nodes": target_nodes,
            }
        )
    selection_hash = _semantic_hash(
        "admin-node-resync-selection",
        selection_version,
    )
    no_target_count = sum(1 for item in selection if not item["target_nodes"])
    return EntityState(
        entity=base.entity,
        version_snapshot={
            **base.version_snapshot,
            "selection_hash": selection_hash,
            "selection_limit": int(payload["limit"]),
            "selected_count": len(selection),
        },
        public_snapshot=base.public_snapshot,
        context={
            **base.context,
            "resync_selection": selection,
            "selection_hash": selection_hash,
            "selected_count": len(selection),
            "no_target_count": no_target_count,
        },
    )


def _node_disable_preview(
    state: EntityState,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    before = dict(state.public_snapshot)
    after = {
        **before,
        "enabled": False,
        "accepting_new_clients": False,
        "is_draining": False,
    }
    warnings: list[str] = []
    if int(state.context["mapped_users"]) > 0:
        warnings.append(
            "На ноде есть привязанные пользователи; без принудительного режима выполнение будет остановлено."
        )
    if bool(payload["force"]):
        warnings.append("Принудительное отключение может оборвать активные подключения.")
    code = str(before["code"])
    return {
        "title": f"Отключение ноды {code}",
        "summary": f"Будет отключена нода {code}",
        "before": before,
        "after": after,
        "warnings": warnings,
    }


def _node_lifecycle_preview(
    state: EntityState,
    *,
    title: str,
    summary: str,
    lifecycle: Mapping[str, bool],
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    before = dict(state.public_snapshot)
    return {
        "title": title,
        "summary": summary,
        "before": before,
        "after": {**before, **dict(lifecycle)},
        "warnings": list(warnings or []),
    }


def _node_drain_preview(
    state: EntityState,
    _payload: Mapping[str, Any],
) -> dict[str, Any]:
    code = str(state.public_snapshot["code"])
    warnings = []
    if not bool(state.public_snapshot["enabled"]):
        warnings.append("Отключённая нода будет включена в режиме вывода из контура.")
    return _node_lifecycle_preview(
        state,
        title=f"Вывод ноды {code} из контура",
        summary=f"Нода {code} перестанет принимать новых клиентов",
        lifecycle={
            "enabled": True,
            "accepting_new_clients": False,
            "is_draining": True,
        },
        warnings=warnings,
    )


def _node_undrain_preview(
    state: EntityState,
    _payload: Mapping[str, Any],
) -> dict[str, Any]:
    code = str(state.public_snapshot["code"])
    return _node_lifecycle_preview(
        state,
        title=f"Возврат ноды {code} в контур",
        summary=f"Нода {code} снова начнёт принимать новых клиентов",
        lifecycle={
            "enabled": True,
            "accepting_new_clients": True,
            "is_draining": False,
        },
    )


def _node_enable_preview(
    state: EntityState,
    _payload: Mapping[str, Any],
) -> dict[str, Any]:
    code = str(state.public_snapshot["code"])
    return _node_lifecycle_preview(
        state,
        title=f"Включение ноды {code}",
        summary=f"Нода {code} будет включена и начнёт принимать новых клиентов",
        lifecycle={
            "enabled": True,
            "accepting_new_clients": True,
            "is_draining": False,
        },
    )


def _node_resync_preview(
    state: EntityState,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    code = str(state.public_snapshot["code"])
    selected_count = int(state.context["selected_count"])
    no_target_count = int(state.context["no_target_count"])
    warnings: list[str] = []
    if selected_count == 0:
        warnings.append("Для переноса не найдено ни одной локальной привязки.")
    if no_target_count:
        warnings.append(
            f"Для {no_target_count} привязок сейчас нет подходящей целевой ноды."
        )
    if not bool(payload["dry_run"]):
        warnings.append(
            "Внешняя панель будет вызвана один раз; неясный исход нельзя повторять автоматически."
        )
    return {
        "title": f"Перенос клиентов с ноды {code}",
        "summary": f"Будет обработано привязок: {selected_count}",
        "before": {
            "code": code,
            "mapped_users": int(state.context["mapped_users"]),
            "selected_users": selected_count,
        },
        "after": {
            "code": code,
            "planned_moves": selected_count - no_target_count,
            "without_target": no_target_count,
            "dry_run": bool(payload["dry_run"]),
        },
        "warnings": warnings,
        "selection": {
            "count": selected_count,
            "without_target": no_target_count,
            "hash": str(state.context["selection_hash"]),
        },
    }


def _node_challenge(
    state: EntityState,
    _payload: Mapping[str, Any],
) -> str:
    return str(state.public_snapshot["code"]).upper()


def _node_l2_challenge(
    _state: EntityState,
    _payload: Mapping[str, Any],
) -> str:
    return "ПОДТВЕРДИТЬ"


def _node_lifecycle_result(
    state: EntityState,
    *,
    enabled: bool,
    accepting_new_clients: bool,
    is_draining: bool,
) -> dict[str, Any]:
    node = state.entity
    node.enabled = enabled
    node.accepting_new_clients = accepting_new_clients
    node.is_draining = is_draining
    return {
        "node": {
            **state.public_snapshot,
            "enabled": enabled,
            "accepting_new_clients": accepting_new_clients,
            "is_draining": is_draining,
        }
    }


def _execute_node_drain(
    _session,
    state: EntityState,
    _payload: Mapping[str, Any],
) -> dict[str, Any]:
    return _node_lifecycle_result(
        state,
        enabled=True,
        accepting_new_clients=False,
        is_draining=True,
    )


def _execute_node_undrain(
    _session,
    state: EntityState,
    _payload: Mapping[str, Any],
) -> dict[str, Any]:
    return _node_lifecycle_result(
        state,
        enabled=True,
        accepting_new_clients=True,
        is_draining=False,
    )


def _execute_node_enable(
    _session,
    state: EntityState,
    _payload: Mapping[str, Any],
) -> dict[str, Any]:
    return _node_lifecycle_result(
        state,
        enabled=True,
        accepting_new_clients=True,
        is_draining=False,
    )


def _execute_node_disable(
    _session,
    state: EntityState,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    mapped_users = int(state.context["mapped_users"])
    if mapped_users > 0 and not bool(payload["force"]):
        raise ActionIntentError(
            "node_has_mapped_users",
            status_code=409,
            message="Сначала перенесите пользователей или подтвердите принудительное отключение.",
        )
    return _node_lifecycle_result(
        state,
        enabled=False,
        accepting_new_clients=False,
        is_draining=False,
    )


def _node_resync_external_context(
    state: EntityState,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "source_node_id": int(state.entity.id),
        "source_node_code": str(state.entity.code or "").strip().lower(),
        "selection": [dict(item) for item in state.context["resync_selection"]],
        "selection_hash": str(state.context["selection_hash"]),
        "dry_run": bool(payload["dry_run"]),
    }


ACTION_POLICIES: dict[str, ActionPolicy] = {
    "node.drain": ActionPolicy(
        action="node.drain",
        target_type="node",
        risk_level="L2",
        payload_normalizer=_normalize_node_lifecycle_payload,
        entity_state_builder=_node_entity_state,
        preview_builder=_node_drain_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_node_l2_challenge,
        executor_kind="db",
        audit_action="admin_node_drain",
        db_executor=_execute_node_drain,
    ),
    "node.undrain": ActionPolicy(
        action="node.undrain",
        target_type="node",
        risk_level="L2",
        payload_normalizer=_normalize_node_lifecycle_payload,
        entity_state_builder=_node_entity_state,
        preview_builder=_node_undrain_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_node_l2_challenge,
        executor_kind="db",
        audit_action="admin_node_undrain",
        db_executor=_execute_node_undrain,
    ),
    "node.enable": ActionPolicy(
        action="node.enable",
        target_type="node",
        risk_level="L2",
        payload_normalizer=_normalize_node_lifecycle_payload,
        entity_state_builder=_node_entity_state,
        preview_builder=_node_enable_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_node_l2_challenge,
        executor_kind="db",
        audit_action="admin_node_enable",
        db_executor=_execute_node_enable,
    ),
    "node.resync": ActionPolicy(
        action="node.resync",
        target_type="node",
        risk_level="L2",
        payload_normalizer=_normalize_node_resync_payload,
        entity_state_builder=_node_resync_entity_state,
        preview_builder=_node_resync_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_node_l2_challenge,
        executor_kind="external",
        audit_action="admin_node_resync",
        external_context_builder=_node_resync_external_context,
    ),
    "node.disable": ActionPolicy(
        action="node.disable",
        target_type="node",
        risk_level="L3",
        payload_normalizer=_normalize_node_lifecycle_payload,
        entity_state_builder=_node_entity_state,
        preview_builder=_node_disable_preview,
        challenge_kind="exact_node_code",
        challenge_builder=_node_challenge,
        executor_kind="db",
        audit_action="admin_node_disable",
        db_executor=_execute_node_disable,
    )
}


def _policy_for(action: str) -> ActionPolicy:
    normalized = str(action or "").strip().lower()
    policy = ACTION_POLICIES.get(normalized)
    if policy is None:
        raise ActionIntentError(
            "unknown_action",
            status_code=422,
            message="Действие не входит в серверный allowlist.",
        )
    return policy


def _payload_hash(payload: Mapping[str, Any]) -> str:
    return _semantic_hash("admin-action-payload", payload)


def _snapshot_hash(snapshot: Mapping[str, Any]) -> str:
    return _semantic_hash("admin-action-preview", snapshot)


def _entity_version_hash(
    policy: ActionPolicy,
    target: Mapping[str, str],
    state: EntityState,
) -> str:
    return _semantic_hash(
        "admin-action-entity-version",
        {
            "action": policy.action,
            "target": dict(target),
            "entity": state.version_snapshot,
        },
    )


def prepare_action_intent(
    *,
    session,
    actor_tg_id: int,
    action: str,
    target: Mapping[str, Any],
    payload: Mapping[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    policy = _policy_for(action)
    normalized_target = _normalize_target(target, expected_type=policy.target_type)
    normalized_payload = policy.payload_normalizer(payload)
    state = policy.entity_state_builder(
        session,
        normalized_target["id"],
        normalized_payload,
        False,
    )
    preview = policy.preview_builder(state, normalized_payload)
    challenge = policy.challenge_builder(state, normalized_payload)
    prepared_at = _as_utc(now or _utcnow())
    expires_at = prepared_at + ACTION_INTENT_TTL
    intent_id = str(uuid.uuid4())
    payload_hash = _payload_hash(normalized_payload)
    snapshot_hash = _snapshot_hash(preview)
    version_hash = _entity_version_hash(policy, normalized_target, state)
    row = AdminActionIntent(
        id=intent_id,
        actor_tg_id=int(actor_tg_id),
        action=policy.action,
        target_type=normalized_target["type"],
        target_id=normalized_target["id"],
        risk_level=policy.risk_level,
        executor_kind=policy.executor_kind,
        canonical_payload_json=_canonical_json(normalized_payload),
        payload_hash=payload_hash,
        preview_snapshot_json=_canonical_json(preview),
        snapshot_hash=snapshot_hash,
        confirmation_challenge_kind=policy.challenge_kind,
        confirmation_challenge_hash=confirmation_sha256(challenge),
        entity_version_hash=version_hash,
        status="prepared",
        expires_at=expires_at,
        created_at=prepared_at,
        updated_at=prepared_at,
    )
    session.add(row)
    session.flush()
    return {
        "ok": True,
        "intent_id": intent_id,
        "action": policy.action,
        "target": normalized_target,
        "risk_level": policy.risk_level,
        "preview": preview,
        "payload_hash": payload_hash,
        "snapshot_hash": snapshot_hash,
        "entity_version_hash": version_hash,
        "confirmation_challenge": challenge,
        "confirmation_challenge_kind": policy.challenge_kind,
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
    }


def _begin_write_lock(session) -> None:
    if str(session.get_bind().dialect.name) == "sqlite":
        session.execute(text("BEGIN IMMEDIATE"))


def _locked_intent(session, intent_id: str) -> AdminActionIntent | None:
    query = session.query(AdminActionIntent).filter(AdminActionIntent.id == intent_id)
    if str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    return query.first()


def _stored_result(intent: AdminActionIntent) -> dict[str, Any]:
    if intent.result_summary_json:
        try:
            value = json.loads(intent.result_summary_json)
            if isinstance(value, dict):
                return value
        except (TypeError, ValueError):
            pass
    return {
        "ok": intent.status == "completed",
        "status": str(intent.status),
        "action_intent_id": str(intent.id),
        "audit_id": int(intent.admin_audit_id) if intent.admin_audit_id else None,
    }


def _verify_confirmation(intent: AdminActionIntent, supplied_hash: str) -> None:
    supplied = str(supplied_hash or "").strip()
    candidate = supplied if _HEX_SHA256_RE.fullmatch(supplied) else "0" * 64
    matches = _constant_time_compare(str(intent.confirmation_challenge_hash), candidate)
    if not matches or candidate != supplied:
        raise ActionIntentError(
            "confirmation_mismatch",
            status_code=409,
            message="Подтверждение не совпало с серверным challenge.",
        )


def _audit_meta(
    intent: AdminActionIntent,
    state: EntityState,
    payload: Mapping[str, Any],
    *,
    outcome: str,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "action_intent_id": str(intent.id),
        "risk_level": str(intent.risk_level),
        "target_type": str(intent.target_type),
        "target_id": str(intent.target_id),
        "payload_hash": str(intent.payload_hash),
        "snapshot_hash": str(intent.snapshot_hash),
        "entity_version_hash": str(intent.entity_version_hash),
        "mapped_users": int(state.context.get("mapped_users") or 0),
        "forced": bool(payload.get("force", False)),
        "outcome": outcome,
    }
    selection_hash = state.context.get("selection_hash")
    if isinstance(selection_hash, str) and _HEX_SHA256_RE.fullmatch(selection_hash):
        meta.update(
            {
                "selection_hash": selection_hash,
                "selected_count": int(state.context.get("selected_count") or 0),
                "no_target_count": int(state.context.get("no_target_count") or 0),
                "limit": int(payload.get("limit") or 0),
                "dry_run": bool(payload.get("dry_run", False)),
            }
        )
    return meta


def _validate_execution(
    *,
    session,
    intent: AdminActionIntent,
    actor_tg_id: int,
    action: str,
    target: Mapping[str, Any],
    payload: Mapping[str, Any],
    idempotency_key: str,
    confirmation_sha256_header: str,
    now: datetime,
) -> tuple[ActionPolicy, dict[str, str], dict[str, Any], EntityState | None, dict[str, Any] | None]:
    if int(intent.actor_tg_id) != int(actor_tg_id) or str(intent.action) != str(action).strip().lower():
        raise ActionIntentError(
            "intent_mismatch",
            status_code=409,
            message="Намерение выпущено для другого оператора или другой команды.",
        )
    policy = _policy_for(intent.action)
    normalized_target = _normalize_target(target, expected_type=policy.target_type)
    if (
        normalized_target["type"] != str(intent.target_type)
        or normalized_target["id"] != str(intent.target_id)
    ):
        raise ActionIntentError(
            "intent_mismatch",
            status_code=409,
            message="Intent выпущен для другой цели.",
        )
    normalized_payload = policy.payload_normalizer(payload)
    if _payload_hash(normalized_payload) != str(intent.payload_hash):
        raise ActionIntentError(
            "intent_mismatch",
            status_code=409,
            message="Payload изменился после preview.",
        )
    _verify_confirmation(intent, confirmation_sha256_header)

    if intent.client_idempotency_key == idempotency_key:
        if intent.status in _TERMINAL_STATUSES or intent.status == "executing":
            return policy, normalized_target, normalized_payload, None, _stored_result(intent)
    elif intent.client_idempotency_key is not None or intent.status in _TERMINAL_STATUSES or intent.status == "executing":
        raise ActionIntentError(
            "intent_consumed",
            status_code=409,
            message="Intent уже использован с другим idempotency key.",
        )

    if intent.status == "expired" or _as_utc(intent.expires_at) <= now:
        intent.status = "expired"
        intent.updated_at = now
        session.commit()
        raise ActionIntentError(
            "expired_intent",
            status_code=409,
            message="Срок действия preview истёк; создайте новый intent.",
        )
    if intent.status != "prepared":
        raise ActionIntentError(
            "intent_consumed",
            status_code=409,
            message="Intent уже использован.",
        )

    state = policy.entity_state_builder(
        session,
        normalized_target["id"],
        normalized_payload,
        True,
    )
    live_version = _entity_version_hash(policy, normalized_target, state)
    if live_version != str(intent.entity_version_hash):
        raise ActionIntentError(
            "stale_intent",
            status_code=409,
            message="Состояние сущности изменилось после preview.",
        )
    return policy, normalized_target, normalized_payload, state, None


def _read_idempotency_owner(session, idempotency_key: str) -> AdminActionIntent | None:
    query = session.query(AdminActionIntent).filter(
        AdminActionIntent.client_idempotency_key == idempotency_key
    )
    if str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    return query.first()


def _external_error_fingerprint(code: str, value: object | None = None) -> str:
    shape: dict[str, Any] = {"code": str(code)[:64]}
    if isinstance(value, BaseException):
        try:
            message = str(value)[:512]
        except Exception:
            message = "<unprintable>"
        shape.update(
            {
                "exception_type": type(value).__name__[:64],
                "message_hash": hashlib.sha256(message.encode("utf-8")).hexdigest(),
            }
        )
    elif value is not None:
        shape["value_type"] = type(value).__name__[:64]
        if isinstance(value, Mapping):
            try:
                bounded_keys: list[str] = []
                for index, key in enumerate(value.keys()):
                    if index >= 16:
                        break
                    bounded_keys.append(
                        key[:64]
                        if isinstance(key, str)
                        else f"<{type(key).__name__}>"
                    )
                shape["keys"] = sorted(bounded_keys)
            except Exception:
                shape["keys"] = ["<unreadable>"]
    return _semantic_hash("admin-action-external-error", shape)


def _terminal_external_result(
    *,
    status: str,
    result_code: str,
    intent_id: str,
    audit_id: int,
    facts: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": status == "completed",
        "status": status,
        "result_code": result_code,
        "action_intent_id": intent_id,
        "audit_id": int(audit_id),
    }
    if facts:
        result["result"] = dict(facts)
    return result


def _malformed_external_outcome(
    *,
    raw_result: object,
    intent_id: str,
    audit_id: int,
) -> ExternalOutcome:
    result = _terminal_external_result(
        status="uncertain",
        result_code="external_result_malformed",
        intent_id=intent_id,
        audit_id=audit_id,
    )
    return ExternalOutcome(
        status="uncertain",
        result=result,
        external_error_hash=_external_error_fingerprint(
            "external_result_malformed",
            raw_result,
        ),
    )


def _normalize_external_outcome(
    *,
    raw_result: object,
    intent_id: str,
    audit_id: int,
) -> ExternalOutcome:
    try:
        if not isinstance(raw_result, Mapping):
            return _malformed_external_outcome(
                raw_result=raw_result,
                intent_id=intent_id,
                audit_id=audit_id,
            )
        if len(raw_result) > len(_EXTERNAL_RESULT_KEYS):
            return _malformed_external_outcome(
                raw_result=raw_result,
                intent_id=intent_id,
                audit_id=audit_id,
            )
        keys = list(raw_result.keys())
        if (
            any(not isinstance(key, str) for key in keys)
            or set(keys) - _EXTERNAL_RESULT_KEYS
            or type(raw_result.get("ok")) is not bool
        ):
            return _malformed_external_outcome(
                raw_result=raw_result,
                intent_id=intent_id,
                audit_id=audit_id,
            )

        succeeded = bool(raw_result["ok"])
        default_code = "completed" if succeeded else "external_failed"
        raw_code = raw_result.get("code")
        if raw_code is None:
            result_code = default_code
        elif (
            not isinstance(raw_code, str)
            or not 1 <= len(raw_code) <= 64
            or raw_code != raw_code.strip().lower()
            or not _EXTERNAL_RESULT_CODE_RE.fullmatch(raw_code)
        ):
            return _malformed_external_outcome(
                raw_result=raw_result,
                intent_id=intent_id,
                audit_id=audit_id,
            )
        else:
            result_code = raw_code

        facts: dict[str, Any] = {}
        for key in _EXTERNAL_COUNT_KEYS:
            if key not in raw_result:
                continue
            value = raw_result[key]
            if type(value) is not int or not 0 <= value <= _MAX_EXTERNAL_COUNT:
                return _malformed_external_outcome(
                    raw_result=raw_result,
                    intent_id=intent_id,
                    audit_id=audit_id,
                )
            facts[key] = int(value)
        if succeeded and int(facts.get("failed") or 0) > 0:
            return _malformed_external_outcome(
                raw_result=raw_result,
                intent_id=intent_id,
                audit_id=audit_id,
            )

        if "job_id" in raw_result and raw_result["job_id"] is not None:
            reference = raw_result["job_id"]
            if (
                not isinstance(reference, str)
                or not 1 <= len(reference) <= _MAX_EXTERNAL_REFERENCE_LENGTH
            ):
                return _malformed_external_outcome(
                    raw_result=raw_result,
                    intent_id=intent_id,
                    audit_id=audit_id,
                )
            facts["external_reference_hash"] = _semantic_hash(
                "admin-action-external-reference",
                reference,
            )

        status = "completed" if succeeded else "failed"
        return ExternalOutcome(
            status=status,
            result=_terminal_external_result(
                status=status,
                result_code=result_code,
                intent_id=intent_id,
                audit_id=audit_id,
                facts=facts,
            ),
        )
    except Exception as exc:
        result = _terminal_external_result(
            status="uncertain",
            result_code="external_result_malformed",
            intent_id=intent_id,
            audit_id=audit_id,
        )
        return ExternalOutcome(
            status="uncertain",
            result=result,
            external_error_hash=_external_error_fingerprint(
                "external_result_normalization_failed",
                exc,
            ),
        )


def _terminal_audit_meta(
    *,
    audit: AdminAudit,
    outcome: ExternalOutcome,
    result_hash: str,
) -> dict[str, Any]:
    try:
        parsed = json.loads(str(audit.meta or "{}"))
    except (TypeError, ValueError):
        parsed = {}
    source = parsed if isinstance(parsed, dict) else {}
    safe: dict[str, Any] = {}
    string_limits = {
        "action_intent_id": 36,
        "risk_level": 8,
        "target_type": 32,
        "target_id": 128,
        "payload_hash": 64,
        "snapshot_hash": 64,
        "entity_version_hash": 64,
    }
    for key, limit in string_limits.items():
        value = source.get(key)
        if isinstance(value, str) and len(value) <= limit:
            safe[key] = value
    mapped_users = source.get("mapped_users")
    if type(mapped_users) is int and 0 <= mapped_users <= _MAX_EXTERNAL_COUNT:
        safe["mapped_users"] = int(mapped_users)
    if type(source.get("forced")) is bool:
        safe["forced"] = bool(source["forced"])
    selection_hash = source.get("selection_hash")
    if isinstance(selection_hash, str) and _HEX_SHA256_RE.fullmatch(selection_hash):
        safe["selection_hash"] = selection_hash
    for key in ("selected_count", "no_target_count", "limit"):
        value = source.get(key)
        if type(value) is int and 0 <= value <= _MAX_EXTERNAL_COUNT:
            safe[key] = int(value)
    if type(source.get("dry_run")) is bool:
        safe["dry_run"] = bool(source["dry_run"])

    safe.update(
        {
            "outcome": outcome.status,
            "result_code": str(outcome.result["result_code"]),
            "result_hash": result_hash,
        }
    )
    if outcome.external_error_hash:
        safe["external_error_hash"] = outcome.external_error_hash
    facts = outcome.result.get("result")
    if isinstance(facts, dict):
        for key in _EXTERNAL_COUNT_KEYS:
            value = facts.get(key)
            if type(value) is int and 0 <= value <= _MAX_EXTERNAL_COUNT:
                safe[key] = int(value)
        reference_hash = facts.get("external_reference_hash")
        if isinstance(reference_hash, str) and _HEX_SHA256_RE.fullmatch(reference_hash):
            safe["external_reference_hash"] = reference_hash
    return safe


def _apply_external_outcome(
    *,
    session,
    intent: AdminActionIntent,
    outcome: ExternalOutcome,
    updated_at: datetime,
) -> None:
    if outcome.status not in _TERMINAL_STATUSES:
        raise ValueError("external outcome must be terminal")
    result_hash = _semantic_hash("admin-action-result", outcome.result)
    intent.status = outcome.status
    intent.result_code = str(outcome.result["result_code"])
    intent.result_summary_json = _canonical_json(outcome.result)
    intent.result_hash = result_hash
    intent.external_error_hash = outcome.external_error_hash
    intent.updated_at = updated_at

    if intent.admin_audit_id is None:
        return
    query = session.query(AdminAudit).filter(
        AdminAudit.id == int(intent.admin_audit_id)
    )
    if str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    audit = query.first()
    if audit is not None:
        audit.meta = _canonical_json(
            _terminal_audit_meta(
                audit=audit,
                outcome=outcome,
                result_hash=result_hash,
            )
        )


def _reconcile_stale_external_execution(
    *,
    session,
    intent: AdminActionIntent,
    idempotency_key: str,
    now: datetime,
) -> dict[str, Any] | None:
    if (
        intent.status != "executing"
        or intent.client_idempotency_key != idempotency_key
        or intent.admin_audit_id is None
        or _as_utc(intent.updated_at) > now - EXTERNAL_EXECUTION_STALE_AFTER
    ):
        return None
    result = _terminal_external_result(
        status="uncertain",
        result_code="external_execution_stale",
        intent_id=str(intent.id),
        audit_id=int(intent.admin_audit_id),
    )
    outcome = ExternalOutcome(
        status="uncertain",
        result=result,
        external_error_hash=_external_error_fingerprint(
            "external_execution_stale"
        ),
    )
    _apply_external_outcome(
        session=session,
        intent=intent,
        outcome=outcome,
        updated_at=now,
    )
    return result


def _persist_external_outcome(
    *,
    session_factory,
    intent_id: str,
    idempotency_key: str,
    outcome: ExternalOutcome,
) -> dict[str, Any]:
    session = session_factory()
    try:
        _begin_write_lock(session)
        intent = _locked_intent(session, intent_id)
        if intent is None or intent.client_idempotency_key != idempotency_key:
            raise ActionIntentError(
                "intent_consumed",
                status_code=409,
                message="Intent больше не принадлежит этому выполнению.",
                intent_id=intent_id,
                audit_id=(
                    int(intent.admin_audit_id)
                    if intent is not None and intent.admin_audit_id is not None
                    else None
                ),
            )
        if intent.status != "executing":
            stored = _stored_result(intent)
            session.rollback()
            return stored
        _apply_external_outcome(
            session=session,
            intent=intent,
            outcome=outcome,
            updated_at=_utcnow(),
        )
        session.commit()
        return outcome.result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def _invoke_external_executor(external_executor, context: dict[str, Any]) -> Any:
    if inspect.iscoroutinefunction(external_executor):
        value = external_executor(context)
    else:
        value = await asyncio.to_thread(external_executor, context)
    if inspect.isawaitable(value):
        return await value
    return value


def _external_timeout_seconds(value: float) -> float:
    try:
        timeout = float(value)
    except (TypeError, ValueError):
        timeout = EXTERNAL_EXECUTION_TIMEOUT_SECONDS
    if not math.isfinite(timeout) or timeout <= 0:
        timeout = EXTERNAL_EXECUTION_TIMEOUT_SECONDS
    return min(max(timeout, 0.01), 300.0)


async def execute_action_intent(
    *,
    session_factory,
    actor_tg_id: int,
    intent_id: str,
    idempotency_key: str,
    confirmation_sha256_header: str,
    action: str,
    target: Mapping[str, Any],
    payload: Mapping[str, Any],
    audit_writer,
    external_executor: Callable[[dict[str, Any]], Any] | None = None,
    external_timeout_seconds: float = EXTERNAL_EXECUTION_TIMEOUT_SECONDS,
    now: datetime | None = None,
) -> dict[str, Any]:
    normalized_intent_id, normalized_idempotency_key = (
        _normalize_execution_identifiers(
            session_factory=session_factory,
            actor_tg_id=actor_tg_id,
            intent_id=intent_id,
            idempotency_key=idempotency_key,
        )
    )
    execution_time = _as_utc(now or _utcnow())
    session = session_factory()
    external_context: dict[str, Any] | None = None
    intent: AdminActionIntent | None = None
    try:
        _begin_write_lock(session)
        owner = _read_idempotency_owner(session, normalized_idempotency_key)
        if owner is not None and owner.id != normalized_intent_id:
            raise ActionIntentError(
                "idempotency_conflict",
                status_code=409,
                message="Idempotency key уже связан с другим intent.",
            )
        intent = _locked_intent(session, normalized_intent_id)
        if intent is None:
            raise ActionIntentError(
                "intent_not_found",
                status_code=409,
                message="Intent не найден; создайте новый preview.",
            )
        policy, normalized_target, normalized_payload, state, replay = _validate_execution(
            session=session,
            intent=intent,
            actor_tg_id=actor_tg_id,
            action=action,
            target=target,
            payload=payload,
            idempotency_key=normalized_idempotency_key,
            confirmation_sha256_header=confirmation_sha256_header,
            now=execution_time,
        )
        if replay is not None:
            reconciled = _reconcile_stale_external_execution(
                session=session,
                intent=intent,
                idempotency_key=normalized_idempotency_key,
                now=execution_time,
            )
            if reconciled is not None:
                session.commit()
                return reconciled
            session.rollback()
            return replay
        assert state is not None
        intent.client_idempotency_key = normalized_idempotency_key
        intent.consumed_at = execution_time
        intent.updated_at = execution_time

        if policy.executor_kind == "db":
            if policy.db_executor is None:
                raise ActionIntentError(
                    "executor_unavailable",
                    status_code=503,
                    message="Исполнитель действия недоступен.",
                )
            domain_result = policy.db_executor(session, state, normalized_payload)
            try:
                audit = audit_writer(
                    session=session,
                    actor_tg_id=int(actor_tg_id),
                    action=policy.audit_action,
                    target_tg_id=None,
                    meta=_audit_meta(
                        intent,
                        state,
                        normalized_payload,
                        outcome="completed",
                    ),
                )
            except Exception:
                session.rollback()
                raise ActionIntentError(
                    "audit_failed",
                    status_code=503,
                    message="Аудит недоступен; действие отменено.",
                ) from None
            result = {
                "ok": True,
                "status": "completed",
                "action_intent_id": str(intent.id),
                "audit_id": int(audit.id),
                **domain_result,
            }
            intent.status = "completed"
            intent.admin_audit_id = int(audit.id)
            intent.result_code = "completed"
            intent.result_summary_json = _canonical_json(result)
            intent.result_hash = _semantic_hash("admin-action-result", result)
            session.commit()
            return result

        if policy.executor_kind != "external" or external_executor is None:
            raise ActionIntentError(
                "executor_unavailable",
                status_code=503,
                message="Внешний исполнитель действия недоступен.",
            )
        try:
            audit = audit_writer(
                session=session,
                actor_tg_id=int(actor_tg_id),
                action=policy.audit_action,
                target_tg_id=None,
                meta=_audit_meta(
                    intent,
                    state,
                    normalized_payload,
                    outcome="executing",
                ),
            )
        except Exception:
            session.rollback()
            raise ActionIntentError(
                "audit_failed",
                status_code=503,
                message="Аудит недоступен; действие не запускалось.",
            ) from None
        executing_result = {
            "ok": True,
            "status": "executing",
            "action_intent_id": str(intent.id),
            "audit_id": int(audit.id),
        }
        intent.status = "executing"
        intent.admin_audit_id = int(audit.id)
        intent.result_code = "executing"
        intent.result_summary_json = _canonical_json(executing_result)
        intent.result_hash = _semantic_hash("admin-action-result", executing_result)
        external_context = {
            "action_intent_id": str(intent.id),
            "actor_tg_id": int(actor_tg_id),
            "action": policy.action,
            "target": normalized_target,
            "payload": normalized_payload,
            "preview": json.loads(intent.preview_snapshot_json),
            "audit_id": int(audit.id),
        }
        if policy.external_context_builder is not None:
            external_context["execution"] = policy.external_context_builder(
                state,
                normalized_payload,
            )
        session.commit()
    except IntegrityError:
        session.rollback()
        conflict_session = session_factory()
        try:
            owner = _read_idempotency_owner(
                conflict_session,
                normalized_idempotency_key,
            )
            if owner is not None and owner.id == normalized_intent_id:
                return _stored_result(owner)
        finally:
            conflict_session.close()
        raise ActionIntentError(
            "idempotency_conflict",
            status_code=409,
            message="Idempotency key уже использован.",
            intent_id=normalized_intent_id,
        ) from None
    except ActionIntentError as error:
        owned_intent_id, audit_id = _loaded_action_intent_error_identifiers(
            intent,
            actor_tg_id=actor_tg_id,
        )
        if error.intent_id is None:
            error.intent_id = owned_intent_id
        if error.audit_id is None:
            error.audit_id = audit_id
        if session.in_transaction():
            session.rollback()
        raise
    except Exception:
        session.rollback()
        owned_intent_id, audit_id = _loaded_action_intent_error_identifiers(
            intent,
            actor_tg_id=actor_tg_id,
        )
        raise ActionIntentError(
            "action_failed",
            status_code=500,
            message="Действие не выполнено.",
            intent_id=owned_intent_id,
            audit_id=audit_id,
        ) from None
    finally:
        session.close()

    assert external_context is not None
    assert external_executor is not None
    try:
        raw_result = await asyncio.wait_for(
            _invoke_external_executor(external_executor, external_context),
            timeout=_external_timeout_seconds(external_timeout_seconds),
        )
    except TimeoutError:
        outcome = ExternalOutcome(
            status="uncertain",
            result=_terminal_external_result(
                status="uncertain",
                result_code="external_timeout",
                intent_id=normalized_intent_id,
                audit_id=int(external_context["audit_id"]),
            ),
            external_error_hash=_external_error_fingerprint("external_timeout"),
        )
    except Exception as exc:
        outcome = ExternalOutcome(
            status="uncertain",
            result=_terminal_external_result(
                status="uncertain",
                result_code="external_exception",
                intent_id=normalized_intent_id,
                audit_id=int(external_context["audit_id"]),
            ),
            external_error_hash=_external_error_fingerprint(
                "external_exception",
                exc,
            ),
        )
    else:
        outcome = _normalize_external_outcome(
            raw_result=raw_result,
            intent_id=normalized_intent_id,
            audit_id=int(external_context["audit_id"]),
        )

    return _persist_external_outcome(
        session_factory=session_factory,
        intent_id=normalized_intent_id,
        idempotency_key=normalized_idempotency_key,
        outcome=outcome,
    )

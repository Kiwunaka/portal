"""Generic persistence and execution runtime for guarded admin action intents.

The domain service owns the one action-policy registry and passes that exact
mapping into this runtime. This module owns generic intent identity,
confirmation, idempotency, locking, replay and bounded external-outcome state;
it does not register actions or HTTP routes.
"""

from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import math
import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from models import (
    AdminActionIntent,
    AdminAudit,
    AdminBroadcastRecipientPlan,
)
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
    {
        "ok",
        "code",
        "count",
        "attempted",
        "sent",
        "changed",
        "failed",
        "retryable_failed",
        "terminal_failed",
        "skipped",
        "job_id",
        "tg_id",
        "key_id",
        "ticket_id",
        "ticket_version",
        "node_code",
        "preset",
        "action",
        "users",
        "tier_days",
        "sync_ok",
        "is_active",
        "enabled",
        "applied",
        "panel_deleted",
        "dry_run",
        "requires_force",
        "preview_tg_ids",
        "details",
        "reason_counts",
    }
)
_EXTERNAL_COUNT_KEYS = (
    "count",
    "attempted",
    "sent",
    "changed",
    "failed",
    "retryable_failed",
    "terminal_failed",
    "skipped",
    "users",
    "tier_days",
    "ticket_version",
)
_MAX_EXTERNAL_COUNT = 1_000_000
_MAX_EXTERNAL_REFERENCE_LENGTH = 128
_MAX_BULK_PREVIEW_IDS = 50
_MAX_BULK_DETAILS = 500
_MAX_BROADCAST_RECIPIENTS = 1000
_INTERNAL_TARGET_CLAIMS_KEY = "_target_overlap_claims"
_INTERNAL_ISSUED_CARD_IDS_KEY = "_issued_card_ids"
_BULK_EXECUTION_LOCK_ENTITY_ID = -10_002


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
ExecutionStateBuilder = Callable[
    [Any, AdminActionIntent, Mapping[str, Any], bool],
    EntityState,
]
PreviewBuilder = Callable[[EntityState, Mapping[str, Any]], dict[str, Any]]
ChallengeBuilder = Callable[[EntityState, Mapping[str, Any]], str]
DbExecutor = Callable[[Any, EntityState, Mapping[str, Any]], dict[str, Any]]
RuntimeDbExecutor = Callable[
    [Any, EntityState, Mapping[str, Any], Mapping[str, Any]],
    dict[str, Any],
]
ExternalContextBuilder = Callable[[EntityState, Mapping[str, Any]], dict[str, Any]]
ExecutorKindBuilder = Callable[[Mapping[str, Any]], str]
AuditTargetBuilder = Callable[[EntityState, Mapping[str, Any]], int | None]
AuditMetaBuilder = Callable[[EntityState, Mapping[str, Any]], dict[str, Any]]
AuditActionBuilder = Callable[[Mapping[str, Any]], str]
PostCommitContextBuilder = Callable[
    [EntityState, Mapping[str, Any]], dict[str, Any] | None
]
ResultSanitizer = Callable[[Mapping[str, Any]], dict[str, Any]]
ReplayResultBuilder = Callable[
    [Any, AdminActionIntent, Mapping[str, Any]],
    dict[str, Any],
]


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
    runtime_payload_normalizer: PayloadNormalizer | None = None
    executor_kind_builder: ExecutorKindBuilder | None = None
    audit_target_builder: AuditTargetBuilder | None = None
    audit_meta_builder: AuditMetaBuilder | None = None
    audit_action_builder: AuditActionBuilder | None = None
    post_commit_context_builder: PostCommitContextBuilder | None = None
    execution_state_builder: ExecutionStateBuilder | None = None
    result_sanitizer: ResultSanitizer | None = None
    replay_result_builder: ReplayResultBuilder | None = None


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
    return hashlib.sha256(f"POKROV:{domain}:v1\n".encode("ascii") + payload).hexdigest()


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
            int(intent.admin_audit_id) if intent.admin_audit_id is not None else None,
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
        or not (
            _TARGET_ID_RE.fullmatch(target_id)
            or re.fullmatch(r"-[0-9]{1,19}", target_id)
        )
        or (expected_type is not None and target_type != expected_type)
    ):
        raise ActionIntentError(
            "invalid_target",
            status_code=422,
            message="Цель действия указана неверно.",
        )
    return {"type": target_type, "id": target_id}


def _reject_extra_payload_fields(
    payload: Mapping[str, Any],
    allowed: set[str],
) -> None:
    if set(payload) - allowed:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Тело запроса содержит неподдерживаемые поля.",
        )


def _bounded_text(
    value: object,
    *,
    field: str,
    minimum: int = 0,
    maximum: int,
    strip: bool = True,
) -> str:
    if not isinstance(value, str):
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message=f"Поле {field} должно быть строкой.",
        )
    normalized = unicodedata.normalize("NFC", value)
    if strip:
        normalized = normalized.strip()
    if not minimum <= len(normalized) <= maximum:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message=f"Поле {field} имеет недопустимую длину.",
        )
    return normalized


def _redacted_text(value: str) -> dict[str, Any]:
    encoded = unicodedata.normalize("NFC", value).encode("utf-8")
    return {
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "length": len(value),
    }


def _safe_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    aware = (
        value.replace(tzinfo=timezone.utc)
        if value.tzinfo is None or value.utcoffset() is None
        else value.astimezone(timezone.utc)
    )
    return aware.isoformat()


def _policy_for(
    action: str,
    policies: Mapping[str, ActionPolicy],
) -> ActionPolicy:
    normalized = str(action or "").strip().lower()
    policy = policies.get(normalized)
    if policy is None:
        raise ActionIntentError(
            "unknown_action",
            status_code=422,
            message="Действие не входит в серверный allowlist.",
        )
    return policy


def _executor_kind_for(policy: ActionPolicy, payload: Mapping[str, Any]) -> str:
    kind = (
        policy.executor_kind_builder(payload)
        if policy.executor_kind_builder is not None
        else policy.executor_kind
    )
    if kind not in {"db", "external"}:
        raise ActionIntentError(
            "executor_unavailable",
            status_code=503,
            message="Тип исполнителя действия указан неверно.",
        )
    return kind


def _audit_action_for(policy: ActionPolicy, payload: Mapping[str, Any]) -> str:
    action = (
        policy.audit_action_builder(payload)
        if policy.audit_action_builder is not None
        else policy.audit_action
    )
    return str(action or "").strip()[:64]


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
    policies: Mapping[str, ActionPolicy],
    session,
    actor_tg_id: int,
    action: str,
    target: Mapping[str, Any],
    payload: Mapping[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    policy = _policy_for(action, policies)
    normalized_target = _normalize_target(target, expected_type=policy.target_type)
    normalized_payload = policy.payload_normalizer(payload)
    runtime_payload = (
        policy.runtime_payload_normalizer(payload)
        if policy.runtime_payload_normalizer is not None
        else normalized_payload
    )
    state = policy.entity_state_builder(
        session,
        normalized_target["id"],
        runtime_payload,
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
        executor_kind=_executor_kind_for(policy, normalized_payload),
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
    if policy.action == "broadcast.send":
        selected = list(state.context.get("selected_tg_ids") or [])
        if not 1 <= len(selected) <= _MAX_BROADCAST_RECIPIENTS or selected != sorted(
            set(int(value) for value in selected)
        ):
            raise ActionIntentError(
                "invalid_selection",
                status_code=409,
                message="Зафиксированный план рассылки создать не удалось.",
            )
        session.add_all(
            [
                AdminBroadcastRecipientPlan(
                    intent_id=intent_id,
                    ordinal=index,
                    tg_id=int(tg_id),
                    created_at=prepared_at,
                )
                for index, tg_id in enumerate(selected)
            ]
        )
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


def _stored_result(
    intent: AdminActionIntent,
    *,
    include_internal: bool = False,
) -> dict[str, Any]:
    if intent.result_summary_json:
        try:
            value = json.loads(intent.result_summary_json)
            if isinstance(value, dict):
                if not include_internal:
                    value.pop(_INTERNAL_TARGET_CLAIMS_KEY, None)
                    value.pop(_INTERNAL_ISSUED_CARD_IDS_KEY, None)
                return value
        except (TypeError, ValueError):
            pass
    return {
        "ok": intent.status == "completed",
        "status": str(intent.status),
        "action_intent_id": str(intent.id),
        "audit_id": int(intent.admin_audit_id) if intent.admin_audit_id else None,
    }


def _replayed_result(
    session,
    intent: AdminActionIntent,
    policy: ActionPolicy,
) -> dict[str, Any]:
    stored = _stored_result(
        intent,
        include_internal=policy.replay_result_builder is not None,
    )
    if policy.replay_result_builder is None or str(intent.status) != "completed":
        return stored
    return policy.replay_result_builder(session, intent, stored)


def _public_execution_result(result: Mapping[str, Any]) -> dict[str, Any]:
    public = dict(result)
    public.pop(_INTERNAL_TARGET_CLAIMS_KEY, None)
    public.pop(_INTERNAL_ISSUED_CARD_IDS_KEY, None)
    return public


def get_action_intent_status(
    *,
    session,
    actor_tg_id: int,
    intent_id: str,
) -> dict[str, Any]:
    normalized_intent_id = _normalize_uuid(intent_id, code="invalid_intent_id")
    intent = (
        session.query(AdminActionIntent)
        .filter(
            AdminActionIntent.id == normalized_intent_id,
            AdminActionIntent.actor_tg_id == int(actor_tg_id),
        )
        .one_or_none()
    )
    if intent is None:
        raise ActionIntentError(
            "intent_not_found",
            status_code=404,
            message="Intent не найден.",
        )
    if str(intent.status) in _TERMINAL_STATUSES or str(intent.status) == "executing":
        return _stored_result(intent)
    return {
        "ok": False,
        "status": str(intent.status),
        "action_intent_id": str(intent.id),
        "audit_id": (
            int(intent.admin_audit_id) if intent.admin_audit_id is not None else None
        ),
        "result_code": str(intent.result_code) if intent.result_code else None,
    }


def _execution_return(
    result: dict[str, Any],
    *,
    replayed: bool,
    return_replay_state: bool,
) -> dict[str, Any] | tuple[dict[str, Any], bool]:
    if return_replay_state:
        return result, replayed
    return result


def _user_overlap_claim_token(tg_id: int) -> str:
    return _semantic_hash("admin-action-target-user", int(tg_id))


def _bulk_target_claims(state: EntityState) -> dict[str, Any]:
    selected = [int(value) for value in state.context.get("selected_tg_ids", [])]
    if not 1 <= len(selected) <= _MAX_BULK_DETAILS:
        raise ActionIntentError(
            "invalid_selection",
            status_code=409,
            message="Зафиксированная выборка пользователей недоступна.",
        )
    return {
        "kind": "user_selection_v1",
        "tokens": [_user_overlap_claim_token(tg_id) for tg_id in selected],
    }


def _persisted_bulk_claims(intent: AdminActionIntent) -> dict[str, Any] | None:
    try:
        stored = json.loads(str(intent.result_summary_json or ""))
        claims = (
            stored.get(_INTERNAL_TARGET_CLAIMS_KEY)
            if isinstance(stored, dict)
            else None
        )
        if not isinstance(claims, dict) or set(claims) != {"kind", "tokens"}:
            return None
        if claims.get("kind") != "user_selection_v1":
            return None
        values = claims.get("tokens")
        if not isinstance(values, list) or not 1 <= len(values) <= _MAX_BULK_DETAILS:
            return None
        tokens = [str(value) for value in values]
        if len(set(tokens)) != len(tokens) or any(
            _HEX_SHA256_RE.fullmatch(value) is None for value in tokens
        ):
            return None
        return {"kind": "user_selection_v1", "tokens": tokens}
    except (AttributeError, TypeError, ValueError):
        return None


def _persisted_bulk_claim_tokens(intent: AdminActionIntent) -> frozenset[str] | None:
    claims = _persisted_bulk_claims(intent)
    if claims is None:
        return None
    return frozenset(claims["tokens"])


def _acquire_bulk_execution_lock(session) -> None:
    if str(session.get_bind().dialect.name) != "postgresql":
        return
    session.execute(
        text("SELECT pg_advisory_xact_lock(:namespace, :entity_id)"),
        {
            "namespace": NODE_MAPPING_LOCK_NAMESPACE,
            "entity_id": _BULK_EXECUTION_LOCK_ENTITY_ID,
        },
    )


def _raise_target_busy(
    *,
    conflicting_intent: AdminActionIntent,
    now: datetime,
) -> None:
    if str(conflicting_intent.status) == "uncertain":
        raise ActionIntentError(
            "target_uncertain",
            status_code=409,
            message=(
                "Результат предыдущего внешнего действия не определён. Сначала "
                "вручную сверьте его и разрешите неопределённость."
            ),
        )
    if _as_utc(conflicting_intent.updated_at) <= now - EXTERNAL_EXECUTION_STALE_AFTER:
        # Never release a stale in-flight external effect implicitly. Replaying the
        # original idempotency key reconciles that intent before a new effect.
        raise ActionIntentError(
            "target_busy_stale",
            status_code=409,
            message=(
                "Предыдущее выполнение для этой цели зависло. Повторите исходный "
                "запрос с тем же ключом идемпотентности для безопасной сверки результата."
            ),
        )
    raise ActionIntentError(
        "target_busy",
        status_code=409,
        message="Для этой цели уже выполняется другое защищённое действие.",
    )


def _assert_no_target_overlap(
    *,
    session,
    intent: AdminActionIntent,
    state: EntityState,
    now: datetime,
) -> None:
    conflicts = session.query(AdminActionIntent).filter(
        AdminActionIntent.status.in_(("executing", "uncertain")),
        AdminActionIntent.id != str(intent.id),
    )
    direct = conflicts.filter(
        AdminActionIntent.target_type == str(intent.target_type),
        AdminActionIntent.target_id == str(intent.target_id),
    ).first()
    if direct is not None:
        _raise_target_busy(conflicting_intent=direct, now=now)

    if str(intent.target_type) == "user":
        try:
            target_tg_id = int(str(intent.target_id))
        except (TypeError, ValueError):
            return
        token = _user_overlap_claim_token(target_tg_id)
        active_bulks = conflicts.filter(
            AdminActionIntent.target_type == "users",
            AdminActionIntent.target_id == "bulk",
        ).all()
        for bulk_intent in active_bulks:
            claims = _persisted_bulk_claim_tokens(bulk_intent)
            if claims is None or token in claims:
                _raise_target_busy(conflicting_intent=bulk_intent, now=now)
        return

    if str(intent.target_type) == "users":
        selected = [
            str(int(value)) for value in state.context.get("selected_tg_ids", [])
        ]
        if selected:
            conflicting_user_intent = conflicts.filter(
                AdminActionIntent.target_type == "user",
                AdminActionIntent.target_id.in_(selected),
            ).first()
            if conflicting_user_intent is not None:
                _raise_target_busy(
                    conflicting_intent=conflicting_user_intent,
                    now=now,
                )


def _verify_confirmation(
    intent: AdminActionIntent,
    supplied_hash: str,
    *,
    constant_time_compare: Callable[[str, str], bool],
) -> None:
    supplied = str(supplied_hash or "").strip()
    candidate = supplied if _HEX_SHA256_RE.fullmatch(supplied) else "0" * 64
    matches = constant_time_compare(str(intent.confirmation_challenge_hash), candidate)
    if not matches or candidate != supplied:
        raise ActionIntentError(
            "confirmation_mismatch",
            status_code=409,
            message="Подтверждение не совпало с серверным challenge.",
        )


def _audit_meta(
    policy: ActionPolicy,
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
        "outcome": outcome,
    }
    if "mapped_users" in state.context:
        meta["mapped_users"] = int(state.context.get("mapped_users") or 0)
    if "force" in payload:
        meta["forced"] = bool(payload.get("force", False))
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
    if policy.audit_meta_builder is not None:
        meta.update(policy.audit_meta_builder(state, payload))
    return meta


def _validate_execution(
    *,
    policies: Mapping[str, ActionPolicy],
    constant_time_compare: Callable[[str, str], bool],
    session,
    intent: AdminActionIntent,
    actor_tg_id: int,
    action: str,
    target: Mapping[str, Any],
    payload: Mapping[str, Any],
    idempotency_key: str,
    confirmation_sha256_header: str,
    now: datetime,
) -> tuple[
    ActionPolicy,
    dict[str, str],
    dict[str, Any],
    dict[str, Any],
    EntityState | None,
    dict[str, Any] | None,
]:
    if (
        int(intent.actor_tg_id) != int(actor_tg_id)
        or str(intent.action) != str(action).strip().lower()
    ):
        raise ActionIntentError(
            "intent_mismatch",
            status_code=409,
            message="Намерение выпущено для другого оператора или другой команды.",
        )
    policy = _policy_for(intent.action, policies)
    normalized_target = _normalize_target(target, expected_type=policy.target_type)
    if normalized_target["type"] != str(intent.target_type) or normalized_target[
        "id"
    ] != str(intent.target_id):
        raise ActionIntentError(
            "intent_mismatch",
            status_code=409,
            message="Intent выпущен для другой цели.",
        )
    normalized_payload = policy.payload_normalizer(payload)
    if _payload_hash(normalized_payload) != str(intent.payload_hash):
        raise ActionIntentError(
            "payload_mismatch"
            if policy.action == "broadcast.send"
            else "intent_mismatch",
            status_code=409,
            message="Payload изменился после preview.",
        )
    runtime_payload = (
        policy.runtime_payload_normalizer(payload)
        if policy.runtime_payload_normalizer is not None
        else normalized_payload
    )
    if str(intent.executor_kind) != _executor_kind_for(policy, normalized_payload):
        raise ActionIntentError(
            "intent_mismatch",
            status_code=409,
            message="Тип исполнения изменился после preview.",
        )
    _verify_confirmation(
        intent,
        confirmation_sha256_header,
        constant_time_compare=constant_time_compare,
    )

    if intent.client_idempotency_key == idempotency_key:
        if intent.status in _TERMINAL_STATUSES or intent.status == "executing":
            return (
                policy,
                normalized_target,
                normalized_payload,
                runtime_payload,
                None,
                _replayed_result(session, intent, policy),
            )
    elif (
        intent.client_idempotency_key is not None
        or intent.status in _TERMINAL_STATUSES
        or intent.status == "executing"
    ):
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

    if (
        policy.action == "user.bulk_key_action"
        and str(intent.executor_kind) == "external"
    ):
        _acquire_bulk_execution_lock(session)

    state = (
        policy.execution_state_builder(session, intent, runtime_payload, True)
        if policy.execution_state_builder is not None
        else policy.entity_state_builder(
            session,
            normalized_target["id"],
            runtime_payload,
            True,
        )
    )
    live_version = _entity_version_hash(policy, normalized_target, state)
    if live_version != str(intent.entity_version_hash):
        raise ActionIntentError(
            "stale_intent",
            status_code=409,
            message="Состояние сущности изменилось после preview.",
        )
    _assert_no_target_overlap(session=session, intent=intent, state=state, now=now)
    return policy, normalized_target, normalized_payload, runtime_payload, state, None


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
                        key[:64] if isinstance(key, str) else f"<{type(key).__name__}>"
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


def _bounded_bulk_preview_ids(value: object) -> list[int]:
    if not isinstance(value, list) or len(value) > _MAX_BULK_PREVIEW_IDS:
        raise ValueError("invalid bulk preview ids")
    ids: list[int] = []
    for item in value:
        if type(item) is not int or not -(2**63) <= item < 2**63:
            raise ValueError("invalid bulk preview id")
        ids.append(int(item))
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate bulk preview id")
    return ids


def _bounded_bulk_details(value: object) -> list[dict[str, int]]:
    if not isinstance(value, list) or len(value) > _MAX_BULK_DETAILS:
        raise ValueError("invalid bulk details")
    details: list[dict[str, int]] = []
    for item in value:
        if not isinstance(item, Mapping) or set(item) != {"tg_id", "changed", "failed"}:
            raise ValueError("invalid bulk detail shape")
        tg_id = item["tg_id"]
        changed = item["changed"]
        failed = item["failed"]
        if type(tg_id) is not int or not -(2**63) <= tg_id < 2**63:
            raise ValueError("invalid bulk detail target")
        if (
            type(changed) is not int
            or type(failed) is not int
            or not 0 <= changed <= _MAX_EXTERNAL_COUNT
            or not 0 <= failed <= _MAX_EXTERNAL_COUNT
        ):
            raise ValueError("invalid bulk detail counters")
        details.append(
            {"tg_id": int(tg_id), "changed": int(changed), "failed": int(failed)}
        )
    if len({item["tg_id"] for item in details}) != len(details):
        raise ValueError("duplicate bulk detail target")
    return details


def _normalize_external_outcome(
    *,
    raw_result: object,
    action: str,
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
        if action == "broadcast.send" and (
            not {"attempted", "sent", "failed"}.issubset(facts)
            or int(facts["sent"]) + int(facts["failed"]) != int(facts["attempted"])
            or succeeded != (int(facts["failed"]) == 0)
        ):
            return _malformed_external_outcome(
                raw_result=raw_result,
                intent_id=intent_id,
                audit_id=audit_id,
            )
        if action == "broadcast.send":
            retryable_failed = int(facts.get("retryable_failed") or 0)
            terminal_failed = int(facts.get("terminal_failed") or 0)
            if retryable_failed + terminal_failed != int(facts["failed"]):
                return _malformed_external_outcome(
                    raw_result=raw_result,
                    intent_id=intent_id,
                    audit_id=audit_id,
                )
            reason_counts_raw = raw_result.get("reason_counts")
            if not isinstance(reason_counts_raw, Mapping):
                return _malformed_external_outcome(
                    raw_result=raw_result,
                    intent_id=intent_id,
                    audit_id=audit_id,
                )
            allowed_reasons = {
                "blocked",
                "bot_not_started_or_chat_not_found",
                "account_deactivated",
                "rate_limited",
                "transient_provider",
                "delivery_uncertain",
                "internal",
                "unknown_safe",
            }
            reason_counts: dict[str, int] = {}
            for reason, count in reason_counts_raw.items():
                if (
                    not isinstance(reason, str)
                    or reason not in allowed_reasons
                    or type(count) is not int
                    or not 0 <= int(count) <= _MAX_EXTERNAL_COUNT
                ):
                    return _malformed_external_outcome(
                        raw_result=raw_result,
                        intent_id=intent_id,
                        audit_id=audit_id,
                    )
                reason_counts[reason] = int(count)
            if sum(reason_counts.values()) != int(facts["failed"]):
                return _malformed_external_outcome(
                    raw_result=raw_result,
                    intent_id=intent_id,
                    audit_id=audit_id,
                )
            facts["reason_counts"] = dict(sorted(reason_counts.items()))
        has_bulk_diagnostics = any(
            key in raw_result for key in ("preview_tg_ids", "details")
        )
        if has_bulk_diagnostics and action != "user.bulk_key_action":
            return _malformed_external_outcome(
                raw_result=raw_result,
                intent_id=intent_id,
                audit_id=audit_id,
            )
        if "preview_tg_ids" in raw_result:
            facts["preview_tg_ids"] = _bounded_bulk_preview_ids(
                raw_result["preview_tg_ids"]
            )
        if "details" in raw_result:
            details = _bounded_bulk_details(raw_result["details"])
            if (
                "users" not in facts
                or "changed" not in facts
                or "failed" not in facts
                or len(details) != int(facts["users"])
                or sum(item["changed"] for item in details) != int(facts["changed"])
                or sum(item["failed"] for item in details) != int(facts["failed"])
            ):
                return _malformed_external_outcome(
                    raw_result=raw_result,
                    intent_id=intent_id,
                    audit_id=audit_id,
                )
            facts["details"] = details
        if "tg_id" in raw_result:
            value = raw_result["tg_id"]
            if type(value) is not int or not -(2**63) <= value < 2**63:
                return _malformed_external_outcome(
                    raw_result=raw_result,
                    intent_id=intent_id,
                    audit_id=audit_id,
                )
            facts["tg_id"] = int(value)
        for key in ("key_id", "ticket_id"):
            if key not in raw_result:
                continue
            value = raw_result[key]
            if type(value) is not int or not 1 <= value < 2**63:
                return _malformed_external_outcome(
                    raw_result=raw_result,
                    intent_id=intent_id,
                    audit_id=audit_id,
                )
            facts[key] = int(value)
        for key in (
            "sync_ok",
            "is_active",
            "enabled",
            "panel_deleted",
            "dry_run",
            "requires_force",
        ):
            if key not in raw_result:
                continue
            value = raw_result[key]
            if type(value) is not bool:
                return _malformed_external_outcome(
                    raw_result=raw_result,
                    intent_id=intent_id,
                    audit_id=audit_id,
                )
            facts[key] = value
        if "applied" in raw_result:
            value = raw_result["applied"]
            if value is not None and type(value) is not bool:
                return _malformed_external_outcome(
                    raw_result=raw_result,
                    intent_id=intent_id,
                    audit_id=audit_id,
                )
            facts["applied"] = value
        bounded_strings = {
            "node_code": (32, re.compile(r"^[a-z0-9][a-z0-9._-]{0,31}$")),
            "preset": (64, re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")),
            "action": (24, re.compile(r"^[a-z0-9][a-z0-9._-]{0,23}$")),
        }
        for key, (maximum, pattern) in bounded_strings.items():
            if key not in raw_result:
                continue
            value = raw_result[key]
            if (
                not isinstance(value, str)
                or not 1 <= len(value) <= maximum
                or value != value.strip().lower()
                or pattern.fullmatch(value) is None
            ):
                return _malformed_external_outcome(
                    raw_result=raw_result,
                    intent_id=intent_id,
                    audit_id=audit_id,
                )
            facts[key] = value

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
    for key in (
        "tg_id",
        "user_tg_id",
        "ticket_id",
        "key_id",
        "days",
        "tier_days",
        "delta_days",
        "display_name_length",
        "reason_length",
        "message_length",
        "recipient_count",
        "body_length",
        "media_file_id_length",
        "media_payload_length",
    ):
        value = source.get(key)
        if type(value) is int and -(2**63) <= value < 2**63:
            safe[key] = int(value)
    for key in (
        "apply_now",
        "notify_soft",
        "notify_hard",
        "auto_disable_on_hard",
        "blocked",
        "enable",
        "sync_ok",
        "is_active",
        "enabled",
        "panel_deleted",
        "requires_force",
    ):
        if type(source.get(key)) is bool:
            safe[key] = bool(source[key])
    for key in ("burst_mbps", "soft_cap_gb", "hard_cap_gb"):
        if key not in source:
            continue
        value = source[key]
        if value is None:
            safe[key] = None
        elif type(value) is int and 1 <= value <= _MAX_EXTERNAL_COUNT:
            safe[key] = int(value)
    for key, limit in (
        ("node_code", 32),
        ("preset", 64),
        ("action", 24),
        ("segment", 32),
        ("status", 20),
        ("media_type", 32),
    ):
        value = source.get(key)
        if isinstance(value, str) and len(value) <= limit:
            safe[key] = value
    for key in (
        "reason_sha256",
        "display_name_sha256",
        "message_sha256",
        "requested_tg_ids_hash",
        "recipient_hash",
        "body_sha256",
        "media_file_id_sha256",
        "media_payload_sha256",
    ):
        value = source.get(key)
        if isinstance(value, str) and _HEX_SHA256_RE.fullmatch(value):
            safe[key] = value

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
        for key in ("tg_id", "key_id", "ticket_id"):
            value = facts.get(key)
            if type(value) is int and -(2**63) <= value < 2**63:
                safe[key] = int(value)
        for key in (
            "sync_ok",
            "is_active",
            "enabled",
            "panel_deleted",
            "dry_run",
            "requires_force",
        ):
            if type(facts.get(key)) is bool:
                safe[key] = bool(facts[key])
        if "applied" in facts and (
            facts["applied"] is None or type(facts["applied"]) is bool
        ):
            safe["applied"] = facts["applied"]
        for key, limit in (("node_code", 32), ("preset", 64), ("action", 24)):
            value = facts.get(key)
            if isinstance(value, str) and len(value) <= limit:
                safe[key] = value
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
    persisted_result = dict(outcome.result)
    persisted_result.pop(_INTERNAL_TARGET_CLAIMS_KEY, None)
    if (
        outcome.status == "uncertain"
        and str(intent.target_type) == "users"
        and str(intent.target_id) == "bulk"
    ):
        claims = _persisted_bulk_claims(intent)
        if claims is not None:
            persisted_result[_INTERNAL_TARGET_CLAIMS_KEY] = claims
    result_hash = _semantic_hash("admin-action-result", persisted_result)
    intent.status = outcome.status
    intent.result_code = str(outcome.result["result_code"])
    intent.result_summary_json = _canonical_json(persisted_result)
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
        external_error_hash=_external_error_fingerprint("external_execution_stale"),
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
) -> tuple[dict[str, Any], bool]:
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
            return stored, True
        _apply_external_outcome(
            session=session,
            intent=intent,
            outcome=outcome,
            updated_at=_utcnow(),
        )
        session.commit()
        return outcome.result, False
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
    policies: Mapping[str, ActionPolicy],
    constant_time_compare: Callable[[str, str], bool],
    session_factory,
    actor_tg_id: int,
    intent_id: str,
    idempotency_key: str,
    confirmation_sha256_header: str,
    action: str,
    target: Mapping[str, Any],
    payload: Mapping[str, Any],
    audit_writer,
    db_executor: RuntimeDbExecutor | None = None,
    external_executor: Callable[[dict[str, Any]], Any] | None = None,
    post_commit_executor: Callable[[dict[str, Any]], Any] | None = None,
    external_timeout_seconds: float = EXTERNAL_EXECUTION_TIMEOUT_SECONDS,
    return_replay_state: bool = False,
    now: datetime | None = None,
) -> dict[str, Any] | tuple[dict[str, Any], bool]:
    normalized_intent_id, normalized_idempotency_key = _normalize_execution_identifiers(
        session_factory=session_factory,
        actor_tg_id=actor_tg_id,
        intent_id=intent_id,
        idempotency_key=idempotency_key,
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
        (
            policy,
            normalized_target,
            normalized_payload,
            runtime_payload,
            state,
            replay,
        ) = _validate_execution(
            policies=policies,
            constant_time_compare=constant_time_compare,
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
                return _execution_return(
                    reconciled,
                    replayed=True,
                    return_replay_state=return_replay_state,
                )
            session.rollback()
            return _execution_return(
                replay,
                replayed=True,
                return_replay_state=return_replay_state,
            )
        assert state is not None
        intent.client_idempotency_key = normalized_idempotency_key
        intent.consumed_at = execution_time
        intent.updated_at = execution_time

        executor_kind = str(intent.executor_kind)
        if executor_kind == "db":
            if policy.db_executor is None and db_executor is None:
                raise ActionIntentError(
                    "executor_unavailable",
                    status_code=503,
                    message="Исполнитель действия недоступен.",
                )
            if policy.db_executor is not None:
                domain_result = policy.db_executor(session, state, normalized_payload)
            else:
                assert db_executor is not None
                domain_result = db_executor(
                    session,
                    state,
                    normalized_payload,
                    runtime_payload,
                )
            try:
                audit = audit_writer(
                    session=session,
                    actor_tg_id=int(actor_tg_id),
                    action=_audit_action_for(policy, normalized_payload),
                    target_tg_id=(
                        policy.audit_target_builder(state, normalized_payload)
                        if policy.audit_target_builder is not None
                        else None
                    ),
                    meta=_audit_meta(
                        policy,
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
            persisted_result = (
                policy.result_sanitizer(result)
                if policy.result_sanitizer is not None
                else result
            )
            intent.status = "completed"
            intent.admin_audit_id = int(audit.id)
            intent.result_code = "completed"
            intent.result_summary_json = _canonical_json(persisted_result)
            intent.result_hash = _semantic_hash(
                "admin-action-result",
                persisted_result,
            )
            session.commit()
            if (
                policy.post_commit_context_builder is not None
                and post_commit_executor is not None
            ):
                post_commit_context = policy.post_commit_context_builder(
                    state,
                    normalized_payload,
                )
                if post_commit_context is not None:
                    try:
                        await asyncio.wait_for(
                            _invoke_external_executor(
                                post_commit_executor,
                                {
                                    "action_intent_id": str(intent.id),
                                    "actor_tg_id": int(actor_tg_id),
                                    "action": policy.action,
                                    "target": normalized_target,
                                    "execution": post_commit_context,
                                },
                            ),
                            timeout=_external_timeout_seconds(external_timeout_seconds),
                        )
                    except Exception:
                        pass
            return _execution_return(
                _public_execution_result(result),
                replayed=False,
                return_replay_state=return_replay_state,
            )

        if executor_kind != "external" or external_executor is None:
            raise ActionIntentError(
                "executor_unavailable",
                status_code=503,
                message="Внешний исполнитель действия недоступен.",
            )
        try:
            audit = audit_writer(
                session=session,
                actor_tg_id=int(actor_tg_id),
                action=_audit_action_for(policy, normalized_payload),
                target_tg_id=(
                    policy.audit_target_builder(state, normalized_payload)
                    if policy.audit_target_builder is not None
                    else None
                ),
                meta=_audit_meta(
                    policy,
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
        if policy.action == "user.bulk_key_action":
            executing_result[_INTERNAL_TARGET_CLAIMS_KEY] = _bulk_target_claims(state)
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
            "runtime_payload": runtime_payload,
            "preview": json.loads(intent.preview_snapshot_json),
            "audit_id": int(audit.id),
        }
        if policy.external_context_builder is not None:
            external_context["execution"] = policy.external_context_builder(
                state,
                runtime_payload,
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
                owner_policy = _policy_for(str(owner.action), policies)
                return _execution_return(
                    _replayed_result(conflict_session, owner, owner_policy),
                    replayed=True,
                    return_replay_state=return_replay_state,
                )
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
            action=str(external_context["action"]),
            intent_id=normalized_intent_id,
            audit_id=int(external_context["audit_id"]),
        )

    persisted, was_already_terminal = _persist_external_outcome(
        session_factory=session_factory,
        intent_id=normalized_intent_id,
        idempotency_key=normalized_idempotency_key,
        outcome=outcome,
    )
    return _execution_return(
        persisted,
        replayed=was_already_terminal,
        return_replay_state=return_replay_state,
    )

from __future__ import annotations

import hashlib
import hmac
import json
import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping

from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError

from models import AdminActionIntent, Node, UserNode
from ru_probe_contract import canonical_json_bytes


ACTION_INTENT_TTL = timedelta(minutes=10)
_HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TARGET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_TERMINAL_STATUSES = frozenset({"completed", "failed", "uncertain"})
_constant_time_compare = hmac.compare_digest


class ActionIntentError(RuntimeError):
    def __init__(self, code: str, *, status_code: int, message: str) -> None:
        self.code = code
        self.status_code = int(status_code)
        self.message = message
        super().__init__(code)


@dataclass(frozen=True)
class EntityState:
    entity: Any
    version_snapshot: dict[str, Any]
    public_snapshot: dict[str, Any]
    context: dict[str, Any]


PayloadNormalizer = Callable[[Mapping[str, Any]], dict[str, Any]]
EntityStateBuilder = Callable[[Any, str, bool], EntityState]
PreviewBuilder = Callable[[EntityState, Mapping[str, Any]], dict[str, Any]]
ChallengeBuilder = Callable[[EntityState, Mapping[str, Any]], str]
DbExecutor = Callable[[Any, EntityState, Mapping[str, Any]], dict[str, Any]]


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


def _normalize_node_disable_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if set(payload) - {"force"}:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Payload действия содержит неподдерживаемые поля.",
        )
    force = payload.get("force", False)
    if not isinstance(force, bool):
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Поле force должно быть boolean.",
        )
    return {"force": force}


def _node_entity_state(session, target_id: str, for_update: bool) -> EntityState:
    query = session.query(Node).filter(func.lower(Node.code) == target_id)
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    node = query.first()
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
            "На ноде есть привязанные пользователи; без force выполнение будет остановлено."
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


def _node_challenge(
    state: EntityState,
    _payload: Mapping[str, Any],
) -> str:
    return str(state.public_snapshot["code"]).upper()


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
            message="Сначала перенесите пользователей или подтвердите force.",
        )
    node = state.entity
    node.enabled = False
    node.accepting_new_clients = False
    node.is_draining = False
    return {
        "node": {
            **state.public_snapshot,
            "enabled": False,
            "accepting_new_clients": False,
            "is_draining": False,
        }
    }


ACTION_POLICIES: dict[str, ActionPolicy] = {
    "node.disable": ActionPolicy(
        action="node.disable",
        target_type="node",
        risk_level="L3",
        payload_normalizer=_normalize_node_disable_payload,
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
    state = policy.entity_state_builder(session, normalized_target["id"], False)
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
    return {
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
            message="Intent выпущен для другого actor или action.",
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

    state = policy.entity_state_builder(session, normalized_target["id"], True)
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


def _persist_external_outcome(
    *,
    session_factory,
    intent_id: str,
    idempotency_key: str,
    status: str,
    result: dict[str, Any],
    external_error_hash: str | None = None,
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
            )
        if intent.status != "executing":
            return _stored_result(intent)
        intent.status = status
        intent.result_code = str(result.get("result_code") or status)[:64]
        intent.result_summary_json = _canonical_json(result)
        intent.result_hash = _semantic_hash("admin-action-result", result)
        intent.external_error_hash = external_error_hash
        intent.updated_at = _utcnow()
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def execute_action_intent(
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
    now: datetime | None = None,
) -> dict[str, Any]:
    normalized_intent_id = _normalize_uuid(intent_id, code="invalid_intent_id")
    normalized_idempotency_key = _normalize_uuid(
        idempotency_key,
        code="invalid_idempotency_key",
    )
    execution_time = _as_utc(now or _utcnow())
    session = session_factory()
    external_context: dict[str, Any] | None = None
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
        ) from None
    except ActionIntentError:
        if session.in_transaction():
            session.rollback()
        raise
    except Exception:
        session.rollback()
        raise ActionIntentError(
            "action_failed",
            status_code=500,
            message="Действие не выполнено.",
        ) from None
    finally:
        session.close()

    assert external_context is not None
    try:
        raw_result = external_executor(external_context)
    except Exception as exc:
        error_hash = _semantic_hash(
            "admin-action-external-error",
            {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )
        uncertain = {
            "ok": False,
            "status": "uncertain",
            "result_code": "external_outcome_uncertain",
            "action_intent_id": normalized_intent_id,
            "audit_id": int(external_context["audit_id"]),
        }
        return _persist_external_outcome(
            session_factory=session_factory,
            intent_id=normalized_intent_id,
            idempotency_key=normalized_idempotency_key,
            status="uncertain",
            result=uncertain,
            external_error_hash=error_hash,
        )

    safe_external = raw_result if isinstance(raw_result, dict) else {}
    completed = {
        "ok": True,
        "status": "completed",
        "result_code": "completed",
        "action_intent_id": normalized_intent_id,
        "audit_id": int(external_context["audit_id"]),
        "result": {
            str(key)[:64]: value
            for key, value in safe_external.items()
            if key in {"ok", "count", "changed", "failed", "skipped", "job_id"}
            and isinstance(value, (str, int, bool, type(None)))
        },
    }
    return _persist_external_outcome(
        session_factory=session_factory,
        intent_id=normalized_intent_id,
        idempotency_key=normalized_idempotency_key,
        status="completed",
        result=completed,
    )

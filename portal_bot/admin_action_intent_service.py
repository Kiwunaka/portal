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
from zoneinfo import ZoneInfo

from sqlalchemy import and_, func, or_, text
from sqlalchemy.exc import IntegrityError

from admin_ops_service import (
    bytes_to_gb as _quota_bytes_to_gb,
    provider_quota_cycle_bounds,
    provider_quota_usage_bytes,
)
from models import (
    AccessKey,
    AdminActionIntent,
    AdminAudit,
    AdminBroadcastRecipientPlan,
    AppSetting,
    ExternalOrder,
    ExternalPaymentEvent,
    Event,
    GiftCard,
    IncentiveCampaign,
    LiveUpdate,
    PlanCatalog,
    PromoCode,
    PromoUsage,
    ReferralBonusQueue,
    RewardClaim,
    StartLink,
    SupportTicket,
    SupportTicketMessage,
    Template,
    User,
    UserKeyPolicy,
    UserNode,
    Node,
    ProviderTrafficQuota,
    WarpMaterial,
)
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
    {
        "ok",
        "code",
        "count",
        "attempted",
        "sent",
        "changed",
        "failed",
        "skipped",
        "job_id",
        "tg_id",
        "key_id",
        "ticket_id",
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
    }
)
_EXTERNAL_COUNT_KEYS = (
    "count",
    "attempted",
    "sent",
    "changed",
    "failed",
    "skipped",
    "users",
    "tier_days",
)
_MAX_EXTERNAL_COUNT = 1_000_000
_MAX_EXTERNAL_REFERENCE_LENGTH = 128
_MAX_BULK_PREVIEW_IDS = 50
_MAX_BULK_DETAILS = 500
_MAX_BROADCAST_RECIPIENTS = 1000
_INTERNAL_TARGET_CLAIMS_KEY = "_target_overlap_claims"
_INTERNAL_ISSUED_CARD_IDS_KEY = "_issued_card_ids"
_BULK_EXECUTION_LOCK_ENTITY_ID = -10_002
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
PostCommitContextBuilder = Callable[[EntityState, Mapping[str, Any]], dict[str, Any] | None]
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
    return value.isoformat()


def _normalize_empty_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, set())
    return {}


_PAYMENT_RECONCILE_STATUSES = frozenset(
    {
        "created",
        "pending",
        "paid",
        "failed",
        "cancelled",
        "refunded",
        "chargeback",
        "manual_review",
        "pending_verification",
    }
)


def _normalize_payment_reconcile_runtime(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"note", "status"})
    note = _bounded_text(
        payload.get("note"),
        field="note",
        minimum=8,
        maximum=1000,
    )
    status_value = payload.get("status")
    status = str(status_value or "").strip().lower()
    if status and status not in _PAYMENT_RECONCILE_STATUSES:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Статус платежа не поддерживается.",
        )
    return {"note": note, "status": status or None}


def _normalize_payment_reconcile_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    runtime = _normalize_payment_reconcile_runtime(payload)
    return {
        "note": _redacted_text(runtime["note"]),
        "status": runtime["status"],
    }


def _normalize_promo_code(value: object, *, field: str = "code") -> str:
    code = _bounded_text(value, field=field, minimum=3, maximum=20).upper()
    if re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{2,19}", code) is None:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Промокод может содержать только A-Z, цифры, дефис и подчёркивание.",
        )
    return code


def _normalize_promo_datetime(value: object) -> str | None:
    if value is None or value == "":
        return None
    raw = _bounded_text(value, field="expires_at", maximum=64)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Срок промокода указан неверно.",
        ) from None
    if parsed.tzinfo is not None and parsed.utcoffset() is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed.isoformat()


def _normalize_promo_type(value: object) -> str:
    promo_type = str(value or "").strip().lower()
    if promo_type not in {"discount", "days"}:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Тип промокода должен быть discount или days.",
        )
    return promo_type


def _normalize_promo_integer(
    value: object,
    *,
    field: str,
    minimum: int,
    maximum: int,
) -> int:
    if type(value) is not int or not minimum <= int(value) <= maximum:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message=f"Поле {field} указано неверно.",
        )
    return int(value)


def _normalize_promo_create_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(
        payload,
        {"code", "promo_type", "value", "uses_left", "expires_at"},
    )
    return {
        "code": _normalize_promo_code(payload.get("code")),
        "promo_type": _normalize_promo_type(payload.get("promo_type")),
        "value": _normalize_promo_integer(
            payload.get("value"),
            field="value",
            minimum=1,
            maximum=100000,
        ),
        "uses_left": _normalize_promo_integer(
            payload.get("uses_left", -1),
            field="uses_left",
            minimum=-1,
            maximum=1_000_000,
        ),
        "expires_at": _normalize_promo_datetime(payload.get("expires_at")),
    }


def _normalize_promo_update_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(
        payload,
        {"new_code", "promo_type", "value", "uses_left", "expires_at"},
    )
    if not payload:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Укажите хотя бы одно изменение промокода.",
        )
    normalized: dict[str, Any] = {}
    if "new_code" in payload:
        normalized["new_code"] = _normalize_promo_code(
            payload.get("new_code"),
            field="new_code",
        )
    if "promo_type" in payload:
        normalized["promo_type"] = _normalize_promo_type(payload.get("promo_type"))
    if "value" in payload:
        normalized["value"] = _normalize_promo_integer(
            payload.get("value"),
            field="value",
            minimum=1,
            maximum=100000,
        )
    if "uses_left" in payload:
        normalized["uses_left"] = _normalize_promo_integer(
            payload.get("uses_left"),
            field="uses_left",
            minimum=-1,
            maximum=1_000_000,
        )
    if "expires_at" in payload:
        normalized["expires_at"] = _normalize_promo_datetime(payload.get("expires_at"))
    return normalized


def _normalize_referral_process_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"limit", "force_without_activity"})
    limit = payload.get("limit", 100)
    force_without_activity = payload.get("force_without_activity", False)
    if type(limit) is not int or not 1 <= int(limit) <= 1000:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Лимит очереди должен быть от 1 до 1000.",
        )
    if type(force_without_activity) is not bool:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Флаг обработки без активности указан неверно.",
        )
    return {
        "limit": int(limit),
        "force_without_activity": bool(force_without_activity),
    }


def _normalize_manual_create_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"display_name", "days"})
    display_name = _bounded_text(
        payload.get("display_name"),
        field="display_name",
        minimum=2,
        maximum=100,
    )
    days = payload.get("days", 30)
    if type(days) is not int or not 1 <= int(days) <= 3650:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Поле days должно быть целым числом от 1 до 3650.",
        )
    return {"display_name": display_name, "days": int(days)}


def _normalize_manual_create_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    runtime = _normalize_manual_create_runtime(payload)
    return {
        "display_name": _redacted_text(runtime["display_name"]),
        "days": runtime["days"],
    }


def _normalize_extend_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"days", "delta_days", "allow_deactivate"})
    days = payload.get("days", 30)
    delta = payload.get("delta_days")
    if days is not None and (type(days) is not int or not 1 <= int(days) <= 3650):
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Поле days должно быть целым числом от 1 до 3650.",
        )
    if delta is not None and (
        type(delta) is not int or not -3650 <= int(delta) <= 3650
    ):
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Поле delta_days должно быть целым числом от -3650 до 3650.",
        )
    resolved = int(delta if delta is not None else (days or 0))
    if resolved == 0:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="delta_days не может быть равен нулю.",
        )
    allow_deactivate = payload.get("allow_deactivate", False)
    if type(allow_deactivate) is not bool:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Поле allow_deactivate должно быть логическим значением.",
        )
    return {
        "delta_days": resolved,
        "allow_deactivate": bool(allow_deactivate),
    }


def _normalize_block_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"blocked"})
    blocked = payload.get("blocked", True)
    if type(blocked) is not bool:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Поле blocked должно быть логическим значением.",
        )
    return {"blocked": bool(blocked)}


def _normalize_safe_delete_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"confirm"})
    confirm = payload.get("confirm", False)
    if type(confirm) is not bool or not confirm:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Для удаления нужно передать confirm=true.",
        )
    return {"confirm": True}


def _normalize_node_code(value: object) -> str:
    code = _bounded_text(value, field="node_code", minimum=1, maximum=32).lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,31}", code):
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Код ноды указан неверно.",
        )
    return code


def _normalize_user_key_toggle_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"node_code", "enable"})
    enable = payload.get("enable")
    if type(enable) is not bool:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Поле enable должно быть логическим значением.",
        )
    return {"node_code": _normalize_node_code(payload.get("node_code")), "enable": enable}


def _normalize_user_key_node_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"node_code"})
    return {"node_code": _normalize_node_code(payload.get("node_code"))}


def _optional_bounded_int(
    value: object,
    *,
    field: str,
    minimum: int,
    maximum: int,
) -> int | None:
    if value is None:
        return None
    if type(value) is not int or not minimum <= int(value) <= maximum:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message=f"Поле {field} имеет недопустимое значение.",
        )
    return int(value)


def _normalize_key_limits_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {
        "node_code",
        "burst_mbps",
        "soft_cap_gb",
        "hard_cap_gb",
        "notify_soft",
        "notify_hard",
        "auto_disable_on_hard",
        "apply_now",
    }
    _reject_extra_payload_fields(payload, allowed)
    soft_cap = _optional_bounded_int(
        payload.get("soft_cap_gb"), field="soft_cap_gb", minimum=1, maximum=1_000_000
    )
    hard_cap = _optional_bounded_int(
        payload.get("hard_cap_gb"), field="hard_cap_gb", minimum=1, maximum=1_000_000
    )
    if soft_cap is not None and hard_cap is not None and hard_cap < soft_cap:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="hard_cap_gb должен быть не меньше soft_cap_gb.",
        )
    normalized: dict[str, Any] = {
        "node_code": _normalize_node_code(payload.get("node_code")),
        "burst_mbps": _optional_bounded_int(
            payload.get("burst_mbps"), field="burst_mbps", minimum=1, maximum=5000
        ),
        "soft_cap_gb": soft_cap,
        "hard_cap_gb": hard_cap,
    }
    for field, default in (
        ("notify_soft", True),
        ("notify_hard", True),
        ("auto_disable_on_hard", True),
        ("apply_now", True),
    ):
        value = payload.get(field, default)
        if type(value) is not bool:
            raise ActionIntentError(
                "invalid_payload",
                status_code=422,
                message=f"Поле {field} должно быть логическим значением.",
            )
        normalized[field] = value
    return normalized


def _normalize_loyalty_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"tier_days"})
    tier_days = payload.get("tier_days")
    if type(tier_days) is not int or not 1 <= int(tier_days) <= 3650:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Поле tier_days должно быть целым числом от 1 до 3650.",
        )
    return {"tier_days": int(tier_days)}


def _normalize_preset_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"preset"})
    preset = _bounded_text(payload.get("preset"), field="preset", minimum=2, maximum=64).lower()
    if preset not in {"reset_key", "rotate_link", "extend_1d", "send_guide"}:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Сценарий не поддерживается.",
        )
    return {"preset": preset}


def _normalize_bulk_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {"action", "segment", "node_codes", "tg_ids", "q", "limit", "dry_run", "force"}
    _reject_extra_payload_fields(payload, allowed)
    action = _bounded_text(payload.get("action"), field="action", minimum=3, maximum=24).lower()
    if action not in {"disable", "enable", "reset", "resync"}:
        raise ActionIntentError(
            "invalid_payload", status_code=422, message="Массовое действие не поддерживается."
        )
    segment = _bounded_text(
        payload.get("segment", "all_active"), field="segment", minimum=2, maximum=32
    ).lower()
    if segment not in {"all", "all_active", "active", "inactive", "expired", "blocked", "paid", "free", "manual", "manual_test", "custom"}:
        raise ActionIntentError(
            "invalid_payload", status_code=422, message="Сегмент не поддерживается."
        )
    raw_nodes = payload.get("node_codes", [])
    raw_ids = payload.get("tg_ids", [])
    if not isinstance(raw_nodes, list) or len(raw_nodes) > 64:
        raise ActionIntentError("invalid_payload", status_code=422, message="Список нод указан неверно.")
    if not isinstance(raw_ids, list) or len(raw_ids) > 500 or any(type(value) is not int for value in raw_ids):
        raise ActionIntentError("invalid_payload", status_code=422, message="Список Telegram ID указан неверно.")
    node_codes: list[str] = []
    for value in raw_nodes:
        code = _normalize_node_code(value)
        if code not in node_codes:
            node_codes.append(code)
    tg_ids = sorted({int(value) for value in raw_ids})
    q = _bounded_text(payload.get("q", ""), field="q", maximum=120, strip=True)
    limit = payload.get("limit", 100)
    if type(limit) is not int or not 1 <= int(limit) <= 500:
        raise ActionIntentError("invalid_payload", status_code=422, message="Поле limit указано неверно.")
    dry_run = payload.get("dry_run", False)
    force = payload.get("force", False)
    if type(dry_run) is not bool or type(force) is not bool:
        raise ActionIntentError("invalid_payload", status_code=422, message="Флаги массового действия указаны неверно.")
    return {
        "action": action,
        "segment": segment,
        "node_codes": node_codes,
        "tg_ids": tg_ids,
        "q": q,
        "limit": int(limit),
        "dry_run": dry_run,
        "force": force,
    }


def _normalize_bulk_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    runtime = _normalize_bulk_runtime(payload)
    return {
        "action": runtime["action"],
        "segment": runtime["segment"],
        "node_codes": runtime["node_codes"],
        "tg_ids_hash": _semantic_hash("admin-bulk-requested-tg-ids", runtime["tg_ids"]),
        "tg_ids_count": len(runtime["tg_ids"]),
        "q": _redacted_text(runtime["q"]),
        "limit": runtime["limit"],
        "dry_run": runtime["dry_run"],
        "force": runtime["force"],
    }


def _normalize_message_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"text"})
    return {"text": _bounded_text(payload.get("text"), field="text", minimum=1, maximum=4000, strip=False)}


def _normalize_message_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    runtime = _normalize_message_runtime(payload)
    return {"text": _redacted_text(runtime["text"])}


def _normalize_broadcast_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"segment", "limit", "tg_ids", "text"})
    segment = _bounded_text(
        payload.get("segment", "all_active"),
        field="segment",
        minimum=2,
        maximum=32,
    ).lower()
    if segment not in {"all_active", "free", "paid", "expired", "custom"}:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Сегмент рассылки не поддерживается.",
        )
    limit = payload.get("limit", 500)
    if type(limit) is not int or not 1 <= int(limit) <= _MAX_BROADCAST_RECIPIENTS:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Поле limit для рассылки указано неверно.",
        )
    raw_ids = payload.get("tg_ids", [])
    if (
        not isinstance(raw_ids, list)
        or len(raw_ids) > _MAX_BROADCAST_RECIPIENTS
        or any(type(value) is not int or int(value) <= 0 for value in raw_ids)
    ):
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Список Telegram ID для рассылки указан неверно.",
        )
    tg_ids = sorted({int(value) for value in raw_ids})
    if segment != "custom" and tg_ids:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Telegram ID разрешены только для пользовательского сегмента.",
        )
    if segment == "custom" and not tg_ids:
        raise ActionIntentError(
            "empty_selection",
            status_code=409,
            message="Список получателей рассылки пуст.",
        )
    text_value = _bounded_text(
        payload.get("text"),
        field="text",
        minimum=1,
        maximum=4000,
        strip=False,
    )
    message_meta = _redacted_text(text_value)
    return {
        "segment": segment,
        "limit": int(limit),
        "tg_ids": tg_ids,
        "text": text_value,
        "requested_tg_ids_hash": hashlib.sha256(
            canonical_json_bytes(tg_ids)
        ).hexdigest(),
        "message_sha256": str(message_meta["sha256"]),
        "message_length": int(message_meta["length"]),
    }


def _normalize_broadcast_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    runtime = _normalize_broadcast_runtime(payload)
    return {
        "segment": runtime["segment"],
        "limit": runtime["limit"],
        "requested_tg_ids_hash": runtime["requested_tg_ids_hash"],
        "message_sha256": runtime["message_sha256"],
        "message_length": runtime["message_length"],
    }


def _normalize_ticket_reply_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {"body", "attachment_id", "media_type", "media_file_id", "media_payload"}
    _reject_extra_payload_fields(payload, allowed)
    body = _bounded_text(payload.get("body"), field="body", minimum=1, maximum=2000, strip=False)
    media_type_raw = payload.get("media_type")
    media_type = None
    if media_type_raw is not None:
        media_type = _bounded_text(media_type_raw, field="media_type", maximum=32) or None
    out: dict[str, Any] = {"body": body, "media_type": media_type}
    for field, maximum in (
        ("attachment_id", 160),
        ("media_file_id", 256),
        ("media_payload", 2000),
    ):
        value = payload.get(field)
        out[field] = (
            _bounded_text(value, field=field, maximum=maximum, strip=False)
            if value is not None
            else None
        )
    return out


def _normalize_ticket_reply_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    runtime = _normalize_ticket_reply_runtime(payload)
    return {
        "body": _redacted_text(runtime["body"]),
        "attachment_id": _redacted_text(runtime["attachment_id"] or ""),
        "media_type": runtime["media_type"],
        "media_file_id": _redacted_text(runtime["media_file_id"] or ""),
        "media_payload": _redacted_text(runtime["media_payload"] or ""),
    }


def _normalize_ticket_status_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"status"})
    status = _bounded_text(payload.get("status"), field="status", minimum=2, maximum=20).lower()
    if status not in {"open", "in_progress", "closed"}:
        raise ActionIntentError("invalid_payload", status_code=422, message="Статус обращения не поддерживается.")
    return {"status": status}


def _normalize_provider_timezone(value: object) -> str:
    timezone_name = _bounded_text(
        value,
        field="timezone",
        minimum=1,
        maximum=64,
    )
    if timezone_name.upper() == "UTC":
        return "UTC"
    try:
        return str(ZoneInfo(timezone_name).key)
    except Exception as exc:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Часовой пояс квоты указан неверно.",
        ) from exc


def _normalize_provider_ratio(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message=f"Поле {field} должно быть числом.",
        )
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.01 <= normalized <= 1.0:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message=f"Поле {field} должно быть от 0.01 до 1.0.",
        )
    return round(normalized, 6)


def _normalize_provider_included_bytes(payload: Mapping[str, Any]) -> int:
    included_bytes = payload.get("included_bytes")
    included_gb = payload.get("included_gb")
    if included_bytes is not None:
        if type(included_bytes) is not int or not 0 <= int(included_bytes) <= 2**63 - 1:
            raise ActionIntentError(
                "invalid_payload",
                status_code=422,
                message="Поле included_bytes указано неверно.",
            )
        normalized = int(included_bytes)
        if included_gb is not None:
            if isinstance(included_gb, bool) or not isinstance(included_gb, (int, float)):
                raise ActionIntentError(
                    "invalid_payload",
                    status_code=422,
                    message="Поле included_gb должно быть числом.",
                )
            gb_value = float(included_gb)
            if not math.isfinite(gb_value) or gb_value < 0:
                raise ActionIntentError(
                    "invalid_payload",
                    status_code=422,
                    message="Поле included_gb указано неверно.",
                )
            if int(gb_value * (1024**3)) != normalized:
                raise ActionIntentError(
                    "invalid_payload",
                    status_code=422,
                    message="included_bytes и included_gb описывают разные лимиты.",
                )
        return normalized
    if included_gb is None:
        return 0
    if isinstance(included_gb, bool) or not isinstance(included_gb, (int, float)):
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Поле included_gb должно быть числом.",
        )
    gb_value = float(included_gb)
    if not math.isfinite(gb_value) or gb_value < 0:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Поле included_gb указано неверно.",
        )
    normalized = int(gb_value * (1024**3))
    if normalized > 2**63 - 1:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Лимит провайдера слишком велик.",
        )
    return normalized


def _normalize_provider_notes(value: object) -> str | None:
    if value is None:
        return None
    normalized = _bounded_text(value, field="notes", maximum=1000)
    return normalized or None


def _normalize_provider_quota_create_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(
        payload,
        {
            "node_code",
            "included_bytes",
            "included_gb",
            "reset_day",
            "timezone",
            "warning_ratio",
            "critical_ratio",
            "enabled",
            "notes",
        },
    )
    reset_day = payload.get("reset_day", 1)
    enabled = payload.get("enabled", True)
    if type(reset_day) is not int or not 1 <= int(reset_day) <= 31:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="День сброса должен быть от 1 до 31.",
        )
    if type(enabled) is not bool:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Поле enabled должно быть логическим значением.",
        )
    warning_ratio = _normalize_provider_ratio(
        payload.get("warning_ratio", 0.8),
        field="warning_ratio",
    )
    critical_ratio = _normalize_provider_ratio(
        payload.get("critical_ratio", 0.95),
        field="critical_ratio",
    )
    if warning_ratio >= critical_ratio:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Порог предупреждения должен быть ниже критического.",
        )
    return {
        "node_code": _normalize_node_code(payload.get("node_code")),
        "included_bytes": _normalize_provider_included_bytes(payload),
        "reset_day": int(reset_day),
        "timezone": _normalize_provider_timezone(payload.get("timezone", "UTC")),
        "warning_ratio": warning_ratio,
        "critical_ratio": critical_ratio,
        "enabled": bool(enabled),
        "notes": _normalize_provider_notes(payload.get("notes")),
    }


def _provider_quota_safe_payload(runtime: Mapping[str, Any]) -> dict[str, Any]:
    notes = runtime.get("notes")
    return {
        key: value
        for key, value in runtime.items()
        if key != "notes"
    } | {
        "notes": _redacted_text(str(notes)) if notes is not None else None,
    }


def _normalize_provider_quota_create_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _provider_quota_safe_payload(_normalize_provider_quota_create_runtime(payload))


def _normalize_provider_quota_update_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(
        payload,
        {
            "included_bytes",
            "included_gb",
            "reset_day",
            "timezone",
            "warning_ratio",
            "critical_ratio",
            "enabled",
            "notes",
        },
    )
    if not payload:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Укажите хотя бы одно изменение квоты.",
        )
    normalized: dict[str, Any] = {}
    if "included_bytes" in payload or "included_gb" in payload:
        normalized["included_bytes"] = _normalize_provider_included_bytes(payload)
    if "reset_day" in payload:
        reset_day = payload.get("reset_day")
        if type(reset_day) is not int or not 1 <= int(reset_day) <= 31:
            raise ActionIntentError(
                "invalid_payload",
                status_code=422,
                message="День сброса должен быть от 1 до 31.",
            )
        normalized["reset_day"] = int(reset_day)
    if "timezone" in payload:
        normalized["timezone"] = _normalize_provider_timezone(payload.get("timezone"))
    for field in ("warning_ratio", "critical_ratio"):
        if field in payload:
            normalized[field] = _normalize_provider_ratio(payload.get(field), field=field)
    if "enabled" in payload:
        enabled = payload.get("enabled")
        if type(enabled) is not bool:
            raise ActionIntentError(
                "invalid_payload",
                status_code=422,
                message="Поле enabled должно быть логическим значением.",
            )
        normalized["enabled"] = bool(enabled)
    if "notes" in payload:
        normalized["notes"] = _normalize_provider_notes(payload.get("notes"))
    return normalized


def _normalize_provider_quota_update_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _provider_quota_safe_payload(_normalize_provider_quota_update_runtime(payload))


def _normalize_key_rotate_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"reason", "dry_run"})
    reason = _bounded_text(payload.get("reason", "manual_review"), field="reason", maximum=160)
    if not reason:
        reason = "manual_review"
    dry_run = payload.get("dry_run", False)
    if type(dry_run) is not bool:
        raise ActionIntentError("invalid_payload", status_code=422, message="Поле dry_run должно быть логическим значением.")
    return {"reason": reason, "dry_run": dry_run}


def _normalize_key_rotate_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    runtime = _normalize_key_rotate_runtime(payload)
    return {"reason": _redacted_text(runtime["reason"]), "dry_run": runtime["dry_run"]}


def _integer_target(target_id: str, *, positive: bool = False) -> int:
    try:
        value = int(str(target_id))
    except (TypeError, ValueError):
        raise ActionIntentError(
            "invalid_target", status_code=422, message="Идентификатор цели указан неверно."
        ) from None
    if not -(2**63) <= value < 2**63 or (positive and value <= 0):
        raise ActionIntentError(
            "invalid_target", status_code=422, message="Идентификатор цели указан неверно."
        )
    return value


def _manual_test_user(user: User) -> bool:
    return bool(
        bool(getattr(user, "is_manual", False))
        or int(user.tg_id) < 0
        or str(user.sub_type or "").strip().upper() == "MANUAL"
        or getattr(user, "created_by_admin", None) is not None
    )


def _user_entity_state(
    session,
    target_id: str,
    _payload: Mapping[str, Any],
    for_update: bool,
) -> EntityState:
    tg_id = _integer_target(target_id)
    query = session.query(User).filter(User.tg_id == tg_id)
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    user = query.first()
    if user is None:
        raise ActionIntentError("target_not_found", status_code=404, message="Пользователь не найден.")
    mappings = (
        session.query(UserNode)
        .filter(UserNode.tg_id == tg_id)
        .order_by(UserNode.id.asc())
        .all()
    )
    policies = (
        session.query(UserKeyPolicy)
        .filter(UserKeyPolicy.tg_id == tg_id)
        .order_by(UserKeyPolicy.node_code.asc(), UserKeyPolicy.id.asc())
        .all()
    )
    claims = (
        session.query(RewardClaim)
        .filter(RewardClaim.tg_id == tg_id)
        .order_by(RewardClaim.reward_key.asc(), RewardClaim.id.asc())
        .all()
    )
    version_snapshot = {
        "tg_id": tg_id,
        "is_active": bool(user.is_active),
        "expiry_at": _safe_iso(user.expiry_at),
        "sub_type": str(user.sub_type or ""),
        "sub_token_hash": _semantic_hash("admin-user-sub-token", str(user.sub_token or "")),
        "uuid_hash": _semantic_hash("admin-user-uuid", str(user.uuid or "")),
        "mappings": [
            {
                "id": int(row.id),
                "node_id": int(row.node_id),
                "client_hash": _semantic_hash(
                    "admin-user-mapping-client",
                    [str(row.client_uuid or ""), str(row.panel_email or "")],
                ),
            }
            for row in mappings
        ],
        "key_policies": [
            {
                "id": int(row.id),
                "node_code": str(row.node_code or "").strip().lower(),
                "burst_mbps": row.burst_mbps,
                "soft_cap_gb": row.soft_cap_gb,
                "hard_cap_gb": row.hard_cap_gb,
                "notify_soft": bool(row.notify_soft),
                "notify_hard": bool(row.notify_hard),
                "auto_disable_on_hard": bool(row.auto_disable_on_hard),
                "updated_at": _safe_iso(row.updated_at),
            }
            for row in policies
        ],
        "reward_claims": [
            {
                "reward_key": str(row.reward_key or ""),
                "claimed_at": _safe_iso(row.claimed_at),
            }
            for row in claims
        ],
    }
    public_snapshot = {
        "tg_id": tg_id,
        "sub_type": _subscription_type_title(str(user.sub_type or "")),
        "is_active": bool(user.is_active),
        "expiry_at": _safe_iso(user.expiry_at),
        "manual_test": _manual_test_user(user),
        "key_count": len(mappings),
    }
    return EntityState(
        entity=user,
        version_snapshot=version_snapshot,
        public_snapshot=public_snapshot,
        context={
            "tg_id": tg_id,
            "user_uuid": str(user.uuid or ""),
            "sub_token": str(user.sub_token or ""),
            "mappings": mappings,
            "key_policies": policies,
            "reward_claims": claims,
        },
    )


def _manual_delete_user_entity_state(
    session,
    target_id: str,
    payload: Mapping[str, Any],
    for_update: bool,
) -> EntityState:
    state = _user_entity_state(session, target_id, payload, for_update)
    if not _manual_test_user(state.entity):
        raise ActionIntentError(
            "target_not_deletable",
            status_code=409,
            message="Удалять можно только явно созданного ручного/тестового пользователя.",
        )
    return state


def _manual_create_entity_state(
    session,
    target_id: str,
    _payload: Mapping[str, Any],
    for_update: bool,
) -> EntityState:
    if str(target_id) != "manual":
        raise ActionIntentError("invalid_target", status_code=422, message="Цель создания указана неверно.")
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        session.execute(
            text("SELECT pg_advisory_xact_lock(:namespace, :entity_id)"),
            {"namespace": NODE_MAPPING_LOCK_NAMESPACE, "entity_id": -10_001},
        )
    minimum = session.query(func.min(User.tg_id)).filter(User.tg_id < 0).scalar()
    candidate = -10_001 if minimum is None else int(minimum) - 1
    manual_count = int(
        session.query(func.count(User.tg_id))
        .filter(
            or_(
                User.is_manual == True,
                User.tg_id < 0,
                func.upper(func.coalesce(User.sub_type, "")) == "MANUAL",
                User.created_by_admin.isnot(None),
            )
        )
        .scalar()
        or 0
    )
    return EntityState(
        entity=None,
        version_snapshot={"next_tg_id": candidate, "manual_count": manual_count},
        public_snapshot={"manual_users": manual_count},
        context={"candidate_tg_id": candidate},
    )


def _ticket_entity_state(
    session,
    target_id: str,
    _payload: Mapping[str, Any],
    for_update: bool,
) -> EntityState:
    ticket_id = _integer_target(target_id, positive=True)
    query = session.query(SupportTicket).filter(SupportTicket.id == ticket_id)
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    ticket = query.first()
    if ticket is None:
        raise ActionIntentError("target_not_found", status_code=404, message="Обращение не найдено.")
    messages = (
        session.query(SupportTicketMessage.id, SupportTicketMessage.created_at)
        .filter(SupportTicketMessage.ticket_id == ticket_id)
        .order_by(SupportTicketMessage.id.asc())
        .all()
    )
    snapshot = {
        "ticket_id": ticket_id,
        "user_tg_id": int(ticket.user_tg_id),
        "status": str(ticket.status or ""),
        "assigned_admin_tg_id": (
            int(ticket.assigned_admin_tg_id)
            if ticket.assigned_admin_tg_id is not None
            else None
        ),
        "updated_at": _safe_iso(ticket.updated_at),
        "closed_at": _safe_iso(ticket.closed_at),
        "message_ids": [int(row[0]) for row in messages],
    }
    return EntityState(
        entity=ticket,
        version_snapshot=snapshot,
        public_snapshot={
            "ticket_id": ticket_id,
            "status": _ticket_status_title(str(ticket.status or "")),
            "messages": len(messages),
        },
        context={"ticket_id": ticket_id, "user_tg_id": int(ticket.user_tg_id)},
    )


def _key_entity_state(
    session,
    target_id: str,
    _payload: Mapping[str, Any],
    for_update: bool,
) -> EntityState:
    key_id = _integer_target(target_id, positive=True)
    query = session.query(AccessKey).filter(AccessKey.id == key_id)
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    key = query.first()
    if key is None:
        raise ActionIntentError("target_not_found", status_code=404, message="Ключ не найден.")
    snapshot = {
        "key_id": key_id,
        "tg_id": int(key.tg_id),
        "node_code": str(key.node_code or "").strip().lower() or None,
        "pool_code": str(key.pool_code or ""),
        "state": str(key.state or ""),
        "updated_at": _safe_iso(key.updated_at),
    }
    return EntityState(
        entity=key,
        version_snapshot=snapshot,
        public_snapshot={
            "key_id": key_id,
            "tg_id": int(key.tg_id),
            "node_code": str(key.node_code or "").strip().upper() or "Не назначена",
            "state": _key_state_title(str(key.state or "")),
        },
        context={"key_id": key_id, "tg_id": int(key.tg_id)},
    )


def _manual_user_filter():
    return or_(
        User.is_manual == True,
        User.tg_id < 0,
        func.upper(func.coalesce(User.sub_type, "")) == "MANUAL",
        User.created_by_admin.isnot(None),
    )


def _bulk_user_query(session, payload: Mapping[str, Any]):
    segment = str(payload["segment"])
    now = _utcnow().replace(tzinfo=None)
    manual = _manual_user_filter()
    active = and_(~manual, User.is_active == True, User.expiry_at.isnot(None), User.expiry_at > now)
    blocked = and_(~manual, User.is_active == False, User.expiry_at.isnot(None), User.expiry_at > now)
    expired = and_(~manual, or_(User.expiry_at.is_(None), User.expiry_at <= now))
    query = session.query(User)
    if segment == "all":
        query = query.filter(User.tg_id > 0, ~manual)
    elif segment in {"all_active", "active"}:
        query = query.filter(active)
    elif segment == "inactive":
        query = query.filter(or_(blocked, expired))
    elif segment == "blocked":
        query = query.filter(blocked)
    elif segment == "expired":
        query = query.filter(expired)
    elif segment == "paid":
        query = query.filter(User.tg_id > 0, ~manual, func.upper(User.sub_type) == "PAID")
    elif segment == "free":
        query = query.filter(User.tg_id > 0, ~manual, func.upper(User.sub_type) == "FREE")
    elif segment in {"manual", "manual_test"}:
        query = query.filter(manual)
    elif segment == "custom":
        if not payload["tg_ids"]:
            raise ActionIntentError(
                "empty_selection", status_code=409, message="Список пользователей пуст."
            )
        query = query.filter(User.tg_id.in_(list(payload["tg_ids"])))
    q = str(payload.get("q") or "").strip()
    if q:
        filters = [
            User.username.ilike(f"%{q}%"),
            User.display_name.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%"),
            User.linked_telegram_username.ilike(f"%{q}%"),
            User.app_install_id.ilike(f"%{q}%"),
        ]
        if q.isdigit():
            filters.extend([User.tg_id == int(q), User.linked_telegram_id == int(q)])
        query = query.filter(or_(*filters))
    return query.order_by(User.created_at.desc(), User.tg_id.desc()).limit(int(payload["limit"]))


def _bulk_entity_state(
    session,
    target_id: str,
    payload: Mapping[str, Any],
    for_update: bool,
) -> EntityState:
    if str(target_id) != "bulk":
        raise ActionIntentError("invalid_target", status_code=422, message="Цель массового действия указана неверно.")
    query = _bulk_user_query(session, payload)
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    users = query.all()
    if not users:
        raise ActionIntentError("empty_selection", status_code=409, message="Под выбранные условия пользователи не найдены.")
    selection = [int(user.tg_id) for user in users]
    selection_hash = _semantic_hash("admin-bulk-selected-users", selection)
    anchor_tg_id = int(selection[0])
    return EntityState(
        entity=None,
        version_snapshot={
            "selection_hash": selection_hash,
            "selected_count": len(selection),
        },
        public_snapshot={
            "selected_count": len(selection),
            "selection_hash": selection_hash,
        },
        context={
            "selected_tg_ids": selection,
            "selected_count": len(selection),
            "selection_hash": selection_hash,
            "anchor_tg_id": anchor_tg_id,
        },
    )


def _broadcast_state_from_selection(selection: list[int]) -> EntityState:
    normalized = sorted({int(value) for value in selection if int(value) > 0})
    if not 1 <= len(normalized) <= _MAX_BROADCAST_RECIPIENTS:
        raise ActionIntentError(
            "empty_selection" if not normalized else "invalid_selection",
            status_code=409,
            message=(
                "Под выбранные условия получатели не найдены."
                if not normalized
                else "Зафиксированная выборка рассылки недоступна."
            ),
        )
    recipient_hash = _semantic_hash(
        "admin-broadcast-selected-recipients",
        normalized,
    )
    snapshot = {
        "recipient_count": len(normalized),
        "recipient_hash": recipient_hash,
    }
    return EntityState(
        entity=None,
        version_snapshot=dict(snapshot),
        public_snapshot=dict(snapshot),
        context={
            "selected_tg_ids": normalized,
            "recipient_count": len(normalized),
            "recipient_hash": recipient_hash,
        },
    )


def _broadcast_entity_state(
    session,
    target_id: str,
    payload: Mapping[str, Any],
    _for_update: bool,
) -> EntityState:
    if str(target_id) != "broadcast":
        raise ActionIntentError(
            "invalid_target",
            status_code=422,
            message="Цель рассылки указана неверно.",
        )
    segment = str(payload["segment"])
    query = session.query(User.tg_id).filter(User.tg_id > 0)
    if segment == "all_active":
        query = query.filter(User.is_active == True)
    elif segment == "free":
        query = query.filter(func.upper(User.sub_type) == "FREE")
    elif segment == "paid":
        query = query.filter(func.upper(User.sub_type) == "PAID")
    elif segment == "expired":
        query = query.filter(
            User.expiry_at.isnot(None),
            User.expiry_at < _utcnow().replace(tzinfo=None),
        )
    elif segment == "custom":
        query = query.filter(User.tg_id.in_(list(payload["tg_ids"])))
    else:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message="Сегмент рассылки не поддерживается.",
        )
    selection = [
        int(row[0])
        for row in query.order_by(User.tg_id.asc())
        .limit(int(payload["limit"]))
        .all()
    ]
    return _broadcast_state_from_selection(selection)


def _broadcast_execution_state(
    session,
    intent: AdminActionIntent,
    _payload: Mapping[str, Any],
    for_update: bool,
) -> EntityState:
    query = session.query(AdminBroadcastRecipientPlan).filter(
        AdminBroadcastRecipientPlan.intent_id == str(intent.id)
    )
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    rows = query.order_by(AdminBroadcastRecipientPlan.ordinal.asc()).all()
    if (
        not 1 <= len(rows) <= _MAX_BROADCAST_RECIPIENTS
        or any(int(row.ordinal) != index for index, row in enumerate(rows))
    ):
        raise ActionIntentError(
            "frozen_selection_unavailable",
            status_code=409,
            message="Зафиксированный план рассылки недоступен; отправка заблокирована.",
        )
    selection = [int(row.tg_id) for row in rows]
    if selection != sorted(set(selection)):
        raise ActionIntentError(
            "frozen_selection_unavailable",
            status_code=409,
            message="Зафиксированный план рассылки повреждён; отправка заблокирована.",
        )
    return _broadcast_state_from_selection(selection)


def _l2_challenge(_state: EntityState, _payload: Mapping[str, Any]) -> str:
    return "ПОДТВЕРДИТЬ"


def _send_challenge(_state: EntityState, _payload: Mapping[str, Any]) -> str:
    return "ОТПРАВИТЬ"


def _user_challenge(state: EntityState, _payload: Mapping[str, Any]) -> str:
    return str(int(state.context["tg_id"]))


def _key_challenge(state: EntityState, _payload: Mapping[str, Any]) -> str:
    return str(int(state.context["key_id"]))


def _bulk_challenge(state: EntityState, _payload: Mapping[str, Any]) -> str:
    return str(int(state.context["anchor_tg_id"]))


def _simple_preview(summary: str, before: object, after: object, warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "title": summary.rstrip(". "),
        "summary": summary,
        "before": before,
        "after": after,
        "warnings": list(warnings or []),
    }


def _preset_title(value: str) -> str:
    return {
        "reset_key": "Сбросить трафик ключей",
        "rotate_link": "Заменить ссылку подписки",
        "extend_1d": "Продлить доступ на один день",
        "send_guide": "Отправить инструкцию",
    }[value]


def _subscription_type_title(value: str) -> str:
    return {
        "PAID": "Платный",
        "FREE": "Бесплатный",
        "MANUAL": "Ручной",
        "TRIAL": "Пробный",
    }.get(value.strip().upper(), "Неизвестно")


def _key_state_title(value: str) -> str:
    return {
        "active": "Активен",
        "rotation_requested": "Ожидает ротации",
        "revoked": "Отозван",
    }.get(value.strip().lower(), "Неизвестно")


def _bulk_action_title(value: str) -> str:
    return {
        "disable": "Выключить ключи",
        "enable": "Включить ключи",
        "reset": "Сбросить трафик",
        "resync": "Синхронизировать подписку",
    }[value]


def _ticket_status_title(value: str) -> str:
    return {
        "open": "Открыто",
        "in_progress": "В работе",
        "closed": "Закрыто",
    }[value]


def _manual_create_preview(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    return _simple_preview(
        "Будет создан ручной пользователь.",
        {"manual_users": int(state.public_snapshot["manual_users"])},
        {
            "manual_users": int(state.public_snapshot["manual_users"]) + 1,
            "days": int(payload["days"]),
            "display_name_length": int(payload["display_name"]["length"]),
        },
    )


def _extend_preview(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    return _simple_preview(
        f"Срок доступа пользователя {state.context['tg_id']} изменится на {payload['delta_days']} дн.",
        state.public_snapshot,
        {"delta_days": int(payload["delta_days"]), "allow_deactivate": bool(payload["allow_deactivate"])},
        ["Отрицательное продление может деактивировать доступ."] if int(payload["delta_days"]) < 0 else [],
    )


def _block_preview(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    active = not bool(payload["blocked"])
    return _simple_preview(
        f"Доступ пользователя {state.context['tg_id']} будет {'заблокирован' if payload['blocked'] else 'разблокирован'}.",
        state.public_snapshot,
        {**state.public_snapshot, "is_active": active},
        ["Изменение будет отправлено во внешнюю панель."],
    )


def _regenerate_preview(state: EntityState, _payload: Mapping[str, Any]) -> dict[str, Any]:
    return _simple_preview(
        f"Токен подписки пользователя {state.context['tg_id']} будет заменён.",
        state.public_snapshot,
        {"token": "будет заменён", "panel_sync": "будет выполнена"},
        ["Старая ссылка перестанет работать. Токен в предпросмотре не показывается."],
    )


def _delete_preview(state: EntityState, _payload: Mapping[str, Any]) -> dict[str, Any]:
    return _simple_preview(
        f"Ручной/тестовый пользователь {state.context['tg_id']} будет удалён.",
        state.public_snapshot,
        {"exists": False},
        ["Связанные привязки, правила и история ключей будут удалены."],
    )


def _key_toggle_preview(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    return _simple_preview(
        f"Ключ пользователя {state.context['tg_id']} на ноде {payload['node_code'].upper()} будет {'включён' if payload['enable'] else 'выключен'}.",
        state.public_snapshot,
        {"node_code": payload["node_code"], "enabled": bool(payload["enable"])},
    )


def _key_reset_preview(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    return _simple_preview(
        f"Трафик ключа пользователя {state.context['tg_id']} на ноде {payload['node_code'].upper()} будет сброшен.",
        state.public_snapshot,
        {"node_code": payload["node_code"], "traffic": "сброшен"},
    )


def _key_resync_preview(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    return _simple_preview(
        f"Идентификатор подписки (subId) ключа пользователя {state.context['tg_id']} на ноде {payload['node_code'].upper()} будет синхронизирован.",
        state.public_snapshot,
        {"node_code": payload["node_code"], "sub_id": "будет синхронизирован"},
    )


def _key_limits_preview(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    return _simple_preview(
        f"Лимиты ключа пользователя {state.context['tg_id']} на ноде {payload['node_code'].upper()} будут обновлены.",
        state.public_snapshot,
        {key: value for key, value in payload.items() if key != "node_code"},
        ["После сохранения лимиты будут отправлены во внешнюю панель."] if payload["apply_now"] else [],
    )


def _loyalty_preview(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    return _simple_preview(
        f"Пользователю {state.context['tg_id']} будет начислена награда лояльности.",
        state.public_snapshot,
        {"tier_days": int(payload["tier_days"]), "expiry": "будет продлён"},
    )


def _preset_preview(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    title = _preset_title(str(payload["preset"]))
    return _simple_preview(
        f"Для пользователя {state.context['tg_id']} будет выполнен сценарий «{title}».",
        state.public_snapshot,
        {"scenario": title},
        ["Сценарий может изменить ключи или отправить сообщение пользователю."],
    )


def _bulk_preview(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    action_title = _bulk_action_title(str(payload["action"]))
    warnings = ["Выборка пользователей зафиксирована хэшем и количеством."]
    if int(state.context["selected_count"]) > 50 and not bool(payload["force"]):
        warnings.append("Для выборки больше 50 пользователей нужен force=true.")
    return _simple_preview(
        f"Массовое действие «{action_title}» затронет {state.context['selected_count']} пользователей.",
        {
            "selected_count": int(state.context["selected_count"]),
            "selection_hash": str(state.context["selection_hash"]),
        },
        {"action_title": action_title, "dry_run": bool(payload["dry_run"])},
        warnings,
    )


def _message_preview(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    return _simple_preview(
        f"Пользователю {state.context['tg_id']} будет отправлено сообщение.",
        {"tg_id": int(state.context["tg_id"])},
        {"message_length": int(payload["text"]["length"])},
        ["Текст сообщения не хранится в защищённом намерении и аудите."],
    )


def _broadcast_preview(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    count = int(state.context["recipient_count"])
    return _simple_preview(
        f"Рассылка будет отправлена {count} зафиксированным получателям.",
        {
            "recipient_count": count,
            "recipient_hash": str(state.context["recipient_hash"]),
        },
        {
            "segment": str(payload["segment"]),
            "limit": int(payload["limit"]),
            "message_sha256": str(payload["message_sha256"]),
            "message_length": int(payload["message_length"]),
        },
        [
            "Список получателей зафиксирован на этапе предпросмотра.",
            "Повторная отправка после неопределённого результата запрещена.",
        ],
    )


def _ticket_reply_preview(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    return _simple_preview(
        f"В обращение #{state.context['ticket_id']} будет добавлен ответ оператора.",
        state.public_snapshot,
        {
            "status": "В работе",
            "body_length": int(payload["body"]["length"]),
            "media_type": "Есть" if payload["media_type"] or payload["attachment_id"]["length"] else "Нет",
            "has_attachment_id": bool(payload["attachment_id"]["length"]),
            "has_media_file_id": bool(payload["media_file_id"]["length"]),
            "media_payload_length": int(payload["media_payload"]["length"]),
        },
        ["Текст и идентификаторы вложений не хранятся в защищённом намерении и аудите."],
    )


def _ticket_status_preview(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    warnings = ["После сохранения пользователю будет отправлено уведомление."] if payload["status"] == "closed" else []
    return _simple_preview(
        f"Статус обращения #{state.context['ticket_id']} будет изменён.",
        state.public_snapshot,
        {
            **state.public_snapshot,
            "status": _ticket_status_title(str(payload["status"])),
        },
        warnings,
    )


def _key_rotate_preview(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    before = dict(state.public_snapshot)
    return _simple_preview(
        f"Для ключа {state.context['key_id']} будет {'показан план ротации' if payload['dry_run'] else 'создана задача ротации'}.",
        before,
        {
            "state": before["state"] if payload["dry_run"] else "Ожидает ротации",
            "dry_run": payload["dry_run"],
        },
    )


def _user_external_context(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    policies = {
        str(row.node_code or "").strip().lower(): (
            int(row.hard_cap_gb) if row.hard_cap_gb is not None else None
        )
        for row in state.context.get("key_policies", [])
    }
    return {
        "tg_id": int(state.context["tg_id"]),
        "user_uuid": str(state.context.get("user_uuid") or ""),
        "sub_token": str(state.context.get("sub_token") or ""),
        "hard_caps": policies,
    }


def _manual_create_external_context(state: EntityState, _payload: Mapping[str, Any]) -> dict[str, Any]:
    return {"candidate_tg_id": int(state.context["candidate_tg_id"])}


def _bulk_external_context(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "selected_tg_ids": list(state.context["selected_tg_ids"]),
        "selection_hash": str(state.context["selection_hash"]),
        "action": str(payload["action"]),
        "node_codes": list(payload["node_codes"]),
        "dry_run": bool(payload["dry_run"]),
        "force": bool(payload["force"]),
    }


def _ticket_external_context(state: EntityState, _payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "ticket_id": int(state.context["ticket_id"]),
        "user_tg_id": int(state.context["user_tg_id"]),
    }


def _broadcast_external_context(
    state: EntityState,
    _payload: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "selected_tg_ids": list(state.context["selected_tg_ids"]),
        "recipient_count": int(state.context["recipient_count"]),
        "recipient_hash": str(state.context["recipient_hash"]),
    }


def _audit_user_target(state: EntityState, _payload: Mapping[str, Any]) -> int | None:
    return int(state.context["tg_id"])


def _audit_manual_create_target(state: EntityState, _payload: Mapping[str, Any]) -> int | None:
    return int(state.context["candidate_tg_id"])


def _manual_create_audit_meta(
    _state: EntityState,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    display_name = payload["display_name"]
    return {
        "days": int(payload["days"]),
        "display_name_sha256": str(display_name["sha256"]),
        "display_name_length": int(display_name["length"]),
    }


def _audit_ticket_target(state: EntityState, _payload: Mapping[str, Any]) -> int | None:
    return int(state.context["user_tg_id"])


def _audit_key_target(state: EntityState, _payload: Mapping[str, Any]) -> int | None:
    return int(state.context["tg_id"])


def _safe_user_audit_meta(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    meta: dict[str, Any] = {"tg_id": int(state.context["tg_id"])}
    for key in (
        "node_code",
        "preset",
        "tier_days",
        "delta_days",
        "burst_mbps",
        "soft_cap_gb",
        "hard_cap_gb",
        "notify_soft",
        "notify_hard",
        "auto_disable_on_hard",
        "apply_now",
        "blocked",
        "enable",
    ):
        if key in payload:
            meta[key] = payload[key]
    return meta


def _bulk_audit_meta(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "selection_hash": str(state.context["selection_hash"]),
        "selected_count": int(state.context["selected_count"]),
        "action": str(payload["action"]),
        "dry_run": bool(payload["dry_run"]),
        "forced": bool(payload["force"]),
    }


def _ticket_audit_meta(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "ticket_id": int(state.context["ticket_id"]),
        "user_tg_id": int(state.context["user_tg_id"]),
    }
    if "status" in payload:
        meta["status"] = str(payload["status"])
    for key in ("body", "attachment_id", "media_file_id", "media_payload"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            meta[f"{key}_sha256"] = str(value.get("sha256") or "")
            meta[f"{key}_length"] = int(value.get("length") or 0)
    if "media_type" in payload:
        meta["media_type"] = payload.get("media_type")
    return meta


def _message_audit_meta(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    text_meta = payload["text"]
    return {
        "tg_id": int(state.context["tg_id"]),
        "message_sha256": str(text_meta["sha256"]),
        "message_length": int(text_meta["length"]),
    }


def _broadcast_audit_meta(
    state: EntityState,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "segment": str(payload["segment"]),
        "limit": int(payload["limit"]),
        "requested_tg_ids_hash": str(payload["requested_tg_ids_hash"]),
        "message_sha256": str(payload["message_sha256"]),
        "message_length": int(payload["message_length"]),
        "recipient_hash": str(state.context["recipient_hash"]),
        "recipient_count": int(state.context["recipient_count"]),
    }


def _key_audit_meta(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "key_id": int(state.context["key_id"]),
        "tg_id": int(state.context["tg_id"]),
        "dry_run": bool(payload["dry_run"]),
        "reason_sha256": str(payload["reason"]["sha256"]),
        "reason_length": int(payload["reason"]["length"]),
    }


def _key_limits_executor_kind(payload: Mapping[str, Any]) -> str:
    return "external" if bool(payload["apply_now"]) else "db"


def _preset_executor_kind(payload: Mapping[str, Any]) -> str:
    return "db" if payload["preset"] == "extend_1d" else "external"


def _bulk_executor_kind(payload: Mapping[str, Any]) -> str:
    return "db" if bool(payload["dry_run"]) else "external"


def _preset_audit_action(payload: Mapping[str, Any]) -> str:
    return f"admin_operator_{payload['preset']}"


def _provider_quota_node_state(node: Node | None) -> str:
    if node is None:
        return "missing"
    if not bool(node.enabled):
        return "disabled"
    if bool(node.is_draining) or not bool(node.accepting_new_clients):
        return "draining"
    return "active"


def _provider_quota_projection(session, *, node_code: str, config: Mapping[str, Any]) -> dict[str, Any]:
    now = _utcnow().astimezone(timezone.utc).replace(tzinfo=None)
    cycle_start, cycle_end = provider_quota_cycle_bounds(
        now=now,
        reset_day=int(config["reset_day"]),
        timezone_name=str(config["timezone"]),
    )
    used_bytes, sample_count, source = provider_quota_usage_bytes(
        s=session,
        node_code=node_code,
        cycle_start=cycle_start,
        cycle_end=cycle_end,
    )
    included_bytes = int(config["included_bytes"])
    projected_at: str | None = None
    elapsed_seconds = max(0.0, (now - cycle_start).total_seconds())
    if included_bytes > 0 and used_bytes >= included_bytes:
        projected_at = now.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    elif used_bytes > 0 and sample_count >= 2 and elapsed_seconds > 0 and included_bytes > used_bytes:
        rate = float(used_bytes) / elapsed_seconds
        if rate > 0:
            projected = now + timedelta(seconds=(included_bytes - used_bytes) / rate)
            projected_at = projected.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "used_bytes": int(used_bytes),
        "used_gb": _quota_bytes_to_gb(used_bytes),
        "sample_count": int(sample_count),
        "source": source,
        "cycle_start": cycle_start.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        "cycle_end": cycle_end.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        "projected_exhaustion_at": projected_at,
    }


def _provider_quota_config(row: ProviderTrafficQuota) -> dict[str, Any]:
    return {
        "included_bytes": max(0, int(row.included_bytes or 0)),
        "reset_day": int(row.reset_day or 1),
        "timezone": str(row.timezone or "UTC"),
        "warning_ratio": round(float(row.warning_ratio or 0.8), 6),
        "critical_ratio": round(float(row.critical_ratio or 0.95), 6),
        "enabled": bool(row.enabled),
        "notes": str(row.notes or "") or None,
    }


def _provider_quota_public_snapshot(
    *,
    node_code: str,
    node: Node | None,
    quota: ProviderTrafficQuota | None,
    config: Mapping[str, Any] | None,
    projection: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return {
        "node_code": node_code.upper(),
        "configured": quota is not None,
        "node_status": _provider_quota_node_state(node),
        "included_gb": _quota_bytes_to_gb(int(config["included_bytes"])) if config is not None else None,
        "used_gb": projection.get("used_gb") if projection is not None else None,
        "reset_day": int(config["reset_day"]) if config is not None else None,
        "timezone": str(config["timezone"]) if config is not None else None,
        "warning_ratio": float(config["warning_ratio"]) if config is not None else None,
        "critical_ratio": float(config["critical_ratio"]) if config is not None else None,
        "enabled": bool(config["enabled"]) if config is not None else False,
        "notes_present": bool(config and config.get("notes")),
        "projected_exhaustion_at": projection.get("projected_exhaustion_at") if projection is not None else None,
        "updated_at": _safe_iso(quota.updated_at) if quota is not None else None,
    }


def _provider_quota_entity_state(
    session,
    target_id: str,
    payload: Mapping[str, Any],
    for_update: bool,
    *,
    mode: str,
) -> EntityState:
    node_code = _normalize_node_code(target_id)
    query = session.query(ProviderTrafficQuota).filter(func.lower(ProviderTrafficQuota.node_code) == node_code)
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    quota = query.first()
    if mode == "create" and quota is not None:
        raise ActionIntentError(
            "target_exists",
            status_code=409,
            message="Квота провайдера для этой ноды уже настроена.",
        )
    if mode in {"update", "delete"} and quota is None:
        raise ActionIntentError(
            "target_not_found",
            status_code=404,
            message="Квота провайдера не найдена.",
        )
    node = session.query(Node).filter(func.lower(Node.code) == node_code).first()
    current_config = _provider_quota_config(quota) if quota is not None else None
    current_projection = (
        _provider_quota_projection(session, node_code=node_code, config=current_config)
        if current_config is not None
        else None
    )
    before = _provider_quota_public_snapshot(
        node_code=node_code,
        node=node,
        quota=quota,
        config=current_config,
        projection=current_projection,
    )
    proposed_config: dict[str, Any] | None = None
    if mode == "delete":
        after = {
            **before,
            "configured": False,
            "included_gb": None,
            "reset_day": None,
            "timezone": None,
            "warning_ratio": None,
            "critical_ratio": None,
            "enabled": False,
            "notes_present": False,
            "projected_exhaustion_at": None,
            "updated_at": None,
        }
    else:
        if mode == "create":
            if str(payload.get("node_code") or "") != node_code:
                raise ActionIntentError(
                    "invalid_payload",
                    status_code=422,
                    message="Код ноды в теле не совпадает с целью действия.",
                )
            proposed_config = {
                key: payload[key]
                for key in (
                    "included_bytes",
                    "reset_day",
                    "timezone",
                    "warning_ratio",
                    "critical_ratio",
                    "enabled",
                    "notes",
                )
            }
        else:
            assert current_config is not None
            proposed_config = {**current_config, **dict(payload)}
        if float(proposed_config["warning_ratio"]) >= float(proposed_config["critical_ratio"]):
            raise ActionIntentError(
                "invalid_payload",
                status_code=422,
                message="Порог предупреждения должен быть ниже критического.",
            )
        proposed_projection = _provider_quota_projection(session, node_code=node_code, config=proposed_config)
        after = _provider_quota_public_snapshot(
            node_code=node_code,
            node=node,
            quota=quota,
            config=proposed_config,
            projection=proposed_projection,
        ) | {"configured": True}

    return EntityState(
        entity=quota,
        version_snapshot={
            "quota": (
                {
                    "id": int(quota.id),
                    **{key: value for key, value in (current_config or {}).items() if key != "notes"},
                    "notes_sha256": hashlib.sha256(str((current_config or {}).get("notes") or "").encode("utf-8")).hexdigest(),
                    "updated_at": _safe_iso(quota.updated_at),
                }
                if quota is not None
                else None
            ),
            "node": (
                {
                    "id": int(node.id),
                    "enabled": bool(node.enabled),
                    "accepting_new_clients": bool(node.accepting_new_clients),
                    "is_draining": bool(node.is_draining),
                }
                if node is not None
                else None
            ),
        },
        public_snapshot=before,
        context={
            "node_code": node_code,
            "quota_id": int(quota.id) if quota is not None else None,
            "proposed_config": proposed_config,
            "after_snapshot": after,
        },
    )


def _provider_quota_create_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _provider_quota_entity_state(session, target_id, payload, for_update, mode="create")


def _provider_quota_update_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _provider_quota_entity_state(session, target_id, payload, for_update, mode="update")


def _provider_quota_delete_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _provider_quota_entity_state(session, target_id, payload, for_update, mode="delete")


def _provider_quota_preview(state: EntityState, _payload: Mapping[str, Any]) -> dict[str, Any]:
    node_code = str(state.context["node_code"]).upper()
    configured = bool(state.public_snapshot["configured"])
    return _simple_preview(
        f"Квота провайдера для ноды {node_code} будет {'обновлена' if configured else 'создана'}.",
        state.public_snapshot,
        dict(state.context["after_snapshot"]),
        ["Прогноз исчерпания рассчитан сервером по доступным накопительным измерениям."],
    )


def _provider_quota_delete_preview(state: EntityState, _payload: Mapping[str, Any]) -> dict[str, Any]:
    node_code = str(state.context["node_code"]).upper()
    return _simple_preview(
        f"Квота провайдера для ноды {node_code} будет удалена.",
        state.public_snapshot,
        dict(state.context["after_snapshot"]),
        ["Контроль лимита и предупреждения прекратятся; состояние самой ноды не изменится."],
    )


def _provider_quota_challenge(state: EntityState, _payload: Mapping[str, Any]) -> str:
    return str(state.context["node_code"]).upper()


def _provider_quota_audit_meta(state: EntityState, _payload: Mapping[str, Any]) -> dict[str, Any]:
    return {"node_code": str(state.context["node_code"]), "quota_id": state.context.get("quota_id")}


def _ticket_status_post_commit(state: EntityState, payload: Mapping[str, Any]) -> dict[str, Any] | None:
    if payload["status"] != "closed":
        return None
    return {
        "ticket_id": int(state.context["ticket_id"]),
        "user_tg_id": int(state.context["user_tg_id"]),
    }


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
    "provider_quota.create": ActionPolicy(
        action="provider_quota.create",
        target_type="provider_quota",
        risk_level="L2",
        payload_normalizer=_normalize_provider_quota_create_payload,
        runtime_payload_normalizer=_normalize_provider_quota_create_runtime,
        entity_state_builder=_provider_quota_create_state,
        preview_builder=_provider_quota_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_l2_challenge,
        executor_kind="db",
        audit_action="admin_provider_quota_create",
        audit_meta_builder=_provider_quota_audit_meta,
    ),
    "provider_quota.update": ActionPolicy(
        action="provider_quota.update",
        target_type="provider_quota",
        risk_level="L2",
        payload_normalizer=_normalize_provider_quota_update_payload,
        runtime_payload_normalizer=_normalize_provider_quota_update_runtime,
        entity_state_builder=_provider_quota_update_state,
        preview_builder=_provider_quota_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_l2_challenge,
        executor_kind="db",
        audit_action="admin_provider_quota_update",
        audit_meta_builder=_provider_quota_audit_meta,
    ),
    "provider_quota.delete": ActionPolicy(
        action="provider_quota.delete",
        target_type="provider_quota",
        risk_level="L3",
        payload_normalizer=_normalize_empty_payload,
        entity_state_builder=_provider_quota_delete_state,
        preview_builder=_provider_quota_delete_preview,
        challenge_kind="exact_node_code",
        challenge_builder=_provider_quota_challenge,
        executor_kind="db",
        audit_action="admin_provider_quota_delete",
        audit_meta_builder=_provider_quota_audit_meta,
    ),
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
    ),
    "user.manual_create": ActionPolicy(
        action="user.manual_create",
        target_type="user",
        risk_level="L2",
        payload_normalizer=_normalize_manual_create_payload,
        runtime_payload_normalizer=_normalize_manual_create_runtime,
        entity_state_builder=_manual_create_entity_state,
        preview_builder=_manual_create_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_l2_challenge,
        executor_kind="external",
        audit_action="admin_manual_create",
        external_context_builder=_manual_create_external_context,
        audit_target_builder=_audit_manual_create_target,
        audit_meta_builder=_manual_create_audit_meta,
    ),
    "user.extend": ActionPolicy(
        action="user.extend",
        target_type="user",
        risk_level="L2",
        payload_normalizer=_normalize_extend_payload,
        entity_state_builder=_user_entity_state,
        preview_builder=_extend_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_l2_challenge,
        executor_kind="db",
        audit_action="admin_manual_extend",
        audit_target_builder=_audit_user_target,
        audit_meta_builder=_safe_user_audit_meta,
    ),
    "user.key_toggle": ActionPolicy(
        action="user.key_toggle",
        target_type="user",
        risk_level="L2",
        payload_normalizer=_normalize_user_key_toggle_payload,
        entity_state_builder=_user_entity_state,
        preview_builder=_key_toggle_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_l2_challenge,
        executor_kind="external",
        audit_action="admin_user_key_toggle",
        external_context_builder=_user_external_context,
        audit_target_builder=_audit_user_target,
        audit_meta_builder=_safe_user_audit_meta,
    ),
    "user.key_limits": ActionPolicy(
        action="user.key_limits",
        target_type="user",
        risk_level="L2",
        payload_normalizer=_normalize_key_limits_payload,
        entity_state_builder=_user_entity_state,
        preview_builder=_key_limits_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_l2_challenge,
        executor_kind="db",
        executor_kind_builder=_key_limits_executor_kind,
        audit_action="admin_user_key_limits_put",
        external_context_builder=_user_external_context,
        audit_target_builder=_audit_user_target,
        audit_meta_builder=_safe_user_audit_meta,
    ),
    "user.key_reset_traffic": ActionPolicy(
        action="user.key_reset_traffic",
        target_type="user",
        risk_level="L2",
        payload_normalizer=_normalize_user_key_node_payload,
        entity_state_builder=_user_entity_state,
        preview_builder=_key_reset_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_l2_challenge,
        executor_kind="external",
        audit_action="admin_user_key_reset_traffic",
        external_context_builder=_user_external_context,
        audit_target_builder=_audit_user_target,
        audit_meta_builder=_safe_user_audit_meta,
    ),
    "user.key_resync_subid": ActionPolicy(
        action="user.key_resync_subid",
        target_type="user",
        risk_level="L2",
        payload_normalizer=_normalize_user_key_node_payload,
        entity_state_builder=_user_entity_state,
        preview_builder=_key_resync_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_l2_challenge,
        executor_kind="external",
        audit_action="admin_user_key_resync_subid",
        external_context_builder=_user_external_context,
        audit_target_builder=_audit_user_target,
        audit_meta_builder=_safe_user_audit_meta,
    ),
    "user.loyalty_grant": ActionPolicy(
        action="user.loyalty_grant",
        target_type="user",
        risk_level="L2",
        payload_normalizer=_normalize_loyalty_payload,
        entity_state_builder=_user_entity_state,
        preview_builder=_loyalty_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_l2_challenge,
        executor_kind="external",
        audit_action="admin_user_loyalty_grant",
        external_context_builder=_user_external_context,
        audit_target_builder=_audit_user_target,
        audit_meta_builder=_safe_user_audit_meta,
    ),
    "user.preset_run": ActionPolicy(
        action="user.preset_run",
        target_type="user",
        risk_level="L2",
        payload_normalizer=_normalize_preset_payload,
        entity_state_builder=_user_entity_state,
        preview_builder=_preset_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_l2_challenge,
        executor_kind="external",
        executor_kind_builder=_preset_executor_kind,
        audit_action="admin_user_preset_run",
        audit_action_builder=_preset_audit_action,
        external_context_builder=_user_external_context,
        audit_target_builder=_audit_user_target,
        audit_meta_builder=_safe_user_audit_meta,
    ),
    "user.block": ActionPolicy(
        action="user.block",
        target_type="user",
        risk_level="L3",
        payload_normalizer=_normalize_block_payload,
        entity_state_builder=_user_entity_state,
        preview_builder=_block_preview,
        challenge_kind="exact_tg_id",
        challenge_builder=_user_challenge,
        executor_kind="external",
        audit_action="admin_manual_block",
        external_context_builder=_user_external_context,
        audit_target_builder=_audit_user_target,
        audit_meta_builder=_safe_user_audit_meta,
    ),
    "user.regenerate_token": ActionPolicy(
        action="user.regenerate_token",
        target_type="user",
        risk_level="L3",
        payload_normalizer=_normalize_empty_payload,
        entity_state_builder=_user_entity_state,
        preview_builder=_regenerate_preview,
        challenge_kind="exact_tg_id",
        challenge_builder=_user_challenge,
        executor_kind="external",
        audit_action="admin_manual_regen_token",
        external_context_builder=_user_external_context,
        audit_target_builder=_audit_user_target,
        audit_meta_builder=_safe_user_audit_meta,
    ),
    "user.safe_delete": ActionPolicy(
        action="user.safe_delete",
        target_type="user",
        risk_level="L3",
        payload_normalizer=_normalize_safe_delete_payload,
        entity_state_builder=_manual_delete_user_entity_state,
        preview_builder=_delete_preview,
        challenge_kind="exact_tg_id",
        challenge_builder=_user_challenge,
        executor_kind="external",
        audit_action="admin_safe_delete_test_user",
        external_context_builder=_user_external_context,
        audit_target_builder=_audit_user_target,
        audit_meta_builder=_safe_user_audit_meta,
    ),
    "user.delete_test": ActionPolicy(
        action="user.delete_test",
        target_type="user",
        risk_level="L3",
        payload_normalizer=_normalize_empty_payload,
        entity_state_builder=_manual_delete_user_entity_state,
        preview_builder=_delete_preview,
        challenge_kind="exact_tg_id",
        challenge_builder=_user_challenge,
        executor_kind="external",
        audit_action="admin_safe_delete_test_user",
        external_context_builder=_user_external_context,
        audit_target_builder=_audit_user_target,
        audit_meta_builder=_safe_user_audit_meta,
    ),
    "user.bulk_key_action": ActionPolicy(
        action="user.bulk_key_action",
        target_type="users",
        risk_level="L3",
        payload_normalizer=_normalize_bulk_payload,
        runtime_payload_normalizer=_normalize_bulk_runtime,
        entity_state_builder=_bulk_entity_state,
        preview_builder=_bulk_preview,
        challenge_kind="exact_tg_id",
        challenge_builder=_bulk_challenge,
        executor_kind="external",
        executor_kind_builder=_bulk_executor_kind,
        audit_action="admin_bulk_key_action",
        external_context_builder=_bulk_external_context,
        audit_meta_builder=_bulk_audit_meta,
    ),
    "key.rotate": ActionPolicy(
        action="key.rotate",
        target_type="key",
        risk_level="L3",
        payload_normalizer=_normalize_key_rotate_payload,
        runtime_payload_normalizer=_normalize_key_rotate_runtime,
        entity_state_builder=_key_entity_state,
        preview_builder=_key_rotate_preview,
        challenge_kind="exact_key_id",
        challenge_builder=_key_challenge,
        executor_kind="db",
        audit_action="admin_key_rotate_request",
        audit_target_builder=_audit_key_target,
        audit_meta_builder=_key_audit_meta,
    ),
    "user.message": ActionPolicy(
        action="user.message",
        target_type="user",
        risk_level="L2",
        payload_normalizer=_normalize_message_payload,
        runtime_payload_normalizer=_normalize_message_runtime,
        entity_state_builder=_user_entity_state,
        preview_builder=_message_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_send_challenge,
        executor_kind="external",
        audit_action="admin_user_message",
        external_context_builder=_user_external_context,
        audit_target_builder=_audit_user_target,
        audit_meta_builder=_message_audit_meta,
    ),
    "broadcast.send": ActionPolicy(
        action="broadcast.send",
        target_type="broadcast",
        risk_level="L3",
        payload_normalizer=_normalize_broadcast_payload,
        runtime_payload_normalizer=_normalize_broadcast_runtime,
        entity_state_builder=_broadcast_entity_state,
        execution_state_builder=_broadcast_execution_state,
        preview_builder=_broadcast_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_send_challenge,
        executor_kind="external",
        audit_action="admin_broadcast",
        external_context_builder=_broadcast_external_context,
        audit_meta_builder=_broadcast_audit_meta,
    ),
    "ticket.reply": ActionPolicy(
        action="ticket.reply",
        target_type="ticket",
        risk_level="L2",
        payload_normalizer=_normalize_ticket_reply_payload,
        runtime_payload_normalizer=_normalize_ticket_reply_runtime,
        entity_state_builder=_ticket_entity_state,
        preview_builder=_ticket_reply_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_send_challenge,
        executor_kind="external",
        audit_action="admin_ticket_reply",
        external_context_builder=_ticket_external_context,
        audit_target_builder=_audit_ticket_target,
        audit_meta_builder=_ticket_audit_meta,
    ),
    "ticket.status": ActionPolicy(
        action="ticket.status",
        target_type="ticket",
        risk_level="L2",
        payload_normalizer=_normalize_ticket_status_payload,
        entity_state_builder=_ticket_entity_state,
        preview_builder=_ticket_status_preview,
        challenge_kind="exact_phrase",
        challenge_builder=_l2_challenge,
        executor_kind="db",
        audit_action="admin_ticket_status",
        audit_target_builder=_audit_ticket_target,
        audit_meta_builder=_ticket_audit_meta,
        post_commit_context_builder=_ticket_status_post_commit,
    ),
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
        if (
            not 1 <= len(selected) <= _MAX_BROADCAST_RECIPIENTS
            or selected != sorted(set(int(value) for value in selected))
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
            int(intent.admin_audit_id)
            if intent.admin_audit_id is not None
            else None
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
        claims = stored.get(_INTERNAL_TARGET_CLAIMS_KEY) if isinstance(stored, dict) else None
        if not isinstance(claims, dict) or set(claims) != {"kind", "tokens"}:
            return None
        if claims.get("kind") != "user_selection_v1":
            return None
        values = claims.get("tokens")
        if not isinstance(values, list) or not 1 <= len(values) <= _MAX_BULK_DETAILS:
            return None
        tokens = [str(value) for value in values]
        if (
            len(set(tokens)) != len(tokens)
            or any(_HEX_SHA256_RE.fullmatch(value) is None for value in tokens)
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
        selected = [str(int(value)) for value in state.context.get("selected_tg_ids", [])]
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


def _payment_reconcile_entity_state(
    session,
    target_id: str,
    payload: Mapping[str, Any],
    for_update: bool,
) -> EntityState:
    order_db_id = _integer_target(target_id, positive=True)
    query = session.query(ExternalOrder).filter(ExternalOrder.id == order_db_id)
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    order = query.first()
    if order is None:
        raise ActionIntentError(
            "target_not_found",
            status_code=404,
            message="Платёжный заказ не найден.",
        )

    event_rows = (
        session.query(
            ExternalPaymentEvent.id,
            ExternalPaymentEvent.event_type,
            ExternalPaymentEvent.external_id,
            ExternalPaymentEvent.order_id,
            ExternalPaymentEvent.signature_ok,
            ExternalPaymentEvent.processed_ok,
            ExternalPaymentEvent.created_at,
        )
        .filter(
            func.lower(ExternalPaymentEvent.provider)
            == str(order.provider or "").strip().lower(),
            ExternalPaymentEvent.order_id == str(order.order_id or ""),
        )
        .order_by(ExternalPaymentEvent.id.asc())
        .all()
    )
    event_versions = [
        {
            "id": int(row[0]),
            "event_type": str(row[1] or ""),
            "external_id_sha256": _semantic_hash(
                "admin-payment-event-id",
                str(row[2] or ""),
            ),
            "order_id": str(row[3] or ""),
            "signature_ok": bool(row[4]),
            "processed_ok": bool(row[5]),
            "created_at": _safe_iso(row[6]),
        }
        for row in event_rows
    ]
    callback_version_hash = _semantic_hash(
        "admin-payment-callback-version",
        event_versions,
    )
    status = str(order.status or "created").strip().lower()
    next_status = str(payload.get("status") or status).strip().lower()
    before = {
        "order_id": str(order.order_id or ""),
        "provider": str(order.provider or ""),
        "status": status,
        "amount": float(order.amount) if order.amount is not None else None,
        "currency": str(order.currency or "") or None,
        "callback_events": len(event_versions),
        "callback_state": (
            "processed"
            if event_versions and bool(event_versions[-1]["processed_ok"])
            else "requires_review"
            if event_versions
            else "missing"
        ),
    }
    after = {
        **before,
        "status": next_status,
        "operator_note_length": len(str(payload.get("note") or "")),
    }
    return EntityState(
        entity=order,
        version_snapshot={
            "id": int(order.id),
            "provider": str(order.provider or ""),
            "order_id": str(order.order_id or ""),
            "tg_id": int(order.tg_id) if order.tg_id is not None else None,
            "status": status,
            "paid_at": _safe_iso(order.paid_at),
            "amount": float(order.amount) if order.amount is not None else None,
            "currency": str(order.currency or ""),
            "meta_sha256": _semantic_hash(
                "admin-payment-order-meta",
                str(order.meta_json or ""),
            ),
            "callback_version_hash": callback_version_hash,
            "callback_events": len(event_versions),
        },
        public_snapshot=before,
        context={
            "order_db_id": int(order.id),
            "provider": str(order.provider or ""),
            "order_id": str(order.order_id or ""),
            "tg_id": int(order.tg_id) if order.tg_id is not None else None,
            "from_status": status,
            "to_status": next_status,
            "callback_version_hash": callback_version_hash,
            "after_snapshot": after,
        },
    )


def _payment_reconcile_preview(
    state: EntityState,
    _payload: Mapping[str, Any],
) -> dict[str, Any]:
    return _simple_preview(
        f"Сверка заказа {state.context['order_id']} у {state.context['provider']}.",
        state.public_snapshot,
        dict(state.context["after_snapshot"]),
        [
            "Провайдер, номер заказа, статус и версия callback зафиксированы сервером.",
            "Callback evidence не изменяется; новый платёж этим действием не создаётся.",
        ],
    )


def _payment_reconcile_audit_target(
    state: EntityState,
    _payload: Mapping[str, Any],
) -> int | None:
    value = state.context.get("tg_id")
    return int(value) if value is not None else None


def _payment_reconcile_audit_meta(
    state: EntityState,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    note = payload.get("note") if isinstance(payload.get("note"), Mapping) else {}
    return {
        "order_db_id": int(state.context["order_db_id"]),
        "provider": str(state.context["provider"]),
        "order_id": str(state.context["order_id"]),
        "from_status": str(state.context["from_status"]),
        "to_status": str(state.context["to_status"]),
        "callback_version_hash": str(state.context["callback_version_hash"]),
        "note_sha256": str(note.get("sha256") or ""),
        "note_length": int(note.get("length") or 0),
    }


ACTION_POLICIES["payment.reconcile"] = ActionPolicy(
    action="payment.reconcile",
    target_type="payment",
    risk_level="L2",
    payload_normalizer=_normalize_payment_reconcile_payload,
    runtime_payload_normalizer=_normalize_payment_reconcile_runtime,
    entity_state_builder=_payment_reconcile_entity_state,
    preview_builder=_payment_reconcile_preview,
    challenge_kind="exact_phrase",
    challenge_builder=_l2_challenge,
    executor_kind="db",
    audit_action="admin_payment_reconcile",
    audit_target_builder=_payment_reconcile_audit_target,
    audit_meta_builder=_payment_reconcile_audit_meta,
)


def _promo_snapshot(session, promo: PromoCode) -> dict[str, Any]:
    code = str(promo.code or "").upper()
    used_count = int(
        session.query(func.count(PromoUsage.id))
        .filter(func.upper(PromoUsage.promo_code) == code)
        .scalar()
        or 0
    )
    return {
        "promo_code": code,
        "promo_type": str(promo.promo_type or ""),
        "value": int(promo.value or 0),
        "uses_left": int(promo.uses_left or 0),
        "used_count": used_count,
        "expires_at": _safe_iso(promo.expires_at),
        "exists": True,
    }


def _promo_entity_state(
    session,
    target_id: str,
    payload: Mapping[str, Any],
    for_update: bool,
    *,
    mode: str,
) -> EntityState:
    target_code = _normalize_promo_code(target_id, field="target")
    if mode == "create" and str(payload.get("code") or "").upper() != target_code:
        raise ActionIntentError(
            "invalid_target",
            status_code=422,
            message="Цель должна совпадать с создаваемым промокодом.",
        )
    query = session.query(PromoCode).filter(func.upper(PromoCode.code) == target_code)
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    promo = query.first()
    if mode == "create" and promo is not None:
        raise ActionIntentError(
            "target_exists",
            status_code=409,
            message="Промокод уже существует.",
        )
    if mode != "create" and promo is None:
        raise ActionIntentError(
            "target_not_found",
            status_code=404,
            message="Промокод не найден.",
        )

    before = (
        _promo_snapshot(session, promo)
        if promo is not None
        else {
            "promo_code": target_code,
            "promo_type": None,
            "value": None,
            "uses_left": None,
            "used_count": None,
            "expires_at": None,
            "exists": False,
        }
    )
    if mode == "create":
        after = {
            "promo_code": str(payload["code"]),
            "promo_type": str(payload["promo_type"]),
            "value": int(payload["value"]),
            "uses_left": int(payload["uses_left"]),
            "used_count": 0,
            "expires_at": payload.get("expires_at"),
            "exists": True,
        }
    elif mode == "delete":
        after = {**before, "exists": False}
    else:
        after = {
            **before,
            "promo_code": str(payload.get("new_code") or before["promo_code"]),
            "promo_type": str(payload.get("promo_type") or before["promo_type"]),
            "value": int(payload.get("value", before["value"])),
            "uses_left": int(payload.get("uses_left", before["uses_left"])),
            "expires_at": (
                payload.get("expires_at")
                if "expires_at" in payload
                else before["expires_at"]
            ),
        }
        if str(after["promo_code"]).upper() != target_code:
            duplicate = (
                session.query(PromoCode.id)
                .filter(func.upper(PromoCode.code) == str(after["promo_code"]).upper())
                .first()
            )
            if duplicate is not None:
                raise ActionIntentError(
                    "target_exists",
                    status_code=409,
                    message="Новый промокод уже существует.",
                )

    version_snapshot = {
        "mode": mode,
        "promo_id": int(promo.id) if promo is not None else None,
        "before": before,
    }
    return EntityState(
        entity=promo,
        version_snapshot=version_snapshot,
        public_snapshot=before,
        context={
            "mode": mode,
            "promo_id": int(promo.id) if promo is not None else None,
            "from_code": target_code,
            "to_code": str(after["promo_code"]).upper(),
            "after_snapshot": after,
            "promo_state_hash": _semantic_hash("admin-promo-state", version_snapshot),
        },
    )


def _promo_create_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _promo_entity_state(session, target_id, payload, for_update, mode="create")


def _promo_update_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _promo_entity_state(session, target_id, payload, for_update, mode="update")


def _promo_delete_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _promo_entity_state(session, target_id, payload, for_update, mode="delete")


def _promo_preview(state: EntityState, _payload: Mapping[str, Any]) -> dict[str, Any]:
    mode = str(state.context["mode"])
    action_title = {"create": "создан", "update": "изменён", "delete": "удалён"}[mode]
    return _simple_preview(
        f"Промокод {state.context['from_code']} будет {action_title}.",
        state.public_snapshot,
        dict(state.context["after_snapshot"]),
        ["Код, тип, значение, остаток использований и срок зафиксированы сервером."],
    )


def _promo_challenge(state: EntityState, _payload: Mapping[str, Any]) -> str:
    return str(state.context["from_code"])


def _promo_audit_meta(state: EntityState, _payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "promo_id": state.context.get("promo_id"),
        "from_code": str(state.context["from_code"]),
        "to_code": str(state.context["to_code"]),
        "promo_state_hash": str(state.context["promo_state_hash"]),
    }


ACTION_POLICIES.update(
    {
        "promo.create": ActionPolicy(
            action="promo.create",
            target_type="promo",
            risk_level="L2",
            payload_normalizer=_normalize_promo_create_payload,
            entity_state_builder=_promo_create_state,
            preview_builder=_promo_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_l2_challenge,
            executor_kind="db",
            audit_action="admin_promo_create",
            audit_meta_builder=_promo_audit_meta,
        ),
        "promo.update": ActionPolicy(
            action="promo.update",
            target_type="promo",
            risk_level="L2",
            payload_normalizer=_normalize_promo_update_payload,
            entity_state_builder=_promo_update_state,
            preview_builder=_promo_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_l2_challenge,
            executor_kind="db",
            audit_action="admin_promo_update",
            audit_meta_builder=_promo_audit_meta,
        ),
        "promo.delete": ActionPolicy(
            action="promo.delete",
            target_type="promo",
            risk_level="L3",
            payload_normalizer=_normalize_empty_payload,
            entity_state_builder=_promo_delete_state,
            preview_builder=_promo_preview,
            challenge_kind="exact_promo_code",
            challenge_builder=_promo_challenge,
            executor_kind="db",
            audit_action="admin_promo_delete",
            audit_meta_builder=_promo_audit_meta,
        ),
    }
)


def _referral_wait_hours() -> int:
    try:
        return max(1, int(os.getenv("REFERRAL_ANTIFRAUD_MAX_WAIT_HOURS", "168")))
    except (TypeError, ValueError):
        return 168


def _referral_process_entity_state(
    session,
    target_id: str,
    payload: Mapping[str, Any],
    for_update: bool,
) -> EntityState:
    if str(target_id).strip().lower() != "ready":
        raise ActionIntentError(
            "invalid_target",
            status_code=422,
            message="Целью должна быть готовая реферальная очередь.",
        )
    now = _utcnow()
    db_now = now.replace(tzinfo=None)
    query = (
        session.query(ReferralBonusQueue)
        .filter(
            ReferralBonusQueue.status == "pending",
            ReferralBonusQueue.ready_at <= db_now,
        )
        .order_by(ReferralBonusQueue.ready_at.asc(), ReferralBonusQueue.id.asc())
        .limit(int(payload["limit"]))
    )
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    rows = query.all()
    items: list[dict[str, Any]] = []
    for row in rows:
        referred = session.query(User).filter(User.tg_id == int(row.referred_tg_id)).first()
        referrer = session.query(User).filter(User.tg_id == int(row.referrer_tg_id)).first()
        queued_at = _as_utc(row.queued_at or now)
        has_activity = bool(
            referred
            and session.query(Event.id)
            .filter(
                Event.tg_id == int(row.referred_tg_id),
                Event.created_at >= (row.queued_at or (db_now - timedelta(days=1))),
                Event.event_name.in_(["connected_ok", "clicked_connect"]),
            )
            .first()
            is not None
        )
        age_hours = max(0, int((now - queued_at).total_seconds() // 3600))
        if referred is None or referrer is None:
            basis = "rejected_missing_user"
        elif not has_activity and not bool(payload["force_without_activity"]):
            basis = (
                "rejected_no_activity"
                if age_hours >= _referral_wait_hours()
                else "waiting_for_activity"
            )
        elif not (
            bool(referrer.is_active)
            and str(referrer.sub_type or "").strip().upper() == "PAID"
            and referrer.expiry_at is not None
            and _as_utc(referrer.expiry_at) > now
        ):
            basis = "rejected_referrer_inactive"
        else:
            basis = "reward_ready"
        items.append(
            {
                "queue_id": int(row.id),
                "order_id": str(row.order_id or ""),
                "referrer_tg_id": int(row.referrer_tg_id),
                "referred_tg_id": int(row.referred_tg_id),
                "queued_at": _safe_iso(row.queued_at),
                "ready_at": _safe_iso(row.ready_at),
                "status": str(row.status or ""),
                "has_activity": has_activity,
                "basis": basis,
                "referrer_state_hash": _semantic_hash(
                    "admin-referral-referrer-state",
                    {
                        "exists": referrer is not None,
                        "active": bool(referrer.is_active) if referrer is not None else None,
                        "sub_type": str(referrer.sub_type or "") if referrer is not None else None,
                        "expiry_at": _safe_iso(referrer.expiry_at) if referrer is not None else None,
                    },
                ),
                "referred_exists": referred is not None,
            }
        )
    selection_hash = _semantic_hash("admin-referral-selection", items)
    first = items[0] if items else None
    before = {
        "selection_count": len(items),
        "queue_id": first["queue_id"] if first else None,
        "order_id": first["order_id"] if first else None,
        "referrer_tg_id": first["referrer_tg_id"] if first else None,
        "referred_tg_id": first["referred_tg_id"] if first else None,
        "decision_basis": first["basis"] if first else "missing",
    }
    return EntityState(
        entity=rows,
        version_snapshot={
            "items": items,
            "selection_hash": selection_hash,
            "force_without_activity": bool(payload["force_without_activity"]),
        },
        public_snapshot=before,
        context={
            "items": items,
            "selected_count": len(items),
            "selection_hash": selection_hash,
            "after_snapshot": {**before, "status": "process"},
        },
    )


def _referral_process_preview(state: EntityState, _payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **_simple_preview(
            "Обработать зафиксированную реферальную очередь.",
            state.public_snapshot,
            dict(state.context["after_snapshot"]),
            [
                "Основание решения рассчитано сервером по пользователям и событиям активности.",
                "Действие продлевает существующий доступ реферера и не создаёт платёж.",
            ],
        ),
        "selection": {
            "selection_count": int(state.context["selected_count"]),
            "selection_hash": str(state.context["selection_hash"]),
        },
    }


def _referral_process_audit_meta(state: EntityState, _payload: Mapping[str, Any]) -> dict[str, Any]:
    items = list(state.context["items"])
    return {
        "queue_ids": [int(item["queue_id"]) for item in items],
        "order_ids_hash": _semantic_hash(
            "admin-referral-order-ids",
            [str(item["order_id"]) for item in items],
        ),
        "selection_hash": str(state.context["selection_hash"]),
        "selected_count": int(state.context["selected_count"]),
    }


ACTION_POLICIES["referral.process"] = ActionPolicy(
    action="referral.process",
    target_type="referral_queue",
    risk_level="L2",
    payload_normalizer=_normalize_referral_process_payload,
    entity_state_builder=_referral_process_entity_state,
    preview_builder=_referral_process_preview,
    challenge_kind="exact_phrase",
    challenge_builder=_l2_challenge,
    executor_kind="db",
    audit_action="admin_referrals_process",
    audit_meta_builder=_referral_process_audit_meta,
)


def _normalize_identifier(
    value: object,
    *,
    field: str,
    minimum: int = 1,
    maximum: int = 128,
    uppercase: bool = False,
) -> str:
    normalized = _bounded_text(
        value,
        field=field,
        minimum=minimum,
        maximum=maximum,
    )
    normalized = normalized.upper() if uppercase else normalized.lower()
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", normalized) is None:
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message=f"Поле {field} содержит недопустимые символы.",
        )
    return normalized


def _normalize_optional_datetime(value: object, *, field: str) -> str | None:
    if value is None or value == "":
        return None
    raw = _bounded_text(value, field=field, maximum=64)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message=f"Поле {field} должно содержать ISO datetime.",
        ) from None
    if parsed.tzinfo is not None and parsed.utcoffset() is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed.isoformat()


def _normalize_json_object(
    value: object,
    *,
    field: str,
    maximum_bytes: int = 200_000,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message=f"Поле {field} должно быть JSON-объектом.",
        )
    try:
        encoded = canonical_json_bytes(dict(value))
        decoded = json.loads(encoded)
    except (TypeError, ValueError):
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message=f"Поле {field} содержит неподдерживаемый JSON.",
        ) from None
    if len(encoded) > maximum_bytes or not isinstance(decoded, dict):
        raise ActionIntentError(
            "invalid_payload",
            status_code=422,
            message=f"Поле {field} слишком велико.",
        )
    return decoded


def _json_fingerprint(domain: str, value: object) -> dict[str, Any]:
    encoded = canonical_json_bytes(value)
    return {
        "sha256": _semantic_hash(domain, value),
        "bytes": len(encoded),
    }


def _row_for_update(query, session, for_update: bool):
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    return query.first()


def _management_challenge(_state: EntityState, _payload: Mapping[str, Any]) -> str:
    return "ПОДТВЕРДИТЬ УПРАВЛЕНИЕ"


def _context_target_challenge(state: EntityState, _payload: Mapping[str, Any]) -> str:
    return str(state.context["challenge"])


def _safe_model_snapshot(row: Any, fields: tuple[str, ...]) -> dict[str, Any] | None:
    if row is None:
        return None
    snapshot: dict[str, Any] = {"id": int(row.id)} if getattr(row, "id", None) is not None else {}
    for field in fields:
        value = getattr(row, field, None)
        if isinstance(value, datetime):
            snapshot[field] = _safe_iso(value)
        elif isinstance(value, str) and field in {
            "label",
            "title",
            "summary",
            "link",
            "description",
            "name",
            "metadata_json",
            "text",
        }:
            snapshot[field] = _redacted_text(value)
        else:
            snapshot[field] = value
    return snapshot


def _normalize_plan_create_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(
        payload,
        {
            "code",
            "label",
            "amount_rub",
            "amount_stars",
            "days",
            "device_limit",
            "node_policy",
            "badge",
            "is_active",
            "sort_order",
        },
    )
    node_policy = payload.get("node_policy")
    badge = payload.get("badge")
    is_active = payload.get("is_active", True)
    if type(is_active) is not bool:
        raise ActionIntentError("invalid_payload", status_code=422, message="is_active должен быть bool.")
    return {
        "code": _normalize_identifier(payload.get("code"), field="code", minimum=2, maximum=32),
        "label": _bounded_text(payload.get("label"), field="label", minimum=2, maximum=120),
        "amount_rub": _normalize_promo_integer(payload.get("amount_rub"), field="amount_rub", minimum=0, maximum=1_000_000),
        "amount_stars": _normalize_promo_integer(payload.get("amount_stars", 0), field="amount_stars", minimum=0, maximum=1_000_000),
        "days": _normalize_promo_integer(payload.get("days", 30), field="days", minimum=1, maximum=3650),
        "device_limit": _normalize_promo_integer(payload.get("device_limit", 1), field="device_limit", minimum=1, maximum=64),
        "node_policy": _bounded_text(node_policy, field="node_policy", maximum=32) or None if node_policy is not None else None,
        "badge": _bounded_text(badge, field="badge", maximum=32) or None if badge is not None else None,
        "is_active": is_active,
        "sort_order": _normalize_promo_integer(payload.get("sort_order", 100), field="sort_order", minimum=0, maximum=10_000),
    }


def _normalize_plan_update_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {
        "label",
        "amount_rub",
        "amount_stars",
        "days",
        "device_limit",
        "node_policy",
        "badge",
        "is_active",
        "sort_order",
    }
    _reject_extra_payload_fields(payload, allowed)
    if not payload:
        raise ActionIntentError("invalid_payload", status_code=422, message="Нужно указать изменение плана.")
    out: dict[str, Any] = {}
    if "label" in payload:
        out["label"] = _bounded_text(payload.get("label"), field="label", minimum=2, maximum=120)
    for field, minimum, maximum in (
        ("amount_rub", 0, 1_000_000),
        ("amount_stars", 0, 1_000_000),
        ("days", 1, 3650),
        ("device_limit", 1, 64),
        ("sort_order", 0, 10_000),
    ):
        if field in payload:
            out[field] = _normalize_promo_integer(payload.get(field), field=field, minimum=minimum, maximum=maximum)
    for field in ("node_policy", "badge"):
        if field in payload:
            value = payload.get(field)
            out[field] = _bounded_text(value, field=field, maximum=32) or None if value is not None else None
    if "is_active" in payload:
        if type(payload.get("is_active")) is not bool:
            raise ActionIntentError("invalid_payload", status_code=422, message="is_active должен быть bool.")
        out["is_active"] = bool(payload["is_active"])
    return out


_PLAN_FIELDS = (
    "code",
    "label",
    "amount_rub",
    "amount_stars",
    "days",
    "device_limit",
    "node_policy",
    "badge",
    "is_active",
    "sort_order",
    "created_at",
    "updated_at",
)


def _plan_state(
    session,
    target_id: str,
    payload: Mapping[str, Any],
    for_update: bool,
    *,
    mode: str,
) -> EntityState:
    code = _normalize_identifier(target_id, field="target", minimum=2, maximum=32)
    if mode == "create" and str(payload.get("code") or "") != code:
        raise ActionIntentError("invalid_target", status_code=422, message="Цель должна совпадать с кодом плана.")
    row = _row_for_update(
        session.query(PlanCatalog).filter(func.lower(PlanCatalog.code) == code),
        session,
        for_update,
    )
    if mode == "create" and row is not None:
        raise ActionIntentError("target_exists", status_code=409, message="План уже существует.")
    if mode != "create" and row is None:
        raise ActionIntentError("target_not_found", status_code=404, message="План не найден.")
    before = _safe_model_snapshot(row, _PLAN_FIELDS)
    if mode == "delete":
        after = None
    elif mode == "create":
        after = dict(payload)
        after["label"] = _redacted_text(str(payload["label"]))
    else:
        after = {**dict(before or {}), **dict(payload)}
        if "label" in payload:
            after["label"] = _redacted_text(str(payload["label"]))
    return EntityState(
        entity=row,
        version_snapshot={"mode": mode, "row": before},
        public_snapshot=before or {"code": code, "exists": False},
        context={"mode": mode, "code": code, "after_snapshot": after, "challenge": code},
    )


def _plan_create_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _plan_state(session, target_id, payload, for_update, mode="create")


def _plan_update_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _plan_state(session, target_id, payload, for_update, mode="update")


def _plan_delete_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _plan_state(session, target_id, payload, for_update, mode="delete")


def _model_change_preview(state: EntityState, _payload: Mapping[str, Any]) -> dict[str, Any]:
    return _simple_preview(
        f"Изменение {state.context['mode']} для {state.context.get('code') or state.context.get('challenge')}",
        state.public_snapshot,
        state.context.get("after_snapshot"),
        ["Сущность и её версия зафиксированы сервером; чувствительный текст заменён fingerprint."],
    )


def _normalize_live_update_runtime(
    payload: Mapping[str, Any],
    *,
    partial: bool,
) -> dict[str, Any]:
    allowed = {
        "title",
        "summary",
        "link",
        "channel_username",
        "post_id",
        "published_at",
        "is_active",
        "sort_order",
    }
    _reject_extra_payload_fields(payload, allowed)
    if partial and not payload:
        raise ActionIntentError("invalid_payload", status_code=422, message="Нужно указать изменение новости.")
    out: dict[str, Any] = {}
    for field, minimum, maximum in (("title", 2, 160), ("summary", 2, 600)):
        if field in payload or not partial:
            out[field] = _bounded_text(payload.get(field), field=field, minimum=minimum, maximum=maximum)
    for field, maximum in (("link", 600), ("channel_username", 64)):
        if field in payload:
            value = payload.get(field)
            out[field] = _bounded_text(value, field=field, maximum=maximum) or None if value is not None else None
    if "channel_username" in out and out["channel_username"] is not None:
        channel = str(out["channel_username"]).lstrip("@").lower()
        if re.fullmatch(r"[a-z0-9_]{4,64}", channel) is None:
            raise ActionIntentError("invalid_payload", status_code=422, message="channel_username указан неверно.")
        out["channel_username"] = channel
    if "post_id" in payload:
        value = payload.get("post_id")
        out["post_id"] = None if value is None else _normalize_promo_integer(value, field="post_id", minimum=1, maximum=2_000_000_000)
    if "published_at" in payload:
        out["published_at"] = _normalize_optional_datetime(payload.get("published_at"), field="published_at")
    if "is_active" in payload or not partial:
        value = payload.get("is_active", True)
        if type(value) is not bool:
            raise ActionIntentError("invalid_payload", status_code=422, message="is_active должен быть bool.")
        out["is_active"] = bool(value)
    if "sort_order" in payload or not partial:
        out["sort_order"] = _normalize_promo_integer(payload.get("sort_order", 100), field="sort_order", minimum=0, maximum=10_000)
    if not partial and not out.get("link") and not (out.get("channel_username") and out.get("post_id")):
        raise ActionIntentError("invalid_payload", status_code=422, message="Нужна ссылка или Telegram post target.")
    return out


def _safe_live_update_payload(runtime: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(runtime)
    for field in ("title", "summary", "link", "channel_username"):
        if isinstance(out.get(field), str):
            out[field] = _redacted_text(str(out[field]))
    return out


def _normalize_live_update_create_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _normalize_live_update_runtime(payload, partial=False)


def _normalize_live_update_create_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _safe_live_update_payload(_normalize_live_update_create_runtime(payload))


def _normalize_live_update_update_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _normalize_live_update_runtime(payload, partial=True)


def _normalize_live_update_update_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _safe_live_update_payload(_normalize_live_update_update_runtime(payload))


_LIVE_UPDATE_FIELDS = (
    "title",
    "summary",
    "link",
    "channel_username",
    "post_id",
    "published_at",
    "is_active",
    "sort_order",
    "created_at",
    "updated_at",
)


def _live_update_state(
    session,
    target_id: str,
    payload: Mapping[str, Any],
    for_update: bool,
    *,
    mode: str,
) -> EntityState:
    row = None
    if mode == "create":
        if target_id != "new":
            raise ActionIntentError("invalid_target", status_code=422, message="Цель создания новости должна быть new.")
        count, max_id = session.query(func.count(LiveUpdate.id), func.max(LiveUpdate.id)).one()
        before: dict[str, Any] | None = None
        version = {"count": int(count or 0), "max_id": int(max_id or 0)}
        challenge = "new"
    else:
        update_id = _integer_target(target_id, positive=True)
        row = _row_for_update(
            session.query(LiveUpdate).filter(LiveUpdate.id == update_id),
            session,
            for_update,
        )
        if row is None:
            raise ActionIntentError("target_not_found", status_code=404, message="Новость не найдена.")
        before = _safe_model_snapshot(row, _LIVE_UPDATE_FIELDS)
        version = before
        challenge = str(update_id)
    safe_after = None if mode == "delete" else _safe_live_update_payload(payload)
    if mode == "update":
        safe_after = {**dict(before or {}), **dict(safe_after or {})}
    return EntityState(
        entity=row,
        version_snapshot={"mode": mode, "row": version},
        public_snapshot=before or {"exists": False},
        context={"mode": mode, "after_snapshot": safe_after, "challenge": challenge},
    )


def _live_update_create_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _live_update_state(session, target_id, payload, for_update, mode="create")


def _live_update_update_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _live_update_state(session, target_id, payload, for_update, mode="update")


def _live_update_delete_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _live_update_state(session, target_id, payload, for_update, mode="delete")


def _normalize_start_link_runtime(payload: Mapping[str, Any], *, partial: bool) -> dict[str, Any]:
    allowed = {"code", "description", "target_action", "is_active"}
    _reject_extra_payload_fields(payload, allowed)
    if partial and not payload:
        raise ActionIntentError("invalid_payload", status_code=422, message="Нужно указать изменение start link.")
    out: dict[str, Any] = {}
    if "code" in payload or not partial:
        out["code"] = _normalize_identifier(payload.get("code"), field="code", minimum=2, maximum=64)
    for field, maximum in (("description", 240), ("target_action", 64)):
        if field in payload or (not partial and field == "target_action"):
            value = payload.get(field)
            minimum = 2 if field == "target_action" else 0
            out[field] = _bounded_text(value, field=field, minimum=minimum, maximum=maximum) or None if value is not None else None
    if "is_active" in payload or not partial:
        value = payload.get("is_active", True)
        if type(value) is not bool:
            raise ActionIntentError("invalid_payload", status_code=422, message="is_active должен быть bool.")
        out["is_active"] = bool(value)
    return out


def _safe_start_link_payload(runtime: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(runtime)
    if isinstance(out.get("description"), str):
        out["description"] = _redacted_text(str(out["description"]))
    return out


def _normalize_start_link_create_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _normalize_start_link_runtime(payload, partial=False)


def _normalize_start_link_create_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _safe_start_link_payload(_normalize_start_link_create_runtime(payload))


def _normalize_start_link_update_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _normalize_start_link_runtime(payload, partial=True)


def _normalize_start_link_update_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _safe_start_link_payload(_normalize_start_link_update_runtime(payload))


_START_LINK_FIELDS = ("code", "description", "target_action", "is_active", "created_at", "updated_at")


def _start_link_state(
    session,
    target_id: str,
    payload: Mapping[str, Any],
    for_update: bool,
    *,
    mode: str,
) -> EntityState:
    if mode == "create":
        code = _normalize_identifier(target_id, field="target", minimum=2, maximum=64)
        if str(payload.get("code") or "") != code:
            raise ActionIntentError("invalid_target", status_code=422, message="Цель должна совпадать с start code.")
        row = _row_for_update(
            session.query(StartLink).filter(func.lower(StartLink.code) == code),
            session,
            for_update,
        )
        if row is not None:
            raise ActionIntentError("target_exists", status_code=409, message="Start link уже существует.")
        before = None
        challenge = code
    else:
        link_id = _integer_target(target_id, positive=True)
        row = _row_for_update(
            session.query(StartLink).filter(StartLink.id == link_id),
            session,
            for_update,
        )
        if row is None:
            raise ActionIntentError("target_not_found", status_code=404, message="Start link не найден.")
        before = _safe_model_snapshot(row, _START_LINK_FIELDS)
        challenge = str(link_id)
    after = None if mode == "delete" else _safe_start_link_payload(payload)
    if mode == "update":
        after = {**dict(before or {}), **dict(after or {})}
    return EntityState(
        entity=row,
        version_snapshot={"mode": mode, "row": before},
        public_snapshot=before or {"exists": False},
        context={"mode": mode, "after_snapshot": after, "challenge": challenge},
    )


def _start_link_create_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _start_link_state(session, target_id, payload, for_update, mode="create")


def _start_link_update_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _start_link_state(session, target_id, payload, for_update, mode="update")


def _start_link_delete_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _start_link_state(session, target_id, payload, for_update, mode="delete")


def _normalize_campaign_runtime(payload: Mapping[str, Any], *, partial: bool) -> dict[str, Any]:
    allowed = {
        "name",
        "campaign_type",
        "target_value",
        "segment",
        "starts_at",
        "ends_at",
        "max_activations",
        "auto_disable",
        "is_active",
        "metadata",
    }
    _reject_extra_payload_fields(payload, allowed)
    if partial and not payload:
        raise ActionIntentError("invalid_payload", status_code=422, message="Нужно указать изменение кампании.")
    out: dict[str, Any] = {}
    if "name" in payload or not partial:
        out["name"] = _bounded_text(payload.get("name"), field="name", minimum=2, maximum=120)
    if not partial:
        campaign_type = str(payload.get("campaign_type") or "").strip().lower()
        if campaign_type not in {"promo", "gift"}:
            raise ActionIntentError("invalid_payload", status_code=422, message="campaign_type должен быть promo или gift.")
        out["campaign_type"] = campaign_type
        out["target_value"] = _bounded_text(payload.get("target_value"), field="target_value", minimum=2, maximum=64).upper()
    if "segment" in payload or not partial:
        out["segment"] = _bounded_text(payload.get("segment", "all_active"), field="segment", minimum=2, maximum=32).lower()
    for field in ("starts_at", "ends_at"):
        if field in payload:
            out[field] = _normalize_optional_datetime(payload.get(field), field=field)
    starts = out.get("starts_at")
    ends = out.get("ends_at")
    if starts and ends and datetime.fromisoformat(str(starts)) > datetime.fromisoformat(str(ends)):
        raise ActionIntentError("invalid_payload", status_code=422, message="starts_at должен быть не позже ends_at.")
    if "max_activations" in payload or not partial:
        out["max_activations"] = _normalize_promo_integer(payload.get("max_activations", -1), field="max_activations", minimum=-1, maximum=1_000_000)
    for field, default in (("auto_disable", True), ("is_active", True)):
        if field in payload or not partial:
            value = payload.get(field, default)
            if type(value) is not bool:
                raise ActionIntentError("invalid_payload", status_code=422, message=f"{field} должен быть bool.")
            out[field] = bool(value)
    if "metadata" in payload or not partial:
        out["metadata"] = _normalize_json_object(payload.get("metadata") or {}, field="metadata", maximum_bytes=50_000)
    return out


def _safe_campaign_payload(runtime: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(runtime)
    for field in ("name", "target_value"):
        if isinstance(out.get(field), str):
            out[field] = _redacted_text(str(out[field]))
    if "metadata" in out:
        out["metadata"] = _json_fingerprint("admin-campaign-metadata", out["metadata"])
    return out


def _normalize_campaign_create_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _normalize_campaign_runtime(payload, partial=False)


def _normalize_campaign_create_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _safe_campaign_payload(_normalize_campaign_create_runtime(payload))


def _normalize_campaign_update_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _normalize_campaign_runtime(payload, partial=True)


def _normalize_campaign_update_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _safe_campaign_payload(_normalize_campaign_update_runtime(payload))


_CAMPAIGN_FIELDS = (
    "name",
    "campaign_type",
    "target_value",
    "segment",
    "starts_at",
    "ends_at",
    "max_activations",
    "activations_count",
    "auto_disable",
    "is_active",
    "created_by",
    "metadata_json",
    "created_at",
    "updated_at",
)


def _campaign_state(
    session,
    target_id: str,
    payload: Mapping[str, Any],
    for_update: bool,
    *,
    mode: str,
) -> EntityState:
    if mode == "create":
        if target_id != "new":
            raise ActionIntentError("invalid_target", status_code=422, message="Цель создания кампании должна быть new.")
        row = None
        count, max_id = session.query(func.count(IncentiveCampaign.id), func.max(IncentiveCampaign.id)).one()
        before = None
        version: object = {"count": int(count or 0), "max_id": int(max_id or 0)}
        challenge = "new"
    else:
        campaign_id = _integer_target(target_id, positive=True)
        row = _row_for_update(
            session.query(IncentiveCampaign).filter(IncentiveCampaign.id == campaign_id),
            session,
            for_update,
        )
        if row is None:
            raise ActionIntentError("target_not_found", status_code=404, message="Кампания не найдена.")
        before = _safe_model_snapshot(row, _CAMPAIGN_FIELDS)
        version = before
        challenge = str(campaign_id)
    after = None if mode == "delete" else _safe_campaign_payload(payload)
    if mode == "update":
        after = {**dict(before or {}), **dict(after or {})}
    return EntityState(
        entity=row,
        version_snapshot={"mode": mode, "row": version},
        public_snapshot=before or {"exists": False},
        context={"mode": mode, "after_snapshot": after, "challenge": challenge},
    )


def _campaign_create_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _campaign_state(session, target_id, payload, for_update, mode="create")


def _campaign_update_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _campaign_state(session, target_id, payload, for_update, mode="update")


def _campaign_delete_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _campaign_state(session, target_id, payload, for_update, mode="delete")


def _normalize_template_runtime(payload: Mapping[str, Any], *, partial: bool) -> dict[str, Any]:
    allowed = {"key", "new_key", "text"}
    _reject_extra_payload_fields(payload, allowed)
    if partial and not payload:
        raise ActionIntentError("invalid_payload", status_code=422, message="Нужно указать изменение шаблона.")
    out: dict[str, Any] = {}
    if "key" in payload or not partial:
        out["key"] = _normalize_identifier(payload.get("key"), field="key", minimum=2, maximum=50)
    if "new_key" in payload:
        value = payload.get("new_key")
        out["new_key"] = None if value is None else _normalize_identifier(value, field="new_key", minimum=2, maximum=50)
    if "text" in payload or not partial:
        out["text"] = _bounded_text(payload.get("text"), field="text", minimum=1, maximum=2000)
    return out


def _safe_template_payload(runtime: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(runtime)
    if isinstance(out.get("text"), str):
        out["text"] = _redacted_text(str(out["text"]))
    return out


def _normalize_template_create_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _normalize_template_runtime(payload, partial=False)


def _normalize_template_create_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _safe_template_payload(_normalize_template_create_runtime(payload))


def _normalize_template_update_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _normalize_template_runtime(payload, partial=True)


def _normalize_template_update_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _safe_template_payload(_normalize_template_update_runtime(payload))


def _template_state(
    session,
    target_id: str,
    payload: Mapping[str, Any],
    for_update: bool,
    *,
    mode: str,
) -> EntityState:
    key = _normalize_identifier(target_id, field="target", minimum=2, maximum=50)
    if mode == "create" and str(payload.get("key") or "") != key:
        raise ActionIntentError("invalid_target", status_code=422, message="Цель должна совпадать с ключом шаблона.")
    row = _row_for_update(
        session.query(Template).filter(func.lower(Template.key) == key),
        session,
        for_update,
    )
    if mode == "create" and row is not None:
        raise ActionIntentError("target_exists", status_code=409, message="Шаблон уже существует.")
    if mode != "create" and row is None:
        raise ActionIntentError("target_not_found", status_code=404, message="Шаблон не найден.")
    before = _safe_model_snapshot(row, ("key", "text", "created_at"))
    after = None if mode == "delete" else _safe_template_payload(payload)
    if mode == "update":
        after = {**dict(before or {}), **dict(after or {})}
    return EntityState(
        entity=row,
        version_snapshot={"mode": mode, "row": before},
        public_snapshot=before or {"key": key, "exists": False},
        context={"mode": mode, "after_snapshot": after, "challenge": key},
    )


def _template_create_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _template_state(session, target_id, payload, for_update, mode="create")


def _template_update_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _template_state(session, target_id, payload, for_update, mode="update")


def _template_delete_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _template_state(session, target_id, payload, for_update, mode="delete")


def _app_setting_value(row: AppSetting | None) -> object:
    if row is None or not str(row.value_json or "").strip():
        return None
    try:
        return json.loads(str(row.value_json))
    except (TypeError, ValueError):
        return {"invalid_json_sha256": _semantic_hash("admin-setting-invalid-json", str(row.value_json or ""))}


def _app_setting_state(
    session,
    target_id: str,
    payload: Mapping[str, Any],
    for_update: bool,
    *,
    target: str,
    setting_key: str,
    fingerprint_domain: str,
) -> EntityState:
    if str(target_id) != target:
        raise ActionIntentError("invalid_target", status_code=422, message="Цель конфигурации указана неверно.")
    row = _row_for_update(
        session.query(AppSetting).filter(AppSetting.key == setting_key),
        session,
        for_update,
    )
    current = _app_setting_value(row)
    before = {
        "exists": row is not None,
        "updated_at": _safe_iso(row.updated_at) if row is not None else None,
        "value": _json_fingerprint(f"{fingerprint_domain}-before", current),
    }
    after = _json_fingerprint(f"{fingerprint_domain}-after", payload)
    return EntityState(
        entity=row,
        version_snapshot={"setting_key": setting_key, **before},
        public_snapshot=before,
        context={
            "mode": "update",
            "setting_key": setting_key,
            "after_snapshot": after,
            "challenge": target,
        },
    )


def _normalize_wheel_config_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"preset", "weights", "cooldown_hours"})
    preset = _bounded_text(
        payload.get("preset", "paid_fortnightly_discounts_v3"),
        field="preset",
        minimum=2,
        maximum=32,
    )
    cooldown = _normalize_promo_integer(payload.get("cooldown_hours", 336), field="cooldown_hours", minimum=1, maximum=2160)
    weights_value = payload.get("weights")
    if not isinstance(weights_value, list) or not 1 <= len(weights_value) <= 20:
        raise ActionIntentError("invalid_payload", status_code=422, message="weights должен содержать 1..20 элементов.")
    weights: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for value in weights_value:
        if not isinstance(value, Mapping):
            raise ActionIntentError("invalid_payload", status_code=422, message="Элемент weights должен быть объектом.")
        _reject_extra_payload_fields(value, {"days", "kind", "value", "weight"})
        weight = _normalize_promo_integer(value.get("weight"), field="weight", minimum=1, maximum=10_000)
        has_legacy_days = value.get("days") is not None
        has_typed_outcome = value.get("kind") is not None or value.get("value") is not None
        if has_legacy_days == has_typed_outcome:
            raise ActionIntentError(
                "invalid_payload",
                status_code=422,
                message="Сектор wheel должен содержать либо days, либо kind/value.",
            )
        if has_legacy_days:
            days = _normalize_promo_integer(value.get("days"), field="days", minimum=1, maximum=365)
            outcome_key = ("days", days)
            normalized = {"days": days, "weight": weight}
        else:
            kind = _bounded_text(value.get("kind"), field="kind", minimum=4, maximum=16).lower()
            if kind not in {"days", "discount"}:
                raise ActionIntentError("invalid_payload", status_code=422, message="kind wheel не поддерживается.")
            outcome_value = _normalize_promo_integer(value.get("value"), field="value", minimum=1, maximum=365)
            outcome_key = (kind, outcome_value)
            normalized = {"kind": kind, "value": outcome_value, "weight": weight}
        if outcome_key in seen:
            raise ActionIntentError("invalid_payload", status_code=422, message="Секторы wheel должны быть уникальны.")
        seen.add(outcome_key)
        weights.append(normalized)
    return {"preset": preset, "weights": weights, "cooldown_hours": cooldown}


def _wheel_config_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _app_setting_state(
        session,
        target_id,
        payload,
        for_update,
        target="wheel",
        setting_key="wheel_config",
        fingerprint_domain="admin-wheel-config",
    )


def _normalize_fingerprinted_config_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _normalize_json_object(payload, field="config")


def _fingerprinted_config_payload(domain: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    runtime = _normalize_fingerprinted_config_runtime(payload)
    return {"config": _json_fingerprint(domain, runtime)}


def _normalize_network_config_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    runtime = _normalize_fingerprinted_config_runtime(payload)
    defaults = runtime.get("defaults") if isinstance(runtime.get("defaults"), Mapping) else {}
    return {
        "config": _json_fingerprint("admin-network-rollout-config", runtime),
        "version": str(runtime.get("version") or "")[:64] or None,
        "default_transport_profile": str(defaults.get("transport_profile") or "")[:64] or None,
    }


def _network_config_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _app_setting_state(
        session,
        target_id,
        payload,
        for_update,
        target="network-rollout",
        setting_key="network_rollout_config",
        fingerprint_domain="admin-network-rollout-config",
    )


def _normalize_promo_slots_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    runtime = _normalize_fingerprinted_config_runtime(payload)
    assignments = runtime.get("assignments")
    if not isinstance(assignments, list) or len(assignments) > 128:
        raise ActionIntentError("invalid_payload", status_code=422, message="assignments должен быть списком до 128 элементов.")
    return {
        "config": _json_fingerprint("admin-promo-slots", runtime),
        "assignments": len(assignments),
    }


def _promo_slots_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _app_setting_state(
        session,
        target_id,
        payload,
        for_update,
        target="promo-slots",
        setting_key="promo_slots_config_v1",
        fingerprint_domain="admin-promo-slots",
    )


def _normalize_loyalty_config_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    runtime = _normalize_fingerprinted_config_runtime(payload)
    tiers = runtime.get("tiers")
    return {
        "config": _json_fingerprint("admin-loyalty-config", runtime),
        "enabled": bool(runtime.get("enabled", True)),
        "tiers": len(tiers) if isinstance(tiers, list) else 0,
    }


def _loyalty_config_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    return _app_setting_state(
        session,
        target_id,
        payload,
        for_update,
        target="loyalty",
        setting_key="loyalty_config",
        fingerprint_domain="admin-loyalty-config",
    )


def _normalize_warp_material_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(
        payload,
        {"tg_id", "install_id", "source", "mode", "wireguard_config", "account"},
    )
    tg_id = _normalize_promo_integer(payload.get("tg_id"), field="tg_id", minimum=1, maximum=2**63 - 1)
    install_value = payload.get("install_id")
    install_id = _bounded_text(install_value, field="install_id", maximum=128) or None if install_value is not None else None
    source = _bounded_text(payload.get("source", "operator_provisioned"), field="source", minimum=2, maximum=64)
    mode = _bounded_text(payload.get("mode", "proxy_over_warp"), field="mode", minimum=3, maximum=32)
    wireguard = _normalize_json_object(payload.get("wireguard_config") or {}, field="wireguard_config", maximum_bytes=100_000)
    if not wireguard:
        raise ActionIntentError("invalid_payload", status_code=422, message="wireguard_config не может быть пустым.")
    account_value = payload.get("account")
    account = None if account_value is None else _normalize_json_object(account_value, field="account", maximum_bytes=100_000)
    return {
        "tg_id": tg_id,
        "install_id": install_id,
        "source": source,
        "mode": mode,
        "wireguard_config": wireguard,
        "account": account,
    }


def _normalize_warp_material_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    runtime = _normalize_warp_material_runtime(payload)
    return {
        "tg_id": int(runtime["tg_id"]),
        "install_id": _redacted_text(str(runtime["install_id"])) if runtime.get("install_id") else None,
        "source": str(runtime["source"]),
        "mode": str(runtime["mode"]),
        "wireguard_config": _json_fingerprint("admin-warp-wireguard", runtime["wireguard_config"]),
        "account": _json_fingerprint("admin-warp-account", runtime["account"]) if runtime.get("account") is not None else None,
    }


def _warp_material_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    tg_id = _integer_target(target_id, positive=True)
    if int(payload.get("tg_id") or 0) != tg_id:
        raise ActionIntentError("invalid_target", status_code=422, message="Цель должна совпадать с tg_id материала.")
    user = _row_for_update(session.query(User).filter(User.tg_id == tg_id), session, for_update)
    if user is None:
        raise ActionIntentError("target_not_found", status_code=404, message="Пользователь не найден.")
    install_id = str(payload.get("install_id") or getattr(user, "app_install_id", "") or "").strip() or None
    query = session.query(WarpMaterial).filter(WarpMaterial.tg_id == tg_id, WarpMaterial.is_active == True)
    if install_id is None:
        query = query.filter(WarpMaterial.install_id.is_(None))
    else:
        query = query.filter(WarpMaterial.install_id == install_id)
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    materials = query.order_by(WarpMaterial.id.asc()).all()
    fingerprints = [
        {
            "id": int(row.id),
            "material_hash": str(row.material_hash or "") or None,
            "state": str(row.state or ""),
            "source": str(row.source or ""),
            "mode": str(row.mode or ""),
            "updated_at": _safe_iso(row.updated_at),
        }
        for row in materials
    ]
    before = {
        "tg_id": tg_id,
        "install_id_sha256": _semantic_hash("admin-warp-install", install_id or ""),
        "active_materials": fingerprints,
    }
    after = {
        "tg_id": tg_id,
        "install_id_sha256": before["install_id_sha256"],
        "source": str(payload["source"]),
        "mode": str(payload["mode"]),
        "wireguard_config": _json_fingerprint("admin-warp-wireguard", payload["wireguard_config"]),
        "account": _json_fingerprint("admin-warp-account", payload["account"]) if payload.get("account") is not None else None,
    }
    return EntityState(
        entity=user,
        version_snapshot={"user_active": bool(user.is_active), **before},
        public_snapshot=before,
        context={"mode": "replace", "after_snapshot": after, "challenge": str(tg_id), "tg_id": tg_id},
    )


def _audit_warp_target(state: EntityState, _payload: Mapping[str, Any]) -> int | None:
    return int(state.context["tg_id"])


def _normalize_access_key_issue_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"plan_code", "quantity"})
    return {
        "plan_code": _normalize_identifier(payload.get("plan_code"), field="plan_code", minimum=2, maximum=32),
        "quantity": _normalize_promo_integer(payload.get("quantity", 1), field="quantity", minimum=1, maximum=200),
    }


def _access_key_issue_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    plan_code = _normalize_identifier(target_id, field="target", minimum=2, maximum=32)
    if str(payload.get("plan_code") or "") != plan_code:
        raise ActionIntentError("invalid_target", status_code=422, message="Цель должна совпадать с plan_code.")
    plan = _row_for_update(
        session.query(PlanCatalog).filter(func.lower(PlanCatalog.code) == plan_code),
        session,
        for_update,
    )
    count, max_id = session.query(func.count(GiftCard.id), func.max(GiftCard.id)).one()
    before = {
        "plan": _safe_model_snapshot(plan, _PLAN_FIELDS),
        "issued_count": int(count or 0),
        "max_issue_id": int(max_id or 0),
    }
    return EntityState(
        entity=plan,
        version_snapshot=before,
        public_snapshot=before,
        context={
            "mode": "issue",
            "after_snapshot": {"plan_code": plan_code, "quantity": int(payload["quantity"])},
            "challenge": plan_code,
        },
    )


def _normalize_gift_code_create_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"card_type"})
    return {"card_type": _normalize_identifier(payload.get("card_type"), field="card_type", minimum=3, maximum=20)}


def _gift_code_create_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    card_type = _normalize_identifier(target_id, field="target", minimum=3, maximum=20)
    if str(payload.get("card_type") or "") != card_type:
        raise ActionIntentError("invalid_target", status_code=422, message="Цель должна совпадать с card_type.")
    count, max_id = session.query(func.count(GiftCard.id), func.max(GiftCard.id)).one()
    before = {"issued_count": int(count or 0), "max_issue_id": int(max_id or 0)}
    return EntityState(
        entity=None,
        version_snapshot=before,
        public_snapshot=before,
        context={"mode": "create", "after_snapshot": {"card_type": card_type}, "challenge": card_type},
    )


def _result_envelope(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: result[key]
        for key in ("ok", "status", "action_intent_id", "audit_id")
        if key in result
    }


def _sanitize_warp_material_result(result: Mapping[str, Any]) -> dict[str, Any]:
    safe = _result_envelope(result)
    material = result.get("material")
    if not isinstance(material, Mapping):
        raise ActionIntentError(
            "invalid_executor_result",
            status_code=500,
            message="Исполнитель WARP вернул некорректный результат.",
        )
    safe_material = {
        key: material[key]
        for key in (
            "id",
            "tg_id",
            "source",
            "mode",
            "state",
            "runtime_ready",
            "wireguard_config_available",
            "material_hash",
            "is_active",
            "provisioned_at",
            "rotation_requested_at",
            "revoked_at",
            "updated_at",
        )
        if key in material
    }
    install_id = material.get("install_id")
    safe_material["install_id_sha256"] = (
        _semantic_hash("admin-warp-install", str(install_id))
        if isinstance(install_id, str) and install_id
        else None
    )
    safe["material"] = safe_material
    return safe


def _internal_issued_card_ids(
    result: Mapping[str, Any],
    *,
    expected_count: int,
) -> list[int]:
    raw_ids = result.get(_INTERNAL_ISSUED_CARD_IDS_KEY)
    if (
        not isinstance(raw_ids, list)
        or len(raw_ids) != expected_count
        or any(type(value) is not int or value <= 0 for value in raw_ids)
        or len(set(raw_ids)) != len(raw_ids)
    ):
        raise ActionIntentError(
            "invalid_executor_result",
            status_code=500,
            message="Исполнитель не сохранил ссылки на выпущенные коды.",
        )
    return [int(value) for value in raw_ids]


def _sanitize_access_key_result(result: Mapping[str, Any]) -> dict[str, Any]:
    issued = result.get("issued")
    if not isinstance(issued, list) or not issued:
        raise ActionIntentError(
            "invalid_executor_result",
            status_code=500,
            message="Исполнитель не вернул выпущенные ключи.",
        )
    ids = _internal_issued_card_ids(result, expected_count=len(issued))
    fingerprints: list[dict[str, Any]] = []
    for item in issued:
        if not isinstance(item, Mapping) or not isinstance(item.get("key"), str):
            raise ActionIntentError(
                "invalid_executor_result",
                status_code=500,
                message="Исполнитель вернул некорректный ключ.",
            )
        fingerprints.append(_redacted_text(str(item["key"])))
    safe = _result_envelope(result)
    safe["plan"] = dict(result.get("plan") or {})
    safe[_INTERNAL_ISSUED_CARD_IDS_KEY] = ids
    safe["issued_fingerprints"] = fingerprints
    safe["issued_count"] = len(fingerprints)
    return safe


def _sanitize_gift_code_result(result: Mapping[str, Any]) -> dict[str, Any]:
    gift = result.get("gift_code")
    if not isinstance(gift, Mapping) or not isinstance(gift.get("code"), str):
        raise ActionIntentError(
            "invalid_executor_result",
            status_code=500,
            message="Исполнитель не вернул подарочный код.",
        )
    ids = _internal_issued_card_ids(result, expected_count=1)
    safe = _result_envelope(result)
    safe[_INTERNAL_ISSUED_CARD_IDS_KEY] = ids
    safe["issued_fingerprints"] = [_redacted_text(str(gift["code"]))]
    safe["issued_count"] = 1
    safe["gift_code_meta"] = {
        key: gift[key]
        for key in ("card_type", "days", "stars")
        if key in gift
    }
    return safe


def _issued_cards_for_replay(
    session,
    intent: AdminActionIntent,
    stored: Mapping[str, Any],
) -> list[GiftCard]:
    expected_count = stored.get("issued_count")
    if type(expected_count) is not int or not 1 <= expected_count <= 200:
        raise ActionIntentError(
            "result_unavailable",
            status_code=409,
            message="Выпущенные коды сохранены, но результат сейчас недоступен; не создавайте новый intent.",
        )
    try:
        ids = _internal_issued_card_ids(stored, expected_count=expected_count)
    except ActionIntentError as error:
        raise ActionIntentError(
            "result_unavailable",
            status_code=409,
            message="Выпущенные коды сохранены, но результат сейчас недоступен; не создавайте новый intent.",
        ) from error
    rows = (
        session.query(GiftCard)
        .filter(
            GiftCard.id.in_(ids),
            GiftCard.created_by == int(intent.actor_tg_id),
        )
        .all()
    )
    by_id = {int(row.id): row for row in rows}
    ordered = [by_id.get(card_id) for card_id in ids]
    fingerprints = stored.get("issued_fingerprints")
    if (
        not isinstance(fingerprints, list)
        or len(fingerprints) != expected_count
        or any(row is None for row in ordered)
    ):
        raise ActionIntentError(
            "result_unavailable",
            status_code=409,
            message="Выпущенные коды сохранены, но результат сейчас недоступен; не создавайте новый intent.",
        )
    verified: list[GiftCard] = []
    for row, fingerprint in zip(ordered, fingerprints, strict=True):
        assert row is not None
        code = str(row.code or "")
        actual = _redacted_text(code)
        if (
            not isinstance(fingerprint, Mapping)
            or fingerprint.get("length") != actual["length"]
            or not _constant_time_compare(
                str(fingerprint.get("sha256") or ""),
                str(actual["sha256"]),
            )
            or str(row.card_type or "").strip().lower() != str(intent.target_id)
        ):
            raise ActionIntentError(
                "result_unavailable",
                status_code=409,
                message="Выпущенные коды сохранены, но результат сейчас недоступен; не создавайте новый intent.",
            )
        verified.append(row)
    return verified


def _rehydrate_access_key_result(
    session,
    intent: AdminActionIntent,
    stored: Mapping[str, Any],
) -> dict[str, Any]:
    rows = _issued_cards_for_replay(session, intent, stored)
    plan = stored.get("plan")
    if not isinstance(plan, Mapping) or str(plan.get("code") or "").strip().lower() != str(intent.target_id):
        raise ActionIntentError(
            "result_unavailable",
            status_code=409,
            message="Выпущенные ключи сохранены, но их описание недоступно; не создавайте новый intent.",
        )
    public = _public_execution_result(stored)
    public.pop("issued_fingerprints", None)
    public.pop("issued_count", None)
    public["plan"] = dict(plan)
    public["issued"] = [
        {
            "key": str(row.code or ""),
            "plan": dict(plan),
            "issued_at": _safe_iso(row.created_at),
        }
        for row in rows
    ]
    return public


def _rehydrate_gift_code_result(
    session,
    intent: AdminActionIntent,
    stored: Mapping[str, Any],
) -> dict[str, Any]:
    rows = _issued_cards_for_replay(session, intent, stored)
    meta = stored.get("gift_code_meta")
    if (
        len(rows) != 1
        or not isinstance(meta, Mapping)
        or str(meta.get("card_type") or "").strip().lower() != str(intent.target_id)
    ):
        raise ActionIntentError(
            "result_unavailable",
            status_code=409,
            message="Подарочный код сохранён, но его описание недоступно; не создавайте новый intent.",
        )
    public = _public_execution_result(stored)
    public.pop("issued_fingerprints", None)
    public.pop("issued_count", None)
    public.pop("gift_code_meta", None)
    public["gift_code"] = {"code": str(rows[0].code or ""), **dict(meta)}
    return public


def _normalize_node_sync_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _reject_extra_payload_fields(payload, {"tg_id", "segment", "limit"})
    tg_value = payload.get("tg_id")
    tg_id = None if tg_value is None else _normalize_promo_integer(tg_value, field="tg_id", minimum=1, maximum=2**63 - 1)
    segment = _bounded_text(payload.get("segment", "active"), field="segment", minimum=2, maximum=32).lower()
    if segment not in {"active", "free", "paid"}:
        raise ActionIntentError("invalid_payload", status_code=422, message="Сегмент sync не поддерживается.")
    return {
        "tg_id": tg_id,
        "segment": segment,
        "limit": _normalize_promo_integer(payload.get("limit", 100), field="limit", minimum=1, maximum=1000),
    }


def _node_sync_state(session, target_id: str, payload: Mapping[str, Any], for_update: bool) -> EntityState:
    if target_id != "global":
        raise ActionIntentError("invalid_target", status_code=422, message="Цель global sync указана неверно.")
    query = session.query(User).filter(User.tg_id > 0)
    if payload.get("tg_id") is not None:
        query = query.filter(User.tg_id == int(payload["tg_id"]))
    elif payload["segment"] == "active":
        query = query.filter(User.is_active == True)
    elif payload["segment"] == "free":
        query = query.filter(func.upper(User.sub_type) == "FREE")
    else:
        query = query.filter(func.upper(User.sub_type) == "PAID")
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    users = query.order_by(User.created_at.asc(), User.tg_id.asc()).limit(int(payload["limit"])).all()
    selection = [
        {
            "tg_id": int(user.tg_id),
            "uuid": str(user.uuid or ""),
            "email": str(user.email or ""),
            "sub_id": str(user.sub_token or user.tg_id),
        }
        for user in users
    ]
    recipient_versions = [
        {
            "tg_id": int(item["tg_id"]),
            "identity_sha256": _semantic_hash(
                "admin-global-sync-recipient",
                [item["uuid"], item["email"], item["sub_id"]],
            ),
        }
        for item in selection
    ]
    selection_hash = _semantic_hash("admin-global-sync-selection", recipient_versions)
    snapshot = {"selected_count": len(selection), "selection_hash": selection_hash}
    return EntityState(
        entity=users,
        version_snapshot={"payload": dict(payload), "recipients": recipient_versions, **snapshot},
        public_snapshot=snapshot,
        context={
            "mode": "sync",
            "after_snapshot": {**snapshot, "state": "panel_sync"},
            "challenge": "ПОДТВЕРДИТЬ УПРАВЛЕНИЕ",
            "selection": selection,
            **snapshot,
        },
    )


def _node_sync_external_context(state: EntityState, _payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "selection": [dict(item) for item in state.context["selection"]],
        "selection_hash": str(state.context["selection_hash"]),
        "selected_count": int(state.context["selected_count"]),
    }


ACTION_POLICIES.update(
    {
        "plan.create": ActionPolicy(
            action="plan.create",
            target_type="plan",
            risk_level="L2",
            payload_normalizer=_normalize_plan_create_payload,
            entity_state_builder=_plan_create_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_l2_challenge,
            executor_kind="db",
            audit_action="admin_plan_create",
        ),
        "plan.update": ActionPolicy(
            action="plan.update",
            target_type="plan",
            risk_level="L2",
            payload_normalizer=_normalize_plan_update_payload,
            entity_state_builder=_plan_update_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_l2_challenge,
            executor_kind="db",
            audit_action="admin_plan_update",
        ),
        "plan.delete": ActionPolicy(
            action="plan.delete",
            target_type="plan",
            risk_level="L3",
            payload_normalizer=_normalize_empty_payload,
            entity_state_builder=_plan_delete_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_plan_code",
            challenge_builder=_context_target_challenge,
            executor_kind="db",
            audit_action="admin_plan_delete",
        ),
        "live_update.create": ActionPolicy(
            action="live_update.create",
            target_type="live_update",
            risk_level="L2",
            payload_normalizer=_normalize_live_update_create_payload,
            runtime_payload_normalizer=_normalize_live_update_create_runtime,
            entity_state_builder=_live_update_create_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_l2_challenge,
            executor_kind="db",
            audit_action="admin_live_update_create",
        ),
        "live_update.update": ActionPolicy(
            action="live_update.update",
            target_type="live_update",
            risk_level="L2",
            payload_normalizer=_normalize_live_update_update_payload,
            runtime_payload_normalizer=_normalize_live_update_update_runtime,
            entity_state_builder=_live_update_update_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_l2_challenge,
            executor_kind="db",
            audit_action="admin_live_update_update",
        ),
        "live_update.delete": ActionPolicy(
            action="live_update.delete",
            target_type="live_update",
            risk_level="L3",
            payload_normalizer=_normalize_empty_payload,
            entity_state_builder=_live_update_delete_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_live_update_id",
            challenge_builder=_context_target_challenge,
            executor_kind="db",
            audit_action="admin_live_update_delete",
        ),
        "start_link.create": ActionPolicy(
            action="start_link.create",
            target_type="start_link",
            risk_level="L2",
            payload_normalizer=_normalize_start_link_create_payload,
            runtime_payload_normalizer=_normalize_start_link_create_runtime,
            entity_state_builder=_start_link_create_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_l2_challenge,
            executor_kind="db",
            audit_action="admin_start_link_create",
        ),
        "start_link.update": ActionPolicy(
            action="start_link.update",
            target_type="start_link",
            risk_level="L2",
            payload_normalizer=_normalize_start_link_update_payload,
            runtime_payload_normalizer=_normalize_start_link_update_runtime,
            entity_state_builder=_start_link_update_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_l2_challenge,
            executor_kind="db",
            audit_action="admin_start_link_update",
        ),
        "start_link.delete": ActionPolicy(
            action="start_link.delete",
            target_type="start_link",
            risk_level="L3",
            payload_normalizer=_normalize_empty_payload,
            entity_state_builder=_start_link_delete_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_start_link_id",
            challenge_builder=_context_target_challenge,
            executor_kind="db",
            audit_action="admin_start_link_deactivate",
        ),
        "wheel_config.update": ActionPolicy(
            action="wheel_config.update",
            target_type="config",
            risk_level="L2",
            payload_normalizer=_normalize_wheel_config_payload,
            entity_state_builder=_wheel_config_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_l2_challenge,
            executor_kind="db",
            audit_action="admin_wheel_config_update",
        ),
        "network_rollout_config.update": ActionPolicy(
            action="network_rollout_config.update",
            target_type="config",
            risk_level="L2",
            payload_normalizer=_normalize_network_config_payload,
            runtime_payload_normalizer=_normalize_fingerprinted_config_runtime,
            entity_state_builder=_network_config_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_l2_challenge,
            executor_kind="db",
            audit_action="admin_network_rollout_config_put",
        ),
        "warp_material.replace": ActionPolicy(
            action="warp_material.replace",
            target_type="warp_material",
            risk_level="L3",
            payload_normalizer=_normalize_warp_material_payload,
            runtime_payload_normalizer=_normalize_warp_material_runtime,
            entity_state_builder=_warp_material_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_tg_id",
            challenge_builder=_context_target_challenge,
            executor_kind="db",
            audit_action="admin_warp_material_put",
            audit_target_builder=_audit_warp_target,
            result_sanitizer=_sanitize_warp_material_result,
        ),
        "promo_slots.update": ActionPolicy(
            action="promo_slots.update",
            target_type="config",
            risk_level="L2",
            payload_normalizer=_normalize_promo_slots_payload,
            runtime_payload_normalizer=_normalize_fingerprinted_config_runtime,
            entity_state_builder=_promo_slots_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_l2_challenge,
            executor_kind="db",
            audit_action="admin_promo_slots_put",
        ),
        "loyalty_config.update": ActionPolicy(
            action="loyalty_config.update",
            target_type="config",
            risk_level="L2",
            payload_normalizer=_normalize_loyalty_config_payload,
            runtime_payload_normalizer=_normalize_fingerprinted_config_runtime,
            entity_state_builder=_loyalty_config_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_l2_challenge,
            executor_kind="db",
            audit_action="admin_loyalty_config_put",
        ),
        "campaign.create": ActionPolicy(
            action="campaign.create",
            target_type="campaign",
            risk_level="L2",
            payload_normalizer=_normalize_campaign_create_payload,
            runtime_payload_normalizer=_normalize_campaign_create_runtime,
            entity_state_builder=_campaign_create_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_l2_challenge,
            executor_kind="db",
            audit_action="admin_campaign_create",
        ),
        "campaign.update": ActionPolicy(
            action="campaign.update",
            target_type="campaign",
            risk_level="L2",
            payload_normalizer=_normalize_campaign_update_payload,
            runtime_payload_normalizer=_normalize_campaign_update_runtime,
            entity_state_builder=_campaign_update_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_l2_challenge,
            executor_kind="db",
            audit_action="admin_campaign_patch",
        ),
        "campaign.delete": ActionPolicy(
            action="campaign.delete",
            target_type="campaign",
            risk_level="L3",
            payload_normalizer=_normalize_empty_payload,
            entity_state_builder=_campaign_delete_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_campaign_id",
            challenge_builder=_context_target_challenge,
            executor_kind="db",
            audit_action="admin_campaign_disable",
        ),
        "template.create": ActionPolicy(
            action="template.create",
            target_type="template",
            risk_level="L2",
            payload_normalizer=_normalize_template_create_payload,
            runtime_payload_normalizer=_normalize_template_create_runtime,
            entity_state_builder=_template_create_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_l2_challenge,
            executor_kind="db",
            audit_action="admin_template_create",
        ),
        "template.update": ActionPolicy(
            action="template.update",
            target_type="template",
            risk_level="L2",
            payload_normalizer=_normalize_template_update_payload,
            runtime_payload_normalizer=_normalize_template_update_runtime,
            entity_state_builder=_template_update_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_l2_challenge,
            executor_kind="db",
            audit_action="admin_template_update",
        ),
        "template.delete": ActionPolicy(
            action="template.delete",
            target_type="template",
            risk_level="L3",
            payload_normalizer=_normalize_empty_payload,
            entity_state_builder=_template_delete_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_template_key",
            challenge_builder=_context_target_challenge,
            executor_kind="db",
            audit_action="admin_template_delete",
        ),
        "access_key.issue": ActionPolicy(
            action="access_key.issue",
            target_type="access_key_batch",
            risk_level="L3",
            payload_normalizer=_normalize_access_key_issue_payload,
            entity_state_builder=_access_key_issue_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_plan_code",
            challenge_builder=_context_target_challenge,
            executor_kind="db",
            audit_action="admin_access_keys_issue",
            result_sanitizer=_sanitize_access_key_result,
            replay_result_builder=_rehydrate_access_key_result,
        ),
        "gift_code.create": ActionPolicy(
            action="gift_code.create",
            target_type="gift_code",
            risk_level="L3",
            payload_normalizer=_normalize_gift_code_create_payload,
            entity_state_builder=_gift_code_create_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_card_type",
            challenge_builder=_context_target_challenge,
            executor_kind="db",
            audit_action="admin_gift_code_create",
            result_sanitizer=_sanitize_gift_code_result,
            replay_result_builder=_rehydrate_gift_code_result,
        ),
        "node.sync_global": ActionPolicy(
            action="node.sync_global",
            target_type="node_sync",
            risk_level="L3",
            payload_normalizer=_normalize_node_sync_payload,
            entity_state_builder=_node_sync_state,
            preview_builder=_model_change_preview,
            challenge_kind="exact_phrase",
            challenge_builder=_management_challenge,
            executor_kind="external",
            audit_action="admin_nodes_sync",
            external_context_builder=_node_sync_external_context,
        ),
    }
)


ACTION_POLICY_ROUTES: dict[str, tuple[tuple[str, str], ...]] = {
    "payment.reconcile": (("POST", "/api/admin/payments/orders/{provider}/{order_id}/reconcile"),),
    "user.manual_create": (("POST", "/api/admin/users/manual"),),
    "user.extend": (
        ("POST", "/api/admin/users/{tg_id}/manual/extend"),
        ("POST", "/api/admin/users/{tg_id}/manual-extend"),
    ),
    "user.block": (("POST", "/api/admin/users/{tg_id}/manual/block"),),
    "user.regenerate_token": (("POST", "/api/admin/users/{tg_id}/manual/regenerate-token"),),
    "user.safe_delete": (("POST", "/api/admin/users/{tg_id}/safe-delete"),),
    "user.delete_test": (("POST", "/api/admin/users/{tg_id}/delete-test-user"),),
    "user.key_toggle": (("POST", "/api/admin/users/{tg_id}/keys/{node_code}/toggle"),),
    "user.key_reset_traffic": (("POST", "/api/admin/users/{tg_id}/keys/{node_code}/reset-traffic"),),
    "user.key_resync_subid": (("POST", "/api/admin/users/{tg_id}/keys/{node_code}/resync-subid"),),
    "user.key_limits": (("PUT", "/api/admin/users/{tg_id}/key-limits/{node_code}"),),
    "user.loyalty_grant": (("POST", "/api/admin/users/{tg_id}/loyalty/grant"),),
    "user.preset_run": (("POST", "/api/admin/users/{tg_id}/presets/run"),),
    "user.bulk_key_action": (("POST", "/api/admin/users/keys/bulk-action"),),
    "user.message": (("POST", "/api/admin/users/{tg_id}/message"),),
    "broadcast.send": (("POST", "/api/admin/broadcast"),),
    "promo.create": (("POST", "/api/admin/promos"),),
    "promo.update": (("PATCH", "/api/admin/promos/{code}"),),
    "promo.delete": (("DELETE", "/api/admin/promos/{code}"),),
    "plan.create": (("POST", "/api/admin/plans"),),
    "plan.update": (("PATCH", "/api/admin/plans/{code}"),),
    "plan.delete": (("DELETE", "/api/admin/plans/{code}"),),
    "live_update.create": (("POST", "/api/admin/live-updates"),),
    "live_update.update": (("PATCH", "/api/admin/live-updates/{update_id}"),),
    "live_update.delete": (("DELETE", "/api/admin/live-updates/{update_id}"),),
    "start_link.create": (("POST", "/api/admin/start-links"),),
    "start_link.update": (("PATCH", "/api/admin/start-links/{link_id}"),),
    "start_link.delete": (("DELETE", "/api/admin/start-links/{link_id}"),),
    "wheel_config.update": (("PUT", "/api/admin/wheel-config"),),
    "network_rollout_config.update": (("PUT", "/api/admin/network-rollout-config"),),
    "warp_material.replace": (("PUT", "/api/admin/client/warp/material"),),
    "promo_slots.update": (("PUT", "/api/admin/promo-slots"),),
    "referral.process": (("POST", "/api/admin/referrals/process"),),
    "loyalty_config.update": (("PUT", "/api/admin/loyalty-config"),),
    "campaign.create": (("POST", "/api/admin/campaigns"),),
    "campaign.update": (("PATCH", "/api/admin/campaigns/{campaign_id}"),),
    "campaign.delete": (("DELETE", "/api/admin/campaigns/{campaign_id}"),),
    "template.create": (("POST", "/api/admin/templates"),),
    "template.update": (("PATCH", "/api/admin/templates/{key}"),),
    "template.delete": (("DELETE", "/api/admin/templates/{key}"),),
    "access_key.issue": (("POST", "/api/admin/access-keys/issue"),),
    "gift_code.create": (("POST", "/api/admin/gift-codes"),),
    "ticket.reply": (("POST", "/api/admin/tickets/{ticket_id}/reply"),),
    "ticket.status": (("POST", "/api/admin/tickets/{ticket_id}/status"),),
    "provider_quota.create": (("POST", "/api/admin/provider-quotas"),),
    "provider_quota.update": (("PATCH", "/api/admin/provider-quotas/{node_code}"),),
    "provider_quota.delete": (("DELETE", "/api/admin/provider-quotas/{node_code}"),),
    "key.rotate": (("POST", "/api/admin/keys/{key_id}/rotate"),),
    "node.sync_global": (("POST", "/api/admin/nodes/sync"),),
    "node.drain": (("POST", "/api/admin/nodes/{node_code}/drain"),),
    "node.enable": (("POST", "/api/admin/nodes/{node_code}/enable"),),
    "node.undrain": (("POST", "/api/admin/nodes/{node_code}/undrain"),),
    "node.disable": (("POST", "/api/admin/nodes/{node_code}/disable"),),
    "node.resync": (("POST", "/api/admin/nodes/{node_code}/resync"),),
}


def action_policy_route_keys() -> frozenset[tuple[str, str]]:
    unknown = set(ACTION_POLICY_ROUTES) - set(ACTION_POLICIES)
    if unknown:
        raise RuntimeError(f"Routes reference unknown action policies: {sorted(unknown)!r}")
    route_keys = [
        route_key
        for routes in ACTION_POLICY_ROUTES.values()
        for route_key in routes
    ]
    if len(route_keys) != len(set(route_keys)):
        raise RuntimeError("An admin mutation route is assigned to multiple policies")
    return frozenset(route_keys)


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
) -> tuple[
    ActionPolicy,
    dict[str, str],
    dict[str, Any],
    dict[str, Any],
    EntityState | None,
    dict[str, Any] | None,
]:
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
            "payload_mismatch" if policy.action == "broadcast.send" else "intent_mismatch",
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
    _verify_confirmation(intent, confirmation_sha256_header)

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
            or int(facts["sent"]) + int(facts["failed"])
            != int(facts["attempted"])
            or succeeded != (int(facts["failed"]) == 0)
        ):
            return _malformed_external_outcome(
                raw_result=raw_result,
                intent_id=intent_id,
                audit_id=audit_id,
            )
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
        (
            policy,
            normalized_target,
            normalized_payload,
            runtime_payload,
            state,
            replay,
        ) = _validate_execution(
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
                            timeout=_external_timeout_seconds(
                                external_timeout_seconds
                            ),
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
                owner_policy = _policy_for(str(owner.action))
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

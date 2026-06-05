from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from models import User, WarpEvent, WarpMaterial
from network_rollout import managed_warp_policy, public_warp_policy


PUBLIC_FEATURE = "extended_protection"
PUBLIC_LABEL = "Расширенная защита"
TECHNICAL_LABEL = "WARP"

_SAFE_STATE_RE = re.compile(r"^[a-z0-9_:-]{2,32}$")
_SAFE_EVENT_RE = re.compile(r"^[a-z0-9_:-]{2,64}$")
_UNSAFE_KEY_FRAGMENTS = (
    "account",
    "auth",
    "bearer",
    "cookie",
    "key",
    "private",
    "secret",
    "subscription",
    "token",
    "url",
    "warp_config",
    "wireguard",
)
_UNSAFE_VALUE_RE = re.compile(r"(https?://|bearer\s+|private[-_ ]?key|access[-_ ]?token)", re.IGNORECASE)
_MATERIAL_SECRET_ENV_KEYS = (
    "WARP_MATERIAL_SECRET",
    "WEBAPP_SESSION_SECRET",
    "CHECKOUT_TICKET_SECRET",
    "BOT_TOKEN",
)
_DEFAULT_MATERIAL_MAX_AGE_HOURS = 24 * 30
_SUMMARY_WINDOW_HOURS = 24


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _iso(value: Any) -> str | None:
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.isoformat(timespec="seconds") + "Z"


def _clean_token(value: Any, *, fallback: str = "") -> str:
    raw = str(value or "").strip().lower()
    if not raw or not _SAFE_STATE_RE.match(raw):
        return fallback
    return raw


def _clean_event(value: Any, *, fallback: str = "runtime_event") -> str:
    raw = str(value or "").strip().lower()
    if not raw or not _SAFE_EVENT_RE.match(raw):
        return fallback
    return raw


def _env_int(
    name: str,
    *,
    default: int,
    minimum: int = 0,
    maximum: int = 1_000_000,
) -> int:
    try:
        value = int(str(os.getenv(name) or "").strip() or default)
    except Exception:
        value = default
    return max(minimum, min(maximum, value))


def _material_fernet() -> Fernet:
    secret = ""
    for key in _MATERIAL_SECRET_ENV_KEYS:
        secret = str(os.getenv(key) or "").strip()
        if secret:
            break
    if not secret:
        raise RuntimeError("WARP material encryption secret is not configured")
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def warp_material_max_age_hours() -> int:
    return _env_int(
        "WARP_MATERIAL_MAX_AGE_HOURS",
        default=_DEFAULT_MATERIAL_MAX_AGE_HOURS,
        minimum=1,
        maximum=24 * 365,
    )


def warp_material_stale_cutoff(*, now: datetime | None = None) -> datetime:
    base = now or _utcnow()
    return base - timedelta(hours=warp_material_max_age_hours())


def warp_material_is_stale(row: WarpMaterial, *, now: datetime | None = None) -> bool:
    if not bool(getattr(row, "is_active", False)):
        return False
    provisioned_at = getattr(row, "provisioned_at", None)
    if not isinstance(provisioned_at, datetime):
        return True
    return provisioned_at < warp_material_stale_cutoff(now=now)


def _canonical_json(value: Any) -> str:
    normalized = value if isinstance(value, (dict, list)) else {}
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _encrypt_json(value: Any) -> str:
    raw = _canonical_json(value).encode("utf-8")
    return _material_fernet().encrypt(raw).decode("ascii")


def _decrypt_json(value: str | None) -> dict[str, Any]:
    raw = str(value or "").strip()
    if not raw:
        return {}
    try:
        decoded = _material_fernet().decrypt(raw.encode("ascii"))
    except (InvalidToken, ValueError, TypeError) as exc:
        raise RuntimeError("WARP material ciphertext cannot be decrypted") from exc
    loaded = json.loads(decoded.decode("utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _unsafe_key(key: Any) -> bool:
    lowered = str(key or "").strip().lower().replace("-", "_")
    if not lowered:
        return True
    return any(fragment in lowered for fragment in _UNSAFE_KEY_FRAGMENTS)


def sanitize_warp_meta(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, child in value.items():
            clean_key = str(key or "").strip()
            if _unsafe_key(clean_key):
                continue
            clean_child = sanitize_warp_meta(child)
            if clean_child is not None:
                out[clean_key[:64]] = clean_child
        return out
    if isinstance(value, (list, tuple)):
        out_list = [sanitize_warp_meta(item) for item in list(value)[:20]]
        return [item for item in out_list if item is not None]
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        if _UNSAFE_VALUE_RE.search(raw):
            return "[redacted]"
        return raw[:500]
    return str(value)[:200]


def _query_active_warp_material(
    session,
    *,
    user: User,
    install_id: str | None,
) -> WarpMaterial | None:
    clean_install = str(install_id or "").strip()
    base = (
        session.query(WarpMaterial)
        .filter(WarpMaterial.tg_id == int(user.tg_id))
        .filter(WarpMaterial.is_active == True)  # noqa: E712
    )
    if clean_install:
        row = (
            base.filter(WarpMaterial.install_id == clean_install)
            .order_by(WarpMaterial.id.desc())
            .first()
        )
        if row:
            return row
    return (
        base.filter(WarpMaterial.install_id.is_(None))
        .order_by(WarpMaterial.id.desc())
        .first()
    )


def _warp_policy_from_material(
    row: WarpMaterial,
    *,
    include_secrets: bool,
) -> dict[str, Any]:
    wireguard_config = _decrypt_json(getattr(row, "wireguard_ciphertext", None))
    account = _decrypt_json(getattr(row, "account_ciphertext", None))
    raw_policy = {
        "enabled": True,
        "state": str(getattr(row, "state", "") or "ready"),
        "mode": str(getattr(row, "mode", "") or "proxy_over_warp"),
        "source": "backend_material_store",
        "wireguard_config": wireguard_config,
        "account": account,
    }
    wrapper = {"warp_policy": raw_policy}
    return managed_warp_policy(wrapper) if include_secrets else public_warp_policy(wrapper)


def _material_unavailable_policy(
    *,
    include_secrets: bool,
    state: str = "material_unavailable",
) -> dict[str, Any]:
    wrapper = {
        "warp_policy": {
            "enabled": True,
            "state": state,
            "mode": "proxy_over_warp",
            "source": "backend_material_store",
        }
    }
    return managed_warp_policy(wrapper) if include_secrets else public_warp_policy(wrapper)


def managed_warp_policy_for_user(
    session,
    *,
    user: User,
    install_id: str | None,
    rollout_config: dict[str, Any],
) -> dict[str, Any]:
    row = _query_active_warp_material(session, user=user, install_id=install_id)
    if not row:
        return managed_warp_policy(rollout_config)
    if warp_material_is_stale(row):
        return _material_unavailable_policy(include_secrets=True, state="material_stale")
    try:
        return _warp_policy_from_material(row, include_secrets=True)
    except RuntimeError:
        return _material_unavailable_policy(include_secrets=True)


def public_warp_policy_for_user(
    session,
    *,
    user: User,
    install_id: str | None,
    rollout_config: dict[str, Any],
) -> dict[str, Any]:
    row = _query_active_warp_material(session, user=user, install_id=install_id)
    if not row:
        return public_warp_policy(rollout_config)
    if warp_material_is_stale(row):
        return _material_unavailable_policy(include_secrets=False, state="material_stale")
    try:
        return _warp_policy_from_material(row, include_secrets=False)
    except RuntimeError:
        return _material_unavailable_policy(include_secrets=False)


def provision_warp_material(
    session,
    *,
    user: User,
    install_id: str | None,
    wireguard_config: dict[str, Any],
    account: dict[str, Any] | None = None,
    source: str = "operator_provisioned",
    mode: str = "proxy_over_warp",
) -> WarpMaterial:
    clean_install = str(install_id or "").strip() or None
    candidate = {
        "enabled": True,
        "state": "ready",
        "mode": str(mode or "proxy_over_warp").strip() or "proxy_over_warp",
        "source": "backend_material_store",
        "wireguard_config": wireguard_config
        if isinstance(wireguard_config, dict)
        else {},
        "account": account if isinstance(account, dict) else {},
    }
    policy = managed_warp_policy({"warp_policy": candidate})
    if not bool(policy.get("runtime_ready")):
        raise ValueError("WARP material does not contain a usable WireGuard config")

    now = _utcnow()
    previous = (
        session.query(WarpMaterial)
        .filter(WarpMaterial.tg_id == int(user.tg_id))
        .filter(WarpMaterial.is_active == True)  # noqa: E712
    )
    if clean_install:
        previous = previous.filter(WarpMaterial.install_id == clean_install)
    else:
        previous = previous.filter(WarpMaterial.install_id.is_(None))
    for row in previous.all():
        row.is_active = False
        row.state = "rotated"
        row.updated_at = now

    wireguard_plain = dict(policy.get("wireguard_config") or {})
    account_plain = dict(policy.get("account") or {})
    wireguard_json = _canonical_json(wireguard_plain)
    account_json = _canonical_json(account_plain)
    material_hash = hashlib.sha256(
        f"{wireguard_json}\n{account_json}".encode("utf-8")
    ).hexdigest()
    row = WarpMaterial(
        tg_id=int(user.tg_id),
        install_id=clean_install,
        source=_clean_event(source, fallback="operator_provisioned")[:64],
        mode=str(policy.get("mode") or "proxy_over_warp")[:32],
        state="ready",
        wireguard_ciphertext=_encrypt_json(wireguard_plain),
        account_ciphertext=_encrypt_json(account_plain) if account_plain else None,
        material_hash=material_hash,
        is_active=True,
        provisioned_at=now,
        updated_at=now,
    )
    session.add(row)
    return row


def mark_warp_material_rotation_requested(
    session,
    *,
    user: User,
    install_id: str | None,
) -> WarpMaterial | None:
    row = _query_active_warp_material(session, user=user, install_id=install_id)
    if not row:
        return None
    now = _utcnow()
    row.state = "rotation_requested"
    row.rotation_requested_at = now
    row.updated_at = now
    return row


def revoke_warp_material(
    session,
    *,
    user: User,
    install_id: str | None,
) -> WarpMaterial | None:
    row = _query_active_warp_material(session, user=user, install_id=install_id)
    if not row:
        return None
    now = _utcnow()
    row.is_active = False
    row.state = "revoked"
    row.revoked_at = now
    row.updated_at = now
    return row


def warp_material_public_payload(row: WarpMaterial, *, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    safe_policy = policy or {}
    return {
        "id": int(getattr(row, "id", 0) or 0),
        "tg_id": int(getattr(row, "tg_id", 0) or 0),
        "install_id": str(getattr(row, "install_id", "") or "") or None,
        "source": str(getattr(row, "source", "") or ""),
        "mode": str(getattr(row, "mode", "") or "proxy_over_warp"),
        "state": str(getattr(row, "state", "") or ""),
        "runtime_ready": bool(safe_policy.get("runtime_ready")),
        "wireguard_config_available": bool(safe_policy.get("wireguard_config_available")),
        "material_hash": str(getattr(row, "material_hash", "") or "") or None,
        "is_active": bool(getattr(row, "is_active", False)),
        "provisioned_at": _iso(getattr(row, "provisioned_at", None)),
        "rotation_requested_at": _iso(getattr(row, "rotation_requested_at", None)),
        "revoked_at": _iso(getattr(row, "revoked_at", None)),
        "updated_at": _iso(getattr(row, "updated_at", None)),
    }


def build_warp_admin_summary(session, *, now: datetime | None = None) -> dict[str, Any]:
    current = now or _utcnow()
    recent_since = current - timedelta(hours=_SUMMARY_WINDOW_HOURS)
    materials = list(session.query(WarpMaterial).all())
    active_materials = [
        row for row in materials if bool(getattr(row, "is_active", False))
    ]
    stale_materials = [row for row in active_materials if warp_material_is_stale(row, now=current)]
    revoked_materials = [
        row
        for row in materials
        if str(getattr(row, "state", "") or "") == "revoked"
        or getattr(row, "revoked_at", None) is not None
    ]
    rotation_requested_materials = [
        row
        for row in active_materials
        if str(getattr(row, "state", "") or "") == "rotation_requested"
    ]

    events = list(session.query(WarpEvent).order_by(WarpEvent.id.asc()).all())
    latest_consent: dict[tuple[int, str], bool] = {}
    recent_material_provisions = 0
    recent_provisioning_failures = 0
    recent_rotation_requests = 0
    recent_runtime_errors = 0
    recent_rate_limits = 0
    recent_runtime_events: list[dict[str, Any]] = []
    runtime_state_counts: dict[str, int] = {}

    for row in events:
        event_name = str(getattr(row, "event_name", "") or "")
        state = str(getattr(row, "state", "") or "")
        key = (
            int(getattr(row, "tg_id", 0) or 0),
            str(getattr(row, "install_id", "") or ""),
        )
        if event_name == "consent":
            latest_consent[key] = True
        elif event_name == "revoke":
            latest_consent[key] = False
        elif bool(getattr(row, "consented", False)):
            latest_consent[key] = True

        created_at = getattr(row, "created_at", None)
        if not isinstance(created_at, datetime) or created_at < recent_since:
            continue
        if event_name == "material_provisioned":
            recent_material_provisions += 1
        if event_name == "material_provision_failed":
            recent_provisioning_failures += 1
        if event_name == "rotate_requested":
            recent_rotation_requests += 1
        if event_name.endswith("_rate_limited") or state == "rate_limited":
            recent_rate_limits += 1
        if event_name.startswith("runtime_") and state in {"error", "failed", "fallback"}:
            recent_runtime_errors += 1
        if event_name.startswith("runtime_"):
            normalized_state = state or "unknown"
            runtime_state_counts[normalized_state] = runtime_state_counts.get(normalized_state, 0) + 1
            recent_runtime_events.append(
                {
                    "event_name": event_name,
                    "state": normalized_state,
                    "reason_code": str(getattr(row, "reason_code", "") or "") or None,
                    "runtime_ready": bool(getattr(row, "runtime_ready", False)),
                    "created_at": _iso(created_at),
                }
            )

    recent_runtime_events.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    last_runtime_event = recent_runtime_events[0] if recent_runtime_events else {}

    return {
        "generated_at": _iso(current),
        "window": {"hours": _SUMMARY_WINDOW_HOURS},
        "material_max_age_hours": warp_material_max_age_hours(),
        "materials": {
            "total": len(materials),
            "active": len(active_materials),
            "stale_active": len(stale_materials),
            "revoked": len(revoked_materials),
            "rotation_requested": len(rotation_requested_materials),
        },
        "events": {
            "active_consents": sum(1 for value in latest_consent.values() if value),
            "recent_material_provisions": recent_material_provisions,
            "recent_provisioning_failures": recent_provisioning_failures,
            "recent_rotation_requests": recent_rotation_requests,
            "recent_runtime_errors": recent_runtime_errors,
            "recent_rate_limits": recent_rate_limits,
        },
        "runtime": {
            "last_state": last_runtime_event.get("state"),
            "last_reason_code": last_runtime_event.get("reason_code"),
            "last_event_at": last_runtime_event.get("created_at"),
            "state_counts": runtime_state_counts,
            "recent_events": recent_runtime_events[:5],
        },
    }


def latest_warp_events(session, *, user: User, install_id: str | None) -> list[WarpEvent]:
    query = session.query(WarpEvent).filter(WarpEvent.tg_id == int(user.tg_id))
    clean_install = str(install_id or "").strip()
    if clean_install:
        query = query.filter(WarpEvent.install_id == clean_install)
    return list(query.order_by(WarpEvent.id.asc()).all())


def build_warp_status(session, *, user: User, policy: dict[str, Any], install_id: str | None = None) -> dict[str, Any]:
    runtime_ready = bool((policy or {}).get("runtime_ready"))
    enabled = bool((policy or {}).get("enabled"))
    wireguard_available = bool((policy or {}).get("wireguard_config_available"))
    mode = str((policy or {}).get("mode") or "proxy_over_warp").strip() or "proxy_over_warp"
    source = str((policy or {}).get("source") or "backend_managed").strip() or "backend_managed"
    policy_state = str((policy or {}).get("state") or "").strip()

    rows = latest_warp_events(session, user=user, install_id=install_id)
    consented = False
    consented_at: str | None = None
    revoked_at: str | None = None
    state = "ready_to_consent" if runtime_ready else "not_ready"
    last_event_payload: dict[str, Any] | None = None

    for row in rows:
        event_name = str(getattr(row, "event_name", "") or "").strip()
        row_state = str(getattr(row, "state", "") or "").strip()
        if event_name == "consent":
            consented = True
            consented_at = _iso(getattr(row, "created_at", None))
            revoked_at = None
            state = row_state or "consented"
        elif event_name == "revoke":
            consented = False
            revoked_at = _iso(getattr(row, "created_at", None))
            state = row_state or "revoked"
        else:
            if row_state:
                state = row_state
            if getattr(row, "consented", False):
                consented = True

        last_event_payload = {
            "event_name": event_name,
            "state": row_state or state,
            "reason_code": str(getattr(row, "reason_code", "") or "") or None,
            "created_at": _iso(getattr(row, "created_at", None)),
        }

    if not runtime_ready:
        consented = False
        state = "not_ready"

    if state == "consented":
        consented = True
    if state == "revoked":
        consented = False

    return {
        "feature": PUBLIC_FEATURE,
        "public_label": PUBLIC_LABEL,
        "technical_label": TECHNICAL_LABEL,
        "enabled": enabled,
        "runtime_ready": runtime_ready,
        "can_enable": bool(runtime_ready and not consented),
        "consented": consented,
        "state": state,
        "policy_state": policy_state,
        "mode": mode,
        "source": source,
        "wireguard_config_available": wireguard_available,
        "consented_at": consented_at,
        "revoked_at": revoked_at,
        "last_event": last_event_payload,
    }


def record_warp_event(
    session,
    *,
    user: User,
    install_id: str | None,
    policy: dict[str, Any],
    event_name: str,
    state: str,
    reason_code: str | None = None,
    consented: bool = False,
    meta: dict[str, Any] | None = None,
) -> WarpEvent:
    safe_meta = sanitize_warp_meta(meta or {})
    row = WarpEvent(
        tg_id=int(user.tg_id),
        install_id=str(install_id or "").strip() or None,
        event_name=_clean_event(event_name),
        state=_clean_token(state, fallback="not_ready"),
        reason_code=_clean_event(reason_code, fallback="") or None,
        runtime_ready=bool((policy or {}).get("runtime_ready")),
        consented=bool(consented),
        meta_json=json.dumps(safe_meta, ensure_ascii=False, sort_keys=True)[:8000] if safe_meta else None,
        created_at=_utcnow(),
    )
    session.add(row)
    return row

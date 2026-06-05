from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from models import User, WarpEvent


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

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func

from models import AppDevice, PlanCatalog, User


ROUTE_MODE_ALL_TRAFFIC = "all_traffic"
ROUTE_MODE_SELECTED_APPS = "selected_apps"
ROUTE_MODE_VALUES = {ROUTE_MODE_ALL_TRAFFIC, ROUTE_MODE_SELECTED_APPS}
DEFAULT_FREE_DEVICE_LIMIT = 1
DEFAULT_PAID_DEVICE_LIMIT = 5
SELECTED_APPS_LIMIT = 128
SELECTED_APP_IDENTIFIER_MAX_LENGTH = 260
DESKTOP_ROUTE_PLATFORMS = {"windows", "linux", "macos", "darwin"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _clean_text(value: Any, *, max_len: int, fallback: str = "") -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    return text[:max_len]


def normalize_install_id(value: Any) -> str:
    return _clean_text(value, max_len=128)


def normalize_device_name(value: Any, *, fallback: str = "Current device") -> str:
    return _clean_text(value, max_len=120, fallback=fallback)


def normalize_route_mode(value: Any, *, fallback: str = ROUTE_MODE_ALL_TRAFFIC) -> str:
    text = str(value or "").strip().lower()
    if text in ROUTE_MODE_VALUES:
        return text
    return fallback


def normalize_selected_apps(value: Any, *, limit: int = SELECTED_APPS_LIMIT) -> list[str]:
    source = value
    if isinstance(source, str):
        text = source.strip()
        if not text:
            source = []
        else:
            try:
                source = json.loads(text)
            except Exception:
                source = [text]
    elif source is None:
        source = []

    if not isinstance(source, (list, tuple, set)):
        return []

    out: list[str] = []
    seen: set[str] = set()
    for raw in source:
        item = str(raw or "").strip()[:SELECTED_APP_IDENTIFIER_MAX_LENGTH]
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
        if len(out) >= limit:
            break
    return out


def _default_route_requires_elevated(platform: Any) -> bool:
    return str(platform or "").strip().lower() in DESKTOP_ROUTE_PLATFORMS


def _safe_iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return None
    return str(value)


def _device_query(s, *, user: User, install_id: str):
    return (
        s.query(AppDevice)
        .filter(AppDevice.tg_id == int(user.tg_id))
        .filter(AppDevice.install_id == normalize_install_id(install_id))
    )


def get_device(s, *, user: User, install_id: str) -> AppDevice | None:
    normalized = normalize_install_id(install_id)
    if not normalized:
        return None
    return _device_query(s, user=user, install_id=normalized).first()


def backfill_user_device(s, *, user: User, now: datetime | None = None) -> AppDevice | None:
    install_id = normalize_install_id(getattr(user, "app_install_id", None))
    if not install_id:
        return None
    existing = get_device(s, user=user, install_id=install_id)
    if existing:
        return existing

    stamp = now or _utcnow()
    platform = _clean_text(getattr(user, "app_platform", None), max_len=32) or None
    device_name = normalize_device_name(
        getattr(user, "app_device_name", None) or getattr(user, "display_name", None)
    )
    row = AppDevice(
        tg_id=int(user.tg_id),
        install_id=install_id,
        device_name=device_name,
        display_name=device_name,
        platform=platform,
        os_version=_clean_text(getattr(user, "app_os_version", None), max_len=64) or None,
        app_version=_clean_text(getattr(user, "app_version", None), max_len=32) or None,
        locale=_clean_text(getattr(user, "app_locale", None), max_len=32) or None,
        timezone=_clean_text(getattr(user, "app_timezone", None), max_len=64) or None,
        last_seen_at=getattr(user, "app_last_seen_at", None) or getattr(user, "created_at", None) or stamp,
        last_ip=_clean_text(getattr(user, "app_last_ip", None), max_len=64) or None,
        route_mode=normalize_route_mode(getattr(user, "route_mode", None)),
        route_selected_apps_json=json.dumps(
            normalize_selected_apps(getattr(user, "route_selected_apps_json", None)),
            ensure_ascii=True,
        ),
        route_requires_elevated_privileges=(
            bool(getattr(user, "route_requires_elevated_privileges"))
            if getattr(user, "route_requires_elevated_privileges", None) is not None
            else _default_route_requires_elevated(platform)
        ),
        created_at=stamp,
        updated_at=stamp,
    )
    s.add(row)
    s.flush()
    return row


def upsert_current_device(
    s,
    *,
    user: User,
    payload: Any,
    now: datetime | None = None,
    request_client_ip: str = "",
) -> AppDevice:
    install_id = normalize_install_id(getattr(payload, "install_id", None))
    if not install_id:
        raise ValueError("install_id is required")

    stamp = now or _utcnow()
    existing_any = s.query(AppDevice).filter(AppDevice.install_id == install_id).first()
    if existing_any and int(existing_any.tg_id) != int(user.tg_id):
        raise ValueError("install_id belongs to another account")

    row = existing_any or AppDevice(tg_id=int(user.tg_id), install_id=install_id, created_at=stamp)
    if not existing_any:
        s.add(row)

    platform = _clean_text(getattr(payload, "platform", None), max_len=32) or row.platform
    device_name = normalize_device_name(getattr(payload, "device_name", None) or row.device_name)
    row.tg_id = int(user.tg_id)
    row.device_name = device_name
    if not _clean_text(row.display_name, max_len=120):
        row.display_name = device_name
    row.platform = platform
    row.model = _clean_text(getattr(payload, "model", None), max_len=120) or row.model
    row.os_version = _clean_text(getattr(payload, "os_version", None), max_len=64) or row.os_version
    row.app_version = _clean_text(getattr(payload, "app_version", None), max_len=32) or row.app_version
    row.locale = _clean_text(getattr(payload, "locale", None), max_len=32) or row.locale
    row.timezone = _clean_text(getattr(payload, "time_zone", None), max_len=64) or row.timezone
    row.last_seen_at = stamp
    row.last_ip = _clean_text(request_client_ip, max_len=64) or row.last_ip
    row.route_mode = normalize_route_mode(getattr(payload, "route_mode", None) or row.route_mode)
    selected_apps = normalize_selected_apps(
        getattr(payload, "selected_apps", None)
        if getattr(payload, "selected_apps", None) is not None
        else row.route_selected_apps_json
    )
    if row.route_mode != ROUTE_MODE_SELECTED_APPS:
        selected_apps = []
    row.route_selected_apps_json = json.dumps(selected_apps, ensure_ascii=True)
    requires = getattr(payload, "requires_elevated_privileges", None)
    row.route_requires_elevated_privileges = (
        bool(requires)
        if requires is not None
        else (
            bool(row.route_requires_elevated_privileges)
            if row.route_requires_elevated_privileges is not None
            else _default_route_requires_elevated(platform)
        )
    )
    row.revoked_at = None
    row.revoked_reason = None
    row.updated_at = stamp

    user.is_app_user = True
    user.app_install_id = install_id
    user.app_device_name = device_name
    user.app_platform = platform
    user.app_os_version = row.os_version
    user.app_version = row.app_version
    user.app_locale = row.locale
    user.app_timezone = row.timezone
    user.app_last_seen_at = stamp
    user.app_last_ip = row.last_ip
    user.route_mode = row.route_mode
    user.route_selected_apps_json = row.route_selected_apps_json
    user.route_requires_elevated_privileges = row.route_requires_elevated_privileges

    s.flush()
    return row


def rename_device(
    s,
    *,
    user: User,
    install_id: str,
    display_name: str,
    now: datetime | None = None,
) -> AppDevice | None:
    row = get_device(s, user=user, install_id=install_id)
    if not row:
        return None
    row.display_name = normalize_device_name(display_name)
    row.updated_at = now or _utcnow()
    s.flush()
    return row


def revoke_device(
    s,
    *,
    user: User,
    install_id: str,
    now: datetime | None = None,
    reason: str = "",
) -> AppDevice | None:
    row = get_device(s, user=user, install_id=install_id)
    if not row:
        return None
    stamp = now or _utcnow()
    row.revoked_at = stamp
    row.revoked_reason = _clean_text(reason, max_len=200) or None
    row.updated_at = stamp
    s.flush()
    return row


def active_device_count(s, *, user: User) -> int:
    return int(
        s.query(func.count(AppDevice.id))
        .filter(AppDevice.tg_id == int(user.tg_id))
        .filter(AppDevice.revoked_at.is_(None))
        .scalar()
        or 0
    )


def resolve_device_limit(s, *, user: User) -> int:
    sub_type = str(getattr(user, "sub_type", "") or "").strip().upper()
    plan_code = str(getattr(user, "current_plan_code", "") or "").strip().lower()
    if sub_type == "PAID":
        if plan_code:
            plan = s.query(PlanCatalog).filter(func.lower(PlanCatalog.code) == plan_code).first()
            if plan and int(plan.device_limit or 0) > 0:
                return int(plan.device_limit)
        return DEFAULT_PAID_DEVICE_LIMIT
    return DEFAULT_FREE_DEVICE_LIMIT


def device_limit_status(s, *, user: User, candidate_install_id: str | None = None) -> dict[str, Any]:
    limit = max(0, int(resolve_device_limit(s, user=user)))
    active_count = active_device_count(s, user=user)
    candidate = normalize_install_id(candidate_install_id)
    if candidate:
        existing = get_device(s, user=user, install_id=candidate)
        if existing and existing.revoked_at is None:
            return {
                "allowed": True,
                "limit": limit,
                "active_count": active_count,
                "remaining": max(limit - active_count, 0),
                "reason": "existing_device",
            }

    allowed = active_count < limit
    return {
        "allowed": bool(allowed),
        "limit": limit,
        "active_count": active_count,
        "remaining": max(limit - active_count, 0),
        "reason": "available" if allowed else "device_limit_reached",
    }


def device_public_payload(device: AppDevice, *, current_install_id: str | None = None) -> dict[str, Any]:
    install_id = normalize_install_id(getattr(device, "install_id", None))
    display_name = normalize_device_name(getattr(device, "display_name", None) or getattr(device, "device_name", None))
    route_mode = normalize_route_mode(getattr(device, "route_mode", None))
    selected_apps = normalize_selected_apps(getattr(device, "route_selected_apps_json", None))
    if route_mode != ROUTE_MODE_SELECTED_APPS:
        selected_apps = []
    return {
        "id": install_id,
        "install_id": install_id,
        "name": display_name,
        "device_name": normalize_device_name(getattr(device, "device_name", None)),
        "display_name": display_name,
        "platform": _clean_text(getattr(device, "platform", None), max_len=32, fallback="device"),
        "os_version": _clean_text(getattr(device, "os_version", None), max_len=64) or None,
        "app_version": _clean_text(getattr(device, "app_version", None), max_len=32) or None,
        "last_seen_at": _safe_iso(getattr(device, "last_seen_at", None) or getattr(device, "created_at", None)),
        "route_mode": route_mode,
        "selected_apps": selected_apps,
        "requires_elevated_privileges": bool(getattr(device, "route_requires_elevated_privileges", False)),
        "revoked": bool(getattr(device, "revoked_at", None)),
        "revoked_at": _safe_iso(getattr(device, "revoked_at", None)),
        "is_current": bool(current_install_id and install_id == normalize_install_id(current_install_id)),
    }


def list_user_devices(
    s,
    *,
    user: User,
    current_install_id: str | None = None,
    include_revoked: bool = False,
) -> list[dict[str, Any]]:
    backfill_user_device(s, user=user)
    q = s.query(AppDevice).filter(AppDevice.tg_id == int(user.tg_id))
    if not include_revoked:
        q = q.filter(AppDevice.revoked_at.is_(None))
    rows = q.order_by(AppDevice.last_seen_at.desc().nullslast(), AppDevice.created_at.desc(), AppDevice.id.desc()).all()
    return [device_public_payload(row, current_install_id=current_install_id) for row in rows]

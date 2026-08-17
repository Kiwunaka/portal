from __future__ import annotations

import json
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable

from fastapi import HTTPException

from account_foundation_service import ensure_user_account_foundation
from economy_service import TRIAL_DURATION_DAYS, reserve_trial
from free_cycle_service import mark_user_became_free
from models import AccountDevice, StartLink, User
from network_rollout import resolved_client_policy
from public_urls import build_subscription_url

ROUTE_MODE_ALL_TRAFFIC = "all_traffic"
ROUTE_MODE_SELECTED_APPS = "selected_apps"
_ROUTE_MODE_VALUES = {ROUTE_MODE_ALL_TRAFFIC, ROUTE_MODE_SELECTED_APPS}
_DESKTOP_ROUTE_PLATFORMS = {"windows", "linux", "macos", "darwin"}
ROUTE_POLICY_SELECTED_APPS_REQUIRED_CODE = "selected_apps_required"
APP_TELEGRAM_START_LINK_TTL_SECONDS = 15 * 60


class RoutePolicyValidationError(ValueError):
    """A stable, user-safe route-policy validation failure."""

    code = ROUTE_POLICY_SELECTED_APPS_REQUIRED_CODE

    def __init__(self) -> None:
        super().__init__("Select at least one app before using selected-apps routing.")


def normalize_app_device_name(value: str | None, *, fallback: str = "Current device") -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    for prefix in (
        "POKROV Android ",
        "POKROV Windows ",
        "POKROV Linux ",
        "POKROV macOS ",
        "POKROV iOS ",
    ):
        if text.casefold().startswith(prefix.casefold()):
            text = text[len(prefix) :].strip()
            if text:
                first, separator, tail = text.partition(" ")
                if first.islower():
                    first = first.capitalize()
                text = first + (separator + tail if separator else "")
            break
    return text[:120]


def normalize_route_mode(value: str | None, *, fallback: str = ROUTE_MODE_ALL_TRAFFIC) -> str:
    text = str(value or "").strip().lower()
    if text in _ROUTE_MODE_VALUES:
        return text
    return fallback


def normalize_selected_apps(value: Any, *, limit: int = 128) -> list[str]:
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

    normalized: list[str] = []
    seen: set[str] = set()
    for raw in source:
        text = str(raw or "").strip()
        if not text:
            continue
        item = text[:260]
        dedupe_key = item.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        normalized.append(item)
        if len(normalized) >= limit:
            break
    return normalized


def _default_route_requires_elevated_privileges(user: User | None) -> bool:
    platform = str(
        (getattr(user, "app_platform", None) if user is not None else "")
        or (getattr(user, "platform", None) if user is not None else "")
        or ""
    ).strip().lower()
    return platform in _DESKTOP_ROUTE_PLATFORMS


def _default_route_requires_for_platform(platform: str | None) -> bool:
    return str(platform or "").strip().lower() in _DESKTOP_ROUTE_PLATFORMS


def resolve_route_policy(
    user: User | None,
    *,
    route_mode: str | None = None,
    selected_apps: Any = None,
    requires_elevated_privileges: bool | None = None,
) -> dict[str, Any]:
    mode = normalize_route_mode(
        route_mode if route_mode is not None else (getattr(user, "route_mode", None) if user is not None else None)
    )
    apps_source = (
        selected_apps
        if selected_apps is not None
        else (getattr(user, "route_selected_apps_json", None) if user is not None else None)
    )
    apps = normalize_selected_apps(apps_source)
    if mode != ROUTE_MODE_SELECTED_APPS:
        apps = []

    if requires_elevated_privileges is None:
        persisted = getattr(user, "route_requires_elevated_privileges", None) if user is not None else None
        required = _default_route_requires_elevated_privileges(user) if persisted is None else bool(persisted)
    else:
        required = bool(requires_elevated_privileges)

    return {
        "route_mode": mode,
        "selected_apps": apps,
        "requires_elevated_privileges": required,
        "route_policy": {
            "mode": mode,
            "selected_apps": apps,
            "requires_elevated_privileges": required,
        },
    }


def persist_route_policy(
    user: User,
    *,
    route_mode: str | None = None,
    selected_apps: Any = None,
    requires_elevated_privileges: bool | None = None,
) -> dict[str, Any]:
    policy = resolve_route_policy(
        user,
        route_mode=route_mode,
        selected_apps=selected_apps,
        requires_elevated_privileges=requires_elevated_privileges,
    )
    if (
        policy["route_mode"] == ROUTE_MODE_SELECTED_APPS
        and not policy["selected_apps"]
    ):
        raise RoutePolicyValidationError()
    user.route_mode = str(policy["route_mode"])
    user.route_selected_apps_json = json.dumps(policy["selected_apps"], ensure_ascii=True)
    user.route_requires_elevated_privileges = bool(policy["requires_elevated_privileges"])
    return policy


def _next_app_account_tg_id(session) -> int:
    from sqlalchemy import func

    max_id = session.query(func.max(User.tg_id)).filter(User.tg_id >= 9_000_000_000_000).scalar()
    if max_id is None:
        return 9_000_000_000_000
    return int(max_id) + 1


def _generate_sub_token() -> str:
    return secrets.token_urlsafe(32)


def build_client_policy(
    *,
    session=None,
    user: User | None = None,
    install_id: str | None = None,
    carrier: str | None = None,
    rollout_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    client_policy = resolved_client_policy(
        session=session,
        user=user,
        install_id=install_id,
        carrier=carrier,
        rollout_config=rollout_config,
    )
    client_policy.update(resolve_route_policy(user))
    return client_policy


def expire_app_telegram_start_codes(
    session,
    *,
    now: datetime,
    account_tg_id: int | None = None,
) -> int:
    """Deactivate expired app-to-Telegram handoffs without deleting audit rows."""

    cutoff = now - timedelta(seconds=APP_TELEGRAM_START_LINK_TTL_SECONDS)
    query = session.query(StartLink).filter(
        StartLink.is_active == True,
        StartLink.target_action.like("app_link:%"),
        StartLink.updated_at < cutoff,
    )
    if account_tg_id is not None:
        query = query.filter(StartLink.target_action == f"app_link:{int(account_tg_id)}")
    rows = query.with_for_update().all()
    for row in rows:
        row.is_active = False
        row.updated_at = now
    if rows:
        session.flush()
    return len(rows)


def app_telegram_start_link_is_fresh(row: StartLink | None, *, now: datetime) -> bool:
    if row is None or not bool(getattr(row, "is_active", False)):
        return False
    action = str(getattr(row, "target_action", "") or "").strip().lower()
    if not action.startswith("app_link:"):
        return True
    updated_at = getattr(row, "updated_at", None)
    return bool(
        updated_at is not None
        and updated_at >= now - timedelta(seconds=APP_TELEGRAM_START_LINK_TTL_SECONDS)
    )


def create_app_telegram_start_code(session, *, account_tg_id: int, now: datetime) -> str:
    action = f"app_link:{int(account_tg_id)}"
    expire_app_telegram_start_codes(
        session,
        now=now,
        account_tg_id=int(account_tg_id),
    )
    existing = (
        session.query(StartLink)
        .filter(StartLink.target_action == action)
        .filter(StartLink.is_active == True)
        .order_by(StartLink.updated_at.desc(), StartLink.id.desc())
        .first()
    )
    if existing and str(existing.code or "").strip():
        existing.updated_at = now
        session.flush()
        return str(existing.code).strip().lower()

    for _ in range(10):
        code = f"app{secrets.token_urlsafe(12).replace('-', '').replace('_', '').lower()}"[:32]
        duplicate = session.query(StartLink.id).filter(StartLink.code == code).first()
        if duplicate:
            continue
        row = StartLink(
            code=code,
            description=f"App Telegram link for {int(account_tg_id)}",
            target_action=action[:64],
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        session.flush()
        return code
    raise HTTPException(status_code=500, detail="Unable to create Telegram link")


def upsert_app_trial_user(
    *,
    s,
    payload,
    now: datetime,
    trial_days: int,
    request_client_ip: str = "",
) -> tuple[User, bool]:
    install_id = str(getattr(payload, "install_id", "") or "").strip()[:128]
    if not install_id:
        raise HTTPException(status_code=400, detail="install_id is required")

    canonical_trial_days = max(1, int(trial_days or 1))
    device_name = normalize_app_device_name(getattr(payload, "device_name", None))
    client_ip = str(request_client_ip or "").strip()[:64]
    user = s.query(User).filter(User.app_install_id == install_id).first()
    created = False

    if not user:
        tg_id = _next_app_account_tg_id(s)
        user = User(
            tg_id=int(tg_id),
            username=f"app_{str(tg_id)[-6:]}",
            uuid=str(uuid.uuid4()),
            email=f"APP_{int(tg_id)}",
            sub_type="FREE",
            current_plan_code="trial",
            created_at=now,
            expiry_at=now + timedelta(days=canonical_trial_days),
            is_active=True,
            stars_paid=0,
            total_gb=0,
            trial_used=True,
            tos_accepted=True,
            first_purchase_done=False,
            sub_token=_generate_sub_token(),
            is_manual=False,
            is_app_user=True,
            display_name=device_name,
            app_install_id=install_id,
            app_device_name=device_name,
            app_platform=str(getattr(payload, "platform", "") or "").strip()[:32],
            app_os_version=str(getattr(payload, "os_version", "") or "").strip()[:64] or None,
            app_version=str(getattr(payload, "app_version", "") or "").strip()[:32] or None,
            app_locale=str(getattr(payload, "locale", "") or "").strip()[:32] or None,
            app_timezone=str(getattr(payload, "time_zone", "") or "").strip()[:64] or None,
            app_last_seen_at=now,
            app_last_ip=client_ip or None,
            route_mode=ROUTE_MODE_ALL_TRAFFIC,
            route_selected_apps_json="[]",
            route_requires_elevated_privileges=_default_route_requires_for_platform(
                str(getattr(payload, "platform", "") or "").strip()
            ),
        )
        mark_user_became_free(user, now=now)
        s.add(user)
        created = True
    else:
        user.is_app_user = True
        user.display_name = device_name
        user.app_device_name = device_name
        user.app_platform = str(getattr(payload, "platform", "") or "").strip()[:32] or user.app_platform
        user.app_os_version = str(getattr(payload, "os_version", "") or "").strip()[:64] or user.app_os_version
        user.app_version = str(getattr(payload, "app_version", "") or "").strip()[:32] or user.app_version
        user.app_locale = str(getattr(payload, "locale", "") or "").strip()[:32] or user.app_locale
        user.app_timezone = str(getattr(payload, "time_zone", "") or "").strip()[:64] or user.app_timezone
        user.app_last_seen_at = now
        user.app_last_ip = client_ip or user.app_last_ip
        if not user.sub_token:
            user.sub_token = _generate_sub_token()
        if not user.username:
            user.username = f"app_{str(user.tg_id)[-6:]}"
        if not user.current_plan_code:
            user.current_plan_code = "trial"
        if not user.sub_type:
            user.sub_type = "FREE"
        if not user.expiry_at:
            user.expiry_at = now + timedelta(days=canonical_trial_days)
        if user.is_active is None:
            user.is_active = True
        if not str(getattr(user, "route_mode", "") or "").strip():
            user.route_mode = ROUTE_MODE_ALL_TRAFFIC
        if getattr(user, "route_selected_apps_json", None) is None:
            user.route_selected_apps_json = "[]"
        if getattr(user, "route_requires_elevated_privileges", None) is None:
            user.route_requires_elevated_privileges = _default_route_requires_elevated_privileges(user)

    ensure_user_account_foundation(s, user, now=now)
    device = s.query(AccountDevice).filter(AccountDevice.install_id == install_id).one()
    reserve_trial(s, account_id=str(user.account_id), device_id=str(device.id), now=now)
    return user, created


def build_start_trial_response_parts(
    *,
    user: User,
    session_token: str,
    now: datetime,
    sync_ok: bool,
    build_access_policy: Callable[..., dict[str, Any]],
    trial_days: int,
    channel_bonus_days: int,
    client_policy: dict[str, Any] | None = None,
    trial_projection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    subscription_url = build_subscription_url(str(user.sub_token or ""))
    access_policy = build_access_policy(user=user, used_bytes=0, now=now)
    linked_telegram_id = int(getattr(user, "linked_telegram_id", 0) or 0) or None
    linked_telegram_username = str(getattr(user, "linked_telegram_username", "") or "").strip() or None
    effective_client_policy = client_policy or build_client_policy(
        user=user,
        install_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
    )
    managed_manifest = {
        "url": "/api/client/profile/managed",
        "transport_kind": str(effective_client_policy.get("transport_kind") or "").strip(),
        "engine_hint": str(effective_client_policy.get("engine_hint") or "").strip(),
        "profile_revision": str(effective_client_policy.get("profile_revision") or "").strip(),
    }
    return {
        "subscription_url": subscription_url,
        "session": {
            "token": session_token,
            "session_token": session_token,
            "account_id": str(int(user.tg_id)),
            "subscription_url": subscription_url,
            "auth_type": "app",
            "linked_telegram_id": linked_telegram_id,
            "linked_telegram_username": linked_telegram_username,
        },
        "client_policy": effective_client_policy,
        "access": {
            **access_policy,
            "sub_type": str(getattr(user, "sub_type", "") or ""),
            "current_plan_code": str(getattr(user, "current_plan_code", "") or ""),
            "is_active": bool(getattr(user, "is_active", False) and getattr(user, "expiry_at", None) and getattr(user, "expiry_at", None) > now),
            "expiry_at": getattr(user, "expiry_at", None).isoformat() if getattr(user, "expiry_at", None) else None,
            "subscription_url": subscription_url,
            "trial_days": TRIAL_DURATION_DAYS,
            "trial_state": str((trial_projection or {}).get("state") or "none"),
            "reserved_at": (trial_projection or {}).get("reserved_at"),
            "reservation_expires_at": (trial_projection or {}).get("reservation_expires_at"),
            "activated_at": (trial_projection or {}).get("activated_at"),
            "bonus_days": int(channel_bonus_days),
            "bonus_claimed": bool(getattr(user, "channel_bonus_claimed_at", None)),
        },
        "provisioning": {
            "status": "ready" if sync_ok else "pending_sync",
            "sync_ok": bool(sync_ok),
            "subscription_url": subscription_url,
            "managed_manifest": managed_manifest,
        },
    }

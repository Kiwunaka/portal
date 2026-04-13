from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable

from fastapi import HTTPException

from free_cycle_service import mark_user_became_free
from models import StartLink, User
from network_rollout import resolved_client_policy
from public_urls import build_subscription_url


def normalize_app_device_name(value: str | None, *, fallback: str = "Current device") -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    return text[:120]


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
    return resolved_client_policy(
        session=session,
        user=user,
        install_id=install_id,
        carrier=carrier,
        rollout_config=rollout_config,
    )


def create_app_telegram_start_code(session, *, account_tg_id: int, now: datetime) -> str:
    action = f"app_link:{int(account_tg_id)}"
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
        )
        mark_user_became_free(user, now=now)
        s.add(user)
        s.flush()
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
        s.flush()

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
) -> dict[str, Any]:
    subscription_url = build_subscription_url(str(user.sub_token or ""))
    access_policy = build_access_policy(user=user, used_bytes=0, now=now)
    linked_telegram_id = int(getattr(user, "linked_telegram_id", 0) or 0) or None
    linked_telegram_username = str(getattr(user, "linked_telegram_username", "") or "").strip() or None
    effective_client_policy = client_policy or build_client_policy(
        user=user,
        install_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
    )
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
            "trial_days": int(trial_days),
            "bonus_days": int(channel_bonus_days),
            "bonus_claimed": bool(getattr(user, "channel_bonus_claimed_at", None)),
        },
        "provisioning": {
            "status": "ready" if sync_ok else "pending_sync",
            "sync_ok": bool(sync_ok),
            "subscription_url": subscription_url,
        },
    }

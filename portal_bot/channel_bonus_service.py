from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Awaitable, Callable

import aiohttp
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

import db
from config import Settings
from control_panel import ControlPanel
from node_policy import node_is_free
from economy_service import CHANNEL_GRANT_DAYS, GRANDFATHERED_CHANNEL_GRANT_DAYS, grant_channel_bonus
from events_service import track_event
from models import CampaignSend, EntitlementGrant, User
from points_service import award_points


def _utcnow() -> datetime:
    from datetime import timezone

    return datetime.now(timezone.utc).replace(tzinfo=None)


def _safe_iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _current_bot_token() -> str:
    return str(os.getenv("BOT_TOKEN") or Settings.BOT_TOKEN or "").strip()


async def _telegram_get_chat_member(chat_id: str, user_id: int) -> dict[str, Any] | None:
    token = _current_bot_token()
    if not token:
        return None
    endpoint = f"https://api.telegram.org/bot{token}/getChatMember"
    payload = {"chat_id": chat_id, "user_id": int(user_id)}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                body = await resp.json(content_type=None)
                if resp.status != 200:
                    return None
                return body if isinstance(body, dict) else None
    except Exception:
        return None


async def _is_channel_member(channel_username: str, tg_id: int) -> tuple[bool, str]:
    username = (channel_username or "").lstrip("@").strip()
    if not username:
        return False, "channel_not_configured"
    body = await _telegram_get_chat_member(f"@{username}", int(tg_id))
    if not body:
        return False, "telegram_api_unavailable"
    if not body.get("ok"):
        desc = str(body.get("description") or "").lower()
        if "user not found" in desc or "participant" in desc or "not a member" in desc:
            return False, "not_member"
        if "chat not found" in desc:
            return False, "channel_not_found"
        if "bot is not a member" in desc:
            return False, "bot_not_in_channel"
        return False, "telegram_api_error"
    status = str((body.get("result") or {}).get("status") or "").lower()
    if status in {"left", "kicked", "not_member"}:
        return False, "not_member"
    return status in {"creator", "administrator", "member", "restricted"}, status or "unknown"


def _membership_check_tg_id(user: User | None) -> int:
    if not user:
        return 0
    if bool(getattr(user, "is_app_user", False)):
        return int(getattr(user, "linked_telegram_id", 0) or 0)
    return int(getattr(user, "tg_id", 0) or 0)


def _has_campaign_mark(session, *, tg_id: int, campaign_key: str) -> bool:
    return bool(
        session.query(CampaignSend.id)
        .filter(CampaignSend.tg_id == int(tg_id))
        .filter(func.lower(CampaignSend.campaign_key) == str(campaign_key or "").strip().lower())
        .first()
    )


def _mark_campaign_once(session, *, tg_id: int, campaign_key: str) -> bool:
    try:
        with session.begin_nested():
            session.add(CampaignSend(tg_id=int(tg_id), campaign_key=str(campaign_key), sent_at=_utcnow()))
            session.flush()
        return True
    except Exception:
        return False


def _track_bonus_event(*, tg_id: int, event_name: str, meta: dict[str, Any] | None = None) -> None:
    track_event(
        tg_id=int(tg_id),
        event_name=str(event_name or "").strip()[:64],
        source="webapp",
        meta=meta or None,
    )


async def _sync_user_after_paid_bonus(user: User) -> bool:
    try:
        panel = ControlPanel()
        try:
            await panel.login()
            ok = await panel.enable_client(user.uuid, True)
            nodes = await panel.refresh()
            free_codes = [
                (getattr(n, "code", "") or "").strip()
                for n in nodes
                if node_is_free(n)
            ]
            if free_codes:
                await panel.set_existing_user_enabled_on_nodes(
                    tg_id=int(user.tg_id),
                    node_codes=free_codes,
                    enable=False,
                )
            return bool(ok)
        finally:
            await panel.close()
    except Exception:
        return False


async def build_channel_subscriber_check_response(
    *,
    user: User,
    channel_username: str,
    bonus_days: int,
    is_channel_member: Callable[[str, int], Awaitable[tuple[bool, str]]] = _is_channel_member,
) -> dict[str, Any]:
    membership_tg_id = _membership_check_tg_id(user)
    already_claimed = bool(getattr(user, "channel_bonus_claimed_at", None))

    if membership_tg_id <= 0:
        return {
            "ok": True,
            "subscriber": False,
            "reason": "telegram_link_required",
            "points_granted": 0,
            "campaign_marked": False,
            "link_required": True,
            "claim_required": False,
            "already_claimed": bool(already_claimed),
            "bonus_days": CHANNEL_GRANT_DAYS,
        }

    is_member, reason = await is_channel_member(channel_username, membership_tg_id)
    if not is_member:
        return {
            "ok": True,
            "subscriber": False,
            "reason": reason,
            "points_granted": 0,
            "campaign_marked": False,
            "link_required": False,
            "claim_required": False,
            "already_claimed": bool(already_claimed),
            "bonus_days": CHANNEL_GRANT_DAYS,
        }

    return {
        "ok": True,
        "subscriber": True,
        "reason": "member",
        "points_granted": 0,
        "campaign_marked": False,
        "link_required": False,
        "claim_required": not already_claimed,
        "already_claimed": bool(already_claimed),
        "bonus_days": CHANNEL_GRANT_DAYS,
    }


def _channel_grant_for_account(session, *, account_id: str) -> EntitlementGrant | None:
    if not str(account_id or "").strip():
        return None
    return (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == str(account_id),
            EntitlementGrant.source.in_(["telegram_channel", "telegram_channel_grandfathered"]),
        )
        .order_by(EntitlementGrant.created_at.asc())
        .first()
    )


async def claim_channel_bonus(
    *,
    s,
    user: User,
    tg_id: int,
    public_channel: str,
    bonus_days: int,
    opening_bonus_campaign_key: str,
    subscriber_campaign_key: str,
    points_expiry_days: int,
    is_channel_member: Callable[[str, int], Awaitable[tuple[bool, str]]] | None = None,
    sync_user_after_paid_bonus: Callable[[User], Awaitable[bool]] | None = None,
) -> dict[str, Any]:
    channel_username = (public_channel or "").lstrip("@").strip()
    is_channel_member = is_channel_member or _is_channel_member
    sync_user_after_paid_bonus = sync_user_after_paid_bonus or _sync_user_after_paid_bonus
    if not channel_username:
        _track_bonus_event(tg_id=tg_id, event_name="promo_channel_denied", meta={"reason": "channel_not_configured"})
        raise HTTPException(status_code=400, detail="Public channel is not configured")

    if not bool(getattr(user, "tos_accepted", False)):
        _track_bonus_event(tg_id=tg_id, event_name="promo_channel_denied", meta={"reason": "tos_required"})
        raise HTTPException(status_code=400, detail="Сначала примите оферту в боте (/start)")
    if (user.sub_type or "").upper() == "MANUAL":
        _track_bonus_event(tg_id=tg_id, event_name="promo_channel_denied", meta={"reason": "manual_account"})
        raise HTTPException(status_code=400, detail="Bonus is disabled for manual accounts")
    account_id = str(user.account_id or "").strip()
    existing_grant = _channel_grant_for_account(s, account_id=account_id)
    if existing_grant is not None:
        days = int(existing_grant.duration_days or CHANNEL_GRANT_DAYS)
        _track_bonus_event(
            tg_id=tg_id,
            event_name="promo_channel_already_claimed",
            meta={"days": days, "claimed_at": _safe_iso(existing_grant.activated_at)},
        )
        return {
            "ok": True,
            "already_claimed": True,
            "premium_days": days,
            "claimed_at": _safe_iso(existing_grant.activated_at or user.channel_bonus_claimed_at),
            "expiry_at": _safe_iso(user.expiry_at),
            "sub_type": user.sub_type,
            "channel": channel_username,
        }
    if _has_campaign_mark(s, tg_id=tg_id, campaign_key=opening_bonus_campaign_key):
        _track_bonus_event(
            tg_id=tg_id,
            event_name="promo_channel_denied",
            meta={"reason": "opening_bonus_conflict", "campaign_key": opening_bonus_campaign_key},
        )
        raise HTTPException(
            status_code=400,
            detail="Для этого аккаунта уже активирован промо-бонус по ссылке. Бонус за канал недоступен.",
        )
    if getattr(user, "channel_bonus_claimed_at", None):
        _track_bonus_event(
            tg_id=tg_id,
            event_name="promo_channel_already_claimed",
            meta={"days": GRANDFATHERED_CHANNEL_GRANT_DAYS, "claimed_at": _safe_iso(user.channel_bonus_claimed_at)},
        )
        return {
            "ok": True,
            "already_claimed": True,
            "premium_days": GRANDFATHERED_CHANNEL_GRANT_DAYS,
            "claimed_at": _safe_iso(user.channel_bonus_claimed_at),
            "expiry_at": _safe_iso(user.expiry_at),
            "sub_type": user.sub_type,
            "channel": channel_username,
        }
    membership_tg_id = _membership_check_tg_id(user)
    if membership_tg_id <= 0:
        _track_bonus_event(
            tg_id=tg_id,
            event_name="promo_channel_denied",
            meta={"reason": "telegram_link_required"},
        )
        raise HTTPException(status_code=400, detail="Сначала привяжите Telegram к аккаунту POKROV")

    is_member, reason = await is_channel_member(channel_username, membership_tg_id)
    if not is_member:
        normalized_reason = str(reason or "").strip().lower()
        if normalized_reason in {"left", "kicked", "not_member"}:
            normalized_reason = "not_member"
        if normalized_reason == "not_member":
            _track_bonus_event(tg_id=tg_id, event_name="promo_channel_denied", meta={"reason": "not_member"})
            raise HTTPException(status_code=400, detail="Сначала подпишитесь на канал и повторите проверку")
        _track_bonus_event(
            tg_id=tg_id,
            event_name="promo_channel_denied",
            meta={"reason": "membership_check_failed", "raw_reason": str(reason or "")[:120]},
        )
        raise HTTPException(status_code=502, detail=f"Не удалось проверить подписку: {reason}")

    now = _utcnow()
    if not account_id:
        from account_foundation_service import ensure_user_account_foundation

        ensure_user_account_foundation(s, user, now=now)
        s.flush()
        account_id = str(user.account_id or "").strip()
    days = CHANNEL_GRANT_DAYS
    points_granted = 0
    sync_ok = False
    try:
        with s.begin_nested():
            grant_channel_bonus(
                s,
                account_id=account_id,
                legacy_tg_id=int(tg_id),
                telegram_id=membership_tg_id,
                now=now,
            )
    except IntegrityError:
        canonical = _channel_grant_for_account(s, account_id=account_id)
        if canonical is None:
            raise
        return {
            "ok": True,
            "already_claimed": True,
            "premium_days": int(canonical.duration_days or CHANNEL_GRANT_DAYS),
            "claimed_at": _safe_iso(canonical.activated_at),
            "expiry_at": _safe_iso(canonical.expires_at),
            "sub_type": user.sub_type,
            "channel": channel_username,
        }
    first_channel_mark = _mark_campaign_once(
        s,
        tg_id=tg_id,
        campaign_key=subscriber_campaign_key,
    )
    if first_channel_mark:
        points_granted = award_points(
            tg_id=tg_id,
            amount=100,
            reason="channel_subscribe_bonus",
            expires_days=points_expiry_days,
        )
    s.commit()
    s.refresh(user)
    try:
        sync_ok = bool(await sync_user_after_paid_bonus(user))
    except Exception as exc:
        import logging

        logging.getLogger(__name__).warning("channel bonus sync failed tg_id=%s err=%s", tg_id, exc)
        sync_ok = False

    _track_bonus_event(
        tg_id=tg_id,
        event_name="promo_channel_activated",
        meta={
            "days": int(days),
            "channel": f"@{channel_username}",
            "sync_ok": bool(sync_ok),
            "points_granted": int(points_granted),
        },
    )

    return {
        "ok": True,
        "already_claimed": False,
        "premium_days": days,
        "claimed_at": _safe_iso(user.channel_bonus_claimed_at),
        "expiry_at": _safe_iso(user.expiry_at),
        "sub_type": user.sub_type,
        "channel": channel_username,
        "sync_ok": bool(sync_ok),
        "points_granted": int(points_granted),
        "linked_telegram_id": int(getattr(user, "linked_telegram_id", 0) or 0) or None,
        "linked_telegram_username": str(getattr(user, "linked_telegram_username", "") or "").strip() or None,
    }

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from datetime import datetime, timedelta

import aiohttp
from dotenv import load_dotenv
from sqlalchemy import and_, func, or_

# Load env from repo-local file first to avoid cwd-dependent startup behavior.
load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
load_dotenv()

from config import Settings
from control_panel import ControlPanel
from db import SessionLocal, init_db
from events_service import track_event
from models import CampaignSend, NodeHealthSample, User
from offers_service import create_offer, expire_stale_offers, get_active_offer
from pay_attempts_service import find_abandoned_candidates, mark_abandoned, mark_abandoned_notified


BOT_USERNAME = (os.getenv("BOT_USERNAME") or "portal_service_bot").lstrip("@")
SUPPORT_USERNAME = (os.getenv("SUPPORT_BOT_USERNAME") or os.getenv("SUPPORT_USERNAME") or "portal_privacy_helpbot").lstrip("@")
FREE_TOTAL_GB = int(os.getenv("FREE_TOTAL_GB", "40"))
PUBLIC_CHANNEL = (os.getenv("PUBLIC_CHANNEL") or "portal_privacy").lstrip("@")
AUTO_FREE_DAYS = int(os.getenv("AUTO_FREE_DAYS", "3650"))


def _bot_pay_url() -> str:
    return f"https://t.me/{BOT_USERNAME}?start=pay"


def _support_url() -> str:
    return f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new"


async def _telegram_send_message(
    *,
    chat_id: int,
    text: str,
    buttons: list[list[dict[str, str]]] | None = None,
) -> bool:
    token = (Settings.BOT_TOKEN or "").strip()
    if not token:
        return False
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    payload: dict[str, object] = {
        "chat_id": int(chat_id),
        "text": text,
        "disable_web_page_preview": True,
    }
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return False
                body = await resp.json(content_type=None)
                return bool((body or {}).get("ok"))
    except Exception:
        return False


async def _telegram_get_chat_member(channel_username: str, user_id: int) -> tuple[bool, str]:
    token = (Settings.BOT_TOKEN or "").strip()
    if not token:
        return False, "bot_token_empty"
    endpoint = f"https://api.telegram.org/bot{token}/getChatMember"
    payload = {"chat_id": f"@{channel_username.lstrip('@')}", "user_id": int(user_id)}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                body = await resp.json(content_type=None)
                if resp.status != 200:
                    return False, "telegram_http_error"
                if not isinstance(body, dict) or not body.get("ok"):
                    desc = str((body or {}).get("description") or "").lower()
                    if "not a member" in desc or "user not found" in desc:
                        return False, "not_member"
                    return False, "telegram_api_error"
                status = str((body.get("result") or {}).get("status") or "").lower()
                return status in {"creator", "administrator", "member", "restricted"}, status
    except Exception:
        return False, "telegram_exception"


async def _switch_user_to_free(*, tg_id: int) -> bool:
    now = datetime.utcnow()
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            return False
        user.sub_type = "FREE"
        user.is_active = True
        user.expiry_at = now + timedelta(days=max(30, int(AUTO_FREE_DAYS)))
        user.channel_bonus_active = False
        user.channel_bonus_revoked_at = now
        s.commit()
        user_uuid = str(user.uuid or "")
        user_email = str(user.email or f"User_{int(tg_id)}")
        user_sub_id = str(user.sub_token or user.tg_id)
    except Exception:
        s.rollback()
        return False
    finally:
        s.close()

    try:
        panel = ControlPanel()
        try:
            await panel.login()
            nodes = await panel.refresh()
            free_codes = [(getattr(n, "code", "") or "").strip() for n in nodes if "free" in (getattr(n, "code", "") or "").lower()]
            paid_codes = [(getattr(n, "code", "") or "").strip() for n in nodes if "free" not in (getattr(n, "code", "") or "").lower()]
            if free_codes:
                await panel.ensure_user_on_all_nodes(
                    tg_id=int(tg_id),
                    client_uuid=user_uuid,
                    email=user_email,
                    sub_id=user_sub_id,
                    enable=True,
                    only_node_codes=free_codes,
                )
            if paid_codes:
                await panel.set_existing_user_enabled_on_nodes(tg_id=int(tg_id), node_codes=paid_codes, enable=False)
        finally:
            await panel.close()
    except Exception:
        return False
    return True


def _mark_campaign_sent_once(*, tg_id: int, campaign_key: str) -> bool:
    s = SessionLocal()
    try:
        exists = (
            s.query(CampaignSend.id)
            .filter(CampaignSend.tg_id == int(tg_id), CampaignSend.campaign_key == str(campaign_key))
            .first()
        )
        if exists:
            return False
        row = CampaignSend(tg_id=int(tg_id), campaign_key=str(campaign_key), sent_at=datetime.utcnow())
        s.add(row)
        s.commit()
        return True
    except Exception:
        s.rollback()
        return False
    finally:
        s.close()


def _sent_recently(*, tg_id: int, campaign_prefix: str, within_days: int) -> bool:
    s = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=max(1, int(within_days)))
        row = (
            s.query(CampaignSend.id)
            .filter(CampaignSend.tg_id == int(tg_id))
            .filter(CampaignSend.campaign_key.like(f"{campaign_prefix}%"))
            .filter(CampaignSend.sent_at >= cutoff)
            .first()
        )
        return bool(row)
    finally:
        s.close()


async def abandoned_cart_job() -> None:
    while True:
        rows = find_abandoned_candidates(older_than_minutes=60, limit=200)
        for row in rows:
            text = "⏳ Слот оплаты всё ещё зарезервирован.\n\nНужна помощь с оплатой или подключением?"
            buttons = [
                [{"text": "🟦 Оплатить / Продлить", "url": _bot_pay_url()}],
                [{"text": "🆘 Помощь с оплатой", "url": _support_url()}],
            ]
            ok = await _telegram_send_message(chat_id=int(row.tg_id), text=text, buttons=buttons)
            if ok:
                mark_abandoned_notified(attempt_id=int(row.id))
                mark_abandoned(attempt_id=int(row.id))
                track_event(
                    tg_id=int(row.tg_id),
                    event_name="expired",
                    source="worker",
                    meta={"flow": "abandoned_cart", "attempt_id": int(row.id)},
                )
        await asyncio.sleep(300)


async def expiry_chain_job() -> None:
    while True:
        now = datetime.utcnow()
        s = SessionLocal()
        try:
            users = (
                s.query(User)
                .filter(User.tg_id > 0)
                .filter(func.upper(User.sub_type) != "MANUAL")
                .filter(User.expiry_at.isnot(None))
                .all()
            )
        finally:
            s.close()

        for u in users:
            expiry = u.expiry_at
            if not expiry:
                continue
            delta = expiry - now
            campaign_key = ""
            if timedelta(days=2) < delta <= timedelta(days=3):
                campaign_key = f"expiry_t3:{expiry.date().isoformat()}"
            elif timedelta(hours=23) < delta <= timedelta(hours=24):
                campaign_key = f"expiry_t24:{expiry.date().isoformat()}"
            elif timedelta(hours=-1) <= delta <= timedelta(hours=1):
                campaign_key = f"expiry_t0:{expiry.date().isoformat()}"
            if not campaign_key:
                continue
            if not _mark_campaign_sent_once(tg_id=int(u.tg_id), campaign_key=campaign_key):
                continue
            text = "⌛ Чтобы защита не прерывалась, продлите доступ."
            buttons = [[{"text": "🟦 Продлить", "url": _bot_pay_url()}]]
            await _telegram_send_message(chat_id=int(u.tg_id), text=text, buttons=buttons)
            track_event(
                tg_id=int(u.tg_id),
                event_name="expired",
                source="worker",
                meta={"flow": "expiry_chain", "campaign_key": campaign_key},
            )
        await asyncio.sleep(3600)


async def _legacy_usage_bytes(*, tg_id: int) -> int:
    if not Settings.PANEL_PATH:
        return 0
    try:
        base = Settings.PANEL_BASE_URL.rstrip("/")
        path = Settings.PANEL_PATH.strip("/")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base}/{path}/login",
                data={"username": Settings.PANEL_USER, "password": Settings.PANEL_PASS},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as login_resp:
                if login_resp.status != 200:
                    return 0
                cookies = login_resp.cookies
            async with session.get(
                f"{base}/{path}/panel/api/inbounds/list",
                cookies=cookies,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as list_resp:
                if list_resp.status != 200:
                    return 0
                data = await list_resp.json()
                if not data.get("success"):
                    return 0
                for inb in data.get("obj", []):
                    if int(inb.get("id") or 0) != int(Settings.INBOUND_ID):
                        continue
                    clients = (inb.get("clientStats") or [])
                    for c in clients:
                        if str(c.get("tgId", "")).strip() == str(int(tg_id)):
                            return int(c.get("up", 0) or 0) + int(c.get("down", 0) or 0)
    except Exception:
        return 0
    return 0


async def oto_free_job() -> None:
    while True:
        expire_stale_offers()
        now = datetime.utcnow()
        s = SessionLocal()
        try:
            users = (
                s.query(User)
                .filter(User.tg_id > 0)
                .filter(func.upper(User.sub_type) == "FREE")
                .filter(User.is_active == True)
                .all()
            )
        finally:
            s.close()

        for u in users:
            if get_active_offer(tg_id=int(u.tg_id), offer_type="trial_oto"):
                continue

            near_expiry = bool(u.expiry_at and (u.expiry_at - now) <= timedelta(hours=24))
            low_gb = False
            used_bytes = await _legacy_usage_bytes(tg_id=int(u.tg_id))
            if used_bytes > 0:
                used_gb = used_bytes / float(1024**3)
                remaining_gb = max(0.0, float(FREE_TOTAL_GB) - used_gb)
                low_gb = remaining_gb <= float(FREE_TOTAL_GB) * 0.2

            if not (near_expiry or low_gb):
                continue

            trigger_reason = "low_gb" if low_gb else "near_expiry"
            offer = create_offer(
                tg_id=int(u.tg_id),
                offer_type="trial_oto",
                plan_code="1_month",
                price_stars=149,
                trigger_reason=trigger_reason,
                expires_at=now + timedelta(hours=2),
            )
            if not offer:
                continue

            text = "🎁 Мягкий апгрейд на 2 часа: 1 месяц за 149⭐.\nОффер закреплён за вами."
            buttons = [[{"text": "🟦 Подключить / Продлить", "url": _bot_pay_url()}]]
            await _telegram_send_message(chat_id=int(u.tg_id), text=text, buttons=buttons)
        await asyncio.sleep(900)


async def reactivation_job() -> None:
    while True:
        now = datetime.utcnow()
        campaign_base = f"reactivation_new_node:{now.strftime('%Y%m%d')}"
        s = SessionLocal()
        try:
            rows = (
                s.query(User)
                .filter(User.tg_id > 0)
                .filter(
                    or_(
                        User.expiry_at.is_(None),
                        User.expiry_at <= now,
                        and_(func.upper(User.sub_type) == "FREE", User.is_active == False),
                    )
                )
                .all()
            )
        finally:
            s.close()

        for u in rows:
            if _sent_recently(tg_id=int(u.tg_id), campaign_prefix="reactivation_new_node:", within_days=30):
                continue
            if not _mark_campaign_sent_once(tg_id=int(u.tg_id), campaign_key=campaign_base):
                continue
            text = "🌍 Доступен 24-часовой тест полного режима. Проверьте качество подключения."
            buttons = [[{"text": "🟦 Проверить и подключить", "url": _bot_pay_url()}]]
            await _telegram_send_message(chat_id=int(u.tg_id), text=text, buttons=buttons)
        await asyncio.sleep(3600)


async def node_metrics_watchdog_job() -> None:
    started_at = datetime.utcnow()
    stale_cycles = 0
    while True:
        stale_after = max(300, int(os.getenv("NODE_METRICS_STALE_AFTER_SECONDS", "900")))
        s = SessionLocal()
        try:
            last_sample = s.query(func.max(NodeHealthSample.sampled_at)).scalar()
        finally:
            s.close()

        now = datetime.utcnow()
        # Suppress false positives right after worker start while collector is warming up.
        if not last_sample and (now - started_at).total_seconds() < stale_after:
            await asyncio.sleep(3600)
            continue
        stale = bool((not last_sample) or ((now - last_sample).total_seconds() > stale_after))
        stale_cycles = stale_cycles + 1 if stale else 0
        # Alert only after two consecutive stale checks and no more than once per day.
        if stale and stale_cycles >= 2 and int(Settings.ADMIN_ID or 0) > 0:
            key = f"metrics_stale:{now.strftime('%Y%m%d')}"
            if _mark_campaign_sent_once(tg_id=int(Settings.ADMIN_ID), campaign_key=key):
                text = "⚠️ Метрики нод устарели: проверьте `portal-node-metrics.timer`."
                await _telegram_send_message(chat_id=int(Settings.ADMIN_ID), text=text)
        await asyncio.sleep(3600)


async def channel_bonus_guard_job() -> None:
    last_verify_error_alert_at: datetime | None = None
    while True:
        channel = (PUBLIC_CHANNEL or "").lstrip("@").strip()
        if not channel:
            await asyncio.sleep(900)
            continue

        now = datetime.utcnow()
        s = SessionLocal()
        try:
            rows = (
                s.query(User)
                .filter(User.tg_id > 0)
                .filter(User.channel_bonus_active == True)
                .filter(or_(User.channel_bonus_expires_at.is_(None), User.channel_bonus_expires_at > now))
                .all()
            )
        finally:
            s.close()

        for u in rows:
            is_member, reason = await _telegram_get_chat_member(channel, int(u.tg_id))
            if is_member:
                continue
            if reason != "not_member":
                # Do not revoke on transient Telegram/API errors to avoid accidental mass downgrades.
                now_alert = datetime.utcnow()
                if (
                    int(Settings.ADMIN_ID or 0) > 0
                    and (last_verify_error_alert_at is None or (now_alert - last_verify_error_alert_at).total_seconds() >= 3600)
                ):
                    await _telegram_send_message(
                        chat_id=int(Settings.ADMIN_ID),
                        text=(
                            "⚠️ Проверка подписки на канал работает нестабильно.\n"
                            f"Причина: `{reason}`.\n"
                            "Откат бонусов временно пропущен."
                        ),
                    )
                    last_verify_error_alert_at = now_alert
                continue
            switched = await _switch_user_to_free(tg_id=int(u.tg_id))
            if switched:
                await _telegram_send_message(
                    chat_id=int(u.tg_id),
                    text=(
                        "ℹ️ Бонусный доступ отключён: подписка на канал не подтверждена.\n\n"
                        "Подпишитесь на канал, чтобы участвовать в бонусах."
                    ),
                )
                track_event(
                    tg_id=int(u.tg_id),
                    event_name="expired",
                    source="worker",
                    meta={"flow": "channel_bonus_guard", "reason": reason},
                )
        await asyncio.sleep(900)


async def main() -> None:
    init_db()
    tasks = [
        asyncio.create_task(abandoned_cart_job()),
        asyncio.create_task(expiry_chain_job()),
        asyncio.create_task(oto_free_job()),
        asyncio.create_task(reactivation_job()),
        asyncio.create_task(node_metrics_watchdog_job()),
        asyncio.create_task(channel_bonus_guard_job()),
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())


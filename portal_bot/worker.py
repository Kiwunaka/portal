from __future__ import annotations

import asyncio
import hashlib
import logging
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

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
from free_cycle_service import mark_user_became_free, process_due_free_cycle_resets
from models import CampaignSend, ExternalOrder, NodeHealthSample, Template, User
from offers_service import create_offer, expire_stale_offers, get_active_offer
from pay_attempts_service import find_abandoned_candidates, mark_abandoned, mark_abandoned_notified

logger = logging.getLogger(__name__)


BOT_USERNAME = (os.getenv("BOT_USERNAME") or "net4ebur_bot").lstrip("@")
SUPPORT_USERNAME = (os.getenv("SUPPORT_BOT_USERNAME") or os.getenv("SUPPORT_USERNAME") or "portal_privacy_helpbot").lstrip("@")
FREE_TOTAL_GB = int(os.getenv("FREE_TOTAL_GB", "30"))
PUBLIC_CHANNEL = (os.getenv("PUBLIC_CHANNEL") or "portal_privacy").lstrip("@")
AUTO_FREE_DAYS = int(os.getenv("AUTO_FREE_DAYS", "3650"))
START99_WELCOME_ENABLED = os.getenv("START99_WELCOME_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on", "y"}
START99_WELCOME_MIN_HOURS = max(1, int(os.getenv("START99_WELCOME_MIN_HOURS", "24")))
START99_WELCOME_MAX_HOURS = max(START99_WELCOME_MIN_HOURS + 1, int(os.getenv("START99_WELCOME_MAX_HOURS", "48")))
START99_WELCOME_DISCOUNT_PCT = max(1, min(95, int(os.getenv("START99_WELCOME_DISCOUNT_PCT", "15"))))
START99_WELCOME_DISCOUNT_CODE = (os.getenv("START99_WELCOME_DISCOUNT_CODE") or "STARTBOOST").strip().upper()[:20]

_TEMPLATE_CACHE_TTL_SECONDS = max(30, int(os.getenv("RETENTION_TEMPLATE_CACHE_TTL_SECONDS", "180")))
_TEMPLATE_CACHE: dict[str, tuple[datetime, str]] = {}

RETENTION_DEFAULT_COPY: dict[str, dict[str, str]] = {
    "welcome": {
        "a": (
            "✨ Добро пожаловать в Portal.\n\n"
            "Запуск займёт 1-2 минуты:\n"
            "1) Откройте раздел Подключение.\n"
            "2) Импортируйте ключ в клиент.\n"
            "3) Проверьте статус узлов.\n\n"
            "Если что-то не получилось, поддержка доступна в один клик."
        ),
        "b": (
            "🛡 Профиль готов к работе.\n\n"
            "Короткий чек-лист перед первым запуском:\n"
            "• Выберите приложение для своей платформы.\n"
            "• Импортируйте ключ одним нажатием.\n"
            "• Сверьте статус узлов в кабинете.\n\n"
            "Нужна помощь с настройкой? Мы на связи в поддержке."
        ),
    },
    "t3": {
        "a": (
            "⌛ До окончания доступа осталось около 3 дней.\n\n"
            "Продлите заранее, чтобы сохранить текущий режим без паузы."
        ),
        "b": (
            "📅 Напоминание: доступ скоро закончится (T-3).\n\n"
            "Продление заранее помогает избежать перерыва в подключении."
        ),
    },
    "t1": {
        "a": (
            "⏱ До завершения подписки примерно 1 день.\n\n"
            "Продлите сейчас, чтобы избежать паузы в доступе."
        ),
        "b": (
            "⚡ T-1: срок доступа заканчивается в ближайшие сутки.\n\n"
            "Продление сейчас сохранит привычный режим без перерыва."
        ),
    },
    "t0": {
        "a": (
            "🚨 Срок подписки подходит к финалу (T0).\n\n"
            "Если доступ нужен без пауз, продлите прямо сейчас."
        ),
        "b": (
            "🔔 Подписка почти завершена.\n\n"
            "Пара минут на продление — и режим останется активным."
        ),
    },
    "reactivation": {
        "a": (
            "🌍 Профиль и история сохранены.\n\n"
            "Вернитесь в один клик и продолжайте без повторной настройки."
        ),
        "b": (
            "🧭 Доступ завершился, но подключение можно восстановить за минуту.\n\n"
            "Откройте оплату и вернитесь в рабочий режим."
        ),
    },
    "start99_offer": {
        "a": (
            "🎁 Вы уже проверили Start в реальном трафике.\n\n"
            "Мы закрепили персональную скидку {discount_pct}% на следующий платёж."
        ),
        "b": (
            "⚡ Start активирован, можно переходить на полный режим.\n\n"
            "Скидка {discount_pct}% уже ждёт в следующем checkout."
        ),
    },
}

RETENTION_BUTTONS: dict[str, dict[str, str]] = {
    "welcome": {"a": "🟦 Открыть кабинет", "b": "🟦 Перейти к подключению"},
    "t3": {"a": "🟦 Продлить заранее", "b": "🟦 Сохранить доступ"},
    "t1": {"a": "🟦 Продлить сейчас", "b": "🟦 Избежать паузы"},
    "t0": {"a": "🟦 Открыть оплату", "b": "🟦 Оставить доступ активным"},
    "reactivation": {"a": "🟦 Вернуться в Portal", "b": "🟦 Проверить подключение"},
    "start99_offer": {"a": "🟦 Продлить со скидкой", "b": "🟦 Зафиксировать доступ"},
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _bot_pay_url() -> str:
    return f"https://t.me/{BOT_USERNAME}?start=pay"


def _support_url() -> str:
    return f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new"


def _ab_variant_for_user(*, tg_id: int, flow_key: str) -> str:
    seed = f"{flow_key}:{int(tg_id)}".encode("utf-8")
    digest = hashlib.sha256(seed).digest()
    return "b" if (digest[0] % 2) else "a"


def _expiry_stage(delta: timedelta) -> str:
    if timedelta(days=2) < delta <= timedelta(days=3):
        return "t3"
    if timedelta(hours=20) < delta <= timedelta(hours=28):
        return "t1"
    if timedelta(hours=-1) <= delta <= timedelta(hours=1):
        return "t0"
    return ""


def _retention_template_key(*, flow: str, variant: str) -> str:
    return f"retention_{str(flow).strip().lower()}_{str(variant).strip().lower()}"


def _load_admin_template_value(*, key: str) -> str | None:
    now = _utcnow()
    cache_key = str(key or "").strip().lower()
    if not cache_key:
        return None
    cached = _TEMPLATE_CACHE.get(cache_key)
    if cached:
        cached_at, cached_value = cached
        if (now - cached_at).total_seconds() <= _TEMPLATE_CACHE_TTL_SECONDS:
            return cached_value
    s = SessionLocal()
    try:
        row = s.query(Template).filter(func.lower(Template.key) == cache_key).first()
        if not row:
            return None
        value = str(row.text or "").strip()
        if not value:
            return None
        _TEMPLATE_CACHE[cache_key] = (now, value)
        return value
    finally:
        s.close()


def _retention_text(*, flow: str, variant: str, context: dict[str, str] | None = None) -> str:
    flow_key = str(flow).strip().lower()
    variant_key = str(variant).strip().lower()
    fallback = (
        RETENTION_DEFAULT_COPY.get(flow_key, {}).get(variant_key)
        or RETENTION_DEFAULT_COPY.get(flow_key, {}).get("a")
        or "Обновление статуса доступа."
    )
    template_key = _retention_template_key(flow=flow_key, variant=variant_key)
    value = _load_admin_template_value(key=template_key) or fallback
    if context:
        try:
            return value.format(**context)
        except Exception:
            return value
    return value


def _retention_buttons(*, flow: str, variant: str) -> list[list[dict[str, str]]]:
    flow_key = str(flow).strip().lower()
    variant_key = str(variant).strip().lower()
    label = (
        RETENTION_BUTTONS.get(flow_key, {}).get(variant_key)
        or RETENTION_BUTTONS.get(flow_key, {}).get("a")
        or "🟦 Продолжить"
    )
    rows = [[{"text": label, "url": _bot_pay_url()}]]
    if flow_key in {"welcome", "reactivation", "start99_offer"} and PUBLIC_CHANNEL:
        rows.append([{"text": "📣 Канал с обновлениями", "url": f"https://t.me/{PUBLIC_CHANNEL}"}])
    return rows


def _ensure_pending_discount(*, tg_id: int, pct: int, code: str) -> tuple[int, bool]:
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            return 0, False
        current = int(getattr(user, "pending_discount_pct", 0) or 0)
        target = max(1, min(95, int(pct)))
        if current >= target and current > 0:
            return current, False
        user.pending_discount_pct = int(target)
        user.pending_discount_code = str(code or START99_WELCOME_DISCOUNT_CODE).strip().upper()[:20]
        user.pending_discount_set_at = _utcnow()
        s.commit()
        return int(target), True
    except Exception:
        s.rollback()
        return 0, False
    finally:
        s.close()


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


def _normalize_channel_membership_reason(reason: str) -> str:
    raw = str(reason or "").strip().lower()
    if raw in {"not_member", "left", "kicked"}:
        return "not_member"
    return raw or "unknown"


async def _switch_user_to_free(*, tg_id: int) -> bool:
    now = _utcnow()
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
        mark_user_became_free(user, now=now)
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
        row = CampaignSend(tg_id=int(tg_id), campaign_key=str(campaign_key), sent_at=_utcnow())
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
        cutoff = _utcnow() - timedelta(days=max(1, int(within_days)))
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


async def welcome_chain_job() -> None:
    while True:
        now = _utcnow()
        s = SessionLocal()
        try:
            users = (
                s.query(User)
                .filter(User.tg_id > 0)
                .filter(func.upper(User.sub_type) != "MANUAL")
                .filter(User.created_at.isnot(None))
                .filter(User.created_at >= now - timedelta(hours=36))
                .filter(User.created_at <= now - timedelta(minutes=10))
                .all()
            )
        finally:
            s.close()

        for u in users:
            campaign_key = "welcome_chain_v1"
            if not _mark_campaign_sent_once(tg_id=int(u.tg_id), campaign_key=campaign_key):
                continue
            variant = _ab_variant_for_user(tg_id=int(u.tg_id), flow_key="welcome")
            text = _retention_text(
                flow="welcome",
                variant=variant,
                context={"channel": f"@{PUBLIC_CHANNEL}" if PUBLIC_CHANNEL else ""},
            )
            ok = await _telegram_send_message(
                chat_id=int(u.tg_id),
                text=text,
                buttons=_retention_buttons(flow="welcome", variant=variant),
            )
            if ok:
                track_event(
                    tg_id=int(u.tg_id),
                    event_name="retention_ping",
                    source="worker",
                    meta={"flow": "welcome_chain", "variant": variant, "campaign_key": campaign_key},
                )
        await asyncio.sleep(3600)


async def expiry_chain_job() -> None:
    while True:
        now = _utcnow()
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
            stage = _expiry_stage(delta)
            if not stage:
                continue
            campaign_key = f"expiry_{stage}:{expiry.date().isoformat()}"
            if not _mark_campaign_sent_once(tg_id=int(u.tg_id), campaign_key=campaign_key):
                continue
            variant = _ab_variant_for_user(tg_id=int(u.tg_id), flow_key=f"expiry_{stage}")
            text = _retention_text(flow=stage, variant=variant, context={"expiry_date": expiry.date().isoformat()})
            ok = await _telegram_send_message(
                chat_id=int(u.tg_id),
                text=text,
                buttons=_retention_buttons(flow=stage, variant=variant),
            )
            if ok:
                track_event(
                    tg_id=int(u.tg_id),
                    event_name="retention_ping",
                    source="worker",
                    meta={"flow": "expiry_chain", "stage": stage, "variant": variant, "campaign_key": campaign_key},
                )
        await asyncio.sleep(3600)


async def start99_welcome_offer_job() -> None:
    while True:
        if not START99_WELCOME_ENABLED:
            await asyncio.sleep(900)
            continue

        now = _utcnow()
        newer_than = now - timedelta(hours=int(START99_WELCOME_MAX_HOURS))
        older_than = now - timedelta(hours=int(START99_WELCOME_MIN_HOURS))
        s = SessionLocal()
        try:
            rows = (
                s.query(ExternalOrder)
                .filter(ExternalOrder.tg_id.isnot(None))
                .filter(ExternalOrder.paid_at.isnot(None))
                .filter(ExternalOrder.paid_at >= newer_than)
                .filter(ExternalOrder.paid_at <= older_than)
                .filter(func.lower(func.coalesce(ExternalOrder.provider, "")) == "freekassa")
                .filter(func.lower(func.coalesce(ExternalOrder.status, "")) == "paid")
                .filter(func.lower(func.coalesce(ExternalOrder.plan_code, "")) == "start_99")
                .order_by(ExternalOrder.paid_at.desc())
                .limit(300)
                .all()
            )
        finally:
            s.close()

        for row in rows:
            tg_id = int(getattr(row, "tg_id", 0) or 0)
            if tg_id <= 0:
                continue
            campaign_key = f"start99_welcome_offer:{str(getattr(row, 'order_id', '') or '')[:32]}"
            if not _mark_campaign_sent_once(tg_id=tg_id, campaign_key=campaign_key):
                continue
            variant = _ab_variant_for_user(tg_id=tg_id, flow_key="start99_offer")
            discount_pct, applied_now = _ensure_pending_discount(
                tg_id=tg_id,
                pct=int(START99_WELCOME_DISCOUNT_PCT),
                code=START99_WELCOME_DISCOUNT_CODE,
            )
            text = _retention_text(
                flow="start99_offer",
                variant=variant,
                context={"discount_pct": str(max(1, int(discount_pct or START99_WELCOME_DISCOUNT_PCT)))},
            )
            if not applied_now and int(discount_pct) > 0:
                text += f"\n\nТекущая сохранённая скидка: {int(discount_pct)}%."
            ok = await _telegram_send_message(
                chat_id=tg_id,
                text=text,
                buttons=_retention_buttons(flow="start99_offer", variant=variant),
            )
            if ok:
                track_event(
                    tg_id=tg_id,
                    event_name="retention_ping",
                    source="worker",
                    meta={
                        "flow": "start99_welcome_offer",
                        "variant": variant,
                        "campaign_key": campaign_key,
                        "discount_pct": int(discount_pct or 0),
                        "applied_now": bool(applied_now),
                    },
                )
        await asyncio.sleep(900)


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
        now = _utcnow()
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
        now = _utcnow()
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
            variant = _ab_variant_for_user(tg_id=int(u.tg_id), flow_key="reactivation")
            text = _retention_text(
                flow="reactivation",
                variant=variant,
                context={"channel": f"@{PUBLIC_CHANNEL}" if PUBLIC_CHANNEL else ""},
            )
            ok = await _telegram_send_message(
                chat_id=int(u.tg_id),
                text=text,
                buttons=_retention_buttons(flow="reactivation", variant=variant),
            )
            if ok:
                track_event(
                    tg_id=int(u.tg_id),
                    event_name="retention_ping",
                    source="worker",
                    meta={"flow": "reactivation", "variant": variant, "campaign_key": campaign_base},
                )
        await asyncio.sleep(3600)


async def node_metrics_watchdog_job() -> None:
    started_at = _utcnow()
    stale_cycles = 0
    while True:
        stale_after = max(300, int(os.getenv("NODE_METRICS_STALE_AFTER_SECONDS", "900")))
        s = SessionLocal()
        try:
            last_sample = s.query(func.max(NodeHealthSample.sampled_at)).scalar()
        finally:
            s.close()

        now = _utcnow()
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

        now = _utcnow()
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
            normalized_reason = _normalize_channel_membership_reason(reason)
            logger.info(
                "channel_bonus_guard user_id=%s raw_status=%s normalized_reason=%s action=%s",
                int(u.tg_id),
                reason,
                normalized_reason,
                "skip_member" if is_member else "verify",
            )
            if is_member:
                continue
            if normalized_reason != "not_member":
                # Do not revoke on transient Telegram/API errors to avoid accidental mass downgrades.
                logger.warning(
                    "channel_bonus_guard user_id=%s raw_status=%s normalized_reason=%s action=%s",
                    int(u.tg_id),
                    reason,
                    normalized_reason,
                    "skip_transient",
                )
                now_alert = _utcnow()
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
                logger.info(
                    "channel_bonus_guard user_id=%s raw_status=%s normalized_reason=%s action=%s",
                    int(u.tg_id),
                    reason,
                    normalized_reason,
                    "revoke_bonus",
                )
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
                    meta={"flow": "channel_bonus_guard", "reason": normalized_reason, "raw_reason": reason},
                )
        await asyncio.sleep(900)


async def free_cycle_reset_job() -> None:
    while True:
        try:
            await process_due_free_cycle_resets(max_users=500)
        except Exception:
            pass
        await asyncio.sleep(600)


async def main() -> None:
    init_db()
    tasks = [
        asyncio.create_task(welcome_chain_job()),
        asyncio.create_task(abandoned_cart_job()),
        asyncio.create_task(expiry_chain_job()),
        asyncio.create_task(start99_welcome_offer_job()),
        asyncio.create_task(oto_free_job()),
        asyncio.create_task(reactivation_job()),
        asyncio.create_task(node_metrics_watchdog_job()),
        asyncio.create_task(channel_bonus_guard_job()),
        asyncio.create_task(free_cycle_reset_job()),
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())


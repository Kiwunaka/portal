from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

import aiohttp
from dotenv import load_dotenv
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import IntegrityError

# Load env from repo-local file first to avoid cwd-dependent startup behavior.
load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
load_dotenv()

from config import Settings
from control_panel import ControlPanel
from copy_catalog import get_copy_text
from db import SessionLocal, init_db
from events_service import track_event
from free_cycle_service import mark_user_became_free, process_due_free_cycle_resets
from models import (
    CampaignSend,
    Event,
    ExternalOrder,
    ExternalPaymentEvent,
    FunnelEvent,
    KeyActionHistory,
    NodeHealthSample,
    OpsAlert,
    PayAttempt,
    ReferralBonusQueue,
    RenderedSubscriptionSnapshot,
    SubscriptionFetchEvent,
    Template,
    User,
    UserKeyPolicy,
)
from node_policy import free_pool_node_codes
from offers_service import create_offer, expire_stale_offers, get_active_offer
from observer_service import cleanup_observer_retention
from pay_attempts_service import find_abandoned_candidates, mark_abandoned, mark_abandoned_notified
from admin_ops_service import refresh_ops_alerts_for_current_state
from antiabuse_privacy_service import drain_antiabuse_retention

logger = logging.getLogger(__name__)


BOT_USERNAME = (os.getenv("BOT_USERNAME") or "pokrov_vpnbot").lstrip("@")
SUPPORT_USERNAME = (os.getenv("SUPPORT_BOT_USERNAME") or os.getenv("SUPPORT_USERNAME") or "pokrov_supportbot").lstrip("@")
FREE_TOTAL_GB = int(os.getenv("FREE_TOTAL_GB", "5"))
PUBLIC_CHANNEL = (os.getenv("PUBLIC_CHANNEL") or "pokrov_vpn").lstrip("@")
AUTO_FREE_DAYS = int(os.getenv("AUTO_FREE_DAYS", "3650"))
START99_WELCOME_ENABLED = os.getenv("START99_WELCOME_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on", "y"}
START99_WELCOME_MIN_HOURS = max(1, int(os.getenv("START99_WELCOME_MIN_HOURS", "24")))
START99_WELCOME_MAX_HOURS = max(START99_WELCOME_MIN_HOURS + 1, int(os.getenv("START99_WELCOME_MAX_HOURS", "48")))
START99_WELCOME_DISCOUNT_PCT = max(1, min(95, int(os.getenv("START99_WELCOME_DISCOUNT_PCT", "15"))))
START99_WELCOME_DISCOUNT_CODE = (os.getenv("START99_WELCOME_DISCOUNT_CODE") or "STARTBOOST").strip().upper()[:20]
REFERRAL_BONUS_DAYS = max(1, int(os.getenv("REFERRAL_BONUS_DAYS", "15")))
REFERRAL_ANTIFRAUD_MAX_WAIT_HOURS = max(1, int(os.getenv("REFERRAL_ANTIFRAUD_MAX_WAIT_HOURS", "168")))
EVENT_RETENTION_DAYS = max(1, int(os.getenv("EVENT_RETENTION_DAYS", "180")))
FUNNEL_EVENT_RETENTION_DAYS = max(1, int(os.getenv("FUNNEL_EVENT_RETENTION_DAYS", "180")))
PAY_ATTEMPT_RETENTION_DAYS = max(1, int(os.getenv("PAY_ATTEMPT_RETENTION_DAYS", "365")))
EXTERNAL_PAYMENT_EVENT_RETENTION_DAYS = max(1, int(os.getenv("EXTERNAL_PAYMENT_EVENT_RETENTION_DAYS", "180")))
SUBSCRIPTION_EVENT_RETENTION_DAYS = max(1, int(os.getenv("SUBSCRIPTION_EVENT_RETENTION_DAYS", "90")))
TELEMETRY_RETENTION_INTERVAL_SECONDS = max(3600, int(os.getenv("TELEMETRY_RETENTION_INTERVAL_SECONDS", "21600")))
ANTIABUSE_RETENTION_BATCH_LIMIT = max(1, min(10_000, int(os.getenv("ANTIABUSE_RETENTION_BATCH_LIMIT", "1000"))))
ANTIABUSE_RETENTION_MAX_BATCHES_PER_RUN = max(
    1,
    min(100, int(os.getenv("ANTIABUSE_RETENTION_MAX_BATCHES_PER_RUN", "20"))),
)
ANTIABUSE_RETENTION_INTERVAL_SECONDS = max(
    60,
    min(900, int(os.getenv("ANTIABUSE_RETENTION_INTERVAL_SECONDS", "300"))),
)
ADMIN_OPS_ALERT_REFRESH_INTERVAL_SECONDS = max(60, int(os.getenv("ADMIN_OPS_ALERT_REFRESH_INTERVAL_SECONDS", "300")))

_TEMPLATE_CACHE_TTL_SECONDS = max(30, int(os.getenv("RETENTION_TEMPLATE_CACHE_TTL_SECONDS", "180")))
_TEMPLATE_CACHE: dict[str, tuple[datetime, str]] = {}

RETENTION_DEFAULT_COPY: dict[str, dict[str, str]] = {
    "welcome": {
        "a": (
            "Добро пожаловать в POKROV.\n\n"
            "Откройте кабинет, скачайте приложение и нажмите «Подключить».\n"
            "Если что-то не получится, поддержка рядом."
        ),
        "b": (
            "Профиль готов.\n\n"
            "Скачайте приложение для своего устройства и проверьте подключение.\n"
            "Если приложение не видит доступ, напишите нам."
        ),
    },
    "t3": {
        "a": (
            "До конца доступа осталось около 3 дней.\n\n"
            "Продлите заранее, чтобы подключение не прервалось."
        ),
        "b": (
            "Доступ скоро закончится.\n\n"
            "Продление заранее помогает избежать перерыва."
        ),
    },
    "t1": {
        "a": (
            "До конца доступа осталось примерно сутки.\n\n"
            "Продлите сейчас, чтобы не возвращаться к настройке заново."
        ),
        "b": (
            "Завтра доступ закончится.\n\n"
            "Продлите сейчас, если хотите пользоваться POKROV без паузы."
        ),
    },
    "t0": {
        "a": (
            "Доступ заканчивается сегодня.\n\n"
            "Если POKROV нужен без паузы, продлите прямо сейчас."
        ),
        "b": (
            "Срок доступа почти завершён.\n\n"
            "Пара минут на продление — и подключение останется активным."
        ),
    },
    "reactivation": {
        "a": (
            "Профиль и настройки сохранены.\n\n"
            "Вернитесь в один клик и продолжайте без повторной настройки."
        ),
        "b": (
            "Срок доступа завершился, но его можно восстановить за минуту.\n\n"
            "Откройте продление и снова подключайтесь."
        ),
    },
    "start99_offer": {
        "a": (
            "Вы уже проверили POKROV в реальном трафике.\n\n"
            "Мы сохранили скидку {discount_pct}% на первое продление."
        ),
        "b": (
            "Бесплатный период почти закончился.\n\n"
            "Скидка {discount_pct}% уже ждёт на следующем шаге продления."
        ),
    },
}

RETENTION_BUTTONS: dict[str, dict[str, str]] = {
    "welcome": {"a": "Открыть кабинет", "b": "Перейти к подключению"},
    "t3": {"a": "Продлить заранее", "b": "Сохранить доступ"},
    "t1": {"a": "Продлить сейчас", "b": "Избежать паузы"},
    "t0": {"a": "Открыть продление", "b": "Оставить доступ активным"},
    "reactivation": {"a": "Вернуться в POKROV", "b": "Проверить подключение"},
    "start99_offer": {"a": "Продлить со скидкой", "b": "Забрать предложение"},
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
    catalog_key = {
        "welcome": "retention.welcome",
        "t3": "retention.t3",
        "t1": "retention.t1",
        "t0": "retention.t0",
        "reactivation": "retention.reactivation",
        "start99_offer": "retention.start99_offer",
    }.get(flow_key, "")
    fallback = (
        get_copy_text(catalog_key, "") if catalog_key else ""
        or RETENTION_DEFAULT_COPY.get(flow_key, {}).get(variant_key)
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
        or "Продолжить"
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
                desc = str((body or {}).get("description") or "").lower()
                if resp.status != 200:
                    if "chat not found" in desc:
                        return False, "channel_not_found"
                    if "bot is not a member" in desc:
                        return False, "bot_not_in_channel"
                    if "not a member" in desc or "user not found" in desc:
                        return False, "not_member"
                    return False, "telegram_http_error"
                if not isinstance(body, dict) or not body.get("ok"):
                    if "chat not found" in desc:
                        return False, "channel_not_found"
                    if "bot is not a member" in desc:
                        return False, "bot_not_in_channel"
                    if "not a member" in desc or "user not found" in desc:
                        return False, "not_member"
                    return False, "telegram_api_error"
                status_raw = str((body.get("result") or {}).get("status") or "").strip().lower()
                if _normalize_channel_membership_reason(status_raw) == "not_member":
                    return False, status_raw or "not_member"
                return status_raw in {"creator", "administrator", "member", "restricted"}, status_raw
    except asyncio.TimeoutError:
        logger.warning("telegram_get_chat_member timeout channel=%s user_id=%s", channel_username, int(user_id))
        return False, "telegram_timeout"
    except aiohttp.ClientError as exc:
        logger.warning(
            "telegram_get_chat_member network_error channel=%s user_id=%s error=%s",
            channel_username,
            int(user_id),
            exc.__class__.__name__,
        )
        return False, "telegram_network_error"
    except (ValueError, TypeError) as exc:
        logger.warning(
            "telegram_get_chat_member payload_error channel=%s user_id=%s error=%s",
            channel_username,
            int(user_id),
            exc.__class__.__name__,
        )
        return False, "telegram_payload_error"
    except Exception as exc:
        logger.warning(
            "telegram_get_chat_member exception channel=%s user_id=%s error=%s",
            channel_username,
            int(user_id),
            exc.__class__.__name__,
        )
        return False, "telegram_exception"


def _normalize_channel_membership_reason(reason: str) -> str:
    raw = str(reason or "").strip().lower()
    raw = raw.strip("`'\"")
    raw = " ".join(raw.split())
    if raw in {"channel_not_found", "bot_not_in_channel"}:
        return raw
    if raw in {"not_member", "left", "kicked"}:
        return "not_member"
    if "not a member" in raw or "user not found" in raw:
        return "not_member"
    if raw.startswith("left") or raw.startswith("kicked"):
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
            free_codes = free_pool_node_codes(nodes)
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
        row = CampaignSend(tg_id=int(tg_id), campaign_key=str(campaign_key), sent_at=_utcnow())
        s.add(row)
        s.commit()
        return True
    except IntegrityError:
        s.rollback()
        return False
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


def _key_history_log(
    *,
    tg_id: int,
    action: str,
    node_code: str | None = None,
    actor_tg_id: int | None = None,
    source: str = "worker",
    meta: dict | None = None,
) -> None:
    s = SessionLocal()
    try:
        row = KeyActionHistory(
            tg_id=int(tg_id),
            node_code=(str(node_code or "").strip().lower() or None),
            action=str(action or "").strip()[:64],
            actor_tg_id=(int(actor_tg_id) if actor_tg_id is not None else None),
            source=str(source or "worker").strip()[:32] or "worker",
            meta=json.dumps(meta or {}, ensure_ascii=False, separators=(",", ":")),
            created_at=_utcnow(),
        )
        s.add(row)
        s.commit()
    except Exception:
        s.rollback()
    finally:
        s.close()


def _process_referral_bonus_queue(*, limit: int = 100) -> dict[str, int]:
    now = _utcnow()
    s = SessionLocal()
    processed = 0
    rewarded = 0
    waiting = 0
    rejected = 0
    try:
        rows = (
            s.query(ReferralBonusQueue)
            .filter(ReferralBonusQueue.status == "pending", ReferralBonusQueue.ready_at <= now)
            .order_by(ReferralBonusQueue.id.asc())
            .limit(max(1, min(int(limit), 1000)))
            .all()
        )
        for row in rows:
            processed += 1
            referred = s.query(User).filter(User.tg_id == int(row.referred_tg_id)).first()
            referrer = s.query(User).filter(User.tg_id == int(row.referrer_tg_id)).first()
            if not referred or not referrer:
                row.status = "rejected_missing_user"
                row.processed_at = now
                rejected += 1
                continue
            has_activity = (
                s.query(Event.id)
                .filter(
                    Event.tg_id == int(referred.tg_id),
                    Event.created_at >= (row.queued_at or (now - timedelta(days=1))),
                    Event.event_name.in_(["connected_ok", "clicked_connect"]),
                )
                .first()
                is not None
            )
            age_hours = max(0, int((now - (row.queued_at or now)).total_seconds() // 3600))
            if not has_activity:
                if age_hours >= int(REFERRAL_ANTIFRAUD_MAX_WAIT_HOURS):
                    row.status = "rejected_no_activity"
                    row.processed_at = now
                    rejected += 1
                else:
                    row.ready_at = now + timedelta(hours=6)
                    waiting += 1
                continue
            ref_sub = str(referrer.sub_type or "").upper().strip()
            ref_expiry = referrer.expiry_at if referrer.expiry_at and referrer.expiry_at > now else None
            if not (bool(referrer.is_active) and ref_sub == "PAID" and ref_expiry):
                row.status = "rejected_referrer_inactive"
                row.processed_at = now
                rejected += 1
                continue
            row_meta = {}
            try:
                parsed_meta = json.loads(getattr(row, "meta", None) or "{}")
                if isinstance(parsed_meta, dict):
                    row_meta = parsed_meta
            except Exception:
                row_meta = {}
            if not bool(row_meta.get("counted")):
                referrer.referral_count = int(referrer.referral_count or 0) + 1
            referrer.expiry_at = ref_expiry + timedelta(days=max(1, int(REFERRAL_BONUS_DAYS)))
            referrer.is_active = True
            row.status = "rewarded"
            row.processed_at = now
            rewarded += 1
        s.commit()
    except Exception:
        s.rollback()
    finally:
        s.close()
    return {"processed": processed, "rewarded": rewarded, "waiting": waiting, "rejected": rejected}


async def referral_bonus_queue_job() -> None:
    while True:
        out = _process_referral_bonus_queue(limit=200)
        if int(out.get("rewarded", 0)) > 0:
            logger.info("referral_bonus_queue rewarded=%s waiting=%s rejected=%s", out.get("rewarded"), out.get("waiting"), out.get("rejected"))
        await asyncio.sleep(900)


async def key_limits_watchdog_job() -> None:
    while True:
        s = SessionLocal()
        try:
            policies = (
                s.query(UserKeyPolicy)
                .filter(or_(UserKeyPolicy.soft_cap_gb.isnot(None), UserKeyPolicy.hard_cap_gb.isnot(None)))
                .all()
            )
        finally:
            s.close()

        if not policies:
            await asyncio.sleep(900)
            continue

        panel = ControlPanel()
        try:
            await panel.login()
            now = _utcnow()
            day_key = now.strftime("%Y%m%d")
            for policy in policies:
                tg_id = int(policy.tg_id)
                node_code = str(policy.node_code or "").strip().lower()
                if not node_code:
                    continue
                snapshots = await panel.get_user_key_snapshots(tg_id=tg_id, node_codes=[node_code])
                if not snapshots:
                    continue
                row = snapshots[0]
                runtime = row.get("runtime") or {}
                total_bytes = int(runtime.get("total", int(runtime.get("up", 0) or 0) + int(runtime.get("down", 0) or 0)) or 0)
                total_gb = float(total_bytes) / float(1024**3)
                soft_cap = int(policy.soft_cap_gb) if policy.soft_cap_gb is not None else None
                hard_cap = int(policy.hard_cap_gb) if policy.hard_cap_gb is not None else None
                if soft_cap and bool(policy.notify_soft) and total_gb >= float(soft_cap):
                    campaign_key = f"key_soft:{tg_id}:{node_code}:{day_key}"
                    if _mark_campaign_sent_once(tg_id=tg_id, campaign_key=campaign_key):
                        await _telegram_send_message(
                            chat_id=tg_id,
                            text=f"ℹ️ Лимит {soft_cap} GB на ключе {node_code.upper()} превышен ({total_gb:.2f} GB).",
                        )
                if hard_cap and bool(policy.notify_hard) and total_gb >= float(hard_cap):
                    campaign_key = f"key_hard:{tg_id}:{node_code}:{day_key}"
                    first_alert = _mark_campaign_sent_once(tg_id=tg_id, campaign_key=campaign_key)
                    if first_alert:
                        await _telegram_send_message(
                            chat_id=tg_id,
                            text=f"⚠️ Жесткий лимит {hard_cap} GB на ключе {node_code.upper()} достигнут ({total_gb:.2f} GB).",
                        )
                    if bool(policy.auto_disable_on_hard):
                        disabled = await panel.set_user_key_enabled_on_node(tg_id=tg_id, node_code=node_code, enable=False)
                        if disabled:
                            _key_history_log(
                                tg_id=tg_id,
                                action="key_disable_hard_cap",
                                node_code=node_code,
                                actor_tg_id=0,
                                source="worker",
                                meta={"hard_cap_gb": hard_cap, "usage_gb": round(total_gb, 3)},
                            )
                            track_event(
                                tg_id=tg_id,
                                event_name="expired",
                                source="worker",
                                meta={"flow": "key_limits_watchdog", "node_code": node_code, "hard_cap_gb": hard_cap},
                            )
        finally:
            await panel.close()
        await asyncio.sleep(900)


async def abandoned_cart_job() -> None:
    while True:
        rows = find_abandoned_candidates(older_than_minutes=60, limit=200)
        for row in rows:
            text = "⏳ Слот оплаты всё ещё зарезервирован.\n\nНужна помощь с оплатой или подключением?"
            buttons = [
                [{"text": "Оплатить / Продлить", "url": _bot_pay_url()}],
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

            text = "🎁 Мягкий апгрейд на 2 часа: 1 месяц за 149 Stars.\nОффер закреплён за вами."
            buttons = [[{"text": "Подключить / Продлить", "url": _bot_pay_url()}]]
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


async def admin_ops_alert_refresh_once() -> int:
    notifications: list[dict] = []
    s = SessionLocal()
    try:
        stale_after_seconds = max(300, int(os.getenv("NODE_METRICS_STALE_AFTER_SECONDS", "900")))
        _rows, notifications, _metrics_status, _capacity_payload = refresh_ops_alerts_for_current_state(
            s=s,
            now=_utcnow(),
            free_limit_gb=int(FREE_TOTAL_GB),
            cycle_days=30,
            stale_after_seconds=stale_after_seconds,
        )
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()

    try:
        await _deliver_ops_alert_notifications(notifications)
    except Exception:
        logger.exception("admin_ops_alert notification delivery failed")
    return len(notifications)


async def _deliver_ops_alert_notifications(notifications: list[dict]) -> None:
    if not notifications or not int(Settings.ADMIN_ID or 0):
        return
    delivered: dict[str, str] = {}
    for item in notifications[:20]:
        fingerprint = str(item.get("fingerprint") or "")
        kind = str(item.get("kind") or "active")
        severity = str(item.get("severity") or "warning").upper()
        title = str(item.get("title") or fingerprint)
        prefix = "RESOLVED" if kind == "resolved" else severity
        ok = await _telegram_send_message(
            chat_id=int(Settings.ADMIN_ID),
            text=f"POKROV ops alert: {prefix}\n{title}\n{fingerprint}",
        )
        delivered[fingerprint] = "sent" if ok else "send_failed"
    if not delivered:
        return
    s = SessionLocal()
    try:
        now = _utcnow()
        for fingerprint, status in delivered.items():
            row = s.query(OpsAlert).filter(OpsAlert.fingerprint == fingerprint).first()
            if not row:
                continue
            row.last_delivery_at = now
            row.last_delivery_status = status
            row.updated_at = now
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


async def admin_ops_alert_refresh_job() -> None:
    while True:
        try:
            notification_count = await admin_ops_alert_refresh_once()
            if notification_count:
                logger.info("admin_ops_alert_refresh notifications=%s", notification_count)
        except Exception:
            logger.exception("admin_ops_alert_refresh_job failed")
        await asyncio.sleep(ADMIN_OPS_ALERT_REFRESH_INTERVAL_SECONDS)


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
                "skip_member" if is_member else "evaluate_non_member",
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
                            f"Причина: `{normalized_reason}` (raw: `{reason}`).\n"
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
            else:
                logger.warning(
                    "channel_bonus_guard user_id=%s raw_status=%s normalized_reason=%s action=%s",
                    int(u.tg_id),
                    reason,
                    normalized_reason,
                    "revoke_failed",
                )
        await asyncio.sleep(900)


async def free_cycle_reset_job() -> None:
    while True:
        try:
            await process_due_free_cycle_resets(max_users=500)
        except Exception:
            logger.exception("free_cycle_reset_job failed")
        await asyncio.sleep(600)


async def observer_retention_job() -> None:
    while True:
        session = SessionLocal()
        try:
            cleanup_observer_retention(s=session)
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("observer_retention_job failed")
        finally:
            session.close()
        await asyncio.sleep(21600)


async def antiabuse_retention_job() -> None:
    while True:
        try:
            report = await asyncio.to_thread(
                drain_antiabuse_retention,
                SessionLocal,
                now=_utcnow(),
                batch_limit=ANTIABUSE_RETENTION_BATCH_LIMIT,
                max_batches=ANTIABUSE_RETENTION_MAX_BATCHES_PER_RUN,
            )
            if int(report.get("changed_batches", 0) or 0) > 0:
                logger.info("antiabuse_retention report=%s", report)
            if any(int(value or 0) > 0 for value in dict(report.get("remaining") or {}).values()):
                logger.warning("antiabuse_retention backlog_remaining=%s", report.get("remaining"))
                await asyncio.sleep(1)
                continue
        except Exception:
            logger.exception("antiabuse_retention_job failed")
        await asyncio.sleep(ANTIABUSE_RETENTION_INTERVAL_SECONDS)


def _delete_older_than(session, model, column, cutoff: datetime) -> int:
    return int(
        session.query(model)
        .filter(column < cutoff)
        .delete(synchronize_session=False)
        or 0
    )


async def telemetry_retention_job() -> None:
    while True:
        session = SessionLocal()
        try:
            now = _utcnow()
            deleted = {
                "events": _delete_older_than(session, Event, Event.created_at, now - timedelta(days=EVENT_RETENTION_DAYS)),
                "funnel_events": _delete_older_than(
                    session,
                    FunnelEvent,
                    FunnelEvent.created_at,
                    now - timedelta(days=FUNNEL_EVENT_RETENTION_DAYS),
                ),
                "pay_attempts": _delete_older_than(
                    session,
                    PayAttempt,
                    PayAttempt.started_at,
                    now - timedelta(days=PAY_ATTEMPT_RETENTION_DAYS),
                ),
                "external_payment_events": _delete_older_than(
                    session,
                    ExternalPaymentEvent,
                    ExternalPaymentEvent.created_at,
                    now - timedelta(days=EXTERNAL_PAYMENT_EVENT_RETENTION_DAYS),
                ),
                "subscription_fetch_events": _delete_older_than(
                    session,
                    SubscriptionFetchEvent,
                    SubscriptionFetchEvent.created_at,
                    now - timedelta(days=SUBSCRIPTION_EVENT_RETENTION_DAYS),
                ),
                "rendered_subscription_snapshots": _delete_older_than(
                    session,
                    RenderedSubscriptionSnapshot,
                    RenderedSubscriptionSnapshot.created_at,
                    now - timedelta(days=SUBSCRIPTION_EVENT_RETENTION_DAYS),
                ),
            }
            session.commit()
            if any(deleted.values()):
                logger.info("telemetry_retention deleted=%s", deleted)
        except Exception:
            session.rollback()
            logger.exception("telemetry_retention_job failed")
        finally:
            session.close()
        await asyncio.sleep(TELEMETRY_RETENTION_INTERVAL_SECONDS)


async def _supervise_job(name: str, job_factory, *, restart_delay_seconds: int = 10) -> None:
    while True:
        try:
            await job_factory()
            logger.warning("worker job %s exited unexpectedly; restarting", name)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("worker job %s crashed; restarting", name)
        await asyncio.sleep(max(1, int(restart_delay_seconds)))


async def main() -> None:
    init_db()
    tasks = [
        asyncio.create_task(_supervise_job("welcome_chain", welcome_chain_job)),
        asyncio.create_task(_supervise_job("abandoned_cart", abandoned_cart_job)),
        asyncio.create_task(_supervise_job("expiry_chain", expiry_chain_job)),
        asyncio.create_task(_supervise_job("start99_welcome_offer", start99_welcome_offer_job)),
        asyncio.create_task(_supervise_job("oto_free", oto_free_job)),
        asyncio.create_task(_supervise_job("reactivation", reactivation_job)),
        asyncio.create_task(_supervise_job("node_metrics_watchdog", node_metrics_watchdog_job)),
        asyncio.create_task(_supervise_job("admin_ops_alert_refresh", admin_ops_alert_refresh_job)),
        asyncio.create_task(_supervise_job("channel_bonus_guard", channel_bonus_guard_job)),
        asyncio.create_task(_supervise_job("free_cycle_reset", free_cycle_reset_job)),
        asyncio.create_task(_supervise_job("observer_retention", observer_retention_job)),
        asyncio.create_task(_supervise_job("antiabuse_retention", antiabuse_retention_job)),
        asyncio.create_task(_supervise_job("telemetry_retention", telemetry_retention_job)),
        asyncio.create_task(_supervise_job("referral_bonus_queue", referral_bonus_queue_job)),
        asyncio.create_task(_supervise_job("key_limits_watchdog", key_limits_watchdog_job)),
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())


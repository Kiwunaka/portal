from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

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
from economy_service import (
    begin_channel_loss_grace,
    cancel_channel_loss_grace,
    expire_stale_trial_reservations,
    migrate_pending_legacy_referral_queue,
    normalize_reserved_trial_deadlines,
    reconcile_stale_trial_projections,
    rebuild_due_entitlement_projections,
    release_due_referrer_rewards,
    reverse_due_channel_grants,
)
from free_cycle_service import FREE_STANDARD_QUOTA_BYTES, process_due_free_cycle_resets, queue_free_profile_reentry
from models import (
    AcquisitionHandoff,
    AcquisitionSession,
    AdminActionIntent,
    CampaignSend,
    Event,
    EntitlementGrant,
    ExternalPaymentEvent,
    FunnelEvent,
    InternalIngestNonce,
    KeyActionHistory,
    NodeHealthSample,
    OpsAlert,
    PayAttempt,
    RenderedSubscriptionSnapshot,
    RuProbeRun,
    RuProbeUploaderHeartbeat,
    SubscriptionFetchEvent,
    Template,
    User,
    UserKeyPolicy,
)
from node_provisioning_service import process_node_provisioning_jobs
from observer_service import cleanup_observer_retention
from pay_attempts_service import find_abandoned_candidates, mark_abandoned, mark_abandoned_notified
from admin_ops_service import ops_alert_notification_batches, refresh_ops_alerts_for_current_state
from antiabuse_privacy_service import drain_antiabuse_retention
from app_first_service import expire_app_telegram_start_codes
from support_attachment_cleanup_service import SupportAttachmentCleanupCursor, reconcile_support_attachments
from emergency_catalog_worker import emergency_catalog_worker_enabled, emergency_catalog_worker_job
import incident_service

logger = logging.getLogger(__name__)


BOT_USERNAME = (os.getenv("BOT_USERNAME") or "pokrov_vpnbot").lstrip("@")
SUPPORT_USERNAME = (os.getenv("SUPPORT_BOT_USERNAME") or os.getenv("SUPPORT_USERNAME") or "pokrov_supportbot").lstrip("@")
FREE_TOTAL_GB = int(FREE_STANDARD_QUOTA_BYTES // (1024**3))
PUBLIC_CHANNEL = (os.getenv("PUBLIC_CHANNEL") or "pokrov_vpn").lstrip("@")
AUTO_FREE_DAYS = int(os.getenv("AUTO_FREE_DAYS", "3650"))
REFERRAL_BONUS_DAYS = max(1, int(os.getenv("REFERRAL_BONUS_DAYS", "10")))
REFERRAL_ANTIFRAUD_MAX_WAIT_HOURS = max(1, int(os.getenv("REFERRAL_ANTIFRAUD_MAX_WAIT_HOURS", "168")))
EVENT_RETENTION_DAYS = max(1, int(os.getenv("EVENT_RETENTION_DAYS", "180")))
FUNNEL_EVENT_RETENTION_DAYS = max(1, int(os.getenv("FUNNEL_EVENT_RETENTION_DAYS", "180")))
PAY_ATTEMPT_RETENTION_DAYS = max(1, int(os.getenv("PAY_ATTEMPT_RETENTION_DAYS", "365")))
EXTERNAL_PAYMENT_EVENT_RETENTION_DAYS = max(1, int(os.getenv("EXTERNAL_PAYMENT_EVENT_RETENTION_DAYS", "180")))
SUBSCRIPTION_EVENT_RETENTION_DAYS = max(1, int(os.getenv("SUBSCRIPTION_EVENT_RETENTION_DAYS", "90")))
RU_PROBE_RETENTION_DAYS = max(1, int(os.getenv("RU_PROBE_RETENTION_DAYS", "180")))
RU_PROBE_HEARTBEAT_RETENTION_DAYS = max(
    1,
    int(os.getenv("RU_PROBE_HEARTBEAT_RETENTION_DAYS", "30")),
)
ADMIN_ACTION_INTENT_RETENTION_DAYS = 7
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
NODE_PROVISIONING_BATCH_LIMIT = max(1, min(100, int(os.getenv("NODE_PROVISIONING_BATCH_LIMIT", "20"))))
NODE_PROVISIONING_MAX_ATTEMPTS = max(1, min(20, int(os.getenv("NODE_PROVISIONING_MAX_ATTEMPTS", "5"))))
NODE_PROVISIONING_STALE_AFTER_SECONDS = max(
    30,
    min(86_400, int(os.getenv("NODE_PROVISIONING_STALE_AFTER_SECONDS", "300"))),
)
NODE_PROVISIONING_POLL_SECONDS = max(1, min(300, int(os.getenv("NODE_PROVISIONING_POLL_SECONDS", "10"))))
ADMIN_OPS_ALERT_REFRESH_INTERVAL_SECONDS = max(60, int(os.getenv("ADMIN_OPS_ALERT_REFRESH_INTERVAL_SECONDS", "300")))
SUPPORT_ATTACHMENT_CLEANUP_INTERVAL_SECONDS = max(
    60,
    int(os.getenv("SUPPORT_ATTACHMENT_CLEANUP_INTERVAL_SECONDS", "900")),
)
SUPPORT_ATTACHMENT_CLEANUP_GRACE_SECONDS = max(
    60,
    int(os.getenv("SUPPORT_ATTACHMENT_CLEANUP_GRACE_SECONDS", "3600")),
)
SUPPORT_ATTACHMENT_CLEANUP_BATCH_SIZE = max(
    1,
    min(1000, int(os.getenv("SUPPORT_ATTACHMENT_CLEANUP_BATCH_SIZE", "100"))),
)
INCIDENT_COMPENSATION_INTERVAL_SECONDS = max(
    30,
    min(900, int(os.getenv("INCIDENT_COMPENSATION_INTERVAL_SECONDS", "60"))),
)
SUPPORT_ATTACHMENT_CLEANUP_SCAN_LIMIT = max(
    1,
    min(5000, int(os.getenv("SUPPORT_ATTACHMENT_CLEANUP_SCAN_LIMIT", "500"))),
)
SUPPORT_ATTACHMENT_UPLOAD_DIR = Path(
    os.getenv("SUPPORT_UPLOAD_DIR") or (Path(__file__).resolve().parent / "uploads" / "support")
).resolve()
_SUPPORT_ATTACHMENT_CLEANUP_CURSOR = SupportAttachmentCleanupCursor()

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
}

RETENTION_BUTTONS: dict[str, dict[str, str]] = {
    "welcome": {"a": "Открыть кабинет", "b": "Перейти к подключению"},
    "t3": {"a": "Продлить заранее", "b": "Сохранить доступ"},
    "t1": {"a": "Продлить сейчас", "b": "Избежать паузы"},
    "t0": {"a": "Открыть продление", "b": "Оставить доступ активным"},
    "reactivation": {"a": "Вернуться в POKROV", "b": "Проверить подключение"},
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


def _expiry_access_kind(user: User) -> str:
    plan_code = str(getattr(user, "current_plan_code", "") or "").strip().lower()
    sub_type = str(getattr(user, "sub_type", "") or "").strip().upper()
    if plan_code == "trial" or sub_type.startswith("TRIAL"):
        return "trial"
    if plan_code in {"channel_bonus", "bonus"} or sub_type.startswith("BONUS") or sub_type in {
        "CHANNEL_BONUS",
        "OPENING_BONUS",
        "FRIEND_GIFT",
    }:
        return "bonus"
    return "paid"


def _expiry_stage(delta: timedelta, *, access_kind: str = "paid") -> str:
    if access_kind == "paid" and timedelta(days=2) < delta <= timedelta(days=3):
        return "t3"
    if timedelta(hours=16) < delta <= timedelta(hours=32):
        return "t1"
    if timedelta(hours=-12) <= delta <= timedelta(hours=12):
        return "t0"
    return ""


def _telegram_delivery_window_open(user: User, *, now: datetime) -> bool:
    timezone_name = str(getattr(user, "app_timezone", "") or "").strip() or "Europe/Moscow"
    try:
        user_timezone = ZoneInfo(timezone_name)
    except Exception:
        user_timezone = ZoneInfo("Europe/Moscow")
    aware_now = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now.astimezone(timezone.utc)
    local_hour = aware_now.astimezone(user_timezone).hour
    return 9 <= local_hour < 21


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
    if flow_key in {"welcome", "reactivation"} and PUBLIC_CHANNEL:
        rows.append([{"text": "📣 Канал с обновлениями", "url": f"https://t.me/{PUBLIC_CHANNEL}"}])
    return rows


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
        user.expiry_at = now + timedelta(days=max(30, int(AUTO_FREE_DAYS)))
        user.channel_bonus_active = False
        user.channel_bonus_revoked_at = now
        queue_free_profile_reentry(s, user=user, source="channel_bonus_revoked", now=now)
        s.commit()
    except Exception:
        s.rollback()
        return False
    finally:
        s.close()

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
    try:
        migration = migrate_pending_legacy_referral_queue(s, now=now, limit=limit)
        release = release_due_referrer_rewards(s, now=now)
        rebuild_due_entitlement_projections(s, now=now)
        s.commit()
        return {
            "processed": int(migration["migrated"]),
            "migrated": int(migration["migrated"]),
            "retryable": int(migration["retryable"]),
            "rewarded": int(release["released"]),
            "waiting": int(release["waiting"]),
            "rejected": int(release["rejected"]),
        }
    except Exception:
        s.rollback()
        return {"processed": 0, "migrated": 0, "retryable": 0, "rewarded": 0, "waiting": 0, "rejected": 0}
    finally:
        s.close()


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
            if not _telegram_delivery_window_open(u, now=now):
                continue
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
            if not _telegram_delivery_window_open(u, now=now):
                continue
            expiry = u.expiry_at
            if not expiry:
                continue
            delta = expiry - now
            access_kind = _expiry_access_kind(u)
            stage = _expiry_stage(delta, access_kind=access_kind)
            if not stage:
                continue
            campaign_key = f"expiry_{access_kind}_{stage}:{expiry.date().isoformat()}"
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
                    meta={
                        "flow": "expiry_chain",
                        "access_kind": access_kind,
                        "stage": stage,
                        "variant": variant,
                        "campaign_key": campaign_key,
                    },
                )
        await asyncio.sleep(3600)


async def reactivation_job() -> None:
    while True:
        now = _utcnow()
        campaign_base = f"promo:reactivation:{now.strftime('%Y%m%d')}"
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
            if not _telegram_delivery_window_open(u, now=now):
                continue
            if _sent_recently(tg_id=int(u.tg_id), campaign_prefix="expiry_", within_days=3):
                continue
            if _sent_recently(tg_id=int(u.tg_id), campaign_prefix="promo:", within_days=30):
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
    for batch in ops_alert_notification_batches(notifications):
        ok = await _telegram_send_message(
            chat_id=int(Settings.ADMIN_ID),
            text=str(batch.get("text") or ""),
        )
        for fingerprint in batch.get("fingerprints") or []:
            delivered[str(fingerprint)] = "sent" if ok else "send_failed"
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
    while True:
        try:
            result = await channel_bonus_guard_once()
            if any(int(result.get(key, 0)) for key in ("grace_started", "grace_cancelled", "reversed")):
                logger.info("channel_bonus_guard result=%s", result)
        except Exception:
            logger.exception("channel_bonus_guard failed")
        await asyncio.sleep(900)


def _channel_grant_telegram_id(session, grant: EntitlementGrant) -> int:
    try:
        metadata = json.loads(str(grant.metadata_json or "{}"))
    except (TypeError, ValueError):
        metadata = {}
    telegram_id = int(metadata.get("telegram_id") or 0) if isinstance(metadata, dict) else 0
    if telegram_id > 0:
        return telegram_id
    users = session.query(User).filter(User.account_id == str(grant.account_id)).order_by(User.tg_id.asc()).all()
    for user in users:
        linked = int(user.linked_telegram_id or 0)
        if linked > 0:
            return linked
    for user in users:
        direct = int(user.tg_id or 0)
        if 0 < direct < 8_000_000_000_000:
            return direct
    return 0


async def channel_bonus_guard_once(
    *,
    is_channel_member=_telegram_get_chat_member,
    now: datetime | None = None,
) -> dict[str, int]:
    current_now = (now or _utcnow()).replace(microsecond=0)
    channel = (PUBLIC_CHANNEL or "").lstrip("@").strip()
    if not channel:
        return {"checked": 0, "grace_started": 0, "grace_cancelled": 0, "reversed": 0, "transient": 0}
    session = SessionLocal()
    checked = 0
    grace_started = 0
    grace_cancelled = 0
    transient = 0
    try:
        grants = (
            session.query(EntitlementGrant)
            .filter(
                EntitlementGrant.source.in_(["telegram_channel", "telegram_channel_grandfathered"]),
                EntitlementGrant.status.in_(["active", "grace"]),
                EntitlementGrant.reversed_at.is_(None),
            )
            .order_by(EntitlementGrant.created_at.asc())
            .all()
        )
        for grant in grants:
            telegram_id = _channel_grant_telegram_id(session, grant)
            if telegram_id <= 0:
                transient += 1
                continue
            checked += 1
            member, reason = await is_channel_member(channel, telegram_id)
            normalized = _normalize_channel_membership_reason(reason)
            if member:
                if cancel_channel_loss_grace(session, account_id=str(grant.account_id), now=current_now):
                    grace_cancelled += 1
            elif normalized == "not_member":
                was_active = str(grant.status) == "active"
                begin_channel_loss_grace(session, account_id=str(grant.account_id), now=current_now)
                if was_active:
                    grace_started += 1
            else:
                transient += 1
        reversal = reverse_due_channel_grants(session, now=current_now)
        session.commit()
        return {
            "checked": checked,
            "grace_started": grace_started,
            "grace_cancelled": grace_cancelled,
            "reversed": int(reversal["reversed"]),
            "transient": transient,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def free_cycle_reset_job() -> None:
    while True:
        try:
            await process_due_free_cycle_resets(max_users=500)
        except Exception:
            logger.exception("free_cycle_reset_job failed")
        await asyncio.sleep(600)


async def node_provisioning_once() -> dict:
    return await process_node_provisioning_jobs(
        SessionLocal,
        limit=NODE_PROVISIONING_BATCH_LIMIT,
        max_attempts=NODE_PROVISIONING_MAX_ATTEMPTS,
        stale_after_seconds=NODE_PROVISIONING_STALE_AFTER_SECONDS,
    )


async def node_provisioning_job() -> None:
    while True:
        try:
            report = await node_provisioning_once()
            if any(int(report.get(key, 0) or 0) > 0 for key in ("claimed", "manual_review", "stale_recovered")):
                logger.info(
                    "node_provisioning claimed=%s succeeded=%s retried=%s manual_review=%s stale_recovered=%s",
                    report.get("claimed"),
                    report.get("succeeded"),
                    report.get("retried"),
                    report.get("manual_review"),
                    report.get("stale_recovered"),
                )
        except Exception:
            logger.exception("node_provisioning_job failed")
        await asyncio.sleep(NODE_PROVISIONING_POLL_SECONDS)


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


async def support_attachment_cleanup_job() -> None:
    while True:
        try:
            report = await asyncio.to_thread(
                reconcile_support_attachments,
                SessionLocal,
                upload_dir=SUPPORT_ATTACHMENT_UPLOAD_DIR,
                now=_utcnow(),
                grace_seconds=SUPPORT_ATTACHMENT_CLEANUP_GRACE_SECONDS,
                batch_size=SUPPORT_ATTACHMENT_CLEANUP_BATCH_SIZE,
                scan_limit=SUPPORT_ATTACHMENT_CLEANUP_SCAN_LIMIT,
                cursor=_SUPPORT_ATTACHMENT_CLEANUP_CURSOR,
            )
            logger.info("support_attachment_cleanup report=%s", report)
        except Exception:
            logger.exception("support_attachment_cleanup_job failed")
        await asyncio.sleep(SUPPORT_ATTACHMENT_CLEANUP_INTERVAL_SECONDS)


async def trial_reservation_expiry_job() -> None:
    while True:
        session = SessionLocal()
        try:
            normalization_result = normalize_reserved_trial_deadlines(session, now=_utcnow())
            result = expire_stale_trial_reservations(session, now=_utcnow())
            projection_result = reconcile_stale_trial_projections(session, now=_utcnow(), limit=200)
            session.commit()
            if int(normalization_result.get("corrected", 0)) > 0:
                logger.info("trial_reservation_normalization result=%s", normalization_result)
            if int(result.get("expired", 0)) > 0:
                logger.info("trial_reservation_expiry result=%s", result)
            if int(projection_result.get("reconciled", 0)) > 0:
                logger.warning("stale_trial_projection_reconciliation result=%s", projection_result)
        except Exception:
            session.rollback()
            logger.exception("trial_reservation_expiry_job failed")
        finally:
            session.close()
        await asyncio.sleep(600)


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


def run_incident_compensation_once(*, session, now: datetime) -> dict[str, int]:
    return incident_service.process_pending_incident_compensations(
        session,
        now=now,
        limit=20,
    )


async def incident_compensation_job() -> None:
    while True:
        session = SessionLocal()
        try:
            result = run_incident_compensation_once(session=session, now=_utcnow())
            session.commit()
            if int(result.get("processed", 0) or 0) > 0:
                logger.info("incident_compensation result=%s", result)
        except Exception:
            session.rollback()
            logger.exception("incident_compensation_job failed")
        finally:
            session.close()
        await asyncio.sleep(INCIDENT_COMPENSATION_INTERVAL_SECONDS)


def _delete_older_than(session, model, column, cutoff: datetime) -> int:
    return int(
        session.query(model)
        .filter(column < cutoff)
        .delete(synchronize_session=False)
        or 0
    )


def run_telemetry_retention_once(*, session, now: datetime) -> dict[str, int]:
    ru_now = (
        now.replace(tzinfo=timezone.utc)
        if now.tzinfo is None or now.utcoffset() is None
        else now.astimezone(timezone.utc)
    )
    deleted = {
        "app_telegram_links_expired": expire_app_telegram_start_codes(
            session,
            now=now,
        ),
        "acquisition_handoffs": _delete_older_than(
            session,
            AcquisitionHandoff,
            AcquisitionHandoff.expires_at,
            now,
        ),
        "acquisition_sessions": _delete_older_than(
            session,
            AcquisitionSession,
            AcquisitionSession.expires_at,
            now,
        ),
        "events": _delete_older_than(
            session,
            Event,
            Event.created_at,
            now - timedelta(days=EVENT_RETENTION_DAYS),
        ),
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
        "ru_probe_runs": int(
            session.query(RuProbeRun)
            .filter(RuProbeRun.retention_hold == False)
            .filter(
                RuProbeRun.finished_at
                < ru_now - timedelta(days=RU_PROBE_RETENTION_DAYS)
            )
            .delete(synchronize_session=False)
            or 0
        ),
        "internal_ingest_nonces": int(
            session.query(InternalIngestNonce)
            .filter(InternalIngestNonce.expires_at < ru_now)
            .delete(synchronize_session=False)
            or 0
        ),
        "ru_probe_uploader_heartbeats": int(
            session.query(RuProbeUploaderHeartbeat)
            .filter(
                RuProbeUploaderHeartbeat.observed_at
                < ru_now - timedelta(days=RU_PROBE_HEARTBEAT_RETENTION_DAYS)
            )
            .delete(synchronize_session=False)
            or 0
        ),
        "admin_action_intents": int(
            session.query(AdminActionIntent)
            .filter(AdminActionIntent.status.in_(("prepared", "expired")))
            .filter(AdminActionIntent.admin_audit_id.is_(None))
            .filter(
                AdminActionIntent.expires_at
                < ru_now - timedelta(days=ADMIN_ACTION_INTENT_RETENTION_DAYS)
            )
            .delete(synchronize_session=False)
            or 0
        ),
    }
    return deleted


async def telemetry_retention_job() -> None:
    while True:
        session = SessionLocal()
        try:
            now = _utcnow()
            deleted = run_telemetry_retention_once(session=session, now=now)
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
        asyncio.create_task(_supervise_job("reactivation", reactivation_job)),
        asyncio.create_task(_supervise_job("node_metrics_watchdog", node_metrics_watchdog_job)),
        asyncio.create_task(_supervise_job("admin_ops_alert_refresh", admin_ops_alert_refresh_job)),
        asyncio.create_task(_supervise_job("channel_bonus_guard", channel_bonus_guard_job)),
        asyncio.create_task(_supervise_job("free_cycle_reset", free_cycle_reset_job)),
        asyncio.create_task(_supervise_job("node_provisioning", node_provisioning_job)),
        asyncio.create_task(_supervise_job("observer_retention", observer_retention_job)),
        asyncio.create_task(_supervise_job("support_attachment_cleanup", support_attachment_cleanup_job)),
        asyncio.create_task(_supervise_job("trial_reservation_expiry", trial_reservation_expiry_job)),
        asyncio.create_task(_supervise_job("antiabuse_retention", antiabuse_retention_job)),
        asyncio.create_task(_supervise_job("incident_compensation", incident_compensation_job)),
        asyncio.create_task(_supervise_job("telemetry_retention", telemetry_retention_job)),
        asyncio.create_task(_supervise_job("referral_bonus_queue", referral_bonus_queue_job)),
        asyncio.create_task(_supervise_job("key_limits_watchdog", key_limits_watchdog_job)),
    ]
    if emergency_catalog_worker_enabled():
        tasks.append(
            asyncio.create_task(
                _supervise_job("emergency_catalog", emergency_catalog_worker_job)
            )
        )
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())


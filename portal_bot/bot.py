# -*- coding: utf-8 -*-
"""
🌐 Kiwunaka Portal Bot v2
Aiogram 3.x + SQLite + Telegram Stars

FIXED: Handle existing users in 3x-ui panel
"""

import asyncio
import base64
import hashlib
import hmac
import logging
import os
import re
import uuid
import secrets
from pathlib import Path
from io import BytesIO
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import aiohttp
import qrcode
from copy_catalog import get_copy_text
try:
    from aiogram import Bot, Dispatcher, F, Router, BaseMiddleware
    from aiogram.filters import Command, CommandStart
    from aiogram.types import (
        Message, CallbackQuery, PreCheckoutQuery,
        InlineKeyboardMarkup, InlineKeyboardButton,
        WebAppInfo, LabeledPrice, ContentType, BufferedInputFile,
        BotCommand, MenuButtonCommands
    )
    from aiogram.enums import ParseMode
    AIROGRAM_AVAILABLE = True
except ModuleNotFoundError:
    AIROGRAM_AVAILABLE = False

    class _FilterExpr:
        def __getattr__(self, _name):
            return self

        def __call__(self, *args, **kwargs):
            return self

        def __eq__(self, _other):
            return self

        def __and__(self, _other):
            return self

        def __rand__(self, _other):
            return self

        def __or__(self, _other):
            return self

        def __ror__(self, _other):
            return self

        def __invert__(self):
            return self

        def in_(self, _values):
            return self

        def startswith(self, _prefix):
            return self

    class _DecoratorRouter:
        def message(self, *args, **kwargs):
            def _decorator(func):
                return func
            return _decorator

        def callback_query(self, *args, **kwargs):
            def _decorator(func):
                return func
            return _decorator

        def pre_checkout_query(self, *args, **kwargs):
            def _decorator(func):
                return func
            return _decorator

    class Bot:
        def __init__(self, *args, **kwargs):
            class _Session:
                async def close(self):
                    return None

            self.session = _Session()

        async def get_chat_member(self, *args, **kwargs):
            raise RuntimeError("aiogram is not installed")

    class Dispatcher:
        def include_router(self, *_args, **_kwargs):
            return None

        async def start_polling(self, *_args, **_kwargs):
            raise RuntimeError("aiogram is not installed")

    class Router(_DecoratorRouter):
        pass

    class BaseMiddleware:
        async def __call__(self, handler, event, data):
            return await handler(event, data)

    class Command:
        def __init__(self, *_args, **_kwargs):
            pass

    class CommandStart:
        def __init__(self, *_args, **_kwargs):
            pass

    class _BaseType:
        def __init__(self, *args, **kwargs):
            self.args = args
            for k, v in kwargs.items():
                setattr(self, k, v)

    class Message(_BaseType):
        pass

    class CallbackQuery(_BaseType):
        pass

    class PreCheckoutQuery(_BaseType):
        pass

    class InlineKeyboardMarkup(_BaseType):
        pass

    class InlineKeyboardButton(_BaseType):
        pass

    class WebAppInfo(_BaseType):
        pass

    class LabeledPrice(_BaseType):
        pass

    class BotCommand(_BaseType):
        pass

    class MenuButtonCommands(_BaseType):
        pass

    class BufferedInputFile(_BaseType):
        pass

    class ContentType:
        SUCCESSFUL_PAYMENT = "successful_payment"

    class ParseMode:
        MARKDOWN = "Markdown"
        HTML = "HTML"

    F = _FilterExpr()
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, BigInteger, func
from sqlalchemy.orm import sessionmaker, declarative_base
import json
from control_panel import ControlPanel
import html

# ==========================================
#               CONFIGURATION
# ==========================================
load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_USERNAME = (os.getenv("BOT_USERNAME") or "portal_privacy_bot").lstrip("@")
BOT_USERNAME_MD = BOT_USERNAME.replace("_", "\\_")

# Panel
PANEL_URL = os.getenv("PANEL_URL", "http://127.0.0.1:15739")
PANEL_USER = os.getenv("PANEL_USER", "admin")
PANEL_PASS = os.getenv("PANEL_PASS", "")
PANEL_PATH = os.getenv("PANEL_PATH", "")
INBOUND_ID = int(os.getenv("INBOUND_ID", "4"))
TRIAL_LIMIT_GB = 30
INBOUND_ID_BACKUP = int(os.getenv("INBOUND_ID_BACKUP", "0"))  # Optional legacy failover inbound id (0 = disabled)

# Server
HOST_DOMAIN = os.getenv("HOST_DOMAIN") or os.getenv("DOMAIN") or "kiwunaka.space"
PUBLIC_WEB_DOMAIN = (os.getenv("PUBLIC_WEB_DOMAIN") or "").strip()
VLESS_PORT = int(os.getenv("VLESS_PORT", "443"))
VLESS_SNI = os.getenv("VLESS_SNI", "yahoo.com")
VLESS_PBK = os.getenv("VLESS_PBK", "")
VLESS_SID = os.getenv("VLESS_SID", "")
VLESS_FP = os.getenv("VLESS_FP", "firefox")
VLESS_FLOW = os.getenv("VLESS_FLOW", "xtls-rprx-vision")

# URLs
# Cache-buster helps Telegram in-app webview pick up new builds quickly.
_WEBAPP_DEFAULT_HOST = PUBLIC_WEB_DOMAIN or HOST_DOMAIN
WEBAPP_URL = os.getenv("WEBAPP_URL", f"https://{_WEBAPP_DEFAULT_HOST}/webapp/?v=20260214")
PUBLIC_API_BASE_URL = os.getenv("PUBLIC_API_BASE_URL", f"https://{HOST_DOMAIN}")
PAY_CHECKOUT_URL = (
    os.getenv("PAY_CHECKOUT_URL")
    or os.getenv("CHECKOUT_URL")
    or f"https://{(PUBLIC_WEB_DOMAIN or HOST_DOMAIN)}/checkout/"
).strip()
CHECKOUT_TICKET_SECRET = (
    (os.getenv("CHECKOUT_TICKET_SECRET") or "").strip()
    or (os.getenv("WEBAPP_SESSION_SECRET") or "").strip()
)
CHECKOUT_TICKET_TTL_SECONDS = max(60, int(os.getenv("CHECKOUT_TICKET_TTL_SECONDS", "900")))
SUPPORT_USERNAME = (os.getenv("SUPPORT_USERNAME") or "portal_privacy_helpbot").lstrip("@")
SUPPORT_USERNAME = (os.getenv("SUPPORT_BOT_USERNAME") or SUPPORT_USERNAME).lstrip("@")
APP_ANDROID_PLAY_URL = (os.getenv("APP_ANDROID_PLAY_URL") or "https://play.google.com/store/apps/details?id=app.hiddify.com").strip()
APP_ANDROID_APK_URL = (os.getenv("APP_ANDROID_APK_URL") or "").strip()
APP_ANDROID_MIRROR_URL = (os.getenv("APP_ANDROID_MIRROR_URL") or "").strip()
APP_WINDOWS_EXE_URL = (os.getenv("APP_WINDOWS_EXE_URL") or "https://github.com/hiddify/hiddify-next/releases").strip()
APP_WINDOWS_MIRROR_URL = (os.getenv("APP_WINDOWS_MIRROR_URL") or "").strip()
APP_DOCS_URL = (os.getenv("APP_DOCS_URL") or "").strip()
FREE_LIMIT_IP = int(os.getenv("FREE_LIMIT_IP", "1"))
PAID_LIMIT_IP = int(os.getenv("PAID_LIMIT_IP", "5"))
FREE_TOTAL_GB = int(os.getenv("FREE_TOTAL_GB", "30"))
FREE_SPEED_LIMIT_KBPS = int(os.getenv("FREE_SPEED_LIMIT_KBPS", "6250"))
FREE_SPEED_MBIT = max(1, int(round((FREE_SPEED_LIMIT_KBPS * 8) / 1000)))
NEWS_CHANNEL_ID = os.getenv("NEWS_CHANNEL_ID", "@portal_privacy")
STACK_TOTAL_DISCOUNT_CAP = float(os.getenv("STACK_TOTAL_DISCOUNT_CAP", "0.70"))
FAMILY_SLOT_STARS = int(os.getenv("FAMILY_SLOT_STARS", "99"))
FAMILY_SLOT_DAYS = int(os.getenv("FAMILY_SLOT_DAYS", "30"))
FAMILY_SLOT_MAX = int(os.getenv("FAMILY_SLOT_MAX", "3"))


def _first_non_empty(*values: str) -> str:
    for value in values:
        value = str(value or "").strip()
        if value:
            return value
    return ""


IOS_APP_LINK = "https://apps.apple.com/app/streisand/id6450534064"
ANDROID_APP_LINK = _first_non_empty(APP_ANDROID_PLAY_URL, APP_ANDROID_APK_URL, APP_ANDROID_MIRROR_URL)
WINDOWS_APP_LINK = _first_non_empty(APP_WINDOWS_EXE_URL, APP_WINDOWS_MIRROR_URL)
MAC_APP_LINK = WINDOWS_APP_LINK or "https://github.com/hiddify/hiddify-next/releases"

# Protected users — NEVER modify, sync, or message these users
PROTECTED_USERS = {
    5187992322,  # @Oksidraiv
    1808391444,  # @ars_oil
}

# Protected UUIDs — never touch in panel operations
PROTECTED_UUIDS = {
    "49a30dde-ac75-42fc-a29f-aa3bf32c2e2b",  # Admin
    "e396db00-b105-41f7-b671-bf26d1098494",  # RODITELI
}
# (legacy tariffs removed; see unified TARIFFS below)

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Track last bot message per user for cleanup
last_bot_message: dict[int, int] = {}  # tg_id -> message_id
AUTO_DELETE_SECONDS = max(0, int(os.getenv("BOT_AUTO_DELETE_SECONDS", "86400")))
_auto_delete_scheduled: set[tuple[int, int]] = set()
_user_context_mode: dict[int, str] = {}  # tg_id -> "main" | "support"

BTN_STYLE_PRIMARY = "primary"
BTN_STYLE_SUCCESS = "success"
BTN_STYLE_DANGER = "danger"
BTN_EMOJI_PRIMARY_ID = (os.getenv("TG_BTN_EMOJI_PRIMARY_ID") or "").strip()
BTN_EMOJI_SUCCESS_ID = (os.getenv("TG_BTN_EMOJI_SUCCESS_ID") or "").strip()
BTN_EMOJI_DANGER_ID = (os.getenv("TG_BTN_EMOJI_DANGER_ID") or "").strip()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "y"}


OPENING_PREMIUM_ENABLED = _env_bool("OPENING_PREMIUM_ENABLED", default=True)
OPENING_PREMIUM_START_CODE = (os.getenv("OPENING_PREMIUM_START_CODE") or "launch14").strip().lower()
OPENING_PREMIUM_DAYS = max(1, int(os.getenv("OPENING_PREMIUM_DAYS", "14")))
OPENING_PREMIUM_CAMPAIGN_KEY = (
    (os.getenv("OPENING_PREMIUM_CAMPAIGN_KEY") or f"opening_premium_{OPENING_PREMIUM_DAYS}d").strip()[:64]
)
FRIEND_GIFT_ENABLED = _env_bool("FRIEND_GIFT_ENABLED", default=True)
FRIEND_GIFT_DAYS = max(1, int(os.getenv("FRIEND_GIFT_DAYS", "3")))
FRIEND_GIFT_CAMPAIGN_KEY = (
    (os.getenv("FRIEND_GIFT_CAMPAIGN_KEY") or f"friend_gift_{FRIEND_GIFT_DAYS}d").strip()[:64]
)
CHANNEL_PREMIUM_DAYS = max(1, int(os.getenv("CHANNEL_PREMIUM_DAYS", "10")))
BOT_RUB_BUTTON_ENABLED = _env_bool("BOT_RUB_BUTTON_ENABLED", default=False)
MAIN_CONNECT_CTA_LABELS = {
    "a": "🟦 Подключить / Продлить",
    "b": "🟦 Выбрать тариф",
}


def _inline_button_supported_fields() -> set[str]:
    fields = getattr(InlineKeyboardButton, "model_fields", None)
    if isinstance(fields, dict):
        return set(fields.keys())
    fields = getattr(InlineKeyboardButton, "__fields__", None)
    if isinstance(fields, dict):
        return set(fields.keys())
    return {"text", "callback_data", "url", "web_app"}


INLINE_BUTTON_FIELDS = _inline_button_supported_fields()
SUPPORTS_BTN_STYLE = "style" in INLINE_BUTTON_FIELDS
SUPPORTS_BTN_ICON = "icon_custom_emoji_id" in INLINE_BUTTON_FIELDS


def _is_private_user_chat(chat_id: int, tg_id: int) -> bool:
    return int(chat_id) > 0 and int(tg_id) > 0 and int(chat_id) == int(tg_id)


def _set_support_context(tg_id: int, *, enabled: bool) -> None:
    if int(tg_id) <= 0:
        return
    _user_context_mode[int(tg_id)] = "support" if enabled else "main"


def _is_support_context(tg_id: int) -> bool:
    return _user_context_mode.get(int(tg_id), "main") == "support"


def _is_support_callback_data(callback_data: str | None) -> bool:
    data = (callback_data or "").strip().lower()
    return data.startswith("support") or data.startswith("faq_") or data.startswith("ticket_")


def _ab_variant_for_user(*, tg_id: int, flow_key: str) -> str:
    seed = f"{str(flow_key).strip().lower()}:{int(tg_id)}".encode("utf-8")
    digest = hashlib.sha256(seed).digest()
    return "b" if (digest[0] % 2) else "a"


def _main_connect_cta_text(tg_id: int) -> str:
    variant = _ab_variant_for_user(tg_id=int(tg_id), flow_key="bot_main_cta")
    return str(MAIN_CONNECT_CTA_LABELS.get(variant) or MAIN_CONNECT_CTA_LABELS["a"])


async def _schedule_auto_delete(bot: Bot, chat_id: int, message_id: int) -> None:
    if AUTO_DELETE_SECONDS <= 0:
        return
    key = (int(chat_id), int(message_id))
    if key in _auto_delete_scheduled:
        return
    _auto_delete_scheduled.add(key)

    async def _delete_later() -> None:
        try:
            await asyncio.sleep(AUTO_DELETE_SECONDS)
            await bot.delete_message(chat_id=int(chat_id), message_id=int(message_id))
        except Exception:
            pass
        finally:
            _auto_delete_scheduled.discard(key)

    asyncio.create_task(_delete_later())


async def _track_context_message(
    *,
    bot: Bot,
    chat_id: int,
    tg_id: int,
    message_id: int,
) -> None:
    chat_id = int(chat_id)
    tg_id = int(tg_id)
    message_id = int(message_id)

    if not _is_private_user_chat(chat_id, tg_id) or tg_id == ADMIN_ID:
        return

    support_mode = _is_support_context(tg_id)
    previous_id = last_bot_message.get(tg_id)
    if not support_mode:
        if previous_id and previous_id != message_id:
            try:
                await bot.delete_message(chat_id=tg_id, message_id=previous_id)
            except Exception:
                pass
        last_bot_message[tg_id] = message_id

    await _schedule_auto_delete(bot, chat_id=tg_id, message_id=message_id)


def _extract_chat_id(*, args: tuple[object, ...], kwargs: dict[str, object]) -> int | None:
    chat_id = kwargs.get("chat_id")
    if chat_id is None and args:
        chat_id = args[0]
    try:
        return int(chat_id) if chat_id is not None else None
    except Exception:
        return None


def _patch_outgoing_message_methods(bot: Bot) -> None:
    for method_name in ("send_message", "send_photo"):
        original = getattr(bot, method_name, None)
        if not callable(original):
            continue

        async def _wrapped(*args, _orig=original, **kwargs):
            result = await _orig(*args, **kwargs)
            try:
                chat_id = _extract_chat_id(args=args, kwargs=kwargs)
                message_id = int(getattr(result, "message_id", 0) or 0)
                if chat_id and message_id:
                    await _track_context_message(
                        bot=bot,
                        chat_id=int(chat_id),
                        tg_id=int(chat_id),
                        message_id=message_id,
                    )
            except Exception:
                pass
            return result

        setattr(bot, method_name, _wrapped)


def _parse_mode_to_bot_api(parse_mode: str | object | None) -> str | None:
    if parse_mode is None:
        return None
    raw = str(getattr(parse_mode, "value", parse_mode)).strip()
    up = raw.upper()
    if "MARKDOWN" in up:
        return "Markdown"
    if "HTML" in up:
        return "HTML"
    return raw or None


def _btn_spec(
    text: str,
    *,
    callback_data: str | None = None,
    url: str | None = None,
    web_app_url: str | None = None,
    style: str | None = None,
    icon_custom_emoji_id: str | None = None,
) -> dict[str, str]:
    spec: dict[str, str] = {"text": text}
    if callback_data:
        spec["callback_data"] = callback_data
    if url:
        spec["url"] = url
    if web_app_url:
        spec["web_app_url"] = web_app_url
    if style:
        spec["style"] = style
    if icon_custom_emoji_id:
        spec["icon_custom_emoji_id"] = icon_custom_emoji_id
    return spec


def _button_from_spec(spec: dict[str, str]) -> InlineKeyboardButton:
    kwargs: dict[str, object] = {"text": spec.get("text", "")}
    if spec.get("callback_data"):
        kwargs["callback_data"] = spec["callback_data"]
    if spec.get("url"):
        kwargs["url"] = spec["url"]
    if spec.get("web_app_url"):
        kwargs["web_app"] = WebAppInfo(url=spec["web_app_url"])
    if spec.get("style") and SUPPORTS_BTN_STYLE:
        kwargs["style"] = spec["style"]
    if spec.get("icon_custom_emoji_id") and SUPPORTS_BTN_ICON:
        kwargs["icon_custom_emoji_id"] = spec["icon_custom_emoji_id"]
    return InlineKeyboardButton(**kwargs)


def _keyboard_from_specs(rows: list[list[dict[str, str]]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[ _button_from_spec(spec) for spec in row ] for row in rows]
    )


def _keyboard_payload(rows: list[list[dict[str, str]]]) -> dict[str, object]:
    payload_rows: list[list[dict[str, object]]] = []
    for row in rows:
        p_row: list[dict[str, object]] = []
        for spec in row:
            b: dict[str, object] = {"text": spec.get("text", "")}
            if spec.get("callback_data"):
                b["callback_data"] = spec["callback_data"]
            if spec.get("url"):
                b["url"] = spec["url"]
            if spec.get("web_app_url"):
                b["web_app"] = {"url": spec["web_app_url"]}
            if spec.get("style"):
                b["style"] = spec["style"]
            if spec.get("icon_custom_emoji_id"):
                b["icon_custom_emoji_id"] = spec["icon_custom_emoji_id"]
            p_row.append(b)
        payload_rows.append(p_row)
    return {"inline_keyboard": payload_rows}


def _needs_raw_markup(rows: list[list[dict[str, str]]]) -> bool:
    for row in rows:
        for spec in row:
            if spec.get("style") and not SUPPORTS_BTN_STYLE:
                return True
            if spec.get("icon_custom_emoji_id") and not SUPPORTS_BTN_ICON:
                return True
    return False


async def _bot_api_call(method: str, payload: dict[str, object]) -> dict[str, object] | None:
    token = (BOT_TOKEN or "").strip()
    if not token:
        return None
    endpoint = f"https://api.telegram.org/bot{token}/{method}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return None
                body = await resp.json(content_type=None)
                if not bool((body or {}).get("ok")):
                    return None
                return body or None
    except Exception:
        return None


async def _send_text_with_specs(
    *,
    bot: Bot,
    chat_id: int,
    text: str,
    rows: list[list[dict[str, str]]],
    parse_mode: str | object | None = None,
) -> bool:
    pm = _parse_mode_to_bot_api(parse_mode)
    if _needs_raw_markup(rows):
        payload: dict[str, object] = {
            "chat_id": int(chat_id),
            "text": text,
            "disable_web_page_preview": True,
            "reply_markup": _keyboard_payload(rows),
        }
        if pm:
            payload["parse_mode"] = pm
        body = await _bot_api_call("sendMessage", payload)
        if not body:
            return False
        result = (body or {}).get("result")
        if isinstance(result, dict):
            message_id = int(result.get("message_id") or 0)
            if message_id:
                await _track_context_message(
                    bot=bot,
                    chat_id=int(chat_id),
                    tg_id=int(chat_id),
                    message_id=int(message_id),
                )
        return True
    try:
        sent = await bot.send_message(
            chat_id=int(chat_id),
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=True,
            reply_markup=_keyboard_from_specs(rows),
        )
        message_id = int(getattr(sent, "message_id", 0) or 0)
        if message_id:
            await _track_context_message(
                bot=bot,
                chat_id=int(chat_id),
                tg_id=int(chat_id),
                message_id=message_id,
            )
        return True
    except Exception:
        return False


async def _edit_text_with_specs(
    *,
    bot: Bot,
    chat_id: int,
    message_id: int,
    text: str,
    rows: list[list[dict[str, str]]],
    parse_mode: str | object | None = None,
) -> bool:
    pm = _parse_mode_to_bot_api(parse_mode)
    if _needs_raw_markup(rows):
        payload: dict[str, object] = {
            "chat_id": int(chat_id),
            "message_id": int(message_id),
            "text": text,
            "disable_web_page_preview": True,
            "reply_markup": _keyboard_payload(rows),
        }
        if pm:
            payload["parse_mode"] = pm
        body = await _bot_api_call("editMessageText", payload)
        if not body:
            return False
        await _track_context_message(
            bot=bot,
            chat_id=int(chat_id),
            tg_id=int(chat_id),
            message_id=int(message_id),
        )
        return True
    try:
        await bot.edit_message_text(
            chat_id=int(chat_id),
            message_id=int(message_id),
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=True,
            reply_markup=_keyboard_from_specs(rows),
        )
        await _track_context_message(
            bot=bot,
            chat_id=int(chat_id),
            tg_id=int(chat_id),
            message_id=int(message_id),
        )
        return True
    except Exception:
        return False


def _utcnow() -> datetime:
    # Use naive UTC everywhere (SQLite DateTime is stored as text; legacy DBs may contain tz offsets).
    return datetime.utcnow().replace(tzinfo=None)


def _naive_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    tz = getattr(dt, "tzinfo", None)
    if tz is None:
        return dt
    try:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        # Last resort: drop tzinfo without converting.
        return dt.replace(tzinfo=None)

# ==========================================
#               DATABASE
# ==========================================
from db import SessionLocal, init_db
from models import (
    Achievement,
    AdminAudit,
    AppSetting,
    CampaignSend,
    FamilySlot,
    GiftCard,
    IncentiveCampaign,
    LiveUpdate,
    PromoCode,
    PromoUsage,
    Review,
    StartLink,
    Template,
    User,
)
from nodes_repo import enabled_nodes
from events_service import track_event
from free_cycle_service import mark_user_became_free
from gift_cards_service import (
    create_gift_card as create_gift_card_service,
    get_gift_card as get_gift_card_service,
    redeem_gift_card as redeem_gift_card_service,
)
from pay_attempts_service import (
    get_attempt_by_payload,
    mark_invoice_sent,
    mark_paid,
    resolve_pending_attempt_for_payment,
    start_attempt,
)
from points_service import award_referral_points, preview_redeemable_points, spend_points
from web_auth_service import create_web_session_token
from tickets_repo import (
    STATUS_CLOSED,
    STATUS_IN_PROGRESS,
    STATUS_OPEN,
    add_ticket_message,
    can_access_ticket,
    create_ticket,
    get_ticket_by_id,
    get_user_active_ticket,
    list_active_tickets,
    list_ticket_messages,
    list_user_tickets,
    set_ticket_status,
)

# Initialize DB schema (idempotent).
init_db()
Session = SessionLocal


def _telegram_payment_fingerprint(payment: object | None) -> str:
    if not payment:
        return ""
    for value in (
        getattr(payment, "telegram_payment_charge_id", None),
        getattr(payment, "provider_payment_charge_id", None),
        getattr(payment, "invoice_payload", None),
    ):
        text = str(value or "").strip()
        if text:
            return text[:255]
    return ""


def _stars_payment_key(payment_fingerprint: str) -> str:
    fp = str(payment_fingerprint or "").strip()
    if not fp:
        return ""
    digest = hashlib.sha256(fp.encode("utf-8")).hexdigest()[:40]
    return f"stars_payment:{digest}"


def _stars_payment_already_processed(payment_fingerprint: str) -> bool:
    key = _stars_payment_key(payment_fingerprint)
    if not key:
        return False
    s = Session()
    try:
        row = s.query(AppSetting).filter(AppSetting.key == key).first()
        if not row or not str(row.value_json or "").strip():
            return False
        payload = json.loads(row.value_json)
        return str((payload or {}).get("status") or "").strip().lower() == "done"
    except Exception:
        return False
    finally:
        s.close()


def _mark_stars_payment_processed(*, payment_fingerprint: str, invoice_payload: str, tg_id: int) -> None:
    key = _stars_payment_key(payment_fingerprint)
    if not key:
        return
    s = Session()
    try:
        now = _utcnow()
        payload = {
            "status": "done",
            "invoice_payload": str(invoice_payload or "")[:255],
            "tg_id": int(tg_id),
            "updated_at": now.isoformat(),
        }
        row = s.query(AppSetting).filter(AppSetting.key == key).first()
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        if not row:
            row = AppSetting(key=key, value_json=encoded, updated_at=now)
            s.add(row)
        else:
            row.value_json = encoded
            row.updated_at = now
        s.commit()
    except Exception:
        s.rollback()
        logger.warning("stars payment dedupe marker failed key=%s tg_id=%s", key, tg_id)
    finally:
        s.close()

# Achievement definitions: id -> {name, description, reward_days, condition}
ACHIEVEMENTS = {
    "first_sub": {
        "name": "🟢 Inception",
        "desc": "Первая активация защищенного канала",
        "days": 0,
        "icon": "🟢"
    },
    "week_active": {
        "name": "🛡 Sentinel",
        "desc": "7 дней непрерывной защиты",
        "days": 1,
        "icon": "🛡"
    },
    "referral_1": {
        "name": "🤝 Uplink",
        "desc": "Подключен 1 новый узел (друг)",
        "days": 3,
        "icon": "🤝"
    },
    "referral_5": {
        "name": "🕸 Networker",
        "desc": "Создана сеть из 5 узлов",
        "days": 7,
        "icon": "🕸"
    },
    "streak_3": {
        "name": "🔥 Phantom",
        "desc": "3 месяца в тени (Streak)",
        "days": 0,  # Already awarded in streak system
        "icon": "🔥"
    },
    "big_spender": {
        "name": "💎 Investor",
        "desc": "Вклад в инфраструктуру (500+ Stars)",
        "days": 10,
        "icon": "💎"
    },
    "jackpot": {
        "name": "🎰 Lucky Glitch",
        "desc": "Сбой матрицы: Джекпот (30 дней)!",
        "days": 0,
        "icon": "🎰"
    },
    "loyal_year": {
        "name": "👑 Architect",
        "desc": "Год в системе PORTAL",
        "days": 30,
        "icon": "👑"
    },
}

# Tariff definitions (Stars).
TARIFFS = {
    "trial": {
        # Free tier: enforced by subscription JSON allowlist rules (see api.py).
        "name": "🆓 Бесплатный (соцсети + AI)",
        "stars": 0,
        # Long expiry so users can keep the profile without re-issuing.
        "days": 3650,
        "gb": FREE_TOTAL_GB,
        "subId": "FREE",
        "sub_type": "FREE"
    },
    "1_month": {
        "name": "📅 1 Месяц",
        "stars": 249,
        "days": 30,
        "gb": 0,
        "subId": "MONTHLY",
        "sub_type": "PAID"
    },
    "3_months": {
        "name": "📅 3 Месяца",
        "stars": 699,
        "days": 91,
        "gb": 0,
        "subId": "QUARTERLY",
        "sub_type": "PAID"
    },
    "6_months": {
        "name": "📅 6 Месяцев",
        "stars": 1199,
        "days": 182,
        "gb": 0,
        "subId": "HALF_YEAR",
        "sub_type": "PAID"
    },
    "9_months": {
        "name": "📅 9 Месяцев",
        "stars": 1399,
        "days": 273,
        "gb": 0,
        "subId": "NINE_MONTHS",
        "sub_type": "PAID"
    },
    "12_months": {
        "name": "📅 1 Год",
        "stars": 1499,
        "days": 365,
        "gb": 0,
        "subId": "YEARLY",
        "sub_type": "PAID"
    }
}

# Backward compatibility: older code used different tariff keys.
TARIFF_KEY_ALIASES = {
    "month_1": "1_month",
    "month_3": "3_months",
    "month_6": "6_months",
    "month_9": "9_months",
    "year_1": "12_months",
}


def normalize_tariff_key(key: str) -> str:
    return TARIFF_KEY_ALIASES.get(key, key)


REFERRAL_BONUS_DAYS = int(os.getenv("REFERRAL_BONUS_DAYS", "15"))

# Gift card types: {key: {name, stars, days}}
GIFT_CARD_TYPES = {
    "mini": {
        "name": "🎁 Mini (7 Дней)",
        "stars": 59,
        "days": 7
    },
    "standard": {
        "name": "🎁 Standard (30 Дней)",
        "stars": 249,
        "days": 30
    },
    "premium": {
        "name": "🎁 Premium (90 Дней)",
        "stars": 699,
        "days": 90
    },
}

def get_user(tg_id: int) -> Optional[User]:
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    session.close()
    return user


def active_family_slots(tg_id: int) -> int:
    session = Session()
    try:
        now = _utcnow()
        total = (
            session.query(func.coalesce(func.sum(FamilySlot.slots), 0))
            .filter(FamilySlot.tg_id == int(tg_id))
            .filter((FamilySlot.expires_at.is_(None)) | (FamilySlot.expires_at > now))
            .scalar()
            or 0
        )
        return int(total)
    finally:
        session.close()


def add_family_slot_pack(tg_id: int, *, slots: int = 1, days: int = FAMILY_SLOT_DAYS) -> tuple[bool, int]:
    session = Session()
    try:
        now = _utcnow()
        current = (
            session.query(func.coalesce(func.sum(FamilySlot.slots), 0))
            .filter(FamilySlot.tg_id == int(tg_id))
            .filter((FamilySlot.expires_at.is_(None)) | (FamilySlot.expires_at > now))
            .scalar()
            or 0
        )
        if int(current) >= int(FAMILY_SLOT_MAX):
            return False, int(current)
        add_slots = min(int(slots), int(FAMILY_SLOT_MAX) - int(current))
        row = FamilySlot(
            tg_id=int(tg_id),
            slots=max(1, int(add_slots)),
            expires_at=now + timedelta(days=max(1, int(days))),
            created_at=now,
        )
        session.add(row)
        session.commit()
        return True, int(current) + int(add_slots)
    except Exception:
        session.rollback()
        return False, 0
    finally:
        session.close()


def can_reset_devices(tg_id: int, *, cooldown_hours: int = 24) -> tuple[bool, int]:
    session = Session()
    try:
        user = session.query(User).filter_by(tg_id=int(tg_id)).first()
        if not user:
            return False, 0
        now = _utcnow()
        last_reset = _naive_utc(getattr(user, "device_reset_last_at", None))
        if not last_reset:
            return True, 0
        next_allowed = last_reset + timedelta(hours=max(1, int(cooldown_hours)))
        if now >= next_allowed:
            return True, 0
        remain = int((next_allowed - now).total_seconds())
        return False, max(0, remain)
    finally:
        session.close()


def mark_devices_reset(tg_id: int) -> bool:
    session = Session()
    try:
        user = session.query(User).filter_by(tg_id=int(tg_id)).first()
        if not user:
            return False
        user.device_reset_last_at = _utcnow()
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


def create_user(tg_id: int, user_uuid: str, email: str, sub_type: str, days: int, gb: int, stars: int, username: str = None) -> User:
    session = Session()
    # Check if exists
    existing = session.query(User).filter_by(tg_id=tg_id).first()
    if existing:
        # Update ALL relevant fields (fix for PENDING users from TOS acceptance)
        existing.expiry_at = _utcnow() + timedelta(days=days)
        existing.is_active = True
        existing.stars_paid += stars
        existing.sub_type = sub_type  # Update from PENDING to actual tariff
        existing.total_gb = gb
        existing.uuid = user_uuid
        existing.email = email
        if username:
            existing.username = username
        if _is_freemium_sub_type(sub_type):
            mark_user_became_free(existing)
        # Generate sub_token if not exists
        if not existing.sub_token:
            existing.sub_token = generate_sub_token()
        session.commit()
        session.close()
        return existing
    
    # Generate unique subscription token for new user
    sub_token = generate_sub_token()
    
    user = User(
        tg_id=tg_id,
        username=username,
        uuid=user_uuid,
        email=email,
        sub_type=sub_type,
        expiry_at=_utcnow() + timedelta(days=days),
        is_active=True,
        stars_paid=stars,
        total_gb=gb,
        trial_used=(sub_type == "TRIAL_10GB_7"),
        sub_token=sub_token
    )
    if _is_freemium_sub_type(sub_type):
        mark_user_became_free(user)
    session.add(user)
    session.commit()
    session.close()
    return user

def update_user_username(tg_id: int, username: str):
    """Update user's telegram username"""
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    if user and username:
        user.username = username
        session.commit()
    session.close()

def generate_sub_token() -> str:
    """Generate unique subscription token (43 chars, impossible to guess)"""
    return secrets.token_urlsafe(32)

def generate_referral_code() -> str:
    """Generate unique 8-char referral code like SWAZ7K3F"""
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "SWAZ" + ''.join(random.choices(chars, k=4))
        session = Session()
        exists = session.query(User).filter_by(referral_code=code).first()
        session.close()
        if not exists:
            return code

def get_or_create_referral_code(tg_id: int) -> str:
    """Get user's referral code or create one if doesn't exist"""
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    if user:
        if not user.referral_code:
            user.referral_code = generate_referral_code()
            session.commit()
        code = user.referral_code
        session.close()
        return code
    session.close()
    return None

def get_user_by_referral_code(code: str) -> Optional[int]:
    """Find user tg_id by their referral code"""
    session = Session()
    user = session.query(User).filter_by(referral_code=code.upper()).first()
    tg_id = user.tg_id if user else None
    session.close()
    return tg_id

def set_referrer(tg_id: int, referrer_id: int) -> bool:
    """Set referrer for a user (only if not already set)"""
    if tg_id == referrer_id:
        return False  # Can't refer yourself
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    referrer = session.query(User).filter_by(tg_id=referrer_id).first()
    if user and not user.referrer_id and referrer:
        user.referrer_id = referrer_id
        session.commit()
        session.close()
        return True
    session.close()
    return False

def set_referrer_by_code(tg_id: int, referral_code: str) -> bool:
    """Link user to their referrer by referral code"""
    referrer_id = get_user_by_referral_code(referral_code)
    if not referrer_id or referrer_id == tg_id:
        return False
    return set_referrer(tg_id, referrer_id)

async def award_referral_bonus(referrer_id: int, bonus_days: int = REFERRAL_BONUS_DAYS) -> bool:
    """Award bonus days to referrer for each paid purchase by referred user."""
    session = Session()
    referrer = session.query(User).filter_by(tg_id=referrer_id).first()
    if referrer:
        # Referral rewards are available only for active paid users.
        if not _is_paid_active_user(referrer):
            session.close()
            return False

        referrer.referral_count = (referrer.referral_count or 0) + 1
        
        # Award Days
        expiry = _naive_utc(referrer.expiry_at)
        now = _utcnow()
        if expiry and expiry > now:
            referrer.expiry_at = expiry + timedelta(days=bonus_days)
        else:
            referrer.expiry_at = now + timedelta(days=bonus_days)
        
        referrer.is_active = True
        
        session.commit()
        session.close()
        
        # Ensure enabled in panel
        try:
            # We need to get UUID. extend_user isn't async/doesn't do panel.
            # So we do it manually via panel API instance if available
            # We assume 'panel' global exists if this is called from bot execution context
            # But this is a helper function. We should import panel or use get_user to find UUID.
            pass # We rely on periodic checks or user interaction to re-enable
            # Or better:
            ref_user = get_user(referrer_id)
            if ref_user:
                 await panel.enable_client(ref_user.uuid, True)
        except:
            pass
            
        return True
    session.close()
    return False

def get_referral_stats(tg_id: int) -> dict:
    """Get referral stats for a user"""
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    if user:
        count = user.referral_count or 0
        if not user.referral_code:
            user.referral_code = generate_referral_code()
            session.commit()
        code = user.referral_code
        session.close()
        return {"count": count, "bonus_earned": count * REFERRAL_BONUS_DAYS, "code": code}
    session.close()
    return {"count": 0, "bonus_earned": 0, "code": None}

def has_referral_discount(tg_id: int) -> bool:
    """Check if user is eligible for 20% referral discount"""
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    result = user and user.referrer_id and not user.first_purchase_done
    session.close()
    return result

def mark_first_purchase_done(tg_id: int):
    """Mark that user has used their 20% referral discount"""
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    if user:
        user.first_purchase_done = True
        session.commit()
    session.close()


def get_pending_discount_pct(tg_id: int) -> int:
    session = Session()
    try:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            return 0
        return max(0, min(95, int(getattr(user, "pending_discount_pct", 0) or 0)))
    finally:
        session.close()


def clear_pending_discount(tg_id: int) -> None:
    session = Session()
    try:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            return
        user.pending_discount_pct = None
        user.pending_discount_code = None
        user.pending_discount_set_at = None
        session.commit()
    finally:
        session.close()

def check_tos_accepted(tg_id: int) -> bool:
    """Check if user has accepted Terms of Service"""
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    result = user.tos_accepted if user else False
    session.close()
    return result

def set_tos_accepted(tg_id: int) -> bool:
    """Mark user as having accepted Terms of Service"""
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    if not user:
        # Create a placeholder user entry
        user = User(
            tg_id=tg_id,
            uuid=str(uuid.uuid4()),
            email=f"user_{tg_id}",
            sub_type="PENDING",
            is_active=False,
            tos_accepted=True
        )
        session.add(user)
    else:
        user.tos_accepted = True
    session.commit()
    session.close()
    return True


def _tos_offer_text() -> str:
    return (
        "📜 *Публичная оферта*\n\n"
        "Перед использованием сервиса ознакомьтесь с условиями:\n\n"
        "• Сервис предоставляется «как есть»\n"
        "• Пользователь сам несёт ответственность за соблюдение законов\n"
        "• Запрещено использование для противоправных действий\n"
        "• Возврат средств при блокировках не гарантируется\n\n"
        "_Нажимая «Принимаю условия», вы соглашаетесь с полным текстом оферты._"
    )


def _tos_offer_keyboard(*, back_callback: str = "back") -> InlineKeyboardMarkup:
    offer_url = f"https://{(PUBLIC_WEB_DOMAIN or HOST_DOMAIN).strip().strip('/')}/offer"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📄 Читать полностью", url=offer_url)],
            [InlineKeyboardButton(text="✅ Принимаю условия", callback_data="accept_tos")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)],
        ]
    )


def ensure_pending_user(tg_id: int, username: str | None = None) -> tuple[User, bool]:
    """
    Ensure a DB row exists for first-touch flows (/start, referrals, mode selection).
    Returns (user, created).
    """
    session = Session()
    try:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        if user:
            if username and not user.username:
                user.username = username
                session.commit()
            return user, False

        user = User(
            tg_id=tg_id,
            username=username,
            uuid=str(uuid.uuid4()),
            email=f"user_{tg_id}",
            sub_type="PENDING",
            is_active=False,
            tos_accepted=False,
            trial_used=False,
            sub_token=generate_sub_token(),
        )
        session.add(user)
        session.commit()
        return user, True
    finally:
        session.close()


def _campaign_claimed(*, tg_id: int, campaign_key: str) -> bool:
    session = Session()
    try:
        row = (
            session.query(CampaignSend.id)
            .filter(CampaignSend.tg_id == int(tg_id), CampaignSend.campaign_key == str(campaign_key))
            .first()
        )
        return bool(row)
    finally:
        session.close()


def _mark_campaign_claim_once(*, tg_id: int, campaign_key: str) -> bool:
    session = Session()
    try:
        exists = (
            session.query(CampaignSend.id)
            .filter(CampaignSend.tg_id == int(tg_id), CampaignSend.campaign_key == str(campaign_key))
            .first()
        )
        if exists:
            return False
        session.add(CampaignSend(tg_id=int(tg_id), campaign_key=str(campaign_key), sent_at=_utcnow()))
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


def _campaign_segment_match(*, user: User, segment: str) -> bool:
    seg = str(segment or "all_active").strip().lower()
    if seg in {"all", "all_active"}:
        return bool(user.is_active)
    if seg == "paid":
        return str(user.sub_type or "").upper() == "PAID"
    if seg == "free":
        return str(user.sub_type or "").upper() == "FREE"
    if seg == "manual":
        return bool(getattr(user, "is_manual", False) or int(user.tg_id) < 0 or str(user.sub_type or "").upper() == "MANUAL")
    return True


def _campaign_lookup(*, session, campaign_type: str, target_value: str, user: User, now: datetime | None = None) -> IncentiveCampaign | None:
    now_dt = now or _utcnow()
    ctype = str(campaign_type or "").strip().lower()
    target = str(target_value or "").strip().upper()
    if ctype not in {"promo", "gift"} or not target:
        return None
    rows = (
        session.query(IncentiveCampaign)
        .filter(func.lower(IncentiveCampaign.campaign_type) == ctype)
        .filter(func.upper(IncentiveCampaign.target_value) == target)
        .filter(IncentiveCampaign.is_active == True)
        .order_by(IncentiveCampaign.id.desc())
        .all()
    )
    for row in rows:
        if row.starts_at and row.starts_at > now_dt:
            continue
        if row.ends_at and row.ends_at < now_dt:
            if bool(row.auto_disable):
                row.is_active = False
            continue
        if int(row.max_activations or -1) >= 0 and int(row.activations_count or 0) >= int(row.max_activations or -1):
            if bool(row.auto_disable):
                row.is_active = False
            continue
        if not _campaign_segment_match(user=user, segment=str(row.segment or "all_active")):
            continue
        return row
    return None


def _campaign_consume(*, row: IncentiveCampaign | None) -> None:
    if not row:
        return
    row.activations_count = int(row.activations_count or 0) + 1
    if bool(row.auto_disable) and int(row.max_activations or -1) >= 0 and int(row.activations_count or 0) >= int(row.max_activations or -1):
        row.is_active = False
    row.updated_at = _utcnow()


async def _try_activate_opening_premium_bonus(
    *,
    message: Message,
    bot: Bot,
    tg_id: int,
    username: str | None,
) -> tuple[bool, str]:
    if not OPENING_PREMIUM_ENABLED or not OPENING_PREMIUM_START_CODE:
        return False, "disabled"
    if not check_tos_accepted(tg_id):
        return False, "tos_required"

    user = get_user(tg_id)
    if not user:
        ensure_pending_user(tg_id, username=username)
        user = get_user(tg_id)
    if username:
        update_user_username(tg_id, username)

    plan = _normalize_sub_type(user.sub_type if user else "")
    now = _utcnow()
    expiry = _naive_utc(user.expiry_at) if user else None
    is_active_paid = bool(user and user.is_active and plan == "PAID" and expiry and expiry > now)
    if is_active_paid:
        return False, "already_paid_active"

    if _campaign_claimed(tg_id=tg_id, campaign_key=OPENING_PREMIUM_CAMPAIGN_KEY):
        return False, "already_claimed"

    promo_tariff = {
        "name": f"🎁 Бонус запуска ({OPENING_PREMIUM_DAYS} дней)",
        "stars": 0,
        "days": int(OPENING_PREMIUM_DAYS),
        "gb": 0,
        "subId": "LAUNCH_BONUS",
        "sub_type": "BONUS",
    }
    await create_subscription(message, tg_id, promo_tariff, bot)

    session = Session()
    try:
        db_user = session.query(User).filter_by(tg_id=int(tg_id)).first()
        if db_user:
            # Opening bonus must not reserve the channel-bonus claim flag.
            db_user.channel_bonus_active = False
            db_user.channel_bonus_expires_at = None
            db_user.channel_bonus_revoked_at = None
            session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()

    if not _mark_campaign_claim_once(tg_id=tg_id, campaign_key=OPENING_PREMIUM_CAMPAIGN_KEY):
        logger.warning(
            "opening bonus activated without campaign mark tg_id=%s campaign_key=%s",
            int(tg_id),
            OPENING_PREMIUM_CAMPAIGN_KEY,
        )

    track_event(
        tg_id=int(tg_id),
        event_name="promo_opening_activated",
        source="bot",
        meta={
            "campaign_key": OPENING_PREMIUM_CAMPAIGN_KEY,
            "days": int(OPENING_PREMIUM_DAYS),
        },
    )
    return True, "activated"


async def _try_activate_friend_gift_bonus(
    *,
    message: Message,
    bot: Bot,
    tg_id: int,
    username: str | None,
    referral_code: str,
) -> tuple[bool, str]:
    if not FRIEND_GIFT_ENABLED:
        return False, "disabled"
    if not check_tos_accepted(tg_id):
        return False, "tos_required"

    ref_code = (referral_code or "").strip().upper()[:10]
    inviter_tg_id = get_user_by_referral_code(ref_code) if ref_code else None
    if not inviter_tg_id or int(inviter_tg_id) == int(tg_id):
        return False, "invalid_ref"

    user = get_user(tg_id)
    if not user:
        ensure_pending_user(tg_id, username=username)
        user = get_user(tg_id)
    if username:
        update_user_username(tg_id, username)

    if _is_paid_active_user(user):
        return False, "already_paid_active"
    if _campaign_claimed(tg_id=tg_id, campaign_key=FRIEND_GIFT_CAMPAIGN_KEY):
        return False, "already_claimed"

    promo_tariff = {
        "name": f"🎁 Подарок от друга ({FRIEND_GIFT_DAYS} дня)",
        "stars": 0,
        "days": int(FRIEND_GIFT_DAYS),
        "gb": 0,
        "subId": "FRIEND_GIFT",
        "sub_type": "BONUS",
    }
    await create_subscription(message, tg_id, promo_tariff, bot)
    set_referrer_by_code(tg_id, ref_code)
    if not _mark_campaign_claim_once(tg_id=tg_id, campaign_key=FRIEND_GIFT_CAMPAIGN_KEY):
        logger.warning(
            "friend gift activated without campaign mark tg_id=%s campaign_key=%s",
            int(tg_id),
            FRIEND_GIFT_CAMPAIGN_KEY,
        )

    track_event(
        tg_id=int(tg_id),
        event_name="promo_friend_gift_activated",
        source="bot",
        meta={
            "campaign_key": FRIEND_GIFT_CAMPAIGN_KEY,
            "referral_code": ref_code,
            "days": int(FRIEND_GIFT_DAYS),
        },
    )
    return True, "activated"


def _channel_name_for_url() -> str:
    channel = (NEWS_CHANNEL_ID or "@portal_privacy").strip().lstrip("@")
    return channel or "portal_privacy"


def _checkout_ticket_for_user(
    *,
    tg_id: int,
    plan_code: str | None = None,
    promo_code: str | None = None,
    campaign_key: str | None = None,
    source: str = "bot",
) -> str:
    if not CHECKOUT_TICKET_SECRET:
        return ""
    now_ts = int(datetime.utcnow().timestamp())
    payload = {
        "tg_id": int(tg_id),
        "plan_code": (plan_code or "").strip().lower()[:32],
        "promo_code": (promo_code or "").strip().upper()[:20],
        "campaign_key": (campaign_key or "").strip()[:64],
        "source": (source or "bot").strip().lower()[:16],
        "iat": now_ts,
        "exp": now_ts + int(CHECKOUT_TICKET_TTL_SECONDS),
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(CHECKOUT_TICKET_SECRET.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return f"{token}.{sig}"


def _bot_checkout_url(
    tg_id: int,
    *,
    plan_code: str | None = None,
    promo_code: str | None = None,
    campaign_key: str | None = None,
) -> str:
    base = (PAY_CHECKOUT_URL or "").strip() or f"https://{(PUBLIC_WEB_DOMAIN or HOST_DOMAIN)}/checkout/"
    parsed = urlsplit(base)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["source"] = "bot"
    query["tg_id"] = str(int(tg_id))
    if plan_code:
        query["plan"] = str(plan_code).strip().lower()
    if promo_code:
        query["promo"] = str(promo_code).strip().upper()
    if campaign_key:
        query["campaign"] = str(campaign_key).strip()[:64]
    ticket = _checkout_ticket_for_user(
        tg_id=int(tg_id),
        plan_code=plan_code,
        promo_code=promo_code,
        campaign_key=campaign_key,
        source="bot",
    )
    if ticket:
        query["checkout_ticket"] = ticket
    built_query = urlencode(query)
    # Keep relative path if PAY_CHECKOUT_URL is relative.
    if parsed.scheme and parsed.netloc:
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/checkout/", built_query, parsed.fragment))
    return urlunsplit(("", "", parsed.path or "/checkout/", built_query, parsed.fragment))


def _web_login_url_with_token(token: str) -> str:
    base = (WEBAPP_URL or "").strip() or f"https://{(PUBLIC_WEB_DOMAIN or HOST_DOMAIN)}/webapp/"
    parsed = urlsplit(base)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["web_session_token"] = str(token or "").strip()
    built_query = urlencode(query)
    if parsed.scheme and parsed.netloc:
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/webapp/", built_query, parsed.fragment))
    return urlunsplit(("", "", parsed.path or "/webapp/", built_query, parsed.fragment))


_START_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _sanitize_start_token(raw: str | None, *, max_len: int, uppercase: bool = False) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    clean = re.sub(r"[^A-Za-z0-9_-]+", "", value)[: max(1, int(max_len))]
    if not clean:
        return ""
    clean = clean.upper() if uppercase else clean
    if not _START_TOKEN_RE.fullmatch(clean):
        return ""
    return clean


def _parse_start_deeplink_context(start_arg: str) -> tuple[str, str]:
    raw = (start_arg or "").strip()
    if not raw:
        return "", ""
    lowered = raw.lower()
    promo_code = ""
    campaign_key = ""

    if lowered.startswith("promo_") and len(raw) > len("promo_"):
        promo_code = _sanitize_start_token(raw[len("promo_"):], max_len=20, uppercase=True)
    elif lowered.startswith("campaign_") and len(raw) > len("campaign_"):
        campaign_raw = raw[len("campaign_"):].strip()
        # Supported format: campaign_<KEY>__promo_<CODE>
        marker = "__promo_"
        if marker in campaign_raw.lower():
            idx = campaign_raw.lower().find(marker)
            promo_code = _sanitize_start_token(campaign_raw[idx + len(marker):], max_len=20, uppercase=True)
            campaign_key = _sanitize_start_token(campaign_raw[:idx], max_len=64, uppercase=False)
        else:
            campaign_key = _sanitize_start_token(campaign_raw, max_len=64, uppercase=False)

    return promo_code, campaign_key


def _resolve_start_link_action(start_arg: str) -> dict[str, str | bool]:
    raw = (start_arg or "").strip().lower()
    if not raw:
        return {"promo_code": "", "campaign_key": "", "opening_bonus": False}
    session = Session()
    try:
        row = (
            session.query(StartLink)
            .filter(func.lower(StartLink.code) == raw)
            .filter(StartLink.is_active == True)
            .first()
        )
    finally:
        session.close()
    if not row:
        return {"promo_code": "", "campaign_key": "", "opening_bonus": False}

    action = str(getattr(row, "target_action", "") or "").strip()
    lowered = action.lower()
    if lowered == "opening_bonus":
        return {"promo_code": "", "campaign_key": "", "opening_bonus": True}
    if lowered.startswith("promo:"):
        promo = _sanitize_start_token(action.split(":", 1)[1], max_len=20, uppercase=True)
        return {"promo_code": promo, "campaign_key": "", "opening_bonus": False}
    if lowered.startswith("campaign:"):
        campaign = _sanitize_start_token(action.split(":", 1)[1], max_len=64, uppercase=False)
        return {"promo_code": "", "campaign_key": campaign, "opening_bonus": False}
    if lowered.startswith("campaign_promo:"):
        rest = action.split(":", 1)[1].strip()
        parts = rest.split(":", 1)
        campaign = _sanitize_start_token(parts[0] if parts else "", max_len=64, uppercase=False)
        promo = _sanitize_start_token(parts[1] if len(parts) > 1 else "", max_len=20, uppercase=True)
        return {"promo_code": promo, "campaign_key": campaign, "opening_bonus": False}
    return {"promo_code": "", "campaign_key": "", "opening_bonus": False}


def _parse_friend_gift_ref_code(start_arg: str) -> str:
    raw = (start_arg or "").strip()
    if not raw:
        return ""
    lowered = raw.lower()
    marker = "gift3_"
    if not lowered.startswith(marker):
        return ""
    code = raw[len(marker):].strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{6,10}", code):
        return ""
    return code[:10]


def _channel_bonus_ineligible_reason(*, tg_id: int, user: User | None) -> str | None:
    if user and _normalize_sub_type(user.sub_type) == "MANUAL":
        return "Для ручных аккаунтов бонус за канал отключён."
    if user and getattr(user, "channel_bonus_claimed_at", None):
        return "Бонус за канал уже был активирован для этого аккаунта."
    if _campaign_claimed(tg_id=tg_id, campaign_key=OPENING_PREMIUM_CAMPAIGN_KEY):
        return "Для этого аккаунта уже активирован промо-бонус по ссылке."
    if _is_paid_active_user(user):
        return "У вас уже активен премиум-доступ."
    return None


def _channel_bonus_eligible(*, tg_id: int, user: User | None) -> bool:
    return _channel_bonus_ineligible_reason(tg_id=tg_id, user=user) is None


def _channel_bonus_keyboard(next_action: str) -> InlineKeyboardMarkup:
    channel_name = _channel_name_for_url()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться на канал", url=f"https://t.me/{channel_name}")],
            [InlineKeyboardButton(text=f"✅ Проверить и получить {CHANNEL_PREMIUM_DAYS} дней", callback_data=f"bonus_claim_{next_action}")],
            [InlineKeyboardButton(text="➡️ Продолжить без бонуса", callback_data=f"bonus_skip_{next_action}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
        ]
    )


def _channel_bonus_offer_text() -> str:
    channel_name = _channel_name_for_url()
    channel_url = f"https://t.me/{channel_name}"
    return (
        "🎁 *Бонус за подписку на канал*\n\n"
        f"Подпишитесь на [КАНАЛ]({channel_url}) и получите *{CHANNEL_PREMIUM_DAYS} дней премиум-доступа*.\n"
        "После подписки нажмите «Проверить и получить».\n\n"
        "Если бонус не нужен, можно продолжить в бесплатном режиме."
    )


async def _show_channel_bonus_offer(callback: CallbackQuery, *, next_action: str) -> None:
    track_event(
        tg_id=int(callback.from_user.id),
        event_name="offer_channel_bonus_shown",
        source="bot",
        meta={"next_action": next_action, "days": int(CHANNEL_PREMIUM_DAYS)},
    )
    await callback.message.edit_text(
        _channel_bonus_offer_text(),
        reply_markup=_channel_bonus_keyboard(next_action),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


async def _activate_channel_bonus(
    *,
    message: Message,
    bot: Bot,
    tg_id: int,
) -> tuple[bool, str]:
    if not check_tos_accepted(tg_id):
        return False, "tos_required"

    user = get_user(tg_id)
    if not _channel_bonus_eligible(tg_id=tg_id, user=user):
        return False, "not_eligible"

    if not await check_subscription(tg_id, bot):
        return False, "not_subscribed"

    bonus_tariff = {
        "name": f"🎁 Бонус за канал ({CHANNEL_PREMIUM_DAYS} дней)",
        "stars": 0,
        "days": int(CHANNEL_PREMIUM_DAYS),
        "gb": 0,
        "subId": "CHANNEL_BONUS",
        "sub_type": "BONUS",
    }
    await create_subscription(message, tg_id, bonus_tariff, bot)

    now = _utcnow()
    session = Session()
    try:
        db_user = session.query(User).filter_by(tg_id=int(tg_id)).first()
        if not db_user:
            return False, "user_not_found"
        db_user.channel_bonus_claimed_at = db_user.channel_bonus_claimed_at or now
        db_user.channel_bonus_active = True
        db_user.channel_bonus_expires_at = db_user.expiry_at
        db_user.channel_bonus_revoked_at = None
        session.commit()
    except Exception:
        session.rollback()
        return False, "db_error"
    finally:
        session.close()

    track_event(
        tg_id=int(tg_id),
        event_name="promo_channel_activated",
        source="bot",
        meta={"days": int(CHANNEL_PREMIUM_DAYS), "channel": f"@{_channel_name_for_url()}"},
    )
    return True, "activated"


# ==========================================
#         WHEEL OF FORTUNE
# ==========================================

WHEEL_DEFAULT_PRIZES: list[tuple[int, int]] = [
    (1, 45),
    (3, 35),
    (7, 15),
    (30, 5),
]
WHEEL_PRESETS: dict[str, list[tuple[int, int]]] = {
    "balanced": WHEEL_DEFAULT_PRIZES,
    "steady": [(1, 55), (3, 30), (7, 12), (30, 3)],
    "generous": [(1, 35), (3, 35), (7, 20), (30, 10)],
}
WHEEL_DEFAULT_COOLDOWN_HOURS = 168


def _normalize_wheel_weights(rows: list[tuple[int, int]] | None) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    seen: set[int] = set()
    for days, weight in (rows or []):
        d = int(days or 0)
        w = int(weight or 0)
        if d <= 0 or w <= 0:
            continue
        if d in seen:
            continue
        seen.add(d)
        out.append((d, w))
    return out or list(WHEEL_DEFAULT_PRIZES)


def _cooldown_days_from_hours(hours: int) -> int:
    val = max(1, int(hours))
    return max(1, min(90, int((val + 23) // 24)))


def _load_wheel_config() -> dict:
    s = Session()
    try:
        row = s.query(AppSetting).filter(AppSetting.key == "wheel_config").first()
    finally:
        s.close()
    if not row or not str(getattr(row, "value_json", "") or "").strip():
        return {
            "preset": "balanced",
            "weights": list(WHEEL_DEFAULT_PRIZES),
            "cooldown_hours": int(WHEEL_DEFAULT_COOLDOWN_HOURS),
            "cooldown_days": int(_cooldown_days_from_hours(WHEEL_DEFAULT_COOLDOWN_HOURS)),
        }
    try:
        payload = json.loads(str(row.value_json))
    except Exception:
        payload = {}
    preset = str(payload.get("preset") or "balanced").strip().lower()
    weights_raw = payload.get("weights") or []
    if isinstance(weights_raw, list):
        weights = _normalize_wheel_weights(
            [
                (int((x or {}).get("days") or 0), int((x or {}).get("weight") or 0))
                for x in weights_raw
            ]
        )
    else:
        weights = list(WHEEL_DEFAULT_PRIZES)
    cooldown_hours = int(payload.get("cooldown_hours") or WHEEL_DEFAULT_COOLDOWN_HOURS)
    cooldown_hours = max(1, min(24 * 90, cooldown_hours))
    cooldown_days = _cooldown_days_from_hours(cooldown_hours)
    return {
        "preset": preset or "manual",
        "weights": weights,
        "cooldown_hours": cooldown_hours,
        "cooldown_days": cooldown_days,
    }


def _save_wheel_config(
    *,
    weights: list[tuple[int, int]] | None = None,
    cooldown_days: int | None = None,
    cooldown_hours: int | None = None,
    preset: str | None = None,
) -> dict:
    current = _load_wheel_config()
    next_weights = _normalize_wheel_weights(weights if weights is not None else current.get("weights"))
    next_preset = str(preset or current.get("preset") or "manual").strip().lower()[:32] or "manual"
    if cooldown_hours is not None:
        next_cooldown_hours = int(cooldown_hours)
    elif cooldown_days is not None:
        next_cooldown_hours = int(cooldown_days) * 24
    else:
        next_cooldown_hours = int(current.get("cooldown_hours") or WHEEL_DEFAULT_COOLDOWN_HOURS)
    next_cooldown_hours = max(1, min(24 * 90, next_cooldown_hours))
    payload = {
        "preset": next_preset,
        "weights": [{"days": int(d), "weight": int(w)} for d, w in next_weights],
        "cooldown_hours": int(next_cooldown_hours),
    }
    s = Session()
    try:
        row = s.query(AppSetting).filter(AppSetting.key == "wheel_config").first()
        now = _utcnow()
        if not row:
            row = AppSetting(
                key="wheel_config",
                value_json=json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
                updated_at=now,
            )
            s.add(row)
        else:
            row.value_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            row.updated_at = now
        s.commit()
    finally:
        s.close()
    return _load_wheel_config()


def _wheel_prizes() -> list[tuple[int, int]]:
    return list(_load_wheel_config().get("weights") or WHEEL_DEFAULT_PRIZES)


def _wheel_cooldown_hours() -> int:
    return int(_load_wheel_config().get("cooldown_hours") or WHEEL_DEFAULT_COOLDOWN_HOURS)


def _wheel_cooldown_days() -> int:
    cfg = _load_wheel_config()
    hours = int(cfg.get("cooldown_hours") or WHEEL_DEFAULT_COOLDOWN_HOURS)
    return _cooldown_days_from_hours(hours)


def wheel_prizes_for_user(user: User | None) -> list[tuple[int, int]]:
    # Weights are managed from admin panel.
    return _wheel_prizes()

def can_spin_wheel(tg_id: int) -> tuple[bool, int]:
    """Check if user can spin the wheel. Returns (can_spin, seconds_until_next)"""
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    session.close()
    
    if not user:
        return False, 0

    now = _utcnow()
    # Wheel is available only for active paid subscriptions.
    if not _is_paid_active_user(user):
        return False, 0
    
    last_spin = _naive_utc(user.last_wheel_spin)
    if not last_spin:
        return True, 0
    
    next_spin = last_spin + timedelta(hours=_wheel_cooldown_hours())
    
    if now >= next_spin:
        return True, 0
    
    seconds_left = int((next_spin - now).total_seconds())
    return False, seconds_left

def spin_wheel(tg_id: int) -> int | None:
    """Spin the wheel and award days. Returns prize days, or None if can't spin"""
    import random

    session = Session()
    try:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        if not user or not _is_paid_active_user(user):
            return None

        now = _utcnow()
        last_spin = _naive_utc(user.last_wheel_spin)
        if last_spin:
            next_spin = last_spin + timedelta(hours=_wheel_cooldown_hours())
            if now < next_spin:
                return None

        prizes = wheel_prizes_for_user(user)
        total_weight = sum(w for _, w in prizes)
        r = random.randint(1, total_weight)

        cumulative = 0
        prize_days = 1
        for days, weight in prizes:
            cumulative += weight
            if r <= cumulative:
                prize_days = days
                break

        expiry = _naive_utc(user.expiry_at)
        if expiry and expiry > now:
            next_expiry = expiry + timedelta(days=prize_days)
        else:
            next_expiry = now + timedelta(days=prize_days)

        guard = session.query(User).filter(User.tg_id == int(tg_id))
        if last_spin is None:
            guard = guard.filter(User.last_wheel_spin.is_(None))
        else:
            guard = guard.filter(User.last_wheel_spin == last_spin)

        updated = guard.update(
            {
                User.last_wheel_spin: now,
                User.expiry_at: next_expiry,
                User.is_active: True,
            },
            synchronize_session=False,
        )
        if int(updated or 0) != 1:
            session.rollback()
            return None

        session.commit()
        return prize_days
    finally:
        session.close()

# ==========================================
#           STREAK SYSTEM
# ==========================================

# Streak milestone rewards: {months: bonus_days}
STREAK_REWARDS = {
    3: 3,     # 3 months = +3 Days
    6: 7,     # 6 months = +7 Days
    12: 30,   # 12 months = +30 Days
}

def get_streak_info(tg_id: int) -> dict:
    """Get user's streak info"""
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    session.close()
    
    if not user:
        # First milestone is always 3 months.
        return {"months": 0, "next_milestone": 3, "bonus_days_next": STREAK_REWARDS.get(3, 0), "last_check": None}
    
    months = user.streak_months or 0
    
    # Find next milestone
    next_milestone = None
    bonus_days_next = 0
    for m, bonus_days in sorted(STREAK_REWARDS.items()):
        if months < m:
            next_milestone = m
            bonus_days_next = bonus_days
            break
    
    return {
        "months": months,
        "next_milestone": next_milestone,
        "bonus_days_next": bonus_days_next,
        "last_check": user.streak_last_check
    }

def update_streak(tg_id: int) -> tuple[int, int]:
    """
    Update streak on purchase/renewal.
    Returns (new_streak_months, bonus_days_awarded)
    """
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    
    if not user:
        session.close()
        return (0, 0)
    
    now = datetime.utcnow()
    old_streak = user.streak_months or 0
    
    # Check if streak should reset (subscription expired > 7 days ago)
    if user.expiry_at:
        days_expired = (now - user.expiry_at).days
        if days_expired > 7:
            # Reset streak
            user.streak_months = 1
            user.streak_last_check = now
            session.commit()
            session.close()
            return (1, 0)
    
    # Check if we should increment (at least 25 days since last check)
    if user.streak_last_check:
        days_since_check = (now - user.streak_last_check).days
        if days_since_check < 25:
            # Too soon, don't increment
            session.close()
            return (old_streak, 0)
    
    # Increment streak
    new_streak = old_streak + 1
    user.streak_months = new_streak
    user.streak_last_check = now
    
    # Check for milestone bonus
    bonus_days = STREAK_REWARDS.get(new_streak, 0)
    if bonus_days > 0:
        if user.expiry_at and user.expiry_at > now:
            user.expiry_at += timedelta(days=bonus_days)
        else:
            user.expiry_at = now + timedelta(days=bonus_days)
    
    session.commit()
    session.close()
    
    return (new_streak, bonus_days)

# ==========================================
#         ACHIEVEMENTS SYSTEM
# ==========================================

def has_achievement(tg_id: int, achievement_id: str) -> bool:
    """Check if user has unlocked an achievement"""
    session = Session()
    exists = session.query(Achievement).filter_by(
        tg_id=tg_id, achievement_id=achievement_id
    ).first() is not None
    session.close()
    return exists

def award_achievement(tg_id: int, achievement_id: str) -> int:
    """Award achievement to user if not already earned. Returns bonus days or 0."""
    if has_achievement(tg_id, achievement_id):
        return 0
    
    ach = ACHIEVEMENTS.get(achievement_id)
    if not ach:
        return 0
    
    session = Session()
    new_ach = Achievement(tg_id=tg_id, achievement_id=achievement_id)
    session.add(new_ach)
    
    # Add bonus Days if any
    bonus_days = ach.get("days", 0)
    if bonus_days > 0:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        if user:
            if user.expiry_at and user.expiry_at > datetime.utcnow():
                user.expiry_at += timedelta(days=bonus_days)
            else:
                user.expiry_at = datetime.utcnow() + timedelta(days=bonus_days)
    
    session.commit()
    session.close()
    return bonus_days

def get_user_achievements(tg_id: int) -> list:
    """Get list of unlocked achievement IDs for user"""
    session = Session()
    achievements = session.query(Achievement).filter_by(tg_id=tg_id).all()
    result = [a.achievement_id for a in achievements]
    session.close()
    return result

async def check_achievements(tg_id: int, bot) -> list:
    """
    Check and award new achievements based on user's state.
    Returns list of newly awarded achievement IDs.
    """
    user = get_user(tg_id)
    if not user:
        return []
    if not _is_paid_active_user(user):
        return []
    
    awarded = []
    
    # first_sub: Has any subscription
    if user.is_active and not has_achievement(tg_id, "first_sub"):
        gb = award_achievement(tg_id, "first_sub")
        awarded.append("first_sub")
    
    # week_active: 7+ days since creation
    if user.created_at:
        days_active = (datetime.utcnow() - user.created_at).days
        if days_active >= 7 and not has_achievement(tg_id, "week_active"):
            gb = award_achievement(tg_id, "week_active")
            if gb > 0:
                try:
                    await panel.update_client_traffic(tg_id, gb)
                except:
                    pass
            awarded.append("week_active")
    
    # referral_1: Invited 1+ friends
    if (user.referral_count or 0) >= 1 and not has_achievement(tg_id, "referral_1"):
        gb = award_achievement(tg_id, "referral_1")
        if gb > 0:
            try:
                await panel.update_client_traffic(tg_id, gb)
            except:
                pass
        awarded.append("referral_1")
    
    # referral_5: Invited 5+ friends
    if (user.referral_count or 0) >= 5 and not has_achievement(tg_id, "referral_5"):
        gb = award_achievement(tg_id, "referral_5")
        if gb > 0:
            try:
                await panel.update_client_traffic(tg_id, gb)
            except:
                pass
        awarded.append("referral_5")
    
    # streak_3: 3+ months streak
    if (user.streak_months or 0) >= 3 and not has_achievement(tg_id, "streak_3"):
        award_achievement(tg_id, "streak_3")
        awarded.append("streak_3")
    
    # big_spender: 500+ stars paid
    if (user.stars_paid or 0) >= 500 and not has_achievement(tg_id, "big_spender"):
        gb = award_achievement(tg_id, "big_spender")
        if gb > 0:
            try:
                await panel.update_client_traffic(tg_id, gb)
            except:
                pass
        awarded.append("big_spender")
    
    # loyal_year: 1 year since creation
    if user.created_at:
        days_active = (datetime.utcnow() - user.created_at).days
        if days_active >= 365 and not has_achievement(tg_id, "loyal_year"):
            gb = award_achievement(tg_id, "loyal_year")
            if gb > 0:
                try:
                    await panel.update_client_traffic(tg_id, gb)
                except:
                    pass
            awarded.append("loyal_year")
    
    # Notify user about new achievements
    for ach_id in awarded:
        ach = ACHIEVEMENTS.get(ach_id)
        if ach:
            try:
                bonus_days = int(ach.get("days", 0) or 0)
                bonus_text = f"\n🎁 Бонус: *+{bonus_days} дн.*" if bonus_days > 0 else ""
                await bot.send_message(
                    tg_id,
                    f"🏆 *Новое достижение!*\n\n"
                    f"{ach['icon']} *{ach['name']}*\n"
                    f"_{ach['desc']}_"
                    f"{bonus_text}",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
    
    return awarded

# ==========================================
#           GIFT CARDS
# ==========================================

def create_gift_card(buyer_tg_id: int, card_type: str) -> str | None:
    """Create a new gift card and return its code."""
    return create_gift_card_service(buyer_tg_id=int(buyer_tg_id), card_type=str(card_type or ""))

def get_gift_card(code: str) -> dict | None:
    """Get gift card info by code."""
    return get_gift_card_service(code)

async def redeem_gift_card(code: str, recipient_tg_id: int, bot) -> tuple[bool, str]:
    """Redeem a gift card. Returns (success, message)."""
    norm_code = str(code or "").strip().upper()
    if norm_code:
        session = Session()
        try:
            user = session.query(User).filter(User.tg_id == int(recipient_tg_id)).first()
            card = session.query(GiftCard).filter(func.upper(GiftCard.code) == norm_code).first()
            if user and card:
                card_type = str(card.card_type or "").strip().upper()
                active_campaigns_for_type = (
                    session.query(func.count(IncentiveCampaign.id))
                    .filter(func.lower(IncentiveCampaign.campaign_type) == "gift")
                    .filter(func.upper(IncentiveCampaign.target_value) == card_type)
                    .filter(IncentiveCampaign.is_active == True)
                    .scalar()
                    or 0
                )
                campaign = _campaign_lookup(
                    session=session,
                    campaign_type="gift",
                    target_value=card_type,
                    user=user,
                    now=_utcnow(),
                )
                if int(active_campaigns_for_type) > 0 and campaign is None:
                    session.flush()
                    return False, "❌ Подарочный код недоступен для этого аккаунта"
        finally:
            session.close()

    result = await redeem_gift_card_service(
        code=code,
        recipient_tg_id=int(recipient_tg_id),
        require_tos=True,
    )
    if not result.get("ok"):
        return False, str(result.get("message") or "❌ Не удалось активировать карту")
    card_type = str(result.get("card_type") or "").strip().upper()
    if card_type:
        session = Session()
        try:
            user = session.query(User).filter(User.tg_id == int(recipient_tg_id)).first()
            if user:
                campaign = _campaign_lookup(
                    session=session,
                    campaign_type="gift",
                    target_value=card_type,
                    user=user,
                    now=_utcnow(),
                )
                _campaign_consume(row=campaign)
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
    days = int(result.get("days") or 0)
    return True, f"✅ Карта активирована!\n\n📅 Тариф продлен на {days} дней"

def build_vless_link(client_uuid: str, email: str = "User") -> str:
    """Generate VLESS Reality link for client"""
    from urllib.parse import quote
    
    # vless://uuid@host:port?params#name
    params = [
        f"type=tcp",
        f"security=reality",
        f"pbk={VLESS_PBK}",
        f"fp={VLESS_FP}",
        f"sni={VLESS_SNI}",
        f"sid={VLESS_SID}",
        f"spx=%2F",
        f"flow={VLESS_FLOW}"
    ]
    
    link = f"vless://{client_uuid}@{HOST_DOMAIN}:{VLESS_PORT}?{'&'.join(params)}#{quote(email)}"
    return link

def build_subscription_link(tg_id: int) -> str:
    """Generate subscription URL for auto-updating config"""
    # Backward compatibility:
    # - prefer per-user secure token when present
    # - fallback to numeric tg_id route for legacy users without token
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    sub_id = ""
    if user:
        sub_id = str(user.sub_token or "").strip()
    session.close()

    if not sub_id:
        sub_id = str(tg_id)

    # Secure path (Proxy on 2096)
    return f"{PUBLIC_API_BASE_URL.rstrip('/')}/s8Kx2mP7qR4wT/{sub_id}"


def next_manual_tg_id() -> int:
    session = Session()
    try:
        min_id = session.query(func.min(User.tg_id)).filter(User.tg_id < 0).scalar()
        if min_id is None:
            return -10001
        return int(min_id) - 1
    finally:
        session.close()


def create_manual_user_record(*, display_name: str, days: int, created_by_admin: int) -> User:
    manual_tg_id = next_manual_tg_id()
    user_uuid = str(uuid.uuid4())
    sub_token = generate_sub_token()
    now = _utcnow()
    session = Session()
    try:
        email = f"MANUAL_{abs(manual_tg_id)}"
        user = User(
            tg_id=manual_tg_id,
            username=None,
            uuid=user_uuid,
            email=email,
            sub_type="MANUAL",
            created_at=now,
            expiry_at=now + timedelta(days=max(1, int(days))),
            is_active=True,
            stars_paid=0,
            total_gb=0,
            trial_used=False,
            tos_accepted=True,
            first_purchase_done=True,
            sub_token=sub_token,
            is_manual=True,
            created_by_admin=int(created_by_admin),
            display_name=(display_name or "").strip()[:100] or email,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()


def regenerate_user_sub_token(tg_id: int) -> str | None:
    session = Session()
    try:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            return None
        token = generate_sub_token()
        user.sub_token = token
        session.commit()
        return token
    finally:
        session.close()


async def sync_user_panel_sub_token(tg_id: int) -> bool:
    """
    Best-effort panel sync after token rotation.
    Ensures existing panel clients receive updated subId from DB token.
    """
    session = Session()
    try:
        user = session.query(User).filter_by(tg_id=int(tg_id)).first()
        if not user:
            return False
        user_uuid = str(user.uuid or "")
        is_active = bool(user.is_active)
    finally:
        session.close()
    if not user_uuid:
        return False
    try:
        return bool(await panel.enable_client(user_uuid, enable=is_active))
    except Exception as exc:
        logger.warning("sub_token panel sync failed for tg_id=%s: %s", int(tg_id), exc)
        return False


def list_manual_users(limit: int = 30) -> list[User]:
    session = Session()
    try:
        return (
            session.query(User)
            .filter((User.tg_id < 0) | (func.upper(User.sub_type) == "MANUAL"))
            .order_by(User.created_at.desc(), User.tg_id.asc())
            .limit(max(1, limit))
            .all()
        )
    finally:
        session.close()



def extend_user(tg_id: int, days: int, stars: int) -> bool:
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    if user:
        now = _utcnow()
        cur = _naive_utc(user.expiry_at) or now
        candidate = max(cur, now) + timedelta(days=days)
        if candidate <= now:
            user.expiry_at = now
            user.is_active = False
        else:
            user.expiry_at = candidate
            user.is_active = True
        user.stars_paid += stars
        session.commit()
    session.close()
    return user is not None


def reset_user_expiry_from_now(tg_id: int, days: int, stars: int) -> bool:
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    if user:
        user.expiry_at = _utcnow() + timedelta(days=days)
        user.stars_paid += stars
        user.is_active = True
        session.commit()
    session.close()
    return user is not None

def mark_trial_used(tg_id: int):
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    if user:
        user.trial_used = True
        session.commit()
    session.close()

def get_stats():
    session = Session()
    total_users = session.query(User).count()
    now = _utcnow()
    active_users = (
        session.query(User)
        .filter(User.is_active == True)
        .filter(User.expiry_at.isnot(None))
        .filter(User.expiry_at > now)
        .count()
    )
    total_stars = session.query(func.sum(User.stars_paid)).scalar() or 0
    session.close()
    return {"total": total_users, "active": active_users, "stars": total_stars}


def audit_admin(actor_tg_id: int, action: str, target_tg_id: int | None = None, meta: str | None = None) -> None:
    try:
        s = Session()
        s.add(AdminAudit(actor_tg_id=actor_tg_id, action=action, target_tg_id=target_tg_id, meta=meta))
        s.commit()
        s.close()
    except Exception:
        # audit must never break admin flows
        pass

# ==========================================
#           PANEL CLIENT
# ==========================================
# Multi-node panel operations are handled by ControlPanel (portal_bot/control_panel.py).
panel = ControlPanel()

# ==========================================
#               BOT HANDLERS
# ==========================================
router = Router()


class CallbackContextMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            if isinstance(event, CallbackQuery) and event.message and event.from_user:
                tg_id = int(event.from_user.id)
                chat_id = int(getattr(getattr(event.message, "chat", None), "id", 0) or 0)
                if _is_private_user_chat(chat_id, tg_id):
                    callback_data = (event.data or "").strip()
                    _set_support_context(tg_id, enabled=_is_support_callback_data(callback_data))
                    await _track_context_message(
                        bot=event.bot,
                        chat_id=chat_id,
                        tg_id=tg_id,
                        message_id=int(event.message.message_id),
                    )
        except Exception:
            pass
        return await handler(event, data)


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    # Used for "page indicator" buttons so Telegram doesn't return "message is not modified".
    await callback.answer()


def _normalize_sub_type(raw: str | None) -> str:
    """
    Keep DB stable:
    - FREE/TRIAL/BONUS: freemium access (non-paid)
    - PAID: any paid access (monthly/quarterly/etc, gifts, legacy VIP/PRO/BASIC)
    - MANUAL: special pinned accounts that we never touch via automation
    """
    s = (raw or "").strip()
    if not s:
        return "FREE"
    up = s.upper()
    if up == "FREE":
        return "FREE"
    if up.startswith("TRIAL"):
        return "TRIAL"
    if up.startswith("BONUS") or up in {"CHANNEL_BONUS", "OPENING_BONUS", "FRIEND_GIFT"}:
        return "BONUS"
    if up == "MANUAL" or s.lower() == "manual":
        return "MANUAL"
    if up in {"VIP", "PRO", "BASIC", "PAID", "MONTHLY", "QUARTERLY", "HALF_YEAR", "YEARLY"}:
        return "PAID"
    # Unknown values are treated as freemium to avoid accidental paid privileges.
    if up in {"", "PENDING"}:
        return "FREE"
    # Legacy fallback for known paid-like values.
    if up.startswith("PAID_") or up.startswith("PREMIUM"):
        return "PAID"
    return "FREE"


def _is_freemium_sub_type(sub_type: str | None) -> bool:
    return _normalize_sub_type(sub_type) in {"FREE", "TRIAL", "BONUS"}


def _has_payment_signal(user: User | None) -> bool:
    if not user:
        return False
    if int(getattr(user, "stars_paid", 0) or 0) > 0:
        return True
    if bool(getattr(user, "first_purchase_done", False)):
        return True
    code = str(getattr(user, "current_plan_code", "") or "").strip().lower()
    if code in {"1_month", "3_months", "6_months", "9_months", "12_months", "start_99"}:
        return True
    return False


def _plan_mode_label(sub_type: str | None) -> str:
    st = _normalize_sub_type(sub_type or "")
    if st in {"FREE", "TRIAL", "BONUS"}:
        return f"до {FREE_TOTAL_GB} ГБ, до {FREE_LIMIT_IP} устройств, до {FREE_SPEED_MBIT} Мбит/с"
    return f"полный доступ, до {PAID_LIMIT_IP} устройств"


def _plan_label_ru(sub_type: str | None) -> str:
    st = _normalize_sub_type(sub_type or "")
    if st == "FREE":
        return "Бесплатный"
    if st == "TRIAL":
        return "Пробный"
    if st == "BONUS":
        return "Бонусный"
    if st == "PAID":
        return "Премиум"
    if st == "MANUAL":
        return "Ручной"
    raw = (sub_type or "").strip()
    return raw or "Не определена"


def _is_paid_active_user(user: User | None) -> bool:
    if not user:
        return False
    expiry = _naive_utc(user.expiry_at)
    if not user.is_active or not expiry or expiry <= _utcnow():
        return False
    return _normalize_sub_type(user.sub_type) == "PAID" and _has_payment_signal(user)


async def _free_remaining_gb(tg_id: int, *, timeout_sec: float = 3.0) -> tuple[float | None, float]:
    """
    Return (remaining_gb, total_gb).
    remaining_gb=None means usage is temporarily unavailable.
    """
    total_gb = float(FREE_TOTAL_GB)
    try:
        usage = await asyncio.wait_for(panel.get_usage_by_tgid(tg_id), timeout=timeout_sec)
    except Exception:
        usage = None
    if not usage:
        return None, total_gb
    used_bytes = int(usage.get("total", 0) or 0)
    used_gb = max(0.0, used_bytes / (1024**3))
    remaining = max(0.0, total_gb - used_gb)
    return round(remaining, 2), total_gb


def _short_node_codes(codes: list[str], *, limit: int = 3) -> str:
    vals = [str(c or "").strip().upper() for c in (codes or []) if str(c or "").strip()]
    if not vals:
        return "—"
    shown = vals[:limit]
    suffix = f" +{len(vals) - limit}" if len(vals) > limit else ""
    return ", ".join(shown) + suffix


def _panel_online_text(snapshot: dict | None) -> str:
    if not snapshot or not bool(snapshot.get("known")):
        return "клиент не найден"
    state = str(snapshot.get("state") or "").lower().strip()
    online_nodes = snapshot.get("online_nodes") or []
    mapped_nodes = snapshot.get("mapped_nodes") or []
    if state == "online":
        return f"онлайн ({_short_node_codes(online_nodes)})"
    if state == "offline":
        return "не в сети"
    return f"статус н/д ({_short_node_codes(mapped_nodes)})"


def _panel_last_online_text(snapshot: dict | None) -> str:
    if not snapshot or not bool(snapshot.get("known")):
        return "н/д"
    age = snapshot.get("last_online_age_seconds")
    if age is None:
        return "н/д"
    try:
        sec = max(0, int(age))
    except Exception:
        return "н/д"
    if sec < 60:
        return "только что"
    if sec < 3600:
        return f"{sec // 60} мин назад"
    if sec < 86400:
        return f"{sec // 3600} ч назад"
    return f"{sec // 86400} дн назад"


async def _panel_online_snapshot(tg_id: int, *, timeout_sec: float = 8.0) -> dict:
    fallback = {
        "known": False,
        "state": "unknown",
        "mapped_nodes": [],
        "online_nodes": [],
        "enabled_nodes": [],
        "last_online_at": None,
        "last_online_age_seconds": None,
    }
    try:
        snap = await asyncio.wait_for(
            panel.get_connection_status_by_tgid(tg_id, per_node_timeout_sec=3.0),
            timeout=max(1.0, float(timeout_sec)),
        )
        if isinstance(snap, dict):
            return snap
    except Exception:
        pass
    return fallback


async def check_subscription(user_id: int, bot: Bot) -> bool:
    channel = (NEWS_CHANNEL_ID or "").strip()
    if not channel:
        return True
    try:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in ["member", "administrator", "creator", "restricted"]
    except Exception as e:
        # Fail closed: if Telegram membership cannot be verified, do not grant gated bonuses.
        err = (str(e) or "").lower()
        hard_fail_markers = (
            "chat not found",
            "bot is not a member",
            "have no rights",
            "not enough rights",
            "forbidden",
            "unauthorized",
            "invalid chat id",
            "peer_id_invalid",
            "channel private",
            "member list is inaccessible",
        )
        if any(m in err for m in hard_fail_markers):
            logger.warning("check_subscription hard-fail user=%s channel=%s err=%s", user_id, channel, e)
            return False
        logger.warning("check_subscription verify-fail user=%s channel=%s err=%s", user_id, channel, e)
        return False

TEXTS = {
    "welcome": (
        "🛡 *PORTAL*\n\n"
        f"{get_copy_text('bot.welcome', 'PORTAL помогает быстро начать работу через Telegram: понятный выбор плана, короткий путь к оплате и живая поддержка рядом.')}\n\n"
        "🔻 *Нажмите кнопку ниже, чтобы продолжить:*"
    ),
    "choose_tariff": (
        "💎 *Выберите уровень доступа*\n\n"
        f"{get_copy_text('bot.choose_tariff', 'Выберите удобный план. В каждом уже видны срок доступа, лимит устройств и доступные страны.')}\n\n"
        "👇 *Тарифные планы:*"
    ),
    "portal_ready": (
        "✅ *Доступ разрешен*\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "🔑 *Статус:* `АКТИВЕН`\n"
        "⏳ *Истекает:* `{expiry}`\n"
        "➖➖➖➖➖➖➖➖➖➖\n\n"
        "Нажмите *«🌐 ОТКРЫТЬ ПОРТАЛ (WEB APP)»* для получения ключей доступа."
    ),
    "already_active": (
        "🛡 *Система активна*\n\n"
        "Доступ уже активен и готов к работе.\n"
        "📅 Действует до: `{expiry}`\n\n"
        "Нужен ключ для нового устройства? Жми кнопку ниже."
    ),
    "status": (
        "👤 *Личный кабинет*\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "🆔 ID: `{tg_id}`\n"
        "🛡 Статус: {status_icon} *{status_text}*\n"
        "📦 Подписка: `{plan_label}`\n"
        "📅 Истекает: `{expiry}`\n"
        "⭐ Оплачено: `{stars}` Stars\n"
        "➖➖➖➖➖➖➖➖➖➖"
    ),
    "no_subscription": (
        "⛔️ *Доступ ограничен*\n\n"
        "У вас нет активного периода доступа.\n"
        "Подключите подходящий план, чтобы продолжить."
    ),
    "instruction": (
        "⚙️ *Быстрая настройка*\n\n"
        "1️⃣ Нажмите кнопку *«🌐 ОТКРЫТЬ ПОРТАЛ (WEB APP)»*\n"
        "2️⃣ Скопируйте ваш *Ключ доступа*\n"
        "3️⃣ Выберите приложение под вашу платформу\n"
        "4️⃣ Импортируйте ключ и нажмите «Подключить»\n\n"
        "_Внутри WebApp есть подробные подсказки для каждой ОС._"
    ),
    "admin_stats": (
        "📊 *Центр управления*\n\n"
        "👥 Пользователей: `{total}`\n"
        "🟢 Активных: `{active}`\n"
        "💰 Оборот: `{stars}` Stars"
    ),
    "trial_used": "❌ Бесплатный режим уже использован. Выберите платный план.",
    "payment_success": "✅ *Оплата принята!* Обновляем статус доступа...",
    "gift_success": "✅ Подписка выдана пользователю {tg_id} на {days} дней."
}

def _bot_enabled_nodes() -> list[dict]:
    """
    Fetch enabled nodes from the control-plane DB.
    Returns NodeRuntime-like objects (dataclass), but we only use .code/.name.
    """
    try:
        from nodes_repo import enabled_nodes  # local import to avoid early import issues

        s = Session()
        try:
            return enabled_nodes(s)
        finally:
            s.close()
    except Exception:
        return []


def _bot_free_codes() -> list[str]:
    nodes = _bot_enabled_nodes()
    return [((getattr(n, "code", "") or "").strip()) for n in nodes if "free" in (getattr(n, "code", "") or "").lower()]


def _node_code_base(code: str) -> str:
    code = (code or "").lower().strip()
    for sep in ("_", "-", "."):
        if sep in code:
            code = code.split(sep, 1)[0]
    return code


def _node_label_ru_bot(code: str, name: str = "") -> str:
    code_raw = (code or "").strip()
    base = _node_code_base(code_raw)
    if "free" in code_raw.lower():
        return "🇳🇱 NL Free"
    flags = {"pl": "🇵🇱", "it": "🇮🇹", "us": "🇺🇸", "nl": "🇳🇱", "de": "🇩🇪", "brain": "🇩🇪"}
    names = {
        "pl": "Польша",
        "it": "Италия",
        "us": "США",
        "nl": "Нидерланды",
        "de": "Германия",
        "brain": "Германия",
    }
    flag = flags.get(base, "🏳️")
    nm = names.get(base, name or (base.upper() if base else code_raw))
    return f"{flag} {nm}".strip()


def _node_ping_from_metrics(node) -> int | None:
    """Best-effort parse of cached node latency from DB metrics."""
    raw = getattr(node, "panel_latency_ms", None)
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw if raw > 0 else None
    if isinstance(raw, float):
        val = int(round(raw))
        return val if val > 0 else None
    try:
        val = int(round(float(str(raw).strip())))
        return val if val > 0 else None
    except Exception:
        return None


async def _probe_tcp_latency_ms(host: str, port: int, *, timeout_sec: float = 1.5) -> int | None:
    """
    Fallback latency probe when metrics are missing.
    Measures TCP connect time to node host:port.
    """
    if not host or not int(port or 0):
        return None
    started = asyncio.get_running_loop().time()
    writer = None
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, int(port)), timeout=timeout_sec)
        elapsed_ms = int((asyncio.get_running_loop().time() - started) * 1000)
        return elapsed_ms if elapsed_ms > 0 else 1
    except Exception:
        return None
    finally:
        if writer:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass


async def _node_ping_ms(node) -> int | None:
    ping = _node_ping_from_metrics(node)
    if ping is not None:
        return ping
    host = (getattr(node, "host", "") or "").strip()
    port = int(getattr(node, "vless_port", 0) or VLESS_PORT)
    return await _probe_tcp_latency_ms(host, port)


def _tariff_savings_pct(tariff_key: str) -> int | None:
    """
    Returns % savings vs paying monthly for the same duration.
    """
    monthly = int(TARIFFS.get("1_month", {}).get("stars") or 0)
    months_map = {"3_months": 3, "6_months": 6, "9_months": 9, "12_months": 12}
    months = months_map.get(tariff_key)
    if not monthly or not months:
        return None
    price = int(TARIFFS.get(tariff_key, {}).get("stars") or 0)
    if price <= 0:
        return None
    baseline = monthly * months
    if baseline <= 0:
        return None
    pct = int(round((1 - (price / baseline)) * 100))
    return pct if pct > 0 else None


def build_choose_tariff_text() -> str:
    nodes = _bot_enabled_nodes()
    paid_nodes = [n for n in nodes if "free" not in (getattr(n, "code", "") or "").lower()]
    paid_count = len(paid_nodes) if paid_nodes else (len(nodes) if nodes else 1)
    paid_list = (
        ", ".join([_node_label_ru_bot(getattr(n, "code", ""), getattr(n, "name", "")) for n in paid_nodes])
        if paid_nodes
        else ("1 локация" if nodes else "1 локация")
    )
    free_node = next((n for n in nodes if "free" in (getattr(n, "code", "") or "").lower()), None)
    free_label = (
        _node_label_ru_bot(getattr(free_node, "code", "free"), getattr(free_node, "name", "NL Free"))
        if free_node
        else "🇳🇱 NL Free"
    )

    s3 = _tariff_savings_pct("3_months")
    s6 = _tariff_savings_pct("6_months")
    s9 = _tariff_savings_pct("9_months")
    s12 = _tariff_savings_pct("12_months")
    savings = []
    if s3:
        savings.append(f"3 мес: -{s3}%")
    if s6:
        savings.append(f"6 мес: -{s6}%")
    if s9:
        savings.append(f"9 мес: -{s9}%")
    if s12:
        savings.append(f"1 год: -{s12}%")
    savings_line = (" (" + ", ".join(savings) + ")") if savings else ""

    payment_hint = "_Оплата Telegram Stars доступна как быстрый резервный путь._"
    if BOT_RUB_BUTTON_ENABLED:
        payment_hint = "_Оплата ₽ на сайте — основной путь. Telegram Stars доступны как резервный вариант._"

    return (
        "💎 *Выберите уровень доступа*\n\n"
        f"🆓 *Бесплатный* — 1 страна: {free_label}\n"
        f"💠 *Премиум* — {paid_count} стран: {paid_list}\n\n"
        f"Бесплатный: до {FREE_TOTAL_GB} ГБ, до {FREE_LIMIT_IP} устройств (по IP), до {FREE_SPEED_MBIT} Мбит/с.\n"
        "Бесплатный: VPN для основных задач; часть медиасервисов может идти напрямую для снижения задержки.\n"
        f"Премиум: полный VPN-маршрут, переключение стран, до {PAID_LIMIT_IP} устройств и высокий профиль скорости.\n"
        "Использовать VPN официально можно — выбирайте режим по сценарию.\n\n"
        f"💰 *Выгода при оплате на срок:*{savings_line}\n\n"
        f"{payment_hint}"
    )


def _dual_pay_text() -> str:
    return (
        "💳 *Оплата в рублях + Stars*\n\n"
        "Основной путь: ₽ на сайте (карта/СБП) с прозрачной разбивкой суммы.\n"
        "Telegram Stars остаются как резервный вариант.\n"
        "Использование VPN официально разрешено.\n\n"
        "Выберите, как продолжить:"
    )


def _dual_pay_keyboard(*, tg_id: int, show_trial: bool) -> InlineKeyboardMarkup:
    ctx = checkout_context_by_user.get(int(tg_id), {}) if checkout_context_by_user else {}
    checkout_url = _bot_checkout_url(
        tg_id=int(tg_id),
        plan_code=str(ctx.get("plan_code") or ""),
        promo_code=str(ctx.get("promo_code") or ""),
        campaign_key=str(ctx.get("campaign_key") or ""),
    )
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="💳 Открыть оплату ₽ (карта/СБП)", url=checkout_url)],
        [InlineKeyboardButton(text="⭐ Оплатить Stars", callback_data="charge_stars")],
    ]
    if show_trial:
        rows.append([InlineKeyboardButton(text="🆓 Бесплатный режим", callback_data="buy_trial")])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def main_keyboard_specs(tg_id: int = 0) -> list[list[dict[str, str]]]:
    rows = [
        [_btn_spec(text="🌐 ОТКРЫТЬ ПОРТАЛ (WEB APP)", web_app_url=WEBAPP_URL)],
        [
            _btn_spec(
                text=_main_connect_cta_text(tg_id),
                callback_data="charge",
                style=BTN_STYLE_PRIMARY,
                icon_custom_emoji_id=BTN_EMOJI_PRIMARY_ID or None,
            ),
        ],
        [
            _btn_spec(text="📦 Подписка", callback_data="status"),
            _btn_spec(text="🔌 Подключение", callback_data="instruction"),
        ],
        [
            _btn_spec(text="🎁 Бонусы", callback_data="menu_bonuses"),
            _btn_spec(text="🆘 Поддержка", callback_data="support"),
        ],
        [
            _btn_spec(text="⚙️ Настройки", callback_data="settings"),
        ],
    ]
    if tg_id == ADMIN_ID:
        rows.append([_btn_spec(text="🔒 Админ-панель", callback_data="admin")])
    return rows


def main_keyboard(tg_id: int = 0) -> InlineKeyboardMarkup:
    """Main menu aligned to the single primary user path."""
    return _keyboard_from_specs(main_keyboard_specs(tg_id))

def tariff_keyboard(
    tg_id: int = 0,
    show_trial: bool = True,
    show_gb_only: bool = False,
    include_long_plans: bool = False,
) -> InlineKeyboardMarkup:
    buttons = []
    
    # Check if user has 20% referral discount
    has_discount = has_referral_discount(tg_id) if tg_id else False
    discount_text = " 🎉 -20%" if has_discount else ""
    
    # Free is always visible. If user already has active paid access, pressing it shows an alert and does nothing.
    if show_trial:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🆓 Бесплатный — 1 страна, {FREE_TOTAL_GB} ГБ, {FREE_LIMIT_IP} устр., {FREE_SPEED_MBIT} Мбит/с",
                    callback_data="buy_trial",
                )
            ]
        )
    
    # Plans order:
    # - main screen: short horizons
    # - long screen: 6/9/12 months only
    if include_long_plans:
        plans = [
            ("6_months", "📅 6 Месяцев"),
            ("9_months", "📅 9 Месяцев"),
            ("12_months", "📅 1 Год"),
        ]
    else:
        plans = [
            ("1_month", "📅 1 Месяц"),
            ("3_months", "📅 3 Месяца"),
        ]
    
    for key, label in plans:
        tariff = TARIFFS.get(key)
        if not tariff: continue
        
        price = tariff["stars"]
        if has_discount:
            price = int(price * 0.8)
            
        icon = "▪️"
        marketing_badge = ""
        if key == "1_month":
            icon = "🚀"
        elif key == "3_months":
            icon = "💠"
            marketing_badge = " (СТАРТ)"
        elif key == "6_months":
            icon = "🎯"
            marketing_badge = " (РЕКОМЕНДУЕМ)"
        elif key == "9_months":
            icon = "⭐"
            marketing_badge = " (РАСШИРЕННЫЙ)"
        elif key == "12_months":
            icon = "👑"
            savings = _tariff_savings_pct(key) or 0
            marketing_badge = f" (МАКС ВЫГОДА, -{savings}%)" if savings > 0 else " (МАКС ВЫГОДА)"

        savings = _tariff_savings_pct(key)
        savings_text = f" (-{savings}%)" if savings and key not in {"12_months"} else ""
        btn_text = f"{icon} {label} — {price} ⭐{discount_text}{marketing_badge}{savings_text}"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"buy_{key}")])
    
    if include_long_plans:
        buttons.append([InlineKeyboardButton(text="◀️ К основным тарифам", callback_data="charge")])
    else:
        buttons.append([InlineKeyboardButton(text="📚 Долгие тарифы", callback_data="charge_long")])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(CommandStart())
async def cmd_start(message: Message):
    tg_id = message.from_user.id
    username = message.from_user.username
    _set_support_context(tg_id, enabled=False)

    start_arg = ""
    referral_code = None
    deeplink_promo_code = ""
    deeplink_campaign_key = ""
    friend_gift_referral_code = ""
    opening_bonus_requested = False
    if message.text:
        parts = message.text.split()
        if len(parts) > 1:
            code_part = parts[1].strip()
            start_arg = code_part
            if code_part.startswith("ref_"):
                code_part = code_part[4:]
            if code_part.upper().startswith("SWAZ") and len(code_part) == 8:
                referral_code = code_part.upper()
            deeplink_promo_code, deeplink_campaign_key = _parse_start_deeplink_context(start_arg)
            friend_gift_referral_code = _parse_friend_gift_ref_code(start_arg)
            start_link_action = _resolve_start_link_action(start_arg)
            if str(start_link_action.get("promo_code") or "").strip():
                deeplink_promo_code = str(start_link_action.get("promo_code") or "").strip().upper()[:20]
            if str(start_link_action.get("campaign_key") or "").strip():
                deeplink_campaign_key = str(start_link_action.get("campaign_key") or "").strip()[:64]
            opening_bonus_requested = bool(start_link_action.get("opening_bonus"))

    try:
        await message.delete()
    except Exception:
        pass

    if tg_id in last_bot_message:
        try:
            await message.bot.delete_message(tg_id, last_bot_message[tg_id])
        except Exception:
            pass

    user = get_user(tg_id)
    panel_client = await panel.get_existing_client(tg_id)
    created_new = False

    if panel_client and not user:
        user = create_user(
            tg_id=tg_id,
            user_uuid=panel_client.get("id", str(uuid.uuid4())),
            email=panel_client.get("email", f"User_{tg_id}"),
            sub_type="PAID",
            days=365,
            gb=1000,
            stars=0,
            username=username,
        )
    elif not user:
        user, created_new = ensure_pending_user(tg_id, username=username)

    if referral_code:
        set_referrer_by_code(tg_id, referral_code)
    if friend_gift_referral_code:
        set_referrer_by_code(tg_id, friend_gift_referral_code)
    update_user_username(tg_id, username)
    if deeplink_promo_code or deeplink_campaign_key:
        checkout_context_by_user[int(tg_id)] = {
            "promo_code": str(deeplink_promo_code or "").upper()[:20],
            "campaign_key": str(deeplink_campaign_key or "")[:64],
        }

    if str(start_arg or "").strip().lower() in {"weblogin", "web_login", "login_web"}:
        token = create_web_session_token(tg_id=int(tg_id), username=username)
        if not token:
            await message.answer(
                "⚠️ Не удалось создать web-сессию. Попробуйте снова через минуту или откройте кабинет из меню бота.",
                reply_markup=main_keyboard(tg_id),
            )
            return
        login_url = _web_login_url_with_token(token)
        await message.answer(
            "✅ Вход подтверждён.\n\nОткройте кабинет по кнопке ниже:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🌐 Открыть кабинет", url=login_url)],
                    [InlineKeyboardButton(text="◀️ В меню", callback_data="back")],
                ]
            ),
        )
        track_event(
            tg_id=int(tg_id),
            event_name="web_login_ticket_issued",
            source="bot",
            meta={"start_arg": str(start_arg or "").lower()},
        )
        return

    promo_requested = bool(
        OPENING_PREMIUM_ENABLED
        and OPENING_PREMIUM_START_CODE
        and start_arg
        and start_arg.strip().lower() == OPENING_PREMIUM_START_CODE
    )
    promo_requested = bool(promo_requested or opening_bonus_requested)
    if promo_requested:
        activated, reason = await _try_activate_opening_premium_bonus(
            message=message,
            bot=message.bot,
            tg_id=tg_id,
            username=username,
        )
        if activated:
            return
        if reason == "already_claimed":
            await message.answer(
                "🎁 Бонус по ссылке уже активирован для вашего аккаунта.\n\n"
                "Открываю меню управления доступом.",
                reply_markup=main_keyboard(tg_id),
            )
            return
        if reason == "already_paid_active":
            await message.answer(
                "✅ У вас уже активен PREMIUM-доступ.\n\n"
                "Открываю меню управления доступом.",
                reply_markup=main_keyboard(tg_id),
            )
            return
        if reason == "tos_required":
            await message.answer(
                "⚠️ Перед активацией бонуса примите условия оферты.",
                reply_markup=_tos_offer_keyboard(back_callback="back"),
                parse_mode=ParseMode.MARKDOWN,
            )
            return

    if friend_gift_referral_code:
        if check_tos_accepted(tg_id):
            activated, reason = await _try_activate_friend_gift_bonus(
                message=message,
                bot=message.bot,
                tg_id=tg_id,
                username=username,
                referral_code=friend_gift_referral_code,
            )
            if activated:
                await message.answer(
                    f"🎁 Подарок из ссылки активирован: +{FRIEND_GIFT_DAYS} дня доступа.",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            if reason == "already_claimed":
                await message.answer(
                    "🎁 Подарок по ссылке уже активирован для вашего аккаунта.\n\n"
                    "Открываю меню управления доступом.",
                    reply_markup=main_keyboard(tg_id),
                )
                return
            if reason == "already_paid_active":
                await message.answer(
                    "✅ У вас уже активен платный доступ.\n\n"
                    "Открываю меню управления доступом.",
                    reply_markup=main_keyboard(tg_id),
                )
                return
            if reason == "invalid_ref":
                await message.answer("⚠️ Подарочная ссылка недействительна или устарела.")
        else:
            pending_auto_friend_gift_referrals[int(tg_id)] = str(friend_gift_referral_code).upper()[:10]
            await message.answer(
                "🎁 Подарок из ссылки сохранён.\n"
                "Сначала примите условия оферты, затем подарок активируется автоматически.",
                parse_mode=ParseMode.MARKDOWN,
            )

    if deeplink_promo_code:
        if check_tos_accepted(tg_id):
            ok, result = activate_promo_code_for_user(tg_id, deeplink_promo_code)
            await message.answer(result, parse_mode=ParseMode.MARKDOWN)
            track_event(
                tg_id=int(tg_id),
                event_name="deep_link_opened",
                source="bot",
                meta={
                    "kind": "promo",
                    "promo_code": str(deeplink_promo_code).upper()[:20],
                    "campaign_key": str(deeplink_campaign_key or "")[:64] or None,
                    "applied": bool(ok),
                },
            )
        else:
            pending_auto_promo_codes[int(tg_id)] = str(deeplink_promo_code).upper()[:20]
            await message.answer(
                "🎟️ Промокод из ссылки сохранён.\n"
                "Сначала примите условия оферты, затем промокод применится автоматически.",
                parse_mode=ParseMode.MARKDOWN,
            )

    if not created_new:
        ok = await _send_text_with_specs(
            bot=message.bot,
            chat_id=tg_id,
            text="👋 *С возвращением в PORTAL!*",
            rows=main_keyboard_specs(tg_id),
            parse_mode=ParseMode.MARKDOWN,
        )
        if not ok:
            await message.answer(
                "👋 *С возвращением в PORTAL!*",
                reply_markup=main_keyboard(tg_id),
                parse_mode=ParseMode.MARKDOWN,
            )
        return

    text = (
        "🛡 *Добро пожаловать в PORTAL*\n\n"
        "Мы подготовили понятный путь запуска и подключения.\n"
        "Как вы хотите настроить подключение?\n\n"
        "🐣 *Новичок*\n"
        "«Хочу быстро и просто, без технических деталей».\n\n"
        "💀 *Профи*\n"
        "«Нужен полный контроль и все инструменты сразу»."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐣 Включить Автопилот (Просто)", callback_data="mode_simple")],
        [InlineKeyboardButton(text="💀 Ручное управление (Профи)", callback_data="mode_pro")],
    ])
    sent = await message.answer(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    last_bot_message[tg_id] = sent.message_id

@router.callback_query(F.data == "back")
async def back_to_main(callback: CallbackQuery):
    tg_id = callback.from_user.id
    pending_redeem_codes.discard(tg_id)
    pending_promo_codes.discard(tg_id)
    pending_auto_promo_codes.pop(int(tg_id), None)
    pending_auto_friend_gift_referrals.pop(int(tg_id), None)
    
    ok = await _edit_text_with_specs(
        bot=callback.message.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=TEXTS["welcome"],
        rows=main_keyboard_specs(tg_id),
        parse_mode=ParseMode.MARKDOWN,
    )
    if not ok:
        await callback.message.edit_text(
            TEXTS["welcome"],
            reply_markup=main_keyboard(tg_id),
            parse_mode=ParseMode.MARKDOWN,
        )
    await callback.answer()

@router.callback_query(F.data == "charge")
async def show_tariffs(callback: CallbackQuery):
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    
    # Check if user has accepted TOS
    if not check_tos_accepted(tg_id):
        await callback.message.edit_text(
            _tos_offer_text(),
            reply_markup=_tos_offer_keyboard(back_callback="back"),
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer()
        return
    
    # Show Free only if user has no active paid access. It should not "downgrade" paid users.
    now = _utcnow()
    expiry = _naive_utc(user.expiry_at) if user else None
    has_active = bool(user and user.is_active and expiry and expiry > now and not _is_freemium_sub_type(user.sub_type))
    show_trial = not has_active

    if BOT_RUB_BUTTON_ENABLED:
        await callback.message.edit_text(
            _dual_pay_text(),
            reply_markup=_dual_pay_keyboard(tg_id=tg_id, show_trial=show_trial),
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer()
        return

    show_gb_only = False  # Kept for legacy UI compatibility.
    await callback.message.edit_text(
        build_choose_tariff_text(),
        reply_markup=tariff_keyboard(tg_id, show_trial, show_gb_only, include_long_plans=False),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "charge_stars")
async def show_tariffs_stars(callback: CallbackQuery):
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    now = _utcnow()
    expiry = _naive_utc(user.expiry_at) if user else None
    has_active = bool(user and user.is_active and expiry and expiry > now and not _is_freemium_sub_type(user.sub_type))
    show_trial = not has_active
    await callback.message.edit_text(
        build_choose_tariff_text(),
        reply_markup=tariff_keyboard(tg_id, show_trial, show_gb_only=False, include_long_plans=False),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "charge_long")
async def show_long_tariffs(callback: CallbackQuery):
    tg_id = callback.from_user.id
    if not check_tos_accepted(tg_id):
        await callback.message.edit_text(
            _tos_offer_text(),
            reply_markup=_tos_offer_keyboard(back_callback="back"),
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "💎 *Долгие тарифы*\n\n"
        "Для тех, кто хочет зафиксировать доступ на длительный срок с лучшей средней ценой в месяц.",
        reply_markup=tariff_keyboard(tg_id, show_trial=False, show_gb_only=False, include_long_plans=True),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()

@router.callback_query(F.data == "accept_tos")
async def accept_tos(callback: CallbackQuery):
    tg_id = callback.from_user.id
    
    # Mark TOS as accepted
    set_tos_accepted(tg_id)

    auto_promo = (pending_auto_promo_codes.pop(int(tg_id), "") or "").strip().upper()
    if auto_promo:
        ok, result = activate_promo_code_for_user(tg_id, auto_promo)
        await callback.message.answer(result, parse_mode=ParseMode.MARKDOWN)
        track_event(
            tg_id=int(tg_id),
            event_name="deep_link_opened",
            source="bot",
            meta={"kind": "promo_after_tos", "promo_code": auto_promo, "applied": bool(ok)},
        )

    auto_friend_ref = (pending_auto_friend_gift_referrals.pop(int(tg_id), "") or "").strip().upper()
    if auto_friend_ref:
        activated, reason = await _try_activate_friend_gift_bonus(
            message=callback.message,
            bot=callback.message.bot,
            tg_id=tg_id,
            username=callback.from_user.username,
            referral_code=auto_friend_ref,
        )
        if activated:
            await callback.answer("✅ Условия приняты. Подарок активирован!", show_alert=True)
            return
        if reason == "already_claimed":
            await callback.message.answer(
                "🎁 Подарок по ссылке уже был активирован ранее.",
                parse_mode=ParseMode.MARKDOWN,
            )
        elif reason == "invalid_ref":
            await callback.message.answer(
                "⚠️ Подарочная ссылка недействительна.",
                parse_mode=ParseMode.MARKDOWN,
            )
    
    # Now show tariffs
    user = get_user(tg_id)

    now = _utcnow()
    expiry = _naive_utc(user.expiry_at) if user else None
    has_active = bool(user and user.is_active and expiry and expiry > now and not _is_freemium_sub_type(user.sub_type))
    show_trial = not has_active
    if BOT_RUB_BUTTON_ENABLED:
        await callback.message.edit_text(
            _dual_pay_text(),
            reply_markup=_dual_pay_keyboard(tg_id=tg_id, show_trial=show_trial),
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        show_gb_only = False
        await callback.message.edit_text(
            build_choose_tariff_text(),
            reply_markup=tariff_keyboard(tg_id, show_trial, show_gb_only, include_long_plans=False),
            parse_mode=ParseMode.MARKDOWN,
        )
    await callback.answer("✅ Условия приняты!")

@router.callback_query(F.data == "status")
async def show_status(callback: CallbackQuery):
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    
    if not user:
        ok = await _edit_text_with_specs(
            bot=callback.message.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=TEXTS["no_subscription"],
            rows=main_keyboard_specs(tg_id),
            parse_mode=ParseMode.MARKDOWN,
        )
        if not ok:
            await callback.message.edit_text(
                TEXTS["no_subscription"],
                reply_markup=main_keyboard(tg_id),
                parse_mode=ParseMode.MARKDOWN,
            )
        await callback.answer()
        return
    
    expiry_dt = _naive_utc(user.expiry_at) if user else None
    if expiry_dt:
        expiry = expiry_dt.strftime("%d.%m.%Y")
    else:
        expiry = "—"
    
    stars = user.stars_paid if user else 0
    is_active = bool(user and user.is_active and expiry_dt and expiry_dt > _utcnow())
    status_icon = "🟢" if is_active else "🔴"
    status_name = "АКТИВЕН" if is_active else "НЕАКТИВЕН"
    status_text = TEXTS["status"].format(
        tg_id=tg_id,
        expiry=expiry,
        stars=stars,
        status_icon=status_icon,
        status_text=status_name,
        plan_label=_plan_label_ru(user.sub_type if user else ""),
    )
    base_limit = FREE_LIMIT_IP if _is_freemium_sub_type(user.sub_type) else PAID_LIMIT_IP
    extra_slots = active_family_slots(tg_id)
    status_text += f"\n📱 Устройства: `{base_limit + extra_slots}` (база {base_limit} + family {extra_slots})"
    if _is_freemium_sub_type(user.sub_type):
        remaining_gb, total_gb = await _free_remaining_gb(tg_id)
        if remaining_gb is None:
            status_text += f"\n📊 Бесплатный лимит: до `{int(total_gb)}` ГБ\n⏳ Остаток: `н/д`"
        else:
            status_text += f"\n📊 Бесплатный остаток: `{remaining_gb}` из `{int(total_gb)}` ГБ"
        is_subscriber = await check_subscription(tg_id, callback.message.bot)
        if is_subscriber:
            status_text += "\n📢 Канал: `подписка подтверждена` — профиль ускорен."
        else:
            status_text += "\n📢 Канал: `не подтверждена` — работает базовый профиль FREE."
    panel_snapshot = await _panel_online_snapshot(tg_id)
    status_text += f"\n🌐 Онлайн: `{_panel_online_text(panel_snapshot)}`"
    status_text += f"\n🕓 Последний онлайн: `{_panel_last_online_text(panel_snapshot)}`"
    
    ok = await _edit_text_with_specs(
        bot=callback.message.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=status_text,
        rows=main_keyboard_specs(tg_id),
        parse_mode=ParseMode.MARKDOWN,
    )
    if not ok:
        await callback.message.edit_text(
            status_text,
            reply_markup=main_keyboard(tg_id),
            parse_mode=ParseMode.MARKDOWN,
        )
    await callback.answer()

@router.callback_query(F.data == "show_key")
async def show_key(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass

    tg_id = callback.from_user.id
    track_event(tg_id=tg_id, event_name="clicked_connect", source="bot")
    user = get_user(tg_id)

    if not check_tos_accepted(tg_id):
        await callback.message.edit_text(
            _tos_offer_text(),
            reply_markup=_tos_offer_keyboard(back_callback="back"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    
    if not user:
        rows = [
            [
                _btn_spec(
                    text=_main_connect_cta_text(tg_id),
                    callback_data="charge",
                    style=BTN_STYLE_PRIMARY,
                    icon_custom_emoji_id=BTN_EMOJI_PRIMARY_ID or None,
                )
            ],
            [
                _btn_spec(
                    text="⛔ Отмена",
                    callback_data="back",
                    style=BTN_STYLE_DANGER,
                    icon_custom_emoji_id=BTN_EMOJI_DANGER_ID or None,
                )
            ],
        ]
        ok = await _edit_text_with_specs(
            bot=callback.message.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="⚠️ *Ключ не найден*\n\nСначала подключите доступ, чтобы получить ключ.",
            rows=rows,
            parse_mode=ParseMode.MARKDOWN,
        )
        if not ok:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=_main_connect_cta_text(tg_id), callback_data="charge")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
            ])
            await callback.message.edit_text(
                "⚠️ *Ключ не найден*\n\nСначала подключите доступ, чтобы получить ключ.",
                reply_markup=kb,
                parse_mode=ParseMode.MARKDOWN
            )
        return

    expiry = _naive_utc(user.expiry_at)
    if not bool(user.is_active and expiry and expiry > _utcnow()):
        rows = [
            [
                _btn_spec(
                    text=_main_connect_cta_text(tg_id),
                    callback_data="charge",
                    style=BTN_STYLE_PRIMARY,
                    icon_custom_emoji_id=BTN_EMOJI_PRIMARY_ID or None,
                )
            ],
            [_btn_spec(text="◀️ Назад", callback_data="back")],
        ]
        await _edit_text_with_specs(
            bot=callback.message.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="⚠️ *Активного доступа пока нет.*\n\nВыберите тариф, чтобы получить новый ключ.",
            rows=rows,
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    msg = await callback.message.edit_text("🔄 `Подключаю защищённый узел...`", parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(0.35)
    await msg.edit_text("🔄 `Проверяю соединение (TLS 1.3)...`", parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(0.35)
    await msg.edit_text("🔄 `Готовлю ключ доступа...`", parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(0.35)

    sub_link = build_subscription_link(tg_id)

    is_free = _is_freemium_sub_type(user.sub_type if user else "")
    free_note = ""
    if is_free:
        nodes = _bot_enabled_nodes()
        paid_nodes = [n for n in nodes if "free" not in (getattr(n, "code", "") or "").lower()]
        paid_count = len(paid_nodes) if paid_nodes else (len(nodes) if nodes else 1)
        paid_list = (
            ", ".join([_node_label_ru_bot(getattr(n, "code", ""), getattr(n, "name", "")) for n in paid_nodes])
            if paid_nodes
            else ("—" if nodes else "—")
        )
        free_note = (
            "\n\n🆓 *Тариф FREE*\n"
            "• 1 бесплатная нода\n"
            f"• Платные: {paid_count} стран ({paid_list})\n"
            f"• Лимит трафика: до {FREE_TOTAL_GB} ГБ\n"
            f"• Лимит устройств: до {FREE_LIMIT_IP} (по IP)\n"
            f"• Лимит скорости: до {FREE_SPEED_MBIT} Мбит/с\n"
            "• Проксируются только соцсети + AI\n"
            "• YouTube идёт напрямую (сервис не помогает)\n"
            "• Всё остальное идёт напрямую (будет виден ваш обычный IP)\n"
        )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Скопировать ссылку", callback_data="copy_key")],
            [InlineKeyboardButton(text="📱 QR-код", callback_data="show_qr")],
            [InlineKeyboardButton(text="👨‍👩‍👧‍👦 Поделиться с семьёй", callback_data="share_access")],
            [InlineKeyboardButton(text="🚨 Panic Mode", callback_data="panic_menu")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
        ]
    )
    
    await msg.edit_text(
        f"🔑 *Ваш ключ доступа:*\n\n"
        f"`{sub_link}`\n\n"
        f"📋 _Нажмите на ссылку, чтобы скопировать_\n\n"
        f"📱 Добавьте как подписку в Hiddify, Streisand или v2rayNG."
        f"{free_note}",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )

@router.callback_query(F.data == "copy_key")
async def copy_key_callback(callback: CallbackQuery):
    tg_id = callback.from_user.id
    sub_link = build_subscription_link(tg_id)
    track_event(tg_id=tg_id, event_name="copied_key", source="bot")
    await callback.answer(f"📋 Скопируйте ссылку:\n{sub_link}", show_alert=True)


@router.callback_query(F.data == "show_qr")
async def show_qr_code(callback: CallbackQuery):
    tg_id = callback.from_user.id
    sub_link = build_subscription_link(tg_id)

    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(sub_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    bio = BytesIO()
    img.save(bio, "PNG")
    bio.seek(0)
    file = BufferedInputFile(bio.read(), filename="portal-key.png")

    await callback.message.answer_photo(
        photo=file,
        caption=(
            "📱 *Ваш QR-ключ доступа*\n\n"
            "Отсканируйте в приложении (Hiddify / v2rayNG)."
        ),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer("QR-код готов")


@router.callback_query(F.data == "share_access")
async def share_family_access(callback: CallbackQuery):
    tg_id = callback.from_user.id
    sub_link = build_subscription_link(tg_id)
    share_text = (
        "🔑 *Доступ к защищенной сети PORTAL*\n\n"
        "Я делюсь с тобой своим приватным каналом связи.\n"
        "1. Скачай приложение Hiddify\n"
        "2. Скопируй ключ ниже и добавь его в приложение\n\n"
        f"`{sub_link}`\n\n"
        "🛡 *Быстро. Надежно. Конфиденциально.*"
    )
    await callback.message.answer(
        "📤 *Перешлите сообщение ниже*\n\nОтправьте его тому, с кем хотите поделиться доступом.",
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.message.answer(share_text, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()


@router.callback_query(F.data == "panic_menu")
async def panic_menu(callback: CallbackQuery):
    text = (
        "🚨 *РЕЖИМ ТРЕВОГИ (PANIC MODE)*\n\n"
        "Используйте это меню, если:\n"
        "• устройство утеряно\n"
        "• вы подозреваете перехват ключа\n"
        "• нужно отключить все активные сессии\n\n"
        "⚠️ Действие: старый ключ будет аннулирован."
    )
    rows = [
        [
            _btn_spec(
                text="☢️ СЖЕЧЬ КЛЮЧИ (Сброс)",
                callback_data="panic_execute",
                style=BTN_STYLE_DANGER,
                icon_custom_emoji_id=BTN_EMOJI_DANGER_ID or None,
            )
        ],
        [
            _btn_spec(
                text="⛔ Отмена",
                callback_data="show_key",
                style=BTN_STYLE_DANGER,
                icon_custom_emoji_id=BTN_EMOJI_DANGER_ID or None,
            )
        ],
    ]
    ok = await _edit_text_with_specs(
        bot=callback.message.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        rows=rows,
        parse_mode=ParseMode.MARKDOWN,
    )
    if not ok:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="☢️ СЖЕЧЬ КЛЮЧИ (Сброс)", callback_data="panic_execute")],
            [InlineKeyboardButton(text="🟢 Отмена", callback_data="show_key")],
        ])
        await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()


@router.callback_query(F.data == "panic_execute")
async def panic_execute(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    user = get_user(user_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    await callback.message.edit_text("🔄 *Initiating Protocol Zero...*", parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(0.8)
    await callback.message.edit_text("🚫 *Revoking certificates...*", parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(0.8)

    new_token = generate_sub_token()
    session = Session()
    user_uuid = ""
    is_active = True
    try:
        db_user = session.query(User).filter_by(tg_id=user_id).first()
        if db_user:
            db_user.sub_token = new_token
            user_uuid = str(db_user.uuid or "")
            is_active = bool(db_user.is_active)
            session.commit()
    finally:
        session.close()

    panel_sync_ok = False
    if user_uuid:
        try:
            panel_sync_ok = bool(await panel.enable_client(user_uuid, enable=is_active))
        except Exception:
            panel_sync_ok = False

    try:
        await bot.send_message(
            ADMIN_ID,
            f"🚨 <b>PANIC BUTTON PRESSED</b>\nUser: {user_id}\nAction: token rotated and requires review.\nPanel sync: {'ok' if panel_sync_ok else 'failed'}",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    await callback.message.edit_text(
        "✅ *Ключи сброшены.*\n\n"
        "Старый доступ заблокирован. Новый ключ уже выпущен.\n"
        "Откройте раздел «Мой ключ», чтобы получить обновленную ссылку.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔑 Мой ключ", callback_data="show_key")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back")],
        ]),
    )
    await callback.answer("Новый ключ выпущен")

@router.callback_query(F.data == "mtproto")
async def show_mtproto(callback: CallbackQuery):
    await callback.message.edit_text(
        "ℹ️ Этот раздел отключен.\n\nИспользуйте «🌐 ОТКРЫТЬ ПОРТАЛ (WEB APP)» для подключения.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="back")]]),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()

@router.callback_query(F.data == "instruction")
async def show_instruction(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🍏 iOS (iPhone)", callback_data="instr_ios"),
            InlineKeyboardButton(text="🤖 Android", callback_data="instr_android"),
        ],
        [
            InlineKeyboardButton(text="💻 Windows", callback_data="instr_win"),
            InlineKeyboardButton(text="🍎 macOS", callback_data="instr_mac"),
        ],
        [InlineKeyboardButton(text="🌐 Открыть Портал", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
    ])
    await callback.message.edit_text(
        "📱 *Выберите ваше устройство:*",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Мой ключ", callback_data="show_key")],
        [InlineKeyboardButton(text="⚙️ Инструкции", callback_data="instruction")],
        [InlineKeyboardButton(text="🎫 Подарки и промокоды", callback_data="menu_more")],
        [InlineKeyboardButton(text=f"👨‍👩‍👧‍👦 Family +1 слот ({FAMILY_SLOT_STARS}⭐)", callback_data="buy_family_slot")],
        [InlineKeyboardButton(text="🆘 Нужна помощь", callback_data="mode_simple")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
    ])
    await callback.message.edit_text(
        "⚙️ *Настройки*\n\nВыберите нужный раздел.",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data.in_({"instr_ios", "instr_android", "instr_win", "instr_mac"}))
async def instruction_platform(callback: CallbackQuery):
    mapping = {
        "instr_ios": (
            "🍏 *Настройка для iOS*\n\n"
            "1. Скачайте Streisand\n"
            "2. Скопируйте ключ в боте\n"
            "3. В приложении нажмите `+` → `Import from Clipboard`",
            IOS_APP_LINK,
            "📥 Скачать Streisand",
        ),
        "instr_android": (
            "🤖 *Настройка для Android*\n\n"
            "1. Скачайте Hiddify или v2rayNG\n"
            "2. Скопируйте ключ в боте\n"
            "3. В приложении импортируйте ключ из буфера",
            ANDROID_APP_LINK,
            "📥 Скачать Hiddify",
        ),
        "instr_win": (
            "💻 *Настройка для Windows*\n\n"
            "1. Установите Hiddify Next или v2rayN\n"
            "2. Скопируйте ключ доступа\n"
            "3. Импортируйте ссылку подписки в клиент",
            WINDOWS_APP_LINK,
            "📥 Скачать клиент",
        ),
        "instr_mac": (
            "🍎 *Настройка для macOS*\n\n"
            "1. Установите Hiddify Next\n"
            "2. Скопируйте ключ доступа\n"
            "3. Импортируйте подписку в приложении",
            MAC_APP_LINK,
            "📥 Скачать клиент",
        ),
    }
    text, url, btn = mapping.get(callback.data or "", mapping["instr_android"])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn, url=url)],
        [InlineKeyboardButton(text="🔑 Мой ключ", callback_data="show_key")],
        [InlineKeyboardButton(text="◀️ Устройства", callback_data="instruction")],
    ])
    await callback.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    await callback.answer()

# ==========================================
#         SUB-MENUS
# ==========================================

@router.callback_query(F.data == "menu_bonuses")
async def menu_bonuses(callback: CallbackQuery):
    """Bonuses submenu: referral, wheel, streak, achievements"""
    tg_id = int(callback.from_user.id)
    user = get_user(tg_id)
    if not _is_paid_active_user(user):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🎁 {CHANNEL_PREMIUM_DAYS} дней премиум за канал", callback_data="bonus_offer_main")],
            [InlineKeyboardButton(text=_main_connect_cta_text(tg_id), callback_data="charge")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
        ])
        await callback.message.edit_text(
            "🎁 *Бонусный центр*\n\n"
            "Можно забрать стартовый бонус за подписку на канал или перейти к тарифам.",
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎁 Пригласить друга", callback_data="referral"),
            InlineKeyboardButton(text="🏆 Ачивки", callback_data="achievements")
        ],
        [
            InlineKeyboardButton(text="🎰 Колесо Фортуны", callback_data="wheel"),
            InlineKeyboardButton(text="🔥 Streak", callback_data="streak")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ])
    
    await callback.message.edit_text(
        "🎁 *Бонусы*\n\n"
        "Реферальная программа, streak, рулетка и достижения.",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "menu_more")
async def menu_more(callback: CallbackQuery):
    """More menu: gift cards, promo, share"""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎫 Подарить", callback_data="gift_cards")],
            [InlineKeyboardButton(text=f"👨‍👩‍👧‍👦 Family +1 слот ({FAMILY_SLOT_STARS}⭐)", callback_data="buy_family_slot")],
            [
                InlineKeyboardButton(text="🎁 Активировать подарок", callback_data="gift_redeem_prompt"),
                InlineKeyboardButton(text="🎟️ Ввести промокод", callback_data="promo_activate_prompt"),
            ],
            [InlineKeyboardButton(text="ℹ️ Помощь по промокоду", callback_data="promo_help")],
            [InlineKeyboardButton(text="⭐ Оставить отзыв", callback_data="review_start")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
        ]
    )
    
    await callback.message.edit_text(
        "📦 *Ещё*\n\n"
        "Дополнительные возможности:",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "promo_help")
async def promo_help(callback: CallbackQuery):
    """Show promo command help"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_more")]
    ])
    await callback.message.edit_text(
        "🎟️ *Активация промокода*\n\n"
        "Команда: `/promo КОД`\n\n"
        "Пример: `/promo NEWYEAR`",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()


@router.callback_query(F.data == "gift_redeem_prompt")
async def gift_redeem_prompt(callback: CallbackQuery):
    pending_redeem_codes.add(callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_more")],
    ])
    await callback.message.edit_text(
        "🎁 *Активация подарка*\n\n"
        "Отправь код в формате `PORTAL-XXXX-XXXX` следующим сообщением.\n"
        "_Старые коды `SWAZ-...` тоже принимаются._",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "promo_activate_prompt")
async def promo_activate_prompt(callback: CallbackQuery):
    pending_promo_codes.add(callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_more")],
    ])
    await callback.message.edit_text(
        "🎟️ *Активация промокода*\n\n"
        "Отправь код следующим сообщением (без `/promo`).\n"
        "Пример: `NEWYEAR`",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()

@router.callback_query(F.data == "review_start")
async def review_start(callback: CallbackQuery):
    """Start review flow from button"""
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    
    if not user or not user.is_active:
        await callback.answer("❌ Активируй подписку, чтобы оставить отзыв", show_alert=True)
        return
    
    if has_user_review(tg_id):
        await callback.answer("❌ Ты уже оставил отзыв. Спасибо!", show_alert=True)
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐", callback_data="rate_1"),
            InlineKeyboardButton(text="⭐⭐", callback_data="rate_2"),
            InlineKeyboardButton(text="⭐⭐⭐", callback_data="rate_3"),
            InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rate_4"),
            InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rate_5"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_more")]
    ])
    
    await callback.message.edit_text(
        "⭐ *Оставь отзыв!*\n\n"
        "Оцени сервис от 1 до 5 звёзд:",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "referral")
async def show_referral(callback: CallbackQuery):
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    if not _is_paid_active_user(user):
        await callback.answer("⚠️ Реферальные бонусы доступны только при активном платном доступе.", show_alert=True)
        return
    
    # Get or create unique referral code
    stats = get_referral_stats(tg_id)
    ref_code = stats.get('code') or get_or_create_referral_code(tg_id)
    
    if not ref_code:
        await callback.answer("⚠️ Сначала активируйте подписку", show_alert=True)
        return
    
    # Generate referral link with SWAZ code
    invite_link = f"https://t.me/{BOT_USERNAME}?start={ref_code}"
    ref_count = stats['count']
    bonus_earned = stats['bonus_earned']
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Поделиться реферальной ссылкой", url=f"https://t.me/share/url?url={invite_link}&text=🛡 PORTAL — приглашение в защищенную сеть")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ])
    
    await callback.message.edit_text(
        f"📡 *Программа расширения сети*\n\n"
        f"Ваш идентификатор агента: `{ref_code}`\n\n"
        f"Расширяйте покрытие PORTAL, подключая новые узлы (друзей).\n"
        f"├ *Им:* скидка 20% на первый доступ\n"
        f"└ *Вам:* +{REFERRAL_BONUS_DAYS} дней доступа за каждую активацию\n\n"
        "Если пользователь оплатит после теста, реферальный бонус начислится автоматически.\n\n"
        f"👇 *Ваша ссылка для приглашения:*\n`{invite_link}`\n\n"
        f"Активировано по ссылке: {ref_count}\n"
        f"Бонусных дней начислено: {bonus_earned}",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "wheel")
async def show_wheel(callback: CallbackQuery):
    """Show Wheel of Fortune menu"""
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    if not _is_paid_active_user(user):
        await callback.answer("⚠️ Рулетка доступна только при активном платном доступе.", show_alert=True)
        return

    can_spin, seconds_left = can_spin_wheel(tg_id)
    
    if not can_spin and seconds_left == 0:
        # User not active
        await callback.answer("⚠️ Активируй подписку, чтобы крутить рулетку!", show_alert=True)
        return
    
    if can_spin:
        status_text = "✅ *Можно крутить!*"
        buttons = [
            [InlineKeyboardButton(text="🎰 КРУТИТЬ!", callback_data="wheel_spin")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
        ]
    else:
        # Calculate time left
        days = seconds_left // 86400
        hours = (seconds_left % 86400) // 3600
        mins = (seconds_left % 3600) // 60
        
        if days > 0:
            time_str = f"{days}д {hours}ч"
        elif hours > 0:
            time_str = f"{hours}ч {mins}м"
        else:
            time_str = f"{mins} мин"
        
        status_text = f"⏳ Следующий спин через: *{time_str}*"
        buttons = [
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
        ]
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    # Display chances matching the actual wheel logic.
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    session.close()
    prizes = wheel_prizes_for_user(user)
    total_weight = sum(w for _, w in prizes) or 1
    prize_lines = []
    for days, w in prizes:
        pct = round((w / total_weight) * 100)
        tag = " (ДЖЕКПОТ!)" if days == 30 else ""
        prize_lines.append(f"• {days} дней — {pct}%{tag}")
    prizes_text = "\n".join(prize_lines)
    
    await callback.message.edit_text(
        f"🎰 *Колесо Фортуны!*\n\n"
        f"Крути раз в неделю и получай бонусные дни!\n\n"
        f"📊 *Призы:*\n{prizes_text}\n\n"
        f"{status_text}",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "wheel_spin")
async def do_wheel_spin(callback: CallbackQuery):
    """Spin the wheel!"""
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    if not _is_paid_active_user(user):
        await callback.answer("⚠️ Рулетка доступна только при активном платном доступе.", show_alert=True)
        return
    
    # Show spinning animation
    await callback.message.edit_text(
        "🎰 *Крутим колесо...*\n\n"
        "🔄 ▓▓▓▓▓▓▓▓▓▓ 🔄",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Small delay for effect
    import asyncio
    await asyncio.sleep(1.5)
    
    # Spin!
    prize = spin_wheel(tg_id)
    
    if prize is None:
        await callback.message.edit_text(
            "❌ Не удалось прокрутить. Попробуй позже!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
            ])
        )
        return
    
    # Keep user enabled in panel (best-effort).
    try:
        await panel.update_client_traffic(tg_id, 0)
    except:
        pass
    
    # Jackpot?
    if prize >= 30:
        emoji = "🎉🎉🎉"
        title = "ДЖЕКПОТ!!!"
        # Award jackpot achievement
        award_achievement(tg_id, "jackpot")
    elif prize >= 7:
        emoji = "✨"
        title = "Отлично!"
    else:
        emoji = "🎁"
        title = "Поздравляем!"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back")]
    ])
    
    await callback.message.edit_text(
        f"{emoji} *{title}*\n\n"
        f"Тебе выпало: *+{prize} Дней*!\n\n"
        f"Подписка продлена.\n"
        f"Приходи через 7 дней за новым призом!",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer(f"🎉 +{prize} Дней!", show_alert=True)

@router.callback_query(F.data == "achievements")
async def show_achievements(callback: CallbackQuery):
    """Show user's achievements"""
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    if not _is_paid_active_user(user):
        await callback.answer("⚠️ Достижения доступны только при активном платном доступе.", show_alert=True)
        return
    
    # Check for new achievements
    await check_achievements(tg_id, callback.bot)
    
    # Get user's unlocked achievements
    unlocked = get_user_achievements(tg_id)
    
    # Build achievements grid (all rewards are days).
    lines = []
    total_days = 0
    for ach_id, ach in ACHIEVEMENTS.items():
        unlocked_now = ach_id in unlocked
        status = "✅" if unlocked_now else "🔒"

        bonus_days = int(ach.get("days", 0) or 0)
        if unlocked_now:
            total_days += bonus_days

        bonus = f" (+{bonus_days} дн.)" if bonus_days > 0 else ""
        lines.append(f"{status} {ach['icon']} *{ach['name']}*{bonus}\n   _{ach['desc']}_")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ])
    
    await callback.message.edit_text(
        f"🏆 *Твои достижения*\n\n"
        f"Открыто: *{len(unlocked)}/{len(ACHIEVEMENTS)}*\n"
        f"Бонусом начислено: *{total_days} дней*\n\n"
        + "\n\n".join(lines),
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "streak")
async def show_streak(callback: CallbackQuery):
    """Show user's streak info"""
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    if not _is_paid_active_user(user):
        await callback.answer("⚠️ Streak доступен только при активном платном доступе.", show_alert=True)
        return

    info = get_streak_info(tg_id)
    
    months = info["months"]
    next_m = info["next_milestone"]
    bonus_days_next = info["bonus_days_next"]
    
    # Build progress bar
    if next_m:
        progress = min(months / next_m, 1.0)
        filled = int(progress * 10)
        bar = "▓" * filled + "░" * (10 - filled)
        progress_text = f"До *{next_m} мес* (+{bonus_days_next} дней): [{bar}]"
    else:
        bar = "▓" * 10
        progress_text = f"🏆 *Все вехи пройдены!* [{bar}]"
    
    # Milestone list
    milestones = "\n".join([
        f"{'✅' if months >= m else '⬜'} {m} мес = +{d} Дней"
        for m, d in sorted(STREAK_REWARDS.items())
    ])
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ])
    
    await callback.message.edit_text(
        f"🔥 *Твой Streak: {months} мес*\n\n"
        f"Каждый месяц активной подписки увеличивает streak.\n"
        f"За вехи получаешь бонусные дни подписки!\n\n"
        f"📊 {progress_text}\n\n"
        f"*Вехи:*\n{milestones}\n\n"
        f"⚠️ _Если подписка истечёт > 7 дней — streak сбросится!_",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()


@router.callback_query(F.data == "buy_family_slot")
async def buy_family_slot(callback: CallbackQuery, bot: Bot):
    tg_id = callback.from_user.id
    current = active_family_slots(tg_id)
    if current >= FAMILY_SLOT_MAX:
        await callback.answer(f"Лимит family-слотов: +{FAMILY_SLOT_MAX}", show_alert=True)
        return
    try:
        await callback.answer()
        await bot.send_invoice(
            chat_id=tg_id,
            title="Family slot +1",
            description=f"+1 устройство на {FAMILY_SLOT_DAYS} дней (макс +{FAMILY_SLOT_MAX})",
            payload=f"familyslot_{tg_id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="Family slot", amount=FAMILY_SLOT_STARS)],
        )
        track_event(tg_id=tg_id, event_name="clicked_pay", source="bot", meta={"plan_code": "family_slot"})
    except Exception:
        await callback.message.answer("❌ Не удалось выставить счёт на family-слот.")


# ==========================================
#         SMART SUPPORT
# ==========================================

FAQ_ANSWERS = {
    "connect": (
        "📱 *Как подключить?*\n\n"
        "1️⃣ Скачай приложение:\n"
        f"• iOS: [Streisand]({IOS_APP_LINK})\n"
        f"• Android: [Клиент]({ANDROID_APP_LINK})\n"
        f"• Windows: [Клиент]({WINDOWS_APP_LINK})\n\n"
        "2️⃣ Нажми *🔑 Мой ключ* в боте\n\n"
        "3️⃣ Скопируй ссылку подписки\n\n"
        "4️⃣ В приложении: ➕ → *Импорт из буфера*\n\n"
        "5️⃣ Подключись! 🚀"
    ),
    "notwork": (
        "⚠️ *Не работает?*\n\n"
        "Попробуй по порядку:\n\n"
        "1. *Обнови подписку* — в приложении потяни вниз список серверов\n\n"
        "2. *Перезапусти приложение*\n\n"
        "3. *Проверь интернет* — отключи прокси, открой google.com\n\n"
        "4. *Смени сервер* — если их несколько в списке\n\n"
        "5. *Перезагрузи телефон*\n\n"
        "Не помогло? Напиши в поддержку 👇"
    ),
    "renew": (
        "💳 *Как продлить доступ?*\n\n"
        f"1️⃣ Открой бота @{BOT_USERNAME_MD}\n\n"
        "2️⃣ Нажми *🛒 Тарифы*\n\n"
        "3️⃣ Выбери нужный план\n\n"
        "4️⃣ Открой оплату ₽ (карта/СБП) или Stars ⭐️\n\n"
        "После успешной оплаты статус обновится автоматически."
    ),
    "referral": (
        "🎁 *Реферальная программа*\n\n"
        "• Пригласи друга по своей ссылке\n"
        "• Друг получит *скидку 20%* на первую покупку\n"
        f"• Ты получишь *+{REFERRAL_BONUS_DAYS} дней* за каждую его покупку!\n\n"
        "Свою ссылку найдёшь в меню → *🎁 Пригласить друга*"
    ),
    "device": (
        "📲 *Смена устройства*\n\n"
        "Просто скачай приложение на новый телефон и добавь ту же ссылку подписки.\n\n"
        "Ссылка: *🔑 Мой ключ* → скопируй → вставь в новое приложение.\n\n"
        f"Лимит устройств зависит от плана: до *{PAID_LIMIT_IP}* в платных режимах."
    ),
}

# ==========================================
#         GIFT CARDS HANDLERS
# ==========================================

@router.callback_query(F.data == "gift_cards")
async def show_gift_cards(callback: CallbackQuery):
    """Show gift card purchase menu"""
    buttons = []
    for key, card in GIFT_CARD_TYPES.items():
        text = f"{card['name']} — {card['days']} дн. — {card['stars']} ⭐"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"buy_giftcard_{key}")])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(
        "🎁 *Подарочные карты*\n\n"
        "Купи карту → получи код → отправь другу!\n"
        "Друг активирует код в меню «Дополнительно» → «Активировать подарок»\n\n"
        "Выбери карту:",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data.startswith("buy_giftcard_"))
async def buy_gift_card(callback: CallbackQuery, bot: Bot):
    """Buy a gift card"""
    card_type = callback.data.replace("buy_giftcard_", "")
    card_info = GIFT_CARD_TYPES.get(card_type)
    
    if not card_info:
        await callback.answer("❌ Неизвестный тип карты", show_alert=True)
        return
    
    tg_id = callback.from_user.id
    
    # Create payment
    await bot.send_invoice(
        chat_id=tg_id,
        title=f"Подарочная карта {card_info['name']}",
        description=f"{card_info['days']} дней",
        payload=f"giftcard_{card_type}_{tg_id}",
        currency="XTR",
        prices=[LabeledPrice(label="Gift Card", amount=card_info["stars"])],
        start_parameter=f"giftcard_{card_type}"
    )
    await callback.answer()

@router.message(Command("redeem"))
async def redeem_command(message: Message, bot: Bot):
    """Redeem a gift card code"""
    pending_redeem_codes.discard(message.from_user.id)
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(
            "📥 *Активация подарочной карты*\n\n"
            "Использование: `/redeem PORTAL-XXXX-XXXX`\n\n"
            "_Старые коды `SWAZ-...` тоже работают._\n\n"
            "_Введи код карты, которую тебе подарили_",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    code = args[1].strip().upper()
    tg_id = message.from_user.id
    
    # Check TOS first
    if not check_tos_accepted(tg_id):
        await message.answer(
            "⚠️ Сначала прими условия использования.\n"
            "Нажми /start и прими оферту."
        )
        return
    
    success, result_msg = await redeem_gift_card(code, tg_id, bot)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Открыть Портал", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back")]
    ]) if success else None
    
    await message.answer(result_msg, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

# ==========================================
#           SHARE (DISABLED)
# ==========================================

@router.message(Command("share"))
async def share_traffic(message: Message, bot: Bot):
    await message.answer(
        "ℹ️ Функция передачи трафика отключена.\n"
        "В сервисе нет лимитов по трафику: доступ считается по сроку (дням)."
    )

# ==========================================
#           REVIEWS
# ==========================================

def _mask_review_username(username: str | None) -> str:
    raw = (username or "").strip()
    if raw.startswith("@"):
        raw = raw[1:].strip()
    if not raw:
        return "Пользователь"
    return f"{raw[:2]}***"


def has_user_review(tg_id: int) -> bool:
    """Check if user already left a review"""
    session = Session()
    exists = session.query(Review).filter_by(tg_id=tg_id).first() is not None
    session.close()
    return exists

def create_review(tg_id: int, username: str, rating: int, text: str = None) -> bool:
    """Create a new review"""
    session = Session()
    # Check if exists
    existing = session.query(Review).filter_by(tg_id=tg_id).first()
    if existing:
        session.close()
        return False
    
    review = Review(
        tg_id=tg_id,
        username=username,
        rating=rating,
        text=text
    )
    session.add(review)
    session.commit()
    session.close()
    return True

def get_featured_reviews(limit: int = 5) -> list:
    """Get top featured reviews for display"""
    session = Session()
    reviews = session.query(Review).filter_by(is_featured=True).order_by(Review.created_at.desc()).limit(limit).all()
    result = [{
        "username": _mask_review_username(r.username),
        "rating": r.rating,
        "text": r.text,
        "date": r.created_at.strftime("%d.%m.%Y") if r.created_at else ""
    } for r in reviews]
    session.close()
    return result

# Store pending review ratings
pending_reviews = {}
# Stores pending support ticket replies: tg_id -> ticket_id
pending_ticket_replies: dict[int, int] = {}
# Pending one-shot inputs from buttons in "More" menu.
pending_redeem_codes: set[int] = set()
pending_promo_codes: set[int] = set()
pending_auto_promo_codes: dict[int, str] = {}
pending_auto_friend_gift_referrals: dict[int, str] = {}
checkout_context_by_user: dict[int, dict[str, str]] = {}

@router.message(Command("review"))
async def review_command(message: Message):
    """Leave a review"""
    tg_id = message.from_user.id
    
    # Check if can review (has active sub, used for 7+ days, no existing review)
    user = get_user(tg_id)
    if not user or not user.is_active:
        await message.answer("❌ Активируй подписку, чтобы оставить отзыв")
        return
    
    if has_user_review(tg_id):
        await message.answer("❌ Ты уже оставил отзыв. Спасибо!")
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐", callback_data="rate_1"),
            InlineKeyboardButton(text="⭐⭐", callback_data="rate_2"),
            InlineKeyboardButton(text="⭐⭐⭐", callback_data="rate_3"),
            InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rate_4"),
            InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rate_5"),
        ],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="back")]
    ])
    
    await message.answer(
        "⭐ *Оставь отзыв!*\n\n"
        "Оцени сервис от 1 до 5 звёзд:",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )

@router.callback_query(F.data.startswith("rate_"))
async def rate_review(callback: CallbackQuery):
    """Handle rating selection"""
    tg_id = callback.from_user.id
    rating = int(callback.data.replace("rate_", ""))
    
    # Save rating, ask for text
    pending_reviews[tg_id] = rating
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="review_skip_text")],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="back")]
    ])
    
    await callback.message.edit_text(
        f"Твоя оценка: {'⭐' * rating}\n\n"
        "Напиши короткий отзыв (до 200 символов):\n\n"
        "_Или нажми 'Пропустить' чтобы оставить только оценку_",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "review_skip_text")
async def skip_review_text(callback: CallbackQuery):
    """Skip text and submit review with just rating"""
    tg_id = callback.from_user.id
    rating = pending_reviews.pop(tg_id, 5)
    username = callback.from_user.username
    
    success = create_review(tg_id, username, rating)
    
    if success:
        await callback.message.edit_text(
            f"✅ *Спасибо за отзыв!*\n\n"
            f"Ты поставил: {'⭐' * rating}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await callback.message.edit_text("❌ Ты уже оставлял отзыв")
    
    await callback.answer()

@router.message()
async def admin_broadcast_capture_any(message: Message):
    """
    Capture any message from admin as broadcast draft (text/media/formatting).
    Uses Telegram copy_message/copy_to so admin doesn't have to write templates.
    """
    if message.from_user.id != ADMIN_ID:
        return
    info = admin_pending_actions.get(ADMIN_ID)
    if not info:
        return
    action = info.get("action")
    if action == "broadcast_capture":
        admin_pending_actions.pop(ADMIN_ID, None)
        draft = {
            "from_chat_id": message.chat.id,
            "message_id": message.message_id,
            "segment": "active",
            "button": None,
        }
        admin_broadcast_drafts[ADMIN_ID] = draft

        ctrl = await message.answer(
            _render_broadcast_draft(draft),
            reply_markup=_broadcast_controls(draft),
            parse_mode=ParseMode.MARKDOWN,
        )
        draft["control_message_id"] = ctrl.message_id
        audit_admin(ADMIN_ID, "admin_broadcast_v2_capture", meta=f"message_id={message.message_id}")
        return

    if action == "admin_dm_capture":
        target_tg_id = int(info.get("target_tg_id") or 0)
        admin_pending_actions.pop(ADMIN_ID, None)
        if target_tg_id <= 0:
            await message.answer("❌ Не найден получатель.")
            return
        try:
            await message.copy_to(chat_id=target_tg_id)
            await message.answer(f"✅ Сообщение отправлено пользователю `{target_tg_id}`.", parse_mode=ParseMode.MARKDOWN)
            audit_admin(ADMIN_ID, "admin_dm_send", target_tg_id=target_tg_id, meta=f"source_msg={message.message_id}")
        except Exception:
            await message.answer("❌ Не удалось отправить. Возможно, пользователь заблокировал бота.")
        return

@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_input(message: Message):
    """Handle text inputs for reviews and admin actions"""
    tg_id = message.from_user.id

    # Support ticket reply capture (user/admin).
    if tg_id in pending_ticket_replies:
        _set_support_context(tg_id, enabled=True)
        ticket_id = pending_ticket_replies.get(tg_id, 0)
        body = (message.text or "").strip()
        if not body:
            await message.answer("❌ Отправь текст для тикета.")
            return

        session = Session()
        try:
            ticket = get_ticket_by_id(session, ticket_id)
            if not ticket:
                await message.answer("❌ Тикет не найден.")
                return
            if not can_access_ticket(ticket, tg_id, ADMIN_ID):
                await message.answer("⛔ Нет доступа к тикету.")
                return

            role = "admin" if tg_id == ADMIN_ID else "user"
            add_ticket_message(
                session,
                ticket_id=ticket.id,
                sender_tg_id=tg_id,
                sender_role=role,
                body=body,
            )
            if tg_id == ADMIN_ID:
                set_ticket_status(
                    session,
                    ticket=ticket,
                    status=STATUS_IN_PROGRESS,
                    assigned_admin_tg_id=ADMIN_ID,
                )
            else:
                set_ticket_status(session, ticket=ticket, status=STATUS_OPEN)
            session.commit()

            await message.answer(f"✅ Ответ добавлен в тикет #{ticket.id}.")

            # Notify opposite side.
            if tg_id == ADMIN_ID:
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="🎫 Открыть тикет", callback_data=f"ticket_view_{ticket.id}")]]
                )
                try:
                    await message.bot.send_message(
                        ticket.user_tg_id,
                        f"💬 Новый ответ оператора в тикете #{ticket.id}.",
                        reply_markup=kb,
                    )
                except Exception:
                    pass
            else:
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="🎫 Открыть тикет", callback_data=f"ticket_view_{ticket.id}")]]
                )
                try:
                    await message.bot.send_message(
                        ADMIN_ID,
                        f"🆕 Новое сообщение в тикете #{ticket.id} от `{ticket.user_tg_id}`",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=kb,
                    )
                except Exception:
                    pass
            pending_ticket_replies.pop(tg_id, None)
        finally:
            session.close()
        return

    if tg_id in pending_redeem_codes:
        pending_redeem_codes.discard(tg_id)
        code = (message.text or "").strip().upper()
        if not code:
            await message.answer("❌ Код пустой. Нажми «🎁 Активировать подарок» и попробуй снова.")
            return
        if not check_tos_accepted(tg_id):
            await message.answer("⚠️ Сначала прими условия. Нажми /start и подтверди оферту.")
            return
        success, result_msg = await redeem_gift_card(code, tg_id, message.bot)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Открыть Портал", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back")],
        ]) if success else InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Ввести код снова", callback_data="gift_redeem_prompt")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back")],
        ])
        await message.answer(result_msg, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return

    if tg_id in pending_promo_codes:
        pending_promo_codes.discard(tg_id)
        code = (message.text or "").strip().upper()
        if not code:
            await message.answer("❌ Код пустой. Нажми «🎟️ Ввести промокод» и попробуй снова.")
            return
        ok, result = activate_promo_code_for_user(tg_id, code)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Ввести другой код", callback_data="promo_activate_prompt")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back")],
        ])
        await message.answer(result, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return
    
    # Check for admin pending actions first
    if tg_id == ADMIN_ID and tg_id in admin_pending_actions:
        action_info = admin_pending_actions.pop(tg_id)
        action = action_info["action"]
        
        # Handle search_user action
        if action == "search_user":
            query = message.text.strip()
            session = Session()
            
            if query.startswith("@"):
                username = query.lstrip("@")
                user = session.query(User).filter(User.username.ilike(username)).first()
            else:
                try:
                    uid = int(query)
                    user = session.query(User).filter_by(tg_id=uid).first()
                except ValueError:
                    user = session.query(User).filter(User.username.ilike(query)).first()
            
            if not user:
                session.close()
                await message.answer(f"❌ Пользователь `{query}` не найден", parse_mode=ParseMode.MARKDOWN)
                return
            
            ach_count = session.query(Achievement).filter_by(tg_id=user.tg_id).count()
            session.close()
            
            status = "✅ Активен" if user.is_active else "❌ Неактивен"
            expiry = user.expiry_at.strftime("%d.%m.%Y") if user.expiry_at else "—"
            
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="👤 Открыть", callback_data=f"adm_user_{user.tg_id}"),
                    InlineKeyboardButton(text="🚫 Бан" if user.is_active else "✅ Разбан", callback_data=f"admin_ban_{user.tg_id}"),
                ],
                [InlineKeyboardButton(text="◀️ Админка", callback_data="admin")]
            ])
            
            safe_username = (user.username or "—").replace("_", "\\_")
            await message.answer(
                f"👤 `{user.tg_id}` @{safe_username}\n"
                f"{status} | До: {expiry}\n"
                f"⭐ Stars: {user.stars_paid or 0}\n"
                f"🔥 Streak: {user.streak_months or 0} | 🏆 {ach_count}",
                reply_markup=kb,
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Handle custom_broadcast action with optional URL button
        if action == "custom_broadcast":
            raw_text = message.text.strip()
            
            # Parse for URL button: text---ButtonText|URL
            msg_text = raw_text
            url_button = None
            
            if "---" in raw_text:
                parts = raw_text.split("---", 1)
                msg_text = parts[0].strip()
                button_part = parts[1].strip()
                if "|" in button_part:
                    btn_text, btn_url = button_part.split("|", 1)
                    url_button = (btn_text.strip(), btn_url.strip())
            
            session = Session()
            users = session.query(User).filter_by(is_active=True).all()
            session.close()
            
            sent = 0
            for user in users:
                if user.tg_id in PROTECTED_USERS or user.tg_id == ADMIN_ID:
                    continue
                try:
                    if url_button:
                        kb = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text=url_button[0], url=url_button[1])]
                        ])
                        await message.bot.send_message(user.tg_id, msg_text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
                    else:
                        await message.bot.send_message(user.tg_id, msg_text, parse_mode=ParseMode.MARKDOWN)
                    sent += 1
                except:
                    pass
            
            btn_info = f" с кнопкой" if url_button else ""
            await message.answer(f"✅ Сообщение{btn_info} отправлено {sent} юзерам")
            return

        if action == "admin_promo_create_form":
            raw = (message.text or "").strip()
            parts = [p.strip() for p in raw.split("|")]
            if len(parts) < 4:
                await message.answer(
                    "Формат: `CODE|days|14|100` или `CODE|discount|20|50|2026-03-01T00:00:00`",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            code = re.sub(r"[^A-Z0-9_]+", "", parts[0].upper())[:20]
            promo_type = parts[1].lower()
            if promo_type not in {"days", "discount"}:
                await message.answer("Тип должен быть `days` или `discount`.", parse_mode=ParseMode.MARKDOWN)
                return
            try:
                value = int(parts[2])
                uses = int(parts[3])
            except Exception:
                await message.answer("value и uses должны быть числами.", parse_mode=ParseMode.MARKDOWN)
                return
            expires_at = None
            if len(parts) >= 5 and parts[4]:
                try:
                    expires_at = datetime.fromisoformat(parts[4])
                except Exception:
                    await message.answer("Неверный expires_at. Используйте ISO формат.", parse_mode=ParseMode.MARKDOWN)
                    return

            s = Session()
            try:
                exists = s.query(PromoCode.id).filter(func.upper(PromoCode.code) == code).first()
                if exists:
                    await message.answer("Промокод уже существует.")
                    return
                row = PromoCode(code=code, promo_type=promo_type, value=value, uses_left=uses, expires_at=expires_at)
                s.add(row)
                s.commit()
            finally:
                s.close()
            await message.answer(f"✅ Промокод `{code}` создан.", parse_mode=ParseMode.MARKDOWN)
            return

        if action == "admin_live_create":
            raw = (message.text or "").strip()
            parts = [p.strip() for p in raw.split("|")]
            if len(parts) < 3:
                await message.answer(
                    "Формат: `Заголовок|Кратко|@channel|123` или `Заголовок|Кратко|https://...`",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            title = parts[0][:160]
            summary = parts[1][:600]
            channel_username = None
            post_id = None
            link = ""
            if len(parts) >= 4 and parts[2].startswith("@"):
                channel_username = parts[2].lstrip("@")[:64]
                try:
                    post_id = int(parts[3])
                except Exception:
                    await message.answer("post_id должен быть числом.", parse_mode=ParseMode.MARKDOWN)
                    return
                link = f"https://t.me/{channel_username}/{post_id}"
            else:
                link = parts[2][:600]
            if not link:
                await message.answer("Ссылка не заполнена.")
                return

            s = Session()
            try:
                now = _utcnow()
                row = LiveUpdate(
                    title=title,
                    summary=summary,
                    link=link,
                    channel_username=channel_username,
                    post_id=post_id,
                    is_active=True,
                    sort_order=100,
                    created_at=now,
                    updated_at=now,
                )
                s.add(row)
                s.commit()
            finally:
                s.close()
            await message.answer("✅ Обновление сохранено.")
            return

        if action == "admin_start_create":
            raw = (message.text or "").strip()
            parts = [p.strip() for p in raw.split("|")]
            if len(parts) < 3:
                await message.answer(
                    "Формат: `code|Описание|target_action`",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            code = re.sub(r"[^a-z0-9_-]+", "", parts[0].lower())[:64]
            if len(code) < 2:
                await message.answer("Некорректный code.")
                return
            description = parts[1][:240]
            target_action = parts[2][:64]

            s = Session()
            try:
                exists = s.query(StartLink.id).filter(func.lower(StartLink.code) == code).first()
                if exists:
                    await message.answer("Такой code уже существует.")
                    return
                now = _utcnow()
                row = StartLink(
                    code=code,
                    description=description or None,
                    target_action=target_action or None,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
                s.add(row)
                s.commit()
            finally:
                s.close()
            await message.answer(
                f"✅ Ссылка создана:\n`https://t.me/{BOT_USERNAME}?start={code}`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        if action == "admin_start_edit":
            link_id = int(action_info.get("link_id") or 0)
            if link_id <= 0:
                await message.answer("Некорректный link_id.")
                return
            raw = (message.text or "").strip()
            parts = [p.strip() for p in raw.split("|")]
            if len(parts) < 3:
                await message.answer(
                    "Формат: `code|Описание|target_action`",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return

            code = re.sub(r"[^a-z0-9_-]+", "", parts[0].lower())[:64]
            if len(code) < 2:
                await message.answer("Некорректный code.")
                return
            description = parts[1][:240]
            target_action = parts[2][:64]

            s = Session()
            try:
                row = s.query(StartLink).filter(StartLink.id == link_id).first()
                if not row:
                    await message.answer("Ссылка не найдена.")
                    return
                exists = (
                    s.query(StartLink.id)
                    .filter(func.lower(StartLink.code) == code)
                    .filter(StartLink.id != link_id)
                    .first()
                )
                if exists:
                    await message.answer("Такой code уже занят.")
                    return
                row.code = code
                row.description = description or None
                row.target_action = target_action or None
                row.updated_at = _utcnow()
                s.commit()
            finally:
                s.close()

            await message.answer(
                f"✅ Ссылка обновлена:\n`https://t.me/{BOT_USERNAME}?start={code}`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        if action == "broadcast_set_button":
            draft = admin_broadcast_drafts.get(ADMIN_ID)
            if not draft:
                await message.answer("Черновик не найден. Сначала создай рассылку заново.")
                return

            raw = (message.text or "").strip()
            if raw.lower() in {"нет", "no", "none", "-"}:
                draft["button"] = None
            else:
                if "|" not in raw:
                    await message.answer("Формат: `Текст кнопки|https://example.com` или `нет`", parse_mode=ParseMode.MARKDOWN)
                    return
                btn_text, btn_url = [x.strip() for x in raw.split("|", 1)]
                if not btn_text or not btn_url.startswith(("http://", "https://")):
                    await message.answer("Проверь текст кнопки и URL (должен начинаться с http/https).")
                    return
                draft["button"] = {"text": btn_text[:64], "url": btn_url}

            # Update controls message if we have it.
            ctrl_id = draft.get("control_message_id")
            if ctrl_id:
                try:
                    await message.bot.edit_message_text(
                        chat_id=ADMIN_ID,
                        message_id=ctrl_id,
                        text=_render_broadcast_draft(draft),
                        reply_markup=_broadcast_controls(draft),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except Exception:
                    pass
            await message.answer("✅ Обновил кнопку. Можно отправлять.")
            return

        if action == "wheel_cd":
            raw = (message.text or "").strip()
            try:
                days = int(raw)
            except Exception:
                await message.answer("Введи число (например `7`).", parse_mode=ParseMode.MARKDOWN)
                return
            if days < 1 or days > 90:
                await message.answer("Диапазон: 1–90 дней.", parse_mode=ParseMode.MARKDOWN)
                return

            _save_wheel_config(cooldown_days=days)
            audit_admin(ADMIN_ID, "admin_wheel_cd_set", meta=f"days={days}")
            await message.answer(f"✅ Кулдаун обновлён: {days}д.")
            return

        if action == "wheel_weights":
            raw = (message.text or "").strip()
            pairs = [p.strip() for p in raw.split(",") if p.strip()]
            parsed: list[tuple[int, int]] = []
            for pair in pairs:
                if ":" not in pair:
                    await message.answer("Формат весов: `1:45,3:35,7:15,30:5`", parse_mode=ParseMode.MARKDOWN)
                    return
                d_raw, w_raw = [x.strip() for x in pair.split(":", 1)]
                try:
                    d_val = int(d_raw)
                    w_val = int(w_raw)
                except Exception:
                    await message.answer("Значения должны быть числами.", parse_mode=ParseMode.MARKDOWN)
                    return
                if d_val <= 0 or w_val <= 0:
                    await message.answer("days/weight должны быть > 0.", parse_mode=ParseMode.MARKDOWN)
                    return
                parsed.append((d_val, w_val))
            if not parsed:
                await message.answer("Добавьте минимум один приз.")
                return
            _save_wheel_config(weights=parsed, preset="manual")
            await message.answer("✅ Веса рулетки обновлены.")
            return

        if action == "manual_create":
            raw = (message.text or "").strip()
            if "|" not in raw:
                await message.answer("Формат: `DisplayName|days`", parse_mode=ParseMode.MARKDOWN)
                return
            name_raw, days_raw = [p.strip() for p in raw.split("|", 1)]
            try:
                days = int(days_raw)
            except Exception:
                await message.answer("Количество дней должно быть числом.", parse_mode=ParseMode.MARKDOWN)
                return
            if days < 1 or days > 3650:
                await message.answer("Диапазон дней: 1..3650", parse_mode=ParseMode.MARKDOWN)
                return

            manual_user = create_manual_user_record(
                display_name=name_raw or "Manual Client",
                days=days,
                created_by_admin=ADMIN_ID,
            )
            sub_id = manual_user.sub_token or str(manual_user.tg_id)
            try:
                res = await panel.ensure_user_on_all_nodes(
                    tg_id=manual_user.tg_id,
                    client_uuid=manual_user.uuid,
                    email=manual_user.email,
                    sub_id=sub_id,
                    enable=True,
                    only_node_codes=None,
                )
                ok = sum(1 for v in res.values() if v)
                fail = sum(1 for v in res.values() if not v)
            except Exception:
                ok = 0
                fail = 1

            link = build_subscription_link(manual_user.tg_id)
            qr = qrcode.QRCode(box_size=7, border=3)
            qr.add_data(link)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            bio = BytesIO()
            img.save(bio, "PNG")
            bio.seek(0)
            photo = BufferedInputFile(bio.read(), filename=f"manual-{abs(manual_user.tg_id)}.png")

            await message.answer_photo(
                photo=photo,
                caption=(
                    "✅ *Manual user создан*\n\n"
                    f"ID: `{manual_user.tg_id}`\n"
                    f"Name: `{(manual_user.display_name or manual_user.email)}`\n"
                    f"Sub: `{manual_user.sub_type}`\n"
                    f"Nodes sync: OK `{ok}`, fail `{fail}`\n\n"
                    f"Link:\n`{link}`"
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="👤 Открыть карточку", callback_data=f"adm_user_{manual_user.tg_id}")],
                    [InlineKeyboardButton(text="🧩 Manual меню", callback_data="admin_manual_menu")],
                ]),
            )
            audit_admin(ADMIN_ID, "admin_manual_create", target_tg_id=manual_user.tg_id, meta=f"days={days}; ok={ok}; fail={fail}")
            return
        
        target_id = action_info.get("target")
        
        try:
            value = int(message.text.strip())
        except ValueError:
            await message.answer("❌ Введи число")
            return
        
        if action == "addgb":
            await message.answer(
                "ℹ️ Лимиты по трафику не используются.\n"
                "Используй продление по дням или смену тарифа.",
                parse_mode=ParseMode.MARKDOWN,
            )
        
        elif action == "extend":
            extend_user(target_id, value, 0)
            await message.answer(f"✅ Подписка юзера `{target_id}` продлена на {value} дней", parse_mode=ParseMode.MARKDOWN)
        
        elif action == "mass_addgb":
            await message.answer(
                "ℹ️ Массовое управление трафиком отключено (используются тарифные политики).\n"
                "Используй массовое продление по дням.",
                parse_mode=ParseMode.MARKDOWN,
            )
        
        elif action == "mass_extend":
            session = Session()
            now = _utcnow()
            try:
                count = (
                    session.query(User)
                    .filter(User.is_active == True)
                    .filter(User.expiry_at.isnot(None))
                    .filter(User.expiry_at > now)
                    .filter(User.tg_id != ADMIN_ID)
                    .count()
                )
            finally:
                session.close()

            await message.answer(
                f"⚠️ *Подтверждение действия*\n\n"
                f"Добавить *{value}* дней активному сегменту.\n"
                f"Будет затронуто: *{count}* пользователей.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=_bulk_confirm_kb(f"mass_extend_run_{value}"),
            )
        
        return
    
    # Handle review text
    if tg_id in pending_reviews:
        rating = pending_reviews.pop(tg_id)
        text = message.text[:200]
        username = message.from_user.username
        
        success = create_review(tg_id, username, rating, text)
        
        if success:
            await message.answer(
                f"✅ *Спасибо за отзыв!*\n\n"
                f"{'⭐' * rating}\n"
                f"_{text}_",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await message.answer("❌ Ты уже оставлял отзыв")


@router.callback_query(F.data == "network_status")
async def network_status(callback: CallbackQuery):
    nodes = _bot_enabled_nodes()
    if not nodes:
        await callback.message.edit_text(
            "📡 *Состояние узлов сети*\n\n"
            "Нет данных по узлам. Проверьте конфигурацию control-plane.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="back")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer()
        return

    ping_values = await asyncio.gather(*[_node_ping_ms(n) for n in nodes])

    lines: list[str] = ["📡 *Состояние узлов сети*\n"]
    loads: list[int] = []
    for n, ping in zip(nodes, ping_values):
        code = _node_code_base(getattr(n, "code", ""))
        label = _node_label_ru_bot(getattr(n, "code", ""), getattr(n, "name", ""))
        healthy = bool(getattr(n, "is_healthy", True))
        ping_text = f"{ping}ms" if isinstance(ping, int) else "n/a"
        load = int(getattr(n, "active_clients", 0) or 0)
        loads.append(max(load, 0))
        dns_sni = "OK" if healthy else "WARN"
        node_kind = "Control" if code in {"brain", "de"} else "Node"
        lines.append(f"{label}: {'🟢' if healthy else '🔴'} Online ({node_kind}, Ping: {ping_text}, DNS/SNI: {dns_sni})")

    avg_load = int(sum(loads) / max(1, len(loads))) if loads else 0
    lines.append(f"\n⚡️ Нагрузка системы: {avg_load}%")
    lines.append("\nДля детальной диагностики откройте WebApp → Nodes.")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Проверить доступность", callback_data="network_status_scan")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
        ]),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "network_status_scan")
async def network_status_scan(callback: CallbackQuery):
    await callback.message.edit_text("🔄 *Сканирование узлов...*", parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(0.6)
    await callback.message.edit_text("🔄 *Проверка DNS / SNI...*", parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(0.6)
    await network_status(callback)

@router.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery):
    """Show support menu"""
    _set_support_context(callback.from_user.id, enabled=True)
    support_new_url = f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new"
    support_my_url = f"https://t.me/{SUPPORT_USERNAME}?start=ticket_my"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❓ Как подключить?", callback_data="faq_connect")],
        [InlineKeyboardButton(text="⚠️ Не работает", callback_data="faq_notwork")],
        [InlineKeyboardButton(text="💳 Как продлить?", callback_data="faq_renew")],
        [InlineKeyboardButton(text="🎁 Реферальная программа", callback_data="faq_referral")],
        [InlineKeyboardButton(text="📲 Смена устройства", callback_data="faq_device")],
        [InlineKeyboardButton(text="🔧 Диагностика", callback_data="support_diagnose")],
        [InlineKeyboardButton(text="🎫 Создать тикет", url=support_new_url)],
        [InlineKeyboardButton(text="📂 Мои тикеты (helpbot)", url=support_my_url)],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ])
    
    await callback.message.edit_text(
        "🤖 *Поддержка*\n\n"
        "Единый канал поддержки: отдельный helpbot.\n"
        "Напиши туда проблему, оператор ответит в той же ветке.\n\n"
        "Выбери вопрос или действие:",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data.startswith("faq_"))
async def show_faq_answer(callback: CallbackQuery):
    """Show FAQ answer"""
    faq_key = callback.data.replace("faq_", "")
    answer = FAQ_ANSWERS.get(faq_key, "Ответ не найден")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к вопросам", callback_data="support")],
        [InlineKeyboardButton(text="💬 Написать в поддержку", url=f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new")]
    ])
    
    await callback.message.edit_text(
        answer,
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )
    await callback.answer()

@router.callback_query(F.data == "support_diagnose")
async def support_diagnose(callback: CallbackQuery):
    """Run diagnostics and show user status"""
    _set_support_context(callback.from_user.id, enabled=True)
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    
    if not user:
        status = "❌ Подписка не найдена"
        details = "Активируй подписку через *🛒 Тарифы*"
    else:
        # Status
        if user.is_active and user.expiry_at and user.expiry_at > datetime.utcnow():
            days_left = (user.expiry_at - datetime.utcnow()).days
            status = f"✅ Активна (ещё {days_left} дн.)"
        else:
            status = "❌ Истекла"
        
        # Details
        expiry = user.expiry_at.strftime("%d.%m.%Y") if user.expiry_at else "—"
        tariff = user.sub_type or "—"
        
        details = (
            f"📦 Тариф: *{tariff}*\n"
            f"📅 До: *{expiry}*\n"
            f"📡 Режим: *{_plan_mode_label(tariff)}*"
        )
    
    # Server check
    server_status = "✅ Онлайн"  # Simplified - we're running so server is up
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Моя ссылка", callback_data="show_key")],
        [InlineKeyboardButton(text="◀️ Назад к поддержке", callback_data="support")],
        [InlineKeyboardButton(text="💬 Написать в поддержку", url=f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new")]
    ])
    
    await callback.message.edit_text(
        f"🔧 *Диагностика*\n\n"
        f"*Твоя подписка:* {status}\n\n"
        f"{details}\n\n"
        f"*Сервер:* {server_status}",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()


def _ticket_status_title(status: str) -> str:
    if status == STATUS_IN_PROGRESS:
        return "В работе"
    if status == STATUS_CLOSED:
        return "Закрыт"
    return "Открыт"


def _ticket_message_preview(text: str, limit: int = 220) -> str:
    one_line = " ".join((text or "").split())
    if not one_line:
        return "(без текста)"
    if len(one_line) > limit:
        return one_line[: limit - 1] + "…"
    return one_line


def _ticket_view_keyboard(ticket_id: int, status: str, *, is_admin: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if status != STATUS_CLOSED:
        rows.append([InlineKeyboardButton(text="✍️ Ответить", callback_data=f"ticket_reply_{ticket_id}")])
        rows.append([InlineKeyboardButton(text="✅ Закрыть", callback_data=f"ticket_close_{ticket_id}")])
    else:
        rows.append([InlineKeyboardButton(text="♻️ Переоткрыть", callback_data=f"ticket_reopen_{ticket_id}")])

    if is_admin:
        rows.append([InlineKeyboardButton(text="🧑‍💼 Взять в работу", callback_data=f"ticket_claim_{ticket_id}")])
        rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_tickets")])
    else:
        rows.append([InlineKeyboardButton(text="📂 Мои тикеты", callback_data="ticket_my")])
        rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="support")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _render_ticket(callback: CallbackQuery, ticket_id: int) -> None:
    tg_id = callback.from_user.id
    is_admin = tg_id == ADMIN_ID
    session = Session()
    try:
        ticket = get_ticket_by_id(session, ticket_id)
        if not ticket:
            await callback.answer("Тикет не найден", show_alert=True)
            return
        if not can_access_ticket(ticket, tg_id, ADMIN_ID):
            await callback.answer("Нет доступа к тикету", show_alert=True)
            return

        msgs = list_ticket_messages(session, ticket_id=ticket.id, limit=20)
        status = _ticket_status_title(ticket.status)
        created = ticket.created_at.strftime("%d.%m %H:%M") if ticket.created_at else "-"
        updated = ticket.updated_at.strftime("%d.%m %H:%M") if ticket.updated_at else "-"
        assigned = str(ticket.assigned_admin_tg_id) if ticket.assigned_admin_tg_id else "-"
        lines = []
        for msg in msgs:
            ts = msg.created_at.strftime("%d.%m %H:%M") if msg.created_at else "-"
            role = "Оператор" if msg.sender_role == "admin" else "Пользователь"
            lines.append(f"[{ts}] {role}: {_ticket_message_preview(msg.body)}")
        history = "\n".join(lines) if lines else "Сообщений пока нет."

        text = (
            f"🎫 Тикет #{ticket.id}\n"
            f"Статус: {status}\n"
            f"Пользователь: {ticket.user_tg_id}\n"
            f"Оператор: {assigned}\n"
            f"Создан: {created}\n"
            f"Обновлён: {updated}\n\n"
            f"{history}"
        )
        await callback.message.edit_text(
            text,
            reply_markup=_ticket_view_keyboard(ticket.id, ticket.status, is_admin=is_admin),
        )
        await callback.answer()
    finally:
        session.close()


@router.callback_query(F.data == "ticket_new")
async def ticket_new(callback: CallbackQuery):
    tg_id = callback.from_user.id
    session = Session()
    try:
        ticket = get_user_active_ticket(session, tg_id)
        if ticket:
            await callback.message.edit_text(
                f"У тебя уже есть активный тикет #{ticket.id}.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🎫 Открыть тикет", callback_data=f"ticket_view_{ticket.id}")],
                        [InlineKeyboardButton(text="📂 Мои тикеты", callback_data="ticket_my")],
                        [InlineKeyboardButton(text="◀️ Назад", callback_data="support")],
                    ]
                ),
            )
            await callback.answer()
            return

        ticket = create_ticket(session, user_tg_id=tg_id)
        session.commit()
        pending_ticket_replies[tg_id] = ticket.id

        await callback.message.edit_text(
            f"Тикет #{ticket.id} создан.\nОтправь одним сообщением описание проблемы.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data="support")]]
            ),
        )
        await callback.answer()

        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🎫 Открыть тикет", callback_data=f"ticket_view_{ticket.id}")]]
        )
        try:
            await callback.bot.send_message(
                ADMIN_ID,
                f"🆕 Новый тикет #{ticket.id} от пользователя `{tg_id}`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb,
            )
        except Exception:
            pass
    finally:
        session.close()


@router.callback_query(F.data == "ticket_my")
async def ticket_my(callback: CallbackQuery):
    tg_id = callback.from_user.id
    session = Session()
    try:
        tickets = list_user_tickets(session, tg_id, limit=10)
    finally:
        session.close()

    if not tickets:
        await callback.message.edit_text(
            "Тикетов пока нет.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🎫 Создать тикет", callback_data="ticket_new")],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="support")],
                ]
            ),
        )
        await callback.answer()
        return

    rows: list[list[InlineKeyboardButton]] = []
    for ticket in tickets:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"#{ticket.id} {_ticket_status_title(ticket.status)}",
                    callback_data=f"ticket_view_{ticket.id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="🎫 Создать тикет", callback_data="ticket_new")])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="support")])

    await callback.message.edit_text(
        "Мои тикеты:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ticket_view_"))
async def ticket_view(callback: CallbackQuery):
    ticket_id = int(callback.data.replace("ticket_view_", ""))
    await _render_ticket(callback, ticket_id)


@router.callback_query(F.data.startswith("ticket_reply_"))
async def ticket_reply(callback: CallbackQuery):
    ticket_id = int(callback.data.replace("ticket_reply_", ""))
    session = Session()
    try:
        ticket = get_ticket_by_id(session, ticket_id)
        if not ticket:
            await callback.answer("Тикет не найден", show_alert=True)
            return
        if not can_access_ticket(ticket, callback.from_user.id, ADMIN_ID):
            await callback.answer("Нет доступа", show_alert=True)
            return
        if callback.from_user.id == ADMIN_ID:
            set_ticket_status(
                session,
                ticket=ticket,
                status=STATUS_IN_PROGRESS,
                assigned_admin_tg_id=ADMIN_ID,
            )
        elif ticket.status == STATUS_CLOSED:
            set_ticket_status(session, ticket=ticket, status=STATUS_OPEN)
        session.commit()
    finally:
        session.close()

    pending_ticket_replies[callback.from_user.id] = ticket_id
    await callback.message.edit_text(
        f"Ответ в тикет #{ticket_id}: отправь одно текстовое сообщение.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data=f"ticket_view_{ticket_id}")]]
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ticket_close_"))
async def ticket_close(callback: CallbackQuery):
    ticket_id = int(callback.data.replace("ticket_close_", ""))
    session = Session()
    try:
        ticket = get_ticket_by_id(session, ticket_id)
        if not ticket:
            await callback.answer("Тикет не найден", show_alert=True)
            return
        if not can_access_ticket(ticket, callback.from_user.id, ADMIN_ID):
            await callback.answer("Нет доступа", show_alert=True)
            return
        set_ticket_status(session, ticket=ticket, status=STATUS_CLOSED)
        session.commit()

        # Notify opposite side.
        if callback.from_user.id == ADMIN_ID:
            try:
                await callback.bot.send_message(ticket.user_tg_id, f"Тикет #{ticket.id} закрыт оператором.")
            except Exception:
                pass
        else:
            try:
                await callback.bot.send_message(
                    ADMIN_ID,
                    f"Пользователь `{ticket.user_tg_id}` закрыл тикет #{ticket.id}.",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass
    finally:
        session.close()
    await _render_ticket(callback, ticket_id)


@router.callback_query(F.data.startswith("ticket_reopen_"))
async def ticket_reopen(callback: CallbackQuery):
    ticket_id = int(callback.data.replace("ticket_reopen_", ""))
    session = Session()
    try:
        ticket = get_ticket_by_id(session, ticket_id)
        if not ticket:
            await callback.answer("Тикет не найден", show_alert=True)
            return
        if not can_access_ticket(ticket, callback.from_user.id, ADMIN_ID):
            await callback.answer("Нет доступа", show_alert=True)
            return
        set_ticket_status(session, ticket=ticket, status=STATUS_OPEN)
        session.commit()

        if callback.from_user.id != ADMIN_ID:
            try:
                await callback.bot.send_message(
                    ADMIN_ID,
                    f"Тикет #{ticket.id} переоткрыт пользователем `{ticket.user_tg_id}`.",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass
    finally:
        session.close()
    await _render_ticket(callback, ticket_id)


@router.callback_query(F.data.startswith("ticket_claim_"))
async def ticket_claim(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Только для админа", show_alert=True)
        return
    ticket_id = int(callback.data.replace("ticket_claim_", ""))
    session = Session()
    try:
        ticket = get_ticket_by_id(session, ticket_id)
        if not ticket:
            await callback.answer("Тикет не найден", show_alert=True)
            return
        set_ticket_status(
            session,
            ticket=ticket,
            status=STATUS_IN_PROGRESS,
            assigned_admin_tg_id=ADMIN_ID,
        )
        session.commit()
    finally:
        session.close()
    await _render_ticket(callback, ticket_id)


@router.callback_query(F.data == "admin_tickets")
async def admin_tickets(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Только для админа", show_alert=True)
        return

    session = Session()
    try:
        tickets = list_active_tickets(session, limit=20)
    finally:
        session.close()

    if not tickets:
        await callback.message.edit_text(
            "В очереди нет активных тикетов.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]]
            ),
        )
        await callback.answer()
        return

    rows: list[list[InlineKeyboardButton]] = []
    for ticket in tickets:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"#{ticket.id} u:{ticket.user_tg_id} {_ticket_status_title(ticket.status)}",
                    callback_data=f"ticket_view_{ticket.id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_tickets")])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin")])

    await callback.message.edit_text(
        "Активные тикеты:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await callback.answer()

@router.callback_query(F.data == "admin")
async def show_admin_panel(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещён")
        return
    
    stats = get_stats()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Найти юзера", callback_data="admin_search_prompt"),
            InlineKeyboardButton(text="👥 Все юзеры", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="🎫 Промокоды", callback_data="admin_promos"),
            InlineKeyboardButton(text="⭐ Отзывы", callback_data="admin_reviews")
        ],
        [
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast_menu"),
            InlineKeyboardButton(text="🎰 Рулетка", callback_data="admin_wheel")
        ],
        [
            InlineKeyboardButton(text="📊 Групповые действия", callback_data="admin_mass"),
            InlineKeyboardButton(text="❤️ Health", callback_data="admin_health")
        ],
        [
            InlineKeyboardButton(text="Sync usernames", callback_data="admin_sync"),
            InlineKeyboardButton(text="🎁 Подарки", callback_data="admin_gift_menu")
        ],
        [
            InlineKeyboardButton(text="📰 Последние обновления", callback_data="admin_live_updates"),
            InlineKeyboardButton(text="🔗 Launch ссылки", callback_data="admin_start_links"),
        ],
        [
            InlineKeyboardButton(text="🎫 Очередь тикетов", callback_data="admin_tickets"),
        ],
        [
            InlineKeyboardButton(text="Ноды", callback_data="admin_nodes"),
            InlineKeyboardButton(text="Sync Free pool", callback_data="admin_sync_free_pl"),
        ],
        [
            InlineKeyboardButton(text="🧩 Manual users", callback_data="admin_manual_menu"),
        ],
        [InlineKeyboardButton(text="Back", callback_data="back")],
    ])
    
    await callback.message.edit_text(
        TEXTS["admin_stats"].format(
            total=stats["total"],
            active=stats["active"],
            stars=stats["stars"]
        ),
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "admin_manual_menu")
async def admin_manual_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать manual user", callback_data="admin_manual_create_prompt")],
        [InlineKeyboardButton(text="📋 Список manual users", callback_data="admin_manual_list")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")],
    ])
    await callback.message.edit_text(
        "🧩 *Manual users*\n\n"
        "Создавайте пользователей без Telegram аккаунта.\n"
        "Они будут подключаться ко всем paid-нодам.",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "admin_manual_create_prompt")
async def admin_manual_create_prompt(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    admin_pending_actions[ADMIN_ID] = {"action": "manual_create"}
    await callback.message.edit_text(
        "➕ *Создание manual user*\n\n"
        "Отправьте: `DisplayName|days`\n"
        "Пример: `Family Router|30`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_manual_menu")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_manual_list")
async def admin_manual_list(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    rows = list_manual_users(limit=40)
    if not rows:
        await callback.message.edit_text(
            "Manual users пока не созданы.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_manual_menu")],
            ]),
        )
        await callback.answer()
        return

    buttons: list[list[InlineKeyboardButton]] = []
    for u in rows:
        name = (u.display_name or u.email or f"manual_{abs(u.tg_id)}").strip()
        buttons.append([
            InlineKeyboardButton(text=f"{name} ({u.tg_id})", callback_data=f"adm_user_{u.tg_id}"),
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_manual_menu")])
    await callback.message.edit_text(
        "📋 *Manual users*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()

@router.callback_query(F.data == "admin_search_prompt")
async def admin_search_prompt(callback: CallbackQuery):
    """Prompt admin to search for user"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    admin_pending_actions[ADMIN_ID] = {"action": "search_user"}
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin")]
    ])
    
    await callback.message.edit_text(
        "🔍 *Поиск пользователя*\n\n"
        "Введи @username или tg\\_id:",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "admin_promos")
async def admin_promos_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    
    session = Session()
    promos = session.query(PromoCode).order_by(PromoCode.created_at.desc()).limit(20).all()
    session.close()
    
    if promos:
        lines = []
        for p in promos:
            type_text = f"{p.value}%" if p.promo_type == "discount" else f"+{p.value} дн."
            uses_text = "∞" if p.uses_left == -1 else str(p.uses_left)
            lines.append(f"`{p.code}` — {type_text}, ×{uses_text}")
        promo_text = "\n".join(lines)
    else:
        promo_text = "_Нет активных промокодов_"
    
    kb_rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="➕ Создать промокод", callback_data="admin_promo_create")],
    ]
    for p in promos[:8]:
        kb_rows.append(
            [InlineKeyboardButton(text=f"🗑 Удалить {p.code}", callback_data=f"admin_promo_delete_{p.code}")]
        )
    kb_rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin")])
    
    await callback.message.edit_text(
        f"🎫 *Промокоды*\n\n{promo_text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "admin_promo_create")
async def admin_promo_create(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    admin_pending_actions[ADMIN_ID] = {"action": "admin_promo_create_form"}
    await callback.message.edit_text(
        "➕ *Создать промокод*\n\n"
        "Формат:\n"
        "`CODE|days|14|100`\n"
        "или\n"
        "`CODE|discount|20|50|2026-03-01T00:00:00`\n\n"
        "Последнее поле `expires_at` необязательное.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_promos")]]),
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_promo_delete_"))
async def admin_promo_delete(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    code = str(callback.data or "").replace("admin_promo_delete_", "", 1).strip().upper()[:20]
    if not code:
        await callback.answer("Некорректный код", show_alert=True)
        return

    s = Session()
    try:
        row = s.query(PromoCode).filter(func.upper(PromoCode.code) == code).first()
        if not row:
            await callback.answer("Промокод не найден", show_alert=True)
            return
        s.delete(row)
        s.commit()
    finally:
        s.close()
    audit_admin(ADMIN_ID, "admin_promo_delete", meta=f"code={code}")
    await admin_promos_menu(callback)

@router.callback_query(F.data == "admin_reviews")
async def admin_reviews_menu(callback: CallbackQuery):
    """Show reviews moderation"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    session = Session()
    reviews = session.query(Review).order_by(Review.created_at.desc()).limit(5).all()
    total = session.query(Review).count()
    featured = session.query(Review).filter_by(is_featured=True).count()
    session.close()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Все отзывы", callback_data="admin_reviews_all")],
        [InlineKeyboardButton(text="⭐ Избранные", callback_data="admin_reviews_featured")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]
    ])
    
    await callback.message.edit_text(
        f"⭐ *Отзывы*\n\n"
        f"Всего: {total}\n"
        f"Избранных: {featured}\n\n"
        f"_Команда: /reviews_",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "admin_health")
async def admin_health_check(callback: CallbackQuery, bot: Bot):
    """Quick health check from admin panel"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    import time
    start_time = time.time()
    status = ["✅ Бот: работает"]
    
    try:
        session = Session()
        user_count = session.query(User).count()
        active_count = session.query(User).filter_by(is_active=True).count()
        session.close()
        status.append(f"✅ БД: {user_count} юзеров ({active_count} активных)")
    except Exception as e:
        status.append(f"❌ БД: ошибка")
    
    try:
        clients = await panel.get_clients_list()
        if clients is not None:
            status.append(f"✅ Панель: {len(clients)} клиентов")
        else:
            status.append("⚠️ Панель: нет ответа")
    except:
        status.append("❌ Панель: ошибка")
    
    elapsed = round((time.time() - start_time) * 1000)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_health")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]
    ])
    
    await callback.message.edit_text(
        f"❤️ *Health Check*\n\n" + 
        "\n".join(status) +
        f"\n\n⏱️ {elapsed}мс",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast_menu")
async def admin_broadcast_menu(callback: CallbackQuery):
    """Broadcast menu with custom messages and templates"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    session = Session()
    active = session.query(User).filter_by(is_active=True).count()
    templates = session.query(Template).all()
    session.close()
    
    template_btns = []
    if templates:
        for t in templates[:5]:  # Show max 5 templates
            template_btns.append([InlineKeyboardButton(
                text=f"📝 {t.key}", 
                callback_data=f"send_tpl_{t.key}"
            )])
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧩 Конструктор рассылки", callback_data="admin_bcast_compose")],
        [InlineKeyboardButton(text="🔄 Обновить ссылки", callback_data="admin_broadcast_links")],
        *template_btns,
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]
    ])
    
    tpl_hint = f"\n📝 Шаблонов: {len(templates)}" if templates else "\n_Нет шаблонов_"
    
    await callback.message.edit_text(
        f"📢 *Рассылка*\n\n"
        f"Активных юзеров: {active}{tpl_hint}\n\n"
        f"_Сообщение одному пользователю:_ открой карточку юзера → `✉️ Сообщение`.\n\n"
        f"_Шаблоны и команды:_\n"
        f"`/template add key текст` — создать\n"
        f"`/template list` — список\n"
        f"`/template send key` — всем\n"
        f"`/template send key @user` — юзеру",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()


@router.callback_query(F.data == "admin_nodes")
async def admin_nodes(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    s = Session()
    try:
        nodes = enabled_nodes(s)
    finally:
        s.close()

    lines = ["🗺 *Ноды (enabled)*\n"]
    for n in nodes:
        code = (getattr(n, "code", "") or "").strip()
        name = (getattr(n, "name", "") or "").strip()
        host = (getattr(n, "host", "") or "").strip()
        port = int(getattr(n, "vless_port", 0) or 0)
        inb = int(getattr(n, "inbound_id", 0) or 0)
        pbase = (getattr(n, "panel_base_url", "") or "").strip()

        lines.append(f"✅ `{code}` {name} — `{host}:{port}` (inb `{inb}`)")
        if pbase:
            lines.append(f"    panel: `{pbase}`")

    free_codes = [((getattr(n, "code", "") or "").strip()) for n in nodes if "free" in (getattr(n, "code", "") or "").lower()]
    if free_codes:
        lines.append(f"\nFree pool: `{', '.join(free_codes)}`.")
    else:
        lines.append("\nFree pool: `not configured`.")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_nodes")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")],
        ]
    )
    await callback.message.edit_text("\n".join(lines), reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()


@router.callback_query(F.data == "admin_sync_free_pl")
async def admin_sync_free_pl(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.answer("⏳ Sync Free pool...")
    await callback.message.edit_text(
        "🆓 *Sync Free pool*\n\nЗапускаю. Это может занять 10–60 секунд.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]]),
        parse_mode=ParseMode.MARKDOWN,
    )

    s = Session()
    try:
        nodes = enabled_nodes(s)
        free_codes = [((getattr(n, "code", "") or "").strip()) for n in nodes if "free" in (getattr(n, "code", "") or "").lower()]
        if not free_codes:
            await callback.message.edit_text(
                "🆓 *Sync Free pool*\n\n❌ Free-ноды не найдены в `nodes`.\nДобавь отдельную free-ноду (code с `free`).",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]]),
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        now = datetime.utcnow()
        users = (
            s.query(User)
            .filter(func.upper(User.sub_type).in_(["FREE", "TRIAL", "BONUS"]))
            .filter(User.is_active == True)
            .filter((User.expiry_at.is_(None)) | (User.expiry_at > now))
            .order_by(User.created_at.asc())
            .all()
        )
    finally:
        s.close()

    sem = asyncio.Semaphore(6)
    passes = 2
    async def sync_one(u: User) -> bool:
        async with sem:
            sub_id = u.sub_token or str(u.tg_id)
            res = await panel.ensure_user_on_all_nodes(
                tg_id=u.tg_id,
                client_uuid=u.uuid,
                email=u.email,
                sub_id=sub_id,
                enable=True,
                only_node_codes=free_codes,
            )
            return any(res.values())

    pending = list(users)
    ok = 0
    for attempt in range(1, passes + 1):
        if not pending:
            break
        results = await asyncio.gather(*(sync_one(u) for u in pending))
        next_pending: list[User] = []
        for u, r in zip(pending, results):
            if r:
                ok += 1
            else:
                next_pending.append(u)
        pending = next_pending
        if pending and attempt < passes:
            await asyncio.sleep(1.0)

    fail = len(pending)

    await callback.message.edit_text(
        "🆓 *Sync Free pool*\n\n"
        f"✅ OK: {ok}\n"
        f"❌ Fail: {fail}\n\n"
        "После этого Free-пользователи будут получать только выделенный free-pool после обновления подписки в приложении.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]]),
        parse_mode=ParseMode.MARKDOWN,
    )


async def _render_reviews_page(*, callback: CallbackQuery, featured_only: bool, page: int) -> None:
    if callback.from_user.id != ADMIN_ID:
        return

    page = max(0, int(page))
    per_page = 8
    offset = page * per_page

    session = Session()
    q = session.query(Review)
    if featured_only:
        q = q.filter_by(is_featured=True)
    total = q.count()
    rows = q.order_by(Review.created_at.desc()).offset(offset).limit(per_page).all()
    session.close()

    pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, pages - 1)

    title = "⭐ Избранные отзывы" if featured_only else "📝 Все отзывы"
    if not rows:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📝 Все", callback_data="admin_reviews_all:0"),
                    InlineKeyboardButton(text="⭐ Избранные", callback_data="admin_reviews_featured:0"),
                ],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")],
            ]
        )
        await callback.message.edit_text(f"{title}\n\nПусто.", reply_markup=kb)
        return

    lines = [f"{title}\nВсего: {total} | Стр {page+1}/{pages}\n"]
    kb_rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text="📝 Все", callback_data="admin_reviews_all:0"),
            InlineKeyboardButton(text="⭐ Избранные", callback_data="admin_reviews_featured:0"),
        ]
    ]

    for r in rows:
        masked = _mask_review_username(r.username)
        u = f"@{masked}" if masked != "Пользователь" else masked
        stars = "⭐" * int(r.rating or 0)
        txt = (r.text or "").strip()
        if len(txt) > 120:
            txt = txt[:120] + "…"
        lines.append(f"ID {r.id} | {u} {stars}\n{txt or '—'}\n")
        kb_rows.append(
            [
                InlineKeyboardButton(
                    text="⭐" if not r.is_featured else "❌",
                    callback_data=f"review_toggle_{r.id}",
                ),
                InlineKeyboardButton(text="🗑", callback_data=f"review_delete_{r.id}"),
            ]
        )

    nav: list[InlineKeyboardButton] = []
    prefix = "admin_reviews_featured" if featured_only else "admin_reviews_all"
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{pages}", callback_data="noop"))
    if (page + 1) < pages:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"{prefix}:{page+1}"))
    kb_rows.append(nav)
    kb_rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin")])

    await callback.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))


@router.callback_query(F.data.startswith("admin_reviews_all"))
async def admin_reviews_all(callback: CallbackQuery):
    page = 0
    parts = (callback.data or "").split(":")
    if len(parts) >= 2 and parts[1].isdigit():
        page = int(parts[1])
    await _render_reviews_page(callback=callback, featured_only=False, page=page)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_reviews_featured"))
async def admin_reviews_featured(callback: CallbackQuery):
    page = 0
    parts = (callback.data or "").split(":")
    if len(parts) >= 2 and parts[1].isdigit():
        page = int(parts[1])
    await _render_reviews_page(callback=callback, featured_only=True, page=page)
    await callback.answer()


def _broadcast_segment_cycle(cur: str) -> str:
    order = ["active", "all", "expired", "trial"]
    try:
        i = order.index(cur)
    except ValueError:
        return "active"
    return order[(i + 1) % len(order)]


def _broadcast_segment_label(seg: str) -> str:
    return {
        "active": "Активные",
        "all": "Все",
        "expired": "Неактивные",
        "trial": "Пробные",
    }.get(seg, seg)


def _render_broadcast_draft(draft: dict) -> str:
    seg = _broadcast_segment_label(draft.get("segment", "active"))
    btn = draft.get("button")
    btn_txt = "нет" if not btn else f"{btn.get('text','')}"
    return (
        "📢 *Конструктор рассылки*\n\n"
        f"🎯 Аудитория: *{seg}*\n"
        f"🔗 Кнопка: *{btn_txt or 'нет'}*\n\n"
        "_Сообщение будет отправлено как копия (с сохранением форматирования/медиа)._"
    )


def _broadcast_controls(draft: dict) -> InlineKeyboardMarkup:
    seg = _broadcast_segment_label(draft.get("segment", "active"))
    btn = draft.get("button")
    btn_label = "Кнопка: нет" if not btn else f"Кнопка: {btn.get('text','')[:16]}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"🎯 {seg}", callback_data="admin_bcast_seg"),
                InlineKeyboardButton(text=f"🔗 {btn_label}", callback_data="admin_bcast_btn"),
            ],
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="admin_bcast_send"),
                InlineKeyboardButton(text="🗑 Отмена", callback_data="admin_bcast_cancel"),
            ],
        ]
    )


@router.callback_query(F.data == "admin_bcast_compose")
async def admin_bcast_compose(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    admin_pending_actions[ADMIN_ID] = {"action": "broadcast_capture"}
    admin_broadcast_drafts.pop(ADMIN_ID, None)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_broadcast_menu")]])
    await callback.message.edit_text(
        "🧩 *Конструктор рассылки*\n\n"
        "1. Отправь сюда сообщение, которое нужно разослать.\n"
        "Можно: текст, фото, видео, документ, с форматированием.\n\n"
        "2. Я сохраню его как черновик и покажу кнопки управления.",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "admin_bcast_seg")
async def admin_bcast_seg(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    draft = admin_broadcast_drafts.get(ADMIN_ID)
    if not draft:
        await callback.answer("Черновик не найден. Создай рассылку заново.", show_alert=True)
        return
    draft["segment"] = _broadcast_segment_cycle(draft.get("segment", "active"))
    await callback.message.edit_text(_render_broadcast_draft(draft), reply_markup=_broadcast_controls(draft), parse_mode=ParseMode.MARKDOWN)
    await callback.answer()


@router.callback_query(F.data == "admin_bcast_btn")
async def admin_bcast_btn(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    draft = admin_broadcast_drafts.get(ADMIN_ID)
    if not draft:
        await callback.answer("Черновик не найден. Создай рассылку заново.", show_alert=True)
        return
    admin_pending_actions[ADMIN_ID] = {"action": "broadcast_set_button"}
    await callback.message.edit_text(
        "🔗 *Кнопка для рассылки*\n\n"
        "Пришли одной строкой:\n"
        "`Текст кнопки|https://example.com`\n\n"
        "Или пришли `нет`, чтобы убрать кнопку.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_broadcast_menu")]]),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "admin_bcast_cancel")
async def admin_bcast_cancel(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    admin_pending_actions.pop(ADMIN_ID, None)
    admin_broadcast_drafts.pop(ADMIN_ID, None)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_broadcast_menu")]])
    await callback.message.edit_text("🗑 Черновик удален.", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "admin_bcast_send")
async def admin_bcast_send(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return
    draft = admin_broadcast_drafts.get(ADMIN_ID)
    if not draft:
        await callback.answer("Черновик не найден. Создай рассылку заново.", show_alert=True)
        return

    segment = draft.get("segment", "active")
    from_chat_id = draft.get("from_chat_id", ADMIN_ID)
    message_id = draft.get("message_id")
    if not message_id:
        await callback.answer("Черновик поврежден (нет message_id).", show_alert=True)
        return

    button = draft.get("button")
    reply_markup = None
    if button:
        try:
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=button["text"], url=button["url"])]]
            )
        except Exception:
            reply_markup = None

    s = Session()
    try:
        q = s.query(User)
        if segment == "active":
            q = q.filter_by(is_active=True)
        elif segment == "expired":
            q = q.filter_by(is_active=False)
        elif segment == "trial":
            q = q.filter(User.sub_type == "TRIAL")
        users = q.all()
    finally:
        s.close()

    total = len(users)
    await callback.message.edit_text(
        f"📤 *Рассылка запущена*\n\nАудитория: *{_broadcast_segment_label(segment)}*\nВсего: *{total}*",
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()

    sent = 0
    failed = 0
    for i, u in enumerate(users, start=1):
        if u.tg_id in PROTECTED_USERS or u.tg_id == ADMIN_ID:
            continue
        try:
            await bot.copy_message(
                chat_id=u.tg_id,
                from_chat_id=from_chat_id,
                message_id=message_id,
                reply_markup=reply_markup,
            )
            sent += 1
        except Exception:
            failed += 1
        if i % 40 == 0:
            try:
                await callback.message.edit_text(
                    f"📤 *Рассылка идет*\n\nОтправлено: *{sent}*\nОшибок: *{failed}*",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass
        await asyncio.sleep(0.04)

    audit_admin(ADMIN_ID, "admin_broadcast_v2", meta=f"segment={segment}; sent={sent}; failed={failed}")
    admin_broadcast_drafts.pop(ADMIN_ID, None)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_broadcast_menu")]])
    await callback.message.edit_text(
        f"✅ *Рассылка завершена*\n\nОтправлено: *{sent}*\nОшибок: *{failed}*",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )

@router.callback_query(F.data == "admin_custom_msg")
async def admin_custom_msg_prompt(callback: CallbackQuery):
    """Prompt for custom message with optional URL button"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    admin_pending_actions[ADMIN_ID] = {"action": "custom_broadcast"}
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_broadcast_menu")]
    ])
    
    await callback.message.edit_text(
        "✍️ *Кастомная рассылка*\n\n"
        "Введи текст сообщения.\n\n"
        "*Формат с кнопкой URL:*\n"
        "`Текст сообщения\n---\nТекст кнопки|https://ссылка.com`\n\n"
        "_Пример:_\n"
        "`Привет! Новое обновление!\n---\n🌐 Подробнее|https://portal-privacy.online/`",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast_links")
async def admin_broadcast_links(callback: CallbackQuery, bot: Bot):
    """Trigger link broadcast from button"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    await callback.answer("🔄 Рассылка ссылок запущена...")
    
    # Call existing broadcast logic
    session = Session()
    users = session.query(User).filter_by(is_active=True).all()
    session.close()
    
    sent = 0
    for user in users:
        if user.tg_id in PROTECTED_USERS or user.tg_id == ADMIN_ID:
            continue
        try:
            sub_link = build_subscription_link(user.tg_id)
            await bot.send_message(
                user.tg_id,
                f"🔗 *Обновлённая ссылка подписки:*\n`{sub_link}`\n\n"
                f"_Пожалуйста, обновите в приложении._",
                parse_mode=ParseMode.MARKDOWN
            )
            sent += 1
        except:
            pass
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_broadcast_menu")]
    ])
    
    await callback.message.edit_text(
        f"✅ *Рассылка завершена*\n\n"
        f"Отправлено: {sent} сообщений",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )

@router.callback_query(F.data.startswith("send_tpl_"))
async def send_template_to_all(callback: CallbackQuery, bot: Bot):
    """Send template to all users from button"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    key = callback.data.replace("send_tpl_", "")
    
    session = Session()
    template = session.query(Template).filter_by(key=key).first()
    users = session.query(User).filter_by(is_active=True).all()
    session.close()
    
    if not template:
        await callback.answer("❌ Шаблон не найден", show_alert=True)
        return
    
    await callback.answer(f"📤 Отправка шаблона '{key}'...")
    
    sent = 0
    for user in users:
        if user.tg_id in PROTECTED_USERS or user.tg_id == ADMIN_ID:
            continue
        try:
            await bot.send_message(user.tg_id, template.text, parse_mode=ParseMode.MARKDOWN)
            sent += 1
        except:
            pass
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_broadcast_menu")]
    ])
    
    await callback.message.edit_text(
        f"✅ *Шаблон '{key}' отправлен*\n\n"
        f"Получили: {sent} юзеров",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )

# ==========================================
#         WHEEL SETTINGS
# ==========================================

@router.callback_query(F.data == "admin_wheel")
async def admin_wheel_settings(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    cfg = _load_wheel_config()
    weights = list(cfg.get("weights") or WHEEL_DEFAULT_PRIZES)
    cooldown_hours = int(cfg.get("cooldown_hours") or WHEEL_DEFAULT_COOLDOWN_HOURS)
    cooldown_days = _cooldown_days_from_hours(cooldown_hours)
    preset = str(cfg.get("preset") or "manual")
    total_weight = sum(w for _, w in weights)
    prizes_text = []
    for days, weight in weights:
        pct = (weight / total_weight) * 100
        prizes_text.append(f"• {days} дней — {pct:.0f}%")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Preset: Balanced", callback_data="wheel_preset_balanced"),
                InlineKeyboardButton(text="Preset: Steady", callback_data="wheel_preset_steady"),
            ],
            [
                InlineKeyboardButton(text="Preset: Generous", callback_data="wheel_preset_generous"),
                InlineKeyboardButton(text="✍️ Ручные веса", callback_data="wheel_weights"),
            ],
            [InlineKeyboardButton(text=f"⚙️ Кулдаун ({cooldown_days}д)", callback_data="wheel_cd")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")],
        ]
    )

    await callback.message.edit_text(
        "🎰 <b>Настройки рулетки</b>\n\n"
        + f"<b>Preset:</b> {html.escape(preset)}\n\n"
        "<b>Шансы выигрыша:</b>\n"
        + "\n".join(prizes_text)
        + "\n\n"
        + f"<b>Кулдаун:</b> {cooldown_days} дней ({cooldown_hours}ч)",
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


def _live_update_public_link(row: LiveUpdate) -> str:
    channel = str(getattr(row, "channel_username", "") or "").strip().lstrip("@")
    post_id = int(getattr(row, "post_id", 0) or 0)
    if channel and post_id > 0:
        return f"https://t.me/{channel}/{post_id}"
    return str(getattr(row, "link", "") or "").strip()


@router.callback_query(F.data == "admin_live_updates")
async def admin_live_updates_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    s = Session()
    try:
        rows = (
            s.query(LiveUpdate)
            .order_by(LiveUpdate.sort_order.asc(), LiveUpdate.id.desc())
            .limit(15)
            .all()
        )
    finally:
        s.close()

    lines = ["📰 *Последние обновления*\n"]
    kb_rows: list[list[InlineKeyboardButton]] = []
    if not rows:
        lines.append("_Пока пусто_")
    for row in rows:
        status = "🟢" if bool(getattr(row, "is_active", False)) else "⚪"
        lines.append(
            f"{status} `{int(row.id)}` {row.title}\n"
            f"↳ {(_live_update_public_link(row) or '—')}"
        )
        kb_rows.append(
            [
                InlineKeyboardButton(
                    text=f"{'Выключить' if bool(row.is_active) else 'Включить'} #{int(row.id)}",
                    callback_data=f"admin_live_toggle_{int(row.id)}",
                )
            ]
        )

    kb_rows.extend(
        [
            [InlineKeyboardButton(text="➕ Добавить обновление", callback_data="admin_live_create")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")],
        ]
    )
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "admin_live_create")
async def admin_live_create_prompt(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    admin_pending_actions[ADMIN_ID] = {"action": "admin_live_create"}
    await callback.message.edit_text(
        "➕ *Новое обновление*\n\n"
        "Формат:\n"
        "`Заголовок|Краткое описание|@channel|123`\n\n"
        "Либо legacy-формат:\n"
        "`Заголовок|Краткое описание|https://t.me/...`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_live_updates")]]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_live_toggle_"))
async def admin_live_toggle(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    raw_id = str(callback.data or "").replace("admin_live_toggle_", "", 1)
    try:
        update_id = int(raw_id)
    except Exception:
        await callback.answer("Некорректный id", show_alert=True)
        return

    s = Session()
    try:
        row = s.query(LiveUpdate).filter(LiveUpdate.id == update_id).first()
        if not row:
            await callback.answer("Обновление не найдено", show_alert=True)
            return
        row.is_active = not bool(row.is_active)
        row.updated_at = _utcnow()
        s.commit()
    finally:
        s.close()
    await admin_live_updates_menu(callback)


@router.callback_query(F.data == "admin_start_links")
async def admin_start_links_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    s = Session()
    try:
        rows = s.query(StartLink).order_by(StartLink.updated_at.desc(), StartLink.id.desc()).limit(20).all()
    finally:
        s.close()

    bot_username = (BOT_USERNAME or "portal_privacy_bot").lstrip("@")
    lines = ["🔗 *Launch ссылки*\n"]
    kb_rows: list[list[InlineKeyboardButton]] = []
    if not rows:
        lines.append("_Пока пусто_")
    for row in rows:
        code = str(getattr(row, "code", "") or "").strip()
        state = "🟢" if bool(getattr(row, "is_active", False)) else "⚪"
        target = str(getattr(row, "target_action", "") or "").strip() or "—"
        lines.append(
            f"{state} `{int(row.id)}` `{code}` → `{target}`\n"
            f"↳ https://t.me/{bot_username}?start={code}"
        )
        kb_rows.append(
            [
                InlineKeyboardButton(
                    text=f"{'Деактивировать' if bool(row.is_active) else 'Активировать'} {code}",
                    callback_data=f"admin_start_toggle_{int(row.id)}",
                ),
                InlineKeyboardButton(
                    text=f"✏️ Изменить {code}",
                    callback_data=f"admin_start_edit_{int(row.id)}",
                ),
            ]
        )

    kb_rows.extend(
        [
            [InlineKeyboardButton(text="➕ Создать launch-ссылку", callback_data="admin_start_create")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")],
        ]
    )
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "admin_start_create")
async def admin_start_create_prompt(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    admin_pending_actions[ADMIN_ID] = {"action": "admin_start_create"}
    await callback.message.edit_text(
        "➕ *Создать launch-ссылку*\n\n"
        "Формат:\n"
        "`code|Описание|target_action`\n\n"
        "Примеры `target_action`:\n"
        "• `opening_bonus`\n"
        "• `promo:WELCOME14`\n"
        "• `campaign:launch_week_1`\n"
        "• `campaign_promo:launch_week_1:WELCOME14`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_start_links")]]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_start_edit_"))
async def admin_start_edit_prompt(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    raw_id = str(callback.data or "").replace("admin_start_edit_", "", 1)
    try:
        link_id = int(raw_id)
    except Exception:
        await callback.answer("Некорректный id", show_alert=True)
        return

    s = Session()
    try:
        row = s.query(StartLink).filter(StartLink.id == link_id).first()
        if not row:
            await callback.answer("Ссылка не найдена", show_alert=True)
            return
        code = str(getattr(row, "code", "") or "").strip()
        description = str(getattr(row, "description", "") or "").strip()
        target_action = str(getattr(row, "target_action", "") or "").strip()
    finally:
        s.close()

    admin_pending_actions[ADMIN_ID] = {"action": "admin_start_edit", "link_id": link_id}
    await callback.message.edit_text(
        "✏️ *Редактировать launch-ссылку*\n\n"
        f"Текущие значения:\n`{code}|{description}|{target_action}`\n\n"
        "Новый формат:\n"
        "`code|Описание|target_action`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_start_links")]]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_start_toggle_"))
async def admin_start_toggle(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    raw_id = str(callback.data or "").replace("admin_start_toggle_", "", 1)
    try:
        link_id = int(raw_id)
    except Exception:
        await callback.answer("Некорректный id", show_alert=True)
        return

    s = Session()
    try:
        row = s.query(StartLink).filter(StartLink.id == link_id).first()
        if not row:
            await callback.answer("Ссылка не найдена", show_alert=True)
            return
        row.is_active = not bool(row.is_active)
        row.updated_at = _utcnow()
        s.commit()
    finally:
        s.close()
    await admin_start_links_menu(callback)

# ==========================================
#         MASS ACTIONS
# ==========================================

@router.callback_query(F.data == "admin_mass")
async def admin_mass_actions(callback: CallbackQuery):
    """Show grouped bulk actions menu with explicit target counts."""
    if callback.from_user.id != ADMIN_ID:
        return
    
    session = Session()
    total = session.query(User).count()
    now = _utcnow()
    active = (
        session.query(User)
        .filter(User.is_active == True)
        .filter(User.expiry_at.isnot(None))
        .filter(User.expiry_at > now)
        .count()
    )
    inactive = total - active
    plan_rows = session.query(User.sub_type, func.count(User.tg_id)).group_by(User.sub_type).all()
    
    # Find users with expiring subscriptions (within 3 days)
    soon = now + timedelta(days=3)
    expiring = session.query(User).filter(
        User.is_active == True,
        User.expiry_at <= soon,
        User.expiry_at > now
    ).count()
    session.close()

    plan_lines = []
    for st, cnt in sorted(plan_rows, key=lambda x: str(x[0] or "")):
        plan_lines.append(f"• `{(st or '—')}`: {cnt}")
    plans_txt = "\n".join(plan_lines) if plan_lines else "—"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить дни активным", callback_data="mass_extend_active"),
            InlineKeyboardButton(text=f"📨 Отправить напоминание ({expiring})", callback_data="mass_remind_expiring"),
        ],
        [
            InlineKeyboardButton(text="🎁 +14 дней сегменту", callback_data="mass_promo_14"),
            InlineKeyboardButton(text="🔄 Синхронизировать с нодами", callback_data="mass_sync_nodes"),
        ],
        [InlineKeyboardButton(text="🧹 Нормализовать сегменты", callback_data="mass_normalize_plans")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]
    ])
    
    await callback.message.edit_text(
        f"📊 *Групповые действия*\n\n"
        f"Всего: {total}\n"
        f"✅ Активных сейчас: {active}\n"
        f"❌ Неактивных: {inactive}\n"
        f"⏳ Истекает в 3 дня: {expiring}\n\n"
        f"*Планы в БД:*\n{plans_txt}",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "mass_addgb_active")
async def mass_addgb_prompt(callback: CallbackQuery):
    """Legacy placeholder: traffic limits are not used."""
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.answer("Лимиты по трафику не используются.", show_alert=True)

@router.callback_query(F.data == "mass_extend_active")
async def mass_extend_prompt(callback: CallbackQuery):
    """Prompt for mass extend"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    admin_pending_actions[ADMIN_ID] = {"action": "mass_extend"}
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_mass")]
    ])
    
    await callback.message.edit_text(
        "📅 *Продлить всем активным*\n\n"
        "Введи количество дней:",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "mass_remind_expiring")
async def mass_remind_expiring(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return

    session = Session()
    now = _utcnow()
    soon = now + timedelta(days=3)
    try:
        users = session.query(User).filter(
            User.is_active == True,
            User.expiry_at <= soon,
            User.expiry_at > now
        ).all()
    finally:
        session.close()

    target = [u for u in users if u.tg_id not in PROTECTED_USERS and u.tg_id != ADMIN_ID]
    await callback.message.edit_text(
        f"⚠️ *Подтверждение действия*\n\n"
        f"Отправить напоминание об истечении.\n"
        f"Будет затронуто: *{len(target)}* пользователей.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_bulk_confirm_kb("mass_remind_expiring_run"),
    )
    await callback.answer()


@router.callback_query(F.data == "mass_remind_expiring_run")
async def mass_remind_expiring_run(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.answer("📤 Отправка...")

    session = Session()
    now = _utcnow()
    soon = now + timedelta(days=3)
    try:
        users = session.query(User).filter(
            User.is_active == True,
            User.expiry_at <= soon,
            User.expiry_at > now
        ).all()
    finally:
        session.close()

    sent = 0
    for user in users:
        if user.tg_id in PROTECTED_USERS or user.tg_id == ADMIN_ID:
            continue
        try:
            expiry = _naive_utc(user.expiry_at)
            days_left = (expiry - now).days if expiry and expiry > now else 0
            await bot.send_message(
                user.tg_id,
                f"⚠️ *Подписка истекает!*\n\n"
                f"Осталось {days_left} дней.\n\n"
                f"Продли сейчас, чтобы не потерять доступ!",
                parse_mode=ParseMode.MARKDOWN
            )
            sent += 1
        except:
            pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_mass")]
    ])

    await callback.message.edit_text(
        f"✅ *Готово*\n\n"
        f"Напоминание отправлено: *{sent}* пользователей.",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )


@router.callback_query(F.data == "mass_normalize_plans")
async def mass_normalize_plans(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    s = Session()
    try:
        users = s.query(User).order_by(User.created_at.asc()).all()
        preview_count = sum(
            1
            for u in users
            if u.tg_id not in PROTECTED_USERS
            and u.tg_id != ADMIN_ID
            and _normalize_sub_type((u.sub_type or "").strip()) != (u.sub_type or "").strip()
        )
    finally:
        s.close()

    if preview_count > 0:
        await callback.message.edit_text(
            f"⚠️ *Подтверждение действия*\n\n"
            f"Нормализовать сегменты (`sub_type`) по правилам.\n"
            f"Будет затронуто: *{preview_count}* пользователей.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_bulk_confirm_kb("mass_normalize_plans_run"),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "ℹ️ Нечего нормализовать: все сегменты уже в консистентном формате.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_mass")]]),
    )
    await callback.answer()


@router.callback_query(F.data == "mass_normalize_plans_run")
async def mass_normalize_plans_run(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.answer("⏳ Выполняю...")
    s = Session()
    try:
        users = s.query(User).order_by(User.created_at.asc()).all()
        changed = 0
        by_to: dict[tuple[str, str], int] = {}
        for u in users:
            if u.tg_id in PROTECTED_USERS or u.tg_id == ADMIN_ID:
                continue
            old = (u.sub_type or "").strip()
            new = _normalize_sub_type(old)
            if new and new != old:
                u.sub_type = new
                changed += 1
                key = (old or "—", new)
                by_to[key] = by_to.get(key, 0) + 1
        s.commit()
    finally:
        s.close()

    lines = ["🧹 *Нормализация сегментов*\n", f"Изменено: *{changed}*"]
    if by_to:
        lines.append("\n*Что поменялось:*")
        for (old, new), cnt in sorted(by_to.items(), key=lambda x: (-x[1], x[0][0], x[0][1]))[:12]:
            lines.append(f"• `{old}` → `{new}`: {cnt}")

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_mass")]])
    await callback.message.edit_text("\n".join(lines), reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()


@router.callback_query(F.data == "mass_promo_14")
async def mass_promo_14(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    s = Session()
    try:
        users = s.query(User).order_by(User.created_at.asc()).all()
        target_count = sum(
            1
            for u in users
            if u.tg_id not in PROTECTED_USERS
            and u.tg_id != ADMIN_ID
            and _normalize_sub_type((u.sub_type or "").strip()) != "MANUAL"
        )
    finally:
        s.close()

    await callback.message.edit_text(
        f"⚠️ *Подтверждение действия*\n\n"
        f"Добавить +14 дней сегменту (кроме MANUAL).\n"
        f"Будет затронуто: *{target_count}* пользователей.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_bulk_confirm_kb("mass_promo_14_run"),
    )
    await callback.answer()


@router.callback_query(F.data == "mass_promo_14_run")
async def mass_promo_14_run(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.answer("🎁 Выполняю...")
    await callback.message.edit_text(
        "🎁 *Промо: +14 дней сегменту*\n\n"
        "Обновляю БД и синхронизирую пользователей на ноды. Это может занять 10–60 секунд.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_mass")]]),
        parse_mode=ParseMode.MARKDOWN,
    )

    now = _utcnow()
    new_expiry = now + timedelta(days=14)

    s = Session()
    try:
        users = s.query(User).order_by(User.created_at.asc()).all()
        target: list[User] = []
        for u in users:
            st = (u.sub_type or "").strip()
            if _normalize_sub_type(st) == "MANUAL":
                continue
            if u.tg_id in PROTECTED_USERS or u.tg_id == ADMIN_ID:
                continue
            u.is_active = True
            u.expiry_at = new_expiry
            u.sub_type = "BONUS"
            target.append(u)
        s.commit()
    finally:
        s.close()

    # Sync to paid nodes (exclude free nodes by ControlPanel default).
    ok_total = 0
    fail_total = 0
    sem = asyncio.Semaphore(6)

    async def sync_one(u: User) -> bool:
        async with sem:
            try:
                sub_id = u.sub_token or str(u.tg_id)
                res = await panel.ensure_user_on_all_nodes(
                    tg_id=u.tg_id,
                    client_uuid=u.uuid,
                    email=u.email,
                    sub_id=sub_id,
                    enable=True,
                )
                return all(res.values()) if res else False
            except Exception:
                return False

    # We need fresh objects after session close. Re-query minimal fields.
    s = Session()
    try:
        rows = (
            s.query(User)
            .filter(func.upper(User.sub_type).in_(["PAID", "BONUS", "TRIAL", "FREE"]))
            .filter(User.tg_id != ADMIN_ID)
            .order_by(User.created_at.asc())
            .all()
        )
    finally:
        s.close()

    results = await asyncio.gather(*(sync_one(u) for u in rows))
    ok_total = sum(1 for r in results if r)
    fail_total = sum(1 for r in results if not r)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_mass")]])
    await callback.message.edit_text(
        "🎁 *Промо: +14 дней сегменту*\n\n"
        f"БД обновлена до: `{new_expiry.strftime('%Y-%m-%d')}`\n"
        f"✅ Sync OK: {ok_total}\n"
        f"❌ Sync Fail: {fail_total}\n"
        f"Сегмент после операции: `BONUS`",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(F.data == "mass_sync_nodes")
async def mass_sync_nodes(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    s = Session()
    try:
        users = s.query(User).order_by(User.created_at.asc()).all()
    finally:
        s.close()
    target_count = sum(1 for u in users if u.tg_id not in PROTECTED_USERS and u.tg_id != ADMIN_ID)

    await callback.message.edit_text(
        f"⚠️ *Подтверждение действия*\n\n"
        f"Синхронизировать сегмент с нодами.\n"
        f"Будет затронуто: *{target_count}* пользователей.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_bulk_confirm_kb("mass_sync_nodes_run"),
    )
    await callback.answer()


@router.callback_query(F.data == "mass_sync_nodes_run")
async def mass_sync_nodes_run(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.answer("🔄 Sync...")
    await callback.message.edit_text(
        "🔄 *Синхронизация пользователей с нодами*\n\nЗапускаю. Это может занять 10–60 секунд.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_mass")]]),
        parse_mode=ParseMode.MARKDOWN,
    )

    now = _utcnow()
    s = Session()
    try:
        users = s.query(User).order_by(User.created_at.asc()).all()
    finally:
        s.close()

    sem = asyncio.Semaphore(6)

    async def sync_one(u: User) -> bool:
        async with sem:
            try:
                st = _normalize_sub_type(u.sub_type)
                if st == "MANUAL":
                    return True
                expiry = _naive_utc(u.expiry_at)
                enable = bool(u.is_active and expiry and expiry > now)
                sub_id = u.sub_token or str(u.tg_id)
                only_codes = None
                if _is_freemium_sub_type(st):
                    only_codes = _bot_free_codes()
                    if not only_codes:
                        return False
                res = await panel.ensure_user_on_all_nodes(
                    tg_id=u.tg_id,
                    client_uuid=u.uuid,
                    email=u.email,
                    sub_id=sub_id,
                    enable=enable,
                    only_node_codes=only_codes,
                )
                return all(res.values()) if res else False
            except Exception:
                return False

    target = [u for u in users if u.tg_id not in PROTECTED_USERS and u.tg_id != ADMIN_ID]
    results = await asyncio.gather(*(sync_one(u) for u in target))
    ok = sum(1 for r in results if r)
    fail = sum(1 for r in results if not r)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_mass")]])
    await callback.message.edit_text(
        "🔄 *Синхронизация пользователей с нодами*\n\n"
        f"✅ OK: {ok}\n"
        f"❌ Fail: {fail}",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )

@router.callback_query(F.data == "admin_sync")
async def admin_sync_callback(callback: CallbackQuery, bot: Bot):
    """Trigger sync from button"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    await callback.answer("🔄 Синхронизация запущена...")
    
    session = Session()
    users = session.query(User).all()
    updated = 0
    
    for user in users:
        if user.tg_id in PROTECTED_USERS:
            continue
        try:
            chat = await bot.get_chat(user.tg_id)
            if chat.username:
                user.username = chat.username
                updated += 1
        except:
            pass
    
    session.commit()
    session.close()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]
    ])
    
    await callback.message.edit_text(
        f"✅ *Синхронизация завершена*\n\n"
        f"Обновлено: {updated} username'ов",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )

@router.callback_query(F.data.startswith("admin_users"))
async def show_admin_users(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещён")
        return
    
    # Params: admin_users[:page][:segment]
    page = 0
    segment = "all"  # all|active|expired|free
    parts = (callback.data or "").split(":")
    if len(parts) >= 2 and parts[1].isdigit():
        page = max(0, int(parts[1]))
    if len(parts) >= 3 and parts[2]:
        segment = parts[2]
    if segment not in {"all", "active", "expired", "free"}:
        segment = "all"

    now = _utcnow()
    per_page = 12
    offset = page * per_page

    session = Session()
    q = session.query(User)

    if segment == "active":
        q = q.filter(User.is_active == True).filter(User.expiry_at.isnot(None)).filter(User.expiry_at > now)
    elif segment == "expired":
        q = q.filter((User.is_active == False) | (User.expiry_at.is_(None)) | (User.expiry_at <= now))
    elif segment == "free":
        q = q.filter(func.upper(User.sub_type).in_(["FREE", "TRIAL", "BONUS"]))

    total = q.count()
    users = q.order_by(User.created_at.desc()).offset(offset).limit(per_page).all()
    session.close()
    
    pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, pages - 1)

    if not users:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Все", callback_data="admin_users:0:all"),
                    InlineKeyboardButton(text="Актив", callback_data="admin_users:0:active"),
                    InlineKeyboardButton(text="Бесплатный", callback_data="admin_users:0:free"),
                ],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")],
            ]
        )
        await callback.message.edit_text("👥 Пользователи\n\nПусто для выбранного фильтра.", reply_markup=kb)
        await callback.answer()
        return

    seg_label = {"all": "Все", "active": "Активные", "expired": "Истекшие", "free": "Бесплатный"}.get(segment, "Все")
    header = f"👥 <b>Пользователи</b> — {seg_label}\nВсего: {total} | Стр {page+1}/{pages}\n\n"

    lines: list[str] = []
    buttons: list[list[InlineKeyboardButton]] = []
    buttons.append(
        [
            InlineKeyboardButton(text="Все", callback_data="admin_users:0:all"),
            InlineKeyboardButton(text="Актив", callback_data="admin_users:0:active"),
            InlineKeyboardButton(text="Истек", callback_data="admin_users:0:expired"),
            InlineKeyboardButton(text="Бесплатный", callback_data="admin_users:0:free"),
        ]
    )

    for u in users:
        expiry = _naive_utc(u.expiry_at)
        is_active = bool(u.is_active and expiry and expiry > now)
        status = "✅" if is_active else "❌"
        uname = f"@{u.username}" if u.username else f"ID:{u.tg_id}"
        days_left = (expiry - now).days if expiry and expiry > now else 0
        plan = (u.sub_type or "—").upper()
        lines.append(f"{status} {html.escape(uname)} — {days_left}д — {html.escape(plan)}")
        label = f"{status} @{u.username}" if u.username else f"{status} {u.tg_id}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"adm_user_{u.tg_id}")])

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_users:{page-1}:{segment}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{pages}", callback_data="noop"))
    if (page + 1) < pages:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_users:{page+1}:{segment}"))
    buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin")])

    await callback.message.edit_text(
        header + "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wheel_preset_"))
async def admin_wheel_set_preset(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    preset = str(callback.data or "").replace("wheel_preset_", "", 1).strip().lower()
    weights = WHEEL_PRESETS.get(preset)
    if not weights:
        await callback.answer("Неизвестный preset", show_alert=True)
        return
    _save_wheel_config(weights=list(weights), preset=preset)
    audit_admin(ADMIN_ID, "admin_wheel_preset_set", meta=f"preset={preset}")
    await admin_wheel_settings(callback)


@router.callback_query(F.data == "wheel_weights")
async def admin_wheel_set_weights_prompt(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    admin_pending_actions[ADMIN_ID] = {"action": "wheel_weights"}
    await callback.message.edit_text(
        "✍️ *Ручные веса рулетки*\n\n"
        "Формат:\n"
        "`1:45,3:35,7:15,30:5`\n\n"
        "Где `дни:вес` через запятую.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_wheel")]]),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mass_extend_run_"))
async def mass_extend_run(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    raw_days = str(callback.data or "").replace("mass_extend_run_", "", 1).strip()
    try:
        days = int(raw_days)
    except Exception:
        await callback.answer("Некорректное число дней", show_alert=True)
        return
    if days < 1 or days > 3650:
        await callback.answer("Диапазон 1..3650", show_alert=True)
        return

    await callback.answer("⏳ Выполняю...")
    session = Session()
    now = _utcnow()
    try:
        users = (
            session.query(User)
            .filter(User.is_active == True)
            .filter(User.expiry_at.isnot(None))
            .filter(User.expiry_at > now)
            .all()
        )
        count = 0
        for user in users:
            if user.tg_id in PROTECTED_USERS or user.tg_id == ADMIN_ID:
                continue
            expiry = _naive_utc(user.expiry_at) or now
            user.expiry_at = expiry + timedelta(days=days)
            count += 1
        session.commit()
    finally:
        session.close()

    await callback.message.edit_text(
        f"✅ *Готово*\n\n"
        f"Добавлено по *{days}* дней.\n"
        f"Затронуто пользователей: *{count}*.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_mass")]]),
    )


def _bulk_confirm_kb(confirm_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data=confirm_cb)],
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_mass")],
        ]
    )


@router.callback_query(F.data == "wheel_cd")
async def admin_wheel_set_cooldown_prompt(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    admin_pending_actions[ADMIN_ID] = {"action": "wheel_cd"}
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_wheel")]])
    await callback.message.edit_text(
        "⚙️ *Кулдаун рулетки*\n\n"
        "Введи число дней (например `7`).",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()

@router.callback_query(F.data.startswith("adm_user_"))
async def admin_view_user(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещён")
        return
    
    tg_id = int(callback.data.replace("adm_user_", ""))
    await render_admin_user_view(callback, tg_id)

@router.callback_query(F.data.startswith("adm_add_days_"))
async def admin_add_days(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    
    parts = callback.data.split("_")
    tg_id = int(parts[3])
    days = int(parts[4])
    
    extend_user(tg_id, days, 0)
    if days >= 0:
        await callback.answer(f"✅ Добавлено {days} дней!")
    else:
        await callback.answer(f"✅ Списано {abs(days)} дней.")
    
    # Refresh user view - re-render directly
    await render_admin_user_view(callback, tg_id)

@router.callback_query(F.data.startswith("adm_add_gb_"))
async def admin_add_gb(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    
    parts = callback.data.split("_")
    tg_id = int(parts[3])
    gb = int(parts[4])
    
    user = get_user(tg_id)
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return

    # Keep handler for backward compatibility; policy is managed by plan/env.
    await panel.update_client_traffic(tg_id, 0)
    await callback.answer("ℹ️ Управление трафиком через эту кнопку отключено.", show_alert=True)
    
    # Refresh user view - re-render directly
    await render_admin_user_view(callback, tg_id)

@router.callback_query(F.data.startswith("adm_sub_gb_"))
async def admin_sub_gb(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    
    parts = callback.data.split("_")
    tg_id = int(parts[3])
    gb = int(parts[4])
    
    user = get_user(tg_id)
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return

    await panel.subtract_client_traffic(tg_id, 0)
    await callback.answer("ℹ️ Управление трафиком через эту кнопку отключено.", show_alert=True)
    
    # Refresh user view
    await render_admin_user_view(callback, tg_id)

@router.callback_query(F.data.startswith("adm_toggle_"))
async def admin_toggle_user(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    
    tg_id = int(callback.data.replace("adm_toggle_", ""))
    user = get_user(tg_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    # Toggle status
    new_status = not user.is_active
    session = Session()
    db_user = session.query(User).filter_by(tg_id=tg_id).first()
    if db_user:
        db_user.is_active = new_status
        session.commit()
    session.close()
    
    # Toggle in panel
    await panel.enable_client(user.uuid, new_status)
    audit_admin(callback.from_user.id, "toggle_user", tg_id, meta=f"new_status={int(new_status)}")
    
    status_text = "активирован" if new_status else "отключен"
    await callback.answer(f"✅ Пользователь {status_text}!")
    
    # Refresh user view - re-render directly
    await render_admin_user_view(callback, tg_id)


@router.callback_query(F.data.startswith("adm_sync_nodes_"))
async def admin_sync_user_nodes(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    tg_id = int((callback.data or "").replace("adm_sync_nodes_", ""))
    s = Session()
    try:
        u = s.query(User).filter_by(tg_id=tg_id).first()
    finally:
        s.close()

    if not u:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    sub_id = u.sub_token or str(u.tg_id)
    only_codes = None
    if _is_freemium_sub_type(u.sub_type):
        only_codes = _bot_free_codes()
        if not only_codes:
            await callback.answer("❌ Free pool не настроен", show_alert=True)
            return
    try:
        res = await panel.ensure_user_on_all_nodes(
            tg_id=u.tg_id,
            client_uuid=u.uuid,
            email=u.email,
            sub_id=sub_id,
            enable=bool(u.is_active),
            only_node_codes=only_codes,
        )
        ok = sum(1 for v in res.values() if v)
        fail = sum(1 for v in res.values() if not v)
        await callback.answer(f"🔁 Sync: OK {ok}, fail {fail}")
    except Exception:
        await callback.answer("❌ Ошибка sync (см. логи)", show_alert=True)

    await render_admin_user_view(callback, tg_id)


@router.callback_query(F.data.startswith("adm_send_link_"))
async def admin_send_user_link(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return

    tg_id = int((callback.data or "").replace("adm_send_link_", ""))
    u = get_user(tg_id)
    if not u:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    try:
        sub_link = build_subscription_link(tg_id)
        await bot.send_message(
            tg_id,
            "🔗 *Ваша ссылка подписки*\n\n"
            f"`{sub_link}`\n\n"
            "_Если приложение просит обновить профиль, просто обновите подписку внутри приложения._",
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer("📨 Отправлено")
    except Exception:
        await callback.answer("❌ Не удалось отправить (юзер заблокировал?)", show_alert=True)

    await render_admin_user_view(callback, tg_id)


@router.callback_query(F.data.startswith("adm_regen_token_"))
async def admin_regen_token(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    tg_id = int((callback.data or "").replace("adm_regen_token_", ""))
    token = regenerate_user_sub_token(tg_id)
    if not token:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    panel_sync_ok = await sync_user_panel_sub_token(tg_id)
    link = build_subscription_link(tg_id)
    audit_admin(callback.from_user.id, "regen_sub_token", tg_id)
    await callback.answer("♻️ Токен перевыпущен")
    await callback.message.answer(
        f"♻️ Новый ключ пользователя `{tg_id}`:\n`{link}`\n\n"
        f"Sync с нодами: {'OK' if panel_sync_ok else 'WARN (проверьте adm_sync_nodes)'}",
        parse_mode=ParseMode.MARKDOWN,
    )
    await render_admin_user_view(callback, tg_id)


@router.callback_query(F.data.startswith("adm_msg_user_"))
async def admin_message_user_prompt(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    tg_id = int((callback.data or "").replace("adm_msg_user_", ""))
    u = get_user(tg_id)
    if not u:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    admin_pending_actions[ADMIN_ID] = {"action": "admin_dm_capture", "target_tg_id": tg_id}
    await callback.message.edit_text(
        f"✉️ *Сообщение пользователю* `{tg_id}`\n\n"
        "Отправь следующим сообщением текст, фото, видео или документ.\n"
        "Я перешлю его пользователю как есть.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="◀️ Отмена", callback_data=f"adm_user_{tg_id}")]]
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "mode_pro")
async def mode_pro_start(callback: CallbackQuery):
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    if _channel_bonus_eligible(tg_id=tg_id, user=user):
        await _show_channel_bonus_offer(callback, next_action="main")
        return

    await callback.message.edit_text(
        "💀 *Ручной режим уже активен*\n\nОткрываю основное меню.",
        reply_markup=main_keyboard(tg_id),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer("Вы уже в ручном режиме", show_alert=False)


@router.callback_query(F.data == "mode_simple")
async def mode_simple_start(callback: CallbackQuery):
    text = (
        "🪄 *Магия Автопилота*\n\n"
        "Вам не нужно разбираться в технологиях.\n"
        "Мы всё сделаем за 3 шага.\n\n"
        "👇 *Какое у вас устройство?*"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍏 iPhone / iPad", callback_data="simple_ios")],
        [InlineKeyboardButton(text="🤖 Android", callback_data="simple_android")],
        [InlineKeyboardButton(text="💻 Компьютер", callback_data="simple_pc")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()


@router.callback_query(F.data.in_({"simple_ios", "simple_android", "simple_pc"}))
async def mode_simple_step2(callback: CallbackQuery):
    mode = callback.data or ""
    if mode == "simple_ios":
        app_name = "Streisand"
        app_link = IOS_APP_LINK
    elif mode == "simple_android":
        app_name = "Hiddify"
        app_link = ANDROID_APP_LINK
    else:
        app_name = "Hiddify"
        app_link = WINDOWS_APP_LINK

    text = (
        f"1️⃣ *Шаг 1: Скачайте приложение*\n\n"
        f"Для работы нужен клиент *{app_name}*.\n"
        "Установите приложение и вернитесь в бот.\n\n"
        "👇 Нажмите, чтобы скачать."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📥 Скачать {app_name}", url=app_link)],
        [_button_from_spec(_btn_spec(
            text="✅ Я установил(а), дальше",
            callback_data="simple_step3",
            style=BTN_STYLE_SUCCESS,
            icon_custom_emoji_id=BTN_EMOJI_SUCCESS_ID or None,
        ))],
        [_button_from_spec(_btn_spec(
            text="⛔ Отмена",
            callback_data="mode_simple",
            style=BTN_STYLE_DANGER,
            icon_custom_emoji_id=BTN_EMOJI_DANGER_ID or None,
        ))],
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()


@router.callback_query(F.data == "simple_step3")
async def mode_simple_step3(callback: CallbackQuery):
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    if _channel_bonus_eligible(tg_id=tg_id, user=user):
        await _show_channel_bonus_offer(callback, next_action="simple")
        return
    await _render_mode_simple_step3(callback)


async def _render_mode_simple_step3(callback: CallbackQuery) -> None:
    starter_price = int(TARIFFS["1_month"]["stars"])
    recommended_price = int(TARIFFS["6_months"]["stars"])
    text = (
        "2️⃣ *Шаг 2: Активация*\n\n"
        "Теперь нужно создать ваш ключ доступа.\n"
        "Рекомендуем тариф на 6 месяцев: лучший баланс цены и срока.\n\n"
        "Нажмите кнопку ниже."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⚡ Рекомендуем: 6 месяцев за {recommended_price} ⭐", callback_data="buy_6_months")],
        [InlineKeyboardButton(text=f"🚀 Начать с 1 месяца за {starter_price} ⭐", callback_data="buy_1_month")],
        [InlineKeyboardButton(text="🤔 Выбрать другой тариф", callback_data="charge")],
        [InlineKeyboardButton(text=f"🎁 {CHANNEL_PREMIUM_DAYS} дней премиум за канал", callback_data="bonus_offer_trial")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="mode_simple")],
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()


async def _activate_trial_tariff(
    callback: CallbackQuery,
    bot: Bot,
    *,
    retry_callback_data: str = "buy_trial",
) -> None:
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    tariff = TARIFFS["trial"]

    is_subscribed = await check_subscription(tg_id, bot)
    if not is_subscribed:
        channel_name = _channel_name_for_url()
        await callback.message.answer(
            "⚡ *Базовый профиль FREE активируется без блокировки.*\n\n"
            "Если подпишетесь на канал, получите приоритетный профиль и бонусы.\n"
            f"Канал: https://t.me/{channel_name}",
            parse_mode=ParseMode.MARKDOWN,
        )

    now = _utcnow()
    current_sub = _normalize_sub_type(user.sub_type if user else "")
    expiry = _naive_utc(user.expiry_at) if user else None
    has_active = bool(user and user.is_active and expiry and expiry > now)
    if has_active and _is_freemium_sub_type(current_sub):
        await callback.answer("Бесплатный режим уже активен. Повторная активация не требуется.", show_alert=True)
        return
    if has_active and not _is_freemium_sub_type(current_sub):
        await callback.answer("У вас уже активирован полный доступ. Бесплатный режим не требуется.", show_alert=True)
        return

    await callback.answer("⏳ Включаю бесплатный режим...")
    await create_subscription(callback.message, tg_id, tariff, bot)


def _parse_bonus_next_action(data: str, prefix: str) -> str | None:
    raw = (data or "").replace(prefix, "", 1).strip().lower()
    if raw in {"main", "simple", "trial"}:
        return raw
    return None


async def _resume_after_bonus_prompt(callback: CallbackQuery, bot: Bot, *, next_action: str) -> None:
    tg_id = callback.from_user.id
    if next_action == "trial":
        await _activate_trial_tariff(callback, bot, retry_callback_data="trial_direct")
        return
    if next_action == "simple":
        await _render_mode_simple_step3(callback)
        return

    await callback.message.edit_text(
        "✅ Продолжаем без бонуса.\n\nОткрываю основное меню.",
        reply_markup=main_keyboard(tg_id),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bonus_offer_"))
async def channel_bonus_offer(callback: CallbackQuery):
    next_action = _parse_bonus_next_action(callback.data or "", "bonus_offer_")
    if not next_action:
        await callback.answer("Некорректный шаг", show_alert=True)
        return
    await _show_channel_bonus_offer(callback, next_action=next_action)


@router.callback_query(F.data.startswith("bonus_claim_"))
async def channel_bonus_claim(callback: CallbackQuery, bot: Bot):
    next_action = _parse_bonus_next_action(callback.data or "", "bonus_claim_")
    if not next_action:
        await callback.answer("Некорректный шаг", show_alert=True)
        return

    tg_id = callback.from_user.id
    user = get_user(tg_id)
    ineligible_reason = _channel_bonus_ineligible_reason(tg_id=tg_id, user=user)
    if ineligible_reason:
        await callback.answer(ineligible_reason, show_alert=True)
        await _resume_after_bonus_prompt(callback, bot, next_action=next_action)
        return

    activated, reason = await _activate_channel_bonus(message=callback.message, bot=bot, tg_id=tg_id)
    if activated:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔑 Мой ключ", callback_data="show_key")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back")],
            ]
        )
        await callback.message.edit_text(
            f"✅ *Бонус активирован*\n\nПремиум-доступ выдан на *{CHANNEL_PREMIUM_DAYS} дней*.",
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer("Готово")
        return

    if reason == "not_subscribed":
        await callback.message.edit_text(
            "⚠️ Сначала подпишитесь на канал, затем нажмите «Проверить и получить».",
            reply_markup=_channel_bonus_keyboard(next_action),
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer()
        return
    if reason == "tos_required":
        await callback.message.edit_text(
            "⚠️ Сначала примите условия оферты, затем активируйте бонус.",
            reply_markup=_tos_offer_keyboard(back_callback=f"bonus_offer_{next_action}"),
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer()
        return

    await callback.answer("Не удалось активировать бонус, продолжаем без него.", show_alert=True)
    await _resume_after_bonus_prompt(callback, bot, next_action=next_action)


@router.callback_query(F.data.startswith("bonus_skip_"))
async def channel_bonus_skip(callback: CallbackQuery, bot: Bot):
    next_action = _parse_bonus_next_action(callback.data or "", "bonus_skip_")
    if not next_action:
        await callback.answer("Некорректный шаг", show_alert=True)
        return
    await _resume_after_bonus_prompt(callback, bot, next_action=next_action)


@router.callback_query(F.data == "trial_direct")
async def trial_direct(callback: CallbackQuery, bot: Bot):
    await _activate_trial_tariff(callback, bot, retry_callback_data="trial_direct")


async def render_admin_user_view(callback: CallbackQuery, tg_id: int):
    """Render admin user detail view - reusable helper"""
    user = get_user(tg_id)
    
    if not user:
        return
    
    uname = f"@{user.username}" if user.username else "—"
    now = _utcnow()
    expiry = _naive_utc(user.expiry_at)
    is_active = bool(user.is_active and expiry and expiry > now)
    status = "✅ Активен" if is_active else "❌ Неактивен"
    expiry_txt = expiry.strftime("%d.%m.%Y") if expiry else "—"
    days_left = (expiry - now).days if expiry and expiry > now else 0
    plan = (user.sub_type or "—").upper()
    manual_name = (getattr(user, "display_name", None) or "").strip()
    is_manual = bool(getattr(user, "is_manual", False) or plan == "MANUAL" or user.tg_id < 0)
    free_usage_line = ""
    if _is_freemium_sub_type(plan):
        remaining_gb, total_gb = await _free_remaining_gb(tg_id)
        if remaining_gb is None:
            free_usage_line = f"\n📊 Бесплатный остаток: <b>н/д</b> из <b>{int(total_gb)} ГБ</b>"
        else:
            free_usage_line = f"\n📊 Бесплатный остаток: <b>{remaining_gb} ГБ</b> из <b>{int(total_gb)} ГБ</b>"
    panel_snapshot = await _panel_online_snapshot(tg_id)
    panel_online_line = html.escape(_panel_online_text(panel_snapshot))
    panel_last_online_line = html.escape(_panel_last_online_text(panel_snapshot))

    manual_line = f"🏷 Имя: <b>{html.escape(manual_name)}</b>\n" if manual_name else ""

    text = (
        f"<b>👤 Пользователь</b>\n\n"
        f"🆔 ID: <code>{tg_id}</code>\n"
        f"📝 Ник: {html.escape(uname)}\n"
        f"{manual_line}"
        f"📦 Тариф: <b>{html.escape(plan)}</b>\n"
        f"🧩 Тип: <b>{'MANUAL' if is_manual else 'TELEGRAM'}</b>\n"
        f"🔋 Статус: {html.escape(status)}\n\n"
        f"📅 До: <b>{html.escape(expiry_txt)}</b> ({days_left} дн.)\n"
        f"📡 Режим: <b>{html.escape(_plan_mode_label(plan))}</b>\n"
        f"🌐 Онлайн: <b>{panel_online_line}</b>\n"
        f"🕓 Последний онлайн: <b>{panel_last_online_line}</b>\n"
        f"⭐ Stars: <b>{int(user.stars_paid or 0)}</b>"
        f"{free_usage_line}"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ 7 дней", callback_data=f"adm_add_days_{tg_id}_7"),
            InlineKeyboardButton(text="➕ 30 дней", callback_data=f"adm_add_days_{tg_id}_30")
        ],
        [
            InlineKeyboardButton(text="➖ 7 дней", callback_data=f"adm_add_days_{tg_id}_-7"),
            InlineKeyboardButton(text="➖ 30 дней", callback_data=f"adm_add_days_{tg_id}_-30"),
        ],
        [InlineKeyboardButton(text="🔁 Sync на ноды", callback_data=f"adm_sync_nodes_{tg_id}")],
        [
            InlineKeyboardButton(text="📨 Отправить ссылку", callback_data=f"adm_send_link_{tg_id}"),
            InlineKeyboardButton(text="✉️ Сообщение", callback_data=f"adm_msg_user_{tg_id}"),
        ],
        [InlineKeyboardButton(text="🎫 Сменить тариф", callback_data=f"adm_tariff_{tg_id}")],
        [
            InlineKeyboardButton(
                text="🔓 Активировать" if not user.is_active else "🔒 Отключить",
                callback_data=f"adm_toggle_{tg_id}"
            )
        ],
        [InlineKeyboardButton(text="♻️ Перевыпустить токен", callback_data=f"adm_regen_token_{tg_id}")],
        [
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"adm_del_{tg_id}")
        ],
        [InlineKeyboardButton(text="◀️ К списку", callback_data="admin_manual_list" if is_manual else "admin_users")]
    ])
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

@router.callback_query(F.data.startswith("adm_tariff_"))
async def admin_tariff_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    
    tg_id = int(callback.data.replace("adm_tariff_", ""))
    
    p1 = int(TARIFFS["1_month"]["stars"])
    p3 = int(TARIFFS["3_months"]["stars"])
    p6 = int(TARIFFS["6_months"]["stars"])
    p9 = int(TARIFFS["9_months"]["stars"])
    p12 = int(TARIFFS["12_months"]["stars"])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Бесплатный (соцсети + AI)", callback_data=f"adm_set_{tg_id}_trial")],
        [InlineKeyboardButton(text=f"📅 1 Месяц ({p1} ⭐)", callback_data=f"adm_set_{tg_id}_1_month")],
        [InlineKeyboardButton(text=f"📅 3 Месяца ({p3} ⭐)", callback_data=f"adm_set_{tg_id}_3_months")],
        [InlineKeyboardButton(text=f"📅 6 Месяцев ({p6} ⭐)", callback_data=f"adm_set_{tg_id}_6_months")],
        [InlineKeyboardButton(text=f"📅 9 Месяцев ({p9} ⭐)", callback_data=f"adm_set_{tg_id}_9_months")],
        [InlineKeyboardButton(text=f"📅 1 Год ({p12} ⭐)", callback_data=f"adm_set_{tg_id}_12_months")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"adm_user_{tg_id}")]
    ])
    
    await callback.message.edit_text(
        f"🎫 *Выберите тариф для пользователя* `{tg_id}`:",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "admin_gift_menu")
async def admin_gift_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    
    mini_price = int(GIFT_CARD_TYPES["mini"]["stars"])
    standard_price = int(GIFT_CARD_TYPES["standard"]["stars"])
    premium_price = int(GIFT_CARD_TYPES["premium"]["stars"])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎫 Создать Mini (7д / {mini_price}⭐)", callback_data="admin_giftcode_mini")],
        [InlineKeyboardButton(text=f"🎫 Создать Standard (30д / {standard_price}⭐)", callback_data="admin_giftcode_standard")],
        [InlineKeyboardButton(text=f"🎫 Создать Premium (90д / {premium_price}⭐)", callback_data="admin_giftcode_premium")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]
    ])
    
    await callback.message.edit_text(
        "🎁 *Подарки для пользователей*\n\n"
        "Основной поток: *gift-коды* (удобно и безопасно).\n"
        "Создайте код кнопками выше или командой:\n"
        "`/giftcode mini`\n"
        "`/giftcode standard`\n"
        "`/giftcode premium`\n"
        "`/giftcode standard 5` _(пакет 5 кодов)_\n\n"
        "Прямая выдача `/gift` остаётся как резервный ручной инструмент.",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_giftcode_"))
async def admin_giftcode_create_from_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    card_type = (callback.data or "").replace("admin_giftcode_", "", 1).strip().lower()
    if card_type not in GIFT_CARD_TYPES:
        await callback.answer("Неизвестный тип gift-кода", show_alert=True)
        return
    code = create_gift_card(ADMIN_ID, card_type)
    if not code:
        await callback.answer("Не удалось создать код", show_alert=True)
        return
    card = GIFT_CARD_TYPES.get(card_type, {})
    await callback.message.answer(
        f"🎫 *Новый gift-код*\n\n"
        f"Код: `{code}`\n"
        f"Тип: {card.get('name', card_type)}\n"
        f"Срок: {int(card.get('days', 0))} дн.\n\n"
        f"Для активации: `/redeem {code}`",
        parse_mode=ParseMode.MARKDOWN,
    )
    audit_admin(ADMIN_ID, "admin_gift_code_create", meta=f"card_type={card_type}; code={code}")
    await callback.answer("Gift-код создан")

@router.callback_query(F.data.startswith("adm_set_"))
async def admin_set_tariff(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return
    
    parts = callback.data.split("_")
    tg_id = int(parts[2])
    # Handle keys with underscores like 1_month (parts[3] + parts[4]?)
    # callback data: adm_set_{tg_id}_{key}
    # split("_"): ["adm", "set", "123", "1", "month"] -> len 5
    # trial -> len 4
    
    if len(parts) >= 5:
        tariff_key = f"{parts[3]}_{parts[4]}"
    else:
        tariff_key = parts[3]

    # Pre-defined presets logic based on TARIFFS constant to avoid duplication
    preset = None
    if tariff_key in TARIFFS:
        t = TARIFFS[tariff_key]
        preset = {"days": t["days"], "gb": t["gb"], "name": t["name"]}
    
    if not preset:
        await callback.answer("❌ Тариф не найден")
        return
    
    user = get_user(tg_id)
    if user:
        target_sub = _normalize_sub_type(t.get("sub_type") or tariff_key)
        old_sub = _normalize_sub_type(user.sub_type)
        if _is_freemium_sub_type(old_sub) and target_sub == "PAID":
            reset_user_expiry_from_now(tg_id, preset["days"], 0)
        else:
            # Default behavior: extend from current expiry.
            extend_user(tg_id, preset["days"], 0)
        
        # Update plan in DB (keep internal sub_type consistent with TARIFFS, so wheel/logic works).
        session = Session()
        db_user = session.query(User).filter_by(tg_id=tg_id).first()
        if db_user:
            db_user.sub_type = t.get("sub_type") or tariff_key.upper()
            db_user.total_gb = preset["gb"]
            if _is_freemium_sub_type(db_user.sub_type):
                mark_user_became_free(db_user)
            session.commit()
        session.close()
        
        # SET traffic on panel (not add) - this resets used to 0 and sets new limit
        await panel.set_tariff_traffic(tg_id, preset["gb"])
        
        await callback.answer(f"✅ Установлен тариф: {preset['name']}")
    else:
        await callback.answer("❌ Пользователь не найден")
        return
    
    # Refresh user view
    await render_admin_user_view(callback, tg_id)

@router.callback_query(F.data.startswith("adm_reset_"))
async def admin_reset_traffic(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    
    tg_id = int(callback.data.replace("adm_reset_", ""))
    
    # Legacy: traffic limits are not used anymore (kept to avoid breaking older callback links).
    await panel.reset_client_traffic(tg_id)
    await callback.answer("ℹ️ Лимиты по трафику отключены.", show_alert=True)
    
    # Refresh user view
    await render_admin_user_view(callback, tg_id)

@router.callback_query(F.data.startswith("adm_del_"))
async def admin_delete_user(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    
    tg_id = int(callback.data.replace("adm_del_", ""))
    
    # Delete from panel
    await panel.delete_client(tg_id)
    
    # Delete from DB
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    if user:
        session.delete(user)
        session.commit()
    session.close()
    
    audit_admin(callback.from_user.id, "delete_user", tg_id)
    
    await callback.answer(f"✅ Пользователь {tg_id} удалён!")
    
    # Go back to paged list (re-render)
    callback_copy = callback
    callback_copy._data = "admin_users:0:all"
    await show_admin_users(callback_copy)



@router.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: CallbackQuery, bot: Bot):
    raw_key = callback.data.replace("buy_", "")
    tariff_key = normalize_tariff_key(raw_key)
    tariff = TARIFFS.get(tariff_key)
    
    if not tariff:
        await callback.answer("❌ Тариф не найден")
        return
    
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    
    # Calculate price with referral discount (20% off on first paid purchase)
    use_discount = has_referral_discount(tg_id) if tariff["stars"] > 0 else False
    pending_discount_pct = get_pending_discount_pct(tg_id) if tariff["stars"] > 0 else 0
    base_price = int(tariff["stars"])
    actual_stars = int(base_price)
    if use_discount:
        actual_stars = int(round(actual_stars * 0.8))
    if pending_discount_pct > 0:
        actual_stars = int(round(actual_stars * (1.0 - (pending_discount_pct / 100.0))))
    actual_stars = max(1, int(actual_stars))
    
    if tariff_key == "trial":
        if _channel_bonus_eligible(tg_id=tg_id, user=user):
            await _show_channel_bonus_offer(callback, next_action="trial")
            return
        await _activate_trial_tariff(callback, bot, retry_callback_data="buy_trial")
        return
    
    # Paid - send invoice (stack first-purchase + points, capped to 70% total discount).
    await callback.answer()
    first_discount_pct = 0.0
    if base_price > 0:
        first_discount_pct = max(0.0, min(0.95, 1.0 - (float(actual_stars) / float(base_price))))
    points_preview = preview_redeemable_points(
        tg_id=tg_id,
        plan_price_stars=int(tariff["stars"]),
        first_purchase_discount_pct=first_discount_pct,
    )
    points_to_use = int(points_preview.redeemable_points)
    final_stars = max(1, int(actual_stars) - points_to_use)
    max_total_discount = int(int(tariff["stars"]) * STACK_TOTAL_DISCOUNT_CAP)
    if int(tariff["stars"]) - final_stars > max_total_discount:
        final_stars = max(1, int(tariff["stars"]) - max_total_discount)
        points_to_use = max(0, int(actual_stars) - final_stars)

    mode_label = "disc" if use_discount else "full"
    attempt = start_attempt(
        tg_id=tg_id,
        source="bot",
        plan_code=tariff_key,
        amount_stars=final_stars,
        currency="XTR",
    )
    if not attempt:
        await callback.message.answer("❌ Не удалось создать попытку оплаты. Попробуйте позже.")
        return

    invoice_payload = f"portal_{tariff_key}_{tg_id}_{mode_label}_a{int(attempt.id)}_p{int(points_to_use)}"
    mark_invoice_sent(attempt_id=int(attempt.id), set_invoice_payload=invoice_payload)

    discount_chunks = []
    if use_discount:
        discount_chunks.append("-20% реф")
    if pending_discount_pct > 0:
        discount_chunks.append(f"-{pending_discount_pct}% промо")
    discount_note = f" ({', '.join(discount_chunks)})" if discount_chunks else ""
    points_note = f" + points -{points_to_use}⭐" if points_to_use > 0 else ""
    prices = [LabeledPrice(label=tariff["name"] + discount_note + points_note, amount=int(final_stars))]
    description = f"Безлимит на {tariff['days']} дней{discount_note}{points_note}"
    track_event(
        tg_id=tg_id,
        event_name="clicked_pay",
        source="bot",
        meta={
            "attempt_id": int(attempt.id),
            "plan_code": tariff_key,
            "base_price": int(base_price),
            "discounted_price": int(actual_stars),
            "promo_discount_pct": int(pending_discount_pct),
            "points_used": int(points_to_use),
            "final_price": int(final_stars),
        },
    )
    await bot.send_invoice(
        chat_id=tg_id,
        title=f"Портал: {tariff['name']}",
        description=description,
        payload=invoice_payload,
        provider_token="",
        currency="XTR",
        prices=prices
    )
    await callback.message.answer(
        "💳 Счёт открыт. После оплаты я автоматически выдам доступ.\n\n"
        "Если закрыли окно оплаты, нажмите «Проверить оплату».",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Проверить оплату", callback_data="status")],
                [InlineKeyboardButton(text="◀️ К тарифам", callback_data="charge")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back")],
            ]
        ),
    )

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)

@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def payment_success(message: Message, bot: Bot):
    payment = message.successful_payment
    payload = payment.invoice_payload
    payment_fingerprint = _telegram_payment_fingerprint(payment)
    logger.info(
        "payment_success: from_tg=%s amount=%s currency=%s payload=%s",
        message.from_user.id if message.from_user else None,
        payment.total_amount,
        payment.currency,
        payload,
    )
    if payment_fingerprint and _stars_payment_already_processed(payment_fingerprint):
        logger.info("payment_success duplicate ignored payload=%s fp=%s", payload, payment_fingerprint)
        return

    # Handle gift card purchase
    if payload.startswith("giftcard_"):
        gift_raw = payload[len("giftcard_"):]
        try:
            card_type, buyer_raw = gift_raw.rsplit("_", 1)
            buyer_tg_id = int(buyer_raw)
        except Exception:
            logger.warning("payment_success giftcard parse error payload=%s", payload)
            await message.answer("❌ Ошибка обработки оплаты. Напиши в поддержку.")
            return
        
        code = create_gift_card(buyer_tg_id, card_type)
        if code:
            card_info = GIFT_CARD_TYPES.get(card_type, {})
            _mark_stars_payment_processed(
                payment_fingerprint=payment_fingerprint,
                invoice_payload=payload,
                tg_id=buyer_tg_id,
            )
            await message.answer(
                f"🎁 *Подарочная карта куплена!*\n\n"
                f"Код: `{code}`\n\n"
                f"📦 {card_info.get('days', 0)} дней (Безлимит)\n\n"
                f"Отправь этот код другу!\n"
                f"Он активирует его командой `/redeem {code}`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            logger.warning("payment_success giftcard create failed buyer_tg_id=%s card_type=%s", buyer_tg_id, card_type)
            await message.answer("❌ Ошибка создания карты. Напиши в поддержку.")
        return

    # Handle family-slot purchase
    if payload.startswith("familyslot_"):
        try:
            buyer_tg_id = int(payload.replace("familyslot_", "", 1))
        except Exception:
            await message.answer("❌ Ошибка обработки family-слота.")
            return
        ok, total = add_family_slot_pack(buyer_tg_id, slots=1, days=FAMILY_SLOT_DAYS)
        if not ok:
            await message.answer(f"⚠️ Лимит family-слотов достигнут (+{FAMILY_SLOT_MAX}).")
            return
        _mark_stars_payment_processed(
            payment_fingerprint=payment_fingerprint,
            invoice_payload=payload,
            tg_id=buyer_tg_id,
        )
        await message.answer(
            f"✅ Family-слот активирован.\n\n"
            f"Добавлено: +1 устройство на {FAMILY_SLOT_DAYS} дней\n"
            f"Текущий доп.лимит: +{total}",
        )
        track_event(
            tg_id=buyer_tg_id,
            event_name="paid",
            source="bot",
            meta={"plan_code": "family_slot", "amount_stars": int(payment.total_amount), "family_slots": int(total)},
        )
        return
    
    # Handle regular tariff purchase
    if payload.startswith("portal_"):
        portal_raw = payload[len("portal_"):]
        try:
            # Backward-compatible payload parser:
            # portal_{tariff}_{tg_id}_{mode}
            # portal_{tariff}_{tg_id}_{mode}_a{attempt_id}_p{points_used}
            match = re.match(
                r"^(?P<tariff>.+)_(?P<tg_id>\d+)_(?P<mode>[a-z]+)(?:_a(?P<attempt_id>\d+))?(?:_p(?P<points>\d+))?$",
                portal_raw,
            )
            if not match:
                raise ValueError("bad payload")
            tariff_key = normalize_tariff_key(str(match.group("tariff") or ""))
            tg_id = int(match.group("tg_id"))
            attempt_id = int(match.group("attempt_id")) if match.group("attempt_id") else None
            points_used = max(0, int(match.group("points"))) if match.group("points") else 0
        except Exception:
            logger.warning("payment_success portal parse error payload=%s", payload)
            await message.answer("❌ Ошибка обработки оплаты. Напиши в поддержку.")
            return

        tariff = TARIFFS.get(tariff_key)
        
        if tariff:
            attempt = get_attempt_by_payload(invoice_payload=payload)
            if attempt and str(getattr(attempt, "status", "") or "").strip().lower() == "paid":
                logger.info("payment_success duplicate portal payload=%s attempt_id=%s", payload, getattr(attempt, "id", None))
                _mark_stars_payment_processed(
                    payment_fingerprint=payment_fingerprint,
                    invoice_payload=payload,
                    tg_id=tg_id,
                )
                return
            logger.info("payment_success portal parsed: tg_id=%s tariff_key=%s stars=%s", tg_id, tariff_key, tariff.get("stars"))
            mark_paid(attempt_id=attempt_id, invoice_payload=payload)
            if points_used > 0:
                spend_points(tg_id=tg_id, amount=int(points_used), pay_attempt_id=attempt_id, reason="payment_redeem")
            track_event(
                tg_id=tg_id,
                event_name="paid",
                source="bot",
                meta={
                    "attempt_id": attempt_id,
                    "plan_code": tariff_key,
                    "invoice_payload": payload,
                    "amount_stars": int(payment.total_amount),
                    "points_used": int(points_used),
                },
            )
            await message.answer(TEXTS["payment_success"])
            await create_subscription(message, tg_id, tariff, bot, paid_amount_stars=int(payment.total_amount), pay_attempt_id=attempt_id)
            _mark_stars_payment_processed(
                payment_fingerprint=payment_fingerprint,
                invoice_payload=payload,
                tg_id=tg_id,
            )
            receipt_text = (
                "🧾 *Квитанция об оплате*\n"
                "➖➖➖➖➖➖➖➖➖➖\n"
                f"📦 Товар: *{tariff['name']}*\n"
                f"💳 Сумма: *{payment.total_amount} XTR*\n"
                f"📅 Дата: *{datetime.utcnow().strftime('%d.%m.%Y %H:%M')} UTC*\n"
                f"🆔 TransID: `{payload}`\n"
                "➖➖➖➖➖➖➖➖➖➖\n"
                "✅ *Лицензия активирована успешно*"
            )
            receipt_rows = [[
                _btn_spec(
                    text="✅ Готово",
                    callback_data="show_key",
                    style=BTN_STYLE_SUCCESS,
                    icon_custom_emoji_id=BTN_EMOJI_SUCCESS_ID or None,
                )
            ]]
            ok = await _send_text_with_specs(
                bot=bot,
                chat_id=tg_id,
                text=receipt_text,
                rows=receipt_rows,
                parse_mode=ParseMode.MARKDOWN,
            )
            if not ok:
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="🔑 Получить ключи", callback_data="show_key")]]
                )
                await message.answer(receipt_text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        else:
            logger.warning("payment_success unknown tariff_key=%s payload=%s", tariff_key, payload)
        return

    # Fallback for legacy/non-standard payloads:
    # resolve the newest pending pay attempt by user + amount.
    payer_tg_id = message.from_user.id if message.from_user else 0
    fallback_attempt = resolve_pending_attempt_for_payment(
        tg_id=int(payer_tg_id),
        amount_stars=int(payment.total_amount),
        currency=str(payment.currency or "XTR"),
        within_hours=24,
    )
    if fallback_attempt:
        tariff_key = normalize_tariff_key(str(fallback_attempt.plan_code or ""))
        tariff = TARIFFS.get(tariff_key)
        if tariff:
            logger.info(
                "payment_success fallback resolved: tg_id=%s attempt_id=%s plan=%s payload=%s",
                payer_tg_id,
                fallback_attempt.id,
                tariff_key,
                payload,
            )
            # Persist real payload to the attempt for traceability, then mark as paid.
            mark_invoice_sent(attempt_id=int(fallback_attempt.id), set_invoice_payload=payload)
            mark_paid(attempt_id=int(fallback_attempt.id), invoice_payload=payload)
            track_event(
                tg_id=int(payer_tg_id),
                event_name="paid",
                source="bot",
                meta={
                    "attempt_id": int(fallback_attempt.id),
                    "plan_code": tariff_key,
                    "invoice_payload": payload,
                    "amount_stars": int(payment.total_amount),
                    "recovered_by_fallback": True,
                },
            )
            await message.answer(TEXTS["payment_success"])
            await create_subscription(
                message,
                int(payer_tg_id),
                tariff,
                bot,
                paid_amount_stars=int(payment.total_amount),
                pay_attempt_id=int(fallback_attempt.id),
            )
            _mark_stars_payment_processed(
                payment_fingerprint=payment_fingerprint,
                invoice_payload=payload,
                tg_id=int(payer_tg_id),
            )
            return

    logger.warning(
        "payment_success unhandled payload=%s from_tg=%s amount=%s currency=%s",
        payload,
        payer_tg_id,
        payment.total_amount,
        payment.currency,
    )
    await message.answer("✅ Оплата получена. Проверяем активацию, если не активировалось — напишите в поддержку.")

async def create_subscription(
    message: Message,
    tg_id: int,
    tariff: dict,
    bot: Bot,
    paid_amount_stars: int | None = None,
    pay_attempt_id: int | None = None,
):
    """Create or extend subscription"""
    user = get_user(tg_id)
    panel_client = await panel.get_existing_client(tg_id)
    
    # Check if this is a PAID purchase (for referral bonus)
    is_paid_purchase = tariff["stars"] > 0
    
    if panel_client:
        # User exists in panel - update DB and add traffic
        client_uuid = panel_client.get("id")
        if user:
            old_sub = _normalize_sub_type(user.sub_type)
            new_sub = _normalize_sub_type(tariff.get("sub_type") or tariff.get("subId"))
            # Freemium -> PAID must start from "now", not from legacy long expiry.
            if _is_freemium_sub_type(old_sub) and new_sub == "PAID":
                reset_user_expiry_from_now(tg_id, tariff["days"], tariff["stars"])
            else:
                extend_user(tg_id, tariff["days"], tariff["stars"])
            # Keep current plan label in DB for status/admin.
            session = Session()
            db_user = session.query(User).filter_by(tg_id=tg_id).first()
            if db_user:
                db_user.sub_type = tariff.get("sub_type") or db_user.sub_type
                if not str(db_user.sub_token or "").strip():
                    db_user.sub_token = generate_sub_token()
                    logger.info("generated missing sub_token for existing user tg_id=%s", int(tg_id))
                if _is_freemium_sub_type(db_user.sub_type):
                    mark_user_became_free(db_user)
                session.commit()
            session.close()
        else:
            create_user(tg_id, panel_client.get("id"), panel_client.get("email"), 
                       tariff.get("sub_type") or tariff["subId"], tariff["days"], tariff["gb"], tariff["stars"])
        
        # Add traffic to existing client
        await panel.update_client_traffic(tg_id, tariff["gb"])
    else:
        # Create new in panel
        user_uuid = str(uuid.uuid4())
        email = f"User_{tg_id}"
        
        # Generate sub_token BEFORE creating in panel
        sub_token = generate_sub_token()
        
        # 3x-ui "subId" in this project is the per-user subscription token, not the tariff.
        # The 3rd argument here is our internal plan marker to decide which nodes to provision.
        success = await panel.add_client(user_uuid, email, tariff.get("sub_type") or tariff["subId"], tariff["gb"], tg_id, sub_token)
        
        if not success:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 Написать в поддержку", url=f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
            ])
            await message.answer("❌ Не удалось активировать портал.\n\nНажмите кнопку ниже для связи с поддержкой.", reply_markup=kb)
            return
        
        # Create user in DB with the generated sub_token
        new_user = create_user(tg_id, user_uuid, email, tariff.get("sub_type") or tariff["subId"], tariff["days"], tariff["gb"], tariff["stars"])
        # Update sub_token (create_user generates its own, but we need the one sent to panel)
        session = Session()
        db_user = session.query(User).filter_by(tg_id=tg_id).first()
        if db_user:
            db_user.sub_token = sub_token
            session.commit()
        session.close()
    
    # Keep legacy trial flag only for actual TRIAL plans (not used by default).
    sub_type = (tariff.get("sub_type") or "").upper()
    if tariff["stars"] == 0 and sub_type.startswith("TRIAL"):
        mark_trial_used(tg_id)
    
    # 🎁 Award referral bonus days for every paid purchase
    if is_paid_purchase:
        # Mark that user has used their 20% discount
        mark_first_purchase_done(tg_id)
        clear_pending_discount(tg_id)
        
        user = get_user(tg_id)
        if user and user.referrer_id:
            try:
                bonus_success = await award_referral_bonus(user.referrer_id, REFERRAL_BONUS_DAYS)
                if bonus_success:
                    if paid_amount_stars and int(paid_amount_stars) > 0:
                        award_referral_points(
                            tg_id=int(user.referrer_id),
                            paid_stars=int(paid_amount_stars),
                            ref_tg_id=int(tg_id),
                            pay_attempt_id=pay_attempt_id,
                        )
                    # Notify referrer about bonus
                    try:
                        await bot.send_message(
                            user.referrer_id,
                            "🎁 *Бонус!*\n\n"
                            "Ваш друг пополнил подписку!\n"
                            f"Вам начислено *+{REFERRAL_BONUS_DAYS} дней*!\n\n"
                            "_Спасибо, что рекомендуете наш сервис!_",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except:
                        pass  # Referrer may have blocked bot
            except Exception as e:
                print(f"Referral bonus error: {e}")
    
    # 🔥 Update streak and bonus only for paid purchases.
    if is_paid_purchase:
        new_streak, streak_bonus = update_streak(tg_id)
        if streak_bonus > 0:
            try:
                await panel.update_client_traffic(tg_id, streak_bonus)
                await message.answer(
                    f"🔥 *Streak бонус!*\n\n"
                    f"Ты на волне уже *{new_streak} месяцев*!\n"
                    f"Тебе начислено *+{streak_bonus} Дней*!",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
    
    user = get_user(tg_id)
    expiry = user.expiry_at.strftime("%d.%m.%Y") if user and user.expiry_at else "—"
    is_free = _is_freemium_sub_type(user.sub_type if user else "")
    free_note = ""
    if is_free:
        free_note = (
            f"\n\n🆓 Бесплатный: до {FREE_TOTAL_GB} ГБ, до {FREE_LIMIT_IP} устройств (по IP), до {FREE_SPEED_MBIT} Мбит/с."
        )
    
    # Build subscription link
    sub_link = build_subscription_link(tg_id)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Открыть Портал", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back")]
    ])
    
    await message.answer(
        f"✅ *Портал активирован!*\n\n"
        f"🔋 Энергии хватит до: `{expiry}`\n\n"
        f"🔗 *Ваша подписка:*\n"
        f"`{sub_link}`\n\n"
        f"📋 _Добавьте ссылку как подписку в приложение_{free_note}",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )


# ==========================================
#           ADMIN COMMANDS
# ==========================================
@router.message(Command("admin"))
async def admin_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    # 🧹 Delete command message
    try:
        await message.delete()
    except:
        pass
    
    stats = get_stats()
    
    await message.answer(
        TEXTS["admin_stats"].format(
            total=stats["total"],
            active=stats["active"],
            stars=stats["stars"]
        ),
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(Command("user"))
async def admin_user_search(message: Message):
    """Search user by @username or tg_id: /user @name or /user 123456"""
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "🔍 *Поиск пользователя*\n\n"
            "Использование:\n"
            "`/user @username`\n"
            "`/user 123456789`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    query = args[1].strip()
    session = Session()
    
    if query.startswith("@"):
        # Search by username
        username = query.lstrip("@")
        user = session.query(User).filter(User.username.ilike(username)).first()
    else:
        # Search by tg_id
        try:
            tg_id = int(query)
            user = session.query(User).filter_by(tg_id=tg_id).first()
        except ValueError:
            user = session.query(User).filter(User.username.ilike(query)).first()
    
    if not user:
        session.close()
        await message.answer(f"❌ Пользователь `{query}` не найден", parse_mode=ParseMode.MARKDOWN)
        return
    
    # Get achievements count
    ach_count = session.query(Achievement).filter_by(tg_id=user.tg_id).count()
    
    session.close()
    


    # Format user info
    status = "✅ Активен" if user.is_active else "❌ Неактивен"
    expiry = user.expiry_at.strftime("%d.%m.%Y") if user.expiry_at else "—"
    created = user.created_at.strftime("%d.%m.%Y") if user.created_at else "—"
    
    safe_username = (user.username or '—').replace('_', '\\_')
    text = (
        f"👤 *Пользователь*\n\n"
        f"ID: `{user.tg_id}`\n"
        f"Username: @{safe_username}\n"
        f"Статус: {status}\n\n"
        f"📦 Тариф: `{user.sub_type or '—'}`\n"
        f"📅 До: `{expiry}`\n"
        f"📡 Режим: `{_plan_mode_label(user.sub_type)}`\n"
        f"⭐ Оплачено: `{user.stars_paid or 0}` Stars\n\n"
        f"🔥 Streak: `{user.streak_months or 0}` мес\n"
        f"🏆 Ачивки: `{ach_count}`\n"
        f"👥 Рефералы: `{user.referral_count or 0}`\n\n"
        f"📆 Создан: `{created}`"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Открыть", callback_data=f"adm_user_{user.tg_id}"),
            InlineKeyboardButton(text="📋 Логи", callback_data=f"admin_logs_{user.tg_id}"),
        ],
        [
            InlineKeyboardButton(text="📅 Продлить", callback_data=f"admin_extend_{user.tg_id}")
        ],
        [InlineKeyboardButton(text="🚫 Заблокировать" if user.is_active else "✅ Разблокировать", 
                              callback_data=f"admin_ban_{user.tg_id}")]
    ])
    
    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

# Admin action states
admin_pending_actions = {}
# In-memory draft for the broadcast composer (admin only).
admin_broadcast_drafts: dict[int, dict] = {}

@router.callback_query(F.data.startswith("admin_logs_"))
async def admin_view_logs(callback: CallbackQuery):
    """View user activity logs"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещён")
        return
    
    tg_id = int(callback.data.replace("admin_logs_", ""))
    session = Session()
    
    user = session.query(User).filter_by(tg_id=tg_id).first()
    if not user:
        session.close()
        await callback.answer("Юзер не найден")
        return
    
    # Get achievements
    achievements = session.query(Achievement).filter_by(tg_id=tg_id).all()
    ach_text = "\n".join([f"  • {ACHIEVEMENTS.get(a.achievement_id, {}).get('name', a.achievement_id)}" 
                          for a in achievements[:5]]) or "  Нет"
    
    # Get gift cards redeemed/created
    cards_created = session.query(GiftCard).filter_by(created_by=tg_id).count()
    cards_redeemed = session.query(GiftCard).filter_by(redeemed_by=tg_id).count()
    
    # Get reviews
    review = session.query(Review).filter_by(tg_id=tg_id).first()
    review_text = f"  {'⭐' * review.rating} {review.text[:50] if review.text else ''}" if review else "  Нет"
    
    session.close()
    
    # Wheel info
    wheel_text = user.last_wheel_spin.strftime("%d.%m.%Y %H:%M") if user.last_wheel_spin else "Никогда"
    
    text = (
        f"📋 *Логи пользователя* `{tg_id}`\n\n"
        f"*Последняя активность:*\n"
        f"  🎰 Рулетка: {wheel_text}\n"
        f"  🔥 Streak check: {user.streak_last_check.strftime('%d.%m.%Y') if user.streak_last_check else 'Нет'}\n\n"
        f"*Ачивки ({len(achievements)}):*\n{ach_text}\n\n"
        f"*Подарочные карты:*\n"
        f"  Создано: {cards_created}\n"
        f"  Активировано: {cards_redeemed}\n\n"
        f"*Отзыв:*\n{review_text}"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к профилю", callback_data=f"admin_profile_{tg_id}")]
    ])
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_profile_"))
async def admin_back_to_profile(callback: CallbackQuery):
    """Return to user profile from logs"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    tg_id = int(callback.data.replace("admin_profile_", ""))
    # Reuse search logic
    from aiogram.types import Message as FakeMessage
    
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    ach_count = session.query(Achievement).filter_by(tg_id=tg_id).count() if user else 0
    session.close()
    
    if not user:
        await callback.answer("Юзер не найден")
        return
    
    status = "✅ Активен" if user.is_active else "❌ Неактивен"
    expiry = user.expiry_at.strftime("%d.%m.%Y") if user.expiry_at else "—"
    created = user.created_at.strftime("%d.%m.%Y") if user.created_at else "—"
    
    safe_username = (user.username or '—').replace('_', '\\_')
    text = (
        f"👤 *Пользователь*\n\n"
        f"ID: `{user.tg_id}`\n"
        f"Username: @{safe_username}\n"
        f"Статус: {status}\n\n"
        f"📦 Тариф: `{user.sub_type or '—'}`\n"
        f"📅 До: `{expiry}`\n"
        f"⭐ Оплачено: `{user.stars_paid or 0}` Stars\n\n"
        f"🔥 Streak: `{user.streak_months or 0}` мес\n"
        f"🏆 Ачивки: `{ach_count}`\n"
        f"👥 Рефералы: `{user.referral_count or 0}`\n\n"
        f"📆 Создан: `{created}`"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Открыть", callback_data=f"adm_user_{user.tg_id}"),
            InlineKeyboardButton(text="📋 Логи", callback_data=f"admin_logs_{user.tg_id}"),
        ],
        [
            InlineKeyboardButton(text="📅 Продлить", callback_data=f"admin_extend_{user.tg_id}")
        ],
        [InlineKeyboardButton(text="🚫 Заблокировать" if user.is_active else "✅ Разблокировать", 
                              callback_data=f"admin_ban_{user.tg_id}")]
    ])
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()

    # Handler removed
    # await callback.answer("🚫 Лимиты по трафику не поддерживаются. Используйте 'Продлить'.", show_alert=True)

@router.callback_query(F.data.startswith("admin_extend_"))
async def admin_extend_prompt(callback: CallbackQuery):
    """Prompt to extend subscription"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    tg_id = int(callback.data.replace("admin_extend_", ""))
    admin_pending_actions[callback.from_user.id] = {"action": "extend", "target": tg_id}
    
    await callback.message.edit_text(
        f"📅 *Продлить подписку*\n\n"
        f"Юзер: `{tg_id}`\n\n"
        f"Отправь количество дней (число):",
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_ban_"))
async def admin_toggle_ban(callback: CallbackQuery):
    """Ban/unban user"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    tg_id = int(callback.data.replace("admin_ban_", ""))
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    
    if user:
        user.is_active = not user.is_active
        new_status = "заблокирован" if not user.is_active else "разблокирован"
        session.commit()
        await callback.answer(f"✅ Юзер {new_status}")
    
    session.close()
    # Return to profile
    await admin_back_to_profile(callback)

# ==========================================
#           PROMO CODES
# ==========================================

@router.message(Command("template"))
async def template_command(message: Message, bot: Bot):
    """
    /template add KEY text - create template
    /template list - show all
    /template send KEY - send to all
    /template send KEY @user - send to user
    /template delete KEY - delete
    """
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split(maxsplit=3)
    
    if len(args) < 2:
        await message.answer(
            "📝 *Шаблоны сообщений*\n\n"
            "`/template add key текст` — создать\n"
            "`/template list` — список\n"
            "`/template send key` — всем\n"
            "`/template send key @user` — юзеру\n"
            "`/template delete key` — удалить",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    subcmd = args[1].lower()
    
    if subcmd == "add" and len(args) >= 4:
        key = args[2].lower()
        text = args[3]
        
        session = Session()
        existing = session.query(Template).filter_by(key=key).first()
        if existing:
            existing.text = text
            action = "обновлён"
        else:
            session.add(Template(key=key, text=text))
            action = "создан"
        session.commit()
        session.close()
        
        await message.answer(f"✅ Шаблон `{key}` {action}", parse_mode=ParseMode.MARKDOWN)
    
    elif subcmd == "list":
        session = Session()
        templates = session.query(Template).all()
        session.close()
        
        if not templates:
            await message.answer("📝 _Нет шаблонов_", parse_mode=ParseMode.MARKDOWN)
            return
        
        lines = [f"`{t.key}` — {t.text[:50]}..." if len(t.text) > 50 else f"`{t.key}` — {t.text}" for t in templates]
        await message.answer("📝 *Шаблоны:*\n\n" + "\n".join(lines), parse_mode=ParseMode.MARKDOWN)
    
    elif subcmd == "send" and len(args) >= 3:
        key = args[2].lower()
        target_user = args[3] if len(args) >= 4 else None
        
        session = Session()
        template = session.query(Template).filter_by(key=key).first()
        
        if not template:
            session.close()
            await message.answer(f"❌ Шаблон `{key}` не найден", parse_mode=ParseMode.MARKDOWN)
            return
        
        if target_user:
            # Send to specific user
            username = target_user.lstrip("@")
            user = session.query(User).filter(User.username.ilike(username)).first()
            if not user:
                try:
                    uid = int(target_user)
                    user = session.query(User).filter_by(tg_id=uid).first()
                except:
                    pass
            session.close()
            
            if not user:
                await message.answer(f"❌ Юзер `{target_user}` не найден", parse_mode=ParseMode.MARKDOWN)
                return
            
            try:
                await bot.send_message(user.tg_id, template.text, parse_mode=ParseMode.MARKDOWN)
                await message.answer(f"✅ Шаблон `{key}` отправлен @{user.username or user.tg_id}", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await message.answer(f"❌ Ошибка: {e}")
        else:
            # Send to all
            users = session.query(User).filter_by(is_active=True).all()
            session.close()
            
            sent = 0
            for user in users:
                if user.tg_id in PROTECTED_USERS or user.tg_id == ADMIN_ID:
                    continue
                try:
                    await bot.send_message(user.tg_id, template.text, parse_mode=ParseMode.MARKDOWN)
                    sent += 1
                except:
                    pass
            
            await message.answer(f"✅ Шаблон `{key}` отправлен {sent} юзерам", parse_mode=ParseMode.MARKDOWN)
    
    elif subcmd == "delete" and len(args) >= 3:
        key = args[2].lower()
        
        session = Session()
        template = session.query(Template).filter_by(key=key).first()
        if template:
            session.delete(template)
            session.commit()
            await message.answer(f"✅ Шаблон `{key}` удалён", parse_mode=ParseMode.MARKDOWN)
        else:
            await message.answer(f"❌ Шаблон `{key}` не найден", parse_mode=ParseMode.MARKDOWN)
        session.close()
    
    else:
        await message.answer("❌ Неверный формат команды")


def activate_promo_code_for_user(tg_id: int, code: str) -> tuple[bool, str]:
    code = (code or "").strip().upper()
    if not code:
        return False, "❌ Промокод пустой"
    if not check_tos_accepted(int(tg_id)):
        return False, "⚠️ Сначала примите оферту через /start."

    session = Session()
    try:
        promo = session.query(PromoCode).filter_by(code=code).first()
        if not promo:
            return False, "❌ Промокод не найден"
        if promo.expires_at and promo.expires_at < _utcnow():
            return False, "❌ Срок действия промокода истёк"

        if promo.uses_left == 0:
            return False, "❌ Промокод больше не активен"

        usage = session.query(PromoUsage).filter_by(tg_id=tg_id, promo_code=code).first()
        if usage:
            return False, "❌ Ты уже использовал этот промокод"

        user = session.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            return False, "❌ Пользователь не найден"

        active_campaigns_for_code = (
            session.query(func.count(IncentiveCampaign.id))
            .filter(func.lower(IncentiveCampaign.campaign_type) == "promo")
            .filter(func.upper(IncentiveCampaign.target_value) == code)
            .filter(IncentiveCampaign.is_active == True)
            .scalar()
            or 0
        )
        campaign = _campaign_lookup(
            session=session,
            campaign_type="promo",
            target_value=code,
            user=user,
            now=_utcnow(),
        )
        if int(active_campaigns_for_code) > 0 and campaign is None:
            session.flush()
            return False, "❌ Промокод недоступен для этого аккаунта"

        promo_type = str(promo.promo_type or "").strip().lower()
        promo_value = int(promo.value or 0)
        if promo_type not in {"days", "discount"} or promo_value <= 0:
            return False, "❌ Промокод некорректен"

        if promo_type == "days":
            now = _utcnow()
            if user:
                expiry = _naive_utc(user.expiry_at)
                if expiry and expiry > now:
                    user.expiry_at = expiry + timedelta(days=promo_value)
                else:
                    user.expiry_at = now + timedelta(days=promo_value)
                user.is_active = True
            result_text = f"🎁 Тебе добавлено *+{promo_value} Дней!*"
        elif promo_type == "discount":
            user = session.query(User).filter_by(tg_id=tg_id).first()
            if user:
                user.pending_discount_pct = max(1, min(95, int(promo_value or 0)))
                user.pending_discount_code = str(code).upper()[:20]
                user.pending_discount_set_at = _utcnow()
            result_text = (
                f"🎉 Скидка *{promo_value}%* активирована.\n"
                "Она применится к следующей оплате в ₽ или Stars."
            )
        else:
            result_text = f"🎉 Скидка *{promo_value}%* будет применена к следующей покупке!"

        session.add(PromoUsage(tg_id=tg_id, promo_code=code))
        _campaign_consume(row=campaign)
        if promo.uses_left > 0:
            promo.uses_left -= 1
        session.commit()
        return True, f"✅ *Промокод активирован!*\n\n{result_text}"
    finally:
        session.close()


@router.message(Command("promo"))
async def promo_command(message: Message, bot: Bot):
    """
    Admin: /promo create CODE TYPE VALUE [USES]
    Admin: /promo list
    User: /promo CODE
    """
    tg_id = message.from_user.id
    pending_promo_codes.discard(tg_id)
    args = message.text.split()
    
    # Admin commands
    if tg_id == ADMIN_ID and len(args) >= 2:
        subcmd = args[1].lower()
        
        if subcmd == "create" and len(args) >= 5:
            # /promo create NEWYEAR discount 20 100
            # /promo create BONUS10 gb 10 50
            code = args[2].upper()
            promo_type = args[3].lower()
            try:
                value = int(args[4])
                uses = int(args[5]) if len(args) > 5 else -1
            except:
                await message.answer("❌ Неверный формат. Пример:\n`/promo create NEWYEAR discount 20 100`", parse_mode=ParseMode.MARKDOWN)
                return
            
            if promo_type not in ["discount", "days"]:
                await message.answer("❌ Тип: `discount` или `days`", parse_mode=ParseMode.MARKDOWN)
                return
            
            session = Session()
            existing = session.query(PromoCode).filter_by(code=code).first()
            if existing:
                session.close()
                await message.answer(f"❌ Код `{code}` уже существует", parse_mode=ParseMode.MARKDOWN)
                return
            
            promo = PromoCode(code=code, promo_type=promo_type, value=value, uses_left=uses)
            session.add(promo)
            session.commit()
            session.close()
            
            type_text = f"{value}%" if promo_type == "discount" else f"+{value} Дней"
            uses_text = "∞" if uses == -1 else str(uses)
            await message.answer(
                f"✅ *Промокод создан!*\n\n"
                f"Код: `{code}`\n"
                f"Тип: {type_text}\n"
                f"Лимит: {uses_text}",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        elif subcmd == "list":
            session = Session()
            promos = session.query(PromoCode).filter(PromoCode.uses_left != 0).all()
            session.close()
            
            if not promos:
                await message.answer("📭 Нет активных промокодов")
                return
            
            lines = []
            for p in promos:
                type_text = f"{p.value}%" if p.promo_type == "discount" else f"+{p.value} Дн."
                uses_text = "∞" if p.uses_left == -1 else str(p.uses_left)
                lines.append(f"`{p.code}` — {type_text}, осталось: {uses_text}")
            
            await message.answer(
                "🎫 *Активные промокоды:*\n\n" + "\n".join(lines),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        elif subcmd == "delete" and len(args) >= 3:
            code = args[2].upper()
            session = Session()
            promo = session.query(PromoCode).filter_by(code=code).first()
            if promo:
                session.delete(promo)
                session.commit()
                await message.answer(f"✅ Промокод `{code}` удалён", parse_mode=ParseMode.MARKDOWN)
            else:
                await message.answer(f"❌ Промокод `{code}` не найден", parse_mode=ParseMode.MARKDOWN)
            session.close()
            return
    
    # User activation: /promo CODE
    if len(args) >= 2:
        code = args[1].upper()
        ok, result = activate_promo_code_for_user(tg_id, code)
        await message.answer(result, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer(
            "🎫 *Активация промокода*\n\n"
            "Использование: `/promo КОД`\n\n"
            "Пример: `/promo NEWYEAR`",
            parse_mode=ParseMode.MARKDOWN
        )

# ==========================================
#           HEALTH CHECK
# ==========================================

@router.message(Command("health"))
async def health_check(message: Message, bot: Bot):
    """Check system health"""
    if message.from_user.id != ADMIN_ID:
        return
    
    import time
    start_time = time.time()
    
    status = []
    
    # Bot status (always OK if we're running)
    status.append("✅ Бот: работает")
    
    # Database check
    try:
        session = Session()
        user_count = session.query(User).count()
        active_count = session.query(User).filter_by(is_active=True).count()
        session.close()
        status.append(f"✅ БД: {user_count} юзеров ({active_count} активных)")
    except Exception as e:
        status.append(f"❌ БД: {str(e)[:50]}")
    
    # Panel check
    try:
        clients = await panel.get_clients_list()
        if clients is not None:
            status.append(f"✅ Панель: {len(clients)} клиентов")
        else:
            status.append("⚠️ Панель: нет ответа")
    except Exception as e:
        status.append(f"❌ Панель: {str(e)[:50]}")
    
    # API check (self-ping)
    try:
        import aiohttp
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{WEBAPP_URL}", timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status == 200:
                    status.append("✅ WebApp: доступен")
                else:
                    status.append(f"⚠️ WebApp: код {r.status}")
    except Exception as e:
        status.append(f"❌ WebApp: {str(e)[:30]}")
    
    elapsed = round((time.time() - start_time) * 1000)
    
    await message.answer(
        f"❤️ *Health Check*\n\n" + 
        "\n".join(status) +
        f"\n\n⏱️ Проверка: {elapsed}мс",
        parse_mode=ParseMode.MARKDOWN
    )

# ==========================================
#           REVIEWS MODERATION
# ==========================================

@router.message(Command("reviews"))
async def reviews_moderation(message: Message):
    """List reviews for moderation: /reviews [featured|all]"""
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split()
    show_featured = len(args) > 1 and args[1].lower() == "featured"
    
    session = Session()
    if show_featured:
        reviews = session.query(Review).filter_by(is_featured=True).order_by(Review.created_at.desc()).limit(10).all()
        title = "⭐ Избранные отзывы"
    else:
        reviews = session.query(Review).order_by(Review.created_at.desc()).limit(10).all()
        title = "📝 Последние отзывы"
    
    session.close()
    
    if not reviews:
        await message.answer("📭 Отзывов нет")
        return
    
    for r in reviews:
        featured = "⭐" if r.is_featured else ""
        masked = _mask_review_username(r.username)
        label = f"@{masked}" if masked != "Пользователь" else masked
        text = r.text[:100] if r.text else "—"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐ Featured" if not r.is_featured else "❌ Unfeatured", 
                                     callback_data=f"review_toggle_{r.id}"),
                InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"review_delete_{r.id}")
            ]
        ])
        await message.answer(
            f"{featured} *{label}* {'⭐' * r.rating}\n"
            f"_{text}_\n"
            f"`ID:{r.id}`",
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN
        )

@router.callback_query(F.data.startswith("review_toggle_"))
async def toggle_review_featured(callback: CallbackQuery):
    """Toggle featured status"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    review_id = int(callback.data.replace("review_toggle_", ""))
    session = Session()
    review = session.query(Review).filter_by(id=review_id).first()
    if review:
        review.is_featured = not review.is_featured
        status = "добавлен в избранное" if review.is_featured else "убран из избранного"
        session.commit()
        await callback.answer(f"✅ Отзыв {status}")
    session.close()

    # If this toggle was triggered from the admin list view, refresh the list.
    try:
        txt = (callback.message.text or "").strip()
        if ("Стр " in txt) and ("Все отзывы" in txt or "Избранные отзывы" in txt):
            featured_only = txt.startswith("⭐")
            import re

            m = re.search(r"Стр\\s+(\\d+)/(\\d+)", txt)
            page = int(m.group(1)) - 1 if m else 0
            await _render_reviews_page(callback=callback, featured_only=featured_only, page=page)
    except Exception:
        pass

@router.callback_query(F.data.startswith("review_delete_"))
async def delete_review(callback: CallbackQuery):
    """Delete review"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    review_id = int(callback.data.replace("review_delete_", ""))
    session = Session()
    review = session.query(Review).filter_by(id=review_id).first()
    if review:
        session.delete(review)
        session.commit()
    session.close()

    # Refresh admin list view if this action came from it; otherwise just confirm.
    try:
        txt = (callback.message.text or "").strip()
        if ("Стр " in txt) and ("Все отзывы" in txt or "Избранные отзывы" in txt):
            featured_only = txt.startswith("⭐")
            import re

            m = re.search(r"Стр\\s+(\\d+)/(\\d+)", txt)
            page = int(m.group(1)) - 1 if m else 0
            await _render_reviews_page(callback=callback, featured_only=featured_only, page=page)
        else:
            await callback.answer("🗑️ Удалено")
    except Exception:
        await callback.answer("🗑️ Удалено")

@router.message(Command("sync"))
async def sync_usernames(message: Message, bot: Bot):
    """Sync usernames from Telegram API for all users and update panel comments"""
    if message.from_user.id != ADMIN_ID:
        return
    
    # 🧹 Delete command message
    try:
        await message.delete()
    except:
        pass
    
    await message.answer("🔄 Синхронизирую никнеймы и обновляю панель...")
    
    session = Session()
    users = session.query(User).all()
    updated = 0
    panel_updated = 0
    errors = 0
    
    for user in users:
        # Skip protected users
        if user.tg_id in PROTECTED_USERS:
            continue
        
        try:
            chat = await bot.get_chat(user.tg_id)
            if chat.username:
                user.username = chat.username
                updated += 1
                # Also update panel comment
                if await panel.update_client_comment(user.tg_id, f"@{chat.username}"):
                    panel_updated += 1
        except Exception:
            errors += 1
    
    session.commit()
    session.close()
    
    await message.answer(
        f"✅ Синхронизация завершена!\n\n"
        f"📊 Обновлено в БД: {updated}\n"
        f"📋 Обновлено в панели: {panel_updated}\n"
        f"❌ Ошибок: {errors}\n"
        f"👥 Всего: {len(users)}"
    )


# Backwards compat from old const
BROADCAST_EXCLUDE = PROTECTED_USERS

@router.message(Command("broadcast"))
async def admin_broadcast(message: Message, bot: Bot):
    """Send new subscription links to all active users"""
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        await message.delete()
    except:
        pass
    
    session = Session()
    users = session.query(User).filter(User.is_active == True).all()
    session.close()
    
    sent = 0
    failed = 0
    skipped = 0
    
    status_msg = await message.answer(f"📤 Отправляю рассылку...\n👥 Всего: {len(users)}")
    
    for user in users:
        # Skip excluded users and admin
        if user.tg_id in BROADCAST_EXCLUDE or user.tg_id == ADMIN_ID:
            skipped += 1
            continue
        
        try:
            sub_link = build_subscription_link(user.tg_id)
            await bot.send_message(
                user.tg_id,
                f"🔄 *Обновление подписки*\n\n"
                f"Мы обновили систему для повышения безопасности.\n\n"
                f"🔗 *Ваша новая ссылка подписки:*\n"
                f"`{sub_link}`\n\n"
                f"📋 _Пожалуйста, обновите ссылку в вашем приложении._\n\n"
                f"Если у вас вопросы — /start",
                parse_mode=ParseMode.MARKDOWN
            )
            sent += 1
            await asyncio.sleep(0.1)  # Rate limit
        except Exception as e:
            failed += 1
    
    await status_msg.edit_text(
        f"✅ *Рассылка завершена!*\n\n"
        f"📨 Отправлено: {sent}\n"
        f"⏭️ Пропущено: {skipped}\n"
        f"❌ Ошибок: {failed}",
        parse_mode=ParseMode.MARKDOWN
    )

    audit_admin(
        actor_tg_id=message.from_user.id,
        action="admin_broadcast",
        meta=json.dumps(
            {"sent": sent, "failed": failed, "skipped": skipped, "total": len(users)},
            ensure_ascii=True,
            separators=(",", ":"),
        ),
    )


@router.message(Command("giftcode"))
async def admin_giftcode(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "🎫 *Формат /giftcode*\n\n"
            "`/giftcode mini`\n"
            "`/giftcode standard`\n"
            "`/giftcode premium`\n"
            "`/giftcode standard 5` _(создать сразу 5 кодов)_",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    card_type = (parts[1] or "").strip().lower()
    if card_type not in GIFT_CARD_TYPES:
        await message.answer("❌ Неизвестный тип. Используйте: mini / standard / premium")
        return

    try:
        count = int(parts[2]) if len(parts) > 2 else 1
    except Exception:
        await message.answer("❌ Количество должно быть числом.")
        return
    count = max(1, min(20, count))

    created: list[str] = []
    for _ in range(count):
        code = create_gift_card(ADMIN_ID, card_type)
        if code:
            created.append(code)

    if not created:
        await message.answer("❌ Не удалось создать gift-коды.")
        return

    card = GIFT_CARD_TYPES.get(card_type, {})
    lines = "\n".join(f"`{c}`" for c in created[:20])
    await message.answer(
        f"✅ Создано кодов: *{len(created)}*\n"
        f"Тип: *{card.get('name', card_type)}*\n"
        f"Срок: *{int(card.get('days', 0))} дн.*\n\n"
        f"{lines}",
        parse_mode=ParseMode.MARKDOWN,
    )
    audit_admin(
        ADMIN_ID,
        "admin_gift_code_batch",
        meta=f"card_type={card_type}; requested={count}; created={len(created)}",
    )


@router.message(Command("gift"))
async def admin_gift(message: Message, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return
    
    # 🧹 Delete command message
    try:
        await message.delete()
    except:
        pass
    
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "📦 *Формат команды /gift:*\n\n"
            "`/gift [tg_id] trial` — Пробный (7 дней)\n"
            "`/gift [tg_id] basic` — Стандарт (30 дней)\n"
            "`/gift [tg_id] pro` — Турбо (30 дней)\n"
            "`/gift [tg_id] vip` — VIP (365 дней)\n"
            "`/gift [tg_id] [days]` — Кастом\n\n"
            "_Примеры:_\n"
            "`/gift 123456789 vip`\n"
            "`/gift 123456789 90`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        gift_tg_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Неверный tg_id")
        return
    if gift_tg_id > 0 and not check_tos_accepted(gift_tg_id):
        await message.answer(
            "⚠️ Этот пользователь ещё не принял оферту.\n"
            "Сначала пусть нажмёт /start и подтвердит условия, затем выдавайте подарок."
        )
        return
    
    # Preset tariffs for gifts
    gift_presets = {
        "trial": {"days": 7, "name": "🎁 Пробный"},
        "basic": {"days": 30, "name": "⚡ Стандарт"},
        "pro": {"days": 30, "name": "🚀 Турбо"},
        "vip": {"days": 365, "name": "👑 VIP"},
    }
    
    # Check if preset or custom
    preset_key = parts[2].lower()
    if preset_key in gift_presets:
        preset = gift_presets[preset_key]
        days = preset["days"]
        name = preset["name"]
    else:
        # Custom: /gift tg_id days
        try:
            days = int(parts[2])
            name = f"🎁 Подарок ({days} дней)"
        except ValueError:
            await message.answer("❌ Неверные параметры")
            return
    
    panel_client = await panel.get_existing_client(gift_tg_id)
    
    user = get_user(gift_tg_id)
    if user:
        # EXISTING USER - extend
        extend_user(gift_tg_id, days, 0)

        # Update sub_type to GIFT
        session = Session()
        db_user = session.query(User).filter_by(tg_id=gift_tg_id).first()
        if db_user:
            db_user.sub_type = "PAID"
            db_user.total_gb = 0
            session.commit()
        session.close()
    else:
        # NEW USER - generate sub_token FIRST before adding to panel
        sub_token = generate_sub_token()
        user_uuid = str(uuid.uuid4())
        email = f"User_{gift_tg_id}"
        
        if not panel_client:
            # Pass sub_token to add_client so panel uses secure subscription ID
            await panel.add_client(user_uuid, email, "PAID", 0, gift_tg_id, sub_token)
        else:
            user_uuid = panel_client.get("id")
            email = panel_client.get("email")
        
        # Create user in DB with generated sub_token
        session = Session()
        new_user = User(
            tg_id=gift_tg_id,
            uuid=user_uuid,
            email=email,
            sub_type="PAID",
            expiry_at=_utcnow() + timedelta(days=days),
            is_active=True,
            stars_paid=0,
            total_gb=0,
            sub_token=sub_token
        )
        session.add(new_user)
        session.commit()
        session.close()
    
    # 🎁 Referral bonus (gift counts as purchase)
    mark_first_purchase_done(gift_tg_id)
    user = get_user(gift_tg_id)
    if user and user.referrer_id:
        try:
            bonus_success = await award_referral_bonus(user.referrer_id, REFERRAL_BONUS_DAYS)
            if bonus_success:
                # Notify referrer about bonus
                try:
                    await bot.send_message(
                        user.referrer_id,
                        "🎁 *Бонус!*\n\n"
                        "Ваш друг получил подписку!\n"
                        f"Вам начислено *+{REFERRAL_BONUS_DAYS} дней*!\n\n"
                        "_Спасибо, что рекомендуете наш сервис!_",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except:
                    pass
        except Exception as e:
            print(f"Referral bonus error: {e}")
    
    await message.answer(
        f"✅ Подарок отправлен!\n\n👤 ID: `{gift_tg_id}`\n📦 Тариф: {name}\n📅 Дней: {days}",
        parse_mode=ParseMode.MARKDOWN,
    )

    audit_admin(
        actor_tg_id=message.from_user.id,
        action="admin_gift",
        target_tg_id=gift_tg_id,
        meta=json.dumps(
            {"days": days, "preset": preset_key, "name": name},
            ensure_ascii=True,
            separators=(",", ":"),
        ),
    )
    
    try:
        # Build subscription link for notification
        sub_link = build_subscription_link(gift_tg_id)
        await bot.send_message(
            gift_tg_id,
            f"🎁 *Вам подарили доступ к Порталу!*\n\n"
            f"📦 Тариф: {name}\n"
            f"📅 Дней: {days}\n"
            f"📡 Режим: полный доступ\n\n"
            f"🔗 *Ваша подписка:*\n`{sub_link}`\n\n"
            f"📋 _Добавьте ссылку как подписку в приложение_",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass

# ==========================================
#               BACKGROUND TASKS
# ==========================================
async def monitor_expiry(bot: Bot) -> None:
    """
    Background task to enforce expiry.

    Important: we DO NOT enforce traffic limits in this project.
    Traffic-based deactivation is dangerous because legacy/manual clients may have old totalGB limits in panels.
    """
    while True:
        try:
            await asyncio.sleep(3600)  # hourly
            now = _utcnow()

            session = Session()
            try:
                users = session.query(User).filter(User.is_active == True).all()
                for user in users:
                    try:
                        # Manual users are special (static accounts). Don't auto-disable them.
                        if _normalize_sub_type(user.sub_type) == "MANUAL":
                            continue

                        expiry = _naive_utc(user.expiry_at)
                        if expiry and now > expiry:
                            # Auto-downgrade to Free instead of disabling access.
                            user.sub_type = "FREE"
                            # Keep Free usable for a long time; actual policies are controlled server-side.
                            auto_free_days = int(os.getenv("AUTO_FREE_DAYS", "3650"))
                            user.expiry_at = now + timedelta(days=auto_free_days)
                            user.is_active = True
                            mark_user_became_free(user, now=now)
                            session.commit()

                            # Ensure the user exists on the Free inbound and disable any existing paid-node clients.
                            nodes = _bot_enabled_nodes()
                            free_codes = _bot_free_codes()

                            try:
                                if free_codes:
                                    sub_id = user.sub_token or str(user.tg_id)
                                    await panel.ensure_user_on_all_nodes(
                                        tg_id=user.tg_id,
                                        client_uuid=user.uuid,
                                        email=user.email,
                                        sub_id=sub_id,
                                        enable=True,
                                        only_node_codes=free_codes,
                                    )
                            except Exception:
                                pass

                            paid_codes = [
                                (getattr(n, "code", "") or "").strip()
                                for n in nodes
                                if "free" not in (getattr(n, "code", "") or "").lower()
                            ]
                            try:
                                await panel.set_existing_user_enabled_on_nodes(tg_id=user.tg_id, node_codes=paid_codes, enable=False)
                            except Exception:
                                pass

                            if user.tg_id > 0 and user.tg_id not in PROTECTED_USERS:
                                kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⚡ Продлить доступ", callback_data="charge")]])
                                try:
                                    await bot.send_message(
                                        chat_id=user.tg_id,
                                        text=(
                                            "⌛️ *Премиум истёк*\n\n"
                                            "Я переключил вас в *Бесплатный*:\n"
                                            "• 1 бесплатная нода\n"
                                            "• Соцсети + AI\n"
                                            "• YouTube идёт напрямую (сервис не помогает)\n\n"
                                            "Хотите все 4 страны и полный доступ, продлите подписку."
                                        ),
                                        reply_markup=kb,
                                        parse_mode=ParseMode.MARKDOWN,
                                    )
                                    track_event(
                                        tg_id=int(user.tg_id),
                                        event_name="expired",
                                        source="bot",
                                        meta={"flow": "monitor_expiry"},
                                    )
                                except Exception:
                                    pass
                    except Exception as e:
                        logger.error("Expiry monitor error user=%s: %s", getattr(user, "tg_id", "?"), e)
            finally:
                session.close()
        except Exception as e:
            logger.error("Expiry monitor loop error: %s", e)
            await asyncio.sleep(60)


async def _configure_public_bot_menu(bot: Bot) -> None:
    try:
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Открыть главное меню"),
                BotCommand(command="promo", description="Активировать промокод"),
                BotCommand(command="redeem", description="Активировать gift-код"),
            ]
        )
    except Exception as e:
        logger.warning("set_my_commands failed: %s", e)

    try:
        await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    except Exception as e:
        logger.warning("set_chat_menu_button failed: %s", e)

# ==========================================
#               MAIN
# ==========================================
async def main():
    bot = Bot(token=BOT_TOKEN)
    _patch_outgoing_message_methods(bot)
    dp = Dispatcher()
    try:
        dp.callback_query.middleware(CallbackContextMiddleware())
    except Exception:
        pass
    dp.include_router(router)
    
    logger.info("🌐 Portal Bot v2 starting...")
    
    await panel.login()
    await _configure_public_bot_menu(bot)
    
    # Start background expiry monitor (no traffic limits).
    asyncio.create_task(monitor_expiry(bot))
    logger.info("⏳ Expiry monitor started")
    if os.getenv("WORKER_EMBEDDED", "false").strip().lower() in {"1", "true", "yes", "on"}:
        try:
            from worker import main as worker_main

            asyncio.create_task(worker_main())
            logger.info("🧰 Embedded worker started")
        except Exception as e:
            logger.error("Failed to start embedded worker: %s", e)
    
    try:
        await dp.start_polling(bot)
    finally:
        await panel.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())




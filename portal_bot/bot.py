# -*- coding: utf-8 -*-
"""
🌐 POKROV Bot v2
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
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
load_dotenv()

import aiohttp
import qrcode
from sqlalchemy.exc import IntegrityError
from bot_texts import bot_text
from node_policy import (
    canonical_free_node_code,
    free_pool_node_codes,
    node_is_free,
    paid_pool_nodes,
    user_free_access_role,
    user_uses_free_pool,
)
from payment_providers import enabled_public_provider_catalog, normalize_provider as normalize_payment_provider
from public_urls import build_subscription_url as build_public_subscription_url
from shared_surface_facts import get_access_matrix
from telegram_profile import (
    TELEGRAM_PROFILE_WEBAPP_MENU_TEXT,
    TELEGRAM_PROFILE_WEBAPP_MENU_URL,
    expected_public_command_payload,
)
try:
    from aiogram import Bot, Dispatcher, F, Router, BaseMiddleware
    from aiogram.filters import Command, CommandStart
    from aiogram.dispatcher.event.bases import SkipHandler
    from aiogram.types import (
        Message, CallbackQuery, PreCheckoutQuery,
        InlineKeyboardMarkup, InlineKeyboardButton,
        WebAppInfo, LabeledPrice, ContentType, BufferedInputFile,
        BotCommand, MenuButtonCommands, MenuButtonWebApp
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

    class SkipHandler(Exception):
        pass

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

    class MenuButtonWebApp(_BaseType):
        pass

    class BufferedInputFile(_BaseType):
        pass

    class ContentType:
        SUCCESSFUL_PAYMENT = "successful_payment"

    class ParseMode:
        MARKDOWN = "Markdown"
        HTML = "HTML"

    F = _FilterExpr()
_RAW_INLINE_KEYBOARD_BUTTON = InlineKeyboardButton
try:
    from aiogram.types import InputRichMessage as TelegramInputRichMessage
except (ImportError, ModuleNotFoundError):
    TelegramInputRichMessage = None
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, BigInteger, func
from sqlalchemy.orm import sessionmaker, declarative_base
import json
from control_panel import ControlPanel
import html
from telegram_emoji import button_label as emoji_button_label, custom_emoji_id
from telegram_rich_messages import (
    RichMessageCopy,
    device_picker_copy,
    help_copy,
    help_triage_copy,
    home_copy,
    long_tariffs_copy,
    payment_success_copy,
    settings_copy,
    support_hub_copy,
    tariff_choice_copy,
)

# ==========================================
#               CONFIGURATION
# ==========================================
load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
load_dotenv()

try:
    from telegram_buttons import (
        BTN_STYLE_DANGER,
        BTN_STYLE_PRIMARY,
        BTN_STYLE_SUCCESS,
        SUPPORTS_BTN_COPY_TEXT,
        modern_inline_button,
    )
except ModuleNotFoundError:
    modern_inline_button = None
    BTN_STYLE_PRIMARY = "primary"
    BTN_STYLE_SUCCESS = "success"
    BTN_STYLE_DANGER = "danger"
    SUPPORTS_BTN_COPY_TEXT = False
else:
    # Route regular main-bot buttons through the shared current Bot API
    # style/custom-emoji helper, while keeping the raw class for capability probes.
    InlineKeyboardButton = modern_inline_button

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_USERNAME = (os.getenv("BOT_USERNAME") or "pokrov_vpnbot").lstrip("@")
BOT_USERNAME_MD = BOT_USERNAME.replace("_", "\\_")

# Panel
PANEL_URL = os.getenv("PANEL_URL", "http://127.0.0.1:15739")
PANEL_USER = os.getenv("PANEL_USER", "admin")
PANEL_PASS = os.getenv("PANEL_PASS", "")
PANEL_PATH = os.getenv("PANEL_PATH", "")
INBOUND_ID = int(os.getenv("INBOUND_ID", "4"))
TRIAL_LIMIT_GB = 5
INBOUND_ID_BACKUP = int(os.getenv("INBOUND_ID_BACKUP", "0"))  # Optional legacy failover inbound id (0 = disabled)

# Server
HOST_DOMAIN = os.getenv("HOST_DOMAIN") or os.getenv("DOMAIN") or "api.pokrov.space"
PUBLIC_WEB_DOMAIN = (os.getenv("PUBLIC_WEB_DOMAIN") or "pokrov.space").strip()
APP_WEB_DOMAIN = (os.getenv("APP_WEB_DOMAIN") or "app.pokrov.space").strip()
VLESS_PORT = int(os.getenv("VLESS_PORT", "443"))
VLESS_SNI = os.getenv("VLESS_SNI", "yahoo.com")
VLESS_PBK = os.getenv("VLESS_PBK", "")
VLESS_SID = os.getenv("VLESS_SID", "")
VLESS_FP = os.getenv("VLESS_FP", "firefox")
VLESS_FLOW = os.getenv("VLESS_FLOW", "xtls-rprx-vision")

# URLs
WEBAPP_URL = os.getenv("WEBAPP_URL", TELEGRAM_PROFILE_WEBAPP_MENU_URL).strip()
PUBLIC_BOT_WEBAPP_MENU_URL = TELEGRAM_PROFILE_WEBAPP_MENU_URL
PUBLIC_API_BASE_URL = os.getenv("PUBLIC_API_BASE_URL", f"https://{HOST_DOMAIN}")
BOT_INTERNAL_API_BASE_URL = (os.getenv("BOT_INTERNAL_API_BASE_URL") or os.getenv("INTERNAL_API_BASE_URL") or "").strip()
PAY_CHECKOUT_URL = (
    os.getenv("PAY_CHECKOUT_URL")
    or os.getenv("CHECKOUT_URL")
    or "https://pay.pokrov.space/checkout/"
).strip()
CHECKOUT_TICKET_SECRET = (
    (os.getenv("CHECKOUT_TICKET_SECRET") or "").strip()
    or (os.getenv("WEBAPP_SESSION_SECRET") or "").strip()
)
CHECKOUT_TICKET_TTL_SECONDS = max(60, int(os.getenv("CHECKOUT_TICKET_TTL_SECONDS", "900")))
SUPPORT_USERNAME = (os.getenv("SUPPORT_USERNAME") or "pokrov_supportbot").lstrip("@")
SUPPORT_USERNAME = (os.getenv("SUPPORT_BOT_USERNAME") or SUPPORT_USERNAME).lstrip("@")
FEEDBACK_USERNAME = (os.getenv("FEEDBACK_USERNAME") or "pokrov_feedbackbot").lstrip("@")
FEEDBACK_USERNAME = (os.getenv("FEEDBACK_BOT_USERNAME") or FEEDBACK_USERNAME).lstrip("@")
APP_ANDROID_PLAY_URL = (os.getenv("APP_ANDROID_PLAY_URL") or "").strip()
APP_ANDROID_APK_URL = (os.getenv("APP_ANDROID_APK_URL") or "").strip()
APP_ANDROID_APK_ARM64_URL = (os.getenv("APP_ANDROID_APK_ARM64_URL") or "").strip()
APP_ANDROID_APK_ARMEABI_V7A_URL = (os.getenv("APP_ANDROID_APK_ARMEABI_V7A_URL") or "").strip()
APP_ANDROID_APK_X86_64_URL = (os.getenv("APP_ANDROID_APK_X86_64_URL") or "").strip()
APP_ANDROID_APK_UNIVERSAL_URL = (os.getenv("APP_ANDROID_APK_UNIVERSAL_URL") or "").strip()
APP_ANDROID_MIRROR_URL = (os.getenv("APP_ANDROID_MIRROR_URL") or "").strip()
APP_WINDOWS_EXE_URL = (os.getenv("APP_WINDOWS_EXE_URL") or "").strip()
APP_WINDOWS_MIRROR_URL = (os.getenv("APP_WINDOWS_MIRROR_URL") or "").strip()
APP_DOCS_URL = (os.getenv("APP_DOCS_URL") or "https://pokrov.space/install/").strip()
FREE_LIMIT_IP = 1
PAID_LIMIT_IP = int(os.getenv("PAID_LIMIT_IP", "5"))
FREE_TOTAL_GB = 5
_BOT_FREE_TIER_FACTS = dict(get_access_matrix().get("free_tier") or {})
FREE_SPEED_MBIT = max(1, int(_BOT_FREE_TIER_FACTS.get("speed_limit_mbps") or 50))
FREE_SOFT_SPEED_MBIT = max(1, int(_BOT_FREE_TIER_FACTS.get("soft_mode_speed_limit_mbps") or 2))
FREE_SPEED_LIMIT_KBPS = FREE_SPEED_MBIT * 125
NEWS_CHANNEL_ID = os.getenv("NEWS_CHANNEL_ID", "@pokrov_vpn")
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


IOS_APP_LINK = APP_DOCS_URL
ANDROID_APP_LINK = _first_non_empty(
    APP_ANDROID_APK_ARM64_URL,
    APP_ANDROID_APK_URL,
    APP_ANDROID_MIRROR_URL,
    APP_DOCS_URL,
)
WINDOWS_APP_LINK = _first_non_empty(APP_WINDOWS_EXE_URL, APP_WINDOWS_MIRROR_URL, APP_DOCS_URL)
MAC_APP_LINK = APP_DOCS_URL

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
_auto_delete_tasks: dict[tuple[int, int], asyncio.Task] = {}
_user_context_mode: dict[int, str] = {}  # tg_id -> "main" | "support"

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
# Invitees receive the regular five-day trial, never extra referral days.
# Retain the old link parser below so deployed links still attribute the
# referrer, but fail closed on the retired gift mutation.
FRIEND_GIFT_ENABLED = False
RUB_CHECKOUT_ENABLED = _env_bool("RUB_CHECKOUT_ENABLED", default=False)
PAID_CHECKOUT_LAUNCH_APPROVED = _env_bool("PAID_CHECKOUT_LAUNCH_APPROVED", default=False)
# Public-beta policy: never create new Telegram Stars checkout. Successful
# historical payments still pass through the fulfillment handler below.
TELEGRAM_STARS_CHECKOUT_ENABLED = False
FRIEND_GIFT_DAYS = 5
FRIEND_GIFT_CAMPAIGN_KEY = (
    (os.getenv("FRIEND_GIFT_CAMPAIGN_KEY") or f"friend_gift_{FRIEND_GIFT_DAYS}d").strip()[:64]
)
CHANNEL_PREMIUM_DAYS = 5
BONUS_WHEEL_ENABLED = _env_bool("BONUS_WHEEL_ENABLED", default=True)
BOT_RUB_BUTTON_ENABLED = _env_bool("BOT_RUB_BUTTON_ENABLED", default=False)
MAIN_CONNECT_CTA_LABELS = {
    "a": "Продлить или начать",
    "b": "Продлить или начать",
}


def _stars_checkout_creation_enabled() -> bool:
    return False


def _inline_button_supported_fields() -> set[str]:
    fields = getattr(_RAW_INLINE_KEYBOARD_BUTTON, "model_fields", None)
    if isinstance(fields, dict):
        return set(fields.keys())
    fields = getattr(_RAW_INLINE_KEYBOARD_BUTTON, "__fields__", None)
    if isinstance(fields, dict):
        return set(fields.keys())
    return {"text", "callback_data", "url", "web_app"}


INLINE_BUTTON_FIELDS = _inline_button_supported_fields()
SUPPORTS_BTN_STYLE = "style" in INLINE_BUTTON_FIELDS
SUPPORTS_BTN_ICON = "icon_custom_emoji_id" in INLINE_BUTTON_FIELDS


def _is_private_user_chat(chat_id: int, tg_id: int) -> bool:
    return int(chat_id) > 0 and int(tg_id) > 0 and int(chat_id) == int(tg_id)


async def _require_private_callback(callback: CallbackQuery) -> bool:
    tg_id = int(getattr(getattr(callback, "from_user", None), "id", 0) or 0)
    chat_id = int(getattr(getattr(getattr(callback, "message", None), "chat", None), "id", 0) or 0)
    if _is_private_user_chat(chat_id, tg_id):
        return True
    await callback.answer(
        "Личную ссылку и QR можно открыть только в личном чате с ботом.",
        show_alert=True,
    )
    return False


async def _edit_or_answer_callback_text(callback: CallbackQuery, text: str, **kwargs: Any):
    message = callback.message
    if bool(getattr(message, "photo", None)):
        return await message.answer(text, **kwargs)
    return await message.edit_text(text, **kwargs)


def _subscription_link_for_format(subscription_url: str, format_name: str) -> str:
    parsed = urlsplit(str(subscription_url or "").strip())
    query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key.lower() != "format"]
    query.append(("format", str(format_name or "").strip().lower()))
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


def _subscription_copy_button(*, label: str, value: str, fallback_callback: str) -> InlineKeyboardButton:
    if SUPPORTS_BTN_COPY_TEXT and len(value) <= 256:
        return InlineKeyboardButton(text=label, copy_text=value)
    return InlineKeyboardButton(text=label.replace("Скопировать", "Показать"), callback_data=fallback_callback)


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
        current_task = asyncio.current_task()
        try:
            await asyncio.sleep(AUTO_DELETE_SECONDS)
            await bot.delete_message(chat_id=int(chat_id), message_id=int(message_id))
        except Exception:
            pass
        finally:
            _auto_delete_scheduled.discard(key)
            if _auto_delete_tasks.get(key) is current_task:
                _auto_delete_tasks.pop(key, None)

    _auto_delete_tasks[key] = asyncio.create_task(_delete_later())


def _cancel_auto_delete(chat_id: int, message_id: int) -> None:
    key = (int(chat_id), int(message_id))
    task = _auto_delete_tasks.pop(key, None)
    if task is not None:
        task.cancel()
    _auto_delete_scheduled.discard(key)


def _preserve_outgoing_message(chat_id: int, message_id: int) -> None:
    chat_id = int(chat_id)
    message_id = int(message_id)
    _cancel_auto_delete(chat_id, message_id)
    if last_bot_message.get(chat_id) == message_id:
        last_bot_message.pop(chat_id, None)


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

        async def _wrapped(*args, _orig=original, track_context: bool = True, **kwargs):
            result = await _orig(*args, **kwargs)
            try:
                if track_context:
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
    emoji_key: str | None = None,
) -> dict[str, str]:
    resolved_icon = icon_custom_emoji_id
    resolved_text = str(text or "").strip()
    if emoji_key:
        if resolved_icon is None and SUPPORTS_BTN_ICON:
            resolved_icon = custom_emoji_id(emoji_key)
        resolved_text = emoji_button_label(
            emoji_key,
            resolved_text,
            icon_supported=bool(resolved_icon),
        )

    spec: dict[str, str] = {"text": resolved_text}
    if emoji_key:
        spec["emoji_key"] = str(emoji_key)
    if callback_data:
        spec["callback_data"] = callback_data
    if url:
        spec["url"] = url
    if web_app_url:
        spec["web_app_url"] = web_app_url
    if style:
        spec["style"] = style
    if resolved_icon:
        spec["icon_custom_emoji_id"] = resolved_icon
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


def _rows_without_custom_icons(
    rows: list[list[dict[str, str]]],
) -> list[list[dict[str, str]]]:
    fallback_rows: list[list[dict[str, str]]] = []
    for row in rows:
        fallback_row: list[dict[str, str]] = []
        for spec in row:
            item = dict(spec)
            had_custom_icon = bool(item.get("icon_custom_emoji_id"))
            item.pop("icon_custom_emoji_id", None)
            emoji_key = item.pop("emoji_key", None)
            if emoji_key and had_custom_icon:
                item["text"] = emoji_button_label(
                    emoji_key,
                    str(item.get("text") or ""),
                    icon_supported=False,
                )
            fallback_row.append(item)
        fallback_rows.append(fallback_row)
    return fallback_rows


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
            fallback_rows = _rows_without_custom_icons(rows)
            if fallback_rows == rows:
                return False
            payload["reply_markup"] = _keyboard_payload(fallback_rows)
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
        fallback_rows = _rows_without_custom_icons(rows)
        if fallback_rows == rows:
            return False
        try:
            sent = await bot.send_message(
                chat_id=int(chat_id),
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
                reply_markup=_keyboard_from_specs(fallback_rows),
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


async def _send_rich_copy(
    *,
    message: Message,
    bot: Bot,
    chat_id: int,
    copy: RichMessageCopy,
    rows: list[list[dict[str, str]]],
    preserve: bool = False,
) -> bool:
    sent = None
    rich_sender = getattr(bot, "send_rich_message", None)
    if TelegramInputRichMessage is not None and callable(rich_sender):
        try:
            sent = await rich_sender(
                chat_id=int(chat_id),
                rich_message=TelegramInputRichMessage(html=copy.rich_html),
                reply_markup=_keyboard_from_specs(rows),
            )
        except Exception:
            fallback_rows = _rows_without_custom_icons(rows)
            if fallback_rows != rows:
                try:
                    sent = await rich_sender(
                        chat_id=int(chat_id),
                        rich_message=TelegramInputRichMessage(html=copy.rich_html),
                        reply_markup=_keyboard_from_specs(fallback_rows),
                    )
                except Exception:
                    sent = None
    if sent is None:
        try:
            sent = await message.answer(
                copy.fallback_html,
                parse_mode=ParseMode.HTML,
                reply_markup=_keyboard_from_specs(rows),
                disable_web_page_preview=True,
            )
        except Exception:
            fallback_rows = _rows_without_custom_icons(rows)
            if fallback_rows == rows:
                return False
            try:
                sent = await message.answer(
                    copy.fallback_html,
                    parse_mode=ParseMode.HTML,
                    reply_markup=_keyboard_from_specs(fallback_rows),
                    disable_web_page_preview=True,
                )
            except Exception:
                return False

    message_id = int(getattr(sent, "message_id", 0) or 0)
    if message_id:
        await _track_context_message(
            bot=bot,
            chat_id=int(chat_id),
            tg_id=int(chat_id),
            message_id=message_id,
        )
        if preserve:
            _preserve_outgoing_message(int(chat_id), message_id)
    return True


async def _edit_rich_copy(
    *,
    callback: CallbackQuery,
    copy: RichMessageCopy,
    rows: list[list[dict[str, str]]],
) -> bool:
    message = callback.message
    bot = getattr(message, "bot", None) or getattr(callback, "bot", None)
    chat_id = int(getattr(getattr(message, "chat", None), "id", callback.from_user.id))
    message_id = int(getattr(message, "message_id", 0) or 0)

    if bot is not None and bool(getattr(message, "photo", None)):
        return await _send_rich_copy(
            message=message,
            bot=bot,
            chat_id=chat_id,
            copy=copy,
            rows=rows,
        )

    if bot is not None and message_id and TelegramInputRichMessage is not None:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                rich_message=TelegramInputRichMessage(html=copy.rich_html),
                reply_markup=_keyboard_from_specs(rows),
            )
            await _track_context_message(
                bot=bot,
                chat_id=chat_id,
                tg_id=int(callback.from_user.id),
                message_id=message_id,
            )
            return True
        except Exception:
            fallback_rows = _rows_without_custom_icons(rows)
            if fallback_rows != rows:
                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        rich_message=TelegramInputRichMessage(html=copy.rich_html),
                        reply_markup=_keyboard_from_specs(fallback_rows),
                    )
                    await _track_context_message(
                        bot=bot,
                        chat_id=chat_id,
                        tg_id=int(callback.from_user.id),
                        message_id=message_id,
                    )
                    return True
                except Exception:
                    pass

    edit_rows = rows if bot is not None else _rows_without_custom_icons(rows)
    try:
        await message.edit_text(
            copy.fallback_html,
            parse_mode=ParseMode.HTML,
            reply_markup=_keyboard_from_specs(edit_rows),
            disable_web_page_preview=True,
        )
    except Exception:
        fallback_rows = _rows_without_custom_icons(rows)
        if fallback_rows == edit_rows:
            return False
        try:
            await message.edit_text(
                copy.fallback_html,
                parse_mode=ParseMode.HTML,
                reply_markup=_keyboard_from_specs(fallback_rows),
                disable_web_page_preview=True,
            )
        except Exception:
            return False

    if bot is not None and message_id:
        await _track_context_message(
            bot=bot,
            chat_id=chat_id,
            tg_id=int(callback.from_user.id),
            message_id=message_id,
        )
    return True


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
            fallback_rows = _rows_without_custom_icons(rows)
            if fallback_rows == rows:
                return False
            payload["reply_markup"] = _keyboard_payload(fallback_rows)
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
        fallback_rows = _rows_without_custom_icons(rows)
        if fallback_rows == rows:
            return False
        try:
            await bot.edit_message_text(
                chat_id=int(chat_id),
                message_id=int(message_id),
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
                reply_markup=_keyboard_from_specs(fallback_rows),
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
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _track_bonus_event(*, tg_id: int, event_name: str, meta: dict | None = None) -> None:
    track_event(
        tg_id=int(tg_id),
        event_name=str(event_name or "").strip()[:64],
        source="bot",
        meta=meta or None,
    )


def _activation_code_safe_meta(code: str) -> dict:
    normalized = str(code or "").strip().upper()
    if not normalized:
        return {}
    return {
        "code_preview": f"...{normalized[-4:]}",
        "code_fp": hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16],
        "code_len": len(normalized),
    }


_BOT_ENTRY_META_KEYS = {
    "command",
    "created_new",
    "entrypoint",
    "start_arg_kind",
    "start_arg_present",
}


def _track_bot_entry(*, tg_id: int, entrypoint: str, meta: dict | None = None) -> None:
    safe_meta = {"entrypoint": str(entrypoint or "").strip()[:32]}
    for key, value in (meta or {}).items():
        if key not in _BOT_ENTRY_META_KEYS:
            continue
        safe_meta[str(key)] = value
    try:
        track_event(
            tg_id=int(tg_id),
            event_name="bot_entry_opened",
            source="bot",
            meta=safe_meta,
        )
    except Exception as exc:
        logger.debug("bot entry analytics failed tg_id=%s entrypoint=%s: %s", tg_id, entrypoint, exc)


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
import channel_bonus_service
import device_pairing_service
from economy_service import create_referral_relationship, record_successful_payment_grant
from account_foundation_service import (
    ensure_user_account_foundation,
)
from rewards_service import (
    PAID_FORTNIGHTLY_DISCOUNTS_V3,
    PAID_WEEKLY_DISCOUNTS_V2,
    PAID_WEEKLY_V1,
    InvalidWheelConfig,
    RewardConflict,
    RewardDisabled,
    RewardDomainError,
    RewardForbidden,
    get_wheel_state,
    parse_paid_weekly_config,
    spin_wheel,
)
from models import (
    Achievement,
    AccessKey,
    AdminAudit,
    AppSetting,
    CampaignSend,
    EntitlementGrant,
    Event,
    FamilySlot,
    GiftCard,
    IncentiveCampaign,
    KeyActionHistory,
    LiveUpdate,
    PointsLedger,
    PromoCode,
    PromoUsage,
    ReferralRelationship,
    Review,
    StartLink,
    SupportTicket,
    SupportTicketMessage,
    Template,
    User,
    UserKeyPolicy,
    UserNode,
)
from nodes_repo import enabled_nodes
from events_service import track_event
from acquisition_service import AcquisitionError, consume_acquisition_handoff
from free_cycle_service import mark_user_became_free, queue_free_profile_reentry
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
    claim_legacy_ticket,
    create_ticket,
    get_ticket_by_id,
    get_user_active_ticket,
    list_active_tickets,
    list_ticket_messages,
    list_user_tickets,
    resolve_support_account_id,
    resolve_ticket_notification_tg_id,
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


def _stars_entitlement_projection_applied(payment_fingerprint: str) -> bool:
    order_id = str(payment_fingerprint or "").strip()
    if not order_id:
        return False
    s = Session()
    try:
        grant = (
            s.query(EntitlementGrant)
            .filter(
                EntitlementGrant.source == "provider_payment",
                EntitlementGrant.provider == "stars",
                EntitlementGrant.external_order_id == order_id,
                EntitlementGrant.status.in_(["active", "expired"]),
            )
            .first()
        )
        if grant is None or str(grant.grant_kind or "") != "paid_access":
            return False
        try:
            metadata = json.loads(str(grant.metadata_json or "{}"))
        except (TypeError, ValueError):
            return False
        return isinstance(metadata, dict) and bool(metadata.get("projection_already_applied"))
    finally:
        s.close()


def _stars_fulfillment_retry_keyboard(payment_grant_id: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    grant_id = str(payment_grant_id or "").strip()
    if grant_id:
        rows.append(
            [
                InlineKeyboardButton(
                    text="🔄 Повторить выдачу доступа",
                    callback_data=f"retry_stars:{grant_id}",
                )
            ]
        )
    rows.extend(
        [
            [InlineKeyboardButton(text="💬 Написать в поддержку", url=f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _send_stars_fulfillment_retry(message: Message, *, payment_grant_id: str) -> None:
    await message.answer(
        "❌ Не получилось обновить доступ. Оплата сохранена — нажмите «Повторить выдачу доступа».",
        reply_markup=_stars_fulfillment_retry_keyboard(payment_grant_id),
    )


def _validated_owned_panel_client(*, tg_id: int, panel_client: dict | None) -> dict[str, object]:
    client = dict(panel_client or {})
    client_uuid = str(client.get("id") or "").strip()
    panel_email = str(client.get("email") or "").strip()
    sub_id = str(client.get("subId") or "").strip()
    panel_tg_id = str(client.get("tgId") or "").strip()
    node_code = str(client.get("_node_code") or "").strip()
    try:
        normalized_uuid = str(uuid.UUID(client_uuid))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("panel client UUID is missing or invalid")
    if panel_tg_id and panel_tg_id != str(int(tg_id)):
        raise ValueError("panel client ownership mismatch")
    if not panel_email or len(panel_email) > 100 or any(ch in panel_email for ch in "\r\n\x00"):
        raise ValueError("panel email is missing or invalid")
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", sub_id):
        raise ValueError("panel subId is missing or invalid")
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,32}", node_code):
        raise ValueError("panel node provenance is missing or invalid")
    try:
        node_id = int(client.get("_node_id") or 0)
    except (TypeError, ValueError):
        node_id = 0
    return {
        "client_uuid": normalized_uuid,
        "panel_email": panel_email,
        "sub_id": sub_id,
        "node_code": node_code,
        "node_id": node_id,
    }


def _reconcile_owned_panel_client(
    *,
    tg_id: int,
    panel_client: dict | None,
    provider_order_id: str,
) -> dict[str, object]:
    credential = _validated_owned_panel_client(tg_id=int(tg_id), panel_client=panel_client)
    now = _utcnow().replace(microsecond=0)
    session = Session()
    try:
        user = session.query(User).filter_by(tg_id=int(tg_id)).with_for_update().one()
        grant = (
            session.query(EntitlementGrant)
            .filter_by(provider="stars", external_order_id=str(provider_order_id))
            .with_for_update()
            .one()
        )
        try:
            grant_metadata = json.loads(str(grant.metadata_json or "{}"))
        except (TypeError, ValueError):
            grant_metadata = {}
        if (
            str(grant.grant_kind or "") != "paid_access"
            or not isinstance(grant_metadata, dict)
            or not bool(grant_metadata.get("projection_already_applied"))
        ):
            raise ValueError("Stars entitlement projection is not applied")

        user.uuid = str(credential["client_uuid"])
        user.email = str(credential["panel_email"])
        user.sub_token = str(credential["sub_id"])

        access_key = (
            session.query(AccessKey)
            .filter_by(tg_id=int(tg_id), node_code=str(credential["node_code"]))
            .with_for_update()
            .one_or_none()
        )
        if access_key is None:
            access_key = (
                session.query(AccessKey)
                .filter_by(tg_id=int(tg_id), key_uuid=str(credential["client_uuid"]))
                .with_for_update()
                .one_or_none()
            )
            if (
                access_key is not None
                and access_key.node_code
                and str(access_key.node_code) != str(credential["node_code"])
            ):
                raise ValueError("panel client node provenance mismatch")
        if access_key is None:
            access_key = AccessKey(
                tg_id=int(tg_id),
                key_uuid=str(credential["client_uuid"]),
                panel_email=str(credential["panel_email"]),
                node_code=str(credential["node_code"]),
                pool_code="premium_pool",
                state="active",
                source="stars_panel_reconcile",
                is_primary=True,
                provisioned_at=now,
                created_at=now,
                updated_at=now,
            )
            session.add(access_key)
        else:
            access_key.key_uuid = str(credential["client_uuid"])
            access_key.panel_email = str(credential["panel_email"])
            access_key.node_code = str(credential["node_code"])
            access_key.pool_code = "premium_pool"
            access_key.state = "active"
            access_key.is_primary = True
            access_key.provisioned_at = access_key.provisioned_at or now
            access_key.updated_at = now

        if int(credential["node_id"]) > 0:
            user_node = (
                session.query(UserNode)
                .filter_by(tg_id=int(tg_id), node_id=int(credential["node_id"]))
                .with_for_update()
                .one_or_none()
            )
            if user_node is None:
                session.add(
                    UserNode(
                        tg_id=int(tg_id),
                        node_id=int(credential["node_id"]),
                        client_uuid=str(credential["client_uuid"]),
                        panel_email=str(credential["panel_email"]),
                        created_at=now,
                    )
                )
            else:
                user_node.client_uuid = str(credential["client_uuid"])
                user_node.panel_email = str(credential["panel_email"])

        grant_metadata["panel_credentials_reconciled"] = True
        grant_metadata["panel_credentials_reconciled_at"] = now.isoformat()
        grant_metadata["panel_node_code"] = str(credential["node_code"])
        grant_metadata["panel_node_evidence"] = (
            "user_node" if int(credential["node_id"]) > 0 else "legacy_access_key"
        )
        grant.metadata_json = json.dumps(
            grant_metadata,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        grant.updated_at = now
        session.commit()
        return credential
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Achievement definitions: id -> {name, description, reward_days, condition}
ACHIEVEMENTS = {
    "first_sub": {
        "name": "🟢 Inception",
        "desc": "Первая активация доступа",
        "days": 0,
        "icon": "🟢"
    },
    "week_active": {
        "name": "🛡 Sentinel",
        "desc": "7 дней непрерывной оптимизации",
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
        "desc": "Год в системе POKROV Network",
        "days": 30,
        "icon": "👑"
    },
}

# Tariff definitions (RUB-first in UX; legacy Stars values stay for compatibility).
TARIFFS = {
    "trial": {
        # Trial/fallback tier: enforced by subscription JSON allowlist rules (see api.py).
        "name": "🚀 Тест на 5 дней",
        "stars": 0,
        "days": 5,
        "gb": TRIAL_LIMIT_GB,
        "subId": "TRIAL_5D",
        "sub_type": "TRIAL"
    },
    "start_99": {
        "name": "⚡ Приветственный 30 дней",
        "stars": 99,
        "days": 30,
        "gb": 0,
        "subId": "START_99",
        "sub_type": "PAID"
    },
    "1_month": {
        "name": "📅 1 Месяц",
        "stars": 239,
        "days": 30,
        "gb": 0,
        "subId": "MONTHLY",
        "sub_type": "PAID"
    },
    "3_months": {
        "name": "📅 3 Месяца",
        "stars": 669,
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
        "stars": 1699,
        "days": 273,
        "gb": 0,
        "subId": "NINE_MONTHS",
        "sub_type": "PAID"
    },
    "12_months": {
        "name": "📅 12 Месяцев",
        "stars": 1999,
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


REFERRAL_BONUS_DAYS = int(os.getenv("REFERRAL_BONUS_DAYS", "10"))

# Gift card types: {key: {name, stars, days}}
GIFT_CARD_TYPES = {
    "mini": {
        "name": "🎁 Mini (7 Дней)",
        "stars": 59,
        "days": 7
    },
    "standard": {
        "name": "🎁 Standard (30 Дней)",
        "stars": 239,
        "days": 30
    },
    "premium": {
        "name": "🎁 Premium (90 Дней)",
        "stars": 669,
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
        ensure_user_account_foundation(session, existing, now=_utcnow())
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
    ensure_user_account_foundation(session, user, now=_utcnow())
    session.commit()
    session.close()
    return user

def sync_telegram_identity(tg_id: int, username: str | None) -> bool:
    """Persist Telegram username for both telegram-native and app-linked user rows."""
    session = Session()
    normalized = str(username or "").strip()[:100] or None
    changed = False
    try:
        user = session.query(User).filter_by(tg_id=int(tg_id)).first()
        if user and user.username != normalized:
            user.username = normalized
            changed = True

        linked_rows = session.query(User).filter(User.linked_telegram_id == int(tg_id)).all()
        for row in linked_rows:
            if row.linked_telegram_username != normalized:
                row.linked_telegram_username = normalized
                changed = True

        projection_user = user or (linked_rows[0] if linked_rows else None)
        if projection_user is not None:
            ensure_user_account_foundation(session, projection_user, now=_utcnow())
        session.commit()
        return changed
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


def update_user_username(tg_id: int, username: str | None):
    """Update user's telegram username"""
    sync_telegram_identity(tg_id, username)

def generate_sub_token() -> str:
    """Generate unique subscription token (43 chars, impossible to guess)"""
    return secrets.token_urlsafe(32)

def generate_referral_code() -> str:
    """Generate unique 8-char referral code like SWAZ7K3F"""
    import string
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "SWAZ" + "".join(secrets.choice(chars) for _ in range(4))
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
    """Project one canonical account referral relationship into legacy user fields."""
    if tg_id == referrer_id:
        return False
    session = Session()
    try:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        referrer = session.query(User).filter_by(tg_id=referrer_id).first()
        if not user or not referrer:
            return False
        ensure_user_account_foundation(session, user, now=_utcnow())
        ensure_user_account_foundation(session, referrer, now=_utcnow())
        session.flush()
        existing = session.query(ReferralRelationship).filter_by(referred_account_id=str(user.account_id)).first()
        if existing is not None:
            if str(existing.referrer_account_id) == str(referrer.account_id):
                user.referrer_id = int(referrer_id)
                session.commit()
            return False
        create_referral_relationship(
            session,
            referred_account_id=str(user.account_id),
            referrer_account_id=str(referrer.account_id),
            source="bot_code",
            now=_utcnow(),
        )
        user.referrer_id = referrer_id
        session.commit()
        return True
    except ValueError:
        session.rollback()
        return False
    finally:
        session.close()

def set_referrer_by_code(tg_id: int, referral_code: str) -> bool:
    """Link user to their referrer by referral code"""
    referrer_id = get_user_by_referral_code(referral_code)
    if not referrer_id or referrer_id == tg_id:
        return False
    return set_referrer(tg_id, referrer_id)

async def award_referral_bonus(referrer_id: int, bonus_days: int = REFERRAL_BONUS_DAYS) -> bool:
    """Retired direct grant; payment fulfillment uses the guarded 72h queue."""
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
    ensure_user_account_foundation(session, user, now=_utcnow())
    session.commit()
    session.close()
    return True


def _tos_offer_text() -> str:
    return (
        "📜 *Условия использования*\n\n"
        "Перед началом нужно принять простые условия:\n\n"
        "• Сервис предоставляется «как есть»\n"
        "• Пользователь сам несёт ответственность за соблюдение законов\n"
        "• Запрещено использование для противоправных действий\n"
        "• Возврат средств при блокировках не гарантируется\n\n"
        "_Нажимая «Принимаю условия», вы подтверждаете согласие с полным текстом оферты._"
    )


def _tos_offer_keyboard(*, back_callback: str = "back") -> InlineKeyboardMarkup:
    offer_url = f"https://{PUBLIC_WEB_DOMAIN.strip().strip('/')}/offer"
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
            ensure_user_account_foundation(session, user, now=_utcnow())
            session.commit()
            session.refresh(user)
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
        ensure_user_account_foundation(session, user, now=_utcnow())
        session.commit()
        session.refresh(user)
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
        session.add(CampaignSend(tg_id=int(tg_id), campaign_key=str(campaign_key), sent_at=_utcnow()))
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
        return False
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
    # The old gift link remains attributable as a normal referral, but cannot
    # grant invitee days. The inviter reward is queued only after first payment.
    return False, "disabled"


def _channel_name_for_url() -> str:
    channel = (NEWS_CHANNEL_ID or "@pokrov_vpn").strip().lstrip("@")
    return channel or "pokrov_vpn"


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
    now_ts = int(datetime.now(timezone.utc).timestamp())
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
    base = (PAY_CHECKOUT_URL or "").strip() or "https://pay.pokrov.space/checkout/"
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
    base = (WEBAPP_URL or "").strip() or "https://app.pokrov.space/"
    parsed = urlsplit(base)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["web_session_token"] = str(token or "").strip()
    built_query = urlencode(query)
    if parsed.scheme and parsed.netloc:
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", built_query, parsed.fragment))
    return urlunsplit(("", "", parsed.path or "/", built_query, parsed.fragment))


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
        return {"promo_code": "", "campaign_key": "", "opening_bonus": False, "app_link_account_id": 0}
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
        return {"promo_code": "", "campaign_key": "", "opening_bonus": False, "app_link_account_id": 0}

    action = str(getattr(row, "target_action", "") or "").strip()
    lowered = action.lower()
    if lowered == "opening_bonus":
        return {"promo_code": "", "campaign_key": "", "opening_bonus": True, "app_link_account_id": 0}
    if lowered.startswith("promo:"):
        promo = _sanitize_start_token(action.split(":", 1)[1], max_len=20, uppercase=True)
        return {"promo_code": promo, "campaign_key": "", "opening_bonus": False, "app_link_account_id": 0}
    if lowered.startswith("campaign:"):
        campaign = _sanitize_start_token(action.split(":", 1)[1], max_len=64, uppercase=False)
        return {"promo_code": "", "campaign_key": campaign, "opening_bonus": False, "app_link_account_id": 0}
    if lowered.startswith("campaign_promo:"):
        rest = action.split(":", 1)[1].strip()
        parts = rest.split(":", 1)
        campaign = _sanitize_start_token(parts[0] if parts else "", max_len=64, uppercase=False)
        promo = _sanitize_start_token(parts[1] if len(parts) > 1 else "", max_len=20, uppercase=True)
        return {"promo_code": promo, "campaign_key": campaign, "opening_bonus": False, "app_link_account_id": 0}
    if lowered.startswith("app_link:"):
        try:
            account_tg_id = int(action.split(":", 1)[1].strip())
        except Exception:
            account_tg_id = 0
        return {
            "promo_code": "",
            "campaign_key": "",
            "opening_bonus": False,
            "app_link_account_id": max(0, int(account_tg_id)),
        }
    return {"promo_code": "", "campaign_key": "", "opening_bonus": False, "app_link_account_id": 0}


def _bind_app_account_to_telegram(
    *,
    account_tg_id: int,
    telegram_id: int,
    telegram_username: str | None,
    start_code: str,
) -> str:
    if (
        int(account_tg_id) <= 0
        or int(telegram_id) <= 0
        or int(account_tg_id) == int(telegram_id)
    ):
        return "invalid"
    if int(telegram_id) == int(ADMIN_ID or 0) and int(account_tg_id) != int(ADMIN_ID or 0):
        return "telegram_already_linked"
    raw_code = str(start_code or "").strip().lower()
    session = Session()
    try:
        row = (
            session.query(StartLink)
            .filter(func.lower(StartLink.code) == raw_code)
            .filter(StartLink.is_active == True)
            .with_for_update()
            .first()
        )
        if not row:
            return "expired"
        locked_users = (
            session.query(User)
            .filter(User.tg_id.in_([int(account_tg_id), int(telegram_id)]))
            .order_by(User.tg_id.asc())
            .with_for_update()
            .all()
        )
        user = next((item for item in locked_users if int(item.tg_id) == int(account_tg_id)), None)
        telegram_user = next(
            (item for item in locked_users if int(item.tg_id) == int(telegram_id)),
            None,
        )
        if not user or telegram_user is None:
            return "not_found"
        incoming_to_account = (
            session.query(User.tg_id)
            .filter(User.linked_telegram_id == int(account_tg_id))
            .filter(User.tg_id != int(account_tg_id))
            .first()
        )
        telegram_user_linked_id = int(
            getattr(telegram_user, "linked_telegram_id", 0) or 0
        )
        if incoming_to_account is not None or telegram_user_linked_id > 0:
            return "transitive_link_not_supported"
        other = (
            session.query(User)
            .filter(User.linked_telegram_id == int(telegram_id))
            .filter(User.tg_id != int(account_tg_id))
            .first()
        )
        if other:
            return "telegram_already_linked"
        linked_id = int(getattr(user, "linked_telegram_id", 0) or 0)
        if linked_id and linked_id != int(telegram_id):
            return "account_linked_elsewhere"

        now = _utcnow()
        user.linked_telegram_id = int(telegram_id)
        user.linked_telegram_username = str(telegram_username or "").strip() or None
        user.linked_telegram_linked_at = now
        row.is_active = False
        row.updated_at = now
        session.flush()
        ensure_user_account_foundation(session, user, now=now)
        session.commit()
        return "linked" if linked_id != int(telegram_id) else "already_linked"
    except Exception:
        session.rollback()
        return "error"
    finally:
        session.close()


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


def _classify_start_arg_for_analytics(
    *,
    start_arg: str,
    referral_code: str | None = None,
    deeplink_promo_code: str = "",
    deeplink_campaign_key: str = "",
    friend_gift_referral_code: str = "",
    opening_bonus_requested: bool = False,
    app_link_account_id: int = 0,
) -> str:
    if not (start_arg or "").strip():
        return "plain"
    if _parse_acquisition_start_handle(start_arg):
        return "acquisition"
    if int(app_link_account_id or 0) > 0:
        return "app_link"
    if (start_arg or "").strip().lower() in {"pay", "renew"}:
        return "payment"
    if opening_bonus_requested:
        return "opening_bonus"
    if friend_gift_referral_code:
        return "friend_gift"
    if referral_code:
        return "referral"
    if deeplink_promo_code and deeplink_campaign_key:
        return "campaign_promo"
    if deeplink_promo_code:
        return "promo"
    if deeplink_campaign_key:
        return "campaign"
    return "other"


def _parse_acquisition_start_handle(start_arg: str) -> str:
    raw = str(start_arg or "").strip()
    if not raw.lower().startswith("acq_"):
        return ""
    handle = raw[4:]
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,60}", handle):
        return ""
    return handle


def _consume_bot_acquisition_handoff(*, tg_id: int, user: User | None, start_arg: str) -> bool:
    handle = _parse_acquisition_start_handle(start_arg)
    if not handle or user is None:
        return False
    session = Session()
    try:
        consume_acquisition_handoff(
            session,
            raw_handle=handle,
            expected_purpose="telegram_continue",
            bound_tg_id=int(tg_id),
            bound_account_id=str(getattr(user, "account_id", "") or "") or None,
            now=_utcnow(),
        )
        session.commit()
        return True
    except AcquisitionError:
        session.rollback()
        return False
    except Exception:
        session.rollback()
        logger.exception("bot acquisition handoff failed tg_id=%s", int(tg_id))
        return False
    finally:
        session.close()


def _channel_bonus_ineligible_reason(*, tg_id: int, user: User | None) -> str | None:
    if user and _normalize_sub_type(user.sub_type) == "MANUAL":
        return "Для ручных аккаунтов бонус за канал отключён."
    if user and getattr(user, "channel_bonus_claimed_at", None):
        return "Бонус за канал уже был активирован для этого аккаунта."
    if _campaign_claimed(tg_id=tg_id, campaign_key=OPENING_PREMIUM_CAMPAIGN_KEY):
        return "Для этого аккаунта уже активирован промо-бонус по ссылке."
    return None


def _channel_bonus_eligible(*, tg_id: int, user: User | None) -> bool:
    return _channel_bonus_ineligible_reason(tg_id=tg_id, user=user) is None


def _channel_acquisition_gate_blocks(*, user: User | None, action: str, is_member: bool) -> bool:
    if bool(is_member):
        return False
    action_key = str(action or "").strip().lower()
    if action_key not in {"acquisition", "trial"}:
        return False
    if user is None:
        return True
    is_genuinely_new = (
        not bool(user.first_purchase_done)
        and not bool(user.trial_used)
        and user.channel_bonus_claimed_at is None
        and str(user.sub_type or "").strip().upper() in {"", "FREE", "PENDING"}
    )
    return bool(is_genuinely_new)


def _channel_acquisition_gate_keyboard(retry_callback_data: str) -> InlineKeyboardMarkup:
    channel_name = _channel_name_for_url()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться на канал", url=f"https://t.me/{channel_name}")],
            [InlineKeyboardButton(text="✅ Проверить подписку", callback_data=str(retry_callback_data))],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
        ]
    )


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
        "🎁 *Бонус за канал*\n\n"
        f"Подпишитесь на [канал POKROV]({channel_url}) и получите *+{CHANNEL_PREMIUM_DAYS} дней полного доступа*.\n"
        "Следующий шаг: после подписки нажмите «Проверить и получить».\n\n"
        "Если не хотите делать это сейчас, можно продолжить без бонуса."
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

    session = Session()
    try:
        db_user = session.query(User).filter_by(tg_id=int(tg_id)).first()
        if not db_user:
            return False, "user_not_found"

        async def _bot_membership(_channel: str, telegram_id: int) -> tuple[bool, str]:
            is_member = await check_subscription(int(telegram_id), bot)
            return bool(is_member), "member" if is_member else "not_member"

        result = await channel_bonus_service.claim_channel_bonus(
            s=session,
            user=db_user,
            tg_id=int(tg_id),
            public_channel=PUBLIC_CHANNEL,
            bonus_days=CHANNEL_PREMIUM_DAYS,
            opening_bonus_campaign_key=OPENING_PREMIUM_CAMPAIGN_KEY,
            subscriber_campaign_key="channel_subscriber_v2",
            points_expiry_days=max(1, int(os.getenv("POINTS_EXPIRY_DAYS", "90"))),
            is_channel_member=_bot_membership,
        )
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
    return True, "already_claimed" if bool(result.get("already_claimed")) else "activated"


# ==========================================
#         WHEEL OF FORTUNE
# ==========================================

WHEEL_DEFAULT_PRIZES: list[tuple[int, int]] = [
    (int(row["days"]), int(row["weight"]))
    for row in PAID_WEEKLY_V1["weights"]
]
WHEEL_PRESETS: dict[str, list[tuple[int, int]]] = {
    "paid_weekly_v1": WHEEL_DEFAULT_PRIZES,
}
WHEEL_DEFAULT_COOLDOWN_HOURS = 168


def _cooldown_days_from_hours(hours: int) -> int:
    val = max(1, int(hours))
    return max(1, min(90, int((val + 23) // 24)))


def _load_wheel_config_payload(session=None) -> dict[str, Any] | None:
    owns_session = session is None
    s = session or Session()
    try:
        row = s.query(AppSetting).filter(AppSetting.key == "wheel_config").first()
    finally:
        if owns_session:
            s.close()
    if not row or not str(getattr(row, "value_json", "") or "").strip():
        return None
    try:
        payload = json.loads(str(row.value_json))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {"preset": "invalid"}
    return dict(payload) if isinstance(payload, dict) else {"preset": "invalid"}


def _load_wheel_config() -> dict[str, Any]:
    raw = _load_wheel_config_payload()
    try:
        config = parse_paid_weekly_config(
            {} if raw is None else raw,
            explicit=raw is not None,
        )
    except InvalidWheelConfig as exc:
        return {
            "preset": "invalid",
            "weights": [],
            "cooldown_hours": 0,
            "cooldown_days": 0,
            "validation_code": exc.code,
        }
    return {
        "preset": config.preset,
        "weights": [
            (int(outcome.value), int(outcome.weight))
            for outcome in config.outcomes
            if outcome.kind == "days"
        ],
        "outcomes": [
            (outcome.kind, int(outcome.value), int(outcome.weight))
            for outcome in config.outcomes
        ],
        "cooldown_hours": int(config.cooldown_hours),
        "cooldown_days": int(_cooldown_days_from_hours(config.cooldown_hours)),
    }


def _save_wheel_config(
    *,
    weights: list[tuple[int, int]] | None = None,
    cooldown_days: int | None = None,
    cooldown_hours: int | None = None,
    preset: str | None = None,
) -> dict:
    selected_preset = str(preset or "paid_fortnightly_discounts_v3")
    selected_cooldown = (
        int(cooldown_hours)
        if cooldown_hours is not None
        else int(cooldown_days) * 24 if cooldown_days is not None else 336
    )
    if selected_preset == "paid_fortnightly_discounts_v3":
        candidate = {
            "preset": selected_preset,
            "weights": [dict(row) for row in PAID_FORTNIGHTLY_DISCOUNTS_V3["weights"]],
            "cooldown_hours": selected_cooldown,
        }
    elif selected_preset == "paid_weekly_discounts_v2":
        candidate = {
            "preset": selected_preset,
            "weights": [dict(row) for row in PAID_WEEKLY_DISCOUNTS_V2["weights"]],
            "cooldown_hours": selected_cooldown,
        }
    else:
        candidate = {
            "preset": selected_preset,
            "weights": [
                {"days": int(days), "weight": int(weight)}
                for days, weight in (weights or WHEEL_DEFAULT_PRIZES)
            ],
            "cooldown_hours": selected_cooldown,
        }
    config = parse_paid_weekly_config(candidate, explicit=True)
    payload_weights = [
        (
            {"days": int(outcome.value), "weight": int(outcome.weight)}
            if config.preset == "paid_weekly_v1"
            else {
                "kind": outcome.kind,
                "value": int(outcome.value),
                "weight": int(outcome.weight),
            }
        )
        for outcome in config.outcomes
    ]
    payload = {
        "preset": config.preset,
        "weights": payload_weights,
        "cooldown_hours": int(config.cooldown_hours),
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
    # Compatibility helper for the fixed, server-authoritative public sectors.
    return _wheel_prizes()


def _ensure_reward_achievement(
    session,
    *,
    tg_id: int,
    achievement_id: str,
    now: datetime,
) -> None:
    exists = (
        session.query(Achievement.id)
        .filter(
            Achievement.tg_id == int(tg_id),
            Achievement.achievement_id == str(achievement_id),
        )
        .first()
    )
    if not exists:
        session.add(
            Achievement(
                tg_id=int(tg_id),
                achievement_id=str(achievement_id),
                unlocked_at=now,
            )
        )

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
    
    now = _utcnow()
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
            if user.expiry_at and user.expiry_at > _utcnow():
                user.expiry_at += timedelta(days=bonus_days)
            else:
                user.expiry_at = _utcnow() + timedelta(days=bonus_days)
    
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
        days_active = (_utcnow() - user.created_at).days
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
        days_active = (_utcnow() - user.created_at).days
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
    if not norm_code:
        _track_bonus_event(tg_id=int(recipient_tg_id), event_name="gift_redeem_denied", meta={"reason": "invalid_code"})
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
                    _track_bonus_event(
                        tg_id=int(recipient_tg_id),
                        event_name="gift_redeem_denied",
                        meta={
                            **_activation_code_safe_meta(norm_code),
                            "card_type": card_type,
                            "reason": "campaign_restriction_mismatch",
                        },
                    )
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
        _track_bonus_event(
            tg_id=int(recipient_tg_id),
            event_name="gift_redeem_denied",
            meta={
                **_activation_code_safe_meta(norm_code),
                "reason": str(result.get("error") or "redeem_failed"),
            },
        )
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
    _track_bonus_event(
        tg_id=int(recipient_tg_id),
        event_name="gift_redeemed",
        meta={
            **_activation_code_safe_meta(norm_code),
            "card_type": result.get("card_type"),
            "days": days,
            "sync_ok": result.get("sync_ok"),
        },
    )
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
    """Generate the canonical public connection link."""
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

    return build_public_subscription_url(sub_id)


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
        ensure_user_account_foundation(session, user, now=now)
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
    sync_panel = ControlPanel()
    try:
        return bool(await sync_panel.enable_client(user_uuid, enable=is_active))
    except Exception as exc:
        logger.warning("sub_token panel sync failed for tg_id=%s: %s", int(tg_id), exc)
        return False
    finally:
        await sync_panel.close()


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


class TelegramIdentitySyncMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            from_user = getattr(event, "from_user", None)
            if from_user and not bool(getattr(from_user, "is_bot", False)):
                sync_telegram_identity(int(from_user.id), getattr(from_user, "username", None))
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


def _free_speed_mbit_for_user(user: User | None) -> int:
    return FREE_SOFT_SPEED_MBIT if user is not None and user_free_access_role(user) == "free_soft" else FREE_SPEED_MBIT


def _plan_mode_label(sub_type: str | None, *, user: User | None = None) -> str:
    st = _normalize_sub_type(sub_type or "")
    if st in {"TRIAL", "BONUS"} or (st == "FREE" and user is not None and not user_uses_free_pool(user)):
        return "премиум-доступ, без лимита трафика"
    if st in {"FREE", "TRIAL", "BONUS"}:
        speed_mbit = _free_speed_mbit_for_user(user)
        return f"до {FREE_TOTAL_GB} ГБ, {FREE_LIMIT_IP} устройство, до {speed_mbit} Мбит/с"
    return f"платный срок, до {PAID_LIMIT_IP} устройств"


def _free_access_note(user: User) -> str:
    speed_mbit = _free_speed_mbit_for_user(user)
    if user_free_access_role(user) == "free_soft":
        return (
            f"\n\n🆓 Мягкий режим: лимит {FREE_TOTAL_GB} ГБ использован, "
            f"{FREE_LIMIT_IP} устройство (по IP), до {speed_mbit} Мбит/с."
        )
    return (
        f"\n\n🆓 Бесплатный: до {FREE_TOTAL_GB} ГБ, {FREE_LIMIT_IP} устройство (по IP), "
        f"до {speed_mbit} Мбит/с."
    )


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


async def _free_remaining_gb(
    tg_id: int,
    *,
    user: User | None = None,
    timeout_sec: float = 3.0,
) -> tuple[float | None, float]:
    """
    Return (remaining_gb, total_gb).
    remaining_gb=None means usage is temporarily unavailable.
    """
    total_gb = float(FREE_TOTAL_GB)
    if user is not None and user_free_access_role(user) == "free_soft":
        return 0.0, total_gb
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

# User-facing copy lives in portal_bot/bot_texts.py + copy/catalog.ru.json
# (resolved at call time via bot_text()).

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


def _bot_free_codes(user: User | None = None, *, nodes: list | None = None) -> list[str]:
    nodes = list(nodes) if nodes is not None else _bot_enabled_nodes()
    access_role = user_free_access_role(user) if user is not None else "free_standard"
    return free_pool_node_codes(nodes, access_role=access_role)


def _bot_resync_node_codes(user: User, *, nodes: list | None = None) -> list[str] | None:
    state = str(getattr(user, "free_profile_state", "") or "standard").strip().lower()
    if state in {"soft_transition_pending", "reset_pending", "error"}:
        raise ValueError(f"free profile transition blocks resync: {state}")
    if not user_uses_free_pool(user):
        return None
    codes = _bot_free_codes(user, nodes=nodes)
    if not codes:
        raise ValueError(f"free profile role is not configured: {user_free_access_role(user)}")
    return codes


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


def _tariff_choice_context() -> dict[str, object]:
    nodes = _bot_enabled_nodes()
    paid_nodes = paid_pool_nodes(nodes)
    paid_count = len(paid_nodes) if paid_nodes else (len(nodes) if nodes else 1)
    paid_list = (
        ", ".join([_node_label_ru_bot(getattr(n, "code", ""), getattr(n, "name", "")) for n in paid_nodes])
        if paid_nodes
        else ("1 локация" if nodes else "1 локация")
    )
    free_code = str(canonical_free_node_code(nodes) or "").strip().lower()
    free_node = next((n for n in nodes if (getattr(n, "code", "") or "").strip().lower() == free_code), None)
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
        savings.append(f"12 мес: -{s12}%")
    return {
        "paid_count": paid_count,
        "paid_list": paid_list,
        "free_label": free_label,
        "savings": savings,
    }


def build_choose_tariff_rich_copy(*, show_trial: bool = True) -> RichMessageCopy:
    context = _tariff_choice_context()
    return tariff_choice_copy(
        show_trial=show_trial,
        paid_count=int(context["paid_count"]),
        paid_list=str(context["paid_list"]),
        free_label=str(context["free_label"]),
        trial_limit_gb=TRIAL_LIMIT_GB,
        trial_device_limit=FREE_LIMIT_IP,
        paid_device_limit=PAID_LIMIT_IP,
        savings=list(context["savings"]),
    )


def build_choose_tariff_text(*, show_trial: bool = True) -> str:
    context = _tariff_choice_context()
    paid_count = int(context["paid_count"])
    paid_list = str(context["paid_list"])
    free_label = str(context["free_label"])
    savings = list(context["savings"])
    savings_line = (" (" + ", ".join(savings) + ")") if savings else ""

    trial_block = (
        f"*5 дней бесплатно* — {free_label}, до {TRIAL_LIMIT_GB} ГБ, "
        f"до {FREE_LIMIT_IP} устройства, без карты.\n\n"
        if show_trial
        else ""
    )
    title = "*POKROV VPN — выберите вариант*" if show_trial else "*POKROV Premium — выберите срок*"
    return (
        f"{title}\n\n"
        f"{trial_block}"
        f"*Платный доступ* — {paid_count} локаций: {paid_list}\n"
        f"До {PAID_LIMIT_IP} устройств. Безлимитный трафик и без тарифного ограничения скорости¹.\n"
        "Приложения: Android и Windows.\n\n"
        "После теста — от *99 ₽*. Автосписаний нет.\n"
        f"💰 *Экономия на длинном сроке:*{savings_line}\n\n"
        "_¹ Фактическая скорость зависит от сети, устройства, локации и нагрузки; POKROV не ставит тарифный лимит скорости._\n\n"
        "_Выберите вариант ниже, и я открою нужное действие._"
    )


def _tariff_pricing_for_user(tg_id: int, tariff_key: str) -> dict[str, int | bool]:
    tariff = TARIFFS.get(tariff_key)
    if not tariff:
        return {
            "base_price": 0,
            "actual_stars": 0,
            "final_stars": 0,
            "points_to_use": 0,
            "pending_discount_pct": 0,
            "use_discount": False,
        }

    use_discount = has_referral_discount(tg_id) if tariff["stars"] > 0 else False
    pending_discount_pct = get_pending_discount_pct(tg_id) if tariff["stars"] > 0 else 0
    base_price = int(tariff["stars"])
    actual_stars = int(base_price)
    if use_discount:
        actual_stars = int(round(actual_stars * 0.8))
    if pending_discount_pct > 0:
        actual_stars = int(round(actual_stars * (1.0 - (pending_discount_pct / 100.0))))
    actual_stars = max(1, int(actual_stars)) if base_price > 0 else 0

    first_discount_pct = 0.0
    if base_price > 0:
        first_discount_pct = max(0.0, min(0.95, 1.0 - (float(actual_stars) / float(base_price))))
    points_preview = preview_redeemable_points(
        tg_id=tg_id,
        plan_price_stars=base_price,
        first_purchase_discount_pct=first_discount_pct,
    )
    points_to_use = int(points_preview.redeemable_points) if base_price > 0 else 0
    final_stars = max(1, int(actual_stars) - points_to_use) if base_price > 0 else 0
    max_total_discount = int(base_price * STACK_TOTAL_DISCOUNT_CAP)
    if base_price > 0 and base_price - final_stars > max_total_discount:
        final_stars = max(1, int(base_price) - max_total_discount)
        points_to_use = max(0, int(actual_stars) - final_stars)

    return {
        "base_price": int(base_price),
        "actual_stars": int(actual_stars),
        "final_stars": int(final_stars),
        "points_to_use": int(points_to_use),
        "pending_discount_pct": int(pending_discount_pct),
        "use_discount": bool(use_discount),
    }


def _tariff_button_label(*, tg_id: int, tariff_key: str, label: str, marketing_badge: str = "", savings_text: str = "") -> str:
    pricing = _tariff_pricing_for_user(tg_id, tariff_key)
    rub_price = int(pricing["base_price"])
    return f"{label} — {rub_price} ₽{marketing_badge}{savings_text}"


def _build_tariff_payment_choice_text(*, tariff_key: str, tg_id: int) -> str:
    tariff = TARIFFS.get(tariff_key) or {}
    pricing = _tariff_pricing_for_user(tg_id, tariff_key)
    discount_chunks: list[str] = []
    if pricing["use_discount"]:
        discount_chunks.append("-20% за реферала")
    if int(pricing["pending_discount_pct"]) > 0:
        discount_chunks.append(f"-{int(pricing['pending_discount_pct'])}% по промокоду")

    discount_line = ""
    if discount_chunks:
        discount_line = "💡 Сработают скидки: " + ", ".join(discount_chunks) + ".\n\n"

    rub_price = int(pricing["base_price"])
    device_limit = 1 if tariff_key == "start_99" else PAID_LIMIT_IP
    benefits = (
        "✅ Безлимитный трафик\n"
        "✅ Без тарифного ограничения скорости¹\n"
        f"✅ До {device_limit} устройств\n"
        "✅ Все доступные платные локации\n\n"
    )
    speed_note = "_¹ Фактическая скорость зависит от сети, устройства, выбранной локации и нагрузки._"
    blocked_reasons = _bot_checkout_blocked_reasons()
    provider_names = ", ".join(
        str(row.get("label") or "").strip()
        for row in _enabled_bot_rub_providers(plan_code=tariff_key)
        if str(row.get("label") or "").strip()
    )
    provider_line = f"Оплата в ₽: *{provider_names}*\n" if provider_names else ""
    if blocked_reasons:
        return (
            f"💳 *{tariff.get('name', 'Тариф')}*\n\n"
            f"{benefits}"
            f"Срок: *{int(tariff.get('days', 0))} дней*\n"
            f"Цена в ₽: *{rub_price} ₽*\n"
            f"{discount_line}"
            "Оплата пока закрыта: "
            f"{'; '.join(blocked_reasons)}.\n\n"
            "Если доступ уже оплачен или у вас есть ключ, используйте раздел «Применить ключ» в кабинете или напишите в поддержку.\n\n"
            f"{speed_note}"
        )
    return (
        f"💎 *POKROV PREMIUM — {tariff.get('name', 'Тариф')}*\n\n"
        f"{benefits}"
        f"Срок: *{int(tariff.get('days', 0))} дней*\n"
        f"Цена в ₽: *{rub_price} ₽*\n"
        "Разовая оплата в рублях — автосписаний нет.\n\n"
        f"{discount_line}"
        f"{provider_line}"
        "В боте email не нужен: оплата привяжется к вашему Telegram.\n"
        "\n"
        "Выберите кассу и завершите оплату. "
        "Доступ обновится автоматически.\n\n"
        f"{speed_note}"
    )


def _build_tariff_payment_choice_keyboard(*, tg_id: int, tariff_key: str) -> InlineKeyboardMarkup:
    pricing = _tariff_pricing_for_user(tg_id, tariff_key)
    rows: list[list[InlineKeyboardButton]] = []
    rub_providers = _enabled_bot_rub_providers(plan_code=tariff_key)
    if rub_providers:
        for provider in rub_providers:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"💳 {provider['label']} · {int(pricing['base_price'])} ₽",
                        callback_data=f"pay_rub:{provider['code']}:{tariff_key}",
                    )
                ]
            )
    if tariff_key not in {"6_months", "9_months", "12_months"}:
        rows.append([InlineKeyboardButton(text="💎 Сэкономить на долгом тарифе", callback_data="charge_long")])
    rows.append([InlineKeyboardButton(text="◀️ К тарифам", callback_data="charge")])
    rows.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _bot_api_base_candidates() -> list[str]:
    out: list[str] = []
    for value in (
        BOT_INTERNAL_API_BASE_URL,
        PUBLIC_API_BASE_URL,
        f"https://{HOST_DOMAIN}" if HOST_DOMAIN else "",
    ):
        base = str(value or "").strip().rstrip("/")
        if base and base not in out:
            out.append(base)
    return out


async def _create_freekassa_payment_link_for_bot(*, tg_id: int, tariff_key: str) -> dict[str, object]:
    return await _create_rub_payment_link_for_bot(provider="freekassa", tg_id=tg_id, tariff_key=tariff_key)


def _enabled_bot_rub_providers(*, plan_code: str | None = None) -> list[dict[str, Any]]:
    if _bot_checkout_blocked_reasons(include_provider_check=False):
        return []
    rows: list[dict[str, Any]] = []
    for row in enabled_public_provider_catalog(plan_code=plan_code):
        if bool(row.get("supports_bot")):
            rows.append(row)
    return rows


def _bot_checkout_blocked_reasons(*, include_provider_check: bool = True) -> list[str]:
    reasons: list[str] = []
    if not RUB_CHECKOUT_ENABLED:
        reasons.append("оплата временно недоступна")
    if not PAID_CHECKOUT_LAUNCH_APPROVED:
        reasons.append("оплата временно недоступна")
    if not CHECKOUT_TICKET_SECRET:
        reasons.append("оплата временно недоступна")
    if include_provider_check and not any(bool(row.get("supports_bot")) for row in enabled_public_provider_catalog()):
        reasons.append("оплата временно недоступна")
    return list(dict.fromkeys(reasons))


def _rub_provider_by_code(provider_code: str, *, plan_code: str | None = None) -> dict[str, Any] | None:
    code = normalize_payment_provider(provider_code)
    if not code:
        return None
    for row in _enabled_bot_rub_providers(plan_code=plan_code):
        if str(row.get("code") or "") == code:
            return row
    return None


def _parse_pay_rub_callback(data: str) -> tuple[str, str]:
    raw = str(data or "").strip()
    if raw.startswith("pay_rub:"):
        _, provider_code, tariff_key = (raw.split(":", 2) + ["", ""])[:3]
        return normalize_payment_provider(provider_code), normalize_tariff_key(tariff_key)
    if raw.startswith("pay_rub_"):
        tariff_key = normalize_tariff_key(raw.replace("pay_rub_", "", 1))
        first_provider = _enabled_bot_rub_providers()[:1]
        provider_code = str(first_provider[0].get("code") or "") if first_provider else ""
        return normalize_payment_provider(provider_code), tariff_key
    return "", ""


def _bot_rub_order_payload(*, provider: str, tg_id: int, tariff_key: str) -> tuple[dict[str, object], str]:
    ctx = checkout_context_by_user.get(int(tg_id), {}) if checkout_context_by_user else {}
    promo_code = str(ctx.get("promo_code") or "")
    campaign_key = str(ctx.get("campaign_key") or "")
    checkout_ticket = _checkout_ticket_for_user(
        tg_id=int(tg_id),
        plan_code=tariff_key,
        promo_code=promo_code,
        campaign_key=campaign_key,
        source="bot",
    )
    if not checkout_ticket:
        raise RuntimeError("Не удалось подготовить персональную ссылку оплаты.")

    payload = {
        "provider": normalize_payment_provider(provider) or "freekassa",
        "plan_code": str(tariff_key or "").strip().lower(),
        "checkout_ticket": checkout_ticket,
        "currency": "RUB",
    }
    return payload, checkout_ticket


async def _create_rub_payment_link_for_bot(*, provider: str, tg_id: int, tariff_key: str) -> dict[str, object]:
    payload, checkout_ticket = _bot_rub_order_payload(provider=provider, tg_id=tg_id, tariff_key=tariff_key)
    timeout = aiohttp.ClientTimeout(total=25)
    last_error = "Не удалось открыть оплату."
    for base in _bot_api_base_candidates():
        url = f"{base}/api/payments/orders/create-public"
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as resp:
                    raw_text = await resp.text()
                    if resp.status >= 400:
                        last_error = raw_text or f"HTTP {resp.status}"
                        continue
                    try:
                        data = json.loads(raw_text)
                    except Exception:
                        last_error = raw_text or "Платёжный сервис вернул неожиданный ответ."
                        continue
                    payment_url = str(data.get("payment_url") or "").strip()
                    if payment_url:
                        data["checkout_ticket"] = checkout_ticket
                        return data
                    last_error = "Платёжная ссылка не получена."
        except Exception as exc:
            last_error = str(exc or last_error)
    raise RuntimeError(last_error)


def _build_direct_rub_payment_keyboard(*, tg_id: int, tariff_key: str, payment_url: str, provider_label: str = "кассу") -> InlineKeyboardMarkup:
    pricing = _tariff_pricing_for_user(tg_id, tariff_key)
    ctx = checkout_context_by_user.get(int(tg_id), {}) if checkout_context_by_user else {}
    checkout_url = _bot_checkout_url(
        tg_id=int(tg_id),
        plan_code=tariff_key,
        promo_code=str(ctx.get("promo_code") or ""),
        campaign_key=str(ctx.get("campaign_key") or ""),
    )
    rows = [
        [InlineKeyboardButton(text=f"💳 Открыть оплату · {provider_label} · {int(pricing['base_price'])} ₽", url=str(payment_url or "").strip())],
        [InlineKeyboardButton(text="🌐 Открыть через сайт, если окно не открылось", url=checkout_url)],
        [InlineKeyboardButton(text="◀️ К тарифам", callback_data="charge")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _dual_pay_text(*, show_trial: bool) -> str:
    blocked_reasons = _bot_checkout_blocked_reasons()
    provider_names = ", ".join(
        str(row.get("label") or "").strip()
        for row in _enabled_bot_rub_providers()
        if str(row.get("label") or "").strip()
    )
    rub_hint = (
        f"В рублях доступны: {provider_names}."
        if provider_names
        else f"Оплата пока закрыта: {'; '.join(blocked_reasons) or 'оплата временно недоступна'}."
    )
    if show_trial:
        return (
            "🔥 *POKROV VPN — привычные сервисы снова доступны*\n\n"
            "✅ Безлимитный трафик на платных тарифах\n"
            "✅ Без тарифного ограничения скорости¹\n"
            "✅ Android + Windows\n"
            f"✅ До {PAID_LIMIT_IP} устройств\n\n"
            "🎁 5 дней бесплатно без карты.\n"
            "После теста — от 99 ₽, без автосписаний.\n"
            f"{rub_hint}\n"
            "После оплаты доступ обновится автоматически.\n\n"
            "_¹ Фактическая скорость зависит от сети, устройства, локации и нагрузки._"
        )
    return (
        "💎 *Продлите POKROV PREMIUM*\n\n"
        "✅ Безлимитный трафик\n"
        "✅ Без тарифного ограничения скорости¹\n"
        f"✅ До {PAID_LIMIT_IP} устройств\n\n"
        f"{rub_hint}\n"
        "После оплаты доступ обновится автоматически. Автосписаний нет.\n\n"
        "Выберите способ оплаты:\n\n"
        "_¹ Фактическая скорость зависит от сети, устройства, локации и нагрузки._"
    )


def _dual_pay_keyboard(*, tg_id: int, show_trial: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if show_trial:
        rows.append([InlineKeyboardButton(text="🔥 Попробовать VPN бесплатно", callback_data="buy_trial")])
    rows.extend(
        [
            [InlineKeyboardButton(text="💳 Купить VPN от 99 ₽", callback_data="charge")],
        ]
    )
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _has_paid_active_access(user: User | None) -> bool:
    if not user:
        return False
    expiry = _naive_utc(user.expiry_at)
    return bool(
        user.is_active
        and expiry
        and expiry > _utcnow()
        and not _is_freemium_sub_type(user.sub_type)
    )


def _trial_offer_available(user: User | None) -> bool:
    return bool(not _has_paid_active_access(user) and not bool(user and user.trial_used))


def _main_menu_cta_spec(tg_id: int) -> dict[str, str]:
    user = get_user(int(tg_id)) if int(tg_id or 0) > 0 else None
    expiry = _naive_utc(getattr(user, "expiry_at", None))
    if bool(user and user.is_active and expiry and expiry > _utcnow()):
        return _btn_spec(
            text="Подключить устройство",
            callback_data="instruction",
            style=BTN_STYLE_PRIMARY,
            emoji_key="device",
        )
    if _trial_offer_available(user):
        return _btn_spec(
            text="Попробовать 5 дней бесплатно",
            callback_data="instruction",
            style=BTN_STYLE_PRIMARY,
            emoji_key="free",
        )
    if not _bot_checkout_blocked_reasons():
        return _btn_spec(
            text="Продлить доступ",
            callback_data="charge",
            style=BTN_STYLE_SUCCESS,
            emoji_key="payment",
        )
    return _btn_spec(
        text="Активировать код",
        callback_data="gift_redeem_prompt",
        style=BTN_STYLE_PRIMARY,
        emoji_key="key",
    )


def main_keyboard_specs(tg_id: int = 0) -> list[list[dict[str, str]]]:
    rows = [
        [_main_menu_cta_spec(tg_id)],
        [
            _btn_spec(text="Мой доступ", callback_data="status", emoji_key="success"),
            _btn_spec(text="Помощь", callback_data="confused_help", emoji_key="support"),
        ],
        [_btn_spec(text="Ещё", callback_data="settings", emoji_key="settings")],
    ]
    if tg_id == ADMIN_ID:
        rows.append([_btn_spec(text="Админ-панель", callback_data="admin", emoji_key="brand")])
    return rows


def main_keyboard(tg_id: int = 0) -> InlineKeyboardMarkup:
    """Main menu aligned to the single primary user path."""
    return _keyboard_from_specs(main_keyboard_specs(tg_id))


def new_user_keyboard_specs() -> list[list[dict[str, str]]]:
    """Cold-start surface: choose a platform before account controls."""
    return [
        [
            _btn_spec(
                text="Android",
                callback_data="instr_android",
                style=BTN_STYLE_PRIMARY,
                emoji_key="phone",
            ),
            _btn_spec(
                text="Windows",
                callback_data="instr_win",
                emoji_key="device",
            ),
        ],
        [_btn_spec(text="Тарифы", callback_data="charge", emoji_key="payment")],
        [
            _btn_spec(
                text="Как проверить POKROV",
                callback_data="verify_pokrov",
                emoji_key="success",
            )
        ],
    ]


def tariff_keyboard_specs(
    tg_id: int = 0,
    show_trial: bool = True,
    show_gb_only: bool = False,
    include_long_plans: bool = False,
) -> list[list[dict[str, str]]]:
    del show_gb_only
    rows: list[list[dict[str, str]]] = []

    if show_trial:
        rows.append(
            [
                _btn_spec(
                    text="Попробовать 5 дней бесплатно",
                    callback_data="instruction",
                    style=BTN_STYLE_SUCCESS,
                    emoji_key="free",
                )
            ]
        )

    if include_long_plans:
        plans = [
            ("6_months", "target", "6 месяцев"),
            ("9_months", "world", "9 месяцев"),
            ("12_months", "crown", "12 месяцев"),
        ]
    else:
        plans = [
            ("start_99", "lightning", "30 дней"),
            ("1_month", "rocket", "1 месяц"),
            ("3_months", "diamond", "3 месяца"),
        ]

    for key, emoji_key, period in plans:
        tariff = TARIFFS.get(key)
        if not tariff:
            continue
        pricing = _tariff_pricing_for_user(tg_id, key)
        btn_text = f"{period} — {int(pricing['base_price'])} ₽"
        savings = _tariff_savings_pct(key)
        if savings:
            btn_text += f" · −{savings}%"
        rows.append(
            [
                _btn_spec(
                    text=btn_text,
                    callback_data=f"buy_{key}",
                    style=BTN_STYLE_PRIMARY if key in {"3_months", "12_months"} else None,
                    emoji_key=emoji_key,
                )
            ]
        )

    if include_long_plans:
        rows.append([_btn_spec(text="◀️ К основным тарифам", callback_data="charge")])
    else:
        rows.append(
            [
                _btn_spec(
                    text="Сэкономить на долгом тарифе",
                    callback_data="charge_long",
                    emoji_key="crown",
                )
            ]
        )

    rows.append([_btn_spec(text="◀️ Назад", callback_data="back")])
    return rows


def tariff_keyboard(
    tg_id: int = 0,
    show_trial: bool = True,
    show_gb_only: bool = False,
    include_long_plans: bool = False,
) -> InlineKeyboardMarkup:
    return _keyboard_from_specs(
        tariff_keyboard_specs(
            tg_id=tg_id,
            show_trial=show_trial,
            show_gb_only=show_gb_only,
            include_long_plans=include_long_plans,
        )
    )
# Telegram handlers live in ordered domain slices. The loader preserves the
# legacy bot.<name> surface and deterministic aiogram registration.
try:
    from .module_slices import load_slices as _load_domain_slices
except ImportError:
    from module_slices import load_slices as _load_domain_slices

_slice_prefix = f"{__package__}." if __package__ else ""
_BOT_SLICE_MODULES = _load_domain_slices(
    globals(),
    (
        f"{_slice_prefix}bot_user_handlers",
        f"{_slice_prefix}bot_admin_handlers",
        f"{_slice_prefix}bot_payment_handlers",
        f"{_slice_prefix}bot_operator_handlers",
    ),
)
if __name__ == "__main__":
    asyncio.run(main())

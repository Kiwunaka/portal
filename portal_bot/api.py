# -*- coding: utf-8 -*-
"""
POKROV API for app-first sessions, cabinet continuation, Telegram, and connection delivery.

- `/api/user/{tg_id}`: authenticated by Telegram WebApp initData
- `/api/reviews`: featured reviews for WebApp
- `/s8Kx2mP7qR4wT/{token}`: subscription endpoint (multi-node)
"""

from __future__ import annotations

import base64
import contextvars
import hashlib
import hmac
import inspect
import ipaddress
import json
import logging
import mimetypes
import os
import re
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse

import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, case, func
from sqlalchemy.exc import IntegrityError

# Load env from repo-local file first to avoid cwd-dependent startup behavior.
load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
load_dotenv()

from config import Settings, env_bool, env_int
from db import SessionLocal, init_db
from models import (
    AdminAudit,
    AppSetting,
    CampaignSend,
    Event,
    ExternalOrder,
    ExternalPaymentEvent,
    FamilySlot,
    FeedbackEntry,
    GiftCard,
    IncentiveCampaign,
    KeyActionHistory,
    LiveUpdate,
    Node,
    NodeHealthSample,
    ObserverUserState,
    PlanCatalog,
    PromoCode,
    PromoUsage,
    PayAttempt,
    ReferralBonusQueue,
    Review,
    RewardClaim,
    StartLink,
    SupportTicket,
    Template,
    User,
    UserKeyPolicy,
    UserNode,
    WebEmailIdentity,
    WebEmailToken,
)
from payment_providers import (
    PROVIDER_META,
    callback_ids as payment_callback_ids,
    callback_status as payment_callback_status,
    create_rub_payment,
    enabled_provider_catalog,
    enabled_rub_provider_codes,
    normalize_provider as _normalize_checkout_provider,
    provider_is_configured,
    verify_callback_signature as verify_provider_callback_signature,
)
from tickets_repo import (
    STATUS_CLOSED,
    STATUS_IN_PROGRESS,
    STATUS_OPEN,
    add_ticket_message,
    create_ticket,
    get_ticket_by_id,
    get_user_active_ticket,
    list_active_tickets,
    list_ticket_messages,
    list_user_tickets,
    set_ticket_status,
)
from nodes_repo import enabled_nodes
from node_policy import (
    SMART_CONNECT_SHORTLIST_LIMIT,
    SMART_CONNECT_STALE_AFTER_SECONDS,
    SMART_CONNECT_STICKINESS_THRESHOLD_PERCENT,
    canonical_free_node_code,
    node_backend_penalty,
    node_cpu_penalty,
    node_is_free,
    node_is_stale,
    user_uses_free_pool,
)
from control_panel import ControlPanel
from events_service import track_event
from offers_service import accept_offer, create_offer, get_active_offer
from pay_attempts_service import start_attempt
from points_service import (
    EXPIRY_DAYS as POINTS_EXPIRY_DAYS,
    MONTHLY_CAP as POINTS_MONTHLY_CAP,
    award_points,
    award_referral_points,
    available_points,
    preview_redeemable_points,
    referral_tier_snapshot,
)
from free_cycle_service import ensure_user_free_cycle_state, mark_user_became_free
from email_auth_service import (
    DuplicateEmailIdentityError,
    InvalidEmailCredentialsError,
    InvalidEmailInputError,
    InvalidEmailTokenError,
    authenticate_email_identity,
    build_debug_payload as build_email_auth_debug_payload,
    deliver_auth_message,
    get_verified_identity_for_user,
    register_email_identity,
    start_password_reset,
    verify_email_identity,
    finish_password_reset,
)
import app_first_service
import channel_bonus_service
from gift_cards_service import redeem_gift_card as redeem_gift_card_service
from observer_service import (
    OBSERVER_PUSH_MAX_AGE_SECONDS,
    build_admin_observer_block,
    get_observer_state_map,
    ingest_observer_batch,
    observer_stale_after_seconds,
)
from network_rollout import (
    NETWORK_ROLLOUT_CONFIG_KEY,
    load_network_rollout_config,
    normalized_network_rollout_config,
    resolved_client_policy,
    transport_node_allowlist,
)
from public_urls import build_subscription_url, public_connect_host
from shared_surface_facts import (
    get_access_matrix,
    get_product_facts,
    get_promo_slots,
    get_public_urls,
    get_tariff_catalog,
)
from transport_catalog import LEGACY_REALITY_FALLBACK, OPERATOR_LAB, RESERVE_XHTTP_CDN, node_transport_profiles, transport_profile_by_name
from web_auth_service import (
    SESSION_TTL_SECONDS,
    build_telegram_oidc_authorize_url,
    create_web_session_token,
    exchange_telegram_oidc_code,
    verify_telegram_login_payload,
    verify_telegram_oidc_state_token,
    verify_web_session_token,
)


init_db()
logger = logging.getLogger(__name__)
_current_request_ctx: contextvars.ContextVar[Request | None] = contextvars.ContextVar(
    "portal_current_request",
    default=None,
)


def _utcnow() -> datetime:
    """
    Return naive UTC datetime backed by timezone-aware source.
    This avoids deprecated _utcnow() usage while keeping DB compatibility.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return float(default)


def _current_bot_token() -> str:
    return str(os.getenv("BOT_TOKEN") or Settings.BOT_TOKEN or "").strip()


_PRODUCT_FACTS = get_product_facts()
_ACCESS_MATRIX = get_access_matrix()
_PROMO_SLOTS = get_promo_slots()
_PUBLIC_URL_FACTS = get_public_urls()
_TARIFF_CATALOG = get_tariff_catalog()
_PUBLIC_URL_TELEGRAM = _PUBLIC_URL_FACTS.get("telegram", {})
_ACCESS_PUBLIC_DEFAULTS = _ACCESS_MATRIX.get("public_defaults", {})
_ACCESS_ENTRY_FLOWS = _ACCESS_MATRIX.get("entry_flows", {})
_FREE_TIER_FACTS = _ACCESS_MATRIX.get("free_tier", {})
_TRIAL_FACTS = _ACCESS_ENTRY_FLOWS.get("store_install", {})
_TELEGRAM_REWARD_FACTS = _ACCESS_ENTRY_FLOWS.get("telegram", {})
_TARIFF_PLANS = list(_TARIFF_CATALOG.get("plans") or [])
_TARIFF_PLAN_MAP = {
    str(plan.get("code") or "").strip().lower(): plan
    for plan in _TARIFF_PLANS
    if str(plan.get("code") or "").strip()
}
PROMO_SLOTS_CONFIG_KEY = "promo_slots_config_v1"
LEGACY_GIFT_PLAN_HINTS = {
    "mini": "start_99",
    "standard": "1_month",
    "premium": "3_months",
}


def _shared_telegram_username(key: str, fallback: str) -> str:
    value = str(_PUBLIC_URL_TELEGRAM.get(key) or fallback).strip()
    return value.lstrip("@")


API_ENABLE_USAGE = env_bool("API_ENABLE_USAGE", default=False)
AUTO_DOWNGRADE_TO_FREE = env_bool("AUTO_DOWNGRADE_TO_FREE", default=True)
AUTO_FREE_DAYS = int(os.getenv("AUTO_FREE_DAYS", "3650"))
FREE_TOTAL_GB = env_int("FREE_TOTAL_GB", int(_FREE_TIER_FACTS.get("traffic_limit_gb", 5) or 5))
FREE_LIMIT_IP = env_int("FREE_LIMIT_IP", int(_FREE_TIER_FACTS.get("device_limit", 1) or 1))
PAID_LIMIT_IP = env_int("PAID_LIMIT_IP", 5)
FREE_SPEED_LIMIT_KBPS = env_int(
    "FREE_SPEED_LIMIT_KBPS",
    int(round(float(_FREE_TIER_FACTS.get("speed_limit_mbps", 50) or 50) * 125)),
)
FREE_SOFT_MODE_SPEED_LIMIT_KBPS = env_int(
    "FREE_SOFT_MODE_SPEED_LIMIT_KBPS",
    int(round(float(_FREE_TIER_FACTS.get("soft_mode_speed_limit_mbps", 2) or 2) * 125)),
)
SUPPORT_USERNAME = (
    os.getenv("SUPPORT_USERNAME") or _shared_telegram_username("support_bot_username", "@pokrov_supportbot")
).lstrip("@")
SUPPORT_USERNAME = (os.getenv("SUPPORT_BOT_USERNAME") or SUPPORT_USERNAME).lstrip("@")
PUBLIC_CHANNEL = (os.getenv("PUBLIC_CHANNEL") or _shared_telegram_username("channel_username", "@pokrov_vpn")).lstrip("@")
BOT_USERNAME = (os.getenv("BOT_USERNAME") or _shared_telegram_username("bot_username", "@pokrov_vpnbot")).lstrip("@")
REFERRAL_BONUS_DAYS = env_int("REFERRAL_BONUS_DAYS", 15)
REFERRAL_ANTIFRAUD_HOURS = max(0, env_int("REFERRAL_ANTIFRAUD_HOURS", 24))
REFERRAL_ANTIFRAUD_MAX_WAIT_HOURS = max(1, env_int("REFERRAL_ANTIFRAUD_MAX_WAIT_HOURS", 168))
CHANNEL_PREMIUM_DAYS = max(1, env_int("CHANNEL_PREMIUM_DAYS", int(_TELEGRAM_REWARD_FACTS.get("bonus_days", 10) or 10)))
APP_TRIAL_DEFAULT_DAYS = max(1, env_int("APP_TRIAL_DEFAULT_DAYS", int(_TRIAL_FACTS.get("trial_days", 5) or 5)))
APP_TRIAL_MAX_DAYS = APP_TRIAL_DEFAULT_DAYS
APP_ACCOUNT_TG_ID_BASE = max(9_000_000_000_000, env_int("APP_ACCOUNT_TG_ID_BASE", 9_000_000_000_000))
OPENING_PREMIUM_DAYS = max(1, env_int("OPENING_PREMIUM_DAYS", 14))
OPENING_PREMIUM_CAMPAIGN_KEY = (
    os.getenv("OPENING_PREMIUM_CAMPAIGN_KEY") or f"opening_premium_{OPENING_PREMIUM_DAYS}d"
).strip()[:64]
CHANNEL_SUBSCRIBER_CAMPAIGN_KEY = (
    os.getenv("CHANNEL_SUBSCRIBER_CAMPAIGN_KEY")
    or getattr(Settings, "CHANNEL_SUBSCRIBER_CAMPAIGN_KEY", "")
    or "channel_subscriber_v1"
).strip()[:64]
MAX_BROADCAST_LIMIT = env_int("MAX_BROADCAST_LIMIT", 1000)
PAY_CHECKOUT_URL = (os.getenv("PAY_CHECKOUT_URL") or "").strip()
RUB_CHECKOUT_ENABLED = env_bool("RUB_CHECKOUT_ENABLED", default=False)
CHECKOUT_WIDGET_ENABLED = env_bool("CHECKOUT_WIDGET_ENABLED", default=False)
CHANNEL_SPEED_BUMP_ENABLED = env_bool("CHANNEL_SPEED_BUMP_ENABLED", default=False)
FREE_SPEED_BUMP_UNSUB_KBPS = max(1, env_int("FREE_SPEED_BUMP_UNSUB_KBPS", 1250))
CHECKOUT_TICKET_SECRET = (
    (os.getenv("CHECKOUT_TICKET_SECRET") or "").strip()
    or (os.getenv("WEBAPP_SESSION_SECRET") or "").strip()
)
CHECKOUT_TICKET_TTL_SECONDS = max(60, env_int("CHECKOUT_TICKET_TTL_SECONDS", 900))
WEBAPP_ENABLE_HAPTIC = env_bool("WEBAPP_ENABLE_HAPTIC", default=True)
WEBAPP_ENABLE_LOTTIE = env_bool("WEBAPP_ENABLE_LOTTIE", default=True)
WEBAPP_DEV_AUTH = env_bool("WEBAPP_DEV_AUTH", default=False)
WEBAPP_DEV_TG_ID = env_int("WEBAPP_DEV_TG_ID", 0)
WEBAPP_DEV_AUTH_PASSWORD = (os.getenv("WEBAPP_DEV_AUTH_PASSWORD") or "").strip()
PROFILE_UPDATE_INTERVAL_HOURS = max(1, env_int("PROFILE_UPDATE_INTERVAL_HOURS", 6))
PAYMENT_CALLBACK_TOLERANT_MODE = env_bool("PAYMENT_CALLBACK_TOLERANT_MODE", default=False)
SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED = env_bool("SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED", default=True)
TELEGRAM_WEB_LOGIN_MAX_AGE_SECONDS = max(60, env_int("TELEGRAM_WEB_LOGIN_MAX_AGE_SECONDS", 86400))
NODE_METRICS_CPU_ALERT_PERCENT = _env_float("NODE_METRICS_CPU_ALERT_PERCENT", 70.0)
NODE_METRICS_MEMORY_ALERT_PERCENT = _env_float("NODE_METRICS_MEMORY_ALERT_PERCENT", 85.0)
NODE_METRICS_DISK_ALERT_PERCENT = _env_float("NODE_METRICS_DISK_ALERT_PERCENT", 90.0)
NODE_METRICS_NETWORK_ALERT_PERCENT = _env_float("NODE_METRICS_NETWORK_ALERT_PERCENT", 70.0)
NODE_METRICS_PORT_CAPACITY_MBPS = _env_float("NODE_METRICS_PORT_CAPACITY_MBPS", 1000.0)
NODE_METRICS_LATENCY_ALERT_MS = _env_float("NODE_METRICS_LATENCY_ALERT_MS", 800.0)
NODE_METRICS_ERROR_RATE_ALERT = _env_float("NODE_METRICS_ERROR_RATE_ALERT", 0.2)
NODE_METRICS_ACTIVE_CLIENTS_ALERT = max(1, env_int("NODE_METRICS_ACTIVE_CLIENTS_ALERT", 200))
NODE_METRICS_SUSTAINED_SAMPLES = max(2, env_int("NODE_METRICS_SUSTAINED_SAMPLES", 3))
SUPPORT_UPLOAD_DIR = Path(
    os.getenv("SUPPORT_UPLOAD_DIR") or (Path(__file__).resolve().parent / "uploads" / "support")
).resolve()
SUPPORT_UPLOAD_URL_PREFIX = f"/{(os.getenv('SUPPORT_UPLOAD_URL_PREFIX') or 'uploads/support').strip().strip('/')}"
SUPPORT_UPLOAD_MAX_BYTES = max(1, env_int("SUPPORT_UPLOAD_MAX_BYTES", 20 * 1024 * 1024))
API_LOCALHOST_DEV_HOSTS = {"localhost", "127.0.0.1", "::1"}
WEBAPP_DEV_ALLOWED_ORIGINS = {
    x.strip().lower().rstrip("/")
    for x in (
        os.getenv(
            "WEBAPP_DEV_ALLOWED_ORIGINS",
            "http://localhost,http://127.0.0.1,http://localhost:3000,http://127.0.0.1:3000,https://localhost,https://127.0.0.1",
        ) or ""
    ).split(",")
    if x.strip()
}
API_PLAN_PRICES = {
    "trial": 0,
    **{
        code: int(plan.get("amount_stars") or 0)
        for code, plan in _TARIFF_PLAN_MAP.items()
    },
}
RUB_PLAN_PRICES = {
    code: {
        "amount_rub": int(plan.get("amount_rub") or 0),
        "days": int(plan.get("duration_days") or 30),
    }
    for code, plan in _TARIFF_PLAN_MAP.items()
}
RUB_PLAN_LABELS = {
    code: str(plan.get("label") or code)
    for code, plan in _TARIFF_PLAN_MAP.items()
}
GIFT_CARD_TYPES = {
    "mini": {"days": 7, "stars": 59, "name": "Mini"},
    "standard": {"days": 30, "stars": 249, "name": "Standard"},
    "premium": {"days": 90, "stars": 699, "name": "Premium"},
}
PAYMENT_PROVIDER_WHITELIST = {"cardlink", "freekassa", "pally", "platima"}
FK_NOTIFY_IP_ALLOWLIST = [
    x.strip()
    for x in (os.getenv("FK_NOTIFY_IP_ALLOWLIST") or "").split(",")
    if x.strip()
]
DEFAULT_LOYALTY_CONFIG: dict[str, Any] = {
    "tiers": [
        {"days": 30, "bonus_days": 2, "perk": "priority_support"},
        {"days": 90, "bonus_days": 7, "perk": "smart_route"},
        {"days": 180, "bonus_days": 14, "perk": "pro_pack"},
    ],
    "enabled": True,
}


def _default_plan_catalog() -> list[dict[str, Any]]:
    return [
        {
            "code": code,
            "label": str(plan.get("label") or code),
            "amount_rub": int(plan.get("amount_rub") or 0),
            "amount_stars": int(plan.get("amount_stars") or 0),
            "days": int(plan.get("duration_days") or 30),
            "device_limit": max(1, int(plan.get("device_limit") or 1)),
            "node_policy": str(plan.get("node_policy") or "").strip() or None,
            "badge": str(plan.get("badge") or "").strip() or None,
            "is_active": True,
            "sort_order": idx + 1,
        }
        for idx, (code, plan) in enumerate(_TARIFF_PLAN_MAP.items())
    ]


def _default_live_updates() -> list[dict[str, Any]]:
    channel = (PUBLIC_CHANNEL or "pokrov_vpn").lstrip("@")
    return [
        {
            "id": 0,
            "title": "Новые точки подключения NL/PL",
            "summary": "Обновили маршруты и короткие рекомендации по старту для актуальных клиентов.",
            "date": "2026-02-14",
            "link": f"https://t.me/{channel}/1",
        },
        {
            "id": 0,
            "title": "Обновлён кабинет POKROV",
            "summary": "Сделали поддержку, загрузки и оплату понятнее, без лишнего шума.",
            "date": "2026-02-13",
            "link": f"https://t.me/{channel}/2",
        },
        {
            "id": 0,
            "title": "Короткий путь к запуску",
            "summary": "Проверили быстрый сценарий через Telegram и обновили стартовые ссылки для новых пользователей.",
            "date": "2026-02-12",
            "link": f"https://t.me/{channel}/3",
        },
    ]


DEFAULT_WHEEL_CONFIG: dict[str, Any] = {
    "preset": "balanced",
    "weights": [
        {"days": 1, "weight": 45},
        {"days": 3, "weight": 35},
        {"days": 7, "weight": 15},
        {"days": 30, "weight": 5},
    ],
    "cooldown_hours": 168,
}


def _normalize_channel_username(raw: str | None) -> str | None:
    val = str(raw or "").strip().lstrip("@")
    if not val:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_]{4,64}", val):
        raise HTTPException(status_code=400, detail="Invalid channel_username")
    return val


def _build_tg_post_link(*, channel_username: str | None, post_id: int | None, fallback_link: str | None = None) -> str:
    channel = _normalize_channel_username(channel_username) if channel_username else None
    pid = int(post_id or 0)
    if channel and pid > 0:
        return f"https://t.me/{channel}/{pid}"
    return str(fallback_link or "").strip()


_DEEPLINK_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _sanitize_deeplink_token(value: str | None, *, max_len: int, uppercase: bool = False) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    clean = re.sub(r"[^A-Za-z0-9_-]+", "", raw)[: max(1, int(max_len))]
    if not clean:
        return ""
    clean = clean.upper() if uppercase else clean
    if not _DEEPLINK_TOKEN_RE.fullmatch(clean):
        return ""
    return clean


def _safe_json_loads(raw: str | None, default: Any) -> Any:
    text_val = str(raw or "").strip()
    if not text_val:
        return default
    try:
        return json.loads(text_val)
    except Exception:
        return default


def _get_app_setting_json(*, s, key: str, default: Any) -> Any:
    row = s.query(AppSetting).filter(AppSetting.key == str(key)).first()
    if not row:
        return default
    return _safe_json_loads(getattr(row, "value_json", None), default)


def _set_app_setting_json(*, s, key: str, value: Any) -> None:
    now = _utcnow()
    row = s.query(AppSetting).filter(AppSetting.key == str(key)).first()
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    if not row:
        row = AppSetting(key=str(key), value_json=encoded, updated_at=now)
        s.add(row)
    else:
        row.value_json = encoded
        row.updated_at = now


def _request_carrier_header(value: str | None) -> str:
    return re.sub(r"[^a-z0-9._:-]+", "-", str(value or "").strip().lower()).strip("-")[:64]


def _validate_wheel_weights(weights: list[dict[str, Any]]) -> list[dict[str, int]]:
    out: list[dict[str, int]] = []
    seen_days: set[int] = set()
    total = 0
    for row in weights:
        days = int(row.get("days") or 0)
        weight = int(row.get("weight") or 0)
        if days <= 0 or days > 365:
            raise HTTPException(status_code=400, detail="Wheel weight days must be in 1..365")
        if weight <= 0 or weight > 10000:
            raise HTTPException(status_code=400, detail="Wheel weight must be in 1..10000")
        if days in seen_days:
            raise HTTPException(status_code=400, detail="Wheel days must be unique")
        seen_days.add(days)
        total += weight
        out.append({"days": days, "weight": weight})
    if total <= 0:
        raise HTTPException(status_code=400, detail="Wheel weights sum must be > 0")
    return out


def _normalized_wheel_config(payload: dict[str, Any] | None) -> dict[str, Any]:
    src = dict(payload or {})
    preset = str(src.get("preset") or DEFAULT_WHEEL_CONFIG["preset"]).strip()[:32] or "balanced"
    cooldown_hours = int(src.get("cooldown_hours") or DEFAULT_WHEEL_CONFIG["cooldown_hours"])
    cooldown_hours = max(1, min(24 * 90, cooldown_hours))
    weights_raw = src.get("weights")
    if not isinstance(weights_raw, list) or not weights_raw:
        weights_raw = list(DEFAULT_WHEEL_CONFIG["weights"])
    weights = _validate_wheel_weights([dict(x or {}) for x in weights_raw])
    return {"preset": preset, "weights": weights, "cooldown_hours": cooldown_hours}

def _fk_shop_configs() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    pairs = {
        "site": {
            "shop_id": (os.getenv("FK_SITE_SHOP_ID") or "").strip(),
            "api_key": (os.getenv("FK_SITE_API_KEY") or "").strip(),
            "secret_word_1": (os.getenv("FK_SITE_SECRET_WORD_1") or "").strip(),
            "secret_word_2": (os.getenv("FK_SITE_SECRET_WORD_2") or "").strip(),
        },
        "bot": {
            "shop_id": (os.getenv("FK_BOT_SHOP_ID") or "").strip(),
            "api_key": (os.getenv("FK_BOT_API_KEY") or "").strip(),
            "secret_word_1": (os.getenv("FK_BOT_SECRET_WORD_1") or "").strip(),
            "secret_word_2": (os.getenv("FK_BOT_SECRET_WORD_2") or "").strip(),
        },
    }
    for key, cfg in pairs.items():
        if cfg["shop_id"]:
            out[key] = cfg
    return out


def _fk_shop_by_source(source: str) -> dict[str, str]:
    shops = _fk_shop_configs()
    src = (source or "site").strip().lower()
    if src in shops:
        return shops[src]
    if "site" in shops:
        return shops["site"]
    if "bot" in shops:
        return shops["bot"]
    return {}


def _fk_shop_by_merchant_id(merchant_id: str) -> dict[str, str]:
    mid = str(merchant_id or "").strip()
    if not mid:
        return {}
    for cfg in _fk_shop_configs().values():
        if str(cfg.get("shop_id") or "").strip() == mid:
            return cfg
    return {}


def _fk_flatten_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        parts: list[str] = []
        for k in sorted(value.keys(), key=lambda x: str(x)):
            parts.extend(_fk_flatten_values(value.get(k)))
        return parts
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_fk_flatten_values(item))
        return out
    if isinstance(value, bool):
        return ["1" if value else "0"]
    if value is None:
        return [""]
    return [str(value)]


def _fk_api_signature(*, api_key: str, payload: dict[str, Any]) -> str:
    top = {str(k): v for k, v in dict(payload or {}).items() if str(k) != "signature"}
    values = _fk_flatten_values({k: top[k] for k in sorted(top)})
    base = "|".join(values)
    return hmac.new(api_key.encode("utf-8"), base.encode("utf-8"), hashlib.sha256).hexdigest()


def _fk_sci_signature(*, merchant_id: str, amount: str, order_id: str, secret_word_2: str) -> str:
    base = f"{merchant_id}:{amount}:{secret_word_2}:{order_id}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()


def _fk_sci_payment_signature(*, merchant_id: str, amount: str, order_id: str, secret_word_1: str, currency: str) -> str:
    base = f"{merchant_id}:{amount}:{secret_word_1}:{currency}:{order_id}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()


def _format_freekassa_amount(amount: float | int) -> str:
    return f"{float(amount or 0):.2f}"


def _freekassa_payment_base_url() -> str:
    host = str(os.getenv("FREEKASSA_PAY_HOST") or "pay.fk.money").strip().strip("/")
    if host.startswith("http://") or host.startswith("https://"):
        return host
    return f"https://{host}"


def _build_freekassa_payment_url(
    *,
    source: str,
    order_id: str,
    amount_rub: float | int,
    currency: str,
    tg_id: int,
    plan_code: str,
    campaign: str,
    promo_code: str,
) -> str:
    shop = _fk_shop_by_source(source)
    merchant_id = str(shop.get("shop_id") or "").strip()
    secret_word_1 = str(shop.get("secret_word_1") or "").strip()
    if not merchant_id or not secret_word_1:
        raise HTTPException(status_code=500, detail=f"Freekassa shop is not configured for source={source}")
    amount_str = _format_freekassa_amount(amount_rub)
    currency_code = str(currency or "RUB").strip().upper() or "RUB"
    signature = _fk_sci_payment_signature(
        merchant_id=merchant_id,
        amount=amount_str,
        order_id=str(order_id),
        secret_word_1=secret_word_1,
        currency=currency_code,
    )
    params: dict[str, str] = {
        "m": merchant_id,
        "oa": amount_str,
        "o": str(order_id),
        "currency": currency_code,
        "s": signature,
        "lang": "ru",
        "us_tg_id": str(int(tg_id)),
        "us_plan_code": str(plan_code or "").strip().lower()[:32],
        "us_source": str(source or "site").strip().lower()[:16],
    }
    if campaign:
        params["us_campaign"] = _sanitize_deeplink_token(campaign, max_len=64, uppercase=False)
    if promo_code:
        params["us_promo_code"] = _sanitize_deeplink_token(promo_code, max_len=20, uppercase=True)
    return f"{_freekassa_payment_base_url()}/?{urlencode(params)}"


def _fk_client_ip(request: Request) -> str:
    forwarded = (request.headers.get("x-forwarded-for") or "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    return str(getattr(getattr(request, "client", None), "host", "") or "")


def _is_ip_allowed(ip: str, allowlist: list[str]) -> bool:
    if not allowlist:
        return True
    try:
        ip_obj = ipaddress.ip_address(ip)
    except Exception:
        return False
    for raw in allowlist:
        token = str(raw or "").strip()
        if not token:
            continue
        try:
            if "/" in token:
                if ip_obj in ipaddress.ip_network(token, strict=False):
                    return True
            else:
                if ip_obj == ipaddress.ip_address(token):
                    return True
        except Exception:
            continue
    return False


class TicketMessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    media_type: str | None = Field(default=None, max_length=32)
    media_file_id: str | None = Field(default=None, max_length=256)
    media_payload: str | None = Field(default=None, max_length=2000)


class TicketCreateIn(TicketMessageIn):
    subject: str | None = Field(default=None, max_length=200)


class PromoRedeemIn(BaseModel):
    code: str = Field(min_length=3, max_length=20)


class GiftRedeemIn(BaseModel):
    code: str = Field(min_length=3, max_length=32)


class TelegramWebLoginIn(BaseModel):
    id: int
    auth_date: int
    hash: str = Field(min_length=1, max_length=128)
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None


class DevWebLoginIn(BaseModel):
    password: str = Field(min_length=1, max_length=1024)


class TelegramOidcFinishIn(BaseModel):
    code: str = Field(min_length=4, max_length=4096)
    state: str = Field(min_length=16, max_length=4096)


class EmailRegisterIn(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=200)
    display_name: str | None = Field(default=None, max_length=100)


class EmailVerifyIn(BaseModel):
    token: str = Field(min_length=16, max_length=255)


class EmailLoginIn(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=200)


class EmailRecoveryStartIn(BaseModel):
    email: str = Field(min_length=5, max_length=200)


class EmailRecoveryFinishIn(BaseModel):
    token: str = Field(min_length=16, max_length=255)
    password: str = Field(min_length=8, max_length=200)


class AppStartTrialIn(BaseModel):
    install_id: str = Field(min_length=8, max_length=128)
    device_name: str = Field(min_length=2, max_length=120)
    platform: str = Field(min_length=2, max_length=32)
    os_version: str | None = Field(default=None, max_length=64)
    app_version: str | None = Field(default=None, max_length=32)
    locale: str | None = Field(default=None, max_length=32)
    time_zone: str | None = Field(default=None, max_length=64)


class AccessKeyRedeemIn(BaseModel):
    key: str = Field(min_length=3, max_length=64)


class ClientRoutePolicyIn(BaseModel):
    route_mode: str = Field(default=app_first_service.ROUTE_MODE_ALL_TRAFFIC, min_length=3, max_length=32)
    selected_apps: list[str] = Field(default_factory=list, max_length=128)
    requires_elevated_privileges: bool | None = None


class ReviewCreateIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: str = Field(min_length=1, max_length=500)


class FeedbackCreateIn(BaseModel):
    category: str = Field(default="general", min_length=2, max_length=32)
    text: str = Field(min_length=1, max_length=1000)
    source: str = Field(default="webapp", min_length=2, max_length=32)
    review_id: int | None = Field(default=None, ge=1)


class AdminMessageIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class AdminBroadcastIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    segment: str = Field(default="all_active")
    limit: int = Field(default=500, ge=1, le=1000)
    tg_ids: list[int] = Field(default_factory=list)


class AdminTicketReplyIn(TicketMessageIn):
    pass


class AdminTicketStatusIn(BaseModel):
    status: str = Field(min_length=2, max_length=20)


class AdminNodeSyncIn(BaseModel):
    tg_id: int | None = None
    segment: str = Field(default="active")
    limit: int = Field(default=100, ge=1, le=1000)


class AdminNodeLifecycleIn(BaseModel):
    force: bool = False


class AdminNodeResyncIn(BaseModel):
    limit: int = Field(default=100, ge=1, le=1000)
    dry_run: bool = False


class AdminPromoCreateIn(BaseModel):
    code: str = Field(min_length=3, max_length=20)
    promo_type: str = Field(min_length=3, max_length=16)
    value: int = Field(ge=1, le=100000)
    uses_left: int = Field(default=-1, ge=-1, le=1_000_000)
    expires_at: str | None = None


class AdminPromoUpdateIn(BaseModel):
    new_code: str | None = Field(default=None, min_length=3, max_length=20)
    promo_type: str | None = Field(default=None, min_length=3, max_length=16)
    value: int | None = Field(default=None, ge=1, le=100000)
    uses_left: int | None = Field(default=None, ge=-1, le=1_000_000)
    expires_at: str | None = None


class AdminTemplateCreateIn(BaseModel):
    key: str = Field(min_length=2, max_length=50)
    text: str = Field(min_length=1, max_length=2000)


class AdminTemplateUpdateIn(BaseModel):
    new_key: str | None = Field(default=None, min_length=2, max_length=50)
    text: str | None = Field(default=None, min_length=1, max_length=2000)


class AdminGiftCodeCreateIn(BaseModel):
    card_type: str = Field(min_length=3, max_length=20)


class AdminAccessKeyIssueIn(BaseModel):
    plan_code: str = Field(min_length=2, max_length=32)
    quantity: int = Field(default=1, ge=1, le=200)


class AdminPromoSlotAssignmentIn(BaseModel):
    slot_id: str = Field(min_length=3, max_length=120)
    content_id: str = Field(min_length=2, max_length=120)
    enabled: bool = True
    title: str | None = Field(default=None, max_length=160)
    body: str | None = Field(default=None, max_length=500)
    cta_label: str | None = Field(default=None, max_length=80)
    cta_href: str | None = Field(default=None, max_length=600)
    contexts: list[str] = Field(default_factory=list, max_length=32)
    sort_order: int = Field(default=100, ge=0, le=10_000)


class AdminPromoSlotsPutIn(BaseModel):
    assignments: list[AdminPromoSlotAssignmentIn] = Field(default_factory=list, max_length=128)


class EventIn(BaseModel):
    event_name: str = Field(min_length=2, max_length=64)
    source: str = Field(default="webapp", max_length=32)
    session_id: str | None = Field(default=None, max_length=64)
    meta: dict[str, Any] | None = None


class ObserverObservationIn(BaseModel):
    occurred_at: str = Field(min_length=10, max_length=64)
    client_email: str | None = Field(default=None, max_length=200)
    client_sub_id: str | None = Field(default=None, max_length=128)
    client_tg_id: int | None = None
    source_ip: str = Field(min_length=3, max_length=64)
    inbound_tag: str | None = Field(default=None, max_length=128)


class ObserverBatchIn(BaseModel):
    batch_id: str = Field(min_length=3, max_length=128)
    cursor: dict[str, Any] | None = None
    parse_error_count: int = Field(default=0, ge=0, le=100000)
    observations: list[ObserverObservationIn] = Field(default_factory=list)


class PayAttemptStartIn(BaseModel):
    plan_code: str = Field(min_length=2, max_length=32)
    source: str = Field(default="webapp", max_length=32)
    offer_id: int | None = None


class FreekassaOrderCreateIn(BaseModel):
    plan_code: str = Field(min_length=2, max_length=32)
    source: str = Field(default="site", max_length=16)
    tg_id: int | None = None
    campaign: str | None = Field(default=None, max_length=64)
    promo_code: str | None = Field(default=None, max_length=32)
    currency: str = Field(default="RUB", max_length=8)


class FreekassaPublicOrderCreateIn(BaseModel):
    plan_code: str = Field(min_length=2, max_length=32)
    checkout_ticket: str = Field(min_length=16, max_length=1200)
    currency: str = Field(default="RUB", max_length=8)


class FreekassaOrderActionOut(BaseModel):
    ok: bool
    provider: str = "freekassa"
    order_id: str
    payment_url: str | None = None
    amount_rub: float
    currency: str = "RUB"
    status: str
    widget_enabled: bool = False
    discount_applied: bool = False
    base_amount_rub: float | None = None
    discount_pct: int = 0


class RubProviderChoiceOut(BaseModel):
    code: str
    label: str
    accent: str = ""
    checkout_hint: str = ""
    supports_bot: bool = True
    supports_webapp: bool = True
    supports_public: bool = True


class RubProvidersOut(BaseModel):
    ok: bool = True
    providers: list[RubProviderChoiceOut] = Field(default_factory=list)
    blocked: bool = False
    blocked_reasons: list[str] = Field(default_factory=list)
    blocked_reason_texts: list[str] = Field(default_factory=list)
    checkout_mode: str = "account_session_first"
    telegram_fallback_available: bool = True


class RubOrderCreateIn(BaseModel):
    provider: str = Field(min_length=2, max_length=32)
    plan_code: str = Field(min_length=2, max_length=32)
    source: str = Field(default="site", max_length=16)
    tg_id: int | None = None
    campaign: str | None = Field(default=None, max_length=64)
    promo_code: str | None = Field(default=None, max_length=32)
    currency: str = Field(default="RUB", max_length=8)


class RubPublicOrderCreateIn(BaseModel):
    provider: str = Field(min_length=2, max_length=32)
    plan_code: str = Field(min_length=2, max_length=32)
    checkout_ticket: str = Field(min_length=16, max_length=1200)
    currency: str = Field(default="RUB", max_length=8)


class RubOrderActionOut(FreekassaOrderActionOut):
    provider_label: str | None = None


class AdminPlanCreateIn(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    label: str = Field(min_length=2, max_length=120)
    amount_rub: int = Field(ge=0, le=1_000_000)
    amount_stars: int = Field(default=0, ge=0, le=1_000_000)
    days: int = Field(default=30, ge=1, le=3650)
    device_limit: int = Field(default=1, ge=1, le=64)
    node_policy: str | None = Field(default=None, max_length=32)
    badge: str | None = Field(default=None, max_length=32)
    is_active: bool = True
    sort_order: int = Field(default=100, ge=0, le=10000)


class AdminPlanUpdateIn(BaseModel):
    label: str | None = Field(default=None, min_length=2, max_length=120)
    amount_rub: int | None = Field(default=None, ge=0, le=1_000_000)
    amount_stars: int | None = Field(default=None, ge=0, le=1_000_000)
    days: int | None = Field(default=None, ge=1, le=3650)
    device_limit: int | None = Field(default=None, ge=1, le=64)
    node_policy: str | None = Field(default=None, max_length=32)
    badge: str | None = Field(default=None, max_length=32)
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0, le=10000)


class AdminLiveUpdateCreateIn(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    summary: str = Field(min_length=2, max_length=600)
    link: str | None = Field(default=None, min_length=8, max_length=600)
    channel_username: str | None = Field(default=None, min_length=4, max_length=64)
    post_id: int | None = Field(default=None, ge=1, le=2_000_000_000)
    published_at: str | None = None
    is_active: bool = True
    sort_order: int = Field(default=100, ge=0, le=10000)


class AdminLiveUpdateUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    summary: str | None = Field(default=None, min_length=2, max_length=600)
    link: str | None = Field(default=None, min_length=8, max_length=600)
    channel_username: str | None = Field(default=None, min_length=4, max_length=64)
    post_id: int | None = Field(default=None, ge=1, le=2_000_000_000)
    published_at: str | None = None
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0, le=10000)


class AdminStartLinkCreateIn(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    description: str | None = Field(default=None, max_length=240)
    target_action: str = Field(min_length=2, max_length=64)
    is_active: bool = True


class AdminStartLinkUpdateIn(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=64)
    description: str | None = Field(default=None, max_length=240)
    target_action: str | None = Field(default=None, min_length=2, max_length=64)
    is_active: bool | None = None


class AdminWheelWeightIn(BaseModel):
    days: int = Field(ge=1, le=365)
    weight: int = Field(ge=1, le=10000)


class AdminWheelConfigIn(BaseModel):
    preset: str = Field(default="balanced", min_length=2, max_length=32)
    weights: list[AdminWheelWeightIn] = Field(default_factory=list, min_length=1, max_length=20)
    cooldown_hours: int = Field(default=168, ge=1, le=2160)


class AdminCampaignLinksBuildIn(BaseModel):
    promo_code: str | None = Field(default=None, max_length=20)
    campaign_key: str | None = Field(default=None, max_length=64)
    plan_code: str | None = Field(default=None, max_length=32)
    source: str = Field(default="bot", max_length=16)



class DashboardResponse(BaseModel):
    tg_id: int
    sub_type: str
    current_plan_code: str | None = None
    access_state: str
    is_active: bool
    expiry_at: str | None
    used_gb: float
    total_gb: float
    remaining_gb: float
    traffic_policy: dict[str, Any]
    traffic_limit_gb: float | None = None
    traffic_remaining_gb: float | None = None
    next_reset_at: str | None = None
    soft_mode_active: bool = False
    active_sessions: int
    active_sessions_source: str | None = None
    device_limit: int
    speed_limit_mbps: int | None = None
    free_next_reset_at: str | None = None
    family_slots: int
    subscription_url: str
    segment: str
    connection_snapshot: dict[str, Any] | None = None
    client_policy: dict[str, Any] | None = None
    linked_identities: dict[str, Any] | None = None
    free_caps: dict[str, Any] | None = None
    redeem_eligibility: dict[str, Any] | None = None
    promo_slots: dict[str, Any] | None = None
    hidden_transport_matrix: dict[str, Any] | None = None
    location_matrix: dict[str, Any] | None = None
    active_offer: dict[str, Any] | None
    points: dict[str, Any]
    features: dict[str, bool]


class NodeStatusResponse(BaseModel):
    code: str
    country: str
    host: str
    ping_ms: int | None
    port_open: bool
    dns_sni_status: str
    is_healthy: bool
    updated_at: str | None


class NodeDiagnosticsResponse(BaseModel):
    ok: bool
    checked_at: str
    dns_status: str
    sni_status: str
    summary: str


class ClientAndroidApps(BaseModel):
    play_url: str = ""
    apk_url: str = ""
    mirror_url: str = ""


class ClientWindowsApps(BaseModel):
    exe_url: str = ""
    mirror_url: str = ""


class ClientAppsResponse(BaseModel):
    android: ClientAndroidApps
    windows: ClientWindowsApps
    docs_url: str = ""
    updated_at: str


class ManualUserCreateRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=100)
    days: int = Field(default=30, ge=1, le=3650)


class ManualUserExtendRequest(BaseModel):
    days: int | None = Field(default=30, ge=1, le=3650)
    delta_days: int | None = Field(default=None, ge=-3650, le=3650)
    allow_deactivate: bool = False


class ManualUserBlockRequest(BaseModel):
    blocked: bool = True


class AdminUserSafeDeleteIn(BaseModel):
    confirm: bool = False


class AdminUserKeyToggleIn(BaseModel):
    enable: bool


class AdminUserKeysBulkActionIn(BaseModel):
    action: str = Field(min_length=3, max_length=24)  # disable|enable|reset|resync
    segment: str = Field(default="all_active", min_length=2, max_length=32)
    node_codes: list[str] = Field(default_factory=list, max_length=64)
    tg_ids: list[int] = Field(default_factory=list, max_length=500)
    q: str = Field(default="", max_length=120)
    limit: int = Field(default=100, ge=1, le=500)
    dry_run: bool = False
    force: bool = False


class AdminUserKeyLimitsIn(BaseModel):
    burst_mbps: int | None = Field(default=None, ge=1, le=5000)
    soft_cap_gb: int | None = Field(default=None, ge=1, le=1_000_000)
    hard_cap_gb: int | None = Field(default=None, ge=1, le=1_000_000)
    notify_soft: bool = True
    notify_hard: bool = True
    auto_disable_on_hard: bool = True
    apply_now: bool = True


class AdminUserPresetRunIn(BaseModel):
    preset: str = Field(min_length=2, max_length=64)  # reset_key|rotate_link|extend_1d|send_guide


class AdminLoyaltyGrantIn(BaseModel):
    tier_days: int = Field(ge=1, le=3650)


class AdminReferralQueueProcessIn(BaseModel):
    limit: int = Field(default=100, ge=1, le=1000)
    force_without_activity: bool = False


class AdminCampaignCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    campaign_type: str = Field(min_length=3, max_length=16)  # promo|gift
    target_value: str = Field(min_length=2, max_length=64)   # promo code or gift card type
    segment: str = Field(default="all_active", min_length=2, max_length=32)
    starts_at: str | None = None
    ends_at: str | None = None
    max_activations: int = Field(default=-1, ge=-1, le=1_000_000)
    auto_disable: bool = True
    is_active: bool = True
    metadata: dict[str, Any] | None = None


class AdminCampaignUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    segment: str | None = Field(default=None, min_length=2, max_length=32)
    starts_at: str | None = None
    ends_at: str | None = None
    max_activations: int | None = Field(default=None, ge=-1, le=1_000_000)
    auto_disable: bool | None = None
    is_active: bool | None = None
    metadata: dict[str, Any] | None = None


def _plan_total_gb(user: User) -> int:
    st = (user.sub_type or "").upper()
    if st == "FREE":
        plan_code = str(getattr(user, "current_plan_code", "") or "").strip().lower()
        if plan_code == "trial":
            return 0
        return max(0, int(FREE_TOTAL_GB))
    return 0


def _plan_device_limit(user: User) -> int:
    plan_code = str(getattr(user, "current_plan_code", "") or "").strip().lower()
    if plan_code:
        s = SessionLocal()
        try:
            row = _resolve_plan_config(s=s, code=plan_code)
            if row:
                return max(1, int(row.get("device_limit") or 1))
        finally:
            s.close()
    if plan_code == "start_99":
        return 1
    st = (user.sub_type or "").upper()
    if st == "FREE":
        return max(0, int(FREE_LIMIT_IP))
    return max(0, int(PAID_LIMIT_IP))


def _effective_free_speed_kbps(user: User) -> int:
    base = max(1, int(FREE_SPEED_LIMIT_KBPS))
    if (user.sub_type or "").upper() != "FREE":
        return base
    if bool(getattr(user, "_free_soft_mode_active", False)):
        return max(1, int(FREE_SOFT_MODE_SPEED_LIMIT_KBPS))
    if not CHANNEL_SPEED_BUMP_ENABLED:
        return base
    # If channel subscription is not confirmed, keep conservative speed profile.
    if not _user_has_channel_subscriber_mark(user):
        return max(1, int(FREE_SPEED_BUMP_UNSUB_KBPS))
    return base


def _gb_to_bytes(gb: int) -> int:
    if gb <= 0:
        return 0
    return int(gb) * 1024 * 1024 * 1024


def _build_access_policy(*, user: User, used_bytes: int, now: datetime | None = None) -> dict[str, Any]:
    current_now = now or _utcnow()
    sub_type = str(getattr(user, "sub_type", "") or "").strip().upper()
    plan_code = str(getattr(user, "current_plan_code", "") or "").strip().lower()
    expiry = getattr(user, "expiry_at", None)
    active_window = bool(getattr(user, "is_active", False) and expiry and expiry > current_now)
    used_gb = round((int(used_bytes or 0) / (1024**3)), 3) if used_bytes else 0.0
    next_reset_at = _safe_iso(getattr(user, "free_cycle_next_reset_at", None)) if sub_type == "FREE" else None

    if sub_type == "FREE" and active_window and plan_code == "trial":
        access_state = "bonus_premium" if getattr(user, "channel_bonus_claimed_at", None) else "trial_premium"
        return {
            "access_state": access_state,
            "traffic_policy": {
                "kind": "unlimited",
                "label": "premium_unlimited",
            },
            "traffic_limit_gb": None,
            "traffic_remaining_gb": None,
            "next_reset_at": None,
            "soft_mode_active": False,
        }

    if sub_type == "FREE":
        limit_gb = float(max(0, int(FREE_TOTAL_GB)))
        remaining_gb = max(round(limit_gb - used_gb, 3), 0.0) if limit_gb > 0 else 0.0
        soft_mode_active = bool(limit_gb > 0 and int(used_bytes or 0) >= _gb_to_bytes(int(limit_gb)))
        if active_window:
            access_state = "free_soft_mode" if soft_mode_active else "free_monthly"
        else:
            access_state = "expired_or_blocked"
        return {
            "access_state": access_state,
            "traffic_policy": {
                "kind": "soft_limited" if soft_mode_active else "metered",
                "label": "free_monthly",
                "limit_gb": limit_gb,
                "remaining_gb": remaining_gb,
                "next_reset_at": next_reset_at,
            },
            "traffic_limit_gb": limit_gb,
            "traffic_remaining_gb": remaining_gb,
            "next_reset_at": next_reset_at,
            "soft_mode_active": soft_mode_active,
        }

    access_state = "paid_unlimited" if active_window else "expired_or_blocked"
    return {
        "access_state": access_state,
        "traffic_policy": {
            "kind": "unlimited",
            "label": "paid_unlimited",
        },
        "traffic_limit_gb": None,
        "traffic_remaining_gb": None,
        "next_reset_at": None,
        "soft_mode_active": False,
    }


def _maybe_downgrade_expired_to_free(s, user: User) -> bool:
    """
    If a paid plan expires, optionally keep the user in FREE mode automatically.

    Rules:
    - Only when AUTO_DOWNGRADE_TO_FREE=true
    - Only if user is currently active (do not auto-unban manually disabled users)
    - Only when expiry_at has passed
    """
    try:
        if not AUTO_DOWNGRADE_TO_FREE:
            return False
        if not user.is_active:
            return False
        if not user.expiry_at:
            return False
        if user.expiry_at >= _utcnow():
            return False
        if (user.sub_type or "").upper() == "FREE":
            # Already free but expired; extend so the free profile stays usable.
            user.expiry_at = _utcnow() + timedelta(days=int(AUTO_FREE_DAYS))
            user.current_plan_code = "free_monthly"
            ensure_user_free_cycle_state(user)
            s.commit()
            return True

        user.sub_type = "FREE"
        user.current_plan_code = "free_monthly"
        user.expiry_at = _utcnow() + timedelta(days=int(AUTO_FREE_DAYS))
        user.is_active = True
        mark_user_became_free(user)
        s.commit()
        return True
    except Exception:
        return False

app = FastAPI(title="POKROV API", version="2.0.0")


@app.middleware("http")
async def bind_current_request(request: Request, call_next):
    token = _current_request_ctx.set(request)
    try:
        return await call_next(request)
    finally:
        _current_request_ctx.reset(token)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
SUPPORT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount(SUPPORT_UPLOAD_URL_PREFIX, StaticFiles(directory=str(SUPPORT_UPLOAD_DIR)), name="support_uploads")


def _verify_telegram_data(init_data: str) -> dict[str, Any] | None:
    """
    Verify Telegram WebApp initData.
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    """
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        check_hash = parsed.pop("hash", "")
        bot_token = _current_bot_token()
        if not check_hash or not bot_token:
            return None

        data_check_arr = sorted([f"{k}={v}" for k, v in parsed.items()])
        data_check_string = "\n".join(data_check_arr)

        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if calculated_hash != check_hash:
            return None
        return json.loads(parsed.get("user", "{}"))
    except Exception:
        return None


def _safe_iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _track_bonus_event(*, tg_id: int, event_name: str, meta: dict[str, Any] | None = None) -> None:
    track_event(
        tg_id=int(tg_id),
        event_name=str(event_name or "").strip()[:64],
        source="webapp",
        meta=meta or None,
    )


def _parse_optional_datetime(raw: str | None) -> datetime | None:
    value = (raw or "").strip()
    if not value:
        return None
    val = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(val)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid datetime format")
    if parsed.tzinfo:
        parsed = parsed.astimezone(tz=None).replace(tzinfo=None)
    return parsed


def _checkout_secret() -> str:
    return (CHECKOUT_TICKET_SECRET or "").strip()


def _checkout_ticket_sign(raw: bytes) -> str:
    return hmac.new(_checkout_secret().encode("utf-8"), raw, hashlib.sha256).hexdigest()


def _create_checkout_ticket(*, tg_id: int, plan_code: str = "", promo_code: str = "", campaign_key: str = "", source: str = "bot") -> str:
    promo = _sanitize_deeplink_token(promo_code, max_len=20, uppercase=True)
    campaign = _sanitize_deeplink_token(campaign_key, max_len=64, uppercase=False)
    payload = {
        "tg_id": int(tg_id),
        "plan_code": (plan_code or "").strip().lower()[:32],
        "promo_code": promo,
        "campaign_key": campaign,
        "source": (source or "bot").strip().lower()[:16],
        "iat": int(time.time()),
        "exp": int(time.time()) + int(CHECKOUT_TICKET_TTL_SECONDS),
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = _checkout_ticket_sign(raw)
    token = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return f"{token}.{sig}"


def _parse_checkout_ticket(token: str) -> dict[str, Any] | None:
    raw_token = (token or "").strip()
    if not raw_token or "." not in raw_token or not _checkout_secret():
        return None
    b64, sig = raw_token.rsplit(".", 1)
    if not b64 or not sig:
        return None
    padded = b64 + "=" * (-len(b64) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        expected = _checkout_ticket_sign(raw)
        if not hmac.compare_digest(expected, sig):
            return None
        payload = json.loads(raw.decode("utf-8", errors="strict"))
        if not isinstance(payload, dict):
            return None
    except Exception:
        return None
    now_ts = int(time.time())
    exp = int(payload.get("exp") or 0)
    iat = int(payload.get("iat") or 0)
    if exp <= 0 or iat <= 0 or exp < now_ts:
        return None
    if iat > now_ts + 60:
        return None
    return payload


def _plan_rows_db(s, *, only_active: bool = True) -> list[PlanCatalog]:
    q = s.query(PlanCatalog)
    if only_active:
        q = q.filter(PlanCatalog.is_active == True)
    return q.order_by(PlanCatalog.sort_order.asc(), PlanCatalog.id.asc()).all()


def _plan_catalog_payload(*, s, only_active: bool = True) -> list[dict[str, Any]]:
    rows = _plan_rows_db(s, only_active=only_active)
    if not rows:
        fallback = _default_plan_catalog()
        return [x for x in fallback if (x.get("is_active") if only_active else True)]
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "code": str(row.code or "").strip().lower(),
                "label": str(row.label or "").strip(),
                "amount_rub": int(row.amount_rub or 0),
                "amount_stars": int(row.amount_stars or 0),
                "days": max(1, int(row.days or 30)),
                "device_limit": max(1, int(row.device_limit or 1)),
                "node_policy": str(row.node_policy or "").strip() or None,
                "badge": str(row.badge or "").strip() or None,
                "is_active": bool(row.is_active),
                "sort_order": int(row.sort_order or 0),
                "created_at": _safe_iso(getattr(row, "created_at", None)),
                "updated_at": _safe_iso(getattr(row, "updated_at", None)),
            }
        )
    return out


def _resolve_plan_config(*, s, code: str) -> dict[str, Any] | None:
    target = (code or "").strip().lower()
    if not target:
        return None
    for row in _plan_catalog_payload(s=s, only_active=False):
        if str(row.get("code") or "").strip().lower() == target:
            return row
    return None


def _access_matrix_state_facts(access_state: str | None) -> dict[str, Any]:
    states = dict(_ACCESS_MATRIX.get("states") or {})
    return dict(states.get(str(access_state or "").strip(), {}) or {})


def _normalized_plan_payload(plan: dict[str, Any] | None, *, fallback_code: str = "") -> dict[str, Any] | None:
    if not plan:
        return None
    code = str(plan.get("code") or fallback_code).strip().lower()
    if not code:
        return None
    return {
        "code": code,
        "label": _normalize_mojibake(str(plan.get("label") or code).strip()),
        "amount_rub": int(plan.get("amount_rub") or 0),
        "amount_stars": int(plan.get("amount_stars") or 0),
        "days": int(plan.get("days") or plan.get("duration_days") or 0),
        "device_limit": max(1, int(plan.get("device_limit") or 1)),
        "node_policy": str(plan.get("node_policy") or "").strip() or None,
        "badge": str(plan.get("badge") or "").strip() or None,
        "comparison_group": str(plan.get("comparison_group") or "").strip() or None,
    }


def _access_key_meta_from_card_type(*, s, card_type: str) -> dict[str, Any] | None:
    normalized = str(card_type or "").strip().lower()
    if not normalized:
        return None

    plan = _resolve_plan_config(s=s, code=normalized)
    normalized_plan = _normalized_plan_payload(plan, fallback_code=normalized)
    if normalized_plan:
        return {
            "kind": "plan",
            "plan_code": normalized_plan["code"],
            "plan": normalized_plan,
            "days": int(normalized_plan["days"] or 0),
            "device_limit": int(normalized_plan["device_limit"] or 1),
            "node_policy": normalized_plan.get("node_policy"),
        }

    legacy = dict(GIFT_CARD_TYPES.get(normalized) or {})
    if not legacy:
        return None

    hinted_plan_code = str(LEGACY_GIFT_PLAN_HINTS.get(normalized) or "").strip().lower()
    hinted_plan = _normalized_plan_payload(_resolve_plan_config(s=s, code=hinted_plan_code), fallback_code=hinted_plan_code)
    return {
        "kind": "legacy_gift",
        "legacy_type": normalized,
        "plan_code": hinted_plan_code or None,
        "plan": hinted_plan,
        "days": int(legacy.get("days") or 0),
        "device_limit": int((hinted_plan or {}).get("device_limit") or 1),
        "node_policy": (hinted_plan or {}).get("node_policy"),
        "label": str(legacy.get("name") or normalized).strip(),
    }


def _access_key_status_payload(*, s, card: GiftCard) -> dict[str, Any]:
    meta = _access_key_meta_from_card_type(s=s, card_type=str(card.card_type or ""))
    return {
        "key": str(card.code or "").strip(),
        "exists": True,
        "redeemed": bool(card.redeemed_by is not None),
        "redeemed_at": _safe_iso(getattr(card, "redeemed_at", None)),
        "issued_at": _safe_iso(getattr(card, "created_at", None)),
        "plan": meta.get("plan") if meta else None,
        "kind": str(meta.get("kind") or "unknown") if meta else "unknown",
        "legacy_type": meta.get("legacy_type") if meta else None,
        "days": int(meta.get("days") or 0) if meta else 0,
        "device_limit": int(meta.get("device_limit") or 0) if meta else 0,
        "node_policy": meta.get("node_policy") if meta else None,
        "created_by": int(card.created_by or 0) if getattr(card, "created_by", None) is not None else None,
        "redeemed_by": int(card.redeemed_by or 0) if getattr(card, "redeemed_by", None) is not None else None,
    }


def _apply_access_key_to_user(*, user: User, meta: dict[str, Any], now: datetime) -> dict[str, Any]:
    days = max(1, int(meta.get("days") or 0))
    current_expiry = getattr(user, "expiry_at", None)
    if not current_expiry or current_expiry <= now:
        current_expiry = now

    if not getattr(user, "uuid", None):
        user.uuid = str(uuid.uuid4())
    if not getattr(user, "email", None):
        user.email = f"User_{int(user.tg_id)}"
    if not getattr(user, "sub_token", None):
        user.sub_token = secrets.token_urlsafe(32)

    user.expiry_at = current_expiry + timedelta(days=days)
    user.sub_type = "PAID"
    user.is_active = True
    user.first_purchase_done = True

    plan_code = str(meta.get("plan_code") or "").strip().lower()
    if plan_code:
        user.current_plan_code = plan_code

    return {
        "expiry_at": _safe_iso(getattr(user, "expiry_at", None)),
        "current_plan_code": str(getattr(user, "current_plan_code", "") or "").strip().lower() or None,
    }


async def _sync_control_panel_access(*, user: User) -> bool:
    sync_ok = False
    panel = ControlPanel()
    try:
        sync_ok = bool(
            await panel.add_client(
                user_uuid=str(user.uuid or ""),
                email=str(user.email or f"User_{int(user.tg_id)}"),
                sub_type=str(user.sub_type or "FREE"),
                total_gb=int(user.total_gb or 0),
                tg_id=int(user.tg_id),
                sub_token=str(user.sub_token or ""),
            )
        )
    except Exception:
        sync_ok = False
    finally:
        await panel.close()
    return sync_ok


def _linked_identities_payload(*, s, user: User, auth_user: dict[str, Any] | None = None) -> dict[str, Any]:
    email_identity = get_verified_identity_for_user(s, tg_id=int(user.tg_id))
    telegram_id = _linked_telegram_id(user) or (0 if bool(getattr(user, "is_app_user", False)) else int(user.tg_id))
    telegram_username = (
        str(getattr(user, "linked_telegram_username", "") or "").strip()
        or (str(getattr(user, "username", "") or "").strip() if telegram_id and not bool(getattr(user, "is_app_user", False)) else "")
        or (str((auth_user or {}).get("username") or "").strip() if telegram_id else "")
    )
    return {
        "app_account": {
            "id": str(int(user.tg_id)),
            "install_id": str(getattr(user, "app_install_id", "") or "").strip() or None,
            "device_name": _normalize_app_device_name(
                getattr(user, "app_device_name", None) or getattr(user, "display_name", None),
            ),
            "platform": str(getattr(user, "app_platform", "") or "").strip() or None,
            "created_at": _safe_iso(getattr(user, "created_at", None)),
        },
        "telegram": {
            "id": telegram_id or None,
            "username": telegram_username or None,
            "linked": bool(telegram_id),
            "role": str(_ACCESS_ENTRY_FLOWS.get("telegram", {}).get("role") or "").strip() or None,
        },
        "email": _email_identity_payload(email_identity),
        "devices": _build_app_device_rows(user),
    }


def _free_caps_payload(*, user: User, access_policy: dict[str, Any]) -> dict[str, Any]:
    free_active = str(access_policy.get("access_state") or "").strip() in {"free_monthly", "free_soft_mode"}
    return {
        "plan_code": str(_FREE_TIER_FACTS.get("plan_code") or "free_monthly"),
        "location_code": str(_FREE_TIER_FACTS.get("location_code") or "NL-free"),
        "traffic_limit_gb": int(_FREE_TIER_FACTS.get("traffic_limit_gb") or 5),
        "cycle_days": int(_FREE_TIER_FACTS.get("cycle_days") or 30),
        "speed_limit_mbps": int(_FREE_TIER_FACTS.get("speed_limit_mbps") or 50),
        "soft_mode_speed_limit_mbps": int(_FREE_TIER_FACTS.get("soft_mode_speed_limit_mbps") or 2),
        "device_limit": int(_FREE_TIER_FACTS.get("device_limit") or 1),
        "monthly_reset": bool(_FREE_TIER_FACTS.get("monthly_reset", True)),
        "active": free_active,
        "next_reset_at": access_policy.get("next_reset_at"),
    }


def _redeem_eligibility_payload(*, user: User, access_policy: dict[str, Any]) -> dict[str, Any]:
    access_state = str(access_policy.get("access_state") or "").strip()
    state_facts = _access_matrix_state_facts(access_state)
    eligible = bool(state_facts.get("redeem_eligible", True))
    reason = None
    if not eligible:
        reason = "already_managed_premium"
    return {
        "eligible": eligible,
        "access_state": access_state,
        "reason": reason,
        "buy_flow": str((_TARIFF_CATALOG.get("commerce_model") or {}).get("primary_purchase_flow") or "buy_key"),
        "redeem_flow": str((_TARIFF_CATALOG.get("commerce_model") or {}).get("primary_fulfillment_flow") or "redeem_key"),
    }


def _hidden_transport_matrix_payload(*, nodes: list[Any], client_policy: dict[str, Any] | None = None) -> dict[str, Any]:
    order = list(_ACCESS_PUBLIC_DEFAULTS.get("hidden_transport_order") or ["vless_reality", "vmess", "trojan", "xhttp"])
    active_transport = str((client_policy or {}).get("transport_kind") or "").strip().lower()
    xhttp_available = any(
        _node_supports_transport_profile(node, RESERVE_XHTTP_CDN) or _node_supports_transport_profile(node, OPERATOR_LAB)
        for node in (nodes or [])
    )
    transports: list[dict[str, Any]] = []
    for key in order:
        available = False
        gated_reason = None
        if key == "vless_reality":
            available = True
        elif key == "xhttp":
            available = bool(xhttp_available)
            if not available:
                gated_reason = "cdn_static_prerequisite"
        else:
            gated_reason = "not_enabled_in_current_rollout"
        transports.append(
            {
                "id": key,
                "hidden": True,
                "available": available,
                "active": active_transport == key,
                "gated_reason": gated_reason,
            }
        )
    return {
        "logical_location_count": int(_ACCESS_PUBLIC_DEFAULTS.get("logical_location_count") or 1),
        "logical_location_label": str(_ACCESS_PUBLIC_DEFAULTS.get("logical_location_label") or "POKROV"),
        "order": order,
        "transports": transports,
    }


def _location_matrix_payload(*, user: User, nodes: list[Any], client_policy: dict[str, Any] | None = None) -> dict[str, Any]:
    route_mode = str((client_policy or {}).get("route_mode") or "").strip().lower()
    active_public_route = "selected_apps" if route_mode == "selected_apps" else "all_except_ru"
    hidden_transport_matrix = _hidden_transport_matrix_payload(nodes=nodes, client_policy=client_policy)
    return {
        "entries": [
            {
                "id": "pokrov-managed",
                "label": str(_ACCESS_PUBLIC_DEFAULTS.get("logical_location_label") or "POKROV"),
                "visible": True,
                "recommended": True,
                "active_routing_mode": active_public_route,
                "routing_modes": [
                    {"id": "all_except_ru", "label": "All except RU", "default": True},
                    {"id": "full_tunnel", "label": "Full tunnel", "default": False},
                    {"id": "selected_apps", "label": "Selected apps", "default": False},
                ],
                "hidden_transport_matrix": hidden_transport_matrix,
            }
        ],
    }


def _promo_slot_catalog_maps() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    slot_map = {
        str(slot.get("id") or "").strip(): dict(slot)
        for slot in list(_PROMO_SLOTS.get("slots") or [])
        if str(slot.get("id") or "").strip()
    }
    content_map = {
        str(item.get("id") or "").strip(): dict(item)
        for item in list(_PROMO_SLOTS.get("content_catalog") or [])
        if str(item.get("id") or "").strip()
    }
    return slot_map, content_map


def _normalize_promo_slot_assignment(raw: dict[str, Any], *, strict: bool) -> dict[str, Any] | None:
    slot_map, content_map = _promo_slot_catalog_maps()
    slot_id = str(raw.get("slot_id") or "").strip()
    if slot_id not in slot_map:
        if strict:
            raise HTTPException(status_code=400, detail=f"Unsupported promo slot: {slot_id or 'empty'}")
        return None

    content_id = str(raw.get("content_id") or "").strip()
    if content_id not in content_map:
        if strict:
            raise HTTPException(status_code=400, detail=f"Unsupported promo content: {content_id or 'empty'}")
        return None

    slot_facts = slot_map[slot_id]
    allowed_content_ids = {
        str(item).strip()
        for item in list(slot_facts.get("allowed_content_ids") or [])
        if str(item).strip()
    }
    if content_id not in allowed_content_ids:
        if strict:
            raise HTTPException(status_code=400, detail=f"Promo content {content_id} is not allowed for slot {slot_id}")
        return None

    allowed_contexts = {
        str(item).strip()
        for item in list(slot_facts.get("contexts") or [])
        if str(item).strip()
    }
    contexts: list[str] = []
    for raw_context in list(raw.get("contexts") or []):
        context = str(raw_context or "").strip()
        if not context:
            continue
        if context not in allowed_contexts:
            if strict:
                raise HTTPException(status_code=400, detail=f"Promo context {context} is not allowed for slot {slot_id}")
            continue
        if context not in contexts:
            contexts.append(context)
    if not contexts:
        contexts = list(allowed_contexts)

    return {
        "slot_id": slot_id,
        "content_id": content_id,
        "enabled": bool(raw.get("enabled", True)),
        "title": str(raw.get("title") or "").strip()[:160] or None,
        "body": str(raw.get("body") or "").strip()[:500] or None,
        "cta_label": str(raw.get("cta_label") or "").strip()[:80] or None,
        "cta_href": str(raw.get("cta_href") or "").strip()[:600] or None,
        "contexts": contexts,
        "sort_order": max(0, int(raw.get("sort_order") or 100)),
    }


def _normalized_promo_slots_config(raw: Any, *, strict: bool = False) -> dict[str, Any]:
    assignments_raw = []
    if isinstance(raw, dict):
        assignments_raw = list(raw.get("assignments") or [])

    assignments: list[dict[str, Any]] = []
    for item in assignments_raw:
        if not isinstance(item, dict):
            if strict:
                raise HTTPException(status_code=400, detail="Promo assignments must be objects")
            continue
        normalized = _normalize_promo_slot_assignment(item, strict=strict)
        if normalized:
            assignments.append(normalized)

    assignments.sort(key=lambda item: (int(item.get("sort_order") or 100), str(item.get("slot_id") or ""), str(item.get("content_id") or "")))
    return {
        "version": str(_PROMO_SLOTS.get("version") or ""),
        "assignments": assignments,
        "remote_available": bool(assignments),
        "fallback_behavior": str(_PROMO_SLOTS.get("fallback_behavior") or "contextual_only_when_remote_unavailable"),
        "mode": str(_PROMO_SLOTS.get("mode") or "whitelist_slots"),
    }


def _promo_slots_payload_for_surface(*, s, surface: str, access_state: str) -> dict[str, Any]:
    slot_map, content_map = _promo_slot_catalog_maps()
    normalized = _normalized_promo_slots_config(
        _get_app_setting_json(s=s, key=PROMO_SLOTS_CONFIG_KEY, default={}),
        strict=False,
    )
    approved_slots = [
        dict(slot)
        for slot in slot_map.values()
        if str(slot.get("surface") or "").strip() == str(surface or "").strip()
    ]

    slots: list[dict[str, Any]] = []
    for assignment in list(normalized.get("assignments") or []):
        slot_id = str(assignment.get("slot_id") or "").strip()
        slot_facts = slot_map.get(slot_id)
        if not slot_facts:
            continue
        if str(slot_facts.get("surface") or "").strip() != str(surface or "").strip():
            continue
        if str(access_state or "").strip() not in set(assignment.get("contexts") or []):
            continue
        content_id = str(assignment.get("content_id") or "").strip()
        content_facts = dict(content_map.get(content_id) or {})
        slots.append(
            {
                "slot_id": slot_id,
                "surface": str(slot_facts.get("surface") or "").strip(),
                "enabled": bool(assignment.get("enabled", True)),
                "content_id": content_id,
                "contexts": list(assignment.get("contexts") or []),
                "title": assignment.get("title"),
                "body": assignment.get("body"),
                "cta_label": assignment.get("cta_label"),
                "cta_href": assignment.get("cta_href"),
                "sort_order": int(assignment.get("sort_order") or 100),
                "goal": str(content_facts.get("goal") or "").strip() or None,
                "kind": str(content_facts.get("kind") or "").strip() or None,
            }
        )

    return {
        "surface": str(surface or "").strip(),
        "access_state": str(access_state or "").strip(),
        "remote_available": bool(normalized.get("remote_available")),
        "fallback_behavior": str(normalized.get("fallback_behavior") or "contextual_only_when_remote_unavailable"),
        "mode": str(normalized.get("mode") or "whitelist_slots"),
        "approved_slots": approved_slots,
        "slots": slots,
    }


def _public_catalog_payload(*, s) -> dict[str, Any]:
    return {
        "catalog_version": str(_TARIFF_CATALOG.get("catalog_version") or ""),
        "commerce_model": dict(_TARIFF_CATALOG.get("commerce_model") or {}),
        "public_surface_policy": dict(_TARIFF_CATALOG.get("public_surface_policy") or {}),
        "pricing_preview": dict(_TARIFF_CATALOG.get("pricing_preview") or {}),
        "plans": _plan_catalog_payload(s=s, only_active=True),
        "free_tier": dict(_FREE_TIER_FACTS),
        "public_defaults": dict(_ACCESS_PUBLIC_DEFAULTS),
        "promo_slots": {
            "mode": str(_PROMO_SLOTS.get("mode") or "whitelist_slots"),
            "fallback_behavior": str(_PROMO_SLOTS.get("fallback_behavior") or "contextual_only_when_remote_unavailable"),
            "slot_ids": [str(slot.get("id") or "").strip() for slot in list(_PROMO_SLOTS.get("slots") or []) if str(slot.get("id") or "").strip()],
        },
    }


def _price_with_pending_discount(*, amount_rub: int, pending_pct: int | None) -> tuple[int, int]:
    base = max(0, int(amount_rub))
    pct = max(0, min(95, int(pending_pct or 0)))
    if base <= 0 or pct <= 0:
        return base, 0
    discounted = int(round(base * (1.0 - (pct / 100.0))))
    return max(1, discounted), pct


def _generate_gift_code_for_admin(s) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    for _ in range(30):
        token = "".join(secrets.choice(alphabet) for _ in range(8))
        code = f"POKROV-{token[:4]}-{token[4:]}"
        exists = s.query(GiftCard.id).filter(GiftCard.code == code).first()
        if not exists:
            return code
    raise HTTPException(status_code=500, detail="Failed to generate unique gift code")


_CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
_MOJIBAKE_RE = re.compile(r"(?:Ð.|Ñ.|Р.|С.)")


def _normalize_mojibake(text: str | None) -> str:
    raw = (text or "").strip()
    if not raw:
        return ""
    if _CYRILLIC_RE.search(raw):
        return raw
    if not _MOJIBAKE_RE.search(raw):
        return raw
    for enc in ("latin1", "cp1252"):
        try:
            fixed = raw.encode(enc, errors="strict").decode("utf-8", errors="strict")
        except Exception:
            continue
        if _CYRILLIC_RE.search(fixed):
            return fixed
    return raw


def _mask_public_username(username: str | None) -> str:
    raw = _normalize_mojibake(username).strip()
    if raw.startswith("@"):
        raw = raw[1:].strip()
    raw = re.sub(r"\s+", "", raw)
    if not raw:
        return "Пользователь"
    return f"{raw[:4]}****"


def _normalize_feedback_text(text_value: str | None, *, max_len: int) -> str:
    normalized = _normalize_mojibake(text_value or "")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized[:max_len]


_FEEDBACK_CATEGORY_ALLOWLIST = {"general", "idea", "bug", "support", "review", "billing"}
_FEEDBACK_SOURCE_ALLOWLIST = {"webapp", "marketing", "bot", "support"}


def _normalize_feedback_category(raw_value: str | None) -> str:
    value = re.sub(r"[^a-z0-9_]+", "", str(raw_value or "").strip().lower())
    if not value:
        return "general"
    if value not in _FEEDBACK_CATEGORY_ALLOWLIST:
        raise HTTPException(status_code=400, detail="Unsupported feedback category")
    return value


def _normalize_feedback_source(raw_value: str | None) -> str:
    value = re.sub(r"[^a-z0-9_]+", "", str(raw_value or "").strip().lower())
    if not value:
        return "webapp"
    if value not in _FEEDBACK_SOURCE_ALLOWLIST:
        raise HTTPException(status_code=400, detail="Unsupported feedback source")
    return value


def _is_admin_tg(tg_id: int) -> bool:
    return int(Settings.ADMIN_ID or 0) > 0 and int(tg_id) == int(Settings.ADMIN_ID)


def _normalize_origin(raw: str) -> str:
    val = (raw or "").strip()
    if not val:
        return ""
    try:
        host = val.split("://", 1)
        if len(host) == 2:
            scheme = host[0].lower()
            rest = host[1].split("/", 1)[0].strip().lower()
            return f"{scheme}://{rest}".rstrip("/")
    except Exception:
        pass
    return val.lower().rstrip("/")


def _is_allowed_dev_origin(raw: str) -> bool:
    norm = _normalize_origin(raw)
    if not norm:
        return True
    return norm in WEBAPP_DEV_ALLOWED_ORIGINS


def _is_local_request(request: Request | None) -> bool:
    if request is None:
        return False
    host = (request.url.hostname or "").strip().lower()
    is_loopback_host = False
    if host in API_LOCALHOST_DEV_HOSTS:
        is_loopback_host = True
    else:
        try:
            ip = ipaddress.ip_address(host)
            is_loopback_host = ip.is_loopback
        except Exception:
            is_loopback_host = False
    if not is_loopback_host:
        return False

    origin = request.headers.get("origin", "")
    referer = request.headers.get("referer", "")
    if origin and not _is_allowed_dev_origin(origin):
        return False
    if referer and not _is_allowed_dev_origin(referer):
        return False

    return True


def _extract_web_session_token(request: Request | None) -> str:
    if request is None:
        request = _current_request_ctx.get()
    if request is None:
        return ""
    auth_header = str(request.headers.get("authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return str(request.headers.get("x-web-auth-token") or "").strip()


def _optional_auth_user(x_telegram_init_data: str, request: Request | None = None) -> dict[str, Any] | None:
    init_data = (x_telegram_init_data or "").strip()
    if init_data:
        user_data = _verify_telegram_data(init_data)
        if user_data:
            return {
                "id": int(user_data.get("id") or 0),
                "username": user_data.get("username"),
                "auth_type": "telegram",
                "auth_origin": "telegram",
                "email": None,
            }
        raise HTTPException(status_code=401, detail="Invalid Telegram signature")

    web_token = _extract_web_session_token(request)
    if web_token:
        payload = verify_web_session_token(web_token)
        if payload:
            return payload
        raise HTTPException(status_code=401, detail="Invalid web session")

    return None


def _request_client_ip(request: Request | None) -> str:
    if request is None:
        request = _current_request_ctx.get()
    if request is None:
        return ""
    for header in ("cf-connecting-ip", "x-real-ip", "x-forwarded-for"):
        raw = str(request.headers.get(header) or "").strip()
        if not raw:
            continue
        if header == "x-forwarded-for":
            raw = raw.split(",", 1)[0].strip()
        if raw:
            return raw[:64]
    client = getattr(request, "client", None)
    host = getattr(client, "host", "") if client else ""
    return str(host or "").strip()[:64]


def _normalize_app_device_name(value: str | None, *, fallback: str = "Current device") -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    return text[:120]


def _build_app_device_rows(user: User) -> list[dict[str, Any]]:
    install_id = str(getattr(user, "app_install_id", "") or "").strip()
    if not install_id:
        return []
    return [
        {
            "id": install_id,
            "name": _normalize_app_device_name(
                getattr(user, "app_device_name", None) or getattr(user, "display_name", None),
            ),
            "platform": str(getattr(user, "app_platform", "") or "").strip() or "device",
            "os_version": str(getattr(user, "app_os_version", "") or "").strip() or None,
            "app_version": str(getattr(user, "app_version", "") or "").strip() or None,
            "last_seen_at": _safe_iso(getattr(user, "app_last_seen_at", None) or getattr(user, "created_at", None)),
            "is_active": bool(getattr(user, "is_active", False)),
            "is_current": True,
        }
    ]


def _linked_telegram_id(user: User | None) -> int:
    if not user:
        return 0
    return int(getattr(user, "linked_telegram_id", 0) or 0)


def _membership_check_tg_id(user: User | None) -> int:
    if not user:
        return 0
    if bool(getattr(user, "is_app_user", False)):
        return _linked_telegram_id(user)
    return int(getattr(user, "tg_id", 0) or 0)


def _email_identity_payload(identity: WebEmailIdentity | None) -> dict[str, Any] | None:
    if not identity:
        return None
    return {
        "email": str(getattr(identity, "email", "") or "").strip() or None,
        "verified": bool(getattr(identity, "is_verified", False)),
        "verified_at": _safe_iso(getattr(identity, "verified_at", None)),
    }


def _ensure_user_row_for_login(*, tg_id: int, username: str | None = None) -> None:
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if user:
            normalized = str(username or "").strip()[:100] or None
            if username is not None and user.username != normalized:
                user.username = normalized
                s.commit()
            return

        now = _utcnow()
        sub_token = secrets.token_urlsafe(32)
        row = User(
            tg_id=int(tg_id),
            username=(str(username).strip()[:100] if username else None),
            uuid=str(uuid.uuid4()),
            email=f"User_{int(tg_id)}",
            sub_type="FREE",
            current_plan_code="free_monthly",
            created_at=now,
            expiry_at=now + timedelta(days=max(3650, int(AUTO_FREE_DAYS))),
            is_active=True,
            stars_paid=0,
            total_gb=0,
            trial_used=False,
            tos_accepted=False,
            sub_token=sub_token,
        )
        mark_user_became_free(row, now=now)
        s.add(row)
        s.commit()
    except Exception:
        s.rollback()
    finally:
        s.close()


def _plan_segment(user: User, now: datetime | None = None) -> str:
    n = now or _utcnow()
    sub = (user.sub_type or "").upper().strip()
    if sub == "MANUAL":
        return "MANUAL"
    if not user.is_active or not user.expiry_at or user.expiry_at <= n:
        return "EXPIRED"
    if sub == "FREE":
        return "FREE"
    return "PAID"


def _manual_test_user_filter():
    return or_(
        User.is_manual == True,
        User.tg_id < 0,
        func.upper(func.coalesce(User.sub_type, "")) == "MANUAL",
        User.created_by_admin.isnot(None),
    )


def _effective_active_user_filter(*, now: datetime):
    return and_(
        User.tg_id > 0,
        ~_manual_test_user_filter(),
        User.is_active == True,
        User.expiry_at.isnot(None),
        User.expiry_at > now,
    )


def _premium_entitlement_filter():
    sub_type = func.upper(func.coalesce(User.sub_type, ""))
    plan_code = func.lower(func.coalesce(User.current_plan_code, ""))
    return or_(
        plan_code.in_(["trial", "channel_bonus", "start_99"]),
        sub_type.in_(["PAID", "BONUS", "CHANNEL_BONUS", "OPENING_BONUS", "FRIEND_GIFT", "VIP", "PRO", "BASIC", "MONTHLY", "QUARTERLY", "HALF_YEAR", "YEARLY"]),
        sub_type.like("PAID%"),
        sub_type.like("PREMIUM%"),
        sub_type.like("TRIAL%"),
        sub_type.like("BONUS%"),
    )


def _trial_entitlement_filter():
    sub_type = func.upper(func.coalesce(User.sub_type, ""))
    plan_code = func.lower(func.coalesce(User.current_plan_code, ""))
    return or_(plan_code == "trial", sub_type.like("TRIAL%"))


def _bonus_entitlement_filter():
    sub_type = func.upper(func.coalesce(User.sub_type, ""))
    plan_code = func.lower(func.coalesce(User.current_plan_code, ""))
    return or_(
        User.channel_bonus_claimed_at.isnot(None),
        plan_code == "channel_bonus",
        sub_type.in_(["BONUS", "CHANNEL_BONUS", "OPENING_BONUS", "FRIEND_GIFT"]),
        sub_type.like("BONUS%"),
    )


def _app_origin_filter():
    return or_(User.is_app_user == True, User.app_install_id.isnot(None))


def _is_manual_test_user(user: User) -> bool:
    try:
        tg_id = int(getattr(user, "tg_id", 0) or 0)
    except Exception:
        tg_id = 0
    sub = str(getattr(user, "sub_type", "") or "").strip().upper()
    return bool(
        getattr(user, "is_manual", False)
        or tg_id < 0
        or sub == "MANUAL"
        or getattr(user, "created_by_admin", None) is not None
    )


def _user_effective_status(user: User, now: datetime | None = None) -> str:
    if _is_manual_test_user(user):
        return "manual_test"
    n = now or _utcnow()
    expiry = getattr(user, "expiry_at", None)
    if bool(getattr(user, "is_active", False)) and expiry and expiry > n:
        return "active"
    if (not bool(getattr(user, "is_active", False))) and expiry and expiry > n:
        return "blocked"
    return "expired"


def _user_origin(user: User) -> str:
    if _is_manual_test_user(user):
        return "manual_test"
    is_app = bool(getattr(user, "is_app_user", False) or str(getattr(user, "app_install_id", "") or "").strip())
    if is_app:
        return "app"
    return "telegram"


def _apply_admin_user_search(query, q: str):
    q_norm = str(q or "").strip()
    if not q_norm:
        return query
    filters = [
        User.username.ilike(f"%{q_norm}%"),
        User.display_name.ilike(f"%{q_norm}%"),
        User.email.ilike(f"%{q_norm}%"),
        User.linked_telegram_username.ilike(f"%{q_norm}%"),
        User.app_install_id.ilike(f"%{q_norm}%"),
    ]
    if q_norm.isdigit():
        filters.extend(
            [
                User.tg_id == int(q_norm),
                User.linked_telegram_id == int(q_norm),
            ]
        )
    return query.filter(or_(*filters))


def _admin_user_status_filter(status: str, *, now: datetime):
    status_norm = str(status or "").strip().lower()
    manual_expr = _manual_test_user_filter()
    active_expr = and_(~manual_expr, User.is_active == True, User.expiry_at.isnot(None), User.expiry_at > now)
    blocked_expr = and_(~manual_expr, User.is_active == False, User.expiry_at.isnot(None), User.expiry_at > now)
    expired_expr = and_(~manual_expr, or_(User.expiry_at.is_(None), User.expiry_at <= now))
    if status_norm in {"", "all"}:
        return None
    if status_norm == "active":
        return active_expr
    if status_norm == "blocked":
        return blocked_expr
    if status_norm == "expired":
        return expired_expr
    if status_norm == "inactive":
        return or_(blocked_expr, expired_expr)
    if status_norm in {"manual", "manual_test"}:
        return manual_expr
    raise HTTPException(status_code=400, detail="Unsupported status")


def _admin_user_origin_filter(origin: str):
    origin_norm = str(origin or "").strip().lower()
    if origin_norm in {"", "all"}:
        return None
    manual_expr = _manual_test_user_filter()
    app_expr = _app_origin_filter()
    if origin_norm in {"manual", "manual_test"}:
        return manual_expr
    if origin_norm == "app":
        return and_(~manual_expr, app_expr, or_(User.linked_telegram_id.is_(None), User.username.is_(None)))
    if origin_norm == "hybrid":
        return and_(~manual_expr, app_expr, User.linked_telegram_id.isnot(None), User.username.isnot(None))
    if origin_norm == "telegram":
        return and_(~manual_expr, ~app_expr)
    raise HTTPException(status_code=400, detail="Unsupported origin")


def _normalize_observer_state_filter(value: str) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"", "all"}:
        return ""
    if raw not in {"ok", "watch", "suspicious"}:
        raise HTTPException(status_code=400, detail="Unsupported observer_state")
    return raw


def _observer_snapshot_or_default(snapshot: dict[str, Any] | None) -> dict[str, Any]:
    data = dict(snapshot or {})
    return {
        "state": str(data.get("state") or "ok"),
        "updated_at": data.get("updated_at"),
    }


def _serialize_admin_user_row(
    user: User,
    *,
    now: datetime | None = None,
    observer_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    current_now = now or _utcnow()
    status = _user_effective_status(user, now=current_now)
    origin = _user_origin(user)
    observer = _observer_snapshot_or_default(observer_snapshot)
    return {
        "tg_id": int(user.tg_id),
        "username": user.username,
        "display_name": getattr(user, "display_name", None),
        "sub_type": user.sub_type,
        "is_active": bool(user.is_active),
        "effective_active": bool(status == "active"),
        "status": status,
        "origin": origin,
        "is_manual": bool(_is_manual_test_user(user)),
        "expiry_at": _safe_iso(user.expiry_at),
        "stars_paid": int(user.stars_paid or 0),
        "created_at": _safe_iso(user.created_at),
        "linked_telegram_id": int(user.linked_telegram_id) if getattr(user, "linked_telegram_id", None) is not None else None,
        "linked_telegram_username": getattr(user, "linked_telegram_username", None),
        "app_install_id": getattr(user, "app_install_id", None),
        "observer_state": observer["state"],
        "observer_updated_at": observer["updated_at"],
    }


def _ensure_free_cycle_state_persisted(s, user: User) -> None:
    if (user.sub_type or "").upper().strip() != "FREE":
        return
    if ensure_user_free_cycle_state(user):
        s.commit()
        try:
            s.refresh(user)
        except Exception:
            pass


def _family_slots_for_user(s, tg_id: int) -> int:
    now = _utcnow()
    total = (
        s.query(func.coalesce(func.sum(FamilySlot.slots), 0))
        .filter(FamilySlot.tg_id == int(tg_id))
        .filter((FamilySlot.expires_at.is_(None)) | (FamilySlot.expires_at > now))
        .scalar()
        or 0
    )
    return int(total)


def _has_campaign_mark(s, *, tg_id: int, campaign_key: str) -> bool:
    row = (
        s.query(CampaignSend.id)
        .filter(CampaignSend.tg_id == int(tg_id))
        .filter(CampaignSend.campaign_key == str(campaign_key))
        .first()
    )
    return bool(row)


def _mark_campaign_once(s, *, tg_id: int, campaign_key: str) -> bool:
    try:
        with s.begin_nested():
            s.add(CampaignSend(tg_id=int(tg_id), campaign_key=str(campaign_key), sent_at=_utcnow()))
            s.flush()
        return True
    except IntegrityError:
        return False


def _user_has_channel_subscriber_mark(user: User | None) -> bool:
    if not user:
        return False
    if getattr(user, "channel_bonus_claimed_at", None):
        return True
    s = SessionLocal()
    try:
        return _has_campaign_mark(
            s,
            tg_id=int(getattr(user, "tg_id", 0) or 0),
            campaign_key=CHANNEL_SUBSCRIBER_CAMPAIGN_KEY,
        )
    finally:
        s.close()


def _active_offer_payload(tg_id: int) -> dict[str, Any] | None:
    offer = get_active_offer(tg_id=int(tg_id), offer_type="trial_oto")
    if not offer:
        return None
    return {
        "id": int(offer.id),
        "offer_type": offer.offer_type,
        "plan_code": offer.plan_code,
        "price_stars": int(offer.price_stars or 0),
        "trigger_reason": offer.trigger_reason,
        "expires_at": _safe_iso(offer.expires_at),
        "status": offer.status,
    }


def _require_auth_user(x_telegram_init_data: str, request: Request | None = None) -> dict[str, Any]:
    user_data = _optional_auth_user(x_telegram_init_data, request=request)
    if user_data:
        return user_data
    raise HTTPException(status_code=401, detail="Telegram auth required")


def _require_user_access(*, target_tg_id: int, x_telegram_init_data: str, request: Request | None = None) -> dict[str, Any]:
    user_data = _require_auth_user(x_telegram_init_data, request=request)
    if int(user_data.get("id", 0)) != int(target_tg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    return user_data


def _require_admin(x_telegram_init_data: str, request: Request | None = None) -> dict[str, Any]:
    user_data = _require_auth_user(x_telegram_init_data, request=request)
    actor_id = int(user_data.get("id", 0))
    if not _is_admin_tg(actor_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_data


def _safe_public_url(value: str) -> str:
    return str(value or "").strip()


def _public_webapp_url() -> str:
    configured = _safe_public_url(getattr(Settings, "WEBAPP_URL", ""))
    if configured:
        return configured
    return "https://app.pokrov.space/"


def _public_checkout_url() -> str:
    configured = _safe_public_url(getattr(Settings, "PAY_CHECKOUT_URL", ""))
    if configured:
        try:
            parsed = urlparse(configured)
            cfg_host = (parsed.hostname or "").lower().strip()
            if cfg_host in {"portal-privacy.online", "www.portal-privacy.online"}:
                return "https://pay.pokrov.space/checkout/"
            if cfg_host and cfg_host != "pay.pokrov.space":
                return configured
        except Exception:
            return configured

    if _safe_public_url(getattr(Settings, "PAY_CHECKOUT_URL", "")):
        return configured
    return "https://pay.pokrov.space/checkout/"


def _checkout_runtime_issues() -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    if not RUB_CHECKOUT_ENABLED:
        issues.append(("checkout_disabled", "RUB checkout is disabled"))
    if not _checkout_secret():
        issues.append(("missing_checkout_ticket_secret", "CHECKOUT_TICKET_SECRET is empty"))
    checkout_url = _public_checkout_url()
    if not checkout_url:
        issues.append(("missing_checkout_url", "PAY_CHECKOUT_URL or PUBLIC_WEB_DOMAIN is not configured"))
    if not _safe_public_url(Settings.PUBLIC_API_BASE_URL):
        issues.append(("missing_public_api_base_url", "PUBLIC_API_BASE_URL is empty"))
    if not (_safe_public_url(Settings.PAY_SUCCESS_URL) or _safe_public_url(Settings.PUBLIC_API_BASE_URL)):
        issues.append(("missing_pay_success_url", "PAY_SUCCESS_URL is not configured"))
    if not (_safe_public_url(Settings.PAY_FAIL_URL) or _safe_public_url(Settings.PUBLIC_API_BASE_URL)):
        issues.append(("missing_pay_fail_url", "PAY_FAIL_URL is not configured"))
    enabled = enabled_rub_provider_codes()
    if not enabled:
        issues.append(("no_enabled_providers", "No RUB payment providers are configured"))
    return issues


def _checkout_runtime_errors() -> list[str]:
    return [detail for _code, detail in _checkout_runtime_issues()]


def _public_checkout_provider_state() -> RubProvidersOut:
    issues = _checkout_runtime_issues()
    blocked = bool(issues)
    rows = [] if blocked else [RubProviderChoiceOut(**row) for row in enabled_provider_catalog()]
    if not rows and not blocked:
        issues = [("no_enabled_providers", "No RUB payment providers are configured")]
        blocked = True
    return RubProvidersOut(
        ok=not blocked,
        providers=rows,
        blocked=blocked,
        blocked_reasons=[code for code, _detail in issues],
        blocked_reason_texts=[detail for _code, detail in issues],
        checkout_mode="account_session_first",
        telegram_fallback_available=True,
    )


def _ensure_checkout_runtime_ready() -> None:
    errors = _checkout_runtime_errors()
    if errors:
        raise HTTPException(status_code=503, detail="; ".join(errors))


def _payment_callback_base_url() -> str:
    return _safe_public_url(Settings.PUBLIC_API_BASE_URL) or f"https://{(Settings.PUBLIC_API_DOMAIN or Settings.HOST_DOMAIN or 'api.pokrov.space').strip().strip('/')}"


def _pay_success_url(provider: str = "") -> str:
    base = _safe_public_url(Settings.PAY_SUCCESS_URL) or f"{_payment_callback_base_url().rstrip('/')}/pay/success"
    provider_code = _normalize_provider(provider)
    if not provider_code:
        return base
    parsed = urlparse(base)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    q["provider"] = provider_code
    return parsed._replace(query=urlencode(q)).geturl()


def _pay_fail_url(provider: str = "") -> str:
    base = _safe_public_url(Settings.PAY_FAIL_URL) or f"{_payment_callback_base_url().rstrip('/')}/pay/fail"
    provider_code = _normalize_provider(provider)
    if not provider_code:
        return base
    parsed = urlparse(base)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    q["provider"] = provider_code
    return parsed._replace(query=urlencode(q)).geturl()


def _provider_result_url(provider: str) -> str:
    return f"{_payment_callback_base_url().rstrip('/')}/api/payments/result/{_normalize_provider(provider)}"


def _provider_refund_url(provider: str) -> str:
    return f"{_payment_callback_base_url().rstrip('/')}/api/payments/refund/{_normalize_provider(provider)}"


def _provider_chargeback_url(provider: str) -> str:
    return f"{_payment_callback_base_url().rstrip('/')}/api/payments/chargeback/{_normalize_provider(provider)}"


def _checkout_url_for_user(*, tg_id: int, plan_code: str = "", promo_code: str = "", campaign_key: str = "", source: str = "bot") -> str:
    base = _public_checkout_url() or "https://pay.pokrov.space/checkout/"
    parsed = urlparse(base)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    q["source"] = (source or "bot").strip().lower()
    q["tg_id"] = str(int(tg_id))
    if plan_code:
        q["plan"] = str(plan_code).strip().lower()[:32]
    promo = _sanitize_deeplink_token(promo_code, max_len=20, uppercase=True)
    campaign = _sanitize_deeplink_token(campaign_key, max_len=64, uppercase=False)
    if promo:
        q["promo"] = promo
    if campaign:
        q["campaign"] = campaign
    if _checkout_secret():
        ticket = _create_checkout_ticket(
            tg_id=int(tg_id),
            plan_code=str(plan_code or ""),
            promo_code=promo,
            campaign_key=campaign,
            source=q["source"],
        )
        if ticket:
            q["checkout_ticket"] = ticket
    built_query = urlencode(q)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/checkout/'}?{built_query}"
    return f"/checkout/?{built_query}"


def _normalize_provider(provider: str) -> str:
    normalized = _normalize_checkout_provider(provider)
    if normalized:
        return normalized
    return re.sub(r"[^a-z0-9_-]", "", str(provider or "").strip().lower())


def _provider_secret(provider: str) -> str:
    p = _normalize_provider(provider)
    key = p.upper()
    return (
        os.getenv(f"{key}_SIGNING_SECRET")
        or os.getenv(f"{key}_SECRET")
        or ""
    ).strip()


def _payload_value(payload: dict[str, Any], *keys: str) -> str:
    for k in keys:
        if k in payload:
            v = str(payload.get(k) or "").strip()
            if v:
                return v
    return ""


def _hmac_sha256_hex(secret: str, data: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), data, hashlib.sha256).hexdigest()


def _observer_signature_payload(*, node_code: str, timestamp: int, raw_body: bytes) -> bytes:
    raw_text = raw_body.decode("utf-8", errors="replace")
    return f"{str(node_code).strip().lower()}\n{int(timestamp)}\n{raw_text}".encode("utf-8")


def _verify_observer_push(*, s, node_code: str, timestamp: int, signature: str, raw_body: bytes) -> Node:
    code = str(node_code or "").strip().lower()
    if not code:
        raise HTTPException(status_code=401, detail="Missing node code")
    node = s.query(Node).filter(func.lower(Node.code) == code).first()
    if not node:
        raise HTTPException(status_code=401, detail="Unknown node")
    secret = str(getattr(node, "observer_push_secret", "") or "").strip()
    if not secret:
        raise HTTPException(status_code=401, detail="Observer push secret is not configured")
    now_ts = int(time.time())
    if abs(now_ts - int(timestamp)) > int(OBSERVER_PUSH_MAX_AGE_SECONDS):
        raise HTTPException(status_code=401, detail="Observer push timestamp is stale")
    expected = _hmac_sha256_hex(secret, _observer_signature_payload(node_code=code, timestamp=int(timestamp), raw_body=raw_body))
    if not hmac.compare_digest(expected, str(signature or "").strip().lower()):
        raise HTTPException(status_code=401, detail="Observer push signature is invalid")
    return node


async def _read_callback_payload(request: Request) -> tuple[dict[str, Any], bytes]:
    raw = await request.body()
    payload: dict[str, Any] = {}
    content_type = (request.headers.get("content-type") or "").lower()
    if "application/json" in content_type:
        try:
            payload = json.loads(raw.decode("utf-8", errors="replace"))
            if not isinstance(payload, dict):
                payload = {}
        except Exception:
            payload = {}
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        try:
            form = await request.form()
            payload = {str(k): str(v) for k, v in form.items()}
        except Exception:
            if "application/x-www-form-urlencoded" in content_type and raw:
                try:
                    payload = {str(k): str(v) for k, v in parse_qsl(raw.decode("utf-8", errors="replace"), keep_blank_values=True)}
                except Exception:
                    payload = {}
            else:
                payload = {}
    else:
        if raw:
            try:
                data = json.loads(raw.decode("utf-8", errors="replace"))
                if isinstance(data, dict):
                    payload = data
            except Exception:
                payload = {}

    for k, v in request.query_params.items():
        payload.setdefault(str(k), str(v))
    return payload, raw


def _verify_callback_signature(*, provider: str, payload: dict[str, Any], raw: bytes, request: Request) -> tuple[bool, str]:
    p = _normalize_provider(provider)
    # Freekassa SCI notify signature:
    # md5(MERCHANT_ID:AMOUNT:SECRET_WORD_2:MERCHANT_ORDER_ID)
    if p == "freekassa":
        merchant_id = _payload_value(payload, "MERCHANT_ID", "merchant_id", "shopId")
        amount = _payload_value(payload, "AMOUNT", "amount")
        order_id = _payload_value(payload, "MERCHANT_ORDER_ID", "merchant_order_id", "order_id")
        provided = _payload_value(payload, "SIGN", "sign", "signature")
        if merchant_id and amount and order_id and provided:
            shop = _fk_shop_by_merchant_id(merchant_id)
            secret2 = (shop.get("secret_word_2") or "").strip()
            if not secret2:
                return False, "missing_secret_word_2"
            expected = _fk_sci_signature(
                merchant_id=merchant_id,
                amount=amount,
                order_id=order_id,
                secret_word_2=secret2,
            )
            if hmac.compare_digest(str(provided).lower(), expected.lower()):
                return True, "ok"
            return False, "invalid_signature"
    if p in {"cardlink", "pally", "platima"}:
        return (True, "ok") if verify_provider_callback_signature(p, payload) else (False, "invalid_signature")

    secret = _provider_secret(provider)
    if not secret:
        return False, "missing_secret"

    provided = (
        _payload_value(
            {**payload, **{k.lower(): v for k, v in payload.items()}},
            "signature",
            "sign",
            "x-signature",
            "x-sign",
            "hash",
        )
        or _payload_value(
            {k.lower(): v for k, v in request.headers.items()},
            "x-signature",
            "x-sign",
            "signature",
            "x-signature-sha256",
        )
    )
    if not provided:
        return False, "missing_signature"

    expected_raw = _hmac_sha256_hex(secret, raw)
    if hmac.compare_digest(provided.lower(), expected_raw.lower()):
        return True, "ok"

    canonical_parts = []
    skip_keys = {"signature", "sign", "hash", "sig"}
    for k in sorted(payload.keys()):
        if k.lower() in skip_keys:
            continue
        canonical_parts.append(f"{k}={payload.get(k)}")
    canonical = "&".join(canonical_parts).encode("utf-8", errors="replace")
    expected_canonical = _hmac_sha256_hex(secret, canonical)
    if hmac.compare_digest(provided.lower(), expected_canonical.lower()):
        return True, "ok"
    return False, "invalid_signature"


def _callback_ids(provider: str, payload: dict[str, Any], raw: bytes) -> tuple[str, str]:
    p = _normalize_provider(provider)
    if p in {"cardlink", "pally", "platima"}:
        order_id, external_id = payment_callback_ids(p, payload)
        if order_id or external_id:
            return order_id, external_id or order_id or hashlib.sha256(raw or b"").hexdigest()[:40]
    order_id = _payload_value(
        payload,
        "order_id",
        "merchant_order_id",
        "MERCHANT_ORDER_ID",
        "invoice_id",
        "inv",
        "order",
    )
    external_id = _payload_value(
        payload,
        "external_tx_id",
        "transaction_id",
        "txn_id",
        "payment_id",
        "id",
        "intid",
        "inv_id",
        "operation_id",
    )
    if not external_id:
        external_id = order_id or hashlib.sha256(raw or b"").hexdigest()[:40]
    return order_id, external_id


def _safe_int(value: Any) -> int | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(str(value).strip())
    except Exception:
        return None


def _safe_float(value: Any) -> float:
    try:
        if value is None or str(value).strip() == "":
            return 0.0
        return float(str(value).strip().replace(",", "."))
    except Exception:
        return 0.0


def _status_from_event(event_type: str, payload: dict[str, Any], signature_ok: bool, provider: str = "") -> str:
    event = (event_type or "").strip().lower()
    if event == "refund":
        return "refunded"
    if event == "chargeback":
        return "chargeback"
    if _normalize_provider(provider) == "freekassa" and event == "result" and signature_ok:
        return "paid"
    provider_state = payment_callback_status(provider, payload)
    if provider_state in {"paid", "success", "succeeded", "approved", "completed"} and signature_ok:
        return "paid"
    if provider_state in {"failed", "fail", "cancelled", "canceled", "rejected", "declined"}:
        return "failed"
    status_raw = _payload_value(payload, "status", "payment_status", "state").lower()
    if status_raw in {"paid", "success", "succeeded", "approved"} and signature_ok:
        return "paid"
    return "pending_verification" if not signature_ok else "processing"


def _upsert_external_order(
    s,
    *,
    provider: str,
    order_id: str,
    payload: dict[str, Any],
    status: str,
    mark_paid: bool,
) -> None:
    if not order_id:
        return
    row = (
        s.query(ExternalOrder)
        .filter(ExternalOrder.provider == provider, ExternalOrder.order_id == order_id)
        .first()
    )
    if not row:
        row = ExternalOrder(provider=provider, order_id=order_id, created_at=_utcnow())
        s.add(row)
    row.tg_id = _safe_int(_payload_value(payload, "tg_id", "telegram_id", "user_id", "us_tg_id")) or row.tg_id
    row.plan_code = _payload_value(payload, "plan_code", "tariff", "plan", "us_plan_code")
    row.source = _payload_value(payload, "source", "checkout_source", "us_source")
    row.campaign = _payload_value(payload, "campaign", "utm_campaign")
    row.promo_code = _payload_value(payload, "promo_code", "coupon")
    row.meta_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))[:4000]
    row.amount = _safe_float(_payload_value(payload, "amount", "sum", "amount_paid", "OutSum"))
    row.currency = _payload_value(payload, "currency", "cur", "ccy") or "RUB"
    row.status = status
    if mark_paid and not row.paid_at:
        row.paid_at = _utcnow()


def _record_external_payment_event(
    *,
    provider: str,
    event_type: str,
    external_id: str,
    order_id: str,
    payload: dict[str, Any],
    signature_ok: bool,
    processed_ok: bool,
) -> tuple[bool, bool]:
    s = SessionLocal()
    try:
        exists = (
            s.query(ExternalPaymentEvent)
            .filter(
                ExternalPaymentEvent.provider == provider,
                ExternalPaymentEvent.event_type == event_type,
                ExternalPaymentEvent.external_id == external_id,
            )
            .first()
        )
        if exists:
            if bool(getattr(exists, "signature_ok", False)):
                return True, True
            if not signature_ok:
                return True, True
            exists.order_id = order_id or None
            exists.payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))[:16000]
            exists.signature_ok = True
            exists.processed_ok = bool(processed_ok)
            status = _status_from_event(event_type, payload, signature_ok=True, provider=provider)
            _upsert_external_order(
                s,
                provider=provider,
                order_id=order_id,
                payload=payload,
                status=status,
                mark_paid=status == "paid",
            )
            s.commit()
            return False, True

        event = ExternalPaymentEvent(
            provider=provider,
            event_type=event_type,
            external_id=external_id,
            order_id=order_id or None,
            payload_json=json.dumps(payload, ensure_ascii=False, separators=(",", ":"))[:16000],
            signature_ok=bool(signature_ok),
            processed_ok=bool(processed_ok),
            created_at=_utcnow(),
        )
        s.add(event)

        status = _status_from_event(event_type, payload, signature_ok=signature_ok, provider=provider)
        _upsert_external_order(
            s,
            provider=provider,
            order_id=order_id,
            payload=payload,
            status=status,
            mark_paid=status == "paid",
        )
        s.commit()
        return False, True
    except Exception as exc:
        s.rollback()
        logger.exception("payment callback persistence failed: provider=%s event=%s err=%s", provider, event_type, exc)
        return False, False
    finally:
        s.close()


def _payment_page_html(*, title: str, message: str, action_url: str, action_label: str) -> str:
    return (
        "<!doctype html><html lang='ru'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{title}</title>"
        "<style>body{font-family:system-ui,sans-serif;background:#0f1115;color:#f5f7fa;padding:32px}"
        ".card{max-width:640px;margin:0 auto;background:#171a21;border:1px solid #2a3342;border-radius:14px;padding:24px}"
        "a{display:inline-block;margin-top:14px;color:#0f1115;background:#7dd3fc;padding:10px 14px;border-radius:10px;text-decoration:none;font-weight:600}"
        "p{line-height:1.5;color:#d6dbe4}</style></head><body>"
        f"<div class='card'><h1>{title}</h1><p>{message}</p><a href='{action_url}'>{action_label}</a></div></body></html>"
    )


def _rub_plan_days(plan_code: str) -> int:
    s = SessionLocal()
    try:
        row = _resolve_plan_config(s=s, code=(plan_code or "").strip().lower())
        if row:
            return max(1, int(row.get("days") or 30))
    finally:
        s.close()
    fallback = RUB_PLAN_PRICES.get((plan_code or "").strip().lower())
    if not fallback:
        return 30
    return max(1, int(fallback.get("days") or 30))


def _apply_external_paid_order(*, provider: str, order_id: str, payload: dict[str, Any]) -> tuple[bool, str]:
    s = SessionLocal()
    try:
        ext_order = None
        if order_id:
            ext_order = (
                s.query(ExternalOrder)
                .filter(ExternalOrder.provider == str(provider), ExternalOrder.order_id == str(order_id))
                .first()
            )
        tg_id = _safe_int(_payload_value(payload, "tg_id", "telegram_id", "user_id", "us_tg_id"))
        if tg_id is None and ext_order and ext_order.tg_id is not None:
            tg_id = int(ext_order.tg_id)
        if tg_id is None:
            return False, "missing_tg_id"

        plan_code = _payload_value(payload, "plan_code", "tariff", "plan", "us_plan_code")
        if not plan_code and ext_order and ext_order.plan_code:
            plan_code = str(ext_order.plan_code)
        plan_code = (plan_code or "1_month").strip().lower()
        plan_cfg = _resolve_plan_config(s=s, code=plan_code)
        if not plan_cfg:
            plan_code = "1_month"
        days = _rub_plan_days(plan_code)

        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            s.rollback()
            _ensure_user_row_for_login(tg_id=int(tg_id), username=None)
            user = s.query(User).filter(User.tg_id == int(tg_id)).first()
            if not user:
                return False, "user_create_failed"

        now = _utcnow()
        old_sub = (user.sub_type or "").upper().strip()
        first_paid_purchase = not bool(getattr(user, "first_purchase_done", False))
        referrer_id = int(getattr(user, "referrer_id", 0) or 0)
        plan_amount_stars = int(plan_cfg.get("amount_stars") or API_PLAN_PRICES.get(plan_code) or 0)
        if old_sub == "FREE":
            start_from = now
        else:
            start_from = user.expiry_at if user.expiry_at and user.expiry_at > now else now
        user.expiry_at = start_from + timedelta(days=days)
        user.sub_type = "PAID"
        user.current_plan_code = plan_code
        user.is_active = True
        user.first_purchase_done = True
        user.pending_discount_pct = None
        user.pending_discount_code = None
        user.pending_discount_set_at = None

        # Anti-fraud referral flow:
        # queue inviter reward and release it after the confirmation window + activity signal.
        if first_paid_purchase and referrer_id > 0:
            _queue_referral_bonus(
                s=s,
                order_id=str(order_id or f"{provider}:{int(tg_id)}:{int(now.timestamp())}"),
                referrer_tg_id=int(referrer_id),
                referred_tg_id=int(tg_id),
                now=now,
            )

        if ext_order:
            ext_order.status = "paid"
            ext_order.paid_at = ext_order.paid_at or now
            ext_order.tg_id = ext_order.tg_id or int(tg_id)
            ext_order.plan_code = plan_code
            ext_order_id = int(ext_order.id) if getattr(ext_order, "id", None) is not None else None
        else:
            ext_order_id = None
        s.commit()
        s.refresh(user)
    except Exception as exc:
        s.rollback()
        logger.exception("external order activation failed: order_id=%s err=%s", order_id, exc)
        return False, "db_error"
    finally:
        s.close()

    if first_paid_purchase and referrer_id > 0 and plan_amount_stars > 0:
        try:
            award_referral_points(
                tg_id=int(referrer_id),
                paid_stars=int(plan_amount_stars),
                ref_tg_id=int(tg_id),
                pay_attempt_id=ext_order_id,
            )
        except Exception as exc:
            logger.warning(
                "referral points award failed for provider=%s order_id=%s referrer=%s referred=%s err=%s",
                provider,
                order_id,
                referrer_id,
                tg_id,
                exc,
            )

    return True, "ok"


async def _handle_payment_callback(*, provider: str, event_type: str, request: Request) -> dict[str, Any]:
    p = _normalize_provider(provider)
    et = re.sub(r"[^a-z_]", "", str(event_type or "").strip().lower())
    if p not in PAYMENT_PROVIDER_WHITELIST:
        raise HTTPException(status_code=404, detail="Unsupported provider")
    if et not in {"result", "refund", "chargeback"}:
        raise HTTPException(status_code=400, detail="Unsupported event type")

    payload, raw = await _read_callback_payload(request)
    if p == "freekassa":
        client_ip = _fk_client_ip(request)
        if not _is_ip_allowed(client_ip, FK_NOTIFY_IP_ALLOWLIST):
            logger.warning("freekassa callback blocked by ip allowlist: ip=%s", client_ip)
            raise HTTPException(status_code=403, detail="Callback IP is not allowed")
    order_id, external_id = _callback_ids(p, payload, raw)
    signature_ok, signature_reason = _verify_callback_signature(provider=p, payload=payload, raw=raw, request=request)
    processed_ok = bool(signature_ok)
    duplicate, persist_ok = _record_external_payment_event(
        provider=p,
        event_type=et,
        external_id=external_id,
        order_id=order_id,
        payload=payload,
        signature_ok=signature_ok,
        processed_ok=processed_ok,
    )

    if not signature_ok:
        logger.warning(
            "payment callback signature invalid: provider=%s event=%s reason=%s order_id=%s external_id=%s",
            p,
            et,
            signature_reason,
            order_id,
            external_id,
        )
        if not PAYMENT_CALLBACK_TOLERANT_MODE:
            raise HTTPException(status_code=400, detail=f"Invalid signature: {signature_reason}")

    activated = False
    activation_reason = ""
    sync_ok = None
    if (not duplicate) and signature_ok and et == "result":
        activated, activation_reason = _apply_external_paid_order(provider=p, order_id=order_id, payload=payload)
        if activated:
            tg_id = _safe_int(_payload_value(payload, "tg_id", "telegram_id", "user_id"))
            if tg_id is not None:
                try:
                    sync_ok = bool(await _sync_user_after_paid_purchase(int(tg_id)))
                except Exception:
                    sync_ok = False

    return {
        "ok": bool(signature_ok and persist_ok),
        "provider": p,
        "event_type": et,
        "order_id": order_id or None,
        "external_id": external_id,
        "signature_ok": bool(signature_ok),
        "duplicate": bool(duplicate),
        "activated": bool(activated),
        "activation_reason": activation_reason or None,
        "sync_ok": sync_ok,
    }


def _parse_freekassa_payment_url(body: dict[str, Any], fallback_order_id: str) -> str:
    if not isinstance(body, dict):
        return ""
    for key in ("location", "paymentUrl", "url", "redirect_url"):
        val = body.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    data = body.get("data")
    if isinstance(data, dict):
        for key in ("location", "paymentUrl", "url", "redirect_url"):
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    shop = _fk_shop_by_source("site")
    shop_id = str(shop.get("shop_id") or "")
    if shop_id and fallback_order_id:
        return f"{_freekassa_payment_base_url()}/?m={shop_id}&oa=0&o={fallback_order_id}"
    return ""


def _parse_freekassa_payment_url(body: dict[str, Any], fallback_order_id: str, source: str = "site") -> str:
    if not isinstance(body, dict):
        return ""
    for key in ("location", "paymentUrl", "url", "redirect_url"):
        val = body.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    data = body.get("data")
    if isinstance(data, dict):
        for key in ("location", "paymentUrl", "url", "redirect_url"):
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    shop = _fk_shop_by_source(source or "site")
    shop_id = str(shop.get("shop_id") or "")
    if shop_id and fallback_order_id:
        return f"{_freekassa_payment_base_url()}/?m={shop_id}&oa=0&o={fallback_order_id}"
    return ""


async def _freekassa_api_request(*, source: str, method: str, data: dict[str, Any]) -> dict[str, Any]:
    shop = _fk_shop_by_source(source)
    shop_id = str(shop.get("shop_id") or "").strip()
    api_key = str(shop.get("api_key") or "").strip()
    if not shop_id or not api_key:
        raise HTTPException(status_code=500, detail="Freekassa shop is not configured")

    nonce = int(time.time() * 1000)
    payload = {"shopId": shop_id, "nonce": nonce}
    for key, value in dict(data or {}).items():
        payload[str(key)] = value
    signature = _fk_api_signature(api_key=api_key, payload=payload)
    payload["signature"] = signature
    fk_base = (getattr(Settings, "FK_API_BASE_URL", "") or os.getenv("FK_API_BASE_URL") or "https://api.fk.life/v1").strip().rstrip("/")
    url = f"{fk_base}/{method.strip('/')}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Sign": signature,
        "Signature": signature,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            timeout=aiohttp.ClientTimeout(total=25),
        ) as resp:
            txt = await resp.text()
            try:
                body = json.loads(txt) if txt else {}
            except Exception:
                body = {"raw": txt}
            if resp.status >= 400:
                logger.error(
                    "freekassa api error source=%s method=%s status=%s body=%s",
                    source,
                    method,
                    resp.status,
                    str(txt or "")[:600],
                )
                raise HTTPException(status_code=502, detail=f"Freekassa API error: {resp.status}")
            return body if isinstance(body, dict) else {"data": body}


async def _telegram_send_message(chat_id: int, text: str) -> bool:
    token = _current_bot_token()
    if not token:
        return False
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": int(chat_id), "text": text}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return False
                body = await resp.json()
                return bool(body.get("ok"))
    except Exception:
        return False


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
                if "free" in (getattr(n, "code", "") or "").lower()
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


async def _sync_user_after_paid_purchase(tg_id: int) -> bool:
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            return False
        return await _sync_user_after_paid_bonus(user)
    finally:
        s.close()


def _ticket_status_title(status: str) -> str:
    st = (status or "").lower().strip()
    if st == STATUS_OPEN:
        return "Открыт"
    if st == STATUS_IN_PROGRESS:
        return "В работе"
    if st == STATUS_CLOSED:
        return "Закрыт"
    return st or "Неизвестно"


def _ticket_message_row(msg) -> dict[str, Any]:
    return {
        "id": msg.id,
        "ticket_id": msg.ticket_id,
        "sender_tg_id": msg.sender_tg_id,
        "sender_role": msg.sender_role,
        "body": msg.body,
        "media_type": getattr(msg, "media_type", None),
        "media_file_id": getattr(msg, "media_file_id", None),
        "media_payload": getattr(msg, "media_payload", None),
        "created_at": _safe_iso(msg.created_at),
    }


def _ticket_row(ticket, messages: list | None = None) -> dict[str, Any]:
    rows = messages if messages is not None else []
    last_message = rows[-1] if rows else None
    return {
        "id": ticket.id,
        "user_tg_id": ticket.user_tg_id,
        "status": ticket.status,
        "status_title": _ticket_status_title(ticket.status),
        "subject": ticket.subject,
        "assigned_admin_tg_id": ticket.assigned_admin_tg_id,
        "created_at": _safe_iso(ticket.created_at),
        "updated_at": _safe_iso(ticket.updated_at),
        "closed_at": _safe_iso(ticket.closed_at),
        "messages": [_ticket_message_row(m) for m in rows],
        "last_message_preview": ((last_message.body or "").strip()[:200] if last_message else ""),
    }


def _audit_admin(*, actor_tg_id: int, action: str, target_tg_id: int | None = None, meta: dict[str, Any] | None = None) -> None:
    s = SessionLocal()
    try:
        row = AdminAudit(
            actor_tg_id=int(actor_tg_id),
            action=(action or "").strip()[:64],
            target_tg_id=int(target_tg_id) if target_tg_id is not None else None,
            meta=json.dumps(meta or {}, ensure_ascii=False, separators=(",", ":"))[:2000],
        )
        s.add(row)
        s.commit()
    except Exception:
        s.rollback()
    finally:
        s.close()


def _sanitize_ticket_upload_name(filename: str | None) -> str:
    raw = Path(str(filename or "").strip()).name
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "_", raw).strip(" ._")
    return cleaned[:120] or "attachment"


def _ticket_upload_kind(content_type: str) -> str:
    normalized = str(content_type or "").split(";", 1)[0].strip().lower()
    if normalized.startswith("image/"):
        return "image"
    if normalized.startswith("video/"):
        return "video"
    if normalized in {"application/pdf", "text/plain", "application/octet-stream"}:
        return "file"
    raise HTTPException(status_code=400, detail="Unsupported attachment type")


def _ticket_upload_suffix(filename: str, content_type: str) -> str:
    suffix = Path(filename).suffix.lower().strip()
    if suffix and re.fullmatch(r"\.[a-z0-9]{1,10}", suffix):
        return suffix
    guessed = mimetypes.guess_extension(content_type or "") or ""
    if guessed and re.fullmatch(r"\.[a-z0-9]{1,10}", guessed.lower()):
        return guessed.lower()
    return ".bin"


def _store_support_upload(*, filename: str | None, content_type: str | None, raw_bytes: bytes) -> dict[str, Any]:
    original_name = _sanitize_ticket_upload_name(filename)
    content_type = str(content_type or "application/octet-stream").split(";", 1)[0].strip().lower()
    media_type = _ticket_upload_kind(content_type)
    suffix = _ticket_upload_suffix(original_name, content_type)
    stored_name = f"{_utcnow().strftime('%Y%m%d')}-{secrets.token_urlsafe(12).replace('-', '').replace('_', '')}{suffix}"
    stored_path = SUPPORT_UPLOAD_DIR / stored_name

    total_size = len(raw_bytes or b"")
    if total_size <= 0:
        raise HTTPException(status_code=400, detail="Attachment is empty")
    if total_size > SUPPORT_UPLOAD_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Attachment is too large")

    try:
        stored_path.write_bytes(raw_bytes)
    except Exception:
        stored_path.unlink(missing_ok=True)
        raise

    file_url = f"{SUPPORT_UPLOAD_URL_PREFIX.rstrip('/')}/{stored_name}"
    payload = {
        "url": file_url,
        "name": original_name,
        "content_type": content_type,
        "size": int(total_size),
    }
    attachment = {
        "media_type": media_type,
        "media_file_id": f"support/{stored_name}",
        "media_payload": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    }
    return {"attachment": attachment, "attachment_payload": payload}


def _json_obj(raw: str | None) -> dict[str, Any]:
    obj = _safe_json_loads(raw, {})
    return obj if isinstance(obj, dict) else {}


def _normalize_retention_flow(raw_flow: str | None) -> str:
    flow = str(raw_flow or "").strip().lower()
    if not flow:
        return ""
    if flow.startswith("welcome"):
        return "welcome"
    if flow in {"t3", "t1", "t0"}:
        return flow
    if flow.startswith("expiry_chain:"):
        tail = flow.split(":", 1)[1].strip().lower()
        if tail in {"t3", "t1", "t0"}:
            return tail
    if flow.startswith("reactivation"):
        return "reactivation"
    if flow.startswith("start99"):
        return "start99_offer"
    return ""


def _key_history_log(
    *,
    tg_id: int,
    action: str,
    node_code: str | None = None,
    actor_tg_id: int | None = None,
    source: str = "admin",
    meta: dict[str, Any] | None = None,
) -> None:
    s = SessionLocal()
    try:
        row = KeyActionHistory(
            tg_id=int(tg_id),
            node_code=(str(node_code or "").strip().lower() or None),
            action=str(action or "").strip()[:64],
            actor_tg_id=(int(actor_tg_id) if actor_tg_id is not None else None),
            source=str(source or "admin").strip()[:32] or "admin",
            meta=json.dumps(meta or {}, ensure_ascii=False, separators=(",", ":")),
            created_at=_utcnow(),
        )
        s.add(row)
        s.commit()
    except Exception:
        s.rollback()
    finally:
        s.close()


def _user_segment_value(user: User) -> str:
    if bool(getattr(user, "is_manual", False) or int(user.tg_id) < 0 or str(user.sub_type or "").upper() == "MANUAL"):
        return "manual"
    if str(user.sub_type or "").upper() == "FREE":
        return "free"
    if str(user.sub_type or "").upper() == "PAID":
        return "paid"
    return "other"


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


def _campaign_lookup(
    *,
    s,
    campaign_type: str,
    target_value: str,
    user: User,
    now: datetime | None = None,
) -> IncentiveCampaign | None:
    now_dt = now or _utcnow()
    ctype = str(campaign_type or "").strip().lower()
    target = str(target_value or "").strip().upper()
    if ctype not in {"promo", "gift"} or not target:
        return None
    rows = (
        s.query(IncentiveCampaign)
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


def _campaign_consume(*, s, row: IncentiveCampaign | None) -> None:
    if not row:
        return
    row.activations_count = int(row.activations_count or 0) + 1
    if bool(row.auto_disable) and int(row.max_activations or -1) >= 0 and int(row.activations_count or 0) >= int(row.max_activations or -1):
        row.is_active = False
    row.updated_at = _utcnow()


def _get_user_node_hard_cap_gb(*, s, tg_id: int, node_code: str) -> int | None:
    code = str(node_code or "").strip().lower()
    if not code:
        return None
    row = (
        s.query(UserKeyPolicy)
        .filter(UserKeyPolicy.tg_id == int(tg_id), func.lower(UserKeyPolicy.node_code) == code)
        .first()
    )
    if not row:
        return None
    val = row.hard_cap_gb
    return int(val) if val is not None else None


def _serialize_key_policy(row: UserKeyPolicy) -> dict[str, Any]:
    return {
        "node_code": str(row.node_code or "").strip().lower(),
        "burst_mbps": int(row.burst_mbps) if row.burst_mbps is not None else None,
        "soft_cap_gb": int(row.soft_cap_gb) if row.soft_cap_gb is not None else None,
        "hard_cap_gb": int(row.hard_cap_gb) if row.hard_cap_gb is not None else None,
        "notify_soft": bool(row.notify_soft),
        "notify_hard": bool(row.notify_hard),
        "auto_disable_on_hard": bool(row.auto_disable_on_hard),
        "updated_by": int(row.updated_by) if row.updated_by is not None else None,
        "updated_at": _safe_iso(row.updated_at),
    }


def _normalized_loyalty_config(payload: dict[str, Any] | None) -> dict[str, Any]:
    src = dict(payload or {})
    enabled = bool(src.get("enabled", True))
    tiers_raw = src.get("tiers")
    if not isinstance(tiers_raw, list) or not tiers_raw:
        tiers_raw = list(DEFAULT_LOYALTY_CONFIG["tiers"])
    tiers: list[dict[str, Any]] = []
    seen_days: set[int] = set()
    for row in tiers_raw:
        if not isinstance(row, dict):
            continue
        days = max(1, min(3650, int(row.get("days") or 0)))
        bonus_days = max(1, min(3650, int(row.get("bonus_days") or 0)))
        perk = str(row.get("perk") or f"tier_{days}").strip()[:64] or f"tier_{days}"
        if days in seen_days:
            continue
        seen_days.add(days)
        tiers.append({"days": days, "bonus_days": bonus_days, "perk": perk})
    tiers.sort(key=lambda x: int(x["days"]))
    if not tiers:
        tiers = list(DEFAULT_LOYALTY_CONFIG["tiers"])
    return {"enabled": enabled, "tiers": tiers}


def _loyalty_config(*, s) -> dict[str, Any]:
    raw = _get_app_setting_json(s=s, key="loyalty_config", default=DEFAULT_LOYALTY_CONFIG)
    return _normalized_loyalty_config(raw if isinstance(raw, dict) else DEFAULT_LOYALTY_CONFIG)


def _user_loyalty_snapshot(*, s, user: User) -> dict[str, Any]:
    cfg = _loyalty_config(s=s)
    now = _utcnow()
    anchor = user.created_at or now
    streak_days = max(0, int((now - anchor).total_seconds() // 86400))
    claims = (
        s.query(RewardClaim)
        .filter(RewardClaim.tg_id == int(user.tg_id), RewardClaim.reward_key.like("loyalty_%"))
        .all()
    )
    claim_keys = {str(c.reward_key or "") for c in claims}
    tiers_payload: list[dict[str, Any]] = []
    for row in cfg.get("tiers", []):
        days = int(row.get("days") or 0)
        key = f"loyalty_{days}"
        tiers_payload.append(
            {
                "days": days,
                "bonus_days": int(row.get("bonus_days") or 0),
                "perk": str(row.get("perk") or ""),
                "unlocked": streak_days >= days,
                "claimed": key in claim_keys,
                "reward_key": key,
            }
        )
    return {
        "enabled": bool(cfg.get("enabled", True)),
        "streak_days": streak_days,
        "tiers": tiers_payload,
    }


def _extract_event_ip(meta_json: str | None) -> str:
    meta = _json_obj(meta_json)
    for key in ("ip", "client_ip", "remote_ip"):
        raw = str(meta.get(key) or "").strip()
        if raw:
            return raw
    return ""


def _compute_user_risk(*, s, user: User, keys_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    now = _utcnow()
    since = now - timedelta(days=30)
    tg_id = int(user.tg_id)
    regen_count = int(
        s.query(func.count(AdminAudit.id))
        .filter(AdminAudit.target_tg_id == tg_id, AdminAudit.action.in_(["admin_manual_regen_token", "admin_operator_rotate_link"]))
        .filter(AdminAudit.created_at >= since)
        .scalar()
        or 0
    )
    disable_count = int(
        s.query(func.count(AdminAudit.id))
        .filter(AdminAudit.target_tg_id == tg_id, AdminAudit.action.in_(["admin_user_key_toggle", "admin_bulk_key_action"]))
        .filter(AdminAudit.created_at >= since)
        .scalar()
        or 0
    )
    event_rows = s.query(Event.meta_json).filter(Event.tg_id == tg_id, Event.created_at >= since).all()
    unique_ips = {ip for ip in (_extract_event_ip(getattr(r, "meta_json", None)) for r in event_rows) if ip}
    ip_count = int(len(unique_ips))
    mismatch_count = int((keys_summary or {}).get("subid_mismatch_count", 0) or 0)
    traffic_gb = float((keys_summary or {}).get("traffic_total_gb", 0.0) or 0.0)
    observer_state_row = s.query(ObserverUserState).filter(ObserverUserState.tg_id == tg_id).first()
    observer_state = str(getattr(observer_state_row, "state", "") or "ok").strip().lower() or "ok"

    score = 0
    factors: list[dict[str, Any]] = []
    if regen_count > 0:
        val = min(30, regen_count * 10)
        score += val
        factors.append({"key": "regen", "weight": val, "value": regen_count})
    if disable_count > 0:
        val = min(20, disable_count * 3)
        score += val
        factors.append({"key": "admin_key_ops", "weight": val, "value": disable_count})
    if ip_count > 3:
        val = min(25, (ip_count - 3) * 5)
        score += val
        factors.append({"key": "multi_ip", "weight": val, "value": ip_count})
    if mismatch_count > 0:
        val = min(20, mismatch_count * 7)
        score += val
        factors.append({"key": "subid_mismatch", "weight": val, "value": mismatch_count})
    if observer_state == "watch":
        score += 15
        factors.append({"key": "observer_watch", "weight": 15, "value": observer_state})
    elif observer_state == "suspicious":
        score += 40
        factors.append({"key": "observer_suspicious", "weight": 40, "value": observer_state})
    if str(user.sub_type or "").upper() == "FREE" and traffic_gb > float(FREE_TOTAL_GB) * 1.2:
        val = min(25, int((traffic_gb / max(1.0, float(FREE_TOTAL_GB))) * 8))
        score += val
        factors.append({"key": "anomalous_traffic", "weight": val, "value": round(traffic_gb, 2)})
    score = max(0, min(100, int(score)))
    level = "low" if score < 30 else ("medium" if score < 60 else ("high" if score < 80 else "critical"))
    return {
        "score": score,
        "level": level,
        "window_days": 30,
        "signals": {
            "regen_count": regen_count,
            "admin_key_ops": disable_count,
            "unique_ips": ip_count,
            "observer_state": observer_state,
            "traffic_gb": round(traffic_gb, 3),
            "subid_mismatch_count": mismatch_count,
        },
        "factors": factors,
        "updated_at": _safe_iso(now),
    }


def _queue_referral_bonus(
    *,
    s,
    order_id: str,
    referrer_tg_id: int,
    referred_tg_id: int,
    now: datetime,
) -> bool:
    if int(referrer_tg_id) <= 0 or int(referred_tg_id) <= 0 or not str(order_id or "").strip():
        return False
    exists = (
        s.query(ReferralBonusQueue.id)
        .filter(
            ReferralBonusQueue.order_id == str(order_id),
            ReferralBonusQueue.referrer_tg_id == int(referrer_tg_id),
            ReferralBonusQueue.referred_tg_id == int(referred_tg_id),
        )
        .first()
    )
    if exists:
        return True
    referrer = s.query(User).filter(User.tg_id == int(referrer_tg_id)).first()
    if referrer:
        # Backward-compatible behavior: referral count is visible right after
        # successful first paid purchase, while bonus days are deferred by anti-fraud queue.
        referrer.referral_count = int(referrer.referral_count or 0) + 1
    ready_at = now + timedelta(hours=int(REFERRAL_ANTIFRAUD_HOURS))
    s.add(
        ReferralBonusQueue(
            order_id=str(order_id),
            referrer_tg_id=int(referrer_tg_id),
            referred_tg_id=int(referred_tg_id),
            queued_at=now,
            ready_at=ready_at,
            status="pending",
            meta=json.dumps({"source": "payment_callback", "counted": True}, ensure_ascii=False, separators=(",", ":")),
        )
    )
    return True


def _process_referral_bonus_queue(*, limit: int = 100, force_without_activity: bool = False) -> dict[str, int]:
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
            if (not has_activity) and (not force_without_activity):
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

            row_meta = _json_obj(getattr(row, "meta", None))
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


_diag_rate_limit: dict[int, float] = {}
EVENT_WHITELIST = {
    "opened_webapp",
    "copied_key",
    "clicked_connect",
    "clicked_pay",
    "pay_started",
    "paid",
    "connected_ok",
    "connect_failed",
    "auth_handoff_started",
    "config_opened",
    "config_import_attempted",
    "config_import_failed",
    "reconnect_loop_detected",
    "renewed",
    "ticket_created",
    "expired",
    "deep_link_opened",
    "copy_used",
}


def _node_country_name(code: str) -> str:
    raw = (code or "").strip().lower()
    if "free" in raw:
        return "NL Free"
    base = _node_code_base(code)
    names = {
        "pl": "Poland",
        "it": "Italy",
        "us": "USA",
        "nl": "Netherlands",
        "de": "Germany",
        "brain": "Germany",
    }
    return names.get(base, base.upper() if base else "Node")


def _safe_ping(node) -> int | None:
    val = getattr(node, "panel_latency_ms", None)
    if isinstance(val, int):
        return val
    try:
        return int(val) if val is not None else None
    except Exception:
        return None


def _generate_sub_token() -> str:
    return secrets.token_urlsafe(32)


def _next_manual_tg_id(s) -> int:
    min_id = s.query(func.min(User.tg_id)).filter(User.tg_id < 0).scalar()
    if min_id is None:
        return -10001
    return int(min_id) - 1


async def _get_panel_usage_legacy(tg_id: int) -> dict | None:
    """
    Optional: get usage from the legacy panel only.
    Multi-node usage is intentionally not queried by default (too expensive/noisy).
    """
    if not API_ENABLE_USAGE:
        return None
    if not Settings.PANEL_PATH:
        return None

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
                    return None
                cookies = login_resp.cookies

            async with session.get(
                f"{base}/{path}/panel/api/inbounds/list",
                cookies=cookies,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as list_resp:
                if list_resp.status != 200:
                    return None
                data = await list_resp.json()
                if not data.get("success"):
                    return None
                for inb in data.get("obj", []):
                    if inb.get("id") != Settings.INBOUND_ID:
                        continue
                    settings = json.loads(inb.get("settings", "{}"))
                    for client in settings.get("clients", []):
                        if str(client.get("tgId", "")).strip() == str(tg_id).strip():
                            email = client.get("email", "")
                            up = 0
                            down = 0
                            for stat in inb.get("clientStats", []) or []:
                                if stat.get("email") == email:
                                    up = stat.get("up", 0)
                                    down = stat.get("down", 0)
                                    break
                            return {"email": email, "used_bytes": up + down, "enable": client.get("enable", True)}
    except Exception:
        return None
    return None


async def _get_user_runtime_summary(*, s, user: User, nodes: list[Node] | None = None) -> dict[str, Any]:
    allowed_nodes = list(nodes or [])
    node_codes = [str(getattr(node, "code", "") or "").strip() for node in allowed_nodes if str(getattr(node, "code", "") or "").strip()]
    fallback = {
        "panel_state": "ok",
        "panel_error": None,
        "known_nodes": 0,
        "active_nodes": 0,
        "enabled_nodes": 0,
        "active_connections": 0,
        "active_connections_source": "none",
        "active_users_estimate": 0,
        "active_users_source": "none",
        "traffic_up_bytes": 0,
        "traffic_down_bytes": 0,
        "traffic_total_bytes": 0,
        "last_online_at": None,
        "last_online_age_seconds": None,
        "status": "unknown",
    }
    if not node_codes:
        return fallback

    panel_rows: list[dict[str, Any]] = []
    panel_error = ""
    panel = ControlPanel()
    try:
        await panel.login()
        panel_rows = await panel.get_user_key_snapshots(tg_id=int(user.tg_id), node_codes=node_codes)
    except Exception as exc:
        panel_error = str(exc)[:200]
    finally:
        try:
            await panel.close()
        except Exception:
            pass

    if panel_error:
        return {**fallback, "panel_state": "error", "panel_error": panel_error}

    known_nodes = 0
    active_nodes = 0
    enabled_nodes = 0
    total_up = 0
    total_down = 0
    active_connections = 0
    saw_ip_count = False
    last_online_at = None
    last_online_age_seconds = None

    for row in panel_rows or []:
        client = row.get("client") or {}
        runtime = row.get("runtime") or {}
        if client:
            known_nodes += 1
        if not isinstance(runtime, dict):
            continue
        if bool(runtime.get("enable", client.get("enable", False))):
            enabled_nodes += 1
        if runtime.get("online") is True:
            active_nodes += 1
        up = int(runtime.get("up", 0) or 0)
        down = int(runtime.get("down", 0) or 0)
        total_up += up
        total_down += down
        ip_count_raw = runtime.get("ip_count")
        if ip_count_raw is not None:
            try:
                active_connections += max(0, int(ip_count_raw))
                saw_ip_count = True
            except Exception:
                pass
        age_raw = runtime.get("last_online_age_seconds")
        iso_raw = str(runtime.get("last_online_at") or "").strip() or None
        if age_raw is None or not iso_raw:
            continue
        try:
            age_value = max(0, int(age_raw))
        except Exception:
            continue
        if last_online_age_seconds is None or age_value < int(last_online_age_seconds):
            last_online_age_seconds = age_value
            last_online_at = iso_raw

    if not saw_ip_count:
        active_connections = int(active_nodes)
        active_connections_source = "online_nodes" if known_nodes else "none"
    else:
        active_connections_source = "panel_ip_count"

    observer_row = s.query(ObserverUserState).filter(ObserverUserState.tg_id == int(user.tg_id)).first()
    observed_ip_count_24h = int(getattr(observer_row, "observed_ip_count_24h", 0) or 0)
    active_users_estimate, active_users_source = _estimate_active_users_proxy(
        live_connections=active_connections,
        live_nodes=active_nodes,
        saw_ip_count=saw_ip_count,
        observed_ip_count_24h=observed_ip_count_24h,
    )

    if active_nodes > 0:
        status = "online"
    elif known_nodes > 0:
        status = "offline"
    else:
        status = "unknown"

    return {
        "panel_state": "ok",
        "panel_error": None,
        "known_nodes": int(known_nodes),
        "active_nodes": int(active_nodes),
        "enabled_nodes": int(enabled_nodes),
        "active_connections": int(active_connections),
        "active_connections_source": active_connections_source,
        "active_users_estimate": int(active_users_estimate),
        "active_users_source": active_users_source,
        "traffic_up_bytes": int(total_up),
        "traffic_down_bytes": int(total_down),
        "traffic_total_bytes": int(total_up + total_down),
        "last_online_at": last_online_at,
        "last_online_age_seconds": int(last_online_age_seconds) if last_online_age_seconds is not None else None,
        "status": status,
    }


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "ts": _utcnow().isoformat()}


@app.post("/api/internal/observer/batches")
async def api_internal_observer_batches(
    request: Request,
    x_portal_node: str = Header(default=""),
    x_portal_timestamp: str = Header(default=""),
    x_portal_signature: str = Header(default=""),
) -> dict:
    raw_body = await request.body()
    try:
        raw_payload = json.loads(raw_body.decode("utf-8", errors="replace"))
        payload = ObserverBatchIn.model_validate(raw_payload if isinstance(raw_payload, dict) else {})
    except Exception:
        raise HTTPException(status_code=400, detail="Observer batch payload is invalid")

    try:
        timestamp = int(str(x_portal_timestamp or "").strip())
    except Exception:
        raise HTTPException(status_code=401, detail="Observer push timestamp is invalid")

    s = SessionLocal()
    try:
        node = _verify_observer_push(
            s=s,
            node_code=x_portal_node,
            timestamp=timestamp,
            signature=x_portal_signature,
            raw_body=raw_body,
        )
        result = ingest_observer_batch(
            s=s,
            node=node,
            batch_id=payload.batch_id,
            cursor=payload.cursor,
            observations=[item.model_dump() for item in payload.observations],
            collector_parse_error_count=int(payload.parse_error_count or 0),
            received_at=_utcnow(),
        )
        s.commit()
        return result
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        logger.exception("observer batch ingest failed node=%s", str(x_portal_node or "").strip().lower())
        raise HTTPException(status_code=500, detail="Observer batch ingest failed")
    finally:
        s.close()


@app.get("/api/public/plans")
async def public_plans(response: Response) -> dict:
    s = SessionLocal()
    try:
        plans = _plan_catalog_payload(s=s, only_active=True)
        response.headers["Cache-Control"] = "public, max-age=120"
        return {"plans": plans, "widget_enabled": bool(CHECKOUT_WIDGET_ENABLED)}
    finally:
        s.close()


@app.get("/api/public/catalog")
async def public_catalog(response: Response) -> dict:
    s = SessionLocal()
    try:
        response.headers["Cache-Control"] = "public, max-age=120"
        return _public_catalog_payload(s=s)
    finally:
        s.close()


@app.get("/api/public/live-updates")
async def public_live_updates(response: Response, limit: int = Query(default=3, ge=1, le=10)) -> dict:
    s = SessionLocal()
    try:
        rows = (
            s.query(LiveUpdate)
            .filter(LiveUpdate.is_active == True)
            .order_by(LiveUpdate.sort_order.asc(), LiveUpdate.id.desc())
            .limit(int(limit))
            .all()
        )
        if not rows:
            response.headers["Cache-Control"] = "public, max-age=120"
            return {"updates": _default_live_updates()[: int(limit)]}
        out = []
        for row in rows:
            tg_link = _build_tg_post_link(
                channel_username=getattr(row, "channel_username", None),
                post_id=getattr(row, "post_id", None),
                fallback_link=str(row.link or "").strip(),
            )
            channel_raw = str(getattr(row, "channel_username", "") or "").strip().lstrip("@")
            out.append(
                {
                    "id": int(row.id),
                    "title": str(row.title or "").strip(),
                    "summary": str(row.summary or "").strip(),
                    "date": (row.published_at or row.created_at or _utcnow()).date().isoformat(),
                    "link": tg_link,
                    "tg_link": tg_link,
                    "channel_username": channel_raw or None,
                    "post_id": int(getattr(row, "post_id", 0) or 0) or None,
                    "is_active": bool(row.is_active),
                    "sort_order": int(row.sort_order or 0),
                }
            )
        response.headers["Cache-Control"] = "public, max-age=120"
        return {"updates": out}
    finally:
        s.close()


@app.post("/api/auth/telegram/web-login")
async def auth_telegram_web_login(payload: TelegramWebLoginIn) -> dict:
    verified = verify_telegram_login_payload(
        payload=payload.model_dump(),
        bot_token=_current_bot_token(),
        max_age_seconds=TELEGRAM_WEB_LOGIN_MAX_AGE_SECONDS,
    )
    if not verified:
        raise HTTPException(status_code=401, detail="Invalid Telegram login payload")

    tg_id = int(verified.get("id") or 0)
    if tg_id <= 0:
        raise HTTPException(status_code=401, detail="Invalid Telegram user")
    username = (verified.get("username") or "").strip() or None
    _ensure_user_row_for_login(tg_id=tg_id, username=username)
    token = create_web_session_token(
        tg_id=tg_id,
        username=username,
        auth_type="telegram",
        auth_origin="telegram",
    )
    if not token:
        raise HTTPException(status_code=500, detail="Web session is not configured")
    return {
        "ok": True,
        "token": token,
        "user": {"id": tg_id, "username": username},
        "expires_in": int(SESSION_TTL_SECONDS),
    }


@app.post("/api/auth/dev/web-login")
async def auth_dev_web_login(payload: DevWebLoginIn, request: Request) -> dict:
    if not WEBAPP_DEV_AUTH or WEBAPP_DEV_TG_ID <= 0 or not WEBAPP_DEV_AUTH_PASSWORD:
        raise HTTPException(status_code=404, detail="Not found")
    if not _is_local_request(request):
        raise HTTPException(status_code=403, detail="Local dev auth only")
    if not hmac.compare_digest(str(payload.password or ""), WEBAPP_DEV_AUTH_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid dev login")

    tg_id = int(WEBAPP_DEV_TG_ID)
    if not _is_admin_tg(tg_id):
        raise HTTPException(status_code=403, detail="Admin access required")

    username = "dev_admin"
    _ensure_user_row_for_login(tg_id=tg_id, username=username)
    token = create_web_session_token(
        tg_id=tg_id,
        username=username,
        auth_type="dev",
        auth_origin="dev",
    )
    if not token:
        raise HTTPException(status_code=500, detail="Web session is not configured")
    return {
        "ok": True,
        "token": token,
        "user": {"id": tg_id, "username": username},
        "expires_in": int(SESSION_TTL_SECONDS),
    }


@app.get("/api/auth/telegram/oidc/start")
async def auth_telegram_oidc_start() -> dict:
    try:
        payload = build_telegram_oidc_authorize_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "ok": True,
        "mode": "oidc",
        "auth_url": payload["auth_url"],
        "redirect_uri": payload["redirect_uri"],
    }


@app.post("/api/auth/telegram/oidc/finish")
async def auth_telegram_oidc_finish(payload: TelegramOidcFinishIn) -> dict:
    if not verify_telegram_oidc_state_token(payload.state):
        raise HTTPException(status_code=401, detail="Invalid Telegram OAuth state")
    try:
        verified = await exchange_telegram_oidc_code(
            code=payload.code,
            state_token=payload.state,
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    tg_id = int(verified.get("id") or 0)
    if tg_id <= 0:
        raise HTTPException(status_code=401, detail="Invalid Telegram user")
    username = (verified.get("preferred_username") or verified.get("username") or "").strip() or None
    _ensure_user_row_for_login(tg_id=tg_id, username=username)
    token = create_web_session_token(
        tg_id=tg_id,
        username=username,
        auth_type="telegram",
        auth_origin="telegram",
    )
    if not token:
        raise HTTPException(status_code=500, detail="Web session is not configured")
    return {
        "ok": True,
        "token": token,
        "user": {"id": tg_id, "username": username},
        "expires_in": int(SESSION_TTL_SECONDS),
    }


@app.post("/api/auth/email/register")
async def auth_email_register(
    payload: EmailRegisterIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    auth_user = _optional_auth_user(x_telegram_init_data, request=request)
    linked_tg_id = int((auth_user or {}).get("id") or 0) or None
    s = SessionLocal()
    try:
        try:
            identity, verify_token = register_email_identity(
                s,
                email=payload.email,
                password=payload.password,
                linked_tg_id=linked_tg_id,
                display_name=payload.display_name,
            )
        except DuplicateEmailIdentityError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except InvalidEmailInputError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        s.commit()
        s.refresh(identity)
        delivery = await deliver_auth_message(
            kind="verify",
            email=str(identity.email),
            token=verify_token,
            linked_tg_id=int(identity.linked_tg_id or 0),
        )
        debug = build_email_auth_debug_payload(verify_token=verify_token)
        return {
            "ok": True,
            "verification_required": True,
            "delivery": delivery,
            "identity": _email_identity_payload(identity),
            "debug": debug,
        }
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.post("/api/auth/email/verify")
async def auth_email_verify(payload: EmailVerifyIn) -> dict:
    s = SessionLocal()
    try:
        try:
            identity = verify_email_identity(s, token=payload.token)
        except InvalidEmailTokenError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        user = s.query(User).filter(User.tg_id == int(identity.linked_tg_id)).first()
        if not user:
            raise HTTPException(status_code=409, detail="Linked account is missing")
        token = create_web_session_token(
            tg_id=int(user.tg_id),
            username=str(user.username or "").strip() or None,
            auth_type="email",
            auth_origin="email",
            email=str(identity.email),
        )
        if not token:
            raise HTTPException(status_code=500, detail="Web session is not configured")
        s.commit()
        return {
            "ok": True,
            "token": token,
            "expires_in": int(SESSION_TTL_SECONDS),
            "user": {
                "id": int(user.tg_id),
                "username": str(user.username or "").strip() or None,
                "email": str(identity.email),
            },
        }
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.post("/api/auth/email/login")
async def auth_email_login(payload: EmailLoginIn) -> dict:
    s = SessionLocal()
    try:
        try:
            identity = authenticate_email_identity(
                s,
                email=payload.email,
                password=payload.password,
            )
        except (InvalidEmailInputError, InvalidEmailCredentialsError) as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        user = s.query(User).filter(User.tg_id == int(identity.linked_tg_id)).first()
        if not user:
            raise HTTPException(status_code=409, detail="Linked account is missing")
        token = create_web_session_token(
            tg_id=int(user.tg_id),
            username=str(user.username or "").strip() or None,
            auth_type="email",
            auth_origin="email",
            email=str(identity.email),
        )
        if not token:
            raise HTTPException(status_code=500, detail="Web session is not configured")
        s.commit()
        return {
            "ok": True,
            "token": token,
            "expires_in": int(SESSION_TTL_SECONDS),
            "user": {
                "id": int(user.tg_id),
                "username": str(user.username or "").strip() or None,
                "email": str(identity.email),
            },
        }
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.post("/api/auth/email/recovery/start")
async def auth_email_recovery_start(payload: EmailRecoveryStartIn) -> dict:
    s = SessionLocal()
    try:
        try:
            identity, reset_token = start_password_reset(s, email=payload.email)
        except InvalidEmailInputError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        s.commit()
        delivery = {"status": "suppressed", "kind": "reset", "email": str(payload.email).strip().lower()}
        if identity and reset_token:
            delivery = await deliver_auth_message(
                kind="reset",
                email=str(identity.email),
                token=reset_token,
                linked_tg_id=int(identity.linked_tg_id or 0),
            )
        debug = build_email_auth_debug_payload(reset_token=reset_token)
        return {
            "ok": True,
            "recovery_requested": True,
            "delivery": delivery,
            "debug": debug,
        }
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.post("/api/auth/email/recovery/finish")
async def auth_email_recovery_finish(payload: EmailRecoveryFinishIn) -> dict:
    s = SessionLocal()
    try:
        try:
            identity = finish_password_reset(
                s,
                token=payload.token,
                password=payload.password,
            )
        except InvalidEmailInputError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except InvalidEmailTokenError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        user = s.query(User).filter(User.tg_id == int(identity.linked_tg_id)).first()
        if not user:
            raise HTTPException(status_code=409, detail="Linked account is missing")
        token = create_web_session_token(
            tg_id=int(user.tg_id),
            username=str(user.username or "").strip() or None,
            auth_type="email",
            auth_origin="email",
            email=str(identity.email),
        )
        if not token:
            raise HTTPException(status_code=500, detail="Web session is not configured")
        s.commit()
        return {
            "ok": True,
            "token": token,
            "expires_in": int(SESSION_TTL_SECONDS),
            "user": {
                "id": int(user.tg_id),
                "username": str(user.username or "").strip() or None,
                "email": str(identity.email),
            },
        }
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.get("/api/auth/session")
async def auth_session(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        email_identity = get_verified_identity_for_user(s, tg_id=tg_id)
    finally:
        s.close()
    device_name = app_first_service.normalize_app_device_name(
        (getattr(user, "app_device_name", None) if user else None)
        or (getattr(user, "display_name", None) if user else None),
    )
    token_auth_type = str(auth_user.get("auth_type") or "").strip()
    linked_email = _email_identity_payload(email_identity)
    session_email = str(auth_user.get("email") or "") or ((linked_email or {}).get("email") if linked_email else None)
    auth_type = token_auth_type or ("app" if bool(getattr(user, "is_app_user", False)) else "telegram")
    auth_origin = str(auth_user.get("auth_origin") or "").strip() or auth_type
    telegram_identity_id = _linked_telegram_id(user) or (tg_id if auth_type == "telegram" else 0)
    telegram_identity_username = (
        str(getattr(user, "linked_telegram_username", "") or "").strip() if user else ""
    ) or (
        str(auth_user.get("username") or "").strip() if auth_type == "telegram" else ""
    )
    return {
        "ok": True,
        "user": {
            "id": tg_id,
            "account_id": str(tg_id),
            "username": (auth_user.get("username") or (getattr(user, "username", None) if user else None)),
            "email": session_email or None,
            "device_name": device_name,
            "linked_telegram_id": _linked_telegram_id(user),
            "linked_telegram_username": (
                str(getattr(user, "linked_telegram_username", "") or "").strip() if user else ""
            )
            or None,
            "is_authorized": True,
            "auth_type": auth_type,
            "auth_origin": auth_origin,
            "linked_identities": {
                "telegram": {
                    "id": telegram_identity_id or None,
                    "username": telegram_identity_username or None,
                }
                if telegram_identity_id
                else None,
                "email": linked_email,
            },
        },
    }


@app.post("/api/client/session/start-trial")
async def client_start_trial(payload: AppStartTrialIn, request: Request) -> dict:
    client_policy: dict[str, Any] | None = None
    s = SessionLocal()
    try:
        user, created = app_first_service.upsert_app_trial_user(
            s=s,
            payload=payload,
            now=_utcnow(),
            trial_days=APP_TRIAL_DEFAULT_DAYS,
            request_client_ip=_request_client_ip(request),
        )
        s.commit()
        s.refresh(user)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
            carrier=_request_carrier_header(request.headers.get("X-Portal-Carrier")),
        )
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()

    session_token = create_web_session_token(
        tg_id=int(user.tg_id),
        username=str(user.username or "").strip() or None,
        auth_type="app",
        auth_origin="app",
    )
    if not session_token:
        raise HTTPException(status_code=500, detail="App session is not configured")

    sync_ok = False
    panel = ControlPanel()
    try:
        sync_ok = bool(
            await panel.add_client(
                user_uuid=str(user.uuid),
                email=str(user.email),
                sub_type=str(user.sub_type or "FREE"),
                total_gb=int(user.total_gb or 0),
                tg_id=int(user.tg_id),
                sub_token=str(user.sub_token or ""),
            )
        )
    except Exception:
        sync_ok = False
    finally:
        await panel.close()

    start_trial_parts = app_first_service.build_start_trial_response_parts(
        user=user,
        session_token=session_token,
        now=_utcnow(),
        sync_ok=bool(sync_ok),
        build_access_policy=_build_access_policy,
        trial_days=APP_TRIAL_DEFAULT_DAYS,
        channel_bonus_days=CHANNEL_PREMIUM_DAYS,
        client_policy=client_policy,
    )
    payload_s = SessionLocal()
    try:
        payload_user = payload_s.query(User).filter(User.tg_id == int(user.tg_id)).first() or user
        payload_nodes = _nodes_for_user(payload_user, enabled_nodes(payload_s), session=payload_s)
        promo_slots = _promo_slots_payload_for_surface(
            s=payload_s,
            surface="app",
            access_state=str(start_trial_parts["access"].get("access_state") or ""),
        )
        linked_identities = _linked_identities_payload(s=payload_s, user=payload_user)
    finally:
        payload_s.close()

    return {
        "ok": True,
        "created": bool(created),
        "session_token": session_token,
        "account_id": str(int(user.tg_id)),
        "subscription_url": start_trial_parts["subscription_url"],
        "sync_ok": bool(sync_ok),
        "session": start_trial_parts["session"],
        "client_policy": start_trial_parts["client_policy"],
        "access": start_trial_parts["access"],
        "linked_identities": linked_identities,
        "free_caps": _free_caps_payload(user=user, access_policy=start_trial_parts["access"]),
        "redeem_eligibility": _redeem_eligibility_payload(user=user, access_policy=start_trial_parts["access"]),
        "promo_slots": promo_slots,
        "hidden_transport_matrix": _hidden_transport_matrix_payload(nodes=payload_nodes, client_policy=client_policy),
        "location_matrix": _location_matrix_payload(user=user, nodes=payload_nodes, client_policy=client_policy),
        "provisioning": start_trial_parts["provisioning"],
    }


def _route_policy_payload(user: User | None) -> dict[str, Any]:
    return {
        "ok": True,
        **app_first_service.resolve_route_policy(user),
    }


@app.get("/api/client/route-policy")
async def client_route_policy(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return _route_policy_payload(user)
    finally:
        s.close()


@app.post("/api/client/route-policy")
async def client_update_route_policy(
    payload: ClientRoutePolicyIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        app_first_service.persist_route_policy(
            user,
            route_mode=payload.route_mode,
            selected_apps=list(payload.selected_apps or []),
            requires_elevated_privileges=payload.requires_elevated_privileges,
        )
        s.commit()
        s.refresh(user)
        return _route_policy_payload(user)
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


SMART_CONNECT_LATENCY_EVENT_NAME = "smart_connect_latency_sample"


class NodeLatencyPointIn(BaseModel):
    node_code: str = Field(min_length=2, max_length=32)
    rtt_ms: int = Field(ge=1, le=60_000)


class NodeLatencySamplesIn(BaseModel):
    profile_revision: str | None = Field(default=None, max_length=128)
    transport_profile: str | None = Field(default=None, max_length=64)
    selected_node_code: str | None = Field(default=None, max_length=32)
    previous_node_code: str | None = Field(default=None, max_length=32)
    stickiness_applied: bool = False
    samples: list[NodeLatencyPointIn] = Field(default_factory=list, max_length=10)


def _smart_connect_latest_sample(session, *, user: User, install_id: str) -> dict[str, Any]:
    query = session.query(Event).filter(Event.tg_id == int(user.tg_id), Event.event_name == SMART_CONNECT_LATENCY_EVENT_NAME)
    if install_id:
        query = query.filter(Event.session_id == install_id)
    row = query.order_by(Event.created_at.desc(), Event.id.desc()).first()
    if not row:
        return {}
    try:
        payload = json.loads(str(getattr(row, "meta_json", "") or "{}"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    payload.setdefault("created_at", _safe_iso(getattr(row, "created_at", None)))
    return payload


def _smart_connect_rejection_reason(
    node: Any,
    *,
    transport_profile: str,
    rollout_config: dict[str, Any],
    now: datetime,
) -> str | None:
    if not bool(getattr(node, "enabled", True)):
        return "disabled"
    if not bool(getattr(node, "accepting_new_clients", True)):
        return "not_accepting_new_clients"
    if bool(getattr(node, "is_draining", False)):
        return "draining"
    if not bool(getattr(node, "is_healthy", True)):
        return "unhealthy"
    if node_is_stale(node, now=now, stale_after_seconds=SMART_CONNECT_STALE_AFTER_SECONDS):
        return "stale"
    if node_cpu_penalty(node) is None:
        return "cpu_hot"
    if node_backend_penalty(node) is None:
        return "health_score_low"
    if not _node_supports_transport_profile(node, transport_profile):
        return "transport_mismatch"
    filtered = _filter_nodes_for_transport_profile(
        nodes=[node],
        rollout_config=rollout_config,
        transport_profile=transport_profile,
    )
    if not filtered:
        return "transport_allowlist_mismatch"
    return None


def _smart_connect_shortlist(
    *,
    session,
    user: User,
    nodes: list[Any],
    transport_profile: str,
    rollout_config: dict[str, Any],
    profile_revision: str,
) -> dict[str, Any]:
    now = _utcnow()
    rejected_counts: dict[str, int] = {}
    eligible: list[Any] = []
    for node in nodes:
        reason = _smart_connect_rejection_reason(
            node,
            transport_profile=transport_profile,
            rollout_config=rollout_config,
            now=now,
        )
        if reason:
            rejected_counts[reason] = int(rejected_counts.get(reason, 0) or 0) + 1
            continue
        eligible.append(node)

    shortlist_limit = 1 if user_uses_free_pool(user) else SMART_CONNECT_SHORTLIST_LIMIT
    shortlist_nodes = eligible[:shortlist_limit]
    shortlist_codes = [str(getattr(node, "code", "") or "").strip().lower() for node in shortlist_nodes]
    install_id = str(getattr(user, "app_install_id", "") or "").strip()
    latest_sample = _smart_connect_latest_sample(session, user=user, install_id=install_id)
    preferred_node_code = str(latest_sample.get("selected_node_code") or "").strip().lower() or None
    if preferred_node_code and preferred_node_code not in shortlist_codes:
        preferred_node_code = None

    shortlist_payload = []
    for index, node in enumerate(shortlist_nodes, start=1):
        code = str(getattr(node, "code", "") or "").strip().lower()
        shortlist_payload.append(
            {
                "code": code,
                "country": _node_country_name(code),
                "rank": index,
                "rank_hint": {
                    "health_score": float(getattr(node, "health_score", 0.0) or 0.0),
                    "cpu_percent": float(getattr(node, "cpu_percent", 0.0) or 0.0),
                    "panel_latency_ms": _safe_ping(node),
                    "backend_penalty": int(node_backend_penalty(node) or 0),
                    "cpu_penalty": int(node_cpu_penalty(node) or 0),
                    "sticky_preferred": bool(preferred_node_code and preferred_node_code == code),
                },
            }
        )

    revision_seed = "|".join(
        [
            str(profile_revision or "").strip(),
            str(transport_profile or "").strip(),
            *(item["code"] for item in shortlist_payload),
        ]
    )
    shortlist_revision = hashlib.sha256(revision_seed.encode("utf-8")).hexdigest()[:12] if revision_seed else ""
    return {
        "eligible": bool(shortlist_payload),
        "fallback_required": not bool(shortlist_payload),
        "shortlist_reason": "eligible" if shortlist_payload else "no_eligible_nodes",
        "shortlist_limit": int(shortlist_limit),
        "shortlist_revision": shortlist_revision,
        "transport_profile": str(transport_profile or ""),
        "profile_revision": str(profile_revision or ""),
        "fallback_order": _managed_manifest_fallback_order(transport_profile),
        "shortlist": shortlist_payload,
        "stickiness": {
            "preferred_node_code": preferred_node_code,
            "threshold_percent": int(SMART_CONNECT_STICKINESS_THRESHOLD_PERCENT),
            "latest_sample_at": latest_sample.get("created_at"),
            "stickiness_applied": bool(latest_sample.get("stickiness_applied", False)),
        },
        "scoring": {
            "formula": "effective_score = rtt_ms + cpu_penalty + backend_penalty",
            "cpu_penalty_buckets": [
                {"range": "<60", "penalty": 0},
                {"range": "60-74", "penalty": 20},
                {"range": "75-84", "penalty": 60},
                {"range": "85-89", "penalty": 120},
                {"range": ">=90", "penalty": "reject"},
            ],
            "backend_penalty_buckets": [
                {"range": ">=90", "penalty": 0},
                {"range": "75-89", "penalty": 30},
                {"range": "60-74", "penalty": 80},
                {"range": "<60", "penalty": "reject"},
            ],
            "stickiness_threshold_percent": int(SMART_CONNECT_STICKINESS_THRESHOLD_PERCENT),
        },
        "rejected_counts": rejected_counts,
    }


@app.get("/api/client/profile/managed")
async def client_managed_profile(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
    x_portal_carrier: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        _maybe_downgrade_expired_to_free(s, user)
        _ensure_free_cycle_state_persisted(s, user)
        rollout_config = load_network_rollout_config(session=s)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
            carrier=_request_carrier_header(x_portal_carrier),
            rollout_config=rollout_config,
        )
        transport_profile = str(client_policy.get("transport_profile") or LEGACY_REALITY_FALLBACK).strip() or LEGACY_REALITY_FALLBACK
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        runtime = await _get_user_runtime_summary(s=s, user=user, nodes=nodes_for_user)
        access_policy = _build_access_policy(
            user=user,
            used_bytes=int(runtime.get("traffic_total_bytes", 0) or 0),
        )
        effective_nodes = _effective_transport_nodes(
            nodes=nodes_for_user,
            rollout_config=rollout_config,
            transport_profile=transport_profile,
        )
        config_format, config_payload = _managed_manifest_payload(
            user=user,
            nodes=effective_nodes,
            title="POKROV",
            transport_profile=transport_profile,
        )
        smart_connect = _smart_connect_shortlist(
            session=s,
            user=user,
            nodes=nodes_for_user,
            transport_profile=transport_profile,
            rollout_config=rollout_config,
            profile_revision=str(client_policy.get("profile_revision") or ""),
        )
        return {
            "version": str(rollout_config.get("version") or ""),
            "profile_revision": str(client_policy.get("profile_revision") or ""),
            "transport_profile": transport_profile,
            "transport_kind": str(client_policy.get("transport_kind") or ""),
            "engine_hint": str(client_policy.get("engine_hint") or ""),
            "config_format": config_format,
            "config_payload": config_payload,
            "fallback_order": _managed_manifest_fallback_order(transport_profile),
            "support_context": dict(client_policy.get("support_context") or {}),
            "subscription_url": build_subscription_url(str(getattr(user, "sub_token", "") or "")),
            "smart_connect": smart_connect,
            "linked_identities": _linked_identities_payload(s=s, user=user, auth_user=auth_user),
            "access": {
                **access_policy,
                "sub_type": str(getattr(user, "sub_type", "") or ""),
                "current_plan_code": str(getattr(user, "current_plan_code", "") or ""),
                "expiry_at": _safe_iso(getattr(user, "expiry_at", None)),
            },
            "free_caps": _free_caps_payload(user=user, access_policy=access_policy),
            "redeem_eligibility": _redeem_eligibility_payload(user=user, access_policy=access_policy),
            "promo_slots": _promo_slots_payload_for_surface(
                s=s,
                surface="app",
                access_state=str(access_policy.get("access_state") or ""),
            ),
            "hidden_transport_matrix": _hidden_transport_matrix_payload(nodes=nodes_for_user, client_policy=client_policy),
            "location_matrix": _location_matrix_payload(user=user, nodes=nodes_for_user, client_policy=client_policy),
        }
    finally:
        s.close()


@app.get("/api/client/promo-slots")
async def client_promo_slots(
    request: Request,
    surface: str = Query(default="app", min_length=2, max_length=32),
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        _maybe_downgrade_expired_to_free(s, user)
        _ensure_free_cycle_state_persisted(s, user)
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        runtime = await _get_user_runtime_summary(s=s, user=user, nodes=nodes_for_user)
        access_policy = _build_access_policy(user=user, used_bytes=int(runtime.get("traffic_total_bytes", 0) or 0))
        return _promo_slots_payload_for_surface(
            s=s,
            surface=str(surface or "app").strip().lower(),
            access_state=str(access_policy.get("access_state") or ""),
        )
    finally:
        s.close()


@app.post("/api/client/nodes/latency-samples")
async def client_nodes_latency_samples(
    payload: NodeLatencySamplesIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
    x_portal_carrier: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        install_id = str(getattr(user, "app_install_id", "") or "").strip()
        if not install_id:
            raise HTTPException(status_code=400, detail="install_id is required")

        rollout_config = load_network_rollout_config(session=s)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=install_id or None,
            carrier=_request_carrier_header(x_portal_carrier),
            rollout_config=rollout_config,
        )
        transport_profile = (
            str(payload.transport_profile or client_policy.get("transport_profile") or LEGACY_REALITY_FALLBACK).strip()
            or LEGACY_REALITY_FALLBACK
        )
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        smart_connect = _smart_connect_shortlist(
            session=s,
            user=user,
            nodes=nodes_for_user,
            transport_profile=transport_profile,
            rollout_config=rollout_config,
            profile_revision=str(payload.profile_revision or client_policy.get("profile_revision") or ""),
        )
        allowed_codes = {
            str(item.get("code") or "").strip().lower()
            for item in smart_connect.get("shortlist") or []
            if str(item.get("code") or "").strip()
        }
        accepted_samples: list[dict[str, int | str]] = []
        for sample in list(payload.samples or [])[:10]:
            code = str(sample.node_code or "").strip().lower()
            if not code or (allowed_codes and code not in allowed_codes):
                continue
            accepted_samples.append({"node_code": code, "rtt_ms": int(sample.rtt_ms)})

        selected_node_code = str(payload.selected_node_code or "").strip().lower()
        if selected_node_code and allowed_codes and selected_node_code not in allowed_codes:
            selected_node_code = ""
        previous_node_code = str(payload.previous_node_code or "").strip().lower()
        if previous_node_code and allowed_codes and previous_node_code not in allowed_codes:
            previous_node_code = ""

        event_meta = {
            "install_id": install_id,
            "profile_revision": str(payload.profile_revision or client_policy.get("profile_revision") or ""),
            "transport_profile": transport_profile,
            "selected_node_code": selected_node_code or None,
            "previous_node_code": previous_node_code or None,
            "stickiness_applied": bool(payload.stickiness_applied),
            "carrier": _request_carrier_header(x_portal_carrier) or None,
            "platform": str(getattr(user, "app_platform", "") or "").strip() or None,
            "samples": accepted_samples,
        }
        s.add(
            Event(
                tg_id=int(user.tg_id),
                event_name=SMART_CONNECT_LATENCY_EVENT_NAME,
                source="app",
                session_id=install_id,
                meta_json=json.dumps(event_meta, ensure_ascii=False),
                created_at=_utcnow(),
            )
        )
        s.commit()
        return {
            "ok": True,
            "accepted_samples": len(accepted_samples),
            "preferred_node_code": selected_node_code or None,
        }
    finally:
        s.close()


@app.post("/api/client/telegram/link")
async def client_telegram_link_start(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        linked_id = _linked_telegram_id(user)
        linked_username = str(getattr(user, "linked_telegram_username", "") or "").strip()
        start_code = ""
        if not linked_id:
            start_code = app_first_service.create_app_telegram_start_code(
                s,
                account_tg_id=int(user.tg_id),
                now=_utcnow(),
            )
        s.commit()
        bot_username = (BOT_USERNAME or "pokrov_vpnbot").lstrip("@")
        channel_username = (PUBLIC_CHANNEL or "").lstrip("@").strip()
        return {
            "ok": True,
            "linked": bool(linked_id),
            "linked_telegram_id": linked_id or None,
            "linked_telegram_username": linked_username or None,
            "start_code": start_code,
            "bot_url": f"https://t.me/{bot_username}?start={start_code}" if start_code else f"https://t.me/{bot_username}",
            "channel_url": f"https://t.me/{channel_username}" if channel_username else None,
        }
    finally:
        s.close()


@app.api_route("/pay/success", methods=["GET", "POST"])
async def pay_success(request: Request):
    if request.method == "POST":
        return {"ok": True, "status": "success"}
    action = _public_webapp_url()
    return HTMLResponse(
        content=_payment_page_html(
            title="Оплата подтверждена",
            message="Платеж получен. Доступ обновится автоматически, а статус появится в личном кабинете.",
            action_url=action,
            action_label="Открыть кабинет",
        )
    )


@app.api_route("/pay/fail", methods=["GET", "POST"])
async def pay_fail(request: Request):
    if request.method == "POST":
        return {"ok": False, "status": "failed"}
    action = _public_checkout_url() or (f"https://t.me/{BOT_USERNAME}" if BOT_USERNAME else "/")
    return HTMLResponse(
        content=_payment_page_html(
            title="Платеж не завершен",
            message="Платеж не прошел. Можно повторить попытку или обратиться в службу заботы через Telegram.",
            action_url=action,
            action_label="Повторить оплату",
        )
    )


@app.api_route("/api/payments/result/{provider}", methods=["POST", "GET"])
async def payment_result(provider: str, request: Request) -> dict:
    return await _handle_payment_callback(provider=provider, event_type="result", request=request)


@app.api_route("/api/payments/refund/{provider}", methods=["POST", "GET"])
async def payment_refund(provider: str, request: Request) -> dict:
    return await _handle_payment_callback(provider=provider, event_type="refund", request=request)


@app.api_route("/api/payments/chargeback/{provider}", methods=["POST", "GET"])
async def payment_chargeback(provider: str, request: Request) -> dict:
    return await _handle_payment_callback(provider=provider, event_type="chargeback", request=request)


@app.api_route("/api/payments/freekassa/notify", methods=["POST", "GET"])
async def payment_freekassa_notify(request: Request):
    result = await _handle_payment_callback(provider="freekassa", event_type="result", request=request)
    if request.method == "POST" and bool(result.get("ok")):
        # Freekassa SCI expects a plain "YES" acknowledgment.
        return PlainTextResponse("YES")
    return result


async def _rub_create_order_internal(
    *,
    request: Request,
    provider: str,
    tg_id: int,
    source: str,
    plan_code: str,
    campaign: str = "",
    promo_code: str = "",
    currency: str = "RUB",
    consume_pending_discount: bool = False,
) -> RubOrderActionOut:
    _ensure_checkout_runtime_ready()
    provider = _normalize_provider(provider)
    if not provider:
        enabled_codes = enabled_rub_provider_codes()
        provider = str(enabled_codes[0] if enabled_codes else "").strip().lower()
    if not provider:
        raise HTTPException(status_code=503, detail="No RUB payment providers are enabled")
    if provider not in PAYMENT_PROVIDER_WHITELIST:
        raise HTTPException(status_code=400, detail="Unsupported payment provider")
    if provider != "freekassa" and not provider_is_configured(provider):
        raise HTTPException(status_code=503, detail=f"{provider} is not configured")
    s = SessionLocal()
    try:
        plan = _resolve_plan_config(s=s, code=plan_code)
        if not plan:
            raise HTTPException(status_code=400, detail="Unknown plan for RUB checkout")
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        base_amount = max(0, int(plan.get("amount_rub") or 0))
        final_amount = base_amount
        discount_pct = 0
        discount_applied = False
        effective_promo = (promo_code or "").strip().upper()[:32]
        pending_code = (getattr(user, "pending_discount_code", "") or "").strip().upper()[:20]
        pending_pct = int(getattr(user, "pending_discount_pct", 0) or 0)
        referral_discount_eligible = bool(getattr(user, "referrer_id", None) and not bool(getattr(user, "first_purchase_done", False)))
        working_amount = int(base_amount)
        if referral_discount_eligible and working_amount > 0:
            working_amount = max(1, int(round(working_amount * 0.8)))
        if pending_pct > 0:
            working_amount, _ = _price_with_pending_discount(amount_rub=working_amount, pending_pct=pending_pct)
            if not effective_promo and pending_code:
                effective_promo = pending_code[:32]
        final_amount = max(1, int(working_amount)) if base_amount > 0 else 0
        discount_applied = bool(base_amount > 0 and final_amount < base_amount)
        discount_pct = int(round((1.0 - (float(final_amount) / float(base_amount))) * 100)) if discount_applied else 0
        amount_rub = float(final_amount)
        order_prefix = "fk" if provider == "freekassa" else provider[:12]
        order_id = f"{order_prefix}_{source}_{tg_id}_{int(time.time())}_{secrets.token_hex(4)}"
        plan_label = str(plan.get("label") or RUB_PLAN_LABELS.get(plan_code) or plan_code).strip()
        ext = ExternalOrder(
            order_id=order_id,
            tg_id=int(tg_id),
            provider=provider,
            plan_code=str(plan.get("code") or plan_code).strip().lower(),
            source=source,
            campaign=(campaign or "").strip()[:64] or None,
            promo_code=effective_promo or None,
            amount=float(amount_rub),
            currency=(currency or "RUB").strip().upper()[:16] or "RUB",
            status="created",
            meta_json=json.dumps(
                {
                    "source": source,
                    "campaign": campaign,
                    "promo_code": effective_promo,
                    "tg_id": int(tg_id),
                    "plan_code": str(plan.get("code") or plan_code).strip().lower(),
                    "provider": provider,
                    "plan_label": plan_label,
                    "pricing": {
                        "base_amount_rub": int(base_amount),
                        "final_amount_rub": int(final_amount),
                        "discount_pct": int(discount_pct),
                        "discount_applied": bool(discount_applied),
                        "pending_discount_code": pending_code or None,
                        "referral_discount_eligible": bool(referral_discount_eligible),
                    },
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )[:4000],
            created_at=_utcnow(),
        )
        s.add(ext)
        if consume_pending_discount and discount_applied:
            user.pending_discount_pct = None
            user.pending_discount_code = None
            user.pending_discount_set_at = None
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()

    req_data = {
        "provider": provider,
        "amount": float(amount_rub),
        "currency": "RUB",
        "tg_id": int(tg_id),
        "plan_code": str(plan.get("code") or plan_code).strip().lower(),
        "plan_label": plan_label,
        "campaign": campaign or "",
        "promo_code": effective_promo or "",
        "source": source,
        "discount_pct": int(discount_pct),
        "base_amount_rub": int(base_amount),
        "final_amount_rub": int(final_amount),
        "referral_discount_eligible": bool(referral_discount_eligible),
        "client_ip": _fk_client_ip(request),
    }
    if provider == "freekassa":
        payment_url = _build_freekassa_payment_url(
            source=source,
            order_id=order_id,
            amount_rub=amount_rub,
            currency="RUB",
            tg_id=int(tg_id),
            plan_code=str(plan.get("code") or plan_code).strip().lower(),
            campaign=campaign or "",
            promo_code=effective_promo or "",
        )
        remote_response: dict[str, Any] = {"payment_url": payment_url}
    else:
        payment = await create_rub_payment(
            provider=provider,
            order_id=order_id,
            amount_rub=amount_rub,
            currency="RUB",
            description=f"POKROV {plan_label}",
            success_url=_pay_success_url(provider),
            fail_url=_pay_fail_url(provider),
            result_url=_provider_result_url(provider),
            refund_url=_provider_refund_url(provider),
            chargeback_url=_provider_chargeback_url(provider),
            logo_url=(os.getenv("PAYMENT_LOGO_URL") or "").strip(),
            custom={
                "tg_id": int(tg_id),
                "plan_code": str(plan.get("code") or plan_code).strip().lower(),
                "provider": provider,
                "source": source,
                "campaign": campaign or "",
                "promo_code": effective_promo or "",
            },
        )
        payment_url = str(payment.get("payment_url") or "").strip()
        remote_response = dict(payment.get("remote") or {})

    s = SessionLocal()
    try:
        row = s.query(ExternalOrder).filter(ExternalOrder.provider == provider, ExternalOrder.order_id == order_id).first()
        if row:
            row.status = "pending"
            row.meta_json = json.dumps(
                {
                    "request": req_data,
                    "response": {"payment_url": payment_url, "remote": remote_response},
                    "pricing": {
                        "base_amount_rub": int(base_amount),
                        "final_amount_rub": int(final_amount),
                        "discount_pct": int(discount_pct),
                        "discount_applied": bool(discount_applied),
                    },
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )[:4000]
            s.commit()
    finally:
        s.close()

    return RubOrderActionOut(
        ok=True,
        provider=provider,
        provider_label=(PROVIDER_META.get(provider).label if provider in PROVIDER_META else provider.title()),
        order_id=order_id,
        payment_url=payment_url or None,
        amount_rub=float(amount_rub),
        currency="RUB",
        status="pending",
        widget_enabled=bool(CHECKOUT_WIDGET_ENABLED),
        discount_applied=bool(discount_applied),
        base_amount_rub=float(base_amount),
        discount_pct=int(discount_pct),
    )


@app.get("/api/payments/providers", response_model=RubProvidersOut)
async def rub_payment_providers() -> RubProvidersOut:
    return _public_checkout_provider_state()


@app.post("/api/payments/orders/create", response_model=RubOrderActionOut)
async def rub_order_create(
    payload: RubOrderCreateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> RubOrderActionOut:
    _ensure_checkout_runtime_ready()
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    actor_tg_id = int(auth_user.get("id", 0))
    source = (payload.source or "site").strip().lower()
    if source not in {"site", "bot"}:
        source = "site"

    tg_id = int(payload.tg_id or actor_tg_id)
    if tg_id != actor_tg_id and not _is_admin_tg(actor_tg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    return await _rub_create_order_internal(
        request=request,
        provider=_normalize_provider(payload.provider),
        tg_id=int(tg_id),
        source=source,
        plan_code=(payload.plan_code or "").strip().lower(),
        campaign=_sanitize_deeplink_token(payload.campaign, max_len=64, uppercase=False),
        promo_code=_sanitize_deeplink_token(payload.promo_code, max_len=20, uppercase=True),
        currency=(payload.currency or "RUB").strip().upper(),
        consume_pending_discount=False,
    )


@app.post("/api/payments/orders/create-public", response_model=RubOrderActionOut)
async def rub_order_create_public(
    payload: RubPublicOrderCreateIn,
    request: Request,
) -> RubOrderActionOut:
    _ensure_checkout_runtime_ready()
    ticket_payload = _parse_checkout_ticket(payload.checkout_ticket)
    if not ticket_payload:
        raise HTTPException(status_code=401, detail="Invalid or expired checkout ticket")
    tg_id = int(ticket_payload.get("tg_id") or 0)
    if tg_id <= 0:
        raise HTTPException(status_code=400, detail="Checkout ticket has no user binding")
    source = str(ticket_payload.get("source") or "bot").strip().lower()
    if source not in {"site", "bot"}:
        source = "bot"
    ticket_plan_code = str(ticket_payload.get("plan_code") or "").strip().lower()
    request_plan_code = (payload.plan_code or "").strip().lower()
    if ticket_plan_code and request_plan_code and request_plan_code != ticket_plan_code:
        raise HTTPException(status_code=400, detail="Plan code does not match checkout ticket")
    plan_code = (ticket_plan_code or request_plan_code or "").strip().lower()
    campaign = _sanitize_deeplink_token(str(ticket_payload.get("campaign_key") or ""), max_len=64, uppercase=False)
    promo_code = _sanitize_deeplink_token(str(ticket_payload.get("promo_code") or ""), max_len=20, uppercase=True)
    return await _rub_create_order_internal(
        request=request,
        provider=_normalize_provider(payload.provider),
        tg_id=tg_id,
        source=source,
        plan_code=plan_code,
        campaign=campaign,
        promo_code=promo_code,
        currency=(payload.currency or "RUB").strip().upper(),
        consume_pending_discount=False,
    )


@app.post("/api/payments/freekassa/orders/create", response_model=RubOrderActionOut)
async def freekassa_order_create(
    payload: FreekassaOrderCreateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> RubOrderActionOut:
    generic = RubOrderCreateIn(
        provider="freekassa",
        plan_code=payload.plan_code,
        source=payload.source,
        tg_id=payload.tg_id,
        campaign=payload.campaign,
        promo_code=payload.promo_code,
        currency=payload.currency,
    )
    return await rub_order_create(generic, request=request, x_telegram_init_data=x_telegram_init_data)


@app.post("/api/payments/freekassa/orders/create-public", response_model=RubOrderActionOut)
async def freekassa_order_create_public(
    payload: FreekassaPublicOrderCreateIn,
    request: Request,
) -> RubOrderActionOut:
    generic = RubPublicOrderCreateIn(
        provider="freekassa",
        plan_code=payload.plan_code,
        checkout_ticket=payload.checkout_ticket,
        currency=payload.currency,
    )
    return await rub_order_create_public(generic, request=request)


@app.get("/api/payments/freekassa/orders/{order_id}")
async def freekassa_order_get(
    order_id: str,
    request: Request,
    source: str = "site",
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    actor_tg_id = int(auth_user.get("id", 0))
    local_status = ""
    request_source = (source or "").strip().lower() or "site"
    s = SessionLocal()
    try:
        row = s.query(ExternalOrder).filter(ExternalOrder.provider == "freekassa", ExternalOrder.order_id == str(order_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        if int(row.tg_id or 0) != actor_tg_id and not _is_admin_tg(actor_tg_id):
            raise HTTPException(status_code=403, detail="Access denied")
        local_status = str(row.status or "")
        if str(row.source or "").strip():
            request_source = str(row.source).strip().lower()
    finally:
        s.close()
    remote = await _freekassa_api_request(source=request_source, method="orders", data={"orderId": order_id})
    return {"ok": True, "provider": "freekassa", "order_id": order_id, "status_local": local_status, "remote": remote}


@app.post("/api/payments/freekassa/orders/{order_id}/refund")
async def freekassa_order_refund(
    order_id: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    _require_admin(x_telegram_init_data, request=request)
    s = SessionLocal()
    try:
        row = s.query(ExternalOrder).filter(ExternalOrder.provider == "freekassa", ExternalOrder.order_id == str(order_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        amount = float(row.amount or 0.0)
        source = str(row.source or "site")
    finally:
        s.close()
    remote = await _freekassa_api_request(
        source=source,
        method="orders/refund",
        data={"orderId": order_id, "amount": amount},
    )
    return {"ok": True, "provider": "freekassa", "order_id": order_id, "remote": remote}


@app.get("/api/payments/freekassa/currencies")
async def freekassa_currencies(
    request: Request,
    source: str = "site",
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    _require_auth_user(x_telegram_init_data, request=request)
    remote = await _freekassa_api_request(source=source, method="currencies", data={})
    return {"ok": True, "provider": "freekassa", "remote": remote}


@app.get("/api/payments/freekassa/currencies/{currency}/status")
async def freekassa_currency_status(
    currency: str,
    request: Request,
    source: str = "site",
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    _require_auth_user(x_telegram_init_data, request=request)
    remote = await _freekassa_api_request(
        source=source,
        method="currencies/status",
        data={"currency": str(currency or "").strip().upper()},
    )
    return {"ok": True, "provider": "freekassa", "currency": str(currency or "").upper(), "remote": remote}


def _sample_memory_percent(sample: NodeHealthSample | None) -> float:
    if not sample:
        return 0.0
    total = float(getattr(sample, "memory_total_mb", 0) or 0.0)
    if total <= 0:
        return 0.0
    used = float(getattr(sample, "memory_used_mb", 0) or 0.0)
    return round((used / total) * 100.0, 2)


def _sample_disk_percent(sample: NodeHealthSample | None) -> float:
    if not sample:
        return 0.0
    total = float(getattr(sample, "disk_total_gb", 0.0) or 0.0)
    if total <= 0:
        return 0.0
    used = float(getattr(sample, "disk_used_gb", 0.0) or 0.0)
    return round((used / total) * 100.0, 2)


def _network_utilization_percent(total_mbps: object) -> float:
    current = float(total_mbps or 0.0)
    capacity = float(NODE_METRICS_PORT_CAPACITY_MBPS or 0.0)
    if current <= 0 or capacity <= 0:
        return 0.0
    return round((current / capacity) * 100.0, 2)


def _sample_network_percent(sample: NodeHealthSample | None) -> float:
    if not sample:
        return 0.0
    return _network_utilization_percent(getattr(sample, "network_total_mbps", 0.0))


def _observer_is_stale(node: Node, *, now: datetime) -> bool:
    last_push_at = getattr(node, "observer_last_push_at", None)
    configured = bool(str(getattr(node, "observer_push_secret", "") or "").strip())
    if not configured and not last_push_at:
        return False
    if not last_push_at:
        return True
    return int((now - last_push_at).total_seconds()) > observer_stale_after_seconds()


def _active_node_metric_alert_kinds(
    *,
    samples: list[NodeHealthSample],
    last_sample_at: datetime | None,
    stale_after_seconds: int,
    now: datetime,
) -> list[str]:
    kinds: list[str] = []
    age_seconds = int((now - last_sample_at).total_seconds()) if last_sample_at else None
    if age_seconds is None or age_seconds > stale_after_seconds:
        kinds.append("stale_metrics")
        return kinds

    if len(samples) < NODE_METRICS_SUSTAINED_SAMPLES:
        return kinds

    window = samples[:NODE_METRICS_SUSTAINED_SAMPLES]
    if all(float(getattr(sample, "cpu_percent", 0.0) or 0.0) >= NODE_METRICS_CPU_ALERT_PERCENT for sample in window):
        kinds.append("cpu_high")
    if all(_sample_memory_percent(sample) >= NODE_METRICS_MEMORY_ALERT_PERCENT for sample in window):
        kinds.append("memory_high")
    if all(_sample_disk_percent(sample) >= NODE_METRICS_DISK_ALERT_PERCENT for sample in window):
        kinds.append("disk_high")
    if all(_sample_network_percent(sample) >= NODE_METRICS_NETWORK_ALERT_PERCENT for sample in window):
        kinds.append("network_high")
    if all(float(getattr(sample, "panel_latency_ms", 0) or 0.0) >= NODE_METRICS_LATENCY_ALERT_MS for sample in window):
        kinds.append("latency_high")
    if all(float(getattr(sample, "panel_error_rate", 0.0) or 0.0) >= NODE_METRICS_ERROR_RATE_ALERT for sample in window):
        kinds.append("error_rate_high")
    if all(int(getattr(sample, "active_clients", 0) or 0) >= NODE_METRICS_ACTIVE_CLIENTS_ALERT for sample in window):
        kinds.append("client_density_high")
    return kinds


def _node_snapshot_alert_kinds(
    *,
    node: Node,
    last_sample_at: datetime | None,
    stale_after_seconds: int,
    now: datetime,
) -> list[str]:
    age_seconds = int((now - last_sample_at).total_seconds()) if last_sample_at else None
    kinds: list[str] = []
    if age_seconds is None or age_seconds > stale_after_seconds:
        kinds.append("stale_metrics")
    cpu_percent = float(getattr(node, "cpu_percent", 0.0) or 0.0)
    memory_total = float(getattr(node, "memory_total_mb", 0.0) or 0.0)
    memory_used = float(getattr(node, "memory_used_mb", 0.0) or 0.0)
    disk_total = float(getattr(node, "disk_total_gb", 0.0) or 0.0)
    disk_used = float(getattr(node, "disk_used_gb", 0.0) or 0.0)
    network_total_mbps = float(getattr(node, "network_total_mbps", 0.0) or 0.0)
    memory_percent = (memory_used / memory_total * 100.0) if memory_total > 0 else 0.0
    disk_percent = (disk_used / disk_total * 100.0) if disk_total > 0 else 0.0
    if cpu_percent >= NODE_METRICS_CPU_ALERT_PERCENT:
        kinds.append("cpu_high")
    if memory_percent >= NODE_METRICS_MEMORY_ALERT_PERCENT:
        kinds.append("memory_high")
    if disk_percent >= NODE_METRICS_DISK_ALERT_PERCENT:
        kinds.append("disk_high")
    if _network_utilization_percent(network_total_mbps) >= NODE_METRICS_NETWORK_ALERT_PERCENT:
        kinds.append("network_high")
    if float(getattr(node, "panel_latency_ms", 0.0) or 0.0) >= NODE_METRICS_LATENCY_ALERT_MS:
        kinds.append("latency_high")
    if float(getattr(node, "panel_error_rate", 0.0) or 0.0) >= NODE_METRICS_ERROR_RATE_ALERT:
        kinds.append("error_rate_high")
    if int(getattr(node, "active_clients", 0) or 0) >= NODE_METRICS_ACTIVE_CLIENTS_ALERT:
        kinds.append("client_density_high")
    if _observer_is_stale(node, now=now):
        kinds.append("observer_push_stale")
    return kinds


def _legacy_node_alert_kind(kind: str) -> str:
    mapping = {
        "cpu_high": "high_cpu",
        "memory_high": "high_memory",
        "disk_high": "high_disk",
        "network_high": "high_network",
        "latency_high": "high_latency",
        "error_rate_high": "high_error_rate",
        "client_density_high": "high_client_density",
        "observer_push_stale": "observer_push_stale",
        "stale_metrics": "stale_metrics",
    }
    return mapping.get(str(kind or ""), str(kind or ""))


def _legacy_node_alerts(kinds: list[str]) -> list[str]:
    return sorted({_legacy_node_alert_kind(kind) for kind in kinds if str(kind or "").strip()})


def _nullable_node_memory_value(*, used_mb: object, total_mb: object) -> tuple[int | None, int | None]:
    total = int(total_mb or 0)
    if total <= 0:
        return None, None
    return int(used_mb or 0), total


def _nullable_node_disk_value(*, used_gb: object, total_gb: object, free_gb: object) -> tuple[float | None, float | None, float | None]:
    total = float(total_gb or 0.0)
    if total <= 0:
        return None, None, None
    return float(used_gb or 0.0), total, float(free_gb or 0.0)


def _nullable_node_network_value(
    *,
    rx_bytes_total: object,
    tx_bytes_total: object,
    rx_mbps: object,
    tx_mbps: object,
    total_mbps: object,
) -> tuple[int | None, int | None, float | None, float | None, float | None]:
    rx_total = int(rx_bytes_total) if rx_bytes_total is not None else None
    tx_total = int(tx_bytes_total) if tx_bytes_total is not None else None
    rx_rate = float(rx_mbps) if rx_mbps is not None else None
    tx_rate = float(tx_mbps) if tx_mbps is not None else None
    total_rate = float(total_mbps) if total_mbps is not None else None
    if total_rate is None and (rx_rate is not None or tx_rate is not None):
        total_rate = float(rx_rate or 0.0) + float(tx_rate or 0.0)
    return rx_total, tx_total, rx_rate, tx_rate, total_rate


def _build_admin_metrics_status_snapshot(*, s, now: datetime, stale_after_seconds: int) -> dict[str, Any]:
    nodes = (
        s.query(Node)
        .filter(Node.enabled == True)
        .order_by(Node.weight.desc(), Node.code.asc())
        .all()
    )
    rows: list[dict[str, Any]] = []
    active_alerts: list[dict[str, Any]] = []
    overall_last_sample: datetime | None = None
    overall_age_seconds: int | None = None

    for node in nodes:
        samples = (
            s.query(NodeHealthSample)
            .filter(NodeHealthSample.node_code == str(node.code or ""))
            .order_by(NodeHealthSample.sampled_at.desc(), NodeHealthSample.id.desc())
            .limit(NODE_METRICS_SUSTAINED_SAMPLES)
            .all()
        )
        latest = samples[0] if samples else None
        last_sample_at = getattr(latest, "sampled_at", None) or getattr(node, "last_health_at", None)
        age_seconds = int((now - last_sample_at).total_seconds()) if last_sample_at else None
        alert_kinds = _active_node_metric_alert_kinds(
            samples=samples,
            last_sample_at=last_sample_at,
            stale_after_seconds=stale_after_seconds,
            now=now,
        )
        if not alert_kinds:
            alert_kinds = _node_snapshot_alert_kinds(
                node=node,
                last_sample_at=last_sample_at,
                stale_after_seconds=stale_after_seconds,
                now=now,
            )
        if last_sample_at and (overall_last_sample is None or last_sample_at > overall_last_sample):
            overall_last_sample = last_sample_at
        if age_seconds is not None:
            overall_age_seconds = age_seconds if overall_age_seconds is None else max(overall_age_seconds, age_seconds)
        row = {
            "node_code": str(node.code or ""),
            "code": str(node.code or ""),
            "status": "stale" if "stale_metrics" in alert_kinds else "fresh",
            "freshness_status": "stale" if "stale_metrics" in alert_kinds else "fresh",
            "last_sample_at": _safe_iso(last_sample_at),
            "age_seconds": age_seconds,
            "cpu_percent": float(getattr(latest, "cpu_percent", getattr(node, "cpu_percent", 0.0)) or 0.0),
            "memory_percent": _sample_memory_percent(latest),
            "disk_percent": _sample_disk_percent(latest),
            "network_total_mbps": float(getattr(latest, "network_total_mbps", getattr(node, "network_total_mbps", 0.0)) or 0.0),
            "network_utilization_percent": _network_utilization_percent(
                getattr(latest, "network_total_mbps", getattr(node, "network_total_mbps", 0.0))
            ),
            "active_clients": int(getattr(latest, "active_clients", getattr(node, "active_clients", 0)) or 0),
            "observer_last_push_at": _safe_iso(getattr(node, "observer_last_push_at", None)),
            "observer_is_stale": bool(_observer_is_stale(node, now=now)),
            "alert_kinds": sorted(set(alert_kinds)),
            "alerts": _legacy_node_alerts(alert_kinds),
        }
        rows.append(row)
        for kind in row["alert_kinds"]:
            active_alerts.append(
                {
                    "node_code": row["node_code"],
                    "kind": kind,
                    "status": row["status"],
                    "age_seconds": row["age_seconds"],
                    "last_sample_at": row["last_sample_at"],
                }
            )

    overall_status = "fresh" if rows and all(row["status"] == "fresh" for row in rows) else "stale"
    legacy_alert_counts = {
        "stale_nodes": sum(1 for row in rows if row["freshness_status"] == "stale"),
        "high_cpu_nodes": sum(1 for row in rows if "high_cpu" in row["alerts"]),
        "high_memory_nodes": sum(1 for row in rows if "high_memory" in row["alerts"]),
        "high_disk_nodes": sum(1 for row in rows if "high_disk" in row["alerts"]),
        "high_network_nodes": sum(1 for row in rows if "high_network" in row["alerts"]),
        "high_latency_nodes": sum(1 for row in rows if "high_latency" in row["alerts"]),
        "high_error_rate_nodes": sum(1 for row in rows if "high_error_rate" in row["alerts"]),
        "high_client_density_nodes": sum(1 for row in rows if "high_client_density" in row["alerts"]),
    }
    return {
        "status": overall_status,
        "last_sample_at": _safe_iso(overall_last_sample),
        "age_seconds": overall_age_seconds,
        "stale_after_seconds": stale_after_seconds,
        "nodes": rows,
        "active_alerts": active_alerts,
        "node_statuses": rows,
        "alerts": legacy_alert_counts,
    }


@app.get("/api/admin/metrics/status")
async def admin_metrics_status(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data, request=request)
    stale_after_seconds = max(300, int(os.getenv("NODE_METRICS_STALE_AFTER_SECONDS", "900")))
    now = _utcnow()
    s = SessionLocal()
    try:
        return _build_admin_metrics_status_snapshot(
            s=s,
            now=now,
            stale_after_seconds=stale_after_seconds,
        )
    finally:
        s.close()


def _parse_admin_datetime(value: str | None) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def _admin_metrics_range(from_value: str | None, to_value: str | None, *, max_days: int = 120) -> tuple[datetime, datetime]:
    now = _utcnow()
    to_dt = _parse_admin_datetime(to_value) or now
    from_dt = _parse_admin_datetime(from_value) or (to_dt - timedelta(days=13))
    if from_dt > to_dt:
        from_dt, to_dt = to_dt, from_dt
    if (to_dt - from_dt).days > max_days:
        from_dt = to_dt - timedelta(days=max_days)
    from_dt = from_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    to_dt = to_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return from_dt, to_dt


def _date_key(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    return text[:10]


def _quality_badge(status: str) -> str:
    status_norm = str(status or "").strip().lower()
    if status_norm in {"fresh", "ok"}:
        return "good"
    if status_norm == "missing":
        return "bad"
    return "warn"


@app.get("/api/admin/nodes/traffic")
async def admin_nodes_traffic(
    x_telegram_init_data: str = Header(default=""),
    from_: str = Query(default="", alias="from"),
    to: str = Query(default="", alias="to"),
) -> dict:
    _require_admin(x_telegram_init_data)
    from_dt, to_dt = _admin_metrics_range(from_, to)
    s = SessionLocal()
    try:
        rows = (
            s.query(
                func.date(NodeHealthSample.sampled_at).label("day"),
                NodeHealthSample.node_code.label("node_code"),
                func.max(NodeHealthSample.active_clients).label("devices"),
                (
                    func.max(func.coalesce(NodeHealthSample.total_traffic_bytes, 0))
                    - func.min(func.coalesce(NodeHealthSample.total_traffic_bytes, 0))
                ).label("traffic_bytes"),
            )
            .filter(NodeHealthSample.sampled_at >= from_dt, NodeHealthSample.sampled_at <= to_dt)
            .group_by(func.date(NodeHealthSample.sampled_at), NodeHealthSample.node_code)
            .order_by(func.date(NodeHealthSample.sampled_at).asc(), NodeHealthSample.node_code.asc())
            .all()
        )
        payload_rows = []
        for row in rows:
            day_key = _date_key(getattr(row, "day", None))
            if not day_key:
                continue
            traffic_bytes = int(getattr(row, "traffic_bytes", 0) or 0)
            payload_rows.append(
                {
                    "date": day_key,
                    "node_code": str(getattr(row, "node_code", "") or ""),
                    "devices": int(getattr(row, "devices", 0) or 0),
                    "traffic_bytes": max(0, traffic_bytes),
                    "traffic_gb": round(max(0, traffic_bytes) / float(1024**3), 3),
                }
            )
        return {
            "from": from_dt.date().isoformat(),
            "to": to_dt.date().isoformat(),
            "rows": payload_rows,
        }
    finally:
        s.close()


@app.get("/api/admin/metrics/timeseries")
async def admin_metrics_timeseries(
    x_telegram_init_data: str = Header(default=""),
    from_: str = Query(default="", alias="from"),
    to: str = Query(default="", alias="to"),
) -> dict:
    _require_admin(x_telegram_init_data)
    from_dt, to_dt = _admin_metrics_range(from_, to)

    days: list[str] = []
    cursor = from_dt.date()
    to_day = to_dt.date()
    while cursor <= to_day:
        days.append(cursor.isoformat())
        cursor = cursor + timedelta(days=1)

    s = SessionLocal()
    try:
        registration_rows = (
            s.query(func.date(User.created_at).label("day"), func.count(User.tg_id).label("value"))
            .filter(User.created_at.isnot(None), User.created_at >= from_dt, User.created_at <= to_dt)
            .group_by(func.date(User.created_at))
            .all()
        )
        registrations_map = {_date_key(getattr(row, "day", None)): int(getattr(row, "value", 0) or 0) for row in registration_rows}

        churn_rows = (
            s.query(func.date(Event.created_at).label("day"), func.count(func.distinct(Event.tg_id)).label("value"))
            .filter(Event.created_at >= from_dt, Event.created_at <= to_dt)
            .filter(Event.event_name == "expired")
            .group_by(func.date(Event.created_at))
            .all()
        )
        churn_map = {_date_key(getattr(row, "day", None)): int(getattr(row, "value", 0) or 0) for row in churn_rows}

        stars_rows = (
            s.query(func.date(PayAttempt.paid_at).label("day"), func.sum(PayAttempt.amount_stars).label("value"))
            .filter(PayAttempt.paid_at.isnot(None), PayAttempt.paid_at >= from_dt, PayAttempt.paid_at <= to_dt)
            .filter(func.lower(func.coalesce(PayAttempt.status, "")) == "paid")
            .group_by(func.date(PayAttempt.paid_at))
            .all()
        )
        stars_map = {_date_key(getattr(row, "day", None)): int(getattr(row, "value", 0) or 0) for row in stars_rows}

        rub_rows = (
            s.query(func.date(ExternalOrder.paid_at).label("day"), func.sum(ExternalOrder.amount).label("value"))
            .filter(ExternalOrder.paid_at.isnot(None), ExternalOrder.paid_at >= from_dt, ExternalOrder.paid_at <= to_dt)
            .filter(func.lower(func.coalesce(ExternalOrder.status, "")) == "paid")
            .filter(func.lower(func.coalesce(ExternalOrder.provider, "")) == "freekassa")
            .group_by(func.date(ExternalOrder.paid_at))
            .all()
        )
        rub_map = {_date_key(getattr(row, "day", None)): round(float(getattr(row, "value", 0.0) or 0.0), 2) for row in rub_rows}

        node_rows = (
            s.query(
                func.date(NodeHealthSample.sampled_at).label("day"),
                NodeHealthSample.node_code.label("node_code"),
                func.max(NodeHealthSample.active_clients).label("devices"),
                (
                    func.max(func.coalesce(NodeHealthSample.total_traffic_bytes, 0))
                    - func.min(func.coalesce(NodeHealthSample.total_traffic_bytes, 0))
                ).label("traffic_bytes"),
            )
            .filter(NodeHealthSample.sampled_at >= from_dt, NodeHealthSample.sampled_at <= to_dt)
            .group_by(func.date(NodeHealthSample.sampled_at), NodeHealthSample.node_code)
            .all()
        )
        nodes_by_day: dict[str, dict[str, dict[str, Any]]] = {}
        for row in node_rows:
            day_key = _date_key(getattr(row, "day", None))
            if not day_key:
                continue
            node_code = str(getattr(row, "node_code", "") or "")
            if not node_code:
                continue
            day_bucket = nodes_by_day.setdefault(day_key, {})
            traffic_bytes = int(getattr(row, "traffic_bytes", 0) or 0)
            day_bucket[node_code] = {
                "devices": int(getattr(row, "devices", 0) or 0),
                "traffic_bytes": max(0, traffic_bytes),
                "traffic_gb": round(max(0, traffic_bytes) / float(1024**3), 3),
            }

        points = [
            {
                "date": day,
                "registrations": int(registrations_map.get(day, 0)),
                "churn": int(churn_map.get(day, 0)),
                "revenue_stars": int(stars_map.get(day, 0)),
                "revenue_rub": float(rub_map.get(day, 0.0)),
                "nodes": nodes_by_day.get(day, {}),
            }
            for day in days
        ]

        return {
            "from": from_dt.date().isoformat(),
            "to": to_dt.date().isoformat(),
            "points": points,
        }
    finally:
        s.close()


@app.get("/api/reviews")
async def featured_reviews() -> dict:
    s = SessionLocal()
    try:
        rows = s.query(Review).filter_by(is_featured=True).order_by(Review.created_at.desc()).limit(10).all()
        reviews = []
        for row in rows:
            text_value = _normalize_feedback_text(row.text, max_len=500)
            if not text_value:
                continue
            reviews.append(
                {
                    "username": _mask_public_username(row.username),
                    "rating": int(row.rating or 0),
                    "text": text_value,
                    "date": row.created_at.strftime("%d.%m.%Y") if row.created_at else "",
                }
            )
        return {
            "reviews": reviews,
            "updated_at": _utcnow().isoformat() + "Z",
        }
    finally:
        s.close()


@app.get("/api/public/social-proof")
async def public_social_proof(response: Response) -> dict:
    """
    Public aggregate counter for marketing surfaces.
    No personal data is exposed.
    """
    s = SessionLocal()
    try:
        total_users = int(s.query(func.count(User.tg_id)).scalar() or 0)
        active_users = int(s.query(func.count(User.tg_id)).filter(User.is_active == True).scalar() or 0)
        paid_users = int(s.query(func.count(User.tg_id)).filter(func.upper(User.sub_type) == "PAID").scalar() or 0)
        connected_users = max(total_users, active_users)
        response.headers["Cache-Control"] = "public, max-age=60"
        return {
            "connected_users": int(connected_users),
            "total_users": int(total_users),
            "active_users": int(active_users),
            "paid_users": int(paid_users),
            "summary": {
                "source": "backend_account_rows",
                "precision": "aggregate",
                "description": "Агрегатная статистика по аккаунтам, без персональных данных.",
            },
            "updated_at": _utcnow().isoformat(),
        }
    finally:
        s.close()


@app.post("/api/events")
async def api_track_event(payload: EventIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    event_name = (payload.event_name or "").strip()
    if event_name not in EVENT_WHITELIST:
        raise HTTPException(status_code=400, detail="Unsupported event name")
    event_id = track_event(
        tg_id=tg_id,
        event_name=event_name,
        source=(payload.source or "webapp"),
        session_id=payload.session_id,
        meta=payload.meta or {},
    )
    return {"ok": bool(event_id), "event_id": event_id}


@app.post("/api/connect/confirm")
async def api_connect_confirm(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    event_id = track_event(tg_id=tg_id, event_name="connected_ok", source="webapp")
    return {"ok": bool(event_id), "event_id": event_id}


@app.post("/api/pay/attempts/start")
async def api_pay_attempt_start(payload: PayAttemptStartIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    plan_code = (payload.plan_code or "").strip().lower()
    if plan_code not in API_PLAN_PRICES:
        raise HTTPException(status_code=400, detail="Unknown plan")
    price = int(API_PLAN_PRICES[plan_code])
    row = start_attempt(
        tg_id=tg_id,
        source=(payload.source or "webapp"),
        plan_code=plan_code,
        amount_stars=price,
        offer_id=payload.offer_id,
        currency="XTR",
    )
    if not row:
        raise HTTPException(status_code=500, detail="Unable to create pay attempt")
    bot_link = f"https://t.me/{BOT_USERNAME}?start=pay" if BOT_USERNAME else ""
    track_event(
        tg_id=tg_id,
        event_name="clicked_pay",
        source=(payload.source or "webapp"),
        meta={"attempt_id": int(row.id), "plan_code": plan_code, "price_stars": price, "offer_id": payload.offer_id},
    )
    return {"ok": True, "attempt_id": int(row.id), "plan_code": plan_code, "amount_stars": price, "pay_url": bot_link}


@app.get("/api/offers/active")
async def api_active_offer(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    return {"offer": _active_offer_payload(tg_id)}


@app.post("/api/offers/{offer_id}/accept")
async def api_accept_offer(offer_id: int, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    ok = accept_offer(offer_id=int(offer_id), tg_id=tg_id)
    if ok:
        track_event(tg_id=tg_id, event_name="clicked_pay", source="offer", meta={"offer_id": int(offer_id)})
    return {"ok": bool(ok)}


@app.get("/api/points")
async def api_points(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    avail, expiring_soon = available_points(tg_id=tg_id)
    tier = referral_tier_snapshot(tg_id=tg_id)
    max_preview = preview_redeemable_points(tg_id=tg_id, plan_price_stars=API_PLAN_PRICES["1_month"], first_purchase_discount_pct=0.20)
    return {
        "tg_id": tg_id,
        "available_points": int(avail),
        "expiring_soon_points": int(expiring_soon),
        "monthly_cap": int(POINTS_MONTHLY_CAP),
        "points_expiry_days": int(POINTS_EXPIRY_DAYS),
        "tier": tier,
        "preview": {
            "plan_price_stars": API_PLAN_PRICES["1_month"],
            "redeemable_points": int(max_preview.redeemable_points),
            "max_points_by_plan_cap": int(max_preview.max_points_by_plan_cap),
            "max_points_by_total_cap": int(max_preview.max_points_by_total_cap),
        },
    }


@app.get("/api/network/probe")
async def api_network_probe(size_mb: int = Query(default=2, ge=1, le=3)) -> Response:
    size = int(size_mb) * 1024 * 1024
    payload = b"0" * size
    return Response(
        content=payload,
        media_type="application/octet-stream",
        headers={
            "Cache-Control": "no-store",
            "Content-Length": str(size),
            "X-Probe-Size-MB": str(int(size_mb)),
        },
    )


@app.get("/api/user/{tg_id}")
async def user_data(
    tg_id: int,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
    x_portal_carrier: str = Header(default=""),
) -> dict:
    auth_user = _require_user_access(target_tg_id=tg_id, x_telegram_init_data=x_telegram_init_data, request=request)

    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        downgraded = _maybe_downgrade_expired_to_free(s, user)
        if downgraded:
            try:
                s.refresh(user)
            except Exception:
                pass
        _ensure_free_cycle_state_persisted(s, user)

        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        subscription_url = ""
        if user.sub_token:
            subscription_url = build_subscription_url(str(user.sub_token or ""))

        # active check (DB-first)
        is_active = bool(user.is_active)
        if user.expiry_at and user.expiry_at < _utcnow():
            is_active = False

        # optional legacy usage
        usage = await _get_panel_usage_legacy(tg_id)
        if usage and not usage.get("enable", True):
            is_active = False

        segment = _plan_segment(user)
        family_slots = _family_slots_for_user(s, tg_id)
        points_available, points_expiring_soon = available_points(tg_id=tg_id)
        runtime = await _get_user_runtime_summary(s=s, user=user, nodes=nodes_for_user)
        runtime_used_bytes = int(runtime.get("traffic_total_bytes", 0) or 0)
        legacy_used_bytes = int(usage["used_bytes"] or 0) if usage else 0
        traffic_source = "panel_runtime" if runtime.get("panel_state") == "ok" and (runtime_used_bytes > 0 or int(runtime.get("known_nodes", 0) or 0) > 0) else "legacy_panel" if usage else "unavailable"
        used_bytes = runtime_used_bytes if traffic_source == "panel_runtime" else legacy_used_bytes
        access_policy = _build_access_policy(user=user, used_bytes=used_bytes)
        setattr(user, "_free_soft_mode_active", bool(access_policy["soft_mode_active"]))
        total_gb = _plan_total_gb(user)
        used_gb = round((used_bytes / (1024**3)), 3) if used_bytes else 0
        remaining_gb = max(round(total_gb - used_gb, 3), 0) if total_gb > 0 else 0
        referral_code = (user.referral_code or "").strip()
        channel_link = f"https://t.me/{PUBLIC_CHANNEL}" if PUBLIC_CHANNEL else ""
        support_link = f"https://t.me/{SUPPORT_USERNAME}" if SUPPORT_USERNAME else ""
        role_admin = _is_admin_tg(tg_id)
        channel_claimed_at = _safe_iso(getattr(user, "channel_bonus_claimed_at", None))
        opening_bonus_claimed = _has_campaign_mark(
            s,
            tg_id=tg_id,
            campaign_key=OPENING_PREMIUM_CAMPAIGN_KEY,
        )
        can_claim_channel_bonus = bool(
            PUBLIC_CHANNEL
            and not channel_claimed_at
            and not opening_bonus_claimed
            and (user.sub_type or "").upper() != "MANUAL"
        )
        free_speed_kbps = _effective_free_speed_kbps(user)
        free_speed_mbps = int(round((free_speed_kbps * 8) / 1000)) if (user.sub_type or "").upper() == "FREE" else None
        is_channel_subscriber = _user_has_channel_subscriber_mark(user)
        speed_bump_active = bool(
            CHANNEL_SPEED_BUMP_ENABLED
            and (user.sub_type or "").upper() == "FREE"
            and free_speed_kbps < int(FREE_SPEED_LIMIT_KBPS)
        )
        devices_payload = _build_app_device_rows(user)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
            carrier=_request_carrier_header(x_portal_carrier),
        )

        return {
            "tg_id": tg_id,
            "username": user.username or auth_user.get("username"),
            "account_id": str(tg_id),
            "device_name": _normalize_app_device_name(
                getattr(user, "app_device_name", None) or getattr(user, "display_name", None),
            ),
            "subscription_url": subscription_url,
            "is_active": is_active,
            "is_admin": role_admin,
            "sub_type": user.sub_type,
            "current_plan_code": str(getattr(user, "current_plan_code", "") or ""),
            "access_state": str(access_policy["access_state"]),
            "segment": segment,
            "expiry_at": user.expiry_at.isoformat() if user.expiry_at else None,
            "traffic_policy": access_policy["traffic_policy"],
            "traffic_limit_gb": access_policy["traffic_limit_gb"],
            "traffic_remaining_gb": access_policy["traffic_remaining_gb"],
            "next_reset_at": access_policy["next_reset_at"],
            "soft_mode_active": bool(access_policy["soft_mode_active"]),
            "limits": {
                "device_limit": _plan_device_limit(user) + family_slots,
                "total_gb": total_gb,
                "speed_mbps": free_speed_mbps,
            },
            "family_slots": int(family_slots),
            "nodes": [
                {"code": n.code, "name": n.name, "host": n.host, "port": n.vless_port, "enabled": True}
                for n in nodes_for_user
            ],
            "devices": devices_payload,
            "last_ip": str(getattr(user, "app_last_ip", "") or "").strip() or None,
            "linked_telegram": {
                "id": _linked_telegram_id(user) or None,
                "username": str(getattr(user, "linked_telegram_username", "") or "").strip() or None,
            },
            "client_policy": client_policy,
            "linked_identities": _linked_identities_payload(s=s, user=user, auth_user=auth_user),
            "free_caps": _free_caps_payload(user=user, access_policy=access_policy),
            "redeem_eligibility": _redeem_eligibility_payload(user=user, access_policy=access_policy),
            "promo_slots": _promo_slots_payload_for_surface(
                s=s,
                surface="webapp",
                access_state=str(access_policy.get("access_state") or ""),
            ),
            "hidden_transport_matrix": _hidden_transport_matrix_payload(nodes=nodes_for_user, client_policy=client_policy),
            "location_matrix": _location_matrix_payload(user=user, nodes=nodes_for_user, client_policy=client_policy),
            "sync": {
                "app_identity_known": bool(str(getattr(user, "app_install_id", "") or "").strip()),
                "telegram_linked": bool(_linked_telegram_id(user)),
                "subscription_ready": bool(str(getattr(user, "sub_token", "") or "").strip()),
                "device_count": int(len(devices_payload)),
            },
            "traffic": {
                "used_gb": used_gb,
                "used_bytes": int(used_bytes),
                "total_gb": total_gb,
                "remaining_gb": remaining_gb,
                "source": traffic_source,
                "policy": access_policy["traffic_policy"],
            },
            "connections": {
                "status": str(runtime.get("status") or "unknown"),
                "active_connections": int(runtime.get("active_connections", 0) or 0),
                "active_users_estimate": int(runtime.get("active_users_estimate", runtime.get("active_connections", 0)) or 0),
                "active_users_source": str(
                    runtime.get("active_users_source") or runtime.get("active_connections_source") or "none"
                ),
                "active_nodes": int(runtime.get("active_nodes", 0) or 0),
                "known_nodes": int(runtime.get("known_nodes", 0) or 0),
                "last_online_at": runtime.get("last_online_at"),
                "last_online_age_seconds": runtime.get("last_online_age_seconds"),
                "source": "panel_runtime" if runtime.get("panel_state") == "ok" else "unavailable",
            },
            "support": {
                "username": SUPPORT_USERNAME,
                "link": support_link,
                "new_ticket_link": f"{support_link}?start=ticket_new" if support_link else "",
            },
            "bonuses": {
                "wheel": {
                    "last_spin_at": _safe_iso(user.last_wheel_spin),
                    "streak_months": int(user.streak_months or 0),
                },
                "referral_count": int(user.referral_count or 0),
                "channel_bonus": {
                    "premium_days": int(CHANNEL_PREMIUM_DAYS),
                    "claimed_at": channel_claimed_at,
                    "can_claim": can_claim_channel_bonus,
                },
                "opening_bonus": {
                    "premium_days": int(OPENING_PREMIUM_DAYS),
                    "claimed": bool(opening_bonus_claimed),
                },
            },
            "points": {
                "available": int(points_available),
                "expiring_soon": int(points_expiring_soon),
                "monthly_cap": 300,
                "expires_days": 90,
            },
            "referral": {
                "code": referral_code,
                "link": (
                    f"https://t.me/{BOT_USERNAME}?start=ref_{referral_code}"
                    if referral_code and BOT_USERNAME
                    else ""
                ),
                "bonus_days": REFERRAL_BONUS_DAYS,
            },
            "channel": {
                "username": PUBLIC_CHANNEL,
                "link": channel_link,
                "subscriber": bool(is_channel_subscriber),
                "speed_bump_active": speed_bump_active,
            },
            "actions": {
                "open_helpbot": support_link,
                "open_channel": channel_link,
                "pay_via_bot": _checkout_url_for_user(
                    tg_id=tg_id,
                    plan_code=str(getattr(user, "current_plan_code", "") or ""),
                    source="bot",
                ),
            },
            "active_offer": _active_offer_payload(tg_id),
            "free_cycle": {
                "next_reset_at": _safe_iso(getattr(user, "free_cycle_next_reset_at", None))
                if (user.sub_type or "").upper() == "FREE"
                else None,
            },
            "features": {
                "haptic": bool(WEBAPP_ENABLE_HAPTIC),
                "lottie": bool(WEBAPP_ENABLE_LOTTIE),
            },
        }
    finally:
        s.close()


@app.get("/api/dashboard")
async def dashboard_snapshot(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
    x_portal_carrier: str = Header(default=""),
) -> DashboardResponse:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        _maybe_downgrade_expired_to_free(s, user)
        _ensure_free_cycle_state_persisted(s, user)
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        runtime = await _get_user_runtime_summary(s=s, user=user, nodes=nodes_for_user)
        usage = await _get_panel_usage_legacy(tg_id)
        runtime_used_bytes = int(runtime.get("traffic_total_bytes", 0) or 0)
        legacy_used_bytes = int(usage["used_bytes"] or 0) if usage else 0
        traffic_source = "panel_runtime" if runtime.get("panel_state") == "ok" and (runtime_used_bytes > 0 or int(runtime.get("known_nodes", 0) or 0) > 0) else "legacy_panel" if usage else "unavailable"
        used_bytes = runtime_used_bytes if traffic_source == "panel_runtime" else legacy_used_bytes
        access_policy = _build_access_policy(user=user, used_bytes=used_bytes)
        setattr(user, "_free_soft_mode_active", bool(access_policy["soft_mode_active"]))
        total_gb = float(_plan_total_gb(user))
        used_gb = round((used_bytes / (1024**3)), 3) if used_bytes else 0.0
        remaining = max(round(total_gb - used_gb, 3), 0.0) if total_gb > 0 else 0.0
        expiry = user.expiry_at
        active = bool(user.is_active and expiry and expiry > _utcnow())
        segment = _plan_segment(user)
        family_slots = _family_slots_for_user(s, tg_id)
        points_available, points_expiring_soon = available_points(tg_id=tg_id)
        sub_url = ""
        if user.sub_token:
            sub_url = build_subscription_url(str(user.sub_token or ""))
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
            carrier=_request_carrier_header(x_portal_carrier),
        )

        return DashboardResponse(
            tg_id=tg_id,
            sub_type=str(user.sub_type or ""),
            current_plan_code=str(getattr(user, "current_plan_code", "") or ""),
            access_state=str(access_policy["access_state"]),
            is_active=active,
            expiry_at=_safe_iso(expiry),
            used_gb=float(used_gb),
            total_gb=float(total_gb),
            remaining_gb=float(remaining),
            traffic_policy=access_policy["traffic_policy"],
            traffic_limit_gb=access_policy["traffic_limit_gb"],
            traffic_remaining_gb=access_policy["traffic_remaining_gb"],
            next_reset_at=access_policy["next_reset_at"],
            soft_mode_active=bool(access_policy["soft_mode_active"]),
            active_sessions=int(runtime.get("active_connections", 0) or 0),
            active_sessions_source=str(runtime.get("active_connections_source") or "none"),
            device_limit=int(_plan_device_limit(user) + family_slots),
            speed_limit_mbps=(
                int(round((_effective_free_speed_kbps(user) * 8) / 1000))
                if (user.sub_type or "").upper() == "FREE"
                else None
            ),
            free_next_reset_at=(
                _safe_iso(getattr(user, "free_cycle_next_reset_at", None))
                if (user.sub_type or "").upper() == "FREE"
                else None
            ),
            family_slots=int(family_slots),
            subscription_url=sub_url,
            segment=segment,
            client_policy=client_policy,
            linked_identities=_linked_identities_payload(s=s, user=user, auth_user=auth_user),
            free_caps=_free_caps_payload(user=user, access_policy=access_policy),
            redeem_eligibility=_redeem_eligibility_payload(user=user, access_policy=access_policy),
            promo_slots=_promo_slots_payload_for_surface(
                s=s,
                surface="webapp",
                access_state=str(access_policy.get("access_state") or ""),
            ),
            hidden_transport_matrix=_hidden_transport_matrix_payload(nodes=nodes_for_user, client_policy=client_policy),
            location_matrix=_location_matrix_payload(user=user, nodes=nodes_for_user, client_policy=client_policy),
            connection_snapshot={
                "status": str(runtime.get("status") or "unknown"),
                "active_connections": int(runtime.get("active_connections", 0) or 0),
                "active_users_estimate": int(runtime.get("active_users_estimate", runtime.get("active_connections", 0)) or 0),
                "active_users_source": str(
                    runtime.get("active_users_source") or runtime.get("active_connections_source") or "none"
                ),
                "active_nodes": int(runtime.get("active_nodes", 0) or 0),
                "known_nodes": int(runtime.get("known_nodes", 0) or 0),
                "last_online_at": runtime.get("last_online_at"),
                "last_online_age_seconds": runtime.get("last_online_age_seconds"),
                "source": "panel_runtime" if runtime.get("panel_state") == "ok" else "unavailable",
            },
            active_offer=_active_offer_payload(tg_id),
            points={
                "available": int(points_available),
                "expiring_soon": int(points_expiring_soon),
                "monthly_cap": 300,
                "expires_days": 90,
            },
            features={"haptic": bool(WEBAPP_ENABLE_HAPTIC), "lottie": bool(WEBAPP_ENABLE_LOTTIE)},
        )
    finally:
        s.close()


@app.get("/api/client/apps")
async def client_apps(request: Request, x_telegram_init_data: str = Header(default="")) -> ClientAppsResponse:
    _require_auth_user(x_telegram_init_data, request=request)
    return ClientAppsResponse(
        android=ClientAndroidApps(
            play_url=_safe_public_url(Settings.APP_ANDROID_PLAY_URL),
            apk_url=_safe_public_url(Settings.APP_ANDROID_APK_URL),
            mirror_url=_safe_public_url(Settings.APP_ANDROID_MIRROR_URL),
        ),
        windows=ClientWindowsApps(
            exe_url=_safe_public_url(Settings.APP_WINDOWS_EXE_URL),
            mirror_url=_safe_public_url(Settings.APP_WINDOWS_MIRROR_URL),
        ),
        docs_url=_safe_public_url(Settings.APP_DOCS_URL),
        updated_at=f"{_utcnow().replace(microsecond=0).isoformat()}Z",
    )


@app.get("/api/nodes/status")
async def nodes_status(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        rows = _nodes_for_user(user, enabled_nodes(s), session=s)
        payload: list[dict[str, Any]] = []
        for n in rows:
            ping = _safe_ping(n)
            payload.append(
                NodeStatusResponse(
                    code=str(getattr(n, "code", "")),
                    country=_node_country_name(str(getattr(n, "code", ""))),
                    host=str(getattr(n, "host", "")),
                    ping_ms=ping,
                    port_open=bool(getattr(n, "is_healthy", True)),
                    dns_sni_status="ok" if bool(getattr(n, "is_healthy", True)) else "degraded",
                    is_healthy=bool(getattr(n, "is_healthy", True)),
                    updated_at=_safe_iso(getattr(n, "last_health_at", None)),
                ).model_dump()
            )
        return {"nodes": payload}
    finally:
        s.close()


@app.post("/api/nodes/diagnostics/run")
async def nodes_run_diagnostics(request: Request, x_telegram_init_data: str = Header(default="")) -> NodeDiagnosticsResponse:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    now_ts = time.time()
    last_ts = _diag_rate_limit.get(tg_id, 0.0)
    if now_ts - last_ts < 8.0:
        raise HTTPException(status_code=429, detail="Too many diagnostics requests")
    _diag_rate_limit[tg_id] = now_ts

    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        nodes = _nodes_for_user(user, enabled_nodes(s), session=s)
        healthy = [n for n in nodes if bool(getattr(n, "is_healthy", True))]
    finally:
        s.close()

    ok = bool(healthy) if nodes else False
    return NodeDiagnosticsResponse(
        ok=ok,
        checked_at=_utcnow().isoformat(),
        dns_status="ok" if ok else "degraded",
        sni_status="ok" if ok else "degraded",
        summary="All checks passed" if ok else "Some nodes are degraded",
    )


@app.get("/api/bonuses")
async def bonuses(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        tier = referral_tier_snapshot(tg_id=tg_id)
        return {
            "tg_id": tg_id,
            "referral_count": int(user.referral_count or 0),
            "referral_code": user.referral_code or "",
            "referral_bonus_days": REFERRAL_BONUS_DAYS,
            "streak_months": int(user.streak_months or 0),
            "last_wheel_spin": _safe_iso(user.last_wheel_spin),
            "channel_bonus_premium_days": int(CHANNEL_PREMIUM_DAYS),
            "channel_bonus_claimed_at": _safe_iso(getattr(user, "channel_bonus_claimed_at", None)),
            "opening_bonus_premium_days": int(OPENING_PREMIUM_DAYS),
            "opening_bonus_claimed": _has_campaign_mark(s, tg_id=tg_id, campaign_key=OPENING_PREMIUM_CAMPAIGN_KEY),
            "channel_username": PUBLIC_CHANNEL,
            "points_tier": tier,
        }
    finally:
        s.close()


@app.post("/api/channel/subscriber/check")
async def channel_subscriber_check(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    if not PUBLIC_CHANNEL:
        raise HTTPException(status_code=400, detail="Public channel is not configured")

    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    finally:
        s.close()

    return await channel_bonus_service.build_channel_subscriber_check_response(
        user=user,
        channel_username=PUBLIC_CHANNEL,
        bonus_days=CHANNEL_PREMIUM_DAYS,
        is_channel_member=_is_channel_member,
    )


@app.post("/api/bonuses/channel/claim")
async def claim_channel_bonus(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    if not PUBLIC_CHANNEL:
        raise HTTPException(status_code=400, detail="Public channel is not configured")

    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        result = await channel_bonus_service.claim_channel_bonus(
            s=s,
            user=user,
            tg_id=tg_id,
            public_channel=PUBLIC_CHANNEL,
            bonus_days=CHANNEL_PREMIUM_DAYS,
            opening_bonus_campaign_key=OPENING_PREMIUM_CAMPAIGN_KEY,
            subscriber_campaign_key=CHANNEL_SUBSCRIBER_CAMPAIGN_KEY,
            points_expiry_days=POINTS_EXPIRY_DAYS,
            is_channel_member=_is_channel_member,
            sync_user_after_paid_bonus=_sync_user_after_paid_bonus,
        )
        return result
    finally:
        s.close()


@app.post("/api/promo/redeem")
async def promo_redeem(payload: PromoRedeemIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    code = (payload.code or "").strip().upper()
    if not code:
        _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={"reason": "empty_code"})
        raise HTTPException(status_code=400, detail="Promo code is required")

    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={"code": code, "reason": "user_not_found"})
            raise HTTPException(status_code=404, detail="User not found")
        if not bool(getattr(user, "tos_accepted", False)):
            _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={"code": code, "reason": "tos_required"})
            raise HTTPException(status_code=400, detail="Сначала примите оферту в боте (/start)")
        promo = s.query(PromoCode).filter(func.upper(PromoCode.code) == code).first()
        if not promo:
            _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={"code": code, "reason": "not_found"})
            raise HTTPException(status_code=404, detail="Promo not found")
        active_campaigns_for_code = (
            s.query(func.count(IncentiveCampaign.id))
            .filter(func.lower(IncentiveCampaign.campaign_type) == "promo")
            .filter(func.upper(IncentiveCampaign.target_value) == code)
            .filter(IncentiveCampaign.is_active == True)
            .scalar()
            or 0
        )
        campaign = _campaign_lookup(
            s=s,
            campaign_type="promo",
            target_value=code,
            user=user,
            now=_utcnow(),
        )
        if int(active_campaigns_for_code) > 0 and campaign is None:
            _track_bonus_event(
                tg_id=tg_id,
                event_name="promo_redeem_denied",
                meta={"code": code, "reason": "campaign_restriction_mismatch"},
            )
            raise HTTPException(status_code=403, detail="Promo campaign restrictions mismatch for this user")
        uses_left = int(promo.uses_left or 0)
        if uses_left == 0:
            _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={"code": code, "reason": "exhausted"})
            raise HTTPException(status_code=400, detail="Promo exhausted")
        if promo.expires_at and promo.expires_at < _utcnow():
            _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={"code": code, "reason": "expired"})
            raise HTTPException(status_code=400, detail="Promo expired")
        used = s.query(PromoUsage).filter_by(tg_id=tg_id, promo_code=promo.code).first()
        if used:
            _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={"code": code, "reason": "already_redeemed"})
            raise HTTPException(status_code=400, detail="Promo already redeemed")

        promo_type = (promo.promo_type or "").strip().lower()
        value = int(promo.value or 0)
        if promo_type not in {"days", "discount"} or value <= 0:
            _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={"code": code, "reason": "invalid_value"})
            raise HTTPException(status_code=400, detail="Promo has invalid value")
        applied_days = 0
        pending_discount_pct = 0
        if promo_type == "days":
            now = _utcnow()
            if user.expiry_at and user.expiry_at > now:
                user.expiry_at = user.expiry_at + timedelta(days=value)
            else:
                user.expiry_at = now + timedelta(days=value)
            user.is_active = True
            applied_days = value
        elif promo_type == "discount":
            user.pending_discount_pct = max(1, min(95, int(value)))
            user.pending_discount_code = str(promo.code or "").strip().upper()[:20]
            user.pending_discount_set_at = _utcnow()
            pending_discount_pct = int(user.pending_discount_pct or 0)

        if uses_left > 0:
            updated = (
                s.query(PromoCode)
                .filter(PromoCode.id == promo.id, PromoCode.uses_left > 0)
                .update({PromoCode.uses_left: PromoCode.uses_left - 1}, synchronize_session=False)
            )
            if int(updated or 0) != 1:
                s.rollback()
                raise HTTPException(status_code=400, detail="Promo exhausted")
            s.flush()
            s.refresh(promo)

        s.add(PromoUsage(tg_id=tg_id, promo_code=promo.code))
        _campaign_consume(s=s, row=campaign)
        try:
            s.commit()
        except IntegrityError:
            s.rollback()
            _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={"code": code, "reason": "already_redeemed"})
            raise HTTPException(status_code=400, detail="Promo already redeemed")
        _track_bonus_event(
            tg_id=tg_id,
            event_name="promo_redeemed",
            meta={
                "code": str(promo.code or ""),
                "promo_type": promo_type,
                "value": int(value),
                "applied_days": int(applied_days),
                "pending_discount_pct": int(pending_discount_pct),
            },
        )
        return {
            "ok": True,
            "code": promo.code,
            "promo_type": promo_type,
            "value": value,
            "applied_days": applied_days,
            "pending_discount_pct": int(pending_discount_pct),
            "uses_left": int(promo.uses_left or 0),
        }
    finally:
        s.close()


@app.post("/api/gift/redeem")
async def gift_redeem(payload: GiftRedeemIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    code = str(payload.code or "").strip().upper()
    if not code:
        _track_bonus_event(tg_id=tg_id, event_name="gift_redeem_denied", meta={"reason": "invalid_code"})
    if code:
        s = SessionLocal()
        try:
            user = s.query(User).filter(User.tg_id == int(tg_id)).first()
            card = s.query(GiftCard).filter(func.upper(GiftCard.code) == code).first()
            if user and card:
                card_type = str(card.card_type or "").strip().upper()
                active_campaigns_for_type = (
                    s.query(func.count(IncentiveCampaign.id))
                    .filter(func.lower(IncentiveCampaign.campaign_type) == "gift")
                    .filter(func.upper(IncentiveCampaign.target_value) == card_type)
                    .filter(IncentiveCampaign.is_active == True)
                    .scalar()
                    or 0
                )
                campaign = _campaign_lookup(
                    s=s,
                    campaign_type="gift",
                    target_value=card_type,
                    user=user,
                    now=_utcnow(),
                )
                if int(active_campaigns_for_type) > 0 and campaign is None:
                    _track_bonus_event(
                        tg_id=tg_id,
                        event_name="gift_redeem_denied",
                        meta={"code": code, "card_type": card_type, "reason": "campaign_restriction_mismatch"},
                    )
                    raise HTTPException(status_code=403, detail="Gift campaign restrictions mismatch for this user")
        finally:
            s.close()
    result = await redeem_gift_card_service(code=payload.code, recipient_tg_id=tg_id, require_tos=True)
    if result.get("ok"):
        card_type = str(result.get("card_type") or "").strip().upper()
        if card_type:
            s2 = SessionLocal()
            try:
                user2 = s2.query(User).filter(User.tg_id == int(tg_id)).first()
                if user2:
                    campaign2 = _campaign_lookup(s=s2, campaign_type="gift", target_value=card_type, user=user2, now=_utcnow())
                    _campaign_consume(s=s2, row=campaign2)
                    s2.commit()
            except Exception:
                s2.rollback()
            finally:
                s2.close()
        track_event(
            tg_id=tg_id,
            event_name="gift_redeemed",
            source="webapp",
            meta={"code": code, "card_type": result.get("card_type"), "days": result.get("days"), "sync_ok": result.get("sync_ok")},
        )
        return result

    error = str(result.get("error") or "redeem_failed")
    message = str(result.get("message") or "Не удалось активировать код")
    _track_bonus_event(tg_id=tg_id, event_name="gift_redeem_denied", meta={"code": code, "reason": error})
    status_map = {
        "invalid_code": 400,
        "not_found": 404,
        "already_redeemed": 400,
        "self_redeem": 400,
        "tos_required": 400,
    }
    raise HTTPException(status_code=status_map.get(error, 400), detail=message)


@app.get("/api/access-keys/status/{key}")
async def access_key_status(key: str) -> dict[str, Any]:
    code = str(key or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Access key is required")
    s = SessionLocal()
    try:
        card = s.query(GiftCard).filter(func.upper(GiftCard.code) == code).first()
        if not card:
            raise HTTPException(status_code=404, detail="Access key not found")
        payload = _access_key_status_payload(s=s, card=card)
        if payload.get("kind") == "unknown":
            raise HTTPException(status_code=400, detail="Access key type is not supported")
        return payload
    finally:
        s.close()


@app.post("/api/access-keys/redeem")
async def access_key_redeem(
    payload: AccessKeyRedeemIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    code = str(payload.key or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Access key is required")

    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        card = s.query(GiftCard).filter(func.upper(GiftCard.code) == code).first()
        if not card:
            raise HTTPException(status_code=404, detail="Access key not found")
        if card.redeemed_by is not None:
            raise HTTPException(status_code=400, detail="Access key already redeemed")
        if int(card.created_by or 0) == int(tg_id):
            raise HTTPException(status_code=400, detail="You cannot redeem your own key")
        if not bool(getattr(user, "tos_accepted", False)):
            raise HTTPException(status_code=400, detail="Accept terms before redeeming a key")

        meta = _access_key_meta_from_card_type(s=s, card_type=str(card.card_type or ""))
        if not meta:
            raise HTTPException(status_code=400, detail="Access key type is not supported")

        now = _utcnow()
        applied = _apply_access_key_to_user(user=user, meta=meta, now=now)
        updated = (
            s.query(GiftCard)
            .filter(GiftCard.id == int(card.id), GiftCard.redeemed_by.is_(None))
            .update(
                {
                    GiftCard.redeemed_by: int(tg_id),
                    GiftCard.redeemed_at: now,
                },
                synchronize_session=False,
            )
        )
        if int(updated or 0) != 1:
            s.rollback()
            raise HTTPException(status_code=400, detail="Access key already redeemed")

        s.commit()
        s.refresh(user)
        card = s.query(GiftCard).filter(GiftCard.id == int(card.id)).first() or card
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
        )
        access_policy = _build_access_policy(user=user, used_bytes=0)
        linked_identities = _linked_identities_payload(s=s, user=user, auth_user=auth_user)
        promo_slots = _promo_slots_payload_for_surface(
            s=s,
            surface="webapp",
            access_state=str(access_policy.get("access_state") or ""),
        )
        key_status = _access_key_status_payload(s=s, card=card)
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        logger.exception("access key redeem failed key=%s tg_id=%s", code, int(tg_id))
        raise HTTPException(status_code=500, detail="Failed to redeem access key")
    finally:
        s.close()

    sync_ok = await _sync_control_panel_access(user=user)
    try:
        track_event(
            tg_id=int(tg_id),
            event_name="access_key_redeemed",
            source="webapp",
            meta={"code": code, "plan_code": key_status.get("plan", {}).get("code"), "sync_ok": bool(sync_ok)},
        )
    except Exception:
        logger.exception("failed to track access_key_redeemed tg_id=%s", int(tg_id))

    return {
        "ok": True,
        "key": code,
        "status": key_status,
        "plan": key_status.get("plan"),
        "access": {
            **access_policy,
            "sub_type": str(getattr(user, "sub_type", "") or ""),
            "current_plan_code": applied.get("current_plan_code"),
            "expiry_at": applied.get("expiry_at"),
        },
        "linked_identities": linked_identities,
        "free_caps": _free_caps_payload(user=user, access_policy=access_policy),
        "redeem_eligibility": _redeem_eligibility_payload(user=user, access_policy=access_policy),
        "promo_slots": promo_slots,
        "hidden_transport_matrix": _hidden_transport_matrix_payload(nodes=nodes_for_user, client_policy=client_policy),
        "location_matrix": _location_matrix_payload(user=user, nodes=nodes_for_user, client_policy=client_policy),
        "provisioning": {
            "sync_ok": bool(sync_ok),
            "managed_profile_path": "/api/client/profile/managed",
            "dashboard_path": "/api/dashboard",
        },
    }


@app.post("/api/reviews")
async def create_review(payload: ReviewCreateIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        db_user = s.query(User).filter_by(tg_id=tg_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        review_text = _normalize_feedback_text(payload.text, max_len=500)
        if len(review_text) < 3:
            raise HTTPException(status_code=400, detail="Review text is too short")
        row = Review(
            tg_id=tg_id,
            username=db_user.username or db_user.linked_telegram_username or auth_user.get("username"),
            rating=int(payload.rating),
            text=review_text,
            is_featured=False,
        )
        s.add(row)
        s.commit()
        return {"ok": True, "review_id": row.id}
    finally:
        s.close()


@app.post("/api/feedback")
async def create_feedback(payload: FeedbackCreateIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        db_user = s.query(User).filter_by(tg_id=tg_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        feedback_text = _normalize_feedback_text(payload.text, max_len=1000)
        if len(feedback_text) < 5:
            raise HTTPException(status_code=400, detail="Feedback text is too short")

        review_id = int(payload.review_id or 0) or None
        if review_id is not None:
            review_row = s.query(Review).filter_by(id=review_id, tg_id=tg_id).first()
            if not review_row:
                raise HTTPException(status_code=404, detail="Review not found")

        row = FeedbackEntry(
            tg_id=tg_id,
            username=db_user.username or db_user.linked_telegram_username or auth_user.get("username"),
            category=_normalize_feedback_category(payload.category),
            text=feedback_text,
            status="new",
            source=_normalize_feedback_source(payload.source),
            review_id=review_id,
        )
        s.add(row)
        s.commit()
        return {"ok": True, "feedback_id": row.id, "status": row.status}
    finally:
        s.close()


@app.get("/api/tickets")
async def get_tickets(request: Request, x_telegram_init_data: str = Header(default=""), limit: int = 20) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        items = list_user_tickets(s, tg_id, limit=max(1, min(int(limit), 50)))
        data = []
        for t in items:
            msgs = list_ticket_messages(s, t.id, limit=1)
            data.append(_ticket_row(t, msgs))
        return {"tickets": data}
    finally:
        s.close()


@app.post("/api/tickets/uploads")
async def upload_ticket_attachment(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
    x_upload_filename: str = Header(default=""),
) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    raw_bytes = await request.body()
    uploaded = _store_support_upload(
        filename=x_upload_filename,
        content_type=request.headers.get("content-type"),
        raw_bytes=raw_bytes,
    )
    logger.info(
        "ticket_attachment_uploaded",
        extra={
            "user_id": tg_id,
            "media_type": uploaded["attachment"].get("media_type"),
            "media_file_id": uploaded["attachment"].get("media_file_id"),
            "size": uploaded["attachment_payload"].get("size"),
        },
    )
    return {"ok": True, **uploaded}


@app.post("/api/tickets")
async def create_user_ticket(payload: TicketCreateIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        ticket = get_user_active_ticket(s, tg_id)
        if not ticket:
            ticket = create_ticket(s, user_tg_id=tg_id, subject=payload.subject)
        add_ticket_message(
            s,
            ticket_id=ticket.id,
            sender_tg_id=tg_id,
            sender_role="user",
            body=payload.body,
            media_type=payload.media_type,
            media_file_id=payload.media_file_id,
            media_payload=payload.media_payload,
        )
        set_ticket_status(s, ticket=ticket, status=STATUS_OPEN)
        s.commit()
        msgs = list_ticket_messages(s, ticket.id, limit=20)
    finally:
        s.close()

    if Settings.ADMIN_ID:
        await _telegram_send_message(int(Settings.ADMIN_ID), f"🆕 Новый обращение #{ticket.id} от пользователя {tg_id}.")
    track_event(tg_id=tg_id, event_name="ticket_created", source="webapp", meta={"ticket_id": int(ticket.id)})
    return {"ticket": _ticket_row(ticket, msgs)}


@app.get("/api/tickets/{ticket_id}")
async def get_ticket(ticket_id: int, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    actor = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        ticket = get_ticket_by_id(s, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if not (_is_admin_tg(actor) or int(ticket.user_tg_id) == actor):
            raise HTTPException(status_code=403, detail="Access denied")
        msgs = list_ticket_messages(s, ticket.id, limit=100)
        return {"ticket": _ticket_row(ticket, msgs)}
    finally:
        s.close()


@app.post("/api/tickets/{ticket_id}/messages")
async def add_ticket_user_message(ticket_id: int, payload: TicketMessageIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    actor = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        ticket = get_ticket_by_id(s, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if not (_is_admin_tg(actor) or int(ticket.user_tg_id) == actor):
            raise HTTPException(status_code=403, detail="Access denied")
        role = "admin" if _is_admin_tg(actor) else "user"
        add_ticket_message(
            s,
            ticket_id=ticket.id,
            sender_tg_id=actor,
            sender_role=role,
            body=payload.body,
            media_type=payload.media_type,
            media_file_id=payload.media_file_id,
            media_payload=payload.media_payload,
        )
        set_ticket_status(
            s,
            ticket=ticket,
            status=STATUS_IN_PROGRESS if role == "admin" else STATUS_OPEN,
            assigned_admin_tg_id=int(Settings.ADMIN_ID) if role == "admin" and Settings.ADMIN_ID else None,
        )
        s.commit()
        msgs = list_ticket_messages(s, ticket.id, limit=100)
    finally:
        s.close()

    if role == "admin":
        await _telegram_send_message(int(ticket.user_tg_id), f"💬 Новый ответ оператора в обращении #{ticket.id}.")
    elif Settings.ADMIN_ID:
        await _telegram_send_message(int(Settings.ADMIN_ID), f"🆕 Новое сообщение в обращении #{ticket.id} от {actor}.")
    return {"ticket": _ticket_row(ticket, msgs)}


@app.get("/api/admin/summary")
async def admin_summary(x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    stale_after_seconds = max(300, int(os.getenv("NODE_METRICS_STALE_AFTER_SECONDS", "900")))
    now = _utcnow()
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)
    s = SessionLocal()
    try:
        active_user_filter = _effective_active_user_filter(now=now)
        user_sub_type = func.upper(func.coalesce(User.sub_type, ""))
        user_counts = (
            s.query(
                func.count(User.tg_id).label("total_users"),
                func.sum(case((active_user_filter, 1), else_=0)).label("active_users"),
                func.sum(case((user_sub_type == "FREE", 1), else_=0)).label("free_users"),
                func.sum(case((user_sub_type == "PAID", 1), else_=0)).label("paid_users"),
                func.sum(case((and_(active_user_filter, _premium_entitlement_filter()), 1), else_=0)).label("active_nonfree_accounts"),
                func.sum(case((and_(active_user_filter, _trial_entitlement_filter()), 1), else_=0)).label("trial_accounts"),
                func.sum(case((and_(active_user_filter, _bonus_entitlement_filter()), 1), else_=0)).label("bonus_accounts"),
            )
            .one()
        )
        total_users = int(getattr(user_counts, "total_users", 0) or 0)
        active_users = int(getattr(user_counts, "active_users", 0) or 0)
        free_users = int(getattr(user_counts, "free_users", 0) or 0)
        paid_users = int(getattr(user_counts, "paid_users", 0) or 0)
        active_nonfree_accounts = int(getattr(user_counts, "active_nonfree_accounts", 0) or 0)
        trial_accounts = int(getattr(user_counts, "trial_accounts", 0) or 0)
        bonus_accounts = int(getattr(user_counts, "bonus_accounts", 0) or 0)
        unique_install_ids_total = (
            s.query(func.count(func.distinct(User.app_install_id)))
            .filter(User.tg_id > 0)
            .filter(~_manual_test_user_filter())
            .filter(User.app_install_id.isnot(None))
            .scalar()
            or 0
        )
        unique_install_ids_24h = (
            s.query(func.count(func.distinct(User.app_install_id)))
            .filter(User.tg_id > 0)
            .filter(~_manual_test_user_filter())
            .filter(User.app_install_id.isnot(None))
            .filter(User.app_last_seen_at.isnot(None))
            .filter(User.app_last_seen_at >= since_24h)
            .scalar()
            or 0
        )
        unique_install_ids_7d = (
            s.query(func.count(func.distinct(User.app_install_id)))
            .filter(User.tg_id > 0)
            .filter(~_manual_test_user_filter())
            .filter(User.app_install_id.isnot(None))
            .filter(User.app_last_seen_at.isnot(None))
            .filter(User.app_last_seen_at >= since_7d)
            .scalar()
            or 0
        )
        open_tickets = s.query(func.count(SupportTicket.id)).filter(SupportTicket.status != STATUS_CLOSED).scalar() or 0
        total_nodes = s.query(func.count(Node.id)).filter(Node.enabled == True).scalar() or 0
        healthy_nodes = s.query(func.count(Node.id)).filter(Node.enabled == True, Node.is_healthy == True).scalar() or 0
        free_node_enabled = bool(
            s.query(Node.id).filter(Node.enabled == True, func.lower(func.coalesce(Node.code, "")) == "free").first()
        )
        observer_counts = (
            s.query(
                func.count(ObserverUserState.tg_id).label("total_rows"),
                func.sum(case((ObserverUserState.state == "watch", 1), else_=0)).label("watch_users"),
                func.sum(case((ObserverUserState.state == "suspicious", 1), else_=0)).label("suspicious_users"),
                func.sum(
                    case(
                        (and_(ObserverUserState.last_observed_at.isnot(None), ObserverUserState.last_observed_at >= since_24h), 1),
                        else_=0,
                    )
                ).label("seen_24h"),
            )
            .one()
        )
        observer_watch_users = int(getattr(observer_counts, "watch_users", 0) or 0)
        observer_suspicious_users = int(getattr(observer_counts, "suspicious_users", 0) or 0)
        observer_seen_accounts_24h = int(getattr(observer_counts, "seen_24h", 0) or 0)
        observer_total_rows = int(getattr(observer_counts, "total_rows", 0) or 0)
        observer_secret_filter = func.length(func.trim(func.coalesce(Node.observer_push_secret, ""))) > 0
        observer_configured_nodes = (
            s.query(func.count(Node.id))
            .filter(Node.enabled == True)
            .filter(observer_secret_filter)
            .scalar()
            or 0
        )
        observer_fresh_nodes = (
            s.query(func.count(Node.id))
            .filter(Node.enabled == True)
            .filter(observer_secret_filter)
            .filter(Node.observer_last_push_at.isnot(None))
            .filter(Node.observer_last_push_at >= now - timedelta(seconds=observer_stale_after_seconds()))
            .scalar()
            or 0
        )
        metrics_status = _build_admin_metrics_status_snapshot(
            s=s,
            now=now,
            stale_after_seconds=stale_after_seconds,
        )
        metrics_age_seconds = metrics_status.get("age_seconds")
        metrics_quality_status = "missing" if not metrics_status.get("nodes") else str(metrics_status.get("status") or "stale")
        if unique_install_ids_7d > 0:
            app_installs_quality_status = "ok"
        elif int(unique_install_ids_total or 0) > 0:
            app_installs_quality_status = "stale"
        else:
            app_installs_quality_status = "missing"
        if observer_fresh_nodes > 0 or observer_seen_accounts_24h > 0:
            observer_quality_status = "ok"
        elif observer_configured_nodes > 0 or observer_total_rows > 0:
            observer_quality_status = "stale"
        else:
            observer_quality_status = "missing"
        payment_callback_failures_24h = (
            s.query(func.count(ExternalPaymentEvent.id))
            .filter(
                ExternalPaymentEvent.created_at >= since_24h,
                or_(
                    ExternalPaymentEvent.signature_ok == False,
                    ExternalPaymentEvent.processed_ok == False,
                ),
            )
            .scalar()
            or 0
        )
        subscription_numeric_fallbacks_24h = (
            s.query(func.count(Event.id))
            .filter(
                Event.created_at >= since_24h,
                Event.event_name == "subscription_numeric_fallback",
            )
            .scalar()
            or 0
        )
        expiring_3d = (
            s.query(func.count(User.tg_id))
            .filter(User.tg_id > 0)
            .filter(func.upper(func.coalesce(User.sub_type, "")) != "MANUAL")
            .filter(User.is_active == True)
            .filter(User.expiry_at.isnot(None))
            .filter(User.expiry_at >= now, User.expiry_at <= now + timedelta(days=3))
            .scalar()
            or 0
        )
        expired_7d = (
            s.query(func.count(func.distinct(Event.tg_id)))
            .filter(Event.created_at >= since_7d, Event.event_name == "expired")
            .scalar()
            or 0
        )
        reactivation_candidates = (
            s.query(func.count(User.tg_id))
            .filter(User.tg_id > 0)
            .filter(func.upper(func.coalesce(User.sub_type, "")) != "MANUAL")
            .filter(
                or_(
                    User.expiry_at <= now,
                    and_(func.upper(func.coalesce(User.sub_type, "")) == "FREE", User.is_active == False),
                )
            )
            .scalar()
            or 0
        )
        bonus_event_rows = (
            s.query(Event.event_name, func.count(Event.id))
            .filter(Event.created_at >= since_24h)
            .filter(
                Event.event_name.in_(
                    [
                        "promo_channel_activated",
                        "promo_channel_denied",
                        "promo_redeemed",
                        "promo_redeem_denied",
                        "gift_redeemed",
                        "gift_redeem_denied",
                    ]
                )
            )
            .group_by(Event.event_name)
            .all()
        )
        bonus_event_map = {str(name or ""): int(count or 0) for name, count in bonus_event_rows}
        retention_ping_rows = (
            s.query(Event.meta_json)
            .filter(Event.created_at >= since_24h, Event.event_name == "retention_ping")
            .all()
        )
        retention_ping_map = {
            "welcome": 0,
            "t3": 0,
            "t1": 0,
            "t0": 0,
            "reactivation": 0,
            "start99_offer": 0,
        }
        for row in retention_ping_rows:
            meta = _json_obj(getattr(row, "meta_json", None))
            flow_key = _normalize_retention_flow(meta.get("flow"))
            if flow_key:
                retention_ping_map[flow_key] = int(retention_ping_map.get(flow_key, 0)) + 1
        last_samples = (
            s.query(Node.code, Node.health_score, Node.panel_latency_ms, Node.active_clients, Node.last_health_at)
            .filter(Node.enabled == True)
            .order_by(Node.health_score.desc(), Node.weight.desc())
            .limit(10)
            .all()
        )
        return {
            "actor_tg_id": actor,
            "users": {
                "total": int(total_users),
                "active": int(active_users),
                "free": int(free_users),
                "paid": int(paid_users),
                "active_nonfree_accounts": int(active_nonfree_accounts),
                "trial_accounts": int(trial_accounts),
                "bonus_accounts": int(bonus_accounts),
                "unique_install_ids_24h": int(unique_install_ids_24h),
                "unique_install_ids_7d": int(unique_install_ids_7d),
                "observer_seen_accounts_24h": int(observer_seen_accounts_24h),
            },
            "data_quality": {
                "metrics": {
                    "status": metrics_quality_status,
                    "badge": _quality_badge(metrics_quality_status),
                    "missing": bool(metrics_quality_status == "missing"),
                    "age_seconds": metrics_age_seconds,
                },
                "app_installs": {
                    "status": app_installs_quality_status,
                    "badge": _quality_badge(app_installs_quality_status),
                    "missing": bool(app_installs_quality_status == "missing"),
                    "unique_install_ids_total": int(unique_install_ids_total),
                    "unique_install_ids_24h": int(unique_install_ids_24h),
                    "unique_install_ids_7d": int(unique_install_ids_7d),
                },
                "observer": {
                    "status": observer_quality_status,
                    "badge": _quality_badge(observer_quality_status),
                    "missing": bool(observer_quality_status == "missing"),
                    "configured_nodes": int(observer_configured_nodes),
                    "fresh_nodes": int(observer_fresh_nodes),
                    "seen_accounts_24h": int(observer_seen_accounts_24h),
                },
            },
            "retention": {
                "expiring_3d": int(expiring_3d),
                "expired_7d": int(expired_7d),
                "reactivation_candidates": int(reactivation_candidates),
                "pings_24h": {
                    "welcome": int(retention_ping_map.get("welcome", 0)),
                    "t3": int(retention_ping_map.get("t3", 0)),
                    "t1": int(retention_ping_map.get("t1", 0)),
                    "t0": int(retention_ping_map.get("t0", 0)),
                    "reactivation": int(retention_ping_map.get("reactivation", 0)),
                    "start99_offer": int(retention_ping_map.get("start99_offer", 0)),
                },
            },
            "tickets": {"open": int(open_tickets)},
            "nodes": {"total": int(total_nodes), "healthy": int(healthy_nodes)},
            "observer": {
                "watch_users": int(observer_watch_users),
                "suspicious_users": int(observer_suspicious_users),
            },
            "errors": {
                "stale_metrics": bool(metrics_status.get("status") != "fresh"),
                "unhealthy_nodes": max(0, int(total_nodes) - int(healthy_nodes)),
                "open_tickets": int(open_tickets),
                "payment_callback_failures_24h": int(payment_callback_failures_24h),
                "subscription_numeric_fallbacks_24h": int(subscription_numeric_fallbacks_24h),
            },
            "resilience": {
                "single_point_risk": bool(int(healthy_nodes) < 2),
                "free_node_enabled": bool(free_node_enabled),
            },
            "bonus_events_24h": {
                "channel_activated": int(bonus_event_map.get("promo_channel_activated", 0)),
                "channel_denied": int(bonus_event_map.get("promo_channel_denied", 0)),
                "promo_redeemed": int(bonus_event_map.get("promo_redeemed", 0)),
                "promo_denied": int(bonus_event_map.get("promo_redeem_denied", 0)),
                "gift_redeemed": int(bonus_event_map.get("gift_redeemed", 0)),
                "gift_denied": int(bonus_event_map.get("gift_redeem_denied", 0)),
            },
            "top_nodes": [
                {
                    "code": n.code,
                    "health_score": float(n.health_score or 0.0),
                    "panel_latency_ms": n.panel_latency_ms,
                    "active_clients": int(n.active_clients or 0),
                    "last_health_at": _safe_iso(n.last_health_at),
                }
                for n in last_samples
            ],
        }
    finally:
        s.close()


@app.get("/api/admin/users")
async def admin_users(
    x_telegram_init_data: str = Header(default=""),
    q: str = "",
    status: str = "",
    origin: str = "",
    observer_state: str = "",
    sort: str = "created_desc",
    limit: int = 50,
    offset: int = 0,
    page: int = 0,
    page_size: int = 0,
) -> dict:
    _require_admin(x_telegram_init_data)
    now = _utcnow()
    page_size_value = max(1, min(int(page_size or limit or 50), 200))
    if int(page or 0) > 0:
        offset_value = max(0, (int(page) - 1) * page_size_value)
        page_value = int(page)
    else:
        offset_value = max(0, int(offset))
        page_value = (offset_value // page_size_value) + 1
    s = SessionLocal()
    try:
        query = s.query(User)
        status_filter = _admin_user_status_filter(status, now=now)
        if status_filter is not None:
            query = query.filter(status_filter)
        origin_filter = _admin_user_origin_filter(origin)
        if origin_filter is not None:
            query = query.filter(origin_filter)
        observer_state_norm = _normalize_observer_state_filter(observer_state)
        if observer_state_norm == "ok":
            query = query.outerjoin(ObserverUserState, ObserverUserState.tg_id == User.tg_id).filter(
                or_(ObserverUserState.tg_id.is_(None), ObserverUserState.state == "ok")
            )
        elif observer_state_norm in {"watch", "suspicious"}:
            query = query.join(ObserverUserState, ObserverUserState.tg_id == User.tg_id).filter(
                ObserverUserState.state == observer_state_norm
            )
        query = _apply_admin_user_search(query, q)
        sort_norm = str(sort or "created_desc").strip().lower()
        if sort_norm == "created_asc":
            query = query.order_by(User.created_at.asc(), User.tg_id.asc())
        elif sort_norm == "expiry_asc":
            query = query.order_by(User.expiry_at.asc(), User.tg_id.asc())
        elif sort_norm == "expiry_desc":
            query = query.order_by(User.expiry_at.desc(), User.tg_id.desc())
        elif sort_norm == "name_asc":
            query = query.order_by(
                func.lower(func.coalesce(User.display_name, User.username, User.email, "")),
                User.tg_id.asc(),
            )
        elif sort_norm == "name_desc":
            query = query.order_by(
                func.lower(func.coalesce(User.display_name, User.username, User.email, "")).desc(),
                User.tg_id.desc(),
            )
        else:
            sort_norm = "created_desc"
            query = query.order_by(User.created_at.desc(), User.tg_id.desc())
        total = int(query.count() or 0)
        rows = (
            query.offset(offset_value)
            .limit(page_size_value)
            .all()
        )
        observer_map = get_observer_state_map(
            s=s,
            tg_ids=[int(getattr(row, "tg_id", 0) or 0) for row in rows],
        )
        return {
            "page": int(page_value),
            "page_size": int(page_size_value),
            "total": int(total),
            "sort": sort_norm,
            "users": [
                _serialize_admin_user_row(
                    u,
                    now=now,
                    observer_snapshot=observer_map.get(int(getattr(u, "tg_id", 0) or 0)),
                )
                for u in rows
            ],
        }
    finally:
        s.close()


def _admin_select_users_for_segment(
    *,
    s,
    segment: str,
    q: str = "",
    tg_ids: list[int] | None = None,
    limit: int = 100,
) -> list[User]:
    seg = str(segment or "active").strip().lower()
    now = _utcnow()
    query = s.query(User)
    if seg in {"all_active"}:
        seg = "active"
    if seg in {"manual"}:
        seg = "manual_test"

    if seg == "all":
        query = query.filter(User.tg_id > 0).filter(~_manual_test_user_filter())
    elif seg == "active":
        query = query.filter(_admin_user_status_filter("active", now=now))
    elif seg == "inactive":
        query = query.filter(_admin_user_status_filter("inactive", now=now))
    elif seg == "expired":
        query = query.filter(_admin_user_status_filter("expired", now=now))
    elif seg == "blocked":
        query = query.filter(_admin_user_status_filter("blocked", now=now))
    elif seg == "paid":
        query = query.filter(User.tg_id > 0).filter(~_manual_test_user_filter()).filter(func.upper(User.sub_type) == "PAID")
    elif seg == "free":
        query = query.filter(User.tg_id > 0).filter(~_manual_test_user_filter()).filter(func.upper(User.sub_type) == "FREE")
    elif seg == "manual_test":
        query = query.filter(_manual_test_user_filter())
    elif seg == "custom":
        picked = sorted({int(x) for x in (tg_ids or [])})
        if not picked:
            return []
        query = query.filter(User.tg_id.in_(picked))
    else:
        raise HTTPException(status_code=400, detail="Unsupported segment")

    query = _apply_admin_user_search(query, q)

    rows = (
        query.order_by(User.created_at.desc(), User.tg_id.desc())
        .limit(max(1, min(int(limit), 500)))
        .all()
    )
    return rows


def _admin_subscription_url(user: User) -> str:
    token = str(getattr(user, "sub_token", "") or "").strip()
    token_or_id = token or str(int(user.tg_id))
    return build_subscription_url(token_or_id)


def _bytes_to_gb(value: int) -> float:
    return round(float(max(0, int(value or 0))) / float(1024**3), 3)


def _estimate_active_users_proxy(
    *,
    live_connections: int,
    live_nodes: int,
    saw_ip_count: bool,
    observed_ip_count_24h: int | None,
) -> tuple[int, str]:
    connections = max(0, int(live_connections or 0))
    nodes = max(0, int(live_nodes or 0))
    observed = max(0, int(observed_ip_count_24h or 0))
    if saw_ip_count:
        if connections <= 0:
            return 0, "panel_ip_count"
        if observed > 0:
            return min(connections, observed), "panel_ip_count_capped_by_unique_ip_24h"
        return connections, "panel_ip_count"
    if nodes > 0:
        return nodes, "online_nodes"
    return 0, "none"


async def _admin_user_keys_state(user: User, *, nodes: list) -> dict[str, Any]:
    allowed_nodes = _nodes_for_user(user, nodes)
    allowed_by_code = {str(getattr(n, "code", "") or ""): n for n in allowed_nodes}
    expected_sub_id = str(getattr(user, "sub_token", "") or user.tg_id)
    policy_by_code: dict[str, dict[str, Any]] = {}
    observed_ip_count_24h = 0
    s = SessionLocal()
    try:
        policy_rows = s.query(UserKeyPolicy).filter(UserKeyPolicy.tg_id == int(user.tg_id)).all()
        for row in policy_rows:
            policy_by_code[str(row.node_code or "").strip().lower()] = _serialize_key_policy(row)
        observer_row = s.query(ObserverUserState).filter(ObserverUserState.tg_id == int(user.tg_id)).first()
        observed_ip_count_24h = int(getattr(observer_row, "observed_ip_count_24h", 0) or 0)
    finally:
        s.close()
    panel_rows: list[dict] = []
    panel_error = ""

    panel = ControlPanel()
    try:
        await panel.login()
        panel_rows = await panel.get_user_key_snapshots(
            tg_id=int(user.tg_id),
            node_codes=[str(code) for code in allowed_by_code.keys() if str(code).strip()],
        )
    except Exception as exc:
        panel_error = str(exc)[:200]
    finally:
        await panel.close()

    keys: list[dict[str, Any]] = []
    online_count = 0
    online_connections_now = 0
    enabled_count = 0
    total_up = 0
    total_down = 0
    mismatch_count = 0
    online_node_codes_now: list[str] = []
    saw_ip_count = False

    for row in panel_rows:
        code = str(row.get("node_code") or "").strip()
        node = allowed_by_code.get(code)
        client = row.get("client") or {}
        runtime = row.get("runtime") or {}
        exists = bool(client)
        current_sub_id = str(client.get("subId", "") or "")
        sub_id_match = bool(exists and current_sub_id == expected_sub_id)
        enabled = bool(runtime.get("enable", client.get("enable", False))) if exists else False
        online_raw = runtime.get("online") if isinstance(runtime, dict) else None
        online = bool(online_raw) if online_raw is not None else None
        up = int((runtime or {}).get("up", 0) or 0)
        down = int((runtime or {}).get("down", 0) or 0)
        total = int((runtime or {}).get("total", up + down) or (up + down))
        last_online_at = str((runtime or {}).get("last_online_at") or "") or None
        last_online_age_seconds = (runtime or {}).get("last_online_age_seconds")
        ip_count_raw = (runtime or {}).get("ip_count")
        current_connections = 0
        if ip_count_raw is not None:
            try:
                current_connections = max(0, int(ip_count_raw))
                saw_ip_count = True
            except Exception:
                current_connections = 0
        elif online is True:
            current_connections = 1
        policy = policy_by_code.get(code.lower(), {})
        link = (
            _generate_vless_link(user_uuid=str(user.uuid or ""), node=node, name=_node_label_ru(node.code, node.name))
            if node and str(user.uuid or "").strip()
            else ""
        )
        if online is True:
            online_count += 1
            online_connections_now += current_connections
            if code:
                online_node_codes_now.append(code)
        if enabled:
            enabled_count += 1
        if exists and not sub_id_match:
            mismatch_count += 1
        total_up += up
        total_down += down
        keys.append(
            {
                "node_code": code,
                "node_name": str(getattr(node, "name", row.get("node_name", "")) or ""),
                "node_host": str(getattr(node, "host", row.get("node_host", "")) or ""),
                "exists": exists,
                "client_uuid": str(client.get("id", "") or ""),
                "panel_email": str(client.get("email", "") or ""),
                "enabled": enabled,
                "online": online,
                "current_connections": int(current_connections),
                "sub_id": current_sub_id,
                "expected_sub_id": expected_sub_id,
                "sub_id_match": sub_id_match,
                "up_bytes": up,
                "down_bytes": down,
                "total_bytes": total,
                "total_gb": _bytes_to_gb(total),
                "last_online_at": last_online_at,
                "last_online_age_seconds": int(last_online_age_seconds) if last_online_age_seconds is not None else None,
                "vless_link": link,
                "panel_error": str(row.get("error", "") or "")[:200] or None,
                "policy": policy or None,
            }
        )

    keys.sort(key=lambda item: str(item.get("node_code") or ""))
    active_users_estimate, active_users_source = _estimate_active_users_proxy(
        live_connections=online_connections_now,
        live_nodes=online_count,
        saw_ip_count=saw_ip_count,
        observed_ip_count_24h=observed_ip_count_24h,
    )
    return {
        "keys": keys,
        "summary": {
            "nodes_total": int(len(keys)),
            "nodes_with_client": int(sum(1 for k in keys if bool(k.get("exists")))),
            "nodes_online": int(online_count),
            "online_keys_now": int(online_count),
            "online_connections_now": int(online_connections_now),
            "active_users_estimate": int(active_users_estimate),
            "active_users_source": active_users_source,
            "online_node_codes_now": sorted(set(online_node_codes_now)),
            "nodes_enabled": int(enabled_count),
            "subid_mismatch_count": int(mismatch_count),
            "traffic_up_bytes": int(total_up),
            "traffic_down_bytes": int(total_down),
            "traffic_total_bytes": int(total_up + total_down),
            "traffic_total_gb": _bytes_to_gb(total_up + total_down),
            "panel_state": "error" if panel_error else "ok",
            "panel_error": panel_error or None,
            "policies_total": int(len(policy_by_code)),
        },
    }


@app.get("/api/admin/users/{tg_id}")
async def admin_user_card(tg_id: int, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        tickets = list_user_tickets(s, tg_id, limit=20)
        nodes = enabled_nodes(s)
        policies = (
            s.query(UserKeyPolicy)
            .filter(UserKeyPolicy.tg_id == int(tg_id))
            .order_by(UserKeyPolicy.node_code.asc())
            .all()
        )
        history_rows = (
            s.query(KeyActionHistory)
            .filter(KeyActionHistory.tg_id == int(tg_id))
            .order_by(KeyActionHistory.created_at.desc(), KeyActionHistory.id.desc())
            .limit(100)
            .all()
        )
        recent_admin_rows = (
            s.query(AdminAudit)
            .filter(or_(AdminAudit.target_tg_id == int(tg_id), AdminAudit.actor_tg_id == int(tg_id)))
            .order_by(AdminAudit.created_at.desc(), AdminAudit.id.desc())
            .limit(100)
            .all()
        )
        loyalty_snapshot = _user_loyalty_snapshot(s=s, user=user)
        observer_payload = build_admin_observer_block(s=s, tg_id=int(tg_id))
        sub_token = str(getattr(user, "sub_token", "") or "").strip()
        user_status = _user_effective_status(user)
        user_origin = _user_origin(user)
        user_payload = {
            "tg_id": int(user.tg_id),
            "username": user.username,
            "display_name": getattr(user, "display_name", None),
            "sub_type": user.sub_type,
            "is_active": bool(user.is_active),
            "effective_active": bool(user_status == "active"),
            "status": user_status,
            "origin": user_origin,
            "is_manual": bool(_is_manual_test_user(user)),
            "expiry_at": _safe_iso(user.expiry_at),
            "stars_paid": int(user.stars_paid or 0),
            "total_gb": int(user.total_gb or 0),
            "trial_used": bool(user.trial_used),
            "referral_count": int(user.referral_count or 0),
            "streak_months": int(user.streak_months or 0),
            "created_at": _safe_iso(user.created_at),
            "subscription_url": _admin_subscription_url(user),
            "subscription_token": sub_token,
            "linked_telegram_id": int(user.linked_telegram_id) if getattr(user, "linked_telegram_id", None) is not None else None,
            "linked_telegram_username": getattr(user, "linked_telegram_username", None),
            "app_install_id": getattr(user, "app_install_id", None),
            "app_platform": getattr(user, "app_platform", None),
            "app_last_seen_at": _safe_iso(getattr(user, "app_last_seen_at", None)),
            "observer_state": observer_payload.get("state", "ok"),
            "observer_updated_at": observer_payload.get("updated_at"),
        }
        ticket_payload = [_ticket_row(t, list_ticket_messages(s, t.id, limit=1)) for t in tickets]
        policy_payload = [_serialize_key_policy(row) for row in policies]
        history_payload = [
            {
                "id": int(row.id),
                "action": str(row.action or ""),
                "node_code": str(row.node_code or "") or None,
                "actor_tg_id": int(row.actor_tg_id) if row.actor_tg_id is not None else None,
                "source": str(row.source or ""),
                "meta": _json_obj(getattr(row, "meta", None)),
                "created_at": _safe_iso(row.created_at),
            }
            for row in history_rows
        ]
        recent_admin_payload = [
            {
                "id": int(row.id),
                "actor_tg_id": int(row.actor_tg_id),
                "action": str(row.action or ""),
                "target_tg_id": int(row.target_tg_id) if row.target_tg_id is not None else None,
                "meta": _json_obj(getattr(row, "meta", None)),
                "created_at": _safe_iso(row.created_at),
            }
            for row in recent_admin_rows
        ]
    finally:
        s.close()

    keys_state = await _admin_user_keys_state(user, nodes=nodes)
    s2 = SessionLocal()
    try:
        risk = _compute_user_risk(s=s2, user=user, keys_summary=(keys_state or {}).get("summary") or {})
    finally:
        s2.close()
    return {
        "user": user_payload,
        "tickets": ticket_payload,
        "key_policies": policy_payload,
        "key_history": history_payload,
        "admin_actions": recent_admin_payload,
        "risk": risk,
        "observer": observer_payload,
        "loyalty": loyalty_snapshot,
        **keys_state,
    }


@app.post("/api/admin/users/manual")
async def admin_create_manual_user(payload: ManualUserCreateRequest, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        tg_id = _next_manual_tg_id(s)
        now = _utcnow()
        user = User(
            tg_id=tg_id,
            username=None,
            uuid=str(uuid.uuid4()),
            email=f"MANUAL_{abs(tg_id)}",
            sub_type="MANUAL",
            current_plan_code="manual",
            created_at=now,
            expiry_at=now + timedelta(days=int(payload.days)),
            is_active=True,
            stars_paid=0,
            total_gb=0,
            trial_used=False,
            tos_accepted=True,
            first_purchase_done=True,
            sub_token=_generate_sub_token(),
            is_manual=True,
            created_by_admin=actor,
            display_name=payload.display_name.strip(),
        )
        s.add(user)
        s.commit()
        s.refresh(user)
        created = {
            "tg_id": int(user.tg_id),
            "uuid": str(user.uuid),
            "email": str(user.email),
            "sub_token": str(user.sub_token or ""),
            "display_name": str(user.display_name or ""),
            "sub_type": str(user.sub_type or ""),
            "is_active": bool(user.is_active),
            "expiry_at": _safe_iso(user.expiry_at),
        }
    finally:
        s.close()

    panel = ControlPanel()
    sync_ok = False
    try:
        await panel.login()
        res = await panel.ensure_user_on_all_nodes(
            tg_id=int(created["tg_id"]),
            client_uuid=str(created["uuid"]),
            email=str(created["email"]),
            sub_id=str(created["sub_token"] or created["tg_id"]),
            enable=True,
            only_node_codes=None,
        )
        sync_ok = bool(any(res.values())) if res else False
    finally:
        await panel.close()

    _audit_admin(
        actor_tg_id=actor,
        action="admin_manual_create",
        target_tg_id=int(created["tg_id"]),
        meta={"days": payload.days, "sync_ok": sync_ok},
    )
    _key_history_log(
        tg_id=int(created["tg_id"]),
        action="manual_create",
        actor_tg_id=actor,
        meta={"days": int(payload.days), "sync_ok": bool(sync_ok)},
    )
    return {
        "ok": True,
        "user": {
            "tg_id": int(created["tg_id"]),
            "display_name": created["display_name"],
            "sub_type": created["sub_type"],
            "is_active": bool(created["is_active"]),
            "expiry_at": created["expiry_at"],
            "subscription_url": build_subscription_url(str(created["sub_token"] or "")),
        },
        "sync_ok": sync_ok,
    }


@app.post("/api/admin/users/{tg_id}/manual/extend")
@app.post("/api/admin/users/{tg_id}/manual-extend")
async def admin_extend_manual_user(tg_id: int, payload: ManualUserExtendRequest, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    delta_days = int(payload.delta_days if payload.delta_days is not None else (payload.days or 0))
    if delta_days == 0:
        raise HTTPException(status_code=400, detail="delta_days must be non-zero")
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        now = _utcnow()
        cur = user.expiry_at if user.expiry_at and user.expiry_at > now else now
        candidate_expiry = cur + timedelta(days=delta_days)
        if candidate_expiry <= now:
            if not bool(payload.allow_deactivate):
                raise HTTPException(
                    status_code=400,
                    detail="Operation would deactivate user; pass allow_deactivate=true to confirm",
                )
            user.expiry_at = now
            user.is_active = False
        else:
            user.expiry_at = candidate_expiry
            user.is_active = True
        s.commit()
        s.refresh(user)
        expiry_iso = _safe_iso(user.expiry_at)
        is_active = bool(user.is_active)
    finally:
        s.close()
    _audit_admin(
        actor_tg_id=actor,
        action="admin_manual_extend",
        target_tg_id=tg_id,
        meta={"delta_days": int(delta_days), "allow_deactivate": bool(payload.allow_deactivate)},
    )
    return {"ok": True, "expiry_at": expiry_iso, "is_active": is_active, "delta_days": int(delta_days)}


@app.post("/api/admin/users/{tg_id}/manual/block")
async def admin_block_manual_user(tg_id: int, payload: ManualUserBlockRequest, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_active = not bool(payload.blocked)
        s.commit()
        user_uuid = str(user.uuid)
        active = bool(user.is_active)
    finally:
        s.close()

    panel = ControlPanel()
    try:
        await panel.login()
        await panel.enable_client(user_uuid, enable=active)
    finally:
        await panel.close()

    _audit_admin(actor_tg_id=actor, action="admin_manual_block", target_tg_id=tg_id, meta={"blocked": bool(payload.blocked)})
    _key_history_log(
        tg_id=int(tg_id),
        action="manual_block" if bool(payload.blocked) else "manual_unblock",
        node_code=None,
        actor_tg_id=actor,
        meta={"blocked": bool(payload.blocked)},
    )
    return {"ok": True, "is_active": active}


@app.post("/api/admin/users/{tg_id}/manual/regenerate-token")
async def admin_regenerate_manual_token(tg_id: int, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.sub_token = _generate_sub_token()
        s.commit()
        s.refresh(user)
        _process_referral_bonus_queue(limit=100, force_without_activity=False)
        sub_token = str(user.sub_token or "")
        user_uuid = str(user.uuid or "")
        is_active = bool(user.is_active)
    finally:
        s.close()

    sync_ok = False
    if user_uuid:
        panel = ControlPanel()
        try:
            await panel.login()
            sync_ok = bool(await panel.enable_client(user_uuid, enable=is_active))
        finally:
            await panel.close()
    _audit_admin(actor_tg_id=actor, action="admin_manual_regen_token", target_tg_id=tg_id)
    _key_history_log(
        tg_id=int(tg_id),
        action="token_regenerate",
        node_code=None,
        actor_tg_id=actor,
        meta={"sync_ok": bool(sync_ok)},
    )
    return {
        "ok": True,
        "subscription_url": build_subscription_url(str(sub_token or "")),
        "sync_ok": bool(sync_ok),
    }


@app.post("/api/admin/users/{tg_id}/safe-delete")
async def admin_safe_delete_test_user(
    tg_id: int,
    payload: AdminUserSafeDeleteIn,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    if not bool(payload.confirm):
        raise HTTPException(status_code=400, detail="confirm=true is required")

    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not _is_manual_test_user(user):
            raise HTTPException(status_code=400, detail="Only explicit manual/test users can be deleted")
        target_meta = {
            "tg_id": int(user.tg_id),
            "display_name": str(getattr(user, "display_name", "") or ""),
            "sub_type": str(getattr(user, "sub_type", "") or ""),
        }
        s.query(UserNode).filter(UserNode.tg_id == int(tg_id)).delete(synchronize_session=False)
        s.query(UserKeyPolicy).filter(UserKeyPolicy.tg_id == int(tg_id)).delete(synchronize_session=False)
        s.query(KeyActionHistory).filter(KeyActionHistory.tg_id == int(tg_id)).delete(synchronize_session=False)
        s.query(Event).filter(Event.tg_id == int(tg_id)).delete(synchronize_session=False)
        s.delete(user)
        s.commit()
    finally:
        s.close()

    panel_deleted = False
    panel = ControlPanel()
    try:
        await panel.login()
        panel_deleted = bool(await panel.delete_client(int(tg_id)))
    except Exception as exc:
        logger.warning("admin safe delete panel cleanup failed tg_id=%s err=%s", int(tg_id), exc)
    finally:
        await panel.close()

    _audit_admin(
        actor_tg_id=actor,
        action="admin_safe_delete_test_user",
        target_tg_id=int(tg_id),
        meta={**target_meta, "panel_deleted": bool(panel_deleted)},
    )
    return {"ok": True, "tg_id": int(tg_id), "panel_deleted": bool(panel_deleted)}


@app.post("/api/admin/users/{tg_id}/delete-test-user")
async def admin_delete_test_user_compat(
    tg_id: int,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    return await admin_safe_delete_test_user(
        tg_id=tg_id,
        payload=AdminUserSafeDeleteIn(confirm=True),
        x_telegram_init_data=x_telegram_init_data,
    )


@app.post("/api/admin/users/{tg_id}/keys/{node_code}/toggle")
async def admin_user_key_toggle(
    tg_id: int,
    node_code: str,
    payload: AdminUserKeyToggleIn,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        expected_sub_id = str(getattr(user, "sub_token", "") or user.tg_id)
        hard_cap_gb = _get_user_node_hard_cap_gb(s=s, tg_id=int(tg_id), node_code=str(node_code or ""))
    finally:
        s.close()

    panel = ControlPanel()
    try:
        await panel.login()
        changed = await panel.set_user_key_enabled_on_node(
            tg_id=int(tg_id),
            node_code=str(node_code or ""),
            enable=bool(payload.enable),
            sub_id=expected_sub_id,
            hard_cap_gb=hard_cap_gb,
        )
    finally:
        await panel.close()

    if changed is None:
        raise HTTPException(status_code=404, detail="Key not found on target node")
    if not changed:
        raise HTTPException(status_code=502, detail="Panel update failed")

    _audit_admin(
        actor_tg_id=actor,
        action="admin_user_key_toggle",
        target_tg_id=int(tg_id),
        meta={"node_code": str(node_code or ""), "enable": bool(payload.enable)},
    )
    _key_history_log(
        tg_id=int(tg_id),
        action="key_enable" if bool(payload.enable) else "key_disable",
        node_code=str(node_code or ""),
        actor_tg_id=actor,
        meta={"enabled": bool(payload.enable)},
    )
    return {"ok": True, "tg_id": int(tg_id), "node_code": str(node_code or ""), "enabled": bool(payload.enable)}


@app.post("/api/admin/users/{tg_id}/keys/{node_code}/reset-traffic")
async def admin_user_key_reset_traffic(
    tg_id: int,
    node_code: str,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    finally:
        s.close()

    panel = ControlPanel()
    try:
        await panel.login()
        changed = await panel.reset_user_key_traffic_on_node(tg_id=int(tg_id), node_code=str(node_code or ""))
    finally:
        await panel.close()

    if changed is None:
        raise HTTPException(status_code=404, detail="Key not found on target node")
    if not changed:
        raise HTTPException(status_code=502, detail="Panel reset failed")

    _audit_admin(
        actor_tg_id=actor,
        action="admin_user_key_reset_traffic",
        target_tg_id=int(tg_id),
        meta={"node_code": str(node_code or "")},
    )
    _key_history_log(
        tg_id=int(tg_id),
        action="key_reset_traffic",
        node_code=str(node_code or ""),
        actor_tg_id=actor,
    )
    return {"ok": True, "tg_id": int(tg_id), "node_code": str(node_code or "")}


@app.post("/api/admin/users/{tg_id}/keys/{node_code}/resync-subid")
async def admin_user_key_resync_subid(
    tg_id: int,
    node_code: str,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        expected_sub_id = str(getattr(user, "sub_token", "") or user.tg_id)
        hard_cap_gb = _get_user_node_hard_cap_gb(s=s, tg_id=int(tg_id), node_code=str(node_code or ""))
    finally:
        s.close()

    panel = ControlPanel()
    try:
        await panel.login()
        changed = await panel.resync_user_key_subid_on_node(
            tg_id=int(tg_id),
            node_code=str(node_code or ""),
            sub_id=expected_sub_id,
            hard_cap_gb=hard_cap_gb,
        )
    finally:
        await panel.close()

    if changed is None:
        raise HTTPException(status_code=404, detail="Key not found on target node")
    if not changed:
        raise HTTPException(status_code=502, detail="Panel subId sync failed")

    _audit_admin(
        actor_tg_id=actor,
        action="admin_user_key_resync_subid",
        target_tg_id=int(tg_id),
        meta={"node_code": str(node_code or "")},
    )
    _key_history_log(
        tg_id=int(tg_id),
        action="key_resync_subid",
        node_code=str(node_code or ""),
        actor_tg_id=actor,
    )
    return {
        "ok": True,
        "tg_id": int(tg_id),
        "node_code": str(node_code or ""),
        "expected_sub_id": expected_sub_id,
    }


@app.get("/api/admin/users/{tg_id}/key-history")
async def admin_user_key_history(tg_id: int, x_telegram_init_data: str = Header(default=""), limit: int = 100) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        rows = (
            s.query(KeyActionHistory)
            .filter(KeyActionHistory.tg_id == int(tg_id))
            .order_by(KeyActionHistory.created_at.desc(), KeyActionHistory.id.desc())
            .limit(max(1, min(int(limit), 500)))
            .all()
        )
        return {
            "rows": [
                {
                    "id": int(r.id),
                    "tg_id": int(r.tg_id),
                    "node_code": str(r.node_code or "") or None,
                    "action": str(r.action or ""),
                    "actor_tg_id": int(r.actor_tg_id) if r.actor_tg_id is not None else None,
                    "source": str(r.source or ""),
                    "meta": _json_obj(getattr(r, "meta", None)),
                    "created_at": _safe_iso(r.created_at),
                }
                for r in rows
            ]
        }
    finally:
        s.close()


@app.get("/api/admin/users/{tg_id}/key-limits")
async def admin_user_key_limits_get(tg_id: int, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        rows = (
            s.query(UserKeyPolicy)
            .filter(UserKeyPolicy.tg_id == int(tg_id))
            .order_by(UserKeyPolicy.node_code.asc())
            .all()
        )
        return {"limits": [_serialize_key_policy(r) for r in rows]}
    finally:
        s.close()


@app.put("/api/admin/users/{tg_id}/key-limits/{node_code}")
async def admin_user_key_limits_put(
    tg_id: int,
    node_code: str,
    payload: AdminUserKeyLimitsIn,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    node = str(node_code or "").strip().lower()
    if not node:
        raise HTTPException(status_code=400, detail="node_code is required")
    if payload.soft_cap_gb is not None and payload.hard_cap_gb is not None and int(payload.hard_cap_gb) < int(payload.soft_cap_gb):
        raise HTTPException(status_code=400, detail="hard_cap_gb must be >= soft_cap_gb")

    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        row = (
            s.query(UserKeyPolicy)
            .filter(UserKeyPolicy.tg_id == int(tg_id), func.lower(UserKeyPolicy.node_code) == node)
            .first()
        )
        if not row:
            row = UserKeyPolicy(
                tg_id=int(tg_id),
                node_code=node,
                updated_by=actor,
                updated_at=_utcnow(),
            )
            s.add(row)
        row.burst_mbps = int(payload.burst_mbps) if payload.burst_mbps is not None else None
        row.soft_cap_gb = int(payload.soft_cap_gb) if payload.soft_cap_gb is not None else None
        row.hard_cap_gb = int(payload.hard_cap_gb) if payload.hard_cap_gb is not None else None
        row.notify_soft = bool(payload.notify_soft)
        row.notify_hard = bool(payload.notify_hard)
        row.auto_disable_on_hard = bool(payload.auto_disable_on_hard)
        row.updated_by = actor
        row.updated_at = _utcnow()
        s.commit()
        s.refresh(row)
        expected_sub_id = str(getattr(user, "sub_token", "") or user.tg_id)
        row_payload = _serialize_key_policy(row)
    finally:
        s.close()

    applied = None
    if bool(payload.apply_now):
        panel = ControlPanel()
        try:
            await panel.login()
            applied = await panel.apply_user_key_limits_on_node(
                tg_id=int(tg_id),
                node_code=node,
                hard_cap_gb=(int(payload.hard_cap_gb) if payload.hard_cap_gb is not None else None),
                sub_id=expected_sub_id,
            )
        finally:
            await panel.close()

    _audit_admin(
        actor_tg_id=actor,
        action="admin_user_key_limits_put",
        target_tg_id=int(tg_id),
        meta={"node_code": node, "policy": row_payload, "apply_now": bool(payload.apply_now), "applied": applied},
    )
    _key_history_log(
        tg_id=int(tg_id),
        action="key_limits_update",
        node_code=node,
        actor_tg_id=actor,
        meta={"policy": row_payload, "apply_now": bool(payload.apply_now), "applied": applied},
    )
    return {"ok": True, "policy": row_payload, "applied": applied}


@app.get("/api/admin/users/{tg_id}/risk")
async def admin_user_risk_get(tg_id: int, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        nodes = enabled_nodes(s)
    finally:
        s.close()
    keys_state = await _admin_user_keys_state(user, nodes=nodes)
    s2 = SessionLocal()
    try:
        risk = _compute_user_risk(s=s2, user=user, keys_summary=(keys_state or {}).get("summary") or {})
    finally:
        s2.close()
    return {"risk": risk}


@app.get("/api/admin/users/{tg_id}/loyalty")
async def admin_user_loyalty_get(tg_id: int, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"loyalty": _user_loyalty_snapshot(s=s, user=user)}
    finally:
        s.close()


@app.post("/api/admin/users/{tg_id}/loyalty/grant")
async def admin_user_loyalty_grant(
    tg_id: int,
    payload: AdminLoyaltyGrantIn,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        loyalty = _user_loyalty_snapshot(s=s, user=user)
        tier = next((x for x in loyalty.get("tiers", []) if int(x.get("days") or 0) == int(payload.tier_days)), None)
        if not tier:
            raise HTTPException(status_code=404, detail="Tier not found")
        if not bool(tier.get("unlocked")):
            raise HTTPException(status_code=400, detail="Tier is not unlocked yet")
        reward_key = str(tier.get("reward_key") or "")
        if bool(tier.get("claimed")):
            raise HTTPException(status_code=400, detail="Tier already claimed")
        bonus_days = int(tier.get("bonus_days") or 0)
        now = _utcnow()
        start = user.expiry_at if user.expiry_at and user.expiry_at > now else now
        user.expiry_at = start + timedelta(days=max(1, bonus_days))
        user.is_active = True
        s.add(RewardClaim(tg_id=int(tg_id), reward_key=reward_key, meta=json.dumps({"tier": int(payload.tier_days)}, ensure_ascii=False)))
        s.commit()
        try:
            sync_ok = bool(await _sync_user_after_paid_bonus(user))
        except Exception as exc:
            logger.warning("loyalty grant sync failed tg_id=%s err=%s", int(tg_id), exc)
            sync_ok = False
        expiry_at = _safe_iso(user.expiry_at)
    except IntegrityError:
        s.rollback()
        raise HTTPException(status_code=400, detail="Tier already claimed")
    finally:
        s.close()
    _audit_admin(
        actor_tg_id=actor,
        action="admin_user_loyalty_grant",
        target_tg_id=int(tg_id),
        meta={"tier_days": int(payload.tier_days), "sync_ok": bool(sync_ok)},
    )
    return {"ok": True, "tier_days": int(payload.tier_days), "expiry_at": expiry_at, "sync_ok": bool(sync_ok)}


@app.post("/api/admin/users/{tg_id}/presets/run")
async def admin_user_preset_run(
    tg_id: int,
    payload: AdminUserPresetRunIn,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    preset = str(payload.preset or "").strip().lower()
    if preset not in {"reset_key", "rotate_link", "extend_1d", "send_guide"}:
        raise HTTPException(status_code=400, detail="Unsupported preset")

    if preset == "extend_1d":
        s = SessionLocal()
        try:
            user = s.query(User).filter(User.tg_id == int(tg_id)).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            now = _utcnow()
            base = user.expiry_at if user.expiry_at and user.expiry_at > now else now
            user.expiry_at = base + timedelta(days=1)
            user.is_active = True
            s.commit()
            expiry_at = _safe_iso(user.expiry_at)
        finally:
            s.close()
        _audit_admin(actor_tg_id=actor, action="admin_operator_extend_1d", target_tg_id=int(tg_id))
        return {"ok": True, "preset": preset, "expiry_at": expiry_at}

    if preset == "send_guide":
        text = (
            "Инструкция по подключению:\n"
            "1) Откройте раздел Устройства.\n"
            "2) Импортируйте ключ.\n"
            "3) Проверьте статус и перезапустите приложение."
        )
        ok = await _telegram_send_message(int(tg_id), text)
        _audit_admin(actor_tg_id=actor, action="admin_operator_send_guide", target_tg_id=int(tg_id), meta={"ok": bool(ok)})
        if not ok:
            raise HTTPException(status_code=502, detail="Telegram send failed")
        return {"ok": True, "preset": preset}

    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        expected_sub_id = str(getattr(user, "sub_token", "") or user.tg_id)
        nodes = enabled_nodes(s)
    finally:
        s.close()
    keys_state = await _admin_user_keys_state(user, nodes=nodes)
    keys = [k for k in (keys_state.get("keys") or []) if bool(k.get("exists"))]

    panel = ControlPanel()
    changed = 0
    failed = 0
    try:
        await panel.login()
        if preset == "reset_key":
            for k in keys:
                ok = await panel.reset_user_key_traffic_on_node(tg_id=int(tg_id), node_code=str(k.get("node_code") or ""))
                if ok:
                    changed += 1
                else:
                    failed += 1
                    continue
                _key_history_log(
                    tg_id=int(tg_id),
                    action="key_reset_traffic",
                    node_code=str(k.get("node_code") or ""),
                    actor_tg_id=actor,
                    source="preset",
                )
        elif preset == "rotate_link":
            s2 = SessionLocal()
            try:
                db_user = s2.query(User).filter(User.tg_id == int(tg_id)).first()
                if not db_user:
                    raise HTTPException(status_code=404, detail="User not found")
                db_user.sub_token = _generate_sub_token()
                s2.commit()
                s2.refresh(db_user)
                expected_sub_id = str(db_user.sub_token or db_user.tg_id)
            finally:
                s2.close()
            for k in keys:
                code = str(k.get("node_code") or "")
                hard_cap = None
                s3 = SessionLocal()
                try:
                    hard_cap = _get_user_node_hard_cap_gb(s=s3, tg_id=int(tg_id), node_code=code)
                finally:
                    s3.close()
                ok = await panel.resync_user_key_subid_on_node(
                    tg_id=int(tg_id),
                    node_code=code,
                    sub_id=expected_sub_id,
                    hard_cap_gb=hard_cap,
                )
                if ok:
                    changed += 1
                else:
                    failed += 1
                    continue
                _key_history_log(tg_id=int(tg_id), action="key_resync_subid", node_code=code, actor_tg_id=actor, source="preset")
            _key_history_log(tg_id=int(tg_id), action="token_regenerate", actor_tg_id=actor, source="preset")
    finally:
        await panel.close()
    _audit_admin(actor_tg_id=actor, action=f"admin_operator_{preset}", target_tg_id=int(tg_id), meta={"changed": changed, "failed": failed})
    return {
        "ok": True,
        "preset": preset,
        "changed": int(changed),
        "failed": int(failed),
        "subscription_url": build_subscription_url(expected_sub_id),
    }


@app.post("/api/admin/users/keys/bulk-action")
async def admin_users_keys_bulk_action(payload: AdminUserKeysBulkActionIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    action = str(payload.action or "").strip().lower()
    if action not in {"disable", "enable", "reset", "resync"}:
        raise HTTPException(status_code=400, detail="Unsupported action")

    s = SessionLocal()
    try:
        users = _admin_select_users_for_segment(
            s=s,
            segment=payload.segment,
            q=payload.q,
            tg_ids=payload.tg_ids,
            limit=payload.limit,
        )
    finally:
        s.close()
    if not users:
        return {"ok": True, "action": action, "dry_run": bool(payload.dry_run), "users": 0, "changed": 0, "failed": 0, "details": []}

    if len(users) > 50 and not bool(payload.force) and not bool(payload.dry_run):
        return {
            "ok": False,
            "requires_force": True,
            "action": action,
            "users": int(len(users)),
            "message": "Bulk action over 50 users requires force=true",
        }

    if bool(payload.dry_run):
        return {
            "ok": True,
            "action": action,
            "dry_run": True,
            "users": int(len(users)),
            "preview_tg_ids": [int(u.tg_id) for u in users[:50]],
        }

    panel = ControlPanel()
    changed = 0
    failed = 0
    details: list[dict[str, Any]] = []
    try:
        await panel.login()
        for user in users:
            tg_id = int(user.tg_id)
            nodes = payload.node_codes or []
            if not nodes:
                snapshots = await panel.get_user_key_snapshots(tg_id=tg_id)
                nodes = [str(r.get("node_code") or "") for r in snapshots if str(r.get("node_code") or "").strip()]
            expected_sub_id = str(getattr(user, "sub_token", "") or user.tg_id)
            user_changed = 0
            user_failed = 0
            for node_code in nodes:
                code = str(node_code or "").strip().lower()
                if not code:
                    continue
                s2 = SessionLocal()
                try:
                    hard_cap_gb = _get_user_node_hard_cap_gb(s=s2, tg_id=tg_id, node_code=code)
                finally:
                    s2.close()
                ok: bool | None
                if action == "disable":
                    ok = await panel.set_user_key_enabled_on_node(tg_id=tg_id, node_code=code, enable=False, sub_id=expected_sub_id, hard_cap_gb=hard_cap_gb)
                elif action == "enable":
                    ok = await panel.set_user_key_enabled_on_node(tg_id=tg_id, node_code=code, enable=True, sub_id=expected_sub_id, hard_cap_gb=hard_cap_gb)
                elif action == "reset":
                    ok = await panel.reset_user_key_traffic_on_node(tg_id=tg_id, node_code=code)
                else:
                    ok = await panel.resync_user_key_subid_on_node(tg_id=tg_id, node_code=code, sub_id=expected_sub_id, hard_cap_gb=hard_cap_gb)
                if ok:
                    changed += 1
                    user_changed += 1
                    hist_action = {
                        "disable": "key_disable",
                        "enable": "key_enable",
                        "reset": "key_reset_traffic",
                        "resync": "key_resync_subid",
                    }[action]
                    _key_history_log(tg_id=tg_id, action=hist_action, node_code=code, actor_tg_id=actor, source="bulk")
                else:
                    failed += 1
                    user_failed += 1
            details.append({"tg_id": tg_id, "changed": user_changed, "failed": user_failed})
    finally:
        await panel.close()
    _audit_admin(
        actor_tg_id=actor,
        action="admin_bulk_key_action",
        meta={
            "action": action,
            "segment": payload.segment,
            "users": len(users),
            "changed": changed,
            "failed": failed,
            "forced": bool(payload.force),
        },
    )
    return {"ok": True, "action": action, "users": int(len(users)), "changed": int(changed), "failed": int(failed), "details": details}


@app.get("/api/admin/audit")
async def admin_audit_log(
    x_telegram_init_data: str = Header(default=""),
    limit: int = 200,
    offset: int = 0,
    action: str = "",
    target_tg_id: int | None = None,
) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        q = s.query(AdminAudit)
        if target_tg_id is not None:
            q = q.filter(AdminAudit.target_tg_id == int(target_tg_id))
        action_norm = str(action or "").strip()
        if action_norm:
            q = q.filter(AdminAudit.action == action_norm)
        rows = (
            q.order_by(AdminAudit.created_at.desc(), AdminAudit.id.desc())
            .offset(max(0, int(offset)))
            .limit(max(1, min(int(limit), 1000)))
            .all()
        )
        return {
            "rows": [
                {
                    "id": int(r.id),
                    "actor_tg_id": int(r.actor_tg_id),
                    "action": str(r.action or ""),
                    "target_tg_id": int(r.target_tg_id) if r.target_tg_id is not None else None,
                    "meta": _json_obj(getattr(r, "meta", None)),
                    "created_at": _safe_iso(r.created_at),
                }
                for r in rows
            ]
        }
    finally:
        s.close()


@app.post("/api/admin/users/{tg_id}/message")
async def admin_user_message(tg_id: int, payload: AdminMessageIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    ok = await _telegram_send_message(tg_id, payload.text)
    _audit_admin(
        actor_tg_id=actor,
        action="admin_user_message",
        target_tg_id=tg_id,
        meta={"ok": ok, "length": len(payload.text)},
    )
    if not ok:
        raise HTTPException(status_code=502, detail="Telegram send failed")
    return {"ok": True}


@app.post("/api/admin/broadcast")
async def admin_broadcast(payload: AdminBroadcastIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    segment = (payload.segment or "all_active").strip().lower()
    limit = max(1, min(int(payload.limit), MAX_BROADCAST_LIMIT))

    s = SessionLocal()
    try:
        target_ids: list[int] = []
        if segment == "custom":
            target_ids = sorted({int(v) for v in payload.tg_ids if int(v) > 0})
        else:
            query = s.query(User.tg_id).filter(User.tg_id > 0)
            if segment == "all_active":
                query = query.filter(User.is_active == True)
            elif segment == "free":
                query = query.filter(func.upper(User.sub_type) == "FREE")
            elif segment == "paid":
                query = query.filter(func.upper(User.sub_type) == "PAID")
            elif segment == "expired":
                query = query.filter(User.expiry_at.isnot(None), User.expiry_at < _utcnow())
            else:
                raise HTTPException(status_code=400, detail="Unsupported segment")
            target_ids = [int(r[0]) for r in query.order_by(User.tg_id.asc()).limit(limit).all()]
    finally:
        s.close()

    sent = 0
    failed = 0
    errors: list[int] = []
    for tg_id in target_ids[:limit]:
        if tg_id == actor:
            continue
        ok = await _telegram_send_message(tg_id, payload.text)
        if ok:
            sent += 1
        else:
            failed += 1
            if len(errors) < 25:
                errors.append(tg_id)

    _audit_admin(
        actor_tg_id=actor,
        action="admin_broadcast",
        meta={"segment": segment, "sent": sent, "failed": failed, "attempted": min(len(target_ids), limit)},
    )
    return {"ok": True, "segment": segment, "attempted": min(len(target_ids), limit), "sent": sent, "failed": failed, "failed_ids": errors}


@app.get("/api/admin/promos")
async def admin_promos(x_telegram_init_data: str = Header(default=""), limit: int = 200) -> dict:
    _require_admin(x_telegram_init_data)
    lim = max(1, min(int(limit), 500))
    s = SessionLocal()
    try:
        rows = s.query(PromoCode).order_by(PromoCode.created_at.desc(), PromoCode.id.desc()).limit(lim).all()
        usage_rows = (
            s.query(PromoUsage.promo_code, func.count(PromoUsage.id))
            .group_by(PromoUsage.promo_code)
            .all()
        )
        usage_map = {str(code or "").upper(): int(cnt or 0) for code, cnt in usage_rows}
        return {
            "promos": [
                {
                    "code": p.code,
                    "promo_type": p.promo_type,
                    "value": int(p.value or 0),
                    "uses_left": int(p.uses_left or 0),
                    "used_count": int(usage_map.get(str(p.code or "").upper(), 0)),
                    "expires_at": _safe_iso(p.expires_at),
                    "created_at": _safe_iso(p.created_at),
                }
                for p in rows
            ]
        }
    finally:
        s.close()


@app.post("/api/admin/promos")
async def admin_promos_create(payload: AdminPromoCreateIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    code = (payload.code or "").strip().upper()
    promo_type = (payload.promo_type or "").strip().lower()
    if promo_type not in {"discount", "days"}:
        raise HTTPException(status_code=400, detail="promo_type must be discount or days")
    s = SessionLocal()
    try:
        exists = s.query(PromoCode.id).filter(func.upper(PromoCode.code) == code).first()
        if exists:
            raise HTTPException(status_code=409, detail="Promo code already exists")
        row = PromoCode(
            code=code,
            promo_type=promo_type,
            value=int(payload.value),
            uses_left=int(payload.uses_left),
            expires_at=_parse_optional_datetime(payload.expires_at),
        )
        s.add(row)
        s.commit()
    finally:
        s.close()

    _audit_admin(actor_tg_id=actor, action="admin_promo_create", meta={"code": code, "promo_type": promo_type})
    return {"ok": True, "code": code}


@app.patch("/api/admin/promos/{code}")
async def admin_promos_update(code: str, payload: AdminPromoUpdateIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    src_code = (code or "").strip().upper()
    s = SessionLocal()
    try:
        row = s.query(PromoCode).filter(func.upper(PromoCode.code) == src_code).first()
        if not row:
            raise HTTPException(status_code=404, detail="Promo not found")

        if payload.new_code is not None and payload.new_code.strip():
            next_code = payload.new_code.strip().upper()
            if next_code != src_code:
                dup = s.query(PromoCode.id).filter(func.upper(PromoCode.code) == next_code).first()
                if dup:
                    raise HTTPException(status_code=409, detail="Promo code already exists")
                row.code = next_code

        if payload.promo_type is not None:
            ptype = (payload.promo_type or "").strip().lower()
            if ptype not in {"discount", "days"}:
                raise HTTPException(status_code=400, detail="promo_type must be discount or days")
            row.promo_type = ptype
        if payload.value is not None:
            row.value = int(payload.value)
        if payload.uses_left is not None:
            row.uses_left = int(payload.uses_left)
        if "expires_at" in payload.model_fields_set:
            row.expires_at = _parse_optional_datetime(payload.expires_at)

        s.commit()
        out_code = row.code
    finally:
        s.close()

    _audit_admin(actor_tg_id=actor, action="admin_promo_update", meta={"from": src_code, "to": out_code})
    return {"ok": True, "code": out_code}


@app.delete("/api/admin/promos/{code}")
async def admin_promos_delete(code: str, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    src_code = (code or "").strip().upper()
    s = SessionLocal()
    try:
        row = s.query(PromoCode).filter(func.upper(PromoCode.code) == src_code).first()
        if not row:
            raise HTTPException(status_code=404, detail="Promo not found")
        s.delete(row)
        s.commit()
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_promo_delete", meta={"code": src_code})
    return {"ok": True}


@app.get("/api/admin/plans")
async def admin_plans(x_telegram_init_data: str = Header(default=""), include_inactive: bool = True) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        rows = _plan_catalog_payload(s=s, only_active=not bool(include_inactive))
        return {"plans": rows}
    finally:
        s.close()


@app.post("/api/admin/plans")
async def admin_plans_create(payload: AdminPlanCreateIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    code = (payload.code or "").strip().lower()
    s = SessionLocal()
    try:
        exists = s.query(PlanCatalog.id).filter(func.lower(PlanCatalog.code) == code).first()
        if exists:
            raise HTTPException(status_code=409, detail="Plan already exists")
        now = _utcnow()
        row = PlanCatalog(
            code=code,
            label=payload.label.strip(),
            amount_rub=int(payload.amount_rub),
            amount_stars=int(payload.amount_stars),
            days=int(payload.days),
            device_limit=int(payload.device_limit),
            node_policy=(payload.node_policy or "").strip()[:32] or None,
            badge=(payload.badge or "").strip()[:32] or None,
            is_active=bool(payload.is_active),
            sort_order=int(payload.sort_order),
            created_at=now,
            updated_at=now,
        )
        s.add(row)
        s.commit()
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_plan_create", meta={"code": code})
    return {"ok": True, "code": code}


@app.patch("/api/admin/plans/{code}")
async def admin_plans_update(code: str, payload: AdminPlanUpdateIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    target = (code or "").strip().lower()
    s = SessionLocal()
    try:
        row = s.query(PlanCatalog).filter(func.lower(PlanCatalog.code) == target).first()
        if not row:
            raise HTTPException(status_code=404, detail="Plan not found")
        if payload.label is not None:
            row.label = payload.label.strip()
        if payload.amount_rub is not None:
            row.amount_rub = int(payload.amount_rub)
        if payload.amount_stars is not None:
            row.amount_stars = int(payload.amount_stars)
        if payload.days is not None:
            row.days = int(payload.days)
        if payload.device_limit is not None:
            row.device_limit = int(payload.device_limit)
        if payload.node_policy is not None:
            row.node_policy = (payload.node_policy or "").strip()[:32] or None
        if payload.badge is not None:
            row.badge = (payload.badge or "").strip()[:32] or None
        if payload.is_active is not None:
            row.is_active = bool(payload.is_active)
        if payload.sort_order is not None:
            row.sort_order = int(payload.sort_order)
        row.updated_at = _utcnow()
        s.commit()
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_plan_update", meta={"code": target})
    return {"ok": True, "code": target}


@app.delete("/api/admin/plans/{code}")
async def admin_plans_delete(code: str, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    target = (code or "").strip().lower()
    s = SessionLocal()
    try:
        row = s.query(PlanCatalog).filter(func.lower(PlanCatalog.code) == target).first()
        if not row:
            raise HTTPException(status_code=404, detail="Plan not found")
        s.delete(row)
        s.commit()
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_plan_delete", meta={"code": target})
    return {"ok": True}


@app.get("/api/admin/live-updates")
async def admin_live_updates(x_telegram_init_data: str = Header(default=""), include_inactive: bool = True) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        q = s.query(LiveUpdate)
        if not include_inactive:
            q = q.filter(LiveUpdate.is_active == True)
        rows = q.order_by(LiveUpdate.sort_order.asc(), LiveUpdate.id.desc()).limit(300).all()
        return {
            "updates": [
                {
                    "id": int(r.id),
                    "title": r.title,
                    "summary": r.summary,
                    "link": str(r.link or "").strip(),
                    "tg_link": _build_tg_post_link(
                        channel_username=getattr(r, "channel_username", None),
                        post_id=getattr(r, "post_id", None),
                        fallback_link=str(r.link or "").strip(),
                    ),
                    "channel_username": str(getattr(r, "channel_username", "") or "").strip().lstrip("@") or None,
                    "post_id": int(getattr(r, "post_id", 0) or 0) or None,
                    "published_at": _safe_iso(r.published_at),
                    "is_active": bool(r.is_active),
                    "sort_order": int(r.sort_order or 0),
                    "created_at": _safe_iso(r.created_at),
                    "updated_at": _safe_iso(r.updated_at),
                }
                for r in rows
            ]
        }
    finally:
        s.close()


@app.post("/api/admin/live-updates")
async def admin_live_updates_create(payload: AdminLiveUpdateCreateIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    channel_username = _normalize_channel_username(payload.channel_username) if payload.channel_username else None
    post_id = int(payload.post_id or 0) if payload.post_id is not None else None
    if post_id is not None and not channel_username:
        raise HTTPException(status_code=400, detail="channel_username is required when post_id is provided")
    final_link = _build_tg_post_link(
        channel_username=channel_username,
        post_id=post_id,
        fallback_link=payload.link,
    )
    if not final_link:
        raise HTTPException(status_code=400, detail="Provide either link or channel_username+post_id")
    s = SessionLocal()
    try:
        now = _utcnow()
        row = LiveUpdate(
            title=payload.title.strip(),
            summary=payload.summary.strip(),
            link=final_link,
            channel_username=channel_username,
            post_id=post_id,
            published_at=_parse_optional_datetime(payload.published_at),
            is_active=bool(payload.is_active),
            sort_order=int(payload.sort_order),
            created_at=now,
            updated_at=now,
        )
        s.add(row)
        s.commit()
        s.refresh(row)
        update_id = int(row.id)
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_live_update_create", meta={"id": update_id})
    return {"ok": True, "id": update_id}


@app.patch("/api/admin/live-updates/{update_id}")
async def admin_live_updates_update(update_id: int, payload: AdminLiveUpdateUpdateIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        row = s.query(LiveUpdate).filter(LiveUpdate.id == int(update_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Live update not found")
        if payload.title is not None:
            row.title = payload.title.strip()
        if payload.summary is not None:
            row.summary = payload.summary.strip()
        if payload.link is not None:
            row.link = payload.link.strip()
        if "channel_username" in payload.model_fields_set:
            row.channel_username = _normalize_channel_username(payload.channel_username) if payload.channel_username else None
        if "post_id" in payload.model_fields_set:
            row.post_id = int(payload.post_id or 0) or None
        if "published_at" in payload.model_fields_set:
            row.published_at = _parse_optional_datetime(payload.published_at)
        if payload.is_active is not None:
            row.is_active = bool(payload.is_active)
        if payload.sort_order is not None:
            row.sort_order = int(payload.sort_order)
        row.link = _build_tg_post_link(
            channel_username=getattr(row, "channel_username", None),
            post_id=getattr(row, "post_id", None),
            fallback_link=str(row.link or "").strip(),
        )
        if not str(row.link or "").strip():
            raise HTTPException(status_code=400, detail="Provide either link or channel_username+post_id")
        row.updated_at = _utcnow()
        s.commit()
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_live_update_update", meta={"id": int(update_id)})
    return {"ok": True, "id": int(update_id)}


@app.delete("/api/admin/live-updates/{update_id}")
async def admin_live_updates_delete(update_id: int, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        row = s.query(LiveUpdate).filter(LiveUpdate.id == int(update_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Live update not found")
        s.delete(row)
        s.commit()
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_live_update_delete", meta={"id": int(update_id)})
    return {"ok": True}


@app.get("/api/admin/start-links")
async def admin_start_links(x_telegram_init_data: str = Header(default=""), include_inactive: bool = True) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        q = s.query(StartLink)
        if not include_inactive:
            q = q.filter(StartLink.is_active == True)
        rows = q.order_by(StartLink.updated_at.desc(), StartLink.id.desc()).limit(500).all()
        bot_username = (BOT_USERNAME or "pokrov_vpnbot").lstrip("@")
        return {
            "start_links": [
                {
                    "id": int(r.id),
                    "code": str(r.code or "").strip().lower(),
                    "description": str(r.description or "").strip() or None,
                    "target_action": str(r.target_action or "").strip() or None,
                    "is_active": bool(r.is_active),
                    "bot_start_link": f"https://t.me/{bot_username}?start={str(r.code or '').strip()}",
                    "created_at": _safe_iso(getattr(r, "created_at", None)),
                    "updated_at": _safe_iso(getattr(r, "updated_at", None)),
                }
                for r in rows
            ]
        }
    finally:
        s.close()


@app.post("/api/admin/start-links")
async def admin_start_links_create(payload: AdminStartLinkCreateIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    code = re.sub(r"[^a-z0-9_-]+", "", str(payload.code or "").strip().lower())[:64]
    if len(code) < 2:
        raise HTTPException(status_code=400, detail="Invalid code")
    s = SessionLocal()
    try:
        exists = s.query(StartLink.id).filter(func.lower(StartLink.code) == code).first()
        if exists:
            raise HTTPException(status_code=409, detail="Start link already exists")
        now = _utcnow()
        row = StartLink(
            code=code,
            description=str(payload.description or "").strip()[:240] or None,
            target_action=str(payload.target_action or "").strip()[:64] or None,
            is_active=bool(payload.is_active),
            created_at=now,
            updated_at=now,
        )
        s.add(row)
        s.commit()
        s.refresh(row)
        row_id = int(row.id)
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_start_link_create", meta={"id": row_id, "code": code})
    return {"ok": True, "id": row_id, "code": code}


@app.patch("/api/admin/start-links/{link_id}")
async def admin_start_links_update(link_id: int, payload: AdminStartLinkUpdateIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        row = s.query(StartLink).filter(StartLink.id == int(link_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Start link not found")
        if payload.code is not None:
            code = re.sub(r"[^a-z0-9_-]+", "", str(payload.code or "").strip().lower())[:64]
            if len(code) < 2:
                raise HTTPException(status_code=400, detail="Invalid code")
            if code != str(row.code or "").strip().lower():
                dup = s.query(StartLink.id).filter(func.lower(StartLink.code) == code, StartLink.id != row.id).first()
                if dup:
                    raise HTTPException(status_code=409, detail="Start link already exists")
                row.code = code
        if "description" in payload.model_fields_set:
            row.description = str(payload.description or "").strip()[:240] or None
        if "target_action" in payload.model_fields_set:
            row.target_action = str(payload.target_action or "").strip()[:64] or None
        if payload.is_active is not None:
            row.is_active = bool(payload.is_active)
        row.updated_at = _utcnow()
        s.commit()
        out_code = str(row.code or "").strip().lower()
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_start_link_update", meta={"id": int(link_id), "code": out_code})
    return {"ok": True, "id": int(link_id), "code": out_code}


@app.delete("/api/admin/start-links/{link_id}")
async def admin_start_links_delete(link_id: int, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        row = s.query(StartLink).filter(StartLink.id == int(link_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Start link not found")
        row.is_active = False
        row.updated_at = _utcnow()
        s.commit()
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_start_link_deactivate", meta={"id": int(link_id)})
    return {"ok": True, "id": int(link_id)}


@app.get("/api/admin/wheel-config")
async def admin_wheel_config_get(x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        cfg = _normalized_wheel_config(_get_app_setting_json(s=s, key="wheel_config", default=DEFAULT_WHEEL_CONFIG))
        return {"wheel_config": cfg}
    finally:
        s.close()


@app.put("/api/admin/wheel-config")
async def admin_wheel_config_put(payload: AdminWheelConfigIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    normalized = _normalized_wheel_config(payload.model_dump())
    s = SessionLocal()
    try:
        _set_app_setting_json(s=s, key="wheel_config", value=normalized)
        s.commit()
    finally:
        s.close()
    _audit_admin(
        actor_tg_id=actor,
        action="admin_wheel_config_update",
        meta={"preset": normalized.get("preset"), "cooldown_hours": normalized.get("cooldown_hours")},
    )
    return {"ok": True, "wheel_config": normalized}


@app.get("/api/admin/network-rollout-config")
async def admin_network_rollout_config_get(x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        return {"network_rollout_config": load_network_rollout_config(session=s)}
    finally:
        s.close()


@app.put("/api/admin/network-rollout-config")
async def admin_network_rollout_config_put(payload: dict[str, Any], x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    normalized = normalized_network_rollout_config(payload if isinstance(payload, dict) else {})
    s = SessionLocal()
    try:
        _set_app_setting_json(s=s, key=NETWORK_ROLLOUT_CONFIG_KEY, value=normalized)
        s.commit()
    finally:
        s.close()
    _audit_admin(
        actor_tg_id=actor,
        action="admin_network_rollout_config_put",
        meta={
            "version": normalized.get("version"),
            "default_transport_profile": ((normalized.get("defaults") or {}).get("transport_profile")),
        },
    )
    return {"ok": True, "network_rollout_config": normalized}


@app.get("/api/admin/promo-slots")
async def admin_promo_slots_get(x_telegram_init_data: str = Header(default="")) -> dict[str, Any]:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        config = _normalized_promo_slots_config(
            _get_app_setting_json(s=s, key=PROMO_SLOTS_CONFIG_KEY, default={}),
            strict=False,
        )
        slot_map, content_map = _promo_slot_catalog_maps()
        return {
            "promo_slots": {
                **config,
                "catalog": {
                    "version": str(_PROMO_SLOTS.get("version") or ""),
                    "mode": str(_PROMO_SLOTS.get("mode") or "whitelist_slots"),
                    "fallback_behavior": str(_PROMO_SLOTS.get("fallback_behavior") or "contextual_only_when_remote_unavailable"),
                    "slots": list(slot_map.values()),
                    "content_catalog": list(content_map.values()),
                },
            }
        }
    finally:
        s.close()


@app.put("/api/admin/promo-slots")
async def admin_promo_slots_put(payload: AdminPromoSlotsPutIn, x_telegram_init_data: str = Header(default="")) -> dict[str, Any]:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    normalized = _normalized_promo_slots_config({"assignments": payload.model_dump().get("assignments") or []}, strict=True)
    s = SessionLocal()
    try:
        _set_app_setting_json(s=s, key=PROMO_SLOTS_CONFIG_KEY, value={"assignments": normalized.get("assignments") or []})
        s.commit()
    finally:
        s.close()

    _audit_admin(
        actor_tg_id=actor,
        action="admin_promo_slots_put",
        meta={"assignments": len(list(normalized.get("assignments") or []))},
    )
    return {"ok": True, "promo_slots": normalized}


@app.post("/api/admin/campaign-links/build")
async def admin_campaign_links_build(payload: AdminCampaignLinksBuildIn, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    promo = _sanitize_deeplink_token(payload.promo_code, max_len=20, uppercase=True)
    campaign = _sanitize_deeplink_token(payload.campaign_key, max_len=64, uppercase=False)
    plan = (payload.plan_code or "").strip().lower()[:32]
    source = (payload.source or "bot").strip().lower()[:16]
    start_payload = ""
    if campaign and promo:
        start_payload = f"campaign_{campaign}__promo_{promo}"
    elif promo:
        start_payload = f"promo_{promo}"
    elif campaign:
        start_payload = f"campaign_{campaign}"
    if start_payload and len(start_payload) > 64:
        raise HTTPException(status_code=400, detail="Telegram start payload exceeds 64 chars")
    bot_username = (BOT_USERNAME or "pokrov_vpnbot").lstrip("@")
    bot_start_link = f"https://t.me/{bot_username}" + (f"?start={start_payload}" if start_payload else "")

    base_checkout = _public_checkout_url() or "https://pay.pokrov.space/checkout/"
    parsed = urlparse(base_checkout)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    q["source"] = source or "bot"
    if plan:
        q["plan"] = plan
    if promo:
        q["promo"] = promo
    if campaign:
        q["campaign"] = campaign
    # Public campaign links cannot mint a valid checkout ticket without a bound user,
    # so the "checkout" action must stay in a safe bot-first flow.
    checkout_link = bot_start_link

    webapp_base = _safe_public_url(Settings.WEBAPP_URL) or "https://app.pokrov.space/"
    wp = urlparse(webapp_base)
    wq = dict(parse_qsl(wp.query, keep_blank_values=True))
    if promo:
        wq["promo"] = promo
    if campaign:
        wq["campaign"] = campaign
    if plan:
        wq["plan"] = plan
    webapp_link = f"{wp.scheme}://{wp.netloc}{wp.path or '/'}?{urlencode(wq)}" if wp.scheme and wp.netloc else f"/?{urlencode(wq)}"
    return {
        "ok": True,
        "bot_start_link": bot_start_link,
        "checkout_link": checkout_link,
        "checkout_mode": "bot_fallback",
        "checkout_reason": "checkout_ticket_requires_bound_user",
        "webapp_link": webapp_link,
    }


@app.get("/api/admin/referrals/pending")
async def admin_referrals_pending(
    x_telegram_init_data: str = Header(default=""),
    limit: int = 200,
    status: str = "",
) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        q = s.query(ReferralBonusQueue)
        status_norm = str(status or "").strip().lower()
        if status_norm:
            q = q.filter(func.lower(ReferralBonusQueue.status) == status_norm)
        rows = q.order_by(ReferralBonusQueue.id.desc()).limit(max(1, min(int(limit), 1000))).all()
        return {
            "rows": [
                {
                    "id": int(r.id),
                    "order_id": str(r.order_id or ""),
                    "referrer_tg_id": int(r.referrer_tg_id),
                    "referred_tg_id": int(r.referred_tg_id),
                    "queued_at": _safe_iso(r.queued_at),
                    "ready_at": _safe_iso(r.ready_at),
                    "status": str(r.status or ""),
                    "processed_at": _safe_iso(r.processed_at),
                    "meta": _json_obj(getattr(r, "meta", None)),
                }
                for r in rows
            ]
        }
    finally:
        s.close()


@app.post("/api/admin/referrals/process")
async def admin_referrals_process(payload: AdminReferralQueueProcessIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    out = _process_referral_bonus_queue(limit=int(payload.limit), force_without_activity=bool(payload.force_without_activity))
    _audit_admin(
        actor_tg_id=actor,
        action="admin_referrals_process",
        meta={"limit": int(payload.limit), "force_without_activity": bool(payload.force_without_activity), **out},
    )
    return {"ok": True, **out}


@app.get("/api/admin/loyalty-config")
async def admin_loyalty_config_get(x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        return {"loyalty_config": _loyalty_config(s=s)}
    finally:
        s.close()


@app.put("/api/admin/loyalty-config")
async def admin_loyalty_config_put(payload: dict[str, Any], x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    normalized = _normalized_loyalty_config(payload if isinstance(payload, dict) else {})
    s = SessionLocal()
    try:
        _set_app_setting_json(s=s, key="loyalty_config", value=normalized)
        s.commit()
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_loyalty_config_put", meta=normalized)
    return {"ok": True, "loyalty_config": normalized}


@app.get("/api/admin/campaigns")
async def admin_campaigns_get(x_telegram_init_data: str = Header(default=""), limit: int = 200) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        rows = (
            s.query(IncentiveCampaign)
            .order_by(IncentiveCampaign.updated_at.desc(), IncentiveCampaign.id.desc())
            .limit(max(1, min(int(limit), 1000)))
            .all()
        )
        return {
            "campaigns": [
                {
                    "id": int(r.id),
                    "name": str(r.name or ""),
                    "campaign_type": str(r.campaign_type or ""),
                    "target_value": str(r.target_value or ""),
                    "segment": str(r.segment or ""),
                    "starts_at": _safe_iso(r.starts_at),
                    "ends_at": _safe_iso(r.ends_at),
                    "max_activations": int(r.max_activations or -1),
                    "activations_count": int(r.activations_count or 0),
                    "auto_disable": bool(r.auto_disable),
                    "is_active": bool(r.is_active),
                    "created_by": int(r.created_by) if r.created_by is not None else None,
                    "metadata": _json_obj(getattr(r, "metadata_json", None)),
                    "created_at": _safe_iso(r.created_at),
                    "updated_at": _safe_iso(r.updated_at),
                }
                for r in rows
            ]
        }
    finally:
        s.close()


@app.post("/api/admin/campaigns")
async def admin_campaigns_create(payload: AdminCampaignCreateIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    ctype = str(payload.campaign_type or "").strip().lower()
    if ctype not in {"promo", "gift"}:
        raise HTTPException(status_code=400, detail="campaign_type must be promo or gift")
    starts_at = _parse_optional_datetime(payload.starts_at)
    ends_at = _parse_optional_datetime(payload.ends_at)
    if starts_at and ends_at and starts_at > ends_at:
        raise HTTPException(status_code=400, detail="starts_at must be <= ends_at")
    now = _utcnow()
    s = SessionLocal()
    try:
        row = IncentiveCampaign(
            name=str(payload.name or "").strip()[:120],
            campaign_type=ctype,
            target_value=str(payload.target_value or "").strip().upper()[:64],
            segment=str(payload.segment or "all_active").strip().lower()[:32],
            starts_at=starts_at,
            ends_at=ends_at,
            max_activations=int(payload.max_activations),
            activations_count=0,
            auto_disable=bool(payload.auto_disable),
            is_active=bool(payload.is_active),
            created_by=actor,
            metadata_json=json.dumps(payload.metadata or {}, ensure_ascii=False, separators=(",", ":")),
            created_at=now,
            updated_at=now,
        )
        s.add(row)
        s.commit()
        s.refresh(row)
        out_id = int(row.id)
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_campaign_create", meta={"campaign_id": out_id, "campaign_type": ctype})
    return {"ok": True, "id": out_id}


@app.patch("/api/admin/campaigns/{campaign_id}")
async def admin_campaigns_patch(
    campaign_id: int,
    payload: AdminCampaignUpdateIn,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        row = s.query(IncentiveCampaign).filter(IncentiveCampaign.id == int(campaign_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Campaign not found")
        if payload.name is not None:
            row.name = str(payload.name).strip()[:120]
        if payload.segment is not None:
            row.segment = str(payload.segment).strip().lower()[:32]
        if payload.starts_at is not None:
            row.starts_at = _parse_optional_datetime(payload.starts_at)
        if payload.ends_at is not None:
            row.ends_at = _parse_optional_datetime(payload.ends_at)
        if row.starts_at and row.ends_at and row.starts_at > row.ends_at:
            raise HTTPException(status_code=400, detail="starts_at must be <= ends_at")
        if payload.max_activations is not None:
            row.max_activations = int(payload.max_activations)
        if payload.auto_disable is not None:
            row.auto_disable = bool(payload.auto_disable)
        if payload.is_active is not None:
            row.is_active = bool(payload.is_active)
        if payload.metadata is not None:
            row.metadata_json = json.dumps(payload.metadata or {}, ensure_ascii=False, separators=(",", ":"))
        row.updated_at = _utcnow()
        s.commit()
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_campaign_patch", meta={"campaign_id": int(campaign_id)})
    return {"ok": True, "id": int(campaign_id)}


@app.delete("/api/admin/campaigns/{campaign_id}")
async def admin_campaigns_delete(campaign_id: int, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        row = s.query(IncentiveCampaign).filter(IncentiveCampaign.id == int(campaign_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Campaign not found")
        row.is_active = False
        row.updated_at = _utcnow()
        s.commit()
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_campaign_disable", meta={"campaign_id": int(campaign_id)})
    return {"ok": True}


@app.get("/api/admin/templates")
async def admin_templates(x_telegram_init_data: str = Header(default=""), limit: int = 200) -> dict:
    _require_admin(x_telegram_init_data)
    lim = max(1, min(int(limit), 500))
    s = SessionLocal()
    try:
        rows = s.query(Template).order_by(Template.created_at.desc(), Template.id.desc()).limit(lim).all()
        return {
            "templates": [
                {"key": t.key, "text": t.text, "created_at": _safe_iso(t.created_at)}
                for t in rows
            ]
        }
    finally:
        s.close()


@app.post("/api/admin/templates")
async def admin_templates_create(payload: AdminTemplateCreateIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    key = (payload.key or "").strip().lower()
    text_val = (payload.text or "").strip()
    s = SessionLocal()
    try:
        exists = s.query(Template.id).filter(func.lower(Template.key) == key).first()
        if exists:
            raise HTTPException(status_code=409, detail="Template already exists")
        row = Template(key=key, text=text_val)
        s.add(row)
        s.commit()
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_template_create", meta={"key": key})
    return {"ok": True, "key": key}


@app.patch("/api/admin/templates/{key}")
async def admin_templates_update(key: str, payload: AdminTemplateUpdateIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    src_key = (key or "").strip().lower()
    s = SessionLocal()
    try:
        row = s.query(Template).filter(func.lower(Template.key) == src_key).first()
        if not row:
            raise HTTPException(status_code=404, detail="Template not found")
        if payload.new_key is not None and payload.new_key.strip():
            new_key = payload.new_key.strip().lower()
            if new_key != src_key:
                exists = s.query(Template.id).filter(func.lower(Template.key) == new_key).first()
                if exists:
                    raise HTTPException(status_code=409, detail="Template key already exists")
                row.key = new_key
        if payload.text is not None:
            row.text = payload.text.strip()
        s.commit()
        out_key = row.key
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_template_update", meta={"from": src_key, "to": out_key})
    return {"ok": True, "key": out_key}


@app.delete("/api/admin/templates/{key}")
async def admin_templates_delete(key: str, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    src_key = (key or "").strip().lower()
    s = SessionLocal()
    try:
        row = s.query(Template).filter(func.lower(Template.key) == src_key).first()
        if not row:
            raise HTTPException(status_code=404, detail="Template not found")
        s.delete(row)
        s.commit()
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_template_delete", meta={"key": src_key})
    return {"ok": True}


@app.get("/api/admin/gift-codes")
async def admin_gift_codes(x_telegram_init_data: str = Header(default=""), limit: int = 100) -> dict:
    _require_admin(x_telegram_init_data)
    lim = max(1, min(int(limit), 500))
    s = SessionLocal()
    try:
        rows = s.query(GiftCard).order_by(GiftCard.created_at.desc(), GiftCard.id.desc()).limit(lim).all()
        return {
            "gift_codes": [
                {
                    "code": g.code,
                    "card_type": g.card_type,
                    "days": int((GIFT_CARD_TYPES.get(g.card_type or "", {}) or {}).get("days", 0)),
                    "stars": int((GIFT_CARD_TYPES.get(g.card_type or "", {}) or {}).get("stars", 0)),
                    "created_by": int(g.created_by or 0),
                    "created_at": _safe_iso(g.created_at),
                    "redeemed_by": int(g.redeemed_by) if g.redeemed_by is not None else None,
                    "redeemed_at": _safe_iso(g.redeemed_at),
                }
                for g in rows
            ]
        }
    finally:
        s.close()


@app.post("/api/admin/access-keys/issue")
async def admin_access_keys_issue(payload: AdminAccessKeyIssueIn, x_telegram_init_data: str = Header(default="")) -> dict[str, Any]:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    plan_code = str(payload.plan_code or "").strip().lower()
    s = SessionLocal()
    try:
        plan = _resolve_plan_config(s=s, code=plan_code)
        normalized_plan = _normalized_plan_payload(plan, fallback_code=plan_code)
        if not normalized_plan:
            raise HTTPException(status_code=400, detail="Unsupported plan_code")

        issued: list[dict[str, Any]] = []
        for _ in range(int(payload.quantity or 1)):
            code = _generate_gift_code_for_admin(s)
            row = GiftCard(code=code, card_type=normalized_plan["code"], created_by=actor)
            s.add(row)
            issued.append(
                {
                    "key": code,
                    "plan": normalized_plan,
                    "issued_at": _safe_iso(_utcnow()),
                }
            )
        s.commit()
    finally:
        s.close()

    _audit_admin(
        actor_tg_id=actor,
        action="admin_access_keys_issue",
        meta={"plan_code": plan_code, "quantity": int(payload.quantity or 1)},
    )
    return {
        "ok": True,
        "plan": normalized_plan,
        "issued": issued,
    }


@app.post("/api/admin/gift-codes")
async def admin_gift_codes_create(payload: AdminGiftCodeCreateIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    card_type = (payload.card_type or "").strip().lower()
    card = GIFT_CARD_TYPES.get(card_type)
    if not card:
        raise HTTPException(status_code=400, detail="Unsupported card_type")
    s = SessionLocal()
    try:
        code = _generate_gift_code_for_admin(s)
        row = GiftCard(code=code, card_type=card_type, created_by=actor)
        s.add(row)
        s.commit()
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_gift_code_create", meta={"code": code, "card_type": card_type})
    return {
        "ok": True,
        "gift_code": {
            "code": code,
            "card_type": card_type,
            "days": int(card.get("days", 0)),
            "stars": int(card.get("stars", 0)),
        },
    }


@app.get("/api/admin/tickets")
async def admin_tickets(x_telegram_init_data: str = Header(default=""), status: str = "", limit: int = 30) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        lim = max(1, min(int(limit), 100))
        st = (status or "").strip().lower()
        if st:
            rows = (
                s.query(SupportTicket)
                .filter(SupportTicket.status == st)
                .order_by(SupportTicket.updated_at.desc(), SupportTicket.id.desc())
                .limit(lim)
                .all()
            )
        else:
            rows = list_active_tickets(s, limit=lim)
        return {"tickets": [_ticket_row(t, list_ticket_messages(s, t.id, limit=1)) for t in rows]}
    finally:
        s.close()


@app.post("/api/admin/tickets/{ticket_id}/reply")
async def admin_ticket_reply(ticket_id: int, payload: AdminTicketReplyIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        ticket = get_ticket_by_id(s, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        add_ticket_message(
            s,
            ticket_id=ticket.id,
            sender_tg_id=actor,
            sender_role="admin",
            body=payload.body,
            media_type=payload.media_type,
            media_file_id=payload.media_file_id,
            media_payload=payload.media_payload,
        )
        set_ticket_status(s, ticket=ticket, status=STATUS_IN_PROGRESS, assigned_admin_tg_id=actor)
        s.commit()
        msgs = list_ticket_messages(s, ticket.id, limit=100)
    finally:
        s.close()

    await _telegram_send_message(int(ticket.user_tg_id), f"💬 Ответ оператора в обращении #{ticket.id}.")
    _audit_admin(actor_tg_id=actor, action="admin_ticket_reply", target_tg_id=int(ticket.user_tg_id), meta={"ticket_id": ticket.id})
    return {"ticket": _ticket_row(ticket, msgs)}


@app.post("/api/admin/tickets/{ticket_id}/status")
async def admin_ticket_status(ticket_id: int, payload: AdminTicketStatusIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    new_status = (payload.status or "").strip().lower()
    if new_status not in {STATUS_OPEN, STATUS_IN_PROGRESS, STATUS_CLOSED}:
        raise HTTPException(status_code=400, detail="Unsupported status")
    s = SessionLocal()
    try:
        ticket = get_ticket_by_id(s, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        set_ticket_status(s, ticket=ticket, status=new_status, assigned_admin_tg_id=actor if new_status == STATUS_IN_PROGRESS else None)
        s.commit()
        msgs = list_ticket_messages(s, ticket.id, limit=100)
    finally:
        s.close()

    _audit_admin(actor_tg_id=actor, action="admin_ticket_status", target_tg_id=int(ticket.user_tg_id), meta={"ticket_id": ticket.id, "status": new_status})
    if new_status == STATUS_CLOSED:
        await _telegram_send_message(int(ticket.user_tg_id), f"✅ Обращение #{ticket.id} закрыто оператором.")
    return {"ticket": _ticket_row(ticket, msgs)}


@app.get("/api/admin/nodes/health")
async def admin_nodes_health(x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        rows = s.query(Node).order_by(Node.enabled.desc(), Node.health_score.desc(), Node.weight.desc(), Node.code.asc()).all()
        window_start = _utcnow() - timedelta(hours=24)
        peak_by_code = {
            str(node_code or ""): (float(peak_mbps) if peak_mbps is not None else None)
            for node_code, peak_mbps in (
                s.query(
                    NodeHealthSample.node_code,
                    func.max(NodeHealthSample.network_total_mbps),
                )
                .filter(NodeHealthSample.sampled_at >= window_start)
                .group_by(NodeHealthSample.node_code)
                .all()
            )
        }
        mapped_counts = {
            int(node_id): int(count or 0)
            for node_id, count in (
                s.query(UserNode.node_id, func.count(func.distinct(UserNode.tg_id)))
                .group_by(UserNode.node_id)
                .all()
            )
        }
    finally:
        s.close()

    online_summary_by_code: dict[str, dict[str, Any]] = {}
    panel = ControlPanel()
    try:
        await panel.login()
        online_summary_by_code = await panel.get_node_online_summaries(
            node_codes=[str(getattr(n, "code", "") or "").strip() for n in rows if str(getattr(n, "code", "") or "").strip()]
        )
    except Exception:
        online_summary_by_code = {}
    finally:
        await panel.close()

    return {
        "nodes": [
            _serialize_admin_node(
                n,
                mapped_users=mapped_counts.get(int(n.id), 0),
                network_peak_mbps_24h=peak_by_code.get(str(n.code or ""), None),
                online_keys_now=int((online_summary_by_code.get(str(n.code or ""), {}) or {}).get("online_keys_now") or 0),
                online_connections_now=int((online_summary_by_code.get(str(n.code or ""), {}) or {}).get("online_connections_now") or 0),
            )
            for n in rows
        ]
    }


async def _build_admin_node_drift_report(*, only_codes: list[str] | None = None) -> dict:
    panel = ControlPanel()
    try:
        await panel.login()
        return await panel.get_node_drift_report(node_codes=only_codes or [])
    finally:
        await panel.close()


@app.get("/api/admin/nodes/drift")
async def admin_nodes_drift(
    x_telegram_init_data: str = Header(default=""),
    only: str = Query(default=""),
) -> dict:
    _require_admin(x_telegram_init_data)
    only_codes = [part.strip().lower() for part in str(only or "").split(",") if part.strip()]
    result = _build_admin_node_drift_report(only_codes=only_codes)
    if inspect.isawaitable(result):
        return await result
    return result


@app.post("/api/admin/nodes/sync")
async def admin_nodes_sync(payload: AdminNodeSyncIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        if payload.tg_id:
            users = s.query(User).filter(User.tg_id == int(payload.tg_id)).all()
        else:
            segment = (payload.segment or "active").strip().lower()
            q = s.query(User).filter(User.tg_id > 0)
            if segment == "active":
                q = q.filter(User.is_active == True)
            elif segment == "free":
                q = q.filter(func.upper(User.sub_type) == "FREE")
            elif segment == "paid":
                q = q.filter(func.upper(User.sub_type) == "PAID")
            else:
                raise HTTPException(status_code=400, detail="Unsupported sync segment")
            users = q.order_by(User.created_at.asc()).limit(max(1, min(int(payload.limit), 1000))).all()
    finally:
        s.close()

    panel = ControlPanel()
    synced = 0
    failed = 0
    try:
        await panel.login()
        for u in users:
            ok = await panel.enable_client(u.uuid, True)
            if ok:
                synced += 1
            else:
                failed += 1
    finally:
        await panel.close()

    _audit_admin(
        actor_tg_id=actor,
        action="admin_nodes_sync",
        meta={"synced": synced, "failed": failed, "count": len(users), "segment": payload.segment, "tg_id": payload.tg_id},
    )
    return {"ok": True, "synced": synced, "failed": failed, "count": len(users)}


@app.post("/api/admin/nodes/{node_code}/drain")
async def admin_node_drain(node_code: str, payload: AdminNodeLifecycleIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    wanted = str(node_code or "").strip().lower()
    s = SessionLocal()
    try:
        node = s.query(Node).filter(func.lower(Node.code) == wanted).first()
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        node.enabled = True
        node.accepting_new_clients = False
        node.is_draining = True
        mapped_users = (
            s.query(func.count(func.distinct(UserNode.tg_id)))
            .filter(UserNode.node_id == int(node.id))
            .scalar()
            or 0
        )
        s.commit()
        s.refresh(node)
        payload_node = _serialize_admin_node(node, mapped_users=int(mapped_users))
    finally:
        s.close()

    _audit_admin(actor_tg_id=actor, action="admin_node_drain", meta={"node_code": wanted, "mapped_users": int(mapped_users)})
    return {"ok": True, "node": payload_node}


@app.post("/api/admin/nodes/{node_code}/enable")
async def admin_node_enable(node_code: str, payload: AdminNodeLifecycleIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    wanted = str(node_code or "").strip().lower()
    s = SessionLocal()
    try:
        node = s.query(Node).filter(func.lower(Node.code) == wanted).first()
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        node.enabled = True
        node.accepting_new_clients = True
        node.is_draining = False
        mapped_users = (
            s.query(func.count(func.distinct(UserNode.tg_id)))
            .filter(UserNode.node_id == int(node.id))
            .scalar()
            or 0
        )
        s.commit()
        s.refresh(node)
        payload_node = _serialize_admin_node(node, mapped_users=int(mapped_users))
    finally:
        s.close()

    _audit_admin(actor_tg_id=actor, action="admin_node_enable", meta={"node_code": wanted, "mapped_users": int(mapped_users)})
    return {"ok": True, "node": payload_node}


@app.post("/api/admin/nodes/{node_code}/disable")
async def admin_node_disable(node_code: str, payload: AdminNodeLifecycleIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    wanted = str(node_code or "").strip().lower()
    s = SessionLocal()
    try:
        node = s.query(Node).filter(func.lower(Node.code) == wanted).first()
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        mapped_users = (
            s.query(func.count(func.distinct(UserNode.tg_id)))
            .filter(UserNode.node_id == int(node.id))
            .scalar()
            or 0
        )
        if int(mapped_users) > 0 and not bool(payload.force):
            raise HTTPException(status_code=409, detail="Node still has mapped users. Run resync first or use force.")
        node.enabled = False
        node.accepting_new_clients = False
        node.is_draining = False
        s.commit()
        s.refresh(node)
        payload_node = _serialize_admin_node(node, mapped_users=int(mapped_users))
    finally:
        s.close()

    _audit_admin(
        actor_tg_id=actor,
        action="admin_node_disable",
        meta={"node_code": wanted, "mapped_users": int(mapped_users), "forced": bool(payload.force)},
    )
    return {"ok": True, "node": payload_node}


@app.post("/api/admin/nodes/{node_code}/resync")
async def admin_node_resync(node_code: str, payload: AdminNodeResyncIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    wanted = str(node_code or "").strip().lower()
    s = SessionLocal()
    try:
        source = s.query(Node).filter(func.lower(Node.code) == wanted).first()
        if not source:
            raise HTTPException(status_code=404, detail="Node not found")
        rows = (
            s.query(UserNode, User)
            .join(User, User.tg_id == UserNode.tg_id)
            .filter(UserNode.node_id == int(source.id))
            .order_by(UserNode.created_at.asc(), UserNode.id.asc())
            .limit(max(1, min(int(payload.limit), 1000)))
            .all()
        )
    finally:
        s.close()

    panel = ControlPanel()
    migrated = 0
    failed = 0
    skipped = 0
    details: list[dict[str, Any]] = []
    try:
        if not payload.dry_run:
            await panel.login()
        for _user_node, user in rows:
            s = SessionLocal()
            try:
                target_codes = _target_node_codes_for_resync(s, user, wanted, enabled_nodes(s))
            finally:
                s.close()
            if not target_codes:
                skipped += 1
                details.append({"tg_id": int(user.tg_id), "status": "no_target", "target_codes": []})
                continue
            if payload.dry_run:
                details.append({"tg_id": int(user.tg_id), "status": "planned", "target_codes": target_codes})
                continue

            sub_id = str(getattr(user, "sub_token", "") or user.tg_id)
            ensure_results = await panel.ensure_user_on_all_nodes(
                tg_id=int(user.tg_id),
                client_uuid=str(user.uuid),
                email=str(user.email),
                sub_id=sub_id,
                enable=True,
                only_node_codes=target_codes,
            )
            if not any(bool(v) for v in ensure_results.values()):
                failed += 1
                details.append(
                    {
                        "tg_id": int(user.tg_id),
                        "status": "ensure_failed",
                        "target_codes": target_codes,
                        "ensure_results": ensure_results,
                    }
                )
                continue

            disable_results = await panel.set_existing_user_enabled_on_nodes(
                tg_id=int(user.tg_id),
                node_codes=[wanted],
                enable=False,
                sub_id=sub_id,
            )
            if not any(bool(v) for v in disable_results.values()):
                failed += 1
                details.append(
                    {
                        "tg_id": int(user.tg_id),
                        "status": "disable_failed",
                        "target_codes": target_codes,
                        "ensure_results": ensure_results,
                        "disable_results": disable_results,
                    }
                )
                continue

            s = SessionLocal()
            try:
                source = s.query(Node).filter(func.lower(Node.code) == wanted).first()
                target_nodes = (
                    s.query(Node)
                    .filter(func.lower(Node.code).in_([code.lower() for code in target_codes]))
                    .all()
                )
                existing_node_ids = {
                    int(row.node_id)
                    for row in s.query(UserNode).filter(UserNode.tg_id == int(user.tg_id)).all()
                }
                for target_node in target_nodes:
                    if int(target_node.id) in existing_node_ids:
                        continue
                    s.add(
                        UserNode(
                            tg_id=int(user.tg_id),
                            node_id=int(target_node.id),
                            client_uuid=str(user.uuid),
                            panel_email=str(user.email),
                        )
                    )
                if source:
                    s.query(UserNode).filter(UserNode.tg_id == int(user.tg_id), UserNode.node_id == int(source.id)).delete()
                s.commit()
            finally:
                s.close()
            migrated += 1
            details.append(
                {
                    "tg_id": int(user.tg_id),
                    "status": "migrated",
                    "target_codes": target_codes,
                    "ensure_results": ensure_results,
                    "disable_results": disable_results,
                }
            )
    finally:
        if not payload.dry_run:
            await panel.close()

    _audit_admin(
        actor_tg_id=actor,
        action="admin_node_resync",
        meta={
            "node_code": wanted,
            "count": len(rows),
            "migrated": migrated,
            "failed": failed,
            "skipped": skipped,
            "dry_run": bool(payload.dry_run),
        },
    )
    return {
        "ok": True,
        "node_code": wanted,
        "count": len(rows),
        "migrated": migrated,
        "failed": failed,
        "skipped": skipped,
        "dry_run": bool(payload.dry_run),
        "details": details,
    }


def _transport_profiles_payload(node: Any) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for profile in node_transport_profiles(node, include_disabled=True):
        name = str(profile.get("name") or "").strip()
        if not name:
            continue
        out[name] = dict(profile)
    return out


def _node_transport_profile(node: Any, transport_profile: str | None) -> dict[str, Any]:
    return transport_profile_by_name(
        node,
        transport_profile or LEGACY_REALITY_FALLBACK,
        include_disabled=True,
        allow_operator_lab=True,
    )


def _node_outbound_from_transport_profile(*, user_uuid: str, node: Any, tag: str, transport_profile: str | None) -> dict[str, Any]:
    profile = _node_transport_profile(node, transport_profile)
    kind = str(profile.get("kind") or "reality").strip().lower()
    tls: dict[str, Any] = {
        "enabled": True,
        "server_name": str(profile.get("tls_server_name") or getattr(node, "reality_sni", "") or ""),
        "utls": {
            "enabled": True,
            "fingerprint": str(profile.get("fingerprint") or getattr(node, "fingerprint", "") or "firefox"),
        },
    }
    outbound: dict[str, Any] = {
        "type": "vless",
        "tag": tag,
        "server": str(profile.get("host") or getattr(node, "host", "") or ""),
        "server_port": int(profile.get("port") or getattr(node, "vless_port", 443) or 443),
        "uuid": user_uuid,
        "tls": tls,
        "packet_encoding": "xudp",
    }
    flow = str(profile.get("flow") or getattr(node, "flow", "") or "").strip()
    if flow:
        outbound["flow"] = flow

    if kind == "grpc":
        outbound["transport"] = {
            "type": "grpc",
            "service_name": str(profile.get("grpc_service_name") or "").strip(),
        }
        outbound.pop("flow", None)
        return outbound

    if kind == "xhttp":
        outbound["transport"] = {
            "type": "http",
            "path": str(profile.get("xhttp_path") or "/").strip() or "/",
        }
        outbound.pop("flow", None)
        return outbound

    tls["reality"] = {
        "enabled": True,
        "public_key": str(profile.get("reality_public_key") or getattr(node, "reality_pbk", "") or ""),
        "short_id": str(profile.get("reality_short_id") or getattr(node, "reality_sid", "") or ""),
    }
    return outbound


def _filter_nodes_for_transport_profile(*, nodes: list, rollout_config: dict[str, Any], transport_profile: str) -> list:
    allowlist = set(transport_node_allowlist(rollout_config, transport_profile))
    if not allowlist:
        return list(nodes)
    return [
        node
        for node in nodes
        if str(getattr(node, "code", "") or "").strip().lower() in allowlist
    ]


def _node_supports_transport_profile(node: Any, transport_profile: str | None) -> bool:
    requested = str(transport_profile or LEGACY_REALITY_FALLBACK).strip() or LEGACY_REALITY_FALLBACK
    profile = transport_profile_by_name(
        node,
        requested,
        include_disabled=False,
        allow_operator_lab=True,
    )
    return str(profile.get("name") or "") == requested and bool(profile.get("enabled"))


def _managed_manifest_fallback_order(transport_profile: str) -> list[str]:
    primary = str(transport_profile or LEGACY_REALITY_FALLBACK).strip() or LEGACY_REALITY_FALLBACK
    order = [primary]
    if primary != LEGACY_REALITY_FALLBACK:
        order.append(LEGACY_REALITY_FALLBACK)
    return order


def _synthetic_transport_node() -> Any:
    connect_host = public_connect_host()
    transport_profiles = [
        {
            "name": LEGACY_REALITY_FALLBACK,
            "enabled": True,
            "kind": "reality",
            "inbound_id": 1,
            "host": connect_host,
            "port": 443,
            "tls_server_name": connect_host,
            "reality_public_key": "",
            "reality_short_id": "",
            "fingerprint": "firefox",
            "flow": "xtls-rprx-vision",
        },
        {
            "name": "grpc_443_primary",
            "enabled": True,
            "kind": "grpc",
            "inbound_id": 2,
            "host": connect_host,
            "port": 443,
            "tls_server_name": f"grpc.{connect_host}",
            "fingerprint": "firefox",
            "grpc_service_name": "pokrov-grpc",
        },
        {
            "name": RESERVE_XHTTP_CDN,
            "enabled": True,
            "kind": "xhttp",
            "inbound_id": 4,
            "host": connect_host,
            "port": 443,
            "tls_server_name": f"cdn.{connect_host}",
            "fingerprint": "firefox",
            "xhttp_path": "/reserve-xhttp",
        },
        {
            "name": OPERATOR_LAB,
            "enabled": True,
            "kind": "xhttp",
            "inbound_id": 3,
            "host": connect_host,
            "port": 443,
            "tls_server_name": f"xhttp.{connect_host}",
            "fingerprint": "firefox",
            "xhttp_path": "/xhttp",
        },
    ]
    return SimpleNamespace(
        code="default",
        name="Default",
        host=connect_host,
        vless_port=443,
        reality_sni=connect_host,
        reality_pbk="",
        reality_sid="",
        fingerprint="firefox",
        flow="xtls-rprx-vision",
        inbound_id=1,
        transport_profiles_json=json.dumps(transport_profiles, ensure_ascii=False),
    )


def _effective_transport_nodes(*, nodes: list[Any], transport_profile: str, rollout_config: dict[str, Any]) -> list[Any]:
    filtered = _filter_nodes_for_transport_profile(
        nodes=nodes,
        rollout_config=rollout_config,
        transport_profile=transport_profile,
    )
    supporting = [
        node for node in filtered if _node_supports_transport_profile(node, transport_profile)
    ]
    if supporting:
        return supporting
    if str(transport_profile or LEGACY_REALITY_FALLBACK).strip() == LEGACY_REALITY_FALLBACK and filtered:
        return filtered
    return [_synthetic_transport_node()]


def _xray_multi_node_config(*, user_uuid: str, nodes: list, title: str, transport_profile: str) -> dict[str, Any]:
    outbounds: list[dict[str, Any]] = []
    selector_tag = "pokrov-selector"
    for node in nodes:
        profile = _node_transport_profile(node, transport_profile)
        tag = str(getattr(node, "code", "") or getattr(node, "name", "") or "node").strip() or "node"
        outbounds.append(
            {
                "tag": tag,
                "protocol": "vless",
                "settings": {
                    "vnext": [
                        {
                            "address": str(profile.get("host") or getattr(node, "host", "") or ""),
                            "port": int(profile.get("port") or getattr(node, "vless_port", 443) or 443),
                            "users": [{"id": user_uuid, "encryption": "none"}],
                        }
                    ]
                },
                "streamSettings": {
                    "network": "xhttp",
                    "security": "tls",
                    "tlsSettings": {
                        "serverName": str(profile.get("tls_server_name") or getattr(node, "reality_sni", "") or ""),
                    },
                    "xhttpSettings": {
                        "path": str(profile.get("xhttp_path") or "/").strip() or "/",
                    },
                },
            }
        )

    return {
        "log": {"loglevel": "warning"},
        "routing": {"domainStrategy": "AsIs"},
        "outbounds": [
            {
                "tag": selector_tag,
                "protocol": "selector",
                "settings": {"actors": [item["tag"] for item in outbounds]},
            },
            *outbounds,
        ],
        "_meta": {"title": title},
    }


def _managed_manifest_payload(*, user: User, nodes: list, title: str, transport_profile: str) -> tuple[str, dict[str, Any]]:
    if str(transport_profile or "").strip() in {OPERATOR_LAB, RESERVE_XHTTP_CDN}:
        return (
            "xray-json",
            _xray_multi_node_config(
                user_uuid=str(user.uuid),
                nodes=nodes,
                title=title,
                transport_profile=transport_profile,
            ),
        )

    if user_uses_free_pool(user):
        return (
            "singbox-json",
            _singbox_free_allowlist_config(
                user_uuid=str(user.uuid),
                nodes=nodes,
                title=title,
                transport_profile=transport_profile,
            ),
        )
    return (
        "singbox-json",
        _singbox_multi_node_config(
            user_uuid=str(user.uuid),
            nodes=nodes,
            title=title,
            transport_profile=transport_profile,
        ),
    )


def _generate_vless_link(*, user_uuid: str, node, name: str) -> str:
    import urllib.parse

    profile = _node_transport_profile(node, LEGACY_REALITY_FALLBACK)
    params = {
        "type": "tcp",
        "security": "reality",
        "pbk": profile.get("reality_public_key") or getattr(node, "reality_pbk", ""),
        "fp": profile.get("fingerprint") or getattr(node, "fingerprint", ""),
        "sni": profile.get("tls_server_name") or getattr(node, "reality_sni", ""),
        "sid": profile.get("reality_short_id") or getattr(node, "reality_sid", ""),
        "spx": "/",
        "flow": profile.get("flow") or getattr(node, "flow", ""),
    }
    query = "&".join([f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in params.items()])
    safe_name = urllib.parse.quote(name)
    host = str(profile.get("host") or getattr(node, "host", "") or "")
    port = int(profile.get("port") or getattr(node, "vless_port", 443) or 443)
    return f"vless://{user_uuid}@{host}:{port}?{query}#{safe_name}"


def _node_code_base(code: str) -> str:
    code = (code or "").lower().strip()
    for sep in ("_", "-", "."):
        if sep in code:
            code = code.split(sep, 1)[0]
    return code


def _node_label_ru(code: str, fallback_name: str = "") -> str:
    """
    Human-friendly labels for clients (Hiddify/sing-box).
    Tags/fragments are often shown directly in apps, so we prefer short Russian names + flags.
    """
    code_raw = (code or "").strip()
    if "free" in code_raw.lower():
        return "🇳🇱 NL Free"
    base = _node_code_base(code_raw)
    flags = {"pl": "🇵🇱", "it": "🇮🇹", "us": "🇺🇸", "nl": "🇳🇱", "brain": "🇩🇪", "de": "🇩🇪"}
    names = {
        "pl": "Польша",
        "it": "Италия",
        "us": "США",
        "nl": "Нидерланды",
        "brain": "Германия",
        "de": "Германия",
    }
    flag = flags.get(base, "🏳️")
    nm = names.get(base, fallback_name or (base.upper() if base else (code_raw or "Node")))
    variant = ""
    lowered = code_raw.lower()
    if base and lowered.startswith(base):
        suffix = code_raw[len(base) :].lstrip("._- ").strip()
        if suffix:
            parts = [part for part in re.split(r"[._-]+", suffix) if part]
            variant = " ".join(part.upper() if part.isdigit() else part.capitalize() for part in parts)
    return f"{flag} {nm} {variant}".strip()


def _singbox_remote_rule_sets() -> list[dict[str, Any]]:
    return [
        {
            "type": "remote",
            "tag": "geoip-ru",
            "format": "binary",
            "url": "https://raw.githubusercontent.com/SagerNet/sing-geoip/rule-set/geoip-ru.srs",
            "download_detour": "direct",
        },
        {
            "type": "remote",
            "tag": "geosite-category-ads-all",
            "format": "binary",
            "url": "https://raw.githubusercontent.com/SagerNet/sing-geosite/rule-set/geosite-category-ads-all.srs",
            "download_detour": "direct",
        },
    ]


def _steam_direct_domain_suffixes() -> list[str]:
    # Based on the official community Steam domain list plus the CDN hosts we
    # observed in production traffic. Keeping this local avoids a hard runtime
    # dependency on third-party list availability inside client configs.
    return [
        "a4e8s8k3.map2.ssl.hwcdn.net",
        "edge.steam-dns.top.comcast.net",
        "f3b7q2p3.ssl.hwcdn.net",
        "playartifact.com",
        "s.team",
        "steam-api.com",
        "steam-chat.com",
        "steam.apac.qtlglb.com",
        "steam.cdn.on.net",
        "steam.cdn.orcon.net.nz",
        "steam.cdn.slingshot.co.nz",
        "steam.cdn.webra.ru",
        "steam.eca.qtlglb.com",
        "steam.naeu.qtlglb.com",
        "steam.ru.qtlglb.com",
        "steam.tv",
        "steamcloudsweden.blob.core.windows.net",
        "steamcommunity-a.akamaihd.net",
        "steamcommunity-a.akamaihd.net.edgesuite.net",
        "steamcommunity.com",
        "steamcontent.com",
        "steamdeck.com",
        "steamgames.com",
        "steampipe-kr.akamaized.net",
        "steampipe-partner.akamaized.net",
        "steampipe.akamaized.net",
        "steampowered.com",
        "steamserver.net",
        "steamstatic.com",
        "steamstore-a.akamaihd.net",
        "steamusercontent-a.akamaihd.net",
        "steamusercontent.com",
        "steamuserimages-a.akamaihd.net",
        "steamvideo-a.akamaihd.net",
        "steambroadcast.akamaized.net",
        "steamcdn-a.akamaihd.net",
        "steammobile.akamaized.net",
        "underlords.com",
        "valvesoftware.com",
    ]


def _steam_direct_process_names() -> list[str]:
    return [
        "steam.exe",
        "steamservice.exe",
        "steamwebhelper.exe",
        "steam",
        "steamservice",
        "steamwebhelper",
    ]


def _singbox_common_route_rules(*, selector_tag: str, youtube_direct: bool = False) -> list[dict[str, Any]]:
    youtube_domain_suffix = [
        "youtube.com",
        "youtu.be",
        "ytimg.com",
        "googlevideo.com",
        "youtubei.googleapis.com",
        "yt3.ggpht.com",
    ]
    rules: list[dict[str, Any]] = [
        {"rule_set": ["geoip-ru"], "outbound": "direct"},
        {"process_name": _steam_direct_process_names(), "outbound": "direct"},
        {"domain_suffix": _steam_direct_domain_suffixes(), "outbound": "direct"},
        {"protocol": "bittorrent", "outbound": "direct"},
    ]
    if youtube_direct:
        rules.append({"domain_suffix": youtube_domain_suffix, "outbound": "direct"})
    rules.extend(
        [
            {"protocol": "dns", "outbound": "dns-out"},
            {"rule_set": ["geosite-category-ads-all"], "outbound": "block"},
            {"ip_is_private": True, "outbound": "direct"},
        ]
    )
    return rules


def _singbox_multi_node_config(
    *,
    user_uuid: str,
    nodes: list,
    title: str,
    transport_profile: str = LEGACY_REALITY_FALLBACK,
) -> dict:
    outbounds = []
    selector_opts = []
    selector_tag = "🌍 Страны"
    for n in nodes:
        tag = _node_label_ru(getattr(n, "code", ""), getattr(n, "name", ""))
        selector_opts.append(tag)
        outbounds.append(
            _node_outbound_from_transport_profile(
                user_uuid=user_uuid,
                node=n,
                tag=tag,
                transport_profile=transport_profile,
            )
        )

    selector_default = selector_opts[0] if selector_opts else "direct"
    outbounds.extend(
        [
            {
                "type": "selector",
                "tag": selector_tag,
                "outbounds": selector_opts,
                "default": selector_default,
            },
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"},
            {"type": "dns", "tag": "dns-out"},
        ]
    )

    return {
        "log": {"level": "warn", "timestamp": True},
        "dns": {
            "servers": [
                {"tag": "google", "address": "8.8.8.8", "detour": selector_tag},
                {"tag": "local", "address": "local", "detour": "direct"},
            ]
        },
        "inbounds": [],
        "outbounds": outbounds,
        "route": {
            "rule_set": _singbox_remote_rule_sets(),
            "rules": _singbox_common_route_rules(selector_tag=selector_tag),
            "auto_detect_interface": True,
            "final": selector_tag,
        },
        "experimental": {
            "cache_file": {"enabled": True},
        },
        "_meta": {"title": title},
    }


def _singbox_free_allowlist_config(
    *,
    user_uuid: str,
    nodes: list,
    title: str,
    transport_profile: str = LEGACY_REALITY_FALLBACK,
) -> dict:
    """
    Dedicated free-pool config.
    Split-routing defaults are the same as paid:
    - RU direct
    - torrents direct
    - Steam downloads direct
    - everything else via selected outbound
    Additionally for free tier:
    - YouTube direct
    """
    selector_tag = "🌍 Страны"

    outbounds = []
    for n in nodes:
        outbounds.append(
            _node_outbound_from_transport_profile(
                user_uuid=user_uuid,
                node=n,
                tag=_node_label_ru(n.code, n.name),
                transport_profile=transport_profile,
            )
        )

    selector_opts = [o["tag"] for o in outbounds]
    selector_default = selector_opts[0] if selector_opts else "direct"
    outbounds.append(
        {
            "type": "selector",
            "tag": selector_tag,
            "outbounds": selector_opts,
            "default": selector_default,
        }
    )
    outbounds.extend(
        [
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"},
            {"type": "dns", "tag": "dns-out"},
        ]
    )

    return {
        "log": {"level": "warn", "timestamp": True},
        "dns": {
            "servers": [
                {"tag": "google", "address": "8.8.8.8", "detour": selector_tag},
                {"tag": "local", "address": "local", "detour": "direct"},
            ]
        },
        "inbounds": [],
        "outbounds": outbounds,
        "route": {
            "rule_set": _singbox_remote_rule_sets(),
            "rules": _singbox_common_route_rules(selector_tag=selector_tag, youtube_direct=True),
            "auto_detect_interface": True,
            "final": selector_tag,
        },
        "experimental": {"cache_file": {"enabled": True}},
        "_meta": {"title": title},
    }


def _node_accepts_new_clients(node: Any) -> bool:
    return bool(getattr(node, "enabled", True)) and bool(getattr(node, "accepting_new_clients", True)) and not bool(
        getattr(node, "is_draining", False)
    )


def _subscription_excluded_codes() -> set[str]:
    return {
        token.strip().lower()
        for token in str(os.getenv("SUBSCRIPTION_EXCLUDE_NODE_CODES", "") or "").split(",")
        if token.strip()
    }


def _node_allowed_for_plan(
    user: User,
    node: Any,
    *,
    excluded_codes: set[str] | None = None,
    free_code: str | None = None,
) -> bool:
    code = str(getattr(node, "code", "") or "").strip().lower()
    if not code:
        return False
    base = _node_code_base(code)
    excluded = excluded_codes or set()
    if code in excluded or base in excluded:
        return False

    if user_uses_free_pool(user):
        return bool(free_code) and code == str(free_code).strip().lower()

    return not node_is_free(node)


def _mapped_nodes_for_user(session, user: User, nodes: list) -> list:
    node_by_id = {int(getattr(node, "id", 0) or 0): node for node in nodes if getattr(node, "id", None) is not None}
    rows = (
        session.query(UserNode)
        .filter(UserNode.tg_id == int(user.tg_id))
        .order_by(UserNode.created_at.asc(), UserNode.id.asc())
        .all()
    )
    out: list[Any] = []
    seen: set[str] = set()
    excluded_codes = _subscription_excluded_codes()
    free_code = str(canonical_free_node_code(nodes) or "").strip().lower()
    for row in rows:
        node = node_by_id.get(int(getattr(row, "node_id", 0) or 0))
        if not node:
            continue
        code = str(getattr(node, "code", "") or "").strip().lower()
        if not code or code in seen:
            continue
        if code in excluded_codes or _node_code_base(code) in excluded_codes:
            continue
        if user_uses_free_pool(user):
            if not free_code or code != free_code:
                continue
        elif not _node_allowed_for_plan(user, node, excluded_codes=excluded_codes, free_code=free_code):
            continue
        seen.add(code)
        out.append(node)
    return out


def _fallback_nodes_for_user(user: User, nodes: list) -> list:
    """
    Per-plan node visibility.
    - FREE: dedicated free pool only.
    - PAID: all enabled non-free nodes.
    """
    if not nodes:
        return nodes

    excluded_codes = _subscription_excluded_codes()

    def _apply_node_filters(pool: list) -> list:
        # 1) Drop explicitly excluded nodes/country-bases from subscription output.
        filtered = list(pool)
        if excluded_codes:
            filtered = []
            for node in pool:
                code = str(getattr(node, "code", "") or "").strip().lower()
                if not code:
                    continue
                base = _node_code_base(code)
                if code in excluded_codes or base in excluded_codes:
                    continue
                filtered.append(node)
            # Backward-compatible fallback: keep original pool if filter removes everything.
            if not filtered:
                filtered = list(pool)

        # 2) Prefer healthy nodes when health data is available; fallback to full pool.
        healthy = [node for node in filtered if bool(getattr(node, "is_healthy", True))]
        return healthy or filtered

    candidate_nodes = [node for node in nodes if _node_accepts_new_clients(node)]
    if not candidate_nodes:
        candidate_nodes = list(nodes)

    if not user_uses_free_pool(user):
        paid = [n for n in candidate_nodes if not node_is_free(n)]
        return _apply_node_filters(paid)

    free_code = str(canonical_free_node_code(candidate_nodes) or canonical_free_node_code(nodes) or "").strip().lower()
    free_nodes = [n for n in candidate_nodes if str(getattr(n, "code", "") or "").strip().lower() == free_code]
    return _apply_node_filters(free_nodes)


def _nodes_for_user(user: User, nodes: list, session=None) -> list:
    own_session = session is None
    s = session or SessionLocal()
    try:
        mapped = _mapped_nodes_for_user(s, user, nodes)
        if mapped:
            return mapped
        return _fallback_nodes_for_user(user, nodes)
    finally:
        if own_session:
            s.close()


def _serialize_admin_node(
    n: Node,
    *,
    mapped_users: int = 0,
    network_peak_mbps_24h: float | None = None,
    online_keys_now: int = 0,
    online_connections_now: int = 0,
) -> dict[str, Any]:
    stale_after_seconds = max(300, int(os.getenv("NODE_METRICS_STALE_AFTER_SECONDS", "900")))
    now = _utcnow()
    last_sample_at = getattr(n, "last_health_at", None) or getattr(n, "last_probe_at", None)
    alert_kinds = _node_snapshot_alert_kinds(
        node=n,
        last_sample_at=last_sample_at,
        stale_after_seconds=stale_after_seconds,
        now=now,
    )
    memory_used_mb, memory_total_mb = _nullable_node_memory_value(
        used_mb=getattr(n, "memory_used_mb", None),
        total_mb=getattr(n, "memory_total_mb", None),
    )
    disk_used_gb, disk_total_gb, disk_free_gb = _nullable_node_disk_value(
        used_gb=getattr(n, "disk_used_gb", None),
        total_gb=getattr(n, "disk_total_gb", None),
        free_gb=getattr(n, "disk_free_gb", None),
    )
    (
        network_rx_bytes_total,
        network_tx_bytes_total,
        network_rx_mbps,
        network_tx_mbps,
        network_total_mbps,
    ) = _nullable_node_network_value(
        rx_bytes_total=getattr(n, "network_rx_bytes_total", None),
        tx_bytes_total=getattr(n, "network_tx_bytes_total", None),
        rx_mbps=getattr(n, "network_rx_mbps", None),
        tx_mbps=getattr(n, "network_tx_mbps", None),
        total_mbps=getattr(n, "network_total_mbps", None),
    )
    network_port_capacity_mbps = float(NODE_METRICS_PORT_CAPACITY_MBPS or 0.0)
    network_utilization_percent = _network_utilization_percent(network_total_mbps)
    network_peak_utilization_percent_24h = _network_utilization_percent(network_peak_mbps_24h)
    transport_health: dict[str, Any] = {}
    raw_transport_health = str(getattr(n, "transport_health_json", "") or "").strip()
    if raw_transport_health:
        try:
            parsed_transport_health = json.loads(raw_transport_health)
        except Exception:
            parsed_transport_health = {}
        if isinstance(parsed_transport_health, dict):
            transport_health = {
                str(key): value
                for key, value in parsed_transport_health.items()
                if str(key or "").strip()
            }
    transport_profiles = _transport_profiles_payload(n)
    return {
        "code": n.code,
        "name": n.name,
        "enabled": bool(n.enabled),
        "accepting_new_clients": bool(getattr(n, "accepting_new_clients", True)),
        "is_draining": bool(getattr(n, "is_draining", False)),
        "mapped_users": int(mapped_users),
        "online_keys_now": int(online_keys_now),
        "online_connections_now": int(online_connections_now),
        "is_healthy": bool(getattr(n, "is_healthy", True)),
        "health_score": float(getattr(n, "health_score", 0.0) or 0.0),
        "panel_latency_ms": getattr(n, "panel_latency_ms", None),
        "panel_error_rate": float(getattr(n, "panel_error_rate", 0.0) or 0.0),
        "active_clients": int(getattr(n, "active_clients", 0) or 0),
        "cpu_percent": float(getattr(n, "cpu_percent", 0.0) or 0.0),
        "memory_used_mb": memory_used_mb,
        "memory_total_mb": memory_total_mb,
        "disk_used_gb": disk_used_gb,
        "disk_total_gb": disk_total_gb,
        "disk_free_gb": disk_free_gb,
        "network_rx_bytes_total": network_rx_bytes_total,
        "network_tx_bytes_total": network_tx_bytes_total,
        "network_rx_mbps": network_rx_mbps,
        "network_tx_mbps": network_tx_mbps,
        "network_total_mbps": network_total_mbps,
        "network_peak_mbps_24h": float(network_peak_mbps_24h) if network_peak_mbps_24h is not None else None,
        "network_port_capacity_mbps": network_port_capacity_mbps if network_port_capacity_mbps > 0 else None,
        "network_utilization_percent": network_utilization_percent if network_total_mbps is not None else None,
        "network_peak_utilization_percent_24h": (
            network_peak_utilization_percent_24h if network_peak_mbps_24h is not None else None
        ),
        "last_ok_at": _safe_iso(getattr(n, "last_ok_at", None)),
        "last_health_at": _safe_iso(getattr(n, "last_health_at", None)),
        "freshness_status": "stale" if "stale_metrics" in alert_kinds else "fresh",
        "freshness_age_seconds": int((now - last_sample_at).total_seconds()) if last_sample_at else None,
        "alerts": _legacy_node_alerts(alert_kinds),
        "alert_kinds": sorted(set(alert_kinds)),
        "last_probe_stage": str(getattr(n, "last_probe_stage", "") or "") or None,
        "last_probe_error_kind": str(getattr(n, "last_probe_error_kind", "") or "") or None,
        "last_probe_error_message": str(getattr(n, "last_probe_error_message", "") or "") or None,
        "hoster_family": str(getattr(n, "hoster_family", "") or "") or None,
        "hoster_asn": str(getattr(n, "hoster_asn", "") or "") or None,
        "subnet": str(getattr(n, "hoster_subnet", "") or "") or None,
        "ipv4_health": str(getattr(n, "ipv4_health", "") or "") or None,
        "ipv6_health": str(getattr(n, "ipv6_health", "") or "") or None,
        "probe_classification": str(getattr(n, "last_probe_classification", "") or "") or None,
        "transport_health": transport_health,
        "transport_profiles": transport_profiles,
        "observer_last_push_at": _safe_iso(getattr(n, "observer_last_push_at", None)),
        "observer_unmatched_count": int(getattr(n, "observer_unmatched_count", 0) or 0),
        "observer_parse_error_count": int(getattr(n, "observer_parse_error_count", 0) or 0),
        "observer_is_stale": bool(_observer_is_stale(n, now=now)),
        "weight": int(getattr(n, "weight", 0) or 0),
    }


def _target_node_codes_for_resync(session, user: User, source_code: str, nodes: list) -> list[str]:
    source_code = str(source_code or "").strip().lower()
    out: list[str] = []
    seen: set[str] = set()

    for node in _mapped_nodes_for_user(session, user, nodes):
        code = str(getattr(node, "code", "") or "").strip().lower()
        if not code or code == source_code or code in seen:
            continue
        seen.add(code)
        out.append(code)

    for node in _fallback_nodes_for_user(user, nodes):
        code = str(getattr(node, "code", "") or "").strip().lower()
        if not code or code == source_code or code in seen:
            continue
        seen.add(code)
        out.append(code)

    return out


def _token_fingerprint(token: str) -> str:
    text = str(token or "").strip()
    if not text:
        return "empty"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


async def _notify_admin_on_subscription_fallback(*, user_tg_id: int, token_fp: str) -> None:
    admin_id = int(Settings.ADMIN_ID or 0)
    if admin_id <= 0:
        return
    day_key = _utcnow().strftime("%Y%m%d")
    campaign_key = f"sub_token_fallback:{int(user_tg_id)}:{day_key}"

    s = SessionLocal()
    try:
        if not _mark_campaign_once(s, tg_id=admin_id, campaign_key=campaign_key):
            return
        s.commit()
    except Exception:
        s.rollback()
        return
    finally:
        s.close()

    try:
        track_event(
            tg_id=int(user_tg_id),
            event_name="subscription_numeric_fallback",
            source="subscription",
            meta={"token_fp": token_fp},
        )
    except Exception:
        logger.exception("failed to track subscription numeric fallback tg_id=%s", int(user_tg_id))

    text = (
        "⚠️ Обнаружен fallback подписки по `tg_id`.\n"
        f"user_id: `{int(user_tg_id)}`\n"
        f"token_fp: `{token_fp}`\n\n"
        "Рекомендуется регенерация sub_token и проверка синка subId в панели."
    )
    await _telegram_send_message(chat_id=admin_id, text=text)


@app.api_route("/s8Kx2mP7qR4wT/{token}", methods=["GET", "HEAD"])
async def subscription(token: str, request: Request, format: str = Query(default="", alias="format")):
    """
    Multi-node subscription endpoint.
    - token is usually `sub_token`
    - legacy fallback: if token is numeric, treat it as `tg_id`
    """
    token_text = str(token or "").strip()
    token_fp = _token_fingerprint(token_text)
    nodes_for_user: list[Any] = []
    rollout_config = normalized_network_rollout_config({})
    carrier = _request_carrier_header(request.headers.get("X-Portal-Carrier"))
    client_policy = resolved_client_policy(rollout_config=rollout_config, carrier=carrier)
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(sub_token=token_text).first()
        lookup_mode = "sub_token"
        if not user and token_text.isdigit():
            if SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED:
                user = s.query(User).filter_by(tg_id=int(token_text)).first()
                if user:
                    lookup_mode = "tg_id_fallback"
            else:
                logger.warning(
                    "subscription numeric fallback disabled token_fp=%s token_len=%s",
                    token_fp,
                    len(token_text),
                )
        if not user:
            logger.warning("subscription lookup failed token_fp=%s token_len=%s", token_fp, len(token_text))
            raise HTTPException(status_code=404, detail="User not found")

        _maybe_downgrade_expired_to_free(s, user)

        if not user.is_active:
            logger.info(
                "subscription inactive response token_fp=%s tg_id=%s lookup_mode=%s",
                token_fp,
                int(user.tg_id),
                lookup_mode,
            )
            return Response(content="", media_type="text/plain")

        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        rollout_config = load_network_rollout_config(session=s)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
            carrier=carrier,
            rollout_config=rollout_config,
        )
    finally:
        s.close()

    user_agent = request.headers.get("user-agent", "").lower()
    format_hint = str(format or "").strip().lower()
    request_host = str(request.url.hostname or request.headers.get("host") or "").split(":", 1)[0].strip().lower()
    connect_host = public_connect_host()
    is_connect_request = bool(request_host and request_host == connect_host)
    is_smart = any(x in user_agent for x in ["hiddify", "dart", "sing-box", "nekobox"])
    force_smart = format_hint in {"smart", "json", "singbox"}
    force_plain = format_hint in {"plain", "legacy", "vless"}
    wants_smart = force_smart or (not force_plain and (is_smart or is_connect_request))
    logger.info(
        "subscription resolved token_fp=%s tg_id=%s lookup_mode=%s smart=%s format_hint=%s host=%s connect_host=%s",
        token_fp,
        int(user.tg_id),
        lookup_mode,
        bool(wants_smart),
        format_hint or "-",
        request_host or "-",
        bool(is_connect_request),
    )
    if lookup_mode == "tg_id_fallback":
        logger.warning(
            "subscription fallback detected token_fp=%s tg_id=%s action=%s",
            token_fp,
            int(user.tg_id),
            "notify_admin_once_per_day",
        )
        await _notify_admin_on_subscription_fallback(user_tg_id=int(user.tg_id), token_fp=token_fp)

    header_expire = int(user.expiry_at.timestamp()) if user.expiry_at else 0
    total_bytes = _gb_to_bytes(_plan_total_gb(user))
    headers = {
        "Subscription-Userinfo": f"upload=0; download=0; total={total_bytes}; expire={header_expire}",
        "Profile-Update-Interval": str(int(PROFILE_UPDATE_INTERVAL_HOURS)),
        "Content-Disposition": 'attachment; filename="POKROV_Subscription"',
    }
    smart_transport_profile = str(client_policy.get("transport_profile") or LEGACY_REALITY_FALLBACK)
    smart_nodes_for_user = _effective_transport_nodes(
        nodes=nodes_for_user,
        rollout_config=rollout_config,
        transport_profile=smart_transport_profile,
    )

    # Explicit plain requests must stay on the legacy/manual path even for FREE accounts.
    if not force_plain and ((user.sub_type or "").upper() == "FREE" or wants_smart):
        if (user.sub_type or "").upper() == "FREE" and not smart_nodes_for_user:
            # Dedicated free pool is required for FREE users.
            return Response(content="", media_type="text/plain", status_code=503)

        cfg = (
            _singbox_free_allowlist_config(
                user_uuid=user.uuid,
                nodes=smart_nodes_for_user,
                title="POKROV Free",
                transport_profile=smart_transport_profile,
            )
            if (user.sub_type or "").upper() == "FREE"
            else _singbox_multi_node_config(
                user_uuid=user.uuid,
                nodes=smart_nodes_for_user,
                title="POKROV",
                transport_profile=smart_transport_profile,
            )
        )
        headers["Content-Disposition"] = 'attachment; filename="POKROV.json"'
        headers["Profile-Title"] = "POKROV"
        if request.method == "HEAD":
            return Response(content="", media_type="application/json", headers=headers)
        return Response(content=json.dumps(cfg, indent=2), media_type="application/json", headers=headers)

    links = []
    legacy_nodes_for_user = _effective_transport_nodes(
        nodes=nodes_for_user,
        rollout_config=rollout_config,
        transport_profile=LEGACY_REALITY_FALLBACK,
    )
    for n in legacy_nodes_for_user:
        links.append(_generate_vless_link(user_uuid=user.uuid, node=n, name=_node_label_ru(n.code, n.name)))
    raw = "\n".join(links)
    encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    if request.method == "HEAD":
        return Response(content="", media_type="text/plain", headers=headers)
    return Response(content=encoded, media_type="text/plain", headers=headers)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "2096")))





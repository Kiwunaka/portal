# -*- coding: utf-8 -*-
"""
Portal API for Telegram WebApp and Subscription endpoint.

- `/api/user/{tg_id}`: authenticated by Telegram WebApp initData
- `/api/reviews`: featured reviews for WebApp
- `/s8Kx2mP7qR4wT/{token}`: subscription endpoint (multi-node)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import re
import secrets
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse

import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import or_, func

# Load env from repo-local file first to avoid cwd-dependent startup behavior.
load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
load_dotenv()

from config import Settings, env_bool, env_int
from db import SessionLocal, init_db
from models import (
    AdminAudit,
    CampaignSend,
    ExternalOrder,
    ExternalPaymentEvent,
    FamilySlot,
    GiftCard,
    LiveUpdate,
    Node,
    NodeHealthSample,
    PlanCatalog,
    PromoCode,
    PromoUsage,
    Review,
    SupportTicket,
    Template,
    User,
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
from control_panel import ControlPanel
from events_service import track_event
from offers_service import accept_offer, create_offer, get_active_offer
from pay_attempts_service import start_attempt
from points_service import (
    EXPIRY_DAYS as POINTS_EXPIRY_DAYS,
    MONTHLY_CAP as POINTS_MONTHLY_CAP,
    award_points,
    available_points,
    preview_redeemable_points,
    referral_tier_snapshot,
)
from free_cycle_service import ensure_user_free_cycle_state, mark_user_became_free
from gift_cards_service import redeem_gift_card as redeem_gift_card_service
from web_auth_service import (
    SESSION_TTL_SECONDS,
    create_web_session_token,
    verify_telegram_login_payload,
    verify_web_session_token,
)


init_db()
logger = logging.getLogger(__name__)


API_ENABLE_USAGE = env_bool("API_ENABLE_USAGE", default=False)
AUTO_DOWNGRADE_TO_FREE = env_bool("AUTO_DOWNGRADE_TO_FREE", default=True)
AUTO_FREE_DAYS = int(os.getenv("AUTO_FREE_DAYS", "3650"))
FREE_TOTAL_GB = env_int("FREE_TOTAL_GB", 30)
FREE_LIMIT_IP = env_int("FREE_LIMIT_IP", 1)
PAID_LIMIT_IP = env_int("PAID_LIMIT_IP", 5)
FREE_SPEED_LIMIT_KBPS = env_int("FREE_SPEED_LIMIT_KBPS", 6250)
SUPPORT_USERNAME = (os.getenv("SUPPORT_USERNAME") or "portal_privacy_helpbot").lstrip("@")
SUPPORT_USERNAME = (os.getenv("SUPPORT_BOT_USERNAME") or SUPPORT_USERNAME).lstrip("@")
PUBLIC_CHANNEL = (os.getenv("PUBLIC_CHANNEL") or "portal_privacy").lstrip("@")
BOT_USERNAME = (os.getenv("BOT_USERNAME") or "portal_service_bot").lstrip("@")
REFERRAL_BONUS_DAYS = env_int("REFERRAL_BONUS_DAYS", 15)
CHANNEL_PREMIUM_DAYS = env_int("CHANNEL_PREMIUM_DAYS", 10)
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
PROFILE_UPDATE_INTERVAL_HOURS = max(1, env_int("PROFILE_UPDATE_INTERVAL_HOURS", 6))
PAYMENT_CALLBACK_TOLERANT_MODE = env_bool("PAYMENT_CALLBACK_TOLERANT_MODE", default=True)
TELEGRAM_WEB_LOGIN_MAX_AGE_SECONDS = max(60, env_int("TELEGRAM_WEB_LOGIN_MAX_AGE_SECONDS", 86400))
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
    "1_month": 249,
    "3_months": 699,
    "6_months": 1199,
    "9_months": 1399,
    "12_months": 1499,
}
RUB_PLAN_PRICES = {
    "start_99": {"amount_rub": 99, "days": 30},
    "1_month": {"amount_rub": 249, "days": 30},
    "3_months": {"amount_rub": 699, "days": 91},
    "6_months": {"amount_rub": 1199, "days": 182},
    "9_months": {"amount_rub": 1399, "days": 273},
    "12_months": {"amount_rub": 1499, "days": 365},
}
RUB_PLAN_LABELS = {
    "start_99": "Start 30 дней",
    "1_month": "Pro 1 месяц",
    "3_months": "Pro 3 месяца",
    "6_months": "Ultra 6 месяцев",
    "9_months": "Ultra 9 месяцев",
    "12_months": "Ultra 12 месяцев",
}
GIFT_CARD_TYPES = {
    "mini": {"days": 7, "stars": 59, "name": "Mini"},
    "standard": {"days": 30, "stars": 249, "name": "Standard"},
    "premium": {"days": 90, "stars": 699, "name": "Premium"},
}
PAYMENT_PROVIDER_WHITELIST = {"aaio", "cardlink", "freekassa"}
FK_NOTIFY_IP_ALLOWLIST = [
    x.strip()
    for x in (os.getenv("FK_NOTIFY_IP_ALLOWLIST") or "").split(",")
    if x.strip()
]


def _default_plan_catalog() -> list[dict[str, Any]]:
    return [
        {
            "code": code,
            "label": RUB_PLAN_LABELS.get(code, code),
            "amount_rub": int(RUB_PLAN_PRICES.get(code, {}).get("amount_rub") or 0),
            "amount_stars": int(API_PLAN_PRICES.get(code) or 0),
            "days": int(RUB_PLAN_PRICES.get(code, {}).get("days") or 30),
            "device_limit": 1 if code == "start_99" else max(1, int(PAID_LIMIT_IP)),
            "node_policy": "nl_only" if code == "start_99" else "paid_pool",
            "badge": "New" if code == "start_99" else "",
            "is_active": True,
            "sort_order": idx + 1,
        }
        for idx, code in enumerate(["start_99", "1_month", "3_months", "6_months", "9_months", "12_months"])
    ]


def _default_live_updates() -> list[dict[str, Any]]:
    channel = (PUBLIC_CHANNEL or "portal_privacy").lstrip("@")
    return [
        {
            "id": 0,
            "title": "Новые узлы NL/PL",
            "summary": "Добавлены свежие маршруты и обновлены рекомендации по клиентам.",
            "date": "2026-02-14",
            "link": f"https://t.me/{channel}/1",
        },
        {
            "id": 0,
            "title": "Промо-неделя для новых пользователей",
            "summary": "Стартовые предложения и бонусы для участников канала проекта.",
            "date": "2026-02-13",
            "link": f"https://t.me/{channel}/2",
        },
        {
            "id": 0,
            "title": "Гайд по быстрому подключению",
            "summary": "Обновили инструкции и deep links для популярных клиентов.",
            "date": "2026-02-12",
            "link": f"https://t.me/{channel}/3",
        },
    ]


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
    top = {
        "data": payload.get("data"),
        "iat": payload.get("iat"),
        "nonce": payload.get("nonce"),
        "shopId": payload.get("shopId"),
    }
    values = _fk_flatten_values(top)
    base = "|".join(values)
    return hmac.new(api_key.encode("utf-8"), base.encode("utf-8"), hashlib.sha256).hexdigest()


def _fk_sci_signature(*, merchant_id: str, amount: str, order_id: str, secret_word_2: str) -> str:
    base = f"{merchant_id}:{amount}:{secret_word_2}:{order_id}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()


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


class ReviewCreateIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: str = Field(min_length=1, max_length=500)


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


class EventIn(BaseModel):
    event_name: str = Field(min_length=2, max_length=64)
    source: str = Field(default="webapp", max_length=32)
    session_id: str | None = Field(default=None, max_length=64)
    meta: dict[str, Any] | None = None


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
    link: str = Field(min_length=8, max_length=600)
    published_at: str | None = None
    is_active: bool = True
    sort_order: int = Field(default=100, ge=0, le=10000)


class AdminLiveUpdateUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    summary: str | None = Field(default=None, min_length=2, max_length=600)
    link: str | None = Field(default=None, min_length=8, max_length=600)
    published_at: str | None = None
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0, le=10000)


class AdminCampaignLinksBuildIn(BaseModel):
    promo_code: str | None = Field(default=None, max_length=20)
    campaign_key: str | None = Field(default=None, max_length=64)
    plan_code: str | None = Field(default=None, max_length=32)
    source: str = Field(default="bot", max_length=16)



class DashboardResponse(BaseModel):
    tg_id: int
    sub_type: str
    current_plan_code: str | None = None
    is_active: bool
    expiry_at: str | None
    used_gb: float
    total_gb: float
    remaining_gb: float
    active_sessions: int
    device_limit: int
    speed_limit_mbps: int | None = None
    free_next_reset_at: str | None = None
    family_slots: int
    subscription_url: str
    segment: str
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
    days: int = Field(default=30, ge=1, le=3650)


class ManualUserBlockRequest(BaseModel):
    blocked: bool = True


def _plan_total_gb(user: User) -> int:
    st = (user.sub_type or "").upper()
    if st == "FREE":
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
        if user.expiry_at >= datetime.utcnow():
            return False
        if (user.sub_type or "").upper() == "FREE":
            # Already free but expired; extend so the free profile stays usable.
            user.expiry_at = datetime.utcnow() + timedelta(days=int(AUTO_FREE_DAYS))
            user.current_plan_code = "trial"
            ensure_user_free_cycle_state(user)
            s.commit()
            return True

        user.sub_type = "FREE"
        user.current_plan_code = "trial"
        user.expiry_at = datetime.utcnow() + timedelta(days=int(AUTO_FREE_DAYS))
        user.is_active = True
        mark_user_became_free(user)
        s.commit()
        return True
    except Exception:
        return False

app = FastAPI(title="Portal API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _verify_telegram_data(init_data: str) -> dict[str, Any] | None:
    """
    Verify Telegram WebApp initData.
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    """
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        check_hash = parsed.pop("hash", "")

        data_check_arr = sorted([f"{k}={v}" for k, v in parsed.items()])
        data_check_string = "\n".join(data_check_arr)

        secret_key = hmac.new(b"WebAppData", Settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if calculated_hash != check_hash:
            return None
        return json.loads(parsed.get("user", "{}"))
    except Exception:
        return None


def _safe_iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


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
    payload = {
        "tg_id": int(tg_id),
        "plan_code": (plan_code or "").strip().lower()[:32],
        "promo_code": (promo_code or "").strip().upper()[:20],
        "campaign_key": (campaign_key or "").strip()[:64],
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
        code = f"PORTAL-{token[:4]}-{token[4:]}"
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


def _dev_auth_user(request: Request | None) -> dict[str, Any] | None:
    if not WEBAPP_DEV_AUTH:
        return None
    if WEBAPP_DEV_TG_ID <= 0:
        return None
    if not _is_local_request(request):
        return None
    return {"id": int(WEBAPP_DEV_TG_ID), "username": "dev_user"}


def _extract_web_session_token(request: Request | None) -> str:
    if request is None:
        return ""
    auth_header = str(request.headers.get("authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return str(request.headers.get("x-web-auth-token") or "").strip()


def _ensure_user_row_for_login(*, tg_id: int, username: str | None = None) -> None:
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if user:
            if username and (not user.username):
                user.username = str(username).strip()[:100]
                s.commit()
            return

        now = datetime.utcnow()
        sub_token = secrets.token_urlsafe(32)
        row = User(
            tg_id=int(tg_id),
            username=(str(username).strip()[:100] if username else None),
            uuid=str(uuid.uuid4()),
            email=f"User_{int(tg_id)}",
            sub_type="FREE",
            current_plan_code="trial",
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
    n = now or datetime.utcnow()
    sub = (user.sub_type or "").upper().strip()
    if sub == "MANUAL":
        return "MANUAL"
    if not user.is_active or not user.expiry_at or user.expiry_at <= n:
        return "EXPIRED"
    if sub == "FREE":
        return "FREE"
    return "PAID"


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
    now = datetime.utcnow()
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
    exists = (
        s.query(CampaignSend.id)
        .filter(CampaignSend.tg_id == int(tg_id))
        .filter(CampaignSend.campaign_key == str(campaign_key))
        .first()
    )
    if exists:
        return False
    s.add(CampaignSend(tg_id=int(tg_id), campaign_key=str(campaign_key), sent_at=datetime.utcnow()))
    return True


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
    init_data = (x_telegram_init_data or "").strip()
    if init_data:
        user_data = _verify_telegram_data(init_data)
        if user_data:
            return user_data

    web_token = _extract_web_session_token(request)
    if web_token:
        payload = verify_web_session_token(web_token)
        if payload:
            return {"id": int(payload.get("id") or 0), "username": payload.get("username")}

    dev = _dev_auth_user(request)
    if dev:
        return dev

    if init_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram signature")
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
    host = str(getattr(Settings, "PUBLIC_WEB_DOMAIN", "") or "").strip().strip("/")
    if host:
        return f"https://{host}/webapp/"
    return _safe_public_url(getattr(Settings, "WEBAPP_URL", "")) or "/webapp/"


def _public_checkout_url() -> str:
    configured = _safe_public_url(getattr(Settings, "PAY_CHECKOUT_URL", ""))
    if configured:
        try:
            parsed = urlparse(configured)
            cfg_host = (parsed.hostname or "").lower().strip()
            if cfg_host and not cfg_host.endswith("kiwunaka.space"):
                return configured
        except Exception:
            return configured

    host = str(getattr(Settings, "PUBLIC_WEB_DOMAIN", "") or "").strip().strip("/")
    if host:
        return f"https://{host}/checkout"
    return configured


def _checkout_url_for_user(*, tg_id: int, plan_code: str = "", promo_code: str = "", campaign_key: str = "", source: str = "bot") -> str:
    base = _public_checkout_url() or f"https://{(Settings.PUBLIC_WEB_DOMAIN or 'portal-privacy.online').strip().strip('/')}/checkout"
    parsed = urlparse(base)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    q["source"] = (source or "bot").strip().lower()
    q["tg_id"] = str(int(tg_id))
    if plan_code:
        q["plan"] = str(plan_code).strip().lower()[:32]
    if promo_code:
        q["promo"] = str(promo_code).strip().upper()[:20]
    if campaign_key:
        q["campaign"] = str(campaign_key).strip()[:64]
    if _checkout_secret():
        ticket = _create_checkout_ticket(
            tg_id=int(tg_id),
            plan_code=str(plan_code or ""),
            promo_code=str(promo_code or ""),
            campaign_key=str(campaign_key or ""),
            source=q["source"],
        )
        if ticket:
            q["checkout_ticket"] = ticket
    built_query = urlencode(q)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/checkout'}?{built_query}"
    return f"/checkout?{built_query}"


def _normalize_provider(provider: str) -> str:
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


def _callback_ids(payload: dict[str, Any], raw: bytes) -> tuple[str, str]:
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
        row = ExternalOrder(provider=provider, order_id=order_id, created_at=datetime.utcnow())
        s.add(row)
    row.tg_id = _safe_int(_payload_value(payload, "tg_id", "telegram_id", "user_id"))
    row.plan_code = _payload_value(payload, "plan_code", "tariff", "plan")
    row.source = _payload_value(payload, "source", "checkout_source")
    row.campaign = _payload_value(payload, "campaign", "utm_campaign")
    row.promo_code = _payload_value(payload, "promo_code", "coupon")
    row.meta_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))[:4000]
    row.amount = _safe_float(_payload_value(payload, "amount", "sum", "amount_paid"))
    row.currency = _payload_value(payload, "currency", "cur", "ccy") or "RUB"
    row.status = status
    if mark_paid and not row.paid_at:
        row.paid_at = datetime.utcnow()


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
            s.query(ExternalPaymentEvent.id)
            .filter(
                ExternalPaymentEvent.provider == provider,
                ExternalPaymentEvent.event_type == event_type,
                ExternalPaymentEvent.external_id == external_id,
            )
            .first()
        )
        if exists:
            return True, True

        event = ExternalPaymentEvent(
            provider=provider,
            event_type=event_type,
            external_id=external_id,
            order_id=order_id or None,
            payload_json=json.dumps(payload, ensure_ascii=False, separators=(",", ":"))[:16000],
            signature_ok=bool(signature_ok),
            processed_ok=bool(processed_ok),
            created_at=datetime.utcnow(),
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


def _apply_external_paid_order(*, order_id: str, payload: dict[str, Any]) -> tuple[bool, str]:
    s = SessionLocal()
    try:
        ext_order = None
        if order_id:
            ext_order = (
                s.query(ExternalOrder)
                .filter(ExternalOrder.provider == "freekassa", ExternalOrder.order_id == str(order_id))
                .first()
            )
        tg_id = _safe_int(_payload_value(payload, "tg_id", "telegram_id", "user_id"))
        if tg_id is None and ext_order and ext_order.tg_id is not None:
            tg_id = int(ext_order.tg_id)
        if tg_id is None:
            return False, "missing_tg_id"

        plan_code = _payload_value(payload, "plan_code", "tariff", "plan")
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

        now = datetime.utcnow()
        old_sub = (user.sub_type or "").upper().strip()
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
        if ext_order:
            ext_order.status = "paid"
            ext_order.paid_at = ext_order.paid_at or now
            ext_order.tg_id = ext_order.tg_id or int(tg_id)
            ext_order.plan_code = plan_code
        s.commit()
        s.refresh(user)
    except Exception as exc:
        s.rollback()
        logger.exception("external order activation failed: order_id=%s err=%s", order_id, exc)
        return False, "db_error"
    finally:
        s.close()

    return True, "ok"


async def _handle_payment_callback(*, provider: str, event_type: str, request: Request) -> dict[str, Any]:
    p = _normalize_provider(provider)
    et = _normalize_provider(event_type)
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
    order_id, external_id = _callback_ids(payload, raw)
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
        activated, activation_reason = _apply_external_paid_order(order_id=order_id, payload=payload)
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
        return f"https://pay.freekassa.ru/?m={shop_id}&oa=0&o={fallback_order_id}"
    return ""


async def _freekassa_api_request(*, source: str, method: str, data: dict[str, Any]) -> dict[str, Any]:
    shop = _fk_shop_by_source(source)
    shop_id = str(shop.get("shop_id") or "").strip()
    api_key = str(shop.get("api_key") or "").strip()
    if not shop_id or not api_key:
        raise HTTPException(status_code=500, detail="Freekassa shop is not configured")

    nonce = int(time.time() * 1000)
    payload = {
        "shopId": shop_id,
        "nonce": nonce,
        "iat": int(time.time()),
        "data": data,
    }
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
                raise HTTPException(status_code=502, detail=f"Freekassa API error: {resp.status}")
            return body if isinstance(body, dict) else {"data": body}


async def _telegram_send_message(chat_id: int, text: str) -> bool:
    token = (Settings.BOT_TOKEN or "").strip()
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
    token = (Settings.BOT_TOKEN or "").strip()
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


_diag_rate_limit: dict[int, float] = {}
EVENT_WHITELIST = {
    "opened_webapp",
    "copied_key",
    "clicked_connect",
    "clicked_pay",
    "paid",
    "connected_ok",
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


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}


@app.get("/api/public/plans")
async def public_plans(response: Response) -> dict:
    s = SessionLocal()
    try:
        plans = _plan_catalog_payload(s=s, only_active=True)
        response.headers["Cache-Control"] = "public, max-age=120"
        return {"plans": plans, "widget_enabled": bool(CHECKOUT_WIDGET_ENABLED)}
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
            out.append(
                {
                    "id": int(row.id),
                    "title": str(row.title or "").strip(),
                    "summary": str(row.summary or "").strip(),
                    "date": (row.published_at or row.created_at or datetime.utcnow()).date().isoformat(),
                    "link": str(row.link or "").strip(),
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
        bot_token=Settings.BOT_TOKEN,
        max_age_seconds=TELEGRAM_WEB_LOGIN_MAX_AGE_SECONDS,
    )
    if not verified:
        raise HTTPException(status_code=401, detail="Invalid Telegram login payload")

    tg_id = int(verified.get("id") or 0)
    if tg_id <= 0:
        raise HTTPException(status_code=401, detail="Invalid Telegram user")
    username = (verified.get("username") or "").strip() or None
    _ensure_user_row_for_login(tg_id=tg_id, username=username)
    token = create_web_session_token(tg_id=tg_id, username=username)
    if not token:
        raise HTTPException(status_code=500, detail="Web session is not configured")
    return {
        "ok": True,
        "token": token,
        "user": {"id": tg_id, "username": username},
        "expires_in": int(SESSION_TTL_SECONDS),
    }


@app.get("/api/auth/session")
async def auth_session(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    return {
        "ok": True,
        "user": {
            "id": int(auth_user.get("id", 0)),
            "username": auth_user.get("username"),
        },
    }


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
            message="Платеж не прошел. Можно повторить попытку или обратиться в поддержку через Telegram.",
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


async def _freekassa_create_order_internal(
    *,
    request: Request,
    tg_id: int,
    source: str,
    plan_code: str,
    campaign: str = "",
    promo_code: str = "",
    currency: str = "RUB",
    consume_pending_discount: bool = True,
) -> FreekassaOrderActionOut:
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
        if pending_pct > 0:
            final_amount, discount_pct = _price_with_pending_discount(amount_rub=base_amount, pending_pct=pending_pct)
            discount_applied = discount_pct > 0 and final_amount < base_amount
            if not effective_promo and pending_code:
                effective_promo = pending_code[:32]
        amount_rub = float(final_amount)
        order_id = f"fk_{source}_{tg_id}_{int(time.time())}_{secrets.token_hex(4)}"
        ext = ExternalOrder(
            order_id=order_id,
            tg_id=int(tg_id),
            provider="freekassa",
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
                    "pricing": {
                        "base_amount_rub": int(base_amount),
                        "final_amount_rub": int(final_amount),
                        "discount_pct": int(discount_pct),
                        "discount_applied": bool(discount_applied),
                        "pending_discount_code": pending_code or None,
                    },
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )[:4000],
            created_at=datetime.utcnow(),
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

    notify_url = f"{Settings.PUBLIC_API_BASE_URL.rstrip('/')}/api/payments/freekassa/notify"
    req_data = {
        "orderId": order_id,
        "amount": amount_rub,
        "currency": "RUB",
        "email": "",
        "ip": _fk_client_ip(request),
        "urlSuccess": _safe_public_url(Settings.PAY_SUCCESS_URL) or f"{Settings.PUBLIC_API_BASE_URL.rstrip('/')}/pay/success",
        "urlFailure": _safe_public_url(Settings.PAY_FAIL_URL) or f"{Settings.PUBLIC_API_BASE_URL.rstrip('/')}/pay/fail",
        "urlNotification": notify_url,
        "metadata": {
            "tg_id": int(tg_id),
            "plan_code": str(plan.get("code") or plan_code).strip().lower(),
            "campaign": campaign or "",
            "promo_code": effective_promo or "",
            "source": source,
            "discount_pct": int(discount_pct),
            "base_amount_rub": int(base_amount),
            "final_amount_rub": int(final_amount),
        },
    }
    remote = await _freekassa_api_request(source=source, method="orders/create", data=req_data)
    payment_url = _parse_freekassa_payment_url(remote, order_id)

    s = SessionLocal()
    try:
        row = s.query(ExternalOrder).filter(ExternalOrder.provider == "freekassa", ExternalOrder.order_id == order_id).first()
        if row:
            row.status = "pending"
            row.meta_json = json.dumps(
                {
                    "request": req_data,
                    "response": remote,
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

    return FreekassaOrderActionOut(
        ok=True,
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


@app.post("/api/payments/freekassa/orders/create", response_model=FreekassaOrderActionOut)
async def freekassa_order_create(
    payload: FreekassaOrderCreateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> FreekassaOrderActionOut:
    if not RUB_CHECKOUT_ENABLED:
        raise HTTPException(status_code=403, detail="RUB checkout is disabled")
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    actor_tg_id = int(auth_user.get("id", 0))
    source = (payload.source or "site").strip().lower()
    if source not in {"site", "bot"}:
        source = "site"

    tg_id = int(payload.tg_id or actor_tg_id)
    if tg_id != actor_tg_id and not _is_admin_tg(actor_tg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    return await _freekassa_create_order_internal(
        request=request,
        tg_id=int(tg_id),
        source=source,
        plan_code=(payload.plan_code or "").strip().lower(),
        campaign=(payload.campaign or "").strip(),
        promo_code=(payload.promo_code or "").strip().upper(),
        currency=(payload.currency or "RUB").strip().upper(),
        consume_pending_discount=True,
    )


@app.post("/api/payments/freekassa/orders/create-public", response_model=FreekassaOrderActionOut)
async def freekassa_order_create_public(
    payload: FreekassaPublicOrderCreateIn,
    request: Request,
) -> FreekassaOrderActionOut:
    if not RUB_CHECKOUT_ENABLED:
        raise HTTPException(status_code=403, detail="RUB checkout is disabled")
    ticket_payload = _parse_checkout_ticket(payload.checkout_ticket)
    if not ticket_payload:
        raise HTTPException(status_code=401, detail="Invalid or expired checkout ticket")
    tg_id = int(ticket_payload.get("tg_id") or 0)
    if tg_id <= 0:
        raise HTTPException(status_code=400, detail="Checkout ticket has no user binding")
    source = str(ticket_payload.get("source") or "bot").strip().lower()
    if source not in {"site", "bot"}:
        source = "bot"
    plan_code = (payload.plan_code or ticket_payload.get("plan_code") or "").strip().lower()
    campaign = str(ticket_payload.get("campaign_key") or "").strip()[:64]
    promo_code = str(ticket_payload.get("promo_code") or "").strip().upper()[:20]
    return await _freekassa_create_order_internal(
        request=request,
        tg_id=tg_id,
        source=source,
        plan_code=plan_code,
        campaign=campaign,
        promo_code=promo_code,
        currency=(payload.currency or "RUB").strip().upper(),
        consume_pending_discount=True,
    )


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


@app.get("/api/admin/metrics/status")
async def admin_metrics_status(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data, request=request)
    stale_after_seconds = max(300, int(os.getenv("NODE_METRICS_STALE_AFTER_SECONDS", "900")))
    now = datetime.utcnow()
    s = SessionLocal()
    try:
        last_sample = s.query(func.max(NodeHealthSample.sampled_at)).scalar()
        if not last_sample:
            # Fallback for environments where sample table may be temporarily empty
            # but per-node health timestamps are present.
            last_sample = s.query(func.max(Node.last_health_at)).scalar()
        age_seconds = int((now - last_sample).total_seconds()) if last_sample else None
        return {
            "status": "fresh" if (age_seconds is not None and age_seconds <= stale_after_seconds) else "stale",
            "last_sample_at": _safe_iso(last_sample),
            "age_seconds": age_seconds,
            "stale_after_seconds": stale_after_seconds,
        }
    finally:
        s.close()


@app.get("/api/reviews")
async def featured_reviews() -> dict:
    s = SessionLocal()
    try:
        rows = s.query(Review).filter_by(is_featured=True).order_by(Review.created_at.desc()).limit(10).all()
        return {
            "reviews": [
                {
                    "username": _normalize_mojibake(r.username or "user"),
                    "rating": r.rating,
                    "text": _normalize_mojibake(r.text or ""),
                    "date": r.created_at.strftime("%d.%m.%Y") if r.created_at else "",
                }
                for r in rows
            ]
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
            "updated_at": datetime.utcnow().isoformat(),
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
async def user_data(tg_id: int, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
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
        _ensure_free_cycle_state_persisted(s, user)

        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes)
        subscription_url = ""
        if user.sub_token:
            subscription_url = f"{Settings.PUBLIC_API_BASE_URL.rstrip('/')}/s8Kx2mP7qR4wT/{user.sub_token}"

        # active check (DB-first)
        is_active = bool(user.is_active)
        if user.expiry_at and user.expiry_at < datetime.utcnow():
            is_active = False

        # optional legacy usage
        usage = await _get_panel_usage_legacy(tg_id)
        if usage and not usage.get("enable", True):
            is_active = False

        segment = _plan_segment(user)
        family_slots = _family_slots_for_user(s, tg_id)
        points_available, points_expiring_soon = available_points(tg_id=tg_id)
        total_gb = _plan_total_gb(user)
        used_gb = round((usage["used_bytes"] / (1024**3)), 3) if usage else 0
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

        return {
            "tg_id": tg_id,
            "username": user.username or auth_user.get("username"),
            "subscription_url": subscription_url,
            "is_active": is_active,
            "is_admin": role_admin,
            "sub_type": user.sub_type,
            "current_plan_code": str(getattr(user, "current_plan_code", "") or ""),
            "segment": segment,
            "expiry_at": user.expiry_at.isoformat() if user.expiry_at else None,
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
            "traffic": {
                "used_gb": used_gb,
                "total_gb": total_gb,
                "remaining_gb": remaining_gb,
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
async def dashboard_snapshot(request: Request, x_telegram_init_data: str = Header(default="")) -> DashboardResponse:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        _maybe_downgrade_expired_to_free(s, user)
        _ensure_free_cycle_state_persisted(s, user)
        usage = await _get_panel_usage_legacy(tg_id)
        total_gb = float(_plan_total_gb(user))
        used_gb = round((usage["used_bytes"] / (1024**3)), 3) if usage else 0.0
        remaining = max(round(total_gb - used_gb, 3), 0.0) if total_gb > 0 else 0.0
        expiry = user.expiry_at
        active = bool(user.is_active and expiry and expiry > datetime.utcnow())
        segment = _plan_segment(user)
        family_slots = _family_slots_for_user(s, tg_id)
        points_available, points_expiring_soon = available_points(tg_id=tg_id)
        sub_url = ""
        if user.sub_token:
            sub_url = f"{Settings.PUBLIC_API_BASE_URL.rstrip('/')}/s8Kx2mP7qR4wT/{user.sub_token}"

        return DashboardResponse(
            tg_id=tg_id,
            sub_type=str(user.sub_type or ""),
            current_plan_code=str(getattr(user, "current_plan_code", "") or ""),
            is_active=active,
            expiry_at=_safe_iso(expiry),
            used_gb=float(used_gb),
            total_gb=float(total_gb),
            remaining_gb=float(remaining),
            active_sessions=int(getattr(user, "active_sessions", 0) or 0),
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
        updated_at=f"{datetime.utcnow().replace(microsecond=0).isoformat()}Z",
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
        rows = _nodes_for_user(user, enabled_nodes(s))
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
        nodes = _nodes_for_user(user, enabled_nodes(s))
        healthy = [n for n in nodes if bool(getattr(n, "is_healthy", True))]
    finally:
        s.close()

    ok = bool(healthy) if nodes else False
    return NodeDiagnosticsResponse(
        ok=ok,
        checked_at=datetime.utcnow().isoformat(),
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

    is_member, reason = await _is_channel_member(PUBLIC_CHANNEL, tg_id)
    if not is_member:
        return {
            "ok": True,
            "subscriber": False,
            "reason": reason,
            "points_granted": 0,
            "campaign_marked": False,
        }

    points_granted = 0
    campaign_marked = False
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        campaign_marked = _mark_campaign_once(
            s,
            tg_id=tg_id,
            campaign_key=CHANNEL_SUBSCRIBER_CAMPAIGN_KEY,
        )
        if campaign_marked:
            points_granted = int(
                award_points(
                    tg_id=tg_id,
                    amount=100,
                    reason="channel_subscribe_bonus",
                    expires_days=POINTS_EXPIRY_DAYS,
                )
            )
        s.commit()
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()

    return {
        "ok": True,
        "subscriber": True,
        "reason": "member",
        "points_granted": int(points_granted),
        "campaign_marked": bool(campaign_marked),
    }


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
        if not bool(getattr(user, "tos_accepted", False)):
            raise HTTPException(status_code=400, detail="Сначала примите оферту в боте (/start)")
        if (user.sub_type or "").upper() == "MANUAL":
            raise HTTPException(status_code=400, detail="Bonus is disabled for manual accounts")
        if _has_campaign_mark(s, tg_id=tg_id, campaign_key=OPENING_PREMIUM_CAMPAIGN_KEY):
            raise HTTPException(
                status_code=400,
                detail="Для этого аккаунта уже активирован промо-бонус по ссылке. Бонус за канал недоступен.",
            )
        if getattr(user, "channel_bonus_claimed_at", None):
            return {
                "ok": True,
                "already_claimed": True,
                "premium_days": int(CHANNEL_PREMIUM_DAYS),
                "claimed_at": _safe_iso(user.channel_bonus_claimed_at),
                "expiry_at": _safe_iso(user.expiry_at),
                "sub_type": user.sub_type,
                "channel": PUBLIC_CHANNEL,
            }
        if (user.sub_type or "").upper() != "FREE":
            raise HTTPException(status_code=400, detail="Бонус доступен только в стартовом режиме")

        is_member, reason = await _is_channel_member(PUBLIC_CHANNEL, tg_id)
        if not is_member:
            if reason == "not_member":
                raise HTTPException(status_code=400, detail="Сначала подпишитесь на канал и повторите проверку")
            raise HTTPException(status_code=502, detail=f"Не удалось проверить подписку: {reason}")

        now = datetime.utcnow()
        days = max(1, int(CHANNEL_PREMIUM_DAYS))
        old_sub = (user.sub_type or "").upper()

        if old_sub == "FREE":
            # FREE has long synthetic expiry; premium bonus should start from now.
            user.expiry_at = now + timedelta(days=days)
        else:
            cur = user.expiry_at if user.expiry_at and user.expiry_at > now else now
            user.expiry_at = cur + timedelta(days=days)

        user.sub_type = "PAID"
        user.current_plan_code = "channel_bonus"
        user.is_active = True
        user.channel_bonus_claimed_at = now
        user.channel_bonus_active = True
        user.channel_bonus_expires_at = user.expiry_at
        user.channel_bonus_revoked_at = None
        first_channel_mark = _mark_campaign_once(
            s,
            tg_id=tg_id,
            campaign_key=CHANNEL_SUBSCRIBER_CAMPAIGN_KEY,
        )
        points_granted = 0
        if first_channel_mark:
            points_granted = award_points(
                tg_id=tg_id,
                amount=100,
                reason="channel_subscribe_bonus",
                expires_days=POINTS_EXPIRY_DAYS,
            )
        s.commit()
        s.refresh(user)
        sync_ok = await _sync_user_after_paid_bonus(user)

        return {
            "ok": True,
            "already_claimed": False,
            "premium_days": days,
            "claimed_at": _safe_iso(user.channel_bonus_claimed_at),
            "expiry_at": _safe_iso(user.expiry_at),
            "sub_type": user.sub_type,
            "channel": PUBLIC_CHANNEL,
            "sync_ok": bool(sync_ok),
            "points_granted": int(points_granted),
        }
    finally:
        s.close()


@app.post("/api/promo/redeem")
async def promo_redeem(payload: PromoRedeemIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    code = (payload.code or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Promo code is required")

    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not bool(getattr(user, "tos_accepted", False)):
            raise HTTPException(status_code=400, detail="Сначала примите оферту в боте (/start)")
        promo = s.query(PromoCode).filter(func.upper(PromoCode.code) == code).first()
        if not promo:
            raise HTTPException(status_code=404, detail="Promo not found")
        if int(promo.uses_left or 0) <= 0:
            raise HTTPException(status_code=400, detail="Promo exhausted")
        if promo.expires_at and promo.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Promo expired")
        used = s.query(PromoUsage).filter_by(tg_id=tg_id, promo_code=promo.code).first()
        if used:
            raise HTTPException(status_code=400, detail="Promo already redeemed")

        promo_type = (promo.promo_type or "").strip().lower()
        value = int(promo.value or 0)
        applied_days = 0
        pending_discount_pct = 0
        if promo_type == "days" and value > 0:
            now = datetime.utcnow()
            if user.expiry_at and user.expiry_at > now:
                user.expiry_at = user.expiry_at + timedelta(days=value)
            else:
                user.expiry_at = now + timedelta(days=value)
            user.is_active = True
            applied_days = value
        elif promo_type == "discount" and value > 0:
            user.pending_discount_pct = max(1, min(95, int(value)))
            user.pending_discount_code = str(promo.code or "").strip().upper()[:20]
            user.pending_discount_set_at = datetime.utcnow()
            pending_discount_pct = int(user.pending_discount_pct or 0)

        promo.uses_left = max(0, int(promo.uses_left or 0) - 1)
        s.add(PromoUsage(tg_id=tg_id, promo_code=promo.code))
        s.commit()
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
    result = await redeem_gift_card_service(code=payload.code, recipient_tg_id=tg_id, require_tos=False)
    if result.get("ok"):
        track_event(
            tg_id=tg_id,
            event_name="gift_redeemed",
            source="webapp",
            meta={"card_type": result.get("card_type"), "days": result.get("days"), "sync_ok": result.get("sync_ok")},
        )
        return result

    error = str(result.get("error") or "redeem_failed")
    message = str(result.get("message") or "Не удалось активировать код")
    status_map = {
        "invalid_code": 400,
        "not_found": 404,
        "already_redeemed": 400,
        "self_redeem": 400,
        "tos_required": 400,
    }
    raise HTTPException(status_code=status_map.get(error, 400), detail=message)


@app.post("/api/reviews")
async def create_review(payload: ReviewCreateIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        db_user = s.query(User).filter_by(tg_id=tg_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        row = Review(
            tg_id=tg_id,
            username=db_user.username or auth_user.get("username"),
            rating=int(payload.rating),
            text=(payload.text or "").strip()[:500],
            is_featured=False,
        )
        s.add(row)
        s.commit()
        return {"ok": True, "review_id": row.id}
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
        await _telegram_send_message(int(Settings.ADMIN_ID), f"🆕 Новый тикет #{ticket.id} от пользователя {tg_id}.")
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
        await _telegram_send_message(int(ticket.user_tg_id), f"💬 Новый ответ оператора в тикете #{ticket.id}.")
    elif Settings.ADMIN_ID:
        await _telegram_send_message(int(Settings.ADMIN_ID), f"🆕 Новое сообщение в тикете #{ticket.id} от {actor}.")
    return {"ticket": _ticket_row(ticket, msgs)}


@app.get("/api/admin/summary")
async def admin_summary(x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        total_users = s.query(func.count(User.tg_id)).scalar() or 0
        active_users = s.query(func.count(User.tg_id)).filter(User.is_active == True).scalar() or 0
        free_users = s.query(func.count(User.tg_id)).filter(func.upper(User.sub_type) == "FREE").scalar() or 0
        paid_users = s.query(func.count(User.tg_id)).filter(func.upper(User.sub_type) == "PAID").scalar() or 0
        open_tickets = s.query(func.count(SupportTicket.id)).filter(SupportTicket.status != STATUS_CLOSED).scalar() or 0
        total_nodes = s.query(func.count(Node.id)).filter(Node.enabled == True).scalar() or 0
        healthy_nodes = s.query(func.count(Node.id)).filter(Node.enabled == True, Node.is_healthy == True).scalar() or 0
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
            },
            "tickets": {"open": int(open_tickets)},
            "nodes": {"total": int(total_nodes), "healthy": int(healthy_nodes)},
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
    limit: int = 50,
    offset: int = 0,
) -> dict:
    _require_admin(x_telegram_init_data)
    q_norm = (q or "").strip()
    s = SessionLocal()
    try:
        query = s.query(User)
        if q_norm:
            filters = [User.username.ilike(f"%{q_norm}%")]
            if q_norm.isdigit():
                filters.append(User.tg_id == int(q_norm))
            query = query.filter(or_(*filters))
        rows = (
            query.order_by(User.created_at.desc(), User.tg_id.desc())
            .offset(max(0, int(offset)))
            .limit(max(1, min(int(limit), 200)))
            .all()
        )
        return {
            "users": [
                {
                    "tg_id": int(u.tg_id),
                    "username": u.username,
                    "display_name": getattr(u, "display_name", None),
                    "sub_type": u.sub_type,
                    "is_active": bool(u.is_active),
                    "is_manual": bool(getattr(u, "is_manual", False) or int(u.tg_id) < 0 or (u.sub_type or "").upper() == "MANUAL"),
                    "expiry_at": _safe_iso(u.expiry_at),
                    "stars_paid": int(u.stars_paid or 0),
                    "created_at": _safe_iso(u.created_at),
                }
                for u in rows
            ]
        }
    finally:
        s.close()


@app.get("/api/admin/users/{tg_id}")
async def admin_user_card(tg_id: int, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        tickets = list_user_tickets(s, tg_id, limit=20)
        return {
            "user": {
                "tg_id": int(user.tg_id),
                "username": user.username,
                "display_name": getattr(user, "display_name", None),
                "sub_type": user.sub_type,
                "is_active": bool(user.is_active),
                "is_manual": bool(getattr(user, "is_manual", False) or int(user.tg_id) < 0 or (user.sub_type or "").upper() == "MANUAL"),
                "expiry_at": _safe_iso(user.expiry_at),
                "stars_paid": int(user.stars_paid or 0),
                "total_gb": int(user.total_gb or 0),
                "trial_used": bool(user.trial_used),
                "referral_count": int(user.referral_count or 0),
                "streak_months": int(user.streak_months or 0),
                "created_at": _safe_iso(user.created_at),
            },
            "tickets": [_ticket_row(t, list_ticket_messages(s, t.id, limit=1)) for t in tickets],
        }
    finally:
        s.close()


@app.post("/api/admin/users/manual")
async def admin_create_manual_user(payload: ManualUserCreateRequest, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        tg_id = _next_manual_tg_id(s)
        now = datetime.utcnow()
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
    return {
        "ok": True,
        "user": {
            "tg_id": int(created["tg_id"]),
            "display_name": created["display_name"],
            "sub_type": created["sub_type"],
            "is_active": bool(created["is_active"]),
            "expiry_at": created["expiry_at"],
            "subscription_url": f"{Settings.PUBLIC_API_BASE_URL.rstrip('/')}/s8Kx2mP7qR4wT/{created['sub_token']}",
        },
        "sync_ok": sync_ok,
    }


@app.post("/api/admin/users/{tg_id}/manual/extend")
async def admin_extend_manual_user(tg_id: int, payload: ManualUserExtendRequest, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        now = datetime.utcnow()
        cur = user.expiry_at if user.expiry_at and user.expiry_at > now else now
        user.expiry_at = cur + timedelta(days=int(payload.days))
        user.is_active = True
        s.commit()
        s.refresh(user)
        expiry_iso = _safe_iso(user.expiry_at)
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_manual_extend", target_tg_id=tg_id, meta={"days": payload.days})
    return {"ok": True, "expiry_at": expiry_iso}


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
        sub_token = str(user.sub_token or "")
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_manual_regen_token", target_tg_id=tg_id)
    return {
        "ok": True,
        "subscription_url": f"{Settings.PUBLIC_API_BASE_URL.rstrip('/')}/s8Kx2mP7qR4wT/{sub_token}",
    }


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
                query = query.filter(User.expiry_at.isnot(None), User.expiry_at < datetime.utcnow())
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
        now = datetime.utcnow()
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
        row.updated_at = datetime.utcnow()
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
                    "link": r.link,
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
    s = SessionLocal()
    try:
        now = datetime.utcnow()
        row = LiveUpdate(
            title=payload.title.strip(),
            summary=payload.summary.strip(),
            link=payload.link.strip(),
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
        if "published_at" in payload.model_fields_set:
            row.published_at = _parse_optional_datetime(payload.published_at)
        if payload.is_active is not None:
            row.is_active = bool(payload.is_active)
        if payload.sort_order is not None:
            row.sort_order = int(payload.sort_order)
        row.updated_at = datetime.utcnow()
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


@app.post("/api/admin/campaign-links/build")
async def admin_campaign_links_build(payload: AdminCampaignLinksBuildIn, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    promo = (payload.promo_code or "").strip().upper()[:20]
    campaign = (payload.campaign_key or "").strip()[:64]
    plan = (payload.plan_code or "").strip().lower()[:32]
    source = (payload.source or "bot").strip().lower()[:16]
    start_payload = ""
    if campaign and promo:
        start_payload = f"campaign_{campaign}__promo_{promo}"
    elif promo:
        start_payload = f"promo_{promo}"
    elif campaign:
        start_payload = f"campaign_{campaign}"
    bot_username = (BOT_USERNAME or "portal_service_bot").lstrip("@")
    bot_start_link = f"https://t.me/{bot_username}" + (f"?start={start_payload}" if start_payload else "")

    base_checkout = _public_checkout_url() or f"https://{(Settings.PUBLIC_WEB_DOMAIN or 'portal-privacy.online').strip().strip('/')}/checkout"
    parsed = urlparse(base_checkout)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    q["source"] = source or "bot"
    if plan:
        q["plan"] = plan
    if promo:
        q["promo"] = promo
    if campaign:
        q["campaign"] = campaign
    checkout_link = f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/checkout'}?{urlencode(q)}" if parsed.scheme and parsed.netloc else f"/checkout?{urlencode(q)}"

    webapp_base = _safe_public_url(Settings.WEBAPP_URL) or f"https://{(Settings.PUBLIC_WEB_DOMAIN or 'portal-privacy.online').strip().strip('/')}/webapp/"
    wp = urlparse(webapp_base)
    wq = dict(parse_qsl(wp.query, keep_blank_values=True))
    if promo:
        wq["promo"] = promo
    if campaign:
        wq["campaign"] = campaign
    if plan:
        wq["plan"] = plan
    webapp_link = f"{wp.scheme}://{wp.netloc}{wp.path or '/webapp/'}?{urlencode(wq)}" if wp.scheme and wp.netloc else f"/webapp/?{urlencode(wq)}"
    return {"ok": True, "bot_start_link": bot_start_link, "checkout_link": checkout_link, "webapp_link": webapp_link}


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

    await _telegram_send_message(int(ticket.user_tg_id), f"💬 Ответ оператора в тикете #{ticket.id}.")
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
        await _telegram_send_message(int(ticket.user_tg_id), f"✅ Тикет #{ticket.id} закрыт оператором.")
    return {"ticket": _ticket_row(ticket, msgs)}


@app.get("/api/admin/nodes/health")
async def admin_nodes_health(x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        rows = s.query(Node).filter(Node.enabled == True).order_by(Node.health_score.desc(), Node.weight.desc()).all()
        return {
            "nodes": [
                {
                    "code": n.code,
                    "name": n.name,
                    "enabled": bool(n.enabled),
                    "is_healthy": bool(getattr(n, "is_healthy", True)),
                    "health_score": float(getattr(n, "health_score", 0.0) or 0.0),
                    "panel_latency_ms": getattr(n, "panel_latency_ms", None),
                    "panel_error_rate": float(getattr(n, "panel_error_rate", 0.0) or 0.0),
                    "active_clients": int(getattr(n, "active_clients", 0) or 0),
                    "last_ok_at": _safe_iso(getattr(n, "last_ok_at", None)),
                    "last_health_at": _safe_iso(getattr(n, "last_health_at", None)),
                    "weight": int(getattr(n, "weight", 0) or 0),
                }
                for n in rows
            ]
        }
    finally:
        s.close()


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


def _generate_vless_link(*, user_uuid: str, node, name: str) -> str:
    import urllib.parse

    params = {
        "type": "tcp",
        "security": "reality",
        "pbk": node.reality_pbk,
        "fp": node.fingerprint,
        "sni": node.reality_sni,
        "sid": node.reality_sid,
        "spx": "/",
        "flow": node.flow,
    }
    query = "&".join([f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in params.items()])
    safe_name = urllib.parse.quote(name)
    return f"vless://{user_uuid}@{node.host}:{node.vless_port}?{query}#{safe_name}"


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
    return f"{flag} {nm}".strip()


def _singbox_multi_node_config(*, user_uuid: str, nodes: list, title: str) -> dict:
    outbounds = []
    selector_opts = []
    selector_tag = "🌍 Страны"
    for n in nodes:
        tag = _node_label_ru(getattr(n, "code", ""), getattr(n, "name", ""))
        selector_opts.append(tag)
        outbounds.append(
            {
                "type": "vless",
                "tag": tag,
                "server": n.host,
                "server_port": n.vless_port,
                "uuid": user_uuid,
                "flow": n.flow,
                "tls": {
                    "enabled": True,
                    "server_name": n.reality_sni,
                    "utls": {"enabled": True, "fingerprint": n.fingerprint},
                    "reality": {"enabled": True, "public_key": n.reality_pbk, "short_id": n.reality_sid},
                },
                "packet_encoding": "xudp",
            }
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
            "rules": [
                # Split routing defaults:
                # - Keep RU traffic direct (faster/cheaper, reduces unnecessary detours).
                # - Keep large Steam downloads direct (common request).
                # - Keep torrents direct (avoid proxying P2P).
                #
                # Note: split routing is client-side. Apps that import plain vless:// links may ignore this.
                {"geoip": ["ru"], "outbound": "direct"},
                {"geosite": ["geolocation-ru"], "outbound": "direct"},
                {
                    "domain_suffix": [
                        "steampowered.com",
                        "steamcommunity.com",
                        "steamcontent.com",
                        "steamusercontent.com",
                        "steamstatic.com",
                        "steamgames.com",
                        "steamserver.net",
                        "steam-chat.com",
                    ],
                    "outbound": "direct",
                },
                {"domain": ["steamcdn-a.akamaihd.net"], "outbound": "direct"},
                {"protocol": "dns", "outbound": "dns-out"},
                {"protocol": "bittorrent", "outbound": "direct"},
                {"geosite": ["category-ads-all"], "outbound": "block"},
                {"geoip": ["private"], "outbound": "direct"},
            ],
            "auto_detect_interface": True,
            "final": selector_tag,
        },
        "experimental": {
            "cache_file": {"enabled": True},
        },
        "_meta": {"title": title},
    }


def _singbox_free_allowlist_config(*, user_uuid: str, nodes: list, title: str) -> dict:
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

    youtube_domain_suffix = [
        "youtube.com",
        "youtu.be",
        "ytimg.com",
        "googlevideo.com",
        "youtubei.googleapis.com",
        "yt3.ggpht.com",
    ]

    outbounds = []
    for n in nodes:
        outbounds.append(
            {
                "type": "vless",
                "tag": _node_label_ru(n.code, n.name),
                "server": n.host,
                "server_port": n.vless_port,
                "uuid": user_uuid,
                "flow": n.flow,
                "tls": {
                    "enabled": True,
                    "server_name": n.reality_sni,
                    "reality": {"enabled": True, "public_key": n.reality_pbk, "short_id": n.reality_sid},
                    "utls": {"enabled": True, "fingerprint": n.fingerprint},
                },
            }
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
            "rules": [
                {"geoip": ["ru"], "outbound": "direct"},
                {"geosite": ["geolocation-ru"], "outbound": "direct"},
                {
                    "domain_suffix": [
                        "steampowered.com",
                        "steamcommunity.com",
                        "steamcontent.com",
                        "steamusercontent.com",
                        "steamstatic.com",
                        "steamgames.com",
                        "steamserver.net",
                        "steam-chat.com",
                    ],
                    "outbound": "direct",
                },
                {"domain": ["steamcdn-a.akamaihd.net"], "outbound": "direct"},
                {"protocol": "bittorrent", "outbound": "direct"},
                {"domain_suffix": youtube_domain_suffix, "outbound": "direct"},
                {"protocol": "dns", "outbound": "dns-out"},
                {"geosite": ["category-ads-all"], "outbound": "block"},
                {"geoip": ["private"], "outbound": "direct"},
            ],
            "auto_detect_interface": True,
            "final": selector_tag,
        },
        "experimental": {"cache_file": {"enabled": True}},
        "_meta": {"title": title},
    }


def _nodes_for_user(user: User, nodes: list) -> list:
    """
    Per-plan node visibility.
    - FREE: dedicated free pool only.
    - PAID: all enabled non-free nodes.
    """
    if not nodes:
        return nodes
    is_free = (user.sub_type or "").upper() == "FREE"
    plan_code = str(getattr(user, "current_plan_code", "") or "").strip().lower()

    if not is_free:
        if plan_code == "start_99":
            start_nodes = []
            for n in nodes:
                code = (getattr(n, "code", "") or "").lower()
                if "free" in code:
                    continue
                if _node_code_base(code) == "nl":
                    start_nodes.append(n)
            if start_nodes:
                return start_nodes
        paid = []
        for n in nodes:
            code = (getattr(n, "code", "") or "").lower()
            if "free" in code:
                continue
            if _node_code_base(code) in {"brain", "de"}:
                continue
            paid.append(n)
        return paid

    free_nodes = [n for n in nodes if "free" in (getattr(n, "code", "") or "").lower()]
    return free_nodes


@app.get("/s8Kx2mP7qR4wT/{token}")
async def subscription(token: str, request: Request):
    """
    Multi-node subscription endpoint.
    - token is usually `sub_token`
    - legacy fallback: if token is numeric, treat it as `tg_id`
    """
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(sub_token=token).first()
        if not user and token.isdigit():
            user = s.query(User).filter_by(tg_id=int(token)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        _maybe_downgrade_expired_to_free(s, user)

        if not user.is_active:
            return Response(content="", media_type="text/plain")

        nodes = enabled_nodes(s)
    finally:
        s.close()

    user_agent = request.headers.get("user-agent", "").lower()
    is_smart = any(x in user_agent for x in ["hiddify", "dart", "sing-box", "nekobox"])

    header_expire = int(user.expiry_at.timestamp()) if user.expiry_at else 0
    total_bytes = _gb_to_bytes(_plan_total_gb(user))
    headers = {
        "Subscription-Userinfo": f"upload=0; download=0; total={total_bytes}; expire={header_expire}",
        "Profile-Update-Interval": str(int(PROFILE_UPDATE_INTERVAL_HOURS)),
        "Content-Disposition": 'attachment; filename="Portal_Subscription"',
    }

    nodes_for_user = _nodes_for_user(user, nodes)

    # FREE and smart clients receive sing-box JSON profiles.
    if (user.sub_type or "").upper() == "FREE" or is_smart:
        if (user.sub_type or "").upper() == "FREE" and not nodes_for_user:
            # Dedicated free pool is required for FREE users.
            return Response(content="", media_type="text/plain", status_code=503)

        cfg = (
            _singbox_free_allowlist_config(user_uuid=user.uuid, nodes=nodes_for_user, title="Portal (Free)")
            if (user.sub_type or "").upper() == "FREE"
            else _singbox_multi_node_config(user_uuid=user.uuid, nodes=nodes_for_user, title="Portal")
        )
        headers["Content-Disposition"] = 'attachment; filename="Portal.json"'
        headers["Profile-Title"] = "Portal"
        return Response(content=json.dumps(cfg, indent=2), media_type="application/json", headers=headers)

    links = []
    for n in nodes_for_user:
        links.append(_generate_vless_link(user_uuid=user.uuid, node=n, name=_node_label_ru(n.code, n.name)))
    raw = "\n".join(links)
    encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    return Response(content=encoded, media_type="text/plain", headers=headers)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "2096")))





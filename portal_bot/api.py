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
import os
import secrets
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl

import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import or_, func

# Load env from repo-local file first to avoid cwd-dependent startup behavior.
load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
load_dotenv()

from config import Settings, env_bool, env_int
from db import SessionLocal, init_db
from models import (
    AdminAudit,
    FamilySlot,
    Node,
    NodeHealthSample,
    PromoCode,
    PromoUsage,
    Review,
    SupportTicket,
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
from points_service import available_points, preview_redeemable_points


init_db()


API_ENABLE_USAGE = env_bool("API_ENABLE_USAGE", default=False)
AUTO_DOWNGRADE_TO_FREE = env_bool("AUTO_DOWNGRADE_TO_FREE", default=True)
AUTO_FREE_DAYS = int(os.getenv("AUTO_FREE_DAYS", "3650"))
FREE_TOTAL_GB = env_int("FREE_TOTAL_GB", 40)
FREE_LIMIT_IP = env_int("FREE_LIMIT_IP", 2)
PAID_LIMIT_IP = env_int("PAID_LIMIT_IP", 5)
SUPPORT_USERNAME = (os.getenv("SUPPORT_USERNAME") or "portal_privacy_helpbot").lstrip("@")
SUPPORT_USERNAME = (os.getenv("SUPPORT_BOT_USERNAME") or SUPPORT_USERNAME).lstrip("@")
PUBLIC_CHANNEL = (os.getenv("PUBLIC_CHANNEL") or "portal_privacy").lstrip("@")
BOT_USERNAME = (os.getenv("BOT_USERNAME") or "").lstrip("@")
REFERRAL_BONUS_DAYS = env_int("REFERRAL_BONUS_DAYS", 15)
CHANNEL_PREMIUM_DAYS = env_int("CHANNEL_PREMIUM_DAYS", 10)
MAX_BROADCAST_LIMIT = env_int("MAX_BROADCAST_LIMIT", 1000)
PAY_CHECKOUT_URL = (os.getenv("PAY_CHECKOUT_URL") or "").strip()
WEBAPP_ENABLE_HAPTIC = env_bool("WEBAPP_ENABLE_HAPTIC", default=True)
WEBAPP_ENABLE_LOTTIE = env_bool("WEBAPP_ENABLE_LOTTIE", default=True)
WEBAPP_DEV_AUTH = env_bool("WEBAPP_DEV_AUTH", default=False)
WEBAPP_DEV_TG_ID = env_int("WEBAPP_DEV_TG_ID", 0)
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
    "1_month": 199,
    "3_months": 499,
    "6_months": 949,
    "9_months": 1299,
    "12_months": 1499,
}


class TicketMessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    media_type: str | None = Field(default=None, max_length=32)
    media_file_id: str | None = Field(default=None, max_length=256)
    media_payload: str | None = Field(default=None, max_length=2000)


class TicketCreateIn(TicketMessageIn):
    subject: str | None = Field(default=None, max_length=200)


class PromoRedeemIn(BaseModel):
    code: str = Field(min_length=3, max_length=20)


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


class EventIn(BaseModel):
    event_name: str = Field(min_length=2, max_length=64)
    source: str = Field(default="webapp", max_length=32)
    session_id: str | None = Field(default=None, max_length=64)
    meta: dict[str, Any] | None = None


class PayAttemptStartIn(BaseModel):
    plan_code: str = Field(min_length=2, max_length=32)
    source: str = Field(default="webapp", max_length=32)
    offer_id: int | None = None


class DashboardResponse(BaseModel):
    tg_id: int
    sub_type: str
    is_active: bool
    expiry_at: str | None
    used_gb: float
    total_gb: float
    remaining_gb: float
    active_sessions: int
    device_limit: int
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
    st = (user.sub_type or "").upper()
    if st == "FREE":
        return max(0, int(FREE_LIMIT_IP))
    return max(0, int(PAID_LIMIT_IP))


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
            s.commit()
            return True

        user.sub_type = "FREE"
        user.expiry_at = datetime.utcnow() + timedelta(days=int(AUTO_FREE_DAYS))
        user.is_active = True
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
    if not x_telegram_init_data:
        dev = _dev_auth_user(request)
        if dev:
            return dev
        raise HTTPException(status_code=401, detail="Telegram auth required")
    user_data = _verify_telegram_data(x_telegram_init_data)
    if not user_data:
        dev = _dev_auth_user(request)
        if dev:
            return dev
        raise HTTPException(status_code=401, detail="Invalid Telegram signature")
    return user_data


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
    base = _node_code_base(code)
    names = {"pl": "Poland", "it": "Italy", "us": "USA", "de": "Germany", "brain": "Germany"}
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


@app.get("/api/admin/metrics/status")
async def admin_metrics_status(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data, request=request)
    stale_after_seconds = max(300, int(os.getenv("NODE_METRICS_STALE_AFTER_SECONDS", "900")))
    now = datetime.utcnow()
    s = SessionLocal()
    try:
        last_sample = s.query(func.max(NodeHealthSample.sampled_at)).scalar()
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
                    "username": r.username or "user",
                    "rating": r.rating,
                    "text": r.text or "",
                    "date": r.created_at.strftime("%d.%m.%Y") if r.created_at else "",
                }
                for r in rows
            ]
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
    max_preview = preview_redeemable_points(tg_id=tg_id, plan_price_stars=API_PLAN_PRICES["1_month"], first_purchase_discount_pct=0.20)
    return {
        "tg_id": tg_id,
        "available_points": int(avail),
        "expiring_soon_points": int(expiring_soon),
        "monthly_cap": 300,
        "points_expiry_days": 90,
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

        _maybe_downgrade_expired_to_free(s, user)

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
        can_claim_channel_bonus = bool(
            PUBLIC_CHANNEL
            and not channel_claimed_at
            and (user.sub_type or "").upper() != "MANUAL"
        )

        return {
            "tg_id": tg_id,
            "username": user.username or auth_user.get("username"),
            "subscription_url": subscription_url,
            "is_active": is_active,
            "is_admin": role_admin,
            "sub_type": user.sub_type,
            "segment": segment,
            "expiry_at": user.expiry_at.isoformat() if user.expiry_at else None,
            "limits": {
                "device_limit": _plan_device_limit(user) + family_slots,
                "total_gb": total_gb,
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
            },
            "actions": {
                "open_helpbot": support_link,
                "open_channel": channel_link,
                "pay_via_bot": (
                    PAY_CHECKOUT_URL
                    if PAY_CHECKOUT_URL
                    else (f"https://t.me/{BOT_USERNAME}?start=pay" if BOT_USERNAME else "")
                ),
            },
            "active_offer": _active_offer_payload(tg_id),
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
            is_active=active,
            expiry_at=_safe_iso(expiry),
            used_gb=float(used_gb),
            total_gb=float(total_gb),
            remaining_gb=float(remaining),
            active_sessions=int(getattr(user, "active_sessions", 0) or 0),
            device_limit=int(_plan_device_limit(user) + family_slots),
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
        return {
            "tg_id": tg_id,
            "referral_count": int(user.referral_count or 0),
            "referral_code": user.referral_code or "",
            "referral_bonus_days": REFERRAL_BONUS_DAYS,
            "streak_months": int(user.streak_months or 0),
            "last_wheel_spin": _safe_iso(user.last_wheel_spin),
            "channel_bonus_premium_days": int(CHANNEL_PREMIUM_DAYS),
            "channel_bonus_claimed_at": _safe_iso(getattr(user, "channel_bonus_claimed_at", None)),
            "channel_username": PUBLIC_CHANNEL,
        }
    finally:
        s.close()


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
        if (user.sub_type or "").upper() == "MANUAL":
            raise HTTPException(status_code=400, detail="Bonus is disabled for manual accounts")
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
        user.is_active = True
        user.channel_bonus_claimed_at = now
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
        if promo_type == "days" and value > 0:
            now = datetime.utcnow()
            if user.expiry_at and user.expiry_at > now:
                user.expiry_at = user.expiry_at + timedelta(days=value)
            else:
                user.expiry_at = now + timedelta(days=value)
            user.is_active = True
            applied_days = value

        promo.uses_left = max(0, int(promo.uses_left or 0) - 1)
        s.add(PromoUsage(tg_id=tg_id, promo_code=promo.code))
        s.commit()
        return {
            "ok": True,
            "code": promo.code,
            "promo_type": promo_type,
            "value": value,
            "applied_days": applied_days,
            "uses_left": int(promo.uses_left or 0),
        }
    finally:
        s.close()


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
    base = _node_code_base(code_raw)
    flags = {"pl": "🇵🇱", "it": "🇮🇹", "us": "🇺🇸", "brain": "🇩🇪", "de": "🇩🇪"}
    names = {"pl": "Польша", "it": "Италия", "us": "США", "brain": "Германия", "de": "Германия"}
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

    if not is_free:
        paid = [n for n in nodes if "free" not in (getattr(n, "code", "") or "").lower()]
        return paid or nodes

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
        "Profile-Update-Interval": "24",
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





# -*- coding: utf-8 -*-
"""
POKROV API for Telegram WebApp and Subscription endpoint.

- `/api/user/{tg_id}`: authenticated by Telegram WebApp initData
- `/api/reviews`: featured reviews for WebApp
- `/s8Kx2mP7qR4wT/{token}`: subscription endpoint (multi-node)
"""

from __future__ import annotations

import base64
import contextlib
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
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse

import aiohttp
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, case, func, text
from sqlalchemy import text as sql_text
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Load env from repo-local file first to avoid cwd-dependent startup behavior.
load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
load_dotenv()

from config import Settings, env_bool, env_int
from db import SessionLocal, init_db
from models import (
    AccessKey,
    AccountDevice,
    AccountExperienceState,
    ConnectionEvidence,
    Achievement,
    AdminAudit,
    AppSetting,
    AuthSession,
    AntiAbuseEvent,
    AcquisitionHandoff,
    AcquisitionSession,
    CampaignSend,
    DevicePairingCode,
    Event,
    EntitlementGrant,
    ExternalOrder,
    ExternalPaymentEvent,
    FamilySlot,
    FeedbackEntry,
    FunnelEvent,
    GiftCard,
    IncentiveCampaign,
    KeyActionHistory,
    KeyPressureState,
    KeySourceObservation,
    KeyUsageRollup,
    LiveUpdate,
    Node,
    NodeCapacityPolicy,
    NodeHealthSample,
    NodePoolMembership,
    NodeProvisioningJob,
    NodeRuntimeMetric,
    ObserverBatch,
    ObserverUserState,
    OpsAlert,
    PlanCatalog,
    PromoCode,
    PromoUsage,
    ProgramApplication,
    PayAttempt,
    PaymentEntitlementClaim,
    ProviderTrafficQuota,
    ProviderTrafficQuotaAudit,
    ReferralBonusQueue,
    ReferralRelationship,
    RenderedSubscriptionSnapshot,
    Review,
    RewardClaim,
    ServiceIncident,
    SecurityEvent,
    SecurityRateLimitBucket,
    StartLink,
    SupportAttachment,
    SupportTicket,
    SupportTicketMessage,
    SubscriptionFetchEvent,
    Template,
    User,
    UserKeyPolicy,
    UserNode,
    WebCabinetHandoffToken,
    WebEmailIdentity,
    WebEmailToken,
    WarpEvent,
    WarpMaterial,
)
from payment_providers import (
    PROVIDER_META,
    callback_ids as payment_callback_ids,
    callback_status as payment_callback_status,
    create_rub_payment,
    enabled_public_provider_catalog,
    normalize_provider as _normalize_checkout_provider,
    public_provider_is_configured_for_plan,
    provider_is_configured,
    verify_callback_signature as verify_provider_callback_signature,
)
from tickets_repo import (
    STATUS_CLOSED,
    STATUS_IN_PROGRESS,
    STATUS_OPEN,
    add_ticket_message,
    can_access_support_attachment,
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
from support_ai_service import SupportAIConfig
from support_agent_service import SupportAgentService, support_fallback_reply
from nodes_repo import enabled_nodes
from node_policy import (
    AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED,
    CAPACITY_AWARE_NODE_SELECTION,
    KEY_PRESSURE_FAIR_USE_ROUTING,
    KEY_PRESSURE_SCORING,
    SMART_CONNECT_SHORTLIST_LIMIT,
    SMART_CONNECT_STALE_AFTER_SECONDS,
    SMART_CONNECT_STICKINESS_THRESHOLD_PERCENT,
    SUBSCRIPTION_DYNAMIC_ORDERING,
    SUBSCRIPTION_EXCLUDE_HARD_REJECT,
    PAID_ROLE,
    canonical_free_node_code,
    free_tier_enabled,
    node_access_role,
    node_capacity_status,
    node_backend_penalty,
    node_cpu_penalty,
    node_hard_reject_reason,
    node_is_free,
    node_is_stale,
    node_selection_score,
    node_tx_ratio,
    node_tx_mbps,
    rank_nodes_for_app,
    rank_nodes_legacy,
    rank_nodes_for_subscription,
    free_user_has_bounded_premium_trial,
    user_free_access_role,
    user_uses_free_pool,
)
from control_panel import ControlPanel
from events_service import track_event
from acquisition_service import (
    AcquisitionError,
    acquisition_snapshot,
    clean_acquisition_slug,
    clean_entry_route,
    consume_acquisition_handoff,
    create_acquisition_handoff,
    normalize_acquisition_touch,
    record_funnel_event,
)
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
from free_cycle_service import (
    FREE_STANDARD_QUOTA_BYTES,
    ensure_user_free_cycle_state,
    mark_user_became_free,
    project_user_to_expired,
    queue_free_profile_reentry,
    reconcile_free_profile_usage,
    reconcile_free_profile_usage_in_new_transaction,
)
from email_auth_service import (
    DuplicateEmailIdentityError,
    InvalidEmailCredentialsError,
    InvalidEmailInputError,
    InvalidEmailTokenError,
    authenticate_email_identity,
    build_debug_payload as build_email_auth_debug_payload,
    consume_login_otp,
    deliver_auth_message,
    email_login_otp_configured,
    get_verified_identity_for_user,
    issue_login_otp,
    register_email_identity,
    start_password_reset,
    validate_email_input,
    verify_email_identity,
    finish_password_reset,
)
from email_delivery_service import deliver_payment_access_key, email_delivery_runtime_status
from account_security_errors import AccountRecoveryError, EmailOtpError
from antiabuse_privacy_service import record_antiabuse_event
from economy_service import (
    create_referral_relationship,
    migrate_pending_legacy_referral_queue,
    queue_first_payment_referrer_reward,
    read_trial_projection,
    rebuild_account_entitlement_projection,
    record_successful_payment_grant,
    release_due_referrer_rewards,
)
from rewards_service import (
    PAID_FORTNIGHTLY_DISCOUNTS_V3,
    PAID_WEEKLY_DISCOUNTS_V2,
    PAID_WEEKLY_V1,
    CalendarState,
    InvalidWheelConfig,
    RewardConflict,
    RewardDisabled,
    RewardDomainError,
    RewardForbidden,
    WheelState,
    checkin_calendar,
    ensure_referral_code,
    evaluate_active_paid,
    get_calendar_state,
    get_reward_history,
    get_wheel_state,
    parse_paid_weekly_config,
    spin_wheel,
)
from payment_entitlement_service import (
    PaymentEntitlementNotFoundError,
    ensure_fallback_gift_card,
    ensure_pending_claim,
    mark_paid_and_fulfill_attached_claim,
    mark_paid as mark_payment_entitlement_paid,
    redeem_payment_fallback,
    record_claim_error as record_payment_entitlement_claim_error,
    reverse_claim as reverse_payment_entitlement_claim,
)
from account_recovery_service import (
    complete_access_reissue,
    exchange_recovery_code,
    rotate_recovery_code,
)
import app_first_service
import account_experience_service
import auth_session_service
import channel_bonus_service
import device_pairing_service
import incident_service
import program_application_service
from account_foundation_service import ensure_user_account_foundation
from gift_cards_service import redeem_gift_card as redeem_gift_card_service
from observer_service import (
    OBSERVER_PUSH_MAX_AGE_SECONDS,
    build_admin_observer_block,
    get_observer_state_map,
    ingest_observer_batch,
    is_observer_batch_unique_conflict,
    observer_batch_replay_response,
    observer_stale_after_seconds,
)
from network_rollout import (
    NETWORK_ROLLOUT_CONFIG_KEY,
    load_network_rollout_config,
    normalized_network_rollout_config,
    ru_bridge_relay_config,
    ru_bridge_relay_enabled,
    ru_bridge_relay_endpoints,
    resolved_client_policy,
    transport_node_allowlist,
    transport_node_exclusions,
)
from public_urls import build_subscription_url, public_connect_base_url, public_connect_host
from shared_surface_facts import (
    get_access_matrix,
    get_product_facts,
    get_promo_slots,
    get_public_urls,
    get_tariff_catalog,
)
from transport_catalog import LEGACY_REALITY_FALLBACK, OPERATOR_LAB, RESERVE_XHTTP_CDN, RU_BRIDGE_RELAY, has_explicit_transport_profile, node_transport_profiles, transport_profile_by_name
from web_auth_service import (
    SESSION_TTL_SECONDS,
    build_telegram_oidc_authorize_url,
    create_web_session_token,
    exchange_telegram_oidc_code,
    inspect_web_session_token,
    verify_telegram_login_payload,
    verify_telegram_oidc_state_token,
)
from warp_service import (
    build_warp_admin_summary,
    build_warp_status,
    managed_warp_policy_for_user,
    mark_warp_material_rotation_requested,
    provision_warp_material,
    public_warp_policy_for_user,
    record_warp_event,
    revoke_warp_material,
    warp_material_public_payload,
)
from admin_ops_service import (
    MANAGED_ALERT_SOURCES as _OPS_MANAGED_ALERT_SOURCES,
    admin_search_results as _ops_admin_search_results,
    admin_nodes_capacity_payload as _ops_admin_nodes_capacity_payload,
    alert_payload as _ops_alert_payload,
    build_admin_metrics_status_snapshot as _ops_build_admin_metrics_status_snapshot,
    build_alert_candidates as _ops_build_alert_candidates,
    build_node_observability as _ops_build_node_observability,
    bytes_to_gb as _ops_bytes_to_gb,
    free_tier_summary as _ops_free_tier_summary,
    free_tier_user_rows as _ops_free_tier_user_rows,
    gb_to_bytes as _ops_gb_to_bytes,
    node_timeseries_rows as _ops_node_timeseries_rows,
    ops_alert_notification_batches as _ops_alert_notification_batches,
    provider_quota_payload as _ops_provider_quota_payload,
    provider_quota_status_rows as _ops_provider_quota_status_rows,
    refresh_ops_alerts_for_current_state as _ops_refresh_alerts_for_current_state,
    refresh_ops_alerts as _ops_refresh_alerts,
    traffic_summary_rows as _ops_traffic_summary_rows,
)
from admin_action_intent_service import (
    NODE_MAPPING_LOCK_NAMESPACE,
    ActionIntentError,
    action_intent_error_identifiers as _action_intent_error_identifiers,
    execute_action_intent as _execute_action_intent,
    get_action_intent_status as _get_action_intent_status,
    node_resync_recipient_fingerprint as _node_resync_recipient_fingerprint,
    prepare_action_intent as _prepare_action_intent,
)
from internal_request_auth import (
    InternalAuthError,
    authenticate_internal_request,
    load_internal_service_key_registry,
)
from ru_probe_contract import RuProbeContractError, validate_run_payload
from ru_probe_service import (
    RuProbeConfigurationError,
    RuProbePayloadConflict,
    RuProbeReadModelError,
    build_ru_manifest,
    evaluate_ru_run,
    get_latest_ru_status,
    get_ru_run_history,
    get_ru_uploader_status,
    store_evaluated_ru_run,
    store_ru_heartbeat,
    validate_ru_heartbeat,
)
from release_evidence_service import (
    ReleaseEvidenceConflict,
    ReleaseEvidenceNotFound,
    ReleaseEvidenceReadError,
    ReleaseEvidenceValidationError,
    get_release_readiness,
    import_release_evidence,
    list_release_candidates,
)


HIDDIFY_HIDDEN_TAG_SUFFIX = " §hide§"
RU_BRIDGE_OUTBOUND_TAG = f"POKROV мост{HIDDIFY_HIDDEN_TAG_SUFFIX}"
RU_BRIDGE_SELECTOR_DIRECT_CODES = {
    token.strip().lower()
    for token in str(os.getenv("RU_BRIDGE_SELECTOR_DIRECT_CODES", "de") or "").split(",")
    if token.strip()
}


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


def _reward_now() -> datetime:
    """Injectable reward clock kept separate from auth/session time."""
    return _utcnow()


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
AUTO_DOWNGRADE_TO_FREE = free_tier_enabled() and env_bool("AUTO_DOWNGRADE_TO_FREE", default=False)
AUTO_FREE_DAYS = int(os.getenv("AUTO_FREE_DAYS", "3650"))
FREE_TOTAL_GB = int(FREE_STANDARD_QUOTA_BYTES // (1024**3))
FREE_STANDARD_QUOTA_GB = int(FREE_STANDARD_QUOTA_BYTES // (1024**3))
FREE_LIMIT_IP = 1
PAID_LIMIT_IP = env_int("PAID_LIMIT_IP", 5)
FREE_SPEED_LIMIT_KBPS = env_int(
    "FREE_SPEED_LIMIT_KBPS",
    int(round(float(_FREE_TIER_FACTS.get("speed_limit_mbps", 50) or 50) * 125)),
)
FREE_SOFT_MODE_SPEED_LIMIT_KBPS = int(
    round(float(_FREE_TIER_FACTS.get("soft_mode_speed_limit_mbps", 2) or 2) * 125)
)
SUPPORT_USERNAME = (
    os.getenv("SUPPORT_USERNAME") or _shared_telegram_username("support_bot_username", "@pokrov_supportbot")
).lstrip("@")
SUPPORT_USERNAME = (os.getenv("SUPPORT_BOT_USERNAME") or SUPPORT_USERNAME).lstrip("@")
PUBLIC_CHANNEL = (os.getenv("PUBLIC_CHANNEL") or _shared_telegram_username("channel_username", "@pokrov_vpn")).lstrip("@")
BOT_USERNAME = (os.getenv("BOT_USERNAME") or _shared_telegram_username("bot_username", "@pokrov_vpnbot")).lstrip("@")
REFERRAL_BONUS_DAYS = env_int("REFERRAL_BONUS_DAYS", 10)
REFERRAL_ANTIFRAUD_HOURS = max(0, env_int("REFERRAL_ANTIFRAUD_HOURS", 24))
REFERRAL_ANTIFRAUD_MAX_WAIT_HOURS = max(1, env_int("REFERRAL_ANTIFRAUD_MAX_WAIT_HOURS", 168))
CHANNEL_PREMIUM_DAYS = 5
APP_TRIAL_DEFAULT_DAYS = 5
APP_TRIAL_MAX_DAYS = 5
WEB_EMAIL_ACCOUNT_TG_ID_BASE = max(8_000_000_000_000, env_int("WEB_EMAIL_ACCOUNT_TG_ID_BASE", 8_000_000_000_000))
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
PAID_CHECKOUT_LAUNCH_APPROVED = env_bool("PAID_CHECKOUT_LAUNCH_APPROVED", default=False)
CHECKOUT_WIDGET_ENABLED = env_bool("CHECKOUT_WIDGET_ENABLED", default=False)
CHANNEL_SPEED_BUMP_ENABLED = env_bool("CHANNEL_SPEED_BUMP_ENABLED", default=False)
BONUS_WHEEL_ENABLED = env_bool("BONUS_WHEEL_ENABLED", default=True)
BONUS_CALENDAR_ENABLED = env_bool("BONUS_CALENDAR_ENABLED", default=False)
BONUS_CALENDAR_REWARD_DAYS = max(0, env_int("BONUS_CALENDAR_REWARD_DAYS", 1))
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
PAYMENT_CALLBACK_TOLERANT_MODE = env_bool("PAYMENT_CALLBACK_TOLERANT_MODE", default=False)
FREEKASSA_GENERIC_HMAC_COMPAT_ENABLED = env_bool(
    "FREEKASSA_GENERIC_HMAC_COMPAT_ENABLED",
    default=False,
)
SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED = env_bool("SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED", default=False)
TELEGRAM_WEB_LOGIN_MAX_AGE_SECONDS = max(60, env_int("TELEGRAM_WEB_LOGIN_MAX_AGE_SECONDS", 86400))
ADMIN_WEB_SESSION_TTL_SECONDS = max(300, env_int("ADMIN_WEB_SESSION_TTL_SECONDS", 3600))
CABINET_HANDOFF_TTL_SECONDS = max(60, min(120, env_int("CABINET_HANDOFF_TTL_SECONDS", 120)))
CABINET_HANDOFF_LEDGER_RETENTION_SECONDS = max(3600, env_int("CABINET_HANDOFF_LEDGER_RETENTION_SECONDS", 86400))
NODE_METRICS_PORT_CAPACITY_MBPS = _env_float("NODE_METRICS_PORT_CAPACITY_MBPS", 1000.0)
SUPPORT_UPLOAD_DIR = Path(
    os.getenv("SUPPORT_UPLOAD_DIR") or (Path(__file__).resolve().parent / "uploads" / "support")
).resolve()
SUPPORT_UPLOAD_URL_PREFIX = f"/{(os.getenv('SUPPORT_UPLOAD_URL_PREFIX') or 'uploads/support').strip().strip('/')}"
SUPPORT_UPLOAD_MAX_BYTES = max(1, env_int("SUPPORT_UPLOAD_MAX_BYTES", 20 * 1024 * 1024))
SUPPORT_PENDING_UPLOAD_TTL_HOURS = max(1, env_int("SUPPORT_PENDING_UPLOAD_TTL_HOURS", 24))
SUPPORT_PENDING_UPLOAD_MAX_COUNT = max(1, env_int("SUPPORT_PENDING_UPLOAD_MAX_COUNT", 5))
SUPPORT_PENDING_UPLOAD_MAX_BYTES = max(
    1,
    env_int("SUPPORT_PENDING_UPLOAD_MAX_BYTES", 50 * 1024 * 1024),
)
SUPPORT_ATTACHMENT_URL_PREFIX = f"/{(os.getenv('SUPPORT_ATTACHMENT_URL_PREFIX') or 'api/tickets/attachments').strip().strip('/')}"
WEB_SESSION_COOKIE_NAME = (os.getenv("WEB_SESSION_COOKIE_NAME") or "portal_web_session").strip() or "portal_web_session"
WEB_SESSION_COOKIE_DOMAIN = (os.getenv("WEB_SESSION_COOKIE_DOMAIN") or ".pokrov.space").strip() or ".pokrov.space"
WEB_SESSION_COOKIE_SAMESITE = (os.getenv("WEB_SESSION_COOKIE_SAMESITE") or "lax").strip().lower() or "lax"
PAYMENT_CALLBACK_MAX_BYTES = max(1024, env_int("PAYMENT_CALLBACK_MAX_BYTES", 256 * 1024))
SUPPORT_AI_CONFIG = SupportAIConfig.from_env()
SUPPORT_AGENT_SERVICE = SupportAgentService(config=SUPPORT_AI_CONFIG)
support_ai_last_reply_at: dict[int, float] = {}
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


def _normalize_cors_origin(raw: str) -> str:
    value = str(raw or "").strip().rstrip("/")
    if not value or value == "*":
        return ""
    try:
        parsed = urlparse(value)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
    except Exception:
        pass
    return value.lower()


def _build_cors_allowed_origins() -> list[str]:
    configured = [
        "https://pokrov.space",
        "https://www.pokrov.space",
        "https://app.pokrov.space",
        "https://admin.pokrov.space",
        "https://www.admin.pokrov.space",
        "https://pay.pokrov.space",
    ]
    for attr in ("WEBAPP_URL", "PAY_CHECKOUT_URL", "API_BASE_URL"):
        configured.append(str(getattr(Settings, attr, "") or ""))
    configured.extend(WEBAPP_DEV_ALLOWED_ORIGINS)
    configured.extend((os.getenv("API_CORS_ALLOWED_ORIGINS") or "").split(","))

    origins: list[str] = []
    for value in configured:
        origin = _normalize_cors_origin(value)
        if origin and origin not in origins:
            origins.append(origin)
    if not origins:
        origins.append("https://app.pokrov.space")
    if "*" in configured:
        logger.warning("Ignoring wildcard API_CORS_ALLOWED_ORIGINS because credentials are enabled")
    return origins


API_CORS_ALLOWED_ORIGINS = _build_cors_allowed_origins()
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
    "standard": {"days": 30, "stars": 239, "name": "Standard"},
    "premium": {"days": 90, "stars": 669, "name": "Premium"},
}
PAYMENT_PROVIDER_WHITELIST = {"cardlink", "freekassa", "lavatop", "pally", "platima"}
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
            "title": "Новые узлы NL/PL",
            "summary": "Добавлены свежие точки доступа и обновлены рекомендации по клиентам.",
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


def _default_live_updates() -> list[dict[str, Any]]:
    channel = (PUBLIC_CHANNEL or "pokrov_vpn").lstrip("@")
    return [
        {
            "id": 0,
            "title": "Новые точки подключения NL/PL",
            "summary": "Обновили точки доступа и короткие рекомендации по старту для актуальных клиентов.",
            "date": "2026-02-14",
            "link": f"https://t.me/{channel}/1",
        },
        {
            "id": 0,
            "title": "Обновлён кабинет POKROV",
            "summary": "Сделали поддержку, загрузки и checkout прямее и без лишнего шума.",
            "date": "2026-02-13",
            "link": f"https://t.me/{channel}/2",
        },
        {
            "id": 0,
            "title": "Короткий путь к запуску",
            "summary": "Проверили быстрый вход через Telegram и обновили открывающие ссылки для новых пользователей.",
            "date": "2026-02-12",
            "link": f"https://t.me/{channel}/3",
        },
    ]


DEFAULT_WHEEL_CONFIG: dict[str, Any] = PAID_FORTNIGHTLY_DISCOUNTS_V3


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
    try:
        config = parse_paid_weekly_config(
            payload or PAID_FORTNIGHTLY_DISCOUNTS_V3,
            explicit=payload is not None,
        )
    except InvalidWheelConfig as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "wheel_config_invalid",
                "validation_code": exc.code,
            },
        ) from None
    weights = [
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
    return {
        "preset": config.preset,
        "weights": weights,
        "cooldown_hours": config.cooldown_hours,
    }

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
    src = str(source or "").strip().lower()
    if src not in {"site", "bot"}:
        return {}
    return shops.get(src, {})


def _fk_shop_by_merchant_id(merchant_id: str) -> dict[str, str]:
    mid = str(merchant_id or "").strip()
    if not mid:
        return {}
    for cfg in _fk_shop_configs().values():
        if str(cfg.get("shop_id") or "").strip() == mid:
            return cfg
    return {}


def _fk_source_by_merchant_id(merchant_id: str) -> str:
    mid = str(merchant_id or "").strip()
    if not mid:
        return ""
    for source, cfg in _fk_shop_configs().items():
        if str(cfg.get("shop_id") or "").strip() == mid:
            return source
    return ""


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
    return _request_client_ip(request)


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


def _is_loopback_ip(ip: str) -> bool:
    try:
        return bool(ipaddress.ip_address(str(ip or "").strip()).is_loopback)
    except Exception:
        return False


class TicketMessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    attachment_id: str | None = Field(default=None, max_length=160)
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


class EmailOtpStartIn(BaseModel):
    email: str = Field(min_length=5, max_length=200)


class EmailOtpFinishIn(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    code: str = Field(min_length=6, max_length=6)
    install_id: str | None = Field(default=None, min_length=8, max_length=128)
    device_name: str | None = Field(default=None, max_length=120)
    platform: str | None = Field(default=None, max_length=32)
    os_version: str | None = Field(default=None, max_length=64)
    app_version: str | None = Field(default=None, max_length=32)
    locale: str | None = Field(default=None, max_length=32)
    time_zone: str | None = Field(default=None, max_length=64)


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


class AppSessionRefreshIn(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=512)


class RecoveryCodeExchangeIn(BaseModel):
    code: str = Field(min_length=18, max_length=32)
    install_id: str = Field(min_length=8, max_length=128)
    device_name: str = Field(min_length=2, max_length=120)
    platform: str = Field(min_length=2, max_length=32)
    os_version: str | None = Field(default=None, max_length=64)
    app_version: str | None = Field(default=None, max_length=32)
    locale: str | None = Field(default=None, max_length=32)
    time_zone: str | None = Field(default=None, max_length=64)


class AccessReissueIn(BaseModel):
    mode: str = Field(min_length=3, max_length=32)


class AccessKeyRedeemIn(BaseModel):
    key: str = Field(min_length=3, max_length=64)


class UnifiedRedeemIn(BaseModel):
    code: str = Field(min_length=3, max_length=4096)


class ClientCabinetTokenIn(BaseModel):
    target_path: str = Field(default="/", min_length=1, max_length=512)


class CabinetHandoffExchangeIn(BaseModel):
    handoff_token: str | None = Field(default=None, max_length=4096)
    token: str | None = Field(default=None, max_length=4096)


class ClientRoutePolicyIn(BaseModel):
    route_mode: str = Field(default=app_first_service.ROUTE_MODE_ALL_TRAFFIC, min_length=3, max_length=32)
    selected_apps: list[str] = Field(default_factory=list, max_length=128)
    requires_elevated_privileges: bool | None = None


class ClientWarpConsentIn(BaseModel):
    consent: bool = True
    reason_code: str | None = Field(default=None, max_length=64)


class ClientWarpActionIn(BaseModel):
    reason_code: str | None = Field(default=None, max_length=64)


class ClientWarpRuntimeEventIn(BaseModel):
    event_name: str = Field(min_length=2, max_length=64)
    state: str | None = Field(default=None, max_length=32)
    reason_code: str | None = Field(default=None, max_length=64)
    message: str | None = Field(default=None, max_length=500)
    meta: dict[str, Any] | None = None


class ClientNotificationsReadIn(BaseModel):
    ids: list[str] = Field(default_factory=list, max_length=100)


class ClientPushRegisterIn(BaseModel):
    platform: str = Field(min_length=2, max_length=32)
    provider: str = Field(min_length=2, max_length=32)
    token: str = Field(min_length=4, max_length=4096)


class ClientSupportAssistantIn(BaseModel):
    ticket_id: int | None = Field(default=None, ge=1)
    ticketId: int | None = Field(default=None, ge=1)
    assistant_session_id: str | None = Field(default=None, max_length=128)
    assistantSessionId: str | None = Field(default=None, max_length=128)
    message: str = Field(min_length=1, max_length=2000)
    scope: str = Field(default="support", min_length=2, max_length=32)
    safeDiagnostics: dict[str, Any] = Field(default_factory=dict)


class ClientDevicePairingClaimIn(BaseModel):
    code: str = Field(min_length=8, max_length=12)
    install_id: str = Field(min_length=8, max_length=128)
    device_name: str = Field(default="Новое устройство", min_length=1, max_length=120)
    platform: str = Field(default="device", min_length=2, max_length=32)
    os_version: str | None = Field(default=None, max_length=64)
    app_version: str | None = Field(default=None, max_length=32)
    locale: str | None = Field(default=None, max_length=32)
    time_zone: str | None = Field(default=None, max_length=64)


class ProgramApplicationCreateIn(BaseModel):
    kind: str = Field(min_length=3, max_length=32)
    source_name: str | None = Field(default=None, max_length=100)
    seats: int | None = Field(default=None, ge=2, le=50)
    summary: str = Field(min_length=20, max_length=2000)
    contact: str | None = Field(default=None, max_length=160)


class AdminWarpMaterialPutIn(BaseModel):
    tg_id: int = Field(gt=0)
    install_id: str | None = Field(default=None, max_length=128)
    source: str = Field(default="operator_provisioned", min_length=2, max_length=64)
    mode: str = Field(default="proxy_over_warp", min_length=3, max_length=32)
    wireguard_config: dict[str, Any] = Field(default_factory=dict)
    account: dict[str, Any] | None = None


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
    dry_run: bool = False


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


class AdminActionIntentTargetIn(BaseModel):
    type: str = Field(min_length=1, max_length=32)
    id: str = Field(min_length=1, max_length=128)


class AdminActionIntentPrepareIn(BaseModel):
    action: str = Field(min_length=1, max_length=64)
    target: AdminActionIntentTargetIn
    payload: dict[str, Any] = Field(default_factory=dict)


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
    badge_label: str | None = Field(default=None, max_length=48)
    image_url: str | None = Field(default=None, max_length=600)
    image_layout: str | None = Field(default=None, max_length=24)
    cta_label: str | None = Field(default=None, max_length=80)
    cta_href: str | None = Field(default=None, max_length=600)
    accent_color: str | None = Field(default=None, max_length=9)
    background_color: str | None = Field(default=None, max_length=9)
    text_color: str | None = Field(default=None, max_length=9)
    button_color: str | None = Field(default=None, max_length=9)
    button_text_color: str | None = Field(default=None, max_length=9)
    placement: str | None = Field(default=None, max_length=64)
    dismissible: bool = True
    whole_card_clickable: bool = True
    starts_at: str | None = Field(default=None, max_length=64)
    ends_at: str | None = Field(default=None, max_length=64)
    contexts: list[str] = Field(default_factory=list, max_length=32)
    sort_order: int = Field(default=100, ge=0, le=10_000)


class AdminPromoSlotsPutIn(BaseModel):
    assignments: list[AdminPromoSlotAssignmentIn] = Field(default_factory=list, max_length=128)


class EventIn(BaseModel):
    event_name: str = Field(min_length=2, max_length=64)
    source: str = Field(default="webapp", max_length=32)
    session_id: str | None = Field(default=None, max_length=64)
    meta: dict[str, Any] | None = None


class FunnelEventIn(BaseModel):
    event_name: str = Field(min_length=2, max_length=64)
    stage: str = Field(default="site_visit", max_length=64)
    channel: str = Field(default="site", max_length=32)
    source: str = Field(default="site", max_length=64)
    session_id: str = Field(min_length=8, max_length=96)
    path: str | None = Field(default=None, max_length=512)
    referrer: str | None = Field(default=None, max_length=600)
    campaign: str | None = Field(default=None, max_length=64)
    utm_content: str | None = Field(default=None, max_length=64)
    ref: str | None = Field(default=None, max_length=64)
    entry_route: str | None = Field(default=None, max_length=128)
    meta: dict[str, Any] | None = None


class AcquisitionHandoffCreateIn(BaseModel):
    session_id: str = Field(min_length=8, max_length=96)
    purpose: str = Field(min_length=3, max_length=32)
    asset: str | None = Field(default=None, max_length=96)
    channel: str = Field(default="site", max_length=32)
    source: str = Field(default="unknown", max_length=64)
    campaign: str | None = Field(default=None, max_length=64)
    utm_content: str | None = Field(default=None, max_length=64)
    ref: str | None = Field(default=None, max_length=64)
    entry_route: str | None = Field(default=None, max_length=128)
    referrer: str | None = Field(default=None, max_length=600)


class AcquisitionHandoffConsumeIn(BaseModel):
    handle: str = Field(min_length=32, max_length=160)
    purpose: str = Field(default="account_continue", min_length=3, max_length=32)


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
    payment_method: str | None = Field(default=None, max_length=16)
    acquisition_handle: str | None = Field(default=None, min_length=32, max_length=160)


class FreekassaPublicOrderCreateIn(BaseModel):
    plan_code: str = Field(min_length=2, max_length=32)
    checkout_ticket: str = Field(min_length=16, max_length=1200)
    currency: str = Field(default="RUB", max_length=8)
    payment_method: str | None = Field(default=None, max_length=16)
    acquisition_handle: str | None = Field(default=None, min_length=32, max_length=160)


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
    supported_plan_codes: list[str] = Field(default_factory=list)


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
    payment_method: str | None = Field(default=None, max_length=16)
    acquisition_handle: str | None = Field(default=None, min_length=32, max_length=160)


class RubPublicOrderCreateIn(BaseModel):
    provider: str = Field(min_length=2, max_length=32)
    plan_code: str = Field(min_length=2, max_length=32)
    checkout_ticket: str | None = Field(default=None, min_length=16, max_length=1200)
    buyer_email: str | None = Field(default=None, min_length=5, max_length=200)
    source: str = Field(default="site", max_length=16)
    campaign: str | None = Field(default=None, max_length=64)
    promo_code: str | None = Field(default=None, max_length=32)
    currency: str = Field(default="RUB", max_length=8)
    payment_method: str | None = Field(default=None, max_length=16)
    acquisition_handle: str | None = Field(default=None, min_length=32, max_length=160)


class Start99EligibilityIn(BaseModel):
    checkout_ticket: str = Field(min_length=16, max_length=1200)


class RubOrderActionOut(FreekassaOrderActionOut):
    provider_label: str | None = None


class AdminPaymentReconcileIn(BaseModel):
    note: str = Field(min_length=8, max_length=1000)
    status: str | None = Field(default=None, min_length=3, max_length=24)


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
    days: int | None = Field(default=None, ge=1, le=365)
    kind: str | None = Field(default=None, min_length=4, max_length=16)
    value: int | None = Field(default=None, ge=1, le=365)
    weight: int = Field(ge=1, le=10000)


class AdminWheelConfigIn(BaseModel):
    preset: str = Field(default="paid_fortnightly_discounts_v3", min_length=2, max_length=32)
    weights: list[AdminWheelWeightIn] = Field(
        default_factory=lambda: [
            AdminWheelWeightIn(**row)
            for row in PAID_FORTNIGHTLY_DISCOUNTS_V3["weights"]
        ],
        min_length=4,
        max_length=7,
    )
    cooldown_hours: int = Field(default=336, ge=168, le=336)


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
    free_profile_state: str = "standard"
    free_profile_active_role: str = "free_standard"
    free_profile_job_id: int | None = None
    free_profile_error_code: str | None = None
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


class ClientAppUpdateInfo(BaseModel):
    platform: str
    channel: str = "beta"
    latest_version: str = ""
    min_supported_version: str = ""
    update_policy: str = "none"
    url: str = ""
    sha256: str = ""
    size: int = 0
    release_notes: str = ""
    release_notes_url: str = ""
    published_at: str = ""
    rollout_percent: int = 100
    force_after: str | None = None


class ClientAndroidApkVariant(BaseModel):
    abi: str
    label: str
    url: str
    sha256: str = ""
    size: int = 0


class ClientAndroidApps(BaseModel):
    play_url: str = ""
    apk_url: str = ""
    mirror_url: str = ""
    apk_variants: list[ClientAndroidApkVariant] = Field(default_factory=list)
    version: str = ""
    sha256: str = ""
    size: int = 0
    release_notes: str = ""
    release_notes_url: str = ""
    published_at: str = ""
    update: ClientAppUpdateInfo


class ClientWindowsApps(BaseModel):
    exe_url: str = ""
    mirror_url: str = ""
    version: str = ""
    sha256: str = ""
    size: int = 0
    release_notes: str = ""
    release_notes_url: str = ""
    published_at: str = ""
    update: ClientAppUpdateInfo


class ClientAppsResponse(BaseModel):
    android: ClientAndroidApps
    windows: ClientWindowsApps
    docs_url: str = ""
    updated_at: str
    update_check: dict[str, Any]


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


class AdminKeyRotateIn(BaseModel):
    reason: str = Field(default="manual_review", max_length=160)
    dry_run: bool = False


class AdminProviderQuotaIn(BaseModel):
    node_code: str = Field(min_length=1, max_length=32)
    included_bytes: int | None = Field(default=None, ge=0)
    included_gb: float | None = Field(default=None, ge=0)
    reset_day: int = Field(default=1, ge=1, le=31)
    timezone: str = Field(default="UTC", min_length=1, max_length=64)
    warning_ratio: float = Field(default=0.80, ge=0.01, le=1.0)
    critical_ratio: float = Field(default=0.95, ge=0.01, le=1.0)
    enabled: bool = True
    notes: str | None = Field(default=None, max_length=1000)


class AdminProviderQuotaPatchIn(BaseModel):
    included_bytes: int | None = Field(default=None, ge=0)
    included_gb: float | None = Field(default=None, ge=0)
    reset_day: int | None = Field(default=None, ge=1, le=31)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    warning_ratio: float | None = Field(default=None, ge=0.01, le=1.0)
    critical_ratio: float | None = Field(default=None, ge=0.01, le=1.0)
    enabled: bool | None = None
    notes: str | None = Field(default=None, max_length=1000)


class AdminAlertSilenceIn(BaseModel):
    minutes: int = Field(default=60, ge=1, le=43200)
    note: str | None = Field(default=None, max_length=300)


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


class AdminServiceIncidentCreateIn(BaseModel):
    incident_key: str = Field(min_length=3, max_length=80)
    title: str = Field(min_length=3, max_length=160)
    summary: str = Field(min_length=3, max_length=600)
    severity: str = Field(default="degraded", min_length=3, max_length=24)
    started_at: str = Field(min_length=10, max_length=64)
    affected_node_codes: list[str] = Field(default_factory=list, max_length=100)
    compensation_days: int = Field(default=0, ge=0, le=30)


class AdminServiceIncidentResolveIn(BaseModel):
    ended_at: str = Field(min_length=10, max_length=64)


class AdminServiceIncidentCompensateIn(BaseModel):
    dry_run: bool = True
    confirm_incident_key: str = Field(default="", max_length=80)


class AdminProgramApplicationReviewIn(BaseModel):
    status: str = Field(min_length=3, max_length=24)
    operator_note: str | None = Field(default=None, max_length=1000)
    reward_days: int = Field(default=0, ge=0, le=7)
    confirm_application_id: str = Field(default="", max_length=36)


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
        return FREE_STANDARD_QUOTA_GB
    return 0


def _plan_device_limit(user: User) -> int:
    plan_code = str(getattr(user, "current_plan_code", "") or "").strip().lower()
    st = (user.sub_type or "").upper()
    if st == "FREE":
        return 1
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
    free_profile_state = str(getattr(user, "free_profile_state", "") or "standard").strip().lower()
    free_profile_active_role = str(
        getattr(user, "free_profile_active_role", "") or "free_standard"
    ).strip().lower()
    free_profile_facts = {
        "free_profile_state": free_profile_state,
        "free_profile_active_role": free_profile_active_role,
        "free_profile_job_id": getattr(user, "free_profile_job_id", None),
        "free_profile_error_code": str(getattr(user, "free_profile_error_code", "") or "").strip() or None,
    }

    if sub_type == "FREE" and free_user_has_bounded_premium_trial(user, now=current_now):
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
            **free_profile_facts,
        }

    if sub_type == "FREE" and not free_tier_enabled():
        return {
            "access_state": "expired_or_blocked",
            "traffic_policy": {
                "kind": "blocked",
                "label": "access_required",
            },
            "traffic_limit_gb": None,
            "traffic_remaining_gb": None,
            "next_reset_at": None,
            "soft_mode_active": False,
            **free_profile_facts,
        }

    if active_window and (
        sub_type.startswith("TRIAL")
        or sub_type.startswith("BONUS")
        or sub_type in {"CHANNEL_BONUS", "OPENING_BONUS", "FRIEND_GIFT"}
    ):
        access_state = "trial_premium" if sub_type.startswith("TRIAL") else "bonus_premium"
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
            **free_profile_facts,
        }

    if sub_type == "FREE":
        limit_gb = float(FREE_STANDARD_QUOTA_BYTES) / float(1024**3)
        remaining_gb = max(round(limit_gb - used_gb, 3), 0.0) if limit_gb > 0 else 0.0
        soft_mode_active = bool(
            free_profile_active_role == "free_soft"
            and free_profile_state in {"soft_active", "reset_pending", "error"}
        )
        if soft_mode_active:
            remaining_gb = 0.0
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
            **free_profile_facts,
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
        **free_profile_facts,
    }


def _build_reconciled_access_policy(
    *,
    session,
    user: User,
    used_bytes: int,
    source: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = now or _utcnow()
    if free_tier_enabled() and str(getattr(user, "sub_type", "") or "").strip().upper() == "FREE":
        reconcile_free_profile_usage_in_new_transaction(
            tg_id=int(user.tg_id),
            used_bytes=max(0, int(used_bytes or 0)),
            source=source,
            now=current,
            session_factory=SessionLocal,
        )
        session.refresh(user)
    return _build_access_policy(user=user, used_bytes=used_bytes, now=current)


def _maybe_downgrade_expired_to_free(s, user: User) -> bool:
    """
    If a paid plan expires, optionally keep the user in FREE mode automatically.

    Rules:
    - Only when AUTO_DOWNGRADE_TO_FREE=true
    - Only if user is currently active (do not auto-unban manually disabled users)
    - Only when expiry_at has passed
    """
    try:
        if not free_tier_enabled() or not AUTO_DOWNGRADE_TO_FREE:
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

        user.expiry_at = _utcnow() + timedelta(days=int(AUTO_FREE_DAYS))
        queue_free_profile_reentry(s, user=user, source="api_expired_to_free")
        s.commit()
        return True
    except Exception:
        return False

app = FastAPI(title="POKROV API", version="2.0.0")


_AUTH_ERROR_HEADER = "X-POKROV-Auth-Error"
_AUTH_ERROR_CODE_RE = re.compile(r"^[a-z0-9_]{1,64}$")
_AUTH_ERROR_FALLBACK_CODES = {
    400: "bad_request",
    401: "auth_required",
    403: "forbidden",
    404: "resource_not_found",
    409: "conflict",
    422: "request_invalid",
    429: "rate_limited",
}


def _has_explicit_auth_error_header(headers: dict[str, str] | None) -> bool:
    return any(
        str(name).lower() == _AUTH_ERROR_HEADER.lower()
        for name in (headers or {})
    )


def _safe_auth_error_code(detail: Any) -> str | None:
    if not isinstance(detail, dict):
        return None
    raw_code = detail.get("code")
    if not isinstance(raw_code, str):
        return None
    code = raw_code.strip().lower()
    return code if _AUTH_ERROR_CODE_RE.fullmatch(code) else None


def _fallback_auth_error_code(status_code: int) -> str:
    if int(status_code) >= 500:
        return "service_unavailable"
    return _AUTH_ERROR_FALLBACK_CODES.get(int(status_code), "request_failed")


@app.exception_handler(StarletteHTTPException)
async def add_auth_error_header(
    request: Request,
    exc: StarletteHTTPException,
) -> Response:
    """Add one safe machine-readable code without changing FastAPI's error body."""
    response = await http_exception_handler(request, exc)
    if _has_explicit_auth_error_header(exc.headers):
        return response
    response.headers[_AUTH_ERROR_HEADER] = (
        _safe_auth_error_code(exc.detail)
        or _fallback_auth_error_code(exc.status_code)
    )
    return response


@app.exception_handler(RequestValidationError)
async def add_validation_error_header(
    request: Request,
    exc: RequestValidationError,
) -> Response:
    """Keep FastAPI's standard 422 response while adding its stable header."""
    response = await request_validation_exception_handler(request, exc)
    response.headers[_AUTH_ERROR_HEADER] = "request_invalid"
    return response


@app.middleware("http")
async def bind_current_request(request: Request, call_next):
    token = _current_request_ctx.set(request)
    try:
        return await call_next(request)
    finally:
        _current_request_ctx.reset(token)


app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[_AUTH_ERROR_HEADER],
)
SUPPORT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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
        try:
            auth_date = int(parsed.get("auth_date") or 0)
        except Exception:
            return None
        if auth_date <= 0:
            return None
        now = int(time.time())
        max_age = max(60, int(TELEGRAM_WEB_LOGIN_MAX_AGE_SECONDS))
        if auth_date > now + 300 or now - auth_date > max_age:
            return None

        data_check_arr = sorted([f"{k}={v}" for k, v in parsed.items()])
        data_check_string = "\n".join(data_check_arr)

        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(calculated_hash, check_hash):
            return None
        return json.loads(parsed.get("user", "{}"))
    except Exception:
        return None


def _safe_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    # PostgreSQL returns several legacy UTC columns as naive datetimes.  A
    # timezone-less API value is interpreted in the device's local timezone,
    # which made fresh node measurements look hours old outside UTC.
    normalized = dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
    return normalized.astimezone(timezone.utc).isoformat()


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


def _has_successful_provider_payment(*, s, user: User) -> bool:
    account_id = str(getattr(user, "account_id", "") or "").strip()
    if account_id and (
        s.query(EntitlementGrant.id)
        .filter(
            EntitlementGrant.account_id == account_id,
            EntitlementGrant.source == "provider_payment",
            EntitlementGrant.status.in_(["active", "recorded", "expired"]),
        )
        .first()
    ):
        return True
    tg_id = int(getattr(user, "tg_id", 0) or 0)
    if tg_id <= 0:
        return False
    row = (
        s.query(ExternalOrder.id)
        .filter(ExternalOrder.tg_id == int(tg_id))
        .filter(func.lower(func.coalesce(ExternalOrder.status, "")) == "paid")
        .first()
    )
    return bool(row)


def _ensure_start99_available_for_user(*, s, user: User | None, plan_code: str) -> None:
    if (plan_code or "").strip().lower() != "start_99":
        return
    if user and _has_successful_provider_payment(s=s, user=user):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "start_99_already_used",
                "message": "Приветственный месяц уже использован.",
                "replacement_plan": "1_month",
            },
        )


def _has_successful_provider_payment_for_email(*, s, buyer_email_norm: str) -> bool:
    email = str(buyer_email_norm or "").strip().lower()
    if not email:
        return False
    row = (
        s.query(PaymentEntitlementClaim.id)
        .filter(func.lower(PaymentEntitlementClaim.buyer_email_norm) == email)
        .filter(PaymentEntitlementClaim.paid_at.isnot(None))
        .filter(func.lower(func.coalesce(PaymentEntitlementClaim.status, "")) != "reversed")
        .first()
    )
    return bool(row)


def _ensure_start99_available_for_order(
    *,
    s,
    user: User | None,
    buyer_email_norm: str,
    plan_code: str,
) -> None:
    _ensure_start99_available_for_user(s=s, user=user, plan_code=plan_code)
    if (plan_code or "").strip().lower() != "start_99":
        return
    if _has_successful_provider_payment_for_email(s=s, buyer_email_norm=buyer_email_norm):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "start_99_already_used",
                "message": "Приветственный месяц уже использован.",
                "replacement_plan": "1_month",
            },
        )


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


def _access_key_safe_meta(code: str) -> dict[str, Any]:
    normalized = str(code or "").strip().upper()
    if not normalized:
        return {}
    return {
        "code_preview": f"...{normalized[-4:]}",
        "code_fp": hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16],
        "code_len": len(normalized),
    }


def _looks_like_subscription_or_proxy_link(value: str) -> bool:
    raw = str(value or "").strip()
    if not raw:
        return False
    parsed = urlparse(raw)
    if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
        host = (parsed.hostname or "").lower().strip()
        path = (parsed.path or "").lower()
        if host.endswith("connect.pokrov.space") or "/sub" in path or "subscription" in path:
            return True
        return True
    return parsed.scheme.lower() in {"vless", "vmess", "trojan", "ss", "hysteria2", "tuic"}


def _access_key_status_payload(*, s, card: GiftCard) -> dict[str, Any]:
    meta = _access_key_meta_from_card_type(s=s, card_type=str(card.card_type or ""))
    payment_claim = (
        s.query(PaymentEntitlementClaim)
        .filter(PaymentEntitlementClaim.fallback_gift_card_id == int(card.id))
        .one_or_none()
    )
    if payment_claim is not None:
        plan_code = str(payment_claim.plan_code or "").strip().lower()
        current_plan = dict((meta or {}).get("plan") or {})
        current_plan["code"] = plan_code
        meta = {
            **(meta or {}),
            "kind": "plan",
            "plan": current_plan,
            "days": max(1, int(payment_claim.duration_days or 0)),
            "legacy_type": None,
        }
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


def _is_legacy_gift_card_for_unified_redeem(*, card: GiftCard | None, meta: dict[str, Any] | None) -> bool:
    if not card or not meta:
        return False
    if str(meta.get("kind") or "").strip() != "legacy_gift":
        return False
    return int(getattr(card, "created_by", 0) or 0) != 0


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
    email_identity = _verified_email_identity_for_account_family(s, user=user)
    telegram_id = _linked_telegram_id(user) or (0 if _is_app_or_email_account(user) else int(user.tg_id))
    telegram_username = (
        str(getattr(user, "linked_telegram_username", "") or "").strip()
        or (str(getattr(user, "username", "") or "").strip() if telegram_id and not _is_app_or_email_account(user) else "")
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
    free_enabled = bool(_FREE_TIER_FACTS.get("enabled", False)) and free_tier_enabled()
    return {
        "enabled": free_enabled,
        "status": str(_FREE_TIER_FACTS.get("status") or "retired_pending_replacement"),
        "plan_code": str(_FREE_TIER_FACTS.get("plan_code") or "free_monthly"),
        "location_code": str(_FREE_TIER_FACTS.get("location_code") or "NL-free") if free_enabled else None,
        "traffic_limit_gb": int(_FREE_TIER_FACTS.get("traffic_limit_gb") or 5),
        "cycle_days": int(_FREE_TIER_FACTS.get("cycle_days") or 30),
        "speed_limit_mbps": int(_FREE_TIER_FACTS.get("speed_limit_mbps") or 50),
        "soft_mode_speed_limit_mbps": int(_FREE_TIER_FACTS.get("soft_mode_speed_limit_mbps") or 2),
        "device_limit": int(_FREE_TIER_FACTS.get("device_limit") or 1),
        "monthly_reset": free_enabled and bool(_FREE_TIER_FACTS.get("monthly_reset", True)),
        "active": free_enabled and free_active,
        "next_reset_at": access_policy.get("next_reset_at"),
        "transition_state": str(access_policy.get("free_profile_state") or "standard"),
        "active_role": str(access_policy.get("free_profile_active_role") or "free_standard"),
        "provisioning_job_id": access_policy.get("free_profile_job_id"),
        "error_code": access_policy.get("free_profile_error_code"),
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


def _node_supports_transport_profile(node: Any, transport_profile: str | None) -> bool:
    requested = str(transport_profile or LEGACY_REALITY_FALLBACK).strip() or LEGACY_REALITY_FALLBACK
    profile = transport_profile_by_name(
        node,
        requested,
        include_disabled=False,
        allow_operator_lab=True,
    )
    return str(profile.get("name") or "") == requested and bool(profile.get("enabled"))


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

    def safe_promo_url(raw_url: Any, *, field: str) -> str | None:
        url = str(raw_url or "").strip()
        if not url:
            return None
        parsed = urlparse(url)
        if parsed.scheme not in {"https", "tg"}:
            if strict:
                raise HTTPException(status_code=400, detail=f"Promo {field} must use https:// or tg://")
            return None
        if parsed.scheme == "https" and not parsed.netloc:
            if strict:
                raise HTTPException(status_code=400, detail=f"Promo {field} must include a host")
            return None
        return url[:600]

    def safe_schedule(raw_dt: Any, *, field: str) -> str | None:
        value = str(raw_dt or "").strip()
        if not value:
            return None
        try:
            _parse_optional_datetime(value)
        except HTTPException:
            if strict:
                raise HTTPException(status_code=400, detail=f"Promo {field} must be an ISO datetime")
            return None
        return value[:64]

    def safe_color(raw_color: Any, *, field: str) -> str | None:
        value = str(raw_color or "").strip().upper()
        if not value:
            return None
        if not re.fullmatch(r"#[0-9A-F]{6}", value):
            if strict:
                raise HTTPException(status_code=400, detail=f"Promo {field} must use #RRGGBB")
            return None
        return value

    image_layout = str(raw.get("image_layout") or "logo").strip().lower()
    if image_layout not in {"logo", "banner"}:
        if strict:
            raise HTTPException(status_code=400, detail="Promo image_layout must be logo or banner")
        image_layout = "logo"

    return {
        "slot_id": slot_id,
        "content_id": content_id,
        "enabled": bool(raw.get("enabled", True)),
        "title": str(raw.get("title") or "").strip()[:160] or None,
        "body": str(raw.get("body") or "").strip()[:500] or None,
        "badge_label": str(raw.get("badge_label") or "").strip()[:48] or None,
        "image_url": safe_promo_url(raw.get("image_url"), field="image_url"),
        "image_layout": image_layout,
        "cta_label": str(raw.get("cta_label") or "").strip()[:80] or None,
        "cta_href": safe_promo_url(raw.get("cta_href"), field="cta_href"),
        "accent_color": safe_color(raw.get("accent_color"), field="accent_color"),
        "background_color": safe_color(raw.get("background_color"), field="background_color"),
        "text_color": safe_color(raw.get("text_color"), field="text_color"),
        "button_color": safe_color(raw.get("button_color"), field="button_color"),
        "button_text_color": safe_color(raw.get("button_text_color"), field="button_text_color"),
        "placement": str(raw.get("placement") or slot_facts.get("placement") or "").strip()[:64] or None,
        "dismissible": bool(raw.get("dismissible", True)),
        "whole_card_clickable": bool(raw.get("whole_card_clickable", True)),
        "starts_at": safe_schedule(raw.get("starts_at"), field="starts_at"),
        "ends_at": safe_schedule(raw.get("ends_at"), field="ends_at"),
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
    now = _utcnow()
    for assignment in list(normalized.get("assignments") or []):
        starts_at = _parse_optional_datetime(assignment.get("starts_at"))
        ends_at = _parse_optional_datetime(assignment.get("ends_at"))
        if starts_at and starts_at > now:
            continue
        if ends_at and ends_at <= now:
            continue
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
                "badge_label": assignment.get("badge_label"),
                "image_url": assignment.get("image_url"),
                "image_layout": assignment.get("image_layout"),
                "cta_label": assignment.get("cta_label"),
                "cta_href": assignment.get("cta_href"),
                "accent_color": assignment.get("accent_color"),
                "background_color": assignment.get("background_color"),
                "text_color": assignment.get("text_color"),
                "button_color": assignment.get("button_color"),
                "button_text_color": assignment.get("button_text_color"),
                "placement": assignment.get("placement") or str(slot_facts.get("placement") or "").strip() or None,
                "dismissible": bool(assignment.get("dismissible", True)),
                "whole_card_clickable": bool(assignment.get("whole_card_clickable", True)),
                "starts_at": assignment.get("starts_at"),
                "ends_at": assignment.get("ends_at"),
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


def _checkout_discount_code_preview_pct(*, s, promo_code: str | None) -> tuple[int, str, str]:
    code = str(promo_code or "").strip().upper()[:20]
    if not code:
        return 0, "", ""

    promo = s.query(PromoCode).filter(func.upper(PromoCode.code) == code).first()
    if promo:
        promo_type = str(getattr(promo, "promo_type", "") or "").strip().lower()
        value = int(getattr(promo, "value", 0) or 0)
        uses_left = int(getattr(promo, "uses_left", 0) or 0)
        expires_at = getattr(promo, "expires_at", None)
        if (
            promo_type == "discount"
            and value > 0
            and uses_left != 0
            and (not expires_at or expires_at >= _utcnow())
        ):
            return max(1, min(95, value)), str(getattr(promo, "code", code) or code).strip().upper()[:20], "promo_code"
        return 0, str(getattr(promo, "code", code) or code).strip().upper()[:20], "promo_code_unavailable"

    preview_codes = ((_TARIFF_CATALOG.get("pricing_preview") or {}).get("discount_codes") or {})
    try:
        preview_pct = int(preview_codes.get(code) or 0)
    except Exception:
        preview_pct = 0
    if preview_pct > 0:
        return max(1, min(95, preview_pct)), code, "catalog_preview"
    return 0, code, ""


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
    if request is None or request.client is None:
        return False
    if not _is_loopback_ip(request.client.host):
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
        request = _current_request_ctx.get()
    if request is None:
        return ""
    auth_header = str(request.headers.get("authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    header_token = str(request.headers.get("x-web-auth-token") or "").strip()
    if header_token:
        return header_token
    cookie_token = str(request.cookies.get(WEB_SESSION_COOKIE_NAME) or "").strip()
    if cookie_token:
        return cookie_token
    # Compatibility cookie used by the static cabinet before HttpOnly handoff.
    return str(request.cookies.get("portal_web_session_token") or "").strip()


def _auth_http_exception(*, detail: str, code: str, status_code: int = 401) -> HTTPException:
    return HTTPException(status_code=status_code, detail=detail, headers={"X-POKROV-Auth-Error": code})


def _auth_session_http_exception(exc: auth_session_service.AuthSessionError) -> HTTPException:
    status_by_code = {
        "device_recovery_required": 409,
        "fresh_auth_required": 409,
        "device_not_found": 404,
        "session_not_configured": 500,
    }
    detail_by_code = {
        "device_recovery_required": "Устройство уже зарегистрировано. Обновите сессию или восстановите доступ.",
        "fresh_auth_required": "Для отзыва устройства подтвердите вход ещё раз.",
        "device_not_found": "Устройство не найдено.",
        "refresh_token_invalid": "Refresh-токен не подтвердился.",
        "refresh_reuse_detected": "Refresh-токен уже использован. Все сессии этой семьи отозваны.",
        "refresh_expired": "Refresh-сессия истекла. Восстановите доступ.",
        "session_revoked": "Сессия отозвана.",
        "access_expired": "Access-сессия истекла.",
        "device_revoked": "Устройство отозвано.",
        "device_credential_changed": "Учётные данные устройства изменились.",
        "session_epoch_changed": "Сессии аккаунта были обновлены. Войдите снова.",
        "session_not_configured": "Сервис сессий не настроен.",
    }
    code = str(exc.code or "session_invalid")
    return _auth_http_exception(
        detail=detail_by_code.get(code, "Не удалось подтвердить сессию устройства."),
        code=code,
        status_code=int(status_by_code.get(code, 401)),
    )


def _account_recovery_http_exception(exc: AccountRecoveryError) -> HTTPException:
    status_by_code = {
        "email_otp_invalid": 401,
        "email_otp_expired": 401,
        "email_otp_not_configured": 503,
        "fresh_auth_required": 409,
        "device_identity_conflict": 409,
        "device_limit_reached": 409,
        "recovery_code_invalid": 401,
        "recovery_session_invalid": 401,
        "recovery_not_configured": 503,
        "account_unavailable": 409,
        "reissue_mode_invalid": 400,
    }
    detail_by_code = {
        "email_otp_invalid": "Код не подтвердился или уже использован.",
        "email_otp_expired": "Код истёк. Запросите новый.",
        "email_otp_not_configured": "Email OTP пока не настроен.",
        "fresh_auth_required": "Сначала подтвердите вход одноразовым кодом.",
        "device_identity_conflict": "Это устройство уже связано с другим аккаунтом.",
        "device_limit_reached": "Достигнут лимит устройств. Отзовите старое устройство или используйте lockdown.",
        "recovery_code_invalid": "Код восстановления не подтвердился или уже использован.",
        "recovery_session_invalid": "Recovery-сессия истекла или уже использована.",
        "recovery_not_configured": "Контур восстановления пока не настроен.",
        "account_unavailable": "Аккаунт недоступен для восстановления.",
        "reissue_mode_invalid": "Неизвестный режим перевыпуска доступа.",
    }
    code = str(exc.code or "account_recovery_failed")
    return _auth_http_exception(
        detail=detail_by_code.get(code, "Не удалось подтвердить восстановление доступа."),
        code=code,
        status_code=int(status_by_code.get(code, 401)),
    )


_RECOVERY_SCOPE_ROUTE_ALLOWLIST = frozenset(
    {
        ("GET", "/api/auth/session"),
        ("POST", "/api/client/session/revoke"),
        ("POST", "/api/client/access/reissue"),
        ("GET", "/api/client/devices"),
        ("DELETE", "/api/client/devices/{device_id}"),
        ("GET", "/api/tickets"),
        ("POST", "/api/tickets"),
        ("GET", "/api/tickets/{ticket_id}"),
        ("POST", "/api/tickets/{ticket_id}/messages"),
    }
)


def _recovery_scope_request_allowed(request: Request | None) -> bool:
    if request is None:
        return False
    method = str(getattr(request, "method", "") or "").upper()
    route = (getattr(request, "scope", None) or {}).get("route")
    route_path = str(getattr(route, "path", "") or "")
    if not method or not route_path:
        return False
    return (method, route_path) in _RECOVERY_SCOPE_ROUTE_ALLOWLIST


def _optional_auth_user(x_telegram_init_data: str, request: Request | None = None) -> dict[str, Any] | None:
    init_data = (x_telegram_init_data or "").strip()
    web_token = _extract_web_session_token(request)
    if web_token:
        payload, reason = inspect_web_session_token(web_token)
        if payload:
            if str(payload.get("purpose") or "").strip() == "cabinet_handoff":
                raise _auth_http_exception(
                    detail="Этот короткий переход нужно обменять в кабинете перед использованием.",
                    code="web_session_exchange_required",
                )
            if str(payload.get("session_id") or "").strip():
                auth_session = SessionLocal()
                try:
                    payload = auth_session_service.validate_access_session(
                        auth_session,
                        payload=payload,
                        now=_utcnow(),
                    )
                except auth_session_service.AuthSessionError as exc:
                    raise _auth_session_http_exception(exc) from exc
                finally:
                    auth_session.close()
                if str(payload.get("scope") or "").strip() == "recovery" and not _recovery_scope_request_allowed(request):
                    raise _auth_http_exception(
                        detail="Recovery-сессия не открывает этот раздел. Сначала перевыпустите доступ.",
                        code="recovery_scope_forbidden",
                        status_code=403,
                    )
            return payload
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
        if reason == "expired":
            raise _auth_http_exception(
                detail="Сессия в браузере устарела. Обновите вход через Telegram или email, и кабинет откроется снова.",
                code="web_session_expired",
            )
        raise _auth_http_exception(
            detail="Не удалось подтвердить сессию в браузере. Повторите вход через Telegram или email.",
            code="web_session_invalid",
        )

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
        raise _auth_http_exception(
            detail="Сессия Telegram устарела или не подтвердилась. Откройте вход заново, и мы вернем вас в кабинет.",
            code="telegram_init_invalid",
        )

    dev = _dev_auth_user(request)
    if dev:
        return {
            "id": int(dev.get("id", 0)),
            "username": dev.get("username"),
            "auth_type": "dev",
            "auth_origin": "dev",
            "email": None,
        }
    return None


def _client_peer_host(request: Request | None) -> str:
    if request is None:
        request = _current_request_ctx.get()
    if request is None:
        return ""
    client = getattr(request, "client", None)
    host = getattr(client, "host", "") if client else ""
    return str(host or "").strip()[:64]


def _is_trusted_proxy_host(host: str) -> bool:
    raw_host = str(host or "").strip()
    if not raw_host:
        return False
    if raw_host == "testclient":
        return True
    try:
        ip_obj = ipaddress.ip_address(raw_host)
    except Exception:
        return False
    if ip_obj.is_loopback:
        return True
    raw_allowlist = os.getenv("TRUSTED_PROXY_IPS") or ""
    for raw in raw_allowlist.split(","):
        token = raw.strip()
        if not token:
            continue
        try:
            if "/" in token and ip_obj in ipaddress.ip_network(token, strict=False):
                return True
            if "/" not in token and ip_obj == ipaddress.ip_address(token):
                return True
        except Exception:
            continue
    return False


def _first_valid_ip_from_header(raw: str) -> str:
    for part in str(raw or "").split(","):
        candidate = part.strip()
        if not candidate:
            continue
        try:
            ipaddress.ip_address(candidate)
            return candidate[:64]
        except Exception:
            continue
    return ""


def _request_client_ip(request: Request | None) -> str:
    if request is None:
        request = _current_request_ctx.get()
    if request is None:
        return ""
    peer_host = _client_peer_host(request)
    if _is_trusted_proxy_host(peer_host):
        for header in ("cf-connecting-ip", "x-real-ip", "x-forwarded-for"):
            raw = str(request.headers.get(header) or "").strip()
            if not raw:
                continue
            parsed = _first_valid_ip_from_header(raw)
            if parsed:
                return parsed
    try:
        ipaddress.ip_address(peer_host)
        return peer_host[:64]
    except Exception:
        return peer_host[:64] or "unknown"


def _record_security_event(
    event_type: str,
    *,
    scope: str | None = None,
    fingerprint: str | None = None,
    client_ip: str | None = None,
    subject: str | None = None,
    reason: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    safe_meta = {}
    for key, value in dict(meta or {}).items():
        key_text = str(key or "").strip()[:64]
        if not key_text:
            continue
        if any(token in key_text.lower() for token in ("token", "secret", "password", "authorization", "api_key")):
            safe_meta[key_text] = "[redacted]"
        else:
            safe_meta[key_text] = str(value)[:240] if value is not None else None
    s = SessionLocal()
    try:
        occurred_at = _utcnow()
        s.add(
            SecurityEvent(
                event_type=str(event_type or "").strip()[:64] or "security_event",
                scope=str(scope or "").strip()[:64] or None,
                fingerprint=str(fingerprint or "").strip()[:64] or None,
                client_ip=str(client_ip or "").strip()[:64] or None,
                subject=str(subject or "").strip()[:160] or None,
                reason=str(reason or "").strip()[:160] or None,
                meta_json=json.dumps(safe_meta, ensure_ascii=False, separators=(",", ":"))[:2000] if safe_meta else None,
                created_at=occurred_at,
            )
        )
        record_antiabuse_event(
            s,
            event_kind=event_type,
            source="api_security",
            occurred_at=occurred_at,
            raw_ip=client_ip,
            reasons=[reason] if reason else None,
            metadata={"scope": scope, **safe_meta},
        )
        s.commit()
    except Exception:
        s.rollback()
    finally:
        s.close()


def _rate_limit_exception(scope: str, retry_after: int) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail={
            "code": "rate_limited",
            "message": "Too many requests. Please retry later.",
            "scope": str(scope or "").strip().lower(),
            "retry_after_seconds": int(retry_after),
        },
        headers={"Retry-After": str(int(retry_after))},
    )


def _rate_limit_window_start(now_ts: float, window_seconds: int) -> datetime:
    start_ts = int(now_ts) - (int(now_ts) % max(1, int(window_seconds)))
    return datetime.fromtimestamp(start_ts, timezone.utc).replace(tzinfo=None)


def _memory_rate_limit(scope: str, fingerprint: str, *, limit: int, window_seconds: int, now_ts: float) -> None:
    key = (str(scope or "").strip().lower(), str(fingerprint or "").strip())
    hits = [ts for ts in _beta_rate_limit_state.get(key, []) if now_ts - ts < float(window_seconds)]
    if len(hits) >= int(limit):
        retry_after = max(1, int(float(window_seconds) - (now_ts - hits[0])) + 1)
        _beta_rate_limit_state[key] = hits
        raise _rate_limit_exception(scope, retry_after)
    hits.append(now_ts)
    _beta_rate_limit_state[key] = hits


def _enforce_durable_rate_limit(scope: str, fingerprint: str, *, limit: int, window_seconds: int = 60) -> None:
    now_ts = time.time()
    now_dt = datetime.fromtimestamp(now_ts, timezone.utc).replace(tzinfo=None)
    window_start = _rate_limit_window_start(now_ts, window_seconds)
    expires_at = window_start + timedelta(seconds=max(1, int(window_seconds)))
    bucket_key = hashlib.sha256(
        f"{str(scope).lower()}|{str(fingerprint)}|{window_start.isoformat()}".encode("utf-8")
    ).hexdigest()
    s = SessionLocal()
    try:
        if secrets.randbelow(100) == 0:
            s.query(SecurityRateLimitBucket).filter(SecurityRateLimitBucket.expires_at < now_dt - timedelta(minutes=5)).delete()
        bucket = (
            s.query(SecurityRateLimitBucket)
            .filter(SecurityRateLimitBucket.bucket_key == bucket_key)
            .with_for_update()
            .first()
        )
        if bucket is None:
            bucket = SecurityRateLimitBucket(
                bucket_key=bucket_key,
                scope=str(scope or "").strip().lower()[:64],
                fingerprint=str(fingerprint or "").strip()[:64],
                window_start=window_start,
                expires_at=expires_at,
                hits=0,
                updated_at=now_dt,
            )
            s.add(bucket)
            try:
                s.flush()
            except IntegrityError:
                s.rollback()
                bucket = (
                    s.query(SecurityRateLimitBucket)
                    .filter(SecurityRateLimitBucket.bucket_key == bucket_key)
                    .with_for_update()
                    .first()
                )
                if bucket is None:
                    _memory_rate_limit(scope, fingerprint, limit=limit, window_seconds=window_seconds, now_ts=now_ts)
                    return
        current_hits = int(bucket.hits or 0)
        if current_hits >= int(limit):
            retry_after = max(1, int((expires_at - now_dt).total_seconds()) + 1)
            s.rollback()
            raise _rate_limit_exception(scope, retry_after)
        bucket.hits = current_hits + 1
        bucket.updated_at = now_dt
        s.commit()
    except HTTPException:
        raise
    except Exception:
        s.rollback()
        _memory_rate_limit(scope, fingerprint, limit=limit, window_seconds=window_seconds, now_ts=now_ts)
    finally:
        s.close()


_BETA_RATE_LIMIT_DEFAULTS_PER_MINUTE = {
    "start_trial": 12,
    "session_refresh": 10,
    "session_refresh_ip": 600,
    "access_key_status": 60,
    "access_key_redeem": 20,
    "unified_redeem": 20,
    "cabinet_token": 10,
    "cabinet_handoff_exchange": 30,
    "telegram_auth": 30,
    "email_auth": 20,
    "email_otp_start": 5,
    "email_otp_start_ip": 20,
    "email_otp_finish": 8,
    "email_otp_finish_ip": 30,
    "email_otp_finish_install": 8,
    "recovery_exchange": 5,
    "recovery_exchange_ip": 30,
    "recovery_exchange_install": 5,
    "recovery_rotate": 5,
    "access_reissue": 5,
    "device_pairing_issue": 6,
    "device_pairing_claim": 8,
    "device_pairing_claim_ip": 30,
    "program_application": 6,
    "ticket_create": 20,
    "ticket_upload": 30,
    "ticket_attachment_download": 120,
    "payment_callback": 120,
    "payment_callback_invalid": 20,
    "public_order_create": 30,
    "subscription_fetch": 180,
    "subscription_fetch_ip": 240,
    "events": 180,
    "admin_destructive": 30,
}
_beta_rate_limit_state: dict[tuple[str, str], list[float]] = {}


def _beta_rate_limit_per_minute(scope: str) -> int:
    normalized = str(scope or "").strip().upper().replace("-", "_")
    default = int(_BETA_RATE_LIMIT_DEFAULTS_PER_MINUTE.get(str(scope or "").strip().lower(), 0) or 0)
    return max(0, env_int(f"API_RATE_LIMIT_{normalized}_PER_MINUTE", default))


def _beta_rate_limit_fingerprint(scope: str, request: Request | None, *, identity: str | None = None) -> str:
    client_ip = _request_client_ip(request) or "unknown"
    subject = f"{client_ip}|{str(identity or '').strip()}"
    return hashlib.sha256(f"{scope}|{subject}".encode("utf-8")).hexdigest()[:32]


def _enforce_beta_rate_limit(scope: str, request: Request | None, *, identity: str | None = None) -> None:
    normalized_scope = str(scope or "").strip().lower()
    limit = _beta_rate_limit_per_minute(normalized_scope)
    if limit <= 0:
        return
    fingerprint = _beta_rate_limit_fingerprint(normalized_scope, request, identity=identity)
    try:
        _enforce_durable_rate_limit(normalized_scope, fingerprint, limit=limit, window_seconds=60)
    except HTTPException as exc:
        _record_security_event(
            "rate_limit_hit",
            scope=normalized_scope,
            fingerprint=fingerprint,
            client_ip=_request_client_ip(request),
            subject=str(identity or "")[:160] or None,
            reason="limit_exceeded",
        )
        raise exc


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


def _is_synthetic_email_account_id(tg_id: int | str | None) -> bool:
    try:
        value = int(tg_id or 0)
    except Exception:
        return False
    return int(WEB_EMAIL_ACCOUNT_TG_ID_BASE) <= value < int(APP_ACCOUNT_TG_ID_BASE)


def _is_app_or_email_account(user: User | None) -> bool:
    if not user:
        return False
    return bool(getattr(user, "is_app_user", False)) or _is_synthetic_email_account_id(getattr(user, "tg_id", 0))


def _linked_account_for_telegram(s, *, telegram_id: int) -> User | None:
    tg_id = int(telegram_id or 0)
    if tg_id <= 0:
        return None
    return (
        s.query(User)
        .filter(User.linked_telegram_id == tg_id)
        .order_by(User.linked_telegram_linked_at.desc(), User.created_at.desc(), User.tg_id.desc())
        .first()
    )


def _verified_email_identity_for_account_family(s, *, user: User | None) -> WebEmailIdentity | None:
    if not user:
        return None
    direct = get_verified_identity_for_user(s, tg_id=int(user.tg_id))
    if direct:
        return direct
    if _is_app_or_email_account(user):
        return None
    linked_account = _linked_account_for_telegram(s, telegram_id=int(getattr(user, "tg_id", 0) or 0))
    if not linked_account or int(getattr(linked_account, "tg_id", 0) or 0) == int(user.tg_id):
        return None
    return get_verified_identity_for_user(s, tg_id=int(linked_account.tg_id))


def _require_email_public_ready() -> dict[str, Any]:
    status = email_delivery_runtime_status()
    if bool(status.get("enabled")):
        return status
    reasons = ", ".join(str(item) for item in (status.get("blocked_reasons") or []) if item) or "not_ready"
    raise HTTPException(
        status_code=503,
        detail=f"Email-вход пока недоступен: доставка писем не готова ({reasons}).",
    )


def _ensure_user_row_for_login(
    *,
    tg_id: int,
    username: str | None = None,
    include_legacy_payment_authority: bool = True,
) -> None:
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if user:
            normalized = str(username or "").strip()[:100] or None
            if username is not None and user.username != normalized:
                user.username = normalized
            ensure_user_account_foundation(
                s,
                user,
                now=_utcnow(),
                include_legacy_payment_authority=include_legacy_payment_authority,
            )
            s.commit()
            return

        now = _utcnow()
        sub_token = secrets.token_urlsafe(32)
        free_enabled = free_tier_enabled()
        row = User(
            tg_id=int(tg_id),
            username=(str(username).strip()[:100] if username else None),
            uuid=str(uuid.uuid4()),
            email=f"User_{int(tg_id)}",
            sub_type="FREE",
            current_plan_code="free_monthly" if free_enabled else "free_retired",
            created_at=now,
            expiry_at=now + timedelta(days=max(3650, int(AUTO_FREE_DAYS))) if free_enabled else now,
            is_active=True,
            stars_paid=0,
            total_gb=0,
            trial_used=False,
            tos_accepted=False,
            sub_token=sub_token,
        )
        if free_enabled:
            mark_user_became_free(row, now=now)
        else:
            project_user_to_expired(row, now=now, source="account_created_without_free")
        s.add(row)
        ensure_user_account_foundation(
            s,
            row,
            now=now,
            include_legacy_payment_authority=include_legacy_payment_authority,
        )
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
    is_signed_integer = q_norm.isdigit() or (q_norm.startswith("-") and q_norm[1:].isdigit())
    if is_signed_integer and int(q_norm) != 0:
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
        "app_device_name": getattr(user, "app_device_name", None),
        "app_platform": getattr(user, "app_platform", None),
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


def _auth_actor_tg_id(auth_user: dict[str, Any] | None) -> int:
    if not auth_user:
        return 0
    direct_id = int((auth_user or {}).get("actor_tg_id") or (auth_user or {}).get("telegram_id") or 0)
    if direct_id > 0:
        return direct_id
    return int((auth_user or {}).get("id") or 0)


def _auth_user_is_recovery_scope(auth_user: dict[str, Any] | None) -> bool:
    return str((auth_user or {}).get("scope") or "").strip() == "recovery"


def _reject_recovery_ticket_media(*, auth_user: dict[str, Any] | None, payload: Any) -> None:
    if not _auth_user_is_recovery_scope(auth_user):
        return
    media_values = (
        getattr(payload, "attachment_id", None),
        getattr(payload, "media_type", None),
        getattr(payload, "media_file_id", None),
        getattr(payload, "media_payload", None),
    )
    if any(value is not None and str(value) != "" for value in media_values):
        raise _auth_http_exception(
            detail="Recovery-сессия поддерживает только текстовые обращения.",
            code="recovery_scope_forbidden",
            status_code=403,
        )


def _auth_user_can_admin_account(*, auth_user: dict[str, Any] | None, user: User | None) -> bool:
    if _auth_user_is_recovery_scope(auth_user):
        return False
    candidates = [
        int((auth_user or {}).get("id") or 0),
        _auth_actor_tg_id(auth_user),
        int(getattr(user, "tg_id", 0) or 0) if user else 0,
    ]
    return any(_is_admin_tg(candidate) for candidate in candidates if candidate)


def _require_admin(x_telegram_init_data: str, request: Request | None = None) -> dict[str, Any]:
    user_data = _require_auth_user(x_telegram_init_data, request=request)
    if _auth_user_is_recovery_scope(user_data):
        raise _auth_http_exception(
            detail="Recovery-сессия не даёт административных прав.",
            code="recovery_scope_forbidden",
            status_code=403,
        )
    account_id = int(user_data.get("id", 0))
    actor_id = _auth_actor_tg_id(user_data)
    if not _is_admin_tg(actor_id):
        _record_security_event(
            "admin_access_denied",
            scope="admin",
            client_ip=_request_client_ip(request),
            subject=f"tg:{actor_id or account_id}",
            reason="not_admin",
        )
        raise HTTPException(status_code=403, detail="Admin access required")
    if request is not None and str(getattr(request, "method", "GET") or "GET").upper() not in {"GET", "HEAD", "OPTIONS"}:
        _enforce_beta_rate_limit("admin_destructive", request, identity=f"admin:{actor_id}")
    out = dict(user_data)
    out["account_id"] = account_id
    out["actor_tg_id"] = actor_id
    out["id"] = actor_id
    return out


def _safe_public_url(value: str) -> str:
    return str(value or "").strip()


def _version_parts(value: str | None) -> tuple[int, ...]:
    raw = str(value or "").strip().lower().lstrip("v")
    if not raw:
        return ()
    nums = [int(part) for part in re.findall(r"\d+", raw)[:4]]
    while nums and nums[-1] == 0:
        nums.pop()
    return tuple(nums)


def _compare_versions(left: str | None, right: str | None) -> int:
    a = _version_parts(left)
    b = _version_parts(right)
    if not a and not b:
        return 0
    if not a:
        return -1
    if not b:
        return 1
    width = max(len(a), len(b))
    aa = a + (0,) * (width - len(a))
    bb = b + (0,) * (width - len(b))
    if aa < bb:
        return -1
    if aa > bb:
        return 1
    return 0


def _client_update_policy(
    *,
    platform: str,
    requested_platform: str,
    current_version: str,
    latest_version: str,
    min_supported_version: str,
    url: str,
) -> str:
    if not url or not latest_version:
        return "none"
    if str(platform or "").strip().lower() != str(requested_platform or "").strip().lower():
        return "none"
    if not str(current_version or "").strip():
        return "none"
    if min_supported_version and _compare_versions(current_version, min_supported_version) < 0:
        return "required"
    if _compare_versions(current_version, latest_version) < 0:
        return "recommended"
    return "none"


def _client_app_update_info(
    *,
    platform: str,
    requested_platform: str,
    current_version: str,
    channel: str,
    latest_version: str,
    min_supported_version: str,
    url: str,
    sha256: str,
    size: int,
    release_notes: str,
    release_notes_url: str,
    published_at: str,
) -> ClientAppUpdateInfo:
    safe_url = _safe_public_url(url)
    return ClientAppUpdateInfo(
        platform=str(platform or "").strip().lower(),
        channel=str(channel or "beta").strip().lower() or "beta",
        latest_version=str(latest_version or "").strip(),
        min_supported_version=str(min_supported_version or "").strip(),
        update_policy=_client_update_policy(
            platform=platform,
            requested_platform=requested_platform,
            current_version=current_version,
            latest_version=latest_version,
            min_supported_version=min_supported_version,
            url=safe_url,
        ),
        url=safe_url,
        sha256=str(sha256 or "").strip(),
        size=max(0, int(size or 0)),
        release_notes=str(release_notes or "").strip()[:1000],
        release_notes_url=_safe_public_url(release_notes_url),
        published_at=str(published_at or "").strip(),
        rollout_percent=100,
        force_after=None,
    )


def _public_webapp_url() -> str:
    configured = _safe_public_url(getattr(Settings, "WEBAPP_URL", ""))
    if configured:
        return configured
    return "https://app.pokrov.space/"


def _normalize_cabinet_target_path(value: str | None) -> str:
    raw = str(value or "/").strip() or "/"
    parsed = urlparse(raw)
    if parsed.scheme or parsed.netloc or raw.startswith("//"):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_cabinet_target",
                "message": "Cabinet handoff target must be a relative app path.",
            },
        )
    path = parsed.path or raw
    if not path.startswith("/"):
        path = f"/{path}"
    path = re.sub(r"/{2,}", "/", path)
    query = str(parsed.query or "").strip()
    return f"{path}?{query}" if query else path


def _build_cabinet_handoff_url(*, token: str, target_path: str) -> str:
    base = _public_webapp_url() or "https://app.pokrov.space/"
    base_parsed = urlparse(base)
    base_host = (base_parsed.hostname or "").lower().strip()
    if base_host in {"kiwunaka.space", "portal-privacy.online", "www.portal-privacy.online"}:
        base_parsed = urlparse("https://app.pokrov.space/")
    target_parsed = urlparse(_normalize_cabinet_target_path(target_path))
    query = {
        key: value
        for key, value in parse_qsl(target_parsed.query, keep_blank_values=True)
        if key not in {"token", "handoff_token", "web_session_token", "web_session"}
    }
    query["handoff_token"] = str(token or "").strip()
    return base_parsed._replace(
        path=target_parsed.path or "/",
        query=urlencode(query),
        fragment="",
    ).geturl()


def _cabinet_handoff_token_hash(token: str) -> str:
    return hashlib.sha256(str(token or "").strip().encode("utf-8")).hexdigest()


def _cleanup_expired_cabinet_handoff_tokens(s, *, now: datetime) -> int:
    cutoff = now - timedelta(seconds=int(CABINET_HANDOFF_LEDGER_RETENTION_SECONDS))
    return (
        s.query(WebCabinetHandoffToken)
        .filter(WebCabinetHandoffToken.expires_at < cutoff)
        .delete(synchronize_session=False)
    )


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
    if not PAID_CHECKOUT_LAUNCH_APPROVED:
        issues.append(
            (
                "paid_checkout_launch_evidence_missing",
                "Paid checkout is closed until Lava.top and paid email delivery evidence are approved",
            )
        )
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
    enabled = enabled_public_provider_catalog()
    if not enabled:
        issues.append(("no_enabled_providers", "No RUB payment providers are configured"))
    email_status = email_delivery_runtime_status()
    if not bool(email_status.get("enabled")):
        reasons = ", ".join(str(item) for item in (email_status.get("blocked_reasons") or []) if item) or "not_ready"
        issues.append(
            (
                "email_delivery_not_ready",
                f"Email delivery is not ready for paid access keys: {reasons}",
            )
        )
    return issues


def _checkout_runtime_errors() -> list[str]:
    return [detail for _code, detail in _checkout_runtime_issues()]


def _public_checkout_provider_state() -> RubProvidersOut:
    issues = _checkout_runtime_issues()
    blocked = bool(issues)
    rows = []
    if not blocked:
        for row in enabled_public_provider_catalog():
            payload = dict(row)
            payload["supported_plan_codes"] = [
                code
                for code in RUB_PLAN_PRICES
                if public_provider_is_configured_for_plan(str(row.get("code") or ""), code)
            ]
            rows.append(RubProviderChoiceOut(**payload))
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


def _ensure_checkout_provider_enabled(provider: str) -> None:
    normalized = _normalize_provider(provider)
    enabled = {str(row.get("code") or "") for row in enabled_public_provider_catalog()}
    if not normalized or normalized not in enabled:
        raise HTTPException(status_code=503, detail=f"{normalized or 'provider'} is not enabled for public RUB checkout")


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


def _payload_nested_value(payload: dict[str, Any], *path: str) -> str:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    return str(current or "").strip()


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
    raw = await _read_limited_request_body(request, max_bytes=PAYMENT_CALLBACK_MAX_BYTES, scope="Payment callback")
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


_PAYMENT_REDACT_KEY_RE = re.compile(
    r"(token|secret|password|passwd|signature|sign|hash|api[_-]?key|authorization|auth|card|pan|cvv|cvc|email)",
    re.IGNORECASE,
)

_EXTERNAL_ORDER_META_JSON_LIMIT = 4000
_PAYMENT_EVENT_JSON_LIMIT = 16000


def _compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _bounded_json_value(value: Any, *, depth: int = 0) -> Any:
    if depth >= 5:
        return "[nested]"
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        items = list(value.items())
        for key, item in items[:32]:
            key_text = str(key or "")[:64]
            if key_text:
                out[key_text] = _bounded_json_value(item, depth=depth + 1)
        if len(items) > 32:
            out["_pokrov_entries_omitted"] = len(items) - 32
        return out
    if isinstance(value, list):
        out = [_bounded_json_value(item, depth=depth + 1) for item in value[:20]]
        if len(value) > 20:
            out.append({"_pokrov_entries_omitted": len(value) - 20})
        return out
    if isinstance(value, str):
        return value[:256]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)[:128]


def _bounded_mapping(
    value: dict[str, Any],
    *,
    max_serialized: int,
    priority_keys: tuple[str, ...] = (),
) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, item in value.items():
        key_text = str(key or "")[:64]
        if key_text:
            normalized[key_text] = _bounded_json_value(item, depth=1)
    ordered_keys = [key for key in priority_keys if key in normalized]
    ordered_keys.extend(key for key in normalized if key not in ordered_keys)
    result: dict[str, Any] = {}
    omitted = 0
    for key in ordered_keys:
        trial = {**result, key: normalized[key]}
        if len(_compact_json(trial)) <= max_serialized:
            result[key] = normalized[key]
        else:
            omitted += 1
    if omitted:
        summary = {
            "omitted_fields": omitted,
            "fingerprint": hashlib.sha256(_compact_json(normalized).encode("utf-8")).hexdigest()[:16],
        }
        trial = {**result, "_pokrov_metadata_summary": summary}
        if len(_compact_json(trial)) <= max_serialized:
            result["_pokrov_metadata_summary"] = summary
    return result


def _redact_payment_payload(value: Any, *, max_serialized: int = 12000) -> Any:
    def _redact(item: Any, *, depth: int = 0) -> Any:
        if depth >= 5:
            return "[nested]"
        if isinstance(item, dict):
            out: dict[str, Any] = {}
            entries = list(item.items())
            for key, child in entries[:32]:
                key_text = str(key or "")[:64]
                if not key_text:
                    continue
                if _PAYMENT_REDACT_KEY_RE.search(key_text):
                    out[key_text] = "[redacted]"
                else:
                    out[key_text] = _redact(child, depth=depth + 1)
            if len(entries) > 32:
                out["_pokrov_entries_omitted"] = len(entries) - 32
            return out
        if isinstance(item, list):
            out = [_redact(child, depth=depth + 1) for child in item[:20]]
            if len(item) > 20:
                out.append({"_pokrov_entries_omitted": len(item) - 20})
            return out
        if isinstance(item, str):
            return item[:256]
        if item is None or isinstance(item, (bool, int, float)):
            return item
        return str(item)[:128]

    redacted = _redact(value)
    serialized = _compact_json(redacted)
    if len(serialized) <= max_serialized:
        return redacted

    result: dict[str, Any] = {}
    if isinstance(redacted, dict) and "_pokrov_processing_error" in redacted:
        result["_pokrov_processing_error"] = redacted["_pokrov_processing_error"]
    result["_pokrov_payload_summary"] = {
        "truncated": True,
        "fingerprint": hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16],
        "serialized_length": len(serialized),
        "entry_count": len(redacted) if isinstance(redacted, dict) else None,
    }
    if isinstance(redacted, dict):
        for key in (
            "eventType",
            "status",
            "payment_status",
            "amount",
            "currency",
            "contractId",
            "order_id",
            "clientUtm",
            "plan_code",
            "provider",
        ):
            if key not in redacted or key in result:
                continue
            trial = {**result, key: redacted[key]}
            if len(_compact_json(trial)) <= max_serialized:
                result[key] = redacted[key]
    return result


def _serialize_payment_event_payload(value: dict[str, Any]) -> str:
    bounded = _redact_payment_payload(value, max_serialized=_PAYMENT_EVENT_JSON_LIMIT - 512)
    serialized = _compact_json(bounded)
    if len(serialized) <= _PAYMENT_EVENT_JSON_LIMIT:
        return serialized
    error_code = bounded.get("_pokrov_processing_error") if isinstance(bounded, dict) else None
    summary = {
        "_pokrov_processing_error": error_code,
        "_pokrov_payload_summary": {
            "truncated": True,
            "fingerprint": hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16],
            "serialized_length": len(serialized),
        },
    }
    return _compact_json(summary)


def _verify_lavatop_callback_auth(request: Request) -> tuple[bool, str]:
    expected_api_key = (os.getenv("LAVATOP_WEBHOOK_API_KEY") or "").strip()
    expected_basic_user = (os.getenv("LAVATOP_WEBHOOK_BASIC_USERNAME") or "").strip()
    expected_basic_password = (os.getenv("LAVATOP_WEBHOOK_BASIC_PASSWORD") or "").strip()
    if not expected_api_key and not (expected_basic_user and expected_basic_password):
        return False, "missing_lavatop_webhook_secret"

    provided_api_key = str(request.headers.get("X-Api-Key") or request.headers.get("x-api-key") or "").strip()
    if expected_api_key and provided_api_key:
        if hmac.compare_digest(provided_api_key, expected_api_key):
            return True, "ok"
        return False, "invalid_lavatop_webhook_api_key"

    auth_header = str(request.headers.get("Authorization") or "").strip()
    if expected_basic_user and expected_basic_password and auth_header.lower().startswith("basic "):
        token = auth_header.split(" ", 1)[1].strip()
        try:
            decoded = base64.b64decode(token.encode("ascii"), validate=True).decode("utf-8")
        except Exception:
            return False, "invalid_lavatop_basic_auth"
        username, sep, password = decoded.partition(":")
        if sep and hmac.compare_digest(username, expected_basic_user) and hmac.compare_digest(password, expected_basic_password):
            return True, "ok"
        return False, "invalid_lavatop_basic_auth"

    return False, "missing_lavatop_webhook_auth"


def _lavatop_webhook_auth_configured() -> bool:
    return bool(
        (os.getenv("LAVATOP_WEBHOOK_API_KEY") or "").strip()
        or (
            (os.getenv("LAVATOP_WEBHOOK_BASIC_USERNAME") or "").strip()
            and (os.getenv("LAVATOP_WEBHOOK_BASIC_PASSWORD") or "").strip()
        )
    )


def _verify_callback_signature(*, provider: str, payload: dict[str, Any], raw: bytes, request: Request) -> tuple[bool, str]:
    p = _normalize_provider(provider)
    # Freekassa SCI notify signature:
    # md5(MERCHANT_ID:AMOUNT:SECRET_WORD_2:MERCHANT_ORDER_ID)
    if p == "freekassa":
        sci_keys = {"MERCHANT_ID", "AMOUNT", "MERCHANT_ORDER_ID", "SIGN"}
        present_sci_keys = sci_keys.intersection(payload.keys())
        if present_sci_keys:
            if present_sci_keys != sci_keys or any(not _payload_value(payload, key) for key in sci_keys):
                return False, "incomplete_sci_payload"
            merchant_id = _payload_value(payload, "MERCHANT_ID")
            amount = _payload_value(payload, "AMOUNT")
            order_id = _payload_value(payload, "MERCHANT_ORDER_ID")
            provided = _payload_value(payload, "SIGN")
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
        if not FREEKASSA_GENERIC_HMAC_COMPAT_ENABLED:
            return False, "generic_hmac_disabled"
    if p == "lavatop":
        return _verify_lavatop_callback_auth(request)
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
    if p in {"cardlink", "lavatop", "pally", "platima"}:
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


def _external_order_meta(row: ExternalOrder | None) -> dict[str, Any]:
    if not row:
        return {}
    try:
        payload = json.loads(str(getattr(row, "meta_json", "") or "{}"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _serialize_external_order_meta(meta: dict[str, Any]) -> str:
    source = dict(meta or {})
    prepared: dict[str, Any] = {}
    section_contracts = {
        "fulfillment": (
            1100,
            (
                "mode",
                "status",
                "buyer_email",
                "access_key",
                "email_delivery",
                "error_code",
                "tg_id",
                "activated_at",
                "access_key_issued_at",
            ),
        ),
        "reversal": (
            1000,
            (
                "operator_action_required",
                "reconciliation_status",
                "recorded_at",
                "event_type",
                "provider",
                "order_id",
                "reason",
                "external_id",
            ),
        ),
        "pricing": (
            900,
            (
                "base_amount_rub",
                "final_amount_rub",
                "discount_pct",
                "discount_applied",
                "pending_discount_code",
                "direct_discount_pct",
                "direct_discount_code",
                "direct_discount_source",
                "referral_discount_eligible",
            ),
        ),
    }
    for key, value in source.items():
        if key == "callback":
            prepared[key] = _redact_payment_payload(value, max_serialized=1000)
        elif key in section_contracts and isinstance(value, dict):
            max_serialized, priority = section_contracts[key]
            prepared[key] = _bounded_mapping(
                value,
                max_serialized=max_serialized,
                priority_keys=priority,
            )
        else:
            prepared[key] = _bounded_json_value(value)

    bounded = _bounded_mapping(
        prepared,
        max_serialized=_EXTERNAL_ORDER_META_JSON_LIMIT,
        priority_keys=(
            "fulfillment",
            "entitlement_snapshot",
            "reversal",
            "pricing",
            "buyer_email",
            "order_id",
            "tg_id",
            "plan_code",
            "provider",
            "source",
            "campaign",
            "requested_promo_code",
            "promo_code",
            "payment_method",
            "lavatop_payment_provider",
            "lavatop_payment_method",
            "plan_label",
            "callback",
        ),
    )
    return _compact_json(bounded)


def _set_external_order_meta(row: ExternalOrder, meta: dict[str, Any]) -> None:
    row.meta_json = _serialize_external_order_meta(meta)


def _payload_amount(payload: dict[str, Any]) -> float:
    return _safe_float(
        _payload_value(payload, "amount", "AMOUNT", "sum", "amount_paid", "OutSum")
        or _payload_nested_value(payload, "contract", "amount")
        or _payload_nested_value(payload, "invoice", "amount")
        or _payload_nested_value(payload, "payment", "amount")
    )


def _payload_amount_decimal(payload: dict[str, Any]) -> Decimal | None:
    raw_amount = (
        _payload_value(payload, "amount", "AMOUNT", "sum", "amount_paid", "OutSum")
        or _payload_nested_value(payload, "contract", "amount")
        or _payload_nested_value(payload, "invoice", "amount")
        or _payload_nested_value(payload, "payment", "amount")
    )
    if not raw_amount:
        return None
    try:
        amount = Decimal(raw_amount)
    except (InvalidOperation, ValueError):
        return None
    if not amount.is_finite() or amount <= 0:
        return None
    scale = max(0, -int(amount.as_tuple().exponent))
    if scale > 2:
        return None
    return amount


def _payload_currency(payload: dict[str, Any]) -> str:
    return (
        _payload_value(payload, "currency", "CURRENCY", "cur", "ccy")
        or _payload_nested_value(payload, "contract", "currency")
        or _payload_nested_value(payload, "invoice", "currency")
        or _payload_nested_value(payload, "payment", "currency")
        or ""
    ).strip().upper()


def _payload_plan_code(payload: dict[str, Any]) -> str:
    return (
        _payload_value(payload, "plan_code", "tariff", "plan", "us_plan_code")
        or _payload_nested_value(payload, "clientUtm", "utm_term")
    ).strip().lower()


def _status_from_event(event_type: str, payload: dict[str, Any], signature_ok: bool, provider: str = "") -> str:
    event = (event_type or "").strip().lower()
    if not signature_ok:
        return "pending_verification"
    if event == "refund":
        return "refunded"
    if event == "chargeback":
        return "chargeback"

    provider_state = payment_callback_status(provider, payload)
    status_raw = _payload_value(payload, "status", "payment_status", "state").lower()
    state = (provider_state or status_raw).strip().lower()
    if state in {"paid", "success", "succeeded", "approved", "completed"}:
        return "paid"
    if state in {"cancelled", "canceled", "cancel"}:
        return "cancelled"
    if state in {"refunded", "refund"}:
        return "refunded"
    if state in {"failed", "fail", "rejected", "declined", "error"}:
        return "failed"
    if state in {"manual_review", "review", "needs_review", "needs_operator", "requires_action"}:
        return "manual_review"
    if state in {"created", "pending", "processing", "new", "waiting"}:
        return "pending"
    if (
        _normalize_provider(provider) == "freekassa"
        and event == "result"
        and not state
        and all(_payload_value(payload, key) for key in ("MERCHANT_ID", "AMOUNT", "MERCHANT_ORDER_ID", "SIGN"))
    ):
        return "paid"
    return "manual_review"


def _payment_order_correlation(*, provider: str, order_id: str) -> str:
    material = f"{_normalize_provider(provider)}|{str(order_id or '').strip()}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def _safe_payment_processing_error(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    allowed = {
        "access_key_issue_failed",
        "access_key_email_delivery_error",
        "delivery_evidence_failed",
        "account_conflict",
        "claim_definition_conflict",
        "claim_reversed",
        "db_error",
        "fallback_creator_conflict",
        "fallback_missing",
        "fallback_ownership_conflict",
        "fallback_redeemed_conflict",
        "fallback_type_conflict",
        "grant_fulfillment_failed",
        "grant_not_found",
        "manual_review",
        "missing_buyer_email",
        "missing_entitlement_snapshot",
        "missing_tg_id",
        "invalid_entitlement_snapshot",
        "order_not_found",
        "order_reversed",
        "payment_pending",
        "unsupported_plan",
        "user_create_failed",
        "verified_email_mismatch",
    }
    return normalized if normalized in allowed else "durable_fulfillment_failed"


_TERMINAL_PAYMENT_FULFILLMENT_CODES = {
    "account_conflict",
    "claim_definition_conflict",
    "claim_reversed",
    "fallback_creator_conflict",
    "fallback_missing",
    "fallback_ownership_conflict",
    "fallback_redeemed_conflict",
    "fallback_type_conflict",
    "manual_review",
    "missing_buyer_email",
    "missing_entitlement_snapshot",
    "invalid_entitlement_snapshot",
    "order_reversed",
    "unsupported_plan",
    "verified_email_mismatch",
}

_TERMINAL_PAYMENT_REVERSAL_CODES = {
    "claim_reversed",
    "fallback_missing",
    "grant_not_found",
    "manual_review",
}


def _upsert_external_order(
    s,
    *,
    provider: str,
    order_id: str,
    payload: dict[str, Any],
    status: str,
    mark_paid: bool,
) -> ExternalOrder | None:
    if not order_id:
        return None
    row = (
        s.query(ExternalOrder)
        .filter(ExternalOrder.provider == provider, ExternalOrder.order_id == order_id)
        .with_for_update()
        .populate_existing()
        .first()
    )
    created = row is None
    if created and _normalize_provider(provider) == "freekassa":
        # FreeKassa callbacks may report an order, but only a locally created
        # order is allowed to become product authority.
        return None
    if created:
        row = ExternalOrder(provider=provider, order_id=order_id, created_at=_utcnow())
        s.add(row)
        row.tg_id = _safe_int(_payload_value(payload, "tg_id", "telegram_id", "user_id", "us_tg_id"))
        row.plan_code = _payload_plan_code(payload) or row.plan_code
    callback_can_define_authority = _normalize_provider(provider) != "freekassa"
    if callback_can_define_authority and created:
        row.source = (
            _payload_value(payload, "source", "checkout_source", "us_source")
            or _payload_nested_value(payload, "clientUtm", "utm_medium")
            or row.source
        )
        row.campaign = (
            _payload_value(payload, "campaign", "utm_campaign")
            or _payload_nested_value(payload, "clientUtm", "utm_campaign")
            or row.campaign
        )
    if callback_can_define_authority:
        row.promo_code = _payload_value(payload, "promo_code", "coupon") or row.promo_code
    meta = _external_order_meta(row)
    meta["callback"] = _redact_payment_payload(payload, max_serialized=1000)
    _set_external_order_meta(row, meta)
    if callback_can_define_authority:
        callback_amount = _payload_amount(payload)
        if callback_amount > 0 and float(row.amount or 0) <= 0:
            row.amount = callback_amount
        row.currency = _payload_currency(payload) or row.currency or "RUB"
    current_status = str(row.status or "").strip().lower()
    incoming_status = str(status or "").strip().lower()
    if current_status == "chargeback":
        incoming_status = "chargeback"
    elif current_status == "refunded" and incoming_status != "chargeback":
        incoming_status = "refunded"
    elif current_status == "paid" and incoming_status in {
        "created",
        "pending",
        "pending_verification",
        "failed",
        "cancelled",
        "manual_review",
    }:
        incoming_status = "paid"
    row.status = incoming_status or current_status or "created"
    if mark_paid and not row.paid_at:
        row.paid_at = _utcnow()
    return row


def _mark_payment_reversal_pending(
    *,
    row: ExternalOrder,
    provider: str,
    event_type: str,
) -> None:
    meta = _external_order_meta(row)
    fulfillment = dict(meta.get("fulfillment") or {})
    fulfillment["status"] = "reversal_pending_operator_action"
    meta["fulfillment"] = fulfillment
    meta["reversal"] = {
        "event_type": re.sub(r"[^a-z_]", "", str(event_type or "").strip().lower())[:32] or "reversal",
        "provider": _normalize_provider(provider),
        "order_id": str(row.order_id or "")[:128],
        "reason": "provider_reversal",
        "operator_action_required": True,
        "reconciliation_status": "pending",
        "recorded_at": _safe_iso(_utcnow()),
    }
    _set_external_order_meta(row, meta)


def _record_external_payment_event(
    *,
    provider: str,
    event_type: str,
    external_id: str,
    order_id: str,
    payload: dict[str, Any],
    signature_ok: bool,
    processed_ok: bool,
    status: str | None = None,
) -> tuple[bool, bool]:
    persist_payload = _redact_payment_payload(payload, max_serialized=_PAYMENT_EVENT_JSON_LIMIT - 512)
    s = SessionLocal()
    try:
        exists = (
            s.query(ExternalPaymentEvent)
            .filter(
                ExternalPaymentEvent.provider == provider,
                ExternalPaymentEvent.event_type == event_type,
                ExternalPaymentEvent.external_id == external_id,
            )
            .with_for_update()
            .first()
        )
        if exists:
            if bool(getattr(exists, "signature_ok", False)) and bool(getattr(exists, "processed_ok", False)):
                return True, True
            if not signature_ok:
                return True, True
            exists.order_id = order_id or None
            exists.payload_json = _serialize_payment_event_payload(persist_payload)
            exists.signature_ok = True
            exists.processed_ok = bool(processed_ok)
            event_status = status or _status_from_event(event_type, payload, signature_ok=True, provider=provider)
            if str(payload.get("_pokrov_validation_error") or "") != "unknown_order":
                order_row = _upsert_external_order(
                    s,
                    provider=provider,
                    order_id=order_id,
                    payload=payload,
                    status=event_status,
                    mark_paid=event_status == "paid",
                )
                if order_row is not None and event_type in {"refund", "chargeback"}:
                    _mark_payment_reversal_pending(row=order_row, provider=provider, event_type=event_type)
            s.commit()
            return False, True

        event = ExternalPaymentEvent(
            provider=provider,
            event_type=event_type,
            external_id=external_id,
            order_id=order_id or None,
            payload_json=_serialize_payment_event_payload(persist_payload),
            signature_ok=bool(signature_ok),
            processed_ok=bool(processed_ok),
            created_at=_utcnow(),
        )
        s.add(event)

        event_status = status or _status_from_event(event_type, payload, signature_ok=signature_ok, provider=provider)
        if signature_ok and str(payload.get("_pokrov_validation_error") or "") != "unknown_order":
            order_row = _upsert_external_order(
                s,
                provider=provider,
                order_id=order_id,
                payload=payload,
                status=event_status,
                mark_paid=event_status == "paid",
            )
            if order_row is not None and event_type in {"refund", "chargeback"}:
                _mark_payment_reversal_pending(row=order_row, provider=provider, event_type=event_type)
        s.commit()
        return False, True
    except Exception:
        s.rollback()
        logger.error(
            "payment callback persistence failed code=callback_persistence_failed correlation=%s",
            _payment_order_correlation(provider=provider, order_id=order_id),
        )
        return False, False
    finally:
        s.close()


def _complete_external_payment_event(
    *,
    provider: str,
    event_type: str,
    external_id: str,
    processed_ok: bool,
    error_code: str | None = None,
) -> bool:
    s = SessionLocal()
    try:
        event = (
            s.query(ExternalPaymentEvent)
            .filter(
                ExternalPaymentEvent.provider == str(provider),
                ExternalPaymentEvent.event_type == str(event_type),
                ExternalPaymentEvent.external_id == str(external_id),
            )
            .with_for_update()
            .one_or_none()
        )
        if event is None:
            return False
        event.processed_ok = bool(processed_ok)
        if error_code:
            try:
                stored = json.loads(str(event.payload_json or "{}"))
                if not isinstance(stored, dict):
                    stored = {}
            except Exception:
                stored = {}
            stored["_pokrov_processing_error"] = _safe_payment_processing_error(error_code)
            event.payload_json = _serialize_payment_event_payload(stored)
        s.commit()
        return True
    except Exception:
        s.rollback()
        logger.error(
            "payment callback completion persistence failed code=callback_completion_failed correlation=%s",
            _payment_order_correlation(provider=provider, order_id=external_id),
        )
        return False
    finally:
        s.close()


def _record_payment_entitlement_retry_error(*, provider: str, order_id: str, error_code: str) -> None:
    s = SessionLocal()
    try:
        record_payment_entitlement_claim_error(
            s,
            provider=provider,
            order_id=order_id,
            error_code=error_code,
            now=_utcnow(),
        )
        s.commit()
    except PaymentEntitlementNotFoundError:
        s.rollback()
    except Exception:
        s.rollback()
        logger.error(
            "payment entitlement retry evidence persistence failed code=retry_evidence_failed correlation=%s",
            _payment_order_correlation(provider=provider, order_id=order_id),
        )
    finally:
        s.close()


def _validate_paid_callback_against_order(*, provider: str, order_id: str, payload: dict[str, Any]) -> tuple[bool, str]:
    if not order_id:
        return False, "missing_order_id"
    s = SessionLocal()
    try:
        row = (
            s.query(ExternalOrder)
            .filter(ExternalOrder.provider == str(provider), ExternalOrder.order_id == str(order_id))
            .first()
        )
        if not row:
            return False, "unknown_order"
        if str(row.provider or "").strip().lower() != str(provider).strip().lower():
            return False, "provider_mismatch"
        persisted_tg_id = int(row.tg_id) if row.tg_id is not None else None
        callback_tg_id = _safe_int(_payload_value(payload, "tg_id", "telegram_id", "user_id", "us_tg_id"))
        if persisted_tg_id is not None and callback_tg_id is not None and persisted_tg_id != callback_tg_id:
            return False, "order_owner_mismatch"
        normalized_provider = _normalize_provider(provider)
        if normalized_provider == "freekassa":
            expected_source = str(row.source or "").strip().lower()
            if expected_source not in {"site", "bot"}:
                return False, "invalid_order_source"
            merchant_id = _payload_value(payload, "MERCHANT_ID")
            if merchant_id:
                merchant_source = _fk_source_by_merchant_id(merchant_id)
                if not merchant_source or merchant_source != expected_source:
                    return False, "merchant_source_mismatch"
            callback_source = _payload_value(payload, "source", "checkout_source", "us_source")
            if callback_source and callback_source.strip().lower() != expected_source:
                return False, "source_mismatch"
            expected_plan = str(row.plan_code or "").strip().lower()
            if not expected_plan:
                return False, "missing_order_plan"
            actual_plan = _payload_plan_code(payload)
            if actual_plan and actual_plan != expected_plan:
                return False, "plan_mismatch"
            expected_currency = str(row.currency or "").strip().upper()
            if expected_currency != "RUB":
                return False, "invalid_order_currency"
            actual_currency = _payload_currency(payload)
            if actual_currency and actual_currency != expected_currency:
                return False, "currency_mismatch"
            actual_amount = _payload_amount_decimal(payload)
            if actual_amount is None:
                return False, "invalid_amount"
            try:
                expected_amount = Decimal(str(row.amount))
            except (InvalidOperation, ValueError):
                return False, "invalid_order_amount"
            if not expected_amount.is_finite() or expected_amount <= 0:
                return False, "invalid_order_amount"
            if actual_amount != expected_amount:
                return False, "amount_mismatch"
            return True, "ok"
        if normalized_provider != "lavatop":
            return True, "ok"
        expected_amount = float(row.amount or 0)
        actual_amount = _payload_amount(payload)
        if expected_amount > 0 and actual_amount <= 0:
            return False, "missing_amount"
        if expected_amount > 0 and abs(expected_amount - actual_amount) > 0.01:
            return False, "amount_mismatch"
        expected_currency = str(row.currency or "RUB").strip().upper() or "RUB"
        actual_currency = _payload_currency(payload)
        if not actual_currency:
            return False, "missing_currency"
        if actual_currency != expected_currency:
            return False, "currency_mismatch"
        expected_plan = str(row.plan_code or "").strip().lower()
        actual_plan = _payload_plan_code(payload)
        if expected_plan and actual_plan and actual_plan != expected_plan:
            return False, "plan_mismatch"
        return True, "ok"
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


def _validated_external_order_entitlement_snapshot(row: ExternalOrder) -> tuple[dict[str, Any] | None, str]:
    snapshot = _external_order_meta(row).get("entitlement_snapshot")
    if not isinstance(snapshot, dict):
        return None, "missing_entitlement_snapshot"
    plan_code = str(snapshot.get("plan_code") or "").strip().lower()
    if not plan_code or plan_code != str(row.plan_code or "").strip().lower():
        return None, "invalid_entitlement_snapshot"
    try:
        duration_days = int(snapshot.get("duration_days") or 0)
    except (TypeError, ValueError):
        return None, "invalid_entitlement_snapshot"
    if duration_days <= 0 or duration_days > 3650:
        return None, "invalid_entitlement_snapshot"
    source = str(snapshot.get("source") or "").strip().lower()
    if source not in {"site", "bot"} or source != str(row.source or "").strip().lower():
        return None, "invalid_entitlement_snapshot"
    currency = str(snapshot.get("currency") or "").strip().upper()
    if currency != "RUB" or currency != str(row.currency or "").strip().upper():
        return None, "invalid_entitlement_snapshot"
    try:
        snapshot_amount = Decimal(str(snapshot.get("amount_rub") or ""))
        order_amount = Decimal(str(row.amount))
    except (InvalidOperation, ValueError):
        return None, "invalid_entitlement_snapshot"
    if (
        not snapshot_amount.is_finite()
        or not order_amount.is_finite()
        or snapshot_amount <= 0
        or snapshot_amount != order_amount
        or max(0, -int(snapshot_amount.as_tuple().exponent)) > 2
    ):
        return None, "invalid_entitlement_snapshot"
    return {
        "plan_code": plan_code,
        "duration_days": duration_days,
        "source": source,
        "currency": currency,
        "amount_rub": snapshot_amount,
    }, "ok"


def _external_order_has_reversal_state(row: ExternalOrder, meta: dict[str, Any]) -> bool:
    if str(row.status or "").strip().lower() in {"refunded", "chargeback"}:
        return True
    fulfillment = meta.get("fulfillment") if isinstance(meta.get("fulfillment"), dict) else {}
    fulfillment_status = str(fulfillment.get("status") or "").strip().lower()
    if fulfillment_status in {"reversed", "reversal_pending_operator_action"}:
        return True
    reversal = meta.get("reversal") if isinstance(meta.get("reversal"), dict) else {}
    reconciliation = str(reversal.get("reconciliation_status") or "").strip().lower()
    return bool(reversal.get("operator_action_required") is True or reconciliation in {
        "pending",
        "reversed",
        "already_reversed",
        "fallback_missing",
        "grant_not_found",
    })


def _apply_external_paid_order(*, provider: str, order_id: str, payload: dict[str, Any]) -> tuple[bool, str]:
    s = SessionLocal()
    try:
        ext_order = None
        if order_id:
            ext_order = (
                s.query(ExternalOrder)
                .filter(ExternalOrder.provider == str(provider), ExternalOrder.order_id == str(order_id))
                .with_for_update()
                .first()
            )
        if ext_order is None:
            return False, "order_not_found"
        tg_id = int(ext_order.tg_id) if ext_order.tg_id is not None else None
        if tg_id is None:
            return False, "missing_tg_id"
        ext_meta = _external_order_meta(ext_order) if ext_order else {}
        fulfillment = dict(ext_meta.get("fulfillment") or {})
        if _external_order_has_reversal_state(ext_order, ext_meta):
            return False, "order_reversed"
        if str(fulfillment.get("status") or "").strip().lower() == "account_extended":
            return True, "already_applied"
        entitlement_snapshot: dict[str, Any] | None = None
        if _normalize_provider(provider) == "freekassa":
            entitlement_snapshot, snapshot_reason = _validated_external_order_entitlement_snapshot(ext_order)
            if entitlement_snapshot is None:
                return False, snapshot_reason

        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            s.rollback()
            _ensure_user_row_for_login(
                tg_id=int(tg_id),
                username=None,
                include_legacy_payment_authority=False,
            )
            ext_order = (
                s.query(ExternalOrder)
                .filter(ExternalOrder.provider == str(provider), ExternalOrder.order_id == str(order_id))
                .with_for_update()
                .populate_existing()
                .one_or_none()
            )
            if ext_order is None:
                return False, "order_not_found"
            refreshed_tg_id = int(ext_order.tg_id) if ext_order.tg_id is not None else None
            if refreshed_tg_id != tg_id:
                return False, "account_conflict"
            ext_meta = _external_order_meta(ext_order)
            fulfillment = dict(ext_meta.get("fulfillment") or {})
            if _external_order_has_reversal_state(ext_order, ext_meta):
                return False, "order_reversed"
            if str(fulfillment.get("status") or "").strip().lower() == "account_extended":
                return True, "already_applied"
            user = s.query(User).filter(User.tg_id == int(tg_id)).first()
            if not user:
                return False, "user_create_failed"

        plan_code = str(ext_order.plan_code or "").strip().lower()
        if not plan_code:
            return False, "unsupported_plan"
        plan_cfg = _resolve_plan_config(s=s, code=plan_code)
        if not plan_cfg:
            return False, "unsupported_plan"
        days = (
            int(entitlement_snapshot["duration_days"])
            if entitlement_snapshot is not None
            else max(1, int(plan_cfg.get("days") or plan_cfg.get("duration_days") or 30))
        )

        now = _utcnow()
        old_sub = (user.sub_type or "").upper().strip()
        referrer_id = int(getattr(user, "referrer_id", 0) or 0)
        new_referral_relationship = False
        plan_amount_stars = int(plan_cfg.get("amount_stars") or API_PLAN_PRICES.get(plan_code) or 0)
        ensure_user_account_foundation(s, user, now=now)
        s.flush()
        if referrer_id > 0:
            referrer = s.query(User).filter(User.tg_id == referrer_id).one_or_none()
            if referrer is not None:
                ensure_user_account_foundation(s, referrer, now=now)
                s.flush()
                existing_relationship = s.query(ReferralRelationship.id).filter_by(
                    referred_account_id=str(user.account_id)
                ).first()
                create_referral_relationship(
                    s,
                    referred_account_id=str(user.account_id),
                    referrer_account_id=str(referrer.account_id),
                    source="legacy_referrer_projection",
                    now=now,
                )
                new_referral_relationship = existing_relationship is None
        payment_result = record_successful_payment_grant(
            s,
            account_id=str(user.account_id),
            legacy_tg_id=int(user.tg_id),
            provider=str(provider),
            order_id=str(order_id),
            plan_code=plan_code,
            duration_days=days,
            paid_at=now,
        )
        first_paid_purchase = bool(payment_result.is_first_payment)
        if first_paid_purchase and new_referral_relationship and referrer_id > 0:
            referrer.referral_count = int(referrer.referral_count or 0) + 1
        user.pending_discount_pct = None
        user.pending_discount_code = None
        user.pending_discount_set_at = None

        if ext_order:
            ext_order.status = "paid"
            ext_order.paid_at = ext_order.paid_at or now
            ext_order.plan_code = plan_code
            fulfillment.update(
                {
                    "mode": "account_extend",
                    "status": "account_extended",
                    "tg_id": int(tg_id),
                    "activated_at": _safe_iso(now),
                }
            )
            ext_meta["fulfillment"] = fulfillment
            _set_external_order_meta(ext_order, ext_meta)
            ext_order_id = int(ext_order.id) if getattr(ext_order, "id", None) is not None else None
        else:
            ext_order_id = None
        s.commit()
        s.refresh(user)
    except Exception:
        s.rollback()
        logger.error(
            "external order activation failed code=account_grant_failed correlation=%s",
            _payment_order_correlation(provider=provider, order_id=order_id),
        )
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
        except Exception:
            logger.warning(
                "referral points award failed code=referral_award_failed correlation=%s",
                _payment_order_correlation(provider=provider, order_id=order_id),
            )

    return True, "ok"


def _payment_fallback_delivery_payload(
    *,
    row: ExternalOrder,
    claim: PaymentEntitlementClaim,
    card: GiftCard,
    fulfillment: dict[str, Any],
    buyer_email: str,
    plan_label: str,
) -> dict[str, Any]:
    delivery_status = str((fulfillment.get("email_delivery") or {}).get("status") or "").strip().lower()
    fulfillment_status = str(fulfillment.get("status") or "").strip().lower()
    if fulfillment_status == "email_sent" or delivery_status in {"sent", "debug_echo"}:
        return {}
    return {
        "buyer_email": buyer_email,
        "access_key": str(card.code or "").strip().upper(),
        "order_id": str(row.order_id),
        "plan_code": str(claim.plan_code),
        "plan_label": str(plan_label or claim.plan_code),
        "days": int(claim.duration_days or 0),
    }


def _mark_payment_order_manual_review(
    *,
    row: ExternalOrder,
    meta: dict[str, Any],
    fulfillment: dict[str, Any],
    error_code: str,
) -> None:
    if str(row.status or "").strip().lower() not in {"refunded", "chargeback"}:
        row.status = "manual_review"
    fulfillment["status"] = "manual_review"
    fulfillment["error_code"] = _safe_payment_processing_error(error_code)
    meta["fulfillment"] = fulfillment
    _set_external_order_meta(row, meta)


def _issue_payment_access_key_for_order(*, provider: str, order_id: str, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    s = SessionLocal()
    try:
        row = (
            s.query(ExternalOrder)
            .filter(ExternalOrder.provider == str(provider), ExternalOrder.order_id == str(order_id))
            .with_for_update()
            .first()
        )
        if not row:
            return False, "order_not_found", {}
        meta = _external_order_meta(row)
        fulfillment = dict(meta.get("fulfillment") or {})
        existing_claim = (
            s.query(PaymentEntitlementClaim)
            .filter(
                PaymentEntitlementClaim.provider == str(provider),
                PaymentEntitlementClaim.order_id == str(order_id),
            )
            .one_or_none()
        )
        if str(row.status or "").strip().lower() in {"refunded", "chargeback"}:
            if existing_claim is not None and str(existing_claim.status or "").strip().lower() == "reversed":
                return False, "claim_reversed", {}
            return False, "order_reversed", {}
        buyer_email = str(
            existing_claim.buyer_email_norm
            if existing_claim is not None
            else (
                fulfillment.get("buyer_email")
                or meta.get("buyer_email")
                or _payload_value(payload, "buyer_email", "email", "buyerEmail")
                or ""
            )
        ).strip()
        try:
            buyer_email = validate_email_input(buyer_email)
        except InvalidEmailInputError:
            _mark_payment_order_manual_review(
                row=row,
                meta=meta,
                fulfillment=fulfillment,
                error_code="missing_buyer_email",
            )
            s.commit()
            return False, "missing_buyer_email", {}

        if existing_claim is not None:
            plan_code = str(existing_claim.plan_code or "").strip().lower()
            duration_days = max(1, int(existing_claim.duration_days or 0))
            display_plan = _resolve_plan_config(s=s, code=plan_code) or {}
            plan_label = _normalize_mojibake(str(display_plan.get("label") or plan_code).strip()) or plan_code
        else:
            plan_code = str(row.plan_code or _payload_plan_code(payload) or "").strip().lower()
            normalized_plan = _normalized_plan_payload(
                _resolve_plan_config(s=s, code=plan_code),
                fallback_code=plan_code,
            )
            if not normalized_plan:
                _mark_payment_order_manual_review(
                    row=row,
                    meta=meta,
                    fulfillment=fulfillment,
                    error_code="unsupported_plan",
                )
                s.commit()
                return False, "unsupported_plan", {}
            plan_code = str(normalized_plan["code"])
            duration_days = max(1, int(normalized_plan.get("days") or 30))
            plan_label = str(normalized_plan.get("label") or plan_code)

        if existing_claim is not None and existing_claim.account_id:
            fulfilled = mark_paid_and_fulfill_attached_claim(
                s,
                provider=provider,
                order_id=order_id,
                buyer_email=buyer_email,
                plan_code=plan_code,
                duration_days=duration_days,
                paid_at=row.paid_at or _utcnow(),
            )
            if fulfilled.code not in {"fulfilled", "already_fulfilled"}:
                if fulfilled.code in _TERMINAL_PAYMENT_FULFILLMENT_CODES:
                    _mark_payment_order_manual_review(
                        row=row,
                        meta=meta,
                        fulfillment=fulfillment,
                        error_code=fulfilled.code,
                    )
                s.commit()
                return False, fulfilled.code, {}
            now = _utcnow()
            row.status = "paid"
            row.paid_at = row.paid_at or fulfilled.claim.paid_at or now
            fulfillment.update(
                {
                    "mode": "account_claim",
                    "status": "account_extended",
                    "activated_at": _safe_iso(fulfilled.claim.fulfilled_at or now),
                }
            )
            fulfillment.pop("access_key", None)
            meta["fulfillment"] = fulfillment
            _set_external_order_meta(row, meta)
            s.commit()
            return True, fulfilled.code, {}

        claim_result = ensure_pending_claim(
            s,
            provider=provider,
            order_id=order_id,
            buyer_email=buyer_email,
            plan_code=plan_code,
            duration_days=duration_days,
            now=row.created_at,
        )
        if claim_result.code == "claim_definition_conflict":
            _mark_payment_order_manual_review(
                row=row,
                meta=meta,
                fulfillment=fulfillment,
                error_code=claim_result.code,
            )
            s.commit()
            return False, "claim_definition_conflict", {}
        paid_result = mark_payment_entitlement_paid(
            s,
            provider=provider,
            order_id=order_id,
            paid_at=row.paid_at or _utcnow(),
        )
        if paid_result.code in {"claim_reversed", "manual_review"}:
            if paid_result.code == "manual_review":
                _mark_payment_order_manual_review(
                    row=row,
                    meta=meta,
                    fulfillment=fulfillment,
                    error_code=paid_result.code,
                )
            s.commit()
            return False, paid_result.code, {}
        claim = paid_result.claim
        if claim.account_id:
            s.commit()
            return _issue_payment_access_key_for_order(provider=provider, order_id=order_id, payload=payload)

        if claim.fallback_gift_card_id:
            fallback_result = ensure_fallback_gift_card(
                s,
                provider=provider,
                order_id=order_id,
                gift_code="unused-existing-fallback",
                now=claim.paid_at,
            )
            if fallback_result.code != "fallback_already_exists":
                if fallback_result.code in _TERMINAL_PAYMENT_FULFILLMENT_CODES:
                    _mark_payment_order_manual_review(
                        row=row,
                        meta=meta,
                        fulfillment=fulfillment,
                        error_code=fallback_result.code,
                    )
                s.commit()
                return False, fallback_result.code, {}
            claim = fallback_result.claim
            card = (
                s.query(GiftCard)
                .filter(GiftCard.id == int(claim.fallback_gift_card_id))
                .with_for_update()
                .one_or_none()
            )
            if card is None:
                _mark_payment_order_manual_review(
                    row=row,
                    meta=meta,
                    fulfillment=fulfillment,
                    error_code="fallback_missing",
                )
                s.commit()
                return False, "fallback_missing", {}
            fulfillment.pop("access_key", None)
            meta["fulfillment"] = fulfillment
            _set_external_order_meta(row, meta)
            row.status = "paid"
            row.paid_at = row.paid_at or claim.paid_at
            row.plan_code = str(claim.plan_code)
            delivery_payload = _payment_fallback_delivery_payload(
                row=row,
                claim=claim,
                card=card,
                fulfillment=fulfillment,
                buyer_email=buyer_email,
                plan_label=plan_label,
            )
            if delivery_payload and not delivery_payload.get("access_key"):
                record_payment_entitlement_claim_error(
                    s,
                    provider=provider,
                    order_id=order_id,
                    error_code="fallback_missing",
                    now=_utcnow(),
                )
                s.commit()
                return False, "fallback_missing", {}
            s.commit()
            return True, "claim_fallback_already_durable", delivery_payload

        existing_key = str(fulfillment.get("access_key") or "").strip().upper()
        key_code = existing_key or _generate_gift_code_for_admin(s)
        fallback_result = ensure_fallback_gift_card(
            s,
            provider=provider,
            order_id=order_id,
            gift_code=key_code,
            now=claim.paid_at,
        )
        if fallback_result.code not in {
            "fallback_created",
            "fallback_already_exists",
            "fallback_linked_existing",
        }:
            if fallback_result.code in _TERMINAL_PAYMENT_FULFILLMENT_CODES:
                _mark_payment_order_manual_review(
                    row=row,
                    meta=meta,
                    fulfillment=fulfillment,
                    error_code=fallback_result.code,
                )
            s.commit()
            return False, fallback_result.code, {}
        claim = fallback_result.claim
        card = (
            s.query(GiftCard)
            .filter(GiftCard.id == int(claim.fallback_gift_card_id or 0))
            .with_for_update()
            .one_or_none()
        )
        if card is None or int(claim.fallback_gift_card_id or 0) != int(card.id):
            record_payment_entitlement_claim_error(
                s,
                provider=provider,
                order_id=order_id,
                error_code="fallback_missing",
                now=_utcnow(),
            )
            _mark_payment_order_manual_review(
                row=row,
                meta=meta,
                fulfillment=fulfillment,
                error_code="fallback_missing",
            )
            s.commit()
            return False, "fallback_missing", {}
        key_code = str(card.code or "").strip().upper()
        if not key_code:
            record_payment_entitlement_claim_error(
                s,
                provider=provider,
                order_id=order_id,
                error_code="fallback_missing",
                now=_utcnow(),
            )
            _mark_payment_order_manual_review(
                row=row,
                meta=meta,
                fulfillment=fulfillment,
                error_code="fallback_missing",
            )
            s.commit()
            return False, "fallback_missing", {}
        reason = "access_key_relinked" if existing_key else "access_key_issued"

        prior_delivery_status = str((fulfillment.get("email_delivery") or {}).get("status") or "").strip().lower()
        already_delivered = bool(
            existing_key
            and (
                str(fulfillment.get("status") or "").strip().lower() == "email_sent"
                or prior_delivery_status in {"sent", "debug_echo"}
            )
        )
        fulfillment.pop("access_key", None)
        if already_delivered:
            row.status = "paid"
            row.paid_at = row.paid_at or claim.paid_at or _utcnow()
            row.plan_code = str(claim.plan_code)
            meta["fulfillment"] = fulfillment
            _set_external_order_meta(row, meta)
            s.commit()
            return True, reason, {}

        now = _utcnow()
        row.status = "paid"
        row.paid_at = row.paid_at or now
        row.plan_code = str(claim.plan_code)
        fulfillment.update(
            {
                "mode": "access_key_email",
                "status": "email_pending",
                "buyer_email": buyer_email,
                "access_key_issued_at": _safe_iso(now),
            }
        )
        meta["fulfillment"] = fulfillment
        _set_external_order_meta(row, meta)
        s.commit()
        return True, reason, {
            "buyer_email": buyer_email,
            "access_key": key_code,
            "order_id": str(row.order_id),
            "plan_code": str(claim.plan_code),
            "plan_label": plan_label,
            "days": int(claim.duration_days or 0),
        }
    except Exception:
        s.rollback()
        logger.error(
            "payment access key issue failed code=access_key_issue_failed correlation=%s",
            _payment_order_correlation(provider=provider, order_id=order_id),
        )
        return False, "access_key_issue_failed", {}
    finally:
        s.close()


def _record_access_key_delivery_result(*, provider: str, order_id: str, delivery: dict[str, Any]) -> bool:
    s = SessionLocal()
    try:
        row = (
            s.query(ExternalOrder)
            .filter(ExternalOrder.provider == str(provider), ExternalOrder.order_id == str(order_id))
            .with_for_update()
            .first()
        )
        if not row:
            return False
        meta = _external_order_meta(row)
        fulfillment = dict(meta.get("fulfillment") or {})
        reversal_status = str(row.status or "").strip().lower() in {"refunded", "chargeback"}
        prior_delivery = fulfillment.get("email_delivery") if isinstance(fulfillment.get("email_delivery"), dict) else {}
        prior_status = str(prior_delivery.get("status") or "").strip().lower()
        if str(fulfillment.get("status") or "").strip().lower() == "email_sent" or prior_status in {"sent", "debug_echo"}:
            s.commit()
            return True
        raw_status = str((delivery or {}).get("status") or "").strip().lower()
        delivery_status = raw_status if raw_status in {
            "sent",
            "debug_echo",
            "not_configured",
            "delivery_error",
            "failed",
        } else "delivery_error"
        raw_mode = str((delivery or {}).get("mode") or "").strip().lower()
        delivery_mode = raw_mode if raw_mode in {"webhook", "not_configured"} else None
        raw_http_status = _safe_int((delivery or {}).get("http_status"))
        http_status = raw_http_status if raw_http_status is not None and 100 <= raw_http_status <= 599 else None
        if delivery_status in {"sent", "debug_echo"}:
            error_code = None
        elif delivery_status == "not_configured":
            error_code = "delivery_not_configured"
        elif http_status is not None and http_status >= 500:
            error_code = "delivery_upstream_5xx"
        elif http_status is not None and http_status >= 400:
            error_code = "delivery_upstream_4xx"
        else:
            error_code = "delivery_not_sent"
        fulfillment["email_delivery"] = {
            "status": delivery_status,
            "mode": delivery_mode,
            "http_status": http_status,
            "error_code": error_code,
        }
        if reversal_status:
            pass
        elif delivery_status in {"sent", "debug_echo"}:
            fulfillment["status"] = "email_sent"
        elif delivery_status:
            fulfillment["status"] = "email_delivery_error"
        meta["fulfillment"] = fulfillment
        _set_external_order_meta(row, meta)
        s.commit()
        return True
    except Exception:
        s.rollback()
        logger.error(
            "access key delivery evidence failed code=delivery_evidence_failed correlation=%s",
            _payment_order_correlation(provider=provider, order_id=order_id),
        )
        return False
    finally:
        s.close()


def _finalize_paid_event_after_delivery(
    *,
    provider: str,
    order_id: str,
    event_type: str,
    external_id: str,
    delivery_succeeded: bool,
) -> tuple[bool, str]:
    s = SessionLocal()
    try:
        event = (
            s.query(ExternalPaymentEvent)
            .filter(
                ExternalPaymentEvent.provider == str(provider),
                ExternalPaymentEvent.event_type == str(event_type),
                ExternalPaymentEvent.external_id == str(external_id),
            )
            .with_for_update()
            .one_or_none()
        )
        if event is None:
            return False, "delivery_evidence_failed"
        order = (
            s.query(ExternalOrder)
            .filter(ExternalOrder.provider == str(provider), ExternalOrder.order_id == str(order_id))
            .with_for_update()
            .populate_existing()
            .one_or_none()
        )
        if order is None:
            return False, "delivery_evidence_failed"

        terminal_reason = ""
        if str(order.status or "").strip().lower() in {"refunded", "chargeback"}:
            terminal_reason = "claim_reversed"
            event.processed_ok = True
        elif delivery_succeeded:
            event.processed_ok = True
        else:
            terminal_reason = "access_key_email_delivery_error"
            event.processed_ok = False

        if terminal_reason:
            try:
                stored = json.loads(str(event.payload_json or "{}"))
                if not isinstance(stored, dict):
                    stored = {}
            except Exception:
                stored = {}
            stored["_pokrov_processing_error"] = _safe_payment_processing_error(terminal_reason)
            event.payload_json = _serialize_payment_event_payload(stored)
        s.commit()
        return True, terminal_reason
    except Exception:
        s.rollback()
        logger.error(
            "payment delivery completion failed code=callback_completion_failed correlation=%s",
            _payment_order_correlation(provider=provider, order_id=order_id),
        )
        return False, "delivery_evidence_failed"
    finally:
        s.close()


def _record_payment_reversal_operator_action(
    *,
    provider: str,
    order_id: str,
    event_type: str,
    payload: dict[str, Any],
    reason: str = "provider_reversal",
) -> tuple[bool, str]:
    normalized_provider = _normalize_provider(provider)
    normalized_event = re.sub(r"[^a-z_]", "", str(event_type or "").strip().lower())[:32] or "reversal"
    tg_id: int | None = None
    reconciled = False
    result_code = "order_not_found"
    s = SessionLocal()
    try:
        row = (
            s.query(ExternalOrder)
            .filter(ExternalOrder.provider == normalized_provider, ExternalOrder.order_id == str(order_id))
            .with_for_update()
            .first()
        )
        if row:
            if normalized_event == "chargeback":
                row.status = "chargeback"
            elif str(row.status or "").strip().lower() != "chargeback":
                row.status = "refunded"
            tg_id = int(row.tg_id) if row.tg_id is not None else None
            reversal_reason = str(reason or normalized_event or "provider_reversal")[:64]
            try:
                reversal = reverse_payment_entitlement_claim(
                    s,
                    provider=normalized_provider,
                    order_id=str(order_id),
                    reason=reversal_reason,
                    reversed_at=_utcnow(),
                )
                reconciled = reversal.code in {"reversed", "already_reversed"}
                result_code = reversal.code
            except PaymentEntitlementNotFoundError:
                grant = (
                    s.query(EntitlementGrant)
                    .filter(
                        EntitlementGrant.provider == normalized_provider,
                        EntitlementGrant.external_order_id == str(order_id),
                        EntitlementGrant.source == "provider_payment",
                    )
                    .with_for_update()
                    .one_or_none()
                )
                if grant is not None:
                    if grant.reversed_at is None:
                        reversed_at = _utcnow()
                        grant.status = "reversed"
                        grant.reversed_at = reversed_at
                        grant.reversal_reason = reversal_reason
                        grant.updated_at = reversed_at
                        rebuild_account_entitlement_projection(
                            s,
                            account_id=str(grant.account_id),
                            now=reversed_at,
                        )
                        result_code = "reversed"
                    else:
                        result_code = "already_reversed"
                    reconciled = True
                else:
                    result_code = "grant_not_found"
            meta = _external_order_meta(row)
            fulfillment = dict(meta.get("fulfillment") or {})
            fulfillment["status"] = "reversed" if reconciled else "reversal_pending_operator_action"
            meta["fulfillment"] = fulfillment
            meta["reversal"] = {
                "event_type": normalized_event,
                "provider": normalized_provider,
                "order_id": str(order_id or ""),
                "reason": str(reason or "provider_reversal")[:120],
                "operator_action_required": not reconciled,
                "reconciliation_status": result_code,
                "recorded_at": _safe_iso(_utcnow()),
                "external_id": str(_callback_ids(normalized_provider, payload, b"")[1] or "")[:160],
            }
            _set_external_order_meta(row, meta)
            s.commit()
        else:
            s.rollback()
    except Exception:
        s.rollback()
        result_code = "reversal_persistence_failed"
        logger.error(
            "payment reversal persistence failed code=reversal_persistence_failed correlation=%s",
            _payment_order_correlation(provider=provider, order_id=order_id),
        )
    finally:
        s.close()
    _record_security_event(
        "payment_reversal_reconciled" if reconciled else "payment_reversal_pending",
        scope="payments",
        subject=f"{normalized_provider}:{str(order_id or '')[:96]}",
        reason=normalized_event,
        meta={"operator_action_required": not reconciled, "reconciliation_status": result_code},
    )
    if tg_id:
        track_event(
            tg_id=int(tg_id),
            event_name="payment_reversal_pending",
            source="payment_callback",
            meta={
                "provider": normalized_provider,
                "order_id": str(order_id or "")[:96],
                "event_type": normalized_event,
                "reconciliation_status": result_code,
            },
        )
    return reconciled, result_code


def _fulfill_external_paid_order(*, provider: str, order_id: str, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    s = SessionLocal()
    try:
        ext_order = (
            s.query(ExternalOrder)
            .filter(ExternalOrder.provider == str(provider), ExternalOrder.order_id == str(order_id))
            .first()
        ) if order_id else None
        if ext_order is None:
            return False, "order_not_found", {}
        tg_id = int(ext_order.tg_id) if ext_order.tg_id is not None else None
    finally:
        s.close()

    if tg_id is not None and int(tg_id) > 0:
        activated, reason = _apply_external_paid_order(provider=provider, order_id=order_id, payload=payload)
        return activated, reason, {"tg_id": int(tg_id)} if activated else {}
    return _issue_payment_access_key_for_order(provider=provider, order_id=order_id, payload=payload)


async def _handle_payment_callback(*, provider: str, event_type: str, request: Request) -> dict[str, Any]:
    p = _normalize_provider(provider)
    et = re.sub(r"[^a-z_]", "", str(event_type or "").strip().lower())
    if p not in PAYMENT_PROVIDER_WHITELIST:
        raise HTTPException(status_code=404, detail="Unsupported provider")
    if et not in {"result", "refund", "chargeback"}:
        raise HTTPException(status_code=400, detail="Unsupported event type")
    _enforce_beta_rate_limit("payment_callback", request, identity=f"{p}:{et}")

    payload, raw = await _read_callback_payload(request)
    if p == "freekassa":
        client_ip = _fk_client_ip(request)
        if not _is_ip_allowed(client_ip, FK_NOTIFY_IP_ALLOWLIST):
            logger.warning("freekassa callback blocked by ip allowlist: ip=%s", client_ip)
            raise HTTPException(status_code=403, detail="Callback IP is not allowed")
    if p == "lavatop":
        allowlist = [item.strip() for item in (os.getenv("LAVATOP_WEBHOOK_IP_ALLOWLIST") or "").split(",") if item.strip()]
        client_ip = _request_client_ip(request)
        if allowlist and not _is_ip_allowed(client_ip, allowlist):
            if _is_loopback_ip(client_ip) and _lavatop_webhook_auth_configured():
                logger.warning(
                    "lavatop callback arrived through local reverse proxy; relying on webhook auth after allowlist miss: ip=%s",
                    client_ip,
                )
            else:
                logger.warning("lavatop callback blocked by ip allowlist: ip=%s", client_ip)
                raise HTTPException(status_code=403, detail="Callback IP is not allowed")
    order_id, external_id = _callback_ids(p, payload, raw)
    signature_ok, signature_reason = _verify_callback_signature(provider=p, payload=payload, raw=raw, request=request)
    callback_status = _status_from_event(et, payload, signature_ok=signature_ok, provider=p)
    validation_reason = ""
    if signature_ok and et == "result" and callback_status == "paid":
        callback_valid, validation_reason = _validate_paid_callback_against_order(provider=p, order_id=order_id, payload=payload)
        if not callback_valid:
            payload = dict(payload)
            payload["_pokrov_validation_error"] = validation_reason
            callback_status = "manual_review"
    requires_durable_completion = bool(
        signature_ok
        and (
            (et == "result" and callback_status == "paid")
            or et in {"refund", "chargeback"}
        )
    )
    processed_ok = bool(
        signature_ok
        and callback_status != "pending_verification"
        and not requires_durable_completion
    )
    duplicate, persist_ok = _record_external_payment_event(
        provider=p,
        event_type=et,
        external_id=external_id,
        order_id=order_id,
        payload=payload,
        signature_ok=signature_ok,
        processed_ok=processed_ok,
        status=callback_status,
    )
    if not persist_ok:
        raise HTTPException(status_code=503, detail="Payment callback persistence is retryable")

    if not signature_ok:
        _record_security_event(
            "payment_callback_invalid_signature",
            scope="payment_callback",
            client_ip=_request_client_ip(request),
            subject=f"{p}:{et}",
            reason=signature_reason,
            meta={"order_id": order_id, "external_id": external_id},
        )
        _enforce_beta_rate_limit("payment_callback_invalid", request, identity=f"{p}:{signature_reason}")
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
    if (not duplicate) and signature_ok and et in {"refund", "chargeback"}:
        try:
            reversed_ok, reversal_code = _record_payment_reversal_operator_action(
                provider=p,
                order_id=order_id,
                event_type=et,
                payload=payload,
                reason=callback_status,
            )
        except Exception:
            logger.error(
                "payment reversal failed code=reversal_persistence_failed correlation=%s",
                _payment_order_correlation(provider=p, order_id=order_id),
            )
            reversed_ok, reversal_code = False, "reversal_persistence_failed"
        if not reversed_ok:
            if reversal_code in _TERMINAL_PAYMENT_REVERSAL_CODES:
                if not _complete_external_payment_event(
                    provider=p,
                    event_type=et,
                    external_id=external_id,
                    processed_ok=True,
                    error_code=reversal_code,
                ):
                    raise HTTPException(status_code=503, detail="Payment callback completion is retryable")
                activation_reason = reversal_code
            else:
                _complete_external_payment_event(
                    provider=p,
                    event_type=et,
                    external_id=external_id,
                    processed_ok=False,
                    error_code=reversal_code,
                )
                raise HTTPException(status_code=503, detail="Payment reversal is retryable")
        elif not _complete_external_payment_event(
            provider=p,
            event_type=et,
            external_id=external_id,
            processed_ok=True,
        ):
            raise HTTPException(status_code=503, detail="Payment callback completion is retryable")

    if (not duplicate) and signature_ok and et == "result" and callback_status == "paid":
        activated, activation_reason, fulfillment = _fulfill_external_paid_order(provider=p, order_id=order_id, payload=payload)
        if not activated:
            safe_reason = _safe_payment_processing_error(activation_reason or "durable_fulfillment_failed")
            if safe_reason in _TERMINAL_PAYMENT_FULFILLMENT_CODES:
                if not _complete_external_payment_event(
                    provider=p,
                    event_type=et,
                    external_id=external_id,
                    processed_ok=True,
                    error_code=safe_reason,
                ):
                    raise HTTPException(status_code=503, detail="Payment callback completion is retryable")
                activation_reason = safe_reason
            else:
                _record_payment_entitlement_retry_error(
                    provider=p,
                    order_id=order_id,
                    error_code=safe_reason,
                )
                _complete_external_payment_event(
                    provider=p,
                    event_type=et,
                    external_id=external_id,
                    processed_ok=False,
                    error_code=safe_reason,
                )
                raise HTTPException(status_code=503, detail="Payment fulfillment is retryable")
        else:
            delivery_finalized = False
            if fulfillment.get("access_key") and fulfillment.get("buyer_email"):
                try:
                    delivery = await deliver_payment_access_key(
                        email=str(fulfillment["buyer_email"]),
                        access_key=str(fulfillment["access_key"]),
                        order_id=str(fulfillment.get("order_id") or order_id),
                        plan_code=str(fulfillment.get("plan_code") or ""),
                        plan_label=str(fulfillment.get("plan_label") or ""),
                        days=int(fulfillment.get("days") or 0),
                    )
                except Exception:
                    delivery = {"status": "delivery_error", "mode": "webhook"}
                evidence_ok = _record_access_key_delivery_result(provider=p, order_id=order_id, delivery=delivery)
                if not evidence_ok:
                    _complete_external_payment_event(
                        provider=p,
                        event_type=et,
                        external_id=external_id,
                        processed_ok=False,
                        error_code="delivery_evidence_failed",
                    )
                    raise HTTPException(status_code=503, detail="Payment delivery evidence is retryable")
                delivery_ok = str(delivery.get("status") or "").strip().lower() in {"sent", "debug_echo"}
                completion_ok, completion_reason = _finalize_paid_event_after_delivery(
                    provider=p,
                    order_id=order_id,
                    event_type=et,
                    external_id=external_id,
                    delivery_succeeded=delivery_ok,
                )
                if not completion_ok:
                    raise HTTPException(status_code=503, detail="Payment callback completion is retryable")
                delivery_finalized = True
                if completion_reason == "claim_reversed":
                    activated = False
                    activation_reason = completion_reason
                    fulfillment = {}
                elif completion_reason:
                    raise HTTPException(status_code=503, detail="Payment access delivery is retryable")
            if (not delivery_finalized) and not _complete_external_payment_event(
                provider=p,
                event_type=et,
                external_id=external_id,
                processed_ok=True,
            ):
                raise HTTPException(status_code=503, detail="Payment callback completion is retryable")
            if activated and fulfillment.get("access_key") and fulfillment.get("buyer_email"):
                activation_reason = activation_reason or "access_key_email_sent"
            tg_id = fulfillment.get("tg_id")
            if tg_id is not None:
                try:
                    sync_ok = bool(await _sync_user_after_paid_purchase(int(tg_id)))
                except Exception:
                    sync_ok = False
                try:
                    await _notify_telegram_paid_access_ready(
                        tg_id=int(tg_id),
                        sync_ok=bool(sync_ok),
                    )
                except Exception:
                    logger.warning(
                        "telegram paid access notification failed code=telegram_notification_failed correlation=%s",
                        _payment_order_correlation(provider=p, order_id=order_id),
                    )
    elif (not duplicate) and signature_ok and et == "result":
        activation_reason = validation_reason or callback_status

    return {
        "ok": bool(signature_ok and persist_ok),
        "provider": p,
        "event_type": et,
        "order_id": order_id or None,
        "external_id": external_id,
        "status": callback_status,
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


async def _telegram_send_message(
    chat_id: int,
    text: str,
    *,
    parse_mode: str | None = None,
    reply_markup: dict[str, Any] | None = None,
    disable_web_page_preview: bool | None = None,
) -> bool:
    token = _current_bot_token()
    if not token:
        return False
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": int(chat_id), "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if disable_web_page_preview is not None:
        payload["disable_web_page_preview"] = bool(disable_web_page_preview)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return False
                body = await resp.json()
                return bool(body.get("ok"))
    except Exception:
        return False


def _telegram_paid_access_keyboard() -> dict[str, Any]:
    rows: list[list[dict[str, Any]]] = [
        [{"text": "📲 Подключить устройство", "callback_data": "instruction"}],
        [{"text": "🌐 Открыть кабинет", "web_app": {"url": _public_webapp_url()}}],
        [{"text": "🔗 Ручная ссылка / QR", "callback_data": "show_key"}],
    ]
    if SUPPORT_USERNAME:
        rows.append([{"text": "💬 Поддержка", "url": f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new"}])
    return {"inline_keyboard": rows}


async def _notify_telegram_paid_access_ready(*, tg_id: int, sync_ok: bool) -> bool:
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            return False
        if not str(getattr(user, "sub_token", "") or "").strip():
            user.sub_token = _generate_sub_token()
            s.commit()
            s.refresh(user)
        expiry = user.expiry_at.strftime("%d.%m.%Y") if user.expiry_at else "—"
    finally:
        s.close()

    if sync_ok:
        text = (
            "✅ *Оплата прошла, доступ готов.*\n\n"
            f"📅 До: `{expiry}`\n\n"
            "Лучший путь: откройте POKROV, войдите тем же способом и нажмите «Подключить».\n\n"
            "Если приложения нет под рукой, нажмите «Ручная ссылка / QR» ниже. Я покажу её отдельно и напомню, как использовать безопасно."
        )
    else:
        text = (
            "✅ *Оплата прошла.*\n\n"
            f"📅 До: `{expiry}`\n\n"
            "Доступ записан в системе, но авто-синхронизация с узлами заняла больше обычного. "
            "Попробуйте открыть POKROV или кабинет через минуту; если подключение не заработает, напишите в поддержку.\n\n"
            "Ручная ссылка доступна по кнопке ниже, но используйте её только как запасной вариант."
        )
    return await _telegram_send_message(
        int(tg_id),
        text,
        parse_mode="Markdown",
        reply_markup=_telegram_paid_access_keyboard(),
        disable_web_page_preview=True,
    )


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


def _ticket_message_row(msg, *, include_media: bool = True) -> dict[str, Any]:
    row = {
        "id": msg.id,
        "ticket_id": msg.ticket_id,
        "sender_tg_id": msg.sender_tg_id,
        "sender_role": msg.sender_role,
        "body": msg.body,
        "created_at": _safe_iso(msg.created_at),
    }
    if include_media:
        row.update(
            {
                "media_type": getattr(msg, "media_type", None),
                "media_file_id": getattr(msg, "media_file_id", None),
                "media_payload": getattr(msg, "media_payload", None),
            }
        )
    return row


_TICKET_ATTACHMENT_URL_RE = re.compile(
    r"^/api/tickets/attachments/\d{8}-[A-Za-z0-9]{8,64}\.(?:png|jpg|jpeg|webp|pdf|txt)$"
)


def _safe_ticket_attachment(msg) -> dict[str, Any] | None:
    media_type = str(getattr(msg, "media_type", "") or "").strip().lower()[:32]
    media_file_id = str(getattr(msg, "media_file_id", "") or "").strip()
    payload = _json_obj(getattr(msg, "media_payload", None))
    if not (media_type or media_file_id or payload):
        return None

    raw_name = str(payload.get("name") or payload.get("file_name") or "").strip()
    name = _sanitize_ticket_upload_name(raw_name) if raw_name else None
    raw_content_type = str(
        payload.get("content_type") or payload.get("mime_type") or ""
    ).strip().lower()[:80]
    content_type = (
        raw_content_type
        if re.fullmatch(
            r"[a-z0-9][a-z0-9.+-]*/[a-z0-9][a-z0-9.+-]*",
            raw_content_type,
        )
        else None
    )
    try:
        parsed_size = int(payload.get("size") or payload.get("file_size") or 0)
        size_bytes = parsed_size if 0 < parsed_size <= 10 * 1024 * 1024 * 1024 else 0
    except (TypeError, ValueError):
        size_bytes = 0
    raw_url = str(payload.get("url") or "").strip()
    download_url = raw_url if _TICKET_ATTACHMENT_URL_RE.fullmatch(raw_url) else None
    attachment_kind = str(payload.get("kind") or media_type).strip().lower()
    safe_type = {
        "photo": "image",
        "image": "image",
        "document": "file",
        "file": "file",
        "video": "video",
        "audio": "audio",
        "voice": "audio",
    }.get(attachment_kind, "attachment")
    return {
        "type": safe_type,
        "name": name,
        "content_type": content_type,
        "size_bytes": size_bytes or None,
        "download_url": download_url,
    }


def _ticket_message_detail_row(msg) -> dict[str, Any]:
    return {
        "id": msg.id,
        "ticket_id": msg.ticket_id,
        "sender_tg_id": msg.sender_tg_id,
        "sender_role": msg.sender_role,
        "body": str(msg.body or "")[:2000],
        "attachment": _safe_ticket_attachment(msg),
        "created_at": _safe_iso(msg.created_at),
    }


def _ticket_operator_presence(ticket) -> str:
    status = str(getattr(ticket, "status", "") or "").strip().lower()
    if status == STATUS_CLOSED:
        return "offline"
    if getattr(ticket, "assigned_admin_tg_id", None):
        return "online"
    return "away"


def _ticket_unread_for_user(messages: list | None) -> int:
    rows = list(messages or [])
    last_user_index = -1
    for index, msg in enumerate(rows):
        if str(getattr(msg, "sender_role", "") or "").strip().lower() == "user":
            last_user_index = index
    unread = 0
    for msg in rows[last_user_index + 1 :]:
        if str(getattr(msg, "sender_role", "") or "").strip().lower() in {"admin", "assistant"}:
            unread += 1
    return unread


def _ticket_summary_row(ticket, messages: list | None = None) -> dict[str, Any]:
    rows = messages if messages is not None else []
    last_message = rows[-1] if rows else None
    last_message_preview = (str(getattr(last_message, "body", "") or "").strip()[:200] if last_message else "")
    has_attachment = bool(last_message and _safe_ticket_attachment(last_message))
    if not last_message_preview and has_attachment:
        last_message_preview = "Вложение"
    return {
        "id": ticket.id,
        "user_tg_id": ticket.user_tg_id,
        "status": ticket.status,
        "status_title": _ticket_status_title(ticket.status),
        "subject": ticket.subject,
        "created_at": _safe_iso(ticket.created_at),
        "updated_at": _safe_iso(ticket.updated_at),
        "closed_at": _safe_iso(ticket.closed_at),
        "last_message_preview": last_message_preview,
        "has_attachment": has_attachment,
        "operatorPresence": _ticket_operator_presence(ticket),
        "operatorTyping": False,
        "unreadForUser": _ticket_unread_for_user(rows),
        "slaHint": None if str(ticket.status or "").strip().lower() == STATUS_CLOSED else "support_queue",
    }


def _ticket_detail_row(ticket, messages: list | None = None) -> dict[str, Any]:
    rows = list(messages or [])
    return {
        **_ticket_summary_row(ticket, rows),
        "messages": [_ticket_message_detail_row(message) for message in rows],
    }


def _ticket_row(ticket, messages: list | None = None, *, include_media: bool = True) -> dict[str, Any]:
    rows = list(messages or [])
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
        "messages": [_ticket_message_row(message, include_media=include_media) for message in rows],
        "last_message_preview": ((last_message.body or "").strip()[:200] if last_message else ""),
        "operatorPresence": _ticket_operator_presence(ticket),
        "operatorTyping": False,
        "unreadForUser": _ticket_unread_for_user(rows),
        "slaHint": None if str(ticket.status or "").strip().lower() == STATUS_CLOSED else "support_queue",
    }


def _load_ticket_row(ticket_id: int, *, message_limit: int = 100, include_media: bool = True) -> dict[str, Any]:
    s = SessionLocal()
    try:
        ticket = get_ticket_by_id(s, int(ticket_id))
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        msgs = list_ticket_messages(s, ticket.id, limit=max(1, min(int(message_limit), 100)))
        return _ticket_row(ticket, msgs, include_media=include_media)
    finally:
        s.close()


async def _maybe_append_support_ai_reply(
    *,
    ticket_id: int,
    user_tg_id: int,
    text: str,
    has_attachment: bool = False,
) -> bool:
    if has_attachment or not SUPPORT_AI_CONFIG.enabled:
        return False
    body = (text or "").strip()
    if not body:
        return False

    if not SUPPORT_AGENT_SERVICE.settings.agent_enabled:
        now = time.monotonic()
        min_interval = max(0.0, float(SUPPORT_AI_CONFIG.min_interval_seconds))
        last = support_ai_last_reply_at.get(int(user_tg_id), 0.0)
        if min_interval and now - last < min_interval:
            return False
        support_ai_last_reply_at[int(user_tg_id)] = now

    result = await SUPPORT_AGENT_SERVICE.generate(
        surface="ticket",
        authenticated_owner_id=str(int(user_tg_id)),
        message=body,
        ticket_id=int(ticket_id),
    )
    reply = str(result.reply or "").strip()
    if not reply:
        return False

    s = SessionLocal()
    try:
        ticket = get_ticket_by_id(s, int(ticket_id))
        if not ticket or int(ticket.user_tg_id) != int(user_tg_id):
            return False
        add_ticket_message(
            s,
            ticket_id=ticket.id,
            sender_tg_id=0,
            sender_role="assistant",
            body=reply,
        )
        s.commit()
        return True
    except Exception:
        try:
            s.rollback()
        except Exception:
            pass
        logger.warning("support AI ticket append failed code=support_reply_persist_error")
        return False
    finally:
        try:
            s.close()
        except Exception:
            logger.warning("support AI ticket session cleanup failed code=support_reply_cleanup_error")


def _add_admin_audit(
    session,
    actor_tg_id: int,
    action: str,
    target_tg_id: int | None = None,
    meta: dict[str, Any] | None = None,
) -> AdminAudit:
    row = AdminAudit(
        actor_tg_id=int(actor_tg_id),
        action=(action or "").strip()[:64],
        target_tg_id=int(target_tg_id) if target_tg_id is not None else None,
        meta=json.dumps(meta or {}, ensure_ascii=False, separators=(",", ":"))[:2000],
    )
    session.add(row)
    session.flush()
    return row


def _audit_admin(*, actor_tg_id: int, action: str, target_tg_id: int | None = None, meta: dict[str, Any] | None = None) -> None:
    s = SessionLocal()
    try:
        _add_admin_audit(
            s,
            actor_tg_id=actor_tg_id,
            action=action,
            target_tg_id=target_tg_id,
            meta=meta,
        )
        s.commit()
    except Exception:
        s.rollback()
    finally:
        s.close()


def _sanitize_ticket_upload_name(filename: str | None) -> str:
    raw = Path(str(filename or "").strip()).name
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "_", raw).strip(" ._")
    return cleaned[:120] or "attachment"


async def _read_limited_request_body(request: Request, *, max_bytes: int, scope: str) -> bytes:
    content_length_raw = str(request.headers.get("content-length") or "").strip()
    if content_length_raw:
        try:
            if int(content_length_raw) > int(max_bytes):
                raise HTTPException(status_code=413, detail=f"{scope} body is too large")
        except HTTPException:
            raise
        except Exception:
            pass
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        if not chunk:
            continue
        total += len(chunk)
        if total > int(max_bytes):
            raise HTTPException(status_code=413, detail=f"{scope} body is too large")
        chunks.append(chunk)
    return b"".join(chunks)


def _support_upload_reject_reason(exc: HTTPException) -> str:
    detail = str(exc.detail or "").strip().lower()
    if "body is too large" in detail:
        return "body_too_large"
    if "pending attachment byte quota" in detail:
        return "pending_bytes_quota"
    if "pending attachment quota" in detail:
        return "pending_count_quota"
    if "unsupported attachment type" in detail:
        return "unsupported_type"
    if "attachment is empty" in detail:
        return "empty_attachment"
    if "attachment is too large" in detail:
        return "attachment_too_large"
    return f"http_{int(exc.status_code)}"
_RU_MANIFEST_PATH = "/api/internal/probes/ru-origin/manifest"
_RU_RUNS_PATH = "/api/internal/probes/ru-origin/runs"
_RU_HEARTBEAT_PATH = "/api/internal/probes/ru-origin/heartbeat"
_RELEASE_CANDIDATES_PATH = "/api/internal/releases/candidates"
_RU_RUN_MAX_BODY_BYTES = 512 * 1024
_RU_HEARTBEAT_MAX_BODY_BYTES = 64 * 1024
_RELEASE_EVIDENCE_MAX_BODY_BYTES = 256 * 1024
_RU_CORRELATION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class _RuProbeHttpError(RuntimeError):
    def __init__(self, status_code: int, code: str) -> None:
        self.status_code = int(status_code)
        self.code = str(code)
        super().__init__(self.code)


def _ru_probe_now() -> datetime:
    return datetime.now(timezone.utc)


def _ru_probe_correlation_id(request: Request) -> str:
    supplied = str(request.headers.get("x-correlation-id") or "")
    if _RU_CORRELATION_RE.fullmatch(supplied) is not None:
        return supplied
    return uuid.uuid4().hex


def _ru_probe_headers(request: Request) -> dict[str, str]:
    required = {
        "x-internal-key-id",
        "x-internal-timestamp",
        "x-internal-nonce",
        "x-internal-signature",
    }
    headers: dict[str, str] = {}
    for raw_name, raw_value in request.scope.get("headers", []):
        name = raw_name.decode("latin-1").lower()
        if name not in required:
            continue
        if name in headers:
            raise InternalAuthError(401, "malformed_auth_header")
        headers[name] = raw_value.decode("latin-1")
    return headers


def _require_exact_ru_probe_route(
    request: Request,
    expected_path: str,
) -> None:
    expected_raw_path = expected_path.encode("ascii")
    if (
        request.scope.get("path") != expected_path
        or request.scope.get("raw_path") != expected_raw_path
        or request.scope.get("query_string", b"") != b""
    ):
        raise InternalAuthError(400, "invalid_signed_path")


def _ru_probe_unique_json_object(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate JSON member")
        result[name] = value
    return result


def _ru_probe_reject_json_constant(_value: str) -> object:
    raise ValueError("non-finite JSON number")


def _ru_probe_json(raw_body: bytes) -> object:
    if not raw_body:
        raise _RuProbeHttpError(422, "invalid_payload")
    try:
        return json.loads(
            raw_body.decode("utf-8"),
            object_pairs_hook=_ru_probe_unique_json_object,
            parse_constant=_ru_probe_reject_json_constant,
        )
    except (UnicodeError, ValueError, RecursionError):
        raise _RuProbeHttpError(422, "invalid_payload") from None


def _ru_probe_error_response(
    *,
    status_code: int,
    code: str,
    correlation_id: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=int(status_code),
        content={
            "code": str(code)[:64],
            "correlation_id": correlation_id,
        },
    )


def _ru_probe_auth_error(error: InternalAuthError) -> tuple[int, str]:
    if error.status_code == 409 and error.code == "replayed_nonce":
        return 409, "replayed_nonce"
    if error.status_code == 413:
        return 413, "request_too_large"
    if error.status_code == 403:
        return 403, "key_scope_forbidden"
    if error.status_code == 401:
        return 401, "key_disabled"
    if error.status_code == 400:
        return 400, "invalid_request"
    return 500, "temporary"


def _ru_probe_http_exception(error: HTTPException) -> tuple[int, str]:
    if int(error.status_code) == 413:
        return 413, "request_too_large"
    if 400 <= int(error.status_code) < 500:
        return 400, "invalid_request"
    return 500, "temporary"


def _ru_probe_contract_error(error: RuProbeContractError) -> tuple[int, str]:
    if error.code == "unsupported_schema_version":
        return 422, "unsupported_schema"
    return 422, "invalid_payload"


def _ru_probe_response_for_exception(
    error: Exception,
    *,
    correlation_id: str,
) -> JSONResponse:
    if isinstance(error, _RuProbeHttpError):
        return _ru_probe_error_response(
            status_code=error.status_code,
            code=error.code,
            correlation_id=correlation_id,
        )
    if isinstance(error, InternalAuthError):
        status_code, code = _ru_probe_auth_error(error)
    elif isinstance(error, HTTPException):
        status_code, code = _ru_probe_http_exception(error)
    elif isinstance(error, RuProbeContractError):
        status_code, code = _ru_probe_contract_error(error)
    elif isinstance(error, RuProbePayloadConflict):
        status_code, code = 409, "payload_conflict"
    elif isinstance(error, RuProbeConfigurationError):
        status_code, code = 500, "temporary"
    else:
        status_code, code = 500, "temporary"
    return _ru_probe_error_response(
        status_code=status_code,
        code=code,
        correlation_id=correlation_id,
    )


def _authenticate_ru_probe_request(
    session,
    request: Request,
    *,
    raw_body: bytes,
    required_scope: str,
    expected_path: str,
    now: datetime,
):
    return authenticate_internal_request(
        session,
        load_internal_service_key_registry(),
        method=request.method,
        path=expected_path,
        raw_body=raw_body,
        headers=_ru_probe_headers(request),
        required_scope=required_scope,
        required_origin="ru",
        now=now,
    )


async def _reject_ru_probe_route_alias(request: Request) -> JSONResponse:
    return _ru_probe_error_response(
        status_code=400,
        code="invalid_request",
        correlation_id=_ru_probe_correlation_id(request),
    )


app.add_api_route(
    f"{_RU_MANIFEST_PATH}/",
    _reject_ru_probe_route_alias,
    methods=["GET"],
    include_in_schema=False,
)
app.add_api_route(
    f"{_RU_RUNS_PATH}/",
    _reject_ru_probe_route_alias,
    methods=["POST"],
    include_in_schema=False,
)
app.add_api_route(
    f"{_RU_HEARTBEAT_PATH}/",
    _reject_ru_probe_route_alias,
    methods=["POST"],
    include_in_schema=False,
)


async def _reject_release_evidence_route_alias(request: Request) -> JSONResponse:
    return _ru_probe_error_response(
        status_code=400,
        code="invalid_request",
        correlation_id=_ru_probe_correlation_id(request),
    )


app.add_api_route(
    f"{_RELEASE_CANDIDATES_PATH}/",
    _reject_release_evidence_route_alias,
    methods=["POST"],
    include_in_schema=False,
)


@app.get(_RU_MANIFEST_PATH)
async def internal_ru_probe_manifest(request: Request):
    correlation_id = _ru_probe_correlation_id(request)
    try:
        _require_exact_ru_probe_route(request, _RU_MANIFEST_PATH)
    except Exception as error:
        return _ru_probe_response_for_exception(
            error,
            correlation_id=correlation_id,
        )
    session = SessionLocal()
    try:
        raw_body = await _read_limited_request_body(
            request,
            max_bytes=0,
            scope="RU probe manifest",
        )
        now = _ru_probe_now()
        _authenticate_ru_probe_request(
            session,
            request,
            raw_body=raw_body,
            required_scope="ru_probe:manifest",
            expected_path=_RU_MANIFEST_PATH,
            now=now,
        )
        manifest = build_ru_manifest(session, now=now)
        session.commit()
        return JSONResponse(status_code=200, content=manifest)
    except Exception as error:
        session.rollback()
        return _ru_probe_response_for_exception(
            error,
            correlation_id=correlation_id,
        )
    finally:
        session.close()


@app.post(_RU_RUNS_PATH)
async def internal_ru_probe_run(request: Request):
    correlation_id = _ru_probe_correlation_id(request)
    try:
        _require_exact_ru_probe_route(request, _RU_RUNS_PATH)
    except Exception as error:
        return _ru_probe_response_for_exception(
            error,
            correlation_id=correlation_id,
        )
    session = SessionLocal()
    try:
        raw_body = await _read_limited_request_body(
            request,
            max_bytes=_RU_RUN_MAX_BODY_BYTES,
            scope="RU probe run",
        )
        now = _ru_probe_now()
        authenticated = _authenticate_ru_probe_request(
            session,
            request,
            raw_body=raw_body,
            required_scope="ru_probe:ingest",
            expected_path=_RU_RUNS_PATH,
            now=now,
        )
        payload = _ru_probe_json(raw_body)
        validated = validate_run_payload(payload)
        if authenticated.subject != validated["probe_host"]["id"]:
            raise _RuProbeHttpError(403, "key_scope_forbidden")
        evaluated = evaluate_ru_run(session, validated, now=now)
        stored = store_evaluated_ru_run(
            session,
            evaluated,
            artifact_sha256=hashlib.sha256(raw_body).hexdigest(),
            ingest_key_id=authenticated.key_id,
            received_at=now,
        )
        session.commit()
        return JSONResponse(
            status_code=201 if stored.created else 200,
            content={
                "code": "created",
                "run_db_id": stored.run_db_id,
                "run_id": stored.run_id,
                "created": stored.created,
                "current_eligible": stored.current_eligible,
                "correlation_id": correlation_id,
            },
        )
    except Exception as error:
        session.rollback()
        return _ru_probe_response_for_exception(
            error,
            correlation_id=correlation_id,
        )
    finally:
        session.close()


@app.post(_RU_HEARTBEAT_PATH)
async def internal_ru_probe_heartbeat(request: Request):
    correlation_id = _ru_probe_correlation_id(request)
    try:
        _require_exact_ru_probe_route(request, _RU_HEARTBEAT_PATH)
    except Exception as error:
        return _ru_probe_response_for_exception(
            error,
            correlation_id=correlation_id,
        )
    session = SessionLocal()
    try:
        raw_body = await _read_limited_request_body(
            request,
            max_bytes=_RU_HEARTBEAT_MAX_BODY_BYTES,
            scope="RU probe heartbeat",
        )
        now = _ru_probe_now()
        authenticated = _authenticate_ru_probe_request(
            session,
            request,
            raw_body=raw_body,
            required_scope="ru_probe:heartbeat",
            expected_path=_RU_HEARTBEAT_PATH,
            now=now,
        )
        heartbeat = validate_ru_heartbeat(_ru_probe_json(raw_body), now=now)
        if authenticated.subject != heartbeat.probe_host_id:
            raise _RuProbeHttpError(403, "key_scope_forbidden")
        stored = store_ru_heartbeat(
            session,
            heartbeat,
            received_at=now,
            ingest_key_id=authenticated.key_id,
        )
        session.commit()
        return JSONResponse(
            status_code=201 if stored.created else 200,
            content={
                "code": "created",
                "correlation_id": correlation_id,
            },
        )
    except Exception as error:
        session.rollback()
        return _ru_probe_response_for_exception(
            error,
            correlation_id=correlation_id,
        )
    finally:
        session.close()


def _release_evidence_response_for_exception(
    error: Exception,
    *,
    correlation_id: str,
) -> JSONResponse:
    if isinstance(error, ReleaseEvidenceConflict):
        return _ru_probe_error_response(
            status_code=409,
            code=error.code,
            correlation_id=correlation_id,
        )
    if isinstance(error, ReleaseEvidenceValidationError):
        return _ru_probe_error_response(
            status_code=422,
            code=error.code,
            correlation_id=correlation_id,
        )
    return _ru_probe_response_for_exception(
        error,
        correlation_id=correlation_id,
    )


@app.post(_RELEASE_CANDIDATES_PATH)
async def internal_release_candidate_import(request: Request):
    correlation_id = _ru_probe_correlation_id(request)
    try:
        _require_exact_ru_probe_route(request, _RELEASE_CANDIDATES_PATH)
    except Exception as error:
        return _release_evidence_response_for_exception(
            error,
            correlation_id=correlation_id,
        )
    session = SessionLocal()
    try:
        raw_body = await _read_limited_request_body(
            request,
            max_bytes=_RELEASE_EVIDENCE_MAX_BODY_BYTES,
            scope="Release evidence",
        )
        now = _ru_probe_now()
        authenticated = authenticate_internal_request(
            session,
            load_internal_service_key_registry(),
            method=request.method,
            path=_RELEASE_CANDIDATES_PATH,
            raw_body=raw_body,
            headers=_ru_probe_headers(request),
            required_scope="release:evidence",
            required_origin="release",
            now=now,
        )
        payload = _ru_probe_json(raw_body)
        stored = import_release_evidence(
            session,
            payload,
            ingest_key_id=authenticated.key_id,
            imported_at=now,
        )
        session.commit()
        return JSONResponse(
            status_code=201 if stored.created else 200,
            content={
                "code": "created" if stored.created else "already_imported",
                "candidate_id": stored.candidate_id,
                "created": stored.created,
                "candidate_created": stored.candidate_created,
                "evidence_created": stored.evidence_created,
                "correlation_id": correlation_id,
            },
        )
    except Exception as error:
        session.rollback()
        return _release_evidence_response_for_exception(
            error,
            correlation_id=correlation_id,
        )
    finally:
        session.close()


def _detect_support_upload_type(*, filename: str, content_type: str, raw_bytes: bytes) -> tuple[str, str, str]:
    declared = str(content_type or "").split(";", 1)[0].strip().lower()
    suffix = Path(filename).suffix.lower().strip()
    data = raw_bytes or b""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", "image", ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", "image", ".jpg"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp", "image", ".webp"
    if data.startswith(b"%PDF-"):
        return "application/pdf", "file", ".pdf"
    if declared == "text/plain" or suffix == ".txt":
        if b"\x00" in data:
            raise HTTPException(status_code=400, detail="Unsupported attachment type")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Unsupported attachment type")
        return "text/plain", "file", ".txt"
    raise HTTPException(status_code=400, detail="Unsupported attachment type")


_SUPPORT_UPLOAD_OWNER_LOCKS = tuple(threading.Lock() for _ in range(256))


def _support_upload_owner_key(*, owner_tg_id: int, owner_account_id: str | None) -> str:
    canonical_owner = str(owner_account_id or "").strip()
    return f"account:{canonical_owner}" if canonical_owner else f"tg:{int(owner_tg_id)}"


def _support_upload_owner_lock(owner_key: str) -> threading.Lock:
    digest = hashlib.sha256(str(owner_key).encode("utf-8")).digest()
    return _SUPPORT_UPLOAD_OWNER_LOCKS[int.from_bytes(digest[:2], "big") % len(_SUPPORT_UPLOAD_OWNER_LOCKS)]


def _support_upload_advisory_lock_key(owner_key: str) -> int:
    return int.from_bytes(hashlib.sha256(str(owner_key).encode("utf-8")).digest()[:8], "big", signed=True)


def _lock_support_upload_owner_in_db(session, owner_key: str) -> None:
    if session.bind is None or session.bind.dialect.name != "postgresql":
        return
    session.execute(
        text("SELECT pg_advisory_xact_lock(:lock_key)"),
        {"lock_key": _support_upload_advisory_lock_key(owner_key)},
    )


def _fsync_parent_directory(path: Path) -> None:
    if os.name != "posix":
        return
    descriptor = os.open(str(path.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _store_support_upload(
    *,
    owner_tg_id: int,
    owner_account_id: str | None = None,
    filename: str | None,
    content_type: str | None,
    raw_bytes: bytes,
) -> dict[str, Any]:
    owner_key = _support_upload_owner_key(
        owner_tg_id=owner_tg_id,
        owner_account_id=owner_account_id,
    )
    with _support_upload_owner_lock(owner_key):
        return _store_support_upload_locked(
            owner_tg_id=owner_tg_id,
            owner_account_id=owner_account_id,
            filename=filename,
            content_type=content_type,
            raw_bytes=raw_bytes,
            owner_key=owner_key,
        )


def _store_support_upload_locked(
    *,
    owner_tg_id: int,
    owner_account_id: str | None,
    filename: str | None,
    content_type: str | None,
    raw_bytes: bytes,
    owner_key: str,
) -> dict[str, Any]:
    original_name = _sanitize_ticket_upload_name(filename)
    content_type, media_type, suffix = _detect_support_upload_type(
        filename=original_name,
        content_type=str(content_type or ""),
        raw_bytes=raw_bytes,
    )
    now = _utcnow()
    stored_name = f"{now.strftime('%Y%m%d')}-{secrets.token_urlsafe(12).replace('-', '').replace('_', '')}{suffix}"
    stored_path = SUPPORT_UPLOAD_DIR / stored_name
    temp_path = SUPPORT_UPLOAD_DIR / f".{stored_name}.{secrets.token_hex(8)}.tmp"

    total_size = len(raw_bytes or b"")
    if total_size <= 0:
        raise HTTPException(status_code=400, detail="Attachment is empty")
    if total_size > SUPPORT_UPLOAD_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Attachment is too large")

    s = SessionLocal()
    try:
        _lock_support_upload_owner_in_db(s, owner_key)
        canonical_owner = str(owner_account_id or "").strip()
        owner_filter = (
            SupportAttachment.owner_account_id == canonical_owner
            if canonical_owner
            else and_(
                SupportAttachment.owner_account_id.is_(None),
                SupportAttachment.owner_tg_id == int(owner_tg_id),
            )
        )
        expired_rows = (
            s.query(SupportAttachment)
            .filter(
                SupportAttachment.ticket_id.is_(None),
                SupportAttachment.message_id.is_(None),
                SupportAttachment.expires_at.isnot(None),
                SupportAttachment.expires_at <= now,
                owner_filter,
            )
            .order_by(SupportAttachment.id.asc())
            .all()
        )
        removed_names: list[str] = []
        for expired in expired_rows:
            removed = (
                s.query(SupportAttachment)
                .filter(
                    SupportAttachment.id == expired.id,
                    SupportAttachment.ticket_id.is_(None),
                    SupportAttachment.message_id.is_(None),
                    SupportAttachment.expires_at.isnot(None),
                    SupportAttachment.expires_at <= now,
                    owner_filter,
                )
                .delete(synchronize_session=False)
            )
            if removed:
                removed_names.append(str(expired.stored_name))
                s.expunge(expired)
        s.commit()
        _lock_support_upload_owner_in_db(s, owner_key)
        for expired_name in removed_names:
            clean_expired_name = Path(expired_name).name
            if clean_expired_name != expired_name or not re.fullmatch(
                r"\d{8}-[A-Za-z0-9]{8,64}\.(png|jpg|jpeg|webp|pdf|txt)",
                clean_expired_name,
            ):
                continue
            row_reappeared = (
                s.query(SupportAttachment.id)
                .filter(SupportAttachment.stored_name == clean_expired_name)
                .first()
                is not None
            )
            if not row_reappeared:
                (SUPPORT_UPLOAD_DIR / clean_expired_name).unlink(missing_ok=True)

        pending = s.query(
            func.count(SupportAttachment.id),
            func.coalesce(func.sum(SupportAttachment.size_bytes), 0),
        ).filter(
            SupportAttachment.ticket_id.is_(None),
            SupportAttachment.message_id.is_(None),
            SupportAttachment.expires_at.isnot(None),
            SupportAttachment.expires_at > now,
            owner_filter,
        )
        pending_count, pending_bytes = pending.one()
        if int(pending_count or 0) >= SUPPORT_PENDING_UPLOAD_MAX_COUNT:
            raise HTTPException(status_code=429, detail="Pending attachment quota exceeded")
        if int(pending_bytes or 0) + total_size > SUPPORT_PENDING_UPLOAD_MAX_BYTES:
            raise HTTPException(status_code=429, detail="Pending attachment byte quota exceeded")

        descriptor = os.open(str(temp_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as temp_file:
            temp_file.write(raw_bytes)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_path, stored_path)
        _fsync_parent_directory(stored_path)
        s.add(
            SupportAttachment(
                stored_name=stored_name,
                owner_tg_id=int(owner_tg_id),
                owner_account_id=str(owner_account_id or "").strip() or None,
                original_name=original_name,
                content_type=content_type,
                size_bytes=int(total_size),
                media_type=media_type,
                expires_at=now + timedelta(hours=SUPPORT_PENDING_UPLOAD_TTL_HOURS),
                created_at=now,
            )
        )
        s.commit()
    except HTTPException:
        s.rollback()
        temp_path.unlink(missing_ok=True)
        raise
    except Exception:
        s.rollback()
        temp_path.unlink(missing_ok=True)
        _record_security_event(
            "support_upload_reject",
            scope="ticket_upload",
            client_ip=_request_client_ip(None),
            subject=f"tg:{int(owner_tg_id)}",
            reason="store_failed",
        )
        raise
    finally:
        s.close()

    file_url = f"{SUPPORT_ATTACHMENT_URL_PREFIX.rstrip('/')}/{stored_name}"
    payload = {
        "url": file_url,
        "name": original_name,
        "content_type": content_type,
        "size": int(total_size),
        "private": True,
    }
    attachment = {
        "media_type": media_type,
        "media_file_id": f"support/{stored_name}",
        "media_payload": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    }
    return {"attachment_id": stored_name, "attachment": attachment, "attachment_payload": payload}


_SUPPORT_ATTACHMENT_BIND_LOCKS = tuple(threading.Lock() for _ in range(64))


def _support_attachment_error(*, code: str, status_code: int) -> HTTPException:
    details = {
        "support_attachment_invalid": "Attachment reference is invalid",
        "support_attachment_not_found": "Attachment not found",
        "support_attachment_already_bound": "Attachment is already bound",
    }
    return _auth_http_exception(detail=details[code], code=code, status_code=status_code)


def _support_attachment_reference(payload: TicketMessageIn) -> str:
    attachment_id = str(payload.attachment_id or "").strip()
    if attachment_id:
        return attachment_id
    media_file_id = str(payload.media_file_id or "").strip()
    return media_file_id.removeprefix("support/") if media_file_id.startswith("support/") else ""


def _support_attachment_bind_lock(reference: str):
    if not reference:
        return contextlib.nullcontext()
    digest = hashlib.sha256(reference.encode("utf-8")).digest()
    return _SUPPORT_ATTACHMENT_BIND_LOCKS[digest[0] % len(_SUPPORT_ATTACHMENT_BIND_LOCKS)]


def _canonical_support_attachment(row: SupportAttachment) -> dict[str, Any]:
    stored_name = str(row.stored_name)
    payload = {
        "url": f"{SUPPORT_ATTACHMENT_URL_PREFIX.rstrip('/')}/{stored_name}",
        "name": str(row.original_name),
        "content_type": str(row.content_type),
        "size": int(row.size_bytes or 0),
        "private": True,
    }
    return {
        "media_type": str(row.media_type),
        "media_file_id": f"support/{stored_name}",
        "media_payload": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    }


def _support_attachment_owned_by(
    row: SupportAttachment,
    *,
    actor_tg_id: int,
    account_id: str | None,
) -> bool:
    return can_access_support_attachment(
        row,
        int(actor_tg_id),
        0,
        account_id=str(account_id or "").strip() or None,
    )


def _resolve_ticket_attachment(
    session,
    *,
    payload: TicketMessageIn,
    actor_tg_id: int,
    account_id: str | None,
) -> tuple[SupportAttachment | None, dict[str, Any]]:
    attachment_id = str(payload.attachment_id or "").strip()
    media_values = (payload.media_type, payload.media_file_id, payload.media_payload)
    has_media = any(value is not None and str(value).strip() for value in media_values)
    if attachment_id and has_media:
        raise _support_attachment_error(code="support_attachment_invalid", status_code=400)

    media_file_id = str(payload.media_file_id or "").strip()
    legacy_private = not attachment_id and media_file_id.startswith("support/")
    if not attachment_id and not legacy_private:
        return None, {
            "media_type": payload.media_type,
            "media_file_id": payload.media_file_id,
            "media_payload": payload.media_payload,
        }
    stored_name = attachment_id or media_file_id.removeprefix("support/")
    if (
        not stored_name
        or Path(stored_name).name != stored_name
        or not re.fullmatch(r"\d{8}-[A-Za-z0-9]{8,64}\.(png|jpg|jpeg|webp|pdf|txt)", stored_name)
    ):
        raise _support_attachment_error(code="support_attachment_not_found", status_code=404)

    query = session.query(SupportAttachment).filter(SupportAttachment.stored_name == stored_name)
    if session.bind is not None and session.bind.dialect.name == "postgresql":
        query = query.with_for_update()
    row = query.first()
    now = _utcnow()
    if not row or not _support_attachment_owned_by(
        row,
        actor_tg_id=actor_tg_id,
        account_id=account_id,
    ):
        raise _support_attachment_error(code="support_attachment_not_found", status_code=404)
    if row.expires_at is not None and row.expires_at <= now:
        raise _support_attachment_error(code="support_attachment_not_found", status_code=404)
    if row.ticket_id is not None or row.message_id is not None:
        raise _support_attachment_error(code="support_attachment_already_bound", status_code=409)

    canonical = _canonical_support_attachment(row)
    if legacy_private:
        try:
            supplied_payload = json.loads(str(payload.media_payload or ""))
            canonical_payload = json.loads(canonical["media_payload"])
        except (TypeError, ValueError, json.JSONDecodeError):
            raise _support_attachment_error(code="support_attachment_invalid", status_code=400)
        accepted_urls = {
            canonical_payload["url"],
            f"{SUPPORT_UPLOAD_URL_PREFIX.rstrip('/')}/{stored_name}",
        }
        supplied_url = str((supplied_payload or {}).get("url") or "")
        comparable_keys = ("name", "content_type", "size", "private")
        if (
            str(payload.media_type or "") != canonical["media_type"]
            or media_file_id != canonical["media_file_id"]
            or not isinstance(supplied_payload, dict)
            or supplied_url not in accepted_urls
            or any(supplied_payload.get(key) != canonical_payload[key] for key in comparable_keys)
        ):
            raise _support_attachment_error(code="support_attachment_invalid", status_code=400)
    return row, canonical


def _bind_ticket_attachment(
    session,
    *,
    row: SupportAttachment,
    ticket_id: int,
    message_id: int,
) -> None:
    now = _utcnow()
    filters = [
        SupportAttachment.id == row.id,
        SupportAttachment.ticket_id.is_(None),
        SupportAttachment.message_id.is_(None),
    ]
    if row.expires_at is not None:
        filters.append(SupportAttachment.expires_at > now)
    updated = session.query(SupportAttachment).filter(*filters).update(
        {
            SupportAttachment.ticket_id: int(ticket_id),
            SupportAttachment.message_id: int(message_id),
            SupportAttachment.attached_at: now,
            SupportAttachment.expires_at: None,
        },
        synchronize_session=False,
    )
    if updated != 1:
        current = (
            session.query(SupportAttachment)
            .filter(SupportAttachment.id == row.id)
            .populate_existing()
            .first()
        )
        if current is None or (current.expires_at is not None and current.expires_at <= now):
            raise _support_attachment_error(code="support_attachment_not_found", status_code=404)
        if current.ticket_id is not None or current.message_id is not None:
            raise _support_attachment_error(code="support_attachment_already_bound", status_code=409)
        raise _support_attachment_error(code="support_attachment_not_found", status_code=404)


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
    if str(user.sub_type or "").upper() == "FREE" and traffic_gb > float(FREE_STANDARD_QUOTA_GB) * 1.2:
        val = min(25, int((traffic_gb / max(1.0, float(FREE_STANDARD_QUOTA_GB))) * 8))
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
    referrer = s.query(User).filter(User.tg_id == int(referrer_tg_id)).first()
    referred = s.query(User).filter(User.tg_id == int(referred_tg_id)).first()
    if referrer is None or referred is None:
        return False
    ensure_user_account_foundation(s, referrer, now=now)
    ensure_user_account_foundation(s, referred, now=now)
    s.flush()
    relationship = create_referral_relationship(
        s,
        referred_account_id=str(referred.account_id),
        referrer_account_id=str(referrer.account_id),
        source="legacy_referrer_projection",
        now=now,
    )
    was_queued = bool(relationship.first_payment_key)
    queue_first_payment_referrer_reward(
        s,
        referred_account_id=str(referred.account_id),
        payment_key=f"payment:{str(order_id)}",
        paid_at=now,
    )
    if not was_queued:
        referrer.referral_count = int(referrer.referral_count or 0) + 1
    return True


def _process_referral_bonus_queue(*, limit: int = 100, force_without_activity: bool = False) -> dict[str, int]:
    now = _utcnow()
    s = SessionLocal()
    try:
        migration = migrate_pending_legacy_referral_queue(s, now=now, limit=limit)
        release = release_due_referrer_rewards(s, now=now)
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
    "routing_lesson_completed",
}

FUNNEL_EVENT_WHITELIST = {
    "page_view",
    "cta_click",
    "install_opened",
    "checkout_view",
    "checkout_start",
    "bot_open_intent",
    "cabinet_open_intent",
    "download_click",
}

FUNNEL_STAGE_WHITELIST = {
    "site_visit",
    "install_intent",
    "cabinet_intent",
    "bot_intent",
    "checkout_view",
    "checkout_start",
    "download",
}

FUNNEL_CHANNEL_WHITELIST = {"site", "marketing", "checkout", "webapp", "bot"}


def _clean_funnel_slug(value: object, *, default: str, max_len: int = 64) -> str:
    raw = str(value or "").strip().lower()
    raw = re.sub(r"[^a-z0-9_.:-]+", "_", raw)
    raw = raw.strip("._:-")
    return (raw or default)[:max_len]


def _clean_public_text(value: object, *, max_len: int) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    raw = raw.replace("\x00", "")
    return raw[:max_len]


def _node_code_base(code: str) -> str:
    normalized = (code or "").lower().strip()
    for separator in ("_", "-", "."):
        if separator in normalized:
            normalized = normalized.split(separator, 1)[0]
    return normalized


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
        "ru": "Russia",
        "fi": "Finland",
        "fr": "France",
        "gb": "United Kingdom",
        "uk": "United Kingdom",
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
# Route implementations live in ordered domain slices. The loader preserves
# the legacy api.<name> surface and deterministic FastAPI registration.
try:
    from .module_slices import load_slices as _load_domain_slices
except ImportError:
    from module_slices import load_slices as _load_domain_slices

_slice_prefix = f"{__package__}." if __package__ else ""
_API_SLICE_MODULES = _load_domain_slices(
    globals(),
    (
        f"{_slice_prefix}api_public_routes",
        f"{_slice_prefix}api_surface_routes",
        f"{_slice_prefix}api_admin_routes",
        f"{_slice_prefix}api_subscription_routes",
    ),
)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "2096")))

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from acquisition_service import handoff_token_hash
from commercial_capacity_quality import commercial_quality_snapshot
from commercial_campaign_policy import (
    active_entitlement_capacity_units,
    campaign_record,
    evaluate_campaign_policy,
)
from commercial_contract import get_commercial_contract
from models import (
    AcquisitionHandoff,
    AcquisitionSession,
    CommercialAssignment,
    CommercialCreative,
    CommercialOffer,
    CommercialReservation,
    IncentiveCampaign,
    PromoCode,
)


OFFER_TOKEN_SCHEMA = "pokrov-commercial-offer-token-v2"
OFFER_TOKEN_VERSION = 2
OFFER_TOKEN_PREFIX = "v2"
OFFER_HOLD_TTL_MIN_SECONDS = 60
OFFER_HOLD_TTL_MAX_SECONDS = 900
OFFER_PUBLIC_ID_RE = re.compile(r"^off_[0-9a-f]{32}$")
CREATIVE_PUBLIC_ID_RE = re.compile(r"^crv_[0-9a-f]{32}$")
ASSIGNMENT_PUBLIC_ID_RE = re.compile(r"^asg_[0-9a-f]{32}$")
RESERVATION_PUBLIC_ID_RE = re.compile(r"^rsv_[0-9a-f]{32}$")
IMPRESSION_PUBLIC_ID_RE = re.compile(r"^imp_[0-9a-f]{32}$")
CLICK_PUBLIC_ID_RE = re.compile(r"^clk_[0-9a-f]{32}$")

OFFER_STATUSES = frozenset({"draft", "review", "live", "paused", "ended", "killed"})
CREATIVE_STATUSES = frozenset({"draft", "review", "live", "paused", "ended", "killed"})
ASSIGNMENT_STATUSES = frozenset({"active", "paused", "ended", "killed"})
AUDIENCE_STATUSES = frozenset({"eligible", "blocked"})
RESERVATION_STATUSES = frozenset({"held", "bound", "consumed", "expired", "released"})

OFFER_PREVIEW_REASONS = frozenset(
    {
        "ready",
        "plan_unknown",
        "plan_inactive",
        "promo_unknown",
        "promo_invalid",
        "promo_expired",
        "promo_depleted",
        "offer_not_found",
        "offer_ambiguous",
        "offer_mismatch",
        "offer_not_live",
        "offer_not_started",
        "offer_ended",
        "offer_revision_stale",
        "offer_terms_stale",
        "offer_price_invalid",
        "offer_price_mismatch",
        "offer_non_stackable",
        "campaign_not_live",
        "campaign_not_started",
        "campaign_ended",
        "commercial_revision_stale",
        "legal_blocked",
        "capacity_blocked",
        "channel_blocked",
        "subject_missing",
        "subject_invalid",
        "subject_conflict",
        "signing_unavailable",
        "audience_blocked",
        "assignment_expired",
        "creative_unavailable",
        "quota_reached",
        "reservation_conflict",
        "reservation_expired",
        "reservation_unavailable",
    }
)

OFFER_TOKEN_FIELDS = frozenset(
    {
        "schema",
        "version",
        "subject",
        "plan",
        "campaign",
        "campaign_revision",
        "creative",
        "variant",
        "assignment",
        "offer",
        "base_amount_rub",
        "final_amount_rub",
        "currency",
        "commercial_revision",
        "terms_revision",
        "reservation",
        "impression",
        "click",
        "issued_at",
        "hold_expires_at",
        "offer_ends_at",
    }
)


class CommercialOfferTokenError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class CommercialOfferPreviewError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _naive_utc(value: datetime) -> datetime:
    return _as_utc(value).replace(tzinfo=None)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _as_utc(value).isoformat(timespec="seconds").replace("+00:00", "Z")


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except Exception as exc:
        raise CommercialOfferTokenError("offer_token_malformed") from exc


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(value),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _secret_bytes(secret: str | bytes | None = None) -> bytes:
    raw = secret if secret is not None else os.getenv("COMMERCIAL_OFFER_HMAC_SECRET", "")
    value = raw if isinstance(raw, bytes) else str(raw or "").encode("utf-8")
    if len(value) < 32:
        raise CommercialOfferTokenError("offer_signing_secret_unavailable")
    return value


def configured_offer_hold_ttl_seconds() -> int:
    try:
        configured = int(os.getenv("COMMERCIAL_OFFER_HOLD_TTL_SECONDS", "600"))
    except ValueError:
        configured = 600
    return max(OFFER_HOLD_TTL_MIN_SECONDS, min(OFFER_HOLD_TTL_MAX_SECONDS, configured))


def commercial_subject_binding(
    *,
    campaign_public_id: str,
    subject_kind: str,
    subject_value: str,
    secret: str | bytes | None = None,
) -> str:
    campaign_id = str(campaign_public_id or "").strip().lower()
    kind = str(subject_kind or "").strip().lower()[:32]
    value = str(subject_value or "").strip()[:512]
    if re.fullmatch(r"cmp_[0-9a-f]{32}", campaign_id) is None:
        raise CommercialOfferPreviewError("subject_invalid")
    if not kind or not value:
        raise CommercialOfferPreviewError("subject_missing")
    message = (
        f"pokrov-offer-subject-v1\x00{campaign_id}\x00{kind}\x00{value}"
    ).encode("utf-8")
    return hmac.new(_secret_bytes(secret), message, hashlib.sha256).hexdigest()


def resolve_acquisition_offer_subject(
    session,
    *,
    raw_handle: str,
    now: datetime | None = None,
) -> tuple[str, str]:
    kind, value, _handoff = resolve_acquisition_offer_context(
        session,
        raw_handle=raw_handle,
        now=now,
    )
    return kind, value


def resolve_acquisition_offer_context(
    session,
    *,
    raw_handle: str,
    now: datetime | None = None,
) -> tuple[str, str, AcquisitionHandoff]:
    current = _as_utc(now or _utcnow())
    handle = str(raw_handle or "").strip()
    if len(handle) < 32:
        raise CommercialOfferPreviewError("subject_invalid")
    row = (
        session.query(AcquisitionHandoff)
        .filter(AcquisitionHandoff.token_hash == handoff_token_hash(handle))
        .first()
    )
    if (
        row is None
        or str(row.purpose or "") != "checkout"
        or row.consumed_at is not None
        or row.bound_order_id is not None
        or _as_utc(row.expires_at) <= current
    ):
        raise CommercialOfferPreviewError("subject_invalid")
    acquisition = (
        session.query(AcquisitionSession)
        .filter(AcquisitionSession.id == str(row.acquisition_session_id))
        .first()
    )
    if acquisition is None or _as_utc(acquisition.expires_at) <= current:
        raise CommercialOfferPreviewError("subject_invalid")
    if not IMPRESSION_PUBLIC_ID_RE.fullmatch(str(row.impression_public_id or "")):
        row.impression_public_id = f"imp_{secrets.token_hex(16)}"
    if not CLICK_PUBLIC_ID_RE.fullmatch(str(row.click_public_id or "")):
        row.click_public_id = f"clk_{secrets.token_hex(16)}"
    return "acquisition_session", str(acquisition.id), row


def sign_commercial_offer_token(
    payload: Mapping[str, Any],
    *,
    secret: str | bytes | None = None,
) -> str:
    value = dict(payload)
    if set(value) != OFFER_TOKEN_FIELDS:
        raise CommercialOfferTokenError("offer_token_fields_invalid")
    if value.get("schema") != OFFER_TOKEN_SCHEMA or value.get("version") != OFFER_TOKEN_VERSION:
        raise CommercialOfferTokenError("offer_token_version_invalid")
    encoded = _b64encode(_canonical_json(value))
    signed = f"{OFFER_TOKEN_PREFIX}.{encoded}".encode("ascii")
    signature = _b64encode(hmac.new(_secret_bytes(secret), signed, hashlib.sha256).digest())
    return f"{OFFER_TOKEN_PREFIX}.{encoded}.{signature}"


def verify_commercial_offer_token(
    token: str,
    *,
    secret: str | bytes | None = None,
    now: datetime | None = None,
    allow_expired: bool = False,
) -> dict[str, Any]:
    parts = str(token or "").split(".")
    if len(parts) != 3 or parts[0] != OFFER_TOKEN_PREFIX:
        raise CommercialOfferTokenError("offer_token_malformed")
    signed = f"{parts[0]}.{parts[1]}".encode("ascii")
    expected = hmac.new(_secret_bytes(secret), signed, hashlib.sha256).digest()
    actual = _b64decode(parts[2])
    if not hmac.compare_digest(expected, actual):
        raise CommercialOfferTokenError("offer_token_signature_invalid")
    try:
        payload = json.loads(_b64decode(parts[1]).decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise CommercialOfferTokenError("offer_token_malformed") from exc
    if not isinstance(payload, dict) or set(payload) != OFFER_TOKEN_FIELDS:
        raise CommercialOfferTokenError("offer_token_fields_invalid")
    if (
        payload.get("schema") != OFFER_TOKEN_SCHEMA
        or type(payload.get("version")) is not int
        or payload.get("version") != OFFER_TOKEN_VERSION
    ):
        raise CommercialOfferTokenError("offer_token_version_invalid")
    current_ts = int(_as_utc(now or _utcnow()).timestamp())
    if any(
        type(payload.get(field)) is not int
        for field in (
            "issued_at",
            "hold_expires_at",
            "offer_ends_at",
            "base_amount_rub",
            "final_amount_rub",
            "campaign_revision",
        )
    ):
        raise CommercialOfferTokenError("offer_token_time_invalid")
    try:
        issued_at = int(payload["issued_at"])
        hold_expires_at = int(payload["hold_expires_at"])
        offer_ends_at = int(payload["offer_ends_at"])
    except (TypeError, ValueError) as exc:
        raise CommercialOfferTokenError("offer_token_time_invalid") from exc
    if issued_at > current_ts + 60:
        raise CommercialOfferTokenError("offer_token_time_invalid")
    if hold_expires_at <= current_ts and not allow_expired:
        raise CommercialOfferTokenError("offer_token_expired")
    if (
        hold_expires_at <= issued_at
        or hold_expires_at - issued_at > OFFER_HOLD_TTL_MAX_SECONDS
        or hold_expires_at > offer_ends_at
    ):
        raise CommercialOfferTokenError("offer_token_time_invalid")
    if not (
        re.fullmatch(r"cmp_[0-9a-f]{32}", str(payload.get("campaign") or ""))
        and re.fullmatch(r"[a-z0-9_]{2,32}", str(payload.get("plan") or ""))
        and OFFER_PUBLIC_ID_RE.fullmatch(str(payload.get("offer") or ""))
        and CREATIVE_PUBLIC_ID_RE.fullmatch(str(payload.get("creative") or ""))
        and ASSIGNMENT_PUBLIC_ID_RE.fullmatch(str(payload.get("assignment") or ""))
        and RESERVATION_PUBLIC_ID_RE.fullmatch(str(payload.get("reservation") or ""))
        and re.fullmatch(r"[0-9a-f]{64}", str(payload.get("subject") or ""))
    ):
        raise CommercialOfferTokenError("offer_token_binding_invalid")
    try:
        base_amount = int(payload["base_amount_rub"])
        final_amount = int(payload["final_amount_rub"])
        campaign_revision = int(payload["campaign_revision"])
    except (TypeError, ValueError) as exc:
        raise CommercialOfferTokenError("offer_token_binding_invalid") from exc
    if (
        base_amount <= 0
        or final_amount <= 0
        or final_amount >= base_amount
        or campaign_revision <= 0
        or not str(payload.get("currency") or "").strip()
        or not str(payload.get("commercial_revision") or "").strip()
        or not str(payload.get("terms_revision") or "").strip()
        or not str(payload.get("variant") or "").strip()
    ):
        raise CommercialOfferTokenError("offer_token_binding_invalid")
    return payload


def _empty_preview(
    *,
    reason_code: str,
    now: datetime,
    plan_code: str,
    currency: str,
    base_amount_rub: int,
    commercial_revision: str,
    terms_url: str,
) -> dict[str, Any]:
    reason = reason_code if reason_code in OFFER_PREVIEW_REASONS else "offer_not_found"
    return {
        "ok": True,
        "valid": False,
        "reason_code": reason,
        "blocking_reasons": [reason],
        "plan_code": plan_code,
        "currency": currency,
        "base_price_rub": int(base_amount_rub),
        "final_price_rub": int(base_amount_rub),
        "benefit_rub": 0,
        "benefit_percent": 0,
        "server_time": _iso(now),
        "offer_ends_at": None,
        "hold_expires_at": None,
        "remaining_quota_lower_bound": None,
        "terms_url": terms_url,
        "commercial_revision": commercial_revision,
        "campaign_id": None,
        "creative_id": None,
        "variant": None,
        "assignment_id": None,
        "offer_id": None,
        "reservation_id": None,
        "offer_token": None,
    }


def _campaign_block_reason(decision: Mapping[str, Any]) -> str:
    reasons = set(decision.get("blocking_reasons") or [])
    if reasons & {
        "legal_profile_missing",
        "legal_profile_not_approved",
        "legal_launch_blocked",
        "seller_binding_missing",
        "seller_unpublished",
        "terms_binding_missing",
        "terms_revision_mismatch",
        "offer_not_approved",
        "rf_advertising_not_approved",
    }:
        return "legal_blocked"
    if reasons & {
        "capacity_guard_required",
        "capacity_projection_unavailable",
        "capacity_forbidden",
        "capacity_resume_hysteresis",
    }:
        return "capacity_blocked"
    if reasons & {"channel_missing", "channel_invalid", "channel_not_allowed"}:
        return "channel_blocked"
    if reasons & {"commercial_revision_mismatch", "campaign_revision_invalid"}:
        return "commercial_revision_stale"
    if "not_started" in reasons:
        return "campaign_not_started"
    if "ended" in reasons or "killed" in reasons:
        return "campaign_ended"
    if reasons & {"paid_cap_missing", "paid_cap_reached"}:
        return "quota_reached"
    return "campaign_not_live"


def _select_offer(
    session,
    *,
    plan_code: str,
    promo_code: str,
    offer_public_id: str,
    now: datetime,
) -> tuple[CommercialOffer | None, IncentiveCampaign | None, PromoCode | None, str | None]:
    promo: PromoCode | None = None
    if promo_code:
        promo = session.query(PromoCode).filter(func.upper(PromoCode.code) == promo_code).first()
        if promo is None:
            return None, None, None, "promo_unknown"
        promo_type = str(promo.promo_type or "").strip().lower()
        value = int(promo.value or 0)
        if promo_type != "discount" or value <= 0 or value > 95:
            return None, None, promo, "promo_invalid"
        if promo.expires_at is not None and _as_utc(promo.expires_at) <= now:
            return None, None, promo, "promo_expired"
        if int(promo.uses_left or 0) == 0:
            return None, None, promo, "promo_depleted"

    query = (
        session.query(CommercialOffer, IncentiveCampaign)
        .join(IncentiveCampaign, IncentiveCampaign.id == CommercialOffer.campaign_id)
        .filter(CommercialOffer.plan_code == plan_code)
    )
    if offer_public_id:
        query = query.filter(CommercialOffer.public_id == offer_public_id)
    if promo_code:
        query = query.filter(
            IncentiveCampaign.campaign_type == "promo",
            func.upper(IncentiveCampaign.target_value) == promo_code,
        )
    rows = query.order_by(CommercialOffer.id.asc()).limit(2).all()
    if not rows:
        return None, None, promo, "offer_not_found"
    if len(rows) > 1:
        return None, None, promo, "offer_ambiguous"
    offer, campaign = rows[0]
    if promo_code and str(campaign.target_value or "").strip().upper() != promo_code:
        return None, None, promo, "offer_mismatch"
    return offer, campaign, promo, None


def _active_reservation_count(session, *, campaign_id: int, offer_id: int) -> tuple[int, int]:
    active_statuses = ("held", "bound")
    campaign_count = (
        session.query(func.count(CommercialReservation.id))
        .filter(
            CommercialReservation.campaign_id == int(campaign_id),
            CommercialReservation.status.in_(active_statuses),
        )
        .scalar()
    )
    offer_count = (
        session.query(func.count(CommercialReservation.id))
        .filter(
            CommercialReservation.offer_id == int(offer_id),
            CommercialReservation.status.in_(active_statuses),
        )
        .scalar()
    )
    return max(0, int(campaign_count or 0)), max(0, int(offer_count or 0))


def _token_payload(
    *,
    subject_hmac: str,
    campaign: IncentiveCampaign,
    offer: CommercialOffer,
    creative: CommercialCreative,
    assignment: CommercialAssignment,
    reservation: CommercialReservation,
) -> dict[str, Any]:
    return {
        "schema": OFFER_TOKEN_SCHEMA,
        "version": OFFER_TOKEN_VERSION,
        "subject": subject_hmac,
        "plan": str(offer.plan_code),
        "campaign": str(campaign.public_id),
        "campaign_revision": int(campaign.revision),
        "creative": str(creative.public_id),
        "variant": str(creative.variant_code),
        "assignment": str(assignment.public_id),
        "offer": str(offer.public_id),
        "base_amount_rub": int(reservation.base_amount_rub),
        "final_amount_rub": int(reservation.final_amount_rub),
        "currency": str(reservation.currency),
        "commercial_revision": str(reservation.commercial_revision),
        "terms_revision": str(offer.terms_revision),
        "reservation": str(reservation.public_id),
        "impression": str(reservation.impression_public_id),
        "click": str(reservation.click_public_id),
        "issued_at": int(_as_utc(reservation.issued_at).timestamp()),
        "hold_expires_at": int(_as_utc(reservation.hold_expires_at).timestamp()),
        "offer_ends_at": int(_as_utc(reservation.offer_ends_at).timestamp()),
    }


def _reservation_block_reason(
    reservation: CommercialReservation,
    *,
    campaign: IncentiveCampaign,
    offer: CommercialOffer,
    creative: CommercialCreative,
    subject_hmac: str,
    commercial_revision: str,
    base_amount_rub: int,
    final_amount_rub: int,
    currency: str,
    impression_public_id: str | None,
    click_public_id: str | None,
    now: datetime,
) -> str | None:
    expected_binding = (
        int(reservation.campaign_id) == int(campaign.id)
        and int(reservation.offer_id) == int(offer.id)
        and int(reservation.creative_id) == int(creative.id)
        and str(reservation.subject_hmac) == subject_hmac
        and str(reservation.commercial_revision) == commercial_revision
        and int(reservation.campaign_revision) == int(campaign.revision)
        and int(reservation.base_amount_rub) == int(base_amount_rub)
        and int(reservation.final_amount_rub) == int(final_amount_rub)
        and str(reservation.currency) == currency
        and (
            impression_public_id is None
            or str(reservation.impression_public_id) == impression_public_id
        )
        and (
            click_public_id is None
            or str(reservation.click_public_id) == click_public_id
        )
    )
    if not expected_binding:
        return "reservation_conflict"
    if (
        str(reservation.status or "") == "held"
        and _as_utc(reservation.hold_expires_at) <= now
    ):
        reservation.status = "expired"
        reservation.updated_at = _naive_utc(now)
        return "reservation_expired"
    if str(reservation.status or "") != "held":
        return "reservation_unavailable"
    return None


def preview_commercial_offer(
    session,
    *,
    plan_code: str,
    promo_code: str | None = None,
    offer_public_id: str | None = None,
    channel: str = "owned_web",
    subject_kind: str | None = None,
    subject_value: str | None = None,
    subject_error: str | None = None,
    impression_public_id: str | None = None,
    click_public_id: str | None = None,
    terms_url: str = "https://pokrov.space/offer/",
    secret: str | bytes | None = None,
    contract: Mapping[str, Any] | None = None,
    now: datetime | None = None,
    hold_ttl_seconds: int | None = None,
) -> dict[str, Any]:
    current = _as_utc(now or _utcnow())
    commercial = dict(contract or get_commercial_contract())
    revision = str(commercial.get("commercial_revision") or "")
    currency = str(commercial.get("currency") or "RUB").strip().upper()
    normalized_plan = str(plan_code or "").strip().lower()[:32]
    normalized_promo = str(promo_code or "").strip().upper()[:20]
    normalized_offer_id = str(offer_public_id or "").strip().lower()[:36]
    normalized_impression_id = str(impression_public_id or "").strip().lower() or None
    normalized_click_id = str(click_public_id or "").strip().lower() or None
    if (normalized_impression_id is None) != (normalized_click_id is None):
        return _empty_preview(
            reason_code="subject_invalid",
            now=current,
            plan_code=normalized_plan,
            currency=currency,
            base_amount_rub=0,
            commercial_revision=revision,
            terms_url=terms_url,
        )
    if normalized_impression_id is not None and (
        IMPRESSION_PUBLIC_ID_RE.fullmatch(normalized_impression_id) is None
        or CLICK_PUBLIC_ID_RE.fullmatch(str(normalized_click_id)) is None
    ):
        return _empty_preview(
            reason_code="subject_invalid",
            now=current,
            plan_code=normalized_plan,
            currency=currency,
            base_amount_rub=0,
            commercial_revision=revision,
            terms_url=terms_url,
        )
    plans = {
        str(item.get("code") or "").strip().lower(): dict(item)
        for item in list(commercial.get("plans") or [])
        if isinstance(item, Mapping)
    }
    plan = plans.get(normalized_plan)
    base = int((plan or {}).get("amount_rub") or 0)

    def invalid(reason: str) -> dict[str, Any]:
        return _empty_preview(
            reason_code=reason,
            now=current,
            plan_code=normalized_plan,
            currency=currency,
            base_amount_rub=base,
            commercial_revision=revision,
            terms_url=terms_url,
        )

    if plan is None:
        return invalid("plan_unknown")
    if plan.get("is_active") is not True or plan.get("public_visibility") == "hidden":
        return invalid("plan_inactive")
    if normalized_offer_id and OFFER_PUBLIC_ID_RE.fullmatch(normalized_offer_id) is None:
        return invalid("offer_not_found")
    if not normalized_promo and not normalized_offer_id:
        return invalid("offer_not_found")

    offer, campaign, promo, selection_error = _select_offer(
        session,
        plan_code=normalized_plan,
        promo_code=normalized_promo,
        offer_public_id=normalized_offer_id,
        now=current,
    )
    if selection_error or offer is None or campaign is None:
        return invalid(selection_error or "offer_not_found")

    try:
        active_units = active_entitlement_capacity_units(session, now=current)
    except Exception:
        active_units = None
    campaign_policy = evaluate_campaign_policy(
        campaign,
        active_units=active_units,
        quality=commercial_quality_snapshot(session, now=current),
        contract=commercial,
        now=current,
    )
    if not bool(campaign_policy.get("activation_allowed")):
        return invalid(_campaign_block_reason(campaign_policy))

    normalized_channel = str(channel or "").strip().lower()[:32]
    if normalized_channel not in set(campaign_record(campaign)["channels"]):
        return invalid("channel_blocked")

    offer_status = str(offer.status or "").strip().lower()
    if offer_status not in OFFER_STATUSES or offer_status != "live":
        return invalid("offer_not_live")
    offer_starts_at = _as_utc(offer.starts_at)
    offer_deadlines = [_as_utc(offer.ends_at)]
    if campaign.ends_at is not None:
        offer_deadlines.append(_as_utc(campaign.ends_at))
    offer_ends_at = min(offer_deadlines)
    if offer_starts_at > current:
        return invalid("offer_not_started")
    if offer_ends_at <= current:
        return invalid("offer_ended")
    if str(offer.commercial_revision or "") != revision:
        return invalid("offer_revision_stale")
    terms_revision = str(commercial.get("terms_revision") or "")
    if str(offer.terms_revision or "") != terms_revision:
        return invalid("offer_terms_stale")
    if str(offer.currency or "").strip().upper() != currency:
        return invalid("offer_price_invalid")
    if int(offer.base_amount_rub or 0) != base:
        return invalid("offer_price_mismatch")
    final = int(offer.final_amount_rub or 0)
    if base <= 0 or final <= 0 or final >= base:
        return invalid("offer_price_invalid")
    if normalized_plan == "start_99":
        return invalid("offer_non_stackable")
    if int(plan.get("base_saving_percent") or 0) > 0 and not bool(offer.stackable_with_base_savings):
        return invalid("offer_non_stackable")
    if promo is not None:
        expected = max(1, int(round(base * (1.0 - (int(promo.value) / 100.0)))))
        if expected != final:
            return invalid("offer_price_mismatch")

    if subject_error:
        return invalid(subject_error if subject_error in OFFER_PREVIEW_REASONS else "subject_invalid")
    if not subject_kind or not subject_value:
        return invalid("subject_missing")
    try:
        subject_hmac = commercial_subject_binding(
            campaign_public_id=str(campaign.public_id),
            subject_kind=subject_kind,
            subject_value=subject_value,
            secret=secret,
        )
    except CommercialOfferTokenError:
        return invalid("signing_unavailable")

    assignment = (
        session.query(CommercialAssignment)
        .filter(
            CommercialAssignment.campaign_id == int(campaign.id),
            CommercialAssignment.offer_id == int(offer.id),
            CommercialAssignment.subject_hmac == subject_hmac,
        )
        .first()
    )
    if assignment is None:
        return invalid("audience_blocked")
    if (
        str(assignment.status or "") not in ASSIGNMENT_STATUSES
        or str(assignment.status or "") != "active"
        or str(assignment.audience_status or "") != "eligible"
    ):
        return invalid("audience_blocked")
    if _as_utc(assignment.expires_at) <= current:
        return invalid("assignment_expired")
    if int(assignment.paid_count or 0) >= int(offer.per_subject_paid_cap or 1):
        return invalid("quota_reached")

    creative = (
        session.query(CommercialCreative)
        .filter(
            CommercialCreative.id == int(assignment.creative_id),
            CommercialCreative.campaign_id == int(campaign.id),
            CommercialCreative.offer_id == int(offer.id),
        )
        .first()
    )
    if creative is None or str(creative.status or "") != "live":
        return invalid("creative_unavailable")
    if str(creative.channel or "") != normalized_channel:
        return invalid("channel_blocked")

    reservation = (
        session.query(CommercialReservation)
        .filter(CommercialReservation.assignment_id == int(assignment.id))
        .first()
    )
    if reservation is not None:
        reservation_reason = _reservation_block_reason(
            reservation,
            campaign=campaign,
            offer=offer,
            creative=creative,
            subject_hmac=subject_hmac,
            commercial_revision=revision,
            base_amount_rub=base,
            final_amount_rub=final,
            currency=currency,
            impression_public_id=normalized_impression_id,
            click_public_id=normalized_click_id,
            now=current,
        )
        if reservation_reason:
            return invalid(reservation_reason)
    else:
        campaign_reserved, offer_reserved = _active_reservation_count(
            session,
            campaign_id=int(campaign.id),
            offer_id=int(offer.id),
        )
        campaign_remaining = (
            int(campaign.paid_cap or 0)
            - int(campaign.paid_conversions_count or 0)
            - campaign_reserved
        )
        offer_remaining = int(offer.paid_cap or 0) - int(offer.paid_count or 0) - offer_reserved
        if min(campaign_remaining, offer_remaining) <= 0:
            return invalid("quota_reached")
        ttl = hold_ttl_seconds if hold_ttl_seconds is not None else configured_offer_hold_ttl_seconds()
        ttl = max(OFFER_HOLD_TTL_MIN_SECONDS, min(OFFER_HOLD_TTL_MAX_SECONDS, int(ttl)))
        hold_expires_at = min(
            current + timedelta(seconds=ttl),
            offer_ends_at,
            _as_utc(assignment.expires_at),
        )
        if hold_expires_at <= current:
            return invalid("reservation_expired")
        candidate = CommercialReservation(
            public_id=f"rsv_{secrets.token_hex(16)}",
            campaign_id=int(campaign.id),
            offer_id=int(offer.id),
            creative_id=int(creative.id),
            assignment_id=int(assignment.id),
            subject_hmac=subject_hmac,
            commercial_revision=revision,
            campaign_revision=int(campaign.revision),
            status="held",
            token_version=OFFER_TOKEN_VERSION,
            impression_public_id=(
                normalized_impression_id or f"imp_{secrets.token_hex(16)}"
            ),
            click_public_id=(normalized_click_id or f"clk_{secrets.token_hex(16)}"),
            base_amount_rub=base,
            final_amount_rub=final,
            currency=currency,
            issued_at=_naive_utc(current),
            hold_expires_at=_naive_utc(hold_expires_at),
            offer_ends_at=_naive_utc(offer_ends_at),
            created_at=_naive_utc(current),
            updated_at=_naive_utc(current),
        )
        try:
            with session.begin_nested():
                session.add(candidate)
                session.flush()
            reservation = candidate
        except IntegrityError:
            reservation = (
                session.query(CommercialReservation)
                .filter(CommercialReservation.assignment_id == int(assignment.id))
                .first()
            )
            if reservation is None:
                return invalid("reservation_conflict")
            reservation_reason = _reservation_block_reason(
                reservation,
                campaign=campaign,
                offer=offer,
                creative=creative,
                subject_hmac=subject_hmac,
                commercial_revision=revision,
                base_amount_rub=base,
                final_amount_rub=final,
                currency=currency,
                impression_public_id=normalized_impression_id,
                click_public_id=normalized_click_id,
                now=current,
            )
            if reservation_reason:
                return invalid(reservation_reason)

    payload = _token_payload(
        subject_hmac=subject_hmac,
        campaign=campaign,
        offer=offer,
        creative=creative,
        assignment=assignment,
        reservation=reservation,
    )
    token = sign_commercial_offer_token(payload, secret=secret)
    reservation.token_sha256 = hashlib.sha256(token.encode("ascii")).hexdigest()
    reservation.updated_at = _naive_utc(current)
    campaign_reserved, offer_reserved = _active_reservation_count(
        session,
        campaign_id=int(campaign.id),
        offer_id=int(offer.id),
    )
    campaign_remaining = (
        int(campaign.paid_cap or 0)
        - int(campaign.paid_conversions_count or 0)
        - campaign_reserved
    )
    offer_remaining = int(offer.paid_cap or 0) - int(offer.paid_count or 0) - offer_reserved
    benefit = base - final
    return {
        "ok": True,
        "valid": True,
        "reason_code": "ready",
        "blocking_reasons": [],
        "plan_code": normalized_plan,
        "currency": currency,
        "base_price_rub": base,
        "final_price_rub": final,
        "benefit_rub": benefit,
        "benefit_percent": int(round((benefit / base) * 100)),
        "server_time": _iso(current),
        "offer_ends_at": _iso(reservation.offer_ends_at),
        "hold_expires_at": _iso(reservation.hold_expires_at),
        "remaining_quota_lower_bound": max(0, min(campaign_remaining, offer_remaining)),
        "terms_url": terms_url,
        "commercial_revision": revision,
        "campaign_id": str(campaign.public_id),
        "creative_id": str(creative.public_id),
        "variant": str(creative.variant_code),
        "assignment_id": str(assignment.public_id),
        "offer_id": str(offer.public_id),
        "reservation_id": str(reservation.public_id),
        "impression_id": str(reservation.impression_public_id),
        "click_id": str(reservation.click_public_id),
        "offer_token": token,
    }

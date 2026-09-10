"""Atomic commercial-offer binding for local RUB payment orders.

The signed offer token is only a transport proof. Current database rows and the
commercial contract are revalidated while the campaign quota owner is locked.
Provider callbacks may consume only the immutable lineage already stored in the
local order intent; callback payloads cannot introduce or repair attribution.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy import func

try:
    from .acquisition_service import acquisition_snapshot, handoff_token_hash
    from .commercial_capacity_quality import commercial_quality_snapshot
    from .commercial_campaign_policy import (
        active_entitlement_capacity_units,
        campaign_record,
        evaluate_campaign_policy,
    )
    from .commercial_contract import get_commercial_contract
    from .commercial_attribution_service import (
        project_commercial_paid_for_order,
        project_commercial_renewal_for_grant,
    )
    from .commercial_offer_service import (
        CommercialOfferTokenError,
        commercial_subject_binding,
        verify_commercial_offer_token,
    )
    from .models import (
        AcquisitionHandoff,
        AcquisitionSession,
        CommercialAssignment,
        CommercialCreative,
        CommercialOffer,
        CommercialReservation,
        EntitlementGrant,
        ExternalOrder,
        IncentiveCampaign,
    )
except ImportError:
    from acquisition_service import acquisition_snapshot, handoff_token_hash
    from commercial_capacity_quality import commercial_quality_snapshot
    from commercial_campaign_policy import (
        active_entitlement_capacity_units,
        campaign_record,
        evaluate_campaign_policy,
    )
    from commercial_contract import get_commercial_contract
    from commercial_attribution_service import (
        project_commercial_paid_for_order,
        project_commercial_renewal_for_grant,
    )
    from commercial_offer_service import (
        CommercialOfferTokenError,
        commercial_subject_binding,
        verify_commercial_offer_token,
    )
    from models import (
        AcquisitionHandoff,
        AcquisitionSession,
        CommercialAssignment,
        CommercialCreative,
        CommercialOffer,
        CommercialReservation,
        EntitlementGrant,
        ExternalOrder,
        IncentiveCampaign,
    )


COMMERCIAL_ORDER_LINEAGE_SCHEMA = "pokrov-commercial-order-lineage-v2"
COMMERCIAL_ORDER_LINEAGE_FIELDS = {
    "schema",
    "campaign",
    "campaign_revision",
    "commercial_revision",
    "terms_revision",
    "offer",
    "creative",
    "variant",
    "assignment",
    "reservation",
    "impression",
    "click",
    "subject",
    "base_amount_rub",
    "final_amount_rub",
    "currency",
    "issued_at",
    "hold_expires_at",
    "offer_ends_at",
    "token_sha256",
}


class CommercialOrderBindingError(RuntimeError):
    """Fail-closed commercial binding error safe for an HTTP detail code."""

    def __init__(self, code: str, *, status_code: int = 409) -> None:
        super().__init__(code)
        self.code = str(code or "commercial_offer_conflict")[:64]
        self.status_code = int(status_code)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _naive_utc(value: datetime) -> datetime:
    return _as_utc(value).replace(tzinfo=None)


def _timestamp(value: datetime) -> int:
    return int(_as_utc(value).timestamp())


def _row_meta(row: Any) -> dict[str, Any]:
    try:
        value = json.loads(str(row.meta_json or "{}"))
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _order_commercial_lineage(row: Any) -> dict[str, Any] | None:
    intent = _row_meta(row).get("order_intent")
    if not isinstance(intent, dict):
        return None
    lineage = intent.get("commercial_offer")
    return dict(lineage) if isinstance(lineage, dict) else None


def lock_commercial_campaign_for_order(
    session,
    *,
    provider: str,
    order_id: str,
) -> bool:
    """Take the commercial campaign lock before callers lock the payment order."""

    snapshot = (
        session.query(ExternalOrder)
        .filter(
            ExternalOrder.provider == str(provider or "").strip().lower()[:32],
            ExternalOrder.order_id == str(order_id or "").strip()[:128],
        )
        .one_or_none()
    )
    lineage = _order_commercial_lineage(snapshot) if snapshot is not None else None
    if lineage is None:
        return False
    campaign_id = str(lineage.get("campaign") or "")
    if not campaign_id:
        raise CommercialOrderBindingError("commercial_lineage_invalid")
    campaign = (
        session.query(IncentiveCampaign)
        .filter(IncentiveCampaign.public_id == campaign_id)
        .with_for_update()
        .one_or_none()
    )
    if campaign is None:
        raise CommercialOrderBindingError("commercial_lineage_missing")
    return True


def _token_error_status(code: str) -> int:
    if code == "offer_token_expired":
        return 410
    if code in {
        "offer_token_malformed",
        "offer_token_signature_invalid",
        "offer_token_fields_invalid",
        "offer_token_version_invalid",
    }:
        return 401
    return 409


def _lineage(
    *,
    token: Mapping[str, Any],
    reservation: CommercialReservation,
) -> dict[str, Any]:
    value = {
        "schema": COMMERCIAL_ORDER_LINEAGE_SCHEMA,
        "campaign": str(token["campaign"]),
        "campaign_revision": int(token["campaign_revision"]),
        "commercial_revision": str(token["commercial_revision"]),
        "terms_revision": str(token["terms_revision"]),
        "offer": str(token["offer"]),
        "creative": str(token["creative"]),
        "variant": str(token["variant"]),
        "assignment": str(token["assignment"]),
        "reservation": str(token["reservation"]),
        "impression": str(token["impression"]),
        "click": str(token["click"]),
        "subject": str(token["subject"]),
        "base_amount_rub": int(token["base_amount_rub"]),
        "final_amount_rub": int(token["final_amount_rub"]),
        "currency": str(token["currency"]),
        "issued_at": int(token["issued_at"]),
        "hold_expires_at": int(token["hold_expires_at"]),
        "offer_ends_at": int(token["offer_ends_at"]),
        "token_sha256": str(reservation.token_sha256 or ""),
    }
    if set(value) != COMMERCIAL_ORDER_LINEAGE_FIELDS:
        raise CommercialOrderBindingError("commercial_lineage_invalid")
    return value


def _load_acquisition_subject(
    session,
    *,
    raw_handle: str,
    reservation: CommercialReservation,
    tg_id: int | None,
    account_id: str | None,
    now: datetime,
) -> tuple[AcquisitionHandoff, AcquisitionSession, dict[str, Any]]:
    handle = str(raw_handle or "").strip()
    if len(handle) < 32:
        raise CommercialOrderBindingError("commercial_subject_invalid")
    handoff = (
        session.query(AcquisitionHandoff)
        .filter(AcquisitionHandoff.token_hash == handoff_token_hash(handle))
        .with_for_update()
        .one_or_none()
    )
    if handoff is None or str(handoff.purpose or "") != "checkout":
        raise CommercialOrderBindingError("commercial_subject_invalid")
    existing_order_id = str(reservation.bound_order_id or "")
    exact_retry = bool(
        handoff.consumed_at is not None
        and existing_order_id
        and str(handoff.bound_order_id or "") == existing_order_id
    )
    if handoff.consumed_at is not None and not exact_retry:
        raise CommercialOrderBindingError("commercial_subject_replayed")
    if not exact_retry and _as_utc(handoff.expires_at) <= now:
        raise CommercialOrderBindingError("commercial_subject_expired", status_code=410)
    acquisition = (
        session.query(AcquisitionSession)
        .filter(AcquisitionSession.id == str(handoff.acquisition_session_id))
        .with_for_update()
        .one_or_none()
    )
    if acquisition is None:
        raise CommercialOrderBindingError("commercial_subject_invalid")
    normalized_account_id = str(account_id or "").strip() or None
    if acquisition.bound_tg_id is not None and tg_id is not None:
        if int(acquisition.bound_tg_id) != int(tg_id):
            raise CommercialOrderBindingError("commercial_subject_cross_account")
    if acquisition.bound_account_id and normalized_account_id:
        if str(acquisition.bound_account_id) != normalized_account_id:
            raise CommercialOrderBindingError("commercial_subject_cross_account")
    return handoff, acquisition, acquisition_snapshot(acquisition)


def _active_bound_count(session, *, campaign_id: int, offer_id: int) -> tuple[int, int, int, int]:
    campaign_bound = int(
        session.query(func.count(CommercialReservation.id))
        .filter(
            CommercialReservation.campaign_id == int(campaign_id),
            CommercialReservation.status == "bound",
        )
        .scalar()
        or 0
    )
    offer_bound = int(
        session.query(func.count(CommercialReservation.id))
        .filter(
            CommercialReservation.offer_id == int(offer_id),
            CommercialReservation.status == "bound",
        )
        .scalar()
        or 0
    )
    campaign_consumed = int(
        session.query(func.count(CommercialReservation.id))
        .filter(
            CommercialReservation.campaign_id == int(campaign_id),
            CommercialReservation.status == "consumed",
        )
        .scalar()
        or 0
    )
    offer_consumed = int(
        session.query(func.count(CommercialReservation.id))
        .filter(
            CommercialReservation.offer_id == int(offer_id),
            CommercialReservation.status == "consumed",
        )
        .scalar()
        or 0
    )
    return campaign_bound, offer_bound, campaign_consumed, offer_consumed


def expire_failed_commercial_reservations(
    session,
    *,
    now: datetime | None = None,
    limit: int = 100,
) -> int:
    """Expire due reservations only when the immutable order records provider failure."""

    current = _as_utc(now or _utcnow())
    candidates = (
        session.query(CommercialReservation)
        .filter(
            CommercialReservation.status == "bound",
            CommercialReservation.hold_expires_at <= _naive_utc(current),
        )
        .order_by(CommercialReservation.hold_expires_at.asc(), CommercialReservation.id.asc())
        .limit(max(1, min(1000, int(limit))))
        .all()
    )
    expired = 0
    candidates.sort(key=lambda row: (int(row.campaign_id), int(row.id)))
    for candidate in candidates:
        campaign = (
            session.query(IncentiveCampaign)
            .filter(IncentiveCampaign.id == int(candidate.campaign_id))
            .with_for_update()
            .one_or_none()
        )
        if campaign is None:
            continue
        order = (
            session.query(ExternalOrder)
            .filter(ExternalOrder.order_id == str(candidate.bound_order_id or ""))
            .order_by(ExternalOrder.id.asc())
            .with_for_update()
            .first()
        )
        reservation = (
            session.query(CommercialReservation)
            .filter(CommercialReservation.id == int(candidate.id))
            .with_for_update()
            .one_or_none()
        )
        if (
            reservation is None
            or str(reservation.status or "") != "bound"
            or _as_utc(reservation.hold_expires_at) > current
            or order is None
            or str(order.order_id or "") != str(reservation.bound_order_id or "")
        ):
            continue
        provider_checkout = (
            _row_meta(order).get("provider_checkout")
            if order is not None
            else None
        )
        if not isinstance(provider_checkout, dict):
            continue
        if str(provider_checkout.get("status") or "").strip().lower() != "error":
            continue
        reservation.status = "expired"
        reservation.released_at = _naive_utc(current)
        reservation.updated_at = _naive_utc(current)
        expired += 1
    return expired


def bind_commercial_offer_to_order(
    session,
    *,
    offer_token: str,
    provider: str,
    candidate_order_id: str,
    plan_code: str,
    currency: str,
    tg_id: int | None = None,
    account_id: str | None = None,
    acquisition_handle: str | None = None,
    secret: str | bytes | None = None,
    contract: Mapping[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Lock, revalidate and bind a reservation before provider I/O."""

    current = _as_utc(now or _utcnow())
    try:
        token = verify_commercial_offer_token(
            offer_token,
            secret=secret,
            now=current,
            allow_expired=True,
        )
    except CommercialOfferTokenError as exc:
        code = str(exc)
        raise CommercialOrderBindingError(code, status_code=_token_error_status(code)) from exc

    normalized_provider = str(provider or "").strip().lower()[:32]
    normalized_plan = str(plan_code or "").strip().lower()[:32]
    normalized_currency = str(currency or "").strip().upper()[:16]
    if not normalized_provider or normalized_plan != str(token["plan"]):
        raise CommercialOrderBindingError("commercial_plan_mismatch")
    if normalized_currency != str(token["currency"]):
        raise CommercialOrderBindingError("commercial_currency_mismatch")

    campaign = (
        session.query(IncentiveCampaign)
        .filter(IncentiveCampaign.public_id == str(token["campaign"]))
        .with_for_update()
        .one_or_none()
    )
    if campaign is None:
        raise CommercialOrderBindingError("commercial_campaign_missing")
    offer = (
        session.query(CommercialOffer)
        .filter(CommercialOffer.public_id == str(token["offer"]))
        .with_for_update()
        .one_or_none()
    )
    creative = (
        session.query(CommercialCreative)
        .filter(CommercialCreative.public_id == str(token["creative"]))
        .with_for_update()
        .one_or_none()
    )
    assignment = (
        session.query(CommercialAssignment)
        .filter(CommercialAssignment.public_id == str(token["assignment"]))
        .with_for_update()
        .one_or_none()
    )
    reservation = (
        session.query(CommercialReservation)
        .filter(CommercialReservation.public_id == str(token["reservation"]))
        .with_for_update()
        .one_or_none()
    )
    if any(row is None for row in (offer, creative, assignment, reservation)):
        raise CommercialOrderBindingError("commercial_lineage_missing")

    campaign_id = int(campaign.id)
    offer_id = int(offer.id)
    creative_id = int(creative.id)
    assignment_id = int(assignment.id)
    relationship_ok = (
        int(offer.campaign_id) == campaign_id
        and int(creative.campaign_id) == campaign_id
        and int(creative.offer_id) == offer_id
        and int(assignment.campaign_id) == campaign_id
        and int(assignment.offer_id) == offer_id
        and int(assignment.creative_id) == creative_id
        and int(reservation.campaign_id) == campaign_id
        and int(reservation.offer_id) == offer_id
        and int(reservation.creative_id) == creative_id
        and int(reservation.assignment_id) == assignment_id
    )
    token_sha256 = hashlib.sha256(str(offer_token).encode("ascii")).hexdigest()
    row_binding_ok = (
        relationship_ok
        and str(reservation.token_sha256 or "") == token_sha256
        and str(reservation.subject_hmac or "") == str(token["subject"])
        and str(assignment.subject_hmac or "") == str(token["subject"])
        and str(campaign.public_id) == str(token["campaign"])
        and int(campaign.revision or 0) == int(token["campaign_revision"])
        and str(offer.plan_code or "").strip().lower() == normalized_plan
        and str(offer.public_id) == str(token["offer"])
        and str(creative.public_id) == str(token["creative"])
        and str(creative.variant_code or "") == str(token["variant"])
        and str(assignment.public_id) == str(token["assignment"])
        and str(reservation.public_id) == str(token["reservation"])
        and str(reservation.impression_public_id) == str(token["impression"])
        and str(reservation.click_public_id) == str(token["click"])
        and int(reservation.base_amount_rub or 0) == int(token["base_amount_rub"])
        and int(reservation.final_amount_rub or 0) == int(token["final_amount_rub"])
        and str(reservation.currency or "").strip().upper() == normalized_currency
        and int(reservation.campaign_revision or 0) == int(token["campaign_revision"])
        and str(reservation.commercial_revision or "") == str(token["commercial_revision"])
        and _timestamp(reservation.issued_at) == int(token["issued_at"])
        and _timestamp(reservation.hold_expires_at) == int(token["hold_expires_at"])
        and _timestamp(reservation.offer_ends_at) == int(token["offer_ends_at"])
    )
    if not row_binding_ok:
        raise CommercialOrderBindingError("commercial_lineage_conflict")

    if _as_utc(reservation.hold_expires_at) <= current:
        if str(reservation.status or "") == "held":
            reservation.status = "expired"
            reservation.updated_at = _naive_utc(current)
        elif str(reservation.status or "") == "bound":
            existing_order = (
                session.query(ExternalOrder)
                .filter(
                    ExternalOrder.provider == normalized_provider,
                    ExternalOrder.order_id == str(reservation.bound_order_id or ""),
                )
                .with_for_update()
                .one_or_none()
            )
            checkout = _row_meta(existing_order).get("provider_checkout") if existing_order else None
            if isinstance(checkout, dict) and str(checkout.get("status") or "") == "error":
                reservation.status = "expired"
                reservation.released_at = _naive_utc(current)
                reservation.updated_at = _naive_utc(current)
        raise CommercialOrderBindingError("offer_token_expired", status_code=410)

    commercial = dict(contract or get_commercial_contract())
    plans = {
        str(item.get("code") or "").strip().lower(): dict(item)
        for item in list(commercial.get("plans") or [])
        if isinstance(item, Mapping)
    }
    plan = plans.get(normalized_plan)
    if plan is None or plan.get("is_active") is not True:
        raise CommercialOrderBindingError("commercial_plan_inactive")
    terms_revision = str(commercial.get("terms_revision") or "")
    commercial_revision = str(commercial.get("commercial_revision") or "")
    if (
        commercial_revision != str(token["commercial_revision"])
        or terms_revision != str(token["terms_revision"])
        or str(campaign.commercial_revision or "") != commercial_revision
        or str(campaign.terms_revision or "") != terms_revision
        or str(offer.commercial_revision or "") != commercial_revision
        or str(offer.terms_revision or "") != terms_revision
    ):
        raise CommercialOrderBindingError("commercial_revision_stale")
    if (
        int(plan.get("amount_rub") or 0) != int(token["base_amount_rub"])
        or int(offer.base_amount_rub or 0) != int(token["base_amount_rub"])
        or int(offer.final_amount_rub or 0) != int(token["final_amount_rub"])
        or str(offer.currency or "").strip().upper() != normalized_currency
    ):
        raise CommercialOrderBindingError("commercial_price_stale")

    try:
        active_units = active_entitlement_capacity_units(session, now=current)
    except Exception:
        active_units = None
    decision = evaluate_campaign_policy(
        campaign,
        active_units=active_units,
        quality=commercial_quality_snapshot(session, now=current),
        contract=commercial,
        now=current,
    )
    if not bool(decision.get("activation_allowed")):
        raise CommercialOrderBindingError("commercial_campaign_blocked")
    if (
        str(offer.status or "") != "live"
        or str(creative.status or "") != "live"
        or str(assignment.status or "") != "active"
        or str(assignment.audience_status or "") != "eligible"
        or _as_utc(offer.starts_at) > current
        or _as_utc(offer.ends_at) <= current
        or _as_utc(assignment.expires_at) <= current
    ):
        raise CommercialOrderBindingError("commercial_offer_not_live")
    if str(creative.channel or "") not in set(campaign_record(campaign)["channels"]):
        raise CommercialOrderBindingError("commercial_channel_blocked")

    subjects: set[str] = set()
    normalized_tg_id = int(tg_id) if tg_id is not None and int(tg_id) > 0 else None
    if normalized_tg_id is not None:
        subjects.add(
            commercial_subject_binding(
                campaign_public_id=str(campaign.public_id),
                subject_kind="telegram",
                subject_value=str(normalized_tg_id),
                secret=secret,
            )
        )
    handoff = None
    acquisition = None
    attribution = None
    if acquisition_handle:
        handoff, acquisition, attribution = _load_acquisition_subject(
            session,
            raw_handle=acquisition_handle,
            reservation=reservation,
            tg_id=normalized_tg_id,
            account_id=account_id,
            now=current,
        )
        subjects.add(
            commercial_subject_binding(
                campaign_public_id=str(campaign.public_id),
                subject_kind="acquisition_session",
                subject_value=str(acquisition.id),
                secret=secret,
            )
        )
        if (
            str(handoff.impression_public_id or "") != str(token["impression"])
            or str(handoff.click_public_id or "") != str(token["click"])
        ):
            raise CommercialOrderBindingError("commercial_touch_mismatch")
    if str(token["subject"]) not in subjects:
        raise CommercialOrderBindingError("commercial_subject_mismatch")

    status = str(reservation.status or "")
    order_id = str(candidate_order_id or "").strip()[:128]
    order_preexisting = False
    if status == "bound":
        order_id = str(reservation.bound_order_id or "")
        existing_order = (
            session.query(ExternalOrder)
            .filter(
                ExternalOrder.provider == normalized_provider,
                ExternalOrder.order_id == order_id,
            )
            .with_for_update()
            .one_or_none()
        )
        if existing_order is None:
            raise CommercialOrderBindingError("commercial_order_binding_conflict")
        order_preexisting = True
    elif status == "held":
        if not order_id:
            raise CommercialOrderBindingError("commercial_order_id_invalid")
        campaign_bound, offer_bound, campaign_consumed, offer_consumed = _active_bound_count(
            session,
            campaign_id=campaign_id,
            offer_id=offer_id,
        )
        campaign_used = max(int(campaign.paid_conversions_count or 0), campaign_consumed)
        offer_used = max(int(offer.paid_count or 0), offer_consumed)
        if (
            int(campaign.paid_cap or 0) <= campaign_used + campaign_bound
            or int(offer.paid_cap or 0) <= offer_used + offer_bound
            or int(assignment.paid_count or 0) >= int(offer.per_subject_paid_cap or 1)
        ):
            raise CommercialOrderBindingError("commercial_quota_reached")
        reservation.status = "bound"
        reservation.bound_order_id = order_id
        reservation.updated_at = _naive_utc(current)
        if handoff is not None and acquisition is not None:
            if handoff.consumed_at is not None:
                raise CommercialOrderBindingError("commercial_subject_replayed")
            normalized_account_id = str(account_id or "").strip() or None
            handoff.consumed_at = _naive_utc(current)
            handoff.bound_tg_id = normalized_tg_id
            handoff.bound_account_id = normalized_account_id
            handoff.bound_order_id = order_id
            if normalized_tg_id is not None:
                acquisition.bound_tg_id = normalized_tg_id
            if normalized_account_id:
                acquisition.bound_account_id = normalized_account_id
    else:
        raise CommercialOrderBindingError("commercial_reservation_unavailable")

    return {
        "order_id": order_id,
        "order_preexisting": order_preexisting,
        "lineage": _lineage(token=token, reservation=reservation),
        "base_amount_rub": int(token["base_amount_rub"]),
        "final_amount_rub": int(token["final_amount_rub"]),
        "currency": normalized_currency,
        "promo_code": str(campaign.target_value or "").strip().upper()[:32],
        "campaign_key": str(campaign.public_id),
        "acquisition_session_id": str(acquisition.id) if acquisition is not None else None,
        "attribution_snapshot": attribution,
    }


def consume_commercial_reservation_for_paid_order(
    session,
    *,
    provider: str,
    order_id: str,
    now: datetime | None = None,
) -> str:
    """Consume the order's pre-bound lineage exactly once in the payment transaction."""

    current = _as_utc(now or _utcnow())
    normalized_provider = str(provider or "").strip().lower()[:32]
    normalized_order_id = str(order_id or "").strip()[:128]
    order_snapshot = (
        session.query(ExternalOrder)
        .filter(
            ExternalOrder.provider == normalized_provider,
            ExternalOrder.order_id == normalized_order_id,
        )
        .one_or_none()
    )
    if order_snapshot is None:
        raise CommercialOrderBindingError("commercial_order_missing")
    lineage = _order_commercial_lineage(order_snapshot)
    if lineage is None:
        return "not_commercial"
    if not isinstance(lineage, dict) or set(lineage) != COMMERCIAL_ORDER_LINEAGE_FIELDS:
        raise CommercialOrderBindingError("commercial_lineage_invalid")
    if lineage.get("schema") != COMMERCIAL_ORDER_LINEAGE_SCHEMA:
        raise CommercialOrderBindingError("commercial_lineage_invalid")

    campaign = (
        session.query(IncentiveCampaign)
        .filter(IncentiveCampaign.public_id == str(lineage["campaign"]))
        .with_for_update()
        .one_or_none()
    )
    order = (
        session.query(ExternalOrder)
        .filter(
            ExternalOrder.provider == normalized_provider,
            ExternalOrder.order_id == normalized_order_id,
        )
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if order is None or _order_commercial_lineage(order) != lineage:
        raise CommercialOrderBindingError("commercial_lineage_conflict")
    offer = (
        session.query(CommercialOffer)
        .filter(CommercialOffer.public_id == str(lineage["offer"]))
        .with_for_update()
        .one_or_none()
    )
    assignment = (
        session.query(CommercialAssignment)
        .filter(CommercialAssignment.public_id == str(lineage["assignment"]))
        .with_for_update()
        .one_or_none()
    )
    reservation = (
        session.query(CommercialReservation)
        .filter(CommercialReservation.public_id == str(lineage["reservation"]))
        .with_for_update()
        .one_or_none()
    )
    if any(row is None for row in (campaign, offer, assignment, reservation)):
        raise CommercialOrderBindingError("commercial_lineage_missing")
    if str(reservation.status or "") == "consumed":
        if str(reservation.bound_order_id or "") != normalized_order_id:
            raise CommercialOrderBindingError("commercial_order_binding_conflict")
        paid_projection = project_commercial_paid_for_order(
            session,
            order=order,
            occurred_at=order.paid_at or current,
        )
        grant = (
            session.query(EntitlementGrant)
            .filter(
                EntitlementGrant.provider == normalized_provider,
                EntitlementGrant.external_order_id == normalized_order_id,
                EntitlementGrant.source == "provider_payment",
            )
            .one_or_none()
        )
        if paid_projection is not None and grant is not None:
            project_commercial_renewal_for_grant(
                session,
                grant=grant,
                occurred_at=order.paid_at or current,
            )
        return "already_consumed"
    if (
        str(reservation.status or "") != "bound"
        or str(reservation.bound_order_id or "") != normalized_order_id
        or int(reservation.campaign_id) != int(campaign.id)
        or int(reservation.offer_id) != int(offer.id)
        or int(reservation.assignment_id) != int(assignment.id)
        or str(reservation.subject_hmac or "") != str(lineage["subject"])
        or str(assignment.subject_hmac or "") != str(lineage["subject"])
        or int(reservation.base_amount_rub or 0) != int(lineage["base_amount_rub"])
        or int(reservation.final_amount_rub or 0) != int(lineage["final_amount_rub"])
        or str(reservation.currency or "").strip().upper() != str(lineage["currency"])
        or str(reservation.token_sha256 or "") != str(lineage["token_sha256"])
        or str(reservation.impression_public_id or "") != str(lineage["impression"])
        or str(reservation.click_public_id or "") != str(lineage["click"])
        or float(order.amount or 0) != float(int(lineage["final_amount_rub"]))
        or str(order.currency or "").strip().upper() != str(lineage["currency"])
        or str(order.plan_code or "").strip().lower() != str(offer.plan_code or "").strip().lower()
    ):
        raise CommercialOrderBindingError("commercial_lineage_conflict")
    if (
        int(campaign.paid_conversions_count or 0) >= int(campaign.paid_cap or 0)
        or int(offer.paid_count or 0) >= int(offer.paid_cap or 0)
        or int(assignment.paid_count or 0) >= int(offer.per_subject_paid_cap or 1)
    ):
        raise CommercialOrderBindingError("commercial_quota_reached")

    campaign.paid_conversions_count = int(campaign.paid_conversions_count or 0) + 1
    offer.paid_count = int(offer.paid_count or 0) + 1
    assignment.paid_count = int(assignment.paid_count or 0) + 1
    reservation.status = "consumed"
    reservation.consumed_at = _naive_utc(current)
    reservation.updated_at = _naive_utc(current)
    paid_projection = project_commercial_paid_for_order(
        session,
        order=order,
        occurred_at=order.paid_at or current,
    )
    grant = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.provider == normalized_provider,
            EntitlementGrant.external_order_id == normalized_order_id,
            EntitlementGrant.source == "provider_payment",
        )
        .one_or_none()
    )
    if paid_projection is not None and grant is not None:
        project_commercial_renewal_for_grant(
            session,
            grant=grant,
            occurred_at=order.paid_at or current,
        )
    return "consumed"

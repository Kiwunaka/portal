from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Callable, Mapping
from urllib.parse import urlencode

from commercial_capacity_quality import commercial_quality_snapshot
from commercial_campaign_policy import (
    active_entitlement_capacity_units,
    campaign_record,
    evaluate_campaign_policy,
)
from commercial_offer_service import CommercialOfferTokenError, commercial_subject_binding
from commercial_pilot_service import campaign_pilot_metadata, sticky_holdout_allocation
from marketing_pilot_contract import get_winback_pilot_contract
from models import (
    CommercialAssignment,
    CommercialCreative,
    CommercialOffer,
    CommercialReservation,
    IncentiveCampaign,
)


_PUBLIC_ID_PATTERNS = {
    "campaign_id": re.compile(r"^cmp_[0-9a-f]{32}$"),
    "offer_id": re.compile(r"^off_[0-9a-f]{32}$"),
    "creative_id": re.compile(r"^crv_[0-9a-f]{32}$"),
    "assignment_id": re.compile(r"^asg_[0-9a-f]{32}$"),
    "impression_id": re.compile(r"^imp_[0-9a-f]{32}$"),
    "click_id": re.compile(r"^clk_[0-9a-f]{32}$"),
}
_LINEAGE_KEYS = frozenset(
    {
        "pilot_id",
        "pilot_revision",
        "pilot_contract_sha256",
        "commercial_revision",
        "campaign_id",
        "offer_id",
        "creative_id",
        "variant",
        "assignment_id",
        "impression_id",
        "click_id",
    }
)
_SURFACE_CONFIG = {
    "app": {
        "channel": "owned_app",
        "slot_id": "app.home.banner",
        "placement": "home_banner",
        "checkout_source": "app",
    },
    "webapp": {
        "channel": "owned_cabinet",
        "slot_id": "webapp.subscription.contextual",
        "placement": "subscription_contextual",
        "checkout_source": "webapp",
    },
}


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _assignment_touch_ids(assignment_public_id: str) -> tuple[str, str]:
    suffix = str(assignment_public_id or "").strip().lower().removeprefix("asg_")
    if re.fullmatch(r"[0-9a-f]{32}", suffix) is None:
        raise ValueError("assignment_id_invalid")
    return f"imp_{suffix}", f"clk_{suffix}"


def _creative_copy(pilot: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    return {
        str(item.get("variant") or "").strip().lower(): {
            "title": str(item.get("title_ru") or "").strip(),
            "body": str(item.get("body_ru") or "").strip(),
        }
        for item in list(pilot.get("creatives") or [])
        if isinstance(item, Mapping)
    }


def _pilot_plan_map(pilot: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("plan_code") or "").strip().lower(): dict(item)
        for item in list((pilot.get("offer") or {}).get("plans") or [])
        if isinstance(item, Mapping)
    }


def _campaign_subject_hmac(campaign: IncentiveCampaign, *, tg_id: int) -> str | None:
    try:
        return commercial_subject_binding(
            campaign_public_id=str(campaign.public_id or ""),
            subject_kind="telegram",
            subject_value=str(int(tg_id)),
        )
    except (CommercialOfferTokenError, ValueError):
        return None


def commercial_winback_promo_slots(
    session,
    *,
    tg_id: int,
    access_state: str,
    checkout_base_url: str,
    issue_checkout_ticket: Callable[..., str],
    surface: str = "app",
    terms_url: str = "https://pokrov.space/offer/",
    now: datetime | None = None,
    pilot_contract: Mapping[str, Any] | None = None,
    commercial_contract: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return at most one fully bound owned-surface winback slot, otherwise fail closed."""

    current = _as_utc(now or datetime.now(timezone.utc))
    pilot = dict(pilot_contract or get_winback_pilot_contract())
    surface_config = _SURFACE_CONFIG.get(str(surface or "").strip().lower())
    if (
        int(tg_id or 0) <= 0
        or surface_config is None
        or str(pilot.get("state") or "") != "owner_approved_ready"
        or str(surface_config["channel"]) not in set(pilot.get("channels") or [])
    ):
        return []
    pilot_offer = dict(pilot.get("offer") or {})
    plan_map = _pilot_plan_map(pilot)
    creative_copy = _creative_copy(pilot)
    if not plan_map or not creative_copy:
        return []
    try:
        active_units = active_entitlement_capacity_units(session, now=current)
    except Exception:
        return []

    campaigns = (
        session.query(IncentiveCampaign)
        .filter(
            IncentiveCampaign.objective == "winback",
            IncentiveCampaign.lifecycle_status == "live",
        )
        .order_by(IncentiveCampaign.id.asc())
        .limit(20)
        .all()
    )
    quality = commercial_quality_snapshot(session, now=current)
    for campaign in campaigns:
        decision = evaluate_campaign_policy(
            campaign,
            active_units=active_units,
            quality=quality,
            contract=commercial_contract,
            now=current,
        )
        if decision.get("activation_allowed") is not True:
            continue
        record = campaign_record(campaign)
        if (
            str(surface_config["channel"]) not in set(record.get("channels") or [])
            or int(record.get("paid_cap") or 0) != int(pilot_offer.get("paid_cap") or 0)
        ):
            continue
        metadata = campaign_pilot_metadata(campaign.metadata_json)
        holdout_percent = metadata.get("holdout_percent")
        if type(holdout_percent) is not int:
            continue
        subject_hmac = _campaign_subject_hmac(campaign, tg_id=int(tg_id))
        if subject_hmac is None:
            continue
        allocation = sticky_holdout_allocation(
            subject_hmac=subject_hmac,
            pilot_id=str(pilot.get("pilot_id") or ""),
            holdout_percent=int(holdout_percent),
        )
        if allocation["cohort"] != "exposed":
            continue
        live_creative_count = int(
            session.query(CommercialCreative)
            .filter(
                CommercialCreative.campaign_id == int(campaign.id),
                CommercialCreative.status == "live",
            )
            .count()
        )
        if not 1 <= live_creative_count <= len(creative_copy):
            continue
        rows = (
            session.query(CommercialAssignment, CommercialOffer, CommercialCreative)
            .join(CommercialOffer, CommercialOffer.id == CommercialAssignment.offer_id)
            .join(CommercialCreative, CommercialCreative.id == CommercialAssignment.creative_id)
            .filter(
                CommercialAssignment.campaign_id == int(campaign.id),
                CommercialAssignment.subject_hmac == subject_hmac,
                CommercialAssignment.status == "active",
                CommercialAssignment.audience_status == "eligible",
                CommercialOffer.status == "live",
                CommercialCreative.status == "live",
                CommercialCreative.channel == str(surface_config["channel"]),
            )
            .order_by(CommercialAssignment.id.asc())
            .limit(3)
            .all()
        )
        for assignment, offer, creative in rows:
            plan = plan_map.get(str(offer.plan_code or "").strip().lower())
            copy = creative_copy.get(str(creative.variant_code or "").strip().lower())
            if plan is None or copy is None:
                continue
            if (
                _as_utc(offer.starts_at) > current
                or _as_utc(offer.ends_at) <= current
                or _as_utc(assignment.expires_at) <= current
                or int(assignment.paid_count or 0) >= int(offer.per_subject_paid_cap or 0)
                or int(offer.base_amount_rub or 0) != int(plan.get("base_amount_rub") or 0)
                or int(offer.final_amount_rub or 0) != int(plan.get("final_amount_rub") or 0)
                or int(offer.paid_cap or 0) != int(pilot_offer.get("paid_cap") or 0)
                or int(offer.per_subject_paid_cap or 0)
                != int(pilot_offer.get("per_subject_paid_cap") or 0)
            ):
                continue
            impression_id, click_id = _assignment_touch_ids(str(assignment.public_id))
            current_naive = current.replace(tzinfo=None)
            campaign_reserved = int(
                session.query(CommercialReservation.id)
                .filter(
                    CommercialReservation.campaign_id == int(campaign.id),
                    CommercialReservation.status == "held",
                    CommercialReservation.hold_expires_at > current_naive,
                )
                .count()
            )
            offer_reserved = int(
                session.query(CommercialReservation.id)
                .filter(
                    CommercialReservation.offer_id == int(offer.id),
                    CommercialReservation.status == "held",
                    CommercialReservation.hold_expires_at > current_naive,
                )
                .count()
            )
            remaining_quota = max(
                0,
                min(
                    int(campaign.paid_cap or 0)
                    - int(campaign.paid_conversions_count or 0)
                    - campaign_reserved,
                    int(offer.paid_cap or 0) - int(offer.paid_count or 0) - offer_reserved,
                ),
            )
            if remaining_quota <= 0:
                continue
            ticket = issue_checkout_ticket(
                tg_id=int(tg_id),
                plan_code=str(offer.plan_code),
                promo_code=str(campaign.target_value or ""),
                campaign_key=str(campaign.public_id or ""),
                source=str(surface_config["checkout_source"]),
                impression_public_id=impression_id,
                click_public_id=click_id,
            )
            if not str(ticket or "").strip():
                continue
            href = f"{str(checkout_base_url).rstrip('/')}/?{urlencode({'plan': str(offer.plan_code), 'promo': str(campaign.target_value or ''), 'checkout_ticket': ticket})}"
            return [
                {
                    "slot_id": str(surface_config["slot_id"]),
                    "surface": str(surface or "").strip().lower(),
                    "enabled": True,
                    "content_id": "winback_offer",
                    "contexts": [str(access_state or "")],
                    "title": copy["title"],
                    "body": copy["body"],
                    "badge_label": "−10%",
                    "image_url": None,
                    "image_layout": "logo",
                    "media_type": None,
                    "media_url": None,
                    "poster_url": None,
                    "fallback_image_url": None,
                    "media_mime": None,
                    "media_width": None,
                    "media_height": None,
                    "media_bytes": None,
                    "media_duration_seconds": None,
                    "autoplay": False,
                    "loop": False,
                    "cta_label": "Вернуться",
                    "cta_href": href,
                    "accent_color": "#0B6B53",
                    "background_color": "#F4FAF7",
                    "text_color": "#10221C",
                    "button_color": "#0B6B53",
                    "button_text_color": "#FFFFFF",
                    "placement": str(surface_config["placement"]),
                    "dismissible": True,
                    "whole_card_clickable": True,
                    "starts_at": _as_utc(campaign.starts_at).isoformat() if campaign.starts_at else None,
                    "ends_at": _as_utc(campaign.ends_at).isoformat() if campaign.ends_at else None,
                    "countdown_mode": "ends_at",
                    "countdown_label": "Предложение действует",
                    "sort_order": 10,
                    "goal": "winback_paid_access",
                    "kind": "first_party_winback",
                    "offer_state": "ready",
                    "reason_code": "ready",
                    "plan_code": str(offer.plan_code),
                    "currency": str(offer.currency),
                    "base_price_rub": int(offer.base_amount_rub),
                    "final_price_rub": int(offer.final_amount_rub),
                    "benefit_percent": int(pilot_offer.get("discount_percent") or 0),
                    "remaining_quota_lower_bound": remaining_quota,
                    "terms_url": str(terms_url or "").strip(),
                    "pilot_id": str(pilot.get("pilot_id") or ""),
                    "pilot_revision": str(pilot.get("revision") or ""),
                    "pilot_contract_sha256": str(pilot.get("contract_sha256") or ""),
                    "commercial_revision": str(pilot.get("commercial_revision") or ""),
                    "campaign_id": str(campaign.public_id),
                    "offer_id": str(offer.public_id),
                    "creative_id": str(creative.public_id),
                    "variant": str(creative.variant_code),
                    "assignment_id": str(assignment.public_id),
                    "impression_id": impression_id,
                    "click_id": click_id,
                }
            ]
    return []


def validate_commercial_promo_event_lineage(
    session,
    *,
    tg_id: int,
    meta: Mapping[str, Any] | None,
    pilot_contract: Mapping[str, Any] | None = None,
) -> dict[str, str] | None:
    raw = dict(meta or {})
    present = _LINEAGE_KEYS & set(raw)
    if not present:
        return None
    if present != _LINEAGE_KEYS:
        raise ValueError("commercial_promo_lineage_incomplete")
    normalized = {key: str(raw.get(key) or "").strip().lower() for key in _LINEAGE_KEYS}
    for key, pattern in _PUBLIC_ID_PATTERNS.items():
        if pattern.fullmatch(normalized[key]) is None:
            raise ValueError("commercial_promo_lineage_invalid")
    if re.fullmatch(r"[a-z0-9_]{1,32}", normalized["variant"]) is None:
        raise ValueError("commercial_promo_lineage_invalid")
    pilot = dict(pilot_contract or get_winback_pilot_contract())
    expected_contract = {
        "pilot_id": str(pilot.get("pilot_id") or "").lower(),
        "pilot_revision": str(pilot.get("revision") or "").lower(),
        "pilot_contract_sha256": str(pilot.get("contract_sha256") or "").lower(),
        "commercial_revision": str(pilot.get("commercial_revision") or "").lower(),
    }
    if any(normalized[key] != value for key, value in expected_contract.items()):
        raise ValueError("commercial_promo_lineage_stale")
    row = (
        session.query(IncentiveCampaign, CommercialOffer, CommercialCreative, CommercialAssignment)
        .join(CommercialOffer, CommercialOffer.campaign_id == IncentiveCampaign.id)
        .join(CommercialCreative, CommercialCreative.offer_id == CommercialOffer.id)
        .join(CommercialAssignment, CommercialAssignment.creative_id == CommercialCreative.id)
        .filter(
            IncentiveCampaign.public_id == normalized["campaign_id"],
            CommercialOffer.public_id == normalized["offer_id"],
            CommercialCreative.public_id == normalized["creative_id"],
            CommercialAssignment.public_id == normalized["assignment_id"],
        )
        .one_or_none()
    )
    if row is None:
        raise ValueError("commercial_promo_lineage_unknown")
    campaign, offer, creative, assignment = row
    relationship_ok = (
        int(offer.campaign_id) == int(campaign.id)
        and int(creative.campaign_id) == int(campaign.id)
        and int(assignment.campaign_id) == int(campaign.id)
        and int(assignment.offer_id) == int(offer.id)
        and int(assignment.creative_id) == int(creative.id)
        and str(creative.variant_code or "").lower() == normalized["variant"]
    )
    expected_subject = _campaign_subject_hmac(campaign, tg_id=int(tg_id))
    impression_id, click_id = _assignment_touch_ids(str(assignment.public_id))
    if (
        not relationship_ok
        or expected_subject is None
        or str(assignment.subject_hmac or "") != expected_subject
        or normalized["impression_id"] != impression_id
        or normalized["click_id"] != click_id
    ):
        raise ValueError("commercial_promo_lineage_conflict")
    return normalized

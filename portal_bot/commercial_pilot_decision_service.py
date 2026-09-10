from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from sqlalchemy import or_

from commercial_attribution_service import commercial_attribution_read_model
from commercial_capacity_quality import commercial_quality_snapshot
from commercial_campaign_policy import (
    active_entitlement_capacity_units,
    evaluate_campaign_policy,
)
from marketing_pilot_contract import get_winback_pilot_contract
from models import (
    AdminActionIntent,
    Event,
    ExternalOrder,
    IncentiveCampaign,
    ServiceIncident,
    SupportTicket,
)


WINBACK_DECISION_STATES = frozenset(
    {
        "stop",
        "continue_collecting",
        "keep",
        "change_copy",
        "change_audience",
        "change_benefit",
        "disable",
        "owner_review_scale_50",
    }
)
_PAYMENT_ERROR_STATUSES = frozenset({"failed", "error", "cancelled", "manual_review"})
_P0_P1_PRIORITIES = frozenset({"critical", "high"})


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _naive_utc(value: datetime) -> datetime:
    return _as_utc(value).replace(tzinfo=None)


def _safe_iso(value: datetime | None) -> str | None:
    return _as_utc(value).isoformat().replace("+00:00", "Z") if value is not None else None


def _campaign_value(row: object | Mapping[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(row, Mapping):
        return row.get(key, default)
    return getattr(row, key, default)


def _campaign_primary_metric(
    attribution: Mapping[str, Any],
    *,
    campaign_id: str,
) -> dict[str, Any]:
    variants = [
        dict(item)
        for item in list(attribution.get("variant_cohorts") or [])
        if isinstance(item, Mapping) and str(item.get("campaign_id") or "") == campaign_id
    ]
    numerator = sum(int(item.get("net_revenue_30d_rub") or 0) for item in variants)
    denominator = sum(int(item.get("paid_capacity_units") or 0) for item in variants)
    return {
        "name": "net_revenue_30d_per_capacity_unit",
        "state": "ready" if denominator > 0 else "insufficient_data",
        "value": round(numerator / denominator, 6) if denominator > 0 else None,
        "net_revenue_30d_rub": numerator if denominator > 0 else None,
        "paid_capacity_units": denominator if denominator > 0 else None,
        "reason": None if denominator > 0 else "no_matured_paid_capacity_evidence",
        "variants": variants,
    }


def winback_guardrail_read_model(
    session,
    *,
    campaign: IncentiveCampaign,
    from_dt: datetime,
    to_dt: datetime,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = _as_utc(now or datetime.now(timezone.utc))
    start = _naive_utc(from_dt)
    end = _naive_utc(to_dt)
    campaign_id = str(campaign.public_id or "")
    orders = (
        session.query(ExternalOrder)
        .filter(
            ExternalOrder.campaign == campaign_id,
            ExternalOrder.created_at >= start,
            ExternalOrder.created_at <= end,
        )
        .order_by(ExternalOrder.id.asc())
        .all()
    )
    order_ids = sorted({str(row.order_id) for row in orders if str(row.order_id or "")})
    payment_errors = sum(
        1 for row in orders if str(row.status or "").strip().lower() in _PAYMENT_ERROR_STATUSES
    )
    support_rows = []
    if order_ids:
        support_rows = (
            session.query(SupportTicket)
            .filter(
                SupportTicket.attempt_ref.in_(order_ids),
                SupportTicket.created_at >= start,
                SupportTicket.created_at <= end,
            )
            .all()
        )
    incident_rows = (
        session.query(ServiceIncident)
        .filter(
            ServiceIncident.status.in_(("confirmed", "resolved")),
            ServiceIncident.started_at <= end,
            or_(ServiceIncident.ended_at.is_(None), ServiceIncident.ended_at >= start),
        )
        .all()
    )
    event_pattern = f'%"campaign_id":"{campaign_id}"%'
    event_counts = {
        name: int(
            session.query(Event.id)
            .filter(
                Event.event_name == name,
                Event.created_at >= start,
                Event.created_at <= end,
                Event.meta_json.like(event_pattern),
            )
            .count()
        )
        for name in ("promo_impression", "promo_click", "promo_dismiss", "promo_expired")
    }
    try:
        active_units = active_entitlement_capacity_units(session, now=current)
    except Exception:
        active_units = None
    policy = evaluate_campaign_policy(
        campaign, active_units=active_units, now=current,
        quality=commercial_quality_snapshot(session, now=current),
    )
    return {
        "schema": "pokrov-winback-guardrails-v1",
        "period": {"from": _safe_iso(from_dt), "to": _safe_iso(to_dt)},
        "generated_at": _safe_iso(current),
        "campaign_id": campaign_id,
        "legal_capacity_policy": policy,
        "quota": {
            "paid_conversions": int(campaign.paid_conversions_count or 0),
            "paid_cap": int(campaign.paid_cap or 0),
            "remaining": max(
                0,
                int(campaign.paid_cap or 0) - int(campaign.paid_conversions_count or 0),
            ),
        },
        "payment_errors": {
            "state": "ready",
            "count": payment_errors,
            "order_count": len(orders),
            "authority": "external_orders_status",
        },
        "support": {
            "state": "ready" if order_ids else "insufficient_data",
            "ticket_count": len(support_rows) if order_ids else None,
            "p0_p1_count": (
                sum(
                    1
                    for row in support_rows
                    if str(row.priority or "").strip().lower() in _P0_P1_PRIORITIES
                )
                if order_ids
                else None
            ),
            "reason": None if order_ids else "no_campaign_order_refs_for_support_join",
            "authority": "support_tickets_attempt_ref_to_server_order",
        },
        "incidents": {
            "state": "ready",
            "count": len(incident_rows),
            "confirmed_open_count": sum(1 for row in incident_rows if row.status == "confirmed"),
            "authority": "service_incidents_overlapping_campaign_window",
        },
        "promo_telemetry": {
            "state": "advisory_only",
            "counts": event_counts,
            "can_select_winner": False,
        },
    }


def build_winback_decision_pack(
    *,
    campaign: object | Mapping[str, Any],
    attribution: Mapping[str, Any],
    guardrails: Mapping[str, Any],
    now: datetime | None = None,
    pilot_contract: Mapping[str, Any] | None = None,
    holdout_evidence: Mapping[str, Any] | None = None,
    action_intents: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    current = _as_utc(now or datetime.now(timezone.utc))
    pilot = dict(pilot_contract or get_winback_pilot_contract())
    campaign_id = str(_campaign_value(campaign, "public_id") or "")
    primary = _campaign_primary_metric(attribution, campaign_id=campaign_id)
    holdout = dict(holdout_evidence or attribution.get("holdout") or {})
    automatic_stop_reasons: list[str] = []
    policy = dict(guardrails.get("legal_capacity_policy") or {})
    policy_reasons = set(policy.get("blocking_reasons") or [])
    if str(pilot.get("state") or "") != "owner_approved_ready":
        automatic_stop_reasons.append("pilot_not_owner_approved")
    if policy.get("activation_allowed") is not True:
        automatic_stop_reasons.extend(sorted(f"policy:{reason}" for reason in policy_reasons))
    quota = dict(guardrails.get("quota") or {})
    if int(quota.get("paid_cap") or 0) <= int(quota.get("paid_conversions") or 0):
        automatic_stop_reasons.append("paid_cap_reached")
    incidents = dict(guardrails.get("incidents") or {})
    if int(incidents.get("count") or 0) > 0:
        automatic_stop_reasons.append("incident_guard_failed")
    support = dict(guardrails.get("support") or {})
    if support.get("state") == "ready" and int(support.get("p0_p1_count") or 0) > 0:
        automatic_stop_reasons.append("p0_p1_support_guard_failed")
    automatic_stop_reasons = sorted(set(automatic_stop_reasons))

    ends_at = _campaign_value(campaign, "ends_at")
    observation_complete = bool(
        isinstance(ends_at, datetime)
        and current >= _as_utc(ends_at) + timedelta(days=int((pilot.get("decision") or {}).get("minimum_observation_days") or 30))
    )
    holdout_ready = holdout.get("state") == "ready"
    winner: dict[str, Any] | None = None
    if primary["state"] == "ready" and holdout_ready:
        ready_variants = [
            item
            for item in primary["variants"]
            if item.get("metric_state") == "ready"
            and item.get("net_revenue_30d_per_capacity_unit") is not None
        ]
        if ready_variants:
            best = max(
                ready_variants,
                key=lambda item: float(item["net_revenue_30d_per_capacity_unit"]),
            )
            winner = {
                "variant": str(best.get("variant") or ""),
                "metric": "net_revenue_30d_per_capacity_unit",
                "value": best.get("net_revenue_30d_per_capacity_unit"),
                "basis": "matured_server_payment_and_capacity_projection",
            }

    if automatic_stop_reasons:
        recommendation = "stop"
    elif not observation_complete or primary["state"] != "ready" or not holdout_ready:
        recommendation = "continue_collecting"
    elif winner is not None:
        recommendation = "owner_review_scale_50"
    else:
        recommendation = "change_copy"
    if recommendation not in WINBACK_DECISION_STATES:
        raise ValueError("winback_decision_state_invalid")
    return {
        "schema": "pokrov-winback-decision-pack-v1",
        "generated_at": _safe_iso(current),
        "pilot": {
            "pilot_id": str(pilot.get("pilot_id") or ""),
            "revision": str(pilot.get("revision") or ""),
            "contract_sha256": str(pilot.get("contract_sha256") or ""),
            "commercial_revision": str(pilot.get("commercial_revision") or ""),
            "marketing_governance_revision": str(pilot.get("marketing_governance_revision") or ""),
            "marketing_governance_sha256": str(pilot.get("marketing_governance_sha256") or ""),
        },
        "campaign": {
            "id": campaign_id,
            "revision": int(_campaign_value(campaign, "revision") or 0),
            "lifecycle_status": str(_campaign_value(campaign, "lifecycle_status") or ""),
            "ends_at": _safe_iso(ends_at) if isinstance(ends_at, datetime) else None,
        },
        "primary_metric": primary,
        "holdout": holdout,
        "guardrails": dict(guardrails),
        "observation_complete": observation_complete,
        "automatic_stop_reasons": automatic_stop_reasons,
        "recommendation": recommendation,
        "winner": winner,
        "winner_can_be_selected_from_ctr": False,
        "scale_automatic": False,
        "maximum_owner_review_paid_cap": int((pilot.get("decision") or {}).get("maximum_next_paid_cap") or 50),
        "available_owner_decisions": sorted(WINBACK_DECISION_STATES),
        "action_intents": [dict(item) for item in list(action_intents or [])],
    }


def build_winback_postmortem(decision_pack: Mapping[str, Any]) -> dict[str, Any]:
    pack = dict(decision_pack)
    encoded = json.dumps(pack, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    winner = pack.get("winner") if isinstance(pack.get("winner"), Mapping) else None
    winner_ready = bool(
        winner
        and (pack.get("primary_metric") or {}).get("state") == "ready"
        and (pack.get("holdout") or {}).get("state") == "ready"
        and pack.get("observation_complete") is True
        and not list(pack.get("automatic_stop_reasons") or [])
    )
    return {
        "schema": "pokrov-winback-postmortem-v1",
        "decision_pack_sha256": hashlib.sha256(encoded).hexdigest(),
        "pilot": dict(pack.get("pilot") or {}),
        "campaign": dict(pack.get("campaign") or {}),
        "recommendation": str(pack.get("recommendation") or "continue_collecting"),
        "winner_state": "ready" if winner_ready else "insufficient_data",
        "winner": dict(winner) if winner_ready else None,
        "refusal_reasons": (
            []
            if winner_ready
            else sorted(
                set(
                    [
                        "winner_requires_matured_net_revenue_30d_per_capacity_unit",
                        "winner_requires_ready_holdout_evidence",
                        "winner_requires_complete_observation_window",
                    ]
                    + list(pack.get("automatic_stop_reasons") or [])
                )
            )
        ),
        "impressions_clicks_ctr_can_select_winner": False,
        "first_payments_can_select_winner": False,
        "scale_requires_owner_approval": True,
    }


def campaign_action_intent_links(session, *, campaign: IncentiveCampaign) -> list[dict[str, Any]]:
    targets = {str(campaign.id), str(campaign.public_id or "")}
    rows = (
        session.query(AdminActionIntent)
        .filter(
            AdminActionIntent.target_type == "campaign",
            AdminActionIntent.target_id.in_(targets),
        )
        .order_by(AdminActionIntent.created_at.desc(), AdminActionIntent.id.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": str(row.id),
            "action": str(row.action),
            "status": str(row.status),
            "risk_level": str(row.risk_level),
            "audit_id": int(row.admin_audit_id) if row.admin_audit_id is not None else None,
            "created_at": _safe_iso(row.created_at),
        }
        for row in rows
    ]


def winback_pilot_operator_readback(
    session,
    *,
    campaign: IncentiveCampaign,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = _as_utc(now or datetime.now(timezone.utc))
    start = _as_utc(campaign.starts_at) if campaign.starts_at else current - timedelta(days=60)
    attribution = commercial_attribution_read_model(
        session,
        from_dt=start,
        to_dt=current,
        now=current,
    )
    guardrails = winback_guardrail_read_model(
        session,
        campaign=campaign,
        from_dt=start,
        to_dt=current,
        now=current,
    )
    decision = build_winback_decision_pack(
        campaign=campaign,
        attribution=attribution,
        guardrails=guardrails,
        now=current,
        action_intents=campaign_action_intent_links(session, campaign=campaign),
    )
    return {
        "decision": decision,
        "postmortem": build_winback_postmortem(decision),
        "attribution": attribution,
    }

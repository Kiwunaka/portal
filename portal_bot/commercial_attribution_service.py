"""Server-owned commercial conversion projections and operator read model.

Rows are deliberately identity-free. Payment callbacks may project only the
immutable lineage already bound to an ExternalOrder. Verified connection
stages may be projected only from ConnectionEvidence written by the observer.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError

try:
    from .commercial_contract import get_commercial_contract
    from .models import (
        CommercialAssignment,
        CommercialConversion,
        CommercialCreative,
        CommercialOffer,
        CommercialReservation,
        ConnectionEvidence,
        EntitlementGrant,
        ExternalOrder,
        IncentiveCampaign,
    )
except ImportError:
    from commercial_contract import get_commercial_contract
    from models import (
        CommercialAssignment,
        CommercialConversion,
        CommercialCreative,
        CommercialOffer,
        CommercialReservation,
        ConnectionEvidence,
        EntitlementGrant,
        ExternalOrder,
        IncentiveCampaign,
    )


COMMERCIAL_CONVERSION_STAGES = frozenset(
    {
        "paid",
        "first_verified_connect",
        "retained_d7",
        "retained_d30",
        "renewal",
        "reversed",
    }
)
COMMERCIAL_LINEAGE_SCHEMA = "pokrov-commercial-order-lineage-v2"
COMMERCIAL_LINEAGE_FIELDS = frozenset(
    {
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
)
RETENTION_EVIDENCE_WINDOWS = {
    "retained_d7": (timedelta(days=7), timedelta(days=14), "paid_at+[7d,14d)"),
    "retained_d30": (timedelta(days=30), timedelta(days=37), "paid_at+[30d,37d)"),
}


class CommercialAttributionError(RuntimeError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.replace(microsecond=0)


def _safe_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _naive_utc(value).isoformat() + "Z"


def _order_meta(order: ExternalOrder) -> dict[str, Any]:
    try:
        value = json.loads(str(order.meta_json or "{}"))
    except (TypeError, ValueError):
        value = {}
    return value if isinstance(value, dict) else {}


def _commercial_lineage(order: ExternalOrder) -> dict[str, Any] | None:
    intent = _order_meta(order).get("order_intent")
    if not isinstance(intent, dict):
        return None
    lineage = intent.get("commercial_offer")
    if lineage is None:
        return None
    if (
        not isinstance(lineage, dict)
        or set(lineage) != COMMERCIAL_LINEAGE_FIELDS
        or lineage.get("schema") != COMMERCIAL_LINEAGE_SCHEMA
    ):
        raise CommercialAttributionError("commercial_lineage_invalid")
    return dict(lineage)


def _capacity_cost_units(plan_code: str) -> int:
    code = str(plan_code or "").strip().lower()
    for plan in list(get_commercial_contract().get("plans") or []):
        if not isinstance(plan, Mapping):
            continue
        if str(plan.get("code") or "").strip().lower() == code:
            return max(0, int(plan.get("capacity_cost_units") or 0))
    return 0


def _evidence_ref(namespace: str, value: str) -> str:
    digest = hashlib.sha256(f"{namespace}\x00{value}".encode("utf-8")).hexdigest()
    return digest[:64]


def _lineage_rows(
    session,
    *,
    lineage: Mapping[str, Any],
) -> tuple[
    IncentiveCampaign,
    CommercialOffer,
    CommercialCreative,
    CommercialAssignment,
    CommercialReservation,
]:
    campaign = session.query(IncentiveCampaign).filter_by(public_id=str(lineage["campaign"])).one_or_none()
    offer = session.query(CommercialOffer).filter_by(public_id=str(lineage["offer"])).one_or_none()
    creative = session.query(CommercialCreative).filter_by(public_id=str(lineage["creative"])).one_or_none()
    assignment = session.query(CommercialAssignment).filter_by(public_id=str(lineage["assignment"])).one_or_none()
    reservation = session.query(CommercialReservation).filter_by(public_id=str(lineage["reservation"])).one_or_none()
    if any(row is None for row in (campaign, offer, creative, assignment, reservation)):
        raise CommercialAttributionError("commercial_lineage_missing")
    if (
        int(offer.campaign_id) != int(campaign.id)
        or int(creative.campaign_id) != int(campaign.id)
        or int(creative.offer_id) != int(offer.id)
        or int(assignment.campaign_id) != int(campaign.id)
        or int(assignment.offer_id) != int(offer.id)
        or int(assignment.creative_id) != int(creative.id)
        or int(reservation.campaign_id) != int(campaign.id)
        or int(reservation.offer_id) != int(offer.id)
        or int(reservation.creative_id) != int(creative.id)
        or int(reservation.assignment_id) != int(assignment.id)
        or str(creative.variant_code) != str(lineage["variant"])
        or str(reservation.impression_public_id) != str(lineage["impression"])
        or str(reservation.click_public_id) != str(lineage["click"])
        or str(reservation.bound_order_id or "") == ""
    ):
        raise CommercialAttributionError("commercial_lineage_conflict")
    return campaign, offer, creative, assignment, reservation


def _projection_identity(row: CommercialConversion) -> tuple[Any, ...]:
    return (
        int(row.campaign_id),
        int(row.offer_id),
        int(row.creative_id),
        int(row.assignment_id),
        int(row.reservation_id),
        str(row.campaign_public_id),
        str(row.offer_public_id),
        str(row.creative_public_id),
        str(row.variant_code),
        str(row.assignment_public_id),
        str(row.reservation_public_id),
        str(row.impression_public_id),
        str(row.click_public_id),
        str(row.commercial_revision),
        int(row.campaign_revision),
        str(row.currency),
    )


def _upsert_stage(
    session,
    *,
    provider: str,
    order_id: str,
    stage: str,
    source: CommercialConversion,
    occurred_at: datetime,
    evidence_kind: str,
    evidence_ref: str,
    gross_amount_rub: int = 0,
    refund_amount_rub: int = 0,
    reversal_kind: str | None = None,
) -> CommercialConversion:
    normalized_stage = str(stage or "").strip().lower()
    if normalized_stage not in COMMERCIAL_CONVERSION_STAGES:
        raise CommercialAttributionError("commercial_stage_invalid")
    normalized_provider = str(provider or "").strip().lower()[:32]
    normalized_order = str(order_id or "").strip()[:128]
    existing = (
        session.query(CommercialConversion)
        .filter_by(
            provider=normalized_provider,
            order_id=normalized_order,
            stage=normalized_stage,
        )
        .with_for_update()
        .one_or_none()
    )
    if existing is not None:
        if (
            _projection_identity(existing) != _projection_identity(source)
            or int(existing.gross_amount_rub or 0) != int(gross_amount_rub)
            or int(existing.refund_amount_rub or 0) != int(refund_amount_rub)
        ):
            raise CommercialAttributionError("commercial_projection_conflict")
        if normalized_stage == "reversed" and reversal_kind == "chargeback":
            existing.reversal_kind = "chargeback"
            existing.updated_at = _naive_utc(occurred_at)
        return existing

    row = CommercialConversion(
        id=f"cnv_{secrets.token_hex(16)}",
        provider=normalized_provider,
        order_id=normalized_order,
        stage=normalized_stage,
        campaign_id=int(source.campaign_id),
        offer_id=int(source.offer_id),
        creative_id=int(source.creative_id),
        assignment_id=int(source.assignment_id),
        reservation_id=int(source.reservation_id),
        campaign_public_id=str(source.campaign_public_id),
        offer_public_id=str(source.offer_public_id),
        creative_public_id=str(source.creative_public_id),
        variant_code=str(source.variant_code),
        assignment_public_id=str(source.assignment_public_id),
        reservation_public_id=str(source.reservation_public_id),
        impression_public_id=str(source.impression_public_id),
        click_public_id=str(source.click_public_id),
        commercial_revision=str(source.commercial_revision),
        campaign_revision=int(source.campaign_revision),
        capacity_cost_units=int(source.capacity_cost_units or 0),
        currency=str(source.currency),
        gross_amount_rub=max(0, int(gross_amount_rub)),
        refund_amount_rub=max(0, int(refund_amount_rub)),
        reversal_kind=(str(reversal_kind or "")[:24] or None),
        evidence_kind=str(evidence_kind or "")[:40],
        evidence_ref=str(evidence_ref or "")[:64],
        occurred_at=_naive_utc(occurred_at),
        created_at=_naive_utc(_utcnow()),
        updated_at=_naive_utc(_utcnow()),
    )
    try:
        with session.begin_nested():
            session.add(row)
            session.flush()
        return row
    except IntegrityError:
        winner = (
            session.query(CommercialConversion)
            .filter_by(
                provider=normalized_provider,
                order_id=normalized_order,
                stage=normalized_stage,
            )
            .with_for_update()
            .one()
        )
        if (
            _projection_identity(winner) != _projection_identity(source)
            or int(winner.gross_amount_rub or 0) != int(gross_amount_rub)
            or int(winner.refund_amount_rub or 0) != int(refund_amount_rub)
        ):
            raise CommercialAttributionError("commercial_projection_conflict")
        return winner


def project_commercial_paid_for_order(
    session,
    *,
    order: ExternalOrder,
    occurred_at: datetime,
) -> CommercialConversion | None:
    lineage = _commercial_lineage(order)
    if lineage is None:
        return None
    campaign, offer, creative, assignment, reservation = _lineage_rows(
        session,
        lineage=lineage,
    )
    if (
        str(reservation.bound_order_id or "") != str(order.order_id)
        or str(reservation.status or "") != "consumed"
        or int(lineage["final_amount_rub"]) != int(round(float(order.amount or 0)))
        or str(lineage["currency"]).upper() != str(order.currency or "").upper()
    ):
        raise CommercialAttributionError("commercial_paid_projection_conflict")
    source = CommercialConversion(
        campaign_id=int(campaign.id),
        offer_id=int(offer.id),
        creative_id=int(creative.id),
        assignment_id=int(assignment.id),
        reservation_id=int(reservation.id),
        campaign_public_id=str(lineage["campaign"]),
        offer_public_id=str(lineage["offer"]),
        creative_public_id=str(lineage["creative"]),
        variant_code=str(lineage["variant"]),
        assignment_public_id=str(lineage["assignment"]),
        reservation_public_id=str(lineage["reservation"]),
        impression_public_id=str(lineage["impression"]),
        click_public_id=str(lineage["click"]),
        commercial_revision=str(lineage["commercial_revision"]),
        campaign_revision=int(lineage["campaign_revision"]),
        capacity_cost_units=_capacity_cost_units(str(order.plan_code or offer.plan_code)),
        currency=str(lineage["currency"]),
    )
    return _upsert_stage(
        session,
        provider=str(order.provider),
        order_id=str(order.order_id),
        stage="paid",
        source=source,
        occurred_at=occurred_at,
        evidence_kind="signed_payment_callback",
        evidence_ref=_evidence_ref("paid-order", f"{order.provider}:{order.order_id}"),
        gross_amount_rub=int(lineage["final_amount_rub"]),
    )


def project_commercial_renewal_for_grant(
    session,
    *,
    grant: EntitlementGrant,
    occurred_at: datetime,
) -> CommercialConversion | None:
    if str(grant.source or "") != "provider_payment":
        return None
    paid = (
        session.query(CommercialConversion)
        .filter_by(
            provider=str(grant.provider or "").lower(),
            order_id=str(grant.external_order_id or ""),
            stage="paid",
        )
        .one_or_none()
    )
    if paid is None:
        return None
    prior = (
        session.query(EntitlementGrant.id)
        .filter(
            EntitlementGrant.account_id == str(grant.account_id),
            EntitlementGrant.source == "provider_payment",
            EntitlementGrant.id != str(grant.id),
            EntitlementGrant.created_at < grant.created_at,
        )
        .first()
    )
    if prior is None:
        return None
    return _upsert_stage(
        session,
        provider=str(paid.provider),
        order_id=str(paid.order_id),
        stage="renewal",
        source=paid,
        occurred_at=occurred_at,
        evidence_kind="payment_entitlement_grant",
        evidence_ref=str(grant.id),
    )


def project_commercial_verified_connection(
    session,
    *,
    evidence: ConnectionEvidence,
) -> list[CommercialConversion]:
    if str(evidence.evidence_kind or "") != "observer_connection":
        raise CommercialAttributionError("commercial_connection_evidence_invalid")
    observed_at = _naive_utc(evidence.observed_at)
    paid_rows = (
        session.query(CommercialConversion)
        .join(
            EntitlementGrant,
            and_(
                EntitlementGrant.provider == CommercialConversion.provider,
                EntitlementGrant.external_order_id == CommercialConversion.order_id,
                EntitlementGrant.source == "provider_payment",
            ),
        )
        .filter(
            CommercialConversion.stage == "paid",
            CommercialConversion.occurred_at <= observed_at,
            EntitlementGrant.account_id == str(evidence.account_id),
            or_(EntitlementGrant.starts_at.is_(None), EntitlementGrant.starts_at <= observed_at),
            or_(EntitlementGrant.expires_at.is_(None), EntitlementGrant.expires_at > observed_at),
            or_(EntitlementGrant.reversed_at.is_(None), EntitlementGrant.reversed_at > observed_at),
        )
        .order_by(CommercialConversion.occurred_at.desc(), CommercialConversion.id.desc())
        .all()
    )
    if not paid_rows:
        return []
    projected = [
        _upsert_stage(
            session,
            provider=str(paid_rows[0].provider),
            order_id=str(paid_rows[0].order_id),
            stage="first_verified_connect",
            source=paid_rows[0],
            occurred_at=observed_at,
            evidence_kind="observer_connection",
            evidence_ref=str(evidence.id),
        )
    ]
    for paid in paid_rows:
        elapsed = observed_at - _naive_utc(paid.occurred_at)
        for stage, (window_start, window_end, _label) in RETENTION_EVIDENCE_WINDOWS.items():
            if window_start <= elapsed < window_end:
                projected.append(
                    _upsert_stage(
                        session,
                        provider=str(paid.provider),
                        order_id=str(paid.order_id),
                        stage=stage,
                        source=paid,
                        occurred_at=observed_at,
                        evidence_kind="observer_connection",
                        evidence_ref=str(evidence.id),
                    )
                )
    return projected


def record_commercial_reversal_projection(
    session,
    *,
    order: ExternalOrder,
    reversal_kind: str,
    occurred_at: datetime,
) -> CommercialConversion | None:
    if _commercial_lineage(order) is None:
        return None
    kind = str(reversal_kind or "").strip().lower()
    if kind not in {"refund", "chargeback"}:
        kind = "refund"
    paid = (
        session.query(CommercialConversion)
        .filter_by(provider=str(order.provider), order_id=str(order.order_id), stage="paid")
        .one_or_none()
    )
    if paid is None:
        paid_at = order.paid_at or occurred_at
        paid = project_commercial_paid_for_order(
            session,
            order=order,
            occurred_at=paid_at,
        )
    if paid is None:
        return None
    return _upsert_stage(
        session,
        provider=str(order.provider),
        order_id=str(order.order_id),
        stage="reversed",
        source=paid,
        occurred_at=occurred_at,
        evidence_kind="signed_payment_reversal",
        evidence_ref=_evidence_ref("reversed-order", f"{order.provider}:{order.order_id}"),
        refund_amount_rub=int(paid.gross_amount_rub or 0),
        reversal_kind=kind,
    )


def commercial_attribution_read_model(
    session,
    *,
    from_dt: datetime,
    to_dt: datetime,
    now: datetime | None = None,
) -> dict[str, Any]:
    generated_at = _naive_utc(now or _utcnow())
    start = _naive_utc(from_dt)
    end = _naive_utc(to_dt)
    rows = (
        session.query(CommercialConversion)
        .filter(
            CommercialConversion.occurred_at >= start,
            CommercialConversion.occurred_at <= end,
        )
        .order_by(CommercialConversion.occurred_at.asc(), CommercialConversion.id.asc())
        .all()
    )
    groups: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        key = (
            str(row.campaign_public_id),
            int(row.campaign_revision),
            str(row.commercial_revision),
            int(row.capacity_cost_units or 0),
        )
        target = groups.setdefault(
            key,
            {
                "campaign_id": key[0],
                "campaign_revision": key[1],
                "commercial_revision": key[2],
                "capacity_cost_units_per_paid_conversion": key[3],
                "gross_revenue_rub": 0,
                "refund_revenue_rub": 0,
                "net_revenue_rub": 0,
                "paid_conversions": 0,
                "first_verified_connects": 0,
                "retained_d7": 0,
                "retained_d30": 0,
                "renewals": 0,
                "paid_capacity_units": 0,
            },
        )
        stage = str(row.stage)
        if stage == "paid":
            target["gross_revenue_rub"] += int(row.gross_amount_rub or 0)
            target["paid_conversions"] += 1
            target["paid_capacity_units"] += int(row.capacity_cost_units or 0)
        elif stage == "reversed":
            target["refund_revenue_rub"] += int(row.refund_amount_rub or 0)
        elif stage == "first_verified_connect":
            target["first_verified_connects"] += 1
        elif stage == "retained_d7":
            target["retained_d7"] += 1
        elif stage == "retained_d30":
            target["retained_d30"] += 1
        elif stage == "renewal":
            target["renewals"] += 1
    for target in groups.values():
        target["net_revenue_rub"] = (
            int(target["gross_revenue_rub"]) - int(target["refund_revenue_rub"])
        )
    order_rows: dict[tuple[str, str], list[CommercialConversion]] = {}
    for row in rows:
        order_rows.setdefault((str(row.provider), str(row.order_id)), []).append(row)
    maturity_cutoff = generated_at - timedelta(days=30)
    mature_groups: dict[tuple[str, int, str, str], dict[str, Any]] = {}
    for related in order_rows.values():
        paid = next((item for item in related if str(item.stage) == "paid"), None)
        if paid is None or _naive_utc(paid.occurred_at) > maturity_cutoff:
            continue
        paid_at = _naive_utc(paid.occurred_at)
        d30_end = paid_at + timedelta(days=30)
        refund_30d = sum(
            int(item.refund_amount_rub or 0)
            for item in related
            if str(item.stage) == "reversed"
            and paid_at <= _naive_utc(item.occurred_at) <= d30_end
        )
        key = (
            str(paid.campaign_public_id),
            int(paid.campaign_revision),
            str(paid.commercial_revision),
            str(paid.variant_code),
        )
        metric = mature_groups.setdefault(
            key,
            {
                "campaign_id": key[0],
                "campaign_revision": key[1],
                "commercial_revision": key[2],
                "variant": key[3],
                "cohort": "exposed",
                "matured_paid_conversions": 0,
                "gross_revenue_30d_rub": 0,
                "refund_revenue_30d_rub": 0,
                "net_revenue_30d_rub": 0,
                "paid_capacity_units": 0,
            },
        )
        metric["matured_paid_conversions"] += 1
        metric["gross_revenue_30d_rub"] += int(paid.gross_amount_rub or 0)
        metric["refund_revenue_30d_rub"] += refund_30d
        metric["paid_capacity_units"] += int(paid.capacity_cost_units or 0)
    for metric in mature_groups.values():
        metric["net_revenue_30d_rub"] = int(metric["gross_revenue_30d_rub"]) - int(
            metric["refund_revenue_30d_rub"]
        )
        denominator = int(metric["paid_capacity_units"])
        metric["net_revenue_30d_per_capacity_unit"] = (
            round(int(metric["net_revenue_30d_rub"]) / denominator, 6)
            if denominator > 0
            else None
        )
        metric["metric_state"] = "ready" if denominator > 0 else "insufficient_data"
    variant_metrics = [mature_groups[key] for key in sorted(mature_groups)]
    campaigns = [groups[key] for key in sorted(groups)]
    summary_keys = (
        "gross_revenue_rub",
        "refund_revenue_rub",
        "net_revenue_rub",
        "paid_conversions",
        "first_verified_connects",
        "retained_d7",
        "retained_d30",
        "renewals",
        "paid_capacity_units",
    )
    summary = {key: sum(int(row[key]) for row in campaigns) for key in summary_keys}
    primary_numerator = sum(int(row["net_revenue_30d_rub"]) for row in variant_metrics)
    primary_denominator = sum(int(row["paid_capacity_units"]) for row in variant_metrics)
    primary_metric = {
        "name": "net_revenue_30d_per_capacity_unit",
        "state": "ready" if primary_denominator > 0 else "insufficient_data",
        "value": (
            round(primary_numerator / primary_denominator, 6)
            if primary_denominator > 0
            else None
        ),
        "net_revenue_30d_rub": primary_numerator if primary_denominator > 0 else None,
        "paid_capacity_units": primary_denominator if primary_denominator > 0 else None,
        "maturity_cutoff": _safe_iso(maturity_cutoff),
        "minimum_observation_days": 30,
        "reason": None if primary_denominator > 0 else "no_matured_paid_capacity_evidence",
    }
    source_updated_at = max((row.updated_at for row in rows), default=None)
    freshness_seconds = (
        max(0, int((generated_at - _naive_utc(source_updated_at)).total_seconds()))
        if source_updated_at is not None
        else None
    )
    return {
        "schema": "pokrov-commercial-attribution-read-model-v1",
        "authority": {
            "revenue": "signed_payment_callbacks_and_external_orders",
            "verified_connection": "connection_evidence:observer_connection",
            "telemetry_is_payment_truth": False,
        },
        "period": {"from": _safe_iso(start), "to": _safe_iso(end)},
        "retention_windows": {
            stage: label
            for stage, (_window_start, _window_end, label) in RETENTION_EVIDENCE_WINDOWS.items()
        },
        "freshness": {
            "generated_at": _safe_iso(generated_at),
            "source_updated_at": _safe_iso(source_updated_at),
            "age_seconds": freshness_seconds,
            "mode": "transactional_projection",
        },
        "summary": summary,
        "primary_metric": primary_metric,
        "variant_cohorts": variant_metrics,
        "holdout": {
            "state": "insufficient_data",
            "reason": "holdout_outcomes_require_separate_identity_free_observation_projection",
            "fabricated_zero": False,
        },
        "campaigns": campaigns,
    }

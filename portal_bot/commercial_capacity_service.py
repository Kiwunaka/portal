"""Commercial capacity automation and read-only forecast.

Active entitlement grants remain the only capacity-unit authority. Reservation
and campaign counters are forecast inputs only; this module never grants or
revokes access.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy import func, or_

from commercial_campaign_policy import (
    CAPACITY_EXEMPT_OBJECTIVES,
    active_entitlement_capacity_units,
    campaign_record,
    capacity_snapshot,
    evaluate_campaign_policy,
)
from commercial_contract import get_commercial_contract
from models import (
    AdminAudit,
    CommercialOffer,
    CommercialReservation,
    IncentiveCampaign,
)


COMMERCIAL_CAPACITY_AUTOMATION_SCHEMA = "pokrov-commercial-capacity-automation-v1"
COMMERCIAL_CAPACITY_POLICY_ID = "commercial-capacity-owner-policy-v1"
AUTO_MANAGED_OBJECTIVES = frozenset({"acquisition", "winback"})
CAPACITY_PAUSE_REASONS = frozenset(
    {"capacity_forbidden", "capacity_resume_hysteresis"}
)
PENDING_RESERVATION_STATUSES = frozenset({"held", "bound"})


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _db_time(value: datetime) -> datetime:
    return _as_utc(value).replace(tzinfo=None)


def _safe_iso(value: object) -> str | None:
    if not isinstance(value, datetime):
        return None
    return _as_utc(value).isoformat()


def _plan_capacity_costs(contract: Mapping[str, Any]) -> dict[str, int]:
    costs: dict[str, int] = {}
    for raw in list(contract.get("plans") or []):
        if not isinstance(raw, Mapping):
            continue
        code = str(raw.get("code") or "").strip().lower()
        if code:
            costs[code] = max(1, int(raw.get("capacity_cost_units") or 1))
    return costs


def _reservation_forecast(
    session,
    *,
    now: datetime,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    costs = _plan_capacity_costs(contract)
    current_db = _db_time(now)
    rows = (
        session.query(
            CommercialReservation.campaign_id,
            CommercialReservation.status,
            CommercialOffer.plan_code,
            func.count(CommercialReservation.id),
        )
        .join(CommercialOffer, CommercialOffer.id == CommercialReservation.offer_id)
        .filter(
            or_(
                CommercialReservation.status != "held",
                CommercialReservation.hold_expires_at > current_db,
            )
        )
        .group_by(
            CommercialReservation.campaign_id,
            CommercialReservation.status,
            CommercialOffer.plan_code,
        )
        .all()
    )
    status_counts: dict[str, int] = {}
    campaign_counts: dict[int, dict[str, int]] = {}
    pending_capacity_units = 0
    for campaign_id, status, plan_code, raw_count in rows:
        normalized_status = str(status or "unknown").strip().lower()[:24]
        count = max(0, int(raw_count or 0))
        status_counts[normalized_status] = status_counts.get(normalized_status, 0) + count
        campaign_bucket = campaign_counts.setdefault(int(campaign_id), {})
        campaign_bucket[normalized_status] = campaign_bucket.get(normalized_status, 0) + count
        if normalized_status in PENDING_RESERVATION_STATUSES:
            pending_capacity_units += count * costs.get(
                str(plan_code or "").strip().lower(), 1
            )
    return {
        "reservation_counts": dict(sorted(status_counts.items())),
        "campaign_reservation_counts": {
            str(campaign_id): dict(sorted(values.items()))
            for campaign_id, values in sorted(campaign_counts.items())
        },
        "pending_capacity_units": pending_capacity_units,
    }


def commercial_capacity_readback(
    session,
    *,
    now: datetime | None = None,
    contract: Mapping[str, Any] | None = None,
    active_units: int | None = None,
) -> dict[str, Any]:
    """Return deterministic capacity, reservation and campaign forecast facts."""

    current = _as_utc(now or datetime.now(timezone.utc))
    commercial = dict(contract or get_commercial_contract())
    resolved_units = (
        active_entitlement_capacity_units(session, now=current)
        if active_units is None
        else max(0, int(active_units))
    )
    capacity = capacity_snapshot(
        active_units=resolved_units,
        contract=commercial,
    )
    reservations = _reservation_forecast(session, now=current, contract=commercial)
    pending_units = int(reservations["pending_capacity_units"])
    projected_units = resolved_units + pending_units
    projected_ratio = projected_units / max(1, capacity.limit_units)
    pause_threshold_units = int(math.ceil(capacity.limit_units * capacity.pause_at_ratio))
    resume_below_units = int(
        math.ceil(capacity.limit_units * capacity.resume_below_ratio) - 1
    )

    campaign_rows = (
        session.query(IncentiveCampaign)
        .order_by(IncentiveCampaign.id.asc())
        .all()
    )
    last_evaluation = max(
        (
            _as_utc(value)
            for value in (
                getattr(row, "last_policy_evaluated_at", None)
                for row in campaign_rows
            )
            if isinstance(value, datetime)
        ),
        default=None,
    )
    last_transition = (
        session.query(AdminAudit)
        .filter(AdminAudit.action.in_(["capacity.auto_pause", "capacity.auto_hold", "capacity.auto_resume"]))
        .order_by(AdminAudit.created_at.desc(), AdminAudit.id.desc())
        .first()
    )
    lifecycle_counts: dict[str, int] = {}
    campaign_readback: list[dict[str, Any]] = []
    campaign_reservations = dict(reservations["campaign_reservation_counts"])
    for row in campaign_rows:
        lifecycle = str(row.lifecycle_status or "unknown").strip().lower()
        lifecycle_counts[lifecycle] = lifecycle_counts.get(lifecycle, 0) + 1
        campaign_readback.append(
            {
                "id": int(row.id),
                "public_id": str(row.public_id or "") or None,
                "revision": max(1, int(row.revision or 1)),
                "objective": str(row.objective or ""),
                "lifecycle_status": lifecycle,
                "state_reason": str(row.state_reason or "legacy_unclassified"),
                "capacity_band": str(row.capacity_band or "unknown"),
                "paid_cap": max(0, int(row.paid_cap or 0)),
                "paid_count": max(0, int(row.paid_conversions_count or 0)),
                "reservation_counts": dict(
                    campaign_reservations.get(str(int(row.id)), {})
                ),
                "last_evaluated_at": _safe_iso(row.last_policy_evaluated_at),
                "auto_managed": str(row.objective or "").strip().lower()
                in AUTO_MANAGED_OBJECTIVES,
                "capacity_exempt": str(row.objective or "").strip().lower()
                in CAPACITY_EXEMPT_OBJECTIVES,
            }
        )

    gate_reasons: list[str] = []
    if not capacity.acquisition_permitted:
        gate_reasons.append("capacity_forbidden")
    if projected_ratio >= capacity.pause_at_ratio:
        gate_reasons.append("pending_reservations_cross_pause_threshold")

    return {
        "schema": COMMERCIAL_CAPACITY_AUTOMATION_SCHEMA,
        "policy_id": COMMERCIAL_CAPACITY_POLICY_ID,
        "commercial_revision": str(commercial.get("commercial_revision") or ""),
        "contract_sha256": str(commercial.get("contract_sha256") or ""),
        "evaluated_at": current.isoformat(),
        "last_policy_evaluated_at": _safe_iso(last_evaluation),
        "last_transition_at": _safe_iso(
            getattr(last_transition, "created_at", None) if last_transition else None
        ),
        "capacity": capacity.as_dict(),
        "forecast": {
            "authority": capacity.authority,
            "active_units": resolved_units,
            "pending_reservation_units": pending_units,
            "projected_units_if_pending_convert": projected_units,
            "projected_ratio_if_pending_convert": round(projected_ratio, 6),
            "available_units_now": max(0, capacity.limit_units - resolved_units),
            "pause_threshold_units": pause_threshold_units,
            "resume_below_units": max(0, resume_below_units),
            "gate_reasons": gate_reasons,
        },
        "reservation_counts": dict(reservations["reservation_counts"]),
        "campaign_lifecycle_counts": dict(sorted(lifecycle_counts.items())),
        "campaigns": campaign_readback,
    }


def _transition_for_campaign(
    row: IncentiveCampaign,
    *,
    active_units: int,
    contract: Mapping[str, Any],
    now: datetime,
) -> tuple[str | None, str, dict[str, Any]]:
    capacity = capacity_snapshot(active_units=active_units, contract=contract)
    objective = str(row.objective or "").strip().lower()
    lifecycle = str(row.lifecycle_status or "").strip().lower()
    state_reason = str(row.state_reason or "").strip().lower()

    if objective not in AUTO_MANAGED_OBJECTIVES or not bool(row.capacity_guard_enabled):
        return None, state_reason or "legacy_unclassified", {}
    if lifecycle == "live" and not capacity.acquisition_permitted:
        return "pause", "capacity_forbidden", {
            "activation_allowed": False,
            "blocking_reasons": ["capacity_forbidden"],
        }
    if lifecycle != "paused" or state_reason not in CAPACITY_PAUSE_REASONS:
        return None, state_reason or "legacy_unclassified", {}

    if capacity.ratio is None or capacity.ratio >= capacity.pause_at_ratio:
        action = "hold" if state_reason != "capacity_forbidden" else None
        return action, "capacity_forbidden", {
            "activation_allowed": False,
            "blocking_reasons": ["capacity_forbidden"],
        }
    if capacity.ratio >= capacity.resume_below_ratio:
        return "hold" if state_reason != "capacity_resume_hysteresis" else None, "capacity_resume_hysteresis", {
            "activation_allowed": False,
            "blocking_reasons": ["capacity_resume_hysteresis"],
        }

    candidate = campaign_record(row)
    candidate["lifecycle_status"] = "live"
    candidate["state_reason"] = "ready"
    decision = evaluate_campaign_policy(
        candidate,
        active_units=active_units,
        contract=contract,
        now=now,
        resuming_from_capacity_pause=True,
    )
    if bool(decision.get("activation_allowed")):
        return "resume", "ready", decision
    action = "hold" if state_reason != "capacity_resume_hysteresis" else None
    return action, "capacity_resume_hysteresis", decision


def run_commercial_capacity_evaluation(
    session,
    *,
    now: datetime | None = None,
    contract: Mapping[str, Any] | None = None,
    active_units: int | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or transactionally apply owner-policy pause/hold/resume transitions."""

    current = _as_utc(now or datetime.now(timezone.utc))
    current_db = _db_time(current)
    commercial = dict(contract or get_commercial_contract())
    resolved_units = (
        active_entitlement_capacity_units(session, now=current)
        if active_units is None
        else max(0, int(active_units))
    )
    capacity = capacity_snapshot(active_units=resolved_units, contract=commercial)
    query = session.query(IncentiveCampaign).filter(
        IncentiveCampaign.objective.in_(sorted(AUTO_MANAGED_OBJECTIVES)),
        IncentiveCampaign.lifecycle_status.in_(["live", "paused"]),
    )
    if apply:
        query = query.with_for_update()
    rows = query.order_by(IncentiveCampaign.id.asc()).all()
    transitions: list[dict[str, Any]] = []

    for row in rows:
        action, next_reason, decision = _transition_for_campaign(
            row,
            active_units=resolved_units,
            contract=commercial,
            now=current,
        )
        before = {
            "revision": max(1, int(row.revision or 1)),
            "lifecycle_status": str(row.lifecycle_status or ""),
            "state_reason": str(row.state_reason or ""),
            "capacity_band": str(row.capacity_band or "unknown"),
        }
        after = dict(before)
        if action == "pause":
            after.update(
                {
                    "revision": before["revision"] + 1,
                    "lifecycle_status": "paused",
                    "state_reason": "capacity_forbidden",
                    "capacity_band": capacity.band,
                }
            )
        elif action == "hold":
            after.update(
                {
                    "revision": before["revision"] + 1,
                    "lifecycle_status": "paused",
                    "state_reason": next_reason,
                    "capacity_band": capacity.band,
                }
            )
        elif action == "resume":
            after.update(
                {
                    "revision": before["revision"] + 1,
                    "lifecycle_status": "live",
                    "state_reason": "ready",
                    "capacity_band": capacity.band,
                }
            )

        if action:
            transition = {
                "campaign_id": int(row.id),
                "public_id": str(row.public_id or "") or None,
                "action": action,
                "before": before,
                "after": after,
                "blocking_reasons": list(decision.get("blocking_reasons") or []),
            }
            transitions.append(transition)
            if apply:
                row.revision = int(after["revision"])
                row.lifecycle_status = str(after["lifecycle_status"])
                row.state_reason = str(after["state_reason"])
                row.capacity_band = str(after["capacity_band"])
                row.is_active = action == "resume"
                row.updated_at = current_db
                audit_meta = json.dumps(
                    {
                        "schema": COMMERCIAL_CAPACITY_AUTOMATION_SCHEMA,
                        "policy_id": COMMERCIAL_CAPACITY_POLICY_ID,
                        "commercial_revision": str(
                            commercial.get("commercial_revision") or ""
                        ),
                        "campaign_public_id": str(row.public_id or ""),
                        "active_units": resolved_units,
                        "limit_units": capacity.limit_units,
                        "band": capacity.band,
                        "before": before,
                        "after": after,
                    },
                    ensure_ascii=True,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                if len(audit_meta) > 2000:
                    raise RuntimeError("commercial_capacity_audit_oversize")
                session.add(
                    AdminAudit(
                        actor_tg_id=0,
                        action=f"capacity.auto_{action}",
                        target_tg_id=None,
                        meta=audit_meta,
                        created_at=current_db,
                    )
                )
        if apply:
            row.capacity_band = capacity.band
            row.last_policy_evaluated_at = current_db
            if not action and next_reason in CAPACITY_PAUSE_REASONS:
                row.state_reason = next_reason

    if apply:
        session.flush()
    return {
        "schema": COMMERCIAL_CAPACITY_AUTOMATION_SCHEMA,
        "policy_id": COMMERCIAL_CAPACITY_POLICY_ID,
        "mode": "apply" if apply else "dry_run",
        "applied": bool(apply),
        "commercial_revision": str(commercial.get("commercial_revision") or ""),
        "contract_sha256": str(commercial.get("contract_sha256") or ""),
        "evaluated_at": current.isoformat(),
        "capacity": capacity.as_dict(),
        "transition_count": len(transitions),
        "transitions": transitions,
        "renewal_recovery_exempt": True,
    }

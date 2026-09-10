from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from sqlalchemy import func, or_

from commercial_contract import get_commercial_contract
from commercial_pilot_service import evaluate_campaign_pilot_binding
from models import EntitlementGrant


CAMPAIGN_PUBLIC_ID_RE = re.compile(r"^cmp_[0-9a-f]{32}$")
CAMPAIGN_OBJECTIVES = frozenset(
    {"acquisition", "winback", "retention", "renewal", "recovery"}
)
CAMPAIGN_LIFECYCLE_STATUSES = frozenset(
    {"draft", "review", "approved", "live", "paused", "ended", "killed"}
)
CAMPAIGN_LEGAL_PROFILE_STATUSES = frozenset(
    {"missing", "pending_owner_review", "owner_approved", "rejected"}
)
CAMPAIGN_CHANNELS = frozenset(
    {
        "owned_telegram",
        "owned_app",
        "owned_cabinet",
        "owned_web",
        "consented_email",
        "transactional_email",
        "partner",
        "rf_advertising",
    }
)
CAMPAIGN_STATE_REASONS = frozenset(
    {
        "draft",
        "pending_review",
        "approved_not_live",
        "ready",
        "owner_paused",
        "budget_paused",
        "capacity_forbidden",
        "capacity_resume_hysteresis",
        "legal_paused",
        "terms_changed",
        "seller_unavailable",
        "channel_blocked",
        "ended",
        "owner_killed",
        "legacy_unclassified",
    }
)
CAMPAIGN_POLICY_REASONS = frozenset(
    {
        "ready",
        "campaign_id_missing",
        "objective_invalid",
        "lifecycle_invalid",
        "lifecycle_not_live",
        "campaign_revision_invalid",
        "commercial_revision_mismatch",
        "legal_profile_missing",
        "legal_profile_not_approved",
        "legal_launch_blocked",
        "seller_binding_missing",
        "seller_unpublished",
        "terms_binding_missing",
        "terms_revision_mismatch",
        "offer_not_approved",
        "channel_missing",
        "channel_invalid",
        "channel_not_allowed",
        "rf_advertising_not_approved",
        "paid_cap_missing",
        "paid_cap_reached",
        "capacity_guard_required",
        "capacity_projection_unavailable",
        "capacity_forbidden",
        "capacity_resume_hysteresis",
        "not_started",
        "ended",
        "killed",
        "pilot_binding_missing",
        "pilot_binding_stale",
        "pilot_owner_approval_missing",
        "pilot_holdout_decision_missing",
        "pilot_window_invalid",
    }
)
CAPACITY_BANDS = frozenset({"green", "yellow", "orange", "red", "hold", "unknown"})
CAPACITY_EXEMPT_OBJECTIVES = frozenset({"renewal", "recovery"})


@dataclass(frozen=True)
class CapacitySnapshot:
    authority: str
    active_units: int | None
    limit_units: int
    ratio: float | None
    band: str
    acquisition_permitted: bool
    pause_at_ratio: float
    resume_below_ratio: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "authority": self.authority,
            "active_units": self.active_units,
            "limit_units": self.limit_units,
            "ratio": self.ratio,
            "band": self.band,
            "acquisition_permitted": self.acquisition_permitted,
            "pause_at_ratio": self.pause_at_ratio,
            "resume_below_ratio": self.resume_below_ratio,
        }


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def normalize_campaign_channels(value: object) -> list[str]:
    if value is None:
        return []
    raw: Sequence[object]
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except ValueError:
            decoded = []
        raw = decoded if isinstance(decoded, list) else []
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        raw = value
    else:
        raw = []
    return sorted(
        {
            str(item or "").strip().lower()
            for item in raw
            if str(item or "").strip()
        }
    )


def active_entitlement_capacity_units(session, *, now: datetime | None = None) -> int:
    current = _as_utc(now or datetime.now(timezone.utc)).replace(tzinfo=None)
    value = (
        session.query(func.count(func.distinct(EntitlementGrant.account_id)))
        .filter(
            EntitlementGrant.account_id.isnot(None),
            EntitlementGrant.account_id != "",
            EntitlementGrant.status.in_(["active", "grace"]),
            EntitlementGrant.reversed_at.is_(None),
            or_(EntitlementGrant.starts_at.is_(None), EntitlementGrant.starts_at <= current),
            or_(EntitlementGrant.expires_at.is_(None), EntitlementGrant.expires_at > current),
        )
        .scalar()
    )
    return max(0, int(value or 0))


def capacity_snapshot(
    *,
    active_units: int | None,
    contract: Mapping[str, Any] | None = None,
) -> CapacitySnapshot:
    commercial = dict(contract or get_commercial_contract())
    policy = dict(commercial.get("capacity_policy") or {})
    limit = max(1, int(policy.get("limit_units") or 300))
    pause_at = float(policy.get("pause_at_ratio") or 0.7)
    resume_below = float(policy.get("resume_below_ratio") or 0.65)
    authority = str(policy.get("unit_authority") or "active_entitlement_projection")
    if active_units is None:
        return CapacitySnapshot(
            authority=authority,
            active_units=None,
            limit_units=limit,
            ratio=None,
            band="unknown",
            acquisition_permitted=False,
            pause_at_ratio=pause_at,
            resume_below_ratio=resume_below,
        )
    units = max(0, int(active_units))
    ratio = units / limit
    band = "hold"
    for raw in list(policy.get("bands") or []):
        if not isinstance(raw, Mapping):
            continue
        minimum = float(raw.get("minimum_ratio") or 0.0)
        maximum_raw = raw.get("maximum_ratio")
        maximum = float(maximum_raw) if maximum_raw is not None else None
        if ratio >= minimum and (maximum is None or ratio <= maximum):
            candidate = str(raw.get("code") or "unknown").strip().lower()
            band = candidate if candidate in CAPACITY_BANDS else "unknown"
            break
    allowed = {
        str(item or "").strip().lower()
        for item in list(policy.get("acquisition_allowed_bands") or [])
    }
    return CapacitySnapshot(
        authority=authority,
        active_units=units,
        limit_units=limit,
        ratio=round(ratio, 6),
        band=band,
        acquisition_permitted=band in allowed and ratio < pause_at,
        pause_at_ratio=pause_at,
        resume_below_ratio=resume_below,
    )


def campaign_record(row: object | Mapping[str, Any]) -> dict[str, Any]:
    def read(key: str, default: Any = None) -> Any:
        if isinstance(row, Mapping):
            return row.get(key, default)
        return getattr(row, key, default)

    def read_datetime(key: str) -> datetime | None:
        value = read(key)
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and value.strip():
            try:
                return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    return {
        "public_id": str(read("public_id") or "").strip().lower(),
        "objective": str(read("objective") or "").strip().lower(),
        "lifecycle_status": str(read("lifecycle_status") or "").strip().lower(),
        "revision": int(read("revision") or 0),
        "commercial_revision": str(read("commercial_revision") or "").strip(),
        "legal_profile_status": str(read("legal_profile_status") or "").strip().lower(),
        "channels": normalize_campaign_channels(
            read("channels", read("channels_json"))
        ),
        "seller_profile_id": str(read("seller_profile_id") or "").strip(),
        "terms_revision": str(read("terms_revision") or "").strip(),
        "paid_cap": int(read("paid_cap") or 0),
        "paid_conversions_count": int(read("paid_conversions_count") or 0),
        "capacity_guard_enabled": bool(read("capacity_guard_enabled", True)),
        "capacity_band": str(read("capacity_band") or "unknown").strip().lower(),
        "state_reason": str(read("state_reason") or "legacy_unclassified").strip().lower(),
        "starts_at": read_datetime("starts_at"),
        "ends_at": read_datetime("ends_at"),
    }


def _time_gate_reasons(record: Mapping[str, Any], *, now: datetime) -> list[str]:
    reasons: list[str] = []
    starts_at = record.get("starts_at")
    ends_at = record.get("ends_at")
    if isinstance(starts_at, datetime) and _as_utc(starts_at) > now:
        reasons.append("not_started")
    if isinstance(ends_at, datetime) and _as_utc(ends_at) <= now:
        reasons.append("ended")
    return reasons


def evaluate_campaign_policy(
    row: object | Mapping[str, Any],
    *,
    active_units: int | None,
    quality: Mapping[str, Any] | None = None,
    contract: Mapping[str, Any] | None = None,
    now: datetime | None = None,
    resuming_from_capacity_pause: bool = False,
) -> dict[str, Any]:
    commercial = dict(contract or get_commercial_contract())
    legal = dict(commercial.get("legal") or {})
    record = campaign_record(row)
    capacity = capacity_snapshot(active_units=active_units, contract=commercial)
    current = _as_utc(now or datetime.now(timezone.utc))
    reasons: list[str] = []

    public_id = str(record["public_id"])
    objective = str(record["objective"])
    lifecycle = str(record["lifecycle_status"])
    legal_profile = str(record["legal_profile_status"])
    channels = list(record["channels"])

    if not CAMPAIGN_PUBLIC_ID_RE.fullmatch(public_id):
        reasons.append("campaign_id_missing")
    if objective not in CAMPAIGN_OBJECTIVES:
        reasons.append("objective_invalid")
    if lifecycle not in CAMPAIGN_LIFECYCLE_STATUSES:
        reasons.append("lifecycle_invalid")
    if int(record["revision"]) < 1:
        reasons.append("campaign_revision_invalid")
    if str(record["commercial_revision"]) != str(commercial.get("commercial_revision") or ""):
        reasons.append("commercial_revision_mismatch")
    if legal_profile == "missing":
        reasons.append("legal_profile_missing")
    elif legal_profile != "owner_approved":
        reasons.append("legal_profile_not_approved")
    if legal.get("launch_ready") is not True:
        reasons.append("legal_launch_blocked")
    if not str(record["seller_profile_id"]):
        reasons.append("seller_binding_missing")
    if str(legal.get("seller_publication_status") or "") != "published":
        reasons.append("seller_unpublished")
    if not str(record["terms_revision"]):
        reasons.append("terms_binding_missing")
    elif str(record["terms_revision"]) != str(commercial.get("terms_revision") or ""):
        reasons.append("terms_revision_mismatch")
    if str(legal.get("offer_review_status") or "") != "approved":
        reasons.append("offer_not_approved")
    if not channels:
        reasons.append("channel_missing")
    invalid_channels = sorted(set(channels) - CAMPAIGN_CHANNELS)
    if invalid_channels:
        reasons.append("channel_invalid")
    allowed_channels = {
        str(item or "").strip().lower()
        for item in list(legal.get("allowed_launch_channels") or [])
    }
    if channels and not set(channels).issubset(allowed_channels):
        reasons.append("channel_not_allowed")
    if (
        "rf_advertising" in channels
        and str(legal.get("rf_advertising_status") or "") != "owner_approved"
    ):
        reasons.append("rf_advertising_not_approved")
    if int(record["paid_cap"]) <= 0:
        reasons.append("paid_cap_missing")
    elif int(record["paid_conversions_count"]) >= int(record["paid_cap"]):
        reasons.append("paid_cap_reached")

    if objective not in CAPACITY_EXEMPT_OBJECTIVES:
        if not bool(record["capacity_guard_enabled"]):
            reasons.append("capacity_guard_required")
        if capacity.active_units is None:
            reasons.append("capacity_projection_unavailable")
        elif not capacity.acquisition_permitted:
            reasons.append("capacity_forbidden")
        elif resuming_from_capacity_pause and (
            capacity.ratio is None or capacity.ratio >= capacity.resume_below_ratio
        ):
            reasons.append("capacity_resume_hysteresis")
        if not quality or not quality["acquisition_permitted"]:
            reasons.append("capacity_forbidden")
        elif resuming_from_capacity_pause and not quality["resume_permitted"]:
            reasons.append("capacity_resume_hysteresis")

    reasons.extend(_time_gate_reasons(record, now=current))
    reasons.extend(evaluate_campaign_pilot_binding(row))
    if lifecycle == "killed":
        reasons.insert(0, "killed")
    elif lifecycle in CAMPAIGN_LIFECYCLE_STATUSES and lifecycle != "live":
        reasons.append("lifecycle_not_live")
    unique_reasons = list(dict.fromkeys(reasons))
    activation_allowed = not unique_reasons
    effective_status = (
        "live"
        if lifecycle == "live" and activation_allowed
        else "blocked"
        if lifecycle == "live"
        else lifecycle if lifecycle in CAMPAIGN_LIFECYCLE_STATUSES else "blocked"
    )
    reason_code = "ready" if activation_allowed else unique_reasons[0]
    assert reason_code in CAMPAIGN_POLICY_REASONS
    return {
        "activation_allowed": activation_allowed,
        "effective_status": effective_status,
        "reason_code": reason_code,
        "blocking_reasons": unique_reasons,
        "commercial_revision": str(commercial.get("commercial_revision") or ""),
        "contract_sha256": str(commercial.get("contract_sha256") or ""),
        "capacity_exempt": objective in CAPACITY_EXEMPT_OBJECTIVES,
        "capacity": capacity.as_dict(),
        "quality_blocking_reasons": list(quality["blocking_reasons"])
        if quality else ["node_quality_unavailable"],
        "evaluated_at": current.isoformat(),
    }


def campaign_policy_authority_snapshot(
    *,
    active_units: int | None,
    quality: Mapping[str, Any],
    contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    commercial = dict(contract or get_commercial_contract())
    legal = dict(commercial.get("legal") or {})
    return {
        "commercial_revision": str(commercial.get("commercial_revision") or ""),
        "contract_sha256": str(commercial.get("contract_sha256") or ""),
        "terms_revision": str(commercial.get("terms_revision") or ""),
        "seller_publication_status": str(legal.get("seller_publication_status") or ""),
        "offer_review_status": str(legal.get("offer_review_status") or ""),
        "rf_advertising_status": str(legal.get("rf_advertising_status") or ""),
        "allowed_launch_channels": sorted(
            str(item or "").strip().lower()
            for item in list(legal.get("allowed_launch_channels") or [])
        ),
        "capacity": capacity_snapshot(
            active_units=active_units,
            contract=commercial,
        ).as_dict(),
        "quality_gate": {
            key: quality[key] for key in (
                "acquisition_permitted", "resume_permitted", "blocking_reasons",
            )
        },
    }


def _safe_iso(value: object) -> str | None:
    if not isinstance(value, datetime):
        return None
    return _as_utc(value).isoformat()


def _json_object(value: object) -> dict[str, Any]:
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        decoded = json.loads(value)
    except ValueError:
        return {}
    return dict(decoded) if isinstance(decoded, dict) else {}


def campaign_admin_readback(
    row: object,
    *,
    active_units: int,
    quality: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "id": int(getattr(row, "id")),
        "public_id": str(getattr(row, "public_id", "") or "") or None,
        "name": str(getattr(row, "name", "") or ""),
        "campaign_type": str(getattr(row, "campaign_type", "") or ""),
        "target_value": str(getattr(row, "target_value", "") or ""),
        "objective": str(getattr(row, "objective", "") or ""),
        "lifecycle_status": str(getattr(row, "lifecycle_status", "") or ""),
        "revision": int(getattr(row, "revision", 0) or 0),
        "commercial_revision": str(getattr(row, "commercial_revision", "") or "") or None,
        "legal_profile_status": str(getattr(row, "legal_profile_status", "") or ""),
        "channels": normalize_campaign_channels(getattr(row, "channels_json", None)),
        "seller_profile_id": str(getattr(row, "seller_profile_id", "") or "") or None,
        "terms_revision": str(getattr(row, "terms_revision", "") or "") or None,
        "paid_cap": int(getattr(row, "paid_cap", 0) or 0),
        "paid_conversions_count": int(getattr(row, "paid_conversions_count", 0) or 0),
        "capacity_guard_enabled": bool(getattr(row, "capacity_guard_enabled", True)),
        "capacity_band": str(getattr(row, "capacity_band", "unknown") or "unknown"),
        "state_reason": str(
            getattr(row, "state_reason", "legacy_unclassified") or "legacy_unclassified"
        ),
        "policy": evaluate_campaign_policy(row, active_units=active_units, quality=quality),
        "segment": str(getattr(row, "segment", "") or ""),
        "starts_at": _safe_iso(getattr(row, "starts_at", None)),
        "ends_at": _safe_iso(getattr(row, "ends_at", None)),
        "max_activations": int(getattr(row, "max_activations", -1) or -1),
        "activations_count": int(getattr(row, "activations_count", 0) or 0),
        "auto_disable": bool(getattr(row, "auto_disable", False)),
        "is_active": bool(getattr(row, "is_active", False)),
        "created_by": (
            int(getattr(row, "created_by"))
            if getattr(row, "created_by", None) is not None
            else None
        ),
        "metadata": _json_object(getattr(row, "metadata_json", None)),
        "last_policy_evaluated_at": _safe_iso(
            getattr(row, "last_policy_evaluated_at", None)
        ),
        "killed_at": _safe_iso(getattr(row, "killed_at", None)),
        "created_at": _safe_iso(getattr(row, "created_at", None)),
        "updated_at": _safe_iso(getattr(row, "updated_at", None)),
    }

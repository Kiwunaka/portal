from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from marketing_pilot_contract import get_winback_pilot_contract


SUBJECT_HMAC_RE = re.compile(r"^[a-f0-9]{64}$")
PILOT_AUDIENCE_REASONS = frozenset(
    {
        "ready",
        "paid_history_missing",
        "current_access_active",
        "access_expiry_missing",
        "expired_window_mismatch",
        "refund_dispute_open",
        "unresolved_payment",
        "unresolved_support",
        "payment_already_consumed",
        "owner_suppressed",
        "channel_not_in_pilot",
        "channel_consent_missing",
    }
)
PILOT_RUNTIME_REASONS = frozenset(
    {
        "ready",
        "audience_blocked",
        "pilot_binding_missing",
        "pilot_binding_stale",
        "pilot_owner_approval_missing",
        "pilot_holdout_decision_missing",
        "legal_or_channel_blocked",
        "campaign_not_live",
        "pilot_window_invalid",
        "pilot_not_started",
        "pilot_ended",
        "capacity_blocked",
        "paid_cap_reached",
        "creative_count_invalid",
        "subject_invalid",
        "holdout_assignment",
    }
)
CONSENT_CHANNELS = frozenset({"consented_email", "owned_telegram"})


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class WinbackAudienceFacts:
    paid_before: bool
    access_expired_at: datetime | None
    current_access_active: bool = False
    refund_dispute_open: bool = False
    unresolved_payment: bool = False
    unresolved_support: bool = False
    payment_already_consumed: bool = False
    owner_suppressed: bool = False
    consented_channels: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class WinbackRuntimeContext:
    pilot_revision: str
    pilot_contract_sha256: str
    marketing_governance_revision: str
    marketing_governance_sha256: str
    commercial_revision: str
    commercial_contract_sha256: str
    pilot_launch_state: str
    approval_record_id: str
    legal_profile_state: str
    channel_launch_state: str
    campaign_state: str
    campaign_starts_at: datetime | None
    campaign_ends_at: datetime | None
    capacity_band: str
    capacity_ratio: float | None
    paid_conversions_count: int
    creative_count: int
    holdout_percent: int | None


def evaluate_winback_audience(
    facts: WinbackAudienceFacts,
    *,
    channel: str,
    now: datetime | None = None,
    contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    pilot = dict(contract or get_winback_pilot_contract())
    current = _as_utc(now or datetime.now(timezone.utc))
    normalized_channel = str(channel or "").strip().lower()
    reasons: list[str] = []
    if not facts.paid_before:
        reasons.append("paid_history_missing")
    if facts.current_access_active:
        reasons.append("current_access_active")
    if facts.access_expired_at is None:
        reasons.append("access_expiry_missing")
        expired_days = None
    else:
        delta = current - _as_utc(facts.access_expired_at)
        expired_days = delta.total_seconds() / 86400
        audience = dict(pilot.get("audience") or {})
        minimum = int(audience.get("expired_min_days") or 7)
        maximum = int(audience.get("expired_max_days") or 30)
        if expired_days < minimum or expired_days > maximum:
            reasons.append("expired_window_mismatch")
    for blocked, reason in (
        (facts.refund_dispute_open, "refund_dispute_open"),
        (facts.unresolved_payment, "unresolved_payment"),
        (facts.unresolved_support, "unresolved_support"),
        (facts.payment_already_consumed, "payment_already_consumed"),
        (facts.owner_suppressed, "owner_suppressed"),
    ):
        if blocked:
            reasons.append(reason)
    if normalized_channel not in set(pilot.get("channels") or []):
        reasons.append("channel_not_in_pilot")
    if (
        normalized_channel in CONSENT_CHANNELS
        and normalized_channel not in {item.strip().lower() for item in facts.consented_channels}
    ):
        reasons.append("channel_consent_missing")
    reasons = sorted(set(reasons))
    return {
        "eligible": not reasons,
        "reason_code": reasons[0] if reasons else "ready",
        "blocking_reasons": reasons,
        "channel": normalized_channel,
        "expired_days": None if expired_days is None else round(expired_days, 6),
        "pilot_id": str(pilot.get("pilot_id") or ""),
        "pilot_revision": str(pilot.get("revision") or ""),
    }


def sticky_holdout_allocation(
    *,
    subject_hmac: str,
    pilot_id: str,
    holdout_percent: int,
) -> dict[str, Any]:
    normalized_subject = str(subject_hmac or "").strip().lower()
    normalized_pilot = str(pilot_id or "").strip().lower()
    if SUBJECT_HMAC_RE.fullmatch(normalized_subject) is None or not normalized_pilot:
        raise ValueError("subject_invalid")
    if type(holdout_percent) is not int or not 1 <= holdout_percent <= 99:
        raise ValueError("holdout_percent_invalid")
    digest = hashlib.sha256(f"{normalized_pilot}:{normalized_subject}".encode("ascii")).digest()
    bucket = int.from_bytes(digest[:8], "big") % 10000
    threshold = holdout_percent * 100
    cohort = "holdout" if bucket < threshold else "exposed"
    return {
        "cohort": cohort,
        "bucket": bucket,
        "threshold": threshold,
        "algorithm": "hmac_sha256_mod_10000",
    }


def evaluate_winback_runtime(
    *,
    audience: Mapping[str, Any],
    subject_hmac: str,
    context: WinbackRuntimeContext,
    now: datetime | None = None,
    contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    pilot = dict(contract or get_winback_pilot_contract())
    current = _as_utc(now or datetime.now(timezone.utc))
    reasons: list[str] = []
    if audience.get("eligible") is not True:
        reasons.append("audience_blocked")
    expected_bindings = {
        "pilot_revision": str(pilot.get("revision") or ""),
        "pilot_contract_sha256": str(pilot.get("contract_sha256") or ""),
        "marketing_governance_revision": str(pilot.get("marketing_governance_revision") or ""),
        "marketing_governance_sha256": str(pilot.get("marketing_governance_sha256") or ""),
        "commercial_revision": str(pilot.get("commercial_revision") or ""),
        "commercial_contract_sha256": str(pilot.get("commercial_contract_sha256") or ""),
    }
    observed_bindings = {
        key: str(getattr(context, key) or "") for key in expected_bindings
    }
    if not all(observed_bindings.values()):
        reasons.append("pilot_binding_missing")
    elif observed_bindings != expected_bindings:
        reasons.append("pilot_binding_stale")
    if (
        context.pilot_launch_state != "owner_approved_ready"
        or not str(context.approval_record_id or "").strip()
    ):
        reasons.append("pilot_owner_approval_missing")
    if context.holdout_percent is None or not 1 <= int(context.holdout_percent) <= 99:
        reasons.append("pilot_holdout_decision_missing")
    if (
        context.legal_profile_state != "owner_approved"
        or context.channel_launch_state != "owner_approved"
    ):
        reasons.append("legal_or_channel_blocked")
    if context.campaign_state != "live":
        reasons.append("campaign_not_live")
    starts = context.campaign_starts_at
    ends = context.campaign_ends_at
    if starts is None or ends is None:
        reasons.append("pilot_window_invalid")
    else:
        starts_utc = _as_utc(starts)
        ends_utc = _as_utc(ends)
        expected_duration = timedelta(hours=int((pilot.get("offer") or {}).get("duration_hours") or 72))
        if ends_utc - starts_utc != expected_duration:
            reasons.append("pilot_window_invalid")
        if current < starts_utc:
            reasons.append("pilot_not_started")
        if current >= ends_utc:
            reasons.append("pilot_ended")
    capacity = dict(pilot.get("capacity") or {})
    allowed_bands = set(capacity.get("allowed_bands") or [])
    pause_at = float(capacity.get("pause_at_ratio") or 0.7)
    if (
        context.capacity_band not in allowed_bands
        or context.capacity_ratio is None
        or float(context.capacity_ratio) >= pause_at
    ):
        reasons.append("capacity_blocked")
    paid_cap = int((pilot.get("offer") or {}).get("paid_cap") or 20)
    if int(context.paid_conversions_count) >= paid_cap:
        reasons.append("paid_cap_reached")
    if not 1 <= int(context.creative_count) <= len(list(pilot.get("creatives") or [])):
        reasons.append("creative_count_invalid")
    allocation: dict[str, Any] | None = None
    if SUBJECT_HMAC_RE.fullmatch(str(subject_hmac or "").strip().lower()) is None:
        reasons.append("subject_invalid")
    elif context.holdout_percent is not None and 1 <= int(context.holdout_percent) <= 99:
        allocation = sticky_holdout_allocation(
            subject_hmac=subject_hmac,
            pilot_id=str(pilot.get("pilot_id") or ""),
            holdout_percent=int(context.holdout_percent),
        )
        if allocation["cohort"] == "holdout":
            reasons.append("holdout_assignment")
    reasons = sorted(set(reasons))
    non_holdout_reasons = [reason for reason in reasons if reason != "holdout_assignment"]
    exposure_allowed = not reasons
    return {
        "eligible": not non_holdout_reasons,
        "exposure_allowed": exposure_allowed,
        "cohort": (allocation or {}).get("cohort", "blocked"),
        "allocation": allocation,
        "reason_code": reasons[0] if reasons else "ready",
        "blocking_reasons": reasons,
        "pilot_id": str(pilot.get("pilot_id") or ""),
        "pilot_revision": str(pilot.get("revision") or ""),
        "pilot_contract_sha256": str(pilot.get("contract_sha256") or ""),
    }


def campaign_pilot_metadata(value: object) -> dict[str, Any]:
    raw: object = value
    if isinstance(value, str):
        try:
            raw = json.loads(value)
        except ValueError:
            raw = {}
    if not isinstance(raw, Mapping):
        return {}
    pilot = raw.get("marketing_pilot")
    if not isinstance(pilot, Mapping):
        return {}
    allowed = {
        "pilot_revision",
        "pilot_contract_sha256",
        "marketing_governance_revision",
        "marketing_governance_sha256",
        "commercial_revision",
        "commercial_contract_sha256",
        "pilot_launch_state",
        "approval_record_id",
        "holdout_percent",
    }
    if set(pilot) - allowed:
        return {}
    return {key: pilot.get(key) for key in allowed if key in pilot}


def evaluate_campaign_pilot_binding(
    row: object | Mapping[str, Any],
    *,
    contract: Mapping[str, Any] | None = None,
) -> list[str]:
    pilot = dict(contract or get_winback_pilot_contract())

    def read(key: str, default: Any = None) -> Any:
        if isinstance(row, Mapping):
            return row.get(key, default)
        return getattr(row, key, default)

    if str(read("objective") or "").strip().lower() != "winback":
        return []
    metadata_value = read("metadata_json")
    if isinstance(row, Mapping) and "metadata" in row:
        metadata_value = row.get("metadata")
    metadata = campaign_pilot_metadata(metadata_value)
    if not metadata:
        return ["pilot_binding_missing"]
    expected = {
        "pilot_revision": str(pilot.get("revision") or ""),
        "pilot_contract_sha256": str(pilot.get("contract_sha256") or ""),
        "marketing_governance_revision": str(pilot.get("marketing_governance_revision") or ""),
        "marketing_governance_sha256": str(pilot.get("marketing_governance_sha256") or ""),
        "commercial_revision": str(pilot.get("commercial_revision") or ""),
        "commercial_contract_sha256": str(pilot.get("commercial_contract_sha256") or ""),
    }
    if any(str(metadata.get(key) or "") != value for key, value in expected.items()):
        return ["pilot_binding_stale"]
    reasons: list[str] = []
    if (
        str(metadata.get("pilot_launch_state") or "") != "owner_approved_ready"
        or not str(metadata.get("approval_record_id") or "").strip()
    ):
        reasons.append("pilot_owner_approval_missing")
    holdout = metadata.get("holdout_percent")
    if type(holdout) is not int or not 1 <= int(holdout) <= 99:
        reasons.append("pilot_holdout_decision_missing")
    if int(read("paid_cap") or 0) != int((pilot.get("offer") or {}).get("paid_cap") or 20):
        reasons.append("pilot_binding_stale")
    raw_channels = read("channels", read("channels_json"))
    if isinstance(raw_channels, str):
        try:
            raw_channels = json.loads(raw_channels)
        except ValueError:
            raw_channels = []
    campaign_channels = {
        str(item or "").strip().lower()
        for item in list(raw_channels or [])
        if str(item or "").strip()
    }
    if not campaign_channels or campaign_channels - set(pilot.get("channels") or []):
        reasons.append("pilot_binding_stale")
    starts = read("starts_at")
    ends = read("ends_at")
    if isinstance(starts, str):
        try:
            starts = datetime.fromisoformat(starts.replace("Z", "+00:00"))
        except ValueError:
            starts = None
    if isinstance(ends, str):
        try:
            ends = datetime.fromisoformat(ends.replace("Z", "+00:00"))
        except ValueError:
            ends = None
    if (
        not isinstance(starts, datetime)
        or not isinstance(ends, datetime)
        or _as_utc(ends) - _as_utc(starts)
        != timedelta(hours=int((pilot.get("offer") or {}).get("duration_hours") or 72))
    ):
        reasons.append("pilot_window_invalid")
    return sorted(set(reasons))

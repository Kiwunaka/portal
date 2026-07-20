from __future__ import annotations

import json
import logging
import re
import secrets
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from economy_service import (
    grant_internal_bonus_days,
    rebuild_account_entitlement_projection,
    resolve_canonical_account_id,
)
from models import (
    Account,
    AccountMergeReview,
    EntitlementGrant,
    NodeProvisioningJob,
    RewardAccountState,
    RewardClaim,
    User,
)
from node_provisioning_service import enqueue_reward_entitlement_sync


PAID_WEEKLY_V1: dict[str, object] = {
    "preset": "paid_weekly_v1",
    "cooldown_hours": 168,
    "weights": [
        {"days": 1, "weight": 9000},
        {"days": 3, "weight": 890},
        {"days": 7, "weight": 100},
        {"days": 30, "weight": 10},
    ],
}
PAID_GRANT_SOURCES = frozenset({"provider_payment", "compatibility_projection"})
WHEEL_SECTORS = (1, 3, 7, 30)
CALENDAR_MILESTONES = frozenset({7, 14, 21, 28})
_TERMINAL_MERGE_REVIEW_STATUSES = frozenset({"closed", "dismissed", "resolved"})
_SAFE_PRESET_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_LOGGER = logging.getLogger(__name__)


class RewardDomainError(RuntimeError):
    def __init__(self, code: str):
        self.code = str(code)
        super().__init__(self.code)


class InvalidWheelConfig(RewardDomainError):
    pass


class RewardForbidden(RewardDomainError):
    pass


class RewardDisabled(RewardDomainError):
    def __init__(self, feature: str):
        self.feature = str(feature)
        super().__init__("bonus_feature_disabled")


class RewardConflict(RewardDomainError):
    def __init__(
        self,
        code: str,
        *,
        next_allowed_at: datetime,
        last_reward_days: int | None,
    ) -> None:
        self.next_allowed_at = next_allowed_at
        self.last_reward_days = last_reward_days
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class WheelConfig:
    preset: str
    cooldown_hours: int
    outcomes: Sequence[tuple[int, int]]


@dataclass(frozen=True, slots=True)
class PaidEligibility:
    eligible: bool
    reason: str
    account_id: str
    legacy_tg_id: int | None


@dataclass(frozen=True, slots=True)
class WheelState:
    enabled: bool
    eligible: bool
    reason: str
    can_spin: bool
    sectors: Sequence[int]
    cooldown_hours: int
    last_spin_at: datetime | None
    next_spin_at: datetime | None
    last_reward_days: int | None
    sync_state: str


@dataclass(frozen=True, slots=True)
class CalendarState:
    enabled: bool
    eligible: bool
    reason: str
    checked_in_today: bool
    cycle_started_on: date | None
    cycle_day: int
    next_milestone: int | None
    achievements: Mapping[str, bool]
    sync_state: str


@dataclass(frozen=True, slots=True)
class RewardMutation:
    feature: str
    account_id: str
    grant_id: str | None
    reward_days: int
    sync_state: str
    wheel_last_spin_at: datetime | None = None
    wheel_next_spin_at: datetime | None = None
    calendar_cycle_started_on: date | None = None
    calendar_cycle_day: int = 0
    already_checked_in: bool = False
    achievements: Mapping[str, bool] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RewardHistoryEntry:
    durable_id: str
    source: str
    reward_days: int
    committed_at: datetime
    metadata: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class RewardBackfillResult:
    canonical_accounts: int
    states_created: int
    wheel_sources_seen: int
    wheel_states_updated: int
    unresolved_users: int
    invalid_merge_chains: int

    @property
    def ready(self) -> bool:
        return self.unresolved_users == 0 and self.invalid_merge_chains == 0


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.replace(microsecond=0)


def reward_sync_state(job: NodeProvisioningJob | None) -> str:
    if job is None:
        return "not_required"
    if job.status == "completed":
        return "synced"
    if job.status == "manual_review":
        return "manual_review"
    return "sync_pending"


def validate_calendar_state(state: RewardAccountState) -> None:
    cycle_day = int(state.calendar_cycle_day or 0)
    if cycle_day == 0:
        if (
            state.calendar_last_check_date is None
            and state.calendar_cycle_started_on is None
        ):
            return
        raise RewardDomainError("calendar_state_invalid")
    if not 1 <= cycle_day <= 28:
        raise RewardDomainError("calendar_state_invalid")
    if (
        state.calendar_last_check_date is None
        or state.calendar_cycle_started_on is None
    ):
        raise RewardDomainError("calendar_state_invalid")
    expected_start = state.calendar_last_check_date - timedelta(days=cycle_day - 1)
    if state.calendar_cycle_started_on != expected_start:
        raise RewardDomainError("calendar_state_invalid")


def _locked_reward_state(
    session,
    *,
    account_id: str,
    now: datetime,
) -> RewardAccountState:
    state = (
        session.query(RewardAccountState)
        .filter(RewardAccountState.account_id == str(account_id))
        .with_for_update()
        .one_or_none()
    )
    if state is None:
        state = RewardAccountState(
            account_id=str(account_id),
            calendar_cycle_day=0,
            created_at=now,
            updated_at=now,
        )
        session.add(state)
        session.flush()
    validate_calendar_state(state)
    return state


def parse_paid_weekly_config(
    payload: Mapping[str, object],
    *,
    explicit: bool,
) -> WheelConfig:
    candidate = dict(PAID_WEEKLY_V1 if not explicit and not payload else payload)
    if candidate.get("preset") != "paid_weekly_v1":
        raise InvalidWheelConfig("wheel_preset_invalid")
    cooldown = candidate.get("cooldown_hours")
    if type(cooldown) is not int or cooldown != 168:
        raise InvalidWheelConfig("wheel_cooldown_invalid")

    raw = candidate.get("weights")
    if (
        not isinstance(raw, list)
        or len(raw) != 4
        or any(not isinstance(row, dict) for row in raw)
    ):
        raise InvalidWheelConfig("wheel_outcome_order_invalid")
    days = tuple(row.get("days") for row in raw)
    if days != WHEEL_SECTORS or any(type(value) is not int for value in days):
        raise InvalidWheelConfig("wheel_outcome_order_invalid")
    weights = tuple(row.get("weight") for row in raw)
    if (
        weights != (9000, 890, 100, 10)
        or any(type(value) is not int for value in weights)
        or sum(weights) != 10000
    ):
        raise InvalidWheelConfig("wheel_weights_invalid")
    outcomes = tuple(zip(days, weights, strict=True))
    return WheelConfig(
        preset="paid_weekly_v1",
        cooldown_hours=168,
        outcomes=outcomes,
    )


def _reward_days_for_draw(config: WheelConfig, draw: int) -> int:
    if type(draw) is not int or not 0 <= draw < 10000:
        raise RewardDomainError("wheel_draw_invalid")
    cursor = 0
    for days, weight in config.outcomes:
        cursor += int(weight)
        if draw < cursor:
            return int(days)
    raise RewardDomainError("wheel_draw_invalid")


def _last_wheel_reward_days(
    session,
    state: RewardAccountState,
) -> int | None:
    if not state.wheel_last_grant_id:
        return None
    grant = session.get(EntitlementGrant, state.wheel_last_grant_id)
    if grant is None or grant.source != "bonus_wheel":
        return None
    return int(grant.duration_days or 0) or None


def _reward_sync_job(
    session,
    *,
    entitlement_grant_id: str | None,
) -> NodeProvisioningJob | None:
    grant_id = str(entitlement_grant_id or "").strip()
    if not grant_id:
        return None
    return (
        session.query(NodeProvisioningJob)
        .filter(
            NodeProvisioningJob.entitlement_grant_id == grant_id,
            NodeProvisioningJob.job_type == "reward_entitlement_sync",
        )
        .order_by(NodeProvisioningJob.id.desc())
        .first()
    )


def _safe_preset_name(payload: Mapping[str, object] | None) -> str:
    raw = str((payload or {}).get("preset") or "missing").strip()
    return raw if _SAFE_PRESET_RE.fullmatch(raw) else "invalid"


def _log_invalid_wheel_config(
    payload: Mapping[str, object] | None,
    exc: InvalidWheelConfig,
) -> None:
    _LOGGER.warning(
        "reward_wheel_config_invalid preset=%s validation_code=%s",
        _safe_preset_name(payload),
        exc.code,
    )


def _parse_wheel_config(
    config_payload: Mapping[str, object] | None,
) -> WheelConfig:
    return (
        parse_paid_weekly_config(PAID_WEEKLY_V1, explicit=False)
        if config_payload is None
        else parse_paid_weekly_config(config_payload, explicit=True)
    )


def evaluate_active_paid(
    session,
    *,
    account_id: str,
    now: datetime,
) -> PaidEligibility:
    current_now = _naive_utc(now)
    try:
        account_key = resolve_canonical_account_id(session, account_id=account_id)
    except ValueError as exc:
        return PaidEligibility(False, str(exc), str(account_id), None)
    account = (
        session.query(Account)
        .filter(Account.id == account_key)
        .with_for_update()
        .one_or_none()
    )
    if account is None:
        return PaidEligibility(False, "account_not_found", account_key, None)
    if (
        str(account.status or "").lower() != "active"
        or account.merged_into_account_id is not None
    ):
        return PaidEligibility(False, "account_inactive", account_key, None)

    rebuild_account_entitlement_projection(
        session,
        account_id=account_key,
        now=current_now,
    )
    paid_users = (
        session.query(User)
        .filter(
            User.account_id == account_key,
            User.is_active.is_(True),
            User.sub_type == "PAID",
            User.expiry_at.isnot(None),
            User.expiry_at > current_now,
        )
        .order_by(User.tg_id.asc())
        .with_for_update()
        .all()
    )
    paid_grant = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == account_key,
            EntitlementGrant.status.in_(["active", "grace"]),
            EntitlementGrant.reversed_at.is_(None),
            EntitlementGrant.grant_kind == "paid_access",
            EntitlementGrant.source.in_(sorted(PAID_GRANT_SOURCES)),
            EntitlementGrant.starts_at.isnot(None),
            EntitlementGrant.starts_at <= current_now,
            EntitlementGrant.expires_at.isnot(None),
            EntitlementGrant.expires_at > current_now,
        )
        .with_for_update()
        .first()
    )
    if not paid_users or paid_grant is None:
        return PaidEligibility(False, "active_paid_required", account_key, None)
    return PaidEligibility(True, "eligible", account_key, int(paid_users[0].tg_id))


def get_wheel_state(
    session,
    *,
    account_id: str,
    enabled: bool,
    config_payload: Mapping[str, object] | None,
    now: datetime,
) -> WheelState:
    current_now = _naive_utc(now)
    if not enabled:
        return WheelState(
            enabled=False,
            eligible=False,
            reason="bonus_feature_disabled",
            can_spin=False,
            sectors=(),
            cooldown_hours=168,
            last_spin_at=None,
            next_spin_at=None,
            last_reward_days=None,
            sync_state="not_required",
        )
    try:
        config = _parse_wheel_config(config_payload)
    except InvalidWheelConfig as exc:
        _log_invalid_wheel_config(config_payload, exc)
        return WheelState(
            enabled=False,
            eligible=False,
            reason="wheel_config_invalid",
            can_spin=False,
            sectors=(),
            cooldown_hours=0,
            last_spin_at=None,
            next_spin_at=None,
            last_reward_days=None,
            sync_state="not_required",
        )

    eligibility = evaluate_active_paid(
        session,
        account_id=account_id,
        now=current_now,
    )
    if not eligibility.eligible:
        return WheelState(
            enabled=True,
            eligible=False,
            reason=eligibility.reason,
            can_spin=False,
            sectors=WHEEL_SECTORS,
            cooldown_hours=config.cooldown_hours,
            last_spin_at=None,
            next_spin_at=None,
            last_reward_days=None,
            sync_state="not_required",
        )

    state = _locked_reward_state(
        session,
        account_id=eligibility.account_id,
        now=current_now,
    )
    last_spin_at = (
        _naive_utc(state.wheel_last_spin_at)
        if state.wheel_last_spin_at is not None
        else None
    )
    next_spin_at = (
        last_spin_at + timedelta(hours=config.cooldown_hours)
        if last_spin_at is not None
        else None
    )
    can_spin = next_spin_at is None or next_spin_at <= current_now
    job = _reward_sync_job(
        session,
        entitlement_grant_id=state.wheel_last_grant_id,
    )
    return WheelState(
        enabled=True,
        eligible=True,
        reason="eligible" if can_spin else "wheel_cooldown_active",
        can_spin=can_spin,
        sectors=WHEEL_SECTORS,
        cooldown_hours=config.cooldown_hours,
        last_spin_at=last_spin_at,
        next_spin_at=next_spin_at,
        last_reward_days=_last_wheel_reward_days(session, state),
        sync_state=reward_sync_state(job),
    )


def spin_wheel(
    session,
    *,
    account_id: str,
    enabled: bool,
    config_payload: Mapping[str, object] | None,
    now: datetime,
    randbelow: Callable[[int], int] = secrets.randbelow,
) -> RewardMutation:
    current_now = _naive_utc(now)
    if not enabled:
        raise RewardDisabled("wheel")
    try:
        config = _parse_wheel_config(config_payload)
    except InvalidWheelConfig as exc:
        _log_invalid_wheel_config(config_payload, exc)
        raise

    eligibility = evaluate_active_paid(
        session,
        account_id=account_id,
        now=current_now,
    )
    if not eligibility.eligible:
        raise RewardForbidden(eligibility.reason)
    state = _locked_reward_state(
        session,
        account_id=eligibility.account_id,
        now=current_now,
    )
    last_spin_at = (
        _naive_utc(state.wheel_last_spin_at)
        if state.wheel_last_spin_at is not None
        else None
    )
    next_spin_at = (
        last_spin_at + timedelta(hours=config.cooldown_hours)
        if last_spin_at is not None
        else None
    )
    if next_spin_at is not None and next_spin_at > current_now:
        raise RewardConflict(
            "wheel_cooldown_active",
            next_allowed_at=next_spin_at,
            last_reward_days=_last_wheel_reward_days(session, state),
        )

    draw = randbelow(10000)
    reward_days = _reward_days_for_draw(config, draw)
    event_id = str(uuid.uuid4())
    grant = grant_internal_bonus_days(
        session,
        account_id=eligibility.account_id,
        source="bonus_wheel",
        plan_code="reward_wheel",
        idempotency_key=f"reward-wheel:v1:{event_id}",
        days=reward_days,
        legacy_tg_id=eligibility.legacy_tg_id,
        metadata={
            "version": 1,
            "preset": config.preset,
            "reward_days": reward_days,
            "committed_at": current_now.isoformat(),
        },
        now=current_now,
    )
    job = enqueue_reward_entitlement_sync(
        session,
        account_id=eligibility.account_id,
        entitlement_grant_id=grant.id,
        now=current_now,
    )
    state.wheel_last_spin_at = current_now
    state.wheel_last_grant_id = grant.id
    state.updated_at = current_now
    validate_calendar_state(state)
    session.flush()
    return RewardMutation(
        feature="wheel",
        account_id=eligibility.account_id,
        grant_id=grant.id,
        reward_days=reward_days,
        sync_state=reward_sync_state(job),
        wheel_last_spin_at=current_now,
        wheel_next_spin_at=current_now + timedelta(hours=config.cooldown_hours),
    )


def _calendar_achievements(state: RewardAccountState) -> dict[str, bool]:
    return {
        "first_checkin": state.calendar_first_checkin_at is not None,
        "streak_7": state.calendar_streak_7_unlocked_at is not None,
    }


def _next_calendar_position(
    state: RewardAccountState,
    today: date,
) -> tuple[date, int]:
    if state.calendar_last_check_date == today:
        return (
            state.calendar_cycle_started_on or today,
            int(state.calendar_cycle_day or 1),
        )
    consecutive = state.calendar_last_check_date == today - timedelta(days=1)
    if consecutive and int(state.calendar_cycle_day or 0) < 28:
        return (
            state.calendar_cycle_started_on or today,
            int(state.calendar_cycle_day or 0) + 1,
        )
    return today, 1


def _calendar_grant_key(
    *,
    origin_account_id: str,
    cycle_start: date,
    milestone: int,
) -> str:
    return (
        f"reward-calendar:v1:{origin_account_id}:"
        f"{cycle_start.isoformat()}:{int(milestone)}"
    )


def _json_object(raw: str | None) -> dict[str, object]:
    try:
        parsed = json.loads(raw or "{}")
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _calendar_grant_for_position(
    session,
    *,
    account_id: str,
    cycle_start: date,
    milestone: int,
) -> EntitlementGrant | None:
    rows = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == str(account_id),
            EntitlementGrant.source == "bonus_calendar",
        )
        .order_by(EntitlementGrant.created_at.desc(), EntitlementGrant.id.desc())
        .limit(64)
        .all()
    )
    expected_cycle_start = cycle_start.isoformat()
    for row in rows:
        metadata = _json_object(row.metadata_json)
        if (
            metadata.get("cycle_start") == expected_cycle_start
            and type(metadata.get("milestone")) is int
            and metadata.get("milestone") == int(milestone)
        ):
            return row
    return None


def _latest_calendar_grant_for_state(
    session,
    state: RewardAccountState,
) -> EntitlementGrant | None:
    cycle_start = state.calendar_cycle_started_on
    cycle_day = int(state.calendar_cycle_day or 0)
    if cycle_start is None or cycle_day < min(CALENDAR_MILESTONES):
        return None
    earned = [milestone for milestone in CALENDAR_MILESTONES if milestone <= cycle_day]
    if not earned:
        return None
    return _calendar_grant_for_position(
        session,
        account_id=state.account_id,
        cycle_start=cycle_start,
        milestone=max(earned),
    )


def _next_calendar_milestone(cycle_day: int) -> int | None:
    return next(
        (milestone for milestone in sorted(CALENDAR_MILESTONES) if milestone > cycle_day),
        None,
    )


def get_calendar_state(
    session,
    *,
    account_id: str,
    enabled: bool,
    now: datetime,
) -> CalendarState:
    current_now = _naive_utc(now)
    empty_achievements = {"first_checkin": False, "streak_7": False}
    if not enabled:
        return CalendarState(
            enabled=False,
            eligible=False,
            reason="bonus_feature_disabled",
            checked_in_today=False,
            cycle_started_on=None,
            cycle_day=0,
            next_milestone=7,
            achievements=empty_achievements,
            sync_state="not_required",
        )

    eligibility = evaluate_active_paid(
        session,
        account_id=account_id,
        now=current_now,
    )
    if not eligibility.eligible:
        return CalendarState(
            enabled=True,
            eligible=False,
            reason=eligibility.reason,
            checked_in_today=False,
            cycle_started_on=None,
            cycle_day=0,
            next_milestone=7,
            achievements=empty_achievements,
            sync_state="not_required",
        )

    state = _locked_reward_state(
        session,
        account_id=eligibility.account_id,
        now=current_now,
    )
    cycle_day = int(state.calendar_cycle_day or 0)
    latest_grant = _latest_calendar_grant_for_state(session, state)
    job = _reward_sync_job(
        session,
        entitlement_grant_id=latest_grant.id if latest_grant else None,
    )
    return CalendarState(
        enabled=True,
        eligible=True,
        reason="eligible",
        checked_in_today=state.calendar_last_check_date == current_now.date(),
        cycle_started_on=state.calendar_cycle_started_on,
        cycle_day=cycle_day,
        next_milestone=_next_calendar_milestone(cycle_day),
        achievements=_calendar_achievements(state),
        sync_state=reward_sync_state(job),
    )


def checkin_calendar(
    session,
    *,
    account_id: str,
    enabled: bool,
    now: datetime,
) -> RewardMutation:
    current_now = _naive_utc(now)
    if not enabled:
        raise RewardDisabled("calendar")
    eligibility = evaluate_active_paid(
        session,
        account_id=account_id,
        now=current_now,
    )
    if not eligibility.eligible:
        raise RewardForbidden(eligibility.reason)
    state = _locked_reward_state(
        session,
        account_id=eligibility.account_id,
        now=current_now,
    )
    today = current_now.date()
    if state.calendar_last_check_date == today:
        grant = None
        cycle_day = int(state.calendar_cycle_day or 0)
        if cycle_day in CALENDAR_MILESTONES and state.calendar_cycle_started_on:
            grant = _calendar_grant_for_position(
                session,
                account_id=eligibility.account_id,
                cycle_start=state.calendar_cycle_started_on,
                milestone=cycle_day,
            )
        job = _reward_sync_job(
            session,
            entitlement_grant_id=grant.id if grant else None,
        )
        return RewardMutation(
            feature="calendar",
            account_id=eligibility.account_id,
            grant_id=grant.id if grant else None,
            reward_days=int(grant.duration_days or 0) if grant else 0,
            sync_state=reward_sync_state(job),
            calendar_cycle_started_on=state.calendar_cycle_started_on,
            calendar_cycle_day=cycle_day,
            already_checked_in=True,
            achievements=_calendar_achievements(state),
        )

    cycle_start, cycle_day = _next_calendar_position(state, today)
    state.calendar_cycle_started_on = cycle_start
    state.calendar_cycle_day = cycle_day
    state.calendar_last_check_date = today
    if state.calendar_first_checkin_at is None:
        state.calendar_first_checkin_at = current_now
    if cycle_day >= 7 and state.calendar_streak_7_unlocked_at is None:
        state.calendar_streak_7_unlocked_at = current_now

    grant = None
    job = None
    if cycle_day in CALENDAR_MILESTONES:
        grant = grant_internal_bonus_days(
            session,
            account_id=eligibility.account_id,
            source="bonus_calendar",
            plan_code="reward_calendar",
            idempotency_key=_calendar_grant_key(
                origin_account_id=eligibility.account_id,
                cycle_start=cycle_start,
                milestone=cycle_day,
            ),
            days=1,
            legacy_tg_id=eligibility.legacy_tg_id,
            metadata={
                "version": 1,
                "origin_account_id": eligibility.account_id,
                "cycle_start": cycle_start.isoformat(),
                "milestone": cycle_day,
                "reward_days": 1,
                "committed_at": current_now.isoformat(),
            },
            now=current_now,
        )
        job = enqueue_reward_entitlement_sync(
            session,
            account_id=eligibility.account_id,
            entitlement_grant_id=grant.id,
            now=current_now,
        )
    state.updated_at = current_now
    validate_calendar_state(state)
    session.flush()
    return RewardMutation(
        feature="calendar",
        account_id=eligibility.account_id,
        grant_id=grant.id if grant else None,
        reward_days=int(grant.duration_days or 0) if grant else 0,
        sync_state=reward_sync_state(job),
        calendar_cycle_started_on=cycle_start,
        calendar_cycle_day=cycle_day,
        already_checked_in=False,
        achievements=_calendar_achievements(state),
    )


def _bounded_reward_days(value: object) -> int | None:
    if type(value) is not int or not 0 <= value <= 366:
        return None
    return int(value)


def _metadata_committed_at(
    metadata: Mapping[str, object],
    *,
    fallback: datetime,
) -> datetime:
    raw = metadata.get("committed_at")
    if not isinstance(raw, str) or not 1 <= len(raw) <= 64:
        return _naive_utc(fallback)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return _naive_utc(fallback)
    return _naive_utc(parsed)


def _legacy_history_metadata(claim: RewardClaim) -> tuple[int, dict[str, object]]:
    raw = _json_object(claim.meta)
    days = _bounded_reward_days(raw.get("days"))
    if days is None:
        days = _bounded_reward_days(raw.get("reward_days"))
    metadata: dict[str, object] = {"reward_key": str(claim.reward_key or "")[:64]}
    feature = raw.get("feature")
    if feature in {"wheel", "calendar"}:
        metadata["feature"] = feature
    preset = raw.get("preset")
    if isinstance(preset, str) and _SAFE_PRESET_RE.fullmatch(preset):
        metadata["preset"] = preset
    streak = raw.get("streak")
    if type(streak) is int and 0 <= streak <= 10000:
        metadata["streak"] = streak
    return days or 0, metadata


def _grant_history_metadata(
    grant: EntitlementGrant,
) -> tuple[int, datetime, dict[str, object]]:
    raw = _json_object(grant.metadata_json)
    reward_days = _bounded_reward_days(raw.get("reward_days"))
    if reward_days is None:
        reward_days = _bounded_reward_days(grant.duration_days)
    metadata: dict[str, object] = {}
    version = raw.get("version")
    if type(version) is int and 0 <= version <= 100:
        metadata["version"] = version
    if grant.source == "bonus_wheel":
        preset = raw.get("preset")
        if isinstance(preset, str) and _SAFE_PRESET_RE.fullmatch(preset):
            metadata["preset"] = preset
    if grant.source == "bonus_calendar":
        cycle_start = raw.get("cycle_start")
        if isinstance(cycle_start, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", cycle_start):
            metadata["cycle_start"] = cycle_start
        milestone = raw.get("milestone")
        if type(milestone) is int and milestone in CALENDAR_MILESTONES:
            metadata["milestone"] = milestone
    committed_at = _metadata_committed_at(
        raw,
        fallback=grant.created_at,
    )
    return reward_days or 0, committed_at, metadata


def get_reward_history(
    session,
    *,
    account_id: str,
    limit: int = 50,
) -> list[RewardHistoryEntry]:
    account_key = resolve_canonical_account_id(session, account_id=account_id)
    max_items = max(1, min(int(limit or 50), 100))
    tg_ids = [
        int(row[0])
        for row in (
            session.query(User.tg_id)
            .filter(User.account_id == account_key)
            .order_by(User.tg_id.asc())
            .all()
        )
    ]
    entries: list[RewardHistoryEntry] = []
    if tg_ids:
        legacy_rows = (
            session.query(RewardClaim)
            .filter(RewardClaim.tg_id.in_(tg_ids))
            .order_by(RewardClaim.claimed_at.desc(), RewardClaim.id.desc())
            .limit(max_items)
            .all()
        )
        for claim in legacy_rows:
            reward_days, metadata = _legacy_history_metadata(claim)
            entries.append(
                RewardHistoryEntry(
                    durable_id=f"legacy_reward_claim:{claim.id}",
                    source="legacy_reward_claim",
                    reward_days=reward_days,
                    committed_at=_naive_utc(claim.claimed_at),
                    metadata=metadata,
                )
            )

    grant_rows = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == account_key,
            EntitlementGrant.source.in_(("bonus_wheel", "bonus_calendar")),
        )
        .order_by(EntitlementGrant.created_at.desc(), EntitlementGrant.id.desc())
        .limit(max_items)
        .all()
    )
    for grant in grant_rows:
        reward_days, committed_at, metadata = _grant_history_metadata(grant)
        entries.append(
            RewardHistoryEntry(
                durable_id=f"account_entitlement_grant:{grant.id}",
                source=str(grant.source),
                reward_days=reward_days,
                committed_at=committed_at,
                metadata=metadata,
            )
        )
    entries.sort(
        key=lambda entry: (entry.committed_at, entry.durable_id),
        reverse=True,
    )
    return entries[:max_items]


def backfill_reward_account_states(
    session,
    *,
    now: datetime,
) -> RewardBackfillResult:
    current_now = _naive_utc(now)
    account_ids = [
        str(row.id)
        for row in session.query(Account.id).order_by(Account.id.asc()).all()
    ]
    known_account_ids = set(account_ids)
    resolutions: dict[str, str | None] = {}
    invalid_account_ids: set[str] = set()
    canonical_account_ids: set[str] = set()
    for account_id in account_ids:
        try:
            canonical_id = resolve_canonical_account_id(
                session,
                account_id=account_id,
            )
        except ValueError:
            resolutions[account_id] = None
            invalid_account_ids.add(account_id)
            continue
        resolutions[account_id] = canonical_id
        canonical_account_ids.add(canonical_id)

    wheel_timestamps: dict[str, list[datetime]] = {
        account_id: [] for account_id in canonical_account_ids
    }
    unresolved_users = 0
    user_rows = (
        session.query(User.tg_id, User.account_id, User.last_wheel_spin)
        .order_by(User.tg_id.asc())
        .all()
    )
    wheel_sources_seen = 0
    for _tg_id, raw_account_id, last_wheel_spin in user_rows:
        if last_wheel_spin is not None:
            wheel_sources_seen += 1
        account_id = str(raw_account_id or "").strip()
        if not account_id or account_id not in known_account_ids:
            unresolved_users += 1
            continue
        canonical_id = resolutions.get(account_id)
        if canonical_id is None:
            unresolved_users += 1
            continue
        if last_wheel_spin is not None:
            wheel_timestamps.setdefault(canonical_id, []).append(
                _naive_utc(last_wheel_spin)
            )

    open_merge_reviews = (
        session.query(AccountMergeReview.id)
        .filter(
            ~AccountMergeReview.status.in_(
                sorted(_TERMINAL_MERGE_REVIEW_STATUSES)
            )
        )
        .count()
    )
    invalid_merge_chains = len(invalid_account_ids) + int(open_merge_reviews)

    existing_state_ids = {
        str(row.account_id)
        for row in session.query(RewardAccountState.account_id)
        .filter(RewardAccountState.account_id.in_(sorted(canonical_account_ids)))
        .all()
    }
    states_created = 0
    wheel_states_updated = 0
    for account_id in sorted(canonical_account_ids):
        state = _locked_reward_state(
            session,
            account_id=account_id,
            now=current_now,
        )
        if account_id not in existing_state_ids:
            states_created += 1
        timestamps = wheel_timestamps.get(account_id, [])
        latest = max(timestamps, default=None)
        if latest is not None and (
            state.wheel_last_spin_at is None
            or _naive_utc(state.wheel_last_spin_at) < latest
        ):
            state.wheel_last_spin_at = latest
            state.updated_at = current_now
            wheel_states_updated += 1
        validate_calendar_state(state)
    session.flush()

    return RewardBackfillResult(
        canonical_accounts=len(canonical_account_ids),
        states_created=states_created,
        wheel_sources_seen=wheel_sources_seen,
        wheel_states_updated=wheel_states_updated,
        unresolved_users=unresolved_users,
        invalid_merge_chains=invalid_merge_chains,
    )

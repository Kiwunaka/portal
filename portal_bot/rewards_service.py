from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from economy_service import (
    rebuild_account_entitlement_projection,
    resolve_canonical_account_id,
)
from models import (
    Account,
    AccountMergeReview,
    EntitlementGrant,
    NodeProvisioningJob,
    RewardAccountState,
    User,
)


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

from __future__ import annotations

import json
import sys
import uuid
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from models import (
    Account,
    Base,
    EntitlementGrant,
    NodeProvisioningJob,
    RewardAccountState,
    User,
)


PAID_ACCOUNT_ID = "00000000-0000-4000-8000-000000000101"
PAID_TG_ID = 700101


@dataclass(frozen=True)
class SeededPaidAccount:
    id: str
    tg_id: int


@pytest.fixture()
def now() -> datetime:
    return datetime(2026, 7, 20, 12, 0, 0)


@pytest.fixture()
def reward_session(tmp_path):
    engine = create_engine(
        f"sqlite:///{(tmp_path / 'rewards.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as session:
        yield session
        session.rollback()
    engine.dispose()


@pytest.fixture()
def paid_account(reward_session, now) -> SeededPaidAccount:
    reward_session.add(
        Account(
            id=PAID_ACCOUNT_ID,
            status="active",
            created_source="test",
            created_at=now,
            updated_at=now,
        )
    )
    reward_session.add(
        User(
            tg_id=PAID_TG_ID,
            account_id=PAID_ACCOUNT_ID,
            uuid="00000000-0000-4000-8000-000000000102",
            sub_type="PAID",
            current_plan_code="month",
            expiry_at=now + timedelta(days=30),
            is_active=True,
        )
    )
    reward_session.add(
        EntitlementGrant(
            id="00000000-0000-4000-8000-000000000103",
            account_id=PAID_ACCOUNT_ID,
            legacy_tg_id=PAID_TG_ID,
            idempotency_key="test-provider-payment:paid-account",
            source="provider_payment",
            status="active",
            grant_kind="paid_access",
            plan_code="month",
            starts_at=now - timedelta(days=1),
            expires_at=now + timedelta(days=30),
            activated_at=now - timedelta(days=1),
            duration_days=31,
            provider="test",
            created_at=now - timedelta(days=1),
            updated_at=now,
        )
    )
    reward_session.flush()
    return SeededPaidAccount(id=PAID_ACCOUNT_ID, tg_id=PAID_TG_ID)


def _grant_reward(session, paid_account: SeededPaidAccount, now: datetime, *, days: int = 1):
    from economy_service import grant_internal_bonus_days

    return grant_internal_bonus_days(
        session,
        account_id=paid_account.id,
        source="bonus_wheel",
        plan_code="reward_wheel",
        idempotency_key="reward-wheel:v1:00000000-0000-4000-8000-000000000001",
        days=days,
        legacy_tg_id=paid_account.tg_id,
        metadata={"version": 1, "reward_days": days, "committed_at": now.isoformat()},
        now=now,
    )


def test_internal_reward_grant_and_sync_job_are_idempotent(reward_session, paid_account, now) -> None:
    from node_provisioning_service import enqueue_reward_entitlement_sync

    first = _grant_reward(reward_session, paid_account, now)
    first_job = enqueue_reward_entitlement_sync(
        reward_session,
        account_id=paid_account.id,
        entitlement_grant_id=first.id,
        now=now,
    )
    second = _grant_reward(reward_session, paid_account, now)
    second_job = enqueue_reward_entitlement_sync(
        reward_session,
        account_id=paid_account.id,
        entitlement_grant_id=second.id,
        now=now,
    )
    reward_session.flush()

    assert second.id == first.id
    assert second_job.id == first_job.id
    assert first.grant_kind == "premium_bonus"
    assert first.provider == "internal_economy"
    assert json.loads(first.metadata_json) == {
        "committed_at": now.isoformat(),
        "reward_days": 1,
        "version": 1,
    }
    assert first_job.idempotency_key == f"reward-entitlement-sync:v1:{first.id}"
    assert first_job.account_id == paid_account.id
    assert first_job.entitlement_grant_id == first.id
    assert reward_session.query(EntitlementGrant).filter_by(source="bonus_wheel").count() == 1
    assert reward_session.query(NodeProvisioningJob).filter_by(job_type="reward_entitlement_sync").count() == 1


@pytest.mark.parametrize(
    ("source", "days", "code"),
    [
        ("provider_payment", 1, "reward_source_invalid"),
        ("bonus_wheel", 2, "reward_days_invalid"),
        ("bonus_calendar", 0, "reward_days_invalid"),
    ],
)
def test_internal_reward_grant_rejects_invalid_source_or_days(
    reward_session,
    paid_account,
    now,
    source: str,
    days: int,
    code: str,
) -> None:
    from economy_service import grant_internal_bonus_days

    with pytest.raises(ValueError, match=code):
        grant_internal_bonus_days(
            reward_session,
            account_id=paid_account.id,
            source=source,
            plan_code="reward",
            idempotency_key="reward-invalid:v1",
            days=days,
            legacy_tg_id=paid_account.tg_id,
            metadata={},
            now=now,
        )


def test_internal_reward_grant_rejects_idempotency_conflict(reward_session, paid_account, now) -> None:
    first = _grant_reward(reward_session, paid_account, now)

    from economy_service import grant_internal_bonus_days

    with pytest.raises(ValueError, match="reward_idempotency_conflict"):
        grant_internal_bonus_days(
            reward_session,
            account_id=paid_account.id,
            source="bonus_wheel",
            plan_code="reward_wheel",
            idempotency_key=first.idempotency_key,
            days=3,
            legacy_tg_id=paid_account.tg_id,
            metadata={"version": 1, "reward_days": 3},
            now=now,
        )


def test_public_account_resolver_follows_merge_chain_under_lock(reward_session, now) -> None:
    from economy_service import resolve_canonical_account_id

    target_id = "00000000-0000-4000-8000-000000000201"
    source_id = "00000000-0000-4000-8000-000000000202"
    reward_session.add_all(
        [
            Account(
                id=target_id,
                status="active",
                created_source="test",
                created_at=now,
                updated_at=now,
            ),
            Account(
                id=source_id,
                status="merged",
                merged_into_account_id=target_id,
                created_source="test",
                created_at=now,
                updated_at=now,
            ),
        ]
    )
    reward_session.flush()

    assert resolve_canonical_account_id(reward_session, account_id=source_id) == target_id


@pytest.mark.parametrize(
    ("status", "merged_into_account_id"),
    (
        ("merged", None),
        ("active", "00000000-0000-4000-8000-000000000211"),
    ),
)
def test_public_account_resolver_rejects_malformed_merge_shape(
    reward_session,
    now,
    status: str,
    merged_into_account_id: str | None,
) -> None:
    from economy_service import resolve_canonical_account_id

    account_id = "00000000-0000-4000-8000-000000000212"
    reward_session.add(
        Account(
            id=account_id,
            status=status,
            merged_into_account_id=merged_into_account_id,
            created_source="test",
            created_at=now,
            updated_at=now,
        )
    )
    reward_session.flush()

    with pytest.raises(ValueError, match="invalid_account_merge_chain"):
        resolve_canonical_account_id(reward_session, account_id=account_id)


def test_reward_grant_and_sync_job_roll_back_atomically(reward_session, paid_account, now) -> None:
    from node_provisioning_service import enqueue_reward_entitlement_sync

    reward_session.commit()
    try:
        grant = _grant_reward(reward_session, paid_account, now)
        enqueue_reward_entitlement_sync(
            reward_session,
            account_id=paid_account.id,
            entitlement_grant_id=grant.id,
            now=now,
        )
        raise RuntimeError("force_rollback")
    except RuntimeError as exc:
        assert str(exc) == "force_rollback"
        reward_session.rollback()

    Session = sessionmaker(bind=reward_session.bind, expire_on_commit=False)
    with Session() as verification:
        assert verification.query(EntitlementGrant).filter_by(source="bonus_wheel").count() == 0
        assert verification.query(NodeProvisioningJob).filter_by(job_type="reward_entitlement_sync").count() == 0
        user = verification.query(User).filter_by(tg_id=paid_account.tg_id).one()
        assert user.expiry_at == now + timedelta(days=30)


def seed_reward_identity(
    session,
    *,
    now: datetime,
    account_status: str,
    sub_type: str,
    grant_source: str,
    grant_kind: str,
) -> str:
    account_id = str(uuid.uuid4())
    tg_id = 710000 + session.query(Account).count()
    session.add(
        Account(
            id=account_id,
            status=account_status,
            created_source="test",
            created_at=now,
            updated_at=now,
        )
    )
    session.add(
        User(
            tg_id=tg_id,
            account_id=account_id,
            uuid=str(uuid.uuid4()),
            sub_type=sub_type,
            current_plan_code="test",
            expiry_at=now + timedelta(days=30),
            is_active=True,
        )
    )
    session.add(
        EntitlementGrant(
            id=str(uuid.uuid4()),
            account_id=account_id,
            legacy_tg_id=tg_id,
            idempotency_key=f"eligibility-test:{account_id}",
            source=grant_source,
            status="active",
            grant_kind=grant_kind,
            plan_code="test",
            starts_at=now - timedelta(days=1),
            expires_at=now + timedelta(days=30),
            activated_at=now - timedelta(days=1),
            duration_days=31,
            provider="test",
            created_at=now - timedelta(days=1),
            updated_at=now,
        )
    )
    session.flush()
    return account_id


@pytest.mark.parametrize(
    ("patch", "code"),
    (
        ({"preset": "balanced"}, "wheel_preset_invalid"),
        ({"cooldown_hours": 167}, "wheel_cooldown_invalid"),
        (
            {
                "weights": [
                    {"days": 1, "weight": 8999},
                    {"days": 3, "weight": 891},
                    {"days": 7, "weight": 100},
                    {"days": 30, "weight": 10},
                ]
            },
            "wheel_weights_invalid",
        ),
        (
            {
                "weights": [
                    {"days": 3, "weight": 890},
                    {"days": 1, "weight": 9000},
                    {"days": 7, "weight": 100},
                    {"days": 30, "weight": 10},
                ]
            },
            "wheel_outcome_order_invalid",
        ),
    ),
)
def test_paid_weekly_v1_rejects_drift(patch, code) -> None:
    from rewards_service import InvalidWheelConfig, PAID_WEEKLY_V1, parse_paid_weekly_config

    payload = deepcopy(PAID_WEEKLY_V1)
    payload.update(patch)
    with pytest.raises(InvalidWheelConfig, match=code):
        parse_paid_weekly_config(payload, explicit=True)


def test_paid_weekly_v1_exposes_exact_immutable_outcomes() -> None:
    from rewards_service import PAID_WEEKLY_V1, parse_paid_weekly_config

    parsed = parse_paid_weekly_config(deepcopy(PAID_WEEKLY_V1), explicit=False)

    assert parsed.preset == "paid_weekly_v1"
    assert parsed.cooldown_hours == 168
    assert parsed.outcomes == ((1, 9000), (3, 890), (7, 100), (30, 10))


@pytest.mark.parametrize(
    ("account_status", "sub_type", "grant_source", "grant_kind", "expected_reason"),
    (
        ("active", "PAID", "provider_payment", "paid_access", "eligible"),
        ("active", "PAID", "compatibility_projection", "paid_access", "eligible"),
        ("active", "TRIAL", "trial_activation", "premium_trial", "active_paid_required"),
        ("active", "BONUS", "bonus_wheel", "premium_bonus", "active_paid_required"),
        ("active", "PAID", "bonus_calendar", "premium_bonus", "active_paid_required"),
        ("blocked", "PAID", "provider_payment", "paid_access", "account_inactive"),
    ),
)
def test_active_paid_predicate_is_server_owned(
    reward_session,
    now,
    account_status: str,
    sub_type: str,
    grant_source: str,
    grant_kind: str,
    expected_reason: str,
) -> None:
    from rewards_service import evaluate_active_paid

    account_id = seed_reward_identity(
        reward_session,
        now=now,
        account_status=account_status,
        sub_type=sub_type,
        grant_source=grant_source,
        grant_kind=grant_kind,
    )
    result = evaluate_active_paid(reward_session, account_id=account_id, now=now)

    assert result.reason == expected_reason
    assert result.eligible is (expected_reason == "eligible")


def test_active_paid_predicate_rejects_expired_paid_interval_with_reward_tail(
    reward_session,
    now,
) -> None:
    from rewards_service import evaluate_active_paid

    account_id = seed_reward_identity(
        reward_session,
        now=now,
        account_status="active",
        sub_type="PAID",
        grant_source="provider_payment",
        grant_kind="paid_access",
    )
    paid_grant = reward_session.query(EntitlementGrant).filter_by(account_id=account_id).one()
    paid_grant.expires_at = now
    reward_session.add(
        EntitlementGrant(
            id=str(uuid.uuid4()),
            account_id=account_id,
            legacy_tg_id=paid_grant.legacy_tg_id,
            idempotency_key=f"reward-tail:{account_id}",
            source="bonus_wheel",
            status="active",
            grant_kind="premium_bonus",
            plan_code="reward_wheel",
            starts_at=now,
            expires_at=now + timedelta(days=7),
            activated_at=now,
            duration_days=7,
            provider="internal_economy",
            created_at=now,
            updated_at=now,
        )
    )
    reward_session.flush()

    result = evaluate_active_paid(reward_session, account_id=account_id, now=now)

    assert result.eligible is False
    assert result.reason == "active_paid_required"


@pytest.mark.parametrize(
    ("cycle_day", "last_check", "cycle_start", "valid"),
    (
        (0, None, None, True),
        (0, date(2026, 7, 20), None, False),
        (1, None, None, False),
        (1, date(2026, 7, 20), date(2026, 7, 20), True),
        (7, date(2026, 7, 20), date(2026, 7, 14), True),
        (7, date(2026, 7, 20), date(2026, 7, 13), False),
        (29, date(2026, 7, 20), date(2026, 6, 22), False),
    ),
)
def test_calendar_state_validator_fails_closed(
    cycle_day: int,
    last_check: date | None,
    cycle_start: date | None,
    valid: bool,
) -> None:
    from rewards_service import RewardDomainError, validate_calendar_state

    state = RewardAccountState(
        account_id=str(uuid.uuid4()),
        calendar_cycle_day=cycle_day,
        calendar_last_check_date=last_check,
        calendar_cycle_started_on=cycle_start,
    )
    if valid:
        validate_calendar_state(state)
    else:
        with pytest.raises(RewardDomainError, match="calendar_state_invalid"):
            validate_calendar_state(state)

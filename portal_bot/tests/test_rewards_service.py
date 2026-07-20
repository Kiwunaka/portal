from __future__ import annotations

import json
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
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


@pytest.fixture()
def paid_reward_session(reward_session, paid_account):
    return reward_session


@pytest.fixture()
def serialized_reward_database(tmp_path, now):
    engine = create_engine(
        f"sqlite:///{(tmp_path / 'serialized-rewards.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as session:
        session.add(
            Account(
                id=PAID_ACCOUNT_ID,
                status="active",
                created_source="test",
                created_at=now,
                updated_at=now,
            )
        )
        session.add(
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
        session.add(
            EntitlementGrant(
                id="00000000-0000-4000-8000-000000000103",
                account_id=PAID_ACCOUNT_ID,
                legacy_tg_id=PAID_TG_ID,
                idempotency_key="test-provider-payment:serialized-account",
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
        session.commit()
    try:
        yield Session, threading.Lock()
    finally:
        engine.dispose()


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


@pytest.mark.parametrize(
    ("draw", "days"),
    (
        (0, 1),
        (8999, 1),
        (9000, 3),
        (9889, 3),
        (9890, 7),
        (9989, 7),
        (9990, 30),
        (9999, 30),
    ),
)
def test_wheel_secure_draw_boundaries(paid_reward_session, now, draw: int, days: int) -> None:
    from rewards_service import PAID_WEEKLY_V1, spin_wheel

    result = spin_wheel(
        paid_reward_session,
        account_id=PAID_ACCOUNT_ID,
        enabled=True,
        config_payload=PAID_WEEKLY_V1,
        now=now,
        randbelow=lambda upper: draw if upper == 10000 else -1,
    )

    assert result.reward_days == days
    assert result.sync_state == "sync_pending"


def test_wheel_retry_returns_authoritative_cooldown_without_second_draw(
    paid_reward_session,
    now,
) -> None:
    from rewards_service import PAID_WEEKLY_V1, RewardConflict, spin_wheel

    draws = iter((9999,))
    first = spin_wheel(
        paid_reward_session,
        account_id=PAID_ACCOUNT_ID,
        enabled=True,
        config_payload=PAID_WEEKLY_V1,
        now=now,
        randbelow=lambda upper: next(draws),
    )
    with pytest.raises(RewardConflict) as exc:
        spin_wheel(
            paid_reward_session,
            account_id=PAID_ACCOUNT_ID,
            enabled=True,
            config_payload=PAID_WEEKLY_V1,
            now=now + timedelta(seconds=1),
            randbelow=lambda upper: next(draws),
        )

    assert exc.value.code == "wheel_cooldown_active"
    assert exc.value.last_reward_days == first.reward_days
    assert exc.value.next_allowed_at == now + timedelta(hours=168)


def test_wheel_disabled_and_ineligible_paths_do_not_draw(reward_session, paid_account, now) -> None:
    from rewards_service import (
        PAID_WEEKLY_V1,
        RewardDisabled,
        RewardForbidden,
        spin_wheel,
    )

    def _unexpected_draw(_upper: int) -> int:
        raise AssertionError("wheel draw must not run")

    with pytest.raises(RewardDisabled, match="bonus_feature_disabled"):
        spin_wheel(
            reward_session,
            account_id=paid_account.id,
            enabled=False,
            config_payload=PAID_WEEKLY_V1,
            now=now,
            randbelow=_unexpected_draw,
        )

    account = reward_session.get(Account, paid_account.id)
    account.status = "blocked"
    reward_session.flush()
    with pytest.raises(RewardForbidden, match="account_inactive"):
        spin_wheel(
            reward_session,
            account_id=paid_account.id,
            enabled=True,
            config_payload=PAID_WEEKLY_V1,
            now=now,
            randbelow=_unexpected_draw,
        )
    assert reward_session.query(EntitlementGrant).filter_by(source="bonus_wheel").count() == 0


@pytest.mark.parametrize("draw", (-1, 10000, True, "0"))
def test_wheel_rejects_invalid_random_draw(draw) -> None:
    from rewards_service import (
        PAID_WEEKLY_V1,
        RewardDomainError,
        _reward_days_for_draw,
        parse_paid_weekly_config,
    )

    config = parse_paid_weekly_config(
        PAID_WEEKLY_V1,
        explicit=False,
    )
    with pytest.raises(RewardDomainError, match="wheel_draw_invalid"):
        _reward_days_for_draw(config, draw)


def test_wheel_state_exposes_sectors_without_weights(paid_reward_session, now) -> None:
    from rewards_service import PAID_WEEKLY_V1, get_wheel_state, spin_wheel

    mutation = spin_wheel(
        paid_reward_session,
        account_id=PAID_ACCOUNT_ID,
        enabled=True,
        config_payload=PAID_WEEKLY_V1,
        now=now,
        randbelow=lambda _upper: 9000,
    )
    state = get_wheel_state(
        paid_reward_session,
        account_id=PAID_ACCOUNT_ID,
        enabled=True,
        config_payload=PAID_WEEKLY_V1,
        now=now + timedelta(seconds=1),
    )

    assert tuple(state.sectors) == (1, 3, 7, 30)
    assert not hasattr(state, "weights")
    assert state.can_spin is False
    assert state.reason == "wheel_cooldown_active"
    assert state.last_reward_days == mutation.reward_days
    assert state.next_spin_at == now + timedelta(hours=168)
    assert state.sync_state == "sync_pending"


def test_wheel_state_disabled_is_visible_but_not_actionable(paid_reward_session, now) -> None:
    from rewards_service import get_wheel_state

    state = get_wheel_state(
        paid_reward_session,
        account_id=PAID_ACCOUNT_ID,
        enabled=False,
        config_payload={"preset": "invalid-and-ignored-while-disabled"},
        now=now,
    )

    assert state.enabled is False
    assert state.eligible is False
    assert state.reason == "bonus_feature_disabled"
    assert state.can_spin is False
    assert tuple(state.sectors) == ()


def test_wheel_state_fails_closed_and_logs_only_bounded_config_metadata(
    paid_reward_session,
    now,
    caplog,
) -> None:
    from rewards_service import PAID_WEEKLY_V1, get_wheel_state

    payload = deepcopy(PAID_WEEKLY_V1)
    payload["weights"][0]["weight"] = 8999
    payload["operator_secret"] = "must-never-enter-log"
    caplog.set_level("WARNING", logger="rewards_service")

    state = get_wheel_state(
        paid_reward_session,
        account_id=PAID_ACCOUNT_ID,
        enabled=True,
        config_payload=payload,
        now=now,
    )

    assert state.enabled is False
    assert state.reason == "wheel_config_invalid"
    assert tuple(state.sectors) == ()
    assert "reward_wheel_config_invalid" in caplog.text
    assert "preset=paid_weekly_v1" in caplog.text
    assert "validation_code=wheel_weights_invalid" in caplog.text
    assert "8999" not in caplog.text
    assert "must-never-enter-log" not in caplog.text


def test_two_serialized_sqlite_sessions_create_one_wheel_grant_and_job(
    serialized_reward_database,
    now,
) -> None:
    from rewards_service import PAID_WEEKLY_V1, RewardConflict, spin_wheel

    Session, write_lock = serialized_reward_database
    barrier = threading.Barrier(2)

    def _attempt_spin() -> tuple[str, int | str]:
        barrier.wait(timeout=5)
        with write_lock:
            with Session() as session:
                try:
                    result = spin_wheel(
                        session,
                        account_id=PAID_ACCOUNT_ID,
                        enabled=True,
                        config_payload=PAID_WEEKLY_V1,
                        now=now,
                        randbelow=lambda _upper: 0,
                    )
                except RewardConflict as exc:
                    session.rollback()
                    return "conflict", exc.code
                session.commit()
                return "winner", result.reward_days

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: _attempt_spin(), range(2)))

    assert sorted(results) == [("conflict", "wheel_cooldown_active"), ("winner", 1)]
    with Session() as verification:
        assert verification.query(EntitlementGrant).filter_by(source="bonus_wheel").count() == 1
        assert (
            verification.query(NodeProvisioningJob)
            .filter_by(job_type="reward_entitlement_sync")
            .count()
            == 1
        )
        state = verification.get(RewardAccountState, PAID_ACCOUNT_ID)
        assert state is not None
        assert state.wheel_last_spin_at == now

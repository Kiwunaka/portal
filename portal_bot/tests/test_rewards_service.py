from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from models import Account, Base, EntitlementGrant, NodeProvisioningJob, User


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

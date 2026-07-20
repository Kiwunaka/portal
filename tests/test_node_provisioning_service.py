from __future__ import annotations

import json
import asyncio
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


GIB = 1024**3
NOW = datetime(2026, 7, 13, 14, 0, 0)


@pytest.fixture()
def database(tmp_path):
    from models import Base

    engine = create_engine(f"sqlite:///{(tmp_path / 'provisioning.db').as_posix()}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield Session
    finally:
        engine.dispose()


def _seed_nodes(session, *, include_soft: bool = True) -> None:
    from models import Node

    rows = [
        Node(
            code="nl-free-standard",
            name="NL Free Standard",
            host="nl-free.test",
            panel_base_url="https://nl-free.test:8444",
            panel_path="panel",
            panel_user="user",
            panel_pass="pass",
            inbound_id=41,
            access_role="free_standard",
            enabled=True,
        ),
        Node(
            code="nl-paid",
            name="NL Paid",
            host="nl-free.test",
            panel_base_url="https://nl-free.test:8444",
            panel_path="panel",
            panel_user="user",
            panel_pass="pass",
            inbound_id=43,
            access_role="paid",
            enabled=True,
        ),
        Node(
            code="nl-lab",
            name="NL Lab",
            host="nl-free.test",
            panel_base_url="https://nl-free.test:8444",
            panel_path="panel",
            panel_user="user",
            panel_pass="pass",
            inbound_id=44,
            access_role="operator_lab",
            enabled=True,
        ),
    ]
    if include_soft:
        rows.append(
            Node(
                code="nl-free-soft",
                name="NL Free Soft",
                host="nl-free.test",
                panel_base_url="https://nl-free.test:8444",
                panel_path="panel",
                panel_user="user",
                panel_pass="pass",
                inbound_id=42,
                access_role="free_soft",
                enabled=True,
            )
        )
    session.add_all(rows)


def _seed_user(session, *, tg_id: int = 2001, profile_state: str = "standard"):
    from models import AccessKey, User

    active_role = "free_soft" if profile_state in {"soft_active", "reset_pending"} else "free_standard"
    node_code = "nl-free-soft" if active_role == "free_soft" else "nl-free-standard"
    user = User(
        tg_id=tg_id,
        uuid=str(uuid.uuid4()),
        email=f"user-{tg_id}@example.test",
        sub_token=f"sub-{tg_id}",
        sub_type="FREE",
        current_plan_code="free_monthly",
        is_active=True,
        expiry_at=NOW + timedelta(days=365),
        free_cycle_anchor_at=NOW - timedelta(days=30),
        free_cycle_last_reset_at=NOW - timedelta(days=30),
        free_cycle_next_reset_at=NOW,
        free_profile_state=profile_state,
        free_profile_active_role=active_role,
        free_profile_source="test",
        free_profile_state_changed_at=NOW - timedelta(days=1),
    )
    session.add(user)
    session.flush()
    key = AccessKey(
        tg_id=tg_id,
        key_uuid=user.uuid,
        panel_email=user.email,
        node_code=node_code,
        pool_code="free_pool",
        state="active",
        source="test",
        is_primary=True,
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(key)
    session.flush()
    return user, key


class FakePanel:
    def __init__(self) -> None:
        self.events: list[tuple] = []
        self.ensure_results: list[object] = []
        self.confirm_results: list[object] = []
        self.disable_results: list[object] = []
        self.reset_results: list[object] = []
        self.rotate_results: list[object] = []
        self.traffic_results: list[object] = []

    @staticmethod
    def _take(values: list[object], default: bool = True):
        result = values.pop(0) if values else default
        if isinstance(result, BaseException):
            raise result
        return result

    async def ensure_user_profile_on_node(self, **kwargs):
        self.events.append(
            (
                "ensure",
                kwargs["node_code"],
                kwargs["expected_access_role"],
                kwargs["total_bytes"],
                kwargs["limit_ip"],
            )
        )
        return self._take(self.ensure_results)

    async def confirm_user_profile_on_node(self, **kwargs):
        self.events.append(
            (
                "confirm",
                kwargs["node_code"],
                kwargs["expected_access_role"],
                kwargs["total_bytes"],
                kwargs["limit_ip"],
            )
        )
        return self._take(self.confirm_results)

    async def set_user_profile_enabled_on_node(self, **kwargs):
        self.events.append(("disable", kwargs["node_code"], kwargs["expected_access_role"], kwargs["enable"]))
        return self._take(self.disable_results)

    async def reset_user_profile_traffic_on_node(self, **kwargs):
        self.events.append(("reset", kwargs["node_code"], kwargs["expected_access_role"]))
        return self._take(self.reset_results)

    async def rotate_user_key_on_node(self, **kwargs):
        self.events.append(("rotate", kwargs["node_code"], kwargs["new_key_uuid"]))
        return self._take(self.rotate_results)

    async def update_client_traffic(self, tg_id: int, add_gb: int):
        self.events.append(("traffic", int(tg_id), int(add_gb)))
        return self._take(self.traffic_results)

    async def close(self):
        self.events.append(("close",))


async def _run(database, panel: FakePanel, *, now: datetime | None = NOW, max_attempts: int = 3):
    from node_provisioning_service import process_node_provisioning_jobs

    return await process_node_provisioning_jobs(
        database,
        panel_factory=lambda: panel,
        now=now,
        limit=10,
        max_attempts=max_attempts,
        stale_after_seconds=60,
    )


def _seed_reward_job(
    session,
    *,
    account_id: str = "00000000-0000-4000-8000-000000000401",
    tg_ids: tuple[int, ...] = (4101,),
):
    from models import Account, EntitlementGrant, User
    from node_provisioning_service import enqueue_reward_entitlement_sync

    grant_id = "00000000-0000-4000-8000-000000000402"
    session.add(
        Account(
            id=account_id,
            status="active",
            created_source="test",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    for tg_id in tg_ids:
        session.add(
            User(
                tg_id=tg_id,
                account_id=account_id,
                uuid=str(uuid.uuid4()),
                sub_type="PAID",
                current_plan_code="month",
                is_active=True,
                expiry_at=NOW + timedelta(days=30),
            )
        )
    grant = EntitlementGrant(
        id=grant_id,
        account_id=account_id,
        legacy_tg_id=tg_ids[0] if tg_ids else None,
        idempotency_key="reward-wheel:v1:worker-test",
        source="bonus_wheel",
        status="active",
        grant_kind="premium_bonus",
        plan_code="reward_wheel",
        starts_at=NOW,
        expires_at=NOW + timedelta(days=1),
        activated_at=NOW,
        duration_days=1,
        provider="internal_economy",
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(grant)
    session.flush()
    job = enqueue_reward_entitlement_sync(
        session,
        account_id=account_id,
        entitlement_grant_id=grant.id,
        now=NOW,
    )
    return grant, job


def test_reward_sync_enqueue_rejects_missing_and_nonreward_grants(database) -> None:
    from models import EntitlementGrant
    from node_provisioning_service import (
        ProvisioningError,
        enqueue_reward_entitlement_sync,
    )

    with database() as session:
        with pytest.raises(ProvisioningError, match="reward_sync_grant_invalid"):
            enqueue_reward_entitlement_sync(
                session,
                account_id="00000000-0000-4000-8000-000000000301",
                entitlement_grant_id="00000000-0000-4000-8000-000000000302",
                now=NOW,
            )

        grant = EntitlementGrant(
            id="00000000-0000-4000-8000-000000000303",
            account_id="00000000-0000-4000-8000-000000000301",
            idempotency_key="provider:v1:nonreward",
            source="provider_payment",
            status="active",
            grant_kind="paid_access",
            plan_code="month",
            starts_at=NOW,
            expires_at=NOW + timedelta(days=30),
            duration_days=30,
            created_at=NOW,
            updated_at=NOW,
        )
        session.add(grant)
        session.flush()

        with pytest.raises(ProvisioningError, match="reward_sync_grant_invalid"):
            enqueue_reward_entitlement_sync(
                session,
                account_id=grant.account_id,
                entitlement_grant_id=grant.id,
                now=NOW,
            )


def test_reward_sync_enqueue_rejects_idempotency_conflict(database) -> None:
    from models import EntitlementGrant, NodeProvisioningJob
    from node_provisioning_service import (
        ProvisioningError,
        enqueue_reward_entitlement_sync,
    )

    account_id = "00000000-0000-4000-8000-000000000311"
    grant_id = "00000000-0000-4000-8000-000000000312"
    with database() as session:
        session.add(
            EntitlementGrant(
                id=grant_id,
                account_id=account_id,
                idempotency_key="reward-wheel:v1:conflict",
                source="bonus_wheel",
                status="active",
                grant_kind="premium_bonus",
                plan_code="reward_wheel",
                starts_at=NOW,
                expires_at=NOW + timedelta(days=1),
                duration_days=1,
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.add(
            NodeProvisioningJob(
                account_id=account_id,
                entitlement_grant_id="00000000-0000-4000-8000-000000000313",
                job_type="reward_entitlement_sync",
                status="queued",
                idempotency_key=f"reward-entitlement-sync:v1:{grant_id}",
                attempts=0,
                next_run_at=NOW,
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.flush()

        with pytest.raises(ProvisioningError, match="reward_sync_idempotency_conflict"):
            enqueue_reward_entitlement_sync(
                session,
                account_id=account_id,
                entitlement_grant_id=grant_id,
                now=NOW,
            )


def test_reward_sync_worker_updates_every_active_account_alias_once(database) -> None:
    from models import NodeProvisioningJob, User
    from rewards_service import reward_sync_state

    with database() as session:
        _seed_reward_job(session, tg_ids=(4101, 4102))
        session.add(
            User(
                tg_id=4103,
                account_id="00000000-0000-4000-8000-000000000401",
                uuid=str(uuid.uuid4()),
                sub_type="PAID",
                current_plan_code="month",
                is_active=False,
                expiry_at=NOW + timedelta(days=30),
            )
        )
        session.commit()

    panel = FakePanel()
    result = asyncio.run(_run(database, panel))

    assert result["claimed"] == result["succeeded"] == 1
    assert panel.events == [
        ("traffic", 4101, 0),
        ("traffic", 4102, 0),
        ("close",),
    ]
    with database() as session:
        job = session.query(NodeProvisioningJob).one()
        assert job.status == "completed"
        assert job.completed_at == NOW
        assert reward_sync_state(job) == "synced"


@pytest.mark.parametrize("failure", (False, RuntimeError("must-not-be-persisted")))
def test_reward_sync_failure_retries_with_backoff_then_enters_manual_review(
    database,
    failure,
) -> None:
    from models import NodeProvisioningJob

    with database() as session:
        _seed_reward_job(session)
        session.commit()

    panel = FakePanel()
    panel.traffic_results = [failure, failure]
    first = asyncio.run(_run(database, panel, max_attempts=2))
    with database() as session:
        job = session.query(NodeProvisioningJob).one()
        retry_at = job.next_run_at
        assert first["retried"] == 1
        assert job.status == "queued"
        assert job.attempts == 1
        assert retry_at == NOW + timedelta(seconds=15)
        assert job.last_error_code == "reward_sync_failed"

    second = asyncio.run(_run(database, panel, now=retry_at, max_attempts=2))
    assert second["manual_review"] == 1
    with database() as session:
        job = session.query(NodeProvisioningJob).one()
        assert job.status == "manual_review"
        assert job.attempts == 2
        assert job.next_run_at is None
        assert job.lock_token is None
        assert job.last_error_code == "reward_sync_failed"
        assert "must-not-be-persisted" not in str(job.result_json)


def test_reward_sync_finalize_requires_same_token_and_canonical_account(database) -> None:
    from models import Account, NodeProvisioningJob
    from node_provisioning_service import (
        _claim_next_job,
        _finalize_success,
        _prepare_job,
    )

    target_account_id = "00000000-0000-4000-8000-000000000409"
    with database() as session:
        _grant, seeded_reward_job = _seed_reward_job(session)
        session.add(
            Account(
                id=target_account_id,
                status="active",
                created_source="test",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.flush()
        claim = _claim_next_job(session, now=NOW, max_attempts=3)
        assert claim is not None
        prepared = _prepare_job(session, claim)
        assert prepared.account_id == seeded_reward_job.account_id
        assert prepared.reward_tg_ids == (4101,)
        assert prepared.client_uuid == prepared.panel_email == prepared.sub_id == ""

        seeded_reward_job.account_id = target_account_id
        seeded_reward_job.status = "queued"
        seeded_reward_job.lock_token = None
        seeded_reward_job.locked_at = None
        session.flush()

        assert (
            _finalize_success(
                session,
                claim=claim,
                prepared=prepared,
                outcome="synced",
                now=NOW,
            )
            == "claim_lost"
        )
        persisted = session.query(NodeProvisioningJob).one()
        assert persisted.completed_at is None


def test_reward_sync_checks_ownership_before_first_call_and_each_alias(database) -> None:
    from node_provisioning_service import PreparedJob, _execute_panel

    prepared = PreparedJob(
        job_id=1,
        job_type="reward_entitlement_sync",
        account_id="00000000-0000-4000-8000-000000000401",
        entitlement_grant_id="00000000-0000-4000-8000-000000000402",
        reward_tg_ids=(4101, 4102),
    )
    checks = iter((False, False, True))
    panel = FakePanel()

    outcome = asyncio.run(
        _execute_panel(
            prepared,
            panel,
            superseded_check=lambda: next(checks),
        )
    )

    assert outcome == "superseded"
    assert panel.events == [("traffic", 4101, 0)]


def test_free_to_soft_confirms_target_before_disabling_standard_and_replay_is_idempotent(database) -> None:
    from free_cycle_service import reconcile_free_profile_usage
    from models import AccessKey, NodeProvisioningJob, User

    with database() as session:
        _seed_nodes(session)
        user, _key = _seed_user(session)
        reconcile_free_profile_usage(session, user=user, used_bytes=5 * GIB, source="node_observer", now=NOW)
        session.commit()

    panel = FakePanel()
    first = asyncio.run(_run(database, panel))
    replay = asyncio.run(_run(database, panel, now=NOW + timedelta(hours=1)))

    assert first["succeeded"] == 1
    assert replay["claimed"] == 0
    assert panel.events == [
        ("ensure", "nl-free-soft", "free_soft", 0, 1),
        ("confirm", "nl-free-soft", "free_soft", 0, 1),
        ("disable", "nl-free-standard", "free_standard", False),
        ("close",),
    ]
    with database() as session:
        user = session.query(User).filter_by(tg_id=2001).one()
        key = session.query(AccessKey).filter_by(tg_id=2001).one()
        job = session.query(NodeProvisioningJob).one()
        assert user.free_profile_state == "soft_active"
        assert user.free_profile_active_role == "free_soft"
        assert key.node_code == "nl-free-soft"
        assert job.status == "succeeded"
        assert job.completed_at == NOW


def test_partial_target_confirmation_retries_without_premature_soft_state(database) -> None:
    from free_cycle_service import reconcile_free_profile_usage
    from models import NodeProvisioningJob, User

    with database() as session:
        _seed_nodes(session)
        user, _key = _seed_user(session)
        reconcile_free_profile_usage(session, user=user, used_bytes=5 * GIB, source="node_observer", now=NOW)
        session.commit()

    panel = FakePanel()
    panel.confirm_results = [False, True]
    failed = asyncio.run(_run(database, panel))
    with database() as session:
        user = session.query(User).filter_by(tg_id=2001).one()
        job = session.query(NodeProvisioningJob).one()
        retry_at = job.next_run_at
        assert failed["retried"] == 1
        assert user.free_profile_state == "error"
        assert user.free_profile_active_role == "free_standard"
        assert job.status == "queued"
        assert job.attempts == 1
        assert retry_at > NOW

    recovered = asyncio.run(_run(database, panel, now=retry_at))
    assert recovered["succeeded"] == 1
    assert [event[0] for event in panel.events] == ["ensure", "confirm", "close", "ensure", "confirm", "disable", "close"]


def test_reset_ensures_limited_standard_resets_traffic_then_disables_soft(database) -> None:
    from free_cycle_service import queue_free_profile_reset
    from models import NodeProvisioningJob, User

    with database() as session:
        _seed_nodes(session)
        user, _key = _seed_user(session, profile_state="soft_active")
        queued = queue_free_profile_reset(session, user=user, source="cycle_due", now=NOW)
        session.commit()
        assert queued["queued"] is True

    panel = FakePanel()
    result = asyncio.run(_run(database, panel))
    assert result["succeeded"] == 1
    assert panel.events == [
        ("ensure", "nl-free-standard", "free_standard", 5 * GIB, 1),
        ("confirm", "nl-free-standard", "free_standard", 5 * GIB, 1),
        ("reset", "nl-free-standard", "free_standard"),
        ("disable", "nl-free-soft", "free_soft", False),
        ("close",),
    ]
    with database() as session:
        user = session.query(User).filter_by(tg_id=2001).one()
        job = session.query(NodeProvisioningJob).one()
        assert user.free_profile_state == "standard"
        assert user.free_profile_active_role == "free_standard"
        assert user.free_cycle_last_reset_at == NOW
        assert user.free_cycle_next_reset_at == NOW + timedelta(days=30)
        assert job.status == "succeeded"


def test_delayed_reset_starts_a_full_thirty_day_cycle_from_confirmation(database) -> None:
    from free_cycle_service import queue_free_profile_reset
    from models import User

    with database() as session:
        _seed_nodes(session)
        user, _key = _seed_user(session, profile_state="soft_active")
        queue_free_profile_reset(session, user=user, source="cycle_due", now=NOW)
        session.commit()

    confirmed_at = NOW + timedelta(days=5)
    result = asyncio.run(_run(database, FakePanel(), now=confirmed_at))

    assert result["succeeded"] == 1
    with database() as session:
        user = session.query(User).filter_by(tg_id=2001).one()
        assert user.free_cycle_last_reset_at == confirmed_at
        assert user.free_cycle_next_reset_at == confirmed_at + timedelta(days=30)


def test_runtime_reset_uses_panel_completion_time(database, monkeypatch) -> None:
    import node_provisioning_service as service
    from free_cycle_service import queue_free_profile_reset
    from models import User

    with database() as session:
        _seed_nodes(session)
        user, _key = _seed_user(session, profile_state="soft_active")
        queue_free_profile_reset(session, user=user, source="cycle_due", now=NOW)
        session.commit()

    completed_at = NOW + timedelta(minutes=5)
    clock = iter((NOW, completed_at))
    monkeypatch.setattr(service, "_utcnow", lambda: next(clock))

    result = asyncio.run(_run(database, FakePanel(), now=None))

    assert result["succeeded"] == 1
    with database() as session:
        user = session.query(User).filter_by(tg_id=2001).one()
        assert user.free_cycle_last_reset_at == completed_at
        assert user.free_cycle_next_reset_at == completed_at + timedelta(days=30)


def test_paid_reentry_confirms_standard_before_disabling_paid_and_soft_sources(database) -> None:
    from free_cycle_service import queue_free_profile_reentry
    from models import AccessKey, NodeProvisioningJob, User

    with database() as session:
        _seed_nodes(session)
        user, key = _seed_user(session, profile_state="soft_active")
        user.sub_type = "PAID"
        user.current_plan_code = "paid_30d"
        key.node_code = "nl-paid"
        key.pool_code = "premium_pool"
        queued = queue_free_profile_reentry(session, user=user, source="paid_expired", now=NOW)
        session.commit()
        assert queued["queued"] is True

    panel = FakePanel()
    result = asyncio.run(_run(database, panel))

    assert result["succeeded"] == 1
    assert panel.events == [
        ("ensure", "nl-free-standard", "free_standard", 5 * GIB, 1),
        ("confirm", "nl-free-standard", "free_standard", 5 * GIB, 1),
        ("reset", "nl-free-standard", "free_standard"),
        ("disable", "nl-free-soft", "free_soft", False),
        ("disable", "nl-paid", "paid", False),
        ("close",),
    ]
    with database() as session:
        user = session.query(User).filter_by(tg_id=2001).one()
        key = session.query(AccessKey).filter_by(tg_id=2001).one()
        job = session.query(NodeProvisioningJob).one()
        assert user.sub_type == "FREE"
        assert user.current_plan_code == "free_monthly"
        assert user.free_profile_state == "standard"
        assert user.free_profile_active_role == "free_standard"
        assert key.node_code == "nl-free-standard"
        assert key.pool_code == "free_pool"
        assert job.status == "succeeded"


def test_repeated_free_reentry_reuses_pending_job_and_cycle_marker(database) -> None:
    from free_cycle_service import queue_free_profile_reentry
    from models import NodeProvisioningJob

    with database() as session:
        _seed_nodes(session)
        user, key = _seed_user(session, profile_state="soft_active")
        user.sub_type = "PAID"
        user.current_plan_code = "paid_30d"
        key.node_code = "nl-paid"
        key.pool_code = "premium_pool"

        first = queue_free_profile_reentry(session, user=user, source="paid_expired", now=NOW)
        first_anchor = user.free_cycle_anchor_at
        replay = queue_free_profile_reentry(
            session,
            user=user,
            source="paid_expired_replay",
            now=NOW + timedelta(seconds=10),
        )
        session.commit()

        assert first["queued"] is True
        assert replay["queued"] is False
        assert replay["job_id"] == first["job_id"]
        assert user.free_cycle_anchor_at == first_anchor
        assert session.query(NodeProvisioningJob).filter_by(tg_id=2001, job_type="free_to_standard").count() == 1


def test_missing_soft_role_never_uses_paid_or_lab_as_fallback(database) -> None:
    from free_cycle_service import reconcile_free_profile_usage
    from models import NodeProvisioningJob, User

    with database() as session:
        _seed_nodes(session, include_soft=False)
        user, _key = _seed_user(session)
        reconcile_free_profile_usage(session, user=user, used_bytes=5 * GIB, source="node_observer", now=NOW)
        session.commit()

    panel = FakePanel()
    result = asyncio.run(_run(database, panel))
    assert result["retried"] == 1
    assert panel.events == [("close",)]
    with database() as session:
        user = session.query(User).filter_by(tg_id=2001).one()
        job = session.query(NodeProvisioningJob).one()
        assert user.free_profile_state == "error"
        assert user.free_profile_active_role == "free_standard"
        assert job.last_error_code == "free_soft_role_missing"


def test_stale_terminal_job_moves_to_manual_review_without_panel_call(database) -> None:
    from models import NodeProvisioningJob

    with database() as session:
        session.add(
            NodeProvisioningJob(
                tg_id=3001,
                job_type="free_to_soft",
                status="running",
                attempts=3,
                locked_at=NOW - timedelta(minutes=5),
                lock_token="dead-worker",
                created_at=NOW - timedelta(days=1),
                updated_at=NOW - timedelta(minutes=5),
            )
        )
        session.commit()

    panel = FakePanel()
    result = asyncio.run(_run(database, panel, max_attempts=3))
    assert result["manual_review"] == 1
    assert panel.events == []
    with database() as session:
        job = session.query(NodeProvisioningJob).one()
        assert job.status == "manual_review"
        assert job.manual_review_at == NOW
        assert job.locked_at is None
        assert job.lock_token is None


def test_exception_result_is_redacted_and_becomes_bounded_manual_review(database) -> None:
    from free_cycle_service import reconcile_free_profile_usage
    from models import NodeProvisioningJob

    raw_secret = "00000000-0000-4000-8000-secret-user@example.test"
    with database() as session:
        _seed_nodes(session)
        user, _key = _seed_user(session)
        reconcile_free_profile_usage(session, user=user, used_bytes=5 * GIB, source="node_observer", now=NOW)
        session.commit()

    panel = FakePanel()
    panel.ensure_results = [RuntimeError(raw_secret)]
    result = asyncio.run(_run(database, panel, max_attempts=1))
    assert result["manual_review"] == 1
    with database() as session:
        job = session.query(NodeProvisioningJob).one()
        serialized = json.dumps({"result": job.result_json, "error": job.last_error_code})
        assert raw_secret not in serialized
        assert "example.test" not in serialized
        assert job.last_error_code == "panel_exception"
        assert job.status == "manual_review"


def test_existing_rotate_access_key_job_is_executed_once(database) -> None:
    from models import AccessKey, NodeProvisioningJob

    with database() as session:
        _seed_nodes(session)
        user, key = _seed_user(session)
        old_uuid = key.key_uuid
        key.state = "rotation_requested"
        session.add(
            NodeProvisioningJob(
                tg_id=user.tg_id,
                key_id=key.id,
                node_code=key.node_code,
                job_type="rotate_access_key",
                status="queued",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.commit()

    panel = FakePanel()
    first = asyncio.run(_run(database, panel))
    second = asyncio.run(_run(database, panel, now=NOW + timedelta(hours=1)))
    assert first["succeeded"] == 1
    assert second["claimed"] == 0
    assert [event[0] for event in panel.events] == ["rotate", "close"]
    with database() as session:
        key = session.query(AccessKey).one()
        job = session.query(NodeProvisioningJob).one()
        assert key.key_uuid != old_uuid
        assert key.key_uuid == panel.events[0][2]
        assert key.state == "active"
        assert key.rotated_at == NOW
        assert job.replacement_key_uuid is None
        assert job.status == "succeeded"


def test_payment_race_does_not_reproject_paid_user_or_key_to_free_soft(database) -> None:
    from free_cycle_service import reconcile_free_profile_usage
    from models import AccessKey, NodeProvisioningJob, User

    with database() as session:
        _seed_nodes(session)
        user, _key = _seed_user(session)
        reconcile_free_profile_usage(session, user=user, used_bytes=5 * GIB, source="node_observer", now=NOW)
        session.commit()

    class PaymentRacePanel(FakePanel):
        async def set_user_profile_enabled_on_node(self, **kwargs):
            result = await super().set_user_profile_enabled_on_node(**kwargs)
            with database() as session:
                user = session.query(User).filter_by(tg_id=2001).one()
                key = session.query(AccessKey).filter_by(tg_id=2001).one()
                user.sub_type = "PAID"
                user.current_plan_code = "paid_30d"
                key.node_code = "paid-main"
                key.pool_code = "premium_pool"
                session.commit()
            return result

    panel = PaymentRacePanel()
    result = asyncio.run(_run(database, panel))

    assert result["succeeded"] == 1
    assert panel.events == [
        ("ensure", "nl-free-soft", "free_soft", 0, 1),
        ("confirm", "nl-free-soft", "free_soft", 0, 1),
        ("disable", "nl-free-standard", "free_standard", False),
        ("disable", "nl-free-soft", "free_soft", False),
        ("disable", "nl-free-standard", "free_standard", True),
        ("close",),
    ]
    with database() as session:
        user = session.query(User).filter_by(tg_id=2001).one()
        key = session.query(AccessKey).filter_by(tg_id=2001).one()
        job = session.query(NodeProvisioningJob).one()
        assert user.sub_type == "PAID"
        assert user.current_plan_code == "paid_30d"
        assert key.node_code == "paid-main"
        assert key.pool_code == "premium_pool"
        assert job.status == "succeeded"
        assert json.loads(job.result_json)["code"] == "superseded"


def test_payment_after_final_panel_check_is_compensated(database, monkeypatch) -> None:
    import node_provisioning_service as service
    from free_cycle_service import reconcile_free_profile_usage
    from models import AccessKey, NodeProvisioningJob, User

    with database() as session:
        _seed_nodes(session)
        user, _key = _seed_user(session)
        reconcile_free_profile_usage(session, user=user, used_bytes=5 * GIB, source="node_observer", now=NOW)
        session.commit()

    original_execute = service._execute_panel

    async def execute_then_pay(prepared, panel, **kwargs):
        outcome = await original_execute(prepared, panel, **kwargs)
        with database() as session:
            user = session.query(User).filter_by(tg_id=2001).one()
            key = session.query(AccessKey).filter_by(tg_id=2001).one()
            user.sub_type = "PAID"
            user.current_plan_code = "paid_30d"
            key.node_code = "nl-paid"
            key.pool_code = "premium_pool"
            session.commit()
        return outcome

    monkeypatch.setattr(service, "_execute_panel", execute_then_pay)
    panel = FakePanel()
    result = asyncio.run(_run(database, panel))

    assert result["succeeded"] == 1
    assert panel.events == [
        ("ensure", "nl-free-soft", "free_soft", 0, 1),
        ("confirm", "nl-free-soft", "free_soft", 0, 1),
        ("disable", "nl-free-standard", "free_standard", False),
        ("disable", "nl-free-soft", "free_soft", False),
        ("disable", "nl-free-standard", "free_standard", True),
        ("close",),
    ]
    with database() as session:
        job = session.query(NodeProvisioningJob).one()
        assert json.loads(job.result_json)["code"] == "superseded"


def test_failed_post_finalize_compensation_is_manual_review(database, monkeypatch) -> None:
    import node_provisioning_service as service
    from free_cycle_service import reconcile_free_profile_usage
    from models import AccessKey, NodeProvisioningJob, User

    with database() as session:
        _seed_nodes(session)
        user, _key = _seed_user(session)
        reconcile_free_profile_usage(session, user=user, used_bytes=5 * GIB, source="node_observer", now=NOW)
        session.commit()

    original_execute = service._execute_panel

    async def execute_then_pay(prepared, panel, **kwargs):
        outcome = await original_execute(prepared, panel, **kwargs)
        with database() as session:
            user = session.query(User).filter_by(tg_id=2001).one()
            key = session.query(AccessKey).filter_by(tg_id=2001).one()
            user.sub_type = "PAID"
            user.current_plan_code = "paid_30d"
            key.node_code = "nl-paid"
            key.pool_code = "premium_pool"
            session.commit()
        return outcome

    monkeypatch.setattr(service, "_execute_panel", execute_then_pay)
    panel = FakePanel()
    panel.disable_results = [True, False, True]
    result = asyncio.run(_run(database, panel))

    assert result["succeeded"] == 0
    assert result["manual_review"] == 1
    with database() as session:
        job = session.query(NodeProvisioningJob).one()
        assert job.status == "manual_review"
        assert job.last_error_code == "superseded_target_disable_failed"


def test_payment_race_during_free_reentry_restores_paid_profile(database) -> None:
    from free_cycle_service import queue_free_profile_reentry
    from models import AccessKey, NodeProvisioningJob, User

    with database() as session:
        _seed_nodes(session)
        user, key = _seed_user(session, profile_state="soft_active")
        user.sub_type = "PAID"
        user.current_plan_code = "paid_30d"
        key.node_code = "nl-paid"
        key.pool_code = "premium_pool"
        queue_free_profile_reentry(session, user=user, source="paid_expired", now=NOW)
        session.commit()

    class PaymentRacePanel(FakePanel):
        async def set_user_profile_enabled_on_node(self, **kwargs):
            result = await super().set_user_profile_enabled_on_node(**kwargs)
            if kwargs["node_code"] == "nl-paid" and kwargs["enable"] is False:
                with database() as session:
                    user = session.query(User).filter_by(tg_id=2001).one()
                    key = session.query(AccessKey).filter_by(tg_id=2001).one()
                    user.sub_type = "PAID"
                    user.current_plan_code = "paid_30d"
                    key.node_code = "nl-paid"
                    key.pool_code = "premium_pool"
                    session.commit()
            return result

    panel = PaymentRacePanel()
    result = asyncio.run(_run(database, panel))

    assert result["succeeded"] == 1
    assert panel.events == [
        ("ensure", "nl-free-standard", "free_standard", 5 * GIB, 1),
        ("confirm", "nl-free-standard", "free_standard", 5 * GIB, 1),
        ("reset", "nl-free-standard", "free_standard"),
        ("disable", "nl-free-soft", "free_soft", False),
        ("disable", "nl-paid", "paid", False),
        ("disable", "nl-free-standard", "free_standard", False),
        ("disable", "nl-paid", "paid", True),
        ("close",),
    ]
    with database() as session:
        user = session.query(User).filter_by(tg_id=2001).one()
        key = session.query(AccessKey).filter_by(tg_id=2001).one()
        job = session.query(NodeProvisioningJob).one()
        assert user.sub_type == "PAID"
        assert user.current_plan_code == "paid_30d"
        assert key.node_code == "nl-paid"
        assert key.pool_code == "premium_pool"
        assert json.loads(job.result_json)["code"] == "superseded"


def test_failed_payment_race_compensation_requires_manual_review(database) -> None:
    from free_cycle_service import queue_free_profile_reentry
    from models import AccessKey, NodeProvisioningJob, User

    with database() as session:
        _seed_nodes(session)
        user, key = _seed_user(session, profile_state="soft_active")
        user.sub_type = "PAID"
        user.current_plan_code = "paid_30d"
        key.node_code = "nl-paid"
        key.pool_code = "premium_pool"
        queue_free_profile_reentry(session, user=user, source="paid_expired", now=NOW)
        session.commit()

    class FailedCompensationPanel(FakePanel):
        def __init__(self) -> None:
            super().__init__()
            self.disable_results = [True, True, False]

        async def set_user_profile_enabled_on_node(self, **kwargs):
            result = await super().set_user_profile_enabled_on_node(**kwargs)
            if kwargs["node_code"] == "nl-paid" and kwargs["enable"] is False:
                with database() as session:
                    user = session.query(User).filter_by(tg_id=2001).one()
                    key = session.query(AccessKey).filter_by(tg_id=2001).one()
                    user.sub_type = "PAID"
                    user.current_plan_code = "paid_30d"
                    key.node_code = "nl-paid"
                    key.pool_code = "premium_pool"
                    session.commit()
            return result

    panel = FailedCompensationPanel()
    result = asyncio.run(_run(database, panel))

    assert result["retried"] == 0
    assert result["manual_review"] == 1
    assert panel.events == [
        ("ensure", "nl-free-standard", "free_standard", 5 * GIB, 1),
        ("confirm", "nl-free-standard", "free_standard", 5 * GIB, 1),
        ("reset", "nl-free-standard", "free_standard"),
        ("disable", "nl-free-soft", "free_soft", False),
        ("disable", "nl-paid", "paid", False),
        ("disable", "nl-free-standard", "free_standard", False),
        ("disable", "nl-paid", "paid", True),
        ("close",),
    ]
    with database() as session:
        job = session.query(NodeProvisioningJob).one()
        assert job.status == "manual_review"
        assert job.last_error_code == "superseded_target_disable_failed"


def test_payment_race_compensation_accepts_one_restored_paid_source(database) -> None:
    from free_cycle_service import queue_free_profile_reentry
    from models import AccessKey, Node, User

    with database() as session:
        _seed_nodes(session)
        session.add(
            Node(
                code="us-paid",
                name="US Paid",
                host="us-paid.test",
                panel_base_url="https://us-paid.test:8444",
                panel_path="panel",
                panel_user="user",
                panel_pass="pass",
                inbound_id=45,
                access_role="paid",
                enabled=True,
            )
        )
        user, key = _seed_user(session, profile_state="soft_active")
        user.sub_type = "PAID"
        user.current_plan_code = "paid_30d"
        key.node_code = "nl-paid"
        key.pool_code = "premium_pool"
        queue_free_profile_reentry(session, user=user, source="paid_expired", now=NOW)
        session.commit()

    class PartialRestorePanel(FakePanel):
        async def set_user_profile_enabled_on_node(self, **kwargs):
            self.events.append(
                ("disable", kwargs["node_code"], kwargs["expected_access_role"], kwargs["enable"])
            )
            if kwargs["node_code"] == "nl-paid" and kwargs["enable"] is False:
                with database() as session:
                    user = session.query(User).filter_by(tg_id=2001).one()
                    key = session.query(AccessKey).filter_by(tg_id=2001).one()
                    user.sub_type = "PAID"
                    user.current_plan_code = "paid_30d"
                    key.node_code = "us-paid"
                    key.pool_code = "premium_pool"
                    session.commit()
            if kwargs["enable"] is True and kwargs["node_code"] == "nl-paid":
                return False
            return True

    result = asyncio.run(_run(database, PartialRestorePanel()))

    assert result["succeeded"] == 1
    assert result["manual_review"] == 0


def test_exhausted_job_does_not_block_next_ready_job(database) -> None:
    from models import AccessKey, NodeProvisioningJob

    with database() as session:
        _seed_nodes(session)
        user, key = _seed_user(session)
        key.state = "rotation_requested"
        session.add_all(
            [
                NodeProvisioningJob(
                    tg_id=9999,
                    job_type="free_to_soft",
                    status="queued",
                    attempts=3,
                    created_at=NOW - timedelta(minutes=1),
                    updated_at=NOW - timedelta(minutes=1),
                ),
                NodeProvisioningJob(
                    tg_id=user.tg_id,
                    key_id=key.id,
                    node_code=key.node_code,
                    job_type="rotate_access_key",
                    status="queued",
                    created_at=NOW,
                    updated_at=NOW,
                ),
            ]
        )
        session.commit()

    panel = FakePanel()
    result = asyncio.run(_run(database, panel, max_attempts=3))

    assert result["manual_review"] == 1
    assert result["succeeded"] == 1
    with database() as session:
        jobs = session.query(NodeProvisioningJob).order_by(NodeProvisioningJob.id.asc()).all()
        assert jobs[0].status == "manual_review"
        assert jobs[1].status == "succeeded"


def test_worker_once_delegates_to_bounded_provisioning_executor(monkeypatch) -> None:
    import worker

    calls: list[dict] = []

    async def fake_process(_session_factory, **kwargs):
        calls.append(kwargs)
        return {"ok": True, "claimed": 2, "succeeded": 2}

    monkeypatch.setattr(worker, "process_node_provisioning_jobs", fake_process)
    result = asyncio.run(worker.node_provisioning_once())

    assert result["succeeded"] == 2
    assert calls[0]["limit"] <= 100
    assert calls[0]["max_attempts"] >= 1
    assert calls[0]["stale_after_seconds"] >= 30

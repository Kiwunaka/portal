from __future__ import annotations

import json
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))


def test_free_tier_is_fail_closed_but_bounded_trial_stays_premium(monkeypatch) -> None:
    import node_policy

    monkeypatch.delenv("FREE_TIER_ENABLED", raising=False)
    now = datetime(2026, 8, 11, 12, 0, 0)
    free_node = SimpleNamespace(
        code="free",
        access_role="free_standard",
        enabled=True,
        accepting_new_clients=True,
        is_draining=False,
    )
    trial_user = SimpleNamespace(
        sub_type="FREE",
        current_plan_code="trial",
        is_active=True,
        expiry_at=now + timedelta(days=5),
    )
    retired_user = SimpleNamespace(
        sub_type="FREE",
        current_plan_code="free_monthly",
        is_active=True,
        expiry_at=now + timedelta(days=30),
    )

    assert node_policy.free_tier_enabled() is False
    assert node_policy.canonical_free_node_code([free_node]) is None
    assert node_policy.free_pool_node_codes([free_node]) == []
    assert node_policy.user_uses_free_pool(trial_user, now=now) is False
    assert node_policy.user_uses_free_pool(retired_user, now=now) is True


def test_retired_free_projection_keeps_account_but_expires_access(monkeypatch) -> None:
    import free_cycle_service

    monkeypatch.delenv("FREE_TIER_ENABLED", raising=False)
    now = datetime(2026, 8, 11, 12, 0, 0)
    user = SimpleNamespace(
        sub_type="PAID",
        current_plan_code="1_month",
        expiry_at=now + timedelta(days=30),
        is_active=True,
        free_cycle_next_reset_at=now + timedelta(days=60),
        free_profile_state="standard",
        free_profile_source="test",
        free_profile_state_changed_at=None,
        free_profile_job_id=17,
        free_profile_error_code="retry",
    )

    free_cycle_service.project_user_to_expired(user, now=now, source="test_retirement")

    assert user.sub_type == "FREE"
    assert user.current_plan_code == "free_retired"
    assert user.expiry_at == now
    assert user.is_active is True
    assert user.free_cycle_next_reset_at is None
    assert user.free_profile_state == "retired"
    assert user.free_profile_job_id is None


def test_shared_access_matrix_publishes_no_post_trial_free_grant() -> None:
    matrix = json.loads((REPO_ROOT / "shared" / "access-matrix.json").read_text(encoding="utf-8"))

    assert matrix["entry_flows"]["store_install"]["downgrade_state"] == "expired_or_blocked"
    assert matrix["entry_flows"]["site_email_signup"]["grant_state"] == "expired_or_blocked"
    assert matrix["free_tier"]["enabled"] is False
    assert matrix["free_tier"]["status"] == "retired_pending_replacement"


def test_provisioning_worker_cancels_queued_free_job_without_panel(monkeypatch, tmp_path) -> None:
    import node_provisioning_service
    from models import Base, NodeProvisioningJob

    monkeypatch.delenv("FREE_TIER_ENABLED", raising=False)
    engine = create_engine(f"sqlite:///{(tmp_path / 'retired-free-jobs.db').as_posix()}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as session:
        session.add(
            NodeProvisioningJob(
                tg_id=1001,
                job_type="free_to_standard",
                status="queued",
                idempotency_key="retired-free-job",
                created_at=datetime(2026, 8, 11, 12, 0, 0),
                updated_at=datetime(2026, 8, 11, 12, 0, 0),
            )
        )
        session.commit()

    class ForbiddenPanel:
        def __init__(self) -> None:
            raise AssertionError("free-tier retirement must not call the panel worker")

    result = asyncio.run(
        node_provisioning_service.process_node_provisioning_jobs(
            Session,
            panel_factory=ForbiddenPanel,
            now=datetime(2026, 8, 11, 12, 1, 0),
            limit=5,
        )
    )

    with Session() as session:
        job = session.query(NodeProvisioningJob).one()
        assert job.status == "cancelled"
        assert job.last_error_code == "free_tier_disabled"
    assert result["claimed"] == 0
    engine.dispose()

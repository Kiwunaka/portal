from __future__ import annotations

import importlib
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker


GIB = 1024**3
NOW = datetime(2026, 7, 13, 12, 0, 0)
PORTAL_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))


def _node(
    code: str,
    role: str,
    inbound_id: int,
    *,
    panel_base_url: str = "https://nl-free.test:8444",
):
    observed_at = datetime.now()
    return SimpleNamespace(
        code=code,
        access_role=role,
        inbound_id=inbound_id,
        panel_base_url=panel_base_url,
        panel_path="panel",
        enabled=True,
        accepting_new_clients=True,
        is_draining=False,
        is_healthy=True,
        health_score=100.0,
        last_health_at=observed_at,
        last_probe_at=observed_at,
        last_authenticated_egress_at=observed_at,
        authenticated_egress_ok=True,
    )


@pytest.fixture()
def session(monkeypatch):
    # The consumer free tier is retired in production. These tests exercise the
    # explicitly opt-in rollback implementation only.
    monkeypatch.setenv("FREE_TIER_ENABLED", "true")
    from models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture()
def api_module(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'api.db').as_posix()}")
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("ADMIN_ID", "9999")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "test-session-secret")
    monkeypatch.setenv("FREE_TIER_ENABLED", "true")
    for module_name in ("config", "db", "api"):
        monkeypatch.delitem(sys.modules, module_name, raising=False)
    module = importlib.import_module("api")
    try:
        yield module
    finally:
        import db

        db.engine.dispose()


def _free_user(*, tg_id: int, plan_code: str = "free_monthly"):
    from models import User

    return User(
        tg_id=tg_id,
        uuid=f"00000000-0000-4000-8000-{tg_id:012d}",
        email=f"user-{tg_id}@example.test",
        sub_token=f"sub-{tg_id}",
        sub_type="FREE",
        current_plan_code=plan_code,
        is_active=True,
        expiry_at=NOW + timedelta(days=365),
        free_cycle_anchor_at=NOW,
        free_cycle_last_reset_at=NOW,
        free_cycle_next_reset_at=NOW + timedelta(days=30),
    )


def test_access_role_validation_requires_distinct_positive_inbounds() -> None:
    from node_policy import NodeAccessRoleError, validate_node_access_roles

    valid = [
        _node("nl-free-standard", "free_standard", 41),
        _node("nl-free-soft", "free_soft", 42),
        _node("nl-paid", "paid", 43),
        _node("nl-lab", "operator_lab", 44),
    ]
    bindings = validate_node_access_roles(valid, require_free_pair=True)
    assert bindings["free_standard"][0].inbound_id == 41
    assert bindings["free_soft"][0].inbound_id == 42

    with pytest.raises(NodeAccessRoleError, match="positive"):
        validate_node_access_roles(
            [_node("nl-free-standard", "free_standard", 0), _node("nl-free-soft", "free_soft", 42)],
            require_free_pair=True,
        )

    with pytest.raises(NodeAccessRoleError, match="duplicate"):
        validate_node_access_roles(
            [_node("nl-free-standard", "free_standard", 42), _node("nl-free-soft", "free_soft", 42)],
            require_free_pair=True,
        )


def test_soft_role_never_falls_back_to_paid_or_operator_lab() -> None:
    from node_policy import NodeAccessRoleError, nodes_for_access_role

    nodes = [_node("nl-paid", "paid", 51), _node("nl-lab", "operator_lab", 52)]
    with pytest.raises(NodeAccessRoleError, match="free_soft"):
        nodes_for_access_role(nodes, "free_soft", required=True)


def test_free_standard_quota_is_exact_binary_five_gib() -> None:
    from free_cycle_service import FREE_STANDARD_QUOTA_BYTES

    assert FREE_STANDARD_QUOTA_BYTES == 5 * GIB


def test_threshold_queues_once_and_persists_pending_state(session) -> None:
    from free_cycle_service import reconcile_free_profile_usage
    from models import NodeProvisioningJob

    user = _free_user(tg_id=1101)
    session.add(user)
    session.flush()

    below = reconcile_free_profile_usage(
        session,
        user=user,
        used_bytes=(5 * GIB) - 1,
        source="node_observer",
        now=NOW,
    )
    assert below["queued"] is False
    assert user.free_profile_state == "standard"

    at_limit = reconcile_free_profile_usage(
        session,
        user=user,
        used_bytes=5 * GIB,
        source="node_observer",
        now=NOW,
    )
    replay = reconcile_free_profile_usage(
        session,
        user=user,
        used_bytes=6 * GIB,
        source="api_runtime",
        now=NOW + timedelta(seconds=1),
    )
    session.flush()

    assert at_limit["queued"] is True
    assert replay["queued"] is False
    assert replay["job_id"] == at_limit["job_id"]
    assert user.free_profile_state == "soft_transition_pending"
    assert user.free_profile_active_role == "free_standard"
    assert user.free_profile_source == "node_observer"
    assert user.free_profile_observed_bytes == 6 * GIB
    assert user.free_profile_observed_at == NOW + timedelta(seconds=1)
    assert session.query(NodeProvisioningJob).filter_by(tg_id=1101, job_type="free_to_soft").count() == 1


@pytest.mark.parametrize(
    ("sub_type", "plan_code"),
    [("PAID", "month"), ("FREE", "trial"), ("FREE", "channel_bonus")],
)
def test_threshold_never_queues_for_paid_or_premium_trial(session, sub_type: str, plan_code: str) -> None:
    from free_cycle_service import reconcile_free_profile_usage
    from models import NodeProvisioningJob

    user = _free_user(tg_id=1200 + session.query(NodeProvisioningJob).count(), plan_code=plan_code)
    user.sub_type = sub_type
    session.add(user)
    session.flush()

    result = reconcile_free_profile_usage(
        session,
        user=user,
        used_bytes=9 * GIB,
        source="node_observer",
        now=NOW,
    )
    session.flush()

    assert result["queued"] is False
    assert session.query(NodeProvisioningJob).count() == 0


def test_access_policy_uses_persisted_profile_not_usage_bytes(api_module) -> None:
    user = _free_user(tg_id=1301)
    user.free_profile_state = "soft_transition_pending"
    user.free_profile_active_role = "free_standard"
    pending = api_module._build_access_policy(user=user, used_bytes=8 * GIB, now=NOW)
    assert pending["access_state"] == "free_monthly"
    assert pending["soft_mode_active"] is False
    assert pending["free_profile_state"] == "soft_transition_pending"

    user.free_profile_state = "soft_active"
    user.free_profile_active_role = "free_soft"
    active = api_module._build_access_policy(user=user, used_bytes=1, now=NOW)
    assert active["access_state"] == "free_soft_mode"
    assert active["soft_mode_active"] is True
    assert active["free_profile_state"] == "soft_active"
    assert active["traffic_remaining_gb"] == 0.0


def test_soft_profile_counter_does_not_replace_standard_quota_evidence(session) -> None:
    from free_cycle_service import reconcile_free_profile_usage

    user = _free_user(tg_id=1302)
    user.free_profile_state = "soft_active"
    user.free_profile_active_role = "free_soft"
    user.free_profile_observed_bytes = 5 * GIB
    user.free_profile_observed_at = NOW
    user.free_profile_observation_source = "node_observer"
    session.add(user)
    session.flush()

    result = reconcile_free_profile_usage(
        session,
        user=user,
        used_bytes=1234,
        source="soft_node_observer",
        now=NOW + timedelta(minutes=5),
    )

    assert result["queued"] is False
    assert result["reason"] == "not_standard"
    assert user.free_profile_observed_bytes == 5 * GIB
    assert user.free_profile_observed_at == NOW
    assert user.free_profile_observation_source == "node_observer"


def test_free_profile_transition_query_locks_canonical_user_row(session) -> None:
    from sqlalchemy.dialects import postgresql

    from free_cycle_service import _locked_free_profile_user_query

    statement = _locked_free_profile_user_query(session, tg_id=1303).statement
    compiled = str(statement.compile(dialect=postgresql.dialect()))

    assert "FOR UPDATE" in compiled.upper()


def test_reconcile_retries_only_deadlock_with_rollback_and_fresh_session(monkeypatch) -> None:
    import free_cycle_service as service

    user = _free_user(tg_id=1304)
    sessions = []
    reconciled = []
    created_jobs = []

    class Deadlock(Exception):
        pgcode = "40P01"

    class Query:
        def filter(self, *_args):
            return self

        def with_for_update(self):
            return self

        def one_or_none(self):
            return user

    class Session:
        def __init__(self):
            self.events = []

        def query(self, _model):
            self.events.append("lock_user")
            return Query()

        def commit(self):
            self.events.append("commit")

        def rollback(self):
            self.events.append("rollback")

        def close(self):
            self.events.append("close")

    def make_session():
        item = Session()
        sessions.append(item)
        return item

    def reconcile(session, **_kwargs):
        reconciled.append(session)
        if len(reconciled) == 1:
            raise OperationalError("SELECT FOR UPDATE", {}, Deadlock())
        created_jobs.append("free_to_soft")
        return {"queued": True, "job_id": 77, "reason": "threshold_reached"}

    monkeypatch.setattr(service, "reconcile_free_profile_usage", reconcile)

    result = service.reconcile_free_profile_usage_in_new_transaction(
        tg_id=user.tg_id,
        used_bytes=5 * GIB,
        source="managed_profile_runtime",
        session_factory=make_session,
    )

    assert result == {"queued": True, "job_id": 77, "reason": "threshold_reached"}
    assert len(sessions) == 2
    assert sessions[0].events == ["lock_user", "rollback", "close"]
    assert sessions[1].events == ["lock_user", "commit", "close"]
    assert reconciled == sessions
    assert created_jobs == ["free_to_soft"]


def test_reconcile_does_not_retry_non_transaction_operational_error(monkeypatch) -> None:
    import free_cycle_service as service

    user = _free_user(tg_id=1305)
    sessions = []

    class ConnectionFailure(Exception):
        pgcode = "08006"

    class Query:
        def filter(self, *_args):
            return self

        def with_for_update(self):
            return self

        def one_or_none(self):
            return user

    class Session:
        def __init__(self):
            self.events = []

        def query(self, _model):
            self.events.append("lock_user")
            return Query()

        def rollback(self):
            self.events.append("rollback")

        def close(self):
            self.events.append("close")

    def make_session():
        item = Session()
        sessions.append(item)
        return item

    def reconcile(_session, **_kwargs):
        raise OperationalError("SELECT FOR UPDATE", {}, ConnectionFailure())

    monkeypatch.setattr(service, "reconcile_free_profile_usage", reconcile)

    with pytest.raises(OperationalError):
        service.reconcile_free_profile_usage_in_new_transaction(
            tg_id=user.tg_id,
            used_bytes=5 * GIB,
            source="managed_profile_runtime",
            session_factory=make_session,
        )

    assert len(sessions) == 1
    assert sessions[0].events == ["lock_user", "rollback", "close"]


def test_exact_finalize_lock_waits_instead_of_skipping_payment_row(session) -> None:
    from sqlalchemy.dialects import postgresql

    from models import User
    from node_provisioning_service import _lock_exact_query

    statement = _lock_exact_query(session.query(User).filter(User.tg_id == 1303), session).statement
    compiled = str(statement.compile(dialect=postgresql.dialect())).upper()

    assert "FOR UPDATE" in compiled
    assert "SKIP LOCKED" not in compiled


def test_node_access_role_model_declares_migration_index() -> None:
    from models import Node

    assert Node.__table__.c.access_role.index is True


def test_free_cycle_is_exactly_thirty_days_not_environment_overridable() -> None:
    portal_dir = Path(__file__).resolve().parents[1] / "portal_bot"
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": str(portal_dir),
            "DATABASE_URL": "sqlite:///:memory:",
            "BOT_TOKEN": "test-token",
            "FREE_CYCLE_DAYS": "3",
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import economy_service, free_cycle_service; "
            "print(free_cycle_service.FREE_CYCLE_DAYS, economy_service.FREE_CYCLE_DAYS)",
        ],
        cwd=portal_dir,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "30 30"


def test_free_plan_total_uses_exact_quota_not_legacy_environment(
    monkeypatch, api_module
) -> None:
    user = _free_user(tg_id=1304)
    monkeypatch.setattr(api_module, "FREE_TOTAL_GB", 99)
    monkeypatch.setattr(api_module, "FREE_LIMIT_IP", 9)

    assert api_module._plan_total_gb(user) == 5
    assert api_module._plan_device_limit(user) == 1


def test_soft_speed_authority_is_exactly_two_mbps() -> None:
    portal_dir = Path(__file__).resolve().parents[1] / "portal_bot"
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": str(portal_dir),
            "DATABASE_URL": "sqlite:///:memory:",
            "BOT_TOKEN": "test-token",
            "FREE_SOFT_MODE_SPEED_LIMIT_KBPS": "9999",
        }
    )
    result = subprocess.run(
        [sys.executable, "-c", "import api; print(api.FREE_SOFT_MODE_SPEED_LIMIT_KBPS)"],
        cwd=portal_dir,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "250"


def test_free_reset_job_rejects_operator_lab_source_binding(session) -> None:
    import json

    from free_cycle_service import queue_free_profile_reset
    from models import NodeProvisioningJob

    user = _free_user(tg_id=1305)
    session.add(user)
    session.flush()

    result = queue_free_profile_reset(
        session,
        user=user,
        source="test",
        now=NOW,
        source_bindings=[{"node_code": "operator-lab", "access_role": "operator_lab"}],
    )

    job = session.query(NodeProvisioningJob).filter_by(id=result["job_id"]).one()
    assert json.loads(job.desired_state_json)["source_bindings"] == []


def test_premium_pool_key_never_exposes_operator_lab(monkeypatch) -> None:
    import nodes_repo

    nodes = [
        _node("nl-paid", "paid", 51),
        _node("nl-lab", "operator_lab", 52),
    ]
    user = SimpleNamespace(sub_type="PAID", current_plan_code="paid_30d", is_active=True)
    key = SimpleNamespace(pool_code="premium_pool")
    monkeypatch.setattr(nodes_repo, "enabled_nodes", lambda _session: nodes)

    selected = nodes_repo.eligible_nodes(object(), user, key=key)

    assert [node.code for node in selected] == ["nl-paid"]


def test_subscription_does_not_restore_pool_when_every_node_is_hard_rejected(monkeypatch) -> None:
    import nodes_repo

    rejected = _node("nl-paid", "paid", 51)
    rejected.is_healthy = False
    user = SimpleNamespace(sub_type="PAID", current_plan_code="paid_30d", is_active=True)
    monkeypatch.setattr(nodes_repo, "enabled_nodes", lambda _session: [rejected])

    assert nodes_repo.eligible_nodes(object(), user, purpose="subscription") == []


def test_api_paid_pool_never_exposes_operator_lab(api_module) -> None:
    nodes = [
        _node("nl-paid", "paid", 51),
        _node("nl-lab", "operator_lab", 52),
    ]
    user = SimpleNamespace(sub_type="PAID", current_plan_code="paid_30d", is_active=True)

    assert api_module._node_allowed_for_plan(user, nodes[0]) is True
    assert api_module._node_allowed_for_plan(user, nodes[1]) is False
    assert [node.code for node in api_module._fallback_nodes_for_user(user, nodes)] == ["nl-paid"]


def test_api_soft_active_user_only_receives_soft_pool(api_module) -> None:
    nodes = [
        _node("nl-free-standard", "free_standard", 41),
        _node("nl-free-soft", "free_soft", 42),
    ]
    user = _free_user(tg_id=1306)
    user.free_profile_state = "soft_active"
    user.free_profile_active_role = "free_soft"

    assert [node.code for node in api_module._fallback_nodes_for_user(user, nodes)] == [
        "nl-free-soft"
    ]

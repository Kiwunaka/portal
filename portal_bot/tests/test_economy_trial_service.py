from __future__ import annotations

import sys
import uuid
import importlib.util
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

NOW = datetime(2026, 7, 12, 9, 0, 0)


def _session(tmp_path: Path):
    from models import Base

    engine = create_engine(f"sqlite:///{(tmp_path / 'economy.db').as_posix()}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _seed_account(session, *, suffix: str, sub_type: str = "FREE"):
    from models import Account, AccountDevice, User

    account_id = str(uuid.uuid4())
    device_id = str(uuid.uuid4())
    tg_id = 9_100_000_000_000 + int(suffix)
    account = Account(id=account_id, status="active", created_source="app_first", created_at=NOW, updated_at=NOW)
    device = AccountDevice(
        id=device_id,
        account_id=account_id,
        install_id=f"install-{suffix}",
        state="active",
        first_seen_at=NOW,
        last_seen_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
    user = User(
        tg_id=tg_id,
        account_id=account_id,
        username=f"trial-{suffix}",
        uuid=str(uuid.uuid4()),
        email=f"APP_{tg_id}",
        sub_type=sub_type,
        current_plan_code="trial" if sub_type == "FREE" else "1_month",
        expiry_at=NOW + timedelta(days=30),
        is_active=True,
        trial_used=True,
        app_install_id=device.install_id,
        created_at=NOW,
    )
    session.add_all([account, device, user])
    session.flush()
    return account, device, user


def test_reservation_is_seven_days_and_does_not_start_trial_clock(tmp_path: Path) -> None:
    from economy_service import read_trial_projection, reserve_trial

    engine, session = _session(tmp_path)
    account, device, user = _seed_account(session, suffix="1")

    grant = reserve_trial(session, account_id=account.id, device_id=device.id, now=NOW)
    replay = reserve_trial(session, account_id=account.id, device_id=device.id, now=NOW + timedelta(hours=1))
    from models import AccountDevice

    second_device = AccountDevice(
        id=str(uuid.uuid4()),
        account_id=account.id,
        install_id="install-second-device",
        state="active",
        first_seen_at=NOW,
        last_seen_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(second_device)
    session.flush()
    second_device_replay = reserve_trial(
        session,
        account_id=account.id,
        device_id=second_device.id,
        now=NOW + timedelta(hours=2),
    )
    projection = read_trial_projection(session, account_id=account.id, now=NOW)

    assert replay.id == grant.id
    assert second_device_replay.id == grant.id
    assert grant.status == "reserved"
    assert grant.reserved_at == NOW
    assert grant.reservation_expires_at == NOW + timedelta(days=7)
    assert grant.activated_at is None
    assert grant.expires_at is None
    assert grant.duration_days == 5
    assert user.current_plan_code == "trial"
    assert user.expiry_at == NOW + timedelta(days=7)
    assert projection == {
        "state": "reserved",
        "reserved_at": NOW.isoformat(),
        "reservation_expires_at": (NOW + timedelta(days=7)).isoformat(),
        "activated_at": None,
        "expires_at": None,
        "duration_days": 5,
    }
    session.close()
    engine.dispose()


def test_evidence_and_activation_are_idempotent_and_never_store_bearer_material(tmp_path: Path) -> None:
    from economy_service import activate_reserved_trial, record_connection_evidence, reserve_trial
    from models import ConnectionEvidence

    engine, session = _session(tmp_path)
    account, device, user = _seed_account(session, suffix="2")
    grant = reserve_trial(session, account_id=account.id, device_id=device.id, now=NOW)
    observed_at = NOW + timedelta(days=2, hours=3)

    evidence = record_connection_evidence(
        session,
        account_id=account.id,
        device_id=device.id,
        node_id=17,
        evidence_kind="observer_connection",
        observed_at=observed_at,
        evidence_key="observer:v1:stable-evidence-key",
    )
    replay = record_connection_evidence(
        session,
        account_id=account.id,
        device_id=device.id,
        node_id=17,
        evidence_kind="observer_connection",
        observed_at=observed_at,
        evidence_key="observer:v1:stable-evidence-key",
    )
    first = activate_reserved_trial(session, account_id=account.id, evidence=evidence)
    second = activate_reserved_trial(session, account_id=account.id, evidence=replay)

    assert evidence.id == replay.id
    assert first.grant.id == second.grant.id == grant.id
    assert first.activated_now is True
    assert second.activated_now is False
    assert session.query(ConnectionEvidence).count() == 1
    assert grant.status == "active"
    assert grant.activated_at == observed_at
    assert grant.expires_at == observed_at + timedelta(days=5)
    assert grant.activation_evidence_id == evidence.id
    assert user.expiry_at == observed_at + timedelta(days=5)
    forbidden = {"subscription_url", "sub_token", "token", "provider_secret", "source_ip", "traffic_payload"}
    assert forbidden.isdisjoint(ConnectionEvidence.__table__.columns.keys())
    session.close()
    engine.dispose()


def test_observer_offsets_activate_at_exact_naive_utc_plus_five_days(tmp_path: Path) -> None:
    from economy_service import activate_reserved_trial, record_connection_evidence, reserve_trial
    from observer_service import parse_observer_datetime

    expected_utc = datetime(2026, 7, 12, 12, 0, 0)
    for index, raw_timestamp in enumerate(
        (
            "2026-07-12T12:00:00Z",
            "2026-07-12T15:00:00+03:00",
            "2026-07-12T08:00:00-04:00",
        ),
        start=6,
    ):
        engine, session = _session(tmp_path)
        account, device, user = _seed_account(session, suffix=str(index))
        reserve_trial(session, account_id=account.id, device_id=device.id, now=NOW)
        observed_at = parse_observer_datetime(raw_timestamp)
        evidence = record_connection_evidence(
            session,
            account_id=account.id,
            device_id=device.id,
            node_id=index,
            evidence_kind="observer_connection",
            observed_at=observed_at,
            evidence_key=f"observer-offset-{index}",
        )

        activation = activate_reserved_trial(session, account_id=account.id, evidence=evidence)

        assert observed_at == expected_utc
        assert observed_at.tzinfo is None
        assert activation.activated_now is True
        assert activation.grant is not None
        assert activation.grant.activated_at == expected_utc
        assert activation.grant.expires_at == expected_utc + timedelta(days=5)
        assert user.expiry_at == expected_utc + timedelta(days=5)
        session.close()
        engine.dispose()


def test_expiration_sweep_projects_free_without_revoking_paid_grants(tmp_path: Path) -> None:
    from economy_service import expire_stale_trial_reservations, reserve_trial

    engine, session = _session(tmp_path)
    free_account, free_device, free_user = _seed_account(session, suffix="3")
    paid_account, paid_device, paid_user = _seed_account(session, suffix="4", sub_type="PAID")
    bonus_account, bonus_device, bonus_user = _seed_account(session, suffix="5")
    bonus_user.sub_type = "BONUS"
    bonus_user.current_plan_code = "channel_bonus"
    bonus_user.expiry_at = NOW + timedelta(days=20)
    free_trial = reserve_trial(session, account_id=free_account.id, device_id=free_device.id, now=NOW)
    paid_trial = reserve_trial(session, account_id=paid_account.id, device_id=paid_device.id, now=NOW)
    bonus_trial = reserve_trial(session, account_id=bonus_account.id, device_id=bonus_device.id, now=NOW)
    session.flush()

    result = expire_stale_trial_reservations(session, now=NOW + timedelta(days=8))

    assert result == {"expired": 3, "projected_free": 1, "preserved_other_access": 2}
    assert free_trial.status == "expired"
    assert free_user.sub_type == "FREE"
    assert free_user.current_plan_code == "free_monthly"
    assert free_user.is_active is True
    assert free_user.expiry_at == NOW + timedelta(days=38)
    assert paid_trial.status == "expired"
    assert paid_user.sub_type == "PAID"
    assert paid_user.current_plan_code == "1_month"
    assert paid_user.expiry_at == NOW + timedelta(days=30)
    assert bonus_trial.status == "expired"
    assert bonus_user.sub_type == "BONUS"
    assert bonus_user.current_plan_code == "channel_bonus"
    assert bonus_user.expiry_at == NOW + timedelta(days=20)
    session.close()
    engine.dispose()


def test_sqlite_and_postgres_economy_migrations_are_additive(tmp_path: Path) -> None:
    import migrations

    sqlite_engine = create_engine(f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}")
    with sqlite_engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE entitlement_grants ("
                "id VARCHAR(36) PRIMARY KEY, account_id VARCHAR(36) NOT NULL, "
                "idempotency_key VARCHAR(160) NOT NULL, source VARCHAR(40) NOT NULL, "
                "status VARCHAR(24) NOT NULL)"
            )
        )
        migrations._ensure_economy_domain_sqlite(conn)

    grant_columns = {column["name"] for column in inspect(sqlite_engine).get_columns("entitlement_grants")}
    assert {"reserved_at", "reservation_expires_at", "activated_at", "duration_days", "activation_evidence_id"} <= grant_columns
    assert inspect(sqlite_engine).has_table("connection_evidence")

    class _Result:
        def scalar(self):
            return False

    class _Conn:
        def __init__(self):
            self.sql: list[str] = []

        def execute(self, statement, _params=None):
            self.sql.append(str(statement))
            return _Result()

    conn = _Conn()
    migrations._ensure_economy_domain_postgres(conn)
    postgres_sql = "\n".join(conn.sql)
    assert "CREATE TABLE IF NOT EXISTS connection_evidence" in postgres_sql
    assert "ALTER TABLE entitlement_grants ADD COLUMN reservation_expires_at TIMESTAMP" in postgres_sql
    assert "CREATE UNIQUE INDEX IF NOT EXISTS uq_connection_evidence_key" in postgres_sql
    assert "CREATE UNIQUE INDEX IF NOT EXISTS uq_entitlement_grants_premium_trial_account" in postgres_sql
    sqlite_engine.dispose()


def test_postgres_rehearsal_orders_and_validates_connection_evidence() -> None:
    script_path = PORTAL_BOT_DIR.parent / "scripts" / "migrate_sqlite_to_postgres.py"
    spec = importlib.util.spec_from_file_location("economy_rehearsal_contract", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.TABLE_DEPENDENCIES["connection_evidence"] == {"accounts", "account_devices", "nodes"}
    assert (
        "connection_evidence",
        "account_id",
        "accounts",
        "id",
    ) in module.ECONOMY_INVARIANT_RELATIONS
    assert (
        "entitlement_grants",
        "activation_evidence_id",
        "connection_evidence",
        "id",
    ) in module.ECONOMY_INVARIANT_RELATIONS


def test_worker_schedules_stale_trial_reservation_sweep() -> None:
    worker_source = (PORTAL_BOT_DIR / "worker.py").read_text(encoding="utf-8")

    assert "expire_stale_trial_reservations" in worker_source
    assert '_supervise_job("trial_reservation_expiry", trial_reservation_expiry_job)' in worker_source

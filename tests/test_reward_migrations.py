from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from migrations import run_migrations
from models import Base, NodeProvisioningJob, RewardAccountState


REWARD_STATE_COLUMNS = {
    "account_id",
    "wheel_last_spin_at",
    "wheel_last_grant_id",
    "calendar_last_check_date",
    "calendar_cycle_started_on",
    "calendar_cycle_day",
    "calendar_first_checkin_at",
    "calendar_streak_7_unlocked_at",
    "created_at",
    "updated_at",
}


def test_reward_state_model_uses_one_row_per_account() -> None:
    assert RewardAccountState.__tablename__ == "reward_account_states"
    assert RewardAccountState.__table__.primary_key.columns.keys() == ["account_id"]
    assert {column.name for column in RewardAccountState.__table__.columns} == REWARD_STATE_COLUMNS


def test_fresh_schema_has_reward_state_and_job_indexes(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'fresh.db').as_posix()}")
    Base.metadata.create_all(engine)
    schema = inspect(engine)

    assert schema.has_table("reward_account_states")
    assert {row["name"] for row in schema.get_columns("reward_account_states")} == REWARD_STATE_COLUMNS
    reward_indexes = {row["name"] for row in schema.get_indexes("reward_account_states")}
    assert "ix_reward_account_states_wheel_last_grant_id" in reward_indexes

    job_columns = {row["name"] for row in schema.get_columns("node_provisioning_jobs")}
    job_indexes = {row["name"] for row in schema.get_indexes("node_provisioning_jobs")}
    assert {"account_id", "entitlement_grant_id"} <= job_columns
    assert {
        "ix_node_provisioning_jobs_account_id",
        "ix_node_provisioning_jobs_entitlement_grant_id",
    } <= job_indexes
    engine.dispose()


def test_calendar_state_rejects_day_outside_zero_to_twenty_eight(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'check.db').as_posix()}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with pytest.raises(IntegrityError):
        with Session.begin() as session:
            session.add(RewardAccountState(account_id="a" * 36, calendar_cycle_day=29))
            session.flush()
    engine.dispose()


def test_sqlite_legacy_job_migration_is_repeatable_and_preserves_rows(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'legacy-job.db').as_posix()}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE node_provisioning_jobs ("
                "id INTEGER PRIMARY KEY, job_type VARCHAR(32) NOT NULL, "
                "status VARCHAR(32) NOT NULL, desired_state_json TEXT, "
                "result_json TEXT, attempts INTEGER NOT NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO node_provisioning_jobs "
                "(id, job_type, status, desired_state_json, result_json, attempts) "
                "VALUES (7, 'rotate_access_key', 'queued', :desired, :result, 2)"
            ),
            {"desired": '{"keep":true}', "result": '{"old":true}'},
        )

    Base.metadata.create_all(engine)
    run_migrations(engine)
    run_migrations(engine)

    schema = inspect(engine)
    columns = {row["name"] for row in schema.get_columns("node_provisioning_jobs")}
    indexes = {row["name"] for row in schema.get_indexes("node_provisioning_jobs")}
    assert {"account_id", "entitlement_grant_id"} <= columns
    assert {
        "ix_node_provisioning_jobs_account_id",
        "ix_node_provisioning_jobs_entitlement_grant_id",
    } <= indexes
    assert schema.has_table("reward_account_states")

    with engine.connect() as connection:
        legacy = connection.execute(
            text(
                "SELECT desired_state_json, result_json, attempts, account_id, entitlement_grant_id "
                "FROM node_provisioning_jobs WHERE id = 7"
            )
        ).one()
    assert tuple(legacy) == ('{"keep":true}', '{"old":true}', 2, None, None)
    engine.dispose()


def test_node_provisioning_job_model_exposes_nullable_reward_ownership() -> None:
    assert NodeProvisioningJob.__table__.c.account_id.nullable is True
    assert NodeProvisioningJob.__table__.c.entitlement_grant_id.nullable is True

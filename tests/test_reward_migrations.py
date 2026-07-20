from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from migrations import run_migrations
from models import (
    Account,
    AccountMergeReview,
    Base,
    NodeProvisioningJob,
    RewardAccountState,
    User,
)


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


def test_reward_backfill_keeps_latest_alias_wheel_timestamp_without_reading_monthly_streaks(
    tmp_path: Path,
) -> None:
    from rewards_service import backfill_reward_account_states

    now = datetime(2026, 7, 20, 12, 0, 0)
    target_id = "00000000-0000-4000-8000-000000000401"
    source_id = "00000000-0000-4000-8000-000000000402"
    engine = create_engine(f"sqlite:///{(tmp_path / 'reward-backfill.db').as_posix()}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as session:
        session.add_all(
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
                User(
                    tg_id=740401,
                    account_id=target_id,
                    uuid="00000000-0000-4000-8000-000000000403",
                    last_wheel_spin=now - timedelta(days=10),
                    streak_months=11,
                    streak_last_check=now - timedelta(days=30),
                ),
                User(
                    tg_id=740402,
                    account_id=source_id,
                    uuid="00000000-0000-4000-8000-000000000404",
                    last_wheel_spin=now - timedelta(days=2),
                    streak_months=22,
                    streak_last_check=now - timedelta(days=60),
                ),
            ]
        )
        session.flush()
        statements: list[str] = []

        def _capture_sql(_conn, _cursor, statement, _parameters, _context, _executemany) -> None:
            statements.append(str(statement).lower())

        event.listen(engine, "before_cursor_execute", _capture_sql)
        try:
            first = backfill_reward_account_states(session, now=now)
        finally:
            event.remove(engine, "before_cursor_execute", _capture_sql)

        assert first.canonical_accounts == 1
        assert first.states_created == 1
        assert first.wheel_sources_seen == 2
        assert first.wheel_states_updated == 1
        assert first.unresolved_users == 0
        assert first.invalid_merge_chains == 0
        assert first.ready is True
        assert not any("streak_months" in statement for statement in statements)
        assert not any("streak_last_check" in statement for statement in statements)

        state = session.get(RewardAccountState, target_id)
        assert state is not None
        assert state.wheel_last_spin_at == now - timedelta(days=2)
        target_user = session.get(User, 740401)
        source_user = session.get(User, 740402)
        assert (target_user.streak_months, target_user.streak_last_check) == (
            11,
            now - timedelta(days=30),
        )
        assert (source_user.streak_months, source_user.streak_last_check) == (
            22,
            now - timedelta(days=60),
        )

        second = backfill_reward_account_states(session, now=now)
        assert second.states_created == 0
        assert second.wheel_sources_seen == 2
        assert second.wheel_states_updated == 0
        assert second.ready is True
    engine.dispose()


def test_reward_backfill_reports_unresolved_users_reviews_and_invalid_chains(
    tmp_path: Path,
) -> None:
    from rewards_service import backfill_reward_account_states

    now = datetime(2026, 7, 20, 12, 0, 0)
    valid_id = "00000000-0000-4000-8000-000000000411"
    broken_id = "00000000-0000-4000-8000-000000000412"
    missing_target_id = "00000000-0000-4000-8000-000000000413"
    engine = create_engine(f"sqlite:///{(tmp_path / 'reward-backfill-blocked.db').as_posix()}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as session:
        session.add_all(
            [
                Account(
                    id=valid_id,
                    status="active",
                    created_source="test",
                    created_at=now,
                    updated_at=now,
                ),
                Account(
                    id=broken_id,
                    status="merged",
                    merged_into_account_id=missing_target_id,
                    created_source="test",
                    created_at=now,
                    updated_at=now,
                ),
                User(
                    tg_id=740411,
                    account_id=valid_id,
                    uuid="00000000-0000-4000-8000-000000000414",
                ),
                User(
                    tg_id=740412,
                    account_id=None,
                    uuid="00000000-0000-4000-8000-000000000415",
                    last_wheel_spin=now - timedelta(days=3),
                ),
                User(
                    tg_id=740413,
                    account_id=broken_id,
                    uuid="00000000-0000-4000-8000-000000000416",
                ),
                AccountMergeReview(
                    id="00000000-0000-4000-8000-000000000417",
                    fingerprint="reward-backfill-open-review",
                    account_id=valid_id,
                    conflicting_account_id=broken_id,
                    reason_code="identity_account_conflict",
                    status="open",
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        session.flush()
        account_count_before = session.query(Account).count()

        result = backfill_reward_account_states(session, now=now)

        assert result.canonical_accounts == 1
        assert result.states_created == 1
        assert result.wheel_sources_seen == 1
        assert result.wheel_states_updated == 0
        assert result.unresolved_users == 2
        assert result.invalid_merge_chains == 2
        assert result.ready is False
        assert session.query(Account).count() == account_count_before
        assert session.get(RewardAccountState, valid_id) is not None
        assert session.get(RewardAccountState, broken_id) is None
    engine.dispose()

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, text


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


USER_COLUMNS = {
    "free_profile_state",
    "free_profile_active_role",
    "free_profile_source",
    "free_profile_state_changed_at",
    "free_profile_job_id",
    "free_profile_error_code",
    "free_profile_standard_node_code",
    "free_profile_soft_node_code",
    "free_profile_observed_bytes",
    "free_profile_observed_at",
    "free_profile_observation_source",
}
JOB_COLUMNS = {
    "idempotency_key",
    "lock_token",
    "last_error_code",
    "replacement_key_uuid",
    "completed_at",
    "manual_review_at",
}


def test_sqlite_free_profile_migration_is_repeatable_and_preserves_rows(tmp_path: Path) -> None:
    from migrations import _ensure_free_profile_schema_sqlite

    engine = create_engine(f"sqlite:///{(tmp_path / 'legacy-free-profile.db').as_posix()}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (tg_id BIGINT PRIMARY KEY, sub_type VARCHAR(50))"))
        connection.execute(text("INSERT INTO users(tg_id, sub_type) VALUES (101, 'FREE')"))
        connection.execute(text("CREATE TABLE nodes (id INTEGER PRIMARY KEY, code VARCHAR(32) NOT NULL)"))
        connection.execute(
            text(
                "INSERT INTO nodes(id, code) VALUES "
                "(1, 'nl-free'), (2, 'nl-free-soft'), (3, 'operator-lab'), (4, 'de-main')"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE node_provisioning_jobs ("
                "id INTEGER PRIMARY KEY, job_type VARCHAR(32), status VARCHAR(32), "
                "desired_state_json TEXT, result_json TEXT, attempts INTEGER)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO node_provisioning_jobs(id, job_type, status, desired_state_json, result_json, attempts) "
                "VALUES (7, 'rotate_access_key', 'queued', :desired, :result, 2)"
            ),
            {"desired": '{"keep":true}', "result": '{"old":true}'},
        )

        _ensure_free_profile_schema_sqlite(connection)
        _ensure_free_profile_schema_sqlite(connection)

        user_columns = {str(row[1]) for row in connection.execute(text("PRAGMA table_info(users)"))}
        node_columns = {str(row[1]) for row in connection.execute(text("PRAGMA table_info(nodes)"))}
        job_columns = {
            str(row[1]) for row in connection.execute(text("PRAGMA table_info(node_provisioning_jobs)"))
        }
        assert USER_COLUMNS <= user_columns
        assert "access_role" in node_columns
        assert JOB_COLUMNS <= job_columns

        user = connection.execute(
            text(
                "SELECT free_profile_state, free_profile_active_role, free_profile_source, "
                "free_profile_observed_bytes FROM users WHERE tg_id = 101"
            )
        ).one()
        assert tuple(user) == ("standard", "free_standard", "legacy_backfill", 0)
        roles = dict(connection.execute(text("SELECT code, access_role FROM nodes ORDER BY id")).fetchall())
        assert roles == {
            "nl-free": "free_standard",
            "nl-free-soft": "free_soft",
            "operator-lab": "operator_lab",
            "de-main": "paid",
        }
        legacy_job = connection.execute(
            text(
                "SELECT desired_state_json, result_json, attempts FROM node_provisioning_jobs WHERE id = 7"
            )
        ).one()
        assert tuple(legacy_job) == ('{"keep":true}', '{"old":true}', 2)

        indexes = {
            str(row[1]): bool(row[2])
            for row in connection.execute(text("PRAGMA index_list(node_provisioning_jobs)"))
        }
        assert indexes["ix_node_provisioning_jobs_idempotency_key"] is True
        assert "ix_node_provisioning_jobs_lock_token" in indexes
        user_indexes = {
            str(row[1]) for row in connection.execute(text("PRAGMA index_list(users)"))
        }
        assert "ix_users_free_profile_job_id" in user_indexes

    engine.dispose()


def test_sqlite_role_backfill_retains_invalid_legacy_value_for_rollback(tmp_path: Path) -> None:
    from migrations import _ensure_free_profile_schema_sqlite

    engine = create_engine(f"sqlite:///{(tmp_path / 'legacy-node-role.db').as_posix()}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE nodes ("
                "id INTEGER PRIMARY KEY, code VARCHAR(32) NOT NULL, access_role VARCHAR(32))"
            )
        )
        connection.execute(
            text("INSERT INTO nodes(id, code, access_role) VALUES (1, 'legacy-main', 'mystery_pool')")
        )

        _ensure_free_profile_schema_sqlite(connection)
        _ensure_free_profile_schema_sqlite(connection)

        row = connection.execute(
            text("SELECT access_role, access_role_legacy FROM nodes WHERE id = 1")
        ).one()
        assert tuple(row) == ("paid", "mystery_pool")

    engine.dispose()


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar(self):
        return self.value


class _PostgresRecorder:
    def __init__(self, existing_columns=()):
        self.existing_columns = set(existing_columns)
        self.executed: list[tuple[str, dict]] = []

    def execute(self, statement, params=None):
        sql = str(statement)
        values = dict(params or {})
        self.executed.append((sql, values))
        if "information_schema.columns" in sql and "SELECT EXISTS" in sql:
            key = (values.get("table_name"), values.get("column_name"))
            return _ScalarResult(key in self.existing_columns)
        return _ScalarResult(None)


def test_postgres_free_profile_migration_is_additive_backfilled_and_indexed() -> None:
    from migrations import _ensure_free_profile_schema_postgres

    connection = _PostgresRecorder()
    _ensure_free_profile_schema_postgres(connection)
    sql = "\n".join(statement for statement, _params in connection.executed)

    for column in sorted(USER_COLUMNS):
        assert f"ALTER TABLE users ADD COLUMN {column}" in sql
    assert "ALTER TABLE nodes ADD COLUMN access_role" in sql
    assert "ALTER TABLE nodes ADD COLUMN access_role_legacy" in sql
    for column in sorted(JOB_COLUMNS):
        assert f"ALTER TABLE node_provisioning_jobs ADD COLUMN {column}" in sql
    assert "UPDATE users" in sql
    assert "legacy_backfill" in sql
    assert "UPDATE nodes" in sql
    assert "free_soft" in sql
    assert "operator_lab" in sql
    assert "CREATE UNIQUE INDEX IF NOT EXISTS ix_node_provisioning_jobs_idempotency_key" in sql
    assert "CREATE INDEX IF NOT EXISTS ix_node_provisioning_jobs_lock_token" in sql
    assert "CREATE INDEX IF NOT EXISTS ix_users_free_profile_job_id" in sql


def test_postgres_free_profile_migration_skips_existing_columns() -> None:
    from migrations import _ensure_free_profile_schema_postgres

    existing = (
        {("users", column) for column in USER_COLUMNS}
        | {("nodes", "access_role"), ("nodes", "access_role_legacy")}
        | {("node_provisioning_jobs", column) for column in JOB_COLUMNS}
    )
    connection = _PostgresRecorder(existing)
    _ensure_free_profile_schema_postgres(connection)
    sql = "\n".join(statement for statement, _params in connection.executed)

    assert " ADD COLUMN " not in sql
    assert "SET access_role_legacy = access_role" in sql
    assert "CREATE UNIQUE INDEX IF NOT EXISTS ix_node_provisioning_jobs_idempotency_key" in sql

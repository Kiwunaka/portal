from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import UniqueConstraint, create_engine, event, inspect, text
from sqlalchemy.exc import IntegrityError


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))

import migrations  # noqa: E402
import models  # noqa: E402


RU_TABLES = {
    "ru_probe_runs",
    "ru_probe_target_results",
    "ru_probe_uploader_heartbeats",
    "internal_ingest_nonces",
}

EXPECTED_COLUMNS = {
    "ru_probe_runs": {
        "id",
        "run_id",
        "schema_version",
        "origin",
        "probe_host_id",
        "probe_host_label",
        "probe_public_ip",
        "runner_version",
        "started_at",
        "finished_at",
        "received_at",
        "manifest_revision",
        "execution_status",
        "evidence_code",
        "environment_verdict",
        "release_verdict",
        "current_eligible",
        "ineligible_reason",
        "google_reachable",
        "xhttp_alive",
        "hysteria_alive",
        "server_reason",
        "server_summary",
        "artifact_sha256",
        "ingest_key_id",
        "retention_hold",
        "retention_hold_reason",
        "retention_held_at",
    },
    "ru_probe_target_results": {
        "id",
        "run_db_id",
        "target_id",
        "target_kind",
        "scope",
        "node_code",
        "endpoint_fingerprint",
        "endpoint_host",
        "endpoint_port",
        "endpoint_sni",
        "requested_address_families_json",
        "transport_metadata_json",
        "transport_profile",
        "probe_mode",
        "http_path",
        "min_body_bytes",
        "local_probe_profile_id",
        "observed_at",
        "overall_status",
        "current_eligible",
        "ineligible_reason",
        "dns_status",
        "dns_latency_ms",
        "tcp_status",
        "tcp_latency_ms",
        "tls_status",
        "tls_latency_ms",
        "http_large_body_status",
        "http_large_body_latency_ms",
        "transport_handshake_status",
        "transport_handshake_latency_ms",
        "ipv4_status",
        "ipv6_status",
        "reported_transport_handshake_status",
        "reported_transport_classification",
        "server_reason_code",
        "server_detail",
    },
    "ru_probe_uploader_heartbeats": {
        "id",
        "probe_host_id",
        "observed_at",
        "received_at",
        "service_version",
        "pending_count",
        "blocked_count",
        "quarantine_count",
        "oldest_pending_at",
        "archive_write_ok",
        "disk_free_bytes",
        "disk_state",
        "last_error_code",
        "ingest_key_id",
    },
    "internal_ingest_nonces": {
        "id",
        "key_scope",
        "key_id",
        "nonce_hash",
        "request_path",
        "request_timestamp",
        "body_sha256",
        "expires_at",
        "created_at",
    },
}

EXPECTED_UNIQUES = {
    "ru_probe_runs": {
        "uq_ru_probe_runs_run_id": ("run_id",),
    },
    "ru_probe_target_results": {
        "uq_ru_probe_target_run_target": ("run_db_id", "target_id"),
    },
    "ru_probe_uploader_heartbeats": {
        "uq_ru_probe_uploader_heartbeat_host_observed": (
            "probe_host_id",
            "observed_at",
        ),
    },
    "internal_ingest_nonces": {
        "uq_internal_ingest_nonce_scope_key_hash": (
            "key_scope",
            "key_id",
            "nonce_hash",
        ),
    },
}

EXPECTED_INDEXES = {
    "ru_probe_runs": {
        "ix_ru_probe_runs_finished_at": ("finished_at",),
        "ix_ru_probe_runs_release_verdict": ("release_verdict",),
        "ix_ru_probe_runs_current_eligible": ("current_eligible",),
        "ix_ru_probe_runs_probe_host_label": ("probe_host_label",),
    },
    "ru_probe_target_results": {
        "ix_ru_probe_target_results_node_code": ("node_code",),
        "ix_ru_probe_target_results_target_kind": ("target_kind",),
        "ix_ru_probe_target_results_overall_status": ("overall_status",),
        "ix_ru_probe_target_results_node_observed_at": (
            "node_code",
            "observed_at",
        ),
        "ix_ru_probe_target_results_run_node": ("run_db_id", "node_code"),
    },
    "ru_probe_uploader_heartbeats": {
        "ix_ru_probe_uploader_heartbeats_received_at": ("received_at",),
        "ix_ru_probe_uploader_heartbeats_probe_host_id": ("probe_host_id",),
        "ix_ru_probe_uploader_heartbeats_host_observed_at": (
            "probe_host_id",
            "observed_at",
        ),
    },
    "internal_ingest_nonces": {
        "ix_internal_ingest_nonces_expires_at": ("expires_at",),
    },
}


@pytest.fixture
def migrated_engine(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'ru-probe.db').as_posix()}")
    legacy_tables = [
        table
        for table in models.Base.metadata.sorted_tables
        if table.name not in RU_TABLES
    ]
    models.Base.metadata.create_all(engine, tables=legacy_tables)
    migrations.run_migrations(engine)
    try:
        yield engine
    finally:
        engine.dispose()


def _unique_constraints(inspector, table: str) -> dict[str, tuple[str, ...]]:
    return {
        str(item["name"]): tuple(item["column_names"])
        for item in inspector.get_unique_constraints(table)
    }


def _indexes(inspector, table: str) -> dict[str, tuple[str, ...]]:
    return {
        str(item["name"]): tuple(item["column_names"])
        for item in inspector.get_indexes(table)
    }


def _normalized_default(value) -> str | None:
    if value is None:
        return None
    return str(value).strip().strip("()").strip().lower()


def _assert_sqlite_autoincrement_contract(table_sql: dict[str, str]) -> None:
    assert set(table_sql) == RU_TABLES
    for table_name, create_sql in table_sql.items():
        normalized = " ".join(create_sql.split()).upper()
        assert "ID INTEGER PRIMARY KEY AUTOINCREMENT" in normalized, (
            f"Explicit SQLite migration lost AUTOINCREMENT for {table_name}: "
            f"{create_sql}"
        )


def _insert(conn, table: str, values: dict):
    columns = ", ".join(values)
    binds = ", ".join(f":{column}" for column in values)
    return conn.execute(
        text(f"INSERT INTO {table} ({columns}) VALUES ({binds})"),
        values,
    )


def _run_values(run_id: str = "run-001") -> dict:
    return {
        "run_id": run_id,
        "schema_version": 2,
        "origin": "ru",
        "probe_host_id": "mini",
        "probe_host_label": "mini",
        "runner_version": "2.0.0",
        "started_at": "2026-07-15T12:00:00+00:00",
        "finished_at": "2026-07-15T12:01:00+00:00",
        "received_at": "2026-07-15T12:01:05+00:00",
        "manifest_revision": "a" * 64,
        "execution_status": "completed",
        "environment_verdict": "pass",
        "release_verdict": "pass",
        "artifact_sha256": "b" * 64,
        "ingest_key_id": "mini-v1",
    }


def _target_values(run_db_id: int, target_id: str = "node:nl") -> dict:
    return {
        "run_db_id": run_db_id,
        "target_id": target_id,
        "target_kind": "delivery_node",
        "scope": "release_required",
        "node_code": "nl",
        "endpoint_fingerprint": "c" * 64,
        "endpoint_host": "nl.example.test",
        "endpoint_port": 443,
        "requested_address_families_json": '["ipv4","ipv6"]',
        "transport_metadata_json": '{"detail_code":null}',
        "transport_profile": "legacy_reality_fallback",
        "probe_mode": "delivery_tls",
        "observed_at": "2026-07-15T12:01:00+00:00",
        "overall_status": "pass",
        "dns_status": "pass",
        "tcp_status": "pass",
        "tls_status": "pass",
        "http_large_body_status": "not_applicable",
        "transport_handshake_status": "pass",
        "ipv4_status": "pass",
        "ipv6_status": "not_run",
        "reported_transport_handshake_status": "pass",
        "reported_transport_classification": "ok",
    }


def _schema_signature(engine) -> dict:
    inspector = inspect(engine)
    signature = {}
    for table in sorted(RU_TABLES):
        signature[table] = {
            "columns": tuple(
                (
                    item["name"],
                    str(item["type"]),
                    bool(item["nullable"]),
                    item.get("default"),
                )
                for item in inspector.get_columns(table)
            ),
            "uniques": tuple(sorted(_unique_constraints(inspector, table).items())),
            "indexes": tuple(sorted(_indexes(inspector, table).items())),
            "foreign_keys": tuple(
                sorted(
                    (
                        tuple(item["constrained_columns"]),
                        item["referred_table"],
                        tuple(item["referred_columns"]),
                        str((item.get("options") or {}).get("ondelete") or ""),
                    )
                    for item in inspector.get_foreign_keys(table)
                )
            ),
        }
    return signature


def test_ru_probe_tables_have_exact_safe_columns(migrated_engine) -> None:
    inspector = inspect(migrated_engine)

    assert RU_TABLES.issubset(set(inspector.get_table_names()))
    for table, expected in EXPECTED_COLUMNS.items():
        actual = {item["name"] for item in inspector.get_columns(table)}
        assert actual == expected

    nonce_columns = EXPECTED_COLUMNS["internal_ingest_nonces"]
    assert "nonce" not in nonce_columns
    assert not {"secret", "signature", "raw_nonce", "raw_body"} & nonce_columns
    assert "verdict" not in EXPECTED_COLUMNS["ru_probe_target_results"]


def test_models_and_explicit_sqlite_ddl_match(migrated_engine) -> None:
    inspector = inspect(migrated_engine)

    for table_name, expected_columns in EXPECTED_COLUMNS.items():
        model_table = models.Base.metadata.tables[table_name]
        db_columns = {
            item["name"]: item for item in inspector.get_columns(table_name)
        }
        assert set(model_table.c.keys()) == expected_columns
        assert set(db_columns) == expected_columns
        for column in model_table.c:
            assert str(db_columns[column.name]["type"]).upper() == str(
                column.type
            ).upper()
            if column.primary_key:
                continue
            assert bool(db_columns[column.name]["nullable"]) is bool(column.nullable)
            model_default = (
                column.server_default.arg
                if column.server_default is not None
                else None
            )
            assert _normalized_default(
                db_columns[column.name].get("default")
            ) == _normalized_default(model_default)

        model_uniques = {
            str(constraint.name): tuple(constraint.columns.keys())
            for constraint in model_table.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        model_indexes = {
            str(index.name): tuple(index.columns.keys())
            for index in model_table.indexes
        }
        assert model_uniques == EXPECTED_UNIQUES[table_name]
        assert _unique_constraints(inspector, table_name) == EXPECTED_UNIQUES[table_name]
        assert model_indexes == EXPECTED_INDEXES[table_name]
        assert _indexes(inspector, table_name) == EXPECTED_INDEXES[table_name]

    target_fk = next(
        iter(models.Base.metadata.tables["ru_probe_target_results"].c.run_db_id.foreign_keys)
    )
    assert target_fk.target_fullname == "ru_probe_runs.id"
    assert target_fk.ondelete == "CASCADE"
    db_foreign_keys = inspector.get_foreign_keys("ru_probe_target_results")
    assert len(db_foreign_keys) == 1
    assert db_foreign_keys[0]["name"] == "fk_ru_probe_target_results_run"
    assert db_foreign_keys[0]["constrained_columns"] == ["run_db_id"]
    assert db_foreign_keys[0]["referred_table"] == "ru_probe_runs"
    assert db_foreign_keys[0]["referred_columns"] == ["id"]
    assert db_foreign_keys[0]["options"] == {"ondelete": "CASCADE"}
    for column_name in ("started_at", "finished_at", "received_at"):
        assert models.RuProbeRun.__table__.c[column_name].type.timezone is True
    assert models.RuProbeTargetResult.__table__.c.observed_at.type.timezone is True
    assert models.RuProbeTargetResult.__table__.c.server_detail.type.length == 500


def test_required_unique_constraints_are_enforced(migrated_engine) -> None:
    with migrated_engine.begin() as conn:
        run_db_id = int(_insert(conn, "ru_probe_runs", _run_values()).lastrowid)
        with pytest.raises(IntegrityError):
            _insert(conn, "ru_probe_runs", _run_values())

        _insert(conn, "ru_probe_target_results", _target_values(run_db_id))
        with pytest.raises(IntegrityError):
            _insert(conn, "ru_probe_target_results", _target_values(run_db_id))

        heartbeat = {
            "probe_host_id": "mini",
            "observed_at": "2026-07-15T12:02:00+00:00",
            "received_at": "2026-07-15T12:02:05+00:00",
            "service_version": "2.0.0",
            "disk_state": "ok",
            "ingest_key_id": "mini-v1",
        }
        _insert(conn, "ru_probe_uploader_heartbeats", heartbeat)
        with pytest.raises(IntegrityError):
            _insert(conn, "ru_probe_uploader_heartbeats", heartbeat)

        nonce = {
            "key_scope": "ru_probe",
            "key_id": "mini-v1",
            "nonce_hash": "d" * 64,
            "request_path": "/internal/ru-probes/ingest",
            "request_timestamp": "2026-07-15T12:02:05+00:00",
            "body_sha256": "e" * 64,
            "expires_at": "2026-07-16T12:02:05+00:00",
        }
        _insert(conn, "internal_ingest_nonces", nonce)
        with pytest.raises(IntegrityError):
            _insert(conn, "internal_ingest_nonces", nonce)


def test_sqlite_foreign_key_is_enabled_and_cascades(migrated_engine) -> None:
    with migrated_engine.begin() as conn:
        assert conn.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
        run_db_id = int(
            _insert(conn, "ru_probe_runs", _run_values("run-cascade")).lastrowid
        )
        _insert(conn, "ru_probe_target_results", _target_values(run_db_id))
        conn.execute(
            text("DELETE FROM ru_probe_runs WHERE id = :run_db_id"),
            {"run_db_id": run_db_id},
        )
        remaining = conn.execute(
            text(
                "SELECT count(*) FROM ru_probe_target_results "
                "WHERE run_db_id = :run_db_id"
            ),
            {"run_db_id": run_db_id},
        ).scalar_one()
        assert remaining == 0

    with migrated_engine.begin() as conn:
        with pytest.raises(IntegrityError):
            _insert(conn, "ru_probe_target_results", _target_values(999999))


def test_second_migration_run_has_no_schema_drift(migrated_engine) -> None:
    before = _schema_signature(migrated_engine)

    migrations.run_migrations(migrated_engine)

    assert _schema_signature(migrated_engine) == before


def test_sqlite_ru_probe_ddl_immediately_follows_admin_ops(migrated_engine) -> None:
    statements: list[str] = []

    def capture(_conn, _cursor, statement, _parameters, _context, _executemany):
        statements.append(" ".join(str(statement).split()))

    event.listen(migrated_engine, "before_cursor_execute", capture)
    try:
        migrations.run_migrations(migrated_engine)
    finally:
        event.remove(migrated_engine, "before_cursor_execute", capture)

    admin_last = next(
        index
        for index, sql in enumerate(statements)
        if "ix_ops_alerts_last_seen_at" in sql
    )
    ru_first = next(
        index
        for index, sql in enumerate(statements)
        if "CREATE TABLE IF NOT EXISTS ru_probe_runs" in sql
    )
    assert ru_first == admin_last + 1


def test_sqlite_autoincrement_guard_rejects_missing_keyword(migrated_engine) -> None:
    with migrated_engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT name, sql FROM sqlite_master "
                "WHERE type = 'table' AND name IN "
                "('ru_probe_runs', 'ru_probe_target_results', "
                "'ru_probe_uploader_heartbeats', 'internal_ingest_nonces')"
            )
        ).fetchall()
    table_sql = {str(row[0]): str(row[1]) for row in rows}
    mutated_table_sql = dict(table_sql)
    mutated_table_sql["ru_probe_runs"] = mutated_table_sql[
        "ru_probe_runs"
    ].replace(" AUTOINCREMENT", "", 1)
    assert mutated_table_sql != table_sql

    _assert_sqlite_autoincrement_contract(table_sql)
    with pytest.raises(AssertionError):
        _assert_sqlite_autoincrement_contract(mutated_table_sql)


def test_admin_action_intent_migration_contract(tmp_path: Path) -> None:
    table_name = "admin_action_intents"
    expected_indexes = {
        "ix_admin_action_intents_actor": ("actor_tg_id",),
        "ix_admin_action_intents_status": ("status",),
        "ix_admin_action_intents_expires_at": ("expires_at",),
        "ix_admin_action_intents_action": ("action",),
        "ix_admin_action_intents_target": ("target_type", "target_id"),
    }
    engine = create_engine(
        f"sqlite:///{(tmp_path / 'admin-action-intent-migration.db').as_posix()}"
    )
    bootstrap_tables = [
        table
        for table in models.Base.metadata.sorted_tables
        if table.name not in RU_TABLES | {table_name}
    ]
    models.Base.metadata.create_all(engine, tables=bootstrap_tables)
    migrations.run_migrations(engine)
    migrations.run_migrations(engine)
    inspector = inspect(engine)
    model_table = models.Base.metadata.tables[table_name]
    assert set(inspector.get_table_names()) >= {table_name, "admin_audit"}
    assert {column["name"] for column in inspector.get_columns(table_name)} == set(
        model_table.c.keys()
    )
    assert _unique_constraints(inspector, table_name) == {
        "uq_admin_action_intents_idempotency": ("client_idempotency_key",)
    }
    assert _indexes(inspector, table_name) == expected_indexes
    foreign_keys = inspector.get_foreign_keys(table_name)
    assert foreign_keys == [
        {
            **foreign_keys[0],
            "name": "fk_admin_action_intents_audit",
            "constrained_columns": ["admin_audit_id"],
            "referred_table": "admin_audit",
            "referred_columns": ["id"],
            "options": {"ondelete": "RESTRICT"},
        }
    ]
    model_fk = next(iter(model_table.c.admin_audit_id.foreign_keys))
    assert model_fk.name == "fk_admin_action_intents_audit"
    assert model_fk.ondelete == "RESTRICT"
    assert {
        str(index.name): tuple(index.columns.keys()) for index in model_table.indexes
    } == expected_indexes

    with engine.begin() as conn:
        audit_id = int(
            conn.execute(
                text(
                    "INSERT INTO admin_audit(actor_tg_id, action, meta, created_at) "
                    "VALUES (9999, 'intent-test', '{}', CURRENT_TIMESTAMP)"
                )
            ).lastrowid
        )
        values = {
            "id": "00000000-0000-4000-8000-000000000001",
            "actor": 9999,
            "action": "node.disable",
            "target_type": "node",
            "target_id": "nl",
            "risk": "L3",
            "executor": "db",
            "payload": '{"force":false}',
            "hash": "a" * 64,
            "preview": '{"summary":"safe"}',
            "snapshot_hash": "b" * 64,
            "challenge_kind": "exact_node_code",
            "challenge_hash": "c" * 64,
            "version_hash": "d" * 64,
            "expires": "2026-07-17T12:10:00+00:00",
            "key": "00000000-0000-4000-8000-000000000002",
            "audit_id": audit_id,
        }
        insert_sql = text(
            """
            INSERT INTO admin_action_intents(
              id, actor_tg_id, action, target_type, target_id, risk_level,
              executor_kind, canonical_payload_json, payload_hash,
              preview_snapshot_json, snapshot_hash, confirmation_challenge_kind,
              confirmation_challenge_hash, entity_version_hash, expires_at,
              client_idempotency_key, admin_audit_id
            ) VALUES (
              :id, :actor, :action, :target_type, :target_id, :risk,
              :executor, :payload, :hash, :preview, :snapshot_hash,
              :challenge_kind, :challenge_hash, :version_hash, :expires,
              :key, :audit_id
            )
            """
        )
        conn.execute(insert_sql, values)
        with pytest.raises(IntegrityError):
            conn.execute(insert_sql, {**values, "id": str(uuid.uuid4())})
    with engine.begin() as conn:
        with pytest.raises(IntegrityError):
            conn.execute(
                text("DELETE FROM admin_audit WHERE id = :audit_id"),
                {"audit_id": audit_id},
            )
    engine.dispose()

    class RecordingConnection:
        def __init__(self) -> None:
            self.statements: list[str] = []

        def execute(self, statement):
            self.statements.append(" ".join(str(statement).split()))

    recorder = RecordingConnection()
    migrations._ensure_admin_action_intent_domain_postgres(recorder)
    postgres_sql = "\n".join(recorder.statements)
    assert "CREATE TABLE IF NOT EXISTS admin_action_intents" in postgres_sql
    assert "CONSTRAINT uq_admin_action_intents_idempotency" in postgres_sql
    assert "CONSTRAINT fk_admin_action_intents_audit" in postgres_sql
    assert "ON DELETE RESTRICT" in postgres_sql
    assert all(name in postgres_sql for name in expected_indexes)

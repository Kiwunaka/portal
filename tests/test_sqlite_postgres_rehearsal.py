from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, event, select
from sqlalchemy.orm import Session


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


from models import Account, AccountDevice, AccountIdentity, AppSetting, Base, EntitlementGrant, User  # noqa: E402


def _load_script():
    module_path = REPO_ROOT / "scripts" / "migrate_sqlite_to_postgres.py"
    spec = importlib.util.spec_from_file_location("migrate_sqlite_to_postgres_rehearsal", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_snapshot_sqlite_uses_consistent_backup_and_quick_check(monkeypatch, tmp_path: Path) -> None:
    module = _load_script()
    source = tmp_path / "source.db"
    snapshot = tmp_path / "snapshot.db"
    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        connection.execute("INSERT INTO sample(value) VALUES ('alpha'), ('beta')")
        connection.commit()

    monkeypatch.setattr(Path, "read_bytes", lambda _path: (_ for _ in ()).throw(AssertionError("hash must stream")))
    report = module.snapshot_sqlite(source, snapshot)

    assert report["quick_check"] == "ok"
    assert len(report["sha256"]) == 64
    assert report["size_bytes"] > 0
    assert report["source_name"] == "source.db"
    assert report["snapshot_name"] == "snapshot.db"
    with sqlite3.connect(snapshot) as connection:
        assert connection.execute("SELECT value FROM sample ORDER BY id").fetchall() == [("alpha",), ("beta",)]


def test_snapshot_sqlite_refuses_to_overwrite_existing_snapshot(tmp_path: Path) -> None:
    module = _load_script()
    source = tmp_path / "source.db"
    snapshot = tmp_path / "snapshot.db"
    source.touch()
    snapshot.write_bytes(b"retain-me")

    with pytest.raises(module.RehearsalError, match="already exists"):
        module.snapshot_sqlite(source, snapshot)

    assert snapshot.read_bytes() == b"retain-me"


def test_rehearsal_target_guard_requires_confirmed_disposable_postgres_name() -> None:
    module = _load_script()
    url = "postgresql+psycopg2://operator:secret@localhost/portal_rehearsal"

    identity = module.validate_rehearsal_target(
        url,
        confirm_target="portal_rehearsal",
        reset_target=True,
    )

    assert identity == {"dialect": "postgresql", "database": "portal_rehearsal"}
    assert "secret" not in json.dumps(identity)

    with pytest.raises(module.RehearsalError, match="disposable"):
        module.validate_rehearsal_target(
            "postgresql://operator:secret@localhost/portal",
            confirm_target="portal",
            reset_target=True,
        )
    with pytest.raises(module.RehearsalError, match="confirmation"):
        module.validate_rehearsal_target(
            url,
            confirm_target="wrong_rehearsal",
            reset_target=True,
        )
    with pytest.raises(module.RehearsalError, match="reset-target"):
        module.validate_rehearsal_target(
            url,
            confirm_target="portal_rehearsal",
            reset_target=False,
        )
    with pytest.raises(module.RehearsalError, match="PostgreSQL"):
        module.validate_rehearsal_target(
            "sqlite:///target_rehearsal.db",
            confirm_target="target_rehearsal",
            reset_target=True,
        )


def test_table_plan_is_stable_and_respects_declared_dependencies() -> None:
    module = _load_script()
    names = {
        "support_ticket_messages",
        "support_tickets",
        "antiabuse_actions",
        "antiabuse_cases",
        "points_ledger",
        "pay_attempts",
        "offers",
        "account_devices",
        "accounts",
        "users",
        "z_standalone",
        "a_standalone",
    }

    first = module.build_table_plan(names)
    second = module.build_table_plan(reversed(sorted(names)))

    assert first == second
    assert first.index("accounts") < first.index("account_devices")
    assert first.index("antiabuse_cases") < first.index("antiabuse_actions")
    assert first.index("support_tickets") < first.index("support_ticket_messages")
    assert first.index("offers") < first.index("pay_attempts") < first.index("points_ledger")
    assert first.index("a_standalone") < first.index("z_standalone")


def test_legacy_truncate_scope_remains_limited_to_shared_source_tables() -> None:
    module = _load_script()
    shared_plan = ["users", "nodes"]

    assert module.legacy_reset_table_names(shared_plan, truncate_target=True) == shared_plan
    assert module.legacy_reset_table_names(shared_plan, truncate_target=False) == []


def test_copy_table_streams_fetchmany_without_loading_all_rows() -> None:
    module = _load_script()
    metadata = MetaData()
    source_table = Table("sample", metadata, Column("id", Integer, primary_key=True), Column("value", String(40)))
    target_table = Table("sample", MetaData(), Column("id", Integer, primary_key=True), Column("value", String(40)))

    class _StreamingResult:
        def __init__(self) -> None:
            self.rows = [{"id": index, "value": f"value-{index}"} for index in range(1, 6)]
            self.offset = 0

        def mappings(self):
            return self

        def fetchmany(self, size: int):
            chunk = self.rows[self.offset : self.offset + size]
            self.offset += len(chunk)
            return chunk

        def all(self):
            raise AssertionError("streaming copy must not call all()")

    class _SourceConnection:
        def __init__(self) -> None:
            self.result = _StreamingResult()

        def execute(self, statement):
            assert statement.get_execution_options().get("stream_results") is True
            return self.result

    class _TargetConnection:
        def __init__(self) -> None:
            self.batch_sizes: list[int] = []

        def execute(self, _statement, payload):
            self.batch_sizes.append(len(payload))

    target = _TargetConnection()
    report = module.copy_table_streaming(
        _SourceConnection(),
        target,
        source_table=source_table,
        target_table=target_table,
        common_columns=("id", "value"),
        chunk_size=2,
    )

    assert report == {"source_count": 5, "loaded_count": 5, "batches": 3}
    assert target.batch_sizes == [2, 2, 1]


def test_transactional_replace_rolls_back_target_reset_on_postprocess_failure(tmp_path: Path) -> None:
    module = _load_script()
    metadata = MetaData()
    sample = Table("sample", metadata, Column("id", Integer, primary_key=True), Column("value", String(40)))
    source_engine = create_engine(f"sqlite:///{(tmp_path / 'source.db').as_posix()}")
    target_engine = create_engine(f"sqlite:///{(tmp_path / 'target.db').as_posix()}")
    metadata.create_all(source_engine)
    metadata.create_all(target_engine)
    with source_engine.begin() as connection:
        connection.execute(sample.insert(), [{"id": 2, "value": "new"}])
    with target_engine.begin() as connection:
        connection.execute(sample.insert(), [{"id": 1, "value": "retain-on-rollback"}])

    def _fail(_connection):
        raise RuntimeError("postprocess failed")

    with pytest.raises(RuntimeError, match="postprocess failed"):
        module.copy_database_transactional(
            source_engine,
            target_engine,
            target_metadata=metadata,
            table_plan=["sample"],
            reset_table_names=["sample"],
            chunk_size=10,
            postprocess=_fail,
        )

    with target_engine.connect() as connection:
        assert connection.execute(select(sample.c.id, sample.c.value)).all() == [(1, "retain-on-rollback")]


def test_transactional_replace_rejects_unapproved_final_count_delta(tmp_path: Path) -> None:
    module = _load_script()
    metadata = MetaData()
    sample = Table("sample", metadata, Column("id", Integer, primary_key=True), Column("value", String(40)))
    source_engine = create_engine(f"sqlite:///{(tmp_path / 'count-source.db').as_posix()}")
    target_engine = create_engine(f"sqlite:///{(tmp_path / 'count-target.db').as_posix()}")
    metadata.create_all(source_engine)
    metadata.create_all(target_engine)
    with source_engine.begin() as connection:
        connection.execute(sample.insert(), [{"id": 2, "value": "new"}])
    with target_engine.begin() as connection:
        connection.execute(sample.insert(), [{"id": 1, "value": "retain-on-rollback"}])

    def _delete_copied_row(connection):
        connection.execute(sample.delete())
        return {"deleted": 1}

    with pytest.raises(module.RehearsalError, match="row count"):
        module.copy_database_transactional(
            source_engine,
            target_engine,
            target_metadata=metadata,
            table_plan=["sample"],
            reset_table_names=["sample"],
            chunk_size=10,
            postprocess=_delete_copied_row,
        )

    with target_engine.connect() as connection:
        assert connection.execute(select(sample.c.id, sample.c.value)).all() == [(1, "retain-on-rollback")]


def test_sequence_sync_runs_after_explicit_copy_and_before_postprocess(monkeypatch, tmp_path: Path) -> None:
    module = _load_script()
    metadata = MetaData()
    sample = Table("sample", metadata, Column("id", Integer, primary_key=True))
    source_engine = create_engine(f"sqlite:///{(tmp_path / 'sequence-source.db').as_posix()}")
    target_engine = create_engine(f"sqlite:///{(tmp_path / 'sequence-target.db').as_posix()}")
    metadata.create_all(source_engine)
    metadata.create_all(target_engine)
    with source_engine.begin() as connection:
        connection.execute(sample.insert(), [{"id": 10}])
    events: list[str] = []

    def _sync(connection, received_metadata):
        assert received_metadata is metadata
        assert connection.execute(select(sample.c.id)).scalar_one() == 10
        events.append("sequence_sync")
        return []

    def _postprocess(_connection):
        events.append("postprocess")
        return {}

    monkeypatch.setattr(module, "sync_owned_sequences_connection", _sync)
    module.copy_database_transactional(
        source_engine,
        target_engine,
        target_metadata=metadata,
        table_plan=["sample"],
        reset_table_names=["sample"],
        chunk_size=10,
        postprocess=_postprocess,
    )

    assert events == ["sequence_sync", "postprocess"]


def test_incomplete_source_inventory_is_rejected_before_target_reset(tmp_path: Path) -> None:
    module = _load_script()
    source_metadata = MetaData()
    Table("app_settings", source_metadata, Column("key", String(128), primary_key=True))
    source_engine = create_engine(f"sqlite:///{(tmp_path / 'incomplete-source.db').as_posix()}")
    target_engine = create_engine(f"sqlite:///{(tmp_path / 'incomplete-target.db').as_posix()}")
    source_metadata.create_all(source_engine)
    Base.metadata.create_all(target_engine)

    with pytest.raises(module.RehearsalError, match="required source tables"):
        module.run_rehearsal_once(
            source_engine,
            target_engine,
            target_metadata=Base.metadata,
            chunk_size=25,
            allow_non_postgres=True,
        )


def test_expected_source_counts_must_match_snapshot_inventory(tmp_path: Path) -> None:
    module = _load_script()
    source_engine = create_engine(f"sqlite:///{(tmp_path / 'inventory-source.db').as_posix()}")
    Base.metadata.create_all(source_engine)
    with Session(source_engine) as session:
        session.add(
            User(
                tg_id=1001,
                uuid="00000000-0000-0000-0000-000000001001",
                email="USER_1001@telegram.local",
            )
        )
        session.commit()
    inventory = module.source_table_counts(source_engine)
    inventory["users"] += 1

    with pytest.raises(module.RehearsalError, match="source count manifest"):
        module.validate_source_inventory(source_engine, expected_counts=inventory)


@pytest.mark.parametrize("invalid_count", [True, "1", 1.9])
def test_source_manifest_requires_exact_json_integer_counts(tmp_path: Path, invalid_count) -> None:
    module = _load_script()
    manifest = tmp_path / "invalid-counts.json"
    manifest.write_text(
        json.dumps({"table_counts": {"users": invalid_count}}),
        encoding="utf-8",
    )

    with pytest.raises(module.RehearsalError, match="invalid count"):
        module.load_source_count_manifest(manifest)


def test_synthetic_rehearsal_backfills_accounts_and_is_idempotent(tmp_path: Path) -> None:
    module = _load_script()
    source_engine = create_engine(f"sqlite:///{(tmp_path / 'source-full.db').as_posix()}")
    target_engine = create_engine(f"sqlite:///{(tmp_path / 'target-full.db').as_posix()}")
    Base.metadata.create_all(source_engine)
    Base.metadata.create_all(target_engine)
    with Session(source_engine) as session:
        session.add(
            User(
                tg_id=1001,
                username="migration_user",
                uuid="00000000-0000-0000-0000-000000001001",
                email="USER_1001@telegram.local",
                sub_type="FREE",
                is_active=True,
                trial_used=True,
                app_install_id="migration-install",
                app_device_name="Migration device",
                app_platform="android",
            )
        )
        session.commit()

    rehearsal_now = datetime(2026, 7, 12, 15, 0, 0)
    first = module.run_rehearsal_once(
        source_engine,
        target_engine,
        target_metadata=Base.metadata,
        chunk_size=25,
        allow_non_postgres=True,
        rehearsal_now=rehearsal_now,
    )
    second = module.run_rehearsal_once(
        source_engine,
        target_engine,
        target_metadata=Base.metadata,
        chunk_size=25,
        allow_non_postgres=True,
        rehearsal_now=rehearsal_now,
    )

    assert first["status"] == "PASS"
    assert second["status"] == "PASS"
    assert first["normalized_digest"] == second["normalized_digest"]
    assert first["content_digest"] == second["content_digest"]
    assert first["postprocess"]["account_backfill"]["users_seen"] == 1
    assert all(check["status"] == "PASS" for check in second["invariants"])
    full_report_path = tmp_path / "full-rehearsal-report.json"
    module.write_report_atomic(full_report_path, {"status": "PASS", "migration": second})
    assert json.loads(full_report_path.read_text(encoding="utf-8"))["status"] == "PASS"
    with Session(target_engine) as session:
        assert session.query(Account).count() == 1
        assert session.query(AccountIdentity).count() >= 2
        assert session.query(AccountDevice).count() == 1
        assert session.query(EntitlementGrant).count() == 1
        assert session.query(User).filter(User.account_id.is_(None)).count() == 0
        marker = session.query(AppSetting).filter_by(key="migration.account_foundation.v1").one()
        marker_payload = json.loads(marker.value_json)
        assert marker_payload["status"] == "complete"
        assert marker_payload["report"]["users_seen"] == 1


def test_prepare_target_schema_runs_create_all_and_runtime_migrations(tmp_path: Path) -> None:
    module = _load_script()
    metadata = MetaData()
    Table("sample", metadata, Column("id", Integer, primary_key=True))
    engine = create_engine(f"sqlite:///{(tmp_path / 'schema.db').as_posix()}")
    calls: list[Engine] = []

    module.prepare_target_schema(
        engine,
        metadata,
        run_migrations=lambda received: calls.append(received),
    )

    assert calls == [engine]
    assert "sample" in set(module.inspect(engine).get_table_names())


def test_rehearse_cli_failure_report_redacts_target_url(monkeypatch, tmp_path: Path) -> None:
    module = _load_script()
    report_path = tmp_path / "failure.json"
    monkeypatch.setenv(
        "REHEARSAL_POSTGRES_URL",
        "postgresql://operator:super-secret@localhost/portal",
    )

    with pytest.raises(SystemExit, match="rehearsal failed"):
        module.main(
            [
                "rehearse",
                "--sqlite-path",
                str(tmp_path / "source.db"),
                "--snapshot-path",
                str(tmp_path / "snapshot.db"),
                "--source-manifest",
                str(tmp_path / "source-counts.json"),
                "--confirm-target",
                "portal",
                "--reset-target",
                "--report",
                str(report_path),
            ]
        )

    raw_report = report_path.read_text(encoding="utf-8")
    assert "super-secret" not in raw_report
    assert "postgresql://" not in raw_report
    assert json.loads(raw_report)["status"] == "FAIL"


def test_invariants_report_orphan_without_exposing_rows(tmp_path: Path) -> None:
    module = _load_script()
    metadata = MetaData()
    accounts = Table("accounts", metadata, Column("id", String(36), primary_key=True))
    users = Table(
        "users",
        metadata,
        Column("tg_id", Integer, primary_key=True),
        Column("account_id", String(36)),
    )
    engine = create_engine(f"sqlite:///{(tmp_path / 'invariants.db').as_posix()}")
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(accounts.insert(), [{"id": "account-ok"}])
        connection.execute(users.insert(), [{"tg_id": 1, "account_id": "missing-account"}])
        checks = module.run_invariant_checks(connection, metadata)

    orphan_check = next(check for check in checks if check["name"] == "users.account_id->accounts.id")
    assert orphan_check == {"name": "users.account_id->accounts.id", "status": "FAIL", "violations": 1}
    assert "missing-account" not in json.dumps(checks)


def test_invariants_cover_security_key_provisioning_and_payment_chains(tmp_path: Path) -> None:
    module = _load_script()
    metadata = MetaData()
    Table("accounts", metadata, Column("id", String(36), primary_key=True))
    Table("account_devices", metadata, Column("id", String(36), primary_key=True), Column("account_id", String(36)))
    Table(
        "auth_sessions",
        metadata,
        Column("id", String(36), primary_key=True),
        Column("account_id", String(36)),
        Column("device_id", String(36)),
    )
    antiabuse_events = Table(
        "antiabuse_events",
        metadata,
        Column("id", String(36), primary_key=True),
        Column("account_id", String(36)),
        Column("device_id", String(36)),
        Column("session_id", String(36)),
    )
    antiabuse_cases = Table(
        "antiabuse_cases",
        metadata,
        Column("id", String(36), primary_key=True),
        Column("account_id", String(36)),
    )
    antiabuse_actions = Table(
        "antiabuse_actions",
        metadata,
        Column("id", String(36), primary_key=True),
        Column("case_id", String(36)),
        Column("account_id", String(36)),
    )
    Table("users", metadata, Column("tg_id", Integer, primary_key=True), Column("account_id", String(36)))
    Table("nodes", metadata, Column("id", Integer, primary_key=True), Column("code", String(32)))
    Table("access_keys", metadata, Column("id", Integer, primary_key=True), Column("tg_id", Integer), Column("node_code", String(32)))
    key_pressure = Table("key_pressure_state", metadata, Column("key_id", Integer, primary_key=True))
    provisioning = Table(
        "node_provisioning_jobs",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("tg_id", Integer),
        Column("key_id", Integer),
        Column("node_code", String(32)),
    )
    Table(
        "external_orders",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("provider", String(32)),
        Column("order_id", String(128)),
    )
    payment_events = Table(
        "external_payment_events",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("provider", String(32)),
        Column("order_id", String(128)),
    )
    engine = create_engine(f"sqlite:///{(tmp_path / 'critical-invariants.db').as_posix()}")
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(
            antiabuse_events.insert(),
            [{"id": "event", "account_id": "missing", "device_id": "missing", "session_id": "missing"}],
        )
        connection.execute(antiabuse_cases.insert(), [{"id": "case", "account_id": "missing"}])
        connection.execute(
            antiabuse_actions.insert(),
            [{"id": "action", "case_id": "missing-case", "account_id": "missing"}],
        )
        connection.execute(key_pressure.insert(), [{"key_id": 999}])
        connection.execute(
            provisioning.insert(),
            [{"id": 1, "tg_id": 999, "key_id": 999, "node_code": "missing-node"}],
        )
        connection.execute(
            payment_events.insert(),
            [{"id": 1, "provider": "provider", "order_id": "missing-order"}],
        )
        checks = module.run_invariant_checks(connection, metadata)

    failed_names = {check["name"] for check in checks if check["status"] == "FAIL"}
    assert {
        "antiabuse_events.account_id->accounts.id",
        "antiabuse_events.device_id->account_devices.id",
        "antiabuse_events.session_id->auth_sessions.id",
        "antiabuse_cases.account_id->accounts.id",
        "antiabuse_actions.account_id->accounts.id",
        "key_pressure_state.key_id->access_keys.id",
        "node_provisioning_jobs.tg_id->users.tg_id",
        "node_provisioning_jobs.key_id->access_keys.id",
        "node_provisioning_jobs.node_code->nodes.code",
        "external_payment_events.(provider,order_id)->external_orders.(provider,order_id)",
    }.issubset(failed_names)


def test_content_digest_changes_when_row_value_changes(tmp_path: Path) -> None:
    module = _load_script()
    metadata = MetaData()
    sample = Table("sample", metadata, Column("id", Integer, primary_key=True), Column("value", String(40)))
    engine = create_engine(f"sqlite:///{(tmp_path / 'content-digest.db').as_posix()}")
    metadata.create_all(engine)
    stream_flags: list[bool] = []

    @event.listens_for(engine, "before_cursor_execute")
    def _capture_stream_flag(_conn, _cursor, _statement, _parameters, context, _executemany):
        if str(_statement).lstrip().upper().startswith("SELECT"):
            stream_flags.append(bool(context.execution_options.get("stream_results")))

    with engine.begin() as connection:
        connection.execute(sample.insert(), [{"id": 1, "value": "first"}])
    first = module.database_content_digest(engine, metadata, ["sample"])
    with engine.begin() as connection:
        connection.execute(sample.update().values(value="second"))
    second = module.database_content_digest(engine, metadata, ["sample"])

    assert first != second
    assert stream_flags and all(stream_flags)


def test_report_digest_ignores_volatile_fields_and_atomic_writer_rejects_secrets(tmp_path: Path) -> None:
    module = _load_script()
    first = {"status": "PASS", "generated_at": "one", "snapshot": {"sha256": "abc"}, "counts": {"users": 1}}
    second = {"status": "PASS", "generated_at": "two", "snapshot": {"sha256": "abc"}, "counts": {"users": 1}}
    assert module.normalized_report_digest(first) == module.normalized_report_digest(second)

    report_path = tmp_path / "reports" / "rehearsal.json"
    module.write_report_atomic(report_path, first)
    assert json.loads(report_path.read_text(encoding="utf-8"))["status"] == "PASS"
    assert not list(report_path.parent.glob("*.tmp"))

    with pytest.raises(module.RehearsalError, match="sensitive"):
        module.write_report_atomic(
            tmp_path / "unsafe.json",
            {"target": "postgresql://operator:secret@db/portal_rehearsal"},
        )
    with pytest.raises(module.RehearsalError, match="sensitive"):
        module.write_report_atomic(tmp_path / "unsafe-key.json", {"token": "must-not-write"})


def test_safe_error_message_never_copies_database_parameters() -> None:
    module = _load_script()
    raw = "duplicate key DETAIL email=private@example.test [parameters: {'token_hash': 'abc'}]"

    message = module.safe_error_message(RuntimeError(raw))

    assert "private@example.test" not in message
    assert "token_hash" not in message
    assert "abc" not in message


def test_terminal_referral_relationship_keeps_transition_orphan_invariant_green(tmp_path: Path) -> None:
    module = _load_script()
    metadata = MetaData()
    accounts = Table("accounts", metadata, Column("id", String(36), primary_key=True))
    relationships = Table(
        "referral_relationships",
        metadata,
        Column("id", String(36), primary_key=True),
        Column("referred_account_id", String(36)),
        Column("referrer_account_id", String(36)),
    )
    transitions = Table(
        "referral_transitions",
        metadata,
        Column("id", String(36), primary_key=True),
        Column("relationship_id", String(36)),
        Column("referred_account_id", String(36)),
        Column("referrer_account_id", String(36)),
    )
    engine = create_engine(f"sqlite:///{(tmp_path / 'terminal-referral-invariant.db').as_posix()}")
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(accounts.insert(), [{"id": "source"}, {"id": "referrer"}])
        connection.execute(
            relationships.insert(),
            [{"id": "retained-terminal", "referred_account_id": "source", "referrer_account_id": "referrer"}],
        )
        connection.execute(
            transitions.insert(),
            [{
                "id": "retained-transition",
                "relationship_id": "retained-terminal",
                "referred_account_id": "source",
                "referrer_account_id": "referrer",
            }],
        )
        checks = module.run_invariant_checks(connection, metadata)

    relationship_check = next(
        check for check in checks if check["name"] == "referral_transitions.relationship_id->referral_relationships.id"
    )
    assert relationship_check == {
        "name": "referral_transitions.relationship_id->referral_relationships.id",
        "status": "PASS",
        "violations": 0,
    }

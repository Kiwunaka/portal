import importlib
import sqlite3
import sys
from pathlib import Path

from sqlalchemy import create_engine


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

migrations = importlib.import_module("migrations")


def test_sqlite_support_bundle_migration_is_rerunnable_and_bounded(
    tmp_path: Path,
) -> None:
    database = tmp_path / "support-bundle-migration.db"
    engine = create_engine(f"sqlite:///{database.as_posix()}")
    with engine.begin() as connection:
        migrations._ensure_support_bundle_domain_sqlite(connection)
        migrations._ensure_support_bundle_domain_sqlite(connection)
    engine.dispose()

    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        upload_columns = {
            row[1]: row[2]
            for row in connection.execute("PRAGMA table_info(support_bundle_uploads)")
        }
        upload_indexes = {
            row[1]: bool(row[2])
            for row in connection.execute("PRAGMA index_list(support_bundle_uploads)")
        }
        chunk_indexes = {
            row[1]: bool(row[2])
            for row in connection.execute("PRAGMA index_list(support_bundle_chunks)")
        }
        upload_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'support_bundle_uploads'"
        ).fetchone()[0]

    assert {
        "support_bundle_access_audits",
        "support_bundle_uploads",
        "support_bundle_chunks",
    } <= tables
    assert {
        "bundle_id",
        "content_type",
        "expected_sha256",
        "expected_size_bytes",
        "failure_code",
        "diagnostic_profile",
        "app_version",
        "build_number",
        "platform",
        "architecture",
        "last_phase",
        "last_error_code",
        "proof_outcome",
        "observed_attempts",
        "retention_hold",
        "retention_hold_reason",
        "retention_held_at",
        "idempotency_key",
        "object_name",
        "owner_binding_hash",
        "received_size_bytes",
        "status",
        "upload_id",
    } <= set(upload_columns)
    assert upload_indexes["uq_support_bundle_upload_id"] is True
    assert upload_indexes["uq_support_bundle_owner_idempotency"] is True
    assert upload_indexes["uq_support_bundle_ticket_bundle"] is True
    assert chunk_indexes["uq_support_bundle_chunk_offset"] is True
    assert "expected_size_bytes <= 2621440" in upload_sql


class _RecordingConnection:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def execute(self, statement, *_args):
        self.statements.append(" ".join(str(statement).split()))
        return self

    def scalar(self):
        return False


def test_postgres_support_bundle_migration_has_same_uniqueness_and_limits() -> None:
    connection = _RecordingConnection()
    migrations._ensure_support_bundle_domain_postgres(connection)
    rendered = "\n".join(connection.statements)

    assert "CREATE TABLE IF NOT EXISTS support_bundle_uploads" in rendered
    assert "CREATE TABLE IF NOT EXISTS support_bundle_chunks" in rendered
    assert "CREATE TABLE IF NOT EXISTS support_bundle_access_audits" in rendered
    assert "expected_size_bytes <= 2621440" in rendered
    assert "uq_support_bundle_owner_idempotency" in rendered
    assert "uq_support_bundle_ticket_bundle" in rendered
    assert "uq_support_bundle_chunk_offset" in rendered
    assert "uq_support_bundle_access_token_hash" in rendered

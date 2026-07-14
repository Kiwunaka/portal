import importlib.util
import re
import sqlite3
import sys
from pathlib import Path

from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, create_engine


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def _load_rehearsal():
    path = REPO_ROOT / "scripts" / "migrate_sqlite_to_postgres.py"
    spec = importlib.util.spec_from_file_location("support_attachment_rehearsal", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_sqlite_attachment_migration_preserves_legacy_rows_and_is_rerunnable(tmp_path: Path) -> None:
    import migrations
    from models import Base

    database = tmp_path / "support-attachments.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TABLE support_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stored_name VARCHAR(160) NOT NULL UNIQUE,
                owner_tg_id BIGINT NOT NULL,
                owner_account_id VARCHAR(36),
                original_name VARCHAR(160) NOT NULL,
                content_type VARCHAR(80) NOT NULL,
                size_bytes INTEGER NOT NULL,
                media_type VARCHAR(32) NOT NULL,
                created_at DATETIME NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO support_attachments (
                stored_name, owner_tg_id, owner_account_id, original_name,
                content_type, size_bytes, media_type, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "20260714-legacypayload.txt",
                1001,
                None,
                "legacy.txt",
                "text/plain",
                12,
                "file",
                "2026-07-14 10:00:00",
            ),
        )
        connection.commit()

    engine = create_engine(f"sqlite:///{database.as_posix()}")
    Base.metadata.create_all(engine)
    migrations.run_migrations(engine)
    migrations.run_migrations(engine)

    with sqlite3.connect(database) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(support_attachments)")}
        indexes = {
            row[1]: bool(row[2])
            for row in connection.execute("PRAGMA index_list(support_attachments)")
        }
        row = connection.execute(
            """
            SELECT stored_name, owner_tg_id, original_name, ticket_id, message_id,
                   attached_at, expires_at
            FROM support_attachments
            """
        ).fetchone()

    assert {"ticket_id", "message_id", "attached_at", "expires_at"} <= columns
    assert indexes["ix_support_attachments_ticket_id"] is False
    assert indexes["ix_support_attachments_message_id"] is True
    assert indexes["ix_support_attachments_expires_at"] is False
    assert row == (
        "20260714-legacypayload.txt",
        1001,
        "legacy.txt",
        None,
        None,
        None,
        None,
    )


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar(self):
        return self.value


class _RecordingPostgresConnection:
    def __init__(self) -> None:
        self.columns = {("support_attachments", "owner_account_id")}
        self.indexes: dict[str, str] = {}
        self.statements: list[str] = []
        self.legacy_rows = [{"stored_name": "20260714-legacy.txt", "owner_tg_id": 1001}]

    def execute(self, statement, params=None):
        sql = " ".join(str(statement).split())
        self.statements.append(sql)
        if "information_schema.columns" in sql and "SELECT EXISTS" in sql:
            key = (params or {}).get("table_name"), (params or {}).get("column_name")
            return _ScalarResult(key in self.columns)
        alter = re.fullmatch(
            r"ALTER TABLE ([a-z_]+) ADD COLUMN ([a-z_]+) (.+);",
            sql,
            flags=re.IGNORECASE,
        )
        if alter:
            self.columns.add((alter.group(1), alter.group(2)))
            return _ScalarResult(None)
        index = re.fullmatch(
            r"CREATE (UNIQUE )?INDEX IF NOT EXISTS ([a-z_]+) ON .+;",
            sql,
            flags=re.IGNORECASE,
        )
        if index:
            self.indexes.setdefault(index.group(2), sql)
            return _ScalarResult(None)
        raise AssertionError(f"Unexpected PostgreSQL migration statement: {sql}")


def test_postgres_attachment_migration_executes_twice_additively_and_preserves_rows() -> None:
    import migrations

    connection = _RecordingPostgresConnection()
    original_rows = list(connection.legacy_rows)

    migrations._ensure_support_attachment_binding_postgres(connection)
    first_columns = set(connection.columns)
    first_indexes = dict(connection.indexes)
    first_statement_count = len(connection.statements)
    migrations._ensure_support_attachment_binding_postgres(connection)
    second_statements = connection.statements[first_statement_count:]

    assert {
        ("support_attachments", "ticket_id"),
        ("support_attachments", "message_id"),
        ("support_attachments", "attached_at"),
        ("support_attachments", "expires_at"),
    } <= connection.columns
    assert connection.columns == first_columns
    assert connection.indexes == first_indexes
    assert set(connection.indexes) == {
        "ix_support_attachments_ticket_id",
        "ix_support_attachments_message_id",
        "ix_support_attachments_expires_at",
    }
    assert connection.indexes["ix_support_attachments_message_id"].startswith(
        "CREATE UNIQUE INDEX IF NOT EXISTS"
    )
    assert not any(statement.startswith("ALTER TABLE") for statement in second_statements)
    mutating_statements = [
        statement
        for statement in connection.statements
        if not statement.upper().startswith("SELECT")
    ]
    assert all(
        statement.startswith("ALTER TABLE support_attachments ADD COLUMN")
        or statement.startswith("CREATE INDEX IF NOT EXISTS")
        or statement.startswith("CREATE UNIQUE INDEX IF NOT EXISTS")
        for statement in mutating_statements
    )
    forbidden = ("FOREIGN KEY", "DROP ", "RENAME ", "DELETE ", "UPDATE ", "INSERT ", "TRUNCATE ", "CREATE TABLE")
    assert not any(token in statement.upper() for statement in mutating_statements for token in forbidden)
    assert connection.legacy_rows == original_rows


def _support_invariant_metadata() -> MetaData:
    metadata = MetaData()
    Table("support_tickets", metadata, Column("id", Integer, primary_key=True))
    Table(
        "support_ticket_messages",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("ticket_id", Integer, nullable=False),
    )
    Table(
        "support_attachments",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("ticket_id", Integer),
        Column("message_id", Integer),
        Column("attached_at", DateTime),
        Column("stored_name", String(160), nullable=False),
    )
    return metadata


def test_rehearsal_orders_attachment_after_ticket_and_message() -> None:
    module = _load_rehearsal()
    plan = module.build_table_plan(
        {"support_attachments", "support_ticket_messages", "support_tickets"}
    )

    assert plan.index("support_tickets") < plan.index("support_ticket_messages")
    assert plan.index("support_ticket_messages") < plan.index("support_attachments")
    assert {"support_tickets", "support_ticket_messages"} <= module.TABLE_DEPENDENCIES[
        "support_attachments"
    ]


def test_rehearsal_attachment_invariants_report_only_counts_and_status(tmp_path: Path) -> None:
    module = _load_rehearsal()
    metadata = _support_invariant_metadata()
    engine = create_engine(f"sqlite:///{(tmp_path / 'invariants.db').as_posix()}")
    metadata.create_all(engine)
    tickets = metadata.tables["support_tickets"]
    messages = metadata.tables["support_ticket_messages"]
    attachments = metadata.tables["support_attachments"]
    with engine.begin() as connection:
        connection.execute(tickets.insert(), [{"id": 1}, {"id": 2}])
        connection.execute(messages.insert(), [{"id": 10, "ticket_id": 1}])
        connection.execute(
            attachments.insert(),
            [
                {"id": 1, "stored_name": "missing-ticket", "ticket_id": 99, "message_id": 10},
                {"id": 2, "stored_name": "missing-message", "ticket_id": 1, "message_id": 99},
                {"id": 3, "stored_name": "mismatch", "ticket_id": 2, "message_id": 10},
            ],
        )
        checks = module.run_invariant_checks(connection, metadata)

    by_name = {check["name"]: check for check in checks}
    expected = {
        "support_attachments.ticket_id->support_tickets.id": 1,
        "support_attachments.message_id->support_ticket_messages.id": 1,
        "support_attachments.(ticket_id,message_id)->support_ticket_messages.(ticket_id,id)": 3,
    }
    for name, violations in expected.items():
        assert by_name[name] == {"name": name, "status": "FAIL", "violations": violations}

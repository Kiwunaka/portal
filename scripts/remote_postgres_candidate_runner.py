from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import select
import shutil
import socket
import sys
import tarfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import sqlalchemy
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import DBAPIError


GATE_NAME = "postgres_candidate_rehearsal"
LIVE_ENV_PATH = "/root/portal_bot/.env"
POSTGRES_SCHEMA_BOOTSTRAP_LOCK = "pokrov_schema_bootstrap"
ACCOUNT_MARKER = "migration.account_foundation.v1"
SUPPORT_MARKER = "migration.support_account_ownership.v1"
SQL_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
MD5_RE = re.compile(r"^[a-f0-9]{32}$")
COMMIT_RE = re.compile(r"^[a-f0-9]{40}$")
MAX_ARCHIVE_BYTES = 128 * 1024 * 1024
MAX_ARCHIVE_FILES = 20_000
MAX_PROTOCOL_FRAME = 16 * 1024 * 1024
PROBE_COLUMN_PREFIX = "pokrov_gate_lock_probe_"
PROBE_INDEX_PREFIX = "pokrov_gate_lock_probe_idx_"
SAFE_ERROR_RE = re.compile(r"^[a-z0-9_]{1,96}$")
MISSING_COLUMN_PATTERNS = (
    re.compile(r'^column "(?P<column>[a-z_][a-z0-9_]{0,62})" does not exist$', re.IGNORECASE),
    re.compile(
        r'^column (?:[a-z_][a-z0-9_]{0,62}\.)?'
        r'(?P<column>[a-z_][a-z0-9_]{0,62}) does not exist$',
        re.IGNORECASE,
    ),
    re.compile(
        r'^column "(?P<column>[a-z_][a-z0-9_]{0,62})" of relation '
        r'"[a-z_][a-z0-9_]{0,62}" does not exist$',
        re.IGNORECASE,
    ),
)
PRODUCTION_SKIP_LOCKED_CONTRACT = "FOR UPDATE SKIP LOCKED"

COUNT_TABLES = (
    "users",
    "accounts",
    "account_identities",
    "account_devices",
    "auth_sessions",
    "entitlement_grants",
    "account_entitlement_grants",
    "support_tickets",
    "support_ticket_messages",
    "support_attachments",
)
REQUIRED_TABLES = (
    "accounts",
    "account_identities",
    "account_devices",
    "auth_sessions",
    "recovery_codes",
    "entitlement_grants",
    "account_entitlement_grants",
    "payment_entitlement_claims",
    "antiabuse_events",
    "antiabuse_cases",
    "antiabuse_actions",
    "account_merge_reviews",
)
REQUIRED_COLUMNS = (
    ("users", "account_id"),
    ("support_tickets", "account_id"),
    ("support_attachments", "owner_account_id"),
    ("account_entitlement_grants", "account_id"),
)
REQUIRED_INDEXES = (
    "ix_users_account_id",
    "ix_support_tickets_account_id",
    "ix_support_attachments_owner_account_id",
    "ix_support_attachments_ticket_id",
    "ix_support_attachments_message_id",
    "ix_support_attachments_expires_at",
    "uq_account_entitlement_grants_premium_trial_account",
)


class RunnerError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProtocolFrame:
    kind: bytes | None
    payload: bytes
    raw: bytes


class PostgresProtocolParser:
    def __init__(self, *, expect_startup: bool) -> None:
        self._buffer = bytearray()
        self._expect_startup = bool(expect_startup)

    def feed(self, data: bytes) -> list[ProtocolFrame]:
        self._buffer.extend(data)
        frames: list[ProtocolFrame] = []
        while True:
            if self._expect_startup:
                if len(self._buffer) < 4:
                    break
                length = int.from_bytes(self._buffer[:4], "big")
                if length < 8 or length > MAX_PROTOCOL_FRAME:
                    raise RunnerError("malformed_startup")
                if len(self._buffer) < length:
                    break
                raw = bytes(self._buffer[:length])
                del self._buffer[:length]
                frames.append(ProtocolFrame(None, raw[4:], raw))
                self._expect_startup = False
                continue
            if len(self._buffer) < 5:
                break
            length = int.from_bytes(self._buffer[1:5], "big")
            if length < 4 or length > MAX_PROTOCOL_FRAME:
                raise RunnerError("malformed_packet")
            total = 1 + length
            if len(self._buffer) < total:
                break
            raw = bytes(self._buffer[:total])
            del self._buffer[:total]
            frames.append(ProtocolFrame(raw[:1], raw[5:], raw))
        return frames


def _is_frontend_commit(frame: ProtocolFrame) -> bool:
    if frame.kind != b"Q":
        return False
    payload = frame.payload[:-1] if frame.payload.endswith(b"\0") else frame.payload
    try:
        statement = payload.decode("ascii")
    except UnicodeDecodeError:
        return False
    return statement.strip().rstrip(";").strip().upper() == "COMMIT"


class CommitAckDropState:
    def __init__(self) -> None:
        self._frontend = PostgresProtocolParser(expect_startup=True)
        self._backend = PostgresProtocolParser(expect_startup=False)
        self.commit_forwarded = False
        self.response_dropped = False

    def process_frontend(self, data: bytes) -> bytes:
        for frame in self._frontend.feed(data):
            if _is_frontend_commit(frame):
                self.commit_forwarded = True
        return data

    def process_backend(self, data: bytes) -> bytes:
        if self.response_dropped:
            return b""
        delivered = bytearray()
        for frame in self._backend.feed(data):
            command = frame.payload[:-1] if frame.payload.endswith(b"\0") else frame.payload
            is_command_complete = frame.kind == b"C"  # CommandComplete
            if self.commit_forwarded and is_command_complete and command.strip().upper() == b"COMMIT":
                self.response_dropped = True
                continue
            if not self.response_dropped:
                delivered.extend(frame.raw)
        return bytes(delivered)


class CommitAckDropProxy:
    def __init__(self, backend_host: str, backend_port: int) -> None:
        self.backend_host = backend_host
        self.backend_port = int(backend_port)
        self.state = CommitAckDropState()
        self.error_class = ""
        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind(("127.0.0.1", 0))
        self._listener.listen(1)
        self._listener.settimeout(15)
        self.port = int(self._listener.getsockname()[1])
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def join(self, timeout: float = 20) -> None:
        self._thread.join(timeout)
        if self._thread.is_alive():
            self.error_class = self.error_class or "proxy_timeout"
            try:
                self._listener.close()
            except OSError:
                pass
            self._thread.join(2)

    def _run(self) -> None:
        client = None
        backend = None
        try:
            client, _address = self._listener.accept()
            backend = socket.create_connection((self.backend_host, self.backend_port), timeout=10)
            client.settimeout(15)
            backend.settimeout(15)
            sockets = (client, backend)
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                readable, _writable, _errors = select.select(sockets, [], sockets, 1)
                if not readable:
                    continue
                for current in readable:
                    data = current.recv(65536)
                    if not data:
                        return
                    if current is client:
                        backend.sendall(self.state.process_frontend(data))
                    else:
                        delivered = self.state.process_backend(data)
                        if delivered:
                            client.sendall(delivered)
                        if self.state.response_dropped:
                            try:
                                client.shutdown(socket.SHUT_RDWR)
                            except OSError:
                                pass
                            return
            self.error_class = "proxy_deadline"
        except Exception as exc:
            if not self.state.response_dropped:
                self.error_class = type(exc).__name__
        finally:
            for current in (client, backend, self._listener):
                if current is not None:
                    try:
                        current.close()
                    except OSError:
                        pass


def _elapsed_ms(started: float) -> int:
    return max(0, int(round((time.monotonic() - started) * 1000)))


def _read_request() -> dict[str, Any]:
    try:
        value = json.loads(sys.stdin.read())
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RunnerError("request_invalid") from exc
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "source_database",
        "target_database",
        "candidate",
    }:
        raise RunnerError("request_shape")
    source = str(value.get("source_database") or "")
    target = str(value.get("target_database") or "")
    candidate = value.get("candidate")
    if source != "portal" or not SQL_IDENTIFIER_RE.fullmatch(target):
        raise RunnerError("database_guard")
    if not target.endswith("_rehearsal") or target == source:
        raise RunnerError("target_guard")
    if not isinstance(candidate, dict) or set(candidate) != {
        "commit",
        "archive_sha256",
        "runner_sha256",
    }:
        raise RunnerError("candidate_shape")
    if not COMMIT_RE.fullmatch(str(candidate.get("commit") or "")):
        raise RunnerError("candidate_commit")
    if not SHA256_RE.fullmatch(str(candidate.get("archive_sha256") or "")):
        raise RunnerError("candidate_hash")
    if not SHA256_RE.fullmatch(str(candidate.get("runner_sha256") or "")):
        raise RunnerError("runner_hash")
    if value.get("schema_version") != 1:
        raise RunnerError("schema_version")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_extract_candidate(archive_path: Path, destination: Path, expected_hash: str) -> Path:
    if not archive_path.is_file() or archive_path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise RunnerError("archive_size")
    if _sha256(archive_path) != expected_hash:
        raise RunnerError("archive_hash")
    destination.mkdir(mode=0o700)
    file_count = 0
    total_bytes = 0
    with tarfile.open(archive_path, "r:") as archive:
        for member in archive.getmembers():
            raw_name = str(member.name)
            path = PurePosixPath(raw_name)
            if (
                not raw_name
                or raw_name.startswith("/")
                or "\\" in raw_name
                or path.is_absolute()
                or any(part in {"", ".", ".."} for part in path.parts)
                or not path.parts
                or path.parts[0] not in {"portal_bot", "shared"}
                or member.issym()
                or member.islnk()
                or member.isdev()
            ):
                raise RunnerError("archive_member")
            target = destination.joinpath(*path.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True, mode=0o700)
                continue
            if not member.isfile():
                raise RunnerError("archive_type")
            file_count += 1
            total_bytes += int(member.size)
            if file_count > MAX_ARCHIVE_FILES or total_bytes > MAX_ARCHIVE_BYTES:
                raise RunnerError("archive_limits")
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            source = archive.extractfile(member)
            if source is None:
                raise RunnerError("archive_read")
            with source, target.open("xb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            target.chmod(0o600)
    portal = destination / "portal_bot"
    shared = destination / "shared"
    if (
        not (portal / "db.py").is_file()
        or not (portal / "migrations.py").is_file()
        or not (shared / "tariff-catalog.json").is_file()
    ):
        raise RunnerError("candidate_incomplete")
    return portal


def _derive_target_url(source_database: str, target_database: str) -> URL:
    load_dotenv(LIVE_ENV_PATH, override=True)
    raw = str(os.environ.get("DATABASE_URL") or "")
    if not raw:
        raise RunnerError("live_database_url_missing")
    try:
        live = make_url(raw)
    except Exception as exc:
        raise RunnerError("live_database_url_invalid") from exc
    if live.get_backend_name() != "postgresql" or live.database != source_database:
        raise RunnerError("live_database_guard")
    target_url = live.set(database=target_database)
    os.environ["DATABASE_URL"] = target_url.render_as_string(hide_password=False)
    os.environ["PGOPTIONS"] = (
        "-c lock_timeout=5s -c statement_timeout=120s "
        "-c idle_in_transaction_session_timeout=60s"
    )
    return target_url


def _preflight_target(target_url: URL, target_database: str) -> tuple[str, int]:
    control = create_engine(target_url, pool_pre_ping=True, hide_parameters=True)
    try:
        with control.connect() as connection:
            row = connection.exec_driver_sql(
                "SELECT current_database(), COALESCE(inet_server_addr()::text, ''), "
                "COALESCE(inet_server_port(), 0)"
            ).one()
    finally:
        control.dispose()
    if str(row[0]) != target_database:
        raise RunnerError("target_preflight_database")
    return str(row[1]), int(row[2])


def _import_candidate_db(portal_path: Path, target_database: str):
    original_create_engine = sqlalchemy.create_engine

    def guarded_create_engine(url, *args, **kwargs):
        try:
            parsed = make_url(str(url))
        except Exception as exc:
            raise RunnerError("candidate_engine_url") from exc
        if parsed.get_backend_name() != "postgresql" or parsed.database != target_database:
            raise RunnerError("candidate_engine_target")
        return original_create_engine(url, *args, **kwargs)

    sqlalchemy.create_engine = guarded_create_engine
    try:
        sys.path.insert(0, str(portal_path))
        db = importlib.import_module("db")
    finally:
        sqlalchemy.create_engine = original_create_engine
    if db.engine.url.get_backend_name() != "postgresql" or db.engine.url.database != target_database:
        raise RunnerError("candidate_engine_target")
    return db


def _target_access_contract(engine, target_url: URL, target_database: str) -> dict[str, Any]:
    expected_user = str(target_url.username or "")
    if not SQL_IDENTIFIER_RE.fullmatch(expected_user):
        raise RunnerError("target_access_identity")
    statement = text(
        """
WITH app_role AS (
    SELECT oid, rolcanlogin, rolsuper, rolreplication, rolbypassrls
    FROM pg_roles
    WHERE rolname = current_user
), public_objects AS (
    SELECT n.nspowner AS owner_oid
    FROM pg_namespace n
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT c.relowner AS owner_oid
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT p.proowner
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT t.typowner
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT e.extowner
    FROM pg_extension e
    JOIN pg_namespace n ON n.oid = e.extnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT c.collowner
    FROM pg_collation c
    JOIN pg_namespace n ON n.oid = c.collnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT c.conowner
    FROM pg_conversion c
    JOIN pg_namespace n ON n.oid = c.connamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT o.oprowner
    FROM pg_operator o
    JOIN pg_namespace n ON n.oid = o.oprnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT o.opcowner
    FROM pg_opclass o
    JOIN pg_namespace n ON n.oid = o.opcnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT o.opfowner
    FROM pg_opfamily o
    JOIN pg_namespace n ON n.oid = o.opfnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT d.dictowner
    FROM pg_ts_dict d
    JOIN pg_namespace n ON n.oid = d.dictnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT c.cfgowner
    FROM pg_ts_config c
    JOIN pg_namespace n ON n.oid = c.cfgnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT s.stxowner
    FROM pg_statistic_ext s
    JOIN pg_namespace n ON n.oid = s.stxnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT d.defaclrole
    FROM pg_default_acl d
    JOIN pg_namespace n ON n.oid = d.defaclnamespace
    WHERE n.nspname = 'public'
)
SELECT
    current_database() = :target_database AS database_identity,
    current_user = session_user AND current_user = :expected_user AS session_identity,
    COALESCE((
        SELECT rolcanlogin AND NOT rolsuper AND NOT rolreplication AND NOT rolbypassrls
        FROM app_role
    ), false) AS ordinary_login,
    COALESCE((
        SELECT d.datdba = a.oid
        FROM pg_database d CROSS JOIN app_role a
        WHERE d.datname = current_database()
    ), false) AS database_owner,
    NOT EXISTS (
        SELECT 1
        FROM pg_database d
        CROSS JOIN LATERAL aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba))) acl
        WHERE d.datname = current_database() AND acl.grantee = 0
    ) AS database_public_access_revoked,
    has_schema_privilege(current_user, 'public', 'USAGE') AS schema_usage,
    has_schema_privilege(current_user, 'public', 'CREATE') AS schema_create,
    NOT EXISTS (
        SELECT 1
        FROM pg_namespace n
        CROSS JOIN LATERAL aclexplode(COALESCE(n.nspacl, acldefault('n', n.nspowner))) acl
        WHERE n.nspname = 'public' AND acl.grantee = 0
    ) AS schema_public_access_revoked,
    has_table_privilege(current_user, 'public.users', 'SELECT') AS users_select,
    (SELECT count(*) FROM public_objects) AS public_objects_total,
    (
        SELECT count(*)
        FROM public_objects o CROSS JOIN app_role a
        WHERE o.owner_oid = a.oid
    ) AS public_objects_owned
"""
    )
    try:
        with engine.connect() as connection:
            row = connection.execute(
                statement,
                {"target_database": target_database, "expected_user": expected_user},
            ).mappings().one()
    except DBAPIError as exc:
        sqlstate = _sqlstate(exc)
        suffix = sqlstate.lower() if re.fullmatch(r"[A-Z0-9]{5}", sqlstate) else "database"
        raise RunnerError(f"target_access_{suffix}") from None
    boolean_fields = (
        "database_identity",
        "session_identity",
        "ordinary_login",
        "database_owner",
        "database_public_access_revoked",
        "schema_usage",
        "schema_create",
        "schema_public_access_revoked",
        "users_select",
    )
    total = int(row["public_objects_total"])
    owned = int(row["public_objects_owned"])
    if not all(row[field] is True for field in boolean_fields) or total <= 0 or owned != total:
        raise RunnerError("target_access_contract")
    return {
        "status": "PASS",
        **{field: True for field in boolean_fields},
        "public_objects_total": total,
        "public_objects_owned": owned,
    }


def _table_exists(connection, table: str) -> bool:
    return connection.execute(
        text("SELECT to_regclass(:table_name) IS NOT NULL"),
        {"table_name": f"public.{table}"},
    ).scalar_one() is True


def _column_exists(connection, table: str, column: str) -> bool:
    return connection.execute(
        text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=:table_name AND column_name=:column_name)"
        ),
        {"table_name": table, "column_name": column},
    ).scalar_one() is True


def _count(connection, table: str) -> int:
    if table not in COUNT_TABLES and table not in REQUIRED_TABLES:
        raise RunnerError("count_table")
    if not _table_exists(connection, table):
        return 0
    return int(connection.exec_driver_sql(f'SELECT COUNT(*) FROM "{table}"').scalar_one())


def _string_rows(rows) -> list[list[str]]:
    return [["" if value is None else str(value) for value in row] for row in rows]


def _legacy_entitlement_signature(engine) -> dict[str, str]:
    with engine.connect() as connection:
        if not _table_exists(connection, "entitlement_grants"):
            raise RunnerError("legacy_entitlement_grants_missing")
        relation = connection.execute(
            text(
                "SELECT c.relkind, c.relpersistence, c.relreplident, "
                "COALESCE(array_to_string(c.reloptions, ','), '') "
                "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname='public' AND c.relname=:table_name"
            ),
            {"table_name": "entitlement_grants"},
        ).one()
        columns = connection.execute(
            text(
                "SELECT ordinal_position, column_name, data_type, udt_name, "
                "COALESCE(character_maximum_length::text, ''), "
                "COALESCE(numeric_precision::text, ''), "
                "COALESCE(numeric_scale::text, ''), is_nullable, "
                "COALESCE(column_default, '') "
                "FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=:table_name "
                "ORDER BY ordinal_position"
            ),
            {"table_name": "entitlement_grants"},
        ).all()
        indexes = connection.execute(
            text(
                "SELECT indexname, indexdef FROM pg_indexes "
                "WHERE schemaname='public' AND tablename=:table_name "
                "ORDER BY indexname"
            ),
            {"table_name": "entitlement_grants"},
        ).all()
        constraints = connection.execute(
            text(
                "SELECT con.conname, con.contype, pg_get_constraintdef(con.oid, true) "
                "FROM pg_constraint con "
                "WHERE con.conrelid='public.entitlement_grants'::regclass "
                "ORDER BY con.conname"
            )
        ).all()
        triggers = connection.execute(
            text(
                "SELECT trigger.tgname, pg_get_triggerdef(trigger.oid, true) "
                "FROM pg_trigger trigger "
                "WHERE trigger.tgrelid='public.entitlement_grants'::regclass "
                "AND NOT trigger.tgisinternal ORDER BY trigger.tgname"
            )
        ).all()
        row_hashes = connection.exec_driver_sql(
            'SELECT md5(row_to_json(legacy_row)::text) '
            'FROM "entitlement_grants" AS legacy_row ORDER BY 1'
        )
        rows_digest = hashlib.sha256()
        for row in row_hashes:
            row_hash = str(row[0] or "").lower()
            if not MD5_RE.fullmatch(row_hash):
                raise RunnerError("legacy_entitlement_row_hash")
            rows_digest.update(row_hash.encode("ascii"))
            rows_digest.update(b"\n")

    schema_payload = {
        "relation": _string_rows([relation]),
        "columns": _string_rows(columns),
        "indexes": _string_rows(indexes),
        "constraints": _string_rows(constraints),
        "triggers": _string_rows(triggers),
    }
    schema_digest = hashlib.sha256(
        json.dumps(
            schema_payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {
        "status": "PASS",
        "rows_sha256": rows_digest.hexdigest(),
        "schema_sha256": schema_digest,
    }


def _bound_partition(connection, table: str, column: str) -> dict[str, int]:
    total = _count(connection, table)
    if total == 0 or not _column_exists(connection, table, column):
        return {"total": total, "bound": 0, "unbound": total}
    bound = int(
        connection.exec_driver_sql(
            f'SELECT COUNT(*) FROM "{table}" WHERE "{column}" IS NOT NULL'
        ).scalar_one()
    )
    return {"total": total, "bound": bound, "unbound": total - bound}


def _attachment_partition(connection) -> dict[str, int]:
    total = _count(connection, "support_attachments")
    required = all(
        _column_exists(connection, "support_attachments", column)
        for column in ("ticket_id", "message_id")
    )
    if total == 0 or not required:
        return {"total": total, "bound": 0, "unbound": total, "dangling": 0}
    row = connection.exec_driver_sql(
        "SELECT "
        "COUNT(*) FILTER (WHERE ticket_id IS NOT NULL AND message_id IS NOT NULL), "
        "COUNT(*) FILTER (WHERE ticket_id IS NULL AND message_id IS NULL), "
        "COUNT(*) FILTER (WHERE (ticket_id IS NULL) <> (message_id IS NULL)) "
        "FROM support_attachments"
    ).one()
    return {
        "total": total,
        "bound": int(row[0]),
        "unbound": int(row[1]),
        "dangling": int(row[2]),
    }


def _aggregate_counts(engine) -> dict[str, Any]:
    def checked(label: str, operation):
        try:
            return operation()
        except RunnerError:
            raise
        except Exception as exc:
            sqlstate = _sqlstate(exc) if isinstance(exc, DBAPIError) else ""
            error_type = re.sub(
                r"[^a-z0-9_]+",
                "_",
                type(exc).__name__.lower(),
            ).strip("_")
            suffix = f"_{sqlstate.lower()}" if re.fullmatch(r"[A-Z0-9]{5}", sqlstate) else ""
            raise RunnerError(f"counts_{label}_{error_type or 'error'}{suffix}") from None

    with engine.connect() as connection:
        return {
            "users": checked(
                "users",
                lambda: _bound_partition(connection, "users", "account_id"),
            ),
            "accounts": checked("accounts", lambda: _count(connection, "accounts")),
            "account_identities": checked(
                "account_identities",
                lambda: _count(connection, "account_identities"),
            ),
            "account_devices": checked(
                "account_devices",
                lambda: _count(connection, "account_devices"),
            ),
            "auth_sessions": checked(
                "auth_sessions",
                lambda: _count(connection, "auth_sessions"),
            ),
            "entitlement_grants": checked(
                "entitlement_grants",
                lambda: _count(connection, "entitlement_grants"),
            ),
            "account_entitlement_grants": checked(
                "account_entitlement_grants",
                lambda: _count(connection, "account_entitlement_grants"),
            ),
            "support_tickets": checked(
                "support_tickets",
                lambda: _bound_partition(connection, "support_tickets", "account_id"),
            ),
            "support_ticket_messages": checked(
                "support_ticket_messages",
                lambda: _count(connection, "support_ticket_messages"),
            ),
            "support_attachments": checked(
                "support_attachments",
                lambda: _attachment_partition(connection),
            ),
        }


def _tables_present(engine, tables: tuple[str, ...]) -> int:
    with engine.connect() as connection:
        return sum(int(_table_exists(connection, table)) for table in tables)


def _sqlstate(exc: DBAPIError) -> str:
    original = getattr(exc, "orig", None)
    return str(getattr(original, "pgcode", "") or getattr(original, "sqlstate", ""))


def _safe_exception_code(phase: str, exc: BaseException) -> str:
    safe_phase = re.sub(r"[^a-z0-9_]+", "_", str(phase).lower()).strip("_")[:24]
    error_type = re.sub(r"[^a-z0-9_]+", "_", type(exc).__name__.lower()).strip("_")[:24]
    parts = [safe_phase or "runner", error_type or "error"]
    if isinstance(exc, DBAPIError):
        sqlstate = _sqlstate(exc).upper()
        if re.fullmatch(r"[A-Z0-9]{5}", sqlstate):
            parts.append(sqlstate.lower())
        primary = str(
            getattr(getattr(getattr(exc, "orig", None), "diag", None), "message_primary", "")
            or ""
        ).strip()
        for pattern in MISSING_COLUMN_PATTERNS:
            match = pattern.fullmatch(primary)
            if match:
                parts.append(f"column_{match.group('column').lower()[:24]}")
                break
        statement = str(getattr(exc, "statement", "") or "")
        if statement:
            fingerprint = hashlib.sha256(statement.encode("utf-8")).hexdigest()[:10]
            parts.append(f"stmt_{fingerprint}")
    code = "_".join(parts)
    return code if SAFE_ERROR_RE.fullmatch(code) else "runner_error"


def _expect_lock_timeout(engine, holder_sql: str, probe_sql: str) -> tuple[int, str]:
    holder = engine.connect()
    probe = engine.connect()
    holder_tx = holder.begin()
    probe_tx = None
    started = time.monotonic()
    code = ""
    try:
        holder.exec_driver_sql(holder_sql)
        probe_tx = probe.begin()
        probe.exec_driver_sql("SET LOCAL lock_timeout = '750ms'")
        probe.exec_driver_sql("SET LOCAL statement_timeout = '5s'")
        try:
            probe.exec_driver_sql(probe_sql)
        except DBAPIError as exc:
            code = _sqlstate(exc)
        else:
            raise RunnerError("ddl_lock_not_blocked")
    finally:
        if probe_tx is not None:
            probe_tx.rollback()
        holder_tx.rollback()
        probe.close()
        holder.close()
    if not code.startswith("55"):
        raise RunnerError("ddl_lock_sqlstate")
    return _elapsed_ms(started), code[:2]


def _run_ddl_lock_gate(engine, *, probe_column: str, probe_index: str) -> dict[str, Any]:
    if not SQL_IDENTIFIER_RE.fullmatch(probe_column) or not SQL_IDENTIFIER_RE.fullmatch(probe_index):
        raise RunnerError("ddl_probe_identifier")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            f"ALTER TABLE support_attachments DROP COLUMN IF EXISTS {probe_column}"
        )
        connection.exec_driver_sql(f"DROP INDEX IF EXISTS {probe_index}")
    alter_ms, alter_class = _expect_lock_timeout(
        engine,
        "LOCK TABLE support_attachments IN ACCESS SHARE MODE",
        f"ALTER TABLE support_attachments ADD COLUMN {probe_column} INTEGER",
    )
    index_ms, index_class = _expect_lock_timeout(
        engine,
        "LOCK TABLE support_attachments IN ROW EXCLUSIVE MODE",
        f"CREATE INDEX {probe_index} ON support_attachments(id)",
    )
    with engine.connect() as connection:
        column_present = _column_exists(connection, "support_attachments", probe_column)
        index_present = connection.execute(
            text("SELECT to_regclass(:index_name) IS NOT NULL"),
            {"index_name": f"public.{probe_index}"},
        ).scalar_one()
    if column_present or index_present or alter_class != "55" or index_class != "55":
        raise RunnerError("ddl_lock_cleanup")
    return {
        "status": "PASS",
        "milliseconds": max(alter_ms, index_ms),
        "sqlstate_class": "55",
    }


def _run_advisory_lock_gate(engine) -> dict[str, str]:
    holder = engine.connect()
    contender = engine.connect()
    holder_tx = holder.begin()
    contender_tx = contender.begin()
    try:
        holder.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_name))"),
            {"lock_name": POSTGRES_SCHEMA_BOOTSTRAP_LOCK},
        )
        first = contender.execute(
            text("SELECT pg_try_advisory_xact_lock(hashtext(:lock_name))"),
            {"lock_name": POSTGRES_SCHEMA_BOOTSTRAP_LOCK},
        ).scalar_one()
        if first is not False:
            raise RunnerError("advisory_lock_not_exclusive")
        holder_tx.commit()
        second = contender.execute(
            text("SELECT pg_try_advisory_xact_lock(hashtext(:lock_name))"),
            {"lock_name": POSTGRES_SCHEMA_BOOTSTRAP_LOCK},
        ).scalar_one()
        if second is not True:
            raise RunnerError("advisory_lock_not_released")
        contender_tx.commit()
    finally:
        if holder_tx.is_active:
            holder_tx.rollback()
        if contender_tx.is_active:
            contender_tx.rollback()
        holder.close()
        contender.close()
    return {"status": "PASS"}


def _schema_contract(engine) -> dict[str, Any]:
    with engine.connect() as connection:
        tables = sum(int(_table_exists(connection, table)) for table in REQUIRED_TABLES)
        columns = sum(
            int(_column_exists(connection, table, column))
            for table, column in REQUIRED_COLUMNS
        )
        indexes = {
            str(row[0])
            for row in connection.exec_driver_sql(
                "SELECT indexname FROM pg_indexes WHERE schemaname='public'"
            ).all()
        }
        marker_rows = connection.execute(
            text(
                "SELECT key, value_json FROM app_settings "
                "WHERE key IN (:account_marker, :support_marker)"
            ),
            {"account_marker": ACCOUNT_MARKER, "support_marker": SUPPORT_MARKER},
        ).all()
    markers = 0
    for key, raw in marker_rows:
        try:
            payload = json.loads(str(raw or "{}"))
        except (TypeError, ValueError, json.JSONDecodeError):
            payload = {}
        if key in {ACCOUNT_MARKER, SUPPORT_MARKER} and payload.get("status") == "complete":
            markers += 1
    present_indexes = len(set(REQUIRED_INDEXES).intersection(indexes))
    if (
        tables != len(REQUIRED_TABLES)
        or columns != len(REQUIRED_COLUMNS)
        or present_indexes != len(REQUIRED_INDEXES)
        or markers != 2
    ):
        raise RunnerError("schema_contract")
    return {
        "status": "PASS",
        "tables": tables,
        "columns": columns,
        "indexes": present_indexes,
        "markers": markers,
    }


def _assert_preserved(pre: dict[str, Any], post: dict[str, Any]) -> None:
    for name in ("users", "support_tickets", "support_attachments"):
        if pre[name]["total"] != post[name]["total"]:
            raise RunnerError("legacy_total_changed")
    if pre["support_ticket_messages"] != post["support_ticket_messages"]:
        raise RunnerError("legacy_messages_changed")
    if pre["entitlement_grants"] != post["entitlement_grants"]:
        raise RunnerError("legacy_entitlement_grants_changed")
    if pre["legacy_entitlement_grants"] != post["legacy_entitlement_grants"]:
        raise RunnerError("legacy_entitlement_grants_changed")


def _run_migrations(portal_path: Path, target_database: str) -> tuple[Any, dict[str, Any]]:
    sys.path.insert(0, str(portal_path))
    db = importlib.import_module("db")
    with db.engine.connect() as connection:
        current = connection.exec_driver_sql("SELECT current_database()").scalar_one()
    if current != target_database:
        raise RunnerError("candidate_connected_wrong_database")
    first_started = time.monotonic()
    db.init_db()
    first_ms = _elapsed_ms(first_started)
    first_counts = _aggregate_counts(db.engine)
    first_legacy_entitlements = _legacy_entitlement_signature(db.engine)
    schema = _schema_contract(db.engine)
    second_started = time.monotonic()
    db.init_db()
    second_ms = _elapsed_ms(second_started)
    second_counts = _aggregate_counts(db.engine)
    second_legacy_entitlements = _legacy_entitlement_signature(db.engine)
    if first_counts != second_counts or first_legacy_entitlements != second_legacy_entitlements:
        raise RunnerError("migration_not_idempotent")
    return db.engine, {
        "migration_first": {"status": "PASS", "milliseconds": first_ms},
        "migration_second": {"status": "PASS", "milliseconds": second_ms},
        "schema_contract": schema,
        "post_counts": second_counts,
        "legacy_entitlement_grants": second_legacy_entitlements,
    }


def _assert_candidate_support_contract(portal_path: Path) -> None:
    api_source = (portal_path / "api.py").read_text(encoding="utf-8")
    cleanup_source = (portal_path / "support_attachment_cleanup_service.py").read_text(
        encoding="utf-8"
    )
    required_api = (
        "def _resolve_ticket_attachment(",
        "query = query.with_for_update()",
        "def _bind_ticket_attachment(",
        "SupportAttachment.ticket_id.is_(None)",
        "SupportAttachment.message_id.is_(None)",
        "support_attachment_already_bound",
        "os.replace(temp_path, stored_path)",
        "_fsync_parent_directory(stored_path)",
    )
    required_cleanup = (
        "query.with_for_update(skip_locked=True)",
        "_fsync_directory(root)",
    )
    if not all(fragment in api_source for fragment in required_api):
        raise RunnerError("candidate_bind_contract")
    if not all(fragment in cleanup_source for fragment in required_cleanup):
        raise RunnerError("candidate_cleanup_contract")


def _synthetic_name(token: str, suffix: str) -> str:
    return f"20990101-{token[:24]}{suffix}.txt"


def _insert_attachment(connection, *, name: str, owner_tg_id: int, expires_sql: str) -> int:
    if expires_sql not in {"past", "future"}:
        raise RunnerError("synthetic_expiry")
    expiry = "CURRENT_TIMESTAMP - INTERVAL '1 day'" if expires_sql == "past" else "CURRENT_TIMESTAMP + INTERVAL '1 day'"
    statement = text(
        "INSERT INTO support_attachments "
        "(stored_name, owner_tg_id, original_name, content_type, size_bytes, media_type, expires_at, created_at) "
        f"VALUES (:name, :owner_tg_id, :name, 'text/plain', 4, 'file', {expiry}, CURRENT_TIMESTAMP) "
        "RETURNING id"
    )
    return int(connection.execute(statement, {"name": name, "owner_tg_id": owner_tg_id}).scalar_one())


def _run_skip_locked(
    engine,
    *,
    session_factory,
    cleanup_service,
    upload_dir: Path,
    token: str,
    owner_tg_id: int,
) -> dict[str, Any]:
    names = [_synthetic_name(token, suffix) for suffix in ("a", "b", "c")]
    with engine.connect() as connection:
        unrelated_eligible = int(
            connection.exec_driver_sql(
                "SELECT COUNT(*) FROM support_attachments "
                "WHERE ticket_id IS NULL AND message_id IS NULL "
                "AND expires_at IS NOT NULL AND expires_at <= CURRENT_TIMESTAMP"
            ).scalar_one()
        )
    if unrelated_eligible:
        raise RunnerError("skip_locked_nonisolated")
    with engine.begin() as connection:
        for name in names:
            _insert_attachment(connection, name=name, owner_tg_id=owner_tg_id, expires_sql="past")
    holder = engine.connect()
    holder_tx = holder.begin()
    try:
        locked = holder.execute(
            text(
                "SELECT id FROM support_attachments "
                "WHERE ticket_id IS NULL AND message_id IS NULL "
                "AND expires_at IS NOT NULL AND expires_at <= CURRENT_TIMESTAMP "
                "AND stored_name = ANY(:names) ORDER BY id FOR UPDATE LIMIT 1"
            ),
            {"names": names},
        ).scalars().all()
        upload_dir.mkdir(mode=0o700)
        cleanup_report = cleanup_service.reconcile_support_attachments(
            session_factory,
            upload_dir=upload_dir,
            now=datetime.now(timezone.utc).replace(tzinfo=None),
            grace_seconds=60,
            batch_size=2,
            scan_limit=10,
        )
    finally:
        holder_tx.rollback()
        holder.close()
    with engine.connect() as connection:
        remaining = int(
            connection.execute(
                text("SELECT COUNT(*) FROM support_attachments WHERE stored_name = ANY(:names)"),
                {"names": names},
            ).scalar_one()
        )
    selected = int(cleanup_report.get("expired_rows_removed") or 0)
    distinct = selected == 2 and len(locked) == 1 and remaining == 1
    if not distinct:
        raise RunnerError("skip_locked")
    return {"status": "PASS", "selected": 2, "distinct": True}


def _run_bind_retry(engine, *, token: str, owner_tg_id: int) -> dict[str, Any]:
    name = _synthetic_name(token, "bind")
    subject = f"candidate-gate-{token}"
    body = f"candidate-gate-message-{token}"
    with engine.begin() as connection:
        ticket_id = int(
            connection.execute(
                text(
                    "INSERT INTO support_tickets "
                    "(user_tg_id, status, subject, created_at, updated_at) "
                    "VALUES (:owner_tg_id, 'open', :subject, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) "
                    "RETURNING id"
                ),
                {"owner_tg_id": owner_tg_id, "subject": subject},
            ).scalar_one()
        )
        _insert_attachment(connection, name=name, owner_tg_id=owner_tg_id, expires_sql="future")

    def bind_once() -> str:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                row = connection.execute(
                    text(
                        "SELECT id, ticket_id, message_id FROM support_attachments "
                        "WHERE stored_name=:name FOR UPDATE"
                    ),
                    {"name": name},
                ).mappings().one()
                if row["ticket_id"] is not None or row["message_id"] is not None:
                    transaction.commit()
                    return "already_bound"
                message_id = int(
                    connection.execute(
                        text(
                            "INSERT INTO support_ticket_messages "
                            "(ticket_id, sender_tg_id, sender_role, body, created_at) "
                            "VALUES (:ticket_id, :owner_tg_id, 'user', :body, CURRENT_TIMESTAMP) "
                            "RETURNING id"
                        ),
                        {"ticket_id": ticket_id, "owner_tg_id": owner_tg_id, "body": body},
                    ).scalar_one()
                )
                updated = connection.execute(
                    text(
                        "UPDATE support_attachments SET ticket_id=:ticket_id, message_id=:message_id, "
                        "attached_at=CURRENT_TIMESTAMP, expires_at=NULL "
                        "WHERE id=:attachment_id AND ticket_id IS NULL AND message_id IS NULL"
                    ),
                    {
                        "ticket_id": ticket_id,
                        "message_id": message_id,
                        "attachment_id": int(row["id"]),
                    },
                ).rowcount
                if updated != 1:
                    raise RunnerError("bind_update")
                transaction.commit()
                return "winner"
            except Exception:
                if transaction.is_active:
                    transaction.rollback()
                raise

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = [future.result() for future in (executor.submit(bind_once), executor.submit(bind_once))]
    winners = results.count("winner")
    losers = results.count("already_bound")
    with engine.connect() as connection:
        retry_row = connection.execute(
            text("SELECT ticket_id, message_id FROM support_attachments WHERE stored_name=:name FOR UPDATE"),
            {"name": name},
        ).one()
        retry_state = "canonical_existing" if retry_row[0] == ticket_id and retry_row[1] is not None else "invalid"
        messages = int(
            connection.execute(
                text("SELECT COUNT(*) FROM support_ticket_messages WHERE ticket_id=:ticket_id"),
                {"ticket_id": ticket_id},
            ).scalar_one()
        )
    if winners != 1 or losers != 1 or retry_state != "canonical_existing" or messages != 1:
        raise RunnerError("bind_retry")
    return {
        "status": "PASS",
        "winners": 1,
        "losers": 1,
        "loser_state": "already_bound",
        "retry_state": "canonical_existing",
        "messages": 1,
    }


def _run_commit_ack_loss(
    engine,
    target_url: URL,
    *,
    expected_server: tuple[str, int],
    token: str,
    owner_tg_id: int,
) -> dict[str, Any]:
    import psycopg2

    name = _synthetic_name(token, "ack")
    backend_host = str(target_url.host or "127.0.0.1")
    if (
        backend_host not in {"127.0.0.1", "localhost"}
        or target_url.query.get("host")
        or target_url.query.get("service")
    ):
        raise RunnerError("database_not_loopback")
    backend_port = int(target_url.port or 5432)
    proxy = CommitAckDropProxy(backend_host, backend_port)
    proxy.start()
    commit_error = False
    connection = None
    try:
        connection = psycopg2.connect(
            host="127.0.0.1",
            port=proxy.port,
            dbname=target_url.database,
            user=target_url.username,
            password=target_url.password,
            sslmode="disable",
            gssencmode="disable",
            connect_timeout=10,
        )
        cursor = connection.cursor()
        cursor.execute(
            "SELECT current_database(), COALESCE(inet_server_addr()::text, ''), "
            "COALESCE(inet_server_port(), 0)"
        )
        observed_database, observed_address, observed_port = cursor.fetchone()
        if (
            str(observed_database) != str(target_url.database)
            or (str(observed_address), int(observed_port)) != expected_server
        ):
            raise RunnerError("proxy_server_identity")
        cursor.execute(
            "INSERT INTO support_attachments "
            "(stored_name, owner_tg_id, original_name, content_type, size_bytes, media_type, expires_at, created_at) "
            "VALUES (%s, %s, %s, 'text/plain', 4, 'file', CURRENT_TIMESTAMP + INTERVAL '1 day', CURRENT_TIMESTAMP)",
            (name, owner_tg_id, name),
        )
        try:
            connection.commit()
        except Exception:
            commit_error = True
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
        proxy.join()
    with engine.connect() as direct:
        committed_rows = int(
            direct.execute(
                text("SELECT COUNT(*) FROM support_attachments WHERE stored_name=:name"),
                {"name": name},
            ).scalar_one()
        )
    if (
        proxy.error_class
        or not proxy.state.commit_forwarded
        or not proxy.state.response_dropped
        or not commit_error
        or committed_rows != 1
    ):
        raise RunnerError("commit_ack_loss")
    return {
        "status": "PASS",
        "commit_forwarded": True,
        "response_dropped": True,
        "commit_error": True,
        "committed_rows": 1,
    }


def _cleanup_synthetic(
    engine,
    *,
    token: str,
    owner_tg_id: int,
    probe_column: str,
    probe_index: str,
) -> bool:
    name_pattern = f"20990101-{token[:24]}%"
    subject = f"candidate-gate-{token}"
    try:
        with engine.begin() as connection:
            ticket_ids = [
                int(row[0])
                for row in connection.execute(
                    text("SELECT id FROM support_tickets WHERE subject=:subject AND user_tg_id=:owner_tg_id"),
                    {"subject": subject, "owner_tg_id": owner_tg_id},
                ).all()
            ]
            connection.execute(
                text("DELETE FROM support_attachments WHERE stored_name LIKE :name_pattern"),
                {"name_pattern": name_pattern},
            )
            if ticket_ids:
                connection.execute(
                    text("DELETE FROM support_ticket_messages WHERE ticket_id = ANY(:ticket_ids)"),
                    {"ticket_ids": ticket_ids},
                )
                connection.execute(
                    text("DELETE FROM support_tickets WHERE id = ANY(:ticket_ids)"),
                    {"ticket_ids": ticket_ids},
                )
            connection.exec_driver_sql(
                f"ALTER TABLE support_attachments DROP COLUMN IF EXISTS {probe_column}"
            )
            connection.exec_driver_sql(f"DROP INDEX IF EXISTS {probe_index}")
        with engine.connect() as connection:
            rows = int(
                connection.execute(
                    text(
                        "SELECT "
                        "(SELECT COUNT(*) FROM support_attachments WHERE stored_name LIKE :name_pattern) + "
                        "(SELECT COUNT(*) FROM support_tickets WHERE subject=:subject AND user_tg_id=:owner_tg_id)"
                    ),
                    {
                        "name_pattern": name_pattern,
                        "subject": subject,
                        "owner_tg_id": owner_tg_id,
                    },
                ).scalar_one()
            )
            column_present = _column_exists(connection, "support_attachments", probe_column)
            index_present = connection.execute(
                text("SELECT to_regclass(:index_name) IS NOT NULL"),
                {"index_name": f"public.{probe_index}"},
            ).scalar_one()
        return rows == 0 and not column_present and not index_present
    except Exception:
        return False


def run() -> int:
    started = time.monotonic()
    phase = "request"
    engine = None
    token = ""
    owner_tg_id = 0
    probe_column = ""
    probe_index = ""
    cleanup_confirmed = False
    try:
        request = _read_request()
        source_database = str(request["source_database"])
        target_database = str(request["target_database"])
        candidate = dict(request["candidate"])
        scratch = Path(__file__).resolve().parent
        archive_path = scratch / "candidate.tar"
        extracted = scratch / "candidate"
        if _sha256(Path(__file__).resolve()) != str(candidate["runner_sha256"]):
            raise RunnerError("runner_hash_mismatch")
        phase = "archive"
        portal_path = _safe_extract_candidate(
            archive_path,
            extracted,
            str(candidate["archive_sha256"]),
        )
        phase = "target_url"
        target_url = _derive_target_url(source_database, target_database)
        expected_server = _preflight_target(target_url, target_database)
        token = uuid.uuid4().hex
        owner_tg_id = -int(token[:15], 16)
        probe_column = f"{PROBE_COLUMN_PREFIX}{token[:12]}"
        probe_index = f"{PROBE_INDEX_PREFIX}{token[:12]}"
        phase = "candidate_import"
        db = _import_candidate_db(portal_path, target_database)
        engine = db.engine
        with engine.connect() as connection:
            current = connection.exec_driver_sql("SELECT current_database()").scalar_one()
        if current != target_database:
            raise RunnerError("target_database_mismatch")
        phase = "target_access"
        target_access = _target_access_contract(engine, target_url, target_database)
        phase = "pre_counts"
        pre_counts = _aggregate_counts(engine)
        pre_legacy_entitlements = _legacy_entitlement_signature(engine)
        checks: dict[str, Any] = {
            "target_access": target_access,
            "pre_migration": {
                "status": "PASS",
                "schema": {"tables_present": _tables_present(engine, COUNT_TABLES)},
                "counts": pre_counts,
                "legacy_entitlement_grants": pre_legacy_entitlements,
            }
        }
        phase = "ddl_lock"
        checks["ddl_lock_impact"] = _run_ddl_lock_gate(
            engine,
            probe_column=probe_column,
            probe_index=probe_index,
        )
        phase = "advisory_lock"
        checks["advisory_lock"] = _run_advisory_lock_gate(engine)
        phase = "migrations"
        migration_started = time.monotonic()
        engine, migration = _run_migrations(portal_path, target_database)
        checks["migration_first"] = migration["migration_first"]
        checks["migration_second"] = migration["migration_second"]
        checks["schema_contract"] = migration["schema_contract"]
        post_counts = migration["post_counts"]
        post_legacy_entitlements = migration["legacy_entitlement_grants"]
        _assert_preserved(
            {**pre_counts, "legacy_entitlement_grants": pre_legacy_entitlements},
            {**post_counts, "legacy_entitlement_grants": post_legacy_entitlements},
        )
        checks["post_migration"] = {
            "status": "PASS",
            "counts": post_counts,
            "legacy_entitlement_grants": post_legacy_entitlements,
        }
        phase = "candidate_support_contract"
        _assert_candidate_support_contract(portal_path)
        cleanup_service = importlib.import_module("support_attachment_cleanup_service")
        phase = "skip_locked"
        checks["skip_locked"] = _run_skip_locked(
            engine,
            session_factory=db.SessionLocal,
            cleanup_service=cleanup_service,
            upload_dir=scratch / "support-upload-probe",
            token=token,
            owner_tg_id=owner_tg_id,
        )
        phase = "bind_retry"
        checks["bind_retry"] = _run_bind_retry(
            engine,
            token=token,
            owner_tg_id=owner_tg_id,
        )
        phase = "commit_ack_loss"
        checks["commit_ack_loss"] = _run_commit_ack_loss(
            engine,
            target_url,
            expected_server=expected_server,
            token=token,
            owner_tg_id=owner_tg_id,
        )
        if _elapsed_ms(migration_started) <= 0:
            raise RunnerError("migration_duration")
    except RunnerError:
        raise
    except Exception as exc:
        raise RunnerError(_safe_exception_code(phase, exc)) from None
    finally:
        if engine is not None and token and probe_column and probe_index:
            cleanup_confirmed = _cleanup_synthetic(
                engine,
                token=token,
                owner_tg_id=owner_tg_id,
                probe_column=probe_column,
                probe_index=probe_index,
            )
    if not cleanup_confirmed:
        raise RunnerError("synthetic_cleanup")
    report = {
        "schema_version": 1,
        "gate": GATE_NAME,
        "status": "PASS",
        "candidate": {
            "commit": str(candidate["commit"]),
            "archive_sha256": str(candidate["archive_sha256"]),
            "runner_sha256": str(candidate["runner_sha256"]),
        },
        "source_database": source_database,
        "target_database": target_database,
        "checks": checks,
        "durations_ms": {"total": _elapsed_ms(started)},
        "synthetic_cleanup": "confirmed",
    }
    sys.stdout.write(json.dumps(report, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except SystemExit:
        raise
    except Exception as exc:
        raw_code = str(exc) if isinstance(exc, RunnerError) else type(exc).__name__.lower()
        code = raw_code if SAFE_ERROR_RE.fullmatch(raw_code) else "runner_error"
        failure = {
            "schema_version": 1,
            "gate": GATE_NAME,
            "status": "FAIL",
            "error": code,
            "synthetic_cleanup": "unknown",
        }
        sys.stdout.write(json.dumps(failure, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
        raise SystemExit(0) from None

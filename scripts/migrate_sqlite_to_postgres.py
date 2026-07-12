from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import uuid
from collections.abc import Callable, Iterable, Sequence
from contextlib import closing
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import MetaData, Table, create_engine, func, inspect, select, text
from sqlalchemy.engine import Connection, Engine, make_url
from sqlalchemy.orm import Session


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


class RehearsalError(RuntimeError):
    pass


TABLE_DEPENDENCIES: dict[str, set[str]] = {
    "account_identities": {"accounts"},
    "account_devices": {"accounts"},
    "auth_sessions": {"accounts", "account_devices"},
    "recovery_codes": {"accounts"},
    "connection_evidence": {"accounts", "account_devices", "nodes"},
    "entitlement_grants": {"accounts", "connection_evidence"},
    "referral_relationships": {"accounts", "connection_evidence", "entitlement_grants"},
    "referral_transitions": {"referral_relationships", "accounts"},
    "antiabuse_events": {"accounts", "account_devices", "auth_sessions"},
    "antiabuse_cases": {"accounts"},
    "antiabuse_actions": {"antiabuse_cases"},
    "account_merge_reviews": {"accounts"},
    "web_email_tokens": {"web_email_identities"},
    "user_nodes": {"users", "nodes"},
    "access_keys": {"users", "nodes"},
    "node_capacity_policy": {"nodes"},
    "node_runtime_metrics": {"nodes"},
    "node_pool_membership": {"nodes"},
    "node_provisioning_jobs": {"nodes"},
    "provider_traffic_quotas": {"nodes"},
    "provider_traffic_quota_audit": {"provider_traffic_quotas"},
    "key_usage_rollups": {"access_keys"},
    "key_source_observations": {"access_keys"},
    "key_pressure_state": {"access_keys"},
    "rendered_subscription_snapshots": {"subscription_fetch_events"},
    "support_ticket_messages": {"support_tickets"},
    "pay_attempts": {"offers"},
    "points_ledger": {"pay_attempts"},
    "promo_usage": {"promo_codes", "users"},
    "reward_claims": {"users"},
    "family_slots": {"users"},
}

ECONOMY_INVARIANT_RELATIONS = (
    ("connection_evidence", "account_id", "accounts", "id"),
    ("connection_evidence", "device_id", "account_devices", "id"),
    ("connection_evidence", "node_id", "nodes", "id"),
    ("entitlement_grants", "activation_evidence_id", "connection_evidence", "id"),
    ("referral_relationships", "referred_account_id", "accounts", "id"),
    ("referral_relationships", "referrer_account_id", "accounts", "id"),
    ("referral_relationships", "friend_evidence_id", "connection_evidence", "id"),
    ("referral_relationships", "friend_grant_id", "entitlement_grants", "id"),
    ("referral_relationships", "referrer_grant_id", "entitlement_grants", "id"),
    ("referral_transitions", "relationship_id", "referral_relationships", "id"),
)

POSTPROCESS_MUTABLE_TABLES = {
    "accounts",
    "account_identities",
    "account_devices",
    "entitlement_grants",
    "referral_relationships",
    "referral_transitions",
    "account_merge_reviews",
    "app_settings",
}

REQUIRED_SOURCE_TABLES = {
    "users",
    "nodes",
    "app_settings",
}

VOLATILE_REPORT_KEYS = {
    "generated_at",
    "observed_at",
    "duration_seconds",
    "normalized_digest",
}

SENSITIVE_REPORT_RE = re.compile(
    r"(?i)(?:postgresql(?:\+[a-z0-9_]+)?|sqlite)://|"
    r"(?:password|passwd|token|secret|authorization)\s*[:=]"
)
SENSITIVE_REPORT_KEY_RE = re.compile(
    r"(?i)^(?:password|passwd|token|secret|authorization|api[_-]?key|private[_-]?key)(?:$|[_-])"
)
POSTGRES_SCHEMA_BOOTSTRAP_LOCK = "pokrov_schema_bootstrap"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(max(4096, int(chunk_size)))
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _load_models():
    try:
        from portal_bot.models import Base  # type: ignore
    except Exception:
        from models import Base  # type: ignore
    return Base


def _load_runtime_migrations():
    try:
        from portal_bot.migrations import run_migrations  # type: ignore
    except Exception:
        from migrations import run_migrations  # type: ignore
    return run_migrations


def _load_account_backfill():
    try:
        from portal_bot.account_foundation_service import (  # type: ignore
            ACCOUNT_FOUNDATION_BACKFILL_KEY,
            backfill_account_foundation,
        )
    except Exception:
        from account_foundation_service import (  # type: ignore
            ACCOUNT_FOUNDATION_BACKFILL_KEY,
            backfill_account_foundation,
        )
    return backfill_account_foundation, ACCOUNT_FOUNDATION_BACKFILL_KEY


def prepare_target_schema(
    engine: Engine,
    metadata: MetaData,
    *,
    run_migrations: Callable[[Engine], None],
) -> None:
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:lock_name))"),
                {"lock_name": POSTGRES_SCHEMA_BOOTSTRAP_LOCK},
            )
            metadata.create_all(bind=connection)
    else:
        metadata.create_all(bind=engine)
    run_migrations(engine)


def snapshot_sqlite(source_path: Path | str, snapshot_path: Path | str) -> dict[str, Any]:
    source = Path(source_path).resolve()
    snapshot = Path(snapshot_path).resolve()
    if snapshot.exists():
        raise RehearsalError(f"snapshot already exists: {snapshot.name}")
    if source == snapshot:
        raise RehearsalError("snapshot path must differ from source")
    if not source.is_file():
        raise RehearsalError(f"sqlite source does not exist: {source.name}")

    snapshot.parent.mkdir(parents=True, exist_ok=True)
    temporary = snapshot.with_name(f".{snapshot.name}.{uuid.uuid4().hex}.tmp")
    try:
        source_uri = f"{source.as_uri()}?mode=ro"
        with closing(sqlite3.connect(source_uri, uri=True)) as source_connection:
            with closing(sqlite3.connect(temporary)) as snapshot_connection:
                source_connection.backup(snapshot_connection)
                quick_check_row = snapshot_connection.execute("PRAGMA quick_check").fetchone()
                quick_check = str(quick_check_row[0] if quick_check_row else "").strip().lower()
                if quick_check != "ok":
                    raise RehearsalError("sqlite snapshot quick_check failed")
                snapshot_connection.commit()
        os.replace(temporary, snapshot)
        try:
            snapshot.chmod(0o600)
        except OSError:
            pass
    finally:
        temporary.unlink(missing_ok=True)

    digest = _sha256_file(snapshot)
    return {
        "source_name": source.name,
        "snapshot_name": snapshot.name,
        "sha256": digest,
        "size_bytes": int(snapshot.stat().st_size),
        "quick_check": "ok",
    }


def validate_rehearsal_target(
    postgres_url: str,
    *,
    confirm_target: str,
    reset_target: bool,
) -> dict[str, str]:
    try:
        parsed = make_url(str(postgres_url or "").strip())
    except Exception as exc:
        raise RehearsalError("invalid PostgreSQL target URL") from exc
    if parsed.get_backend_name() != "postgresql":
        raise RehearsalError("rehearsal target must use PostgreSQL")
    database = str(parsed.database or "").strip()
    confirmation = str(confirm_target or "").strip()
    if not database.endswith("_rehearsal"):
        raise RehearsalError("target database must be disposable and end with _rehearsal")
    if confirmation != database:
        raise RehearsalError("target confirmation does not match database name")
    if not reset_target:
        raise RehearsalError("rehearsal requires explicit --reset-target")
    return {"dialect": "postgresql", "database": database}


def build_table_plan(table_names: Iterable[str]) -> list[str]:
    pending = {str(name) for name in table_names if str(name).strip()}
    planned: list[str] = []
    while pending:
        ready = sorted(
            name
            for name in pending
            if (TABLE_DEPENDENCIES.get(name, set()) & pending).issubset(set(planned))
        )
        if not ready:
            raise RehearsalError(f"table dependency cycle: {', '.join(sorted(pending))}")
        planned.extend(ready)
        pending.difference_update(ready)
    return planned


def source_table_counts(engine: Engine) -> dict[str, int]:
    table_names = sorted(inspect(engine).get_table_names())
    metadata = MetaData()
    if table_names:
        metadata.reflect(bind=engine, only=table_names)
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            counts = {
                name: _table_count(connection, metadata.tables[name])
                for name in table_names
            }
        finally:
            transaction.rollback()
    return counts


def validate_source_inventory(
    engine: Engine,
    *,
    expected_counts: dict[str, int] | None = None,
) -> dict[str, int]:
    actual = source_table_counts(engine)
    missing_required = sorted(REQUIRED_SOURCE_TABLES - set(actual))
    if missing_required:
        raise RehearsalError(
            f"required source tables are missing: {', '.join(missing_required)}"
        )
    if expected_counts is not None:
        normalized_expected = {
            str(name): max(0, int(count))
            for name, count in expected_counts.items()
        }
        if normalized_expected != actual:
            mismatched = sorted(
                name
                for name in set(normalized_expected) | set(actual)
                if normalized_expected.get(name) != actual.get(name)
            )
            raise RehearsalError(
                f"source count manifest mismatch: {', '.join(mismatched[:20])}"
            )
    return actual


def load_source_count_manifest(path: Path | str) -> dict[str, int]:
    manifest_path = Path(path).resolve()
    if not manifest_path.is_file():
        raise RehearsalError(f"source count manifest does not exist: {manifest_path.name}")
    raw = manifest_path.read_text(encoding="utf-8")
    _assert_report_safe(raw)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RehearsalError("source count manifest is invalid JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("table_counts"), dict):
        raise RehearsalError("source count manifest requires table_counts")
    counts: dict[str, int] = {}
    for raw_name, raw_count in payload["table_counts"].items():
        name = str(raw_name or "").strip()
        if not name or not re.fullmatch(r"[a-z][a-z0-9_]{0,80}", name):
            raise RehearsalError("source count manifest contains invalid table name")
        if isinstance(raw_count, bool) or not isinstance(raw_count, int):
            raise RehearsalError("source count manifest contains invalid count")
        count = raw_count
        if count < 0:
            raise RehearsalError("source count manifest contains negative count")
        counts[name] = count
    if not counts:
        raise RehearsalError("source count manifest is empty")
    return counts


def copy_table_streaming(
    source_connection,
    target_connection,
    *,
    source_table: Table,
    target_table: Table,
    common_columns: Sequence[str],
    chunk_size: int,
) -> dict[str, int]:
    columns = tuple(str(name) for name in common_columns)
    if not columns:
        return {"source_count": 0, "loaded_count": 0, "batches": 0}
    batch_size = max(1, int(chunk_size))
    statement = select(*(source_table.c[name] for name in columns)).execution_options(
        stream_results=True,
        yield_per=batch_size,
    )
    result = source_connection.execute(statement).mappings()
    source_count = 0
    loaded_count = 0
    batches = 0
    while True:
        rows = result.fetchmany(batch_size)
        if not rows:
            break
        payload = [{name: row[name] for name in columns} for row in rows]
        source_count += len(payload)
        target_connection.execute(target_table.insert(), payload)
        loaded_count += len(payload)
        batches += 1
    return {
        "source_count": source_count,
        "loaded_count": loaded_count,
        "batches": batches,
    }


def _reset_target_tables(
    connection: Connection,
    *,
    metadata: MetaData,
    table_names: Sequence[str],
) -> None:
    names = [name for name in table_names if name in metadata.tables]
    if not names:
        return
    if connection.dialect.name == "postgresql":
        quote = connection.dialect.identifier_preparer.quote
        rendered = ", ".join(quote(name) for name in names)
        connection.execute(text(f"TRUNCATE TABLE {rendered} RESTART IDENTITY CASCADE"))
        return
    for name in reversed(names):
        connection.execute(metadata.tables[name].delete())


def _table_count(connection: Connection, table: Table) -> int:
    return int(connection.execute(select(func.count()).select_from(table)).scalar_one() or 0)


def copy_database_transactional(
    source_engine: Engine,
    target_engine: Engine,
    *,
    target_metadata: MetaData,
    table_plan: Sequence[str],
    reset_table_names: Sequence[str],
    chunk_size: int,
    postprocess: Callable[[Connection], dict[str, Any] | None] | None = None,
    validator: Callable[[Connection], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    source_metadata = MetaData()
    if table_plan:
        source_metadata.reflect(bind=source_engine, only=list(table_plan))
    table_reports: dict[str, dict[str, Any]] = {}
    postprocess_report: dict[str, Any] = {}
    invariant_report: list[dict[str, Any]] = []
    final_counts: dict[str, int] = {}
    pre_postprocess_sequences: list[dict[str, Any]] = []

    with source_engine.connect() as source_connection:
        with target_engine.begin() as target_connection:
            _reset_target_tables(
                target_connection,
                metadata=target_metadata,
                table_names=reset_table_names,
            )
            for table_name in table_plan:
                source_table = source_metadata.tables[table_name]
                target_table = target_metadata.tables[table_name]
                source_columns = {column.name for column in source_table.columns}
                target_columns = {column.name for column in target_table.columns}
                common_columns = tuple(
                    column.name for column in target_table.columns if column.name in source_columns
                )
                copied = copy_table_streaming(
                    source_connection,
                    target_connection,
                    source_table=source_table,
                    target_table=target_table,
                    common_columns=common_columns,
                    chunk_size=chunk_size,
                )
                table_reports[table_name] = {
                    **copied,
                    "common_columns": len(common_columns),
                    "source_only_columns": sorted(source_columns - target_columns),
                    "target_only_columns": sorted(target_columns - source_columns),
                }

            pre_postprocess_sequences = sync_owned_sequences_connection(
                target_connection,
                target_metadata,
            )
            if postprocess is not None:
                postprocess_report = dict(postprocess(target_connection) or {})
            if validator is not None:
                invariant_report = list(validator(target_connection))
                failed = [row for row in invariant_report if row.get("status") != "PASS"]
                if failed:
                    raise RehearsalError(f"invariant checks failed: {len(failed)}")
            final_counts = {
                name: _table_count(target_connection, target_metadata.tables[name])
                for name in sorted(target_metadata.tables)
            }
            count_failures: list[str] = []
            for table_name, table_report in table_reports.items():
                final_count = int(final_counts.get(table_name, 0))
                source_count = int(table_report.get("source_count", 0))
                table_report["final_count"] = final_count
                if table_name in POSTPROCESS_MUTABLE_TABLES:
                    table_report["final_count_status"] = "POSTPROCESS_ALLOWED"
                elif final_count == source_count:
                    table_report["final_count_status"] = "PASS"
                else:
                    table_report["final_count_status"] = "FAIL"
                    count_failures.append(table_name)
            if count_failures:
                raise RehearsalError(
                    f"row count changed for immutable tables: {', '.join(sorted(count_failures))}"
                )

    return {
        "tables": table_reports,
        "postprocess": postprocess_report,
        "invariants": invariant_report,
        "final_counts": final_counts,
        "pre_postprocess_sequences": pre_postprocess_sequences,
    }


def _orphan_check(
    connection: Connection,
    metadata: MetaData,
    *,
    child_table: str,
    child_column: str,
    parent_table: str,
    parent_column: str,
) -> dict[str, Any] | None:
    if child_table not in metadata.tables or parent_table not in metadata.tables:
        return None
    child = metadata.tables[child_table]
    parent = metadata.tables[parent_table]
    if child_column not in child.c or parent_column not in parent.c:
        return None
    join = child.outerjoin(parent, child.c[child_column] == parent.c[parent_column])
    violations = int(
        connection.execute(
            select(func.count())
            .select_from(join)
            .where(child.c[child_column].is_not(None), parent.c[parent_column].is_(None))
        ).scalar_one()
        or 0
    )
    return {
        "name": f"{child_table}.{child_column}->{parent_table}.{parent_column}",
        "status": "PASS" if violations == 0 else "FAIL",
        "violations": violations,
    }


def _composite_orphan_check(
    connection: Connection,
    metadata: MetaData,
    *,
    child_table: str,
    child_columns: Sequence[str],
    parent_table: str,
    parent_columns: Sequence[str],
) -> dict[str, Any] | None:
    if child_table not in metadata.tables or parent_table not in metadata.tables:
        return None
    if len(child_columns) != len(parent_columns) or not child_columns:
        raise RehearsalError("invalid composite invariant definition")
    child = metadata.tables[child_table]
    parent = metadata.tables[parent_table]
    if any(column not in child.c for column in child_columns):
        return None
    if any(column not in parent.c for column in parent_columns):
        return None
    join_condition = child.c[child_columns[0]] == parent.c[parent_columns[0]]
    for child_column, parent_column in zip(child_columns[1:], parent_columns[1:]):
        join_condition = join_condition & (child.c[child_column] == parent.c[parent_column])
    query = select(func.count()).select_from(child.outerjoin(parent, join_condition))
    for child_column in child_columns:
        query = query.where(child.c[child_column].is_not(None))
    query = query.where(parent.c[parent_columns[0]].is_(None))
    violations = int(connection.execute(query).scalar_one() or 0)
    child_label = ",".join(child_columns)
    parent_label = ",".join(parent_columns)
    return {
        "name": f"{child_table}.({child_label})->{parent_table}.({parent_label})",
        "status": "PASS" if violations == 0 else "FAIL",
        "violations": violations,
    }


def run_invariant_checks(connection: Connection, metadata: MetaData) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    users = metadata.tables.get("users")
    if users is not None and "account_id" in users.c:
        null_accounts = int(
            connection.execute(
                select(func.count()).select_from(users).where(users.c.account_id.is_(None))
            ).scalar_one()
            or 0
        )
        checks.append(
            {
                "name": "users.account_id_not_null",
                "status": "PASS" if null_accounts == 0 else "FAIL",
                "violations": null_accounts,
            }
        )

    relations = ECONOMY_INVARIANT_RELATIONS + (
        ("users", "account_id", "accounts", "id"),
        ("account_identities", "account_id", "accounts", "id"),
        ("account_devices", "account_id", "accounts", "id"),
        ("auth_sessions", "account_id", "accounts", "id"),
        ("auth_sessions", "device_id", "account_devices", "id"),
        ("recovery_codes", "account_id", "accounts", "id"),
        ("entitlement_grants", "account_id", "accounts", "id"),
        ("antiabuse_events", "account_id", "accounts", "id"),
        ("antiabuse_events", "device_id", "account_devices", "id"),
        ("antiabuse_events", "session_id", "auth_sessions", "id"),
        ("antiabuse_cases", "account_id", "accounts", "id"),
        ("antiabuse_actions", "case_id", "antiabuse_cases", "id"),
        ("antiabuse_actions", "account_id", "accounts", "id"),
        ("account_merge_reviews", "account_id", "accounts", "id"),
        ("account_merge_reviews", "conflicting_account_id", "accounts", "id"),
        ("web_email_tokens", "identity_id", "web_email_identities", "id"),
        ("web_email_identities", "linked_tg_id", "users", "tg_id"),
        ("support_tickets", "user_tg_id", "users", "tg_id"),
        ("support_ticket_messages", "ticket_id", "support_tickets", "id"),
        ("pay_attempts", "offer_id", "offers", "id"),
        ("pay_attempts", "tg_id", "users", "tg_id"),
        ("points_ledger", "pay_attempt_id", "pay_attempts", "id"),
        ("points_ledger", "tg_id", "users", "tg_id"),
        ("user_nodes", "tg_id", "users", "tg_id"),
        ("user_nodes", "node_id", "nodes", "id"),
        ("access_keys", "tg_id", "users", "tg_id"),
        ("access_keys", "node_code", "nodes", "code"),
        ("key_usage_rollups", "key_id", "access_keys", "id"),
        ("key_source_observations", "key_id", "access_keys", "id"),
        ("key_pressure_state", "key_id", "access_keys", "id"),
        ("node_provisioning_jobs", "tg_id", "users", "tg_id"),
        ("node_provisioning_jobs", "key_id", "access_keys", "id"),
        ("node_provisioning_jobs", "node_code", "nodes", "code"),
        ("provider_traffic_quotas", "node_code", "nodes", "code"),
        ("provider_traffic_quota_audit", "quota_id", "provider_traffic_quotas", "id"),
        ("provider_traffic_quota_audit", "node_code", "nodes", "code"),
        ("ops_alerts", "tg_id", "users", "tg_id"),
        ("ops_alerts", "key_id", "access_keys", "id"),
        ("ops_alerts", "node_code", "nodes", "code"),
        ("key_action_history", "tg_id", "users", "tg_id"),
        ("key_action_history", "node_code", "nodes", "code"),
        ("user_key_policy", "tg_id", "users", "tg_id"),
        ("user_key_policy", "node_code", "nodes", "code"),
        ("subscription_fetch_events", "tg_id", "users", "tg_id"),
        ("rendered_subscription_snapshots", "fetch_event_id", "subscription_fetch_events", "id"),
        ("rendered_subscription_snapshots", "tg_id", "users", "tg_id"),
        ("external_orders", "tg_id", "users", "tg_id"),
    )
    for child_table, child_column, parent_table, parent_column in relations:
        check = _orphan_check(
            connection,
            metadata,
            child_table=child_table,
            child_column=child_column,
            parent_table=parent_table,
            parent_column=parent_column,
        )
        if check is not None:
            checks.append(check)
    payment_check = _composite_orphan_check(
        connection,
        metadata,
        child_table="external_payment_events",
        child_columns=("provider", "order_id"),
        parent_table="external_orders",
        parent_columns=("provider", "order_id"),
    )
    if payment_check is not None:
        checks.append(payment_check)
    return checks


def _run_account_backfill(
    connection: Connection,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    backfill_account_foundation, marker_key = _load_account_backfill()
    try:
        from portal_bot.models import AppSetting  # type: ignore
    except Exception:
        from models import AppSetting  # type: ignore
    effective_now = now or _utcnow()
    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        report = backfill_account_foundation(session, now=effective_now)
        marker_payload = json.dumps(
            {
                "completed_at": effective_now.isoformat(),
                "report": {
                    "accounts_created": int(report.accounts_created),
                    "accounts_merged": int(report.accounts_merged),
                    "devices_created": int(report.devices_created),
                    "grants_created": int(report.grants_created),
                    "identities_created": int(report.identities_created),
                    "reviews_created": int(report.reviews_created),
                    "users_seen": int(report.users_seen),
                },
                "status": "complete",
                "version": 1,
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        marker = session.query(AppSetting).filter(AppSetting.key == marker_key).first()
        if marker is None:
            marker = AppSetting(key=marker_key, value_json=marker_payload, updated_at=effective_now)
            session.add(marker)
        else:
            marker.value_json = marker_payload
            marker.updated_at = effective_now
        session.flush()
        session.commit()
    return {
        "account_backfill": {
            "accounts_created": int(report.accounts_created),
            "accounts_merged": int(report.accounts_merged),
            "devices_created": int(report.devices_created),
            "grants_created": int(report.grants_created),
            "identities_created": int(report.identities_created),
            "reviews_created": int(report.reviews_created),
            "users_seen": int(report.users_seen),
        }
    }


def _integer_primary_key_candidates(metadata: MetaData) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    for table_name, table in sorted(metadata.tables.items()):
        primary_keys = list(table.primary_key.columns)
        if len(primary_keys) != 1:
            continue
        column = primary_keys[0]
        try:
            python_type = column.type.python_type
        except (AttributeError, NotImplementedError):
            continue
        if python_type is int:
            candidates.append((table_name, column.name))
    return candidates


def sync_owned_sequences_connection(
    connection: Connection,
    metadata: MetaData,
) -> list[dict[str, Any]]:
    if connection.dialect.name != "postgresql":
        return []
    results: list[dict[str, Any]] = []
    for table_name, column_name in _integer_primary_key_candidates(metadata):
        sequence_name = connection.execute(
            text("SELECT pg_get_serial_sequence(:table_name, :column_name)"),
            {"table_name": table_name, "column_name": column_name},
        ).scalar_one_or_none()
        if not sequence_name:
            continue
        table = metadata.tables[table_name]
        max_value = connection.execute(select(func.max(table.c[column_name]))).scalar_one_or_none()
        if max_value is None:
            connection.execute(
                text("SELECT setval(CAST(:sequence_name AS regclass), 1, false)"),
                {"sequence_name": str(sequence_name)},
            )
            state = "empty"
            rendered_max = None
        else:
            connection.execute(
                text("SELECT setval(CAST(:sequence_name AS regclass), :max_value, true)"),
                {"sequence_name": str(sequence_name), "max_value": int(max_value)},
            )
            state = "populated"
            rendered_max = int(max_value)
        results.append(
            {
                "table": table_name,
                "column": column_name,
                "state": state,
                "max_value": rendered_max,
            }
        )
    return results


def sync_owned_sequences(engine: Engine, metadata: MetaData) -> list[dict[str, Any]]:
    if engine.dialect.name != "postgresql":
        return []
    with engine.begin() as connection:
        return sync_owned_sequences_connection(connection, metadata)


def _digest_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return format(value, ".17g")
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray, memoryview)):
        return {"bytes_sha256": hashlib.sha256(bytes(value)).hexdigest()}
    return str(value)


def database_content_digest(
    engine: Engine,
    metadata: MetaData,
    table_names: Sequence[str],
    *,
    chunk_size: int = 1000,
) -> str:
    digest = hashlib.sha256()
    with engine.connect() as connection:
        for table_name in sorted(name for name in table_names if name in metadata.tables):
            table = metadata.tables[table_name]
            columns = list(table.columns)
            order_columns = list(table.primary_key.columns) or columns
            digest.update(
                json.dumps(
                    {"table": table_name, "columns": [column.name for column in columns]},
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            statement = select(*columns).order_by(*order_columns).execution_options(
                stream_results=True,
                yield_per=max(1, int(chunk_size)),
            )
            result = connection.execute(statement).mappings()
            while True:
                rows = result.fetchmany(max(1, int(chunk_size)))
                if not rows:
                    break
                for row in rows:
                    normalized = [_digest_value(row[column.name]) for column in columns]
                    digest.update(
                        json.dumps(
                            normalized,
                            ensure_ascii=True,
                            separators=(",", ":"),
                        ).encode("utf-8")
                    )
    return digest.hexdigest()


def _without_volatile(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_volatile(item)
            for key, item in sorted(value.items())
            if key not in VOLATILE_REPORT_KEYS
        }
    if isinstance(value, list):
        return [_without_volatile(item) for item in value]
    return value


def normalized_report_digest(report: dict[str, Any]) -> str:
    payload = json.dumps(
        _without_volatile(report),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def run_rehearsal_once(
    source_engine: Engine,
    target_engine: Engine,
    *,
    target_metadata: MetaData,
    chunk_size: int,
    allow_non_postgres: bool = False,
    expected_source_counts: dict[str, int] | None = None,
    rehearsal_now: datetime | None = None,
) -> dict[str, Any]:
    if target_engine.dialect.name != "postgresql" and not allow_non_postgres:
        raise RehearsalError("rehearsal target must use PostgreSQL")
    source_counts = validate_source_inventory(
        source_engine,
        expected_counts=expected_source_counts,
    )
    source_tables = set(source_counts)
    target_tables = set(target_metadata.tables)
    shared_tables = source_tables & target_tables
    table_plan = build_table_plan(shared_tables)
    if not table_plan:
        raise RehearsalError("no shared source/target tables")
    reset_plan = build_table_plan(target_tables)
    effective_now = rehearsal_now or _utcnow()

    copied = copy_database_transactional(
        source_engine,
        target_engine,
        target_metadata=target_metadata,
        table_plan=table_plan,
        reset_table_names=reset_plan,
        chunk_size=chunk_size,
        postprocess=lambda connection: _run_account_backfill(
            connection,
            now=effective_now,
        ),
        validator=lambda connection: run_invariant_checks(connection, target_metadata),
    )
    sequence_report = sync_owned_sequences(target_engine, target_metadata)
    content_digest = database_content_digest(
        target_engine,
        target_metadata,
        sorted(target_tables),
        chunk_size=chunk_size,
    )
    report: dict[str, Any] = {
        "status": "PASS",
        "source_tables": len(source_tables),
        "target_tables": len(target_tables),
        "missing_source_tables": sorted(target_tables - source_tables),
        "source_counts": source_counts,
        "table_plan": table_plan,
        "tables": copied["tables"],
        "postprocess": copied["postprocess"],
        "invariants": copied["invariants"],
        "final_counts": copied["final_counts"],
        "sequences": sequence_report,
        "pre_postprocess_sequences": copied["pre_postprocess_sequences"],
        "content_digest": content_digest,
    }
    report["normalized_digest"] = normalized_report_digest(report)
    return report


def _assert_report_safe(payload: str) -> None:
    if SENSITIVE_REPORT_RE.search(payload):
        raise RehearsalError("report contains sensitive connection material")


def _assert_report_keys_safe(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if SENSITIVE_REPORT_KEY_RE.search(str(key)):
                raise RehearsalError("report contains sensitive key material")
            _assert_report_keys_safe(item)
    elif isinstance(value, list):
        for item in value:
            _assert_report_keys_safe(item)


def safe_error_message(exc: BaseException) -> str:
    if isinstance(exc, RehearsalError):
        message = str(exc).splitlines()[0][:300]
        message = re.sub(
            r"(?i)(?:postgresql(?:\+[a-z0-9_]+)?|sqlite)://\S+",
            "<redacted-url>",
            message,
        )
        if "[parameters" not in message.lower() and " detail " not in f" {message.lower()} ":
            return message
    return f"database_or_runtime_error ({type(exc).__name__}); inspect local protected logs"


def write_report_atomic(path: Path | str, report: dict[str, Any]) -> None:
    target = Path(path).resolve()
    if target.exists():
        raise RehearsalError(f"report already exists: {target.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    _assert_report_keys_safe(report)
    payload = json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    _assert_report_safe(payload)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _backup_restore_capability() -> dict[str, Any]:
    pg_dump = shutil.which("pg_dump")
    pg_restore = shutil.which("pg_restore")
    if pg_dump and pg_restore:
        return {"status": "AVAILABLE_NOT_RUN", "pg_dump": True, "pg_restore": True}
    return {
        "status": "SKIPPED_TOOL_UNAVAILABLE",
        "pg_dump": bool(pg_dump),
        "pg_restore": bool(pg_restore),
    }


def legacy_reset_table_names(
    shared_table_plan: Sequence[str],
    *,
    truncate_target: bool,
) -> list[str]:
    return list(shared_table_plan) if truncate_target else []


def _legacy_main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="One-shot data migration from SQLite to PostgreSQL.")
    parser.add_argument("--sqlite-url", default=os.getenv("SQLITE_DATABASE_URL", "sqlite:////root/portal_bot/portal.db"))
    parser.add_argument("--postgres-url", default=os.getenv("POSTGRES_DATABASE_URL", ""))
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--truncate-target", action="store_true")
    args = parser.parse_args(list(argv))
    if not args.postgres_url:
        raise SystemExit("Missing --postgres-url (or POSTGRES_DATABASE_URL).")
    if not str(args.sqlite_url).startswith("sqlite"):
        raise SystemExit("--sqlite-url must point to a sqlite database.")
    if not str(args.postgres_url).startswith("postgresql"):
        raise SystemExit("--postgres-url must point to a postgresql database.")

    Base = _load_models()
    source_engine = create_engine(args.sqlite_url)
    target_engine = create_engine(args.postgres_url)
    prepare_target_schema(
        target_engine,
        Base.metadata,
        run_migrations=_load_runtime_migrations(),
    )
    source_tables = set(inspect(source_engine).get_table_names())
    table_plan = build_table_plan(source_tables & set(Base.metadata.tables))
    if not table_plan:
        raise SystemExit("No shared tables found between source sqlite and model metadata.")
    copied = copy_database_transactional(
        source_engine,
        target_engine,
        target_metadata=Base.metadata,
        table_plan=table_plan,
        reset_table_names=legacy_reset_table_names(
            table_plan,
            truncate_target=bool(args.truncate_target),
        ),
        chunk_size=args.chunk_size,
    )
    sequences = sync_owned_sequences(target_engine, Base.metadata)
    total = sum(int(row.get("loaded_count", 0)) for row in copied["tables"].values())
    for table_name in table_plan:
        print(f"{table_name}: copied {copied['tables'][table_name]['loaded_count']} rows")
    print(f"done: copied {total} total rows; synchronized {len(sequences)} sequences")
    return 0


def _inventory_main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="Create a read-only SQLite source count manifest.")
    parser.add_argument("--sqlite-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(list(argv))
    source_path = Path(args.sqlite_path).resolve()
    if not source_path.is_file():
        raise SystemExit(f"sqlite source does not exist: {source_path.name}")
    engine = create_engine(f"sqlite:///{source_path.as_posix()}")
    counts = validate_source_inventory(engine)
    report = {
        "status": "REVIEW_REQUIRED",
        "generated_at": _utcnow().isoformat() + "Z",
        "source_name": source_path.name,
        "table_counts": counts,
    }
    write_report_atomic(Path(args.output), report)
    print(f"inventory written; review required; output={args.output}")
    return 0


def _rehearse_main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="Fail-closed SQLite-to-PostgreSQL rehearsal.")
    parser.add_argument("--sqlite-path", required=True)
    parser.add_argument("--snapshot-path", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--postgres-url-env", default="REHEARSAL_POSTGRES_URL")
    parser.add_argument("--confirm-target", required=True)
    parser.add_argument("--reset-target", action="store_true")
    parser.add_argument("--rerun-check", action="store_true")
    parser.add_argument("--report", required=True)
    parser.add_argument("--chunk-size", type=int, default=1000)
    args = parser.parse_args(list(argv))

    env_name = str(args.postgres_url_env or "").strip()
    if re.fullmatch(r"[A-Z][A-Z0-9_]{2,80}", env_name) is None:
        raise SystemExit("--postgres-url-env must be an uppercase environment variable name")
    postgres_url = str(os.getenv(env_name) or "").strip()
    if not postgres_url:
        raise SystemExit(f"Missing PostgreSQL URL in environment variable {env_name}.")

    report_path = Path(args.report)
    try:
        target_identity = validate_rehearsal_target(
            postgres_url,
            confirm_target=args.confirm_target,
            reset_target=bool(args.reset_target),
        )
        snapshot_report = snapshot_sqlite(Path(args.sqlite_path), Path(args.snapshot_path))
        expected_source_counts = load_source_count_manifest(Path(args.source_manifest))
        Base = _load_models()
        source_engine = create_engine(f"sqlite:///{Path(args.snapshot_path).resolve().as_posix()}")
        target_engine = create_engine(postgres_url, pool_pre_ping=True)
        prepare_target_schema(
            target_engine,
            Base.metadata,
            run_migrations=_load_runtime_migrations(),
        )
        rehearsal_now = _utcnow()
        first = run_rehearsal_once(
            source_engine,
            target_engine,
            target_metadata=Base.metadata,
            chunk_size=args.chunk_size,
            expected_source_counts=expected_source_counts,
            rehearsal_now=rehearsal_now,
        )
        rerun = None
        if args.rerun_check:
            second = run_rehearsal_once(
                source_engine,
                target_engine,
                target_metadata=Base.metadata,
                chunk_size=args.chunk_size,
                expected_source_counts=expected_source_counts,
                rehearsal_now=rehearsal_now,
            )
            rerun = {
                "status": "PASS"
                if (
                    first["normalized_digest"] == second["normalized_digest"]
                    and first["content_digest"] == second["content_digest"]
                )
                else "FAIL",
                "first_digest": first["normalized_digest"],
                "second_digest": second["normalized_digest"],
                "first_content_digest": first["content_digest"],
                "second_content_digest": second["content_digest"],
            }
            if rerun["status"] != "PASS":
                raise RehearsalError("rerun digest mismatch")
        report = {
            "status": "PASS",
            "generated_at": _utcnow().isoformat() + "Z",
            "source": snapshot_report,
            "target": target_identity,
            "migration": first,
            "rerun": rerun,
            "backup_restore": _backup_restore_capability(),
        }
        write_report_atomic(report_path, report)
        print(f"rehearsal PASS; report={report_path}")
        return 0
    except Exception as exc:
        message = safe_error_message(exc)
        failure_report = {
            "status": "FAIL",
            "generated_at": _utcnow().isoformat() + "Z",
            "error": {"type": type(exc).__name__, "message": message[:500]},
            "backup_restore": _backup_restore_capability(),
        }
        try:
            write_report_atomic(report_path, failure_report)
        except Exception:
            pass
        raise SystemExit(f"rehearsal failed: {message}") from exc


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "inventory":
        return _inventory_main(args[1:])
    if args and args[0] == "rehearse":
        return _rehearse_main(args[1:])
    return _legacy_main(args)


if __name__ == "__main__":
    raise SystemExit(main())

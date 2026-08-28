from __future__ import annotations

import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import Engine, event, text

from node_policy import free_tier_enabled


def _sqlite_column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table});")).fetchall()
    return any(r[1] == column for r in rows)  # (cid, name, type, notnull, dflt_value, pk)


def _sqlite_index_exists(conn, index_name: str) -> bool:
    rows = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='index' AND name=:name;"),
        {"name": index_name},
    ).fetchall()
    return bool(rows)


def _sqlite_enable_foreign_keys_on_checkout(
    dbapi_connection,
    _connection_record,
    _connection_proxy,
) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


def _configure_sqlite_foreign_keys(engine: Engine) -> None:
    pool = engine.pool
    if not event.contains(pool, "checkout", _sqlite_enable_foreign_keys_on_checkout):
        event.listen(pool, "checkout", _sqlite_enable_foreign_keys_on_checkout)


_POSTGRES_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
POSTGRES_SCHEMA_BOOTSTRAP_LOCK = "pokrov_schema_bootstrap"


def _postgres_ident(value: str) -> str:
    raw = str(value or "").strip()
    if not _POSTGRES_IDENTIFIER_RE.match(raw):
        raise ValueError(f"Unsafe PostgreSQL identifier: {value!r}")
    return raw


def _postgres_column_exists(conn, table: str, column: str) -> bool:
    return bool(
        conn.execute(
            text(
                """
                SELECT EXISTS (
                  SELECT 1
                  FROM information_schema.columns
                  WHERE table_schema = 'public'
                    AND table_name = :table_name
                    AND column_name = :column_name
                );
                """
            ),
            {"table_name": str(table), "column_name": str(column)},
        ).scalar()
    )


def _postgres_column_is_not_null(conn, table: str, column: str) -> bool:
    value = conn.execute(
        text(
            """
            SELECT is_nullable = 'NO'
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table_name
              AND column_name = :column_name;
            """
        ),
        {"table_name": str(table), "column_name": str(column)},
    ).scalar()
    return bool(value)


def _postgres_column_default_matches(conn, table: str, column: str, expected: str) -> bool:
    value = conn.execute(
        text(
            """
            SELECT column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table_name
              AND column_name = :column_name;
            """
        ),
        {"table_name": str(table), "column_name": str(column)},
    ).scalar()

    def normalize(raw: object) -> str:
        normalized = str(raw or "").strip().lower()
        normalized = re.sub(r"::[a-z0-9_ ]+$", "", normalized).strip()
        while normalized.startswith("(") and normalized.endswith(")"):
            normalized = normalized[1:-1].strip()
        return normalized

    return bool(value is not None and normalize(value) == normalize(expected))


def _postgres_varchar_limit(conn, table: str, column: str) -> int | None:
    value = conn.execute(
        text(
            """
            SELECT character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table_name
              AND column_name = :column_name;
            """
        ),
        {"table_name": str(table), "column_name": str(column)},
    ).scalar()
    try:
        return int(value) if value is not None else None
    except Exception:
        return None


def _ensure_economy_domain_sqlite(conn) -> None:
    if conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='account_entitlement_grants';")
    ).fetchone():
        for column, ddl in (
            ("reserved_at", "DATETIME"),
            ("reservation_expires_at", "DATETIME"),
            ("activated_at", "DATETIME"),
            ("duration_days", "INTEGER"),
            ("activation_evidence_id", "VARCHAR(36)"),
        ):
            if not _sqlite_column_exists(conn, "account_entitlement_grants", column):
                conn.execute(text(f"ALTER TABLE account_entitlement_grants ADD COLUMN {column} {ddl};"))
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS connection_evidence (
              id VARCHAR(36) PRIMARY KEY,
              account_id VARCHAR(36) NOT NULL,
              device_id VARCHAR(36),
              node_id INTEGER NOT NULL,
              evidence_kind VARCHAR(40) NOT NULL,
              observed_at DATETIME NOT NULL,
              evidence_key VARCHAR(160) NOT NULL,
              created_at DATETIME NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS referral_relationships (
              id VARCHAR(36) PRIMARY KEY,
              referred_account_id VARCHAR(36) NOT NULL,
              referrer_account_id VARCHAR(36) NOT NULL,
              source VARCHAR(32) NOT NULL,
              status VARCHAR(24) NOT NULL,
              review_status VARCHAR(24) NOT NULL DEFAULT 'clear',
              friend_evidence_id VARCHAR(36),
              friend_grant_id VARCHAR(36),
              friend_granted_at DATETIME,
              first_payment_key VARCHAR(160),
              first_payment_at DATETIME,
              hold_until DATETIME,
              referrer_grant_id VARCHAR(36),
              referrer_granted_at DATETIME,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS referral_transitions (
              id VARCHAR(36) PRIMARY KEY,
              relationship_id VARCHAR(36) NOT NULL,
              referred_account_id VARCHAR(36) NOT NULL,
              referrer_account_id VARCHAR(36) NOT NULL,
              transition_key VARCHAR(160) NOT NULL,
              transition_kind VARCHAR(40) NOT NULL,
              status VARCHAR(24) NOT NULL,
              occurred_at DATETIME NOT NULL,
              metadata_json TEXT,
              created_at DATETIME NOT NULL
            );
            """
        )
    )
    for sql in (
        "CREATE INDEX IF NOT EXISTS ix_account_entitlement_grants_reservation_expires_at ON account_entitlement_grants(reservation_expires_at);",
        "CREATE INDEX IF NOT EXISTS ix_account_entitlement_grants_activation_evidence_id ON account_entitlement_grants(activation_evidence_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_account_entitlement_grants_premium_trial_account ON account_entitlement_grants(account_id) WHERE source = 'premium_trial';",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_connection_evidence_key ON connection_evidence(evidence_key);",
        "CREATE INDEX IF NOT EXISTS ix_connection_evidence_account_id ON connection_evidence(account_id);",
        "CREATE INDEX IF NOT EXISTS ix_connection_evidence_device_id ON connection_evidence(device_id);",
        "CREATE INDEX IF NOT EXISTS ix_connection_evidence_node_id ON connection_evidence(node_id);",
        "CREATE INDEX IF NOT EXISTS ix_connection_evidence_observed_at ON connection_evidence(observed_at);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_referral_relationship_referred_account ON referral_relationships(referred_account_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_referral_relationship_first_payment ON referral_relationships(first_payment_key);",
        "CREATE INDEX IF NOT EXISTS ix_referral_relationship_referrer_account ON referral_relationships(referrer_account_id);",
        "CREATE INDEX IF NOT EXISTS ix_referral_relationship_hold_until ON referral_relationships(hold_until);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_referral_transition_key ON referral_transitions(transition_key);",
        "CREATE INDEX IF NOT EXISTS ix_referral_transition_relationship ON referral_transitions(relationship_id);",
    ):
        conn.execute(text(sql))


def _ensure_economy_domain_postgres(conn) -> None:
    for column, ddl in (
        ("reserved_at", "TIMESTAMP"),
        ("reservation_expires_at", "TIMESTAMP"),
        ("activated_at", "TIMESTAMP"),
        ("duration_days", "INTEGER"),
        ("activation_evidence_id", "VARCHAR(36)"),
    ):
        _postgres_add_column_if_missing(conn, "account_entitlement_grants", column, ddl)
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS connection_evidence (
              id VARCHAR(36) PRIMARY KEY,
              account_id VARCHAR(36) NOT NULL,
              device_id VARCHAR(36),
              node_id INTEGER NOT NULL,
              evidence_kind VARCHAR(40) NOT NULL,
              observed_at TIMESTAMP NOT NULL,
              evidence_key VARCHAR(160) NOT NULL,
              created_at TIMESTAMP NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS referral_relationships (
              id VARCHAR(36) PRIMARY KEY,
              referred_account_id VARCHAR(36) NOT NULL,
              referrer_account_id VARCHAR(36) NOT NULL,
              source VARCHAR(32) NOT NULL,
              status VARCHAR(24) NOT NULL,
              review_status VARCHAR(24) NOT NULL DEFAULT 'clear',
              friend_evidence_id VARCHAR(36),
              friend_grant_id VARCHAR(36),
              friend_granted_at TIMESTAMP,
              first_payment_key VARCHAR(160),
              first_payment_at TIMESTAMP,
              hold_until TIMESTAMP,
              referrer_grant_id VARCHAR(36),
              referrer_granted_at TIMESTAMP,
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS referral_transitions (
              id VARCHAR(36) PRIMARY KEY,
              relationship_id VARCHAR(36) NOT NULL,
              referred_account_id VARCHAR(36) NOT NULL,
              referrer_account_id VARCHAR(36) NOT NULL,
              transition_key VARCHAR(160) NOT NULL,
              transition_kind VARCHAR(40) NOT NULL,
              status VARCHAR(24) NOT NULL,
              occurred_at TIMESTAMP NOT NULL,
              metadata_json TEXT,
              created_at TIMESTAMP NOT NULL
            );
            """
        )
    )
    for sql in (
        "CREATE INDEX IF NOT EXISTS ix_account_entitlement_grants_reservation_expires_at ON account_entitlement_grants(reservation_expires_at);",
        "CREATE INDEX IF NOT EXISTS ix_account_entitlement_grants_activation_evidence_id ON account_entitlement_grants(activation_evidence_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_account_entitlement_grants_premium_trial_account ON account_entitlement_grants(account_id) WHERE source = 'premium_trial';",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_connection_evidence_key ON connection_evidence(evidence_key);",
        "CREATE INDEX IF NOT EXISTS ix_connection_evidence_account_id ON connection_evidence(account_id);",
        "CREATE INDEX IF NOT EXISTS ix_connection_evidence_device_id ON connection_evidence(device_id);",
        "CREATE INDEX IF NOT EXISTS ix_connection_evidence_node_id ON connection_evidence(node_id);",
        "CREATE INDEX IF NOT EXISTS ix_connection_evidence_observed_at ON connection_evidence(observed_at);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_referral_relationship_referred_account ON referral_relationships(referred_account_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_referral_relationship_first_payment ON referral_relationships(first_payment_key);",
        "CREATE INDEX IF NOT EXISTS ix_referral_relationship_referrer_account ON referral_relationships(referrer_account_id);",
        "CREATE INDEX IF NOT EXISTS ix_referral_relationship_hold_until ON referral_relationships(hold_until);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_referral_transition_key ON referral_transitions(transition_key);",
        "CREATE INDEX IF NOT EXISTS ix_referral_transition_relationship ON referral_transitions(relationship_id);",
    ):
        conn.execute(text(sql))


def _ensure_payment_entitlement_claims_sqlite(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS payment_entitlement_claims (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              provider VARCHAR(32) NOT NULL,
              order_id VARCHAR(128) NOT NULL,
              buyer_email_norm VARCHAR(255) NOT NULL,
              account_id VARCHAR(36),
              status VARCHAR(32) NOT NULL DEFAULT 'pending_payment',
              plan_code VARCHAR(32) NOT NULL,
              duration_days INTEGER NOT NULL,
              grant_id VARCHAR(36),
              fallback_gift_card_id INTEGER,
              paid_at DATETIME,
              attached_at DATETIME,
              fulfilled_at DATETIME,
              reversed_at DATETIME,
              reversal_reason VARCHAR(64),
              last_error VARCHAR(120),
              last_error_at DATETIME,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL,
              UNIQUE(provider, order_id)
            );
            """
        )
    )
    for column, ddl in (
        ("buyer_email_norm", "VARCHAR(255) NOT NULL DEFAULT 'unavailable@invalid.local'"),
        ("account_id", "VARCHAR(36)"),
        ("status", "VARCHAR(32) NOT NULL DEFAULT 'manual_review'"),
        ("plan_code", "VARCHAR(32) NOT NULL DEFAULT 'unknown'"),
        ("duration_days", "INTEGER NOT NULL DEFAULT 0"),
        ("grant_id", "VARCHAR(36)"),
        ("fallback_gift_card_id", "INTEGER"),
        ("paid_at", "DATETIME"),
        ("attached_at", "DATETIME"),
        ("fulfilled_at", "DATETIME"),
        ("reversed_at", "DATETIME"),
        ("reversal_reason", "VARCHAR(64)"),
        ("last_error", "VARCHAR(120)"),
        ("last_error_at", "DATETIME"),
        ("created_at", "DATETIME NOT NULL DEFAULT '1970-01-01 00:00:00'"),
        ("updated_at", "DATETIME NOT NULL DEFAULT '1970-01-01 00:00:00'"),
    ):
        if not _sqlite_column_exists(conn, "payment_entitlement_claims", column):
            conn.execute(text(f"ALTER TABLE payment_entitlement_claims ADD COLUMN {column} {ddl};"))
    conn.execute(
        text(
            """
            UPDATE payment_entitlement_claims
            SET buyer_email_norm = COALESCE(NULLIF(TRIM(buyer_email_norm), ''), 'unavailable@invalid.local'),
                status = 'manual_review',
                plan_code = COALESCE(NULLIF(TRIM(plan_code), ''), 'unknown'),
                duration_days = COALESCE(duration_days, 0),
                last_error = COALESCE(NULLIF(TRIM(last_error), ''), 'migration_incomplete_claim'),
                last_error_at = COALESCE(last_error_at, CURRENT_TIMESTAMP),
                created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
                updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)
            WHERE buyer_email_norm IS NULL OR TRIM(buyer_email_norm) = ''
               OR status IS NULL OR TRIM(status) = ''
               OR plan_code IS NULL OR TRIM(plan_code) = ''
               OR duration_days IS NULL OR duration_days <= 0
               OR created_at IS NULL
               OR updated_at IS NULL;
            """
        )
    )
    for sql in (
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_entitlement_claim_provider_order ON payment_entitlement_claims(provider, order_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_entitlement_claim_fallback_card ON payment_entitlement_claims(fallback_gift_card_id) WHERE fallback_gift_card_id IS NOT NULL;",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_claim_provider ON payment_entitlement_claims(provider);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_claim_order_id ON payment_entitlement_claims(order_id);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_claim_email ON payment_entitlement_claims(buyer_email_norm);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_claim_account ON payment_entitlement_claims(account_id);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_claim_status ON payment_entitlement_claims(status);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_claim_grant ON payment_entitlement_claims(grant_id);",
    ):
        conn.execute(text(sql))


def _ensure_external_order_attention_index(conn) -> None:
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_external_orders_status_created_at_id "
            "ON external_orders(status, created_at, id);"
        )
    )


def _ensure_payment_entitlement_claims_postgres(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS payment_entitlement_claims (
              id SERIAL PRIMARY KEY,
              provider VARCHAR(32) NOT NULL,
              order_id VARCHAR(128) NOT NULL,
              buyer_email_norm VARCHAR(255) NOT NULL,
              account_id VARCHAR(36),
              status VARCHAR(32) NOT NULL DEFAULT 'pending_payment',
              plan_code VARCHAR(32) NOT NULL,
              duration_days INTEGER NOT NULL,
              grant_id VARCHAR(36),
              fallback_gift_card_id INTEGER,
              paid_at TIMESTAMP,
              attached_at TIMESTAMP,
              fulfilled_at TIMESTAMP,
              reversed_at TIMESTAMP,
              reversal_reason VARCHAR(64),
              last_error VARCHAR(120),
              last_error_at TIMESTAMP,
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL,
              UNIQUE(provider, order_id)
            );
            """
        )
    )
    for column, ddl in (
        ("buyer_email_norm", "VARCHAR(255) NOT NULL DEFAULT 'unavailable@invalid.local'"),
        ("account_id", "VARCHAR(36)"),
        ("status", "VARCHAR(32) NOT NULL DEFAULT 'manual_review'"),
        ("plan_code", "VARCHAR(32) NOT NULL DEFAULT 'unknown'"),
        ("duration_days", "INTEGER NOT NULL DEFAULT 0"),
        ("grant_id", "VARCHAR(36)"),
        ("fallback_gift_card_id", "INTEGER"),
        ("paid_at", "TIMESTAMP"),
        ("attached_at", "TIMESTAMP"),
        ("fulfilled_at", "TIMESTAMP"),
        ("reversed_at", "TIMESTAMP"),
        ("reversal_reason", "VARCHAR(64)"),
        ("last_error", "VARCHAR(120)"),
        ("last_error_at", "TIMESTAMP"),
        ("created_at", "TIMESTAMP NOT NULL DEFAULT TIMESTAMP '1970-01-01 00:00:00'"),
        ("updated_at", "TIMESTAMP NOT NULL DEFAULT TIMESTAMP '1970-01-01 00:00:00'"),
    ):
        _postgres_add_column_if_missing(conn, "payment_entitlement_claims", column, ddl)
    conn.execute(
        text(
            """
            UPDATE payment_entitlement_claims
            SET buyer_email_norm = COALESCE(NULLIF(BTRIM(buyer_email_norm), ''), 'unavailable@invalid.local'),
                status = 'manual_review',
                plan_code = COALESCE(NULLIF(BTRIM(plan_code), ''), 'unknown'),
                duration_days = COALESCE(duration_days, 0),
                last_error = COALESCE(NULLIF(BTRIM(last_error), ''), 'migration_incomplete_claim'),
                last_error_at = COALESCE(last_error_at, CURRENT_TIMESTAMP),
                created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
                updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)
            WHERE buyer_email_norm IS NULL OR BTRIM(buyer_email_norm) = ''
               OR status IS NULL OR BTRIM(status) = ''
               OR plan_code IS NULL OR BTRIM(plan_code) = ''
               OR duration_days IS NULL OR duration_days <= 0
               OR created_at IS NULL
               OR updated_at IS NULL;
            """
        )
    )
    for column in (
        "buyer_email_norm",
        "status",
        "plan_code",
        "duration_days",
        "created_at",
        "updated_at",
    ):
        if not _postgres_column_is_not_null(conn, "payment_entitlement_claims", column):
            conn.execute(
                text(
                    f"ALTER TABLE payment_entitlement_claims "
                    f"ALTER COLUMN {_postgres_ident(column)} SET NOT NULL;"
                )
            )
    for sql in (
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_entitlement_claim_provider_order ON payment_entitlement_claims(provider, order_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_entitlement_claim_fallback_card ON payment_entitlement_claims(fallback_gift_card_id) WHERE fallback_gift_card_id IS NOT NULL;",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_claim_provider ON payment_entitlement_claims(provider);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_claim_order_id ON payment_entitlement_claims(order_id);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_claim_email ON payment_entitlement_claims(buyer_email_norm);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_claim_account ON payment_entitlement_claims(account_id);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_claim_status ON payment_entitlement_claims(status);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_claim_grant ON payment_entitlement_claims(grant_id);",
    ):
        conn.execute(text(sql))


def _postgres_add_column_if_missing(conn, table: str, column: str, ddl: str) -> bool:
    if _postgres_column_exists(conn, table, column):
        return False
    conn.execute(text(f"ALTER TABLE {_postgres_ident(table)} ADD COLUMN {_postgres_ident(column)} {ddl};"))
    return True


def _ensure_support_attachment_binding_postgres(conn) -> None:
    _postgres_add_column_if_missing(conn, "support_attachments", "ticket_id", "INTEGER")
    _postgres_add_column_if_missing(conn, "support_attachments", "message_id", "INTEGER")
    _postgres_add_column_if_missing(conn, "support_attachments", "attached_at", "TIMESTAMP")
    _postgres_add_column_if_missing(conn, "support_attachments", "expires_at", "TIMESTAMP")
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_attachments_ticket_id ON support_attachments(ticket_id);"))
    conn.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_support_attachments_message_id "
            "ON support_attachments(message_id);"
        )
    )
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_attachments_expires_at ON support_attachments(expires_at);"))


_FREE_PROFILE_USER_COLUMNS = (
    ("free_profile_state", "VARCHAR(32) NOT NULL DEFAULT 'standard'"),
    ("free_profile_active_role", "VARCHAR(32) NOT NULL DEFAULT 'free_standard'"),
    ("free_profile_source", "VARCHAR(64) NOT NULL DEFAULT 'legacy_backfill'"),
    ("free_profile_state_changed_at", "DATETIME"),
    ("free_profile_job_id", "INTEGER"),
    ("free_profile_error_code", "VARCHAR(64)"),
    ("free_profile_standard_node_code", "VARCHAR(32)"),
    ("free_profile_soft_node_code", "VARCHAR(32)"),
    ("free_profile_observed_bytes", "BIGINT NOT NULL DEFAULT 0"),
    ("free_profile_observed_at", "DATETIME"),
    ("free_profile_observation_source", "VARCHAR(64)"),
)

_FREE_PROFILE_JOB_COLUMNS = (
    ("idempotency_key", "VARCHAR(160)"),
    ("lock_token", "VARCHAR(64)"),
    ("last_error_code", "VARCHAR(64)"),
    ("replacement_key_uuid", "VARCHAR(36)"),
    ("completed_at", "DATETIME"),
    ("manual_review_at", "DATETIME"),
)


def _sqlite_table_exists(conn, table: str) -> bool:
    return bool(
        conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name;"),
            {"name": str(table)},
        ).fetchone()
    )


def _ensure_free_profile_schema_sqlite(conn) -> None:
    if _sqlite_table_exists(conn, "users"):
        for column, ddl in _FREE_PROFILE_USER_COLUMNS:
            if not _sqlite_column_exists(conn, "users", column):
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {column} {ddl};"))
        conn.execute(
            text(
                """
                UPDATE users
                SET free_profile_state = COALESCE(NULLIF(trim(free_profile_state), ''), 'standard'),
                    free_profile_active_role = COALESCE(NULLIF(trim(free_profile_active_role), ''), 'free_standard'),
                    free_profile_source = COALESCE(NULLIF(trim(free_profile_source), ''), 'legacy_backfill'),
                    free_profile_observed_bytes = COALESCE(free_profile_observed_bytes, 0);
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_free_profile_job_id ON users(free_profile_job_id);"))

    if _sqlite_table_exists(conn, "nodes"):
        node_role_added = False
        if not _sqlite_column_exists(conn, "nodes", "access_role"):
            conn.execute(text("ALTER TABLE nodes ADD COLUMN access_role VARCHAR(32) NOT NULL DEFAULT 'paid';"))
            node_role_added = True
        if not _sqlite_column_exists(conn, "nodes", "access_role_legacy"):
            conn.execute(text("ALTER TABLE nodes ADD COLUMN access_role_legacy VARCHAR(32);"))
        if not node_role_added:
            conn.execute(
                text(
                    """
                    UPDATE nodes
                    SET access_role_legacy = access_role
                    WHERE access_role_legacy IS NULL
                      AND access_role IS NOT NULL
                      AND trim(access_role) <> ''
                      AND access_role NOT IN ('free_standard', 'free_soft', 'paid', 'operator_lab');
                    """
                )
            )
        node_role_where = (
            "1 = 1"
            if node_role_added
            else "access_role IS NULL OR trim(access_role) = '' "
            "OR access_role NOT IN ('free_standard', 'free_soft', 'paid', 'operator_lab')"
        )
        conn.execute(
            text(
                f"""
                UPDATE nodes
                SET access_role = CASE
                    WHEN instr(lower(COALESCE(code, '')), 'operator') > 0
                      OR substr(lower(COALESCE(code, '')), -4) IN ('_lab', '-lab') THEN 'operator_lab'
                    WHEN instr(lower(COALESCE(code, '')), 'free') > 0
                      AND instr(lower(COALESCE(code, '')), 'soft') > 0 THEN 'free_soft'
                    WHEN instr(lower(COALESCE(code, '')), 'free') > 0 THEN 'free_standard'
                    ELSE 'paid'
                END
                WHERE {node_role_where};
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_access_role ON nodes(access_role);"))

    if _sqlite_table_exists(conn, "node_provisioning_jobs"):
        for column, ddl in _FREE_PROFILE_JOB_COLUMNS:
            if not _sqlite_column_exists(conn, "node_provisioning_jobs", column):
                conn.execute(text(f"ALTER TABLE node_provisioning_jobs ADD COLUMN {column} {ddl};"))
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_node_provisioning_jobs_idempotency_key "
                "ON node_provisioning_jobs(idempotency_key);"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_node_provisioning_jobs_lock_token "
                "ON node_provisioning_jobs(lock_token);"
            )
        )


def _ensure_free_profile_schema_postgres(conn) -> None:
    for column, ddl in _FREE_PROFILE_USER_COLUMNS:
        _postgres_add_column_if_missing(conn, "users", column, ddl.replace("DATETIME", "TIMESTAMP"))
    node_role_added = _postgres_add_column_if_missing(
        conn,
        "nodes",
        "access_role",
        "VARCHAR(32) NOT NULL DEFAULT 'paid'",
    )
    _postgres_add_column_if_missing(conn, "nodes", "access_role_legacy", "VARCHAR(32)")
    for column, ddl in _FREE_PROFILE_JOB_COLUMNS:
        _postgres_add_column_if_missing(
            conn,
            "node_provisioning_jobs",
            column,
            ddl.replace("DATETIME", "TIMESTAMP"),
        )

    if not node_role_added:
        conn.execute(
            text(
                """
                UPDATE nodes
                SET access_role_legacy = access_role
                WHERE access_role_legacy IS NULL
                  AND access_role IS NOT NULL
                  AND btrim(access_role) <> ''
                  AND access_role NOT IN ('free_standard', 'free_soft', 'paid', 'operator_lab');
                """
            )
        )
    conn.execute(
        text(
            """
            UPDATE users
            SET free_profile_state = COALESCE(NULLIF(btrim(free_profile_state), ''), 'standard'),
                free_profile_active_role = COALESCE(NULLIF(btrim(free_profile_active_role), ''), 'free_standard'),
                free_profile_source = COALESCE(NULLIF(btrim(free_profile_source), ''), 'legacy_backfill'),
                free_profile_observed_bytes = COALESCE(free_profile_observed_bytes, 0)
            WHERE free_profile_state IS NULL OR btrim(free_profile_state) = ''
               OR free_profile_active_role IS NULL OR btrim(free_profile_active_role) = ''
               OR free_profile_source IS NULL OR btrim(free_profile_source) = ''
               OR free_profile_observed_bytes IS NULL;
            """
        )
    )
    conn.execute(
        text(
            f"""
            UPDATE nodes
            SET access_role = CASE
                WHEN position('operator' in lower(COALESCE(code, ''))) > 0
                  OR right(lower(COALESCE(code, '')), 4) IN ('_lab', '-lab') THEN 'operator_lab'
                WHEN position('free' in lower(COALESCE(code, ''))) > 0
                  AND position('soft' in lower(COALESCE(code, ''))) > 0 THEN 'free_soft'
                WHEN position('free' in lower(COALESCE(code, ''))) > 0 THEN 'free_standard'
                ELSE 'paid'
            END
            WHERE {
                'TRUE'
                if node_role_added
                else "access_role IS NULL OR btrim(access_role) = '' "
                "OR access_role NOT IN ('free_standard', 'free_soft', 'paid', 'operator_lab')"
            };
            """
        )
    )
    for column, default in (
        ("free_profile_state", "'standard'"),
        ("free_profile_active_role", "'free_standard'"),
        ("free_profile_source", "'legacy_backfill'"),
        ("free_profile_observed_bytes", "0"),
    ):
        if not _postgres_column_default_matches(conn, "users", column, default):
            conn.execute(text(f"ALTER TABLE users ALTER COLUMN {column} SET DEFAULT {default};"))
        if not _postgres_column_is_not_null(conn, "users", column):
            conn.execute(text(f"ALTER TABLE users ALTER COLUMN {column} SET NOT NULL;"))
    if not _postgres_column_default_matches(conn, "nodes", "access_role", "'paid'"):
        conn.execute(text("ALTER TABLE nodes ALTER COLUMN access_role SET DEFAULT 'paid';"))
    if not _postgres_column_is_not_null(conn, "nodes", "access_role"):
        conn.execute(text("ALTER TABLE nodes ALTER COLUMN access_role SET NOT NULL;"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_free_profile_job_id ON users(free_profile_job_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_access_role ON nodes(access_role);"))
    conn.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_node_provisioning_jobs_idempotency_key "
            "ON node_provisioning_jobs(idempotency_key);"
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_node_provisioning_jobs_lock_token "
            "ON node_provisioning_jobs(lock_token);"
        )
    )


_REWARD_JOB_COLUMNS = (
    ("account_id", "VARCHAR(36)"),
    ("entitlement_grant_id", "VARCHAR(36)"),
)


def _ensure_reward_schema_sqlite(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS reward_account_states (
              account_id VARCHAR(36) PRIMARY KEY,
              wheel_last_spin_at DATETIME,
              wheel_last_grant_id VARCHAR(36),
              calendar_last_check_date DATE,
              calendar_cycle_started_on DATE,
              calendar_cycle_day INTEGER DEFAULT 0 NOT NULL,
              calendar_first_checkin_at DATETIME,
              calendar_streak_7_unlocked_at DATETIME,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL,
              CONSTRAINT ck_reward_account_state_cycle_day
                CHECK (
                  calendar_cycle_day IS NULL
                  OR (calendar_cycle_day >= 0 AND calendar_cycle_day <= 28)
                )
            );
            """
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_reward_account_states_wheel_last_grant_id "
            "ON reward_account_states(wheel_last_grant_id);"
        )
    )

    if _sqlite_table_exists(conn, "node_provisioning_jobs"):
        for column, ddl in _REWARD_JOB_COLUMNS:
            if not _sqlite_column_exists(conn, "node_provisioning_jobs", column):
                conn.execute(text(f"ALTER TABLE node_provisioning_jobs ADD COLUMN {column} {ddl};"))
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_node_provisioning_jobs_account_id "
                "ON node_provisioning_jobs(account_id);"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_node_provisioning_jobs_entitlement_grant_id "
                "ON node_provisioning_jobs(entitlement_grant_id);"
            )
        )


def _ensure_reward_schema_postgres(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS reward_account_states (
              account_id VARCHAR(36) PRIMARY KEY,
              wheel_last_spin_at TIMESTAMP,
              wheel_last_grant_id VARCHAR(36),
              calendar_last_check_date DATE,
              calendar_cycle_started_on DATE,
              calendar_cycle_day INTEGER DEFAULT 0 NOT NULL,
              calendar_first_checkin_at TIMESTAMP,
              calendar_streak_7_unlocked_at TIMESTAMP,
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL,
              CONSTRAINT ck_reward_account_state_cycle_day
                CHECK (
                  calendar_cycle_day IS NULL
                  OR (calendar_cycle_day >= 0 AND calendar_cycle_day <= 28)
                )
            );
            """
        )
    )
    conn.execute(
        text(
            "ALTER TABLE node_provisioning_jobs "
            "ADD COLUMN IF NOT EXISTS account_id VARCHAR(36);"
        )
    )
    conn.execute(
        text(
            "ALTER TABLE node_provisioning_jobs "
            "ADD COLUMN IF NOT EXISTS entitlement_grant_id VARCHAR(36);"
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_reward_account_states_wheel_last_grant_id "
            "ON reward_account_states(wheel_last_grant_id);"
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_node_provisioning_jobs_account_id "
            "ON node_provisioning_jobs(account_id);"
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_node_provisioning_jobs_entitlement_grant_id "
            "ON node_provisioning_jobs(entitlement_grant_id);"
        )
    )


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SHARED_DIR = _REPO_ROOT / "shared"


def _load_shared_json(filename: str) -> dict:
    return json.loads((_SHARED_DIR / filename).read_text(encoding="utf-8"))


RETENTION_TEMPLATE_PRESETS: dict[str, str] = {
    "retention_welcome_a": (
        "🚀 Тест уже активирован.\n\n"
        "Чтобы всё заработало с первого раза:\n"
        "1) откройте раздел подключения;\n"
        "2) скопируйте ключ или QR;\n"
        "3) откройте приложение и проверьте доступ.\n\n"
        "Если где-то застряли — напишите в службу заботы. Мы рядом и обычно помогаем очень быстро."
    ),
    "retention_welcome_b": (
        "✨ Добро пожаловать в POKROV.\n\n"
        "Перед первым запуском:\n"
        "• выберите приложение для своего устройства;\n"
        "• импортируйте ключ одним действием;\n"
        "• сохраните канал {channel}, чтобы не потерять обновления и подсказки."
    ),
    "retention_t3_a": (
        "⌛ До окончания доступа осталось около 3 дней.\n\n"
        "Если сервис нужен каждый день, лучше продлить заранее и не ловить паузу в самый неудобный момент."
    ),
    "retention_t3_b": (
        "📅 Напоминание T-3.\n\n"
        "Позаботьтесь о своем интернете заранее: продлите подписку сегодня и забудьте о блокировках."
    ),
    "retention_t1_a": (
        "⏱ До завершения теста остались примерно сутки.\n\n"
        "Если сервис вам подошёл, лучше открыть продление сейчас, чтобы интернет продолжал работать без пауз."
    ),
    "retention_t1_b": (
        "⚡ T-1: срок доступа заканчивается в ближайшие сутки.\n\n"
        "Продлите сейчас, чтобы не возвращаться к настройке и подключению заново."
    ),
    "retention_t0_a": (
        "🔔 Тест заканчивается сегодня.\n\n"
        "Если хотите сохранить доступ и не возвращаться к настройке заново, откройте продление прямо сейчас."
    ),
    "retention_t0_b": (
        "🔔 Подписка почти завершена.\n\n"
        "Пара минут на продление сейчас сохранит доступ активным и снимет лишнее трение."
    ),
    "retention_reactivation_a": (
        "🌍 Ваш профиль и настройки сохранены.\n\n"
        "Вернитесь в один клик и продолжайте пользоваться интернетом без повторной настройки."
    ),
    "retention_reactivation_b": (
        "🧭 Срок подписки истек, но мы с радостью вернем вас в онлайн всего в пару кликов!\n\n"
        "Откройте продление и вернитесь в рабочий режим за пару минут."
    ),
}

DEFAULT_PAID_DEVICE_LIMIT = max(1, int(os.getenv("PAID_LIMIT_IP") or "5"))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _datetime_sql_param(value: datetime, *, dialect: str) -> datetime | str:
    if dialect == "sqlite":
        return value.strftime("%Y-%m-%d %H:%M:%S.%f")
    return value


def _legacy_transport_catalog_payload(
    *,
    host: str | None,
    vless_port,
    reality_sni: str | None,
    reality_pbk: str | None,
    reality_sid: str | None,
    fingerprint: str | None,
    flow: str | None,
    inbound_id,
) -> str:
    try:
        inbound_value = int(inbound_id or 0)
    except Exception:
        inbound_value = 0
    try:
        port_value = int(vless_port or 443)
    except Exception:
        port_value = 443
    payload = [
        {
            "name": "legacy_reality_fallback",
            "enabled": inbound_value > 0,
            "kind": "reality",
            "inbound_id": inbound_value,
            "host": str(host or "").strip(),
            "port": max(1, port_value),
            "tls_server_name": str(reality_sni or "").strip(),
            "reality_public_key": str(reality_pbk or "").strip(),
            "reality_short_id": str(reality_sid or "").strip(),
            "fingerprint": str(fingerprint or "").strip() or "firefox",
            "flow": str(flow or "").strip() or "xtls-rprx-vision",
        }
    ]
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

def _seed_retention_templates(conn, *, dialect: str) -> None:
    if dialect == "sqlite":
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='templates';")
        ).fetchone()
        if not exists:
            return
    elif dialect == "postgresql":
        exists = conn.execute(text("SELECT to_regclass('public.templates');")).scalar()
        if not exists:
            return
    else:
        return

    # Force-upsert presets so active environments receive refreshed retention copy.
    for key, value in RETENTION_TEMPLATE_PRESETS.items():
        updated = conn.execute(
            text('UPDATE templates SET "text" = :text WHERE lower("key") = :key;'),
            {"key": str(key).lower(), "text": value},
        )
        if int(getattr(updated, "rowcount", 0) or 0) > 0:
            continue
        conn.execute(
            text('INSERT INTO templates ("key", "text", "created_at") VALUES (:key, :text, :created_at);'),
            {
                "key": key,
                "text": value,
                "created_at": _datetime_sql_param(_utcnow(), dialect=dialect),
            },
        )


PLAN_CATALOG_PRESETS = [
    {
        "code": str(plan.get("code") or "").strip().lower(),
        "label": str(plan.get("label") or "").strip(),
        "amount_rub": int(plan.get("amount_rub") or 0),
        "amount_stars": int(plan.get("amount_stars") or 0),
        "days": int(plan.get("duration_days") or 30),
        "device_limit": max(1, int(plan.get("device_limit") or DEFAULT_PAID_DEVICE_LIMIT)),
        "node_policy": str(plan.get("node_policy") or "").strip() or None,
        "badge": str(plan.get("badge") or "").strip() or None,
        "is_active": bool(plan.get("is_active", True)),
        "sort_order": int(plan.get("sort_order") or 100),
    }
    for plan in list(_load_shared_json("tariff-catalog.json").get("plans") or [])
    if str(plan.get("code") or "").strip()
]


def _seed_plan_catalog(conn, *, dialect: str) -> None:
    if dialect == "sqlite":
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='plan_catalog';")
        ).fetchone()
        if not exists:
            return
    elif dialect == "postgresql":
        exists = conn.execute(text("SELECT to_regclass('public.plan_catalog');")).scalar()
        if not exists:
            return
    else:
        return

    now = _utcnow()
    now_param = _datetime_sql_param(now, dialect=dialect)
    for item in PLAN_CATALOG_PRESETS:
        updated = conn.execute(
            text(
                """
                UPDATE plan_catalog
                SET label = :label,
                    amount_rub = :amount_rub,
                    amount_stars = :amount_stars,
                    days = :days,
                    device_limit = :device_limit,
                    node_policy = :node_policy,
                    badge = :badge,
                    is_active = :is_active,
                    sort_order = :sort_order,
                    updated_at = :updated_at
                WHERE lower(code) = :code;
                """
            ),
            {
                **item,
                "code": str(item["code"]).lower(),
                "updated_at": now_param,
            },
        )
        if int(getattr(updated, "rowcount", 0) or 0) > 0:
            continue
        conn.execute(
            text(
                """
                INSERT INTO plan_catalog (
                    code, label, amount_rub, amount_stars, days, device_limit, node_policy,
                    badge, is_active, sort_order, created_at, updated_at
                )
                VALUES (
                    :code, :label, :amount_rub, :amount_stars, :days, :device_limit, :node_policy,
                    :badge, :is_active, :sort_order, :created_at, :updated_at
                );
                """
            ),
            {
                **item,
                "created_at": now_param,
                "updated_at": now_param,
            },
        )


def _ensure_capacity_domain_sqlite(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS access_keys (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              tg_id BIGINT NOT NULL,
              key_uuid VARCHAR(36) NOT NULL,
              panel_email VARCHAR(100) NOT NULL,
              node_code VARCHAR(32),
              pool_code VARCHAR(32) DEFAULT 'premium_pool' NOT NULL,
              state VARCHAR(32) DEFAULT 'active' NOT NULL,
              source VARCHAR(32) DEFAULT 'legacy_user' NOT NULL,
              is_primary BOOLEAN DEFAULT 1 NOT NULL,
              provisioned_at DATETIME,
              last_seen_at DATETIME,
              rotated_at DATETIME,
              revoked_at DATETIME,
              meta_json TEXT,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS node_capacity_policy (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              node_code VARCHAR(32) NOT NULL,
              max_tx_mbps FLOAT,
              soft_tx_ratio FLOAT DEFAULT 0.70 NOT NULL,
              drain_tx_ratio FLOAT DEFAULT 0.82 NOT NULL,
              hard_tx_ratio FLOAT DEFAULT 0.92 NOT NULL,
              soft_cpu_percent FLOAT DEFAULT 75 NOT NULL,
              hard_cpu_percent FLOAT DEFAULT 90 NOT NULL,
              stale_after_seconds INTEGER DEFAULT 180 NOT NULL,
              max_packet_loss_percent FLOAT DEFAULT 2 NOT NULL,
              max_tcp_retrans_percent FLOAT DEFAULT 5 NOT NULL,
              rank_weight INTEGER DEFAULT 100 NOT NULL,
              allow_free_pool BOOLEAN DEFAULT 0 NOT NULL,
              allow_premium_pool BOOLEAN DEFAULT 1 NOT NULL,
              is_enabled BOOLEAN DEFAULT 1 NOT NULL,
              updated_by BIGINT,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS node_runtime_metrics (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              node_code VARCHAR(32) NOT NULL,
              sampled_at DATETIME NOT NULL,
              source VARCHAR(64) DEFAULT 'collector' NOT NULL,
              batch_id VARCHAR(128),
              provisioned_clients_count INTEGER DEFAULT 0 NOT NULL,
              online_connections_hint INTEGER DEFAULT 0 NOT NULL,
              network_rx_mbps_1m FLOAT,
              network_tx_mbps_1m FLOAT,
              network_rx_mbps_5m FLOAT,
              network_tx_mbps_5m FLOAT,
              network_total_mbps FLOAT,
              cpu_percent FLOAT,
              memory_used_mb INTEGER,
              memory_total_mb INTEGER,
              tcp_retrans_percent FLOAT,
              packet_loss_percent FLOAT,
              edge_reachability_ok BOOLEAN,
              authenticated_egress_ok BOOLEAN,
              dataplane_ok BOOLEAN,
              dataplane_rtt_ms INTEGER,
              capacity_score FLOAT,
              capacity_state VARCHAR(32) DEFAULT 'unknown' NOT NULL,
              reject_reason VARCHAR(64),
              meta_json TEXT
            );
            """
        )
    )
    for col, ddl in (
        ("edge_reachability_ok", "BOOLEAN"),
        ("authenticated_egress_ok", "BOOLEAN"),
    ):
        if not _sqlite_column_exists(conn, "node_runtime_metrics", col):
            conn.execute(text(f"ALTER TABLE node_runtime_metrics ADD COLUMN {col} {ddl};"))
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS key_usage_rollups (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              key_id INTEGER,
              tg_id BIGINT,
              node_code VARCHAR(32) NOT NULL,
              panel_email VARCHAR(100),
              window_bucket_at DATETIME NOT NULL,
              window_seconds INTEGER DEFAULT 300 NOT NULL,
              upload_bytes BIGINT DEFAULT 0 NOT NULL,
              download_bytes BIGINT DEFAULT 0 NOT NULL,
              total_bytes BIGINT DEFAULT 0 NOT NULL,
              peak_tx_mbps FLOAT,
              observations INTEGER DEFAULT 0 NOT NULL,
              source VARCHAR(64) DEFAULT 'observer' NOT NULL,
              created_at DATETIME NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS key_source_observations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              key_id INTEGER,
              tg_id BIGINT,
              node_code VARCHAR(32) NOT NULL,
              panel_email VARCHAR(100),
              source_ip_hash VARCHAR(64) NOT NULL,
              source_asn VARCHAR(32),
              source_country VARCHAR(8),
              window_bucket_at DATETIME NOT NULL,
              first_seen_at DATETIME NOT NULL,
              last_seen_at DATETIME NOT NULL,
              hit_count INTEGER DEFAULT 0 NOT NULL,
              meta_json TEXT
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS key_pressure_state (
              key_id INTEGER PRIMARY KEY,
              tg_id BIGINT,
              node_code VARCHAR(32),
              panel_email VARCHAR(100),
              state VARCHAR(32) DEFAULT 'ok' NOT NULL,
              pressure_score FLOAT DEFAULT 0 NOT NULL,
              reasons_json TEXT,
              distinct_source_ips_1h INTEGER DEFAULT 0 NOT NULL,
              distinct_source_ips_24h INTEGER DEFAULT 0 NOT NULL,
              node_count_24h INTEGER DEFAULT 0 NOT NULL,
              traffic_gb_24h FLOAT DEFAULT 0 NOT NULL,
              manual_review_required BOOLEAN DEFAULT 0 NOT NULL,
              updated_at DATETIME NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS subscription_fetch_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              tg_id BIGINT NOT NULL,
              token_fp VARCHAR(32) NOT NULL,
              lookup_mode VARCHAR(32) NOT NULL,
              client_format VARCHAR(32) NOT NULL,
              user_agent_hash VARCHAR(64),
              request_host VARCHAR(255),
              selected_nodes_json TEXT,
              excluded_nodes_json TEXT,
              response_status INTEGER DEFAULT 200 NOT NULL,
              created_at DATETIME NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS rendered_subscription_snapshots (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              fetch_event_id INTEGER,
              tg_id BIGINT NOT NULL,
              profile_revision VARCHAR(128),
              client_format VARCHAR(32) NOT NULL,
              node_order_json TEXT NOT NULL,
              excluded_nodes_json TEXT,
              content_sha256 VARCHAR(64) NOT NULL,
              created_at DATETIME NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS node_pool_membership (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              node_code VARCHAR(32) NOT NULL,
              pool_code VARCHAR(32) NOT NULL,
              is_enabled BOOLEAN DEFAULT 1 NOT NULL,
              source VARCHAR(32) DEFAULT 'migration' NOT NULL,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS node_provisioning_jobs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              account_id VARCHAR(36),
              entitlement_grant_id VARCHAR(36),
              tg_id BIGINT,
              key_id INTEGER,
              node_code VARCHAR(32),
              job_type VARCHAR(32) NOT NULL,
              status VARCHAR(32) DEFAULT 'queued' NOT NULL,
              desired_state_json TEXT,
              result_json TEXT,
              attempts INTEGER DEFAULT 0 NOT NULL,
              next_run_at DATETIME,
              locked_at DATETIME,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL
            );
            """
        )
    )
    for sql in [
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_access_keys_tg_uuid ON access_keys(tg_id, key_uuid);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_access_keys_node_email ON access_keys(node_code, panel_email);",
        "CREATE INDEX IF NOT EXISTS ix_access_keys_tg_id ON access_keys(tg_id);",
        "CREATE INDEX IF NOT EXISTS ix_access_keys_key_uuid ON access_keys(key_uuid);",
        "CREATE INDEX IF NOT EXISTS ix_access_keys_pool_code ON access_keys(pool_code);",
        "CREATE INDEX IF NOT EXISTS ix_access_keys_state ON access_keys(state);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_node_capacity_policy_code ON node_capacity_policy(node_code);",
        "CREATE INDEX IF NOT EXISTS ix_node_runtime_metrics_node_code ON node_runtime_metrics(node_code);",
        "CREATE INDEX IF NOT EXISTS ix_node_runtime_metrics_sampled_at ON node_runtime_metrics(sampled_at);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_key_usage_rollup_window ON key_usage_rollups(key_id, node_code, window_bucket_at, window_seconds);",
        "CREATE INDEX IF NOT EXISTS ix_key_usage_rollups_tg_id ON key_usage_rollups(tg_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_key_source_window ON key_source_observations(key_id, node_code, source_ip_hash, window_bucket_at);",
        "CREATE INDEX IF NOT EXISTS ix_key_pressure_state_state ON key_pressure_state(state);",
        "CREATE INDEX IF NOT EXISTS ix_subscription_fetch_events_tg_id ON subscription_fetch_events(tg_id);",
        "CREATE INDEX IF NOT EXISTS ix_subscription_fetch_events_created_at ON subscription_fetch_events(created_at);",
        "CREATE INDEX IF NOT EXISTS ix_rendered_subscription_snapshots_tg_id ON rendered_subscription_snapshots(tg_id);",
        "CREATE INDEX IF NOT EXISTS ix_rendered_subscription_snapshots_created_at ON rendered_subscription_snapshots(created_at);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_node_pool_membership_code_pool ON node_pool_membership(node_code, pool_code);",
        "CREATE INDEX IF NOT EXISTS ix_node_provisioning_jobs_status ON node_provisioning_jobs(status);",
    ]:
        conn.execute(text(sql))

    now_param = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(sep=" ", timespec="seconds")
    conn.execute(
        text(
            """
            INSERT OR IGNORE INTO access_keys (
              tg_id, key_uuid, panel_email, pool_code, state, source, is_primary, created_at, updated_at
            )
            SELECT tg_id, uuid, coalesce(nullif(trim(email), ''), 'user-' || tg_id),
                   CASE
                     WHEN :free_tier_enabled = 1
                          AND upper(coalesce(sub_type, '')) = 'FREE'
                          AND lower(coalesce(current_plan_code, '')) NOT IN ('trial', 'channel_bonus', 'start_99')
                       THEN 'free_pool'
                     ELSE 'premium_pool'
                   END,
                   CASE
                     WHEN coalesce(is_active, 1)
                          AND (
                            :free_tier_enabled = 1
                            OR upper(coalesce(sub_type, '')) <> 'FREE'
                            OR lower(coalesce(current_plan_code, '')) IN ('trial', 'channel_bonus', 'start_99')
                          )
                       THEN 'active'
                     ELSE 'inactive'
                   END,
                   'legacy_user', 1, :now_value, :now_value
            FROM users
            WHERE uuid IS NOT NULL AND trim(uuid) <> '';
            """
        ),
        {"now_value": now_param, "free_tier_enabled": int(free_tier_enabled())},
    )
    conn.execute(
        text(
            """
            INSERT OR IGNORE INTO node_capacity_policy (
                node_code,
                soft_tx_ratio,
                drain_tx_ratio,
                hard_tx_ratio,
                soft_cpu_percent,
                hard_cpu_percent,
                stale_after_seconds,
                max_packet_loss_percent,
                max_tcp_retrans_percent,
                rank_weight,
                allow_free_pool,
                allow_premium_pool,
                is_enabled,
                created_at,
                updated_at
            )
            SELECT code,
                   0.70, 0.82, 0.92,
                   75, 90, 180,
                   2, 5, 100,
                   CASE WHEN lower(code) LIKE '%free%' THEN 1 ELSE 0 END,
                   CASE WHEN lower(code) LIKE '%free%' THEN 0 ELSE 1 END,
                   1,
                   :now_value, :now_value
            FROM nodes
            WHERE code IS NOT NULL AND trim(code) <> '';
            """
        ),
        {"now_value": now_param},
    )
    conn.execute(
        text(
            """
            INSERT OR IGNORE INTO node_pool_membership (node_code, pool_code, is_enabled, source, created_at, updated_at)
            SELECT code,
                   CASE WHEN lower(code) LIKE '%free%' THEN 'free_pool' ELSE 'premium_pool' END,
                   1,
                   'migration', :now_value, :now_value
            FROM nodes
            WHERE code IS NOT NULL AND trim(code) <> '';
            """
        ),
        {"now_value": now_param},
    )


def _ensure_capacity_domain_postgres(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS access_keys (
              id SERIAL PRIMARY KEY,
              tg_id BIGINT NOT NULL,
              key_uuid VARCHAR(36) NOT NULL,
              panel_email VARCHAR(100) NOT NULL,
              node_code VARCHAR(32),
              pool_code VARCHAR(32) NOT NULL DEFAULT 'premium_pool',
              state VARCHAR(32) NOT NULL DEFAULT 'active',
              source VARCHAR(32) NOT NULL DEFAULT 'legacy_user',
              is_primary BOOLEAN NOT NULL DEFAULT TRUE,
              provisioned_at TIMESTAMP,
              last_seen_at TIMESTAMP,
              rotated_at TIMESTAMP,
              revoked_at TIMESTAMP,
              meta_json TEXT,
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS node_capacity_policy (
              id SERIAL PRIMARY KEY,
              node_code VARCHAR(32) NOT NULL,
              max_tx_mbps DOUBLE PRECISION,
              soft_tx_ratio DOUBLE PRECISION NOT NULL DEFAULT 0.70,
              drain_tx_ratio DOUBLE PRECISION NOT NULL DEFAULT 0.82,
              hard_tx_ratio DOUBLE PRECISION NOT NULL DEFAULT 0.92,
              soft_cpu_percent DOUBLE PRECISION NOT NULL DEFAULT 75,
              hard_cpu_percent DOUBLE PRECISION NOT NULL DEFAULT 90,
              stale_after_seconds INTEGER NOT NULL DEFAULT 180,
              max_packet_loss_percent DOUBLE PRECISION NOT NULL DEFAULT 2,
              max_tcp_retrans_percent DOUBLE PRECISION NOT NULL DEFAULT 5,
              rank_weight INTEGER NOT NULL DEFAULT 100,
              allow_free_pool BOOLEAN NOT NULL DEFAULT FALSE,
              allow_premium_pool BOOLEAN NOT NULL DEFAULT TRUE,
              is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
              updated_by BIGINT,
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS node_runtime_metrics (
              id SERIAL PRIMARY KEY,
              node_code VARCHAR(32) NOT NULL,
              sampled_at TIMESTAMP NOT NULL,
              source VARCHAR(64) NOT NULL DEFAULT 'collector',
              batch_id VARCHAR(128),
              provisioned_clients_count INTEGER NOT NULL DEFAULT 0,
              online_connections_hint INTEGER NOT NULL DEFAULT 0,
              network_rx_mbps_1m DOUBLE PRECISION,
              network_tx_mbps_1m DOUBLE PRECISION,
              network_rx_mbps_5m DOUBLE PRECISION,
              network_tx_mbps_5m DOUBLE PRECISION,
              network_total_mbps DOUBLE PRECISION,
              cpu_percent DOUBLE PRECISION,
              memory_used_mb INTEGER,
              memory_total_mb INTEGER,
              tcp_retrans_percent DOUBLE PRECISION,
              packet_loss_percent DOUBLE PRECISION,
              edge_reachability_ok BOOLEAN,
              authenticated_egress_ok BOOLEAN,
              dataplane_ok BOOLEAN,
              dataplane_rtt_ms INTEGER,
              capacity_score DOUBLE PRECISION,
              capacity_state VARCHAR(32) NOT NULL DEFAULT 'unknown',
              reject_reason VARCHAR(64),
              meta_json TEXT
            );
            """
        )
    )
    _postgres_add_column_if_missing(conn, "node_runtime_metrics", "edge_reachability_ok", "BOOLEAN")
    _postgres_add_column_if_missing(conn, "node_runtime_metrics", "authenticated_egress_ok", "BOOLEAN")
    conn.execute(text("CREATE TABLE IF NOT EXISTS key_usage_rollups (id SERIAL PRIMARY KEY, key_id INTEGER, tg_id BIGINT, node_code VARCHAR(32) NOT NULL, panel_email VARCHAR(100), window_bucket_at TIMESTAMP NOT NULL, window_seconds INTEGER NOT NULL DEFAULT 300, upload_bytes BIGINT NOT NULL DEFAULT 0, download_bytes BIGINT NOT NULL DEFAULT 0, total_bytes BIGINT NOT NULL DEFAULT 0, peak_tx_mbps DOUBLE PRECISION, observations INTEGER NOT NULL DEFAULT 0, source VARCHAR(64) NOT NULL DEFAULT 'observer', created_at TIMESTAMP NOT NULL);"))
    conn.execute(text("CREATE TABLE IF NOT EXISTS key_source_observations (id SERIAL PRIMARY KEY, key_id INTEGER, tg_id BIGINT, node_code VARCHAR(32) NOT NULL, panel_email VARCHAR(100), source_ip_hash VARCHAR(64) NOT NULL, source_asn VARCHAR(32), source_country VARCHAR(8), window_bucket_at TIMESTAMP NOT NULL, first_seen_at TIMESTAMP NOT NULL, last_seen_at TIMESTAMP NOT NULL, hit_count INTEGER NOT NULL DEFAULT 0, meta_json TEXT);"))
    conn.execute(text("CREATE TABLE IF NOT EXISTS key_pressure_state (key_id INTEGER PRIMARY KEY, tg_id BIGINT, node_code VARCHAR(32), panel_email VARCHAR(100), state VARCHAR(32) NOT NULL DEFAULT 'ok', pressure_score DOUBLE PRECISION NOT NULL DEFAULT 0, reasons_json TEXT, distinct_source_ips_1h INTEGER NOT NULL DEFAULT 0, distinct_source_ips_24h INTEGER NOT NULL DEFAULT 0, node_count_24h INTEGER NOT NULL DEFAULT 0, traffic_gb_24h DOUBLE PRECISION NOT NULL DEFAULT 0, manual_review_required BOOLEAN NOT NULL DEFAULT FALSE, updated_at TIMESTAMP NOT NULL);"))
    conn.execute(text("CREATE TABLE IF NOT EXISTS subscription_fetch_events (id SERIAL PRIMARY KEY, tg_id BIGINT NOT NULL, token_fp VARCHAR(32) NOT NULL, lookup_mode VARCHAR(32) NOT NULL, client_format VARCHAR(32) NOT NULL, user_agent_hash VARCHAR(64), request_host VARCHAR(255), selected_nodes_json TEXT, excluded_nodes_json TEXT, response_status INTEGER NOT NULL DEFAULT 200, created_at TIMESTAMP NOT NULL);"))
    conn.execute(text("CREATE TABLE IF NOT EXISTS rendered_subscription_snapshots (id SERIAL PRIMARY KEY, fetch_event_id INTEGER, tg_id BIGINT NOT NULL, profile_revision VARCHAR(128), client_format VARCHAR(32) NOT NULL, node_order_json TEXT NOT NULL, excluded_nodes_json TEXT, content_sha256 VARCHAR(64) NOT NULL, created_at TIMESTAMP NOT NULL);"))
    conn.execute(text("CREATE TABLE IF NOT EXISTS node_pool_membership (id SERIAL PRIMARY KEY, node_code VARCHAR(32) NOT NULL, pool_code VARCHAR(32) NOT NULL, is_enabled BOOLEAN NOT NULL DEFAULT TRUE, source VARCHAR(32) NOT NULL DEFAULT 'migration', created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL);"))
    conn.execute(text("CREATE TABLE IF NOT EXISTS node_provisioning_jobs (id SERIAL PRIMARY KEY, account_id VARCHAR(36), entitlement_grant_id VARCHAR(36), tg_id BIGINT, key_id INTEGER, node_code VARCHAR(32), job_type VARCHAR(32) NOT NULL, status VARCHAR(32) NOT NULL DEFAULT 'queued', desired_state_json TEXT, result_json TEXT, attempts INTEGER NOT NULL DEFAULT 0, next_run_at TIMESTAMP, locked_at TIMESTAMP, created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL);"))
    for sql in [
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_access_keys_tg_uuid ON access_keys(tg_id, key_uuid);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_access_keys_node_email ON access_keys(node_code, panel_email);",
        "CREATE INDEX IF NOT EXISTS ix_access_keys_tg_id ON access_keys(tg_id);",
        "CREATE INDEX IF NOT EXISTS ix_access_keys_key_uuid ON access_keys(key_uuid);",
        "CREATE INDEX IF NOT EXISTS ix_access_keys_pool_code ON access_keys(pool_code);",
        "CREATE INDEX IF NOT EXISTS ix_access_keys_state ON access_keys(state);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_node_capacity_policy_code ON node_capacity_policy(node_code);",
        "CREATE INDEX IF NOT EXISTS ix_node_runtime_metrics_node_code ON node_runtime_metrics(node_code);",
        "CREATE INDEX IF NOT EXISTS ix_node_runtime_metrics_sampled_at ON node_runtime_metrics(sampled_at);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_key_usage_rollup_window ON key_usage_rollups(key_id, node_code, window_bucket_at, window_seconds);",
        "CREATE INDEX IF NOT EXISTS ix_key_usage_rollups_tg_id ON key_usage_rollups(tg_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_key_source_window ON key_source_observations(key_id, node_code, source_ip_hash, window_bucket_at);",
        "CREATE INDEX IF NOT EXISTS ix_key_pressure_state_state ON key_pressure_state(state);",
        "CREATE INDEX IF NOT EXISTS ix_subscription_fetch_events_tg_id ON subscription_fetch_events(tg_id);",
        "CREATE INDEX IF NOT EXISTS ix_subscription_fetch_events_created_at ON subscription_fetch_events(created_at);",
        "CREATE INDEX IF NOT EXISTS ix_rendered_subscription_snapshots_tg_id ON rendered_subscription_snapshots(tg_id);",
        "CREATE INDEX IF NOT EXISTS ix_rendered_subscription_snapshots_created_at ON rendered_subscription_snapshots(created_at);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_node_pool_membership_code_pool ON node_pool_membership(node_code, pool_code);",
        "CREATE INDEX IF NOT EXISTS ix_node_provisioning_jobs_status ON node_provisioning_jobs(status);",
    ]:
        conn.execute(text(sql))
    now_param = datetime.now(timezone.utc).replace(tzinfo=None)
    conn.execute(
        text(
            """
            INSERT INTO access_keys (tg_id, key_uuid, panel_email, pool_code, state, source, is_primary, created_at, updated_at)
            SELECT tg_id, uuid, coalesce(nullif(btrim(email), ''), 'user-' || tg_id),
                   CASE
                     WHEN :free_tier_enabled
                          AND upper(coalesce(sub_type, '')) = 'FREE'
                          AND lower(coalesce(current_plan_code, '')) NOT IN ('trial', 'channel_bonus', 'start_99')
                       THEN 'free_pool'
                     ELSE 'premium_pool'
                   END,
                   CASE
                     WHEN coalesce(is_active, TRUE)
                          AND (
                            :free_tier_enabled
                            OR upper(coalesce(sub_type, '')) <> 'FREE'
                            OR lower(coalesce(current_plan_code, '')) IN ('trial', 'channel_bonus', 'start_99')
                          )
                       THEN 'active'
                     ELSE 'inactive'
                   END,
                   'legacy_user', TRUE, :now_value, :now_value
            FROM users
            WHERE uuid IS NOT NULL AND btrim(uuid) <> ''
            ON CONFLICT DO NOTHING;
            """
        ),
        {"now_value": now_param, "free_tier_enabled": bool(free_tier_enabled())},
    )
    conn.execute(
        text(
            """
            INSERT INTO node_capacity_policy (
                node_code,
                soft_tx_ratio,
                drain_tx_ratio,
                hard_tx_ratio,
                soft_cpu_percent,
                hard_cpu_percent,
                stale_after_seconds,
                max_packet_loss_percent,
                max_tcp_retrans_percent,
                rank_weight,
                allow_free_pool,
                allow_premium_pool,
                is_enabled,
                created_at,
                updated_at
            )
            SELECT code,
                   0.70, 0.82, 0.92,
                   75, 90, 180,
                   2, 5, 100,
                   CASE WHEN lower(code) LIKE '%free%' THEN TRUE ELSE FALSE END,
                   CASE WHEN lower(code) LIKE '%free%' THEN FALSE ELSE TRUE END,
                   TRUE,
                   :now_value, :now_value
            FROM nodes
            WHERE code IS NOT NULL AND btrim(code) <> ''
            ON CONFLICT DO NOTHING;
            """
        ),
        {"now_value": now_param},
    )
    conn.execute(
        text(
            """
            INSERT INTO node_pool_membership (node_code, pool_code, is_enabled, source, created_at, updated_at)
            SELECT code,
                   CASE WHEN lower(code) LIKE '%free%' THEN 'free_pool' ELSE 'premium_pool' END,
                   TRUE,
                   'migration', :now_value, :now_value
            FROM nodes
            WHERE code IS NOT NULL AND btrim(code) <> ''
            ON CONFLICT DO NOTHING;
            """
        ),
        {"now_value": now_param},
    )


def _ensure_admin_ops_domain_sqlite(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS provider_traffic_quotas (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              node_code VARCHAR(32) NOT NULL,
              included_bytes BIGINT DEFAULT 0 NOT NULL,
              reset_day INTEGER DEFAULT 1 NOT NULL,
              timezone VARCHAR(64) DEFAULT 'UTC' NOT NULL,
              warning_ratio FLOAT DEFAULT 0.80 NOT NULL,
              critical_ratio FLOAT DEFAULT 0.95 NOT NULL,
              enabled BOOLEAN DEFAULT 1 NOT NULL,
              notes TEXT,
              updated_by BIGINT,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS operator_tasks (
              id VARCHAR(36) PRIMARY KEY,
              environment VARCHAR(32) NOT NULL,
              title VARCHAR(180) NOT NULL,
              owner_operator_id VARCHAR(36),
              owner_team VARCHAR(48),
              status VARCHAR(24) DEFAULT 'open' NOT NULL,
              priority VARCHAR(16) DEFAULT 'normal' NOT NULL,
              due_at DATETIME,
              next_action VARCHAR(500),
              source VARCHAR(64) NOT NULL,
              linked_entity_type VARCHAR(64),
              linked_entity_id VARCHAR(128),
              version INTEGER DEFAULT 1 NOT NULL,
              created_by BIGINT NOT NULL,
              updated_by BIGINT NOT NULL,
              completed_at DATETIME,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL,
              CONSTRAINT ck_operator_tasks_status CHECK (status IN ('open', 'in_progress', 'blocked', 'done', 'cancelled')),
              CONSTRAINT ck_operator_tasks_priority CHECK (priority IN ('critical', 'high', 'normal', 'low')),
              CONSTRAINT fk_operator_tasks_owner_operator FOREIGN KEY(owner_operator_id) REFERENCES admin_operators(id) ON DELETE SET NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS operator_incident_events (
              id VARCHAR(36) PRIMARY KEY,
              incident_id VARCHAR(36) NOT NULL,
              environment VARCHAR(32) NOT NULL,
              incident_version INTEGER NOT NULL,
              event_type VARCHAR(32) NOT NULL,
              from_status VARCHAR(24),
              to_status VARCHAR(24),
              note VARCHAR(2000),
              actor_operator_id VARCHAR(36),
              actor_tg_id BIGINT NOT NULL,
              created_at DATETIME NOT NULL,
              CONSTRAINT fk_operator_incident_events_incident FOREIGN KEY(incident_id) REFERENCES service_incidents(id) ON DELETE CASCADE,
              CONSTRAINT uq_operator_incident_event_version UNIQUE(incident_id, incident_version)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS operator_incident_links (
              id VARCHAR(36) PRIMARY KEY,
              incident_id VARCHAR(36) NOT NULL,
              environment VARCHAR(32) NOT NULL,
              entity_type VARCHAR(64) NOT NULL,
              entity_id VARCHAR(128) NOT NULL,
              label VARCHAR(180),
              created_by BIGINT NOT NULL,
              created_at DATETIME NOT NULL,
              CONSTRAINT fk_operator_incident_links_incident FOREIGN KEY(incident_id) REFERENCES service_incidents(id) ON DELETE CASCADE,
              CONSTRAINT uq_operator_incident_link_entity UNIQUE(incident_id, entity_type, entity_id)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS provider_traffic_quota_audit (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              quota_id INTEGER,
              node_code VARCHAR(32) NOT NULL,
              actor_tg_id BIGINT,
              action VARCHAR(32) NOT NULL,
              before_json TEXT,
              after_json TEXT,
              created_at DATETIME NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS ops_alerts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              fingerprint VARCHAR(160) NOT NULL,
              source VARCHAR(64) NOT NULL,
              severity VARCHAR(16) NOT NULL,
              status VARCHAR(24) DEFAULT 'active' NOT NULL,
              title VARCHAR(180) NOT NULL,
              body VARCHAR(1000),
              node_code VARCHAR(32),
              tg_id BIGINT,
              key_id INTEGER,
              first_seen_at DATETIME NOT NULL,
              last_seen_at DATETIME NOT NULL,
              resolved_at DATETIME,
              acknowledged_at DATETIME,
              acknowledged_by BIGINT,
              silence_until DATETIME,
              last_delivery_at DATETIME,
              last_delivery_status VARCHAR(64),
              metadata_json TEXT,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL
            );
            """
        )
    )
    for table, cols in {
        "provider_traffic_quotas": [
            ("included_bytes", "BIGINT DEFAULT 0 NOT NULL"),
            ("reset_day", "INTEGER DEFAULT 1 NOT NULL"),
            ("timezone", "VARCHAR(64) DEFAULT 'UTC' NOT NULL"),
            ("warning_ratio", "FLOAT DEFAULT 0.80 NOT NULL"),
            ("critical_ratio", "FLOAT DEFAULT 0.95 NOT NULL"),
            ("enabled", "BOOLEAN DEFAULT 1 NOT NULL"),
            ("notes", "TEXT"),
            ("updated_by", "BIGINT"),
            ("created_at", "DATETIME"),
            ("updated_at", "DATETIME"),
        ],
        "ops_alerts": [
            ("source", "VARCHAR(64) DEFAULT 'ops' NOT NULL"),
            ("severity", "VARCHAR(16) DEFAULT 'warning' NOT NULL"),
            ("status", "VARCHAR(24) DEFAULT 'active' NOT NULL"),
            ("body", "VARCHAR(1000)"),
            ("node_code", "VARCHAR(32)"),
            ("tg_id", "BIGINT"),
            ("key_id", "INTEGER"),
            ("resolved_at", "DATETIME"),
            ("acknowledged_at", "DATETIME"),
            ("acknowledged_by", "BIGINT"),
            ("silence_until", "DATETIME"),
            ("last_delivery_at", "DATETIME"),
            ("last_delivery_status", "VARCHAR(64)"),
            ("metadata_json", "TEXT"),
            ("environment", "VARCHAR(32) DEFAULT 'production' NOT NULL"),
            ("incident_id", "VARCHAR(36)"),
            ("version", "INTEGER DEFAULT 1 NOT NULL"),
            ("created_at", "DATETIME"),
            ("updated_at", "DATETIME"),
        ],
        "service_incidents": [
            ("environment", "VARCHAR(32) DEFAULT 'production' NOT NULL"),
            ("workflow_status", "VARCHAR(24) DEFAULT 'investigating' NOT NULL"),
            ("workflow_version", "INTEGER DEFAULT 1 NOT NULL"),
            ("owner_operator_id", "VARCHAR(36)"),
            ("owner_team", "VARCHAR(48)"),
            ("impact", "VARCHAR(1000)"),
            ("next_update_at", "DATETIME"),
            ("runbook_url", "VARCHAR(500)"),
            ("communications_summary", "VARCHAR(2000)"),
            ("postmortem_status", "VARCHAR(24) DEFAULT 'not_required' NOT NULL"),
            ("postmortem_url", "VARCHAR(500)"),
        ],
    }.items():
        if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table;"), {"table": table}).fetchone():
            for col, ddl in cols:
                if not _sqlite_column_exists(conn, table, col):
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl};"))
    for sql in [
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_provider_traffic_quotas_node_code ON provider_traffic_quotas(node_code);",
        "CREATE INDEX IF NOT EXISTS ix_provider_traffic_quotas_enabled ON provider_traffic_quotas(enabled);",
        "CREATE INDEX IF NOT EXISTS ix_provider_traffic_quota_audit_node_code ON provider_traffic_quota_audit(node_code);",
        "CREATE INDEX IF NOT EXISTS ix_provider_traffic_quota_audit_created_at ON provider_traffic_quota_audit(created_at);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_ops_alerts_fingerprint ON ops_alerts(fingerprint);",
        "CREATE INDEX IF NOT EXISTS ix_ops_alerts_source ON ops_alerts(source);",
        "CREATE INDEX IF NOT EXISTS ix_ops_alerts_severity ON ops_alerts(severity);",
        "CREATE INDEX IF NOT EXISTS ix_ops_alerts_status ON ops_alerts(status);",
        "CREATE INDEX IF NOT EXISTS ix_ops_alerts_node_code ON ops_alerts(node_code);",
        "CREATE INDEX IF NOT EXISTS ix_ops_alerts_last_seen_at ON ops_alerts(last_seen_at);",
        "CREATE INDEX IF NOT EXISTS ix_ops_alerts_environment ON ops_alerts(environment);",
        "CREATE INDEX IF NOT EXISTS ix_ops_alerts_incident_id ON ops_alerts(incident_id);",
        "CREATE INDEX IF NOT EXISTS ix_operator_tasks_environment_status ON operator_tasks(environment, status);",
        "CREATE INDEX IF NOT EXISTS ix_operator_tasks_environment_team ON operator_tasks(environment, owner_team);",
        "CREATE INDEX IF NOT EXISTS ix_operator_tasks_owner_operator_id ON operator_tasks(owner_operator_id);",
        "CREATE INDEX IF NOT EXISTS ix_operator_tasks_due_at ON operator_tasks(due_at);",
        "CREATE INDEX IF NOT EXISTS ix_operator_tasks_linked_entity ON operator_tasks(linked_entity_type, linked_entity_id);",
        "CREATE INDEX IF NOT EXISTS ix_operator_incident_events_incident_created ON operator_incident_events(incident_id, created_at);",
        "CREATE INDEX IF NOT EXISTS ix_operator_incident_events_environment ON operator_incident_events(environment);",
        "CREATE INDEX IF NOT EXISTS ix_operator_incident_links_entity ON operator_incident_links(entity_type, entity_id);",
        "CREATE INDEX IF NOT EXISTS ix_operator_incident_links_environment ON operator_incident_links(environment);",
    ]:
        conn.execute(text(sql))
    if conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='service_incidents';")
    ).fetchone():
        for sql in (
            "CREATE INDEX IF NOT EXISTS ix_service_incidents_environment ON service_incidents(environment);",
            "CREATE INDEX IF NOT EXISTS ix_service_incidents_workflow_status ON service_incidents(workflow_status);",
            "CREATE INDEX IF NOT EXISTS ix_service_incidents_owner_operator_id ON service_incidents(owner_operator_id);",
            "CREATE INDEX IF NOT EXISTS ix_service_incidents_owner_team ON service_incidents(owner_team);",
            "CREATE INDEX IF NOT EXISTS ix_service_incidents_next_update_at ON service_incidents(next_update_at);",
        ):
            conn.execute(text(sql))


def _ensure_admin_ops_domain_postgres(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS provider_traffic_quotas (
              id SERIAL PRIMARY KEY,
              node_code VARCHAR(32) NOT NULL,
              included_bytes BIGINT NOT NULL DEFAULT 0,
              reset_day INTEGER NOT NULL DEFAULT 1,
              timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
              warning_ratio DOUBLE PRECISION NOT NULL DEFAULT 0.80,
              critical_ratio DOUBLE PRECISION NOT NULL DEFAULT 0.95,
              enabled BOOLEAN NOT NULL DEFAULT TRUE,
              notes TEXT,
              updated_by BIGINT,
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS operator_tasks (
              id VARCHAR(36) PRIMARY KEY,
              environment VARCHAR(32) NOT NULL,
              title VARCHAR(180) NOT NULL,
              owner_operator_id VARCHAR(36) REFERENCES admin_operators(id) ON DELETE SET NULL,
              owner_team VARCHAR(48),
              status VARCHAR(24) NOT NULL DEFAULT 'open',
              priority VARCHAR(16) NOT NULL DEFAULT 'normal',
              due_at TIMESTAMP,
              next_action VARCHAR(500),
              source VARCHAR(64) NOT NULL,
              linked_entity_type VARCHAR(64),
              linked_entity_id VARCHAR(128),
              version INTEGER NOT NULL DEFAULT 1,
              created_by BIGINT NOT NULL,
              updated_by BIGINT NOT NULL,
              completed_at TIMESTAMP,
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL,
              CONSTRAINT ck_operator_tasks_status CHECK (status IN ('open', 'in_progress', 'blocked', 'done', 'cancelled')),
              CONSTRAINT ck_operator_tasks_priority CHECK (priority IN ('critical', 'high', 'normal', 'low'))
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS operator_incident_events (
              id VARCHAR(36) PRIMARY KEY,
              incident_id VARCHAR(36) NOT NULL REFERENCES service_incidents(id) ON DELETE CASCADE,
              environment VARCHAR(32) NOT NULL,
              incident_version INTEGER NOT NULL,
              event_type VARCHAR(32) NOT NULL,
              from_status VARCHAR(24),
              to_status VARCHAR(24),
              note VARCHAR(2000),
              actor_operator_id VARCHAR(36),
              actor_tg_id BIGINT NOT NULL,
              created_at TIMESTAMP NOT NULL,
              CONSTRAINT uq_operator_incident_event_version UNIQUE(incident_id, incident_version)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS operator_incident_links (
              id VARCHAR(36) PRIMARY KEY,
              incident_id VARCHAR(36) NOT NULL REFERENCES service_incidents(id) ON DELETE CASCADE,
              environment VARCHAR(32) NOT NULL,
              entity_type VARCHAR(64) NOT NULL,
              entity_id VARCHAR(128) NOT NULL,
              label VARCHAR(180),
              created_by BIGINT NOT NULL,
              created_at TIMESTAMP NOT NULL,
              CONSTRAINT uq_operator_incident_link_entity UNIQUE(incident_id, entity_type, entity_id)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS provider_traffic_quota_audit (
              id SERIAL PRIMARY KEY,
              quota_id INTEGER,
              node_code VARCHAR(32) NOT NULL,
              actor_tg_id BIGINT,
              action VARCHAR(32) NOT NULL,
              before_json TEXT,
              after_json TEXT,
              created_at TIMESTAMP NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS ops_alerts (
              id SERIAL PRIMARY KEY,
              fingerprint VARCHAR(160) NOT NULL,
              source VARCHAR(64) NOT NULL,
              severity VARCHAR(16) NOT NULL,
              status VARCHAR(24) NOT NULL DEFAULT 'active',
              title VARCHAR(180) NOT NULL,
              body VARCHAR(1000),
              node_code VARCHAR(32),
              tg_id BIGINT,
              key_id INTEGER,
              first_seen_at TIMESTAMP NOT NULL,
              last_seen_at TIMESTAMP NOT NULL,
              resolved_at TIMESTAMP,
              acknowledged_at TIMESTAMP,
              acknowledged_by BIGINT,
              silence_until TIMESTAMP,
              last_delivery_at TIMESTAMP,
              last_delivery_status VARCHAR(64),
              metadata_json TEXT,
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL
            );
            """
        )
    )
    for table, column, ddl in [
        ("provider_traffic_quotas", "included_bytes", "BIGINT DEFAULT 0"),
        ("provider_traffic_quotas", "reset_day", "INTEGER DEFAULT 1"),
        ("provider_traffic_quotas", "timezone", "VARCHAR(64) DEFAULT 'UTC'"),
        ("provider_traffic_quotas", "warning_ratio", "DOUBLE PRECISION DEFAULT 0.80"),
        ("provider_traffic_quotas", "critical_ratio", "DOUBLE PRECISION DEFAULT 0.95"),
        ("provider_traffic_quotas", "enabled", "BOOLEAN DEFAULT TRUE"),
        ("provider_traffic_quotas", "notes", "TEXT"),
        ("provider_traffic_quotas", "updated_by", "BIGINT"),
        ("ops_alerts", "body", "VARCHAR(1000)"),
        ("ops_alerts", "node_code", "VARCHAR(32)"),
        ("ops_alerts", "tg_id", "BIGINT"),
        ("ops_alerts", "key_id", "INTEGER"),
        ("ops_alerts", "resolved_at", "TIMESTAMP"),
        ("ops_alerts", "acknowledged_at", "TIMESTAMP"),
        ("ops_alerts", "acknowledged_by", "BIGINT"),
        ("ops_alerts", "silence_until", "TIMESTAMP"),
        ("ops_alerts", "last_delivery_at", "TIMESTAMP"),
        ("ops_alerts", "last_delivery_status", "VARCHAR(64)"),
        ("ops_alerts", "metadata_json", "TEXT"),
        ("ops_alerts", "environment", "VARCHAR(32) DEFAULT 'production'"),
        ("ops_alerts", "incident_id", "VARCHAR(36)"),
        ("ops_alerts", "version", "INTEGER DEFAULT 1"),
        ("service_incidents", "environment", "VARCHAR(32) DEFAULT 'production'"),
        ("service_incidents", "workflow_status", "VARCHAR(24) DEFAULT 'investigating'"),
        ("service_incidents", "workflow_version", "INTEGER DEFAULT 1"),
        ("service_incidents", "owner_operator_id", "VARCHAR(36)"),
        ("service_incidents", "owner_team", "VARCHAR(48)"),
        ("service_incidents", "impact", "VARCHAR(1000)"),
        ("service_incidents", "next_update_at", "TIMESTAMP"),
        ("service_incidents", "runbook_url", "VARCHAR(500)"),
        ("service_incidents", "communications_summary", "VARCHAR(2000)"),
        ("service_incidents", "postmortem_status", "VARCHAR(24) DEFAULT 'not_required'"),
        ("service_incidents", "postmortem_url", "VARCHAR(500)"),
    ]:
        _postgres_add_column_if_missing(conn, table, column, ddl)
    for sql in [
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_provider_traffic_quotas_node_code ON provider_traffic_quotas(node_code);",
        "CREATE INDEX IF NOT EXISTS ix_provider_traffic_quotas_enabled ON provider_traffic_quotas(enabled);",
        "CREATE INDEX IF NOT EXISTS ix_provider_traffic_quota_audit_node_code ON provider_traffic_quota_audit(node_code);",
        "CREATE INDEX IF NOT EXISTS ix_provider_traffic_quota_audit_created_at ON provider_traffic_quota_audit(created_at);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_ops_alerts_fingerprint ON ops_alerts(fingerprint);",
        "CREATE INDEX IF NOT EXISTS ix_ops_alerts_source ON ops_alerts(source);",
        "CREATE INDEX IF NOT EXISTS ix_ops_alerts_severity ON ops_alerts(severity);",
        "CREATE INDEX IF NOT EXISTS ix_ops_alerts_status ON ops_alerts(status);",
        "CREATE INDEX IF NOT EXISTS ix_ops_alerts_node_code ON ops_alerts(node_code);",
        "CREATE INDEX IF NOT EXISTS ix_ops_alerts_last_seen_at ON ops_alerts(last_seen_at);",
        "CREATE INDEX IF NOT EXISTS ix_ops_alerts_environment ON ops_alerts(environment);",
        "CREATE INDEX IF NOT EXISTS ix_ops_alerts_incident_id ON ops_alerts(incident_id);",
        "CREATE INDEX IF NOT EXISTS ix_operator_tasks_environment_status ON operator_tasks(environment, status);",
        "CREATE INDEX IF NOT EXISTS ix_operator_tasks_environment_team ON operator_tasks(environment, owner_team);",
        "CREATE INDEX IF NOT EXISTS ix_operator_tasks_owner_operator_id ON operator_tasks(owner_operator_id);",
        "CREATE INDEX IF NOT EXISTS ix_operator_tasks_due_at ON operator_tasks(due_at);",
        "CREATE INDEX IF NOT EXISTS ix_operator_tasks_linked_entity ON operator_tasks(linked_entity_type, linked_entity_id);",
        "CREATE INDEX IF NOT EXISTS ix_operator_incident_events_incident_created ON operator_incident_events(incident_id, created_at);",
        "CREATE INDEX IF NOT EXISTS ix_operator_incident_events_environment ON operator_incident_events(environment);",
        "CREATE INDEX IF NOT EXISTS ix_operator_incident_links_entity ON operator_incident_links(entity_type, entity_id);",
        "CREATE INDEX IF NOT EXISTS ix_operator_incident_links_environment ON operator_incident_links(environment);",
        "CREATE INDEX IF NOT EXISTS ix_service_incidents_environment ON service_incidents(environment);",
        "CREATE INDEX IF NOT EXISTS ix_service_incidents_workflow_status ON service_incidents(workflow_status);",
        "CREATE INDEX IF NOT EXISTS ix_service_incidents_owner_operator_id ON service_incidents(owner_operator_id);",
        "CREATE INDEX IF NOT EXISTS ix_service_incidents_owner_team ON service_incidents(owner_team);",
        "CREATE INDEX IF NOT EXISTS ix_service_incidents_next_update_at ON service_incidents(next_update_at);",
    ]:
        conn.execute(text(sql))


def _ensure_ru_probe_domain_sqlite(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS ru_probe_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id VARCHAR(36) NOT NULL,
              schema_version INTEGER NOT NULL,
              origin VARCHAR(16) NOT NULL,
              probe_host_id VARCHAR(64) NOT NULL,
              probe_host_label VARCHAR(128) NOT NULL,
              probe_public_ip VARCHAR(64),
              runner_version VARCHAR(64) NOT NULL,
              started_at DATETIME NOT NULL,
              finished_at DATETIME NOT NULL,
              received_at DATETIME NOT NULL,
              manifest_revision VARCHAR(64) NOT NULL,
              execution_status VARCHAR(32) NOT NULL,
              evidence_code VARCHAR(64),
              environment_verdict VARCHAR(32) NOT NULL,
              release_verdict VARCHAR(32) NOT NULL,
              current_eligible BOOLEAN NOT NULL DEFAULT FALSE,
              ineligible_reason VARCHAR(64),
              google_reachable BOOLEAN,
              xhttp_alive BOOLEAN,
              hysteria_alive BOOLEAN,
              server_reason VARCHAR(500),
              server_summary VARCHAR(1000),
              artifact_sha256 VARCHAR(64) NOT NULL,
              ingest_key_id VARCHAR(128) NOT NULL,
              retention_hold BOOLEAN NOT NULL DEFAULT FALSE,
              retention_hold_reason VARCHAR(500),
              retention_held_at DATETIME,
              CONSTRAINT uq_ru_probe_runs_run_id UNIQUE (run_id)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS ru_probe_target_results (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_db_id INTEGER NOT NULL,
              target_id VARCHAR(128) NOT NULL,
              target_kind VARCHAR(32) NOT NULL,
              scope VARCHAR(32) NOT NULL,
              node_code VARCHAR(32),
              endpoint_fingerprint VARCHAR(64) NOT NULL,
              endpoint_host VARCHAR(255) NOT NULL,
              endpoint_port INTEGER NOT NULL,
              endpoint_sni VARCHAR(255),
              requested_address_families_json JSON NOT NULL,
              transport_metadata_json JSON NOT NULL,
              transport_profile VARCHAR(64) NOT NULL,
              probe_mode VARCHAR(64) NOT NULL,
              http_path VARCHAR(512),
              min_body_bytes INTEGER,
              local_probe_profile_id VARCHAR(128),
              observed_at DATETIME NOT NULL,
              overall_status VARCHAR(32) NOT NULL,
              current_eligible BOOLEAN NOT NULL DEFAULT FALSE,
              ineligible_reason VARCHAR(64),
              dns_status VARCHAR(32) NOT NULL,
              dns_latency_ms INTEGER,
              tcp_status VARCHAR(32) NOT NULL,
              tcp_latency_ms INTEGER,
              tls_status VARCHAR(32) NOT NULL,
              tls_latency_ms INTEGER,
              http_large_body_status VARCHAR(32) NOT NULL,
              http_large_body_latency_ms INTEGER,
              transport_handshake_status VARCHAR(32) NOT NULL,
              transport_handshake_latency_ms INTEGER,
              ipv4_status VARCHAR(32) NOT NULL,
              ipv6_status VARCHAR(32) NOT NULL,
              reported_transport_handshake_status VARCHAR(32) NOT NULL,
              reported_transport_classification VARCHAR(64) NOT NULL,
              server_reason_code VARCHAR(64),
              server_detail VARCHAR(500),
              CONSTRAINT fk_ru_probe_target_results_run FOREIGN KEY (run_db_id) REFERENCES ru_probe_runs(id) ON DELETE CASCADE,
              CONSTRAINT uq_ru_probe_target_run_target UNIQUE (run_db_id, target_id)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS ru_probe_uploader_heartbeats (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              probe_host_id VARCHAR(64) NOT NULL,
              observed_at DATETIME NOT NULL,
              received_at DATETIME NOT NULL,
              service_version VARCHAR(64) NOT NULL,
              pending_count INTEGER NOT NULL DEFAULT 0,
              blocked_count INTEGER NOT NULL DEFAULT 0,
              quarantine_count INTEGER NOT NULL DEFAULT 0,
              oldest_pending_at DATETIME,
              archive_write_ok BOOLEAN NOT NULL DEFAULT FALSE,
              disk_free_bytes BIGINT,
              disk_state VARCHAR(32) NOT NULL,
              last_error_code VARCHAR(64),
              ingest_key_id VARCHAR(128) NOT NULL,
              CONSTRAINT uq_ru_probe_uploader_heartbeat_host_observed UNIQUE (probe_host_id, observed_at)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS internal_ingest_nonces (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              key_scope VARCHAR(64) NOT NULL,
              key_id VARCHAR(128) NOT NULL,
              nonce_hash VARCHAR(64) NOT NULL,
              request_path VARCHAR(512) NOT NULL,
              request_timestamp DATETIME NOT NULL,
              body_sha256 VARCHAR(64) NOT NULL,
              expires_at DATETIME NOT NULL,
              created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT uq_internal_ingest_nonce_scope_key_hash UNIQUE (key_scope, key_id, nonce_hash)
            );
            """
        )
    )
    for sql in [
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_runs_finished_at ON ru_probe_runs(finished_at);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_runs_release_verdict ON ru_probe_runs(release_verdict);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_runs_current_eligible ON ru_probe_runs(current_eligible);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_runs_probe_host_label ON ru_probe_runs(probe_host_label);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_target_results_node_code ON ru_probe_target_results(node_code);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_target_results_target_kind ON ru_probe_target_results(target_kind);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_target_results_overall_status ON ru_probe_target_results(overall_status);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_target_results_node_observed_at ON ru_probe_target_results(node_code, observed_at DESC);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_target_results_run_node ON ru_probe_target_results(run_db_id, node_code);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_uploader_heartbeats_received_at ON ru_probe_uploader_heartbeats(received_at);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_uploader_heartbeats_probe_host_id ON ru_probe_uploader_heartbeats(probe_host_id);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_uploader_heartbeats_host_observed_at ON ru_probe_uploader_heartbeats(probe_host_id, observed_at DESC);",
        "CREATE INDEX IF NOT EXISTS ix_internal_ingest_nonces_expires_at ON internal_ingest_nonces(expires_at);",
    ]:
        conn.execute(text(sql))


def _ensure_ru_probe_domain_postgres(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS ru_probe_runs (
              id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
              run_id VARCHAR(36) NOT NULL,
              schema_version INTEGER NOT NULL,
              origin VARCHAR(16) NOT NULL,
              probe_host_id VARCHAR(64) NOT NULL,
              probe_host_label VARCHAR(128) NOT NULL,
              probe_public_ip VARCHAR(64),
              runner_version VARCHAR(64) NOT NULL,
              started_at TIMESTAMPTZ NOT NULL,
              finished_at TIMESTAMPTZ NOT NULL,
              received_at TIMESTAMPTZ NOT NULL,
              manifest_revision VARCHAR(64) NOT NULL,
              execution_status VARCHAR(32) NOT NULL,
              evidence_code VARCHAR(64),
              environment_verdict VARCHAR(32) NOT NULL,
              release_verdict VARCHAR(32) NOT NULL,
              current_eligible BOOLEAN NOT NULL DEFAULT FALSE,
              ineligible_reason VARCHAR(64),
              google_reachable BOOLEAN,
              xhttp_alive BOOLEAN,
              hysteria_alive BOOLEAN,
              server_reason VARCHAR(500),
              server_summary VARCHAR(1000),
              artifact_sha256 VARCHAR(64) NOT NULL,
              ingest_key_id VARCHAR(128) NOT NULL,
              retention_hold BOOLEAN NOT NULL DEFAULT FALSE,
              retention_hold_reason VARCHAR(500),
              retention_held_at TIMESTAMPTZ,
              CONSTRAINT uq_ru_probe_runs_run_id UNIQUE (run_id)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS ru_probe_target_results (
              id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
              run_db_id INTEGER NOT NULL,
              target_id VARCHAR(128) NOT NULL,
              target_kind VARCHAR(32) NOT NULL,
              scope VARCHAR(32) NOT NULL,
              node_code VARCHAR(32),
              endpoint_fingerprint VARCHAR(64) NOT NULL,
              endpoint_host VARCHAR(255) NOT NULL,
              endpoint_port INTEGER NOT NULL,
              endpoint_sni VARCHAR(255),
              requested_address_families_json JSONB NOT NULL,
              transport_metadata_json JSONB NOT NULL,
              transport_profile VARCHAR(64) NOT NULL,
              probe_mode VARCHAR(64) NOT NULL,
              http_path VARCHAR(512),
              min_body_bytes INTEGER,
              local_probe_profile_id VARCHAR(128),
              observed_at TIMESTAMPTZ NOT NULL,
              overall_status VARCHAR(32) NOT NULL,
              current_eligible BOOLEAN NOT NULL DEFAULT FALSE,
              ineligible_reason VARCHAR(64),
              dns_status VARCHAR(32) NOT NULL,
              dns_latency_ms INTEGER,
              tcp_status VARCHAR(32) NOT NULL,
              tcp_latency_ms INTEGER,
              tls_status VARCHAR(32) NOT NULL,
              tls_latency_ms INTEGER,
              http_large_body_status VARCHAR(32) NOT NULL,
              http_large_body_latency_ms INTEGER,
              transport_handshake_status VARCHAR(32) NOT NULL,
              transport_handshake_latency_ms INTEGER,
              ipv4_status VARCHAR(32) NOT NULL,
              ipv6_status VARCHAR(32) NOT NULL,
              reported_transport_handshake_status VARCHAR(32) NOT NULL,
              reported_transport_classification VARCHAR(64) NOT NULL,
              server_reason_code VARCHAR(64),
              server_detail VARCHAR(500),
              CONSTRAINT fk_ru_probe_target_results_run
                FOREIGN KEY (run_db_id) REFERENCES ru_probe_runs(id)
                ON DELETE CASCADE,
              CONSTRAINT uq_ru_probe_target_run_target
                UNIQUE (run_db_id, target_id)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS ru_probe_uploader_heartbeats (
              id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
              probe_host_id VARCHAR(64) NOT NULL,
              observed_at TIMESTAMPTZ NOT NULL,
              received_at TIMESTAMPTZ NOT NULL,
              service_version VARCHAR(64) NOT NULL,
              pending_count INTEGER NOT NULL DEFAULT 0,
              blocked_count INTEGER NOT NULL DEFAULT 0,
              quarantine_count INTEGER NOT NULL DEFAULT 0,
              oldest_pending_at TIMESTAMPTZ,
              archive_write_ok BOOLEAN NOT NULL DEFAULT FALSE,
              disk_free_bytes BIGINT,
              disk_state VARCHAR(32) NOT NULL,
              last_error_code VARCHAR(64),
              ingest_key_id VARCHAR(128) NOT NULL,
              CONSTRAINT uq_ru_probe_uploader_heartbeat_host_observed
                UNIQUE (probe_host_id, observed_at)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS internal_ingest_nonces (
              id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
              key_scope VARCHAR(64) NOT NULL,
              key_id VARCHAR(128) NOT NULL,
              nonce_hash VARCHAR(64) NOT NULL,
              request_path VARCHAR(512) NOT NULL,
              request_timestamp TIMESTAMPTZ NOT NULL,
              body_sha256 VARCHAR(64) NOT NULL,
              expires_at TIMESTAMPTZ NOT NULL,
              created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT uq_internal_ingest_nonce_scope_key_hash
                UNIQUE (key_scope, key_id, nonce_hash)
            );
            """
        )
    )
    for sql in [
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_runs_finished_at ON ru_probe_runs(finished_at);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_runs_release_verdict ON ru_probe_runs(release_verdict);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_runs_current_eligible ON ru_probe_runs(current_eligible);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_runs_probe_host_label ON ru_probe_runs(probe_host_label);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_target_results_node_code ON ru_probe_target_results(node_code);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_target_results_target_kind ON ru_probe_target_results(target_kind);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_target_results_overall_status ON ru_probe_target_results(overall_status);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_target_results_node_observed_at ON ru_probe_target_results(node_code, observed_at DESC);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_target_results_run_node ON ru_probe_target_results(run_db_id, node_code);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_uploader_heartbeats_received_at ON ru_probe_uploader_heartbeats(received_at);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_uploader_heartbeats_probe_host_id ON ru_probe_uploader_heartbeats(probe_host_id);",
        "CREATE INDEX IF NOT EXISTS ix_ru_probe_uploader_heartbeats_host_observed_at ON ru_probe_uploader_heartbeats(probe_host_id, observed_at DESC);",
        "CREATE INDEX IF NOT EXISTS ix_internal_ingest_nonces_expires_at ON internal_ingest_nonces(expires_at);",
    ]:
        conn.execute(text(sql))


def _ensure_release_evidence_domain_sqlite(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS release_candidates (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              candidate_id VARCHAR(64) NOT NULL,
              component VARCHAR(64) NOT NULL,
              version VARCHAR(128) NOT NULL,
              revision VARCHAR(128) NOT NULL,
              artifact_sha256 VARCHAR(64) NOT NULL,
              canonical_descriptor_json TEXT NOT NULL,
              descriptor_sha256 VARCHAR(64) NOT NULL,
              ingest_key_id VARCHAR(128) NOT NULL,
              imported_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT uq_release_candidates_candidate_id UNIQUE (candidate_id)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS release_origin_evidence (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              candidate_id VARCHAR(64) NOT NULL,
              origin VARCHAR(16) NOT NULL,
              check_name VARCHAR(128) NOT NULL,
              status VARCHAR(32) NOT NULL,
              evidence_sha256 VARCHAR(64) NOT NULL,
              observed_at DATETIME NOT NULL,
              detail_json TEXT NOT NULL,
              ru_probe_run_id INTEGER,
              imported_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT fk_release_origin_evidence_candidate FOREIGN KEY (candidate_id) REFERENCES release_candidates(candidate_id) ON DELETE RESTRICT,
              CONSTRAINT fk_release_origin_evidence_ru_probe_run FOREIGN KEY (ru_probe_run_id) REFERENCES ru_probe_runs(id) ON DELETE RESTRICT,
              CONSTRAINT uq_release_origin_evidence_hash UNIQUE (evidence_sha256)
            );
            """
        )
    )
    for sql in [
        "CREATE INDEX IF NOT EXISTS ix_release_candidates_imported_at ON release_candidates(imported_at);",
        "CREATE INDEX IF NOT EXISTS ix_release_candidates_component ON release_candidates(component);",
        "CREATE INDEX IF NOT EXISTS ix_release_origin_evidence_candidate_origin ON release_origin_evidence(candidate_id, origin);",
        "CREATE INDEX IF NOT EXISTS ix_release_origin_evidence_observed_at ON release_origin_evidence(observed_at);",
        "CREATE INDEX IF NOT EXISTS ix_release_origin_evidence_ru_probe_run_id ON release_origin_evidence(ru_probe_run_id);",
    ]:
        conn.execute(text(sql))


def _ensure_release_evidence_domain_postgres(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS release_candidates (
              id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
              candidate_id VARCHAR(64) NOT NULL,
              component VARCHAR(64) NOT NULL,
              version VARCHAR(128) NOT NULL,
              revision VARCHAR(128) NOT NULL,
              artifact_sha256 VARCHAR(64) NOT NULL,
              canonical_descriptor_json TEXT NOT NULL,
              descriptor_sha256 VARCHAR(64) NOT NULL,
              ingest_key_id VARCHAR(128) NOT NULL,
              imported_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT uq_release_candidates_candidate_id
                UNIQUE (candidate_id)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS release_origin_evidence (
              id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
              candidate_id VARCHAR(64) NOT NULL,
              origin VARCHAR(16) NOT NULL,
              check_name VARCHAR(128) NOT NULL,
              status VARCHAR(32) NOT NULL,
              evidence_sha256 VARCHAR(64) NOT NULL,
              observed_at TIMESTAMPTZ NOT NULL,
              detail_json TEXT NOT NULL,
              ru_probe_run_id INTEGER,
              imported_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT fk_release_origin_evidence_candidate
                FOREIGN KEY (candidate_id) REFERENCES release_candidates(candidate_id)
                ON DELETE RESTRICT,
              CONSTRAINT fk_release_origin_evidence_ru_probe_run
                FOREIGN KEY (ru_probe_run_id) REFERENCES ru_probe_runs(id)
                ON DELETE RESTRICT,
              CONSTRAINT uq_release_origin_evidence_hash
                UNIQUE (evidence_sha256)
            );
            """
        )
    )
    for sql in [
        "CREATE INDEX IF NOT EXISTS ix_release_candidates_imported_at ON release_candidates(imported_at);",
        "CREATE INDEX IF NOT EXISTS ix_release_candidates_component ON release_candidates(component);",
        "CREATE INDEX IF NOT EXISTS ix_release_origin_evidence_candidate_origin ON release_origin_evidence(candidate_id, origin);",
        "CREATE INDEX IF NOT EXISTS ix_release_origin_evidence_observed_at ON release_origin_evidence(observed_at);",
        "CREATE INDEX IF NOT EXISTS ix_release_origin_evidence_ru_probe_run_id ON release_origin_evidence(ru_probe_run_id);",
    ]:
        conn.execute(text(sql))


def _ensure_admin_action_intent_domain_sqlite(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS admin_action_intents (
              id VARCHAR(36) NOT NULL PRIMARY KEY,
              actor_tg_id BIGINT NOT NULL,
              action VARCHAR(64) NOT NULL,
              target_type VARCHAR(32) NOT NULL,
              target_id VARCHAR(128) NOT NULL,
              risk_level VARCHAR(8) NOT NULL,
              executor_kind VARCHAR(16) NOT NULL,
              canonical_payload_json TEXT NOT NULL,
              payload_hash VARCHAR(64) NOT NULL,
              preview_snapshot_json TEXT NOT NULL,
              snapshot_hash VARCHAR(64) NOT NULL,
              confirmation_challenge_kind VARCHAR(32) NOT NULL,
              confirmation_challenge_hash VARCHAR(64) NOT NULL,
              entity_version_hash VARCHAR(64) NOT NULL,
              status VARCHAR(16) NOT NULL DEFAULT 'prepared',
              expires_at DATETIME NOT NULL,
              consumed_at DATETIME,
              client_idempotency_key VARCHAR(36),
              result_code VARCHAR(64),
              result_summary_json TEXT,
              result_hash VARCHAR(64),
              external_error_hash VARCHAR(64),
              admin_audit_id INTEGER,
              created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT uq_admin_action_intents_idempotency UNIQUE (client_idempotency_key),
              CONSTRAINT fk_admin_action_intents_audit FOREIGN KEY (admin_audit_id) REFERENCES admin_audit(id) ON DELETE RESTRICT
            );
            """
        )
    )
    for sql in [
        "CREATE INDEX IF NOT EXISTS ix_admin_action_intents_actor ON admin_action_intents(actor_tg_id);",
        "CREATE INDEX IF NOT EXISTS ix_admin_action_intents_status ON admin_action_intents(status);",
        "CREATE INDEX IF NOT EXISTS ix_admin_action_intents_expires_at ON admin_action_intents(expires_at);",
        "CREATE INDEX IF NOT EXISTS ix_admin_action_intents_action ON admin_action_intents(action);",
        "CREATE INDEX IF NOT EXISTS ix_admin_action_intents_target ON admin_action_intents(target_type, target_id);",
    ]:
        conn.execute(text(sql))
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS admin_broadcast_recipient_plan (
              id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
              intent_id VARCHAR(36) NOT NULL,
              ordinal INTEGER NOT NULL,
              tg_id BIGINT NOT NULL,
              created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT fk_admin_broadcast_plan_intent
                FOREIGN KEY (intent_id) REFERENCES admin_action_intents(id)
                ON DELETE CASCADE,
              CONSTRAINT uq_admin_broadcast_plan_intent_ordinal
                UNIQUE (intent_id, ordinal),
              CONSTRAINT uq_admin_broadcast_plan_intent_tg_id
                UNIQUE (intent_id, tg_id),
              CONSTRAINT ck_admin_broadcast_plan_ordinal
                CHECK (ordinal >= 0 AND ordinal < 1000),
              CONSTRAINT ck_admin_broadcast_plan_tg_id CHECK (tg_id > 0)
            );
            """
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_admin_broadcast_plan_intent "
            "ON admin_broadcast_recipient_plan(intent_id);"
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS admin_broadcast_delivery_attempts (
              id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
              intent_id VARCHAR(36) NOT NULL,
              campaign_intent_id VARCHAR(36) NOT NULL,
              tg_id BIGINT NOT NULL,
              attempt_number INTEGER NOT NULL,
              status VARCHAR(16) NOT NULL,
              reason_code VARCHAR(64) NOT NULL,
              retryable BOOLEAN NOT NULL DEFAULT FALSE,
              http_status INTEGER,
              telegram_error_code INTEGER,
              retry_after_seconds INTEGER,
              message_id BIGINT,
              provider_error_hash VARCHAR(64),
              duration_ms INTEGER NOT NULL,
              started_at DATETIME NOT NULL,
              finished_at DATETIME NOT NULL,
              created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT fk_admin_broadcast_attempt_intent
                FOREIGN KEY (intent_id) REFERENCES admin_action_intents(id)
                ON DELETE CASCADE,
              CONSTRAINT uq_admin_broadcast_attempt_number
                UNIQUE (campaign_intent_id, tg_id, attempt_number),
              CONSTRAINT ck_admin_broadcast_attempt_tg_id CHECK (tg_id > 0),
              CONSTRAINT ck_admin_broadcast_attempt_number
                CHECK (attempt_number >= 1 AND attempt_number <= 20),
              CONSTRAINT ck_admin_broadcast_attempt_duration
                CHECK (duration_ms >= 0 AND duration_ms <= 3600000)
            );
            """
        )
    )
    for sql in [
        "CREATE INDEX IF NOT EXISTS ix_admin_broadcast_attempt_intent ON admin_broadcast_delivery_attempts(intent_id);",
        "CREATE INDEX IF NOT EXISTS ix_admin_broadcast_attempt_campaign ON admin_broadcast_delivery_attempts(campaign_intent_id);",
        "CREATE INDEX IF NOT EXISTS ix_admin_broadcast_attempt_result ON admin_broadcast_delivery_attempts(intent_id, status, retryable);",
        "CREATE INDEX IF NOT EXISTS ix_admin_broadcast_attempt_recipient ON admin_broadcast_delivery_attempts(campaign_intent_id, tg_id);",
    ]:
        conn.execute(text(sql))
    for sql in [
        "DROP TRIGGER IF EXISTS trg_user_nodes_guard_mapping_insert;",
        """
        CREATE TRIGGER trg_user_nodes_guard_mapping_insert
        BEFORE INSERT ON user_nodes
        WHEN NOT EXISTS (
          SELECT 1
          FROM nodes
          WHERE id = NEW.node_id
            AND COALESCE(enabled, 0) = 1
            AND COALESCE(accepting_new_clients, 0) = 1
        )
        BEGIN
          SELECT RAISE(ABORT, 'user_node_target_unavailable');
        END;
        """,
        "DROP TRIGGER IF EXISTS trg_user_nodes_guard_mapping_update;",
        """
        CREATE TRIGGER trg_user_nodes_guard_mapping_update
        BEFORE UPDATE ON user_nodes
        WHEN OLD.node_id != NEW.node_id
        AND NOT EXISTS (
          SELECT 1
          FROM nodes
          WHERE id = NEW.node_id
            AND COALESCE(enabled, 0) = 1
            AND COALESCE(accepting_new_clients, 0) = 1
        )
        BEGIN
          SELECT RAISE(ABORT, 'user_node_target_unavailable');
        END;
        """,
    ]:
        conn.execute(text(sql))


def _ensure_admin_action_intent_domain_postgres(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS admin_action_intents (
              id VARCHAR(36) NOT NULL PRIMARY KEY,
              actor_tg_id BIGINT NOT NULL,
              action VARCHAR(64) NOT NULL,
              target_type VARCHAR(32) NOT NULL,
              target_id VARCHAR(128) NOT NULL,
              risk_level VARCHAR(8) NOT NULL,
              executor_kind VARCHAR(16) NOT NULL,
              canonical_payload_json TEXT NOT NULL,
              payload_hash VARCHAR(64) NOT NULL,
              preview_snapshot_json TEXT NOT NULL,
              snapshot_hash VARCHAR(64) NOT NULL,
              confirmation_challenge_kind VARCHAR(32) NOT NULL,
              confirmation_challenge_hash VARCHAR(64) NOT NULL,
              entity_version_hash VARCHAR(64) NOT NULL,
              status VARCHAR(16) NOT NULL DEFAULT 'prepared',
              expires_at TIMESTAMPTZ NOT NULL,
              consumed_at TIMESTAMPTZ,
              client_idempotency_key VARCHAR(36),
              result_code VARCHAR(64),
              result_summary_json TEXT,
              result_hash VARCHAR(64),
              external_error_hash VARCHAR(64),
              admin_audit_id INTEGER,
              created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT uq_admin_action_intents_idempotency UNIQUE (client_idempotency_key),
              CONSTRAINT fk_admin_action_intents_audit
                FOREIGN KEY (admin_audit_id) REFERENCES admin_audit(id)
                ON DELETE RESTRICT
            );
            """
        )
    )
    for sql in [
        "CREATE INDEX IF NOT EXISTS ix_admin_action_intents_actor ON admin_action_intents(actor_tg_id);",
        "CREATE INDEX IF NOT EXISTS ix_admin_action_intents_status ON admin_action_intents(status);",
        "CREATE INDEX IF NOT EXISTS ix_admin_action_intents_expires_at ON admin_action_intents(expires_at);",
        "CREATE INDEX IF NOT EXISTS ix_admin_action_intents_action ON admin_action_intents(action);",
        "CREATE INDEX IF NOT EXISTS ix_admin_action_intents_target ON admin_action_intents(target_type, target_id);",
    ]:
        conn.execute(text(sql))
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS admin_broadcast_recipient_plan (
              id BIGSERIAL NOT NULL PRIMARY KEY,
              intent_id VARCHAR(36) NOT NULL,
              ordinal INTEGER NOT NULL,
              tg_id BIGINT NOT NULL,
              created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT fk_admin_broadcast_plan_intent
                FOREIGN KEY (intent_id) REFERENCES admin_action_intents(id)
                ON DELETE CASCADE,
              CONSTRAINT uq_admin_broadcast_plan_intent_ordinal
                UNIQUE (intent_id, ordinal),
              CONSTRAINT uq_admin_broadcast_plan_intent_tg_id
                UNIQUE (intent_id, tg_id),
              CONSTRAINT ck_admin_broadcast_plan_ordinal
                CHECK (ordinal >= 0 AND ordinal < 1000),
              CONSTRAINT ck_admin_broadcast_plan_tg_id CHECK (tg_id > 0)
            );
            """
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_admin_broadcast_plan_intent "
            "ON admin_broadcast_recipient_plan(intent_id);"
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS admin_broadcast_delivery_attempts (
              id BIGSERIAL NOT NULL PRIMARY KEY,
              intent_id VARCHAR(36) NOT NULL,
              campaign_intent_id VARCHAR(36) NOT NULL,
              tg_id BIGINT NOT NULL,
              attempt_number INTEGER NOT NULL,
              status VARCHAR(16) NOT NULL,
              reason_code VARCHAR(64) NOT NULL,
              retryable BOOLEAN NOT NULL DEFAULT FALSE,
              http_status INTEGER,
              telegram_error_code INTEGER,
              retry_after_seconds INTEGER,
              message_id BIGINT,
              provider_error_hash VARCHAR(64),
              duration_ms INTEGER NOT NULL,
              started_at TIMESTAMPTZ NOT NULL,
              finished_at TIMESTAMPTZ NOT NULL,
              created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT fk_admin_broadcast_attempt_intent
                FOREIGN KEY (intent_id) REFERENCES admin_action_intents(id)
                ON DELETE CASCADE,
              CONSTRAINT uq_admin_broadcast_attempt_number
                UNIQUE (campaign_intent_id, tg_id, attempt_number),
              CONSTRAINT ck_admin_broadcast_attempt_tg_id CHECK (tg_id > 0),
              CONSTRAINT ck_admin_broadcast_attempt_number
                CHECK (attempt_number >= 1 AND attempt_number <= 20),
              CONSTRAINT ck_admin_broadcast_attempt_duration
                CHECK (duration_ms >= 0 AND duration_ms <= 3600000)
            );
            """
        )
    )
    for sql in [
        "CREATE INDEX IF NOT EXISTS ix_admin_broadcast_attempt_intent ON admin_broadcast_delivery_attempts(intent_id);",
        "CREATE INDEX IF NOT EXISTS ix_admin_broadcast_attempt_campaign ON admin_broadcast_delivery_attempts(campaign_intent_id);",
        "CREATE INDEX IF NOT EXISTS ix_admin_broadcast_attempt_result ON admin_broadcast_delivery_attempts(intent_id, status, retryable);",
        "CREATE INDEX IF NOT EXISTS ix_admin_broadcast_attempt_recipient ON admin_broadcast_delivery_attempts(campaign_intent_id, tg_id);",
    ]:
        conn.execute(text(sql))
    conn.execute(
        text(
            """
            CREATE OR REPLACE FUNCTION pokrov_guard_user_node_mapping()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            DECLARE
              target_available BOOLEAN;
            BEGIN
              -- 1347373906 is the stable POKR namespace shared with the action core.
              IF TG_OP = 'UPDATE' THEN
                IF OLD.node_id IS NOT DISTINCT FROM NEW.node_id THEN
                  RETURN NEW;
                END IF;
                PERFORM pg_advisory_xact_lock(
                  1347373906,
                  LEAST(OLD.node_id, NEW.node_id)
                );
                PERFORM pg_advisory_xact_lock(
                  1347373906,
                  GREATEST(OLD.node_id, NEW.node_id)
                );
              ELSE
                PERFORM pg_advisory_xact_lock(1347373906, NEW.node_id);
              END IF;

              SELECT (enabled IS TRUE AND accepting_new_clients IS TRUE)
              INTO target_available
              FROM nodes
              WHERE id = NEW.node_id
              FOR UPDATE;

              IF NOT FOUND OR NOT COALESCE(target_available, FALSE) THEN
                RAISE EXCEPTION 'user_node_target_unavailable'
                  USING ERRCODE = '23514';
              END IF;
              RETURN NEW;
            END;
            $$;
            """
        )
    )
    conn.execute(
        text(
            "DROP TRIGGER IF EXISTS trg_user_nodes_guard_mapping ON user_nodes;"
        )
    )
    conn.execute(
        text(
            """
            CREATE TRIGGER trg_user_nodes_guard_mapping
            BEFORE INSERT OR UPDATE ON user_nodes
            FOR EACH ROW
            EXECUTE FUNCTION pokrov_guard_user_node_mapping();
            """
        )
    )


def _ensure_acquisition_domain_sqlite(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS acquisition_sessions (
              id VARCHAR(36) PRIMARY KEY,
              session_key_hash VARCHAR(64) NOT NULL,
              first_source VARCHAR(64) NOT NULL DEFAULT 'unknown',
              first_channel VARCHAR(32) NOT NULL DEFAULT 'site',
              first_campaign VARCHAR(64),
              first_content VARCHAR(64),
              first_ref VARCHAR(64),
              first_entry_route VARCHAR(128) NOT NULL DEFAULT '/',
              first_referrer_host VARCHAR(128),
              last_source VARCHAR(64) NOT NULL DEFAULT 'unknown',
              last_channel VARCHAR(32) NOT NULL DEFAULT 'site',
              last_campaign VARCHAR(64),
              last_content VARCHAR(64),
              last_ref VARCHAR(64),
              last_entry_route VARCHAR(128) NOT NULL DEFAULT '/',
              last_referrer_host VARCHAR(128),
              bound_tg_id BIGINT,
              bound_account_id VARCHAR(36),
              created_at DATETIME NOT NULL,
              first_touch_at DATETIME NOT NULL,
              last_touch_at DATETIME NOT NULL,
              expires_at DATETIME NOT NULL
            );
            """
        )
    )
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_acquisition_sessions_key_hash ON acquisition_sessions(session_key_hash);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_sessions_bound_tg_id ON acquisition_sessions(bound_tg_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_sessions_bound_account_id ON acquisition_sessions(bound_account_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_sessions_last_touch_at ON acquisition_sessions(last_touch_at);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_sessions_expires_at ON acquisition_sessions(expires_at);"))
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS acquisition_handoffs (
              id VARCHAR(36) PRIMARY KEY,
              token_hash VARCHAR(64) NOT NULL,
              acquisition_session_id VARCHAR(36) NOT NULL REFERENCES acquisition_sessions(id),
              purpose VARCHAR(32) NOT NULL,
              asset VARCHAR(96),
              bound_tg_id BIGINT,
              bound_account_id VARCHAR(36),
              bound_order_id VARCHAR(128),
              impression_public_id VARCHAR(36),
              click_public_id VARCHAR(36),
              created_at DATETIME NOT NULL,
              expires_at DATETIME NOT NULL,
              consumed_at DATETIME
            );
            """
        )
    )
    for column in ("impression_public_id", "click_public_id"):
        if not _sqlite_column_exists(conn, "acquisition_handoffs", column):
            conn.execute(
                text(f"ALTER TABLE acquisition_handoffs ADD COLUMN {column} VARCHAR(36);")
            )
    conn.execute(
        text(
            "UPDATE acquisition_handoffs "
            "SET impression_public_id='imp_' || substr(replace(id, '-', ''), 1, 32) "
            "WHERE impression_public_id IS NULL OR trim(impression_public_id)='';"
        )
    )
    conn.execute(
        text(
            "UPDATE acquisition_handoffs "
            "SET click_public_id='clk_' || substr(replace(id, '-', ''), 1, 32) "
            "WHERE click_public_id IS NULL OR trim(click_public_id)='';"
        )
    )
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_acquisition_handoffs_token_hash ON acquisition_handoffs(token_hash);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_handoffs_session_id ON acquisition_handoffs(acquisition_session_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_handoffs_purpose ON acquisition_handoffs(purpose);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_handoffs_bound_tg_id ON acquisition_handoffs(bound_tg_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_handoffs_bound_account_id ON acquisition_handoffs(bound_account_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_handoffs_bound_order_id ON acquisition_handoffs(bound_order_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_handoffs_expires_at ON acquisition_handoffs(expires_at);"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_acquisition_handoffs_impression_id ON acquisition_handoffs(impression_public_id);"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_acquisition_handoffs_click_id ON acquisition_handoffs(click_public_id);"))


def _ensure_acquisition_domain_postgres(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS acquisition_sessions (
              id VARCHAR(36) PRIMARY KEY,
              session_key_hash VARCHAR(64) NOT NULL,
              first_source VARCHAR(64) NOT NULL DEFAULT 'unknown',
              first_channel VARCHAR(32) NOT NULL DEFAULT 'site',
              first_campaign VARCHAR(64),
              first_content VARCHAR(64),
              first_ref VARCHAR(64),
              first_entry_route VARCHAR(128) NOT NULL DEFAULT '/',
              first_referrer_host VARCHAR(128),
              last_source VARCHAR(64) NOT NULL DEFAULT 'unknown',
              last_channel VARCHAR(32) NOT NULL DEFAULT 'site',
              last_campaign VARCHAR(64),
              last_content VARCHAR(64),
              last_ref VARCHAR(64),
              last_entry_route VARCHAR(128) NOT NULL DEFAULT '/',
              last_referrer_host VARCHAR(128),
              bound_tg_id BIGINT,
              bound_account_id VARCHAR(36),
              created_at TIMESTAMP NOT NULL,
              first_touch_at TIMESTAMP NOT NULL,
              last_touch_at TIMESTAMP NOT NULL,
              expires_at TIMESTAMP NOT NULL
            );
            """
        )
    )
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_acquisition_sessions_key_hash ON acquisition_sessions(session_key_hash);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_sessions_bound_tg_id ON acquisition_sessions(bound_tg_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_sessions_bound_account_id ON acquisition_sessions(bound_account_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_sessions_last_touch_at ON acquisition_sessions(last_touch_at);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_sessions_expires_at ON acquisition_sessions(expires_at);"))
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS acquisition_handoffs (
              id VARCHAR(36) PRIMARY KEY,
              token_hash VARCHAR(64) NOT NULL,
              acquisition_session_id VARCHAR(36) NOT NULL REFERENCES acquisition_sessions(id),
              purpose VARCHAR(32) NOT NULL,
              asset VARCHAR(96),
              bound_tg_id BIGINT,
              bound_account_id VARCHAR(36),
              bound_order_id VARCHAR(128),
              impression_public_id VARCHAR(36),
              click_public_id VARCHAR(36),
              created_at TIMESTAMP NOT NULL,
              expires_at TIMESTAMP NOT NULL,
              consumed_at TIMESTAMP
            );
            """
        )
    )
    for column in ("impression_public_id", "click_public_id"):
        _postgres_add_column_if_missing(
            conn,
            "acquisition_handoffs",
            column,
            "VARCHAR(36)",
        )
    conn.execute(
        text(
            "UPDATE acquisition_handoffs "
            "SET impression_public_id='imp_' || substring(replace(id, '-', '') from 1 for 32) "
            "WHERE impression_public_id IS NULL OR btrim(impression_public_id)='';"
        )
    )
    conn.execute(
        text(
            "UPDATE acquisition_handoffs "
            "SET click_public_id='clk_' || substring(replace(id, '-', '') from 1 for 32) "
            "WHERE click_public_id IS NULL OR btrim(click_public_id)='';"
        )
    )
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_acquisition_handoffs_token_hash ON acquisition_handoffs(token_hash);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_handoffs_session_id ON acquisition_handoffs(acquisition_session_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_handoffs_purpose ON acquisition_handoffs(purpose);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_handoffs_bound_tg_id ON acquisition_handoffs(bound_tg_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_handoffs_bound_account_id ON acquisition_handoffs(bound_account_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_handoffs_bound_order_id ON acquisition_handoffs(bound_order_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_acquisition_handoffs_expires_at ON acquisition_handoffs(expires_at);"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_acquisition_handoffs_impression_id ON acquisition_handoffs(impression_public_id);"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_acquisition_handoffs_click_id ON acquisition_handoffs(click_public_id);"))


def _ensure_emergency_catalog_domain_sqlite(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS emergency_catalog_snapshots (
              id VARCHAR(36) PRIMARY KEY,
              catalog_version VARCHAR(64) NOT NULL,
              contract_version VARCHAR(64) NOT NULL,
              source_revision VARCHAR(64) NOT NULL,
              source_digest VARCHAR(64) NOT NULL,
              status VARCHAR(24) NOT NULL DEFAULT 'staging',
              candidate_count INTEGER NOT NULL DEFAULT 0,
              healthy_count INTEGER NOT NULL DEFAULT 0,
              active_endpoint_count INTEGER NOT NULL DEFAULT 0,
              catalog_ciphertext TEXT,
              catalog_hash VARCHAR(64),
              signature_b64 VARCHAR(128),
              signing_key_id VARCHAR(64),
              rejection_code VARCHAR(64),
              parent_snapshot_id VARCHAR(36),
              rollback_of_snapshot_id VARCHAR(36),
              operator_approved BOOLEAN NOT NULL DEFAULT 0,
              issued_at DATETIME,
              expires_at DATETIME,
              activated_at DATETIME,
              superseded_at DATETIME,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS emergency_catalog_endpoints (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              snapshot_id VARCHAR(36) NOT NULL REFERENCES emergency_catalog_snapshots(id) ON DELETE CASCADE,
              stable_id VARCHAR(32) NOT NULL,
              ordinal INTEGER NOT NULL,
              transport VARCHAR(16) NOT NULL,
              endpoint_host_hash VARCHAR(64) NOT NULL,
              material_ciphertext TEXT NOT NULL,
              material_hash VARCHAR(64) NOT NULL,
              probe_state VARCHAR(24) NOT NULL DEFAULT 'pending',
              exit_country VARCHAR(2),
              latency_ms INTEGER,
              authenticated BOOLEAN NOT NULL DEFAULT 0,
              payload_ok BOOLEAN NOT NULL DEFAULT 0,
              payload_sha256 VARCHAR(64),
              verification_source VARCHAR(32),
              verified_at DATETIME,
              error_code VARCHAR(64),
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL,
              CONSTRAINT uq_emergency_catalog_endpoint_snapshot_stable UNIQUE (snapshot_id, stable_id)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS emergency_eligibility_cache (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              account_id VARCHAR(36) NOT NULL,
              install_id_hash VARCHAR(64) NOT NULL,
              country_code VARCHAR(2) NOT NULL,
              source VARCHAR(32) NOT NULL,
              observed_at DATETIME NOT NULL,
              expires_at DATETIME NOT NULL,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL,
              CONSTRAINT uq_emergency_eligibility_account_install UNIQUE (account_id, install_id_hash)
            );
            """
        )
    )
    for ddl in (
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_emergency_catalog_snapshots_catalog_version ON emergency_catalog_snapshots(catalog_version);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_snapshots_source_digest ON emergency_catalog_snapshots(source_digest);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_snapshots_status ON emergency_catalog_snapshots(status);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_snapshots_expires_at ON emergency_catalog_snapshots(expires_at);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_status_activated ON emergency_catalog_snapshots(status, activated_at);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_source_created ON emergency_catalog_snapshots(source_digest, created_at);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_endpoints_snapshot_id ON emergency_catalog_endpoints(snapshot_id);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_endpoints_stable_id ON emergency_catalog_endpoints(stable_id);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_endpoints_probe_state ON emergency_catalog_endpoints(probe_state);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_endpoints_verified_at ON emergency_catalog_endpoints(verified_at);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_endpoint_snapshot_probe ON emergency_catalog_endpoints(snapshot_id, probe_state);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_eligibility_cache_account_id ON emergency_eligibility_cache(account_id);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_eligibility_cache_expires_at ON emergency_eligibility_cache(expires_at);",
    ):
        conn.execute(text(ddl))


def _ensure_emergency_catalog_domain_postgres(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS emergency_catalog_snapshots (
              id VARCHAR(36) PRIMARY KEY,
              catalog_version VARCHAR(64) NOT NULL,
              contract_version VARCHAR(64) NOT NULL,
              source_revision VARCHAR(64) NOT NULL,
              source_digest VARCHAR(64) NOT NULL,
              status VARCHAR(24) NOT NULL DEFAULT 'staging',
              candidate_count INTEGER NOT NULL DEFAULT 0,
              healthy_count INTEGER NOT NULL DEFAULT 0,
              active_endpoint_count INTEGER NOT NULL DEFAULT 0,
              catalog_ciphertext TEXT,
              catalog_hash VARCHAR(64),
              signature_b64 VARCHAR(128),
              signing_key_id VARCHAR(64),
              rejection_code VARCHAR(64),
              parent_snapshot_id VARCHAR(36),
              rollback_of_snapshot_id VARCHAR(36),
              operator_approved BOOLEAN NOT NULL DEFAULT FALSE,
              issued_at TIMESTAMP,
              expires_at TIMESTAMP,
              activated_at TIMESTAMP,
              superseded_at TIMESTAMP,
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS emergency_catalog_endpoints (
              id SERIAL PRIMARY KEY,
              snapshot_id VARCHAR(36) NOT NULL REFERENCES emergency_catalog_snapshots(id) ON DELETE CASCADE,
              stable_id VARCHAR(32) NOT NULL,
              ordinal INTEGER NOT NULL,
              transport VARCHAR(16) NOT NULL,
              endpoint_host_hash VARCHAR(64) NOT NULL,
              material_ciphertext TEXT NOT NULL,
              material_hash VARCHAR(64) NOT NULL,
              probe_state VARCHAR(24) NOT NULL DEFAULT 'pending',
              exit_country VARCHAR(2),
              latency_ms INTEGER,
              authenticated BOOLEAN NOT NULL DEFAULT FALSE,
              payload_ok BOOLEAN NOT NULL DEFAULT FALSE,
              payload_sha256 VARCHAR(64),
              verification_source VARCHAR(32),
              verified_at TIMESTAMP,
              error_code VARCHAR(64),
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL,
              CONSTRAINT uq_emergency_catalog_endpoint_snapshot_stable UNIQUE (snapshot_id, stable_id)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS emergency_eligibility_cache (
              id SERIAL PRIMARY KEY,
              account_id VARCHAR(36) NOT NULL,
              install_id_hash VARCHAR(64) NOT NULL,
              country_code VARCHAR(2) NOT NULL,
              source VARCHAR(32) NOT NULL,
              observed_at TIMESTAMP NOT NULL,
              expires_at TIMESTAMP NOT NULL,
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL,
              CONSTRAINT uq_emergency_eligibility_account_install UNIQUE (account_id, install_id_hash)
            );
            """
        )
    )
    for ddl in (
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_emergency_catalog_snapshots_catalog_version ON emergency_catalog_snapshots(catalog_version);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_snapshots_source_digest ON emergency_catalog_snapshots(source_digest);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_snapshots_status ON emergency_catalog_snapshots(status);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_snapshots_expires_at ON emergency_catalog_snapshots(expires_at);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_status_activated ON emergency_catalog_snapshots(status, activated_at);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_source_created ON emergency_catalog_snapshots(source_digest, created_at);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_endpoints_snapshot_id ON emergency_catalog_endpoints(snapshot_id);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_endpoints_stable_id ON emergency_catalog_endpoints(stable_id);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_endpoints_probe_state ON emergency_catalog_endpoints(probe_state);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_endpoints_verified_at ON emergency_catalog_endpoints(verified_at);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_catalog_endpoint_snapshot_probe ON emergency_catalog_endpoints(snapshot_id, probe_state);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_eligibility_cache_account_id ON emergency_eligibility_cache(account_id);",
        "CREATE INDEX IF NOT EXISTS ix_emergency_eligibility_cache_expires_at ON emergency_eligibility_cache(expires_at);",
    ):
        conn.execute(text(ddl))


def _ensure_release_health_domain_sqlite(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS release_health_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              schema_version INTEGER NOT NULL DEFAULT 1,
              event_id VARCHAR(36) NOT NULL,
              occurred_at DATETIME NOT NULL,
              received_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              component VARCHAR(32) NOT NULL,
              subsystem VARCHAR(32) NOT NULL,
              stage VARCHAR(32) NOT NULL,
              event_name VARCHAR(96) NOT NULL,
              severity VARCHAR(16) NOT NULL,
              outcome VARCHAR(24) NOT NULL,
              app_version VARCHAR(64) NOT NULL,
              build_number VARCHAR(32) NOT NULL,
              channel VARCHAR(16) NOT NULL,
              candidate_label VARCHAR(64) NOT NULL,
              git_revision VARCHAR(40) NOT NULL,
              core_version VARCHAR(64),
              core_abi INTEGER,
              platform VARCHAR(16) NOT NULL,
              architecture VARCHAR(32) NOT NULL,
              error_code VARCHAR(32),
              error_origin VARCHAR(16),
              selected_app_count INTEGER
            );
            """
        )
    )
    if not _sqlite_column_exists(conn, "release_health_events", "selected_app_count"):
        conn.execute(
            text(
                "ALTER TABLE release_health_events "
                "ADD COLUMN selected_app_count INTEGER;"
            )
        )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS release_health_cohort_buckets (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              cohort_fingerprint VARCHAR(64) NOT NULL,
              window_started_at DATETIME NOT NULL,
              bucket_index INTEGER NOT NULL,
              event_count INTEGER NOT NULL DEFAULT 0,
              failure_count INTEGER NOT NULL DEFAULT 0,
              crash_event_count INTEGER NOT NULL DEFAULT 0,
              crash_failure_count INTEGER NOT NULL DEFAULT 0,
              connect_event_count INTEGER NOT NULL DEFAULT 0,
              connect_failure_count INTEGER NOT NULL DEFAULT 0,
              update_event_count INTEGER NOT NULL DEFAULT 0,
              update_failure_count INTEGER NOT NULL DEFAULT 0,
              updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT uq_release_health_cohort_window_bucket
                UNIQUE (cohort_fingerprint, window_started_at, bucket_index),
              CONSTRAINT ck_release_health_cohort_bucket_index
                CHECK (bucket_index >= 0 AND bucket_index < 4096),
              CONSTRAINT ck_release_health_cohort_event_count
                CHECK (event_count >= 0 AND event_count <= 64),
              CONSTRAINT ck_release_health_cohort_failure_count
                CHECK (failure_count >= 0 AND failure_count <= event_count),
              CONSTRAINT ck_release_health_cohort_crash_counts
                CHECK (crash_event_count >= 0 AND crash_event_count <= 32
                  AND crash_failure_count >= 0
                  AND crash_failure_count <= crash_event_count),
              CONSTRAINT ck_release_health_cohort_connect_counts
                CHECK (connect_event_count >= 0 AND connect_event_count <= 32
                  AND connect_failure_count >= 0
                  AND connect_failure_count <= connect_event_count),
              CONSTRAINT ck_release_health_cohort_update_counts
                CHECK (update_event_count >= 0 AND update_event_count <= 32
                  AND update_failure_count >= 0
                  AND update_failure_count <= update_event_count)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS release_health_ingest_counters (
              reason VARCHAR(64) PRIMARY KEY,
              count BIGINT NOT NULL DEFAULT 0,
              updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS release_known_issues (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              candidate_label VARCHAR(64) NOT NULL,
              issue_code VARCHAR(32) NOT NULL,
              app_version VARCHAR(64) NOT NULL,
              build_number VARCHAR(32),
              platform VARCHAR(16) NOT NULL,
              severity VARCHAR(16) NOT NULL,
              status VARCHAR(16) NOT NULL,
              title VARCHAR(120) NOT NULL,
              safe_summary VARCHAR(500) NOT NULL,
              error_code VARCHAR(32),
              incident_ref VARCHAR(64),
              release_ref VARCHAR(64),
              created_by_tg_id BIGINT NOT NULL,
              updated_by_tg_id BIGINT NOT NULL,
              created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
    )
    for ddl in (
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_release_health_events_event_id ON release_health_events(event_id);",
        "CREATE INDEX IF NOT EXISTS ix_release_health_events_received_at ON release_health_events(received_at);",
        "CREATE INDEX IF NOT EXISTS ix_release_health_events_build_platform ON release_health_events(app_version, build_number, platform);",
        "CREATE INDEX IF NOT EXISTS ix_release_health_events_name_outcome ON release_health_events(event_name, outcome);",
        "CREATE INDEX IF NOT EXISTS ix_release_health_events_error_code ON release_health_events(error_code);",
        "CREATE INDEX IF NOT EXISTS ix_release_health_cohort_window ON release_health_cohort_buckets(cohort_fingerprint, window_started_at);",
        "CREATE INDEX IF NOT EXISTS ix_release_health_cohort_updated_at ON release_health_cohort_buckets(updated_at);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_release_known_issue_candidate_code ON release_known_issues(candidate_label, issue_code);",
        "CREATE INDEX IF NOT EXISTS ix_release_known_issues_candidate_label ON release_known_issues(candidate_label);",
        "CREATE INDEX IF NOT EXISTS ix_release_known_issues_app_version ON release_known_issues(app_version);",
        "CREATE INDEX IF NOT EXISTS ix_release_known_issues_platform ON release_known_issues(platform);",
        "CREATE INDEX IF NOT EXISTS ix_release_known_issues_status ON release_known_issues(status);",
    ):
        conn.execute(text(ddl))


def _ensure_release_health_domain_postgres(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS release_health_events (
              id SERIAL PRIMARY KEY,
              schema_version INTEGER NOT NULL DEFAULT 1,
              event_id VARCHAR(36) NOT NULL,
              occurred_at TIMESTAMPTZ NOT NULL,
              received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
              component VARCHAR(32) NOT NULL,
              subsystem VARCHAR(32) NOT NULL,
              stage VARCHAR(32) NOT NULL,
              event_name VARCHAR(96) NOT NULL,
              severity VARCHAR(16) NOT NULL,
              outcome VARCHAR(24) NOT NULL,
              app_version VARCHAR(64) NOT NULL,
              build_number VARCHAR(32) NOT NULL,
              channel VARCHAR(16) NOT NULL,
              candidate_label VARCHAR(64) NOT NULL,
              git_revision VARCHAR(40) NOT NULL,
              core_version VARCHAR(64),
              core_abi INTEGER,
              platform VARCHAR(16) NOT NULL,
              architecture VARCHAR(32) NOT NULL,
              error_code VARCHAR(32),
              error_origin VARCHAR(16),
              selected_app_count INTEGER
            );
            """
        )
    )
    _postgres_add_column_if_missing(
        conn,
        "release_health_events",
        "selected_app_count",
        "INTEGER",
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS release_health_cohort_buckets (
              id SERIAL PRIMARY KEY,
              cohort_fingerprint VARCHAR(64) NOT NULL,
              window_started_at TIMESTAMPTZ NOT NULL,
              bucket_index INTEGER NOT NULL,
              event_count INTEGER NOT NULL DEFAULT 0,
              failure_count INTEGER NOT NULL DEFAULT 0,
              crash_event_count INTEGER NOT NULL DEFAULT 0,
              crash_failure_count INTEGER NOT NULL DEFAULT 0,
              connect_event_count INTEGER NOT NULL DEFAULT 0,
              connect_failure_count INTEGER NOT NULL DEFAULT 0,
              update_event_count INTEGER NOT NULL DEFAULT 0,
              update_failure_count INTEGER NOT NULL DEFAULT 0,
              updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT uq_release_health_cohort_window_bucket
                UNIQUE (cohort_fingerprint, window_started_at, bucket_index),
              CONSTRAINT ck_release_health_cohort_bucket_index
                CHECK (bucket_index >= 0 AND bucket_index < 4096),
              CONSTRAINT ck_release_health_cohort_event_count
                CHECK (event_count >= 0 AND event_count <= 64),
              CONSTRAINT ck_release_health_cohort_failure_count
                CHECK (failure_count >= 0 AND failure_count <= event_count),
              CONSTRAINT ck_release_health_cohort_crash_counts
                CHECK (crash_event_count >= 0 AND crash_event_count <= 32
                  AND crash_failure_count >= 0
                  AND crash_failure_count <= crash_event_count),
              CONSTRAINT ck_release_health_cohort_connect_counts
                CHECK (connect_event_count >= 0 AND connect_event_count <= 32
                  AND connect_failure_count >= 0
                  AND connect_failure_count <= connect_event_count),
              CONSTRAINT ck_release_health_cohort_update_counts
                CHECK (update_event_count >= 0 AND update_event_count <= 32
                  AND update_failure_count >= 0
                  AND update_failure_count <= update_event_count)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS release_health_ingest_counters (
              reason VARCHAR(64) PRIMARY KEY,
              count BIGINT NOT NULL DEFAULT 0,
              updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS release_known_issues (
              id SERIAL PRIMARY KEY,
              candidate_label VARCHAR(64) NOT NULL,
              issue_code VARCHAR(32) NOT NULL,
              app_version VARCHAR(64) NOT NULL,
              build_number VARCHAR(32),
              platform VARCHAR(16) NOT NULL,
              severity VARCHAR(16) NOT NULL,
              status VARCHAR(16) NOT NULL,
              title VARCHAR(120) NOT NULL,
              safe_summary VARCHAR(500) NOT NULL,
              error_code VARCHAR(32),
              incident_ref VARCHAR(64),
              release_ref VARCHAR(64),
              created_by_tg_id BIGINT NOT NULL,
              updated_by_tg_id BIGINT NOT NULL,
              created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
    )
    for ddl in (
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_release_health_events_event_id ON release_health_events(event_id);",
        "CREATE INDEX IF NOT EXISTS ix_release_health_events_received_at ON release_health_events(received_at);",
        "CREATE INDEX IF NOT EXISTS ix_release_health_events_build_platform ON release_health_events(app_version, build_number, platform);",
        "CREATE INDEX IF NOT EXISTS ix_release_health_events_name_outcome ON release_health_events(event_name, outcome);",
        "CREATE INDEX IF NOT EXISTS ix_release_health_events_error_code ON release_health_events(error_code);",
        "CREATE INDEX IF NOT EXISTS ix_release_health_cohort_window ON release_health_cohort_buckets(cohort_fingerprint, window_started_at);",
        "CREATE INDEX IF NOT EXISTS ix_release_health_cohort_updated_at ON release_health_cohort_buckets(updated_at);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_release_known_issue_candidate_code ON release_known_issues(candidate_label, issue_code);",
        "CREATE INDEX IF NOT EXISTS ix_release_known_issues_candidate_label ON release_known_issues(candidate_label);",
        "CREATE INDEX IF NOT EXISTS ix_release_known_issues_app_version ON release_known_issues(app_version);",
        "CREATE INDEX IF NOT EXISTS ix_release_known_issues_platform ON release_known_issues(platform);",
        "CREATE INDEX IF NOT EXISTS ix_release_known_issues_status ON release_known_issues(status);",
    ):
        conn.execute(text(ddl))


def _ensure_support_bundle_domain_sqlite(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS support_bundle_uploads (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              upload_id VARCHAR(36) NOT NULL,
              ticket_id INTEGER NOT NULL,
              owner_tg_id BIGINT NOT NULL,
              owner_account_id VARCHAR(36),
              owner_binding_hash VARCHAR(64) NOT NULL,
              idempotency_key VARCHAR(64) NOT NULL,
              bundle_id VARCHAR(64) NOT NULL,
              expected_size_bytes INTEGER NOT NULL,
              expected_sha256 VARCHAR(64) NOT NULL,
              content_type VARCHAR(80) NOT NULL,
              received_size_bytes INTEGER NOT NULL DEFAULT 0,
              status VARCHAR(24) NOT NULL DEFAULT 'issued',
              object_name VARCHAR(96),
              failure_code VARCHAR(64),
              diagnostic_profile VARCHAR(16),
              app_version VARCHAR(64),
              build_number VARCHAR(80),
              platform VARCHAR(16),
              architecture VARCHAR(16),
              last_phase VARCHAR(32),
              last_error_code VARCHAR(32),
              proof_outcome VARCHAR(24),
              observed_attempts INTEGER,
              retention_hold BOOLEAN NOT NULL DEFAULT 0,
              retention_hold_reason VARCHAR(64),
              retention_held_at DATETIME,
              expires_at DATETIME NOT NULL,
              completed_at DATETIME,
              validated_at DATETIME,
              created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(ticket_id) REFERENCES support_tickets(id),
              CHECK(expected_size_bytes > 0 AND expected_size_bytes <= 2621440),
              CHECK(received_size_bytes >= 0 AND received_size_bytes <= expected_size_bytes)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS support_bundle_chunks (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              upload_id INTEGER NOT NULL,
              offset_bytes INTEGER NOT NULL,
              size_bytes INTEGER NOT NULL,
              sha256 VARCHAR(64) NOT NULL,
              stored_name VARCHAR(128) NOT NULL,
              created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(upload_id) REFERENCES support_bundle_uploads(id),
              CHECK(offset_bytes >= 0),
              CHECK(size_bytes > 0 AND size_bytes <= 262144)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS support_bundle_access_audits (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              grant_id VARCHAR(36) NOT NULL,
              upload_id VARCHAR(36) NOT NULL,
              ticket_id INTEGER NOT NULL,
              actor_tg_id BIGINT NOT NULL,
              actor_role VARCHAR(16) NOT NULL,
              action VARCHAR(24) NOT NULL,
              reason_code VARCHAR(32) NOT NULL,
              access_token_hash VARCHAR(64),
              expires_at DATETIME NOT NULL,
              used_at DATETIME,
              retention_hold BOOLEAN NOT NULL DEFAULT 0,
              created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
    )
    for column, ddl in (
        ("diagnostic_profile", "VARCHAR(16)"),
        ("app_version", "VARCHAR(64)"),
        ("build_number", "VARCHAR(80)"),
        ("platform", "VARCHAR(16)"),
        ("architecture", "VARCHAR(16)"),
        ("last_phase", "VARCHAR(32)"),
        ("last_error_code", "VARCHAR(32)"),
        ("proof_outcome", "VARCHAR(24)"),
        ("observed_attempts", "INTEGER"),
        ("retention_hold", "BOOLEAN NOT NULL DEFAULT 0"),
        ("retention_hold_reason", "VARCHAR(64)"),
        ("retention_held_at", "DATETIME"),
    ):
        if not _sqlite_column_exists(conn, "support_bundle_uploads", column):
            conn.execute(
                text(f"ALTER TABLE support_bundle_uploads ADD COLUMN {column} {ddl};")
            )
    for ddl in (
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_bundle_upload_id ON support_bundle_uploads(upload_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_bundle_owner_idempotency ON support_bundle_uploads(owner_binding_hash, idempotency_key);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_bundle_ticket_bundle ON support_bundle_uploads(ticket_id, bundle_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_uploads_ticket_id ON support_bundle_uploads(ticket_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_uploads_status ON support_bundle_uploads(status);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_uploads_expires_at ON support_bundle_uploads(expires_at);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_uploads_owner_account_id ON support_bundle_uploads(owner_account_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_uploads_owner_tg_id ON support_bundle_uploads(owner_tg_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_uploads_retention_hold ON support_bundle_uploads(retention_hold);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_bundle_chunk_offset ON support_bundle_chunks(upload_id, offset_bytes);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_bundle_chunk_stored_name ON support_bundle_chunks(stored_name);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_chunks_upload_id ON support_bundle_chunks(upload_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_bundle_access_grant_id ON support_bundle_access_audits(grant_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_bundle_access_token_hash ON support_bundle_access_audits(access_token_hash);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_access_upload_id ON support_bundle_access_audits(upload_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_access_ticket_id ON support_bundle_access_audits(ticket_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_access_actor_tg_id ON support_bundle_access_audits(actor_tg_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_access_action ON support_bundle_access_audits(action);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_access_expires_at ON support_bundle_access_audits(expires_at);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_access_retention_hold ON support_bundle_access_audits(retention_hold);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_access_created_at ON support_bundle_access_audits(created_at);",
    ):
        conn.execute(text(ddl))


def _ensure_support_bundle_domain_postgres(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS support_bundle_uploads (
              id SERIAL PRIMARY KEY,
              upload_id VARCHAR(36) NOT NULL,
              ticket_id INTEGER NOT NULL REFERENCES support_tickets(id),
              owner_tg_id BIGINT NOT NULL,
              owner_account_id VARCHAR(36),
              owner_binding_hash VARCHAR(64) NOT NULL,
              idempotency_key VARCHAR(64) NOT NULL,
              bundle_id VARCHAR(64) NOT NULL,
              expected_size_bytes INTEGER NOT NULL,
              expected_sha256 VARCHAR(64) NOT NULL,
              content_type VARCHAR(80) NOT NULL,
              received_size_bytes INTEGER NOT NULL DEFAULT 0,
              status VARCHAR(24) NOT NULL DEFAULT 'issued',
              object_name VARCHAR(96),
              failure_code VARCHAR(64),
              diagnostic_profile VARCHAR(16),
              app_version VARCHAR(64),
              build_number VARCHAR(80),
              platform VARCHAR(16),
              architecture VARCHAR(16),
              last_phase VARCHAR(32),
              last_error_code VARCHAR(32),
              proof_outcome VARCHAR(24),
              observed_attempts INTEGER,
              retention_hold BOOLEAN NOT NULL DEFAULT FALSE,
              retention_hold_reason VARCHAR(64),
              retention_held_at TIMESTAMPTZ,
              expires_at TIMESTAMPTZ NOT NULL,
              completed_at TIMESTAMPTZ,
              validated_at TIMESTAMPTZ,
              created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CHECK(expected_size_bytes > 0 AND expected_size_bytes <= 2621440),
              CHECK(received_size_bytes >= 0 AND received_size_bytes <= expected_size_bytes)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS support_bundle_chunks (
              id SERIAL PRIMARY KEY,
              upload_id INTEGER NOT NULL REFERENCES support_bundle_uploads(id),
              offset_bytes INTEGER NOT NULL,
              size_bytes INTEGER NOT NULL,
              sha256 VARCHAR(64) NOT NULL,
              stored_name VARCHAR(128) NOT NULL,
              created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CHECK(offset_bytes >= 0),
              CHECK(size_bytes > 0 AND size_bytes <= 262144)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS support_bundle_access_audits (
              id SERIAL PRIMARY KEY,
              grant_id VARCHAR(36) NOT NULL,
              upload_id VARCHAR(36) NOT NULL,
              ticket_id INTEGER NOT NULL,
              actor_tg_id BIGINT NOT NULL,
              actor_role VARCHAR(16) NOT NULL,
              action VARCHAR(24) NOT NULL,
              reason_code VARCHAR(32) NOT NULL,
              access_token_hash VARCHAR(64),
              expires_at TIMESTAMPTZ NOT NULL,
              used_at TIMESTAMPTZ,
              retention_hold BOOLEAN NOT NULL DEFAULT FALSE,
              created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
    )
    for column, ddl in (
        ("diagnostic_profile", "VARCHAR(16)"),
        ("app_version", "VARCHAR(64)"),
        ("build_number", "VARCHAR(80)"),
        ("platform", "VARCHAR(16)"),
        ("architecture", "VARCHAR(16)"),
        ("last_phase", "VARCHAR(32)"),
        ("last_error_code", "VARCHAR(32)"),
        ("proof_outcome", "VARCHAR(24)"),
        ("observed_attempts", "INTEGER"),
        ("retention_hold", "BOOLEAN NOT NULL DEFAULT FALSE"),
        ("retention_hold_reason", "VARCHAR(64)"),
        ("retention_held_at", "TIMESTAMPTZ"),
    ):
        _postgres_add_column_if_missing(
            conn,
            "support_bundle_uploads",
            column,
            ddl,
        )
    for ddl in (
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_bundle_upload_id ON support_bundle_uploads(upload_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_bundle_owner_idempotency ON support_bundle_uploads(owner_binding_hash, idempotency_key);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_bundle_ticket_bundle ON support_bundle_uploads(ticket_id, bundle_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_uploads_ticket_id ON support_bundle_uploads(ticket_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_uploads_status ON support_bundle_uploads(status);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_uploads_expires_at ON support_bundle_uploads(expires_at);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_uploads_owner_account_id ON support_bundle_uploads(owner_account_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_uploads_owner_tg_id ON support_bundle_uploads(owner_tg_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_uploads_retention_hold ON support_bundle_uploads(retention_hold);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_bundle_chunk_offset ON support_bundle_chunks(upload_id, offset_bytes);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_bundle_chunk_stored_name ON support_bundle_chunks(stored_name);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_chunks_upload_id ON support_bundle_chunks(upload_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_bundle_access_grant_id ON support_bundle_access_audits(grant_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_bundle_access_token_hash ON support_bundle_access_audits(access_token_hash);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_access_upload_id ON support_bundle_access_audits(upload_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_access_ticket_id ON support_bundle_access_audits(ticket_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_access_actor_tg_id ON support_bundle_access_audits(actor_tg_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_access_action ON support_bundle_access_audits(action);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_access_expires_at ON support_bundle_access_audits(expires_at);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_access_retention_hold ON support_bundle_access_audits(retention_hold);",
        "CREATE INDEX IF NOT EXISTS ix_support_bundle_access_created_at ON support_bundle_access_audits(created_at);",
    ):
        conn.execute(text(ddl))


def _ensure_support_mode_domain_sqlite(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS support_mode_policies (
              id VARCHAR(36) PRIMARY KEY,
              policy_id VARCHAR(64) NOT NULL,
              ticket_id INTEGER NOT NULL,
              owner_tg_id BIGINT NOT NULL,
              owner_account_id VARCHAR(36),
              environment VARCHAR(32) NOT NULL,
              platform VARCHAR(16) NOT NULL,
              app_version VARCHAR(32) NOT NULL,
              build_number VARCHAR(80) NOT NULL,
              allowed_categories_json TEXT NOT NULL,
              allowed_collectors_json TEXT NOT NULL,
              maximum_bundle_bytes INTEGER NOT NULL,
              maximum_total_bytes INTEGER NOT NULL,
              maximum_bundles INTEGER NOT NULL,
              nonce VARCHAR(32) NOT NULL,
              activation_code_hash VARCHAR(64) NOT NULL,
              status VARCHAR(16) NOT NULL DEFAULT 'issued',
              created_by_tg_id BIGINT NOT NULL,
              issued_at DATETIME NOT NULL,
              expires_at DATETIME NOT NULL,
              redeemed_at DATETIME,
              created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(ticket_id) REFERENCES support_tickets(id) ON DELETE RESTRICT,
              CHECK(maximum_bundle_bytes >= 65536 AND maximum_bundle_bytes <= 2097152),
              CHECK(maximum_total_bytes >= maximum_bundle_bytes AND maximum_total_bytes <= 4194304),
              CHECK(maximum_bundles >= 1 AND maximum_bundles <= 2)
            );
            """
        )
    )
    for ddl in (
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_mode_policy_id ON support_mode_policies(policy_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_mode_activation_code_hash ON support_mode_policies(activation_code_hash);",
        "CREATE INDEX IF NOT EXISTS ix_support_mode_ticket_id ON support_mode_policies(ticket_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_mode_owner_tg_id ON support_mode_policies(owner_tg_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_mode_owner_account_id ON support_mode_policies(owner_account_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_mode_environment ON support_mode_policies(environment);",
        "CREATE INDEX IF NOT EXISTS ix_support_mode_status ON support_mode_policies(status);",
        "CREATE INDEX IF NOT EXISTS ix_support_mode_expires_at ON support_mode_policies(expires_at);",
    ):
        conn.execute(text(ddl))


def _ensure_support_mode_domain_postgres(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS support_mode_policies (
              id VARCHAR(36) PRIMARY KEY,
              policy_id VARCHAR(64) NOT NULL,
              ticket_id INTEGER NOT NULL REFERENCES support_tickets(id) ON DELETE RESTRICT,
              owner_tg_id BIGINT NOT NULL,
              owner_account_id VARCHAR(36),
              environment VARCHAR(32) NOT NULL,
              platform VARCHAR(16) NOT NULL,
              app_version VARCHAR(32) NOT NULL,
              build_number VARCHAR(80) NOT NULL,
              allowed_categories_json TEXT NOT NULL,
              allowed_collectors_json TEXT NOT NULL,
              maximum_bundle_bytes INTEGER NOT NULL,
              maximum_total_bytes INTEGER NOT NULL,
              maximum_bundles INTEGER NOT NULL,
              nonce VARCHAR(32) NOT NULL,
              activation_code_hash VARCHAR(64) NOT NULL,
              status VARCHAR(16) NOT NULL DEFAULT 'issued',
              created_by_tg_id BIGINT NOT NULL,
              issued_at TIMESTAMPTZ NOT NULL,
              expires_at TIMESTAMPTZ NOT NULL,
              redeemed_at TIMESTAMPTZ,
              created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CHECK(maximum_bundle_bytes >= 65536 AND maximum_bundle_bytes <= 2097152),
              CHECK(maximum_total_bytes >= maximum_bundle_bytes AND maximum_total_bytes <= 4194304),
              CHECK(maximum_bundles >= 1 AND maximum_bundles <= 2)
            );
            """
        )
    )
    for ddl in (
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_mode_policy_id ON support_mode_policies(policy_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_support_mode_activation_code_hash ON support_mode_policies(activation_code_hash);",
        "CREATE INDEX IF NOT EXISTS ix_support_mode_ticket_id ON support_mode_policies(ticket_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_mode_owner_tg_id ON support_mode_policies(owner_tg_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_mode_owner_account_id ON support_mode_policies(owner_account_id);",
        "CREATE INDEX IF NOT EXISTS ix_support_mode_environment ON support_mode_policies(environment);",
        "CREATE INDEX IF NOT EXISTS ix_support_mode_status ON support_mode_policies(status);",
        "CREATE INDEX IF NOT EXISTS ix_support_mode_expires_at ON support_mode_policies(expires_at);",
    ):
        conn.execute(text(ddl))


def _ensure_payment_entitlement_outbox_sqlite(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS payment_entitlement_outbox (
              id VARCHAR(36) PRIMARY KEY,
              idempotency_key VARCHAR(220) NOT NULL,
              aggregate_type VARCHAR(32) NOT NULL DEFAULT 'payment_entitlement',
              aggregate_id VARCHAR(36) NOT NULL,
              event_type VARCHAR(64) NOT NULL DEFAULT 'payment_entitlement.applied',
              schema_version INTEGER NOT NULL DEFAULT 1,
              payload_json TEXT NOT NULL,
              status VARCHAR(24) NOT NULL DEFAULT 'pending',
              attempts INTEGER NOT NULL DEFAULT 0,
              next_run_at DATETIME NOT NULL,
              claimed_at DATETIME,
              claim_token VARCHAR(64),
              last_error_code VARCHAR(64),
              terminal_reason VARCHAR(64),
              delivered_at DATETIME,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL,
              CHECK(attempts >= 0)
            );
            """
        )
    )
    for ddl in (
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_entitlement_outbox_idempotency ON payment_entitlement_outbox(idempotency_key);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_outbox_aggregate_id ON payment_entitlement_outbox(aggregate_id);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_outbox_status ON payment_entitlement_outbox(status);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_outbox_next_run_at ON payment_entitlement_outbox(next_run_at);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_outbox_claim_token ON payment_entitlement_outbox(claim_token);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_outbox_status_next_id ON payment_entitlement_outbox(status, next_run_at, id);",
    ):
        conn.execute(text(ddl))


def _ensure_payment_entitlement_outbox_postgres(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS payment_entitlement_outbox (
              id VARCHAR(36) PRIMARY KEY,
              idempotency_key VARCHAR(220) NOT NULL,
              aggregate_type VARCHAR(32) NOT NULL DEFAULT 'payment_entitlement',
              aggregate_id VARCHAR(36) NOT NULL,
              event_type VARCHAR(64) NOT NULL DEFAULT 'payment_entitlement.applied',
              schema_version INTEGER NOT NULL DEFAULT 1,
              payload_json TEXT NOT NULL,
              status VARCHAR(24) NOT NULL DEFAULT 'pending',
              attempts INTEGER NOT NULL DEFAULT 0,
              next_run_at TIMESTAMPTZ NOT NULL,
              claimed_at TIMESTAMPTZ,
              claim_token VARCHAR(64),
              last_error_code VARCHAR(64),
              terminal_reason VARCHAR(64),
              delivered_at TIMESTAMPTZ,
              created_at TIMESTAMPTZ NOT NULL,
              updated_at TIMESTAMPTZ NOT NULL,
              CHECK(attempts >= 0)
            );
            """
        )
    )
    for ddl in (
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_entitlement_outbox_idempotency ON payment_entitlement_outbox(idempotency_key);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_outbox_aggregate_id ON payment_entitlement_outbox(aggregate_id);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_outbox_status ON payment_entitlement_outbox(status);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_outbox_next_run_at ON payment_entitlement_outbox(next_run_at);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_outbox_claim_token ON payment_entitlement_outbox(claim_token);",
        "CREATE INDEX IF NOT EXISTS ix_payment_entitlement_outbox_status_next_id ON payment_entitlement_outbox(status, next_run_at, id);",
    ):
        conn.execute(text(ddl))


def _ensure_commercial_offer_domain_sqlite(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commercial_offers (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              public_id VARCHAR(36) NOT NULL UNIQUE,
              campaign_id INTEGER NOT NULL REFERENCES incentive_campaigns(id) ON DELETE CASCADE,
              plan_code VARCHAR(32) NOT NULL,
              status VARCHAR(24) NOT NULL DEFAULT 'draft',
              commercial_revision VARCHAR(32) NOT NULL,
              terms_revision VARCHAR(64) NOT NULL,
              currency VARCHAR(16) NOT NULL DEFAULT 'RUB',
              base_amount_rub INTEGER NOT NULL CHECK(base_amount_rub >= 0),
              final_amount_rub INTEGER NOT NULL CHECK(final_amount_rub >= 0),
              stackable_with_base_savings BOOLEAN NOT NULL DEFAULT 0,
              paid_cap INTEGER NOT NULL DEFAULT 0 CHECK(paid_cap >= 0),
              paid_count INTEGER NOT NULL DEFAULT 0 CHECK(paid_count >= 0),
              per_subject_paid_cap INTEGER NOT NULL DEFAULT 1 CHECK(per_subject_paid_cap > 0),
              starts_at DATETIME NOT NULL,
              ends_at DATETIME NOT NULL,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commercial_creatives (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              public_id VARCHAR(36) NOT NULL UNIQUE,
              campaign_id INTEGER NOT NULL REFERENCES incentive_campaigns(id) ON DELETE CASCADE,
              offer_id INTEGER NOT NULL REFERENCES commercial_offers(id) ON DELETE CASCADE,
              variant_code VARCHAR(32) NOT NULL,
              status VARCHAR(24) NOT NULL DEFAULT 'draft',
              channel VARCHAR(32) NOT NULL,
              content_revision VARCHAR(64) NOT NULL,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL,
              CONSTRAINT uq_commercial_creative_offer_variant UNIQUE (offer_id, variant_code)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commercial_assignments (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              public_id VARCHAR(36) NOT NULL UNIQUE,
              campaign_id INTEGER NOT NULL REFERENCES incentive_campaigns(id) ON DELETE CASCADE,
              offer_id INTEGER NOT NULL REFERENCES commercial_offers(id) ON DELETE CASCADE,
              creative_id INTEGER NOT NULL REFERENCES commercial_creatives(id) ON DELETE CASCADE,
              subject_hmac VARCHAR(64) NOT NULL,
              status VARCHAR(24) NOT NULL DEFAULT 'active',
              audience_status VARCHAR(24) NOT NULL DEFAULT 'blocked',
              audience_reason VARCHAR(64) NOT NULL DEFAULT 'not_evaluated',
              paid_count INTEGER NOT NULL DEFAULT 0 CHECK(paid_count >= 0),
              assigned_at DATETIME NOT NULL,
              expires_at DATETIME NOT NULL,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL,
              CONSTRAINT uq_commercial_assignment_campaign_offer_subject
                UNIQUE (campaign_id, offer_id, subject_hmac)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commercial_reservations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              public_id VARCHAR(36) NOT NULL UNIQUE,
              campaign_id INTEGER NOT NULL REFERENCES incentive_campaigns(id) ON DELETE CASCADE,
              offer_id INTEGER NOT NULL REFERENCES commercial_offers(id) ON DELETE CASCADE,
              creative_id INTEGER NOT NULL REFERENCES commercial_creatives(id) ON DELETE CASCADE,
              assignment_id INTEGER NOT NULL REFERENCES commercial_assignments(id) ON DELETE CASCADE,
              subject_hmac VARCHAR(64) NOT NULL,
              commercial_revision VARCHAR(32) NOT NULL,
              campaign_revision INTEGER NOT NULL,
              status VARCHAR(24) NOT NULL DEFAULT 'held',
              token_version INTEGER NOT NULL DEFAULT 2,
              token_sha256 VARCHAR(64),
              impression_public_id VARCHAR(36) NOT NULL,
              click_public_id VARCHAR(36) NOT NULL,
              base_amount_rub INTEGER NOT NULL CHECK(base_amount_rub >= 0),
              final_amount_rub INTEGER NOT NULL CHECK(final_amount_rub >= 0),
              currency VARCHAR(16) NOT NULL,
              issued_at DATETIME NOT NULL,
              hold_expires_at DATETIME NOT NULL,
              offer_ends_at DATETIME NOT NULL,
              bound_order_id VARCHAR(128),
              consumed_at DATETIME,
              released_at DATETIME,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL,
              CONSTRAINT uq_commercial_reservation_assignment UNIQUE (assignment_id)
            );
            """
        )
    )
    for column in ("impression_public_id", "click_public_id"):
        if not _sqlite_column_exists(conn, "commercial_reservations", column):
            conn.execute(
                text(
                    f"ALTER TABLE commercial_reservations ADD COLUMN {column} VARCHAR(36);"
                )
            )
    conn.execute(
        text(
            "UPDATE commercial_reservations "
            "SET impression_public_id='imp_' || substr(public_id, 5) "
            "WHERE impression_public_id IS NULL OR trim(impression_public_id)='';"
        )
    )
    conn.execute(
        text(
            "UPDATE commercial_reservations "
            "SET click_public_id='clk_' || substr(public_id, 5) "
            "WHERE click_public_id IS NULL OR trim(click_public_id)='';"
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commercial_conversions (
              id VARCHAR(36) PRIMARY KEY,
              provider VARCHAR(32) NOT NULL,
              order_id VARCHAR(128) NOT NULL,
              stage VARCHAR(32) NOT NULL,
              campaign_id INTEGER NOT NULL REFERENCES incentive_campaigns(id) ON DELETE CASCADE,
              offer_id INTEGER NOT NULL REFERENCES commercial_offers(id) ON DELETE CASCADE,
              creative_id INTEGER NOT NULL REFERENCES commercial_creatives(id) ON DELETE CASCADE,
              assignment_id INTEGER NOT NULL REFERENCES commercial_assignments(id) ON DELETE CASCADE,
              reservation_id INTEGER NOT NULL REFERENCES commercial_reservations(id) ON DELETE CASCADE,
              campaign_public_id VARCHAR(36) NOT NULL,
              offer_public_id VARCHAR(36) NOT NULL,
              creative_public_id VARCHAR(36) NOT NULL,
              variant_code VARCHAR(32) NOT NULL,
              assignment_public_id VARCHAR(36) NOT NULL,
              reservation_public_id VARCHAR(36) NOT NULL,
              impression_public_id VARCHAR(36) NOT NULL,
              click_public_id VARCHAR(36) NOT NULL,
              commercial_revision VARCHAR(32) NOT NULL,
              campaign_revision INTEGER NOT NULL,
              capacity_cost_units INTEGER NOT NULL DEFAULT 0 CHECK(capacity_cost_units >= 0),
              currency VARCHAR(16) NOT NULL DEFAULT 'RUB',
              gross_amount_rub INTEGER NOT NULL DEFAULT 0 CHECK(gross_amount_rub >= 0),
              refund_amount_rub INTEGER NOT NULL DEFAULT 0 CHECK(refund_amount_rub >= 0),
              reversal_kind VARCHAR(24),
              evidence_kind VARCHAR(40) NOT NULL,
              evidence_ref VARCHAR(64) NOT NULL,
              occurred_at DATETIME NOT NULL,
              created_at DATETIME NOT NULL,
              updated_at DATETIME NOT NULL,
              CONSTRAINT uq_commercial_conversion_order_stage UNIQUE(provider, order_id, stage),
              CHECK(stage IN ('paid', 'first_verified_connect', 'retained_d7', 'retained_d30', 'renewal', 'reversed'))
            );
            """
        )
    )
    for ddl in (
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_commercial_offers_public_id ON commercial_offers(public_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_offers_campaign_id ON commercial_offers(campaign_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_offers_plan_code ON commercial_offers(plan_code);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_offers_status ON commercial_offers(status);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_offers_ends_at ON commercial_offers(ends_at);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_offers_campaign_plan ON commercial_offers(campaign_id, plan_code);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_offers_status_ends ON commercial_offers(status, ends_at);",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_commercial_creatives_public_id ON commercial_creatives(public_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_creatives_campaign_id ON commercial_creatives(campaign_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_creatives_offer_id ON commercial_creatives(offer_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_creatives_campaign_status ON commercial_creatives(campaign_id, status);",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_commercial_assignments_public_id ON commercial_assignments(public_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_assignments_campaign_id ON commercial_assignments(campaign_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_assignments_offer_id ON commercial_assignments(offer_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_assignments_creative_id ON commercial_assignments(creative_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_assignments_subject_hmac ON commercial_assignments(subject_hmac);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_assignments_expires_at ON commercial_assignments(expires_at);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_assignments_subject_status ON commercial_assignments(subject_hmac, status);",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_commercial_reservations_public_id ON commercial_reservations(public_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_campaign_id ON commercial_reservations(campaign_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_offer_id ON commercial_reservations(offer_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_creative_id ON commercial_reservations(creative_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_assignment_id ON commercial_reservations(assignment_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_subject_hmac ON commercial_reservations(subject_hmac);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_hold_expires_at ON commercial_reservations(hold_expires_at);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_bound_order_id ON commercial_reservations(bound_order_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_commercial_reservations_bound_order_id ON commercial_reservations(bound_order_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_campaign_status ON commercial_reservations(campaign_id, status);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_offer_status ON commercial_reservations(offer_id, status);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_status_hold ON commercial_reservations(status, hold_expires_at);",
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_commercial_reservations_impression_id ON commercial_reservations(impression_public_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_commercial_reservations_click_id ON commercial_reservations(click_public_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_conversions_campaign_id ON commercial_conversions(campaign_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_conversions_offer_id ON commercial_conversions(offer_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_conversions_creative_id ON commercial_conversions(creative_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_conversions_assignment_id ON commercial_conversions(assignment_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_conversions_reservation_id ON commercial_conversions(reservation_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_conversions_occurred_at ON commercial_conversions(occurred_at);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_conversions_campaign_stage_time ON commercial_conversions(campaign_id, stage, occurred_at);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_conversions_order ON commercial_conversions(provider, order_id);",
    ):
        conn.execute(text(ddl))


def _ensure_commercial_offer_domain_postgres(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commercial_offers (
              id SERIAL PRIMARY KEY,
              public_id VARCHAR(36) NOT NULL UNIQUE,
              campaign_id INTEGER NOT NULL REFERENCES incentive_campaigns(id) ON DELETE CASCADE,
              plan_code VARCHAR(32) NOT NULL,
              status VARCHAR(24) NOT NULL DEFAULT 'draft',
              commercial_revision VARCHAR(32) NOT NULL,
              terms_revision VARCHAR(64) NOT NULL,
              currency VARCHAR(16) NOT NULL DEFAULT 'RUB',
              base_amount_rub INTEGER NOT NULL CHECK(base_amount_rub >= 0),
              final_amount_rub INTEGER NOT NULL CHECK(final_amount_rub >= 0),
              stackable_with_base_savings BOOLEAN NOT NULL DEFAULT FALSE,
              paid_cap INTEGER NOT NULL DEFAULT 0 CHECK(paid_cap >= 0),
              paid_count INTEGER NOT NULL DEFAULT 0 CHECK(paid_count >= 0),
              per_subject_paid_cap INTEGER NOT NULL DEFAULT 1 CHECK(per_subject_paid_cap > 0),
              starts_at TIMESTAMP NOT NULL,
              ends_at TIMESTAMP NOT NULL,
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commercial_creatives (
              id SERIAL PRIMARY KEY,
              public_id VARCHAR(36) NOT NULL UNIQUE,
              campaign_id INTEGER NOT NULL REFERENCES incentive_campaigns(id) ON DELETE CASCADE,
              offer_id INTEGER NOT NULL REFERENCES commercial_offers(id) ON DELETE CASCADE,
              variant_code VARCHAR(32) NOT NULL,
              status VARCHAR(24) NOT NULL DEFAULT 'draft',
              channel VARCHAR(32) NOT NULL,
              content_revision VARCHAR(64) NOT NULL,
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL,
              CONSTRAINT uq_commercial_creative_offer_variant UNIQUE (offer_id, variant_code)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commercial_assignments (
              id SERIAL PRIMARY KEY,
              public_id VARCHAR(36) NOT NULL UNIQUE,
              campaign_id INTEGER NOT NULL REFERENCES incentive_campaigns(id) ON DELETE CASCADE,
              offer_id INTEGER NOT NULL REFERENCES commercial_offers(id) ON DELETE CASCADE,
              creative_id INTEGER NOT NULL REFERENCES commercial_creatives(id) ON DELETE CASCADE,
              subject_hmac VARCHAR(64) NOT NULL,
              status VARCHAR(24) NOT NULL DEFAULT 'active',
              audience_status VARCHAR(24) NOT NULL DEFAULT 'blocked',
              audience_reason VARCHAR(64) NOT NULL DEFAULT 'not_evaluated',
              paid_count INTEGER NOT NULL DEFAULT 0 CHECK(paid_count >= 0),
              assigned_at TIMESTAMP NOT NULL,
              expires_at TIMESTAMP NOT NULL,
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL,
              CONSTRAINT uq_commercial_assignment_campaign_offer_subject
                UNIQUE (campaign_id, offer_id, subject_hmac)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commercial_reservations (
              id SERIAL PRIMARY KEY,
              public_id VARCHAR(36) NOT NULL UNIQUE,
              campaign_id INTEGER NOT NULL REFERENCES incentive_campaigns(id) ON DELETE CASCADE,
              offer_id INTEGER NOT NULL REFERENCES commercial_offers(id) ON DELETE CASCADE,
              creative_id INTEGER NOT NULL REFERENCES commercial_creatives(id) ON DELETE CASCADE,
              assignment_id INTEGER NOT NULL REFERENCES commercial_assignments(id) ON DELETE CASCADE,
              subject_hmac VARCHAR(64) NOT NULL,
              commercial_revision VARCHAR(32) NOT NULL,
              campaign_revision INTEGER NOT NULL,
              status VARCHAR(24) NOT NULL DEFAULT 'held',
              token_version INTEGER NOT NULL DEFAULT 2,
              token_sha256 VARCHAR(64),
              impression_public_id VARCHAR(36) NOT NULL,
              click_public_id VARCHAR(36) NOT NULL,
              base_amount_rub INTEGER NOT NULL CHECK(base_amount_rub >= 0),
              final_amount_rub INTEGER NOT NULL CHECK(final_amount_rub >= 0),
              currency VARCHAR(16) NOT NULL,
              issued_at TIMESTAMP NOT NULL,
              hold_expires_at TIMESTAMP NOT NULL,
              offer_ends_at TIMESTAMP NOT NULL,
              bound_order_id VARCHAR(128),
              consumed_at TIMESTAMP,
              released_at TIMESTAMP,
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL,
              CONSTRAINT uq_commercial_reservation_assignment UNIQUE (assignment_id)
            );
            """
        )
    )
    for column in ("impression_public_id", "click_public_id"):
        _postgres_add_column_if_missing(
            conn,
            "commercial_reservations",
            column,
            "VARCHAR(36)",
        )
    conn.execute(
        text(
            "UPDATE commercial_reservations "
            "SET impression_public_id='imp_' || substring(public_id from 5) "
            "WHERE impression_public_id IS NULL OR btrim(impression_public_id)='';"
        )
    )
    conn.execute(
        text(
            "UPDATE commercial_reservations "
            "SET click_public_id='clk_' || substring(public_id from 5) "
            "WHERE click_public_id IS NULL OR btrim(click_public_id)='';"
        )
    )
    conn.execute(text("ALTER TABLE commercial_reservations ALTER COLUMN impression_public_id SET NOT NULL;"))
    conn.execute(text("ALTER TABLE commercial_reservations ALTER COLUMN click_public_id SET NOT NULL;"))
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commercial_conversions (
              id VARCHAR(36) PRIMARY KEY,
              provider VARCHAR(32) NOT NULL,
              order_id VARCHAR(128) NOT NULL,
              stage VARCHAR(32) NOT NULL,
              campaign_id INTEGER NOT NULL REFERENCES incentive_campaigns(id) ON DELETE CASCADE,
              offer_id INTEGER NOT NULL REFERENCES commercial_offers(id) ON DELETE CASCADE,
              creative_id INTEGER NOT NULL REFERENCES commercial_creatives(id) ON DELETE CASCADE,
              assignment_id INTEGER NOT NULL REFERENCES commercial_assignments(id) ON DELETE CASCADE,
              reservation_id INTEGER NOT NULL REFERENCES commercial_reservations(id) ON DELETE CASCADE,
              campaign_public_id VARCHAR(36) NOT NULL,
              offer_public_id VARCHAR(36) NOT NULL,
              creative_public_id VARCHAR(36) NOT NULL,
              variant_code VARCHAR(32) NOT NULL,
              assignment_public_id VARCHAR(36) NOT NULL,
              reservation_public_id VARCHAR(36) NOT NULL,
              impression_public_id VARCHAR(36) NOT NULL,
              click_public_id VARCHAR(36) NOT NULL,
              commercial_revision VARCHAR(32) NOT NULL,
              campaign_revision INTEGER NOT NULL,
              capacity_cost_units INTEGER NOT NULL DEFAULT 0 CHECK(capacity_cost_units >= 0),
              currency VARCHAR(16) NOT NULL DEFAULT 'RUB',
              gross_amount_rub INTEGER NOT NULL DEFAULT 0 CHECK(gross_amount_rub >= 0),
              refund_amount_rub INTEGER NOT NULL DEFAULT 0 CHECK(refund_amount_rub >= 0),
              reversal_kind VARCHAR(24),
              evidence_kind VARCHAR(40) NOT NULL,
              evidence_ref VARCHAR(64) NOT NULL,
              occurred_at TIMESTAMP NOT NULL,
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL,
              CONSTRAINT uq_commercial_conversion_order_stage UNIQUE(provider, order_id, stage),
              CHECK(stage IN ('paid', 'first_verified_connect', 'retained_d7', 'retained_d30', 'renewal', 'reversed'))
            );
            """
        )
    )
    for ddl in (
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_commercial_offers_public_id ON commercial_offers(public_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_offers_campaign_id ON commercial_offers(campaign_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_offers_plan_code ON commercial_offers(plan_code);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_offers_status ON commercial_offers(status);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_offers_ends_at ON commercial_offers(ends_at);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_offers_campaign_plan ON commercial_offers(campaign_id, plan_code);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_offers_status_ends ON commercial_offers(status, ends_at);",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_commercial_creatives_public_id ON commercial_creatives(public_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_creatives_campaign_id ON commercial_creatives(campaign_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_creatives_offer_id ON commercial_creatives(offer_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_creatives_campaign_status ON commercial_creatives(campaign_id, status);",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_commercial_assignments_public_id ON commercial_assignments(public_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_assignments_campaign_id ON commercial_assignments(campaign_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_assignments_offer_id ON commercial_assignments(offer_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_assignments_creative_id ON commercial_assignments(creative_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_assignments_subject_hmac ON commercial_assignments(subject_hmac);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_assignments_expires_at ON commercial_assignments(expires_at);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_assignments_subject_status ON commercial_assignments(subject_hmac, status);",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_commercial_reservations_public_id ON commercial_reservations(public_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_campaign_id ON commercial_reservations(campaign_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_offer_id ON commercial_reservations(offer_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_creative_id ON commercial_reservations(creative_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_assignment_id ON commercial_reservations(assignment_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_subject_hmac ON commercial_reservations(subject_hmac);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_hold_expires_at ON commercial_reservations(hold_expires_at);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_bound_order_id ON commercial_reservations(bound_order_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_commercial_reservations_bound_order_id ON commercial_reservations(bound_order_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_campaign_status ON commercial_reservations(campaign_id, status);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_offer_status ON commercial_reservations(offer_id, status);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_reservations_status_hold ON commercial_reservations(status, hold_expires_at);",
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_commercial_reservations_impression_id ON commercial_reservations(impression_public_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_commercial_reservations_click_id ON commercial_reservations(click_public_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_conversions_campaign_id ON commercial_conversions(campaign_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_conversions_offer_id ON commercial_conversions(offer_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_conversions_creative_id ON commercial_conversions(creative_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_conversions_assignment_id ON commercial_conversions(assignment_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_conversions_reservation_id ON commercial_conversions(reservation_id);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_conversions_occurred_at ON commercial_conversions(occurred_at);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_conversions_campaign_stage_time ON commercial_conversions(campaign_id, stage, occurred_at);",
        "CREATE INDEX IF NOT EXISTS ix_commercial_conversions_order ON commercial_conversions(provider, order_id);",
    ):
        conn.execute(text(ddl))


def _ensure_operator_governance_sqlite(conn) -> None:
    if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_operator_roles';")).fetchone():
        for column, ddl in (
            ("grant_kind", "VARCHAR(24) NOT NULL DEFAULT 'standing'"),
            ("grant_reason", "VARCHAR(240)"),
            ("expires_at", "DATETIME"),
            ("review_status", "VARCHAR(24) NOT NULL DEFAULT 'not_required'"),
            ("reviewed_by_operator_id", "VARCHAR(36)"),
            ("reviewed_at", "DATETIME"),
            ("review_note", "VARCHAR(240)"),
        ):
            if not _sqlite_column_exists(conn, "admin_operator_roles", column):
                conn.execute(text(f"ALTER TABLE admin_operator_roles ADD COLUMN {column} {ddl};"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_admin_operator_roles_expires_at ON admin_operator_roles(expires_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_admin_operator_roles_review_status ON admin_operator_roles(review_status);"))
    if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_operator_audit';")).fetchone():
        for column, ddl in (
            ("resource_type", "VARCHAR(32)"),
            ("resource_id", "VARCHAR(128)"),
            ("command_intent_id", "VARCHAR(36)"),
            ("legacy_audit_id", "INTEGER"),
            ("details_json", "TEXT"),
        ):
            if not _sqlite_column_exists(conn, "admin_operator_audit", column):
                conn.execute(text(f"ALTER TABLE admin_operator_audit ADD COLUMN {column} {ddl};"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_admin_operator_audit_resource_type ON admin_operator_audit(resource_type);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_admin_operator_audit_resource_id ON admin_operator_audit(resource_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_admin_operator_audit_command_intent_id ON admin_operator_audit(command_intent_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_admin_operator_audit_legacy_audit_id ON admin_operator_audit(legacy_audit_id);"))


def run_migrations(engine: Engine) -> None:
    """
    Idempotent SQLite migrations for legacy DBs.
    create_all handles new tables, but won't add columns to existing ones.
    """
    dialect = (getattr(engine, "dialect", None) and engine.dialect.name or "").lower()
    if dialect == "postgresql":
        _run_postgres_migrations(engine)
        return
    if dialect and dialect != "sqlite":
        return

    _configure_sqlite_foreign_keys(engine)
    with engine.begin() as conn:
        _ensure_operator_governance_sqlite(conn)
        # users table: add columns if missing
        if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")).fetchone():
            wanted_cols = [
                ("account_id", "VARCHAR(36)"),
                ("referral_code", "VARCHAR(10)"),
                ("first_purchase_done", "BOOLEAN DEFAULT 0"),
                ("sub_token", "VARCHAR(64)"),
                ("current_plan_code", "VARCHAR(32)"),
                ("streak_months", "INTEGER DEFAULT 0"),
                ("streak_last_check", "DATETIME"),
                ("channel_bonus_claimed_at", "DATETIME"),
                ("tos_accepted", "BOOLEAN DEFAULT 0"),
                ("trial_used", "BOOLEAN DEFAULT 0"),
                ("last_wheel_spin", "DATETIME"),
                ("is_manual", "BOOLEAN DEFAULT 0"),
                ("created_by_admin", "BIGINT"),
                ("display_name", "VARCHAR(100)"),
                ("device_reset_last_at", "DATETIME"),
                ("channel_bonus_active", "BOOLEAN DEFAULT 0"),
                ("channel_bonus_expires_at", "DATETIME"),
                ("channel_bonus_revoked_at", "DATETIME"),
                ("pending_discount_pct", "INTEGER"),
                ("pending_discount_code", "VARCHAR(20)"),
                ("pending_discount_set_at", "DATETIME"),
                ("free_cycle_anchor_at", "DATETIME"),
                ("free_cycle_last_reset_at", "DATETIME"),
                ("free_cycle_next_reset_at", "DATETIME"),
                ("is_app_user", "BOOLEAN DEFAULT 0"),
                ("app_install_id", "VARCHAR(128)"),
                ("app_device_name", "VARCHAR(120)"),
                ("app_platform", "VARCHAR(32)"),
                ("app_os_version", "VARCHAR(64)"),
                ("app_version", "VARCHAR(32)"),
                ("app_locale", "VARCHAR(32)"),
                ("app_timezone", "VARCHAR(64)"),
                ("app_last_seen_at", "DATETIME"),
                ("app_last_ip", "VARCHAR(64)"),
                ("route_mode", "VARCHAR(32)"),
                ("route_selected_apps_json", "TEXT"),
                ("route_requires_elevated_privileges", "BOOLEAN"),
                ("linked_telegram_id", "BIGINT"),
                ("linked_telegram_username", "VARCHAR(100)"),
                ("linked_telegram_linked_at", "DATETIME"),
            ]
            for col, ddl in wanted_cols:
                if not _sqlite_column_exists(conn, "users", col):
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {ddl};"))

            # Legacy DBs sometimes stored timezone offsets in ISO strings (e.g. "...+00:00"),
            # which leads to offset-aware datetimes in Python and breaks naive comparisons.
            # Best-effort normalization: keep "YYYY-MM-DD HH:MM:SS" (first 19 chars).
            # This is safe for the common "+00:00" case and is idempotent.
            for col in ("created_at", "expiry_at", "last_wheel_spin", "streak_last_check"):
                if _sqlite_column_exists(conn, "users", col):
                    conn.execute(
                        text(
                            f"""
                            UPDATE users
                            SET {col} = substr({col}, 1, 19)
                            WHERE {col} IS NOT NULL
                              AND typeof({col}) = 'text'
                              AND length({col}) > 19
                              AND substr({col}, 20, 1) IN ('+', '-');
                            """
                        )
                    )

            # Normalize plan labels to keep the codebase decision-complete:
            # - FREE: free tier
            # - PAID: any paid access (monthly/quarterly/etc, gifts, legacy VIP/PRO/BASIC)
            # - MANUAL: special pinned accounts that we never touch via automation
            conn.execute(text("UPDATE users SET sub_type='MANUAL' WHERE lower(coalesce(sub_type,''))='manual';"))
            conn.execute(text("UPDATE users SET is_manual=1 WHERE upper(coalesce(sub_type,''))='MANUAL';"))
            conn.execute(text("UPDATE users SET sub_type='FREE' WHERE upper(coalesce(sub_type,'')) LIKE 'TRIAL%';"))
            conn.execute(
                text(
                    """
                    UPDATE users
                    SET sub_type='PAID'
                    WHERE upper(coalesce(sub_type,'')) IN (
                      'VIP','PRO','BASIC',
                      'PAID',
                      'MONTHLY','QUARTERLY','HALF_YEAR','YEARLY',
                      'GIFT'
                    );
                    """
                )
            )

        # Best-effort indexes
        # (SQLite IF NOT EXISTS supported for indexes)
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_reviews_tg_id ON reviews(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_reviews_featured_created ON reviews(is_featured, created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_achievements_tg_id ON achievements(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_nodes_tg_id ON user_nodes(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_nodes_node_id ON user_nodes(node_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_account_id ON users(account_id);"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_promo_usage_tg_code ON promo_usage(tg_id, promo_code);"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_app_install_id ON users(app_install_id) WHERE app_install_id IS NOT NULL;"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_linked_telegram_id ON users(linked_telegram_id) WHERE linked_telegram_id IS NOT NULL;"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS web_email_identities (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email VARCHAR(200) NOT NULL,
                  email_norm VARCHAR(200) NOT NULL,
                  password_hash VARCHAR(255) NOT NULL,
                  linked_tg_id BIGINT NOT NULL,
                  is_verified BOOLEAN NOT NULL DEFAULT 0,
                  verified_at DATETIME,
                  last_login_at DATETIME,
                  created_at DATETIME NOT NULL,
                  updated_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS web_email_tokens (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  identity_id INTEGER NOT NULL,
                  token_kind VARCHAR(32) NOT NULL,
                  token_hash VARCHAR(64) NOT NULL,
                  expires_at DATETIME NOT NULL,
                  used_at DATETIME,
                  created_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS web_cabinet_handoff_tokens (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  token_hash VARCHAR(64) NOT NULL,
                  target_path VARCHAR(512) NOT NULL,
                  expires_at DATETIME NOT NULL,
                  used_at DATETIME,
                  created_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_web_email_identities_email_norm ON web_email_identities(email_norm);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_email_identities_linked_tg_id ON web_email_identities(linked_tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_email_identities_verified ON web_email_identities(is_verified);"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_web_email_tokens_token_hash ON web_email_tokens(token_hash);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_email_tokens_identity_id ON web_email_tokens(identity_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_email_tokens_kind ON web_email_tokens(token_kind);"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_web_cabinet_handoff_tokens_token_hash ON web_cabinet_handoff_tokens(token_hash);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_cabinet_handoff_tokens_tg_id ON web_cabinet_handoff_tokens(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_cabinet_handoff_tokens_expires_at ON web_cabinet_handoff_tokens(expires_at);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS feedback_entries (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  username VARCHAR(100),
                  category VARCHAR(32) NOT NULL DEFAULT 'general',
                  text VARCHAR(1000) NOT NULL,
                  status VARCHAR(20) NOT NULL DEFAULT 'new',
                  source VARCHAR(32) NOT NULL DEFAULT 'webapp',
                  review_id INTEGER,
                  created_at DATETIME NOT NULL,
                  reviewed_at DATETIME
                );
                """
            )
        )
        if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback_entries';")).fetchone():
            wanted_cols = [
                ("username", "VARCHAR(100)"),
                ("category", "VARCHAR(32) NOT NULL DEFAULT 'general'"),
                ("status", "VARCHAR(20) NOT NULL DEFAULT 'new'"),
                ("source", "VARCHAR(32) NOT NULL DEFAULT 'webapp'"),
                ("review_id", "INTEGER"),
                ("reviewed_at", "DATETIME"),
            ]
            for col, ddl in wanted_cols:
                if not _sqlite_column_exists(conn, "feedback_entries", col):
                    conn.execute(text(f"ALTER TABLE feedback_entries ADD COLUMN {col} {ddl};"))
            conn.execute(
                text(
                    """
                    UPDATE feedback_entries
                    SET category = 'general'
                    WHERE category IS NULL OR trim(category) = '';
                    """
                )
            )
            conn.execute(
                text(
                    """
                    UPDATE feedback_entries
                    SET status = 'new'
                    WHERE status IS NULL OR trim(status) = '';
                    """
                )
            )
            conn.execute(
                text(
                    """
                    UPDATE feedback_entries
                    SET source = 'webapp'
                    WHERE source IS NULL OR trim(source) = '';
                    """
                )
            )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_feedback_entries_tg_id ON feedback_entries(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_feedback_entries_status ON feedback_entries(status);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_feedback_entries_created_at ON feedback_entries(created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_feedback_entries_review_id ON feedback_entries(review_id);"))

        # support_tickets table: backfill columns for legacy DBs if table already exists
        if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='support_tickets';")).fetchone():
            wanted_cols = [
                ("account_id", "VARCHAR(36)"),
                ("environment", "VARCHAR(32) DEFAULT 'production' NOT NULL"),
                ("status", "VARCHAR(20) DEFAULT 'open'"),
                ("subject", "VARCHAR(200)"),
                ("priority", "VARCHAR(16) DEFAULT 'normal' NOT NULL"),
                ("queue", "VARCHAR(48) DEFAULT 'general' NOT NULL"),
                ("assigned_admin_tg_id", "BIGINT"),
                ("assigned_team", "VARCHAR(48)"),
                ("waiting_on", "VARCHAR(24)"),
                ("sla_due_at", "DATETIME"),
                ("escalated_at", "DATETIME"),
                ("incident_id", "VARCHAR(36)"),
                ("attempt_ref", "VARCHAR(64)"),
                ("version", "INTEGER DEFAULT 1 NOT NULL"),
                ("updated_at", "DATETIME"),
                ("closed_at", "DATETIME"),
            ]
            for col, ddl in wanted_cols:
                if not _sqlite_column_exists(conn, "support_tickets", col):
                    conn.execute(text(f"ALTER TABLE support_tickets ADD COLUMN {col} {ddl};"))

            # Ensure missing values are normalized.
            conn.execute(
                text(
                    """
                    UPDATE support_tickets
                    SET status = 'open'
                    WHERE status IS NULL OR trim(status) = '';
                    """
                )
            )
            conn.execute(
                text(
                    """
                    UPDATE support_tickets
                    SET environment = coalesce(nullif(trim(environment), ''), 'production'),
                        priority = coalesce(nullif(trim(priority), ''), 'normal'),
                        queue = coalesce(nullif(trim(queue), ''), 'general'),
                        version = CASE WHEN version IS NULL OR version < 1 THEN 1 ELSE version END,
                        sla_due_at = coalesce(sla_due_at, datetime(created_at, '+24 hours'));
                    """
                )
            )
            conn.execute(
                text(
                    """
                    UPDATE support_tickets
                    SET updated_at = coalesce(updated_at, created_at)
                    WHERE updated_at IS NULL;
                    """
                )
            )

        # Ticket indexes (safe for both new and old DBs).
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_user_tg_id ON support_tickets(user_tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_account_id ON support_tickets(account_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_status ON support_tickets(status);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_updated_at ON support_tickets(updated_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_environment ON support_tickets(environment);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_priority ON support_tickets(priority);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_queue ON support_tickets(queue);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_sla_due_at ON support_tickets(sla_due_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_escalated_at ON support_tickets(escalated_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_incident_id ON support_tickets(incident_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_attempt_ref ON support_tickets(attempt_ref);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_ticket_messages_ticket_id ON support_ticket_messages(ticket_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_ticket_messages_sender_tg_id ON support_ticket_messages(sender_tg_id);"))

        # support_ticket_messages: media metadata for richer support intake.
        if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='support_ticket_messages';")).fetchone():
            wanted_cols = [
                ("media_type", "VARCHAR(32)"),
                ("media_file_id", "VARCHAR(256)"),
                ("media_payload", "VARCHAR(2000)"),
                ("visibility", "VARCHAR(16) DEFAULT 'public' NOT NULL"),
                ("macro_code", "VARCHAR(48)"),
            ]
            for col, ddl in wanted_cols:
                if not _sqlite_column_exists(conn, "support_ticket_messages", col):
                    conn.execute(text(f"ALTER TABLE support_ticket_messages ADD COLUMN {col} {ddl};"))
            conn.execute(
                text(
                    "UPDATE support_ticket_messages SET visibility = 'public' "
                    "WHERE visibility IS NULL OR trim(visibility) = '';"
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_ticket_messages_visibility ON support_ticket_messages(visibility);"))

        if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='support_attachments';")).fetchone():
            wanted_cols = [
                ("owner_account_id", "VARCHAR(36)"),
                ("ticket_id", "INTEGER"),
                ("message_id", "INTEGER"),
                ("attached_at", "DATETIME"),
                ("expires_at", "DATETIME"),
            ]
            for col, ddl in wanted_cols:
                if not _sqlite_column_exists(conn, "support_attachments", col):
                    conn.execute(text(f"ALTER TABLE support_attachments ADD COLUMN {col} {ddl};"))
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_support_attachments_owner_account_id "
                "ON support_attachments(owner_account_id);"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_support_attachments_ticket_id "
                "ON support_attachments(ticket_id);"
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_support_attachments_message_id "
                "ON support_attachments(message_id);"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_support_attachments_expires_at "
                "ON support_attachments(expires_at);"
            )
        )

        # nodes: runtime health fields for soft LB + fallback.
        if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='nodes';")).fetchone():
            wanted_cols = [
                ("health_score", "FLOAT DEFAULT 0"),
                ("last_health_at", "DATETIME"),
                ("is_healthy", "BOOLEAN DEFAULT 1"),
                ("accepting_new_clients", "BOOLEAN DEFAULT 1"),
                ("is_draining", "BOOLEAN DEFAULT 0"),
                ("panel_latency_ms", "INTEGER"),
                ("panel_error_rate", "FLOAT DEFAULT 0"),
                ("active_clients", "INTEGER DEFAULT 0"),
                ("provisioned_clients_count", "INTEGER DEFAULT 0"),
                ("online_connections_hint", "INTEGER DEFAULT 0"),
                ("cpu_percent", "FLOAT DEFAULT 0"),
                ("memory_used_mb", "INTEGER DEFAULT 0"),
                ("memory_total_mb", "INTEGER DEFAULT 0"),
                ("disk_used_gb", "FLOAT DEFAULT 0"),
                ("disk_total_gb", "FLOAT DEFAULT 0"),
                ("disk_free_gb", "FLOAT DEFAULT 0"),
                ("network_rx_bytes_total", "BIGINT"),
                ("network_tx_bytes_total", "BIGINT"),
                ("network_rx_mbps", "FLOAT"),
                ("network_tx_mbps", "FLOAT"),
                ("network_total_mbps", "FLOAT"),
                ("network_rx_mbps_1m", "FLOAT"),
                ("network_tx_mbps_1m", "FLOAT"),
                ("network_rx_mbps_5m", "FLOAT"),
                ("network_tx_mbps_5m", "FLOAT"),
                ("tcp_retrans_percent", "FLOAT"),
                ("packet_loss_percent", "FLOAT"),
                ("edge_reachability_ok", "BOOLEAN"),
                ("authenticated_egress_ok", "BOOLEAN"),
                ("last_authenticated_egress_at", "DATETIME"),
                ("authenticated_egress_error_kind", "VARCHAR(64)"),
                ("dataplane_ok", "BOOLEAN"),
                ("dataplane_rtt_ms", "INTEGER"),
                ("capacity_score", "FLOAT"),
                ("capacity_state", "VARCHAR(32) DEFAULT 'unknown'"),
                ("capacity_reject_reason", "VARCHAR(64)"),
                ("last_ok_at", "DATETIME"),
                ("last_probe_at", "DATETIME"),
                ("last_probe_stage", "VARCHAR(64)"),
                ("last_probe_error_kind", "VARCHAR(64)"),
                ("last_probe_error_message", "VARCHAR(500)"),
                ("hoster_family", "VARCHAR(64)"),
                ("hoster_asn", "VARCHAR(32)"),
                ("hoster_subnet", "VARCHAR(64)"),
                ("ipv4_health", "VARCHAR(32)"),
                ("ipv6_health", "VARCHAR(32)"),
                ("last_probe_classification", "VARCHAR(64)"),
                ("transport_health_json", "TEXT"),
                ("transport_profiles_json", "TEXT"),
                ("observer_push_secret", "VARCHAR(128)"),
                ("observer_last_push_at", "DATETIME"),
                ("observer_last_batch_id", "VARCHAR(128)"),
                ("observer_unmatched_count", "INTEGER DEFAULT 0"),
                ("observer_parse_error_count", "INTEGER DEFAULT 0"),
            ]
            for col, ddl in wanted_cols:
                if not _sqlite_column_exists(conn, "nodes", col):
                    conn.execute(text(f"ALTER TABLE nodes ADD COLUMN {col} {ddl};"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_enabled ON nodes(enabled);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_accepting_new_clients ON nodes(accepting_new_clients);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_is_draining ON nodes(is_draining);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_is_healthy ON nodes(is_healthy);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_health_score ON nodes(health_score);"))
            if _sqlite_column_exists(conn, "nodes", "transport_profiles_json"):
                rows = conn.execute(
                    text(
                        """
                        SELECT id, host, vless_port, reality_sni, reality_pbk, reality_sid, fingerprint, flow, inbound_id
                        FROM nodes
                        WHERE transport_profiles_json IS NULL OR trim(transport_profiles_json) = '';
                        """
                    )
                ).fetchall()
                for row in rows:
                    mapping = row._mapping
                    conn.execute(
                        text("UPDATE nodes SET transport_profiles_json = :payload WHERE id = :row_id;"),
                        {
                            "row_id": int(mapping["id"]),
                            "payload": _legacy_transport_catalog_payload(
                                host=mapping["host"],
                                vless_port=mapping["vless_port"],
                                reality_sni=mapping["reality_sni"],
                                reality_pbk=mapping["reality_pbk"],
                                reality_sid=mapping["reality_sid"],
                                fingerprint=mapping["fingerprint"],
                                flow=mapping["flow"],
                                inbound_id=mapping["inbound_id"],
                            ),
                        },
                    )

        # node_health_samples: historical runtime samples.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS node_health_samples (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  node_code VARCHAR(20) NOT NULL,
                  sampled_at DATETIME NOT NULL,
                  panel_latency_ms INTEGER,
                  panel_error_rate FLOAT DEFAULT 0,
                  active_clients INTEGER DEFAULT 0,
                  cpu_percent FLOAT DEFAULT 0,
                  memory_used_mb INTEGER DEFAULT 0,
                  memory_total_mb INTEGER DEFAULT 0,
                  disk_used_gb FLOAT DEFAULT 0,
                  disk_total_gb FLOAT DEFAULT 0,
                  disk_free_gb FLOAT DEFAULT 0,
                  network_rx_bytes_total BIGINT,
                  network_tx_bytes_total BIGINT,
                  network_rx_mbps FLOAT,
                  network_tx_mbps FLOAT,
                  network_total_mbps FLOAT,
                  total_up_bytes BIGINT DEFAULT 0,
                  total_down_bytes BIGINT DEFAULT 0,
                  total_traffic_bytes BIGINT DEFAULT 0,
                  is_healthy BOOLEAN DEFAULT 1,
                  score FLOAT DEFAULT 0,
                  source VARCHAR(64) DEFAULT 'collector',
                  probe_at DATETIME,
                  probe_stage VARCHAR(64),
                  probe_error_kind VARCHAR(64),
                  probe_error_message VARCHAR(500),
                  probe_classification VARCHAR(64),
                  ipv4_health VARCHAR(32),
                  ipv6_health VARCHAR(32),
                  transport_health_json TEXT
                );
                """
            )
        )
        if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='node_health_samples';")).fetchone():
            node_sample_cols = [
                ("cpu_percent", "FLOAT DEFAULT 0"),
                ("memory_used_mb", "INTEGER DEFAULT 0"),
                ("memory_total_mb", "INTEGER DEFAULT 0"),
                ("disk_used_gb", "FLOAT DEFAULT 0"),
                ("disk_total_gb", "FLOAT DEFAULT 0"),
                ("disk_free_gb", "FLOAT DEFAULT 0"),
                ("network_rx_bytes_total", "BIGINT"),
                ("network_tx_bytes_total", "BIGINT"),
                ("network_rx_mbps", "FLOAT"),
                ("network_tx_mbps", "FLOAT"),
                ("network_total_mbps", "FLOAT"),
                ("total_up_bytes", "BIGINT DEFAULT 0"),
                ("total_down_bytes", "BIGINT DEFAULT 0"),
                ("total_traffic_bytes", "BIGINT DEFAULT 0"),
                ("probe_at", "DATETIME"),
                ("probe_stage", "VARCHAR(64)"),
                ("probe_error_kind", "VARCHAR(64)"),
                ("probe_error_message", "VARCHAR(500)"),
                ("probe_classification", "VARCHAR(64)"),
                ("ipv4_health", "VARCHAR(32)"),
                ("ipv6_health", "VARCHAR(32)"),
                ("transport_health_json", "TEXT"),
            ]
            for col, ddl in node_sample_cols:
                if not _sqlite_column_exists(conn, "node_health_samples", col):
                    conn.execute(text(f"ALTER TABLE node_health_samples ADD COLUMN {col} {ddl};"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_node_health_samples_node_code ON node_health_samples(node_code);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_node_health_samples_sampled_at ON node_health_samples(sampled_at);"))

        _ensure_capacity_domain_sqlite(conn)
        _ensure_admin_ops_domain_sqlite(conn)
        _ensure_economy_domain_sqlite(conn)
        _ensure_payment_entitlement_claims_sqlite(conn)
        _ensure_ru_probe_domain_sqlite(conn)
        _ensure_release_evidence_domain_sqlite(conn)
        _ensure_admin_action_intent_domain_sqlite(conn)
        _ensure_emergency_catalog_domain_sqlite(conn)
        _ensure_release_health_domain_sqlite(conn)
        _ensure_support_bundle_domain_sqlite(conn)
        _ensure_support_mode_domain_sqlite(conn)
        _ensure_payment_entitlement_outbox_sqlite(conn)

        # events: minimal product analytics.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  event_name VARCHAR(64) NOT NULL,
                  schema_version INTEGER NOT NULL DEFAULT 1,
                  event_id VARCHAR(36),
                  source VARCHAR(32) DEFAULT 'unknown',
                  session_id VARCHAR(64),
                  account_id VARCHAR(36),
                  device_id VARCHAR(36),
                  platform VARCHAR(24),
                  app_version VARCHAR(32),
                  build_number VARCHAR(24),
                  surface VARCHAR(32),
                  subsystem VARCHAR(32),
                  stage VARCHAR(64),
                  result VARCHAR(24),
                  error_category VARCHAR(32),
                  error_code VARCHAR(64),
                  retryable BOOLEAN,
                  attempt_number INTEGER,
                  retry_after_seconds INTEGER,
                  duration_ms INTEGER,
                  trace_id VARCHAR(64),
                  network_class VARCHAR(24),
                  occurred_at DATETIME,
                  received_at DATETIME,
                  clock_skew_state VARCHAR(24),
                  meta_json VARCHAR(4000),
                  created_at DATETIME NOT NULL
                );
                """
            )
        )
        event_columns = [
            ("schema_version", "INTEGER NOT NULL DEFAULT 1"),
            ("event_id", "VARCHAR(36)"),
            ("account_id", "VARCHAR(36)"),
            ("device_id", "VARCHAR(36)"),
            ("platform", "VARCHAR(24)"),
            ("app_version", "VARCHAR(32)"),
            ("build_number", "VARCHAR(24)"),
            ("surface", "VARCHAR(32)"),
            ("subsystem", "VARCHAR(32)"),
            ("stage", "VARCHAR(64)"),
            ("result", "VARCHAR(24)"),
            ("error_category", "VARCHAR(32)"),
            ("error_code", "VARCHAR(64)"),
            ("retryable", "BOOLEAN"),
            ("attempt_number", "INTEGER"),
            ("retry_after_seconds", "INTEGER"),
            ("duration_ms", "INTEGER"),
            ("trace_id", "VARCHAR(64)"),
            ("network_class", "VARCHAR(24)"),
            ("occurred_at", "DATETIME"),
            ("received_at", "DATETIME"),
            ("clock_skew_state", "VARCHAR(24)"),
        ]
        for column, ddl in event_columns:
            if not _sqlite_column_exists(conn, "events", column):
                conn.execute(text(f"ALTER TABLE events ADD COLUMN {column} {ddl};"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_tg_id ON events(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_event_name ON events(event_name);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_event_created ON events(event_name, created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_tg_created ON events(tg_id, created_at);"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_events_event_id ON events(event_id) WHERE event_id IS NOT NULL;"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_account_created ON events(account_id, created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_error_created ON events(error_category, error_code, created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_received_at ON events(received_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_platform_version_created ON events(platform, app_version, created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_result_created ON events(result, created_at);"))

        # warp_events: app-facing enhanced protection lifecycle ledger.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS warp_events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  install_id VARCHAR(128),
                  event_name VARCHAR(64) NOT NULL,
                  state VARCHAR(32) NOT NULL,
                  reason_code VARCHAR(64),
                  runtime_ready BOOLEAN DEFAULT 0 NOT NULL,
                  consented BOOLEAN DEFAULT 0 NOT NULL,
                  meta_json TEXT,
                  created_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_events_tg_id ON warp_events(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_events_install_id ON warp_events(install_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_events_event_name ON warp_events(event_name);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_events_state ON warp_events(state);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_events_created_at ON warp_events(created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_events_tg_created ON warp_events(tg_id, created_at);"))

        # warp_materials: encrypted backend-owned WARP account/WireGuard material.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS warp_materials (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  install_id VARCHAR(128),
                  source VARCHAR(64) DEFAULT 'operator_provisioned' NOT NULL,
                  mode VARCHAR(32) DEFAULT 'proxy_over_warp' NOT NULL,
                  state VARCHAR(32) DEFAULT 'ready' NOT NULL,
                  wireguard_ciphertext TEXT NOT NULL,
                  account_ciphertext TEXT,
                  material_hash VARCHAR(64),
                  is_active BOOLEAN DEFAULT 1 NOT NULL,
                  provisioned_at DATETIME NOT NULL,
                  rotation_requested_at DATETIME,
                  revoked_at DATETIME,
                  updated_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_materials_tg_id ON warp_materials(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_materials_install_id ON warp_materials(install_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_materials_state ON warp_materials(state);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_materials_material_hash ON warp_materials(material_hash);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_materials_is_active ON warp_materials(is_active);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_materials_provisioned_at ON warp_materials(provisioned_at);"))
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_warp_materials_tg_install_active "
                "ON warp_materials(tg_id, install_id, is_active);"
            )
        )

        # awg2_lab_materials: encrypted, device-bound owner-lab endpoint material.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS awg2_lab_materials (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  install_id VARCHAR(128) NOT NULL,
                  contract_id VARCHAR(64) NOT NULL,
                  contract_sha256 VARCHAR(64) NOT NULL,
                  generation VARCHAR(64) NOT NULL,
                  endpoint_revision VARCHAR(64) NOT NULL,
                  server_record_id VARCHAR(64) NOT NULL,
                  node_code VARCHAR(64) NOT NULL,
                  endpoint_ciphertext TEXT NOT NULL,
                  material_hash VARCHAR(64) NOT NULL,
                  state VARCHAR(32) DEFAULT 'ready' NOT NULL,
                  is_active BOOLEAN DEFAULT 1 NOT NULL,
                  provisioned_at DATETIME NOT NULL,
                  revoked_at DATETIME,
                  updated_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_tg_id ON awg2_lab_materials(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_install_id ON awg2_lab_materials(install_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_generation ON awg2_lab_materials(generation);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_server_record_id ON awg2_lab_materials(server_record_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_node_code ON awg2_lab_materials(node_code);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_material_hash ON awg2_lab_materials(material_hash);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_state ON awg2_lab_materials(state);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_is_active ON awg2_lab_materials(is_active);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_provisioned_at ON awg2_lab_materials(provisioned_at);"))
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_tg_install_active "
                "ON awg2_lab_materials(tg_id, install_id, is_active);"
            )
        )

        # awg31_lab_materials: separate encrypted AWG 3.1 owner-lab material.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS awg31_lab_materials (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  install_id VARCHAR(128) NOT NULL,
                  contract_id VARCHAR(64) NOT NULL,
                  contract_sha256 VARCHAR(64) NOT NULL,
                  generation VARCHAR(64) NOT NULL,
                  endpoint_revision VARCHAR(64) NOT NULL,
                  server_record_id VARCHAR(64) NOT NULL,
                  node_code VARCHAR(64) NOT NULL,
                  endpoint_ciphertext TEXT NOT NULL,
                  material_hash VARCHAR(64) NOT NULL,
                  state VARCHAR(32) DEFAULT 'ready' NOT NULL,
                  is_active BOOLEAN DEFAULT 1 NOT NULL,
                  provisioned_at DATETIME NOT NULL,
                  revoked_at DATETIME,
                  updated_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_tg_id ON awg31_lab_materials(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_install_id ON awg31_lab_materials(install_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_generation ON awg31_lab_materials(generation);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_server_record_id ON awg31_lab_materials(server_record_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_node_code ON awg31_lab_materials(node_code);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_material_hash ON awg31_lab_materials(material_hash);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_state ON awg31_lab_materials(state);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_is_active ON awg31_lab_materials(is_active);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_provisioned_at ON awg31_lab_materials(provisioned_at);"))
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_tg_install_active "
                "ON awg31_lab_materials(tg_id, install_id, is_active);"
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS funnel_events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id VARCHAR(96) NOT NULL,
                  tg_id BIGINT,
                  channel VARCHAR(32) NOT NULL DEFAULT 'site',
                  event_name VARCHAR(64) NOT NULL,
                  stage VARCHAR(64) NOT NULL,
                  source VARCHAR(64) NOT NULL DEFAULT 'unknown',
                  path VARCHAR(512),
                  referrer VARCHAR(600),
                  campaign VARCHAR(64),
                  meta_json VARCHAR(4000),
                  created_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_funnel_events_session_id ON funnel_events(session_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_funnel_events_tg_id ON funnel_events(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_funnel_events_channel ON funnel_events(channel);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_funnel_events_event_name ON funnel_events(event_name);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_funnel_events_stage ON funnel_events(stage);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_funnel_events_source ON funnel_events(source);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_funnel_events_created_at ON funnel_events(created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_funnel_events_stage_created ON funnel_events(stage, created_at);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS observer_batches (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  node_id INTEGER NOT NULL,
                  batch_id VARCHAR(128) NOT NULL,
                  cursor_json TEXT,
                  observation_count INTEGER DEFAULT 0,
                  accepted_count INTEGER DEFAULT 0,
                  deduped_count INTEGER DEFAULT 0,
                  unmatched_count INTEGER DEFAULT 0,
                  parse_error_count INTEGER DEFAULT 0,
                  updated_tg_ids_json TEXT,
                  created_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS observer_daily_observations (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  node_id INTEGER NOT NULL,
                  source_ip_raw VARCHAR(64) NOT NULL,
                  score_ip_key VARCHAR(64) NOT NULL,
                  day_bucket DATE NOT NULL,
                  first_seen_at DATETIME NOT NULL,
                  last_seen_at DATETIME NOT NULL,
                  hit_count INTEGER DEFAULT 0,
                  identity_source VARCHAR(32) NOT NULL,
                  counts_for_suspicion BOOLEAN DEFAULT 1
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS observer_window_observations (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  node_id INTEGER NOT NULL,
                  source_ip_raw VARCHAR(64) NOT NULL,
                  score_ip_key VARCHAR(64) NOT NULL,
                  window_bucket_at DATETIME NOT NULL,
                  first_seen_at DATETIME NOT NULL,
                  last_seen_at DATETIME NOT NULL,
                  hit_count INTEGER DEFAULT 0,
                  counts_for_suspicion BOOLEAN DEFAULT 1
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS observer_user_state (
                  tg_id BIGINT PRIMARY KEY,
                  state VARCHAR(20) NOT NULL DEFAULT 'ok',
                  reasons_json TEXT,
                  observed_ip_count_24h INTEGER DEFAULT 0,
                  observed_ip_count_7d INTEGER DEFAULT 0,
                  observed_ip_count_30d INTEGER DEFAULT 0,
                  observed_node_count_24h INTEGER DEFAULT 0,
                  observed_node_count_7d INTEGER DEFAULT 0,
                  observed_node_count_30d INTEGER DEFAULT 0,
                  overlap_count_24h INTEGER DEFAULT 0,
                  last_observed_at DATETIME,
                  updated_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_observer_batches_node_batch "
                "ON observer_batches(node_id, batch_id);"
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_observer_daily_tg_node_ip_day "
                "ON observer_daily_observations(tg_id, node_id, source_ip_raw, day_bucket);"
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observer_daily_tg_id ON observer_daily_observations(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observer_daily_node_id ON observer_daily_observations(node_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observer_daily_score_ip_key ON observer_daily_observations(score_ip_key);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observer_daily_day_bucket ON observer_daily_observations(day_bucket);"))
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_observer_window_tg_node_score_bucket "
                "ON observer_window_observations(tg_id, node_id, score_ip_key, window_bucket_at);"
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observer_window_tg_id ON observer_window_observations(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observer_window_node_id ON observer_window_observations(node_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observer_window_score_ip_key ON observer_window_observations(score_ip_key);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observer_window_bucket ON observer_window_observations(window_bucket_at);"))

        # offers: one-time offers and retention prompts.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS offers (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  offer_type VARCHAR(32) NOT NULL,
                  plan_code VARCHAR(32) NOT NULL,
                  price_stars INTEGER DEFAULT 0,
                  status VARCHAR(20) DEFAULT 'active',
                  trigger_reason VARCHAR(64),
                  expires_at DATETIME,
                  accepted_at DATETIME,
                  created_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_offers_tg_id ON offers(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_offers_tg_status_exp ON offers(tg_id, status, expires_at);"))

        # pay attempts: purchase funnels + abandoned cart.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS pay_attempts (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  source VARCHAR(32) DEFAULT 'bot',
                  plan_code VARCHAR(32) NOT NULL,
                  amount_stars INTEGER DEFAULT 0,
                  currency VARCHAR(12) DEFAULT 'XTR',
                  status VARCHAR(20) DEFAULT 'started',
                  invoice_payload VARCHAR(255),
                  offer_id INTEGER,
                  acquisition_session_id VARCHAR(36),
                  started_at DATETIME NOT NULL,
                  updated_at DATETIME NOT NULL,
                  paid_at DATETIME,
                  abandoned_notified_at DATETIME
                );
                """
            )
        )
        if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='pay_attempts';")).fetchone():
            if not _sqlite_column_exists(conn, "pay_attempts", "acquisition_session_id"):
                conn.execute(text("ALTER TABLE pay_attempts ADD COLUMN acquisition_session_id VARCHAR(36);"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_pay_attempts_invoice_payload ON pay_attempts(invoice_payload);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pay_attempts_tg_status_started ON pay_attempts(tg_id, status, started_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pay_attempts_acquisition_session_id ON pay_attempts(acquisition_session_id);"))

        # external provider orders/events: callback idempotency and audit trail.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS external_orders (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  order_id VARCHAR(128) NOT NULL,
                  tg_id BIGINT,
                  provider VARCHAR(32) NOT NULL,
                  plan_code VARCHAR(32),
                  source VARCHAR(32),
                  campaign VARCHAR(64),
                  acquisition_session_id VARCHAR(36),
                  promo_code VARCHAR(32),
                  meta_json TEXT,
                  amount FLOAT DEFAULT 0,
                  currency VARCHAR(16) DEFAULT 'RUB',
                  status VARCHAR(24) DEFAULT 'created',
                  created_at DATETIME NOT NULL,
                  paid_at DATETIME
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_orders_order_id ON external_orders(order_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_orders_tg_id ON external_orders(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_orders_provider ON external_orders(provider);"))
        _ensure_external_order_attention_index(conn)
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_external_orders_provider_order "
                "ON external_orders(provider, order_id);"
            )
        )
        if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='external_orders';")).fetchone():
            wanted_external_cols = [
                ("source", "VARCHAR(32)"),
                ("campaign", "VARCHAR(64)"),
                ("acquisition_session_id", "VARCHAR(36)"),
                ("promo_code", "VARCHAR(32)"),
                ("meta_json", "TEXT"),
            ]
            for col, ddl in wanted_external_cols:
                if not _sqlite_column_exists(conn, "external_orders", col):
                    conn.execute(text(f"ALTER TABLE external_orders ADD COLUMN {col} {ddl};"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_orders_acquisition_session_id ON external_orders(acquisition_session_id);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS external_payment_events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  provider VARCHAR(32) NOT NULL,
                  event_type VARCHAR(24) NOT NULL,
                  external_id VARCHAR(128) NOT NULL,
                  order_id VARCHAR(128),
                  payload_json TEXT NOT NULL,
                  signature_ok BOOLEAN DEFAULT 0,
                  processed_ok BOOLEAN DEFAULT 0,
                  created_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_payment_events_provider ON external_payment_events(provider);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_payment_events_event_type ON external_payment_events(event_type);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_payment_events_external_id ON external_payment_events(external_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_payment_events_order_id ON external_payment_events(order_id);"))
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_external_payment_events_provider_type_extid "
                "ON external_payment_events(provider, event_type, external_id);"
            )
        )

        # points ledger: referral points and spends.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS points_ledger (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  delta_points INTEGER NOT NULL,
                  reason VARCHAR(64) NOT NULL,
                  ref_tg_id BIGINT,
                  pay_attempt_id INTEGER,
                  expires_at DATETIME,
                  created_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_points_ledger_tg_id ON points_ledger(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_points_ledger_tg_exp_created ON points_ledger(tg_id, expires_at, created_at);"))

        # campaign sends: dedupe for periodic campaigns.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS campaign_sends (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  campaign_key VARCHAR(64) NOT NULL,
                  sent_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_campaign_sends_tg_id ON campaign_sends(tg_id);"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_campaign_sends_tg_campaign ON campaign_sends(tg_id, campaign_key);"))

        # family slots: additive slot packs with expiry.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS family_slots (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  slots INTEGER NOT NULL DEFAULT 1,
                  expires_at DATETIME,
                  created_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_family_slots_tg_id ON family_slots(tg_id);"))

        # plan catalog: DB-backed pricing and limits with code fallback.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS plan_catalog (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  code VARCHAR(32) NOT NULL,
                  label VARCHAR(120) NOT NULL,
                  amount_rub INTEGER DEFAULT 0,
                  amount_stars INTEGER DEFAULT 0,
                  days INTEGER DEFAULT 30,
                  device_limit INTEGER DEFAULT 1,
                  node_policy VARCHAR(32),
                  badge VARCHAR(32),
                  is_active BOOLEAN DEFAULT 1,
                  sort_order INTEGER DEFAULT 100,
                  created_at DATETIME NOT NULL,
                  updated_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_plan_catalog_code ON plan_catalog(code);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_plan_catalog_active_sort ON plan_catalog(is_active, sort_order);"))

        # live updates: admin-managed cards for landing page.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS live_updates (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title VARCHAR(160) NOT NULL,
                  summary VARCHAR(600) NOT NULL,
                  link VARCHAR(600) NOT NULL,
                  published_at DATETIME,
                  is_active BOOLEAN DEFAULT 1,
                  sort_order INTEGER DEFAULT 100,
                  created_at DATETIME NOT NULL,
                  updated_at DATETIME NOT NULL
                );
                """
            )
        )
        if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='live_updates';")).fetchone():
            live_updates_cols = [
                ("channel_username", "VARCHAR(64)"),
                ("post_id", "INTEGER"),
            ]
            for col, ddl in live_updates_cols:
                if not _sqlite_column_exists(conn, "live_updates", col):
                    conn.execute(text(f"ALTER TABLE live_updates ADD COLUMN {col} {ddl};"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_live_updates_active_sort ON live_updates(is_active, sort_order);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_live_updates_channel_post ON live_updates(channel_username, post_id);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS news_draft_runs (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  run_id VARCHAR(64) NOT NULL,
                  status VARCHAR(24) NOT NULL,
                  sources_total INTEGER DEFAULT 0 NOT NULL,
                  sources_succeeded INTEGER DEFAULT 0 NOT NULL,
                  sources_failed INTEGER DEFAULT 0 NOT NULL,
                  candidates_seen INTEGER DEFAULT 0 NOT NULL,
                  drafts_created INTEGER DEFAULT 0 NOT NULL,
                  duplicates_skipped INTEGER DEFAULT 0 NOT NULL,
                  duration_ms INTEGER,
                  failure_code VARCHAR(64),
                  started_at DATETIME NOT NULL,
                  finished_at DATETIME
                );
                """
            )
        )
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_news_draft_runs_run_id ON news_draft_runs(run_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_draft_runs_started ON news_draft_runs(started_at);"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS news_drafts (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  source_name VARCHAR(64) NOT NULL,
                  source_url VARCHAR(600) NOT NULL,
                  source_title VARCHAR(300) NOT NULL,
                  source_item_sha256 VARCHAR(64) NOT NULL,
                  fetch_run_id VARCHAR(64) NOT NULL,
                  source_published_at DATETIME,
                  status VARCHAR(24) DEFAULT 'pending' NOT NULL,
                  reviewed_by_tg_id BIGINT,
                  reviewed_at DATETIME,
                  live_update_id INTEGER,
                  discovered_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_news_drafts_item_hash ON news_drafts(source_item_sha256);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_drafts_status_discovered ON news_drafts(status, discovered_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_drafts_fetch_run ON news_drafts(fetch_run_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_drafts_live_update ON news_drafts(live_update_id);"))

        # deep links: admin-managed start payloads.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS start_links (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  code VARCHAR(64) NOT NULL,
                  description VARCHAR(240),
                  target_action VARCHAR(64),
                  is_active BOOLEAN DEFAULT 1,
                  created_at DATETIME NOT NULL,
                  updated_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_start_links_code ON start_links(code);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_start_links_is_active ON start_links(is_active);"))

        # Generic app settings storage (JSON payload as text).
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                  "key" VARCHAR(64) PRIMARY KEY,
                  value_json TEXT,
                  updated_at DATETIME NOT NULL
                );
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS web_email_identities (
                  id SERIAL PRIMARY KEY,
                  email VARCHAR(200) NOT NULL,
                  email_norm VARCHAR(200) NOT NULL,
                  password_hash VARCHAR(255) NOT NULL,
                  linked_tg_id BIGINT NOT NULL,
                  is_verified BOOLEAN DEFAULT FALSE,
                  verified_at TIMESTAMP,
                  last_login_at TIMESTAMP,
                  created_at TIMESTAMP NOT NULL,
                  updated_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS web_email_tokens (
                  id SERIAL PRIMARY KEY,
                  identity_id INTEGER NOT NULL,
                  token_kind VARCHAR(32) NOT NULL,
                  token_hash VARCHAR(64) NOT NULL,
                  expires_at TIMESTAMP NOT NULL,
                  used_at TIMESTAMP,
                  created_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS web_cabinet_handoff_tokens (
                  id SERIAL PRIMARY KEY,
                  tg_id BIGINT NOT NULL,
                  token_hash VARCHAR(64) NOT NULL,
                  target_path VARCHAR(512) NOT NULL,
                  expires_at TIMESTAMP NOT NULL,
                  used_at TIMESTAMP,
                  created_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_web_email_identities_email_norm ON web_email_identities(email_norm);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_email_identities_linked_tg_id ON web_email_identities(linked_tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_email_identities_verified ON web_email_identities(is_verified);"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_web_email_tokens_token_hash ON web_email_tokens(token_hash);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_email_tokens_identity_id ON web_email_tokens(identity_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_email_tokens_kind ON web_email_tokens(token_kind);"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_web_cabinet_handoff_tokens_token_hash ON web_cabinet_handoff_tokens(token_hash);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_cabinet_handoff_tokens_tg_id ON web_cabinet_handoff_tokens(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_cabinet_handoff_tokens_expires_at ON web_cabinet_handoff_tokens(expires_at);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS key_action_history (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  node_code VARCHAR(32),
                  action VARCHAR(64) NOT NULL,
                  actor_tg_id BIGINT,
                  source VARCHAR(32) DEFAULT 'admin',
                  meta TEXT,
                  created_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_key_action_history_tg_id ON key_action_history(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_key_action_history_node_code ON key_action_history(node_code);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_key_action_history_created_at ON key_action_history(created_at);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS user_key_policy (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  node_code VARCHAR(32) NOT NULL,
                  burst_mbps INTEGER,
                  soft_cap_gb INTEGER,
                  hard_cap_gb INTEGER,
                  notify_soft BOOLEAN DEFAULT 1,
                  notify_hard BOOLEAN DEFAULT 1,
                  auto_disable_on_hard BOOLEAN DEFAULT 1,
                  updated_by BIGINT,
                  updated_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_user_key_policy_tg_node ON user_key_policy(tg_id, node_code);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_key_policy_tg_id ON user_key_policy(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_key_policy_node_code ON user_key_policy(node_code);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS referral_bonus_queue (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  referrer_tg_id BIGINT NOT NULL,
                  referred_tg_id BIGINT NOT NULL,
                  order_id VARCHAR(128) NOT NULL,
                  queued_at DATETIME NOT NULL,
                  ready_at DATETIME NOT NULL,
                  status VARCHAR(24) DEFAULT 'pending',
                  processed_at DATETIME,
                  meta TEXT
                );
                """
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_referral_bonus_queue_order_pair "
                "ON referral_bonus_queue(order_id, referrer_tg_id, referred_tg_id);"
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_referral_bonus_queue_ready_at ON referral_bonus_queue(ready_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_referral_bonus_queue_status ON referral_bonus_queue(status);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS incentive_campaigns (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  public_id VARCHAR(36),
                  name VARCHAR(120) NOT NULL,
                  campaign_type VARCHAR(16) NOT NULL,
                  target_value VARCHAR(64) NOT NULL,
                  objective VARCHAR(32) NOT NULL DEFAULT 'retention',
                  lifecycle_status VARCHAR(24) NOT NULL DEFAULT 'draft',
                  revision INTEGER NOT NULL DEFAULT 1,
                  commercial_revision VARCHAR(32),
                  legal_profile_status VARCHAR(24) NOT NULL DEFAULT 'missing',
                  channels_json TEXT,
                  seller_profile_id VARCHAR(64),
                  terms_revision VARCHAR(64),
                  paid_cap INTEGER NOT NULL DEFAULT 0,
                  paid_conversions_count INTEGER NOT NULL DEFAULT 0,
                  capacity_guard_enabled BOOLEAN NOT NULL DEFAULT 1,
                  capacity_band VARCHAR(16) NOT NULL DEFAULT 'unknown',
                  state_reason VARCHAR(64) NOT NULL DEFAULT 'legacy_unclassified',
                  last_policy_evaluated_at DATETIME,
                  killed_at DATETIME,
                  segment VARCHAR(32) DEFAULT 'all_active',
                  starts_at DATETIME,
                  ends_at DATETIME,
                  max_activations INTEGER DEFAULT -1,
                  activations_count INTEGER DEFAULT 0,
                  auto_disable BOOLEAN DEFAULT 1,
                  is_active BOOLEAN DEFAULT 0,
                  created_by BIGINT,
                  metadata_json TEXT,
                  created_at DATETIME NOT NULL,
                  updated_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_incentive_campaigns_type_target ON incentive_campaigns(campaign_type, target_value);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_incentive_campaigns_is_active ON incentive_campaigns(is_active);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_incentive_campaigns_ends_at ON incentive_campaigns(ends_at);"))
        for column, ddl in [
            ("public_id", "VARCHAR(36)"),
            ("objective", "VARCHAR(32) NOT NULL DEFAULT 'retention'"),
            ("lifecycle_status", "VARCHAR(24) NOT NULL DEFAULT 'draft'"),
            ("revision", "INTEGER NOT NULL DEFAULT 1"),
            ("commercial_revision", "VARCHAR(32)"),
            ("legal_profile_status", "VARCHAR(24) NOT NULL DEFAULT 'missing'"),
            ("channels_json", "TEXT"),
            ("seller_profile_id", "VARCHAR(64)"),
            ("terms_revision", "VARCHAR(64)"),
            ("paid_cap", "INTEGER NOT NULL DEFAULT 0"),
            ("paid_conversions_count", "INTEGER NOT NULL DEFAULT 0"),
            ("capacity_guard_enabled", "BOOLEAN NOT NULL DEFAULT 1"),
            ("capacity_band", "VARCHAR(16) NOT NULL DEFAULT 'unknown'"),
            ("state_reason", "VARCHAR(64) NOT NULL DEFAULT 'legacy_unclassified'"),
            ("last_policy_evaluated_at", "DATETIME"),
            ("killed_at", "DATETIME"),
        ]:
            if not _sqlite_column_exists(conn, "incentive_campaigns", column):
                conn.execute(text(f"ALTER TABLE incentive_campaigns ADD COLUMN {column} {ddl};"))
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_incentive_campaigns_public_id "
                "ON incentive_campaigns(public_id);"
            )
        )
        conn.execute(
            text(
                "UPDATE incentive_campaigns SET is_active=0, lifecycle_status='draft', "
                "state_reason='legacy_unclassified' WHERE public_id IS NULL AND is_active=1;"
            )
        )
        _ensure_commercial_offer_domain_sqlite(conn)

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS reward_claims (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  reward_key VARCHAR(64) NOT NULL,
                  meta TEXT,
                  claimed_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_reward_claim_tg_key ON reward_claims(tg_id, reward_key);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_reward_claims_tg_id ON reward_claims(tg_id);"))

        # SQLite does not enforce VARCHAR length, so legacy gift card code storage
        # already accepts the newer POKROV-XXXX-XXXX format without table rebuild.

        # Seed default retention templates for admin editing (idempotent).
        _ensure_acquisition_domain_sqlite(conn)
        _ensure_free_profile_schema_sqlite(conn)
        _ensure_reward_schema_sqlite(conn)
        _seed_retention_templates(conn, dialect="sqlite")
        _seed_plan_catalog(conn, dialect="sqlite")


def _run_postgres_migrations(engine: Engine) -> None:
    """
    PostgreSQL-safe idempotent migrations.
    `create_all()` already creates tables; here we only ensure additive columns/indexes.
    """
    with engine.begin() as conn:
        conn.execute(
            text(
                f"SELECT pg_advisory_xact_lock(hashtext('{POSTGRES_SCHEMA_BOOTSTRAP_LOCK}'));"
            )
        )
        code_limit = _postgres_varchar_limit(conn, "gift_cards", "code")
        if code_limit is not None and code_limit < 32:
            conn.execute(text("ALTER TABLE gift_cards ALTER COLUMN code TYPE VARCHAR(32);"))
        for column, ddl in (
            ("grant_kind", "VARCHAR(24) NOT NULL DEFAULT 'standing'"),
            ("grant_reason", "VARCHAR(240)"),
            ("expires_at", "TIMESTAMP"),
            ("review_status", "VARCHAR(24) NOT NULL DEFAULT 'not_required'"),
            ("reviewed_by_operator_id", "VARCHAR(36)"),
            ("reviewed_at", "TIMESTAMP"),
            ("review_note", "VARCHAR(240)"),
        ):
            _postgres_add_column_if_missing(conn, "admin_operator_roles", column, ddl)
        for column, ddl in (
            ("resource_type", "VARCHAR(32)"),
            ("resource_id", "VARCHAR(128)"),
            ("command_intent_id", "VARCHAR(36)"),
            ("legacy_audit_id", "INTEGER"),
            ("details_json", "TEXT"),
        ):
            _postgres_add_column_if_missing(conn, "admin_operator_audit", column, ddl)
        for ddl in (
            "CREATE INDEX IF NOT EXISTS ix_admin_operator_roles_expires_at ON admin_operator_roles(expires_at);",
            "CREATE INDEX IF NOT EXISTS ix_admin_operator_roles_review_status ON admin_operator_roles(review_status);",
            "CREATE INDEX IF NOT EXISTS ix_admin_operator_audit_resource_type ON admin_operator_audit(resource_type);",
            "CREATE INDEX IF NOT EXISTS ix_admin_operator_audit_resource_id ON admin_operator_audit(resource_id);",
            "CREATE INDEX IF NOT EXISTS ix_admin_operator_audit_command_intent_id ON admin_operator_audit(command_intent_id);",
            "CREATE INDEX IF NOT EXISTS ix_admin_operator_audit_legacy_audit_id ON admin_operator_audit(legacy_audit_id);",
        ):
            conn.execute(text(ddl))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_reviews_featured_created ON reviews(is_featured, created_at);"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS feedback_entries (
                  id SERIAL PRIMARY KEY,
                  tg_id BIGINT NOT NULL,
                  username VARCHAR(100),
                  category VARCHAR(32) NOT NULL DEFAULT 'general',
                  text VARCHAR(1000) NOT NULL,
                  status VARCHAR(20) NOT NULL DEFAULT 'new',
                  source VARCHAR(32) NOT NULL DEFAULT 'webapp',
                  review_id INTEGER,
                  created_at TIMESTAMP NOT NULL,
                  reviewed_at TIMESTAMP
                );
                """
            )
        )
        _postgres_add_column_if_missing(conn, "feedback_entries", "username", "VARCHAR(100)")
        _postgres_add_column_if_missing(conn, "feedback_entries", "category", "VARCHAR(32) DEFAULT 'general'")
        _postgres_add_column_if_missing(conn, "feedback_entries", "status", "VARCHAR(20) DEFAULT 'new'")
        _postgres_add_column_if_missing(conn, "feedback_entries", "source", "VARCHAR(32) DEFAULT 'webapp'")
        _postgres_add_column_if_missing(conn, "feedback_entries", "review_id", "INTEGER")
        _postgres_add_column_if_missing(conn, "feedback_entries", "reviewed_at", "TIMESTAMP")
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_feedback_entries_tg_id ON feedback_entries(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_feedback_entries_status ON feedback_entries(status);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_feedback_entries_created_at ON feedback_entries(created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_feedback_entries_review_id ON feedback_entries(review_id);"))
        _postgres_add_column_if_missing(conn, "support_tickets", "account_id", "VARCHAR(36)")
        for column, ddl in (
            ("environment", "VARCHAR(32) DEFAULT 'production' NOT NULL"),
            ("priority", "VARCHAR(16) DEFAULT 'normal' NOT NULL"),
            ("queue", "VARCHAR(48) DEFAULT 'general' NOT NULL"),
            ("assigned_team", "VARCHAR(48)"),
            ("waiting_on", "VARCHAR(24)"),
            ("sla_due_at", "TIMESTAMP"),
            ("escalated_at", "TIMESTAMP"),
            ("incident_id", "VARCHAR(36)"),
            ("attempt_ref", "VARCHAR(64)"),
            ("version", "INTEGER DEFAULT 1 NOT NULL"),
        ):
            _postgres_add_column_if_missing(conn, "support_tickets", column, ddl)
        _postgres_add_column_if_missing(conn, "support_ticket_messages", "visibility", "VARCHAR(16) DEFAULT 'public' NOT NULL")
        _postgres_add_column_if_missing(conn, "support_ticket_messages", "macro_code", "VARCHAR(48)")
        conn.execute(
            text(
                "UPDATE support_tickets SET "
                "environment = coalesce(nullif(trim(environment), ''), 'production'), "
                "priority = coalesce(nullif(trim(priority), ''), 'normal'), "
                "queue = coalesce(nullif(trim(queue), ''), 'general'), "
                "version = CASE WHEN version IS NULL OR version < 1 THEN 1 ELSE version END, "
                "sla_due_at = coalesce(sla_due_at, created_at + interval '24 hours');"
            )
        )
        conn.execute(text("UPDATE support_ticket_messages SET visibility = 'public' WHERE visibility IS NULL OR trim(visibility) = '';"))
        _postgres_add_column_if_missing(conn, "support_attachments", "owner_account_id", "VARCHAR(36)")
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_account_id ON support_tickets(account_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_environment ON support_tickets(environment);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_priority ON support_tickets(priority);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_queue ON support_tickets(queue);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_sla_due_at ON support_tickets(sla_due_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_escalated_at ON support_tickets(escalated_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_incident_id ON support_tickets(incident_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_attempt_ref ON support_tickets(attempt_ref);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_ticket_messages_visibility ON support_ticket_messages(visibility);"))
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_support_attachments_owner_account_id "
                "ON support_attachments(owner_account_id);"
            )
        )
        _ensure_support_attachment_binding_postgres(conn)
        _postgres_add_column_if_missing(conn, "users", "referral_code", "VARCHAR(10)")
        _postgres_add_column_if_missing(conn, "users", "account_id", "VARCHAR(36)")
        _postgres_add_column_if_missing(conn, "users", "first_purchase_done", "BOOLEAN DEFAULT FALSE")
        _postgres_add_column_if_missing(conn, "users", "sub_token", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "users", "streak_months", "INTEGER DEFAULT 0")
        _postgres_add_column_if_missing(conn, "users", "streak_last_check", "TIMESTAMP")
        _postgres_add_column_if_missing(conn, "users", "channel_bonus_claimed_at", "TIMESTAMP")
        _postgres_add_column_if_missing(conn, "users", "tos_accepted", "BOOLEAN DEFAULT FALSE")
        _postgres_add_column_if_missing(conn, "users", "trial_used", "BOOLEAN DEFAULT FALSE")
        _postgres_add_column_if_missing(conn, "users", "last_wheel_spin", "TIMESTAMP")
        _postgres_add_column_if_missing(conn, "users", "is_manual", "BOOLEAN DEFAULT FALSE")
        _postgres_add_column_if_missing(conn, "users", "created_by_admin", "BIGINT")
        _postgres_add_column_if_missing(conn, "users", "display_name", "VARCHAR(100)")
        _postgres_add_column_if_missing(conn, "users", "device_reset_last_at", "TIMESTAMP")
        _postgres_add_column_if_missing(conn, "users", "channel_bonus_active", "BOOLEAN DEFAULT FALSE")
        _postgres_add_column_if_missing(conn, "users", "channel_bonus_expires_at", "TIMESTAMP")
        _postgres_add_column_if_missing(conn, "users", "channel_bonus_revoked_at", "TIMESTAMP")
        _postgres_add_column_if_missing(conn, "users", "pending_discount_pct", "INTEGER")
        _postgres_add_column_if_missing(conn, "users", "pending_discount_code", "VARCHAR(20)")
        _postgres_add_column_if_missing(conn, "users", "pending_discount_set_at", "TIMESTAMP")
        _postgres_add_column_if_missing(conn, "users", "free_cycle_anchor_at", "TIMESTAMP")
        _postgres_add_column_if_missing(conn, "users", "free_cycle_last_reset_at", "TIMESTAMP")
        _postgres_add_column_if_missing(conn, "users", "free_cycle_next_reset_at", "TIMESTAMP")
        _postgres_add_column_if_missing(conn, "users", "current_plan_code", "VARCHAR(32)")
        _postgres_add_column_if_missing(conn, "users", "is_app_user", "BOOLEAN DEFAULT FALSE")
        _postgres_add_column_if_missing(conn, "users", "app_install_id", "VARCHAR(128)")
        _postgres_add_column_if_missing(conn, "users", "app_device_name", "VARCHAR(120)")
        _postgres_add_column_if_missing(conn, "users", "app_platform", "VARCHAR(32)")
        _postgres_add_column_if_missing(conn, "users", "app_os_version", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "users", "app_version", "VARCHAR(32)")
        _postgres_add_column_if_missing(conn, "users", "app_locale", "VARCHAR(32)")
        _postgres_add_column_if_missing(conn, "users", "app_timezone", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "users", "app_last_seen_at", "TIMESTAMP")
        _postgres_add_column_if_missing(conn, "users", "app_last_ip", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "users", "route_mode", "VARCHAR(32)")
        _postgres_add_column_if_missing(conn, "users", "route_selected_apps_json", "TEXT")
        _postgres_add_column_if_missing(conn, "users", "route_requires_elevated_privileges", "BOOLEAN")
        _postgres_add_column_if_missing(conn, "users", "linked_telegram_id", "BIGINT")
        _postgres_add_column_if_missing(conn, "users", "linked_telegram_username", "VARCHAR(100)")
        _postgres_add_column_if_missing(conn, "users", "linked_telegram_linked_at", "TIMESTAMP")
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_app_install_id ON users(app_install_id) WHERE app_install_id IS NOT NULL;"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_linked_telegram_id ON users(linked_telegram_id) WHERE linked_telegram_id IS NOT NULL;"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_account_id ON users(account_id);"))
        _postgres_add_column_if_missing(conn, "nodes", "accepting_new_clients", "BOOLEAN DEFAULT TRUE")
        _postgres_add_column_if_missing(conn, "nodes", "is_draining", "BOOLEAN DEFAULT FALSE")
        _postgres_add_column_if_missing(conn, "nodes", "active_clients", "INTEGER DEFAULT 0")
        _postgres_add_column_if_missing(conn, "nodes", "provisioned_clients_count", "INTEGER DEFAULT 0")
        _postgres_add_column_if_missing(conn, "nodes", "online_connections_hint", "INTEGER DEFAULT 0")
        _postgres_add_column_if_missing(conn, "nodes", "cpu_percent", "DOUBLE PRECISION DEFAULT 0")
        _postgres_add_column_if_missing(conn, "nodes", "memory_used_mb", "INTEGER DEFAULT 0")
        _postgres_add_column_if_missing(conn, "nodes", "memory_total_mb", "INTEGER DEFAULT 0")
        _postgres_add_column_if_missing(conn, "nodes", "disk_used_gb", "DOUBLE PRECISION DEFAULT 0")
        _postgres_add_column_if_missing(conn, "nodes", "disk_total_gb", "DOUBLE PRECISION DEFAULT 0")
        _postgres_add_column_if_missing(conn, "nodes", "disk_free_gb", "DOUBLE PRECISION DEFAULT 0")
        _postgres_add_column_if_missing(conn, "nodes", "network_rx_bytes_total", "BIGINT")
        _postgres_add_column_if_missing(conn, "nodes", "network_tx_bytes_total", "BIGINT")
        _postgres_add_column_if_missing(conn, "nodes", "network_rx_mbps", "DOUBLE PRECISION")
        _postgres_add_column_if_missing(conn, "nodes", "network_tx_mbps", "DOUBLE PRECISION")
        _postgres_add_column_if_missing(conn, "nodes", "network_total_mbps", "DOUBLE PRECISION")
        _postgres_add_column_if_missing(conn, "nodes", "network_rx_mbps_1m", "DOUBLE PRECISION")
        _postgres_add_column_if_missing(conn, "nodes", "network_tx_mbps_1m", "DOUBLE PRECISION")
        _postgres_add_column_if_missing(conn, "nodes", "network_rx_mbps_5m", "DOUBLE PRECISION")
        _postgres_add_column_if_missing(conn, "nodes", "network_tx_mbps_5m", "DOUBLE PRECISION")
        _postgres_add_column_if_missing(conn, "nodes", "tcp_retrans_percent", "DOUBLE PRECISION")
        _postgres_add_column_if_missing(conn, "nodes", "packet_loss_percent", "DOUBLE PRECISION")
        _postgres_add_column_if_missing(conn, "nodes", "edge_reachability_ok", "BOOLEAN")
        _postgres_add_column_if_missing(conn, "nodes", "authenticated_egress_ok", "BOOLEAN")
        _postgres_add_column_if_missing(conn, "nodes", "last_authenticated_egress_at", "TIMESTAMP")
        _postgres_add_column_if_missing(conn, "nodes", "authenticated_egress_error_kind", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "nodes", "dataplane_ok", "BOOLEAN")
        _postgres_add_column_if_missing(conn, "nodes", "dataplane_rtt_ms", "INTEGER")
        _postgres_add_column_if_missing(conn, "nodes", "capacity_score", "DOUBLE PRECISION")
        _postgres_add_column_if_missing(conn, "nodes", "capacity_state", "VARCHAR(32) DEFAULT 'unknown'")
        _postgres_add_column_if_missing(conn, "nodes", "capacity_reject_reason", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "nodes", "last_probe_at", "TIMESTAMP")
        _postgres_add_column_if_missing(conn, "nodes", "last_probe_stage", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "nodes", "last_probe_error_kind", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "nodes", "last_probe_error_message", "VARCHAR(500)")
        _postgres_add_column_if_missing(conn, "nodes", "hoster_family", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "nodes", "hoster_asn", "VARCHAR(32)")
        _postgres_add_column_if_missing(conn, "nodes", "hoster_subnet", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "nodes", "ipv4_health", "VARCHAR(32)")
        _postgres_add_column_if_missing(conn, "nodes", "ipv6_health", "VARCHAR(32)")
        _postgres_add_column_if_missing(conn, "nodes", "last_probe_classification", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "nodes", "transport_health_json", "TEXT")
        _postgres_add_column_if_missing(conn, "nodes", "transport_profiles_json", "TEXT")
        _postgres_add_column_if_missing(conn, "nodes", "observer_push_secret", "VARCHAR(128)")
        _postgres_add_column_if_missing(conn, "nodes", "observer_last_push_at", "TIMESTAMP")
        _postgres_add_column_if_missing(conn, "nodes", "observer_last_batch_id", "VARCHAR(128)")
        _postgres_add_column_if_missing(conn, "nodes", "observer_unmatched_count", "INTEGER DEFAULT 0")
        _postgres_add_column_if_missing(conn, "nodes", "observer_parse_error_count", "INTEGER DEFAULT 0")
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_accepting_new_clients ON nodes(accepting_new_clients);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_is_draining ON nodes(is_draining);"))
        rows = conn.execute(
            text(
                """
                SELECT id, host, vless_port, reality_sni, reality_pbk, reality_sid, fingerprint, flow, inbound_id
                FROM nodes
                WHERE transport_profiles_json IS NULL OR btrim(transport_profiles_json) = '';
                """
            )
        ).fetchall()
        for row in rows:
            mapping = row._mapping
            conn.execute(
                text("UPDATE nodes SET transport_profiles_json = :payload WHERE id = :row_id;"),
                {
                    "row_id": int(mapping["id"]),
                    "payload": _legacy_transport_catalog_payload(
                        host=mapping["host"],
                        vless_port=mapping["vless_port"],
                        reality_sni=mapping["reality_sni"],
                        reality_pbk=mapping["reality_pbk"],
                        reality_sid=mapping["reality_sid"],
                        fingerprint=mapping["fingerprint"],
                        flow=mapping["flow"],
                        inbound_id=mapping["inbound_id"],
                    ),
                },
            )
        _postgres_add_column_if_missing(conn, "node_health_samples", "cpu_percent", "DOUBLE PRECISION DEFAULT 0")
        _postgres_add_column_if_missing(conn, "node_health_samples", "memory_used_mb", "INTEGER DEFAULT 0")
        _postgres_add_column_if_missing(conn, "node_health_samples", "memory_total_mb", "INTEGER DEFAULT 0")
        _postgres_add_column_if_missing(conn, "node_health_samples", "disk_used_gb", "DOUBLE PRECISION DEFAULT 0")
        _postgres_add_column_if_missing(conn, "node_health_samples", "disk_total_gb", "DOUBLE PRECISION DEFAULT 0")
        _postgres_add_column_if_missing(conn, "node_health_samples", "disk_free_gb", "DOUBLE PRECISION DEFAULT 0")
        _postgres_add_column_if_missing(conn, "node_health_samples", "network_rx_bytes_total", "BIGINT")
        _postgres_add_column_if_missing(conn, "node_health_samples", "network_tx_bytes_total", "BIGINT")
        _postgres_add_column_if_missing(conn, "node_health_samples", "network_rx_mbps", "DOUBLE PRECISION")
        _postgres_add_column_if_missing(conn, "node_health_samples", "network_tx_mbps", "DOUBLE PRECISION")
        _postgres_add_column_if_missing(conn, "node_health_samples", "network_total_mbps", "DOUBLE PRECISION")
        _postgres_add_column_if_missing(conn, "node_health_samples", "total_up_bytes", "BIGINT DEFAULT 0")
        _postgres_add_column_if_missing(conn, "node_health_samples", "total_down_bytes", "BIGINT DEFAULT 0")
        _postgres_add_column_if_missing(conn, "node_health_samples", "total_traffic_bytes", "BIGINT DEFAULT 0")
        _postgres_add_column_if_missing(conn, "node_health_samples", "probe_at", "TIMESTAMP")
        _postgres_add_column_if_missing(conn, "node_health_samples", "probe_stage", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "node_health_samples", "probe_error_kind", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "node_health_samples", "probe_error_message", "VARCHAR(500)")
        _postgres_add_column_if_missing(conn, "node_health_samples", "probe_classification", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "node_health_samples", "ipv4_health", "VARCHAR(32)")
        _postgres_add_column_if_missing(conn, "node_health_samples", "ipv6_health", "VARCHAR(32)")
        _postgres_add_column_if_missing(conn, "node_health_samples", "transport_health_json", "TEXT")

        _ensure_capacity_domain_postgres(conn)
        _ensure_admin_ops_domain_postgres(conn)
        _ensure_economy_domain_postgres(conn)
        _ensure_payment_entitlement_claims_postgres(conn)
        _ensure_ru_probe_domain_postgres(conn)
        _ensure_release_evidence_domain_postgres(conn)
        _ensure_admin_action_intent_domain_postgres(conn)
        _ensure_emergency_catalog_domain_postgres(conn)
        _ensure_release_health_domain_postgres(conn)
        _ensure_support_bundle_domain_postgres(conn)
        _ensure_support_mode_domain_postgres(conn)
        _ensure_payment_entitlement_outbox_postgres(conn)

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS external_orders (
                  id SERIAL PRIMARY KEY,
                  order_id VARCHAR(128) NOT NULL,
                  tg_id BIGINT,
                  provider VARCHAR(32) NOT NULL,
                  plan_code VARCHAR(32),
                  source VARCHAR(32),
                  campaign VARCHAR(64),
                  acquisition_session_id VARCHAR(36),
                  promo_code VARCHAR(32),
                  meta_json TEXT,
                  amount DOUBLE PRECISION DEFAULT 0,
                  currency VARCHAR(16) DEFAULT 'RUB',
                  status VARCHAR(24) DEFAULT 'created',
                  created_at TIMESTAMP NOT NULL,
                  paid_at TIMESTAMP
                );
                """
            )
        )
        _postgres_add_column_if_missing(conn, "external_orders", "source", "VARCHAR(32)")
        _postgres_add_column_if_missing(conn, "external_orders", "campaign", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "external_orders", "acquisition_session_id", "VARCHAR(36)")
        _postgres_add_column_if_missing(conn, "external_orders", "promo_code", "VARCHAR(32)")
        _postgres_add_column_if_missing(conn, "external_orders", "meta_json", "TEXT")
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_orders_order_id ON external_orders(order_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_orders_tg_id ON external_orders(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_orders_provider ON external_orders(provider);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_orders_acquisition_session_id ON external_orders(acquisition_session_id);"))
        _ensure_external_order_attention_index(conn)
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_external_orders_provider_order "
                "ON external_orders(provider, order_id);"
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS external_payment_events (
                  id SERIAL PRIMARY KEY,
                  provider VARCHAR(32) NOT NULL,
                  event_type VARCHAR(24) NOT NULL,
                  external_id VARCHAR(128) NOT NULL,
                  order_id VARCHAR(128),
                  payload_json TEXT NOT NULL,
                  signature_ok BOOLEAN DEFAULT FALSE,
                  processed_ok BOOLEAN DEFAULT FALSE,
                  created_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_payment_events_provider ON external_payment_events(provider);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_payment_events_event_type ON external_payment_events(event_type);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_payment_events_external_id ON external_payment_events(external_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_payment_events_order_id ON external_payment_events(order_id);"))
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_external_payment_events_provider_type_extid "
                "ON external_payment_events(provider, event_type, external_id);"
            )
        )

        for column, ddl in [
            ("schema_version", "INTEGER NOT NULL DEFAULT 1"),
            ("event_id", "VARCHAR(36)"),
            ("account_id", "VARCHAR(36)"),
            ("device_id", "VARCHAR(36)"),
            ("platform", "VARCHAR(24)"),
            ("app_version", "VARCHAR(32)"),
            ("build_number", "VARCHAR(24)"),
            ("surface", "VARCHAR(32)"),
            ("subsystem", "VARCHAR(32)"),
            ("stage", "VARCHAR(64)"),
            ("result", "VARCHAR(24)"),
            ("error_category", "VARCHAR(32)"),
            ("error_code", "VARCHAR(64)"),
            ("retryable", "BOOLEAN"),
            ("attempt_number", "INTEGER"),
            ("retry_after_seconds", "INTEGER"),
            ("duration_ms", "INTEGER"),
            ("trace_id", "VARCHAR(64)"),
            ("network_class", "VARCHAR(24)"),
            ("occurred_at", "TIMESTAMP"),
            ("received_at", "TIMESTAMP"),
            ("clock_skew_state", "VARCHAR(24)"),
        ]:
            _postgres_add_column_if_missing(conn, "events", column, ddl)

        # Multi-column indexes from P0.
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_event_created ON events(event_name, created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_tg_created ON events(tg_id, created_at);"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_events_event_id ON events(event_id) WHERE event_id IS NOT NULL;"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_account_created ON events(account_id, created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_error_created ON events(error_category, error_code, created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_received_at ON events(received_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_platform_version_created ON events(platform, app_version, created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_result_created ON events(result, created_at);"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS warp_events (
                  id SERIAL PRIMARY KEY,
                  tg_id BIGINT NOT NULL,
                  install_id VARCHAR(128),
                  event_name VARCHAR(64) NOT NULL,
                  state VARCHAR(32) NOT NULL,
                  reason_code VARCHAR(64),
                  runtime_ready BOOLEAN DEFAULT FALSE NOT NULL,
                  consented BOOLEAN DEFAULT FALSE NOT NULL,
                  meta_json TEXT,
                  created_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_events_tg_id ON warp_events(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_events_install_id ON warp_events(install_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_events_event_name ON warp_events(event_name);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_events_state ON warp_events(state);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_events_created_at ON warp_events(created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_events_tg_created ON warp_events(tg_id, created_at);"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS warp_materials (
                  id SERIAL PRIMARY KEY,
                  tg_id BIGINT NOT NULL,
                  install_id VARCHAR(128),
                  source VARCHAR(64) NOT NULL DEFAULT 'operator_provisioned',
                  mode VARCHAR(32) NOT NULL DEFAULT 'proxy_over_warp',
                  state VARCHAR(32) NOT NULL DEFAULT 'ready',
                  wireguard_ciphertext TEXT NOT NULL,
                  account_ciphertext TEXT,
                  material_hash VARCHAR(64),
                  is_active BOOLEAN NOT NULL DEFAULT TRUE,
                  provisioned_at TIMESTAMP NOT NULL,
                  rotation_requested_at TIMESTAMP,
                  revoked_at TIMESTAMP,
                  updated_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_materials_tg_id ON warp_materials(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_materials_install_id ON warp_materials(install_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_materials_state ON warp_materials(state);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_materials_material_hash ON warp_materials(material_hash);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_materials_is_active ON warp_materials(is_active);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_warp_materials_provisioned_at ON warp_materials(provisioned_at);"))
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_warp_materials_tg_install_active "
                "ON warp_materials(tg_id, install_id, is_active);"
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS awg2_lab_materials (
                  id SERIAL PRIMARY KEY,
                  tg_id BIGINT NOT NULL,
                  install_id VARCHAR(128) NOT NULL,
                  contract_id VARCHAR(64) NOT NULL,
                  contract_sha256 VARCHAR(64) NOT NULL,
                  generation VARCHAR(64) NOT NULL,
                  endpoint_revision VARCHAR(64) NOT NULL,
                  server_record_id VARCHAR(64) NOT NULL,
                  node_code VARCHAR(64) NOT NULL,
                  endpoint_ciphertext TEXT NOT NULL,
                  material_hash VARCHAR(64) NOT NULL,
                  state VARCHAR(32) NOT NULL DEFAULT 'ready',
                  is_active BOOLEAN NOT NULL DEFAULT TRUE,
                  provisioned_at TIMESTAMP NOT NULL,
                  revoked_at TIMESTAMP,
                  updated_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_tg_id ON awg2_lab_materials(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_install_id ON awg2_lab_materials(install_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_generation ON awg2_lab_materials(generation);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_server_record_id ON awg2_lab_materials(server_record_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_node_code ON awg2_lab_materials(node_code);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_material_hash ON awg2_lab_materials(material_hash);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_state ON awg2_lab_materials(state);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_is_active ON awg2_lab_materials(is_active);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_provisioned_at ON awg2_lab_materials(provisioned_at);"))
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_awg2_lab_materials_tg_install_active "
                "ON awg2_lab_materials(tg_id, install_id, is_active);"
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS awg31_lab_materials (
                  id SERIAL PRIMARY KEY,
                  tg_id BIGINT NOT NULL,
                  install_id VARCHAR(128) NOT NULL,
                  contract_id VARCHAR(64) NOT NULL,
                  contract_sha256 VARCHAR(64) NOT NULL,
                  generation VARCHAR(64) NOT NULL,
                  endpoint_revision VARCHAR(64) NOT NULL,
                  server_record_id VARCHAR(64) NOT NULL,
                  node_code VARCHAR(64) NOT NULL,
                  endpoint_ciphertext TEXT NOT NULL,
                  material_hash VARCHAR(64) NOT NULL,
                  state VARCHAR(32) NOT NULL DEFAULT 'ready',
                  is_active BOOLEAN NOT NULL DEFAULT TRUE,
                  provisioned_at TIMESTAMP NOT NULL,
                  revoked_at TIMESTAMP,
                  updated_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_tg_id ON awg31_lab_materials(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_install_id ON awg31_lab_materials(install_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_generation ON awg31_lab_materials(generation);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_server_record_id ON awg31_lab_materials(server_record_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_node_code ON awg31_lab_materials(node_code);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_material_hash ON awg31_lab_materials(material_hash);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_state ON awg31_lab_materials(state);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_is_active ON awg31_lab_materials(is_active);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_provisioned_at ON awg31_lab_materials(provisioned_at);"))
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_awg31_lab_materials_tg_install_active "
                "ON awg31_lab_materials(tg_id, install_id, is_active);"
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS funnel_events (
                  id SERIAL PRIMARY KEY,
                  session_id VARCHAR(96) NOT NULL,
                  tg_id BIGINT,
                  channel VARCHAR(32) NOT NULL DEFAULT 'site',
                  event_name VARCHAR(64) NOT NULL,
                  stage VARCHAR(64) NOT NULL,
                  source VARCHAR(64) NOT NULL DEFAULT 'unknown',
                  path VARCHAR(512),
                  referrer VARCHAR(600),
                  campaign VARCHAR(64),
                  meta_json VARCHAR(4000),
                  created_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_funnel_events_session_id ON funnel_events(session_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_funnel_events_tg_id ON funnel_events(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_funnel_events_channel ON funnel_events(channel);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_funnel_events_event_name ON funnel_events(event_name);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_funnel_events_stage ON funnel_events(stage);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_funnel_events_source ON funnel_events(source);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_funnel_events_created_at ON funnel_events(created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_funnel_events_stage_created ON funnel_events(stage, created_at);"))
        _postgres_add_column_if_missing(conn, "pay_attempts", "acquisition_session_id", "VARCHAR(36)")
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pay_attempts_tg_status_started ON pay_attempts(tg_id, status, started_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pay_attempts_acquisition_session_id ON pay_attempts(acquisition_session_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_offers_tg_status_exp ON offers(tg_id, status, expires_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_points_ledger_tg_exp_created ON points_ledger(tg_id, expires_at, created_at);"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_campaign_sends_tg_campaign ON campaign_sends(tg_id, campaign_key);"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_promo_usage_tg_code ON promo_usage(tg_id, promo_code);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS observer_batches (
                  id SERIAL PRIMARY KEY,
                  node_id INTEGER NOT NULL,
                  batch_id VARCHAR(128) NOT NULL,
                  cursor_json TEXT,
                  observation_count INTEGER DEFAULT 0,
                  accepted_count INTEGER DEFAULT 0,
                  deduped_count INTEGER DEFAULT 0,
                  unmatched_count INTEGER DEFAULT 0,
                  parse_error_count INTEGER DEFAULT 0,
                  updated_tg_ids_json TEXT,
                  created_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS observer_daily_observations (
                  id SERIAL PRIMARY KEY,
                  tg_id BIGINT NOT NULL,
                  node_id INTEGER NOT NULL,
                  source_ip_raw VARCHAR(64) NOT NULL,
                  score_ip_key VARCHAR(64) NOT NULL,
                  day_bucket DATE NOT NULL,
                  first_seen_at TIMESTAMP NOT NULL,
                  last_seen_at TIMESTAMP NOT NULL,
                  hit_count INTEGER DEFAULT 0,
                  identity_source VARCHAR(32) NOT NULL,
                  counts_for_suspicion BOOLEAN DEFAULT TRUE
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS observer_window_observations (
                  id SERIAL PRIMARY KEY,
                  tg_id BIGINT NOT NULL,
                  node_id INTEGER NOT NULL,
                  source_ip_raw VARCHAR(64) NOT NULL,
                  score_ip_key VARCHAR(64) NOT NULL,
                  window_bucket_at TIMESTAMP NOT NULL,
                  first_seen_at TIMESTAMP NOT NULL,
                  last_seen_at TIMESTAMP NOT NULL,
                  hit_count INTEGER DEFAULT 0,
                  counts_for_suspicion BOOLEAN DEFAULT TRUE
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS observer_user_state (
                  tg_id BIGINT PRIMARY KEY,
                  state VARCHAR(20) NOT NULL DEFAULT 'ok',
                  reasons_json TEXT,
                  observed_ip_count_24h INTEGER DEFAULT 0,
                  observed_ip_count_7d INTEGER DEFAULT 0,
                  observed_ip_count_30d INTEGER DEFAULT 0,
                  observed_node_count_24h INTEGER DEFAULT 0,
                  observed_node_count_7d INTEGER DEFAULT 0,
                  observed_node_count_30d INTEGER DEFAULT 0,
                  overlap_count_24h INTEGER DEFAULT 0,
                  last_observed_at TIMESTAMP,
                  updated_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_observer_batches_node_batch "
                "ON observer_batches(node_id, batch_id);"
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_observer_daily_tg_node_ip_day "
                "ON observer_daily_observations(tg_id, node_id, source_ip_raw, day_bucket);"
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observer_daily_tg_id ON observer_daily_observations(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observer_daily_node_id ON observer_daily_observations(node_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observer_daily_score_ip_key ON observer_daily_observations(score_ip_key);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observer_daily_day_bucket ON observer_daily_observations(day_bucket);"))
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_observer_window_tg_node_score_bucket "
                "ON observer_window_observations(tg_id, node_id, score_ip_key, window_bucket_at);"
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observer_window_tg_id ON observer_window_observations(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observer_window_node_id ON observer_window_observations(node_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observer_window_score_ip_key ON observer_window_observations(score_ip_key);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observer_window_bucket ON observer_window_observations(window_bucket_at);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS plan_catalog (
                  id SERIAL PRIMARY KEY,
                  code VARCHAR(32) NOT NULL,
                  label VARCHAR(120) NOT NULL,
                  amount_rub INTEGER DEFAULT 0,
                  amount_stars INTEGER DEFAULT 0,
                  days INTEGER DEFAULT 30,
                  device_limit INTEGER DEFAULT 1,
                  node_policy VARCHAR(32),
                  badge VARCHAR(32),
                  is_active BOOLEAN DEFAULT TRUE,
                  sort_order INTEGER DEFAULT 100,
                  created_at TIMESTAMP NOT NULL,
                  updated_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_plan_catalog_code ON plan_catalog(code);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_plan_catalog_active_sort ON plan_catalog(is_active, sort_order);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS live_updates (
                  id SERIAL PRIMARY KEY,
                  title VARCHAR(160) NOT NULL,
                  summary VARCHAR(600) NOT NULL,
                  link VARCHAR(600) NOT NULL,
                  channel_username VARCHAR(64),
                  post_id INTEGER,
                  published_at TIMESTAMP,
                  is_active BOOLEAN DEFAULT TRUE,
                  sort_order INTEGER DEFAULT 100,
                  created_at TIMESTAMP NOT NULL,
                  updated_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        _postgres_add_column_if_missing(conn, "live_updates", "channel_username", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "live_updates", "post_id", "INTEGER")
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_live_updates_active_sort ON live_updates(is_active, sort_order);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_live_updates_channel_post ON live_updates(channel_username, post_id);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS news_draft_runs (
                  id SERIAL PRIMARY KEY,
                  run_id VARCHAR(64) NOT NULL,
                  status VARCHAR(24) NOT NULL,
                  sources_total INTEGER DEFAULT 0 NOT NULL,
                  sources_succeeded INTEGER DEFAULT 0 NOT NULL,
                  sources_failed INTEGER DEFAULT 0 NOT NULL,
                  candidates_seen INTEGER DEFAULT 0 NOT NULL,
                  drafts_created INTEGER DEFAULT 0 NOT NULL,
                  duplicates_skipped INTEGER DEFAULT 0 NOT NULL,
                  duration_ms INTEGER,
                  failure_code VARCHAR(64),
                  started_at TIMESTAMP NOT NULL,
                  finished_at TIMESTAMP
                );
                """
            )
        )
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_news_draft_runs_run_id ON news_draft_runs(run_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_draft_runs_started ON news_draft_runs(started_at);"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS news_drafts (
                  id SERIAL PRIMARY KEY,
                  source_name VARCHAR(64) NOT NULL,
                  source_url VARCHAR(600) NOT NULL,
                  source_title VARCHAR(300) NOT NULL,
                  source_item_sha256 VARCHAR(64) NOT NULL,
                  fetch_run_id VARCHAR(64) NOT NULL,
                  source_published_at TIMESTAMP,
                  status VARCHAR(24) DEFAULT 'pending' NOT NULL,
                  reviewed_by_tg_id BIGINT,
                  reviewed_at TIMESTAMP,
                  live_update_id INTEGER,
                  discovered_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_news_drafts_item_hash ON news_drafts(source_item_sha256);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_drafts_status_discovered ON news_drafts(status, discovered_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_drafts_fetch_run ON news_drafts(fetch_run_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_drafts_live_update ON news_drafts(live_update_id);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS start_links (
                  id SERIAL PRIMARY KEY,
                  code VARCHAR(64) NOT NULL,
                  description VARCHAR(240),
                  target_action VARCHAR(64),
                  is_active BOOLEAN DEFAULT TRUE,
                  created_at TIMESTAMP NOT NULL,
                  updated_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_start_links_code ON start_links(code);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_start_links_is_active ON start_links(is_active);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                  "key" VARCHAR(64) PRIMARY KEY,
                  value_json TEXT,
                  updated_at TIMESTAMP NOT NULL
                );
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS key_action_history (
                  id SERIAL PRIMARY KEY,
                  tg_id BIGINT NOT NULL,
                  node_code VARCHAR(32),
                  action VARCHAR(64) NOT NULL,
                  actor_tg_id BIGINT,
                  source VARCHAR(32) DEFAULT 'admin',
                  meta TEXT,
                  created_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_key_action_history_tg_id ON key_action_history(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_key_action_history_node_code ON key_action_history(node_code);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_key_action_history_created_at ON key_action_history(created_at);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS user_key_policy (
                  id SERIAL PRIMARY KEY,
                  tg_id BIGINT NOT NULL,
                  node_code VARCHAR(32) NOT NULL,
                  burst_mbps INTEGER,
                  soft_cap_gb INTEGER,
                  hard_cap_gb INTEGER,
                  notify_soft BOOLEAN DEFAULT TRUE,
                  notify_hard BOOLEAN DEFAULT TRUE,
                  auto_disable_on_hard BOOLEAN DEFAULT TRUE,
                  updated_by BIGINT,
                  updated_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_user_key_policy_tg_node "
                "ON user_key_policy(tg_id, node_code);"
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_key_policy_tg_id ON user_key_policy(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_key_policy_node_code ON user_key_policy(node_code);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS referral_bonus_queue (
                  id SERIAL PRIMARY KEY,
                  referrer_tg_id BIGINT NOT NULL,
                  referred_tg_id BIGINT NOT NULL,
                  order_id VARCHAR(128) NOT NULL,
                  queued_at TIMESTAMP NOT NULL,
                  ready_at TIMESTAMP NOT NULL,
                  status VARCHAR(24) DEFAULT 'pending',
                  processed_at TIMESTAMP,
                  meta TEXT
                );
                """
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_referral_bonus_queue_order_pair "
                "ON referral_bonus_queue(order_id, referrer_tg_id, referred_tg_id);"
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_referral_bonus_queue_ready_at ON referral_bonus_queue(ready_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_referral_bonus_queue_status ON referral_bonus_queue(status);"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS incentive_campaigns (
                  id SERIAL PRIMARY KEY,
                  public_id VARCHAR(36),
                  name VARCHAR(120) NOT NULL,
                  campaign_type VARCHAR(16) NOT NULL,
                  target_value VARCHAR(64) NOT NULL,
                  objective VARCHAR(32) NOT NULL DEFAULT 'retention',
                  lifecycle_status VARCHAR(24) NOT NULL DEFAULT 'draft',
                  revision INTEGER NOT NULL DEFAULT 1,
                  commercial_revision VARCHAR(32),
                  legal_profile_status VARCHAR(24) NOT NULL DEFAULT 'missing',
                  channels_json TEXT,
                  seller_profile_id VARCHAR(64),
                  terms_revision VARCHAR(64),
                  paid_cap INTEGER NOT NULL DEFAULT 0,
                  paid_conversions_count INTEGER NOT NULL DEFAULT 0,
                  capacity_guard_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                  capacity_band VARCHAR(16) NOT NULL DEFAULT 'unknown',
                  state_reason VARCHAR(64) NOT NULL DEFAULT 'legacy_unclassified',
                  last_policy_evaluated_at TIMESTAMP,
                  killed_at TIMESTAMP,
                  segment VARCHAR(32) DEFAULT 'all_active',
                  starts_at TIMESTAMP,
                  ends_at TIMESTAMP,
                  max_activations INTEGER DEFAULT -1,
                  activations_count INTEGER DEFAULT 0,
                  auto_disable BOOLEAN DEFAULT TRUE,
                  is_active BOOLEAN DEFAULT FALSE,
                  created_by BIGINT,
                  metadata_json TEXT,
                  created_at TIMESTAMP NOT NULL,
                  updated_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_incentive_campaigns_type_target ON incentive_campaigns(campaign_type, target_value);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_incentive_campaigns_is_active ON incentive_campaigns(is_active);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_incentive_campaigns_ends_at ON incentive_campaigns(ends_at);"))
        for column, ddl in [
            ("public_id", "VARCHAR(36)"),
            ("objective", "VARCHAR(32) NOT NULL DEFAULT 'retention'"),
            ("lifecycle_status", "VARCHAR(24) NOT NULL DEFAULT 'draft'"),
            ("revision", "INTEGER NOT NULL DEFAULT 1"),
            ("commercial_revision", "VARCHAR(32)"),
            ("legal_profile_status", "VARCHAR(24) NOT NULL DEFAULT 'missing'"),
            ("channels_json", "TEXT"),
            ("seller_profile_id", "VARCHAR(64)"),
            ("terms_revision", "VARCHAR(64)"),
            ("paid_cap", "INTEGER NOT NULL DEFAULT 0"),
            ("paid_conversions_count", "INTEGER NOT NULL DEFAULT 0"),
            ("capacity_guard_enabled", "BOOLEAN NOT NULL DEFAULT TRUE"),
            ("capacity_band", "VARCHAR(16) NOT NULL DEFAULT 'unknown'"),
            ("state_reason", "VARCHAR(64) NOT NULL DEFAULT 'legacy_unclassified'"),
            ("last_policy_evaluated_at", "TIMESTAMP"),
            ("killed_at", "TIMESTAMP"),
        ]:
            _postgres_add_column_if_missing(conn, "incentive_campaigns", column, ddl)
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_incentive_campaigns_public_id "
                "ON incentive_campaigns(public_id);"
            )
        )
        conn.execute(
            text(
                "UPDATE incentive_campaigns SET is_active=FALSE, lifecycle_status='draft', "
                "state_reason='legacy_unclassified' WHERE public_id IS NULL AND is_active=TRUE;"
            )
        )
        _ensure_commercial_offer_domain_postgres(conn)

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS reward_claims (
                  id SERIAL PRIMARY KEY,
                  tg_id BIGINT NOT NULL,
                  reward_key VARCHAR(64) NOT NULL,
                  meta TEXT,
                  claimed_at TIMESTAMP NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_reward_claim_tg_key ON reward_claims(tg_id, reward_key);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_reward_claims_tg_id ON reward_claims(tg_id);"))

        # Seed default retention templates for admin editing (idempotent).
        _ensure_acquisition_domain_postgres(conn)
        _ensure_free_profile_schema_postgres(conn)
        _ensure_reward_schema_postgres(conn)
        _seed_retention_templates(conn, dialect="postgresql")
        _seed_plan_catalog(conn, dialect="postgresql")

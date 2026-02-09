from __future__ import annotations

from sqlalchemy import Engine, text


def _sqlite_column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table});")).fetchall()
    return any(r[1] == column for r in rows)  # (cid, name, type, notnull, dflt_value, pk)


def _sqlite_index_exists(conn, index_name: str) -> bool:
    rows = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='index' AND name=:name;"),
        {"name": index_name},
    ).fetchall()
    return bool(rows)


def run_migrations(engine: Engine) -> None:
    """
    Idempotent SQLite migrations for legacy DBs.
    create_all handles new tables, but won't add columns to existing ones.
    """
    with engine.begin() as conn:
        # users table: add columns if missing
        if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")).fetchone():
            wanted_cols = [
                ("referral_code", "VARCHAR(10)"),
                ("first_purchase_done", "BOOLEAN DEFAULT 0"),
                ("sub_token", "VARCHAR(64)"),
                ("streak_months", "INTEGER DEFAULT 0"),
                ("streak_last_check", "DATETIME"),
                ("channel_bonus_claimed_at", "DATETIME"),
                ("tos_accepted", "BOOLEAN DEFAULT 0"),
                ("trial_used", "BOOLEAN DEFAULT 0"),
                ("last_wheel_spin", "DATETIME"),
                ("is_manual", "BOOLEAN DEFAULT 0"),
                ("created_by_admin", "BIGINT"),
                ("display_name", "VARCHAR(100)"),
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
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_achievements_tg_id ON achievements(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_nodes_tg_id ON user_nodes(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_nodes_node_id ON user_nodes(node_id);"))

        # support_tickets table: backfill columns for legacy DBs if table already exists
        if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='support_tickets';")).fetchone():
            wanted_cols = [
                ("status", "VARCHAR(20) DEFAULT 'open'"),
                ("subject", "VARCHAR(200)"),
                ("assigned_admin_tg_id", "BIGINT"),
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
                    SET updated_at = coalesce(updated_at, created_at)
                    WHERE updated_at IS NULL;
                    """
                )
            )

        # Ticket indexes (safe for both new and old DBs).
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_user_tg_id ON support_tickets(user_tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_status ON support_tickets(status);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_tickets_updated_at ON support_tickets(updated_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_ticket_messages_ticket_id ON support_ticket_messages(ticket_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_support_ticket_messages_sender_tg_id ON support_ticket_messages(sender_tg_id);"))

        # support_ticket_messages: media metadata for richer support intake.
        if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='support_ticket_messages';")).fetchone():
            wanted_cols = [
                ("media_type", "VARCHAR(32)"),
                ("media_file_id", "VARCHAR(256)"),
                ("media_payload", "VARCHAR(2000)"),
            ]
            for col, ddl in wanted_cols:
                if not _sqlite_column_exists(conn, "support_ticket_messages", col):
                    conn.execute(text(f"ALTER TABLE support_ticket_messages ADD COLUMN {col} {ddl};"))

        # nodes: runtime health fields for soft LB + fallback.
        if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='nodes';")).fetchone():
            wanted_cols = [
                ("health_score", "FLOAT DEFAULT 0"),
                ("last_health_at", "DATETIME"),
                ("is_healthy", "BOOLEAN DEFAULT 1"),
                ("panel_latency_ms", "INTEGER"),
                ("panel_error_rate", "FLOAT DEFAULT 0"),
                ("active_clients", "INTEGER DEFAULT 0"),
                ("last_ok_at", "DATETIME"),
            ]
            for col, ddl in wanted_cols:
                if not _sqlite_column_exists(conn, "nodes", col):
                    conn.execute(text(f"ALTER TABLE nodes ADD COLUMN {col} {ddl};"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_enabled ON nodes(enabled);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_is_healthy ON nodes(is_healthy);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_health_score ON nodes(health_score);"))

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
                  is_healthy BOOLEAN DEFAULT 1,
                  score FLOAT DEFAULT 0,
                  source VARCHAR(64) DEFAULT 'collector'
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_node_health_samples_node_code ON node_health_samples(node_code);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_node_health_samples_sampled_at ON node_health_samples(sampled_at);"))

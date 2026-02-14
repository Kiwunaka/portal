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
    dialect = (getattr(engine, "dialect", None) and engine.dialect.name or "").lower()
    if dialect == "postgresql":
        _run_postgres_migrations(engine)
        return
    if dialect and dialect != "sqlite":
        return

    with engine.begin() as conn:
        # users table: add columns if missing
        if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")).fetchone():
            wanted_cols = [
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
                ("free_cycle_anchor_at", "DATETIME"),
                ("free_cycle_last_reset_at", "DATETIME"),
                ("free_cycle_next_reset_at", "DATETIME"),
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

        # events: minimal product analytics.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tg_id BIGINT NOT NULL,
                  event_name VARCHAR(64) NOT NULL,
                  source VARCHAR(32) DEFAULT 'unknown',
                  session_id VARCHAR(64),
                  meta_json VARCHAR(4000),
                  created_at DATETIME NOT NULL
                );
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_tg_id ON events(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_event_name ON events(event_name);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_event_created ON events(event_name, created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_tg_created ON events(tg_id, created_at);"))

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
                  started_at DATETIME NOT NULL,
                  updated_at DATETIME NOT NULL,
                  paid_at DATETIME,
                  abandoned_notified_at DATETIME
                );
                """
            )
        )
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_pay_attempts_invoice_payload ON pay_attempts(invoice_payload);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pay_attempts_tg_status_started ON pay_attempts(tg_id, status, started_at);"))

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
                ("promo_code", "VARCHAR(32)"),
                ("meta_json", "TEXT"),
            ]
            for col, ddl in wanted_external_cols:
                if not _sqlite_column_exists(conn, "external_orders", col):
                    conn.execute(text(f"ALTER TABLE external_orders ADD COLUMN {col} {ddl};"))

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


def _run_postgres_migrations(engine: Engine) -> None:
    """
    PostgreSQL-safe idempotent migrations.
    `create_all()` already creates tables; here we only ensure additive columns/indexes.
    """
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_code VARCHAR(10);"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS first_purchase_done BOOLEAN DEFAULT FALSE;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS sub_token VARCHAR(64);"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS streak_months INTEGER DEFAULT 0;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS streak_last_check TIMESTAMP;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS channel_bonus_claimed_at TIMESTAMP;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS tos_accepted BOOLEAN DEFAULT FALSE;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_used BOOLEAN DEFAULT FALSE;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_wheel_spin TIMESTAMP;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_manual BOOLEAN DEFAULT FALSE;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_by_admin BIGINT;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name VARCHAR(100);"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS device_reset_last_at TIMESTAMP;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS channel_bonus_active BOOLEAN DEFAULT FALSE;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS channel_bonus_expires_at TIMESTAMP;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS channel_bonus_revoked_at TIMESTAMP;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS free_cycle_anchor_at TIMESTAMP;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS free_cycle_last_reset_at TIMESTAMP;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS free_cycle_next_reset_at TIMESTAMP;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS current_plan_code VARCHAR(32);"))

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
        conn.execute(text("ALTER TABLE external_orders ADD COLUMN IF NOT EXISTS source VARCHAR(32);"))
        conn.execute(text("ALTER TABLE external_orders ADD COLUMN IF NOT EXISTS campaign VARCHAR(64);"))
        conn.execute(text("ALTER TABLE external_orders ADD COLUMN IF NOT EXISTS promo_code VARCHAR(32);"))
        conn.execute(text("ALTER TABLE external_orders ADD COLUMN IF NOT EXISTS meta_json TEXT;"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_orders_order_id ON external_orders(order_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_orders_tg_id ON external_orders(tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_external_orders_provider ON external_orders(provider);"))
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

        # Multi-column indexes from P0.
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_event_created ON events(event_name, created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_tg_created ON events(tg_id, created_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pay_attempts_tg_status_started ON pay_attempts(tg_id, status, started_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_offers_tg_status_exp ON offers(tg_id, status, expires_at);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_points_ledger_tg_exp_created ON points_ledger(tg_id, expires_at, created_at);"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_campaign_sends_tg_campaign ON campaign_sends(tg_id, campaign_key);"))

from __future__ import annotations

import os
from datetime import datetime, timezone

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


RETENTION_TEMPLATE_PRESETS: dict[str, str] = {
    "retention_welcome_a": (
        "✨ Добро пожаловать в Portal.\n\n"
        "Запуск занимает 1-2 минуты:\n"
        "1) Откройте раздел Подключение.\n"
        "2) Импортируйте ключ в клиент.\n"
        "3) Проверьте статус узлов.\n\n"
        "Актуальные апдейты публикуются в {channel}."
    ),
    "retention_welcome_b": (
        "🛡 Профиль готов к работе.\n\n"
        "Перед первым запуском:\n"
        "• выберите приложение для своей платформы;\n"
        "• импортируйте ключ одним действием;\n"
        "• сохраните канал {channel} для обновлений."
    ),
    "retention_t3_a": (
        "⌛ До окончания доступа осталось около 3 дней.\n\n"
        "Продлите заранее, чтобы сохранить текущий режим без паузы."
    ),
    "retention_t3_b": (
        "📅 Напоминание T-3.\n\n"
        "Продление заранее помогает избежать перерыва в подключении."
    ),
    "retention_t1_a": (
        "⏱ До завершения подписки примерно 1 день.\n\n"
        "Продлите сейчас, чтобы избежать паузы в доступе."
    ),
    "retention_t1_b": (
        "⚡ T-1: срок доступа заканчивается в ближайшие сутки.\n\n"
        "Продление сейчас сохранит привычный режим без перерыва."
    ),
    "retention_t0_a": (
        "🚨 Срок подписки подходит к финалу.\n\n"
        "Если доступ нужен без пауз, продлите прямо сейчас."
    ),
    "retention_t0_b": (
        "🔔 Подписка почти завершена.\n\n"
        "Пара минут на продление — и режим останется активным."
    ),
    "retention_reactivation_a": (
        "🌍 Профиль и история сохранены.\n\n"
        "Вернитесь в один клик и продолжайте без повторной настройки."
    ),
    "retention_reactivation_b": (
        "🧭 Доступ завершился, но его можно восстановить за минуту.\n\n"
        "Откройте оплату и вернитесь в рабочий режим."
    ),
}

DEFAULT_PAID_DEVICE_LIMIT = max(1, int(os.getenv("PAID_LIMIT_IP") or "5"))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

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
            {"key": key, "text": value, "created_at": _utcnow()},
        )


PLAN_CATALOG_PRESETS = [
    {
        "code": "start_99",
        "label": "Приветственный 30 дней",
        "amount_rub": 99,
        "amount_stars": 99,
        "days": 30,
        "device_limit": 1,
        "node_policy": "nl_only",
        "badge": "Один раз",
        "is_active": True,
        "sort_order": 1,
    },
    {
        "code": "1_month",
        "label": "1 месяц",
        "amount_rub": 249,
        "amount_stars": 249,
        "days": 30,
        "device_limit": DEFAULT_PAID_DEVICE_LIMIT,
        "node_policy": "paid_pool",
        "badge": "Базовый",
        "is_active": True,
        "sort_order": 2,
    },
    {
        "code": "3_months",
        "label": "3 месяца",
        "amount_rub": 699,
        "amount_stars": 699,
        "days": 91,
        "device_limit": DEFAULT_PAID_DEVICE_LIMIT,
        "node_policy": "paid_pool",
        "badge": "Выгоднее",
        "is_active": True,
        "sort_order": 3,
    },
    {
        "code": "6_months",
        "label": "6 месяцев",
        "amount_rub": 1199,
        "amount_stars": 1199,
        "days": 182,
        "device_limit": DEFAULT_PAID_DEVICE_LIMIT,
        "node_policy": "paid_pool",
        "badge": "Популярный",
        "is_active": True,
        "sort_order": 4,
    },
    {
        "code": "9_months",
        "label": "9 месяцев",
        "amount_rub": 1399,
        "amount_stars": 1399,
        "days": 273,
        "device_limit": DEFAULT_PAID_DEVICE_LIMIT,
        "node_policy": "paid_pool",
        "badge": "Надолго",
        "is_active": True,
        "sort_order": 5,
    },
    {
        "code": "12_months",
        "label": "12 месяцев",
        "amount_rub": 1644,
        "amount_stars": 1644,
        "days": 365,
        "device_limit": DEFAULT_PAID_DEVICE_LIMIT,
        "node_policy": "paid_pool",
        "badge": "-45%",
        "is_active": True,
        "sort_order": 6,
    },
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
                "updated_at": now,
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
                "created_at": now,
                "updated_at": now,
            },
        )

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
                ("pending_discount_pct", "INTEGER"),
                ("pending_discount_code", "VARCHAR(20)"),
                ("pending_discount_set_at", "DATETIME"),
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
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_promo_usage_tg_code ON promo_usage(tg_id, promo_code);"))

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
                ("accepting_new_clients", "BOOLEAN DEFAULT 1"),
                ("is_draining", "BOOLEAN DEFAULT 0"),
                ("panel_latency_ms", "INTEGER"),
                ("panel_error_rate", "FLOAT DEFAULT 0"),
                ("active_clients", "INTEGER DEFAULT 0"),
                ("cpu_percent", "FLOAT DEFAULT 0"),
                ("memory_used_mb", "INTEGER DEFAULT 0"),
                ("memory_total_mb", "INTEGER DEFAULT 0"),
                ("disk_used_gb", "FLOAT DEFAULT 0"),
                ("disk_total_gb", "FLOAT DEFAULT 0"),
                ("disk_free_gb", "FLOAT DEFAULT 0"),
                ("last_ok_at", "DATETIME"),
            ]
            for col, ddl in wanted_cols:
                if not _sqlite_column_exists(conn, "nodes", col):
                    conn.execute(text(f"ALTER TABLE nodes ADD COLUMN {col} {ddl};"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_enabled ON nodes(enabled);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_accepting_new_clients ON nodes(accepting_new_clients);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_is_draining ON nodes(is_draining);"))
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
                  cpu_percent FLOAT DEFAULT 0,
                  memory_used_mb INTEGER DEFAULT 0,
                  memory_total_mb INTEGER DEFAULT 0,
                  disk_used_gb FLOAT DEFAULT 0,
                  disk_total_gb FLOAT DEFAULT 0,
                  disk_free_gb FLOAT DEFAULT 0,
                  total_up_bytes BIGINT DEFAULT 0,
                  total_down_bytes BIGINT DEFAULT 0,
                  total_traffic_bytes BIGINT DEFAULT 0,
                  is_healthy BOOLEAN DEFAULT 1,
                  score FLOAT DEFAULT 0,
                  source VARCHAR(64) DEFAULT 'collector'
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
                ("total_up_bytes", "BIGINT DEFAULT 0"),
                ("total_down_bytes", "BIGINT DEFAULT 0"),
                ("total_traffic_bytes", "BIGINT DEFAULT 0"),
            ]
            for col, ddl in node_sample_cols:
                if not _sqlite_column_exists(conn, "node_health_samples", col):
                    conn.execute(text(f"ALTER TABLE node_health_samples ADD COLUMN {col} {ddl};"))
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
                  name VARCHAR(120) NOT NULL,
                  campaign_type VARCHAR(16) NOT NULL,
                  target_value VARCHAR(64) NOT NULL,
                  segment VARCHAR(32) DEFAULT 'all_active',
                  starts_at DATETIME,
                  ends_at DATETIME,
                  max_activations INTEGER DEFAULT -1,
                  activations_count INTEGER DEFAULT 0,
                  auto_disable BOOLEAN DEFAULT 1,
                  is_active BOOLEAN DEFAULT 1,
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
        # already accepts the newer PORTAL-XXXX-XXXX format without table rebuild.

        # Seed default retention templates for admin editing (idempotent).
        _seed_retention_templates(conn, dialect="sqlite")
        _seed_plan_catalog(conn, dialect="sqlite")


def _run_postgres_migrations(engine: Engine) -> None:
    """
    PostgreSQL-safe idempotent migrations.
    `create_all()` already creates tables; here we only ensure additive columns/indexes.
    """
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE gift_cards ALTER COLUMN code TYPE VARCHAR(32);"))
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
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS pending_discount_pct INTEGER;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS pending_discount_code VARCHAR(20);"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS pending_discount_set_at TIMESTAMP;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS free_cycle_anchor_at TIMESTAMP;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS free_cycle_last_reset_at TIMESTAMP;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS free_cycle_next_reset_at TIMESTAMP;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS current_plan_code VARCHAR(32);"))
        conn.execute(text("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS accepting_new_clients BOOLEAN DEFAULT TRUE;"))
        conn.execute(text("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS is_draining BOOLEAN DEFAULT FALSE;"))
        conn.execute(text("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS cpu_percent DOUBLE PRECISION DEFAULT 0;"))
        conn.execute(text("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS memory_used_mb INTEGER DEFAULT 0;"))
        conn.execute(text("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS memory_total_mb INTEGER DEFAULT 0;"))
        conn.execute(text("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS disk_used_gb DOUBLE PRECISION DEFAULT 0;"))
        conn.execute(text("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS disk_total_gb DOUBLE PRECISION DEFAULT 0;"))
        conn.execute(text("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS disk_free_gb DOUBLE PRECISION DEFAULT 0;"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_accepting_new_clients ON nodes(accepting_new_clients);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nodes_is_draining ON nodes(is_draining);"))
        conn.execute(text("ALTER TABLE node_health_samples ADD COLUMN IF NOT EXISTS cpu_percent DOUBLE PRECISION DEFAULT 0;"))
        conn.execute(text("ALTER TABLE node_health_samples ADD COLUMN IF NOT EXISTS memory_used_mb INTEGER DEFAULT 0;"))
        conn.execute(text("ALTER TABLE node_health_samples ADD COLUMN IF NOT EXISTS memory_total_mb INTEGER DEFAULT 0;"))
        conn.execute(text("ALTER TABLE node_health_samples ADD COLUMN IF NOT EXISTS disk_used_gb DOUBLE PRECISION DEFAULT 0;"))
        conn.execute(text("ALTER TABLE node_health_samples ADD COLUMN IF NOT EXISTS disk_total_gb DOUBLE PRECISION DEFAULT 0;"))
        conn.execute(text("ALTER TABLE node_health_samples ADD COLUMN IF NOT EXISTS disk_free_gb DOUBLE PRECISION DEFAULT 0;"))
        conn.execute(text("ALTER TABLE node_health_samples ADD COLUMN IF NOT EXISTS total_up_bytes BIGINT DEFAULT 0;"))
        conn.execute(text("ALTER TABLE node_health_samples ADD COLUMN IF NOT EXISTS total_down_bytes BIGINT DEFAULT 0;"))
        conn.execute(text("ALTER TABLE node_health_samples ADD COLUMN IF NOT EXISTS total_traffic_bytes BIGINT DEFAULT 0;"))

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
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_promo_usage_tg_code ON promo_usage(tg_id, promo_code);"))

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
        conn.execute(text("ALTER TABLE live_updates ADD COLUMN IF NOT EXISTS channel_username VARCHAR(64);"))
        conn.execute(text("ALTER TABLE live_updates ADD COLUMN IF NOT EXISTS post_id INTEGER;"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_live_updates_active_sort ON live_updates(is_active, sort_order);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_live_updates_channel_post ON live_updates(channel_username, post_id);"))

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
                  name VARCHAR(120) NOT NULL,
                  campaign_type VARCHAR(16) NOT NULL,
                  target_value VARCHAR(64) NOT NULL,
                  segment VARCHAR(32) DEFAULT 'all_active',
                  starts_at TIMESTAMP,
                  ends_at TIMESTAMP,
                  max_activations INTEGER DEFAULT -1,
                  activations_count INTEGER DEFAULT 0,
                  auto_disable BOOLEAN DEFAULT TRUE,
                  is_active BOOLEAN DEFAULT TRUE,
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
        _seed_retention_templates(conn, dialect="postgresql")
        _seed_plan_catalog(conn, dialect="postgresql")

from __future__ import annotations

import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path

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


_POSTGRES_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


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


def _postgres_add_column_if_missing(conn, table: str, column: str, ddl: str) -> bool:
    if _postgres_column_exists(conn, table, column):
        return False
    conn.execute(text(f"ALTER TABLE {_postgres_ident(table)} ADD COLUMN {_postgres_ident(column)} {ddl};"))
    return True


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
                ("is_app_user", "BOOLEAN DEFAULT 0"),
                ("app_install_id", "VARCHAR(128)"),
                ("app_install_secret_hash", "VARCHAR(64)"),
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
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_web_email_identities_email_norm ON web_email_identities(email_norm);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_email_identities_linked_tg_id ON web_email_identities(linked_tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_email_identities_verified ON web_email_identities(is_verified);"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_web_email_tokens_token_hash ON web_email_tokens(token_hash);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_email_tokens_identity_id ON web_email_tokens(identity_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_email_tokens_kind ON web_email_tokens(token_kind);"))

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
                ("network_rx_bytes_total", "BIGINT"),
                ("network_tx_bytes_total", "BIGINT"),
                ("network_rx_mbps", "FLOAT"),
                ("network_tx_mbps", "FLOAT"),
                ("network_total_mbps", "FLOAT"),
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
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_web_email_identities_email_norm ON web_email_identities(email_norm);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_email_identities_linked_tg_id ON web_email_identities(linked_tg_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_email_identities_verified ON web_email_identities(is_verified);"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_web_email_tokens_token_hash ON web_email_tokens(token_hash);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_email_tokens_identity_id ON web_email_tokens(identity_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_web_email_tokens_kind ON web_email_tokens(token_kind);"))

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
        # already accepts the newer POKROV-XXXX-XXXX format without table rebuild.

        # Seed default retention templates for admin editing (idempotent).
        _seed_retention_templates(conn, dialect="sqlite")
        _seed_plan_catalog(conn, dialect="sqlite")


def _run_postgres_migrations(engine: Engine) -> None:
    """
    PostgreSQL-safe idempotent migrations.
    `create_all()` already creates tables; here we only ensure additive columns/indexes.
    """
    with engine.begin() as conn:
        conn.execute(text("SELECT pg_advisory_xact_lock(hashtext('pokrov_schema_migrations'));"))
        code_limit = _postgres_varchar_limit(conn, "gift_cards", "code")
        if code_limit is not None and code_limit < 32:
            conn.execute(text("ALTER TABLE gift_cards ALTER COLUMN code TYPE VARCHAR(32);"))
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
        _postgres_add_column_if_missing(conn, "users", "referral_code", "VARCHAR(10)")
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
        _postgres_add_column_if_missing(conn, "users", "app_install_secret_hash", "VARCHAR(64)")
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
        _postgres_add_column_if_missing(conn, "nodes", "accepting_new_clients", "BOOLEAN DEFAULT TRUE")
        _postgres_add_column_if_missing(conn, "nodes", "is_draining", "BOOLEAN DEFAULT FALSE")
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
        _postgres_add_column_if_missing(conn, "external_orders", "source", "VARCHAR(32)")
        _postgres_add_column_if_missing(conn, "external_orders", "campaign", "VARCHAR(64)")
        _postgres_add_column_if_missing(conn, "external_orders", "promo_code", "VARCHAR(32)")
        _postgres_add_column_if_missing(conn, "external_orders", "meta_json", "TEXT")
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
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pay_attempts_tg_status_started ON pay_attempts(tg_id, status, started_at);"))
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

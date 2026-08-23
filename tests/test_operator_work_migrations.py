from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, text


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

import migrations  # noqa: E402


def _columns(connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(text(f"PRAGMA table_info({table});"))}


def test_operator_work_migration_is_additive_and_idempotent_for_legacy_incidents() -> None:
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE admin_operators (
                  id VARCHAR(36) PRIMARY KEY,
                  legacy_actor_tg_id BIGINT,
                  status VARCHAR(24) NOT NULL
                );
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE service_incidents (
                  id VARCHAR(36) PRIMARY KEY,
                  incident_key VARCHAR(80) NOT NULL,
                  status VARCHAR(24) NOT NULL,
                  started_at DATETIME NOT NULL,
                  created_at DATETIME NOT NULL
                );
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE ops_alerts (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  fingerprint VARCHAR(160) NOT NULL,
                  source VARCHAR(64) NOT NULL,
                  severity VARCHAR(16) NOT NULL,
                  status VARCHAR(24) NOT NULL,
                  title VARCHAR(180) NOT NULL,
                  node_code VARCHAR(32),
                  first_seen_at DATETIME NOT NULL,
                  last_seen_at DATETIME NOT NULL,
                  created_at DATETIME NOT NULL,
                  updated_at DATETIME NOT NULL
                );
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO service_incidents (id, incident_key, status, started_at, created_at)
                VALUES ('11111111-1111-4111-8111-111111111111', 'legacy-incident', 'confirmed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
                """
            )
        )

        migrations._ensure_admin_ops_domain_sqlite(connection)
        migrations._ensure_admin_ops_domain_sqlite(connection)

        assert {
            "environment",
            "workflow_status",
            "workflow_version",
            "owner_operator_id",
            "owner_team",
            "impact",
            "next_update_at",
            "runbook_url",
            "communications_summary",
            "postmortem_status",
            "postmortem_url",
        } <= _columns(connection, "service_incidents")
        assert {"environment", "incident_id", "version"} <= _columns(connection, "ops_alerts")
        assert {
            "operator_tasks",
            "operator_incident_events",
            "operator_incident_links",
        } <= {
            str(row[0])
            for row in connection.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'operator_%';"
                )
            )
        }
        legacy = connection.execute(
            text(
                "SELECT environment, workflow_status, workflow_version, postmortem_status "
                "FROM service_incidents WHERE incident_key='legacy-incident';"
            )
        ).one()
        assert tuple(legacy) == ("production", "investigating", 1, "not_required")


def test_operator_governance_migration_is_additive_and_idempotent() -> None:
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE admin_operator_roles (
                  id VARCHAR(36) PRIMARY KEY,
                  operator_id VARCHAR(36) NOT NULL,
                  role_code VARCHAR(48) NOT NULL,
                  environment_scope VARCHAR(32) NOT NULL,
                  granted_at DATETIME NOT NULL,
                  revoked_at DATETIME
                );
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE admin_operator_audit (
                  id VARCHAR(36) PRIMARY KEY,
                  operator_id VARCHAR(36) NOT NULL,
                  action VARCHAR(96) NOT NULL,
                  result VARCHAR(24) NOT NULL,
                  environment_scope VARCHAR(32) NOT NULL,
                  roles_json TEXT NOT NULL,
                  permissions_json TEXT NOT NULL,
                  created_at DATETIME NOT NULL
                );
                """
            )
        )

        migrations._ensure_operator_governance_sqlite(connection)
        migrations._ensure_operator_governance_sqlite(connection)

        assert {
            "grant_kind",
            "grant_reason",
            "expires_at",
            "review_status",
            "reviewed_by_operator_id",
            "reviewed_at",
            "review_note",
        } <= _columns(connection, "admin_operator_roles")
        assert {
            "resource_type",
            "resource_id",
            "command_intent_id",
            "legacy_audit_id",
            "details_json",
        } <= _columns(connection, "admin_operator_audit")

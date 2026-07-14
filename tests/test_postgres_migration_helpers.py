import sys
import unittest
from pathlib import Path


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class _FakeConn:
    def __init__(self, *, existing_columns=None, varchar_limits=None):
        self.existing_columns = set(existing_columns or [])
        self.varchar_limits = dict(varchar_limits or {})
        self.executed = []

    def execute(self, statement, params=None):
        sql = str(statement)
        self.executed.append((sql, dict(params or {})))
        if "information_schema.columns" in sql and "SELECT EXISTS" in sql:
            key = (params or {}).get("table_name"), (params or {}).get("column_name")
            return _ScalarResult(key in self.existing_columns)
        if "character_maximum_length" in sql:
            key = (params or {}).get("table_name"), (params or {}).get("column_name")
            return _ScalarResult(self.varchar_limits.get(key))
        return _ScalarResult(None)


class PostgresMigrationHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        portal_dir = Path(__file__).resolve().parents[1] / "portal_bot"
        if str(portal_dir) not in sys.path:
            sys.path.insert(0, str(portal_dir))
        import migrations

        cls.migrations = migrations

    def test_existing_column_skips_noop_alter(self) -> None:
        conn = _FakeConn(existing_columns={("users", "referral_code")})

        changed = self.migrations._postgres_add_column_if_missing(conn, "users", "referral_code", "VARCHAR(10)")

        self.assertFalse(changed)
        self.assertEqual(len(conn.executed), 1)
        self.assertNotIn("ALTER TABLE", conn.executed[0][0])

    def test_missing_column_runs_alter_once(self) -> None:
        conn = _FakeConn()

        changed = self.migrations._postgres_add_column_if_missing(conn, "users", "referral_code", "VARCHAR(10)")

        self.assertTrue(changed)
        alter_sql = conn.executed[-1][0]
        self.assertIn("ALTER TABLE users ADD COLUMN referral_code VARCHAR(10)", alter_sql)

    def test_unsafe_identifier_is_rejected(self) -> None:
        conn = _FakeConn()

        with self.assertRaises(ValueError):
            self.migrations._postgres_add_column_if_missing(conn, "users; drop table users", "referral_code", "TEXT")

    def test_support_ownership_migration_declares_additive_columns_and_indexes(self) -> None:
        source = Path(self.migrations.__file__).read_text(encoding="utf-8")

        self.assertIn(
            '_postgres_add_column_if_missing(conn, "support_tickets", "account_id", "VARCHAR(36)")',
            source,
        )
        self.assertIn(
            '_postgres_add_column_if_missing(conn, "support_attachments", "owner_account_id", "VARCHAR(36)")',
            source,
        )
        self.assertIn("ix_support_tickets_account_id", source)
        self.assertIn("ix_support_attachments_owner_account_id", source)

    def test_varchar_limit_reads_information_schema(self) -> None:
        conn = _FakeConn(varchar_limits={("gift_cards", "code"): 16})

        limit = self.migrations._postgres_varchar_limit(conn, "gift_cards", "code")

        self.assertEqual(limit, 16)

    def test_capacity_policy_backfill_sets_not_null_defaults(self) -> None:
        conn = _FakeConn()

        self.migrations._ensure_capacity_domain_postgres(conn)

        backfill_sql = next(
            sql
            for sql, _params in conn.executed
            if "INSERT INTO node_capacity_policy" in sql
        )
        for column in (
            "soft_tx_ratio",
            "drain_tx_ratio",
            "hard_tx_ratio",
            "soft_cpu_percent",
            "hard_cpu_percent",
            "stale_after_seconds",
            "max_packet_loss_percent",
            "max_tcp_retrans_percent",
            "rank_weight",
            "is_enabled",
        ):
            self.assertIn(column, backfill_sql)
        for value in ("0.70", "0.82", "0.92", "75", "90", "180", "2", "5", "100"):
            self.assertIn(value, backfill_sql)

    def test_node_pool_membership_backfill_sets_enabled_default(self) -> None:
        conn = _FakeConn()

        self.migrations._ensure_capacity_domain_postgres(conn)

        backfill_sql = next(
            sql
            for sql, _params in conn.executed
            if "INSERT INTO node_pool_membership" in sql
        )
        self.assertIn("is_enabled", backfill_sql)
        self.assertIn("TRUE", backfill_sql)


if __name__ == "__main__":
    unittest.main()

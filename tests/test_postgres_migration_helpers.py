import sys
import unittest
from pathlib import Path


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value

    def fetchall(self):
        return []

    def fetchone(self):
        return None


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


class _BeginContext:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc, traceback):
        return False


class _FakeEngine:
    def __init__(self):
        self.conn = _FakeConn()

    def begin(self):
        return _BeginContext(self.conn)


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

    def test_ru_probe_postgres_ddl_is_safe_and_dependency_ordered(self) -> None:
        conn = _FakeConn()

        self.migrations._ensure_ru_probe_domain_postgres(conn)

        sql = [" ".join(statement.split()) for statement, _params in conn.executed]
        run_pos = next(i for i, item in enumerate(sql) if "CREATE TABLE IF NOT EXISTS ru_probe_runs" in item)
        target_pos = next(i for i, item in enumerate(sql) if "CREATE TABLE IF NOT EXISTS ru_probe_target_results" in item)
        heartbeat_pos = next(i for i, item in enumerate(sql) if "CREATE TABLE IF NOT EXISTS ru_probe_uploader_heartbeats" in item)
        nonce_pos = next(i for i, item in enumerate(sql) if "CREATE TABLE IF NOT EXISTS internal_ingest_nonces" in item)
        first_index_pos = next(i for i, item in enumerate(sql) if "CREATE INDEX IF NOT EXISTS" in item)

        self.assertLess(run_pos, target_pos)
        self.assertLess(target_pos, heartbeat_pos)
        self.assertLess(heartbeat_pos, nonce_pos)
        self.assertLess(nonce_pos, first_index_pos)

        target_ddl = sql[target_pos]
        self.assertIn("ON DELETE CASCADE", target_ddl)
        self.assertIn("CONSTRAINT uq_ru_probe_target_run_target", target_ddl)
        self.assertIn("overall_status", target_ddl)
        self.assertNotIn(" verdict ", f" {target_ddl.lower()} ")

        nonce_ddl = sql[nonce_pos]
        self.assertIn("nonce_hash VARCHAR(64) NOT NULL", nonce_ddl)
        self.assertIn("request_path VARCHAR(512) NOT NULL", nonce_ddl)
        self.assertIn("body_sha256 VARCHAR(64) NOT NULL", nonce_ddl)
        self.assertNotIn(" nonce VARCHAR", nonce_ddl)
        self.assertNotIn(" signature ", f" {nonce_ddl.lower()} ")
        self.assertNotIn(" secret ", f" {nonce_ddl.lower()} ")

        ru_sql = " ".join(sql[run_pos:])
        self.assertIn("TIMESTAMPTZ", ru_sql)
        self.assertNotIn(" TIMESTAMP ", f" {ru_sql} ")
        for index_name in (
            "ix_ru_probe_runs_finished_at",
            "ix_ru_probe_target_results_overall_status",
            "ix_ru_probe_target_results_node_observed_at",
            "ix_ru_probe_target_results_run_node",
            "ix_ru_probe_uploader_heartbeats_host_observed_at",
            "ix_internal_ingest_nonces_expires_at",
        ):
            self.assertTrue(any(index_name in item for item in sql), index_name)

    def test_postgres_ru_probe_ddl_immediately_follows_admin_ops(self) -> None:
        engine = _FakeEngine()

        self.migrations._run_postgres_migrations(engine)

        sql = [
            " ".join(statement.split())
            for statement, _params in engine.conn.executed
        ]
        admin_last = next(
            i for i, item in enumerate(sql) if "ix_ops_alerts_last_seen_at" in item
        )
        ru_first = next(
            i
            for i, item in enumerate(sql)
            if "CREATE TABLE IF NOT EXISTS ru_probe_runs" in item
        )
        external_orders = next(
            i
            for i, item in enumerate(sql)
            if "CREATE TABLE IF NOT EXISTS external_orders" in item
        )
        self.assertEqual(ru_first, admin_last + 1)
        self.assertLess(ru_first, external_orders)


if __name__ == "__main__":
    unittest.main()

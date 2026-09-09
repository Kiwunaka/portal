import importlib
import os
import sqlite3
import sys
import tempfile
import unittest
import uuid
from contextlib import closing
from pathlib import Path


class NodeObservabilitySchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str((Path(self._tmp.name) / f"portal_api_test_{uuid.uuid4().hex}.db").resolve())
        self._saved_env = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(self.db_path).as_posix()}"

        for module_name in ("db", "models", "migrations", "config"):
            sys.modules.pop(module_name, None)

        self.db = importlib.import_module("db")
        self.db.init_db()

    def tearDown(self) -> None:
        try:
            self.db.engine.dispose()
        except Exception:
            pass
        if self._saved_env is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self._saved_env
        try:
            Path(self.db_path).unlink(missing_ok=True)
        except PermissionError:
            pass

    def _columns(self, table_name: str) -> set[str]:
        with closing(sqlite3.connect(self.db_path)) as conn:
            rows = conn.execute(f"PRAGMA table_info({table_name});").fetchall()
        return {str(row[1]) for row in rows}

    def test_nodes_table_has_probe_observability_columns(self) -> None:
        cols = self._columns("nodes")
        self.assertTrue(
            {
                "last_probe_at",
                "last_probe_stage",
                "last_probe_error_kind",
                "last_probe_error_message",
                "hoster_family",
                "hoster_asn",
                "hoster_subnet",
                "ipv4_health",
                "ipv6_health",
                "last_probe_classification",
                "transport_health_json",
                "edge_reachability_ok",
                "authenticated_egress_ok",
                "last_authenticated_egress_at",
                "authenticated_egress_error_kind",
            }.issubset(cols)
        )

    def test_node_runtime_metrics_separates_edge_and_authenticated_egress(self) -> None:
        cols = self._columns("node_runtime_metrics")
        self.assertTrue({"edge_reachability_ok", "authenticated_egress_ok"}.issubset(cols))

    def test_node_health_samples_table_has_probe_observability_columns(self) -> None:
        cols = self._columns("node_health_samples")
        self.assertTrue(
            {
                "probe_at",
                "probe_stage",
                "probe_error_kind",
                "probe_error_message",
                "probe_classification",
                "ipv4_health",
                "ipv6_health",
                "transport_health_json",
            }.issubset(cols)
        )

    def test_latest_health_samples_index_survives_legacy_migration(self) -> None:
        index_name = "ix_node_health_samples_node_sampled_id"

        def columns():
            with closing(sqlite3.connect(self.db_path)) as conn:
                return [row[2] for row in conn.execute(f"PRAGMA index_info({index_name});")]

        self.assertEqual(columns(), ["node_code", "sampled_at", "id"])
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(f"DROP INDEX {index_name};")
        migrations = importlib.import_module("migrations")
        migrations.run_migrations(self.db.engine)
        migrations.run_migrations(self.db.engine)
        self.assertEqual(columns(), ["node_code", "sampled_at", "id"])


if __name__ == "__main__":
    unittest.main()

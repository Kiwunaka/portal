import importlib
import os
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


class RetentionTemplateSeedTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._saved_env: dict[str, str | None] = {}
        for key in ("DATABASE_URL", "BOT_TOKEN"):
            self._saved_env[key] = os.environ.get(key)

        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = (repo_root / f"portal_api_test_{uuid.uuid4().hex}.db").resolve()
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path.as_posix()}"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"

        for mod_name in ("config", "db", "migrations"):
            if mod_name in sys.modules:
                importlib.reload(sys.modules[mod_name])

        self.db = importlib.import_module("db")
        importlib.reload(self.db)
        self.migrations = importlib.import_module("migrations")
        importlib.reload(self.migrations)

    def tearDown(self) -> None:
        try:
            self.db.engine.dispose()
        except Exception:
            pass
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        try:
            self.db_path.unlink(missing_ok=True)
        except Exception:
            pass
        self._tmp.cleanup()

    def test_init_db_seeds_retention_templates_idempotently(self) -> None:
        from models import Template

        self.db.init_db()
        self.db.init_db()

        s = self.db.SessionLocal()
        try:
            keys = sorted([str(k) for k in self.migrations.RETENTION_TEMPLATE_PRESETS.keys()])
            rows = s.query(Template).filter(Template.key.in_(keys)).all()
            self.assertEqual(len(rows), len(keys))
            self.assertEqual(len({str(r.key) for r in rows}), len(keys))
        finally:
            s.close()

    def test_run_migrations_refreshes_existing_retention_template_text(self) -> None:
        from models import Template

        self.db.init_db()
        s = self.db.SessionLocal()
        try:
            row = s.query(Template).filter(Template.key == "retention_t1_a").first()
            self.assertIsNotNone(row)
            row.text = "stale copy"
            s.commit()
        finally:
            s.close()

        self.migrations.run_migrations(self.db.engine)

        s = self.db.SessionLocal()
        try:
            row = s.query(Template).filter(Template.key == "retention_t1_a").first()
            self.assertIsNotNone(row)
            self.assertEqual(str(row.text), str(self.migrations.RETENTION_TEMPLATE_PRESETS["retention_t1_a"]))
        finally:
            s.close()

    def test_run_migrations_adds_live_updates_and_start_links_schema(self) -> None:
        self.db.init_db()
        self.migrations.run_migrations(self.db.engine)

        with self.db.engine.begin() as conn:
            live_cols = conn.execute(self.migrations.text("PRAGMA table_info(live_updates);")).fetchall()
            names = {str(r[1]) for r in live_cols}
            self.assertIn("channel_username", names)
            self.assertIn("post_id", names)

            start_link_table = conn.execute(
                self.migrations.text("SELECT name FROM sqlite_master WHERE type='table' AND name='start_links';")
            ).fetchone()
            app_settings_table = conn.execute(
                self.migrations.text("SELECT name FROM sqlite_master WHERE type='table' AND name='app_settings';")
            ).fetchone()
            self.assertIsNotNone(start_link_table)
            self.assertIsNotNone(app_settings_table)

    def test_run_migrations_adds_node_probe_columns(self) -> None:
        self.db.init_db()
        self.migrations.run_migrations(self.db.engine)

        with self.db.engine.begin() as conn:
            node_cols = conn.execute(self.migrations.text("PRAGMA table_info(nodes);")).fetchall()
            node_names = {str(r[1]) for r in node_cols}
            self.assertIn("last_probe_at", node_names)
            self.assertIn("last_probe_stage", node_names)
            self.assertIn("last_probe_error_kind", node_names)
            self.assertIn("last_probe_error_message", node_names)

            sample_cols = conn.execute(self.migrations.text("PRAGMA table_info(node_health_samples);")).fetchall()
            sample_names = {str(r[1]) for r in sample_cols}
            self.assertIn("probe_stage", sample_names)
            self.assertIn("probe_error_kind", sample_names)
            self.assertIn("probe_error_message", sample_names)


if __name__ == "__main__":
    unittest.main()

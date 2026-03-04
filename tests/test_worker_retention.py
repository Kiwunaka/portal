import importlib
import os
import sys
import tempfile
import unittest
import uuid
from datetime import timedelta
from pathlib import Path


class WorkerRetentionTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._saved_env: dict[str, str | None] = {}
        for key in ("DATABASE_URL", "BOT_TOKEN", "PUBLIC_CHANNEL"):
            self._saved_env[key] = os.environ.get(key)

        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = (repo_root / f"portal_api_test_{uuid.uuid4().hex}.db").resolve()
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path.as_posix()}"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"
        os.environ["PUBLIC_CHANNEL"] = "portal_privacy"

        for mod_name in ("config", "db", "worker"):
            if mod_name in sys.modules:
                importlib.reload(sys.modules[mod_name])

        self.db = importlib.import_module("db")
        importlib.reload(self.db)
        self.db.init_db()

        self.worker = importlib.import_module("worker")
        importlib.reload(self.worker)
        self.worker._TEMPLATE_CACHE.clear()

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

    def test_expiry_stage_windows(self) -> None:
        self.assertEqual(self.worker._expiry_stage(timedelta(days=2, hours=12)), "t3")
        self.assertEqual(self.worker._expiry_stage(timedelta(hours=23)), "t1")
        self.assertEqual(self.worker._expiry_stage(timedelta(minutes=30)), "t0")
        self.assertEqual(self.worker._expiry_stage(timedelta(days=5)), "")

    def test_ab_variant_is_stable(self) -> None:
        v1 = self.worker._ab_variant_for_user(tg_id=1001, flow_key="expiry_t3")
        v2 = self.worker._ab_variant_for_user(tg_id=1001, flow_key="expiry_t3")
        self.assertEqual(v1, v2)
        self.assertIn(v1, {"a", "b"})

    def test_retention_text_uses_template_override(self) -> None:
        from models import Template

        s = self.db.SessionLocal()
        try:
            row = s.query(Template).filter(Template.key == "retention_t1_a").first()
            if row is None:
                row = Template(key="retention_t1_a", text="Custom T-1 message until {expiry_date}")
                s.add(row)
            else:
                row.text = "Custom T-1 message until {expiry_date}"
            s.commit()
        finally:
            s.close()

        self.worker._TEMPLATE_CACHE.clear()
        text = self.worker._retention_text(flow="t1", variant="a", context={"expiry_date": "2026-02-20"})
        self.assertIn("Custom T-1 message", text)
        self.assertIn("2026-02-20", text)

    def test_retention_buttons_include_channel_for_welcome(self) -> None:
        buttons = self.worker._retention_buttons(flow="welcome", variant="a")
        self.assertGreaterEqual(len(buttons), 2)
        self.assertIn("t.me/portal_privacy", str(buttons[1][0].get("url") or ""))

    def test_channel_membership_reason_normalization(self) -> None:
        self.assertEqual(self.worker._normalize_channel_membership_reason("left"), "not_member")
        self.assertEqual(self.worker._normalize_channel_membership_reason("kicked"), "not_member")
        self.assertEqual(self.worker._normalize_channel_membership_reason("not_member"), "not_member")
        self.assertEqual(self.worker._normalize_channel_membership_reason("telegram_http_error"), "telegram_http_error")


if __name__ == "__main__":
    unittest.main()

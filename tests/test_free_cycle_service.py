import importlib
import os
import sys
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta
from pathlib import Path


class FreeCycleServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = str((repo_root / f"portal_free_cycle_test_{uuid.uuid4().hex}.db").resolve())
        self._saved_env: dict[str, str | None] = {}
        for k in ("DATABASE_URL", "BOT_TOKEN", "FREE_CYCLE_DAYS"):
            self._saved_env[k] = os.environ.get(k)

        os.environ["DATABASE_URL"] = f"sqlite:///{Path(self.db_path).as_posix()}"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"
        os.environ["FREE_CYCLE_DAYS"] = "30"

        for module_name in ("config", "db", "models", "migrations", "free_cycle_service"):
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])

        from db import init_db

        init_db()

        import free_cycle_service as fcs

        self.fcs = fcs

    def tearDown(self) -> None:
        try:
            from db import engine

            engine.dispose()
        except Exception:
            pass

        for k, v in self._saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

        try:
            Path(self.db_path).unlink(missing_ok=True)
        except Exception:
            pass
        self._tmp.cleanup()

    def _seed_user(self, *, tg_id: int, due: bool, with_cycle: bool) -> None:
        from db import SessionLocal
        from models import User

        now = datetime.utcnow()
        s = SessionLocal()
        try:
            row = User(
                tg_id=int(tg_id),
                username=f"u{tg_id}",
                uuid=str(uuid.uuid4()),
                email=f"User_{tg_id}",
                sub_type="FREE",
                created_at=now - timedelta(days=10),
                expiry_at=now + timedelta(days=300),
                is_active=True,
                stars_paid=0,
                total_gb=0,
                trial_used=False,
                tos_accepted=True,
                sub_token=f"token_{tg_id}",
            )
            if with_cycle:
                anchor = now - timedelta(days=60)
                row.free_cycle_anchor_at = anchor
                row.free_cycle_last_reset_at = anchor + timedelta(days=30)
                row.free_cycle_next_reset_at = (now - timedelta(minutes=5)) if due else (now + timedelta(days=5))
            s.add(row)
            s.commit()
        finally:
            s.close()

    async def test_process_due_free_cycle_resets(self) -> None:
        from db import SessionLocal
        from models import User

        self._seed_user(tg_id=1001, due=True, with_cycle=True)
        self._seed_user(tg_id=1002, due=False, with_cycle=True)

        class FakePanel:
            async def login(self):
                return True

            async def close(self):
                return True

            async def reset_client_traffic(self, tg_id: int, *, only_free: bool = False):
                return int(tg_id) == 1001 and bool(only_free)

        old_panel = self.fcs.ControlPanel
        self.fcs.ControlPanel = FakePanel
        try:
            result = await self.fcs.process_due_free_cycle_resets(max_users=20)
        finally:
            self.fcs.ControlPanel = old_panel

        self.assertTrue(result.get("ok"))
        self.assertEqual(int(result.get("due") or 0), 1)
        self.assertEqual(int(result.get("reset_ok") or 0), 1)
        self.assertEqual(int(result.get("reset_failed") or 0), 0)

        s = SessionLocal()
        try:
            u = s.query(User).filter(User.tg_id == 1001).first()
            self.assertIsNotNone(u)
            self.assertIsNotNone(u.free_cycle_last_reset_at)
            self.assertIsNotNone(u.free_cycle_next_reset_at)
            self.assertGreater(u.free_cycle_next_reset_at, datetime.utcnow())
        finally:
            s.close()

    def test_bootstrap_existing_free_users(self) -> None:
        from db import SessionLocal
        from models import User

        self._seed_user(tg_id=2001, due=False, with_cycle=False)
        ts = datetime.utcnow()
        result = self.fcs.bootstrap_free_cycle_for_existing_users(now=ts)
        self.assertEqual(int(result.get("initialized") or 0), 1)

        s = SessionLocal()
        try:
            u = s.query(User).filter(User.tg_id == 2001).first()
            self.assertIsNotNone(u)
            self.assertIsNotNone(u.free_cycle_anchor_at)
            self.assertIsNotNone(u.free_cycle_last_reset_at)
            self.assertIsNotNone(u.free_cycle_next_reset_at)
        finally:
            s.close()


if __name__ == "__main__":
    unittest.main()

import importlib
import os
import sys
import tempfile
import unittest
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from fastapi.testclient import TestClient


def _sign_telegram_init_data(*, bot_token: str, params: dict) -> str:
    import hashlib
    import hmac

    items = sorted((k, v) for k, v in params.items())
    data_check_string = "\n".join([f"{k}={v}" for k, v in items])
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    check_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    params2 = dict(params)
    params2["hash"] = check_hash
    return urlencode(params2)


class ApiAuthAndTicketsTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = str((repo_root / f"portal_api_test_{uuid.uuid4().hex}.db").resolve())
        db_uri_path = Path(self.db_path).as_posix()
        self.bot_token = "test_bot_token_123"
        self._saved_env: dict[str, str | None] = {}
        for k in ("DATABASE_URL", "BOT_TOKEN", "ADMIN_ID", "BOT_USERNAME", "SUPPORT_USERNAME", "PUBLIC_CHANNEL", "CHANNEL_PREMIUM_DAYS"):
            self._saved_env[k] = os.environ.get(k)

        os.environ["DATABASE_URL"] = f"sqlite:///{db_uri_path}"
        os.environ["BOT_TOKEN"] = self.bot_token
        os.environ["ADMIN_ID"] = "9999"
        os.environ["BOT_USERNAME"] = "portal_service_bot"
        os.environ["SUPPORT_USERNAME"] = "portal_privacy_helpbot"
        os.environ["PUBLIC_CHANNEL"] = "portal_privacy"
        os.environ["CHANNEL_PREMIUM_DAYS"] = "10"

        if "config" in sys.modules:
            importlib.reload(sys.modules["config"])
        if "db" in sys.modules:
            importlib.reload(sys.modules["db"])
        if "api" in sys.modules:
            importlib.reload(sys.modules["api"])
        self.api = importlib.import_module("api")
        importlib.reload(self.api)
        self.client = TestClient(self.api.app)

        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=1001,
                    username="alice",
                    uuid=str(uuid.uuid4()),
                    email="user_1001",
                    sub_type="FREE",
                    is_active=True,
                )
            )
            s.commit()
        finally:
            s.close()

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

    def _init_data(self, tg_id: int, username: str) -> str:
        return _sign_telegram_init_data(
            bot_token=self.bot_token,
            params={
                "auth_date": "1700000000",
                "query_id": "AAEAAAE",
                "user": f'{{"id":{tg_id},"first_name":"Test","username":"{username}"}}',
            },
        )

    def test_admin_endpoint_requires_admin_guard(self) -> None:
        hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        r = self.client.get("/api/admin/summary", headers=hdrs)
        self.assertEqual(r.status_code, 403)

    def test_ticket_lifecycle_with_media_metadata(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        create = self.client.post(
            "/api/tickets",
            headers=user_hdrs,
            json={
                "subject": "Проблема входа",
                "body": "Не подключается из приложения",
                "media_type": "photo",
                "media_file_id": "file_123",
                "media_payload": '{"w":100,"h":200}',
            },
        )
        self.assertEqual(create.status_code, 200, create.text)
        ticket = create.json()["ticket"]
        self.assertEqual(ticket["status"], "open")
        self.assertEqual(ticket["messages"][0]["media_type"], "photo")
        ticket_id = ticket["id"]

        reply = self.client.post(
            f"/api/admin/tickets/{ticket_id}/reply",
            headers=admin_hdrs,
            json={"body": "Проверили, уже исправлено"},
        )
        self.assertEqual(reply.status_code, 200, reply.text)
        self.assertEqual(reply.json()["ticket"]["status"], "in_progress")

    def test_channel_bonus_claim_upgrades_free_to_paid(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

        async def fake_is_member(channel_username: str, tg_id: int):
            return True, "member"

        async def fake_sync(_user):
            return True

        self.api._is_channel_member = fake_is_member
        self.api._sync_user_after_paid_bonus = fake_sync

        r = self.client.post("/api/bonuses/channel/claim", headers=user_hdrs)
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body["ok"])
        self.assertFalse(body["already_claimed"])
        self.assertEqual(body["premium_days"], 10)
        self.assertEqual(body["sub_type"], "PAID")

        # Second claim should be idempotent.
        r2 = self.client.post("/api/bonuses/channel/claim", headers=user_hdrs)
        self.assertEqual(r2.status_code, 200, r2.text)
        self.assertTrue(r2.json()["already_claimed"])

    def test_channel_bonus_claim_requires_membership(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

        async def fake_not_member(channel_username: str, tg_id: int):
            return False, "not_member"

        self.api._is_channel_member = fake_not_member

        r = self.client.post("/api/bonuses/channel/claim", headers=user_hdrs)
        self.assertEqual(r.status_code, 400, r.text)

    def test_nodes_diagnostics_rate_limit(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        r1 = self.client.post("/api/nodes/diagnostics/run", headers=user_hdrs)
        self.assertEqual(r1.status_code, 200, r1.text)
        r2 = self.client.post("/api/nodes/diagnostics/run", headers=user_hdrs)
        self.assertEqual(r2.status_code, 429, r2.text)

    def test_admin_manual_user_crud_flow(self) -> None:
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        class FakePanel:
            async def login(self):
                return True

            async def close(self):
                return True

            async def ensure_user_on_all_nodes(self, **kwargs):
                return {"pl": True, "de": True}

            async def enable_client(self, user_uuid: str, enable: bool = True):
                return True

        self.api.ControlPanel = FakePanel

        created = self.client.post(
            "/api/admin/users/manual",
            headers=admin_hdrs,
            json={"display_name": "Offline Client", "days": 30},
        )
        self.assertEqual(created.status_code, 200, created.text)
        body = created.json()
        self.assertTrue(body["ok"])
        self.assertTrue(body["sync_ok"])
        self.assertIn("/s8Kx2mP7qR4wT/", body["user"]["subscription_url"])
        manual_tg_id = int(body["user"]["tg_id"])
        self.assertLess(manual_tg_id, 0)

        extend = self.client.post(
            f"/api/admin/users/{manual_tg_id}/manual/extend",
            headers=admin_hdrs,
            json={"days": 7},
        )
        self.assertEqual(extend.status_code, 200, extend.text)
        self.assertTrue(extend.json()["ok"])
        self.assertIsInstance(datetime.fromisoformat(extend.json()["expiry_at"]), datetime)

        block = self.client.post(
            f"/api/admin/users/{manual_tg_id}/manual/block",
            headers=admin_hdrs,
            json={"blocked": True},
        )
        self.assertEqual(block.status_code, 200, block.text)
        self.assertTrue(block.json()["ok"])
        self.assertFalse(block.json()["is_active"])

        regen = self.client.post(
            f"/api/admin/users/{manual_tg_id}/manual/regenerate-token",
            headers=admin_hdrs,
            json={},
        )
        self.assertEqual(regen.status_code, 200, regen.text)
        self.assertTrue(regen.json()["ok"])
        self.assertIn("/s8Kx2mP7qR4wT/", regen.json()["subscription_url"])


if __name__ == "__main__":
    unittest.main()

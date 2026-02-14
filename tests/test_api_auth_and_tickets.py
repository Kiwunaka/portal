import importlib
import os
import sys
import tempfile
import unittest
import uuid
import time
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
        for k in (
            "DATABASE_URL",
            "BOT_TOKEN",
            "ADMIN_ID",
            "WEBAPP_SESSION_SECRET",
            "BOT_USERNAME",
            "SUPPORT_USERNAME",
            "PUBLIC_CHANNEL",
            "CHANNEL_PREMIUM_DAYS",
            "OPENING_PREMIUM_DAYS",
            "OPENING_PREMIUM_CAMPAIGN_KEY",
        ):
            self._saved_env[k] = os.environ.get(k)

        os.environ["DATABASE_URL"] = f"sqlite:///{db_uri_path}"
        os.environ["BOT_TOKEN"] = self.bot_token
        os.environ["ADMIN_ID"] = "9999"
        os.environ["WEBAPP_SESSION_SECRET"] = "test_webapp_secret_123"
        os.environ["BOT_USERNAME"] = "portal_service_bot"
        os.environ["SUPPORT_USERNAME"] = "portal_privacy_helpbot"
        os.environ["PUBLIC_CHANNEL"] = "portal_privacy"
        os.environ["CHANNEL_PREMIUM_DAYS"] = "10"
        os.environ["OPENING_PREMIUM_DAYS"] = "14"
        os.environ["OPENING_PREMIUM_CAMPAIGN_KEY"] = "opening_premium_14d"

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
                    tos_accepted=True,
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

    def _telegram_login_payload(self, tg_id: int, username: str) -> dict:
        import hashlib
        import hmac

        payload = {
            "id": int(tg_id),
            "first_name": "Test",
            "username": username,
            "auth_date": int(time.time()),
        }
        data_check = "\n".join([f"{k}={payload[k]}" for k in sorted(payload.keys())])
        secret_key = hashlib.sha256(self.bot_token.encode("utf-8")).digest()
        payload["hash"] = hmac.new(secret_key, data_check.encode("utf-8"), hashlib.sha256).hexdigest()
        return payload

    def test_admin_endpoint_requires_admin_guard(self) -> None:
        hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        r = self.client.get("/api/admin/summary", headers=hdrs)
        self.assertEqual(r.status_code, 403)

    def test_web_login_session_flow(self) -> None:
        payload = self._telegram_login_payload(1001, "alice")
        login = self.client.post("/api/auth/telegram/web-login", json=payload)
        self.assertEqual(login.status_code, 200, login.text)
        token = str(login.json().get("token") or "")
        self.assertTrue(token)

        hdrs = {"Authorization": f"Bearer {token}"}
        session = self.client.get("/api/auth/session", headers=hdrs)
        self.assertEqual(session.status_code, 200, session.text)
        self.assertEqual(int(session.json().get("user", {}).get("id", 0)), 1001)

        dash = self.client.get("/api/dashboard", headers=hdrs)
        self.assertEqual(dash.status_code, 200, dash.text)

    def test_web_login_rejects_invalid_signature(self) -> None:
        bad = {
            "id": 1001,
            "first_name": "Test",
            "username": "alice",
            "auth_date": int(time.time()),
            "hash": "bad_signature",
        }
        r = self.client.post("/api/auth/telegram/web-login", json=bad)
        self.assertEqual(r.status_code, 401, r.text)

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

    def test_channel_bonus_claim_requires_tos(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            u = s.query(User).filter_by(tg_id=1001).first()
            assert u is not None
            u.tos_accepted = False
            s.commit()
        finally:
            s.close()

        r = self.client.post("/api/bonuses/channel/claim", headers=user_hdrs)
        self.assertEqual(r.status_code, 400, r.text)
        self.assertIn("оферту", r.text.lower())

    def test_channel_bonus_claim_blocked_by_opening_promo_claim(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        from db import SessionLocal
        from models import CampaignSend

        s = SessionLocal()
        try:
            s.add(CampaignSend(tg_id=1001, campaign_key="opening_premium_14d"))
            s.commit()
        finally:
            s.close()

        r = self.client.post("/api/bonuses/channel/claim", headers=user_hdrs)
        self.assertEqual(r.status_code, 400, r.text)
        self.assertIn("промо-бонус", r.text.lower())

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

    def test_admin_promos_templates_and_gift_codes_crud(self) -> None:
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

        created_promo = self.client.post(
            "/api/admin/promos",
            headers=admin_hdrs,
            json={"code": "WELCOME14", "promo_type": "days", "value": 14, "uses_left": 100},
        )
        self.assertEqual(created_promo.status_code, 200, created_promo.text)

        promo_list = self.client.get("/api/admin/promos?limit=20", headers=admin_hdrs)
        self.assertEqual(promo_list.status_code, 200, promo_list.text)
        self.assertTrue(any((p.get("code") or "") == "WELCOME14" for p in promo_list.json().get("promos", [])))

        updated_promo = self.client.patch(
            "/api/admin/promos/WELCOME14",
            headers=admin_hdrs,
            json={"value": 21, "uses_left": 50},
        )
        self.assertEqual(updated_promo.status_code, 200, updated_promo.text)

        deleted_promo = self.client.delete("/api/admin/promos/WELCOME14", headers=admin_hdrs)
        self.assertEqual(deleted_promo.status_code, 200, deleted_promo.text)

        created_tpl = self.client.post(
            "/api/admin/templates",
            headers=admin_hdrs,
            json={"key": "retention_t3", "text": "Подписка скоро завершится. Продлите доступ."},
        )
        self.assertEqual(created_tpl.status_code, 200, created_tpl.text)

        tpl_list = self.client.get("/api/admin/templates?limit=20", headers=admin_hdrs)
        self.assertEqual(tpl_list.status_code, 200, tpl_list.text)
        self.assertTrue(any((t.get("key") or "") == "retention_t3" for t in tpl_list.json().get("templates", [])))

        updated_tpl = self.client.patch(
            "/api/admin/templates/retention_t3",
            headers=admin_hdrs,
            json={"text": "Напоминаем: продлите доступ, чтобы не было паузы."},
        )
        self.assertEqual(updated_tpl.status_code, 200, updated_tpl.text)

        deleted_tpl = self.client.delete("/api/admin/templates/retention_t3", headers=admin_hdrs)
        self.assertEqual(deleted_tpl.status_code, 200, deleted_tpl.text)

        gift_created = self.client.post(
            "/api/admin/gift-codes",
            headers=admin_hdrs,
            json={"card_type": "standard"},
        )
        self.assertEqual(gift_created.status_code, 200, gift_created.text)
        code = gift_created.json().get("gift_code", {}).get("code")
        self.assertTrue(code)

        gift_list = self.client.get("/api/admin/gift-codes?limit=20", headers=admin_hdrs)
        self.assertEqual(gift_list.status_code, 200, gift_list.text)
        self.assertTrue(any((g.get("code") or "") == code for g in gift_list.json().get("gift_codes", [])))

        redeemed = self.client.post("/api/gift/redeem", headers=user_hdrs, json={"code": code})
        self.assertEqual(redeemed.status_code, 200, redeemed.text)
        self.assertTrue(redeemed.json().get("ok"))
        self.assertEqual(str(redeemed.json().get("card_type") or ""), "standard")

        redeemed_twice = self.client.post("/api/gift/redeem", headers=user_hdrs, json={"code": code})
        self.assertEqual(redeemed_twice.status_code, 400, redeemed_twice.text)


if __name__ == "__main__":
    unittest.main()

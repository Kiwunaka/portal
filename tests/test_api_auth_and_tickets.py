import importlib
import json
import os
import sys
import tempfile
import unittest
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch
from urllib.parse import urlencode

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError


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
            "SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED",
            "SUPPORT_UPLOAD_DIR",
        ):
            self._saved_env[k] = os.environ.get(k)

        os.environ["DATABASE_URL"] = f"sqlite:///{db_uri_path}"
        os.environ["BOT_TOKEN"] = self.bot_token
        os.environ["ADMIN_ID"] = "9999"
        os.environ["WEBAPP_SESSION_SECRET"] = "test_webapp_secret_123"
        os.environ["BOT_USERNAME"] = "net4ebur_bot"
        os.environ["SUPPORT_USERNAME"] = "portal_privacy_helpbot"
        os.environ["PUBLIC_CHANNEL"] = "portal_privacy"
        os.environ["CHANNEL_PREMIUM_DAYS"] = "10"
        os.environ["OPENING_PREMIUM_DAYS"] = "14"
        os.environ["OPENING_PREMIUM_CAMPAIGN_KEY"] = "opening_premium_14d"
        os.environ["SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED"] = "true"
        os.environ["SUPPORT_UPLOAD_DIR"] = str((Path(self._tmp.name) / "support_uploads").resolve())

        if "config" in sys.modules:
            importlib.reload(sys.modules["config"])
        if "db" in sys.modules:
            importlib.reload(sys.modules["db"])
        if "offers_service" in sys.modules:
            importlib.reload(sys.modules["offers_service"])
        if "points_service" in sys.modules:
            importlib.reload(sys.modules["points_service"])
        if "gift_cards_service" in sys.modules:
            importlib.reload(sys.modules["gift_cards_service"])
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

    def _event_rows(self, event_name: str) -> list[dict]:
        from db import SessionLocal
        from models import Event

        s = SessionLocal()
        try:
            rows = s.query(Event).filter(Event.event_name == event_name).order_by(Event.id.asc()).all()
            out: list[dict] = []
            for row in rows:
                meta = {}
                if getattr(row, "meta_json", None):
                    meta = json.loads(str(row.meta_json))
                out.append({"tg_id": int(row.tg_id or 0), "source": str(row.source or ""), "meta": meta})
            return out
        finally:
            s.close()

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

    def test_ticket_upload_returns_attachment_metadata_and_serves_file(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

        uploaded = self.client.post(
            "/api/tickets/uploads",
            headers={**user_hdrs, "Content-Type": "image/png", "X-Upload-Filename": "screen.png"},
            content=b"\x89PNG\r\n\x1a\nbinary-test",
        )
        self.assertEqual(uploaded.status_code, 200, uploaded.text)
        body = uploaded.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["attachment"]["media_type"], "image")
        media_file_id = str(body["attachment"]["media_file_id"] or "")
        self.assertIn("/", media_file_id)

        payload = body["attachment_payload"]
        self.assertEqual(payload["name"], "screen.png")
        self.assertEqual(payload["content_type"], "image/png")
        self.assertGreaterEqual(int(payload["size"] or 0), 8)

        file_url = str(payload["url"] or "")
        self.assertTrue(file_url.startswith("/uploads/support/"))

        fetched = self.client.get(file_url)
        self.assertEqual(fetched.status_code, 200, fetched.text)
        self.assertEqual(fetched.headers.get("content-type"), "image/png")
        self.assertEqual(fetched.content, b"\x89PNG\r\n\x1a\nbinary-test")

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
        self.assertEqual(body["sub_type"], "BONUS")
        self.assertTrue(body["sync_ok"])
        activated_events = self._event_rows("promo_channel_activated")
        self.assertEqual(len(activated_events), 1)
        self.assertEqual(activated_events[0]["source"], "webapp")
        self.assertEqual(int(activated_events[0]["meta"].get("days") or 0), 10)
        self.assertTrue(bool(activated_events[0]["meta"].get("sync_ok")))

        # Second claim should be idempotent.
        r2 = self.client.post("/api/bonuses/channel/claim", headers=user_hdrs)
        self.assertEqual(r2.status_code, 200, r2.text)
        self.assertTrue(r2.json()["already_claimed"])
        repeat_events = self._event_rows("promo_channel_already_claimed")
        self.assertEqual(len(repeat_events), 1)
        self.assertEqual(repeat_events[0]["source"], "webapp")

    def test_channel_bonus_claim_does_not_persist_points_when_outer_commit_fails(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        from db import SessionLocal
        from models import PointsLedger, User

        async def fake_is_member(channel_username: str, tg_id: int):
            return True, "member"

        self.api._is_channel_member = fake_is_member

        class _FailingCommitSession:
            def __init__(self, inner):
                self._inner = inner

            def commit(self):
                raise RuntimeError("forced outer commit failure")

            def __getattr__(self, name):
                return getattr(self._inner, name)

        def _failing_session_factory():
            return _FailingCommitSession(SessionLocal())

        with patch.object(self.api, "SessionLocal", new=_failing_session_factory):
            with self.assertRaises(RuntimeError):
                self.client.post("/api/bonuses/channel/claim", headers=user_hdrs)

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            self.assertIsNotNone(user)
            self.assertEqual((user.sub_type or "").upper(), "FREE")
            self.assertIsNone(getattr(user, "channel_bonus_claimed_at", None))

            rows = (
                s.query(PointsLedger)
                .filter(PointsLedger.tg_id == 1001)
                .filter(PointsLedger.reason == "channel_subscribe_bonus")
                .all()
            )
            self.assertEqual(rows, [])
        finally:
            s.close()

    def test_channel_bonus_claim_requires_membership(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

        async def fake_not_member(channel_username: str, tg_id: int):
            return False, "not_member"

        self.api._is_channel_member = fake_not_member

        r = self.client.post("/api/bonuses/channel/claim", headers=user_hdrs)
        self.assertEqual(r.status_code, 400, r.text)

    def test_channel_bonus_claim_treats_left_as_not_member(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

        async def fake_left(channel_username: str, tg_id: int):
            return False, "left"

        self.api._is_channel_member = fake_left

        r = self.client.post("/api/bonuses/channel/claim", headers=user_hdrs)
        self.assertEqual(r.status_code, 400, r.text)
        self.assertIn("подпишитесь", r.text.lower())
        denied = self._event_rows("promo_channel_denied")
        self.assertEqual(len(denied), 1)
        self.assertEqual(str(denied[0]["meta"].get("reason") or ""), "not_member")

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
            json={"delta_days": 7},
        )
        self.assertEqual(extend.status_code, 200, extend.text)
        self.assertTrue(extend.json()["ok"])
        self.assertEqual(int(extend.json().get("delta_days") or 0), 7)
        self.assertIsInstance(datetime.fromisoformat(extend.json()["expiry_at"]), datetime)

        alias_extend = self.client.post(
            f"/api/admin/users/{manual_tg_id}/manual-extend",
            headers=admin_hdrs,
            json={"delta_days": 1},
        )
        self.assertEqual(alias_extend.status_code, 200, alias_extend.text)
        self.assertEqual(int(alias_extend.json().get("delta_days") or 0), 1)

        backwards_compat = self.client.post(
            f"/api/admin/users/{manual_tg_id}/manual/extend",
            headers=admin_hdrs,
            json={"days": 3},
        )
        self.assertEqual(backwards_compat.status_code, 200, backwards_compat.text)
        self.assertEqual(int(backwards_compat.json().get("delta_days") or 0), 3)

        reject_negative = self.client.post(
            f"/api/admin/users/{manual_tg_id}/manual/extend",
            headers=admin_hdrs,
            json={"delta_days": -3650},
        )
        self.assertEqual(reject_negative.status_code, 400, reject_negative.text)

        allow_negative = self.client.post(
            f"/api/admin/users/{manual_tg_id}/manual/extend",
            headers=admin_hdrs,
            json={"delta_days": -3650, "allow_deactivate": True},
        )
        self.assertEqual(allow_negative.status_code, 200, allow_negative.text)
        self.assertFalse(bool(allow_negative.json().get("is_active")))

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
        self.assertTrue(bool(regen.json().get("sync_ok")))
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

    def test_admin_loyalty_grant_syncs_panel_and_returns_sync_flag(self) -> None:
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            self.assertIsNotNone(user)
            user.created_at = datetime.utcnow() - timedelta(days=45)
            s.commit()
        finally:
            s.close()

        cfg = self.client.put(
            "/api/admin/loyalty-config",
            headers=admin_hdrs,
            json={"enabled": True, "tiers": [{"days": 30, "bonus_days": 5, "perk": "loyal_30"}]},
        )
        self.assertEqual(cfg.status_code, 200, cfg.text)

        seen: list[int] = []

        async def fake_sync(user):
            seen.append(int(getattr(user, "tg_id", 0) or 0))
            return True

        self.api._sync_user_after_paid_bonus = fake_sync

        granted = self.client.post(
            "/api/admin/users/1001/loyalty/grant",
            headers=admin_hdrs,
            json={"tier_days": 30},
        )
        self.assertEqual(granted.status_code, 200, granted.text)
        self.assertTrue(granted.json().get("ok"))
        self.assertTrue(bool(granted.json().get("sync_ok")))
        self.assertEqual(seen, [1001])

    def test_gift_redeem_tracks_denied_attempt(self) -> None:
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

        created = self.client.post(
            "/api/admin/gift-codes",
            headers=admin_hdrs,
            json={"card_type": "standard"},
        )
        self.assertEqual(created.status_code, 200, created.text)
        code = str(created.json().get("gift_code", {}).get("code") or "")
        self.assertTrue(code)

        ok = self.client.post("/api/gift/redeem", headers=user_hdrs, json={"code": code})
        self.assertEqual(ok.status_code, 200, ok.text)

        denied_resp = self.client.post("/api/gift/redeem", headers=user_hdrs, json={"code": code})
        self.assertEqual(denied_resp.status_code, 400, denied_resp.text)

        denied = self._event_rows("gift_redeem_denied")
        self.assertEqual(len(denied), 1)
        self.assertEqual(str(denied[0]["meta"].get("code") or ""), code)
        self.assertEqual(str(denied[0]["meta"].get("reason") or ""), "already_redeemed")

    def test_promo_redeem_supports_unlimited_uses_flag(self) -> None:
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

        created = self.client.post(
            "/api/admin/promos",
            headers=admin_hdrs,
            json={"code": "FOREVER20", "promo_type": "discount", "value": 20, "uses_left": -1},
        )
        self.assertEqual(created.status_code, 200, created.text)

        redeemed = self.client.post("/api/promo/redeem", headers=user_hdrs, json={"code": "FOREVER20"})
        self.assertEqual(redeemed.status_code, 200, redeemed.text)
        events = self._event_rows("promo_redeemed")
        self.assertEqual(len(events), 1)
        self.assertEqual(str(events[0]["meta"].get("code") or ""), "FOREVER20")
        self.assertEqual(str(events[0]["meta"].get("promo_type") or ""), "discount")

        from db import SessionLocal
        from models import PromoCode

        s = SessionLocal()
        try:
            row = s.query(PromoCode).filter_by(code="FOREVER20").first()
            self.assertIsNotNone(row)
            self.assertEqual(int(row.uses_left or 0), -1)
        finally:
            s.close()

    def test_promo_redeem_rejects_zero_value_without_burning_usage(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        from db import SessionLocal
        from models import PromoCode, PromoUsage

        s = SessionLocal()
        try:
            s.add(PromoCode(code="ZERODAYS", promo_type="days", value=0, uses_left=2))
            s.commit()
        finally:
            s.close()

        redeemed = self.client.post("/api/promo/redeem", headers=user_hdrs, json={"code": "ZERODAYS"})
        self.assertEqual(redeemed.status_code, 400, redeemed.text)
        denied = self._event_rows("promo_redeem_denied")
        self.assertEqual(len(denied), 1)
        self.assertEqual(str(denied[0]["meta"].get("code") or ""), "ZERODAYS")
        self.assertEqual(str(denied[0]["meta"].get("reason") or ""), "invalid_value")

        s = SessionLocal()
        try:
            promo = s.query(PromoCode).filter_by(code="ZERODAYS").first()
            self.assertIsNotNone(promo)
            self.assertEqual(int(promo.uses_left or 0), 2)

            usage = s.query(PromoUsage).filter_by(tg_id=1001, promo_code="ZERODAYS").all()
            self.assertEqual(usage, [])
        finally:
            s.close()

    def test_subscription_endpoint_accepts_sub_token_and_tg_id_fallback(self) -> None:
        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_type = "PAID"
            user.sub_token = "token_1001_secure"
            user.is_active = True
            user.expiry_at = datetime.utcnow() + timedelta(days=10)
            s.commit()
        finally:
            s.close()

        by_token = self.client.get("/s8Kx2mP7qR4wT/token_1001_secure")
        self.assertEqual(by_token.status_code, 200, by_token.text)

        with patch.object(self.api, "_telegram_send_message", new=AsyncMock(return_value=True)) as mocked_send:
            by_tg_id = self.client.get("/s8Kx2mP7qR4wT/1001")
        self.assertEqual(by_tg_id.status_code, 200, by_tg_id.text)
        self.assertEqual(mocked_send.await_count, 1)
        kwargs = mocked_send.await_args.kwargs
        self.assertEqual(int(kwargs.get("chat_id") or 0), 9999)
        self.assertIn("fallback подписки", str(kwargs.get("text") or ""))

    def test_subscription_endpoint_blocks_numeric_fallback_when_flag_disabled(self) -> None:
        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_type = "PAID"
            user.sub_token = "token_1001_secure"
            user.is_active = True
            user.expiry_at = datetime.utcnow() + timedelta(days=10)
            s.commit()
        finally:
            s.close()

        self.api.SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED = False
        by_tg_id = self.client.get("/s8Kx2mP7qR4wT/1001")
        self.assertEqual(by_tg_id.status_code, 404, by_tg_id.text)

    def test_admin_metrics_timeseries_and_nodes_traffic_endpoints(self) -> None:
        from db import SessionLocal
        from models import Event, ExternalOrder, ExternalPaymentEvent, NodeHealthSample, PayAttempt

        now = datetime.utcnow().replace(microsecond=0)
        day_start = now.replace(hour=0, minute=0, second=0)
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        s = SessionLocal()
        try:
            s.add(Event(tg_id=1001, event_name="expired", source="test", created_at=now))
            s.add(
                PayAttempt(
                    tg_id=1001,
                    source="test",
                    plan_code="1_month",
                    amount_stars=299,
                    currency="XTR",
                    status="paid",
                    started_at=now,
                    updated_at=now,
                    paid_at=now,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="fk_test_1",
                    tg_id=1001,
                    provider="freekassa",
                    amount=299.0,
                    currency="RUB",
                    status="paid",
                    created_at=now,
                    paid_at=now,
                )
            )
            s.add(
                ExternalPaymentEvent(
                    provider="freekassa",
                    event_type="result",
                    external_id="bad_callback_1",
                    order_id="fk_test_1",
                    payload_json="{}",
                    signature_ok=False,
                    processed_ok=False,
                    created_at=now,
                )
            )
            s.add(Event(tg_id=1001, event_name="subscription_numeric_fallback", source="subscription", created_at=now))
            s.add(
                NodeHealthSample(
                    node_code="pl",
                    sampled_at=day_start + timedelta(hours=1),
                    panel_latency_ms=50,
                    panel_error_rate=0.0,
                    active_clients=3,
                    total_up_bytes=1024,
                    total_down_bytes=2048,
                    total_traffic_bytes=3072,
                    is_healthy=True,
                    score=95.0,
                    source="test",
                )
            )
            s.add(
                NodeHealthSample(
                    node_code="pl",
                    sampled_at=day_start + timedelta(hours=20),
                    panel_latency_ms=40,
                    panel_error_rate=0.0,
                    active_clients=5,
                    total_up_bytes=4096,
                    total_down_bytes=8192,
                    total_traffic_bytes=12288,
                    is_healthy=True,
                    score=96.0,
                    source="test",
                )
            )
            s.commit()
        finally:
            s.close()

        qs = f"from={day_start.date().isoformat()}&to={day_start.date().isoformat()}"
        ts_resp = self.client.get(f"/api/admin/metrics/timeseries?{qs}", headers=admin_hdrs)
        self.assertEqual(ts_resp.status_code, 200, ts_resp.text)
        points = ts_resp.json().get("points", [])
        self.assertGreaterEqual(len(points), 1)
        today = points[0]
        self.assertGreaterEqual(int(today.get("revenue_stars") or 0), 299)
        self.assertGreaterEqual(float(today.get("revenue_rub") or 0), 299.0)
        self.assertIn("pl", (today.get("nodes") or {}))

        traffic_resp = self.client.get(f"/api/admin/nodes/traffic?{qs}", headers=admin_hdrs)
        self.assertEqual(traffic_resp.status_code, 200, traffic_resp.text)
        rows = traffic_resp.json().get("rows", [])
        self.assertTrue(any((r.get("node_code") == "pl" and float(r.get("traffic_gb") or 0) >= 0) for r in rows))

        summary_resp = self.client.get("/api/admin/summary", headers=admin_hdrs)
        self.assertEqual(summary_resp.status_code, 200, summary_resp.text)
        payload = summary_resp.json()
        self.assertIn("errors", payload)
        self.assertGreaterEqual(int(payload["errors"].get("payment_callback_failures_24h") or 0), 1)
        self.assertGreaterEqual(int(payload["errors"].get("subscription_numeric_fallbacks_24h") or 0), 1)
        self.assertIn("stale_metrics", payload["errors"])

    def test_admin_summary_includes_bonus_event_breakdown(self) -> None:
        from db import SessionLocal
        from models import Event

        now = datetime.utcnow().replace(microsecond=0)
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        s = SessionLocal()
        try:
            for event_name in (
                "promo_channel_activated",
                "promo_channel_denied",
                "promo_redeemed",
                "promo_redeem_denied",
                "gift_redeemed",
                "gift_redeem_denied",
            ):
                s.add(Event(tg_id=1001, event_name=event_name, source="test", created_at=now))
            s.commit()
        finally:
            s.close()

        summary_resp = self.client.get("/api/admin/summary", headers=admin_hdrs)
        self.assertEqual(summary_resp.status_code, 200, summary_resp.text)
        payload = summary_resp.json()
        bonus_events = payload.get("bonus_events_24h") or {}
        self.assertEqual(int(bonus_events.get("channel_activated") or 0), 1)
        self.assertEqual(int(bonus_events.get("channel_denied") or 0), 1)
        self.assertEqual(int(bonus_events.get("promo_redeemed") or 0), 1)
        self.assertEqual(int(bonus_events.get("promo_denied") or 0), 1)
        self.assertEqual(int(bonus_events.get("gift_redeemed") or 0), 1)
        self.assertEqual(int(bonus_events.get("gift_denied") or 0), 1)

    def test_admin_start_links_and_wheel_config(self) -> None:
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        created = self.client.post(
            "/api/admin/start-links",
            headers=admin_hdrs,
            json={
                "code": "launch14",
                "description": "Campaign launch link",
                "target_action": "opening_bonus",
                "is_active": True,
            },
        )
        self.assertEqual(created.status_code, 200, created.text)
        link_id = int(created.json().get("id") or 0)
        self.assertGreater(link_id, 0)

        rows = self.client.get("/api/admin/start-links", headers=admin_hdrs)
        self.assertEqual(rows.status_code, 200, rows.text)
        self.assertTrue(any((r.get("code") or "") == "launch14" for r in rows.json().get("start_links", [])))

        patched = self.client.patch(
            f"/api/admin/start-links/{link_id}",
            headers=admin_hdrs,
            json={"description": "Updated", "is_active": False},
        )
        self.assertEqual(patched.status_code, 200, patched.text)

        removed = self.client.delete(f"/api/admin/start-links/{link_id}", headers=admin_hdrs)
        self.assertEqual(removed.status_code, 200, removed.text)

        cfg_get = self.client.get("/api/admin/wheel-config", headers=admin_hdrs)
        self.assertEqual(cfg_get.status_code, 200, cfg_get.text)
        self.assertIn("wheel_config", cfg_get.json())

        cfg_put = self.client.put(
            "/api/admin/wheel-config",
            headers=admin_hdrs,
            json={
                "preset": "manual",
                "weights": [
                    {"days": 1, "weight": 50},
                    {"days": 3, "weight": 30},
                    {"days": 7, "weight": 15},
                    {"days": 30, "weight": 5},
                ],
                "cooldown_hours": 96,
            },
        )
        self.assertEqual(cfg_put.status_code, 200, cfg_put.text)
        body = cfg_put.json().get("wheel_config") or {}
        self.assertEqual(int(body.get("cooldown_hours") or 0), 96)

    def test_admin_campaign_links_respect_telegram_start_payload_limit(self) -> None:
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        ok = self.client.post(
            "/api/admin/campaign-links/build",
            headers=admin_hdrs,
            json={
                "promo_code": "WELCOME14",
                "campaign_key": "launch_week_1",
                "plan_code": "1_month",
                "source": "bot",
            },
        )
        self.assertEqual(ok.status_code, 200, ok.text)
        body = ok.json()
        self.assertTrue(body.get("ok"))
        self.assertIn("start=campaign_launch_week_1__promo_WELCOME14", body.get("bot_start_link") or "")
        self.assertEqual(body.get("checkout_link"), body.get("bot_start_link"))
        self.assertEqual(body.get("checkout_mode"), "bot_fallback")

        too_long_campaign = "a" * 64
        bad = self.client.post(
            "/api/admin/campaign-links/build",
            headers=admin_hdrs,
            json={
                "promo_code": "WELCOME14",
                "campaign_key": too_long_campaign,
                "plan_code": "1_month",
                "source": "bot",
            },
        )
        self.assertEqual(bad.status_code, 400, bad.text)
        self.assertIn("64", bad.text)

    def test_mark_campaign_once_returns_false_on_duplicate_insert_race(self) -> None:
        class _Nested:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, _tb):
                return False

        class _FakeSession:
            def begin_nested(self):
                return _Nested()

            def add(self, _row) -> None:
                return None

            def flush(self) -> None:
                raise IntegrityError("insert", {}, Exception("duplicate"))

        self.assertFalse(self.api._mark_campaign_once(_FakeSession(), tg_id=1001, campaign_key="channel_subscriber_10d"))


if __name__ == "__main__":
    unittest.main()

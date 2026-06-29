import importlib
import os
import sys
import tempfile
import time
import unittest
import uuid
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlencode
from unittest.mock import patch

from fastapi.testclient import TestClient


def _sign_telegram_init_data(*, bot_token: str, params: dict) -> str:
    import hashlib
    import hmac

    items = sorted((k, v) for k, v in params.items())
    data_check_string = "\n".join([f"{k}={v}" for k, v in items])
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    check_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    payload = dict(params)
    payload["hash"] = check_hash
    return urlencode(payload)


class BackendRouteGapCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = str((repo_root / f"portal_api_gap_test_{uuid.uuid4().hex}.db").resolve())
        self.bot_token = "test_bot_token_123"
        self._saved_env = {
            key: os.environ.get(key)
            for key in (
                "DATABASE_URL",
                "BOT_TOKEN",
                "ADMIN_ID",
                "WEBAPP_SESSION_SECRET",
                "BOT_USERNAME",
                "SUPPORT_USERNAME",
                "PUBLIC_CHANNEL",
            )
        }
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(self.db_path).as_posix()}"
        os.environ["BOT_TOKEN"] = self.bot_token
        os.environ["ADMIN_ID"] = "9999"
        os.environ["WEBAPP_SESSION_SECRET"] = "test_webapp_secret_123"
        os.environ["BOT_USERNAME"] = "pokrov_vpnbot"
        os.environ["SUPPORT_USERNAME"] = "pokrov_supportbot"
        os.environ["PUBLIC_CHANNEL"] = "pokrov_vpn"

        for module_name in ("config", "db", "api"):
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
        self.api = importlib.import_module("api")
        importlib.reload(self.api)
        self.client = TestClient(self.api.app)

        from db import SessionLocal
        from models import User

        session = SessionLocal()
        try:
            session.add(
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
            session.add(
                User(
                    tg_id=9999,
                    username="admin",
                    uuid=str(uuid.uuid4()),
                    email="user_9999",
                    sub_type="PAID",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            session.commit()
        finally:
            session.close()

    def tearDown(self) -> None:
        try:
            from db import engine

            engine.dispose()
        except Exception:
            pass
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        try:
            Path(self.db_path).unlink(missing_ok=True)
        except Exception:
            pass
        self._tmp.cleanup()

    def _init_data(self, tg_id: int, username: str) -> str:
        return _sign_telegram_init_data(
            bot_token=self.bot_token,
            params={
                "auth_date": str(int(time.time())),
                "query_id": f"query-{tg_id}",
                "user": f'{{"id":{tg_id},"first_name":"Test","username":"{username}"}}',
            },
        )

    @property
    def admin_headers(self) -> dict[str, str]:
        return {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

    @property
    def user_headers(self) -> dict[str, str]:
        return {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

    def test_public_catalog_and_funnel_gap_routes(self) -> None:
        catalog = self.client.get("/api/public/catalog")
        self.assertEqual(catalog.status_code, 200, catalog.text)
        self.assertIn("Cache-Control", catalog.headers)
        self.assertIsInstance(catalog.json(), dict)

        funnel = self.client.post(
            "/api/funnel/events",
            json={
                "event_name": "page_view",
                "stage": "site_visit",
                "channel": "marketing",
                "source": "home",
                "session_id": "session-gap-001",
                "path": "/",
                "meta": {"surface": "gap-test"},
            },
        )
        self.assertEqual(funnel.status_code, 200, funnel.text)
        self.assertTrue(funnel.json().get("ok"))

        bad_funnel = self.client.post(
            "/api/funnel/events",
            json={
                "event_name": "unknown_event",
                "stage": "site_visit",
                "channel": "marketing",
                "source": "home",
                "session_id": "session-gap-002",
            },
        )
        self.assertEqual(bad_funnel.status_code, 400, bad_funnel.text)

        connect = self.client.post("/api/connect/confirm", headers=self.user_headers)
        self.assertEqual(connect.status_code, 200, connect.text)
        self.assertTrue(connect.json().get("ok"))

        summary = self.client.get("/api/admin/funnel/summary", headers=self.admin_headers)
        self.assertEqual(summary.status_code, 200, summary.text)
        body = summary.json()
        self.assertIn("stages", body)
        self.assertIn("period", body)

    def test_admin_broadcast_and_referral_gap_routes(self) -> None:
        sent_to: list[int] = []

        async def fake_send_message(tg_id: int, _text: str) -> bool:
            sent_to.append(int(tg_id))
            return True

        with patch.object(self.api, "_telegram_send_message", new=fake_send_message):
            broadcast = self.client.post(
                "/api/admin/broadcast",
                headers=self.admin_headers,
                json={"text": "POKROV test broadcast", "segment": "custom", "tg_ids": [1001], "limit": 5},
            )
        self.assertEqual(broadcast.status_code, 200, broadcast.text)
        self.assertEqual(broadcast.json().get("sent"), 1)
        self.assertEqual(sent_to, [1001])

        from db import SessionLocal
        from models import ReferralBonusQueue

        session = SessionLocal()
        try:
            session.add(
                ReferralBonusQueue(
                    referrer_tg_id=9999,
                    referred_tg_id=1001,
                    order_id="gap-order-1",
                    ready_at=self.api._utcnow() + timedelta(days=1),
                    status="pending",
                    meta="{}",
                )
            )
            session.commit()
        finally:
            session.close()

        pending = self.client.get("/api/admin/referrals/pending", headers=self.admin_headers)
        self.assertEqual(pending.status_code, 200, pending.text)
        self.assertEqual(pending.json()["rows"][0]["order_id"], "gap-order-1")

        with patch.object(
            self.api,
            "_process_referral_bonus_queue",
            return_value={"processed": 0, "skipped": 1, "failed": 0},
        ):
            processed = self.client.post(
                "/api/admin/referrals/process",
                headers=self.admin_headers,
                json={"limit": 10, "force_without_activity": False},
            )
        self.assertEqual(processed.status_code, 200, processed.text)
        self.assertTrue(processed.json().get("ok"))
        self.assertEqual(processed.json().get("skipped"), 1)

    def test_admin_campaign_crud_gap_routes(self) -> None:
        created = self.client.post(
            "/api/admin/campaigns",
            headers=self.admin_headers,
            json={
                "name": "Gap campaign",
                "campaign_type": "promo",
                "target_value": "GAP10",
                "segment": "all_active",
                "max_activations": 5,
                "auto_disable": True,
                "is_active": True,
                "metadata": {"source": "test"},
            },
        )
        self.assertEqual(created.status_code, 200, created.text)
        campaign_id = int(created.json()["id"])

        listed = self.client.get("/api/admin/campaigns", headers=self.admin_headers)
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertTrue(any(int(row["id"]) == campaign_id for row in listed.json()["campaigns"]))

        patched = self.client.patch(
            f"/api/admin/campaigns/{campaign_id}",
            headers=self.admin_headers,
            json={"name": "Gap campaign patched", "is_active": False},
        )
        self.assertEqual(patched.status_code, 200, patched.text)

        deleted = self.client.delete(f"/api/admin/campaigns/{campaign_id}", headers=self.admin_headers)
        self.assertEqual(deleted.status_code, 200, deleted.text)
        self.assertTrue(deleted.json().get("ok"))

    def test_admin_node_runtime_and_sync_gap_routes(self) -> None:
        class FakePanel:
            async def login(self):
                return True

            async def get_node_runtime_snapshots(self, node_codes=None):
                codes = node_codes or ["nl-free"]
                return {
                    code: {
                        "node_code": code,
                        "panel": {"ok": True},
                        "dataplane": {"ok": True},
                        "transport": {"ok": True},
                    }
                    for code in codes
                }

            async def enable_client(self, _uuid, _enable):
                return True

            async def close(self):
                return None

        with patch.object(self.api, "ControlPanel", FakePanel):
            runtime = self.client.get("/api/admin/nodes/runtime?only=nl-free", headers=self.admin_headers)
            self.assertEqual(runtime.status_code, 200, runtime.text)
            self.assertEqual(runtime.json()["nodes"][0]["node_code"], "nl-free")

            synced = self.client.post(
                "/api/admin/nodes/sync",
                headers=self.admin_headers,
                json={"tg_id": 1001, "segment": "active", "limit": 10},
            )
        self.assertEqual(synced.status_code, 200, synced.text)
        self.assertEqual(synced.json().get("synced"), 1)

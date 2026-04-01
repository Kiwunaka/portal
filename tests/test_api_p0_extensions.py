import importlib
import os
import sys
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta
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


class ApiP0ExtensionsTests(unittest.TestCase):
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
            "BOT_USERNAME",
            "SUPPORT_USERNAME",
            "PUBLIC_CHANNEL",
            "WEBAPP_DEV_AUTH",
            "WEBAPP_DEV_TG_ID",
            "APP_ANDROID_PLAY_URL",
            "APP_ANDROID_APK_URL",
            "APP_ANDROID_MIRROR_URL",
            "APP_WINDOWS_EXE_URL",
            "APP_WINDOWS_MIRROR_URL",
            "APP_DOCS_URL",
        ):
            self._saved_env[k] = os.environ.get(k)

        os.environ["DATABASE_URL"] = f"sqlite:///{db_uri_path}"
        os.environ["BOT_TOKEN"] = self.bot_token
        os.environ["ADMIN_ID"] = "9999"
        os.environ["BOT_USERNAME"] = "pokrov_vpnbot"
        os.environ["SUPPORT_USERNAME"] = "pokrov_supportbot"
        os.environ["PUBLIC_CHANNEL"] = "pokrov_vpn"
        os.environ["WEBAPP_DEV_AUTH"] = "true"
        os.environ["WEBAPP_DEV_TG_ID"] = "1001"
        os.environ["APP_ANDROID_PLAY_URL"] = ""
        os.environ["APP_ANDROID_APK_URL"] = ""
        os.environ["APP_ANDROID_MIRROR_URL"] = ""
        os.environ["APP_WINDOWS_EXE_URL"] = ""
        os.environ["APP_WINDOWS_MIRROR_URL"] = ""
        os.environ["APP_DOCS_URL"] = ""

        for module_name in (
            "api",
            "events_service",
            "offers_service",
            "pay_attempts_service",
            "points_service",
            "db",
            "models",
            "migrations",
            "config",
        ):
            if module_name in sys.modules:
                sys.modules.pop(module_name, None)

        importlib.import_module("config")
        importlib.import_module("db")
        self.api = importlib.import_module("api")
        importlib.reload(self.api)

        from db import SessionLocal
        from models import NodeHealthSample, User

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
                    expiry_at=(datetime.utcnow() + timedelta(days=15)).replace(microsecond=0),
                )
            )
            s.add(
                NodeHealthSample(
                    node_code="de",
                    sampled_at=datetime.utcnow(),
                    panel_latency_ms=72,
                    panel_error_rate=0.0,
                    active_clients=12,
                    is_healthy=True,
                    score=0.95,
                    source="tests",
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

    def test_dev_auth_allows_localhost_without_header(self) -> None:
        client = TestClient(self.api.app, base_url="http://localhost")
        r = client.get("/api/dashboard")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["tg_id"], 1001)

    def test_dev_auth_denies_non_localhost_without_header(self) -> None:
        client = TestClient(self.api.app, base_url="http://example.com")
        r = client.get("/api/dashboard")
        self.assertEqual(r.status_code, 401, r.text)

    def test_dev_auth_denies_bad_origin_even_on_localhost(self) -> None:
        client = TestClient(self.api.app, base_url="http://localhost")
        r = client.get("/api/dashboard", headers={"Origin": "https://evil.example"})
        self.assertEqual(r.status_code, 401, r.text)

    def test_dev_auth_allows_localhost_origin(self) -> None:
        client = TestClient(self.api.app, base_url="http://localhost")
        r = client.get("/api/dashboard", headers={"Origin": "http://localhost:3000"})
        self.assertEqual(r.status_code, 200, r.text)

    def test_events_whitelist_and_reject_unknown(self) -> None:
        client = TestClient(self.api.app)
        hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

        ok = client.post("/api/events", headers=hdrs, json={"event_name": "opened_webapp", "source": "webapp", "meta": {"tab": "status"}})
        self.assertEqual(ok.status_code, 200, ok.text)
        self.assertTrue(ok.json()["ok"])

        bad = client.post("/api/events", headers=hdrs, json={"event_name": "totally_unknown_event", "source": "webapp"})
        self.assertEqual(bad.status_code, 400, bad.text)

    def test_pay_attempt_start_offer_accept_and_points(self) -> None:
        client = TestClient(self.api.app)
        hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

        from offers_service import create_offer

        offer = create_offer(
            tg_id=1001,
            offer_type="trial_oto",
            plan_code="1_month",
            price_stars=149,
            trigger_reason="near_expiry",
        )
        self.assertIsNotNone(offer)

        active = client.get("/api/offers/active", headers=hdrs)
        self.assertEqual(active.status_code, 200, active.text)
        self.assertEqual(active.json()["offer"]["price_stars"], 149)

        accept = client.post(f"/api/offers/{offer.id}/accept", headers=hdrs)
        self.assertEqual(accept.status_code, 200, accept.text)
        self.assertTrue(accept.json()["ok"])

        start = client.post(
            "/api/pay/attempts/start",
            headers=hdrs,
            json={"plan_code": "9_months", "source": "webapp", "offer_id": offer.id},
        )
        self.assertEqual(start.status_code, 200, start.text)
        body = start.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["amount_stars"], 1399)
        self.assertIn("t.me/pokrov_vpnbot", body["pay_url"])

        points = client.get("/api/points", headers=hdrs)
        self.assertEqual(points.status_code, 200, points.text)
        self.assertIn("available_points", points.json())
        self.assertIn("preview", points.json())

    def test_network_probe_returns_exact_payload_size(self) -> None:
        client = TestClient(self.api.app)
        r = client.get("/api/network/probe?size_mb=2")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.headers.get("x-probe-size-mb"), "2")
        self.assertEqual(len(r.content), 2 * 1024 * 1024)

    def test_public_social_proof_returns_aggregate(self) -> None:
        client = TestClient(self.api.app)
        r = client.get("/api/public/social-proof")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertGreaterEqual(int(body.get("connected_users", 0)), 1)
        self.assertIn("updated_at", body)
        self.assertEqual(r.headers.get("cache-control"), "public, max-age=60")

    def test_featured_reviews_mask_username_in_api_response(self) -> None:
        from db import SessionLocal
        from models import Review

        s = SessionLocal()
        try:
            s.add(
                Review(
                    tg_id=1001,
                    username="alexey",
                    rating=5,
                    text="Отличный сервис",
                    is_featured=True,
                )
            )
            s.commit()
        finally:
            s.close()

        client = TestClient(self.api.app)
        r = client.get("/api/reviews")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(len(body.get("reviews", [])), 1)
        self.assertEqual(body["reviews"][0]["username"], "alex****")
        self.assertNotIn("alexey", str(body))

    def test_review_create_rejects_too_short_text_after_trim(self) -> None:
        client = TestClient(self.api.app)
        hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

        r = client.post("/api/reviews", headers=hdrs, json={"rating": 5, "text": "  ok  "})
        self.assertEqual(r.status_code, 400, r.text)
        self.assertEqual(r.json()["detail"], "Review text is too short")

    def test_feedback_endpoint_persists_new_entry(self) -> None:
        from db import SessionLocal
        from models import FeedbackEntry

        client = TestClient(self.api.app)
        hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        r = client.post(
            "/api/feedback",
            headers=hdrs,
            json={"category": "idea", "text": "Добавьте больше живых отзывов на сайт"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["status"], "new")
        self.assertGreater(int(body["feedback_id"]), 0)

        s = SessionLocal()
        try:
            row = s.query(FeedbackEntry).filter_by(id=int(body["feedback_id"])).first()
            self.assertIsNotNone(row)
            self.assertEqual(row.tg_id, 1001)
            self.assertEqual(row.username, "alice")
            self.assertEqual(row.category, "idea")
            self.assertEqual(row.status, "new")
            self.assertEqual(row.text, "Добавьте больше живых отзывов на сайт")
        finally:
            s.close()

    def test_admin_metrics_status_endpoint(self) -> None:
        client = TestClient(self.api.app)
        hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        r = client.get("/api/admin/metrics/status", headers=hdrs)
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertIn(body["status"], {"fresh", "stale"})
        self.assertIn("stale_after_seconds", body)

    def test_client_apps_endpoint_returns_empty_defaults(self) -> None:
        client = TestClient(self.api.app)
        hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        r = client.get("/api/client/apps", headers=hdrs)
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["android"]["play_url"], "")
        self.assertEqual(body["android"]["apk_url"], "")
        self.assertEqual(body["android"]["mirror_url"], "")
        self.assertEqual(body["windows"]["exe_url"], "")
        self.assertEqual(body["windows"]["mirror_url"], "")
        self.assertEqual(body["docs_url"], "")
        self.assertRegex(body["updated_at"], r"^\d{4}-\d{2}-\d{2}T")
        self.assertTrue(body["updated_at"].endswith("Z"))

    def test_client_apps_endpoint_returns_configured_urls(self) -> None:
        self.api.Settings.APP_ANDROID_PLAY_URL = "https://play.google.com/store/apps/details?id=space.pokrov.vpn"
        self.api.Settings.APP_ANDROID_APK_URL = "https://github.com/example/pokrov-vpn/releases/latest/download/pokrov-vpn-android.apk"
        self.api.Settings.APP_ANDROID_MIRROR_URL = "https://downloads.example.com/mobile/pokrov-vpn-android.apk"
        self.api.Settings.APP_WINDOWS_EXE_URL = "https://github.com/example/pokrov-vpn/releases/latest/download/pokrov-vpn-windows.exe"
        self.api.Settings.APP_WINDOWS_MIRROR_URL = "https://downloads.example.com/desktop/pokrov-vpn-windows.exe"
        self.api.Settings.APP_DOCS_URL = "https://pokrov.space/install/"

        client = TestClient(self.api.app)
        hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        r = client.get("/api/client/apps", headers=hdrs)
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["android"]["play_url"], self.api.Settings.APP_ANDROID_PLAY_URL)
        self.assertEqual(body["android"]["apk_url"], self.api.Settings.APP_ANDROID_APK_URL)
        self.assertEqual(body["android"]["mirror_url"], self.api.Settings.APP_ANDROID_MIRROR_URL)
        self.assertEqual(body["windows"]["exe_url"], self.api.Settings.APP_WINDOWS_EXE_URL)
        self.assertEqual(body["windows"]["mirror_url"], self.api.Settings.APP_WINDOWS_MIRROR_URL)
        self.assertEqual(body["docs_url"], self.api.Settings.APP_DOCS_URL)

    def test_start_trial_returns_session_and_subscription_url(self) -> None:
        calls: list[dict[str, object]] = []

        class _FakePanel:
            async def add_client(self, **kwargs):
                calls.append(kwargs)
                return True

            async def close(self):
                return None

        old_panel = self.api.ControlPanel
        try:
            self.api.ControlPanel = _FakePanel
            client = TestClient(self.api.app)
            response = client.post(
                "/api/client/session/start-trial",
                json={
                    "install_id": "install-12345678",
                    "device_name": "Alice Pixel",
                    "platform": "android",
                    "os_version": "14",
                    "app_version": "1.0.0",
                    "locale": "ru-RU",
                    "time_zone": "Europe/Moscow",
                },
            )
        finally:
            self.api.ControlPanel = old_panel

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertTrue(body["created"])
        self.assertTrue(str(body["session_token"]))
        self.assertTrue(str(body["subscription_url"]).startswith("https://connect.pokrov.space/s8Kx2mP7qR4wT/"))
        self.assertTrue(calls)

    def test_user_payload_includes_app_and_telegram_monitoring_context(self) -> None:
        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            row = s.query(User).filter(User.tg_id == 1001).first()
            self.assertIsNotNone(row)
            row.is_app_user = True
            row.app_install_id = "install-1001"
            row.app_device_name = "Alice phone"
            row.app_platform = "android"
            row.app_version = "1.2.3"
            row.app_last_ip = "203.0.113.10"
            row.linked_telegram_id = 777001
            row.linked_telegram_username = "alice_linked"
            row.sub_token = row.sub_token or "subtoken-monitoring"
            s.commit()
        finally:
            s.close()

        client = TestClient(self.api.app)
        hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        r = client.get("/api/user/1001", headers=hdrs)
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body.get("last_ip"), "203.0.113.10")
        self.assertEqual(body.get("linked_telegram", {}).get("id"), 777001)
        self.assertEqual(body.get("linked_telegram", {}).get("username"), "alice_linked")
        self.assertTrue(body.get("sync", {}).get("app_identity_known"))
        self.assertTrue(body.get("sync", {}).get("telegram_linked"))
        self.assertTrue(body.get("sync", {}).get("subscription_ready"))
        self.assertEqual(body.get("sync", {}).get("device_count"), 1)


if __name__ == "__main__":
    unittest.main()

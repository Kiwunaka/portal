import importlib
import hashlib
import json
import os
import sys
import tempfile
import concurrent.futures
import threading
import unittest
import uuid
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
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


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ApiAuthAndTicketsTests(unittest.TestCase):
    @staticmethod
    def _legacy_reality_subscription_node(
        *,
        code: str,
        access_role: str,
        last_health_at: datetime | None,
        is_healthy: bool = True,
        accepting_new_clients: bool = True,
        is_draining: bool = False,
        legacy_profile_enabled: bool = True,
    ):
        from models import Node

        return Node(
            code=code,
            name=code.upper(),
            host=f"{code}.example.test",
            vless_port=443,
            reality_sni="www.example.test",
            reality_pbk=f"pbk-{code}",
            reality_sid=f"sid-{code}",
            panel_base_url=f"https://{code}.example.test:8444",
            panel_path="/panel",
            panel_user="admin",
            panel_pass="pass",
            inbound_id=1,
            enabled=True,
            access_role=access_role,
            accepting_new_clients=accepting_new_clients,
            is_draining=is_draining,
            is_healthy=is_healthy,
            last_health_at=last_health_at,
            transport_profiles_json=json.dumps(
                [{"name": "legacy_reality_fallback", "enabled": legacy_profile_enabled}]
            ),
        )

    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str((Path(self._tmp.name) / f"portal_api_test_{uuid.uuid4().hex}.db").resolve())
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
            "SUPPORT_AI_ENABLED",
            "SUPPORT_AI_API_KEY",
            "SUPPORT_AI_MODEL",
            "SUPPORT_AI_MIN_INTERVAL_SECONDS",
            "FREE_TIER_ENABLED",
            "AUTO_DOWNGRADE_TO_FREE",
        ):
            self._saved_env[k] = os.environ.get(k)

        os.environ["DATABASE_URL"] = f"sqlite:///{db_uri_path}"
        os.environ["BOT_TOKEN"] = self.bot_token
        os.environ["ADMIN_ID"] = "9999"
        os.environ["WEBAPP_SESSION_SECRET"] = "test_webapp_secret_123"
        os.environ["BOT_USERNAME"] = "net4ebur_bot"
        os.environ["SUPPORT_USERNAME"] = "portal_privacy_helpbot"
        os.environ["PUBLIC_CHANNEL"] = "pokrov_vpn"
        os.environ["CHANNEL_PREMIUM_DAYS"] = "10"
        os.environ["OPENING_PREMIUM_DAYS"] = "14"
        os.environ["OPENING_PREMIUM_CAMPAIGN_KEY"] = "opening_premium_14d"
        os.environ["SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED"] = "true"
        os.environ["SUPPORT_UPLOAD_DIR"] = str((Path(self._tmp.name) / "support_uploads").resolve())
        os.environ["SUPPORT_AI_ENABLED"] = "false"
        os.environ["SUPPORT_AI_API_KEY"] = ""
        os.environ["SUPPORT_AI_MODEL"] = "deepseek/deepseek-v4-flash-0731"
        os.environ["SUPPORT_AI_MIN_INTERVAL_SECONDS"] = "0"
        os.environ["FREE_TIER_ENABLED"] = "true"
        os.environ["AUTO_DOWNGRADE_TO_FREE"] = "true"

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
        if "account_foundation_service" in sys.modules:
            importlib.reload(sys.modules["account_foundation_service"])
        if "economy_service" in sys.modules:
            importlib.reload(sys.modules["economy_service"])
        if "events_service" in sys.modules:
            importlib.reload(sys.modules["events_service"])
        if "channel_bonus_service" in sys.modules:
            importlib.reload(sys.modules["channel_bonus_service"])
        if "api" in sys.modules:
            importlib.reload(sys.modules["api"])
        self.api = importlib.import_module("api")
        importlib.reload(self.api)
        self._telegram_send_patcher = patch.object(
            self.api,
            "_telegram_send_message",
            new_callable=AsyncMock,
            return_value=True,
        )
        self.telegram_send_mock = self._telegram_send_patcher.start()
        self.addCleanup(self._telegram_send_patcher.stop)
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
                "auth_date": str(int(time.time())),
                "query_id": "AAEAAAE",
                "user": f'{{"id":{tg_id},"first_name":"Test","username":"{username}"}}',
            },
        )

    def _telegram_login_payload(self, tg_id: int, username: str, *, auth_date: int | None = None) -> dict:
        import hashlib
        import hmac

        payload = {
            "id": int(tg_id),
            "first_name": "Test",
            "username": username,
            "auth_date": int(auth_date if auth_date is not None else time.time()),
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

    def _promote_test_user_to_paid(self, tg_id: int = 1001) -> None:
        from account_foundation_service import ensure_user_account_foundation
        from db import SessionLocal
        from models import EntitlementGrant, User

        now = _utcnow().replace(microsecond=0)
        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=tg_id).one()
            ensure_user_account_foundation(s, user, now=now)
            user.sub_type = "PAID"
            user.current_plan_code = "1_month"
            user.is_active = True
            user.expiry_at = now + timedelta(days=30)
            s.add(
                EntitlementGrant(
                    id=str(uuid.uuid4()),
                    account_id=str(user.account_id),
                    legacy_tg_id=int(user.tg_id),
                    idempotency_key=f"test-paid-channel:{user.account_id}",
                    source="provider_payment",
                    status="active",
                    grant_kind="paid_access",
                    plan_code="1_month",
                    starts_at=now,
                    expires_at=now + timedelta(days=30),
                    activated_at=now,
                    duration_days=30,
                    provider="test",
                    created_at=now,
                    updated_at=now,
                )
            )
            s.commit()
        finally:
            s.close()

    def test_telegram_delivery_is_offline_by_default(self) -> None:
        self.assertIsInstance(self.api._telegram_send_message, AsyncMock)

    def test_normal_session_support_assistant_accepts_safe_diagnostics(self) -> None:
        headers = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        response = self.client.post(
            "/api/client/support/assistant",
            headers=headers,
            json={
                "message": "Connection diagnostic question",
                "scope": "support",
                "safeDiagnostics": {
                    "platform": "windows",
                    "connection_status": "disconnected",
                },
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["source"], "local_fallback")
        events = self._event_rows("client_support_assistant")
        self.assertEqual(len(events), 1)
        self.assertEqual(
            events[0]["meta"]["diagnostics_keys"],
            ["connection_status", "platform"],
        )

    def _upload_support_attachment(
        self,
        headers: dict[str, str],
        *,
        name: str = "diagnostic.txt",
        content: bytes = b"private diagnostic",
    ):
        return self.client.post(
            "/api/tickets/uploads",
            headers={**headers, "Content-Type": "text/plain", "X-Upload-Filename": name},
            content=content,
        )

    def _execute_node_intent(self, *, action: str, node_code: str, payload: dict):
        return self._execute_admin_intent(
            action=action,
            target_type="node",
            target_id=node_code,
            method="POST",
            path=f"/api/admin/nodes/{node_code}/{action.split('.', 1)[1]}",
            payload=payload,
        )

    def _prepare_admin_intent(
        self,
        *,
        action: str,
        target_type: str,
        target_id: str | int,
        payload: dict,
    ):
        admin_headers = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        return self.client.post(
            "/api/admin/action-intents",
            headers=admin_headers,
            json={
                "action": action,
                "target": {"type": target_type, "id": str(target_id)},
                "payload": payload,
            },
        )

    def _execute_admin_intent(
        self,
        *,
        action: str,
        target_type: str,
        target_id: str | int,
        method: str,
        path: str,
        payload: dict,
    ):
        admin_headers = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        prepared = self._prepare_admin_intent(
            action=action,
            target_type=target_type,
            target_id=target_id,
            payload=payload,
        )
        self.assertEqual(prepared.status_code, 200, prepared.text)
        challenge = str(prepared.json()["confirmation_challenge"])
        return self.client.request(
            method,
            path,
            headers={
                **admin_headers,
                "X-Admin-Intent-Id": str(prepared.json()["intent_id"]),
                "X-Admin-Idempotency-Key": str(uuid.uuid4()),
                "X-Admin-Confirmation-SHA256": hashlib.sha256(challenge.encode("utf-8")).hexdigest(),
            },
            json=payload,
        )

    def test_admin_endpoint_requires_admin_guard(self) -> None:
        hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        r = self.client.get("/api/admin/summary", headers=hdrs)
        self.assertEqual(r.status_code, 403)

    def test_admin_users_supports_effective_status_origin_and_extended_search(self) -> None:
        from db import SessionLocal
        from models import NodeProvisioningJob, User

        now = _utcnow()
        s = SessionLocal()
        try:
            s.add_all(
                [
                    User(
                        tg_id=1002,
                        username="bob",
                        uuid=str(uuid.uuid4()),
                        email="user_1002",
                        sub_type="PAID",
                        is_active=True,
                        expiry_at=now - timedelta(days=2),
                        tos_accepted=True,
                    ),
                    User(
                        tg_id=1003,
                        username="carol",
                        uuid=str(uuid.uuid4()),
                        email="user_1003",
                        sub_type="PAID",
                        is_active=False,
                        expiry_at=now + timedelta(days=20),
                        tos_accepted=True,
                    ),
                    User(
                        tg_id=-501,
                        username=None,
                        uuid=str(uuid.uuid4()),
                        email="manual_501",
                        sub_type="MANUAL",
                        is_active=True,
                        expiry_at=now + timedelta(days=30),
                        tos_accepted=True,
                        is_manual=True,
                        display_name="QA Manual",
                        created_by_admin=9999,
                    ),
                    User(
                        tg_id=1004,
                        username=None,
                        uuid=str(uuid.uuid4()),
                        email="user_1004",
                        sub_type="FREE",
                        is_active=True,
                        expiry_at=now + timedelta(days=15),
                        tos_accepted=True,
                        is_app_user=True,
                        app_install_id="ios-install-1004",
                        app_device_name="iPhone 15 Pro",
                        app_platform="ios",
                        display_name="Alice iPhone",
                        linked_telegram_id=4040,
                        linked_telegram_username="linked_alice",
                    ),
                ]
            )
            s.commit()
        finally:
            s.close()

        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        manual = self.client.get(
            "/api/admin/users",
            headers=admin_hdrs,
            params={"status": "manual_test", "origin": "manual_test", "sort": "created_desc", "page": 1, "page_size": 10},
        )
        self.assertEqual(manual.status_code, 200, manual.text)
        manual_body = manual.json()
        self.assertEqual(int(manual_body["total"]), 1)
        self.assertEqual(int(manual_body["users"][0]["tg_id"]), -501)
        self.assertEqual(manual_body["users"][0]["status"], "manual_test")
        self.assertEqual(manual_body["users"][0]["origin"], "manual_test")

        inactive = self.client.get(
            "/api/admin/users",
            headers=admin_hdrs,
            params={"status": "inactive", "sort": "status", "page": 1, "page_size": 20},
        )
        self.assertEqual(inactive.status_code, 200, inactive.text)
        inactive_rows = {int(row["tg_id"]): row["status"] for row in inactive.json()["users"]}
        self.assertEqual(inactive_rows[1002], "expired")
        self.assertEqual(inactive_rows[1003], "blocked")

        search = self.client.get(
            "/api/admin/users",
            headers=admin_hdrs,
            params={"q": "ios-install-1004", "page": 1, "page_size": 10},
        )
        self.assertEqual(search.status_code, 200, search.text)
        search_rows = search.json()["users"]
        self.assertEqual(len(search_rows), 1)
        self.assertEqual(int(search_rows[0]["tg_id"]), 1004)
        self.assertEqual(search_rows[0]["origin"], "app")
        self.assertEqual(search_rows[0]["linked_telegram_username"], "linked_alice")
        self.assertEqual(search_rows[0]["app_device_name"], "iPhone 15 Pro")
        self.assertEqual(search_rows[0]["app_platform"], "ios")

    def test_admin_delete_test_user_rejects_real_user_and_deletes_manual_user(self) -> None:
        from db import SessionLocal
        from models import Event, Node, User, UserKeyPolicy, UserNode

        now = _utcnow()
        s = SessionLocal()
        try:
            node = Node(
                code="delete-test",
                name="Delete test node",
                host="delete.example.test",
                vless_port=443,
                reality_sni="delete.example.test",
                reality_pbk="pbk-delete",
                reality_sid="sid-delete",
                panel_base_url="https://delete.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=1,
                enabled=True,
                accepting_new_clients=True,
                access_role="paid",
            )
            s.add(node)
            s.flush()
            user = User(
                tg_id=-777,
                username=None,
                uuid=str(uuid.uuid4()),
                email="manual_777",
                sub_type="MANUAL",
                is_active=True,
                expiry_at=now + timedelta(days=7),
                tos_accepted=True,
                is_manual=True,
                display_name="Delete Me",
                created_by_admin=9999,
                sub_token="manual-delete-token",
            )
            s.add(user)
            s.flush()
            s.add(UserNode(tg_id=-777, node_id=node.id, client_uuid=str(user.uuid), panel_email=str(user.email)))
            s.add(UserKeyPolicy(tg_id=-777, node_code=node.code))
            s.add(Event(tg_id=-777, event_name="opened_webapp", source="tests"))
            s.commit()
        finally:
            s.close()

        class FakePanel:
            async def login(self):
                return True

            async def close(self):
                return True

            async def delete_client(self, tg_id: int):
                return tg_id == -777

        original_panel = self.api.ControlPanel
        self.api.ControlPanel = FakePanel
        try:
            admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

            real = self._prepare_admin_intent(
                action="user.delete_test",
                target_type="user",
                target_id=1001,
                payload={},
            )
            self.assertEqual(real.status_code, 409, real.text)

            deleted = self._execute_admin_intent(
                action="user.delete_test",
                target_type="user",
                target_id=-777,
                method="POST",
                path="/api/admin/users/-777/delete-test-user",
                payload={},
            )
            self.assertEqual(deleted.status_code, 200, deleted.text)
            self.assertTrue(bool(deleted.json()["panel_deleted"]))
        finally:
            self.api.ControlPanel = original_panel

        s = SessionLocal()
        try:
            self.assertIsNone(s.query(User).filter(User.tg_id == -777).first())
            self.assertIsNone(s.query(UserNode).filter(UserNode.tg_id == -777).first())
            self.assertIsNone(s.query(UserKeyPolicy).filter(UserKeyPolicy.tg_id == -777).first())
            self.assertIsNone(s.query(Event).filter(Event.tg_id == -777).first())
        finally:
            s.close()

    def test_admin_nodes_drift_returns_summary(self) -> None:
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        fake_payload = {
            "summary": {"total": 2, "ok": 1, "drift": 1},
            "results": [
                {
                    "node_code": "it",
                    "status": "ok",
                    "mismatches": [],
                    "runtime": {"auth_method": "key"},
                    "checks": {"inbound_present": True},
                },
                {
                    "node_code": "nl",
                    "status": "drift",
                    "mismatches": ["port_match"],
                    "runtime": {"inspect_error": ""},
                    "checks": {"port_match": False},
                },
            ],
        }

        self.api._build_admin_node_drift_report = lambda **_kwargs: fake_payload
        r = self.client.get("/api/admin/nodes/drift", headers=admin_hdrs)
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["summary"]["total"], 2)
        self.assertEqual(body["summary"]["drift"], 1)
        self.assertEqual(body["results"][1]["node_code"], "nl")

    def test_user_data_exposes_paid_pool_when_mapping_exists(self) -> None:
        from db import SessionLocal
        from models import Node, User, UserNode

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_type = "PAID"
            user.current_plan_code = "1_month"
            user.sub_token = "subtoken-paid-1001"
            pl = Node(
                code="pl",
                name="Poland",
                host="pl.example.test",
                vless_port=443,
                reality_sni="www.orange.pl",
                reality_pbk="pbk-pl",
                reality_sid="sid-pl",
                panel_base_url="https://pl.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=1,
                enabled=True,
            )
            it = Node(
                code="it",
                name="Italy",
                host="it.example.test",
                vless_port=443,
                reality_sni="www.tim.it",
                reality_pbk="pbk-it",
                reality_sid="sid-it",
                panel_base_url="https://it.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=1,
                enabled=True,
            )
            s.add_all([pl, it])
            s.flush()
            s.add(UserNode(tg_id=1001, node_id=it.id, client_uuid=str(user.uuid), panel_email=str(user.email)))
            s.commit()
        finally:
            s.close()

        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        r = self.client.get("/api/user/1001", headers=user_hdrs)
        self.assertEqual(r.status_code, 200, r.text)
        nodes = r.json()["nodes"]
        self.assertEqual([row["code"] for row in nodes], ["it", "pl"])

    def test_user_data_filters_free_mapping_but_keeps_paid_brain_mapping(self) -> None:
        from db import SessionLocal
        from models import Node, User, UserNode

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_type = "PAID"
            user.current_plan_code = "1_month"
            user.sub_token = "subtoken-paid-1001"
            brain = Node(
                code="brain",
                name="Brain",
                host="brain.example.test",
                vless_port=443,
                reality_sni="www.google.com",
                reality_pbk="pbk-brain",
                reality_sid="sid-brain",
                panel_base_url="https://brain.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=1,
                enabled=True,
            )
            free = Node(
                code="free",
                name="Free",
                host="free.example.test",
                vless_port=443,
                reality_sni="www.google.com",
                reality_pbk="pbk-free",
                reality_sid="sid-free",
                panel_base_url="https://free.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=1,
                enabled=True,
            )
            it = Node(
                code="it",
                name="Italy",
                host="it.example.test",
                vless_port=443,
                reality_sni="www.tim.it",
                reality_pbk="pbk-it",
                reality_sid="sid-it",
                panel_base_url="https://it.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=1,
                enabled=True,
            )
            s.add_all([brain, free, it])
            s.flush()
            s.add_all(
                [
                    UserNode(tg_id=1001, node_id=brain.id, client_uuid=str(user.uuid), panel_email=str(user.email)),
                    UserNode(tg_id=1001, node_id=free.id, client_uuid=str(user.uuid), panel_email=str(user.email)),
                    UserNode(tg_id=1001, node_id=it.id, client_uuid=str(user.uuid), panel_email=str(user.email)),
                ]
            )
            s.commit()
        finally:
            s.close()

        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        r = self.client.get("/api/user/1001", headers=user_hdrs)
        self.assertEqual(r.status_code, 200, r.text)
        nodes = r.json()["nodes"]
        self.assertEqual([row["code"] for row in nodes], ["brain", "it"])

    def test_dashboard_uses_runtime_summary_for_usage_and_connections(self) -> None:
        from db import SessionLocal
        from models import Node, ObserverUserState, User, UserNode

        gib = 1024 ** 3
        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_type = "PAID"
            user.current_plan_code = "1_month"
            user.total_gb = 50
            user.expiry_at = _utcnow() + timedelta(days=30)
            user.sub_token = "subtoken-paid-1001"
            it = Node(
                code="it",
                name="Italy",
                host="it.example.test",
                vless_port=443,
                reality_sni="www.tim.it",
                reality_pbk="pbk-it",
                reality_sid="sid-it",
                panel_base_url="https://it.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=1,
                enabled=True,
            )
            nl = Node(
                code="nl",
                name="Netherlands",
                host="nl.example.test",
                vless_port=443,
                reality_sni="www.kpn.com",
                reality_pbk="pbk-nl",
                reality_sid="sid-nl",
                panel_base_url="https://nl.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=1,
                enabled=True,
            )
            s.add_all([it, nl])
            s.flush()
            s.add_all(
                [
                    UserNode(tg_id=1001, node_id=it.id, client_uuid=str(user.uuid), panel_email=str(user.email)),
                    UserNode(tg_id=1001, node_id=nl.id, client_uuid=str(user.uuid), panel_email=str(user.email)),
                ]
            )
            s.add(
                ObserverUserState(
                    tg_id=1001,
                    state="watch",
                    observed_ip_count_24h=1,
                    observed_ip_count_7d=2,
                    observed_ip_count_30d=2,
                    observed_node_count_24h=1,
                    observed_node_count_7d=1,
                    observed_node_count_30d=1,
                    overlap_count_24h=0,
                )
            )
            s.commit()
        finally:
            s.close()

        class FakePanel:
            async def login(self):
                return True

            async def close(self):
                return True

            async def get_user_key_snapshots(self, *, tg_id: int, node_codes=None):
                self.tg_id = tg_id
                self.node_codes = node_codes or []
                return [
                    {
                        "node_code": "it",
                        "node_name": "Italy",
                        "node_host": "it.example.test",
                        "client": {"id": "it-client", "enable": True},
                        "runtime": {
                            "enable": True,
                            "online": True,
                            "up": gib,
                            "down": gib,
                            "total": 2 * gib,
                            "ip_count": 2,
                            "last_online_at": "2030-01-01T00:00:00Z",
                            "last_online_age_seconds": 30,
                        },
                        "error": "",
                    },
                    {
                        "node_code": "nl",
                        "node_name": "Netherlands",
                        "node_host": "nl.example.test",
                        "client": {"id": "nl-client", "enable": True},
                        "runtime": {
                            "enable": True,
                            "online": False,
                            "up": gib // 2,
                            "down": gib // 2,
                            "total": gib,
                            "ip_count": 0,
                            "last_online_at": "2030-01-01T00:10:00Z",
                            "last_online_age_seconds": 600,
                        },
                        "error": "",
                    },
                ]

        async def fake_legacy_usage(_tg_id: int):
            return None

        original_panel = self.api.ControlPanel
        original_legacy = self.api._get_panel_usage_legacy
        self.api.ControlPanel = FakePanel
        self.api._get_panel_usage_legacy = fake_legacy_usage
        try:
            hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
            r = self.client.get("/api/dashboard", headers=hdrs)
            self.assertEqual(r.status_code, 200, r.text)
            body = r.json()
            self.assertEqual(body["access_state"], "paid_unlimited")
            self.assertEqual(body["traffic_policy"]["kind"], "unlimited")
            self.assertIsNone(body["traffic_limit_gb"])
            self.assertIsNone(body["traffic_remaining_gb"])
            self.assertFalse(body["soft_mode_active"])
            self.assertEqual(body["used_gb"], 3.0)
            self.assertEqual(body["remaining_gb"], 0.0)
            self.assertEqual(body["active_sessions"], 2)
            self.assertEqual(body["active_sessions_source"], "panel_ip_count")
            self.assertEqual(body["connection_snapshot"]["active_connections"], 2)
            self.assertEqual(body["connection_snapshot"]["active_users_estimate"], 1)
            self.assertEqual(body["connection_snapshot"]["active_users_source"], "panel_ip_count_capped_by_unique_ip_24h")
            self.assertEqual(body["connection_snapshot"]["active_nodes"], 1)
            self.assertEqual(body["connection_snapshot"]["known_nodes"], 2)
            self.assertEqual(body["connection_snapshot"]["status"], "online")
        finally:
            self.api.ControlPanel = original_panel
            self.api._get_panel_usage_legacy = original_legacy

    def test_user_data_exposes_runtime_traffic_and_connections_without_app_install(self) -> None:
        from db import SessionLocal
        from models import Node, ObserverUserState, User, UserNode

        gib = 1024 ** 3
        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_type = "PAID"
            user.current_plan_code = "1_month"
            user.total_gb = 25
            user.expiry_at = _utcnow() + timedelta(days=14)
            user.app_install_id = None
            user.app_device_name = None
            user.sub_token = "subtoken-paid-1001"
            it = Node(
                code="it",
                name="Italy",
                host="it.example.test",
                vless_port=443,
                reality_sni="www.tim.it",
                reality_pbk="pbk-it",
                reality_sid="sid-it",
                panel_base_url="https://it.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=1,
                enabled=True,
            )
            s.add(it)
            s.flush()
            s.add(UserNode(tg_id=1001, node_id=it.id, client_uuid=str(user.uuid), panel_email=str(user.email)))
            s.add(
                ObserverUserState(
                    tg_id=1001,
                    state="watch",
                    observed_ip_count_24h=2,
                    observed_ip_count_7d=2,
                    observed_ip_count_30d=2,
                    observed_node_count_24h=1,
                    observed_node_count_7d=1,
                    observed_node_count_30d=1,
                    overlap_count_24h=0,
                )
            )
            s.commit()
        finally:
            s.close()

        class FakePanel:
            async def login(self):
                return True

            async def close(self):
                return True

            async def get_user_key_snapshots(self, *, tg_id: int, node_codes=None):
                return [
                    {
                        "node_code": "it",
                        "node_name": "Italy",
                        "node_host": "it.example.test",
                        "client": {"id": "it-client", "enable": True},
                        "runtime": {
                            "enable": True,
                            "online": True,
                            "up": gib,
                            "down": gib // 2,
                            "total": gib + (gib // 2),
                            "ip_count": 3,
                            "last_online_at": "2030-01-01T00:00:00Z",
                            "last_online_age_seconds": 15,
                        },
                        "error": "",
                    }
                ]

        async def fake_legacy_usage(_tg_id: int):
            return None

        original_panel = self.api.ControlPanel
        original_legacy = self.api._get_panel_usage_legacy
        self.api.ControlPanel = FakePanel
        self.api._get_panel_usage_legacy = fake_legacy_usage
        try:
            hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
            r = self.client.get("/api/user/1001", headers=hdrs)
            self.assertEqual(r.status_code, 200, r.text)
            body = r.json()
            self.assertEqual(body["access_state"], "paid_unlimited")
            self.assertEqual(body["traffic_policy"]["kind"], "unlimited")
            self.assertIsNone(body["traffic_limit_gb"])
            self.assertIsNone(body["traffic_remaining_gb"])
            self.assertEqual(body["devices"], [])
            self.assertEqual(int(body["sync"]["device_count"]), 0)
            self.assertEqual(body["traffic"]["source"], "panel_runtime")
            self.assertEqual(body["traffic"]["used_bytes"], gib + (gib // 2))
            self.assertAlmostEqual(body["traffic"]["used_gb"], 1.5, places=3)
            self.assertEqual(body["connections"]["active_connections"], 3)
            self.assertEqual(body["connections"]["active_users_estimate"], 2)
            self.assertEqual(body["connections"]["active_users_source"], "panel_ip_count_capped_by_unique_ip_24h")
            self.assertEqual(body["connections"]["active_nodes"], 1)
            self.assertEqual(body["connections"]["known_nodes"], 1)
            self.assertEqual(body["connections"]["status"], "online")
            self.assertEqual(body["connections"]["source"], "panel_runtime")
        finally:
            self.api.ControlPanel = original_panel
            self.api._get_panel_usage_legacy = original_legacy

    def test_dashboard_downgrades_expired_premium_to_free_monthly(self) -> None:
        from db import SessionLocal
        from models import NodeProvisioningJob, User

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_type = "PAID"
            user.current_plan_code = "1_month"
            user.expiry_at = _utcnow() - timedelta(days=1)
            user.is_active = True
            user.sub_token = "downgrade-token-1001"
            s.commit()
        finally:
            s.close()

        async def fake_runtime(*, s, user, nodes=None):
            return {
                "panel_state": "ok",
                "known_nodes": 0,
                "active_nodes": 0,
                "enabled_nodes": 0,
                "active_connections": 0,
                "active_connections_source": "none",
                "traffic_total_bytes": 0,
                "status": "unknown",
                "last_online_at": None,
                "last_online_age_seconds": None,
            }

        original_runtime = self.api._get_user_runtime_summary
        original_legacy = self.api._get_panel_usage_legacy
        self.api._get_user_runtime_summary = fake_runtime
        self.api._get_panel_usage_legacy = AsyncMock(return_value=None)
        try:
            hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
            response = self.client.get("/api/dashboard", headers=hdrs)
            self.assertEqual(response.status_code, 200, response.text)
            body = response.json()
            self.assertEqual(body["current_plan_code"], "free_monthly")
            self.assertEqual(body["access_state"], "free_monthly")
            self.assertEqual(body["traffic_policy"]["kind"], "metered")
            self.assertEqual(body["traffic_limit_gb"], 5.0)
            self.assertFalse(body["soft_mode_active"])
            self.assertTrue(body["next_reset_at"])
        finally:
            self.api._get_user_runtime_summary = original_runtime
            self.api._get_panel_usage_legacy = original_legacy

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            self.assertEqual(user.current_plan_code, "free_monthly")
            self.assertEqual(user.free_profile_state, "reset_pending")
            self.assertEqual(
                s.query(NodeProvisioningJob).filter_by(tg_id=1001, job_type="free_to_standard").count(),
                1,
            )
        finally:
            s.close()

    def test_dashboard_queues_soft_transition_but_does_not_claim_active_from_bytes(self) -> None:
        from db import SessionLocal
        from models import NodeProvisioningJob, User

        gib = 1024 ** 3
        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_type = "FREE"
            user.current_plan_code = "free_monthly"
            user.expiry_at = _utcnow() + timedelta(days=365)
            user.is_active = True
            user.sub_token = "free-soft-token-1001"
            user.free_cycle_next_reset_at = _utcnow() + timedelta(days=11)
            user.free_profile_state = "standard"
            user.free_profile_active_role = "free_standard"
            s.commit()
        finally:
            s.close()

        async def fake_runtime(*, s, user, nodes=None):
            return {
                "panel_state": "ok",
                "known_nodes": 1,
                "active_nodes": 1,
                "enabled_nodes": 1,
                "active_connections": 1,
                "active_connections_source": "panel_ip_count",
                "traffic_total_bytes": 6 * gib,
                "status": "online",
                "last_online_at": "2030-01-01T00:00:00Z",
                "last_online_age_seconds": 30,
            }

        original_runtime = self.api._get_user_runtime_summary
        original_legacy = self.api._get_panel_usage_legacy
        self.api._get_user_runtime_summary = fake_runtime
        self.api._get_panel_usage_legacy = AsyncMock(return_value=None)
        try:
            hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
            response = self.client.get("/api/dashboard", headers=hdrs)
            self.assertEqual(response.status_code, 200, response.text)
            body = response.json()
            self.assertEqual(body["access_state"], "free_monthly")
            self.assertEqual(body["traffic_policy"]["kind"], "metered")
            self.assertEqual(body["traffic_limit_gb"], 5.0)
            self.assertEqual(body["traffic_remaining_gb"], 0.0)
            self.assertFalse(body["soft_mode_active"])
            self.assertEqual(body["free_profile_state"], "soft_transition_pending")
            self.assertEqual(body["free_profile_active_role"], "free_standard")
            self.assertEqual(body["free_caps"]["transition_state"], "soft_transition_pending")
            self.assertEqual(body["free_caps"]["active_role"], "free_standard")
            self.assertTrue(body["next_reset_at"])

            replay = self.client.get("/api/dashboard", headers=hdrs)
            self.assertEqual(replay.status_code, 200, replay.text)
        finally:
            self.api._get_user_runtime_summary = original_runtime
            self.api._get_panel_usage_legacy = original_legacy

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).one()
            self.assertEqual(user.free_profile_state, "soft_transition_pending")
            self.assertEqual(
                s.query(NodeProvisioningJob).filter_by(tg_id=1001, job_type="free_to_soft").count(),
                1,
            )
        finally:
            s.close()

    def test_dashboard_soft_active_legacy_remaining_stays_zero_on_fresh_counter(self) -> None:
        from db import SessionLocal
        from models import User

        gib = 1024 ** 3
        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).one()
            user.sub_type = "FREE"
            user.current_plan_code = "free_monthly"
            user.expiry_at = _utcnow() + timedelta(days=365)
            user.is_active = True
            user.free_profile_state = "soft_active"
            user.free_profile_active_role = "free_soft"
            user.free_profile_observed_bytes = 5 * gib
            s.commit()
        finally:
            s.close()

        async def fake_runtime(*, s, user, nodes=None):
            return {
                "panel_state": "ok",
                "known_nodes": 1,
                "active_nodes": 1,
                "enabled_nodes": 1,
                "active_connections": 1,
                "active_connections_source": "panel_ip_count",
                "traffic_total_bytes": gib // 16,
                "status": "online",
                "last_online_at": "2030-01-01T00:00:00Z",
                "last_online_age_seconds": 30,
            }

        original_runtime = self.api._get_user_runtime_summary
        original_legacy = self.api._get_panel_usage_legacy
        self.api._get_user_runtime_summary = fake_runtime
        self.api._get_panel_usage_legacy = AsyncMock(return_value=None)
        try:
            hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
            response = self.client.get("/api/dashboard", headers=hdrs)
            self.assertEqual(response.status_code, 200, response.text)
            body = response.json()
            self.assertEqual(body["access_state"], "free_soft_mode")
            self.assertTrue(body["soft_mode_active"])
            self.assertEqual(body["remaining_gb"], 0.0)
            self.assertEqual(body["traffic_remaining_gb"], 0.0)
        finally:
            self.api._get_user_runtime_summary = original_runtime
            self.api._get_panel_usage_legacy = original_legacy

    def test_admin_node_disable_requires_resync_when_mapped_users_exist(self) -> None:
        from db import SessionLocal
        from models import Node, UserNode

        s = SessionLocal()
        try:
            node = Node(
                code="pl",
                name="Poland",
                host="pl.example.test",
                vless_port=443,
                reality_sni="www.orange.pl",
                reality_pbk="pbk-pl",
                reality_sid="sid-pl",
                panel_base_url="https://pl.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=1,
                enabled=True,
            )
            s.add(node)
            s.flush()
            s.add(UserNode(tg_id=1001, node_id=node.id, client_uuid="uuid-1001", panel_email="user_1001"))
            s.commit()
        finally:
            s.close()

        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        r = self.client.post("/api/admin/nodes/pl/disable", headers=admin_hdrs, json={})
        self.assertEqual(r.status_code, 428, r.text)
        self.assertEqual(r.json()["detail"]["code"], "intent_required")
        guarded = self._execute_node_intent(action="node.disable", node_code="pl", payload={"force": False})
        self.assertEqual(guarded.status_code, 409, guarded.text)
        self.assertEqual(guarded.json()["detail"]["code"], "node_has_mapped_users")

    def test_admin_node_resync_moves_mapping_off_draining_node(self) -> None:
        from db import SessionLocal
        from models import Node, User, UserNode

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_type = "PAID"
            user.current_plan_code = "1_month"
            user.sub_token = "subtoken-paid-1001"
            source = Node(
                code="pl",
                name="Poland",
                host="pl.example.test",
                vless_port=443,
                reality_sni="www.orange.pl",
                reality_pbk="pbk-pl",
                reality_sid="sid-pl",
                panel_base_url="https://pl.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=1,
                enabled=True,
            )
            target = Node(
                code="it",
                name="Italy",
                host="it.example.test",
                vless_port=443,
                reality_sni="www.tim.it",
                reality_pbk="pbk-it",
                reality_sid="sid-it",
                panel_base_url="https://it.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=1,
                enabled=True,
            )
            s.add_all([source, target])
            s.flush()
            s.add(UserNode(tg_id=1001, node_id=source.id, client_uuid=str(user.uuid), panel_email=str(user.email)))
            s.commit()
        finally:
            s.close()

        class FakePanel:
            async def login(self):
                return True

            async def close(self):
                return True

            async def ensure_user_on_all_nodes(self, **kwargs):
                self.ensure_kwargs = kwargs
                return {"it": True}

            async def set_existing_user_enabled_on_nodes(self, **kwargs):
                self.disable_kwargs = kwargs
                return {"pl": True}

        original_panel = self.api.ControlPanel
        self.api.ControlPanel = FakePanel
        try:
            drained = self._execute_node_intent(action="node.drain", node_code="pl", payload={"force": False})
            self.assertEqual(drained.status_code, 200, drained.text)
            resync = self._execute_node_intent(
                action="node.resync",
                node_code="pl",
                payload={"limit": 50, "dry_run": False},
            )
            self.assertEqual(resync.status_code, 200, resync.text)
            self.assertEqual(int((resync.json().get("result") or {}).get("changed") or 0), 1)
        finally:
            self.api.ControlPanel = original_panel

        from db import SessionLocal
        from models import UserNode

        s = SessionLocal()
        try:
            rows = s.query(UserNode).filter(UserNode.tg_id == 1001).all()
            node_ids = sorted(int(row.node_id) for row in rows)
            self.assertEqual(len(node_ids), 1)
        finally:
            s.close()

    def test_admin_nodes_health_exposes_resource_metrics(self) -> None:
        from db import SessionLocal
        from models import Node

        s = SessionLocal()
        try:
            node = Node(
                code="nl",
                name="Netherlands",
                host="nl.example.test",
                vless_port=443,
                reality_sni="www.kpn.com",
                reality_pbk="pbk-nl",
                reality_sid="sid-nl",
                panel_base_url="https://nl.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=1,
                enabled=True,
                health_score=96.2,
                panel_latency_ms=88,
                panel_error_rate=0.0,
                active_clients=21,
                cpu_percent=37.5,
                memory_used_mb=1240,
                memory_total_mb=2048,
                disk_used_gb=11.4,
                disk_total_gb=40.0,
                disk_free_gb=28.6,
                hoster_family="hetzner",
                hoster_asn="AS24940",
                hoster_subnet="5.45.84.0/24",
                ipv4_health="healthy",
                ipv6_health="degraded",
                last_probe_classification="provider_specific_path",
                transport_profiles_json='{"legacy_reality_fallback":{"enabled":true},"grpc_443_primary":{"enabled":true}}',
                transport_health_json=json.dumps(
                    {
                        "dns_resolution": "healthy",
                        "tcp_connect": "healthy",
                        "tls_handshake": "degraded",
                        "reality_target": "healthy",
                        "panel_state": "healthy",
                        "dataplane_state": "healthy",
                        "endpoint": "forbidden-legacy-endpoint.invalid",
                        "tls_server_name": "forbidden-legacy-sni.invalid",
                        "peer_ip": "198.51.100.123",
                        "certificate": "forbidden-legacy-certificate",
                        "raw_exception": "forbidden-legacy-exception",
                        "token": "forbidden-legacy-token",
                    }
                ),
                last_probe_stage="tls_sni",
                last_probe_error_kind="tls_handshake_failed",
                last_probe_error_message="forbidden-legacy-error-message",
            )
            s.add(node)
            s.commit()
        finally:
            s.close()

        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        r = self.client.get("/api/admin/nodes/health", headers=admin_hdrs)
        self.assertEqual(r.status_code, 200, r.text)
        rows = r.json()["nodes"]
        item = next(row for row in rows if row["code"] == "nl")
        self.assertEqual(item["cpu_percent"], 37.5)
        self.assertEqual(item["memory_used_mb"], 1240)
        self.assertEqual(item["memory_total_mb"], 2048)
        self.assertEqual(item["disk_used_gb"], 11.4)
        self.assertEqual(item["disk_total_gb"], 40.0)
        self.assertEqual(item["disk_free_gb"], 28.6)
        self.assertEqual(item["last_probe_stage"], "tls_sni")
        self.assertEqual(item["last_probe_error_kind"], "tls_handshake_failed")
        self.assertEqual(item["last_probe_error_message"], "tls_handshake_failed")
        self.assertEqual(item["hoster_family"], "hetzner")
        self.assertEqual(item["hoster_asn"], "AS24940")
        self.assertNotIn("subnet", item)
        self.assertEqual(item["ipv4_health"], "healthy")
        self.assertEqual(item["ipv6_health"], "degraded")
        self.assertEqual(item["probe_classification"], "provider_specific_path")
        self.assertEqual(item["transport_health"]["tls_handshake"], "degraded")
        rendered = json.dumps(item, sort_keys=True)
        for forbidden in (
            "forbidden-legacy-endpoint.invalid",
            "forbidden-legacy-sni.invalid",
            "198.51.100.123",
            "forbidden-legacy-certificate",
            "forbidden-legacy-exception",
            "forbidden-legacy-token",
            "forbidden-legacy-error-message",
            "5.45.84.0/24",
        ):
            self.assertNotIn(forbidden, rendered)
        if "transport_profiles" in item:
            self.assertTrue(item["transport_profiles"]["legacy_reality_fallback"]["enabled"])
            self.assertTrue(item["transport_profiles"]["grpc_443_primary"]["enabled"])

    def test_admin_nodes_health_exposes_probe_failure_fields_and_alerts(self) -> None:
        from db import SessionLocal
        from models import Node

        now = _utcnow()
        s = SessionLocal()
        try:
            node = Node(
                code="de",
                name="Germany",
                host="de.example.test",
                vless_port=443,
                reality_sni="www.telekom.de",
                reality_pbk="pbk-de",
                reality_sid="sid-de",
                panel_base_url="https://de.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=1,
                enabled=True,
                health_score=44.0,
                is_healthy=False,
                panel_latency_ms=1800,
                panel_error_rate=0.31,
                active_clients=220,
                cpu_percent=91.0,
                memory_used_mb=1940,
                memory_total_mb=2048,
                disk_used_gb=38.0,
                disk_total_gb=40.0,
                disk_free_gb=2.0,
                last_health_at=now - timedelta(hours=2),
                last_probe_at=now - timedelta(hours=2),
                last_probe_stage="tls_sni",
                last_probe_error_kind="tls_timeout",
                last_probe_error_message="tls handshake timeout",
            )
            s.add(node)
            s.commit()
        finally:
            s.close()

        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        r = self.client.get("/api/admin/nodes/health", headers=admin_hdrs)
        self.assertEqual(r.status_code, 200, r.text)
        item = next(row for row in r.json()["nodes"] if row["code"] == "de")
        self.assertEqual(item["last_probe_stage"], "tls_sni")
        self.assertIsNone(item["last_probe_error_kind"])
        self.assertIsNone(item["last_probe_error_message"])
        self.assertEqual(item["freshness_status"], "stale")
        self.assertIn("high_cpu", item["alerts"])
        self.assertIn("high_memory", item["alerts"])
        self.assertIn("high_disk", item["alerts"])
        self.assertIn("high_client_density", item["alerts"])
        self.assertIn("high_latency", item["alerts"])
        self.assertIn("high_error_rate", item["alerts"])

    def test_admin_metrics_status_reports_per_node_staleness_and_alerts(self) -> None:
        from db import SessionLocal
        from models import Node

        now = _utcnow()
        s = SessionLocal()
        try:
            s.add_all(
                [
                    Node(
                        code="pl",
                        name="Poland",
                        host="pl.example.test",
                        vless_port=443,
                        reality_sni="www.orange.pl",
                        reality_pbk="pbk-pl",
                        reality_sid="sid-pl",
                        panel_base_url="https://pl.example.test:8444",
                        panel_path="/panel",
                        panel_user="admin",
                        panel_pass="pass",
                        inbound_id=1,
                        enabled=True,
                        is_healthy=True,
                        cpu_percent=78.0,
                        memory_used_mb=900,
                        memory_total_mb=2048,
                        disk_used_gb=10.0,
                        disk_total_gb=40.0,
                        active_clients=45,
                        last_health_at=now - timedelta(minutes=5),
                        last_probe_at=now - timedelta(minutes=5),
                    ),
                    Node(
                        code="it",
                        name="Italy",
                        host="it.example.test",
                        vless_port=443,
                        reality_sni="www.tim.it",
                        reality_pbk="pbk-it",
                        reality_sid="sid-it",
                        panel_base_url="https://it.example.test:8444",
                        panel_path="/panel",
                        panel_user="admin",
                        panel_pass="pass",
                        inbound_id=1,
                        enabled=True,
                        is_healthy=True,
                        cpu_percent=12.0,
                        memory_used_mb=300,
                        memory_total_mb=2048,
                        disk_used_gb=5.0,
                        disk_total_gb=40.0,
                        active_clients=12,
                        last_health_at=now - timedelta(hours=3),
                        last_probe_at=now - timedelta(hours=3),
                    ),
                ]
            )
            s.commit()
        finally:
            s.close()

        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        r = self.client.get("/api/admin/metrics/status", headers=admin_hdrs)
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["status"], "stale")
        self.assertEqual(int(body["alerts"]["stale_nodes"]), 1)
        self.assertEqual(int(body["alerts"]["high_cpu_nodes"]), 1)
        rows = {row["code"]: row for row in body["node_statuses"]}
        self.assertEqual(rows["pl"]["freshness_status"], "fresh")
        self.assertIn("high_cpu", rows["pl"]["alerts"])
        self.assertEqual(rows["it"]["freshness_status"], "stale")
        self.assertIn("stale_metrics", rows["it"]["alerts"])

    def test_api_events_accepts_extended_user_metric_events(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        r = self.client.post(
            "/api/events",
            headers=user_hdrs,
            json={"event_name": "config_import_failed", "source": "app", "meta": {"reason": "bad_qr"}},
        )
        self.assertEqual(r.status_code, 200, r.text)
        rows = self._event_rows("config_import_failed")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["meta"]["reason"], "bad_qr")

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

    def test_web_login_rejects_expired_payload_with_reauth_message(self) -> None:
        payload = self._telegram_login_payload(
            1001,
            "alice",
            auth_date=int(time.time()) - int(self.api.TELEGRAM_WEB_LOGIN_MAX_AGE_SECONDS) - 5,
        )

        r = self.client.post("/api/auth/telegram/web-login", json=payload)

        self.assertEqual(r.status_code, 401, r.text)
        self.assertEqual(r.headers.get("x-pokrov-auth-error"), "telegram_login_expired")
        self.assertIn("Сессия Telegram устарела", str(r.json().get("detail") or ""))

    def test_auth_session_prefers_valid_web_session_when_telegram_header_is_stale(self) -> None:
        token = self.api.create_web_session_token(tg_id=1001, username="alice")

        r = self.client.get(
            "/api/auth/session",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Telegram-Init-Data": "deprecated=1&hash=bad",
            },
        )

        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(int(r.json().get("user", {}).get("id", 0)), 1001)

    def test_auth_session_uses_telegram_init_data_when_web_session_is_expired(self) -> None:
        token = self.api.create_web_session_token(tg_id=1001, username="alice")

        with patch("web_auth_service.time.time", return_value=time.time() + int(self.api.SESSION_TTL_SECONDS) + 5):
            r = self.client.get(
                "/api/auth/session",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Telegram-Init-Data": self._init_data(1001, "alice"),
                },
            )

        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(int(r.json().get("user", {}).get("id", 0)), 1001)

    def test_auth_session_rejects_expired_web_session_with_reauth_message(self) -> None:
        token = self.api.create_web_session_token(tg_id=1001, username="alice")

        with patch("web_auth_service.time.time", return_value=time.time() + int(self.api.SESSION_TTL_SECONDS) + 5):
            r = self.client.get("/api/auth/session", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(r.status_code, 401, r.text)
        self.assertEqual(r.headers.get("x-pokrov-auth-error"), "web_session_expired")
        self.assertIn("Сессия в браузере устарела", str(r.json().get("detail") or ""))

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

        reply = self._execute_admin_intent(
            action="ticket.reply",
            target_type="ticket",
            target_id=ticket_id,
            method="POST",
            path=f"/api/admin/tickets/{ticket_id}/reply",
            payload={"body": "Проверили, уже исправлено"},
        )
        self.assertEqual(reply.status_code, 200, reply.text)
        self.assertEqual(reply.json()["ticket"]["status"], "in_progress")

    def test_ticket_create_appends_ai_hint_when_enabled(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        from support_agent_service import SupportReplyResult

        async def fake_generate(*, surface, authenticated_owner_id, message, assistant_session_id=None, ticket_id=None, validated_sender_id=None):
            self.assertEqual(surface, "ticket")
            self.assertEqual(authenticated_owner_id, "1001")
            self.assertEqual(message, "How do I start the trial?")
            self.assertGreater(ticket_id, 0)
            self.assertIsNone(assistant_session_id)
            self.assertIsNone(validated_sender_id)
            return SupportReplyResult(
                reply="Откройте приложение POKROV и нажмите Try free.",
                assistant_session_id="stable-ticket-session-id",
                suggested_actions=(),
                should_escalate=False,
                source="support_agent",
            )

        self.api.SUPPORT_AI_CONFIG.enabled = True
        self.api.SUPPORT_AI_CONFIG.api_key = "sk-test"
        self.api.SUPPORT_AI_CONFIG.min_interval_seconds = 0

        with patch.object(self.api.SUPPORT_AGENT_SERVICE, "generate", side_effect=fake_generate), patch.object(
            self.api, "_telegram_send_message", new_callable=AsyncMock
        ):
            create = self.client.post(
                "/api/tickets",
                headers=user_hdrs,
                json={"subject": "Trial", "body": "How do I start the trial?"},
            )

        self.assertEqual(create.status_code, 200, create.text)
        messages = create.json()["ticket"]["messages"]
        self.assertEqual([message["sender_role"] for message in messages], ["user", "assistant"])
        self.assertIn("Try free", messages[-1]["body"])

    def test_ticket_followup_appends_ai_hint_for_user_messages_only(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        from support_agent_service import SupportReplyResult

        create = self.client.post(
            "/api/tickets",
            headers=user_hdrs,
            json={"subject": "Connection", "body": "Initial issue"},
        )
        self.assertEqual(create.status_code, 200, create.text)
        ticket_id = create.json()["ticket"]["id"]

        async def fake_generate(*, surface, authenticated_owner_id, message, assistant_session_id=None, ticket_id=None, validated_sender_id=None):
            self.assertEqual(surface, "ticket")
            self.assertEqual(authenticated_owner_id, "1001")
            self.assertEqual(message, "Connection is slow")
            self.assertGreater(ticket_id, 0)
            self.assertIsNone(assistant_session_id)
            self.assertIsNone(validated_sender_id)
            return SupportReplyResult(
                reply="Попробуйте обновить профиль и выбрать другое направление.",
                assistant_session_id="stable-ticket-session-id",
                suggested_actions=(),
                should_escalate=False,
                source="support_agent",
            )

        self.api.SUPPORT_AI_CONFIG.enabled = True
        self.api.SUPPORT_AI_CONFIG.api_key = "sk-test"
        self.api.SUPPORT_AI_CONFIG.min_interval_seconds = 0

        with patch.object(self.api.SUPPORT_AGENT_SERVICE, "generate", side_effect=fake_generate) as ai_call, patch.object(
            self.api, "_telegram_send_message", new_callable=AsyncMock
        ):
            user_reply = self.client.post(
                f"/api/tickets/{ticket_id}/messages",
                headers=user_hdrs,
                json={"body": "Connection is slow"},
            )
            admin_reply = self.client.post(
                f"/api/tickets/{ticket_id}/messages",
                headers=admin_hdrs,
                json={"body": "Operator reply"},
            )

        self.assertEqual(user_reply.status_code, 200, user_reply.text)
        self.assertEqual(admin_reply.status_code, 200, admin_reply.text)
        self.assertEqual(ai_call.call_count, 1)
        messages = admin_reply.json()["ticket"]["messages"]
        self.assertEqual([message["sender_role"] for message in messages], ["user", "user", "assistant", "admin"])

    def test_ticket_upload_returns_private_attachment_metadata_and_requires_auth(self) -> None:
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
        self.assertTrue(file_url.startswith("/api/tickets/attachments/"))
        self.assertTrue(payload["private"])

        fetched = self.client.get(file_url)
        self.assertEqual(fetched.status_code, 401, fetched.text)

        fetched = self.client.get(file_url, headers=user_hdrs)
        self.assertEqual(fetched.status_code, 200, fetched.text)
        self.assertEqual(fetched.headers.get("content-type"), "image/png")
        self.assertEqual(fetched.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(fetched.content, b"\x89PNG\r\n\x1a\nbinary-test")

    def test_ticket_upload_stages_opaque_id_with_default_expiry(self) -> None:
        from db import SessionLocal
        from models import SupportAttachment

        headers = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        before = _utcnow()
        response = self._upload_support_attachment(headers)

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        attachment_id = str(payload.get("attachment_id") or "")
        self.assertTrue(attachment_id)
        self.assertEqual(
            payload["attachment_payload"]["url"],
            f"/api/tickets/attachments/{attachment_id}",
        )
        self.assertEqual(payload["attachment"]["media_file_id"], f"support/{attachment_id}")

        session = SessionLocal()
        try:
            row = session.query(SupportAttachment).filter_by(stored_name=attachment_id).one()
            self.assertIsNone(row.ticket_id)
            self.assertIsNone(row.message_id)
            self.assertIsNone(row.attached_at)
            self.assertGreaterEqual(row.expires_at, before + timedelta(hours=23, minutes=59))
            self.assertLessEqual(row.expires_at, before + timedelta(hours=24, minutes=1))
        finally:
            session.close()

    def test_ticket_upload_cleanup_and_pending_quota_boundaries(self) -> None:
        from db import SessionLocal
        from models import Account, SecurityEvent, SupportAttachment, User

        headers = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        upload_dir = Path(self.api.SUPPORT_UPLOAD_DIR)
        now = _utcnow()
        session = SessionLocal()
        try:
            account = Account(id="attachment-quota-account", status="active", created_source="test")
            session.add(account)
            session.query(User).filter_by(tg_id=1001).one().account_id = account.id
            rows = [
                SupportAttachment(
                    stored_name="20260714-expiredrow.txt",
                    owner_tg_id=1001,
                    owner_account_id=account.id,
                    original_name="expired.txt",
                    content_type="text/plain",
                    size_bytes=7,
                    media_type="file",
                    expires_at=now - timedelta(minutes=1),
                    created_at=now - timedelta(hours=25),
                ),
                SupportAttachment(
                    stored_name="20260714-legacyrow.txt",
                    owner_tg_id=1001,
                    owner_account_id=None,
                    original_name="legacy.txt",
                    content_type="text/plain",
                    size_bytes=6,
                    media_type="file",
                    expires_at=None,
                    created_at=now - timedelta(days=30),
                ),
                SupportAttachment(
                    stored_name="20260714-boundrow.txt",
                    owner_tg_id=1001,
                    owner_account_id=account.id,
                    original_name="bound.txt",
                    content_type="text/plain",
                    size_bytes=5,
                    media_type="file",
                    ticket_id=77,
                    message_id=88,
                    expires_at=now - timedelta(minutes=1),
                    created_at=now - timedelta(hours=25),
                ),
                SupportAttachment(
                    stored_name="20260714-otherowner.txt",
                    owner_tg_id=2002,
                    owner_account_id="other-attachment-owner",
                    original_name="other-owner.txt",
                    content_type="text/plain",
                    size_bytes=11,
                    media_type="file",
                    expires_at=now - timedelta(minutes=1),
                    created_at=now - timedelta(hours=25),
                ),
                SupportAttachment(
                    stored_name="nested/20260714-otherowner.txt",
                    owner_tg_id=1001,
                    owner_account_id=account.id,
                    original_name="malformed.txt",
                    content_type="text/plain",
                    size_bytes=9,
                    media_type="file",
                    expires_at=now - timedelta(minutes=1),
                    created_at=now - timedelta(hours=25),
                ),
            ]
            session.add_all(rows)
            session.commit()
        finally:
            session.close()
        for name in (
            "20260714-expiredrow.txt",
            "20260714-legacyrow.txt",
            "20260714-boundrow.txt",
            "20260714-otherowner.txt",
        ):
            (upload_dir / name).write_bytes(name.encode("ascii"))

        with patch.object(self.api, "SUPPORT_PENDING_UPLOAD_MAX_COUNT", 5), patch.object(
            self.api, "SUPPORT_PENDING_UPLOAD_MAX_BYTES", 50 * 1024 * 1024
        ):
            accepted = self._upload_support_attachment(headers, name="fresh.txt", content=b"fresh")
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertFalse((upload_dir / "20260714-expiredrow.txt").exists())
        self.assertTrue((upload_dir / "20260714-legacyrow.txt").exists())
        self.assertTrue((upload_dir / "20260714-boundrow.txt").exists())
        self.assertTrue((upload_dir / "20260714-otherowner.txt").exists())

        with patch.object(self.api, "SUPPORT_PENDING_UPLOAD_MAX_COUNT", 1):
            count_limited = self._upload_support_attachment(headers, name="over-count.txt", content=b"x")
        self.assertEqual(count_limited.status_code, 429, count_limited.text)

        with patch.object(self.api, "SUPPORT_PENDING_UPLOAD_MAX_COUNT", 5), patch.object(
            self.api, "SUPPORT_PENDING_UPLOAD_MAX_BYTES", 5
        ):
            bytes_limited = self._upload_support_attachment(headers, name="over-bytes.txt", content=b"x")
        self.assertEqual(bytes_limited.status_code, 429, bytes_limited.text)

        session = SessionLocal()
        try:
            names = {row.stored_name for row in session.query(SupportAttachment).all()}
        finally:
            session.close()
        self.assertNotIn("20260714-expiredrow.txt", names)
        self.assertIn("20260714-legacyrow.txt", names)
        self.assertIn("20260714-boundrow.txt", names)
        self.assertIn("20260714-otherowner.txt", names)
        session = SessionLocal()
        try:
            reasons = [
                row.reason
                for row in session.query(SecurityEvent)
                .filter(SecurityEvent.event_type == "support_upload_reject")
                .order_by(SecurityEvent.id.asc())
                .all()
            ]
        finally:
            session.close()
        self.assertEqual(reasons, ["pending_count_quota", "pending_bytes_quota"])

    def test_ticket_upload_rejection_telemetry_is_single_bounded_and_redacted(self) -> None:
        from db import SessionLocal
        from models import SecurityEvent

        headers = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        marker = "private-filename-marker"

        unsupported = self.client.post(
            "/api/tickets/uploads",
            headers={
                **headers,
                "Content-Type": "application/octet-stream",
                "X-Upload-Filename": f"{marker}.bin",
            },
            content=b"private-body-marker",
        )
        self.assertEqual(unsupported.status_code, 400, unsupported.text)

        session = SessionLocal()
        try:
            rows = (
                session.query(SecurityEvent)
                .filter(SecurityEvent.event_type == "support_upload_reject")
                .order_by(SecurityEvent.id.asc())
                .all()
            )
            self.assertEqual([row.reason for row in rows], ["unsupported_type"])
            serialized = "\n".join(f"{row.reason}\n{row.meta_json or ''}" for row in rows)
            self.assertNotIn(marker, serialized)
            self.assertNotIn("private-body-marker", serialized)
        finally:
            session.close()

        with patch.object(self.api, "SUPPORT_UPLOAD_MAX_BYTES", 3):
            oversized = self.client.post(
                "/api/tickets/uploads",
                headers={
                    **headers,
                    "Content-Type": "text/plain",
                    "X-Upload-Filename": f"{marker}.txt",
                },
                content=b"oversized-private-body",
            )
        self.assertEqual(oversized.status_code, 413, oversized.text)

        session = SessionLocal()
        try:
            rows = (
                session.query(SecurityEvent)
                .filter(SecurityEvent.event_type == "support_upload_reject")
                .order_by(SecurityEvent.id.asc())
                .all()
            )
            self.assertEqual([row.reason for row in rows], ["unsupported_type", "body_too_large"])
            serialized = "\n".join(f"{row.reason}\n{row.meta_json or ''}" for row in rows)
            self.assertNotIn(marker, serialized)
            self.assertNotIn("oversized-private-body", serialized)
        finally:
            session.close()

    def _run_concurrent_pending_uploads(
        self,
        *,
        owners: tuple[tuple[int, str | None], tuple[int, str | None]],
        payloads: tuple[bytes, bytes],
        max_count: int,
        max_bytes: int,
    ) -> tuple[list[tuple[str, int | str]], int]:
        from fastapi import HTTPException
        from sqlalchemy.orm import Query

        barrier = threading.Barrier(2)
        arrivals = 0
        arrivals_lock = threading.Lock()
        original_one = Query.one

        def coordinated_one(query):
            nonlocal arrivals
            statement = str(query.statement).lower()
            if "support_attachments" in statement and "count(" in statement:
                with arrivals_lock:
                    arrivals += 1
                try:
                    barrier.wait(timeout=0.4)
                except threading.BrokenBarrierError:
                    pass
            return original_one(query)

        def store(index: int) -> tuple[str, int | str]:
            owner_tg_id, owner_account_id = owners[index]
            try:
                self.api._store_support_upload(
                    owner_tg_id=owner_tg_id,
                    owner_account_id=owner_account_id,
                    filename=f"concurrent-{index}.txt",
                    content_type="text/plain",
                    raw_bytes=payloads[index],
                )
                return ("ok", 200)
            except HTTPException as exc:
                return ("http", int(exc.status_code))
            except Exception as exc:  # The RED path may expose a SQLite write race.
                return ("error", type(exc).__name__)

        with patch.object(self.api, "SUPPORT_PENDING_UPLOAD_MAX_COUNT", max_count), patch.object(
            self.api, "SUPPORT_PENDING_UPLOAD_MAX_BYTES", max_bytes
        ), patch.object(Query, "one", new=coordinated_one):
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(store, (0, 1)))
        return results, arrivals

    def test_concurrent_pending_upload_count_is_serialized_by_canonical_account(self) -> None:
        results, arrivals = self._run_concurrent_pending_uploads(
            owners=((1001, "shared-quota-owner"), (1002, "shared-quota-owner")),
            payloads=(b"one", b"two"),
            max_count=1,
            max_bytes=1024,
        )

        self.assertEqual(sorted(results), [("http", 429), ("ok", 200)])
        self.assertEqual(arrivals, 2)

    def test_concurrent_pending_upload_bytes_are_serialized_by_legacy_tg_owner(self) -> None:
        results, arrivals = self._run_concurrent_pending_uploads(
            owners=((1001, None), (1001, None)),
            payloads=(b"abc", b"def"),
            max_count=5,
            max_bytes=5,
        )

        self.assertEqual(sorted(results), [("http", 429), ("ok", 200)])
        self.assertEqual(arrivals, 2)

    def test_pending_upload_owner_keys_and_advisory_keys_keep_distinct_owners_separate(self) -> None:
        shared_from_first_tg = self.api._support_upload_owner_key(
            owner_tg_id=1001,
            owner_account_id="shared",
        )
        shared_from_second_tg = self.api._support_upload_owner_key(
            owner_tg_id=1002,
            owner_account_id="shared",
        )
        other_account = self.api._support_upload_owner_key(
            owner_tg_id=1001,
            owner_account_id="other",
        )
        legacy_owner = self.api._support_upload_owner_key(owner_tg_id=1001, owner_account_id=None)

        self.assertEqual(shared_from_first_tg, shared_from_second_tg)
        self.assertEqual(len(self.api._SUPPORT_UPLOAD_OWNER_LOCKS), 256)
        self.assertIsInstance(self.api._SUPPORT_UPLOAD_OWNER_LOCKS, tuple)
        advisory_keys = {
            self.api._support_upload_advisory_lock_key(owner_key)
            for owner_key in (shared_from_first_tg, other_account, legacy_owner)
        }
        self.assertEqual(len(advisory_keys), 3)

    def test_pending_upload_postgres_uses_transaction_advisory_owner_lock(self) -> None:
        class _Session:
            def __init__(self, dialect_name: str):
                self.bind = SimpleNamespace(dialect=SimpleNamespace(name=dialect_name))
                self.calls: list[tuple[str, dict[str, int]]] = []

            def execute(self, statement, params):
                self.calls.append((str(statement), dict(params)))

        postgres = _Session("postgresql")
        sqlite = _Session("sqlite")

        self.api._lock_support_upload_owner_in_db(postgres, "account:shared")
        self.api._lock_support_upload_owner_in_db(sqlite, "account:shared")

        self.assertEqual(len(postgres.calls), 1)
        self.assertIn("pg_advisory_xact_lock", postgres.calls[0][0])
        self.assertIsInstance(postgres.calls[0][1]["lock_key"], int)
        self.assertEqual(sqlite.calls, [])

    def test_pending_upload_db_owner_lock_is_reacquired_after_cleanup_commit(self) -> None:
        from db import SessionLocal

        sessions = []
        lock_boundaries: list[int] = []
        boundary_events: list[str] = []

        class _RecordingSession:
            def __init__(self, inner):
                self._inner = inner
                self.commit_count = 0

            def commit(self):
                self._inner.commit()
                self.commit_count += 1
                boundary_events.append(f"commit:{self.commit_count}")

            def query(self, *entities, **kwargs):
                if any("count(" in str(entity).lower() for entity in entities):
                    boundary_events.append(f"quota:{self.commit_count}")
                return self._inner.query(*entities, **kwargs)

            def __getattr__(self, name):
                return getattr(self._inner, name)

        def session_factory():
            session = _RecordingSession(SessionLocal())
            sessions.append(session)
            return session

        def record_lock(session, _owner_key: str):
            lock_boundaries.append(session.commit_count)
            boundary_events.append(f"lock:{session.commit_count}")

        with patch.object(self.api, "SessionLocal", new=session_factory), patch.object(
            self.api, "_lock_support_upload_owner_in_db", new=record_lock
        ):
            self.api._store_support_upload(
                owner_tg_id=1001,
                owner_account_id="lock-order-owner",
                filename="lock-order.txt",
                content_type="text/plain",
                raw_bytes=b"lock order",
            )

        self.assertEqual(lock_boundaries, [0, 1])
        self.assertEqual(sessions[0].commit_count, 2)
        self.assertEqual(
            boundary_events,
            ["lock:0", "commit:1", "lock:1", "quota:1", "commit:2"],
        )

    def test_attachment_id_binds_create_and_reply_with_conflict_and_owner_checks(self) -> None:
        from db import SessionLocal
        from models import SupportAttachment, SupportTicketMessage, User

        alice = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        admin = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        first_upload = self._upload_support_attachment(alice, name="create.txt", content=b"create payload")
        self.assertEqual(first_upload.status_code, 200, first_upload.text)
        first_id = first_upload.json()["attachment_id"]

        created = self.client.post(
            "/api/tickets",
            headers=alice,
            json={"subject": "Private", "body": "Create with staged file", "attachment_id": first_id},
        )
        self.assertEqual(created.status_code, 200, created.text)
        ticket = created.json()["ticket"]
        ticket_id = int(ticket["id"])
        message = ticket["messages"][-1]
        self.assertEqual(message["media_file_id"], f"support/{first_id}")
        self.assertEqual(json.loads(message["media_payload"])["name"], "create.txt")

        second_upload = self._upload_support_attachment(alice, name="reply.txt", content=b"reply payload")
        second_id = second_upload.json()["attachment_id"]
        replied = self.client.post(
            f"/api/tickets/{ticket_id}/messages",
            headers=alice,
            json={"body": "Reply with staged file", "attachment_id": second_id},
        )
        self.assertEqual(replied.status_code, 200, replied.text)

        before_count = len(replied.json()["ticket"]["messages"])
        duplicate = self.client.post(
            f"/api/tickets/{ticket_id}/messages",
            headers=alice,
            json={"body": "Must roll back", "attachment_id": second_id},
        )
        self.assertEqual(duplicate.status_code, 409, duplicate.text)
        self.assertEqual(duplicate.headers.get("x-pokrov-auth-error"), "support_attachment_already_bound")

        mixed_upload = self._upload_support_attachment(alice, name="mixed.txt", content=b"mixed")
        mixed = self.client.post(
            f"/api/tickets/{ticket_id}/messages",
            headers=alice,
            json={
                "body": "Mixed",
                "attachment_id": mixed_upload.json()["attachment_id"],
                "media_type": "file",
            },
        )
        self.assertEqual(mixed.status_code, 400, mixed.text)
        self.assertEqual(mixed.headers.get("x-pokrov-auth-error"), "support_attachment_invalid")

        expired_upload = self._upload_support_attachment(alice, name="expired.txt", content=b"expired")
        expired_id = expired_upload.json()["attachment_id"]
        session = SessionLocal()
        try:
            session.query(SupportAttachment).filter_by(stored_name=expired_id).update(
                {SupportAttachment.expires_at: _utcnow() - timedelta(seconds=1)}
            )
            session.add(
                User(
                    tg_id=1002,
                    username="bob",
                    uuid=str(uuid.uuid4()),
                    email="user_1002",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            session.commit()
        finally:
            session.close()
        expired = self.client.post(
            f"/api/tickets/{ticket_id}/messages",
            headers=alice,
            json={"body": "Expired", "attachment_id": expired_id},
        )
        self.assertEqual(expired.status_code, 404, expired.text)
        self.assertEqual(expired.headers.get("x-pokrov-auth-error"), "support_attachment_not_found")

        bob = {"X-Telegram-Init-Data": self._init_data(1002, "bob")}
        foreign_upload = self._upload_support_attachment(bob, name="foreign.txt", content=b"foreign")
        foreign = self.client.post(
            f"/api/tickets/{ticket_id}/messages",
            headers=admin,
            json={"body": "Admin cannot steal staged upload", "attachment_id": foreign_upload.json()["attachment_id"]},
        )
        self.assertEqual(foreign.status_code, 404, foreign.text)
        self.assertEqual(foreign.headers.get("x-pokrov-auth-error"), "support_attachment_not_found")

        session = SessionLocal()
        try:
            self.assertEqual(
                session.query(SupportTicketMessage).filter_by(ticket_id=ticket_id).count(),
                before_count,
            )
            bound = session.query(SupportAttachment).filter_by(stored_name=first_id).one()
            self.assertEqual(bound.ticket_id, ticket_id)
            self.assertIsNotNone(bound.message_id)
            self.assertIsNotNone(bound.attached_at)
            self.assertIsNone(bound.expires_at)
        finally:
            session.close()

    def test_old_private_triplet_is_verified_and_nonprivate_triplet_remains_compatible(self) -> None:
        from db import SessionLocal
        from models import SupportAttachment

        headers = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        uploaded = self._upload_support_attachment(headers, name="old-client.txt", content=b"old client")
        body = uploaded.json()
        legacy = self.client.post(
            "/api/tickets",
            headers=headers,
            json={"subject": "Old client", "body": "Legacy private triplet", **body["attachment"]},
        )
        self.assertEqual(legacy.status_code, 200, legacy.text)
        ticket_id = int(legacy.json()["ticket"]["id"])
        session = SessionLocal()
        try:
            self.assertIsNotNone(
                session.query(SupportAttachment).filter_by(stored_name=body["attachment_id"]).one().message_id
            )
        finally:
            session.close()

        forged_upload = self._upload_support_attachment(headers, name="forged.txt", content=b"forged")
        forged_attachment = dict(forged_upload.json()["attachment"])
        forged_payload = json.loads(forged_attachment["media_payload"])
        forged_payload["name"] = "different.txt"
        forged_attachment["media_payload"] = json.dumps(forged_payload)
        forged = self.client.post(
            f"/api/tickets/{ticket_id}/messages",
            headers=headers,
            json={"body": "Forged metadata", **forged_attachment},
        )
        self.assertEqual(forged.status_code, 400, forged.text)
        self.assertEqual(forged.headers.get("x-pokrov-auth-error"), "support_attachment_invalid")

        missing = self.client.post(
            f"/api/tickets/{ticket_id}/messages",
            headers=headers,
            json={
                "body": "Forged reference",
                "media_type": "file",
                "media_file_id": "support/20260714-doesnotexist.txt",
                "media_payload": "{}",
            },
        )
        self.assertEqual(missing.status_code, 404, missing.text)
        self.assertEqual(missing.headers.get("x-pokrov-auth-error"), "support_attachment_not_found")

        telegram = self.client.post(
            f"/api/tickets/{ticket_id}/messages",
            headers=headers,
            json={
                "body": "Telegram compatibility",
                "media_type": "photo",
                "media_file_id": "telegram-file-id",
                "media_payload": '{"file_unique_id":"telegram-unique"}',
            },
        )
        self.assertEqual(telegram.status_code, 200, telegram.text)
        self.assertEqual(telegram.json()["ticket"]["messages"][-1]["media_file_id"], "telegram-file-id")

    def test_bound_download_follows_ticket_access_while_unbound_uses_owner_fallback(self) -> None:
        from db import SessionLocal
        from models import SupportAttachment, User

        alice = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        bob = {"X-Telegram-Init-Data": self._init_data(1002, "bob")}
        admin = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        session = SessionLocal()
        try:
            session.add(
                User(
                    tg_id=1002,
                    username="bob",
                    uuid=str(uuid.uuid4()),
                    email="user_1002",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            session.commit()
        finally:
            session.close()

        bound_upload = self._upload_support_attachment(alice, name="bound.txt", content=b"bound")
        bound_id = bound_upload.json()["attachment_id"]
        created = self.client.post(
            "/api/tickets",
            headers=alice,
            json={"subject": "Bound ACL", "body": "Bound", "attachment_id": bound_id},
        )
        self.assertEqual(created.status_code, 200, created.text)
        bound_url = bound_upload.json()["attachment_payload"]["url"]
        session = SessionLocal()
        try:
            row = session.query(SupportAttachment).filter_by(stored_name=bound_id).one()
            row.owner_tg_id = 1002
            row.owner_account_id = None
            session.commit()
        finally:
            session.close()
        self.assertEqual(self.client.get(bound_url, headers=alice).status_code, 200)
        self.assertEqual(self.client.get(bound_url, headers=bob).status_code, 403)
        self.assertEqual(self.client.get(bound_url, headers=admin).status_code, 200)

        unbound_upload = self._upload_support_attachment(bob, name="unbound.txt", content=b"unbound")
        unbound_url = unbound_upload.json()["attachment_payload"]["url"]
        self.assertEqual(self.client.get(unbound_url, headers=bob).status_code, 200)
        self.assertEqual(self.client.get(unbound_url, headers=alice).status_code, 403)
        self.assertEqual(self.client.get(unbound_url, headers=admin).status_code, 200)

        session = SessionLocal()
        try:
            row = session.query(SupportAttachment).filter_by(stored_name=unbound_upload.json()["attachment_id"]).one()
            row.expires_at = _utcnow() - timedelta(seconds=1)
            session.commit()
        finally:
            session.close()
        self.assertEqual(self.client.get(unbound_url, headers=bob).status_code, 404)
        self.assertEqual(self.client.get(unbound_url, headers=admin).status_code, 404)

    def test_upload_commit_ack_loss_preserves_durable_row_and_final_file(self) -> None:
        from db import SessionLocal
        from models import SecurityEvent, SupportAttachment

        headers = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        replace_calls: list[tuple[Path, Path]] = []
        finalization_events: list[str] = []
        original_replace = self.api.os.replace
        original_parent_fsync = self.api._fsync_parent_directory

        def recording_replace(source, destination):
            finalization_events.append("replace")
            replace_calls.append((Path(source), Path(destination)))
            return original_replace(source, destination)

        def recording_parent_fsync(path):
            finalization_events.append("parent_fsync")
            return original_parent_fsync(path)

        class _FailingCommitSession:
            def __init__(self, inner):
                self._inner = inner
                self.commit_count = 0

            def commit(self):
                self.commit_count += 1
                finalization_events.append(f"commit_{self.commit_count}")
                if self.commit_count == 2:
                    self._inner.commit()
                    finalization_events.append("commit_2_durable")
                    raise RuntimeError("forced attachment commit acknowledgement loss")
                return self._inner.commit()

            def __getattr__(self, name):
                return getattr(self._inner, name)

        calls = 0
        failing_sessions: list[_FailingCommitSession] = []

        def _session_factory():
            nonlocal calls
            calls += 1
            inner = SessionLocal()
            if calls == 1:
                return inner
            failing = _FailingCommitSession(inner)
            failing_sessions.append(failing)
            return failing

        with patch.object(self.api, "SessionLocal", new=_session_factory), patch.object(
            self.api.os, "replace", new=recording_replace
        ), patch.object(
            self.api, "_fsync_parent_directory", new=recording_parent_fsync
        ):
            with self.assertRaises(RuntimeError):
                self._upload_support_attachment(headers, name="atomic.txt", content=b"atomic")
        self.assertEqual(len(replace_calls), 1)
        self.assertIn(2, [session.commit_count for session in failing_sessions])
        self.assertLess(finalization_events.index("replace"), finalization_events.index("parent_fsync"))
        self.assertLess(finalization_events.index("parent_fsync"), finalization_events.index("commit_2"))
        self.assertLess(finalization_events.index("commit_2"), finalization_events.index("commit_2_durable"))
        self.assertFalse(replace_calls[0][0].exists())
        self.assertTrue(replace_calls[0][1].exists())
        session = SessionLocal()
        try:
            row = session.query(SupportAttachment).filter_by(original_name="atomic.txt").one()
            self.assertEqual(replace_calls[0][1].name, row.stored_name)
            events = session.query(SecurityEvent).filter_by(event_type="support_upload_reject").all()
            self.assertEqual([row.reason for row in events], ["store_failed"])
        finally:
            session.close()

    def test_upload_precommit_failure_leaves_rowless_final_for_grace_reconciliation(self) -> None:
        from db import SessionLocal
        from models import SupportAttachment

        cleanup = importlib.import_module("support_attachment_cleanup_service")
        headers = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        replace_calls: list[tuple[Path, Path]] = []
        original_replace = self.api.os.replace

        def recording_replace(source, destination):
            replace_calls.append((Path(source), Path(destination)))
            return original_replace(source, destination)

        class _FailingAddSession:
            def __init__(self, inner):
                self._inner = inner

            def add(self, value):
                if isinstance(value, SupportAttachment):
                    raise RuntimeError("forced pre-commit attachment persistence failure")
                return self._inner.add(value)

            def __getattr__(self, name):
                return getattr(self._inner, name)

        calls = 0

        def _session_factory():
            nonlocal calls
            calls += 1
            inner = SessionLocal()
            return inner if calls == 1 else _FailingAddSession(inner)

        with patch.object(self.api, "SessionLocal", new=_session_factory), patch.object(
            self.api.os, "replace", new=recording_replace
        ):
            with self.assertRaises(RuntimeError):
                self._upload_support_attachment(headers, name="precommit.txt", content=b"precommit")

        self.assertEqual(len(replace_calls), 1)
        temp_path, final_path = replace_calls[0]
        self.assertFalse(temp_path.exists())
        self.assertTrue(final_path.exists())
        session = SessionLocal()
        try:
            self.assertEqual(session.query(SupportAttachment).filter_by(original_name="precommit.txt").count(), 0)
        finally:
            session.close()

        now = _utcnow()
        recent = cleanup.reconcile_support_attachments(
            SessionLocal,
            upload_dir=Path(self.api.SUPPORT_UPLOAD_DIR),
            now=now,
            grace_seconds=3600,
            batch_size=10,
            scan_limit=20,
        )
        self.assertEqual(recent["orphan_files_removed"], 0)
        self.assertTrue(final_path.exists())

        old_timestamp = (now - timedelta(hours=2)).replace(tzinfo=timezone.utc).timestamp()
        os.utime(final_path, (old_timestamp, old_timestamp))
        expired = cleanup.reconcile_support_attachments(
            SessionLocal,
            upload_dir=Path(self.api.SUPPORT_UPLOAD_DIR),
            now=now,
            grace_seconds=3600,
            batch_size=10,
            scan_limit=20,
        )
        self.assertEqual(expired["orphan_files_removed"], 1)
        self.assertFalse(final_path.exists())

    def test_support_upload_parent_directory_fsync_is_posix_only(self) -> None:
        target = Path(self.api.SUPPORT_UPLOAD_DIR) / "20260714-fsynctest.txt"
        expected_flags = self.api.os.O_RDONLY | getattr(self.api.os, "O_DIRECTORY", 0)
        with patch.object(self.api.os, "name", "posix"), patch.object(
            self.api.os, "open", return_value=73
        ) as open_mock, patch.object(self.api.os, "fsync") as fsync_mock, patch.object(
            self.api.os, "close"
        ) as close_mock:
            self.api._fsync_parent_directory(target)

        open_mock.assert_called_once_with(str(target.parent), expected_flags)
        fsync_mock.assert_called_once_with(73)
        close_mock.assert_called_once_with(73)

    def test_concurrent_attachment_bind_has_one_winner_and_no_duplicate_message(self) -> None:
        from db import SessionLocal
        from models import SupportAttachment, SupportTicketMessage

        headers = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        created = self.client.post(
            "/api/tickets",
            headers=headers,
            json={"subject": "Concurrency", "body": "Initial"},
        )
        ticket_id = int(created.json()["ticket"]["id"])
        upload = self._upload_support_attachment(headers, name="race.txt", content=b"race")
        attachment_id = upload.json()["attachment_id"]

        def _bind(body: str):
            with TestClient(self.api.app) as client:
                return client.post(
                    f"/api/tickets/{ticket_id}/messages",
                    headers=headers,
                    json={"body": body, "attachment_id": attachment_id},
                )

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            responses = list(executor.map(_bind, ("racer one", "racer two")))
        self.assertEqual(sorted(response.status_code for response in responses), [200, 409])

        session = SessionLocal()
        try:
            messages = session.query(SupportTicketMessage).filter_by(ticket_id=ticket_id).all()
            self.assertEqual(len(messages), 2)
            attachment = session.query(SupportAttachment).filter_by(stored_name=attachment_id).one()
            self.assertIn(attachment.message_id, {message.id for message in messages})
        finally:
            session.close()

    def test_attachment_bind_boundary_expiry_or_deletion_is_not_found_and_rolls_back_message(self) -> None:
        from db import SessionLocal
        from models import SupportAttachment, SupportTicketMessage

        headers = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        created = self.client.post(
            "/api/tickets",
            headers=headers,
            json={"subject": "Bind boundary", "body": "Initial"},
        )
        self.assertEqual(created.status_code, 200, created.text)
        ticket_id = int(created.json()["ticket"]["id"])
        original_bind = self.api._bind_ticket_attachment

        for boundary in ("expired", "deleted"):
            with self.subTest(boundary=boundary):
                upload = self._upload_support_attachment(
                    headers,
                    name=f"boundary-{boundary}.txt",
                    content=boundary.encode("ascii"),
                )
                self.assertEqual(upload.status_code, 200, upload.text)
                attachment_id = upload.json()["attachment_id"]
                body = f"must roll back {boundary} boundary"

                session = SessionLocal()
                try:
                    before_count = session.query(SupportTicketMessage).filter_by(ticket_id=ticket_id).count()
                finally:
                    session.close()

                def boundary_bind(session, *, row, ticket_id, message_id):
                    query = session.query(SupportAttachment).filter(SupportAttachment.id == row.id)
                    if boundary == "expired":
                        query.update(
                            {SupportAttachment.expires_at: _utcnow() - timedelta(seconds=1)},
                            synchronize_session=False,
                        )
                    else:
                        query.delete(synchronize_session=False)
                    return original_bind(
                        session,
                        row=row,
                        ticket_id=ticket_id,
                        message_id=message_id,
                    )

                with patch.object(self.api, "_bind_ticket_attachment", new=boundary_bind):
                    response = self.client.post(
                        f"/api/tickets/{ticket_id}/messages",
                        headers=headers,
                        json={"body": body, "attachment_id": attachment_id},
                    )

                self.assertEqual(response.status_code, 404, response.text)
                self.assertEqual(
                    response.headers.get("x-pokrov-auth-error"),
                    "support_attachment_not_found",
                )
                session = SessionLocal()
                try:
                    self.assertEqual(
                        session.query(SupportTicketMessage).filter_by(ticket_id=ticket_id).count(),
                        before_count,
                    )
                    self.assertEqual(
                        session.query(SupportTicketMessage).filter_by(ticket_id=ticket_id, body=body).count(),
                        0,
                    )
                    restored = session.query(SupportAttachment).filter_by(stored_name=attachment_id).one()
                    self.assertIsNone(restored.ticket_id)
                    self.assertIsNone(restored.message_id)
                    self.assertGreater(restored.expires_at, _utcnow())
                finally:
                    session.close()

    def test_linked_account_sessions_share_tickets_and_uploads_with_strict_nonnull_owner(self) -> None:
        from db import SessionLocal
        from models import Account, SupportAttachment, SupportTicket, User

        s = SessionLocal()
        try:
            shared = Account(id="shared-support-account", status="active", created_source="test")
            other = Account(id="other-support-account", status="active", created_source="test")
            alice = s.query(User).filter_by(tg_id=1001).one()
            alice.account_id = shared.id
            linked = User(
                tg_id=1002,
                account_id=shared.id,
                username="linked",
                uuid=str(uuid.uuid4()),
                email="user_1002",
                sub_type="FREE",
                is_active=True,
                tos_accepted=True,
            )
            s.add_all([shared, other, linked])
            s.commit()
        finally:
            s.close()

        alice_headers = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        linked_headers = {"X-Telegram-Init-Data": self._init_data(1002, "linked")}
        admin_headers = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        created = self.client.post(
            "/api/tickets",
            headers=alice_headers,
            json={"subject": "Shared", "body": "Created from Telegram identity one"},
        )
        self.assertEqual(created.status_code, 200, created.text)
        ticket_payload = created.json()["ticket"]
        ticket_id = int(ticket_payload["id"])
        self.assertNotIn("account_id", ticket_payload)

        listed = self.client.get("/api/tickets", headers=linked_headers)
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertIn(ticket_id, [int(row["id"]) for row in listed.json()["tickets"]])

        opened = self.client.get(f"/api/tickets/{ticket_id}", headers=linked_headers)
        self.assertEqual(opened.status_code, 200, opened.text)
        replied = self.client.post(
            f"/api/tickets/{ticket_id}/messages",
            headers=linked_headers,
            json={"body": "Reply from Telegram identity two"},
        )
        self.assertEqual(replied.status_code, 200, replied.text)

        uploaded = self.client.post(
            "/api/tickets/uploads",
            headers={**alice_headers, "Content-Type": "image/png", "X-Upload-Filename": "shared.png"},
            content=b"\x89PNG\r\n\x1a\nshared-account",
        )
        self.assertEqual(uploaded.status_code, 200, uploaded.text)
        file_url = uploaded.json()["attachment_payload"]["url"]
        downloaded = self.client.get(file_url, headers=linked_headers)
        self.assertEqual(downloaded.status_code, 200, downloaded.text)

        s = SessionLocal()
        try:
            ticket = s.query(SupportTicket).filter_by(id=ticket_id).one()
            attachment = s.query(SupportAttachment).order_by(SupportAttachment.id.desc()).first()
            self.assertEqual(ticket.account_id, "shared-support-account")
            self.assertEqual(attachment.owner_account_id, "shared-support-account")
            attachment.owner_tg_id = 1002
            attachment.owner_account_id = "other-support-account"
            tempting = SupportTicket(
                user_tg_id=1002,
                account_id="other-support-account",
                status="open",
                created_at=_utcnow(),
                updated_at=_utcnow(),
            )
            s.add(tempting)
            s.commit()
            tempting_id = int(tempting.id)
        finally:
            s.close()

        denied = self.client.get(f"/api/tickets/{tempting_id}", headers=linked_headers)
        self.assertEqual(denied.status_code, 403, denied.text)
        denied_attachment = self.client.get(file_url, headers=linked_headers)
        self.assertEqual(denied_attachment.status_code, 403, denied_attachment.text)
        admin_opened = self.client.get(f"/api/tickets/{tempting_id}", headers=admin_headers)
        self.assertEqual(admin_opened.status_code, 200, admin_opened.text)
        admin_downloaded = self.client.get(file_url, headers=admin_headers)
        self.assertEqual(admin_downloaded.status_code, 200, admin_downloaded.text)

    def test_ticket_upload_rejects_svg_and_octet_stream(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

        svg = self.client.post(
            "/api/tickets/uploads",
            headers={**user_hdrs, "Content-Type": "image/svg+xml", "X-Upload-Filename": "x.svg"},
            content=b"<svg><script>alert(1)</script></svg>",
        )
        self.assertEqual(svg.status_code, 400, svg.text)

        opaque = self.client.post(
            "/api/tickets/uploads",
            headers={**user_hdrs, "Content-Type": "application/octet-stream", "X-Upload-Filename": "x.bin"},
            content=b"\x00\x01\x02\x03",
        )
        self.assertEqual(opaque.status_code, 400, opaque.text)

    def test_cors_credentials_do_not_use_wildcard_origin(self) -> None:
        cors_middleware = next(
            middleware
            for middleware in self.api.app.user_middleware
            if getattr(middleware.cls, "__name__", "") == "CORSMiddleware"
        )

        middleware_options = getattr(cors_middleware, "kwargs", {})
        allow_origins = middleware_options.get("allow_origins") or []
        self.assertNotIn("*", allow_origins)
        self.assertIn("https://app.pokrov.space", allow_origins)
        self.assertIn("https://admin.pokrov.space", allow_origins)
        self.assertIn("https://www.admin.pokrov.space", allow_origins)
        self.assertTrue(middleware_options.get("allow_credentials"))

    def test_request_client_ip_trusts_forwarded_headers_only_from_proxy(self) -> None:
        untrusted_request = SimpleNamespace(
            headers={"x-real-ip": "203.0.113.10", "x-forwarded-for": "203.0.113.11"},
            client=SimpleNamespace(host="198.51.100.20"),
        )
        trusted_request = SimpleNamespace(
            headers={"x-real-ip": "203.0.113.10", "x-forwarded-for": "203.0.113.11"},
            client=SimpleNamespace(host="127.0.0.1"),
        )

        self.assertEqual(self.api._request_client_ip(untrusted_request), "198.51.100.20")
        self.assertEqual(self.api._request_client_ip(trusted_request), "203.0.113.10")

        allowed = self.client.options(
            "/api/me",
            headers={
                "Origin": "https://app.pokrov.space",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertEqual(allowed.headers.get("access-control-allow-origin"), "https://app.pokrov.space")
        self.assertEqual(allowed.headers.get("access-control-allow-credentials"), "true")

        admin_allowed = self.client.options(
            "/api/admin/ops/overview",
            headers={
                "Origin": "https://admin.pokrov.space",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertEqual(admin_allowed.headers.get("access-control-allow-origin"), "https://admin.pokrov.space")

        admin_www_allowed = self.client.options(
            "/api/admin/ops/overview",
            headers={
                "Origin": "https://www.admin.pokrov.space",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertEqual(
            admin_www_allowed.headers.get("access-control-allow-origin"),
            "https://www.admin.pokrov.space",
        )
        self.assertEqual(admin_allowed.headers.get("access-control-allow-credentials"), "true")

        blocked = self.client.options(
            "/api/me",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertNotEqual(blocked.headers.get("access-control-allow-origin"), "https://evil.example")

    def test_channel_bonus_claim_extends_active_paid_access(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        self._promote_test_user_to_paid()

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
        self.assertEqual(body["premium_days"], 5)
        self.assertEqual(body["sub_type"], "PAID")
        self.assertTrue(body["sync_ok"])
        activated_events = self._event_rows("promo_channel_activated")
        self.assertEqual(len(activated_events), 1)
        self.assertEqual(activated_events[0]["source"], "webapp")
        self.assertEqual(int(activated_events[0]["meta"].get("days") or 0), 5)
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
        self._promote_test_user_to_paid()
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
            self.assertEqual((user.sub_type or "").upper(), "PAID")
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
        self._promote_test_user_to_paid()

        async def fake_not_member(channel_username: str, tg_id: int):
            return False, "not_member"

        self.api._is_channel_member = fake_not_member

        r = self.client.post("/api/bonuses/channel/claim", headers=user_hdrs)
        self.assertEqual(r.status_code, 400, r.text)

    def test_channel_bonus_claim_treats_left_as_not_member(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        self._promote_test_user_to_paid()

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
        self._promote_test_user_to_paid()
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

        created = self._execute_admin_intent(
            action="user.manual_create",
            target_type="user",
            target_id="manual",
            method="POST",
            path="/api/admin/users/manual",
            payload={"display_name": "Offline Client", "days": 30},
        )
        self.assertEqual(created.status_code, 200, created.text)
        body = created.json()
        self.assertTrue(body["ok"])
        self.assertTrue(body["sync_ok"])
        self.assertTrue(str(body["user"]["subscription_url"]).startswith("https://connect.pokrov.space/s8Kx2mP7qR4wT/"))
        manual_tg_id = int(body["user"]["tg_id"])
        self.assertLess(manual_tg_id, 0)
        session = self.api.SessionLocal()
        try:
            manual_user = session.query(self.api.User).filter_by(tg_id=manual_tg_id).one()
            self.assertTrue(manual_user.account_id)
        finally:
            session.close()

        extend = self._execute_admin_intent(
            action="user.extend",
            target_type="user",
            target_id=manual_tg_id,
            method="POST",
            path=f"/api/admin/users/{manual_tg_id}/manual/extend",
            payload={"delta_days": 7},
        )
        self.assertEqual(extend.status_code, 200, extend.text)
        self.assertTrue(extend.json()["ok"])
        self.assertEqual(int(extend.json().get("delta_days") or 0), 7)
        self.assertIsInstance(datetime.fromisoformat(extend.json()["expiry_at"]), datetime)

        alias_extend = self._execute_admin_intent(
            action="user.extend",
            target_type="user",
            target_id=manual_tg_id,
            method="POST",
            path=f"/api/admin/users/{manual_tg_id}/manual-extend",
            payload={"delta_days": 1},
        )
        self.assertEqual(alias_extend.status_code, 200, alias_extend.text)
        self.assertEqual(int(alias_extend.json().get("delta_days") or 0), 1)

        backwards_compat = self._execute_admin_intent(
            action="user.extend",
            target_type="user",
            target_id=manual_tg_id,
            method="POST",
            path=f"/api/admin/users/{manual_tg_id}/manual/extend",
            payload={"days": 3},
        )
        self.assertEqual(backwards_compat.status_code, 200, backwards_compat.text)
        self.assertEqual(int(backwards_compat.json().get("delta_days") or 0), 3)

        reject_negative = self._execute_admin_intent(
            action="user.extend",
            target_type="user",
            target_id=manual_tg_id,
            method="POST",
            path=f"/api/admin/users/{manual_tg_id}/manual/extend",
            payload={"delta_days": -3650},
        )
        self.assertEqual(reject_negative.status_code, 409, reject_negative.text)

        allow_negative = self._execute_admin_intent(
            action="user.extend",
            target_type="user",
            target_id=manual_tg_id,
            method="POST",
            path=f"/api/admin/users/{manual_tg_id}/manual/extend",
            payload={"delta_days": -3650, "allow_deactivate": True},
        )
        self.assertEqual(allow_negative.status_code, 200, allow_negative.text)
        self.assertFalse(bool(allow_negative.json().get("is_active")))

        block = self._execute_admin_intent(
            action="user.block",
            target_type="user",
            target_id=manual_tg_id,
            method="POST",
            path=f"/api/admin/users/{manual_tg_id}/manual/block",
            payload={"blocked": True},
        )
        self.assertEqual(block.status_code, 200, block.text)
        self.assertTrue(block.json()["ok"])
        self.assertFalse(block.json()["is_active"])

        regen = self._execute_admin_intent(
            action="user.regenerate_token",
            target_type="user",
            target_id=manual_tg_id,
            method="POST",
            path=f"/api/admin/users/{manual_tg_id}/manual/regenerate-token",
            payload={},
        )
        self.assertEqual(regen.status_code, 200, regen.text)
        self.assertTrue(regen.json()["ok"])
        self.assertTrue(bool(regen.json().get("sync_ok")))
        self.assertTrue(str(regen.json()["subscription_url"]).startswith("https://connect.pokrov.space/s8Kx2mP7qR4wT/"))

    def test_admin_users_support_effective_status_origin_filters_and_search(self) -> None:
        from db import SessionLocal
        from models import User

        now = _utcnow().replace(microsecond=0)
        s = SessionLocal()
        try:
            base_user = s.query(User).filter_by(tg_id=1001).first()
            assert base_user is not None
            base_user.display_name = "Alice Visible"
            base_user.expiry_at = now + timedelta(days=2)
            base_user.linked_telegram_username = "alice_visible"

            s.add(
                User(
                    tg_id=2001,
                    username="paid_active",
                    display_name="Paid Active",
                    uuid=str(uuid.uuid4()),
                    email="paid_active_2001",
                    sub_type="PAID",
                    is_active=True,
                    expiry_at=now + timedelta(days=5),
                    tos_accepted=True,
                )
            )
            s.add(
                User(
                    tg_id=2002,
                    username="expired_paid",
                    display_name="Expired Paid",
                    uuid=str(uuid.uuid4()),
                    email="expired_paid_2002",
                    sub_type="PAID",
                    is_active=True,
                    expiry_at=now - timedelta(days=1),
                    tos_accepted=True,
                )
            )
            s.add(
                User(
                    tg_id=2003,
                    username="blocked_paid",
                    display_name="Blocked Paid",
                    uuid=str(uuid.uuid4()),
                    email="blocked_paid_2003",
                    sub_type="PAID",
                    is_active=False,
                    expiry_at=now + timedelta(days=5),
                    tos_accepted=True,
                )
            )
            s.add(
                User(
                    tg_id=2004,
                    username=None,
                    display_name="Standalone App User",
                    uuid=str(uuid.uuid4()),
                    email="app_user_2004",
                    sub_type="FREE",
                    is_active=True,
                    expiry_at=now + timedelta(days=3),
                    tos_accepted=True,
                    is_app_user=True,
                    app_install_id="install-2004",
                )
            )
            s.add(
                User(
                    tg_id=-10050,
                    username=None,
                    display_name="Router Lab",
                    uuid=str(uuid.uuid4()),
                    email="manual_router_lab",
                    sub_type="MANUAL",
                    is_active=True,
                    expiry_at=now + timedelta(days=30),
                    tos_accepted=True,
                    is_manual=True,
                    created_by_admin=9999,
                )
            )
            s.commit()
        finally:
            s.close()

        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        inactive_resp = self.client.get(
            "/api/admin/users?status=inactive&sort=created_desc&page=1&page_size=20",
            headers=admin_hdrs,
        )
        self.assertEqual(inactive_resp.status_code, 200, inactive_resp.text)
        inactive_body = inactive_resp.json()
        self.assertEqual(int(inactive_body.get("page") or 0), 1)
        self.assertEqual(int(inactive_body.get("page_size") or 0), 20)
        inactive_rows = inactive_body.get("users", [])
        inactive_ids = {int(row["tg_id"]) for row in inactive_rows}
        inactive_statuses = {str(row.get("status") or "") for row in inactive_rows}
        self.assertTrue({2002, 2003}.issubset(inactive_ids))
        self.assertEqual(inactive_statuses, {"expired", "blocked"})

        manual_resp = self.client.get(
            "/api/admin/users?origin=manual_test&q=Router%20Lab&page=1&page_size=20",
            headers=admin_hdrs,
        )
        self.assertEqual(manual_resp.status_code, 200, manual_resp.text)
        manual_rows = manual_resp.json().get("users", [])
        self.assertEqual(len(manual_rows), 1)
        self.assertEqual(int(manual_rows[0]["tg_id"]), -10050)
        self.assertEqual(str(manual_rows[0].get("origin") or ""), "manual_test")
        self.assertEqual(str(manual_rows[0].get("status") or ""), "manual_test")

        app_resp = self.client.get(
            "/api/admin/users?origin=app&page=1&page_size=20",
            headers=admin_hdrs,
        )
        self.assertEqual(app_resp.status_code, 200, app_resp.text)
        self.assertTrue(any(int(row["tg_id"]) == 2004 for row in app_resp.json().get("users", [])))

    def test_admin_bulk_key_action_accepts_inactive_and_manual_test_segments(self) -> None:
        from db import SessionLocal
        from models import User

        now = _utcnow().replace(microsecond=0)
        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=2101,
                    username="inactive_paid",
                    uuid=str(uuid.uuid4()),
                    email="inactive_paid_2101",
                    sub_type="PAID",
                    is_active=False,
                    expiry_at=now + timedelta(days=7),
                    tos_accepted=True,
                )
            )
            s.add(
                User(
                    tg_id=-10060,
                    username=None,
                    display_name="Manual Segment User",
                    uuid=str(uuid.uuid4()),
                    email="manual_segment_user",
                    sub_type="MANUAL",
                    is_active=True,
                    expiry_at=now + timedelta(days=30),
                    tos_accepted=True,
                    is_manual=True,
                    created_by_admin=9999,
                )
            )
            s.commit()
        finally:
            s.close()

        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        inactive_resp = self._execute_admin_intent(
            action="user.bulk_key_action",
            target_type="users",
            target_id="bulk",
            method="POST",
            path="/api/admin/users/keys/bulk-action",
            payload={"action": "disable", "segment": "inactive", "dry_run": True},
        )
        self.assertEqual(inactive_resp.status_code, 200, inactive_resp.text)
        self.assertIn(2101, inactive_resp.json().get("preview_tg_ids", []))

        manual_resp = self._execute_admin_intent(
            action="user.bulk_key_action",
            target_type="users",
            target_id="bulk",
            method="POST",
            path="/api/admin/users/keys/bulk-action",
            payload={"action": "disable", "segment": "manual_test", "dry_run": True},
        )
        self.assertEqual(manual_resp.status_code, 200, manual_resp.text)
        self.assertIn(-10060, manual_resp.json().get("preview_tg_ids", []))

    def test_admin_safe_delete_only_removes_explicit_test_users(self) -> None:
        from db import SessionLocal
        from models import User

        class FakePanel:
            async def login(self):
                return True

            async def close(self):
                return True

            async def delete_client(self, _tg_id: int):
                return True

        self.api.ControlPanel = FakePanel

        now = _utcnow().replace(microsecond=0)
        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=-10070,
                    username=None,
                    display_name="Disposable Router",
                    uuid=str(uuid.uuid4()),
                    email="disposable_router",
                    sub_type="MANUAL",
                    is_active=True,
                    expiry_at=now + timedelta(days=30),
                    tos_accepted=True,
                    is_manual=True,
                    created_by_admin=9999,
                )
            )
            s.commit()
        finally:
            s.close()

        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        reject_real = self._prepare_admin_intent(
            action="user.safe_delete",
            target_type="user",
            target_id=1001,
            payload={"confirm": True},
        )
        self.assertEqual(reject_real.status_code, 409, reject_real.text)

        deleted = self._execute_admin_intent(
            action="user.safe_delete",
            target_type="user",
            target_id=-10070,
            method="POST",
            path="/api/admin/users/-10070/safe-delete",
            payload={"confirm": True},
        )
        self.assertEqual(deleted.status_code, 200, deleted.text)
        self.assertTrue(bool(deleted.json().get("ok")))

        s = SessionLocal()
        try:
            row = s.query(User).filter(User.tg_id == -10070).first()
            self.assertIsNone(row)
        finally:
            s.close()

    def test_admin_promos_templates_and_gift_codes_crud(self) -> None:
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

        created_promo = self._execute_admin_intent(
            action="promo.create",
            target_type="promo",
            target_id="WELCOME14",
            method="POST",
            path="/api/admin/promos",
            payload={"code": "WELCOME14", "promo_type": "days", "value": 14, "uses_left": 100},
        )
        self.assertEqual(created_promo.status_code, 200, created_promo.text)

        promo_list = self.client.get("/api/admin/promos?limit=20", headers=admin_hdrs)
        self.assertEqual(promo_list.status_code, 200, promo_list.text)
        self.assertTrue(any((p.get("code") or "") == "WELCOME14" for p in promo_list.json().get("promos", [])))

        updated_promo = self._execute_admin_intent(
            action="promo.update",
            target_type="promo",
            target_id="WELCOME14",
            method="PATCH",
            path="/api/admin/promos/WELCOME14",
            payload={"value": 21, "uses_left": 50},
        )
        self.assertEqual(updated_promo.status_code, 200, updated_promo.text)

        deleted_promo = self._execute_admin_intent(
            action="promo.delete",
            target_type="promo",
            target_id="WELCOME14",
            method="DELETE",
            path="/api/admin/promos/WELCOME14",
            payload={},
        )
        self.assertEqual(deleted_promo.status_code, 200, deleted_promo.text)

        created_tpl = self._execute_admin_intent(
            action="template.create",
            target_type="template",
            target_id="retention_t3",
            method="POST",
            path="/api/admin/templates",
            payload={"key": "retention_t3", "text": "Подписка скоро завершится. Продлите доступ."},
        )
        self.assertEqual(created_tpl.status_code, 200, created_tpl.text)

        tpl_list = self.client.get("/api/admin/templates?limit=20", headers=admin_hdrs)
        self.assertEqual(tpl_list.status_code, 200, tpl_list.text)
        self.assertTrue(any((t.get("key") or "") == "retention_t3" for t in tpl_list.json().get("templates", [])))

        updated_tpl = self._execute_admin_intent(
            action="template.update",
            target_type="template",
            target_id="retention_t3",
            method="PATCH",
            path="/api/admin/templates/retention_t3",
            payload={"text": "Напоминаем: продлите доступ, чтобы не было паузы."},
        )
        self.assertEqual(updated_tpl.status_code, 200, updated_tpl.text)

        deleted_tpl = self._execute_admin_intent(
            action="template.delete",
            target_type="template",
            target_id="retention_t3",
            method="DELETE",
            path="/api/admin/templates/retention_t3",
            payload={},
        )
        self.assertEqual(deleted_tpl.status_code, 200, deleted_tpl.text)

        gift_created = self._execute_admin_intent(
            action="gift_code.create",
            target_type="gift_code",
            target_id="standard",
            method="POST",
            path="/api/admin/gift-codes",
            payload={"card_type": "standard"},
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
            user.created_at = _utcnow() - timedelta(days=45)
            s.commit()
        finally:
            s.close()

        cfg = self._execute_admin_intent(
            action="loyalty_config.update",
            target_type="config",
            target_id="loyalty",
            method="PUT",
            path="/api/admin/loyalty-config",
            payload={"enabled": True, "tiers": [{"days": 30, "bonus_days": 5, "perk": "loyal_30"}]},
        )
        self.assertEqual(cfg.status_code, 200, cfg.text)

        seen: list[int] = []

        async def fake_sync(user):
            seen.append(int(getattr(user, "tg_id", 0) or 0))
            return True

        self.api._sync_user_after_paid_bonus = fake_sync

        granted = self._execute_admin_intent(
            action="user.loyalty_grant",
            target_type="user",
            target_id=1001,
            method="POST",
            path="/api/admin/users/1001/loyalty/grant",
            payload={"tier_days": 30},
        )
        self.assertEqual(granted.status_code, 200, granted.text)
        self.assertTrue(granted.json().get("ok"))
        self.assertTrue(bool(granted.json().get("sync_ok")))
        self.assertEqual(seen, [1001])

    def test_gift_redeem_tracks_denied_attempt(self) -> None:
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

        created = self._execute_admin_intent(
            action="gift_code.create",
            target_type="gift_code",
            target_id="standard",
            method="POST",
            path="/api/admin/gift-codes",
            payload={"card_type": "standard"},
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
        redeemed = self._event_rows("gift_redeemed")
        self.assertEqual(len(redeemed), 1)
        for row in [redeemed[0], denied[0]]:
            meta_dump = json.dumps(row["meta"], ensure_ascii=False)
            self.assertNotIn("code", row["meta"])
            self.assertNotIn(code, meta_dump)
            self.assertEqual(str(row["meta"].get("code_preview") or ""), f"...{code[-4:]}")
            self.assertEqual(
                str(row["meta"].get("code_fp") or ""),
                hashlib.sha256(code.encode("utf-8")).hexdigest()[:16],
            )
        self.assertEqual(str(denied[0]["meta"].get("reason") or ""), "already_redeemed")

    def test_access_key_redeem_tracks_redacted_key_metadata(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}
        code = "POKROV-ACCESS-2026"

        from db import SessionLocal
        from models import GiftCard

        s = SessionLocal()
        try:
            s.add(GiftCard(code=code, card_type="standard", created_by=9999))
            s.commit()
        finally:
            s.close()

        async def fake_sync_control_panel_access(*, user):
            return True

        with patch.object(self.api, "_sync_control_panel_access", fake_sync_control_panel_access):
            response = self.client.post("/api/access-keys/redeem", headers=user_hdrs, json={"key": code})

        self.assertEqual(response.status_code, 200, response.text)
        events = self._event_rows("access_key_redeemed")
        self.assertEqual(len(events), 1)
        meta = events[0]["meta"]
        meta_dump = json.dumps(meta, ensure_ascii=False)
        self.assertNotIn("code", meta)
        self.assertNotIn(code, meta_dump)
        self.assertEqual(meta.get("code_preview"), "...2026")
        self.assertEqual(meta.get("code_fp"), hashlib.sha256(code.encode("utf-8")).hexdigest()[:16])

    def test_promo_redeem_supports_unlimited_uses_flag(self) -> None:
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

        created = self._execute_admin_intent(
            action="promo.create",
            target_type="promo",
            target_id="FOREVER20",
            method="POST",
            path="/api/admin/promos",
            payload={"code": "FOREVER20", "promo_type": "discount", "value": 20, "uses_left": -1},
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
            user.expiry_at = _utcnow() + timedelta(days=10)
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
            user.expiry_at = _utcnow() + timedelta(days=10)
            s.commit()
        finally:
            s.close()

        self.api.SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED = False
        by_tg_id = self.client.get("/s8Kx2mP7qR4wT/1001")
        self.assertEqual(by_tg_id.status_code, 404, by_tg_id.text)

    def test_subscription_endpoint_supports_head_for_plain_and_hiddify_clients(self) -> None:
        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_type = "PAID"
            user.sub_token = "token_1001_secure"
            user.is_active = True
            user.expiry_at = _utcnow() + timedelta(days=10)
            s.commit()
        finally:
            s.close()

        plain = self.client.head("/s8Kx2mP7qR4wT/token_1001_secure")
        self.assertEqual(plain.status_code, 200, plain.text)
        self.assertEqual(plain.text, "")
        self.assertEqual(plain.headers.get("content-type"), "text/plain; charset=utf-8")
        self.assertEqual(plain.headers.get("profile-update-interval"), "6")
        self.assertIn("POKROV_Subscription", plain.headers.get("content-disposition", ""))

        hiddify = self.client.head(
            "/s8Kx2mP7qR4wT/token_1001_secure",
            headers={"User-Agent": "HiddifyNext/2.0"},
        )
        self.assertEqual(hiddify.status_code, 200, hiddify.text)
        self.assertEqual(hiddify.text, "")
        self.assertEqual(hiddify.headers.get("content-type"), "application/json")
        self.assertEqual(hiddify.headers.get("profile-title"), "POKROV")
        self.assertIn("POKROV.json", hiddify.headers.get("content-disposition", ""))

    def test_subscription_endpoint_supports_explicit_smart_and_plain_formats(self) -> None:
        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_token = "token_1001_secure"
            user.sub_type = "BONUS"
            user.current_plan_code = "1_month"
            user.is_active = True
            user.expiry_at = _utcnow() + timedelta(days=10)
            s.add(user)
            s.commit()
        finally:
            s.close()

        with patch.object(self.api, "_nodes_for_user", side_effect=lambda user, nodes, session=None: list(nodes or [])[:1]):
            smart = self.client.get("/s8Kx2mP7qR4wT/token_1001_secure?existing=1&format=smart")
        self.assertEqual(smart.status_code, 200, smart.text)
        self.assertEqual(smart.headers.get("content-type"), "application/json")
        smart_body = smart.json()
        self.assertIn("route", smart_body)
        self.assertIn("rule_set", smart_body["route"])
        rendered_route = json.dumps(smart_body["route"], ensure_ascii=False)
        self.assertNotIn('"geoip":', rendered_route)
        self.assertNotIn('"geosite":', rendered_route)

        plain = self.client.get("/s8Kx2mP7qR4wT/token_1001_secure?format=plain")
        self.assertEqual(plain.status_code, 200, plain.text)
        self.assertIn("text/plain", plain.headers.get("content-type", ""))
        self.assertIsInstance(plain.text, str)
        self.assertTrue(bool(plain.text.strip()))

    def test_subscription_endpoint_supports_happ_format_with_custom_tunnel_config(self) -> None:
        from db import SessionLocal
        from models import Node, User, UserNode

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_token = "token_1001_secure"
            user.sub_type = "PAID"
            user.current_plan_code = "1_month"
            user.is_active = True
            user.expiry_at = _utcnow() + timedelta(days=10)
            node = Node(
                code="de",
                name="Germany",
                host="de.example.test",
                vless_port=443,
                reality_sni="www.google.com",
                reality_pbk="pbk-de",
                reality_sid="sid-de",
                panel_base_url="https://de.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=1,
                enabled=True,
            )
            s.add(node)
            s.flush()
            s.add(UserNode(tg_id=1001, node_id=node.id, client_uuid=str(user.uuid), panel_email=str(user.email)))
            s.commit()
        finally:
            s.close()

        rollout_config = self.api.normalized_network_rollout_config(
            {
                self.api.RU_BRIDGE_RELAY: {
                    "enabled": True,
                    "reality_public_key": "bridge-pbk",
                    "reality_short_id": "bridge-sid",
                    "excluded_node_codes": [],
                }
            }
        )
        with patch.object(self.api, "load_network_rollout_config", return_value=rollout_config):
            happ = self.client.get("/s8Kx2mP7qR4wT/token_1001_secure?existing=1&format=happ")
            happ_ua = self.client.get(
                "/s8Kx2mP7qR4wT/token_1001_secure",
                headers={"Host": "connect.pokrov.space", "User-Agent": "Happ/3.0"},
            )

        self.assertEqual(happ.status_code, 200, happ.text)
        self.assertIn("text/plain", happ.headers.get("content-type", ""))
        self.assertIn("POKROV_Happ_Subscription", happ.headers.get("content-disposition", ""))
        self.assertEqual(happ.headers.get("subscriptions-expand-now"), "1")
        self.assertIn("#custom-tunnel-config: ", happ.text)
        self.assertIn("#subscriptions-expand-now: 1", happ.text)
        self.assertIn("vless://", happ.text)
        self.assertIn("Белые списки", happ.text)
        self.assertNotEqual(happ.text.lstrip()[:1], "{")

        custom_line = next(line for line in happ.text.splitlines() if line.startswith("#custom-tunnel-config: "))
        cfg = json.loads(custom_line.split(": ", 1)[1])
        self.assertTrue(
            any("Белые списки" in str(outbound.get("tag") or "") for outbound in cfg.get("outbounds", [])),
            cfg,
        )
        self.assertEqual(
            cfg["dns"]["servers"],
            [
                {"tag": "bootstrap", "address": "local"},
                {"tag": "google", "address": "8.8.8.8", "detour": "🌍 Страны"},
            ],
        )
        self.assertEqual(
            cfg["route"]["default_domain_resolver"],
            {"server": "bootstrap", "strategy": "prefer_ipv4"},
        )
        self.assertEqual(cfg["dns"]["final"], "google")

        self.assertEqual(happ_ua.status_code, 200, happ_ua.text)
        self.assertIn("text/plain", happ_ua.headers.get("content-type", ""))
        self.assertIn("#custom-tunnel-config: ", happ_ua.text)

    def test_subscription_endpoint_defaults_to_smart_profile_on_connect_host(self) -> None:
        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_token = "token_1001_secure"
            user.sub_type = "PAID"
            user.current_plan_code = "1_month"
            user.is_active = True
            user.expiry_at = _utcnow() + timedelta(days=10)
            s.add(user)
            s.commit()
        finally:
            s.close()

        with patch.object(self.api, "_nodes_for_user", side_effect=lambda user, nodes, session=None: list(nodes or [])[:1]):
            connect_default = self.client.get(
                "/s8Kx2mP7qR4wT/token_1001_secure",
                headers={"Host": "connect.pokrov.space"},
            )
        self.assertEqual(connect_default.status_code, 200, connect_default.text)
        self.assertEqual(connect_default.headers.get("content-type"), "application/json")
        self.assertIn("route", connect_default.json())

        legacy_default = self.client.get(
            "/s8Kx2mP7qR4wT/token_1001_secure",
            headers={"Host": "api.pokrov.space"},
        )
        self.assertEqual(legacy_default.status_code, 200, legacy_default.text)
        self.assertIn("text/plain", legacy_default.headers.get("content-type", ""))
        self.assertTrue(bool(legacy_default.text.strip()))

    def test_free_plain_subscription_fails_closed_when_legacy_reality_is_not_eligible(self) -> None:
        from db import SessionLocal
        from models import User

        stale_at = _utcnow() - timedelta(hours=1)
        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_token = "token_1001_secure"
            user.sub_type = "FREE"
            user.current_plan_code = "free_monthly"
            user.is_active = True
            user.expiry_at = _utcnow() + timedelta(days=10)
            node = self._legacy_reality_subscription_node(
                code="nl-free",
                access_role="free_standard",
                last_health_at=stale_at,
            )
            s.add(node)
            s.commit()
        finally:
            s.close()

        stale = self.client.get("/s8Kx2mP7qR4wT/token_1001_secure?format=plain")
        self.assertEqual(stale.status_code, 503, stale.text)
        self.assertEqual(stale.text, "")

        s = SessionLocal()
        try:
            node = s.query(self.api.Node).filter_by(code="nl-free").one()
            node.last_health_at = _utcnow()
            node.is_healthy = False
            s.commit()
        finally:
            s.close()

        unhealthy = self.client.get("/s8Kx2mP7qR4wT/token_1001_secure?format=plain")
        self.assertEqual(unhealthy.status_code, 503, unhealthy.text)
        self.assertEqual(unhealthy.text, "")

    def test_paid_happ_subscription_does_not_resurrect_rejected_legacy_nodes(self) -> None:
        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_token = "token_1001_secure"
            user.sub_type = "PAID"
            user.current_plan_code = "1_month"
            user.is_active = True
            user.expiry_at = _utcnow() + timedelta(days=10)
            s.add(
                self._legacy_reality_subscription_node(
                    code="pl",
                    access_role="paid",
                    last_health_at=_utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        rejected_states = (
            ("unhealthy", {"is_healthy": False}),
            ("draining", {"is_healthy": True, "is_draining": True}),
            (
                "non_accepting",
                {
                    "is_healthy": True,
                    "is_draining": False,
                    "accepting_new_clients": False,
                },
            ),
            (
                "disabled_legacy_profile",
                {
                    "accepting_new_clients": True,
                    "is_draining": False,
                    "legacy_profile_enabled": False,
                },
            ),
        )
        for state, values in rejected_states:
            with self.subTest(state=state):
                s = SessionLocal()
                try:
                    node = s.query(self.api.Node).filter_by(code="pl").one()
                    node.is_healthy = bool(values.get("is_healthy", True))
                    node.is_draining = bool(values.get("is_draining", False))
                    node.accepting_new_clients = bool(values.get("accepting_new_clients", True))
                    profile_enabled = bool(values.get("legacy_profile_enabled", True))
                    node.transport_profiles_json = json.dumps(
                        [{"name": "legacy_reality_fallback", "enabled": profile_enabled}]
                    )
                    s.commit()
                finally:
                    s.close()

                happ = self.client.get("/s8Kx2mP7qR4wT/token_1001_secure?format=happ")
                self.assertEqual(happ.status_code, 200, happ.text)
                self.assertIn("#custom-tunnel-config: ", happ.text)
                self.assertNotIn("vless://", happ.text)
                custom_line = next(
                    line for line in happ.text.splitlines() if line.startswith("#custom-tunnel-config: ")
                )
                config = json.loads(custom_line.split(": ", 1)[1])
                self.assertFalse(
                    any(outbound.get("type") == "vless" for outbound in config.get("outbounds", [])),
                    config,
                )

    def test_paid_stale_or_missing_telemetry_keeps_legacy_happ_recovery(self) -> None:
        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_token = "token_1001_secure"
            user.sub_type = "PAID"
            user.current_plan_code = "1_month"
            user.is_active = True
            user.expiry_at = _utcnow() + timedelta(days=10)
            s.add(
                self._legacy_reality_subscription_node(
                    code="pl",
                    access_role="paid",
                    last_health_at=_utcnow() - timedelta(hours=1),
                )
            )
            s.commit()
        finally:
            s.close()

        for state in ("stale", "missing"):
            with self.subTest(state=state):
                if state == "missing":
                    s = SessionLocal()
                    try:
                        node = s.query(self.api.Node).filter_by(code="pl").one()
                        node.last_health_at = None
                        node.last_probe_at = None
                        node.last_ok_at = None
                        s.commit()
                    finally:
                        s.close()

                plain = self.client.get("/s8Kx2mP7qR4wT/token_1001_secure?format=plain")
                self.assertEqual(plain.status_code, 200, plain.text)
                self.assertTrue(bool(plain.text.strip()))

                happ = self.client.get("/s8Kx2mP7qR4wT/token_1001_secure?format=happ")
                self.assertEqual(happ.status_code, 200, happ.text)
                self.assertIn("vless://", happ.text)
                self.assertIn("pl.example.test", happ.text)

    def test_paid_legacy_recovery_fallback_only_allows_stale_enabled_reality(self) -> None:
        from types import SimpleNamespace

        stale = SimpleNamespace(code="stale", enabled_profile=True)
        unhealthy = SimpleNamespace(code="unhealthy", enabled_profile=True)
        disabled_profile = SimpleNamespace(code="disabled-profile", enabled_profile=False)
        reasons = {"stale": "stale", "unhealthy": "unhealthy", "disabled-profile": "stale"}

        with patch.object(self.api, "_filter_nodes_for_transport_profile", return_value=[stale, unhealthy, disabled_profile]), patch.object(
            self.api, "_node_capacity_policy_by_code", return_value={}
        ), patch.object(
            self.api, "_node_supports_transport_profile", side_effect=lambda node, _profile: node.enabled_profile
        ), patch.object(
            self.api, "node_hard_reject_reason", side_effect=lambda node, **_kwargs: reasons[node.code]
        ):
            rows = self.api._paid_legacy_recovery_nodes(
                session=object(),
                nodes=[stale, unhealthy, disabled_profile],
                rollout_config={},
            )

        self.assertEqual([row.code for row in rows], ["stale"])

    def test_dashboard_and_profile_payloads_use_canonical_connect_host(self) -> None:
        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_token = "token_1001_secure"
            user.is_active = True
            user.expiry_at = _utcnow() + timedelta(days=10)
            s.commit()
        finally:
            s.close()

        headers = {"Authorization": "Bearer " + self.api.create_web_session_token(tg_id=1001, username="alice")}

        dashboard = self.client.get("/api/dashboard", headers=headers)
        self.assertEqual(dashboard.status_code, 200, dashboard.text)
        self.assertTrue(str(dashboard.json().get("subscription_url") or "").startswith("https://connect.pokrov.space/s8Kx2mP7qR4wT/"))

        profile = self.client.get("/api/user/1001", headers=headers)
        self.assertEqual(profile.status_code, 200, profile.text)
        self.assertTrue(str(profile.json().get("subscription_url") or "").startswith("https://connect.pokrov.space/s8Kx2mP7qR4wT/"))

    def test_admin_metrics_timeseries_and_nodes_traffic_endpoints(self) -> None:
        from db import SessionLocal
        from models import Event, ExternalOrder, ExternalPaymentEvent, NodeHealthSample, PayAttempt

        now = _utcnow().replace(microsecond=0)
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

        now = _utcnow().replace(microsecond=0)
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

    def test_admin_summary_uses_effective_active_status(self) -> None:
        from db import SessionLocal
        from models import User

        now = _utcnow().replace(microsecond=0)
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=3201,
                    username="effective_active",
                    uuid="00000000-0000-0000-0000-000000003201",
                    email="effective_active_3201",
                    sub_type="PAID",
                    is_active=True,
                    expiry_at=now + timedelta(days=5),
                    tos_accepted=True,
                )
            )
            s.add(
                User(
                    tg_id=3202,
                    username="effective_expired",
                    uuid="00000000-0000-0000-0000-000000003202",
                    email="effective_expired_3202",
                    sub_type="PAID",
                    is_active=True,
                    expiry_at=now - timedelta(days=1),
                    tos_accepted=True,
                )
            )
            s.add(
                User(
                    tg_id=3203,
                    username="effective_blocked",
                    uuid="00000000-0000-0000-0000-000000003203",
                    email="effective_blocked_3203",
                    sub_type="PAID",
                    is_active=False,
                    expiry_at=now + timedelta(days=5),
                    tos_accepted=True,
                )
            )
            s.commit()
        finally:
            s.close()

        summary_resp = self.client.get("/api/admin/summary", headers=admin_hdrs)
        self.assertEqual(summary_resp.status_code, 200, summary_resp.text)
        payload = summary_resp.json()
        self.assertEqual(int(payload.get("users", {}).get("active") or 0), 1)

    def test_admin_summary_exposes_truth_metrics_and_quality_status(self) -> None:
        from db import SessionLocal
        from models import Node, NodeHealthSample, ObserverUserState, User

        now = _utcnow().replace(microsecond=0)
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        s = SessionLocal()
        try:
            s.add(
                Node(
                    code="pl",
                    name="Poland",
                    host="pl.example.test",
                    vless_port=443,
                    reality_sni="www.orange.pl",
                    reality_pbk="pbk-pl",
                    reality_sid="sid-pl",
                    panel_base_url="https://pl.example.test:8444",
                    panel_path="/panel",
                    panel_user="admin",
                    panel_pass="pass",
                    inbound_id=7,
                    enabled=True,
                    observer_push_secret="observer-secret",
                    observer_last_push_at=now - timedelta(minutes=4),
                )
            )
            s.add(
                NodeHealthSample(
                    node_code="pl",
                    sampled_at=now - timedelta(minutes=2),
                    cpu_percent=31.0,
                    memory_used_mb=800,
                    memory_total_mb=2048,
                    disk_used_gb=14.0,
                    disk_total_gb=40.0,
                    disk_free_gb=26.0,
                    network_total_mbps=120.0,
                    active_clients=18,
                    panel_latency_ms=90,
                    panel_error_rate=0.0,
                    is_healthy=True,
                    score=96.0,
                )
            )
            s.add_all(
                [
                    User(
                        tg_id=3301,
                        username="paid_truth",
                        uuid="00000000-0000-0000-0000-000000003301",
                        email="paid_truth_3301",
                        sub_type="PAID",
                        is_active=True,
                        expiry_at=now + timedelta(days=15),
                        tos_accepted=True,
                        app_install_id="install-paid-3301",
                        app_last_seen_at=now - timedelta(hours=2),
                    ),
                    User(
                        tg_id=3302,
                        username="trial_truth",
                        uuid="00000000-0000-0000-0000-000000003302",
                        email="trial_truth_3302",
                        sub_type="FREE",
                        current_plan_code="trial",
                        is_active=True,
                        expiry_at=now + timedelta(days=4),
                        tos_accepted=True,
                        app_install_id="install-trial-3302",
                        app_last_seen_at=now - timedelta(hours=8),
                    ),
                    User(
                        tg_id=3303,
                        username="bonus_truth",
                        uuid="00000000-0000-0000-0000-000000003303",
                        email="bonus_truth_3303",
                        sub_type="BONUS",
                        current_plan_code="channel_bonus",
                        is_active=True,
                        expiry_at=now + timedelta(days=9),
                        tos_accepted=True,
                        channel_bonus_claimed_at=now - timedelta(hours=5),
                        app_install_id="install-bonus-3303",
                        app_last_seen_at=now - timedelta(days=3),
                    ),
                    User(
                        tg_id=3304,
                        username="free_truth",
                        uuid="00000000-0000-0000-0000-000000003304",
                        email="free_truth_3304",
                        sub_type="FREE",
                        current_plan_code="free_monthly",
                        is_active=True,
                        expiry_at=now + timedelta(days=2),
                        tos_accepted=True,
                        app_install_id="install-free-3304",
                        app_last_seen_at=now - timedelta(days=12),
                    ),
                ]
            )
            s.add_all(
                [
                    ObserverUserState(
                        tg_id=3301,
                        state="ok",
                        observed_ip_count_24h=1,
                        observed_node_count_24h=1,
                        last_observed_at=now - timedelta(hours=1),
                    ),
                    ObserverUserState(
                        tg_id=3302,
                        state="watch",
                        observed_ip_count_24h=2,
                        observed_node_count_24h=1,
                        last_observed_at=now - timedelta(hours=6),
                    ),
                ]
            )
            s.commit()
        finally:
            s.close()

        summary_resp = self.client.get("/api/admin/summary", headers=admin_hdrs)
        self.assertEqual(summary_resp.status_code, 200, summary_resp.text)
        payload = summary_resp.json()
        users = payload.get("users") or {}
        self.assertEqual(int(users.get("active_nonfree_accounts") or 0), 3)
        self.assertEqual(int(users.get("trial_accounts") or 0), 1)
        self.assertEqual(int(users.get("bonus_accounts") or 0), 1)
        self.assertEqual(int(users.get("unique_install_ids_24h") or 0), 2)
        self.assertEqual(int(users.get("unique_install_ids_7d") or 0), 3)
        self.assertEqual(int(users.get("observer_seen_accounts_24h") or 0), 2)

        quality = payload.get("data_quality") or {}
        self.assertEqual((quality.get("metrics") or {}).get("status"), "fresh")
        self.assertEqual((quality.get("metrics") or {}).get("badge"), "good")
        self.assertEqual((quality.get("app_installs") or {}).get("status"), "ok")
        self.assertEqual((quality.get("app_installs") or {}).get("badge"), "good")
        self.assertEqual((quality.get("observer") or {}).get("status"), "ok")
        self.assertEqual((quality.get("observer") or {}).get("badge"), "good")

    def test_admin_summary_marks_missing_truth_data_sources(self) -> None:
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        summary_resp = self.client.get("/api/admin/summary", headers=admin_hdrs)
        self.assertEqual(summary_resp.status_code, 200, summary_resp.text)
        payload = summary_resp.json()
        users = payload.get("users") or {}
        self.assertEqual(int(users.get("unique_install_ids_24h") or 0), 0)
        self.assertEqual(int(users.get("unique_install_ids_7d") or 0), 0)
        self.assertEqual(int(users.get("observer_seen_accounts_24h") or 0), 0)

        quality = payload.get("data_quality") or {}
        self.assertEqual((quality.get("app_installs") or {}).get("status"), "missing")
        self.assertEqual((quality.get("app_installs") or {}).get("badge"), "bad")
        self.assertTrue(bool((quality.get("app_installs") or {}).get("missing")))
        self.assertEqual((quality.get("observer") or {}).get("status"), "missing")
        self.assertEqual((quality.get("observer") or {}).get("badge"), "bad")
        self.assertTrue(bool((quality.get("observer") or {}).get("missing")))

    def test_admin_summary_includes_retention_cohorts_and_pings(self) -> None:
        from db import SessionLocal
        from models import Event, User

        now = _utcnow().replace(microsecond=0)
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=3101,
                    username="expiring_soon",
                    uuid="00000000-0000-0000-0000-000000003101",
                    email="expiring_soon_3101",
                    sub_type="PAID",
                    is_active=True,
                    expiry_at=now + timedelta(days=2),
                    tos_accepted=True,
                )
            )
            s.add(
                User(
                    tg_id=3102,
                    username="reactivation_candidate",
                    uuid="00000000-0000-0000-0000-000000003102",
                    email="reactivation_candidate_3102",
                    sub_type="FREE",
                    is_active=False,
                    expiry_at=now - timedelta(days=2),
                    tos_accepted=True,
                )
            )
            s.add(Event(tg_id=3101, event_name="expired", source="test", created_at=now - timedelta(days=1)))
            s.add(Event(tg_id=3102, event_name="expired", source="test", created_at=now - timedelta(days=2)))
            retention_flows = {
                "welcome_chain": "welcome",
                "expiry_chain:t3": "t3",
                "expiry_chain:t1": "t1",
                "expiry_chain:t0": "t0",
                "reactivation": "reactivation",
                "start99_welcome_offer": "start99_offer",
            }
            for flow_label, expected_flow in retention_flows.items():
                s.add(
                    Event(
                        tg_id=3101,
                        event_name="retention_ping",
                        source="worker",
                        meta_json=json.dumps({"flow": flow_label, "variant": "a"}),
                        created_at=now,
                    )
                )
            s.commit()
        finally:
            s.close()

        summary_resp = self.client.get("/api/admin/summary", headers=admin_hdrs)
        self.assertEqual(summary_resp.status_code, 200, summary_resp.text)
        payload = summary_resp.json()
        retention = payload.get("retention") or {}
        self.assertEqual(int(retention.get("expiring_3d") or 0), 1)
        self.assertEqual(int(retention.get("expired_7d") or 0), 2)
        self.assertEqual(int(retention.get("reactivation_candidates") or 0), 1)
        pings = retention.get("pings_24h") or {}
        self.assertEqual(int(pings.get("welcome") or 0), 1)
        self.assertEqual(int(pings.get("t3") or 0), 1)
        self.assertEqual(int(pings.get("t1") or 0), 1)
        self.assertEqual(int(pings.get("t0") or 0), 1)
        self.assertEqual(int(pings.get("reactivation") or 0), 1)
        self.assertEqual(int(pings.get("start99_offer") or 0), 1)

    def test_admin_metrics_status_reports_per_node_freshness_and_alerts(self) -> None:
        from db import SessionLocal
        from models import Node, NodeHealthSample

        now = _utcnow().replace(microsecond=0)
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        s = SessionLocal()
        try:
            s.add(
                Node(
                    code="pl",
                    name="Poland",
                    host="pl.example.test",
                    vless_port=443,
                    reality_sni="www.orange.pl",
                    reality_pbk="pbk-pl",
                    reality_sid="sid-pl",
                    panel_base_url="https://pl.example.test:8444",
                    panel_path="/panel",
                    panel_user="admin",
                    panel_pass="pass",
                    inbound_id=7,
                    enabled=True,
                )
            )
            s.add(
                Node(
                    code="de",
                    name="Germany",
                    host="de.example.test",
                    vless_port=443,
                    reality_sni="www.telekom.de",
                    reality_pbk="pbk-de",
                    reality_sid="sid-de",
                    panel_base_url="https://de.example.test:8444",
                    panel_path="/panel",
                    panel_user="admin",
                    panel_pass="pass",
                    inbound_id=9,
                    enabled=True,
                )
            )
            for minutes_ago in (1, 2, 3):
                s.add(
                    NodeHealthSample(
                        node_code="pl",
                        sampled_at=now - timedelta(minutes=minutes_ago),
                        cpu_percent=82.0,
                        memory_used_mb=1800,
                        memory_total_mb=2048,
                        disk_used_gb=38.5,
                        disk_total_gb=40.0,
                        disk_free_gb=1.5,
                        network_rx_mbps=410.0,
                        network_tx_mbps=410.0,
                        network_total_mbps=820.0,
                        active_clients=140,
                        panel_latency_ms=120,
                        panel_error_rate=0.01,
                        is_healthy=True,
                        score=92.0,
                    )
                )
            s.add(
                NodeHealthSample(
                    node_code="de",
                    sampled_at=now - timedelta(minutes=45),
                    cpu_percent=15.0,
                    memory_used_mb=700,
                    memory_total_mb=2048,
                    disk_used_gb=10.0,
                    disk_total_gb=40.0,
                    disk_free_gb=30.0,
                    active_clients=12,
                    panel_latency_ms=90,
                    panel_error_rate=0.0,
                    is_healthy=True,
                    score=95.0,
                )
            )
            s.commit()
        finally:
            s.close()

        old_stale_after = os.environ.get("NODE_METRICS_STALE_AFTER_SECONDS")
        os.environ["NODE_METRICS_STALE_AFTER_SECONDS"] = "900"
        try:
            metrics_resp = self.client.get("/api/admin/metrics/status", headers=admin_hdrs)
        finally:
            if old_stale_after is None:
                os.environ.pop("NODE_METRICS_STALE_AFTER_SECONDS", None)
            else:
                os.environ["NODE_METRICS_STALE_AFTER_SECONDS"] = old_stale_after
        self.assertEqual(metrics_resp.status_code, 200, metrics_resp.text)
        payload = metrics_resp.json()
        self.assertEqual(payload.get("status"), "stale")
        self.assertTrue(payload.get("nodes"))
        self.assertTrue(payload.get("active_alerts"))

        pl = next(row for row in payload["nodes"] if row["node_code"] == "pl")
        de = next(row for row in payload["nodes"] if row["node_code"] == "de")
        self.assertEqual(pl["status"], "fresh")
        self.assertIn("cpu_high", pl.get("alert_kinds", []))
        self.assertIn("network_high", pl.get("alert_kinds", []))
        self.assertEqual(de["status"], "stale")
        self.assertIn("stale_metrics", de.get("alert_kinds", []))
        self.assertTrue(any(alert.get("kind") == "cpu_high" and alert.get("node_code") == "pl" for alert in payload.get("active_alerts", [])))
        self.assertTrue(any(alert.get("kind") == "network_high" and alert.get("node_code") == "pl" for alert in payload.get("active_alerts", [])))

    def test_admin_nodes_health_preserves_missing_ram_and_disk_as_null(self) -> None:
        from db import SessionLocal
        from models import Node

        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        s = SessionLocal()
        try:
            s.add(
                Node(
                    code="pl",
                    name="Poland",
                    host="pl.example.test",
                    vless_port=443,
                    reality_sni="www.orange.pl",
                    reality_pbk="pbk-pl",
                    reality_sid="sid-pl",
                    panel_base_url="https://pl.example.test:8444",
                    panel_path="/panel",
                    panel_user="admin",
                    panel_pass="pass",
                    inbound_id=7,
                    enabled=True,
                    memory_used_mb=0,
                    memory_total_mb=0,
                    disk_used_gb=0.0,
                    disk_total_gb=0.0,
                    disk_free_gb=0.0,
                )
            )
            s.commit()
        finally:
            s.close()

        response = self.client.get("/api/admin/nodes/health", headers=admin_hdrs)
        self.assertEqual(response.status_code, 200, response.text)
        rows = response.json().get("nodes") or []
        pl = next(row for row in rows if row.get("code") == "pl")
        self.assertIsNone(pl["memory_used_mb"])
        self.assertIsNone(pl["memory_total_mb"])
        self.assertIsNone(pl["disk_used_gb"])
        self.assertIsNone(pl["disk_total_gb"])
        self.assertIsNone(pl["disk_free_gb"])

    def test_admin_nodes_health_exposes_network_capacity_and_peak(self) -> None:
        from db import SessionLocal
        from models import Node, NodeHealthSample

        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        now = _utcnow().replace(microsecond=0)

        s = SessionLocal()
        try:
            s.add(
                Node(
                    code="pl",
                    name="Poland",
                    host="pl.example.test",
                    vless_port=443,
                    reality_sni="www.orange.pl",
                    reality_pbk="pbk-pl",
                    reality_sid="sid-pl",
                    panel_base_url="https://pl.example.test:8444",
                    panel_path="/panel",
                    panel_user="admin",
                    panel_pass="pass",
                    inbound_id=7,
                    enabled=True,
                    network_rx_bytes_total=1_500_000_000,
                    network_tx_bytes_total=900_000_000,
                    network_rx_mbps=420.0,
                    network_tx_mbps=180.0,
                    network_total_mbps=600.0,
                )
            )
            s.add(
                NodeHealthSample(
                    node_code="pl",
                    sampled_at=now - timedelta(hours=2),
                    network_rx_mbps=500.0,
                    network_tx_mbps=280.0,
                    network_total_mbps=780.0,
                    is_healthy=True,
                    score=95.0,
                )
            )
            s.commit()
        finally:
            s.close()

        response = self.client.get("/api/admin/nodes/health", headers=admin_hdrs)
        self.assertEqual(response.status_code, 200, response.text)
        rows = response.json().get("nodes") or []
        pl = next(row for row in rows if row.get("code") == "pl")
        self.assertEqual(pl["network_rx_bytes_total"], 1_500_000_000)
        self.assertEqual(pl["network_tx_bytes_total"], 900_000_000)
        self.assertAlmostEqual(float(pl["network_total_mbps"] or 0.0), 600.0, places=2)
        self.assertAlmostEqual(float(pl["network_peak_mbps_24h"] or 0.0), 780.0, places=2)
        self.assertAlmostEqual(float(pl["network_utilization_percent"] or 0.0), 60.0, places=2)
        self.assertAlmostEqual(float(pl["network_peak_utilization_percent_24h"] or 0.0), 78.0, places=2)
        self.assertEqual(float(pl["network_port_capacity_mbps"] or 0.0), 1000.0)

    def test_admin_nodes_health_exposes_live_online_keys_and_connections(self) -> None:
        from db import SessionLocal
        from models import Node

        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        s = SessionLocal()
        try:
            s.add(
                Node(
                    code="it",
                    name="Italy",
                    host="it.example.test",
                    vless_port=443,
                    reality_sni="www.tim.it",
                    reality_pbk="pbk-it",
                    reality_sid="sid-it",
                    panel_base_url="https://it.example.test:8444",
                    panel_path="/panel",
                    panel_user="admin",
                    panel_pass="pass",
                    inbound_id=7,
                    enabled=True,
                )
            )
            s.commit()
        finally:
            s.close()

        class FakePanel:
            async def login(self):
                return True

            async def close(self):
                return True

            async def get_node_online_summaries(self, *, node_codes=None):
                self.node_codes = list(node_codes or [])
                return {
                    "it": {
                        "online_keys_now": 2,
                        "online_connections_now": 5,
                    }
                }

        original_panel = self.api.ControlPanel
        self.api.ControlPanel = FakePanel
        try:
            response = self.client.get("/api/admin/nodes/health", headers=admin_hdrs)
            self.assertEqual(response.status_code, 200, response.text)
            rows = response.json().get("nodes") or []
            it = next(row for row in rows if row.get("code") == "it")
            self.assertEqual(int(it["online_keys_now"] or 0), 2)
            self.assertEqual(int(it["online_connections_now"] or 0), 5)
        finally:
            self.api.ControlPanel = original_panel

    def test_admin_user_card_exposes_online_now_summary_and_current_nodes(self) -> None:
        from db import SessionLocal
        from models import Node, ObserverUserState, User, UserNode

        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).first()
            assert user is not None
            user.sub_token = "subtoken-1001"
            pl = Node(
                code="pl",
                name="Poland",
                host="pl.example.test",
                vless_port=443,
                reality_sni="www.orange.pl",
                reality_pbk="pbk-pl",
                reality_sid="sid-pl",
                panel_base_url="https://pl.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=1,
                enabled=True,
            )
            us = Node(
                code="us",
                name="USA",
                host="us.example.test",
                vless_port=443,
                reality_sni="www.att.com",
                reality_pbk="pbk-us",
                reality_sid="sid-us",
                panel_base_url="https://us.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=2,
                enabled=True,
            )
            nl = Node(
                code="nl",
                name="Netherlands",
                host="nl.example.test",
                vless_port=443,
                reality_sni="www.kpn.com",
                reality_pbk="pbk-nl",
                reality_sid="sid-nl",
                panel_base_url="https://nl.example.test:8444",
                panel_path="/panel",
                panel_user="admin",
                panel_pass="pass",
                inbound_id=3,
                enabled=True,
            )
            s.add_all([pl, us, nl])
            s.flush()
            s.add_all(
                [
                    UserNode(tg_id=1001, node_id=pl.id, client_uuid=str(user.uuid), panel_email=str(user.email)),
                    UserNode(tg_id=1001, node_id=us.id, client_uuid=str(user.uuid), panel_email=str(user.email)),
                    UserNode(tg_id=1001, node_id=nl.id, client_uuid=str(user.uuid), panel_email=str(user.email)),
                ]
            )
            s.add(
                ObserverUserState(
                    tg_id=1001,
                    state="watch",
                    observed_ip_count_24h=2,
                    observed_ip_count_7d=3,
                    observed_ip_count_30d=3,
                    observed_node_count_24h=2,
                    observed_node_count_7d=2,
                    observed_node_count_30d=2,
                    overlap_count_24h=0,
                )
            )
            s.commit()
        finally:
            s.close()

        class FakePanel:
            async def login(self):
                return True

            async def close(self):
                return True

            async def get_user_key_snapshots(self, *, tg_id: int, node_codes=None):
                self.tg_id = tg_id
                self.node_codes = list(node_codes or [])
                return [
                    {
                        "node_code": "pl",
                        "node_name": "Poland",
                        "node_host": "pl.example.test",
                        "client": {"id": "pl-client", "enable": True, "subId": "subtoken-1001"},
                        "runtime": {
                            "enable": True,
                            "online": True,
                            "up": 100,
                            "down": 200,
                            "total": 300,
                            "ip_count": 3,
                            "last_online_at": "2030-01-01T00:00:00Z",
                            "last_online_age_seconds": 5,
                        },
                        "error": "",
                    },
                    {
                        "node_code": "us",
                        "node_name": "USA",
                        "node_host": "us.example.test",
                        "client": {"id": "us-client", "enable": True, "subId": "subtoken-1001"},
                        "runtime": {
                            "enable": True,
                            "online": True,
                            "up": 50,
                            "down": 75,
                            "total": 125,
                            "ip_count": None,
                            "last_online_at": "2030-01-01T00:00:02Z",
                            "last_online_age_seconds": 7,
                        },
                        "error": "",
                    },
                    {
                        "node_code": "nl",
                        "node_name": "Netherlands",
                        "node_host": "nl.example.test",
                        "client": {"id": "nl-client", "enable": True, "subId": "subtoken-1001"},
                        "runtime": {
                            "enable": True,
                            "online": False,
                            "up": 25,
                            "down": 25,
                            "total": 50,
                            "ip_count": 0,
                            "last_online_at": "2030-01-01T00:10:00Z",
                            "last_online_age_seconds": 600,
                        },
                        "error": "",
                    },
                ]

        original_panel = self.api.ControlPanel
        self.api.ControlPanel = FakePanel
        try:
            response = self.client.get("/api/admin/users/1001", headers=admin_hdrs)
            self.assertEqual(response.status_code, 200, response.text)
            body = response.json()
            summary = body.get("summary") or {}
            self.assertEqual(int(summary.get("online_keys_now") or 0), 2)
            self.assertEqual(int(summary.get("online_connections_now") or 0), 4)
            self.assertEqual(int(summary.get("active_users_estimate") or 0), 2)
            self.assertEqual(summary.get("active_users_source"), "panel_ip_count_capped_by_unique_ip_24h")
            self.assertEqual(summary.get("online_node_codes_now"), ["pl", "us"])

            key_rows = {str(row.get("node_code") or ""): row for row in body.get("keys") or []}
            self.assertEqual(int(key_rows["pl"].get("current_connections") or 0), 3)
            self.assertEqual(int(key_rows["us"].get("current_connections") or 0), 1)
            self.assertEqual(int(key_rows["nl"].get("current_connections") or 0), 0)
        finally:
            self.api.ControlPanel = original_panel

    def test_api_events_accept_extended_funnel_event_names(self) -> None:
        user_hdrs = {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

        import_attempt = self.client.post(
            "/api/events",
            headers=user_hdrs,
            json={"event_name": "config_import_attempted", "source": "webapp", "meta": {"surface": "dashboard"}},
        )
        self.assertEqual(import_attempt.status_code, 200, import_attempt.text)

        connect_fail = self.client.post(
            "/api/events",
            headers=user_hdrs,
            json={"event_name": "connect_failed", "source": "webapp", "meta": {"reason": "timeout"}},
        )
        self.assertEqual(connect_fail.status_code, 200, connect_fail.text)

        import_rows = self._event_rows("config_import_attempted")
        fail_rows = self._event_rows("connect_failed")
        self.assertEqual(len(import_rows), 1)
        self.assertEqual(len(fail_rows), 1)
        self.assertEqual(import_rows[0]["meta"].get("surface"), "dashboard")
        self.assertEqual(fail_rows[0]["meta"].get("reason"), "timeout")

    def test_admin_start_links_and_wheel_config(self) -> None:
        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

        created = self._execute_admin_intent(
            action="start_link.create",
            target_type="start_link",
            target_id="launch14",
            method="POST",
            path="/api/admin/start-links",
            payload={
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

        patched = self._execute_admin_intent(
            action="start_link.update",
            target_type="start_link",
            target_id=link_id,
            method="PATCH",
            path=f"/api/admin/start-links/{link_id}",
            payload={"description": "Updated", "is_active": False},
        )
        self.assertEqual(patched.status_code, 200, patched.text)

        removed = self._execute_admin_intent(
            action="start_link.delete",
            target_type="start_link",
            target_id=link_id,
            method="DELETE",
            path=f"/api/admin/start-links/{link_id}",
            payload={},
        )
        self.assertEqual(removed.status_code, 200, removed.text)

        cfg_get = self.client.get("/api/admin/wheel-config", headers=admin_hdrs)
        self.assertEqual(cfg_get.status_code, 200, cfg_get.text)
        self.assertEqual(
            cfg_get.json()["wheel_config"],
            {
                "preset": "paid_fortnightly_discounts_v3",
                "weights": [
                    {"kind": "days", "value": 1, "weight": 7500},
                    {"kind": "discount", "value": 5, "weight": 1800},
                    {"kind": "days", "value": 3, "weight": 500},
                    {"kind": "discount", "value": 7, "weight": 150},
                    {"kind": "days", "value": 7, "weight": 40},
                    {"kind": "discount", "value": 10, "weight": 9},
                    {"kind": "days", "value": 30, "weight": 1},
                ],
                "cooldown_hours": 336,
            },
        )

        cfg_put = self._execute_admin_intent(
            action="wheel_config.update",
            target_type="config",
            target_id="wheel",
            method="PUT",
            path="/api/admin/wheel-config",
            payload={
                "preset": "paid_weekly_v1",
                "weights": [
                    {"days": 1, "weight": 9000},
                    {"days": 3, "weight": 890},
                    {"days": 7, "weight": 100},
                    {"days": 30, "weight": 10},
                ],
                "cooldown_hours": 168,
            },
        )
        self.assertEqual(cfg_put.status_code, 200, cfg_put.text)
        body = cfg_put.json().get("wheel_config") or {}
        self.assertEqual(int(body.get("cooldown_hours") or 0), 168)

        invalid = self._execute_admin_intent(
            action="wheel_config.update",
            target_type="config",
            target_id="wheel",
            method="PUT",
            path="/api/admin/wheel-config",
            payload={
                "preset": "manual",
                "weights": [
                    {"days": 1, "weight": 8999},
                    {"days": 3, "weight": 891},
                    {"days": 7, "weight": 100},
                    {"days": 30, "weight": 10},
                ],
                "cooldown_hours": 168,
            },
        )
        self.assertEqual(invalid.status_code, 400, invalid.text)
        self.assertEqual(invalid.json()["detail"]["code"], "wheel_config_invalid")

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

    def test_paid_stale_happ_uses_legacy_transport_when_requested_grpc_is_disabled(self) -> None:
        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=1001).one()
            user.sub_token = "token_1001_secure"
            user.sub_type = "PAID"
            user.is_active = True
            user.expiry_at = _utcnow() + timedelta(days=10)
            node = self._legacy_reality_subscription_node(
                code="pl", access_role="paid", last_health_at=_utcnow() - timedelta(hours=1)
            )
            node.transport_profiles_json = json.dumps([
                {"name": "legacy_reality_fallback", "enabled": True},
                {"name": "grpc_443_primary", "enabled": False},
            ])
            s.add(node)
            s.commit()
        finally:
            s.close()

        with patch.object(
            self.api.app_first_service,
            "build_client_policy",
            return_value={"transport_profile": "grpc_443_primary"},
        ):
            response = self.client.get("/s8Kx2mP7qR4wT/token_1001_secure?format=happ")
        self.assertEqual(response.status_code, 200, response.text)
        cfg = json.loads(next(line for line in response.text.splitlines() if line.startswith("#custom-tunnel-config: ")).split(": ", 1)[1])
        outbound = next(row for row in cfg["outbounds"] if row.get("type") == "vless")
        self.assertIn("reality", outbound["tls"])
        self.assertNotIn("transport", outbound)


if __name__ == "__main__":
    unittest.main()

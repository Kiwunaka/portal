import json
import os
import sys
import unittest
from pathlib import Path


class PanelClientConflictTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._saved = {}
        for k in ("DATABASE_URL", "BOT_TOKEN"):
            self._saved[k] = os.environ.get(k)
            os.environ.pop(k, None)
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"

    def tearDown(self) -> None:
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    @staticmethod
    def _node(code: str):
        from nodes_repo import NodeRuntime

        return NodeRuntime(
            id=1,
            code=code,
            name=code,
            host="example.test",
            accepting_new_clients=True,
            is_draining=False,
            vless_port=443,
            reality_sni="example.com",
            reality_pbk="pbk",
            reality_sid="sid",
            fingerprint="firefox",
            flow="xtls-rprx-vision",
            panel_base_url="http://127.0.0.1:15739",
            panel_path="xui",
            panel_user="admin",
            panel_pass="pass",
            inbound_id=1,
            weight=100,
            health_score=0.0,
            last_health_at=None,
            is_healthy=True,
            panel_latency_ms=100,
            panel_error_rate=0.0,
            active_clients=0,
            last_ok_at=None,
            cpu_percent=None,
            last_probe_at=None,
        )

    async def test_cleanup_cross_inbound_conflicts(self) -> None:
        from panel_client import PanelClient

        client = PanelClient(self._node("pl"))

        async def fake_get_inbounds():
            return [
                {"id": 1, "settings": json.dumps({"clients": []})},
                {"id": 2, "settings": json.dumps({"clients": [{"id": "u-2", "email": "User_42", "tgId": "42"}]})},
                {"id": 3, "settings": json.dumps({"clients": [{"id": "u-3", "email": "Another", "tgId": "42"}]})},
            ]

        deleted: list[tuple[int, str]] = []

        async def fake_delete_client_from_inbound(*, inbound_id: int, client_uuid: str) -> bool:
            deleted.append((inbound_id, client_uuid))
            return True

        client._get_inbounds = fake_get_inbounds
        client._delete_client_from_inbound = fake_delete_client_from_inbound

        ok = await client._cleanup_cross_inbound_conflicts(tg_id=42, email="User_42")
        self.assertTrue(ok)
        self.assertEqual(set(deleted), {(2, "u-2"), (3, "u-3")})

    async def test_ensure_client_retries_after_cleanup(self) -> None:
        from panel_client import PanelClient

        client = PanelClient(self._node("pl"))

        async def fake_find_client_by_tgid(_tg_id: int):
            return None

        cleanup_calls = 0

        async def fake_cleanup_cross_inbound_conflicts(*, tg_id: int, email: str) -> bool:
            nonlocal cleanup_calls
            cleanup_calls += 1
            return True

        add_calls = 0

        async def fake_add_client(**kwargs) -> bool:
            nonlocal add_calls
            add_calls += 1
            return add_calls == 2

        client.find_client_by_tgid = fake_find_client_by_tgid
        client._cleanup_cross_inbound_conflicts = fake_cleanup_cross_inbound_conflicts
        client.add_client = fake_add_client

        ok = await client.ensure_client(
            tg_id=42,
            client_uuid="uuid-42",
            email="User_42",
            sub_id="sub-42",
            enable=True,
        )
        self.assertTrue(ok)
        self.assertEqual(cleanup_calls, 2)
        self.assertEqual(add_calls, 2)

    async def test_ensure_client_updates_sub_id_for_existing_client(self) -> None:
        from panel_client import PanelClient

        client = PanelClient(self._node("pl"))
        existing = {"id": "uuid-42", "email": "User_42", "tgId": "42", "subId": "legacy", "enable": True}

        async def fake_find_client_by_tgid(_tg_id: int):
            return existing

        captured: dict[str, object] = {}

        async def fake_update_client_enable(client_payload: dict, enable: bool, sub_id: str | None = None) -> bool:
            captured["client"] = client_payload
            captured["enable"] = enable
            captured["sub_id"] = sub_id
            return True

        client.find_client_by_tgid = fake_find_client_by_tgid
        client.update_client_enable = fake_update_client_enable

        ok = await client.ensure_client(
            tg_id=42,
            client_uuid="uuid-42",
            email="User_42",
            sub_id="secure-42",
            enable=True,
        )
        self.assertTrue(ok)
        self.assertEqual(captured.get("sub_id"), "secure-42")

    async def test_add_client_falls_back_to_modern_clients_api(self) -> None:
        from panel_client import PanelClient

        class FakeResponse:
            def __init__(self, status: int, payload: dict):
                self.status = status
                self._payload = payload

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def json(self, *args, **kwargs):
                return self._payload

        class FakeSession:
            def __init__(self):
                self.posts: list[tuple[str, dict]] = []

            def post(self, url: str, **kwargs):
                self.posts.append((url, kwargs))
                if url.endswith("/panel/api/inbounds/addClient"):
                    return FakeResponse(404, {"success": False})
                if url.endswith("/panel/api/clients/add"):
                    return FakeResponse(200, {"success": True})
                return FakeResponse(500, {"success": False})

        fake_session = FakeSession()
        client = PanelClient(self._node("de"))
        client.session = fake_session
        client.cookies = {"session": "ok"}
        client.csrf_token = "csrf"

        ok = await client.add_client(
            client_uuid="uuid-42",
            email="User_42",
            tg_id=42,
            sub_id="secure-42",
            enable=True,
            flow="xtls-rprx-vision",
            inbound_id=1,
        )

        self.assertTrue(ok)
        self.assertEqual(len(fake_session.posts), 2)
        modern_url, modern_kwargs = fake_session.posts[1]
        self.assertTrue(modern_url.endswith("/xui/panel/api/clients/add"))
        self.assertEqual(modern_kwargs["headers"], {"X-CSRF-Token": "csrf"})
        modern_payload = modern_kwargs["json"]
        self.assertEqual(modern_payload["inboundIds"], [1])
        self.assertEqual(modern_payload["client"]["email"], "User_42")
        self.assertEqual(modern_payload["client"]["id"], "uuid-42")
        self.assertEqual(modern_payload["client"]["tgId"], 42)
        self.assertEqual(modern_payload["client"]["subId"], "secure-42")

    async def test_update_client_falls_back_to_modern_clients_api(self) -> None:
        from panel_client import PanelClient

        class FakeResponse:
            def __init__(self, status: int, payload: dict):
                self.status = status
                self._payload = payload

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def json(self, *args, **kwargs):
                return self._payload

        class FakeSession:
            def __init__(self):
                self.posts: list[tuple[str, dict]] = []

            def post(self, url: str, **kwargs):
                self.posts.append((url, kwargs))
                if "/panel/api/inbounds/updateClient/" in url:
                    return FakeResponse(404, {"success": False})
                if "/panel/api/clients/update/" in url:
                    return FakeResponse(200, {"success": True})
                return FakeResponse(500, {"success": False})

        fake_session = FakeSession()
        client = PanelClient(self._node("de"))
        client.session = fake_session
        client.cookies = {"session": "ok"}
        client.csrf_token = "csrf"

        ok = await client.update_client_enable(
            {"id": "uuid-42", "email": "User_42", "tgId": "42", "subId": "legacy"},
            True,
            sub_id="secure-42",
            inbound_id=1,
            flow="xtls-rprx-vision",
        )

        self.assertTrue(ok)
        self.assertEqual(len(fake_session.posts), 2)
        modern_url, modern_kwargs = fake_session.posts[1]
        self.assertTrue(modern_url.endswith("/xui/panel/api/clients/update/User_42"))
        modern_payload = modern_kwargs["json"]
        self.assertEqual(modern_payload["inboundIds"], [1])
        self.assertEqual(modern_payload["email"], "User_42")
        self.assertEqual(modern_payload["id"], "uuid-42")
        self.assertEqual(modern_payload["tgId"], 42)
        self.assertEqual(modern_payload["subId"], "secure-42")


if __name__ == "__main__":
    unittest.main()

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


if __name__ == "__main__":
    unittest.main()

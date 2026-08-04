import asyncio
import json
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


class PanelClientMetricsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._saved = {}
        for key in ("DATABASE_URL", "BOT_TOKEN"):
            self._saved[key] = os.environ.get(key)
            os.environ.pop(key, None)
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"

    def tearDown(self) -> None:
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    @staticmethod
    def _node():
        from nodes_repo import NodeRuntime

        return NodeRuntime(
            id=1,
            code="pl",
            name="Poland",
            host="pl.example.test",
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
        )

    async def test_get_system_metrics_parses_nested_panel_status(self) -> None:
        from panel_client import PanelClient

        client = PanelClient(self._node())

        async def fake_get_server_status():
            return {
                "cpu": 6.6559,
                "mem": {"current": 582238208, "total": 1986318336},
                "disk": {"current": 7653847040, "total": 41641402368},
                "netIO": {"up": 126925, "down": 129934},
                "netTraffic": {"sent": 1168830945544, "recv": 1179433328818},
            }

        client.get_server_status = fake_get_server_status

        metrics = await client.get_system_metrics()
        self.assertEqual(metrics["memory_used_mb"], 555)
        self.assertEqual(metrics["memory_total_mb"], 1894)
        self.assertEqual(metrics["disk_used_gb"], 7.13)
        self.assertEqual(metrics["disk_total_gb"], 38.78)
        self.assertEqual(metrics["disk_free_gb"], 31.65)
        self.assertEqual(metrics["network_tx_bytes_total"], 1168830945544)
        self.assertEqual(metrics["network_rx_bytes_total"], 1179433328818)
        self.assertEqual(metrics["network_tx_bytes_per_sec"], 126925)
        self.assertEqual(metrics["network_rx_bytes_per_sec"], 129934)

    async def test_get_client_snapshot_reuses_one_inbounds_read(self) -> None:
        from panel_client import PanelClient

        client = PanelClient(self._node())
        calls = 0

        async def fake_get_inbounds():
            nonlocal calls
            calls += 1
            return [
                {
                    "id": 1,
                    "settings": json.dumps(
                        {"clients": [{"tgId": "42", "email": "user@example.test", "enable": True}]}
                    ),
                    "clientStats": [{"email": "user@example.test", "online": True, "up": 3, "down": 4}],
                }
            ]

        client._get_inbounds = fake_get_inbounds
        found, runtime = await client.get_client_snapshot_by_tgid(42)

        self.assertEqual(calls, 1)
        self.assertEqual(found["email"], "user@example.test")
        self.assertEqual(runtime["total"], 7)

    async def test_user_key_snapshots_are_bounded_and_keep_partial_results_in_order(self) -> None:
        from control_panel import ControlPanel

        nodes = [
            SimpleNamespace(code="pl", name="Poland", host="pl.example.test", enabled=True, is_healthy=True),
            SimpleNamespace(code="nl", name="Netherlands", host="nl.example.test", enabled=True, is_healthy=False),
        ]
        panel = ControlPanel(concurrency=2)
        hostile_panel_error = (
            "panel unavailable at https://panel.example.test/private?token=super-secret"
        )

        async def fake_refresh():
            return nodes

        active = 0
        max_active = 0

        class FakeClient:
            def __init__(self, code: str) -> None:
                self.code = code

            async def get_client_snapshot_by_tgid(self, tg_id: int):
                nonlocal active, max_active
                if tg_id != 42:
                    raise AssertionError(f"unexpected tg_id: {tg_id}")
                active += 1
                max_active = max(max_active, active)
                try:
                    await asyncio.sleep(0.15)
                    if self.code == "nl":
                        raise RuntimeError(hostile_panel_error)
                    return {"email": "user@example.test", "enable": True}, {"total": 7, "online": True}
                finally:
                    active -= 1

        panel.refresh = fake_refresh
        panel._clients = {node.code: FakeClient(node.code) for node in nodes}
        started = asyncio.get_running_loop().time()
        rows = await panel.get_user_key_snapshots(tg_id=42)
        elapsed = asyncio.get_running_loop().time() - started

        self.assertEqual(max_active, 2)
        self.assertLess(elapsed, 0.25)
        self.assertEqual([row["node_code"] for row in rows], ["pl", "nl"])
        self.assertEqual(rows[0]["runtime"]["total"], 7)
        self.assertIsNone(rows[1]["client"])
        self.assertEqual(rows[1]["error"], "panel_request_failed")
        serialized = repr(rows)
        self.assertNotIn("panel unavailable", serialized)
        self.assertNotIn("https://panel.example.test/private", serialized)
        self.assertNotIn("super-secret", serialized)

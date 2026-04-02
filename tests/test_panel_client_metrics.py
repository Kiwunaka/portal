import os
import sys
import unittest
from pathlib import Path


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

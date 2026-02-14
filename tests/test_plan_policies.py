import importlib
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


class PlanPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._saved = {}
        for k in (
            "FREE_LIMIT_IP",
            "PAID_LIMIT_IP",
            "FREE_TOTAL_GB",
            "NODE_PL_FREE_LIMIT_IP",
            "NODE_PL_FREE_TOTAL_GB",
            "NODE_PL_LIMIT_IP",
            "NODE_PL_TOTAL_GB",
            "DATABASE_URL",
            "BOT_TOKEN",
        ):
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
            inbound_id=4,
            weight=100,
            health_score=0.0,
            last_health_at=None,
            is_healthy=True,
            panel_latency_ms=100,
            panel_error_rate=0.0,
            active_clients=0,
            last_ok_at=None,
        )

    def test_panel_policy_defaults(self) -> None:
        from panel_client import PanelClient

        free_client = PanelClient(self._node("pl_free"))
        paid_client = PanelClient(self._node("pl"))

        self.assertEqual(free_client._limit_ip_policy(), 1)
        self.assertEqual(free_client._total_gb_policy(), 30)
        self.assertEqual(free_client._total_bytes_policy(), 30 * 1024 * 1024 * 1024)

        self.assertEqual(paid_client._limit_ip_policy(), 5)
        self.assertEqual(paid_client._total_gb_policy(), 0)
        self.assertEqual(paid_client._total_bytes_policy(), 0)

    def test_panel_policy_node_overrides(self) -> None:
        from panel_client import PanelClient

        os.environ["FREE_LIMIT_IP"] = "1"
        os.environ["NODE_PL_FREE_LIMIT_IP"] = "3"
        os.environ["FREE_TOTAL_GB"] = "30"
        os.environ["NODE_PL_FREE_TOTAL_GB"] = "45"
        os.environ["PAID_LIMIT_IP"] = "5"
        os.environ["NODE_PL_LIMIT_IP"] = "7"

        free_client = PanelClient(self._node("pl_free"))
        paid_client = PanelClient(self._node("pl"))

        self.assertEqual(free_client._limit_ip_policy(), 3)
        self.assertEqual(free_client._total_gb_policy(), 45)
        self.assertEqual(paid_client._limit_ip_policy(), 7)

    def test_api_plan_total_gb_policy(self) -> None:
        os.environ["FREE_TOTAL_GB"] = "30"
        os.environ["FREE_LIMIT_IP"] = "1"
        os.environ["PAID_LIMIT_IP"] = "5"

        api = importlib.import_module("api")
        importlib.reload(api)

        free_user = SimpleNamespace(sub_type="FREE")
        paid_user = SimpleNamespace(sub_type="PAID")

        self.assertEqual(api._plan_total_gb(free_user), 30)
        self.assertEqual(api._plan_total_gb(paid_user), 0)
        self.assertEqual(api._plan_device_limit(free_user), 1)
        self.assertEqual(api._plan_device_limit(paid_user), 5)


if __name__ == "__main__":
    unittest.main()

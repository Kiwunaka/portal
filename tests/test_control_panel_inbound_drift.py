import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


class ControlPanelInboundDriftTests(unittest.TestCase):
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
        return SimpleNamespace(
            code="test",
            name="Test",
            host="example.test",
            inbound_id=1,
            vless_port=443,
            reality_sni="example.com",
            reality_sid="sid",
            reality_pbk="expected-public-key",
        )

    @staticmethod
    def _runtime(public_key: str) -> dict:
        return {
            "inbound_id": 1,
            "enable": True,
            "port": 443,
            "protocol": "vless",
            "network": "tcp",
            "security": "reality",
            "dest": "example.com:443",
            "server_names": ["example.com"],
            "short_ids": ["sid"],
            "public_key": public_key,
        }

    def test_missing_runtime_public_key_is_drift(self) -> None:
        from control_panel import ControlPanel

        result = ControlPanel._compare_node_inbound(self._node(), self._runtime(""))

        self.assertEqual(result["status"], "drift")
        self.assertIn("pbk_match", result["mismatches"])
        self.assertFalse(result["checks"]["pbk_match"])

    def test_matching_runtime_public_key_is_ok(self) -> None:
        from control_panel import ControlPanel

        result = ControlPanel._compare_node_inbound(
            self._node(), self._runtime("expected-public-key")
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["mismatches"], [])
        self.assertTrue(result["checks"]["pbk_match"])


if __name__ == "__main__":
    unittest.main()

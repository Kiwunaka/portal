import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


class ControlPlaneDriftReportTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        scripts_dir = str(repo_root / "scripts")
        portal_dir = str(repo_root / "portal_bot")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

    def test_compare_node_runtime_reports_ok_when_runtime_matches(self) -> None:
        import control_plane_drift_report as report

        node = SimpleNamespace(
            code="it",
            host="151.241.215.84",
            inbound_id=1,
            vless_port=443,
            reality_sni="www.tim.it",
            reality_sid="afc9734908a5e244",
            reality_pbk="s0kxPPb-NBAgk8oJjvhI7g_ZK4ln2acJlaM16ec6CCw",
        )
        inspected = {
            "inspect_error": "",
            "enable": True,
            "port": 443,
            "protocol": "vless",
            "network": "tcp",
            "security": "reality",
            "dest": "www.tim.it:443",
            "server_names": ["www.tim.it"],
            "short_ids": ["afc9734908a5e244"],
            "public_key": "s0kxPPb-NBAgk8oJjvhI7g_ZK4ln2acJlaM16ec6CCw",
        }

        result = report.compare_node_runtime(node, inspected)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["mismatches"], [])


if __name__ == "__main__":
    unittest.main()

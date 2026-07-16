import importlib.util
import sys
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "render_ru_probe_report.py"
    spec = importlib.util.spec_from_file_location("render_ru_probe_report", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RenderRuProbeReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_render_includes_reserve_status_and_classifications_for_extended_payload(self) -> None:
        report = self.module._render(
            {
                "timestamp_utc": "2026-03-23T12:00:00Z",
                "probe_host": "mini-rf-1",
                "probe_public_ip": "203.0.113.10",
                "google_reachable": True,
                "classifications": [
                    "canonical_host_problem",
                    "xhttp_alive",
                ],
                "reserve": {
                    "host": "rf1.pokrov.space",
                    "xhttp_alive": True,
                    "hysteria_alive": False,
                },
                "targets": [
                    {
                        "name": "pokrov-space",
                        "kind": "canonical",
                        "host": "pokrov.space",
                        "port": 443,
                        "ok": False,
                        "dns_ok": True,
                        "tcp_ok": True,
                        "tls_ok": False,
                        "http_ok": False,
                        "udp_ok": None,
                    },
                    {
                        "name": "reserve-xhttp",
                        "kind": "reserve_xhttp",
                        "host": "rf1.pokrov.space",
                        "port": 443,
                        "ok": True,
                        "dns_ok": True,
                        "tcp_ok": True,
                        "tls_ok": True,
                        "http_ok": None,
                        "udp_ok": None,
                    },
                ],
                "nodes": {
                    "pl": {
                        "address": "82.40.38.84:443",
                        "reachable": False,
                        "detail": "timeout",
                    }
                },
            }
        )

        self.assertIn("## Reserve", report)
        self.assertIn("rf1.pokrov.space", report)
        self.assertIn("xhttp_alive", report)
        self.assertIn("canonical_host_problem", report)
        self.assertIn("pokrov-space", report)

    def test_status_keeps_boolean_and_stage_states_distinct(self) -> None:
        self.assertEqual(self.module._status(True), "ok")
        self.assertEqual(self.module._status(False), "fail")
        self.assertEqual(self.module._status("pass"), "pass")
        self.assertEqual(self.module._status("fail"), "fail")
        self.assertEqual(self.module._status("not_run"), "not_run")
        self.assertEqual(
            self.module._status("not_applicable"),
            "not_applicable",
        )


if __name__ == "__main__":
    unittest.main()

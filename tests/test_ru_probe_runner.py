import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "ru_probe_runner.py"
    spec = importlib.util.spec_from_file_location("ru_probe_runner", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RuProbeRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_build_default_targets_includes_public_hosts_foreign_nodes_and_reserve_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inventory = Path(tmp) / "inventory.md"
            inventory.write_text(
                "\n".join(
                    [
                        "| Code | Physical name | Country | Role | Runtime status | Plan | IP |",
                        "|---|---|---|---|---|---|---|",
                        "| `brain` | `BRAINnode` | `DE` | Brain / control-plane | disabled | `2 vCPU` | `82.21.114.104` |",
                        "| `mini` | `RFMINI` | `RU` | RU probe only | enabled | `1 vCPU` | `198.18.0.10` |",
                        "| `rf1` | `RF1` | `RU` | reserve ingress / VIP-manual contour | disabled | `2 vCPU` | `198.18.0.11` |",
                        "| `pl` | `PLnode` | `PL` | Premium delivery | enabled | `1 vCPU` | `82.40.38.84` |",
                        "| `nl` | `NLnode` | `NL` | Premium delivery | enabled | `1 vCPU` | `82.24.195.93` |",
                    ]
                ),
                encoding="utf-8",
            )

            targets = self.module._build_default_targets(inventory, reserve_host="rf1.pokrov.space")

        names = {target["name"] for target in targets}
        self.assertIn("google", names)
        self.assertIn("pokrov-space", names)
        self.assertIn("app-pokrov-space", names)
        self.assertIn("api-pokrov-space", names)
        self.assertIn("node-pl", names)
        self.assertIn("node-nl", names)
        self.assertIn("reserve-xhttp", names)
        self.assertIn("reserve-hysteria", names)
        self.assertNotIn("api-telegram", names)
        self.assertNotIn("telegram-web", names)
        self.assertNotIn("node-brain", names)
        self.assertNotIn("node-mini", names)
        self.assertNotIn("node-rf1", names)

    def test_classify_probe_report_distinguishes_probe_host_canonical_node_and_reserve_states(self) -> None:
        classifications = self.module._classify_probe_report(
            {
                "google_reachable": True,
                "targets": [
                    {"name": "pokrov-space", "kind": "canonical", "ok": False},
                    {"name": "node-pl", "kind": "foreign_node", "ok": False},
                ],
                "reserve": {
                    "xhttp_alive": True,
                    "hysteria_alive": False,
                },
            }
        )

        self.assertIn("canonical_host_problem", classifications)
        self.assertIn("foreign_edge_problem", classifications)
        self.assertIn("eu_node_problem", classifications)
        self.assertIn("xhttp_alive", classifications)
        self.assertNotIn("hysteria_alive", classifications)

    def test_classify_probe_report_flags_probe_host_failures_before_other_incidents(self) -> None:
        classifications = self.module._classify_probe_report(
            {
                "google_reachable": False,
                "targets": [
                    {"name": "node-pl", "kind": "foreign_node", "ok": False},
                ],
                "reserve": {
                    "xhttp_alive": False,
                    "hysteria_alive": False,
                },
            }
        )

        self.assertEqual(classifications[0], "probe_host_problem")

    def test_classify_probe_report_ignores_telegram_targets_for_ru_gate(self) -> None:
        classifications = self.module._classify_probe_report(
            {
                "google_reachable": True,
                "targets": [
                    {"name": "api-telegram", "kind": "telegram", "ok": False},
                    {"name": "telegram-web", "kind": "telegram", "ok": False},
                    {"name": "pokrov-space", "kind": "canonical", "ok": True},
                    {"name": "node-pl", "kind": "foreign_node", "ok": True},
                ],
                "reserve": {
                    "xhttp_alive": False,
                    "hysteria_alive": False,
                },
            }
        )

        self.assertNotIn("telegram_reachability_problem", classifications)
        self.assertNotIn("canonical_host_problem", classifications)
        self.assertNotIn("foreign_edge_problem", classifications)

    def test_build_probe_notes_match_origin_label(self) -> None:
        current_notes = self.module._build_probe_notes(probe_host="current")
        brain_notes = self.module._build_probe_notes(probe_host="brain")
        ru_notes = self.module._build_probe_notes(probe_host="mini")

        self.assertIn("operator workstation", current_notes[0])
        self.assertIn("control-plane host 82.21.114.104", brain_notes[0])
        self.assertIn("external RU host", ru_notes[0])

    def test_foreign_node_probe_treats_tls_handshake_as_reachability_even_on_target_mismatch(self) -> None:
        with mock.patch.object(
            self.module.dataplane_probe,
            "probe_node_endpoint",
            return_value={
                "ok": False,
                "stage": "reality_target",
                "error_kind": "reality_target_mismatch",
                "error_message": "certificate names do not match expected reality target",
                "resolved_ips": ["82.40.38.84"],
                "latency_ms": 42,
                "tls_protocol": "TLSv1.3",
                "tls_cipher": "TLS_AES_256_GCM_SHA384",
            },
        ):
            result = self.module._run_target_probe(
                {
                    "name": "node-pl",
                    "kind": "foreign_node",
                    "host": "82.40.38.84",
                    "port": 443,
                    "sni": "",
                    "include_http": False,
                },
                timeout_sec=5.0,
            )

        self.assertTrue(result["tcp_ok"])
        self.assertTrue(result["tls_ok"])
        self.assertTrue(result["ok"])


if __name__ == "__main__":
    unittest.main()

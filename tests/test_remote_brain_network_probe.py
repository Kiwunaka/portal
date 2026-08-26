import importlib.util
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_module():
    path = SCRIPTS_DIR / "remote_brain_network_probe.py"
    spec = importlib.util.spec_from_file_location("remote_brain_network_probe", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RemoteBrainNetworkProbeTests(unittest.TestCase):
    def test_parse_inventory_uses_named_ip_column(self) -> None:
        module = _load_module()
        inventory_text = textwrap.dedent(
            """
            | Code | Physical name | Country | Role | Runtime status | Plan | IP |
            |---|---|---|---|---|---|---|
            | `brain` | `BRAINnode` | `DE` | Brain / control-plane | enabled | `2 vCPU` | `82.21.114.104` |
            | `pl` | `PLnode` | `PL` | Premium delivery | enabled | `1 vCPU` | `82.40.38.84` |
            """
        ).strip()

        with tempfile.TemporaryDirectory() as tmp_dir:
            inventory_path = Path(tmp_dir) / "inventory.md"
            inventory_path.write_text(inventory_text, encoding="utf-8")

            parsed = module._parse_inventory(inventory_path)

        self.assertEqual(
            parsed,
            {
                "brain": "82.21.114.104",
                "pl": "82.40.38.84",
            },
        )

    def test_parse_live_node_rows_is_typed_and_fail_closed(self) -> None:
        module = _load_module()

        parsed = module._parse_live_node_rows("de|de.pokrov.space|443\nnl|nl.pokrov.space|8443\n")

        self.assertEqual(
            parsed,
            [
                module.LiveNodeTarget(code="de", host="de.pokrov.space", port=443),
                module.LiveNodeTarget(code="nl", host="nl.pokrov.space", port=8443),
            ],
        )
        for invalid in (
            "de|de.pokrov.space|0",
            "de|bad host|443",
            "de|de.pokrov.space|443\nde|other.pokrov.space|443",
            "broken-row",
            "",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                module._parse_live_node_rows(invalid)

    def test_live_probe_report_never_returns_hosts_or_raw_errors(self) -> None:
        module = _load_module()
        targets = [
            module.LiveNodeTarget(code="de", host="sensitive.example", port=443),
            module.LiveNodeTarget(code="nl", host="private.example", port=8443),
        ]
        responses = iter(
            [
                (0, "open\n", ""),
                (0, "closed:sensitive.example\n", "raw sensitive error"),
            ]
        )

        original_run = module._run
        module._run = lambda *_args, **_kwargs: next(responses)
        try:
            report = module._probe_live_node_targets(object(), targets)
        finally:
            module._run = original_run

        self.assertFalse(report["ok"])
        self.assertEqual(report["node_count"], 2)
        self.assertEqual(report["nodes"][0]["tcp_status"], "open")
        self.assertEqual(report["nodes"][1]["error_kind"], "invalid_probe_result")
        encoded = json.dumps(report)
        self.assertNotIn("sensitive.example", encoded)
        self.assertNotIn("private.example", encoded)
        self.assertNotIn("raw sensitive error", encoded)

    def test_redacted_inventory_report_omits_addresses_and_fails_closed(self) -> None:
        module = _load_module()

        report = module._redact_inventory_report(
            {
                "free": {"ip": "sensitive-address", "port_9443": "closed"},
                "pl": {"ip": "other-sensitive-address", "port_443": "open"},
            }
        )

        self.assertFalse(report["ok"])
        self.assertEqual(report["target_source"], "retained_inventory_diagnostic")
        self.assertEqual(
            report["nodes"],
            [
                {"node_code": "free", "ports": {"9443": "closed"}},
                {"node_code": "pl", "ports": {"443": "open"}},
            ],
        )
        encoded = json.dumps(report)
        self.assertNotIn("sensitive-address", encoded)


if __name__ == "__main__":
    unittest.main()

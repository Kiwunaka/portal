import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "node_observability_gate.py"
    spec = importlib.util.spec_from_file_location("node_observability_gate", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class NodeObservabilityGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_node_freshness_failures_report_stale_and_unhealthy_nodes(self) -> None:
        now = datetime.utcnow()
        failures = self.module._node_state_failures(
            [
                {
                    "code": "pl",
                    "enabled": True,
                    "is_healthy": False,
                    "last_probe_at": now.isoformat(),
                    "last_health_at": now.isoformat(),
                },
                {
                    "code": "it",
                    "enabled": True,
                    "is_healthy": True,
                    "last_probe_at": (now - timedelta(minutes=90)).isoformat(),
                    "last_health_at": (now - timedelta(minutes=90)).isoformat(),
                },
            ],
            stale_after_minutes=30,
            now=now,
        )

        self.assertIn("enabled node pl is unhealthy", failures)
        self.assertIn("enabled node it has stale health data", failures)

    def test_drift_and_dns_failures_use_existing_script_payloads(self) -> None:
        drift_failures = self.module._drift_failures({"summary": {"total": 3, "ok": 2, "drift": 1}})
        dns_failures = self.module._dns_failures(
            {
                "warnings": [{"type": "shared_aaaa_across_different_nodes"}],
                "hosts": [
                    {"host": "pl.pokrov.space", "warnings": ["missing_a_record"]},
                ],
            }
        )

        self.assertEqual(drift_failures, ["control-plane drift detected on 1 node(s)"])
        self.assertIn("dns audit reported shared_aaaa_across_different_nodes", dns_failures)
        self.assertIn("dns audit host pl.pokrov.space warning: missing_a_record", dns_failures)


if __name__ == "__main__":
    unittest.main()

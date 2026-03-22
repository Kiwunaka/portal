import importlib.util
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "predeploy_node_readiness.py"
    spec = importlib.util.spec_from_file_location("predeploy_node_readiness", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PredeployNodeReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_readiness_failures_flag_stale_and_unhealthy_nodes(self) -> None:
        now = datetime(2026, 3, 22, 18, 0, 0, tzinfo=timezone.utc)
        rows = [
            self.module.NodeReadinessRow(
                code="pl",
                host="pl.pokrov.space",
                enabled=True,
                accepting_new_clients=True,
                is_draining=False,
                is_healthy=True,
                health_score=94.2,
                last_health_at=now - timedelta(minutes=4),
                last_probe_at=now - timedelta(minutes=4),
                last_probe_stage="panel_metrics",
                last_probe_error_kind="",
                last_probe_error_message="",
            ),
            self.module.NodeReadinessRow(
                code="us",
                host="us.pokrov.space",
                enabled=True,
                accepting_new_clients=True,
                is_draining=False,
                is_healthy=False,
                health_score=20.0,
                last_health_at=now - timedelta(hours=2),
                last_probe_at=now - timedelta(hours=2),
                last_probe_stage="tcp_connect",
                last_probe_error_kind="tcp_timeout",
                last_probe_error_message="timed out",
            ),
        ]

        failures = self.module._readiness_failures(
            rows,
            stale_after_seconds=1800,
            now=now,
        )

        self.assertIn("unhealthy:us", failures)
        self.assertIn("stale:us", failures)
        self.assertIn("probe_error:us:tcp_timeout", failures)

    def test_dns_and_drift_failures_are_aggregated(self) -> None:
        dns_report = {
            "hosts": [
                {"code": "pl", "warnings": []},
                {"code": "us", "warnings": ["missing_a_record"]},
            ],
            "warnings": [{"type": "shared_aaaa_across_different_nodes"}],
        }
        drift_payload = {
            "summary": {"total": 2, "ok": 1, "drift": 1},
            "results": [
                {"node_code": "pl", "status": "ok", "mismatches": []},
                {"node_code": "us", "status": "drift", "mismatches": ["pbk_match", "sni_match"]},
            ],
        }

        failures = self.module._aggregate_predeploy_failures(
            readiness_failures=[],
            dns_report=dns_report,
            drift_payload=drift_payload,
        )

        self.assertIn("dns:us:missing_a_record", failures)
        self.assertIn("dns_warning:shared_aaaa_across_different_nodes", failures)
        self.assertIn("drift:us:pbk_match,sni_match", failures)

    def test_dataplane_probe_retries_before_failing(self) -> None:
        row = self.module.NodeReadinessRow(
            code="pl",
            host="pl.pokrov.space",
            enabled=True,
            accepting_new_clients=True,
            is_draining=False,
            is_healthy=True,
            health_score=94.2,
            last_health_at=None,
            last_probe_at=None,
            last_probe_stage="",
            last_probe_error_kind="",
            last_probe_error_message="",
        )
        failed = self.module.DataplaneProbeResult(
            code="pl",
            host="pl.pokrov.space",
            dns_ok=True,
            tcp_ok=False,
            tls_ok=False,
            target_tls_ok=False,
            dns_records=["203.0.113.10"],
            error_kind="tcp_connect_error",
            error_message="timed out",
        )
        recovered = self.module.DataplaneProbeResult(
            code="pl",
            host="pl.pokrov.space",
            dns_ok=True,
            tcp_ok=True,
            tls_ok=True,
            target_tls_ok=True,
            dns_records=["203.0.113.10"],
            error_kind="",
            error_message="",
        )

        with patch.object(self.module, "_probe_node_dataplane", side_effect=[failed, recovered]) as probe_mock:
            result = self.module._probe_node_dataplane_with_retry(row, attempts=2, retry_delay_sec=0)

        self.assertEqual(probe_mock.call_count, 2)
        self.assertTrue(result.tcp_ok)
        self.assertTrue(result.target_tls_ok)


if __name__ == "__main__":
    unittest.main()

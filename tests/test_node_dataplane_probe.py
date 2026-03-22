import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "node_dataplane_probe.py"
    spec = importlib.util.spec_from_file_location("node_dataplane_probe", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class NodeDataplaneProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_probe_endpoint_reports_success_when_all_stages_pass(self) -> None:
        with mock.patch.object(
            self.module,
            "_resolve_dns",
            return_value={"resolved_ips": ["1.2.3.4"], "stage": "dns"},
        ), mock.patch.object(
            self.module,
            "_probe_tcp",
            return_value={"latency_ms": 23, "stage": "tcp_443"},
        ), mock.patch.object(
            self.module,
            "_probe_tls",
            return_value={
                "tls_protocol": "TLSv1.3",
                "tls_cipher": "TLS_AES_256_GCM_SHA384",
                "certificate_names": ["www.example.com"],
                "target_ok": True,
                "stage": "reality_target",
            },
        ):
            result = self.module.probe_node_endpoint(host="pl.pokrov.space", sni="www.example.com")

        self.assertTrue(result["ok"])
        self.assertEqual(result["stage"], "reality_target")
        self.assertEqual(result["error_kind"], "")
        self.assertEqual(result["certificate_names"], ["www.example.com"])

    def test_probe_endpoint_reports_target_mismatch(self) -> None:
        with mock.patch.object(
            self.module,
            "_resolve_dns",
            return_value={"resolved_ips": ["1.2.3.4"], "stage": "dns"},
        ), mock.patch.object(
            self.module,
            "_probe_tcp",
            return_value={"latency_ms": 23, "stage": "tcp_443"},
        ), mock.patch.object(
            self.module,
            "_probe_tls",
            return_value={
                "tls_protocol": "TLSv1.3",
                "tls_cipher": "TLS_AES_256_GCM_SHA384",
                "certificate_names": ["other.example.com"],
                "target_ok": False,
                "stage": "reality_target",
                "error_kind": "reality_target_mismatch",
                "error_message": "certificate names do not match expected reality target",
            },
        ):
            result = self.module.probe_node_endpoint(host="pl.pokrov.space", sni="www.example.com")

        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "reality_target")
        self.assertEqual(result["error_kind"], "reality_target_mismatch")

    def test_validate_reality_target_accepts_exact_and_wildcard_names(self) -> None:
        self.assertTrue(self.module._certificate_matches_expected_target("www.example.com", ["www.example.com"]))
        self.assertTrue(self.module._certificate_matches_expected_target("api.example.com", ["*.example.com"]))
        self.assertFalse(self.module._certificate_matches_expected_target("www.example.com", ["cdn.example.net"]))


if __name__ == "__main__":
    unittest.main()

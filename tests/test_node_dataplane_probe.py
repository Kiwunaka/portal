import importlib.util
import socket
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
            return_value={
                "resolved_ips": ["1.2.3.4"],
                "resolved_ipv4": ["1.2.3.4"],
                "resolved_ipv6": [],
                "stage": "dns",
            },
        ), mock.patch.object(
            self.module,
            "_probe_tcp",
            return_value={
                "latency_ms": 23,
                "stage": "tcp_443",
                "connected_ip": "1.2.3.4",
                "connected_family": "ipv4",
            },
        ), mock.patch.object(
            self.module,
            "_probe_tls",
            return_value={
                "tls_protocol": "TLSv1.3",
                "tls_cipher": "TLS_AES_256_GCM_SHA384",
                "certificate_names": ["www.example.com"],
                "target_ok": True,
                "stage": "reality_target",
                "connected_ip": "1.2.3.4",
                "connected_family": "ipv4",
            },
        ):
            result = self.module.probe_node_endpoint(host="pl.pokrov.space", sni="www.example.com")

        self.assertTrue(result["ok"])
        self.assertEqual(result["stage"], "reality_target")
        self.assertEqual(result["error_kind"], "")
        self.assertEqual(result["certificate_names"], ["www.example.com"])
        self.assertEqual(result["probe_classification"], "healthy")
        self.assertEqual(result["ipv4_health"], "healthy")
        self.assertEqual(result["ipv6_health"], "unavailable")
        self.assertEqual(
            result["transport_health"],
            {
                "dns_resolution": "healthy",
                "tcp_connect": "healthy",
                "tls_handshake": "healthy",
                "reality_target": "healthy",
            },
        )
        self.assertEqual(result["root_cause_summary"], "DNS, TCP, TLS, and reality-target checks passed.")
        self.assertIn("1.2.3.4", result["root_cause_detail"])
        self.assertIn("ipv4", result["root_cause_detail"])

    def test_probe_endpoint_reports_target_mismatch(self) -> None:
        with mock.patch.object(
            self.module,
            "_resolve_dns",
            return_value={
                "resolved_ips": ["1.2.3.4"],
                "resolved_ipv4": ["1.2.3.4"],
                "resolved_ipv6": [],
                "stage": "dns",
            },
        ), mock.patch.object(
            self.module,
            "_probe_tcp",
            return_value={
                "latency_ms": 23,
                "stage": "tcp_443",
                "connected_ip": "1.2.3.4",
                "connected_family": "ipv4",
            },
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
                "connected_ip": "1.2.3.4",
                "connected_family": "ipv4",
            },
        ):
            result = self.module.probe_node_endpoint(host="pl.pokrov.space", sni="www.example.com")

        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "reality_target")
        self.assertEqual(result["error_kind"], "reality_target_mismatch")
        self.assertEqual(result["probe_classification"], "provider_specific_path")
        self.assertEqual(result["ipv4_health"], "degraded")
        self.assertEqual(result["ipv6_health"], "unavailable")
        self.assertEqual(
            result["transport_health"],
            {
                "dns_resolution": "healthy",
                "tcp_connect": "healthy",
                "tls_handshake": "healthy",
                "reality_target": "degraded",
            },
        )
        self.assertIn("certificate names did not match", result["root_cause_summary"].lower())
        self.assertIn("other.example.com", result["root_cause_detail"])
        self.assertIn("www.example.com", result["root_cause_detail"])

    def test_probe_endpoint_populates_default_health_fields_for_dns_failures(self) -> None:
        with mock.patch.object(
            self.module,
            "_resolve_dns",
            side_effect=socket.gaierror("dns failed"),
        ):
            result = self.module.probe_node_endpoint(host="pl.pokrov.space", sni="www.example.com")

        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "dns")
        self.assertEqual(result["error_kind"], "dns_lookup_failed")
        self.assertEqual(result["probe_classification"], "dns_failure")
        self.assertEqual(result["ipv4_health"], "unknown")
        self.assertEqual(result["ipv6_health"], "unknown")
        self.assertEqual(
            result["transport_health"],
            {
                "dns_resolution": "degraded",
                "tcp_connect": "unavailable",
                "tls_handshake": "unavailable",
                "reality_target": "unavailable",
            },
        )
        self.assertIn("dns lookup failed", result["root_cause_summary"].lower())
        self.assertIn("pl.pokrov.space", result["root_cause_detail"])
        self.assertIn("dns failed", result["root_cause_detail"].lower())

    def test_probe_endpoint_derives_hoster_metadata_from_connected_ip(self) -> None:
        with mock.patch.object(
            self.module,
            "_resolve_dns",
            return_value={
                "resolved_ips": ["5.45.84.10"],
                "resolved_ipv4": ["5.45.84.10"],
                "resolved_ipv6": [],
                "stage": "dns",
            },
        ), mock.patch.object(
            self.module,
            "_probe_tcp",
            return_value={
                "latency_ms": 19,
                "stage": "tcp_443",
                "connected_ip": "5.45.84.10",
                "connected_family": "ipv4",
            },
        ), mock.patch.object(
            self.module,
            "_probe_tls",
            return_value={
                "tls_protocol": "TLSv1.3",
                "tls_cipher": "TLS_AES_256_GCM_SHA384",
                "certificate_names": ["www.example.com"],
                "target_ok": True,
                "stage": "reality_target",
                "connected_ip": "5.45.84.10",
                "connected_family": "ipv4",
            },
        ), mock.patch.object(
            self.module.socket,
            "gethostbyaddr",
            return_value=("static.hetzner.de", [], ["5.45.84.10"]),
        ):
            result = self.module.probe_node_endpoint(host="pl.pokrov.space", sni="www.example.com")

        self.assertEqual(result["hoster_family"], "hetzner")
        self.assertEqual(result["hoster_asn"], "AS24940")
        self.assertEqual(result["hoster_subnet"], "5.45.84.0/24")

    def test_probe_endpoint_uses_distinct_telegram_app_and_web_semantics(self) -> None:
        with mock.patch.object(
            self.module,
            "_resolve_dns",
            return_value={
                "resolved_ips": ["149.154.167.220"],
                "resolved_ipv4": ["149.154.167.220"],
                "resolved_ipv6": [],
                "stage": "dns",
            },
        ), mock.patch.object(
            self.module,
            "_probe_tcp",
            return_value={
                "latency_ms": 25,
                "stage": "tcp_443",
                "connected_ip": "149.154.167.220",
                "connected_family": "ipv4",
            },
        ), mock.patch.object(
            self.module,
            "_probe_tls",
            return_value={
                "tls_protocol": "TLSv1.3",
                "tls_cipher": "TLS_AES_256_GCM_SHA384",
                "certificate_names": ["api.telegram.org"],
                "target_ok": True,
                "stage": "reality_target",
                "connected_ip": "149.154.167.220",
                "connected_family": "ipv4",
            },
        ):
            app_result = self.module.probe_node_endpoint(host="api.telegram.org", sni="api.telegram.org")

        with mock.patch.object(
            self.module,
            "_resolve_dns",
            side_effect=socket.gaierror("telegram web dns failed"),
        ):
            web_result = self.module.probe_node_endpoint(host="t.me", sni="t.me")

        self.assertEqual(app_result["target_semantics"], "telegram_app_path")
        self.assertIn("telegram app path", app_result["root_cause_summary"].lower())
        self.assertEqual(web_result["target_semantics"], "telegram_web_path")
        self.assertIn("telegram web path", web_result["root_cause_summary"].lower())

    def test_validate_reality_target_accepts_exact_and_wildcard_names(self) -> None:
        self.assertTrue(self.module._certificate_matches_expected_target("www.example.com", ["www.example.com"]))
        self.assertTrue(self.module._certificate_matches_expected_target("api.example.com", ["*.example.com"]))
        self.assertFalse(self.module._certificate_matches_expected_target("www.example.com", ["cdn.example.net"]))

    def test_probe_tls_treats_missing_certificate_names_as_unknown_not_mismatch(self) -> None:
        class _FakeSocket:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        class _FakeTlsSocket:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def getpeercert(self):
                return {}

            def version(self):
                return "TLSv1.3"

            def cipher(self):
                return ("TLS_AES_256_GCM_SHA384", "", "")

        class _FakeContext:
            check_hostname = False
            verify_mode = None

            def wrap_socket(self, sock, server_hostname=None):
                return _FakeTlsSocket()

        with mock.patch.object(self.module.ssl, "create_default_context", return_value=_FakeContext()), mock.patch.object(
            self.module.socket,
            "create_connection",
            return_value=_FakeSocket(),
        ):
            result = self.module._probe_tls("pl.pokrov.space", 443, "www.example.com", 5.0)

        self.assertEqual(result["certificate_names"], [])
        self.assertTrue(result["target_ok"])
        self.assertNotIn("error_kind", result)


if __name__ == "__main__":
    unittest.main()

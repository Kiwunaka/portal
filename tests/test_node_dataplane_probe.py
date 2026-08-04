import importlib.util
import io
import json
import socket
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "node_dataplane_probe.py"
    spec = importlib.util.spec_from_file_location("node_dataplane_probe", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _certificate_der(*, common_name: str, dns_names: list[str]) -> bytes:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.now(timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName(name) for name in dns_names]), critical=False)
        .sign(key, hashes.SHA256())
    )
    return certificate.public_bytes(serialization.Encoding.DER)


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
        self.assertEqual(result["probe_kind"], "edge_reachability")
        self.assertTrue(result["edge_reachability_ok"])
        self.assertEqual(result["stage"], "reality_target")
        self.assertEqual(result["error_kind"], "")
        self.assertNotIn("certificate_names", result)
        self.assertNotIn("host", result)
        self.assertNotIn("sni", result)
        self.assertNotIn("resolved_ips", result)
        self.assertNotIn("connected_ip", result)
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
        self.assertEqual(result["root_cause_detail"], "edge_reachability_healthy")

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
        self.assertFalse(result["edge_reachability_ok"])
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
        self.assertEqual(result["root_cause_detail"], "reality_target_mismatch")

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
        self.assertEqual(result["root_cause_detail"], "dns_lookup_failed")

    def test_probe_stdout_and_artifact_redact_endpoint_and_exception_material(self) -> None:
        sensitive_values = ("secret-node.example", "secret-sni.example", "203.0.113.99", "cert.example", "private-token")
        with mock.patch.object(
            self.module,
            "_resolve_dns",
            return_value={
                "resolved_ips": [sensitive_values[2]],
                "resolved_ipv4": [sensitive_values[2]],
                "resolved_ipv6": [],
                "stage": "dns",
            },
        ), mock.patch.object(
            self.module,
            "_probe_tcp",
            return_value={"latency_ms": 23, "stage": "tcp_443", "connected_ip": sensitive_values[2], "connected_family": "ipv4"},
        ), mock.patch.object(
            self.module,
            "_probe_tls",
            return_value={
                "certificate_names": [sensitive_values[3]],
                "target_ok": False,
                "stage": "reality_target",
                "error_kind": "reality_target_mismatch",
                "error_message": sensitive_values[4],
                "connected_ip": sensitive_values[2],
                "connected_family": "ipv4",
            },
        ):
            result = self.module.probe_node_endpoint(host=sensitive_values[0], sni=sensitive_values[1])
            rendered = json.dumps(result, default=str)
            for value in sensitive_values:
                self.assertNotIn(value, rendered)

        with mock.patch.object(self.module, "_resolve_dns", side_effect=socket.gaierror("private-token secret-node.example")):
            failure = self.module.probe_node_endpoint(host=sensitive_values[0], sni=sensitive_values[1])
        rendered_failure = json.dumps(failure, default=str)
        for value in sensitive_values:
            self.assertNotIn(value, rendered_failure)

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            sys,
            "argv",
            ["node_dataplane_probe.py", "--host", sensitive_values[0], "--sni", sensitive_values[1], "--out", str(Path(tmp) / "probe.json")],
        ), mock.patch.object(self.module, "probe_node_endpoint", return_value=result), mock.patch(
            "sys.stdout", new_callable=io.StringIO
        ) as stdout:
            self.assertEqual(self.module.main(), 2)
            artifact = (Path(tmp) / "probe.json").read_text(encoding="utf-8")
            for value in sensitive_values:
                self.assertNotIn(value, stdout.getvalue())
                self.assertNotIn(value, artifact)

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
        self.assertIsNone(result["hoster_subnet"])

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

    def test_probe_tls_fails_closed_when_cert_none_has_no_der_certificate(self) -> None:
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

            def getpeercert(self, binary_form=False):
                return None if binary_form else {}

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
        self.assertFalse(result["target_check_available"])
        self.assertFalse(result["target_ok"])
        self.assertEqual(result["error_kind"], "reality_target_unavailable")

    def test_probe_tls_parses_der_names_when_cert_none_mapping_is_empty(self) -> None:
        certificate_der = _certificate_der(common_name="fallback.example.test", dns_names=["*.example.test"])

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

            def getpeercert(self, binary_form=False):
                return certificate_der if binary_form else {}

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
            result = self.module._probe_tls("pl.pokrov.space", 443, "api.example.test", 5.0)

        self.assertEqual(result["certificate_names"], ["*.example.test", "fallback.example.test"])
        self.assertTrue(result["target_check_available"])
        self.assertTrue(result["target_ok"])


if __name__ == "__main__":
    unittest.main()

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_module():
    path = SCRIPTS_DIR / "remote_transport_front_smoke.py"
    spec = importlib.util.spec_from_file_location("remote_transport_front_smoke", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class RemoteTransportFrontSmokeTests(unittest.TestCase):
    def test_build_tls_probe_command_uses_sni_and_port_443(self) -> None:
        module = _load_module()

        command = module.build_tls_probe_command(
            address="front.example.test",
            server_name="connect.pokrov.space",
        )

        self.assertIn("openssl s_client", command)
        self.assertIn("-connect front.example.test:443", command)
        self.assertIn("-servername connect.pokrov.space", command)

    def test_parse_tls_probe_output_reports_successful_handshake(self) -> None:
        module = _load_module()

        result = module.parse_tls_probe_output(
            """
CONNECTION ESTABLISHED
Protocol version: TLSv1.3
Ciphersuite: TLS_AES_256_GCM_SHA384
Peer certificate: CN = connect.pokrov.space
Verification: OK
DONE
""".strip(),
            "",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["protocol"], "TLSv1.3")
        self.assertEqual(result["server_name"], "connect.pokrov.space")
        self.assertEqual(result["error"], "")

    def test_parse_tls_probe_output_reports_failure_details(self) -> None:
        module = _load_module()

        result = module.parse_tls_probe_output(
            "",
            "140735229867776:error:0A000458:SSL routines:ssl3_read_bytes:tlsv1 unrecognized name",
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["protocol"], "")
        self.assertIn("unrecognized name", result["error"])


if __name__ == "__main__":
    unittest.main()

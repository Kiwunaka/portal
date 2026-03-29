import importlib.util
import sys
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "remote_install_mini_canary_stack.py"
    spec = importlib.util.spec_from_file_location("remote_install_mini_canary_stack", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RemoteInstallMiniCanaryStackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_build_xray_config_uses_packet_up_xhttp(self) -> None:
        config = self.module.build_xray_config(
            client_id="11111111-1111-1111-1111-111111111111",
            xhttp_path="/pokrov-test",
        )

        inbound = config["inbounds"][0]
        self.assertEqual(inbound["protocol"], "vless")
        self.assertEqual(inbound["streamSettings"]["network"], "xhttp")
        self.assertEqual(inbound["streamSettings"]["xhttpSettings"]["mode"], "packet-up")
        self.assertEqual(inbound["streamSettings"]["xhttpSettings"]["path"], "/pokrov-test")

    def test_build_hysteria_config_binds_udp_443_and_uses_existing_tls_files(self) -> None:
        rendered = self.module.build_hysteria_config(
            auth_password="secret-pass",
            cert_path="/etc/hysteria/server.crt",
            key_path="/etc/hysteria/server.key",
        )

        self.assertIn("listen: :443", rendered)
        self.assertIn("password: secret-pass", rendered)
        self.assertIn("cert: /etc/hysteria/server.crt", rendered)
        self.assertIn("key: /etc/hysteria/server.key", rendered)

    def test_build_nginx_site_config_uses_requested_domain_and_cert_paths(self) -> None:
        rendered = self.module.build_nginx_site_config(
            xhttp_path="/pokrov-test",
            server_names=["pokrovvpn.duckdns.org"],
            cert_path="/etc/letsencrypt/live/pokrovvpn.duckdns.org/fullchain.pem",
            key_path="/etc/letsencrypt/live/pokrovvpn.duckdns.org/privkey.pem",
        )

        self.assertIn("server_name pokrovvpn.duckdns.org;", rendered)
        self.assertIn("location ^~ /pokrov-test", rendered)
        self.assertIn("proxy_pass http://127.0.0.1:10080;", rendered)
        self.assertIn("ssl_certificate /etc/letsencrypt/live/pokrovvpn.duckdns.org/fullchain.pem;", rendered)
        self.assertIn("ssl_certificate_key /etc/letsencrypt/live/pokrovvpn.duckdns.org/privkey.pem;", rendered)
        self.assertIn("index index.html index.htm;", rendered)

    def test_build_client_links_returns_hiddify_ready_links(self) -> None:
        links = self.module.build_client_links(
            endpoint="pokrovvpn.duckdns.org",
            sni="pokrovvpn.duckdns.org",
            client_id="11111111-1111-1111-1111-111111111111",
            xhttp_path="/pokrov-test",
            hy2_password="secret-pass",
        )

        self.assertIn("type=xhttp", links["xhttp"])
        self.assertIn("mode=packet-up", links["xhttp"])
        self.assertIn("core=xray", links["xhttp"])
        self.assertIn("allowInsecure=0", links["xhttp"])
        self.assertTrue(links["xhttp"].startswith("xvless://"))
        self.assertIn("@pokrovvpn.duckdns.org:443", links["xhttp"])
        self.assertIn("insecure=0", links["hysteria2"])
        self.assertIn("@pokrovvpn.duckdns.org:443", links["hysteria2"])
        self.assertTrue(links["hysteria2"].startswith("hysteria2://"))


if __name__ == "__main__":
    unittest.main()

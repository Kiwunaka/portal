import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_module():
    path = SCRIPTS_DIR / "remote_apply_transport_front.py"
    spec = importlib.util.spec_from_file_location("remote_apply_transport_front", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class RemoteApplyTransportFrontTests(unittest.TestCase):
    def test_default_transport_front_routes_include_reserve_xhttp_cdn_route(self) -> None:
        module = _load_module()

        routes = module.default_transport_front_routes()

        by_name = {route["name"]: route for route in routes}
        self.assertIn("reserve_xhttp_cdn", by_name)
        self.assertEqual(by_name["reserve_xhttp_cdn"]["server_names"], ["cdn.connect.pokrov.space"])
        self.assertEqual(by_name["reserve_xhttp_cdn"]["backend_host"], "127.0.0.1")
        self.assertEqual(by_name["reserve_xhttp_cdn"]["backend_port"], 12443)
        self.assertEqual(by_name["reserve_xhttp_cdn"]["server_name_suffixes"], [])
        self.assertFalse(by_name["reserve_xhttp_cdn"]["send_proxy_v2"])

    def test_normalize_transport_front_route_accepts_loopback_targets_only(self) -> None:
        module = _load_module()

        normalized = module.normalize_transport_front_route(
            {
                "name": "grpc_443_primary",
                "server_names": [" Connect.Pokrov.Space ", "grpc.connect.pokrov.space"],
                "backend_host": "127.0.0.1",
                "backend_port": "11443",
            }
        )

        self.assertEqual(normalized["name"], "grpc_443_primary")
        self.assertEqual(
            normalized["server_names"],
            ["connect.pokrov.space", "grpc.connect.pokrov.space"],
        )
        self.assertEqual(normalized["backend_host"], "127.0.0.1")
        self.assertEqual(normalized["backend_port"], 11443)

    def test_normalize_transport_front_route_rejects_config_injection(self) -> None:
        module = _load_module()

        for field, value in (
            ("name", "smart_dns\nbackend injected"),
            ("server_names", ["safe.example\nbackend injected"]),
        ):
            route = {
                "name": "smart_dns",
                "server_names": ["safe.example"],
                "backend_host": "127.0.0.1",
                "backend_port": 18443,
            }
            route[field] = value
            with self.assertRaises(ValueError):
                module.normalize_transport_front_route(route)

    def test_normalize_transport_front_route_rejects_non_loopback_backends(self) -> None:
        module = _load_module()

        with self.assertRaises(ValueError):
            module.normalize_transport_front_route(
                {
                    "name": "legacy_reality_fallback",
                    "server_names": ["connect.pokrov.space"],
                    "backend_host": "10.0.0.4",
                    "backend_port": 10443,
                }
            )

    def test_render_transport_front_config_routes_sni_to_loopback_backends(self) -> None:
        module = _load_module()

        routes = [
            module.normalize_transport_front_route(
                {
                    "name": "legacy_reality_fallback",
                    "server_names": ["connect.pokrov.space"],
                    "backend_host": "127.0.0.1",
                    "backend_port": 10443,
                }
            ),
            module.normalize_transport_front_route(
                {
                    "name": "grpc_443_primary",
                    "server_names": ["grpc.connect.pokrov.space", "mux.connect.pokrov.space"],
                    "backend_host": "127.0.0.1",
                    "backend_port": 11443,
                }
            ),
            module.normalize_transport_front_route(
                {
                    "name": "reserve_xhttp_cdn",
                    "server_names": ["cdn.connect.pokrov.space"],
                    "backend_host": "127.0.0.1",
                    "backend_port": 12443,
                }
            ),
        ]

        rendered = module.render_transport_front_config(
            routes,
            bind_address=":443",
            default_route_name="legacy_reality_fallback",
        )

        self.assertIn("bind :443", rendered)
        self.assertIn(
            "use_backend be_legacy_reality_fallback if { req.ssl_sni -i connect.pokrov.space }",
            rendered,
        )
        self.assertIn(
            "use_backend be_grpc_443_primary if { req.ssl_sni -i grpc.connect.pokrov.space }",
            rendered,
        )
        self.assertIn(
            "use_backend be_reserve_xhttp_cdn if { req.ssl_sni -i cdn.connect.pokrov.space }",
            rendered,
        )
        self.assertIn("default_backend be_legacy_reality_fallback", rendered)
        self.assertIn("server legacy_reality_fallback 127.0.0.1:10443 check", rendered)
        self.assertIn("server grpc_443_primary 127.0.0.1:11443 check", rendered)
        self.assertIn("server reserve_xhttp_cdn 127.0.0.1:12443 check", rendered)

    def test_render_transport_front_config_supports_fronted_smart_dns_with_proxy_v2(self) -> None:
        module = _load_module()

        rendered = module.render_transport_front_config(
            [
                {
                    "name": "legacy_reality_fallback",
                    "server_names": ["connect.pokrov.space"],
                    "backend_host": "127.0.0.1",
                    "backend_port": 10443,
                },
                {
                    "name": "smart_dns",
                    "server_names": ["dns.pokrov.space"],
                    "server_name_suffixes": ["openai.com", "xbox.com"],
                    "backend_host": "127.0.0.1",
                    "backend_port": 18443,
                    "send_proxy_v2": True,
                },
            ],
            default_route_name="legacy_reality_fallback",
        )

        self.assertIn("use_backend be_smart_dns if { req.ssl_sni -i dns.pokrov.space }", rendered)
        self.assertIn("use_backend be_smart_dns if { req.ssl_sni -i openai.com }", rendered)
        self.assertIn("use_backend be_smart_dns if { req.ssl_sni -m end -i .openai.com }", rendered)
        self.assertIn("use_backend be_smart_dns if { req.ssl_sni -i xbox.com }", rendered)
        self.assertIn("server smart_dns 127.0.0.1:18443 check send-proxy-v2", rendered)

    def test_build_apply_commands_reloads_systemd_and_checks_listener(self) -> None:
        module = _load_module()

        commands = module.build_apply_commands(unit_name="portal-transport-front")

        joined = "\n".join(commands)
        self.assertIn("systemctl daemon-reload", joined)
        self.assertIn("systemctl enable portal-transport-front", joined)
        self.assertIn("systemctl restart portal-transport-front", joined)
        self.assertIn("systemctl status --no-pager portal-transport-front", joined)
        self.assertIn("ss -tlnp", joined)


if __name__ == "__main__":
    unittest.main()

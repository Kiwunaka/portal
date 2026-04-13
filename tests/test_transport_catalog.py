from __future__ import annotations

import importlib
import json
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse


class TransportCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"

        self.transport_catalog = importlib.import_module("transport_catalog")
        importlib.reload(self.transport_catalog)
        self.api = importlib.import_module("api")
        importlib.reload(self.api)

    def test_node_transport_profiles_fall_back_to_legacy_compat_fields(self) -> None:
        node = SimpleNamespace(
            host="legacy.example.test",
            vless_port=443,
            reality_sni="legacy-sni.example.test",
            reality_pbk="legacy-pbk",
            reality_sid="legacy-sid",
            fingerprint="firefox",
            flow="xtls-rprx-vision",
            inbound_id=7,
            transport_profiles_json="",
        )

        profiles = self.transport_catalog.node_transport_profiles(node)

        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0]["name"], "legacy_reality_fallback")
        self.assertEqual(profiles[0]["kind"], "reality")
        self.assertEqual(profiles[0]["port"], 443)
        self.assertEqual(profiles[0]["inbound_id"], 7)

    def test_generate_vless_link_uses_legacy_profile_from_catalog(self) -> None:
        node = SimpleNamespace(
            host="compat-fields.example.test",
            vless_port=443,
            reality_sni="compat-sni.example.test",
            reality_pbk="compat-pbk",
            reality_sid="compat-sid",
            fingerprint="firefox",
            flow="xtls-rprx-vision",
            inbound_id=7,
            transport_profiles_json=json.dumps(
                [
                    {
                        "name": "legacy_reality_fallback",
                        "enabled": True,
                        "kind": "reality",
                        "inbound_id": 17,
                        "host": "catalog-legacy.example.test",
                        "port": 8443,
                        "tls_server_name": "catalog-sni.example.test",
                        "reality_public_key": "catalog-pbk",
                        "reality_short_id": "catalog-sid",
                    }
                ]
            ),
        )

        link = self.api._generate_vless_link(
            user_uuid="11111111-1111-1111-1111-111111111111",
            node=node,
            name="Legacy",
        )

        parsed = urlparse(link)
        params = parse_qs(parsed.query)
        self.assertEqual(parsed.hostname, "catalog-legacy.example.test")
        self.assertEqual(parsed.port, 8443)
        self.assertEqual(params["sni"][0], "catalog-sni.example.test")
        self.assertEqual(params["pbk"][0], "catalog-pbk")
        self.assertEqual(params["sid"][0], "catalog-sid")

    def test_singbox_multi_node_config_can_emit_grpc_transport(self) -> None:
        node = SimpleNamespace(
            code="pl",
            name="Poland",
            host="compat-fields.example.test",
            vless_port=443,
            reality_sni="compat-sni.example.test",
            reality_pbk="compat-pbk",
            reality_sid="compat-sid",
            fingerprint="firefox",
            flow="xtls-rprx-vision",
            inbound_id=7,
            transport_profiles_json=json.dumps(
                [
                    {
                        "name": "legacy_reality_fallback",
                        "enabled": True,
                        "kind": "reality",
                        "inbound_id": 17,
                        "host": "catalog-legacy.example.test",
                        "port": 443,
                        "tls_server_name": "catalog-sni.example.test",
                        "reality_public_key": "catalog-pbk",
                        "reality_short_id": "catalog-sid",
                    },
                    {
                        "name": "grpc_443_primary",
                        "enabled": True,
                        "kind": "grpc",
                        "inbound_id": 18,
                        "host": "grpc-primary.example.test",
                        "port": 443,
                        "tls_server_name": "grpc-sni.example.test",
                        "grpc_service_name": "pokrov-grpc",
                    },
                ]
            ),
        )

        cfg = self.api._singbox_multi_node_config(
            user_uuid="11111111-1111-1111-1111-111111111111",
            nodes=[node],
            title="Portal",
            transport_profile="grpc_443_primary",
        )

        outbound = next(item for item in cfg["outbounds"] if item.get("type") == "vless")
        self.assertEqual(outbound["server"], "grpc-primary.example.test")
        self.assertEqual(outbound["server_port"], 443)
        self.assertEqual(outbound["tls"]["server_name"], "grpc-sni.example.test")
        self.assertEqual(outbound["transport"]["type"], "grpc")
        self.assertEqual(outbound["transport"]["service_name"], "pokrov-grpc")
        self.assertNotIn("reality", outbound["tls"])

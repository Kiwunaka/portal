from __future__ import annotations

import importlib
import json
import os
import sys
import unittest
from unittest.mock import patch
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

    def test_node_transport_profiles_synthesize_legacy_when_catalog_omits_it(self) -> None:
        node = SimpleNamespace(
            host="legacy.example.test",
            vless_port=443,
            reality_sni="legacy-sni.example.test",
            reality_pbk="legacy-pbk",
            reality_sid="legacy-sid",
            fingerprint="firefox",
            flow="xtls-rprx-vision",
            inbound_id=7,
            transport_profiles_json=json.dumps(
                [
                    {
                        "name": "grpc_443_primary",
                        "enabled": True,
                        "kind": "grpc",
                        "inbound_id": 18,
                        "host": "grpc-primary.example.test",
                        "port": 443,
                        "tls_server_name": "grpc-sni.example.test",
                        "grpc_service_name": "pokrov-grpc",
                    }
                ]
            ),
        )

        profiles = self.transport_catalog.node_transport_profiles(node)

        self.assertEqual(
            [profile["name"] for profile in profiles],
            ["legacy_reality_fallback", "grpc_443_primary"],
        )
        self.assertEqual(profiles[0]["inbound_id"], 7)
        self.assertEqual(profiles[0]["kind"], "reality")
        self.assertEqual(profiles[1]["grpc_service_name"], "pokrov-grpc")

    def test_node_transport_profiles_accept_xhttp_fields_and_preserve_grpc_fields(self) -> None:
        node = SimpleNamespace(
            host="legacy.example.test",
            vless_port=443,
            reality_sni="legacy-sni.example.test",
            reality_pbk="legacy-pbk",
            reality_sid="legacy-sid",
            fingerprint="firefox",
            flow="xtls-rprx-vision",
            inbound_id=7,
            transport_profiles_json=json.dumps(
                [
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
                    {
                        "name": "operator_lab",
                        "enabled": False,
                        "kind": "xhttp",
                        "inbound_id": 19,
                        "host": "lab-front.example.test",
                        "port": 443,
                        "tls_server_name": "lab-sni.example.test",
                        "xhttp_path": "/lab-front",
                    },
                ]
            ),
        )

        profiles = self.transport_catalog.node_transport_profiles(node)
        by_name = {profile["name"]: profile for profile in profiles}

        self.assertEqual(
            [profile["name"] for profile in profiles],
            ["legacy_reality_fallback", "grpc_443_primary", "operator_lab"],
        )
        self.assertEqual(by_name["grpc_443_primary"]["kind"], "grpc")
        self.assertEqual(by_name["grpc_443_primary"]["grpc_service_name"], "pokrov-grpc")
        self.assertNotIn("xhttp_path", by_name["grpc_443_primary"])
        self.assertEqual(by_name["operator_lab"]["kind"], "xhttp")
        self.assertEqual(by_name["operator_lab"]["xhttp_path"], "/lab-front")
        self.assertNotIn("grpc_service_name", by_name["operator_lab"])

    def test_node_transport_profiles_normalize_delivery_endpoints(self) -> None:
        node = SimpleNamespace(
            host="primary.example.test",
            vless_port=443,
            reality_sni="sni.example.test",
            reality_pbk="pbk",
            reality_sid="sid",
            fingerprint="firefox",
            flow="xtls-rprx-vision",
            inbound_id=7,
            transport_profiles_json=json.dumps(
                [
                    {
                        "name": "legacy_reality_fallback",
                        "enabled": True,
                        "kind": "reality",
                        "inbound_id": 7,
                        "delivery_endpoints": [
                            {"id": "de1", "host": "DE-ONE.EXAMPLE.TEST.", "label": "  Германия   1  "},
                            {"id": "de2", "host": "de-two.example.test", "label": "Германия 2"},
                            {"id": "duplicate", "host": "de-two.example.test", "label": "Duplicate"},
                            {"id": "duplicate-label", "host": "de-three.example.test", "label": "германия 2"},
                            {"id": "missing-label", "host": "de-four.example.test", "label": ""},
                            {"id": "bad", "host": "https://bad.example.test", "label": "Bad"},
                        ],
                    }
                ]
            ),
        )

        profile = self.transport_catalog.node_transport_profiles(node)[0]

        self.assertEqual(
            profile["delivery_endpoints"],
            [
                {"id": "de1", "host": "de-one.example.test", "label": "Германия 1"},
                {"id": "de2", "host": "de-two.example.test", "label": "Германия 2"},
            ],
        )

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

    def test_explicit_disabled_legacy_profile_is_not_synthesized_as_enabled(self) -> None:
        node = SimpleNamespace(
            host="legacy.example.test", vless_port=443, reality_sni="sni",
            reality_pbk="pbk", reality_sid="sid", fingerprint="firefox",
            flow="xtls-rprx-vision", inbound_id=7,
            transport_profiles_json=json.dumps([{"name": "legacy_reality_fallback", "enabled": False}]),
        )

        profile = self.transport_catalog.transport_profile_by_name(
            node, "legacy_reality_fallback", include_disabled=False
        )

        self.assertFalse(profile["enabled"])
        self.assertTrue(
            self.transport_catalog.has_explicit_transport_profile(node, "legacy_reality_fallback")
        )

    def test_explicit_disabled_grpc_profile_is_not_synthesized_as_enabled(self) -> None:
        node = SimpleNamespace(
            host="grpc.example.test", vless_port=443, reality_sni="sni",
            reality_pbk="pbk", reality_sid="sid", fingerprint="firefox",
            flow="xtls-rprx-vision", inbound_id=7,
            transport_profiles_json=json.dumps([{"name": "grpc_443_primary", "enabled": False}]),
        )

        profile = self.transport_catalog.transport_profile_by_name(
            node, "grpc_443_primary", include_disabled=False
        )

        self.assertFalse(profile["enabled"])
        self.assertTrue(
            self.transport_catalog.has_explicit_transport_profile(node, "grpc_443_primary")
        )

        with patch.object(self.api, "_filter_nodes_for_transport_profile", return_value=[node]):
            effective = self.api._effective_transport_nodes(
                nodes=[node],
                transport_profile="grpc_443_primary",
                rollout_config={},
            )
        self.assertEqual(effective, [])

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

    def test_subscription_renderers_expand_one_node_into_two_delivery_endpoints(self) -> None:
        node = SimpleNamespace(
            code="de",
            name="Germany",
            host="de-one.example.test",
            vless_port=443,
            reality_sni="sni.example.test",
            reality_pbk="pbk",
            reality_sid="sid",
            fingerprint="firefox",
            flow="xtls-rprx-vision",
            inbound_id=7,
            transport_profiles_json=json.dumps(
                [
                    {
                        "name": "legacy_reality_fallback",
                        "enabled": True,
                        "kind": "reality",
                        "inbound_id": 7,
                        "host": "de-one.example.test",
                        "port": 443,
                        "tls_server_name": "sni.example.test",
                        "reality_public_key": "pbk",
                        "reality_short_id": "sid",
                        "delivery_endpoints": [
                            {"id": "de1", "host": "de-one.example.test", "label": "🇩🇪 Германия 1"},
                            {"id": "de2", "host": "de-two.example.test", "label": "🇩🇪 Германия 2"},
                        ],
                    }
                ]
            ),
        )

        cfg = self.api._singbox_multi_node_config(
            user_uuid="11111111-1111-1111-1111-111111111111",
            nodes=[node],
            title="Portal",
            transport_profile="legacy_reality_fallback",
        )
        outbounds = {item["tag"]: item for item in cfg["outbounds"]}

        self.assertEqual(outbounds["🇩🇪 Германия 1"]["server"], "de-one.example.test")
        self.assertEqual(outbounds["🇩🇪 Германия 2"]["server"], "de-two.example.test")
        self.assertEqual(
            outbounds["🇩🇪 Германия"]["outbounds"],
            ["🇩🇪 Германия 1", "🇩🇪 Германия 2"],
        )
        self.assertEqual(outbounds["🌍 Страны"]["outbounds"], ["🇩🇪 Германия"])

        clash = self.api._clash_subscription_config(
            user_uuid="11111111-1111-1111-1111-111111111111",
            nodes=[node],
            title="Portal",
            transport_profile="legacy_reality_fallback",
        )
        self.assertIn('name: "🇩🇪 Германия 1"', clash)
        self.assertIn('server: "de-one.example.test"', clash)
        self.assertIn('name: "🇩🇪 Германия 2"', clash)
        self.assertIn('server: "de-two.example.test"', clash)

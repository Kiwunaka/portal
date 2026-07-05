import os
import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse, parse_qs, unquote


def _sign_telegram_init_data(*, bot_token: str, params: dict) -> str:
    """
    Create a valid initData string according to Telegram WebApp rules.
    """
    import hashlib
    import hmac
    from urllib.parse import urlencode

    # Telegram expects hash over sorted key=value lines (excluding hash)
    items = sorted((k, v) for k, v in params.items())
    data_check_string = "\n".join([f"{k}={v}" for k, v in items])
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    check_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    params2 = dict(params)
    params2["hash"] = check_hash
    return urlencode(params2)


class PortalApiTests(unittest.TestCase):
    def setUp(self) -> None:
        # Match how scripts/services import portal_bot (flat module imports).
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        # Avoid writing a real portal.db during import.
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"

    def test_verify_telegram_data(self) -> None:
        # Import after env set.
        import importlib

        api = importlib.import_module("api")
        importlib.reload(api)

        init_data = _sign_telegram_init_data(
            bot_token=os.environ["BOT_TOKEN"],
            params={
                "auth_date": str(int(time.time())),
                "query_id": "AAEAAAE",
                "user": '{"id":12345,"first_name":"Test","username":"t"}',
            },
        )
        user = api._verify_telegram_data(init_data)
        self.assertIsNotNone(user)
        self.assertEqual(user["id"], 12345)

    def test_verify_telegram_data_uses_runtime_bot_token_when_settings_were_cached(self) -> None:
        import importlib

        config = importlib.import_module("config")
        stale_token = "stale_bot_token_456"
        original_token = os.environ["BOT_TOKEN"]
        try:
            os.environ["BOT_TOKEN"] = stale_token
            importlib.reload(config)

            os.environ["BOT_TOKEN"] = original_token
            api = importlib.import_module("api")
            importlib.reload(api)

            init_data = _sign_telegram_init_data(
                bot_token=original_token,
                params={
                    "auth_date": str(int(time.time())),
                    "query_id": "AAEAAAE",
                    "user": '{"id":54321,"first_name":"Test","username":"runtime"}',
                },
            )
            user = api._verify_telegram_data(init_data)
            self.assertIsNotNone(user)
            self.assertEqual(user["id"], 54321)
        finally:
            os.environ["BOT_TOKEN"] = original_token
            importlib.reload(config)

    def test_verify_telegram_data_rejects_expired_auth_date(self) -> None:
        import importlib

        api = importlib.import_module("api")
        importlib.reload(api)

        init_data = _sign_telegram_init_data(
            bot_token=os.environ["BOT_TOKEN"],
            params={
                "auth_date": "1700000000",
                "query_id": "AAEAAAE",
                "user": '{"id":12345,"first_name":"Test","username":"expired"}',
            },
        )
        self.assertIsNone(api._verify_telegram_data(init_data))

    def test_generate_vless_link_contains_reality_params(self) -> None:
        import importlib

        api = importlib.import_module("api")
        importlib.reload(api)

        node = SimpleNamespace(
            host="example.test",
            vless_port=443,
            reality_pbk="PBK123",
            fingerprint="firefox",
            reality_sni="www.cloudflare.com",
            reality_sid="abcdef01",
            flow="xtls-rprx-vision",
        )
        link = api._generate_vless_link(user_uuid="11111111-1111-1111-1111-111111111111", node=node, name="рџ‡єрџ‡ё РЎРЁРђ")
        u = urlparse(link)
        self.assertEqual(u.scheme, "vless")
        qs = parse_qs(u.query)
        self.assertEqual(qs["security"][0], "reality")
        self.assertEqual(qs["pbk"][0], "PBK123")
        self.assertEqual(qs["fp"][0], "firefox")
        self.assertEqual(qs["sni"][0], "www.cloudflare.com")
        self.assertEqual(qs["sid"][0], "abcdef01")
        self.assertEqual(qs["flow"][0], "xtls-rprx-vision")
        self.assertEqual(unquote(u.fragment), "рџ‡єрџ‡ё РЎРЁРђ")

    def test_singbox_config_has_selector(self) -> None:
        import importlib

        api = importlib.import_module("api")
        importlib.reload(api)

        nodes = [
            SimpleNamespace(code="pl", host="pl.test", vless_port=443, reality_sni="sni", reality_pbk="pbk", reality_sid="sid", fingerprint="firefox", flow="xtls-rprx-vision"),
            SimpleNamespace(code="it", host="it.test", vless_port=443, reality_sni="sni", reality_pbk="pbk", reality_sid="sid", fingerprint="firefox", flow="xtls-rprx-vision"),
            SimpleNamespace(code="us", host="us.test", vless_port=443, reality_sni="sni", reality_pbk="pbk", reality_sid="sid", fingerprint="firefox", flow="xtls-rprx-vision"),
        ]
        cfg = api._singbox_multi_node_config(user_uuid="11111111-1111-1111-1111-111111111111", nodes=nodes, title="Portal")
        vless_outbounds = [o for o in cfg["outbounds"] if o.get("type") == "vless"]
        self.assertEqual(len(vless_outbounds), 3)
        selector = next(o for o in cfg["outbounds"] if o.get("type") == "selector")
        self.assertIn(selector["default"], selector["outbounds"])
        self.assertEqual(len(selector["outbounds"]), 3)
        self.assertEqual(set(selector["outbounds"]), {o.get("tag") for o in vless_outbounds})
        self.assertEqual(selector["default"], vless_outbounds[0].get("tag"))
        self.assertTrue(any(r.get("tag") == "geoip-ru" for r in cfg["route"]["rule_set"]))
        rules = cfg["route"]["rules"]
        self.assertTrue(any(r.get("rule_set") == ["geoip-ru"] and r.get("outbound") == "direct" for r in rules))
        self.assertTrue(any(r.get("protocol") == "bittorrent" and r.get("outbound") == "direct" for r in rules))
        steam_rule = next(r for r in rules if r.get("domain_suffix") and "steampowered.com" in r.get("domain_suffix"))
        self.assertIn("s.team", steam_rule["domain_suffix"])
        self.assertIn("steam.tv", steam_rule["domain_suffix"])
        self.assertIn("steam-api.com", steam_rule["domain_suffix"])
        self.assertIn("steamdeck.com", steam_rule["domain_suffix"])
        self.assertIn("valvesoftware.com", steam_rule["domain_suffix"])
        self.assertIn("steampipe.akamaized.net", steam_rule["domain_suffix"])
        self.assertIn("steamstore-a.akamaihd.net", steam_rule["domain_suffix"])
        self.assertTrue(
            any(
                r.get("process_name") == ["steam.exe", "steamservice.exe", "steamwebhelper.exe", "steam", "steamservice", "steamwebhelper"]
                and r.get("outbound") == "direct"
                for r in rules
            )
        )
        self.assertFalse(any(r.get("domain_suffix") and "youtube.com" in r.get("domain_suffix") and r.get("outbound") == "direct" for r in rules))

    def test_singbox_bridge_outbound_is_hidden_from_hiddify_lists(self) -> None:
        import importlib

        api = importlib.import_module("api")
        importlib.reload(api)

        nodes = [
            SimpleNamespace(code="pl", host="pl.test", vless_port=443, reality_sni="sni", reality_pbk="pbk", reality_sid="sid", fingerprint="firefox", flow="xtls-rprx-vision"),
            SimpleNamespace(code="us", host="us.test", vless_port=443, reality_sni="sni", reality_pbk="pbk", reality_sid="sid", fingerprint="firefox", flow="xtls-rprx-vision"),
        ]
        rollout_config = api.normalized_network_rollout_config(
            {
                "ru_bridge_relay": {
                    "enabled": True,
                    "reality_public_key": "bridge-pbk",
                    "reality_short_id": "bridge-sid",
                    "excluded_node_codes": ["us"],
                }
            }
        )

        cfg = api._singbox_multi_node_config(
            user_uuid="11111111-1111-1111-1111-111111111111",
            nodes=nodes,
            title="Portal",
            rollout_config=rollout_config,
        )
        outbounds = {o.get("tag"): o for o in cfg["outbounds"]}
        selector = next(o for o in cfg["outbounds"] if o.get("type") == "selector")
        bridge_tag = api.RU_BRIDGE_OUTBOUND_TAG

        self.assertIn(bridge_tag, outbounds)
        self.assertNotIn("POKROV мост", outbounds)
        self.assertIn(api.HIDDIFY_HIDDEN_TAG_SUFFIX, bridge_tag)
        self.assertNotIn(bridge_tag, selector["outbounds"])
        self.assertNotIn("🇵🇱 Польша", selector["outbounds"])
        self.assertIn("🇵🇱 Польша · Белые списки", selector["outbounds"])
        self.assertIn("🇺🇸 США", selector["outbounds"])
        self.assertEqual(
            1,
            sum(1 for outbound in cfg["outbounds"] if outbound.get("type") == "vless" and outbound.get("detour") == bridge_tag),
        )

    def test_singbox_config_keeps_unique_tags_for_poland_canary_nodes(self) -> None:
        import importlib

        api = importlib.import_module("api")
        importlib.reload(api)

        nodes = [
            SimpleNamespace(
                code="pl",
                name="Poland",
                host="pl.test",
                vless_port=443,
                reality_sni="www.play.pl",
                reality_pbk="pbk",
                reality_sid="sid",
                fingerprint="firefox",
                flow="xtls-rprx-vision",
            ),
            SimpleNamespace(
                code="pl_canary",
                name="Poland Canary",
                host="pl-canary.test",
                vless_port=443,
                reality_sni="www.play.pl",
                reality_pbk="pbk",
                reality_sid="sid",
                fingerprint="firefox",
                flow="xtls-rprx-vision",
            ),
        ]

        cfg = api._singbox_multi_node_config(
            user_uuid="11111111-1111-1111-1111-111111111111",
            nodes=nodes,
            title="Portal",
        )
        vless_outbounds = [o for o in cfg["outbounds"] if o.get("type") == "vless"]
        tags = [o.get("tag") for o in vless_outbounds]
        selector = next(o for o in cfg["outbounds"] if o.get("type") == "selector")

        self.assertEqual(len(tags), 2)
        self.assertEqual(len(set(tags)), 2)
        self.assertEqual(len(set(selector["outbounds"])), 2)
        self.assertIn("Польша", tags[0])
        self.assertIn("Canary", tags[1])

    def test_free_config_split_routing_and_youtube_direct(self) -> None:
        import importlib

        api = importlib.import_module("api")
        importlib.reload(api)

        nodes = [
            SimpleNamespace(code="pl", name="Poland", host="pl.test", vless_port=443, reality_sni="sni", reality_pbk="pbk", reality_sid="sid", fingerprint="firefox", flow="xtls-rprx-vision"),
        ]
        cfg = api._singbox_free_allowlist_config(user_uuid="11111111-1111-1111-1111-111111111111", nodes=nodes, title="Portal (Free)")
        selector = next(o for o in cfg["outbounds"] if o.get("type") == "selector")
        selector_tag = selector["tag"]
        self.assertEqual(cfg["route"]["final"], selector_tag)
        first_vless = next(o for o in cfg["outbounds"] if o.get("type") == "vless")
        self.assertNotIn("transport", first_vless)
        self.assertEqual(selector["default"], first_vless["tag"])

        self.assertTrue(any(r.get("tag") == "geoip-ru" for r in cfg["route"]["rule_set"]))
        rules = cfg["route"]["rules"]
        self.assertTrue(any(r.get("rule_set") == ["geoip-ru"] and r.get("outbound") == "direct" for r in rules))
        self.assertTrue(any(r.get("protocol") == "bittorrent" and r.get("outbound") == "direct" for r in rules))
        steam_rule = next(r for r in rules if r.get("domain_suffix") and "steampowered.com" in r.get("domain_suffix"))
        self.assertIn("steamcdn-a.akamaihd.net", steam_rule["domain_suffix"])
        self.assertTrue(
            any(
                r.get("process_name") == ["steam.exe", "steamservice.exe", "steamwebhelper.exe", "steam", "steamservice", "steamwebhelper"]
                and r.get("outbound") == "direct"
                for r in rules
            )
        )
        self.assertTrue(any(r.get("domain_suffix") and "youtube.com" in r.get("domain_suffix") and r.get("outbound") == "direct" for r in rules))

    def test_nodes_for_user_includes_all_non_free_nodes_for_paid_pool(self) -> None:
        import importlib

        api = importlib.import_module("api")
        importlib.reload(api)

        user = SimpleNamespace(tg_id=1001, sub_type="PAID", current_plan_code="1_month")
        nodes = [
            SimpleNamespace(code="brain"),
            SimpleNamespace(code="de"),
            SimpleNamespace(code="pl"),
            SimpleNamespace(code="it"),
            SimpleNamespace(code="nl"),
            SimpleNamespace(code="free"),
        ]
        out = api._nodes_for_user(user, nodes)
        codes = [n.code for n in out]
        self.assertIn("brain", codes)
        self.assertIn("de", codes)
        self.assertIn("pl", codes)
        self.assertIn("it", codes)
        self.assertIn("nl", codes)
        self.assertNotIn("free", codes)

    def test_nodes_for_trial_user_use_premium_pool(self) -> None:
        import importlib

        api = importlib.import_module("api")
        importlib.reload(api)

        user = SimpleNamespace(tg_id=1002, sub_type="FREE", current_plan_code="trial")
        nodes = [
            SimpleNamespace(code="free"),
            SimpleNamespace(code="nl"),
            SimpleNamespace(code="it"),
        ]
        out = api._nodes_for_user(user, nodes)
        self.assertEqual([n.code for n in out], ["nl", "it"])

    def test_nodes_for_free_user_only_use_canonical_free_node(self) -> None:
        import importlib

        api = importlib.import_module("api")
        importlib.reload(api)

        user = SimpleNamespace(tg_id=1003, sub_type="FREE", current_plan_code="free_monthly")
        nodes = [
            SimpleNamespace(code="pl_free"),
            SimpleNamespace(code="free"),
            SimpleNamespace(code="nl"),
        ]
        out = api._nodes_for_user(user, nodes)
        self.assertEqual([n.code for n in out], ["free"])

    def test_node_labels_include_nl_and_nl_free(self) -> None:
        import importlib

        api = importlib.import_module("api")
        importlib.reload(api)

        self.assertEqual(api._node_country_name("nl"), "Netherlands")
        self.assertEqual(api._node_country_name("pl_free"), "NL Free")
        self.assertIn("Нидерланды", api._node_label_ru("nl"))
        self.assertIn("NL Free", api._node_label_ru("pl_free"))


if __name__ == "__main__":
    unittest.main()

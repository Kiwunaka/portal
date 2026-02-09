import os
import sys
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
                "auth_date": "1700000000",
                "query_id": "AAEAAAE",
                "user": '{"id":12345,"first_name":"Test","username":"t"}',
            },
        )
        user = api._verify_telegram_data(init_data)
        self.assertIsNotNone(user)
        self.assertEqual(user["id"], 12345)

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
        rules = cfg["route"]["rules"]
        self.assertTrue(any(r.get("geoip") == ["ru"] and r.get("outbound") == "direct" for r in rules))
        self.assertTrue(any(r.get("protocol") == "bittorrent" and r.get("outbound") == "direct" for r in rules))
        self.assertFalse(any(r.get("domain_suffix") and "youtube.com" in r.get("domain_suffix") and r.get("outbound") == "direct" for r in rules))

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

        rules = cfg["route"]["rules"]
        self.assertTrue(any(r.get("geoip") == ["ru"] and r.get("outbound") == "direct" for r in rules))
        self.assertTrue(any(r.get("protocol") == "bittorrent" and r.get("outbound") == "direct" for r in rules))
        self.assertTrue(any(r.get("domain") == ["steamcdn-a.akamaihd.net"] and r.get("outbound") == "direct" for r in rules))
        self.assertTrue(any(r.get("domain_suffix") and "youtube.com" in r.get("domain_suffix") and r.get("outbound") == "direct" for r in rules))


if __name__ == "__main__":
    unittest.main()

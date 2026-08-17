import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "verify_brain_ready.py"
    spec = importlib.util.spec_from_file_location("verify_brain_ready", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class VerifyBrainReadyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_subscription_check_script_includes_connect_probe(self) -> None:
        script = self.module._build_subscription_check_script(
            api_domain="api.pokrov.space",
            connect_domain="connect.pokrov.space",
            repeat=3,
        )

        self.assertIn("https://connect.pokrov.space/s8Kx2mP7qR4wT/$SEL_TOK", script)
        self.assertIn('print(f"connect_json=1 outbounds={len(payload.get(\'outbounds\') or [])}")', script)
        self.assertIn('RAW_PAYLOAD="$RAW" python3 - <<\'PY\'', script)
        self.assertIn('RAW_CONNECT_PAYLOAD="$RAW_CONNECT" python3 - <<\'PY\'', script)
        self.assertIn("for i in $(seq 1 3); do", script)
        self.assertIn("sub_fetch_$i user=selected", script)
        self.assertNotIn("sub_fetch_$i tg_id=", script)

    def test_required_units_include_feedbackbot(self) -> None:
        self.assertIn("portal-feedbackbot", self.module.DEFAULT_REQUIRED_UNITS)

    def test_required_units_include_worker(self) -> None:
        self.assertIn("portal-worker", self.module.DEFAULT_REQUIRED_UNITS)

    def test_listener_probe_uses_ere_compatible_grouping(self) -> None:
        cmd = self.module._listener_probe_cmd((443, 8444))
        self.assertIn("python3 -", cmd)
        self.assertIn("ports = [443, 8444]", cmd)
        self.assertNotIn("?:", cmd)

    def test_required_secret_probe_never_prints_secret_value(self) -> None:
        cmd = self.module._required_secret_presence_cmd()

        self.assertIn("DEVICE_PAIRING_HMAC_SECRET", cmd)
        self.assertIn("present length_ok=1", cmd)
        self.assertNotIn("print(values", cmd)
        self.assertNotIn("print(value", cmd)

    def test_curl_retry_accepts_any_current_marker(self) -> None:
        cmd = self.module._curl_retry(
            "pay.pokrov.space/checkout/",
            host="pay.pokrov.space",
            contains_any=("checkout-shell", "ключ доступа"),
        )

        self.assertIn("checkout-shell", cmd)
        self.assertIn("ключ доступа", cmd)
        self.assertIn("||", cmd)
        self.assertIn("head -c 200", cmd)

    def test_cache_header_probe_requires_no_cache_html_policy(self) -> None:
        cmd = self.module._cache_header_retry("app.pokrov.space/dashboard", host="app.pokrov.space")

        self.assertIn("curl -fsSI", cmd)
        self.assertIn("--resolve", cmd)
        self.assertIn("cache-control", cmd.lower())
        self.assertIn("no-cache", cmd)
        self.assertIn("must-revalidate", cmd)

    def test_binary_rule_set_probe_requires_octet_stream_and_srs_magic(self) -> None:
        cmd = self.module._binary_rule_set_retry(
            "connect.pokrov.space/rules/geoip-ru.srs",
            host="connect.pokrov.space",
        )

        self.assertIn("application/octet-stream", cmd)
        self.assertIn("535253", cmd)
        self.assertIn("size", cmd)
        self.assertIn("curl -fsS", cmd)
        self.assertIn("--resolve", cmd)

    def test_caddy_serves_only_owned_singbox_rule_set_paths_before_redirect(self) -> None:
        caddyfile = (Path(__file__).resolve().parents[1] / "infra" / "Caddyfile.internal").read_text(encoding="utf-8")

        connect_block = caddyfile[caddyfile.index("@connect_host host connect.pokrov.space") :]
        self.assertIn("@singbox_rules path /rules/geoip-ru.srs /rules/adblock.srs", connect_block)
        self.assertIn('header Content-Type "application/octet-stream"', connect_block)
        self.assertIn("root * /var/www/portal", connect_block)
        self.assertLess(connect_block.index("handle @singbox_rules"), connect_block.index("redir https://app.pokrov.space{uri} 308"))

    def test_caddy_allows_only_telegram_to_embed_the_user_cabinet(self) -> None:
        caddyfile = (Path(__file__).resolve().parents[1] / "infra" / "Caddyfile.internal").read_text(encoding="utf-8")

        webapp_block = caddyfile[
            caddyfile.index("@webapp_host host app.pokrov.space") : caddyfile.index("@adminapp_host host")
        ]
        frame_deny_block = caddyfile[
            caddyfile.index("@frame_deny not host app.pokrov.space") : caddyfile.index("@www_marketing host")
        ]
        self.assertIn('Content-Security-Policy "frame-ancestors \'none\'', frame_deny_block)
        self.assertIn('X-Frame-Options "DENY"', frame_deny_block)
        self.assertNotIn('X-Frame-Options "DENY"', webapp_block)
        self.assertIn("frame-ancestors https://web.telegram.org https://*.telegram.org", webapp_block)
        self.assertNotIn("frame-ancestors *", webapp_block)

    def test_main_returns_failure_when_required_service_is_inactive(self) -> None:
        ssh = MagicMock()
        sftp = MagicMock()
        remote_file = MagicMock()
        remote_file.write = MagicMock()
        remote_file.__enter__.return_value = remote_file
        remote_file.__exit__.return_value = None
        sftp.file.return_value = remote_file
        ssh.open_sftp.return_value = sftp

        run_results = [
            (0, "active\n", ""),
            (0, "active\n", ""),
            (0, "active\n", ""),
            (0, "active\n", ""),
            (0, "active\n", ""),
            (3, "inactive\n", ""),
            (0, "DEVICE_PAIRING_HMAC_SECRET=present length_ok=1\n", ""),
            (0, "LISTEN 0 4096 0.0.0.0:443\nLISTEN 0 4096 0.0.0.0:8444\n", ""),
            (0, "ok", ""),
            (0, "ok", ""),
            (0, "ok", ""),
            (0, "ok", ""),
            (0, "Ускорить интернет сейчас", ""),
            (0, "Открыть кабинет", ""),
            (0, "Публичная оферта | POKROV", ""),
            (0, "Ваш путь к быстрой сети | POKROV", ""),
            (0, "ok", ""),
            (0, "sub_fetch_1 user=selected mode=token fmt=plain lines=1 hosts=1 connect_json=1 outbounds=1", ""),
            (0, "", ""),
            (0, "ok", ""),
            (0, "ok", ""),
            (0, "ok", ""),
            (0, "sub_fetch_1 user=selected mode=token fmt=plain lines=1 hosts=1 connect_json=1 outbounds=1", ""),
            (0, "", ""),
        ]

        with patch.object(self.module.argparse.ArgumentParser, "parse_args") as parse_args:
            parse_args.return_value = self.module.argparse.Namespace(
                web_domain="pokrov.space",
                api_domain="api.pokrov.space",
                connect_domain="connect.pokrov.space",
                domain="",
                brain_ip="82.21.114.104",
                ssh_user="root",
                ssh_port=29374,
                passwords="C:/tmp/PASSWORDS.txt",
                repeat=1,
                check_legacy_2096=False,
            )
            with patch.object(self.module, "_parse_passwords", return_value={"brain": "secret"}):
                with patch.object(self.module, "_ssh_connect", return_value=ssh):
                    with patch.object(self.module, "_run", side_effect=run_results):
                        exit_code = self.module.main()

        self.assertEqual(exit_code, 2)
        ssh.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()

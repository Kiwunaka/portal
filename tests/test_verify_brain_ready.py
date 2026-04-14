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

    def test_required_units_include_feedbackbot(self) -> None:
        self.assertIn("portal-feedbackbot", self.module.DEFAULT_REQUIRED_UNITS)

    def test_listener_probe_uses_ere_compatible_grouping(self) -> None:
        cmd = self.module._listener_probe_cmd((443, 8444))
        self.assertIn("python3 -", cmd)
        self.assertIn("ports = [443, 8444]", cmd)
        self.assertNotIn("?:", cmd)

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
            (3, "inactive\n", ""),
            (0, "LISTEN 0 4096 0.0.0.0:443\nLISTEN 0 4096 0.0.0.0:8444\n", ""),
            (0, "ok", ""),
            (0, "ok", ""),
            (0, "Ускорить интернет сейчас", ""),
            (0, "Открыть кабинет", ""),
            (0, "Публичная оферта | POKROV", ""),
            (0, "Ваш путь к быстрой сети | POKROV", ""),
            (0, "ok", ""),
            (0, "sub_fetch_1 tg_id=1 mode=token fmt=plain lines=1 hosts=1 connect_json=1 outbounds=1", ""),
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

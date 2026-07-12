import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "release_gate_check.py"
    spec = importlib.util.spec_from_file_location("release_gate_check", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReleaseGateCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_client_security_smoke_gate_is_included_in_default_gate_set(self) -> None:
        gates = self.module._default_gates()

        names = [name for name, _cmd, _cwd in gates]

        self.assertIn("Client security smoke", names)
        self.assertIn("Client Flutter tests", names)

    def test_account_foundation_is_in_release_pytest_matrix(self) -> None:
        self.assertIn("tests/test_account_foundation.py", self.module.RELEASE_PYTEST_ARGS)

    def test_account_foundation_compatibility_suites_are_in_release_pytest_matrix(self) -> None:
        for suite in (
            "tests/test_account_recovery.py",
            "tests/test_auth_sessions.py",
            "portal_bot/tests/test_app_first_service.py",
            "portal_bot/tests/test_email_auth.py",
            "tests/test_bot_paywall.py",
        ):
            with self.subTest(suite=suite):
                self.assertIn(suite, self.module.RELEASE_PYTEST_ARGS)

    def test_client_security_smoke_gate_is_included_in_quick_gate_set(self) -> None:
        gates = self.module._quick_gates()

        names = [name for name, _cmd, _cwd in gates]

        self.assertIn("Client security smoke", names)
        self.assertIn("Client portal Flutter tests", names)

    def test_requested_client_platform_gates_are_appended(self) -> None:
        gates = self.module._default_gates(
            client_platform_gates=["windows", "android-apk"],
        )

        names = [name for name, _cmd, _cwd in gates]

        self.assertIn("Client Windows release build", names)
        self.assertIn("Client Android APK build", names)

    def test_android_localhost_audit_gate_is_opt_in(self) -> None:
        with patch.dict(self.module.os.environ, {}, clear=True):
            gate = self.module._optional_android_localhost_audit_gate()

        self.assertIsNone(gate)

    def test_android_localhost_audit_gate_uses_configured_serial(self) -> None:
        env = {
            "ANDROID_AUDIT_SERIAL": "emulator-5554",
            "ANDROID_AUDIT_RELEASE_EVIDENCE": "apk sha256 abc123",
        }
        with patch.dict(self.module.os.environ, env, clear=True):
            name, cmd, cwd = self.module._optional_android_localhost_audit_gate()

        self.assertEqual(name, "Android localhost audit")
        self.assertEqual(cmd[:3], [sys.executable, "scripts/android_localhost_audit.py", "--serial"])
        self.assertIn("emulator-5554", cmd)
        self.assertIn("--package", cmd)
        self.assertIn("space.pokrov.pokrov_android_shell", cmd)
        self.assertIn("--release-evidence", cmd)
        self.assertIn("apk sha256 abc123", cmd)
        self.assertIn("--require-release-build", cmd)
        self.assertEqual(cwd, self.module.REPO_ROOT)

    def test_android_localhost_audit_gate_uses_configured_package(self) -> None:
        env = {
            "ANDROID_AUDIT_SERIAL": "R58N12345AB",
            "ANDROID_AUDIT_PACKAGE": "space.pokrov.custom",
            "ANDROID_AUDIT_RELEASE_EVIDENCE": "apk sha256 abc123",
        }
        with patch.dict(self.module.os.environ, env, clear=True):
            _name, cmd, _cwd = self.module._optional_android_localhost_audit_gate()

        package_index = cmd.index("--package") + 1
        self.assertEqual(cmd[package_index], "space.pokrov.custom")

    def test_required_android_localhost_audit_gate_requires_serial(self) -> None:
        with patch.dict(self.module.os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "ANDROID_AUDIT_SERIAL"):
                self.module._required_android_localhost_audit_gate()

    def test_required_android_localhost_audit_gate_rejects_emulator_serial(self) -> None:
        with patch.dict(self.module.os.environ, {"ANDROID_AUDIT_SERIAL": "emulator-5554"}, clear=True):
            with self.assertRaisesRegex(ValueError, "physical hardware"):
                self.module._required_android_localhost_audit_gate()

    def test_required_android_localhost_audit_gate_requires_release_evidence(self) -> None:
        with patch.dict(self.module.os.environ, {"ANDROID_AUDIT_SERIAL": "R58N12345AB"}, clear=True):
            with self.assertRaisesRegex(ValueError, "ANDROID_AUDIT_RELEASE_EVIDENCE"):
                self.module._required_android_localhost_audit_gate()

    def test_required_android_localhost_audit_gate_accepts_physical_serial(self) -> None:
        env = {
            "ANDROID_AUDIT_SERIAL": "R58N12345AB",
            "ANDROID_AUDIT_RELEASE_EVIDENCE": "apk sha256 abc123",
        }
        with patch.dict(self.module.os.environ, env, clear=True):
            name, cmd, cwd = self.module._required_android_localhost_audit_gate()

        self.assertEqual(name, "Android localhost audit")
        self.assertIn("R58N12345AB", cmd)
        self.assertIn("--require-release-build", cmd)
        self.assertEqual(cwd, self.module.REPO_ROOT)

    def test_select_android_localhost_audit_gate_is_optional_without_android_builds(self) -> None:
        with patch.dict(self.module.os.environ, {}, clear=True):
            gate = self.module._select_android_localhost_audit_gate(
                client_platform_gates=["windows"],
            )

        self.assertIsNone(gate)

    def test_parse_client_platform_gates_uses_cli_or_env(self) -> None:
        with patch.dict(self.module.os.environ, {"CLIENT_PLATFORM_GATES": "windows,android-aab"}, clear=True):
            self.assertEqual(
                self.module._parse_client_platform_gates(""),
                ["windows", "android-aab"],
            )

        self.assertEqual(
            self.module._parse_client_platform_gates("android-apk"),
            ["android-apk"],
        )

    def test_runtime_smoke_gate_uses_redacting_wrapper(self) -> None:
        with patch.dict(self.module.os.environ, {"TELEGRAM_INIT_DATA": "query_id=AAA&hash=secret"}, clear=True):
            name, cmd, cwd = self.module._optional_runtime_smoke_gate()

        self.assertEqual(name, "Client apps runtime smoke")
        self.assertIn("scripts/runtime_app_download_smoke.py", cmd)
        self.assertIn("--redact", cmd)
        self.assertNotIn("scripts/smoke_client_apps.py", cmd)
        self.assertEqual(cwd, self.module.REPO_ROOT)

    def test_missing_client_root_can_be_skipped_for_ci_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "POKROV-app" / "config" / "product-contract.seed.json"
            with patch.object(self.module, "CLIENT_ROOT_REQUIRED_PATHS", (missing,)):
                gates = [
                    self.module._client_security_smoke_gate(),
                    self.module._client_flutter_test_gate(suite="portal"),
                    ("Public link checks", [sys.executable, "scripts/check-links.py"], self.module.REPO_ROOT),
                ]

                filtered = self.module._filter_client_gates_when_missing(
                    gates,
                    allow_missing_client_root=True,
                    client_platform_gates=[],
                )

        names = [name for name, _cmd, _cwd in filtered]
        self.assertNotIn("Client security smoke", names)
        self.assertNotIn("Client portal Flutter tests", names)
        self.assertIn("Public link checks", names)
        self.assertIn("Client workspace preflight (skipped)", names)

    def test_missing_client_root_stays_strict_for_platform_builds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "POKROV-app" / "config" / "product-contract.seed.json"
            with patch.object(self.module, "CLIENT_ROOT_REQUIRED_PATHS", (missing,)):
                gates = [self.module._client_security_smoke_gate()]

                filtered = self.module._filter_client_gates_when_missing(
                    gates,
                    allow_missing_client_root=True,
                    client_platform_gates=["windows"],
                )

        names = [name for name, _cmd, _cwd in filtered]
        self.assertEqual(names, ["Client security smoke"])

    def test_redact_text_covers_telegram_init_data_and_query_fields(self) -> None:
        raw = (
            "python scripts/smoke_client_apps.py --init-data query_id=AAH&user=%7B%22id%22%3A1%7D"
            "&auth_date=1710000000&hash=supersecret "
            "--init-data=query_id=DDD&signature=sig&chat_instance=chat&hash=equalform "
            "TELEGRAM_INIT_DATA=query_id=BBB&hash=hidden "
            "X-Telegram-Init-Data: query_id=CCC&user={id:2}&signature=abc&chat_instance=123&hash=def"
        )

        redacted = self.module._redact_text(raw)

        self.assertNotIn("supersecret", redacted)
        self.assertNotIn("hidden", redacted)
        self.assertNotIn("equalform", redacted)
        self.assertNotIn("signature=sig", redacted)
        self.assertNotIn("chat_instance=chat", redacted)
        self.assertNotIn("query_id=AAH", redacted)
        self.assertNotIn("query_id=BBB", redacted)
        self.assertNotIn("query_id=CCC", redacted)
        self.assertNotIn("query_id=DDD", redacted)
        self.assertIn("--init-data <redacted>", redacted)
        self.assertIn("TELEGRAM_INIT_DATA=<redacted>", redacted)
        self.assertIn("X-Telegram-Init-Data: <redacted>", redacted)


if __name__ == "__main__":
    unittest.main()

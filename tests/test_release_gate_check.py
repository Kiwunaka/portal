import importlib.util
import sys
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
        with patch.dict(self.module.os.environ, {"ANDROID_AUDIT_SERIAL": "emulator-5554"}, clear=True):
            name, cmd, cwd = self.module._optional_android_localhost_audit_gate()

        self.assertEqual(name, "Android localhost audit")
        self.assertEqual(cmd[:3], [sys.executable, "scripts/android_localhost_audit.py", "--serial"])
        self.assertIn("emulator-5554", cmd)
        self.assertEqual(cwd, self.module.REPO_ROOT)

    def test_required_android_localhost_audit_gate_requires_serial(self) -> None:
        with patch.dict(self.module.os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "ANDROID_AUDIT_SERIAL"):
                self.module._required_android_localhost_audit_gate()

    def test_required_android_localhost_audit_gate_rejects_emulator_serial(self) -> None:
        with patch.dict(self.module.os.environ, {"ANDROID_AUDIT_SERIAL": "emulator-5554"}, clear=True):
            with self.assertRaisesRegex(ValueError, "physical hardware"):
                self.module._required_android_localhost_audit_gate()

    def test_required_android_localhost_audit_gate_accepts_physical_serial(self) -> None:
        with patch.dict(self.module.os.environ, {"ANDROID_AUDIT_SERIAL": "R58N12345AB"}, clear=True):
            name, cmd, cwd = self.module._required_android_localhost_audit_gate()

        self.assertEqual(name, "Android localhost audit")
        self.assertIn("R58N12345AB", cmd)
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


if __name__ == "__main__":
    unittest.main()

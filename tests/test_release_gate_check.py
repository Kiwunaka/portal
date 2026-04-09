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

    def test_client_security_smoke_gate_is_included_in_quick_gate_set(self) -> None:
        gates = self.module._quick_gates()

        names = [name for name, _cmd, _cwd in gates]

        self.assertIn("Client security smoke", names)

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


if __name__ == "__main__":
    unittest.main()

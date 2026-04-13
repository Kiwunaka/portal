import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "run_client_release_gate.py"
    spec = importlib.util.spec_from_file_location("run_client_release_gate", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RunClientReleaseGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_suite_command_uses_expected_flutter_args(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client_root = Path(tmp)

            command = self.module._suite_command(client_root, suite="portal")

        self.assertEqual(command.cwd, client_root)
        self.assertEqual(command.command, ["flutter", "test", "test/features/portal"])

    def test_windows_target_declares_expected_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client_root = Path(tmp)

            command = self.module._build_target_command(client_root, target="windows")

        self.assertEqual(command.command, ["flutter", "build", "windows", "--release"])
        self.assertTrue(str(command.expected_artifact).endswith("build\\windows\\x64\\runner\\Release\\POKROVVPN.exe"))

    def test_windows_sqlite_bootstrap_dir_prefers_runner_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client_root = Path(tmp)
            runner_dir = client_root / "build" / "windows" / "x64" / "runner" / "Release"
            runner_dir.mkdir(parents=True)
            (runner_dir / "sqlite3.dll").write_text("dll", encoding="utf-8")

            bootstrap_dir = self.module._windows_sqlite_bootstrap_dir(client_root)

        self.assertEqual(bootstrap_dir, runner_dir)


if __name__ == "__main__":
    unittest.main()

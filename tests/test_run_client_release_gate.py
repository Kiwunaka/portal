import importlib.util
import subprocess
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

    def test_libcore_preflight_requires_clean_expected_sha(self) -> None:
        client_root = Path("C:/fake/client")

        def fake_run(command, **kwargs):
            rendered = " ".join(str(part) for part in command)
            if rendered.endswith("rev-parse HEAD:libcore"):
                return subprocess.CompletedProcess(command, 0, stdout="expectedsha\n", stderr="")
            if rendered.endswith("rev-parse HEAD"):
                return subprocess.CompletedProcess(command, 0, stdout="expectedsha\n", stderr="")
            if rendered.endswith("branch --show-current"):
                return subprocess.CompletedProcess(command, 0, stdout="\n", stderr="")
            if rendered.endswith("status --porcelain"):
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
            raise AssertionError(f"unexpected command: {rendered}")

        issue = self.module._libcore_preflight_issue(client_root, runner=fake_run)

        self.assertIsNone(issue)

    def test_libcore_preflight_reports_sha_drift(self) -> None:
        client_root = Path("C:/fake/client")

        def fake_run(command, **kwargs):
            rendered = " ".join(str(part) for part in command)
            if rendered.endswith("rev-parse HEAD:libcore"):
                return subprocess.CompletedProcess(command, 0, stdout="expectedsha\n", stderr="")
            if rendered.endswith("rev-parse HEAD"):
                return subprocess.CompletedProcess(command, 0, stdout="actualsha\n", stderr="")
            if rendered.endswith("branch --show-current"):
                return subprocess.CompletedProcess(command, 0, stdout="release-branch\n", stderr="")
            if rendered.endswith("status --porcelain"):
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
            raise AssertionError(f"unexpected command: {rendered}")

        issue = self.module._libcore_preflight_issue(client_root, runner=fake_run)

        self.assertIn("expectedsha", issue or "")
        self.assertIn("actualsha", issue or "")
        self.assertIn("release-branch", issue or "")

    def test_libcore_preflight_reports_dirty_submodule(self) -> None:
        client_root = Path("C:/fake/client")

        def fake_run(command, **kwargs):
            rendered = " ".join(str(part) for part in command)
            if rendered.endswith("rev-parse HEAD:libcore"):
                return subprocess.CompletedProcess(command, 0, stdout="expectedsha\n", stderr="")
            if rendered.endswith("rev-parse HEAD"):
                return subprocess.CompletedProcess(command, 0, stdout="expectedsha\n", stderr="")
            if rendered.endswith("branch --show-current"):
                return subprocess.CompletedProcess(command, 0, stdout="\n", stderr="")
            if rendered.endswith("status --porcelain"):
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=" M libcore/file.go\n?? libcore/new_file.go\n",
                    stderr="",
                )
            raise AssertionError(f"unexpected command: {rendered}")

        issue = self.module._libcore_preflight_issue(client_root, runner=fake_run)

        self.assertIn("dirty", issue or "")
        self.assertIn("expectedsha", issue or "")
        self.assertIn("(detached HEAD)", issue or "")
        self.assertIn("M libcore/file.go", issue or "")

    def test_render_libcore_preflight_report_lists_status_context(self) -> None:
        client_root = Path("C:/fake/client")
        status = self.module.LibcorePreflightStatus(
            expected_sha="expectedsha",
            actual_sha="expectedsha",
            branch="(detached HEAD)",
            dirty_lines=("M file.go", "?? new.go"),
        )

        report = self.module._render_libcore_preflight_report(
            client_root,
            status=status,
            issue="libcore worktree is dirty",
        )

        self.assertIn("pinned SHA: expectedsha", report)
        self.assertIn("checked-out SHA: expectedsha", report)
        self.assertIn("dirty: M file.go", report)
        self.assertIn("[fail] libcore worktree is dirty", report)


if __name__ == "__main__":
    unittest.main()

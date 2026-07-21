import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "run_client_release_gate.py"
    spec = importlib.util.spec_from_file_location("run_client_release_gate", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = _load_module()


def _write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _prepare_client_root(root: Path) -> None:
    _write(root / "scripts" / "validate-seed.ps1", "Write-Host validate")
    _write(root / "scripts" / "bootstrap-workspace.ps1", "Write-Host bootstrap")
    _write(root / "scripts" / "run-tests.ps1", "Write-Host tests")
    _write(root / "scripts" / "fetch-libcore-assets.ps1", "Write-Host fetch")
    _write(root / "scripts" / "build-windows-release.ps1", "Write-Host build")
    _write(root / "config" / "product-contract.seed.json", "{}")
    _write(root / "config" / "runtime-profile.seed.json", "{}")
    _write(root / "config" / "runtime-artifacts.seed.json", "{}")
    _write(
        root / "config" / "windows-release.seed.json",
        '{"artifact_root": "artifacts/releases/pokrov-app", "zip_name_template": "pokrov-app-windows-{version}.zip", "installer_name_template": "pokrov-app-windows-{version}-setup.exe", "manifest_name_template": "pokrov-app-windows-{version}.json"}',
    )
    _write(root / "packages" / "app_shell" / "pubspec.yaml", "name: app_shell\n")
    _write(root / "apps" / "android_shell" / "pubspec.yaml", "name: android_shell\n")
    _write(root / "apps" / "windows_shell" / "pubspec.yaml", "name: windows_shell\nversion: 0.7.0+1\n")


def _command_has_suffix(command: list[str], suffix: list[str]) -> bool:
    return command[-len(suffix) :] == suffix


def test_preflight_reports_missing_seed_workspace_paths() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        client_root = Path(tmp)

        status = MODULE._preflight_status(client_root)
        issue = MODULE._preflight_issue_from_status(status)

    assert status.client_root == client_root
    assert status.validate_seed_script in status.missing_paths
    assert status.bootstrap_script in status.missing_paths
    assert issue is not None
    assert "POKROV-app gate root is incomplete" in issue


def test_client_root_resolver_selects_the_main_worktree() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        workspace_root = Path(tmp)
        platform_root = workspace_root / "VPN"
        platform_checkout = platform_root / ".worktrees" / "integration"
        client_repo = workspace_root / "POKROV-app"
        main_worktree = client_repo / ".worktrees" / "final-client-integration"
        (client_repo / ".git").mkdir(parents=True)

        git_results = (
            subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=f"{platform_root / '.git'}\n",
            ),
            subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    f"worktree {client_repo}\n"
                    "branch refs/heads/codex/client-work\n\n"
                    f"worktree {main_worktree}\n"
                    "branch refs/heads/main\n"
                ),
            ),
        )
        with patch.dict(MODULE.os.environ, {"POKROV_APP_ROOT": ""}, clear=False):
            with patch.object(MODULE.subprocess, "run", side_effect=git_results):
                resolved = MODULE._resolve_client_root(platform_checkout)

    assert resolved == main_worktree.resolve()


def test_client_root_resolver_keeps_explicit_override_authoritative() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        override = Path(tmp) / "explicit-client"
        with patch.dict(MODULE.os.environ, {"POKROV_APP_ROOT": str(override)}, clear=False):
            with patch.object(MODULE.subprocess, "run") as run:
                resolved = MODULE._resolve_client_root(Path(tmp) / "platform")

    assert resolved == override.resolve()
    run.assert_not_called()


def test_portal_suite_command_targets_pokrov_app_shells() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        client_root = Path(tmp)
        _prepare_client_root(client_root)

        command = MODULE._suite_command(client_root, suite="portal")

    assert len(command.steps) == 4
    assert str(command.steps[0].cwd) == str(client_root)
    assert "bootstrap-workspace.ps1" in " ".join(command.steps[0].command)
    assert command.steps[1].cwd == client_root / "packages" / "app_shell"
    assert _command_has_suffix(command.steps[1].command, ["test"])
    assert command.steps[2].cwd == client_root / "apps" / "android_shell"
    assert _command_has_suffix(command.steps[2].command, ["test"])
    assert command.steps[3].cwd == client_root / "apps" / "windows_shell"
    assert _command_has_suffix(command.steps[3].command, ["test"])


def test_windows_target_declares_expected_release_artifacts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        client_root = Path(tmp)
        _prepare_client_root(client_root)

        command = MODULE._build_target_command(client_root, target="windows")

    assert len(command.steps) == 1
    assert command.steps[0].cwd == client_root
    assert "build-windows-release.ps1" in " ".join(command.steps[0].command)
    assert "-SyncRuntime" in command.steps[0].command
    assert "-SkipTests" in command.steps[0].command
    assert "-SkipAnalyze" in command.steps[0].command
    assert command.expected_artifacts == (
        client_root / "artifacts" / "releases" / "pokrov-app" / "pokrov-app-windows-0.7.0+1.zip",
        client_root / "artifacts" / "releases" / "pokrov-app" / "pokrov-app-windows-0.7.0+1-setup.exe",
        client_root / "artifacts" / "releases" / "pokrov-app" / "pokrov-app-windows-0.7.0+1.json",
    )


def test_android_apk_target_declares_android_shell_artifact() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        client_root = Path(tmp)
        _prepare_client_root(client_root)

        command = MODULE._build_target_command(client_root, target="android-apk")

    assert len(command.steps) == 3
    assert "bootstrap-workspace.ps1" in " ".join(command.steps[0].command)
    assert "fetch-libcore-assets.ps1" in " ".join(command.steps[1].command)
    assert "-Platforms" in command.steps[1].command
    assert "android" in command.steps[1].command
    assert "-SyncToHosts" in command.steps[1].command
    assert command.steps[2].cwd == client_root / "apps" / "android_shell"
    assert _command_has_suffix(command.steps[2].command, ["build", "apk", "--release"])
    assert command.expected_artifacts == (
        client_root
        / "apps"
        / "android_shell"
        / "build"
        / "app"
        / "outputs"
        / "flutter-apk"
        / "app-release.apk",
    )


def test_run_requires_declared_artifacts_to_exist() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        client_root = Path(tmp)
        _prepare_client_root(client_root)
        command = MODULE._build_target_command(client_root, target="android-aab")

        original_run_step = MODULE._run_step
        try:
            MODULE._run_step = lambda step: 0
            rc = MODULE._run(command, client_root=client_root)
        finally:
            MODULE._run_step = original_run_step

    assert rc == 2


def test_run_succeeds_when_expected_artifacts_exist() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        client_root = Path(tmp)
        _prepare_client_root(client_root)
        command = MODULE._build_target_command(client_root, target="android-aab")
        artifact = command.expected_artifacts[0]
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(b"aab")

        original_run_step = MODULE._run_step
        try:
            MODULE._run_step = lambda step: 0
            rc = MODULE._run(command, client_root=client_root)
        finally:
            MODULE._run_step = original_run_step

    assert rc == 0


def test_preflight_report_lists_pokrov_app_context() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        client_root = Path(tmp)
        _prepare_client_root(client_root)
        status = MODULE._preflight_status(client_root)

        report = MODULE._render_preflight_report(status, issue=None)

    assert f"[client-root] path: {client_root}" in report
    assert "[client-root] android shell:" in report
    assert "[client-root] windows shell:" in report
    assert "[ok] POKROV-app gate root is present" in report


def test_preflight_issue_clears_once_seed_workspace_exists() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        client_root = Path(tmp)
        _prepare_client_root(client_root)

        issue = MODULE._preflight_issue_from_status(MODULE._preflight_status(client_root))

    assert issue is None

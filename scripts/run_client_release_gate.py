from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _resolve_client_root(platform_checkout: Path) -> Path:
    override = os.getenv("POKROV_APP_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()

    common_dir = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=platform_checkout,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    client_repo = Path(common_dir).resolve().parent.parent / "POKROV-app"
    if not (client_repo / ".git").exists():
        return client_repo

    worktrees = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=client_repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    for block in worktrees.strip().split("\n\n"):
        fields = dict(line.split(" ", 1) for line in block.splitlines() if " " in line)
        if fields.get("branch") == "refs/heads/main" and fields.get("worktree"):
            return Path(fields["worktree"]).resolve()
    return client_repo


CLIENT_ROOT = _resolve_client_root(REPO_ROOT)


@dataclass(frozen=True)
class ClientGateStep:
    command: list[str]
    cwd: Path


@dataclass(frozen=True)
class ClientGateCommand:
    steps: tuple[ClientGateStep, ...]
    expected_artifacts: tuple[Path, ...] = ()


@dataclass(frozen=True)
class ClientGatePreflightStatus:
    client_root: Path
    missing_paths: tuple[Path, ...]
    validate_seed_script: Path
    bootstrap_script: Path
    run_tests_script: Path
    sync_core_script: Path
    build_windows_script: Path
    android_shell_root: Path
    windows_shell_root: Path
    product_contract_path: Path
    runtime_profile_path: Path
    runtime_artifacts_path: Path
    windows_release_config_path: Path


def _run_captured(command: list[str], *, cwd: Path | None = None, runner=subprocess.run) -> subprocess.CompletedProcess:
    return runner(
        command,
        cwd=str(cwd) if cwd is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _resolve_powershell_executable() -> str:
    return shutil.which("pwsh") or shutil.which("powershell") or "powershell"


def _powershell_file_command(script_path: Path, *arguments: str) -> list[str]:
    return [
        _resolve_powershell_executable(),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        *arguments,
    ]


def _resolve_flutter_executable() -> str:
    return shutil.which("flutter.bat") or shutil.which("flutter") or "flutter"


def _preflight_status(client_root: Path) -> ClientGatePreflightStatus:
    validate_seed_script = client_root / "scripts" / "validate-seed.ps1"
    bootstrap_script = client_root / "scripts" / "bootstrap-workspace.ps1"
    run_tests_script = client_root / "scripts" / "run-tests.ps1"
    sync_core_script = client_root / "scripts" / "sync-pokrov-core-runtime.ps1"
    build_windows_script = client_root / "scripts" / "build-windows-release.ps1"
    android_shell_root = client_root / "apps" / "android_shell"
    windows_shell_root = client_root / "apps" / "windows_shell"
    product_contract_path = client_root / "config" / "product-contract.seed.json"
    runtime_profile_path = client_root / "config" / "runtime-profile.seed.json"
    runtime_artifacts_path = client_root / "config" / "runtime-artifacts.seed.json"
    windows_release_config_path = client_root / "config" / "windows-release.seed.json"
    required_paths = (
        client_root,
        validate_seed_script,
        bootstrap_script,
        run_tests_script,
        sync_core_script,
        build_windows_script,
        android_shell_root,
        windows_shell_root,
        product_contract_path,
        runtime_profile_path,
        runtime_artifacts_path,
        windows_release_config_path,
    )
    missing_paths = tuple(path for path in required_paths if not path.exists())
    return ClientGatePreflightStatus(
        client_root=client_root,
        missing_paths=missing_paths,
        validate_seed_script=validate_seed_script,
        bootstrap_script=bootstrap_script,
        run_tests_script=run_tests_script,
        sync_core_script=sync_core_script,
        build_windows_script=build_windows_script,
        android_shell_root=android_shell_root,
        windows_shell_root=windows_shell_root,
        product_contract_path=product_contract_path,
        runtime_profile_path=runtime_profile_path,
        runtime_artifacts_path=runtime_artifacts_path,
        windows_release_config_path=windows_release_config_path,
    )


def _preflight_issue_from_status(status: ClientGatePreflightStatus) -> str | None:
    if status.missing_paths:
        rendered = ", ".join(str(path) for path in status.missing_paths[:4])
        if len(status.missing_paths) > 4:
            rendered = f"{rendered} (+{len(status.missing_paths) - 4} more)"
        return f"POKROV-app gate root is incomplete: missing {rendered}"
    return None


def _render_preflight_report(
    status: ClientGatePreflightStatus,
    *,
    issue: str | None,
) -> str:
    lines = [
        f"[client-root] path: {status.client_root}",
        f"[client-root] android shell: {status.android_shell_root}",
        f"[client-root] windows shell: {status.windows_shell_root}",
        f"[client-root] validate seed: {status.validate_seed_script}",
        f"[client-root] bootstrap workspace: {status.bootstrap_script}",
        f"[client-root] run tests: {status.run_tests_script}",
        f"[client-root] sync core runtime: {status.sync_core_script}",
        f"[client-root] build windows release: {status.build_windows_script}",
    ]
    if status.missing_paths:
        for missing_path in status.missing_paths[:10]:
            lines.append(f"[client-root] missing: {missing_path}")
        if len(status.missing_paths) > 10:
            lines.append(f"[client-root] missing: ... (+{len(status.missing_paths) - 10} more)")
    lines.append(f"[{'fail' if issue else 'ok'}] {issue or 'POKROV-app gate root is present'}")
    return "\n".join(lines)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_pubspec_version(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    match = re.search(r"(?m)^version:\s*(.+)$", content)
    if match is None:
        raise ValueError(f"unable to resolve version from {path}")
    version = match.group(1).strip()
    if not version:
        raise ValueError(f"unable to resolve version from {path}: empty value")
    return version


def _suite_command(client_root: Path, *, suite: str) -> ClientGateCommand:
    status = _preflight_status(client_root)

    if suite == "full":
        return ClientGateCommand(
            steps=(
                ClientGateStep(
                    command=_powershell_file_command(status.run_tests_script),
                    cwd=client_root,
                ),
            )
        )
    if suite == "portal":
        return ClientGateCommand(
            steps=(
                ClientGateStep(
                    command=_powershell_file_command(status.bootstrap_script),
                    cwd=client_root,
                ),
                ClientGateStep(
                    command=["flutter", "test"],
                    cwd=client_root / "packages" / "app_shell",
                ),
                ClientGateStep(
                    command=["flutter", "test"],
                    cwd=status.android_shell_root,
                ),
                ClientGateStep(
                    command=["flutter", "test"],
                    cwd=status.windows_shell_root,
                ),
            )
        )
    raise ValueError(f"unsupported suite: {suite}")


def _android_target_command(client_root: Path, *, target: str) -> ClientGateCommand:
    status = _preflight_status(client_root)
    build_args = {
        "android-apk": ["build", "apk", "--release"],
        "android-aab": ["build", "appbundle", "--release"],
    }
    expected_artifacts = {
        "android-apk": status.android_shell_root / "build" / "app" / "outputs" / "flutter-apk" / "app-release.apk",
        "android-aab": status.android_shell_root / "build" / "app" / "outputs" / "bundle" / "release" / "app-release.aab",
    }
    return ClientGateCommand(
        steps=(
            ClientGateStep(
                command=_powershell_file_command(status.validate_seed_script),
                cwd=client_root,
            ),
            ClientGateStep(
                command=_powershell_file_command(status.bootstrap_script),
                cwd=client_root,
            ),
            ClientGateStep(
                command=["flutter", *build_args[target]],
                cwd=status.android_shell_root,
            ),
        ),
        expected_artifacts=(expected_artifacts[target],),
    )


def _windows_target_command(client_root: Path) -> ClientGateCommand:
    status = _preflight_status(client_root)
    release_config = _load_json(status.windows_release_config_path)
    version = _read_pubspec_version(status.windows_shell_root / "pubspec.yaml")
    artifact_root = client_root / str(release_config["artifact_root"])
    zip_name = str(release_config["zip_name_template"]).replace("{version}", version)
    installer_template = str(release_config.get("installer_name_template", "") or "").strip()
    installer_name = installer_template.replace("{version}", version) if installer_template else ""
    manifest_name = str(release_config["manifest_name_template"]).replace("{version}", version)
    expected = [artifact_root / zip_name]
    if installer_name:
        expected.append(artifact_root / installer_name)
    expected.append(artifact_root / manifest_name)
    return ClientGateCommand(
        steps=(
            ClientGateStep(
                command=_powershell_file_command(
                    status.build_windows_script,
                    "-SkipTests",
                    "-SkipAnalyze",
                ),
                cwd=client_root,
            ),
        ),
        expected_artifacts=tuple(expected),
    )


def _build_target_command(client_root: Path, *, target: str) -> ClientGateCommand:
    if target == "windows":
        return _windows_target_command(client_root)
    if target in {"android-apk", "android-aab"}:
        return _android_target_command(client_root, target=target)
    raise ValueError(f"unsupported target: {target}")


def _run_step(step: ClientGateStep) -> int:
    resolved_command = [
        _resolve_flutter_executable() if index == 0 and value == "flutter" else value
        for index, value in enumerate(step.command)
    ]
    print(f"[client-gate] {' '.join(resolved_command)} (cwd={step.cwd})")
    proc = subprocess.run(resolved_command, cwd=str(step.cwd))
    return int(proc.returncode)


def _run(command: ClientGateCommand, *, client_root: Path) -> int:
    status = _preflight_status(client_root)
    issue = _preflight_issue_from_status(status)
    if issue is not None:
        print(_render_preflight_report(status, issue=issue))
        return 2

    for step in command.steps:
        rc = _run_step(step)
        if rc != 0:
            return rc

    for expected_artifact in command.expected_artifacts:
        if not expected_artifact.exists():
            print(f"[fail] expected artifact is missing: {expected_artifact}")
            return 2

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run POKROV-app release gates from the platform repo.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    subparsers.add_parser("preflight")

    test_parser = subparsers.add_parser("test")
    test_parser.add_argument("--suite", choices=["full", "portal"], required=True)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--target", choices=["windows", "android-apk", "android-aab"], required=True)

    args = parser.parse_args()
    status = _preflight_status(CLIENT_ROOT)
    issue = _preflight_issue_from_status(status)

    if args.mode == "preflight":
        print(_render_preflight_report(status, issue=issue))
        return 0 if issue is None else 2

    if issue is not None:
        print(_render_preflight_report(status, issue=issue))
        return 2

    if args.mode == "test":
        command = _suite_command(CLIENT_ROOT, suite=args.suite)
    else:
        command = _build_target_command(CLIENT_ROOT, target=args.target)

    return _run(command, client_root=CLIENT_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())

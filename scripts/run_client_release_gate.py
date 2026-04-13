from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLIENT_ROOT = REPO_ROOT / "external" / "client-fork" / "app"


@dataclass(frozen=True)
class ClientGateCommand:
    command: list[str]
    cwd: Path
    expected_artifact: Path | None = None


@dataclass(frozen=True)
class LibcorePreflightStatus:
    expected_sha: str
    actual_sha: str
    branch: str
    dirty_lines: tuple[str, ...]


def _run_captured(command: list[str], *, runner=subprocess.run) -> subprocess.CompletedProcess:
    return runner(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _libcore_preflight_status(
    client_root: Path,
    *,
    runner=subprocess.run,
) -> tuple[LibcorePreflightStatus | None, str | None]:
    libcore_root = client_root / "libcore"
    expected = _run_captured(
        ["git", "-C", str(client_root), "rev-parse", "HEAD:libcore"],
        runner=runner,
    )
    if expected.returncode != 0:
        detail = (expected.stderr or expected.stdout or "").strip()
        return None, f"unable to resolve pinned libcore SHA: {detail or expected.returncode}"
    expected_sha = str(expected.stdout or "").strip()
    if not expected_sha:
        return None, "unable to resolve pinned libcore SHA: empty output"

    actual = _run_captured(
        ["git", "-C", str(libcore_root), "rev-parse", "HEAD"],
        runner=runner,
    )
    if actual.returncode != 0:
        if not libcore_root.exists():
            return None, f"libcore checkout is missing: {libcore_root}"
        detail = (actual.stderr or actual.stdout or "").strip()
        return None, f"unable to resolve libcore HEAD SHA: {detail or actual.returncode}"
    actual_sha = str(actual.stdout or "").strip()
    if not actual_sha:
        return None, "unable to resolve libcore HEAD SHA: empty output"

    branch = _run_captured(
        ["git", "-C", str(libcore_root), "branch", "--show-current"],
        runner=runner,
    )
    if branch.returncode != 0:
        detail = (branch.stderr or branch.stdout or "").strip()
        return None, f"unable to resolve libcore branch: {detail or branch.returncode}"
    branch_name = str(branch.stdout or "").strip() or "(detached HEAD)"

    dirty = _run_captured(
        ["git", "-C", str(libcore_root), "status", "--porcelain"],
        runner=runner,
    )
    if dirty.returncode != 0:
        detail = (dirty.stderr or dirty.stdout or "").strip()
        return None, f"unable to inspect libcore worktree: {detail or dirty.returncode}"
    dirty_lines = tuple(
        line.strip() for line in str(dirty.stdout or "").splitlines() if line.strip()
    )

    status = LibcorePreflightStatus(
        expected_sha=expected_sha,
        actual_sha=actual_sha,
        branch=branch_name,
        dirty_lines=dirty_lines,
    )
    return status, None


def _libcore_preflight_issue(client_root: Path, *, runner=subprocess.run) -> str | None:
    status, issue = _libcore_preflight_status(client_root, runner=runner)
    if issue is not None:
        return issue

    assert status is not None

    return _libcore_issue_from_status(status)


def _libcore_issue_from_status(status: LibcorePreflightStatus) -> str | None:
    if status.actual_sha != status.expected_sha:
        return (
            "libcore SHA drift: "
            f"expected {status.expected_sha}, got {status.actual_sha} "
            f"(branch {status.branch})"
        )

    if status.dirty_lines:
        preview = ", ".join(status.dirty_lines[:3])
        if len(status.dirty_lines) > 3:
            preview = f"{preview} (+{len(status.dirty_lines) - 3} more)"
        return (
            "libcore worktree is dirty: "
            f"pinned {status.expected_sha}, branch {status.branch}; "
            f"changes: {preview}"
        )

    return None


def _render_libcore_preflight_report(
    client_root: Path,
    *,
    status: LibcorePreflightStatus | None,
    issue: str | None,
) -> str:
    lines = [f"[libcore] path: {client_root / 'libcore'}"]
    if status is not None:
        lines.append(f"[libcore] pinned SHA: {status.expected_sha}")
        lines.append(f"[libcore] checked-out SHA: {status.actual_sha}")
        lines.append(f"[libcore] branch: {status.branch}")
        if status.dirty_lines:
            for dirty_line in status.dirty_lines[:10]:
                lines.append(f"[libcore] dirty: {dirty_line}")
            if len(status.dirty_lines) > 10:
                lines.append(f"[libcore] dirty: ... (+{len(status.dirty_lines) - 10} more)")
    lines.append(f"[{'fail' if issue else 'ok'}] {issue or 'libcore checkout is clean and pinned'}")
    return "\n".join(lines)


def _suite_command(client_root: Path, *, suite: str) -> ClientGateCommand:
    suite_commands = {
        "full": ["flutter", "test"],
        "portal": ["flutter", "test", "test/features/portal"],
    }
    command = suite_commands.get(suite)
    if command is None:
        raise ValueError(f"unsupported suite: {suite}")
    return ClientGateCommand(command=command, cwd=client_root)


def _build_target_command(client_root: Path, *, target: str) -> ClientGateCommand:
    commands = {
        "windows": (
            ["flutter", "build", "windows", "--release"],
            client_root / "build" / "windows" / "x64" / "runner" / "Release" / "POKROVVPN.exe",
        ),
        "android-apk": (
            ["flutter", "build", "apk", "--release"],
            client_root / "build" / "app" / "outputs" / "flutter-apk" / "app-release.apk",
        ),
        "android-aab": (
            ["flutter", "build", "appbundle", "--release"],
            client_root / "build" / "app" / "outputs" / "bundle" / "release" / "app-release.aab",
        ),
    }
    try:
        command, artifact = commands[target]
    except KeyError as exc:
        raise ValueError(f"unsupported target: {target}") from exc
    return ClientGateCommand(command=command, cwd=client_root, expected_artifact=artifact)


def _windows_sqlite_bootstrap_dir(client_root: Path) -> Path | None:
    candidates = [
        client_root / "build" / "windows" / "x64" / "runner" / "Release",
        client_root / "build" / "windows" / "x64" / "plugins" / "sqlite3_flutter_libs" / "Release",
    ]
    for directory in candidates:
        if (directory / "sqlite3.dll").exists():
            return directory
    return None


def _run(command: ClientGateCommand) -> int:
    libcore_status, libcore_error = _libcore_preflight_status(command.cwd)
    libcore_issue = libcore_error or (
        _libcore_issue_from_status(libcore_status) if libcore_status is not None else None
    )
    if libcore_issue is not None:
        print(
            _render_libcore_preflight_report(
                command.cwd,
                status=libcore_status,
                issue=libcore_error or libcore_issue,
            )
        )
        return 2

    env = os.environ.copy()
    executable = shutil.which("flutter.bat") or shutil.which("flutter") or "flutter"
    resolved_command = [
        executable if index == 0 and value == "flutter" else value
        for index, value in enumerate(command.command)
    ]

    if command.command[:2] == ["flutter", "test"] and os.name == "nt":
        bootstrap_dir = _windows_sqlite_bootstrap_dir(command.cwd)
        if bootstrap_dir is None:
            bootstrap = _build_target_command(command.cwd, target="windows")
            rc = _run(bootstrap)
            if rc != 0:
                return rc
            bootstrap_dir = _windows_sqlite_bootstrap_dir(command.cwd)
        if bootstrap_dir is not None:
            env["PATH"] = f"{bootstrap_dir}{os.pathsep}{env.get('PATH', '')}"

    print(f"[client-gate] {' '.join(command.command)} (cwd={command.cwd})")
    proc = subprocess.run(resolved_command, cwd=str(command.cwd), env=env)
    if proc.returncode != 0:
        return int(proc.returncode)

    if command.expected_artifact is not None and not command.expected_artifact.exists():
        print(f"[fail] expected artifact is missing: {command.expected_artifact}")
        return 2

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run client Flutter release gates from the root repo.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    subparsers.add_parser("preflight")

    test_parser = subparsers.add_parser("test")
    test_parser.add_argument("--suite", choices=["full", "portal"], required=True)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--target", choices=["windows", "android-apk", "android-aab"], required=True)

    args = parser.parse_args()
    if not CLIENT_ROOT.exists():
        print(f"[fail] client root is missing: {CLIENT_ROOT}")
        return 2

    if args.mode == "preflight":
        status, issue = _libcore_preflight_status(CLIENT_ROOT)
        issue = issue or _libcore_preflight_issue(CLIENT_ROOT)
        print(_render_libcore_preflight_report(CLIENT_ROOT, status=status, issue=issue))
        return 0 if issue is None else 2
    if args.mode == "test":
        command = _suite_command(CLIENT_ROOT, suite=args.suite)
    else:
        command = _build_target_command(CLIENT_ROOT, target=args.target)

    return _run(command)


if __name__ == "__main__":
    raise SystemExit(main())

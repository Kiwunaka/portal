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

    test_parser = subparsers.add_parser("test")
    test_parser.add_argument("--suite", choices=["full", "portal"], required=True)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--target", choices=["windows", "android-apk", "android-aab"], required=True)

    args = parser.parse_args()
    if not CLIENT_ROOT.exists():
        print(f"[fail] client root is missing: {CLIENT_ROOT}")
        return 2

    if args.mode == "test":
        command = _suite_command(CLIENT_ROOT, suite=args.suite)
    else:
        command = _build_target_command(CLIENT_ROOT, target=args.target)

    return _run(command)


if __name__ == "__main__":
    raise SystemExit(main())

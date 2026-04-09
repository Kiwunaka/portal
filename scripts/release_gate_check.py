from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE_PYTEST_ARGS = [
    "portal_bot/tests/test_app_first_api.py",
    "tests/test_portal_api.py",
    "tests/test_worker_retention.py",
    "tests/test_observer_service.py",
    "tests/test_observer_api.py",
    "tests/test_collect_xray_observer.py",
    "tests/test_predeploy_node_readiness.py",
    "tests/test_admin_webapp_smoke.py",
    "tests/test_public_copy_guardrails.py",
    "tests/test_reviews_username_masking.py",
    "-q",
]


def _npm_exec() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


@dataclass
class GateResult:
    name: str
    command: str
    returncode: int
    duration_sec: float
    output_tail: str


def _is_frontend_build(command: list[str], cwd: Path) -> bool:
    return len(command) >= 3 and command[0] == _npm_exec() and command[1:3] == ["run", "build"] and (cwd / "package.json").exists()


def _prepare_frontend_build_copy(cwd: Path) -> Path:
    temp_root = Path(tempfile.mkdtemp(prefix=f"{cwd.name}-gate-"))
    target = temp_root / cwd.name
    shutil.copytree(
        cwd,
        target,
        ignore=shutil.ignore_patterns("out", ".next", "node_modules"),
    )
    shared_src = REPO_ROOT / "shared"
    shared_dst = temp_root / "shared"
    if shared_src.exists():
        shutil.copytree(shared_src, shared_dst, dirs_exist_ok=True)
    copy_src = REPO_ROOT / "copy"
    copy_dst = temp_root / "copy"
    if copy_src.exists():
        shutil.copytree(copy_src, copy_dst, dirs_exist_ok=True)
    source_node_modules = cwd / "node_modules"
    target_node_modules = target / "node_modules"
    if cwd.name.lower() == "webapp":
        proc = subprocess.run(
            [_npm_exec(), "ci", "--no-audit", "--no-fund"],
            cwd=str(target),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Failed to install dependencies for {cwd}: {(proc.stdout or '').strip()}")
        return target
    if os.name == "nt":
        proc = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(target_node_modules), str(source_node_modules)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Failed to create node_modules junction for {cwd}: {(proc.stdout or '').strip()}")
    else:
        target_node_modules.symlink_to(source_node_modules, target_is_directory=True)
    return target


def _run_cmd(*, name: str, command: list[str], cwd: Path) -> GateResult:
    run_cwd = cwd
    cleanup_dir: Path | None = None
    if _is_frontend_build(command, cwd):
        run_cwd = _prepare_frontend_build_copy(cwd)
        cleanup_dir = run_cwd.parent
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            command,
            cwd=str(run_cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    finally:
        if cleanup_dir:
            shutil.rmtree(cleanup_dir, ignore_errors=True)
    duration = time.perf_counter() - started
    out = (proc.stdout or "").strip()
    tail = "\n".join(out.splitlines()[-40:]) if out else ""
    return GateResult(
        name=name,
        command=" ".join(command),
        returncode=int(proc.returncode),
        duration_sec=duration,
        output_tail=tail,
    )


def _render_markdown(results: list[GateResult]) -> str:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok = all(r.returncode == 0 for r in results)
    lines: list[str] = []
    lines.append("# Release Gate Report")
    lines.append("")
    lines.append(f"- Generated at: `{created_at}`")
    lines.append(f"- Status: `{'PASS' if ok else 'FAIL'}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Gate | Exit code | Duration (s) |")
    lines.append("|---|---:|---:|")
    for r in results:
        lines.append(f"| {r.name} | {r.returncode} | {r.duration_sec:.2f} |")
    lines.append("")
    lines.append("## Command Tails")
    lines.append("")
    for r in results:
        lines.append(f"### {r.name}")
        lines.append("")
        lines.append(f"- Command: `{r.command}`")
        lines.append(f"- Exit: `{r.returncode}`")
        lines.append("")
        lines.append("```text")
        lines.append(r.output_tail or "<no output>")
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def _optional_runtime_smoke_gate() -> tuple[str, list[str], Path] | None:
    init_data = str(os.getenv("TELEGRAM_INIT_DATA", "") or "").strip()
    if not init_data:
        return None
    return (
        "Client apps runtime smoke",
        [
            sys.executable,
            "scripts/smoke_client_apps.py",
            "--check-providers",
            "--require-release-handoff",
        ],
        REPO_ROOT,
    )


def _optional_android_localhost_audit_gate() -> tuple[str, list[str], Path] | None:
    serial = str(os.getenv("ANDROID_AUDIT_SERIAL", "") or "").strip()
    if not serial:
        return None
    connect_wait_sec = str(os.getenv("ANDROID_AUDIT_CONNECT_WAIT_SEC", "30") or "30").strip()
    disconnect_wait_sec = str(os.getenv("ANDROID_AUDIT_DISCONNECT_WAIT_SEC", "15") or "15").strip()
    return (
        "Android localhost audit",
        [
            sys.executable,
            "scripts/android_localhost_audit.py",
            "--serial",
            serial,
            "--connect-wait-sec",
            connect_wait_sec,
            "--disconnect-wait-sec",
            disconnect_wait_sec,
        ],
        REPO_ROOT,
    )


def _api_lifecycle_smoke_gate() -> tuple[str, list[str], Path]:
    return (
        "API lifecycle smoke",
        [
            sys.executable,
            "scripts/api_lifecycle_smoke.py",
        ],
        REPO_ROOT,
    )


def _release_pytest_gate() -> tuple[str, list[str], Path]:
    return (
        "Release pytest matrix",
        [sys.executable, "-m", "pytest", *RELEASE_PYTEST_ARGS],
        REPO_ROOT,
    )


def _client_security_smoke_gate() -> tuple[str, list[str], Path]:
    return (
        "Client security smoke",
        [sys.executable, "scripts/client_security_smoke.py"],
        REPO_ROOT,
    )


def _predeploy_node_readiness_gate(
    *,
    brain_ip: str,
    domain: str,
    ssh_user: str,
    ssh_port: int,
    passwords: str,
) -> tuple[str, list[str], Path]:
    return (
        "Node predeploy readiness",
        [
            sys.executable,
            "scripts/predeploy_node_readiness.py",
            "--brain-ip",
            brain_ip,
            "--web-domain",
            domain,
            "--ssh-user",
            ssh_user,
            "--ssh-port",
            str(ssh_port),
            "--passwords",
            passwords,
        ],
        REPO_ROOT,
    )


def _default_gates() -> list[tuple[str, list[str], Path]]:
    return [
        _release_pytest_gate(),
        ("Admin/auth regressions", [sys.executable, "-m", "pytest", "tests/test_api_auth_and_tickets.py", "-q"], REPO_ROOT),
        _client_security_smoke_gate(),
        _api_lifecycle_smoke_gate(),
        ("Public link checks", [sys.executable, "scripts/check-links.py"], REPO_ROOT),
        ("Marketing production build", [_npm_exec(), "run", "build"], REPO_ROOT / "marketing"),
        ("Admin webapp smoke", [sys.executable, "scripts/admin_webapp_smoke.py"], REPO_ROOT),
        ("WebApp production build", [_npm_exec(), "run", "build"], REPO_ROOT / "webapp"),
        ("WebApp Playwright E2E", [_npm_exec(), "run", "test:e2e"], REPO_ROOT / "webapp"),
        ("UI visual smoke", [sys.executable, "scripts/ui_visual_smoke.py"], REPO_ROOT),
    ]


def _quick_gates() -> list[tuple[str, list[str], Path]]:
    return [
        ("Critical worker regression", [sys.executable, "-m", "pytest", "tests/test_worker_retention.py", "-q"], REPO_ROOT),
        _client_security_smoke_gate(),
        _api_lifecycle_smoke_gate(),
        ("Public link checks", [sys.executable, "scripts/check-links.py"], REPO_ROOT),
        ("Marketing production build", [_npm_exec(), "run", "build"], REPO_ROOT / "marketing"),
        ("Admin webapp smoke", [sys.executable, "scripts/admin_webapp_smoke.py"], REPO_ROOT),
        ("WebApp production build", [_npm_exec(), "run", "build"], REPO_ROOT / "webapp"),
        ("WebApp Playwright E2E", [_npm_exec(), "run", "test:e2e"], REPO_ROOT / "webapp"),
        ("UI visual smoke", [sys.executable, "scripts/ui_visual_smoke.py"], REPO_ROOT),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local release gates and save markdown report.")
    parser.add_argument(
        "--output",
        default="docs/audit-artifacts/release_gate_report.md",
        help="Output markdown file path (relative to repository root).",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run a shorter gate set.",
    )
    parser.add_argument("--brain-ip", default="")
    parser.add_argument("--web-domain", default="pokrov.space")
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"))
    args = parser.parse_args()

    gates: list[tuple[str, list[str], Path]] = []
    if str(args.brain_ip or "").strip():
        gates.append(
            _predeploy_node_readiness_gate(
                brain_ip=str(args.brain_ip).strip(),
                domain=args.web_domain,
                ssh_user=args.ssh_user,
                ssh_port=int(args.ssh_port),
                passwords=args.passwords,
            )
        )

    gates.extend(_default_gates())
    if args.quick:
        gates = []
        if str(args.brain_ip or "").strip():
            gates.append(
                _predeploy_node_readiness_gate(
                    brain_ip=str(args.brain_ip).strip(),
                    domain=args.web_domain,
                    ssh_user=args.ssh_user,
                    ssh_port=int(args.ssh_port),
                    passwords=args.passwords,
                )
            )
        gates.extend(_quick_gates())

    runtime_smoke_gate = _optional_runtime_smoke_gate()
    if runtime_smoke_gate is not None:
        gates.append(runtime_smoke_gate)

    android_localhost_audit_gate = _optional_android_localhost_audit_gate()
    if android_localhost_audit_gate is not None:
        gates.append(android_localhost_audit_gate)

    results: list[GateResult] = []
    for name, cmd, cwd in gates:
        print(f"[gate] {name}: {' '.join(cmd)}")
        results.append(_run_cmd(name=name, command=cmd, cwd=cwd))

    output_path = (REPO_ROOT / args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_render_markdown(results), encoding="utf-8")

    print(f"[report] {output_path}")
    for r in results:
        print(f"[result] {r.name}: exit={r.returncode} duration={r.duration_sec:.2f}s")

    return 0 if all(r.returncode == 0 for r in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())

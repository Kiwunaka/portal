from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTEST_BASETEMP_ROOT = REPO_ROOT / ".tmp" / "pytest-basetemp"
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


@dataclass
class ReportContext:
    quick: bool
    brain_ip: str
    client_platform_gates: list[str]
    runtime_smoke_requested: bool
    android_audit_requested: bool
    android_audit_required: bool


_SECRET_OPTION_RE = re.compile(
    r"(?i)(--(?:token|secret|password|passwd|api-key|auth|authorization|client-secret))\s+([^\s`]+)"
)
_TELEGRAM_INIT_OPTION_RE = re.compile(r"(?i)(--init-data)(?:=|\s+)([^\s`]+)")
_TELEGRAM_INIT_ENV_RE = re.compile(r"(?i)\b(TELEGRAM_INIT_DATA\s*[:=]\s*)([^\s`]+)")
_TELEGRAM_INIT_HEADER_RE = re.compile(r"(?i)\b(X-Telegram-Init-Data\s*:\s*)([^\r\n`]+)")
_TELEGRAM_INIT_FIELD_RE = re.compile(
    r"(?i)\b(query_id|user|auth_date|hash|signature|chat_instance|start_param|can_send_after)=([^&\s`]+)"
)
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b((?:secret|secret[_-]?key|token|password|passwd|api[_-]?key|client[_-]?secret)\s*[:=]\s*)([^\s`]+)"
)
_BEARER_RE = re.compile(r"(?i)\bBearer\s+([A-Za-z0-9._~+/=-]+)")
DEFAULT_ANDROID_AUDIT_PACKAGE = "space.pokrov.pokrov_android_shell"
CLIENT_ROOT = Path(os.getenv("POKROV_APP_ROOT", str(REPO_ROOT.parent / "POKROV-app")))
CLIENT_ROOT_REQUIRED_PATHS = (
    CLIENT_ROOT / "config" / "product-contract.seed.json",
    CLIENT_ROOT / "config" / "runtime-profile.seed.json",
    CLIENT_ROOT / "config" / "runtime-artifacts.seed.json",
    CLIENT_ROOT / "apps" / "android_shell",
    CLIENT_ROOT / "apps" / "windows_shell",
)
CLIENT_ROOT_GATE_NAMES = {
    "Client security smoke",
    "Client Flutter tests",
    "Client portal Flutter tests",
}


def _redact_text(text: str) -> str:
    redacted = _SECRET_OPTION_RE.sub(r"\1 <redacted>", str(text or ""))
    redacted = _TELEGRAM_INIT_OPTION_RE.sub(r"\1 <redacted>", redacted)
    redacted = _TELEGRAM_INIT_ENV_RE.sub(r"\1<redacted>", redacted)
    redacted = _TELEGRAM_INIT_HEADER_RE.sub(r"\1<redacted>", redacted)
    redacted = _BEARER_RE.sub("Bearer <redacted>", redacted)
    redacted = _SECRET_ASSIGNMENT_RE.sub(r"\1<redacted>", redacted)
    redacted = _TELEGRAM_INIT_FIELD_RE.sub(r"\1=<redacted>", redacted)
    return redacted


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
    if cwd.name.lower() == "webapp" or not source_node_modules.exists():
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


def _missing_client_root_issue() -> str | None:
    missing = [path for path in CLIENT_ROOT_REQUIRED_PATHS if not path.exists()]
    if not missing:
        return None
    rendered = ", ".join(str(path) for path in missing[:3])
    if len(missing) > 3:
        rendered = f"{rendered} (+{len(missing) - 3} more)"
    return f"POKROV-app workspace is unavailable for this gate run: missing {rendered}"


def _client_workspace_skipped_gate(issue: str) -> tuple[str, list[str], Path]:
    return (
        "Client workspace preflight (skipped)",
        [
            sys.executable,
            "-c",
            f"print({issue!r}); print('BLOCKED_BY_ACCESS: client gates skipped for this CI guardrail run')",
        ],
        REPO_ROOT,
    )


def _filter_client_gates_when_missing(
    gates: list[tuple[str, list[str], Path]],
    *,
    allow_missing_client_root: bool,
    client_platform_gates: list[str],
) -> list[tuple[str, list[str], Path]]:
    issue = _missing_client_root_issue()
    if issue is None:
        return gates
    if not allow_missing_client_root or client_platform_gates:
        return gates
    return [
        *(gate for gate in gates if gate[0] not in CLIENT_ROOT_GATE_NAMES),
        _client_workspace_skipped_gate(issue),
    ]


def _is_pytest_command(command: list[str]) -> bool:
    return len(command) >= 3 and command[1:3] == ["-m", "pytest"]


def _has_pytest_basetemp(command: list[str]) -> bool:
    return any(part == "--basetemp" or str(part).startswith("--basetemp=") for part in command)


def _prepare_pytest_command(command: list[str]) -> tuple[list[str], Path | None]:
    if not _is_pytest_command(command) or _has_pytest_basetemp(command):
        return command, None
    PYTEST_BASETEMP_ROOT.mkdir(parents=True, exist_ok=True)
    basetemp = Path(tempfile.mkdtemp(prefix="release-gate-", dir=str(PYTEST_BASETEMP_ROOT)))
    return [*command, "--basetemp", str(basetemp)], basetemp


def _run_cmd(*, name: str, command: list[str], cwd: Path) -> GateResult:
    run_cwd = cwd
    cleanup_paths: list[Path] = []
    prepared_command = command
    if _is_frontend_build(command, cwd):
        run_cwd = _prepare_frontend_build_copy(cwd)
        cleanup_paths.append(run_cwd.parent)
    prepared_command, pytest_basetemp = _prepare_pytest_command(prepared_command)
    if pytest_basetemp is not None:
        cleanup_paths.append(pytest_basetemp)
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            prepared_command,
            cwd=str(run_cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    finally:
        for cleanup_path in reversed(cleanup_paths):
            shutil.rmtree(cleanup_path, ignore_errors=True)
    duration = time.perf_counter() - started
    out = (proc.stdout or "").strip()
    tail = "\n".join(out.splitlines()[-40:]) if out else ""
    return GateResult(
        name=name,
        command=" ".join(prepared_command),
        returncode=int(proc.returncode),
        duration_sec=duration,
        output_tail=tail,
    )


def _status_for_gate(results: list[GateResult], gate_name: str) -> str:
    for result in results:
        if result.name == gate_name:
            return "PASS" if result.returncode == 0 else "FAIL"
    return "NOT_RUN"


def _render_evidence_classification(results: list[GateResult], context: ReportContext) -> list[str]:
    gate_set = "quick" if context.quick else "default"
    if not results:
        current_status = "NOT_RUN"
    else:
        current_status = "PASS" if all(r.returncode == 0 for r in results) else "FAIL"

    brain_status = (
        _status_for_gate(results, "Node predeploy readiness")
        if str(context.brain_ip or "").strip()
        else "BLOCKED_BY_ACCESS"
    )
    ru_status = "BLOCKED_BY_ACCESS"

    if context.android_audit_requested:
        android_status = _status_for_gate(results, "Android localhost audit")
    else:
        android_status = "BLOCKED_BY_ACCESS"

    runtime_status = (
        _status_for_gate(results, "Client apps runtime smoke")
        if context.runtime_smoke_requested
        else "SKIPPED_NO_LIVE_TOKEN"
    )
    platform_status = "NOT_REQUESTED"
    if context.client_platform_gates:
        platform_results = [
            _status_for_gate(results, _client_build_gate(target=target)[0])
            for target in context.client_platform_gates
        ]
        platform_status = "PASS" if all(status == "PASS" for status in platform_results) else "FAIL"

    lines = [
        "## Evidence Classification",
        "",
        "| Evidence | Scope | Status | Notes |",
        "|---|---|---|---|",
        (
            f"| current-origin check | local {gate_set} gate set | {current_status} | "
            "Runs on the operator workstation; does not prove brain-origin or RU-origin reachability. |"
        ),
        (
            f"| brain-origin check | `scripts/verify_brain_ready.py` / predeploy readiness | {brain_status} | "
            "Requires `--brain-ip` and live SSH/API access; keep separate from current-origin results. |"
        ),
        (
            f"| RU-origin check | external RU probe (`mini` or replacement) | {ru_status} | "
            "Not run by this local gate; requires an external RU probe host and redacted report. |"
        ),
        (
            f"| Android physical audit | release-build localhost/control-surface audit | {android_status} | "
            "Public Android remains blocked unless this is run on physical hardware with the release build. |"
        ),
        (
            f"| Runtime app-download smoke | `/api/client/apps` and provider checks | {runtime_status} | "
            "Requires `TELEGRAM_INIT_DATA`; omit raw token values from evidence. |"
        ),
        (
            f"| Client platform builds | {', '.join(context.client_platform_gates) or 'none requested'} | {platform_status} | "
            "Repo/static gates alone do not create Android or Windows beta artifacts. |"
        ),
    ]
    lines.append("")
    return lines


def _render_markdown(results: list[GateResult], *, context: ReportContext | None = None) -> str:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok = all(r.returncode == 0 for r in results)
    context = context or ReportContext(
        quick=False,
        brain_ip="",
        client_platform_gates=[],
        runtime_smoke_requested=False,
        android_audit_requested=False,
        android_audit_required=False,
    )
    lines: list[str] = []
    lines.append("# Release Gate Report")
    lines.append("")
    lines.append(f"- Generated at: `{created_at}`")
    lines.append(f"- Status: `{'PASS' if ok else 'FAIL'}`")
    lines.append(f"- Gate set: `{'quick' if context.quick else 'default'}`")
    lines.append(f"- Brain IP supplied: `{'yes' if str(context.brain_ip or '').strip() else 'no'}`")
    lines.append(f"- Client platform gates: `{', '.join(context.client_platform_gates) or 'none'}`")
    lines.append(f"- Android audit required by selected gates: `{'yes' if context.android_audit_required else 'no'}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Gate | Exit code | Duration (s) |")
    lines.append("|---|---:|---:|")
    for r in results:
        lines.append(f"| {r.name} | {r.returncode} | {r.duration_sec:.2f} |")
    lines.append("")
    lines.extend(_render_evidence_classification(results, context))
    lines.append("## Command Tails")
    lines.append("")
    for r in results:
        lines.append(f"### {r.name}")
        lines.append("")
        lines.append(f"- Command: `{_redact_text(r.command)}`")
        lines.append(f"- Exit: `{r.returncode}`")
        lines.append("")
        lines.append("```text")
        lines.append(_redact_text(r.output_tail) if r.output_tail else "<no output>")
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
            "scripts/runtime_app_download_smoke.py",
            "--redact",
            "--check-providers",
            "--require-release-handoff",
        ],
        REPO_ROOT,
    )


def _optional_android_localhost_audit_gate() -> tuple[str, list[str], Path] | None:
    serial = str(os.getenv("ANDROID_AUDIT_SERIAL", "") or "").strip()
    if not serial:
        return None
    package_name = str(os.getenv("ANDROID_AUDIT_PACKAGE", "") or "").strip() or DEFAULT_ANDROID_AUDIT_PACKAGE
    release_evidence = str(os.getenv("ANDROID_AUDIT_RELEASE_EVIDENCE", "") or "").strip()
    expected_version_name = str(os.getenv("ANDROID_AUDIT_EXPECTED_VERSION_NAME", "") or "").strip()
    expected_version_code = str(os.getenv("ANDROID_AUDIT_EXPECTED_VERSION_CODE", "") or "").strip()
    connect_wait_sec = str(os.getenv("ANDROID_AUDIT_CONNECT_WAIT_SEC", "30") or "30").strip()
    disconnect_wait_sec = str(os.getenv("ANDROID_AUDIT_DISCONNECT_WAIT_SEC", "15") or "15").strip()
    command = [
        sys.executable,
        "scripts/android_localhost_audit.py",
        "--serial",
        serial,
        "--package",
        package_name,
        "--connect-wait-sec",
        connect_wait_sec,
        "--disconnect-wait-sec",
        disconnect_wait_sec,
    ]
    if release_evidence:
        command.extend(["--release-evidence", release_evidence, "--require-release-build"])
    if expected_version_name:
        command.extend(["--expected-version-name", expected_version_name])
    if expected_version_code:
        command.extend(["--expected-version-code", expected_version_code])
    return ("Android localhost audit", command, REPO_ROOT)


def _required_android_localhost_audit_gate() -> tuple[str, list[str], Path]:
    gate = _optional_android_localhost_audit_gate()
    if gate is None:
        raise ValueError(
            "ANDROID_AUDIT_SERIAL must reference a physical Android device when Android client build gates are requested"
        )
    serial = str(os.getenv("ANDROID_AUDIT_SERIAL", "") or "").strip().lower()
    if serial.startswith("emulator-"):
        raise ValueError(
            "ANDROID_AUDIT_SERIAL must reference physical hardware, not an emulator, when Android client build gates are requested"
        )
    if not str(os.getenv("ANDROID_AUDIT_RELEASE_EVIDENCE", "") or "").strip():
        raise ValueError(
            "ANDROID_AUDIT_RELEASE_EVIDENCE must identify the release-installed artifact, checksum, or handoff record "
            "when Android client build gates are requested"
        )
    return gate


def _select_android_localhost_audit_gate(
    *, client_platform_gates: list[str]
) -> tuple[str, list[str], Path] | None:
    requires_android_audit = any(
        target in {"android-apk", "android-aab"} for target in client_platform_gates
    )
    return (
        _required_android_localhost_audit_gate()
        if requires_android_audit
        else _optional_android_localhost_audit_gate()
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


def _client_flutter_test_gate(*, suite: str) -> tuple[str, list[str], Path]:
    gate_names = {
        "full": "Client Flutter tests",
        "portal": "Client portal Flutter tests",
    }
    return (
        gate_names[suite],
        [sys.executable, "scripts/run_client_release_gate.py", "test", "--suite", suite],
        REPO_ROOT,
    )


def _client_build_gate(*, target: str) -> tuple[str, list[str], Path]:
    gate_names = {
        "windows": "Client Windows release build",
        "android-apk": "Client Android APK build",
        "android-aab": "Client Android AAB build",
    }
    return (
        gate_names[target],
        [sys.executable, "scripts/run_client_release_gate.py", "build", "--target", target],
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


def _parse_client_platform_gates(raw_value: str) -> list[str]:
    source = str(raw_value or "").strip() or str(os.getenv("CLIENT_PLATFORM_GATES", "") or "").strip()
    if not source:
        return []
    valid = {"windows", "android-apk", "android-aab"}
    parsed = [item.strip().lower() for item in source.split(",") if item.strip()]
    invalid = [item for item in parsed if item not in valid]
    if invalid:
        raise ValueError(f"unsupported client platform gates: {', '.join(invalid)}")
    return parsed


def _default_gates(*, client_platform_gates: list[str] | None = None) -> list[tuple[str, list[str], Path]]:
    gates = [
        _release_pytest_gate(),
        ("Admin/auth regressions", [sys.executable, "-m", "pytest", "tests/test_api_auth_and_tickets.py", "-q"], REPO_ROOT),
        _client_security_smoke_gate(),
        _client_flutter_test_gate(suite="full"),
        _api_lifecycle_smoke_gate(),
        ("Public link checks", [sys.executable, "scripts/check-links.py"], REPO_ROOT),
        ("Marketing production build", [_npm_exec(), "run", "build"], REPO_ROOT / "marketing"),
        ("Admin webapp smoke", [sys.executable, "scripts/admin_webapp_smoke.py"], REPO_ROOT),
        ("WebApp production build", [_npm_exec(), "run", "build"], REPO_ROOT / "webapp"),
        ("WebApp Playwright E2E", [_npm_exec(), "run", "test:e2e"], REPO_ROOT / "webapp"),
        ("UI visual smoke", [sys.executable, "scripts/ui_visual_smoke.py"], REPO_ROOT),
    ]
    for target in client_platform_gates or []:
        gates.append(_client_build_gate(target=target))
    return gates


def _quick_gates(*, client_platform_gates: list[str] | None = None) -> list[tuple[str, list[str], Path]]:
    gates = [
        ("Critical worker regression", [sys.executable, "-m", "pytest", "tests/test_worker_retention.py", "-q"], REPO_ROOT),
        _client_security_smoke_gate(),
        _client_flutter_test_gate(suite="portal"),
        _api_lifecycle_smoke_gate(),
        ("Public link checks", [sys.executable, "scripts/check-links.py"], REPO_ROOT),
        ("Marketing production build", [_npm_exec(), "run", "build"], REPO_ROOT / "marketing"),
        ("Admin webapp smoke", [sys.executable, "scripts/admin_webapp_smoke.py"], REPO_ROOT),
        ("WebApp production build", [_npm_exec(), "run", "build"], REPO_ROOT / "webapp"),
        ("WebApp Playwright E2E", [_npm_exec(), "run", "test:e2e"], REPO_ROOT / "webapp"),
        ("UI visual smoke", [sys.executable, "scripts/ui_visual_smoke.py"], REPO_ROOT),
    ]
    for target in client_platform_gates or []:
        gates.append(_client_build_gate(target=target))
    return gates


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
    parser.add_argument(
        "--client-platform-gates",
        default="",
        help="Optional comma-separated client build gates: windows,android-apk,android-aab",
    )
    parser.add_argument(
        "--allow-missing-client-root",
        action="store_true",
        help="Skip sibling POKROV-app checks when that private workspace is unavailable in CI.",
    )
    args = parser.parse_args()

    try:
        client_platform_gates = _parse_client_platform_gates(args.client_platform_gates)
        android_localhost_audit_gate = _select_android_localhost_audit_gate(
            client_platform_gates=client_platform_gates
        )
    except ValueError as exc:
        print(f"[fail] {exc}")
        return 2

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

    gates.extend(_default_gates(client_platform_gates=client_platform_gates))
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
        gates.extend(_quick_gates(client_platform_gates=client_platform_gates))

    runtime_smoke_gate = _optional_runtime_smoke_gate()
    if runtime_smoke_gate is not None:
        gates.append(runtime_smoke_gate)

    if android_localhost_audit_gate is not None:
        gates.append(android_localhost_audit_gate)

    allow_missing_client_root = bool(args.allow_missing_client_root) or str(
        os.getenv("ALLOW_MISSING_CLIENT_ROOT", "")
    ).strip().lower() in {"1", "true", "yes"}
    gates = _filter_client_gates_when_missing(
        gates,
        allow_missing_client_root=allow_missing_client_root,
        client_platform_gates=client_platform_gates,
    )

    results: list[GateResult] = []
    for name, cmd, cwd in gates:
        print(f"[gate] {name}: {' '.join(cmd)}")
        results.append(_run_cmd(name=name, command=cmd, cwd=cwd))

    output_path = (REPO_ROOT / args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    context = ReportContext(
        quick=bool(args.quick),
        brain_ip=str(args.brain_ip or "").strip(),
        client_platform_gates=client_platform_gates,
        runtime_smoke_requested=runtime_smoke_gate is not None,
        android_audit_requested=android_localhost_audit_gate is not None,
        android_audit_required=any(target in {"android-apk", "android-aab"} for target in client_platform_gates),
    )
    output_path.write_text(_render_markdown(results, context=context), encoding="utf-8")

    print(f"[report] {output_path}")
    for r in results:
        print(f"[result] {r.name}: exit={r.returncode} duration={r.duration_sec:.2f}s")

    return 0 if all(r.returncode == 0 for r in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())

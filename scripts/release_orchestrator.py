from __future__ import annotations

import argparse
import queue
import re
import subprocess
import sys
import time
from copy import copy
from pathlib import Path
from threading import Thread


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BACKEND_RESTART_UNITS = (
    "portal-api",
    "portal-bot",
    "portal-helpbot",
    "portal-feedbackbot",
)


def _parse_qdisc_hosts(values: list[str] | None) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for raw in values or []:
        text = str(raw or "").strip()
        if not text or "=" not in text:
            continue
        node_code, host = text.split("=", 1)
        node_code = str(node_code or "").strip().lower()
        host = str(host or "").strip()
        if node_code and host:
            mapping[node_code] = host
    return mapping


def _stream_pipe(pipe, output: "queue.Queue[str]") -> None:
    try:
        for line in iter(pipe.readline, ""):
            output.put(line)
    finally:
        try:
            pipe.close()
        except Exception:
            pass


def _run(name: str, cmd: list[str], cwd: Path = REPO_ROOT, *, timeout_sec: int | None = None, heartbeat_sec: int = 30) -> int:
    started = time.monotonic()
    timeout_label = f" timeout={timeout_sec}s" if timeout_sec else ""
    print(f"[step] {name}: {' '.join(cmd)}{timeout_label}", flush=True)
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except OSError as exc:
        print(f"[fail] {name} start failed: {exc}", flush=True)
        return 127

    output: "queue.Queue[str]" = queue.Queue()
    if proc.stdout is not None:
        Thread(target=_stream_pipe, args=(proc.stdout, output), daemon=True).start()

    last_heartbeat = started
    while True:
        try:
            line = output.get(timeout=1)
        except queue.Empty:
            line = ""
        if line:
            sys.stdout.write(line)
            sys.stdout.flush()

        now = time.monotonic()
        if proc.poll() is not None:
            while True:
                try:
                    line = output.get_nowait()
                except queue.Empty:
                    break
                sys.stdout.write(line)
            sys.stdout.flush()
            break

        elapsed = now - started
        if timeout_sec and elapsed >= timeout_sec:
            proc.kill()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
            print(f"[fail] {name} timed out after {int(elapsed)}s", flush=True)
            return 124
        if heartbeat_sec > 0 and now - last_heartbeat >= heartbeat_sec:
            print(f"[step] {name}: still running ({int(elapsed)}s elapsed)", flush=True)
            last_heartbeat = now

    elapsed = time.monotonic() - started
    if proc.returncode != 0:
        print(f"[fail] {name} exit={proc.returncode} duration={int(elapsed)}s", flush=True)
        return int(proc.returncode)
    print(f"[ok] {name} duration={int(elapsed)}s", flush=True)
    return 0


def _dry_run(name: str, cmd: list[str], cwd: Path = REPO_ROOT) -> None:
    print(f"[dry-run] {name}: {' '.join(cmd)} (cwd={cwd})", flush=True)


def _build_qdisc_base_cmd(args: argparse.Namespace, node_code: str) -> list[str]:
    qdisc_hosts = _parse_qdisc_hosts(getattr(args, "qdisc_host", []))
    base_cmd = [
        "--profiles",
        args.qdisc_profiles,
        "--node-code",
        node_code,
        "--ssh-user",
        args.ssh_user,
        "--ssh-port",
        str(args.ssh_port),
        "--passwords",
        args.passwords,
    ]
    host = qdisc_hosts.get(node_code, "")
    if host:
        base_cmd.extend(["--host", host])
    return base_cmd


def _extract_qdisc_node_code(step_name: str) -> str:
    match = re.search(r"\(([^()]+)\)\s*$", str(step_name or "").strip())
    return str(match.group(1)).strip().lower() if match else ""


def _build_qdisc_failure_cleanup_steps(
    args: argparse.Namespace,
    *,
    step_name: str,
    python: str,
) -> list[tuple[str, list[str], Path]]:
    normalized_name = str(step_name or "").strip().lower()
    if not normalized_name.startswith("qdisc "):
        return []
    if "rollback" in normalized_name or "disable" in normalized_name:
        return []

    node_code = _extract_qdisc_node_code(step_name)
    if not node_code:
        return []

    base_cmd = _build_qdisc_base_cmd(args, node_code)
    return [
        (
            f"qdisc rollback-safe disable ({node_code})",
            [python, "scripts/remote_apply_node_qdisc.py", "disable", *base_cmd],
            REPO_ROOT,
        ),
        (
            f"qdisc rollback ({node_code})",
            [python, "scripts/remote_apply_node_qdisc.py", "rollback", *base_cmd],
            REPO_ROOT,
        ),
    ]


def _apply_stage(args: argparse.Namespace) -> None:
    stage = str(getattr(args, "stage", "all") or "all").strip().lower()
    if stage == "all":
        return
    if stage == "gates":
        args.gates_only = True
        return
    if stage == "verify":
        args.verify_only = True
        return

    args.skip_gates = True
    args.skip_verify = True
    args.ensure_metrics_timer = False
    args.ensure_observer_node = []
    args.qdisc_node = []
    args.qdisc_host = []
    if stage == "backend":
        args.skip_backend = False
        args.skip_static = True
    elif stage == "static":
        args.skip_backend = True
        args.skip_static = False
    elif stage == "deploy":
        args.skip_backend = False
        args.skip_static = False
    else:
        raise SystemExit(f"unknown --stage value: {stage}")


def _step_timeout_sec(args: argparse.Namespace, step_name: str) -> int | None:
    name = str(step_name or "").strip().lower()
    if name == "release gates":
        value = getattr(args, "gate_timeout_sec", None)
    elif name == "backend deploy":
        value = getattr(args, "backend_timeout_sec", None)
    elif name == "static deploy":
        value = getattr(args, "static_timeout_sec", None)
    elif name == "post-deploy verify":
        value = getattr(args, "verify_timeout_sec", None)
    else:
        value = getattr(args, "step_timeout_sec", None)
    try:
        timeout = int(value or 0)
    except (TypeError, ValueError):
        timeout = 0
    return timeout if timeout > 0 else None


def _build_steps(args: argparse.Namespace, *, python: str) -> list[tuple[str, list[str], Path]]:
    steps: list[tuple[str, list[str], Path]] = []

    if not args.skip_gates:
        gate_cmd = [
            python,
            "scripts/release_gate_check.py",
            "--brain-ip",
            args.brain_ip,
            "--web-domain",
            args.web_domain,
            "--ssh-user",
            args.ssh_user,
            "--ssh-port",
            str(args.ssh_port),
            "--passwords",
            args.passwords,
        ]
        if args.quick_gate:
            gate_cmd.append("--quick")
        steps.append(("release gates", gate_cmd, REPO_ROOT))

    release_metadata_file = str(getattr(args, "release_metadata_file", "") or "").strip()
    release_env_file = str(getattr(args, "release_env_file", "") or "").strip()
    if release_metadata_file or release_env_file:
        handoff_cmd = [
            python,
            "scripts/remote_brain_apply_release_handoff.py",
            "--brain-ip",
            args.brain_ip,
        ]
        if release_metadata_file:
            handoff_cmd.extend(["--metadata-file", release_metadata_file])
        if release_env_file:
            handoff_cmd.extend(["--env-file", release_env_file])
        handoff_cmd.extend(
            [
                "--ssh-user",
                args.ssh_user,
                "--ssh-port",
                str(args.ssh_port),
                "--passwords",
                args.passwords,
            ]
        )
        steps.append(("release handoff sync", handoff_cmd, REPO_ROOT))

    if args.ensure_metrics_timer:
        steps.append(
            (
                "metrics timer ensure",
                [
                    python,
                    "scripts/remote_install_node_metrics_timer.py",
                    "--brain-ip",
                    args.brain_ip,
                    "--ssh-user",
                    args.ssh_user,
                    "--ssh-port",
                    str(args.ssh_port),
                    "--passwords",
                    args.passwords,
                ],
                REPO_ROOT,
            )
        )

    for node_code in [str(item or "").strip().lower() for item in (args.ensure_observer_node or []) if str(item or "").strip()]:
        steps.append(
            (
                f"observer timer ensure ({node_code})",
                [
                    python,
                    "scripts/remote_install_node_observer.py",
                    "--brain-ip",
                    args.brain_ip,
                    "--node-code",
                    node_code,
                    "--ssh-user",
                    args.ssh_user,
                    "--ssh-port",
                    str(args.ssh_port),
                    "--passwords",
                    args.passwords,
                ],
                REPO_ROOT,
            )
        )

    if not args.skip_backend:
        steps.append(
            (
                "backend deploy",
                [
                    python,
                    "scripts/remote_deploy_brain_portal_code.py",
                    "--brain-ip",
                    args.brain_ip,
                    "--ssh-user",
                    args.ssh_user,
                    "--ssh-port",
                    str(args.ssh_port),
                    "--passwords",
                    args.passwords,
                    "--restart",
                    ",".join(DEFAULT_BACKEND_RESTART_UNITS),
                ],
                REPO_ROOT,
            )
        )

    if not args.skip_static:
        steps.append(
            (
                "static deploy",
                [
                    python,
                    "scripts/remote_deploy_brain_static_sites.py",
                    "--brain-ip",
                    args.brain_ip,
                    "--ssh-user",
                    args.ssh_user,
                    "--ssh-port",
                    str(args.ssh_port),
                    "--passwords",
                    args.passwords,
                    "--web-domain",
                    args.web_domain,
                    "--api-domain",
                    args.api_domain,
                ],
                REPO_ROOT,
            )
        )

    for node_code in [str(item or "").strip().lower() for item in (getattr(args, "qdisc_node", []) or []) if str(item or "").strip()]:
        base_cmd = _build_qdisc_base_cmd(args, node_code)
        steps.append(
            (
                f"qdisc persistence install ({node_code})",
                [python, "scripts/remote_apply_node_qdisc.py", "install", *base_cmd],
                REPO_ROOT,
            )
        )
        steps.append(
            (
                f"qdisc apply ({node_code})",
                [python, "scripts/remote_apply_node_qdisc.py", "apply", *base_cmd],
                REPO_ROOT,
            )
        )
        steps.append(
            (
                f"qdisc smoke gate ({node_code})",
                [
                    python,
                    "scripts/remote_node_qdisc_smoke.py",
                    *base_cmd,
                    "--probe-url",
                    args.qdisc_probe_url,
                    "--heavy-url",
                    args.qdisc_heavy_url,
                    "--probe-attempts",
                    str(args.qdisc_probe_attempts),
                    "--probe-pause-seconds",
                    str(args.qdisc_probe_pause_seconds),
                    "--heavy-duration-seconds",
                    str(args.qdisc_heavy_duration_seconds),
                    "--min-heavy-bytes",
                    str(args.qdisc_min_heavy_bytes),
                    "--min-probe-successes",
                    str(args.qdisc_min_probe_successes),
                    "--max-probe-connect-p95-seconds",
                    str(args.qdisc_max_probe_connect_p95_seconds),
                    "--max-probe-ttfb-p95-seconds",
                    str(args.qdisc_max_probe_ttfb_p95_seconds),
                    "--max-probe-total-p95-seconds",
                    str(args.qdisc_max_probe_total_p95_seconds),
                ],
                REPO_ROOT,
            )
        )

    if not args.skip_verify:
        steps.append(
            (
                "post-deploy verify",
                [
                    python,
                    "scripts/verify_brain_ready.py",
                    "--brain-ip",
                    args.brain_ip,
                    "--ssh-user",
                    args.ssh_user,
                    "--ssh-port",
                    str(args.ssh_port),
                    "--passwords",
                    args.passwords,
                    "--web-domain",
                    args.web_domain,
                    "--api-domain",
                    args.api_domain,
                    "--repeat",
                    "5",
                ],
                REPO_ROOT,
            )
        )

    return steps


def _has_remote_steps(args: argparse.Namespace, *, release_metadata_file: str, release_env_file: str) -> bool:
    return any(
        (
            not args.skip_backend,
            not args.skip_static,
            not args.skip_verify,
            bool(args.ensure_metrics_timer),
            bool(release_metadata_file),
            bool(release_env_file),
            bool(getattr(args, "ensure_observer_node", [])),
            bool(getattr(args, "qdisc_node", [])),
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="One-command release orchestrator: gates -> deploy -> verify.")
    parser.add_argument("--brain-ip", default="", help="Brain node public IP (required for deploy/verify steps)")
    parser.add_argument("--web-domain", default="pokrov.space")
    parser.add_argument("--api-domain", default="api.pokrov.space")
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"))
    parser.add_argument("--quick-gate", action="store_true", help="Run quick release gates")
    parser.add_argument(
        "--stage",
        choices=("all", "gates", "deploy", "backend", "static", "verify"),
        default="all",
        help="Shortcut for common partial runs: gates, backend, static, deploy (backend+static), or verify.",
    )
    parser.add_argument("--skip-gates", action="store_true")
    parser.add_argument("--skip-backend", action="store_true")
    parser.add_argument("--skip-static", action="store_true")
    parser.add_argument("--skip-verify", action="store_true")
    parser.add_argument("--ensure-metrics-timer", action="store_true", help="Install/repair portal-node-metrics.timer before verify")
    parser.add_argument(
        "--ensure-observer-node",
        action="append",
        default=[],
        help="Install/repair portal-node-observer.timer on the given delivery node code. Can be repeated.",
    )
    parser.add_argument("--gates-only", action="store_true", help="Run gates only (no remote deploy/verify)")
    parser.add_argument("--verify-only", action="store_true", help="Run only post-deploy verify")
    parser.add_argument(
        "--release-metadata-file",
        default="",
        help="Client-owned POKROV-app release-handoff.json path to sync APP_* download URLs onto brain before deploy/verify.",
    )
    parser.add_argument(
        "--release-env-file",
        default="",
        help="Legacy release-links.env path to sync APP_* download URLs onto brain before deploy/verify.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned commands without executing them")
    parser.add_argument("--step-timeout-sec", type=int, default=3600, help="Default timeout for uncategorized steps; 0 disables it")
    parser.add_argument("--gate-timeout-sec", type=int, default=7200, help="Timeout for release gates; 0 disables it")
    parser.add_argument("--backend-timeout-sec", type=int, default=2400, help="Timeout for backend deploy; 0 disables it")
    parser.add_argument("--static-timeout-sec", type=int, default=3600, help="Timeout for static deploy; 0 disables it")
    parser.add_argument("--verify-timeout-sec", type=int, default=900, help="Timeout for post-deploy verify; 0 disables it")
    parser.add_argument("--qdisc-node", action="append", default=[], help="Apply qdisc rollout steps for the given node code. Can be repeated.")
    parser.add_argument(
        "--qdisc-host",
        action="append",
        default=[],
        help="Node-code to host mapping for qdisc rollout, e.g. pl=203.0.113.10. Can be repeated.",
    )
    parser.add_argument("--qdisc-profiles", default=str(REPO_ROOT / "infra" / "node-qdisc-profiles.json"))
    parser.add_argument("--qdisc-probe-url", default="https://1.1.1.1/cdn-cgi/trace")
    parser.add_argument("--qdisc-heavy-url", default="https://speed.cloudflare.com/__down?bytes=50000000")
    parser.add_argument("--qdisc-probe-attempts", type=int, default=8)
    parser.add_argument("--qdisc-probe-pause-seconds", type=float, default=1.0)
    parser.add_argument("--qdisc-heavy-duration-seconds", type=float, default=10.0)
    parser.add_argument("--qdisc-min-heavy-bytes", type=int, default=1048576)
    parser.add_argument("--qdisc-min-probe-successes", type=int, default=3)
    parser.add_argument("--qdisc-max-probe-connect-p95-seconds", type=float, default=1.0)
    parser.add_argument("--qdisc-max-probe-ttfb-p95-seconds", type=float, default=1.0)
    parser.add_argument("--qdisc-max-probe-total-p95-seconds", type=float, default=2.0)
    args = parser.parse_args()
    _apply_stage(args)

    if args.gates_only and args.verify_only:
        raise SystemExit("--gates-only and --verify-only are mutually exclusive")

    if args.verify_only:
        args.skip_gates = True
        args.skip_backend = True
        args.skip_static = True
        args.skip_verify = False
        args.ensure_metrics_timer = False
        args.ensure_observer_node = []
        args.qdisc_node = []
        args.qdisc_host = []

    release_metadata_file = str(args.release_metadata_file or "").strip()
    release_env_file = str(args.release_env_file or "").strip()
    if (release_metadata_file or release_env_file) and args.gates_only:
        raise SystemExit("--release-metadata-file and --release-env-file cannot be used with --gates-only")

    python = sys.executable
    steps: list[tuple[str, list[str], Path]] = []

    if args.gates_only:
        gate_args = copy(args)
        gate_args.skip_backend = True
        gate_args.skip_static = True
        gate_args.skip_verify = True
        gate_args.ensure_metrics_timer = False
        gate_args.ensure_observer_node = []
        gate_args.release_metadata_file = ""
        gate_args.release_env_file = ""
        gate_args.qdisc_node = []
        gate_args.qdisc_host = []
        steps = _build_steps(gate_args, python=python)
        if args.dry_run:
            for name, cmd, cwd in steps:
                _dry_run(name, cmd, cwd)
            print("[done] gates-only dry-run finished")
            return 0
        for name, cmd, cwd in steps:
            rc = _run(name, cmd, cwd, timeout_sec=_step_timeout_sec(args, name))
            if rc != 0:
                return rc
        print("[done] gates-only mode finished")
        return 0

    need_remote = _has_remote_steps(
        args,
        release_metadata_file=release_metadata_file,
        release_env_file=release_env_file,
    )
    if need_remote and not args.brain_ip.strip():
        raise SystemExit("--brain-ip is required for deploy/verify steps")
    steps = _build_steps(args, python=python)

    if args.dry_run:
        for name, cmd, cwd in steps:
            _dry_run(name, cmd, cwd)
        print("[done] dry-run finished")
        return 0

    for name, cmd, cwd in steps:
        rc = _run(name, cmd, cwd, timeout_sec=_step_timeout_sec(args, name))
        if rc != 0:
            for cleanup_name, cleanup_cmd, cleanup_cwd in _build_qdisc_failure_cleanup_steps(args, step_name=name, python=python):
                cleanup_rc = _run(cleanup_name, cleanup_cmd, cleanup_cwd, timeout_sec=_step_timeout_sec(args, cleanup_name))
                if cleanup_rc != 0:
                    print(f"[warn] {cleanup_name} exit={cleanup_rc}")
            return rc

    print("[done] release orchestration completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

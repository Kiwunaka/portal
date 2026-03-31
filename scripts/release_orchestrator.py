from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(name: str, cmd: list[str], cwd: Path = REPO_ROOT) -> int:
    print(f"[step] {name}: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(cwd))
    if proc.returncode != 0:
        print(f"[fail] {name} exit={proc.returncode}")
        return int(proc.returncode)
    print(f"[ok] {name}")
    return 0


def _dry_run(name: str, cmd: list[str], cwd: Path = REPO_ROOT) -> None:
    print(f"[dry-run] {name}: {' '.join(cmd)} (cwd={cwd})")


def main() -> int:
    parser = argparse.ArgumentParser(description="One-command release orchestrator: gates -> deploy -> verify.")
    parser.add_argument("--brain-ip", default="", help="Brain node public IP (required for deploy/verify steps)")
    parser.add_argument("--web-domain", default="pokrov.space")
    parser.add_argument("--api-domain", default="api.pokrov.space")
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"))
    parser.add_argument("--quick-gate", action="store_true", help="Run quick release gates")
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
    parser.add_argument("--dry-run", action="store_true", help="Print planned commands without executing them")
    args = parser.parse_args()

    if args.gates_only and args.verify_only:
        raise SystemExit("--gates-only and --verify-only are mutually exclusive")

    if args.verify_only:
        args.skip_gates = True
        args.skip_backend = True
        args.skip_static = True
        args.skip_verify = False
        args.ensure_metrics_timer = False

    python = sys.executable
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

    if args.gates_only:
        if args.dry_run:
            for name, cmd, cwd in steps:
                _dry_run(name, cmd, cwd)
            print("[done] gates-only dry-run finished")
            return 0
        for name, cmd, cwd in steps:
            rc = _run(name, cmd, cwd)
            if rc != 0:
                return rc
        print("[done] gates-only mode finished")
        return 0

    need_remote = not (args.skip_backend and args.skip_static and args.skip_verify and not args.ensure_metrics_timer)
    if need_remote and not args.brain_ip.strip():
        raise SystemExit("--brain-ip is required for deploy/verify steps")

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
                    "portal-api,portal-bot,portal-helpbot",
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

    if args.dry_run:
        for name, cmd, cwd in steps:
            _dry_run(name, cmd, cwd)
        print("[done] dry-run finished")
        return 0

    for name, cmd, cwd in steps:
        rc = _run(name, cmd, cwd)
        if rc != 0:
            return rc

    print("[done] release orchestration completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

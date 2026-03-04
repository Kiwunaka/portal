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


def main() -> int:
    parser = argparse.ArgumentParser(description="One-command release orchestrator: gates -> deploy -> verify.")
    parser.add_argument("--brain-ip", default="", help="Brain node public IP (required for deploy/verify steps)")
    parser.add_argument("--web-domain", default="portal-privacy.online")
    parser.add_argument("--api-domain", default="kiwunaka.space")
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"))
    parser.add_argument("--quick-gate", action="store_true", help="Run quick release gates")
    parser.add_argument("--skip-gates", action="store_true")
    parser.add_argument("--skip-backend", action="store_true")
    parser.add_argument("--skip-static", action="store_true")
    parser.add_argument("--skip-verify", action="store_true")
    parser.add_argument("--ensure-metrics-timer", action="store_true", help="Install/repair portal-node-metrics.timer before verify")
    parser.add_argument("--gates-only", action="store_true", help="Run gates only (no remote deploy/verify)")
    args = parser.parse_args()

    python = sys.executable

    if not args.skip_gates:
        gate_cmd = [python, "scripts/release_gate_check.py"]
        if args.quick_gate:
            gate_cmd.append("--quick")
        rc = _run("release gates", gate_cmd)
        if rc != 0:
            return rc

    if args.gates_only:
        print("[done] gates-only mode finished")
        return 0

    need_remote = not (args.skip_backend and args.skip_static and args.skip_verify and not args.ensure_metrics_timer)
    if need_remote and not args.brain_ip.strip():
        raise SystemExit("--brain-ip is required for deploy/verify steps")

    if args.ensure_metrics_timer:
        rc = _run(
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
        )
        if rc != 0:
            return rc

    if not args.skip_backend:
        rc = _run(
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
        )
        if rc != 0:
            return rc

    if not args.skip_static:
        rc = _run(
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
        )
        if rc != 0:
            return rc

    if not args.skip_verify:
        rc = _run(
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
        )
        if rc != 0:
            return rc

    print("[done] release orchestration completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

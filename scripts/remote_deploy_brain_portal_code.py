from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
DEFAULT_RESTART_UNITS = (
    "portal-api",
    "portal-bot",
    "portal-helpbot",
    "portal-feedbackbot",
)
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from node_access import connect_node


def _parse_passwords(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    for i, ln in enumerate(lines):
        if "BRAINnode" in ln:
            for j in range(i + 1, min(i + 30, len(lines))):
                v = lines[j].strip()
                if v and not v.startswith("ssh-ed25519 "):
                    return v
    return ""


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def _print_remote_result(label: str, code: int, out: str, err: str) -> None:
    message = (out.strip() or err.strip()).strip()
    if message:
        print(f"{label}: {message}")
    else:
        print(f"{label}: exit={code}")


def _run_checked(ssh: paramiko.SSHClient, cmd: str, *, label: str, timeout: int = 120) -> bool:
    code, out, err = _run(ssh, cmd, timeout=timeout)
    if code == 0:
        return True
    _print_remote_result(label, code, out, err)
    return False


def iter_upload_mappings(repo_root: Path) -> list[tuple[Path, str]]:
    mappings: list[tuple[Path, str]] = []
    for path in sorted((repo_root / "portal_bot").glob("*.py")):
        mappings.append((path, f"/root/portal_bot/{path.name}"))

    requirements = repo_root / "portal_bot" / "requirements.txt"
    if requirements.exists():
        mappings.append((requirements, "/root/portal_bot/requirements.txt"))

    for source_name, target_name in (
        ("collect_node_metrics.py", "collect_node_metrics.py"),
        ("node_dataplane_probe.py", "node_dataplane_probe.py"),
    ):
        source = repo_root / "scripts" / source_name
        if source.exists():
            mappings.append((source, f"/root/portal_bot/{target_name}"))

    for shared_name in (
        "product-facts.json",
        "public-urls.json",
        "design-tokens.json",
        "tariff-catalog.json",
        "access-matrix.json",
        "promo-slots.json",
        "support-ai-knowledge.json",
    ):
        source = repo_root / "shared" / shared_name
        if source.exists():
            mappings.append((source, f"/root/shared/{shared_name}"))

    return mappings


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy portal_bot/*.py to brain and restart portal-api/portal-bot.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument(
        "--restart",
        default=",".join(DEFAULT_RESTART_UNITS),
        help="comma-separated systemd units to restart",
    )
    args = ap.parse_args()

    ssh, auth_method = connect_node(
        code="brain",
        host=args.brain_ip,
        user=args.ssh_user,
        port=args.ssh_port,
        passwords_path=Path(args.passwords),
    )
    try:
        print(f"brain auth: {auth_method}")
        if not _run_checked(ssh, "mkdir -p /root/portal_bot /root/shared", label="prepare remote dirs", timeout=60):
            return 1
        sftp = ssh.open_sftp()
        try:
            for source, target in iter_upload_mappings(REPO_ROOT):
                sftp.put(str(source), target)
        finally:
            sftp.close()

        if not _run_checked(
            ssh,
            (
                "cd /root/portal_bot && "
                "test -x venv/bin/python || python3 -m venv venv && "
                "venv/bin/python -m pip install -r requirements.txt >/tmp/portal_requirements.log 2>&1"
            ),
            label="install portal requirements",
            timeout=1800,
        ):
            return 1

        for unit in [u.strip() for u in args.restart.split(",") if u.strip()]:
            restart_ok = _run_checked(ssh, f"systemctl restart {unit}", label=f"{unit} restart", timeout=60)
            code, out, err = _run(ssh, f"systemctl is-active {unit}", timeout=30)
            status = (out.strip() or err.strip()).strip()
            print(f"{unit}: {status}")
            if not restart_ok or code != 0 or status != "active":
                if code != 0 or status != "active":
                    _print_remote_result(f"{unit} status", code, out, err)
                return 1
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())

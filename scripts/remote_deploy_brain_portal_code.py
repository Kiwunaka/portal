from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy portal_bot/*.py to brain and restart portal-api/portal-bot.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--restart", default="portal-api,portal-bot", help="comma-separated systemd units to restart")
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
        _run(ssh, "mkdir -p /root/portal_bot", timeout=60)
        sftp = ssh.open_sftp()
        try:
            for p in sorted((REPO_ROOT / "portal_bot").glob("*.py")):
                sftp.put(str(p), f"/root/portal_bot/{p.name}")
            requirements = REPO_ROOT / "portal_bot" / "requirements.txt"
            if requirements.exists():
                sftp.put(str(requirements), "/root/portal_bot/requirements.txt")
            collector = REPO_ROOT / "scripts" / "collect_node_metrics.py"
            if collector.exists():
                sftp.put(str(collector), "/root/portal_bot/collect_node_metrics.py")
        finally:
            sftp.close()

        _run(
            ssh,
            (
                "cd /root/portal_bot && "
                "test -x venv/bin/python || python3 -m venv venv && "
                "venv/bin/python -m pip install -r requirements.txt >/tmp/portal_requirements.log 2>&1"
            ),
            timeout=1800,
        )

        for unit in [u.strip() for u in args.restart.split(",") if u.strip()]:
            _run(ssh, f"systemctl restart {unit} >/dev/null 2>&1 || true", timeout=60)
            _, out, err = _run(ssh, f"systemctl is-active {unit} || true", timeout=30)
            print(f"{unit}: {(out.strip() or err.strip()).strip()}")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

"""
Start/stop/status x-ui (3x-ui) on a node via SSH with password/key fallback.

Default target: brain node.
"""

import argparse
import os
import sys
from pathlib import Path

import paramiko

from node_access import connect_node

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 60) -> str:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    return out or err


def _print_safe(text: str) -> None:
    enc = sys.stdout.encoding or "utf-8"
    safe = str(text or "").encode(enc, errors="replace").decode(enc, errors="replace")
    print(safe)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="82.21.114.104")
    ap.add_argument("--code", default="brain")
    ap.add_argument("--action", choices=["status", "start", "restart", "stop"], default="status")
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    args = ap.parse_args()

    ssh, auth_method = connect_node(
        code=args.code,
        host=args.host,
        user=args.ssh_user,
        port=args.ssh_port,
        passwords_path=Path(args.passwords),
    )
    try:
        _print_safe(f"auth_method={auth_method}")
        if args.action in {"start", "restart"}:
            _print_safe(_run(ssh, "systemctl enable x-ui >/dev/null 2>&1 || true", timeout=60))
        _print_safe(_run(ssh, f"systemctl {args.action} x-ui || true", timeout=60))
        _print_safe(_run(ssh, "systemctl is-active x-ui || true", timeout=30))
        if args.action in {"start", "restart"}:
            _print_safe(_run(ssh, "ss -tlnp | grep -E ':(\\d+)' | grep x-ui || true", timeout=30))
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())


from __future__ import annotations

"""
Start/stop/status x-ui (3x-ui) on a node via SSH.

Default target: brain node.
"""

import argparse
import os
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


def _parse_passwords(path: Path) -> dict[str, str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    out: dict[str, str] = {}
    markers = {"brain": "BRAINnode", "us": "USnode", "pl": "PLnode", "it": "ITnode", "free": "Free Node"}
    for code, marker in markers.items():
        try:
            idx = next(i for i, ln in enumerate(lines) if marker in ln)
        except StopIteration:
            continue
        pw = ""
        for j in range(idx + 1, min(idx + 12, len(lines))):
            ln = lines[j]
            if not ln or ln.startswith("ssh-ed25519 "):
                continue
            pw = ln
            break
        if pw:
            out[code] = pw
    return out


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 60) -> str:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    return out or err


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="82.21.114.104")
    ap.add_argument("--code", default="brain")
    ap.add_argument("--action", choices=["status", "start", "restart", "stop"], default="status")
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    args = ap.parse_args()

    pw = os.getenv(f"NODE_PASS_{args.code.upper()}", "").strip() or _parse_passwords(Path(args.passwords)).get(args.code, "")
    if not pw:
        raise SystemExit(f"Missing password for {args.code}")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(args.host, port=args.ssh_port, username=args.ssh_user, password=pw, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        if args.action in {"start", "restart"}:
            print(_run(ssh, "systemctl enable x-ui >/dev/null 2>&1 || true", timeout=60))
        print(_run(ssh, f"systemctl {args.action} x-ui || true", timeout=60))
        print(_run(ssh, "systemctl is-active x-ui || true", timeout=30))
        if args.action in {"start", "restart"}:
            print(_run(ssh, "ss -tlnp | grep -E ':(\\d+)' | grep x-ui || true", timeout=30))
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())


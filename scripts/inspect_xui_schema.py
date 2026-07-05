from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy

from node_passwords import parse_passwords


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 60) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True, help="node ip")
    ap.add_argument("--code", default="", help="node code (used only for NODE_PASS_CODE env)")
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    args = ap.parse_args()

    pw = ""
    if args.code:
        pw = os.getenv(f"NODE_PASS_{args.code.upper()}", "").strip()
    if not pw:
        wanted = [args.code] if args.code else []
        pw_map = parse_passwords(Path(args.passwords), requested_codes=wanted)
        pw = pw_map.get(args.code, "") if args.code else ""
    if not pw:
        raise SystemExit("Password not found. Set NODE_PASS_<CODE> env var.")

    ssh = paramiko.SSHClient()
    configure_ssh_host_key_policy(ssh)
    ssh.connect(args.host, port=args.ssh_port, username=args.ssh_user, password=pw, timeout=30)
    try:
        for q in [
            "sqlite3 /etc/x-ui/x-ui.db \"pragma table_info(inbounds);\"",
            "sqlite3 /etc/x-ui/x-ui.db \"pragma table_info(settings);\" 2>/dev/null || true",
            "sqlite3 /etc/x-ui/x-ui.db \"select id, port, protocol, remark, enable from inbounds order by id;\" 2>/dev/null || true",
        ]:
            code, out, err = _run(ssh, q, timeout=30)
            print(f"== {q} ==")
            print((out or err).strip())
            print()
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())

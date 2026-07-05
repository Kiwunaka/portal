from __future__ import annotations

"""
Grant expiry for all users on a REMOTE server (portal.db).

This updates only the SQLite DB; it does not restart services.

Env:
- SSH_HOST
- SSH_PASS
Optional:
- SSH_PORT (default 29374)
- SSH_USER (default root)
- REMOTE_PORTAL_DB (default /root/portal_bot/portal.db)
"""

import argparse
import os
from datetime import datetime, timedelta, timezone

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy


def _require(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise SystemExit(f"Missing required env var: {name}")
    return v


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    args = ap.parse_args()

    host = _require("SSH_HOST")
    password = _require("SSH_PASS")
    port = int(os.getenv("SSH_PORT", "29374"))
    user = os.getenv("SSH_USER", "root")

    remote_db = os.getenv("REMOTE_PORTAL_DB", "/root/portal_bot/portal.db")

    expiry = datetime.now(timezone.utc) + timedelta(days=int(args.days))
    expiry_str = expiry.replace(tzinfo=None).isoformat(sep=" ", timespec="seconds")

    ssh = paramiko.SSHClient()
    configure_ssh_host_key_policy(ssh)
    ssh.connect(host, port=port, username=user, password=password, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        # Ensure sqlite3 exists
        _run(ssh, "command -v sqlite3 >/dev/null 2>&1 || (apt-get update -y && apt-get install -y sqlite3)", timeout=900)

        cmd = (
            f"sqlite3 {remote_db} "
            f"\"update users set is_active=1, expiry_at='{expiry_str}';"
            f"select 'users_total=' || count(*) from users;\""
        )
        code, out, err = _run(ssh, cmd, timeout=120)
        if code != 0:
            raise SystemExit(err.strip() or out.strip())
        print(out.strip())
        print(f"expiry_at_utc={expiry_str}")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())


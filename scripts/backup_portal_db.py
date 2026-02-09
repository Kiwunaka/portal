from __future__ import annotations

"""
Backup control-plane SQLite DB from a remote server via SSH.

This is designed to be safe for a running production server:
- Uses SQLite `.backup` to produce a consistent snapshot.
- Writes temporary file under /tmp by default, then downloads it via SFTP.
- Optionally cleans up the temp file.

Environment (required):
- SSH_HOST
- SSH_PASS

Environment (optional):
- SSH_PORT (default 22)
- SSH_USER (default root)
- REMOTE_PORTAL_DB (default /root/portal_bot/portal.db)
"""

import argparse
import os
import time
from pathlib import Path

import paramiko


def _require(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise SystemExit(f"Missing required env var: {name}")
    return v


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 60) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def main() -> int:
    p = argparse.ArgumentParser(description="Backup /root/portal_bot/portal.db from a remote server")
    p.add_argument("--out", default="", help="local output path (default: portal.db.from-old-<timestamp>.db)")
    p.add_argument("--remote-tmp", default="/tmp/portal.db", help="remote tmp path to write the snapshot")
    p.add_argument("--no-cleanup", action="store_true", help="do not delete remote tmp file after download")
    args = p.parse_args()

    host = _require("SSH_HOST")
    password = _require("SSH_PASS")
    port = int(os.getenv("SSH_PORT", "22"))
    user = os.getenv("SSH_USER", "root")

    remote_db = os.getenv("REMOTE_PORTAL_DB", "/root/portal_bot/portal.db")
    remote_tmp = args.remote_tmp

    out_path = Path(args.out) if args.out else Path(f"portal.db.from-old-{time.strftime('%Y%m%d-%H%M%S')}.db")
    out_path = out_path.resolve()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        # Consistent snapshot. Does not stop services.
        cmd = f"sqlite3 {remote_db} \".backup '{remote_tmp}'\""
        code, out, err = _run(ssh, cmd, timeout=120)
        if code != 0:
            raise SystemExit(f"Remote sqlite backup failed (exit={code}): {err or out}")

        sftp = ssh.open_sftp()
        try:
            sftp.get(remote_tmp, str(out_path))
        finally:
            sftp.close()

        if not args.no_cleanup:
            _run(ssh, f"rm -f {remote_tmp}", timeout=30)

        print(f"OK: saved {out_path}")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())


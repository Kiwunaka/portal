from __future__ import annotations

"""
Inspect what hostnames current users connect to (OLD server subscription output).

This is important before moving the root domain DNS:
- If users' VLESS links use kiwunaka.space:443, moving A-record will break those connections.
- If links already use IPs or other subdomains, moving kiwunaka.space for API/WebApp is safer.

This script:
- SSH into old server
- picks 1 active user with sub_token
- fetches subscription from localhost API (no DNS)
- decodes base64 list and prints only unique hosts/ports (no token, no UUIDs)
"""

import os
import re

import paramiko


def _require_env(name: str) -> str:
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
    host = _require_env("OLD_SSH_HOST")
    password = _require_env("OLD_SSH_PASS")
    port = int(os.getenv("OLD_SSH_PORT", "29374"))
    user = os.getenv("OLD_SSH_USER", "root")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        cmd = r"""#!/usr/bin/env bash
set -euo pipefail

DB="/root/portal_bot/portal.db"
TOK="$(python3 -c "import sqlite3;con=sqlite3.connect('/root/portal_bot/portal.db');cur=con.cursor();row=cur.execute(\"select sub_token from users where is_active=1 and sub_token is not null limit 1\").fetchone();print(row[0] if row else '')")"
if [ -z "$TOK" ]; then
  echo "no_active_token"
  exit 2
fi

# Fetch subscription from localhost. We don't care about SNI here; --insecure.
RAW="$(curl -fsS --insecure https://127.0.0.1:2096/s8Kx2mP7qR4wT/$TOK)"

cat >/tmp/inspect_sub_hosts.py <<'PY'
import base64
import re
import sys

raw = sys.stdin.read().strip()
try:
    dec = base64.b64decode(raw).decode("utf-8", "replace")
except Exception:
    dec = raw

lines = [l.strip() for l in dec.splitlines() if l.strip()]
hosts = set()
ports = set()
schemes = set()
has_at = 0

for l in lines:
    m = re.match(r"^([a-zA-Z0-9+.-]+)://", l)
    if m:
        schemes.add(m.group(1).lower())
    if "@" in l:
        has_at += 1
    m2 = re.search(r"@([^:/?#]+):(\d+)", l)
    if m2:
        hosts.add(m2.group(1))
        ports.add(m2.group(2))

print("schemes=" + ",".join(sorted(schemes)))
print("has_at=" + str(has_at))
print("hosts=" + ",".join(sorted(hosts)))
print("ports=" + ",".join(sorted(ports)))
print("lines=" + str(len(lines)))
PY
python3 /tmp/inspect_sub_hosts.py <<< "$RAW"
rm -f /tmp/inspect_sub_hosts.py
"""

        sftp = ssh.open_sftp()
        try:
            remote = "/tmp/inspect_sub_hosts.sh"
            with sftp.file(remote, "w") as f:
                f.write(cmd)
            sftp.chmod(remote, 0o700)
        finally:
            sftp.close()

        code, out, err = _run(ssh, "bash /tmp/inspect_sub_hosts.sh", timeout=120)
        _run(ssh, "rm -f /tmp/inspect_sub_hosts.sh", timeout=30)

        txt = (out.strip() or err.strip()).strip()
        # Sanity: never leak tokens even if remote echoed something unexpected.
        txt = re.sub(r"[A-Za-z0-9_-]{20,}", "<redacted>", txt)
        print(txt)
        return 0 if code == 0 else 2
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())

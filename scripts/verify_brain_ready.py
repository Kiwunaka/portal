from __future__ import annotations

"""
Verify brain node is ready to take over the public domain (pre-DNS switch).

Checks:
- systemd: caddy + portal-api active, portal-bot disabled/stopped
- HTTP(S): /api/health on :2096, WebApp on /webapp/, marketing on /
- Subscription endpoint returns multiple locations and is stable across repeated requests

No secrets printed:
- does not print subscription tokens, UUIDs, or raw subscription content
"""

import argparse
import os
import re
import time
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


def _parse_passwords(path: Path) -> dict[str, str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    out: dict[str, str] = {}
    markers = {"brain": "BRAINnode", "us": "USnode", "pl": "PLnode", "it": "ITnode", "nl": "NLnode", "free": "Free Node"}
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


def _ssh_connect(ip: str, *, user: str, port: int, password: str) -> paramiko.SSHClient:
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(ip, port=port, username=user, password=password, timeout=30, banner_timeout=30, auth_timeout=30)
    t = cli.get_transport()
    if t:
        t.set_keepalive(30)
    return cli


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True)
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--repeat", type=int, default=5, help="repeat subscription fetch N times")
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords)).get("brain", "")
    if not pw:
        raise SystemExit("Missing brain password (set NODE_PASS_BRAIN or add to PASSWORDS.txt).")

    ssh = _ssh_connect(args.brain_ip, user=args.ssh_user, port=args.ssh_port, password=pw)
    try:
        checks = [
            ("caddy", "systemctl is-active caddy || true"),
            ("portal-api", "systemctl is-active portal-api || true"),
            ("portal-bot enabled?", "systemctl is-enabled portal-bot 2>/dev/null || echo disabled"),
            ("listen", "ss -tlnp | grep -E ':(443|8444|2096)\\b' || true"),
        ]
        for name, cmd in checks:
            code, out, err = _run(ssh, cmd, timeout=60)
            val = (out.strip() or err.strip()).strip()
            print(f"[{name}] {val}")

        # HTTP checks via resolve to loopback so DNS isn't needed.
        curl_checks = [
            ("health2096", f"curl -fsS --insecure --resolve {args.domain}:2096:127.0.0.1 https://{args.domain}:2096/api/health"),
            ("webapp443", f"curl -fsS --insecure --resolve {args.domain}:443:127.0.0.1 https://{args.domain}/webapp/ >/dev/null && echo ok"),
            ("mkt443", f"curl -fsS --insecure --resolve {args.domain}:443:127.0.0.1 https://{args.domain}/ >/dev/null && echo ok"),
            ("webapp8444", f"curl -fsS --insecure --resolve {args.domain}:8444:127.0.0.1 https://{args.domain}:8444/webapp/ >/dev/null && echo ok"),
        ]
        for name, cmd in curl_checks:
            code, out, err = _run(ssh, cmd, timeout=30)
            val = (out.strip() or err.strip()).strip()
            print(f"[{name}] {val}")

        # Subscription stability: pick one active user token from DB on brain (do not print).
        # We decode base64 and only print line count + unique host count.
        sub_check = f"""#!/usr/bin/env bash
set -euo pipefail

TOK="$(python3 -c "import sqlite3;db='/root/portal_bot/portal.db';con=sqlite3.connect(db);cur=con.cursor();row=cur.execute(\\"select sub_token from users where is_active=1 and sub_token is not null order by created_at asc limit 1\\").fetchone();print(row[0] if row else '')")"
if [ -z "$TOK" ]; then
  echo "no_active_token"
  exit 2
fi

for i in $(seq 1 {int(args.repeat)}); do
  RAW="$(curl -fsS --insecure --resolve {args.domain}:2096:127.0.0.1 https://{args.domain}:2096/s8Kx2mP7qR4wT/$TOK)"
  DECODED="$(python3 -c "import base64,sys;print(base64.b64decode(sys.stdin.read().strip()).decode('utf-8','replace'))" <<< "$RAW")"
  LINES="$(python3 -c "import sys;print(len([l for l in sys.stdin.read().splitlines() if l.strip()]))" <<< "$DECODED")"
  HOSTS="$(python3 -c "import re,sys;hosts=set();\nfor l in sys.stdin.read().splitlines():\n m=re.search(r'@([^:]+):',l);\n if m: hosts.add(m.group(1));\nprint(len(hosts))" <<< "$DECODED")"
  echo "sub_fetch_$i lines=$LINES hosts=$HOSTS"
  sleep 0.4
done
"""
        sftp = ssh.open_sftp()
        try:
            remote = "/tmp/verify_subscriptions.sh"
            with sftp.file(remote, "w") as f:
                f.write(sub_check)
            sftp.chmod(remote, 0o700)
        finally:
            sftp.close()

        code, out, err = _run(ssh, "bash /tmp/verify_subscriptions.sh", timeout=180)
        _run(ssh, "rm -f /tmp/verify_subscriptions.sh", timeout=30)
        print((out.strip() or err.strip()).strip())
        return 0 if code == 0 else 2
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


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
    ap = argparse.ArgumentParser(description="Print subscription hosts from brain without leaking tokens.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--domain", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--db", default="/root/portal_bot/portal.db")
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    ssh = paramiko.SSHClient()
    configure_ssh_host_key_policy(ssh)
    ssh.connect(args.brain_ip, port=args.ssh_port, username=args.ssh_user, password=pw, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        # Fetch a token locally on the brain, then curl subscription via localhost resolve.
        cmd = f"""
set -e
TOK="$(sqlite3 {args.db} "select sub_token from users where is_active=1 and sub_token is not null order by created_at asc limit 1;")"
if [ -z "$TOK" ]; then
  echo "NO_TOKEN"
  exit 0
fi
RAW="$(curl -fsS --insecure --resolve {args.domain}:2096:127.0.0.1 https://{args.domain}:2096/s8Kx2mP7qR4wT/$TOK)"
echo "TOKLEN=${{#TOK}}"
echo "RAWLEN=${{#RAW}}"
DECODED="$(printf \"%s\" \"$RAW\" | base64 -d 2>/dev/null || true)"
printf "%s" "$DECODED" | awk -F'@' 'NF>1{{print $2}}' | cut -d':' -f1 | cut -d'?' -f1 | sort -u
""".strip()

        code, out, err = _run(ssh, cmd, timeout=60)
        if code != 0:
            raise SystemExit(err.strip() or out.strip() or "remote subscription host inspection failed")
        text = (out.strip() or err.strip()).strip()
        print(text)
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())

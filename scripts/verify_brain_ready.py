from __future__ import annotations

"""
Verify brain node is ready to serve production traffic.

Checks:
- systemd status and listeners
- HTTPS endpoints via localhost resolve on 443 (no DNS switch required)
- subscription endpoint stability across repeated requests (token not printed)
"""

import argparse
import os
import re
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


def _print_result(name: str, out: str, err: str) -> None:
    val = (out.strip() or err.strip()).strip().replace("\ufeff", "")
    print(f"[{name}] {val}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--web-domain", default="portal-privacy.online", help="Public web domain for / and /webapp checks")
    ap.add_argument("--api-domain", default="kiwunaka.space", help="Public API domain for /api/health and subscription checks")
    ap.add_argument("--domain", default="", help="Deprecated alias for --web-domain")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--repeat", type=int, default=5, help="repeat subscription fetch N times")
    ap.add_argument("--check-legacy-2096", action="store_true", help="also verify legacy :2096 endpoint (optional)")
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords)).get("brain", "")
    if not pw:
        raise SystemExit("Missing brain password (set NODE_PASS_BRAIN or add to PASSWORDS.txt).")

    web_domain = (args.domain or "").strip() or (args.web_domain or "").strip()
    api_domain = (args.api_domain or "").strip()
    if not web_domain:
        raise SystemExit("Missing --web-domain")
    if not api_domain:
        raise SystemExit("Missing --api-domain")

    ssh = _ssh_connect(args.brain_ip, user=args.ssh_user, port=args.ssh_port, password=pw)
    try:
        checks = [
            ("caddy", "systemctl is-active caddy || true"),
            ("portal-api", "systemctl is-active portal-api || true"),
            ("portal-bot", "systemctl is-active portal-bot || true"),
            ("portal-helpbot", "systemctl is-active portal-helpbot || true"),
            ("listen", "ss -tlnp | grep -E ':(443|2096|8444)\\b' || true"),
        ]
        for name, cmd in checks:
            code, out, err = _run(ssh, cmd, timeout=60)
            _print_result(name, out, err)

        curl_checks = [
            ("health443", f"curl -fsS --insecure --resolve {api_domain}:443:127.0.0.1 https://{api_domain}/api/health"),
            ("webapp443", f"curl -fsS --insecure --resolve {web_domain}:443:127.0.0.1 https://{web_domain}/webapp/ >/dev/null && echo ok"),
            ("mkt443", f"curl -fsS --insecure --resolve {web_domain}:443:127.0.0.1 https://{web_domain}/ >/dev/null && echo ok"),
            ("fkverify443", f"curl -fsS --insecure --resolve {web_domain}:443:127.0.0.1 https://{web_domain}/fk-verify.html >/dev/null && echo ok"),
        ]
        if args.check_legacy_2096:
            curl_checks.append(
                ("health2096", f"curl -fsS --insecure --resolve {api_domain}:2096:127.0.0.1 https://{api_domain}:2096/api/health"),
            )

        for name, cmd in curl_checks:
            code, out, err = _run(ssh, cmd, timeout=30)
            _print_result(name, out, err)

        sub_check = f"""#!/usr/bin/env bash
set -euo pipefail

CANDIDATES="$(python3 -c "import sqlite3;db='/root/portal_bot/portal.db';con=sqlite3.connect(db);cur=con.cursor();rows=cur.execute(\\"select tg_id,sub_token from users where is_active=1 and sub_token is not null and sub_token<>'' order by created_at asc limit 25\\").fetchall();print('\\\\n'.join(f'{{r[0]}}|{{r[1]}}' for r in rows))")"
if [ -z "${{CANDIDATES:-}}" ]; then
  echo "no_active_tokens"
  exit 2
fi

SEL_TG=""
SEL_TOK=""
while IFS='|' read -r TRY_TG TRY_TOK; do
  [ -z "${{TRY_TG:-}}" ] && continue
  [ -z "${{TRY_TOK:-}}" ] && continue
  RAW="$(curl -fsS --insecure --resolve {api_domain}:443:127.0.0.1 https://{api_domain}/s8Kx2mP7qR4wT/$TRY_TOK 2>/dev/null || true)"
  if [ -n "$RAW" ]; then
    SEL_TG="$TRY_TG"
    SEL_TOK="$TRY_TOK"
    break
  fi
  RAW="$(curl -fsS --insecure --resolve {api_domain}:443:127.0.0.1 https://{api_domain}/s8Kx2mP7qR4wT/$TRY_TG 2>/dev/null || true)"
  if [ -n "$RAW" ]; then
    SEL_TG="$TRY_TG"
    SEL_TOK="$TRY_TOK"
    break
  fi
done <<< "$CANDIDATES"

if [ -z "${{SEL_TG:-}}" ]; then
  echo "no_resolvable_subscription_user"
  exit 2
fi

for i in $(seq 1 {int(args.repeat)}); do
  MODE="token"
  RAW="$(curl -fsS --insecure --resolve {api_domain}:443:127.0.0.1 https://{api_domain}/s8Kx2mP7qR4wT/$SEL_TOK 2>/dev/null || true)"
  if [ -z "$RAW" ]; then
    MODE="tg_id_fallback"
    RAW="$(curl -fsS --insecure --resolve {api_domain}:443:127.0.0.1 https://{api_domain}/s8Kx2mP7qR4wT/$SEL_TG 2>/dev/null || true)"
  fi
  if [ -z "$RAW" ]; then
    echo "sub_fetch_$i tg_id=$SEL_TG mode=failed"
    exit 2
  fi
  METRICS="$(python3 - <<'PY'
import base64
import re
import sys

raw = sys.stdin.read().strip()
text = raw
fmt = "plain"
if raw:
    try:
        cand = base64.b64decode(raw + ("=" * (-len(raw) % 4)), validate=False).decode("utf-8", "replace")
        if "vless://" in cand or "\n" in cand:
            text = cand
            fmt = "base64"
    except Exception:
        pass

lines = [ln for ln in text.splitlines() if ln.strip()]
hosts = set()
for ln in lines:
    m = re.search(r'@([^:]+):', ln)
    if m:
        hosts.add(m.group(1))
print(f"fmt={{fmt}} lines={{len(lines)}} hosts={{len(hosts)}}")
PY
<<< "$RAW")"
  echo "sub_fetch_$i tg_id=$SEL_TG mode=$MODE $METRICS"
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

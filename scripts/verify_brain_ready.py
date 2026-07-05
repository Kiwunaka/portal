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
import shlex
from pathlib import Path

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
DEFAULT_REQUIRED_UNITS = (
    "caddy",
    "portal-api",
    "portal-bot",
    "portal-helpbot",
    "portal-feedbackbot",
)
DEFAULT_REQUIRED_LISTENER_PORTS = (443, 8444)


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
    configure_ssh_host_key_policy(cli)
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


def _listener_probe_cmd(ports: tuple[int, ...]) -> str:
    port_list = ", ".join(str(int(port)) for port in ports)
    script = f"""python3 - <<'PY'
import re
import subprocess

ports = [{port_list}]
text = subprocess.run(["ss", "-tlnp"], check=False, capture_output=True, text=True).stdout
for line in text.splitlines():
    if any(re.search(rf":{{port}}\\b", line) for port in ports):
        print(line)
PY"""
    return "bash -lc " + shlex.quote(script)


def _listener_missing_ports(output: str, ports: tuple[int, ...]) -> list[int]:
    text = str(output or "")
    missing: list[int] = []
    for port in ports:
        if not re.search(rf":{int(port)}\b", text):
            missing.append(int(port))
    return missing


def _curl_retry(
    url: str,
    *,
    host: str,
    contains: str | None = None,
    contains_any: tuple[str, ...] | list[str] | None = None,
    attempts: int = 12,
    pause_sec: float = 1.0,
) -> str:
    markers = [item for item in ([contains] if contains else []) + list(contains_any or []) if str(item or "").strip()]
    target_url = str(url or "").strip()
    if not target_url.startswith(("http://", "https://")):
        target_url = f"https://{target_url}"
    base = " ".join(
        [
            "curl",
            "-fsS",
            "--insecure",
            "--resolve",
            shlex.quote(f"{host}:443:127.0.0.1"),
            shlex.quote(target_url),
        ]
    )
    body_file = "/tmp/portal_verify_body.$$"
    marker_check = "true"
    if markers:
        marker_check = "( " + " || ".join(f"grep -F -- {shlex.quote(marker)} \"$body_file\" >/dev/null" for marker in markers) + " )"
    script = (
        f"body_file={shlex.quote(body_file)}; "
        "cleanup() { rm -f \"$body_file\"; }; "
        "trap cleanup EXIT; "
        f"for i in $(seq 1 {int(attempts)}); do "
        f"if {base} > \"$body_file\"; then "
        f"if {marker_check}; then "
        "head -c 200 \"$body_file\"; "
        "exit 0; "
        "fi; "
        f"fi; sleep {pause_sec}; "
        "done; "
        f"{base} > \"$body_file\" 2>/dev/null || true; "
        "head -c 200 \"$body_file\"; "
        "exit 22"
    )
    return "bash -lc " + shlex.quote(script)


def _cache_header_retry(
    url: str,
    *,
    host: str,
    expected: tuple[str, ...] = ("no-cache", "must-revalidate"),
    attempts: int = 6,
    pause_sec: float = 1.0,
) -> str:
    target_url = str(url or "").strip()
    if not target_url.startswith(("http://", "https://")):
        target_url = f"https://{target_url}"
    base = " ".join(
        [
            "curl",
            "-fsSI",
            "--insecure",
            "--resolve",
            shlex.quote(f"{host}:443:127.0.0.1"),
            shlex.quote(target_url),
        ]
    )
    expected_checks = " && ".join(
        f"printf '%s' \"$value\" | tr '[:upper:]' '[:lower:]' | grep -F -- {shlex.quote(item.lower())} >/dev/null"
        for item in expected
    )
    script = (
        "headers_file=/tmp/portal_verify_headers.$$; "
        "cleanup() { rm -f \"$headers_file\"; }; "
        "trap cleanup EXIT; "
        f"for i in $(seq 1 {int(attempts)}); do "
        f"if {base} > \"$headers_file\"; then "
        "value=$(awk 'BEGIN{IGNORECASE=1} /^cache-control:/ {sub(/^[^:]*:[[:space:]]*/, \"\"); gsub(/\\r/, \"\"); print; exit}' \"$headers_file\"); "
        f"if [ -n \"$value\" ] && {expected_checks}; then "
        "printf 'Cache-Control: %s\\n' \"$value\"; "
        "exit 0; "
        "fi; "
        f"fi; sleep {pause_sec}; "
        "done; "
        "awk 'BEGIN{IGNORECASE=1} /^cache-control:/ {gsub(/\\r/, \"\"); print; found=1} END{if(!found) print \"Cache-Control: <missing>\"}' \"$headers_file\"; "
        "exit 22"
    )
    return "bash -lc " + shlex.quote(script)


def _build_subscription_check_script(*, api_domain: str, connect_domain: str, repeat: int) -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail

CANDIDATES="$(runuser -u postgres -- psql -d portal -tAc \"select tg_id||'|'||sub_token from users where is_active=true and sub_token is not null and sub_token<>'' order by created_at asc limit 25\" 2>/dev/null | sed '/^\\s*$/d' || true)"
if [ -z "${{CANDIDATES:-}}" ]; then
  CANDIDATES="$(python3 -c "import sqlite3;db='/root/portal_bot/portal.db';con=sqlite3.connect(db);cur=con.cursor();rows=cur.execute(\\"select tg_id,sub_token from users where is_active=1 and sub_token is not null and sub_token<>'' order by created_at asc limit 25\\").fetchall();print('\\\\n'.join(f'{{r[0]}}|{{r[1]}}' for r in rows))" 2>/dev/null || true)"
fi
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

for i in $(seq 1 {int(repeat)}); do
  MODE="token"
  RAW="$(curl -fsS --insecure --resolve {api_domain}:443:127.0.0.1 https://{api_domain}/s8Kx2mP7qR4wT/$SEL_TOK 2>/dev/null || true)"
  if [ -z "$RAW" ]; then
    MODE="tg_id_fallback"
    RAW="$(curl -fsS --insecure --resolve {api_domain}:443:127.0.0.1 https://{api_domain}/s8Kx2mP7qR4wT/$SEL_TG 2>/dev/null || true)"
  fi
  if [ -z "$RAW" ]; then
    echo "sub_fetch_$i user=selected mode=failed"
    exit 2
  fi
  RAW_CONNECT="$(curl -fsS --insecure --resolve {connect_domain}:443:127.0.0.1 https://{connect_domain}/s8Kx2mP7qR4wT/$SEL_TOK 2>/dev/null || true)"
  if [ -z "$RAW_CONNECT" ]; then
    echo "sub_fetch_$i user=selected connect=failed"
    exit 2
  fi
  METRICS="$(RAW_PAYLOAD="$RAW" python3 - <<'PY'
import base64
import re
import sys
import os

raw = os.environ.get("RAW_PAYLOAD", "").strip()
text = raw
fmt = "plain"
if raw:
    try:
        cand = base64.b64decode(raw + ("=" * (-len(raw) % 4)), validate=False).decode("utf-8", "replace")
        if "vless://" in cand or "\\n" in cand:
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
)"
  CONNECT_METRICS="$(RAW_CONNECT_PAYLOAD="$RAW_CONNECT" python3 - <<'PY'
import json
import sys
import os

raw = os.environ.get("RAW_CONNECT_PAYLOAD", "").strip()
payload = json.loads(raw)
if not isinstance(payload, dict) or "outbounds" not in payload:
    raise SystemExit(2)
print(f"connect_json=1 outbounds={{len(payload.get('outbounds') or [])}}")
PY
)"
  echo "sub_fetch_$i user=selected mode=$MODE $METRICS $CONNECT_METRICS"
  sleep 0.4
done
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--web-domain", default="pokrov.space", help="Public web domain for / and /webapp checks")
    ap.add_argument("--api-domain", default="api.pokrov.space", help="Public API domain for /api/health and subscription checks")
    ap.add_argument("--connect-domain", default="connect.pokrov.space", help="Canonical connect host for smart subscription checks")
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
    connect_domain = (args.connect_domain or "").strip()
    if not web_domain:
        raise SystemExit("Missing --web-domain")
    if not api_domain:
        raise SystemExit("Missing --api-domain")
    if not connect_domain:
        raise SystemExit("Missing --connect-domain")

    ssh = _ssh_connect(args.brain_ip, user=args.ssh_user, port=args.ssh_port, password=pw)
    try:
        failures: list[str] = []
        for unit in DEFAULT_REQUIRED_UNITS:
            name = unit
            cmd = f"systemctl is-active {unit}"
            code, out, err = _run(ssh, cmd, timeout=60)
            _print_result(name, out, err)
            if code != 0 or (out.strip() or err.strip()).strip() != "active":
                failures.append(f"{unit} is not active")

        required_listener_ports = list(DEFAULT_REQUIRED_LISTENER_PORTS)
        if args.check_legacy_2096:
            required_listener_ports.append(2096)
        listen_cmd = _listener_probe_cmd(tuple(required_listener_ports))
        code, out, err = _run(ssh, listen_cmd, timeout=60)
        _print_result("listen", out, err)
        missing_ports = _listener_missing_ports(out or err, tuple(required_listener_ports))
        if code != 0 or missing_ports:
            failures.append(
                "missing listeners: " + ", ".join(str(port) for port in missing_ports)
                if missing_ports
                else "listener probe failed"
            )

        curl_checks = [
            ("health443", _curl_retry(f"{api_domain}/api/health", host=api_domain)),
            ("webapp443", _curl_retry("app.pokrov.space/", host="app.pokrov.space")),
            ("webappCache443", _cache_header_retry("app.pokrov.space/", host="app.pokrov.space")),
            ("webappDashboardCache443", _cache_header_retry("app.pokrov.space/dashboard", host="app.pokrov.space")),
            ("webappAdminCache443", _cache_header_retry("app.pokrov.space/admin", host="app.pokrov.space")),
            ("mkt443", _curl_retry(f"{web_domain}/", host=web_domain, contains_any=("Android + Windows", "POKROV"))),
            ("mktCache443", _cache_header_retry(f"{web_domain}/", host=web_domain)),
            (
                "mktCabinet443",
                _curl_retry(f"{web_domain}/", host=web_domain, contains_any=("https://app.pokrov.space", "app.pokrov.space")),
            ),
            ("offer443", _curl_retry(f"{web_domain}/offer/", host=web_domain, contains_any=("https://pokrov.space/offer/", "POKROV"))),
            (
                "checkout443",
                _curl_retry(
                    "pay.pokrov.space/checkout/",
                    host="pay.pokrov.space",
                    contains_any=("checkout-shell", "ключ доступа", "https://pokrov.space/checkout/"),
                ),
            ),
            ("checkoutCache443", _cache_header_retry("pay.pokrov.space/checkout/", host="pay.pokrov.space")),
            ("fkverify443", _curl_retry(f"{web_domain}/fk-verify.html", host=web_domain)),
        ]
        if args.check_legacy_2096:
            curl_checks.append(
                ("health2096", f"curl -fsS --insecure --resolve {api_domain}:2096:127.0.0.1 https://{api_domain}:2096/api/health"),
            )

        for name, cmd in curl_checks:
            code, out, err = _run(ssh, cmd, timeout=30)
            _print_result(name, out, err)
            if code != 0:
                failures.append(f"{name} probe failed")

        sub_check = _build_subscription_check_script(
            api_domain=api_domain,
            connect_domain=connect_domain,
            repeat=args.repeat,
        )
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
        if code != 0:
            failures.append("subscription stability probe failed")

        if failures:
            print("[summary] verify failed:")
            for item in failures:
                print(f" - {item}")
            return 2
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())

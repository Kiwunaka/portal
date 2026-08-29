"""
Verify brain node is ready to serve production traffic.

Checks:
- systemd status and listeners
- HTTPS endpoints via localhost resolve on 443 (no DNS switch required)
- subscription endpoint stability across repeated requests (token not printed)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import paramiko
from ssh_host_keys import OpenSshConfigSession, configure_ssh_host_key_policy


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
DEFAULT_REQUIRED_UNITS = (
    "caddy",
    "portal-api",
    "portal-bot",
    "portal-helpbot",
    "portal-feedbackbot",
    "portal-worker",
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


def _run(ssh: paramiko.SSHClient | OpenSshConfigSession, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    if isinstance(ssh, OpenSshConfigSession):
        result = ssh.run(cmd, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def _run_subscription_script(
    ssh: paramiko.SSHClient | OpenSshConfigSession,
    script: str,
) -> tuple[int, str, str]:
    if isinstance(ssh, OpenSshConfigSession):
        result = ssh.run("bash -s", timeout=180, input_text=script)
        return result.returncode, result.stdout, result.stderr

    sftp = ssh.open_sftp()
    try:
        remote = "/tmp/verify_subscriptions.sh"
        with sftp.file(remote, "w") as remote_file:
            remote_file.write(script)
        sftp.chmod(remote, 0o700)
    finally:
        sftp.close()

    try:
        return _run(ssh, "bash /tmp/verify_subscriptions.sh", timeout=180)
    finally:
        _run(ssh, "rm -f /tmp/verify_subscriptions.sh", timeout=30)


def _print_result(name: str, out: str, err: str) -> None:
    val = (out.strip() or err.strip()).strip().replace("\ufeff", "")
    print(f"[{name}] {val}")


def _result_row(name: str, passed: bool, **details: Any) -> dict[str, Any]:
    """Build one bounded readiness result without retaining raw responses."""
    return {"name": name, "status": "PASS" if passed else "FAIL", **details}


def _subscription_sample_count(output: str) -> int:
    """Count successful redacted subscription samples in verifier output."""
    return sum(
        1
        for line in str(output or "").splitlines()
        if re.fullmatch(
            r"sub_fetch_\d+ user=selected mode=(?:token|tg_id_fallback) "
            r"fmt=(?:plain|base64) lines=\d+ hosts=\d+ connect_json=1 outbounds=\d+",
            line.strip(),
        )
    )


def _build_json_report(*, checks: list[dict[str, Any]], failures: list[str]) -> dict[str, Any]:
    """Build the secret-free Brain readiness evidence envelope."""
    return {
        "schema_version": "pokrov-brain-readiness-v1",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "origin": "brain",
        "checks": checks,
        "check_count": len(checks),
        "failure_count": len(failures),
        "ok": not failures and bool(checks),
    }


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


def _required_secret_presence_cmd() -> str:
    """Check release-critical secret presence without returning secret bytes."""
    script = r"""set -euo pipefail
env_file="$(systemctl show portal-api.service --property=EnvironmentFiles --value | awk '{print $1}')"
if [ -z "$env_file" ] || [ ! -r "$env_file" ]; then
  env_file=/root/portal_bot/.env
fi
ENV_FILE="$env_file" python3 - <<'PY'
import os
from pathlib import Path

path = Path(os.environ["ENV_FILE"])
values = {}
for raw_line in path.read_text(encoding="utf-8", errors="strict").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    values[key.strip()] = value.strip().strip('"').strip("'")

name = "DEVICE_PAIRING_HMAC_SECRET"
if len(values.get(name, "")) < 32:
    print(f"{name}=missing_or_short")
    raise SystemExit(2)
print(f"{name}=present length_ok=1")
PY"""
    return "bash -lc " + shlex.quote(script)


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


def _binary_rule_set_retry(
    url: str,
    *,
    host: str,
    attempts: int = 6,
    pause_sec: float = 1.0,
) -> str:
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
            "-D",
            '"$headers_file"',
            "-o",
            '"$body_file"',
            shlex.quote(target_url),
        ]
    )
    script = (
        "headers_file=/tmp/portal_verify_rule_headers.$$; "
        "body_file=/tmp/portal_verify_rule_body.$$; "
        "cleanup() { rm -f \"$headers_file\" \"$body_file\"; }; "
        "trap cleanup EXIT; "
        f"for i in $(seq 1 {int(attempts)}); do "
        f"if {base}; then "
        "content_type=$(awk 'BEGIN{IGNORECASE=1} /^content-type:/ {sub(/^[^:]*:[[:space:]]*/, \"\"); gsub(/\\r/, \"\"); print; exit}' \"$headers_file\"); "
        "size=$(wc -c < \"$body_file\" | tr -d '[:space:]'); "
        "magic=$(od -An -tx1 -N3 \"$body_file\" | tr -d '[:space:]'); "
        "if [ \"$content_type\" = application/octet-stream ] && [ \"$magic\" = 535253 ] && [ \"$size\" -ge 32 ]; then "
        "printf 'Content-Type: %s size=%s magic=SRS\\n' \"$content_type\" \"$size\"; "
        "exit 0; "
        "fi; "
        "fi; "
        f"sleep {pause_sec}; "
        "done; "
        "printf 'invalid rule set content_type=%s size=%s magic=%s\\n' \"${content_type:-<missing>}\" \"${size:-0}\" \"${magic:-<missing>}\"; "
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
    connection = ap.add_mutually_exclusive_group(required=True)
    connection.add_argument("--brain-ip")
    connection.add_argument("--ssh-config-alias")
    ap.add_argument("--ssh-config", default="")
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--repeat", type=int, default=5, help="repeat subscription fetch N times")
    ap.add_argument("--check-legacy-2096", action="store_true", help="also verify legacy :2096 endpoint (optional)")
    ap.add_argument("--json-out", default="", help="Optional secret-free JSON readiness evidence path.")
    args = ap.parse_args()

    web_domain = (args.domain or "").strip() or (args.web_domain or "").strip()
    api_domain = (args.api_domain or "").strip()
    connect_domain = (args.connect_domain or "").strip()
    if not web_domain:
        raise SystemExit("Missing --web-domain")
    if not api_domain:
        raise SystemExit("Missing --api-domain")
    if not connect_domain:
        raise SystemExit("Missing --connect-domain")

    if args.ssh_config_alias:
        try:
            ssh = OpenSshConfigSession(
                alias=args.ssh_config_alias,
                config_path=Path(args.ssh_config).expanduser() if args.ssh_config else None,
            )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    else:
        pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords)).get("brain", "")
        if not pw:
            raise SystemExit("Missing brain password (set NODE_PASS_BRAIN or add to PASSWORDS.txt).")
        ssh = _ssh_connect(args.brain_ip, user=args.ssh_user, port=args.ssh_port, password=pw)
    try:
        failures: list[str] = []
        checks: list[dict[str, Any]] = []
        for unit in DEFAULT_REQUIRED_UNITS:
            name = unit
            cmd = f"systemctl is-active {unit}"
            code, out, err = _run(ssh, cmd, timeout=60)
            _print_result(name, out, err)
            passed = code == 0 and (out.strip() or err.strip()).strip() == "active"
            checks.append(_result_row(f"unit:{unit}", passed))
            if not passed:
                failures.append(f"{unit} is not active")

        code, out, err = _run(ssh, _required_secret_presence_cmd(), timeout=60)
        _print_result("requiredSecrets", out, err)
        checks.append(_result_row("required_secret_presence", code == 0))
        if code != 0:
            failures.append("DEVICE_PAIRING_HMAC_SECRET is missing or too short")

        required_listener_ports = list(DEFAULT_REQUIRED_LISTENER_PORTS)
        if args.check_legacy_2096:
            required_listener_ports.append(2096)
        listen_cmd = _listener_probe_cmd(tuple(required_listener_ports))
        code, out, err = _run(ssh, listen_cmd, timeout=60)
        _print_result("listen", out, err)
        missing_ports = _listener_missing_ports(out or err, tuple(required_listener_ports))
        listener_passed = code == 0 and not missing_ports
        checks.append(
            _result_row(
                "required_listeners",
                listener_passed,
                required_ports=required_listener_ports,
                missing_ports=missing_ports,
            )
        )
        if not listener_passed:
            failures.append(
                "missing listeners: " + ", ".join(str(port) for port in missing_ports)
                if missing_ports
                else "listener probe failed"
            )

        curl_checks = [
            ("health443", _curl_retry(f"{api_domain}/api/health", host=api_domain)),
            (
                "rulesGeoIpRu443",
                _binary_rule_set_retry(
                    f"{connect_domain}/rules/geoip-ru.srs",
                    host=connect_domain,
                ),
            ),
            (
                "rulesAdblock443",
                _binary_rule_set_retry(
                    f"{connect_domain}/rules/adblock.srs",
                    host=connect_domain,
                ),
            ),
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
            checks.append(_result_row(f"endpoint:{name}", code == 0))
            if code != 0:
                failures.append(f"{name} probe failed")

        sub_check = _build_subscription_check_script(
            api_domain=api_domain,
            connect_domain=connect_domain,
            repeat=args.repeat,
        )
        code, out, err = _run_subscription_script(ssh, sub_check)
        print((out.strip() or err.strip()).strip())
        sample_count = _subscription_sample_count(out)
        subscription_passed = code == 0 and sample_count == int(args.repeat)
        checks.append(
            _result_row(
                "subscription_stability",
                subscription_passed,
                samples_requested=int(args.repeat),
                samples_observed=sample_count,
            )
        )
        if not subscription_passed:
            failures.append("subscription stability probe failed")

        report = _build_json_report(checks=checks, failures=failures)
        json_out = str(getattr(args, "json_out", "") or "").strip()
        if json_out:
            output_path = Path(json_out)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(output_path)

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

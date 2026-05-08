from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from node_access import DEFAULT_PASSWORDS, connect_node
from smoke_client_apps import _provider_readiness_failures, _release_handoff_failures


PASS = "PASS"
FAIL = "FAIL"
BLOCKED_BY_ACCESS = "BLOCKED_BY_ACCESS"
EXTERNAL_DEPENDENCY = "EXTERNAL_DEPENDENCY"

_REMOTE_CHECK_KEYS = {"name", "status", "missing", "note", "source", "http_status"}
DEFAULT_SYNTHETIC_TG_ID = 900000001


def _status(name: str, status: str, *, missing: list[str] | None = None, note: str = "", **extra: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "name": name,
        "status": status,
        "missing": list(missing or []),
    }
    if note:
        row["note"] = note
    row.update(extra)
    return row


def _remote_smoke_script(*, unit: str, api_base_url: str, tg_id: int, check_providers: bool, timeout: int) -> str:
    config = {
        "unit": unit,
        "api_base_url": api_base_url.rstrip("/"),
        "tg_id": int(tg_id),
        "check_providers": bool(check_providers),
        "timeout": int(timeout),
    }
    encoded_config = json.dumps(config, ensure_ascii=False)
    return f"""python3 - <<'PY'
import hashlib
import hmac
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

PASS = "PASS"
BLOCKED_BY_ACCESS = "BLOCKED_BY_ACCESS"

cfg = json.loads({encoded_config!r})
unit = str(cfg.get("unit") or "portal-bot")
base = str(cfg.get("api_base_url") or "https://api.pokrov.space").rstrip("/")
tg_id = int(cfg.get("tg_id") or 1)
timeout = int(cfg.get("timeout") or 20)
check_providers = bool(cfg.get("check_providers"))


def check(name, status, *, missing=None, note="", source="", http_status=None):
    row = {{
        "name": name,
        "status": status,
        "missing": list(missing or []),
        "note": note,
        "source": source,
    }}
    if http_status is not None:
        row["http_status"] = int(http_status)
    return row


def read_token():
    pid_raw = subprocess.run(
        ["systemctl", "show", unit, "-p", "MainPID", "--value"],
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    try:
        pid = int(pid_raw)
    except Exception:
        pid = 0
    if pid <= 0:
        return False, ""
    try:
        for item in open(f"/proc/{{pid}}/environ", "rb").read().split(b"\\0"):
            if b"=" not in item:
                continue
            key, value = item.split(b"=", 1)
            if key.decode("utf-8", "replace") == "BOT_TOKEN":
                return True, value.decode("utf-8", "replace")
    except Exception:
        return True, ""
    return True, ""


def signed_init_data(token):
    user = json.dumps(
        {{"id": tg_id, "first_name": "POKROV", "username": "release_probe"}},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    fields = {{
        "query_id": f"brain_release_probe_{{int(time.time())}}",
        "user": user,
        "auth_date": str(int(time.time())),
    }}
    data_check_string = "\\n".join(f"{{key}}={{value}}" for key, value in sorted(fields.items()))
    secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urllib.parse.urlencode(fields)


def get_json(path, *, headers=None):
    req = urllib.request.Request(f"{{base}}{{path}}", headers=headers or {{"Accept": "application/json"}}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
            try:
                payload = json.loads(body or "{{}}")
            except Exception:
                payload = {{"_non_json": body[:200]}}
            return int(response.status), payload, ""
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            payload = json.loads(body or "{{}}")
        except Exception:
            payload = {{"_non_json": body[:200]}}
        return int(exc.code), payload, "HTTPError"
    except Exception as exc:
        return None, {{}}, type(exc).__name__


checks = []
pid_present, token = read_token()
checks.append(
    check(
        "brain_bot_runtime_token",
        PASS if pid_present and token else BLOCKED_BY_ACCESS,
        missing=[] if pid_present and token else [f"{{unit}} BOT_TOKEN"],
        note="Token presence is read on brain and never returned.",
        source=f"brain:{{unit}}",
    )
)

health_status, health_payload, health_error = get_json("/api/health")
checks.append(
    check(
        "api_health",
        PASS if health_status is not None and 200 <= int(health_status) < 400 else BLOCKED_BY_ACCESS,
        missing=[] if health_status is not None and 200 <= int(health_status) < 400 else [health_error or f"HTTP {{health_status}}"],
        note="Brain-origin API health request.",
        source=f"{{base}}/api/health",
        http_status=health_status,
    )
)

apps_payload = {{}}
providers_payload = {{}}
if token:
    init_data = signed_init_data(token)
    apps_status, apps_payload, apps_error = get_json(
        "/api/client/apps",
        headers={{"Accept": "application/json", "X-Telegram-Init-Data": init_data}},
    )
    checks.append(
        check(
            "api_client_apps_signed_init_data",
            PASS if apps_status is not None and 200 <= int(apps_status) < 400 else BLOCKED_BY_ACCESS,
            missing=[] if apps_status is not None and 200 <= int(apps_status) < 400 else [apps_error or f"HTTP {{apps_status}}"],
            note="Uses synthetic signed initData generated on brain from the runtime BOT_TOKEN; neither token nor initData is returned.",
            source=f"{{base}}/api/client/apps",
            http_status=apps_status,
        )
    )
    if check_providers:
        providers_status, providers_payload, providers_error = get_json("/api/payments/providers")
        checks.append(
            check(
                "api_payment_providers",
                PASS if providers_status is not None and 200 <= int(providers_status) < 400 else BLOCKED_BY_ACCESS,
                missing=[] if providers_status is not None and 200 <= int(providers_status) < 400 else [providers_error or f"HTTP {{providers_status}}"],
                note="Live provider catalog request; policy validation happens locally after redaction.",
                source=f"{{base}}/api/payments/providers",
                http_status=providers_status,
            )
        )

print(json.dumps({{
    "unit": unit,
    "api_base_url": base,
    "tg_id": tg_id,
    "signed_init_data_origin": "brain_runtime_bot_token",
    "pid_present": bool(pid_present),
    "token_present": bool(token),
    "checks": checks,
    "client_apps": apps_payload if isinstance(apps_payload, dict) else {{}},
    "payment_providers": providers_payload if isinstance(providers_payload, dict) else {{}},
}}, ensure_ascii=False))
PY"""


def _classification(checks: list[Mapping[str, Any]]) -> str:
    statuses = [str(check.get("status") or "") for check in checks]
    if statuses and all(status == PASS for status in statuses):
        return PASS
    if FAIL in statuses:
        return FAIL
    if BLOCKED_BY_ACCESS in statuses:
        return BLOCKED_BY_ACCESS
    return EXTERNAL_DEPENDENCY


def _sanitize_remote_checks(remote_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    sanitized: list[dict[str, Any]] = []
    for raw in remote_payload.get("checks", []) if isinstance(remote_payload.get("checks"), list) else []:
        if not isinstance(raw, Mapping):
            continue
        row = {key: raw[key] for key in _REMOTE_CHECK_KEYS if key in raw}
        row.setdefault("name", "remote_check")
        row.setdefault("status", BLOCKED_BY_ACCESS)
        row.setdefault("missing", [])
        row.setdefault("note", "")
        row.setdefault("source", "brain")
        sanitized.append(row)
    if not sanitized:
        sanitized.append(
            _status(
                "brain_runtime_app_smoke",
                BLOCKED_BY_ACCESS,
                missing=["remote checks"],
                note="Remote smoke did not return structured checks.",
                source="brain",
            )
        )
    return sanitized


def build_report(
    *,
    remote_payload: Mapping[str, Any],
    require_release_handoff: bool = True,
    check_providers: bool = True,
) -> dict[str, Any]:
    checks = _sanitize_remote_checks(remote_payload)
    client_apps = remote_payload.get("client_apps") if isinstance(remote_payload.get("client_apps"), Mapping) else {}
    provider_payload = remote_payload.get("payment_providers") if isinstance(remote_payload.get("payment_providers"), Mapping) else {}

    if require_release_handoff:
        release_failures = _release_handoff_failures(dict(client_apps or {}))
        checks.append(
            _status(
                "runtime_client_apps_release_handoff",
                PASS if not release_failures else BLOCKED_BY_ACCESS,
                missing=release_failures,
                note="Live /api/client/apps must expose GitHub Releases APK/EXE and install docs before runtime link launch.",
                source="/api/client/apps",
            )
        )

    if check_providers:
        if provider_payload:
            provider_failures = _provider_readiness_failures(dict(provider_payload))
            provider_status = PASS if not provider_failures else FAIL
            checks.append(
                _status(
                    "runtime_payment_provider_policy",
                    provider_status,
                    missing=provider_failures,
                    note="Blocked provider catalog with reasons is acceptable while paid checkout evidence is not green; green catalog must be Lava.top-only.",
                    source="/api/payments/providers",
                )
            )
        else:
            checks.append(
                _status(
                    "runtime_payment_provider_policy",
                    BLOCKED_BY_ACCESS,
                    missing=["/api/payments/providers payload"],
                    note="Provider catalog was not available for policy validation.",
                    source="/api/payments/providers",
                )
            )

    classification = _classification(checks)
    runtime_app_download_smoke_passed = classification == PASS and (
        not require_release_handoff
        or any(check.get("name") == "runtime_client_apps_release_handoff" and check.get("status") == PASS for check in checks)
    )
    return {
        "ok": classification == PASS,
        "classification": classification,
        "mode": "brain_runtime_app_download_smoke",
        "signed_init_data_origin": str(remote_payload.get("signed_init_data_origin") or "brain_runtime_bot_token"),
        "source_unit": str(remote_payload.get("unit") or ""),
        "api_base_url": str(remote_payload.get("api_base_url") or ""),
        "tg_id": int(remote_payload.get("tg_id") or 0),
        "runtime_app_download_smoke_passed": bool(runtime_app_download_smoke_passed),
        "note": "This proves backend auth and runtime link policy using synthetic signed initData generated on brain; it is not proof that a real user opened Telegram WebApp.",
        "client_apps": dict(client_apps or {}),
        "checks": checks,
    }


def _fetch_remote_payload(*, brain_ip: str, ssh_user: str, ssh_port: int, passwords: str, source_unit: str, api_base_url: str, tg_id: int, check_providers: bool, timeout: int) -> dict[str, Any]:
    ssh, _auth_method = connect_node(
        code="brain",
        host=brain_ip,
        user=ssh_user,
        port=int(ssh_port),
        passwords_path=Path(passwords),
    )
    try:
        command = "bash -lc " + shlex.quote(
            _remote_smoke_script(
                unit=source_unit,
                api_base_url=api_base_url,
                tg_id=int(tg_id),
                check_providers=check_providers,
                timeout=int(timeout),
            )
        )
        _stdin, stdout, stderr = ssh.exec_command(command, timeout=max(60, int(timeout) * 4))
        code = stdout.channel.recv_exit_status()
        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
    finally:
        ssh.close()
    if code != 0:
        return {
            "unit": source_unit,
            "api_base_url": api_base_url,
            "tg_id": int(tg_id),
            "checks": [
                _status(
                    "brain_runtime_app_smoke_remote_command",
                    BLOCKED_BY_ACCESS,
                    missing=[f"remote command exit {code}"],
                    note=(err or out or "Remote brain runtime app smoke failed before returning structured checks.")[:240],
                    source=f"brain:{source_unit}",
                )
            ],
        }
    try:
        payload = json.loads(out or "{}")
    except json.JSONDecodeError:
        payload = {}
    return payload if isinstance(payload, dict) else {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run brain-local /api/client/apps smoke with synthetic signed initData without returning BOT_TOKEN or initData.",
    )
    parser.add_argument("--brain-ip", required=True)
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--source-unit", default="portal-bot")
    parser.add_argument("--api-base-url", default="https://api.pokrov.space")
    parser.add_argument("--tg-id", type=int, default=DEFAULT_SYNTHETIC_TG_ID)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--skip-providers", action="store_true")
    parser.add_argument("--no-require-release-handoff", action="store_true")
    parser.add_argument("--output", default="")
    args = parser.parse_args(argv)

    remote_payload = _fetch_remote_payload(
        brain_ip=args.brain_ip,
        ssh_user=args.ssh_user,
        ssh_port=int(args.ssh_port),
        passwords=args.passwords,
        source_unit=args.source_unit,
        api_base_url=args.api_base_url,
        tg_id=int(args.tg_id),
        check_providers=not bool(args.skip_providers),
        timeout=int(args.timeout),
    )
    report = build_report(
        remote_payload=remote_payload,
        require_release_handoff=not bool(args.no_require_release_handoff),
        check_providers=not bool(args.skip_providers),
    )
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from payment_email_readiness_smoke import build_report  # noqa: E402


PASS = "PASS"
BLOCKED_BY_ACCESS = "BLOCKED_BY_ACCESS"
EXTERNAL_DEPENDENCY = "EXTERNAL_DEPENDENCY"

_SECRET_OR_VALUE_NAMES = {
    "LAVATOP_API_BASE_URL",
    "EMAIL_AUTH_WEBHOOK_URL",
    "EMAIL_DELIVERY_WEBHOOK_URL",
    "EMAIL_DELIVERY_WEBHOOK_SECRET",
    "LAVATOP_API_KEY",
    "LAVATOP_OFFER_ID",
    "LAVATOP_PAYMENT_METHOD",
    "LAVATOP_PAYMENT_PROVIDER",
    "LAVATOP_PERIODICITY",
    "LAVATOP_BUYER_LANGUAGE",
    "LAVATOP_WEBHOOK_API_KEY",
    "LAVATOP_WEBHOOK_BASIC_USERNAME",
    "LAVATOP_WEBHOOK_BASIC_PASSWORD",
}
_POST_DEPLOY_ALLOWED_CHECK_KEYS = {"name", "status", "missing", "note", "source", "http_status"}
_POST_DEPLOY_EMAIL_CHECKS = {
    "email_delivery_verify",
    "email_delivery_reset",
    "email_delivery_payment_access_key",
}
_BOOLEAN_NAMES = {
    "EMAIL_AUTH_DEBUG_ECHO",
    "EMAIL_AUTH_PUBLIC_ENABLED",
    "LAVATOP_DYNAMIC_AMOUNT_ENABLED",
    "LAVATOP_PROVIDER_ACCEPTANCE_CONFIRMED",
}


def _offer_env_name(plan_code: str) -> str:
    suffix = "".join(ch if ch.isalnum() else "_" for ch in str(plan_code or "").upper()).strip("_")
    return f"LAVATOP_OFFER_ID_{suffix}" if suffix else "LAVATOP_OFFER_ID"


def _remote_env_probe_script(*, unit: str, names: list[str]) -> str:
    encoded_names = json.dumps(sorted(set(names)))
    return f"""python3 - <<'PY'
import json
import subprocess

unit = {unit!r}
names = set(json.loads({encoded_names!r}))
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
env = {{}}
if pid > 0:
    try:
        for item in open(f"/proc/{{pid}}/environ", "rb").read().split(b"\\0"):
            if b"=" not in item:
                continue
            key, value = item.split(b"=", 1)
            key_text = key.decode("utf-8", "replace")
            if key_text in names:
                env[key_text] = value.decode("utf-8", "replace")
    except Exception:
        pass
print(json.dumps({{"unit": unit, "pid_present": bool(pid > 0), "env": env}}, ensure_ascii=False))
PY"""


def _remote_post_deploy_probe_script(
    *,
    unit: str,
    plan_code: str,
    email_probe_to: str,
    lavatop_probe_email: str,
) -> str:
    names = sorted(set(_SECRET_OR_VALUE_NAMES) | set(_BOOLEAN_NAMES) | {_offer_env_name(plan_code)})
    config = {
        "unit": unit,
        "plan_code": plan_code,
        "email_probe_to": email_probe_to,
        "lavatop_probe_email": lavatop_probe_email,
        "names": names,
    }
    encoded_config = json.dumps(config, ensure_ascii=False)
    return f"""python3 - <<'PY'
import json
import os
import subprocess
import time
import urllib.error
import urllib.request

PASS = "PASS"
BLOCKED_BY_ACCESS = "BLOCKED_BY_ACCESS"

cfg = json.loads({encoded_config!r})
unit = str(cfg.get("unit") or "portal-api")
plan_code = str(cfg.get("plan_code") or "start_99").strip().lower() or "start_99"
email_probe_to = str(cfg.get("email_probe_to") or "").strip()
lavatop_probe_email = str(cfg.get("lavatop_probe_email") or "").strip()
names = set(cfg.get("names") or [])


def check(name, status, *, missing=None, note="", source="", http_status=None):
    item = {{
        "name": name,
        "status": status,
        "missing": list(missing or []),
        "note": note,
        "source": source,
    }}
    if http_status is not None:
        item["http_status"] = int(http_status)
    return item


def offer_env_name(plan):
    suffix = "".join(ch if ch.isalnum() else "_" for ch in str(plan or "").upper()).strip("_")
    return f"LAVATOP_OFFER_ID_{{suffix}}" if suffix else "LAVATOP_OFFER_ID"


def env_present(env, name):
    return bool(str(env.get(name) or "").strip())


def truthy(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


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

env = {{}}
checks = []
if pid <= 0:
    checks.append(
        check(
            "brain_source_unit_pid",
            BLOCKED_BY_ACCESS,
            missing=[f"{{unit}} MainPID"],
            note="Unable to inspect the live process environment on brain.",
            source=f"brain:{{unit}}",
        )
    )
else:
    try:
        for item in open(f"/proc/{{pid}}/environ", "rb").read().split(b"\\0"):
            if b"=" not in item:
                continue
            key, value = item.split(b"=", 1)
            key_text = key.decode("utf-8", "replace")
            if key_text in names:
                env[key_text] = value.decode("utf-8", "replace")
    except Exception as exc:
        checks.append(
            check(
                "brain_source_unit_env",
                BLOCKED_BY_ACCESS,
                missing=[type(exc).__name__],
                note="Unable to inspect the live process environment on brain.",
                source=f"brain:{{unit}}",
            )
        )


def post_json(url, payload, headers, timeout=25):
    request = urllib.request.Request(
        str(url),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(response.status), ""
    except urllib.error.HTTPError as exc:
        return int(exc.code), "HTTPError"
    except Exception as exc:
        return None, type(exc).__name__


def email_public_mode_check():
    missing = []
    if not truthy(env.get("EMAIL_AUTH_PUBLIC_ENABLED")):
        missing.append("EMAIL_AUTH_PUBLIC_ENABLED=true")
    if truthy(env.get("EMAIL_AUTH_DEBUG_ECHO")):
        missing.append("EMAIL_AUTH_DEBUG_ECHO=false")
    return check(
        "email_public_mode",
        PASS if not missing else BLOCKED_BY_ACCESS,
        missing=missing,
        note="Public email auth runtime mode can stay enabled when public mode is on and debug echo is off; live inbox proof is checked separately.",
        source=f"brain:{{unit}}",
    )


def email_delivery_check(kind):
    url = str(env.get("EMAIL_DELIVERY_WEBHOOK_URL") or env.get("EMAIL_AUTH_WEBHOOK_URL") or "").strip()
    secret = str(env.get("EMAIL_DELIVERY_WEBHOOK_SECRET") or "").strip()
    missing = []
    if not email_probe_to:
        missing.append("email_probe_to")
    if not url:
        missing.append("EMAIL_DELIVERY_WEBHOOK_URL or EMAIL_AUTH_WEBHOOK_URL")
    if not secret:
        missing.append("EMAIL_DELIVERY_WEBHOOK_SECRET")
    if missing:
        return check(
            f"email_delivery_{{kind}}",
            BLOCKED_BY_ACCESS,
            missing=missing,
            note="Live email delivery proof requires a probe recipient and relay runtime env.",
            source=f"brain:{{unit}}",
        )
    payload = {{"kind": kind, "email": email_probe_to}}
    if kind in {{"verify", "reset"}}:
        payload["token"] = "probe-token-redacted"
    else:
        payload.update(
            {{
                "access_key": "POKROV-PROBE-KEY1",
                "order_id": "probe-order",
                "plan_code": plan_code,
                "plan_label": "POKROV Start",
                "days": 30,
            }}
        )
    status, error = post_json(
        url,
        payload,
        {{
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Pokrov-Email-Secret": secret,
            "Authorization": f"Bearer {{secret}}",
        }},
        timeout=25,
    )
    ok = status is not None and int(status) < 400
    return check(
        f"email_delivery_{{kind}}",
        PASS if ok else BLOCKED_BY_ACCESS,
        missing=[] if ok else [error or f"HTTP {{status}}"],
        note="Live email delivery probe returned a redacted HTTP status only.",
        source=f"brain:{{unit}}",
        http_status=status,
    )


def lavatop_invoice_check():
    offer_name = offer_env_name(plan_code)
    offer_id = str(env.get(offer_name) or env.get("LAVATOP_OFFER_ID") or "").strip()
    api_key = str(env.get("LAVATOP_API_KEY") or "").strip()
    missing = []
    if not lavatop_probe_email:
        missing.append("lavatop_probe_email")
    if not api_key:
        missing.append("LAVATOP_API_KEY")
    if not offer_id:
        missing.append(f"{{offer_name}} or LAVATOP_OFFER_ID")
    if missing:
        return check(
            "lavatop_live_invoice_creation",
            BLOCKED_BY_ACCESS,
            missing=missing,
            note="Live Lava.top invoice proof requires a probe buyer and runtime credentials.",
            source=f"brain:{{unit}}",
        )
    base_url = str(env.get("LAVATOP_API_BASE_URL") or "https://gate.lava.top").rstrip("/")
    order_id = f"lavatop_probe_{{int(time.time())}}"
    payload = {{
        "email": lavatop_probe_email,
        "offerId": offer_id,
        "currency": "RUB",
        "buyerLanguage": str(env.get("LAVATOP_BUYER_LANGUAGE") or "RU").upper()[:2],
        "clientUtm": {{
            "utm_source": "pokrov",
            "utm_medium": "probe",
            "utm_campaign": "operator_probe",
            "utm_term": plan_code,
            "utm_content": order_id,
        }},
    }}
    payment_provider = str(env.get("LAVATOP_PAYMENT_PROVIDER") or "").strip().upper()
    payment_method = str(env.get("LAVATOP_PAYMENT_METHOD") or "").strip().upper()
    periodicity = str(env.get("LAVATOP_PERIODICITY") or "").strip().upper()
    if payment_provider:
        payload["paymentProvider"] = payment_provider
    if payment_method:
        payload["paymentMethod"] = payment_method
    if periodicity:
        payload["periodicity"] = periodicity
    if truthy(env.get("LAVATOP_DYNAMIC_AMOUNT_ENABLED")):
        payload["amount"] = 99.0
    status, error = post_json(
        f"{{base_url}}/api/v3/invoice",
        payload,
        {{"Content-Type": "application/json", "Accept": "application/json", "X-Api-Key": api_key}},
        timeout=35,
    )
    ok = status is not None and int(status) < 400
    return check(
        "lavatop_live_invoice_creation",
        PASS if ok else BLOCKED_BY_ACCESS,
        missing=[] if ok else [error or f"HTTP {{status}}"],
        note="Live Lava.top invoice probe returned a redacted HTTP status only.",
        source=f"brain:{{unit}}",
        http_status=status,
    )


if not checks:
    checks.extend(
        [
            email_public_mode_check(),
            email_delivery_check("verify"),
            email_delivery_check("reset"),
            email_delivery_check("payment_access_key"),
            lavatop_invoice_check(),
        ]
    )

print(json.dumps({{"checks": checks}}, ensure_ascii=False))
PY"""


def _classification(statuses: list[str]) -> str:
    if statuses and all(status == PASS for status in statuses):
        return PASS
    if BLOCKED_BY_ACCESS in statuses:
        return BLOCKED_BY_ACCESS
    return EXTERNAL_DEPENDENCY


def _post_deploy_probe_mode(by_name: Mapping[str, Mapping[str, object]]) -> str:
    email_pass = all(str(by_name.get(name, {}).get("status") or "") == PASS for name in _POST_DEPLOY_EMAIL_CHECKS)
    lavatop_pass = str(by_name.get("lavatop_live_invoice_creation", {}).get("status") or "") == PASS
    if email_pass and lavatop_pass:
        return "email_and_lavatop_probe_passed"
    if email_pass:
        return "email_probe_passed_lavatop_pending"
    if lavatop_pass:
        return "lavatop_invoice_probe_passed_email_pending"
    return "blocked_missing_or_failed_probe_inputs"


def _post_deploy_email_public_safe(by_name: Mapping[str, Mapping[str, object]]) -> bool:
    if "email_public_mode" in by_name:
        return str(by_name.get("email_public_mode", {}).get("status") or "") == PASS
    return all(
        str(by_name.get(name, {}).get("status") or "") == PASS for name in {"email_delivery_verify", "email_delivery_reset"}
    )


def build_brain_post_deploy_report(
    *,
    remote_payload: Mapping[str, object],
    source_unit: str = "portal-api",
    plan_code: str = "start_99",
) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    for raw_check in remote_payload.get("checks", []) if isinstance(remote_payload.get("checks"), list) else []:
        if not isinstance(raw_check, Mapping):
            continue
        check = {key: raw_check[key] for key in _POST_DEPLOY_ALLOWED_CHECK_KEYS if key in raw_check}
        check.setdefault("missing", [])
        check.setdefault("note", "")
        check.setdefault("source", f"brain:{source_unit}")
        checks.append(check)
    if not checks:
        checks.append(
            {
                "name": "brain_post_deploy_probe",
                "status": BLOCKED_BY_ACCESS,
                "missing": ["remote checks"],
                "note": "Remote post-deploy probe did not return check results.",
                "source": f"brain:{source_unit}",
            }
        )
    statuses = [str(check.get("status") or "") for check in checks]
    classification = _classification(statuses)
    by_name = {str(check.get("name") or ""): check for check in checks}
    safe_to_keep_email_public = _post_deploy_email_public_safe(by_name)
    lavatop_invoice_probe_passed = str(by_name.get("lavatop_live_invoice_creation", {}).get("status") or "") == PASS
    return {
        "ok": classification == PASS,
        "classification": classification,
        "mode": "brain_post_deploy_live_probe",
        "live": True,
        "source_unit": source_unit,
        "plan_code": plan_code,
        "post_deploy_probe_mode": _post_deploy_probe_mode(by_name),
        "safe_to_keep_email_public": safe_to_keep_email_public,
        "email_public_probe_can_be_evaluated_independently": True,
        "lavatop_invoice_probe_passed": lavatop_invoice_probe_passed,
        "safe_to_enable_paid_checkout": False,
        "note": "Lava.top invoice creation proof is only one part of paid-checkout launch evidence; webhook/replay/failure/reconciliation proof is still separate.",
        "checks": checks,
    }


def sanitize_env_for_report(raw_env: Mapping[str, str], *, plan_code: str) -> dict[str, str]:
    names = set(_SECRET_OR_VALUE_NAMES) | set(_BOOLEAN_NAMES) | {_offer_env_name(plan_code)}
    sanitized: dict[str, str] = {}
    for name in sorted(names):
        value = str(raw_env.get(name) or "").strip()
        if not value:
            continue
        if name in _BOOLEAN_NAMES:
            sanitized[name] = value
        else:
            sanitized[name] = "present"
    return sanitized


def build_brain_readiness_report(
    *,
    raw_env: Mapping[str, str],
    source_unit: str = "portal-api",
    pid_present: bool = True,
    plan_code: str = "start_99",
) -> dict[str, object]:
    sanitized = sanitize_env_for_report(raw_env, plan_code=plan_code)
    report = build_report(env=sanitized, plan_code=plan_code)
    report["mode"] = "brain_proc_env_readiness"
    report["source_unit"] = source_unit
    report["pid_present"] = bool(pid_present)
    if not pid_present:
        report["ok"] = False
        report["classification"] = "BLOCKED_BY_ACCESS"
        report["safe_to_enable_paid_checkout"] = False
        report.setdefault("checks", []).insert(
            0,
            {
                "name": "brain_source_unit_pid",
                "status": "BLOCKED_BY_ACCESS",
                "missing": [f"{source_unit} MainPID"],
                "note": "Unable to inspect the live process environment on brain.",
            },
        )
    return report


def main(argv: list[str] | None = None) -> int:
    from node_access import DEFAULT_PASSWORDS, connect_node

    parser = argparse.ArgumentParser(
        description="Read redacted Lava.top/email readiness from a live brain unit environment.",
    )
    parser.add_argument("--brain-ip", required=True)
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--source-unit", default="portal-api")
    parser.add_argument("--plan-code", default="start_99")
    parser.add_argument("--output", default="")
    parser.add_argument("--post-deploy-live", action="store_true", help="Run live email/Lava.top probes on brain without returning secrets.")
    parser.add_argument("--email-probe-to", default="", help="Safe recipient email for brain-local verify/reset/payment-access-key probes.")
    parser.add_argument("--lavatop-probe-email", default="", help="Safe buyer email for the brain-local Lava.top invoice probe.")
    args = parser.parse_args(argv)

    names = sorted(set(_SECRET_OR_VALUE_NAMES) | set(_BOOLEAN_NAMES) | {_offer_env_name(args.plan_code)})
    ssh, _auth_method = connect_node(
        code="brain",
        host=args.brain_ip,
        user=args.ssh_user,
        port=int(args.ssh_port),
        passwords_path=Path(args.passwords),
    )
    try:
        if args.post_deploy_live:
            command = "bash -lc " + shlex.quote(
                _remote_post_deploy_probe_script(
                    unit=args.source_unit,
                    plan_code=args.plan_code,
                    email_probe_to=args.email_probe_to,
                    lavatop_probe_email=args.lavatop_probe_email,
                )
            )
        else:
            command = "bash -lc " + shlex.quote(_remote_env_probe_script(unit=args.source_unit, names=names))
        _stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
        code = stdout.channel.recv_exit_status()
        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
    finally:
        ssh.close()

    if code != 0:
        if args.post_deploy_live:
            report = build_brain_post_deploy_report(
                remote_payload={
                    "checks": [
                        {
                            "name": "brain_post_deploy_probe",
                            "status": BLOCKED_BY_ACCESS,
                            "missing": [f"remote command exit {code}"],
                            "note": "Remote brain post-deploy probe failed before returning redacted checks.",
                            "source": f"brain:{args.source_unit}",
                        }
                    ]
                },
                source_unit=str(args.source_unit),
                plan_code=str(args.plan_code),
            )
            encoded = json.dumps(report, ensure_ascii=False, indent=2)
            if args.output:
                out_path = Path(args.output)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(encoded + "\n", encoding="utf-8")
            print(encoded)
            return 2
        raise SystemExit((err or out or "brain env probe failed").strip())

    payload = json.loads(out or "{}")
    if args.post_deploy_live:
        report = build_brain_post_deploy_report(
            remote_payload=payload,
            source_unit=str(args.source_unit),
            plan_code=args.plan_code,
        )
    else:
        report = build_brain_readiness_report(
            raw_env=dict(payload.get("env") or {}),
            source_unit=str(payload.get("unit") or args.source_unit),
            pid_present=bool(payload.get("pid_present")),
            plan_code=args.plan_code,
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

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Mapping


PASS = "PASS"
BLOCKED_BY_ACCESS = "BLOCKED_BY_ACCESS"
EXTERNAL_DEPENDENCY = "EXTERNAL_DEPENDENCY"


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "y"}


def _env(env: Mapping[str, str], name: str) -> str:
    return str(env.get(name) or "").strip()


def _offer_env_name(plan_code: str) -> str:
    suffix = "".join(ch if ch.isalnum() else "_" for ch in str(plan_code or "").upper()).strip("_")
    return f"LAVATOP_OFFER_ID_{suffix}" if suffix else "LAVATOP_OFFER_ID"


def _check(name: str, status: str, *, missing: list[str] | None = None, note: str = "") -> dict[str, object]:
    return {
        "name": name,
        "status": status,
        "missing": list(missing or []),
        "note": note,
    }


def build_report(*, env: Mapping[str, str] | None = None, plan_code: str = "start_99") -> dict[str, object]:
    src = env if env is not None else os.environ
    plan = str(plan_code or "start_99").strip().lower() or "start_99"
    offer_name = _offer_env_name(plan)
    offer_configured = bool(_env(src, offer_name) or _env(src, "LAVATOP_OFFER_ID"))

    checks: list[dict[str, object]] = []

    invoice_missing: list[str] = []
    if not _env(src, "LAVATOP_API_KEY"):
        invoice_missing.append("LAVATOP_API_KEY")
    if not offer_configured:
        invoice_missing.append(f"{offer_name} or LAVATOP_OFFER_ID")
    checks.append(
        _check(
            "lavatop_invoice_credentials",
            BLOCKED_BY_ACCESS if invoice_missing else PASS,
            missing=invoice_missing,
            note="Required before creating Lava.top invoices.",
        )
    )

    has_webhook_api_key = bool(_env(src, "LAVATOP_WEBHOOK_API_KEY"))
    has_webhook_basic = bool(_env(src, "LAVATOP_WEBHOOK_BASIC_USERNAME") and _env(src, "LAVATOP_WEBHOOK_BASIC_PASSWORD"))
    checks.append(
        _check(
            "lavatop_webhook_auth",
            PASS if has_webhook_api_key or has_webhook_basic else BLOCKED_BY_ACCESS,
            missing=[] if (has_webhook_api_key or has_webhook_basic) else ["LAVATOP_WEBHOOK_API_KEY or LAVATOP_WEBHOOK_BASIC_USERNAME+LAVATOP_WEBHOOK_BASIC_PASSWORD"],
            note="Required before accepting paid callbacks.",
        )
    )

    checks.append(
        _check(
            "lavatop_provider_acceptance",
            PASS if _truthy(_env(src, "LAVATOP_PROVIDER_ACCEPTANCE_CONFIRMED")) else EXTERNAL_DEPENDENCY,
            missing=[] if _truthy(_env(src, "LAVATOP_PROVIDER_ACCEPTANCE_CONFIRMED")) else ["LAVATOP_PROVIDER_ACCEPTANCE_CONFIRMED=true"],
            note="Operator/provider acceptance evidence is external to local code.",
        )
    )

    email_mode_missing: list[str] = []
    if not _truthy(_env(src, "EMAIL_AUTH_PUBLIC_ENABLED")):
        email_mode_missing.append("EMAIL_AUTH_PUBLIC_ENABLED=true")
    if _truthy(_env(src, "EMAIL_AUTH_DEBUG_ECHO")):
        email_mode_missing.append("EMAIL_AUTH_DEBUG_ECHO=false")
    checks.append(
        _check(
            "email_public_mode",
            BLOCKED_BY_ACCESS if email_mode_missing else PASS,
            missing=email_mode_missing,
            note="Public email auth must not launch in debug/disabled mode.",
        )
    )

    has_delivery_url = bool(_env(src, "EMAIL_DELIVERY_WEBHOOK_URL") or _env(src, "EMAIL_AUTH_WEBHOOK_URL"))
    has_delivery_secret = bool(_env(src, "EMAIL_DELIVERY_WEBHOOK_SECRET"))
    delivery_missing: list[str] = []
    if not has_delivery_url:
        delivery_missing.append("EMAIL_DELIVERY_WEBHOOK_URL or EMAIL_AUTH_WEBHOOK_URL")
    if not has_delivery_secret:
        delivery_missing.append("EMAIL_DELIVERY_WEBHOOK_SECRET")
    checks.append(
        _check(
            "email_delivery_webhook",
            PASS if not delivery_missing else BLOCKED_BY_ACCESS,
            missing=delivery_missing,
            note="Required before auth emails and paid access keys can be delivered.",
        )
    )

    statuses = [str(check["status"]) for check in checks]
    if all(status == PASS for status in statuses):
        classification = PASS
    elif BLOCKED_BY_ACCESS in statuses:
        classification = BLOCKED_BY_ACCESS
    else:
        classification = EXTERNAL_DEPENDENCY

    ok = classification == PASS
    return {
        "ok": ok,
        "classification": classification,
        "safe_to_enable_paid_checkout": ok,
        "mode": "env_readiness",
        "plan_code": plan,
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify Lava.top + email delivery readiness without printing secrets or sending live requests.",
    )
    parser.add_argument("--plan-code", default="start_99")
    parser.add_argument("--output", default="", help="Optional JSON output path.")
    args = parser.parse_args(argv)

    report = build_report(env=os.environ, plan_code=args.plan_code)
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(encoded + "\n")
    print(encoded)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

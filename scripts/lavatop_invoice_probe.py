from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request


def _offer_id(plan_code: str) -> str:
    suffix = "".join(ch if ch.isalnum() else "_" for ch in plan_code.upper()).strip("_")
    return (os.getenv(f"LAVATOP_OFFER_ID_{suffix}") or os.getenv("LAVATOP_OFFER_ID") or "").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or dry-run a Lava.top invoice request.")
    parser.add_argument("--plan-code", default="start_99")
    parser.add_argument("--email", default=os.getenv("LAVATOP_PROBE_EMAIL") or "operator@example.invalid")
    parser.add_argument("--amount", type=float, default=99.0)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    base_url = (os.getenv("LAVATOP_API_BASE_URL") or "https://gate.lava.top").rstrip("/")
    api_key = (os.getenv("LAVATOP_API_KEY") or "").strip()
    offer_id = _offer_id(args.plan_code)
    order_id = f"lavatop_probe_{int(time.time())}"
    payload = {
        "email": args.email,
        "offerId": offer_id or "redacted-offer-id",
        "currency": "RUB",
        "buyerLanguage": (os.getenv("LAVATOP_BUYER_LANGUAGE") or "RU").upper()[:2],
        "clientUtm": {
            "utm_source": "pokrov",
            "utm_medium": "probe",
            "utm_campaign": "operator_probe",
            "utm_term": args.plan_code,
            "utm_content": order_id,
        },
    }
    if (os.getenv("LAVATOP_DYNAMIC_AMOUNT_ENABLED") or "").strip().lower() in {"1", "true", "yes", "on"}:
        payload["amount"] = float(args.amount)

    if not args.live:
        safe_payload = dict(payload)
        safe_payload["offerId"] = "configured" if offer_id else "missing"
        print(json.dumps({"dry_run": True, "api_key_configured": bool(api_key), "payload": safe_payload}, ensure_ascii=False, indent=2))
        return 0
    if not api_key or not offer_id:
        print("LAVATOP_API_KEY and LAVATOP_OFFER_ID(_PLAN) are required", file=sys.stderr)
        return 2

    request = urllib.request.Request(
        f"{base_url}/api/v3/invoice",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json", "X-Api-Key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(json.dumps({"status": response.status, "body": body[:800]}, ensure_ascii=False, indent=2))
            return 0 if response.status < 400 else 1
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(json.dumps({"status": exc.code, "body": body[:800]}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.request


def env(name: str, default: str = "") -> str:
    return str(os.getenv(name, default) or "").strip()


def require(name: str) -> str:
    value = env(name)
    if not value:
        raise SystemExit(f"Missing required env: {name}")
    return value


def create_checkout_ticket(*, tg_id: int, plan_code: str, promo_code: str, campaign_key: str, source: str, secret: str, ttl_seconds: int) -> str:
    payload = {
        "tg_id": int(tg_id),
        "plan_code": str(plan_code or "").strip().lower()[:32],
        "promo_code": str(promo_code or "").strip().upper()[:20],
        "campaign_key": str(campaign_key or "").strip()[:64],
        "source": str(source or "site").strip().lower()[:16],
        "iat": int(time.time()),
        "exp": int(time.time()) + int(ttl_seconds),
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return f"{token}.{sig}"


def http_json(url: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, str, dict]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status, body, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:  # type: ignore[name-defined]
        body = exc.read().decode("utf-8", errors="replace")
        parsed = {}
        try:
            parsed = json.loads(body) if body else {}
        except Exception:
            pass
        return exc.code, body, parsed


def http_text(url: str) -> tuple[int, str]:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8", errors="replace")
        return response.status, body


def main() -> int:
    parser = argparse.ArgumentParser(description="Legacy guard smoke for FreeKassa staging endpoints.")
    parser.add_argument(
        "--legacy-reconciliation",
        action="store_true",
        help="Required explicit acknowledgement: FreeKassa is legacy reconciliation tooling, not the public-beta checkout path.",
    )
    args = parser.parse_args()
    if not args.legacy_reconciliation:
        print(
            "[FAIL] FreeKassa staging smoke is legacy reconciliation-only. "
            "Use Lava.top probe tooling for public-beta paid checkout evidence, "
            "or pass --legacy-reconciliation for an intentional legacy check.",
            file=sys.stderr,
        )
        return 2

    api_base = require("SMOKE_API_BASE_URL").rstrip("/")
    checkout_secret = require("CHECKOUT_TICKET_SECRET")
    tg_id = int(require("SMOKE_TEST_TG_ID"))
    plan_code = env("SMOKE_PLAN_CODE", "1_month")
    promo_code = env("SMOKE_PROMO_CODE", "")
    campaign_key = env("SMOKE_CAMPAIGN_KEY", "staging_smoke")
    source = env("SMOKE_SOURCE", "site")
    ttl_seconds = int(env("CHECKOUT_TICKET_TTL_SECONDS", "900"))

    ticket = create_checkout_ticket(
        tg_id=tg_id,
        plan_code=plan_code,
        promo_code=promo_code,
        campaign_key=campaign_key,
        source=source,
        secret=checkout_secret,
        ttl_seconds=ttl_seconds,
    )

    status, body_text, order = http_json(
        f"{api_base}/api/payments/freekassa/orders/create-public",
        method="POST",
        payload={"plan_code": plan_code, "checkout_ticket": ticket, "currency": "RUB"},
    )
    if status not in {403, 503}:
        print(json.dumps(order, ensure_ascii=False, indent=2))
        raise SystemExit(f"Legacy FreeKassa public create was not blocked; HTTP {status}")
    detail = str(order.get("detail") or body_text or "")
    if "public beta RUB checkout" not in detail and "RUB checkout" not in detail:
        print(json.dumps(order, ensure_ascii=False, indent=2))
        raise SystemExit("Legacy FreeKassa public create returned an unexpected block reason")

    success_status, _ = http_text(f"{api_base}/pay/success")
    fail_status, _ = http_text(f"{api_base}/pay/fail")
    if success_status != 200 or fail_status != 200:
        raise SystemExit(f"Landing pages are unhealthy: success={success_status}, fail={fail_status}")

    print(json.dumps({
        "ok": True,
        "legacy_public_create_blocked": True,
        "blocked_status": status,
        "blocked_reason": detail,
        "success_status": success_status,
        "fail_status": fail_status,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

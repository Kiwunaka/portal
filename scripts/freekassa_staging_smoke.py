#!/usr/bin/env python3
from __future__ import annotations

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
    if status != 200:
        print(body_text)
        raise SystemExit(f"Order creation failed with HTTP {status}")
    payment_url = str(order.get("payment_url") or "").strip()
    order_id = str(order.get("order_id") or "").strip()
    if not payment_url or not order_id:
        print(json.dumps(order, ensure_ascii=False, indent=2))
        raise SystemExit("Order creation succeeded but payment_url or order_id is missing")

    success_status, _ = http_text(f"{api_base}/pay/success")
    fail_status, _ = http_text(f"{api_base}/pay/fail")
    if success_status != 200 or fail_status != 200:
        raise SystemExit(f"Landing pages are unhealthy: success={success_status}, fail={fail_status}")

    print(json.dumps({
        "ok": True,
        "order_id": order_id,
        "payment_url": payment_url,
        "amount_rub": order.get("amount_rub"),
        "discount_pct": order.get("discount_pct"),
        "success_status": success_status,
        "fail_status": fail_status,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

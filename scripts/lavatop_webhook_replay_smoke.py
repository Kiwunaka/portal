from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay a Lava.top success webhook against the local/API callback.")
    parser.add_argument("--url", default=os.getenv("LAVATOP_REPLAY_URL") or "http://127.0.0.1:8080/api/payments/result/lavatop")
    parser.add_argument("--order-id", required=True)
    parser.add_argument("--contract-id", default="replay-contract-id")
    parser.add_argument("--plan-code", default="start_99")
    parser.add_argument("--amount", type=float, default=99.0)
    parser.add_argument("--currency", default="RUB")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    payload = {
        "eventType": "payment.success",
        "contractId": args.contract_id,
        "amount": float(args.amount),
        "currency": args.currency.upper(),
        "status": "completed",
        "clientUtm": {
            "utm_source": "pokrov",
            "utm_medium": "replay",
            "utm_term": args.plan_code,
            "utm_content": args.order_id,
        },
    }
    if not args.live:
        print(json.dumps({"dry_run": True, "url": args.url, "payload": payload}, ensure_ascii=False, indent=2))
        return 0

    webhook_key = (os.getenv("LAVATOP_WEBHOOK_API_KEY") or "").strip()
    if not webhook_key:
        print("LAVATOP_WEBHOOK_API_KEY is required for replay", file=sys.stderr)
        return 2
    request = urllib.request.Request(
        args.url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json", "X-Api-Key": webhook_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(json.dumps({"status": response.status, "body": body[:800]}, ensure_ascii=False, indent=2))
            return 0 if response.status < 400 else 1
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(json.dumps({"status": exc.code, "body": body[:800]}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

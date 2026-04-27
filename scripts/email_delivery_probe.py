from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def _secret_headers() -> dict[str, str]:
    secret = (os.getenv("EMAIL_DELIVERY_WEBHOOK_SECRET") or "").strip()
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if secret:
        headers["X-Pokrov-Email-Secret"] = secret
        headers["Authorization"] = f"Bearer {secret}"
    return headers


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe the POKROV email delivery webhook.")
    parser.add_argument("--url", default=os.getenv("EMAIL_DELIVERY_WEBHOOK_URL") or os.getenv("EMAIL_AUTH_WEBHOOK_URL") or "")
    parser.add_argument("--email", default=os.getenv("EMAIL_PROBE_TO") or "operator@example.invalid")
    parser.add_argument("--kind", choices=["verify", "reset", "payment_access_key"], default="verify")
    parser.add_argument("--live", action="store_true", help="Actually POST to the configured relay.")
    args = parser.parse_args()

    payload: dict[str, object] = {"kind": args.kind, "email": args.email}
    if args.kind in {"verify", "reset"}:
        payload["token"] = "probe-token-redacted"
    else:
        payload.update(
            {
                "access_key": "POKROV-PROBE-KEY1",
                "order_id": "probe-order",
                "plan_code": "start_99",
                "plan_label": "POKROV Start",
                "days": 30,
            }
        )

    if not args.live:
        print(json.dumps({"dry_run": True, "url_configured": bool(args.url), "payload": payload}, ensure_ascii=False, indent=2))
        return 0
    if not args.url:
        print("EMAIL_DELIVERY_WEBHOOK_URL is not configured", file=sys.stderr)
        return 2

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(args.url, data=data, headers=_secret_headers(), method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(json.dumps({"status": response.status, "body": body[:500]}, ensure_ascii=False, indent=2))
            return 0 if response.status < 400 else 1
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(json.dumps({"status": exc.code, "body": body[:500]}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

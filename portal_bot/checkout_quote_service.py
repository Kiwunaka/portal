"""Signed, short-lived base checkout calculations; no commercial reservation."""

import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from uuid import uuid4

from commercial_offer_service import _secret_bytes, configured_offer_hold_ttl_seconds


PREFIX = "bq1"


class CheckoutQuoteError(ValueError):
    pass


def _digest(value):
    message = b"pokrov-base-quote-binding-v1\x00" + json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(_secret_bytes(), message, hashlib.sha256).hexdigest()


def _timestamp(now):
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return int(current.timestamp())


def quote_binding(*, tg_id, buyer_email, plan, pricing, revision):
    return _digest({
        "owner": ["telegram", str(tg_id)] if tg_id else ["email", buyer_email],
        "plan": plan["code"],
        "duration_days": int(plan.get("duration_days") or plan.get("days") or 30),
        "currency": "RUB",
        "pricing": pricing,
        "revision": revision,
    })


def sign_checkout_quote(binding, *, now=None):
    issued = _timestamp(now)
    payload = {"id": str(uuid4()), "binding": binding, "issued": issued,
               "expires": issued + configured_offer_hold_ttl_seconds()}
    encoded = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).decode().rstrip("=")
    message = f"{PREFIX}.{encoded}"
    signature = hmac.new(_secret_bytes(), message.encode(), hashlib.sha256).hexdigest()
    return f"{message}.{signature}", payload


def verify_checkout_quote(token, *, now=None, allow_expired=False):
    try:
        prefix, encoded, signature = token.split(".")
        if prefix != PREFIX:
            raise ValueError()
        expected = hmac.new(_secret_bytes(), f"{prefix}.{encoded}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError()
        payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
        if set(payload) != {"id", "binding", "issued", "expires"}:
            raise ValueError()
        current = _timestamp(now)
        if not allow_expired and payload["expires"] <= current:
            raise CheckoutQuoteError("checkout_quote_expired")
        return payload
    except CheckoutQuoteError:
        raise
    except (ValueError, TypeError, KeyError) as exc:
        raise CheckoutQuoteError("checkout_quote_invalid") from exc

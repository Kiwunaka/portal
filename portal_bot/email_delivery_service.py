from __future__ import annotations

import os
from typing import Any

import aiohttp

from config import env_bool, env_int


EMAIL_DELIVERY_WEBHOOK_URL = str(
    os.getenv("EMAIL_DELIVERY_WEBHOOK_URL") or os.getenv("EMAIL_AUTH_WEBHOOK_URL") or ""
).strip()
EMAIL_DELIVERY_WEBHOOK_SECRET = str(os.getenv("EMAIL_DELIVERY_WEBHOOK_SECRET") or "").strip()
EMAIL_DELIVERY_WEBHOOK_TIMEOUT_SECONDS = max(
    3,
    env_int(
        "EMAIL_DELIVERY_WEBHOOK_TIMEOUT_SECONDS",
        env_int("EMAIL_AUTH_WEBHOOK_TIMEOUT_SECONDS", 10),
    ),
)
EMAIL_AUTH_DEBUG_ECHO = env_bool("EMAIL_AUTH_DEBUG_ECHO", default=False)
EMAIL_AUTH_PUBLIC_ENABLED = env_bool("EMAIL_AUTH_PUBLIC_ENABLED", default=False)

EMAIL_DELIVERY_SECRET_HEADER = "X-Pokrov-Email-Secret"


def email_delivery_runtime_status() -> dict[str, Any]:
    delivery_url_configured = bool(EMAIL_DELIVERY_WEBHOOK_URL)
    delivery_secret_configured = bool(EMAIL_DELIVERY_WEBHOOK_SECRET)
    delivery_configured = bool(delivery_url_configured and delivery_secret_configured)
    blocked_reasons: list[str] = []
    if not EMAIL_AUTH_PUBLIC_ENABLED:
        blocked_reasons.append("public_email_disabled")
    if not delivery_url_configured:
        blocked_reasons.append("delivery_webhook_missing")
    if delivery_url_configured and not delivery_secret_configured:
        blocked_reasons.append("delivery_webhook_secret_missing")
    if EMAIL_AUTH_DEBUG_ECHO:
        blocked_reasons.append("debug_echo_enabled")

    enabled = bool(EMAIL_AUTH_PUBLIC_ENABLED and delivery_configured and not EMAIL_AUTH_DEBUG_ECHO)
    return {
        "ok": True,
        "enabled": enabled,
        "public_enabled": bool(EMAIL_AUTH_PUBLIC_ENABLED),
        "delivery_configured": delivery_configured,
        "delivery_url_configured": delivery_url_configured,
        "delivery_secret_configured": delivery_secret_configured,
        "debug_echo": bool(EMAIL_AUTH_DEBUG_ECHO),
        "mode": "webhook" if delivery_configured else "not_configured",
        "blocked_reasons": blocked_reasons,
    }


def _delivery_headers() -> dict[str, str]:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if EMAIL_DELIVERY_WEBHOOK_SECRET:
        headers[EMAIL_DELIVERY_SECRET_HEADER] = EMAIL_DELIVERY_WEBHOOK_SECRET
        headers["Authorization"] = f"Bearer {EMAIL_DELIVERY_WEBHOOK_SECRET}"
    return headers


async def deliver_email_message(payload: dict[str, Any]) -> dict[str, Any]:
    kind = str((payload or {}).get("kind") or "").strip()
    email = str((payload or {}).get("email") or "").strip()
    if EMAIL_AUTH_DEBUG_ECHO:
        return {"status": "debug_echo", "kind": kind, "email": email}
    if not EMAIL_DELIVERY_WEBHOOK_URL:
        return {"status": "not_configured", "kind": kind, "email": email}
    if not EMAIL_DELIVERY_WEBHOOK_SECRET:
        return {"status": "delivery_secret_missing", "kind": kind, "email": email}

    timeout = aiohttp.ClientTimeout(total=EMAIL_DELIVERY_WEBHOOK_TIMEOUT_SECONDS)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as client:
            async with client.post(
                EMAIL_DELIVERY_WEBHOOK_URL,
                json=dict(payload or {}),
                headers=_delivery_headers(),
            ) as response:
                text = (await response.text()).strip()
                if response.status >= 400:
                    return {
                        "status": "delivery_error",
                        "kind": kind,
                        "email": email,
                        "http_status": int(response.status),
                        "detail": text[:300] or None,
                    }
    except Exception as exc:
        return {
            "status": "delivery_error",
            "kind": kind,
            "email": email,
            "detail": str(exc)[:300],
        }
    return {"status": "sent", "kind": kind, "email": email, "mode": "webhook"}


async def deliver_auth_message(
    *,
    kind: str,
    email: str,
    token: str,
    linked_tg_id: int | None = None,
) -> dict[str, Any]:
    return await deliver_email_message(
        {
            "kind": str(kind),
            "email": str(email),
            "token": str(token),
            "linked_tg_id": int(linked_tg_id or 0) or None,
        }
    )


async def deliver_payment_access_key(
    *,
    email: str,
    access_key: str,
    order_id: str,
    plan_code: str,
    plan_label: str,
    days: int,
) -> dict[str, Any]:
    return await deliver_email_message(
        {
            "kind": "payment_access_key",
            "email": str(email),
            "access_key": str(access_key),
            "order_id": str(order_id),
            "plan_code": str(plan_code),
            "plan_label": str(plan_label),
            "days": int(days or 0),
        }
    )

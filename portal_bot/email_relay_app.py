from __future__ import annotations

import hmac
import os
import smtplib
from email.message import EmailMessage
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from email_delivery_service import EMAIL_DELIVERY_SECRET_HEADER


load_dotenv()


SMTP_HOST = str(os.getenv("EMAIL_RELAY_SMTP_HOST") or "").strip()
SMTP_PORT = int(str(os.getenv("EMAIL_RELAY_SMTP_PORT") or "587").strip() or "587")
SMTP_USERNAME = str(os.getenv("EMAIL_RELAY_SMTP_USERNAME") or "").strip()
SMTP_PASSWORD = str(os.getenv("EMAIL_RELAY_SMTP_PASSWORD") or "").strip()
SMTP_FROM = str(os.getenv("EMAIL_RELAY_FROM") or SMTP_USERNAME or "").strip()
SMTP_USE_TLS = str(os.getenv("EMAIL_RELAY_SMTP_TLS") or "true").strip().lower() in {"1", "true", "yes", "on"}
RELAY_SECRET = str(os.getenv("EMAIL_DELIVERY_WEBHOOK_SECRET") or "").strip()
PUBLIC_APP_URL = str(os.getenv("WEBAPP_URL") or "https://app.pokrov.space/").strip()


class EmailDeliveryIn(BaseModel):
    kind: str = Field(min_length=2, max_length=64)
    email: str = Field(min_length=5, max_length=200)
    token: str | None = Field(default=None, max_length=512)
    linked_tg_id: int | None = None
    access_key: str | None = Field(default=None, max_length=128)
    order_id: str | None = Field(default=None, max_length=160)
    plan_code: str | None = Field(default=None, max_length=64)
    plan_label: str | None = Field(default=None, max_length=160)
    days: int | None = None


app = FastAPI(title="POKROV email relay", version="1.0")


def _configured() -> bool:
    return bool(SMTP_HOST and SMTP_PORT and SMTP_FROM)


def _secret_ok(header_secret: str, authorization: str) -> bool:
    if not RELAY_SECRET:
        return True
    if header_secret and hmac.compare_digest(header_secret, RELAY_SECRET):
        return True
    prefix = "bearer "
    if authorization.lower().startswith(prefix):
        token = authorization[len(prefix) :].strip()
        return bool(token and hmac.compare_digest(token, RELAY_SECRET))
    return False


def _public_url(path: str, token: str) -> str:
    base = PUBLIC_APP_URL.rstrip("/") or "https://app.pokrov.space"
    return f"{base}/?{path}={token}"


def _app_url(path: str) -> str:
    base = PUBLIC_APP_URL.rstrip("/") or "https://app.pokrov.space"
    return f"{base}/{path.lstrip('/')}"


def _message_for(payload: EmailDeliveryIn) -> tuple[str, str]:
    kind = payload.kind.strip()
    if kind == "verify":
        token = str(payload.token or "").strip()
        return (
            "POKROV email verification",
            "Use this token to finish email verification:\n\n"
            f"{token}\n\n"
            f"Open: {_public_url('email_token', token)}\n",
        )
    if kind == "reset":
        token = str(payload.token or "").strip()
        return (
            "POKROV password reset",
            "Use this token to finish password reset:\n\n"
            f"{token}\n\n"
            f"Open: {_public_url('email_reset_token', token)}\n",
        )
    if kind == "payment_access_key":
        access_key = str(payload.access_key or "").strip()
        return (
            "POKROV access key",
            "Your paid access key is ready.\n\n"
            f"Access key: {access_key}\n"
            f"Plan: {payload.plan_label or payload.plan_code or 'POKROV'}\n"
            f"Days: {int(payload.days or 0)}\n"
            f"Order: {payload.order_id or ''}\n\n"
            f"Redeem it in the cabinet: {_app_url('redeem/')}\n",
        )
    raise HTTPException(status_code=400, detail="Unsupported email kind")


def _send_email(*, to_email: str, subject: str, body: str) -> None:
    if not _configured():
        raise HTTPException(status_code=503, detail="SMTP relay is not configured")
    message = EmailMessage()
    message["From"] = SMTP_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
        if SMTP_USE_TLS:
            smtp.starttls()
        if SMTP_USERNAME:
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.send_message(message)


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {"ok": True, "smtp_configured": _configured(), "auth_required": bool(RELAY_SECRET)}


@app.post("/email/deliver")
async def deliver(
    payload: EmailDeliveryIn,
    request: Request,
    x_pokrov_email_secret: str = Header(default="", alias=EMAIL_DELIVERY_SECRET_HEADER),
    authorization: str = Header(default=""),
) -> dict[str, Any]:
    if not _secret_ok(x_pokrov_email_secret, authorization):
        raise HTTPException(status_code=401, detail="Invalid relay secret")
    subject, body = _message_for(payload)
    try:
        _send_email(to_email=payload.email, subject=subject, body=body)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)[:300]) from exc
    return {"ok": True, "status": "sent", "kind": payload.kind, "email": payload.email}

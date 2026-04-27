from __future__ import annotations

import hmac
import html
import os
import smtplib
from email.message import EmailMessage
from typing import Any
from urllib.parse import quote

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from email_delivery_service import EMAIL_DELIVERY_SECRET_HEADER


load_dotenv()


SMTP_HOST = str(os.getenv("EMAIL_RELAY_SMTP_HOST") or "").strip()
SMTP_PORT = int(str(os.getenv("EMAIL_RELAY_SMTP_PORT") or "587").strip() or "587")
SMTP_USERNAME = str(os.getenv("EMAIL_RELAY_SMTP_USERNAME") or "").strip()
SMTP_PASSWORD = str(os.getenv("EMAIL_RELAY_SMTP_PASSWORD") or "").strip()
SMTP_FROM = str(os.getenv("EMAIL_RELAY_FROM") or "POKROV <noreply@pokrov.space>").strip()
SMTP_USE_TLS = str(os.getenv("EMAIL_RELAY_SMTP_TLS") or "true").strip().lower() in {"1", "true", "yes", "on"}
RELAY_SECRET = str(os.getenv("EMAIL_DELIVERY_WEBHOOK_SECRET") or "").strip()
PUBLIC_APP_URL = str(os.getenv("WEBAPP_URL") or "https://app.pokrov.space/").strip()
LOGO_URL = str(os.getenv("EMAIL_RELAY_LOGO_URL") or "https://pokrov.space/pokrov-logo.svg").strip()


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
    return f"{base}/?{path}={quote(token)}"


def _app_url(path: str) -> str:
    base = PUBLIC_APP_URL.rstrip("/") or "https://app.pokrov.space"
    return f"{base}/{path.lstrip('/')}"


def _email_html(*, title: str, intro: str, code_label: str, code: str, action_label: str, action_url: str) -> str:
    safe_title = html.escape(title)
    safe_intro = html.escape(intro)
    safe_code_label = html.escape(code_label)
    safe_code = html.escape(code)
    safe_action_label = html.escape(action_label)
    safe_action_url = html.escape(action_url, quote=True)
    safe_logo_url = html.escape(LOGO_URL, quote=True)
    return f"""<!doctype html>
<html lang="ru">
  <body style="margin:0;background:#f5f7fb;font-family:Arial,Helvetica,sans-serif;color:#142236;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f5f7fb;padding:28px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#ffffff;border:1px solid #e5ebf3;border-radius:16px;overflow:hidden;">
            <tr>
              <td style="padding:28px 28px 10px 28px;">
                <img src="{safe_logo_url}" width="52" height="52" alt="POKROV" style="display:block;border:0;margin-bottom:18px;" />
                <h1 style="font-size:22px;line-height:1.25;margin:0 0 12px 0;color:#102033;">{safe_title}</h1>
                <p style="font-size:15px;line-height:1.6;margin:0;color:#46566b;">{safe_intro}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:18px 28px;">
                <div style="font-size:13px;color:#7a8798;margin-bottom:8px;">{safe_code_label}</div>
                <div style="font-size:22px;line-height:1.35;letter-spacing:0.02em;font-weight:700;color:#102033;background:#f2f6fb;border:1px solid #dfe8f2;border-radius:10px;padding:14px 16px;word-break:break-all;">{safe_code}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:4px 28px 30px 28px;">
                <a href="{safe_action_url}" style="display:inline-block;background:#1565c0;color:#ffffff;text-decoration:none;font-weight:700;font-size:15px;border-radius:10px;padding:13px 18px;">{safe_action_label}</a>
                <p style="font-size:12px;line-height:1.55;margin:18px 0 0 0;color:#7a8798;">Если кнопка не открывается, скопируйте ссылку: <br><span style="word-break:break-all;">{safe_action_url}</span></p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def _message_for(payload: EmailDeliveryIn) -> tuple[str, str, str]:
    kind = payload.kind.strip()
    if kind == "verify":
        token = str(payload.token or "").strip()
        action_url = _public_url("email_token", token)
        subject = "Подтверждение email в POKROV"
        body = (
            "Подтвердите email для входа в POKROV.\n\n"
            f"Код подтверждения:\n{token}\n\n"
            f"Открыть кабинет: {action_url}\n\n"
            "Если вы не запрашивали это письмо, просто проигнорируйте его.\n"
        )
        return (
            subject,
            body,
            _email_html(
                title=subject,
                intro="Введите этот код в окне входа или откройте кабинет по кнопке ниже.",
                code_label="Код подтверждения",
                code=token,
                action_label="Открыть кабинет",
                action_url=action_url,
            ),
        )
    if kind == "reset":
        token = str(payload.token or "").strip()
        action_url = _public_url("email_reset_token", token)
        subject = "Сброс пароля в POKROV"
        body = (
            "Вы запросили сброс пароля для POKROV.\n\n"
            f"Код сброса:\n{token}\n\n"
            f"Открыть кабинет: {action_url}\n\n"
            "Если вы не запрашивали сброс, просто проигнорируйте это письмо.\n"
        )
        return (
            subject,
            body,
            _email_html(
                title=subject,
                intro="Введите этот код в окне восстановления доступа или откройте кабинет по кнопке ниже.",
                code_label="Код сброса",
                code=token,
                action_label="Открыть кабинет",
                action_url=action_url,
            ),
        )
    if kind == "payment_access_key":
        access_key = str(payload.access_key or "").strip()
        action_url = _app_url("redeem/")
        subject = "Ключ доступа POKROV"
        body = (
            "Ваш ключ доступа готов.\n\n"
            f"Ключ доступа:\n{access_key}\n\n"
            f"Тариф: {payload.plan_label or payload.plan_code or 'POKROV'}\n"
            f"Дней: {int(payload.days or 0)}\n"
            f"Заказ: {payload.order_id or ''}\n\n"
            f"Активировать ключ в кабинете: {action_url}\n"
        )
        return (
            subject,
            body,
            _email_html(
                title=subject,
                intro="Спасибо за оплату. Скопируйте ключ и активируйте его в кабинете.",
                code_label="Ключ доступа",
                code=access_key,
                action_label="Активировать ключ",
                action_url=action_url,
            ),
        )
    raise HTTPException(status_code=400, detail="Unsupported email kind")


def _send_email(*, to_email: str, subject: str, body: str, html_body: str) -> None:
    if not _configured():
        raise HTTPException(status_code=503, detail="SMTP relay is not configured")
    message = EmailMessage()
    message["From"] = SMTP_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    message.add_alternative(html_body, subtype="html")
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
    subject, body, html_body = _message_for(payload)
    try:
        _send_email(to_email=payload.email, subject=subject, body=body, html_body=html_body)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)[:300]) from exc
    return {"ok": True, "status": "sent", "kind": payload.kind, "email": payload.email}

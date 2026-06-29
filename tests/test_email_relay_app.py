from __future__ import annotations

import importlib.util
import sys
from email.message import EmailMessage
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]


def _load_email_relay_app(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "portal_bot"))
    monkeypatch.setenv("EMAIL_RELAY_SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("EMAIL_RELAY_SMTP_PORT", "587")
    monkeypatch.setenv("EMAIL_RELAY_FROM", "POKROV <noreply@pokrov.space>")
    monkeypatch.setenv("EMAIL_DELIVERY_WEBHOOK_SECRET", "relay-secret")
    monkeypatch.setenv("WEBAPP_URL", "https://app.pokrov.space/")

    module_path = ROOT / "portal_bot" / "email_relay_app.py"
    spec = importlib.util.spec_from_file_location("email_relay_app_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_email_relay_healthz_reports_configuration_and_auth(monkeypatch) -> None:
    module = _load_email_relay_app(monkeypatch)
    client = TestClient(module.app)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "smtp_configured": True,
        "auth_required": True,
    }


def test_email_relay_deliver_requires_secret_before_send(monkeypatch) -> None:
    module = _load_email_relay_app(monkeypatch)
    client = TestClient(module.app)

    response = client.post(
        "/email/deliver",
        json={"kind": "verify", "email": "user@example.test", "token": "tok"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid relay secret"


def test_email_relay_private_config_secret_and_url_helpers(monkeypatch) -> None:
    module = _load_email_relay_app(monkeypatch)

    assert module._configured() is True
    assert module._secret_ok("relay-secret", "") is True
    assert module._secret_ok("", "Bearer relay-secret") is True
    assert module._secret_ok("wrong", "") is False
    assert module._public_url("email_token", "tok en/+=") == (
        "https://app.pokrov.space/?email_token=tok%20en/%2B%3D"
    )
    assert module._app_url("/redeem/") == "https://app.pokrov.space/redeem/"


def test_email_relay_private_logo_helpers_attach_inline_logo(monkeypatch, tmp_path) -> None:
    module = _load_email_relay_app(monkeypatch)
    logo = tmp_path / "logo.jpg"
    logo.write_bytes(b"fake-jpeg")
    module.LOGO_PATH = str(logo)

    assert module._logo_available() is True
    assert module._logo_mime_subtype() == "jpeg"
    assert module._logo_src() == f"cid:{module.LOGO_CID}"

    message = EmailMessage()
    message.set_content("plain")
    message.add_alternative("<p>html</p>", subtype="html")
    module._attach_logo(message)

    related_parts = [
        part
        for part in message.walk()
        if part.get_content_maintype() == "image"
        and part.get("Content-ID") == f"<{module.LOGO_CID}>"
    ]
    assert related_parts

    module.LOGO_PATH = str(tmp_path / "missing.png")
    assert module._logo_available() is False
    assert module._logo_src() == module.LOGO_URL


def test_email_relay_private_html_and_message_builders_escape_and_route(monkeypatch) -> None:
    module = _load_email_relay_app(monkeypatch)

    html = module._email_html(
        title="<script>",
        intro="intro & copy",
        code_label="code",
        code="A&B",
        action_label="open",
        action_url='https://app.pokrov.space/?email_token=A&B"',
    )

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "intro &amp; copy" in html
    assert "A&amp;B" in html
    assert "email_token=A&amp;B&quot;" in html

    verify_subject, verify_body, verify_html = module._message_for(
        module.EmailDeliveryIn(kind="verify", email="user@example.test", token="verify-token")
    )
    reset_subject, reset_body, reset_html = module._message_for(
        module.EmailDeliveryIn(kind="reset", email="user@example.test", token="reset-token")
    )
    paid_subject, paid_body, paid_html = module._message_for(
        module.EmailDeliveryIn(
            kind="payment_access_key",
            email="user@example.test",
            access_key="ACCESS-123",
            plan_label="Start",
            days=30,
            order_id="ord_1",
        )
    )

    assert "verify-token" in verify_body
    assert "email_token=verify-token" in verify_html
    assert "reset-token" in reset_body
    assert "email_reset_token=reset-token" in reset_html
    assert "ACCESS-123" in paid_body
    assert "redeem/" in paid_html
    assert verify_subject
    assert reset_subject
    assert paid_subject

    try:
        module._message_for(module.EmailDeliveryIn(kind="unknown", email="user@example.test"))
    except module.HTTPException as exc:
        assert exc.status_code == 400
    else:  # pragma: no cover - keeps the assertion explicit
        raise AssertionError("unsupported email kind should fail closed")


def test_email_relay_private_send_email_fails_closed_when_unconfigured(monkeypatch) -> None:
    module = _load_email_relay_app(monkeypatch)
    module.RESEND_API_KEY = ""
    module.SMTP_HOST = ""
    module.SMTP_FROM = ""

    try:
        module._send_email(
            to_email="user@example.test",
            subject="subject",
            body="body",
            html_body="<p>body</p>",
        )
    except module.HTTPException as exc:
        assert exc.status_code == 503
        assert exc.detail == "Email relay is not configured"
    else:  # pragma: no cover - keeps the assertion explicit
        raise AssertionError("unconfigured email relay should fail closed")

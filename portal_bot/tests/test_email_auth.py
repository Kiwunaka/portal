from __future__ import annotations

import asyncio
import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

REPO_ROOT = PORTAL_BOT_DIR.parent


def _load_api(
    monkeypatch,
    tmp_path: Path,
    *,
    email_public_ready: bool = False,
    email_delivery_secret_ready: bool = True,
):
    db_path = tmp_path / "portal-email-auth.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("BOT_TOKEN", "777000:test-bot-token")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "portal-test-secret")
    monkeypatch.setenv("EMAIL_AUTH_DEBUG_ECHO", "false" if email_public_ready else "true")
    monkeypatch.setenv("EMAIL_AUTH_PUBLIC_ENABLED", "true" if email_public_ready else "false")
    if email_public_ready:
        monkeypatch.setenv("EMAIL_DELIVERY_WEBHOOK_URL", "https://relay.pokrov.test/email/deliver")
        if email_delivery_secret_ready:
            monkeypatch.setenv("EMAIL_DELIVERY_WEBHOOK_SECRET", "relay-secret")
        else:
            monkeypatch.delenv("EMAIL_DELIVERY_WEBHOOK_SECRET", raising=False)
    else:
        monkeypatch.delenv("EMAIL_DELIVERY_WEBHOOK_URL", raising=False)
        monkeypatch.delenv("EMAIL_DELIVERY_WEBHOOK_SECRET", raising=False)
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.pokrov.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "pokrov.test")
    monkeypatch.setenv("WEBAPP_URL", "https://app.pokrov.test/")
    monkeypatch.setenv("SUPPORT_UPLOAD_DIR", str((tmp_path / "support-uploads").resolve()))
    monkeypatch.setenv("SUPPORT_AI_ENABLED", "false")
    monkeypatch.setenv("SUPPORT_AI_API_KEY", "")

    for name in [
        "api",
        "helpbot",
        "config",
        "db",
        "email_auth_service",
        "email_delivery_service",
        "app_first_service",
        "migrations",
        "web_auth_service",
        "control_panel",
        "nodes_repo",
        "tickets_repo",
        "events_service",
        "offers_service",
        "pay_attempts_service",
        "points_service",
        "free_cycle_service",
        "gift_cards_service",
        "payment_providers",
        "support_ai_service",
        "support_agent_context",
        "support_agent_grounding",
        "support_agent_harness",
        "support_agent_knowledge",
        "support_agent_policy",
        "support_agent_provider",
        "support_agent_safety",
        "support_agent_service",
        "support_agent_sessions",
        "support_agent_state",
    ]:
        monkeypatch.delitem(sys.modules, name, raising=False)

    return importlib.import_module("api")


def _capture_auth_delivery(monkeypatch, api):
    captured: dict[str, str] = {}

    async def fake_deliver_auth_message(*, kind: str, email: str, token: str, linked_tg_id: int | None = None):
        captured[str(kind)] = str(token)
        return {"status": "sent", "kind": str(kind), "email": str(email), "mode": "test"}

    monkeypatch.setattr(api, "deliver_auth_message", fake_deliver_auth_message)
    return captured


def _install_fake_panel(monkeypatch, api):
    class FakePanel:
        async def add_client(self, **_kwargs):
            return True

        async def close(self):
            return None

    monkeypatch.setattr(api, "ControlPanel", FakePanel)


def _recovery_http_fixture(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ADMIN_ID", "9000000000000")
    api = _load_api(monkeypatch, tmp_path, email_public_ready=True)
    _install_fake_panel(monkeypatch, api)
    captured = _capture_auth_delivery(monkeypatch, api)

    async def fake_telegram_send_message(*_args, **_kwargs):
        return True

    monkeypatch.setattr(api, "_telegram_send_message", fake_telegram_send_message)
    client = TestClient(api.app)

    start = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-recovery-http-original",
            "device_name": "Original phone",
            "platform": "android",
            "app_version": "1.0.0-rc.1",
        },
    )
    assert start.status_code == 200, "recovery-http-start"
    normal_headers = {"Authorization": f"Bearer {start.json()['access_token']}"}

    register = client.post(
        "/api/auth/email/register",
        headers=normal_headers,
        json={"email": "recovery-http@pokrov.test", "password": "StrongPass123!"},
    )
    assert register.status_code == 200, "recovery-http-register"
    verify = client.post("/api/auth/email/verify", json={"token": str(captured["verify"])})
    assert verify.status_code == 200, "recovery-http-verify"

    otp_start = client.post("/api/auth/email/otp/start", json={"email": "recovery-http@pokrov.test"})
    assert otp_start.status_code == 200, "recovery-http-otp-start"
    otp_finish = client.post(
        "/api/auth/email/otp/finish",
        headers=normal_headers,
        json={"email": "recovery-http@pokrov.test", "code": str(captured["login_otp"])},
    )
    assert otp_finish.status_code == 200, "recovery-http-otp-finish"

    rotate = client.post("/api/client/recovery-code/rotate", headers=normal_headers)
    assert rotate.status_code == 200, "recovery-http-rotate"
    exchange = client.post(
        "/api/client/recovery/exchange",
        json={
            "code": str(rotate.json()["recovery_code"]),
            "install_id": "install-recovery-http-new",
            "device_name": "New PC",
            "platform": "windows",
            "os_version": "11",
            "app_version": "1.0.0-rc.1",
        },
    )
    assert exchange.status_code == 200, "recovery-http-exchange"
    recovery_headers = {"Authorization": f"Bearer {exchange.json()['access_token']}"}
    return api, client, normal_headers, recovery_headers


def _seed_ticket_with_private_attachment(client: TestClient, normal_headers: dict[str, str]):
    upload = client.post(
        "/api/tickets/uploads",
        headers={**normal_headers, "Content-Type": "image/png", "X-Upload-Filename": "private-screen.png"},
        content=b"\x89PNG\r\n\x1a\nprivate-test-payload",
    )
    assert upload.status_code == 200, "private-ticket-upload"
    attachment = dict(upload.json()["attachment"])
    attachment_payload = dict(upload.json()["attachment_payload"])
    create = client.post(
        "/api/tickets",
        headers=normal_headers,
        json={
            "subject": "Private attachment",
            "body": "Initial message with an attachment",
            "media_type": attachment["media_type"],
            "media_file_id": attachment["media_file_id"],
            "media_payload": attachment["media_payload"],
        },
    )
    assert create.status_code == 200, "private-ticket-create"
    ticket = dict(create.json()["ticket"])
    assert any("media_file_id" in message for message in ticket["messages"]), "normal-ticket-media-contract"
    return int(ticket["id"]), str(attachment_payload["url"])


def _assert_recovery_forbidden(response, case_name: str) -> None:
    assert response.status_code == 403, case_name
    assert response.headers.get("X-POKROV-Auth-Error") == "recovery_scope_forbidden", case_name


def _messages_are_text_only(ticket: dict) -> bool:
    media_keys = {"media_type", "media_file_id", "media_payload"}
    messages = list(ticket.get("messages") or [])
    return bool(messages) and all(media_keys.isdisjoint(message) for message in messages)


def test_owned_backend_files_do_not_use_datetime_utcnow():
    owned_paths = [
        REPO_ROOT / "portal_bot" / "models.py",
        REPO_ROOT / "portal_bot" / "bot.py",
        REPO_ROOT / "portal_bot" / "web_auth_service.py",
        REPO_ROOT / "portal_bot" / "email_auth_service.py",
        REPO_ROOT / "tests" / "test_api_auth_and_tickets.py",
    ]

    offenders: list[str] = []
    for path in owned_paths:
        if ".utcnow" in path.read_text(encoding="utf-8"):
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == []


def test_models_datetime_defaults_use_shared_utc_helper():
    import models

    defaults = [
        models.User.__table__.c.created_at.default.arg,
        models.WebEmailIdentity.__table__.c.created_at.default.arg,
        models.WebEmailIdentity.__table__.c.updated_at.default.arg,
        models.WebEmailToken.__table__.c.created_at.default.arg,
    ]

    for default in defaults:
        assert getattr(default, "__module__", "") == "models"
        assert getattr(default, "__name__", "") == "_utcnow"


def test_email_register_verify_login_and_session(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path, email_public_ready=True)
    captured = _capture_auth_delivery(monkeypatch, api)
    client = TestClient(api.app)

    register = client.post(
        "/api/auth/email/register",
        json={
            "email": "reader@pokrov.test",
            "password": "StrongPass123!",
            "display_name": "Reader",
        },
    )

    assert register.status_code == 200, register.text
    register_body = register.json()
    assert register_body["ok"] is True
    assert register_body["verification_required"] is True
    verify_token = str(captured["verify"])
    assert verify_token

    verify = client.post(
        "/api/auth/email/verify",
        json={"token": verify_token},
    )

    assert verify.status_code == 200, verify.text
    verify_body = verify.json()
    assert verify_body["ok"] is True
    assert verify_body["token"]
    assert verify_body["user"]["email"] == "reader@pokrov.test"

    session = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {verify_body['token']}"},
    )

    assert session.status_code == 200, session.text
    session_body = session.json()
    assert session_body["user"]["auth_type"] == "email"
    assert session_body["user"]["auth_origin"] == "email"
    assert session_body["user"]["email"] == "reader@pokrov.test"
    assert session_body["user"]["linked_identities"]["email"]["verified"] is True

    login = client.post(
        "/api/auth/email/login",
        json={"email": "reader@pokrov.test", "password": "StrongPass123!"},
    )

    assert login.status_code == 200, login.text
    login_body = login.json()
    assert login_body["ok"] is True
    assert login_body["user"]["email"] == "reader@pokrov.test"


def test_email_status_stays_disabled_in_debug_mode(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    status = client.get("/api/auth/email/status")

    assert status.status_code == 200, status.text
    body = status.json()
    assert body["ok"] is True
    assert body["enabled"] is False
    assert "debug_echo_enabled" in body["blocked_reasons"]


def test_email_status_requires_delivery_secret(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path, email_public_ready=True, email_delivery_secret_ready=False)
    client = TestClient(api.app)

    status = client.get("/api/auth/email/status")

    assert status.status_code == 200, status.text
    body = status.json()
    assert body["ok"] is True
    assert body["enabled"] is False
    assert body["public_enabled"] is True
    assert body["delivery_configured"] is True
    assert body["delivery_secret_configured"] is False
    assert "delivery_webhook_secret_missing" in body["blocked_reasons"]


def test_email_register_and_recovery_start_require_public_delivery(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    register = client.post(
        "/api/auth/email/register",
        json={"email": "blocked@pokrov.test", "password": "StrongPass123!"},
    )

    assert register.status_code == 503, register.text
    assert "Email-вход пока недоступен" in register.text

    recovery = client.post(
        "/api/auth/email/recovery/start",
        json={"email": "blocked@pokrov.test"},
    )

    assert recovery.status_code == 503, recovery.text
    assert "Email-вход пока недоступен" in recovery.text


def test_email_delivery_posts_secret_header(monkeypatch):
    monkeypatch.setenv("EMAIL_AUTH_DEBUG_ECHO", "false")
    monkeypatch.setenv("EMAIL_DELIVERY_WEBHOOK_URL", "https://relay.pokrov.test/email/deliver")
    monkeypatch.setenv("EMAIL_DELIVERY_WEBHOOK_SECRET", "relay-secret")
    monkeypatch.delitem(sys.modules, "email_delivery_service", raising=False)
    service = importlib.import_module("email_delivery_service")
    capture: dict[str, object] = {}

    class FakeResponse:
        status = 202

        async def text(self) -> str:
            return "ok"

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

    class FakeSession:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, url: str, *, json: dict | None = None, headers: dict | None = None):
            capture["url"] = url
            capture["json"] = dict(json or {})
            capture["headers"] = dict(headers or {})
            return FakeResponse()

    monkeypatch.setattr(service.aiohttp, "ClientSession", FakeSession)

    result = asyncio.run(
        service.deliver_auth_message(
            kind="verify",
            email="reader@pokrov.test",
            token="verify-token",
            linked_tg_id=8000000000000,
        )
    )

    assert result["status"] == "sent"
    assert capture["url"] == "https://relay.pokrov.test/email/deliver"
    assert capture["json"]["token"] == "verify-token"
    assert capture["headers"]["X-Pokrov-Email-Secret"] == "relay-secret"
    assert capture["headers"]["Authorization"] == "Bearer relay-secret"


def test_email_register_can_link_to_existing_user(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path, email_public_ready=True)
    captured = _capture_auth_delivery(monkeypatch, api)
    client = TestClient(api.app)

    db = api.SessionLocal()
    try:
        db.add(
            api.User(
                tg_id=1001,
                username="alice",
                uuid="a2c28474-4bbb-4b58-a44c-d5f8de0a1001",
                email="user_1001",
                sub_type="FREE",
                current_plan_code="free_monthly",
                is_active=True,
                tos_accepted=True,
            )
        )
        db.commit()
    finally:
        db.close()

    current_session_token = api.create_web_session_token(tg_id=1001, username="alice")
    register = client.post(
        "/api/auth/email/register",
        headers={"Authorization": f"Bearer {current_session_token}"},
        json={
            "email": "alice@pokrov.test",
            "password": "StrongPass123!",
            "display_name": "Alice",
        },
    )

    assert register.status_code == 200, register.text
    verify_token = str(captured["verify"])

    verify = client.post("/api/auth/email/verify", json={"token": verify_token})
    assert verify.status_code == 200, verify.text
    verify_body = verify.json()
    assert verify_body["user"]["id"] == 1001
    assert verify_body["user"]["email"] == "alice@pokrov.test"

    session = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {verify_body['token']}"},
    )

    assert session.status_code == 200, session.text
    session_body = session.json()
    assert session_body["user"]["id"] == 1001
    assert session_body["user"]["linked_identities"]["email"]["email"] == "alice@pokrov.test"


def test_email_register_from_app_session_links_to_app_account(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path, email_public_ready=True)
    _install_fake_panel(monkeypatch, api)
    captured = _capture_auth_delivery(monkeypatch, api)
    client = TestClient(api.app)

    start = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-email-link-app",
            "device_name": "Pixel 9",
            "platform": "android",
            "os_version": "15",
            "app_version": "1.0.0",
            "locale": "ru",
            "time_zone": "Europe/Moscow",
            "trial_days": 5,
        },
    )

    assert start.status_code == 200, start.text
    app_account_id = int(start.json()["account_id"])
    app_session_token = str(start.json()["session_token"])

    register = client.post(
        "/api/auth/email/register",
        headers={"Authorization": f"Bearer {app_session_token}"},
        json={
            "email": "app-linked@pokrov.test",
            "password": "StrongPass123!",
            "display_name": "App Linked",
        },
    )

    assert register.status_code == 200, register.text
    verify = client.post("/api/auth/email/verify", json={"token": str(captured["verify"])})
    assert verify.status_code == 200, verify.text
    verify_body = verify.json()
    assert int(verify_body["user"]["id"]) == app_account_id
    assert verify_body["user"]["email"] == "app-linked@pokrov.test"

    login = client.post(
        "/api/auth/email/login",
        json={"email": "app-linked@pokrov.test", "password": "StrongPass123!"},
    )

    assert login.status_code == 200, login.text
    login_body = login.json()
    assert int(login_body["user"]["id"]) == app_account_id

    session = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {login_body['token']}"},
    )

    assert session.status_code == 200, session.text
    session_body = session.json()
    assert int(session_body["user"]["id"]) == app_account_id
    assert session_body["user"]["auth_type"] == "email"
    assert session_body["user"]["auth_origin"] == "email"
    assert session_body["user"]["email"] == "app-linked@pokrov.test"
    assert session_body["user"]["device_name"] == "Pixel 9"

    db = api.SessionLocal()
    try:
        users = db.query(api.User).all()
        assert [int(user.tg_id) for user in users] == [app_account_id]
        user = users[0]
        assert bool(user.is_app_user) is True
        assert user.app_install_id == "install-email-link-app"
        identity = db.query(api.WebEmailIdentity).filter_by(email_norm="app-linked@pokrov.test").first()
        assert identity is not None
        assert int(identity.linked_tg_id) == app_account_id
        from models import AccountIdentity

        canonical_email = (
            db.query(AccountIdentity)
            .filter_by(
                account_id=str(user.account_id),
                kind="email",
                provider="email",
                subject_norm="app-linked@pokrov.test",
            )
            .one()
        )
        assert canonical_email.verified_at is not None
    finally:
        db.close()


def test_email_account_linked_to_admin_telegram_does_not_grant_admin_access(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_ID", "777001")
    api = _load_api(monkeypatch, tmp_path, email_public_ready=True)
    captured = _capture_auth_delivery(monkeypatch, api)
    client = TestClient(api.app)

    register = client.post(
        "/api/auth/email/register",
        json={
            "email": "operator@pokrov.test",
            "password": "StrongPass123!",
            "display_name": "Operator",
        },
    )
    assert register.status_code == 200, register.text
    verify = client.post("/api/auth/email/verify", json={"token": str(captured["verify"])})
    assert verify.status_code == 200, verify.text
    account_id = int(verify.json()["user"]["id"])

    db = api.SessionLocal()
    try:
        user = db.query(api.User).filter(api.User.tg_id == account_id).first()
        assert user is not None
        user.linked_telegram_id = 777001
        user.linked_telegram_username = "admin_owner"
        user.linked_telegram_linked_at = api._utcnow()
        db.commit()
    finally:
        db.close()

    login = client.post(
        "/api/auth/email/login",
        json={"email": "operator@pokrov.test", "password": "StrongPass123!"},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['token']}"}

    profile = client.get(f"/api/user/{account_id}", headers=headers)
    assert profile.status_code == 200, profile.text
    profile_body = profile.json()
    assert profile_body["is_admin"] is False
    assert profile_body["linked_identities"]["telegram"]["id"] == 777001
    assert profile_body["linked_identities"]["email"]["email"] == "operator@pokrov.test"

    admin_summary = client.get("/api/admin/summary", headers=headers)
    assert admin_summary.status_code == 403, admin_summary.text


def test_telegram_session_shows_email_from_linked_email_account(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path, email_public_ready=True)
    captured = _capture_auth_delivery(monkeypatch, api)
    client = TestClient(api.app)

    register = client.post(
        "/api/auth/email/register",
        json={"email": "linked@pokrov.test", "password": "StrongPass123!"},
    )
    assert register.status_code == 200, register.text
    verify = client.post("/api/auth/email/verify", json={"token": str(captured["verify"])})
    assert verify.status_code == 200, verify.text
    account_id = int(verify.json()["user"]["id"])

    api._ensure_user_row_for_login(tg_id=777001, username="linked_owner")
    db = api.SessionLocal()
    try:
        telegram_user = db.query(api.User).filter(api.User.tg_id == 777001).one()
        assert telegram_user.account_id
        user = db.query(api.User).filter(api.User.tg_id == account_id).first()
        assert user is not None
        user.linked_telegram_id = 777001
        user.linked_telegram_username = "linked_owner"
        user.linked_telegram_linked_at = api._utcnow()
        db.commit()
    finally:
        db.close()

    token = api.create_web_session_token(
        tg_id=777001,
        username="linked_owner",
        auth_type="telegram",
        auth_origin="telegram",
    )
    headers = {"Authorization": f"Bearer {token}"}

    session = client.get("/api/auth/session", headers=headers)
    assert session.status_code == 200, session.text
    session_body = session.json()
    assert session_body["user"]["email"] == "linked@pokrov.test"
    assert session_body["user"]["linked_identities"]["email"]["email"] == "linked@pokrov.test"

    profile = client.get("/api/user/777001", headers=headers)
    assert profile.status_code == 200, profile.text
    profile_body = profile.json()
    assert profile_body["email"] == "linked@pokrov.test"
    assert profile_body["linked_identities"]["email"]["email"] == "linked@pokrov.test"


def test_email_recovery_resets_password(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path, email_public_ready=True)
    captured = _capture_auth_delivery(monkeypatch, api)
    client = TestClient(api.app)

    register = client.post(
        "/api/auth/email/register",
        json={
            "email": "recover@pokrov.test",
            "password": "StrongPass123!",
        },
    )
    assert register.status_code == 200, register.text
    verify_token = str(captured["verify"])
    verify = client.post("/api/auth/email/verify", json={"token": verify_token})
    assert verify.status_code == 200, verify.text

    recovery_start = client.post(
        "/api/auth/email/recovery/start",
        json={"email": "recover@pokrov.test"},
    )

    assert recovery_start.status_code == 200, recovery_start.text
    recovery_token = str(captured["reset"])
    assert recovery_token

    recovery_finish = client.post(
        "/api/auth/email/recovery/finish",
        json={"token": recovery_token, "password": "FreshPass456!"},
    )

    assert recovery_finish.status_code == 200, recovery_finish.text
    assert recovery_finish.json()["ok"] is True

    old_login = client.post(
        "/api/auth/email/login",
        json={"email": "recover@pokrov.test", "password": "StrongPass123!"},
    )
    assert old_login.status_code == 401, old_login.text

    new_login = client.post(
        "/api/auth/email/login",
        json={"email": "recover@pokrov.test", "password": "FreshPass456!"},
    )
    assert new_login.status_code == 200, new_login.text


def test_email_register_rejects_duplicate_verified_identity(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path, email_public_ready=True)
    captured = _capture_auth_delivery(monkeypatch, api)
    client = TestClient(api.app)

    first_register = client.post(
        "/api/auth/email/register",
        json={"email": "dupe@pokrov.test", "password": "StrongPass123!"},
    )
    assert first_register.status_code == 200, first_register.text
    verify_token = str(captured["verify"])
    verify = client.post("/api/auth/email/verify", json={"token": verify_token})
    assert verify.status_code == 200, verify.text

    duplicate = client.post(
        "/api/auth/email/register",
        json={"email": "dupe@pokrov.test", "password": "SecondPass456!"},
    )

    assert duplicate.status_code == 409, duplicate.text


def test_email_otp_login_is_generic_single_use_and_password_remains_compatibility(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path, email_public_ready=True)
    captured = _capture_auth_delivery(monkeypatch, api)
    client = TestClient(api.app)

    register = client.post(
        "/api/auth/email/register",
        json={"email": "otp-owner@pokrov.test", "password": "StrongPass123!"},
    )
    assert register.status_code == 200, register.text
    verify = client.post("/api/auth/email/verify", json={"token": str(captured["verify"])})
    assert verify.status_code == 200, verify.text

    unknown = client.post("/api/auth/email/otp/start", json={"email": "missing@pokrov.test"})
    assert unknown.status_code == 200, unknown.text
    assert unknown.json()["otp_requested"] is True
    assert "identity" not in unknown.json()

    start = client.post("/api/auth/email/otp/start", json={"email": "OTP-OWNER@pokrov.test"})
    assert start.status_code == 200, start.text
    assert start.json()["otp_requested"] is True
    assert start.json() == unknown.json()
    code = str(captured["login_otp"])
    assert len(code) == 6 and code.isdigit()

    finish = client.post(
        "/api/auth/email/otp/finish",
        json={"email": "otp-owner@pokrov.test", "code": code},
    )
    assert finish.status_code == 200, finish.text
    assert finish.json()["token"]
    assert finish.json()["auth_method"] == "email_otp"

    replay = client.post(
        "/api/auth/email/otp/finish",
        json={"email": "otp-owner@pokrov.test", "code": code},
    )
    assert replay.status_code == 401, replay.text
    assert replay.headers["X-POKROV-Auth-Error"] == "email_otp_invalid"

    compatibility = client.post(
        "/api/auth/email/login",
        json={"email": "otp-owner@pokrov.test", "password": "StrongPass123!"},
    )
    assert compatibility.status_code == 200, compatibility.text
    assert compatibility.json()["auth_method"] == "password_compatibility"


def test_api_support_ai_persistence_failure_logs_only_fixed_code(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    api.SUPPORT_AI_CONFIG.enabled = True
    api.SUPPORT_AI_CONFIG.api_key = "synthetic-test-key"
    api.SUPPORT_AI_CONFIG.min_interval_seconds = 0
    api.support_ai_last_reply_at.clear()

    async def fake_generate_support_reply(*_args, **_kwargs):
        return SimpleNamespace(reply="Synthetic assistant reply")

    class FailingSession:
        def __init__(self, *, rollback_fails: bool, close_fails: bool):
            self.rollback_fails = rollback_fails
            self.close_fails = close_fails
            self.rollback_attempted = False
            self.closed = False

        def rollback(self):
            self.rollback_attempted = True
            if self.rollback_fails:
                raise RuntimeError("rollback failure marker")

        def close(self):
            self.closed = True
            if self.close_fails:
                raise RuntimeError("close failure marker")

    monkeypatch.setattr(api.SUPPORT_AGENT_SERVICE, "generate", fake_generate_support_reply)
    monkeypatch.setattr(
        api,
        "get_ticket_by_id",
        lambda _session, ticket_id: SimpleNamespace(id=int(ticket_id), user_tg_id=7101),
    )

    def fail_to_append(*_args, **_kwargs):
        raise RuntimeError("synthetic persistence detail echoed the assistant body")

    monkeypatch.setattr(api, "add_ticket_message", fail_to_append)
    for rollback_fails, close_fails in ((False, False), (True, False), (False, True), (True, True)):
        session = FailingSession(rollback_fails=rollback_fails, close_fails=close_fails)
        monkeypatch.setattr(api, "SessionLocal", lambda session=session: session)
        with unittest.TestCase().assertLogs("api", level="WARNING") as captured:
            appended = asyncio.run(
                api._maybe_append_support_ai_reply(
                    ticket_id=71,
                    user_tg_id=7101,
                    text="Synthetic user message",
                )
            )

        expected = [
            "WARNING:api:support AI ticket append failed code=support_reply_persist_error"
        ]
        if close_fails:
            expected.append(
                "WARNING:api:support AI ticket session cleanup failed code=support_reply_cleanup_error"
            )
        fixed_log_only = captured.output == expected
        assert fixed_log_only, "api-support-ai-persistence-log"
        assert appended is False, "api-support-ai-persistence-result"
        assert session.rollback_attempted and session.closed, "api-support-ai-persistence-cleanup"


def test_helpbot_support_ai_persistence_failure_logs_only_fixed_code(monkeypatch, tmp_path):
    monkeypatch.setenv("HELP_BOT_TOKEN", "777000:test-help-bot-token")
    monkeypatch.setenv("ADMIN_ID", "9000000000000")
    _load_api(monkeypatch, tmp_path)
    helpbot = importlib.import_module("helpbot")
    helpbot.SUPPORT_AI_CONFIG.enabled = True
    helpbot.SUPPORT_AI_CONFIG.api_key = "synthetic-test-key"
    helpbot.SUPPORT_AI_CONFIG.min_interval_seconds = 0
    helpbot.support_ai_last_reply_at.clear()

    async def fake_generate_support_reply(*_args, **_kwargs):
        return SimpleNamespace(reply="Synthetic assistant reply")

    class FailingSession:
        def __init__(self, *, rollback_fails: bool, close_fails: bool):
            self.rollback_fails = rollback_fails
            self.close_fails = close_fails
            self.rollback_attempted = False
            self.closed = False

        def commit(self):
            return None

        def rollback(self):
            self.rollback_attempted = True
            if self.rollback_fails:
                raise RuntimeError("rollback failure marker")

        def close(self):
            self.closed = True
            if self.close_fails:
                raise RuntimeError("close failure marker")

    monkeypatch.setattr(helpbot.SUPPORT_AGENT_SERVICE, "generate", fake_generate_support_reply)

    def fail_to_append(*_args, **_kwargs):
        raise RuntimeError("synthetic persistence detail echoed the assistant body")

    monkeypatch.setattr(helpbot, "add_ticket_message", fail_to_append)
    message = SimpleNamespace(from_user=SimpleNamespace(id=7201))
    for rollback_fails, close_fails in ((False, False), (True, False), (False, True), (True, True)):
        session = FailingSession(rollback_fails=rollback_fails, close_fails=close_fails)
        monkeypatch.setattr(helpbot, "SessionLocal", lambda session=session: session)
        with unittest.TestCase().assertLogs("helpbot", level="WARNING") as captured:
            reply = asyncio.run(
                helpbot._maybe_generate_support_ai_reply(
                    message,
                    ticket_id=72,
                    text="Synthetic user message",
                )
            )

        expected = [
            "WARNING:helpbot:support AI ticket append failed code=support_reply_persist_error"
        ]
        if close_fails:
            expected.append(
                "WARNING:helpbot:support AI ticket session cleanup failed code=support_reply_cleanup_error"
            )
        fixed_log_only = captured.output == expected
        assert fixed_log_only, "helpbot-support-ai-persistence-log"
        assert reply is None, "helpbot-support-ai-persistence-result"
        assert session.rollback_attempted and session.closed, "helpbot-support-ai-persistence-cleanup"


def test_sqlalchemy_engine_hides_statement_parameters(monkeypatch, tmp_path):
    _load_api(monkeypatch, tmp_path)
    db = importlib.import_module("db")

    engine_hides_parameters = db.engine.hide_parameters is True
    assert engine_hides_parameters, "db-engine-hide-parameters"

    marker = "synthetic-private-bind-value"
    rendered = marker
    try:
        with db.engine.connect() as connection:
            connection.execute(
                db.text("SELECT * FROM missing_support_table WHERE body = :body"),
                {"body": marker},
            )
    except Exception as exc:
        rendered = str(exc)
    parameters_hidden = marker not in rendered
    assert parameters_hidden, "db-exception-hide-parameters"


def test_recovery_scope_allowlist_uses_route_templates_and_fails_closed(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)

    def build_request(method: str, actual_path: str, route_template: str | None):
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "scheme": "https",
            "path": actual_path,
            "raw_path": actual_path.encode("ascii"),
            "query_string": b"",
            "headers": [],
            "server": ("api.pokrov.test", 443),
            "client": ("127.0.0.1", 12345),
        }
        if route_template is not None:
            scope["route"] = SimpleNamespace(path=route_template)
        return api.Request(scope)

    allowed = [
        ("GET", "/api/auth/session"),
        ("POST", "/api/client/session/revoke"),
        ("POST", "/api/client/access/reissue"),
        ("GET", "/api/client/devices"),
        ("DELETE", "/api/client/devices/{device_id}"),
        ("GET", "/api/tickets"),
        ("POST", "/api/tickets"),
        ("GET", "/api/tickets/{ticket_id}"),
        ("POST", "/api/tickets/{ticket_id}/messages"),
    ]
    allowed_results = [
        api._recovery_scope_request_allowed(build_request(method, "/not-authoritative", route_template))
        for method, route_template in allowed
    ]
    assert all(allowed_results), "recovery-route-template-allowlist"

    denied = [
        build_request("POST", "/api/client/support/assistant", "/api/client/support/assistant"),
        build_request("GET", "/api/tickets", None),
        build_request(
            "POST",
            "/api/tickets/17/messages",
            "/api/tickets/{ticket_id}/messages/extra",
        ),
        build_request("POST", "/api/tickets/17", "/api/tickets/{ticket_id}"),
    ]
    denied_results = [
        api._recovery_scope_request_allowed(request)
        for request in denied
    ]
    assert not any(denied_results), "recovery-route-template-fail-closed"


def test_recovery_scope_http_denies_non_text_and_private_client_surfaces(monkeypatch, tmp_path):
    _api, client, normal_headers, recovery_headers = _recovery_http_fixture(monkeypatch, tmp_path)
    _ticket_id, attachment_url = _seed_ticket_with_private_attachment(client, normal_headers)

    session = client.get("/api/auth/session", headers=recovery_headers)
    assert session.status_code == 200, "recovery-session-status"
    devices = client.get("/api/client/devices", headers=recovery_headers)
    assert devices.status_code == 200, "recovery-device-list"
    missing_device = client.delete("/api/client/devices/not-a-device", headers=recovery_headers)
    assert missing_device.status_code == 404, "recovery-device-template"

    blocked_requests = [
        (
            "standalone-support-ai",
            "POST",
            "/api/client/support/assistant",
            {},
            {
                "json": {
                    "message": "Text-only support question",
                    "safeDiagnostics": {"platform": "windows", "runtimeState": "disconnected"},
                }
            },
        ),
        (
            "ticket-upload",
            "POST",
            "/api/tickets/uploads",
            {"Content-Type": "image/png", "X-Upload-Filename": "blocked.png"},
            {"content": b"\x89PNG\r\n\x1a\nblocked"},
        ),
        ("attachment-download", "GET", attachment_url, {}, {}),
        ("managed-profile", "GET", "/api/client/profile/managed", {}, {}),
        ("subscription", "GET", "/api/client/subscription", {}, {}),
        ("route-policy", "GET", "/api/client/route-policy", {}, {}),
        ("locations", "GET", "/api/client/locations", {}, {}),
        ("node-candidates", "GET", "/api/client/nodes/candidates", {}, {}),
    ]
    results = []
    for case_name, method, path, extra_headers, request_kwargs in blocked_requests:
        response = client.request(
            method,
            path,
            headers={**recovery_headers, **extra_headers},
            **request_kwargs,
        )
        results.append(
            (
                case_name,
                response.status_code == 403,
                response.headers.get("X-POKROV-Auth-Error") == "recovery_scope_forbidden",
            )
        )
    assert all(status_ok and code_ok for _case, status_ok, code_ok in results), "recovery-http-deny-matrix"

    revoke = client.post("/api/client/session/revoke", headers=recovery_headers)
    assert revoke.status_code == 200, "recovery-session-revoke"
    revoked_session = client.get("/api/auth/session", headers=recovery_headers)
    assert revoked_session.status_code == 401, "recovery-session-revoked"


def test_recovery_ticket_http_rejects_nonempty_media_fields(monkeypatch, tmp_path):
    _api, client, _normal_headers, recovery_headers = _recovery_http_fixture(monkeypatch, tmp_path)
    text_create = client.post(
        "/api/tickets",
        headers=recovery_headers,
        json={"subject": "Text only", "body": "Initial text message"},
    )
    assert text_create.status_code == 200, "recovery-text-ticket-create"
    ticket_id = int(text_create.json()["ticket"]["id"])

    media_cases = [
        ("attachment-id", {"attachment_id": "staged-private-id"}),
        ("media-type", {"media_type": "photo"}),
        ("media-file-id", {"media_file_id": "private-file-id"}),
        ("media-payload", {"media_payload": '{"private":true}'}),
    ]
    results = []
    for case_name, media in media_cases:
        create = client.post(
            "/api/tickets",
            headers=recovery_headers,
            json={"subject": "Blocked media", "body": "Blocked create", **media},
        )
        message = client.post(
            f"/api/tickets/{ticket_id}/messages",
            headers=recovery_headers,
            json={"body": "Blocked message", **media},
        )
        for operation, response in (("create", create), ("message", message)):
            results.append(
                (
                    f"{operation}-{case_name}",
                    response.status_code == 403,
                    response.headers.get("X-POKROV-Auth-Error") == "recovery_scope_forbidden",
                )
            )
    assert all(status_ok and code_ok for _case, status_ok, code_ok in results), "recovery-media-rejection"

    empty_media = client.post(
        f"/api/tickets/{ticket_id}/messages",
        headers=recovery_headers,
        json={
            "body": "Empty media fields remain text-only",
            "media_type": "",
            "media_file_id": "",
            "media_payload": "",
        },
    )
    assert empty_media.status_code == 200, "recovery-empty-media-fields"


def test_recovery_ticket_http_hides_attachment_metadata_and_enforces_ownership(monkeypatch, tmp_path):
    api, client, normal_headers, recovery_headers = _recovery_http_fixture(monkeypatch, tmp_path)
    ticket_id, _attachment_url = _seed_ticket_with_private_attachment(client, normal_headers)

    db = api.SessionLocal()
    try:
        foreign_ticket = api.SupportTicket(
            user_tg_id=123456,
            status="open",
            subject="Foreign ticket",
            created_at=api._utcnow(),
            updated_at=api._utcnow(),
        )
        db.add(foreign_ticket)
        db.commit()
        foreign_ticket_id = int(foreign_ticket.id)
    finally:
        db.close()

    ticket_list = client.get("/api/tickets", headers=recovery_headers)
    owned_get = client.get(f"/api/tickets/{ticket_id}", headers=recovery_headers)
    owned_create = client.post(
        "/api/tickets",
        headers=recovery_headers,
        json={"subject": "Recovery follow-up", "body": "Text-only create"},
    )
    owned_message = client.post(
        f"/api/tickets/{ticket_id}/messages",
        headers=recovery_headers,
        json={"body": "Text-only follow-up"},
    )
    assert all(
        response.status_code == 200
        for response in (ticket_list, owned_get, owned_create, owned_message)
    ), "recovery-owned-ticket-matrix"

    listed = list(ticket_list.json()["tickets"])
    assert any(int(ticket["id"]) == ticket_id for ticket in listed), "recovery-owned-ticket-listed"
    assert all(int(ticket["id"]) != foreign_ticket_id for ticket in listed), "recovery-foreign-ticket-not-listed"
    listed_owned = next(ticket for ticket in listed if int(ticket["id"]) == ticket_id)
    recovery_tickets = [
        listed_owned,
        dict(owned_get.json()["ticket"]),
        dict(owned_create.json()["ticket"]),
        dict(owned_message.json()["ticket"]),
    ]
    assert all(_messages_are_text_only(ticket) for ticket in recovery_tickets), "recovery-ticket-media-omission"

    foreign_get = client.get(f"/api/tickets/{foreign_ticket_id}", headers=recovery_headers)
    foreign_message = client.post(
        f"/api/tickets/{foreign_ticket_id}/messages",
        headers=recovery_headers,
        json={"body": "Must not cross account boundary"},
    )
    assert foreign_get.status_code == 403, "recovery-foreign-ticket-get"
    assert foreign_message.status_code == 403, "recovery-foreign-ticket-message"

    normal_get = client.get(f"/api/tickets/{ticket_id}", headers=normal_headers)
    assert normal_get.status_code == 200, "normal-ticket-get"
    assert any(
        "media_file_id" in message
        for message in normal_get.json()["ticket"]["messages"]
    ), "normal-ticket-media-compatible"


def test_recovery_actor_equal_to_admin_id_cannot_access_foreign_ticket(monkeypatch, tmp_path):
    api, client, normal_headers, recovery_headers = _recovery_http_fixture(monkeypatch, tmp_path)
    _owned_ticket_id, attachment_url = _seed_ticket_with_private_attachment(client, normal_headers)
    session_response = client.get("/api/auth/session", headers=recovery_headers)
    assert session_response.status_code == 200, session_response.text
    recovery_actor = int(session_response.json()["user"]["id"])

    db = api.SessionLocal()
    try:
        foreign_ticket = api.SupportTicket(
            user_tg_id=123456,
            status="open",
            subject="Foreign ticket",
            created_at=api._utcnow(),
            updated_at=api._utcnow(),
        )
        db.add(foreign_ticket)
        db.commit()
        foreign_ticket_id = int(foreign_ticket.id)
    finally:
        db.close()

    monkeypatch.setattr(api.Settings, "ADMIN_ID", recovery_actor)

    foreign_get = client.get(f"/api/tickets/{foreign_ticket_id}", headers=recovery_headers)
    foreign_message = client.post(
        f"/api/tickets/{foreign_ticket_id}/messages",
        headers=recovery_headers,
        json={"body": "Recovery scope must not inherit admin bypass"},
    )
    attachment_download = client.get(attachment_url, headers=recovery_headers)

    assert foreign_get.status_code == 403, "recovery-admin-foreign-ticket-get"
    assert foreign_message.status_code == 403, "recovery-admin-foreign-ticket-message"
    assert attachment_download.status_code == 403, "recovery-admin-attachment-download"
    assert (
        attachment_download.headers.get("X-POKROV-Auth-Error") == "recovery_scope_forbidden"
    ), "recovery-admin-attachment-code"


def test_email_otp_fresh_auth_recovery_exchange_and_vpn_reissue(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_ID", "9000000000000")
    api = _load_api(monkeypatch, tmp_path, email_public_ready=True)
    _install_fake_panel(monkeypatch, api)
    captured = _capture_auth_delivery(monkeypatch, api)
    client = TestClient(api.app)

    start = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-recovery-original",
            "device_name": "Original phone",
            "platform": "android",
            "app_version": "1.0.0-rc.1",
        },
    )
    assert start.status_code == 200, start.text
    access_token = str(start.json()["access_token"])
    headers = {"Authorization": f"Bearer {access_token}"}

    register = client.post(
        "/api/auth/email/register",
        headers=headers,
        json={"email": "recover-app@pokrov.test", "password": "StrongPass123!"},
    )
    assert register.status_code == 200, register.text
    verify = client.post("/api/auth/email/verify", json={"token": str(captured["verify"])})
    assert verify.status_code == 200, verify.text

    otp_start = client.post("/api/auth/email/otp/start", json={"email": "recover-app@pokrov.test"})
    assert otp_start.status_code == 200, otp_start.text
    otp_finish = client.post(
        "/api/auth/email/otp/finish",
        headers=headers,
        json={"email": "recover-app@pokrov.test", "code": str(captured["login_otp"])},
    )
    assert otp_finish.status_code == 200, otp_finish.text
    assert otp_finish.json()["fresh_auth_until"]

    rotate = client.post("/api/client/recovery-code/rotate", headers=headers)
    assert rotate.status_code == 200, rotate.text
    recovery_code = str(rotate.json()["recovery_code"])
    assert recovery_code.startswith("PKR-")

    exchange = client.post(
        "/api/client/recovery/exchange",
        json={
            "code": recovery_code,
            "install_id": "install-recovery-new-device",
            "device_name": "New PC",
            "platform": "windows",
            "os_version": "11",
            "app_version": "1.0.0-rc.1",
        },
    )
    assert exchange.status_code == 200, exchange.text
    exchange_body = exchange.json()
    assert exchange_body["session"]["scope"] == "recovery"
    assert exchange_body["allowed_actions"] == ["status", "support", "reissue", "device_revoke"]
    assert "subscription_url" not in exchange_body

    recovery_headers = {"Authorization": f"Bearer {exchange_body['access_token']}"}
    db = api.SessionLocal()
    try:
        foreign_ticket = api.SupportTicket(
            user_tg_id=123456,
            status="open",
            subject="Foreign ticket",
            created_at=api._utcnow(),
            updated_at=api._utcnow(),
        )
        db.add(foreign_ticket)
        db.commit()
        foreign_ticket_id = int(foreign_ticket.id)
    finally:
        db.close()

    forbidden_foreign_ticket = client.get(f"/api/tickets/{foreign_ticket_id}", headers=recovery_headers)
    assert forbidden_foreign_ticket.status_code == 403, forbidden_foreign_ticket.text

    forbidden_subscription = client.get("/api/client/subscription", headers=recovery_headers)
    assert forbidden_subscription.status_code == 403, forbidden_subscription.text
    assert forbidden_subscription.headers["X-POKROV-Auth-Error"] == "recovery_scope_forbidden"

    forbidden_email_link = client.post(
        "/api/auth/email/register",
        headers=recovery_headers,
        json={"email": "takeover@pokrov.test", "password": "StrongPass123!"},
    )
    assert forbidden_email_link.status_code == 403, forbidden_email_link.text
    assert forbidden_email_link.headers["X-POKROV-Auth-Error"] == "recovery_scope_forbidden"

    over_limit = client.post(
        "/api/client/access/reissue",
        headers=recovery_headers,
        json={"mode": "vpn_credentials"},
    )
    assert over_limit.status_code == 409, over_limit.text
    assert over_limit.headers["X-POKROV-Auth-Error"] == "device_limit_reached"

    reissue = client.post(
        "/api/client/access/reissue",
        headers=recovery_headers,
        json={"mode": "account_lockdown"},
    )
    assert reissue.status_code == 200, reissue.text
    reissue_body = reissue.json()
    assert reissue_body["mode"] == "account_lockdown"
    assert reissue_body["session"]["scope"] == "client"
    assert reissue_body["access_token"] != exchange_body["access_token"]

    replay = client.post(
        "/api/client/access/reissue",
        headers=recovery_headers,
        json={"mode": "vpn_credentials"},
    )
    assert replay.status_code == 401, replay.text

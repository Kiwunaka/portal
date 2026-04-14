from __future__ import annotations

import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

REPO_ROOT = PORTAL_BOT_DIR.parent


def _load_api(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "portal-email-auth.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("BOT_TOKEN", "777000:test-bot-token")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "portal-test-secret")
    monkeypatch.setenv("EMAIL_AUTH_DEBUG_ECHO", "true")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.pokrov.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "pokrov.test")
    monkeypatch.setenv("WEBAPP_URL", "https://app.pokrov.test/")

    for name in [
        "api",
        "config",
        "db",
        "email_auth_service",
        "migrations",
        "models",
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
    ]:
        sys.modules.pop(name, None)

    return importlib.import_module("api")


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
    api = _load_api(monkeypatch, tmp_path)
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
    verify_token = str(register_body["debug"]["verify_token"])
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


def test_email_register_can_link_to_existing_user(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
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
    verify_token = str(register.json()["debug"]["verify_token"])

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


def test_email_recovery_resets_password(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    register = client.post(
        "/api/auth/email/register",
        json={
            "email": "recover@pokrov.test",
            "password": "StrongPass123!",
        },
    )
    verify_token = str(register.json()["debug"]["verify_token"])
    verify = client.post("/api/auth/email/verify", json={"token": verify_token})
    assert verify.status_code == 200, verify.text

    recovery_start = client.post(
        "/api/auth/email/recovery/start",
        json={"email": "recover@pokrov.test"},
    )

    assert recovery_start.status_code == 200, recovery_start.text
    recovery_token = str(recovery_start.json()["debug"]["reset_token"])
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
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    first_register = client.post(
        "/api/auth/email/register",
        json={"email": "dupe@pokrov.test", "password": "StrongPass123!"},
    )
    verify_token = str(first_register.json()["debug"]["verify_token"])
    verify = client.post("/api/auth/email/verify", json={"token": verify_token})
    assert verify.status_code == 200, verify.text

    duplicate = client.post(
        "/api/auth/email/register",
        json={"email": "dupe@pokrov.test", "password": "SecondPass456!"},
    )

    assert duplicate.status_code == 409, duplicate.text

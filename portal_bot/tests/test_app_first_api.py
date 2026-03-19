from __future__ import annotations

import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def _load_api(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "portal-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "portal-test-secret")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.portal.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "portal.test")
    monkeypatch.setenv("PUBLIC_CHANNEL", "pokrov_vpn")
    monkeypatch.setenv("BOT_USERNAME", "portal_service_bot")
    monkeypatch.setenv("SUPPORT_BOT_USERNAME", "portal_privacy_helpbot")

    for name in [
        "api",
        "config",
        "db",
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


def test_start_trial_returns_session_and_real_device_payload(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    start_trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-123",
            "device_name": "Samsung S25",
            "platform": "android",
            "os_version": "15",
            "app_version": "1.0.0",
            "locale": "ru",
            "time_zone": "Europe/Moscow",
            "trial_days": 5,
        },
    )

    assert start_trial_response.status_code == 200
    payload = start_trial_response.json()
    assert payload["ok"] is True
    assert payload["session_token"]

    session_response = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {payload['session_token']}"},
    )

    assert session_response.status_code == 200
    session_payload = session_response.json()
    assert session_payload["user"]["device_name"] == "Samsung S25"
    assert session_payload["user"]["account_id"]

    user_response = client.get(
        f"/api/user/{session_payload['user']['account_id']}",
        headers={"Authorization": f"Bearer {payload['session_token']}"},
    )

    assert user_response.status_code == 200
    user_payload = user_response.json()
    assert user_payload["devices"][0]["name"] == "Samsung S25"
    assert user_payload["devices"][0]["platform"] == "android"


def test_start_trial_reuses_existing_install_id(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    request_payload = {
        "install_id": "install-repeat",
        "device_name": "Windows PC",
        "platform": "windows",
        "os_version": "11",
        "app_version": "1.0.0",
        "locale": "ru",
        "time_zone": "Europe/Moscow",
        "trial_days": 5,
    }

    first = client.post("/api/client/session/start-trial", json=request_payload)
    second = client.post("/api/client/session/start-trial", json=request_payload)

    assert first.status_code == 200
    assert second.status_code == 200

    first_session = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {first.json()['session_token']}"},
    )
    second_session = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {second.json()['session_token']}"},
    )

    assert first_session.json()["user"]["account_id"] == second_session.json()["user"]["account_id"]


def test_app_session_can_create_support_ticket(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-support",
            "device_name": "Xiaomi 15 Pro",
            "platform": "android",
            "os_version": "15",
            "app_version": "1.0.0",
            "locale": "ru",
            "time_zone": "Europe/Moscow",
            "trial_days": 5,
        },
    )

    token = trial_response.json()["session_token"]
    create_ticket_response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "subject": "Не подключается",
            "body": "Нужна помощь с первым запуском",
        },
    )

    assert create_ticket_response.status_code == 200
    ticket_payload = create_ticket_response.json()["ticket"]
    assert ticket_payload["subject"] == "Не подключается"
    assert ticket_payload["messages"][0]["body"] == "Нужна помощь с первым запуском"


def test_app_session_can_request_telegram_link(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-link",
            "device_name": "Pixel 10",
            "platform": "android",
            "trial_days": 5,
        },
    )

    token = trial_response.json()["session_token"]
    link_response = client.post(
        "/api/client/telegram/link",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert link_response.status_code == 200
    payload = link_response.json()
    assert payload["ok"] is True
    assert payload["linked"] is False
    assert payload["bot_url"].startswith("https://t.me/portal_service_bot?start=")
    assert payload["start_code"].startswith("app")


def test_channel_bonus_claim_uses_linked_telegram_identity_for_app_account(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    async def fake_is_channel_member(channel_username: str, tg_id: int):
        assert channel_username == "pokrov_vpn"
        return (tg_id == 777001, "member" if tg_id == 777001 else "not_member")

    monkeypatch.setattr(api, "_is_channel_member", fake_is_channel_member)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-bonus",
            "device_name": "Galaxy Fold",
            "platform": "android",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]
    session_response = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {token}"},
    )
    account_id = int(session_response.json()["user"]["account_id"])

    db = api.SessionLocal()
    try:
        user = db.query(api.User).filter_by(tg_id=account_id).first()
        user.linked_telegram_id = 777001
        user.linked_telegram_username = "portal_user"
        db.commit()
    finally:
        db.close()

    claim_response = client.post(
        "/api/bonuses/channel/claim",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert claim_response.status_code == 200
    payload = claim_response.json()
    assert payload["ok"] is True
    assert payload["already_claimed"] is False
    assert payload["premium_days"] == 10

    user_response = client.get(
        f"/api/user/{account_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert user_response.status_code == 200
    user_payload = user_response.json()
    assert user_payload["sub_type"] == "BONUS"
    assert user_payload["bonuses"]["channel_bonus"]["claimed_at"]

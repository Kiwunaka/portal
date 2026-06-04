from __future__ import annotations

import importlib
import sys
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def _load_api(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "portal-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "portal-test-secret")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.pokrov.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "pokrov.test")
    monkeypatch.setenv("PUBLIC_CHANNEL", "pokrov_vpn")
    monkeypatch.setenv("BOT_USERNAME", "pokrov_vpnbot")
    monkeypatch.setenv("SUPPORT_BOT_USERNAME", "pokrov_supportbot")

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


def _install_fake_panel(monkeypatch, api):
    class FakePanel:
        async def add_client(self, **_kwargs):
            return True

        async def close(self):
            return None

    monkeypatch.setattr(api, "ControlPanel", FakePanel)


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


def test_start_trial_enforces_canonical_trial_days_and_reports_provisioning(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    start_trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-canonical-trial",
            "device_name": "Surface Laptop",
            "platform": "windows",
            "os_version": "11",
            "app_version": "1.0.0",
            "locale": "ru",
            "time_zone": "Europe/Moscow",
            "trial_days": 1,
        },
    )

    assert start_trial_response.status_code == 200
    payload = start_trial_response.json()
    assert payload["ok"] is True
    assert payload["session"]["token"] == payload["session_token"]
    assert payload["session"]["account_id"] == payload["account_id"]
    assert payload["access"]["trial_days"] == 5
    assert payload["access"]["subscription_url"] == payload["subscription_url"]
    assert payload["client_policy"]["routing_mode_default"] == "all_except_ru"
    assert payload["client_policy"]["transport_profile"] == "legacy_reality_fallback"
    assert payload["client_policy"]["dns_policy"] == "ru_direct_split"
    assert payload["client_policy"]["package_catalog_version"]
    assert payload["client_policy"]["support_context"]["routing_mode"] == "all_except_ru"
    assert payload["client_policy"]["route_mode"] == "all_traffic"
    assert payload["client_policy"]["selected_apps"] == []
    assert payload["client_policy"]["requires_elevated_privileges"] is True
    assert payload["client_policy"]["route_policy"]["mode"] == "all_traffic"
    assert payload["provisioning"]["status"] in {"ready", "pending_sync"}
    assert payload["provisioning"]["sync_ok"] == payload["sync_ok"]

    db = api.SessionLocal()
    try:
        user = db.query(api.User).filter_by(tg_id=int(payload["account_id"])).first()
        assert user is not None
        assert user.expiry_at is not None
        remaining = user.expiry_at - api._utcnow()
        assert remaining >= timedelta(days=4)
        assert remaining <= timedelta(days=6)
    finally:
        db.close()


def test_app_route_policy_can_be_updated_and_reloaded(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-route-api",
            "device_name": "Windows PC",
            "platform": "windows",
            "os_version": "11",
            "app_version": "1.0.0",
            "locale": "ru",
            "time_zone": "Europe/Moscow",
            "trial_days": 5,
        },
    )

    assert trial_response.status_code == 200
    token = trial_response.json()["session_token"]

    update_response = client.post(
        "/api/client/route-policy",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "route_mode": "selected_apps",
            "selected_apps": ["chrome.exe", "telegram.exe"],
        },
    )

    assert update_response.status_code == 200
    updated_payload = update_response.json()
    assert updated_payload["ok"] is True
    assert updated_payload["route_mode"] == "selected_apps"
    assert updated_payload["selected_apps"] == ["chrome.exe", "telegram.exe"]
    assert updated_payload["requires_elevated_privileges"] is True

    fetch_response = client.get(
        "/api/client/route-policy",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert fetch_response.status_code == 200
    fetched_payload = fetch_response.json()
    assert fetched_payload["route_mode"] == "selected_apps"
    assert fetched_payload["selected_apps"] == ["chrome.exe", "telegram.exe"]

    dashboard_response = client.get(
        "/api/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert dashboard_response.status_code == 200
    dashboard_payload = dashboard_response.json()
    assert dashboard_payload["client_policy"]["route_mode"] == "selected_apps"
    assert dashboard_payload["client_policy"]["selected_apps"] == ["chrome.exe", "telegram.exe"]


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


def test_start_trial_rate_limits_fresh_installs_by_origin(monkeypatch, tmp_path):
    monkeypatch.setenv("API_RATE_LIMIT_START_TRIAL_PER_MINUTE", "1")
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    headers = {"X-Real-IP": "198.51.100.44"}

    class FakePanel:
        async def add_client(self, **_kwargs):
            return True

        async def close(self):
            return None

    old_panel = api.ControlPanel
    try:
        api.ControlPanel = FakePanel
        first = client.post(
            "/api/client/session/start-trial",
            headers=headers,
            json={
                "install_id": "install-rate-one",
                "device_name": "Pixel 10",
                "platform": "android",
            },
        )
        repeated_same_install = client.post(
            "/api/client/session/start-trial",
            headers=headers,
            json={
                "install_id": "install-rate-one",
                "device_name": "Pixel 10",
                "platform": "android",
            },
        )
        blocked_new_install = client.post(
            "/api/client/session/start-trial",
            headers=headers,
            json={
                "install_id": "install-rate-two",
                "device_name": "Pixel 10",
                "platform": "android",
            },
        )
    finally:
        api.ControlPanel = old_panel

    assert first.status_code == 200, first.text
    assert repeated_same_install.status_code == 200, repeated_same_install.text
    assert repeated_same_install.json()["account_id"] == first.json()["account_id"]
    assert blocked_new_install.status_code == 429
    assert blocked_new_install.headers["retry-after"]
    assert blocked_new_install.json()["detail"]["code"] == "rate_limited"
    assert blocked_new_install.json()["detail"]["scope"] == "start_trial"


def test_access_key_status_rate_limit_returns_retry_contract(monkeypatch, tmp_path):
    monkeypatch.setenv("API_RATE_LIMIT_ACCESS_KEY_STATUS_PER_MINUTE", "1")
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    db = api.SessionLocal()
    try:
        db.add(api.GiftCard(code="BETAKEY1", card_type="standard", created_by=9999))
        db.commit()
    finally:
        db.close()

    headers = {"X-Real-IP": "198.51.100.45"}
    first = client.get("/api/access-keys/status/BETAKEY1", headers=headers)
    blocked = client.get("/api/access-keys/status/BETAKEY1", headers=headers)

    assert first.status_code == 200, first.text
    assert blocked.status_code == 429
    assert blocked.headers["retry-after"]
    detail = blocked.json()["detail"]
    assert detail["code"] == "rate_limited"
    assert detail["scope"] == "access_key_status"
    assert detail["retry_after_seconds"] >= 1


def test_app_session_can_redeem_access_key_through_unified_endpoint(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    _install_fake_panel(monkeypatch, api)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-redeem-unified",
            "device_name": "Windows PC",
            "platform": "windows",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]

    db = api.SessionLocal()
    try:
        db.add(api.GiftCard(code="POKROV-ACCESS-2026", card_type="1_month", created_by=0))
        db.commit()
    finally:
        db.close()

    async def fake_sync_control_panel_access(*, user):
        return True

    monkeypatch.setattr(api, "_sync_control_panel_access", fake_sync_control_panel_access)

    response = client.post(
        "/api/redeem",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": "POKROV-ACCESS-2026"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ok"] is True
    assert body["kind"] == "access_key"
    assert body["code_preview"] == "...2026"
    assert body["result"]["access"]["access_state"]
    assert body["result"]["provisioning"]["managed_profile_path"] == "/api/client/profile/managed"


def test_app_session_can_redeem_gift_card_through_unified_endpoint(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    _install_fake_panel(monkeypatch, api)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-redeem-gift-unified",
            "device_name": "Windows PC",
            "platform": "windows",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]

    db = api.SessionLocal()
    try:
        db.add(api.GiftCard(code="POKROV-GIFT-2026", card_type="standard", created_by=7777))
        db.commit()
    finally:
        db.close()

    class FakeGiftPanel:
        async def login(self):
            return True

        async def get_existing_client(self, _tg_id):
            return None

        async def add_client(self, *_args, **_kwargs):
            return True

        async def update_client_traffic(self, *_args, **_kwargs):
            return True

        async def close(self):
            return None

    monkeypatch.setattr(sys.modules["control_panel"], "ControlPanel", FakeGiftPanel)

    response = client.post(
        "/api/redeem",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": "POKROV-GIFT-2026"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ok"] is True
    assert body["kind"] == "gift"
    assert body["code_preview"] == "...2026"
    assert body["result"]["ok"] is True
    assert body["result"]["card_type"] == "standard"
    assert body["result"]["days"] == 30
    assert body["summary"]["ok"] is True
    assert body["summary"]["channel_bonus"]["premium_days"] == api.CHANNEL_PREMIUM_DAYS

    db = api.SessionLocal()
    try:
        card = db.query(api.GiftCard).filter_by(code="POKROV-GIFT-2026").first()
        account = db.query(api.User).filter_by(app_install_id="install-redeem-gift-unified").first()
        assert int(card.redeemed_by or 0) == int(account.tg_id)
        assert str(account.sub_type or "").upper() == "PAID"
    finally:
        db.close()


def test_unified_redeem_rejects_subscription_links(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    _install_fake_panel(monkeypatch, api)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-redeem-link",
            "device_name": "Pixel 10",
            "platform": "android",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]

    response = client.post(
        "/api/redeem",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": "https://connect.pokrov.space/sub/example"},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "subscription_link_not_redeem_code"
    assert "subscription" in detail["message"]


def test_unified_redeem_rate_limit_returns_retry_contract(monkeypatch, tmp_path):
    monkeypatch.setenv("API_RATE_LIMIT_UNIFIED_REDEEM_PER_MINUTE", "1")
    api = _load_api(monkeypatch, tmp_path)
    _install_fake_panel(monkeypatch, api)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-redeem-rate",
            "device_name": "Pixel 10",
            "platform": "android",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Real-IP": "198.51.100.77",
    }

    first = client.post("/api/redeem", headers=headers, json={"code": "UNKNOWN-CODE-1"})
    blocked = client.post("/api/redeem", headers=headers, json={"code": "UNKNOWN-CODE-2"})

    assert first.status_code == 404
    assert blocked.status_code == 429
    assert blocked.headers["retry-after"]
    detail = blocked.json()["detail"]
    assert detail["code"] == "rate_limited"
    assert detail["scope"] == "unified_redeem"


def test_app_session_can_request_short_lived_cabinet_token(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    _install_fake_panel(monkeypatch, api)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-cabinet-token",
            "device_name": "Surface Laptop",
            "platform": "windows",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]

    response = client.post(
        "/api/client/cabinet-token",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_path": "/profile"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ok"] is True
    assert body["token"]
    assert body["handoff_token"] == body["token"]
    assert body["expires_in"] <= 120
    assert body["target_path"] == "/profile"
    assert body["auth_origin"] == "app_cabinet_handoff"
    assert body["scope"] == "cabinet_handoff"
    assert body["handoff_url"].startswith("https://app.pokrov.space/profile")
    parsed = urlparse(body["handoff_url"])
    assert parse_qs(parsed.query)["handoff_token"] == [body["handoff_token"]]

    direct_session_response = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {body['handoff_token']}"},
    )
    assert direct_session_response.status_code == 401
    assert direct_session_response.headers["x-pokrov-auth-error"] == "web_session_exchange_required"

    exchange_response = client.post(
        "/api/auth/cabinet-handoff/exchange",
        json={"handoff_token": body["handoff_token"]},
    )
    assert exchange_response.status_code == 200, exchange_response.text
    exchanged = exchange_response.json()
    assert exchanged["ok"] is True
    assert exchanged["token"]
    assert exchanged["token"] != body["handoff_token"]
    assert exchanged["target_path"] == "/profile"

    session_response = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {exchanged['token']}"},
    )
    assert session_response.status_code == 200, session_response.text
    session_payload = session_response.json()
    assert session_payload["user"]["auth_origin"] == "app_cabinet_handoff"

    replay_response = client.post(
        "/api/auth/cabinet-handoff/exchange",
        json={"handoff_token": body["handoff_token"]},
    )
    assert replay_response.status_code == 409
    assert replay_response.json()["detail"]["code"] == "cabinet_handoff_already_used"


def test_cabinet_token_rejects_external_target_path(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    _install_fake_panel(monkeypatch, api)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-cabinet-token-external",
            "device_name": "Pixel 10",
            "platform": "android",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]

    response = client.post(
        "/api/client/cabinet-token",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_path": "https://evil.example/"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_cabinet_target"


def test_cabinet_token_rate_limit_returns_retry_contract(monkeypatch, tmp_path):
    monkeypatch.setenv("API_RATE_LIMIT_CABINET_TOKEN_PER_MINUTE", "1")
    api = _load_api(monkeypatch, tmp_path)
    _install_fake_panel(monkeypatch, api)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-cabinet-rate",
            "device_name": "Pixel 10",
            "platform": "android",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Real-IP": "198.51.100.78",
    }

    first = client.post(
        "/api/client/cabinet-token",
        headers=headers,
        json={"target_path": "/profile"},
    )
    blocked = client.post(
        "/api/client/cabinet-token",
        headers=headers,
        json={"target_path": "/profile"},
    )

    assert first.status_code == 200, first.text
    assert blocked.status_code == 429
    assert blocked.headers["retry-after"]
    detail = blocked.json()["detail"]
    assert detail["code"] == "rate_limited"
    assert detail["scope"] == "cabinet_token"


def test_cabinet_token_cleans_old_handoff_ledger_rows(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    _install_fake_panel(monkeypatch, api)
    client = TestClient(api.app)

    old_hash = "a" * 64
    db = api.SessionLocal()
    try:
        db.add(
            api.WebCabinetHandoffToken(
                tg_id=404,
                token_hash=old_hash,
                target_path="/profile",
                expires_at=api._utcnow() - timedelta(days=3),
                used_at=api._utcnow() - timedelta(days=3),
                created_at=api._utcnow() - timedelta(days=4),
            )
        )
        db.commit()
    finally:
        db.close()

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-cabinet-cleanup",
            "device_name": "Pixel 10",
            "platform": "android",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]

    response = client.post(
        "/api/client/cabinet-token",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_path": "/profile"},
    )

    assert response.status_code == 200, response.text
    db = api.SessionLocal()
    try:
        assert db.query(api.WebCabinetHandoffToken).filter_by(token_hash=old_hash).count() == 0
        assert db.query(api.WebCabinetHandoffToken).count() == 1
    finally:
        db.close()


def test_cabinet_handoff_exchange_rate_limit_returns_retry_contract(monkeypatch, tmp_path):
    monkeypatch.setenv("API_RATE_LIMIT_CABINET_HANDOFF_EXCHANGE_PER_MINUTE", "1")
    api = _load_api(monkeypatch, tmp_path)
    _install_fake_panel(monkeypatch, api)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-cabinet-exchange-rate",
            "device_name": "Pixel 10",
            "platform": "android",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]
    handoff = client.post(
        "/api/client/cabinet-token",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_path": "/profile"},
    )
    handoff_token = handoff.json()["handoff_token"]
    headers = {"X-Real-IP": "198.51.100.88"}

    first = client.post(
        "/api/auth/cabinet-handoff/exchange",
        headers=headers,
        json={"handoff_token": "bad-handoff-token-1"},
    )
    blocked = client.post(
        "/api/auth/cabinet-handoff/exchange",
        headers=headers,
        json={"handoff_token": handoff_token},
    )

    assert first.status_code == 401
    assert blocked.status_code == 429
    assert blocked.headers["retry-after"]
    detail = blocked.json()["detail"]
    assert detail["code"] == "rate_limited"
    assert detail["scope"] == "cabinet_handoff_exchange"


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
    assert payload["bot_url"].startswith("https://t.me/pokrov_vpnbot?start=")
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


def test_channel_subscriber_check_is_read_only_for_linked_app_account(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    async def fake_is_channel_member(channel_username: str, tg_id: int):
        assert channel_username == "pokrov_vpn"
        return (tg_id == 888001, "member" if tg_id == 888001 else "not_member")

    monkeypatch.setattr(api, "_is_channel_member", fake_is_channel_member)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-readonly-check",
            "device_name": "Pixel Fold",
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
        user.linked_telegram_id = 888001
        user.linked_telegram_username = "readonly_member"
        db.commit()
    finally:
        db.close()

    check_response = client.post(
        "/api/channel/subscriber/check",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert check_response.status_code == 200
    payload = check_response.json()
    assert payload["ok"] is True
    assert payload["subscriber"] is True
    assert payload["reason"] == "member"
    assert payload["claim_required"] is True
    assert payload["bonus_days"] == 10
    assert payload["points_granted"] == 0
    assert payload["campaign_marked"] is False

    assert api.available_points(tg_id=account_id)[0] == 0


def test_app_session_can_read_bonus_and_referral_summaries(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    _install_fake_panel(monkeypatch, api)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-bonus-summary",
            "device_name": "Pixel Fold",
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
        user.referral_count = 3
        user.referral_code = "POKROV3"
        user.channel_bonus_claimed_at = api._utcnow()
        user.pending_discount_pct = 20
        user.pending_discount_code = "APP20"
        db.commit()
    finally:
        db.close()

    summary_response = client.get(
        "/api/bonuses/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    referral_response = client.get(
        "/api/bonuses/referral/summary",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert summary_response.status_code == 200, summary_response.text
    summary = summary_response.json()
    assert summary["ok"] is True
    assert summary["referral_count"] == 3
    assert summary["referral_code"] == "POKROV3"
    assert summary["channel_bonus_claimed_at"]
    assert summary["channel_bonus"]["claimed"] is True
    assert summary["referral"]["count"] == 3
    assert summary["referral"]["code"] == "POKROV3"
    assert "start=ref_POKROV3" in summary["referral"]["link"]
    assert summary["promo"]["redeem_endpoint"] == "/api/bonuses/promo/redeem"
    assert summary["promo"]["pending_discount_pct"] == 20
    assert summary["wheel"]["enabled"] is False
    assert summary["calendar"]["enabled"] is False

    assert referral_response.status_code == 200, referral_response.text
    referral = referral_response.json()
    assert referral["ok"] is True
    assert referral["count"] == 3
    assert referral["code"] == "POKROV3"
    assert referral["bonus_days"] == api.REFERRAL_BONUS_DAYS
    assert referral["tier"]["tier_key"]


def test_app_session_can_read_safe_bonus_history(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    _install_fake_panel(monkeypatch, api)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-bonus-history",
            "device_name": "Windows PC",
            "platform": "windows",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]
    session_response = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {token}"},
    )
    account_id = int(session_response.json()["user"]["account_id"])

    now = api._utcnow()
    db = api.SessionLocal()
    try:
        user = db.query(api.User).filter_by(tg_id=account_id).first()
        user.channel_bonus_claimed_at = now - timedelta(days=1)
        db.add(
            api.CampaignSend(
                tg_id=account_id,
                campaign_key=api.OPENING_PREMIUM_CAMPAIGN_KEY,
                sent_at=now - timedelta(days=3),
            )
        )
        db.add(api.PromoCode(code="APPDAYS", promo_type="days", value=7, uses_left=0))
        db.add(api.PromoUsage(tg_id=account_id, promo_code="APPDAYS", used_at=now))
        db.add(
            api.Event(
                tg_id=account_id,
                event_name="promo_redeemed",
                source="webapp",
                meta_json='{"sub_token":"must-not-leak","code":"APPDAYS"}',
                created_at=now,
            )
        )
        db.commit()
    finally:
        db.close()

    history_response = client.get(
        "/api/bonuses/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    summary_response = client.get(
        "/api/bonuses/summary",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert history_response.status_code == 200, history_response.text
    history = history_response.json()
    assert history["ok"] is True
    assert history["tg_id"] == account_id
    assert history["next_cursor"] is None
    assert len(history["items"]) == 3
    assert [item["kind"] for item in history["items"]] == [
        "promo",
        "telegram_channel",
        "opening_bonus",
    ]
    assert history["items"][0]["days"] == 7
    assert history["items"][0]["code_preview"] == "...DAYS"
    assert "APPDAYS" not in str(history)
    assert "sub_token" not in str(history)
    assert "must-not-leak" not in str(history)

    assert summary_response.status_code == 200, summary_response.text
    summary = summary_response.json()
    assert summary["history"]["endpoint"] == "/api/bonuses/history"
    assert summary["history"]["recent_count"] == 3


def test_app_bonus_wheel_and_calendar_endpoints_are_feature_gated(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    _install_fake_panel(monkeypatch, api)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-gated-bonus-features",
            "device_name": "Pixel",
            "platform": "android",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]
    headers = {"Authorization": f"Bearer {token}"}

    wheel_state = client.get("/api/bonuses/wheel/state", headers=headers)
    wheel_spin = client.post("/api/bonuses/wheel/spin", headers=headers)
    calendar_state = client.get("/api/bonuses/calendar", headers=headers)
    calendar_checkin = client.post("/api/bonuses/calendar/checkin", headers=headers)

    assert wheel_state.status_code == 200, wheel_state.text
    wheel_payload = wheel_state.json()
    assert wheel_payload["ok"] is True
    assert wheel_payload["enabled"] is False
    assert wheel_payload["state"] == "disabled_until_feature_flag"
    assert wheel_payload["feature_flag_enabled"] is False
    assert wheel_payload["spin_endpoint"] == "/api/bonuses/wheel/spin"

    assert calendar_state.status_code == 200, calendar_state.text
    calendar_payload = calendar_state.json()
    assert calendar_payload["ok"] is True
    assert calendar_payload["enabled"] is False
    assert calendar_payload["state"] == "disabled_until_feature_flag"
    assert calendar_payload["feature_flag_enabled"] is False
    assert calendar_payload["checkin_endpoint"] == "/api/bonuses/calendar/checkin"

    assert wheel_spin.status_code == 403, wheel_spin.text
    assert wheel_spin.json()["detail"]["code"] == "bonus_feature_disabled"
    assert wheel_spin.json()["detail"]["feature"] == "wheel"

    assert calendar_checkin.status_code == 403, calendar_checkin.text
    assert calendar_checkin.json()["detail"]["code"] == "bonus_feature_disabled"
    assert calendar_checkin.json()["detail"]["feature"] == "calendar"

    db = api.SessionLocal()
    try:
        user = db.query(api.User).filter_by(app_install_id="install-gated-bonus-features").first()
        assert user.last_wheel_spin is None
        assert int(user.streak_months or 0) == 0
        assert db.query(api.RewardClaim).count() == 0
    finally:
        db.close()


def test_app_bonus_wheel_calendar_and_achievements_write_live_ledger(monkeypatch, tmp_path):
    monkeypatch.setenv("BONUS_WHEEL_ENABLED", "true")
    monkeypatch.setenv("BONUS_CALENDAR_ENABLED", "true")
    monkeypatch.setenv("BONUS_CALENDAR_REWARD_DAYS", "1")
    api = _load_api(monkeypatch, tmp_path)
    _install_fake_panel(monkeypatch, api)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-live-bonus-ledger",
            "device_name": "Pixel",
            "platform": "android",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]
    headers = {"Authorization": f"Bearer {token}"}

    db = api.SessionLocal()
    try:
        db.add(
            api.AppSetting(
                key="wheel_config",
                value_json='{"preset":"test","weights":[{"days":3,"weight":1}],"cooldown_hours":168}',
            )
        )
        db.commit()
    finally:
        db.close()

    wheel_state = client.get("/api/bonuses/wheel/state", headers=headers)
    assert wheel_state.status_code == 200, wheel_state.text
    assert wheel_state.json()["enabled"] is True
    assert wheel_state.json()["can_spin"] is True

    wheel_spin = client.post("/api/bonuses/wheel/spin", headers=headers)
    assert wheel_spin.status_code == 200, wheel_spin.text
    spin_payload = wheel_spin.json()
    assert spin_payload["ok"] is True
    assert spin_payload["reward_days"] == 3
    assert spin_payload["reward_key"].startswith("wheel_")
    assert spin_payload["summary"]["wheel"]["can_spin"] is False
    assert spin_payload["summary"]["achievements"]["items"]

    second_spin = client.post("/api/bonuses/wheel/spin", headers=headers)
    assert second_spin.status_code == 409, second_spin.text
    assert second_spin.json()["detail"]["code"] == "wheel_cooldown_active"

    calendar_state = client.get("/api/bonuses/calendar", headers=headers)
    assert calendar_state.status_code == 200, calendar_state.text
    assert calendar_state.json()["enabled"] is True
    assert calendar_state.json()["can_checkin"] is True

    calendar_checkin = client.post("/api/bonuses/calendar/checkin", headers=headers)
    assert calendar_checkin.status_code == 200, calendar_checkin.text
    checkin_payload = calendar_checkin.json()
    assert checkin_payload["ok"] is True
    assert checkin_payload["reward_days"] == 1
    assert checkin_payload["reward_key"].startswith("calendar_")
    assert checkin_payload["summary"]["calendar"]["checked_in_today"] is True
    assert checkin_payload["summary"]["achievements"]["unlocked_count"] >= 2

    second_checkin = client.post("/api/bonuses/calendar/checkin", headers=headers)
    assert second_checkin.status_code == 409, second_checkin.text
    assert second_checkin.json()["detail"]["code"] == "calendar_already_checked_in"

    history = client.get("/api/bonuses/history", headers=headers)
    assert history.status_code == 200, history.text
    kinds = [item["kind"] for item in history.json()["items"]]
    assert "wheel_spin" in kinds
    assert "calendar_checkin" in kinds
    assert "raw_config" not in str(history.json())

    db = api.SessionLocal()
    try:
        user = db.query(api.User).filter_by(app_install_id="install-live-bonus-ledger").first()
        assert user is not None
        assert user.last_wheel_spin is not None
        assert int(user.streak_months or 0) == 1
        assert db.query(api.RewardClaim).filter_by(tg_id=user.tg_id).count() == 2
    finally:
        db.close()


def test_app_session_can_redeem_promo_through_bonus_and_unified_endpoints(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    _install_fake_panel(monkeypatch, api)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-promo-redeem",
            "device_name": "Windows PC",
            "platform": "windows",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]

    db = api.SessionLocal()
    try:
        db.add(api.PromoCode(code="APPDAYS", promo_type="days", value=7, uses_left=2))
        db.add(api.PromoCode(code="APP20", promo_type="discount", value=20, uses_left=1))
        db.commit()
    finally:
        db.close()

    days_response = client.post(
        "/api/bonuses/promo/redeem",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": "appdays"},
    )
    discount_response = client.post(
        "/api/redeem",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": "APP20"},
    )

    assert days_response.status_code == 200, days_response.text
    days = days_response.json()
    assert days["ok"] is True
    assert days["code"] == "APPDAYS"
    assert days["promo_type"] == "days"
    assert days["applied_days"] == 7
    assert days["summary"]["promo"]["redeem_supported"] is True

    assert discount_response.status_code == 200, discount_response.text
    discount = discount_response.json()
    assert discount["ok"] is True
    assert discount["kind"] == "promo"
    assert discount["code_preview"] == "...PP20"
    assert discount["result"]["promo_type"] == "discount"
    assert discount["result"]["pending_discount_pct"] == 20

    db = api.SessionLocal()
    try:
        appdays = db.query(api.PromoCode).filter_by(code="APPDAYS").first()
        app20 = db.query(api.PromoCode).filter_by(code="APP20").first()
        assert int(appdays.uses_left or 0) == 1
        assert int(app20.uses_left or 0) == 0
        assert db.query(api.PromoUsage).count() == 2
    finally:
        db.close()

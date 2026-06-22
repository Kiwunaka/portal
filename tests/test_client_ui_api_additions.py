from __future__ import annotations

import hashlib
import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _load_api(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "client-ui-api-additions.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "client-ui-api-secret")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.pokrov.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "pokrov.test")
    monkeypatch.setenv("PAY_CHECKOUT_URL", "https://pay.pokrov.space/checkout/")
    monkeypatch.setenv("PUBLIC_CHANNEL", "pokrov_vpn")
    monkeypatch.setenv("BOT_USERNAME", "pokrov_vpnbot")
    monkeypatch.setenv("SUPPORT_BOT_USERNAME", "pokrov_supportbot")
    monkeypatch.setenv("BOT_TOKEN", "test_bot_token_123")
    monkeypatch.setenv("ADMIN_ID", "9999")
    monkeypatch.setenv("ADMIN_IDS", "9999")
    monkeypatch.setenv("SUPPORT_AI_ENABLED", "0")

    for name in [
        "api",
        "app_first_service",
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
        "shared_surface_facts",
        "transport_catalog",
        "node_policy",
        "support_ai_service",
    ]:
        sys.modules.pop(name, None)

    api = importlib.import_module("api")

    class _FakePanel:
        async def login(self):
            return True

        async def close(self):
            return None

        async def add_client(self, **kwargs):
            return True

        async def get_node_online_summaries(self, *, node_codes=None):
            return {
                str(code): {"online_keys_now": 0, "online_connections_now": 0}
                for code in (node_codes or [])
            }

    api.ControlPanel = _FakePanel
    return api


def _rollout_payload() -> dict[str, object]:
    return {
        "version": "2026-06-22",
        "defaults": {
            "routing_mode_default": "all_except_ru",
            "transport_profile": "legacy_reality_fallback",
            "dns_policy": "ru_direct_split",
            "ip_version_preference": "ipv4_only",
        },
        "carrier_overrides": {},
        "cohort_overrides": {},
        "operator_lab": {"enabled": False},
        "package_catalog_feed": {"version": "2026-06-22"},
        "routing_rules_feed": {"version": "2026-06-22"},
        "support_recovery_order": ["app", "web", "telegram"],
    }


def _transport_profiles() -> str:
    return json.dumps(
        [
            {
                "name": "legacy_reality_fallback",
                "enabled": True,
                "kind": "reality",
                "inbound_id": 1,
                "host": "example.test",
                "port": 443,
                "tls_server_name": "www.example.test",
                "reality_public_key": "pbk",
                "reality_short_id": "sid",
                "fingerprint": "firefox",
                "flow": "xtls-rprx-vision",
            }
        ]
    )


def _add_node(
    api,
    *,
    code: str,
    health_score: float = 95.0,
    cpu_percent: float = 30.0,
    panel_latency_ms: int | None = 40,
    is_healthy: bool = True,
    enabled: bool = True,
    last_health_at: datetime | None = None,
) -> None:
    from models import Node

    s = api.SessionLocal()
    try:
        node = Node(
            code=code,
            name=code.upper(),
            host=f"{code}.example.test",
            vless_port=443,
            reality_sni="www.example.test",
            reality_pbk="pbk",
            reality_sid="sid",
            fingerprint="firefox",
            flow="xtls-rprx-vision",
            panel_base_url=f"https://{code}.example.test:8444",
            panel_path="xui",
            panel_user="u",
            panel_pass="p",
            inbound_id=1,
            enabled=enabled,
            accepting_new_clients=True,
            is_draining=False,
            weight=100,
            health_score=health_score,
            is_healthy=is_healthy,
            cpu_percent=cpu_percent,
            panel_latency_ms=panel_latency_ms,
            last_health_at=last_health_at or _utcnow(),
            transport_profiles_json=_transport_profiles(),
        )
        s.add(node)
        s.commit()
    finally:
        s.close()


def _seed_rollout(api) -> None:
    s = api.SessionLocal()
    try:
        api._set_app_setting_json(s=s, key="network_rollout_config", value=_rollout_payload())
        s.commit()
    finally:
        s.close()


def _start_trial(client: TestClient, *, install_id: str, platform: str = "windows") -> dict[str, object]:
    response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": install_id,
            "device_name": "Windows 11",
            "platform": platform,
            "os_version": "11",
            "app_version": "1.0.0-beta.2",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _auth_headers(start_body: dict[str, object]) -> dict[str, str]:
    return {"Authorization": f"Bearer {start_body['session_token']}"}


def test_client_locations_catalog_exposes_searchable_real_node_catalog(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    _seed_rollout(api)

    now = _utcnow()
    _add_node(api, code="nl-ams-01", health_score=94.0, cpu_percent=31.0, panel_latency_ms=38, last_health_at=now)
    _add_node(api, code="de-fra-01", health_score=91.0, cpu_percent=42.0, panel_latency_ms=52, last_health_at=now)
    _add_node(api, code="nl-free", health_score=89.0, cpu_percent=58.0, panel_latency_ms=71, last_health_at=now)
    _add_node(api, code="old-node", health_score=98.0, cpu_percent=20.0, last_health_at=now - timedelta(hours=3))

    start_body = _start_trial(client, install_id="locations-catalog-device")
    response = client.get("/api/client/locations?platform=windows&q=ams", headers=_auth_headers(start_body))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["auto"]["enabled"] is True
    assert body["freePoolCode"] == "nl-free"
    assert body["query"] == "ams"
    assert body["search"]["matched"] >= 1
    assert body["countries"]

    all_cities = [
        city
        for country in body["countries"]
        for city in country["cities"]
    ]
    amsterdam = next(city for city in all_cities if city["code"] == "nl-ams-01")
    assert amsterdam["city"] == "Amsterdam"
    assert amsterdam["countryCode"] == "nl"
    assert amsterdam["premium"] is True
    assert amsterdam["healthScore"] == 0.94
    assert amsterdam["latencyMs"] == 38
    assert amsterdam["load"] == 0.31
    assert "old-node" not in {city["code"] for city in all_cities}


def test_client_account_devices_notifications_push_and_subscription_contract(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    _seed_rollout(api)
    _add_node(api, code="nl-ams-01")

    start_body = _start_trial(client, install_id="account-p1-device")
    headers = _auth_headers(start_body)

    subscription = client.get("/api/client/subscription", headers=headers)
    assert subscription.status_code == 200, subscription.text
    sub_body = subscription.json()
    assert sub_body["lane"] == "trialPremium"
    assert sub_body["daysLeft"] == 5
    assert sub_body["autoRenew"] is False
    assert sub_body["renewUrl"].startswith("https://pay.pokrov.space/checkout/")
    assert sub_body["plans"]
    assert {"id", "title", "price"} <= set(sub_body["plans"][0])

    devices = client.get("/api/client/devices", headers=headers)
    assert devices.status_code == 200, devices.text
    device_body = devices.json()
    assert len(device_body["items"]) == 1
    assert device_body["items"][0]["id"] == "account-p1-device"
    assert device_body["items"][0]["current"] is True
    revoke_current = client.delete("/api/client/devices/account-p1-device", headers=headers)
    assert revoke_current.status_code == 409

    notifications = client.get("/api/client/notifications", headers=headers)
    assert notifications.status_code == 200, notifications.text
    inbox = notifications.json()
    assert "items" in inbox
    assert "unreadCount" in inbox
    assert inbox["nextCursor"] is None

    mark_read = client.post(
        "/api/client/notifications/read",
        headers=headers,
        json={"ids": ["access.trial"]},
    )
    assert mark_read.status_code == 200, mark_read.text
    assert mark_read.json()["ok"] is True

    push = client.post(
        "/api/client/push/register",
        headers=headers,
        json={"platform": "windows", "provider": "poll", "token": "local-test-token"},
    )
    assert push.status_code == 200, push.text
    push_body = push.json()
    assert push_body["ok"] is True
    assert push_body["provider"] == "poll"
    assert push_body["tokenHash"] == hashlib.sha256(b"local-test-token").hexdigest()


def test_client_support_assistant_and_ticket_presence_contract(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    _seed_rollout(api)
    _add_node(api, code="nl-ams-01")

    start_body = _start_trial(client, install_id="support-p1-device")
    headers = _auth_headers(start_body)

    assistant = client.post(
        "/api/client/support/assistant",
        headers=headers,
        json={
            "message": "VPN включился, но сайты не открываются.",
            "scope": "support",
            "safeDiagnostics": {"platform": "windows", "phase": "running"},
        },
    )
    assert assistant.status_code == 200, assistant.text
    assistant_body = assistant.json()
    assert assistant_body["reply"]
    assert assistant_body["suggestedActions"]
    assert assistant_body["shouldEscalate"] in {True, False}

    ticket = client.post(
        "/api/tickets",
        headers=headers,
        json={"subject": "Connection issue", "body": "ERR_CONNECTION_CLOSED"},
    )
    assert ticket.status_code == 200, ticket.text
    ticket_body = ticket.json()["ticket"]
    assert ticket_body["operatorPresence"] in {"online", "away", "offline"}
    assert ticket_body["operatorTyping"] is False
    assert isinstance(ticket_body["unreadForUser"], int)
    assert "slaHint" in ticket_body

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
        "economy_service",
        "incident_service",
        "device_pairing_service",
        "program_application_service",
        "payment_providers",
        "shared_surface_facts",
        "transport_catalog",
        "node_policy",
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
    dataplane_rtt_ms: int | None = None,
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
            dataplane_rtt_ms=dataplane_rtt_ms,
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
    _add_node(
        api,
        code="nl-ams-01",
        health_score=94.0,
        cpu_percent=31.0,
        panel_latency_ms=3800,
        dataplane_rtt_ms=38,
        last_health_at=now,
    )
    _add_node(api, code="de-fra-01", health_score=91.0, cpu_percent=42.0, panel_latency_ms=52, last_health_at=now)
    _add_node(api, code="nl-free", health_score=89.0, cpu_percent=58.0, panel_latency_ms=71, last_health_at=now)
    _add_node(api, code="old-node", health_score=98.0, cpu_percent=20.0, last_health_at=now - timedelta(hours=3))

    start_body = _start_trial(client, install_id="locations-catalog-device")
    response = client.get("/api/client/locations?platform=windows&q=ams", headers=_auth_headers(start_body))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["auto"]["enabled"] is True
    assert body["freePoolCode"] is None
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
    assert amsterdam["latencySource"] == "brain"
    assert amsterdam["load"] == 0.31
    assert amsterdam["variants"] == [
        {
            "id": "direct",
            "label": "Обычный",
            "description": "Прямое подключение",
        }
    ]
    assert amsterdam["probe"] == {"host": "example.test", "port": 443}
    assert amsterdam["measuredAt"] == now.replace(tzinfo=timezone.utc).isoformat()
    assert datetime.fromisoformat(amsterdam["measuredAt"]).utcoffset() == timedelta(0)
    assert "old-node" not in {city["code"] for city in all_cities}


def test_client_locations_catalog_exposes_only_safe_available_bridge_variants(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    rollout_payload = _rollout_payload()
    rollout_payload["ru_bridge_relay"] = {
        "enabled": True,
        "allowlist_node_codes": ["nl", "us"],
        "excluded_node_codes": ["us"],
        "endpoints": [
            {
                "id": "mini",
                "label": "Белые списки",
                "endpoint_host": "bridge-secret.example.test",
                "reality_public_key": "bridge-secret-pbk",
                "reality_short_id": "bridge-secret-sid",
            },
            {
                "id": "ru_spb",
                "label": "Белые списки тип 2",
                "endpoint_host": "bridge-spb-secret.example.test",
                "reality_public_key": "bridge-spb-secret-pbk",
                "reality_short_id": "bridge-spb-secret-sid",
            },
            {
                "id": "disabled",
                "label": "Не показывать",
                "enabled": False,
                "reality_public_key": "disabled-secret-pbk",
            },
            {
                "id": "invalid",
                "label": "Без ключа",
                "endpoint_host": "invalid-secret.example.test",
            },
        ],
    }
    s = api.SessionLocal()
    try:
        api._set_app_setting_json(s=s, key="network_rollout_config", value=rollout_payload)
        s.commit()
    finally:
        s.close()

    now = _utcnow()
    _add_node(api, code="nl-ams-01", last_health_at=now)
    _add_node(api, code="us-nyc-01", last_health_at=now)
    _add_node(api, code="de-fra-01", last_health_at=now)
    start_body = _start_trial(client, install_id="locations-bridge-variants-device")

    response = client.get("/api/client/locations", headers=_auth_headers(start_body))

    assert response.status_code == 200, response.text
    cities = {
        city["code"]: city
        for country in response.json()["countries"]
        for city in country["cities"]
    }
    assert cities["nl-ams-01"]["variants"] == [
        {"id": "direct", "label": "Обычный", "description": "Прямое подключение"},
        {"id": "mini", "label": "Белые списки", "description": "Для ограниченных сетей"},
        {"id": "ru_spb", "label": "Белые списки тип 2", "description": "Для ограниченных сетей"},
    ]
    assert cities["us-nyc-01"]["variants"] == [
        {"id": "direct", "label": "Обычный", "description": "Прямое подключение"}
    ]
    assert cities["de-fra-01"]["variants"] == [
        {"id": "direct", "label": "Обычный", "description": "Прямое подключение"}
    ]
    for city in cities.values():
        for variant in city["variants"]:
            assert set(variant) == {"id", "label", "description"}
    encoded_variants = json.dumps(
        {code: city["variants"] for code, city in cities.items()},
        ensure_ascii=False,
    )
    assert "secret" not in encoded_variants
    assert "§hide§" not in encoded_variants


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
    assert sub_body["identities"] == {
        "telegram": {"linked": False, "username": None, "source": None},
        "email": {"linked": False, "address": None, "verified": False},
    }

    devices = client.get("/api/client/devices", headers=headers)
    assert devices.status_code == 200, devices.text
    device_body = devices.json()
    assert len(device_body["items"]) == 1
    assert device_body["items"][0]["id"] == "account-p1-device"
    assert device_body["items"][0]["current"] is True
    revoke_current = client.delete("/api/client/devices/account-p1-device", headers=headers)
    assert revoke_current.status_code == 409

    from models import EntitlementGrant, LiveUpdate, ServiceIncident, User

    now = _utcnow()
    s = api.SessionLocal()
    try:
        user = s.query(User).filter(User.app_install_id == "account-p1-device").one()
        user.expiry_at = now + timedelta(hours=23)
        s.add(
            ServiceIncident(
                id="00000000-0000-4000-8000-000000009001",
                incident_key="client-inbox-incident",
                title="Проверяем маршрут",
                summary="Один из маршрутов временно работает нестабильно.",
                severity="degraded",
                status="confirmed",
                started_at=now - timedelta(minutes=5),
                affected_node_codes_json="[]",
                compensation_days=1,
                confirmed_by=9999,
                confirmed_at=now - timedelta(minutes=5),
                created_at=now - timedelta(minutes=5),
                updated_at=now,
            )
        )
        s.add(
            LiveUpdate(
                title="Версия 1.0.1",
                summary="Исправили подключение после сна.",
                link="https://pokrov.space/updates/1-0-1",
                published_at=now - timedelta(minutes=10),
                is_active=True,
                sort_order=1,
                created_at=now - timedelta(minutes=10),
                updated_at=now,
            )
        )
        s.add(
            EntitlementGrant(
                id="00000000-0000-4000-8000-000000009002",
                account_id=str(user.account_id),
                legacy_tg_id=int(user.tg_id),
                idempotency_key=f"incident-compensation:v1:test:{user.account_id}",
                source="incident_compensation",
                status="active",
                grant_kind="premium_bonus",
                plan_code="incident_compensation",
                starts_at=now,
                expires_at=now + timedelta(days=1),
                activated_at=now,
                duration_days=1,
                provider="internal_economy",
                metadata_json=json.dumps({"incident_title": "Компенсация за сбой"}),
                created_at=now,
                updated_at=now,
            )
        )
        s.commit()
    finally:
        s.close()

    notifications = client.get("/api/client/notifications", headers=headers)
    assert notifications.status_code == 200, notifications.text
    inbox = notifications.json()
    assert "items" in inbox
    assert "unreadCount" in inbox
    assert inbox["nextCursor"] is None
    assert {item["kind"] for item in inbox["items"]} >= {
        "incident",
        "release",
        "compensation",
        "access",
    }
    assert next(item for item in inbox["items"] if item["kind"] == "incident")["id"] == (
        "incident.00000000-0000-4000-8000-000000009001"
    )
    access_notice = next(item for item in inbox["items"] if item["kind"] == "access")
    assert access_notice["id"].startswith("access.trial.t1.")
    assert access_notice["title"] == "Пробный период закончится завтра"

    mark_read = client.post(
        "/api/client/notifications/read",
        headers=headers,
        json={"ids": [access_notice["id"]]},
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


def test_native_telegram_account_is_already_linked_in_client_profile(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    _seed_rollout(api)
    _add_node(api, code="nl-ams-01")

    started = _start_trial(client, install_id="native-telegram-device")
    headers = _auth_headers(started)
    from models import User

    with api.SessionLocal() as db:
        user = db.query(User).filter(User.app_install_id == "native-telegram-device").one()
        user.is_app_user = False
        user.username = "pokrov_owner"
        db.commit()

    subscription = client.get("/api/client/subscription", headers=headers)
    assert subscription.status_code == 200, subscription.text
    identities = subscription.json()["identities"]
    assert identities["telegram"] == {
        "linked": True,
        "username": "pokrov_owner",
        "source": "native",
    }
    assert identities["email"] == {
        "linked": False,
        "address": None,
        "verified": False,
    }

    link = client.post("/api/client/telegram/link", headers=headers)
    assert link.status_code == 200, link.text
    assert link.json()["linked"] is True
    assert link.json()["start_code"] == ""
    assert "?start=" not in link.json()["bot_url"]


def test_confirmed_incident_admin_flow_previews_and_applies_exact_compensation(
    monkeypatch,
    tmp_path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    _seed_rollout(api)
    _add_node(api, code="nl-ams-01")
    api._require_admin = lambda _init_data, request=None: {"id": 9999}

    start_body = _start_trial(client, install_id="incident-account-device")
    headers = _auth_headers(start_body)
    runtime = client.post(
        "/api/client/runtime/stats",
        headers=headers,
        json={
            "profile_revision": "rev-incident",
            "selected_node_code": "nl-ams-01",
            "runtime_phase": "running",
            "connected": True,
            "uptime_seconds": 120,
        },
    )
    assert runtime.status_code == 200, runtime.text

    now = _utcnow()
    create = client.post(
        "/api/admin/service-incidents",
        json={
            "incident_key": "inc-api-nl-20260723",
            "title": "NL route outage",
            "summary": "Confirmed outage on the NL route.",
            "severity": "major",
            "started_at": (now - timedelta(minutes=5)).isoformat(),
            "affected_node_codes": ["nl-ams-01"],
            "compensation_days": 1,
        },
    )
    assert create.status_code == 200, create.text
    incident_id = create.json()["incident"]["id"]

    resolve = client.post(
        f"/api/admin/service-incidents/{incident_id}/resolve",
        json={"ended_at": (now + timedelta(seconds=1)).isoformat()},
    )
    assert resolve.status_code == 200, resolve.text
    assert resolve.json()["compensationQueued"] is True

    preview = client.post(
        f"/api/admin/service-incidents/{incident_id}/compensate",
        json={"dry_run": True},
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["preview"]["impactedAccounts"] == 1

    wrong_confirmation = client.post(
        f"/api/admin/service-incidents/{incident_id}/compensate",
        json={"dry_run": False, "confirm_incident_key": "wrong"},
    )
    assert wrong_confirmation.status_code == 409

    applied = client.post(
        f"/api/admin/service-incidents/{incident_id}/compensate",
        json={
            "dry_run": False,
            "confirm_incident_key": "inc-api-nl-20260723",
        },
    )
    assert applied.status_code == 200, applied.text
    assert applied.json()["grantedAccounts"] == 1

    repeated = client.post(
        f"/api/admin/service-incidents/{incident_id}/compensate",
        json={
            "dry_run": False,
            "confirm_incident_key": "inc-api-nl-20260723",
        },
    )
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["existingGrants"] == 1

    inbox = client.get("/api/client/notifications", headers=headers)
    assert inbox.status_code == 200, inbox.text
    assert any(item["kind"] == "compensation" for item in inbox.json()["items"])

    public_status = client.get("/api/public/service-status")
    assert public_status.status_code == 200
    assert public_status.json()["status"] == "operational"
    assert public_status.json()["recent"][0]["key"] == "inc-api-nl-20260723"


def test_device_pairing_api_uses_one_time_code_and_returns_real_client_session(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    api._plan_device_limit = lambda _user: 5
    client = TestClient(api.app)
    _seed_rollout(api)
    _add_node(api, code="nl-ams-01")

    owner_session = _start_trial(client, install_id="pairing-owner-device")
    owner_headers = _auth_headers(owner_session)
    issued = client.post("/api/client/device-pairing/codes", headers=owner_headers)
    assert issued.status_code == 200, issued.text
    pairing = issued.json()["pairing"]
    assert pairing["status"] == "active"
    assert len(str(pairing["code"]).replace("-", "")) == 8
    assert str(pairing["pairing_uri"]).startswith("pokrov://pair?code=")
    assert 590 <= int(pairing["ttl_seconds"]) <= 600

    from models import DevicePairingCode

    s = api.SessionLocal()
    try:
        stored = s.query(DevicePairingCode).filter(DevicePairingCode.id == pairing["id"]).one()
        assert str(stored.code_hmac) != str(pairing["code"])
        assert str(pairing["code"]).replace("-", "") not in str(stored.code_hmac)
        assert stored.code_hint == str(pairing["code"])[-4:]
    finally:
        s.close()

    claimed = client.post(
        "/api/client/device-pairing/claim",
        json={
            "code": pairing["code"],
            "install_id": "pairing-new-android-device",
            "device_name": "Android TV",
            "platform": "android_tv",
            "os_version": "14",
            "app_version": "1.0.0",
            "locale": "ru-RU",
            "time_zone": "Europe/Moscow",
        },
    )
    assert claimed.status_code == 200, claimed.text
    claim_body = claimed.json()
    assert claim_body["access_token"]
    assert claim_body["refresh_token"]
    assert claim_body["canonical_account_id"] == owner_session["canonical_account_id"]

    new_headers = {"Authorization": f"Bearer {claim_body['access_token']}"}
    devices = client.get("/api/client/devices", headers=new_headers)
    assert devices.status_code == 200, devices.text
    assert {row["id"] for row in devices.json()["items"]} == {
        "pairing-owner-device",
        "pairing-new-android-device",
    }

    repeated = client.post(
        "/api/client/device-pairing/claim",
        json={
            "code": pairing["code"],
            "install_id": "pairing-third-device",
            "device_name": "Third",
            "platform": "android",
        },
    )
    assert repeated.status_code == 409
    assert repeated.json()["detail"]["code"] == "pairing_code_used"


def test_program_application_api_requires_operator_review_and_idempotent_confirmation(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    _seed_rollout(api)
    _add_node(api, code="nl-ams-01")
    api._require_admin = lambda _init_data, request=None: {"id": 9999}

    start = _start_trial(client, install_id="program-applicant-device")
    headers = _auth_headers(start)
    created = client.post(
        "/api/client/programs/applications",
        headers=headers,
        json={
            "kind": "research",
            "summary": "Воспроизводимый отчёт: соединение не восстанавливается после смены сети.",
            "contact": "@qa_user",
        },
    )
    assert created.status_code == 200, created.text
    application = created.json()["application"]
    assert application["status"] == "submitted"
    assert application["reward_days"] == 0
    assert application["rewarded"] is False

    duplicate = client.post(
        "/api/client/programs/applications",
        headers=headers,
        json={
            "kind": "research",
            "summary": "Ещё один отчёт не должен обходить уже открытую заявку пользователя.",
        },
    )
    assert duplicate.status_code == 409

    wrong = client.post(
        f"/api/admin/program-applications/{application['id']}/review",
        json={
            "status": "approved",
            "operator_note": "Подтверждено на чистом стенде.",
            "reward_days": 3,
            "confirm_application_id": "wrong",
        },
    )
    assert wrong.status_code == 409

    approved = client.post(
        f"/api/admin/program-applications/{application['id']}/review",
        json={
            "status": "approved",
            "operator_note": "Подтверждено на чистом стенде.",
            "reward_days": 3,
            "confirm_application_id": application["id"],
        },
    )
    assert approved.status_code == 200, approved.text
    approved_body = approved.json()["application"]
    assert approved_body["status"] == "rewarded"
    assert approved_body["reward_days"] == 3
    assert approved_body["reward_grant_id"]

    repeated = client.post(
        f"/api/admin/program-applications/{application['id']}/review",
        json={
            "status": "approved",
            "operator_note": "Повторная отправка того же решения.",
            "reward_days": 3,
            "confirm_application_id": application["id"],
        },
    )
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["application"]["reward_grant_id"] == approved_body["reward_grant_id"]

    programs = client.get("/api/client/programs", headers=headers)
    assert programs.status_code == 200, programs.text
    assert programs.json()["applications"][0]["status"] == "rewarded"
    assert programs.json()["applications"][0]["decision_note"] == "Подтверждено на чистом стенде."
    assert next(item for item in programs.json()["capabilities"] if item["kind"] == "affiliate")["enabled"] is False

    inbox = client.get("/api/client/notifications", headers=headers)
    assert inbox.status_code == 200, inbox.text
    program_notice = next(item for item in inbox.json()["items"] if item["kind"] == "program")
    assert program_notice["body"] == "Проверка завершена: начислено 3 дн."


def test_client_support_assistant_and_ticket_presence_contract(monkeypatch, tmp_path, caplog) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    _seed_rollout(api)
    _add_node(api, code="nl-ams-01")

    async def _runtime_summary(**_kwargs):
        return {
            "panel_state": "ok",
            "status": "online",
            "active_connections": 2,
            "last_online_age_seconds": 90,
            "traffic_total_bytes": 0,
        }

    monkeypatch.setattr(api, "_get_user_runtime_summary", _runtime_summary)

    from support_ai_service import SupportAIConfig
    from support_agent_grounding import SupportGroundingEngine
    from support_agent_harness import SupportAgentHarness
    from support_agent_knowledge import SupportKnowledgeStore
    from support_agent_policy import SupportAgentPolicyStore
    from support_agent_provider import ProviderUsage, SynthesisTurn
    from support_agent_service import SupportAgentService
    from support_agent_sessions import OwnerRateLimiter, SessionInFlightGuard, SupportSessionStore

    class _RepeatAdapter:
        def __init__(self) -> None:
            self.requests = []

        async def complete_synthesis(self, **request):
            self.requests.append(request)
            content = json.dumps(
                {
                    "schema_version": "1",
                    "status": "answer",
                    "reply": "Переподключитесь и повторите проверку доступа.",
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            return SynthesisTurn(
                content=content,
                finish_reason="stop",
                usage=ProviderUsage(prompt_tokens=100, completion_tokens=20, cached_tokens=80),
                latency_ms=5,
            )

    class _RecordingHarness:
        def __init__(self, wrapped) -> None:
            self.wrapped = wrapped
            self.requests = []

        async def run(self, request):
            self.requests.append(request)
            return await self.wrapped.run(request)

    policy = SupportAgentPolicyStore().load(Path(api.__file__).resolve().parents[1] / "shared" / "support-agent-policy.json")
    knowledge_store = SupportKnowledgeStore()
    knowledge = knowledge_store.load(Path(api.__file__).resolve().parents[1] / "shared" / "support-ai-knowledge.json")
    adapter = _RepeatAdapter()
    recording_harness = _RecordingHarness(
        SupportAgentHarness(
            policy=policy,
            knowledge=knowledge,
            grounding_engine=SupportGroundingEngine(knowledge_store, knowledge),
            session_store=SupportSessionStore(),
            rate_limiter=OwnerRateLimiter(),
            in_flight_guard=SessionInFlightGuard(),
            adapter=adapter,
        )
    )
    api.SUPPORT_AGENT_SERVICE = SupportAgentService(
        config=SupportAIConfig(
            enabled=True,
            api_key="sk-test",
            api_base_url="https://openrouter.ai/api/v1",
            model="deepseek-v4-flash-0731",
            reasoning_effort="medium",
        ),
        env={"SUPPORT_AI_AGENT_ENABLED": "true"},
        harness_factory=lambda _config, _settings: recording_harness,
        time_source=lambda: 100.0,
    )

    start_body = _start_trial(client, install_id="support-p1-device")
    headers = _auth_headers(start_body)
    from models import IncentiveCampaign, PromoCode

    promo_session = api.SessionLocal()
    try:
        promo_session.add(
            PromoCode(
                code="SUPPORT20",
                promo_type="discount",
                value=20,
                uses_left=10,
            )
        )
        promo_session.add(
            IncentiveCampaign(
                name="Support account offer",
                campaign_type="promo",
                target_value="SUPPORT20",
                segment="all_active",
                max_activations=10,
                activations_count=0,
                is_active=True,
            )
        )
        promo_session.commit()
    finally:
        promo_session.close()

    invalid_scope = client.post(
        "/api/client/support/assistant",
        headers=headers,
        json={"message": "Подключено, но интернета нет", "scope": "billing"},
    )
    assert invalid_scope.status_code == 422

    too_many_diagnostics = client.post(
        "/api/client/support/assistant",
        headers=headers,
        json={
            "message": "Подключено, но интернета нет",
            "scope": "support",
            "safeDiagnostics": {f"unknown_{index}": "value" for index in range(21)},
        },
    )
    assert too_many_diagnostics.status_code == 422
    assert recording_harness.requests == []

    oversized_diagnostics = client.post(
        "/api/client/support/assistant",
        headers=headers,
        json={
            "message": "Подключено, но интернета нет",
            "scope": "support",
            "safeDiagnostics": {"platform": "x" * 513},
        },
    )
    assert oversized_diagnostics.status_code == 422
    assert recording_harness.requests == []

    attacker_value = "vless://private-profile sk-private-token"

    assistant = client.post(
        "/api/client/support/assistant",
        headers=headers,
        json={
            "message": "Подключено, но интернета нет",
            "scope": "support",
            "safeDiagnostics": {
                "app_version": "1.0.0",
                "platform": "windows",
                "route_mode": "all_except_ru",
                "connection_status": "connected",
                "connection_active": True,
                "current_location_label": "Франкфурт · Белые списки",
                "enhanced_protection_state": "fallback",
                "enhanced_protection_consent": True,
                "enhanced_protection_available": True,
                "attacker_key": attacker_value,
            },
        },
    )
    assert assistant.status_code == 200, assistant.text
    assistant_body = assistant.json()
    assert assistant_body["reply"]
    assert assistant_body["suggestedActions"]
    assert assistant_body["shouldEscalate"] is False
    assert assistant_body["source"] == "support_agent"
    generated_session_id = assistant_body["assistantSessionId"]
    assert 16 <= len(generated_session_id) <= 64
    first_diagnostics = dict(recording_harness.requests[0].safe_diagnostics)
    assert {
        "app_version": "1.0.0",
        "connection_status": "connected",
        "connection_active": True,
        "current_location_label": "Франкфурт · Белые списки",
        "enhanced_protection_available": True,
        "enhanced_protection_consent": True,
        "enhanced_protection_state": "fallback",
        "platform": "windows",
        "route_mode": "all_except_ru",
    }.items() <= first_diagnostics.items()
    assert first_diagnostics["account_access_state"] == "trial_premium"
    assert first_diagnostics["account_days_left"] == 5
    assert first_diagnostics["account_device_count"] == 1
    assert first_diagnostics["account_telegram_linked"] is False
    assert first_diagnostics["panel_active_connections"] == 2
    assert first_diagnostics["panel_last_online_age_seconds"] == 90
    assert first_diagnostics["panel_runtime_state"] == "online"
    assert first_diagnostics["telegram_bonus_state"] == "available"
    assert first_diagnostics["public_promo_state"] == "available"
    assert first_diagnostics["public_promo_codes"] == "SUPPORT20"

    supplied = client.post(
        "/api/client/support/assistant",
        headers=headers,
        json={
            "message": "Подключено, но интернета нет",
            "scope": "support",
            "assistant_session_id": generated_session_id,
        },
    )
    assert supplied.status_code == 200, supplied.text
    assert supplied.json()["assistantSessionId"] == generated_session_id

    invalid_session = client.post(
        "/api/client/support/assistant",
        headers=headers,
        json={
            "message": "Подключено, но интернета нет",
            "scope": "support",
            "assistantSessionId": "../../invalid",
        },
    )
    assert invalid_session.status_code == 200, invalid_session.text
    assert invalid_session.json()["assistantSessionId"] != "../../invalid"

    for _index in range(3):
        response = client.post(
            "/api/client/support/assistant",
            headers=headers,
            json={
                "message": "Подключено, но интернета нет",
                "scope": "support",
                "assistantSessionId": generated_session_id,
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["source"] == "support_agent"

    seventh = client.post(
        "/api/client/support/assistant",
        headers=headers,
        json={
            "message": "Подключено, но интернета нет",
            "scope": "support",
            "assistantSessionId": generated_session_id,
        },
    )
    assert seventh.status_code == 200, seventh.text
    assert seventh.json()["source"] == "local_fallback"
    assert seventh.json()["shouldEscalate"] is True
    assert len(adapter.requests) == 6

    second_start = _start_trial(client, install_id="support-p2-device")
    second_headers = _auth_headers(second_start)
    cross_owner = client.post(
        "/api/client/support/assistant",
        headers=second_headers,
        json={
            "message": "Подключено, но интернета нет",
            "scope": "support",
            "assistantSessionId": generated_session_id,
        },
    )
    assert cross_owner.status_code == 200, cross_owner.text
    assert cross_owner.json()["source"] == "support_agent"
    assert recording_harness.requests[0].session_scope.client_session_id == generated_session_id
    assert recording_harness.requests[-1].session_scope.client_session_id == generated_session_id
    assert (
        recording_harness.requests[0].session_scope.internal_session_key
        != recording_harness.requests[-1].session_scope.internal_session_key
    )

    from models import Event

    event_session = api.SessionLocal()
    try:
        events = event_session.query(Event).filter(Event.event_name == "client_support_assistant").all()
        serialized_events = "\n".join(str(event.meta_json or "") for event in events)
    finally:
        event_session.close()
    for diagnostic_key in (
        "account_access_state",
        "account_days_left",
        "account_device_count",
        "account_plan",
        "account_telegram_linked",
        "app_version",
        "connection_status",
        "connection_active",
        "current_location_label",
        "panel_active_connections",
        "panel_last_online_age_seconds",
        "panel_runtime_state",
        "telegram_bonus_state",
        "public_promo_state",
        "public_promo_codes",
    ):
        assert diagnostic_key in serialized_events
    assert "attacker_key" not in serialized_events
    assert attacker_value not in serialized_events
    assert attacker_value not in caplog.text

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

    calls_before_denial = len(recording_harness.requests)
    denied_ticket = client.post(
        "/api/client/support/assistant",
        headers=second_headers,
        json={
            "ticketId": ticket_body["id"],
            "message": "Подключено, но интернета нет",
            "scope": "support",
            "assistantSessionId": generated_session_id,
        },
    )
    assert denied_ticket.status_code == 403
    assert len(recording_harness.requests) == calls_before_denial

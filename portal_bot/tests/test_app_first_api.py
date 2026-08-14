from __future__ import annotations

import importlib
import hashlib
import hmac
import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


class _FakePanel:
    async def add_client(self, **_kwargs):
        return True

    async def close(self):
        return None


def _load_api(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "portal-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "portal-test-secret")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.pokrov.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "pokrov.test")
    monkeypatch.setenv("PUBLIC_CHANNEL", "pokrov_vpn")
    monkeypatch.setenv("BOT_USERNAME", "pokrov_vpnbot")
    monkeypatch.setenv("SUPPORT_BOT_USERNAME", "pokrov_supportbot")
    monkeypatch.setenv("ANTIABUSE_HMAC_SECRET", "antiabuse-api-test-secret")
    monkeypatch.setenv("ANTIABUSE_HMAC_VERSION", "2")

    for name in [
        "api",
        "account_experience_service",
        "app_first_service",
        "account_foundation_service",
        "antiabuse_privacy_service",
        "auth_session_service",
        "config",
        "db",
        "economy_service",
        "migrations",
        "models",
        "web_auth_service",
        "control_panel",
        "nodes_repo",
        "tickets_repo",
        "events_service",
        "channel_bonus_service",
        "offers_service",
        "pay_attempts_service",
        "points_service",
        "free_cycle_service",
        "gift_cards_service",
        "payment_providers",
    ]:
        monkeypatch.setitem(sys.modules, name, None)
        monkeypatch.delitem(sys.modules, name)

    api = importlib.import_module("api")
    monkeypatch.setattr(api, "ControlPanel", _FakePanel)
    return api


def _install_fake_panel(monkeypatch, api):
    monkeypatch.setattr(api, "ControlPanel", _FakePanel)


def _promote_install_to_paid(api, *, install_id: str, now):
    db = api.SessionLocal()
    try:
        user = db.query(api.User).filter_by(app_install_id=install_id).one()
        user.sub_type = "PAID"
        user.current_plan_code = "month"
        user.is_active = True
        user.expiry_at = now + timedelta(days=30)
        grant = api.EntitlementGrant(
            id=f"00000000-0000-4000-8000-{abs(int(user.tg_id)) % 10**12:012d}",
            account_id=str(user.account_id),
            legacy_tg_id=int(user.tg_id),
            idempotency_key=f"test-provider-payment:{user.account_id}",
            source="provider_payment",
            status="active",
            grant_kind="paid_access",
            plan_code="month",
            starts_at=now - timedelta(days=1),
            expires_at=now + timedelta(days=30),
            activated_at=now - timedelta(days=1),
            duration_days=31,
            provider="test",
            created_at=now - timedelta(days=1),
            updated_at=now,
        )
        db.add(grant)
        db.commit()
        return int(user.tg_id), str(user.account_id)
    finally:
        db.close()


def test_load_api_restores_collected_core_modules_after_monkeypatch_context(tmp_path):
    module_names = ("models", "economy_service", "account_foundation_service")
    originals = {name: importlib.import_module(name) for name in module_names}

    with pytest.MonkeyPatch.context() as isolated:
        _load_api(isolated, tmp_path)

    assert {name: sys.modules.get(name) for name in module_names} == originals


def test_load_api_removes_core_module_that_was_absent_before_context(tmp_path):
    with pytest.MonkeyPatch.context() as outer:
        outer.delitem(sys.modules, "economy_service", raising=False)
        assert "economy_service" not in sys.modules

        with pytest.MonkeyPatch.context() as isolated:
            _load_api(isolated, tmp_path)

        assert "economy_service" not in sys.modules


def test_load_api_removes_transitive_service_that_was_absent_before_context(tmp_path):
    with pytest.MonkeyPatch.context() as outer:
        outer.delitem(sys.modules, "app_first_service", raising=False)
        assert "app_first_service" not in sys.modules

        with pytest.MonkeyPatch.context() as isolated:
            _load_api(isolated, tmp_path)

        assert "app_first_service" not in sys.modules


def test_start_trial_returns_session_and_real_device_payload(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    start_trial_response = client.post(
        "/api/client/session/start-trial",
        headers={"X-Forwarded-For": "198.51.100.87"},
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
    assert payload["access_token"] == payload["session_token"]
    assert payload["refresh_token"].startswith("pkr_rt_")
    assert payload["session"]["session_id"]
    assert payload["session"]["device_id"]
    assert payload["session"]["canonical_account_id"]
    assert payload["session"]["refresh_token"] == payload["refresh_token"]

    db = api.SessionLocal()
    try:
        stored = db.query(api.AuthSession).filter_by(id=payload["session"]["session_id"]).one()
        assert stored.device_id == payload["session"]["device_id"]
        assert stored.refresh_token_hash != payload["refresh_token"]
        assert payload["refresh_token"] not in stored.refresh_token_hash
        antiabuse = db.query(api.AntiAbuseEvent).filter_by(event_kind="trial_reserved").one()
        assert antiabuse.account_id == payload["session"]["canonical_account_id"]
        assert antiabuse.device_id == payload["session"]["device_id"]
        assert antiabuse.session_id == payload["session"]["session_id"]
        assert antiabuse.raw_ip == "198.51.100.87"
        assert antiabuse.install_hmac
        assert antiabuse.ip_full_hmac
        assert antiabuse.ip_prefix_hmac
        assert antiabuse.hmac_version == 2
    finally:
        db.close()

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


def test_account_onboarding_and_connection_milestone_are_server_scoped(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    started = client.post(
        "/api/client/session/start-trial",
        headers={"X-Forwarded-For": "198.51.100.88"},
        json={
            "install_id": "experience-install-123",
            "device_name": "Pixel test",
            "platform": "android",
        },
    )
    assert started.status_code == 200
    token = started.json()["session_token"]
    auth = {"Authorization": f"Bearer {token}"}
    session_payload = client.get("/api/auth/session", headers=auth).json()
    tg_id = int(session_payload["user"]["account_id"])

    before = client.get(f"/api/user/{tg_id}", headers=auth)
    assert before.status_code == 200
    assert before.json()["experience"] == {
        "onboarding": {
            "version": 1,
            "status": "pending",
            "should_show": True,
            "updated_at": None,
        },
        "first_connection": {
            "state": "none",
            "reported_at": None,
            "verified_at": None,
        },
        "next_step": "connect",
    }

    completed = client.post(
        "/api/account/experience/onboarding",
        headers=auth,
        json={"status": "completed"},
    )
    assert completed.status_code == 200
    assert completed.json()["experience"]["onboarding"]["status"] == "completed"
    assert completed.json()["experience"]["onboarding"]["should_show"] is False

    runtime = client.post(
        "/api/client/runtime/stats",
        headers=auth,
        json={"runtime_phase": "running", "connected": True, "uptime_seconds": 12},
    )
    assert runtime.status_code == 200

    after = client.get(f"/api/user/{tg_id}", headers=auth).json()
    assert after["experience"]["first_connection"]["state"] == "reported"
    assert after["experience"]["first_connection"]["reported_at"]
    assert after["experience"]["first_connection"]["verified_at"] is None
    assert after["sync"]["connected_once"] is True


def test_security_event_is_mirrored_to_privacy_ledger(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)

    api._record_security_event(
        "rate_limit_hit",
        scope="email_otp",
        client_ip="203.0.113.42",
        reason="limit_exceeded",
        meta={"refresh_token": "must-not-survive", "attempt": 6},
    )

    db = api.SessionLocal()
    try:
        security = db.query(api.SecurityEvent).filter_by(event_type="rate_limit_hit").one()
        antiabuse = db.query(api.AntiAbuseEvent).filter_by(event_kind="rate_limit_hit").one()
        assert security.client_ip == "203.0.113.42"
        assert antiabuse.source == "api_security"
        assert antiabuse.raw_ip == "203.0.113.42"
        assert antiabuse.ip_full_hmac
        assert antiabuse.ip_prefix_hmac
        assert "must-not-survive" not in str(antiabuse.metadata_json)
    finally:
        db.close()


def test_start_trial_rolls_back_account_when_ledger_insert_fails(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    def _fail_ledger(*_args, **_kwargs):
        raise RuntimeError("ledger unavailable")

    monkeypatch.setattr(api, "record_antiabuse_event", _fail_ledger)

    with pytest.raises(RuntimeError, match="ledger unavailable"):
        client.post(
            "/api/client/session/start-trial",
            json={
                "install_id": "install-ledger-failure",
                "device_name": "Test device",
                "platform": "android",
                "os_version": "15",
                "app_version": "1.0.0",
                "locale": "ru",
                "time_zone": "Europe/Moscow",
            },
        )

    db = api.SessionLocal()
    try:
        assert db.query(api.User).filter_by(app_install_id="install-ledger-failure").count() == 0
        assert db.query(api.AntiAbuseEvent).count() == 0
    finally:
        db.close()


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
    assert payload["access"]["trial_state"] == "reserved"
    assert payload["access"]["reserved_at"]
    assert payload["access"]["reservation_expires_at"]
    assert payload["access"]["activated_at"] is None
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


def test_start_trial_ignores_environment_trial_day_override(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_TRIAL_DEFAULT_DAYS", "19")
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    response = client.post(
        "/api/client/session/start-trial",
        json={"install_id": "install-fixed-five-days", "device_name": "Pixel", "platform": "android"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert api.APP_TRIAL_DEFAULT_DAYS == 5
    assert api.APP_TRIAL_MAX_DAYS == 5
    assert body["access"]["trial_days"] == 5
    db = api.SessionLocal()
    try:
        grant = db.query(api.EntitlementGrant).filter_by(
            account_id=body["canonical_account_id"],
            source="premium_trial",
        ).one()
        assert grant.duration_days == 5
    finally:
        db.close()


def test_signed_observer_evidence_activates_once_while_client_telemetry_cannot(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    start = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-observer-activation",
            "device_name": "Pixel",
            "platform": "android",
        },
    )
    assert start.status_code == 200, start.text
    body = start.json()
    token_headers = {"Authorization": f"Bearer {body['access_token']}"}

    confirm = client.post("/api/connect/confirm", headers=token_headers)
    telemetry = client.post(
        "/api/events",
        headers=token_headers,
        json={"event_name": "clicked_connect", "source": "client"},
    )
    assert confirm.status_code == 200
    assert telemetry.status_code == 200

    db = api.SessionLocal()
    try:
        grant = db.query(api.EntitlementGrant).filter_by(account_id=body["canonical_account_id"], source="premium_trial").one()
        assert grant.status == "reserved"
        assert grant.activated_at is None
        observed_at = grant.reserved_at + timedelta(hours=2)
        assert db.query(api.ConnectionEvidence).count() == 0
        node = api.Node(
            code="trial-node",
            name="Trial node",
            host="trial-node.pokrov.test",
            vless_port=443,
            panel_base_url="https://trial-node.pokrov.test:8444",
            panel_path="/panel/",
            panel_user="observer",
            panel_pass="not-returned",
            inbound_id=31,
            enabled=True,
            observer_push_secret="observer-signing-secret",
        )
        db.add(node)
        db.commit()
    finally:
        db.close()

    observer_body = json.dumps(
        {
            "batch_id": "trial-batch-001",
            "observations": [
                {
                    "occurred_at": observed_at.isoformat(),
                    "client_tg_id": int(body["account_id"]),
                    "source_ip": "198.51.100.10",
                }
            ],
        },
        separators=(",", ":"),
    ).encode("utf-8")
    timestamp = int(time.time())
    canonical = f"trial-node\n{timestamp}\n{observer_body.decode('utf-8')}".encode("utf-8")
    signature = hmac.new(b"observer-signing-secret", canonical, hashlib.sha256).hexdigest()
    observer_headers = {
        "Content-Type": "application/json",
        "X-Portal-Node": "trial-node",
        "X-Portal-Timestamp": str(timestamp),
        "X-Portal-Signature": signature,
    }
    first = client.post("/api/internal/observer/batches", content=observer_body, headers=observer_headers)
    replay = client.post("/api/internal/observer/batches", content=observer_body, headers=observer_headers)

    assert first.status_code == 200, first.text
    assert replay.status_code == 200, replay.text
    assert first.json()["activated_trial_count"] == 1
    assert replay.json()["activated_trial_count"] == 0
    assert "subscription_url" not in json.dumps(first.json())
    assert "observer-signing-secret" not in json.dumps(first.json())

    db = api.SessionLocal()
    try:
        grant = db.query(api.EntitlementGrant).filter_by(account_id=body["canonical_account_id"], source="premium_trial").one()
        assert grant.status == "active"
        assert grant.activated_at == observed_at
        assert grant.expires_at == observed_at + timedelta(days=5)
        assert db.query(api.ConnectionEvidence).count() == 1
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


def test_start_trial_requires_recovery_for_existing_device_session(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    class CountingPanel:
        calls = 0

        async def add_client(self, **_kwargs):
            type(self).calls += 1
            return True

        async def close(self):
            return None

    monkeypatch.setattr(api, "ControlPanel", CountingPanel)

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
    db = api.SessionLocal()
    try:
        user = db.query(api.User).filter_by(tg_id=int(first.json()["account_id"])).one()
        before = (user.app_device_name, user.app_platform, user.app_last_seen_at, user.app_last_ip)
    finally:
        db.close()

    second = client.post(
        "/api/client/session/start-trial",
        headers={"X-Real-IP": "203.0.113.77"},
        json={**request_payload, "device_name": "Injected name", "platform": "android"},
    )

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.headers["X-POKROV-Auth-Error"] == "device_recovery_required"
    assert CountingPanel.calls == 1

    first_session = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {first.json()['session_token']}"},
    )

    assert first_session.status_code == 200
    db = api.SessionLocal()
    try:
        assert db.query(api.AuthSession).count() == 1
        user = db.query(api.User).filter_by(tg_id=int(first.json()["account_id"])).one()
        after = (user.app_device_name, user.app_platform, user.app_last_seen_at, user.app_last_ip)
        assert after == before
    finally:
        db.close()


def test_app_route_policy_rejects_empty_selected_apps_without_persisting(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-route-empty-selected-apps",
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

    response = client.post(
        "/api/client/route-policy",
        headers={"Authorization": f"Bearer {token}"},
        json={"route_mode": "selected_apps", "selected_apps": []},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == {
        "code": "selected_apps_required",
        "message": "Select at least one app before using selected-apps routing.",
    }
    persisted = client.get(
        "/api/client/route-policy",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert persisted.status_code == 200
    assert persisted.json()["route_mode"] == "all_traffic"
    assert persisted.json()["selected_apps"] == []


def test_failed_bootstrap_does_not_consume_unreturned_refresh_credential(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app, raise_server_exceptions=False)
    original_build_client_policy = api.app_first_service.build_client_policy

    def _fail_client_policy(**_kwargs):
        raise RuntimeError("synthetic payload failure")

    api.app_first_service.build_client_policy = _fail_client_policy
    request_payload = {
        "install_id": "install-bootstrap-rollback",
        "device_name": "Windows PC",
        "platform": "windows",
    }
    failed = client.post("/api/client/session/start-trial", json=request_payload)
    assert failed.status_code == 500

    db = api.SessionLocal()
    try:
        assert db.query(api.AuthSession).count() == 0
    finally:
        db.close()

    api.app_first_service.build_client_policy = original_build_client_policy
    retried = client.post("/api/client/session/start-trial", json=request_payload)
    assert retried.status_code == 200
    assert retried.json()["refresh_token"].startswith("pkr_rt_")


def test_refresh_rotates_once_and_replay_revokes_family(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    started = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-refresh-api",
            "device_name": "Pixel 10",
            "platform": "android",
            "os_version": "16",
            "app_version": "1.0.0",
            "locale": "ru",
            "time_zone": "Europe/Moscow",
        },
    )
    assert started.status_code == 200
    first = started.json()

    rotated = client.post(
        "/api/client/session/refresh",
        json={"refresh_token": first["refresh_token"]},
    )
    assert rotated.status_code == 200
    second = rotated.json()
    assert second["access_token"] == second["session_token"]
    assert second["refresh_token"] != first["refresh_token"]
    assert second["session_id"] != first["session"]["session_id"]
    assert second["refresh_family_id"] == first["session"]["refresh_family_id"]
    assert second["account_id"] == first["account_id"]
    assert second["canonical_account_id"] == first["canonical_account_id"]
    assert second["session"]["account_id"] == first["account_id"]

    old_access_during_overlap = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {first['access_token']}"},
    )
    assert old_access_during_overlap.status_code == 200

    replay = client.post(
        "/api/client/session/refresh",
        json={"refresh_token": first["refresh_token"]},
    )
    assert replay.status_code == 401
    assert replay.headers["X-POKROV-Auth-Error"] == "refresh_reuse_detected"

    revoked_access = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {second['access_token']}"},
    )
    assert revoked_access.status_code == 401
    assert revoked_access.headers["X-POKROV-Auth-Error"] == "session_revoked"

    db = api.SessionLocal()
    try:
        family = db.query(api.AuthSession).filter_by(refresh_family_id=second["refresh_family_id"]).all()
        assert len(family) == 2
        assert all(row.revoked_at is not None for row in family)
    finally:
        db.close()


def test_real_device_registry_revoke_requires_fresh_auth(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    started = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-device-revoke",
            "device_name": "Surface Laptop",
            "platform": "windows",
            "os_version": "11",
            "app_version": "1.0.0",
            "locale": "ru",
            "time_zone": "Europe/Moscow",
        },
    )
    assert started.status_code == 200
    body = started.json()
    headers = {"Authorization": f"Bearer {body['access_token']}"}

    renamed = client.patch(
        "/api/client/devices/current",
        headers=headers,
        json={
            "device_name": "POKROV Windows Surface Laptop",
            "platform": "windows",
            "os_version": "11 24H2",
            "app_version": "1.0.6",
        },
    )
    assert renamed.status_code == 200
    assert renamed.json()["ok"] is True

    devices = client.get("/api/client/devices", headers=headers)
    assert devices.status_code == 200
    item = devices.json()["items"][0]
    assert item["id"] == "install-device-revoke"
    assert item["registryId"] == body["session"]["device_id"]
    assert item["current"] is True
    assert item["label"] == "POKROV Windows Surface Laptop"
    assert item["osVersion"] == "11 24H2"
    assert item["appVersion"] == "1.0.6"

    stale = client.delete(f"/api/client/devices/{item['registryId']}", headers=headers)
    assert stale.status_code == 409
    assert stale.headers["X-POKROV-Auth-Error"] == "fresh_auth_required"

    db = api.SessionLocal()
    try:
        actor = db.query(api.AuthSession).filter_by(id=body["session"]["session_id"]).one()
        actor.fresh_auth_at = api._utcnow()
        db.commit()
    finally:
        db.close()

    revoked = client.delete(f"/api/client/devices/{item['registryId']}", headers=headers)
    assert revoked.status_code == 200
    assert revoked.json()["ok"] is True
    assert revoked.json()["device"]["active"] is False

    rejected = client.get("/api/auth/session", headers=headers)
    assert rejected.status_code == 401
    assert rejected.headers["X-POKROV-Auth-Error"] == "session_revoked"


def test_refresh_rate_limits_by_hashed_credential_before_cgnat_ceiling(monkeypatch, tmp_path):
    monkeypatch.setenv("API_RATE_LIMIT_SESSION_REFRESH_PER_MINUTE", "1")
    monkeypatch.setenv("API_RATE_LIMIT_SESSION_REFRESH_IP_PER_MINUTE", "10")
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    headers = {"X-Real-IP": "198.51.100.200"}

    first = client.post(
        "/api/client/session/start-trial",
        headers=headers,
        json={"install_id": "install-cgnat-one", "device_name": "Phone one", "platform": "android"},
    ).json()
    second = client.post(
        "/api/client/session/start-trial",
        headers=headers,
        json={"install_id": "install-cgnat-two", "device_name": "Phone two", "platform": "android"},
    ).json()

    first_refresh = client.post(
        "/api/client/session/refresh",
        headers=headers,
        json={"refresh_token": first["refresh_token"]},
    )
    second_refresh = client.post(
        "/api/client/session/refresh",
        headers=headers,
        json={"refresh_token": second["refresh_token"]},
    )

    assert first_refresh.status_code == 200, first_refresh.text
    assert second_refresh.status_code == 200, second_refresh.text


def test_client_can_revoke_current_session_without_revoking_device(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    started = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-session-logout",
            "device_name": "Pixel 10",
            "platform": "android",
        },
    )
    assert started.status_code == 200
    body = started.json()
    headers = {"Authorization": f"Bearer {body['access_token']}"}

    revoked = client.post("/api/client/session/revoke", headers=headers)
    assert revoked.status_code == 200
    assert revoked.json() == {"ok": True, "session_id": body["session"]["session_id"], "revoked": True}

    rejected = client.get("/api/auth/session", headers=headers)
    assert rejected.status_code == 401
    assert rejected.headers["X-POKROV-Auth-Error"] == "session_revoked"

    db = api.SessionLocal()
    try:
        device = db.query(api.AccountDevice).filter_by(id=body["session"]["device_id"]).one()
        assert device.state == "active"
        assert device.revoked_at is None
    finally:
        db.close()


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
    assert repeated_same_install.status_code == 409, repeated_same_install.text
    assert repeated_same_install.headers["X-POKROV-Auth-Error"] == "device_recovery_required"
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
    assert exchanged["cookie_bound"] is True
    set_cookie = exchange_response.headers.get("set-cookie", "")
    assert "portal_web_session=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Secure" in set_cookie
    assert exchanged["target_path"] == "/profile"

    session_response = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {exchanged['token']}"},
    )
    assert session_response.status_code == 200, session_response.text
    session_payload = session_response.json()
    assert session_payload["user"]["auth_origin"] == "app_cabinet_handoff"

    pending_handoff = client.post(
        "/api/client/cabinet-token",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_path": "/support"},
    )
    assert pending_handoff.status_code == 200

    logout_response = client.post(
        "/api/client/session/revoke",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_response.status_code == 200
    revoked_cabinet = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {exchanged['token']}"},
    )
    assert revoked_cabinet.status_code == 401
    assert revoked_cabinet.headers["X-POKROV-Auth-Error"] == "session_revoked"
    rejected_exchange = client.post(
        "/api/auth/cabinet-handoff/exchange",
        json={"handoff_token": pending_handoff.json()["handoff_token"]},
    )
    assert rejected_exchange.status_code == 401
    assert rejected_exchange.headers["X-POKROV-Auth-Error"] == "session_revoked"

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

    _promote_install_to_paid(
        api,
        install_id="install-bonus",
        now=api._utcnow(),
    )

    claim_response = client.post(
        "/api/bonuses/channel/claim",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert claim_response.status_code == 200
    payload = claim_response.json()
    assert payload["ok"] is True
    assert payload["already_claimed"] is False
    assert payload["premium_days"] == 5

    user_response = client.get(
        f"/api/user/{account_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert user_response.status_code == 200
    user_payload = user_response.json()
    assert user_payload["sub_type"] == "PAID"
    assert user_payload["bonuses"]["channel_bonus"]["claimed_at"]


def test_channel_subscriber_check_is_read_only_for_linked_app_account(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    membership_checks = 0

    async def fake_is_channel_member(channel_username: str, tg_id: int):
        nonlocal membership_checks
        membership_checks += 1
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
    assert payload["bonus_days"] == 5
    assert payload["points_granted"] == 0
    assert payload["campaign_marked"] is False
    assert membership_checks == 1

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

    lesson_response = client.post(
        "/api/events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "event_name": "routing_lesson_completed",
            "source": "app",
            "meta": {"surface": "route_explainer"},
        },
    )
    assert lesson_response.status_code == 200, lesson_response.text

    summary_response = client.get(
        "/api/bonuses/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    referral_response = client.get(
        "/api/bonuses/referral/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    bonuses_response = client.get(
        "/api/bonuses",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert summary_response.status_code == 200, summary_response.text
    summary = summary_response.json()
    assert summary["reward_access"] == {
        "eligible": False,
        "state": "paid_required",
        "reason": "active_paid_required",
        "message": (
            "Telegram-бонус уже получен. Рулетка, календарь и реферальные "
            "начисления откроются после первой оплаты."
        ),
    }
    assert summary["ok"] is True
    assert summary["referral_count"] == 3
    assert summary["referral_code"] == "POKROV3"
    assert summary["channel_bonus_claimed_at"]
    assert summary["channel_bonus"]["claimed"] is True
    assert summary["channel_bonus"]["offer_days"] == 5
    assert summary["channel_bonus"]["claimed_days"] == 10
    assert summary["channel_bonus"]["eligible"] is True
    assert summary["channel_bonus"]["can_claim"] is False
    assert summary["channel_bonus"]["reason"] == "already_claimed"
    assert summary["referral"]["count"] == 3
    assert summary["referral"]["code"] == "POKROV3"
    assert "start=ref_POKROV3" in summary["referral"]["link"]
    assert summary["promo"]["redeem_endpoint"] == "/api/bonuses/promo/redeem"
    assert summary["promo"]["pending_discount_pct"] == 20
    assert summary["wheel"]["enabled"] is True
    assert summary["wheel"]["eligible"] is False
    assert summary["wheel"]["reason"] == "active_paid_required"
    assert summary["calendar"]["enabled"] is False
    assert summary["calendar"]["eligible"] is False
    assert summary["calendar"]["reason"] == "bonus_feature_disabled"
    quests = {item["id"]: item for item in summary["achievements"]["quests"]}
    assert quests["first_tunnel"]["completed"] is False
    assert quests["first_tunnel"]["verification"] == "connection_evidence"
    assert quests["second_device"]["progress"] == 1
    assert quests["second_device"]["target"] == 2
    assert quests["routing_lesson"]["completed"] is True
    assert quests["quality_feedback"]["completed"] is False
    assert summary["achievements"]["quest_rewards_enabled"] is False

    assert referral_response.status_code == 200, referral_response.text
    referral = referral_response.json()
    assert referral["ok"] is True
    assert referral["count"] == 3
    assert referral["code"] == "POKROV3"
    assert referral["bonus_days"] == api.REFERRAL_BONUS_DAYS
    assert referral["tier"]["tier_key"]

    assert bonuses_response.status_code == 200, bonuses_response.text
    channel = bonuses_response.json()["channel"]
    assert channel["offer_days"] == 5
    assert channel["claimed_days"] == 10


def test_paid_bonus_summary_creates_one_stable_referral_link(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)
    _install_fake_panel(monkeypatch, api)
    client = TestClient(api.app)
    install_id = "install-paid-referral-link"

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": install_id,
            "device_name": "Pixel Fold",
            "platform": "android",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]
    trial_summary = client.get(
        "/api/bonuses/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert trial_summary.status_code == 200, trial_summary.text
    assert trial_summary.json()["referral_code"] == ""

    _promote_install_to_paid(api, install_id=install_id, now=api._utcnow())
    paid_summary = client.get(
        "/api/bonuses/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert paid_summary.status_code == 200, paid_summary.text
    first_code = paid_summary.json()["referral_code"]
    assert re.fullmatch(r"SWAZ[A-Z0-9]{4}", first_code)
    assert paid_summary.json()["referral"]["code"] == first_code
    assert paid_summary.json()["referral"]["link"].endswith(
        f"start=ref_{first_code}"
    )

    repeated = client.get(
        "/api/bonuses/referral/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["code"] == first_code
    assert repeated.json()["link"].endswith(f"start=ref_{first_code}")


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
    monkeypatch.setenv("BONUS_WHEEL_ENABLED", "false")
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
    assert wheel_payload["eligible"] is False
    assert wheel_payload["reason"] == "bonus_feature_disabled"
    assert wheel_payload["sectors"] == []
    assert "weights" not in wheel_payload
    assert "weight" not in str(wheel_payload).lower()

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


@pytest.mark.parametrize("sub_type", ("FREE", "TRIAL", "BONUS"))
def test_non_paid_reward_mutation_is_forbidden(monkeypatch, tmp_path, sub_type):
    monkeypatch.setenv("BONUS_WHEEL_ENABLED", "true")
    monkeypatch.setenv("BONUS_CALENDAR_ENABLED", "true")
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": f"install-non-paid-{sub_type.lower()}",
            "device_name": "Pixel",
            "platform": "android",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]
    headers = {"Authorization": f"Bearer {token}"}

    db = api.SessionLocal()
    try:
        user = db.query(api.User).filter_by(app_install_id=f"install-non-paid-{sub_type.lower()}").one()
        user.sub_type = sub_type
        user.current_plan_code = sub_type.lower()
        db.commit()
    finally:
        db.close()

    wheel_spin = client.post("/api/bonuses/wheel/spin", headers=headers)
    calendar_checkin = client.post("/api/bonuses/calendar/checkin", headers=headers)

    assert wheel_spin.status_code == 403, wheel_spin.text
    assert wheel_spin.json()["detail"]["code"] == "active_paid_required"
    assert calendar_checkin.status_code == 403, calendar_checkin.text
    assert calendar_checkin.json()["detail"]["code"] == "active_paid_required"


def test_paid_reward_api_uses_account_ledger_and_idempotent_calendar(monkeypatch, tmp_path):
    monkeypatch.setenv("BONUS_WHEEL_ENABLED", "true")
    monkeypatch.setenv("BONUS_CALENDAR_ENABLED", "true")
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    install_id = "install-live-paid-reward-ledger"
    trial_response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": install_id,
            "device_name": "Pixel",
            "platform": "android",
            "trial_days": 5,
        },
    )
    token = trial_response.json()["session_token"]
    headers = {"Authorization": f"Bearer {token}"}
    base_now = datetime(2026, 7, 20, 12, 0, 0)
    tg_id, account_id = _promote_install_to_paid(api, install_id=install_id, now=base_now)
    current_now = [base_now]
    monkeypatch.setattr(api, "_reward_now", lambda: current_now[0])

    wheel_state = client.get("/api/bonuses/wheel/state", headers=headers)
    assert wheel_state.status_code == 200, wheel_state.text
    wheel_payload = wheel_state.json()
    assert wheel_payload["enabled"] is True
    assert wheel_payload["eligible"] is True
    assert wheel_payload["can_spin"] is True
    assert wheel_payload["sectors"] == [1, 3, 7, 30]
    assert "weights" not in wheel_payload
    assert "probability" not in json.dumps(wheel_payload).lower()

    wheel_spin = client.post("/api/bonuses/wheel/spin", headers=headers)
    assert wheel_spin.status_code == 200, wheel_spin.text
    spin_payload = wheel_spin.json()
    assert spin_payload["ok"] is True
    assert spin_payload["reward_kind"] in {"days", "discount"}
    if spin_payload["reward_kind"] == "days":
        assert spin_payload["reward_days"] in (1, 3, 7, 30)
        assert spin_payload["reward_value"] == spin_payload["reward_days"]
        assert spin_payload["discount_pct"] == 0
        assert spin_payload["grant_id"]
        assert spin_payload["sync_state"] == "sync_pending"
    else:
        assert spin_payload["reward_days"] == 0
        assert spin_payload["reward_value"] in (5, 7, 10)
        assert spin_payload["discount_pct"] == spin_payload["reward_value"]
        assert spin_payload["grant_id"] is None
        assert spin_payload["sync_state"] == "not_required"
    assert spin_payload["summary"]["wheel"]["can_spin"] is False
    assert spin_payload["summary"]["achievements"]["items"]

    second_spin = client.post("/api/bonuses/wheel/spin", headers=headers)
    assert second_spin.status_code == 409, second_spin.text
    assert second_spin.json()["detail"]["code"] == "wheel_cooldown_active"

    calendar_state = client.get("/api/bonuses/calendar", headers=headers)
    assert calendar_state.status_code == 200, calendar_state.text
    assert calendar_state.json()["enabled"] is True
    assert calendar_state.json()["can_checkin"] is True

    first_checkin = client.post("/api/bonuses/calendar/checkin", headers=headers)
    assert first_checkin.status_code == 200, first_checkin.text
    assert first_checkin.json()["reward_days"] == 0
    assert first_checkin.json()["grant_id"] is None

    same_day = client.post("/api/bonuses/calendar/checkin", headers=headers)
    assert same_day.status_code == 200, same_day.text
    assert same_day.json()["already_checked_in"] is True
    assert same_day.json()["grant_id"] is None

    milestone = None
    for offset in range(1, 7):
        current_now[0] = base_now + timedelta(days=offset)
        milestone = client.post("/api/bonuses/calendar/checkin", headers=headers)
        assert milestone.status_code == 200, milestone.text
    milestone_payload = milestone.json()
    assert milestone_payload["calendar_cycle_day"] == 7
    assert milestone_payload["reward_days"] == 1
    assert milestone_payload["grant_id"]
    assert milestone_payload["sync_state"] == "sync_pending"

    day_seven_retry = client.post("/api/bonuses/calendar/checkin", headers=headers)
    assert day_seven_retry.status_code == 200, day_seven_retry.text
    assert day_seven_retry.json()["already_checked_in"] is True
    assert day_seven_retry.json()["grant_id"] == milestone_payload["grant_id"]

    history = client.get("/api/bonuses/history", headers=headers)
    assert history.status_code == 200, history.text
    kinds = [item["kind"] for item in history.json()["items"]]
    assert "wheel_spin" in kinds
    assert "calendar_checkin" in kinds
    assert "raw_config" not in str(history.json())

    db = api.SessionLocal()
    try:
        user = db.query(api.User).filter_by(tg_id=tg_id).one()
        assert user is not None
        assert user.account_id == account_id
        assert user.last_wheel_spin is None
        assert int(user.streak_months or 0) == 0
        assert user.streak_last_check is None
        legacy_discount_claims = (
            db.query(api.RewardClaim).filter_by(tg_id=user.tg_id).count()
        )
        assert legacy_discount_claims == (
            1 if spin_payload["reward_kind"] == "discount" else 0
        )
        reward_grants = (
            db.query(api.EntitlementGrant)
            .filter(
                api.EntitlementGrant.account_id == account_id,
                api.EntitlementGrant.source.in_(("bonus_wheel", "bonus_calendar")),
            )
            .all()
        )
        expected_grants = 2 if spin_payload["reward_kind"] == "days" else 1
        assert len(reward_grants) == expected_grants
        assert (
            db.query(api.NodeProvisioningJob)
            .filter_by(job_type="reward_entitlement_sync")
            .count()
            == expected_grants
        )
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

from __future__ import annotations

import base64
import hashlib
import hmac
import importlib
import json
import os
import sys
import time
import uuid
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


class _FakePanel:
    async def login(self):
        return True

    async def close(self):
        return None

    async def add_client(self, **_kwargs):
        return True

    async def get_node_online_summaries(self, *, node_codes=None):
        return {
            str(code): {"online_keys_now": 0, "online_connections_now": 0}
            for code in (node_codes or [])
        }


def _sign_telegram_init_data(*, bot_token: str, params: dict[str, str]) -> str:
    items = sorted((k, v) for k, v in params.items())
    data_check_string = "\n".join([f"{k}={v}" for k, v in items])
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    check_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    payload = dict(params)
    payload["hash"] = check_hash
    return urlencode(payload)


def _load_api(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "portal-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "portal-test-secret")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.pokrov.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "pokrov.test")
    monkeypatch.setenv("PUBLIC_CHANNEL", "pokrov_vpn")
    monkeypatch.setenv("BOT_USERNAME", "pokrov_vpnbot")
    monkeypatch.setenv("SUPPORT_BOT_USERNAME", "pokrov_supportbot")
    monkeypatch.setenv("BOT_TOKEN", "test_bot_token_123")
    monkeypatch.setenv("ADMIN_ID", "9999")
    monkeypatch.setenv("ADMIN_IDS", "9999")

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
        "warp_service",
    ]:
        sys.modules.pop(name, None)

    api = importlib.import_module("api")
    monkeypatch.setattr(api, "ControlPanel", _FakePanel)
    original_enabled_nodes = api.enabled_nodes

    def _authenticated_test_nodes(session):
        observed_at = api._utcnow()
        synthetic_profiles = api._synthetic_transport_node().transport_profiles_json
        return [
            replace(
                node,
                is_healthy=True,
                edge_reachability_ok=True,
                authenticated_egress_ok=True,
                last_authenticated_egress_at=observed_at,
                dataplane_ok=True,
                last_probe_at=observed_at,
                transport_profiles_json=synthetic_profiles,
            )
            for node in original_enabled_nodes(session)
        ]

    monkeypatch.setattr(api, "enabled_nodes", _authenticated_test_nodes)
    return api


def _admin_headers() -> dict[str, str]:
    init_data = _sign_telegram_init_data(
        bot_token=os.environ["BOT_TOKEN"],
        params={
            "auth_date": str(int(time.time())),
            "query_id": "AAEAAAE",
            "user": '{"id":9999,"first_name":"Admin","username":"admin"}',
        },
    )
    return {"X-Telegram-Init-Data": init_data}


def _guarded_admin_headers(
    client: TestClient,
    *,
    action: str,
    target_type: str,
    target_id: str,
    payload: dict[str, object],
) -> dict[str, str]:
    prepared = client.post(
        "/api/admin/action-intents",
        headers=_admin_headers(),
        json={
            "action": action,
            "target": {"type": target_type, "id": target_id},
            "payload": payload,
        },
    )
    assert prepared.status_code == 200, prepared.text
    prepared_body = prepared.json()
    challenge = str(prepared_body["confirmation_challenge"])
    return {
        **_admin_headers(),
        "X-Admin-Intent-Id": str(prepared_body["intent_id"]),
        "X-Admin-Idempotency-Key": str(uuid.uuid4()),
        "X-Admin-Confirmation-SHA256": hashlib.sha256(challenge.encode("utf-8")).hexdigest(),
    }


def _rollout_payload() -> dict[str, object]:
    return {
        "version": "2026-04-13",
        "defaults": {
            "routing_mode_default": "all_except_ru",
            "transport_profile": "legacy_reality_fallback",
            "dns_policy": "ru_direct_split",
            "ip_version_preference": "ipv4_only",
        },
        "carrier_overrides": {
            "carrier-x": {
                "transport_profile": "grpc_443_primary",
                "dns_policy": "ru_direct_split",
                "routing_mode_default": "all_except_ru",
                "ip_version_preference": "ipv6_preferred",
            }
        },
        "cohort_overrides": {
            "ru-risk-canary": {
                "install_ids": ["install-canary"],
                "transport_profile": "grpc_443_primary",
            }
        },
        "operator_lab": {
            "enabled": False,
            "allowlist_install_ids": [],
            "allowlist_tg_ids": [],
            "allowlist_node_codes": [],
            "expires_at": None,
        },
        "reserve_xhttp_cdn": {
            "enabled": False,
            "allowlist_node_codes": [],
            "xhttp_path": "/reserve-xhttp",
            "tls_server_name": "cdn.connect.pokrov.space",
        },
        "package_catalog_feed": {"version": "2026-04-13"},
        "routing_rules_feed": {"version": "2026-04-13"},
        "support_recovery_order": ["app", "web", "telegram"],
    }


def test_start_trial_resolves_default_and_cohort_rollout_from_app_setting(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    rollout_payload = _rollout_payload()

    db = api.SessionLocal()
    try:
        api._set_app_setting_json(s=db, key="network_rollout_config", value=rollout_payload)
        db.commit()
    finally:
        db.close()

    default_trial = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-default",
            "device_name": "Pixel 10",
            "platform": "android",
            "trial_days": 5,
        },
    )
    assert default_trial.status_code == 200, default_trial.text
    assert default_trial.json()["client_policy"]["transport_profile"] == "legacy_reality_fallback"
    assert default_trial.json()["client_policy"]["support_context"]["ip_version_preference"] == "ipv4_only"

    cohort_trial = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-canary",
            "device_name": "Pixel Canary",
            "platform": "android",
            "trial_days": 5,
        },
    )
    assert cohort_trial.status_code == 200, cohort_trial.text
    assert cohort_trial.json()["client_policy"]["transport_profile"] == "grpc_443_primary"

    carrier_trial = client.post(
        "/api/client/session/start-trial",
        headers={"X-Portal-Carrier": "carrier-x"},
        json={
            "install_id": "install-carrier",
            "device_name": "Carrier Device",
            "platform": "android",
            "trial_days": 5,
        },
    )
    assert carrier_trial.status_code == 200, carrier_trial.text
    assert carrier_trial.json()["client_policy"]["transport_profile"] == "grpc_443_primary"
    assert carrier_trial.json()["client_policy"]["transport_kind"] == "grpc"
    assert carrier_trial.json()["client_policy"]["engine_hint"] == "singbox"
    assert carrier_trial.json()["client_policy"]["profile_revision"] == "2026-04-13:grpc_443_primary"
    assert carrier_trial.json()["client_policy"]["support_context"]["ip_version_preference"] == "ipv6_preferred"


def test_carrier_rollout_flows_through_dashboard_user_managed_manifest_and_subscription(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    db = api.SessionLocal()
    try:
        api._set_app_setting_json(s=db, key="network_rollout_config", value=_rollout_payload())
        db.commit()
    finally:
        db.close()

    start_trial = client.post(
        "/api/client/session/start-trial",
        headers={"X-Portal-Carrier": "carrier-x"},
        json={
            "install_id": "install-carrier-managed",
            "device_name": "Carrier Device",
            "platform": "android",
            "trial_days": 5,
        },
    )
    assert start_trial.status_code == 200, start_trial.text
    start_body = start_trial.json()
    assert start_body["client_policy"]["transport_profile"] == "grpc_443_primary"
    assert start_body["client_policy"]["transport_kind"] == "grpc"
    assert start_body["client_policy"]["engine_hint"] == "singbox"
    assert start_body["client_policy"]["profile_revision"] == "2026-04-13:grpc_443_primary"

    auth_headers = {
        "Authorization": f"Bearer {start_body['session_token']}",
        "X-Portal-Carrier": "carrier-x",
    }

    dashboard = client.get("/api/dashboard", headers=auth_headers)
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["client_policy"]["transport_profile"] == "grpc_443_primary"
    assert dashboard.json()["client_policy"]["transport_kind"] == "grpc"
    assert dashboard.json()["client_policy"]["engine_hint"] == "singbox"
    assert dashboard.json()["client_policy"]["profile_revision"] == "2026-04-13:grpc_443_primary"
    assert dashboard.json()["client_policy"]["support_context"]["ip_version_preference"] == "ipv6_preferred"

    user_response = client.get(f"/api/user/{start_body['account_id']}", headers=auth_headers)
    assert user_response.status_code == 200, user_response.text
    assert user_response.json()["client_policy"]["transport_profile"] == "grpc_443_primary"
    assert user_response.json()["client_policy"]["transport_kind"] == "grpc"
    assert user_response.json()["client_policy"]["engine_hint"] == "singbox"
    assert user_response.json()["client_policy"]["profile_revision"] == "2026-04-13:grpc_443_primary"

    managed_manifest = client.get("/api/client/profile/managed", headers=auth_headers)
    assert managed_manifest.status_code == 200, managed_manifest.text
    manifest_body = managed_manifest.json()
    assert manifest_body["version"] == "2026-04-13"
    assert manifest_body["profile_revision"] == "2026-04-13:grpc_443_primary"
    assert manifest_body["transport_profile"] == "grpc_443_primary"
    assert manifest_body["transport_kind"] == "grpc"
    assert manifest_body["engine_hint"] == "singbox"
    assert manifest_body["config_format"] == "singbox-json"
    assert manifest_body["fallback_order"] == ["grpc_443_primary", "legacy_reality_fallback"]
    assert manifest_body["support_context"]["transport"] == "grpc_443_primary"
    assert manifest_body["support_context"]["ip_version_preference"] == "ipv6_preferred"
    assert any(
        ((item.get("transport") or {}).get("type") == "grpc")
        for item in manifest_body["config_payload"]["outbounds"]
        if isinstance(item, dict)
    )

    connect_client = TestClient(api.app, base_url="https://connect.pokrov.space")
    subscription_path = start_body["subscription_url"].replace("https://connect.pokrov.space", "", 1)
    smart_subscription = connect_client.get(
        subscription_path,
        headers={"X-Portal-Carrier": "carrier-x", "User-Agent": "sing-box/1.0"},
    )
    assert smart_subscription.status_code == 200, smart_subscription.text
    smart_body = smart_subscription.json()
    assert any(
        ((item.get("transport") or {}).get("type") == "grpc")
        for item in smart_body["outbounds"]
        if isinstance(item, dict)
    )

    plain_subscription = connect_client.get(
        f"{subscription_path}?format=plain",
        headers={"X-Portal-Carrier": "carrier-x", "User-Agent": "curl/8.0"},
    )
    assert plain_subscription.status_code == 200, plain_subscription.text
    plain_links = base64.b64decode(plain_subscription.text).decode("utf-8")
    assert "security=reality" in plain_links
    assert "serviceName=" not in plain_links


def test_managed_profile_exposes_warp_policy_without_leaking_public_policy_secrets(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    rollout_payload = _rollout_payload()
    rollout_payload["warp_policy"] = {
        "enabled": True,
        "mode": "proxy_over_warp",
        "source": "backend_managed",
        "wireguard_config": {
            "private-key": "test-private-key",
            "local-address-ipv4": "172.16.0.2",
            "local-address-ipv6": "2606:4700:110:abcd::2",
            "peer-public-key": "test-peer-public-key",
            "client-id": "test-client-id",
        },
        "account": {
            "account-id": "test-account-id",
            "access-token": "test-access-token",
        },
    }

    db = api.SessionLocal()
    try:
        api._set_app_setting_json(s=db, key="network_rollout_config", value=rollout_payload)
        db.commit()
    finally:
        db.close()

    start_trial = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-warp-policy",
            "device_name": "Windows WARP Policy Device",
            "platform": "windows",
            "trial_days": 5,
        },
    )
    assert start_trial.status_code == 200, start_trial.text
    start_body = start_trial.json()
    public_policy = start_body["client_policy"]["warp_policy"]
    assert public_policy == {
        "enabled": True,
        "runtime_ready": True,
        "state": "ready",
        "mode": "proxy_over_warp",
        "source": "backend_managed",
        "wireguard_config_available": True,
    }
    public_policy_json = json.dumps(start_body["client_policy"], sort_keys=True)
    assert "test-private-key" not in public_policy_json
    assert "test-access-token" not in public_policy_json
    assert "wireguard_config" not in public_policy
    assert "account" not in public_policy

    auth_headers = {"Authorization": f"Bearer {start_body['session_token']}"}
    dashboard = client.get("/api/dashboard", headers=auth_headers)
    assert dashboard.status_code == 200, dashboard.text
    dashboard_policy_json = json.dumps(dashboard.json()["client_policy"], sort_keys=True)
    assert "test-private-key" not in dashboard_policy_json
    assert "test-access-token" not in dashboard_policy_json

    user_response = client.get(f"/api/user/{start_body['account_id']}", headers=auth_headers)
    assert user_response.status_code == 200, user_response.text
    user_policy_json = json.dumps(user_response.json()["client_policy"], sort_keys=True)
    assert "test-private-key" not in user_policy_json
    assert "test-access-token" not in user_policy_json

    managed_manifest = client.get("/api/client/profile/managed", headers=auth_headers)
    assert managed_manifest.status_code == 200, managed_manifest.text
    warp_policy = managed_manifest.json()["warp_policy"]
    assert warp_policy["enabled"] is True
    assert warp_policy["runtime_ready"] is True
    assert warp_policy["state"] == "ready"
    assert warp_policy["mode"] == "proxy_over_warp"
    assert warp_policy["wireguard_config"]["private-key"] == "test-private-key"
    assert warp_policy["account"]["account-id"] == "test-account-id"


def test_admin_warp_material_store_encrypts_at_rest_and_scopes_managed_profile(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    start_trial = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-warp-material",
            "device_name": "Windows WARP Material Device",
            "platform": "windows",
            "trial_days": 5,
        },
    )
    assert start_trial.status_code == 200, start_trial.text
    start_body = start_trial.json()
    auth_headers = {"Authorization": f"Bearer {start_body['session_token']}"}

    initial_status = client.get("/api/client/warp/status", headers=auth_headers)
    assert initial_status.status_code == 200, initial_status.text
    assert initial_status.json()["runtime_ready"] is True
    assert initial_status.json()["source"] == "client_local"
    assert initial_status.json()["wireguard_config_available"] is False

    material_payload = {
        "tg_id": int(start_body["account_id"]),
        "install_id": "install-warp-material",
        "source": "operator_test",
        "mode": "proxy_over_warp",
        "wireguard_config": {
            "private-key": "material-private-key",
            "local-address-ipv4": "172.16.9.2",
            "local-address-ipv6": "2606:4700:110:feed::2",
            "peer-public-key": "material-peer-public-key",
            "client-id": "material-client-id",
        },
        "account": {
            "account-id": "material-account-id",
            "access-token": "material-access-token",
        },
    }
    provision = client.put(
        "/api/admin/client/warp/material",
        headers=_guarded_admin_headers(
            client,
            action="warp_material.replace",
            target_type="warp_material",
            target_id=str(start_body["account_id"]),
            payload=material_payload,
        ),
        json=material_payload,
    )
    assert provision.status_code == 200, provision.text
    provision_body = provision.json()
    assert provision_body["ok"] is True
    assert provision_body["material"]["state"] == "ready"
    assert provision_body["material"]["runtime_ready"] is True
    assert provision_body["warp_status"]["runtime_ready"] is True
    assert provision_body["warp_status"]["state"] == "ready_to_consent"
    provision_json = json.dumps(provision_body, ensure_ascii=False, sort_keys=True)
    assert "material-private-key" not in provision_json
    assert "material-access-token" not in provision_json

    db = api.SessionLocal()
    try:
        row = (
            db.query(api.WarpMaterial)
            .filter(api.WarpMaterial.tg_id == int(start_body["account_id"]))
            .filter(api.WarpMaterial.install_id == "install-warp-material")
            .one()
        )
        assert row.is_active is True
        assert row.state == "ready"
        assert row.wireguard_ciphertext
        assert row.account_ciphertext
        stored_json = json.dumps(
            {
                "wireguard_ciphertext": row.wireguard_ciphertext,
                "account_ciphertext": row.account_ciphertext,
                "material_hash": row.material_hash,
            },
            sort_keys=True,
        )
        assert "material-private-key" not in stored_json
        assert "material-access-token" not in stored_json
    finally:
        db.close()

    status = client.get("/api/client/warp/status", headers=auth_headers)
    assert status.status_code == 200, status.text
    assert status.json()["runtime_ready"] is True
    assert status.json()["wireguard_config_available"] is True
    assert "material-private-key" not in json.dumps(status.json(), ensure_ascii=False, sort_keys=True)

    managed_manifest = client.get("/api/client/profile/managed", headers=auth_headers)
    assert managed_manifest.status_code == 200, managed_manifest.text
    warp_policy = managed_manifest.json()["warp_policy"]
    assert warp_policy["runtime_ready"] is True
    assert warp_policy["wireguard_config"]["private-key"] == "material-private-key"
    assert warp_policy["account"]["access-token"] == "material-access-token"

    dashboard = client.get("/api/dashboard", headers=auth_headers)
    assert dashboard.status_code == 200, dashboard.text
    dashboard_json = json.dumps(dashboard.json(), ensure_ascii=False, sort_keys=True)
    assert "material-private-key" not in dashboard_json
    assert "material-access-token" not in dashboard_json

    revoke = client.post("/api/client/warp/revoke", headers=auth_headers, json={"reason_code": "user_disabled"})
    assert revoke.status_code == 200, revoke.text
    assert revoke.json()["state"] == "revoked"
    assert revoke.json()["consented"] is False

    after_revoke = client.get("/api/client/profile/managed", headers=auth_headers)
    assert after_revoke.status_code == 200, after_revoke.text
    after_revoke_policy = after_revoke.json()["warp_policy"]
    assert after_revoke_policy["runtime_ready"] is False
    assert "wireguard_config" not in after_revoke_policy
    assert "account" not in after_revoke_policy

    db = api.SessionLocal()
    try:
        revoked_row = db.query(api.WarpMaterial).filter(api.WarpMaterial.id == int(provision_body["material"]["id"])).one()
        assert revoked_row.is_active is False
        assert revoked_row.state == "revoked"
        assert revoked_row.revoked_at is not None
    finally:
        db.close()


def test_warp_material_hardening_limits_stale_material_and_reports_summary(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("WARP_MATERIAL_PROVISION_LIMIT_PER_HOUR", "1")
    monkeypatch.setenv("WARP_ROTATION_LIMIT_PER_HOUR", "1")
    monkeypatch.setenv("WARP_MATERIAL_MAX_AGE_HOURS", "1")
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    start_trial = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-warp-hardening",
            "device_name": "Windows WARP Hardening Device",
            "platform": "windows",
        },
    )
    assert start_trial.status_code == 200, start_trial.text
    start_body = start_trial.json()
    auth_headers = {"Authorization": f"Bearer {start_body['session_token']}"}
    admin_headers = _admin_headers()

    material_payload = {
        "tg_id": int(start_body["account_id"]),
        "install_id": "install-warp-hardening",
        "source": "operator_test",
        "mode": "proxy_over_warp",
        "wireguard_config": {
            "private-key": "hardening-private-key",
            "local-address-ipv4": "172.16.10.2",
            "peer-public-key": "hardening-peer-public-key",
            "client-id": "hardening-client-id",
        },
        "account": {
            "account-id": "hardening-account-id",
            "access-token": "hardening-access-token",
        },
    }

    provision = client.put(
        "/api/admin/client/warp/material",
        headers=_guarded_admin_headers(
            client,
            action="warp_material.replace",
            target_type="warp_material",
            target_id=str(start_body["account_id"]),
            payload=material_payload,
        ),
        json=material_payload,
    )
    assert provision.status_code == 200, provision.text

    second_material_payload = {
        **material_payload,
        "wireguard_config": {
            **material_payload["wireguard_config"],
            "private-key": "second-private-key",
        },
    }
    rate_limited_provision = client.put(
        "/api/admin/client/warp/material",
        headers=_guarded_admin_headers(
            client,
            action="warp_material.replace",
            target_type="warp_material",
            target_id=str(start_body["account_id"]),
            payload=second_material_payload,
        ),
        json=second_material_payload,
    )
    assert rate_limited_provision.status_code == 429, rate_limited_provision.text
    assert rate_limited_provision.json()["detail"]["code"] == "warp_material_rate_limited"

    consent = client.post("/api/client/warp/consent", headers=auth_headers, json={"consent": True})
    assert consent.status_code == 200, consent.text
    assert consent.json()["consented"] is True

    rotate = client.post("/api/client/warp/rotate", headers=auth_headers, json={"reason_code": "user_requested"})
    assert rotate.status_code == 200, rotate.text
    assert rotate.json()["state"] == "rotation_requested"

    rate_limited_rotate = client.post(
        "/api/client/warp/rotate",
        headers=auth_headers,
        json={"reason_code": "user_requested_again"},
    )
    assert rate_limited_rotate.status_code == 429, rate_limited_rotate.text
    assert rate_limited_rotate.json()["detail"]["code"] == "warp_rotation_rate_limited"

    runtime_error = client.post(
        "/api/client/warp/events",
        headers=auth_headers,
        json={
            "event_name": "runtime_error",
            "state": "error",
            "reason_code": "handshake_failed",
            "message": "baseline fallback used",
            "meta": {
                "safe_detail": "handshake failed",
                "account": {"access-token": "hardening-access-token"},
            },
        },
    )
    assert runtime_error.status_code == 200, runtime_error.text

    db = api.SessionLocal()
    try:
        material = (
            db.query(api.WarpMaterial)
            .filter(api.WarpMaterial.tg_id == int(start_body["account_id"]))
            .filter(api.WarpMaterial.install_id == "install-warp-hardening")
            .one()
        )
        material.provisioned_at = api._utcnow() - timedelta(hours=2, minutes=5)
        material.updated_at = api._utcnow() - timedelta(hours=2)
        db.commit()
    finally:
        db.close()

    managed_manifest = client.get("/api/client/profile/managed", headers=auth_headers)
    assert managed_manifest.status_code == 200, managed_manifest.text
    stale_policy = managed_manifest.json()["warp_policy"]
    assert stale_policy["state"] == "material_stale"
    assert stale_policy["runtime_ready"] is False
    assert "wireguard_config" not in stale_policy
    assert "account" not in stale_policy

    status = client.get("/api/client/warp/status", headers=auth_headers)
    assert status.status_code == 200, status.text
    assert status.json()["state"] == "error"
    assert status.json()["runtime_ready"] is True
    assert status.json()["source"] == "client_local"
    assert status.json()["wireguard_config_available"] is False
    assert status.json()["policy_state"] == "material_stale"

    summary = client.get("/api/admin/client/warp/summary", headers=admin_headers)
    assert summary.status_code == 200, summary.text
    summary_body = summary.json()
    assert summary_body["materials"]["total"] == 1
    assert summary_body["materials"]["active"] == 1
    assert summary_body["materials"]["stale_active"] == 1
    assert summary_body["materials"]["rotation_requested"] == 1
    assert summary_body["events"]["active_consents"] == 1
    assert summary_body["events"]["recent_material_provisions"] == 1
    assert summary_body["events"]["recent_runtime_errors"] == 1
    assert summary_body["events"]["recent_rate_limits"] >= 2
    assert summary_body["runtime"]["last_state"] == "error"
    assert summary_body["runtime"]["last_reason_code"] == "handshake_failed"
    assert summary_body["runtime"]["state_counts"]["error"] == 1
    assert summary_body["runtime"]["recent_events"][0]["event_name"] == "runtime_error"
    assert summary_body["runtime"]["recent_events"][0]["state"] == "error"
    assert "message" not in summary_body["runtime"]["recent_events"][0]
    assert "meta" not in summary_body["runtime"]["recent_events"][0]
    summary_json = json.dumps(summary_body, ensure_ascii=False, sort_keys=True)
    assert "hardening-private-key" not in summary_json
    assert "hardening-access-token" not in summary_json


def test_client_warp_lifecycle_api_records_consent_and_redacts_runtime_events(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    telemetry_secrets = [
        "vless://synthetic-vless-secret@node.example:443?security=reality",
        "trojan://synthetic-trojan-secret@node.example:443",
        "ss://synthetic-ss-secret@node.example:443",
        "wg://synthetic-wg-secret@node.example:443",
        "connect.pokrov.space/s8Kx2mP7qR4wT/synthetic-connect-secret",
        "Bearer synthetic-bearer-secret",
        "access-token=synthetic-access-secret",
        "private-key=synthetic-private-secret",
        "token=synthetic-token-secret",
        "11111111-2222-3333-4444-555555555555",
    ]
    rollout_payload = _rollout_payload()
    rollout_payload["warp_policy"] = {
        "enabled": True,
        "mode": "proxy_over_warp",
        "source": "backend_managed",
        "wireguard_config": {
            "private-key": "test-private-key",
            "local-address-ipv4": "172.16.0.2",
            "peer-public-key": "test-peer-public-key",
            "client-id": "test-client-id",
        },
        "account": {
            "account-id": "test-account-id",
            "access-token": "test-access-token",
        },
    }

    db = api.SessionLocal()
    try:
        api._set_app_setting_json(s=db, key="network_rollout_config", value=rollout_payload)
        db.commit()
    finally:
        db.close()

    start_trial = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-warp-lifecycle",
            "device_name": "Windows WARP Lifecycle Device",
            "platform": "windows",
        },
    )
    assert start_trial.status_code == 200, start_trial.text
    auth_headers = {"Authorization": f"Bearer {start_trial.json()['session_token']}"}

    status = client.get("/api/client/warp/status", headers=auth_headers)
    assert status.status_code == 200, status.text
    body = status.json()
    assert body["feature"] == "extended_protection"
    assert body["public_label"] == "Расширенная защита"
    assert body["technical_label"] == "WARP"
    assert body["state"] == "ready_to_consent"
    assert body["runtime_ready"] is True
    assert body["consented"] is False
    status_json = json.dumps(body, ensure_ascii=False, sort_keys=True)
    assert "test-private-key" not in status_json
    assert "test-access-token" not in status_json
    assert "wireguard_config" not in body
    assert "account" not in body

    consent = client.post("/api/client/warp/consent", headers=auth_headers, json={"consent": True})
    assert consent.status_code == 200, consent.text
    assert consent.json()["state"] == "consented"
    assert consent.json()["consented"] is True
    assert consent.json()["consented_at"]

    event = client.post(
        "/api/client/warp/events",
        headers=auth_headers,
        json={
            "event_name": "runtime_fallback",
            "state": "fallback",
            "reason_code": "handshake_failed",
            "message": telemetry_secrets[0],
            "meta": {
                "wireguard_config": {"private-key": "test-private-key"},
                "account": {"access-token": "test-access-token"},
                "subscription_url": "https://connect.pokrov.space/s8Kx2mP7qR4wT/secret",
                "safe_detail": ["fallback", *telemetry_secrets],
                "runtime_phase": "running",
                "nested": {
                    "safe_detail": "ss://another-secret@203.0.113.5:443",
                    "node_host": "node.internal.example",
                },
            },
        },
    )
    assert event.status_code == 200, event.text
    assert event.json()["ok"] is True
    assert event.json()["state"] == "fallback"

    after_event = client.get("/api/client/warp/status", headers=auth_headers)
    assert after_event.status_code == 200, after_event.text
    after_body = after_event.json()
    assert after_body["state"] == "fallback"
    assert after_body["last_event"]["event_name"] == "runtime_fallback"
    after_json = json.dumps(after_body, ensure_ascii=False, sort_keys=True)
    assert "test-private-key" not in after_json
    assert "test-access-token" not in after_json
    assert "connect.pokrov.space/s8Kx2mP7qR4wT/secret" not in after_json
    for sentinel in telemetry_secrets:
        assert sentinel not in after_json
        assert sentinel not in event.text

    rotate = client.post("/api/client/warp/rotate", headers=auth_headers, json={"reason_code": "user_requested"})
    assert rotate.status_code == 200, rotate.text
    assert rotate.json()["state"] == "rotation_requested"
    assert rotate.json()["consented"] is True

    revoke = client.post("/api/client/warp/revoke", headers=auth_headers, json={"reason_code": "user_disabled"})
    assert revoke.status_code == 200, revoke.text
    assert revoke.json()["state"] == "revoked"
    assert revoke.json()["consented"] is False
    assert revoke.json()["revoked_at"]

    db = api.SessionLocal()
    try:
        rows = db.query(api.WarpEvent).order_by(api.WarpEvent.id.asc()).all()
        assert [row.event_name for row in rows] == [
            "consent",
            "runtime_fallback",
            "rotate_requested",
            "revoke",
        ]
        ledger_json = "\n".join(str(row.meta_json or "") for row in rows)
        assert "test-private-key" not in ledger_json
        assert "test-access-token" not in ledger_json
        assert "connect.pokrov.space/s8Kx2mP7qR4wT/secret" not in ledger_json
        assert "ss://another-secret" not in ledger_json
        assert "node.internal.example" not in ledger_json
        assert "message" not in ledger_json
        assert "nested" not in ledger_json
        for sentinel in telemetry_secrets:
            assert sentinel not in ledger_json
        assert "fallback" in ledger_json
        assert "running" in ledger_json
    finally:
        db.close()


def test_client_warp_consent_accepts_client_local_policy_without_server_material(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    start_trial = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-warp-not-ready",
            "device_name": "Android WARP Not Ready Device",
            "platform": "android",
        },
    )
    assert start_trial.status_code == 200, start_trial.text
    auth_headers = {"Authorization": f"Bearer {start_trial.json()['session_token']}"}

    status = client.get("/api/client/warp/status", headers=auth_headers)
    assert status.status_code == 200, status.text
    assert status.json()["state"] == "ready_to_consent"
    assert status.json()["runtime_ready"] is True
    assert status.json()["wireguard_config_available"] is False
    assert status.json()["source"] == "client_local"
    assert status.json()["can_enable"] is True

    consent = client.post("/api/client/warp/consent", headers=auth_headers, json={"consent": True})
    assert consent.status_code == 200, consent.text
    assert consent.json()["state"] == "consented"
    assert consent.json()["consented"] is True

    db = api.SessionLocal()
    try:
        rows = db.query(api.WarpEvent).order_by(api.WarpEvent.id.asc()).all()
        assert [row.event_name for row in rows] == ["consent"]
        assert rows[0].runtime_ready is True
        assert rows[0].consented is True
    finally:
        db.close()


def test_admin_network_rollout_config_roundtrip_if_route_is_exposed(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    admin_hdrs = _admin_headers()
    route_paths = {getattr(route, "path", "") for route in api.app.routes}

    if "/api/admin/network-rollout-config" not in route_paths:
        pytest.skip("backend admin rollout route is not exposed in the current workspace")

    rollout_payload = _rollout_payload()
    get_before = client.get("/api/admin/network-rollout-config", headers=admin_hdrs)
    assert get_before.status_code == 200, get_before.text

    put_response = client.put(
        "/api/admin/network-rollout-config",
        headers=_guarded_admin_headers(
            client,
            action="network_rollout_config.update",
            target_type="config",
            target_id="network-rollout",
            payload=rollout_payload,
        ),
        json=rollout_payload,
    )
    assert put_response.status_code == 200, put_response.text
    assert put_response.json()["network_rollout_config"]["carrier_overrides"]["carrier-x"]["transport_profile"] == "grpc_443_primary"

    get_after = client.get("/api/admin/network-rollout-config", headers=admin_hdrs)
    assert get_after.status_code == 200, get_after.text
    assert get_after.json()["network_rollout_config"]["cohort_overrides"]["ru-risk-canary"]["install_ids"] == ["install-canary"]


def test_reserve_xhttp_rollout_stays_opt_in_and_emits_xray_manifest_only_when_enabled(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    rollout_payload = _rollout_payload()
    rollout_payload["reserve_xhttp_cdn"] = {
        "enabled": True,
        "allowlist_node_codes": ["default"],
        "xhttp_path": "/reserve-xhttp",
        "tls_server_name": "cdn.connect.pokrov.space",
    }
    rollout_payload["cohort_overrides"]["reserve-canary"] = {
        "install_ids": ["install-reserve"],
        "transport_profile": "reserve_xhttp_cdn",
    }

    db = api.SessionLocal()
    try:
        api._set_app_setting_json(s=db, key="network_rollout_config", value=rollout_payload)
        db.commit()
    finally:
        db.close()

    reserve_trial = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "install-reserve",
            "device_name": "Reserve Device",
            "platform": "android",
            "trial_days": 5,
        },
    )
    assert reserve_trial.status_code == 200, reserve_trial.text
    reserve_body = reserve_trial.json()
    assert reserve_body["client_policy"]["transport_profile"] == "reserve_xhttp_cdn"
    assert reserve_body["client_policy"]["transport_kind"] == "xhttp"
    assert reserve_body["client_policy"]["engine_hint"] == "xray"
    assert reserve_body["client_policy"]["profile_revision"] == "2026-04-13:reserve_xhttp_cdn"

    managed_manifest = client.get(
        "/api/client/profile/managed",
        headers={"Authorization": f"Bearer {reserve_body['session_token']}"},
    )
    assert managed_manifest.status_code == 200, managed_manifest.text
    manifest_body = managed_manifest.json()
    assert manifest_body["transport_profile"] == "reserve_xhttp_cdn"
    assert manifest_body["transport_kind"] == "xhttp"
    assert manifest_body["engine_hint"] == "xray"
    assert manifest_body["config_format"] == "xray-json"
    assert manifest_body["fallback_order"] == ["reserve_xhttp_cdn", "legacy_reality_fallback"]


@pytest.mark.parametrize("lab_profile", ["awg2_lab", "awg31_lab", "hy2_lab"])
def test_managed_lab_tcp_fallback_is_revision_bound_and_uses_normal_provisioning(
    monkeypatch, tmp_path, lab_profile,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    trial = client.post("/api/client/session/start-trial", json={
        "install_id": "install-lab-fallback", "device_name": "Lab fixture",
        "platform": "android", "trial_days": 5,
    })
    assert trial.status_code == 200
    baseline_policy = trial.json()["client_policy"]
    lab_revision = f"test-rollout:{lab_profile}:generation-1"
    lab_policy = {
        **baseline_policy,
        "transport_profile": lab_profile,
        "transport_kind": lab_profile,
        "profile_revision": lab_revision,
        "support_context": {
            **baseline_policy["support_context"], "transport": lab_profile,
        },
    }
    monkeypatch.setattr(api.app_first_service, "build_client_policy", lambda **kwargs: dict(lab_policy))
    panel_requests = []
    async def panel_state(**kwargs):
        panel_requests.append(kwargs["panel_required"])
        return True, {"traffic_total_bytes": 0}
    monkeypatch.setattr(api, "_managed_profile_panel_state", panel_state)
    # Isolate fallback admission from lab-key encryption, covered by lab suites.
    rendered_profiles = []
    original_render = api._managed_manifest_payload
    def render(**kwargs):
        rendered_profiles.append(kwargs["transport_profile"])
        if kwargs["transport_profile"] == lab_profile:
            return "singbox-json", {"outbounds": []}
        return original_render(**kwargs)
    monkeypatch.setattr(api, "_managed_manifest_payload", render)
    headers = {"Authorization": f"Bearer {trial.json()['session_token']}"}
    response = client.get("/api/client/profile/managed", headers=headers,
        params={"fallback_from_revision": lab_revision})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["transport_profile"] == "legacy_reality_fallback"
    assert body["transport_kind"] == "reality"
    outbounds = body["config_payload"]["outbounds"]
    assert any(outbound.get("type") == "vless" for outbound in outbounds)
    assert not any(outbound.get("type") in {"awg", "hysteria2"} for outbound in outbounds)
    assert not body["config_payload"].get("endpoints")
    assert body["profile_revision"] == f"{lab_revision}:fallback:legacy_reality_fallback"
    assert body["support_context"]["transport"] == "legacy_reality_fallback"
    assert body["support_context"]["routing_mode"] == baseline_policy["support_context"]["routing_mode"]
    assert body["fallback_order"] == ["legacy_reality_fallback"]
    assert panel_requests == [True]
    assert rendered_profiles == ["legacy_reality_fallback"]

    stale = client.get("/api/client/profile/managed", headers=headers,
        params={"fallback_from_revision": "old-revision"})
    assert stale.status_code == 409
    assert len(rendered_profiles) == 1
    assert panel_requests == [True]
    # The opt-in request does not persist a cohort or rollout mutation.
    ordinary = client.get("/api/client/profile/managed", headers=headers)
    assert ordinary.status_code == 200
    assert ordinary.json()["transport_profile"] == lab_profile
    assert panel_requests == [True, False]

    async def pending_panel_state(**kwargs):
        assert kwargs["panel_required"] is True
        return False, {"traffic_total_bytes": 0}
    monkeypatch.setattr(api, "_managed_profile_panel_state", pending_panel_state)
    monkeypatch.setattr(api, "_provisioned_node_codes_for_user", lambda *args, **kwargs: set())
    pending = client.get("/api/client/profile/managed", headers=headers,
        params={"fallback_from_revision": lab_revision})
    assert pending.status_code == 200
    assert pending.json()["provisioning"]["status"] == "pending_sync"
    assert pending.json()["provisioning"]["sync_ok"] is False

    lab_policy["transport_profile"] = "legacy_reality_fallback"
    retired_lab = client.get("/api/client/profile/managed", headers=headers,
        params={"fallback_from_revision": lab_revision})
    assert retired_lab.status_code == 409

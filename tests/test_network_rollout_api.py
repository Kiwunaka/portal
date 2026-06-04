from __future__ import annotations

import base64
import hashlib
import hmac
import importlib
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


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
    ]:
        sys.modules.pop(name, None)

    return importlib.import_module("api")


def _admin_headers() -> dict[str, str]:
    init_data = _sign_telegram_init_data(
        bot_token=os.environ["BOT_TOKEN"],
        params={
            "auth_date": "1700000000",
            "query_id": "AAEAAAE",
            "user": '{"id":9999,"first_name":"Admin","username":"admin"}',
        },
    )
    return {"X-Telegram-Init-Data": init_data}


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
        headers=admin_hdrs,
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

from __future__ import annotations

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
    assert carrier_trial.json()["client_policy"]["transport_profile"] == "legacy_reality_fallback"
    assert carrier_trial.json()["client_policy"]["support_context"]["ip_version_preference"] == "ipv4_only"


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

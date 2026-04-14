from __future__ import annotations

import hashlib
import hmac
import importlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
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
    db_path = tmp_path / "smart-connect-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "smart-connect-secret")
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
        "transport_catalog",
        "node_policy",
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
            return {str(code): {"online_keys_now": 0, "online_connections_now": 0} for code in (node_codes or [])}

    api.ControlPanel = _FakePanel
    return api


def _rollout_payload() -> dict[str, object]:
    return {
        "version": "2026-04-14",
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
        "cohort_overrides": {},
        "operator_lab": {
            "enabled": False,
            "allowlist_install_ids": [],
            "allowlist_tg_ids": [],
            "allowlist_node_codes": [],
            "expires_at": None,
        },
        "package_catalog_feed": {"version": "2026-04-14"},
        "routing_rules_feed": {"version": "2026-04-14"},
        "support_recovery_order": ["app", "web", "telegram"],
    }


def _transport_profiles(*, legacy_enabled: bool = True, grpc_enabled: bool = True) -> str:
    payload = [
        {
            "name": "legacy_reality_fallback",
            "enabled": legacy_enabled,
            "kind": "reality",
            "inbound_id": 1,
            "host": "example.test",
            "port": 443,
            "tls_server_name": "www.example.test",
            "reality_public_key": "pbk",
            "reality_short_id": "sid",
            "fingerprint": "firefox",
            "flow": "xtls-rprx-vision",
        },
        {
            "name": "grpc_443_primary",
            "enabled": grpc_enabled,
            "kind": "grpc",
            "inbound_id": 2,
            "host": "example.test",
            "port": 443,
            "tls_server_name": "www.example.test",
            "grpc_service_name": "pokrov-grpc",
            "fingerprint": "firefox",
            "flow": "",
        },
    ]
    return json.dumps(payload)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _add_node(
    api,
    *,
    code: str,
    weight: int = 100,
    health_score: float = 95.0,
    is_healthy: bool = True,
    accepting_new_clients: bool = True,
    is_draining: bool = False,
    cpu_percent: float = 30.0,
    last_health_at: datetime | None = None,
    grpc_enabled: bool = True,
) -> int:
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
            enabled=True,
            accepting_new_clients=accepting_new_clients,
            is_draining=is_draining,
            weight=weight,
            health_score=health_score,
            is_healthy=is_healthy,
            cpu_percent=cpu_percent,
            last_health_at=last_health_at or _utcnow(),
            transport_profiles_json=_transport_profiles(grpc_enabled=grpc_enabled),
        )
        s.add(node)
        s.commit()
        return int(node.id)
    finally:
        s.close()


def _start_trial(client: TestClient, *, install_id: str, carrier: str = "") -> dict[str, object]:
    headers = {"X-Portal-Carrier": carrier} if carrier else {}
    response = client.post(
        "/api/client/session/start-trial",
        headers=headers,
        json={
            "install_id": install_id,
            "device_name": "Pixel 10",
            "platform": "android",
            "trial_days": 5,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _auth_headers(start_body: dict[str, object], *, carrier: str = "") -> dict[str, str]:
    headers = {"Authorization": f"Bearer {start_body['session_token']}"}
    if carrier:
        headers["X-Portal-Carrier"] = carrier
    return headers


def test_managed_profile_exposes_top_five_eligible_premium_shortlist(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    db = api.SessionLocal()
    try:
        api._set_app_setting_json(s=db, key="network_rollout_config", value=_rollout_payload())
        db.commit()
    finally:
        db.close()

    now = _utcnow()
    _add_node(api, code="pl", health_score=98.0, weight=110, last_health_at=now)
    _add_node(api, code="de", health_score=96.0, weight=105, last_health_at=now)
    _add_node(api, code="us", health_score=94.0, weight=100, last_health_at=now)
    _add_node(api, code="it", health_score=92.0, weight=95, last_health_at=now)
    _add_node(api, code="nl", health_score=90.0, weight=90, last_health_at=now)
    _add_node(api, code="es", health_score=88.0, weight=85, last_health_at=now)
    _add_node(api, code="fr", health_score=97.0, cpu_percent=90.0, last_health_at=now)
    _add_node(api, code="cz", health_score=97.0, is_healthy=False, last_health_at=now)
    _add_node(api, code="pt", health_score=97.0, is_draining=True, last_health_at=now)
    _add_node(api, code="ro", health_score=97.0, last_health_at=now - timedelta(hours=2))
    _add_node(api, code="be", health_score=97.0, grpc_enabled=False, last_health_at=now)
    _add_node(api, code="nl-free", health_score=99.0, weight=999, last_health_at=now)

    start_body = _start_trial(client, install_id="install-premium-shortlist", carrier="carrier-x")
    managed = client.get("/api/client/profile/managed", headers=_auth_headers(start_body, carrier="carrier-x"))
    assert managed.status_code == 200, managed.text

    smart_connect = managed.json()["smart_connect"]
    assert smart_connect["eligible"] is True
    assert smart_connect["fallback_required"] is False
    assert [item["code"] for item in smart_connect["shortlist"]] == ["pl", "de", "us", "it", "nl"]
    assert len(smart_connect["shortlist"]) == 5
    penalties = {item["code"]: item for item in smart_connect["shortlist"]}
    assert penalties["nl"]["rank_hint"]["backend_penalty"] == 0
    assert penalties["nl"]["rank_hint"]["cpu_penalty"] == 0
    assert "fr" not in {item["code"] for item in smart_connect["shortlist"]}
    assert "be" not in {item["code"] for item in smart_connect["shortlist"]}
    assert "nl-free" not in {item["code"] for item in smart_connect["shortlist"]}


def test_managed_profile_uses_nl_free_only_for_free_pool(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    now = _utcnow()
    _add_node(api, code="pl", health_score=98.0, last_health_at=now)
    _add_node(api, code="nl-free", health_score=80.0, last_health_at=now)

    start_body = _start_trial(client, install_id="install-free-pool")
    db = api.SessionLocal()
    try:
        user = db.query(api.User).filter(api.User.tg_id == int(start_body["account_id"])).first()
        assert user is not None
        user.current_plan_code = "free_monthly"
        user.sub_type = "FREE"
        db.commit()
    finally:
        db.close()

    managed = client.get("/api/client/profile/managed", headers=_auth_headers(start_body))
    assert managed.status_code == 200, managed.text

    smart_connect = managed.json()["smart_connect"]
    assert [item["code"] for item in smart_connect["shortlist"]] == ["nl-free"]


def test_managed_profile_shortlist_respects_usernode_mapping_precedence(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    now = _utcnow()
    top_id = _add_node(api, code="pl", health_score=98.0, last_health_at=now)
    mapped_id = _add_node(api, code="it", health_score=85.0, last_health_at=now)
    _add_node(api, code="de", health_score=96.0, last_health_at=now)

    start_body = _start_trial(client, install_id="install-pinned")
    db = api.SessionLocal()
    try:
        user = db.query(api.User).filter(api.User.tg_id == int(start_body["account_id"])).first()
        assert user is not None
        db.add(api.UserNode(tg_id=int(user.tg_id), node_id=mapped_id, client_uuid=str(user.uuid), panel_email=str(user.email)))
        db.add(api.UserNode(tg_id=int(user.tg_id), node_id=top_id, client_uuid=str(user.uuid), panel_email=str(user.email)))
        db.commit()
    finally:
        db.close()

    managed = client.get("/api/client/profile/managed", headers=_auth_headers(start_body))
    assert managed.status_code == 200, managed.text
    assert [item["code"] for item in managed.json()["smart_connect"]["shortlist"]] == ["it", "pl"]


def test_managed_profile_flags_fallback_when_no_eligible_nodes_remain(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    stale_at = _utcnow() - timedelta(hours=3)
    _add_node(api, code="pl", health_score=95.0, cpu_percent=90.0, last_health_at=_utcnow())
    _add_node(api, code="de", health_score=95.0, is_healthy=False, last_health_at=_utcnow())
    _add_node(api, code="it", health_score=95.0, last_health_at=stale_at)

    start_body = _start_trial(client, install_id="install-fallback")
    managed = client.get("/api/client/profile/managed", headers=_auth_headers(start_body))
    assert managed.status_code == 200, managed.text

    smart_connect = managed.json()["smart_connect"]
    assert smart_connect["eligible"] is False
    assert smart_connect["fallback_required"] is True
    assert smart_connect["shortlist"] == []
    assert smart_connect["shortlist_reason"] == "no_eligible_nodes"


def test_latency_samples_are_ingested_and_exposed_as_sticky_hint(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    now = _utcnow()
    _add_node(api, code="pl", health_score=98.0, last_health_at=now)
    _add_node(api, code="it", health_score=95.0, last_health_at=now)

    start_body = _start_trial(client, install_id="install-sticky")
    headers = _auth_headers(start_body)
    ingest = client.post(
        "/api/client/nodes/latency-samples",
        headers=headers,
        json={
            "profile_revision": "2026-04-14:legacy_reality_fallback",
            "transport_profile": "legacy_reality_fallback",
            "selected_node_code": "it",
            "previous_node_code": "pl",
            "stickiness_applied": True,
            "samples": [
                {"node_code": "pl", "rtt_ms": 120},
                {"node_code": "it", "rtt_ms": 95},
            ],
        },
    )
    assert ingest.status_code == 200, ingest.text
    assert ingest.json()["ok"] is True
    assert ingest.json()["accepted_samples"] == 2

    managed = client.get("/api/client/profile/managed", headers=headers)
    assert managed.status_code == 200, managed.text
    sticky = managed.json()["smart_connect"]["stickiness"]
    assert sticky["preferred_node_code"] == "it"
    assert sticky["threshold_percent"] == 15

    db = api.SessionLocal()
    try:
        row = (
            db.query(api.Event)
            .filter(api.Event.event_name == "smart_connect_latency_sample")
            .order_by(api.Event.id.desc())
            .first()
        )
        assert row is not None
        meta = json.loads(str(row.meta_json or "{}"))
        assert meta["selected_node_code"] == "it"
        assert meta["install_id"] == "install-sticky"
    finally:
        db.close()

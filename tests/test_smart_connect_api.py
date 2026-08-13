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


def _load_api(monkeypatch, tmp_path: Path, *, authenticated_egress_enforcement: bool = True):
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
    monkeypatch.setenv(
        "AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED",
        "true" if authenticated_egress_enforcement else "false",
    )

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
    dataplane_ok: bool | None = True,
    authenticated_egress_ok: bool | None = True,
    last_authenticated_egress_at: datetime | None = None,
    last_health_at: datetime | None = None,
    legacy_enabled: bool = True,
    grpc_enabled: bool = True,
    disk_used_gb: float | None = None,
    disk_total_gb: float | None = None,
    disk_free_gb: float | None = None,
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
            dataplane_ok=dataplane_ok,
            authenticated_egress_ok=authenticated_egress_ok,
            last_authenticated_egress_at=last_authenticated_egress_at or last_health_at or _utcnow(),
            last_health_at=last_health_at or _utcnow(),
            disk_used_gb=disk_used_gb,
            disk_total_gb=disk_total_gb,
            disk_free_gb=disk_free_gb,
            transport_profiles_json=_transport_profiles(
                legacy_enabled=legacy_enabled,
                grpc_enabled=grpc_enabled,
            ),
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


def test_managed_profile_exposes_capacity_ranked_eligible_premium_shortlist(monkeypatch, tmp_path) -> None:
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
    assert [item["code"] for item in smart_connect["shortlist"]] == ["pl", "de", "us", "it", "nl", "es"]
    assert [item["outbound_tag"] for item in smart_connect["shortlist"]] == [
        "🇵🇱 Польша",
        "🇩🇪 Германия",
        "🇺🇸 США",
        "🇮🇹 Италия",
        "🇳🇱 Нидерланды",
        "🏳️ ES",
    ]
    assert len(smart_connect["shortlist"]) == 6
    penalties = {item["code"]: item for item in smart_connect["shortlist"]}
    assert penalties["nl"]["rank_hint"]["backend_penalty"] == 0
    assert penalties["nl"]["rank_hint"]["cpu_penalty"] == 0
    assert penalties["pl"]["probe"]["host"] == "example.test"
    assert penalties["pl"]["probe"]["port"] == 443
    assert "fr" not in {item["code"] for item in smart_connect["shortlist"]}
    assert "be" not in {item["code"] for item in smart_connect["shortlist"]}
    assert "nl-free" not in {item["code"] for item in smart_connect["shortlist"]}
    selector = next(
        item
        for item in managed.json()["config_payload"]["outbounds"]
        if item.get("type") == "selector" and item.get("tag") == "🌍 Страны"
    )
    assert selector["default"] == "🇵🇱 Польша"


def test_managed_profile_does_not_deliver_a_node_to_retired_free_pool(monkeypatch, tmp_path) -> None:
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
    assert managed.status_code == 503, managed.text
    assert managed.json()["detail"] == "No eligible nodes"


def test_managed_profile_premium_shortlist_ignores_usernode_mapping_limits(monkeypatch, tmp_path) -> None:
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
    assert [item["code"] for item in managed.json()["smart_connect"]["shortlist"]] == ["pl", "de", "it"]


def test_manual_choice_can_promote_any_eligible_catalog_node_beyond_auto_shortlist(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    api.SMART_CONNECT_SHORTLIST_LIMIT = 2
    client = TestClient(api.app)

    now = _utcnow()
    _add_node(api, code="pl", health_score=99.0, last_health_at=now)
    _add_node(api, code="de", health_score=98.0, last_health_at=now)
    _add_node(api, code="it", health_score=80.0, last_health_at=now)

    start_body = _start_trial(client, install_id="install-manual-outside-auto-shortlist")
    headers = _auth_headers(start_body)
    selected = client.post(
        "/api/client/nodes/select",
        headers=headers,
        json={"mode": "manual", "selected_node_code": "it", "samples": []},
    )
    assert selected.status_code == 200, selected.text
    assert selected.json()["selected_node_code"] == "it"

    managed = client.get(
        "/api/client/profile/managed?selected_node_code=it",
        headers=headers,
    )
    assert managed.status_code == 200, managed.text
    payload = managed.json()
    assert [item["code"] for item in payload["smart_connect"]["shortlist"]] == ["it", "pl"]
    assert payload["smart_connect"]["selected_node_code"] == "it"
    country_selector = next(
        item
        for item in payload["config_payload"]["outbounds"]
        if item.get("type") == "selector" and item.get("tag") == "🌍 Страны"
    )
    assert country_selector["default"] == "🇮🇹 Италия"


def test_managed_profile_fails_closed_when_no_eligible_nodes_remain(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    stale_at = _utcnow() - timedelta(hours=3)
    _add_node(api, code="pl", health_score=95.0, cpu_percent=90.0, last_health_at=_utcnow())
    _add_node(api, code="de", health_score=95.0, is_healthy=False, last_health_at=_utcnow())
    _add_node(api, code="it", health_score=95.0, last_health_at=stale_at)
    _add_node(api, code="es", health_score=95.0, authenticated_egress_ok=None, last_health_at=_utcnow())

    start_body = _start_trial(client, install_id="install-fallback")
    managed = client.get("/api/client/profile/managed", headers=_auth_headers(start_body))
    assert managed.status_code == 503, managed.text
    assert managed.json()["detail"] == "No eligible nodes"


def test_smart_connect_excludes_disk_full_runtime_projection_but_keeps_unknown_disk(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    now = _utcnow()
    _add_node(
        api,
        code="pl",
        health_score=99.0,
        disk_used_gb=96.0,
        disk_total_gb=100.0,
        disk_free_gb=4.0,
        last_health_at=now,
    )
    _add_node(api, code="de", health_score=95.0, last_health_at=now)

    start_body = _start_trial(client, install_id="install-disk-policy-runtime")
    managed = client.get("/api/client/profile/managed", headers=_auth_headers(start_body))

    assert managed.status_code == 200, managed.text
    assert [item["code"] for item in managed.json()["smart_connect"]["shortlist"]] == ["de"]


def test_smart_connect_uses_authenticated_egress_not_basic_edge_flag(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    _add_node(
        api,
        code="pl",
        health_score=95.0,
        dataplane_ok=False,
        authenticated_egress_ok=True,
        last_health_at=_utcnow(),
    )
    start_body = _start_trial(client, install_id="install-authenticated-egress-authority")

    managed = client.get("/api/client/profile/managed", headers=_auth_headers(start_body))

    assert managed.status_code == 200, managed.text
    assert [item["code"] for item in managed.json()["smart_connect"]["shortlist"]] == ["pl"]


def test_smart_connect_keeps_legacy_eligibility_until_authenticated_egress_enforcement(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path, authenticated_egress_enforcement=False)
    client = TestClient(api.app)

    _add_node(
        api,
        code="pl",
        health_score=95.0,
        authenticated_egress_ok=None,
        last_health_at=_utcnow(),
    )
    start_body = _start_trial(client, install_id="install-authenticated-egress-rollout-disabled")

    managed = client.get("/api/client/profile/managed", headers=_auth_headers(start_body))

    assert managed.status_code == 200, managed.text
    assert [item["code"] for item in managed.json()["smart_connect"]["shortlist"]] == ["pl"]


def test_smart_connect_rejects_stale_authenticated_egress_even_with_fresh_basic_health(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    _add_node(
        api,
        code="pl",
        authenticated_egress_ok=True,
        last_authenticated_egress_at=_utcnow() - timedelta(hours=2),
        last_health_at=_utcnow(),
    )
    start_body = _start_trial(client, install_id="install-stale-authenticated-egress")

    managed = client.get("/api/client/profile/managed", headers=_auth_headers(start_body))

    assert managed.status_code == 503, managed.text
    assert managed.json()["detail"] == "No eligible nodes"


def test_managed_profile_ignores_rejected_explicit_node_and_emits_only_shortlist(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    now = _utcnow()
    _add_node(api, code="pl", health_score=98.0, last_health_at=now)
    _add_node(api, code="de", health_score=95.0, authenticated_egress_ok=False, last_health_at=now)

    start_body = _start_trial(client, install_id="install-managed-fail-closed")
    managed = client.get(
        "/api/client/profile/managed?selected_node_code=de",
        headers=_auth_headers(start_body),
    )
    assert managed.status_code == 200, managed.text
    payload = managed.json()
    assert [item["code"] for item in payload["smart_connect"]["shortlist"]] == ["pl"]
    assert "selected_node_code" not in payload["smart_connect"]
    country_selector = next(
        item
        for item in payload["config_payload"]["outbounds"]
        if item.get("type") == "selector" and item.get("tag") == "🌍 Страны"
    )
    assert country_selector["outbounds"] == ["🇵🇱 Польша"]


def test_client_nodes_select_rejects_manual_hard_rejected_node(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    now = _utcnow()
    _add_node(api, code="pl", health_score=98.0, last_health_at=now)
    _add_node(api, code="de", health_score=95.0, authenticated_egress_ok=False, last_health_at=now)
    start_body = _start_trial(client, install_id="install-manual-fail-closed")

    response = client.post(
        "/api/client/nodes/select",
        headers=_auth_headers(start_body),
        json={"mode": "manual", "selected_node_code": "de", "samples": []},
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "selected node is not eligible"


def test_client_nodes_select_fails_closed_when_shortlist_is_empty(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    _add_node(api, code="de", health_score=95.0, authenticated_egress_ok=False, last_health_at=_utcnow())
    start_body = _start_trial(client, install_id="install-auto-fail-closed")

    response = client.post(
        "/api/client/nodes/select",
        headers=_auth_headers(start_body),
        json={"mode": "auto", "samples": []},
    )

    assert response.status_code == 503, response.text
    assert response.json()["detail"] == "No eligible nodes"


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
    managed_payload = managed.json()
    sticky = managed_payload["smart_connect"]["stickiness"]
    assert sticky["preferred_node_code"] == "it"
    assert sticky["threshold_percent"] == 20
    selector = next(
        item
        for item in managed_payload["config_payload"]["outbounds"]
        if item.get("type") == "selector" and item.get("tag") == "🌍 Страны"
    )
    assert selector["default"] == "🇮🇹 Италия"

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


def test_client_candidates_and_select_support_capacity_ranking_and_manual_choice(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    now = _utcnow()
    _add_node(api, code="pl", health_score=98.0, last_health_at=now)
    _add_node(api, code="it", health_score=96.0, last_health_at=now)
    _add_node(api, code="de", health_score=95.0, cpu_percent=90.0, last_health_at=now)

    start_body = _start_trial(client, install_id="install-candidates")
    headers = _auth_headers(start_body)

    candidates = client.get("/api/client/nodes/candidates", headers=headers)
    assert candidates.status_code == 200, candidates.text
    candidate_payload = candidates.json()
    assert candidate_payload["strategy"] == "capacity_rtt_sticky"
    assert [item["code"] for item in candidate_payload["shortlist"]] == ["pl", "it"]
    assert candidate_payload["rejected_counts"]["cpu_hot"] == 1

    auto_select = client.post(
        "/api/client/nodes/select",
        headers=headers,
        json={
            "mode": "auto",
            "profile_revision": candidate_payload["profile_revision"],
            "transport_profile": candidate_payload["transport_profile"],
            "samples": [
                {"node_code": "pl", "rtt_ms": 150},
                {"node_code": "it", "rtt_ms": 50},
            ],
        },
    )
    assert auto_select.status_code == 200, auto_select.text
    assert auto_select.json()["selected_node_code"] == "it"
    assert auto_select.json()["accepted_samples"] == 2

    manual_select = client.post(
        "/api/client/nodes/select",
        headers=headers,
        json={
            "mode": "manual",
            "selected_node_code": "pl",
            "previous_node_code": "it",
            "samples": [],
        },
    )
    assert manual_select.status_code == 200, manual_select.text
    assert manual_select.json()["selected_node_code"] == "pl"
    assert manual_select.json()["accepted_samples"] == 0

    db = api.SessionLocal()
    try:
        rows = (
            db.query(api.Event)
            .filter(api.Event.event_name == "smart_connect_node_select")
            .order_by(api.Event.id.asc())
            .all()
        )
        assert len(rows) == 2
        manual_meta = json.loads(str(rows[-1].meta_json or "{}"))
        assert manual_meta["mode"] == "manual"
        assert manual_meta["samples"] == []
    finally:
        db.close()


def test_ru_bridge_relay_emits_nested_country_protocol_choices_with_us_direct_only(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    rollout_payload = _rollout_payload()
    rollout_payload["ru_bridge_relay"] = {
        "enabled": True,
        "allowlist_node_codes": ["pl", "nl", "it", "us", "de"],
        "excluded_node_codes": ["us"],
        "endpoints": [
            {
                "id": "mini",
                "label": "Белые списки",
                "endpoint_host": "176.123.166.119",
                "endpoint_port": 443,
                "tls_server_name": "www.yandex.ru",
                "reality_public_key": "ru-bridge-pbk",
                "reality_short_id": "ab12cd34",
                "fingerprint": "chrome",
            },
            {
                "id": "ru_spb",
                "label": "Белые списки тип 2",
                "endpoint_host": "193.233.216.73",
                "endpoint_port": 443,
                "tls_server_name": "www.yandex.ru",
                "reality_public_key": "ru-spb-bridge-pbk",
                "reality_short_id": "ef56ab78",
                "fingerprint": "chrome",
            },
        ],
    }
    rollout_payload["cohort_overrides"]["ru-bridge-canary"] = {
        "install_ids": ["install-ru-bridge"],
        "transport_profile": "ru_bridge_relay",
    }
    db = api.SessionLocal()
    try:
        api._set_app_setting_json(s=db, key="network_rollout_config", value=rollout_payload)
        db.commit()
    finally:
        db.close()

    now = _utcnow()
    _add_node(api, code="pl", health_score=98.0, last_health_at=now)
    _add_node(api, code="nl", health_score=96.0, last_health_at=now)
    _add_node(api, code="it", health_score=94.0, last_health_at=now)
    _add_node(api, code="us", health_score=99.0, last_health_at=now)
    _add_node(api, code="de", health_score=97.0, last_health_at=now, legacy_enabled=False)

    start_body = _start_trial(client, install_id="install-ru-bridge")
    assert start_body["client_policy"]["transport_profile"] == "ru_bridge_relay"
    assert start_body["client_policy"]["transport_kind"] == "ru_bridge"
    assert start_body["client_policy"]["engine_hint"] == "singbox"

    managed = client.get("/api/client/profile/managed", headers=_auth_headers(start_body))
    assert managed.status_code == 200, managed.text
    body = managed.json()
    assert body["transport_profile"] == "ru_bridge_relay"
    assert body["fallback_order"] == ["ru_bridge_relay", "legacy_reality_fallback"]
    assert body["config_format"] == "singbox-json"
    assert body["smart_connect"]["rejected_counts"]["transport_mismatch"] == 1

    config = body["config_payload"]
    outbounds = {item["tag"]: item for item in config["outbounds"]}
    hidden_bridge_tag = f"POKROV мост{api.HIDDIFY_HIDDEN_TAG_SUFFIX}"
    hidden_spb_bridge_tag = f"POKROV мост Белые списки тип 2{api.HIDDIFY_HIDDEN_TAG_SUFFIX}"
    assert hidden_bridge_tag in outbounds
    assert hidden_spb_bridge_tag in outbounds
    assert "POKROV мост" not in outbounds
    assert not any("via RU" in tag or "RU bridge" in tag for tag in outbounds)
    bridge = outbounds[hidden_bridge_tag]
    assert bridge["server"] == "176.123.166.119"
    assert bridge["server_port"] == 443
    assert bridge["tls"]["server_name"] == "www.yandex.ru"
    assert bridge["tls"]["reality"]["public_key"] == "ru-bridge-pbk"
    assert bridge["tls"]["reality"]["short_id"] == "ab12cd34"
    assert outbounds[hidden_spb_bridge_tag]["server"] == "193.233.216.73"
    assert config["_meta"]["ru_bridge"]["endpoints"] == [
        {"id": "mini", "label": "Белые списки"},
        {"id": "ru_spb", "label": "Белые списки тип 2"},
    ]

    country_selector = outbounds["🌍 Страны"]
    assert country_selector["outbounds"] == [
        "🇵🇱 Польша",
        "🇳🇱 Нидерланды",
        "🇮🇹 Италия",
        "🇺🇸 США",
    ]

    for label in ["🇵🇱 Польша", "🇳🇱 Нидерланды", "🇮🇹 Италия", "🇺🇸 США"]:
        assert outbounds[label]["type"] == "selector"

    for label in ["🇵🇱 Польша", "🇳🇱 Нидерланды", "🇮🇹 Италия"]:
        normal_tag = f"{label} · Обычный"
        bridge_tag = f"{label} · Белые списки"
        bridge_spb_tag = f"{label} · Белые списки тип 2"
        assert outbounds[label]["outbounds"] == [normal_tag, bridge_tag, bridge_spb_tag]
        assert outbounds[normal_tag]["type"] == "vless"
        assert "detour" not in outbounds[normal_tag]
        assert outbounds[bridge_tag]["type"] == "vless"
        assert outbounds[bridge_tag]["detour"] == hidden_bridge_tag
        assert outbounds[bridge_spb_tag]["type"] == "vless"
        assert outbounds[bridge_spb_tag]["detour"] == hidden_spb_bridge_tag

    assert outbounds["🇺🇸 США"]["outbounds"] == ["🇺🇸 США · Обычный"]
    assert outbounds["🇺🇸 США · Обычный"]["type"] == "vless"
    assert "detour" not in outbounds["🇺🇸 США · Обычный"]
    assert "🇺🇸 США · Белые списки" not in outbounds
    assert "🇺🇸 США · Белые списки тип 2" not in outbounds
    assert "🇩🇪 Германия" not in outbounds

from __future__ import annotations

import asyncio
import hashlib
import hmac
import importlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from fastapi.testclient import TestClient


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _sign_telegram_init_data(*, bot_token: str, tg_id: int = 9999, username: str = "admin") -> str:
    params = {
        "auth_date": str(int(datetime.now(timezone.utc).timestamp())),
        "query_id": "ops-test",
        "user": f'{{"id":{tg_id},"first_name":"Admin","username":"{username}"}}',
    }
    items = sorted((k, v) for k, v in params.items())
    data_check_string = "\n".join([f"{k}={v}" for k, v in items])
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    check_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    payload = dict(params)
    payload["hash"] = check_hash
    return urlencode(payload)


def _load_api(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "admin-ops-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "admin-ops-secret")
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
        "admin_ops_service",
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
        "internal_request_auth",
        "ru_probe_contract",
        "ru_probe_service",
        "worker",
    ]:
        sys.modules.pop(name, None)

    return importlib.import_module("api")


def _admin_headers() -> dict[str, str]:
    return {"X-Telegram-Init-Data": _sign_telegram_init_data(bot_token="test_bot_token_123")}


def _gb(value: float) -> int:
    return int(value * 1024 * 1024 * 1024)


def _ru_payload_from_manifest(
    manifest: dict[str, object],
    *,
    now: datetime,
    run_id: str,
) -> dict[str, object]:
    finished_at = now - timedelta(minutes=6)
    targets: list[dict[str, object]] = []
    for expected in manifest["targets"]:
        stages: dict[str, dict[str, object]] = {}
        for stage_name in (
            "dns",
            "tcp",
            "tls",
            "http_large_body",
            "transport_handshake",
        ):
            required = stage_name in expected["required_stages"]
            stages[stage_name] = {
                "status": "pass" if required else "not_applicable",
                "latency_ms": 10 if required else None,
                "code": None,
            }
        families = expected["endpoint"]["address_families"]
        targets.append(
            {
                "target_id": expected["target_id"],
                "target_kind": expected["target_kind"],
                "scope": expected["scope"],
                "node_code": expected["node_code"],
                "endpoint": dict(expected["endpoint"]),
                "endpoint_fingerprint": expected["endpoint_fingerprint"],
                "stages": stages,
                "address_family_status": {
                    "ipv4": "pass" if "ipv4" in families else "not_applicable",
                    "ipv6": "pass" if "ipv6" in families else "not_applicable",
                },
                "transport": {
                    "profile_code": expected["endpoint"]["transport_profile"],
                    "handshake_status": stages["transport_handshake"]["status"],
                    "classification": "ok",
                    "detail_code": None,
                },
                "detail_code": None,
                "detail": None,
            }
        )
    return {
        "schema_version": 2,
        "run_id": run_id,
        "origin": "ru",
        "probe_host": {"id": "mini", "label": "Мини", "public_ip": None},
        "runner_version": "2.0.0",
        "manifest_revision": manifest["manifest_revision"],
        "started_at": (finished_at - timedelta(minutes=2))
        .isoformat()
        .replace("+00:00", "Z"),
        "finished_at": finished_at.isoformat().replace("+00:00", "Z"),
        "execution_status": "completed",
        "evidence_code": None,
        "targets": targets,
        "ok": True,
        "google_reachable": True,
        "xhttp_alive": False,
        "hysteria_alive": False,
        "classifications": [],
    }


def _seed_ops_fixture(api, *, now: datetime) -> None:
    from models import AccessKey, KeyUsageRollup, Node, NodeHealthSample, ProviderTrafficQuota, User

    s = api.SessionLocal()
    try:
        s.add_all(
            [
                Node(
                    code="nl-free",
                    name="NL Free",
                    host="nl-free.example.test",
                    inbound_id=1,
                    enabled=True,
                    accepting_new_clients=True,
                    is_healthy=True,
                    health_score=92,
                    last_health_at=now,
                ),
                Node(
                    code="de",
                    name="DE",
                    host="de.example.test",
                    inbound_id=1,
                    enabled=True,
                    accepting_new_clients=True,
                    is_healthy=True,
                    health_score=95,
                    last_health_at=now,
                ),
            ]
        )
        s.add_all(
            [
                User(
                    tg_id=1001,
                    username="nearcap",
                    uuid="00000000-0000-0000-0000-000000001001",
                    email="nearcap@example.test",
                    sub_type="FREE",
                    current_plan_code="free_monthly",
                    expiry_at=now + timedelta(days=20),
                    is_active=True,
                    free_cycle_anchor_at=now - timedelta(days=10),
                    free_cycle_last_reset_at=now - timedelta(days=10),
                    free_cycle_next_reset_at=now + timedelta(days=20),
                ),
                User(
                    tg_id=1002,
                    username="overcap",
                    uuid="00000000-0000-0000-0000-000000001002",
                    email="overcap@example.test",
                    sub_type="FREE",
                    current_plan_code="free_monthly",
                    expiry_at=now + timedelta(days=20),
                    is_active=True,
                    free_cycle_anchor_at=now - timedelta(days=10),
                    free_cycle_last_reset_at=now - timedelta(days=10),
                    free_cycle_next_reset_at=now + timedelta(days=20),
                ),
            ]
        )
        s.flush()
        s.add_all(
            [
                AccessKey(
                    tg_id=1001,
                    key_uuid="00000000-0000-0000-0000-000000011001",
                    panel_email="nearcap@example.test",
                    node_code="nl-free",
                    pool_code="free_pool",
                    state="active",
                ),
                AccessKey(
                    tg_id=1002,
                    key_uuid="00000000-0000-0000-0000-000000011002",
                    panel_email="overcap@example.test",
                    node_code="nl-free",
                    pool_code="free_pool",
                    state="active",
                ),
            ]
        )
        s.flush()
        keys = {row.tg_id: row.id for row in s.query(AccessKey).all()}
        s.add_all(
            [
                KeyUsageRollup(
                    key_id=keys[1001],
                    tg_id=1001,
                    node_code="nl-free",
                    panel_email="nearcap@example.test",
                    window_bucket_at=now - timedelta(days=1),
                    window_seconds=86400,
                    total_bytes=_gb(4.25),
                    observations=12,
                ),
                KeyUsageRollup(
                    key_id=keys[1002],
                    tg_id=1002,
                    node_code="nl-free",
                    panel_email="overcap@example.test",
                    window_bucket_at=now - timedelta(days=1),
                    window_seconds=86400,
                    total_bytes=_gb(5.5),
                    observations=14,
                ),
                KeyUsageRollup(
                    key_id=keys[1002],
                    tg_id=1002,
                    node_code="de",
                    panel_email="overcap@example.test",
                    window_bucket_at=now - timedelta(days=1),
                    window_seconds=86400,
                    total_bytes=_gb(1.0),
                    observations=4,
                ),
            ]
        )
        s.add_all(
            [
                NodeHealthSample(
                    node_code="de",
                    sampled_at=now - timedelta(days=5),
                    total_traffic_bytes=_gb(1.0),
                    network_total_mbps=80.0,
                    cpu_percent=20.0,
                    score=95.0,
                    is_healthy=True,
                ),
                NodeHealthSample(
                    node_code="de",
                    sampled_at=now - timedelta(hours=1),
                    total_traffic_bytes=_gb(9.0),
                    network_total_mbps=110.0,
                    cpu_percent=35.0,
                    score=90.0,
                    is_healthy=True,
                ),
            ]
        )
        s.add(
            ProviderTrafficQuota(
                node_code="de",
                included_bytes=_gb(10.0),
                reset_day=28,
                timezone="UTC",
                warning_ratio=0.5,
                critical_ratio=0.8,
                enabled=True,
                notes="test quota",
            )
        )
        s.commit()
    finally:
        s.close()


def _seed_ru_read_fixture(api, *, now: datetime) -> None:
    from models import (
        NodeHealthSample,
        NodeRuntimeMetric,
        OpsAlert,
        RuProbeUploaderHeartbeat,
    )

    s = api.SessionLocal()
    try:
        node = s.query(api.Node).filter(api.Node.code == "de").one()
        node.observer_last_push_at = now - timedelta(minutes=3)
        node.observer_last_batch_id = "observer-batch-safe"
        node.observer_unmatched_count = 2
        node.observer_parse_error_count = 1
        node.transport_profiles_json = json.dumps(
            [
                {
                    "name": "legacy_reality_fallback",
                    "enabled": True,
                    "kind": "reality",
                    "inbound_id": 1,
                    "host": "203.0.113.77",
                    "port": 443,
                    "tls_server_name": "front.example.test",
                    "reality_public_key": "SYNTHETIC-PUBLIC-MATERIAL",
                    "reality_short_id": "SYNTHETIC-SHORT-ID",
                }
            ]
        )
        s.add(
            NodeHealthSample(
                node_code="de",
                sampled_at=now - timedelta(minutes=2),
                panel_latency_ms=42,
                panel_error_rate=0.0,
                active_clients=7,
                cpu_percent=23.5,
                memory_used_mb=1024,
                memory_total_mb=4096,
                disk_used_gb=12.5,
                disk_total_gb=80.0,
                disk_free_gb=67.5,
                network_rx_mbps=10.0,
                network_tx_mbps=20.0,
                network_total_mbps=30.0,
                is_healthy=True,
                score=95.0,
                source="brain",
                probe_at=now - timedelta(minutes=2),
                probe_stage="tls",
                probe_classification="ok",
                ipv4_health="ok",
                ipv6_health="missing",
                transport_health_json="{malformed-json",
            )
        )
        s.add(
            NodeRuntimeMetric(
                node_code="de",
                sampled_at=now - timedelta(minutes=1),
                source="collector",
                provisioned_clients_count=7,
                online_connections_hint=3,
                network_rx_mbps_1m=11.0,
                network_tx_mbps_1m=21.0,
                network_rx_mbps_5m=9.0,
                network_tx_mbps_5m=19.0,
                network_total_mbps=32.0,
                cpu_percent=24.0,
                memory_used_mb=1024,
                memory_total_mb=4096,
                capacity_score=88.0,
                capacity_state="ok",
                meta_json="{malformed-json",
            )
        )
        s.flush()
        aware_now = now.replace(tzinfo=timezone.utc)
        manifest = api.build_ru_manifest(s, now=aware_now)
        payload = _ru_payload_from_manifest(
            manifest,
            now=aware_now,
            run_id="00000000-0000-4000-8000-000000000201",
        )
        evaluated = api.evaluate_ru_run(s, payload, now=aware_now)
        api.store_evaluated_ru_run(
            s,
            evaluated,
            artifact_sha256="b" * 64,
            ingest_key_id="ru-test",
            received_at=aware_now - timedelta(minutes=5),
        )
        s.add(
            RuProbeUploaderHeartbeat(
                probe_host_id="mini",
                observed_at=now - timedelta(minutes=10),
                received_at=now - timedelta(minutes=9),
                service_version="2.0.0",
                pending_count=2,
                blocked_count=0,
                quarantine_count=1,
                oldest_pending_at=now - timedelta(hours=1),
                archive_write_ok=True,
                disk_free_bytes=10_000_000,
                disk_state="ok",
                last_error_code="quarantine_present",
                ingest_key_id="ru-test",
            )
        )
        s.add(
            OpsAlert(
                fingerprint="node_metrics:de:cpu_high",
                source="node_metrics",
                severity="warning",
                status="active",
                title="CPU",
                node_code="de",
                first_seen_at=now,
                last_seen_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        s.commit()
    finally:
        s.close()


def test_provider_quota_cycle_bounds_handles_short_month_reset(monkeypatch, tmp_path) -> None:
    _load_api(monkeypatch, tmp_path)
    from admin_ops_service import provider_quota_cycle_bounds

    start, end = provider_quota_cycle_bounds(now=datetime(2026, 3, 30, 12, 0, 0), reset_day=31, timezone_name="UTC")

    assert start == datetime(2026, 2, 28, 0, 0, 0)
    assert end == datetime(2026, 3, 31, 0, 0, 0)


def test_capacity_alert_candidates_ignore_disabled_nodes(monkeypatch, tmp_path) -> None:
    _load_api(monkeypatch, tmp_path)
    from admin_ops_service import build_alert_candidates

    candidates = build_alert_candidates(
        metrics_status={},
        provider_status=[],
        free_summary={},
        capacity_rows=[
            {
                "code": "brain",
                "enabled": False,
                "capacity_state": "hard_reject",
                "reject_reason": "disabled",
            },
            {
                "code": "us",
                "enabled": True,
                "capacity_state": "hard_reject",
                "reject_reason": "unhealthy",
            },
        ],
    )

    fingerprints = {row["fingerprint"] for row in candidates}
    assert "node_capacity:brain" not in fingerprints
    assert "node_capacity:us" in fingerprints


def test_admin_ops_free_tier_provider_status_and_alerts(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    sent_messages: list[tuple[int, str]] = []

    async def fake_send(chat_id: int, text: str, **_kwargs) -> bool:
        sent_messages.append((chat_id, text))
        return True

    monkeypatch.setattr(api, "_telegram_send_message", fake_send)
    now = _utcnow()
    _seed_ops_fixture(api, now=now)
    client = TestClient(api.app)
    headers = _admin_headers()

    free_summary = client.get("/api/admin/free-tier/summary", headers=headers)
    assert free_summary.status_code == 200, free_summary.text
    free_body = free_summary.json()
    assert free_body["summary"]["free_users"] == 2
    assert free_body["summary"]["near_cap_users"] == 1
    assert free_body["summary"]["over_cap_users"] == 1
    assert free_body["facts"]["node_pool"] == "NL-free"

    free_users = client.get("/api/admin/free-tier/users", headers=headers)
    assert free_users.status_code == 200, free_users.text
    states = {row["username"]: row["state"] for row in free_users.json()["users"]}
    assert states == {"overcap": "over_cap", "nearcap": "near_cap"}

    quota_status = client.get("/api/admin/provider-quotas/status", headers=headers)
    assert quota_status.status_code == 200, quota_status.text
    de_status = next(row for row in quota_status.json()["nodes"] if row["node_code"] == "de")
    assert de_status["state"] == "critical"
    assert de_status["used_gb"] == 8.0
    assert de_status["remaining_gb"] == 2.0

    traffic = client.get("/api/admin/traffic/summary", headers=headers)
    assert traffic.status_code == 200, traffic.text
    assert {row["node_code"] for row in traffic.json()["rows"]} >= {"nl-free", "de"}

    overview = client.get("/api/admin/ops/overview", headers=headers)
    assert overview.status_code == 200, overview.text
    overview_body = overview.json()
    assert overview_body["alerts"]["active_count"] >= 2
    fingerprints = {row["fingerprint"] for row in overview_body["alerts"]["active"]}
    assert "provider_quota:de" in fingerprints
    assert "free_tier:over_cap" in fingerprints
    assert sent_messages
    assert all("test_bot_token_123" not in text for _chat_id, text in sent_messages)
    assert all("panel_pass" not in text for _chat_id, text in sent_messages)

    provider_alert = next(row for row in overview_body["alerts"]["active"] if row["fingerprint"] == "provider_quota:de")
    ack = client.post(f"/api/admin/alerts/{provider_alert['id']}/ack", headers=headers)
    assert ack.status_code == 200, ack.text
    assert ack.json()["alert"]["acknowledged_by"] == 9999

    silence = client.post(f"/api/admin/alerts/{provider_alert['id']}/silence", headers=headers, json={"minutes": 30})
    assert silence.status_code == 200, silence.text
    assert silence.json()["alert"]["status"] == "silenced"


def test_admin_short_lived_session_can_authorize_ops_endpoints(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    now = _utcnow()
    _seed_ops_fixture(api, now=now)
    client = TestClient(api.app)

    issued = client.post("/api/admin/auth/session", headers=_admin_headers())
    assert issued.status_code == 200, issued.text
    body = issued.json()
    assert body["token_transport"] == "bearer"
    assert body["expires_in"] == int(api.ADMIN_WEB_SESSION_TTL_SECONDS)
    assert body["user"]["role"] == "superadmin"

    overview = client.get("/api/admin/ops/overview", headers={"Authorization": f"Bearer {body['token']}"})
    assert overview.status_code == 200, overview.text
    assert overview.json()["ok"] is True


def test_admin_payments_summary_counts_revenue_attention_and_abandoned(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import Event, ExternalOrder, FunnelEvent, PayAttempt

    now = _utcnow()
    _seed_ops_fixture(api, now=now)
    s = api.SessionLocal()
    try:
        s.add_all(
            [
                ExternalOrder(
                    order_id="paid-ops-1",
                    tg_id=1001,
                    provider="lavatop",
                    plan_code="1_month",
                    source="site",
                    amount=990.0,
                    currency="RUB",
                    status="paid",
                    created_at=now - timedelta(hours=3),
                    paid_at=now - timedelta(hours=2),
                ),
                ExternalOrder(
                    order_id="pending-ops-1",
                    tg_id=1002,
                    provider="lavatop",
                    plan_code="1_month",
                    source="site",
                    amount=990.0,
                    currency="RUB",
                    status="pending",
                    created_at=now - timedelta(hours=2),
                ),
                ExternalOrder(
                    order_id="manual-ops-1",
                    tg_id=1002,
                    provider="lavatop",
                    plan_code="1_month",
                    source="site",
                    amount=990.0,
                    currency="RUB",
                    status="manual_review",
                    created_at=now - timedelta(hours=1),
                ),
                ExternalOrder(
                    order_id="failed-ops-1",
                    tg_id=1002,
                    provider="lavatop",
                    plan_code="1_month",
                    source="site",
                    amount=990.0,
                    currency="RUB",
                    status="failed",
                    created_at=now - timedelta(minutes=30),
                ),
                FunnelEvent(
                    session_id="checkout-session-1",
                    channel="site",
                    event_name="checkout_start",
                    stage="checkout_start",
                    source="site",
                    path="/checkout",
                    created_at=now - timedelta(hours=3),
                ),
                FunnelEvent(
                    session_id="checkout-session-2",
                    channel="site",
                    event_name="checkout_view",
                    stage="checkout_view",
                    source="site",
                    path="/checkout",
                    created_at=now - timedelta(hours=2),
                ),
                Event(tg_id=1001, event_name="clicked_pay", source="webapp", created_at=now - timedelta(hours=3)),
                Event(tg_id=1002, event_name="pay_started", source="webapp", created_at=now - timedelta(hours=2)),
                Event(tg_id=1001, event_name="paid", source="webapp", created_at=now - timedelta(hours=1)),
                PayAttempt(
                    tg_id=1002,
                    source="bot",
                    plan_code="1_month",
                    amount_stars=0,
                    currency="RUB",
                    status="started",
                    invoice_payload="ops-summary-started",
                    started_at=now - timedelta(hours=2),
                    updated_at=now - timedelta(hours=2),
                ),
            ]
        )
        s.commit()
    finally:
        s.close()

    client = TestClient(api.app)
    response = client.get("/api/admin/payments/summary?period=7d", headers=_admin_headers())

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["period"]["key"] == "7d"
    assert body["revenue"]["currency"] == "RUB"
    assert body["revenue"]["amount"] == 990.0
    assert body["revenue"]["paid_count"] == 1
    assert body["attention"]["pending_count"] == 1
    assert body["attention"]["manual_review_count"] == 1
    assert body["attention"]["failed_count"] == 1
    assert body["attention"]["problem_count"] == 3
    assert body["abandoned"]["buy_click_not_paid"] >= 1
    assert body["abandoned"]["checkout_not_paid"] >= 1
    assert {row["order_id"] for row in body["problem_orders"]} >= {"pending-ops-1", "manual-ops-1", "failed-ops-1"}


def test_admin_online_users_aggregate_omits_raw_ips(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import KeyPressureState, ObserverUserState

    now = _utcnow()
    _seed_ops_fixture(api, now=now)
    s = api.SessionLocal()
    try:
        s.add_all(
            [
                KeyPressureState(
                    key_id=9001,
                    tg_id=1001,
                    node_code="de",
                    panel_email="nearcap@example.test",
                    state="watch",
                    pressure_score=72.5,
                    reasons_json=json.dumps(["multi_ip", "burst"], ensure_ascii=False),
                    distinct_source_ips_1h=2,
                    distinct_source_ips_24h=2,
                    node_count_24h=1,
                    traffic_gb_24h=1.25,
                    manual_review_required=True,
                    updated_at=now,
                ),
                ObserverUserState(
                    tg_id=1001,
                    state="watch",
                    reasons_json=json.dumps(["multi_ip"], ensure_ascii=False),
                    observed_ip_count_24h=2,
                    observed_ip_count_7d=2,
                    observed_ip_count_30d=2,
                    observed_node_count_24h=1,
                    observed_node_count_7d=1,
                    observed_node_count_30d=1,
                    last_observed_at=now,
                    updated_at=now,
                ),
            ]
        )
        s.commit()
    finally:
        s.close()

    class FakeControlPanel:
        async def get_node_online_clients(self, *, node_codes=None):
            return {
                "rows": [
                    {
                        "node_code": "de",
                        "node_name": "DE",
                        "tg_id": 1001,
                        "panel_email": "nearcap@example.test",
                        "client_uuid": "client-1001",
                        "ip_count": 2,
                        "last_online_at": now.isoformat(),
                        "source_ip_raw": "203.0.113.77",
                    },
                    {
                        "node_code": "nl-free",
                        "panel_email": "unknown@example.test",
                        "client_uuid": "client-unknown",
                        "ip_count": 1,
                        "last_online_at": now.isoformat(),
                        "source_ip_raw": "198.51.100.42",
                    },
                ],
                "errors": [{"node_code": "pl", "error": "panel timeout"}],
            }

        async def close(self):
            return None

    monkeypatch.setattr(api, "ControlPanel", FakeControlPanel)
    client = TestClient(api.app)
    response = client.get("/api/admin/online/users?limit=50", headers=_admin_headers())

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["summary"]["raw_ip_exposed"] is False
    assert body["summary"]["known_users_online"] == 1
    assert body["summary"]["unknown_online_keys"] == 1
    assert body["summary"]["nodes_with_panel_errors"] == 1
    known = next(row for row in body["rows"] if row["tg_id"] == 1001)
    assert known["raw_ip_exposed"] is False
    assert known["online_connections_now"] == 2
    assert "manual_review" in known["risk_flags"]
    assert "multi_ip" in known["risk_flags"]
    assert "observer:watch" in known["risk_flags"]
    assert "203.0.113.77" not in response.text
    assert "198.51.100.42" not in response.text
    assert "source_ip_raw" not in response.text


def test_admin_broadcast_dry_run_does_not_send(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    now = _utcnow()
    _seed_ops_fixture(api, now=now)
    sent_messages: list[tuple[int, str]] = []

    async def fake_send(chat_id: int, text: str, **_kwargs) -> bool:
        sent_messages.append((chat_id, text))
        return True

    monkeypatch.setattr(api, "_telegram_send_message", fake_send)
    client = TestClient(api.app)
    response = client.post(
        "/api/admin/broadcast",
        headers=_admin_headers(),
        json={"text": "Проверка dry-run", "segment": "all_active", "limit": 20, "dry_run": True},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ok"] is True
    assert body["dry_run"] is True
    assert body["attempted"] == 2
    assert body["sent"] == 0
    assert body["failed"] == 0
    assert sent_messages == []


def test_provider_quota_usage_handles_counter_reset(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from admin_ops_service import provider_quota_usage_bytes
    from models import NodeHealthSample

    now = _utcnow()
    s = api.SessionLocal()
    try:
        s.add_all(
            [
                NodeHealthSample(node_code="de", sampled_at=now - timedelta(hours=3), total_traffic_bytes=_gb(10)),
                NodeHealthSample(node_code="de", sampled_at=now - timedelta(hours=2), total_traffic_bytes=_gb(1)),
                NodeHealthSample(node_code="de", sampled_at=now - timedelta(hours=1), total_traffic_bytes=_gb(3)),
            ]
        )
        s.commit()
        used_bytes, sample_count, source = provider_quota_usage_bytes(
            s=s,
            node_code="de",
            cycle_start=now - timedelta(hours=4),
            cycle_end=now + timedelta(hours=1),
        )
        assert sample_count == 3
        assert used_bytes == _gb(3)
        assert source == "node_health_samples_total_counter_delta"
    finally:
        s.close()


def test_provider_quota_crud_writes_audit(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import ProviderTrafficQuotaAudit

    client = TestClient(api.app)
    headers = _admin_headers()

    created = client.post(
        "/api/admin/provider-quotas",
        headers=headers,
        json={
            "node_code": "nl-free",
            "included_gb": 100,
            "reset_day": 15,
            "timezone": "UTC",
            "warning_ratio": 0.7,
            "critical_ratio": 0.9,
            "enabled": True,
            "notes": "free hoster cap",
        },
    )
    assert created.status_code == 200, created.text
    assert created.json()["quota"]["included_gb"] == 100.0

    updated = client.patch(
        "/api/admin/provider-quotas/nl-free",
        headers=headers,
        json={"included_gb": 120, "notes": "raised after provider change"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["quota"]["included_gb"] == 120.0

    deleted = client.delete("/api/admin/provider-quotas/nl-free", headers=headers)
    assert deleted.status_code == 200, deleted.text

    s = api.SessionLocal()
    try:
        actions = [row.action for row in s.query(ProviderTrafficQuotaAudit).order_by(ProviderTrafficQuotaAudit.id.asc()).all()]
    finally:
        s.close()
    assert actions == ["create", "update", "delete"]


def test_durable_alert_refresh_resolves_missing_candidates(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from admin_ops_service import refresh_ops_alerts
    from models import OpsAlert

    now = _utcnow()
    s = api.SessionLocal()
    try:
        rows, notifications = refresh_ops_alerts(
            s=s,
            now=now,
            candidates=[
                {
                    "fingerprint": "provider_quota:de",
                    "source": "provider_quota",
                    "severity": "critical",
                    "title": "Provider cap de",
                    "body": "test",
                    "node_code": "de",
                    "metadata": {"used_pct": 99},
                }
            ],
        )
        s.commit()
        assert rows[0].status == "active"
        assert notifications == [
            {
                "kind": "active",
                "fingerprint": "provider_quota:de",
                "severity": "critical",
                "title": "Provider cap de",
            }
        ]

        rows, notifications = refresh_ops_alerts(s=s, now=now + timedelta(minutes=5), candidates=[])
        s.commit()
        row = s.query(OpsAlert).filter(OpsAlert.fingerprint == "provider_quota:de").one()
        assert row.status == "resolved"
        assert row.resolved_at is not None
        assert notifications == [
            {
                "kind": "resolved",
                "fingerprint": "provider_quota:de",
                "severity": "critical",
                "title": "Provider cap de",
            }
        ]
        assert rows[0].status == "resolved"
    finally:
        s.close()


def test_worker_refreshes_durable_alerts_without_admin_ui(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import OpsAlert

    now = _utcnow()
    _seed_ops_fixture(api, now=now)
    delivered: list[dict] = []

    async def fake_deliver(notifications: list[dict]) -> None:
        delivered.extend(notifications)

    worker = importlib.import_module("worker")
    monkeypatch.setattr(worker, "_deliver_ops_alert_notifications", fake_deliver)

    notification_count = asyncio.run(worker.admin_ops_alert_refresh_once())

    assert notification_count >= 2
    assert {item["fingerprint"] for item in delivered} >= {"provider_quota:de", "free_tier:over_cap"}

    s = api.SessionLocal()
    try:
        fingerprints = {
            row.fingerprint
            for row in s.query(OpsAlert).filter(OpsAlert.status == "active").all()
        }
    finally:
        s.close()
    assert {"provider_quota:de", "free_tier:over_cap"}.issubset(fingerprints)


def test_ru_read_endpoints_require_admin_and_return_stable_dtos(
    monkeypatch, tmp_path
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    now = _utcnow()
    _seed_ops_fixture(api, now=now)
    _seed_ru_read_fixture(api, now=now)

    class FakeControlPanel:
        async def login(self):
            return None

        async def get_node_online_summaries(self, *, node_codes=None):
            return {}

        async def close(self):
            return None

    monkeypatch.setattr(api, "ControlPanel", FakeControlPanel)
    client = TestClient(api.app)
    paths = [
        "/api/admin/probes/ru-origin/latest",
        "/api/admin/probes/ru-origin/runs?limit=10",
        "/api/admin/probes/ru-origin/uploader-status",
        "/api/admin/nodes/de/observability",
        "/api/admin/search?q=de",
    ]

    for path in paths:
        denied = client.get(path)
        assert denied.status_code in {401, 403}, (path, denied.text)

    headers = _admin_headers()
    latest = client.get(paths[0], headers=headers)
    assert latest.status_code == 200, latest.text
    latest_body = latest.json()
    assert latest_body["latest_eligible_run"]["run_id"].endswith("0201")
    assert latest_body["latest_received_attempt"]["run_id"].endswith("0201")
    assert latest_body["nodes"][0]["threshold_seconds"] == 7 * 60 * 60

    runs = client.get(paths[1], headers=headers)
    assert runs.status_code == 200, runs.text
    assert runs.json()["items"][0]["run_id"].endswith("0201")
    assert "artifact_sha256" not in runs.text
    assert "203.0.113.77" not in runs.text

    uploader = client.get(paths[2], headers=headers)
    assert uploader.status_code == 200, uploader.text
    assert uploader.json()["heartbeat"]["pending_count"] == 2
    assert uploader.json()["threshold_seconds"] == 45 * 60

    observability = client.get(paths[3], headers=headers)
    assert observability.status_code == 200, observability.text
    body = observability.json()
    assert body["node"]["code"] == "de"
    assert body["sources"]["brain_metrics"]["sampled_at"]
    assert body["sources"]["brain_metrics"]["threshold_seconds"] >= 300
    assert body["sources"]["brain_metrics"]["status"] == "ok"
    assert body["sources"]["brain_metrics"]["details"]["cpu_percent"] == 23.5
    assert body["sources"]["runtime"]["sampled_at"]
    assert body["sources"]["runtime"]["status"] == "ok"
    assert body["sources"]["runtime"]["details"]["provisioned_clients_count"] == 7
    assert body["sources"]["observer"]["sampled_at"]
    assert body["sources"]["ru_origin"]["sampled_at"]
    assert body["ru"]["history"]["items"]
    serialized = observability.text.lower()
    for forbidden in (
        "panel_pass",
        "panel_user",
        "reality_public_key",
        "reality_short_id",
        "synthetic-public-material",
        "synthetic-short-id",
        "203.0.113.77",
        "source_ip_raw",
    ):
        assert forbidden not in serialized

    s = api.SessionLocal()
    try:
        from models import NodeHealthSample, NodeRuntimeMetric

        s.add(
            api.Node(
                code="brain",
                name="Brain",
                host="brain.example.test",
                inbound_id=1,
                enabled=True,
                accepting_new_clients=True,
                last_probe_at=now - timedelta(seconds=30),
                transport_profiles_json=json.dumps(
                    [
                        {
                            "name": "legacy_reality_fallback",
                            "enabled": True,
                            "kind": "reality",
                            "inbound_id": 1,
                            "port": 443,
                        }
                    ]
                ),
            )
        )
        s.add(
            api.Node(
                code="panel-down",
                name="Panel down",
                host="panel-down.example.test",
                inbound_id=1,
                enabled=True,
                accepting_new_clients=True,
                is_healthy=False,
                last_health_at=now - timedelta(seconds=20),
                last_probe_at=now - timedelta(seconds=10),
                cpu_percent=0.0,
                provisioned_clients_count=0,
                online_connections_hint=0,
            )
        )
        s.add(
            NodeHealthSample(
                node_code="panel-down",
                sampled_at=now - timedelta(seconds=20),
                panel_latency_ms=125,
                panel_error_rate=0.5,
                active_clients=0,
                cpu_percent=0.0,
                is_healthy=False,
                score=10.0,
                source="collector",
                probe_at=now - timedelta(seconds=10),
                probe_stage="panel_login",
                probe_error_kind="panel_login_failed",
                transport_health_json=json.dumps(
                    {
                        "panel_state": "failed",
                        "dataplane_state": "healthy",
                    }
                ),
            )
        )
        s.add(
            NodeRuntimeMetric(
                node_code="panel-down",
                sampled_at=now - timedelta(seconds=15),
                source="collector",
                provisioned_clients_count=0,
                online_connections_hint=0,
                capacity_state="unknown",
                meta_json=json.dumps(
                    {
                        "panel_state": "failed",
                        "dataplane_state": "healthy",
                    }
                ),
            )
        )
        s.commit()
    finally:
        s.close()

    health = client.get("/api/admin/nodes/health", headers=headers)
    assert health.status_code == 200, health.text
    brain_health = next(row for row in health.json()["nodes"] if row["code"] == "brain")
    assert brain_health["country_code"] == "DE"
    assert isinstance(brain_health["transport_profiles"], dict)
    assert brain_health["transport_profiles"]["legacy_reality_fallback"]["enabled"] is True
    assert brain_health["cpu_percent"] == 0.0  # legacy compatibility field remains numeric

    service = importlib.import_module("admin_ops_service")

    def reject_eager_history(*args, **kwargs):
        raise AssertionError("RU history must not be queried when include_ru_history=false")

    monkeypatch.setattr(service, "get_ru_run_history", reject_eager_history)
    current_only = client.get(
        "/api/admin/nodes/brain/observability?include_ru_history=false",
        headers=headers,
    )
    assert current_only.status_code == 200, current_only.text
    current_body = current_only.json()
    assert "history" not in current_body["ru"]
    assert current_body["sources"]["brain_metrics"]["status"] == "missing"
    assert current_body["sources"]["brain_metrics"]["sampled_at"] is None
    assert current_body["sources"]["brain_metrics"]["details"]["cpu_percent"] is None
    assert current_body["sources"]["brain_metrics"]["details"]["panel_error_rate"] is None
    assert current_body["sources"]["runtime"]["details"]["provisioned_clients_count"] is None
    assert current_body["sources"]["runtime"]["details"]["online_connections_hint"] is None
    assert current_body["capacity"]["provisioned_clients_count"] is None
    assert current_body["capacity"]["online_connections_hint"] is None

    panel_down = client.get(
        "/api/admin/nodes/panel-down/observability?include_ru_history=false",
        headers=headers,
    )
    assert panel_down.status_code == 200, panel_down.text
    panel_body = panel_down.json()
    assert panel_body["sources"]["runtime"]["status"] == "failed"
    assert panel_body["sources"]["runtime"]["reason_code"] == "runtime_panel_failed"
    assert panel_body["sources"]["runtime"]["sampled_at"]
    assert panel_body["sources"]["runtime"]["details"]["provisioned_clients_count"] is None
    assert panel_body["sources"]["runtime"]["details"]["online_connections_hint"] is None
    assert panel_body["sources"]["brain_metrics"]["status"] == "failed"
    assert panel_body["sources"]["brain_metrics"]["reason_code"] == "brain_panel_failed"
    assert panel_body["sources"]["brain_metrics"]["details"]["cpu_percent"] is None
    assert panel_body["capacity"]["provisioned_clients_count"] is None
    assert panel_body["capacity"]["online_connections_hint"] is None

    missing_node = client.get(
        "/api/admin/nodes/does-not-exist/observability",
        headers=headers,
    )
    assert missing_node.status_code == 404
    assert missing_node.json()["detail"] == "Node not found"

    invalid_cursor = client.get(
        "/api/admin/probes/ru-origin/runs?cursor=not-a-cursor",
        headers=headers,
    )
    assert invalid_cursor.status_code == 400
    assert invalid_cursor.json()["detail"] == "Invalid RU history cursor"


def test_admin_search_is_typed_bounded_and_never_echoes_key_or_email(
    monkeypatch, tmp_path
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import AccessKey, AccountDevice, ExternalOrder, User

    now = _utcnow()
    _seed_ops_fixture(api, now=now)
    s = api.SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == 1001).one()
        user.display_name = "Тестовый операторский поиск"
        user.app_install_id = "install-search-1001"
        user.email = "private-search@example.test"
        user.account_id = "00000000-0000-4000-8000-000000000301"
        s.add(
            AccountDevice(
                id="00000000-0000-4000-8000-000000000302",
                account_id=user.account_id,
                install_id="install-device-search",
                label="Windows",
                state="active",
                first_seen_at=now,
                last_seen_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        s.add(
            ExternalOrder(
                order_id="order-search-2026",
                tg_id=1001,
                provider="lavatop",
                plan_code="1_month",
                amount=990.0,
                currency="RUB",
                status="paid",
                meta_json='{"callback_body":"SYNTHETIC-SECRET-CALLBACK"}',
                created_at=now,
                paid_at=now,
            )
        )
        s.add(
            AccessKey(
                tg_id=1001,
                key_uuid="00000000-0000-4000-8000-000000000303",
                panel_email="private-key-search@example.test",
                node_code="de",
                pool_code="premium_pool",
                state="active",
                meta_json='{"subscription_url":"https://secret.invalid/token"}',
                created_at=now,
                updated_at=now,
            )
        )
        s.commit()
    finally:
        s.close()

    client = TestClient(api.app)
    headers = _admin_headers()
    queries = [
        "1001",
        "nearcap",
        "Тестовый операторский",
        "install-device-search",
        "order-search-2026",
        "de",
        "private-key-search@example.test",
    ]
    seen_kinds: set[str] = set()
    for query in queries:
        response = client.get(
            f"/api/admin/search?{urlencode({'q': query})}",
            headers=headers,
        )
        assert response.status_code == 200, response.text
        rows = response.json()["results"]
        assert len(rows) <= 20
        assert all(set(row) == {"kind", "id", "title", "subtitle", "href"} for row in rows)
        assert all(str(row["href"]).startswith("/") for row in rows)
        seen_kinds.update(str(row["kind"]) for row in rows)
        lower = response.text.lower()
        for forbidden in (
            "private-key-search@example.test",
            "00000000-0000-4000-8000-000000000303",
            "synthetic-secret-callback",
            "secret.invalid",
            "subscription_url",
            "callback_body",
        ):
            assert forbidden not in lower
    assert {"user", "order", "node", "key"}.issubset(seen_kinds)

    short = client.get("/api/admin/search?q=x", headers=headers)
    assert short.status_code == 400
    assert short.json()["detail"] == "Search query must contain at least 2 characters"

    for literal_wildcards in ("%%", "__", "%_", "de%"):
        response = client.get(
            f"/api/admin/search?{urlencode({'q': literal_wildcards})}",
            headers=headers,
        )
        assert response.status_code == 200, response.text
        assert response.json()["results"] == []


def test_ru_alert_candidates_use_server_freshness_and_received_heartbeat_facts(
    monkeypatch, tmp_path
) -> None:
    _load_api(monkeypatch, tmp_path)
    from admin_ops_service import build_alert_candidates

    candidates = build_alert_candidates(
        metrics_status={},
        provider_status=[],
        free_summary={},
        capacity_rows=[],
        ru_status={
            "status": "stale",
            "age_seconds": 7 * 60 * 60 + 1,
            "threshold_seconds": 7 * 60 * 60,
            "reason_code": "eligible_run_stale",
        },
        ru_uploader_status={
            "status": "stale",
            "age_seconds": 45 * 60 + 1,
            "threshold_seconds": 45 * 60,
            "reason_code": "uploader_heartbeat_stale",
            "heartbeat": {
                "pending_count": 3,
                "blocked_count": 1,
                "quarantine_count": 2,
                "archive_write_ok": False,
                "disk_state": "critical",
                "last_error_code": "archive_write_failed",
            },
        },
    )

    fingerprints = {row["fingerprint"] for row in candidates}
    assert {
        "ru_probe_run_stale",
        "ru_probe_uploader_heartbeat_stale",
        "ru_probe_uploader_backlog",
        "ru_probe_uploader_blocked",
        "ru_probe_uploader_quarantine",
        "ru_probe_uploader_archive",
        "ru_probe_uploader_disk",
    }.issubset(fingerprints)
    assert {row["source"] for row in candidates if row["fingerprint"].startswith("ru_probe")} == {
        "ru_probe"
    }

    no_heartbeat = build_alert_candidates(
        metrics_status={},
        provider_status=[],
        free_summary={},
        capacity_rows=[],
        ru_status={"status": "missing"},
        ru_uploader_status={"status": "missing", "heartbeat": None},
    )
    assert not {
        row["fingerprint"]
        for row in no_heartbeat
        if row["fingerprint"].startswith("ru_probe_uploader_")
        and row["fingerprint"] != "ru_probe_uploader_heartbeat_stale"
    }


def test_admin_action_intent_audit_helper_preserves_l1_wrapper_compatibility(
    monkeypatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import AdminAudit

    session = api.SessionLocal()
    try:
        rolled_back = api._add_admin_audit(
            session,
            actor_tg_id=9999,
            action="intent_atomic_probe",
            meta={"safe": True},
        )
        assert isinstance(rolled_back.id, int)
        session.rollback()
    finally:
        session.close()

    session = api.SessionLocal()
    try:
        assert session.query(AdminAudit).filter_by(action="intent_atomic_probe").count() == 0
        committed = api._add_admin_audit(
            session,
            actor_tg_id=9999,
            action="intent_atomic_commit",
            meta={"safe": True},
        )
        committed_id = int(committed.id)
        session.commit()
    finally:
        session.close()

    api._audit_admin(
        actor_tg_id=9999,
        action="legacy_l1_wrapper",
        meta={"safe": True},
    )
    session = api.SessionLocal()
    try:
        assert session.query(AdminAudit).filter_by(id=committed_id).count() == 1
        assert session.query(AdminAudit).filter_by(action="legacy_l1_wrapper").count() == 1
    finally:
        session.close()

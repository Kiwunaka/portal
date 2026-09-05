from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import importlib
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

import pytest
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


def _load_api(
    monkeypatch,
    tmp_path: Path,
    *,
    operator_session_secret: str = "admin-operator-session-secret-32-bytes-test",
    operator_environment: str = "test",
):
    db_path = tmp_path / "admin-ops-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "admin-ops-secret")
    monkeypatch.setenv("ADMIN_OPERATOR_SESSION_SECRET", operator_session_secret)
    monkeypatch.setenv("ADMIN_OPERATOR_ENVIRONMENT", operator_environment)
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
        "admin_v2",
        "admin_v2.meta",
        "admin_v2.roles",
        "admin_v2.router",
        "admin_v2.security",
        "admin_ops_service",
        "operator_network_service",
        "operator_money_actions",
        "operator_money_service",
        "operator_governance_actions",
        "operator_governance_service",
        "operator_growth_service",
        "operator_release_actions",
        "operator_release_service",
        "support_mode_service",
        "support_work_actions",
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
        "commercial_attribution_service",
        "commercial_offer_service",
        "commercial_order_service",
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
                reset_day=(now - timedelta(days=6)).day,
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
                "alert_confirmed": False,
            },
            {
                "code": "de",
                "enabled": True,
                "capacity_state": "hard_reject",
                "reject_reason": "unhealthy",
                "alert_confirmed": True,
                "alert_consecutive_samples": 3,
            },
        ],
    )

    fingerprints = {row["fingerprint"] for row in candidates}
    assert "node_capacity:brain" not in fingerprints
    assert "node_capacity:us" not in fingerprints
    assert fingerprints == {"node_capacity:pool"}
    assert candidates[0]["metadata"]["nodes"] == ["de"]


def test_node_metric_alerts_require_sustained_samples_without_snapshot_fallback(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from admin_ops_service import build_admin_metrics_status_snapshot
    from models import Node, NodeHealthSample

    now = _utcnow()
    s = api.SessionLocal()
    try:
        s.add(
            Node(
                code="de",
                name="DE",
                host="de.example.test",
                inbound_id=1,
                enabled=True,
                is_healthy=True,
                last_health_at=now,
                disk_used_gb=95,
                disk_total_gb=100,
            )
        )
        s.add(
            NodeHealthSample(
                node_code="de",
                sampled_at=now,
                disk_used_gb=95,
                disk_total_gb=100,
                is_healthy=True,
            )
        )
        s.flush()

        snapshot = build_admin_metrics_status_snapshot(s=s, now=now, stale_after_seconds=900)
        assert "disk_high" not in snapshot["nodes"][0]["alert_kinds"]

        s.add_all(
            [
                NodeHealthSample(
                    node_code="de",
                    sampled_at=now - timedelta(minutes=1),
                    disk_used_gb=94,
                    disk_total_gb=100,
                    is_healthy=True,
                ),
                NodeHealthSample(
                    node_code="de",
                    sampled_at=now - timedelta(minutes=2),
                    disk_used_gb=93,
                    disk_total_gb=100,
                    is_healthy=True,
                ),
            ]
        )
        s.flush()

        snapshot = build_admin_metrics_status_snapshot(s=s, now=now, stale_after_seconds=900)
        assert "disk_high" in snapshot["nodes"][0]["alert_kinds"]
    finally:
        s.close()


def test_error_rate_alert_does_not_linger_after_healthy_samples(monkeypatch, tmp_path) -> None:
    _load_api(monkeypatch, tmp_path)
    from admin_ops_service import _active_node_metric_alert_kinds
    from models import NodeHealthSample

    now = _utcnow()
    healthy_samples = [
        NodeHealthSample(
            node_code="it",
            sampled_at=now - timedelta(minutes=index),
            panel_error_rate=0.5,
            is_healthy=True,
        )
        for index in range(3)
    ]
    assert "error_rate_high" not in _active_node_metric_alert_kinds(
        samples=healthy_samples,
        last_sample_at=now,
        stale_after_seconds=900,
        now=now,
    )

    healthy_samples[1].is_healthy = False
    assert "error_rate_high" in _active_node_metric_alert_kinds(
        samples=healthy_samples,
        last_sample_at=now,
        stale_after_seconds=900,
        now=now,
    )


def test_capacity_hard_reject_alert_requires_three_runtime_samples(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from admin_ops_service import admin_nodes_capacity_payload, build_alert_candidates
    from models import Node, NodeRuntimeMetric

    now = _utcnow()
    s = api.SessionLocal()
    try:
        s.add(
            Node(
                code="us",
                name="US",
                host="us.example.test",
                inbound_id=1,
                enabled=True,
                accepting_new_clients=True,
                is_healthy=False,
                last_health_at=now,
            )
        )
        s.add_all(
            [
                NodeRuntimeMetric(
                    node_code="us",
                    sampled_at=now - timedelta(minutes=1),
                    capacity_state="healthy",
                ),
                NodeRuntimeMetric(
                    node_code="us",
                    sampled_at=now,
                    capacity_state="hard_reject",
                    reject_reason="unhealthy",
                ),
            ]
        )
        s.flush()

        capacity = admin_nodes_capacity_payload(s=s, now=now)
        row = capacity["nodes"][0]
        assert row["capacity_state"] == "hard_reject"
        assert row["alert_confirmed"] is False
        assert row["alert_consecutive_samples"] == 1
        assert not {
            candidate["fingerprint"]
            for candidate in build_alert_candidates(
                metrics_status={},
                provider_status=[],
                free_summary={},
                capacity_rows=capacity["nodes"],
            )
        }

        s.add_all(
            [
                NodeRuntimeMetric(
                    node_code="us",
                    sampled_at=now + timedelta(minutes=1),
                    capacity_state="hard_reject",
                    reject_reason="unhealthy",
                ),
                NodeRuntimeMetric(
                    node_code="us",
                    sampled_at=now + timedelta(minutes=2),
                    capacity_state="hard_reject",
                    reject_reason="unhealthy",
                ),
            ]
        )
        s.flush()

        capacity = admin_nodes_capacity_payload(s=s, now=now + timedelta(minutes=2))
        row = capacity["nodes"][0]
        assert row["alert_confirmed"] is True
        assert row["alert_consecutive_samples"] == 3
        candidates = build_alert_candidates(
            metrics_status={},
            provider_status=[],
            free_summary={},
            capacity_rows=capacity["nodes"],
        )
        assert {candidate["fingerprint"] for candidate in candidates} == {"node_capacity:pool"}
        assert "Маршрутизация временно ограничена" in candidates[0]["title"]
    finally:
        s.close()


def test_confirmed_capacity_alert_suppresses_duplicate_error_rate_alert(monkeypatch, tmp_path) -> None:
    _load_api(monkeypatch, tmp_path)
    from admin_ops_service import build_alert_candidates

    candidates = build_alert_candidates(
        metrics_status={
            "active_alerts": [
                {"node_code": "it", "kind": "error_rate_high", "age_seconds": 10},
                {"node_code": "it", "kind": "latency_high", "age_seconds": 10},
            ]
        },
        provider_status=[],
        free_summary={},
        capacity_rows=[
            {
                "code": "it",
                "enabled": True,
                "capacity_state": "hard_reject",
                "reject_reason": "unhealthy",
                "alert_confirmed": True,
                "alert_consecutive_samples": 3,
            }
        ],
    )

    fingerprints = {candidate["fingerprint"] for candidate in candidates}
    assert "node_metrics:it:error_rate_high" not in fingerprints
    assert "node_metrics:it:latency_high" not in fingerprints
    assert "node_capacity:pool" in fingerprints


def test_ops_alert_notifications_are_batched_in_russian_without_fingerprints(monkeypatch, tmp_path) -> None:
    _load_api(monkeypatch, tmp_path)
    from admin_ops_service import ops_alert_notification_batches

    batches = ops_alert_notification_batches(
        [
            {
                "kind": "active",
                "fingerprint": "node_metrics:nl:disk_high",
                "severity": "warning",
                "title": "Нода nl: заканчивается место на диске",
                "body": "Действие: проверить диск.",
            },
            {
                "kind": "active",
                "fingerprint": "node_capacity:pool",
                "severity": "warning",
                "title": "Маршрутизация временно ограничена на 2 нодах",
                "body": "Действие: проверить dataplane.",
            },
        ]
    )

    assert len(batches) == 1
    assert "нужна проверка" in batches[0]["text"]
    assert "Действие:" in batches[0]["text"]
    assert "node_metrics:" not in batches[0]["text"]
    assert "node_capacity:" not in batches[0]["text"]


def test_admin_ops_free_tier_provider_status_and_alerts(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("FREE_TOTAL_GB", "99")
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
    assert free_body["facts"]["enabled"] is False
    assert free_body["facts"]["status"] == "retired_pending_replacement"
    assert free_body["facts"]["node_pool"] is None
    assert free_body["facts"]["traffic_limit_bytes"] == 5 * 1024**3
    assert free_body["facts"]["standard_access_role"] == "free_standard"
    assert free_body["facts"]["soft_access_role"] == "free_soft"
    assert free_body["facts"]["soft_mode_speed_limit_mbps"] == 2

    free_users = client.get("/api/admin/free-tier/users", headers=headers)
    assert free_users.status_code == 200, free_users.text
    user_rows = free_users.json()["users"]
    states = {row["username"]: row["state"] for row in user_rows}
    assert states == {"overcap": "over_cap", "nearcap": "near_cap"}
    assert all(row["transition_state"] == "standard" for row in user_rows)
    assert all(row["active_role"] == "free_standard" for row in user_rows)
    assert all("provisioning_job_id" in row and "provisioning_error_code" in row for row in user_rows)

    quota_status = client.get("/api/admin/provider-quotas/status", headers=headers)
    assert quota_status.status_code == 200, quota_status.text
    de_status = next(row for row in quota_status.json()["nodes"] if row["node_code"] == "de")
    assert de_status["state"] == "critical"
    assert de_status["used_gb"] == 8.0
    assert de_status["remaining_gb"] == 2.0

    traffic = client.get("/api/admin/traffic/summary", headers=headers)
    assert traffic.status_code == 200, traffic.text
    assert {row["node_code"] for row in traffic.json()["rows"]} >= {"nl-free", "de"}

    alerts_refresh = client.get("/api/admin/alerts", headers=headers)
    assert alerts_refresh.status_code == 200, alerts_refresh.text

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
    assert ack.status_code == 428, ack.text
    assert ack.json()["detail"]["code"] == "intent_required"

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


def test_admin_v2_meta_is_guarded_and_reports_missing_identity_honestly(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("PORTAL_BUILD_COMMIT", raising=False)
    monkeypatch.delenv("GIT_COMMIT", raising=False)
    monkeypatch.delenv("PORTAL_DEPLOYED_AT", raising=False)
    monkeypatch.delenv("PORTAL_DB_SCHEMA", raising=False)
    monkeypatch.delenv("ACTIVE_CLIENT_RELEASE", raising=False)
    monkeypatch.delenv("ACTIVE_CORE_RELEASE", raising=False)
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app, base_url="https://api.pokrov.test")

    denied = client.get("/api/admin/v2/meta")
    assert denied.status_code == 401
    assert denied.json()["error"]["code"] == "operator_session_missing"

    bootstrap = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert bootstrap.status_code == 200, bootstrap.text
    bootstrap_body = bootstrap.json()
    assert bootstrap_body["data"]["token_transport"] == "http_only_cookie"
    assert "token" not in bootstrap_body["data"]
    assert "__Host-pokrov_admin_session=" in bootstrap.headers["set-cookie"]
    assert "HttpOnly" in bootstrap.headers["set-cookie"]
    assert "Secure" in bootstrap.headers["set-cookie"]
    assert "SameSite=strict" in bootstrap.headers["set-cookie"]

    response = client.get(
        "/api/admin/v2/meta",
        headers={"X-Correlation-Id": "operator-meta-test"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data"] == {
        "app": "pokrov-operator-api",
        "api_schema": "admin-v2.1",
        "portal_commit": None,
        "deployed_at": None,
        "db_schema": None,
        "active_client_release": None,
        "core_release": None,
        "expected_frontend_app": "pokrov-operator-center",
    }
    assert body["meta"]["schema_version"] == "admin-v2.1"
    assert body["meta"]["trace_id"] == response.headers["X-Correlation-ID"]
    assert body["meta"]["trace_id"] != "operator-meta-test"
    assert body["sources"] == []
    assert {item["field"] for item in body["warnings"]} == {
        "portal_commit",
        "deployed_at",
        "db_schema",
        "active_client_release",
        "core_release",
    }
    money_blocked = client.get("/api/admin/v2/money/payments/summary")
    assert money_blocked.status_code == 409, money_blocked.text
    assert money_blocked.json()["error"]["code"] == "money_environment_unavailable"


def test_admin_v2_meta_exposes_exact_configured_deployment_identity(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("PORTAL_BUILD_COMMIT", "a" * 40)
    monkeypatch.setenv("PORTAL_DEPLOYED_AT", "2026-08-21T12:00:00Z")
    monkeypatch.setenv("PORTAL_DB_SCHEMA", "portal-2026-08-21")
    monkeypatch.setenv("ACTIVE_CLIENT_RELEASE", "1.2.0-rc.1")
    monkeypatch.setenv("ACTIVE_CORE_RELEASE", "1.2.0-rc.1")
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app, base_url="https://api.pokrov.test")

    bootstrap = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert bootstrap.status_code == 200, bootstrap.text
    response = client.get("/api/admin/v2/meta")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data"]["portal_commit"] == "a" * 40
    assert body["data"]["deployed_at"] == "2026-08-21T12:00:00Z"
    assert body["data"]["db_schema"] == "portal-2026-08-21"
    assert body["data"]["active_client_release"] == "1.2.0-rc.1"
    assert body["data"]["core_release"] == "1.2.0-rc.1"
    assert body["warnings"] == []


def test_admin_v2_operator_session_rbac_csrf_step_up_revoke_and_audit(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app, base_url="https://api.pokrov.test")

    first = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert first.status_code == 200, first.text
    first_body = first.json()["data"]
    first_session_id = first_body["session"]["id"]
    assert first_body["operator"]["roles"] == ["superadmin"]
    assert "system.meta.read" in first_body["operator"]["permissions"]
    assert "legacy.admin.access" in first_body["operator"]["permissions"]

    second = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert second.status_code == 200, second.text
    second_body = second.json()["data"]
    current_session_id = second_body["session"]["id"]
    csrf = second_body["session"]["csrf_token"]
    assert first_session_id != current_session_id

    me = client.get("/api/admin/v2/auth/me")
    assert me.status_code == 200, me.text
    assert me.json()["data"]["session"]["csrf_token"] == csrf

    inventory = client.get("/api/admin/v2/auth/sessions")
    assert inventory.status_code == 200, inventory.text
    assert inventory.json()["data"]["count"] == 2
    assert sum(1 for row in inventory.json()["data"]["items"] if row["current"]) == 1

    missing_csrf = client.post(f"/api/admin/v2/auth/sessions/{first_session_id}/revoke")
    assert missing_csrf.status_code == 403
    assert missing_csrf.json()["error"]["code"] == "operator_csrf_invalid"

    revoked = client.post(
        f"/api/admin/v2/auth/sessions/{first_session_id}/revoke",
        headers={"X-Pokrov-Admin-CSRF": csrf},
    )
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["data"] == {
        "session_id": first_session_id,
        "revoked": True,
        "current": False,
    }

    step_up = client.post(
        "/api/admin/v2/auth/step-up",
        headers={**_admin_headers(), "X-Pokrov-Admin-CSRF": csrf},
    )
    assert step_up.status_code == 200, step_up.text
    assert step_up.json()["data"]["method"] == "legacy_admin_reverified"
    assert step_up.json()["warnings"][0]["code"] == "compatibility_step_up"

    legacy_bridge = client.post("/api/admin/auth/session")
    assert legacy_bridge.status_code == 403
    assert legacy_bridge.headers["X-POKROV-Auth-Error"] == "operator_csrf_invalid"

    from models import AdminOperator, AdminOperatorAudit, AdminOperatorRole, AdminOperatorSession

    db = api.SessionLocal()
    try:
        operator = db.query(AdminOperator).one()
        role = db.query(AdminOperatorRole).one()
        sessions = db.query(AdminOperatorSession).order_by(AdminOperatorSession.created_at.asc()).all()
        audits = db.query(AdminOperatorAudit).order_by(AdminOperatorAudit.created_at.asc()).all()
        assert operator.legacy_actor_tg_id == 9999
        assert role.role_code == "superadmin"
        assert role.environment_scope == "test"
        assert len(sessions) == 2
        assert all(len(row.token_hash) == 64 for row in sessions)
        assert sessions[0].revoked_at is not None
        assert sessions[1].step_up_at is not None
        assert {row.action for row in audits} >= {
            "session.bootstrap",
            "session.revoke",
            "session.step_up",
        }
        for row in audits:
            assert json.loads(row.roles_json) == ["superadmin"]
            assert "system.meta.read" in json.loads(row.permissions_json)
    finally:
        db.close()

    logout = client.post(
        "/api/admin/v2/auth/logout",
        headers={"X-Pokrov-Admin-CSRF": csrf},
    )
    assert logout.status_code == 200, logout.text
    assert logout.headers["Clear-Site-Data"] == '"cookies", "storage"'
    after_logout = client.get("/api/admin/v2/meta")
    assert after_logout.status_code == 401


def test_admin_v2_oidc_login_and_step_up_are_cookie_bound_and_require_provisioned_operator(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("TELEGRAM_OAUTH_CLIENT_ID", "777000")
    monkeypatch.setenv("TELEGRAM_OAUTH_CLIENT_SECRET", "telegram-oidc-test-secret")
    monkeypatch.setenv("ADMIN_OPERATOR_OIDC_REDIRECT_URI", "https://admin.pokrov.test/")
    monkeypatch.setenv("ADMIN_OPERATOR_LEGACY_BOOTSTRAP_ENABLED", "false")
    api = _load_api(monkeypatch, tmp_path)

    from models import AdminOperator, AdminOperatorAudit, AdminOperatorRole

    operator_id = str(uuid.uuid4())
    db = api.SessionLocal()
    try:
        db.add(
            AdminOperator(
                id=operator_id,
                legacy_actor_tg_id=9999,
                display_name="owner",
                identity_source="legacy_bootstrap",
                status="active",
            )
        )
        db.add(
            AdminOperatorRole(
                id=str(uuid.uuid4()),
                operator_id=operator_id,
                role_code="superadmin",
                environment_scope="test",
            )
        )
        db.commit()
    finally:
        db.close()

    client = TestClient(api.app, base_url="https://api.pokrov.test")
    legacy = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert legacy.status_code == 403
    assert legacy.json()["error"]["code"] == "operator_legacy_bootstrap_disabled"

    import admin_v2.router as admin_v2_router
    import web_auth_service

    exchanges: list[str] = []

    async def fake_exchange(
        *,
        code: str,
        state_token: str,
        expected_purpose: str | None = None,
        transaction_token: str | None = None,
        state_signing_secret: str | None = None,
    ) -> dict[str, object]:
        assert code in {"oidc-login-code", "oidc-step-up-code"}
        assert transaction_token
        assert state_signing_secret == "admin-operator-session-secret-32-bytes-test"
        public = web_auth_service.verify_telegram_oidc_state_token(
            state_token,
            expected_purpose=expected_purpose,
            require_code_verifier=False,
            signing_secret=state_signing_secret,
        )
        private = web_auth_service.verify_telegram_oidc_state_token(
            transaction_token,
            expected_purpose=expected_purpose,
            signing_secret=state_signing_secret,
        )
        assert public and private
        assert public["code_verifier"] == ""
        assert len(private["code_verifier"]) >= 43
        assert public["csrf"] == private["csrf"]
        exchanges.append(str(expected_purpose))
        return {"id": 9999, "preferred_username": "owner"}

    monkeypatch.setattr(admin_v2_router, "exchange_telegram_oidc_code", fake_exchange)

    start = client.get("/api/admin/v2/auth/oidc/start?mode=login")
    assert start.status_code == 200, start.text
    start_data = start.json()["data"]
    assert start_data["provider"] == "telegram_oidc"
    assert start_data["redirect_uri"] == "https://admin.pokrov.test/"
    assert start_data["auth_url"].startswith("https://oauth.telegram.org/auth?")
    state = web_auth_service.verify_telegram_oidc_state_token(
        start_data["auth_url"].split("state=", 1)[1].split("&", 1)[0],
        expected_purpose="admin_operator_login",
        require_code_verifier=False,
        signing_secret="admin-operator-session-secret-32-bytes-test",
    )
    assert state is not None
    assert state["code_verifier"] == ""

    from urllib.parse import parse_qs, urlsplit

    public_state = parse_qs(urlsplit(start_data["auth_url"]).query)["state"][0]
    finish = client.post(
        "/api/admin/v2/auth/oidc/finish",
        json={"code": "oidc-login-code", "state": public_state},
    )
    assert finish.status_code == 200, finish.text
    identity = finish.json()["data"]
    assert identity["identity_method"] == "telegram_oidc"
    assert identity["token_transport"] == "http_only_cookie"
    assert "token" not in identity
    assert "__Host-pokrov_admin_session=" in finish.headers["set-cookie"]
    csrf = identity["session"]["csrf_token"]

    step_start = client.get("/api/admin/v2/auth/oidc/start?mode=step_up")
    assert step_start.status_code == 200, step_start.text
    step_state = parse_qs(urlsplit(step_start.json()["data"]["auth_url"]).query)["state"][0]
    stepped = client.post(
        "/api/admin/v2/auth/step-up",
        headers={"X-Pokrov-Admin-CSRF": csrf},
        json={"code": "oidc-step-up-code", "state": step_state},
    )
    assert stepped.status_code == 200, stepped.text
    assert stepped.json()["data"]["method"] == "telegram_oidc"
    assert stepped.json()["warnings"] == []
    assert exchanges == ["admin_operator_login", "admin_operator_step_up"]

    compatibility_step_up = client.post(
        "/api/admin/v2/auth/step-up",
        headers={"X-Pokrov-Admin-CSRF": csrf, **_admin_headers()},
    )
    assert compatibility_step_up.status_code == 403
    assert compatibility_step_up.json()["error"]["code"] == "operator_legacy_step_up_disabled"

    db = api.SessionLocal()
    try:
        operator = db.query(AdminOperator).filter(AdminOperator.id == operator_id).one()
        audits = db.query(AdminOperatorAudit).order_by(AdminOperatorAudit.created_at.asc()).all()
        assert operator.identity_source == "telegram_oidc"
        assert [(row.action, row.reason_code) for row in audits] == [
            ("session.oidc", "telegram_oidc_verified"),
            ("session.step_up", "telegram_oidc_verified"),
        ]
    finally:
        db.close()


def test_admin_v2_governance_roles_jit_audit_lineage_and_privacy(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app, base_url="https://api.pokrov.test")
    bootstrap = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert bootstrap.status_code == 200, bootstrap.text
    admin_data = bootstrap.json()["data"]
    admin_operator_id = admin_data["operator"]["id"]
    csrf = admin_data["session"]["csrf_token"]
    unsafe = {"X-Pokrov-Admin-CSRF": csrf}

    from models import (
        AdminOperator,
        AdminOperatorAudit,
        AdminOperatorRole,
        SupportBundleAccessAudit,
    )

    target_id = str(uuid.uuid4())
    isolated_operator_id = str(uuid.uuid4())
    db = api.SessionLocal()
    try:
        db.add(
            AdminOperator(
                id=target_id,
                legacy_actor_tg_id=8888,
                display_name="support-operator",
                identity_source="test_fixture",
                status="active",
                created_at=_utcnow(),
                updated_at=_utcnow(),
            )
        )
        db.add(
            AdminOperatorRole(
                id=str(uuid.uuid4()),
                operator_id=target_id,
                role_code="readonly",
                environment_scope="test",
                granted_by_operator_id=admin_operator_id,
                granted_at=_utcnow(),
            )
        )
        db.add(
            AdminOperator(
                id=isolated_operator_id,
                legacy_actor_tg_id=7777,
                display_name="other-environment-operator",
                identity_source="test_fixture",
                status="active",
                created_at=_utcnow(),
                updated_at=_utcnow(),
            )
        )
        db.add(
            SupportBundleAccessAudit(
                grant_id=str(uuid.uuid4()),
                upload_id=str(uuid.uuid4()),
                ticket_id=321,
                actor_tg_id=9999,
                actor_role="support_l2",
                action="download",
                reason_code="ticket_diagnosis",
                expires_at=_utcnow() + timedelta(minutes=15),
                retention_hold=False,
                created_at=_utcnow(),
            )
        )
        db.commit()
    finally:
        db.close()

    roles = client.get("/api/admin/v2/governance/roles")
    assert roles.status_code == 200, roles.text
    assert {row["code"] for row in roles.json()["data"]["roles"]} >= {
        "superadmin",
        "security_auditor",
        "network_operator",
    }
    assert roles.json()["data"]["rules"]["self_role_change"] == "denied"

    operators = client.get("/api/admin/v2/governance/operators?role=readonly")
    assert operators.status_code == 200, operators.text
    assert operators.json()["data"]["items"][0]["id"] == target_id
    all_operators = client.get("/api/admin/v2/governance/operators?limit=200")
    assert all_operators.status_code == 200, all_operators.text
    assert isolated_operator_id not in {
        row["id"] for row in all_operators.json()["data"]["items"]
    }
    detail = client.get(f"/api/admin/v2/governance/operators/{target_id}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["data"]["operator"]["display_name"] == "support-operator"
    assert all("token_hash" not in row for row in detail.json()["data"]["sessions"])

    no_step_up = client.post(
        "/api/admin/v2/governance/action-intents",
        headers=unsafe,
        json={
            "action": "operator.role.grant",
            "target": {"type": "operator", "id": target_id},
            "payload": {
                "role_code": "network_operator",
                "grant_kind": "jit",
                "expires_at": (_utcnow() + timedelta(minutes=30)).isoformat() + "Z",
                "reason": "Temporary incident response coverage",
            },
        },
    )
    assert no_step_up.status_code == 403
    assert no_step_up.json()["error"]["code"] == "operator_step_up_required"

    stepped = client.post(
        "/api/admin/v2/auth/step-up",
        headers={**unsafe, **_admin_headers()},
    )
    assert stepped.status_code == 200, stepped.text

    command = {
        "action": "operator.role.grant",
        "target": {"type": "operator", "id": target_id},
        "payload": {
            "role_code": "network_operator",
            "grant_kind": "jit",
            "expires_at": (_utcnow() + timedelta(minutes=30)).isoformat() + "Z",
            "reason": "Temporary incident response coverage",
        },
    }
    prepared = client.post(
        "/api/admin/v2/governance/action-intents",
        headers=unsafe,
        json=command,
    )
    assert prepared.status_code == 200, prepared.text
    intent = prepared.json()["data"]
    assert intent["risk_level"] == "L3"
    assert intent["confirmation_challenge"] == target_id
    executed = client.post(
        f"/api/admin/v2/governance/action-intents/{intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": str(uuid.uuid4()),
            "X-Admin-Confirmation-SHA256": hashlib.sha256(target_id.encode("utf-8")).hexdigest(),
        },
        json=command,
    )
    assert executed.status_code == 200, executed.text
    granted = executed.json()["data"]["role"]
    assert granted["grant_kind"] == "jit"
    assert granted["review_status"] == "pending_review"
    assert granted["active"] is True

    self_grant = client.post(
        "/api/admin/v2/governance/action-intents",
        headers=unsafe,
        json={
            "action": "operator.role.grant",
            "target": {"type": "operator", "id": admin_operator_id},
            "payload": {
                "role_code": "readonly",
                "grant_kind": "standing",
                "reason": "Attempted self role assignment",
            },
        },
    )
    assert self_grant.status_code == 409
    assert self_grant.json()["error"]["code"] == "self_governance_denied"

    lineage = client.get(
        f"/api/admin/v2/governance/audit/commands/{intent['intent_id']}"
    )
    assert lineage.status_code == 200, lineage.text
    lineage_data = lineage.json()["data"]
    assert lineage_data["intent"]["payload_hash"] == intent["payload_hash"]
    assert lineage_data["legacy_audit"]["id"] == executed.json()["data"]["audit_id"]
    assert lineage_data["operator_audits"][0]["session_id"] == admin_data["session"]["id"]
    from operator_governance_service import audit_export_csv, command_lineage

    protected_csv = audit_export_csv(
        {
            "items": [
                {
                    "id": "audit-formula-test",
                    "operator_name": "=WEBSERVICE(\"https://invalid.test\")",
                    "roles": [],
                    "permissions": [],
                    "resource": None,
                }
            ]
        }
    )
    assert "'=WEBSERVICE" in protected_csv

    db = api.SessionLocal()
    try:
        assert command_lineage(db, intent_id=intent["intent_id"], environment="production") is None
    finally:
        db.close()

    audit = client.get(
        f"/api/admin/v2/governance/audit?command_intent_id={intent['intent_id']}"
    )
    assert audit.status_code == 200, audit.text
    assert audit.json()["data"]["items"][0]["resource"] == {
        "type": "operator",
        "id": target_id,
    }
    exported = client.get(
        f"/api/admin/v2/governance/audit/export?command_intent_id={intent['intent_id']}"
    )
    assert exported.status_code == 200, exported.text
    assert "text/csv" in exported.headers["content-type"]
    assert intent["intent_id"] in exported.text

    review_command = {
        "action": "operator.access.review",
        "target": {"type": "operator_role", "id": granted["id"]},
        "payload": {"note": "Reviewed incident scope and observed usage"},
    }
    review_prepared = client.post(
        "/api/admin/v2/governance/action-intents",
        headers=unsafe,
        json=review_command,
    )
    assert review_prepared.status_code == 200, review_prepared.text
    review_intent = review_prepared.json()["data"]
    reviewed = client.post(
        f"/api/admin/v2/governance/action-intents/{review_intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": str(uuid.uuid4()),
            "X-Admin-Confirmation-SHA256": hashlib.sha256("ПОДТВЕРДИТЬ".encode("utf-8")).hexdigest(),
        },
        json=review_command,
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["data"]["role"]["review_status"] == "reviewed"

    sensitive = client.get("/api/admin/v2/governance/sensitive-access?ticket_id=321")
    assert sensitive.status_code == 200, sensitive.text
    assert sensitive.json()["data"]["items"][0]["action"] == "download"
    assert "access_token_hash" not in sensitive.json()["data"]["items"][0]
    assert sensitive.json()["data"]["source_scope"] == "global_legacy_support_bundle_authority"

    privacy = client.get("/api/admin/v2/governance/privacy")
    assert privacy.status_code == 200, privacy.text
    privacy_data = privacy.json()["data"]
    assert privacy_data["raw_policy"]["default_days"] == 90
    assert next(row for row in privacy_data["retention"] if row["code"] == "events")["raw_retention_days"] == 90
    assert privacy_data["deletion_anonymization"]["policy"]["raw_ip_hours"] == 72
    assert set(privacy_data["deletion_anonymization"]["backlog"]) == {
        "antiabuse_raw_ip",
        "antiabuse_full_hmac",
        "antiabuse_prefix_hmac",
        "security_event_ip",
        "user_last_ip",
    }
    assert privacy_data["diagnostic_bundles"]["expired_unheld_backlog"] == 0
    session_fields = next(row for row in privacy_data["field_inventory"] if row["family"] == "operator_session")
    assert session_fields["excluded"] == ["token", "token_hash", "csrf"]

    db = api.SessionLocal()
    try:
        read_audits = (
            db.query(AdminOperatorAudit)
            .filter(
                AdminOperatorAudit.action.in_(
                    ["governance.audit.export", "governance.sensitive_access.read"]
                )
            )
            .order_by(AdminOperatorAudit.created_at.asc())
            .all()
        )
        assert [row.action for row in read_audits] == [
            "governance.audit.export",
            "governance.sensitive_access.read",
        ]
        assert all(row.result == "success" for row in read_audits)
        assert all("token" not in str(row.details_json or "").lower() for row in read_audits)
    finally:
        db.close()


def test_admin_v2_network_reads_and_node_action_use_permissioned_boundary(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app, base_url="https://api.pokrov.test")
    bootstrap = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert bootstrap.status_code == 200, bootstrap.text
    csrf = bootstrap.json()["data"]["session"]["csrf_token"]
    unsafe = {"X-Pokrov-Admin-CSRF": csrf}

    from models import Node, OpsAlert

    db = api.SessionLocal()
    try:
        db.add(
            Node(
                code="nl-v2",
                name="NL v2",
                host="nl-v2.example.com",
                enabled=True,
                accepting_new_clients=True,
                is_draining=False,
                is_healthy=True,
                health_score=1.0,
                transport_profiles_json=json.dumps(
                    [{"name": "legacy_reality_fallback", "enabled": True}]
                ),
            )
        )
        alert = OpsAlert(
            fingerprint="network-v2-silence-alert",
            source="node_metrics",
            severity="warning",
            status="active",
            title="Network v2 silence test",
            environment="test",
            first_seen_at=_utcnow(),
            last_seen_at=_utcnow(),
            created_at=_utcnow(),
            updated_at=_utcnow(),
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        alert_id = int(alert.id)
        alert_version = int(alert.version)
    finally:
        db.close()

    fleet = client.get("/api/admin/v2/network/fleet")
    assert fleet.status_code == 200, fleet.text
    assert fleet.json()["data"]["items"][0]["code"] == "nl-v2"
    assert fleet.json()["sources"][0]["authority"] == "nodes"

    detail = client.get("/api/admin/v2/network/nodes/nl-v2")
    assert detail.status_code == 200, detail.text
    assert detail.json()["data"]["lifecycle"]["enabled"] is True

    providers = client.get("/api/admin/v2/network/providers")
    assert providers.status_code == 200, providers.text
    assert providers.json()["data"]["statuses"][0]["node_code"] == "nl-v2"

    alerts = client.get("/api/admin/v2/network/alerts?status=active")
    assert alerts.status_code == 200, alerts.text
    assert [row["id"] for row in alerts.json()["data"]["items"]] == [alert_id]

    command = {
        "action": "node.drain",
        "target": {"type": "node", "id": "nl-v2"},
        "payload": {"force": False},
    }
    prepared = client.post(
        "/api/admin/v2/network/action-intents", headers=unsafe, json=command
    )
    assert prepared.status_code == 200, prepared.text
    intent = prepared.json()["data"]
    executed = client.post(
        f"/api/admin/v2/network/action-intents/{intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": str(uuid.uuid4()),
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                intent["confirmation_challenge"].encode("utf-8")
            ).hexdigest(),
        },
        json=command,
    )
    assert executed.status_code == 200, executed.text
    assert executed.json()["data"]["node"]["is_draining"] is True

    db = api.SessionLocal()
    try:
        row = db.query(Node).filter(Node.code == "nl-v2").one()
        assert row.accepting_new_clients is False
        assert row.is_draining is True
    finally:
        db.close()

    silence_command = {
        "action": "alert.silence",
        "target": {"type": "alert", "id": str(alert_id)},
        "payload": {"expected_version": alert_version, "minutes": 60},
    }
    prepared = client.post(
        "/api/admin/v2/network/action-intents", headers=unsafe, json=silence_command
    )
    assert prepared.status_code == 200, prepared.text
    silence_intent = prepared.json()["data"]
    silenced = client.post(
        f"/api/admin/v2/network/action-intents/{silence_intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": str(uuid.uuid4()),
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                silence_intent["confirmation_challenge"].encode("utf-8")
            ).hexdigest(),
        },
        json=silence_command,
    )
    assert silenced.status_code == 200, silenced.text
    assert silenced.json()["data"]["alert_status"] == "silenced"

    db = api.SessionLocal()
    try:
        row = db.query(OpsAlert).filter(OpsAlert.id == alert_id).one()
        assert row.silence_until is not None
        assert int(row.version) == alert_version + 1
        node = db.query(Node).filter(Node.code == "nl-v2").one()
        node.host = "not a valid host"
        db.commit()
    finally:
        db.close()

    invalid_ru = client.get("/api/admin/v2/network/ru/latest")
    assert invalid_ru.status_code == 503, invalid_ru.text
    assert invalid_ru.json()["error"]["code"] == "ru_configuration_invalid"


def test_admin_v2_money_lineage_and_program_review_use_single_intent_boundary(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path, operator_environment="production")
    client = TestClient(api.app, base_url="https://api.pokrov.test")
    bootstrap = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert bootstrap.status_code == 200, bootstrap.text
    csrf = bootstrap.json()["data"]["session"]["csrf_token"]
    unsafe = {"X-Pokrov-Admin-CSRF": csrf}

    from models import (
        Account,
        EntitlementGrant,
        ExternalOrder,
        ExternalPaymentEvent,
        GiftCard,
        PaymentEntitlementClaim,
        PaymentEntitlementOutbox,
        ProgramApplication,
        PromoCode,
        User,
    )

    now = _utcnow()
    account_id = str(uuid.uuid4())
    free_account_id = str(uuid.uuid4())
    grant_id = str(uuid.uuid4())
    application_id = str(uuid.uuid4())
    db = api.SessionLocal()
    try:
        db.add(Account(id=account_id, status="active", created_source="test"))
        db.add(Account(id=free_account_id, status="active", created_source="test"))
        db.add(
            User(
                tg_id=4301,
                account_id=account_id,
                username="money_user",
                display_name="Money User",
                sub_type="PAID",
                current_plan_code="start_99",
                expiry_at=now + timedelta(days=30),
                is_active=True,
            )
        )
        db.add(
            User(
                tg_id=4302,
                account_id=free_account_id,
                username="legacy_free_user",
                display_name="Legacy Free User",
                sub_type="FREE",
                is_active=True,
            )
        )
        order = ExternalOrder(
            order_id="money-v2-order",
            provider="freekassa",
            tg_id=4301,
            plan_code="start_99",
            amount=99,
            currency="RUB",
            status="paid",
            created_at=now - timedelta(minutes=12),
            paid_at=now - timedelta(minutes=10),
            meta_json='{"provider_token":"RAW-ORDER-SECRET"}',
        )
        db.add(order)
        db.flush()
        order_db_id = int(order.id)
        db.add(
            ExternalPaymentEvent(
                provider="freekassa",
                event_type="result",
                external_id="provider-event-secret-id",
                order_id="money-v2-order",
                payload_json='{"token":"RAW-CALLBACK-SECRET"}',
                signature_ok=True,
                processed_ok=False,
            )
        )
        claim = PaymentEntitlementClaim(
            provider="freekassa",
            order_id="money-v2-order",
            buyer_email_norm="private@example.test",
            account_id=account_id,
            status="paid_attached",
            plan_code="start_99",
            duration_days=30,
            grant_id=grant_id,
            paid_at=now - timedelta(minutes=10),
            last_error="RAW-CLAIM-DETAIL",
        )
        db.add(claim)
        db.add(
            EntitlementGrant(
                id=grant_id,
                account_id=account_id,
                legacy_tg_id=4301,
                idempotency_key="money-v2-grant",
                source="payment_callback",
                status="reserved",
                grant_kind="paid_access",
                plan_code="start_99",
                provider="freekassa",
                external_order_id="money-v2-order",
                metadata_json='{"token":"RAW-GRANT-SECRET"}',
            )
        )
        db.flush()
        db.add(
            PaymentEntitlementOutbox(
                id=str(uuid.uuid4()),
                idempotency_key="money-v2-outbox",
                aggregate_id=str(claim.id),
                payload_json='{"secret":"RAW-OUTBOX-SECRET"}',
                status="pending",
                next_run_at=now,
            )
        )
        db.add(GiftCard(code="GIFT-RAW-SECRET-123", card_type="mini", created_by=9999))
        db.add(PromoCode(code="V2PROMO", promo_type="days", value=3, uses_left=10))
        db.add(
            ProgramApplication(
                id=application_id,
                account_id=account_id,
                legacy_tg_id=4301,
                kind="research",
                status="submitted",
                summary="Bounded research application",
                contact="private-contact@example.test",
            )
        )
        db.commit()
    finally:
        db.close()

    summary = client.get("/api/admin/v2/money/payments/summary?period=7d")
    assert summary.status_code == 200, summary.text
    mismatch_queues = summary.json()["data"]["mismatch_queues"]
    assert mismatch_queues.get("paid_without_entitlement") == 1, summary.json()
    assert mismatch_queues.get("callback_failed") == 1, summary.json()
    assert summary.json()["sources"][0]["authority"] == "external_orders"

    orders = client.get("/api/admin/v2/money/payments/orders?status=paid&provider=freekassa")
    assert orders.status_code == 200, orders.text
    assert orders.json()["data"]["total"] == 1
    assert orders.json()["data"]["orders"][0]["order_id"] == "money-v2-order"

    detail = client.get("/api/admin/v2/money/payments/orders/freekassa/money-v2-order")
    assert detail.status_code == 200, detail.text
    detail_text = json.dumps(detail.json(), ensure_ascii=False)
    for secret in (
        "RAW-ORDER-SECRET",
        "RAW-CALLBACK-SECRET",
        "RAW-CLAIM-DETAIL",
        "RAW-GRANT-SECRET",
        "RAW-OUTBOX-SECRET",
        "private@example.test",
        "provider-event-secret-id",
    ):
        assert secret not in detail_text
    assert detail.json()["data"]["lineage"]["claim"]["status"] == "paid_attached"
    assert detail.json()["data"]["lineage"]["grant"]["status"] == "reserved"

    access = client.get("/api/admin/v2/money/access")
    assert access.status_code == 200, access.text
    access_text = json.dumps(access.json(), ensure_ascii=False)
    assert "GIFT-RAW-SECRET-123" not in access_text
    assert access.json()["data"]["authority"]["telemetry_confirms_payment"] is False

    free_archive = client.get("/api/admin/v2/money/free-archive?q=legacy_free")
    assert free_archive.status_code == 200, free_archive.text
    assert free_archive.json()["data"]["total"] == 1
    assert free_archive.json()["data"]["users"][0]["username"] == "legacy_free_user"

    promos = client.get("/api/admin/v2/money/promos")
    assert promos.status_code == 200, promos.text
    assert promos.json()["data"]["promos"][0]["code"] == "V2PROMO"

    bonuses = client.get("/api/admin/v2/growth/bonuses")
    assert bonuses.status_code == 200, bonuses.text
    assert bonuses.json()["data"]["wheel"]["preset"] == "paid_fortnightly_v3"
    assert bonuses.json()["data"]["loyalty"]["enabled"] is True

    programs = client.get("/api/admin/v2/growth/programs?status=submitted")
    assert programs.status_code == 200, programs.text
    assert programs.json()["data"]["applications"][0]["account_ref"].startswith("account_")
    assert "account_id" not in programs.json()["data"]["applications"][0]

    step_up = client.post(
        "/api/admin/v2/auth/step-up",
        headers={**_admin_headers(), **unsafe},
    )
    assert step_up.status_code == 200, step_up.text
    review_command = {
        "action": "program_application.review",
        "target": {"type": "program_application", "id": application_id},
        "payload": {"status": "approved", "operator_note": "Evidence reviewed", "reward_days": 3},
    }
    prepared = client.post(
        "/api/admin/v2/growth/action-intents",
        headers=unsafe,
        json=review_command,
    )
    assert prepared.status_code == 200, prepared.text
    intent = prepared.json()["data"]
    assert intent["risk_level"] == "L3"
    assert intent["confirmation_challenge"] == application_id
    executed = client.post(
        f"/api/admin/v2/growth/action-intents/{intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": str(uuid.uuid4()),
            "X-Admin-Confirmation-SHA256": hashlib.sha256(application_id.encode("utf-8")).hexdigest(),
        },
        json=review_command,
    )
    assert executed.status_code == 200, executed.text
    assert executed.json()["data"]["application"]["status"] == "rewarded"

    db = api.SessionLocal()
    try:
        application = db.query(ProgramApplication).filter_by(id=application_id).one()
        assert application.status == "rewarded"
        assert application.reward_days == 3
        assert application.reward_grant_id
        reward_grant = (
            db.query(EntitlementGrant)
            .filter(EntitlementGrant.id == application.reward_grant_id)
            .one()
        )
        assert reward_grant.account_id == account_id
        assert reward_grant.idempotency_key == f"program-application:v1:{application_id}"
    finally:
        db.close()


def test_admin_v2_shift_incident_and_alert_lifecycle_use_action_intents(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app, base_url="https://api.pokrov.test")
    bootstrap = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert bootstrap.status_code == 200, bootstrap.text
    identity = bootstrap.json()["data"]
    csrf = identity["session"]["csrf_token"]
    operator_id = identity["operator"]["id"]
    unsafe = {"X-Pokrov-Admin-CSRF": csrf}

    task_id = str(uuid.uuid4())
    task_command = {
        "action": "operator_task.create",
        "target": {"type": "operator_task", "id": task_id},
        "payload": {
            "title": "Проверить отказавшую команду",
            "owner_operator_id": operator_id,
            "owner_team": "superadmin",
            "priority": "high",
            "next_action": "Сверить audit trail",
            "source": "failed_command",
            "linked_entity_type": "command",
            "linked_entity_id": "cmd-42",
        },
    }
    prepared = client.post(
        "/api/admin/v2/shift/action-intents",
        headers=unsafe,
        json=task_command,
    )
    assert prepared.status_code == 200, prepared.text
    task_intent = prepared.json()["data"]
    task_execute = client.post(
        f"/api/admin/v2/shift/action-intents/{task_intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": "11111111-1111-4111-8111-111111111111",
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                task_intent["confirmation_challenge"].encode("utf-8")
            ).hexdigest(),
        },
        json=task_command,
    )
    assert task_execute.status_code == 200, task_execute.text
    assert task_execute.json()["data"]["task_id"] == task_id

    shift = client.get("/api/admin/v2/shift")
    assert shift.status_code == 200, shift.text
    assert [row["id"] for row in shift.json()["data"]["mine"]] == [task_id]
    assert [row["id"] for row in shift.json()["data"]["team"]] == [task_id]

    task_update_command = {
        "action": "operator_task.update",
        "target": {"type": "operator_task", "id": task_id},
        "payload": {
            "expected_version": 1,
            "status": "in_progress",
            "next_action": "Выполнить безопасный повтор команды",
        },
    }
    prepared = client.post(
        "/api/admin/v2/shift/action-intents",
        headers=unsafe,
        json=task_update_command,
    )
    assert prepared.status_code == 200, prepared.text
    task_update_intent = prepared.json()["data"]
    updated_task = client.post(
        f"/api/admin/v2/shift/action-intents/{task_update_intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                task_update_intent["confirmation_challenge"].encode("utf-8")
            ).hexdigest(),
        },
        json=task_update_command,
    )
    assert updated_task.status_code == 200, updated_task.text
    assert updated_task.json()["data"]["task_version"] == 2
    tasks = client.get("/api/admin/v2/tasks")
    assert tasks.status_code == 200, tasks.text
    assert tasks.json()["data"]["items"][0]["status"] == "in_progress"

    incident_id = str(uuid.uuid4())
    incident_key = "ops-test-incident-42"
    started_at = (_utcnow() - timedelta(minutes=10)).isoformat() + "Z"
    incident_command = {
        "action": "incident.create",
        "target": {"type": "incident", "id": incident_id},
        "payload": {
            "incident_key": incident_key,
            "title": "Тестовый отказ узла",
            "summary": "Проверка единого operator incident workflow.",
            "severity": "major",
            "started_at": started_at,
            "affected_node_codes": ["ru-test-1"],
            "compensation_days": 0,
            "owner_operator_id": operator_id,
            "owner_team": "incident_commander",
            "impact": "Тестовый контур недоступен.",
            "runbook_url": "https://docs.pokrov.test/runbooks/node",
        },
    }
    prepared = client.post(
        "/api/admin/v2/incidents/action-intents",
        headers=unsafe,
        json=incident_command,
    )
    assert prepared.status_code == 200, prepared.text
    incident_intent = prepared.json()["data"]
    created = client.post(
        f"/api/admin/v2/incidents/action-intents/{incident_intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": "22222222-2222-4222-8222-222222222222",
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                incident_intent["confirmation_challenge"].encode("utf-8")
            ).hexdigest(),
        },
        json=incident_command,
    )
    assert created.status_code == 200, created.text
    assert created.json()["data"]["incident_version"] == 1

    from models import OpsAlert

    db = api.SessionLocal()
    try:
        alert = OpsAlert(
            fingerprint="operator-v2-alert-42",
            source="test_source",
            severity="critical",
            status="active",
            title="Источник недоступен",
            environment="test",
            first_seen_at=_utcnow(),
            last_seen_at=_utcnow(),
            created_at=_utcnow(),
            updated_at=_utcnow(),
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        alert_id = int(alert.id)
    finally:
        db.close()

    alert_command = {
        "action": "alert.link_incident",
        "target": {"type": "alert", "id": str(alert_id)},
        "payload": {
            "expected_version": 1,
            "incident_id": incident_id,
            "expected_incident_version": 1,
        },
    }
    prepared = client.post(
        "/api/admin/v2/incidents/action-intents",
        headers=unsafe,
        json=alert_command,
    )
    assert prepared.status_code == 200, prepared.text
    alert_intent = prepared.json()["data"]
    linked = client.post(
        f"/api/admin/v2/incidents/action-intents/{alert_intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": "33333333-3333-4333-8333-333333333333",
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                alert_intent["confirmation_challenge"].encode("utf-8")
            ).hexdigest(),
        },
        json=alert_command,
    )
    assert linked.status_code == 200, linked.text
    assert linked.json()["data"]["incident_version"] == 2

    acknowledge_command = {
        "action": "alert.ack",
        "target": {"type": "alert", "id": str(alert_id)},
        "payload": {"expected_version": 2},
    }
    prepared = client.post(
        "/api/admin/v2/incidents/action-intents",
        headers=unsafe,
        json=acknowledge_command,
    )
    assert prepared.status_code == 200, prepared.text
    acknowledge_intent = prepared.json()["data"]
    acknowledged = client.post(
        f"/api/admin/v2/incidents/action-intents/{acknowledge_intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": "66666666-6666-4666-8666-666666666666",
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                acknowledge_intent["confirmation_challenge"].encode("utf-8")
            ).hexdigest(),
        },
        json=acknowledge_command,
    )
    assert acknowledged.status_code == 200, acknowledged.text
    assert acknowledged.json()["data"]["alert_status"] == "acknowledged"

    link_command = {
        "action": "incident.link",
        "target": {"type": "incident", "id": incident_id},
        "payload": {
            "expected_version": 2,
            "entity_type": "release",
            "entity_id": "1.2.0-rc.1",
            "label": "Кандидат релиза",
        },
    }
    prepared = client.post(
        "/api/admin/v2/incidents/action-intents",
        headers=unsafe,
        json=link_command,
    )
    assert prepared.status_code == 200, prepared.text
    link_intent = prepared.json()["data"]
    linked_entity = client.post(
        f"/api/admin/v2/incidents/action-intents/{link_intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                link_intent["confirmation_challenge"].encode("utf-8")
            ).hexdigest(),
        },
        json=link_command,
    )
    assert linked_entity.status_code == 200, linked_entity.text
    assert linked_entity.json()["data"]["incident_version"] == 3

    stale_update = {
        "action": "incident.update",
        "target": {"type": "incident", "id": incident_id},
        "payload": {"expected_version": 2, "note": "Старая версия"},
    }
    stale = client.post(
        "/api/admin/v2/incidents/action-intents",
        headers=unsafe,
        json=stale_update,
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "state_changed"

    resolved_command = {
        "action": "incident.update",
        "target": {"type": "incident", "id": incident_id},
        "payload": {
            "expected_version": 3,
            "workflow_status": "resolved",
            "ended_at": _utcnow().isoformat() + "Z",
            "note": "Работоспособность восстановлена.",
            "communications_summary": "Статус опубликован в тестовом канале.",
            "postmortem_status": "pending",
        },
    }
    prepared = client.post(
        "/api/admin/v2/incidents/action-intents",
        headers=unsafe,
        json=resolved_command,
    )
    assert prepared.status_code == 200, prepared.text
    resolved_intent = prepared.json()["data"]
    resolved = client.post(
        f"/api/admin/v2/incidents/action-intents/{resolved_intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": "44444444-4444-4444-8444-444444444444",
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                resolved_intent["confirmation_challenge"].encode("utf-8")
            ).hexdigest(),
        },
        json=resolved_command,
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["data"]["incident_version"] == 4

    compensation_command = {
        "action": "incident.compensate",
        "target": {"type": "incident", "id": incident_id},
        "payload": {"expected_version": 4},
    }
    blocked = client.post(
        "/api/admin/v2/incidents/action-intents",
        headers=unsafe,
        json=compensation_command,
    )
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "operator_step_up_required"

    stepped_up = client.post(
        "/api/admin/v2/auth/step-up",
        headers={**unsafe, **_admin_headers()},
    )
    assert stepped_up.status_code == 200, stepped_up.text
    prepared = client.post(
        "/api/admin/v2/incidents/action-intents",
        headers=unsafe,
        json=compensation_command,
    )
    assert prepared.status_code == 200, prepared.text
    compensation_intent = prepared.json()["data"]
    assert compensation_intent["preview"]["impacted_accounts"] == 0
    compensated = client.post(
        f"/api/admin/v2/incidents/action-intents/{compensation_intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": "55555555-5555-4555-8555-555555555555",
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                incident_key.encode("utf-8")
            ).hexdigest(),
        },
        json=compensation_command,
    )
    assert compensated.status_code == 200, compensated.text
    assert compensated.json()["data"]["incident_version"] == 5
    assert compensated.json()["data"]["granted_accounts"] == 0

    detail = client.get(f"/api/admin/v2/incidents/{incident_id}")
    assert detail.status_code == 200, detail.text
    body = detail.json()["data"]
    assert body["workflow_status"] == "resolved"
    assert [event["event_type"] for event in body["timeline"]] == [
        "created",
        "alert_link",
        "link",
        "status",
        "compensation",
    ]
    assert [row["id"] for row in body["alerts"]] == [alert_id]
    assert body["alerts"][0]["status"] == "acknowledged"
    assert body["linked_entities"][0]["entity_id"] == "1.2.0-rc.1"

    db = api.SessionLocal()
    try:
        false_positive_alert = OpsAlert(
            fingerprint="operator-v2-false-positive-42",
            source="test_source",
            severity="warning",
            status="active",
            title="Ложный тестовый сигнал",
            environment="test",
            first_seen_at=_utcnow(),
            last_seen_at=_utcnow(),
            created_at=_utcnow(),
            updated_at=_utcnow(),
        )
        incident_alert = OpsAlert(
            fingerprint="operator-v2-create-incident-42",
            source="test_source",
            severity="critical",
            status="active",
            title="Новый тестовый отказ",
            environment="test",
            first_seen_at=_utcnow(),
            last_seen_at=_utcnow(),
            created_at=_utcnow(),
            updated_at=_utcnow(),
        )
        db.add_all([false_positive_alert, incident_alert])
        db.commit()
        db.refresh(false_positive_alert)
        db.refresh(incident_alert)
        false_positive_alert_id = int(false_positive_alert.id)
        incident_alert_id = int(incident_alert.id)
    finally:
        db.close()

    false_positive_command = {
        "action": "alert.false_positive",
        "target": {"type": "alert", "id": str(false_positive_alert_id)},
        "payload": {"expected_version": 1},
    }
    prepared = client.post(
        "/api/admin/v2/incidents/action-intents",
        headers=unsafe,
        json=false_positive_command,
    )
    assert prepared.status_code == 200, prepared.text
    false_positive_intent = prepared.json()["data"]
    false_positive = client.post(
        f"/api/admin/v2/incidents/action-intents/{false_positive_intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                false_positive_intent["confirmation_challenge"].encode("utf-8")
            ).hexdigest(),
        },
        json=false_positive_command,
    )
    assert false_positive.status_code == 200, false_positive.text
    assert false_positive.json()["data"]["alert_status"] == "false_positive"

    alert_incident_id = str(uuid.uuid4())
    alert_incident_command = {
        "action": "alert.create_incident",
        "target": {"type": "alert", "id": str(incident_alert_id)},
        "payload": {
            "expected_version": 1,
            "incident_id": alert_incident_id,
            "incident_key": "alert-created-incident-42",
            "title": "Инцидент из алерта",
            "summary": "Создан из критического тестового алерта.",
            "severity": "critical",
            "started_at": (_utcnow() - timedelta(minutes=2)).isoformat() + "Z",
            "affected_node_codes": [],
            "compensation_days": 0,
            "owner_operator_id": operator_id,
            "owner_team": "incident_commander",
        },
    }
    prepared = client.post(
        "/api/admin/v2/incidents/action-intents",
        headers=unsafe,
        json=alert_incident_command,
    )
    assert prepared.status_code == 200, prepared.text
    alert_incident_intent = prepared.json()["data"]
    alert_incident = client.post(
        f"/api/admin/v2/incidents/action-intents/{alert_incident_intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                alert_incident_intent["confirmation_challenge"].encode("utf-8")
            ).hexdigest(),
        },
        json=alert_incident_command,
    )
    assert alert_incident.status_code == 200, alert_incident.text
    assert alert_incident.json()["data"]["incident_id"] == alert_incident_id
    created_detail = client.get(f"/api/admin/v2/incidents/{alert_incident_id}")
    assert created_detail.status_code == 200, created_detail.text
    assert created_detail.json()["data"]["alerts"][0]["id"] == incident_alert_id

    legacy_prepare = client.post(
        "/api/admin/action-intents",
        headers=unsafe,
        json={
            "action": "alert.ack",
            "target": {"type": "alert", "id": str(incident_alert_id)},
            "payload": {"expected_version": 2},
        },
    )
    assert legacy_prepare.status_code == 200, legacy_prepare.text
    legacy_intent = legacy_prepare.json()
    legacy_ack = client.post(
        f"/api/admin/alerts/{incident_alert_id}/ack",
        headers={
            **unsafe,
            "X-Admin-Intent-Id": legacy_intent["intent_id"],
            "X-Admin-Idempotency-Key": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                legacy_intent["confirmation_challenge"].encode("utf-8")
            ).hexdigest(),
        },
    )
    assert legacy_ack.status_code == 200, legacy_ack.text
    assert legacy_ack.json()["alert_status"] == "acknowledged"


def test_network_operator_high_risk_route_requires_fresh_step_up(
    monkeypatch,
    tmp_path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app, base_url="https://api.pokrov.test")
    bootstrap = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert bootstrap.status_code == 200, bootstrap.text
    csrf = bootstrap.json()["data"]["session"]["csrf_token"]

    from models import AdminOperatorRole, Node

    db = api.SessionLocal()
    try:
        role = db.query(AdminOperatorRole).one()
        role.role_code = "network_operator"
        db.add(
            Node(
                code="de-step-up",
                name="DE step-up",
                host="de-step-up.example.test",
                enabled=True,
                accepting_new_clients=True,
                is_draining=False,
                is_healthy=True,
                health_score=1.0,
            )
        )
        db.commit()
    finally:
        db.close()

    assert client.get("/api/admin/v2/network/fleet").status_code == 200
    assert client.get("/api/admin/users").status_code == 403

    command = {
        "action": "node.disable",
        "target": {"type": "node", "id": "de-step-up"},
        "payload": {"force": False},
    }
    unsafe = {"X-Pokrov-Admin-CSRF": csrf}
    blocked = client.post(
        "/api/admin/v2/network/action-intents",
        headers=unsafe,
        json=command,
    )
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "operator_step_up_required"

    stepped_up = client.post(
        "/api/admin/v2/auth/step-up",
        headers={**unsafe, **_admin_headers()},
    )
    assert stepped_up.status_code == 200, stepped_up.text
    prepared = client.post(
        "/api/admin/v2/network/action-intents",
        headers=unsafe,
        json=command,
    )
    assert prepared.status_code == 200, prepared.text
    assert prepared.json()["data"]["risk_level"] == "L3"
    assert prepared.json()["data"]["confirmation_challenge"] == "DE-STEP-UP"


def test_payments_operator_uses_money_bridge_and_native_action_boundary(
    monkeypatch,
    tmp_path,
) -> None:
    api = _load_api(monkeypatch, tmp_path, operator_environment="production")
    client = TestClient(api.app, base_url="https://api.pokrov.test")
    bootstrap = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert bootstrap.status_code == 200, bootstrap.text
    csrf = bootstrap.json()["data"]["session"]["csrf_token"]

    from models import AdminOperatorRole

    db = api.SessionLocal()
    try:
        role = db.query(AdminOperatorRole).one()
        role.role_code = "payments_operator"
        db.commit()
    finally:
        db.close()

    promo_slots = client.get("/api/admin/promo-slots")
    assert promo_slots.status_code == 200, promo_slots.text
    assert client.get("/api/admin/users").status_code == 403

    empty_upload = client.post(
        "/api/admin/promo-media",
        headers={"X-Pokrov-Admin-CSRF": csrf},
        content=b"",
    )
    assert empty_upload.status_code == 400
    assert "empty" in empty_upload.text.lower()

    command = {
        "action": "promo_slots.update",
        "target": {"type": "config", "id": "promo-slots"},
        "payload": {"assignments": []},
    }
    prepared = client.post(
        "/api/admin/v2/money/action-intents",
        headers={"X-Pokrov-Admin-CSRF": csrf},
        json=command,
    )
    assert prepared.status_code == 200, prepared.text
    assert prepared.json()["data"]["risk_level"] == "L2"


def test_admin_v2_secret_and_role_boundaries_fail_closed(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path, operator_session_secret="short")
    client = TestClient(api.app, base_url="https://api.pokrov.test")

    unavailable = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert unavailable.status_code == 503
    assert unavailable.json()["error"]["code"] == "operator_session_not_configured"

    from admin_v2.roles import ROLE_REGISTRY, permissions_for_roles

    assert permissions_for_roles(["unknown_role"]) == frozenset()
    for role_code in (
        "sre",
        "network_operator",
        "payments_operator",
        "growth_operator",
        "release_manager",
        "incident_commander",
    ):
        assert "command.high_risk" in ROLE_REGISTRY[role_code]
        assert "session.step_up" in ROLE_REGISTRY[role_code]
    for role_code in ("readonly", "support_l1", "support_l2", "security_auditor"):
        assert "command.high_risk" not in ROLE_REGISTRY[role_code]


def test_admin_v2_revoked_role_and_expired_session_fail_closed(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app, base_url="https://api.pokrov.test")

    bootstrap = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert bootstrap.status_code == 200, bootstrap.text

    from models import AdminOperatorRole, AdminOperatorSession

    db = api.SessionLocal()
    try:
        role = db.query(AdminOperatorRole).one()
        role.revoked_at = _utcnow()
        db.commit()
    finally:
        db.close()

    revoked_role = client.get("/api/admin/v2/meta")
    assert revoked_role.status_code == 403
    assert revoked_role.json()["error"]["code"] == "operator_permission_missing"

    expiry_dir = tmp_path / "expired"
    expiry_dir.mkdir()
    expiry_api = _load_api(monkeypatch, expiry_dir)
    expiry_client = TestClient(expiry_api.app, base_url="https://api.pokrov.test")
    expiry_bootstrap = expiry_client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert expiry_bootstrap.status_code == 200, expiry_bootstrap.text
    session_id = expiry_bootstrap.json()["data"]["session"]["id"]

    db = expiry_api.SessionLocal()
    try:
        session = db.query(AdminOperatorSession).filter(AdminOperatorSession.id == session_id).one()
        session.idle_expires_at = _utcnow() - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()

    expired = expiry_client.get("/api/admin/v2/meta")
    assert expired.status_code == 401
    assert expired.json()["error"]["code"] == "operator_session_expired"

    db = expiry_api.SessionLocal()
    try:
        session = db.query(AdminOperatorSession).filter(AdminOperatorSession.id == session_id).one()
        assert session.revoked_at is not None
        assert session.revoke_reason == "idle_expired"
    finally:
        db.close()


def test_admin_v2_high_risk_permission_requires_fresh_step_up() -> None:
    from admin_v2.security import (
        AdminV2Error,
        OperatorContext,
        OperatorSessionConfig,
        require_permission,
    )

    now = _utcnow()
    config = OperatorSessionConfig(
        secret="admin-operator-session-secret-32-bytes-test",
        environment="test",
        idle_ttl_seconds=1800,
        absolute_ttl_seconds=43200,
        step_up_ttl_seconds=600,
        max_active_sessions=10,
        trusted_origins=frozenset({"https://api.pokrov.test"}),
    )
    context = OperatorContext(
        operator_id="operator-1",
        actor_tg_id=9999,
        display_name="admin",
        session_id="session-1",
        environment="test",
        roles=("superadmin",),
        permissions=frozenset({"command.high_risk"}),
        created_at=now,
        idle_expires_at=now + timedelta(minutes=30),
        absolute_expires_at=now + timedelta(hours=12),
        step_up_at=None,
        csrf_token="csrf",
    )

    with pytest.raises(AdminV2Error) as missing_step_up:
        require_permission(context, "command.high_risk", config=config, step_up=True)
    assert missing_step_up.value.code == "operator_step_up_required"

    fresh_context = OperatorContext(**{**context.__dict__, "step_up_at": now})
    require_permission(fresh_context, "command.high_risk", config=config, step_up=True)

    stale_context = OperatorContext(
        **{**context.__dict__, "step_up_at": now - timedelta(seconds=config.step_up_ttl_seconds + 1)}
    )
    with pytest.raises(AdminV2Error) as stale_step_up:
        require_permission(stale_context, "command.high_risk", config=config, step_up=True)
    assert stale_step_up.value.code == "operator_step_up_required"


def test_admin_ops_overview_uses_one_metrics_snapshot_without_full_summary_or_alert_refresh(
    monkeypatch,
    tmp_path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    now = _utcnow()
    _seed_ops_fixture(api, now=now)
    metric_calls = 0
    original_metrics_snapshot = api._ops_build_admin_metrics_status_snapshot

    def counted_metrics_snapshot(**kwargs):
        nonlocal metric_calls
        metric_calls += 1
        return original_metrics_snapshot(**kwargs)

    async def forbidden_slow_path(**_kwargs):
        raise AssertionError("overview must not refresh durable alerts")

    async def forbidden_full_summary(**_kwargs):
        raise AssertionError("overview must not load the full admin summary")

    monkeypatch.setattr(api, "_ops_build_admin_metrics_status_snapshot", counted_metrics_snapshot)
    monkeypatch.setattr(api, "_refresh_ops_alerts_for_payload", forbidden_slow_path)
    monkeypatch.setattr(api, "admin_summary", forbidden_full_summary)

    response = TestClient(api.app).get("/api/admin/ops/overview", headers=_admin_headers())

    assert response.status_code == 200, response.text
    assert metric_calls == 1
    body = response.json()
    assert body["summary"]["users"]["active"] == 2
    assert body["summary"]["nodes"] == {"total": 2, "healthy": 2}


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
    assert body["commercial_attribution"]["schema"] == "pokrov-commercial-attribution-read-model-v1"
    assert body["commercial_attribution"]["authority"]["telemetry_is_payment_truth"] is False
    assert {row["order_id"] for row in body["problem_orders"]} >= {"pending-ops-1", "manual-ops-1", "failed-ops-1"}


def test_admin_payments_summary_flags_only_unreconciled_reversals(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import ExternalOrder

    now = _utcnow()
    s = api.SessionLocal()
    try:
        s.add_all(
            [
                ExternalOrder(
                    order_id="refund-needs-operator",
                    provider="lavatop",
                    plan_code="1_month",
                    amount=990,
                    currency="RUB",
                    status="refunded",
                    meta_json=json.dumps({
                        "fulfillment": {"status": "reversal_pending_operator_action"},
                        "reversal": {
                            "operator_action_required": True,
                            "reconciliation_status": "grant_not_found",
                        },
                    }),
                    created_at=now - timedelta(hours=2),
                ),
                ExternalOrder(
                    order_id="refund-reconciled",
                    provider="lavatop",
                    plan_code="1_month",
                    amount=990,
                    currency="RUB",
                    status="refunded",
                    meta_json=json.dumps({
                        "fulfillment": {"status": "reversed"},
                        "reversal": {
                            "operator_action_required": False,
                            "reconciliation_status": "reversed",
                        },
                    }),
                    created_at=now - timedelta(hours=1),
                ),
                ExternalOrder(
                    order_id="refund-without-reconciliation-evidence",
                    provider="lavatop",
                    plan_code="1_month",
                    amount=990,
                    currency="RUB",
                    status="refunded",
                    meta_json=json.dumps({}),
                    created_at=now - timedelta(minutes=30),
                ),
            ]
        )
        s.commit()
        body = api._admin_payments_summary_payload(s=s, period="7d")
    finally:
        s.close()

    assert body["attention"]["failed_count"] == 2
    assert body["attention"]["problem_count"] == 2
    assert {row["order_id"] for row in body["problem_orders"]} == {
        "refund-needs-operator",
        "refund-without-reconciliation-evidence",
    }


def test_admin_problem_list_filters_reversal_state_before_limit(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import ExternalOrder

    now = _utcnow()
    s = api.SessionLocal()
    try:
        reconciled = [
            ExternalOrder(
                order_id=f"reconciled-{index}",
                provider="lavatop",
                plan_code="1_month",
                amount=990,
                currency="RUB",
                status="refunded",
                meta_json=json.dumps({
                    "fulfillment": {"status": "reversed"},
                    "reversal": {
                        "operator_action_required": False,
                        "reconciliation_status": "reversed",
                    },
                }),
                created_at=now - timedelta(minutes=index),
            )
            for index in range(101)
        ]
        s.add_all(reconciled)
        s.add(ExternalOrder(
            order_id="old-unreconciled-refund",
            provider="lavatop",
            plan_code="1_month",
            amount=990,
            currency="RUB",
            status="refunded",
            meta_json=json.dumps({
                "fulfillment": {"status": "reversal_pending_operator_action"},
                "reversal": {
                    "operator_action_required": True,
                    "reconciliation_status": "grant_not_found",
                },
            }),
            created_at=now - timedelta(hours=6),
        ))
        s.commit()
        body = api._admin_payments_summary_payload(s=s, period="7d")
    finally:
        s.close()

    assert body["attention"]["failed_count"] == 1
    assert body["attention"]["problem_count"] == 1
    assert [row["order_id"] for row in body["problem_orders"]] == ["old-unreconciled-refund"]


def test_admin_attention_includes_old_outstanding_reversal_globally(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import ExternalOrder

    now = _utcnow()
    s = api.SessionLocal()
    try:
        s.add_all([
            ExternalOrder(
                order_id="old-outstanding-refund",
                provider="lavatop",
                status="refunded",
                meta_json=json.dumps({
                    "fulfillment": {"status": "reversal_pending_operator_action"},
                    "reversal": {
                        "operator_action_required": True,
                        "reconciliation_status": "grant_not_found",
                    },
                }),
                created_at=now - timedelta(days=120),
            ),
            ExternalOrder(
                order_id="old-reconciled-refund",
                provider="lavatop",
                status="refunded",
                meta_json=json.dumps({
                    "fulfillment": {"status": "reversed"},
                    "reversal": {
                        "operator_action_required": False,
                        "reconciliation_status": "reversed",
                    },
                }),
                created_at=now - timedelta(days=110),
            ),
        ])
        s.commit()
        body = api._admin_payments_summary_payload(s=s, period="7d")
    finally:
        s.close()

    assert body["attention"]["failed_count"] == 1
    assert body["attention"]["problem_count"] == 1
    assert [row["order_id"] for row in body["problem_orders"]] == ["old-outstanding-refund"]


def test_admin_problem_rows_share_one_descending_limit(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import ExternalOrder

    now = _utcnow()
    s = api.SessionLocal()
    try:
        s.add(ExternalOrder(
            order_id="old-unresolved-before-limit",
            provider="lavatop",
            status="refunded",
            meta_json=json.dumps({
                "fulfillment": {"status": "reversal_pending_operator_action"},
                "reversal": {
                    "operator_action_required": True,
                    "reconciliation_status": "grant_not_found",
                },
            }),
            created_at=now - timedelta(days=2),
        ))
        for index in range(25):
            s.add(ExternalOrder(
                order_id=f"newer-manual-{index:02d}",
                provider="lavatop",
                status="manual_review" if index % 2 == 0 else "failed",
                created_at=now - timedelta(minutes=index),
            ))
        s.commit()
        body = api._admin_payments_summary_payload(s=s, period="7d")
    finally:
        s.close()

    order_ids = [row["order_id"] for row in body["problem_orders"]]
    assert len(order_ids) == 25
    assert "newer-manual-24" in order_ids
    assert "old-unresolved-before-limit" not in order_ids


def test_admin_reversal_python_verifier_excludes_large_reconciled_set(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import ExternalOrder

    now = _utcnow()
    s = api.SessionLocal()
    try:
        for index in range(300):
            s.add(ExternalOrder(
                order_id=f"canonical-reconciled-{index:03d}",
                provider="lavatop",
                status="refunded",
                meta_json=json.dumps({
                    "fulfillment": {"status": "reversed"},
                    "reversal": {
                        "operator_action_required": False,
                        "reconciliation_status": "reversed",
                        "recorded_at": now.isoformat(),
                    },
                }, separators=(",", ":")),
                created_at=now - timedelta(days=90),
            ))
        s.add(ExternalOrder(
            order_id="canonical-unresolved",
            provider="lavatop",
            status="chargeback",
            meta_json=json.dumps({
                "fulfillment": {"status": "reversal_pending_operator_action"},
                "reversal": {
                    "operator_action_required": True,
                    "reconciliation_status": "grant_not_found",
                    "recorded_at": now.isoformat(),
                },
            }, separators=(",", ":")),
            created_at=now - timedelta(days=90),
        ))
        s.commit()

        checked: list[str] = []
        original = api._payment_reversal_needs_operator

        def _tracked(order):
            checked.append(str(order.order_id))
            return original(order)

        api._payment_reversal_needs_operator = _tracked
        try:
            body = api._admin_payments_summary_payload(s=s, period="7d")
        finally:
            api._payment_reversal_needs_operator = original
    finally:
        s.close()

    assert body["attention"]["failed_count"] == 1
    assert [row["order_id"] for row in body["problem_orders"]] == ["canonical-unresolved"]
    assert len(checked) == 301
    assert "canonical-unresolved" in checked


def test_admin_reversal_attention_ignores_nested_success_markers(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import ExternalOrder

    now = _utcnow()
    s = api.SessionLocal()
    try:
        s.add(ExternalOrder(
            order_id="unresolved-with-nested-success",
            provider="lavatop",
            status="refunded",
            meta_json=json.dumps({
                "callback": {
                    "fulfillment": {"status": "reversed"},
                    "reversal": {
                        "operator_action_required": False,
                        "reconciliation_status": "reversed",
                    },
                },
                "fulfillment": {"status": "reversal_pending_operator_action"},
                "reversal": {
                    "operator_action_required": True,
                    "reconciliation_status": "pending",
                    "recorded_at": now.isoformat(),
                },
            }, separators=(",", ":")),
            created_at=now - timedelta(days=60),
        ))
        s.commit()
        body = api._admin_payments_summary_payload(s=s, period="7d")
    finally:
        s.close()

    assert body["attention"]["failed_count"] == 1
    assert [row["order_id"] for row in body["problem_orders"]] == ["unresolved-with-nested-success"]


def test_reversal_problem_time_overflow_falls_back_to_order_creation(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import ExternalOrder

    created_at = _utcnow() - timedelta(days=1)
    order = ExternalOrder(
        order_id="overflow-reversal-time",
        provider="lavatop",
        status="refunded",
        meta_json=json.dumps({
            "reversal": {"recorded_at": "0001-01-01T00:00:00+14:00"},
        }),
        created_at=created_at,
    )

    assert api._payment_reversal_problem_time(order) == created_at


def test_admin_problem_recency_uses_reversal_recorded_at(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import ExternalOrder

    now = _utcnow()
    s = api.SessionLocal()
    try:
        s.add_all([
            ExternalOrder(
                order_id="fresh-refund-old-purchase",
                provider="lavatop",
                status="refunded",
                meta_json=json.dumps({
                    "fulfillment": {"status": "reversal_pending_operator_action"},
                    "reversal": {
                        "operator_action_required": True,
                        "reconciliation_status": "pending",
                        "recorded_at": (now - timedelta(minutes=5)).isoformat(),
                    },
                }),
                created_at=now - timedelta(days=120),
            ),
            ExternalOrder(
                order_id="older-ordinary-problem",
                provider="lavatop",
                status="manual_review",
                created_at=now - timedelta(hours=1),
            ),
        ])
        s.commit()
        body = api._admin_payments_summary_payload(s=s, period="7d")
    finally:
        s.close()

    assert [row["order_id"] for row in body["problem_orders"]][:2] == [
        "fresh-refund-old-purchase",
        "older-ordinary-problem",
    ]


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
    unknown = next(row for row in body["rows"] if row["tg_id"] is None)
    assert known["row_id"] == "user:1001"
    assert unknown["row_id"].startswith("panel:")
    assert "identity" not in known
    assert "panel_email" not in unknown
    assert known["online_connections_now"] == 2
    assert "manual_review" in known["risk_flags"]
    assert "multi_ip" in known["risk_flags"]
    assert "observer:watch" in known["risk_flags"]
    assert body["panel_errors"] == [{"node_code": "pl", "evidence_code": "panel_request_failed"}]
    assert "203.0.113.77" not in response.text
    assert "198.51.100.42" not in response.text
    assert "source_ip_raw" not in response.text
    assert "nearcap@example.test" not in response.text
    assert "unknown@example.test" not in response.text
    assert "client-1001" not in response.text
    assert "client-unknown" not in response.text
    assert "panel timeout" not in response.text


def test_admin_v2_cutover_projections_and_referral_action(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path, operator_environment="production")
    now = _utcnow()
    _seed_ops_fixture(api, now=now)

    class FakeControlPanel:
        async def get_node_online_clients(self, *, node_codes=None):
            return {
                "rows": [
                    {
                        "node_code": "de",
                        "tg_id": 1001,
                        "panel_email": "cutover@example.test",
                        "client_uuid": "cutover-client-secret",
                        "ip_count": 1,
                        "last_online_at": now.isoformat(),
                        "source_ip_raw": "203.0.113.99",
                    }
                ],
                "errors": [],
            }

        async def close(self):
            return None

    monkeypatch.setattr(api, "ControlPanel", FakeControlPanel)
    client = TestClient(api.app, base_url="https://api.pokrov.test")
    bootstrap = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert bootstrap.status_code == 200, bootstrap.text
    csrf = bootstrap.json()["data"]["session"]["csrf_token"]

    overview = client.get("/api/admin/v2/shift/overview")
    assert overview.status_code == 200, overview.text
    assert overview.json()["sources"][0]["authority"] == "ops_metrics_capacity_and_alert_read_models"

    online = client.get("/api/admin/v2/support/online?limit=50&only=de")
    assert online.status_code == 200, online.text
    assert online.json()["data"]["summary"]["raw_ip_exposed"] is False
    assert online.json()["sources"][0]["authority"] == "control_panel_online_and_account_read_model"
    assert "203.0.113.99" not in online.text
    assert "cutover@example.test" not in online.text
    assert "cutover-client-secret" not in online.text

    funnel = client.get(
        "/api/admin/v2/growth/funnel?from=2026-07-01T00:00:00Z&to=2026-07-31T00:00:00Z"
    )
    assert funnel.status_code == 200, funnel.text
    assert funnel.json()["sources"][0]["authority"] == "acquisition_commerce_and_event_read_models"

    referrals = client.get("/api/admin/v2/growth/referrals?limit=100&status=pending")
    assert referrals.status_code == 200, referrals.text
    assert referrals.json()["sources"][0]["authority"] == "referral_bonus_queue"

    command = {
        "action": "referral.process",
        "target": {"type": "referral_queue", "id": "ready"},
        "payload": {"limit": 100, "force_without_activity": False},
    }
    prepared = client.post(
        "/api/admin/v2/growth/action-intents",
        headers={"X-Pokrov-Admin-CSRF": csrf},
        json=command,
    )
    assert prepared.status_code == 200, prepared.text
    intent = prepared.json()["data"]
    executed = client.post(
        f"/api/admin/v2/growth/action-intents/{intent['intent_id']}/execute",
        headers={
            "X-Pokrov-Admin-CSRF": csrf,
            "X-Admin-Idempotency-Key": str(uuid.uuid4()),
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                str(intent["confirmation_challenge"]).encode("utf-8")
            ).hexdigest(),
        },
        json=command,
    )
    assert executed.status_code == 200, executed.text
    assert executed.json()["data"]["status"] == "completed"


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

    guarded = client.post(
        "/api/admin/broadcast",
        headers=_admin_headers(),
        json={"text": "Реальная отправка", "segment": "all_active", "limit": 20, "dry_run": False},
    )
    assert guarded.status_code == 428, guarded.text
    assert guarded.json()["detail"]["code"] == "intent_required"
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


def test_provider_quota_read_contract_redacts_persisted_notes(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import ProviderTrafficQuota

    client = TestClient(api.app)
    private_note = "SYNTHETIC-PRIVATE-PROVIDER-NOTE"
    s = api.SessionLocal()
    try:
        s.add(
            ProviderTrafficQuota(
                node_code="nl-free",
                included_bytes=_gb(100),
                reset_day=15,
                timezone="UTC",
                warning_ratio=0.7,
                critical_ratio=0.9,
                enabled=True,
                notes=private_note,
            )
        )
        s.commit()
    finally:
        s.close()

    response = client.get("/api/admin/provider-quotas", headers=_admin_headers())
    assert response.status_code == 200, response.text
    assert private_note not in response.text
    quota = response.json()["quotas"][0]
    assert quota["node_code"] == "nl-free"
    assert quota["notes_present"] is True
    assert quota["notes_length"] == len(private_note)
    assert len(quota["notes_sha256"]) == 64
    assert "notes" not in quota


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
                "body": "test",
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
                "body": "test",
            }
        ]
        assert rows[0].status == "resolved"
    finally:
        s.close()


def test_durable_alert_refresh_notifies_when_warning_resolves(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from admin_ops_service import refresh_ops_alerts

    now = _utcnow()
    s = api.SessionLocal()
    try:
        refresh_ops_alerts(
            s=s,
            now=now,
            candidates=[
                {
                    "fingerprint": "node_metrics:de:disk_high",
                    "source": "node_metrics",
                    "severity": "warning",
                    "title": "Node de: Disk usage high",
                    "body": "test",
                    "node_code": "de",
                }
            ],
        )
        s.flush()

        _rows, notifications = refresh_ops_alerts(
            s=s,
            now=now + timedelta(minutes=5),
            candidates=[],
        )

        assert notifications == [
            {
                "kind": "resolved",
                "fingerprint": "node_metrics:de:disk_high",
                "severity": "warning",
                "title": "Node de: Disk usage high",
                "body": "test",
            }
        ]
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


def test_admin_observability_sanitizes_legacy_transport_health_on_read(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from admin_ops_service import build_node_observability
    from models import NodeHealthSample, NodeRuntimeMetric

    now = _utcnow()
    session = api.SessionLocal()
    try:
        session.add(
            api.Node(
                code="pl",
                name="Poland",
                host="pl.example.test",
                inbound_id=1,
                enabled=True,
                accepting_new_clients=True,
                hoster_family="hetzner",
                hoster_asn="AS24940",
                hoster_subnet="198.51.100.0/24",
                last_probe_stage="tls_sni",
                last_probe_error_kind="tls_handshake_failed",
                last_probe_error_message="forbidden-admin-error-message",
            )
        )
        session.add(
            NodeHealthSample(
                node_code="pl",
                sampled_at=now,
                is_healthy=True,
                score=95.0,
                probe_stage="tls_sni",
                probe_error_kind="tls_handshake_failed",
                probe_classification="transport_failure",
                transport_health_json=json.dumps(
                    {
                        "panel_state": "healthy",
                        "dataplane_state": "healthy",
                        "endpoint": "forbidden-admin-endpoint.invalid",
                        "certificate": "forbidden-admin-certificate",
                        "token": "forbidden-admin-token",
                        "nested": {"host": "forbidden-nested.invalid"},
                    }
                ),
            )
        )
        session.add(
            NodeRuntimeMetric(
                node_code="pl",
                sampled_at=now,
                source="node_agent",
                meta_json=json.dumps(
                    {
                        "panel_state": "healthy",
                        "exception": "forbidden-admin-runtime-exception",
                    }
                ),
            )
        )
        session.commit()

        payload = build_node_observability(
            s=session,
            node_code="pl",
            now=now,
            metrics_stale_after_seconds=900,
            include_ru_history=False,
        )
    finally:
        session.close()

    assert payload is not None
    assert payload["node"] == {
        "code": "pl",
        "name": "Poland",
        "hoster_family": "hetzner",
        "hoster_asn": "AS24940",
        "weight": 100,
    }
    assert payload["sources"]["brain_metrics"]["details"]["probe_stage"] == "tls_sni"
    rendered = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "forbidden-admin-error-message",
        "forbidden-admin-endpoint.invalid",
        "forbidden-admin-certificate",
        "forbidden-admin-token",
        "forbidden-admin-runtime-exception",
        "forbidden-nested.invalid",
        "198.51.100.0/24",
    ):
        assert forbidden not in rendered


def test_admin_v2_support_inbox_user360_and_attempts_are_versioned_and_bounded(
    monkeypatch, tmp_path
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import AccessKey, Event, User
    from tickets_repo import add_ticket_message, create_ticket

    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    db = api.SessionLocal()
    try:
        user = User(
            tg_id=1001,
            uuid=str(uuid.uuid4()),
            email="support-v2@example.test",
            sub_type="paid",
            is_active=True,
            sub_token="fixture-token",
            app_install_id="raw-install-do-not-return",
            app_platform="windows",
            app_version="1.2.0",
            app_last_seen_at=now,
        )
        db.add(user)
        ticket = create_ticket(db, user_tg_id=1001, subject="Core не запускается")
        ticket.environment = "test"
        ticket.priority = "critical"
        ticket.queue = "connection"
        add_ticket_message(
            db,
            ticket_id=ticket.id,
            sender_tg_id=1001,
            sender_role="user",
            body="Проверочная ошибка",
        )
        db.add(
            Event(
                tg_id=1001,
                event_name="runtime_start_failed",
                source="client",
                session_id="raw-session-do-not-return",
                device_id="raw-device-do-not-return",
                platform="windows",
                app_version="1.2.0",
                build_number="42",
                surface="client",
                subsystem="runtime",
                stage="core_start",
                result="failure",
                error_code="CORE-001",
                attempt_number=1,
                trace_id="raw-trace-do-not-return",
                occurred_at=now,
                received_at=now,
                meta_json='{"token":"forbidden-support-token","url":"https://private.invalid"}',
            )
        )
        db.add(
            AccessKey(
                tg_id=1001,
                key_uuid="sensitive-key-lookup-do-not-return",
                panel_email="hidden-key@example.test",
                state="active",
            )
        )
        db.commit()
        ticket_id = int(ticket.id)
        ticket_version = int(ticket.version)
    finally:
        db.close()

    class FakeControlPanel:
        async def login(self):
            return None

        async def get_user_key_snapshots(self, *, tg_id, node_codes):
            return []

        async def close(self):
            return None

    monkeypatch.setitem(
        api.admin_user_card.__globals__,
        "ControlPanel",
        FakeControlPanel,
    )

    client = TestClient(api.app, base_url="https://api.pokrov.test")
    bootstrap = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert bootstrap.status_code == 200, bootstrap.text
    csrf = bootstrap.json()["data"]["session"]["csrf_token"]

    listing = client.get("/api/admin/v2/support/tickets?status=active")
    assert listing.status_code == 200, listing.text
    assert listing.json()["data"]["items"][0]["priority"] == "critical"
    assert listing.json()["data"]["items"][0]["version"] == ticket_version

    user360 = client.get("/api/admin/v2/support/users/1001")
    assert user360.status_code == 200, user360.text
    rendered = user360.text
    assert "attempt_" in rendered and "fp_" in rendered
    for forbidden in (
        "forbidden-support-token",
        "private.invalid",
        "raw-install-do-not-return",
        "raw-session-do-not-return",
        "raw-device-do-not-return",
        "raw-trace-do-not-return",
    ):
        assert forbidden not in rendered

    attempts = client.get(f"/api/admin/v2/support/attempts?ticket_id={ticket_id}")
    assert attempts.status_code == 200, attempts.text
    assert attempts.json()["data"]["attempts"][0]["event_count"] == 1

    from models import AdminOperatorRole

    db = api.SessionLocal()
    try:
        role = db.query(AdminOperatorRole).one()
        role.role_code = "support_l1"
        db.commit()
    finally:
        db.close()

    redacted_360 = client.get("/api/admin/v2/support/users/1001")
    assert redacted_360.status_code == 200, redacted_360.text
    assert redacted_360.json()["data"]["field_access"]["support_diagnostics"] == {
        "state": "redacted",
        "required_permission": "support.sensitive.read",
        "classification": "sensitive_support_diagnostics",
    }
    for field in ("installations", "sessions", "attempts", "fingerprints"):
        assert redacted_360.json()["data"][field] == []
    assert redacted_360.json()["warnings"][0]["code"] == "field_redacted"

    sensitive_attempts = client.get(
        f"/api/admin/v2/support/attempts?ticket_id={ticket_id}"
    )
    assert sensitive_attempts.status_code == 403
    assert sensitive_attempts.json()["error"]["code"] == "operator_permission_denied"

    legacy_listing = client.get("/api/admin/users?q=1001")
    assert legacy_listing.status_code == 200, legacy_listing.text
    assert legacy_listing.json()["field_access"]["sensitive_identity"]["state"] == "redacted"
    assert legacy_listing.json()["users"][0]["app_install_id"] is None

    legacy_card = client.get("/api/admin/users/1001")
    assert legacy_card.status_code == 200, legacy_card.text
    assert legacy_card.json()["field_access"]["app_events"]["state"] == "redacted"
    assert legacy_card.json()["field_access"]["payment_orders"]["state"] == "redacted"
    assert legacy_card.json()["field_access"]["admin_actions"]["state"] == "redacted"
    assert legacy_card.json()["field_access"]["legacy_user_actions"]["state"] == "redacted"
    assert legacy_card.json()["user"]["app_install_id"] is None
    assert legacy_card.json()["app_events"] == []
    assert legacy_card.json()["payment_orders"] == []
    assert legacy_card.json()["admin_actions"] == []

    safe_search = client.get("/api/admin/search?q=1001")
    assert safe_search.status_code == 200, safe_search.text
    assert {row["kind"] for row in safe_search.json()["results"]} <= {"user", "key"}
    sensitive_search = client.get("/api/admin/search?q=raw-install-do-not-return")
    assert sensitive_search.status_code == 200, sensitive_search.text
    assert sensitive_search.json()["results"] == []
    sensitive_key_search = client.get("/api/admin/search?q=hidden-key@example.test")
    assert sensitive_key_search.status_code == 200, sensitive_key_search.text
    assert sensitive_key_search.json()["results"] == []

    assert client.get("/api/admin/users/1001/investigation").status_code == 403
    assert client.get("/api/admin/promo-slots").status_code == 403

    command = {
        "action": "ticket.claim",
        "target": {"type": "ticket", "id": str(ticket_id)},
        "payload": {"expected_version": ticket_version},
    }
    prepared = client.post(
        "/api/admin/v2/support/action-intents",
        headers={"X-Pokrov-Admin-CSRF": csrf},
        json=command,
    )
    assert prepared.status_code == 200, prepared.text
    intent = prepared.json()["data"]
    executed = client.post(
        f"/api/admin/v2/support/action-intents/{intent['intent_id']}/execute",
        headers={
            "X-Pokrov-Admin-CSRF": csrf,
            "X-Admin-Idempotency-Key": "21111111-1111-4111-8111-111111111111",
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                intent["confirmation_challenge"].encode("utf-8")
            ).hexdigest(),
        },
        json=command,
    )
    assert executed.status_code == 200, executed.text
    assert executed.json()["data"]["ticket"]["assigned_admin_tg_id"] == 9999

    stale = client.post(
        "/api/admin/v2/support/action-intents",
        headers={"X-Pokrov-Admin-CSRF": csrf},
        json=command,
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "stale_version"


def test_admin_v2_issues_one_time_signed_support_mode_through_action_intent(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("POKROV_SUPPORT_MODE_SIGNING_KEY_ID", "support-root-test")
    monkeypatch.setenv(
        "POKROV_SUPPORT_MODE_SIGNING_PRIVATE_KEY_B64",
        base64.urlsafe_b64encode(b"m" * 32).decode("ascii").rstrip("="),
    )
    monkeypatch.setenv("POKROV_SUPPORT_MODE_CODE_SECRET", "c" * 48)
    api = _load_api(monkeypatch, tmp_path)
    from models import AdminActionIntent, SupportModePolicy, SupportTicket

    db = api.SessionLocal()
    try:
        ticket = SupportTicket(
            user_tg_id=1001,
            account_id="11111111-1111-4111-8111-111111111111",
            environment="test",
            status="open",
            subject="Temporary support mode",
            priority="normal",
            queue="general",
            version=1,
        )
        db.add(ticket)
        db.commit()
        ticket_id = int(ticket.id)
    finally:
        db.close()

    client = TestClient(api.app, base_url="https://api.pokrov.test")
    bootstrap = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert bootstrap.status_code == 200, bootstrap.text
    csrf = bootstrap.json()["data"]["session"]["csrf_token"]
    command = {
        "action": "support.mode.issue",
        "target": {"type": "ticket", "id": str(ticket_id)},
        "payload": {
            "expected_version": 1,
            "allowed_categories": ["build", "events", "network", "redaction"],
            "allowed_collectors": [
                "build_summary",
                "network_summary",
                "operational_events",
                "redaction_report",
            ],
            "app_version": "1.2.0+30",
            "build_number": "candidate-local-30",
            "maximum_bundle_bytes": 1048576,
            "maximum_bundles": 2,
            "maximum_total_bytes": 1572864,
            "platform": "windows",
            "ttl_minutes": 20,
        },
    }
    prepared = client.post(
        "/api/admin/v2/support/action-intents",
        headers={"X-Pokrov-Admin-CSRF": csrf},
        json=command,
    )
    assert prepared.status_code == 200, prepared.text
    intent = prepared.json()["data"]
    execution_headers = {
        "X-Pokrov-Admin-CSRF": csrf,
        "X-Admin-Idempotency-Key": "22111111-1111-4111-8111-111111111111",
        "X-Admin-Confirmation-SHA256": hashlib.sha256(
            intent["confirmation_challenge"].encode("utf-8")
        ).hexdigest(),
    }
    executed = client.post(
        f"/api/admin/v2/support/action-intents/{intent['intent_id']}/execute",
        headers=execution_headers,
        json=command,
    )
    assert executed.status_code == 200, executed.text
    data = executed.json()["data"]
    assert data["activation_code"].startswith("PSM1-")
    assert data["support_mode"]["maximum_bundles"] == 2

    replay = client.post(
        f"/api/admin/v2/support/action-intents/{intent['intent_id']}/execute",
        headers=execution_headers,
        json=command,
    )
    assert replay.status_code == 200, replay.text
    assert replay.json()["data"]["activation_code"] == data["activation_code"]

    with api.SessionLocal() as check:
        policy = check.query(SupportModePolicy).one()
        stored_intent = check.query(AdminActionIntent).filter_by(id=intent["intent_id"]).one()
        assert data["activation_code"] not in policy.activation_code_hash
        assert data["activation_code"] not in stored_intent.result_summary_json

    decoded = client.get(
        "/api/admin/v2/support/diagnostic-codes/PSD1-6C4Q-J082-00FA-QK8B"
    )
    assert decoded.status_code == 200, decoded.text
    assert decoded.json()["data"]["contains_identity"] is False
    assert decoded.json()["data"]["connection_state"] == "degraded"


def test_admin_v2_support_search_and_bundle_download_are_scoped_single_use_and_audited(
    monkeypatch, tmp_path
) -> None:
    accepted = tmp_path / "accepted-support-v2"
    accepted.mkdir()
    monkeypatch.setenv("POKROV_SUPPORT_BUNDLE_ACCEPTED_DIR", str(accepted))
    api = _load_api(monkeypatch, tmp_path)
    from models import Event, SupportBundleAccessAudit, SupportBundleUpload, User
    from tickets_repo import create_ticket

    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    payload = b"encrypted-admin-v2-support-object"
    upload_id = str(uuid.uuid4())
    object_name = f"{upload_id}.pokrov-support"
    db = api.SessionLocal()
    try:
        db.add(
            User(
                tg_id=1001,
                uuid=str(uuid.uuid4()),
                email="bundle-v2@example.test",
                sub_type="paid",
                is_active=True,
                sub_token="bundle-v2-test-token",
            )
        )
        ticket = create_ticket(db, user_tg_id=1001, subject="Bundle lookup")
        ticket.environment = "test"
        ticket.queue = "connection"
        db.flush()
        ticket_id = int(ticket.id)
        db.add(
            Event(
                tg_id=1001,
                event_name="dns_probe_failed",
                source="client",
                platform="windows",
                app_version="1.2.0",
                build_number="42",
                subsystem="dns",
                stage="dns_probe",
                result="failure",
                error_code="DNS-001",
                trace_id="corr-admin-v2-501",
                occurred_at=now,
                received_at=now,
            )
        )
        db.add(
            SupportBundleUpload(
                upload_id=upload_id,
                ticket_id=ticket_id,
                owner_tg_id=1001,
                owner_binding_hash=hashlib.sha256(upload_id.encode()).hexdigest(),
                idempotency_key=f"admin-v2-{upload_id}",
                bundle_id="private-client-bundle-id",
                expected_size_bytes=len(payload),
                expected_sha256=hashlib.sha256(payload).hexdigest(),
                content_type="application/octet-stream",
                received_size_bytes=len(payload),
                status="validated",
                object_name=object_name,
                diagnostic_profile="standard",
                app_version="1.2.0",
                build_number="42",
                platform="windows",
                last_phase="dns_probe",
                last_error_code="DNS-001",
                proof_outcome="failure",
                expires_at=now + timedelta(days=7),
                completed_at=now,
                validated_at=now,
            )
        )
        db.commit()
    finally:
        db.close()
    (accepted / object_name).write_bytes(payload)

    client = TestClient(api.app, base_url="https://api.pokrov.test")
    bootstrap = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert bootstrap.status_code == 200, bootstrap.text
    csrf = bootstrap.json()["data"]["session"]["csrf_token"]

    detail = client.get(f"/api/admin/v2/support/tickets/{ticket_id}")
    assert detail.status_code == 200, detail.text
    bundle_ref = detail.json()["data"]["support_bundles"][0]["bundle_ref"]
    for query, expected_kind in (
        (f"#{ticket_id}", "case"),
        (bundle_ref, "support_bundle"),
        ("corr-admin-v2-501", "correlation"),
    ):
        response = client.get("/api/admin/v2/support/search", params={"q": query})
        assert response.status_code == 200, response.text
        assert response.json()["data"]["results"][0]["kind"] == expected_kind
        assert response.json()["data"]["results"][0]["href"] == f"/tickets?selected={ticket_id}"
    assert upload_id not in client.get(
        "/api/admin/v2/support/search", params={"q": bundle_ref}
    ).text

    known = client.get(
        "/api/admin/v2/support/known-issues",
        params={
            "error_code": "DNS-001",
            "app_version": "1.2.0",
            "build_number": "42",
            "platform": "windows",
        },
    )
    assert known.status_code == 200, known.text
    assert known.json()["data"] == {"issues": [], "count": 0}

    grant_path = f"/api/admin/v2/support/tickets/{ticket_id}/bundles/{bundle_ref}/access-grants"
    denied = client.post(
        grant_path,
        headers={"X-Pokrov-Admin-CSRF": csrf},
        json={"reason_code": "incident_review"},
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "operator_step_up_required"

    step_up = client.post(
        "/api/admin/v2/auth/step-up",
        headers={**_admin_headers(), "X-Pokrov-Admin-CSRF": csrf},
    )
    assert step_up.status_code == 200, step_up.text
    issued = client.post(
        grant_path,
        headers={"X-Pokrov-Admin-CSRF": csrf},
        json={"reason_code": "incident_review"},
    )
    assert issued.status_code == 200, issued.text
    token = issued.json()["data"]["access_grant"]
    content_path = f"/api/admin/v2/support/tickets/{ticket_id}/bundles/{bundle_ref}/content"
    downloaded = client.get(
        content_path,
        headers={"X-Pokrov-Support-Grant": token},
    )
    assert downloaded.status_code == 200, downloaded.text
    assert downloaded.content == payload
    assert downloaded.headers["cache-control"] == "no-store"
    replay = client.get(
        content_path,
        headers={"X-Pokrov-Support-Grant": token},
    )
    assert replay.status_code == 403

    db = api.SessionLocal()
    try:
        audits = db.query(SupportBundleAccessAudit).order_by(
            SupportBundleAccessAudit.created_at.asc()
        ).all()
        assert [row.action for row in audits] == ["grant_issued", "downloaded"]
        assert all(row.actor_tg_id == 9999 for row in audits)
        assert all(row.actor_role == "superadmin" for row in audits)
        assert all(row.reason_code == "incident_review" for row in audits)
        assert all(row.created_at is not None for row in audits)
    finally:
        db.close()


def test_admin_v2_release_cockpit_and_news_use_guarded_v2_contracts(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("APP_ANDROID_VERSION", "1.2.0")
    monkeypatch.setenv("APP_ANDROID_MIN_SUPPORTED_VERSION", "1.1.0")
    monkeypatch.setenv(
        "APP_ANDROID_APK_URL",
        "https://github.com/Kiwunaka/pokrov/releases/download/v1.2.0/pokrov-android-universal.apk",
    )
    api = _load_api(monkeypatch, tmp_path, operator_environment="production")
    client = TestClient(api.app, base_url="https://api.pokrov.test")
    bootstrap = client.post("/api/admin/v2/auth/bootstrap", headers=_admin_headers())
    assert bootstrap.status_code == 200, bootstrap.text
    csrf = bootstrap.json()["data"]["session"]["csrf_token"]
    unsafe = {"X-Pokrov-Admin-CSRF": csrf}

    from models import NewsDraft, ReleaseCandidate, ReleaseOriginEvidence, User
    from operator_release_service import RELEASE_GATE_NAMES

    candidate_id = "c" * 64
    now = _utcnow()
    descriptor = {
        "component": "client",
        "version": "1.2.0",
        "revision": "d" * 40,
        "artifact_sha256": "e" * 64,
    }
    db = api.SessionLocal()
    try:
        db.add(
            ReleaseCandidate(
                candidate_id=candidate_id,
                component="client",
                version="1.2.0",
                revision="d" * 40,
                artifact_sha256="e" * 64,
                canonical_descriptor_json=json.dumps(descriptor, sort_keys=True),
                descriptor_sha256=hashlib.sha256(
                    json.dumps(descriptor, sort_keys=True).encode("utf-8")
                ).hexdigest(),
                ingest_key_id="admin-v2-test",
                imported_at=now,
            )
        )
        checks = [
            ("current", "current_origin_reachability"),
            ("brain", "brain_origin_reachability"),
            ("ru", "ru_origin_reachability"),
            *(("current", name) for name in RELEASE_GATE_NAMES),
        ]
        for origin, check_name in checks:
            db.add(
                ReleaseOriginEvidence(
                    candidate_id=candidate_id,
                    origin=origin,
                    check_name=check_name,
                    status="PASS",
                    evidence_sha256=hashlib.sha256(
                        f"{origin}:{check_name}".encode("utf-8")
                    ).hexdigest(),
                    observed_at=now,
                    detail_json='{"source":"retained-test"}',
                    imported_at=now,
                )
            )
        draft = NewsDraft(
            source_name="Test source",
            source_url="https://example.test/source",
            source_title="Release source title",
            source_item_sha256="f" * 64,
            fetch_run_id="admin-v2-news",
            status="pending",
            discovered_at=now,
        )
        db.add(draft)
        db.add(
            User(
                tg_id=7401,
                uuid="00000000-0000-4000-8000-000000007401",
                email="v2-broadcast@example.test",
                sub_type="PAID",
                created_at=now,
                expiry_at=now + timedelta(days=30),
                is_active=True,
                sub_token="v2-broadcast-token",
            )
        )
        db.commit()
        draft_id = int(draft.id)
    finally:
        db.close()

    candidates = client.get("/api/admin/v2/releases/candidates")
    assert candidates.status_code == 200, candidates.text
    assert candidates.json()["data"]["items"][0]["candidate_id"] == candidate_id
    cockpit = client.get(f"/api/admin/v2/releases/candidates/{candidate_id}/cockpit")
    assert cockpit.status_code == 200, cockpit.text
    assert cockpit.json()["data"]["gate_matrix"]["status"] == "PASS"
    assert cockpit.json()["data"]["gate_matrix"]["gate_f_decision"] == "NOT_EVALUATED"
    assert cockpit.json()["data"]["gate_matrix"]["policy_version"] == "pokrov.operator-cockpit-gates/v1"
    assert cockpit.json()["data"]["components"][0]["revision"] == "d" * 40

    step_up = client.post(
        "/api/admin/v2/auth/step-up",
        headers={**unsafe, **_admin_headers()},
    )
    assert step_up.status_code == 200, step_up.text
    rollout_command = {
        "action": "release.rollout.start",
        "target": {"type": "release_candidate", "id": candidate_id},
        "payload": {
            "platform": "android",
            "rollout_percent": 15,
            "min_supported_version": "1.1.0",
            "observation_hours": 24,
            "thresholds": {
                "crash_failures": 0,
                "connect_failures": 0,
                "update_failures": 0,
            },
        },
    }
    prepared = client.post(
        "/api/admin/v2/releases/action-intents", headers=unsafe, json=rollout_command
    )
    assert prepared.status_code == 200, prepared.text
    intent = prepared.json()["data"]
    executed = client.post(
        f"/api/admin/v2/releases/action-intents/{intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": str(uuid.uuid4()),
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                candidate_id.encode("utf-8")
            ).hexdigest(),
        },
        json=rollout_command,
    )
    assert executed.status_code == 200, executed.text
    assert executed.json()["data"]["rollout"]["rollout_percent"] == 15
    public_apps = client.get("/api/public/client-apps?platform=android&current_version=1.1.0")
    assert public_apps.status_code == 200, public_apps.text
    assert public_apps.json()["android"]["update"]["rollout_percent"] == 15
    pause_command = {
        "action": "release.rollout.pause",
        "target": {"type": "release_candidate", "id": candidate_id},
        "payload": {"platform": "android"},
    }
    pause_prepared = client.post(
        "/api/admin/v2/releases/action-intents", headers=unsafe, json=pause_command
    )
    assert pause_prepared.status_code == 200, pause_prepared.text
    pause_intent = pause_prepared.json()["data"]
    paused = client.post(
        f"/api/admin/v2/releases/action-intents/{pause_intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": str(uuid.uuid4()),
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                pause_intent["confirmation_challenge"].encode("utf-8")
            ).hexdigest(),
        },
        json=pause_command,
    )
    assert paused.status_code == 200, paused.text
    paused_apps = client.get("/api/public/client-apps?platform=android&current_version=1.1.0")
    assert paused_apps.status_code == 200, paused_apps.text
    assert paused_apps.json()["android"]["update"]["rollout_percent"] == 0
    assert paused_apps.json()["android"]["update"]["update_policy"] == "none"

    from telegram_delivery_service import TelegramDeliveryResult

    async def delivered(_chat_id: int, _message: str, **_kwargs):
        return TelegramDeliveryResult(
            sent=True,
            reason_code="sent",
            retryable=False,
            duration_ms=7,
            http_status=200,
            message_id=501,
        )

    monkeypatch.setattr(api, "_telegram_send_message_detailed", delivered)
    broadcast_command = {
        "action": "broadcast.send",
        "target": {"type": "broadcast", "id": "broadcast"},
        "payload": {
            "segment": "custom",
            "limit": 10,
            "tg_ids": [7401],
            "text": "Проверка v2 delivery",
        },
    }
    broadcast_prepared = client.post(
        "/api/admin/v2/growth/action-intents", headers=unsafe, json=broadcast_command
    )
    assert broadcast_prepared.status_code == 200, broadcast_prepared.text
    broadcast_intent = broadcast_prepared.json()["data"]
    broadcast_executed = client.post(
        f"/api/admin/v2/growth/action-intents/{broadcast_intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": str(uuid.uuid4()),
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                "ОТПРАВИТЬ".encode("utf-8")
            ).hexdigest(),
        },
        json=broadcast_command,
    )
    assert broadcast_executed.status_code == 200, broadcast_executed.text
    delivery = client.get(
        f"/api/admin/v2/growth/broadcasts/{broadcast_intent['intent_id']}/delivery"
    )
    assert delivery.status_code == 200, delivery.text
    assert delivery.json()["data"]["delivered"] == 1
    assert delivery.json()["data"]["retry_scope"] == "failed_retryable_only"
    broadcast_status = client.get(
        f"/api/admin/v2/growth/action-intents/{broadcast_intent['intent_id']}"
    )
    assert broadcast_status.status_code == 200, broadcast_status.text
    assert broadcast_status.json()["data"]["status"] == "completed"

    drafts = client.get("/api/admin/v2/growth/news-drafts?status=pending")
    assert drafts.status_code == 200, drafts.text
    assert drafts.json()["data"]["drafts"][0]["id"] == draft_id
    news_command = {
        "action": "live_update.create",
        "target": {"type": "live_update", "id": "new"},
        "payload": {
            "source_draft_id": draft_id,
            "title": "Проверенный заголовок",
            "summary": "Проверенная оператором краткая выжимка для пользователей POKROV.",
            "link": "https://example.test/source",
            "is_active": True,
            "sort_order": 100,
        },
    }
    news_prepared = client.post(
        "/api/admin/v2/growth/action-intents", headers=unsafe, json=news_command
    )
    assert news_prepared.status_code == 200, news_prepared.text
    news_intent = news_prepared.json()["data"]
    news_executed = client.post(
        f"/api/admin/v2/growth/action-intents/{news_intent['intent_id']}/execute",
        headers={
            **unsafe,
            "X-Admin-Idempotency-Key": str(uuid.uuid4()),
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                news_intent["confirmation_challenge"].encode("utf-8")
            ).hexdigest(),
        },
        json=news_command,
    )
    assert news_executed.status_code == 200, news_executed.text
    updates = client.get("/api/admin/v2/growth/live-updates")
    assert updates.status_code == 200, updates.text
    assert updates.json()["data"]["updates"][0]["source_draft_id"] == draft_id

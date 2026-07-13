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
        "worker",
    ]:
        sys.modules.pop(name, None)

    return importlib.import_module("api")


def _admin_headers() -> dict[str, str]:
    return {"X-Telegram-Init-Data": _sign_telegram_init_data(bot_token="test_bot_token_123")}


def _gb(value: float) -> int:
    return int(value * 1024 * 1024 * 1024)


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
    assert free_body["facts"]["node_pool"] == "NL-free"
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
    assert known["raw_ip_exposed"] is False
    assert known["online_connections_now"] == 2
    assert "manual_review" in known["risk_flags"]
    assert "multi_ip" in known["risk_flags"]
    assert "observer:watch" in known["risk_flags"]
    assert "203.0.113.77" not in response.text
    assert "198.51.100.42" not in response.text


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

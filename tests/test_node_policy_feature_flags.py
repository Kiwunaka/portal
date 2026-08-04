from __future__ import annotations

import importlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def _reload_node_policy(monkeypatch, **env):
    for key, value in env.items():
        monkeypatch.setenv(key, str(value))
    sys.modules.pop("node_policy", None)
    return importlib.import_module("node_policy")


def _node(code: str, **overrides):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    values = {
        "code": code,
        "enabled": True,
        "accepting_new_clients": True,
        "is_draining": False,
        "is_healthy": True,
        "health_score": 80.0,
        "weight": 100,
        "cpu_percent": 10.0,
        "last_health_at": now,
        "last_ok_at": now,
        "last_probe_at": now,
        "network_tx_mbps_1m": 0.0,
        "network_tx_mbps_5m": 0.0,
        "packet_loss_percent": 0.0,
        "tcp_retrans_percent": 0.0,
        "dataplane_ok": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_capacity_flag_falls_back_to_legacy_health_weight_order(monkeypatch):
    node_policy = _reload_node_policy(monkeypatch, CAPACITY_AWARE_NODE_SELECTION="false")

    saturated = _node("high-health-saturated", health_score=99.0, weight=10, network_tx_mbps_1m=950.0)
    lower_health = _node("lower-health", health_score=75.0, weight=500, network_tx_mbps_1m=0.0)

    ranked = node_policy.rank_nodes_for_app([lower_health, saturated])

    assert [node.code for node in ranked] == ["high-health-saturated", "lower-health"]


def test_authenticated_egress_enforcement_defaults_off(monkeypatch):
    monkeypatch.delenv("AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED", raising=False)

    node_policy = _reload_node_policy(monkeypatch)

    assert node_policy.AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED is False


def test_subscription_flags_can_return_legacy_order_without_hard_exclusion(monkeypatch):
    node_policy = _reload_node_policy(
        monkeypatch,
        SUBSCRIPTION_DYNAMIC_ORDERING="false",
        SUBSCRIPTION_EXCLUDE_HARD_REJECT="false",
    )

    stale = _node(
        "stale-high-health",
        health_score=99.0,
        weight=100,
        last_health_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2),
    )
    healthy = _node("healthy-lower-health", health_score=80.0, weight=100)

    ranked = node_policy.rank_nodes_for_subscription([healthy, stale])

    assert [node.code for node in ranked] == ["stale-high-health", "healthy-lower-health"]


def test_subscription_default_keeps_low_health_nodes_as_fallback_choices(monkeypatch):
    node_policy = _reload_node_policy(monkeypatch)

    healthy = _node("healthy", health_score=82.0, weight=100)
    low_health = _node("low-health", health_score=45.0, weight=100)

    ranked = node_policy.rank_nodes_for_subscription([low_health, healthy])
    capacity = node_policy.node_capacity_status(low_health)

    assert [node.code for node in ranked] == ["healthy", "low-health"]
    assert node_policy.node_hard_reject_reason(low_health) is None
    assert capacity["state"] == "healthy"
    assert capacity["reject_reason"] is None
    assert node_policy.node_backend_penalty(low_health) > node_policy.node_backend_penalty(healthy)


def test_subscription_default_excludes_explicit_hard_reject(monkeypatch):
    node_policy = _reload_node_policy(monkeypatch)

    healthy = _node("healthy")
    failed = _node("failed", is_healthy=False)

    assert [node.code for node in node_policy.rank_nodes_for_subscription([failed, healthy])] == ["healthy"]


def test_manual_country_ranking_keeps_low_health_as_penalized_fallback(monkeypatch):
    node_policy = _reload_node_policy(monkeypatch)

    healthy = _node("healthy", health_score=82.0, weight=100)
    low_health = _node("low-health", health_score=45.0, weight=100)

    ranked = node_policy.rank_nodes_for_manual_country([low_health, healthy])

    assert [node.code for node in ranked] == ["healthy", "low-health"]
    assert node_policy.node_capacity_state(low_health) == "healthy"


def test_capacity_state_contract_uses_plan_default_cpu_reject(monkeypatch):
    node_policy = _reload_node_policy(monkeypatch)

    hot = _node("hot", cpu_percent=85.0)

    assert node_policy.SMART_CONNECT_CPU_REJECT_PERCENT == 85.0
    assert node_policy.node_capacity_state(hot) == "hard_reject"
    assert node_policy.node_hard_reject_reason(hot) == "cpu_hot"


def test_manual_country_ranking_keeps_soft_drain_but_excludes_hard_reject(monkeypatch):
    node_policy = _reload_node_policy(monkeypatch)

    healthy = _node("healthy", network_tx_mbps_1m=100.0)
    soft_drain = _node("soft-drain", network_tx_mbps_1m=830.0)
    hard_reject = _node("hard", network_tx_mbps_1m=950.0)

    ranked = node_policy.rank_nodes_for_manual_country([hard_reject, soft_drain, healthy])

    assert [node.code for node in ranked] == ["healthy", "soft-drain"]
    assert node_policy.node_capacity_state(soft_drain) == "drain"


def test_key_pressure_ranking_prefers_fair_use_pool(monkeypatch):
    node_policy = _reload_node_policy(monkeypatch)

    premium = _node("premium", health_score=99.0, pool_code="premium_pool")
    fair_use = _node("fair-use", health_score=80.0, pool_code="fair_use_pool")

    ranked = node_policy.rank_nodes_for_key_pressure([premium, fair_use])

    assert [node.code for node in ranked] == ["fair-use", "premium"]

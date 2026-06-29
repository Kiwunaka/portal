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

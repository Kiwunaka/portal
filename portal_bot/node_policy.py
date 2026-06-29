from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any


FREE_NODE_CODE_PREFERENCES = ("nl-free", "nl_free", "free", "pl_free")
_PREMIUM_PLAN_CODES = {"trial", "channel_bonus", "start_99"}


def _env_int(name: str, default: int, *, minimum: int = 0, maximum: int = 1_000_000) -> int:
    try:
        value = int(str(os.getenv(name) or "").strip() or default)
    except Exception:
        value = default
    return max(minimum, min(maximum, value))


def _env_float(name: str, default: float, *, minimum: float = 0.0, maximum: float = 1_000_000.0) -> float:
    try:
        value = float(str(os.getenv(name) or "").strip() or default)
    except Exception:
        value = default
    return max(minimum, min(maximum, value))


def _env_bool(name: str, default: bool) -> bool:
    raw = str(os.getenv(name) or "").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return bool(default)


CAPACITY_AWARE_NODE_SELECTION = _env_bool("CAPACITY_AWARE_NODE_SELECTION", True)
SUBSCRIPTION_DYNAMIC_ORDERING = _env_bool("SUBSCRIPTION_DYNAMIC_ORDERING", True)
SUBSCRIPTION_EXCLUDE_HARD_REJECT = _env_bool("SUBSCRIPTION_EXCLUDE_HARD_REJECT", True)
KEY_PRESSURE_SCORING = _env_bool("KEY_PRESSURE_SCORING", True)
KEY_PRESSURE_FAIR_USE_ROUTING = _env_bool("KEY_PRESSURE_FAIR_USE_ROUTING", False)
USERNODE_MAPPING_AS_CANDIDATE_LIMIT = _env_bool("USERNODE_MAPPING_AS_CANDIDATE_LIMIT", False)
SMART_CONNECT_SHORTLIST_LIMIT = _env_int("SMART_CONNECT_SHORTLIST_LIMIT", 8, minimum=1, maximum=32)
SMART_CONNECT_STICKINESS_THRESHOLD_PERCENT = _env_int("SMART_CONNECT_STICKINESS_THRESHOLD_PERCENT", 20, minimum=0, maximum=100)
SMART_CONNECT_STALE_AFTER_SECONDS = _env_int("SMART_CONNECT_STALE_AFTER_SECONDS", 180, minimum=60, maximum=86_400)
SMART_CONNECT_CPU_REJECT_PERCENT = _env_float("SMART_CONNECT_CPU_REJECT_PERCENT", 90.0, minimum=1.0, maximum=100.0)
SMART_CONNECT_CPU_SOFT_PERCENT = _env_float("SMART_CONNECT_CPU_SOFT_PERCENT", 75.0, minimum=1.0, maximum=100.0)
SMART_CONNECT_TX_SOFT_RATIO = _env_float("SMART_CONNECT_TX_SOFT_RATIO", 0.70, minimum=0.01, maximum=10.0)
SMART_CONNECT_TX_DRAIN_RATIO = _env_float("SMART_CONNECT_TX_DRAIN_RATIO", 0.82, minimum=0.01, maximum=10.0)
SMART_CONNECT_TX_HARD_RATIO = _env_float("SMART_CONNECT_TX_HARD_RATIO", 0.92, minimum=0.01, maximum=10.0)
SMART_CONNECT_MAX_PACKET_LOSS_PERCENT = _env_float("SMART_CONNECT_MAX_PACKET_LOSS_PERCENT", 2.0, minimum=0.0, maximum=100.0)
SMART_CONNECT_MAX_TCP_RETRANS_PERCENT = _env_float("SMART_CONNECT_MAX_TCP_RETRANS_PERCENT", 5.0, minimum=0.0, maximum=100.0)
SMART_CONNECT_DEFAULT_PORT_CAPACITY_MBPS = _env_float("NODE_METRICS_PORT_CAPACITY_MBPS", 1000.0, minimum=0.0)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalize_utc_naive(value: datetime | None) -> datetime | None:
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def node_code(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return str(getattr(value, "code", "") or "").strip()


def node_code_base(code: str) -> str:
    raw = str(code or "").lower().strip()
    for sep in ("_", "-", "."):
        if sep in raw:
            raw = raw.split(sep, 1)[0]
    return raw


def node_is_free(value: Any) -> bool:
    return "free" in node_code(value).lower()


def node_is_delivery_ready(node: Any) -> bool:
    return bool(getattr(node, "enabled", True)) and bool(getattr(node, "accepting_new_clients", True)) and not bool(
        getattr(node, "is_draining", False)
    )


def node_last_freshness_at(node: Any) -> datetime | None:
    for attr in ("last_health_at", "last_probe_at", "last_ok_at"):
        value = getattr(node, attr, None)
        if isinstance(value, datetime):
            return _normalize_utc_naive(value)
    return None


def node_is_stale(
    node: Any,
    *,
    now: datetime | None = None,
    stale_after_seconds: int = SMART_CONNECT_STALE_AFTER_SECONDS,
) -> bool:
    sample_at = node_last_freshness_at(node)
    if sample_at is None:
        return True
    current = _normalize_utc_naive(now) or _utcnow()
    return (current - sample_at).total_seconds() > max(60, int(stale_after_seconds))


def node_cpu_penalty(node: Any) -> int | None:
    try:
        cpu_percent = float(getattr(node, "cpu_percent", 0.0) or 0.0)
    except Exception:
        cpu_percent = 0.0
    if cpu_percent >= SMART_CONNECT_CPU_REJECT_PERCENT:
        return None
    if cpu_percent >= 85.0:
        return 120
    if cpu_percent >= 75.0:
        return 60
    if cpu_percent >= 60.0:
        return 20
    return 0


def node_backend_penalty(node: Any) -> int | None:
    try:
        health_score = float(getattr(node, "health_score", 0.0) or 0.0)
    except Exception:
        health_score = 0.0
    if health_score < 60.0:
        return None
    if health_score < 75.0:
        return 80
    if health_score < 90.0:
        return 30
    return 0


def _float_attr(node: Any, attr: str, default: float = 0.0) -> float:
    try:
        return float(getattr(node, attr, default) or default)
    except Exception:
        return float(default)


def _int_attr(node: Any, attr: str, default: int = 0) -> int:
    try:
        return int(getattr(node, attr, default) or default)
    except Exception:
        return int(default)


def _policy_float(policy: Any, attr: str, default: float) -> float:
    if policy is None:
        return float(default)
    try:
        value = getattr(policy, attr, None)
        if value is None:
            return float(default)
        return float(value)
    except Exception:
        return float(default)


def _policy_int(policy: Any, attr: str, default: int) -> int:
    if policy is None:
        return int(default)
    try:
        value = getattr(policy, attr, None)
        if value is None:
            return int(default)
        return int(value)
    except Exception:
        return int(default)


def node_capacity_mbps(node: Any, policy: Any | None = None) -> float:
    configured = _policy_float(policy, "max_tx_mbps", 0.0)
    if configured > 0:
        return configured
    direct = _float_attr(node, "max_tx_mbps", 0.0)
    if direct > 0:
        return direct
    return float(SMART_CONNECT_DEFAULT_PORT_CAPACITY_MBPS or 0.0)


def node_tx_mbps(node: Any) -> float:
    for attr in ("network_tx_mbps_1m", "network_tx_mbps_5m", "network_tx_mbps", "network_total_mbps"):
        value = _float_attr(node, attr, 0.0)
        if value > 0:
            return value
    return 0.0


def node_tx_ratio(node: Any, policy: Any | None = None) -> float | None:
    capacity = node_capacity_mbps(node, policy)
    if capacity <= 0:
        return None
    return max(0.0, node_tx_mbps(node) / capacity)


def node_capacity_status(
    node: Any,
    *,
    policy: Any | None = None,
    now: datetime | None = None,
    stale_after_seconds: int | None = None,
) -> dict[str, Any]:
    stale_after = int(stale_after_seconds or _policy_int(policy, "stale_after_seconds", SMART_CONNECT_STALE_AFTER_SECONDS))
    tx_ratio = node_tx_ratio(node, policy)
    tx_soft = _policy_float(policy, "soft_tx_ratio", SMART_CONNECT_TX_SOFT_RATIO)
    tx_drain = _policy_float(policy, "drain_tx_ratio", SMART_CONNECT_TX_DRAIN_RATIO)
    tx_hard = _policy_float(policy, "hard_tx_ratio", SMART_CONNECT_TX_HARD_RATIO)
    cpu_soft = _policy_float(policy, "soft_cpu_percent", SMART_CONNECT_CPU_SOFT_PERCENT)
    cpu_hard = _policy_float(policy, "hard_cpu_percent", SMART_CONNECT_CPU_REJECT_PERCENT)
    packet_loss_limit = _policy_float(policy, "max_packet_loss_percent", SMART_CONNECT_MAX_PACKET_LOSS_PERCENT)
    retrans_limit = _policy_float(policy, "max_tcp_retrans_percent", SMART_CONNECT_MAX_TCP_RETRANS_PERCENT)

    reason: str | None = None
    state = "healthy"
    if not bool(getattr(node, "enabled", True)):
        reason = "disabled"
    elif not bool(getattr(node, "accepting_new_clients", True)):
        reason = "not_accepting_new_clients"
    elif bool(getattr(node, "is_draining", False)):
        reason = "draining"
    elif not bool(getattr(node, "is_healthy", True)):
        reason = "unhealthy"
    elif node_is_stale(node, now=now, stale_after_seconds=stale_after):
        reason = "stale"
    elif getattr(node, "dataplane_ok", None) is False:
        reason = "dataplane_down"
    elif _float_attr(node, "cpu_percent", 0.0) >= cpu_hard:
        reason = "cpu_hot"
    elif tx_ratio is not None and tx_ratio >= tx_hard:
        reason = "network_saturated"
    elif packet_loss_limit > 0 and _float_attr(node, "packet_loss_percent", 0.0) >= packet_loss_limit:
        reason = "packet_loss"
    elif retrans_limit > 0 and _float_attr(node, "tcp_retrans_percent", 0.0) >= retrans_limit:
        reason = "tcp_retrans"
    elif node_backend_penalty(node) is None:
        reason = "health_score_low"

    if reason:
        state = "hard_reject"
    elif tx_ratio is not None and tx_ratio >= tx_drain:
        state = "drain"
    elif tx_ratio is not None and tx_ratio >= tx_soft:
        state = "warm"
    elif _float_attr(node, "cpu_percent", 0.0) >= cpu_soft:
        state = "warm"

    score = node_selection_score(node, policy=policy, client_rtt_ms=None)
    return {
        "state": state,
        "reject_reason": reason,
        "score": float(score),
        "tx_mbps": node_tx_mbps(node),
        "tx_ratio": tx_ratio,
        "capacity_mbps": node_capacity_mbps(node, policy),
        "provisioned_clients_count": _int_attr(node, "provisioned_clients_count", _int_attr(node, "active_clients", 0)),
        "online_connections_hint": _int_attr(node, "online_connections_hint", 0),
    }


def node_hard_reject_reason(
    node: Any,
    *,
    policy: Any | None = None,
    now: datetime | None = None,
    stale_after_seconds: int | None = None,
) -> str | None:
    return str(
        node_capacity_status(
            node,
            policy=policy,
            now=now,
            stale_after_seconds=stale_after_seconds,
        ).get("reject_reason")
        or ""
    ) or None


def node_selection_score(
    node: Any,
    *,
    policy: Any | None = None,
    client_rtt_ms: int | None = None,
) -> float:
    score = 0.0
    score += float(client_rtt_ms or 0)
    score += float(_int_attr(node, "dataplane_rtt_ms", 0))
    score += float(_int_attr(node, "panel_latency_ms", 0) or 0) * 0.35
    backend = node_backend_penalty(node)
    if backend is None:
        score += 10_000
    else:
        score += float(backend)
        score -= max(0.0, min(_float_attr(node, "health_score", 0.0), 100.0)) / 20.0
    cpu = node_cpu_penalty(node)
    if cpu is None:
        score += 10_000
    else:
        score += float(cpu)
    tx_ratio = node_tx_ratio(node, policy)
    if tx_ratio is not None:
        if tx_ratio >= SMART_CONNECT_TX_HARD_RATIO:
            score += 10_000
        else:
            score += max(0.0, tx_ratio) * 180.0
    score += _float_attr(node, "packet_loss_percent", 0.0) * 80.0
    score += _float_attr(node, "tcp_retrans_percent", 0.0) * 25.0
    weight = _policy_int(policy, "rank_weight", _int_attr(node, "weight", 100))
    score -= max(0, min(500, weight)) / 10.0
    if str(getattr(node, "capacity_state", "") or "").strip().lower() == "warm":
        score += 40.0
    return round(score, 3)


def legacy_node_rank_key(node: Any) -> tuple[float, int, str]:
    return (
        -max(0.0, min(_float_attr(node, "health_score", 0.0), 100.0)),
        -_int_attr(node, "weight", 0),
        node_code(node).lower(),
    )


def rank_nodes_legacy(nodes: list[Any]) -> list[Any]:
    return sorted(list(nodes), key=legacy_node_rank_key)


def rank_nodes_for_app(
    nodes: list[Any],
    *,
    client_rtt_by_code: dict[str, int] | None = None,
    policy_by_code: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> list[Any]:
    if not CAPACITY_AWARE_NODE_SELECTION:
        return rank_nodes_legacy(nodes)

    rtt = {str(k or "").strip().lower(): int(v) for k, v in dict(client_rtt_by_code or {}).items() if str(k or "").strip()}
    policies = {str(k or "").strip().lower(): v for k, v in dict(policy_by_code or {}).items() if str(k or "").strip()}

    def key(node: Any) -> tuple[float, str]:
        code = node_code(node).lower()
        policy = policies.get(code)
        reason = node_hard_reject_reason(node, policy=policy, now=now)
        reject_penalty = 1_000_000.0 if reason else 0.0
        return (
            reject_penalty
            + node_selection_score(node, policy=policy, client_rtt_ms=rtt.get(code)),
            code,
        )

    return sorted(list(nodes), key=key)


def rank_nodes_for_subscription(
    nodes: list[Any],
    *,
    policy_by_code: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> list[Any]:
    ranked = (
        rank_nodes_for_app(nodes, policy_by_code=policy_by_code, now=now)
        if SUBSCRIPTION_DYNAMIC_ORDERING
        else rank_nodes_legacy(nodes)
    )
    if not SUBSCRIPTION_EXCLUDE_HARD_REJECT:
        return ranked
    return [
        node
        for node in ranked
        if not node_hard_reject_reason(
            node,
            policy=(policy_by_code or {}).get(node_code(node).lower()) if policy_by_code else None,
            now=now,
        )
    ]


def user_uses_free_pool(user: Any) -> bool:
    sub_type = str(getattr(user, "sub_type", "") or "").strip().upper()
    plan_code = str(getattr(user, "current_plan_code", "") or "").strip().lower()

    if plan_code in _PREMIUM_PLAN_CODES:
        return False
    if sub_type == "FREE":
        return True
    if sub_type in {"", "PENDING"}:
        return True
    if sub_type.startswith("TRIAL"):
        return False
    if sub_type.startswith("BONUS") or sub_type in {"CHANNEL_BONUS", "OPENING_BONUS", "FRIEND_GIFT"}:
        return False
    if sub_type in {"MANUAL", "PAID", "VIP", "PRO", "BASIC", "MONTHLY", "QUARTERLY", "HALF_YEAR", "YEARLY"}:
        return False
    if sub_type.startswith("PAID_") or sub_type.startswith("PREMIUM"):
        return False
    return True


def canonical_free_node_code(nodes: list[Any]) -> str | None:
    pools = (
        [node for node in nodes if node_is_free(node) and node_is_delivery_ready(node)],
        [node for node in nodes if node_is_free(node)],
    )
    for pool in pools:
        if not pool:
            continue
        by_code = {node_code(node).lower(): node_code(node) for node in pool if node_code(node)}
        for preferred in FREE_NODE_CODE_PREFERENCES:
            actual = by_code.get(preferred)
            if actual:
                return actual
        first = next((node_code(node) for node in pool if node_code(node)), "")
        if first:
            return first
    return None


def free_pool_node_codes(nodes: list[Any]) -> list[str]:
    code = canonical_free_node_code(nodes)
    return [code] if code else []


def paid_pool_nodes(nodes: list[Any]) -> list[Any]:
    ready = [node for node in nodes if node_is_delivery_ready(node) and not node_is_free(node) and node_code(node)]
    if ready:
        return ready
    return [node for node in nodes if not node_is_free(node) and node_code(node)]


def paid_pool_node_codes(nodes: list[Any]) -> list[str]:
    return [node_code(node) for node in paid_pool_nodes(nodes)]

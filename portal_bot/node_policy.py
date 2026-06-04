from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any


FREE_NODE_CODE_PREFERENCES = ("nl-free", "nl_free", "free", "pl_free")
_PREMIUM_PLAN_CODES = {"trial", "channel_bonus", "start_99"}
_PREMIUM_FREE_PLAN_CODES = {"trial"}
_PREMIUM_FREE_WINDOW_DAYS = (
    max(1, int(os.getenv("APP_TRIAL_DEFAULT_DAYS", "5")))
    + max(0, int(os.getenv("CHANNEL_PREMIUM_DAYS", "10")))
    + 1
)
SMART_CONNECT_SHORTLIST_LIMIT = 5
SMART_CONNECT_STICKINESS_THRESHOLD_PERCENT = 15
SMART_CONNECT_STALE_AFTER_SECONDS = 900
SMART_CONNECT_CPU_REJECT_PERCENT = 90.0


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


def _free_user_has_active_premium_window(user: Any, *, now: datetime | None = None) -> bool:
    expiry = _normalize_utc_naive(getattr(user, "expiry_at", None))
    if expiry is None:
        return False
    current = _normalize_utc_naive(now) or _utcnow()
    if not bool(getattr(user, "is_active", False)) or expiry <= current:
        return False
    return expiry <= current + timedelta(days=_PREMIUM_FREE_WINDOW_DAYS)


def user_uses_free_pool(user: Any) -> bool:
    sub_type = str(getattr(user, "sub_type", "") or "").strip().upper()
    plan_code = str(getattr(user, "current_plan_code", "") or "").strip().lower()

    if sub_type == "FREE":
        if plan_code in _PREMIUM_FREE_PLAN_CODES and _free_user_has_active_premium_window(user):
            return False
        return True
    if plan_code in _PREMIUM_PLAN_CODES:
        return False
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

from __future__ import annotations

from typing import Any


FREE_NODE_CODE_PREFERENCES = ("nl-free", "nl_free", "free", "pl_free")
_PREMIUM_PLAN_CODES = {"trial", "channel_bonus", "start_99"}


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

"""Read existing node and support signals without turning connections into people."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import case, func

from models import Node, NodeCapacityPolicy, SupportTicket
from node_policy import node_capacity_status


def commercial_quality_snapshot(session, *, now: datetime | None = None) -> dict:
    current = now or datetime.now(timezone.utc)
    current_db = (
        current.astimezone(timezone.utc).replace(tzinfo=None)
        if current.tzinfo is not None else current
    )
    rows = (
        session.query(Node, NodeCapacityPolicy)
        .outerjoin(NodeCapacityPolicy, (NodeCapacityPolicy.node_code == Node.code) & NodeCapacityPolicy.is_enabled.is_(True))
        .filter(Node.enabled.is_(True), Node.access_role == "paid")
        .order_by(Node.code.asc())
        .all()
    )
    nodes = []
    for node, policy in rows:
        if policy is not None and not policy.allow_premium_pool:
            continue
        capacity = node_capacity_status(node, policy=policy, now=current)
        missing = [
            name for name in ("cpu_percent", "packet_loss_percent")
            if getattr(node, name) is None
        ]
        if all(getattr(node, name) is None for name in (
            "network_tx_mbps_1m", "network_tx_mbps_5m", "network_tx_mbps", "network_total_mbps",
        )):
            missing.append("tx_mbps")
        state = "unknown" if missing else capacity["state"]
        nodes.append({
            "code": node.code,
            "state": state,
            "reject_reason": capacity["reject_reason"],
            "missing_metrics": missing,
            "sample_at": node.last_health_at.isoformat() if node.last_health_at else None,
            "cpu_percent": node.cpu_percent,
            "tx_mbps": None if "tx_mbps" in missing else capacity["tx_mbps"],
            "tx_ratio": None if "tx_mbps" in missing else capacity["tx_ratio"],
            "packet_loss_percent": node.packet_loss_percent,
            "online_connections_hint": int(node.online_connections_hint or 0),
        })

    open_count, high_count, overdue_count = (
        session.query(
            func.count(SupportTicket.id),
            func.sum(case((SupportTicket.priority.in_(["critical", "high"]), 1), else_=0)),
            func.sum(case((
                (SupportTicket.sla_due_at <= current_db)
                & (SupportTicket.waiting_on.is_(None) | (SupportTicket.waiting_on != "customer")),
                1,
            ), else_=0)),
        )
        .filter(
            SupportTicket.environment == "production",
            SupportTicket.status.in_(["open", "in_progress"]),
        )
        .one()
    )
    support = {
        "open_tickets": int(open_count or 0),
        "high_priority_open_tickets": int(high_count or 0),
        "overdue_actionable_tickets": int(overdue_count or 0),
    }
    blocking = []
    expansion = []
    if not nodes or any(node["state"] == "unknown" for node in nodes):
        blocking.append("node_quality_unavailable")
    if any(node["state"] in {"drain", "hard_reject"} for node in nodes):
        blocking.append("node_quality_pressure")
    if any(node["state"] == "warm" for node in nodes):
        expansion.append("node_warm")
    if support["high_priority_open_tickets"] or support["overdue_actionable_tickets"]:
        blocking.append("support_pressure")
    return {
        "authority": "node_capacity_policy_and_support_queue",
        "acquisition_permitted": not blocking,
        "resume_permitted": not blocking and not expansion,
        "blocking_reasons": blocking,
        "expansion_reasons": expansion,
        "nodes": nodes,
        "support": support,
        "online_connections_hint": sum(node["online_connections_hint"] for node in nodes),
        "concurrent_devices": None,
        "concurrent_devices_status": "not_measured",
    }

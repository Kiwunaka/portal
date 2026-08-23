"""Read-only Operator Center v2 projections for network operations.

The service composes existing node, RU-origin, provider and alert authorities.
It does not poll providers, refresh alerts or execute commands while serving a
read request.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

try:
    from .admin_ops_service import (
        alert_payload,
        build_node_observability,
        provider_quota_payload,
        provider_quota_status_rows,
        traffic_summary_rows,
    )
    from .models import Node, OpsAlert, ProviderTrafficQuota
except ImportError:
    from admin_ops_service import (
        alert_payload,
        build_node_observability,
        provider_quota_payload,
        provider_quota_status_rows,
        traffic_summary_rows,
    )
    from models import Node, OpsAlert, ProviderTrafficQuota


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _country_code(node_code: object) -> str | None:
    match = re.match(r"^([a-z]{2})(?:[-_]|$)", str(node_code or "").strip().lower())
    return match.group(1).upper() if match else None


def _network_utilization(details: dict[str, Any], capacity: dict[str, Any]) -> float | None:
    total = details.get("network_total_mbps")
    maximum = capacity.get("capacity_mbps")
    if not isinstance(total, (int, float)) or not isinstance(maximum, (int, float)) or maximum <= 0:
        return None
    return round(max(0.0, float(total)) / float(maximum) * 100.0, 2)


def build_network_fleet(
    session,
    *,
    now: datetime,
    metrics_stale_after_seconds: int,
) -> dict[str, Any]:
    """Build one bounded fleet list from the existing Node 360 projection."""

    nodes = session.query(Node).order_by(
        Node.enabled.desc(),
        Node.health_score.desc(),
        Node.weight.desc(),
        Node.code.asc(),
    ).all()
    items: list[dict[str, Any]] = []
    for node in nodes:
        detail = build_node_observability(
            s=session,
            node_code=str(node.code or ""),
            now=now,
            metrics_stale_after_seconds=metrics_stale_after_seconds,
            include_ru_history=False,
        )
        if detail is None:
            continue
        brain = dict(detail["sources"]["brain_metrics"])
        brain_details = dict(brain.get("details") or {})
        capacity = dict(detail["capacity"])
        items.append(
            {
                "code": str(detail["node"]["code"]),
                "name": str(detail["node"].get("name") or "") or None,
                "country_code": _country_code(detail["node"]["code"]),
                "enabled": bool(detail["lifecycle"]["enabled"]),
                "accepting_new_clients": bool(detail["lifecycle"]["accepting_new_clients"]),
                "is_draining": bool(detail["lifecycle"]["is_draining"]),
                "mapped_users": int(detail["lifecycle"].get("mapped_users") or 0),
                "is_healthy": bool(node.is_healthy) if brain.get("sampled_at") else None,
                "health_score": float(node.health_score) if brain.get("sampled_at") and node.health_score is not None else None,
                "capacity_state": str(capacity.get("state") or "unknown"),
                "capacity_reject_reason": str(capacity.get("reject_reason") or "") or None,
                "cpu_percent": brain_details.get("cpu_percent"),
                "network_utilization_percent": _network_utilization(brain_details, capacity),
                "provisioned_clients_count": capacity.get("provisioned_clients_count"),
                "online_connections_hint": capacity.get("online_connections_hint"),
                "freshness_status": str(brain.get("status") or "missing"),
                "freshness_age_seconds": brain.get("age_seconds"),
                "last_health_at": brain.get("sampled_at"),
                "hoster_family": detail["node"].get("hoster_family"),
                "hoster_asn": detail["node"].get("hoster_asn"),
                "subnet": None,
                "alert_kinds": sorted(
                    {
                        str(row.get("source") or "")
                        for row in detail.get("alerts") or []
                        if str(row.get("source") or "").strip()
                    }
                ),
                "transport_profiles": list(detail.get("transports") or []),
                "sources": detail["sources"],
            }
        )
    return {
        "generated_at": _iso(now),
        "authority": {
            "inventory": "nodes",
            "brain_metrics": "node_health_samples",
            "runtime": "node_runtime_metrics",
            "ru_origin": "ru_probe_runs",
            "alerts": "ops_alerts",
        },
        "items": items,
        "count": len(items),
    }


def node_360(
    session,
    *,
    node_code: str,
    now: datetime,
    metrics_stale_after_seconds: int,
    include_ru_history: bool,
) -> dict[str, Any] | None:
    return build_node_observability(
        s=session,
        node_code=node_code,
        now=now,
        metrics_stale_after_seconds=metrics_stale_after_seconds,
        include_ru_history=include_ru_history,
    )


def list_network_alerts(
    session,
    *,
    environment: str,
    status: str,
    now: datetime,
    limit: int = 300,
) -> dict[str, Any]:
    wanted = str(status or "active").strip().lower()
    query = session.query(OpsAlert).filter(OpsAlert.environment == str(environment))
    if wanted in {"active", "open"}:
        query = query.filter(OpsAlert.status.in_(("active", "acknowledged")))
    elif wanted not in {"all", "*"}:
        query = query.filter(OpsAlert.status == wanted)
    rows = query.order_by(OpsAlert.last_seen_at.desc(), OpsAlert.id.desc()).limit(
        max(1, min(int(limit), 500))
    ).all()
    payload = [alert_payload(row, now=now) for row in rows]
    if wanted in {"active", "open"}:
        payload = [row for row in payload if row["status"] in {"active", "silenced", "acknowledged"}]
    return {
        "generated_at": _iso(now),
        "authority": "ops_alerts",
        "items": payload,
        "count": len(payload),
    }


def build_provider_read_model(session, *, now: datetime) -> dict[str, Any]:
    configs: list[dict[str, Any]] = []
    for row in session.query(ProviderTrafficQuota).order_by(ProviderTrafficQuota.node_code.asc()).all():
        item = provider_quota_payload(row)
        notes = str(item.pop("notes", "") or "")
        item.pop("updated_by", None)
        item.update(
            {
                "notes_present": bool(notes),
                "notes_length": len(notes),
                "notes_sha256": hashlib.sha256(notes.encode("utf-8")).hexdigest(),
            }
        )
        configs.append(item)
    return {
        "generated_at": _iso(now),
        "authority": {
            "configuration": "provider_traffic_quotas",
            "usage": "node_health_samples_total_counter_delta",
        },
        "configs": configs,
        "statuses": provider_quota_status_rows(s=session, now=now),
    }


def build_traffic_read_model(
    session,
    *,
    from_dt: datetime,
    to_dt: datetime,
) -> dict[str, Any]:
    rows = traffic_summary_rows(s=session, from_dt=from_dt, to_dt=to_dt)
    return {
        "from": _iso(from_dt),
        "to": _iso(to_dt),
        "authority": "key_usage_rollups",
        "rows": rows,
    }


__all__ = [
    "build_network_fleet",
    "build_provider_read_model",
    "build_traffic_read_model",
    "list_network_alerts",
    "node_360",
]

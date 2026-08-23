from __future__ import annotations

import calendar
import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo
from typing import Any

from sqlalchemy import String, func, or_

from models import (
    AccessKey,
    AccountDevice,
    ExternalOrder,
    KeyPressureState,
    KeyUsageRollup,
    Node,
    NodeCapacityPolicy,
    NodeHealthSample,
    NodeRuntimeMetric,
    OpsAlert,
    ProviderTrafficQuota,
    SecurityEvent,
    User,
    UserNode,
)
from node_policy import node_capacity_status
from node_observability_sanitizer import (
    safe_error_kind,
    safe_hoster_asn,
    safe_hoster_family,
    safe_probe_classification,
    safe_probe_stage,
    sanitize_transport_health,
)
from observer_service import observer_stale_after_seconds
from ru_probe_service import (
    RU_RUN_STALE_AFTER_SECONDS,
    RuProbeConfigurationError,
    get_latest_ru_status,
    get_ru_run_history,
    get_ru_uploader_status,
)
from transport_catalog import node_transport_profiles


MANAGED_ALERT_SOURCES = {
    "node_metrics",
    "node_capacity",
    "provider_quota",
    "free_tier",
    "security",
    "ru_probe",
}


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return float(default)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return int(default)


NODE_METRICS_CPU_ALERT_PERCENT = _env_float("NODE_METRICS_CPU_ALERT_PERCENT", 70.0)
NODE_METRICS_MEMORY_ALERT_PERCENT = _env_float("NODE_METRICS_MEMORY_ALERT_PERCENT", 85.0)
NODE_METRICS_DISK_ALERT_PERCENT = _env_float("NODE_METRICS_DISK_ALERT_PERCENT", 90.0)
NODE_METRICS_NETWORK_ALERT_PERCENT = _env_float("NODE_METRICS_NETWORK_ALERT_PERCENT", 70.0)
NODE_METRICS_PORT_CAPACITY_MBPS = _env_float("NODE_METRICS_PORT_CAPACITY_MBPS", 1000.0)
NODE_METRICS_LATENCY_ALERT_MS = _env_float("NODE_METRICS_LATENCY_ALERT_MS", 800.0)
NODE_METRICS_ERROR_RATE_ALERT = _env_float("NODE_METRICS_ERROR_RATE_ALERT", 0.2)
NODE_METRICS_ACTIVE_CLIENTS_ALERT = max(1, _env_int("NODE_METRICS_ACTIVE_CLIENTS_ALERT", 200))
NODE_METRICS_SUSTAINED_SAMPLES = max(2, _env_int("NODE_METRICS_SUSTAINED_SAMPLES", 3))
NODE_CAPACITY_ALERT_SUSTAINED_SAMPLES = max(2, _env_int("NODE_CAPACITY_ALERT_SUSTAINED_SAMPLES", 3))


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def safe_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def bytes_to_gb(value: int | float | None) -> float:
    return round(float(max(0, int(value or 0))) / float(1024**3), 3)


def gb_to_bytes(value: int | float | None) -> int:
    return int(max(0.0, float(value or 0.0)) * float(1024**3))


def _json_loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except Exception:
        return fallback


def _json_object(value: str | None) -> dict[str, Any]:
    parsed = _json_loads(value, {})
    return parsed if isinstance(parsed, dict) else {}


def _panel_state_from_json(value: str | None) -> str | None:
    state = sanitize_transport_health(value).get("panel_state")
    return str(state) if state and state != "unknown" else None


def _month_boundary(*, year: int, month: int, day: int, tz: ZoneInfo) -> datetime:
    last_day = calendar.monthrange(year, month)[1]
    return datetime(year, month, min(max(1, int(day or 1)), last_day), tzinfo=tz)


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    raw = (year * 12) + (month - 1) + delta
    return raw // 12, (raw % 12) + 1


def provider_quota_cycle_bounds(
    *,
    now: datetime,
    reset_day: int,
    timezone_name: str,
) -> tuple[datetime, datetime]:
    tz_name = str(timezone_name or "UTC").strip() or "UTC"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = timezone.utc
    now_aware = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now.astimezone(timezone.utc)
    local_now = now_aware.astimezone(tz)
    current = _month_boundary(year=local_now.year, month=local_now.month, day=reset_day, tz=tz)
    if local_now >= current:
        start_local = current
        end_year, end_month = _shift_month(local_now.year, local_now.month, 1)
        end_local = _month_boundary(year=end_year, month=end_month, day=reset_day, tz=tz)
    else:
        prev_year, prev_month = _shift_month(local_now.year, local_now.month, -1)
        start_local = _month_boundary(year=prev_year, month=prev_month, day=reset_day, tz=tz)
        end_local = current
    return (
        start_local.astimezone(timezone.utc).replace(tzinfo=None),
        end_local.astimezone(timezone.utc).replace(tzinfo=None),
    )


def provider_quota_payload(row: ProviderTrafficQuota) -> dict[str, Any]:
    return {
        "id": int(row.id),
        "node_code": str(row.node_code or ""),
        "included_bytes": int(row.included_bytes or 0),
        "included_gb": bytes_to_gb(row.included_bytes),
        "reset_day": int(row.reset_day or 1),
        "timezone": str(row.timezone or "UTC"),
        "warning_ratio": float(row.warning_ratio or 0.8),
        "critical_ratio": float(row.critical_ratio or 0.95),
        "enabled": bool(row.enabled),
        "notes": str(row.notes or "") or None,
        "updated_by": int(row.updated_by) if row.updated_by is not None else None,
        "created_at": safe_iso(row.created_at),
        "updated_at": safe_iso(row.updated_at),
    }


def provider_quota_usage_bytes(
    *,
    s,
    node_code: str,
    cycle_start: datetime,
    cycle_end: datetime,
) -> tuple[int, int, str | None]:
    samples = (
        s.query(NodeHealthSample.total_traffic_bytes)
        .filter(func.lower(NodeHealthSample.node_code) == str(node_code or "").strip().lower())
        .filter(NodeHealthSample.sampled_at >= cycle_start, NodeHealthSample.sampled_at < cycle_end)
        .order_by(NodeHealthSample.sampled_at.asc(), NodeHealthSample.id.asc())
        .limit(20000)
        .all()
    )
    sample_count = len(samples)
    if sample_count < 2:
        return 0, sample_count, "node_health_samples_total_counter_delta"
    used_bytes = 0
    previous = int(samples[0][0] or 0)
    for sample in samples[1:]:
        current = int(sample[0] or 0)
        if current >= previous:
            used_bytes += current - previous
        else:
            # Counter reset after reboot or collector reset: count the new counter value as post-reset traffic.
            used_bytes += max(0, current)
        previous = current
    return max(0, used_bytes), sample_count, "node_health_samples_total_counter_delta"


def provider_quota_status_rows(*, s, now: datetime) -> list[dict[str, Any]]:
    quotas = {str(q.node_code or "").strip().lower(): q for q in s.query(ProviderTrafficQuota).all()}
    nodes_by_code = {str(n.code or "").strip().lower(): n for n in s.query(Node).order_by(Node.code.asc()).all()}
    codes = sorted(set(quotas.keys()) | set(nodes_by_code.keys()))
    rows: list[dict[str, Any]] = []
    for code in codes:
        if not code:
            continue
        quota = quotas.get(code)
        node = nodes_by_code.get(code)
        if not quota:
            rows.append(
                {
                    "node_code": code,
                    "node_name": str(getattr(node, "name", "") or ""),
                    "configured": False,
                    "enabled": False,
                    "state": "unconfigured",
                    "included_bytes": 0,
                    "included_gb": 0.0,
                    "used_bytes": 0,
                    "used_gb": 0.0,
                    "remaining_bytes": 0,
                    "remaining_gb": 0.0,
                    "used_ratio": 0.0,
                    "used_pct": 0.0,
                    "warning_ratio": 0.8,
                    "critical_ratio": 0.95,
                    "cycle_start": None,
                    "cycle_end": None,
                    "sample_count": 0,
                    "source": "not_configured",
                }
            )
            continue
        cycle_start, cycle_end = provider_quota_cycle_bounds(
            now=now,
            reset_day=int(quota.reset_day or 1),
            timezone_name=str(quota.timezone or "UTC"),
        )
        used_bytes, sample_count, source = provider_quota_usage_bytes(
            s=s,
            node_code=code,
            cycle_start=cycle_start,
            cycle_end=cycle_end,
        )
        included_bytes = max(0, int(quota.included_bytes or 0))
        used_ratio = (float(used_bytes) / float(included_bytes)) if included_bytes > 0 else 0.0
        if not bool(quota.enabled):
            state = "disabled"
        elif included_bytes <= 0:
            state = "missing_limit"
        elif used_ratio >= float(quota.critical_ratio or 0.95):
            state = "critical"
        elif used_ratio >= float(quota.warning_ratio or 0.8):
            state = "warning"
        else:
            state = "ok"
        rows.append(
            {
                "node_code": code,
                "node_name": str(getattr(node, "name", "") or ""),
                "configured": True,
                "enabled": bool(quota.enabled),
                "state": state,
                "included_bytes": included_bytes,
                "included_gb": bytes_to_gb(included_bytes),
                "used_bytes": int(used_bytes),
                "used_gb": bytes_to_gb(used_bytes),
                "remaining_bytes": max(0, included_bytes - int(used_bytes)) if included_bytes > 0 else 0,
                "remaining_gb": bytes_to_gb(max(0, included_bytes - int(used_bytes))) if included_bytes > 0 else 0.0,
                "used_ratio": round(used_ratio, 4),
                "used_pct": round(used_ratio * 100.0, 1),
                "warning_ratio": float(quota.warning_ratio or 0.8),
                "critical_ratio": float(quota.critical_ratio or 0.95),
                "cycle_start": safe_iso(cycle_start),
                "cycle_end": safe_iso(cycle_end),
                "reset_day": int(quota.reset_day or 1),
                "timezone": str(quota.timezone or "UTC"),
                "sample_count": int(sample_count),
                "source": source,
                "updated_at": safe_iso(quota.updated_at),
            }
        )
    return rows


def _free_cycle_bounds(user: User, *, now: datetime, cycle_days: int) -> tuple[datetime, datetime]:
    end = getattr(user, "free_cycle_next_reset_at", None)
    start = getattr(user, "free_cycle_last_reset_at", None) or getattr(user, "free_cycle_anchor_at", None)
    if not end or end <= now - timedelta(days=max(1, cycle_days) * 2):
        end = now + timedelta(days=max(1, cycle_days))
    if not start or start >= end:
        start = end - timedelta(days=max(1, cycle_days))
    return start, end


def _free_usage_by_tg(*, s, tg_ids: list[int], min_start: datetime, now: datetime) -> dict[int, list[KeyUsageRollup]]:
    if not tg_ids:
        return {}
    rows = (
        s.query(KeyUsageRollup)
        .filter(KeyUsageRollup.tg_id.in_(tg_ids))
        .filter(KeyUsageRollup.window_bucket_at >= min_start, KeyUsageRollup.window_bucket_at <= now)
        .order_by(KeyUsageRollup.window_bucket_at.asc())
        .all()
    )
    by_tg: dict[int, list[KeyUsageRollup]] = {}
    for row in rows:
        if row.tg_id is None:
            continue
        by_tg.setdefault(int(row.tg_id), []).append(row)
    return by_tg


def free_tier_user_rows(
    *,
    s,
    now: datetime,
    free_limit_gb: int,
    cycle_days: int,
    limit: int = 200,
    offset: int = 0,
    q: str = "",
) -> tuple[list[dict[str, Any]], int]:
    query = s.query(User).filter(User.tg_id > 0).filter(func.upper(func.coalesce(User.sub_type, "")) == "FREE")
    raw_q = str(q or "").strip()
    if raw_q:
        like = f"%{raw_q.lower()}%"
        query = query.filter(
            (func.lower(func.coalesce(User.username, "")).like(like))
            | (func.lower(func.coalesce(User.display_name, "")).like(like))
            | (func.cast(User.tg_id, String).like(f"%{raw_q}%"))
        )
    total = int(query.count() or 0)
    users = query.order_by(User.created_at.desc(), User.tg_id.desc()).offset(max(0, int(offset))).limit(max(1, min(int(limit), 1000))).all()
    bounds = {int(u.tg_id): _free_cycle_bounds(u, now=now, cycle_days=cycle_days) for u in users}
    min_start = min((start for start, _end in bounds.values()), default=now - timedelta(days=cycle_days))
    usage_rows = _free_usage_by_tg(s=s, tg_ids=[int(u.tg_id) for u in users], min_start=min_start, now=now)
    limit_bytes = gb_to_bytes(free_limit_gb)
    out: list[dict[str, Any]] = []
    for user in users:
        tg_id = int(user.tg_id)
        start, end = bounds[tg_id]
        used_bytes = sum(
            int(row.total_bytes or 0)
            for row in usage_rows.get(tg_id, [])
            if start <= row.window_bucket_at < min(end, now + timedelta(seconds=1))
        )
        used_ratio = float(used_bytes) / float(limit_bytes) if limit_bytes > 0 else 0.0
        state = "over_cap" if used_ratio >= 1 else "near_cap" if used_ratio >= 0.8 else "ok"
        out.append(
            {
                "tg_id": tg_id,
                "username": str(user.username or "") or None,
                "display_name": str(getattr(user, "display_name", "") or "") or None,
                "is_active": bool(user.is_active),
                "current_plan_code": str(getattr(user, "current_plan_code", "") or "") or None,
                "used_bytes": int(used_bytes),
                "used_gb": bytes_to_gb(used_bytes),
                "limit_bytes": int(limit_bytes),
                "limit_gb": float(free_limit_gb),
                "remaining_bytes": max(0, limit_bytes - int(used_bytes)),
                "remaining_gb": bytes_to_gb(max(0, limit_bytes - int(used_bytes))),
                "used_ratio": round(used_ratio, 4),
                "used_pct": round(used_ratio * 100.0, 1),
                "state": state,
                "transition_state": str(getattr(user, "free_profile_state", "") or "standard"),
                "active_role": str(getattr(user, "free_profile_active_role", "") or "free_standard"),
                "provisioning_job_id": getattr(user, "free_profile_job_id", None),
                "provisioning_error_code": str(getattr(user, "free_profile_error_code", "") or "") or None,
                "cycle_start": safe_iso(start),
                "cycle_end": safe_iso(end),
                "next_reset_at": safe_iso(getattr(user, "free_cycle_next_reset_at", None)),
                "source": "key_usage_rollups",
                "rollup_count": len(usage_rows.get(tg_id, [])),
            }
        )
    out.sort(key=lambda row: (row["state"] != "over_cap", row["state"] != "near_cap", -row["used_bytes"]))
    return out, total


def free_tier_summary(*, s, now: datetime, free_limit_gb: int, cycle_days: int) -> dict[str, Any]:
    rows, total = free_tier_user_rows(s=s, now=now, free_limit_gb=free_limit_gb, cycle_days=cycle_days, limit=1000, offset=0)
    used_bytes = sum(int(row["used_bytes"]) for row in rows)
    limit_bytes = gb_to_bytes(free_limit_gb) * int(total)
    remaining_bytes = max(0, int(limit_bytes) - int(used_bytes))
    over_cap = sum(1 for row in rows if row["state"] == "over_cap")
    near_cap = sum(1 for row in rows if row["state"] == "near_cap")
    cycle_starts = [datetime.fromisoformat(str(row["cycle_start"])) for row in rows if row.get("cycle_start")]
    elapsed_days = max(1.0, (now - min(cycle_starts)).total_seconds() / 86400.0) if cycle_starts else 1.0
    return {
        "generated_at": safe_iso(now),
        "free_users": int(total),
        "sampled_users": len(rows),
        "limit_gb_per_user": float(free_limit_gb),
        "cycle_days": int(cycle_days),
        "used_bytes": int(used_bytes),
        "used_gb": bytes_to_gb(used_bytes),
        "limit_bytes": int(limit_bytes),
        "limit_gb_total": bytes_to_gb(limit_bytes),
        "remaining_bytes": int(remaining_bytes),
        "remaining_gb": bytes_to_gb(remaining_bytes),
        "used_pct": round((float(used_bytes) / float(limit_bytes) * 100.0) if limit_bytes > 0 else 0.0, 1),
        "near_cap_users": int(near_cap),
        "over_cap_users": int(over_cap),
        "burn_rate_gb_per_day": round(bytes_to_gb(used_bytes) / elapsed_days, 3),
        "source": "key_usage_rollups",
    }


def traffic_summary_rows(*, s, from_dt: datetime, to_dt: datetime) -> list[dict[str, Any]]:
    rollups = (
        s.query(KeyUsageRollup)
        .filter(KeyUsageRollup.window_bucket_at >= from_dt, KeyUsageRollup.window_bucket_at <= to_dt)
        .order_by(KeyUsageRollup.window_bucket_at.asc())
        .limit(20000)
        .all()
    )
    key_ids = sorted({int(row.key_id) for row in rollups if row.key_id is not None})
    pool_by_key_id: dict[int, str] = {}
    if key_ids:
        for key_id, pool_code in s.query(AccessKey.id, AccessKey.pool_code).filter(AccessKey.id.in_(key_ids)).all():
            pool_by_key_id[int(key_id)] = str(pool_code or "unknown")
    buckets: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rollups:
        date_key = str(row.window_bucket_at.date().isoformat()) if row.window_bucket_at else ""
        node_code = str(row.node_code or "unknown").strip().lower() or "unknown"
        pool_code = pool_by_key_id.get(int(row.key_id), "") if row.key_id is not None else ""
        if not pool_code:
            pool_code = "free_pool" if "free" in node_code else "unknown"
        key = (date_key, node_code, pool_code)
        bucket = buckets.setdefault(
            key,
            {"date": date_key, "node_code": node_code, "pool_code": pool_code, "traffic_bytes": 0, "samples": 0},
        )
        bucket["traffic_bytes"] += int(row.total_bytes or 0)
        bucket["samples"] += int(row.observations or 0)
    rows = []
    for bucket in buckets.values():
        bytes_value = int(bucket["traffic_bytes"])
        rows.append({**bucket, "traffic_gb": bytes_to_gb(bytes_value)})
    rows.sort(key=lambda row: (row["date"], row["node_code"], row["pool_code"]))
    return rows


def node_timeseries_rows(*, s, from_dt: datetime, to_dt: datetime, node_code: str = "") -> list[dict[str, Any]]:
    wanted = str(node_code or "").strip().lower()
    sample_query = s.query(NodeHealthSample).filter(NodeHealthSample.sampled_at >= from_dt, NodeHealthSample.sampled_at <= to_dt)
    runtime_query = s.query(NodeRuntimeMetric).filter(NodeRuntimeMetric.sampled_at >= from_dt, NodeRuntimeMetric.sampled_at <= to_dt)
    if wanted:
        sample_query = sample_query.filter(func.lower(NodeHealthSample.node_code) == wanted)
        runtime_query = runtime_query.filter(func.lower(NodeRuntimeMetric.node_code) == wanted)
    rows: list[dict[str, Any]] = []
    for row in sample_query.order_by(NodeHealthSample.sampled_at.asc()).limit(5000).all():
        rows.append(
            {
                "sampled_at": safe_iso(row.sampled_at),
                "node_code": str(row.node_code or ""),
                "source": str(row.source or "node_health_samples"),
                "cpu_percent": float(row.cpu_percent or 0.0),
                "memory_used_mb": int(row.memory_used_mb or 0) if row.memory_used_mb is not None else None,
                "memory_total_mb": int(row.memory_total_mb or 0) if row.memory_total_mb is not None else None,
                "disk_used_gb": float(row.disk_used_gb or 0.0) if row.disk_used_gb is not None else None,
                "disk_total_gb": float(row.disk_total_gb or 0.0) if row.disk_total_gb is not None else None,
                "network_rx_mbps": float(row.network_rx_mbps or 0.0) if row.network_rx_mbps is not None else None,
                "network_tx_mbps": float(row.network_tx_mbps or 0.0) if row.network_tx_mbps is not None else None,
                "network_total_mbps": float(row.network_total_mbps or 0.0) if row.network_total_mbps is not None else None,
                "traffic_bytes_total": int(row.total_traffic_bytes or 0),
                "active_clients": int(row.active_clients or 0),
                "is_healthy": bool(row.is_healthy),
                "score": float(row.score or 0.0),
            }
        )
    for row in runtime_query.order_by(NodeRuntimeMetric.sampled_at.asc()).limit(5000).all():
        rows.append(
            {
                "sampled_at": safe_iso(row.sampled_at),
                "node_code": str(row.node_code or ""),
                "source": str(row.source or "node_runtime_metrics"),
                "cpu_percent": float(row.cpu_percent or 0.0) if row.cpu_percent is not None else None,
                "memory_used_mb": int(row.memory_used_mb or 0) if row.memory_used_mb is not None else None,
                "memory_total_mb": int(row.memory_total_mb or 0) if row.memory_total_mb is not None else None,
                "network_rx_mbps": float(row.network_rx_mbps_1m or 0.0) if row.network_rx_mbps_1m is not None else None,
                "network_tx_mbps": float(row.network_tx_mbps_1m or 0.0) if row.network_tx_mbps_1m is not None else None,
                "network_total_mbps": float(row.network_total_mbps or 0.0) if row.network_total_mbps is not None else None,
                "provisioned_clients_count": int(row.provisioned_clients_count or 0),
                "online_connections_hint": int(row.online_connections_hint or 0),
                "packet_loss_percent": float(row.packet_loss_percent or 0.0) if row.packet_loss_percent is not None else None,
                "tcp_retrans_percent": float(row.tcp_retrans_percent or 0.0) if row.tcp_retrans_percent is not None else None,
                "edge_reachability_ok": row.edge_reachability_ok,
                "authenticated_egress_ok": row.authenticated_egress_ok,
                "dataplane_ok": row.dataplane_ok,
                "dataplane_rtt_ms": int(row.dataplane_rtt_ms or 0) if row.dataplane_rtt_ms is not None else None,
                "capacity_score": float(row.capacity_score or 0.0) if row.capacity_score is not None else None,
                "capacity_state": str(row.capacity_state or "unknown"),
                "reject_reason": str(row.reject_reason or "") or None,
            }
        )
    rows.sort(key=lambda item: (str(item.get("sampled_at") or ""), str(item.get("node_code") or ""), str(item.get("source") or "")))
    return rows


def alert_payload(row: OpsAlert, *, now: datetime | None = None) -> dict[str, Any]:
    current_now = now or utcnow()
    silenced = bool(row.silence_until and row.silence_until > current_now and str(row.status or "") == "active")
    effective_status = "silenced" if silenced else str(row.status or "active")
    return {
        "id": int(row.id),
        "version": int(row.version or 1),
        "fingerprint": str(row.fingerprint or ""),
        "source": str(row.source or ""),
        "severity": str(row.severity or "warning"),
        "status": effective_status,
        "raw_status": str(row.status or "active"),
        "title": str(row.title or ""),
        "body": str(row.body or "") or None,
        "node_code": str(row.node_code or "") or None,
        "tg_id": int(row.tg_id) if row.tg_id is not None else None,
        "key_id": int(row.key_id) if row.key_id is not None else None,
        "incident_id": str(row.incident_id) if row.incident_id else None,
        "first_seen_at": safe_iso(row.first_seen_at),
        "last_seen_at": safe_iso(row.last_seen_at),
        "resolved_at": safe_iso(row.resolved_at),
        "acknowledged_at": safe_iso(row.acknowledged_at),
        "acknowledged_by": int(row.acknowledged_by) if row.acknowledged_by is not None else None,
        "silence_until": safe_iso(row.silence_until),
        "last_delivery_at": safe_iso(row.last_delivery_at),
        "last_delivery_status": str(row.last_delivery_status or "") or None,
        "metadata": _json_loads(row.metadata_json, {}),
        "created_at": safe_iso(row.created_at),
        "updated_at": safe_iso(row.updated_at),
    }


def _sample_memory_percent(sample: NodeHealthSample | None) -> float:
    if not sample:
        return 0.0
    total = float(getattr(sample, "memory_total_mb", 0) or 0.0)
    if total <= 0:
        return 0.0
    used = float(getattr(sample, "memory_used_mb", 0) or 0.0)
    return round((used / total) * 100.0, 2)


def _sample_disk_percent(sample: NodeHealthSample | None) -> float:
    if not sample:
        return 0.0
    total = float(getattr(sample, "disk_total_gb", 0.0) or 0.0)
    if total <= 0:
        return 0.0
    used = float(getattr(sample, "disk_used_gb", 0.0) or 0.0)
    return round((used / total) * 100.0, 2)


def _network_utilization_percent(total_mbps: object) -> float:
    current = float(total_mbps or 0.0)
    capacity = float(NODE_METRICS_PORT_CAPACITY_MBPS or 0.0)
    if current <= 0 or capacity <= 0:
        return 0.0
    return round((current / capacity) * 100.0, 2)


def _sample_network_percent(sample: NodeHealthSample | None) -> float:
    if not sample:
        return 0.0
    return _network_utilization_percent(getattr(sample, "network_total_mbps", 0.0))


def _observer_is_stale(node: Node, *, now: datetime) -> bool:
    last_push_at = getattr(node, "observer_last_push_at", None)
    configured = bool(str(getattr(node, "observer_push_secret", "") or "").strip())
    if not configured and not last_push_at:
        return False
    if not last_push_at:
        return True
    return int((now - last_push_at).total_seconds()) > observer_stale_after_seconds()


def _active_node_metric_alert_kinds(
    *,
    samples: list[NodeHealthSample],
    last_sample_at: datetime | None,
    stale_after_seconds: int,
    now: datetime,
) -> list[str]:
    kinds: list[str] = []
    age_seconds = int((now - last_sample_at).total_seconds()) if last_sample_at else None
    if age_seconds is None or age_seconds > stale_after_seconds:
        kinds.append("stale_metrics")
        return kinds
    if len(samples) < NODE_METRICS_SUSTAINED_SAMPLES:
        return kinds
    window = samples[:NODE_METRICS_SUSTAINED_SAMPLES]
    if all(float(getattr(sample, "cpu_percent", 0.0) or 0.0) >= NODE_METRICS_CPU_ALERT_PERCENT for sample in window):
        kinds.append("cpu_high")
    if all(_sample_memory_percent(sample) >= NODE_METRICS_MEMORY_ALERT_PERCENT for sample in window):
        kinds.append("memory_high")
    if all(_sample_disk_percent(sample) >= NODE_METRICS_DISK_ALERT_PERCENT for sample in window):
        kinds.append("disk_high")
    if all(_sample_network_percent(sample) >= NODE_METRICS_NETWORK_ALERT_PERCENT for sample in window):
        kinds.append("network_high")
    if all(float(getattr(sample, "panel_latency_ms", 0) or 0.0) >= NODE_METRICS_LATENCY_ALERT_MS for sample in window):
        kinds.append("latency_high")
    if (
        all(float(getattr(sample, "panel_error_rate", 0.0) or 0.0) >= NODE_METRICS_ERROR_RATE_ALERT for sample in window)
        and any(not bool(getattr(sample, "is_healthy", True)) for sample in window)
    ):
        kinds.append("error_rate_high")
    if all(int(getattr(sample, "active_clients", 0) or 0) >= NODE_METRICS_ACTIVE_CLIENTS_ALERT for sample in window):
        kinds.append("client_density_high")
    return kinds


def _point_in_time_node_metric_alert_kinds(source: object | None) -> list[str]:
    """Return compatibility alerts for the latest known node state.

    Durable operator alerts still use ``_active_node_metric_alert_kinds`` and
    therefore require the configured sustained sample window.  These
    point-in-time kinds are only used by status payloads that historically
    exposed the current threshold crossings immediately.
    """
    if source is None:
        return []
    kinds: list[str] = []
    if float(getattr(source, "cpu_percent", 0.0) or 0.0) >= NODE_METRICS_CPU_ALERT_PERCENT:
        kinds.append("cpu_high")
    if _sample_memory_percent(source) >= NODE_METRICS_MEMORY_ALERT_PERCENT:
        kinds.append("memory_high")
    if _sample_disk_percent(source) >= NODE_METRICS_DISK_ALERT_PERCENT:
        kinds.append("disk_high")
    if _sample_network_percent(source) >= NODE_METRICS_NETWORK_ALERT_PERCENT:
        kinds.append("network_high")
    if float(getattr(source, "panel_latency_ms", 0) or 0.0) >= NODE_METRICS_LATENCY_ALERT_MS:
        kinds.append("latency_high")
    if (
        float(getattr(source, "panel_error_rate", 0.0) or 0.0) >= NODE_METRICS_ERROR_RATE_ALERT
        and not bool(getattr(source, "is_healthy", True))
    ):
        kinds.append("error_rate_high")
    if int(getattr(source, "active_clients", 0) or 0) >= NODE_METRICS_ACTIVE_CLIENTS_ALERT:
        kinds.append("client_density_high")
    return kinds


def _legacy_node_alert_kind(kind: str) -> str:
    mapping = {
        "cpu_high": "high_cpu",
        "memory_high": "high_memory",
        "disk_high": "high_disk",
        "network_high": "high_network",
        "latency_high": "high_latency",
        "error_rate_high": "high_error_rate",
        "client_density_high": "high_client_density",
        "observer_push_stale": "observer_push_stale",
        "stale_metrics": "stale_metrics",
    }
    return mapping.get(str(kind or ""), str(kind or ""))


def _legacy_node_alerts(kinds: list[str]) -> list[str]:
    return sorted({_legacy_node_alert_kind(kind) for kind in kinds if str(kind or "").strip()})


def build_admin_metrics_status_snapshot(*, s, now: datetime, stale_after_seconds: int) -> dict[str, Any]:
    nodes = s.query(Node).filter(Node.enabled == True).order_by(Node.weight.desc(), Node.code.asc()).all()
    rows: list[dict[str, Any]] = []
    active_alerts: list[dict[str, Any]] = []
    overall_last_sample: datetime | None = None
    overall_age_seconds: int | None = None
    for node in nodes:
        samples = (
            s.query(NodeHealthSample)
            .filter(NodeHealthSample.node_code == str(node.code or ""))
            .order_by(NodeHealthSample.sampled_at.desc(), NodeHealthSample.id.desc())
            .limit(NODE_METRICS_SUSTAINED_SAMPLES)
            .all()
        )
        latest = samples[0] if samples else None
        last_sample_at = getattr(latest, "sampled_at", None) or getattr(node, "last_health_at", None)
        age_seconds = int((now - last_sample_at).total_seconds()) if last_sample_at else None
        alert_kinds = _active_node_metric_alert_kinds(
            samples=samples,
            last_sample_at=last_sample_at,
            stale_after_seconds=stale_after_seconds,
            now=now,
        )
        if _observer_is_stale(node, now=now):
            alert_kinds.append("observer_push_stale")
        display_alert_kinds = sorted(
            set(alert_kinds + _point_in_time_node_metric_alert_kinds(latest or node))
        )
        if last_sample_at and (overall_last_sample is None or last_sample_at > overall_last_sample):
            overall_last_sample = last_sample_at
        if age_seconds is not None:
            overall_age_seconds = age_seconds if overall_age_seconds is None else max(overall_age_seconds, age_seconds)
        row = {
            "node_code": str(node.code or ""),
            "code": str(node.code or ""),
            "status": "stale" if "stale_metrics" in alert_kinds else "fresh",
            "freshness_status": "stale" if "stale_metrics" in alert_kinds else "fresh",
            "last_sample_at": safe_iso(last_sample_at),
            "age_seconds": age_seconds,
            "cpu_percent": float(getattr(latest, "cpu_percent", getattr(node, "cpu_percent", 0.0)) or 0.0),
            "memory_percent": _sample_memory_percent(latest),
            "disk_percent": _sample_disk_percent(latest),
            "network_total_mbps": float(getattr(latest, "network_total_mbps", getattr(node, "network_total_mbps", 0.0)) or 0.0),
            "network_utilization_percent": _network_utilization_percent(getattr(latest, "network_total_mbps", getattr(node, "network_total_mbps", 0.0))),
            "active_clients": int(getattr(latest, "active_clients", getattr(node, "active_clients", 0)) or 0),
            "observer_last_push_at": safe_iso(getattr(node, "observer_last_push_at", None)),
            "observer_is_stale": bool(_observer_is_stale(node, now=now)),
            "alert_kinds": sorted(set(alert_kinds)),
            "display_alert_kinds": display_alert_kinds,
            "alerts": _legacy_node_alerts(display_alert_kinds),
        }
        rows.append(row)
        for kind in row["alert_kinds"]:
            active_alerts.append({"node_code": row["node_code"], "kind": kind, "status": row["status"], "age_seconds": row["age_seconds"], "last_sample_at": row["last_sample_at"]})
    overall_status = "fresh" if rows and all(row["status"] == "fresh" for row in rows) else "stale"
    security_rows = (
        s.query(SecurityEvent.event_type, func.count(SecurityEvent.id))
        .filter(SecurityEvent.created_at >= now - timedelta(hours=24))
        .group_by(SecurityEvent.event_type)
        .all()
    )
    security_counts = {str(event_type): int(count or 0) for event_type, count in security_rows}
    return {
        "status": overall_status,
        "last_sample_at": safe_iso(overall_last_sample),
        "age_seconds": overall_age_seconds,
        "stale_after_seconds": stale_after_seconds,
        "nodes": rows,
        "active_alerts": active_alerts,
        "node_statuses": rows,
        "alerts": {
            "stale_nodes": sum(1 for row in rows if row["freshness_status"] == "stale"),
            "high_cpu_nodes": sum(1 for row in rows if "high_cpu" in row["alerts"]),
            "high_memory_nodes": sum(1 for row in rows if "high_memory" in row["alerts"]),
            "high_disk_nodes": sum(1 for row in rows if "high_disk" in row["alerts"]),
            "high_network_nodes": sum(1 for row in rows if "high_network" in row["alerts"]),
            "high_latency_nodes": sum(1 for row in rows if "high_latency" in row["alerts"]),
            "high_error_rate_nodes": sum(1 for row in rows if "high_error_rate" in row["alerts"]),
            "high_client_density_nodes": sum(1 for row in rows if "high_client_density" in row["alerts"]),
        },
        "security": {
            "window": "24h",
            "rate_limit_hits": int(security_counts.get("rate_limit_hit", 0)),
            "payment_callback_invalid_signatures": int(security_counts.get("payment_callback_invalid_signature", 0)),
            "support_upload_rejects": int(security_counts.get("support_upload_reject", 0)),
            "support_attachment_denies": int(security_counts.get("support_attachment_denied", 0)),
            "admin_access_denies": int(security_counts.get("admin_access_denied", 0)),
            "subscription_lookup_failures": int(security_counts.get("subscription_lookup_failed", 0)),
            "events": security_counts,
        },
    }


def _node_capacity_policy_by_code(s) -> dict[str, Any]:
    try:
        rows = s.query(NodeCapacityPolicy).filter(NodeCapacityPolicy.is_enabled == True).all()
    except Exception:
        return {}
    return {str(getattr(row, "node_code", "") or "").strip().lower(): row for row in rows if str(getattr(row, "node_code", "") or "").strip()}


def _capacity_alert_evidence(*, s, node_code: str, state: str) -> dict[str, Any]:
    normalized_state = str(state or "").strip().lower()
    if normalized_state != "hard_reject":
        return {
            "confirmed": True,
            "consecutive_samples": 0,
            "required_samples": NODE_CAPACITY_ALERT_SUSTAINED_SAMPLES,
        }
    recent_states = [
        str(row[0] or "").strip().lower()
        for row in (
            s.query(NodeRuntimeMetric.capacity_state)
            .filter(func.lower(NodeRuntimeMetric.node_code) == str(node_code or "").strip().lower())
            .order_by(NodeRuntimeMetric.sampled_at.desc(), NodeRuntimeMetric.id.desc())
            .limit(NODE_CAPACITY_ALERT_SUSTAINED_SAMPLES)
            .all()
        )
    ]
    consecutive_samples = 0
    for recent_state in recent_states:
        if recent_state != "hard_reject":
            break
        consecutive_samples += 1
    return {
        "confirmed": bool(
            len(recent_states) >= NODE_CAPACITY_ALERT_SUSTAINED_SAMPLES
            and consecutive_samples >= NODE_CAPACITY_ALERT_SUSTAINED_SAMPLES
        ),
        "consecutive_samples": consecutive_samples,
        "required_samples": NODE_CAPACITY_ALERT_SUSTAINED_SAMPLES,
    }


def admin_nodes_capacity_payload(*, s, now: datetime) -> dict[str, Any]:
    rows = s.query(Node).order_by(Node.enabled.desc(), Node.code.asc()).all()
    policy_by_code = _node_capacity_policy_by_code(s)
    pressure_by_code = {
        str(node_code or "").strip().lower(): int(count or 0)
        for node_code, count in (
            s.query(KeyPressureState.node_code, func.count(KeyPressureState.key_id))
            .filter(KeyPressureState.state != "ok")
            .group_by(KeyPressureState.node_code)
            .all()
        )
    }
    nodes_payload = []
    for node in rows:
        code = str(getattr(node, "code", "") or "").strip().lower()
        policy = policy_by_code.get(code)
        capacity = node_capacity_status(node, policy=policy, now=now)
        alert_evidence = _capacity_alert_evidence(
            s=s,
            node_code=code,
            state=str(capacity.get("state") or "unknown"),
        )
        nodes_payload.append({
            "code": code,
            "name": str(getattr(node, "name", "") or ""),
            "enabled": bool(getattr(node, "enabled", True)),
            "accepting_new_clients": bool(getattr(node, "accepting_new_clients", True)),
            "is_draining": bool(getattr(node, "is_draining", False)),
            "capacity_state": str(capacity.get("state") or "unknown"),
            "capacity_score": float(capacity.get("score") or 0.0),
            "reject_reason": str(capacity.get("reject_reason") or "") or None,
            "alert_confirmed": bool(alert_evidence["confirmed"]),
            "alert_consecutive_samples": int(alert_evidence["consecutive_samples"]),
            "alert_required_samples": int(alert_evidence["required_samples"]),
            "tx_mbps": capacity.get("tx_mbps"),
            "tx_ratio": capacity.get("tx_ratio"),
            "capacity_mbps": capacity.get("capacity_mbps"),
            "cpu_percent": float(getattr(node, "cpu_percent", 0.0) or 0.0),
            "edge_reachability_ok": getattr(node, "edge_reachability_ok", None),
            "authenticated_egress_ok": getattr(node, "authenticated_egress_ok", None),
            "dataplane_ok": getattr(node, "dataplane_ok", None),
            "dataplane_rtt_ms": getattr(node, "dataplane_rtt_ms", None),
            "packet_loss_percent": getattr(node, "packet_loss_percent", None),
            "tcp_retrans_percent": getattr(node, "tcp_retrans_percent", None),
            "provisioned_clients_count": int(capacity.get("provisioned_clients_count") or 0),
            "online_connections_hint": int(capacity.get("online_connections_hint") or 0),
            "pressure_keys": int(pressure_by_code.get(code, 0) or 0),
            "last_health_at": safe_iso(getattr(node, "last_health_at", None)),
            "policy": {
                "soft_tx_ratio": getattr(policy, "soft_tx_ratio", None),
                "drain_tx_ratio": getattr(policy, "drain_tx_ratio", None),
                "hard_tx_ratio": getattr(policy, "hard_tx_ratio", None),
                "stale_after_seconds": getattr(policy, "stale_after_seconds", None),
            },
        })
    return {"ok": True, "updated_at": safe_iso(now), "nodes": nodes_payload}


def _ops_utc_naive(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _source_age_seconds(*, now: datetime, sampled_at: datetime | None) -> int | None:
    normalized_now = _ops_utc_naive(now)
    normalized_sample = _ops_utc_naive(sampled_at)
    if normalized_now is None or normalized_sample is None:
        return None
    return max(0, int((normalized_now - normalized_sample).total_seconds()))


def _source_row(
    *,
    status: str,
    sampled_at: datetime | None,
    now: datetime,
    threshold_seconds: int,
    reason_code: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": str(status),
        "sampled_at": safe_iso(_ops_utc_naive(sampled_at)),
        "age_seconds": _source_age_seconds(now=now, sampled_at=sampled_at),
        "threshold_seconds": int(threshold_seconds),
        "reason_code": str(reason_code),
        "details": details or {},
    }


def _safe_transport_rows(node: Node) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for profile in node_transport_profiles(node, include_disabled=True):
        name = str(profile.get("name") or "").strip()
        if not name:
            continue
        rows.append(
            {
                "name": name,
                "enabled": bool(profile.get("enabled")),
                "kind": str(profile.get("kind") or "unknown"),
                "port": int(profile.get("port") or 0) or None,
                "has_inbound": int(profile.get("inbound_id") or 0) > 0,
            }
        )
    return rows


def _compact_node_alert(row: OpsAlert, *, now: datetime) -> dict[str, Any]:
    payload = alert_payload(row, now=now)
    return {
        key: payload.get(key)
        for key in (
            "id",
            "fingerprint",
            "source",
            "severity",
            "status",
            "title",
            "first_seen_at",
            "last_seen_at",
            "resolved_at",
            "acknowledged_at",
            "silence_until",
        )
    }


def build_node_observability(
    *,
    s,
    node_code: str,
    now: datetime,
    metrics_stale_after_seconds: int,
    include_ru_history: bool = True,
) -> dict[str, Any] | None:
    wanted = str(node_code or "").strip().lower()
    node = s.query(Node).filter(func.lower(Node.code) == wanted).one_or_none()
    if node is None:
        return None
    normalized_now = _ops_utc_naive(now) or now
    stale_threshold = max(300, int(metrics_stale_after_seconds))
    observer_threshold = max(60, int(observer_stale_after_seconds()))
    latest_sample = (
        s.query(NodeHealthSample)
        .filter(func.lower(NodeHealthSample.node_code) == wanted)
        .order_by(NodeHealthSample.sampled_at.desc(), NodeHealthSample.id.desc())
        .first()
    )
    latest_runtime = (
        s.query(NodeRuntimeMetric)
        .filter(func.lower(NodeRuntimeMetric.node_code) == wanted)
        .order_by(NodeRuntimeMetric.sampled_at.desc(), NodeRuntimeMetric.id.desc())
        .first()
    )
    brain_panel_state = _panel_state_from_json(
        getattr(latest_sample, "transport_health_json", None)
    )
    sample_time = getattr(latest_sample, "sampled_at", None) or getattr(
        node, "last_health_at", None
    )
    sample_age = _source_age_seconds(
        now=normalized_now,
        sampled_at=sample_time,
    )
    if sample_time is None:
        brain_status, brain_reason = "missing", "brain_metrics_missing"
    elif sample_age is not None and sample_age > stale_threshold:
        brain_status, brain_reason = "stale", "brain_metrics_stale"
    elif brain_panel_state == "unavailable":
        brain_status, brain_reason = "unavailable", "brain_panel_unavailable"
    elif brain_panel_state in {"failed", "error"}:
        brain_status, brain_reason = "failed", "brain_panel_failed"
    elif latest_sample is not None and not bool(latest_sample.is_healthy):
        brain_status, brain_reason = "failed", "brain_probe_failed"
    else:
        brain_status, brain_reason = "ok", "brain_metrics_fresh"
    has_brain_source = sample_time is not None
    brain_details = {
        "cpu_percent": (
            None
            if latest_sample is not None
            and brain_panel_state in {"failed", "error", "unavailable"}
            and float(latest_sample.cpu_percent or 0.0) == 0.0
            else float(latest_sample.cpu_percent)
            if latest_sample is not None
            and latest_sample.cpu_percent is not None
            else float(getattr(node, "cpu_percent", 0.0) or 0.0)
            if has_brain_source
            else None
        ),
        "memory_used_mb": (
            int(latest_sample.memory_used_mb)
            if latest_sample is not None
            and latest_sample.memory_used_mb is not None
            else getattr(node, "memory_used_mb", None) if has_brain_source else None
        ),
        "memory_total_mb": (
            int(latest_sample.memory_total_mb)
            if latest_sample is not None
            and latest_sample.memory_total_mb is not None
            else getattr(node, "memory_total_mb", None) if has_brain_source else None
        ),
        "disk_used_gb": (
            float(latest_sample.disk_used_gb)
            if latest_sample is not None
            and latest_sample.disk_used_gb is not None
            else getattr(node, "disk_used_gb", None) if has_brain_source else None
        ),
        "disk_total_gb": (
            float(latest_sample.disk_total_gb)
            if latest_sample is not None
            and latest_sample.disk_total_gb is not None
            else getattr(node, "disk_total_gb", None) if has_brain_source else None
        ),
        "network_rx_mbps": (
            latest_sample.network_rx_mbps
            if latest_sample is not None
            else getattr(node, "network_rx_mbps", None) if has_brain_source else None
        ),
        "network_tx_mbps": (
            latest_sample.network_tx_mbps
            if latest_sample is not None
            else getattr(node, "network_tx_mbps", None) if has_brain_source else None
        ),
        "network_total_mbps": (
            latest_sample.network_total_mbps
            if latest_sample is not None
            else getattr(node, "network_total_mbps", None) if has_brain_source else None
        ),
        "panel_latency_ms": (
            latest_sample.panel_latency_ms
            if latest_sample is not None
            else getattr(node, "panel_latency_ms", None) if has_brain_source else None
        ),
        "panel_error_rate": (
            float(latest_sample.panel_error_rate or 0.0)
            if latest_sample is not None
            else float(getattr(node, "panel_error_rate", 0.0) or 0.0)
            if has_brain_source
            else None
        ),
        "probe_stage": (
            safe_probe_stage(latest_sample.probe_stage) or None
            if latest_sample is not None
            else (safe_probe_stage(getattr(node, "last_probe_stage", "")) or None)
            if has_brain_source
            else None
        ),
        "probe_error_kind": (
            safe_error_kind(latest_sample.probe_error_kind) or None
            if latest_sample is not None
            else (safe_error_kind(getattr(node, "last_probe_error_kind", "")) or None)
            if has_brain_source
            else None
        ),
        "probe_classification": (
            safe_probe_classification(latest_sample.probe_classification) or None
            if latest_sample is not None
            else (
                safe_probe_classification(
                    getattr(node, "last_probe_classification", "")
                )
                or None
            )
            if has_brain_source
            else None
        ),
    }

    runtime_time = getattr(latest_runtime, "sampled_at", None)
    runtime_panel_state = _panel_state_from_json(
        getattr(latest_runtime, "meta_json", None)
    )
    runtime_age = _source_age_seconds(
        now=normalized_now,
        sampled_at=runtime_time,
    )
    if runtime_time is None:
        runtime_status, runtime_reason = "missing", "runtime_missing"
    elif runtime_age is not None and runtime_age > stale_threshold:
        runtime_status, runtime_reason = "stale", "runtime_stale"
    elif runtime_panel_state == "unavailable":
        runtime_status, runtime_reason = "unavailable", "runtime_panel_unavailable"
    elif runtime_panel_state in {"failed", "error"}:
        runtime_status, runtime_reason = "failed", "runtime_panel_failed"
    else:
        runtime_status, runtime_reason = "ok", "runtime_fresh"
    runtime_panel_available = runtime_panel_state not in {
        "failed",
        "error",
        "unavailable",
    }
    runtime_details = {
        "source": str(getattr(latest_runtime, "source", "") or "") or None,
        "provisioned_clients_count": (
            int(latest_runtime.provisioned_clients_count or 0)
            if latest_runtime is not None and runtime_panel_available
            else None
        ),
        "online_connections_hint": (
            int(latest_runtime.online_connections_hint or 0)
            if latest_runtime is not None and runtime_panel_available
            else None
        ),
        "network_rx_mbps_1m": getattr(latest_runtime, "network_rx_mbps_1m", None),
        "network_tx_mbps_1m": getattr(latest_runtime, "network_tx_mbps_1m", None),
        "network_rx_mbps_5m": getattr(latest_runtime, "network_rx_mbps_5m", None),
        "network_tx_mbps_5m": getattr(latest_runtime, "network_tx_mbps_5m", None),
        "capacity_score": getattr(latest_runtime, "capacity_score", None),
        "capacity_state": (
            str(getattr(latest_runtime, "capacity_state", "") or "")
            or str(getattr(node, "capacity_state", "") or "unknown")
        ),
        "reject_reason": (
            str(getattr(latest_runtime, "reject_reason", "") or "")
            or str(getattr(node, "capacity_reject_reason", "") or "")
            or None
        ),
    }

    observer_time = getattr(node, "observer_last_push_at", None)
    observer_age = _source_age_seconds(
        now=normalized_now,
        sampled_at=observer_time,
    )
    if observer_time is None:
        observer_status, observer_reason = "missing", "observer_missing"
    elif observer_age is not None and observer_age > observer_threshold:
        observer_status, observer_reason = "stale", "observer_stale"
    else:
        observer_status, observer_reason = "ok", "observer_fresh"

    try:
        ru_latest = get_latest_ru_status(s, now=normalized_now)
    except RuProbeConfigurationError as error:
        ru_latest = {"nodes": []}
        ru_node = {
            "status": "failed",
            "sampled_at": None,
            "age_seconds": None,
            "threshold_seconds": RU_RUN_STALE_AFTER_SECONDS,
            "reason_code": "ru_configuration_invalid",
            "configuration_error_code": str(error.code),
            "target": None,
        }
    else:
        ru_node = next(
            (
                row
                for row in list(ru_latest.get("nodes") or [])
                if str(row.get("node_code") or "").strip().lower() == wanted
            ),
            None,
        )
    if ru_node is None:
        ru_node = {
            "status": "missing",
            "sampled_at": None,
            "age_seconds": None,
            "threshold_seconds": RU_RUN_STALE_AFTER_SECONDS,
            "reason_code": "ru_target_missing",
            "target": None,
        }
    ru_history = (
        get_ru_run_history(s, node_code=wanted, limit=10)
        if include_ru_history
        else None
    )
    policy = _node_capacity_policy_by_code(s).get(wanted)
    capacity = node_capacity_status(node, policy=policy, now=normalized_now)
    mapped_users = int(
        s.query(func.count(func.distinct(UserNode.tg_id)))
        .filter(UserNode.node_id == int(node.id))
        .scalar()
        or 0
    )
    alerts = (
        s.query(OpsAlert)
        .filter(func.lower(func.coalesce(OpsAlert.node_code, "")) == wanted)
        .filter(OpsAlert.status != "resolved")
        .order_by(OpsAlert.severity.asc(), OpsAlert.last_seen_at.desc())
        .limit(100)
        .all()
    )
    return {
        "ok": True,
        "generated_at": safe_iso(normalized_now),
        "node": {
            "code": wanted,
            "name": str(node.name or ""),
            "hoster_family": safe_hoster_family(node.hoster_family),
            "hoster_asn": safe_hoster_asn(node.hoster_asn),
            "weight": int(node.weight or 0),
        },
        "lifecycle": {
            "enabled": bool(node.enabled),
            "accepting_new_clients": bool(node.accepting_new_clients),
            "is_draining": bool(node.is_draining),
            "mapped_users": mapped_users,
        },
        "capacity": {
            "state": str(capacity.get("state") or "unknown"),
            "score": capacity.get("score"),
            "reject_reason": capacity.get("reject_reason"),
            "tx_mbps": capacity.get("tx_mbps"),
            "tx_ratio": capacity.get("tx_ratio"),
            "capacity_mbps": capacity.get("capacity_mbps"),
            "provisioned_clients_count": runtime_details["provisioned_clients_count"],
            "online_connections_hint": runtime_details["online_connections_hint"],
        },
        "sources": {
            "brain_metrics": _source_row(
                status=brain_status,
                sampled_at=sample_time,
                now=normalized_now,
                threshold_seconds=stale_threshold,
                reason_code=brain_reason,
                details=brain_details,
            ),
            "runtime": _source_row(
                status=runtime_status,
                sampled_at=runtime_time,
                now=normalized_now,
                threshold_seconds=stale_threshold,
                reason_code=runtime_reason,
                details=runtime_details,
            ),
            "observer": _source_row(
                status=observer_status,
                sampled_at=observer_time,
                now=normalized_now,
                threshold_seconds=observer_threshold,
                reason_code=observer_reason,
                details={
                    "last_batch_id": str(node.observer_last_batch_id or "") or None,
                    "unmatched_count": int(node.observer_unmatched_count or 0),
                    "parse_error_count": int(node.observer_parse_error_count or 0),
                },
            ),
            "ru_origin": dict(ru_node),
        },
        "network": {
            "ipv4_health": str(node.ipv4_health or "") or None,
            "ipv6_health": str(node.ipv6_health or "") or None,
            "edge_reachability_ok": node.edge_reachability_ok,
            "authenticated_egress_ok": node.authenticated_egress_ok,
            "last_authenticated_egress_at": safe_iso(node.last_authenticated_egress_at),
            "authenticated_egress_error_kind": safe_error_kind(
                node.authenticated_egress_error_kind
            )
            or None,
            "dataplane_ok": node.dataplane_ok,
            "dataplane_rtt_ms": node.dataplane_rtt_ms,
            "packet_loss_percent": node.packet_loss_percent,
            "tcp_retrans_percent": node.tcp_retrans_percent,
            "probe_classification": safe_probe_classification(
                node.last_probe_classification
            )
            or None,
            "last_probe_stage": safe_probe_stage(node.last_probe_stage) or None,
            "last_probe_error_kind": safe_error_kind(node.last_probe_error_kind) or None,
        },
        "transports": _safe_transport_rows(node),
        "ru": {
            "latest": dict(ru_node),
            **({"history": ru_history} if include_ru_history else {}),
        },
        "alerts": [_compact_node_alert(row, now=normalized_now) for row in alerts],
    }


def admin_search_results(
    *,
    s,
    q: str,
    limit: int = 20,
    allowed_kinds: set[str] | frozenset[str] | None = None,
    include_sensitive_user_filters: bool = True,
) -> list[dict[str, str]]:
    query_text = str(q or "").strip()
    if not 2 <= len(query_text) <= 128:
        raise ValueError("invalid_search_query")
    normalized_limit = max(1, min(int(limit), 20))
    escaped_query = (
        query_text.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    like = f"%{escaped_query.lower()}%"
    numeric_like = f"%{escaped_query}%"
    results: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    allowed = (
        {"user", "node", "order", "key"}
        if allowed_kinds is None
        else set(allowed_kinds) & {"user", "node", "order", "key"}
    )

    def add(item: dict[str, str]) -> None:
        key = (item["kind"], item["id"])
        if key in seen or len(results) >= normalized_limit:
            return
        seen.add(key)
        results.append(item)

    user_filters = [
        func.cast(User.tg_id, String).like(numeric_like, escape="\\"),
        func.lower(func.coalesce(User.username, "")).like(like, escape="\\"),
        func.lower(func.coalesce(User.display_name, "")).like(like, escape="\\"),
    ]
    if include_sensitive_user_filters:
        user_filters.extend(
            [
                func.lower(func.coalesce(User.app_install_id, "")).like(like, escape="\\"),
                func.lower(func.coalesce(User.email, "")).like(like, escape="\\"),
            ]
        )
    user_filter = or_(*user_filters)
    users = (
        s.query(User)
        .filter(user_filter)
        .order_by(User.tg_id.asc())
        .limit(normalized_limit)
        .all()
        if "user" in allowed
        else []
    )
    matching_devices = (
        s.query(AccountDevice)
        .filter(func.lower(AccountDevice.install_id).like(like, escape="\\"))
        .order_by(AccountDevice.last_seen_at.desc(), AccountDevice.id.asc())
        .limit(normalized_limit)
        .all()
        if "user" in allowed and include_sensitive_user_filters
        else []
    )
    account_ids = [
        str(row.account_id)
        for row in matching_devices
        if str(row.account_id or "").strip()
    ]
    if account_ids:
        users_by_account = {
            str(row.account_id): row
            for row in s.query(User)
            .filter(User.account_id.in_(account_ids))
            .order_by(User.tg_id.asc())
            .all()
            if str(row.account_id or "").strip()
        }
        for device in matching_devices:
            user = users_by_account.get(str(device.account_id or ""))
            if user is not None and all(
                int(existing.tg_id) != int(user.tg_id) for existing in users
            ):
                users.append(user)
    for user in users:
        access = "Активный доступ" if bool(user.is_active) else "Доступ выключен"
        username = str(user.username or "").strip()
        title = (
            str(user.display_name or "").strip()
            or (f"@{username}" if username else f"Пользователь {int(user.tg_id)}")
        )
        add(
            {
                "kind": "user",
                "id": str(int(user.tg_id)),
                "title": title,
                "subtitle": f"{access}, Telegram ID {int(user.tg_id)}",
                "href": f"/users?selected={int(user.tg_id)}",
            }
        )

    nodes = (
        s.query(Node)
        .filter(
            or_(
                func.lower(func.coalesce(Node.code, "")).like(like, escape="\\"),
                func.lower(func.coalesce(Node.name, "")).like(like, escape="\\"),
                func.lower(func.coalesce(Node.hoster_family, "")).like(like, escape="\\"),
                func.lower(func.coalesce(Node.hoster_asn, "")).like(like, escape="\\"),
            )
        )
        .order_by(Node.code.asc())
        .limit(normalized_limit)
        .all()
        if "node" in allowed
        else []
    )
    for node in nodes:
        code = str(node.code or "").strip().lower()
        lifecycle = (
            "Выводится из эксплуатации"
            if bool(node.is_draining)
            else "Включена"
            if bool(node.enabled)
            else "Выключена"
        )
        hoster = str(node.hoster_family or "").strip()
        subtitle = f"{lifecycle}, {hoster}" if hoster else lifecycle
        add(
            {
                "kind": "node",
                "id": code,
                "title": f"Нода {code.upper()}",
                "subtitle": subtitle,
                "href": f"/nodes?selected={quote(code, safe='')}",
            }
        )

    orders = (
        s.query(ExternalOrder)
        .filter(
            or_(
                func.lower(ExternalOrder.order_id).like(like, escape="\\"),
                func.cast(ExternalOrder.tg_id, String).like(numeric_like, escape="\\"),
            )
        )
        .order_by(ExternalOrder.created_at.desc(), ExternalOrder.id.desc())
        .limit(normalized_limit)
        .all()
        if "order" in allowed
        else []
    )
    for order in orders:
        order_id = str(order.order_id or "")
        add(
            {
                "kind": "order",
                "id": order_id,
                "title": f"Заказ {order_id}",
                "subtitle": (
                    f"Статус {str(order.status or 'unknown')}, "
                    f"провайдер {str(order.provider or 'unknown')}"
                ),
                "href": f"/payments?selected={quote(order_id, safe='')}",
            }
        )

    key_filter_parts = [
        func.cast(AccessKey.id, String).like(numeric_like, escape="\\"),
        func.cast(AccessKey.tg_id, String).like(numeric_like, escape="\\"),
    ]
    if include_sensitive_user_filters:
        key_filter_parts.extend(
            [
                func.lower(AccessKey.key_uuid).like(like, escape="\\"),
                func.lower(AccessKey.panel_email).like(like, escape="\\"),
            ]
        )
    key_filter = or_(*key_filter_parts)
    keys = (
        s.query(AccessKey)
        .filter(key_filter)
        .order_by(AccessKey.id.asc())
        .limit(normalized_limit)
        .all()
        if "key" in allowed
        else []
    )
    for key in keys:
        key_id = str(int(key.id))
        node_code = str(key.node_code or "").strip().lower() or "не назначена"
        add(
            {
                "kind": "key",
                "id": key_id,
                "title": f"Ключ #{key_id}",
                "subtitle": (
                    f"Нода {node_code}, пользователь {int(key.tg_id)}, "
                    f"состояние {str(key.state or 'unknown')}"
                ),
                "href": f"/users?selected={int(key.tg_id)}&tab=access",
            }
        )
    return results


def refresh_ops_alerts_for_current_state(
    *,
    s,
    now: datetime,
    free_limit_gb: int,
    cycle_days: int,
    stale_after_seconds: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    metrics_status = build_admin_metrics_status_snapshot(s=s, now=now, stale_after_seconds=stale_after_seconds)
    provider_status = provider_quota_status_rows(s=s, now=now)
    free_summary = free_tier_summary(s=s, now=now, free_limit_gb=free_limit_gb, cycle_days=cycle_days)
    capacity_payload = admin_nodes_capacity_payload(s=s, now=now)
    ru_status = get_latest_ru_status(s, now=now)
    ru_uploader_status = get_ru_uploader_status(s, now=now)
    candidates = build_alert_candidates(
        metrics_status=metrics_status,
        provider_status=provider_status,
        free_summary=free_summary,
        capacity_rows=list(capacity_payload.get("nodes") or []),
        ru_status=ru_status,
        ru_uploader_status=ru_uploader_status,
    )
    rows, notifications = refresh_ops_alerts(s=s, now=now, candidates=candidates)
    return [alert_payload(row, now=now) for row in rows], notifications, metrics_status, capacity_payload


def build_alert_candidates(
    *,
    metrics_status: dict[str, Any],
    provider_status: list[dict[str, Any]],
    free_summary: dict[str, Any],
    capacity_rows: list[dict[str, Any]],
    ru_status: dict[str, Any] | None = None,
    ru_uploader_status: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    confirmed_capacity_nodes = {
        str(row.get("code") or row.get("node_code") or "").strip().lower()
        for row in capacity_rows
        if str(row.get("capacity_state") or "").strip().lower() == "hard_reject"
        and row.get("enabled") is not False
        and row.get("alert_confirmed") is not False
    }
    for alert in list(metrics_status.get("active_alerts") or []):
        node_code = str(alert.get("node_code") or "").strip().lower()
        kind = str(alert.get("kind") or "").strip()
        if not node_code or not kind:
            continue
        # Panel API latency is control-plane telemetry. Keep it in the admin
        # dashboard, but do not page while durable dataplane/error checks stay
        # healthy.
        if kind == "latency_high":
            continue
        if kind == "error_rate_high" and node_code in confirmed_capacity_nodes:
            continue
        severity = "warning"
        title_by_kind = {
            "cpu_high": "стабильно высокая загрузка CPU",
            "memory_high": "стабильно высокая загрузка памяти",
            "disk_high": "заканчивается место на диске",
            "network_high": "канал близок к насыщению",
            "error_rate_high": "повторяются ошибки проверки доступности",
            "client_density_high": "слишком много активных клиентов",
            "observer_push_stale": "observer давно не присылал данные",
            "stale_metrics": "метрики давно не обновлялись",
        }
        title = title_by_kind.get(kind, f"неизвестное состояние мониторинга ({kind})")
        if kind in {"stale_metrics", "observer_push_stale"}:
            detail = "Пользовательский трафик не признан упавшим. Проверьте таймер и свежесть источника метрик."
        elif kind == "error_rate_high":
            detail = "Возможное влияние: новые подключения могут обходить ноду. Проверьте свежий dataplane-тест."
        else:
            detail = (
                f"Состояние подтверждено {NODE_METRICS_SUSTAINED_SAMPLES} последовательными замерами. "
                "Проверьте график и саму ноду; массовый перезапуск не требуется."
            )
        candidates.append(
            {
                "fingerprint": f"node_metrics:{node_code}:{kind}",
                "source": "node_metrics",
                "severity": severity,
                "title": f"Нода {node_code}: {title}",
                "body": detail,
                "node_code": node_code,
                "metadata": alert,
            }
        )
    enabled_capacity_rows = [row for row in capacity_rows if row.get("enabled") is not False]
    hard_reject_rows = [
        row
        for row in enabled_capacity_rows
        if str(row.get("capacity_state") or "").strip().lower() == "hard_reject"
        and row.get("alert_confirmed") is not False
    ]
    if hard_reject_rows:
        codes = sorted(
            {
                str(row.get("code") or row.get("node_code") or "").strip().lower()
                for row in hard_reject_rows
                if str(row.get("code") or row.get("node_code") or "").strip()
            }
        )
        reason_labels = {
            "unhealthy": "health-check считает ноду нездоровой",
            "stale": "метрики устарели",
            "cpu_hot": "перегружен CPU",
            "disk_full": "критически мало места на диске",
            "network_saturated": "насыщен канал",
            "packet_loss": "высокая потеря пакетов",
            "tcp_retrans": "много TCP-повторов",
            "not_accepting_new_clients": "выключена выдача новым клиентам",
            "draining": "нода в режиме вывода из пула",
        }
        reasons = sorted(
            {
                reason_labels.get(str(row.get("reject_reason") or "").strip().lower(), "неуточнённая причина")
                for row in hard_reject_rows
            }
        )
        pool_wide = bool(enabled_capacity_rows) and len(hard_reject_rows) == len(enabled_capacity_rows)
        dataplane_down = bool(hard_reject_rows) and all(
            row.get("edge_reachability_ok") is False or row.get("dataplane_ok") is False
            for row in hard_reject_rows
        )
        severity = "critical" if pool_wide and dataplane_down else "warning"
        if severity == "critical":
            title = "Не подтверждён пользовательский dataplane на всём пуле"
            impact = "Новые подключения могут не найти рабочую ноду."
        else:
            title = f"Маршрутизация временно ограничена на {len(codes)} нодах"
            impact = "Текущие соединения могут работать; ограничение касается выбора нод для новых подключений."
        body = (
            f"Ноды: {', '.join(codes)}. Причины: {', '.join(reasons)}. {impact} "
            "Действие: проверьте свежий dataplane и metrics timer; не перезапускайте весь пул сразу."
        )
        candidates.append(
            {
                "fingerprint": "node_capacity:pool",
                "source": "node_capacity",
                "severity": severity,
                "title": title,
                "body": body,
                "metadata": {"nodes": codes, "reasons": reasons, "pool_wide": pool_wide, "dataplane_down": dataplane_down},
            }
        )
    for row in provider_status:
        node_code = str(row.get("node_code") or "").strip().lower()
        state = str(row.get("state") or "").strip().lower()
        if not node_code or state not in {"warning", "critical"}:
            continue
        candidates.append(
            {
                "fingerprint": f"provider_quota:{node_code}",
                "source": "provider_quota",
                "severity": "critical" if state == "critical" else "warning",
                "title": f"Лимит провайдера для {node_code}: использовано {row.get('used_pct')}%",
                "body": (
                    f"Использовано {row.get('used_gb')} из {row.get('included_gb')} ГБ в текущем цикле. "
                    "Действие: проверить тариф или заранее вывести ноду из новой выдачи."
                ),
                "node_code": node_code,
                "metadata": row,
            }
        )
    if int(free_summary.get("over_cap_users") or 0) > 0:
        candidates.append(
            {
                "fingerprint": "free_tier:over_cap",
                "source": "free_tier",
                "severity": "warning",
                "title": "У пользователей бесплатного тарифа превышен лимит",
                "body": f"Пользователей сверх лимита: {int(free_summary.get('over_cap_users') or 0)}. Проверьте корректность сброса цикла и ограничения.",
                "metadata": free_summary,
            }
        )
    elif int(free_summary.get("near_cap_users") or 0) > 0:
        candidates.append(
            {
                "fingerprint": "free_tier:near_cap",
                "source": "free_tier",
                "severity": "warning",
                "title": "Пользователи бесплатного тарифа близки к лимиту",
                "body": f"Выше 80% лимита: {int(free_summary.get('near_cap_users') or 0)}. Это предупреждение, вмешательство обычно не требуется.",
                "metadata": free_summary,
            }
        )
    security = dict(metrics_status.get("security") or {})
    if int(security.get("payment_callback_invalid_signatures") or 0) > 0:
        candidates.append(
            {
                "fingerprint": "security:payment_callback_invalid_signature",
                "source": "security",
                "severity": "critical",
                "title": "Платёжные callback пришли с неверной подписью",
                "body": f"За 24 часа: {int(security.get('payment_callback_invalid_signatures') or 0)}. Действие: проверить источник запросов и секрет провайдера.",
                "metadata": security,
            }
        )
    ru = dict(ru_status or {})
    if str(ru.get("status") or "") == "stale":
        candidates.append(
            {
                "fingerprint": "ru_probe_run_stale",
                "source": "ru_probe",
                "severity": "critical",
                "title": "Запуск RU-origin устарел",
                "body": (
                    f"Возраст последнего пригодного запуска: {ru.get('age_seconds')} сек.; "
                    f"порог: {ru.get('threshold_seconds')} сек."
                ),
                "metadata": {
                    "status": ru.get("status"),
                    "age_seconds": ru.get("age_seconds"),
                    "threshold_seconds": ru.get("threshold_seconds"),
                    "reason_code": ru.get("reason_code"),
                    "sampled_at": ru.get("sampled_at"),
                },
            }
        )
    uploader = dict(ru_uploader_status or {})
    if str(uploader.get("status") or "") == "stale":
        candidates.append(
            {
                "fingerprint": "ru_probe_uploader_heartbeat_stale",
                "source": "ru_probe",
                "severity": "critical",
                "title": "Сигнал RU-загрузчика устарел",
                "body": (
                    f"Возраст последнего принятого сигнала: {uploader.get('age_seconds')} сек.; "
                    f"порог: {uploader.get('threshold_seconds')} сек."
                ),
                "metadata": {
                    "status": uploader.get("status"),
                    "age_seconds": uploader.get("age_seconds"),
                    "threshold_seconds": uploader.get("threshold_seconds"),
                    "reason_code": uploader.get("reason_code"),
                    "sampled_at": uploader.get("sampled_at"),
                },
            }
        )
    heartbeat = uploader.get("heartbeat")
    if isinstance(heartbeat, dict):
        pending_count = int(heartbeat.get("pending_count") or 0)
        blocked_count = int(heartbeat.get("blocked_count") or 0)
        quarantine_count = int(heartbeat.get("quarantine_count") or 0)
        if pending_count > 0:
            candidates.append(
                {
                    "fingerprint": "ru_probe_uploader_backlog",
                    "source": "ru_probe",
                    "severity": "warning",
                    "title": "Очередь RU-загрузчика не пуста",
                    "body": f"Ожидают отправки: {pending_count}.",
                    "metadata": {
                        "pending_count": pending_count,
                        "oldest_pending_at": heartbeat.get("oldest_pending_at"),
                    },
                }
            )
        if blocked_count > 0:
            candidates.append(
                {
                    "fingerprint": "ru_probe_uploader_blocked",
                    "source": "ru_probe",
                    "severity": "critical",
                    "title": "RU-загрузчик: есть заблокированные артефакты",
                    "body": f"Заблокировано: {blocked_count}.",
                    "metadata": {"blocked_count": blocked_count},
                }
            )
        if quarantine_count > 0:
            candidates.append(
                {
                    "fingerprint": "ru_probe_uploader_quarantine",
                    "source": "ru_probe",
                    "severity": "warning",
                    "title": "Карантин RU-загрузчика не пуст",
                    "body": f"Требуют проверки оператором: {quarantine_count}.",
                    "metadata": {"quarantine_count": quarantine_count},
                }
            )
        if heartbeat.get("archive_write_ok") is False:
            candidates.append(
                {
                    "fingerprint": "ru_probe_uploader_archive",
                    "source": "ru_probe",
                    "severity": "critical",
                    "title": "RU-загрузчик не записал архив",
                    "body": "Последний принятый сигнал сообщает об ошибке записи архива.",
                    "metadata": {
                        "archive_write_ok": False,
                        "last_error_code": heartbeat.get("last_error_code"),
                    },
                }
            )
        disk_state = str(heartbeat.get("disk_state") or "unknown")
        if disk_state in {"low", "critical"}:
            disk_state_text = (
                "критически мало места"
                if disk_state == "critical"
                else "мало места"
            )
            candidates.append(
                {
                    "fingerprint": "ru_probe_uploader_disk",
                    "source": "ru_probe",
                    "severity": "critical" if disk_state == "critical" else "warning",
                    "title": f"Диск RU-загрузчика: {disk_state_text}",
                    "body": "Последний принятый сигнал сообщает о нехватке места.",
                    "metadata": {
                        "disk_state": disk_state,
                        "disk_free_bytes": heartbeat.get("disk_free_bytes"),
                    },
                }
            )
    return candidates


def refresh_ops_alerts(*, s, now: datetime, candidates: list[dict[str, Any]]) -> tuple[list[OpsAlert], list[dict[str, Any]]]:
    environment = str(
        os.getenv("ADMIN_OPERATOR_ENVIRONMENT")
        or os.getenv("POKROV_ENVIRONMENT")
        or "production"
    ).strip().lower()
    fingerprints = sorted({str(item.get("fingerprint") or "") for item in candidates if str(item.get("fingerprint") or "")})
    existing_rows = s.query(OpsAlert).filter(
        OpsAlert.environment == environment,
        OpsAlert.source.in_(sorted(MANAGED_ALERT_SOURCES)),
    ).all()
    existing_by_fingerprint = {str(row.fingerprint or ""): row for row in existing_rows}
    seen = set()
    notifications: list[dict[str, Any]] = []

    for item in candidates:
        fingerprint = str(item.get("fingerprint") or "").strip()
        if not fingerprint:
            continue
        seen.add(fingerprint)
        row = existing_by_fingerprint.get(fingerprint)
        is_new = row is None or str(getattr(row, "status", "") or "") == "resolved"
        if row is None:
            row = OpsAlert(
                fingerprint=fingerprint,
                source=str(item.get("source") or "ops")[:64],
                severity=str(item.get("severity") or "warning")[:16],
                status="active",
                environment=environment,
                title=str(item.get("title") or fingerprint)[:180],
                body=str(item.get("body") or "")[:1000] or None,
                node_code=str(item.get("node_code") or "")[:32] or None,
                tg_id=int(item["tg_id"]) if item.get("tg_id") is not None else None,
                key_id=int(item["key_id"]) if item.get("key_id") is not None else None,
                first_seen_at=now,
                last_seen_at=now,
                created_at=now,
                updated_at=now,
            )
            s.add(row)
            existing_by_fingerprint[fingerprint] = row
        else:
            if str(row.status or "") == "resolved":
                row.status = "active"
                row.resolved_at = None
                row.first_seen_at = now
                row.acknowledged_at = None
                row.acknowledged_by = None
            row.severity = str(item.get("severity") or row.severity or "warning")[:16]
            row.source = str(item.get("source") or row.source or "ops")[:64]
            row.title = str(item.get("title") or row.title or fingerprint)[:180]
            row.body = str(item.get("body") or "")[:1000] or None
            row.node_code = str(item.get("node_code") or "")[:32] or None
            row.tg_id = int(item["tg_id"]) if item.get("tg_id") is not None else row.tg_id
            row.key_id = int(item["key_id"]) if item.get("key_id") is not None else row.key_id
            row.last_seen_at = now
            row.updated_at = now
        row.metadata_json = json.dumps(item.get("metadata") or {}, ensure_ascii=False, separators=(",", ":"))[:4000]
        if is_new and str(row.severity or "") in {"warning", "critical"}:
            notifications.append(
                {
                    "kind": "active",
                    "fingerprint": fingerprint,
                    "severity": row.severity,
                    "title": row.title,
                    "body": row.body,
                }
            )

    for row in existing_rows:
        fingerprint = str(row.fingerprint or "")
        if fingerprint in seen:
            continue
        if str(row.status or "") != "resolved":
            row.status = "resolved"
            row.resolved_at = now
            row.last_seen_at = now
            row.updated_at = now
            if str(row.severity or "") in {"warning", "critical"}:
                notifications.append(
                    {
                        "kind": "resolved",
                        "fingerprint": fingerprint,
                        "severity": row.severity,
                        "title": row.title,
                        "body": row.body,
                    }
                )

    s.flush()
    rows = (
        s.query(OpsAlert)
        .filter(OpsAlert.source.in_(sorted(MANAGED_ALERT_SOURCES)))
        .order_by(OpsAlert.status.asc(), OpsAlert.severity.asc(), OpsAlert.last_seen_at.desc())
        .all()
    )
    return rows, notifications


def ops_alert_notification_batches(notifications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Render compact Russian Telegram batches without internal fingerprints."""

    batches: list[dict[str, Any]] = []
    active = [item for item in notifications if str(item.get("kind") or "active") != "resolved"]
    resolved = [item for item in notifications if str(item.get("kind") or "") == "resolved"]

    if active:
        critical = any(str(item.get("severity") or "warning") == "critical" for item in active)
        header = "🛑 POKROV: критическая проблема" if critical else "⚠️ POKROV: нужна проверка"
        lines = [header]
        for item in active[:6]:
            title = str(item.get("title") or "Событие мониторинга").strip()
            body = str(item.get("body") or "").strip()
            lines.append(f"\n• {title}")
            if body:
                lines.append(body[:600])
        if len(active) > 6:
            lines.append(f"\nЕщё событий: {len(active) - 6}. Они сохранены в админ-панели.")
        batches.append(
            {
                "fingerprints": [str(item.get("fingerprint") or "") for item in active],
                "text": "\n".join(lines)[:3900],
            }
        )

    if resolved:
        lines = [f"✅ POKROV: восстановлено, закрыто событий — {len(resolved)}"]
        lines.append("Текущие проверки больше не подтверждают проблемы. Действий не требуется.")
        batches.append(
            {
                "fingerprints": [str(item.get("fingerprint") or "") for item in resolved],
                "text": "\n".join(lines)[:3900],
            }
        )
    return batches

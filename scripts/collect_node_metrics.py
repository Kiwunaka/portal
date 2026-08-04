from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "portal_bot"))

from db import SessionLocal, init_db  # noqa: E402
from models import Node, NodeCapacityPolicy, NodeHealthSample, NodeRuntimeMetric  # noqa: E402
from nodes_repo import NodeRuntime  # noqa: E402
from panel_client import PanelClient  # noqa: E402
from node_dataplane_probe import probe_node_endpoint  # noqa: E402
from authenticated_egress_probe import probe_authenticated_egress  # noqa: E402
from node_observability_sanitizer import (  # noqa: E402
    ERROR_KINDS as _SAFE_ERROR_KINDS,
    HOSTER_FAMILIES as _SAFE_HOSTER_FAMILIES,
    PROBE_CLASSIFICATIONS as _SAFE_PROBE_CLASSIFICATIONS,
    PROBE_STAGES as _SAFE_PROBE_STAGES,
    TRANSPORT_HEALTH_KEYS as _SAFE_TRANSPORT_KEYS,
    TRANSPORT_HEALTH_STATES as _SAFE_TRANSPORT_STATES,
    safe_error_kind as _shared_safe_error_kind,
    safe_hoster_asn,
    safe_hoster_family,
    safe_probe_classification as _shared_safe_probe_classification,
    safe_probe_stage as _shared_safe_probe_stage,
)
from node_policy import AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED, node_capacity_status  # noqa: E402


_NODE_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def _parse_only_codes(value: str) -> list[str]:
    """Parse an explicit, exact node-code allowlist for a scoped collector run."""

    raw_codes = str(value or "").split(",")
    codes = [code.strip().lower() for code in raw_codes]
    if not codes or any(not code or _NODE_CODE_RE.fullmatch(code) is None for code in codes):
        raise ValueError("--only requires comma-separated valid node codes")
    if len(set(codes)) != len(codes):
        raise ValueError("--only requires unique node codes")
    return sorted(codes)


def _to_runtime(node: Node) -> NodeRuntime:
    return NodeRuntime(
        id=node.id,
        code=node.code,
        name=node.name,
        host=node.host,
        vless_port=node.vless_port,
        reality_sni=node.reality_sni,
        reality_pbk=node.reality_pbk,
        reality_sid=node.reality_sid,
        fingerprint=node.fingerprint,
        flow=node.flow,
        panel_base_url=node.panel_base_url,
        panel_path=node.panel_path,
        panel_user=node.panel_user,
        panel_pass=node.panel_pass,
        inbound_id=node.inbound_id,
        accepting_new_clients=bool(getattr(node, "accepting_new_clients", True)),
        is_draining=bool(getattr(node, "is_draining", False)),
        weight=int(node.weight or 0),
        health_score=float(node.health_score or 0.0),
        last_health_at=node.last_health_at,
        is_healthy=bool(node.is_healthy),
        panel_latency_ms=node.panel_latency_ms,
        panel_error_rate=float(node.panel_error_rate or 0.0),
        active_clients=int(node.active_clients or 0),
        provisioned_clients_count=int(getattr(node, "provisioned_clients_count", node.active_clients or 0) or 0),
        online_connections_hint=int(getattr(node, "online_connections_hint", 0) or 0),
        cpu_percent=float(getattr(node, "cpu_percent", 0.0) or 0.0),
        network_rx_mbps=getattr(node, "network_rx_mbps", None),
        network_tx_mbps=getattr(node, "network_tx_mbps", None),
        network_total_mbps=getattr(node, "network_total_mbps", None),
        network_rx_mbps_1m=getattr(node, "network_rx_mbps_1m", None),
        network_tx_mbps_1m=getattr(node, "network_tx_mbps_1m", None),
        network_rx_mbps_5m=getattr(node, "network_rx_mbps_5m", None),
        network_tx_mbps_5m=getattr(node, "network_tx_mbps_5m", None),
        tcp_retrans_percent=getattr(node, "tcp_retrans_percent", None),
        packet_loss_percent=getattr(node, "packet_loss_percent", None),
        disk_used_gb=getattr(node, "disk_used_gb", None),
        disk_total_gb=getattr(node, "disk_total_gb", None),
        disk_free_gb=getattr(node, "disk_free_gb", None),
        edge_reachability_ok=getattr(node, "edge_reachability_ok", None),
        authenticated_egress_ok=getattr(node, "authenticated_egress_ok", None),
        last_authenticated_egress_at=getattr(node, "last_authenticated_egress_at", None),
        authenticated_egress_error_kind=getattr(node, "authenticated_egress_error_kind", None),
        dataplane_ok=getattr(node, "dataplane_ok", None),
        dataplane_rtt_ms=getattr(node, "dataplane_rtt_ms", None),
        capacity_score=getattr(node, "capacity_score", None),
        capacity_state=getattr(node, "capacity_state", None),
        capacity_reject_reason=getattr(node, "capacity_reject_reason", None),
        last_ok_at=node.last_ok_at,
        last_probe_at=getattr(node, "last_probe_at", None),
    )


def _calc_score(
    *,
    latency_ms: int | None,
    error_rate: float,
    active_clients: int,
    healthy: bool,
    cpu_percent: float = 0.0,
    memory_used_mb: int = 0,
    memory_total_mb: int = 0,
    disk_used_gb: float = 0.0,
    disk_total_gb: float = 0.0,
) -> float:
    if not healthy:
        return 0.0
    latency_penalty = min(max(latency_ms or 0, 0), 3000) / 30.0
    error_penalty = max(0.0, min(error_rate, 1.0)) * 40.0
    memory_percent = (float(memory_used_mb or 0) / float(memory_total_mb or 0) * 100.0) if int(memory_total_mb or 0) > 0 else 0.0
    disk_percent = (float(disk_used_gb or 0.0) / float(disk_total_gb or 0.0) * 100.0) if float(disk_total_gb or 0.0) > 0 else 0.0
    cpu_penalty = min(max(float(cpu_percent or 0.0), 0.0), 100.0) / 4.0
    memory_penalty = min(max(memory_percent, 0.0), 100.0) / 5.0
    disk_penalty = min(max(disk_percent, 0.0), 100.0) / 6.0
    score = 100.0 - latency_penalty - error_penalty - cpu_penalty - memory_penalty - disk_penalty
    return max(0.0, round(score, 3))


def _rolling_error_rate(s, node_code: str, window: int) -> float:
    rows = (
        s.query(NodeHealthSample.is_healthy)
        .filter(NodeHealthSample.node_code == node_code)
        .order_by(NodeHealthSample.id.desc())
        .limit(max(1, int(window)))
        .all()
    )
    if not rows:
        return 0.0
    total = len(rows)
    errors = sum(1 for r in rows if not bool(r[0]))
    return errors / total


def _safe_error_kind(value: object, fallback: str = "probe_failed") -> str:
    return _shared_safe_error_kind(value, fallback)


def _safe_probe_stage(value: object, fallback: str = "probe") -> str:
    return _shared_safe_probe_stage(value, fallback)


def _safe_probe_classification(value: object, fallback: str = "probe_failed") -> str:
    return _shared_safe_probe_classification(value, fallback)


def _nullable_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _nullable_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _json_text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except Exception:
        return _string_or_none(value)


def _json_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items() if str(key or "").strip()}
    text = _string_or_none(value)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except Exception:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {str(key): item for key, item in parsed.items() if str(key or "").strip()}


def _inbound_clients(inbound: dict) -> list[dict]:
    settings = _json_dict(inbound.get("settings", "{}"))
    clients = settings.get("clients", []) or []
    return clients if isinstance(clients, list) else []


def _has_required_system_metrics(
    *,
    cpu_percent: float | None,
    memory_used_mb: int | None,
    memory_total_mb: int | None,
    disk_used_gb: float | None,
    disk_total_gb: float | None,
    disk_free_gb: float | None,
    network_rx_bytes_total: int | None,
    network_tx_bytes_total: int | None,
    network_rx_bytes_per_sec: int | None,
    network_tx_bytes_per_sec: int | None,
) -> bool:
    """A fresh sample is usable only when every required metric family arrived."""
    has_rx = network_rx_bytes_total is not None or network_rx_bytes_per_sec is not None
    has_tx = network_tx_bytes_total is not None or network_tx_bytes_per_sec is not None
    return all(
        value is not None
        for value in (
            cpu_percent,
            memory_used_mb,
            memory_total_mb,
            disk_used_gb,
            disk_total_gb,
            disk_free_gb,
        )
    ) and has_rx and has_tx


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _bytes_per_second_to_mbps(value: object) -> float | None:
    numeric = _nullable_float(value)
    if numeric is None or numeric < 0:
        return None
    return round((numeric * 8.0) / 1_000_000.0, 3)


def _combine_probe_root_cause(
    *,
    panel_state: str,
    panel_stage: str,
    panel_error_kind: str,
    panel_error_message: str,
    dataplane_state: str,
    dataplane_stage: str,
    dataplane_error_kind: str,
    dataplane_error_message: str,
    dataplane_summary: str,
    dataplane_detail: str,
) -> tuple[str, str]:
    if panel_state == "healthy":
        return dataplane_summary, dataplane_detail

    stage_label = str(panel_stage or "panel probe").replace("_", " ").strip()
    if stage_label.startswith("panel "):
        stage_label = stage_label[len("panel ") :].strip() or "probe"
    if dataplane_state == "healthy":
        summary = f"Panel {stage_label} failed while dataplane remained healthy."
    elif dataplane_state == "failed":
        summary = f"Panel {stage_label} failed and dataplane also failed."
    else:
        summary = f"Panel {stage_label} failed."

    details: list[str] = []
    if panel_error_message or panel_error_kind:
        details.append(f"panel error: {panel_error_message or panel_error_kind}")
    if dataplane_state == "healthy":
        details.append(f"dataplane healthy: {dataplane_detail or dataplane_summary}")
    elif dataplane_error_message or dataplane_error_kind:
        details.append(f"dataplane error: {dataplane_error_message or dataplane_error_kind}")
        if dataplane_detail:
            details.append(dataplane_detail)
    elif dataplane_detail:
        details.append(dataplane_detail)
    return summary, " ".join(part for part in details if part).strip()


def _build_transport_health_payload(
    *,
    panel_state: str,
    panel_stage: str,
    panel_error_kind: str,
    panel_error_message: str,
    dataplane_state: str,
    dataplane_stage: str,
    dataplane_error_kind: str,
    dataplane_error_message: str,
    authenticated_egress_state: str,
    authenticated_egress_error_kind: str,
    authenticated_egress_required: bool,
    metrics_complete: bool,
    probe: dict[str, object] | None,
) -> dict[str, object]:
    raw_transport = _json_dict((probe or {}).get("transport_health"))
    payload = {
        key: str(raw_transport.get(key) or "unknown")
        if str(raw_transport.get(key) or "unknown") in _SAFE_TRANSPORT_STATES
        else "unknown"
        for key in _SAFE_TRANSPORT_KEYS
    }
    safe_dataplane_error_kind = _safe_error_kind(
        dataplane_error_kind,
        "probe_failed" if dataplane_state != "healthy" else "",
    )
    dataplane_summary = safe_dataplane_error_kind or "edge_reachability_healthy"
    dataplane_detail = dataplane_summary
    safe_panel_error_kind = _safe_error_kind(
        panel_error_kind,
        "panel_probe_failed" if panel_state != "healthy" else "",
    )
    root_cause_summary, root_cause_detail = _combine_probe_root_cause(
        panel_state=panel_state,
        panel_stage=panel_stage,
        panel_error_kind=safe_panel_error_kind,
        panel_error_message=safe_panel_error_kind,
        dataplane_state=dataplane_state,
        dataplane_stage=dataplane_stage,
        dataplane_error_kind=safe_dataplane_error_kind,
        dataplane_error_message=safe_dataplane_error_kind,
        dataplane_summary=dataplane_summary,
        dataplane_detail=dataplane_detail,
    )
    if (
        authenticated_egress_required
        and panel_state == "healthy"
        and dataplane_state == "healthy"
        and authenticated_egress_state != "healthy"
    ):
        root_cause_summary = (
            "Authenticated egress failed while edge reachability passed."
            if authenticated_egress_state == "failed"
            else "Authenticated egress is unavailable while edge reachability passed."
        )
        root_cause_detail = authenticated_egress_error_kind or "authenticated_egress_unavailable"
    payload.update(
        {
            "panel_state": panel_state,
            "panel_stage": panel_stage,
            "panel_error_kind": safe_panel_error_kind,
            "panel_error_message": safe_panel_error_kind or None,
            "dataplane_state": dataplane_state,
            "dataplane_stage": dataplane_stage,
            "dataplane_error_kind": safe_dataplane_error_kind,
            "dataplane_error_message": safe_dataplane_error_kind or None,
            "edge_reachability_state": dataplane_state,
            "authenticated_egress_state": authenticated_egress_state,
            "authenticated_egress_error_kind": _safe_error_kind(
                authenticated_egress_error_kind,
                "authenticated_egress_unavailable" if authenticated_egress_state != "healthy" else "",
            ),
            "metrics_state": "complete" if metrics_complete else "missing",
            "root_cause_summary": root_cause_summary,
            "root_cause_detail": root_cause_detail,
        }
    )
    target_semantics = str((probe or {}).get("target_semantics") or "").strip()
    if target_semantics in {"telegram_app_path", "telegram_web_path", "generic_path"}:
        payload["target_semantics"] = target_semantics
    return payload


def _network_rate_from_totals(
    *,
    current_total: int | None,
    previous_total: int | None,
    previous_at: datetime | None,
    sampled_at: datetime,
) -> float | None:
    if current_total is None or previous_total is None or previous_at is None:
        return None
    delta = int(current_total) - int(previous_total)
    if delta < 0:
        return None
    elapsed_seconds = max(60.0, float((sampled_at - previous_at).total_seconds()))
    if elapsed_seconds <= 0:
        return None
    return round(((delta * 8.0) / elapsed_seconds) / 1_000_000.0, 3)


def _resolve_network_rates(
    *,
    previous_sample: NodeHealthSample | None,
    sampled_at: datetime,
    rx_total: int | None,
    tx_total: int | None,
    rx_bytes_per_sec: int | None,
    tx_bytes_per_sec: int | None,
) -> tuple[float | None, float | None, float | None]:
    prev_rx_total = _nullable_int(getattr(previous_sample, "network_rx_bytes_total", None))
    prev_tx_total = _nullable_int(getattr(previous_sample, "network_tx_bytes_total", None))
    prev_at = getattr(previous_sample, "sampled_at", None) if previous_sample else None
    rx_mbps = _network_rate_from_totals(
        current_total=rx_total,
        previous_total=prev_rx_total,
        previous_at=prev_at,
        sampled_at=sampled_at,
    )
    tx_mbps = _network_rate_from_totals(
        current_total=tx_total,
        previous_total=prev_tx_total,
        previous_at=prev_at,
        sampled_at=sampled_at,
    )
    if rx_mbps is None:
        rx_mbps = _bytes_per_second_to_mbps(rx_bytes_per_sec)
    if tx_mbps is None:
        tx_mbps = _bytes_per_second_to_mbps(tx_bytes_per_sec)
    total_mbps = None
    if rx_mbps is not None or tx_mbps is not None:
        total_mbps = round(float(rx_mbps or 0.0) + float(tx_mbps or 0.0), 3)
    return rx_mbps, tx_mbps, total_mbps


def _average_with_history(s, *, node_code: str, attr: str, current_value: float | None, limit: int = 4) -> float | None:
    values: list[float] = []
    if current_value is not None:
        values.append(float(current_value))
    rows = (
        s.query(NodeHealthSample)
        .filter(NodeHealthSample.node_code == node_code)
        .order_by(NodeHealthSample.sampled_at.desc(), NodeHealthSample.id.desc())
        .limit(max(1, int(limit)))
        .all()
    )
    for row in rows:
        value = _nullable_float(getattr(row, attr, None))
        if value is not None:
            values.append(float(value))
    if not values:
        return None
    return round(sum(values) / len(values), 3)


async def _collect_one(*, node: Node, error_window: int, source: str) -> dict:
    runtime = _to_runtime(node)
    client = PanelClient(runtime)
    started = time.perf_counter()
    now = _utcnow()
    panel_healthy = False
    latency_ms: int | None = None
    active_clients = 0
    online_connections_hint = 0
    total_up_bytes = 0
    total_down_bytes = 0
    cpu_percent: float | None = None
    memory_used_mb: int | None = None
    memory_total_mb: int | None = None
    disk_used_gb: float | None = None
    disk_total_gb: float | None = None
    disk_free_gb: float | None = None
    network_rx_bytes_total: int | None = None
    network_tx_bytes_total: int | None = None
    network_rx_bytes_per_sec: int | None = None
    network_tx_bytes_per_sec: int | None = None
    network_rx_mbps: float | None = None
    network_tx_mbps: float | None = None
    network_total_mbps: float | None = None
    panel_stage = "panel_login"
    panel_error_kind = "panel_login_failed"
    panel_error_message = "panel_login_failed"
    panel_state = "failed"
    probe_at = now
    probe: dict | None = None
    dataplane_latency_ms: int | None = None
    metrics_complete = False

    try:
        ok = await client.login()
        if ok:
            panel_stage = "panel_status"
            panel_error_kind = ""
            panel_error_message = ""
            system_metrics = await client.get_system_metrics()
            cpu_percent = _nullable_float(system_metrics.get("cpu_percent"))
            memory_used_mb = _nullable_int(system_metrics.get("memory_used_mb"))
            memory_total_mb = _nullable_int(system_metrics.get("memory_total_mb"))
            disk_used_gb = _nullable_float(system_metrics.get("disk_used_gb"))
            disk_total_gb = _nullable_float(system_metrics.get("disk_total_gb"))
            disk_free_gb = _nullable_float(system_metrics.get("disk_free_gb"))
            network_rx_bytes_total = _nullable_int(system_metrics.get("network_rx_bytes_total"))
            network_tx_bytes_total = _nullable_int(system_metrics.get("network_tx_bytes_total"))
            network_rx_bytes_per_sec = _nullable_int(system_metrics.get("network_rx_bytes_per_sec"))
            network_tx_bytes_per_sec = _nullable_int(system_metrics.get("network_tx_bytes_per_sec"))
            metrics_complete = _has_required_system_metrics(
                cpu_percent=cpu_percent,
                memory_used_mb=memory_used_mb,
                memory_total_mb=memory_total_mb,
                disk_used_gb=disk_used_gb,
                disk_total_gb=disk_total_gb,
                disk_free_gb=disk_free_gb,
                network_rx_bytes_total=network_rx_bytes_total,
                network_tx_bytes_total=network_tx_bytes_total,
                network_rx_bytes_per_sec=network_rx_bytes_per_sec,
                network_tx_bytes_per_sec=network_tx_bytes_per_sec,
            )
            try:
                online_summary = await client.get_node_online_summary()
                online_connections_hint = int((online_summary or {}).get("online_connections_now") or 0)
            except Exception:
                online_connections_hint = 0
            panel_stage = "panel_inbound_lookup"
            inbounds = await client._get_inbounds()
            for inb in inbounds:
                if int(inb.get("id") or 0) != int(runtime.inbound_id):
                    continue
                active_clients = len(_inbound_clients(inb))
                try:
                    for stat in inb.get("clientStats", []) or []:
                        total_up_bytes += int(stat.get("up", 0) or 0)
                        total_down_bytes += int(stat.get("down", 0) or 0)
                except Exception:
                    total_up_bytes = 0
                    total_down_bytes = 0
                panel_healthy = True
                panel_state = "healthy"
                panel_stage = "panel_inbound_lookup"
                panel_error_kind = ""
                panel_error_message = ""
                break
            if not panel_healthy:
                panel_error_kind = "inbound_not_found"
                panel_error_message = "inbound_not_found"
        latency_ms = int((time.perf_counter() - started) * 1000)
    except Exception:
        latency_ms = int((time.perf_counter() - started) * 1000)
        panel_error_kind = "panel_probe_failed"
        panel_error_message = panel_error_kind
    finally:
        await client.close()

    try:
        probe = await asyncio.to_thread(
            probe_node_endpoint,
            host=str(runtime.host or "").strip(),
            port=int(runtime.vless_port or 443),
            sni=str(runtime.reality_sni or runtime.host or "").strip() or None,
        )
        probe_at = probe.get("probed_at") or now
        dataplane_latency_ms = _nullable_int(probe.get("latency_ms"))
    except Exception:  # pragma: no cover - defensive fallback
        probe = {
            "ok": False,
            "stage": "probe",
            "error_kind": "probe_failed",
            "error_message": "probe_failed",
            "probe_classification": "probe_failed",
            "ipv4_health": "unknown",
            "ipv6_health": "unknown",
            "transport_health": {},
            "root_cause_summary": "probe_failed",
            "root_cause_detail": "probe_failed",
        }
        probe_at = now
    edge_reachability_ok = bool((probe or {}).get("edge_reachability_ok", (probe or {}).get("ok")))
    dataplane_stage = _safe_probe_stage((probe or {}).get("stage"))
    dataplane_error_kind = _safe_error_kind((probe or {}).get("error_kind"))
    dataplane_error_message = dataplane_error_kind or None
    dataplane_state = "healthy" if edge_reachability_ok else "failed"

    if edge_reachability_ok:
        try:
            authenticated_probe = await asyncio.to_thread(
                probe_authenticated_egress,
                node_code=str(runtime.code or "").strip(),
                host=str(runtime.host or "").strip(),
                port=int(runtime.vless_port or 443),
            )
        except Exception:  # pragma: no cover - defensive fallback
            authenticated_probe = {
                "ok": None,
                "state": "unavailable",
                "stage": "authenticated_egress",
                "error_kind": "authenticated_egress_probe_failed",
                "probe_classification": "authenticated_egress_unavailable",
                "probed_at": now,
            }
    else:
        authenticated_probe = {
            "ok": None,
            "state": "unavailable",
            "stage": "authenticated_egress",
            "error_kind": "prerequisite_failed",
            "probe_classification": "authenticated_egress_unavailable",
            "probed_at": now,
        }
    authenticated_raw_ok = authenticated_probe.get("ok")
    authenticated_egress_ok = authenticated_raw_ok if isinstance(authenticated_raw_ok, bool) else None
    authenticated_egress_state = (
        "healthy" if authenticated_egress_ok is True else ("failed" if authenticated_egress_ok is False else "unavailable")
    )
    authenticated_egress_error_kind = _safe_error_kind(
        authenticated_probe.get("error_kind"),
        "authenticated_egress_unavailable" if authenticated_egress_ok is not True else "",
    )
    authenticated_probe_at = authenticated_probe.get("probed_at")
    if not isinstance(authenticated_probe_at, datetime):
        authenticated_probe_at = now

    healthy = bool(
        panel_healthy
        and dataplane_state == "healthy"
        and (not AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED or authenticated_egress_ok is True)
        and metrics_complete
    )
    if panel_state != "healthy":
        probe_stage = panel_stage
        probe_error_kind = panel_error_kind
        probe_error_message = panel_error_message
    elif dataplane_state != "healthy":
        probe_stage = dataplane_stage
        probe_error_kind = dataplane_error_kind
        probe_error_message = dataplane_error_message
    elif AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED:
        probe_stage = "authenticated_egress"
        probe_error_kind = authenticated_egress_error_kind
        probe_error_message = ""
    else:
        probe_stage = dataplane_stage
        probe_error_kind = ""
        probe_error_message = ""
    selected_probe_at = (
        authenticated_probe_at
        if AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED and panel_state == "healthy" and dataplane_state == "healthy"
        else probe_at
    )

    hoster_family = safe_hoster_family((probe or {}).get("hoster_family"))
    hoster_asn = safe_hoster_asn((probe or {}).get("hoster_asn"))
    hoster_subnet = None
    authenticated_classification_active = bool(
        AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED and panel_state == "healthy" and dataplane_state == "healthy"
    )
    probe_classification = _safe_probe_classification(
        authenticated_probe.get("probe_classification")
        if authenticated_classification_active
        else (probe or {}).get("probe_classification"),
        (
            "authenticated_egress_unavailable"
            if authenticated_classification_active and authenticated_egress_ok is not True
            else "edge_reachability_healthy"
        ),
    )
    ipv4_health = str((probe or {}).get("ipv4_health") or "unknown").strip().lower()
    ipv6_health = str((probe or {}).get("ipv6_health") or "unknown").strip().lower()
    if ipv4_health not in _SAFE_TRANSPORT_STATES:
        ipv4_health = "unknown"
    if ipv6_health not in _SAFE_TRANSPORT_STATES:
        ipv6_health = "unknown"
    transport_health_payload = _build_transport_health_payload(
        panel_state=panel_state,
        panel_stage=panel_stage,
        panel_error_kind=panel_error_kind,
        panel_error_message=panel_error_message,
        dataplane_state=dataplane_state,
        dataplane_stage=dataplane_stage,
        dataplane_error_kind=dataplane_error_kind,
        dataplane_error_message=dataplane_error_message,
        authenticated_egress_state=authenticated_egress_state,
        authenticated_egress_error_kind=authenticated_egress_error_kind,
        authenticated_egress_required=AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED,
        metrics_complete=metrics_complete,
        probe=probe,
    )
    transport_health_json = _json_text(transport_health_payload)

    s = SessionLocal()
    try:
        previous_sample = (
            s.query(NodeHealthSample)
            .filter(NodeHealthSample.node_code == runtime.code)
            .order_by(NodeHealthSample.sampled_at.desc(), NodeHealthSample.id.desc())
            .first()
        )
        network_rx_mbps, network_tx_mbps, network_total_mbps = _resolve_network_rates(
            previous_sample=previous_sample,
            sampled_at=now,
            rx_total=network_rx_bytes_total,
            tx_total=network_tx_bytes_total,
            rx_bytes_per_sec=network_rx_bytes_per_sec,
            tx_bytes_per_sec=network_tx_bytes_per_sec,
        )
        network_rx_mbps_1m = network_rx_mbps
        network_tx_mbps_1m = network_tx_mbps
        network_rx_mbps_5m = _average_with_history(
            s,
            node_code=runtime.code,
            attr="network_rx_mbps",
            current_value=network_rx_mbps,
            limit=4,
        )
        network_tx_mbps_5m = _average_with_history(
            s,
            node_code=runtime.code,
            attr="network_tx_mbps",
            current_value=network_tx_mbps,
            limit=4,
        )
        error_rate = _rolling_error_rate(s, runtime.code, error_window)
        if not healthy:
            error_rate = min(1.0, max(error_rate, 0.5))
        score = _calc_score(
            latency_ms=dataplane_latency_ms if dataplane_latency_ms is not None else latency_ms,
            error_rate=error_rate,
            active_clients=active_clients,
            healthy=healthy,
            cpu_percent=cpu_percent,
            memory_used_mb=int(memory_used_mb or 0),
            memory_total_mb=int(memory_total_mb or 0),
            disk_used_gb=float(disk_used_gb or 0.0),
            disk_total_gb=float(disk_total_gb or 0.0),
        )
        sample = NodeHealthSample(
            node_code=runtime.code,
            sampled_at=now,
            panel_latency_ms=latency_ms,
            panel_error_rate=error_rate,
            active_clients=active_clients,
            cpu_percent=cpu_percent,
            total_up_bytes=max(0, int(total_up_bytes)),
            total_down_bytes=max(0, int(total_down_bytes)),
            total_traffic_bytes=max(0, int(total_up_bytes) + int(total_down_bytes)),
            is_healthy=healthy,
            score=score,
            source=source,
            probe_at=selected_probe_at,
            probe_stage=probe_stage,
            probe_error_kind=probe_error_kind or None,
            probe_error_message=probe_error_message or None,
            probe_classification=probe_classification,
            ipv4_health=ipv4_health,
            ipv6_health=ipv6_health,
            transport_health_json=transport_health_json,
        )
        sample.memory_used_mb = _nullable_int(memory_used_mb)
        sample.memory_total_mb = _nullable_int(memory_total_mb)
        sample.disk_used_gb = _nullable_float(disk_used_gb)
        sample.disk_total_gb = _nullable_float(disk_total_gb)
        sample.disk_free_gb = _nullable_float(disk_free_gb)
        sample.network_rx_bytes_total = _nullable_int(network_rx_bytes_total)
        sample.network_tx_bytes_total = _nullable_int(network_tx_bytes_total)
        sample.network_rx_mbps = _nullable_float(network_rx_mbps)
        sample.network_tx_mbps = _nullable_float(network_tx_mbps)
        sample.network_total_mbps = _nullable_float(network_total_mbps)
        s.add(sample)

        row = s.query(Node).filter(Node.id == node.id).first()
        if row:
            row.health_score = score
            row.last_health_at = now
            row.is_healthy = healthy
            row.panel_latency_ms = latency_ms
            row.panel_error_rate = error_rate
            row.active_clients = active_clients
            row.provisioned_clients_count = active_clients
            row.online_connections_hint = online_connections_hint
            row.cpu_percent = cpu_percent
            row.memory_used_mb = _nullable_int(memory_used_mb)
            row.memory_total_mb = _nullable_int(memory_total_mb)
            row.disk_used_gb = _nullable_float(disk_used_gb)
            row.disk_total_gb = _nullable_float(disk_total_gb)
            row.disk_free_gb = _nullable_float(disk_free_gb)
            row.network_rx_bytes_total = _nullable_int(network_rx_bytes_total)
            row.network_tx_bytes_total = _nullable_int(network_tx_bytes_total)
            row.network_rx_mbps = _nullable_float(network_rx_mbps)
            row.network_tx_mbps = _nullable_float(network_tx_mbps)
            row.network_total_mbps = _nullable_float(network_total_mbps)
            row.network_rx_mbps_1m = _nullable_float(network_rx_mbps_1m)
            row.network_tx_mbps_1m = _nullable_float(network_tx_mbps_1m)
            row.network_rx_mbps_5m = _nullable_float(network_rx_mbps_5m)
            row.network_tx_mbps_5m = _nullable_float(network_tx_mbps_5m)
            row.edge_reachability_ok = edge_reachability_ok
            row.authenticated_egress_ok = authenticated_egress_ok
            row.last_authenticated_egress_at = authenticated_probe_at
            row.authenticated_egress_error_kind = authenticated_egress_error_kind or None
            row.dataplane_ok = dataplane_state == "healthy"
            row.dataplane_rtt_ms = dataplane_latency_ms if dataplane_state == "healthy" else None
            row.last_probe_at = selected_probe_at
            row.last_probe_stage = probe_stage or None
            row.last_probe_error_kind = probe_error_kind or None
            row.last_probe_error_message = probe_error_message or None
            row.hoster_family = hoster_family
            row.hoster_asn = hoster_asn
            row.hoster_subnet = hoster_subnet
            row.ipv4_health = ipv4_health
            row.ipv6_health = ipv6_health
            row.last_probe_classification = probe_classification
            row.transport_health_json = transport_health_json
            policy = s.query(NodeCapacityPolicy).filter(NodeCapacityPolicy.node_code == runtime.code).first()
            capacity = node_capacity_status(row, policy=policy, now=now)
            row.capacity_score = float(capacity.get("score") or 0.0)
            row.capacity_state = str(capacity.get("state") or "unknown")
            row.capacity_reject_reason = str(capacity.get("reject_reason") or "") or None
            s.add(
                NodeRuntimeMetric(
                    node_code=runtime.code,
                    sampled_at=now,
                    source=source,
                    provisioned_clients_count=int(active_clients),
                    online_connections_hint=int(online_connections_hint),
                    network_rx_mbps_1m=_nullable_float(network_rx_mbps_1m),
                    network_tx_mbps_1m=_nullable_float(network_tx_mbps_1m),
                    network_rx_mbps_5m=_nullable_float(network_rx_mbps_5m),
                    network_tx_mbps_5m=_nullable_float(network_tx_mbps_5m),
                    network_total_mbps=_nullable_float(network_total_mbps),
                    cpu_percent=_nullable_float(cpu_percent),
                    memory_used_mb=_nullable_int(memory_used_mb),
                    memory_total_mb=_nullable_int(memory_total_mb),
                    edge_reachability_ok=edge_reachability_ok,
                    authenticated_egress_ok=authenticated_egress_ok,
                    dataplane_ok=dataplane_state == "healthy",
                    dataplane_rtt_ms=dataplane_latency_ms if dataplane_state == "healthy" else None,
                    capacity_score=float(capacity.get("score") or 0.0),
                    capacity_state=str(capacity.get("state") or "unknown"),
                    reject_reason=str(capacity.get("reject_reason") or "") or None,
                    meta_json=json.dumps(
                        {
                            "panel_state": panel_state,
                            "dataplane_state": dataplane_state,
                            "edge_reachability_state": dataplane_state,
                            "authenticated_egress_state": authenticated_egress_state,
                            "authenticated_egress_error_kind": authenticated_egress_error_kind,
                            "probe_stage": probe_stage,
                            "probe_error_kind": probe_error_kind,
                        },
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                )
            )
            if healthy:
                row.last_ok_at = now
        s.commit()
        return {
            "code": runtime.code,
            "healthy": healthy,
            "score": score,
            "latency_ms": latency_ms,
            "dataplane_rtt_ms": dataplane_latency_ms,
            "active_clients": active_clients,
            "provisioned_clients_count": active_clients,
            "online_connections_hint": online_connections_hint,
            "total_up_bytes": max(0, int(total_up_bytes)),
            "total_down_bytes": max(0, int(total_down_bytes)),
            "error_rate": round(error_rate, 4),
            "cpu_percent": cpu_percent,
            "metrics_complete": metrics_complete,
            "memory_used_mb": memory_used_mb,
            "memory_total_mb": memory_total_mb,
            "disk_free_gb": disk_free_gb,
            "network_total_mbps": network_total_mbps,
            "probe_stage": probe_stage,
            "probe_error_kind": probe_error_kind,
            "probe_classification": probe_classification,
            "ipv4_health": ipv4_health,
            "ipv6_health": ipv6_health,
            "panel_state": panel_state,
            "dataplane_state": dataplane_state,
            "edge_reachability_state": dataplane_state,
            "authenticated_egress_state": authenticated_egress_state,
        }
    finally:
        s.close()


def _persist_collector_failure(*, node: Node, error_window: int, source: str, detail_code: str) -> bool:
    """Persist an eligible node's bounded collector failure without inventing telemetry."""

    now = _utcnow()
    transport_health_json = _json_text(
        _build_transport_health_payload(
            panel_state="unavailable",
            panel_stage="collector",
            panel_error_kind=detail_code,
            panel_error_message=detail_code,
            dataplane_state="unavailable",
            dataplane_stage="collector",
            dataplane_error_kind=detail_code,
            dataplane_error_message=detail_code,
            authenticated_egress_state="unavailable",
            authenticated_egress_error_kind=detail_code,
            authenticated_egress_required=AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED,
            metrics_complete=False,
            probe=None,
        )
    )
    s = None
    try:
        s = SessionLocal()
        row = s.query(Node).filter(Node.id == node.id, Node.enabled == True).first()
        if row is None:
            return False
        error_rate = min(1.0, max(_rolling_error_rate(s, str(row.code or ""), error_window), 0.5))
        s.add(
            NodeHealthSample(
                node_code=row.code,
                sampled_at=now,
                panel_latency_ms=None,
                panel_error_rate=error_rate,
                active_clients=None,
                cpu_percent=None,
                memory_used_mb=None,
                memory_total_mb=None,
                disk_used_gb=None,
                disk_total_gb=None,
                disk_free_gb=None,
                network_rx_bytes_total=None,
                network_tx_bytes_total=None,
                network_rx_mbps=None,
                network_tx_mbps=None,
                network_total_mbps=None,
                total_up_bytes=None,
                total_down_bytes=None,
                total_traffic_bytes=None,
                is_healthy=False,
                score=0.0,
                source=source,
                probe_at=now,
                probe_stage="collector",
                probe_error_kind=detail_code,
                probe_error_message=detail_code,
                probe_classification="collector_unavailable",
                ipv4_health="unknown",
                ipv6_health="unknown",
                transport_health_json=transport_health_json,
            )
        )
        row.health_score = 0.0
        row.last_health_at = now
        row.is_healthy = False
        row.panel_error_rate = error_rate
        row.edge_reachability_ok = None
        row.authenticated_egress_ok = None
        row.authenticated_egress_error_kind = detail_code
        row.dataplane_ok = None
        row.dataplane_rtt_ms = None
        row.last_probe_at = now
        row.last_probe_stage = "collector"
        row.last_probe_error_kind = detail_code
        row.last_probe_error_message = detail_code
        row.last_probe_classification = "collector_unavailable"
        row.transport_health_json = transport_health_json
        policy = s.query(NodeCapacityPolicy).filter(NodeCapacityPolicy.node_code == row.code).first()
        capacity = node_capacity_status(row, policy=policy, now=now)
        row.capacity_score = float(capacity.get("score") or 0.0)
        row.capacity_state = str(capacity.get("state") or "unknown")
        row.capacity_reject_reason = str(capacity.get("reject_reason") or "") or None
        s.add(
            NodeRuntimeMetric(
                node_code=row.code,
                sampled_at=now,
                source=source,
                provisioned_clients_count=int(row.provisioned_clients_count or 0),
                online_connections_hint=int(row.online_connections_hint or 0),
                network_rx_mbps_1m=_nullable_float(row.network_rx_mbps_1m),
                network_tx_mbps_1m=_nullable_float(row.network_tx_mbps_1m),
                network_rx_mbps_5m=_nullable_float(row.network_rx_mbps_5m),
                network_tx_mbps_5m=_nullable_float(row.network_tx_mbps_5m),
                network_total_mbps=_nullable_float(row.network_total_mbps),
                cpu_percent=_nullable_float(row.cpu_percent),
                memory_used_mb=_nullable_int(row.memory_used_mb),
                memory_total_mb=_nullable_int(row.memory_total_mb),
                edge_reachability_ok=None,
                authenticated_egress_ok=None,
                dataplane_ok=None,
                dataplane_rtt_ms=None,
                capacity_score=float(capacity.get("score") or 0.0),
                capacity_state=str(capacity.get("state") or "unknown"),
                reject_reason=str(capacity.get("reject_reason") or "") or None,
                meta_json=json.dumps(
                    {
                        "panel_state": "unavailable",
                        "dataplane_state": "unavailable",
                        "edge_reachability_state": "unavailable",
                        "authenticated_egress_state": "unavailable",
                        "authenticated_egress_error_kind": detail_code,
                        "probe_stage": "collector",
                        "probe_error_kind": detail_code,
                        "metrics_state": "missing",
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            )
        )
        s.commit()
        return True
    except Exception:
        if s is not None:
            try:
                s.rollback()
            except Exception:
                pass
        return False
    finally:
        if s is not None:
            try:
                s.close()
            except Exception:
                pass


def _collector_failure_row(*, node: Node, error_window: int, source: str, detail_code: str) -> dict:
    persisted = _persist_collector_failure(
        node=node,
        error_window=error_window,
        source=source,
        detail_code=detail_code,
    )
    if not persisted:
        print(f"{str(node.code or '').strip()}: collector_failure_persistence_failed", file=sys.stderr)
    return {
        "code": str(node.code or ""),
        "healthy": False,
        "score": 0.0,
        "latency_ms": None,
        "dataplane_rtt_ms": None,
        "active_clients": None,
        "provisioned_clients_count": None,
        "online_connections_hint": None,
        "total_up_bytes": None,
        "total_down_bytes": None,
        "error_rate": 1.0,
        "cpu_percent": None,
        "memory_used_mb": None,
        "memory_total_mb": None,
        "disk_free_gb": None,
        "network_total_mbps": None,
        "probe_stage": "collector",
        "probe_error_kind": detail_code,
        "probe_classification": "collector_unavailable",
        "ipv4_health": "unknown",
        "ipv6_health": "unknown",
        "panel_state": "unavailable",
        "dataplane_state": "unavailable",
        "edge_reachability_state": "unavailable",
        "authenticated_egress_state": "unavailable",
        "metrics_complete": False,
        "collector_status": "failure_persisted" if persisted else "persistence_failed",
    }


async def run(
    *,
    error_window: int,
    source: str,
    max_concurrency: int = 4,
    per_node_timeout_seconds: float = 45.0,
    only: list[str] | None = None,
) -> int:
    # Full-pool service runs retain the legacy initialization behavior. A
    # scoped canary must validate its enabled-node allowlist before any setup
    # that could write to the database.
    if only is None:
        init_db()
    s = SessionLocal()
    try:
        enabled = s.query(Node).filter(Node.enabled == True).order_by(Node.code.asc()).all()
        if only is None:
            nodes = enabled
        else:
            requested = set(only)
            if not requested:
                print("Requested --only scope does not match enabled node inventory.", file=sys.stderr)
                return 2
            nodes = [node for node in enabled if str(node.code or "").strip().lower() in requested]
            found = {str(node.code or "").strip().lower() for node in nodes}
            if found != requested:
                print("Requested --only scope does not match enabled node inventory.", file=sys.stderr)
                return 2
    finally:
        s.close()

    if not nodes:
        print("No enabled nodes found.")
        return 0

    semaphore = asyncio.Semaphore(max(1, int(max_concurrency)))
    timeout_seconds = max(1.0, float(per_node_timeout_seconds))

    async def collect_bounded(node: Node) -> dict:
        async with semaphore:
            try:
                return await asyncio.wait_for(
                    _collect_one(node=node, error_window=error_window, source=source),
                    timeout=timeout_seconds,
                )
            except TimeoutError:
                return _collector_failure_row(
                    node=node,
                    error_window=error_window,
                    source=source,
                    detail_code="collector_timeout",
                )
            except Exception:
                return _collector_failure_row(
                    node=node,
                    error_window=error_window,
                    source=source,
                    detail_code="collector_exception",
                )

    # asyncio.gather preserves the input order, keeping stdout and handoff
    # evidence deterministic even though node collection is concurrent.
    results = await asyncio.gather(*(collect_bounded(node) for node in nodes))

    for row in results:
        print(
            f"{row['code']}: healthy={row['healthy']} score={row['score']} "
            f"latency_ms={row['latency_ms']} dataplane_rtt_ms={row['dataplane_rtt_ms']} "
            f"provisioned_clients={row['provisioned_clients_count']} "
            f"online_connections_hint={row['online_connections_hint']} "
            f"up_bytes={row['total_up_bytes']} down_bytes={row['total_down_bytes']} "
            f"error_rate={row['error_rate']} cpu={row['cpu_percent']} "
            f"ram={row['memory_used_mb']}/{row['memory_total_mb']}MB disk_free={row['disk_free_gb']}GB "
            f"collector_status={row.get('collector_status', 'ok')}"
        )
    return 1 if any(row.get("collector_status") == "persistence_failed" for row in results) else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Collect per-node runtime metrics and update health score.")
    ap.add_argument("--error-window", type=int, default=int(os.getenv("NODE_HEALTH_ERROR_WINDOW", "30")))
    ap.add_argument("--source", default="collector")
    ap.add_argument("--only", default=None, help="comma-separated exact enabled node-code allowlist")
    ap.add_argument("--max-concurrency", type=int, default=int(os.getenv("NODE_METRICS_MAX_CONCURRENCY", "4")))
    ap.add_argument(
        "--per-node-timeout-seconds",
        type=float,
        default=float(os.getenv("NODE_METRICS_PER_NODE_TIMEOUT_SECONDS", "45")),
    )
    args = ap.parse_args()
    try:
        only = _parse_only_codes(args.only) if args.only is not None else None
    except ValueError as exc:
        ap.error(str(exc))
    return asyncio.run(
        run(
            error_window=args.error_window,
            source=args.source,
            max_concurrency=args.max_concurrency,
            per_node_timeout_seconds=args.per_node_timeout_seconds,
            only=only,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())

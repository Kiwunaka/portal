from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "portal_bot"))

from db import SessionLocal, init_db  # noqa: E402
from models import Node, NodeHealthSample  # noqa: E402
from nodes_repo import NodeRuntime  # noqa: E402
from panel_client import PanelClient  # noqa: E402
from node_dataplane_probe import probe_node_endpoint  # noqa: E402


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
        last_ok_at=node.last_ok_at,
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
    load_penalty = min(max(active_clients, 0), 2000) / 20.0
    memory_percent = (float(memory_used_mb or 0) / float(memory_total_mb or 0) * 100.0) if int(memory_total_mb or 0) > 0 else 0.0
    disk_percent = (float(disk_used_gb or 0.0) / float(disk_total_gb or 0.0) * 100.0) if float(disk_total_gb or 0.0) > 0 else 0.0
    cpu_penalty = min(max(float(cpu_percent or 0.0), 0.0), 100.0) / 4.0
    memory_penalty = min(max(memory_percent, 0.0), 100.0) / 5.0
    disk_penalty = min(max(disk_percent, 0.0), 100.0) / 6.0
    score = 100.0 - latency_penalty - error_penalty - load_penalty - cpu_penalty - memory_penalty - disk_penalty
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


def _truncate_error(message: object, limit: int = 500) -> str:
    text = str(message or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


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


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _bytes_per_second_to_mbps(value: object) -> float | None:
    numeric = _nullable_float(value)
    if numeric is None or numeric < 0:
        return None
    return round((numeric * 8.0) / 1_000_000.0, 3)


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


async def _collect_one(*, node: Node, error_window: int, source: str) -> dict:
    runtime = _to_runtime(node)
    client = PanelClient(runtime)
    started = time.perf_counter()
    now = _utcnow()
    healthy = False
    latency_ms: int | None = None
    active_clients = 0
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
    probe_stage = "panel_login"
    probe_error_kind = "panel_login_failed"
    probe_error_message = "panel login returned false"
    probe_at = now
    probe: dict | None = None

    try:
        ok = await client.login()
        if ok:
            probe_stage = "panel_status"
            probe_error_kind = ""
            probe_error_message = ""
            system_metrics = await client.get_system_metrics()
            cpu_percent = system_metrics.get("cpu_percent")  # type: ignore[assignment]
            memory_used_mb = system_metrics.get("memory_used_mb")  # type: ignore[assignment]
            memory_total_mb = system_metrics.get("memory_total_mb")  # type: ignore[assignment]
            disk_used_gb = system_metrics.get("disk_used_gb")  # type: ignore[assignment]
            disk_total_gb = system_metrics.get("disk_total_gb")  # type: ignore[assignment]
            disk_free_gb = system_metrics.get("disk_free_gb")  # type: ignore[assignment]
            network_rx_bytes_total = _nullable_int(system_metrics.get("network_rx_bytes_total"))
            network_tx_bytes_total = _nullable_int(system_metrics.get("network_tx_bytes_total"))
            network_rx_bytes_per_sec = _nullable_int(system_metrics.get("network_rx_bytes_per_sec"))
            network_tx_bytes_per_sec = _nullable_int(system_metrics.get("network_tx_bytes_per_sec"))
            probe_stage = "panel_inbound_lookup"
            inbounds = await client._get_inbounds()
            for inb in inbounds:
                if int(inb.get("id") or 0) != int(runtime.inbound_id):
                    continue
                try:
                    import json as _json

                    settings = _json.loads(inb.get("settings", "{}"))
                    clients = settings.get("clients", []) or []
                    active_clients = len(clients)
                except Exception:
                    active_clients = 0
                try:
                    for stat in inb.get("clientStats", []) or []:
                        total_up_bytes += int(stat.get("up", 0) or 0)
                        total_down_bytes += int(stat.get("down", 0) or 0)
                except Exception:
                    total_up_bytes = 0
                    total_down_bytes = 0
                healthy = True
                probe_stage = "panel_inbound_lookup"
                probe_error_kind = ""
                probe_error_message = ""
                break
            if not healthy:
                probe_error_kind = "inbound_not_found"
                probe_error_message = f"inbound {runtime.inbound_id} not found on panel"
        latency_ms = int((time.perf_counter() - started) * 1000)
    except Exception as exc:
        healthy = False
        latency_ms = int((time.perf_counter() - started) * 1000)
        probe_error_kind = "panel_probe_failed"
        probe_error_message = _truncate_error(exc)
    finally:
        await client.close()

    if healthy:
        probe = probe_node_endpoint(
            host=str(runtime.host or "").strip(),
            port=int(runtime.vless_port or 443),
            sni=str(runtime.reality_sni or runtime.host or "").strip() or None,
        )
        probe_at = probe.get("probed_at") or now
        probe_stage = str(probe.get("stage") or probe_stage or "")
        probe_error_kind = str(probe.get("error_kind") or "")
        probe_error_message = _truncate_error(probe.get("error_message") or "")
        healthy = bool(probe.get("ok"))
    else:
        probe_at = now

    hoster_family = _string_or_none((probe or {}).get("hoster_family"))
    hoster_asn = _string_or_none((probe or {}).get("hoster_asn"))
    hoster_subnet = _string_or_none((probe or {}).get("hoster_subnet"))
    probe_classification = _string_or_none((probe or {}).get("probe_classification"))
    ipv4_health = _string_or_none((probe or {}).get("ipv4_health"))
    ipv6_health = _string_or_none((probe or {}).get("ipv6_health"))
    transport_health_json = _json_text((probe or {}).get("transport_health_json"))
    if transport_health_json is None:
        transport_health_json = _json_text((probe or {}).get("transport_health"))

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
        error_rate = _rolling_error_rate(s, runtime.code, error_window)
        if not healthy:
            error_rate = min(1.0, max(error_rate, 0.5))
        score = _calc_score(
            latency_ms=latency_ms,
            error_rate=error_rate,
            active_clients=active_clients,
            healthy=healthy,
            cpu_percent=float(cpu_percent or 0.0),
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
            cpu_percent=float(cpu_percent or 0.0),
            total_up_bytes=max(0, int(total_up_bytes)),
            total_down_bytes=max(0, int(total_down_bytes)),
            total_traffic_bytes=max(0, int(total_up_bytes) + int(total_down_bytes)),
            is_healthy=healthy,
            score=score,
            source=source,
            probe_at=probe_at,
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
            row.cpu_percent = float(cpu_percent or 0.0)
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
            row.last_probe_at = probe_at
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
            if healthy:
                row.last_ok_at = now
        s.commit()
        return {
            "code": runtime.code,
            "healthy": healthy,
            "score": score,
            "latency_ms": latency_ms,
            "active_clients": active_clients,
            "total_up_bytes": max(0, int(total_up_bytes)),
            "total_down_bytes": max(0, int(total_down_bytes)),
            "error_rate": round(error_rate, 4),
            "cpu_percent": cpu_percent,
            "memory_used_mb": memory_used_mb,
            "memory_total_mb": memory_total_mb,
            "disk_free_gb": disk_free_gb,
            "network_total_mbps": network_total_mbps,
            "probe_stage": probe_stage,
            "probe_error_kind": probe_error_kind,
            "probe_classification": probe_classification,
            "ipv4_health": ipv4_health,
            "ipv6_health": ipv6_health,
        }
    finally:
        s.close()


async def run(*, error_window: int, source: str) -> int:
    init_db()
    s = SessionLocal()
    try:
        nodes = s.query(Node).filter(Node.enabled == True).order_by(Node.code.asc()).all()
    finally:
        s.close()

    if not nodes:
        print("No enabled nodes found.")
        return 0

    results = []
    for node in nodes:
        results.append(await _collect_one(node=node, error_window=error_window, source=source))

    for row in results:
        print(
            f"{row['code']}: healthy={row['healthy']} score={row['score']} "
            f"latency_ms={row['latency_ms']} active_clients={row['active_clients']} "
            f"up_bytes={row['total_up_bytes']} down_bytes={row['total_down_bytes']} "
            f"error_rate={row['error_rate']} cpu={row['cpu_percent']} "
            f"ram={row['memory_used_mb']}/{row['memory_total_mb']}MB disk_free={row['disk_free_gb']}GB"
        )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Collect per-node runtime metrics and update health score.")
    ap.add_argument("--error-window", type=int, default=int(os.getenv("NODE_HEALTH_ERROR_WINDOW", "30")))
    ap.add_argument("--source", default="collector")
    args = ap.parse_args()
    return asyncio.run(run(error_window=args.error_window, source=args.source))


if __name__ == "__main__":
    raise SystemExit(main())

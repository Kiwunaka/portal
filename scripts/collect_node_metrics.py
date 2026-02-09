from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "portal_bot"))

from db import SessionLocal, init_db  # noqa: E402
from models import Node, NodeHealthSample  # noqa: E402
from nodes_repo import NodeRuntime  # noqa: E402
from panel_client import PanelClient  # noqa: E402


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
        weight=int(node.weight or 0),
        health_score=float(node.health_score or 0.0),
        last_health_at=node.last_health_at,
        is_healthy=bool(node.is_healthy),
        panel_latency_ms=node.panel_latency_ms,
        panel_error_rate=float(node.panel_error_rate or 0.0),
        active_clients=int(node.active_clients or 0),
        last_ok_at=node.last_ok_at,
    )


def _calc_score(*, latency_ms: int | None, error_rate: float, active_clients: int, healthy: bool) -> float:
    if not healthy:
        return 0.0
    latency_penalty = min(max(latency_ms or 0, 0), 3000) / 30.0
    error_penalty = max(0.0, min(error_rate, 1.0)) * 40.0
    load_penalty = min(max(active_clients, 0), 2000) / 20.0
    score = 100.0 - latency_penalty - error_penalty - load_penalty
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


async def _collect_one(*, node: Node, error_window: int, source: str) -> dict:
    runtime = _to_runtime(node)
    client = PanelClient(runtime)
    started = time.perf_counter()
    now = datetime.utcnow()
    healthy = False
    latency_ms: int | None = None
    active_clients = 0

    try:
        ok = await client.login()
        if ok:
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
                healthy = True
                break
        latency_ms = int((time.perf_counter() - started) * 1000)
    except Exception:
        healthy = False
        latency_ms = int((time.perf_counter() - started) * 1000)
    finally:
        await client.close()

    s = SessionLocal()
    try:
        error_rate = _rolling_error_rate(s, runtime.code, error_window)
        if not healthy:
            error_rate = min(1.0, max(error_rate, 0.5))
        score = _calc_score(
            latency_ms=latency_ms,
            error_rate=error_rate,
            active_clients=active_clients,
            healthy=healthy,
        )
        sample = NodeHealthSample(
            node_code=runtime.code,
            sampled_at=now,
            panel_latency_ms=latency_ms,
            panel_error_rate=error_rate,
            active_clients=active_clients,
            is_healthy=healthy,
            score=score,
            source=source,
        )
        s.add(sample)

        row = s.query(Node).filter(Node.id == node.id).first()
        if row:
            row.health_score = score
            row.last_health_at = now
            row.is_healthy = healthy
            row.panel_latency_ms = latency_ms
            row.panel_error_rate = error_rate
            row.active_clients = active_clients
            if healthy:
                row.last_ok_at = now
        s.commit()
        return {
            "code": runtime.code,
            "healthy": healthy,
            "score": score,
            "latency_ms": latency_ms,
            "active_clients": active_clients,
            "error_rate": round(error_rate, 4),
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
            f"error_rate={row['error_rate']}"
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

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from config import Settings
from models import Node


@dataclass(frozen=True)
class NodeRuntime:
    id: int | None
    code: str
    name: str
    host: str
    vless_port: int
    reality_sni: str
    reality_pbk: str
    reality_sid: str
    fingerprint: str
    flow: str

    panel_base_url: str
    panel_path: str
    panel_user: str
    panel_pass: str
    inbound_id: int
    accepting_new_clients: bool
    is_draining: bool
    weight: int
    health_score: float
    last_health_at: datetime | None
    is_healthy: bool
    panel_latency_ms: int | None
    panel_error_rate: float
    active_clients: int
    last_ok_at: datetime | None


def _score_value(n: Node) -> float:
    try:
        return float(n.health_score or 0.0)
    except Exception:
        return 0.0


def _sort_nodes(rows: list[Node]) -> list[Node]:
    # First by health score, then by static weight.
    return sorted(
        rows,
        key=lambda n: (
            -_score_value(n),
            -int(n.weight or 0),
            (n.code or ""),
        ),
    )


def legacy_node() -> NodeRuntime:
    return NodeRuntime(
        id=None,
        code=Settings.LEGACY_NODE_CODE,
        name=Settings.LEGACY_NODE_NAME,
        host=Settings.HOST_DOMAIN,
        vless_port=Settings.VLESS_PORT,
        reality_sni=Settings.VLESS_SNI,
        reality_pbk=Settings.VLESS_PBK,
        reality_sid=Settings.VLESS_SID,
        fingerprint=Settings.VLESS_FP,
        flow=Settings.VLESS_FLOW,
        panel_base_url=Settings.PANEL_BASE_URL,
        panel_path=Settings.PANEL_PATH,
        panel_user=Settings.PANEL_USER,
        panel_pass=Settings.PANEL_PASS,
        inbound_id=Settings.INBOUND_ID,
        accepting_new_clients=True,
        is_draining=False,
        weight=100,
        health_score=0.0,
        last_health_at=None,
        is_healthy=True,
        panel_latency_ms=None,
        panel_error_rate=0.0,
        active_clients=0,
        last_ok_at=None,
    )


def enabled_nodes(session) -> list[NodeRuntime]:
    rows: list[Node] = session.query(Node).filter_by(enabled=True).all()
    if not rows:
        return [legacy_node()]
    healthy_rows = [n for n in rows if bool(getattr(n, "is_healthy", True))]
    chosen_rows = _sort_nodes(healthy_rows) if healthy_rows else _sort_nodes(rows)
    out: list[NodeRuntime] = []
    for n in chosen_rows:
        out.append(
            NodeRuntime(
                id=n.id,
                code=n.code,
                name=n.name,
                host=n.host,
                vless_port=n.vless_port,
                reality_sni=n.reality_sni,
                reality_pbk=n.reality_pbk,
                reality_sid=n.reality_sid,
                fingerprint=n.fingerprint,
                flow=n.flow,
                panel_base_url=n.panel_base_url,
                panel_path=n.panel_path,
                panel_user=n.panel_user,
                panel_pass=n.panel_pass,
                inbound_id=n.inbound_id,
                accepting_new_clients=bool(getattr(n, "accepting_new_clients", True)),
                is_draining=bool(getattr(n, "is_draining", False)),
                weight=int(getattr(n, "weight", 0) or 0),
                health_score=float(getattr(n, "health_score", 0.0) or 0.0),
                last_health_at=getattr(n, "last_health_at", None),
                is_healthy=bool(getattr(n, "is_healthy", True)),
                panel_latency_ms=getattr(n, "panel_latency_ms", None),
                panel_error_rate=float(getattr(n, "panel_error_rate", 0.0) or 0.0),
                active_clients=int(getattr(n, "active_clients", 0) or 0),
                last_ok_at=getattr(n, "last_ok_at", None),
            )
        )
    return out

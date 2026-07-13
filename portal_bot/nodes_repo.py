from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from config import Settings
from models import Node
from node_policy import (
    canonical_free_node_code,
    node_hard_reject_reason,
    node_is_free,
    paid_pool_nodes,
    rank_nodes_for_subscription,
    user_free_access_role,
    user_uses_free_pool,
)


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
    provisioned_clients_count: int = 0
    online_connections_hint: int = 0
    cpu_percent: float = 0.0
    network_rx_mbps: float | None = None
    network_tx_mbps: float | None = None
    network_total_mbps: float | None = None
    network_rx_mbps_1m: float | None = None
    network_tx_mbps_1m: float | None = None
    network_rx_mbps_5m: float | None = None
    network_tx_mbps_5m: float | None = None
    tcp_retrans_percent: float | None = None
    packet_loss_percent: float | None = None
    dataplane_ok: bool | None = None
    dataplane_rtt_ms: int | None = None
    capacity_score: float | None = None
    capacity_state: str | None = None
    capacity_reject_reason: str | None = None
    last_ok_at: datetime | None = None
    last_probe_at: datetime | None = None
    transport_profiles_json: str | None = None
    access_role: str | None = None


def _score_value(n: Node) -> float:
    try:
        return float(n.health_score or 0.0)
    except Exception:
        return 0.0


def _sort_nodes(rows: list[Node]) -> list[Node]:
    # Keep enabled nodes visible, but order degraded ones after healthy nodes.
    return sorted(
        rows,
        key=lambda n: (
            not bool(getattr(n, "is_healthy", True)),
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
        provisioned_clients_count=0,
        online_connections_hint=0,
        cpu_percent=0.0,
        network_rx_mbps=None,
        network_tx_mbps=None,
        network_total_mbps=None,
        network_rx_mbps_1m=None,
        network_tx_mbps_1m=None,
        network_rx_mbps_5m=None,
        network_tx_mbps_5m=None,
        tcp_retrans_percent=None,
        packet_loss_percent=None,
        dataplane_ok=None,
        dataplane_rtt_ms=None,
        capacity_score=None,
        capacity_state="unknown",
        capacity_reject_reason=None,
        last_ok_at=None,
        last_probe_at=None,
        transport_profiles_json=None,
        access_role="paid",
    )


def enabled_nodes(session) -> list[NodeRuntime]:
    rows: list[Node] = session.query(Node).filter_by(enabled=True).all()
    if not rows:
        return [legacy_node()]
    chosen_rows = _sort_nodes(rows)
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
                provisioned_clients_count=int(
                    getattr(n, "provisioned_clients_count", getattr(n, "active_clients", 0)) or 0
                ),
                online_connections_hint=int(getattr(n, "online_connections_hint", 0) or 0),
                cpu_percent=float(getattr(n, "cpu_percent", 0.0) or 0.0),
                network_rx_mbps=getattr(n, "network_rx_mbps", None),
                network_tx_mbps=getattr(n, "network_tx_mbps", None),
                network_total_mbps=getattr(n, "network_total_mbps", None),
                network_rx_mbps_1m=getattr(n, "network_rx_mbps_1m", None),
                network_tx_mbps_1m=getattr(n, "network_tx_mbps_1m", None),
                network_rx_mbps_5m=getattr(n, "network_rx_mbps_5m", None),
                network_tx_mbps_5m=getattr(n, "network_tx_mbps_5m", None),
                tcp_retrans_percent=getattr(n, "tcp_retrans_percent", None),
                packet_loss_percent=getattr(n, "packet_loss_percent", None),
                dataplane_ok=getattr(n, "dataplane_ok", None),
                dataplane_rtt_ms=getattr(n, "dataplane_rtt_ms", None),
                capacity_score=getattr(n, "capacity_score", None),
                capacity_state=getattr(n, "capacity_state", None),
                capacity_reject_reason=getattr(n, "capacity_reject_reason", None),
                last_ok_at=getattr(n, "last_ok_at", None),
                last_probe_at=getattr(n, "last_probe_at", None),
                transport_profiles_json=getattr(n, "transport_profiles_json", None),
                access_role=getattr(n, "access_role", None),
            )
        )
    return out


def eligible_nodes(session, user, key=None, purpose: str = "subscription") -> list[NodeRuntime]:
    nodes = enabled_nodes(session)
    if not nodes:
        return nodes

    if user_uses_free_pool(user):
        free_code = str(
            canonical_free_node_code(nodes, access_role=user_free_access_role(user)) or ""
        ).strip().lower()
        pool = [node for node in nodes if str(node.code or "").strip().lower() == free_code]
    else:
        pool = paid_pool_nodes(nodes)
        if key is not None:
            pool_code = str(getattr(key, "pool_code", "") or "").strip().lower()
            if pool_code == "free_pool":
                free_code = str(
                    canonical_free_node_code(nodes, access_role=user_free_access_role(user)) or ""
                ).strip().lower()
                pool = [node for node in nodes if str(node.code or "").strip().lower() == free_code]
            elif pool_code == "premium_pool":
                pool = paid_pool_nodes(nodes)

    if str(purpose or "").strip().lower() in {"subscription", "profile", "smart_connect"}:
        ranked = rank_nodes_for_subscription(pool)
        if ranked:
            return ranked
    return [
        node
        for node in rank_nodes_for_subscription(pool)
        if not node_hard_reject_reason(node)
    ] or list(pool)

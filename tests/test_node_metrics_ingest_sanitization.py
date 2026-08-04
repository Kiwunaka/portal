from __future__ import annotations

import hashlib
import hmac
import json
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient


TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from test_smart_connect_api import _load_api


def test_signed_node_metrics_meta_persists_only_bounded_safe_schema(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    from models import Node, NodeRuntimeMetric

    session = api.SessionLocal()
    try:
        session.add(
            Node(
                code="pl",
                name="Poland",
                host="pl.example.test",
                vless_port=443,
                reality_sni="www.example.test",
                reality_pbk="pbk",
                reality_sid="sid",
                panel_base_url="https://pl.example.test:8444",
                panel_path="xui",
                panel_user="u",
                panel_pass="p",
                inbound_id=1,
                enabled=True,
                observer_push_secret="test-node-metrics-secret",
            )
        )
        session.commit()
    finally:
        session.close()

    payload = {
        "source": "node_agent",
        "dataplane_ok": True,
        "dataplane_rtt_ms": 45,
        "meta": {
            "panel_state": "healthy",
            "probe_stage": "tls_sni",
            "probe_error_kind": "tls_handshake_failed",
            "dataplane_rtt_ms": 45,
            "transport_health": {
                "dns_resolution": "healthy",
                "tcp_connect": "healthy",
                "tls_handshake": "degraded",
                "reality_target": "healthy",
                "endpoint": "forbidden-agent-endpoint.invalid",
                "tls_server_name": "forbidden-agent-sni.invalid",
            },
            "peer_ip": "198.51.100.231",
            "certificate": "forbidden-agent-certificate",
            "exception": "forbidden-agent-exception",
            "token": "forbidden-agent-token",
            "subnet": "198.51.100.0/24",
            "nested": {"endpoint": "forbidden-nested.invalid"},
            "items": ["forbidden-list-item"],
        },
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    timestamp = str(int(time.time()))
    signature = hmac.new(
        b"test-node-metrics-secret",
        timestamp.encode("utf-8") + b"." + body,
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/api/internal/nodes/pl/metrics",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-POKROV-Timestamp": timestamp,
            "X-POKROV-Signature": signature,
        },
    )

    assert response.status_code == 200, response.text
    session = api.SessionLocal()
    try:
        metric = session.query(NodeRuntimeMetric).one()
        persisted = json.loads(metric.meta_json)
    finally:
        session.close()

    assert persisted == {
        "panel_state": "healthy",
        "probe_stage": "tls_sni",
        "probe_error_kind": "tls_handshake_failed",
        "dataplane_rtt_ms": 45,
        "transport_health": {
            "dns_resolution": "healthy",
            "tcp_connect": "healthy",
            "tls_handshake": "degraded",
            "reality_target": "healthy",
        },
    }

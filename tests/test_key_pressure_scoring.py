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


def test_key_pressure_scoring_does_not_escalate_ip_churn_without_traffic(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)

    state, score, reasons, manual_review = api._key_pressure_state(
        traffic_gb_24h=0.2,
        peak_tx_mbps=0.5,
        distinct_source_ips_24h=50,
        distinct_asns_24h=8,
        distinct_countries_24h=5,
        node_count_24h=5,
    )

    assert state == "warm"
    assert score == 35.0
    assert "churn_without_traffic_pressure_capped" in reasons
    assert manual_review is False


def test_key_pressure_scoring_flags_heavy_use_without_fair_use_enforcement(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)

    state, score, reasons, manual_review = api._key_pressure_state(
        traffic_gb_24h=350.0,
        peak_tx_mbps=140.0,
        distinct_source_ips_24h=25,
        distinct_asns_24h=6,
        distinct_countries_24h=4,
        node_count_24h=4,
    )

    assert state == "suspected_shared"
    assert score >= 100.0
    assert "traffic_gb_24h>=300" in reasons
    assert manual_review is True


def test_internal_xray_stats_records_rollup_sources_and_pressure(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("NODE_AGENT_METRICS_SECRET", raising=False)
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    from models import AccessKey, KeyPressureState, KeySourceObservation, KeyUsageRollup, Node

    session = api.SessionLocal()
    try:
        node = Node(
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
            observer_push_secret="pl-secret",
        )
        session.add(node)
        session.flush()
        key = AccessKey(
            tg_id=4242,
            key_uuid="11111111-1111-4111-8111-111111111111",
            panel_email="user-4242",
            node_code="pl",
            pool_code="premium_pool",
            state="active",
            source="test",
        )
        session.add(key)
        session.commit()
        key_id = int(key.id)
    finally:
        session.close()

    payload = {
        "source": "xray_stats",
        "window_seconds": 300,
        "keys": [
            {
                "panel_email": "user-4242",
                "key_uuid": "11111111-1111-4111-8111-111111111111",
                "upload_bytes": 1234,
                "download_bytes": 9876,
                "peak_tx_mbps": 140,
                "observations": 3,
                "source_ip_hashes": ["203.0.113.10", "198.51.100.22"],
                "source_asns": ["AS64500", "AS64501"],
                "source_countries": ["DE", "US"],
                "distinct_source_ips_1h": 2,
                "distinct_source_ips_24h": 25,
                "distinct_asns_24h": 6,
                "distinct_countries_24h": 4,
                "node_count_24h": 4,
                "traffic_gb_24h": 350,
            }
        ],
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    timestamp = str(int(time.time()))
    signature = hmac.new(
        b"pl-secret",
        timestamp.encode("utf-8") + b"." + body,
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/api/internal/nodes/pl/xray-stats",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-POKROV-Timestamp": timestamp,
            "X-POKROV-Signature": signature,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"ok": True, "node_code": "pl", "accepted": 1}

    session = api.SessionLocal()
    try:
        rollup = session.query(KeyUsageRollup).filter(KeyUsageRollup.key_id == key_id).one()
        assert rollup.node_code == "pl"
        assert rollup.tg_id == 4242
        assert rollup.panel_email == "user-4242"
        assert rollup.total_bytes == 11110
        assert rollup.peak_tx_mbps == 140
        assert rollup.observations == 3
        assert rollup.source == "xray_stats"

        observations = session.query(KeySourceObservation).filter(KeySourceObservation.key_id == key_id).all()
        assert len(observations) == 2
        assert {row.node_code for row in observations} == {"pl"}
        assert {row.panel_email for row in observations} == {"user-4242"}
        assert all(len(row.source_ip_hash) == 64 for row in observations)

        pressure = session.get(KeyPressureState, key_id)
        assert pressure is not None
        assert pressure.state == "suspected_shared"
        assert pressure.pressure_score >= 100.0
        assert pressure.distinct_source_ips_24h == 25
        assert pressure.node_count_24h == 4
        assert pressure.traffic_gb_24h == 350.0
        assert pressure.manual_review_required is True
        assert "traffic_gb_24h>=300" in json.loads(pressure.reasons_json)
    finally:
        session.close()

from __future__ import annotations

import sys
from pathlib import Path

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

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from migrations import run_migrations  # noqa: E402
from models import (  # noqa: E402
    Base,
    Node,
    NodeHealthSample,
    NodeRuntimeMetric,
    OpsAlert,
    ProviderTrafficQuota,
)
from operator_network_service import (  # noqa: E402
    build_network_fleet,
    build_provider_read_model,
    list_network_alerts,
    node_360,
)


@pytest.fixture()
def database(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'operator-network.db').as_posix()}")
    Base.metadata.create_all(engine)
    run_migrations(engine)
    factory = sessionmaker(bind=engine)
    try:
        yield factory
    finally:
        engine.dispose()


def _seed(factory) -> datetime:
    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    session = factory()
    try:
        session.add(
            Node(
                code="nl-main",
                name="NL Main",
                host="secret.node.example",
                panel_base_url="https://secret-panel.example",
                panel_user="secret-user",
                panel_pass="secret-pass",
                enabled=True,
                accepting_new_clients=True,
                is_draining=False,
                is_healthy=True,
                health_score=0.95,
                hoster_family="hetzner",
                hoster_asn="AS24940",
                hoster_subnet="198.51.100.0/24",
                last_health_at=now,
                transport_profiles_json=json.dumps(
                    [{"name": "legacy_reality_fallback", "enabled": True}]
                ),
            )
        )
        session.flush()
        session.add_all(
            [
                NodeHealthSample(
                    node_code="nl-main",
                    sampled_at=now,
                    is_healthy=True,
                    cpu_percent=21.5,
                    network_total_mbps=100.0,
                    transport_health_json=json.dumps({"panel_state": "healthy"}),
                ),
                NodeRuntimeMetric(
                    node_code="nl-main",
                    sampled_at=now,
                    source="node_agent",
                    provisioned_clients_count=12,
                    online_connections_hint=7,
                    capacity_state="healthy",
                ),
                OpsAlert(
                    fingerprint="test-network-alert",
                    source="node_metrics",
                    severity="warning",
                    status="active",
                    title="Synthetic network alert",
                    environment="test",
                    first_seen_at=now,
                    last_seen_at=now,
                ),
                OpsAlert(
                    fingerprint="production-network-alert",
                    source="node_metrics",
                    severity="warning",
                    status="active",
                    title="Must remain isolated",
                    environment="production",
                    first_seen_at=now,
                    last_seen_at=now,
                ),
                ProviderTrafficQuota(
                    node_code="nl-main",
                    included_bytes=100 * 1024**3,
                    reset_day=1,
                    timezone="UTC",
                    warning_ratio=0.8,
                    critical_ratio=0.95,
                    enabled=True,
                    notes="secret provider contract note",
                ),
            ]
        )
        session.commit()
        return now
    finally:
        session.close()


def test_network_fleet_and_node_360_keep_authority_age_and_hide_connection_material(database) -> None:
    now = _seed(database)
    session = database()
    try:
        fleet = build_network_fleet(
            session, now=now + timedelta(seconds=5), metrics_stale_after_seconds=900
        )
        assert fleet["authority"]["inventory"] == "nodes"
        assert fleet["items"][0]["code"] == "nl-main"
        assert fleet["items"][0]["freshness_status"] == "ok"
        assert fleet["items"][0]["freshness_age_seconds"] == 5
        assert fleet["items"][0]["country_code"] == "NL"

        detail = node_360(
            session,
            node_code="nl-main",
            now=now + timedelta(seconds=5),
            metrics_stale_after_seconds=900,
            include_ru_history=False,
        )
        assert detail is not None
        assert detail["sources"]["runtime"]["details"]["provisioned_clients_count"] == 12
        serialized = json.dumps({"fleet": fleet, "detail": detail})
        for forbidden in (
            "secret.node.example",
            "secret-panel.example",
            "secret-user",
            "secret-pass",
            "198.51.100.0/24",
        ):
            assert forbidden not in serialized
    finally:
        session.close()


def test_network_alerts_are_environment_scoped_and_provider_notes_are_hashed(database) -> None:
    now = _seed(database)
    session = database()
    try:
        alerts = list_network_alerts(
            session, environment="test", status="active", now=now, limit=20
        )
        assert [row["fingerprint"] for row in alerts["items"]] == ["test-network-alert"]

        providers = build_provider_read_model(session, now=now)
        assert providers["configs"][0]["notes_present"] is True
        assert providers["configs"][0]["notes_length"] == len("secret provider contract note")
        assert len(providers["configs"][0]["notes_sha256"]) == 64
        serialized = json.dumps(providers)
        assert "secret provider contract note" not in serialized
    finally:
        session.close()


def test_invalid_ru_configuration_degrades_sources_without_crashing_fleet(database) -> None:
    now = _seed(database)
    session = database()
    try:
        session.add(
            Node(
                code="de-invalid",
                name="Invalid RU target",
                host="not a valid host",
                enabled=True,
                accepting_new_clients=False,
                transport_profiles_json=json.dumps(
                    [{"name": "legacy_reality_fallback", "enabled": True}]
                ),
            )
        )
        session.commit()

        fleet = build_network_fleet(
            session, now=now + timedelta(seconds=5), metrics_stale_after_seconds=900
        )
        assert fleet["count"] == 2
        assert {
            row["sources"]["ru_origin"]["reason_code"] for row in fleet["items"]
        } == {"ru_configuration_invalid"}
        assert all(
            row["sources"]["ru_origin"]["configuration_error_code"]
            for row in fleet["items"]
        )
    finally:
        session.close()

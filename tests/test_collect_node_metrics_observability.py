import asyncio
import importlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
import uuid
from datetime import datetime
from pathlib import Path
from unittest import mock


class _FakePanelClientOk:
    def __init__(self, runtime) -> None:
        self.runtime = runtime

    async def login(self) -> bool:
        return True

    async def get_system_metrics(self) -> dict:
        return {
            "cpu_percent": 11.0,
            "memory_used_mb": 256,
            "memory_total_mb": 1024,
            "disk_used_gb": 10.0,
            "disk_total_gb": 40.0,
            "disk_free_gb": 30.0,
            "network_rx_bytes_total": 1_500_000_000,
            "network_tx_bytes_total": 900_000_000,
            "network_rx_bytes_per_sec": 125_000,
            "network_tx_bytes_per_sec": 250_000,
        }

    async def _get_inbounds(self) -> list[dict]:
        return [
            {
                "id": self.runtime.inbound_id,
                "settings": '{"clients":[{"id":"u1"},{"id":"u2"}]}',
                "clientStats": [{"up": 100, "down": 200}],
            }
        ]

    async def close(self) -> None:
        return None


class _FakePanelClientLoginFail:
    def __init__(self, runtime) -> None:
        self.runtime = runtime

    async def login(self) -> bool:
        return False

    async def close(self) -> None:
        return None


class _FakePanelClientMissingInbound:
    def __init__(self, runtime) -> None:
        self.runtime = runtime

    async def login(self) -> bool:
        return True

    async def get_system_metrics(self) -> dict:
        return {
            "cpu_percent": 9.0,
            "memory_used_mb": 128,
            "memory_total_mb": 1024,
            "disk_used_gb": 8.0,
            "disk_total_gb": 40.0,
            "disk_free_gb": 32.0,
            "network_rx_bytes_total": 100_000_000,
            "network_tx_bytes_total": 120_000_000,
            "network_rx_bytes_per_sec": 64_000,
            "network_tx_bytes_per_sec": 32_000,
        }

    async def _get_inbounds(self) -> list[dict]:
        return [
            {
                "id": self.runtime.inbound_id + 1,
                "settings": '{"clients":[{"id":"u1"}]}',
                "clientStats": [{"up": 50, "down": 75}],
            }
        ]

    async def close(self) -> None:
        return None


class _FakePanelClientNoSystemMetrics:
    def __init__(self, runtime) -> None:
        self.runtime = runtime

    async def login(self) -> bool:
        return True

    async def get_system_metrics(self) -> dict:
        return {
            "cpu_percent": 11.0,
            "memory_used_mb": None,
            "memory_total_mb": None,
            "disk_used_gb": None,
            "disk_total_gb": None,
            "disk_free_gb": None,
            "network_rx_bytes_total": None,
            "network_tx_bytes_total": None,
            "network_rx_bytes_per_sec": None,
            "network_tx_bytes_per_sec": None,
        }

    async def _get_inbounds(self) -> list[dict]:
        return [
            {
                "id": self.runtime.inbound_id,
                "settings": '{"clients":[{"id":"u1"},{"id":"u2"}]}',
                "clientStats": [{"up": 100, "down": 200}],
            }
        ]

    async def close(self) -> None:
        return None


class CollectNodeMetricsObservabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.portal_dir = str(self.repo_root / "portal_bot")
        self.scripts_dir = str(self.repo_root / "scripts")
        if self.portal_dir not in sys.path:
            sys.path.insert(0, self.portal_dir)
        if self.scripts_dir not in sys.path:
            sys.path.insert(0, self.scripts_dir)

        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str((Path(self._tmp.name) / f"portal_api_test_{uuid.uuid4().hex}.db").resolve())
        self._saved_env = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(self.db_path).as_posix()}"

        for module_name in ("db", "models", "migrations", "config"):
            sys.modules.pop(module_name, None)

        self.db = importlib.import_module("db")
        self.models = importlib.import_module("models")
        self.db.init_db()

        spec = importlib.util.spec_from_file_location(
            "collect_node_metrics",
            self.repo_root / "scripts" / "collect_node_metrics.py",
        )
        self.collector = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        sys.modules[spec.name] = self.collector
        spec.loader.exec_module(self.collector)

        session = self.db.SessionLocal()
        try:
            node = self.models.Node(
                code="pl",
                name="Poland",
                host="pl.pokrov.space",
                vless_port=443,
                reality_sni="www.example.com",
                reality_pbk="pbk",
                reality_sid="sid",
                panel_base_url="https://pl.pokrov.space:8444",
                panel_path="/panel/",
                panel_user="admin",
                panel_pass="secret",
                inbound_id=7,
                enabled=True,
            )
            session.add(node)
            session.commit()
            self.node_id = int(node.id)
        finally:
            session.close()

    def tearDown(self) -> None:
        try:
            self.db.engine.dispose()
        except Exception:
            pass
        if self._saved_env is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self._saved_env
        Path(self.db_path).unlink(missing_ok=True)

    def _load_node(self):
        session = self.db.SessionLocal()
        try:
            node = session.query(self.models.Node).filter(self.models.Node.id == self.node_id).first()
            sample = session.query(self.models.NodeHealthSample).order_by(self.models.NodeHealthSample.id.desc()).first()
            return node, sample
        finally:
            session.close()

    def _decode_transport_health(self, text: str | None) -> dict:
        self.assertIsNotNone(text)
        return json.loads(text or "{}")

    def test_collect_one_persists_external_probe_failure_details(self) -> None:
        session = self.db.SessionLocal()
        try:
            node = session.query(self.models.Node).filter(self.models.Node.id == self.node_id).first()
        finally:
            session.close()

        with mock.patch.object(self.collector, "PanelClient", _FakePanelClientOk), mock.patch.object(
            self.collector,
            "probe_node_endpoint",
            return_value={
                "ok": False,
                "stage": "tls_sni",
                "error_kind": "tls_handshake_failed",
                "error_message": "tls handshake failed",
                "hoster_family": "hetzner",
                "hoster_asn": "AS24940",
                "hoster_subnet": "1.2.3.0/24",
                "probe_classification": "provider_specific_path",
                "ipv4_health": "degraded",
                "ipv6_health": "healthy",
                "transport_health": {
                    "legacy_reality_fallback": "degraded",
                    "grpc_443_primary": "healthy",
                },
                "probed_at": datetime.utcnow(),
                "resolved_ips": ["1.2.3.4"],
            },
        ):
            result = asyncio.run(self.collector._collect_one(node=node, error_window=5, source="tests"))

        self.assertFalse(result["healthy"])
        node_row, sample = self._load_node()
        self.assertIsNotNone(node_row)
        self.assertEqual(node_row.last_probe_stage, "tls_sni")
        self.assertEqual(node_row.last_probe_error_kind, "tls_handshake_failed")
        self.assertEqual(node_row.last_probe_error_message, "tls handshake failed")
        self.assertEqual(node_row.hoster_family, "hetzner")
        self.assertEqual(node_row.hoster_asn, "AS24940")
        self.assertEqual(node_row.hoster_subnet, "1.2.3.0/24")
        self.assertEqual(node_row.last_probe_classification, "provider_specific_path")
        self.assertEqual(node_row.ipv4_health, "degraded")
        self.assertEqual(node_row.ipv6_health, "healthy")
        self.assertIn("grpc_443_primary", str(node_row.transport_health_json))
        self.assertIsNotNone(node_row.last_probe_at)
        self.assertIsNotNone(sample)
        self.assertEqual(sample.probe_stage, "tls_sni")
        self.assertEqual(sample.probe_error_kind, "tls_handshake_failed")
        self.assertEqual(sample.probe_classification, "provider_specific_path")
        self.assertEqual(sample.ipv4_health, "degraded")
        self.assertEqual(sample.ipv6_health, "healthy")
        self.assertIn("grpc_443_primary", str(sample.transport_health_json))

    def test_collect_one_persists_panel_and_dataplane_states_when_panel_login_fails(self) -> None:
        session = self.db.SessionLocal()
        try:
            node = session.query(self.models.Node).filter(self.models.Node.id == self.node_id).first()
        finally:
            session.close()

        with mock.patch.object(self.collector, "PanelClient", _FakePanelClientLoginFail), mock.patch.object(
            self.collector,
            "probe_node_endpoint",
            return_value={
                "ok": True,
                "stage": "reality_target",
                "error_kind": "",
                "error_message": "",
                "probe_classification": "healthy",
                "ipv4_health": "healthy",
                "ipv6_health": "unavailable",
                "hoster_family": "hetzner",
                "hoster_asn": "AS24940",
                "hoster_subnet": "1.2.3.0/24",
                "transport_health": {
                    "dns_resolution": "healthy",
                    "tcp_connect": "healthy",
                    "tls_handshake": "healthy",
                    "reality_target": "healthy",
                },
                "root_cause_summary": "DNS, TCP, TLS, and reality-target checks passed.",
                "root_cause_detail": "connected to 1.2.3.4 over ipv4",
                "connected_ip": "1.2.3.4",
                "probed_at": datetime.utcnow(),
            },
        ) as probe_mock:
            result = asyncio.run(self.collector._collect_one(node=node, error_window=5, source="tests"))

        probe_mock.assert_called_once()
        self.assertFalse(result["healthy"])
        self.assertEqual(result["panel_state"], "failed")
        self.assertEqual(result["dataplane_state"], "healthy")
        node_row, sample = self._load_node()
        self.assertEqual(node_row.last_probe_stage, "panel_login")
        self.assertEqual(node_row.last_probe_error_kind, "panel_login_failed")
        self.assertIn("login", node_row.last_probe_error_message.lower())
        self.assertEqual(node_row.last_probe_classification, "healthy")
        self.assertEqual(node_row.hoster_family, "hetzner")
        self.assertEqual(node_row.hoster_asn, "AS24940")
        self.assertEqual(node_row.hoster_subnet, "1.2.3.0/24")
        self.assertEqual(sample.probe_stage, "panel_login")
        self.assertEqual(sample.probe_error_kind, "panel_login_failed")
        node_transport = self._decode_transport_health(node_row.transport_health_json)
        sample_transport = self._decode_transport_health(sample.transport_health_json)
        self.assertEqual(node_transport["panel_state"], "failed")
        self.assertEqual(node_transport["panel_error_kind"], "panel_login_failed")
        self.assertEqual(node_transport["dataplane_state"], "healthy")
        self.assertEqual(node_transport["dataplane_stage"], "reality_target")
        self.assertEqual(node_transport["dns_resolution"], "healthy")
        self.assertIn("panel login failed", node_transport["root_cause_summary"].lower())
        self.assertIn("dataplane", node_transport["root_cause_detail"].lower())
        self.assertEqual(sample_transport["panel_state"], "failed")
        self.assertEqual(sample_transport["dataplane_state"], "healthy")

    def test_collect_one_persists_panel_lookup_and_dataplane_failure_separately(self) -> None:
        session = self.db.SessionLocal()
        try:
            node = session.query(self.models.Node).filter(self.models.Node.id == self.node_id).first()
        finally:
            session.close()

        with mock.patch.object(self.collector, "PanelClient", _FakePanelClientMissingInbound), mock.patch.object(
            self.collector,
            "probe_node_endpoint",
            return_value={
                "ok": False,
                "stage": "tls_sni",
                "error_kind": "tls_handshake_failed",
                "error_message": "tls handshake failed",
                "probe_classification": "provider_specific_path",
                "ipv4_health": "degraded",
                "ipv6_health": "unavailable",
                "transport_health": {
                    "dns_resolution": "healthy",
                    "tcp_connect": "healthy",
                    "tls_handshake": "degraded",
                    "reality_target": "unavailable",
                },
                "root_cause_summary": "TLS handshake reached the node but failed before the reality target check.",
                "root_cause_detail": "connected to 1.2.3.4 over ipv4",
                "connected_ip": "1.2.3.4",
                "probed_at": datetime.utcnow(),
            },
        ) as probe_mock:
            result = asyncio.run(self.collector._collect_one(node=node, error_window=5, source="tests"))

        probe_mock.assert_called_once()
        self.assertFalse(result["healthy"])
        self.assertEqual(result["panel_state"], "failed")
        self.assertEqual(result["dataplane_state"], "failed")
        node_row, sample = self._load_node()
        self.assertEqual(node_row.last_probe_stage, "panel_inbound_lookup")
        self.assertEqual(node_row.last_probe_error_kind, "inbound_not_found")
        self.assertEqual(node_row.last_probe_classification, "provider_specific_path")
        self.assertEqual(sample.probe_stage, "panel_inbound_lookup")
        self.assertEqual(sample.probe_error_kind, "inbound_not_found")
        node_transport = self._decode_transport_health(node_row.transport_health_json)
        sample_transport = self._decode_transport_health(sample.transport_health_json)
        self.assertEqual(node_transport["panel_state"], "failed")
        self.assertEqual(node_transport["panel_stage"], "panel_inbound_lookup")
        self.assertEqual(node_transport["panel_error_kind"], "inbound_not_found")
        self.assertEqual(node_transport["dataplane_state"], "failed")
        self.assertEqual(node_transport["dataplane_stage"], "tls_sni")
        self.assertEqual(node_transport["dataplane_error_kind"], "tls_handshake_failed")
        self.assertEqual(node_transport["tls_handshake"], "degraded")
        self.assertIn("panel inbound lookup failed", node_transport["root_cause_summary"].lower())
        self.assertIn("tls handshake failed", node_transport["root_cause_detail"].lower())
        self.assertEqual(sample_transport["panel_error_kind"], "inbound_not_found")
        self.assertEqual(sample_transport["dataplane_error_kind"], "tls_handshake_failed")

    def test_calc_score_penalizes_resource_pressure(self) -> None:
        baseline = self.collector._calc_score(
            latency_ms=80,
            error_rate=0.0,
            active_clients=20,
            healthy=True,
            cpu_percent=15.0,
            memory_used_mb=256,
            memory_total_mb=2048,
            disk_used_gb=10.0,
            disk_total_gb=40.0,
        )
        pressured = self.collector._calc_score(
            latency_ms=80,
            error_rate=0.0,
            active_clients=20,
            healthy=True,
            cpu_percent=92.0,
            memory_used_mb=1960,
            memory_total_mb=2048,
            disk_used_gb=38.5,
            disk_total_gb=40.0,
        )
        self.assertLess(pressured, baseline)

    def test_collect_one_preserves_missing_system_metrics_as_null(self) -> None:
        session = self.db.SessionLocal()
        try:
            node = session.query(self.models.Node).filter(self.models.Node.id == self.node_id).first()
        finally:
            session.close()

        with mock.patch.object(self.collector, "PanelClient", _FakePanelClientNoSystemMetrics), mock.patch.object(
            self.collector,
            "probe_node_endpoint",
            return_value={
                "ok": True,
                "stage": "reality_target",
                "error_kind": "",
                "error_message": "",
                "probed_at": datetime.utcnow(),
            },
        ):
            result = asyncio.run(self.collector._collect_one(node=node, error_window=5, source="tests"))

        self.assertTrue(result["healthy"])
        node_row, sample = self._load_node()
        self.assertIsNone(node_row.memory_used_mb)
        self.assertIsNone(node_row.memory_total_mb)
        self.assertIsNone(node_row.disk_used_gb)
        self.assertIsNone(node_row.disk_total_gb)
        self.assertIsNone(node_row.disk_free_gb)
        self.assertIsNone(sample.memory_used_mb)
        self.assertIsNone(sample.memory_total_mb)
        self.assertIsNone(sample.disk_used_gb)
        self.assertIsNone(sample.disk_total_gb)
        self.assertIsNone(sample.disk_free_gb)

    def test_collect_one_calculates_network_rates_from_cumulative_totals(self) -> None:
        session = self.db.SessionLocal()
        try:
            session.add(
                self.models.NodeHealthSample(
                    node_code="pl",
                    sampled_at=datetime.utcnow(),
                    network_rx_bytes_total=1_000_000_000,
                    network_tx_bytes_total=500_000_000,
                    network_rx_mbps=0.0,
                    network_tx_mbps=0.0,
                    network_total_mbps=0.0,
                    is_healthy=True,
                    score=90.0,
                    source="seed",
                )
            )
            session.commit()
            node = session.query(self.models.Node).filter(self.models.Node.id == self.node_id).first()
        finally:
            session.close()

        class _FakePanelClientNetwork:
            def __init__(self, runtime) -> None:
                self.runtime = runtime

            async def login(self) -> bool:
                return True

            async def get_system_metrics(self) -> dict:
                return {
                    "cpu_percent": 11.0,
                    "memory_used_mb": 256,
                    "memory_total_mb": 1024,
                    "disk_used_gb": 10.0,
                    "disk_total_gb": 40.0,
                    "disk_free_gb": 30.0,
                    "network_rx_bytes_total": 1_060_000_000,
                    "network_tx_bytes_total": 515_000_000,
                    "network_rx_bytes_per_sec": None,
                    "network_tx_bytes_per_sec": None,
                }

            async def _get_inbounds(self) -> list[dict]:
                return [
                    {
                        "id": self.runtime.inbound_id,
                        "settings": '{"clients":[{"id":"u1"},{"id":"u2"}]}',
                        "clientStats": [{"up": 100, "down": 200}],
                    }
                ]

            async def close(self) -> None:
                return None

        with mock.patch.object(self.collector, "PanelClient", _FakePanelClientNetwork), mock.patch.object(
            self.collector,
            "probe_node_endpoint",
            return_value={
                "ok": True,
                "stage": "reality_target",
                "error_kind": "",
                "error_message": "",
                "probed_at": datetime.utcnow(),
            },
        ), mock.patch.object(
            self.collector,
            "_utcnow",
            side_effect=[datetime(2026, 4, 2, 12, 0, 0), datetime(2026, 4, 2, 12, 1, 0)],
        ):
            result = asyncio.run(self.collector._collect_one(node=node, error_window=5, source="tests"))

        self.assertTrue(result["healthy"])
        node_row, sample = self._load_node()
        self.assertEqual(node_row.network_rx_bytes_total, 1_060_000_000)
        self.assertEqual(node_row.network_tx_bytes_total, 515_000_000)
        self.assertAlmostEqual(float(node_row.network_rx_mbps or 0.0), 8.0, places=2)
        self.assertAlmostEqual(float(node_row.network_tx_mbps or 0.0), 2.0, places=2)
        self.assertAlmostEqual(float(node_row.network_total_mbps or 0.0), 10.0, places=2)
        self.assertAlmostEqual(float(sample.network_total_mbps or 0.0), 10.0, places=2)

    def test_score_does_not_use_configured_client_count_as_load(self) -> None:
        low = self.collector._calc_score(
            latency_ms=100,
            error_rate=0.0,
            active_clients=0,
            healthy=True,
            cpu_percent=10.0,
            memory_used_mb=256,
            memory_total_mb=1024,
            disk_used_gb=10.0,
            disk_total_gb=40.0,
        )
        high = self.collector._calc_score(
            latency_ms=100,
            error_rate=0.0,
            active_clients=2000,
            healthy=True,
            cpu_percent=10.0,
            memory_used_mb=256,
            memory_total_mb=1024,
            disk_used_gb=10.0,
            disk_total_gb=40.0,
        )
        self.assertEqual(low, high)


if __name__ == "__main__":
    unittest.main()

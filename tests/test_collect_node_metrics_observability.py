import asyncio
import importlib
import importlib.util
import json
import os
import sys
import tempfile
import builtins
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
            "cpu_percent": None,
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
        self._authenticated_probe_patch = mock.patch.object(
            self.collector,
            "probe_authenticated_egress",
            return_value={
                "ok": True,
                "state": "healthy",
                "stage": "authenticated_egress",
                "error_kind": "",
                "probe_classification": "authenticated_egress",
                "probed_at": datetime.utcnow(),
            },
        )
        self.authenticated_probe_mock = self._authenticated_probe_patch.start()
        self.addCleanup(self._authenticated_probe_patch.stop)

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

    def test_collect_one_persists_only_safe_external_probe_failure_categories(self) -> None:
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
                "error_message": "private-token secret-node.example 203.0.113.99",
                "hoster_family": "hetzner",
                "hoster_asn": "AS24940",
                "hoster_subnet": "203.0.113.0/24",
                "probe_classification": "provider_specific_path",
                "ipv4_health": "degraded",
                "ipv6_health": "healthy",
                "transport_health": {
                    "dns_resolution": "healthy",
                    "tcp_connect": "healthy",
                    "tls_handshake": "degraded",
                    "reality_target": "unavailable",
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
        self.assertEqual(node_row.last_probe_error_message, "tls_handshake_failed")
        self.assertEqual(node_row.hoster_family, "hetzner")
        self.assertEqual(node_row.hoster_asn, "AS24940")
        self.assertIsNone(node_row.hoster_subnet)
        self.assertEqual(node_row.last_probe_classification, "provider_specific_path")
        self.assertEqual(node_row.ipv4_health, "degraded")
        self.assertEqual(node_row.ipv6_health, "healthy")
        node_transport = self._decode_transport_health(node_row.transport_health_json)
        self.assertEqual(node_transport["tls_handshake"], "degraded")
        self.assertIsNotNone(node_row.last_probe_at)
        self.assertIsNotNone(sample)
        self.assertEqual(sample.probe_stage, "tls_sni")
        self.assertEqual(sample.probe_error_kind, "tls_handshake_failed")
        self.assertEqual(sample.probe_classification, "provider_specific_path")
        self.assertEqual(sample.ipv4_health, "degraded")
        self.assertEqual(sample.ipv6_health, "healthy")
        sample_transport = self._decode_transport_health(sample.transport_health_json)
        self.assertEqual(sample_transport["tls_handshake"], "degraded")
        session = self.db.SessionLocal()
        try:
            runtime_metric = session.query(self.models.NodeRuntimeMetric).order_by(self.models.NodeRuntimeMetric.id.desc()).first()
        finally:
            session.close()
        self.assertIsNotNone(runtime_metric)
        persisted = " ".join(
            [
                str(node_row.last_probe_error_message or ""),
                str(node_row.transport_health_json or ""),
                str(sample.probe_error_message or ""),
                str(sample.transport_health_json or ""),
                str(getattr(runtime_metric, "meta_json", "") or ""),
            ]
        )
        for value in ("private-token", "secret-node.example", "203.0.113.99"):
            self.assertNotIn(value, persisted)

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
        self.assertEqual(node_row.last_probe_error_message, "panel_login_failed")
        self.assertEqual(node_row.last_probe_classification, "healthy")
        self.assertEqual(node_row.hoster_family, "hetzner")
        self.assertEqual(node_row.hoster_asn, "AS24940")
        self.assertIsNone(node_row.hoster_subnet)
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
        self.assertIn("edge_reachability_healthy", node_transport["root_cause_detail"])
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
        self.assertIn("tls_handshake_failed", node_transport["root_cause_detail"])
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

        self.assertFalse(result["healthy"])
        self.assertFalse(result["metrics_complete"])
        node_row, sample = self._load_node()
        self.assertFalse(node_row.is_healthy)
        self.assertEqual(node_row.health_score, 0.0)
        self.assertIsNone(node_row.cpu_percent)
        self.assertIsNone(node_row.memory_used_mb)
        self.assertIsNone(node_row.memory_total_mb)
        self.assertIsNone(node_row.disk_used_gb)
        self.assertIsNone(node_row.disk_total_gb)
        self.assertIsNone(node_row.disk_free_gb)
        self.assertIsNone(sample.cpu_percent)
        self.assertIsNone(sample.memory_used_mb)
        self.assertIsNone(sample.memory_total_mb)
        self.assertIsNone(sample.disk_used_gb)
        self.assertIsNone(sample.disk_total_gb)
        self.assertIsNone(sample.disk_free_gb)
        transport = self._decode_transport_health(sample.transport_health_json)
        self.assertEqual(transport["panel_state"], "healthy")
        self.assertEqual(transport["dataplane_state"], "healthy")
        self.assertEqual(transport["metrics_state"], "missing")

    def test_collect_one_fails_closed_when_authenticated_egress_material_is_unavailable(self) -> None:
        session = self.db.SessionLocal()
        try:
            node = session.query(self.models.Node).filter(self.models.Node.id == self.node_id).first()
        finally:
            session.close()

        with mock.patch.object(self.collector, "PanelClient", _FakePanelClientOk), mock.patch.object(
            self.collector,
            "probe_node_endpoint",
            return_value={
                "ok": True,
                "edge_reachability_ok": True,
                "stage": "reality_target",
                "error_kind": "",
                "error_message": "",
                "probe_classification": "healthy",
                "probed_at": datetime.utcnow(),
            },
        ), mock.patch.object(
            self.collector,
            "probe_authenticated_egress",
            return_value={
                "ok": None,
                "state": "unavailable",
                "stage": "authenticated_egress",
                "error_kind": "probe_material_unavailable",
                "probe_classification": "authenticated_egress_unavailable",
                "probed_at": datetime.utcnow(),
            },
        ):
            result = asyncio.run(self.collector._collect_one(node=node, error_window=5, source="tests"))

        self.assertFalse(result["healthy"])
        self.assertEqual(result["edge_reachability_state"], "healthy")
        self.assertEqual(result["authenticated_egress_state"], "unavailable")
        node_row, sample = self._load_node()
        self.assertTrue(node_row.edge_reachability_ok)
        self.assertTrue(node_row.dataplane_ok)
        self.assertIsNone(node_row.authenticated_egress_ok)
        self.assertFalse(node_row.is_healthy)
        self.assertEqual(node_row.last_probe_stage, "authenticated_egress")
        self.assertEqual(node_row.last_probe_error_kind, "probe_material_unavailable")
        transport = self._decode_transport_health(sample.transport_health_json)
        self.assertEqual(transport["edge_reachability_state"], "healthy")
        self.assertEqual(transport["authenticated_egress_state"], "unavailable")
        self.assertIn("authenticated egress is unavailable", transport["root_cause_summary"].lower())

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

    def test_collect_one_runs_dataplane_probe_via_to_thread(self) -> None:
        session = self.db.SessionLocal()
        try:
            node = session.query(self.models.Node).filter(self.models.Node.id == self.node_id).first()
        finally:
            session.close()

        calls: list[object] = []

        async def fake_to_thread(function, *args, **kwargs):
            calls.append(function)
            return function(*args, **kwargs)

        with mock.patch.object(self.collector, "PanelClient", _FakePanelClientOk), mock.patch.object(
            self.collector,
            "probe_node_endpoint",
            return_value={"ok": True, "stage": "reality_target", "probed_at": datetime.utcnow()},
        ) as probe_mock, mock.patch.object(self.collector.asyncio, "to_thread", side_effect=fake_to_thread):
            result = asyncio.run(self.collector._collect_one(node=node, error_window=5, source="tests"))

        self.assertTrue(result["healthy"])
        self.assertEqual(calls, [probe_mock, self.authenticated_probe_mock])
        probe_mock.assert_called_once()

    def test_run_bounds_concurrency_and_keeps_output_order(self) -> None:
        session = self.db.SessionLocal()
        try:
            for code in ("de", "us"):
                session.add(
                    self.models.Node(
                        code=code,
                        name=code.upper(),
                        host=f"{code}.pokrov.space",
                        inbound_id=1,
                        enabled=True,
                    )
                )
            session.commit()
        finally:
            session.close()

        active = 0
        max_active = 0

        async def fake_collect_one(*, node, error_window, source):
            nonlocal active, max_active
            active += 1
            max_active = max(max_active, active)
            try:
                await asyncio.sleep({"de": 0.03, "pl": 0.02, "us": 0.01}[node.code])
                return {
                    "code": node.code,
                    "healthy": True,
                    "score": 100.0,
                    "latency_ms": 1,
                    "dataplane_rtt_ms": 1,
                    "active_clients": 0,
                    "provisioned_clients_count": 0,
                    "online_connections_hint": 0,
                    "total_up_bytes": 0,
                    "total_down_bytes": 0,
                    "error_rate": 0.0,
                    "cpu_percent": 1.0,
                    "memory_used_mb": 1,
                    "memory_total_mb": 2,
                    "disk_free_gb": 1.0,
                    "network_total_mbps": 0.0,
                    "probe_stage": "reality_target",
                    "probe_error_kind": "",
                    "probe_classification": "healthy",
                    "ipv4_health": "healthy",
                    "ipv6_health": "unavailable",
                    "panel_state": "healthy",
                    "dataplane_state": "healthy",
                    "metrics_complete": True,
                }
            finally:
                active -= 1

        with mock.patch.object(self.collector, "_collect_one", side_effect=fake_collect_one), mock.patch.object(
            builtins, "print"
        ) as print_mock:
            self.assertEqual(
                asyncio.run(
                    self.collector.run(
                        error_window=5,
                        source="tests",
                        max_concurrency=2,
                        per_node_timeout_seconds=1,
                    )
                ),
                0,
            )

        self.assertEqual(max_active, 2)
        self.assertEqual([str(call.args[0]).split(":", 1)[0] for call in print_mock.call_args_list], ["de", "pl", "us"])

    def test_run_timeout_persists_unhealthy_state_and_hard_rejects_old_healthy_node(self) -> None:
        old_at = datetime(2026, 8, 2, 9, 0, 0)
        session = self.db.SessionLocal()
        try:
            node = session.query(self.models.Node).filter(self.models.Node.id == self.node_id).one()
            node.is_healthy = True
            node.health_score = 91.0
            node.last_health_at = old_at
            node.last_ok_at = old_at
            node.cpu_percent = 31.5
            node.memory_used_mb = 512
            node.memory_total_mb = 1024
            node.network_total_mbps = 14.25
            node.edge_reachability_ok = True
            node.authenticated_egress_ok = True
            node.dataplane_ok = True
            session.add(
                self.models.NodeHealthSample(
                    node_code="pl",
                    sampled_at=old_at,
                    cpu_percent=31.5,
                    is_healthy=True,
                    score=91.0,
                )
            )
            session.commit()
        finally:
            session.close()

        async def slow_collect_one(*, node, error_window, source):
            await asyncio.sleep(1)

        async def timeout_wait_for(awaitable, *, timeout):
            awaitable.close()
            raise TimeoutError

        with mock.patch.object(self.collector, "_collect_one", side_effect=slow_collect_one), mock.patch.object(
            self.collector.asyncio, "wait_for", side_effect=timeout_wait_for
        ), mock.patch.object(builtins, "print"):
            result = asyncio.run(
                self.collector.run(
                    error_window=5,
                    source="tests",
                    max_concurrency=1,
                    per_node_timeout_seconds=1,
                    only=["pl"],
                )
            )

        self.assertEqual(result, 0)
        session = self.db.SessionLocal()
        try:
            node = session.query(self.models.Node).filter(self.models.Node.id == self.node_id).one()
            sample = (
                session.query(self.models.NodeHealthSample)
                .order_by(self.models.NodeHealthSample.id.desc())
                .first()
            )
            runtime = (
                session.query(self.models.NodeRuntimeMetric)
                .order_by(self.models.NodeRuntimeMetric.id.desc())
                .first()
            )
            self.assertFalse(node.is_healthy)
            self.assertEqual(node.last_probe_stage, "collector")
            self.assertEqual(node.last_probe_error_kind, "collector_timeout")
            self.assertEqual(node.capacity_state, "hard_reject")
            self.assertEqual(node.capacity_reject_reason, "unhealthy")
            self.assertEqual(self.collector.node_capacity_status(node, now=node.last_health_at)["reject_reason"], "unhealthy")
            self.assertEqual(node.cpu_percent, 31.5)
            self.assertEqual(node.network_total_mbps, 14.25)
            self.assertEqual(node.last_ok_at, old_at)
            self.assertFalse(sample.is_healthy)
            self.assertEqual(sample.probe_error_kind, "collector_timeout")
            self.assertEqual(sample.probe_error_message, "collector_timeout")
            self.assertEqual(sample.probe_classification, "collector_unavailable")
            self.assertIsNone(sample.cpu_percent)
            self.assertIsNone(sample.network_total_mbps)
            self.assertEqual(self._decode_transport_health(sample.transport_health_json)["metrics_state"], "missing")
            self.assertEqual(runtime.capacity_state, "hard_reject")
            self.assertEqual(runtime.cpu_percent, 31.5)
            self.assertEqual(runtime.network_total_mbps, 14.25)
            self.assertEqual(json.loads(runtime.meta_json or "{}")["probe_error_kind"], "collector_timeout")
        finally:
            session.close()

    def test_run_exception_persists_redacted_failure_state(self) -> None:
        async def exploding_collect_one(*, node, error_window, source):
            raise RuntimeError("https://operator:private-token@example.invalid")

        with mock.patch.object(self.collector, "_collect_one", side_effect=exploding_collect_one), mock.patch.object(
            builtins, "print"
        ) as print_mock:
            result = asyncio.run(
                self.collector.run(
                    error_window=5,
                    source="tests",
                    max_concurrency=1,
                    per_node_timeout_seconds=1,
                    only=["pl"],
                )
            )

        self.assertEqual(result, 0)
        session = self.db.SessionLocal()
        try:
            node = session.query(self.models.Node).filter(self.models.Node.id == self.node_id).one()
            sample = session.query(self.models.NodeHealthSample).order_by(self.models.NodeHealthSample.id.desc()).first()
            self.assertFalse(node.is_healthy)
            self.assertEqual(node.last_probe_error_kind, "collector_exception")
            self.assertEqual(sample.probe_error_kind, "collector_exception")
            self.assertNotIn("private-token", sample.transport_health_json or "")
            self.assertNotIn("private-token", " ".join(str(call.args[0]) for call in print_mock.call_args_list))
        finally:
            session.close()

    def test_run_returns_nonzero_and_redacts_persistence_failure(self) -> None:
        async def exploding_collect_one(*, node, error_window, source):
            raise RuntimeError("postgres://operator:private-password@example.invalid")

        real_session_local = self.collector.SessionLocal
        session_count = 0

        def session_local():
            nonlocal session_count
            session_count += 1
            session = real_session_local()
            if session_count == 2:
                session.commit = mock.Mock(side_effect=RuntimeError("private-password"))
            return session

        with mock.patch.object(self.collector, "_collect_one", side_effect=exploding_collect_one), mock.patch.object(
            self.collector, "SessionLocal", side_effect=session_local
        ), mock.patch.object(builtins, "print") as print_mock:
            result = asyncio.run(
                self.collector.run(
                    error_window=5,
                    source="tests",
                    max_concurrency=1,
                    per_node_timeout_seconds=1,
                    only=["pl"],
                )
            )

        self.assertEqual(result, 1)
        printed = " ".join(str(call.args[0]) for call in print_mock.call_args_list)
        self.assertIn("collector_failure_persistence_failed", printed)
        self.assertIn("collector_status=persistence_failed", printed)
        self.assertNotIn("private-password", printed)
        session = self.db.SessionLocal()
        try:
            node = session.query(self.models.Node).filter(self.models.Node.id == self.node_id).one()
            self.assertTrue(node.is_healthy)
            self.assertEqual(session.query(self.models.NodeHealthSample).count(), 0)
        finally:
            session.close()

    def test_run_only_collects_the_exact_enabled_scope(self) -> None:
        untouched_at = datetime(2026, 8, 1, 12, 0, 0)
        session = self.db.SessionLocal()
        try:
            session.add(
                self.models.Node(
                    code="de",
                    name="Germany",
                    host="de.pokrov.space",
                    inbound_id=1,
                    enabled=True,
                    is_healthy=False,
                    last_probe_at=untouched_at,
                )
            )
            session.commit()
        finally:
            session.close()

        calls: list[str] = []

        async def fake_collect_one(*, node, error_window, source):
            calls.append(str(node.code))
            return {
                "code": node.code,
                "healthy": True,
                "score": 100.0,
                "latency_ms": 1,
                "dataplane_rtt_ms": 1,
                "active_clients": 0,
                "provisioned_clients_count": 0,
                "online_connections_hint": 0,
                "total_up_bytes": 0,
                "total_down_bytes": 0,
                "error_rate": 0.0,
                "cpu_percent": 1.0,
                "memory_used_mb": 1,
                "memory_total_mb": 2,
                "disk_free_gb": 1.0,
                "network_total_mbps": 0.0,
                "probe_stage": "authenticated_egress",
                "probe_error_kind": "",
                "probe_classification": "authenticated_egress",
                "ipv4_health": "healthy",
                "ipv6_health": "unavailable",
                "panel_state": "healthy",
                "dataplane_state": "healthy",
                "metrics_complete": True,
            }

        with mock.patch.object(self.collector, "_collect_one", side_effect=fake_collect_one), mock.patch.object(
            builtins, "print"
        ):
            result = asyncio.run(
                self.collector.run(
                    error_window=5,
                    source="tests",
                    max_concurrency=1,
                    per_node_timeout_seconds=1,
                    only=["pl"],
                )
            )

        self.assertEqual(result, 0)
        self.assertEqual(calls, ["pl"])
        session = self.db.SessionLocal()
        try:
            untouched = session.query(self.models.Node).filter_by(code="de").one()
            self.assertFalse(untouched.is_healthy)
            self.assertEqual(untouched.last_probe_at, untouched_at)
            self.assertEqual(session.query(self.models.NodeHealthSample).count(), 0)
            self.assertEqual(session.query(self.models.NodeRuntimeMetric).count(), 0)
        finally:
            session.close()

    def test_run_only_rejects_unknown_or_disabled_code_before_collection(self) -> None:
        untouched_at = datetime(2026, 8, 1, 12, 0, 0)
        session = self.db.SessionLocal()
        try:
            session.add(
                self.models.Node(
                    code="de",
                    name="Germany",
                    host="de.pokrov.space",
                    inbound_id=1,
                    enabled=False,
                    is_healthy=False,
                    last_probe_at=untouched_at,
                )
            )
            session.commit()
        finally:
            session.close()

        with mock.patch.object(self.collector, "_collect_one") as collect_one, mock.patch.object(
            self.collector, "init_db"
        ) as init_db, mock.patch.object(builtins, "print") as print_mock:
            result = asyncio.run(
                self.collector.run(
                    error_window=5,
                    source="tests",
                    only=["de", "unknown"],
                )
            )

        self.assertEqual(result, 2)
        init_db.assert_not_called()
        collect_one.assert_not_called()
        self.assertEqual(print_mock.call_args.args[0], "Requested --only scope does not match enabled node inventory.")
        session = self.db.SessionLocal()
        try:
            untouched = session.query(self.models.Node).filter_by(code="de").one()
            self.assertFalse(untouched.is_healthy)
            self.assertEqual(untouched.last_probe_at, untouched_at)
            self.assertEqual(session.query(self.models.NodeHealthSample).count(), 0)
            self.assertEqual(session.query(self.models.NodeRuntimeMetric).count(), 0)
        finally:
            session.close()

    def test_main_parses_only_as_a_normalized_exact_allowlist(self) -> None:
        with mock.patch.object(sys, "argv", ["collect_node_metrics.py", "--only", "PL,de"]), mock.patch.object(
            self.collector, "run", new_callable=mock.AsyncMock, return_value=0
        ) as run_mock:
            self.assertEqual(self.collector.main(), 0)

        self.assertEqual(run_mock.await_args.kwargs["only"], ["de", "pl"])

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

import asyncio
import importlib
import importlib.util
import os
import sys
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

        self.db_path = str((self.repo_root / f"portal_api_test_{uuid.uuid4().hex}.db").resolve())
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
        self.assertIsNotNone(node_row.last_probe_at)
        self.assertIsNotNone(sample)
        self.assertEqual(sample.probe_stage, "tls_sni")
        self.assertEqual(sample.probe_error_kind, "tls_handshake_failed")

    def test_collect_one_persists_panel_login_failure_details(self) -> None:
        session = self.db.SessionLocal()
        try:
            node = session.query(self.models.Node).filter(self.models.Node.id == self.node_id).first()
        finally:
            session.close()

        with mock.patch.object(self.collector, "PanelClient", _FakePanelClientLoginFail), mock.patch.object(
            self.collector,
            "probe_node_endpoint",
            return_value={"ok": True, "stage": "reality_target", "error_kind": "", "error_message": "", "probed_at": datetime.utcnow()},
        ):
            result = asyncio.run(self.collector._collect_one(node=node, error_window=5, source="tests"))

        self.assertFalse(result["healthy"])
        node_row, sample = self._load_node()
        self.assertEqual(node_row.last_probe_stage, "panel_login")
        self.assertEqual(node_row.last_probe_error_kind, "panel_login_failed")
        self.assertIn("login", node_row.last_probe_error_message.lower())
        self.assertEqual(sample.probe_stage, "panel_login")
        self.assertEqual(sample.probe_error_kind, "panel_login_failed")

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


if __name__ == "__main__":
    unittest.main()

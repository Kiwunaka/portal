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


if __name__ == "__main__":
    unittest.main()

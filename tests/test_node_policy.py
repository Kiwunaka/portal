from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    portal_dir = str(repo_root / "portal_bot")
    if portal_dir not in sys.path:
        sys.path.insert(0, portal_dir)
    module_path = repo_root / "portal_bot" / "node_policy.py"
    spec = importlib.util.spec_from_file_location("node_policy", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@dataclass
class _Node:
    last_health_at: datetime | None = None
    last_probe_at: datetime | None = None
    last_ok_at: datetime | None = None


class NodePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_utcnow_returns_naive_utc_datetime(self) -> None:
        now = self.module._utcnow()

        self.assertIsNone(now.tzinfo)

    def test_node_is_stale_accepts_timezone_aware_samples(self) -> None:
        aware_now = datetime.now(timezone.utc)
        stale_node = _Node(last_health_at=aware_now - timedelta(hours=1))
        fresh_node = _Node(last_health_at=aware_now - timedelta(seconds=60))

        self.assertTrue(self.module.node_is_stale(stale_node))
        self.assertFalse(self.module.node_is_stale(fresh_node))

    def test_capacity_hard_rejects_nearly_full_disk(self) -> None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        node = SimpleNamespace(
            enabled=True,
            accepting_new_clients=True,
            is_draining=False,
            is_healthy=True,
            dataplane_ok=True,
            last_probe_at=now,
            cpu_percent=20.0,
            disk_used_gb=96.0,
            disk_total_gb=100.0,
        )

        status = self.module.node_capacity_status(node, now=now)

        self.assertEqual(status["state"], "hard_reject")
        self.assertEqual(status["reject_reason"], "disk_full")
        self.assertEqual(status["disk_percent"], 96.0)

    def test_capacity_marks_disk_warning_as_warm(self) -> None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        node = SimpleNamespace(
            enabled=True,
            accepting_new_clients=True,
            is_draining=False,
            is_healthy=True,
            dataplane_ok=True,
            last_probe_at=now,
            cpu_percent=20.0,
            disk_used_gb=92.0,
            disk_total_gb=100.0,
        )

        status = self.module.node_capacity_status(node, now=now)

        self.assertEqual(status["state"], "warm")
        self.assertIsNone(status["reject_reason"])
        self.assertEqual(status["disk_percent"], 92.0)

    def test_capacity_does_not_infer_disk_usage_without_total(self) -> None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        node = SimpleNamespace(
            enabled=True,
            accepting_new_clients=True,
            is_draining=False,
            is_healthy=True,
            dataplane_ok=True,
            last_probe_at=now,
            cpu_percent=20.0,
            disk_used_gb=96.0,
            disk_total_gb=0.0,
        )

        status = self.module.node_capacity_status(node, now=now)

        self.assertEqual(status["state"], "healthy")
        self.assertIsNone(status["disk_percent"])

    def test_access_roles_reject_overlap_from_any_transport_profile(self) -> None:
        shared_panel = {
            "panel_base_url": "https://panel.example.test:8444",
            "panel_path": "panel",
            "enabled": True,
        }
        paid = SimpleNamespace(
            id=1,
            code="nl-paid",
            name="NL Paid",
            inbound_id=43,
            access_role="paid",
            transport_profiles_json=json.dumps(
                {
                    "operator_shadow": {"inbound_id": 42, "enabled": True},
                }
            ),
            **shared_panel,
        )
        free_soft = SimpleNamespace(
            id=2,
            code="nl-free-soft",
            name="NL Free Soft",
            inbound_id=42,
            access_role="free_soft",
            transport_profiles_json=None,
            **shared_panel,
        )

        with self.assertRaisesRegex(
            self.module.NodeAccessRoleError,
            r"duplicate panel transport inbound binding for "
            r"nl-paid/operator_shadow and nl-free-soft/legacy_reality_fallback: inbound_id=42",
        ):
            self.module.validate_node_access_roles([paid, free_soft])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.util
import sys
import unittest
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
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


if __name__ == "__main__":
    unittest.main()

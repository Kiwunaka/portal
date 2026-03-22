import importlib.util
import sys
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "audit_node_dns.py"
    spec = importlib.util.spec_from_file_location("audit_node_dns", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AuditNodeDnsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_build_hosts_covers_all_delivery_nodes(self) -> None:
        hosts = self.module._build_hosts(
            domain="pokrov.space",
            include_brain=True,
            inventory={
                "brain": "82.21.114.104",
                "pl": "82.40.38.84",
                "it": "151.241.215.84",
                "us": "82.21.92.142",
                "nl": "82.24.195.93",
                "free": "151.245.217.23",
            },
        )

        self.assertEqual(
            [item.code for item in hosts],
            ["pl", "it", "us", "nl", "free", "brain"],
        )
        self.assertEqual(hosts[3].host, "nl.pokrov.space")
        self.assertEqual(hosts[4].host, "free.pokrov.space")


if __name__ == "__main__":
    unittest.main()

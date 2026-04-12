import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "remote_brain_network_probe.py"
    spec = importlib.util.spec_from_file_location("remote_brain_network_probe", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RemoteBrainNetworkProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_parse_inventory_reads_ip_from_current_inventory_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inventory = Path(tmp) / "inventory.md"
            inventory.write_text(
                "\n".join(
                    [
                        "| Code | Physical name | Country | Role | Runtime status | Plan | IP |",
                        "|---|---|---|---|---|---|---|",
                        "| `brain` | `BRAINnode` | `DE` | Brain / control-plane | enabled | `2 vCPU` | `82.21.114.104` |",
                        "| `us` | `USnode` | `US` | Premium delivery | enabled | `1 vCPU` | `82.21.92.142` |",
                    ]
                ),
                encoding="utf-8",
            )

            parsed = self.module._parse_inventory(inventory)

        self.assertEqual(parsed["brain"], "82.21.114.104")
        self.assertEqual(parsed["us"], "82.21.92.142")

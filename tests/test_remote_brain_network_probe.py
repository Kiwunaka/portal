import importlib.util
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_module():
    path = SCRIPTS_DIR / "remote_brain_network_probe.py"
    spec = importlib.util.spec_from_file_location("remote_brain_network_probe", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class RemoteBrainNetworkProbeTests(unittest.TestCase):
    def test_parse_inventory_uses_named_ip_column(self) -> None:
        module = _load_module()
        inventory_text = textwrap.dedent(
            """
            | Code | Physical name | Country | Role | Runtime status | Plan | IP |
            |---|---|---|---|---|---|---|
            | `brain` | `BRAINnode` | `DE` | Brain / control-plane | enabled | `2 vCPU` | `82.21.114.104` |
            | `pl` | `PLnode` | `PL` | Premium delivery | enabled | `1 vCPU` | `82.40.38.84` |
            """
        ).strip()

        with tempfile.TemporaryDirectory() as tmp_dir:
            inventory_path = Path(tmp_dir) / "inventory.md"
            inventory_path.write_text(inventory_text, encoding="utf-8")

            parsed = module._parse_inventory(inventory_path)

        self.assertEqual(
            parsed,
            {
                "brain": "82.21.114.104",
                "pl": "82.40.38.84",
            },
        )


if __name__ == "__main__":
    unittest.main()

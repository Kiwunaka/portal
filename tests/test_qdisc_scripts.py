from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


def _load_module(name: str, relative_path: str):
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class QdiscScriptTests(unittest.TestCase):
    def test_remote_apply_node_qdisc_builds_cake_and_fq_codel_commands(self) -> None:
        module = _load_module("remote_apply_node_qdisc", "scripts/remote_apply_node_qdisc.py")

        profile = {
            "node_code": "pl",
            "iface": "eth0",
            "uplink_mbps": 1000,
            "target_rate_mbps": 850,
            "preferred_qdisc": "cake",
        }

        cake_commands = module._build_apply_commands(profile, has_cake=True)
        fallback_commands = module._build_apply_commands(profile, has_cake=False)

        self.assertTrue(any("cake bandwidth 850mbit nat triple-isolate" in command for command in cake_commands))
        self.assertTrue(any("fq_codel" in command for command in fallback_commands))

    def test_remote_apply_node_qdisc_loads_repo_truth_profiles(self) -> None:
        module = _load_module("remote_apply_node_qdisc", "scripts/remote_apply_node_qdisc.py")

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "node-qdisc-profiles.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "node_code": "pl",
                            "iface": "eth0",
                            "uplink_mbps": 1000,
                            "target_rate_mbps": 850,
                            "preferred_qdisc": "cake",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            profiles = module.load_profiles(path)

        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles["pl"]["target_rate_mbps"], 850)
        self.assertEqual(profiles["pl"]["preferred_qdisc"], "cake")

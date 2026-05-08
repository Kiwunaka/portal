from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


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
    def test_repo_truth_profiles_include_free_node(self) -> None:
        module = _load_module("remote_apply_node_qdisc_repo_truth", "scripts/remote_apply_node_qdisc.py")

        profiles = module.load_profiles()

        self.assertIn("free", profiles)

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

    def test_remote_apply_node_qdisc_prefers_profile_selected_qdisc_even_when_cake_exists(self) -> None:
        module = _load_module("remote_apply_node_qdisc_preferred", "scripts/remote_apply_node_qdisc.py")

        executed: list[str] = []

        def executor(cmd: str) -> tuple[int, str, str]:
            executed.append(cmd)
            if "modprobe -n -q sch_cake" in cmd:
                return 0, "cake\n", ""
            return 0, "", ""

        profile = {
            "node_code": "pl",
            "iface": "eth0",
            "uplink_mbps": 1000,
            "target_rate_mbps": 850,
            "preferred_qdisc": "fq_codel",
            "enabled": True,
        }

        module.apply_profile(profile, executor=executor)

        self.assertTrue(any("root fq_codel" in command for command in executed))
        self.assertFalse(any("root cake bandwidth" in command for command in executed))

    def test_remote_apply_node_qdisc_apply_rolls_back_when_profile_disabled(self) -> None:
        module = _load_module("remote_apply_node_qdisc_disabled", "scripts/remote_apply_node_qdisc.py")

        executed: list[str] = []

        def executor(cmd: str) -> tuple[int, str, str]:
            executed.append(cmd)
            return 0, "", ""

        profile = {
            "node_code": "pl",
            "iface": "eth0",
            "uplink_mbps": 1000,
            "target_rate_mbps": 850,
            "preferred_qdisc": "cake",
            "enabled": False,
        }

        _code, summary = module.apply_profile(profile, executor=executor)

        self.assertIn("disabled", summary.lower())
        self.assertTrue(any("qdisc del dev eth0 root" in command for command in executed))
        self.assertFalse(any("qdisc replace dev eth0 root" in command for command in executed))

    def test_remote_apply_node_qdisc_select_profile_normalizes_known_host_aliases_and_node_code_env(self) -> None:
        module = _load_module("remote_apply_node_qdisc_aliases", "scripts/remote_apply_node_qdisc.py")

        profiles = {
            "pl": {"node_code": "pl", "iface": "eth0"},
            "nl": {"node_code": "nl", "iface": "eth0"},
            "free": {"node_code": "free", "iface": "eth0"},
        }

        self.assertEqual(module._select_profile(profiles, "PLnode")["node_code"], "pl")
        self.assertEqual(module._select_profile(profiles, "FREENLnode")["node_code"], "free")
        with patch.dict(module.os.environ, {"NODE_CODE": "nl"}, clear=False):
            with patch.object(module.socket, "gethostname", return_value="PLnode"):
                self.assertEqual(module._select_profile(profiles, None)["node_code"], "nl")

    def test_remote_apply_node_qdisc_builds_persistence_commands_and_rollback_disables_service(self) -> None:
        module = _load_module("remote_apply_node_qdisc_persistence", "scripts/remote_apply_node_qdisc.py")

        install_commands = module._build_persistence_commands("install")
        disable_commands = module._build_persistence_commands("disable")
        uninstall_commands = module._build_persistence_commands("uninstall")
        rollback_commands = module._build_rollback_commands({"iface": "eth0"})

        self.assertTrue(any("systemctl enable --now portal-node-qdisc.service" in command for command in install_commands))
        self.assertTrue(any("systemctl disable --now portal-node-qdisc.service" in command for command in disable_commands))
        self.assertTrue(any("rm -f /etc/systemd/system/portal-node-qdisc.service" in command for command in uninstall_commands))
        self.assertTrue(any("systemctl disable --now portal-node-qdisc.service" in command for command in rollback_commands))

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

    def test_remote_node_qdisc_smoke_uses_same_node_alias_normalization(self) -> None:
        module = _load_module("remote_node_qdisc_smoke_aliases", "scripts/remote_node_qdisc_smoke.py")

        profiles = {"free": {"node_code": "free", "iface": "eth0"}}

        self.assertEqual(module._select_profile(profiles, "FREENLnode")["node_code"], "free")

    def test_remote_node_qdisc_smoke_gate_requires_heavy_flow_evidence(self) -> None:
        module = _load_module("remote_node_qdisc_smoke_gate", "scripts/remote_node_qdisc_smoke.py")

        failures = module.evaluate_gate(
            {
                "node_code": "pl",
                "iface": "eth0",
                "probe_connect_p95": 0.2,
                "probe_ttfb_p95": 0.3,
                "probe_total_p95": 0.4,
                "probe_connect_samples": [0.2, 0.2, 0.2],
                "probe_ttfb_samples": [0.3, 0.3, 0.3],
                "probe_total_samples": [0.4, 0.4, 0.4],
                "probe_return_code": 0,
                "heavy_bytes_downloaded": 0,
                "heavy_elapsed_seconds": 0.0,
                "heavy_exit_code": 0,
            },
            min_heavy_bytes=1048576,
            min_probe_successes=3,
            max_probe_connect_p95_seconds=1.0,
            max_probe_ttfb_p95_seconds=1.0,
            max_probe_total_p95_seconds=2.0,
        )

        self.assertTrue(any("heavy flow" in item.lower() for item in failures))

    def test_remote_node_qdisc_smoke_preserves_failed_heavy_flow_exit_code(self) -> None:
        module = _load_module("remote_node_qdisc_smoke_failed_heavy", "scripts/remote_node_qdisc_smoke.py")

        def fake_executor(cmd: str) -> tuple[int, str, str]:
            if "tc -s qdisc" in cmd:
                return 0, "qdisc ok", ""
            return 0, "0.1 0.2 0.3\n0.1 0.2 0.3\n0.1 0.2 0.3\n", ""

        class FakeHeavyProcess:
            pid = 4242
            returncode = 28

            def poll(self) -> int:
                return self.returncode

            def terminate(self) -> None:
                raise AssertionError("already-failed heavy flow must not be terminated as running")

            def communicate(self, timeout: int = 10) -> tuple[str, str]:
                return "2097152 0.500\n", "curl: transfer closed with outstanding read data"

        with patch.object(module, "_run_local", fake_executor):
            with patch.object(module.subprocess, "Popen", return_value=FakeHeavyProcess()):
                report = module.run_smoke(
                    {"node_code": "pl", "iface": "eth0"},
                    probe_url="https://probe.pokrov.test",
                    heavy_url="https://heavy.pokrov.test/file",
                    executor=module._run_local,
                )

        self.assertEqual(report["heavy_exit_code"], 28)
        failures = module.evaluate_gate(
            report,
            min_heavy_bytes=1048576,
            min_probe_successes=3,
            max_probe_connect_p95_seconds=1.0,
            max_probe_ttfb_p95_seconds=1.0,
            max_probe_total_p95_seconds=2.0,
        )
        self.assertTrue(any("heavy flow exited non-zero" in item for item in failures))

    def test_remote_node_qdisc_smoke_main_exits_non_zero_on_threshold_failure(self) -> None:
        module = _load_module("remote_node_qdisc_smoke_main", "scripts/remote_node_qdisc_smoke.py")

        args = module.argparse.Namespace(
            profiles="C:/tmp/node-qdisc-profiles.json",
            node_code="pl",
            host="",
            ssh_user="root",
            ssh_port=29374,
            passwords="C:/tmp/PASSWORDS.txt",
            probe_url="https://1.1.1.1/cdn-cgi/trace",
            heavy_url="https://speed.cloudflare.com/__down?bytes=50000000",
            probe_attempts=8,
            probe_pause_seconds=1.0,
            heavy_timeout_seconds=120,
            heavy_duration_seconds=10.0,
            min_heavy_bytes=1048576,
            min_probe_successes=3,
            max_probe_connect_p95_seconds=1.0,
            max_probe_ttfb_p95_seconds=1.0,
            max_probe_total_p95_seconds=2.0,
        )

        report = {
            "node_code": "pl",
            "iface": "eth0",
            "probe_url": args.probe_url,
            "heavy_url": args.heavy_url,
            "probe_attempts": args.probe_attempts,
            "probe_connect_p95": 0.2,
            "probe_ttfb_p95": 1.8,
            "probe_total_p95": 2.5,
            "probe_connect_samples": [0.2, 0.2, 0.2],
            "probe_ttfb_samples": [1.8, 1.8, 1.8],
            "probe_total_samples": [2.5, 2.5, 2.5],
            "probe_return_code": 0,
            "probe_stderr": "",
            "tc_snapshots": ["tc_before", "tc_after"],
            "heavy_bytes_downloaded": 5 * 1024 * 1024,
            "heavy_elapsed_seconds": 4.0,
            "heavy_exit_code": 0,
        }

        with patch.object(module.argparse.ArgumentParser, "parse_args", return_value=args):
            with patch.object(module, "_load_profiles", return_value={"pl": {"node_code": "pl", "iface": "eth0"}}):
                with patch.object(module, "_select_profile", return_value={"node_code": "pl", "iface": "eth0"}):
                    with patch.object(module, "run_smoke", return_value=report):
                        self.assertNotEqual(module.main(), 0)

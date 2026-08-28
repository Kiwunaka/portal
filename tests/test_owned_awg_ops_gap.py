import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_module(name: str):
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class OwnedAwgActivationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module("remote_activate_owned_awg_labs")

    def test_service_unit_pins_owned_userspace_binary_and_quick_wrapper(self) -> None:
        module = self.module
        unit = module._unit_content().decode("utf-8")

        self.assertIn(
            f"Environment=WG_QUICK_USERSPACE_IMPLEMENTATION={module.SERVER_BINARY_TARGET}",
            unit,
        )
        self.assertIn(f"ExecStart={module.AWG_QUICK_TARGET} up %i", unit)
        self.assertIn(f"ExecReload=/bin/bash -c 'exec {module.AWG_TARGET} syncconf", unit)

    def test_server_preflight_requires_every_target_absent_and_udp_port_free(self) -> None:
        module = self.module
        with patch.object(
            module,
            "_run_remote",
            side_effect=["absent"] * 7 + ["free", "free"],
        ) as run_remote:
            result = module._server_preflight(MagicMock())

        self.assertEqual(result["occupied_paths"], [])
        self.assertEqual(result["udp_ports"], {"4500": "free", "3478": "free"})
        self.assertEqual(run_remote.call_count, 9)

    def test_awg31_variant_is_randomized_and_keeps_distinct_interface(self) -> None:
        module = self.module
        awg2, awg31, _server2, _server31 = module._endpoint_material("192.0.2.10")

        self.assertEqual(awg2["peers"][0]["port"], module.AWG2_PORT)
        self.assertEqual(awg31["peers"][0]["port"], module.AWG31_PORT)
        self.assertTrue(awg31["random_trailers"])
        self.assertEqual(awg31["content_padding_addition"], "64-512")
        self.assertNotEqual(awg2["private_key"], awg31["private_key"])


class OwnedAwgUdpPathContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module("remote_probe_owned_awg_udp_path")

    def test_phone_selector_excludes_emulators_and_requires_one_physical_device(self) -> None:
        module = self.module
        completed = SimpleNamespace(
            stdout=(
                "List of devices attached\n"
                "emulator-5554 device\n"
                "2UCUT24716017005 device\n"
            )
        )
        with patch.object(module.subprocess, "run", return_value=completed):
            self.assertEqual(
                module._phone_serial(Path("C:/Android/adb.exe")),
                "2UCUT24716017005",
            )

        completed.stdout += "SECOND-PHONE device\n"
        with patch.object(module.subprocess, "run", return_value=completed):
            with self.assertRaisesRegex(RuntimeError, "exactly one physical phone"):
                module._phone_serial(Path("C:/Android/adb.exe"))

    def test_phone_sender_cleanup_runs_when_probe_execution_fails(self) -> None:
        module = self.module
        calls = [
            SimpleNamespace(returncode=0),
            SimpleNamespace(returncode=0),
            SimpleNamespace(returncode=1),
            SimpleNamespace(returncode=0),
        ]
        with patch.object(module.subprocess, "run", side_effect=calls) as run:
            with self.assertRaisesRegex(RuntimeError, "sender unavailable"):
                module._send_phone(
                    Path("C:/Android/adb.exe"),
                    "PHONE",
                    Path("C:/safe/pokrov-udp-probe"),
                    "192.0.2.10",
                    module.PROFILE_PORTS["awg2_lab"],
                )

        self.assertEqual(run.call_count, 4)
        self.assertEqual(run.call_args_list[-1].args[0][-3:], ["rm", "-f", "/data/local/tmp/pokrov-udp-probe"])


class OwnedAwgCoreInteropContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module("remote_run_owned_awg_core_interop")

    def test_interop_failure_classification_keeps_network_boundaries_distinct(self) -> None:
        module = self.module
        cases = {
            "before an outer packet was emitted": "failed_before_outer_packet",
            "after an outer packet write error": "failed_outer_write",
            "because no outer response was received": "failed_no_outer_response",
            "after outer responses were received": "failed_after_outer_response",
            "owned AWG TLS egress failed": "failed_tls",
            "owned AWG TCP egress failed": "failed_tcp",
        }
        for output, expected in cases.items():
            with self.subTest(output=output):
                self.assertEqual(module._classify(output, 1), expected)
        self.assertEqual(module._classify("", 0), "passed")
        self.assertEqual(module._classify("unknown", 1), "failed_other")

    def test_remote_helper_accepts_only_owned_profiles(self) -> None:
        helper = self.module._REMOTE_HELPER

        self.assertIn('{"awg2_lab", "awg31_lab"}', helper)
        self.assertIn('raise SystemExit("profile invalid")', helper)
        self.assertIn("Awg2LabMaterial.is_active.is_(True)", helper)
        self.assertIn("Awg31LabMaterial.is_active.is_(True)", helper)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import io
import sys
import tempfile
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
        self.assertIn(
            f"ExecReload=/bin/bash -c 'exec {module.AWG_TARGET} syncconf", unit
        )

    def test_server_preflight_requires_every_target_absent_and_udp_port_free(
        self,
    ) -> None:
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
        self.assertEqual(awg31["content_padding_addition"], "0")
        self.assertNotEqual(awg2["private_key"], awg31["private_key"])

    def test_new_owned_lab_material_uses_mobile_safe_mtu(self) -> None:
        module = self.module
        awg2, awg31, server2, server31 = module._endpoint_material("192.0.2.10")

        self.assertEqual(module.OWNED_AWG_MTU, 1280)
        self.assertEqual(awg2["mtu"], module.OWNED_AWG_MTU)
        self.assertEqual(awg31["mtu"], module.OWNED_AWG_MTU)
        self.assertIn(f"MTU = {module.OWNED_AWG_MTU}", server2)
        self.assertIn(f"MTU = {module.OWNED_AWG_MTU}", server31)

    def test_server_configs_pin_outer_udp_replies_to_the_endpoint_address(self) -> None:
        module = self.module
        endpoint = "192.0.2.10"
        _awg2, _awg31, server2, server31 = module._endpoint_material(endpoint)

        for interface, port, config in (
            (module.AWG2_INTERFACE, module.AWG2_PORT, server2),
            (module.AWG31_INTERFACE, module.AWG31_PORT, server31),
        ):
            with self.subTest(interface=interface):
                self.assertIn(
                    f"-o eth0 -p udp -m udp --sport {port}",
                    config,
                )
                self.assertIn(
                    f"--comment 'POKROV owned {interface} reply source'",
                    config,
                )
                self.assertIn(f"-j SNAT --to-source {endpoint}", config)
                self.assertIn(
                    f"ip -4 rule add priority {10_000 + port} ipproto udp "
                    f"sport {port} lookup {20_000 + port}",
                    config,
                )
                self.assertIn(
                    f"ip -4 route replace table {20_000 + port} default",
                    config,
                )
                self.assertIn("PostUp = iptables -t nat -C POSTROUTING", config)
                self.assertIn("PostDown = iptables -t nat -D POSTROUTING", config)

    def test_activation_helper_uses_current_mobile_safe_awg31_metadata(self) -> None:
        helper = self.module._REMOTE_ADMIN_HELPER

        self.assertIn(self.module.AWG31_GENERATION, helper)
        self.assertIn(self.module.AWG31_SERVER_RECORD, helper)
        self.assertIn(self.module.AWG31_VARIANT, helper)
        self.assertNotIn("awg31-lab-v3-randomized-trailers", helper)
        self.assertNotIn("de-awg31-20260828-03-randomized-trailers", helper)


class OwnedAwgUdpPathContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module("remote_probe_owned_awg_udp_path")

    def test_phone_selector_excludes_emulators_and_requires_one_physical_device(
        self,
    ) -> None:
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
        self.assertEqual(
            run.call_args_list[-1].args[0][-3:],
            ["rm", "-f", "/data/local/tmp/pokrov-udp-probe"],
        )


class OwnedAwgReplySourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module("remote_ensure_owned_awg_reply_source")

    def test_config_injection_is_idempotent_and_bound_to_one_lab_port(self) -> None:
        module = self.module
        original = b"""[Interface]\nListenPort = 4500\nPostUp = true\nPostDown = true\n\n[Peer]\nAllowedIPs = 10.0.0.2/32\n"""

        updated, changed = module._updated_config(
            original, "pokrovawg2", 4500, "192.0.2.10"
        )
        repeated, changed_again = module._updated_config(
            updated, "pokrovawg2", 4500, "192.0.2.10"
        )

        self.assertTrue(changed)
        self.assertFalse(changed_again)
        self.assertEqual(updated, repeated)
        text = updated.decode("utf-8")
        self.assertEqual(text.count("POKROV owned pokrovawg2 reply source"), 3)
        self.assertIn("--sport 4500", text)
        self.assertIn("--to-source 192.0.2.10", text)
        self.assertIn("sport 4500 lookup 24500", text)
        self.assertIn("route replace table 24500 default", text)

    def test_config_injection_rejects_a_conflicting_managed_rule(self) -> None:
        module = self.module
        conflicting = b"""[Interface]\nListenPort = 4500\nPostUp = echo 'POKROV owned pokrovawg2 reply source'\nPostDown = true\n\n[Peer]\n"""

        with self.assertRaisesRegex(RuntimeError, "conflicting"):
            module._updated_config(conflicting, "pokrovawg2", 4500, "192.0.2.10")


class OwnedAwgMtuUpdateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module("remote_set_owned_awg_mtu")

    def test_server_mtu_transform_is_exact_and_idempotent(self) -> None:
        module = self.module
        original = b"[Interface]\nMTU = 1408\nListenPort = 4500\n"

        updated = module._replace_server_mtu(original, target=1280)
        repeated = module._replace_server_mtu(updated, target=1280)

        self.assertEqual(module._server_mtu(updated), 1280)
        self.assertEqual(updated, repeated)

    def test_server_mtu_transform_rejects_unowned_or_duplicate_values(self) -> None:
        module = self.module
        with self.assertRaisesRegex(RuntimeError, "outside the owned contract"):
            module._replace_server_mtu(b"[Interface]\nMTU = 1500\n", target=1280)
        with self.assertRaisesRegex(RuntimeError, "precondition"):
            module._replace_server_mtu(
                b"[Interface]\nMTU = 1408\nMTU = 1408\n",
                target=1280,
            )

    def test_material_mtu_transform_preserves_other_fields(self) -> None:
        module = self.module
        endpoint = module._material_with_mtu(
            b'{"mtu":1408,"private_key":"kept-in-memory-only","peers":[]}',
            target=1280,
        )

        self.assertEqual(endpoint["mtu"], 1280)
        self.assertEqual(endpoint["private_key"], "kept-in-memory-only")


class OwnedAwgCoreInteropContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module("remote_run_owned_awg_core_interop")

    def test_interop_failure_classification_keeps_network_boundaries_distinct(
        self,
    ) -> None:
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

    def test_secret_free_interop_result_can_be_retained_without_shell_redirect(
        self,
    ) -> None:
        module = self.module
        result = {
            "schema_version": "pokrov-owned-awg-core-interop-v1",
            "profile": "awg2_lab",
            "outcome": "failed_no_outer_response",
            "raw_material_returned": False,
        }
        with tempfile.TemporaryDirectory() as raw_temp:
            output = Path(raw_temp) / "nested" / "interop.json"
            stream = io.StringIO()
            with patch("sys.stdout", stream):
                module._emit_result(result, str(output))

            retained = output.read_text(encoding="utf-8")

        self.assertTrue(retained.endswith("\n"))
        self.assertIn('"raw_material_returned": false', retained)
        self.assertEqual(stream.getvalue().strip(), retained.strip())

    def test_ru_pi_remote_root_is_narrow_and_randomized(self) -> None:
        module = self.module
        first = module._remote_root()
        second = module._remote_root()

        self.assertRegex(first, module._REMOTE_ROOT_PATTERN)
        self.assertRegex(second, module._REMOTE_ROOT_PATTERN)
        self.assertNotEqual(first, second)
        for unsafe in ("/tmp", "/", "/tmp/pokrov-awg-ru-pi-", "/var/tmp/test"):
            self.assertIsNone(module._REMOTE_ROOT_PATTERN.fullmatch(unsafe))

    def test_ru_pi_preflight_requires_pi4_arm64_and_direct_default_route(self) -> None:
        module = self.module
        preflight = module._RU_PI_PREFLIGHT

        self.assertIn('"$(uname -m)" = "aarch64"', preflight)
        self.assertIn('"Raspberry Pi 4"', preflight)
        self.assertIn("ip route show default", preflight)
        for tunneled_default in (" dev tun", " dev wg", " dev awg", " dev warp", " dev tailscale"):
            self.assertIn(tunneled_default, preflight)
        self.assertNotRegex(preflight, r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

    def test_ru_pi_ssh_boundary_rejects_unsafe_alias(self) -> None:
        module = self.module
        with tempfile.TemporaryDirectory() as raw_temp:
            root = Path(raw_temp)
            config = root / "config"
            known_hosts = root / "known_hosts"
            config.write_text("Host owned-pi\n", encoding="utf-8")
            known_hosts.write_text("safe-placeholder\n", encoding="utf-8")

            command = module._ssh_base("owned-pi", config, known_hosts)
            self.assertEqual(command[-1], "owned-pi")
            self.assertIn("BatchMode=yes", command)
            self.assertIn("StrictHostKeyChecking=yes", command)
            with self.assertRaisesRegex(RuntimeError, "alias"):
                module._ssh_base("owned-pi; whoami", config, known_hosts)


class OwnedAwgDeviceEvidenceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bind_module = _load_module("remote_bind_owned_awg_lab_device")
        cls.select_module = _load_module("remote_select_owned_awg_lab")

    def test_bind_result_is_atomically_retained_without_raw_device_identity(
        self,
    ) -> None:
        result = {
            "schema_version": "pokrov-owned-awg-device-bind-v1",
            "mode": "PLAN",
            "device_label_sha256": "a" * 64,
            "raw_identifiers_returned": False,
        }
        with tempfile.TemporaryDirectory() as raw_temp:
            output = Path(raw_temp) / "nested" / "bind.json"
            stream = io.StringIO()
            with patch("sys.stdout", stream):
                self.bind_module._emit_result(result, str(output))

            retained = output.read_text(encoding="utf-8")
            temporary_files = list(output.parent.glob(f".{output.name}.*.tmp"))

        self.assertTrue(retained.endswith("\n"))
        self.assertIn('"raw_identifiers_returned": false', retained)
        self.assertEqual(temporary_files, [])
        self.assertEqual(stream.getvalue().strip(), retained.strip())

    def test_bind_precondition_failures_are_structured_and_secret_free(self) -> None:
        helper = self.bind_module._REMOTE_HELPER

        self.assertIn("def blocked(reason, **safe_fields):", helper)
        self.assertIn('"raw_identifiers_returned": False', helper)
        self.assertIn('"device_candidate_unavailable"', helper)
        self.assertIn('"entitled_user_resolution"', helper)
        self.assertIn("_load_account_component_users", helper)
        self.assertIn("account_component_user_count", helper)
        self.assertIn("runtime_owner_entitled_user_count", helper)

    def test_bind_helper_uses_current_awg31_metadata(self) -> None:
        helper = self.bind_module._REMOTE_HELPER
        activation = _load_module("remote_activate_owned_awg_labs")

        self.assertIn(activation.AWG31_GENERATION, helper)
        self.assertIn(activation.AWG31_ENDPOINT_REVISION, helper)
        self.assertIn(activation.AWG31_SERVER_RECORD, helper)
        self.assertNotIn("awg31-lab-v3-randomized-trailers", helper)
        self.assertNotIn("de-awg31-20260828-03-randomized-trailers", helper)
        self.assertIn('"runtime_admin_owner_fallback"', helper)
        self.assertIn(
            '(target_selection_mode == "exact_local_install" or len(candidates) == 1)',
            helper,
        )
        self.assertIn("len(global_install_users) == 1", helper)
        self.assertIn('"exact_install_device_resolution_ambiguous"', helper)
        self.assertIn("AccountDevice.install_id == exact_install_id", helper)
        self.assertIn("AccountDevice.install_id.isnot(None)", helper)
        self.assertIn('target_selection_mode = "confirmed_install_hash"', helper)
        self.assertIn('"confirmed_install_hash_resolution"', helper)
        self.assertIn('"target_install_confirmation_failed"', helper)
        self.assertIn("hmac.compare_digest", helper)
        self.assertIn("cleanup_tg_ids = {tg_id, int(target_user.tg_id)}", helper)
        self.assertIn("device_account_matches_global_install_user", helper)
        self.assertIn('"global_install_user_resolution_ambiguous"', helper)
        self.assertIn('"account_user_resolution_unavailable"', helper)
        self.assertIn('"account_component_entitled"', helper)
        self.assertIn('"entitled_user_install_ownership"', helper)
        self.assertIn('"exact_install_one_day_extension"', helper)
        self.assertIn('"user.extend"', helper)
        self.assertIn("entitlement_extension_applied", helper)
        self.assertIn('"device_target_identity_incomplete"', helper)
        self.assertIn('"owned_awg_source_material_unavailable"', helper)

    def test_selection_result_is_atomically_retained_without_raw_install_id(
        self,
    ) -> None:
        result = {
            "schema_version": "pokrov-owned-awg-lab-selection-v1",
            "mode": "PLAN",
            "profile": "awg2_lab",
            "install_id_sha256": "b" * 64,
            "raw_identifiers_returned": False,
        }
        with tempfile.TemporaryDirectory() as raw_temp:
            output = Path(raw_temp) / "nested" / "selection.json"
            stream = io.StringIO()
            with patch("sys.stdout", stream):
                self.select_module._emit_result(result, str(output))

            retained = output.read_text(encoding="utf-8")
            temporary_files = list(output.parent.glob(f".{output.name}.*.tmp"))

        self.assertTrue(retained.endswith("\n"))
        self.assertIn('"raw_identifiers_returned": false', retained)
        self.assertNotIn("raw-install-id", retained)
        self.assertEqual(temporary_files, [])
        self.assertEqual(stream.getvalue().strip(), retained.strip())


if __name__ == "__main__":
    unittest.main()

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "release_gate_check.py"
    spec = importlib.util.spec_from_file_location("release_gate_check", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReleaseGateCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_client_security_smoke_gate_is_included_in_default_gate_set(self) -> None:
        gates = self.module._default_gates()

        names = [name for name, _cmd, _cwd in gates]

        self.assertIn("Client security smoke", names)
        self.assertIn("Client Flutter tests", names)

    def test_client_preflight_gate_runs_before_default_client_checks(self) -> None:
        gates = self.module._default_gates()

        names = [name for name, _cmd, _cwd in gates]
        commands = {name: cmd for name, cmd, _cwd in gates}

        self.assertIn("Client preflight", names)
        self.assertLess(names.index("Client preflight"), names.index("Client security smoke"))
        self.assertLess(names.index("Client preflight"), names.index("Client Flutter tests"))
        self.assertEqual(
            commands["Client preflight"],
            [sys.executable, "scripts/run_client_release_gate.py", "preflight"],
        )

    def test_client_security_smoke_gate_is_included_in_quick_gate_set(self) -> None:
        gates = self.module._quick_gates()

        names = [name for name, _cmd, _cwd in gates]

        self.assertIn("Client security smoke", names)
        self.assertIn("Client portal Flutter tests", names)
        self.assertIn("Payment and marketing release honesty", names)
        self.assertIn("GitHub release tooling", names)

    def test_client_preflight_gate_runs_before_quick_client_checks(self) -> None:
        gates = self.module._quick_gates()

        names = [name for name, _cmd, _cwd in gates]
        commands = {name: cmd for name, cmd, _cwd in gates}

        self.assertIn("Client preflight", names)
        self.assertLess(names.index("Client preflight"), names.index("Client security smoke"))
        self.assertLess(names.index("Client preflight"), names.index("Client portal Flutter tests"))
        self.assertEqual(
            commands["Client preflight"],
            [sys.executable, "scripts/run_client_release_gate.py", "preflight"],
        )

    def test_release_pytest_matrix_includes_payment_and_marketing_release_honesty(self) -> None:
        args = list(self.module.RELEASE_PYTEST_ARGS)

        self.assertIn("tests/test_bot_paywall.py", args)
        self.assertIn("tests/test_marketing_release_readiness.py", args)

    def test_release_pytest_matrix_includes_smart_connect_and_rollout_contracts(self) -> None:
        args = list(self.module.RELEASE_PYTEST_ARGS)

        self.assertIn("tests/test_smart_connect_api.py", args)
        self.assertIn("tests/test_network_rollout_api.py", args)

    def test_release_pytest_matrix_includes_client_and_runtime_smoke_policy_tests(self) -> None:
        args = list(self.module.RELEASE_PYTEST_ARGS)

        self.assertIn("tests/test_client_security_smoke.py", args)
        self.assertIn("tests/test_smoke_client_apps.py", args)
        self.assertIn("tests/test_brain_runtime_app_download_smoke.py", args)

    def test_release_pytest_matrix_includes_github_release_tooling_tests(self) -> None:
        args = list(self.module.RELEASE_PYTEST_ARGS)

        self.assertIn("tests/test_prepare_github_release_plan.py", args)
        self.assertIn("tests/test_publish_github_release_assets.py", args)
        self.assertIn("tests/test_paid_checkout_launch_evidence_check.py", args)
        self.assertIn("tests/test_live_probe_scripts.py", args)
        self.assertIn("tests/test_public_beta_post_deploy_probe.py", args)
        self.assertIn("tests/test_freekassa_api_probe.py", args)
        self.assertIn("tests/test_freekassa_staging_smoke.py", args)
        self.assertIn("tests/test_public_beta_external_access_preflight.py", args)
        self.assertIn("tests/test_validate_android_physical_audit_evidence.py", args)
        self.assertIn("tests/test_public_beta_launch_decision.py", args)

    def test_quick_gate_includes_github_release_tooling_tests(self) -> None:
        gates = self.module._quick_gates()

        commands = {name: cmd for name, cmd, _cwd in gates}

        self.assertIn("tests/test_prepare_github_release_plan.py", commands["GitHub release tooling"])
        self.assertIn("tests/test_publish_github_release_assets.py", commands["GitHub release tooling"])

    def test_quick_gate_includes_paid_checkout_launch_evidence_tooling_tests(self) -> None:
        gates = self.module._quick_gates()

        commands = {name: cmd for name, cmd, _cwd in gates}

        self.assertIn("tests/test_paid_checkout_launch_evidence_check.py", commands["Paid checkout launch evidence tooling"])
        self.assertIn("tests/test_live_probe_scripts.py", commands["Paid checkout launch evidence tooling"])
        self.assertIn("tests/test_public_beta_post_deploy_probe.py", commands["Paid checkout launch evidence tooling"])
        self.assertIn("tests/test_freekassa_api_probe.py", commands["Paid checkout launch evidence tooling"])
        self.assertIn("tests/test_freekassa_staging_smoke.py", commands["Paid checkout launch evidence tooling"])

    def test_quick_gate_includes_external_access_preflight_tooling_tests(self) -> None:
        gates = self.module._quick_gates()

        commands = {name: cmd for name, cmd, _cwd in gates}

        self.assertIn("External access preflight tooling", commands)
        self.assertIn("tests/test_public_beta_external_access_preflight.py", commands["External access preflight tooling"])
        self.assertIn("tests/test_public_beta_launch_decision.py", commands["External access preflight tooling"])

    def test_brain_ip_adds_runtime_static_verify_and_node_readiness_gates(self) -> None:
        gates = self.module._brain_origin_gates(
            brain_ip="82.21.114.104",
            web_domain="pokrov.space",
            api_domain="api.pokrov.space",
            connect_domain="connect.pokrov.space",
            ssh_user="root",
            ssh_port=29374,
            passwords="C:/tmp/PASSWORDS.txt",
        )

        names = [name for name, _cmd, _cwd in gates]
        commands = [" ".join(cmd) for _name, cmd, _cwd in gates]

        self.assertEqual(names[0], "Brain-origin runtime/static verify")
        self.assertEqual(names[1], "Node predeploy readiness")
        self.assertIn("scripts/verify_brain_ready.py", commands[0])
        self.assertIn("scripts/predeploy_node_readiness.py", commands[1])

    def test_brain_evidence_classification_fails_when_runtime_static_verify_fails(self) -> None:
        results = [
            self.module.GateResult("Brain-origin runtime/static verify", "verify", 2, 0.1, "legacy_static_present"),
            self.module.GateResult("Node predeploy readiness", "nodes", 0, 0.1, "ok"),
            self.module.GateResult("Critical worker regression", "pytest", 0, 0.1, "ok"),
        ]
        context = self.module.ReportContext(
            quick=True,
            brain_ip="82.21.114.104",
            client_platform_gates=[],
            runtime_smoke_requested=False,
            android_audit_requested=False,
            android_audit_required=False,
        )

        lines = "\n".join(self.module._render_evidence_classification(results, context))

        self.assertIn("| brain-origin check |", lines)
        self.assertIn("| current-origin check | local quick gate set | PASS |", lines)
        self.assertIn("| brain-origin check | `scripts/verify_brain_ready.py` plus node predeploy readiness | FAIL |", lines)

    def test_ru_origin_skip_evidence_marks_release_gate_as_operator_skipped(self) -> None:
        skip_file = self.module.REPO_ROOT / "docs" / "audit-artifacts" / "ru-origin-skip-accepted-2026-05-08.md"

        self.assertEqual(self.module._ru_origin_status(skip_file), "SKIPPED_BY_OPERATOR")

    def test_ru_origin_missing_skip_evidence_stays_blocked_by_access(self) -> None:
        skip_file = self.module.REPO_ROOT / "docs" / "audit-artifacts" / "missing-ru-origin-skip.md"

        self.assertEqual(self.module._ru_origin_status(skip_file), "BLOCKED_BY_ACCESS")

    def test_requested_client_platform_gates_are_appended(self) -> None:
        gates = self.module._default_gates(
            client_platform_gates=["windows", "android-apk"],
        )

        names = [name for name, _cmd, _cwd in gates]

        self.assertIn("Client Windows release build", names)
        self.assertIn("Client Android APK build", names)

    def test_android_localhost_audit_gate_is_opt_in(self) -> None:
        with patch.dict(self.module.os.environ, {}, clear=True):
            gate = self.module._optional_android_localhost_audit_gate()

        self.assertIsNone(gate)

    def test_android_localhost_audit_gate_uses_configured_serial(self) -> None:
        env = {
            "ANDROID_AUDIT_SERIAL": "emulator-5554",
            "ANDROID_AUDIT_RELEASE_EVIDENCE": "apk sha256 abc123",
        }
        with patch.dict(self.module.os.environ, env, clear=True):
            name, cmd, cwd = self.module._optional_android_localhost_audit_gate()

        self.assertEqual(name, "Android localhost audit")
        self.assertEqual(cmd[:3], [sys.executable, "scripts/android_localhost_audit.py", "--serial"])
        self.assertIn("emulator-5554", cmd)
        self.assertIn("--package", cmd)
        self.assertIn("space.pokrov.pokrov_android_shell", cmd)
        self.assertIn("--release-evidence", cmd)
        self.assertIn("apk sha256 abc123", cmd)
        self.assertIn("--require-release-build", cmd)
        self.assertEqual(cwd, self.module.REPO_ROOT)

    def test_android_localhost_audit_gate_uses_configured_package(self) -> None:
        env = {
            "ANDROID_AUDIT_SERIAL": "R58N12345AB",
            "ANDROID_AUDIT_PACKAGE": "space.pokrov.custom",
            "ANDROID_AUDIT_RELEASE_EVIDENCE": "apk sha256 abc123",
        }
        with patch.dict(self.module.os.environ, env, clear=True):
            _name, cmd, _cwd = self.module._optional_android_localhost_audit_gate()

        package_index = cmd.index("--package") + 1
        self.assertEqual(cmd[package_index], "space.pokrov.custom")

    def test_required_android_localhost_audit_gate_requires_serial(self) -> None:
        with patch.dict(self.module.os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "ANDROID_AUDIT_SERIAL"):
                self.module._required_android_localhost_audit_gate()

    def test_required_android_audit_gate_accepts_retained_evidence_json_for_validation(self) -> None:
        env = {
            "ANDROID_AUDIT_EVIDENCE_JSON": "docs/audit-artifacts/android-localhost-audit-physical.json",
            "ANDROID_AUDIT_VALIDATION_OUTPUT": "docs/audit-artifacts/android-validation.json",
        }
        with patch.dict(self.module.os.environ, env, clear=True):
            name, cmd, cwd = self.module._required_android_localhost_audit_gate()

        self.assertEqual(name, "Android physical audit evidence validation")
        self.assertIn("scripts/validate_android_physical_audit_evidence.py", cmd)
        self.assertIn("docs/audit-artifacts/android-localhost-audit-physical.json", cmd)
        self.assertIn("--output", cmd)
        self.assertIn("docs/audit-artifacts/android-validation.json", cmd)
        self.assertEqual(cwd, self.module.REPO_ROOT)

    def test_required_android_localhost_audit_gate_rejects_emulator_serial(self) -> None:
        with patch.dict(self.module.os.environ, {"ANDROID_AUDIT_SERIAL": "emulator-5554"}, clear=True):
            with self.assertRaisesRegex(ValueError, "physical hardware"):
                self.module._required_android_localhost_audit_gate()

    def test_required_android_localhost_audit_gate_requires_release_evidence(self) -> None:
        with patch.dict(self.module.os.environ, {"ANDROID_AUDIT_SERIAL": "R58N12345AB"}, clear=True):
            with self.assertRaisesRegex(ValueError, "ANDROID_AUDIT_RELEASE_EVIDENCE"):
                self.module._required_android_localhost_audit_gate()

    def test_required_android_localhost_audit_gate_accepts_physical_serial(self) -> None:
        env = {
            "ANDROID_AUDIT_SERIAL": "R58N12345AB",
            "ANDROID_AUDIT_RELEASE_EVIDENCE": "apk sha256 abc123",
        }
        with patch.dict(self.module.os.environ, env, clear=True):
            name, cmd, cwd = self.module._required_android_localhost_audit_gate()

        self.assertEqual(name, "Android localhost audit")
        self.assertIn("R58N12345AB", cmd)
        self.assertIn("--require-release-build", cmd)
        self.assertEqual(cwd, self.module.REPO_ROOT)

    def test_select_android_localhost_audit_gate_is_optional_without_android_builds(self) -> None:
        with patch.dict(self.module.os.environ, {}, clear=True):
            gate = self.module._select_android_localhost_audit_gate(
                client_platform_gates=["windows"],
            )

        self.assertIsNone(gate)

    def test_parse_client_platform_gates_uses_cli_or_env(self) -> None:
        with patch.dict(self.module.os.environ, {"CLIENT_PLATFORM_GATES": "windows,android-aab"}, clear=True):
            self.assertEqual(
                self.module._parse_client_platform_gates(""),
                ["windows", "android-aab"],
            )

        self.assertEqual(
            self.module._parse_client_platform_gates("android-apk"),
            ["android-apk"],
        )

    def test_runtime_smoke_gate_uses_redacting_wrapper(self) -> None:
        with patch.dict(self.module.os.environ, {"TELEGRAM_INIT_DATA": "query_id=AAA&hash=secret"}, clear=True):
            name, cmd, cwd = self.module._optional_runtime_smoke_gate()

        self.assertEqual(name, "Client apps runtime smoke")
        self.assertIn("scripts/runtime_app_download_smoke.py", cmd)
        self.assertIn("--redact", cmd)
        self.assertNotIn("scripts/smoke_client_apps.py", cmd)
        self.assertEqual(cwd, self.module.REPO_ROOT)

    def test_redact_text_covers_telegram_init_data_and_query_fields(self) -> None:
        raw = (
            "python scripts/smoke_client_apps.py --init-data query_id=AAH&user=%7B%22id%22%3A1%7D"
            "&auth_date=1710000000&hash=supersecret "
            "--init-data=query_id=DDD&signature=sig&chat_instance=chat&hash=equalform "
            "--passwords C:/secret dir/PASSWORDS.txt "
            "TELEGRAM_INIT_DATA=query_id=BBB&hash=hidden "
            "X-Telegram-Init-Data: query_id=CCC&user={id:2}&signature=abc&chat_instance=123&hash=def"
        )

        redacted = self.module._redact_text(raw)

        self.assertNotIn("supersecret", redacted)
        self.assertNotIn("hidden", redacted)
        self.assertNotIn("equalform", redacted)
        self.assertNotIn("PASSWORDS.txt", redacted)
        self.assertNotIn("secret dir", redacted)
        self.assertNotIn("signature=sig", redacted)
        self.assertNotIn("chat_instance=chat", redacted)
        self.assertNotIn("query_id=AAH", redacted)
        self.assertNotIn("query_id=BBB", redacted)
        self.assertNotIn("query_id=CCC", redacted)
        self.assertNotIn("query_id=DDD", redacted)
        self.assertIn("--init-data <redacted>", redacted)
        self.assertIn("TELEGRAM_INIT_DATA=<redacted>", redacted)
        self.assertIn("X-Telegram-Init-Data: <redacted>", redacted)

    def test_build_in_place_env_skips_frontend_temp_copy(self) -> None:
        class _Completed:
            returncode = 0
            stdout = "ok"

        webapp_dir = self.module.REPO_ROOT / "webapp"
        command = [self.module._npm_exec(), "run", "build"]
        with patch.dict(self.module.os.environ, {"RELEASE_GATE_BUILD_IN_PLACE": "1"}, clear=True):
            with patch.object(self.module, "_prepare_frontend_build_copy", side_effect=AssertionError("copy disabled")):
                with patch.object(self.module.subprocess, "run", return_value=_Completed()) as run:
                    result = self.module._run_cmd(name="WebApp production build", command=command, cwd=webapp_dir)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(run.call_args.kwargs["cwd"], str(webapp_dir))


if __name__ == "__main__":
    unittest.main()

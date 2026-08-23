import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
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
        self.assertIn("Client release-handoff v2 contract", names)

    def test_platform_release_v2_workflow_is_strict_and_cross_repository(self) -> None:
        workflow = (self.module.REPO_ROOT / ".github" / "workflows" / "release-v2-contract.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("repository: Kiwunaka/POKROV-app", workflow)
        self.assertIn("repository: Kiwunaka/pokrov-core", workflow)
        self.assertIn("ref: main", workflow)
        self.assertIn("run_client_release_gate.py contract", workflow)
        self.assertIn("--client-root", workflow)
        self.assertIn("--core-root", workflow)
        self.assertNotIn("allow-missing-client-root", workflow)
        self.assertNotIn("release_orchestrator.py", workflow)

    def test_weekly_release_snapshot_uses_strict_multi_repo_gate(self) -> None:
        workflow = (
            self.module.REPO_ROOT / ".github" / "workflows" / "weekly-release-gate-snapshot.yml"
        ).read_text(encoding="utf-8-sig")

        self.assertIn("repository: Kiwunaka/POKROV-app", workflow)
        self.assertIn("repository: Kiwunaka/pokrov-core", workflow)
        self.assertIn("POKROV_CORE_ROOT:", workflow)
        self.assertIn("release_gate_check.py --quick", workflow)
        self.assertNotIn("allow-missing-client-root", workflow)

    def test_guardrails_runs_both_critical_playwright_frontends(self) -> None:
        workflow = (
            self.module.REPO_ROOT / ".github" / "workflows" / "guardrails.yml"
        ).read_text(encoding="utf-8")
        quick_gate_names = [name for name, _cmd, _cwd in self.module._quick_gates()]

        self.assertIn("cd webapp", workflow)
        self.assertIn("npx playwright install --with-deps chromium", workflow)
        self.assertIn("cd adminapp", workflow)
        self.assertIn("npx playwright install chromium", workflow)
        self.assertIn("npm run test:e2e", workflow)
        self.assertIn("WebApp Playwright E2E", quick_gate_names)

    def test_adminapp_isolated_build_includes_backend_contract_sources(self) -> None:
        support_paths = self.module._frontend_build_support_paths(self.module.REPO_ROOT / "adminapp")

        self.assertEqual(
            tuple(path.name for path in support_paths),
            ("scripts", "portal_bot"),
        )
        self.assertEqual(
            self.module._frontend_build_support_paths(self.module.REPO_ROOT / "webapp"),
            (),
        )

    def test_failure_tails_are_redacted_in_ci_output(self) -> None:
        result = self.module.GateResult(
            name="example",
            command="example",
            returncode=1,
            duration_sec=0.1,
            output_tail="Authorization: Bearer supersecret",
        )
        output = io.StringIO()

        with redirect_stdout(output):
            self.module._print_failure_tails([result])

        rendered = output.getvalue()
        self.assertIn("[failure-tail] example", rendered)
        self.assertNotIn("supersecret", rendered)
        self.assertIn("Bearer <redacted>", rendered)

    def test_client_root_resolver_selects_the_main_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp)
            platform_root = workspace_root / "VPN"
            client_repo = workspace_root / "POKROV-app"
            main_worktree = client_repo / ".worktrees" / "final-client-integration"
            (client_repo / ".git").mkdir(parents=True)
            git_results = (
                subprocess.CompletedProcess(args=[], returncode=0, stdout=f"{platform_root / '.git'}\n"),
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout=(
                        f"worktree {client_repo}\n"
                        "branch refs/heads/codex/client-work\n\n"
                        f"worktree {main_worktree}\n"
                        "branch refs/heads/main\n"
                    ),
                ),
            )
            with patch.dict(self.module.os.environ, {"POKROV_APP_ROOT": ""}, clear=False):
                with patch.object(self.module.subprocess, "run", side_effect=git_results):
                    resolved = self.module._resolve_client_root(platform_root / ".worktrees" / "integration")

        self.assertEqual(resolved, main_worktree.resolve())

    def test_account_foundation_is_in_release_pytest_matrix(self) -> None:
        self.assertIn("tests/test_account_foundation.py", self.module.RELEASE_PYTEST_ARGS)

    def test_account_foundation_compatibility_suites_are_in_release_pytest_matrix(self) -> None:
        for suite in (
            "tests/test_antiabuse_privacy.py",
            "tests/test_antiabuse_retention_script.py",
            "tests/test_sqlite_postgres_rehearsal.py",
            "tests/test_account_recovery.py",
            "tests/test_auth_sessions.py",
            "portal_bot/tests/test_app_first_service.py",
            "portal_bot/tests/test_email_auth.py",
            "tests/test_bot_paywall.py",
        ):
            with self.subTest(suite=suite):
                self.assertIn(suite, self.module.RELEASE_PYTEST_ARGS)

    def test_economy_bonus_referral_suites_are_in_release_pytest_matrix(self) -> None:
        for suite in (
            "portal_bot/tests/test_economy_bonus_referral_service.py",
            "portal_bot/tests/test_economy_trial_service.py",
            "portal_bot/tests/test_channel_bonus_service.py",
            "tests/test_api_payments_callbacks.py",
        ):
            with self.subTest(suite=suite):
                self.assertIn(suite, self.module.RELEASE_PYTEST_ARGS)

    def test_free_profile_suites_are_in_release_pytest_matrix(self) -> None:
        for suite in (
            "tests/test_free_soft_profile_contract.py",
            "tests/test_free_soft_profile_migrations.py",
            "tests/test_node_provisioning_service.py",
            "tests/test_panel_client_free_profiles.py",
            "tests/test_free_soft_inbound_shaper.py",
            "tests/test_free_cycle_service.py",
            "tests/test_key_pressure_scoring.py",
            "tests/test_admin_ops_api.py",
            "tests/test_plan_policies.py",
        ):
            with self.subTest(suite=suite):
                self.assertIn(suite, self.module.RELEASE_PYTEST_ARGS)

    def test_client_security_smoke_gate_is_included_in_quick_gate_set(self) -> None:
        gates = self.module._quick_gates()

        names = [name for name, _cmd, _cwd in gates]

        self.assertIn("Client security smoke", names)
        self.assertIn("Client portal Flutter tests", names)
        self.assertIn("Client release-handoff v2 contract", names)

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

    def test_missing_client_root_can_be_skipped_for_ci_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "POKROV-app" / "config" / "product-contract.seed.json"
            with patch.object(self.module, "CLIENT_ROOT_REQUIRED_PATHS", (missing,)):
                gates = [
                    self.module._client_release_v2_contract_gate(),
                    self.module._client_security_smoke_gate(),
                    self.module._client_flutter_test_gate(suite="portal"),
                    ("Public link checks", [sys.executable, "scripts/check-links.py"], self.module.REPO_ROOT),
                ]

                filtered = self.module._filter_client_gates_when_missing(
                    gates,
                    allow_missing_client_root=True,
                    client_platform_gates=[],
                )

        names = [name for name, _cmd, _cwd in filtered]
        self.assertNotIn("Client security smoke", names)
        self.assertNotIn("Client portal Flutter tests", names)
        self.assertNotIn("Client release-handoff v2 contract", names)
        self.assertIn("Public link checks", names)
        self.assertIn("Client workspace preflight (skipped)", names)

    def test_missing_client_root_stays_strict_for_platform_builds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "POKROV-app" / "config" / "product-contract.seed.json"
            with patch.object(self.module, "CLIENT_ROOT_REQUIRED_PATHS", (missing,)):
                gates = [self.module._client_security_smoke_gate()]

                filtered = self.module._filter_client_gates_when_missing(
                    gates,
                    allow_missing_client_root=True,
                    client_platform_gates=["windows"],
                )

        names = [name for name, _cmd, _cwd in filtered]
        self.assertEqual(names, ["Client security smoke"])

    def test_redact_text_covers_telegram_init_data_and_query_fields(self) -> None:
        raw = (
            "python scripts/smoke_client_apps.py --init-data query_id=AAH&user=%7B%22id%22%3A1%7D"
            "&auth_date=1710000000&hash=supersecret "
            "--init-data=query_id=DDD&signature=sig&chat_instance=chat&hash=equalform "
            "TELEGRAM_INIT_DATA=query_id=BBB&hash=hidden "
            "X-Telegram-Init-Data: query_id=CCC&user={id:2}&signature=abc&chat_instance=123&hash=def"
        )

        redacted = self.module._redact_text(raw)

        self.assertNotIn("supersecret", redacted)
        self.assertNotIn("hidden", redacted)
        self.assertNotIn("equalform", redacted)
        self.assertNotIn("signature=sig", redacted)
        self.assertNotIn("chat_instance=chat", redacted)
        self.assertNotIn("query_id=AAH", redacted)
        self.assertNotIn("query_id=BBB", redacted)
        self.assertNotIn("query_id=CCC", redacted)
        self.assertNotIn("query_id=DDD", redacted)
        self.assertIn("--init-data <redacted>", redacted)
        self.assertIn("TELEGRAM_INIT_DATA=<redacted>", redacted)
        self.assertIn("X-Telegram-Init-Data: <redacted>", redacted)


if __name__ == "__main__":
    unittest.main()

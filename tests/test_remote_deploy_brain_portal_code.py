import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_module():
    path = SCRIPTS_DIR / "remote_deploy_brain_portal_code.py"
    spec = importlib.util.spec_from_file_location("remote_deploy_brain_portal_code", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class RemoteDeployBrainPortalCodeTests(unittest.TestCase):
    def test_iter_upload_mappings_includes_shared_runtime_assets(self) -> None:
        module = _load_module()
        mappings = module.iter_upload_mappings(REPO_ROOT)
        targets = {target for _source, target in mappings}

        self.assertIn("/root/shared/product-facts.json", targets)
        self.assertIn("/root/shared/public-urls.json", targets)
        self.assertIn("/root/shared/design-tokens.json", targets)
        self.assertIn("/root/shared/support-ai-knowledge.json", targets)
        self.assertIn("/root/shared/support-agent-policy.json", targets)
        self.assertIn("/root/shared/contracts/observability/error-catalog.json", targets)
        self.assertIn("/root/copy/catalog.ru.json", targets)
        self.assertIn("/root/portal_bot/admin_v2/roles.py", targets)
        self.assertIn("/root/portal_bot/authenticated_egress_probe.py", targets)
        self.assertIn("/root/portal_bot/singbox_authenticated_egress_adapter.py", targets)
        self.assertIn("/root/portal_bot/emergency_linux_probe_adapter.py", targets)
        self.assertFalse(any(target.startswith("/root/portal_bot/tests/") for target in targets))

    def test_restart_default_includes_long_running_services(self) -> None:
        module = _load_module()
        self.assertIn("portal-feedbackbot", module.DEFAULT_RESTART_UNITS)
        self.assertIn("portal-worker", module.DEFAULT_RESTART_UNITS)

    def test_stage_targets_keep_sftp_uploads_out_of_live_paths(self) -> None:
        module = _load_module()
        stage_root = "/root/portal_bot.deploy-staging/20260705T010203Z-1"

        self.assertEqual(
            "/root/portal_bot.deploy-staging/20260705T010203Z-1/portal_bot/api.py",
            module._stage_target_for("/root/portal_bot/api.py", stage_root),
        )
        self.assertEqual(
            "/root/portal_bot.deploy-staging/20260705T010203Z-1/shared/product-facts.json",
            module._stage_target_for("/root/shared/product-facts.json", stage_root),
        )
        self.assertEqual(
            "/root/portal_bot.deploy-staging/20260705T010203Z-1/portal_bot/admin_v2/roles.py",
            module._stage_target_for("/root/portal_bot/admin_v2/roles.py", stage_root),
        )
        self.assertEqual(
            "/root/portal_bot.deploy-staging/20260705T010203Z-1/shared/contracts/observability/error-catalog.json",
            module._stage_target_for("/root/shared/contracts/observability/error-catalog.json", stage_root),
        )
        self.assertEqual(
            "/root/portal_bot.deploy-staging/20260705T010203Z-1/copy/catalog.ru.json",
            module._stage_target_for("/root/copy/catalog.ru.json", stage_root),
        )

    def test_restart_units_reject_shell_metacharacters(self) -> None:
        module = _load_module()

        self.assertEqual(["portal-api", "portal-bot.service"], module._parse_restart_units("portal-api,portal-bot.service"))
        with self.assertRaises(SystemExit):
            module._parse_restart_units("portal-api; systemctl stop x-ui")

    def test_command_builders_preflight_before_live_promotion_and_can_restore(self) -> None:
        module = _load_module()
        stage_root = "/root/portal_bot.deploy-staging/20260705T010203Z-1"
        backup_root = "/root/portal_bot.deploy-backups/20260705T010203Z-1"
        mappings = [(Path("api.py"), "/root/portal_bot/api.py"), (Path("product-facts.json"), "/root/shared/product-facts.json")]

        preflight = module._build_preflight_command(stage_root)
        import_preflight = module._build_stage_runtime_import_command(stage_root)
        promote = module._build_promote_command(mappings, stage_root)
        restore = module._build_restore_command([target for _source, target in mappings], backup_root)

        self.assertIn("compileall -q", preflight)
        self.assertIn("root.rglob", preflight)
        self.assertIn("*.json", preflight)
        self.assertIn("portal_shared_json_preflight.log", preflight)
        self.assertIn("admin_v2.roles", import_preflight)
        self.assertIn("operator_observability_service", import_preflight)
        self.assertIn("/root/portal_bot.deploy-staging/20260705T010203Z-1/portal_bot/api.py", promote)
        self.assertIn("install -D -m 0644", promote)
        self.assertIn("/root/portal_bot.deploy-backups/20260705T010203Z-1/root/portal_bot/api.py", restore)
        self.assertIn("rm -f /root/shared/product-facts.json", restore)

    def test_emergency_probe_adapter_is_promoted_and_restored_executable(self) -> None:
        module = _load_module()
        target = "/root/portal_bot/emergency_linux_probe_adapter.py"
        stage_root = "/root/portal_bot.deploy-staging/20260705T010203Z-1"
        backup_root = "/root/portal_bot.deploy-backups/20260705T010203Z-1"

        promote = module._build_promote_command([(Path("adapter.py"), target)], stage_root)
        restore = module._build_restore_command([target], backup_root)

        self.assertIn("install -D -m 0755", promote)
        self.assertIn("install -D -m 0755", restore)

    def test_backup_prune_is_bounded_to_timestamped_deploy_snapshots(self) -> None:
        module = _load_module()

        command = module._build_backup_prune_command(5)

        self.assertIn('root=/root/portal_bot.deploy-backups', command)
        self.assertIn('test "$root" = /root/portal_bot.deploy-backups', command)
        self.assertIn("^[0-9]{8}T[0-9]{6}Z-[0-9]+$", command)
        self.assertIn("head -n -5", command)
        self.assertIn('rm -rf -- "$root/$name"', command)
        with self.assertRaises(SystemExit):
            module._build_backup_prune_command(0)

    def test_prepare_and_delayed_health_checks_cover_nested_payload_and_crash_loops(self) -> None:
        module = _load_module()
        stage_root = "/root/portal_bot.deploy-staging/20260705T010203Z-1"
        backup_root = "/root/portal_bot.deploy-backups/20260705T010203Z-1"
        mappings = [
            (Path("roles.py"), "/root/portal_bot/admin_v2/roles.py"),
            (Path("error-catalog.json"), "/root/shared/contracts/observability/error-catalog.json"),
        ]

        prepare = module._build_prepare_command(mappings, stage_root, backup_root)
        verify = module._build_post_restart_verify_command(["portal-api", "portal-worker"])

        self.assertIn(f"{stage_root}/portal_bot/admin_v2", prepare)
        self.assertIn(f"{stage_root}/shared/contracts/observability", prepare)
        self.assertIn(f"sleep {module.POST_RESTART_SETTLE_SECONDS}", verify)
        self.assertIn("NRestarts", verify)
        self.assertIn("portal-api", verify)
        self.assertIn("portal-worker", verify)
        self.assertIn(module.POST_RESTART_HEALTH_URL, verify)
        self.assertEqual(
            "systemctl reset-failed portal-api && systemctl restart portal-api",
            module._build_clean_restart_command("portal-api"),
        )

    def test_main_fails_when_requested_unit_is_not_active_after_restart(self) -> None:
        module = _load_module()
        ssh = MagicMock()
        sftp = MagicMock()
        ssh.open_sftp.return_value = sftp
        run_results = [
            (0, "", ""),  # prepare dirs
            (0, "", ""),  # backup live files
            (0, "", ""),  # staged syntax/json preflight
            (0, "", ""),  # staged requirements preflight
            (0, "", ""),  # staged runtime import preflight
            (0, "", ""),  # live requirements install
            (0, "", ""),  # promote staged files
            (0, "", ""),  # restart command
            (1, "portal-feedbackbot state=activating restarts=2", ""),  # delayed verification
            (0, "", ""),  # rollback restore
            (0, "", ""),  # rollback restart
            (0, "portal-feedbackbot state=active restarts=0\napi_health=PASS\n", ""),
        ]

        with patch.object(module.argparse.ArgumentParser, "parse_args") as parse_args:
            parse_args.return_value = module.argparse.Namespace(
                brain_ip="82.21.114.104",
                ssh_user="root",
                ssh_port=29374,
                passwords="C:/tmp/PASSWORDS.txt",
                restart="portal-feedbackbot",
                backup_retain_count=5,
            )
            with patch.object(module, "connect_node", return_value=(ssh, "password")):
                with patch.object(module, "_release_id", return_value="20260705T010203Z-1"):
                    with patch.object(module, "_run", side_effect=run_results):
                        exit_code = module.main()

        uploaded_targets = [call.args[1] for call in sftp.put.call_args_list]
        self.assertTrue(uploaded_targets)
        self.assertTrue(all("/root/portal_bot.deploy-staging/20260705T010203Z-1/" in target for target in uploaded_targets))
        self.assertFalse(any(target.startswith("/root/portal_bot/") for target in uploaded_targets))
        self.assertEqual(exit_code, 1)
        ssh.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()

import argparse
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
    path = SCRIPTS_DIR / "remote_deploy_brain_awg_route_fix.py"
    spec = importlib.util.spec_from_file_location("remote_deploy_brain_awg_route_fix", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _args(module, *, apply: bool, confirm: str = "") -> argparse.Namespace:
    return argparse.Namespace(
        brain_ip=module.EXPECTED_BRAIN_IP,
        ssh_user="root",
        ssh_port=29374,
        passwords="C:/private/PASSWORDS.txt",
        json_out="",
        apply=apply,
        confirm=confirm,
        backup_retain_count=5,
    )


def _matched_row(module, *, relative: str | None = None) -> dict:
    return {
        "source_path": relative or module.TARGET_RELATIVE_PATH,
        "remote_target": module.TARGET_REMOTE_PATH,
        "raw_match": False,
        "crlf_normalized_match": True,
        "classification": "CRLF_ONLY_DIFFERENCE",
    }


class RemoteDeployBrainAwgRouteFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_reviewed_revisions_have_exactly_one_semantic_runtime_delta(self) -> None:
        module = self.module
        mappings = module._reviewed_upload_mappings(REPO_ROOT)
        live_payload = module._source_payload(REPO_ROOT, module.EXPECTED_LIVE_REVISION)
        candidate_payload = module._source_payload(REPO_ROOT, module.EXPECTED_CANDIDATE_REVISION)

        self.assertEqual(len(mappings), module.EXPECTED_PAYLOAD_COUNT)
        self.assertEqual(
            module._payload_mapping_sha256(mappings),
            module.EXPECTED_PAYLOAD_MAPPING_SHA256,
        )
        candidate_target = module._validate_static_scope(live_payload, candidate_payload)

        self.assertEqual(len(live_payload), module.EXPECTED_PAYLOAD_COUNT)
        self.assertEqual(module._sha256(candidate_target), module.EXPECTED_CANDIDATE_TARGET_SHA256)
        self.assertEqual(
            module._semantic_delta_targets(live_payload, candidate_payload),
            [module.TARGET_RELATIVE_PATH],
        )

    def test_reviewed_mapping_rejects_one_sided_revision_shape_drift(self) -> None:
        module = self.module
        source = REPO_ROOT / "portal_bot" / "future_runtime.py"

        with patch.object(
            module,
            "iter_upload_mappings",
            return_value=[(source, "/root/portal_bot/future_runtime.py")],
        ), patch.object(
            module,
            "_revision_paths",
            side_effect=[{"portal_bot/future_runtime.py"}, set()],
        ):
            with self.assertRaisesRegex(ValueError, "payload shapes differ"):
                module._reviewed_upload_mappings(REPO_ROOT)

    def test_apply_requires_exact_confirmation_and_canonical_brain(self) -> None:
        module = self.module
        with self.assertRaisesRegex(ValueError, "--apply requires"):
            module._validate_apply_confirmation(_args(module, apply=True))

        args = _args(module, apply=True, confirm=module.APPLY_CONFIRMATION)
        args.brain_ip = "127.0.0.1"
        with self.assertRaisesRegex(ValueError, "canonical Brain"):
            module._validate_apply_confirmation(args)

        module._validate_apply_confirmation(
            _args(module, apply=True, confirm=module.APPLY_CONFIRMATION)
        )

    def test_target_preflight_compiles_only_staged_route_file(self) -> None:
        module = self.module
        command = module._build_target_preflight_command("/root/stage/one")
        promote = module._build_guarded_promote_command("/root/stage/one")

        self.assertIn("-m py_compile", command)
        self.assertIn("/root/stage/one/portal_bot/api_client_routes.py", command)
        self.assertNotIn("compileall", command)
        self.assertIn(module.EXPECTED_LIVE_TARGET_SHA256, promote)
        self.assertIn("install -D -m 0644", promote)
        self.assertIn(module.TARGET_REMOTE_PATH, promote)

    def test_plan_audits_live_baseline_without_remote_mutation(self) -> None:
        module = self.module
        ssh = MagicMock()
        sftp = MagicMock()
        ssh.open_sftp.return_value = sftp
        live_payload = [(module.TARGET_RELATIVE_PATH, module.TARGET_REMOTE_PATH, b"old\n")]
        candidate_payload = [(module.TARGET_RELATIVE_PATH, module.TARGET_REMOTE_PATH, b"new\n")]

        parser = MagicMock()
        parser.parse_args.return_value = _args(module, apply=False)
        with patch.object(module, "_parser", return_value=parser), patch.object(
            module, "_source_payload", side_effect=[live_payload, candidate_payload]
        ), patch.object(module, "_validate_static_scope", return_value=b"new\n"), patch.object(
            module, "_build_backup_prune_command", return_value="prune"
        ), patch.object(module, "connect_node", return_value=(ssh, "key:test")), patch.object(
            module, "_audit_payload", return_value=[_matched_row(module)]
        ), patch.object(module, "_run_checked") as run_checked:
            result = module.main()

        self.assertEqual(result, 0)
        run_checked.assert_not_called()
        ssh.close.assert_called_once()

    def test_predeploy_drift_fails_before_any_mutation(self) -> None:
        module = self.module
        ssh = MagicMock()
        ssh.open_sftp.return_value = MagicMock()
        live_payload = [(module.TARGET_RELATIVE_PATH, module.TARGET_REMOTE_PATH, b"old\n")]
        candidate_payload = [(module.TARGET_RELATIVE_PATH, module.TARGET_REMOTE_PATH, b"new\n")]
        mismatch = _matched_row(module)
        mismatch["crlf_normalized_match"] = False
        mismatch["classification"] = "CONTENT_MISMATCH"

        parser = MagicMock()
        parser.parse_args.return_value = _args(
            module,
            apply=True,
            confirm=module.APPLY_CONFIRMATION,
        )
        with patch.object(module, "_parser", return_value=parser), patch.object(
            module, "_source_payload", side_effect=[live_payload, candidate_payload]
        ), patch.object(module, "_validate_static_scope", return_value=b"new\n"), patch.object(
            module, "_build_backup_prune_command", return_value="prune"
        ), patch.object(module, "connect_node", return_value=(ssh, "key:test")), patch.object(
            module, "_audit_payload", return_value=[mismatch]
        ), patch.object(module, "_run_checked") as run_checked:
            result = module.main()

        self.assertEqual(result, 1)
        run_checked.assert_not_called()
        ssh.close.assert_called_once()

    def test_apply_promotes_one_file_restarts_one_unit_and_requires_full_readback(self) -> None:
        module = self.module
        ssh = MagicMock()
        sftp = MagicMock()
        staged_file = MagicMock()
        sftp.open.return_value.__enter__.return_value = staged_file
        ssh.open_sftp.return_value = sftp
        live_payload = [(module.TARGET_RELATIVE_PATH, module.TARGET_REMOTE_PATH, b"old\n")]
        candidate_payload = [(module.TARGET_RELATIVE_PATH, module.TARGET_REMOTE_PATH, b"new\n")]

        parser = MagicMock()
        parser.parse_args.return_value = _args(
            module,
            apply=True,
            confirm=module.APPLY_CONFIRMATION,
        )
        with patch.object(module, "_parser", return_value=parser), patch.object(
            module, "_source_payload", side_effect=[live_payload, candidate_payload]
        ), patch.object(module, "_validate_static_scope", return_value=b"new\n"), patch.object(
            module, "connect_node", return_value=(ssh, "key:test")
        ), patch.object(
            module,
            "_audit_payload",
            side_effect=[
                [_matched_row(module)],
                [_matched_row(module)],
                [_matched_row(module)],
            ],
        ) as audit_payload, patch.object(
            module, "_run_checked", return_value=True
        ) as run_checked, patch.object(
            module, "_run"
        ), patch.object(
            module, "_release_id", return_value="20260828T120000Z-1"
        ):
            result = module.main()

        self.assertEqual(result, 0)
        self.assertEqual(audit_payload.call_count, 3)
        staged_file.write.assert_called_once_with(b"new\n")
        commands = [call.args[1] for call in run_checked.call_args_list]
        self.assertTrue(any("install -D -m 0644" in command for command in commands))
        self.assertTrue(any("systemctl restart portal-api" in command for command in commands))
        self.assertFalse(any("portal-bot" in command for command in commands))
        self.assertFalse(any("portal-worker" in command for command in commands))
        ssh.close.assert_called_once()

    def test_failed_candidate_readback_invokes_baseline_restore(self) -> None:
        module = self.module
        ssh = MagicMock()
        sftp = MagicMock()
        sftp.open.return_value.__enter__.return_value = MagicMock()
        ssh.open_sftp.return_value = sftp
        live_payload = [(module.TARGET_RELATIVE_PATH, module.TARGET_REMOTE_PATH, b"old\n")]
        candidate_payload = [(module.TARGET_RELATIVE_PATH, module.TARGET_REMOTE_PATH, b"new\n")]
        mismatch = _matched_row(module)
        mismatch["crlf_normalized_match"] = False
        mismatch["classification"] = "CONTENT_MISMATCH"

        parser = MagicMock()
        parser.parse_args.return_value = _args(
            module,
            apply=True,
            confirm=module.APPLY_CONFIRMATION,
        )
        with patch.object(module, "_parser", return_value=parser), patch.object(
            module, "_source_payload", side_effect=[live_payload, candidate_payload]
        ), patch.object(module, "_validate_static_scope", return_value=b"new\n"), patch.object(
            module, "connect_node", return_value=(ssh, "key:test")
        ), patch.object(
            module,
            "_audit_payload",
            side_effect=[[_matched_row(module)], [_matched_row(module)], [mismatch]],
        ), patch.object(module, "_run_checked", return_value=True), patch.object(
            module, "_restore_and_audit", return_value=True
        ) as restore, patch.object(
            module, "_release_id", return_value="20260828T120000Z-2"
        ):
            result = module.main()

        self.assertEqual(result, 1)
        restore.assert_called_once()
        self.assertEqual(restore.call_args.kwargs["live_payload"], live_payload)


if __name__ == "__main__":
    unittest.main()

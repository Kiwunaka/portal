from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/validate_release_1_2_hosted_gate_contract.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_release_1_2_hosted_gate_contract", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class HostedGateContractTest(unittest.TestCase):
    def test_github_head_ref_wins_over_detached_checkout(self) -> None:
        with mock.patch.dict(
            "os.environ",
            {"POKROV_RELEASE_HEAD_REF": "codex/1.2.0-hosted-gate-control"},
        ):
            self.assertEqual(
                MODULE._current_branch(ROOT),
                "codex/1.2.0-hosted-gate-control",
            )

    def test_contract_and_workflow_are_self_consistent(self) -> None:
        contract = MODULE._read_object(ROOT / MODULE.CONTRACT_PATH)

        self.assertEqual(
            MODULE._validate_contract_data(ROOT, contract), MODULE.EXPECTED_REVISIONS
        )

    def test_diff_policy_requires_exact_non_ui_paths(self) -> None:
        allowed = [".github/workflows/gate.yml", "tests/test_gate.py"]
        prefixes = ["adminapp/", "marketing/src/", "webapp/"]

        self.assertEqual(MODULE._diff_policy_errors(allowed, allowed, prefixes), [])
        self.assertEqual(
            MODULE._diff_policy_errors(
                [*allowed, "adminapp/src/page.tsx"], allowed, prefixes
            ),
            ["isolated_diff_paths", "visible_ui:adminapp/src/page.tsx"],
        )

    def test_github_output_contains_only_exact_public_commit_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "github-output"
            MODULE._emit_github_outputs(path, MODULE.EXPECTED_REVISIONS)

            self.assertEqual(
                path.read_text(encoding="utf-8").splitlines(),
                [
                    f"platform_revision={MODULE.EXPECTED_REVISIONS['platform']}",
                    f"client_revision={MODULE.EXPECTED_REVISIONS['client']}",
                    f"core_revision={MODULE.EXPECTED_REVISIONS['core']}",
                ],
            )

    def test_workflow_rejects_mutating_command(self) -> None:
        source = (ROOT / MODULE.WORKFLOW_PATH).read_text(encoding="utf-8")

        self.assertIn(
            "workflow_forbidden:git push",
            MODULE._workflow_contract_errors(source + "\ngit push\n"),
        )

    def test_runner_cleanup_is_limited_to_verified_client_artifacts(self) -> None:
        source = (ROOT / MODULE.WORKFLOW_PATH).read_text(encoding="utf-8")

        self.assertIn('[IO.Path]::Combine($clientRoot, "artifacts")', source)
        self.assertIn(
            '[IO.Path]::Combine($clientRoot, ".git", "lfs", "objects")', source
        )
        self.assertIn("$resolvedTarget.StartsWith(", source)
        self.assertIn(
            "Remove-Item -LiteralPath $resolvedTarget -Recurse -Force", source
        )


if __name__ == "__main__":
    unittest.main()

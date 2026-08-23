from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/validate_release_1_2_pr00.py"
SPEC = importlib.util.spec_from_file_location("validate_release_1_2_pr00", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ReleasePr00Test(unittest.TestCase):
    def test_github_head_ref_wins_over_detached_checkout(self) -> None:
        with mock.patch.dict(
            "os.environ", {"POKROV_RELEASE_HEAD_REF": "codex/1.2.0-pr00-true"}
        ):
            self.assertEqual(MODULE._current_branch(ROOT), "codex/1.2.0-pr00-true")

    def test_contract_and_snapshots_are_self_consistent(self) -> None:
        contract = MODULE._read_object(ROOT / MODULE.CONTRACT_PATH)

        self.assertEqual(MODULE._validate_contract_data(ROOT, contract), 4)

    def test_diff_policy_requires_exact_paths_and_rejects_ui(self) -> None:
        allowed = ["docs/freeze.json", "scripts/validate.py"]
        prefixes = ["adminapp/", "marketing/src/", "webapp/"]

        self.assertEqual(MODULE._diff_policy_errors(allowed, allowed, prefixes), [])
        self.assertEqual(
            MODULE._diff_policy_errors(
                [*allowed, "webapp/src/app/page.tsx"], allowed, prefixes
            ),
            ["isolated_diff_paths", "visible_ui:webapp/src/app/page.tsx"],
        )
        self.assertEqual(
            MODULE._diff_policy_errors(allowed[:-1], allowed, prefixes),
            ["isolated_diff_paths"],
        )

    def test_motion_snapshot_rejects_incomplete_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "motion.dart"
            path.write_text(
                "abstract final class PokrovMotionTokens {}\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "motion_semantics"):
                MODULE._validate_snapshot_semantics("motion_semantics", path)


if __name__ == "__main__":
    unittest.main()

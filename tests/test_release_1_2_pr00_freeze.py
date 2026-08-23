from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/validate_release_1_2_pr00_freeze.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_release_1_2_pr00_freeze", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_isolated_diff_policy_accepts_only_exact_non_ui_paths() -> None:
    allowed = ["docs/evidence.json", "scripts/validate.py", "tests/test_validate.py"]
    prefixes = ["adminapp/", "marketing/src/", "webapp/"]

    assert MODULE._diff_policy_errors(allowed, allowed, prefixes) == []
    assert MODULE._diff_policy_errors(
        [*allowed, "webapp/app/page.tsx"], allowed, prefixes
    ) == ["isolated_diff_paths", "visible_ui:webapp/app/page.tsx"]
    assert MODULE._diff_policy_errors(allowed[:-1], allowed, prefixes) == [
        "isolated_diff_paths"
    ]


def test_source_plan_acceptance_set_is_exact() -> None:
    assert MODULE.EXPECTED_ACCEPTANCE == {
        "release_branches",
        "baseline_shas",
        "flags",
        "manifest_schema",
        "product_facts_snapshot",
        "reason_code_draft",
        "motion_semantics",
        "no_visible_ui_change",
    }

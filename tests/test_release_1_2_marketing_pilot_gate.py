from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "release_1_2_marketing_pilot_gate.py"
SPEC = importlib.util.spec_from_file_location("release_1_2_marketing_pilot_gate", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_gate_stops_and_retains_not_run_status(tmp_path: Path) -> None:
    steps = [
        MODULE.GateStep("a", "unit", ("a",), tmp_path),
        MODULE.GateStep("b", "unit", ("b",), tmp_path),
        MODULE.GateStep("c", "unit", ("c",), tmp_path),
    ]
    codes = iter((0, 1))

    def runner(*_args, **_kwargs):
        return subprocess.CompletedProcess([], next(codes))

    results = MODULE.run_gate(steps=steps, keep_going=False, runner=runner)
    assert [row.status for row in results] == ["PASS", "FAIL", "NOT_RUN"]


def test_manual_lanes_never_claim_external_pass() -> None:
    lanes = MODULE.manual_lanes()
    assert lanes
    assert all(row["status"] != "PASS" for row in lanes)
    assert all(row["required_for_external_pilot"] is True for row in lanes)


def test_gate_includes_every_owned_surface_and_decision_lane(tmp_path: Path) -> None:
    steps = MODULE.build_steps(platform_root=tmp_path / "platform", client_root=tmp_path / "client")
    ids = {row.id for row in steps}
    assert {
        "marketing-governance-scan",
        "winback-pilot-current",
        "pilot-backend-contracts",
        "pilot-operator-api",
        "marketing-build",
        "cabinet-build",
        "operator-center-build",
        "client-promo-tests",
        "client-promo-render-test",
        "docs-contract",
    } <= ids

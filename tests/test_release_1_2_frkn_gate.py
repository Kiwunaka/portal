from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "release_1_2_frkn_gate.py"
SPEC = importlib.util.spec_from_file_location("release_1_2_frkn_gate", MODULE_PATH)
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


def test_gate_covers_every_repository_and_cross_repo_contract(tmp_path: Path) -> None:
    platform = tmp_path / "platform"
    core = tmp_path / "core"
    client = tmp_path / "client"
    steps = MODULE.build_steps(
        platform_root=platform,
        core_root=core,
        client_root=client,
        evidence_dir=tmp_path / "evidence",
        go_executable="go-1.25.13",
        flutter_executable="flutter",
    )
    ids = {row.id for row in steps}
    assert {
        "cross-repo-contract-sync",
        "platform-awg-contract-tests",
        "platform-doc-contracts",
        "core-contract-and-tests",
        "client-runtime-analyze",
        "client-runtime-tests",
        "platform-diff-check",
        "core-diff-check",
        "client-diff-check",
    } <= ids


def test_manual_lanes_never_claim_exact_or_ru_pass() -> None:
    lanes = MODULE.manual_lanes()
    assert lanes
    assert all(row["status"] != "PASS" for row in lanes)
    assert all(row["required_for_candidate"] is True for row in lanes)

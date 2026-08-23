from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    module_path = REPO_ROOT / "scripts" / "release_1_2_local_quality_gate.py"
    spec = importlib.util.spec_from_file_location(
        "release_1_2_local_quality_gate", module_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = _load_module()


def _steps(tmp_path: Path):
    return [
        MODULE.GateStep("one", "unit", ("one",), tmp_path),
        MODULE.GateStep("two", "e2e", ("two",), tmp_path),
        MODULE.GateStep("three", "performance", ("three",), tmp_path),
    ]


def test_gate_stops_after_first_failure_and_marks_remaining_not_run(
    tmp_path: Path,
) -> None:
    return_codes = iter([0, 1])

    def runner(*_args, **_kwargs):
        return subprocess.CompletedProcess([], next(return_codes))

    results = MODULE.run_gate(
        steps=_steps(tmp_path), keep_going=False, runner=runner
    )

    assert [result.status for result in results] == ["PASS", "FAIL", "NOT_RUN"]


def test_keep_going_runs_every_step(tmp_path: Path) -> None:
    return_codes = iter([1, 0, 0])

    def runner(*_args, **_kwargs):
        return subprocess.CompletedProcess([], next(return_codes))

    results = MODULE.run_gate(
        steps=_steps(tmp_path), keep_going=True, runner=runner
    )

    assert [result.status for result in results] == ["FAIL", "PASS", "PASS"]


def test_manual_lanes_never_claim_pass() -> None:
    lanes = MODULE.manual_lanes()

    assert lanes
    assert all(lane["status"] != "PASS" for lane in lanes)
    assert all(lane["required_for_promotion"] is True for lane in lanes)
    assert {lane["status"] for lane in lanes} == {
        "MANUAL_OWNER_TEST",
        "BLOCKED_BY_ACCESS",
    }


def test_evidence_dir_rejects_release_artifact_tree(tmp_path: Path) -> None:
    platform_root = tmp_path / "platform"
    forbidden = platform_root / "artifacts" / "releases" / "gate"

    with pytest.raises(ValueError, match="cannot be written"):
        MODULE._validate_evidence_dir(forbidden, platform_root)


def test_full_step_set_combines_required_local_quality_lanes(tmp_path: Path) -> None:
    platform_root = tmp_path / "platform"
    client_root = tmp_path / "client"
    core_root = tmp_path / "core"
    evidence_dir = tmp_path / "evidence"
    steps = MODULE.build_steps(
        platform_root=platform_root,
        client_root=client_root,
        core_root=core_root,
        evidence_dir=evidence_dir,
    )
    ids = {step.id for step in steps}

    assert {
        "client-analyze",
        "client-widget-suite",
        "client-seed-contract",
        "client-docs-contract",
        "webapp-lint",
        "webapp-build",
        "webapp-cabinet-e2e",
        "marketing-build",
        "marketing-seo",
        "marketing-responsive-reduced-motion",
        "web-static-performance-gate",
    } <= ids
    assert all("artifacts\\releases" not in " ".join(step.command) for step in steps)

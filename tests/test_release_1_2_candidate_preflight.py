from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "release_1_2_candidate_preflight.py"
SPEC = importlib.util.spec_from_file_location(
    "release_1_2_candidate_preflight", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


LEDGER_PATH = (
    REPO_ROOT
    / "docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/EXECUTION-LEDGER.csv"
)
STAGE_POLICY_PATH = REPO_ROOT / MODULE.STAGE_POLICY_RELATIVE_PATH


def test_pending_lane_preserves_non_pass_labels() -> None:
    base = {
        "plan": "REL",
        "id": "X",
        "phase": "P11",
        "index": "I1",
        "summary": "x",
        "next_action": "x",
    }
    expected = {
        "MANUAL_OWNER_TEST": "manual_owner_test",
        "BLOCKED_BY_ACCESS": "blocked_by_access",
        "BLOCKED_BY_OWNER_DECISION": "blocked_by_owner_decision",
        "NOT_AUTHORIZED": "not_authorized",
        "NOT_REQUESTED": "not_requested",
        "VERIFIED_DEFERRED_1_2_0": "deferred",
        "VERIFIED_MONITOR_ONLY": "monitor_only",
    }
    for status, lane in expected.items():
        assert MODULE._pending_lane({**base, "status": status}) == lane


def test_pending_phase_11_defaults_to_candidate_lane() -> None:
    row = {
        "plan": "REL_DOD",
        "id": "DOD-20",
        "phase": "P11",
        "index": "I0",
        "status": "CAPTURED",
        "summary": "decision",
        "next_action": "run",
    }
    assert MODULE._pending_lane(row) == "phase_11_local_or_candidate"


def test_stage_policy_is_exact_and_defaults_unknown_work_to_pre_freeze() -> None:
    rows = MODULE._load_ledger(LEDGER_PATH)
    summary, assignments = MODULE._load_stage_policy(STAGE_POLICY_PATH, rows)

    assert summary == {
        "schema": "pokrov.release-1.2.0.row-stage-policy/v1",
        "path": "shared/release-1.2.0-candidate-stage-policy.json",
        "sha256": summary["sha256"],
        "default_stage": "pre_freeze",
        "override_count": 71,
        "ledger_row_count": 377,
    }
    assert len(summary["sha256"]) == 64
    assert len(assignments) == 377
    assert assignments[("FE", "P12-130")]["stage"] == "pre_freeze"
    assert assignments[("OBS", "OBS-070")]["stage"] == "pre_freeze"
    assert assignments[("REL_GATE", "GATE-F")]["stage"] == "candidate"
    assert assignments[("OBS_PB", "PB-14")]["stage"] == "candidate"
    assert assignments[("FE", "P12-201")]["stage"] == "deferred"
    assert assignments[("REL", "REL-001")] == {
        "stage": "external",
        "reason": assignments[("REL", "REL-001")]["reason"],
        "external_gate": "pre_candidate",
    }
    assert assignments[("MKT_STAGE", "STAGE-5")]["external_gate"] == ("post_candidate")


def test_stage_blockers_do_not_make_candidate_or_deferred_rows_circular() -> None:
    assert (
        MODULE._stage_blockers(
            [
                {"stage": "candidate"},
                {"stage": "deferred"},
                {"stage": "external", "external_gate": "post_candidate"},
            ]
        )
        == []
    )

    blockers = MODULE._stage_blockers(
        [
            {"stage": "pre_freeze"},
            {"stage": "pre_freeze"},
            {"stage": "external", "external_gate": "pre_candidate"},
        ]
    )
    assert blockers == [
        {
            "id": "ledger_pre_freeze_incomplete",
            "status": "BLOCKED_LOCAL_FREEZE",
            "detail": "2 explicitly staged rows remain below local I3",
        },
        {
            "id": "ledger_external_pre_candidate_incomplete",
            "status": "BLOCKED_EXTERNAL_PRECONDITION",
            "detail": "1 external pre-candidate rows remain unresolved",
        },
    ]


def _write_stage_policy(path: Path, overrides: list[dict[str, str]]) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "pokrov.release-1.2.0.row-stage-policy/v1",
                "default_stage": "pre_freeze",
                "stages": {
                    "pre_freeze": "a",
                    "candidate": "b",
                    "external": "c",
                    "deferred": "d",
                },
                "overrides": overrides,
            }
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("overrides", "error"),
    [
        (
            [
                {
                    "plan": "REL",
                    "id": "UNKNOWN",
                    "stage": "candidate",
                    "reason": "x",
                }
            ],
            "unknown ledger key",
        ),
        (
            [
                {
                    "plan": "REL",
                    "id": "REL-001",
                    "stage": "candidate",
                    "reason": "x",
                },
                {
                    "plan": "REL",
                    "id": "REL-001",
                    "stage": "deferred",
                    "reason": "y",
                },
            ],
            "duplicate candidate stage override",
        ),
        (
            [
                {
                    "plan": "REL",
                    "id": "REL-001",
                    "stage": "external",
                    "reason": "x",
                }
            ],
            "needs an exact external_gate",
        ),
    ],
)
def test_stage_policy_rejects_unknown_duplicate_or_ambiguous_overrides(
    tmp_path: Path, overrides: list[dict[str, str]], error: str
) -> None:
    path = tmp_path / "policy.json"
    _write_stage_policy(path, overrides)
    rows = MODULE._load_ledger(LEDGER_PATH)
    with pytest.raises(ValueError, match=error):
        MODULE._load_stage_policy(path, rows)


def test_exact_product_and_component_targets_are_accepted() -> None:
    blockers = MODULE._target_contract_blockers(
        versions={
            "android": "1.2.0+30",
            "windows": "1.2.0+30",
            "app_shell": "1.2.0",
        },
        handoff_target={
            "product_version": "1.2.0",
            "platform_build": 30,
            "package_version": "1.2.0+30",
            "state": "PRE_CANDIDATE_LOCAL",
            "candidate_created": False,
        },
        core_release={
            "version": "1.1.0",
            "state": "PRE_CANDIDATE_LOCAL",
            "candidate_created": False,
        },
        core_target={
            "required_for_product": "1.2.0",
            "version": "1.1.0",
            "release_tag": "v1.1.0",
            "state": "PRE_CANDIDATE_LOCAL",
            "candidate_created": False,
            "artifact_state": "pending",
        },
    )
    assert blockers == []


def test_relabelled_retained_core_or_candidate_state_fails_closed() -> None:
    blockers = MODULE._target_contract_blockers(
        versions={
            "android": "1.2.0+31",
            "windows": "1.2.0+30",
            "app_shell": "1.2.1",
        },
        handoff_target={
            "product_version": "1.2.0",
            "platform_build": 30,
            "package_version": "1.2.0+30",
            "state": "CANDIDATE",
            "candidate_created": True,
        },
        core_release={
            "version": "1.0.3",
            "state": "RELEASED",
            "candidate_created": True,
        },
        core_target={
            "required_for_product": "1.2.0",
            "version": "1.0.3",
            "release_tag": "v1.0.3",
            "state": "RELEASED",
            "candidate_created": True,
            "artifact_state": "ready",
        },
    )
    assert {blocker["id"] for blocker in blockers} == {
        "client_target_version_stale",
        "client_build_number_drift",
        "client_handoff_target_invalid",
        "core_source_target_invalid",
        "client_core_target_invalid",
    }

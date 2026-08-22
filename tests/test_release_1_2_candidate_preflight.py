from __future__ import annotations

import importlib.util
import hashlib
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


def test_exact_bound_core_target_is_accepted() -> None:
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
            "artifact_state": "exact_local_replacement_bound",
        },
    )
    assert blockers == []


def _bound_runtime_seed(client_root: Path, core_revision: str) -> dict[str, object]:
    android_path = client_root / "apps/android_shell/android/app/libs/pokrov-core.aar"
    windows_path = (
        client_root
        / "apps/windows_shell/windows/runner/resources/runtime/pokrov-core.dll"
    )
    cronet_path = windows_path.with_name("libcronet.dll")
    for path, content in (
        (android_path, b"android-core"),
        (windows_path, b"windows-core"),
        (cronet_path, b"cronet"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def identity(path: Path) -> dict[str, object]:
        return {
            "size": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    android = identity(android_path)
    windows = identity(windows_path)
    cronet = identity(cronet_path)
    proof_hash = "a" * 64
    return {
        "version": "1.1.0",
        "release_tag_created": False,
        "source_commit": core_revision,
        "activation_state": "active_pre_candidate_local",
        "development_target": {
            "artifact_state": "exact_local_replacement_bound",
        },
        "artifact_provenance": {
            "status": "clean_reproducible_pre_candidate_local",
            "vcs_stamp": "disabled_for_reproducible_release_artifacts",
            "release_url": None,
            "evidence_ceiling": "PRE_CANDIDATE_LOCAL",
            "candidate_created": False,
            "promotion_authorized": False,
            "reproducible_build": {
                "android": android,
                "windows": windows,
                "libcronet_sha256": cronet["sha256"],
            },
            "artifact_evidence": {
                "android": {
                    "result": "PASS_BYTE_IDENTICAL_TWO_BUILDS",
                    "tree_sha256": proof_hash,
                    "evidence_sha256": proof_hash,
                    "abis": ["armeabi-v7a", "arm64-v8a", "x86", "x86_64"],
                },
                "windows": {
                    "result": "PASS_BYTE_IDENTICAL_TWO_BUILDS",
                    "tree_sha256": proof_hash,
                    "evidence_sha256": proof_hash,
                    "required_exports": 15,
                    "proxy_only_start_stop_cycles": 100,
                    "proxy_only_result": "PASS_LOCAL",
                },
                "sbom": [
                    {"name": "pokrov-core.cdx.json", "sha256": proof_hash},
                    {"name": "sing-box.cdx.json", "sha256": proof_hash},
                ],
            },
        },
        "desktop_abi": {
            "required_capabilities": ["structured_operational_events"],
            "structured_events": {
                "callback_symbol": "pokrovCoreSetEventCallback",
                "context_symbol": "pokrovCoreSetEventContext",
                "exact_replacement_artifact": "bound_pre_candidate_local",
            },
        },
        "assets": {
            "android": {
                "entry": "pokrov-core.aar",
                **android,
                "sync_destination": "apps/android_shell/android/app/libs",
                "sync_policy": "exact_pre_candidate_build",
            },
            "windows": {
                "entry": "pokrov-core.dll",
                **windows,
                "runtime_dependencies": ["libcronet.dll"],
                "runtime_dependency_size": {"libcronet.dll": cronet["size"]},
                "runtime_dependency_sha256": {"libcronet.dll": cronet["sha256"]},
                "sync_destination": (
                    "apps/windows_shell/windows/runner/resources/runtime"
                ),
                "sync_policy": "exact_pre_candidate_build",
            },
        },
    }


def test_bound_core_artifacts_require_exact_local_bytes(tmp_path: Path) -> None:
    core_revision = "f" * 40
    runtime_seed = _bound_runtime_seed(tmp_path, core_revision)

    summary, blockers = MODULE._core_artifact_binding(
        client_root=tmp_path,
        runtime_seed=runtime_seed,
        core_revision=core_revision,
    )
    assert blockers == []
    assert summary["verified_exact_local_bytes"] is True
    assert all(item["match"] for item in summary["files"].values())

    dll_path = (
        tmp_path / "apps/windows_shell/windows/runner/resources/runtime/pokrov-core.dll"
    )
    dll_path.write_bytes(b"tampered")
    summary, blockers = MODULE._core_artifact_binding(
        client_root=tmp_path,
        runtime_seed=runtime_seed,
        core_revision=core_revision,
    )
    assert summary["verified_exact_local_bytes"] is False
    assert {blocker["id"] for blocker in blockers} == {
        "core_artifact_binding_bytes_invalid"
    }


def test_unbound_core_artifact_remains_pending(tmp_path: Path) -> None:
    summary, blockers = MODULE._core_artifact_binding(
        client_root=tmp_path,
        runtime_seed={
            "development_target": {"artifact_state": "pending"},
            "desktop_abi": {
                "structured_events": {"exact_replacement_artifact": "pending"}
            },
        },
        core_revision="f" * 40,
    )
    assert summary["verified_exact_local_bytes"] is False
    assert [blocker["id"] for blocker in blockers] == [
        "core_replacement_artifact_pending"
    ]


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

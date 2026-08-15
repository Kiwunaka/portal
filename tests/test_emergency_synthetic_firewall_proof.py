from __future__ import annotations

from pathlib import Path

from scripts import emergency_synthetic_firewall_proof as proof


def _executor_result(**check_overrides: bool) -> dict[str, object]:
    checks = {key: True for key in proof._CHECK_KEYS}
    checks.update(check_overrides)
    return {
        "schema_version": proof.EXECUTOR_SCHEMA,
        "core_sha256": proof.PINNED_CORE_SHA256,
        "executor_sha256": "a" * 64,
        "fixture_manifest_sha256": "b" * 64,
        "firewall_policy_sha256": "c" * 64,
        "payload_sha256": "d" * 64,
        "isolation": {
            "kind": "linux-network-namespace",
            "ephemeral": True,
            "host_firewall_untouched": True,
            "teardown_completed": True,
        },
        "checks": checks,
    }


def _validate(result: dict[str, object]) -> dict[str, object]:
    return proof._validate_executor_result(
        result,
        core_sha256=proof.PINNED_CORE_SHA256,
        executor_sha256="a" * 64,
        manifest_sha256="b" * 64,
        expected_payload_sha256="d" * 64,
    )


def test_complete_isolated_matrix_is_pass() -> None:
    result = _validate(_executor_result())

    assert result["classification"] == "PASS"
    assert result["failed_checks"] == []


def test_reachable_direct_foreign_fails_proof() -> None:
    result = _validate(_executor_result(direct_foreign_blocked=False))

    assert result["classification"] == "FAIL"
    assert result["failed_checks"] == ["direct_foreign_blocked"]


def test_incomplete_teardown_cannot_be_pass() -> None:
    executor_result = _executor_result()
    executor_result["isolation"]["teardown_completed"] = False  # type: ignore[index]

    result = _validate(executor_result)

    assert result["classification"] == "FAIL"
    assert result["failed_checks"] == ["teardown_incomplete"]


def test_preflight_without_controlled_material_is_blocked(tmp_path: Path) -> None:
    core = tmp_path / "pokrov-core.dll"
    core.write_bytes(b"not-the-exact-core")

    # A wrong candidate is a failure, not a synthetic PASS or readiness signal.
    try:
        proof.preflight(
            core_path=core,
            executor_path=None,
            executor_sha256=None,
            manifest_path=None,
            manifest_sha256=None,
        )
    except proof.ProofFailure as exc:
        assert exc.code == "exact_core_hash_mismatch"
    else:
        raise AssertionError("wrong Core hash must fail closed")


def test_missing_exact_core_is_blocked(tmp_path: Path) -> None:
    result = proof.preflight(
        core_path=tmp_path / "missing.dll",
        executor_path=None,
        executor_sha256=None,
        manifest_path=None,
        manifest_sha256=None,
    )

    assert result["classification"] == "BLOCKED_BY_ACCESS"
    assert result["reasons"] == ["exact_core_unavailable"]

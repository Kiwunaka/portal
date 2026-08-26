from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import pytest


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "performance_budget_gate.py"
    spec = importlib.util.spec_from_file_location("performance_budget_gate", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = _load_module()
REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    REPO_ROOT
    / "shared"
    / "contracts"
    / "performance"
    / "performance-budgets.v1.json"
)


def _contract() -> dict[str, object]:
    return MODULE._load_json(CONTRACT_PATH)


def _evidence(
    *,
    budget_id: str = "client.android.cold_start_useful_ui_ms",
    samples: list[float] | None = None,
    state: str = "MEASURED",
    warmups: int = 3,
    baseline: dict[str, object] | None = None,
) -> dict[str, object]:
    environment = {
        "architecture": "arm64-v8a",
        "artifact_sha256": "a" * 64,
        "build_mode": "release",
        "captured_at_utc": "2026-08-22T12:00:00Z",
        "collector_id": "pokrov.client-device",
        "collector_version": "1.0.0",
        "device_model": "reference-device-a",
        "network_profile": "controlled-wifi-a",
        "origin": "device-lab",
        "os_version": "Android 16",
        "platform": "android",
        "power_mode": "balanced",
        "toolchain": "Flutter 3.38.5;adb 1.0.41",
    }
    return {
        "schema_version": 1,
        "budget_contract": {
            "id": "pokrov.performance-budgets",
            "sha256": MODULE.contract_sha256(CONTRACT_PATH),
            "version": "1.0.0",
        },
        "release": {
            "candidate_label": "1.2.0-rc.1",
            "source_revision": "b" * 40,
            "version": "1.2.0",
            "working_tree_state": "clean",
        },
        "environment": environment,
        "measurements": [
            {
                "baseline": baseline,
                "budget_id": budget_id,
                "samples": samples if samples is not None else [2000.0] * 20,
                "state": state,
                "unit": "ms",
                "warmup_samples_discarded": warmups,
            }
        ],
    }


def test_canonical_contract_is_strict_and_versioned() -> None:
    contract = _contract()
    budgets = MODULE.validate_budget_contract(contract)

    assert contract["contract_version"] == "1.0.0"
    assert len(budgets) == 32
    assert "client.connect_verified_ms" in budgets
    assert "web.marketing.critical_route_js_gzip_bytes" in budgets
    assert "api.health.current_origin_ms" in budgets


def test_measured_samples_are_computed_by_gate() -> None:
    outcome = MODULE.evaluate_evidence(
        _contract(),
        _evidence(samples=[1900.0] * 18 + [2400.0] * 2),
        contract_path=CONTRACT_PATH,
    )

    result = outcome.summary["results"][0]
    assert result["value"] == 2400.0
    assert result["gate_status"] == "PASS"
    assert result["target_met"] is False
    assert outcome.has_budget_failure is False


def test_stop_threshold_failure_cannot_be_reported_as_pass() -> None:
    outcome = MODULE.evaluate_evidence(
        _contract(),
        _evidence(samples=[2600.0] * 20),
        contract_path=CONTRACT_PATH,
    )

    assert outcome.summary["results"][0]["gate_status"] == "FAIL"
    assert outcome.summary["overall_status"] == "FAIL"
    assert outcome.has_budget_failure is True


def test_source_bound_environment_is_validated_and_fingerprinted() -> None:
    direct = _evidence()
    direct["environment"]["source_address"] = "192.0.2.10"
    direct["environment"]["proxy_policy"] = "disabled_for_source_bound_probe"
    ambient = _evidence()

    direct_outcome = MODULE.evaluate_evidence(
        _contract(),
        direct,
        contract_path=CONTRACT_PATH,
    )
    ambient_outcome = MODULE.evaluate_evidence(
        _contract(),
        ambient,
        contract_path=CONTRACT_PATH,
    )

    assert (
        direct_outcome.summary["environment_fingerprint"]
        != ambient_outcome.summary["environment_fingerprint"]
    )

    invalid_address = _evidence()
    invalid_address["environment"]["source_address"] = "localhost"
    invalid_address["environment"]["proxy_policy"] = (
        "disabled_for_source_bound_probe"
    )
    with pytest.raises(MODULE.ContractError, match="expected literal IP"):
        MODULE.evaluate_evidence(
            _contract(),
            invalid_address,
            contract_path=CONTRACT_PATH,
        )

    missing_policy = _evidence()
    missing_policy["environment"]["source_address"] = "192.0.2.10"
    with pytest.raises(MODULE.ContractError, match="must appear together"):
        MODULE.evaluate_evidence(
            _contract(),
            missing_policy,
            contract_path=CONTRACT_PATH,
        )


def test_insufficient_samples_are_rejected() -> None:
    with pytest.raises(MODULE.ContractError, match="insufficient retained samples"):
        MODULE.evaluate_evidence(
            _contract(),
            _evidence(samples=[1000.0] * 19),
            contract_path=CONTRACT_PATH,
        )


def test_manual_state_never_satisfies_required_scope() -> None:
    evidence = _evidence(state="MANUAL_OWNER_TEST", samples=[], warmups=0)
    outcome = MODULE.evaluate_evidence(
        _contract(),
        evidence,
        contract_path=CONTRACT_PATH,
        required_scopes={"candidate_device"},
    )

    assert outcome.has_budget_failure is True
    assert "client.android.cold_start_useful_ui_ms" in outcome.summary[
        "nonpassing_required_budget_ids"
    ]
    assert outcome.summary["results"][0]["gate_status"] == "MANUAL_OWNER_TEST"


def test_comparable_baseline_enforces_regression_threshold() -> None:
    evidence = _evidence(samples=[2200.0] * 20)
    fingerprint = MODULE.environment_fingerprint(evidence["environment"])
    evidence["measurements"][0]["baseline"] = {
        "candidate_label": "1.2.0-beta.9",
        "environment_fingerprint": fingerprint,
        "source_revision": "c" * 40,
        "value": 1900.0,
    }
    outcome = MODULE.evaluate_evidence(
        _contract(), evidence, contract_path=CONTRACT_PATH
    )

    result = outcome.summary["results"][0]
    assert result["stop_met"] is True
    assert result["regression_met"] is False
    assert result["gate_status"] == "FAIL"


def test_baseline_from_different_environment_is_rejected() -> None:
    evidence = _evidence(samples=[2000.0] * 20)
    evidence["measurements"][0]["baseline"] = {
        "candidate_label": "1.2.0-beta.9",
        "environment_fingerprint": "d" * 64,
        "source_revision": "c" * 40,
        "value": 1900.0,
    }

    with pytest.raises(MODULE.ContractError, match="fingerprint mismatch"):
        MODULE.evaluate_evidence(
            _contract(), evidence, contract_path=CONTRACT_PATH
        )


def test_contract_digest_mismatch_is_rejected() -> None:
    evidence = _evidence()
    evidence["budget_contract"]["sha256"] = "0" * 64

    with pytest.raises(MODULE.ContractError, match="sha256: mismatch"):
        MODULE.evaluate_evidence(
            _contract(), evidence, contract_path=CONTRACT_PATH
        )


def test_json_loader_rejects_duplicate_keys() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "duplicate.json"
        path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
        with pytest.raises(MODULE.ContractError, match="invalid JSON"):
            MODULE._load_json(path)


def test_observation_without_stop_threshold_records_first_baseline() -> None:
    evidence = _evidence(
        budget_id="client.android.idle_pss_bytes",
        samples=[120_000_000.0] * 60,
        warmups=30,
    )
    evidence["measurements"][0]["unit"] = "bytes"
    evidence["environment"]["idle_window_seconds"] = 60
    outcome = MODULE.evaluate_evidence(
        _contract(), evidence, contract_path=CONTRACT_PATH
    )

    assert outcome.summary["results"][0]["gate_status"] == "BASELINE_RECORDED"
    assert outcome.has_budget_failure is False

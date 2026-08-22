from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))


def _load_module():
    module_path = SCRIPTS_ROOT / "new_performance_evidence.py"
    spec = importlib.util.spec_from_file_location("new_performance_evidence", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = _load_module()
CONTRACT_PATH = (
    REPO_ROOT
    / "shared"
    / "contracts"
    / "performance"
    / "performance-budgets.v1.json"
)


def _environment(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
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
        ),
        encoding="utf-8",
    )
    return path


def test_create_measured_evidence_uses_contract_unit_and_git_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    environment = _environment(tmp_path / "environment.json")
    samples = tmp_path / "samples.json"
    samples.write_text(json.dumps([2000] * 20), encoding="utf-8")
    monkeypatch.setattr(MODULE, "_git_identity", lambda _: ("b" * 40, "dirty"))

    evidence = MODULE.create_evidence(
        contract_path=CONTRACT_PATH,
        budget_id="client.android.cold_start_useful_ui_ms",
        environment_path=environment,
        samples_path=samples,
        state="MEASURED",
        warmups=3,
        baseline_summary_path=None,
        repo_root=tmp_path,
        candidate_label="local-device-run",
        release_version="1.2.0",
    )

    measurement = evidence["measurements"][0]
    assert measurement["unit"] == "ms"
    assert measurement["samples"] == [2000.0] * 20
    assert evidence["release"]["working_tree_state"] == "dirty"


def test_non_measured_evidence_rejects_samples(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    environment = _environment(tmp_path / "environment.json")
    samples = tmp_path / "samples.json"
    samples.write_text("[1]", encoding="utf-8")
    monkeypatch.setattr(MODULE, "_git_identity", lambda _: ("b" * 40, "clean"))

    with pytest.raises(MODULE.ContractError, match="cannot use --samples"):
        MODULE.create_evidence(
            contract_path=CONTRACT_PATH,
            budget_id="client.android.cold_start_useful_ui_ms",
            environment_path=environment,
            samples_path=samples,
            state="MANUAL_OWNER_TEST",
            warmups=0,
            baseline_summary_path=None,
            repo_root=tmp_path,
            candidate_label="candidate",
            release_version="1.2.0",
        )


def test_baseline_summary_must_contain_accepted_matching_result(tmp_path: Path) -> None:
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "release": {
                    "candidate_label": "old",
                    "source_revision": "c" * 40,
                },
                "results": [
                    {
                        "budget_id": "client.android.cold_start_useful_ui_ms",
                        "environment_fingerprint": "d" * 64,
                        "gate_status": "FAIL",
                        "value": 3000,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(MODULE.ContractError, match="not an accepted measurement"):
        MODULE._baseline_from_summary(
            summary, budget_id="client.android.cold_start_useful_ui_ms"
        )

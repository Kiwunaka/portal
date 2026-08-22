from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "release_1_2_stop_ship_gate.py"
SPEC = importlib.util.spec_from_file_location("release_1_2_stop_ship_gate", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_canonical_registry_contains_exact_seven_stop_ship_findings() -> None:
    registry = MODULE._read_registry(MODULE.DEFAULT_REGISTRY)

    assert {entry["id"] for entry in registry["entries"]} == MODULE.EXPECTED_IDS
    assert all(entry["regressions"] for entry in registry["entries"])


def test_branch_payload_requires_strict_mode_and_every_named_check() -> None:
    payload = {
        "required_status_checks": {
            "strict": True,
            "contexts": ["test"],
            "checks": [{"context": "release-contract", "app_id": 1}],
        }
    }

    assert MODULE._evaluate_branch_payload(
        payload, ["test", "release-contract"]
    ) == ("PASS", [])
    assert MODULE._evaluate_branch_payload(payload, ["missing"]) == (
        "FAIL",
        ["missing"],
    )
    payload["required_status_checks"]["strict"] = False
    assert MODULE._evaluate_branch_payload(payload, ["test"])[0] == "FAIL"


def test_github_plan_limit_is_blocked_by_access_without_false_pass() -> None:
    completed = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout="",
        stderr=json.dumps(
            {
                "message": "Upgrade to GitHub Pro or make this repository public to enable this feature.",
                "status": "403",
            }
        ),
    )
    with patch.object(MODULE.subprocess, "run", return_value=completed):
        result = MODULE._query_branch_protection("owner/repo", "main", ["test"])

    assert result["result"] == "BLOCKED_BY_ACCESS"
    assert result["error_class"] == "feature_or_permission_unavailable"


def test_unprotected_branch_is_an_explicit_failure() -> None:
    completed = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout="",
        stderr='{"message":"Branch not protected","status":"404"}',
    )
    with patch.object(MODULE.subprocess, "run", return_value=completed):
        result = MODULE._query_branch_protection("owner/repo", "main", ["test"])

    assert result["result"] == "FAIL_UNPROTECTED"
    assert result["error_class"] == "branch_unprotected"


def test_local_registry_anchors_resolve_without_repository_assumptions(
    tmp_path: Path,
) -> None:
    registry = MODULE._read_registry(MODULE.DEFAULT_REGISTRY)
    roots = {
        "platform": tmp_path / "platform",
        "client": tmp_path / "client",
        "core": tmp_path / "core",
    }
    for entry in registry["entries"]:
        for regression in entry["regressions"]:
            path = roots[regression["repository"]] / regression["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            existing = path.read_text(encoding="utf-8") if path.exists() else ""
            path.write_text(
                existing + "\n".join(regression["contains"]) + "\n",
                encoding="utf-8",
            )
    results = MODULE._validate_regressions(
        registry,
        roots,
    )

    assert len(results) == 7
    assert {result["result"] for result in results} == {"PASS"}
    assert all(
        len(check["sha256"]) == 64
        for result in results
        for check in result["checks"]
    )

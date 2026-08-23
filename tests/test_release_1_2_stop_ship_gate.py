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
    assert registry["branch_policy"]["required_signatures"] is True
    assert registry["branch_policy"]["require_status_check_app_binding"] is True
    assert registry["branch_policy"]["codeowners"]["selected_code_owners"] == []


def test_registry_reviewer_selection_state_is_fail_closed(tmp_path: Path) -> None:
    registry = json.loads(MODULE.DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    registry["branch_policy"]["codeowners"]["selection_state"] = "READY"
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")

    try:
        MODULE._read_registry(path)
    except ValueError as exc:
        assert "selection_state contradicts" in str(exc)
    else:
        raise AssertionError("contradictory reviewer selection must fail closed")


def _complete_branch_payload() -> dict[str, object]:
    return {
        "required_status_checks": {
            "strict": True,
            "contexts": [],
            "checks": [
                {"context": "test", "app_id": 1},
                {"context": "release-contract", "app_id": 1},
            ],
        },
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": True,
            "required_approving_review_count": 1,
            "require_last_push_approval": True,
        },
        "enforce_admins": {"enabled": True},
        "required_linear_history": {"enabled": True},
        "required_conversation_resolution": {"enabled": True},
        "required_signatures": {"enabled": True},
        "allow_force_pushes": {"enabled": False},
        "allow_deletions": {"enabled": False},
    }


def test_branch_payload_requires_strict_mode_and_every_named_check() -> None:
    registry = MODULE._read_registry(MODULE.DEFAULT_REGISTRY)
    policy = registry["branch_policy"]
    payload = _complete_branch_payload()

    assert MODULE._evaluate_branch_payload(
        payload, ["test", "release-contract"], policy
    ) == ("PASS", [])
    assert MODULE._evaluate_branch_payload(payload, ["missing"], policy) == (
        "FAIL",
        ["required_check:missing", "required_check_app_binding:missing"],
    )
    payload["required_status_checks"]["strict"] = False
    assert MODULE._evaluate_branch_payload(payload, ["test"], policy)[0] == "FAIL"


def test_branch_payload_rejects_every_missing_release_policy_control() -> None:
    registry = MODULE._read_registry(MODULE.DEFAULT_REGISTRY)
    policy = registry["branch_policy"]
    payload = _complete_branch_payload()

    for field in (
        "enforce_admins",
        "required_linear_history",
        "required_conversation_resolution",
        "required_signatures",
        "allow_force_pushes",
        "allow_deletions",
    ):
        mutated = dict(payload)
        mutated[field] = None
        result, missing = MODULE._evaluate_branch_payload(mutated, ["test"], policy)
        assert result == "FAIL"
        assert field in missing

    for field in (
        "dismiss_stale_reviews",
        "require_code_owner_reviews",
        "require_last_push_approval",
    ):
        mutated = dict(payload)
        mutated_reviews = dict(payload["required_pull_request_reviews"])
        mutated_reviews[field] = False
        mutated["required_pull_request_reviews"] = mutated_reviews
        result, missing = MODULE._evaluate_branch_payload(mutated, ["test"], policy)
        assert result == "FAIL"
        assert f"review:{field}" in missing

    unbound = _complete_branch_payload()
    unbound["required_status_checks"] = {
        "strict": True,
        "contexts": ["test"],
        "checks": [],
    }
    result, missing = MODULE._evaluate_branch_payload(unbound, ["test"], policy)
    assert result == "FAIL"
    assert "required_check_app_binding:test" in missing


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
        policy = MODULE._read_registry(MODULE.DEFAULT_REGISTRY)["branch_policy"]
        result = MODULE._query_branch_protection("owner/repo", "main", ["test"], policy)

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
        policy = MODULE._read_registry(MODULE.DEFAULT_REGISTRY)["branch_policy"]
        result = MODULE._query_branch_protection("owner/repo", "main", ["test"], policy)

    assert result["result"] == "FAIL_UNPROTECTED"
    assert result["error_class"] == "branch_unprotected"


def test_reviewer_control_blocks_when_no_non_author_reviewer_exists() -> None:
    completed = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=json.dumps([[{"login": "Kiwunaka", "permissions": {"admin": True}}]]),
        stderr="",
    )
    contract = MODULE._read_registry(MODULE.DEFAULT_REGISTRY)["branch_policy"][
        "codeowners"
    ]
    with patch.object(MODULE.subprocess, "run", return_value=completed):
        result = MODULE._query_reviewer_control("Kiwunaka/portal", "master", contract)

    assert result["result"] == "BLOCKED_BY_OWNER_DECISION"
    assert result["eligible_non_author_reviewer_count"] == 0


def test_reviewer_control_requires_eligible_owner_and_secure_coverage() -> None:
    collaborators = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=json.dumps([[{"login": "reviewer", "permissions": {"push": True}}]]),
        stderr="",
    )
    codeowners = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="* @reviewer\n/.github/ @reviewer\n",
        stderr="",
    )
    contract = {
        "path": ".github/CODEOWNERS",
        "excluded_pr_author": "Kiwunaka",
        "minimum_eligible_non_author_reviewers": 1,
        "selected_code_owners": ["@reviewer"],
        "selection_state": "READY",
    }
    with patch.object(
        MODULE.subprocess,
        "run",
        side_effect=[collaborators, codeowners],
    ):
        result = MODULE._query_reviewer_control("Kiwunaka/portal", "master", contract)

    assert result["result"] == "PASS"
    assert result["selected_code_owner_count"] == 1


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
        len(check["sha256"]) == 64 for result in results for check in result["checks"]
    )

"""Validate permanent 1.2.0 STOP-SHIP regressions and hosted controls."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = REPO_ROOT / "shared" / "release-1.2.0-stop-ship-regressions.json"
EXPECTED_IDS = {
    "PAY-001",
    "PAY-002",
    "REL-001",
    "REL-002",
    "WIN-001",
    "WIN-002",
    "WIN-003",
}

REQUIRED_TRUE_BRANCH_POLICY_FIELDS = {
    "enforce_admins",
    "required_linear_history",
    "required_conversation_resolution",
    "required_signatures",
}
REQUIRED_FALSE_BRANCH_POLICY_FIELDS = {
    "allow_force_pushes",
    "allow_deletions",
}
REQUIRED_TRUE_REVIEW_FIELDS = {
    "dismiss_stale_reviews",
    "require_code_owner_reviews",
    "require_last_push_approval",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_registry(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("STOP-SHIP registry must be an object")
    if value.get("schema") != "pokrov.release-stop-ship-regressions.v1":
        raise ValueError("STOP-SHIP registry schema is invalid")
    if value.get("release") != "1.2.0":
        raise ValueError("STOP-SHIP registry release must be 1.2.0")
    policy = value.get("branch_policy")
    if not isinstance(policy, dict):
        raise ValueError("STOP-SHIP registry branch_policy must be an object")
    if policy.get("require_status_check_app_binding") is not True:
        raise ValueError("branch_policy must bind required checks to a GitHub App")
    for field in REQUIRED_TRUE_BRANCH_POLICY_FIELDS:
        if policy.get(field) is not True:
            raise ValueError(f"branch_policy.{field} must be true")
    for field in REQUIRED_FALSE_BRANCH_POLICY_FIELDS:
        if policy.get(field) is not False:
            raise ValueError(f"branch_policy.{field} must be false")
    reviews = policy.get("required_pull_request_reviews")
    if not isinstance(reviews, dict):
        raise ValueError("branch_policy reviews must be an object")
    for field in REQUIRED_TRUE_REVIEW_FIELDS:
        if reviews.get(field) is not True:
            raise ValueError(f"branch_policy reviews.{field} must be true")
    if (
        not isinstance(reviews.get("required_approving_review_count"), int)
        or reviews["required_approving_review_count"] < 1
    ):
        raise ValueError("branch_policy must require at least one approving review")
    codeowners = policy.get("codeowners")
    if not isinstance(codeowners, dict):
        raise ValueError("branch_policy codeowners must be an object")
    if codeowners.get("path") != ".github/CODEOWNERS":
        raise ValueError("branch_policy CODEOWNERS path must be .github/CODEOWNERS")
    selected = codeowners.get("selected_code_owners")
    if not isinstance(selected, list) or not all(
        isinstance(owner, str) and owner.startswith("@") for owner in selected
    ):
        raise ValueError("selected_code_owners must contain GitHub @principals")
    expected_selection_state = "READY" if selected else "BLOCKED_BY_OWNER_DECISION"
    if codeowners.get("selection_state") != expected_selection_state:
        raise ValueError(
            "branch_policy CODEOWNERS selection_state contradicts selected owners"
        )
    minimum = codeowners.get("minimum_eligible_non_author_reviewers")
    if not isinstance(minimum, int) or minimum < 1:
        raise ValueError("branch_policy requires a non-author reviewer")
    entries = value.get("entries")
    if not isinstance(entries, list):
        raise ValueError("STOP-SHIP registry entries must be a list")
    ids = [entry.get("id") for entry in entries if isinstance(entry, dict)]
    if len(ids) != len(set(ids)) or set(ids) != EXPECTED_IDS:
        raise ValueError(f"STOP-SHIP IDs must be exactly {sorted(EXPECTED_IDS)}")
    return value


def _validate_regressions(
    registry: dict[str, Any],
    roots: dict[str, Path],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for entry in registry["entries"]:
        regressions = entry.get("regressions")
        if not isinstance(regressions, list) or not regressions:
            raise ValueError(f"{entry['id']} has no permanent regression")
        checks: list[dict[str, Any]] = []
        for regression in regressions:
            repository = regression.get("repository")
            relative_path = regression.get("path")
            fragments = regression.get("contains")
            if repository not in roots or not isinstance(relative_path, str):
                raise ValueError(f"{entry['id']} regression target is invalid")
            if (
                not isinstance(fragments, list)
                or not fragments
                or not all(
                    isinstance(fragment, str) and fragment for fragment in fragments
                )
            ):
                raise ValueError(f"{entry['id']} regression anchors are invalid")
            path = roots[repository] / relative_path
            missing: list[str] = []
            if path.is_file():
                text = path.read_text(encoding="utf-8-sig")
                missing = [fragment for fragment in fragments if fragment not in text]
            else:
                missing = ["<file_missing>"]
            checks.append(
                {
                    "repository": repository,
                    "path": relative_path,
                    "result": "PASS" if not missing else "FAIL",
                    "missing_anchor_count": len(missing),
                    "sha256": _sha256_file(path) if path.is_file() else None,
                }
            )
        results.append(
            {
                "id": entry["id"],
                "result": "PASS"
                if all(check["result"] == "PASS" for check in checks)
                else "FAIL",
                "checks": checks,
            }
        )
    return results


def _source_identity(root: Path) -> dict[str, str]:
    revision = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
    ).stdout.strip()
    status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
    ).stdout
    return {
        "revision": revision,
        "working_tree_state": "clean" if not status.strip() else "dirty",
    }


def _required_check_names(payload: dict[str, Any]) -> set[str]:
    required = payload.get("required_status_checks")
    if not isinstance(required, dict):
        return set()
    names = {
        item for item in required.get("contexts", []) if isinstance(item, str) and item
    }
    for item in required.get("checks", []):
        if isinstance(item, dict) and isinstance(item.get("context"), str):
            names.add(item["context"])
    return names


def _app_bound_check_names(payload: dict[str, Any]) -> set[str]:
    required = payload.get("required_status_checks")
    if not isinstance(required, dict):
        return set()
    return {
        item["context"]
        for item in required.get("checks", [])
        if isinstance(item, dict)
        and isinstance(item.get("context"), str)
        and isinstance(item.get("app_id"), int)
        and item["app_id"] > 0
    }


def _enabled_state(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, dict) and isinstance(value.get("enabled"), bool):
        return value["enabled"]
    return None


def _evaluate_branch_payload(
    payload: dict[str, Any],
    required_checks: list[str],
    policy: dict[str, Any],
) -> tuple[str, list[str]]:
    missing: list[str] = []
    status_checks = payload.get("required_status_checks")
    if not isinstance(status_checks, dict):
        missing.append("required_status_checks")
    else:
        if status_checks.get("strict") is not True:
            missing.append("strict_status_checks")
        present = _required_check_names(payload)
        missing.extend(
            f"required_check:{name}" for name in sorted(set(required_checks) - present)
        )
        if policy["require_status_check_app_binding"]:
            app_bound = _app_bound_check_names(payload)
            missing.extend(
                f"required_check_app_binding:{name}"
                for name in sorted(set(required_checks) - app_bound)
            )

    reviews = payload.get("required_pull_request_reviews")
    required_reviews = policy["required_pull_request_reviews"]
    if not isinstance(reviews, dict):
        missing.append("required_pull_request_reviews")
    else:
        for field in REQUIRED_TRUE_REVIEW_FIELDS:
            if reviews.get(field) is not True:
                missing.append(f"review:{field}")
        actual_count = reviews.get("required_approving_review_count")
        if (
            not isinstance(actual_count, int)
            or actual_count < required_reviews["required_approving_review_count"]
        ):
            missing.append("review:required_approving_review_count")

    for field in REQUIRED_TRUE_BRANCH_POLICY_FIELDS:
        if _enabled_state(payload.get(field)) is not True:
            missing.append(field)
    for field in REQUIRED_FALSE_BRANCH_POLICY_FIELDS:
        if _enabled_state(payload.get(field)) is not False:
            missing.append(field)
    missing = sorted(set(missing))
    return ("PASS" if not missing else "FAIL"), missing


def _query_branch_protection(
    repository: str,
    branch: str,
    required_checks: list[str],
    policy: dict[str, Any],
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "gh",
            "api",
            "-H",
            "Accept: application/vnd.github+json",
            f"repos/{repository}/branches/{branch}/protection",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    raw = completed.stdout.strip() or completed.stderr.strip()
    try:
        payload = json.loads(completed.stdout) if completed.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    if completed.returncode == 0:
        result, missing = _evaluate_branch_payload(payload, required_checks, policy)
        return {
            "repository": repository,
            "branch": branch,
            "result": result,
            "required_checks": required_checks,
            "missing_policy_requirements": missing,
        }
    lowered = raw.lower()
    if "upgrade to github pro" in lowered or '"status":"403"' in lowered:
        result = "BLOCKED_BY_ACCESS"
    elif "branch not protected" in lowered or '"status":"404"' in lowered:
        result = "FAIL_UNPROTECTED"
    else:
        result = "BLOCKED_BY_ACCESS"
    return {
        "repository": repository,
        "branch": branch,
        "result": result,
        "required_checks": required_checks,
        "error_class": "feature_or_permission_unavailable"
        if result == "BLOCKED_BY_ACCESS"
        else "branch_unprotected",
    }


def _query_eligible_reviewers(
    repository: str,
    excluded_login: str,
) -> tuple[str, set[str]]:
    completed = subprocess.run(
        [
            "gh",
            "api",
            "--paginate",
            "--slurp",
            f"repos/{repository}/collaborators?affiliation=direct&per_page=100",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        return "BLOCKED_BY_ACCESS", set()
    try:
        pages = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return "BLOCKED_BY_ACCESS", set()
    if not isinstance(pages, list):
        return "BLOCKED_BY_ACCESS", set()
    if pages and all(isinstance(item, dict) for item in pages):
        pages = [pages]
    reviewers: set[str] = set()
    for page in pages:
        if not isinstance(page, list):
            return "BLOCKED_BY_ACCESS", set()
        for item in page:
            if not isinstance(item, dict) or item.get("login") == excluded_login:
                continue
            login = item.get("login")
            if not isinstance(login, str) or not login:
                continue
            permissions = item.get("permissions")
            if not isinstance(permissions, dict):
                continue
            if any(
                permissions.get(name) is True for name in ("push", "maintain", "admin")
            ):
                reviewers.add(f"@{login}")
    return "PASS", reviewers


def _query_remote_codeowners(repository: str, branch: str) -> tuple[str, str]:
    completed = subprocess.run(
        [
            "gh",
            "api",
            "-H",
            "Accept: application/vnd.github.raw+json",
            f"repos/{repository}/contents/.github/CODEOWNERS?ref={branch}",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode == 0:
        return "PASS", completed.stdout
    raw = (completed.stdout + completed.stderr).lower()
    if '"status":"404"' in raw or "not found" in raw:
        return "FAIL_MISSING_CODEOWNERS", ""
    return "BLOCKED_BY_ACCESS", ""


def _codeowners_lines(text: str) -> list[tuple[str, set[str]]]:
    parsed: list[tuple[str, set[str]]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        owners = {part for part in parts[1:] if part.startswith("@")}
        if owners:
            parsed.append((parts[0], owners))
    return parsed


def _query_reviewer_control(
    repository: str,
    branch: str,
    codeowners_contract: dict[str, Any],
) -> dict[str, Any]:
    selected = set(codeowners_contract["selected_code_owners"])
    reviewer_status, eligible = _query_eligible_reviewers(
        repository,
        codeowners_contract["excluded_pr_author"],
    )
    result: dict[str, Any] = {
        "repository": repository,
        "branch": branch,
        "codeowners_path": codeowners_contract["path"],
        "selected_code_owner_count": len(selected),
        "eligible_non_author_reviewer_count": len(eligible),
    }
    if reviewer_status != "PASS":
        return {**result, "result": reviewer_status}
    if len(eligible) < codeowners_contract["minimum_eligible_non_author_reviewers"]:
        return {**result, "result": "BLOCKED_BY_OWNER_DECISION"}
    if not selected:
        return {**result, "result": "BLOCKED_BY_OWNER_DECISION"}
    if not selected.issubset(eligible):
        return {**result, "result": "FAIL_SELECTED_CODE_OWNER_NOT_ELIGIBLE"}

    codeowners_status, text = _query_remote_codeowners(repository, branch)
    if codeowners_status != "PASS":
        return {**result, "result": codeowners_status}
    lines = _codeowners_lines(text)
    root_owners: set[str] = set()
    control_owners: set[str] = set()
    for pattern, owners in lines:
        if pattern in {"*", "/*"}:
            root_owners.update(owners)
        if pattern in {"/.github/", ".github/", "/.github/CODEOWNERS"}:
            control_owners.update(owners)
    if not selected.issubset(root_owners) or not selected.issubset(control_owners):
        return {**result, "result": "FAIL_CODEOWNERS_COVERAGE"}
    return {**result, "result": "PASS"}


def build_report(
    *,
    registry_path: Path,
    platform_root: Path,
    client_root: Path,
    core_root: Path,
    query_github: bool,
) -> dict[str, Any]:
    registry = _read_registry(registry_path)
    branch_policy = registry["branch_policy"]
    roots = {
        "platform": platform_root,
        "client": client_root,
        "core": core_root,
    }
    sources = {name: _source_identity(root) for name, root in roots.items()}
    regressions = _validate_regressions(registry, roots)
    hosted_controls: list[dict[str, Any]] = []
    manual_gates: list[dict[str, str]] = []
    for entry in registry["entries"]:
        for control in entry.get("hosted_controls", []):
            if query_github:
                result = _query_branch_protection(
                    control["repository"],
                    control["branch"],
                    control["required_checks"],
                    branch_policy,
                )
            else:
                result = {
                    **control,
                    "result": "NOT_RUN",
                }
            hosted_controls.append({"stop_ship_id": entry["id"], **result})
        if isinstance(entry.get("manual_gate"), str):
            manual_gates.append(
                {
                    "stop_ship_id": entry["id"],
                    "gate": entry["manual_gate"],
                    "result": "NOT_RUN",
                }
            )

    reviewer_controls: list[dict[str, Any]] = []
    rel_001 = next(entry for entry in registry["entries"] if entry["id"] == "REL-001")
    for control in rel_001.get("hosted_controls", []):
        if query_github:
            reviewer = _query_reviewer_control(
                control["repository"],
                control["branch"],
                branch_policy["codeowners"],
            )
        else:
            reviewer = {
                "repository": control["repository"],
                "branch": control["branch"],
                "result": "NOT_RUN",
            }
        reviewer_controls.append(reviewer)

    local_pass = all(item["result"] == "PASS" for item in regressions)
    hosted_fail = any(
        item["result"] in {"FAIL", "FAIL_UNPROTECTED"} for item in hosted_controls
    )
    hosted_incomplete = any(
        item["result"] in {"BLOCKED_BY_ACCESS", "NOT_RUN"} for item in hosted_controls
    )
    reviewer_fail = any(item["result"].startswith("FAIL") for item in reviewer_controls)
    reviewer_incomplete = any(
        item["result"] in {"BLOCKED_BY_ACCESS", "BLOCKED_BY_OWNER_DECISION", "NOT_RUN"}
        for item in reviewer_controls
    )
    if not local_pass or hosted_fail or reviewer_fail:
        status = "NO_GO"
    elif hosted_incomplete or reviewer_incomplete or manual_gates:
        status = "BLOCKED"
    else:
        status = "PASS"
    return {
        "schema": "pokrov.release-1.2.0.stop-ship-gate.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "release": "1.2.0",
        "status": status,
        "candidate_proven": False,
        "sources": sources,
        "registry": str(registry_path),
        "registry_sha256": _sha256_file(registry_path),
        "expected_stop_ship_ids": sorted(EXPECTED_IDS),
        "required_branch_policy": branch_policy,
        "local_regressions": regressions,
        "hosted_branch_protection": hosted_controls,
        "hosted_codeowner_reviewers": reviewer_controls,
        "manual_gates": manual_gates,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--platform-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--client-root", type=Path, required=True)
    parser.add_argument("--core-root", type=Path, required=True)
    parser.add_argument("--query-github", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expect-nonpass", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = build_report(
            registry_path=args.registry.resolve(),
            platform_root=args.platform_root.resolve(),
            client_root=args.client_root.resolve(),
            core_root=args.core_root.resolve(),
            query_github=args.query_github,
        )
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f"STOP_SHIP_GATE_ERROR: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "status": report["status"],
                "local_regressions": len(report["local_regressions"]),
                "hosted_controls": len(report["hosted_branch_protection"]),
                "reviewer_controls": len(report["hosted_codeowner_reviewers"]),
                "manual_gates": len(report["manual_gates"]),
                "output": str(output),
            },
            sort_keys=True,
        )
    )
    if args.expect_nonpass:
        return 0 if report["status"] != "PASS" else 1
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

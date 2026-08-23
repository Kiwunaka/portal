"""Validate the real release-base POKROV 1.2.0 PR-00 freeze commit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = Path(
    "docs/developer/work-orders/2026-08-23--release-1.2.0-pr00/PR00-FREEZE.json"
)
EXPECTED_ACCEPTANCE = {
    "release_branches",
    "baseline_shas",
    "flags",
    "manifest_schema",
    "product_facts_snapshot",
    "reason_code_draft",
    "motion_semantics",
    "no_visible_ui_change",
}
EXPECTED_BRANCHES = {
    "platform": {
        "repository": "Kiwunaka/portal",
        "promotion_branch": "master",
        "release_branch": "release/1.2.0-frontend",
        "base_revision": "280ed9157f5804d4bc719cb8d6cab471caafb937",
    },
    "client": {
        "repository": "Kiwunaka/POKROV-app",
        "promotion_branch": "main",
        "release_branch": "release/1.2.0-frontend",
        "base_revision": "ba7930ea83487874f47a49199ade89868c5675b3",
    },
}
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()


def _current_branch(root: Path) -> str:
    return os.environ.get("POKROV_RELEASE_HEAD_REF", "").strip() or _git(
        root, "branch", "--show-current"
    )


def _diff_policy_errors(
    changed_paths: list[str], allowed_paths: list[str], visible_prefixes: list[str]
) -> list[str]:
    errors: list[str] = []
    if set(changed_paths) != set(allowed_paths):
        errors.append("isolated_diff_paths")
    errors.extend(
        f"visible_ui:{path}"
        for path in changed_paths
        if any(path.startswith(prefix) for prefix in visible_prefixes)
    )
    return errors


def _validate_snapshot_semantics(role: str, path: Path) -> None:
    if role == "manifest_schema":
        value = _read_object(path)
        if "$schema" not in value or "oneOf" not in value or "$defs" not in value:
            raise ValueError("manifest_schema_semantics")
        return
    if role == "product_facts_snapshot":
        value = _read_object(path)
        required = {
            "brands",
            "strategy",
            "trial",
            "engines",
            "platform_scope",
            "network_defaults",
            "legal",
            "operations",
        }
        if not required.issubset(value):
            raise ValueError("product_facts_semantics")
        return
    if role == "reason_code_draft":
        value = _read_object(path)
        entries = value.get("entries")
        if value.get("catalog_version") != "1.2.0" or not isinstance(entries, list):
            raise ValueError("reason_code_semantics")
        codes = [item.get("code") for item in entries if isinstance(item, dict)]
        if len(codes) != len(entries) or len(set(codes)) != len(codes):
            raise ValueError("reason_code_uniqueness")
        return
    if role == "motion_semantics":
        source = path.read_text(encoding="utf-8")
        required_markers = (
            "abstract final class PokrovMotionTokens",
            "Duration(milliseconds: 120)",
            "Duration(milliseconds: 240)",
            "debugLoopingOverride",
            "FLUTTER_TEST",
            "disableAnimations ? Duration.zero : value",
        )
        if any(marker not in source for marker in required_markers):
            raise ValueError("motion_semantics")
        return
    raise ValueError(f"unsupported_snapshot_role:{role}")


def _validate_contract_data(root: Path, contract: dict[str, Any]) -> int:
    errors: list[str] = []

    def require(condition: bool, field: str) -> None:
        if not condition:
            errors.append(field)

    require(contract.get("schema") == "pokrov.release-1.2.0.pr00-freeze/v2", "schema")
    require(contract.get("state") == "PRE_CANDIDATE_LOCAL", "state")
    require(contract.get("candidate_created") is False, "candidate_created")
    require(contract.get("promotion_authorized") is False, "promotion_authorized")
    source_plan = contract.get("source_plan", {})
    if not isinstance(source_plan, dict):
        source_plan = {}
    require(set(source_plan.get("acceptance", [])) == EXPECTED_ACCEPTANCE, "acceptance")

    branches = contract.get("branches", {})
    if not isinstance(branches, dict):
        branches = {}
    for name, expected in EXPECTED_BRANCHES.items():
        actual = branches.get(name, {})
        require(isinstance(actual, dict), f"branches.{name}")
        if isinstance(actual, dict):
            for field, value in expected.items():
                require(actual.get(field) == value, f"branches.{name}.{field}")
    core = branches.get("core", {})
    index = branches.get("release_index", {})
    require(isinstance(core, dict), "branches.core")
    require(isinstance(index, dict), "branches.release_index")
    if isinstance(core, dict):
        require(core.get("promotion_branch") == "main", "branches.core.promotion")
        require(
            core.get("release_branch_condition") == "ONLY_IF_ABI_CHANGES",
            "branches.core.condition",
        )
    if isinstance(index, dict):
        require(index.get("promotion_branch") == "main", "branches.index.promotion")
        require(
            index.get("release_creation_condition") == "ONLY_AFTER_SIGNED_ARTIFACTS",
            "branches.index.condition",
        )

    flags = contract.get("flags", {})
    if not isinstance(flags, dict):
        flags = {}
    expected_flags = {
        "product_target": "1.2.0",
        "platform_build": 30,
        "candidate_created": False,
        "promotion_authorized": False,
        "visible_ui_change_allowed_in_pr00": False,
        "abi_v3_blocks_1_2_0": False,
        "linux_shipped_in_1_2_0": False,
        "public_release_index_published": False,
    }
    for field, value in expected_flags.items():
        require(flags.get(field) == value, f"flags.{field}")

    snapshots = contract.get("snapshots", [])
    require(isinstance(snapshots, list) and len(snapshots) == 4, "snapshots")
    roles: set[str] = set()
    if isinstance(snapshots, list):
        for position, item in enumerate(snapshots):
            if not isinstance(item, dict):
                errors.append(f"snapshots.{position}")
                continue
            role = str(item.get("role") or "")
            roles.add(role)
            relative = item.get("path")
            source_revision = str(item.get("source_revision") or "")
            source_blob = str(item.get("source_git_blob") or "")
            require(
                SHA1_RE.fullmatch(source_revision) is not None,
                f"snapshots.{position}.source_revision",
            )
            require(
                SHA1_RE.fullmatch(source_blob) is not None,
                f"snapshots.{position}.source_blob",
            )
            require(isinstance(relative, str), f"snapshots.{position}.path")
            if not isinstance(relative, str):
                continue
            path = root / relative
            require(path.is_file(), f"snapshots.{position}.file")
            if not path.is_file():
                continue
            require(
                path.stat().st_size == item.get("size"), f"snapshots.{position}.size"
            )
            declared_sha = str(item.get("sha256") or "")
            require(
                SHA256_RE.fullmatch(declared_sha) is not None,
                f"snapshots.{position}.sha256_format",
            )
            require(_sha256(path) == declared_sha, f"snapshots.{position}.sha256")
            try:
                _validate_snapshot_semantics(role, path)
            except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
                errors.append(str(exc))
    require(
        roles
        == {
            "manifest_schema",
            "product_facts_snapshot",
            "reason_code_draft",
            "motion_semantics",
        },
        "snapshot_roles",
    )
    if errors:
        raise ValueError("PR00_CONTRACT_INVALID: " + ", ".join(errors))
    return len(snapshots)


def validate(*, root: Path, base_ref: str) -> dict[str, Any]:
    contract = _read_object(root / CONTRACT_PATH)
    snapshot_count = _validate_contract_data(root, contract)
    errors: list[str] = []

    def require(condition: bool, field: str) -> None:
        if not condition:
            errors.append(field)

    isolated = contract.get("isolated_pr", {})
    if not isinstance(isolated, dict):
        isolated = {}
    expected_base = str(isolated.get("target_revision") or "").lower()
    head = _git(root, "rev-parse", "HEAD").lower()
    resolved_base = _git(root, "rev-parse", base_ref).lower()
    merge_base = _git(root, "merge-base", base_ref, "HEAD").lower()
    branch = _current_branch(root)
    require(branch == "codex/1.2.0-pr00-true", "branch")
    require(resolved_base == expected_base, "target_revision")
    require(merge_base == expected_base, "merge_base")
    require(
        _git(root, "rev-list", "--count", f"{expected_base}..HEAD") == "1",
        "single_commit",
    )
    require(_git(root, "rev-parse", "HEAD^").lower() == expected_base, "parent")
    require(
        not _git(root, "status", "--porcelain", "--untracked-files=all"), "worktree"
    )

    changed_paths = [
        line
        for line in _git(
            root, "diff", "--name-only", f"{expected_base}..HEAD"
        ).splitlines()
        if line
    ]
    allowed = isolated.get("allowed_paths", [])
    visible = isolated.get("visible_ui_prefixes", [])
    if not isinstance(allowed, list) or not isinstance(visible, list):
        errors.append("isolated_diff_contract")
    else:
        errors.extend(_diff_policy_errors(changed_paths, allowed, visible))
    require(contract.get("hosted_required_checks") == "NOT_RUN", "hosted_status")
    require(contract.get("candidate_eligible") is False, "candidate_eligible")
    if errors:
        raise ValueError("PR00_RELEASE_BASE_INVALID: " + ", ".join(errors))
    return {
        "status": "PASS_RELEASE_BASE_ISOLATED_NO_VISIBLE_UI",
        "revision": head,
        "target_revision": expected_base,
        "merge_base": merge_base,
        "changed_paths": changed_paths,
        "visible_ui_paths": 0,
        "snapshot_count": snapshot_count,
        "hosted_required_checks": "NOT_RUN",
        "candidate_created": False,
        "candidate_eligible": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--base-ref", default="origin/master")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = validate(root=args.root.resolve(), base_ref=args.base_ref)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

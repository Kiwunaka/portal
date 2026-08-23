"""Validate the isolated POKROV 1.2.0 PR-00 freeze evidence commit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = Path(
    "docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/"
    "evidence/013K-pr00-isolated/pr00-freeze.json"
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


def _git_identity(root: Path) -> dict[str, str]:
    porcelain = _git(root, "status", "--porcelain", "--untracked-files=all")
    return {
        "revision": _git(root, "rev-parse", "HEAD").lower(),
        "branch": _git(root, "branch", "--show-current"),
        "working_tree_state": "dirty" if porcelain else "clean",
    }


def _diff_policy_errors(
    changed_paths: list[str], allowed_paths: list[str], visible_prefixes: list[str]
) -> list[str]:
    errors: list[str] = []
    if set(changed_paths) != set(allowed_paths):
        errors.append("isolated_diff_paths")
    for path in changed_paths:
        if any(path.startswith(prefix) for prefix in visible_prefixes):
            errors.append(f"visible_ui:{path}")
    return errors


def validate(
    *,
    platform_root: Path,
    client_root: Path,
    core_root: Path,
    release_index_root: Path,
) -> dict[str, Any]:
    evidence = _read_object(platform_root / EVIDENCE_PATH)
    errors: list[str] = []

    def require(condition: bool, field: str) -> None:
        if not condition:
            errors.append(field)

    require(evidence.get("schema") == "pokrov.release-1.2.0.pr00-freeze/v1", "schema")
    require(evidence.get("product_version") == "1.2.0", "product_version")
    require(evidence.get("state") == "PRE_CANDIDATE_LOCAL", "state")
    require(evidence.get("candidate_created") is False, "candidate_created")
    require(evidence.get("promotion_authorized") is False, "promotion_authorized")
    require(
        set(evidence.get("source_plan_acceptance", [])) == EXPECTED_ACCEPTANCE,
        "source_plan_acceptance",
    )

    repositories = evidence.get("repositories", {})
    if not isinstance(repositories, dict):
        repositories = {}
    roots = {
        "platform": platform_root,
        "client": client_root,
        "core": core_root,
        "release_index": release_index_root,
    }
    identities = {name: _git_identity(root) for name, root in roots.items()}
    platform_contract = repositories.get("platform", {})
    if not isinstance(platform_contract, dict):
        platform_contract = {}
    diff_base = str(platform_contract.get("diff_base") or "").lower()
    require(
        identities["platform"]["branch"] == "codex/1.2.0-pr00-freeze",
        "platform.proof_branch",
    )
    require(
        _git(platform_root, "rev-parse", "HEAD^").lower() == diff_base,
        "platform.diff_base",
    )
    require(
        _git(platform_root, "rev-list", "--count", f"{diff_base}..HEAD") == "1",
        "platform.single_commit",
    )
    for name in ("client", "core", "release_index"):
        contract = repositories.get(name, {})
        if not isinstance(contract, dict):
            contract = {}
        require(
            identities[name]["revision"] == str(contract.get("revision") or ""),
            f"{name}.revision",
        )
        require(
            contract.get("promotion_branch")
            == ("master" if name == "platform" else "main"),
            f"{name}.promotion_branch",
        )
    require(
        platform_contract.get("promotion_branch") == "master",
        "platform.promotion_branch",
    )
    for name, identity in identities.items():
        require(identity["working_tree_state"] == "clean", f"{name}.worktree")

    canonical_inputs = evidence.get("canonical_inputs", [])
    require(isinstance(canonical_inputs, list), "canonical_inputs")
    if isinstance(canonical_inputs, list):
        for position, item in enumerate(canonical_inputs):
            if not isinstance(item, dict):
                errors.append(f"canonical_inputs.{position}")
                continue
            repo = item.get("repo")
            root = roots.get(repo)
            relative = item.get("path")
            if root is None or not isinstance(relative, str):
                errors.append(f"canonical_inputs.{position}.path")
                continue
            path = root / relative
            require(path.is_file(), f"canonical_inputs.{position}.file")
            if path.is_file():
                require(
                    path.stat().st_size == item.get("size"),
                    f"canonical_inputs.{position}.size",
                )
                require(
                    _sha256(path) == item.get("sha256"),
                    f"canonical_inputs.{position}.sha256",
                )

    flags = evidence.get("expected_flags", {})
    if not isinstance(flags, dict):
        flags = {}
    handoff = _read_object(client_root / "config/release-handoff.seed.json")
    handoff_target = handoff.get("release_truth", {}).get("development_target", {})
    runtime = _read_object(client_root / "config/runtime-artifacts.seed.json").get(
        "core", {}
    )
    runtime_target = runtime.get("development_target", {})
    provenance = runtime.get("artifact_provenance", {})
    index_contract = _read_object(release_index_root / "release-index.contract.json")
    index_target = index_contract.get("development_target", {})
    keyring = _read_object(release_index_root / index_contract["trusted_keyring_path"])
    require(
        handoff_target.get("product_version") == flags.get("product_target"),
        "flags.product_target",
    )
    require(
        handoff_target.get("platform_build") == flags.get("platform_build"),
        "flags.platform_build",
    )
    require(
        handoff_target.get("state") == flags.get("client_state"), "flags.client_state"
    )
    require(handoff_target.get("candidate_created") is False, "flags.client_candidate")
    require(
        runtime_target.get("version") == flags.get("core_target"), "flags.core_target"
    )
    require(
        runtime_target.get("artifact_state") == flags.get("core_artifact_state"),
        "flags.core_artifact_state",
    )
    require(runtime_target.get("candidate_created") is False, "flags.core_candidate")
    require(provenance.get("promotion_authorized") is False, "flags.core_promotion")
    require(
        index_target.get("state") == flags.get("release_index_state"),
        "flags.index_state",
    )
    require(index_target.get("candidate_created") is False, "flags.index_candidate")
    require(index_target.get("promotion_authorized") is False, "flags.index_promotion")
    require(
        repositories.get("release_index", {}).get("published") is False,
        "flags.index_published",
    )
    active_keys = [
        key
        for key in keyring.get("keys", [])
        if isinstance(key, dict) and key.get("state") == "active"
    ]
    require(
        len(active_keys) == flags.get("release_index_active_signing_keys"),
        "flags.index_active_signing_keys",
    )

    diff = evidence.get("isolated_diff", {})
    if not isinstance(diff, dict):
        diff = {}
    changed_paths = [
        line
        for line in _git(
            platform_root, "diff", "--name-only", f"{diff_base}..HEAD"
        ).splitlines()
        if line
    ]
    allowed_paths = diff.get("allowed_paths", [])
    visible_prefixes = diff.get("visible_ui_prefixes", [])
    if not isinstance(allowed_paths, list) or not isinstance(visible_prefixes, list):
        errors.append("isolated_diff.contract")
    else:
        errors.extend(
            _diff_policy_errors(changed_paths, allowed_paths, visible_prefixes)
        )
    require(evidence.get("hosted_required_checks") == "NOT_RUN", "hosted_status")
    require(evidence.get("candidate_eligible") is False, "candidate_eligible")
    if errors:
        raise ValueError("PR00_FREEZE_INVALID: " + ", ".join(errors))
    return {
        "status": "PASS_LOCAL_ISOLATED_NO_VISIBLE_UI",
        "platform_revision": identities["platform"]["revision"],
        "diff_base": diff_base,
        "changed_paths": changed_paths,
        "canonical_input_count": len(canonical_inputs),
        "hosted_required_checks": "NOT_RUN",
        "candidate_created": False,
        "candidate_eligible": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform-root", type=Path, default=ROOT)
    parser.add_argument("--client-root", type=Path, required=True)
    parser.add_argument("--core-root", type=Path, required=True)
    parser.add_argument("--release-index-root", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = validate(
            platform_root=args.platform_root.resolve(),
            client_root=args.client_root.resolve(),
            core_root=args.core_root.resolve(),
            release_index_root=args.release_index_root.resolve(),
        )
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

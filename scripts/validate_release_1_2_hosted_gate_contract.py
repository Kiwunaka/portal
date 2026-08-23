"""Validate the exact POKROV 1.2.0 hosted client gate control commit."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = Path(
    "docs/developer/work-orders/2026-08-23--release-1.2.0-hosted-client-gate/"
    "HOSTED-CLIENT-GATE.json"
)
WORKFLOW_PATH = Path(".github/workflows/release-1.2.0-hosted-client-gate.yml")
EXPECTED_REVISIONS = {
    "platform": "9b9467c7ad788298dd51de2d5c769d13be5a12b3",
    "client": "b783f6e075c60be42668b5b896e714b96a425156",
    "core": "fcb3c8bbc6efdeed284417369aacb522722ebfa2",
}
EXPECTED_REPOSITORIES = {
    "platform": "Kiwunaka/portal",
    "client": "Kiwunaka/POKROV-app",
    "core": "Kiwunaka/pokrov-core",
}
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


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


def _workflow_contract_errors(source: str) -> list[str]:
    required = (
        "runs-on: ubuntu-24.04",
        "timeout-minutes: 60",
        "POKROV_RELEASE_HEAD_REF: ${{ github.head_ref || github.ref_name }}",
        "POKROV_RELEASE_CLIENT_DEPLOY_KEY: ${{ secrets.POKROV_RELEASE_CLIENT_DEPLOY_KEY }}",
        "repository: Kiwunaka/portal",
        "ref: ${{ steps.tuple.outputs.platform_revision }}",
        "repository: Kiwunaka/POKROV-app",
        "ref: ${{ steps.tuple.outputs.client_revision }}",
        "ssh-key: ${{ secrets.POKROV_RELEASE_CLIENT_DEPLOY_KEY }}",
        "repository: Kiwunaka/pokrov-core",
        "ref: ${{ steps.tuple.outputs.core_revision }}",
        "actions/setup-java@cf277c60eb25467037889841efdb72551f06f6c3",
        "subosito/flutter-action@1a449444c387b1966244ae4d4f8c696479add0b2",
        'flutter-version: "3.38.5"',
        "./scripts/validate-seed.ps1",
        "./scripts/run-tests.ps1",
        "git -C platform rev-parse HEAD",
        "git -C client rev-parse HEAD",
        "git -C core rev-parse HEAD",
    )
    errors = [
        f"workflow_missing:{fragment}"
        for fragment in required
        if fragment not in source
    ]
    forbidden = (
        "git push",
        "gh pr create",
        "release_orchestrator.py",
        "remote_deploy",
        "--allow-missing-client-root",
    )
    errors.extend(
        f"workflow_forbidden:{fragment}" for fragment in forbidden if fragment in source
    )
    return errors


def _validate_contract_data(root: Path, contract: dict[str, Any]) -> dict[str, str]:
    errors: list[str] = []

    def require(condition: bool, field: str) -> None:
        if not condition:
            errors.append(field)

    require(
        contract.get("schema") == "pokrov.release-1.2.0.hosted-client-gate/v1",
        "schema",
    )
    require(contract.get("state") == "PRE_CANDIDATE_LOCAL", "state")
    require(contract.get("candidate_created") is False, "candidate_created")
    require(contract.get("promotion_authorized") is False, "promotion_authorized")
    control = contract.get("control", {})
    if not isinstance(control, dict):
        control = {}
    require(control.get("repository") == "Kiwunaka/portal", "control.repository")
    require(
        control.get("branch") == "codex/1.2.0-hosted-gate-control", "control.branch"
    )
    require(control.get("target_branch") == "master", "control.target_branch")
    require(
        control.get("target_revision") == "280ed9157f5804d4bc719cb8d6cab471caafb937",
        "control.target_revision",
    )
    require(control.get("single_commit_required") is True, "control.single_commit")

    source_tuple = contract.get("source_tuple", {})
    if not isinstance(source_tuple, dict):
        source_tuple = {}
    for name, expected_revision in EXPECTED_REVISIONS.items():
        item = source_tuple.get(name, {})
        require(isinstance(item, dict), f"source_tuple.{name}")
        if not isinstance(item, dict):
            continue
        revision = str(item.get("revision") or "")
        require(
            item.get("repository") == EXPECTED_REPOSITORIES[name],
            f"source_tuple.{name}.repository",
        )
        require(revision == expected_revision, f"source_tuple.{name}.revision")
        require(
            SHA1_RE.fullmatch(revision) is not None,
            f"source_tuple.{name}.revision_format",
        )
    private_checkout = contract.get("private_checkout", {})
    if not isinstance(private_checkout, dict):
        private_checkout = {}
    require(
        private_checkout.get("secret_name") == "POKROV_RELEASE_CLIENT_DEPLOY_KEY",
        "private_checkout.secret_name",
    )
    require(
        private_checkout.get("credential_type") == "read_only_ssh_deploy_key",
        "private_checkout.credential_type",
    )
    require(
        private_checkout.get("required_repository") == "Kiwunaka/POKROV-app",
        "private_checkout.repository",
    )
    require(
        private_checkout.get("required_permission") == "contents:read",
        "private_checkout.permission",
    )
    require(
        private_checkout.get("private_key_or_token_material_in_repository") is False,
        "private_checkout.no_material",
    )
    toolchain = contract.get("toolchain", {})
    if not isinstance(toolchain, dict):
        toolchain = {}
    require(toolchain.get("runner") == "ubuntu-24.04", "toolchain.runner")
    require(toolchain.get("python") == "3.12", "toolchain.python")
    require(toolchain.get("java") == "17", "toolchain.java")
    require(toolchain.get("flutter") == "3.38.5", "toolchain.flutter")
    require(contract.get("hosted_execution") == "NOT_RUN", "hosted_execution")
    require(contract.get("candidate_eligible") is False, "candidate_eligible")
    workflow = root / WORKFLOW_PATH
    require(workflow.is_file(), "workflow.file")
    if workflow.is_file():
        errors.extend(_workflow_contract_errors(workflow.read_text(encoding="utf-8")))
    if errors:
        raise ValueError("HOSTED_GATE_CONTRACT_INVALID: " + ", ".join(errors))
    return dict(EXPECTED_REVISIONS)


def validate(*, root: Path, base_ref: str) -> dict[str, Any]:
    contract = _read_object(root / CONTRACT_PATH)
    revisions = _validate_contract_data(root, contract)
    errors: list[str] = []

    def require(condition: bool, field: str) -> None:
        if not condition:
            errors.append(field)

    control = contract["control"]
    expected_base = str(control["target_revision"]).lower()
    branch = _current_branch(root)
    head = _git(root, "rev-parse", "HEAD").lower()
    resolved_base = _git(root, "rev-parse", base_ref).lower()
    merge_base = _git(root, "merge-base", base_ref, "HEAD").lower()
    require(branch == control["branch"], "branch")
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
    isolated = contract.get("isolated_diff", {})
    if not isinstance(isolated, dict):
        isolated = {}
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
    if errors:
        raise ValueError("HOSTED_GATE_CONTROL_INVALID: " + ", ".join(errors))
    return {
        "status": "PASS_EXACT_HOSTED_GATE_CONTROL_LOCAL",
        "revision": head,
        "target_revision": expected_base,
        "source_tuple": revisions,
        "changed_paths": changed_paths,
        "visible_ui_paths": 0,
        "hosted_execution": "NOT_RUN",
        "candidate_created": False,
        "candidate_eligible": False,
    }


def _emit_github_outputs(path: Path, revisions: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        for name in ("platform", "client", "core"):
            stream.write(f"{name}_revision={revisions[name]}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--base-ref", default="origin/master")
    parser.add_argument("--emit-github-output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = validate(root=args.root.resolve(), base_ref=args.base_ref)
        if args.emit_github_output is not None:
            _emit_github_outputs(args.emit_github_output, result["source_tuple"])
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

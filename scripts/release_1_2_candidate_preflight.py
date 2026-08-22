"""Build a read-only POKROV 1.2.0 exact-candidate preflight report."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_VERSION = "1.2.0"
TARGET_BUILD = 30
CORE_TARGET_VERSION = "1.1.0"
VALID_INDEXES = {f"I{number}" for number in range(6)}
VALID_STAGES = {"pre_freeze", "candidate", "external", "deferred"}
VALID_EXTERNAL_GATES = {"pre_candidate", "post_candidate"}
STAGE_POLICY_RELATIVE_PATH = Path("shared/release-1.2.0-candidate-stage-policy.json")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _git_identity(repo_root: Path) -> dict[str, Any]:
    revision = (
        subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        .stdout.strip()
        .lower()
    )
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()
    porcelain = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()
    return {
        "revision": revision,
        "branch": branch,
        "working_tree_state": "dirty" if porcelain else "clean",
    }


def _pubspec_version(path: Path) -> str:
    match = re.search(
        r"^version:\s*([^\s]+)\s*$", path.read_text(encoding="utf-8"), re.MULTILINE
    )
    if match is None:
        raise ValueError(f"missing version in {path}")
    return match.group(1)


def _load_ledger(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    keys: set[tuple[str, str]] = set()
    for row in rows:
        key = (row["plan"], row["id"])
        if key in keys:
            raise ValueError(f"duplicate ledger key {key}")
        keys.add(key)
        if row["index"] not in VALID_INDEXES:
            raise ValueError(f"invalid index for {key}: {row['index']}")
    if len(rows) != 377:
        raise ValueError(f"expected 377 ledger rows, got {len(rows)}")
    return rows


def _load_stage_policy(
    path: Path, rows: list[dict[str, str]]
) -> tuple[dict[str, Any], dict[tuple[str, str], dict[str, str]]]:
    policy = _read_json(path)
    if policy.get("schema") != "pokrov.release-1.2.0.row-stage-policy/v1":
        raise ValueError("candidate stage policy schema is unsupported")
    if policy.get("default_stage") != "pre_freeze":
        raise ValueError("candidate stage policy must fail safe to pre_freeze")
    stages = policy.get("stages")
    if not isinstance(stages, dict) or set(stages) != VALID_STAGES:
        raise ValueError("candidate stage policy must define the four exact stages")
    if any(
        not isinstance(value, str) or not value.strip() for value in stages.values()
    ):
        raise ValueError("candidate stage descriptions must be non-empty strings")

    ledger_keys = {(row["plan"], row["id"]) for row in rows}
    assignments = {
        key: {
            "stage": "pre_freeze",
            "reason": "Fail-safe default: local I3 is required before candidate creation.",
        }
        for key in ledger_keys
    }
    overrides = policy.get("overrides")
    if not isinstance(overrides, list):
        raise ValueError("candidate stage policy overrides must be a list")
    seen: set[tuple[str, str]] = set()
    for position, raw_override in enumerate(overrides):
        if not isinstance(raw_override, dict):
            raise ValueError(f"candidate stage override {position} must be an object")
        allowed_fields = {"plan", "id", "stage", "reason", "external_gate"}
        extra_fields = set(raw_override) - allowed_fields
        if extra_fields:
            raise ValueError(
                f"candidate stage override {position} has unsupported fields: "
                f"{sorted(extra_fields)}"
            )
        plan = raw_override.get("plan")
        identifier = raw_override.get("id")
        stage = raw_override.get("stage")
        reason = raw_override.get("reason")
        if not all(
            isinstance(value, str) and value.strip()
            for value in (plan, identifier, stage, reason)
        ):
            raise ValueError(
                f"candidate stage override {position} has an empty required field"
            )
        key = (plan, identifier)
        if key not in ledger_keys:
            raise ValueError(
                f"candidate stage override references unknown ledger key {key}"
            )
        if key in seen:
            raise ValueError(f"duplicate candidate stage override for {key}")
        seen.add(key)
        if stage not in VALID_STAGES:
            raise ValueError(f"invalid candidate stage for {key}: {stage}")
        external_gate = raw_override.get("external_gate")
        if stage == "external":
            if external_gate not in VALID_EXTERNAL_GATES:
                raise ValueError(
                    f"external candidate stage for {key} needs an exact external_gate"
                )
        elif external_gate is not None:
            raise ValueError(
                f"non-external candidate stage for {key} cannot set external_gate"
            )
        assignment = {"stage": stage, "reason": reason.strip()}
        if stage == "external":
            assignment["external_gate"] = external_gate
        assignments[key] = assignment

    return (
        {
            "schema": policy["schema"],
            "path": STAGE_POLICY_RELATIVE_PATH.as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "default_stage": policy["default_stage"],
            "override_count": len(overrides),
            "ledger_row_count": len(assignments),
        },
        assignments,
    )


def _pending_lane(row: dict[str, str]) -> str:
    status = row["status"].upper()
    if "NOT_AUTHORIZED" in status:
        return "not_authorized"
    if "BLOCKED_BY_ACCESS" in status:
        return "blocked_by_access"
    if "BLOCKED_BY_OWNER" in status:
        return "blocked_by_owner_decision"
    if "MANUAL_OWNER_TEST" in status:
        return "manual_owner_test"
    if "NOT_REQUESTED" in status:
        return "not_requested"
    if "DEFERRED" in status:
        return "deferred"
    if "MONITOR_ONLY" in status:
        return "monitor_only"
    if row["phase"] == "P11":
        return "phase_11_local_or_candidate"
    return "local_closure_or_candidate_dependency"


def _stage_blockers(pending_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    pre_freeze = [row for row in pending_rows if row["stage"] == "pre_freeze"]
    external_pre_candidate = [
        row
        for row in pending_rows
        if row["stage"] == "external" and row.get("external_gate") == "pre_candidate"
    ]
    if pre_freeze:
        blockers.append(
            {
                "id": "ledger_pre_freeze_incomplete",
                "status": "BLOCKED_LOCAL_FREEZE",
                "detail": (
                    f"{len(pre_freeze)} explicitly staged rows remain below local I3"
                ),
            }
        )
    if external_pre_candidate:
        blockers.append(
            {
                "id": "ledger_external_pre_candidate_incomplete",
                "status": "BLOCKED_EXTERNAL_PRECONDITION",
                "detail": (
                    f"{len(external_pre_candidate)} external pre-candidate rows remain unresolved"
                ),
            }
        )
    return blockers


def _target_contract_blockers(
    *,
    versions: dict[str, str],
    handoff_target: dict[str, Any],
    core_release: dict[str, Any],
    core_target: dict[str, Any],
) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []

    def add(identifier: str, detail: str) -> None:
        blockers.append(
            {
                "id": identifier,
                "status": "BLOCKED_LOCAL_CONTRACT",
                "detail": detail,
            }
        )

    android_product = versions["android"].split("+", 1)[0]
    windows_product = versions["windows"].split("+", 1)[0]
    if android_product != windows_product:
        add("client_shell_version_drift", "Android and Windows product versions differ")
    if android_product != TARGET_VERSION or versions["app_shell"] != TARGET_VERSION:
        add(
            "client_target_version_stale",
            f"active client packages must target {TARGET_VERSION}",
        )
    expected_package = f"{TARGET_VERSION}+{TARGET_BUILD}"
    if (
        versions["android"] != expected_package
        or versions["windows"] != expected_package
    ):
        add(
            "client_build_number_drift",
            f"active shells must use exact package version {expected_package}",
        )
    if (
        str(handoff_target.get("product_version") or "") != TARGET_VERSION
        or handoff_target.get("platform_build") != TARGET_BUILD
        or str(handoff_target.get("package_version") or "") != expected_package
        or str(handoff_target.get("state") or "") != "PRE_CANDIDATE_LOCAL"
        or handoff_target.get("candidate_created") is not False
    ):
        add(
            "client_handoff_target_invalid",
            "release-handoff development target is not the exact pre-candidate contract",
        )
    if (
        str(core_release.get("version") or "") != CORE_TARGET_VERSION
        or str(core_release.get("state") or "") != "PRE_CANDIDATE_LOCAL"
        or core_release.get("candidate_created") is not False
    ):
        add(
            "core_source_target_invalid",
            f"Core source must identify {CORE_TARGET_VERSION} PRE_CANDIDATE_LOCAL",
        )
    if (
        str(core_target.get("required_for_product") or "") != TARGET_VERSION
        or str(core_target.get("version") or "") != CORE_TARGET_VERSION
        or str(core_target.get("release_tag") or "") != f"v{CORE_TARGET_VERSION}"
        or str(core_target.get("state") or "") != "PRE_CANDIDATE_LOCAL"
        or core_target.get("candidate_created") is not False
        or str(core_target.get("artifact_state") or "") != "pending"
    ):
        add(
            "client_core_target_invalid",
            "client Core development target disagrees with the pre-candidate source contract",
        )
    return blockers


def build_report(
    *,
    platform_root: Path,
    client_root: Path,
    core_root: Path,
    release_index_root: Path | None,
) -> dict[str, Any]:
    ledger_path = (
        platform_root
        / "docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/EXECUTION-LEDGER.csv"
    )
    rows = _load_ledger(ledger_path)
    stage_policy, stage_assignments = _load_stage_policy(
        platform_root / STAGE_POLICY_RELATIVE_PATH, rows
    )
    pending = [row for row in rows if int(row["index"][1:]) < 3]
    sources = {
        "platform": _git_identity(platform_root),
        "client": _git_identity(client_root),
        "core": _git_identity(core_root),
    }
    blockers: list[dict[str, str]] = []
    for name, value in sources.items():
        if value["working_tree_state"] != "clean":
            blockers.append(
                {
                    "id": f"{name}_worktree_dirty",
                    "status": "BLOCKED_LOCAL_FREEZE",
                    "detail": "exact candidate identity requires a clean committed revision",
                }
            )

    release_index: dict[str, Any]
    if release_index_root is None or not (release_index_root / ".git").exists():
        release_index = {"status": "BLOCKED_BY_ACCESS"}
        blockers.append(
            {
                "id": "release_index_missing",
                "status": "BLOCKED_BY_ACCESS",
                "detail": "public release-index repository/revision is unavailable",
            }
        )
    else:
        release_index = {"status": "AVAILABLE", **_git_identity(release_index_root)}
        if release_index["working_tree_state"] != "clean":
            blockers.append(
                {
                    "id": "release_index_worktree_dirty",
                    "status": "BLOCKED_LOCAL_FREEZE",
                    "detail": "release-index revision must be clean",
                }
            )

    versions = {
        "target": TARGET_VERSION,
        "android": _pubspec_version(client_root / "apps/android_shell/pubspec.yaml"),
        "windows": _pubspec_version(client_root / "apps/windows_shell/pubspec.yaml"),
        "app_shell": _pubspec_version(client_root / "packages/app_shell/pubspec.yaml"),
    }
    core_release = _read_json(core_root / "config/release.json")
    runtime_seed = _read_json(client_root / "config/runtime-artifacts.seed.json")[
        "core"
    ]
    handoff_target = _read_json(client_root / "config/release-handoff.seed.json")[
        "release_truth"
    ]["development_target"]
    core_target = runtime_seed.get("development_target", {})
    if not isinstance(core_target, dict):
        core_target = {}
    blockers.extend(
        _target_contract_blockers(
            versions=versions,
            handoff_target=handoff_target,
            core_release=core_release,
            core_target=core_target,
        )
    )
    core_state = {
        "source_version": str(core_release.get("version") or ""),
        "source_state": str(core_release.get("state") or ""),
        "source_revision": sources["core"]["revision"],
        "seed_version": str(runtime_seed.get("version") or ""),
        "target_version": str(core_target.get("version") or ""),
        "target_state": str(core_target.get("state") or ""),
        "seed_source_revision": str(runtime_seed.get("source_commit") or "").lower(),
        "seed_structured_event_artifact": str(
            runtime_seed.get("desktop_abi", {})
            .get("structured_events", {})
            .get("exact_replacement_artifact", "")
        ),
    }
    if core_state["seed_source_revision"] != core_state["source_revision"]:
        blockers.append(
            {
                "id": "client_core_seed_revision_stale",
                "status": "BLOCKED_LOCAL_ARTIFACT",
                "detail": "client runtime seed does not bind the active Core source revision",
            }
        )
    if core_state["seed_structured_event_artifact"] != "ready":
        blockers.append(
            {
                "id": "core_replacement_artifact_pending",
                "status": "BLOCKED_LOCAL_ARTIFACT",
                "detail": "exact structured-event Core replacement artifact is not ready",
            }
        )

    pending_rows: list[dict[str, Any]] = []
    for row in pending:
        assignment = stage_assignments[(row["plan"], row["id"])]
        pending_row: dict[str, Any] = {
            "plan": row["plan"],
            "id": row["id"],
            "phase": row["phase"],
            "index": row["index"],
            "status": row["status"],
            "lane": _pending_lane(row),
            "stage": assignment["stage"],
            "stage_reason": assignment["reason"],
            "summary": row["summary"],
            "next_action": row["next_action"],
        }
        if "external_gate" in assignment:
            pending_row["external_gate"] = assignment["external_gate"]
        pending_rows.append(pending_row)
    blockers.extend(_stage_blockers(pending_rows))
    lane_counts: dict[str, int] = {}
    stage_counts: dict[str, int] = {}
    for row in pending_rows:
        lane_counts[row["lane"]] = lane_counts.get(row["lane"], 0) + 1
        stage_counts[row["stage"]] = stage_counts.get(row["stage"], 0) + 1
    external_pre_candidate_count = sum(
        row.get("external_gate") == "pre_candidate" for row in pending_rows
    )

    return {
        "schema": "pokrov.release-1.2.candidate-preflight/v1",
        "captured_at_utc": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "status": "BLOCKED" if blockers else "READY_LOCAL_FREEZE",
        "candidate_created": False,
        "candidate_proven": False,
        "promotion_authorized": False,
        "sources": sources,
        "release_index": release_index,
        "versions": versions,
        "core": core_state,
        "stage_policy": stage_policy,
        "ledger": {
            "total": len(rows),
            "below_i3": len(pending_rows),
            "pre_freeze_rows_below_i3": stage_counts.get("pre_freeze", 0),
            "candidate_rows_below_i3": stage_counts.get("candidate", 0),
            "external_rows_below_i3": stage_counts.get("external", 0),
            "external_pre_candidate_rows_below_i3": external_pre_candidate_count,
            "deferred_rows_below_i3": stage_counts.get("deferred", 0),
            "pending_stage_counts": dict(sorted(stage_counts.items())),
            "pending_lane_counts": dict(sorted(lane_counts.items())),
            "pending_rows": pending_rows,
        },
        "blockers": blockers,
        "evidence_ceiling": "LOCAL_READ_ONLY_PREFLIGHT",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--client-root", type=Path, required=True)
    parser.add_argument("--core-root", type=Path, required=True)
    parser.add_argument("--release-index-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--expect-blocked",
        action="store_true",
        help="Return success only when the honest current status is BLOCKED.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = build_report(
            platform_root=args.platform_root.resolve(),
            client_root=args.client_root.resolve(),
            core_root=args.core_root.resolve(),
            release_index_root=args.release_index_root.resolve()
            if args.release_index_root
            else None,
        )
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"CANDIDATE_PREFLIGHT_ERROR: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "blockers": len(report["blockers"]),
                "candidate_created": False,
                "candidate_rows_below_i3": report["ledger"]["candidate_rows_below_i3"],
                "deferred_rows_below_i3": report["ledger"]["deferred_rows_below_i3"],
                "external_pre_candidate_rows_below_i3": report["ledger"][
                    "external_pre_candidate_rows_below_i3"
                ],
                "ledger_below_i3": report["ledger"]["below_i3"],
                "output": str(output),
                "pre_freeze_rows_below_i3": report["ledger"][
                    "pre_freeze_rows_below_i3"
                ],
                "status": report["status"],
            },
            sort_keys=True,
        )
    )
    if args.expect_blocked:
        return 0 if report["status"] == "BLOCKED" else 1
    return 0 if report["status"] == "READY_LOCAL_FREEZE" else 1


if __name__ == "__main__":
    raise SystemExit(main())

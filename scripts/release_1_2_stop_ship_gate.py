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
            if not isinstance(fragments, list) or not fragments or not all(
                isinstance(fragment, str) and fragment for fragment in fragments
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


def _required_check_names(payload: dict[str, Any]) -> set[str]:
    required = payload.get("required_status_checks")
    if not isinstance(required, dict):
        return set()
    names = {
        item
        for item in required.get("contexts", [])
        if isinstance(item, str) and item
    }
    for item in required.get("checks", []):
        if isinstance(item, dict) and isinstance(item.get("context"), str):
            names.add(item["context"])
    return names


def _evaluate_branch_payload(
    payload: dict[str, Any],
    required_checks: list[str],
) -> tuple[str, list[str]]:
    status_checks = payload.get("required_status_checks")
    if not isinstance(status_checks, dict):
        return "FAIL", required_checks
    strict = status_checks.get("strict") is True
    present = _required_check_names(payload)
    missing = sorted(set(required_checks) - present)
    return ("PASS" if strict and not missing else "FAIL"), missing


def _query_branch_protection(
    repository: str,
    branch: str,
    required_checks: list[str],
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
        result, missing = _evaluate_branch_payload(payload, required_checks)
        return {
            "repository": repository,
            "branch": branch,
            "result": result,
            "required_checks": required_checks,
            "missing_required_checks": missing,
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


def build_report(
    *,
    registry_path: Path,
    platform_root: Path,
    client_root: Path,
    core_root: Path,
    query_github: bool,
) -> dict[str, Any]:
    registry = _read_registry(registry_path)
    roots = {
        "platform": platform_root,
        "client": client_root,
        "core": core_root,
    }
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

    local_pass = all(item["result"] == "PASS" for item in regressions)
    hosted_fail = any(
        item["result"] in {"FAIL", "FAIL_UNPROTECTED"}
        for item in hosted_controls
    )
    hosted_incomplete = any(
        item["result"] in {"BLOCKED_BY_ACCESS", "NOT_RUN"}
        for item in hosted_controls
    )
    if not local_pass or hosted_fail:
        status = "NO_GO"
    elif hosted_incomplete or manual_gates:
        status = "BLOCKED"
    else:
        status = "PASS"
    return {
        "schema": "pokrov.release-1.2.0.stop-ship-gate.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "release": "1.2.0",
        "status": status,
        "candidate_proven": False,
        "registry": str(registry_path),
        "registry_sha256": _sha256_file(registry_path),
        "expected_stop_ship_ids": sorted(EXPECTED_IDS),
        "local_regressions": regressions,
        "hosted_branch_protection": hosted_controls,
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

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


PASSISH_STATUSES = {
    "Pass",
    "Retest pass",
    "Retest Pass",
    "Retest passed",
    "Retested pass",
}

PASS_RESULT_RE = re.compile(r"\b(PASS|passed|pass)\b", re.IGNORECASE)
RUN_ID_RE = re.compile(r"\b[A-Z][A-Z0-9-]+-\d{3}\b")
TEST_REF_RE = re.compile(
    r"(?:portal_bot[\\/])?tests[\\/][A-Za-z0-9_./\\-]+\.(?:py|ts|tsx|dart|kt)"
    r"|webapp[\\/]e2e[\\/][A-Za-z0-9_./\\-]+\.ts"
    r"|POKROV-app[\\/][A-Za-z0-9_./\\-]+\.(?:dart|kt|ps1|md)"
)

OUTPUT_FIELDS = [
    "canonical_id",
    "subsystem",
    "source_tracker",
    "feature",
    "story_status",
    "evidence_tier",
    "test_ref_count",
    "test_refs",
    "missing_test_ref_count",
    "missing_test_refs",
    "has_recorded_run_id",
    "has_pass_result",
    "owner_gate",
    "retest_proof_status",
    "evidence_basis",
    "next_action",
    "updated_at",
]

ENTRYPOINT_OUTPUT_FIELDS = [
    "entry_id",
    "entry_type",
    "subsystem",
    "trigger_or_path",
    "handler_or_component",
    "code_evidence",
    "coverage_tier",
    "story_or_route_ref_count",
    "story_or_route_refs",
    "test_ref_count",
    "test_refs",
    "evidence_basis",
    "next_action",
    "updated_at",
]

SOURCE_REF_RE = re.compile(r"([A-Za-z0-9_./\\() -]+\.(?:py|tsx|ts|dart|kt|ps1|md))(?::(\d+))?")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _normalize_ref(ref: str) -> str:
    return ref.replace("\\", "/")


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _resolve_ref(repo_root: Path, ref: str) -> Path:
    if ref.startswith("POKROV-app/"):
        return repo_root.parent / ref
    return repo_root / ref


def _collect_refs(row: dict[str, str]) -> list[str]:
    text = " ".join(
        row.get(key, "")
        for key in (
            "test_method",
            "code_evidence",
            "latest_result",
            "retest_status",
            "owner_or_access_note",
        )
    )
    return _dedupe([_normalize_ref(ref) for ref in TEST_REF_RE.findall(text)])


def _combined_evidence_text(row: dict[str, str]) -> str:
    return " ".join(
        row.get(key, "")
        for key in (
            "test_method",
            "code_evidence",
            "latest_result",
            "retest_status",
            "owner_or_access_note",
        )
    )


def _collect_source_refs(text: str) -> list[tuple[str, int | None]]:
    refs: list[tuple[str, int | None]] = []
    current_path: str | None = None
    for raw_part in re.split(r"[,;\s]+", text or ""):
        part = raw_part.strip().strip('"').strip("'")
        if not part:
            continue
        match = SOURCE_REF_RE.fullmatch(part)
        if match:
            current_path = _normalize_ref(match.group(1))
            line = int(match.group(2)) if match.group(2) else None
            refs.append((current_path, line))
            continue
        if current_path and part.isdigit():
            refs.append((current_path, int(part)))
    return _dedupe_refs(refs)


def _dedupe_refs(refs: list[tuple[str, int | None]]) -> list[tuple[str, int | None]]:
    seen: set[tuple[str, int | None]] = set()
    result: list[tuple[str, int | None]] = []
    for ref in refs:
        if ref not in seen:
            seen.add(ref)
            result.append(ref)
    return result


def _source_refs_match(
    entry_refs: list[tuple[str, int | None]],
    story_refs: list[tuple[str, int | None]],
    *,
    line_tolerance: int = 3,
) -> bool:
    for entry_path, entry_line in entry_refs:
        for story_path, story_line in story_refs:
            if entry_path != story_path:
                continue
            if entry_line is None or story_line is None:
                return True
            if abs(entry_line - story_line) <= line_tolerance:
                return True
    return False


def _client_feature_dirs(refs: list[tuple[str, int | None]]) -> set[str]:
    dirs: set[str] = set()
    for path, _line in refs:
        match = re.search(r"packages/app_shell/lib/src/features/([^/]+)/", path)
        if match:
            dirs.add(match.group(1))
    return dirs


def _trigger_tokens(entry: dict[str, str]) -> list[str]:
    trigger = entry.get("trigger_or_path", "")
    tokens: list[str] = []
    patterns = (
        r"F\.data == ['\"]([^'\"]+)['\"]",
        r"F\.data\.startswith\(['\"]([^'\"]+)['\"]\)",
        r"Command\(['\"]([^'\"]+)['\"]\)",
    )
    for pattern in patterns:
        tokens.extend(match.group(1) for match in re.finditer(pattern, trigger))
    if "CommandStart()" in trigger:
        tokens.append("/start")
    if "ContentType.SUCCESSFUL_PAYMENT" in trigger:
        tokens.append("successful_payment")
    in_match = re.search(r"F\.data\.in_\(\{([^}]+)\}\)", trigger)
    if in_match:
        tokens.extend(re.findall(r"['\"]([^'\"]+)['\"]", in_match.group(1)))
    handler = entry.get("handler_or_component", "")
    if handler:
        tokens.append(handler)
    return _dedupe([token for token in tokens if token])


def _token_variants(token: str) -> set[str]:
    stripped = token.strip().strip("/")
    variants = {stripped, stripped.replace("_", " "), stripped.replace("_", "")}
    if stripped.endswith("_run"):
        base = stripped[: -len("_run")]
        variants.update({base, base.replace("_", " "), base.replace("_", "")})
    return {variant.lower() for variant in variants if variant}


def _story_text_matches_token(story: dict[str, str], token: str) -> bool:
    text = " ".join(
        story.get(key, "")
        for key in ("route_or_trigger", "feature", "user_story", "expected_behavior")
    ).lower()
    compact_text = text.replace("_", "").replace(" ", "")
    route = story.get("route_or_trigger", "").lower()
    route_parts = re.split(r"[,;\s]+", route)
    for variant in _token_variants(token):
        if variant in text or variant.replace(" ", "") in compact_text:
            return True
        for part in route_parts:
            if part.endswith("*") and variant.startswith(part[:-1].strip("/")):
                return True
    if token.startswith("/") and token.lower() in text:
        return True
    return False


def _matched_story_rows(entry: dict[str, str], stories: list[dict[str, str]]) -> list[dict[str, str]]:
    entry_type = entry.get("entry_type", "")
    entry_refs = _collect_source_refs(entry.get("code_evidence", ""))
    tokens = _trigger_tokens(entry)
    matched: list[dict[str, str]] = []
    for story in stories:
        story_refs = _collect_source_refs(story.get("code_evidence", ""))
        path_match = bool(entry_refs and story_refs and _source_refs_match(entry_refs, story_refs))
        feature_dir_match = (
            entry_type == "flutter_feature_file"
            and bool(_client_feature_dirs(entry_refs) & _client_feature_dirs(story_refs))
        )
        route_match = False
        if entry.get("trigger_or_path") and entry.get("trigger_or_path") == story.get("route_or_trigger"):
            route_match = True
        token_match = entry_type == "aiogram_handler" and any(
            _story_text_matches_token(story, token) for token in tokens
        )
        if path_match or feature_dir_match or route_match or token_match:
            matched.append(story)
    return matched


def _refs_from_rows(rows: list[dict[str, str]]) -> list[str]:
    refs: list[str] = []
    for row in rows:
        refs.extend(_collect_refs(row))
    return _dedupe(refs)


def _script_path_from_trigger(trigger: str) -> str:
    match = re.search(r"(scripts/[A-Za-z0-9_.\-]+\.py)", _normalize_ref(trigger))
    return match.group(1) if match else ""


def classify_entrypoint(
    entry: dict[str, str],
    stories: list[dict[str, str]],
    backend_routes: dict[str, dict[str, str]],
    scripts: dict[str, dict[str, str]],
    updated_at: str,
) -> dict[str, str]:
    entry_type = entry.get("entry_type", "")
    refs: list[str] = []
    story_or_route_refs: list[str] = []
    tier = "needs_story_mapping_review"
    basis = "No direct story, route, or script coverage mapping was found."
    next_action = "Map this entrypoint to a canonical story/route test or explicitly label it internal/no-op."

    if entry_type == "fastapi_route":
        route = backend_routes.get(entry.get("trigger_or_path", ""))
        if route:
            story_or_route_refs = [route.get("canonical_id", "")]
            refs = _dedupe([ref.strip() for ref in route.get("test_refs", "").split(";") if ref.strip()])
            if refs:
                tier = "direct_route_test_ref"
                basis = "FastAPI route maps to backend route coverage with direct test refs."
                next_action = "Keep route coverage current when endpoint behavior changes."
            else:
                tier = "route_mapping_no_direct_ref"
                basis = "FastAPI route maps to backend route coverage, but no direct test refs are recorded."
                next_action = "Add direct route scenario test refs."
    elif entry_type == "script_cli":
        script_path = _script_path_from_trigger(entry.get("trigger_or_path", ""))
        script = scripts.get(script_path)
        if script:
            story_or_route_refs = [script.get("script_id", "")]
            refs = _dedupe([ref.strip() for ref in script.get("test_refs", "").split(";") if ref.strip()])
            if refs:
                tier = "direct_script_test_ref"
                basis = "Script CLI maps to script workflow coverage with direct test refs."
                next_action = "Keep script workflow coverage current when operator behavior changes."
            else:
                tier = "script_mapping_no_direct_ref"
                basis = "Script CLI maps to script workflow coverage, but no direct test refs are recorded."
                next_action = "Add direct script workflow test refs."
    else:
        matches = _matched_story_rows(entry, stories)
        story_or_route_refs = [row.get("canonical_id", "") for row in matches]
        refs = _refs_from_rows(matches)
        if refs:
            tier = "direct_story_test_ref"
            basis = "Entrypoint maps to canonical story row(s) with direct test refs."
            next_action = "Keep story mapping current when handler/component behavior changes."
        elif matches:
            tier = "story_mapping_no_direct_ref"
            basis = "Entrypoint maps to story row(s), but no direct test refs are recorded."
            next_action = "Add direct story test refs or mark the story as a manual owner gate."

    return {
        "entry_id": entry.get("entry_id", ""),
        "entry_type": entry_type,
        "subsystem": entry.get("subsystem", ""),
        "trigger_or_path": entry.get("trigger_or_path", ""),
        "handler_or_component": entry.get("handler_or_component", ""),
        "code_evidence": entry.get("code_evidence", ""),
        "coverage_tier": tier,
        "story_or_route_ref_count": str(len([ref for ref in story_or_route_refs if ref])),
        "story_or_route_refs": "; ".join(ref for ref in story_or_route_refs if ref),
        "test_ref_count": str(len(refs)),
        "test_refs": "; ".join(refs),
        "evidence_basis": basis,
        "next_action": next_action,
        "updated_at": updated_at,
    }


def classify_row(repo_root: Path, row: dict[str, str], updated_at: str) -> dict[str, str]:
    text = _combined_evidence_text(row)
    refs = _collect_refs(row)
    missing_refs = [ref for ref in refs if not _resolve_ref(repo_root, ref).exists()]
    has_recorded_run_id = bool(RUN_ID_RE.search(text))
    has_pass_result = bool(PASS_RESULT_RE.search(text))
    story_status = row.get("story_status", "")
    source_tracker = row.get("source_tracker", "")
    owner_gate = (
        story_status == "Manual owner test"
        or "manual_owner_test" in text.lower()
        or "manual owner" in text.lower()
    )

    if story_status == "Manual owner test":
        tier = "manual_owner_gate"
        basis = "Story is explicitly labelled Manual owner test."
        next_action = "Run and record the owner-controlled live/device/provider check when access is available."
    elif refs and missing_refs:
        tier = "stale_file_ref"
        basis = "One or more referenced test files no longer exist."
        next_action = "Fix the referenced test mapping or add a replacement scenario test."
    elif refs:
        tier = "direct_file_ref"
        basis = "Canonical row points at existing automated test file(s)."
        next_action = "Keep mapped tests current when behavior changes."
    elif (
        source_tracker.lower().endswith(".xlsx")
        and story_status in PASSISH_STATUSES
        and has_pass_result
    ):
        tier = "imported_pass_no_file_ref"
        basis = "Imported source tracker records a pass, but no direct test file reference is machine-checkable."
        next_action = "Map this story to direct automated test file(s), or explicitly keep the imported workbook as retained evidence."
    elif has_recorded_run_id and story_status in PASSISH_STATUSES and has_pass_result:
        tier = "recorded_run_no_file_ref"
        basis = "Canonical row references a recorded passing run but no direct test file reference."
        next_action = "Add direct test file references if this story remains active."
    elif story_status in PASSISH_STATUSES and has_pass_result:
        tier = "textual_pass_no_file_ref"
        basis = "Canonical row has textual pass evidence but no direct test file reference."
        next_action = "Replace textual evidence with a direct test mapping or manual-gate label."
    else:
        tier = "weak_or_missing_evidence"
        basis = "No strong automated, imported-pass, or manual-gate evidence was detected."
        next_action = "Add a scenario test, relabel the row, or document the access blocker."

    if story_status == "Manual owner test":
        retest_proof_status = "manual_owner_gate_open"
    elif tier == "direct_file_ref" and has_pass_result and not missing_refs:
        retest_proof_status = "direct_test_ref_passed"
    elif tier == "direct_file_ref":
        retest_proof_status = "direct_test_ref_without_pass_result"
    elif tier == "stale_file_ref":
        retest_proof_status = "stale_test_ref"
    elif tier == "imported_pass_no_file_ref":
        retest_proof_status = "imported_pass_without_direct_ref"
    elif tier in {"recorded_run_no_file_ref", "textual_pass_no_file_ref"}:
        retest_proof_status = "pass_without_direct_ref"
    else:
        retest_proof_status = "weak_or_missing_retest_evidence"

    return {
        "canonical_id": row.get("canonical_id", ""),
        "subsystem": row.get("subsystem", ""),
        "source_tracker": source_tracker,
        "feature": row.get("feature", ""),
        "story_status": story_status,
        "evidence_tier": tier,
        "test_ref_count": str(len(refs)),
        "test_refs": "; ".join(refs),
        "missing_test_ref_count": str(len(missing_refs)),
        "missing_test_refs": "; ".join(missing_refs),
        "has_recorded_run_id": str(has_recorded_run_id),
        "has_pass_result": str(has_pass_result),
        "owner_gate": str(owner_gate),
        "retest_proof_status": retest_proof_status,
        "evidence_basis": basis,
        "next_action": next_action,
        "updated_at": updated_at,
    }


def build_audit(repo_root: Path, tracker_path: Path, updated_at: str) -> list[dict[str, str]]:
    rows = _read_csv(tracker_path)
    return [classify_row(repo_root, row, updated_at) for row in rows]


def build_entrypoint_audit(
    repo_root: Path,
    entrypoints_path: Path,
    tracker_path: Path,
    backend_routes_path: Path,
    script_coverage_path: Path,
    updated_at: str,
) -> list[dict[str, str]]:
    del repo_root
    entries = _read_csv(entrypoints_path)
    stories = _read_csv(tracker_path)
    backend_routes = {
        f"{row.get('method', '')} {row.get('path', '')}": row
        for row in _read_csv(backend_routes_path)
    }
    scripts = {row.get("path", ""): row for row in _read_csv(script_coverage_path)}
    return [
        classify_entrypoint(entry, stories, backend_routes, scripts, updated_at)
        for entry in entries
    ]


def write_audit(rows: list[dict[str, str]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_entrypoint_audit(rows: list[dict[str, str]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ENTRYPOINT_OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _print_summary(rows: list[dict[str, str]], out_path: Path) -> None:
    tier_counts = Counter(row["evidence_tier"] for row in rows)
    missing = sum(int(row["missing_test_ref_count"]) for row in rows)
    print(f"wrote {len(rows)} story evidence rows to {out_path}")
    for tier, count in sorted(tier_counts.items()):
        print(f"{tier}: {count}")
    print(f"missing_test_refs: {missing}")


def _print_entrypoint_summary(rows: list[dict[str, str]], out_path: Path) -> None:
    tier_counts = Counter(row["coverage_tier"] for row in rows)
    print(f"wrote {len(rows)} entrypoint coverage rows to {out_path}")
    for tier, count in sorted(tier_counts.items()):
        print(f"{tier}: {count}")


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Audit canonical POKROV user-story rows for machine-checkable test evidence."
    )
    parser.add_argument(
        "--tracker",
        default=str(repo_root / "docs" / "developer" / "pokrov-canonical-feature-tracker.csv"),
        help="Canonical feature tracker CSV.",
    )
    parser.add_argument(
        "--out",
        default=str(repo_root / "docs" / "developer" / "pokrov-story-test-evidence-audit.csv"),
        help="Output CSV path.",
    )
    parser.add_argument(
        "--entrypoints",
        default=str(repo_root / "docs" / "developer" / "pokrov-entrypoint-inventory.csv"),
        help="Entrypoint inventory CSV.",
    )
    parser.add_argument(
        "--backend-routes",
        default=str(repo_root / "docs" / "developer" / "pokrov-backend-route-coverage.csv"),
        help="Backend route coverage CSV.",
    )
    parser.add_argument(
        "--script-coverage",
        default=str(repo_root / "docs" / "developer" / "pokrov-script-workflow-coverage.csv"),
        help="Script workflow coverage CSV.",
    )
    parser.add_argument(
        "--entrypoint-out",
        default=str(repo_root / "docs" / "developer" / "pokrov-entrypoint-story-coverage.csv"),
        help="Output CSV path for entrypoint-to-story coverage.",
    )
    parser.add_argument(
        "--skip-entrypoint-audit",
        action="store_true",
        help="Only write the story evidence audit CSV.",
    )
    parser.add_argument("--updated-at", default="2026-06-27")
    args = parser.parse_args(argv)

    tracker_path = Path(args.tracker)
    out_path = Path(args.out)
    rows = build_audit(repo_root, tracker_path, args.updated_at)
    write_audit(rows, out_path)
    _print_summary(rows, out_path)
    if not args.skip_entrypoint_audit:
        entrypoint_rows = build_entrypoint_audit(
            repo_root,
            Path(args.entrypoints),
            tracker_path,
            Path(args.backend_routes),
            Path(args.script_coverage),
            args.updated_at,
        )
        entrypoint_out = Path(args.entrypoint_out)
        write_entrypoint_audit(entrypoint_rows, entrypoint_out)
        _print_entrypoint_summary(entrypoint_rows, entrypoint_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

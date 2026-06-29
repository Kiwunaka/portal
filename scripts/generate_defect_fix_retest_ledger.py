from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRACKER = REPO_ROOT / "docs" / "developer" / "pokrov-canonical-feature-tracker.csv"
DEFAULT_STORY_AUDIT = REPO_ROOT / "docs" / "developer" / "pokrov-story-test-evidence-audit.csv"
DEFAULT_OUT = REPO_ROOT / "docs" / "developer" / "pokrov-defect-fix-retest-ledger.csv"
DEFAULT_MARKDOWN_OUT = REPO_ROOT / "docs" / "developer" / "pokrov-defect-fix-retest-ledger.md"
TODAY = "2026-06-27"

FIELDS = [
    "ledger_id",
    "canonical_id",
    "subsystem",
    "surface",
    "feature",
    "route_or_trigger",
    "defect_area",
    "defect_or_issue",
    "fix_status",
    "retest_status",
    "story_status",
    "retest_proof_status",
    "closure_status",
    "proof_ref_count",
    "proof_refs",
    "next_action",
    "updated_at",
]


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _single_line(value: object) -> str:
    return " ".join(str(value or "").split())


def _defect_area(defect_text: str, subsystem: str) -> str:
    text = defect_text.lower()
    if "remote-" in text or "fail-closed" in text or subsystem == "Scripts and Ops":
        return "operator_script_safety"
    if "telegram" in text or "app-first" in text:
        return "telegram_ux_logic"
    if "stale test" in text or "harness" in text or "mock" in text or "screenshot" in text:
        return "test_harness_or_audit"
    if "d-" in text and subsystem == "WebApp and Admin":
        return "webapp_user_flow"
    if "iss-" in text or subsystem == "POKROV client app":
        return "client_app_story"
    if subsystem == "Marketing site":
        return "marketing_story_or_copy"
    return "product_behavior"


def _closure_status(row: dict[str, str], audit_row: dict[str, str]) -> str:
    if row.get("story_status") == "Manual owner test":
        return "manual_owner_gate_open"

    proof_status = audit_row.get("retest_proof_status", "")
    if proof_status != "direct_test_ref_passed":
        return "needs_retest_proof"

    fix_text = f"{row.get('fix_status', '')} {row.get('defects_or_issues', '')}".lower()
    if "no product code change" in fix_text or "harness" in fix_text or "not a user-facing failure" in fix_text:
        return "closed_retested_no_product_change"
    return "closed_retested"


def build_rows(
    *,
    tracker_path: Path = DEFAULT_TRACKER,
    story_audit_path: Path = DEFAULT_STORY_AUDIT,
) -> list[dict[str, str]]:
    tracker_rows = [
        row
        for row in _read_csv_rows(tracker_path)
        if row.get("defects_or_issues", "").strip()
    ]
    audit_by_id = {
        row.get("canonical_id", ""): row
        for row in _read_csv_rows(story_audit_path)
    }

    rows: list[dict[str, str]] = []
    for index, row in enumerate(tracker_rows, start=1):
        canonical_id = row.get("canonical_id", "")
        audit_row = audit_by_id.get(canonical_id, {})
        proof_refs = [
            ref.strip()
            for ref in audit_row.get("test_refs", "").split(";")
            if ref.strip()
        ]
        rows.append(
            {
                "ledger_id": f"DEFECT-FIX-{index:03d}",
                "canonical_id": _single_line(canonical_id),
                "subsystem": _single_line(row.get("subsystem", "")),
                "surface": _single_line(row.get("surface", "")),
                "feature": _single_line(row.get("feature", "")),
                "route_or_trigger": _single_line(row.get("route_or_trigger", "")),
                "defect_area": _defect_area(
                    row.get("defects_or_issues", ""),
                    row.get("subsystem", ""),
                ),
                "defect_or_issue": _single_line(row.get("defects_or_issues", "")),
                "fix_status": _single_line(row.get("fix_status", "")),
                "retest_status": _single_line(row.get("retest_status", "")),
                "story_status": _single_line(row.get("story_status", "")),
                "retest_proof_status": _single_line(audit_row.get("retest_proof_status", "")),
                "closure_status": _closure_status(row, audit_row),
                "proof_ref_count": str(len(proof_refs)),
                "proof_refs": "; ".join(proof_refs),
                "next_action": _single_line(row.get("next_action", "")),
                "updated_at": TODAY,
            }
        )
    return rows


def write_csv(rows: list[dict[str, str]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _count_table(title: str, rows: list[tuple[str, int]]) -> list[str]:
    out = [title, "", "| Label | Count |", "| --- | ---: |"]
    out.extend(f"| `{label}` | {count} |" for label, count in rows)
    out.append("")
    return out


def write_markdown(rows: list[dict[str, str]], out_path: Path) -> None:
    closure_counts = Counter(row["closure_status"] for row in rows)
    area_counts = Counter(row["defect_area"] for row in rows)
    subsystem_counts = Counter(row["subsystem"] for row in rows)
    weak_count = sum(
        closure_counts[status]
        for status in (
            "needs_retest_proof",
            "manual_owner_gate_open",
        )
    )

    lines = [
        "# POKROV Defect Fix Retest Ledger",
        "",
        f"Last updated: {TODAY}",
        "",
        "## Purpose",
        "",
        "This generated ledger extracts every canonical story row with",
        "`defects_or_issues` and records the fix, retest, proof refs, and closure",
        "status in one audit table. It supports the goal requirement to document",
        "discrepancies, fixes, and repeat verification separately from the full",
        "feature/story tracker.",
        "",
        "## Canonical Files",
        "",
        "- CSV: [pokrov-defect-fix-retest-ledger.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-defect-fix-retest-ledger.csv)",
        "- Source tracker: [pokrov-canonical-feature-tracker.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-canonical-feature-tracker.csv)",
        "- Story evidence audit: [pokrov-story-test-evidence-audit.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-story-test-evidence-audit.csv)",
        "- Generator: [generate_defect_fix_retest_ledger.py](C:/Users/kiwun/Documents/ai/VPN/scripts/generate_defect_fix_retest_ledger.py)",
        "",
        "## Current Counts",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Defect rows | {len(rows)} |",
        f"| Closed and retested rows | {closure_counts.get('closed_retested', 0)} |",
        f"| Closed no-product-change rows | {closure_counts.get('closed_retested_no_product_change', 0)} |",
        f"| Rows needing retest proof | {closure_counts.get('needs_retest_proof', 0)} |",
        f"| Manual owner-gate defect rows | {closure_counts.get('manual_owner_gate_open', 0)} |",
        f"| Open or weak closure rows | {weak_count} |",
        "",
    ]
    lines.extend(_count_table("### By Closure Status", sorted(closure_counts.items())))
    lines.extend(_count_table("### By Defect Area", sorted(area_counts.items())))
    lines.extend(_count_table("### By Subsystem", sorted(subsystem_counts.items())))
    lines.extend(
        [
            "## Completion Rule",
            "",
            "Local defect rows are considered closed only when `closure_status` is",
            "`closed_retested` or `closed_retested_no_product_change` and",
            "`retest_proof_status` is `direct_test_ref_passed`. Owner-only gates stay",
            "outside this local defect ledger unless their canonical row records a",
            "defect.",
            "",
            "## Regeneration",
            "",
            "```powershell",
            "python scripts\\generate_defect_fix_retest_ledger.py",
            "```",
            "",
        ]
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the POKROV defect/fix/retest ledger.")
    parser.add_argument("--tracker", default=str(DEFAULT_TRACKER))
    parser.add_argument("--story-audit", default=str(DEFAULT_STORY_AUDIT))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--markdown-out", default=str(DEFAULT_MARKDOWN_OUT))
    args = parser.parse_args()

    rows = build_rows(
        tracker_path=Path(args.tracker).resolve(),
        story_audit_path=Path(args.story_audit).resolve(),
    )
    write_csv(rows, Path(args.out).resolve())
    write_markdown(rows, Path(args.markdown_out).resolve())
    print(f"wrote {len(rows)} defect/fix/retest rows to {Path(args.out).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

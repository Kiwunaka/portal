from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = REPO_ROOT / "docs" / "developer" / "pokrov-code-function-inventory.csv"
DEFAULT_SYMBOL_COVERAGE = REPO_ROOT / "docs" / "developer" / "pokrov-symbol-coverage-audit.csv"
DEFAULT_OUT = REPO_ROOT / "docs" / "developer" / "pokrov-private-helper-coverage.csv"
DEFAULT_MARKDOWN_OUT = REPO_ROOT / "docs" / "developer" / "pokrov-private-helper-coverage.md"
TODAY = "2026-07-05"

FIELDS = [
    "symbol_id",
    "root",
    "path",
    "line",
    "language",
    "subsystem",
    "symbol_kind",
    "qualified_name",
    "signature",
    "private_helper_area",
    "risk_tier",
    "expected_behavior_from_code",
    "current_status",
    "proof_status",
    "strict_coverage_required",
    "coverage_policy_status",
    "next_action",
    "owner_policy_note",
    "updated_at",
]


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _single_line(value: object) -> str:
    return " ".join(str(value or "").split())


def _area(row: dict[str, str]) -> str:
    path = row.get("path", "")
    if path.startswith("apps/windows_shell/"):
        return "client_desktop_host_helper"
    if "telegram-webapp-init" in path:
        return "telegram_webapp_bootstrap_helper"
    if "qa-overlay" in path:
        return "qa_tooling_helper"
    if "email_relay" in path:
        return "email_relay_internal_helper"
    if "freekassa" in path or "lavatop" in path or "payment" in path:
        return "payment_probe_internal_helper"
    if "webapp/scripts/" in path:
        return "webapp_operator_script_helper"
    if "/features/" in path:
        return "client_feature_copy_or_logic_helper"
    if "/design_system/" in path or "/shared/" in path or "/shell/" in path:
        return "client_private_ui_helper"
    if path.startswith("webapp/src/"):
        return "webapp_private_ui_helper"
    return "private_implementation_helper"


def _risk_tier(row: dict[str, str], signature: str) -> str:
    area = _area(row)
    path = row.get("path", "")
    name = row.get("qualified_name", "")
    if area in {
        "email_relay_internal_helper",
        "payment_probe_internal_helper",
        "client_desktop_host_helper",
        "telegram_webapp_bootstrap_helper",
    }:
        return "high"
    if "Future<" in signature or name.endswith("._stateFile") or area in {
        "client_feature_copy_or_logic_helper",
        "webapp_operator_script_helper",
    }:
        return "medium"
    if "navigation_shell" in path or "qa-overlay" in path:
        return "medium"
    return "low"


def _expected_behavior(row: dict[str, str], signature: str) -> str:
    name = row.get("qualified_name") or row.get("name") or "private helper"
    path = row.get("path", "")
    language = row.get("language", "")
    if "extends Intent" in signature:
        return "Carry the private app-shell action intent used by keyboard or command handlers without changing public state by itself."
    if "String " in signature or signature.startswith("String"):
        return "Return deterministic user-facing label or status copy for the feature state represented by the containing source file."
    if "IconData " in signature:
        return "Return the expected Material icon for the feature preset or fallback state represented by the input."
    if "extends StatelessWidget" in signature or "extends StatefulWidget" in signature:
        return "Render a private UI component inside its containing screen without becoming a standalone product story."
    if "extends CustomPainter" in signature or name.endswith(".paint"):
        return "Draw or refresh private visual decoration for the containing Flutter widget without changing product state."
    if name.endswith(".shouldRepaint"):
        return "Report repaint necessity for the private painter from delegate state only."
    if any(name.endswith(f".{method}") for method in ("initState", "didChangeDependencies", "didUpdateWidget", "dispose", "createState")):
        return "Maintain Flutter lifecycle behavior for the private widget state used by the containing screen."
    if "Future<" in signature or signature.startswith("Future"):
        return "Complete the asynchronous internal helper operation implied by the function name and containing module."
    if language == "python":
        return "Support the internal backend or operator flow named by the helper while preserving fail-closed behavior in its parent entrypoint."
    if "tsx" in language or "typescript" in language:
        return "Support private React or operator UI behavior inside the containing route/component without creating a public API."
    return f"Support the private implementation behavior named `{name}` inside `{path}`."


def _next_action(row: dict[str, str], risk_tier: str) -> str:
    if risk_tier == "high":
        return "Add direct or public-wrapper behavior coverage before accepting a strict one-test-per-private-helper policy."
    if risk_tier == "medium":
        return "Prefer wrapper, widget, or story-level assertions if Q-001 requires stricter private-helper coverage."
    return "Keep as source-inventory-only unless the owner requires one-test-per-private-helper coverage or this helper changes."


def build_rows(
    *,
    inventory_path: Path = DEFAULT_INVENTORY,
    symbol_coverage_path: Path = DEFAULT_SYMBOL_COVERAGE,
) -> list[dict[str, str]]:
    inventory_by_id = {row["symbol_id"]: row for row in _read_csv_rows(inventory_path)}
    private_rows = [
        row
        for row in _read_csv_rows(symbol_coverage_path)
        if row.get("coverage_tier") == "private_inventory_only"
    ]

    rows: list[dict[str, str]] = []
    for coverage in private_rows:
        symbol_id = coverage["symbol_id"]
        inventory = inventory_by_id.get(symbol_id, {})
        signature = _single_line(inventory.get("doc_or_signature", ""))
        risk_tier = _risk_tier(coverage, signature)
        rows.append(
            {
                "symbol_id": symbol_id,
                "root": _single_line(coverage.get("root", "")),
                "path": _single_line(coverage.get("path", "")),
                "line": _single_line(coverage.get("line", "")),
                "language": _single_line(coverage.get("language", "")),
                "subsystem": _single_line(coverage.get("subsystem", "")),
                "symbol_kind": _single_line(coverage.get("symbol_kind", "")),
                "qualified_name": _single_line(coverage.get("qualified_name", "")),
                "signature": signature,
                "private_helper_area": _area(coverage),
                "risk_tier": risk_tier,
                "expected_behavior_from_code": _expected_behavior(coverage, signature),
                "current_status": "source_inventory_only",
                "proof_status": "no_dedicated_private_helper_test",
                "strict_coverage_required": "yes_if_owner_requires_one_test_per_private_helper",
                "coverage_policy_status": "needs_owner_decision_q001",
                "next_action": _next_action(coverage, risk_tier),
                "owner_policy_note": "Q-001 decides whether this private symbol needs a dedicated behavior test or remains covered by story/symbol tiers.",
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


def _count_table(title: str, rows: list[tuple[str, int]], *, count_label: str = "Count") -> list[str]:
    out = [title, "", f"| Label | {count_label} |", "| --- | ---: |"]
    out.extend(f"| `{label}` | {count} |" for label, count in rows)
    out.append("")
    return out


def write_markdown(rows: list[dict[str, str]], out_path: Path) -> None:
    area_counts = Counter(row["private_helper_area"] for row in rows)
    risk_counts = Counter(row["risk_tier"] for row in rows)
    language_counts = Counter(row["language"] for row in rows)
    status_counts = Counter(row["current_status"] for row in rows)
    policy_counts = Counter(row["coverage_policy_status"] for row in rows)

    lines = [
        "# POKROV Private Helper Coverage Matrix",
        "",
        f"Last updated: {TODAY}",
        "",
        "## Purpose",
        "",
        "This generated matrix expands the `private_inventory_only` tier from",
        "`pokrov-symbol-coverage-audit.csv` into per-symbol expected behavior,",
        "risk, proof status, and next action. It does not claim dedicated tests for",
        "private helpers; it makes Q-001 measurable if the owner requires stricter",
        "one-test-per-private-helper coverage.",
        "",
        "## Canonical Files",
        "",
        "- CSV: [pokrov-private-helper-coverage.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-private-helper-coverage.csv)",
        "- Source symbol coverage: [pokrov-symbol-coverage-audit.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-symbol-coverage-audit.csv)",
        "- Low-level inventory: [pokrov-code-function-inventory.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-code-function-inventory.csv)",
        "- Generator: [generate_private_helper_coverage.py](C:/Users/kiwun/Documents/ai/VPN/scripts/generate_private_helper_coverage.py)",
        "",
        "## Current Counts",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Private helper rows | {len(rows)} |",
        f"| Rows needing Q-001 owner decision | {policy_counts.get('needs_owner_decision_q001', 0)} |",
        f"| High risk rows | {risk_counts.get('high', 0)} |",
        f"| Medium risk rows | {risk_counts.get('medium', 0)} |",
        f"| Low risk rows | {risk_counts.get('low', 0)} |",
        "",
    ]
    lines.extend(_count_table("### By Private Helper Area", sorted(area_counts.items())))
    lines.extend(_count_table("### By Risk Tier", sorted(risk_counts.items())))
    lines.extend(_count_table("### By Language", sorted(language_counts.items())))
    lines.extend(_count_table("### By Current Status", sorted(status_counts.items())))
    lines.extend(
        [
            "## Completion Rule",
            "",
            "If the owner chooses `ACCEPT_STORY_AND_SYMBOL_TIERS` or",
            "`REQUIRE_PUBLIC_AND_ENTRYPOINT_ONLY`, these rows remain tracked as",
            "`source_inventory_only` and Q-001 can close after the policy decision is",
            "recorded. If the owner chooses `REQUIRE_ONE_TEST_PER_PRIVATE_HELPER`,",
            "each row must receive a dedicated test reference or explicit owner waiver",
            "before Q-001 can close.",
            "",
            "## Regeneration",
            "",
            "```powershell",
            "python scripts\\generate_private_helper_coverage.py",
            "```",
            "",
        ]
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the private-helper coverage matrix for Q-001.")
    parser.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    parser.add_argument("--symbol-coverage", default=str(DEFAULT_SYMBOL_COVERAGE))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--markdown-out", default=str(DEFAULT_MARKDOWN_OUT))
    args = parser.parse_args()

    rows = build_rows(
        inventory_path=Path(args.inventory).resolve(),
        symbol_coverage_path=Path(args.symbol_coverage).resolve(),
    )
    write_csv(rows, Path(args.out).resolve())
    write_markdown(rows, Path(args.markdown_out).resolve())
    print(f"wrote {len(rows)} private helper rows to {Path(args.out).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

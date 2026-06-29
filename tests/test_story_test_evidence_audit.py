from __future__ import annotations

import csv
import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLIENT_ROOT = REPO_ROOT.parent / "POKROV-app"
TRACKER = REPO_ROOT / "docs" / "developer" / "pokrov-canonical-feature-tracker.csv"
TRACKER_MD = REPO_ROOT / "docs" / "developer" / "pokrov-canonical-feature-tracker.md"
STORY_AUDIT = REPO_ROOT / "docs" / "developer" / "pokrov-story-test-evidence-audit.csv"
STORY_AUDIT_MD = REPO_ROOT / "docs" / "developer" / "pokrov-story-test-evidence-audit.md"
DEFECT_FIX_RETEST_LEDGER = (
    REPO_ROOT / "docs" / "developer" / "pokrov-defect-fix-retest-ledger.csv"
)
DEFECT_FIX_RETEST_LEDGER_MD = (
    REPO_ROOT / "docs" / "developer" / "pokrov-defect-fix-retest-ledger.md"
)
ENTRYPOINT_STORY_COVERAGE = (
    REPO_ROOT / "docs" / "developer" / "pokrov-entrypoint-story-coverage.csv"
)
ENTRYPOINT_STORY_COVERAGE_MD = (
    REPO_ROOT / "docs" / "developer" / "pokrov-entrypoint-story-coverage.md"
)
OPEN_QUESTIONS = REPO_ROOT / "docs" / "developer" / "pokrov-open-questions.csv"
OPEN_QUESTIONS_MD = REPO_ROOT / "docs" / "developer" / "pokrov-open-questions.md"
OWNER_ANSWER_SHEET = (
    REPO_ROOT / "docs" / "developer" / "pokrov-owner-answer-sheet.md"
)
OWNER_GATED_SCENARIOS = (
    REPO_ROOT / "docs" / "developer" / "pokrov-owner-gated-scenarios.csv"
)
OWNER_GATED_RESULTS = (
    REPO_ROOT / "docs" / "developer" / "pokrov-owner-gated-results.csv"
)
OWNER_GATED_SCENARIOS_MD = (
    REPO_ROOT / "docs" / "developer" / "pokrov-owner-gated-scenarios.md"
)
OWNER_GATED_EXECUTION_GUIDE = (
    REPO_ROOT / "docs" / "developer" / "pokrov-owner-gated-execution-guide.md"
)
BACKEND_ROUTE_COVERAGE = (
    REPO_ROOT / "docs" / "developer" / "pokrov-backend-route-coverage.csv"
)
SCRIPT_WORKFLOW_COVERAGE = (
    REPO_ROOT / "docs" / "developer" / "pokrov-script-workflow-coverage.csv"
)
ENTRYPOINT_INVENTORY = (
    REPO_ROOT / "docs" / "developer" / "pokrov-entrypoint-inventory.csv"
)
CODE_FUNCTION_INVENTORY = (
    REPO_ROOT / "docs" / "developer" / "pokrov-code-function-inventory.csv"
)
SYMBOL_COVERAGE_AUDIT = (
    REPO_ROOT / "docs" / "developer" / "pokrov-symbol-coverage-audit.csv"
)
PRIVATE_HELPER_COVERAGE = (
    REPO_ROOT / "docs" / "developer" / "pokrov-private-helper-coverage.csv"
)
COVERAGE_POLICY_DECISION_GUIDE = (
    REPO_ROOT / "docs" / "developer" / "pokrov-coverage-policy-decision-guide.md"
)
DOCS_INDEX = REPO_ROOT / "docs" / "README.md"
REPOSITORY_MAP = REPO_ROOT / "docs" / "developer" / "repository-map.md"
DEVELOPER_GUIDE = REPO_ROOT / "docs" / "developer" / "developer-guide.md"
WORK_ORDERS_README = REPO_ROOT / "docs" / "developer" / "work-orders" / "README.md"
COMPLETION_AUDIT = (
    REPO_ROOT
    / "docs"
    / "developer"
    / "work-orders"
    / "2026-06-27--repo-feature-story-audit"
    / "COMPLETION-AUDIT.md"
)
COMPLETION_AUDIT_CSV = (
    REPO_ROOT
    / "docs"
    / "developer"
    / "work-orders"
    / "2026-06-27--repo-feature-story-audit"
    / "COMPLETION-AUDIT.csv"
)
WORK_ORDER_INDEX = (
    REPO_ROOT
    / "docs"
    / "developer"
    / "work-orders"
    / "2026-06-27--repo-feature-story-audit"
    / "INDEX.md"
)
WORK_ORDER = (
    REPO_ROOT
    / "docs"
    / "developer"
    / "work-orders"
    / "2026-06-27--repo-feature-story-audit"
    / "WO-001-canonical-feature-tracker.md"
)
NAVIGATION_ARTIFACTS = (
    "pokrov-canonical-feature-tracker.md",
    "pokrov-canonical-feature-tracker.csv",
    "pokrov-entrypoint-inventory.csv",
    "pokrov-entrypoint-story-coverage.csv",
    "pokrov-entrypoint-story-coverage.md",
    "pokrov-code-function-inventory.csv",
    "pokrov-code-function-inventory.md",
    "pokrov-symbol-coverage-audit.csv",
    "pokrov-symbol-coverage-audit.md",
    "pokrov-private-helper-coverage.csv",
    "pokrov-private-helper-coverage.md",
    "pokrov-coverage-policy-decision-guide.md",
    "pokrov-story-test-evidence-audit.csv",
    "pokrov-story-test-evidence-audit.md",
    "pokrov-defect-fix-retest-ledger.csv",
    "pokrov-defect-fix-retest-ledger.md",
    "pokrov-backend-route-coverage.csv",
    "pokrov-script-workflow-coverage.csv",
    "pokrov-owner-gated-scenarios.md",
    "pokrov-owner-gated-execution-guide.md",
    "pokrov-owner-gated-scenarios.csv",
    "pokrov-owner-gated-results.csv",
    "pokrov-owner-answer-sheet.md",
    "pokrov-open-questions.md",
    "pokrov-open-questions.csv",
)
WORK_ORDER_NAVIGATION_ARTIFACTS = (
    "docs/developer/work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.md",
    "docs/developer/work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.csv",
)
CANONICAL_AUDIT_TEXT_FILES = (
    TRACKER_MD,
    STORY_AUDIT_MD,
    DEFECT_FIX_RETEST_LEDGER_MD,
    ENTRYPOINT_STORY_COVERAGE_MD,
    OPEN_QUESTIONS_MD,
    OWNER_ANSWER_SHEET,
    OWNER_GATED_SCENARIOS_MD,
    OWNER_GATED_EXECUTION_GUIDE,
    COVERAGE_POLICY_DECISION_GUIDE,
    COMPLETION_AUDIT,
    WORK_ORDER_INDEX,
    WORK_ORDER,
)
CANONICAL_AUDIT_CSV_FILES = (
    TRACKER,
    STORY_AUDIT,
    DEFECT_FIX_RETEST_LEDGER,
    ENTRYPOINT_STORY_COVERAGE,
    OPEN_QUESTIONS,
    OWNER_GATED_SCENARIOS,
    OWNER_GATED_RESULTS,
    BACKEND_ROUTE_COVERAGE,
    SCRIPT_WORKFLOW_COVERAGE,
    ENTRYPOINT_INVENTORY,
    CODE_FUNCTION_INVENTORY,
    SYMBOL_COVERAGE_AUDIT,
    PRIVATE_HELPER_COVERAGE,
    COMPLETION_AUDIT_CSV,
)
MOJIBAKE_MARKERS = (
    "\u0420\u201c",
    "\u0420\u201d",
    "\u0420\u045c",
    "\u0420\u045f",
    "\u0420\u0452",
    "\u0420\u0454",
    "\u0420\u00bb",
    "\u0420\u00b0",
    "\u0420\u0491",
    "\u0421\u0403",
    "\u0421\u201a",
    "\u0421\u040b",
    "\u0412\u00b7",
    "\u0432\u0402",
)
STORY_EVIDENCE_TIER_LABELS = (
    "direct_file_ref",
    "imported_pass_no_file_ref",
    "manual_owner_gate",
    "stale_file_ref",
    "weak_or_missing_evidence",
)
ENTRYPOINT_COVERAGE_LABELS = {
    "direct_route_test_ref": "Direct route test ref",
    "direct_script_test_ref": "Direct script test ref",
    "direct_story_test_ref": "Direct story test ref",
    "needs_story_mapping_review": "Needs story mapping review",
}
ENTRYPOINT_TYPE_LABELS = {
    "fastapi_route": "FastAPI route",
    "script_cli": "Script CLI",
    "aiogram_handler": "Aiogram handler",
    "next_page_route": "Next.js page route",
    "flutter_feature_file": "Flutter feature file",
}
TRACKER_SUBSYSTEM_LABELS = {
    "Backend API": "Backend API",
    "Scripts and Ops": "Scripts and Ops",
    "POKROV client app": "POKROV client app",
    "WebApp and Admin": "WebApp and Admin",
    "Telegram bots": "Telegram bots",
    "Marketing site": "Marketing site",
}
TRACKER_LANGUAGE_LABELS = {
    "python": "Python",
    "dart": "Dart",
    "tsx": "TSX",
    "typescript": "TypeScript",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "cpp": "C++",
    "c-header": "C header",
}
TRACKER_SYMBOL_COVERAGE_LABELS = {
    "story_source_file": "Story source file",
    "story_dependency_source_file": "Story dependency source file",
    "entrypoint_mapped": "Entrypoint mapped",
    "direct_token_test_ref": "Direct token test ref",
    "module_test_ref": "Module test ref",
    "private_inventory_only": "Private inventory only",
    "client_platform_host_manual_gate": "Client platform host manual gate",
    "entrypoint_route_test_ref": "Entrypoint route test ref",
    "operator_tooling_inventory": "Operator tooling inventory",
    "next_route_boundary_inventory": "Next route boundary inventory",
    "client_desktop_tray_manual_gate": "Client desktop tray manual gate",
    "qa_tooling_inventory": "QA tooling inventory",
    "script_cli_deprecated": "Script CLI deprecated",
    "telegram_webapp_bootstrap_inventory": "Telegram WebApp bootstrap inventory",
    "entrypoint_story_source_ref": "Entrypoint story source ref",
    "client_package_public_api_review": "Client package public API review",
    "entrypoint_needs_mapping_review": "Entrypoint needs mapping review",
    "public_symbol_review": "Public symbol review",
}


def _load_module():
    module_path = REPO_ROOT / "scripts" / "audit_story_test_evidence.py"
    spec = importlib.util.spec_from_file_location("audit_story_test_evidence", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_defect_ledger_module():
    module_path = REPO_ROOT / "scripts" / "generate_defect_fix_retest_ledger.py"
    spec = importlib.util.spec_from_file_location("generate_defect_fix_retest_ledger", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _source_refs(text: str) -> list[str]:
    refs: list[str] = []
    for raw_part in re.split(r"[,;\s]+", text or ""):
        part = raw_part.strip().strip('"')
        if not part:
            continue
        match = re.match(
            r"(.+\.(?:py|tsx|ts|dart|kt|ps1|md|mjs|txt|xml|json|csv|ya?ml))(?::\d+)?$",
            part.replace("\\", "/"),
        )
        if match:
            refs.append(match.group(1))
    return refs


def _source_line_refs(text: str) -> list[tuple[str, int]]:
    refs: list[tuple[str, int]] = []
    normalized = (text or "").replace("\\", "/")
    for match in re.finditer(
        r"(?P<path>[^,;\s\"']+\.(?:py|tsx|ts|dart|kt|ps1|md|mjs|txt|xml|json|csv|ya?ml)):(?P<lines>\d+(?:,\d+)*)",
        normalized,
    ):
        path = match.group("path")
        for raw_line in match.group("lines").split(","):
            refs.append((path, int(raw_line)))
    return refs


def _markdown_count_tables_after_heading(body: str, heading: str) -> list[dict[str, int]]:
    lines = body.splitlines()
    start = lines.index(heading)
    tables: list[dict[str, int]] = []
    index = start + 1
    while index < len(lines):
        if lines[index].startswith("## "):
            break
        if not lines[index].startswith("|"):
            index += 1
            continue
        table: dict[str, int] = {}
        while index < len(lines) and lines[index].startswith("|"):
            cells = [
                cell.strip().replace("`", "")
                for cell in lines[index].strip().strip("|").split("|")
            ]
            index += 1
            if len(cells) < 2:
                continue
            if cells[1] in {"Count", "Entrypoints", "Rows"}:
                continue
            if cells[0] in {
                "Coverage tier",
                "Entrypoint type",
                "Evidence tier",
                "Metric",
                "Source",
            }:
                continue
            if set(cells[0]) <= {"-"} or set(cells[1].rstrip(":")) <= {"-"}:
                continue
            table[cells[0]] = int(cells[1].replace(",", ""))
        if table:
            tables.append(table)
    return tables


def _markdown_table_after_heading(body: str, heading: str) -> dict[str, int]:
    tables = _markdown_count_tables_after_heading(body, heading)
    assert tables, f"No table found after {heading}"
    return tables[0]


def _resolve_source_ref(row: dict[str, str], ref: str) -> Path | None:
    if ref in {"AGENTS.md", "DESIGN.md"}:
        return REPO_ROOT / ref
    if ref.startswith(("portal_bot/", "scripts/", "shared/", "webapp/", "marketing/", "copy/", "tests/", "docs/")):
        return REPO_ROOT / ref
    if ref.startswith("POKROV-app/"):
        return REPO_ROOT.parent / ref
    if row.get("subsystem") == "POKROV client app" and ref.startswith(("packages/", "apps/", "lib/")):
        return CLIENT_ROOT / ref
    return None


def test_canonical_tracker_markdown_summary_matches_csv_artifacts() -> None:
    with TRACKER.open("r", encoding="utf-8", newline="") as f:
        tracker_rows = list(csv.DictReader(f))
    with BACKEND_ROUTE_COVERAGE.open("r", encoding="utf-8", newline="") as f:
        backend_rows = list(csv.DictReader(f))
    with SCRIPT_WORKFLOW_COVERAGE.open("r", encoding="utf-8", newline="") as f:
        script_rows = list(csv.DictReader(f))
    with CODE_FUNCTION_INVENTORY.open("r", encoding="utf-8", newline="") as f:
        code_rows = list(csv.DictReader(f))
    with SYMBOL_COVERAGE_AUDIT.open("r", encoding="utf-8", newline="") as f:
        symbol_rows = list(csv.DictReader(f))
    with PRIVATE_HELPER_COVERAGE.open("r", encoding="utf-8", newline="") as f:
        private_helper_rows = list(csv.DictReader(f))
    with STORY_AUDIT.open("r", encoding="utf-8", newline="") as f:
        story_rows = list(csv.DictReader(f))
    with ENTRYPOINT_INVENTORY.open("r", encoding="utf-8", newline="") as f:
        entrypoint_rows = list(csv.DictReader(f))
    with ENTRYPOINT_STORY_COVERAGE.open("r", encoding="utf-8", newline="") as f:
        entrypoint_coverage_rows = list(csv.DictReader(f))

    body = TRACKER_MD.read_text(encoding="utf-8")
    subsystem_counts = Counter(row["subsystem"] for row in tracker_rows)
    status_counts = Counter(row["story_status"] for row in tracker_rows)
    backend_status_counts = Counter(row["story_status"] for row in backend_rows)
    script_status_counts = Counter(row["story_status"] for row in script_rows)
    script_category_counts = Counter(row["category"] for row in script_rows)
    symbol_coverage_counts = Counter(row["coverage_tier"] for row in symbol_rows)
    private_helper_risk_counts = Counter(row["risk_tier"] for row in private_helper_rows)
    evidence_counts = Counter(row["evidence_tier"] for row in story_rows)
    entrypoint_type_counts = Counter(row["entry_type"] for row in entrypoint_rows)
    entrypoint_subsystem_counts = Counter(row["subsystem"] for row in entrypoint_rows)
    entrypoint_coverage_counts = Counter(
        row["coverage_tier"] for row in entrypoint_coverage_rows
    )

    assert f"- Total canonical rows: {len(tracker_rows)}" in body
    for subsystem, label in TRACKER_SUBSYSTEM_LABELS.items():
        assert f"- {label}: {subsystem_counts[subsystem]}" in body

    assert _markdown_table_after_heading(body, "### Story Status Counts") == {
        "Manual owner test": status_counts.get("Manual owner test", 0),
        "Needs scenario test": status_counts.get("Needs scenario test", 0),
        "Retest passed": status_counts.get("Retest passed", 0),
    }
    assert _markdown_table_after_heading(body, "### Backend API Route Coverage") == {
        "Retest passed": backend_status_counts.get("Retest passed", 0)
    }
    script_tables = _markdown_count_tables_after_heading(
        body, "### Script/Ops Workflow Coverage"
    )
    assert script_tables[0] == {
        "Retest passed": script_status_counts.get("Retest passed", 0),
        "Needs scenario test": script_status_counts.get("Needs scenario test", 0),
    }
    assert script_tables[1] == dict(script_category_counts)

    assert _markdown_table_after_heading(body, "### Low-Level Code Function Inventory") == {
        "Total source symbols": len(code_rows),
        "Root repo symbols": sum(row["root"] == "root" for row in code_rows),
        "POKROV-app symbols": sum(row["root"] == "POKROV-app" for row in code_rows),
        "Symbols with token-level test references": sum(
            int(row.get("test_ref_count") or 0) > 0 for row in code_rows
        ),
        "Parser errors": sum(
            "parse_error" in (row.get("parser_note") or "") for row in code_rows
        ),
    }
    assert _markdown_table_after_heading(body, "### Source Symbol Coverage Audit") == {
        label: symbol_coverage_counts.get(tier, 0)
        for tier, label in TRACKER_SYMBOL_COVERAGE_LABELS.items()
    }
    assert _markdown_table_after_heading(body, "### Private Helper Coverage Matrix") == {
        "Private helper rows": len(private_helper_rows),
        "Rows needing Q-001 owner decision": sum(
            row["coverage_policy_status"] == "needs_owner_decision_q001"
            for row in private_helper_rows
        ),
        "High risk rows": private_helper_risk_counts.get("high", 0),
        "Medium risk rows": private_helper_risk_counts.get("medium", 0),
        "Low risk rows": private_helper_risk_counts.get("low", 0),
    }
    assert _markdown_table_after_heading(body, "### Story Test Evidence Audit") == {
        "Direct automated test file reference": evidence_counts.get("direct_file_ref", 0),
        "Imported pass without direct file reference": evidence_counts.get(
            "imported_pass_no_file_ref", 0
        ),
        "Manual owner gate": evidence_counts.get("manual_owner_gate", 0),
        "Stale or missing test references": evidence_counts.get("stale_file_ref", 0),
        "Unresolved source tracker references": 0,
    }
    entrypoint_tables = _markdown_count_tables_after_heading(
        body, "### Entrypoint Inventory Counts"
    )
    assert entrypoint_tables[0] == dict(entrypoint_type_counts)
    assert entrypoint_tables[1] == dict(entrypoint_subsystem_counts)
    assert _markdown_table_after_heading(body, "### Entrypoint Story Coverage") == {
        "Direct route test reference": entrypoint_coverage_counts.get(
            "direct_route_test_ref", 0
        ),
        "Direct script test reference": entrypoint_coverage_counts.get(
            "direct_script_test_ref", 0
        ),
        "Direct story test reference": entrypoint_coverage_counts.get(
            "direct_story_test_ref", 0
        ),
        "Needs story mapping review": entrypoint_coverage_counts.get(
            "needs_story_mapping_review", 0
        ),
    }


def test_work_order_index_imported_coverage_matches_tracker_csv() -> None:
    with TRACKER.open("r", encoding="utf-8", newline="") as f:
        tracker_rows = list(csv.DictReader(f))

    subsystem_counts = Counter(row["subsystem"] for row in tracker_rows)
    body = WORK_ORDER_INDEX.read_text(encoding="utf-8")

    assert _markdown_table_after_heading(body, "## Current Imported Coverage") == {
        "Telegram bots tracker": subsystem_counts["Telegram bots"],
        "WebApp/admin tracker": subsystem_counts["WebApp and Admin"],
        "Marketing tracker": subsystem_counts["Marketing site"],
        "POKROV-app client tracker": subsystem_counts["POKROV client app"],
        "Backend API route rows": subsystem_counts["Backend API"],
        "Active script/operator workflow rows": subsystem_counts["Scripts and Ops"],
    }


def test_work_order_current_output_counts_match_csv_artifacts() -> None:
    with TRACKER.open("r", encoding="utf-8", newline="") as f:
        tracker_rows = list(csv.DictReader(f))
    with BACKEND_ROUTE_COVERAGE.open("r", encoding="utf-8", newline="") as f:
        backend_rows = list(csv.DictReader(f))
    with SCRIPT_WORKFLOW_COVERAGE.open("r", encoding="utf-8", newline="") as f:
        script_rows = list(csv.DictReader(f))
    with ENTRYPOINT_INVENTORY.open("r", encoding="utf-8", newline="") as f:
        entrypoint_rows = list(csv.DictReader(f))
    with CODE_FUNCTION_INVENTORY.open("r", encoding="utf-8", newline="") as f:
        code_rows = list(csv.DictReader(f))
    with SYMBOL_COVERAGE_AUDIT.open("r", encoding="utf-8", newline="") as f:
        symbol_rows = list(csv.DictReader(f))
    with PRIVATE_HELPER_COVERAGE.open("r", encoding="utf-8", newline="") as f:
        private_rows = list(csv.DictReader(f))
    with STORY_AUDIT.open("r", encoding="utf-8", newline="") as f:
        story_rows = list(csv.DictReader(f))
    with DEFECT_FIX_RETEST_LEDGER.open("r", encoding="utf-8", newline="") as f:
        defect_rows = list(csv.DictReader(f))
    with OWNER_GATED_SCENARIOS.open("r", encoding="utf-8", newline="") as f:
        owner_gate_rows = list(csv.DictReader(f))
    with OWNER_GATED_RESULTS.open("r", encoding="utf-8", newline="") as f:
        owner_result_rows = list(csv.DictReader(f))
    with OPEN_QUESTIONS.open("r", encoding="utf-8", newline="") as f:
        question_rows = list(csv.DictReader(f))
    with ENTRYPOINT_STORY_COVERAGE.open("r", encoding="utf-8", newline="") as f:
        entrypoint_coverage_rows = list(csv.DictReader(f))

    tracker_status_counts = Counter(row["story_status"] for row in tracker_rows)
    subsystem_counts = Counter(row["subsystem"] for row in tracker_rows)
    source_tracker_counts = Counter(row["source_tracker"] for row in tracker_rows)
    backend_status_counts = Counter(row["story_status"] for row in backend_rows)
    script_status_counts = Counter(row["story_status"] for row in script_rows)
    code_root_counts = Counter(row["root"] for row in code_rows)
    entrypoint_hint_counts = Counter(row["entrypoint_hint"] for row in code_rows)
    symbol_tier_counts = Counter(row["coverage_tier"] for row in symbol_rows)
    story_evidence_counts = Counter(row["evidence_tier"] for row in story_rows)
    story_retest_counts = Counter(row["retest_proof_status"] for row in story_rows)
    defect_closure_counts = Counter(row["closure_status"] for row in defect_rows)
    entrypoint_coverage_counts = Counter(
        row["coverage_tier"] for row in entrypoint_coverage_rows
    )

    imported_story_rows = sum(
        count
        for source_tracker, count in source_tracker_counts.items()
        if not source_tracker.startswith("generated from ")
    )
    required_open_owner_gates = sum(
        row["required_for_goal_completion"] == "yes"
        and row["current_status"] not in {"PASS", "OPERATOR_ATTESTED", "SKIPPED_BY_OWNER"}
        for row in owner_gate_rows
    )
    direct_route_refs = entrypoint_coverage_counts.get("direct_route_test_ref", 0)
    direct_script_refs = entrypoint_coverage_counts.get("direct_script_test_ref", 0)
    direct_story_refs = entrypoint_coverage_counts.get("direct_story_test_ref", 0)
    code_evidence_ref_count = sum(
        len(_source_refs(row.get("code_evidence", ""))) for row in tracker_rows
    )
    line_ref_count = 0
    for source_table in (TRACKER, OWNER_GATED_SCENARIOS, OWNER_GATED_RESULTS, OPEN_QUESTIONS):
        with source_table.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                for value in row.values():
                    line_ref_count += len(_source_line_refs(value or ""))

    body = WORK_ORDER.read_text(encoding="utf-8")
    expected_fragments = [
        f"- Canonical CSV rows: `{len(tracker_rows)}`",
        (
            "- Canonical story status rows: "
            f"`{tracker_status_counts['Retest passed']}` `Retest passed`, "
            f"`{tracker_status_counts['Manual owner test']}` `Manual owner test`"
        ),
        f"- Entrypoint inventory rows: `{len(entrypoint_rows)}`",
        f"- Imported verified story rows: `{imported_story_rows}`",
        f"- Backend API route-family rows: `{len(backend_rows)}`",
        (
            "- Backend route direct test-reference mappings: "
            f"`{backend_status_counts['Retest passed']}/{len(backend_rows)}`; "
            "scenario gaps: `0`"
        ),
        f"- Scripts/Ops workflow rows: `{len(script_rows)}`",
        (
            "- Script workflow direct test-reference mappings: "
            f"`{script_status_counts['Retest passed']}/{len(script_rows)}`; "
            "scenario gaps: `0`"
        ),
        (
            "- Low-level code function inventory rows: "
            f"`{len(code_rows)}`; parser errors: "
            f"`{sum('parse_error' in (row.get('parser_note') or '') for row in code_rows)}`; "
            "token-level test-reference hints: "
            f"`{sum(int(row.get('test_ref_count') or 0) > 0 for row in code_rows)}`"
        ),
        (
            "- Low-level entrypoint hints: "
            f"`{entrypoint_hint_counts['fastapi_route_handler']}` FastAPI route handlers, "
            f"`{entrypoint_hint_counts['fastapi_middleware']}` FastAPI middleware, "
            f"`{entrypoint_hint_counts['telegram_handler']}` Telegram handlers, "
            f"`{entrypoint_hint_counts['script_cli_main']}` script CLI mains, "
            f"`{entrypoint_hint_counts['framework_override']}` framework overrides, "
            f"`{entrypoint_hint_counts['next_page_component']}` Next.js page component"
        ),
        (
            "- Source symbol coverage audit rows: "
            f"`{len(symbol_rows)}`; expected-behavior notes: "
            f"`{sum(bool(row.get('expected_behavior_from_code')) for row in symbol_rows)}`; "
            f"entrypoint mapping gaps: `{symbol_tier_counts.get('entrypoint_needs_mapping_review', 0)}`; "
            f"story source refs: `{symbol_tier_counts['story_source_file']}`; "
            f"story dependency refs: `{symbol_tier_counts['story_dependency_source_file']}`; "
            f"module test refs: `{symbol_tier_counts['module_test_ref']}`; "
            f"direct token test refs: `{symbol_tier_counts['direct_token_test_ref']}`; "
            f"private inventory-only rows: `{symbol_tier_counts.get('private_inventory_only', 0)}`"
        ),
        (
            "- Private helper coverage matrix rows: "
            f"`{len(private_rows)}`; Q-001 owner-decision rows: "
            f"`{sum(row.get('coverage_policy_status') == 'needs_owner_decision_q001' for row in private_rows)}`"
        ),
        (
            "- Story evidence audit rows: "
            f"`{len(story_rows)}`; direct file refs: "
            f"`{story_evidence_counts['direct_file_ref']}`; "
            "imported-pass rows without direct file refs: "
            f"`{story_evidence_counts.get('imported_pass_no_file_ref', 0)}`; "
            f"manual owner gates: `{story_evidence_counts['manual_owner_gate']}`; "
            f"stale refs: `{story_evidence_counts.get('stale_file_ref', 0)}`"
        ),
        (
            "- Story retest proof rows: "
            f"`{story_retest_counts['direct_test_ref_passed']}` `direct_test_ref_passed`; "
            f"`{story_retest_counts['manual_owner_gate_open']}` `manual_owner_gate_open`"
        ),
        (
            "- Defect/fix/retest ledger rows: "
            f"`{len(defect_rows)}`; `closed_retested`: "
            f"`{defect_closure_counts['closed_retested']}`; "
            "`closed_retested_no_product_change`: "
            f"`{defect_closure_counts['closed_retested_no_product_change']}`; "
            "weak/open closure rows: `0`"
        ),
        (
            "- Owner-gated scenario matrix rows: "
            f"`{len(owner_gate_rows)}`; owner-gated result ledger rows: "
            f"`{len(owner_result_rows)}`; required owner-gated scenarios still open: "
            f"`{required_open_owner_gates}`"
        ),
        (
            "- Open questions ledger rows: "
            f"`{len(question_rows)}`; blocking full-goal questions: "
            f"`{sum(row['blocks_goal_completion'] == 'yes' for row in question_rows)}`"
        ),
        (
            "- Entrypoint story coverage rows: "
            f"`{len(entrypoint_coverage_rows)}`; direct route refs: "
            f"`{direct_route_refs}`; direct script refs: `{direct_script_refs}`; "
            f"direct story refs: `{direct_story_refs}`; review gaps: "
            f"`{entrypoint_coverage_counts.get('needs_story_mapping_review', 0)}`"
        ),
        (
            "- Canonical source-evidence file refs checked: "
            f"`{code_evidence_ref_count}`; missing source refs: `0`"
        ),
        (
            "- Canonical line-number source refs checked: "
            f"`{line_ref_count}`; out-of-bounds line refs: `0`"
        ),
        (
            "- Canonical source-tracker refs checked: "
            f"`{len(tracker_rows)}`; unresolved source-tracker refs: `0`"
        ),
    ]

    missing = [fragment for fragment in expected_fragments if fragment not in body]
    assert subsystem_counts["Scripts and Ops"] == len(script_rows)
    assert code_root_counts["root"] + code_root_counts["POKROV-app"] == len(code_rows)
    assert not missing


def test_story_evidence_markdown_summary_matches_csv() -> None:
    with STORY_AUDIT.open("r", encoding="utf-8", newline="") as f:
        story_rows = list(csv.DictReader(f))
    with TRACKER.open("r", encoding="utf-8", newline="") as f:
        tracker_rows = list(csv.DictReader(f))
    with ENTRYPOINT_STORY_COVERAGE.open("r", encoding="utf-8", newline="") as f:
        entrypoint_rows = list(csv.DictReader(f))
    with OWNER_GATED_SCENARIOS.open("r", encoding="utf-8", newline="") as f:
        owner_gate_rows = list(csv.DictReader(f))
    with OWNER_GATED_RESULTS.open("r", encoding="utf-8", newline="") as f:
        owner_result_rows = list(csv.DictReader(f))

    evidence_counts = Counter(row["evidence_tier"] for row in story_rows)
    entrypoint_counts = Counter(row["coverage_tier"] for row in entrypoint_rows)
    required_tracker_fields = (
        "canonical_id",
        "subsystem",
        "surface",
        "feature",
        "user_story",
        "expected_behavior",
        "code_evidence",
        "canon_guardrails",
        "test_method",
    )
    missing_required_fields = sum(
        1
        for row in tracker_rows
        for field in required_tracker_fields
        if not row.get(field, "").strip()
    )
    priority_only_guardrails = sum(
        1
        for row in tracker_rows
        if re.fullmatch(r"P\d+", row.get("canon_guardrails", "").strip())
    )
    rows_without_resolvable_code_refs = 0
    for row in tracker_rows:
        refs = _source_refs(row.get("code_evidence", ""))
        if not any(
            (path := _resolve_source_ref(row, ref)) is not None and path.exists()
            for ref in refs
        ):
            rows_without_resolvable_code_refs += 1

    generated_sources = {
        "generated from portal_bot/api.py route decorators": REPO_ROOT
        / "portal_bot"
        / "api.py",
        "generated from scripts/manifest.yaml": REPO_ROOT / "scripts" / "manifest.yaml",
    }
    unresolved_source_trackers = 0
    for row in tracker_rows:
        raw_tracker = row.get("source_tracker", "").strip()
        if raw_tracker in generated_sources:
            unresolved_source_trackers += int(not generated_sources[raw_tracker].exists())
            continue
        normalized = raw_tracker.replace("\\", "/")
        candidates = [REPO_ROOT / normalized]
        tracker_path = Path(raw_tracker)
        if tracker_path.is_absolute():
            candidates.append(tracker_path)
        if normalized.startswith("POKROV-app/"):
            candidates.append(REPO_ROOT.parent / normalized)
        unresolved_source_trackers += int(not any(candidate.exists() for candidate in candidates))

    open_required_owner_gates = sum(
        1
        for row in owner_gate_rows
        if row.get("required_for_goal_completion") == "yes"
        and row.get("current_status") in {"MANUAL_OWNER_TEST", "BLOCKED_BY_ACCESS"}
    )

    tables = _markdown_count_tables_after_heading(
        STORY_AUDIT_MD.read_text(encoding="utf-8"),
        "## Current Counts",
    )
    assert tables[0] == {
        tier: evidence_counts.get(tier, 0) for tier in STORY_EVIDENCE_TIER_LABELS
    }
    retest_proof_counts = Counter(row.get("retest_proof_status", "") for row in story_rows)
    assert tables[1] == {
        "direct_test_ref_passed": retest_proof_counts.get("direct_test_ref_passed", 0),
        "manual_owner_gate_open": retest_proof_counts.get("manual_owner_gate_open", 0),
        "direct_test_ref_without_pass_result": retest_proof_counts.get(
            "direct_test_ref_without_pass_result", 0
        ),
        "stale_test_ref": retest_proof_counts.get("stale_test_ref", 0),
        "imported_pass_without_direct_ref": retest_proof_counts.get(
            "imported_pass_without_direct_ref", 0
        ),
        "pass_without_direct_ref": retest_proof_counts.get("pass_without_direct_ref", 0),
        "weak_or_missing_retest_evidence": retest_proof_counts.get(
            "weak_or_missing_retest_evidence", 0
        ),
    }
    assert tables[2] == {
        "Total audited story rows": len(story_rows),
        "Missing referenced test files": sum(
            int(row.get("missing_test_ref_count") or 0) for row in story_rows
        ),
        "Missing required story contract fields": missing_required_fields,
        "Priority-only canon_guardrails rows": priority_only_guardrails,
        "Rows without resolvable code_evidence refs": rows_without_resolvable_code_refs,
        "Rows with unresolved source_tracker refs": unresolved_source_trackers,
        "Owner-gated scenario rows": len(owner_gate_rows),
        "Owner-gated result rows": len(owner_result_rows),
        "Required owner-gated scenarios still open": open_required_owner_gates,
    }
    assert tables[3] == {
        tier: entrypoint_counts.get(tier, 0)
        for tier in (
            "direct_route_test_ref",
            "direct_script_test_ref",
            "direct_story_test_ref",
            "needs_story_mapping_review",
        )
    }


def test_entrypoint_coverage_markdown_summary_matches_csv() -> None:
    with ENTRYPOINT_STORY_COVERAGE.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    coverage_counts = Counter(row["coverage_tier"] for row in rows)
    type_counts = Counter(row["entry_type"] for row in rows)
    tables = _markdown_count_tables_after_heading(
        ENTRYPOINT_STORY_COVERAGE_MD.read_text(encoding="utf-8"),
        "## Current Counts",
    )

    assert tables[0] == {
        label: coverage_counts.get(tier, 0)
        for tier, label in ENTRYPOINT_COVERAGE_LABELS.items()
    }
    assert tables[1] == {
        label: type_counts.get(entrypoint_type, 0)
        for entrypoint_type, label in ENTRYPOINT_TYPE_LABELS.items()
    }


def test_canonical_line_number_source_refs_are_in_bounds() -> None:
    source_tables = (
        (TRACKER, "canonical_id"),
        (OWNER_GATED_SCENARIOS, "gate_id"),
        (OWNER_GATED_RESULTS, "gate_id"),
        (OPEN_QUESTIONS, "question_id"),
    )
    line_count_cache: dict[Path, int] = {}
    invalid_refs: list[str] = []
    checked_refs = 0

    for table_path, id_field in source_tables:
        with table_path.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            row_id = row.get(id_field, "<missing id>")
            for value in row.values():
                for ref, line_no in _source_line_refs(value or ""):
                    checked_refs += 1
                    path = _resolve_source_ref(row, ref)
                    if path is None:
                        invalid_refs.append(f"{table_path.name}:{row_id}: unresolved {ref}:{line_no}")
                        continue
                    if not path.exists():
                        invalid_refs.append(f"{table_path.name}:{row_id}: missing {ref}:{line_no}")
                        continue
                    if path not in line_count_cache:
                        line_count_cache[path] = len(path.read_text(encoding="utf-8").splitlines())
                    if line_no <= 0 or line_no > line_count_cache[path]:
                        invalid_refs.append(
                            f"{table_path.name}:{row_id}: out-of-bounds {ref}:{line_no} "
                            f"(file has {line_count_cache[path]} lines)"
                        )

    assert checked_refs == 352
    assert not invalid_refs


def test_canonical_audit_artifacts_are_linked_from_developer_navigation() -> None:
    missing_files = [
        artifact
        for artifact in NAVIGATION_ARTIFACTS
        if not (REPO_ROOT / "docs" / "developer" / artifact).exists()
    ]
    missing_files.extend(
        artifact
        for artifact in WORK_ORDER_NAVIGATION_ARTIFACTS
        if not (REPO_ROOT / artifact).exists()
    )
    assert not missing_files

    docs_index = DOCS_INDEX.read_text(encoding="utf-8")
    repository_map = REPOSITORY_MAP.read_text(encoding="utf-8")
    developer_guide = DEVELOPER_GUIDE.read_text(encoding="utf-8")
    work_orders_readme = WORK_ORDERS_README.read_text(encoding="utf-8")
    work_order_body = WORK_ORDER.read_text(encoding="utf-8")
    combined_navigation = "\n".join((docs_index, repository_map, developer_guide))

    missing_from_repository_map = [
        artifact for artifact in NAVIGATION_ARTIFACTS if artifact not in repository_map
    ]
    missing_from_navigation = [
        artifact for artifact in NAVIGATION_ARTIFACTS if artifact not in combined_navigation
    ]
    missing_work_order_artifacts = [
        artifact
        for artifact in WORK_ORDER_NAVIGATION_ARTIFACTS
        if artifact not in combined_navigation or artifact not in repository_map
    ]
    missing_from_work_order_scope = [
        f"docs/developer/{artifact}"
        for artifact in NAVIGATION_ARTIFACTS
        if f"docs/developer/{artifact}" not in work_order_body
    ]

    assert not missing_from_repository_map
    assert not missing_from_navigation
    assert not missing_work_order_artifacts
    assert not missing_from_work_order_scope
    assert "pokrov-canonical-feature-tracker.md" in docs_index
    assert "pokrov-owner-gated-scenarios.md" in docs_index
    assert "pokrov-open-questions.md" in docs_index
    assert "COMPLETION-AUDIT.csv" in docs_index
    assert "COMPLETION-AUDIT.csv" in repository_map
    assert "COMPLETION-AUDIT.csv" in developer_guide
    assert "Feature Story Audit Artifacts" in developer_guide
    assert "2026-06-27--repo-feature-story-audit" in work_orders_readme
    assert "2026-06-27--repo-feature-story-audit/INDEX.md" in work_orders_readme


def test_canonical_audit_history_does_not_present_stale_counts_as_current() -> None:
    checked_docs = {
        "tracker": TRACKER_MD.read_text(encoding="utf-8"),
        "work_order": WORK_ORDER.read_text(encoding="utf-8"),
    }
    forbidden_fragments = (
        "current active set to 119 scripts",
        "regenerated evidence audit reports 520 direct file refs",
        "current CSV has `520` `Retest passed`",
        "latest regenerated audit has 521 rows",
        "now reports 520 direct refs",
        "now reports `500` direct file refs",
        "current generated inventory and symbol coverage have `4577` rows",
    )
    violations = [
        f"{name}: {fragment}"
        for name, body in checked_docs.items()
        for fragment in forbidden_fragments
        if fragment in body
    ]

    assert not violations


def test_canonical_audit_markdown_has_no_mojibake_markers() -> None:
    violations: list[str] = []
    for path in CANONICAL_AUDIT_TEXT_FILES:
        body = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(body.splitlines(), 1):
            for marker in MOJIBAKE_MARKERS:
                if marker in line:
                    violations.append(f"{path.relative_to(REPO_ROOT)}:{line_number}: {marker}")

    assert not violations


def test_canonical_audit_csv_has_no_mojibake_markers() -> None:
    violations: list[str] = []
    for path in CANONICAL_AUDIT_CSV_FILES:
        body = path.read_text(encoding="utf-8-sig")
        for line_number, line in enumerate(body.splitlines(), 1):
            for marker in MOJIBAKE_MARKERS:
                if marker in line:
                    violations.append(f"{path.relative_to(REPO_ROOT)}:{line_number}: {marker}")

    assert not violations


def test_generated_story_evidence_artifacts_match_canonical_files(tmp_path: Path) -> None:
    module = _load_module()
    story_out = tmp_path / "story-evidence.csv"
    entrypoint_out = tmp_path / "entrypoint-story-coverage.csv"

    result = module.main(
        [
            "--out",
            str(story_out),
            "--entrypoint-out",
            str(entrypoint_out),
            "--updated-at",
            "2026-06-27",
        ]
    )

    assert result == 0
    assert story_out.read_text(encoding="utf-8") == STORY_AUDIT.read_text(
        encoding="utf-8"
    )
    assert entrypoint_out.read_text(
        encoding="utf-8"
    ) == (
        REPO_ROOT
        / "docs"
        / "developer"
        / "pokrov-entrypoint-story-coverage.csv"
    ).read_text(encoding="utf-8")


def test_story_retest_proof_status_is_direct_or_manual() -> None:
    with STORY_AUDIT.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    status_counts = Counter(row.get("retest_proof_status", "") for row in rows)
    invalid_rows: list[str] = []
    for row in rows:
        status = row.get("retest_proof_status", "")
        if row.get("story_status") == "Manual owner test":
            if status != "manual_owner_gate_open":
                invalid_rows.append(f"{row['canonical_id']}: {status}")
        elif status != "direct_test_ref_passed":
            invalid_rows.append(f"{row['canonical_id']}: {status}")

    weak_statuses = {
        "direct_test_ref_without_pass_result",
        "stale_test_ref",
        "imported_pass_without_direct_ref",
        "pass_without_direct_ref",
        "weak_or_missing_retest_evidence",
        "",
    }

    assert not invalid_rows
    manual_owner_rows = sum(row.get("story_status") == "Manual owner test" for row in rows)
    assert status_counts["direct_test_ref_passed"] == len(rows) - manual_owner_rows
    assert status_counts["manual_owner_gate_open"] == manual_owner_rows
    assert sum(status_counts[status] for status in weak_statuses) == 0


def test_defect_fix_retest_ledger_matches_canonical_defects() -> None:
    with TRACKER.open("r", encoding="utf-8", newline="") as f:
        tracker_rows = list(csv.DictReader(f))
    with DEFECT_FIX_RETEST_LEDGER.open("r", encoding="utf-8", newline="") as f:
        ledger_rows = list(csv.DictReader(f))

    defect_rows = [
        row for row in tracker_rows if row.get("defects_or_issues", "").strip()
    ]
    expected_ids = {row["canonical_id"] for row in defect_rows}
    actual_ids = {row["canonical_id"] for row in ledger_rows}
    closure_counts = Counter(row.get("closure_status", "") for row in ledger_rows)
    invalid_rows: list[str] = []
    for row in ledger_rows:
        for field in (
            "ledger_id",
            "canonical_id",
            "defect_area",
            "defect_or_issue",
            "fix_status",
            "retest_status",
            "retest_proof_status",
            "closure_status",
            "proof_refs",
            "next_action",
        ):
            if not row.get(field, "").strip():
                invalid_rows.append(f"{row.get('ledger_id', '<missing id>')}: {field}")
        if row.get("retest_proof_status") != "direct_test_ref_passed":
            invalid_rows.append(
                f"{row.get('ledger_id', '<missing id>')}: proof={row.get('retest_proof_status')}"
            )
        if row.get("closure_status") not in {
            "closed_retested",
            "closed_retested_no_product_change",
        }:
            invalid_rows.append(
                f"{row.get('ledger_id', '<missing id>')}: closure={row.get('closure_status')}"
            )
        if int(row.get("proof_ref_count") or 0) <= 0:
            invalid_rows.append(f"{row.get('ledger_id', '<missing id>')}: proof_ref_count")

    assert actual_ids == expected_ids
    assert len(ledger_rows) == len(defect_rows) == 18
    assert closure_counts["closed_retested"] == 16
    assert closure_counts["closed_retested_no_product_change"] == 2
    assert not invalid_rows


def test_defect_fix_retest_markdown_summary_matches_csv() -> None:
    with DEFECT_FIX_RETEST_LEDGER.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

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
    tables = _markdown_count_tables_after_heading(
        DEFECT_FIX_RETEST_LEDGER_MD.read_text(encoding="utf-8"),
        "## Current Counts",
    )

    assert tables[0] == {
        "Defect rows": len(rows),
        "Closed and retested rows": closure_counts.get("closed_retested", 0),
        "Closed no-product-change rows": closure_counts.get(
            "closed_retested_no_product_change", 0
        ),
        "Rows needing retest proof": closure_counts.get("needs_retest_proof", 0),
        "Manual owner-gate defect rows": closure_counts.get("manual_owner_gate_open", 0),
        "Open or weak closure rows": weak_count,
    }
    assert tables[1] == dict(sorted(closure_counts.items()))
    assert tables[2] == dict(sorted(area_counts.items()))
    assert tables[3] == dict(sorted(subsystem_counts.items()))


def test_generated_defect_fix_retest_ledger_matches_canonical_files(tmp_path: Path) -> None:
    module = _load_defect_ledger_module()
    csv_out = tmp_path / "defect-ledger.csv"
    md_out = tmp_path / "defect-ledger.md"

    rows = module.build_rows(
        tracker_path=TRACKER,
        story_audit_path=STORY_AUDIT,
    )
    module.write_csv(rows, csv_out)
    module.write_markdown(rows, md_out)

    assert csv_out.read_text(encoding="utf-8") == DEFECT_FIX_RETEST_LEDGER.read_text(
        encoding="utf-8"
    )
    assert md_out.read_text(encoding="utf-8") == DEFECT_FIX_RETEST_LEDGER_MD.read_text(
        encoding="utf-8"
    )


def test_canonical_code_evidence_source_refs_exist() -> None:
    with TRACKER.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    missing: list[str] = []
    unresolved: list[str] = []
    for row in rows:
        for ref in _source_refs(row.get("code_evidence", "")):
            path = _resolve_source_ref(row, ref)
            if path is None:
                unresolved.append(f"{row['canonical_id']}: {ref}")
            elif not path.exists():
                missing.append(f"{row['canonical_id']}: {ref}")

    assert not unresolved
    assert not missing


def test_canonical_code_evidence_uses_concrete_source_refs() -> None:
    with TRACKER.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    wildcard_refs = [
        f"{row['canonical_id']}: {row.get('code_evidence', '')}"
        for row in rows
        if "*" in row.get("code_evidence", "")
    ]

    assert not wildcard_refs


def test_canonical_code_evidence_has_resolvable_refs() -> None:
    with TRACKER.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    missing_resolvable_refs: list[str] = []
    for row in rows:
        refs = _source_refs(row.get("code_evidence", ""))
        resolved = [
            path
            for ref in refs
            if (path := _resolve_source_ref(row, ref)) is not None and path.exists()
        ]
        if not resolved:
            missing_resolvable_refs.append(
                f"{row['canonical_id']}: {row.get('code_evidence', '')}"
            )

    assert not missing_resolvable_refs


def test_canonical_source_trackers_are_resolvable() -> None:
    generated_sources = {
        "generated from portal_bot/api.py route decorators": REPO_ROOT
        / "portal_bot"
        / "api.py",
        "generated from scripts/manifest.yaml": REPO_ROOT / "scripts" / "manifest.yaml",
    }
    with TRACKER.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    unresolved: list[str] = []
    for row in rows:
        raw_tracker = row.get("source_tracker", "").strip()
        if raw_tracker in generated_sources:
            if not generated_sources[raw_tracker].exists():
                unresolved.append(f"{row['canonical_id']}: {raw_tracker}")
            continue

        normalized = raw_tracker.replace("\\", "/")
        candidates = []
        tracker_path = Path(raw_tracker)
        if tracker_path.is_absolute():
            candidates.append(tracker_path)
        candidates.append(REPO_ROOT / normalized)
        if normalized.startswith("POKROV-app/"):
            candidates.append(REPO_ROOT.parent / normalized)

        if not any(candidate.exists() for candidate in candidates):
            unresolved.append(f"{row['canonical_id']}: {raw_tracker}")

    assert not unresolved


def test_owner_gated_scenarios_are_explicit_and_resolvable() -> None:
    required_gate_ids = {
        "OWNER-GATE-ANDROID-PHYSICAL-INSTALL-CONNECT",
        "OWNER-GATE-WINDOWS-INSTALL-CONNECT",
        "OWNER-GATE-TELEGRAM-WEBAPP-SESSION",
        "OWNER-GATE-PAYMENT-DASHBOARD-MATURITY",
        "OWNER-GATE-SIGNING-STORE-TRUST",
        "OWNER-GATE-LIVE-DEPLOY-APP-SESSION",
        "OWNER-GATE-RU-ORIGIN-PROBE",
        "OWNER-GATE-WARP-RUNTIME-RELEASE-BUILD",
    }
    allowed_labels = {
        "PASS",
        "FAIL",
        "MANUAL_OWNER_TEST",
        "OPERATOR_ATTESTED",
        "SKIPPED_BY_OWNER",
        "BLOCKED_BY_ACCESS",
        "NOT_REQUESTED",
        "NOT_APPLICABLE",
    }
    required_fields = (
        "gate_id",
        "canonical_row",
        "gate_area",
        "current_status",
        "required_for_goal_completion",
        "blocking_question_id",
        "scenario",
        "expected_behavior",
        "required_evidence",
        "allowed_result_labels",
        "source_docs",
        "claim_guardrail",
        "next_action",
    )
    required_result_fields = (
        "gate_id",
        "current_status",
        "latest_result",
        "evidence_ref",
        "defects_or_issues",
        "fix_status",
        "retest_status",
        "owner_or_access_note",
        "next_action",
        "updated_at",
    )

    with OWNER_GATED_SCENARIOS.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    with OWNER_GATED_RESULTS.open("r", encoding="utf-8", newline="") as f:
        result_rows = list(csv.DictReader(f))
    with TRACKER.open("r", encoding="utf-8", newline="") as f:
        tracker_rows = list(csv.DictReader(f))
    with OPEN_QUESTIONS.open("r", encoding="utf-8", newline="") as f:
        question_rows = {row["question_id"]: row for row in csv.DictReader(f)}

    gate_ids = {row["gate_id"] for row in rows}
    missing_required_gate_ids = sorted(required_gate_ids - gate_ids)
    duplicate_gate_ids = sorted(
        gate_id for gate_id in gate_ids if sum(row["gate_id"] == gate_id for row in rows) > 1
    )
    result_gate_ids = {row["gate_id"] for row in result_rows}
    result_rows_by_gate = {row["gate_id"]: row for row in result_rows}
    missing_result_gate_ids = sorted(gate_ids - result_gate_ids)
    extra_result_gate_ids = sorted(result_gate_ids - gate_ids)
    duplicate_result_gate_ids = sorted(
        gate_id
        for gate_id in result_gate_ids
        if sum(row["gate_id"] == gate_id for row in result_rows) > 1
    )
    assert not missing_required_gate_ids
    assert not duplicate_gate_ids
    assert not missing_result_gate_ids
    assert not extra_result_gate_ids
    assert not duplicate_result_gate_ids

    manual_canonical_ids = {
        row["canonical_id"]
        for row in tracker_rows
        if row.get("story_status") == "Manual owner test"
    }
    scenario_canonical_ids = {row.get("canonical_row", "") for row in rows}
    manual_without_scenarios = sorted(manual_canonical_ids - scenario_canonical_ids)
    scenarios_without_manual_row = sorted(scenario_canonical_ids - manual_canonical_ids)
    invalid_rows: list[str] = []
    invalid_labels: list[str] = []
    missing_docs: list[str] = []
    invalid_results: list[str] = []
    open_required_gates = []
    for row in rows:
        gate_id = row.get("gate_id", "<missing gate>")
        for field in required_fields:
            if not row.get(field, "").strip():
                invalid_rows.append(f"{gate_id}: {field}")
        if row.get("current_status") not in allowed_labels:
            invalid_labels.append(f"{gate_id}: {row.get('current_status')}")
        for label in row.get("allowed_result_labels", "").split(";"):
            if label and label not in allowed_labels:
                invalid_labels.append(f"{gate_id}: {label}")
        required_for_completion = row.get("required_for_goal_completion", "")
        if required_for_completion not in {"yes", "no"}:
            invalid_rows.append(
                f"{gate_id}: required_for_goal_completion={required_for_completion}"
            )
        blocking_question_id = row.get("blocking_question_id", "")
        blocking_question = question_rows.get(blocking_question_id)
        if blocking_question is None:
            invalid_rows.append(f"{gate_id}: unknown blocking_question_id={blocking_question_id}")
        elif blocking_question.get("blocks_goal_completion") != "yes":
            invalid_rows.append(
                f"{gate_id}: blocking_question_id={blocking_question_id} does not block goal"
            )
        if blocking_question_id != "Q-004":
            invalid_rows.append(f"{gate_id}: blocking_question_id={blocking_question_id}")
        if required_for_completion == "yes" and row.get("current_status") in {
            "MANUAL_OWNER_TEST",
            "BLOCKED_BY_ACCESS",
        }:
            open_required_gates.append(gate_id)
        if required_for_completion == "no" and row.get("current_status") not in {
            "NOT_REQUESTED",
            "NOT_APPLICABLE",
            "PASS",
            "OPERATOR_ATTESTED",
            "SKIPPED_BY_OWNER",
        }:
            invalid_rows.append(
                f"{gate_id}: optional gate has active status {row.get('current_status')}"
            )
        for ref in _source_refs(row.get("source_docs", "")):
            path = _resolve_source_ref({"subsystem": "POKROV client app"}, ref)
            if path is None or not path.exists():
                missing_docs.append(f"{gate_id}: {ref}")
        result = result_rows_by_gate[gate_id]
        for field in required_result_fields:
            if field in {"evidence_ref", "defects_or_issues"}:
                continue
            if not result.get(field, "").strip():
                invalid_results.append(f"{gate_id}: {field}")
        if result.get("current_status") != row.get("current_status"):
            invalid_results.append(
                f"{gate_id}: result current_status={result.get('current_status')} scenario current_status={row.get('current_status')}"
            )
        status = result.get("current_status", "")
        latest_result = result.get("latest_result", "")
        evidence_ref = result.get("evidence_ref", "").strip()
        defects_or_issues = result.get("defects_or_issues", "").strip()
        fix_status = result.get("fix_status", "")
        retest_status = result.get("retest_status", "")
        owner_or_access_note = result.get("owner_or_access_note", "")
        status_context = " ".join(
            (latest_result, evidence_ref, fix_status, retest_status, owner_or_access_note)
        ).lower()

        if status not in allowed_labels:
            invalid_labels.append(f"{gate_id}: result {status}")
        if status in {"PASS", "OPERATOR_ATTESTED"} and not evidence_ref:
            invalid_results.append(f"{gate_id}: evidence_ref required for pass/attestation")
        for evidence_ref in _source_refs(result.get("evidence_ref", "")):
            evidence_path = _resolve_source_ref({"subsystem": "POKROV client app"}, evidence_ref)
            if evidence_path is None or not evidence_path.exists():
                invalid_results.append(f"{gate_id}: unresolved evidence_ref {evidence_ref}")
        if status == "PASS":
            if retest_status != "Retest passed":
                invalid_results.append(f"{gate_id}: PASS requires Retest passed")
            if fix_status not in {"Not needed", "Fixed"}:
                invalid_results.append(f"{gate_id}: PASS has unexpected fix_status={fix_status}")
        if status == "OPERATOR_ATTESTED" and "attest" not in status_context:
            invalid_results.append(f"{gate_id}: OPERATOR_ATTESTED requires attestation context")
        if status == "FAIL" and not defects_or_issues:
            invalid_results.append(f"{gate_id}: defects_or_issues required for FAIL")
        if status == "FAIL":
            if retest_status != "Needs retest":
                invalid_results.append(f"{gate_id}: FAIL requires Needs retest")
            if fix_status not in {"Needs fix", "Blocked by access"}:
                invalid_results.append(f"{gate_id}: FAIL has unexpected fix_status={fix_status}")
        if status == "BLOCKED_BY_ACCESS":
            if not result.get("evidence_ref", "").strip():
                invalid_results.append(f"{gate_id}: BLOCKED_BY_ACCESS requires evidence_ref")
            if "access" not in status_context:
                invalid_results.append(f"{gate_id}: BLOCKED_BY_ACCESS requires access context")
        if status == "SKIPPED_BY_OWNER":
            if "owner" not in status_context:
                invalid_results.append(f"{gate_id}: SKIPPED_BY_OWNER requires owner context")
            if "skip" not in status_context and "not requested" not in status_context:
                invalid_results.append(f"{gate_id}: SKIPPED_BY_OWNER requires skip context")
        if status == "NOT_REQUESTED":
            if required_for_completion != "no":
                invalid_results.append(f"{gate_id}: NOT_REQUESTED is only for optional gates")
            if retest_status != "Not requested":
                invalid_results.append(f"{gate_id}: NOT_REQUESTED requires Not requested retest")
        if status == "MANUAL_OWNER_TEST" and retest_status != "Manual owner test":
            invalid_results.append(f"{gate_id}: MANUAL_OWNER_TEST requires Manual owner test")

    summary = OWNER_GATED_SCENARIOS_MD.read_text(encoding="utf-8")
    execution_guide = OWNER_GATED_EXECUTION_GUIDE.read_text(encoding="utf-8")
    for row in rows:
        assert row["gate_area"] in summary
        assert row["canonical_row"] in summary
        assert row["blocking_question_id"] in summary
        assert row["gate_id"] in execution_guide
        assert row["required_evidence"].split(";")[0] in execution_guide
    assert "CLIENT_APP-US-067" in summary
    assert "pokrov-owner-gated-scenarios.csv" in summary
    assert "pokrov-owner-gated-results.csv" in summary
    assert "pokrov-owner-gated-execution-guide.md" in summary
    assert "pokrov-owner-gated-scenarios.csv" in execution_guide
    assert "pokrov-owner-gated-results.csv" in execution_guide
    for label in allowed_labels:
        assert label in execution_guide
    for status_rule in (
        "`PASS` requires `evidence_ref`",
        "`FAIL` requires `defects_or_issues`",
        "`BLOCKED_BY_ACCESS` requires `evidence_ref`",
        "`SKIPPED_BY_OWNER` requires owner",
        "`NOT_REQUESTED` is allowed only for conditional gates",
    ):
        assert status_rule in execution_guide
    for field in required_fields:
        assert f"`{field}`" in execution_guide
    for field in required_result_fields:
        assert f"`{field}`" in execution_guide
    assert f"Required owner-gated scenarios still open: {len(open_required_gates)}" in summary
    assert "pokrov-owner-gated-scenarios.csv" in COMPLETION_AUDIT.read_text(
        encoding="utf-8"
    )
    assert "pokrov-owner-gated-results.csv" in COMPLETION_AUDIT.read_text(
        encoding="utf-8"
    )
    assert (
        f"required owner-gated scenarios still open: {len(open_required_gates)}"
        in COMPLETION_AUDIT.read_text(encoding="utf-8")
    )

    assert not invalid_rows
    assert not invalid_labels
    assert not missing_docs
    assert not invalid_results
    assert not manual_without_scenarios
    assert not scenarios_without_manual_row


def test_open_questions_ledger_tracks_owner_blockers() -> None:
    required_question_ids = {"Q-001", "Q-002", "Q-003", "Q-004"}
    blocking_question_ids = {"Q-004"}
    required_fields = (
        "question_id",
        "category",
        "status",
        "blocks_goal_completion",
        "question",
        "default_assumption",
        "required_owner_answer",
        "current_action",
        "source_refs",
        "updated_at",
    )

    with OPEN_QUESTIONS.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    question_ids = {row["question_id"] for row in rows}
    duplicate_question_ids = sorted(
        question_id
        for question_id in question_ids
        if sum(row["question_id"] == question_id for row in rows) > 1
    )
    assert question_ids == required_question_ids
    assert not duplicate_question_ids

    invalid_rows: list[str] = []
    missing_refs: list[str] = []
    for row in rows:
        question_id = row.get("question_id", "<missing question>")
        for field in required_fields:
            if not row.get(field, "").strip():
                invalid_rows.append(f"{question_id}: {field}")
        if row.get("status") not in {"open", "answered"}:
            invalid_rows.append(f"{question_id}: status={row.get('status')}")
        if row.get("blocks_goal_completion") not in {"yes", "no"}:
            invalid_rows.append(
                f"{question_id}: blocks_goal_completion={row.get('blocks_goal_completion')}"
            )
        if (row.get("blocks_goal_completion") == "yes") != (
            question_id in blocking_question_ids
        ):
            invalid_rows.append(
                f"{question_id}: unexpected blocking flag {row.get('blocks_goal_completion')}"
            )
        for ref in _source_refs(row.get("source_refs", "")):
            path = _resolve_source_ref({"subsystem": ""}, ref)
            if path is None or not path.exists():
                missing_refs.append(f"{question_id}: {ref}")
    q001_row = next(row for row in rows if row["question_id"] == "Q-001")
    if q001_row.get("status") != "answered":
        invalid_rows.append("Q-001: expected answered")
    if q001_row.get("blocks_goal_completion") != "no":
        invalid_rows.append("Q-001: expected nonblocking")
    if "ACCEPT_STORY_AND_SYMBOL_TIERS" not in q001_row.get("required_owner_answer", ""):
        invalid_rows.append("Q-001: missing accepted policy code")

    tracker_body = TRACKER_MD.read_text(encoding="utf-8")
    questions_summary = OPEN_QUESTIONS_MD.read_text(encoding="utf-8")
    owner_answer_sheet = OWNER_ANSWER_SHEET.read_text(encoding="utf-8")
    coverage_policy_guide = COVERAGE_POLICY_DECISION_GUIDE.read_text(encoding="utf-8")
    completion_body = COMPLETION_AUDIT.read_text(encoding="utf-8")
    for question_id in required_question_ids:
        assert question_id in tracker_body
        assert question_id in questions_summary
    for blocking_question_id in blocking_question_ids:
        assert blocking_question_id in owner_answer_sheet
    assert "pokrov-coverage-policy-decision-guide.md" in tracker_body
    assert "pokrov-coverage-policy-decision-guide.md" in questions_summary
    assert "Q-001" in coverage_policy_guide
    assert "pokrov-open-questions.csv" in coverage_policy_guide
    assert "ACCEPT_STORY_AND_SYMBOL_TIERS" in coverage_policy_guide
    assert "REQUIRE_PUBLIC_AND_ENTRYPOINT_ONLY" in coverage_policy_guide
    assert "REQUIRE_ONE_TEST_PER_PRIVATE_HELPER" in coverage_policy_guide
    assert "pokrov-private-helper-coverage.csv" in coverage_policy_guide
    assert "pokrov-private-helper-coverage.md" in coverage_policy_guide
    assert "pokrov-private-helper-test-matrix.csv" in coverage_policy_guide
    for policy_code in (
        "ACCEPT_STORY_AND_SYMBOL_TIERS",
        "REQUIRE_PUBLIC_AND_ENTRYPOINT_ONLY",
        "REQUIRE_ONE_TEST_PER_PRIVATE_HELPER",
    ):
        assert policy_code in owner_answer_sheet
    for gate_id in (
        "OWNER-GATE-ANDROID-PHYSICAL-INSTALL-CONNECT",
        "OWNER-GATE-WINDOWS-INSTALL-CONNECT",
        "OWNER-GATE-TELEGRAM-WEBAPP-SESSION",
        "OWNER-GATE-PAYMENT-DASHBOARD-MATURITY",
        "OWNER-GATE-SIGNING-STORE-TRUST",
        "OWNER-GATE-LIVE-DEPLOY-APP-SESSION",
        "OWNER-GATE-RU-ORIGIN-PROBE",
        "OWNER-GATE-WARP-RUNTIME-RELEASE-BUILD",
    ):
        assert gate_id in owner_answer_sheet
    for answer_marker in (
        "EXECUTE OWNER-GATE-TELEGRAM-WEBAPP-SESSION",
        "SKIPPED_BY_OWNER",
        "BLOCKED_BY_ACCESS",
        "PASS",
        "pokrov-owner-gated-results.csv",
    ):
        assert answer_marker in owner_answer_sheet
    assert "pokrov-open-questions.csv" in tracker_body
    assert "pokrov-open-questions.csv" in questions_summary
    assert "pokrov-owner-answer-sheet.md" in tracker_body
    assert "pokrov-owner-answer-sheet.md" in questions_summary
    assert "pokrov-owner-answer-sheet.md" in completion_body
    assert "pokrov-open-questions.csv" in completion_body
    assert "Blocking full goal completion | 1" in questions_summary
    assert "Answered questions | 1" in questions_summary
    assert "ACCEPT_STORY_AND_SYMBOL_TIERS" in questions_summary
    assert "blocking open questions: 1" in completion_body

    assert not invalid_rows
    assert not missing_refs


def test_completion_audit_tracks_current_story_counts() -> None:
    with TRACKER.open("r", encoding="utf-8", newline="") as f:
        tracker_rows = list(csv.DictReader(f))
    with STORY_AUDIT.open("r", encoding="utf-8", newline="") as f:
        story_audit_rows = list(csv.DictReader(f))

    status_counts: dict[str, int] = {}
    for row in tracker_rows:
        status_counts[row["story_status"]] = status_counts.get(row["story_status"], 0) + 1
    evidence_counts: dict[str, int] = {}
    for row in story_audit_rows:
        evidence_counts[row["evidence_tier"]] = (
            evidence_counts.get(row["evidence_tier"], 0) + 1
        )
    retest_proof_counts: dict[str, int] = {}
    for row in story_audit_rows:
        status = row.get("retest_proof_status", "")
        retest_proof_counts[status] = retest_proof_counts.get(status, 0) + 1

    body = COMPLETION_AUDIT.read_text(encoding="utf-8")
    expected_fragments = [
        f"`docs/developer/pokrov-canonical-feature-tracker.csv` has {len(tracker_rows)} rows",
        f"{status_counts['Retest passed']} `Retest passed` rows",
        f"{status_counts['Manual owner test']} `Manual owner test`",
        f"{evidence_counts['direct_file_ref']} `direct_file_ref` rows",
        f"{evidence_counts['manual_owner_gate']} `manual_owner_gate`",
        f"{retest_proof_counts['direct_test_ref_passed']} `direct_test_ref_passed` rows",
        f"{retest_proof_counts['manual_owner_gate_open']} `manual_owner_gate_open` row",
    ]

    missing = [fragment for fragment in expected_fragments if fragment not in body]
    assert not missing


def test_completion_audit_requirement_ledger_tracks_goal_scope() -> None:
    required_fields = {
        "requirement_id",
        "requirement",
        "status",
        "blocks_goal_completion",
        "blocker_relationship",
        "evidence_refs",
        "remaining_gap",
    }
    allowed_statuses = {
        "locally_proven",
        "locally_proven_for_local_suites",
        "locally_documented_and_guarded",
    }
    allowed_blocker_relationships = {
        "none",
        "related_context",
        "blocking_requirement",
    }
    required_ids = {f"REQ-{index:03d}" for index in range(1, 18)}
    required_blockers = {"Q-004"}

    with COMPLETION_AUDIT_CSV.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    ids = {row["requirement_id"] for row in rows}
    duplicate_ids = sorted(
        requirement_id
        for requirement_id in ids
        if sum(row["requirement_id"] == requirement_id for row in rows) > 1
    )
    assert ids == required_ids
    assert not duplicate_ids

    completion_body = COMPLETION_AUDIT.read_text(encoding="utf-8")
    work_order_index = WORK_ORDER_INDEX.read_text(encoding="utf-8")
    assert "COMPLETION-AUDIT.csv" in completion_body
    assert "COMPLETION-AUDIT.csv" in work_order_index
    assert "1078 canonical source-evidence file refs" in completion_body
    assert "352 explicit line refs" in completion_body
    assert "525 source-tracker refs" in completion_body
    assert "test_work_order_current_output_counts_match_csv_artifacts" in completion_body

    status_display_labels = {
        "locally_proven": "Locally proven",
        "locally_proven_for_local_suites": "Locally proven for local suites",
        "locally_documented_and_guarded": "Locally documented and guarded",
    }
    completion_lines = completion_body.splitlines()
    checklist_header = "| Requirement | Current evidence | Status | Remaining gap |"
    checklist_start = completion_lines.index(checklist_header)
    checklist_rows: list[dict[str, str]] = []
    for line in completion_lines[checklist_start + 2 :]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        checklist_rows.append(
            {
                "requirement": cells[0],
                "current_evidence": cells[1],
                "status": cells[2],
                "remaining_gap": cells[3],
            }
        )
    assert len(checklist_rows) == len(rows)
    checklist_mismatches: list[str] = []
    for row, checklist_row in zip(rows, checklist_rows):
        requirement_id = row["requirement_id"]
        if checklist_row["requirement"] != row["requirement"]:
            checklist_mismatches.append(f"{requirement_id}: requirement")
        if checklist_row["status"] != status_display_labels[row["status"]]:
            checklist_mismatches.append(
                f"{requirement_id}: status={checklist_row['status']}"
            )
        if checklist_row["remaining_gap"] != row["remaining_gap"]:
            checklist_mismatches.append(
                f"{requirement_id}: remaining_gap={checklist_row['remaining_gap']}"
            )
        if not checklist_row["current_evidence"]:
            checklist_mismatches.append(f"{requirement_id}: current_evidence")
        for evidence_ref in [
            value.strip()
            for value in row.get("evidence_refs", "").split(";")
            if value.strip()
        ]:
            path_ref, _, symbol_ref = evidence_ref.partition("::")
            markers = [path_ref, Path(path_ref).name]
            if symbol_ref:
                markers.append(symbol_ref)
            if not any(marker and marker in checklist_row["current_evidence"] for marker in markers):
                checklist_mismatches.append(
                    f"{requirement_id}: evidence not visible in Markdown row: {evidence_ref}"
                )
    assert not checklist_mismatches

    evidence_by_requirement = {
        row["requirement_id"]: row.get("evidence_refs", "") for row in rows
    }
    req_001_refs = evidence_by_requirement["REQ-001"]
    for evidence_ref in (
        "tests/test_story_test_evidence_audit.py::test_canonical_tracker_markdown_summary_matches_csv_artifacts",
        "tests/test_story_test_evidence_audit.py::test_work_order_index_imported_coverage_matches_tracker_csv",
    ):
        assert evidence_ref in req_001_refs
        assert evidence_ref.split("::", 1)[1] in completion_body
    for subsystem_fragment in (
        "525 rows: 165 backend API",
        "123 scripts/ops",
        "67 client app",
        "58 WebApp/admin",
        "57 Telegram bots",
        "55 marketing",
    ):
        assert subsystem_fragment in completion_body
    req_002_refs = evidence_by_requirement["REQ-002"]
    for evidence_ref in (
        "docs/developer/pokrov-canonical-feature-tracker.csv",
        "docs/developer/pokrov-canonical-feature-tracker.md",
        "tests/test_story_test_evidence_audit.py::test_canonical_tracker_story_contract_fields_are_populated",
    ):
        assert evidence_ref in req_002_refs
        if "::" in evidence_ref:
            assert evidence_ref.split("::", 1)[1] in completion_body
    assert "canonical story contract table" in completion_body
    assert "current missing story contract fields: 0" in completion_body
    req_003_refs = evidence_by_requirement["REQ-003"]
    for evidence_ref in (
        "tests/test_story_test_evidence_audit.py::test_canonical_tracker_status_fields_are_normalized",
        "tests/test_story_test_evidence_audit.py::test_story_retest_proof_status_is_direct_or_manual",
        "tests/test_story_test_evidence_audit.py::test_defect_fix_retest_ledger_matches_canonical_defects",
    ):
        assert evidence_ref in req_003_refs
        assert evidence_ref.split("::", 1)[1] in completion_body
    assert "docs/developer/pokrov-defect-fix-retest-ledger.csv" in req_003_refs
    assert "18 defect/fix/retest rows" in completion_body
    assert "16 `closed_retested` and 2 `closed_retested_no_product_change`" in completion_body
    req_006_refs = evidence_by_requirement["REQ-006"]
    for evidence_ref in (
        "tests/test_story_test_evidence_audit.py::test_generated_story_evidence_artifacts_match_canonical_files",
        "tests/test_story_test_evidence_audit.py::test_generated_defect_fix_retest_ledger_matches_canonical_files",
        "tests/test_code_function_inventory.py::test_generated_code_inventory_artifacts_match_canonical_files",
        "tests/test_code_function_inventory.py::test_generated_private_helper_coverage_artifacts_match_canonical_files",
    ):
        assert evidence_ref in req_006_refs
        assert evidence_ref.split("::", 1)[1] in completion_body
    assert "defect/fix/retest ledger" in completion_body
    req_005_refs = evidence_by_requirement["REQ-005"]
    for evidence_ref in (
        "docs/developer/pokrov-canonical-feature-tracker.csv",
        "docs/developer/pokrov-owner-gated-scenarios.csv",
        "docs/developer/pokrov-owner-gated-results.csv",
        "docs/developer/pokrov-open-questions.csv",
        "tests/test_story_test_evidence_audit.py::test_canonical_line_number_source_refs_are_in_bounds",
    ):
        assert evidence_ref in req_005_refs
        if "::" in evidence_ref:
            assert evidence_ref.split("::", 1)[1] in completion_body
    assert "352 `path:line` refs" in completion_body
    assert "current out-of-bounds line refs: 0" in completion_body
    req_007_refs = evidence_by_requirement["REQ-007"]
    for evidence_ref in (
        "tests/test_story_test_evidence_audit.py::test_canonical_tracker_markdown_summary_matches_csv_artifacts",
        "tests/test_story_test_evidence_audit.py::test_story_evidence_markdown_summary_matches_csv",
        "tests/test_story_test_evidence_audit.py::test_defect_fix_retest_markdown_summary_matches_csv",
        "tests/test_story_test_evidence_audit.py::test_entrypoint_coverage_markdown_summary_matches_csv",
        "tests/test_code_function_inventory.py::test_code_inventory_markdown_summary_matches_csv",
        "tests/test_code_function_inventory.py::test_symbol_coverage_markdown_summary_matches_csv",
        "tests/test_code_function_inventory.py::test_private_helper_coverage_markdown_summary_matches_csv",
    ):
        assert evidence_ref in req_007_refs
        assert evidence_ref.split("::", 1)[1] in completion_body
    assert "pokrov-defect-fix-retest-ledger.md" in completion_body
    req_008_refs = evidence_by_requirement["REQ-008"]
    for evidence_ref in (
        "tests/test_code_function_inventory.py::test_code_inventory_markdown_summary_matches_csv",
        "tests/test_code_function_inventory.py::test_generated_code_inventory_artifacts_match_canonical_files",
    ):
        assert evidence_ref in req_008_refs
        assert evidence_ref.split("::", 1)[1] in completion_body
    assert "4602 symbols across root and active `POKROV-app`" in completion_body
    assert "parser errors: 0" in completion_body
    assert "Owner accepted the current Q-001 story/symbol-tier approach on 2026-06-28" in completion_body
    req_009_refs = evidence_by_requirement["REQ-009"]
    for evidence_ref in (
        "tests/test_code_function_inventory.py::test_symbol_coverage_markdown_summary_matches_csv",
        "tests/test_code_function_inventory.py::test_symbol_coverage_rows_have_expected_behavior_from_code",
        "tests/test_code_function_inventory.py::test_generated_private_inventory_tier_contains_only_private_non_entrypoints",
    ):
        assert evidence_ref in req_009_refs
        assert evidence_ref.split("::", 1)[1] in completion_body
    assert "manual-tier rows have resolvable `manual_gate_refs`" in completion_body
    assert "80 platform/tray manual-tier rows have `manual_gate_refs`" in completion_body
    assert "6 private-inventory rows remain source-inventory-only under the accepted Q-001 policy" in completion_body
    assert "0 review-tier rows remain" in completion_body
    req_010_refs = evidence_by_requirement["REQ-010"]
    for evidence_ref in (
        "tests/test_story_test_evidence_audit.py::test_open_questions_ledger_tracks_owner_blockers",
        "tests/test_code_function_inventory.py::test_private_helper_coverage_matrix_matches_private_inventory_only",
    ):
        assert evidence_ref in req_010_refs
        assert evidence_ref.split("::", 1)[1] in completion_body
    for q001_fragment in (
        "Q-001 policy codes",
        "compact owner answer sheet",
        "private-helper decision matrix",
    ):
        assert q001_fragment in completion_body
    req_011_refs = evidence_by_requirement["REQ-011"]
    for evidence_ref in (
        "tests/test_story_test_evidence_audit.py::test_story_evidence_markdown_summary_matches_csv",
        "tests/test_story_test_evidence_audit.py::test_story_retest_proof_status_is_direct_or_manual",
        "tests/test_story_test_evidence_audit.py::test_generated_story_evidence_artifacts_match_canonical_files",
    ):
        assert evidence_ref in req_011_refs
        assert evidence_ref.split("::", 1)[1] in completion_body
    for story_evidence_fragment in (
        "524 `direct_file_ref` rows",
        "1 `manual_owner_gate`",
        "0 missing test refs",
        "source-tracker refs",
        "owner-gate rows",
    ):
        assert story_evidence_fragment in completion_body
    req_012_refs = evidence_by_requirement["REQ-012"]
    for evidence_ref in (
        "docs/developer/pokrov-owner-gated-scenarios.csv",
        "docs/developer/pokrov-owner-gated-results.csv",
        "docs/developer/pokrov-owner-gated-scenarios.md",
        "tests/test_story_test_evidence_audit.py::test_owner_gated_scenarios_are_explicit_and_resolvable",
    ):
        assert evidence_ref in req_012_refs
        if "::" in evidence_ref:
            assert evidence_ref.split("::", 1)[1] in completion_body
    for owner_gate_fragment in (
        "8 source-linked owner/operator scenarios",
        "blocking_question_id=Q-004",
        "8 matching result rows",
        "summarizes the manual matrix",
        "bidirectional linkage with all `Manual owner test` canonical rows",
        "required owner-gated scenarios still open: 2",
    ):
        assert owner_gate_fragment in completion_body
    gate_header = "| Gate ID | Status | Gate | Canonical row/question | Required owner/current evidence |"
    gate_start = completion_lines.index(gate_header)
    gate_table_rows: list[dict[str, str]] = []
    for line in completion_lines[gate_start + 2 :]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        gate_table_rows.append(
            {
                "gate_id": cells[0].replace("`", ""),
                "status": cells[1].replace("`", ""),
                "gate": cells[2],
                "canonical_row_question": cells[3],
                "required_evidence": cells[4],
            }
        )
    with OWNER_GATED_SCENARIOS.open("r", encoding="utf-8", newline="") as f:
        owner_gate_rows = list(csv.DictReader(f))
    gate_table_by_id = {
        row["gate_id"]: row
        for row in gate_table_rows
    }
    assert set(gate_table_by_id) == {row["gate_id"] for row in owner_gate_rows}
    gate_table_mismatches: list[str] = []
    for owner_gate in owner_gate_rows:
        gate_id = owner_gate["gate_id"]
        table_row = gate_table_by_id[gate_id]
        first_required_evidence = owner_gate["required_evidence"].split(";", 1)[0]
        if table_row["status"] != owner_gate["current_status"]:
            gate_table_mismatches.append(f"{gate_id}: status={table_row['status']}")
        if owner_gate["gate_area"] not in table_row["gate"]:
            gate_table_mismatches.append(f"{gate_id}: gate_area")
        for fragment in (
            owner_gate["canonical_row"],
            owner_gate["blocking_question_id"],
        ):
            if fragment not in table_row["canonical_row_question"]:
                gate_table_mismatches.append(f"{gate_id}: {fragment}")
        if first_required_evidence not in table_row["required_evidence"]:
            gate_table_mismatches.append(
                f"{gate_id}: required_evidence={first_required_evidence}"
            )
    assert not gate_table_mismatches
    assert (
        "tests/test_story_test_evidence_audit.py::test_work_order_current_output_counts_match_csv_artifacts"
        in evidence_by_requirement["REQ-004"]
    )
    req_014_refs = evidence_by_requirement["REQ-014"]
    for evidence_ref in (
        "tests/test_story_test_evidence_audit.py::test_entrypoint_coverage_markdown_summary_matches_csv",
        "tests/test_story_test_evidence_audit.py::test_generated_story_evidence_artifacts_match_canonical_files",
    ):
        assert evidence_ref in req_014_refs
        assert evidence_ref.split("::", 1)[1] in completion_body
    for entrypoint_fragment in (
        "514/514 direct mappings",
        "165 route",
        "123 script",
        "226 story",
        "needs_story_mapping_review = 0",
    ):
        assert entrypoint_fragment in completion_body
    req_015_refs = evidence_by_requirement["REQ-015"]
    for evidence_ref in (
        "docs/developer/pokrov-canonical-feature-tracker.md",
        "docs/developer/work-orders/2026-06-27--repo-feature-story-audit/WO-001-canonical-feature-tracker.md",
        "docs/developer/pokrov-defect-fix-retest-ledger.csv",
        "docs/developer/pokrov-defect-fix-retest-ledger.md",
        "tests/test_story_test_evidence_audit.py::test_defect_fix_retest_ledger_matches_canonical_defects",
        "tests/test_story_test_evidence_audit.py::test_defect_fix_retest_markdown_summary_matches_csv",
    ):
        assert evidence_ref in req_015_refs
        if "::" in evidence_ref:
            assert evidence_ref.split("::", 1)[1] in completion_body
    req_013_refs = evidence_by_requirement["REQ-013"]
    assert (
        "tests/test_story_test_evidence_audit.py::test_owner_gated_scenarios_are_explicit_and_resolvable"
        in req_013_refs
    )
    assert "allowed status label" in completion_body
    assert "first required-evidence fragment" in completion_body
    assert "audit-only drift such as `COMPLETION-SOURCE-REF-EVIDENCE-001`" in completion_body
    assert "Story-row mismatches need defect-ledger rows" in completion_body
    assert "audit-only discrepancies need closed findings with verification" in completion_body
    assert "COMPLETION-SOURCE-REF-EVIDENCE-001" in TRACKER_MD.read_text(
        encoding="utf-8"
    )
    assert "COMPLETION-SOURCE-REF-EVIDENCE-001" in WORK_ORDER.read_text(
        encoding="utf-8"
    )
    req_016_refs = evidence_by_requirement["REQ-016"]
    for evidence_ref in (
        "docs/developer/pokrov-canonical-feature-tracker.md",
        "docs/developer/work-orders/2026-06-27--repo-feature-story-audit/WO-001-canonical-feature-tracker.md",
        "docs/developer/work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.md",
        "tests/test_story_test_evidence_audit.py::test_completion_audit_requirement_ledger_tracks_goal_scope",
    ):
        assert evidence_ref in req_016_refs
        if "::" in evidence_ref:
            assert evidence_ref.split("::", 1)[1] in completion_body
    assert "requires these broad retest run IDs" in completion_body
    tracker_body_for_retests = TRACKER_MD.read_text(encoding="utf-8")
    work_order_body_for_retests = WORK_ORDER.read_text(encoding="utf-8")
    for run_id in (
        "ROOT-PYTEST-011",
        "WEBAPP-FULL-002",
        "MARKETING-RETEST-002",
        "CLIENT-TEST-003",
        "COMPLETION-DISCREPANCY-EVIDENCE-001",
    ):
        assert run_id in completion_body
        assert run_id in tracker_body_for_retests
        assert run_id in work_order_body_for_retests
    for retest_marker in (
        "765 passed, 62 warnings, 2 subtests",
        "46/46",
        "23/23",
        "41 passed",
        "Live device provider Telegram account deploy and RU checks are not inferred",
    ):
        assert retest_marker in completion_body
    for generator_command in (
        "python scripts/audit_story_test_evidence.py",
        "python scripts/generate_defect_fix_retest_ledger.py",
        "python scripts/generate_code_function_inventory.py",
        "python scripts/generate_private_helper_coverage.py",
    ):
        assert generator_command in completion_body
        generator_ref = generator_command.removeprefix("python ")
        assert (REPO_ROOT / generator_ref).exists()
        assert generator_ref in work_order_body_for_retests
    req_017_refs = evidence_by_requirement["REQ-017"]
    assert (
        "tests/test_story_test_evidence_audit.py::test_open_questions_ledger_tracks_owner_blockers"
        in req_017_refs
    )
    assert "required question IDs" in completion_body
    assert "answer-sheet policy/gate markers" in completion_body

    invalid_rows: list[str] = []
    missing_refs: list[str] = []
    missing_test_symbols: list[str] = []
    blocker_ids_seen: set[str] = set()
    blocking_rows = []
    for row in rows:
        requirement_id = row.get("requirement_id", "<missing requirement>")
        for field in required_fields:
            if not row.get(field, "").strip():
                invalid_rows.append(f"{requirement_id}: missing {field}")
        if row.get("status") not in allowed_statuses:
            invalid_rows.append(f"{requirement_id}: status={row.get('status')}")
        if row.get("blocks_goal_completion") not in {"yes", "no"}:
            invalid_rows.append(
                f"{requirement_id}: blocks_goal_completion={row.get('blocks_goal_completion')}"
            )
        blocker_relationship = row.get("blocker_relationship", "")
        if blocker_relationship not in allowed_blocker_relationships:
            invalid_rows.append(
                f"{requirement_id}: blocker_relationship={blocker_relationship}"
            )
        if row.get("blocks_goal_completion") == "yes":
            blocking_rows.append(row)
        if row.get("requirement") not in completion_body:
            invalid_rows.append(f"{requirement_id}: requirement missing from Markdown audit")
        for blocker_id in [
            value.strip()
            for value in row.get("blocker_ids", "").split(";")
            if value.strip()
        ]:
            blocker_ids_seen.add(blocker_id)
            if blocker_id not in required_blockers:
                invalid_rows.append(f"{requirement_id}: unknown blocker_id={blocker_id}")
        row_blocker_ids = [
            value.strip()
            for value in row.get("blocker_ids", "").split(";")
            if value.strip()
        ]
        if row.get("blocks_goal_completion") == "yes":
            if blocker_relationship != "blocking_requirement":
                invalid_rows.append(
                    f"{requirement_id}: blocking row must use blocking_requirement"
                )
            if not row_blocker_ids:
                invalid_rows.append(f"{requirement_id}: blocking row needs blocker_ids")
        elif row_blocker_ids:
            if blocker_relationship != "related_context":
                invalid_rows.append(
                    f"{requirement_id}: nonblocking blocker refs must use related_context"
                )
        elif blocker_relationship != "none":
            invalid_rows.append(
                f"{requirement_id}: rows without blocker_ids must use none"
            )
        for evidence_ref in [
            value.strip()
            for value in row.get("evidence_refs", "").split(";")
            if value.strip()
        ]:
            path_ref = evidence_ref.split("::", 1)[0]
            if not any(path_ref.endswith(suffix) for suffix in (".csv", ".md", ".py")):
                continue
            path = _resolve_source_ref({"subsystem": ""}, path_ref)
            if path is None or not path.exists():
                missing_refs.append(f"{requirement_id}: {evidence_ref}")
                continue
            if "::" in evidence_ref and path_ref.endswith(".py"):
                symbol = evidence_ref.split("::", 1)[1]
                pattern = rf"^\s*def\s+{re.escape(symbol)}\s*\("
                if re.search(pattern, path.read_text(encoding="utf-8"), re.MULTILINE) is None:
                    missing_test_symbols.append(f"{requirement_id}: {evidence_ref}")

    assert len(rows) == 17
    assert len(blocking_rows) == 2
    assert blocker_ids_seen == required_blockers
    relationship_counts = Counter(row["blocker_relationship"] for row in rows)
    status_counts = Counter(row["status"] for row in rows)
    completion_tables = _markdown_count_tables_after_heading(
        completion_body,
        "## Machine Ledger Counts",
    )
    assert completion_tables[0] == {
        "Completion requirement rows": len(rows),
        "Blocking requirement rows": relationship_counts.get("blocking_requirement", 0),
        "Related context rows": relationship_counts.get("related_context", 0),
        "No blocker context rows": relationship_counts.get("none", 0),
    }
    assert completion_tables[1] == dict(status_counts)
    assert not invalid_rows
    assert not missing_refs
    assert not missing_test_symbols


def test_canonical_tracker_status_fields_are_normalized() -> None:
    with TRACKER.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    allowed_story_statuses = {"Retest passed", "Manual owner test"}
    bad_story_statuses: list[str] = []
    empty_status_fields: list[str] = []
    stale_latest_failures: list[str] = []
    manual_without_owner_note: list[str] = []

    for row in rows:
        canonical_id = row["canonical_id"]
        if row.get("story_status") not in allowed_story_statuses:
            bad_story_statuses.append(
                f"{canonical_id}: {row.get('story_status', '')}"
            )
        for field in ("latest_result", "fix_status", "retest_status", "next_action"):
            if not row.get(field, "").strip():
                empty_status_fields.append(f"{canonical_id}: {field}")
        if row.get("story_status") == "Retest passed" and re.search(
            r"\b(?:fail|failed|issue|exposed)\b",
            row.get("latest_result", ""),
            flags=re.IGNORECASE,
        ):
            stale_latest_failures.append(
                f"{canonical_id}: {row.get('latest_result', '')}"
            )
        if row.get("story_status") == "Manual owner test" and not row.get(
            "owner_or_access_note", ""
        ).strip():
            manual_without_owner_note.append(canonical_id)

    assert not bad_story_statuses
    assert not empty_status_fields
    assert not stale_latest_failures
    assert not manual_without_owner_note


def test_canonical_tracker_story_contract_fields_are_populated() -> None:
    with TRACKER.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    required_fields = (
        "canonical_id",
        "subsystem",
        "surface",
        "feature",
        "user_story",
        "expected_behavior",
        "code_evidence",
        "canon_guardrails",
        "test_method",
    )
    missing: list[str] = []
    priority_only_guardrails: list[str] = []
    for row in rows:
        canonical_id = row.get("canonical_id", "<missing id>")
        for field in required_fields:
            if not row.get(field, "").strip():
                missing.append(f"{canonical_id}: {field}")
        if re.fullmatch(r"P\d+", row.get("canon_guardrails", "").strip()):
            priority_only_guardrails.append(
                f"{canonical_id}: {row.get('canon_guardrails', '')}"
            )

    assert not missing
    assert not priority_only_guardrails


def test_story_test_evidence_audit_classifies_refs_imports_and_manual_gates(
    tmp_path: Path,
) -> None:
    module = _load_module()
    repo = tmp_path / "repo"
    client = tmp_path / "POKROV-app"
    (repo / "tests").mkdir(parents=True)
    (
        client
        / "apps"
        / "android_shell"
        / "android"
        / "app"
        / "src"
        / "test"
        / "kotlin"
        / "space"
        / "pokrov"
    ).mkdir(parents=True)
    (repo / "tests" / "test_story.py").write_text("def test_story(): pass\n", encoding="utf-8")
    (
        client
        / "apps"
        / "android_shell"
        / "android"
        / "app"
        / "src"
        / "test"
        / "kotlin"
        / "space"
        / "pokrov"
        / "AndroidRuntimeStateTest.kt"
    ).write_text("class AndroidRuntimeStateTest\n", encoding="utf-8")
    tracker = repo / "tracker.csv"
    fields = [
        "canonical_id",
        "subsystem",
        "source_tracker",
        "feature",
        "story_status",
        "test_method",
        "code_evidence",
        "latest_result",
        "retest_status",
        "owner_or_access_note",
    ]
    rows = [
        {
            "canonical_id": "A",
            "subsystem": "Backend API",
            "source_tracker": "generated",
            "feature": "Direct",
            "story_status": "Retest passed",
            "test_method": r"Test refs: tests\test_story.py",
            "code_evidence": "",
            "latest_result": "PASS",
            "retest_status": "",
            "owner_or_access_note": "",
        },
        {
            "canonical_id": "B",
            "subsystem": "Marketing site",
            "source_tracker": r"outputs\marketing.xlsx",
            "feature": "Imported",
            "story_status": "Pass",
            "test_method": "Unit/static smoke",
            "code_evidence": "",
            "latest_result": "Source workbook says passed",
            "retest_status": "",
            "owner_or_access_note": "",
        },
        {
            "canonical_id": "K",
            "subsystem": "POKROV client app",
            "source_tracker": "client.xlsx",
            "feature": "Kotlin",
            "story_status": "Retest passed",
            "test_method": "POKROV-app/apps/android_shell/android/app/src/test/kotlin/space/pokrov/AndroidRuntimeStateTest.kt",
            "code_evidence": "",
            "latest_result": "PASS",
            "retest_status": "",
            "owner_or_access_note": "",
        },
        {
            "canonical_id": "C",
            "subsystem": "Scripts and Ops",
            "source_tracker": "generated",
            "feature": "Stale",
            "story_status": "Retest passed",
            "test_method": "tests/missing_test.py",
            "code_evidence": "",
            "latest_result": "PASS",
            "retest_status": "",
            "owner_or_access_note": "",
        },
        {
            "canonical_id": "D",
            "subsystem": "POKROV client app",
            "source_tracker": "client.xlsx",
            "feature": "Manual",
            "story_status": "Manual owner test",
            "test_method": "Release docs",
            "code_evidence": "",
            "latest_result": "Manual owner test",
            "retest_status": "",
            "owner_or_access_note": "Requires physical device",
        },
    ]
    with tracker.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    audit = module.build_audit(repo, tracker, "2026-06-27")
    by_id = {row["canonical_id"]: row for row in audit}

    assert by_id["A"]["evidence_tier"] == "direct_file_ref"
    assert by_id["A"]["test_refs"] == "tests/test_story.py"
    assert by_id["A"]["missing_test_ref_count"] == "0"
    assert by_id["B"]["evidence_tier"] == "imported_pass_no_file_ref"
    assert by_id["K"]["evidence_tier"] == "direct_file_ref"
    assert by_id["K"]["test_refs"] == "POKROV-app/apps/android_shell/android/app/src/test/kotlin/space/pokrov/AndroidRuntimeStateTest.kt"
    assert by_id["C"]["evidence_tier"] == "stale_file_ref"
    assert by_id["C"]["missing_test_refs"] == "tests/missing_test.py"
    assert by_id["D"]["evidence_tier"] == "manual_owner_gate"


def test_entrypoint_audit_maps_routes_handlers_scripts_and_pages(tmp_path: Path) -> None:
    module = _load_module()
    repo = tmp_path / "repo"
    (repo / "tests").mkdir(parents=True)
    (repo / "webapp" / "e2e").mkdir(parents=True)
    (repo / "tests" / "test_backend.py").write_text("def test_backend(): pass\n", encoding="utf-8")
    (repo / "tests" / "test_bot.py").write_text("def test_bot(): pass\n", encoding="utf-8")
    (repo / "tests" / "test_script.py").write_text("def test_script(): pass\n", encoding="utf-8")
    (repo / "webapp" / "e2e" / "admin-gate.spec.ts").write_text("test('admin', () => {})\n", encoding="utf-8")

    tracker = repo / "tracker.csv"
    tracker_fields = [
        "canonical_id",
        "subsystem",
        "source_tracker",
        "feature",
        "user_story",
        "expected_behavior",
        "route_or_trigger",
        "story_status",
        "test_method",
        "code_evidence",
        "latest_result",
        "retest_status",
        "owner_or_access_note",
    ]
    with tracker.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=tracker_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            [
                {
                    "canonical_id": "TG-001",
                    "subsystem": "Telegram bots",
                    "source_tracker": "generated",
                    "feature": "Admin mass",
                    "user_story": "Admin can run mass action",
                    "expected_behavior": "mass_remind_expiring run is guarded",
                    "route_or_trigger": "admin_mass; mass_remind_expiring*",
                    "story_status": "Retest passed",
                    "test_method": "Direct refs: tests/test_bot.py",
                    "code_evidence": "portal_bot/bot.py:100,120",
                    "latest_result": "PASS",
                    "retest_status": "",
                    "owner_or_access_note": "",
                },
                {
                    "canonical_id": "WEB-001",
                    "subsystem": "WebApp and Admin",
                    "source_tracker": "generated",
                    "feature": "Admin",
                    "user_story": "Admin can open dashboard",
                    "expected_behavior": "Admin route renders",
                    "route_or_trigger": "/admin",
                    "story_status": "Retest passed",
                    "test_method": "Direct refs: webapp/e2e/admin-gate.spec.ts",
                    "code_evidence": r"webapp\src\app\(admin)\admin\page.tsx",
                    "latest_result": "PASS",
                    "retest_status": "",
                    "owner_or_access_note": "",
                },
                {
                    "canonical_id": "CLIENT-001",
                    "subsystem": "POKROV client app",
                    "source_tracker": "generated",
                    "feature": "Rules",
                    "user_story": "Client can show route rules",
                    "expected_behavior": "Rules surface uses route labels and helper formatting",
                    "route_or_trigger": "",
                    "story_status": "Retest passed",
                    "test_method": "Direct refs: POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart",
                    "code_evidence": "packages/app_shell/lib/src/features/rules/rules_surface.dart",
                    "latest_result": "PASS",
                    "retest_status": "",
                    "owner_or_access_note": "",
                },
            ]
        )

    entrypoints = repo / "entrypoints.csv"
    entrypoint_fields = [
        "entry_id",
        "entry_type",
        "subsystem",
        "surface",
        "trigger_or_path",
        "handler_or_component",
        "code_evidence",
        "coverage_note",
        "updated_at",
    ]
    with entrypoints.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=entrypoint_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            [
                {
                    "entry_id": "API-001",
                    "entry_type": "fastapi_route",
                    "subsystem": "Backend API",
                    "surface": "health",
                    "trigger_or_path": "GET /api/health",
                    "handler_or_component": "health",
                    "code_evidence": "portal_bot/api.py:10",
                    "coverage_note": "",
                    "updated_at": "2026-06-27",
                },
                {
                    "entry_id": "TG-001",
                    "entry_type": "aiogram_handler",
                    "subsystem": "Telegram bots",
                    "surface": "admin",
                    "trigger_or_path": "router.callback_query(F.data == 'mass_remind_expiring_run')",
                    "handler_or_component": "mass_remind_expiring_run",
                    "code_evidence": "portal_bot/bot.py:121",
                    "coverage_note": "",
                    "updated_at": "2026-06-27",
                },
                {
                    "entry_id": "OPS-001",
                    "entry_type": "script_cli",
                    "subsystem": "Scripts and Ops",
                    "surface": "ops",
                    "trigger_or_path": "python scripts/example.py",
                    "handler_or_component": "main()/CLI",
                    "code_evidence": "scripts/example.py; main() present",
                    "coverage_note": "",
                    "updated_at": "2026-06-27",
                },
                {
                    "entry_id": "WEB-001",
                    "entry_type": "next_page_route",
                    "subsystem": "WebApp and Admin",
                    "surface": "admin",
                    "trigger_or_path": "/admin",
                    "handler_or_component": "page",
                    "code_evidence": r"webapp\src\app\(admin)\admin\page.tsx",
                    "coverage_note": "",
                    "updated_at": "2026-06-27",
                },
                {
                    "entry_id": "CLIENT-001",
                    "entry_type": "flutter_feature_file",
                    "subsystem": "POKROV client app",
                    "surface": "rules",
                    "trigger_or_path": r"packages\app_shell\lib\src\features\rules\route_labels.dart",
                    "handler_or_component": "route_labels",
                    "code_evidence": r"packages\app_shell\lib\src\features\rules\route_labels.dart",
                    "coverage_note": "",
                    "updated_at": "2026-06-27",
                },
            ]
        )

    backend = repo / "backend.csv"
    with backend.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["canonical_id", "method", "path", "test_ref_count", "test_refs"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow(
            {
                "canonical_id": "BACKEND-API-001",
                "method": "GET",
                "path": "/api/health",
                "test_ref_count": "1",
                "test_refs": "tests/test_backend.py",
            }
        )

    scripts = repo / "scripts.csv"
    with scripts.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["script_id", "path", "test_ref_count", "test_refs"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow(
            {
                "script_id": "OPS-SCRIPT-001",
                "path": "scripts/example.py",
                "test_ref_count": "1",
                "test_refs": "tests/test_script.py",
            }
        )

    audit = module.build_entrypoint_audit(repo, entrypoints, tracker, backend, scripts, "2026-06-27")
    by_id = {row["entry_id"]: row for row in audit}

    assert by_id["API-001"]["coverage_tier"] == "direct_route_test_ref"
    assert by_id["API-001"]["story_or_route_refs"] == "BACKEND-API-001"
    assert by_id["TG-001"]["coverage_tier"] == "direct_story_test_ref"
    assert by_id["TG-001"]["story_or_route_refs"] == "TG-001"
    assert by_id["TG-001"]["test_refs"] == "tests/test_bot.py"
    assert by_id["OPS-001"]["coverage_tier"] == "direct_script_test_ref"
    assert by_id["WEB-001"]["coverage_tier"] == "direct_story_test_ref"
    assert by_id["WEB-001"]["test_refs"] == "webapp/e2e/admin-gate.spec.ts"
    assert by_id["CLIENT-001"]["coverage_tier"] == "direct_story_test_ref"
    assert by_id["CLIENT-001"]["story_or_route_refs"] == "CLIENT-001"

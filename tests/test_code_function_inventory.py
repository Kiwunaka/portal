from __future__ import annotations

import csv
import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLIENT_ROOT = REPO_ROOT.parent / "POKROV-app"
CODE_FUNCTION_INVENTORY = (
    REPO_ROOT / "docs" / "developer" / "pokrov-code-function-inventory.csv"
)
CODE_FUNCTION_INVENTORY_MD = (
    REPO_ROOT / "docs" / "developer" / "pokrov-code-function-inventory.md"
)
SYMBOL_COVERAGE_AUDIT = (
    REPO_ROOT / "docs" / "developer" / "pokrov-symbol-coverage-audit.csv"
)
SYMBOL_COVERAGE_AUDIT_MD = (
    REPO_ROOT / "docs" / "developer" / "pokrov-symbol-coverage-audit.md"
)
PRIVATE_HELPER_COVERAGE = (
    REPO_ROOT / "docs" / "developer" / "pokrov-private-helper-coverage.csv"
)
PRIVATE_HELPER_COVERAGE_MD = (
    REPO_ROOT / "docs" / "developer" / "pokrov-private-helper-coverage.md"
)
OWNER_GATED_SCENARIOS = (
    REPO_ROOT / "docs" / "developer" / "pokrov-owner-gated-scenarios.csv"
)
OWNER_GATED_EXECUTION_GUIDE = (
    REPO_ROOT / "docs" / "developer" / "pokrov-owner-gated-execution-guide.md"
)
ENTRYPOINT_HINT_LABELS = {
    "fastapi_route_handler": "FastAPI route handler",
    "telegram_handler": "Telegram handler",
    "script_cli_main": "Script CLI main",
    "framework_override": "Framework override",
    "fastapi_middleware": "FastAPI middleware",
    "next_page_component": "Next.js page component",
}
LANGUAGE_LABELS = {
    "python": "Python",
    "dart": "Dart",
    "tsx": "TSX",
    "typescript": "TypeScript",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "cpp": "C++",
    "c-header": "C header",
}
SYMBOL_COVERAGE_LABELS = {
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
    module_path = REPO_ROOT / "scripts" / "generate_code_function_inventory.py"
    spec = importlib.util.spec_from_file_location("generate_code_function_inventory", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_private_helper_module():
    module_path = REPO_ROOT / "scripts" / "generate_private_helper_coverage.py"
    spec = importlib.util.spec_from_file_location("generate_private_helper_coverage", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _markdown_count_table_after_heading(body: str, heading: str) -> dict[str, int]:
    lines = body.splitlines()
    start = lines.index(heading)
    table_start = next(
        index for index in range(start + 1, len(lines)) if lines[index].startswith("|")
    )
    table: dict[str, int] = {}
    for line in lines[table_start:]:
        if not line.startswith("|"):
            break
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        if cells[0] in {
            "Metric",
            "Language",
            "Subsystem",
            "Symbol kind",
            "Entrypoint hint",
            "Coverage tier",
            "Label",
        }:
            continue
        if set(cells[0]) <= {"-"} or set(cells[1].rstrip(":")) <= {"-"}:
            continue
        table[cells[0]] = int(cells[1].replace(",", ""))
    return table


def test_code_inventory_markdown_summary_matches_csv() -> None:
    with CODE_FUNCTION_INVENTORY.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    with SYMBOL_COVERAGE_AUDIT.open("r", encoding="utf-8", newline="") as f:
        symbol_rows = list(csv.DictReader(f))

    body = CODE_FUNCTION_INVENTORY_MD.read_text(encoding="utf-8")
    current_counts = _markdown_count_table_after_heading(body, "## Current Counts")
    assert current_counts == {
        "Total symbols": len(rows),
        "Root repo symbols": sum(row["root"] == "root" for row in rows),
        "POKROV-app symbols": sum(row["root"] == "POKROV-app" for row in rows),
        "Symbols with token-level test references": sum(
            int(row.get("test_ref_count") or 0) > 0 for row in rows
        ),
        "Parser errors": sum(
            "parse_error" in (row.get("parser_note") or "") for row in rows
        ),
    }

    assert _markdown_count_table_after_heading(body, "### By Language") == {
        LANGUAGE_LABELS[language]: count
        for language, count in Counter(row["language"] for row in rows).items()
    }
    assert _markdown_count_table_after_heading(body, "### By Subsystem") == dict(
        Counter(row["subsystem"] for row in rows)
    )
    assert _markdown_count_table_after_heading(body, "### By Symbol Kind") == {
        kind.capitalize(): count for kind, count in Counter(row["symbol_kind"] for row in rows).items()
    }
    expected_entrypoint_hints = {
        ENTRYPOINT_HINT_LABELS[hint]: count
        for hint, count in Counter(row["entrypoint_hint"] for row in rows).items()
        if hint
    }
    assert _markdown_count_table_after_heading(body, "### By Entrypoint Hint") == expected_entrypoint_hints
    assert f"for all {len(symbol_rows)} symbols" in body


def test_symbol_coverage_markdown_summary_matches_csv() -> None:
    with SYMBOL_COVERAGE_AUDIT.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    tier_counts = Counter(row["coverage_tier"] for row in rows)
    manual_gate_ref_counts: Counter[str] = Counter()
    for row in rows:
        for ref in row.get("manual_gate_refs", "").split(";"):
            if ref.strip():
                manual_gate_ref_counts[ref.strip()] += 1
    expected = {
        label: tier_counts.get(tier, 0)
        for tier, label in SYMBOL_COVERAGE_LABELS.items()
    }
    body = SYMBOL_COVERAGE_AUDIT_MD.read_text(encoding="utf-8")
    actual = _markdown_count_table_after_heading(body, "## Current Counts")
    interpretation = body.split("## Interpretation", 1)[1].split(
        "## Current Open Review Buckets", 1
    )[0]
    documented_owner_refs = set(re.findall(r"OWNER-GATE-[A-Z0-9-]+", interpretation))
    actual_owner_refs = {
        ref for ref in manual_gate_ref_counts if ref.startswith("OWNER-GATE-")
    }

    assert actual == expected
    assert _markdown_count_table_after_heading(
        body, "### Manual Gate Reference Counts"
    ) == dict(manual_gate_ref_counts)
    assert documented_owner_refs == actual_owner_refs


def test_symbol_coverage_rows_have_expected_behavior_from_code() -> None:
    with SYMBOL_COVERAGE_AUDIT.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    with OWNER_GATED_SCENARIOS.open("r", encoding="utf-8", newline="") as f:
        owner_gate_ids = {row["gate_id"] for row in csv.DictReader(f)}

    missing: list[str] = []
    dishonest_manual_claims: list[str] = []
    review_bucket_claims: list[str] = []
    missing_manual_gate_refs: list[str] = []
    unexpected_manual_gate_refs: list[str] = []
    invalid_manual_gate_refs: list[str] = []
    allowed_manual_gate_refs = owner_gate_ids | {"NOT_CURRENT_PUBLIC_BETA_TARGET"}
    manual_tiers = {
        "client_platform_host_manual_gate",
        "client_desktop_tray_manual_gate",
    }
    for row in rows:
        behavior = row.get("expected_behavior_from_code", "").strip()
        if not behavior:
            missing.append(f"{row['symbol_id']}: {row.get('path')}::{row.get('qualified_name')}")
            continue
        tier = row.get("coverage_tier", "")
        manual_gate_refs = [
            ref.strip()
            for ref in row.get("manual_gate_refs", "").split(";")
            if ref.strip()
        ]
        lower_behavior = behavior.lower()
        if tier.endswith("_manual_gate") and "require" not in lower_behavior:
            dishonest_manual_claims.append(f"{row['symbol_id']}: {behavior}")
        if tier in manual_tiers and not manual_gate_refs:
            missing_manual_gate_refs.append(
                f"{row['symbol_id']}: {row.get('path')}::{row.get('qualified_name')}"
            )
        if tier not in manual_tiers and manual_gate_refs:
            unexpected_manual_gate_refs.append(
                f"{row['symbol_id']}: tier={tier} refs={manual_gate_refs}"
            )
        for ref in manual_gate_refs:
            if ref not in allowed_manual_gate_refs:
                invalid_manual_gate_refs.append(
                    f"{row['symbol_id']}: tier={tier} ref={ref}"
                )
        if (
            tier in {"public_symbol_review", "client_package_public_api_review"}
            and "covered" in lower_behavior
            and "not be treated as covered" not in lower_behavior
        ):
            review_bucket_claims.append(f"{row['symbol_id']}: {behavior}")

    assert not missing
    assert not dishonest_manual_claims
    assert not review_bucket_claims
    assert not missing_manual_gate_refs
    assert not unexpected_manual_gate_refs
    assert not invalid_manual_gate_refs
    symbol_summary = SYMBOL_COVERAGE_AUDIT_MD.read_text(encoding="utf-8")
    execution_guide = OWNER_GATED_EXECUTION_GUIDE.read_text(encoding="utf-8")
    for required_doc_fragment in (
        "manual_gate_refs",
        "pokrov-owner-gated-scenarios.csv",
        "NOT_CURRENT_PUBLIC_BETA_TARGET",
    ):
        assert required_doc_fragment in symbol_summary
        assert required_doc_fragment in execution_guide


def test_generated_code_inventory_artifacts_match_canonical_files(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = _load_module()
    inventory_out = tmp_path / "code-function-inventory.csv"
    symbol_coverage_out = tmp_path / "symbol-coverage-audit.csv"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_code_function_inventory.py",
            "--out",
            str(inventory_out),
            "--symbol-coverage-out",
            str(symbol_coverage_out),
        ],
    )

    assert module.main() == 0
    assert inventory_out.read_text(encoding="utf-8") == CODE_FUNCTION_INVENTORY.read_text(
        encoding="utf-8"
    )
    assert symbol_coverage_out.read_text(
        encoding="utf-8"
    ) == SYMBOL_COVERAGE_AUDIT.read_text(encoding="utf-8")


def test_generated_private_inventory_tier_contains_only_private_non_entrypoints() -> None:
    with SYMBOL_COVERAGE_AUDIT.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    leaked_public_or_entrypoint: list[str] = []
    for row in rows:
        if row.get("coverage_tier") != "private_inventory_only":
            continue
        if row.get("visibility") != "private" or row.get("entrypoint_hint"):
            leaked_public_or_entrypoint.append(
                "{path}::{name} visibility={visibility} entrypoint_hint={entrypoint_hint}".format(
                    path=row.get("path", ""),
                    name=row.get("qualified_name") or row.get("name", ""),
                    visibility=row.get("visibility", ""),
                    entrypoint_hint=row.get("entrypoint_hint", ""),
                )
            )

    assert not leaked_public_or_entrypoint


def test_private_helper_coverage_matrix_matches_private_inventory_only() -> None:
    with SYMBOL_COVERAGE_AUDIT.open("r", encoding="utf-8", newline="") as f:
        symbol_rows = list(csv.DictReader(f))
    with CODE_FUNCTION_INVENTORY.open("r", encoding="utf-8", newline="") as f:
        inventory_rows = {row["symbol_id"]: row for row in csv.DictReader(f)}
    with PRIVATE_HELPER_COVERAGE.open("r", encoding="utf-8", newline="") as f:
        private_rows = list(csv.DictReader(f))

    private_symbol_rows = [
        row for row in symbol_rows if row.get("coverage_tier") == "private_inventory_only"
    ]
    expected_ids = {row["symbol_id"] for row in private_symbol_rows}
    actual_ids = {row["symbol_id"] for row in private_rows}

    assert actual_ids == expected_ids
    assert len(private_rows) == len(expected_ids)

    allowed_areas = {
        "client_desktop_host_helper",
        "client_feature_copy_or_logic_helper",
        "client_private_ui_helper",
        "email_relay_internal_helper",
        "payment_probe_internal_helper",
        "private_implementation_helper",
        "qa_tooling_helper",
        "telegram_webapp_bootstrap_helper",
        "webapp_operator_script_helper",
        "webapp_private_ui_helper",
    }
    allowed_risk_tiers = {"high", "medium", "low"}
    required_fields = {
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
    }
    invalid_rows: list[str] = []
    missing_sources: list[str] = []
    for row in private_rows:
        symbol_id = row["symbol_id"]
        for field in required_fields:
            if not row.get(field, "").strip():
                invalid_rows.append(f"{symbol_id}: missing {field}")
        if row.get("private_helper_area") not in allowed_areas:
            invalid_rows.append(f"{symbol_id}: area={row.get('private_helper_area')}")
        if row.get("risk_tier") not in allowed_risk_tiers:
            invalid_rows.append(f"{symbol_id}: risk={row.get('risk_tier')}")
        if row.get("current_status") != "source_inventory_only":
            invalid_rows.append(f"{symbol_id}: current_status={row.get('current_status')}")
        if row.get("proof_status") != "no_dedicated_private_helper_test":
            invalid_rows.append(f"{symbol_id}: proof_status={row.get('proof_status')}")
        if row.get("coverage_policy_status") != "needs_owner_decision_q001":
            invalid_rows.append(f"{symbol_id}: policy={row.get('coverage_policy_status')}")

        inventory = inventory_rows[symbol_id]
        for field in ("root", "path", "line", "language", "subsystem", "symbol_kind", "qualified_name"):
            if row.get(field) != inventory.get(field):
                invalid_rows.append(f"{symbol_id}: {field} mismatch")
        base = CLIENT_ROOT if row.get("root") == "POKROV-app" else REPO_ROOT
        if not (base / row.get("path", "")).exists():
            missing_sources.append(f"{symbol_id}: {row.get('path')}")

    assert not invalid_rows
    assert not missing_sources


def test_private_helper_coverage_markdown_summary_matches_csv() -> None:
    with PRIVATE_HELPER_COVERAGE.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    body = PRIVATE_HELPER_COVERAGE_MD.read_text(encoding="utf-8")
    current_counts = _markdown_count_table_after_heading(body, "## Current Counts")
    risk_counts = Counter(row["risk_tier"] for row in rows)
    assert current_counts == {
        "Private helper rows": len(rows),
        "Rows needing Q-001 owner decision": sum(
            row["coverage_policy_status"] == "needs_owner_decision_q001"
            for row in rows
        ),
        "High risk rows": risk_counts.get("high", 0),
        "Medium risk rows": risk_counts.get("medium", 0),
        "Low risk rows": risk_counts.get("low", 0),
    }
    assert _markdown_count_table_after_heading(body, "### By Private Helper Area") == dict(
        sorted(Counter(row["private_helper_area"] for row in rows).items())
    )
    assert _markdown_count_table_after_heading(body, "### By Risk Tier") == dict(
        sorted(Counter(row["risk_tier"] for row in rows).items())
    )
    assert _markdown_count_table_after_heading(body, "### By Language") == dict(
        sorted(Counter(row["language"] for row in rows).items())
    )
    assert _markdown_count_table_after_heading(body, "### By Current Status") == dict(
        sorted(Counter(row["current_status"] for row in rows).items())
    )


def test_generated_private_helper_coverage_artifacts_match_canonical_files(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = _load_private_helper_module()
    matrix_out = tmp_path / "private-helper-coverage.csv"
    markdown_out = tmp_path / "private-helper-coverage.md"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_private_helper_coverage.py",
            "--out",
            str(matrix_out),
            "--markdown-out",
            str(markdown_out),
        ],
    )

    assert module.main() == 0
    assert matrix_out.read_text(encoding="utf-8") == PRIVATE_HELPER_COVERAGE.read_text(
        encoding="utf-8"
    )
    assert markdown_out.read_text(encoding="utf-8") == PRIVATE_HELPER_COVERAGE_MD.read_text(
        encoding="utf-8"
    )


def test_generate_code_function_inventory_parses_core_languages_and_writes_single_line_csv(
    tmp_path: Path,
) -> None:
    module = _load_module()
    root = tmp_path / "repo"
    client = tmp_path / "POKROV-app"
    (root / "portal_bot").mkdir(parents=True)
    (root / "scripts").mkdir(parents=True)
    (root / "webapp" / "e2e").mkdir(parents=True)
    (root / "webapp" / "scripts").mkdir(parents=True)
    (root / "webapp" / "src" / "app").mkdir(parents=True)
    (root / "webapp" / "src" / "components").mkdir(parents=True)
    (root / "webapp" / "src" / "lib").mkdir(parents=True)
    (root / "marketing" / "src" / "app").mkdir(parents=True)
    (root / "marketing" / "src" / "components").mkdir(parents=True)
    (root / "shared").mkdir(parents=True)
    (root / "tests").mkdir(parents=True)
    (client / "packages" / "app_shell" / "lib").mkdir(parents=True)
    (client / "packages" / "app_shell" / "test").mkdir(parents=True)
    (client / "packages" / "platform_contracts" / "lib").mkdir(parents=True)
    (
        client
        / "apps"
        / "android_shell"
        / "android"
        / "app"
        / "src"
        / "main"
        / "kotlin"
        / "space"
        / "pokrov"
    ).mkdir(parents=True)
    (client / "apps" / "ios_shell" / "ios" / "Runner").mkdir(parents=True)
    (client / "apps" / "windows_shell" / "lib").mkdir(parents=True)
    (client / "apps" / "windows_shell" / "windows" / "runner").mkdir(parents=True)

    (root / "portal_bot" / "sample.py").write_text(
        "\ufeffclass Service:\n"
        "    def handle(self):\n"
        "        return active_story()\n\n"
        "import dependency\n\n"
        "def active_story():\n"
        "    return 'ok'\n",
        encoding="utf-8",
    )
    (root / "portal_bot" / "dependency.py").write_text(
        "def dependency_helper():\n"
        "    return 'dependency'\n",
        encoding="utf-8",
    )
    (root / "portal_bot" / "internal.py").write_text(
        "def _private_helper():\n"
        "    return 'internal'\n\n"
        "def exported_helper():\n"
        "    return 'review me'\n",
        encoding="utf-8",
    )
    (root / "portal_bot" / "untested.py").write_text(
        "def untested_public_helper():\n"
        "    return 'review me'\n",
        encoding="utf-8",
    )
    (root / "portal_bot" / "api.py").write_text(
        "app = object()\n\n"
        "@app.get('/api/health')\n"
        "def health():\n"
        "    return {'ok': True}\n\n"
        "@app.api_route('/pay/success', methods=['GET', 'POST'])\n"
        "def pay_success():\n"
        "    return {'ok': True}\n",
        encoding="utf-8",
    )
    (root / "portal_bot" / "bot.py").write_text(
        "router = object()\n\n"
        "@router.callback_query()\n"
        "async def callback_handler(callback):\n"
        "    return None\n\n"
        "@router.pre_checkout_query()\n"
        "async def pre_checkout_handler(query):\n"
        "    return None\n",
        encoding="utf-8",
    )
    (root / "portal_bot" / "legacy_redirect_bot.py").write_text(
        "router = object()\n\n"
        "@router.message()\n"
        "async def redirect_start(message):\n"
        "    return None\n",
        encoding="utf-8",
    )
    (root / "portal_bot" / "email_relay_app.py").write_text(
        "app = object()\n\n"
        "@app.post('/email/deliver')\n"
        "def deliver_email():\n"
        "    return {'ok': True}\n",
        encoding="utf-8",
    )
    (root / "webapp" / "src" / "app" / "page.tsx").write_text(
        "import { PageTitle } from '@/components/page-title'\n"
        "import { sharedSurfaceLabel } from '@/lib/portal'\n"
        "function localTsHelper() { return 'local' }\n"
        "export default function Page() { return <main><PageTitle />{sharedSurfaceLabel()}</main> }\n"
        "export const formatTitle = () => 'POKROV'\n",
        encoding="utf-8",
    )
    (root / "webapp" / "src" / "app" / "layout.tsx").write_text(
        "export default function FixtureRootBoundary({ children }) { return <html><body>{children}</body></html> }\n",
        encoding="utf-8",
    )
    (root / "webapp" / "src" / "app" / "telegram-webapp-init.tsx").write_text(
        "export default function FixtureTelegramBootstrap() { return null }\n",
        encoding="utf-8",
    )
    (root / "webapp" / "src" / "app" / "qa-overlay.tsx").write_text(
        "export default function FixtureQaToolPanel() { return <button>QA</button> }\n",
        encoding="utf-8",
    )
    (root / "webapp" / "src" / "lib" / "portal.ts").write_text(
        "export {\n"
        "  sharedSurfaceLabel,\n"
        "} from '../../../shared/shared-catalog'\n",
        encoding="utf-8",
    )
    (root / "webapp" / "src" / "components" / "page-title.tsx").write_text(
        "export function PageTitle() { return <h1>POKROV</h1> }\n",
        encoding="utf-8",
    )
    (root / "shared" / "shared-catalog.ts").write_text(
        "export function sharedSurfaceLabel() { return 'shared' }\n",
        encoding="utf-8",
    )
    (root / "marketing" / "src" / "app" / "page.tsx").write_text(
        "import { MarketingBadge } from '@/components/marketing-badge'\n"
        "export default function MarketingPage() { return <MarketingBadge /> }\n",
        encoding="utf-8",
    )
    (root / "marketing" / "src" / "components" / "marketing-badge.tsx").write_text(
        "export function MarketingBadge() { return <span>POKROV</span> }\n",
        encoding="utf-8",
    )
    (root / "webapp" / "e2e" / "cabinet-flow.spec.ts").write_text(
        "function e2eOnlyHelper() { return 'localTsHelper' }\n",
        encoding="utf-8",
    )
    (root / "webapp" / "scripts" / "serve_export.py").write_text(
        "class FixtureStaticExportHandler:\n"
        "    def send_head(self):\n"
        "        return None\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_sample.py").write_text(
        "from portal_bot.sample import active_story\n\n"
        "def test_active_story():\n"
        "    assert active_story() == 'ok'\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_internal_module.py").write_text(
        "import portal_bot.internal\n\n"
        "def test_internal_module_imports():\n"
        "    assert portal_bot.internal\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_code_function_inventory.py").write_text(
        "from portal_bot.untested import untested_public_helper\n",
        encoding="utf-8",
    )
    (root / "scripts" / "audit_story_test_evidence.py").write_text(
        "def audit_story_test_evidence():\n"
        "    return 'tracked source script'\n",
        encoding="utf-8",
    )
    (client / "packages" / "app_shell" / "lib" / "widget.dart").write_text(
        "class AppShell {\n"
        "  String label() => 'POKROV';\n"
        "}\n\n"
        "class _InternalDart\n"
        "    extends Object {\n"
        "  String label() => 'internal';\n"
        "}\n",
        encoding="utf-8",
    )
    (client / "packages" / "app_shell" / "test" / "widget_test.dart").write_text(
        "void main() { AppShell().label(); }\n",
        encoding="utf-8",
    )
    (client / "packages" / "platform_contracts" / "lib" / "platform_contracts.dart").write_text(
        "class FixturePlatformPublicApi {\n"
        "  const FixturePlatformPublicApi();\n"
        "}\n",
        encoding="utf-8",
    )
    (
        client
        / "apps"
        / "android_shell"
        / "android"
        / "app"
        / "src"
        / "main"
        / "kotlin"
        / "space"
        / "pokrov"
        / "RuntimeHostBridge.kt"
    ).write_text(
        "class RuntimeHostBridge {\n"
        "  fun startRuntime() {}\n"
        "}\n",
        encoding="utf-8",
    )
    (
        client
        / "apps"
        / "android_shell"
        / "android"
        / "app"
        / "src"
        / "main"
        / "kotlin"
        / "space"
        / "pokrov"
        / "GeneratedPluginRegistrant.kt"
    ).write_text(
        "class GeneratedPluginRegistrant { fun ignoredGenerated() {} }\n",
        encoding="utf-8",
    )
    (client / "apps" / "ios_shell" / "ios" / "Runner" / "RuntimeHostBridge.swift").write_text(
        "final class IosRuntimeHostBridge {\n"
        "  func startRuntime() {}\n"
        "}\n",
        encoding="utf-8",
    )
    (client / "apps" / "windows_shell" / "lib" / "main.dart").write_text(
        "Future<void> fixtureShowWindow({\n"
        "  required Future<bool> Function() isMinimized,\n"
        "  required Future<void> Function() show,\n"
        "}) async {\n"
        "  if (await isMinimized()) return;\n"
        "  await show();\n"
        "}\n\n"
        "void fixtureTrayMouseDown() {}\n",
        encoding="utf-8",
    )
    (client / "apps" / "windows_shell" / "windows" / "runner" / "main.cpp").write_text(
        "int wWinMain() {\n"
        "  return 0;\n"
        "}\n",
        encoding="utf-8",
    )

    symbols = module.collect_symbols(root, "root", module.ROOT_INCLUDED_DIRS)
    symbols.extend(module.collect_symbols(client, "POKROV-app", module.CLIENT_INCLUDED_DIRS))
    out = tmp_path / "inventory.csv"
    module.write_csv(symbols, out, root, client)

    rows = list(csv.DictReader(out.open("r", encoding="utf-8", newline="")))
    ids = [row["symbol_id"] for row in rows]
    names = {row["qualified_name"] for row in rows}

    assert len(rows) == len(ids) == len(set(ids))
    assert "Service" in names
    assert "Service.handle" in names
    assert "active_story" in names
    assert "dependency_helper" in names
    assert "_private_helper" in names
    assert "exported_helper" in names
    assert "untested_public_helper" in names
    assert "health" in names
    assert "pay_success" in names
    assert "callback_handler" in names
    assert "pre_checkout_handler" in names
    assert "redirect_start" in names
    assert "deliver_email" in names
    assert "audit_story_test_evidence" in names
    assert "Page" in names
    assert "formatTitle" in names
    assert "localTsHelper" in names
    assert "PageTitle" in names
    assert "sharedSurfaceLabel" in names
    assert "MarketingPage" in names
    assert "MarketingBadge" in names
    assert "FixtureRootBoundary" in names
    assert "FixtureTelegramBootstrap" in names
    assert "FixtureQaToolPanel" in names
    assert "FixtureStaticExportHandler" in names
    assert "FixtureStaticExportHandler.send_head" in names
    assert "AppShell" in names
    assert "AppShell.label" in names
    assert "_InternalDart" in names
    assert "_InternalDart.label" in names
    assert "RuntimeHostBridge" in names
    assert "RuntimeHostBridge.startRuntime" in names
    assert "IosRuntimeHostBridge" in names
    assert "IosRuntimeHostBridge.startRuntime" in names
    assert "fixtureTrayMouseDown" in names
    assert "fixtureShowWindow" in names
    assert "Function" not in names
    assert "FixturePlatformPublicApi" in names
    assert "wWinMain" in names
    assert "e2eOnlyHelper" not in names
    assert "GeneratedPluginRegistrant" not in names
    assert "ignoredGenerated" not in names
    assert all("\n" not in row["doc_or_signature"] for row in rows)
    assert not [row for row in rows if row["parser_note"].endswith("parse_error")]

    active = next(row for row in rows if row["qualified_name"] == "active_story")
    assert int(active["test_ref_count"]) == 1
    assert active["test_refs"] == "tests/test_sample.py"

    by_name = {row["qualified_name"]: row for row in rows}
    assert by_name["health"]["entrypoint_hint"] == "fastapi_route_handler"
    assert by_name["pay_success"]["entrypoint_hint"] == "fastapi_route_handler"
    assert by_name["localTsHelper"]["visibility"] == "private"
    assert by_name["localTsHelper"]["test_refs"] == "webapp/e2e/cabinet-flow.spec.ts"
    assert by_name["_InternalDart.label"]["visibility"] == "private"
    assert by_name["deliver_email"]["entrypoint_hint"] == "fastapi_route_handler"
    assert by_name["callback_handler"]["entrypoint_hint"] == "telegram_handler"
    assert by_name["pre_checkout_handler"]["entrypoint_hint"] == "telegram_handler"
    assert by_name["redirect_start"]["entrypoint_hint"] == "telegram_handler"
    assert sum(1 for row in rows if row["qualified_name"] == "fixtureShowWindow") == 1
    assert not [
        row
        for row in rows
        if row["path"] == "portal_bot/bot.py" and row["entrypoint_hint"] == "fastapi_route_handler"
    ]

    tracker = tmp_path / "tracker.csv"
    tracker_fields = ["canonical_id", "code_evidence"]
    with tracker.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=tracker_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            [
                {"canonical_id": "STORY-001", "code_evidence": "portal_bot/sample.py"},
                {"canonical_id": "WEB-001", "code_evidence": "webapp/src/app/page.tsx"},
                {"canonical_id": "MKT-001", "code_evidence": "marketing/src/app/page.tsx"},
                {"canonical_id": "CLIENT-001", "code_evidence": "packages/app_shell/lib/widget.dart"},
            ]
        )

    entrypoint_coverage = tmp_path / "entrypoint-coverage.csv"
    entrypoint_fields = ["entry_id", "trigger_or_path", "handler_or_component", "code_evidence"]
    with entrypoint_coverage.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=entrypoint_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            [
                {
                    "entry_id": "API-001",
                    "trigger_or_path": "GET /api/health",
                    "handler_or_component": "health",
                    "code_evidence": "portal_bot/api.py:4",
                },
                {
                    "entry_id": "TG-001",
                    "trigger_or_path": "router.callback_query()",
                    "handler_or_component": "callback_handler",
                    "code_evidence": "portal_bot/bot.py:4",
                },
                {
                    "entry_id": "WEB-001",
                    "trigger_or_path": "/",
                    "handler_or_component": "Page",
                    "code_evidence": "webapp/src/app/page.tsx",
                },
            ]
        )

    coverage_out = tmp_path / "symbol-coverage.csv"
    module.write_symbol_coverage_audit(
        symbols,
        coverage_out,
        root,
        client,
        tracker,
        entrypoint_coverage,
    )
    coverage_rows = list(csv.DictReader(coverage_out.open("r", encoding="utf-8", newline="")))
    coverage_by_name = {row["qualified_name"]: row for row in coverage_rows}

    assert coverage_by_name["health"]["coverage_tier"] == "entrypoint_mapped"
    assert coverage_by_name["health"]["coverage_refs"] == "API-001"
    assert "externally reachable route" in coverage_by_name["health"]["expected_behavior_from_code"]
    assert coverage_by_name["callback_handler"]["coverage_tier"] == "entrypoint_mapped"
    assert coverage_by_name["active_story"]["coverage_tier"] == "story_source_file"
    assert coverage_by_name["active_story"]["coverage_refs"] == "STORY-001"
    assert "canonical user-story behavior" in coverage_by_name["active_story"]["expected_behavior_from_code"]
    assert coverage_by_name["dependency_helper"]["coverage_tier"] == "story_dependency_source_file"
    assert coverage_by_name["dependency_helper"]["coverage_refs"] == "STORY-001"
    assert coverage_by_name["Page"]["coverage_tier"] == "entrypoint_mapped"
    assert coverage_by_name["PageTitle"]["coverage_tier"] == "story_dependency_source_file"
    assert coverage_by_name["PageTitle"]["coverage_refs"] == "WEB-001"
    assert coverage_by_name["sharedSurfaceLabel"]["coverage_tier"] == "story_dependency_source_file"
    assert coverage_by_name["sharedSurfaceLabel"]["coverage_refs"] == "WEB-001"
    assert coverage_by_name["MarketingBadge"]["coverage_tier"] == "story_dependency_source_file"
    assert coverage_by_name["MarketingBadge"]["coverage_refs"] == "MKT-001"
    assert coverage_by_name["AppShell"]["coverage_tier"] == "story_source_file"
    assert coverage_by_name["FixtureRootBoundary"]["coverage_tier"] == "next_route_boundary_inventory"
    assert coverage_by_name["FixtureTelegramBootstrap"]["coverage_tier"] == "telegram_webapp_bootstrap_inventory"
    assert coverage_by_name["FixtureQaToolPanel"]["coverage_tier"] == "qa_tooling_inventory"
    assert coverage_by_name["FixtureStaticExportHandler"]["coverage_tier"] == "operator_tooling_inventory"
    assert coverage_by_name["FixtureStaticExportHandler.send_head"]["coverage_tier"] == "operator_tooling_inventory"
    assert coverage_by_name["fixtureTrayMouseDown"]["coverage_tier"] == "client_desktop_tray_manual_gate"
    assert (
        coverage_by_name["fixtureTrayMouseDown"]["manual_gate_refs"]
        == "OWNER-GATE-WINDOWS-INSTALL-CONNECT"
    )
    assert coverage_by_name["FixturePlatformPublicApi"]["coverage_tier"] == "client_package_public_api_review"
    assert "must not be treated as covered runtime API" in coverage_by_name["FixturePlatformPublicApi"]["expected_behavior_from_code"]
    assert coverage_by_name["_private_helper"]["coverage_tier"] == "private_inventory_only"
    assert "private implementation detail" in coverage_by_name["_private_helper"]["expected_behavior_from_code"]
    assert coverage_by_name["exported_helper"]["coverage_tier"] == "module_test_ref"
    assert coverage_by_name["exported_helper"]["coverage_refs"] == "tests/test_internal_module.py"
    assert coverage_by_name["untested_public_helper"]["coverage_tier"] == "public_symbol_review"
    assert coverage_by_name["RuntimeHostBridge"]["coverage_tier"] == "client_platform_host_manual_gate"
    assert (
        coverage_by_name["RuntimeHostBridge"]["manual_gate_refs"]
        == "OWNER-GATE-ANDROID-PHYSICAL-INSTALL-CONNECT"
    )
    assert coverage_by_name["RuntimeHostBridge.startRuntime"]["coverage_tier"] == "client_platform_host_manual_gate"
    assert (
        coverage_by_name["RuntimeHostBridge.startRuntime"]["manual_gate_refs"]
        == "OWNER-GATE-ANDROID-PHYSICAL-INSTALL-CONNECT"
    )


def test_symbol_coverage_uses_script_manifest_status_for_cli_mains(tmp_path: Path) -> None:
    module = _load_module()
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    (root / "tests").mkdir(parents=True)
    (root / "scripts" / "active.py").write_text(
        "def main() -> int:\n    return 0\n",
        encoding="utf-8",
    )
    (root / "scripts" / "deprecated.py").write_text(
        "def main() -> int:\n    return 0\n",
        encoding="utf-8",
    )
    (root / "scripts" / "unlisted.py").write_text(
        "def main() -> int:\n    return 0\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_active.py").write_text("from scripts.active import main\n", encoding="utf-8")

    tracker = tmp_path / "tracker.csv"
    with tracker.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["canonical_id", "code_evidence"], lineterminator="\n")
        writer.writeheader()

    entrypoint_coverage = tmp_path / "entrypoint-coverage.csv"
    with entrypoint_coverage.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["entry_id", "trigger_or_path", "handler_or_component", "code_evidence"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow(
            {
                "entry_id": "OPS-001",
                "trigger_or_path": "python scripts/active.py",
                "handler_or_component": "main()/CLI",
                "code_evidence": "scripts/active.py",
            }
        )

    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"active":["scripts/active.py"],"deprecated":["scripts/deprecated.py"],"archive_only":[],"denylist":[]}',
        encoding="utf-8",
    )

    symbols = module.collect_symbols(root, "root", module.ROOT_INCLUDED_DIRS)
    coverage_out = tmp_path / "symbol-coverage.csv"
    module.write_symbol_coverage_audit(
        symbols,
        coverage_out,
        root,
        None,
        tracker,
        entrypoint_coverage,
        manifest,
    )

    coverage_rows = list(csv.DictReader(coverage_out.open("r", encoding="utf-8", newline="")))
    coverage_by_path = {row["path"]: row for row in coverage_rows}

    assert coverage_by_path["scripts/active.py"]["coverage_tier"] == "entrypoint_mapped"
    assert coverage_by_path["scripts/deprecated.py"]["coverage_tier"] == "script_cli_deprecated"
    assert coverage_by_path["scripts/unlisted.py"]["coverage_tier"] == "script_cli_manifest_review"

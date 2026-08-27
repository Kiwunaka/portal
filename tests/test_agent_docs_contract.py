from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts.agent_context_packet_audit import (
    DOCUMENT_CLASSES,
    ROOT_MAX_BYTES,
    ROOT_MAX_LINES,
    ROUTER_MAX_BYTES,
    ROUTER_MAX_LINES,
    audit_platform_context,
    find_broken_local_markdown_links,
    parse_markdown_table,
    physical_line_count,
    tracked_agents_files,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATION_ROOT = REPO_ROOT / "docs" / "developer" / "orchestration"
WORK_ORDERS_ROOT = REPO_ROOT / "docs" / "developer" / "work-orders"
GLOBAL_READ_PACK_CONTRACT_RE = re.compile(
    r"(?:"
    r"^##\s+REFERENCE DOCS\s*$|"
    r"^#{2,6}\s+(?:global\s+)?must-read"
    r"(?:\s+(?:pack|list|order|docs?|references?))?\s*$|"
    r"^\s*(?:[-*]\s*)?(?:global\s+)?must-read"
    r"(?:\s+(?:pack|list|order|docs?|references?))?\s*:\s*$"
    r")",
    flags=re.IGNORECASE | re.MULTILINE,
)


def _without_markdown_decoration(value: str) -> str:
    return (
        value.strip()
        .lstrip("-*+> ")
        .replace("**", "")
        .replace("`", "")
        .strip()
    )


def _normalized_contract_cell(value: str) -> str:
    return " ".join(value.replace("`", "").split())


def _opening_markdown_fence(line: str) -> tuple[str, int] | None:
    match = re.fullmatch(r" {0,3}(`{3,}|~{3,})(.*)", line)
    if match is None:
        return None
    marker_run, info = match.groups()
    marker = marker_run[0]
    if marker == "`" and "`" in info:
        return None
    return marker, len(marker_run)


def _is_markdown_fence_close(line: str, fence: tuple[str, int]) -> bool:
    marker, minimum_length = fence
    return re.fullmatch(
        rf" {{0,3}}{re.escape(marker)}{{{minimum_length},}}[ \t]*",
        line,
    ) is not None


def _unique_markdown_table_rows(
    text: str,
    header: tuple[str, ...],
    *,
    key_column: str,
) -> list[dict[str, str]]:
    assert key_column in header
    lines = text.splitlines()
    matching_tables: list[list[dict[str, str]]] = []
    fence: tuple[str, int] | None = None
    for index, raw_line in enumerate(lines):
        if fence is not None:
            if _is_markdown_fence_close(raw_line, fence):
                fence = None
            continue
        opening_fence = _opening_markdown_fence(raw_line)
        if opening_fence is not None:
            fence = opening_fence
            continue

        line = raw_line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
        if cells != header:
            continue

        assert index + 1 < len(lines), f"missing separator for table {header!r}"
        separator = lines[index + 1].strip()
        assert separator.startswith("|") and separator.endswith("|")
        separator_cells = tuple(
            cell.strip() for cell in separator.strip("|").split("|")
        )
        assert len(separator_cells) == len(header)
        assert all(
            re.fullmatch(r":?-{3,}:?", cell) for cell in separator_cells
        )

        rows: list[dict[str, str]] = []
        for raw_row in lines[index + 2 :]:
            row_line = raw_row.strip()
            if not row_line.startswith("|") or not row_line.endswith("|"):
                break
            values = tuple(
                cell.strip() for cell in row_line.strip("|").split("|")
            )
            assert len(values) == len(header), (header, values)
            rows.append(dict(zip(header, values, strict=True)))
        matching_tables.append(rows)

    assert len(matching_tables) == 1, (
        f"expected one table with header {header!r}, found {len(matching_tables)}"
    )
    rows = matching_tables[0]
    keys = [_normalized_contract_cell(row[key_column]) for row in rows]
    assert len(keys) == len(set(keys)), f"duplicate {key_column} values: {keys!r}"
    return rows


def test_unique_markdown_table_rows_handles_fences_and_rejects_ambiguity() -> None:
    assert _opening_markdown_fence("   ````python") == ("`", 4)
    assert _opening_markdown_fence("    ```python") is None
    assert not _is_markdown_fence_close("```", ("`", 4))
    assert not _is_markdown_fence_close("~~~~", ("`", 4))
    assert _is_markdown_fence_close("  ````` \t", ("`", 4))

    header = "| Contract | Value |\n| --- | --- |"
    ignored_duplicate = (
        f"{header}\n"
        "| Schema | `1` |\n"
        "| `Schema` | `2` |"
    )
    real_table = (
        f"{header}\n"
        "| Schema | `2` |\n"
        "| Applicability | `conditional` |"
    )
    outer_four_with_inner_three = (
        "````markdown\n"
        f"{ignored_duplicate}\n"
        "```\n"
        f"{ignored_duplicate}\n"
        "````"
    )
    backticks_with_literal_tildes = (
        "```text\n"
        "~~~\n"
        f"{ignored_duplicate}\n"
        "~~~\n"
        "```"
    )
    standard_fenced_duplicate = f"~~~markdown\n{ignored_duplicate}\n~~~"
    rows = _unique_markdown_table_rows(
        "\n\n".join(
            (
                outer_four_with_inner_three,
                backticks_with_literal_tildes,
                standard_fenced_duplicate,
                real_table,
            )
        ),
        ("Contract", "Value"),
        key_column="Contract",
    )
    assert [row["Contract"] for row in rows] == ["Schema", "Applicability"]

    with pytest.raises(AssertionError, match="expected one table"):
        _unique_markdown_table_rows(
            f"{real_table}\n\n{real_table}",
            ("Contract", "Value"),
            key_column="Contract",
        )
    with pytest.raises(AssertionError, match="duplicate Contract values"):
        _unique_markdown_table_rows(
            ignored_duplicate,
            ("Contract", "Value"),
            key_column="Contract",
        )

    assert _opening_markdown_fence("```invalid`info") is None


def _declared_pipe_enum(text: str, label: str) -> set[str]:
    lines = text.splitlines()
    for index, raw_line in enumerate(lines):
        line = _without_markdown_decoration(raw_line)
        if not line.casefold().startswith(label.casefold()):
            continue
        remainder = line[len(label) :].lstrip()
        if not remainder.startswith(":"):
            continue

        chunks = [remainder[1:].strip()] if remainder[1:].strip() else []
        cursor = index + 1
        while not chunks or chunks[-1].rstrip().endswith("|"):
            if cursor >= len(lines):
                break
            raw_candidate = lines[cursor].strip()
            cursor += 1
            if raw_candidate.startswith("```"):
                if chunks:
                    break
                continue
            candidate = _without_markdown_decoration(raw_candidate)
            if not candidate:
                if chunks:
                    break
                continue
            if candidate.startswith("#"):
                break
            chunks.append(candidate)
            if not candidate.rstrip().endswith("|"):
                break

        values = {
            part.strip().strip("` .")
            for part in " ".join(chunks).split("|")
            if part.strip().strip("` .")
        }
        assert values, f"empty enum declaration for {label!r}"
        assert all(
            re.fullmatch(r"(?:[a-z][a-z0-9_]*|n/a)", value)
            for value in values
        ), (
            label,
            values,
        )
        return values
    raise AssertionError(f"missing enum declaration for {label!r}")


def _has_exact_identifier_block(text: str, expected: set[str]) -> bool:
    for body in re.findall(r"```[^\r\n]*\r?\n(.*?)```", text, flags=re.DOTALL):
        lines = [
            line.strip().strip("`")
            for line in body.splitlines()
            if line.strip()
        ]
        if len(lines) == len(expected) and set(lines) == expected:
            return True
    return False


def _json_objects(text: str) -> list[dict[str, object]]:
    objects: list[dict[str, object]] = []
    for body in re.findall(
        r"```json\s*\r?\n(.*?)```",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    ):
        parsed = json.loads(body)
        if isinstance(parsed, dict):
            objects.append(parsed)
    return objects


def _normalized_prose(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.casefold()).split())


def _assert_concepts(text: str, *groups: tuple[str, ...]) -> None:
    normalized = f" {_normalized_prose(text)} "
    for alternatives in groups:
        assert any(
            f" {_normalized_prose(alternative)} " in normalized
            for alternative in alternatives
        ), alternatives


def test_platform_root_contract_budget_and_semantics() -> None:
    text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert len(text.encode("utf-8")) <= ROOT_MAX_BYTES
    assert physical_line_count(text) <= ROOT_MAX_LINES
    assert audit_platform_context(REPO_ROOT) == []


def test_platform_router_has_required_shape() -> None:
    text = (
        REPO_ROOT / "docs" / "developer" / "agent-context-map.md"
    ).read_text(encoding="utf-8")
    assert len(text.encode("utf-8")) <= ROUTER_MAX_BYTES
    assert physical_line_count(text) <= ROUTER_MAX_LINES
    assert "| Task | Read first | Inspect | Verify | Docs impact |" in text
    for task in (
        "Backend/API/bots",
        "Account/auth/email/payments",
        "Web cabinet",
        "Standalone adminapp",
        "Marketing/SEO/copy",
        "Shared facts/design contracts",
        "Infrastructure/observability",
        "Scripts/release operations",
        "Documentation/cleanup",
        "Active client repository",
        "Historical investigation",
    ):
        assert f"| {task} |" in text
    lowered = text.casefold()
    assert "global must-read" not in lowered
    assert "embeddings" not in lowered
    assert "vector db" not in lowered


def test_registry_classifies_every_listed_document() -> None:
    text = (REPO_ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    rows = parse_markdown_table(
        text,
        ("Class", "Owner", "Document", "Review state"),
    )
    assert rows
    assert {row["Class"].strip("`") for row in rows} == set(DOCUMENT_CLASSES)
    assert all(row["Owner"].strip() for row in rows)
    assert all(row["Document"].strip() for row in rows)
    assert all(
        row["Review state"].strip("`")
        in {
            "RECONCILED",
            "REVIEWED_NO_CHANGE",
            "PENDING_WAVE_2",
            "PENDING_WAVE_3",
            "PENDING_CLIENT_REVIEW",
            "PENDING_COLLISION_REVIEW",
            "UNRESOLVED_OWNER_DECISION",
        }
        for row in rows
    )
    expected_reconciled = {
        "docs/developer/agent-playbooks/external-model-consults.md": "RECONCILED",
        "DESIGN.md": "RECONCILED",
        "docs/design/generated-assets-policy.md": "RECONCILED",
        "docs/developer/developer-guide.md": "RECONCILED",
        "docs/developer/repository-map.md": "RECONCILED",
        "docs/developer/work-orders/README.md": "RECONCILED",
        "docs/developer/orchestration/flow-state.md": "RECONCILED",
        "docs/developer/orchestration/orchestration-standard.md": "RECONCILED",
        "docs/developer/orchestration/wo-authoring-guide.md": "RECONCILED",
        "docs/developer/orchestration/context-cost-harnesses.md": "RECONCILED",
    }
    review_state_by_document = {
        row["Document"].strip("`"): row["Review state"].strip("`")
        for row in rows
    }
    assert {
        document: review_state_by_document.get(document)
        for document in expected_reconciled
    } == expected_reconciled
    assert "Start Here As Agent" not in text


def test_docs_finalization_registry_states_are_exact() -> None:
    text = (REPO_ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    rows = parse_markdown_table(
        text,
        ("Class", "Owner", "Document", "Review state"),
    )
    review_state_by_document = {
        row["Document"].strip("`"): row["Review state"].strip("`")
        for row in rows
    }
    ledger_document = next(
        document
        for document in review_state_by_document
        if document.startswith("docs/developer/pokrov-canonical-feature-tracker.md")
    )
    reconciled_documents = {
        "docs/developer/openai-operator-assistants.md",
        "docs/architecture/client-downloads-flow.md",
        "docs/user/compatibility-clients-guide-ru.md",
        "C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md",
        "C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md",
        ledger_document,
        "docs/operations/rollback-runbook.md",
        "docs/operations/android-release-audit.md",
        "docs/operations/runtime-app-download-smoke.md",
        "docs/operations/ru-origin-probe.md",
    }
    assert len(reconciled_documents) == 10
    assert {
        document: review_state_by_document.get(document)
        for document in reconciled_documents
    } == {document: "RECONCILED" for document in reconciled_documents}

    assert {
        document: state
        for document, state in review_state_by_document.items()
        if state.startswith("PENDING_")
    } == {
        "docs/developer/work-orders/2026-07-09-growth-megapass/": "PENDING_WAVE_3",
        "docs/architecture/system-overview.md": "PENDING_WAVE_3",
        "docs/architecture/app-first-and-bonus-flows.md": "PENDING_WAVE_3",
        "docs/architecture/support-feedback-flow.md": "PENDING_WAVE_3",
        "docs/operations/payment-reconciliation.md": "PENDING_WAVE_3",
        "docs/operations/lavatop-payment-operations.md": "PENDING_WAVE_3",
        "docs/superpowers/specs/": "PENDING_COLLISION_REVIEW",
    }
    assert (
        review_state_by_document["docs/archive/superpowers-plans/"]
        == "RECONCILED"
    )
    assert (
        "`PENDING_WAVE_3` remains only for unmerged market-ready slices and "
        "canonical/operations follow-ups."
    ) in text
    assert (
        "`PENDING_COLLISION_REVIEW` on `docs/superpowers/specs/` remains for "
        "concurrent design/research."
    ) in text


def test_docs_finalization_archives_context_renewal_material() -> None:
    active_roadmap = (
        REPO_ROOT
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-07-10-pokrov-codex-docs-renewal-roadmap.md"
    )
    active_design = (
        REPO_ROOT
        / "docs"
        / "superpowers"
        / "specs"
        / "2026-07-10-agent-context-refactor-design.md"
    )
    archive_root = REPO_ROOT / "docs" / "archive" / "superpowers-plans"
    archived_roadmap = archive_root / active_roadmap.name
    archived_design = archive_root / active_design.name

    assert not active_roadmap.exists()
    assert not active_design.exists()
    assert archived_roadmap.is_file()
    assert archived_design.is_file()

    design = archived_design.read_text(encoding="utf-8")
    assert "Status: IMPLEMENTED_HISTORICAL" in design
    assert "## Current Owners" in design
    for owner in (
        "AGENTS.md",
        "docs/README.md",
        "docs/developer/agent-context-map.md",
        "C:/Users/kiwun/Documents/ai/POKROV-app/docs/",
    ):
        assert owner in design
    assert (
        "client-without-AGENTS, expected-canon, worktree, baseline, and "
        "promotion sections are 2026-07-10 historical snapshots"
    ) in design
    assert "not current instructions" in design

    roadmap = archived_roadmap.read_text(encoding="utf-8")
    roadmap_lowered = roadmap.casefold()
    assert "REQUIRED SUB-SKILL" not in roadmap
    assert "implement this plan task-by-task" not in roadmap
    assert (
        "> **Archived execution record — historical/non-executable.**" in roadmap
    )
    assert "## Retained Execution Snapshot — 2026-07-12 (superseded)" in roadmap
    assert "## Closure — 2026-07-14" in roadmap
    for closure_marker in (
        "platform canon landed through `5553d22`",
        "local `master` reached `35975f5`",
        "client renewal landed through `efb6aea`",
        "historical/non-executable",
        "`4722cd8`",
        "`4b6124b`",
    ):
        assert closure_marker.casefold() in roadmap_lowered
    assert (
        "No push, deploy, destructive cleanup, or manual release gates ran "
        "as part of this closure."
    ) in roadmap
    assert (
        "This closure is not a release, deploy, or production-readiness claim."
    ) in roadmap
    active_design_path = (
        "docs/superpowers/specs/2026-07-10-agent-context-refactor-design.md"
    )
    archived_design_path = (
        "docs/archive/superpowers-plans/"
        "2026-07-10-agent-context-refactor-design.md"
    )
    assert active_design_path not in roadmap
    assert roadmap.count(archived_design_path) == 2

    archive_readme = (archive_root / "README.md").read_text(encoding="utf-8")
    assert "Last updated: 2026-07-14" in archive_readme
    assert "completed plans and designs" in archive_readme.casefold()
    active_finalization_plan = (
        REPO_ROOT
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-07-14-docs-finalization.md"
    )
    archived_finalization_plan = archive_root / active_finalization_plan.name
    assert not active_finalization_plan.exists()
    assert archived_finalization_plan.is_file()

    for archived_name in (
        archived_roadmap.name,
        archived_design.name,
        archived_finalization_plan.name,
    ):
        assert f"]({archived_name})" in archive_readme

    finalization_plan = archived_finalization_plan.read_text(encoding="utf-8")
    assert "REQUIRED SUB-SKILL" not in finalization_plan
    assert (
        "> **Archived execution record — historical/non-executable.**"
        in finalization_plan
    )
    assert "Status: COMPLETED_HISTORICAL" in finalization_plan
    assert "- [ ]" not in finalization_plan
    assert "`84 passed in 73.24s`" in finalization_plan
    assert "Independent scoped review returned `CLEAN`." in finalization_plan
    assert (
        "- Move: `docs/superpowers/plans/"
        "2026-07-10-pokrov-codex-docs-renewal-roadmap.md` -> "
        "`docs/archive/superpowers-plans/"
        "2026-07-10-pokrov-codex-docs-renewal-roadmap.md`"
    ) in finalization_plan
    assert (
        "- Move: `docs/superpowers/specs/"
        "2026-07-10-agent-context-refactor-design.md` -> "
        "`docs/archive/superpowers-plans/"
        "2026-07-10-agent-context-refactor-design.md`"
    ) in finalization_plan


def test_docs_finalization_rollback_preserves_release_evidence() -> None:
    text = (
        REPO_ROOT / "docs" / "operations" / "rollback-runbook.md"
    ).read_text(encoding="utf-8")
    lowered = text.casefold()
    assert "Last updated: 2026-08-27" in text
    assert "remove or blank public download urls" not in lowered
    assert "switch the active pointer to the last verified release handoff" in lowered
    assert (
        "disable the public route while preserving versioned metadata and artifacts"
        in lowered
    )
    assert "prepare a short support notice" in lowered
    assert "only through an explicitly authorized owner/operator" in lowered
    assert "config/release-rollback-catalog.seed.json" in text
    assert "scripts/set-release-stable-pointer.ps1" in text
    assert "optimistic lock" in lowered
    assert "external backup" in lowered
    assert "`wo-013af`" in lowered
    assert "manifest\n`a2752b6a...`" in lowered
    assert "`i3` verified-local evidence only" in lowered
    assert "were not mutated" in lowered
    assert "required before `i4/i5`" in lowered
    assert (
        "[Paid Beta Deploy And Rollback Checklist]"
        "(deployment-and-access.md#paid-beta-deploy-and-rollback-checklist)"
    ) in text


def test_context_links_and_tracked_agents_are_valid() -> None:
    assert find_broken_local_markdown_links(
        REPO_ROOT,
        (
            "AGENTS.md",
            "docs/README.md",
            "docs/developer/agent-context-map.md",
        ),
    ) == []
    assert tracked_agents_files(REPO_ROOT) == ["AGENTS.md"]


def test_orchestration_docs_and_templates_fit_budgets() -> None:
    budgets = {
        "README.md": 4096,
        "orchestration-standard.md": 16384,
        "wo-authoring-guide.md": 12288,
        "flow-state.md": 6144,
        "context-cost-harnesses.md": 12288,
    }
    for relative_path, maximum in budgets.items():
        payload = (ORCHESTRATION_ROOT / relative_path).read_bytes()
        assert len(payload) <= maximum, relative_path

    work_orders_index = WORK_ORDERS_ROOT / "README.md"
    assert len(work_orders_index.read_bytes()) <= 4096, work_orders_index.name

    templates = sorted((ORCHESTRATION_ROOT / "templates").glob("*.md"))
    assert templates
    assert "test-quality-report.template.md" not in {path.name for path in templates}
    for template in templates:
        maximum = 12288 if template.name == "WO.template.md" else 8192
        assert len(template.read_bytes()) <= maximum, template.name


def test_orchestration_uses_normalized_lifecycle_and_evidence_contract() -> None:
    standard = (
        ORCHESTRATION_ROOT / "orchestration-standard.md"
    ).read_text(encoding="utf-8")
    quick_start = (ORCHESTRATION_ROOT / "README.md").read_text(encoding="utf-8")
    expected_ceremony_contract = {
        "direct": (
            "small, low-risk, single-pass work",
            "focused validation and handoff",
        ),
        "bounded_wo": (
            "durable context, independent review, multiple bounded steps, or meaningful risk",
            "compact WO; selected roles; conditional FLOW_STATE",
        ),
        "release_wo": (
            "release, deploy, payment, security, persistence, provider, "
            "device, or origin-sensitive work",
            "full triggered proof blocks, release validator, candidate-specific evidence",
        ),
    }
    for owner_name, owner in (
        ("orchestration-standard.md", standard),
        ("README.md", quick_start),
    ):
        ceremony_rows = _unique_markdown_table_rows(
            owner,
            ("Ceremony", "Trigger", "Required artifacts"),
            key_column="Ceremony",
        )
        assert len(ceremony_rows) == 3, owner_name
        ceremony_contract = {
            _normalized_contract_cell(row["Ceremony"]): (
                _normalized_contract_cell(row["Trigger"]),
                _normalized_contract_cell(row["Required artifacts"]),
            )
            for row in ceremony_rows
        }
        assert ceremony_contract == expected_ceremony_contract, owner_name

    assert _declared_pipe_enum(standard, "WO status") == {
        "draft",
        "ready",
        "active",
        "review",
        "fix_cycle",
        "blocked",
        "partial",
        "complete",
    }
    assert _declared_pipe_enum(standard, "Review verdict") == {
        "pass",
        "changes_required",
        "blocked",
    }
    assert _declared_pipe_enum(standard, "Finding status") == {
        "open",
        "fixed",
        "accepted_risk",
        "blocked",
    }

    evidence_fields = {
        "name",
        "source",
        "target_scope",
        "freshness",
        "attribution",
        "result",
        "reference",
        "notes",
    }
    assert _has_exact_identifier_block(standard, evidence_fields)
    assert _declared_pipe_enum(standard, "source") == {
        "static_review",
        "synthetic_test",
        "tracked_fixture",
        "generated_artifact",
        "api_e2e",
        "ui_behavior",
        "runtime_smoke",
        "full_validation_epoch",
        "manual",
        "n/a",
    }
    assert _declared_pipe_enum(standard, "target_scope") == {
        "local",
        "exact_candidate",
        "deployed_environment",
        "provider",
        "physical_device",
        "current_origin",
        "brain_origin",
        "ru_origin",
    }
    assert _declared_pipe_enum(standard, "freshness") == {
        "current_candidate",
        "current_environment",
        "retained_current",
        "historical_stale",
    }
    assert _declared_pipe_enum(standard, "attribution") == {
        "wo_owned",
        "wave_integration",
        "pre_existing",
        "unrelated",
        "blocked_by_access",
    }
    for manual_label in (
        "MANUAL_OWNER_TEST",
        "OPERATOR_ATTESTED",
        "SKIPPED_BY_OWNER",
        "SKIPPED_BY_OPERATOR",
        "NOT_REQUESTED",
        "BLOCKED_BY_ACCESS",
    ):
        assert re.search(rf"\b{manual_label}\b", standard)

    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in ORCHESTRATION_ROOT.rglob("*.md")
    )
    for stale_heading in (
        "### Fast",
        "### Balanced",
        "### Strict",
        "Minimal Launch Sequence",
        "Evidence Source Tiers",
    ):
        assert stale_heading.casefold() not in combined.casefold()
    for stale_value in (
        "`clean_pass`",
        "`executing`",
        "`spec-review`",
        "`quality-review`",
        "`fix-cycle`",
        "`redesign-required`",
        "`accepted-risk`",
    ):
        assert stale_value not in combined


def test_roles_have_exact_roster_and_single_responsibility_boundaries() -> None:
    role_paths = sorted((ORCHESTRATION_ROOT / "roles").glob("*.md"))
    expected_roles = {
        "orchestrator.md",
        "scout-discovery.md",
        "implementation-strategy.md",
        "executor.md",
        "spec-reviewer.md",
        "quality-reviewer.md",
        "release-validator.md",
    }
    assert {path.name for path in role_paths} == expected_roles

    requirements = {
        "orchestrator.md": (
            ("ceremony",),
            ("collision gate",),
            ("route roles", "role routing", "routing"),
            ("status",),
            ("integration",),
            ("closure", "completion"),
        ),
        "scout-discovery.md": (
            ("read only",),
            ("anchor", "anchors"),
            ("conflict", "conflicts"),
            ("scope",),
            ("docs impact",),
            ("validation",),
        ),
        "implementation-strategy.md": (
            ("optional",),
            ("complex", "unclear"),
            ("approach",),
            ("invariant", "invariants"),
            ("oracle",),
            ("risk", "risks"),
            ("slice", "slices"),
        ),
        "executor.md": (
            ("bounded",),
            ("write", "writes"),
            ("docs impact",),
            ("evidence",),
            ("never", "must not", "does not"),
            ("self close", "close itself", "self closure"),
        ),
        "spec-reviewer.md": (
            ("contract",),
            ("compliance", "compliant"),
            ("only",),
        ),
        "quality-reviewer.md": (
            ("correctness",),
            ("maintainability",),
            ("security",),
            ("performance",),
            ("usability",),
            ("evidence quality",),
        ),
        "release-validator.md": (
            ("exact candidate",),
            ("gate", "gates"),
            ("origin", "origins"),
            ("manual",),
            ("rollback",),
            ("public claim", "public claims"),
        ),
    }
    assert GLOBAL_READ_PACK_CONTRACT_RE.search("No global Must-Read pack.") is None
    for role_path in role_paths:
        maximum = 5120 if role_path.name == "orchestrator.md" else 4096
        text = role_path.read_text(encoding="utf-8")
        assert len(text.encode("utf-8")) <= maximum, role_path.name
        assert GLOBAL_READ_PACK_CONTRACT_RE.search(text) is None
        _assert_concepts(text, *requirements[role_path.name])


def test_reviewer_interface_uses_normalized_fields_and_verdicts() -> None:
    template = (
        ORCHESTRATION_ROOT / "templates" / "review-verdict.template.md"
    ).read_text(encoding="utf-8")
    assert _declared_pipe_enum(template, "verdict") == {
        "pass",
        "changes_required",
        "blocked",
    }
    evidence_fields = (
        "name",
        "source",
        "target_scope",
        "freshness",
        "attribution",
        "result",
        "reference",
        "notes",
    )
    evidence_block = template.split("\nevidence:\n", 1)[1].split(
        "\n\nnext_action:", 1
    )[0]
    assert re.findall(
        r"^  ([a-z][a-z0-9_]*):",
        evidence_block,
        flags=re.MULTILINE,
    ) == list(evidence_fields)
    for field in (
        "finding",
        "id",
        "issue_class",
        "severity",
        "reference",
        "required_change",
        "status",
        "evidence",
        *evidence_fields,
        "next_action",
    ):
        assert re.search(rf"(?<![a-z0-9_]){field}(?![a-z0-9_])", template.casefold())


def test_default_wo_uses_only_compact_contract_headings() -> None:
    template = (
        ORCHESTRATION_ROOT / "templates" / "WO.template.md"
    ).read_text(encoding="utf-8")
    assert re.findall(r"^# ([^#].*)$", template, flags=re.MULTILINE) == ["WO"]
    allowed_h2 = {
        "Metadata",
        "Goal",
        "Non-Goals",
        "Write Scope",
        "No-Touch Scope",
        "Authority Anchors",
        "Acceptance Oracle",
        "Docs Impact",
        "Validation And Evidence",
        "Status And Handoff",
    }
    actual_h2 = re.findall(r"^## ([^#].*)$", template, flags=re.MULTILINE)
    assert len(actual_h2) == len(allowed_h2)
    assert set(actual_h2) == allowed_h2
    for forbidden in (
        "### Backend Validation",
        "### Webapp Validation",
        "### Marketing Validation",
        "### Infra Validation",
        "### Client Validation",
        "## FLOW_STATE",
        "Current Code Anchors (Must Read)",
    ):
        assert forbidden not in template


def test_flow_state_uses_conditional_v2_schema_and_stop_contract() -> None:
    flow = (ORCHESTRATION_ROOT / "flow-state.md").read_text(encoding="utf-8")
    flow_contract_rows = _unique_markdown_table_rows(
        flow,
        ("Contract", "Value"),
        key_column="Contract",
    )
    assert len(flow_contract_rows) == 3
    flow_contract = {
        _normalized_contract_cell(row["Contract"]): _normalized_contract_cell(
            row["Value"]
        )
        for row in flow_contract_rows
    }
    assert flow_contract == {
        "Schema": "2",
        "Applicability": "conditional",
        "Same-class stop threshold": "3",
    }

    assert _declared_pipe_enum(flow, "Conditional triggers") == {
        "review",
        "fix_cycle",
        "blocked",
        "partial",
        "durable_handoff",
    }
    allowed_states = {
        "review",
        "fix_cycle",
        "redesign_required",
        "blocked",
        "partial",
        "complete",
    }
    allowed_next_actions = {
        "execute",
        "owned_finding_recheck",
        "fresh_final_review",
        "release_validation",
        "problem_class_analysis",
        "wait_for_access",
        "close",
    }
    assert _declared_pipe_enum(flow, "Allowed states") == allowed_states
    assert _declared_pipe_enum(flow, "Allowed next actions") == allowed_next_actions

    schemas = [
        item
        for item in _json_objects(flow)
        if "version" in item and "wo_id" in item
    ]
    assert len(schemas) == 1
    schema = schemas[0]
    assert set(schema) == {
        "version",
        "wo_id",
        "state",
        "cycle",
        "open_findings",
        "same_class_without_mechanism_change",
        "next_action",
        "stop_reason",
    }
    assert schema["version"] == 2
    assert schema["state"] in allowed_states
    assert schema["next_action"] in allowed_next_actions
    assert isinstance(schema["cycle"], int)
    assert isinstance(schema["open_findings"], list) and schema["open_findings"]
    finding = schema["open_findings"][0]
    assert isinstance(finding, dict)
    assert set(finding) == {
        "id",
        "owner",
        "issue_class",
        "status",
        "mechanism_changed",
        "evidence_ref",
    }
    assert finding["status"] in {"open", "fixed", "accepted_risk", "blocked"}
    assert isinstance(finding["mechanism_changed"], bool)
    counters = schema["same_class_without_mechanism_change"]
    assert isinstance(counters, dict) and counters
    assert all(isinstance(value, int) and value >= 1 for value in counters.values())

    for stale_flow_token in (
        '"version": 1',
        '"ordinary_fix_cycles"',
        '"state": "draft | executing',
        '"next_action": "continue |',
    ):
        assert stale_flow_token not in flow


def test_external_model_playbook_is_optional_and_isolated() -> None:
    playbook = (
        REPO_ROOT
        / "docs"
        / "developer"
        / "agent-playbooks"
        / "external-model-consults.md"
    )
    text = playbook.read_text(encoding="utf-8")
    assert len(text.encode("utf-8")) <= 16384
    for required in (
        "OPERATOR_PLAYBOOK",
        "opt-in",
        "Codex",
        "reverify",
        "opencode.cmd",
        "OpenRouter",
        "SKILL PACKET",
    ):
        assert required.casefold() in text.casefold()

    expected_model_ids = {
        "openrouter/deepseek/deepseek-v4-pro",
        "openrouter/z-ai/glm-5.1",
        "openrouter/openai/gpt-5.5-pro",
        "openrouter/moonshotai/kimi-k2.6",
        "openrouter/moonshotai/kimi-k2.7-code",
        "openrouter/xiaomi/mimo-v2.5-pro",
        "openrouter/minimax/minimax-m2.7",
        "openrouter/nvidia/nemotron-3-ultra-550b-a55b",
    }
    model_rows = _unique_markdown_table_rows(
        text,
        (
            "Model ID",
            "Availability",
            "Context tokens",
            "Input / 1M USD",
            "Output / 1M USD",
            "Role",
            "Cost check",
        ),
        key_column="Model ID",
    )
    assert len(model_rows) == 8
    assert {
        _normalized_contract_cell(row["Model ID"]) for row in model_rows
    } == expected_model_ids
    assert all(row["Availability"] == "`AVAILABLE`" for row in model_rows)
    assert all(row["Context tokens"].strip("`").isdigit() for row in model_rows)
    assert all(row["Input / 1M USD"].startswith("`$") for row in model_rows)
    assert all(row["Output / 1M USD"].startswith("`$") for row in model_rows)
    assert all(
        _normalized_contract_cell(row["Cost check"])
        == "reverify before cost-sensitive use"
        for row in model_rows
    )
    assert "Last verified: 2026-07-11" in text

    harness = (ORCHESTRATION_ROOT / "context-cost-harnesses.md").read_text(
        encoding="utf-8"
    )
    for forbidden in (
        "openrouter/deepseek/deepseek-v4-pro",
        "openrouter/openai/gpt-5.5-pro",
        "opencode.cmd",
        "$30 / $180",
    ):
        assert forbidden not in harness
    assert harness.count("external-model-consults.md") == 1
    for forbidden in (
        "OpenRouter",
        "OpenCode",
        "DeepSeek",
        "GPT-5.5",
        "Kimi",
        "GLM",
        "MiniMax",
        "MiMo",
        "Nemotron",
    ):
        assert forbidden.casefold() not in harness.casefold()

    root_contract = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    router = (
        REPO_ROOT / "docs" / "developer" / "agent-context-map.md"
    ).read_text(encoding="utf-8")
    assert "openrouter/deepseek/deepseek-v4-pro" not in root_contract
    assert "external-model-consults.md" not in router

    support_source = (
        REPO_ROOT / "scripts" / "pokrov_support_ai_kb_refresh.py"
    ).read_text(encoding="utf-8")
    assert "external-model-consults.md" not in support_source
    docs_assistant_source = (
        REPO_ROOT / "scripts" / "pokrov_ai_docs_assistant.py"
    ).read_text(encoding="utf-8")
    assert "external-model-consults.md" not in docs_assistant_source

    old_helper = (
        REPO_ROOT / "docs" / "developer" / "openai-operator-assistants.md"
    ).read_text(encoding="utf-8")
    for required in (
        "Document class: `EXPERIMENTAL`",
        "Not part of the default Codex task route.",
        "Direct canonical reads and rg/Git remain the normal path.",
    ):
        assert required in old_helper


def test_developer_entrypoints_match_current_repository_ownership() -> None:
    developer = (
        REPO_ROOT / "docs" / "developer" / "developer-guide.md"
    ).read_text(encoding="utf-8")
    repository = (
        REPO_ROOT / "docs" / "developer" / "repository-map.md"
    ).read_text(encoding="utf-8")
    combined = developer + "\n" + repository

    for required in (
        "adminapp/",
        "portal_bot/",
        "tests/test_account_foundation.py",
        "POKROV-app",
        "docs/developer/agent-context-map.md",
    ):
        assert required in combined

    for stale in (
        "webapp owns the primary admin surface",
        "mini is probe-only",
        "0.x.x-beta",
        "webapp/src/app/(dashboard)/admin/",
        "OpenCode",
        "Fireworks",
        "CODY",
    ):
        assert stale.casefold() not in combined.casefold()


def test_developer_guide_primary_admin_commands_include_build_and_e2e() -> None:
    developer = (
        REPO_ROOT / "docs" / "developer" / "developer-guide.md"
    ).read_text(encoding="utf-8")
    adminapp_block = re.search(
        r"Push-Location adminapp\s+(.*?)\s+Pop-Location",
        developer,
        flags=re.DOTALL,
    )
    assert adminapp_block is not None
    commands = {
        line.strip()
        for line in adminapp_block.group(1).splitlines()
        if line.strip()
    }
    assert {"npm.cmd run build", "npm.cmd run test:e2e"} <= commands


def test_active_platform_canon_has_no_known_stale_claims() -> None:
    active_paths = (
        "docs/product/portal-vpn-product.md",
        "docs/product/beta-known-limitations.md",
        "docs/architecture/api-contracts.md",
        "docs/architecture/payment-state-machine.md",
        "docs/operations/publishing-and-signing-guide.md",
        "docs/design/design-system-sync.md",
        "docs/launch/known-issues.md",
        "docs/launch/open-source-client-rollout-plan.md",
        "docs/user/portal-vpn-user-guide-ru.md",
    )
    combined = "\n".join(
        (REPO_ROOT / path).read_text(encoding="utf-8")
        for path in active_paths
    )
    for stale in (
        "webapp is also the primary admin operator surface",
        "web admin is the primary operator surface",
        "0.x.x-beta",
        "avoids direct public `VPN` wording",
        "release repository remains private",
        "up to `5` eligible non-free nodes",
        "`15%` stickiness threshold",
        "must not enable public paid checkout",
    ):
        assert stale.casefold() not in combined.casefold()

    product = (
        REPO_ROOT / "docs" / "product" / "portal-vpn-product.md"
    ).read_text(encoding="utf-8")
    assert "up to `8`" in product
    assert "`20%` stickiness" in product
    assert "`adminapp`" in product


def test_beta_limitations_use_public_release_truth() -> None:
    import json

    payload = json.loads(
        (REPO_ROOT / "shared" / "beta-known-limitations.json").read_text(
            encoding="utf-8"
        )
    )
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "release repository remains private" not in serialized
    assert "GitHub Releases" in serialized
    assert set(payload["source_docs"]) == {
        "docs/product/beta-known-limitations.md",
        "docs/launch/known-issues.md",
    }


def test_account_foundation_owners_preserve_dual_identity_truth() -> None:
    owner_paths = (
        "docs/product/portal-vpn-product.md",
        "docs/product/payment-and-access-key-contract.md",
        "docs/architecture/api-contracts.md",
        "docs/architecture/payment-state-machine.md",
    )
    required = (
        "UUID `accounts.id`",
        "`users.account_id` is a nullable projection",
        "public numeric `account_id`",
        "stateless bearer",
        "Production deployment of account foundation is not proven",
        "Rotating sessions",
        "recovery exchange",
        "entitlement-ledger authority",
        "must not be claimed",
    )
    for relative_path in owner_paths:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for phrase in required:
            assert phrase.casefold() in text.casefold(), (
                f"{relative_path} is missing account boundary: {phrase}"
            )


def test_active_operations_use_current_client_release_path() -> None:
    active_paths = (
        "docs/operations/deployment-and-access.md",
        "docs/operations/monitoring-and-visibility.md",
        "docs/operations/publishing-and-signing-guide.md",
        "docs/operations/client-delivery-update-content-plan.md",
        "docs/operations/android-production-signing-handoff.md",
    )
    combined = "\n".join(
        (REPO_ROOT / path).read_text(encoding="utf-8")
        for path in active_paths
    )
    assert "external/client-fork/scripts/release_handoff.ps1" not in combined
    assert "external/client-fork/scripts/check_release_urls.py" not in combined
    assert "pokrov-android-arm64-v8a.apk" in combined
    assert "pokrov-android-universal.apk" in combined
    assert "larger fallback" in combined
    assert "pokrov-android-arm64-v8a.apk" in combined
    assert "pokrov-android-armeabi-v7a.apk" in combined
    assert "POKROV-app/artifacts/releases/pokrov-app/" in combined
    assert "v1.1.6" in combined
    assert "1.2.0+30" in combined
    assert "v1.0.13" not in combined
    assert "stable-direct" in combined.casefold()


def test_active_release_owners_name_public_github_stable_direct() -> None:
    owner_paths = (
        "docs/operations/deployment-and-access.md",
        "docs/operations/publishing-and-signing-guide.md",
        "docs/developer/developer-guide.md",
        "docs/developer/repository-map.md",
    )
    for relative_path in owner_paths:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert "stable-direct" in text.casefold(), relative_path
        assert "v1.1.6" in text, relative_path
        assert "1.1.6+29" in text, relative_path
        assert "1.2.0+30" in text, relative_path
        assert "candidate_created=false" in text, relative_path
        assert "config/release-handoff.seed.json" in text, relative_path
        assert "v1.0.10" not in text, relative_path
        assert "v1.0.13" not in text, relative_path

    historical_beta = (
        REPO_ROOT / "docs/operations/public-beta-release-runbook.md"
    ).read_text(encoding="utf-8")
    assert "Document class: `EVIDENCE`" in historical_beta
    assert "historical outside-store beta" in historical_beta


def test_superseded_release_trackers_are_evidence_only() -> None:
    registry = (REPO_ROOT / "docs/README.md").read_text(encoding="utf-8")
    expected_rows = (
        "| `EVIDENCE` | retained public beta release | "
        "`docs/operations/public-beta-release-runbook.md` | `RECONCILED` |",
        "| `EVIDENCE` | retained 2026-08-13 direct release tracker | "
        "`docs/operations/2026-08-13-direct-release-readiness-tracker.md` | "
        "`RECONCILED` |",
    )
    for row in expected_rows:
        assert row in registry

    beta = (REPO_ROOT / "docs/operations/public-beta-release-runbook.md").read_text(
        encoding="utf-8"
    )
    direct = (
        REPO_ROOT / "docs/operations/2026-08-13-direct-release-readiness-tracker.md"
    ).read_text(encoding="utf-8")
    assert "Document class: `EVIDENCE`" in beta
    assert "Document class: `EVIDENCE`" in direct
    assert "## Current Decision" not in beta
    assert "supersedes this" in direct
    assert "do not authorize a new candidate or promotion" in direct


def test_completed_versioned_work_orders_are_evidence_only() -> None:
    registry = (REPO_ROOT / "docs/README.md").read_text(encoding="utf-8")
    expected = {
        "retained v1.0.4-beta.1 manual-proof queue": (
            "docs/developer/work-orders/2026-08-14--postrelease-manual-proof/"
        ),
        "completed POKROV 1.0.6 stable-direct release": (
            "docs/developer/work-orders/2026-08-14-stable-1.0.6-release/"
        ),
        "completed POKROV 1.1.1 product-analytics/operator wave": (
            "docs/developer/work-orders/2026-08-17--product-analytics-admin-bot/"
        ),
        "completed POKROV 1.0.8 promos/variant-status wave": (
            "docs/developer/work-orders/"
            "2026-08-14-stable-1.0.7-promos-node-status-ru-apps/"
        ),
        "completed conversion-first acquisition and retention wave": (
            "docs/developer/work-orders/"
            "2026-08-14--conversion-acquisition-reconciliation/"
        ),
        "released POKROV 1.0.10 emergency-network wave": (
            "docs/developer/work-orders/2026-08-15--emergency-network/"
        ),
    }
    for owner, directory in expected.items():
        row = f"| `EVIDENCE` | {owner} | `{directory}` | `RECONCILED` |"
        assert row in registry
        index_text = (REPO_ROOT / directory / "INDEX.md").read_text(
            encoding="utf-8"
        )
        assert "Document class: `EVIDENCE`" in index_text


def test_publishing_keeps_release_link_handoff_as_evidence_only() -> None:
    publishing = (
        REPO_ROOT / "docs/operations/publishing-and-signing-guide.md"
    ).read_text(encoding="utf-8")
    runtime_wiring = publishing.split("## Runtime Wiring", 1)[1].split(
        "## Public Mailboxes And PR Readiness", 1
    )[0]
    assert "release-links-and-final-handoff.md" in runtime_wiring
    assert "Operator shortcut" not in runtime_wiring
    assert "retained evidence" in runtime_wiring.casefold()
    assert "not current procedure" in runtime_wiring.casefold()


def test_design_and_surface_docs_have_current_owners() -> None:
    design = (REPO_ROOT / "DESIGN.md").read_text(encoding="utf-8")
    sync = (
        REPO_ROOT / "docs" / "design" / "design-system-sync.md"
    ).read_text(encoding="utf-8")
    generated_policy = (
        REPO_ROOT / "docs" / "design" / "generated-assets-policy.md"
    ).read_text(encoding="utf-8")
    admin = (REPO_ROOT / "adminapp" / "README.md").read_text(encoding="utf-8")
    web = (REPO_ROOT / "webapp" / "README.md").read_text(encoding="utf-8")
    marketing = (REPO_ROOT / "marketing" / "README.md").read_text(encoding="utf-8")

    assert "Document class: CANONICAL" in design
    assert "retained history" in design.casefold()
    assert "SEO/search-intent" in design
    assert "SEO/search-intent" in sync
    assert "avoids direct public `VPN` wording" not in sync
    assert "SEO/search-intent" in generated_policy
    assert "legacy public `VPN` product wording outside unavoidable" not in generated_policy
    assert (
        "docs/developer/work-orders/2026-04-open-beta-v4/evidence/screenshots/"
        not in generated_policy
    )
    assert "docs/design/generated/<YYYY-MM-DD>-<packet>/" in generated_policy
    assert (
        "Keep prompt/reference, source master, derived outputs, review note, "
        "and release-scope note together in that packet."
        in generated_policy
    )
    assert (
        "An active WO may link to its packet; never append new evidence to a "
        "completed WO."
        in generated_policy
    )
    assert (
        "Keep client release evidence authority in the client repository only "
        "where the active client release guide requires it."
        in generated_policy
    )
    assert "primary operator" in admin.casefold()
    assert "parity fallback" in web.casefold()
    assert "acquisition" in marketing.casefold()
    assert "docs/archive/design-plans/2026-06-06-web-admin-site-density-plan.md" in marketing
    assert "docs/design/2026-06-06-web-admin-site-density-plan.md" not in marketing


def test_surface_readme_repo_doc_pointers_resolve() -> None:
    import re

    for source_path in (
        "adminapp/README.md",
        "webapp/README.md",
        "marketing/README.md",
    ):
        text = (REPO_ROOT / source_path).read_text(encoding="utf-8")
        pointers = re.findall(
            r"`((?:docs|shared)/[^`\s]+(?:\.md|\.json))`",
            text,
        )
        for pointer in pointers:
            assert (REPO_ROOT / pointer).exists(), (
                f"{source_path} points to missing repository file {pointer}"
            )


def test_admin_command_center_and_ru_probe_owners_are_cross_linked() -> None:
    admin = (REPO_ROOT / "adminapp/README.md").read_text(encoding="utf-8")
    overview = (
        REPO_ROOT / "docs/architecture/system-overview.md"
    ).read_text(encoding="utf-8")
    monitoring = (
        REPO_ROOT / "docs/operations/monitoring-and-visibility.md"
    ).read_text(encoding="utf-8")
    handoff = (
        REPO_ROOT / "docs/operations/ru-origin-probe-handoff.md"
    ).read_text(encoding="utf-8")
    publishing = (
        REPO_ROOT / "docs/operations/publishing-and-signing-guide.md"
    ).read_text(encoding="utf-8")
    deployment = (
        REPO_ROOT / "docs/operations/deployment-and-access.md"
    ).read_text(encoding="utf-8")

    assert admin.count("| `/") == 22
    for pointer in (
        "docs/architecture/system-overview.md",
        "docs/operations/monitoring-and-visibility.md",
        "docs/operations/ru-origin-probe-handoff.md",
    ):
        assert pointer in admin
    assert "ru_probe_runner.py" in overview
    assert "ru_probe_uploader.py" in overview
    assert "ru_probe_runs + ru_probe_target_results" in overview
    assert "/api/admin/probes/ru-origin/latest" in overview
    assert "/api/admin/v2/network/{traffic|alerts|providers|emergency}" in admin
    assert "/api/admin/v2/network/*" in overview
    assert "/api/admin/v2/network/*" in monitoring
    assert "/api/admin/emergency-network/status" in overview
    assert "/api/admin/emergency-network/status" in monitoring

    combined_ru = monitoring + "\n" + handoff
    for required in (
        "6 hours",
        "7 hours",
        "45 minutes",
        "180 days",
        "MANUAL_OWNER_TEST",
        "BLOCKED_BY_ACCESS",
    ):
        assert required.casefold() in combined_ru.casefold()
    assert "retention_hold=true" in monitoring
    assert "не содержит команд для изменения живого хоста" in handoff

    release_owners = publishing + "\n" + deployment
    for required in (
        "exact candidate",
        "artifact_sha256",
        "POST /api/internal/releases/candidates",
        "retention hold",
        "production deploy",
        "RU-origin",
    ):
        assert required.casefold() in release_owners.casefold()
    assert "do not prove production deploy" in publishing.casefold()
    assert "current workstation only" in deployment.casefold()

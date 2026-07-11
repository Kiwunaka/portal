from __future__ import annotations

from pathlib import Path

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
    assert "Start Here As Agent" not in text


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


def test_orchestration_docs_fit_budgets_and_use_normalized_vocabulary() -> None:
    budgets = {
        "README.md": 4096,
        "orchestration-standard.md": 16384,
        "wo-authoring-guide.md": 12288,
        "flow-state.md": 6144,
        "context-cost-harnesses.md": 12288,
        "roles/orchestrator.md": 5120,
        "templates/WO.template.md": 12288,
        "templates/WAVE-INDEX.template.md": 8192,
    }
    for relative_path, maximum in budgets.items():
        payload = (ORCHESTRATION_ROOT / relative_path).read_bytes()
        assert len(payload) <= maximum, relative_path

    standard = (
        ORCHESTRATION_ROOT / "orchestration-standard.md"
    ).read_text(encoding="utf-8")
    for ceremony in ("direct", "bounded_wo", "release_wo"):
        assert f"`{ceremony}`" in standard
    for stale in ("### Fast", "### Balanced", "### Strict", "Minimal Launch Sequence"):
        assert stale not in standard

    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in ORCHESTRATION_ROOT.rglob("*.md")
    )
    for stale in ("Evidence Source Tiers", "clean_pass", "spec-review", "quality-review"):
        assert stale not in combined


def test_roles_are_scoped_and_do_not_copy_global_read_packs() -> None:
    roles = sorted((ORCHESTRATION_ROOT / "roles").glob("*.md"))
    assert roles
    for role in roles:
        maximum = 5120 if role.name == "orchestrator.md" else 4096
        text = role.read_text(encoding="utf-8")
        assert len(text.encode("utf-8")) <= maximum, role.name
        assert "## REFERENCE DOCS" not in text
        assert "Must-Read" not in text
    assert "optional" in (
        ORCHESTRATION_ROOT / "roles" / "implementation-strategy.md"
    ).read_text(encoding="utf-8").casefold()


def test_default_wo_is_compact_and_flow_state_is_conditional() -> None:
    template = (
        ORCHESTRATION_ROOT / "templates" / "WO.template.md"
    ).read_text(encoding="utf-8")
    for heading in (
        "## Goal",
        "## Non-Goals",
        "## Write Scope",
        "## Authority Anchors",
        "## Acceptance Oracle",
        "## Docs Impact",
        "## Validation And Evidence",
        "## Status And Handoff",
    ):
        assert heading in template
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

    flow = (ORCHESTRATION_ROOT / "flow-state.md").read_text(encoding="utf-8")
    assert "third" in flow.casefold()
    assert "mechanism" in flow.casefold()
    assert "only" in flow.casefold()

from __future__ import annotations

import json
import re
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
UNIVERSAL_FLOW_STATE_REQUIREMENT_RES = (
    re.compile(
        r"\b(?:each|every|all)\s+active\s+`?\bWOs?\b`?\s+"
        r"(?:"
        r"(?:(?:must|should)\s+|(?:is\s+required|needs?)\s+to\s+)"
        r"(?:keep|maintain|create|record|have)|"
        r"(?:requires?|needs?|has|keeps?|maintains?|creates?|records?)"
        r")"
        r"(?:\s+(?:a|an|the))?"
        r"(?:\s+(?:compact|conditional|durable|current|local|valid|explicit|own|shared)){0,2}"
        r"\s+`?\bFLOW(?:_|\s+)STATE\b`?",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"`?\bFLOW(?:_|\s+)STATE\b`?\s+is\s+"
        r"(?:required|mandatory|kept|maintained|created|recorded)\s+"
        r"(?:for|by)\s+(?:each|every|all)\s+active\s+`?\bWOs?\b`?",
        flags=re.IGNORECASE,
    ),
)


def _without_markdown_decoration(value: str) -> str:
    return (
        value.strip()
        .lstrip("-*+> ")
        .replace("**", "")
        .replace("`", "")
        .strip()
    )


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


def _has_universal_flow_state_requirement(text: str) -> bool:
    return any(
        pattern.search(text) is not None
        for pattern in UNIVERSAL_FLOW_STATE_REQUIREMENT_RES
    )


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
    for owner in (standard, quick_start):
        for ceremony in ("direct", "bounded_wo", "release_wo"):
            assert f"`{ceremony}`" in owner

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
    for field in (
        "finding",
        "id",
        "issue_class",
        "severity",
        "reference",
        "required_change",
        "status",
        "evidence",
        "source",
        "target_scope",
        "freshness",
        "attribution",
        "result",
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

    universal_requirement_smoke_cases = (
        ("Each active WO has a status. FLOW_STATE exists only for review...", False),
        (
            "Each active WO should record status. "
            "FLOW_STATE exists only for review...",
            False,
        ),
        ("Every active WO must keep FLOW_STATE.", True),
        ("All active WOs require FLOW_STATE.", True),
        ("FLOW_STATE is not required for each active WO.", False),
        ("Each active WO should keep FLOW_STATE.", True),
        ("Each active WO must maintain FLOW_STATE.", True),
        ("FLOW_STATE is mandatory for all active WOs.", True),
    )
    for statement, expected in universal_requirement_smoke_cases:
        assert _has_universal_flow_state_requirement(statement) is expected
    assert not _has_universal_flow_state_requirement(flow)

    paragraphs = re.split(r"\r?\n\s*\r?\n", flow)
    normalized_paragraphs = [_normalized_prose(paragraph) for paragraph in paragraphs]
    assert any(
        all(
            trigger in paragraph
            for trigger in (
                "flow state",
                "only",
                "review",
                "fix cycle",
                "blocked",
                "partial",
                "durable handoff",
            )
        )
        for paragraph in normalized_paragraphs
    )
    assert any(
        ("third" in paragraph or " 3 " in f" {paragraph} ")
        and all(
            term in paragraph
            for term in (
                "same",
                "class",
                "without",
                "mechanism",
                "change",
                "stop",
                "ordinary",
                "routing",
            )
        )
        for paragraph in normalized_paragraphs
    )

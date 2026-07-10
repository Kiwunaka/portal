# Platform Developer And Orchestration Renewal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make platform orchestration risk-triggered and compact, isolate optional external-model preferences, and reduce developer entrypoints to current workflow and repository ownership.

**Architecture:** First update only the non-overlapping orchestration subtree and the canonical docs-contract test. Then add the operator-only consult playbook. Only after account-foundation and stale-worktree collision resolution may `developer-guide.md` and `repository-map.md` be reconciled.

**Tech Stack:** Markdown, Python 3/pytest contract tests, existing prompt-packet auditor, Git collision checks, OpenCode/OpenRouter as optional operator consults only.

## Global Constraints

- Direct tasks do not require a WO or `FLOW_STATE`.
- Ceremony values are `direct`, `bounded_wo`, and `release_wo`.
- WO status values are `draft | ready | active | review | fix_cycle | blocked | partial | complete`.
- Review verdict values are `pass | changes_required | blocked`.
- Third same-class finding without a mechanism change stops ordinary fix routing.
- `FLOW_STATE` exists only for review/fix-cycle, blocked/partial state, or durable handoff.
- The external-model playbook is `OPERATOR_PLAYBOOK`, opt-in, and absent from normal backend/frontend/client routes.
- Codex remains implementation/orchestration authority.
- Runtime support-AI provider routing stays in its domain architecture/operations docs and is not confused with coding-agent consult routing.
- No new dependency, service, model gateway, MCP server, vector store, or loader.
- Completed WOs are evidence and are never rewritten into current product truth.
- Preserve active and stale dirty worktree changes before touching overlapping developer docs.

---

## Collision-Gated Slices

### Slice A: allowed before account-foundation landing

```text
docs/developer/orchestration/**
docs/developer/work-orders/README.md
tests/test_agent_docs_contract.py
```

Do not modify any other `docs/developer/work-orders/**` path.

### Slice B: allowed only after collision resolution

```text
docs/developer/agent-playbooks/external-model-consults.md
docs/developer/openai-operator-assistants.md
docs/developer/developer-guide.md
docs/developer/repository-map.md
tests/test_agent_docs_contract.py
```

Both `market-ready-cis-integration` and stale
`release-hardening-platform` edit `developer-guide.md` and
`repository-map.md`. Run the snapshot/overlap stage from the cleanup plan
before Slice B.

## File Responsibilities And Budgets

| File | Single responsibility | Hard maximum |
| --- | --- | ---: |
| `orchestration/README.md` | index and ceremony quick start | 4 KiB |
| `orchestration-standard.md` | ceremony, routing, lifecycle, roles, closure | 16 KiB |
| `wo-authoring-guide.md` | compact/full WO and optional proof blocks | 12 KiB |
| `flow-state.md` | conditional review-loop state and stop rule | 6 KiB |
| `context-cost-harnesses.md` | provider-neutral packet/redaction/telemetry | 12 KiB |
| `roles/orchestrator.md` | classification, routing, status, integration | 5 KiB |
| every other role | one bounded role | 4 KiB |
| `templates/WO.template.md` | default compact WO | 12 KiB |
| every other retained template | one artifact contract | 8 KiB |
| `work-orders/README.md` | naming, storage, immutability, evidence boundary | 4 KiB |
| `external-model-consults.md` | optional operator consult preferences | 16 KiB |

---

### Task 1: Add Failing Orchestration Contract Tests

**Files:**
- Modify: `tests/test_agent_docs_contract.py`
- Test: `tests/test_agent_docs_contract.py`

**Interfaces:**
- Consumes: containment constants/helpers
- Produces: one mechanical owner for orchestration vocabulary and budgets

- [ ] **Step 1: Add budget and vocabulary tests**

Append:

```python
ORCHESTRATION_ROOT = REPO_ROOT / "docs" / "developer" / "orchestration"


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
```

- [ ] **Step 2: Run RED**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py -q
```

Expected: failures for current file sizes, stale ceremony/status vocabulary,
copied reference packs, and oversized/default-all-fields WO template.

### Task 2: Rewrite The Orchestration Core

**Files:**
- Modify: `docs/developer/orchestration/README.md`
- Modify: `docs/developer/orchestration/orchestration-standard.md`
- Modify: `docs/developer/orchestration/wo-authoring-guide.md`
- Modify: `docs/developer/orchestration/flow-state.md`
- Modify: `docs/developer/orchestration/context-cost-harnesses.md`
- Modify: `docs/developer/work-orders/README.md`
- Test: `tests/test_agent_docs_contract.py`

**Interfaces:**
- Consumes: normalized values in Global Constraints
- Produces: single process owners without global product/branch duplication

- [ ] **Step 1: Replace ceremony selection**

Use this table in the standard and quick-start index:

```markdown
| Ceremony | Trigger | Required artifacts |
| --- | --- | --- |
| `direct` | small, low-risk, single-pass work | focused validation and handoff |
| `bounded_wo` | durable context, independent review, multiple bounded steps, or meaningful risk | compact WO; selected roles; conditional `FLOW_STATE` |
| `release_wo` | release, deploy, payment, security, persistence, provider, device, or origin-sensitive work | full triggered proof blocks, release validator, candidate-specific evidence |
```

Delete `Fast`, `Balanced`, `Strict`, the global must-read rule, and the
mandatory scout→strategy→executor→reviewer launch chain.

- [ ] **Step 2: Normalize routing and lifecycle**

Use:

```text
WO status:
draft | ready | active | review | fix_cycle | blocked | partial | complete

Review verdict:
pass | changes_required | blocked

Finding status:
open | fixed | accepted_risk | blocked
```

Route by exact write scope and repository lane. Add a collision gate before
execution and whenever write scope changes. Keep branch/promotion details in
the root router/developer guide rather than repeating them in every role.

- [ ] **Step 3: Replace evidence tiers with dimensions**

Use this record everywhere:

```text
name
source
target_scope
freshness
attribution
result
reference
notes
```

Use these exact enums:

```text
source:
static_review | synthetic_test | tracked_fixture | generated_artifact |
api_e2e | ui_behavior | runtime_smoke | full_validation_epoch | manual | n/a

target_scope:
local | exact_candidate | deployed_environment | provider | physical_device |
current_origin | brain_origin | ru_origin

freshness:
current_candidate | current_environment | retained_current | historical_stale

attribution:
wo_owned | wave_integration | pre_existing | unrelated | blocked_by_access
```

Manual records may additionally carry `MANUAL_OWNER_TEST`,
`OPERATOR_ATTESTED`, `SKIPPED_BY_OWNER`, `SKIPPED_BY_OPERATOR`,
`NOT_REQUESTED`, or `BLOCKED_BY_ACCESS`.

- [ ] **Step 4: Make full WO blocks conditional**

The compact WO contains only metadata, goal, non-goals, write/no-touch scope,
authority anchors, acceptance oracle, docs impact, validation/evidence, and
status/handoff.

The authoring guide owns the trigger matrix:

```markdown
| Optional block | Required when |
| --- | --- |
| MREP | a trustworthy end-to-end path exists and local correctness can diverge |
| Risk proof | runtime, persistence, security, payment, release, generated-artifact, or origin risk exists |
| Mechanism adequacy | weak textual proof could falsely close semantic/runtime acceptance |
| Reviewability | an independent reviewer is selected |
| Validation attribution | checks span WO, wave, integration, or pre-existing failures |
| Manual gates | provider, device, signing, store, deploy, account, or origin access is required |
| Promotion evidence | more than a throwaway local edit is intended to land |
| Context/cost harness | reusable prompt, provider route, batch/eval, or prompt-heavy system changes |
```

State that completed WOs are immutable evidence; corrections use an addendum or
superseding WO.

- [ ] **Step 5: Make context/cost provider-neutral**

Keep stable-prefix/dynamic-suffix order, redaction, provider-neutral telemetry,
and `agent_context_packet_audit.py`. Remove the downloaded-playbook
provenance, model/provider routing, exact provider caching thresholds, model
IDs, prices, `opencode.cmd`, and the Codex use-case marketing table.

Do not link the external playbook until Task 5 creates it.

- [ ] **Step 6: Rewrite work-order storage rules**

Remove the volatile `Active Waves` list. State:

- active WOs are `ACTIVE_EXECUTION`;
- completed/superseded WOs are `EVIDENCE`;
- one active `INDEX.md` exists per wave;
- completed evidence is not rewritten into product canon;
- continuity requires goal, scope, authority anchors, validation/evidence,
  blockers, next action, and lane/promotion state.

### Task 3: Rewrite Roles And Templates

**Files:**
- Modify: all seven files under `docs/developer/orchestration/roles/`
- Modify: retained files under `docs/developer/orchestration/templates/`
- Delete: `docs/developer/orchestration/templates/test-quality-report.template.md`
- Test: `tests/test_agent_docs_contract.py`

**Interfaces:**
- Consumes: normalized standard from Task 2
- Produces: bounded paste-ready roles and compact artifact templates

- [ ] **Step 1: Apply exact role boundaries**

```text
orchestrator:
select ceremony; run collision gate; route roles; own status/integration/closure

scout:
read-only anchors; conflicts; scope; docs impact; validation seeds

implementation strategy:
optional approach/invariants/oracle/risks/slices for complex or unclear work

executor:
bounded writes; docs impact; evidence records; never self-close

spec reviewer:
contract compliance only

quality reviewer:
correctness; maintainability; security; performance; usability; evidence quality

release validator:
exact candidate; current gates; origins; manual blockers; rollback; public claims
```

Every role reads the assigned WO/router row/subsystem anchors rather than a
copied global pack.

- [ ] **Step 2: Use one reviewer interface**

```text
verdict: pass | changes_required | blocked
finding: id, issue_class, severity, reference, required_change, status
evidence: source, target_scope, freshness, attribution, result, reference
next_action
```

- [ ] **Step 3: Replace the default WO template**

Use these headings only:

```markdown
# WO
## Metadata
## Goal
## Non-Goals
## Write Scope
## No-Touch Scope
## Authority Anchors
## Acceptance Oracle
## Docs Impact
## Validation And Evidence
## Status And Handoff
```

Do not include fixed subsystem matrices, default `FLOW_STATE`, reviewer logs,
or a fixed document checklist.

- [ ] **Step 4: Normalize the conditional flow state**

Use this complete schema in `flow-state.md`, not in the default WO:

```json
{
  "version": 2,
  "wo_id": "WO-XXX",
  "state": "review",
  "cycle": 1,
  "open_findings": [
    {
      "id": "Q1",
      "owner": "spec",
      "issue_class": "docs_impact_missing",
      "status": "open",
      "mechanism_changed": false,
      "evidence_ref": "review-verdict.md#Q1"
    }
  ],
  "same_class_without_mechanism_change": {
    "docs_impact_missing": 1
  },
  "next_action": "owned_finding_recheck",
  "stop_reason": null
}
```

Allowed states:
`review | fix_cycle | redesign_required | blocked | partial | complete`.

Allowed next actions:
`execute | owned_finding_recheck | fresh_final_review | release_validation |
problem_class_analysis | wait_for_access | close`.

- [ ] **Step 5: Remove the duplicate quality-report template**

Confirm first:

```powershell
rg.exe -n "test-quality-report\.template" .
```

Expected: no live reference. Delete the file and use review verdict plus
completion evidence as the two retained owners.

- [ ] **Step 6: Run the orchestration contract tests**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py -q
git diff --check
```

Expected: budgets, normalized vocabulary, role scoping, compact template, and
conditional flow checks pass.

- [ ] **Step 7: Commit Slice A**

```powershell
git add docs/developer/orchestration docs/developer/work-orders/README.md tests/test_agent_docs_contract.py
git commit -m "docs: simplify risk-aware orchestration"
```

### Task 4: Create The Optional External-Model Playbook

**Files:**
- Create: `docs/developer/agent-playbooks/external-model-consults.md`
- Modify: `docs/developer/orchestration/context-cost-harnesses.md`
- Modify: `docs/developer/openai-operator-assistants.md`
- Modify: `tests/test_agent_docs_contract.py`

**Interfaces:**
- Consumes: provider-neutral harness from Task 2
- Produces: one opt-in owner for model routing, prices, prompts, skill packets, and OpenCode shell notes

- [ ] **Step 1: Add failing isolation tests**

Append:

```python
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

    harness = (
        ORCHESTRATION_ROOT / "context-cost-harnesses.md"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "openrouter/deepseek/deepseek-v4-pro",
        "openrouter/openai/gpt-5.5-pro",
        "opencode.cmd",
        "$30 / $180",
    ):
        assert forbidden not in harness

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
```

- [ ] **Step 2: Run RED**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py -q
```

Expected: missing playbook failure.

- [ ] **Step 3: Verify current model availability and price snapshot**

Run a read-only official OpenRouter model query:

```powershell
$ids = @(
  'deepseek/deepseek-v4-pro',
  'z-ai/glm-5.1',
  'openai/gpt-5.5-pro',
  'moonshotai/kimi-k2.6',
  'moonshotai/kimi-k2.7-code',
  'xiaomi/mimo-v2.5-pro',
  'minimax/minimax-m2.7',
  'nvidia/nemotron-3-ultra-550b-a55b'
)
$response = Invoke-RestMethod -Uri 'https://openrouter.ai/api/v1/models' -Method Get
$response.data |
  Where-Object { $_.id -in $ids } |
  Select-Object id, context_length,
    @{Name='input_per_million'; Expression={ [decimal]$_.pricing.prompt * 1000000 }},
    @{Name='output_per_million'; Expression={ [decimal]$_.pricing.completion * 1000000 }}
```

Expected: returned rows are recorded with `Last verified: 2026-07-10`. A
missing model is marked unavailable in the snapshot rather than silently
replaced. Do not print auth configuration or API keys.

- [ ] **Step 4: Create the playbook with exact ownership**

Use these sections:

```markdown
# External Model Consults
Document class: `OPERATOR_PLAYBOOK`
Usage: opt-in only
Last verified: 2026-07-10

## Authority Boundary
## Data And Secret Boundary
## Current OpenRouter Consult Set
## Price, Availability, And Latency Snapshot
## OpenCode And PowerShell Rules
## Cache-Aware Packet Shape
## SKILL PACKET
## Design Consult Pattern
## Copy Consult Pattern
## Output Extraction And Local Synthesis
```

The model table contains exactly the eight queried IDs. Preserve the current
roles:

- GPT-5.5 Pro: narrow expensive senior review;
- DeepSeek V4 Pro: contradiction and dense design/canon critique, xhigh when
  explicitly needed;
- Kimi K2.6: taste, human Russian copy, roleplay, elegant alternatives;
- Kimi K2.7 Code: code and engineering critique;
- GLM, MiniMax, MiMo, and Nemotron: parallel alternative-angle reviewers.

Every price/availability row says to reverify before cost-sensitive use.

OpenCode rules:

- invoke `opencode.cmd` in PowerShell;
- never invoke `E:/OpenCode/OpenCode.exe` as a CLI;
- never print auth/config contents, headers, bearer material, or secrets;
- use UTF-8 files/helpers if inline Cyrillic becomes garbled;
- extract only the requested final answer and discard hidden reasoning details.

The packet order is stable role/canon/rubric first and dynamic task/date/cwd/
git/file excerpts/tool output last.

- [ ] **Step 5: Link without duplication and classify the old helper**

Add one link from `context-cost-harnesses.md` for optional consult routing.
Mark `openai-operator-assistants.md`:

```text
Document class: EXPERIMENTAL
Not part of the default Codex task route.
Direct canonical reads and rg/Git remain the normal path.
```

Do not add the new playbook to product/support allowlists.

- [ ] **Step 6: Run GREEN and commit**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_pokrov_ai_docs_assistant.py tests/test_pokrov_support_ai_kb_refresh.py -q
git diff --check
git add docs/developer/agent-playbooks/external-model-consults.md docs/developer/orchestration/context-cost-harnesses.md docs/developer/openai-operator-assistants.md tests/test_agent_docs_contract.py
git commit -m "docs: isolate optional model consult playbooks"
```

Expected: playbook isolation tests pass and existing helper/support tests remain
green.

### Task 5: Reconcile Developer Guide And Repository Map

**Files:**
- Modify: `docs/developer/developer-guide.md`
- Modify: `docs/developer/repository-map.md`
- Create or reconcile: `docs/developer/work-orders/2026-07-09-growth-megapass/INDEX.md`
- Modify: `tests/test_agent_docs_contract.py`

**Interfaces:**
- Consumes: landed account-foundation commit and stale-worktree overlap review
- Produces: current workflow owner and current path/test owner

- [ ] **Step 1: Run the collision gate**

```powershell
git status --short --branch
git worktree list --porcelain
git -C ..\market-ready-cis-integration status --short
git -C ..\market-ready-cis-integration diff --name-only -- docs/developer/developer-guide.md docs/developer/repository-map.md
```

Expected: active account-foundation changes are committed and present in the
current baseline. The stale `release-hardening-platform` diff has been
snapshotted and classified. Otherwise stop.

- [ ] **Step 2: Add failing current-entrypoint assertions**

Append:

```python
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
```

Run and expect RED on the stale ownership/version/probe statements.

- [ ] **Step 3: Reduce each entrypoint to one responsibility**

`developer-guide.md` owns:

- task router entry;
- branch/worktree/collision workflow;
- focused backend/web/admin/marketing/infra/client commands;
- docs-impact rules;
- cleanup workflow and never-touch boundary;
- current account-foundation test/command additions.

`repository-map.md` owns:

- top-level path/subsystem ownership;
- standalone `adminapp` and web-admin fallback;
- script categories at entrypoint level;
- concise test entrypoints, including account foundation;
- platform/client/archive boundaries.

Remove global must-read packs, copied release snapshots, feature-tracker
inventories masquerading as canon, model consult routing, stale
`0.x.x-beta`, webapp-primary-admin, and probe-only `mini` wording.

- [ ] **Step 4: Index the active market-ready wave**

The wave index lists:

```text
00-decisions-analysis-and-next-work.md = decision/background
01-market-ready-cis-release-design.md = owner-approved target, not runtime truth
02-market-ready-cis-implementation-workstreams.md = active execution map
03-account-foundation-slice.md = landed additive account-foundation evidence
```

Record current, next, blockers, and links to canonical owners. Do not rewrite
the four source files.

- [ ] **Step 5: Run GREEN and commit**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_account_foundation.py -q
git diff --check
git add docs/developer/developer-guide.md docs/developer/repository-map.md docs/developer/work-orders/2026-07-09-growth-megapass/INDEX.md tests/test_agent_docs_contract.py
git commit -m "docs: reduce developer entrypoints to current ownership"
```

### Task 6: Run Full Developer/Orchestration Regression

**Files:**
- Verify only

- [ ] **Step 1: Run mechanical and compatibility checks**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py tests/test_pokrov_ai_docs_assistant.py tests/test_pokrov_support_ai_kb_refresh.py tests/test_cleanup_inventory.py -q
python scripts/pokrov_ai_docs_assistant.py inventory
python scripts/pokrov_support_ai_kb_refresh.py inventory
python scripts/cleanup_inventory.py --class all --dry-run
git diff --check
git status --short
```

Expected:

- all tests pass;
- no prompt/model/operator playbook enters support or default coding routes;
- no cleanup is applied;
- all orchestration and role budgets pass;
- account-foundation additions remain present.

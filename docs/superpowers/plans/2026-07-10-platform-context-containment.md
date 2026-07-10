# Platform Codex Context Containment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the truncated 39 KiB platform instruction contract with a tested thin root, task router, classified docs registry, and safe cleanup inventory in exactly seven files.

**Architecture:** Extend the existing stdlib context-packet auditor with a platform-context mode and keep packet auditing backward compatible. The root file holds universal guards only; `docs/README.md` owns classification; `agent-context-map.md` owns progressive task routes. Cleanup support is a separate two-file commit.

**Tech Stack:** Markdown, Python 3 standard library, argparse, pathlib, subprocess, pytest, existing cleanup inventory.

## Global Constraints

- Wave 1 changes exactly seven files.
- Root `AGENTS.md`: at most 8,192 UTF-8 bytes and 120 physical lines.
- Router: at most 12,288 UTF-8 bytes and 240 physical lines.
- Only tracked platform instruction file: root `AGENTS.md`.
- No global must-read list, dated release snapshot, model catalog, prices, prompt patterns, active-plan list, or embeddings recommendation.
- Universal secret, destructive-operation, evidence-retention, archive, concurrent-work, release-claim, lane, docs-impact, verification, and handoff guards remain in root.
- No product/economy/ad-filter decision is made in containment.
- No new dependency, service, loader, nested instruction file, or checker script.
- Do not modify docs-assistant/support-KB allowlists in this wave.
- Do not run cleanup with `--apply`.

---

## Exact Write Set

1. `AGENTS.md`
2. `docs/README.md`
3. `docs/developer/agent-context-map.md`
4. `scripts/agent_context_packet_audit.py`
5. `tests/test_agent_docs_contract.py`
6. `scripts/cleanup_inventory.py`
7. `tests/test_cleanup_inventory.py`

If an eighth file is necessary, stop and create a separate reviewed plan task.

### Interfaces

The auditor exports:

```python
ROOT_MAX_BYTES: int
ROOT_MAX_LINES: int
ROUTER_MAX_BYTES: int
ROUTER_MAX_LINES: int
DOCUMENT_CLASSES: tuple[str, ...]
physical_line_count(text: str) -> int
parse_markdown_table(text: str, header: tuple[str, ...]) -> list[dict[str, str]]
find_broken_local_markdown_links(root: Path, relative_paths: Iterable[str]) -> list[str]
tracked_agents_files(root: Path) -> list[str]
audit_platform_context(root: Path) -> list[str]
```

The router table is exactly:

```markdown
| Task | Read first | Inspect | Verify | Docs impact |
```

The registry table is exactly:

```markdown
| Class | Owner | Document | Review state |
```

---

### Task 1: Write The Failing Platform Contract Tests

**Files:**
- Create: `tests/test_agent_docs_contract.py`
- Read: `scripts/agent_context_packet_audit.py`
- Test: `tests/test_agent_docs_contract.py`

**Interfaces:**
- Consumes: existing `audit_text` behavior
- Produces: executable root/router/registry/link/nested-contract requirements

- [ ] **Step 1: Create the test module**

Use this complete test body:

```python
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
```

- [ ] **Step 2: Run the new tests and confirm RED**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py -q
```

Expected: collection/import failure because the new auditor symbols do not
exist. After the symbols exist but before docs rewrite, expected failures
include the 8,192-byte/120-line budget and missing registry/router shape.

### Task 2: Add Platform-Context Audit Mode

**Files:**
- Modify: `scripts/agent_context_packet_audit.py`
- Test: `tests/test_agent_docs_contract.py`
- Regression test: `tests/test_agent_context_packet_audit.py`

**Interfaces:**
- Consumes: test interface from Task 1
- Produces: `python scripts/agent_context_packet_audit.py --platform-context-root .`

- [ ] **Step 1: Add imports and constants**

Add:

```python
import subprocess
from collections.abc import Iterable


ROOT_MAX_BYTES = 8192
ROOT_MAX_LINES = 120
ROUTER_MAX_BYTES = 12288
ROUTER_MAX_LINES = 240

DOCUMENT_CLASSES = (
    "CANONICAL",
    "ACTIVE_EXECUTION",
    "EVIDENCE",
    "HISTORICAL_REFERENCE",
    "OPERATOR_PLAYBOOK",
    "EXPERIMENTAL",
)

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
```

- [ ] **Step 2: Add complete helpers**

Add below `estimate_tokens`:

```python
def physical_line_count(text: str) -> int:
    return len(text.splitlines())


def parse_markdown_table(
    text: str,
    header: tuple[str, ...],
) -> list[dict[str, str]]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
        if cells != header:
            continue
        rows: list[dict[str, str]] = []
        for row_line in lines[index + 2 :]:
            if not row_line.startswith("|"):
                break
            values = tuple(cell.strip() for cell in row_line.strip("|").split("|"))
            if len(values) != len(header):
                break
            rows.append(dict(zip(header, values, strict=True)))
        return rows
    return []


def find_broken_local_markdown_links(
    root: Path,
    relative_paths: Iterable[str],
) -> list[str]:
    broken: list[str] = []
    workspace_prefix = root.resolve().as_posix().rstrip("/") + "/"
    for relative_path in relative_paths:
        document = (root / relative_path).resolve()
        text = document.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK_RE.findall(text):
            target = raw_target.strip().strip("<>").split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            normalized = target.replace("\\", "/")
            if normalized.startswith(workspace_prefix):
                candidate = root / normalized.removeprefix(workspace_prefix)
            elif re.match(r"^[A-Za-z]:/", normalized):
                candidate = Path(normalized)
            else:
                candidate = document.parent / normalized
            if not candidate.exists():
                broken.append(f"{relative_path} -> {target}")
    return sorted(set(broken))


def tracked_agents_files(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "--", "AGENTS.md", ":(glob)**/AGENTS.md"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return sorted(set(completed.stdout.splitlines()))


def audit_platform_context(root: Path) -> list[str]:
    errors: list[str] = []
    agents_path = root / "AGENTS.md"
    router_path = root / "docs" / "developer" / "agent-context-map.md"
    registry_path = root / "docs" / "README.md"

    agents_bytes = agents_path.read_bytes()
    agents_text = agents_bytes.decode("utf-8")
    router_bytes = router_path.read_bytes()
    router_text = router_bytes.decode("utf-8")
    registry_text = registry_path.read_text(encoding="utf-8")

    if len(agents_bytes) > ROOT_MAX_BYTES:
        errors.append(f"AGENTS.md exceeds {ROOT_MAX_BYTES} bytes")
    if physical_line_count(agents_text) > ROOT_MAX_LINES:
        errors.append(f"AGENTS.md exceeds {ROOT_MAX_LINES} lines")
    if len(router_bytes) > ROUTER_MAX_BYTES:
        errors.append(f"agent-context-map.md exceeds {ROUTER_MAX_BYTES} bytes")
    if physical_line_count(router_text) > ROUTER_MAX_LINES:
        errors.append(f"agent-context-map.md exceeds {ROUTER_MAX_LINES} lines")

    for required in (
        "docs/developer/agent-context-map.md",
        "POKROV-app",
        "secrets",
        "archive",
        "evidence",
        "MANUAL_OWNER_TEST",
        "git status",
        "git diff",
    ):
        if required.casefold() not in agents_text.casefold():
            errors.append(f"AGENTS.md missing required semantic anchor: {required}")

    for forbidden in (
        "Current Release Gate Snapshot",
        "Must-Read Order",
        "Preferred model routing",
        "Copy rewrite prompt pattern",
        "Active Plans Quick Access",
    ):
        if forbidden.casefold() in agents_text.casefold():
            errors.append(f"AGENTS.md contains volatile section: {forbidden}")

    if "| Task | Read first | Inspect | Verify | Docs impact |" not in router_text:
        errors.append("agent-context-map.md lacks task router table")
    if "| Class | Owner | Document | Review state |" not in registry_text:
        errors.append("docs/README.md lacks registry table")
    if tracked_agents_files(root) != ["AGENTS.md"]:
        errors.append("tracked platform AGENTS.md set is not root-only")
    errors.extend(
        find_broken_local_markdown_links(
            root,
            ("AGENTS.md", "docs/README.md", "docs/developer/agent-context-map.md"),
        )
    )
    return errors
```

- [ ] **Step 3: Add the CLI mode without breaking packet mode**

Change positional files to `nargs="*"`, add:

```python
    parser.add_argument(
        "--platform-context-root",
        type=Path,
        help="Audit the platform AGENTS/router/registry contract.",
    )
```

Route after `parse_args`:

```python
    if bool(args.files) == bool(args.platform_context_root):
        parser.error("provide packet files or --platform-context-root, not both")

    if args.platform_context_root:
        errors = audit_platform_context(args.platform_context_root.resolve())
        if args.json:
            print(json.dumps({"errors": errors}, ensure_ascii=False, indent=2))
        else:
            status = "PASS" if not errors else "FAIL"
            print(f"{status} platform-context")
            for error in errors:
                print(f"  {error}")
        return 0 if not errors else 1
```

Keep the existing packet-audit branch unchanged below the new mode.

- [ ] **Step 4: Run tests**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_agent_context_packet_audit.py tests/test_agent_docs_contract.py -q
```

Expected: existing packet tests pass; docs-contract tests fail only on the
current oversized/stale Markdown files.

### Task 3: Rewrite Root, Registry, And Router

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/README.md`
- Modify: `docs/developer/agent-context-map.md`
- Test: `tests/test_agent_docs_contract.py`

**Interfaces:**
- Consumes: platform audit mode
- Produces: the universal root, classification registry, and progressive routes

- [ ] **Step 1: Replace root with the thin contract**

Use these headings and only their stated responsibilities:

```markdown
# Repository Agent Contract
## Scope And Lanes
## Start Here
## Authority And Current Truth
## Universal Safety
## Release And Evidence Honesty
## Git, Worktrees, And Cleanup
## Documentation Impact
## Verification And Handoff
```

Required residue:

- platform path ownership and separate `POKROV-app/main`;
- inspect `git status`/`git diff`, classify task, open one router row;
- system/developer/user/repository instruction precedence;
- no secret printing, committing, or moving;
- no broad deletion; preserve evidence, archive, and concurrent work;
- candidate/manual labels including `MANUAL_OWNER_TEST`;
- no unsupported stable/store/signing/device/RU-origin/payment claim;
- external model output is advisory and redacted;
- behavior changes update their canonical owner;
- focused checks and compact handoff.

Do not copy product values, host/bot registries, release dates, provider/model
lists, prices, prompt packets, or active plans.

- [ ] **Step 2: Replace docs index with a classified registry**

Start with this table and add every important active document without claiming
an unperformed review:

```markdown
| Class | Owner | Document | Review state |
| --- | --- | --- | --- |
| `CANONICAL` | product | `docs/product/portal-vpn-product.md` | `PENDING_WAVE_3` |
| `ACTIVE_EXECUTION` | market-ready wave | `docs/developer/work-orders/2026-07-09-growth-megapass/` | `PENDING_WAVE_3` |
| `EVIDENCE` | release evidence | `docs/audit-artifacts/` | `REVIEWED_NO_CHANGE` |
| `HISTORICAL_REFERENCE` | archive | `docs/archive/` | `REVIEWED_NO_CHANGE` |
| `OPERATOR_PLAYBOOK` | operator consults | `docs/developer/agent-playbooks/external-model-consults.md` | `PENDING_WAVE_2` |
| `EXPERIMENTAL` | OpenAI helper | `docs/developer/openai-operator-assistants.md` | `PENDING_WAVE_2` |
```

- [ ] **Step 3: Replace the router with direct routes**

Include the exact 11 task names asserted by the test. Add:

- task/workflow: system/developer → user → root contract → scoped contract →
  router/process docs;
- intended product: owner-approved shared contracts → canonical domain docs →
  current code/tests → active WOs → history → external critique;
- observed runtime: production DB/provider/control state → exact current
  runtime/API/UI/device/origin evidence → generated artifacts → older evidence;
- release claims: exact candidate → current candidate gates → required
  manual/provider/device/origin checks → current release decision → history;
- platform/client lane boundary;
- release/manual/origin labels;
- archive route: registry → `rg` → Git → targeted history;
- rule that history explains why and never decides current action;
- direct files and focused commands in every row.

Remove the dated beta status block, global read loop, combined web/admin route,
and vector/embeddings proposal.

- [ ] **Step 4: Run GREEN checks**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_agent_context_packet_audit.py tests/test_agent_docs_contract.py -q
python -B scripts/agent_context_packet_audit.py --platform-context-root .
git diff --check
```

Expected: tests pass and CLI prints `PASS platform-context`.

- [ ] **Step 5: Commit containment**

```powershell
git add AGENTS.md docs/README.md docs/developer/agent-context-map.md scripts/agent_context_packet_audit.py tests/test_agent_docs_contract.py
git commit -m "docs: contain Codex repository context"
```

### Task 4: Add Cleanup Containment

**Files:**
- Modify: `scripts/cleanup_inventory.py`
- Modify: `tests/test_cleanup_inventory.py`

**Interfaces:**
- Consumes: existing `DirRule` and protected-zone behavior
- Produces: safe `adminapp/out` inventory and protected local video workspace

- [ ] **Step 1: Add failing cleanup tests**

Add:

```python
    def test_adminapp_static_export_is_safe_generated_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "adminapp" / "out").mkdir(parents=True)
            matches = self.module._walk_inventory(
                root,
                (self.module.CLASS_SAFE,),
            )

        match = next(item for item in matches if item.path == "adminapp/out/")
        self.assertEqual(match.cleanup_class, self.module.CLASS_SAFE)

    def test_content_video_workspace_is_never_traversed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".content-video-ad" / "__pycache__").mkdir(parents=True)
            matches = self.module._walk_inventory(
                root,
                (self.module.CLASS_SAFE,),
            )

        self.assertFalse(
            any(item.path.startswith(".content-video-ad/") for item in matches)
        )
```

- [ ] **Step 2: Run RED**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_cleanup_inventory.py -q
```

Expected: `adminapp/out/` is missing and the local video path is discoverable
under current generic cache rules.

- [ ] **Step 3: Implement the minimal cleanup rules**

Add `adminapp/out` to the existing static-export `exact_paths` tuple:

```python
exact_paths=(
    PurePosixPath("adminapp/out"),
    PurePosixPath("webapp/out"),
    PurePosixPath("webapp/dist"),
    PurePosixPath("marketing/out"),
),
```

Add this entry to `PROTECTED_DIRS`:

```python
PurePosixPath(".content-video-ad"),
```

- [ ] **Step 4: Run GREEN**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_cleanup_inventory.py -q
python scripts/cleanup_inventory.py --class all --dry-run
git diff --check
```

Expected: tests pass; dry run never reports `.content-video-ad/**`; no deletion
occurs.

- [ ] **Step 5: Commit cleanup guard**

```powershell
git add scripts/cleanup_inventory.py tests/test_cleanup_inventory.py
git commit -m "chore: protect current generated and local workspaces"
```

### Task 5: Run The Full Containment Regression

**Files:**
- Verify only

**Interfaces:**
- Consumes: two containment commits
- Produces: Wave 1 completion evidence

- [ ] **Step 1: Run focused regression**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_agent_context_packet_audit.py tests/test_agent_docs_contract.py tests/test_pokrov_ai_docs_assistant.py tests/test_pokrov_support_ai_kb_refresh.py tests/test_cleanup_inventory.py -q
```

Expected: all tests pass. A Windows pytest temp cleanup warning is non-blocking
only if the process exits 0 and every named test passed.

- [ ] **Step 2: Confirm the exact write set**

```powershell
git diff master...HEAD --name-only
git status --short
```

Expected for Wave 1 commits: only the seven files listed at the top of this
plan, plus already committed spec/plan files.

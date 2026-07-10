# POKROV Codex And Documentation Renewal Roadmap

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the approved Codex instruction and active-documentation renewal across the platform repo, `POKROV-app`, and local worktree estate without overwriting concurrent work or promoting historical evidence into current canon.

**Architecture:** Execute five independently reviewable plans. Containment lands first because the current root instruction chain is truncated; developer/canon work waits for the active account-foundation branch; client work uses its own Git lane; cleanup and promotion run last from verified snapshots.

**Tech Stack:** Markdown, Python 3 standard library, pytest, Git worktrees, PowerShell Core, existing repository validation scripts, Flutter/Dart tooling already present in `POKROV-app`.

## Global Constraints

- Platform instruction architecture is Codex-only.
- Platform and client root `AGENTS.md` files must each be at most 8,192 UTF-8 bytes and 120 physical lines.
- Platform `docs/developer/agent-context-map.md` must be at most 12,288 UTF-8 bytes and 240 physical lines.
- No new dependency, service, MCP server, vector store, GraphRAG layer, documentation generator, or manifest loader.
- No tracked nested platform `AGENTS.md` files.
- The external-model consult playbook is operator-only and is not required reading for ordinary coding tasks.
- Historical retrieval uses the registry, `rg`, and Git now; no index is implemented in this program.
- Archive and evidence may explain why but may not define what to do now.
- Completed evidence, release artifacts, generated design assets, secrets, `ops-local/**`, and active neighboring worktrees are not rewritten or deleted.
- Current distributed beta is `1.0.0-beta`; `1.0.0-rc.1` is target candidate state; stable `1.0.0` is not proven.
- Current `5 days + 10 days` economics remain current until the neighboring implementation and migration evidence prove a replacement.
- Ad filtering remains `UNRESOLVED_OWNER_DECISION`; documentation alone cannot settle it.
- Every wave starts with a branch/HEAD/dirty-path collision gate.
- Platform and client commits, tests, promotion evidence, and rollback remain separate.

---

## Plan Set And Interfaces

| Order | Plan | Produces | Consumed by |
| --- | --- | --- | --- |
| 1 | `2026-07-10-platform-context-containment.md` | thin root contract, task router, registry baseline, size/semantic tests | every later platform task |
| 2 | `2026-07-10-platform-docs-orchestration-renewal.md` | compact developer/orchestration contracts and operator-only external consult playbook | canonical refresh and future orchestrated work |
| 3 | `2026-07-10-platform-canon-refresh.md` | reconciled active platform canon and current/history/evidence classification | client cross-repo alignment |
| 4 | `2026-07-10-pokrov-app-context-docs-renewal.md` | client root contract, client task routes, reconciled client canon | final cross-repo verification |
| 5 | `2026-07-10-worktree-cleanup-promotion.md` | recoverable stale-worktree snapshots, clean steady state, promoted platform/client lines | final handoff |

The exact approved design is
`docs/superpowers/specs/2026-07-10-agent-context-refactor-design.md` at
platform commit `c584916`.

Plan 5 has an early non-destructive Stage A. Run that inventory/snapshot stage
before plans 2 and 3 because stale dirty worktrees also edit active docs.
Destructive removal and branch deletion remain last.

### Interface: collision gate

Every sub-plan consumes this record:

```text
repository
baseline_branch
baseline_head
active_worktrees
dirty_paths
planned_write_paths
overlap
decision = proceed | narrow | wait | replay
```

If `overlap` is non-empty and the owning work is not committed, the decision
cannot be `proceed`.

### Interface: document registry

Both repository indexes use the same classes:

```text
CANONICAL
ACTIVE_EXECUTION
EVIDENCE
HISTORICAL_REFERENCE
OPERATOR_PLAYBOOK
EXPERIMENTAL
```

Each registered active document has one owner and one class. The registry
points to evidence/history without changing its contents.

### Interface: verification evidence

Every task records:

```text
source
target_scope
freshness
attribution
command_or_artifact
result
```

Do not collapse static review, candidate identity, runtime environment,
manual/origin scope, freshness, and attribution into one numeric tier.

---

### Task 1: Confirm The Approved Baseline

**Files:**
- Read: `docs/superpowers/specs/2026-07-10-agent-context-refactor-design.md`
- Read: all five plans listed above
- Do not modify: `.worktrees/market-ready-cis-integration/**`
- Do not modify: `C:/Users/kiwun/Documents/ai/POKROV-app/.worktrees/market-ready-cis-client-integration/**`

**Interfaces:**
- Consumes: approved design commit `c584916`
- Produces: first collision-gate record

- [ ] **Step 1: Verify the platform planning branch**

Run:

```powershell
git branch --show-current
git rev-parse --short HEAD
git status --short
```

Expected: branch `codex/agent-context-refactor`; HEAD contains `c584916);
only the new plan files may be dirty while planning is in progress.

- [ ] **Step 2: Verify the neighboring platform task without reading secret content**

Run from
`C:/Users/kiwun/Documents/ai/VPN/.worktrees/market-ready-cis-integration`:

```powershell
git branch --show-current
git rev-parse --short HEAD
git status --short
git diff --name-only
```

Expected: branch `codex/market-ready-cis-integration`; any dirty overlap is
recorded and blocks the corresponding later plan.

- [ ] **Step 3: Verify the client baseline**

Run from `C:/Users/kiwun/Documents/ai/POKROV-app`:

```powershell
git branch --show-current
git rev-parse --short HEAD
git status --short
git worktree list --porcelain
```

Expected: the main checkout is clean; active client integration remains a
separate worktree; the exact HEAD is copied into the collision record.

### Task 2: Execute Containment

**Files:**
- Plan: `docs/superpowers/plans/2026-07-10-platform-context-containment.md`

**Interfaces:**
- Consumes: first collision-gate record
- Produces: tested thin root and router contract

- [ ] **Step 1: Execute every containment checkbox**

Use `superpowers:subagent-driven-development` or
`superpowers:executing-plans`.

Expected: containment is committed independently and changes no more than the
plan's explicit write set.

- [ ] **Step 2: Run the containment plan's final command set**

Expected: byte/line/semantic/link/allowlist tests pass and the active
neighboring worktrees have unchanged status.

- [ ] **Step 3: Execute only orchestration Plan Slice A when still non-overlapping**

Allowed early paths are `docs/developer/orchestration/**`,
`docs/developer/work-orders/README.md`, and
`tests/test_agent_docs_contract.py`.

Expected: the risk-aware orchestration commit lands independently. Do not touch
`developer-guide.md`, `repository-map.md`, or active growth-wave files yet.

### Task 3: Wait For Or Reconcile Account-Foundation Landing

**Files:**
- Collision candidates:
  - `docs/architecture/app-first-and-bonus-flows.md`
  - `docs/architecture/system-overview.md`
  - `docs/developer/developer-guide.md`
  - `docs/developer/repository-map.md`
  - `docs/developer/work-orders/2026-07-09-growth-megapass/03-account-foundation-slice.md`
- Stale overlap sources:
  - `C:/Users/kiwun/.config/superpowers/worktrees/VPN/premium-bank-app-portal`
  - `C:/Users/kiwun/.config/superpowers/worktrees/VPN/release-hardening-platform`
  - `C:/Users/kiwun/.config/superpowers/worktrees/POKROV-app/release-hardening-client`

**Interfaces:**
- Consumes: committed containment
- Produces: updated platform baseline suitable for plans 2 and 3

- [ ] **Step 1: Require the neighboring implementation to be committed**

Run in the neighboring platform worktree:

```powershell
git status --short
git log -1 --oneline
```

Expected: clean status and a commit that preserves the account-foundation code,
tests, and four active-doc changes. If status is dirty, stop here.

- [ ] **Step 2: Run Plan 5 Stage A for every stale dirty worktree**

Expected: tracked/untracked patches and retained ignored state are snapshotted;
overlap with the developer/canonical/client plans is classified before any
older worktree is removed.

- [ ] **Step 3: Replay the planning branch on the committed baseline**

Use the exact rebase procedure in the cleanup/promotion plan.

Expected: no product/account/payment conflict is resolved by taking the older
planning-branch copy.

### Task 4: Execute Platform And Client Renewal

**Files:**
- Plan: `docs/superpowers/plans/2026-07-10-platform-docs-orchestration-renewal.md`
- Plan: `docs/superpowers/plans/2026-07-10-platform-canon-refresh.md`
- Plan: `docs/superpowers/plans/2026-07-10-pokrov-app-context-docs-renewal.md`

**Interfaces:**
- Consumes: committed containment and reconciled platform/client baselines
- Produces: independently tested platform and client documentation commits

- [ ] **Step 1: Execute the developer/orchestration plan**

Expected: direct tasks stay direct; WO/review/release ceremony is trigger-based;
the external-model playbook is optional.

- [ ] **Step 2: Execute the platform canon plan**

Expected: every important doc is classified and either reconciled or recorded
as `REVIEWED_NO_CHANGE`; evidence/history contents remain intact.

- [ ] **Step 3: Execute the client plan in a dedicated client worktree**

Expected: `POKROV-app` has its own thin root contract, task routes, and
current-vs-history boundaries; release artifacts are untouched.

### Task 5: Promote And Clean

**Files:**
- Plan: `docs/superpowers/plans/2026-07-10-worktree-cleanup-promotion.md`

**Interfaces:**
- Consumes: green platform and client commits
- Produces: platform `master`, client `main`, retained snapshots, and only
  active worktrees

- [ ] **Step 1: Execute snapshot and cleanup stages before branch deletion**

Expected: every dirty stale worktree has a readable stash and every retained
ignored path has a verified external local snapshot or causes cleanup to stop.

- [ ] **Step 2: Promote without force**

Expected: platform commits are reachable from `master`; client commits are
reachable from `main`; no force push, hard reset, or forced worktree removal
is used.

- [ ] **Step 3: Run the cross-repository final verification**

Expected: all commands from the five plans pass, active neighboring work is
preserved, and final Git/worktree status matches the steady state defined in
the approved spec.

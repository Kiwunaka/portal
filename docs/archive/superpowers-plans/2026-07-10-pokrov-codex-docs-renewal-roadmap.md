# POKROV Codex And Documentation Renewal Roadmap

> **Archived execution record — historical/non-executable.** This roadmap preserves the original task sequence and checkboxes as evidence. Do not execute it as a current plan; use the current owners and task router instead.

**Goal:** Deliver the approved Codex instruction and active-documentation renewal across the platform repo, `POKROV-app`, and local worktree estate without overwriting concurrent work or promoting historical evidence into current canon.

**Architecture:** Execute five independently reviewable plans. Containment lands first because the current root instruction chain is truncated; the landed account-foundation baseline now allows the remaining developer/canon work to proceed in a fixed shared-test order; client work uses its own Git lane. Cleanup Stage B/C, promotion, push, and deploy remain deferred after verified snapshots.

**Tech Stack:** Markdown, Python 3 standard library, pytest, Git worktrees, PowerShell Core, existing repository validation scripts, Flutter/Dart tooling already present in `POKROV-app`.

## Retained Execution Snapshot — 2026-07-12 (superseded)

- Platform containment is complete: root `AGENTS.md`, the task router, classified registry, guards, and official Codex alignment are committed on `codex/agent-context-refactor`.
- Orchestration Slice A and the optional external-model playbook are complete. The playbook is opt-in, isolated from default routes, and introduces no dependency or service. Remaining orchestration Tasks 5 and 6 must run before platform-canon Task 2 because both plans modify `tests/test_agent_docs_contract.py`.
- Client Tasks 1–5 are complete on `codex/agent-context-refactor-client` through `3507d9f`; the separate local-scope clarification is `4b6124b`. Client docs, seeds, layout, Flutter suites, and Android Gradle validation passed; release artifacts and the release-handoff seed are unchanged. Review result is `PASS_WITH_MINOR`: the three renewal commits revert cleanly in reverse order, but the first two are not conflict-free when reverted individually from the final head because they share one guard file.
- Account foundation landed as reviewed commit `db00e1e`; local platform `master` reached it. Production deployment and a real PostgreSQL two-connection concurrency proof remain manual gates.
- The documentation branch replayed cleanly onto `db00e1e` through `8cec9ba`; all 27 documentation patches retained identical stable patch IDs.
- Platform canonical refresh is `UNBLOCKED_NOT_EXECUTED`: the former branch collision is resolved, but no canon task has run.
- Cleanup Stage A is complete: snapshots and three named stashes preserve the stale worktrees. Cleanup Stage B/C and every destructive cleanup action are `DEFERRED`; no proof gate was pinned, no production cleanup command ran, and no ignored output, worktree, or branch was deleted.
- Promotion, push, deploy, and manual release gates have not run. Preserve the two documentation branches and the active neighboring worktrees until an explicit reconciliation/promotion pass.

## Closure — 2026-07-14

Platform canon landed through `5553d22`, and local `master` reached `35975f5`.
Client renewal landed through `efb6aea`.

No push, deploy, destructive cleanup, or manual release gates ran as part of this closure. This closure is not a release, deploy, or production-readiness claim.

All old worktree paths, hashes `4722cd8` and `4b6124b`, deferred promotion commands, and the final verification recipe below are retained as historical/non-executable evidence. Do not run them as current instructions.

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
- Complete orchestration-plan Tasks 5 and 6 before platform-canon Task 2; do
  not interleave their shared `tests/test_agent_docs_contract.py` edits.
- This roadmap does not authorize deploy, push, promotion, destructive
  cleanup, package installation, or a new dependency, index, MCP, service, or
  documentation generator.

---

## Plan Set And Interfaces

| Order | Plan | Produces | Consumed by |
| --- | --- | --- | --- |
| 1 | `2026-07-10-platform-context-containment.md` | thin root contract, task router, registry baseline, size/semantic tests | every later platform task |
| 2 | `2026-07-10-platform-docs-orchestration-renewal.md` | compact developer/orchestration contracts and operator-only external consult playbook | canonical refresh and future orchestrated work |
| 3 | `2026-07-10-platform-canon-refresh.md` | reconciled active platform canon and current/history/evidence classification | client cross-repo alignment |
| 4 | `2026-07-10-pokrov-app-context-docs-renewal.md` | client root contract, client task routes, reconciled client canon | final cross-repo verification |
| 5 | `2026-07-10-worktree-cleanup-promotion.md` | completed Stage A snapshots; Stage B/C and promotion remain deferred | future owner-authorized handoff |

The exact approved design is
`docs/archive/superpowers-plans/2026-07-10-agent-context-refactor-design.md` at
platform commit `c584916`.

Plan 5 has an early non-destructive Stage A. Run that inventory/snapshot stage
before plans 2 and 3 because stale dirty worktrees also edit active docs.
Destructive removal, branch deletion, promotion, push, and deploy remain
deferred; this roadmap amendment does not authorize them.

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
- Read: `docs/archive/superpowers-plans/2026-07-10-agent-context-refactor-design.md`
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
git merge-base --is-ancestor c584916 HEAD
```

Expected: branch `codex/agent-context-refactor`; HEAD contains `c584916`;
`git status --short` is empty; the ancestry check exits `0`.

- [ ] **Step 2: Verify the neighboring platform task without reading secret content**

Run from
`C:/Users/kiwun/Documents/ai/VPN/.worktrees/market-ready-cis-integration`:

```powershell
git branch --show-current
git rev-parse --short HEAD
git status --short
git diff --name-only
```

Expected: branch `codex/market-ready-cis-integration`; HEAD is `db00e1e`; the
worktree is clean. The former dirty overlap is resolved and no longer blocks
the later canon plan.

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

### Task 2: Preserve Completed Containment — Do Not Re-run

**Files:**
- Plan: `docs/superpowers/plans/2026-07-10-platform-context-containment.md`

**Interfaces:**
- Consumes: retained containment commit and verification record
- Produces: a no-rerun boundary for the tested thin root and router contract

- [x] **Step 1: Containment landed with every checkbox complete**

Recorded result: containment is committed independently and changes no more
than the plan's explicit write set. Do not execute it again.

- [x] **Step 2: The containment final command set passed**

Recorded result: byte/line/semantic/link/allowlist tests passed and the active
neighboring worktrees had unchanged status.

- [x] **Step 3: Orchestration Plan Slice A landed independently**

The completed early paths are `docs/developer/orchestration/**`,
`docs/developer/work-orders/README.md`, and
`tests/test_agent_docs_contract.py`.

Recorded result: the risk-aware orchestration commit landed independently and
did not touch `developer-guide.md`, `repository-map.md`, or active growth-wave
files. Do not replay this slice.

### Task 3: Confirm The Replayed Account-Foundation Baseline

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
- Produces: verified platform baseline suitable for the remaining orchestration and canon tasks

- [ ] **Step 1: Verify the landed account-foundation baseline**

```powershell
git rev-parse --short master
git merge-base --is-ancestor db00e1e HEAD
git merge-base --is-ancestor 8cec9ba HEAD
git rev-list --count db00e1e..8cec9ba
```

Expected: local `master` is `db00e1e`; both ancestry checks exit `0`; the
recorded replay contains exactly 27 patches through `8cec9ba`, with the
already reviewed identical stable patch IDs. Later plan-amendment commits may
follow `8cec9ba` without changing that replay record.

- [ ] **Step 2: Confirm the completed Stage A retention record**

Expected: tracked/untracked patches and retained ignored state are snapshotted;
three named stashes preserve the stale worktrees; overlap with the
developer/canonical/client plans is classified. Do not run Stage B/C or remove
an older worktree.

- [ ] **Step 3: Preserve the reviewed replay boundary**

Expected: no product/account/payment conflict is re-resolved and the landed
system/app-first docs, account service, and account tests remain the read-only
truth used by the canon plan.

### Task 4: Execute Remaining Platform Renewal And Preserve Client Renewal

**Files:**
- Plan: `docs/superpowers/plans/2026-07-10-platform-docs-orchestration-renewal.md`
- Plan: `docs/superpowers/plans/2026-07-10-platform-canon-refresh.md`
- Plan: `docs/superpowers/plans/2026-07-10-pokrov-app-context-docs-renewal.md`

**Interfaces:**
- Consumes: committed containment and reconciled platform/client baselines
- Produces: independently tested platform and client documentation commits

- [ ] **Step 1: Finish orchestration Tasks 5 and 6 before canon assertions**

Execute the developer-guide, repository-map, active growth-wave index, and
full orchestration regression in that order. Expected: direct tasks stay
direct; WO/review/release ceremony is trigger-based; the external-model
playbook is optional; the resulting `tests/test_agent_docs_contract.py` is
committed and green before platform-canon Task 2 starts.

- [ ] **Step 2: Execute the platform canon plan**

Expected: every important doc is classified and either reconciled or recorded
as `REVIEWED_NO_CHANGE`; Task 1A makes the client resolver work from the root
checkout and `.worktrees/**`; evidence/history contents remain intact.

- [x] **Step 3: Preserve the completed client-plan result**

Recorded result: `POKROV-app` has its own thin root contract, task routes, and
current-vs-history boundaries through `3507d9f`, with the local-scope
clarification at `4b6124b`; release artifacts and the release-handoff seed are
untouched. Do not execute the client plan again.

### Task 5: Keep Promotion And Destructive Cleanup Deferred

**Files:**
- Plan: `docs/superpowers/plans/2026-07-10-worktree-cleanup-promotion.md`

**Interfaces:**
- Consumes: green platform and client commits
- Produces: an explicit deferred-state handoff with retained Stage A snapshots

- [x] **Step 1: Stage A snapshots were retained and verified**

Recorded result: the completed Stage A evidence covers every formerly dirty
stale worktree, the three named stashes, and retained ignored-path snapshots.
Do not rerun Stage A, remove a worktree, delete a branch, or run Stage B/C.

- [x] **Step 2: Promotion remains explicitly unauthorized**

Recorded boundary: no branch promotion, push, deploy, force push, hard reset,
or forced worktree removal runs under this roadmap amendment.

- [ ] **Step 3: Run the exact final read-only verification set**

Run only these commands; do not invoke any plan's RED step, `git add`,
`git mv`, `git commit`, cleanup/promotion command, push/deploy command, or
destructive operator:

```powershell
$platform = 'C:\Users\kiwun\Documents\ai\VPN\.worktrees\agent-context-refactor'
$account = 'C:\Users\kiwun\Documents\ai\VPN\.worktrees\market-ready-cis-integration'
$clientMain = 'C:\Users\kiwun\Documents\ai\POKROV-app'
$clientDocs = 'C:\Users\kiwun\Documents\ai\POKROV-app\.worktrees\agent-context-refactor-client'
$python = 'C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe'

function Assert-CleanRepo([string]$label, [string]$path) {
  $status = @(& git -C $path status --short)
  if ($LASTEXITCODE -ne 0) {
    throw "$label status failed with exit $LASTEXITCODE"
  }
  if ($status.Count -ne 0) {
    throw "$label is not clean ($($status.Count) path(s))"
  }
  & git -C $path diff --check
  if ($LASTEXITCODE -ne 0) {
    throw "$label diff check failed with exit $LASTEXITCODE"
  }
}

Assert-CleanRepo 'platform' $platform
Assert-CleanRepo 'account-foundation worktree' $account
Assert-CleanRepo 'client main checkout' $clientMain
Assert-CleanRepo 'client docs worktree' $clientDocs

foreach ($commit in @('c584916', 'db00e1e', '8cec9ba')) {
  & git -C $platform merge-base --is-ancestor $commit HEAD
  if ($LASTEXITCODE -ne 0) {
    throw "platform HEAD does not contain $commit"
  }
}
$accountHead = & git -C $account rev-parse --short HEAD
if ($LASTEXITCODE -ne 0 -or $accountHead -ne 'db00e1e') {
  throw "account-foundation HEAD is $accountHead instead of db00e1e"
}
$clientMainBranch = & git -C $clientMain branch --show-current
if ($LASTEXITCODE -ne 0 -or $clientMainBranch -ne 'main') {
  throw "client main checkout branch is $clientMainBranch instead of main"
}
$clientMainHead = & git -C $clientMain rev-parse --short HEAD
if ($LASTEXITCODE -ne 0 -or $clientMainHead -ne '4722cd8') {
  throw "client main checkout moved from deferred-promotion head 4722cd8 to $clientMainHead"
}
$clientDocsBranch = & git -C $clientDocs branch --show-current
if ($LASTEXITCODE -ne 0 -or $clientDocsBranch -ne 'codex/agent-context-refactor-client') {
  throw "client docs worktree branch is $clientDocsBranch"
}
$clientDocsHead = & git -C $clientDocs rev-parse --short HEAD
if ($LASTEXITCODE -ne 0 -or $clientDocsHead -ne '4b6124b') {
  throw "client docs worktree HEAD is $clientDocsHead instead of 4b6124b"
}
foreach ($commit in @('3507d9f', '4b6124b')) {
  & git -C $clientDocs merge-base --is-ancestor $commit HEAD
  if ($LASTEXITCODE -ne 0) {
    throw "client docs worktree HEAD does not contain $commit"
  }
}

Push-Location $platform
try {
  & $python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_beta_known_limitations_contract.py tests/test_shared_surface_facts.py tests/test_pokrov_migration_defaults.py tests/test_account_foundation.py tests/test_check_script_manifest.py tests/test_public_copy_guardrails.py tests/test_frontend_text_integrity.py tests/test_admin_design_guardrails.py tests/test_pokrov_ai_docs_assistant.py -q
  if ($LASTEXITCODE -ne 0) {
    throw "platform final pytest suite failed with exit $LASTEXITCODE"
  }
  & $python scripts/check-links.py
  if ($LASTEXITCODE -ne 0) {
    throw "platform link check failed with exit $LASTEXITCODE"
  }
} finally {
  Pop-Location
}

Assert-CleanRepo 'platform after verification' $platform
Assert-CleanRepo 'account-foundation worktree after verification' $account
Assert-CleanRepo 'client main checkout after verification' $clientMain
Assert-CleanRepo 'client docs worktree after verification' $clientDocs
```

Expected: the platform, account-foundation, root client `main`, and client docs
checkouts all remain clean. Root client `main` stays exactly at
`4722cd8`; the docs worktree stays on
`codex/agent-context-refactor-client` at `4b6124b` and contains both completed
docs commits. Platform ancestry checks, the listed GREEN pytest suite, link
check, and both pre/post `git diff --check` passes for all four checkouts exit
`0`. Do not fast-forward or promote client `main`: Stage B/C, promotion, push,
and deploy remain deferred, and no command above changes repository or
external state.

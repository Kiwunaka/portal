# POKROV Orchestration Standard

Last updated: 2026-04-23

## Document Status

This file is living source of truth for orchestrated work in the `POKROV` workspace.

## Purpose

Use this standard for multi-step, multi-review, or multi-repository work that should survive chat boundaries without losing intent, evidence, or closure state.

The goal is not maximum autonomy.

The goal is reliable execution with:

- one work-order contract per unit of work
- one orchestrator that owns routing and status
- fresh-context review after implementation
- durable evidence for validation, manual checks, and git state

## When To Use

Use orchestrated work when at least one of these is true:

- the task spans more than one implementation step
- the task needs executor and reviewer separation
- the task touches release-sensitive or manual-check-heavy flows
- the task touches both platform and client lanes
- the task should be resumable from a wave folder rather than from chat memory

Ad hoc direct work is still acceptable for very small, low-risk edits.

## Request-To-WO Flow

The orchestrator may create a `WO` draft directly from the user request.

This is the preferred starting point when it helps the session move quickly without inventing false certainty.

Default rule:

- create the `WO` draft from the request
- fill what is already grounded by the request and current repo truth
- mark uncertain fields as `candidate`, `unknown`, `needs discovery`, or `blocked by evidence`
- run discovery and strategy only for the parts that still need grounding

## Autofill Modes

### Fast

Use when the request is narrow, the write scope is obvious, and the canonical repo lane is easy to classify.

Expected flow:

1. request
2. `WO` draft
3. executor
4. review loop

### Balanced

Use by default.

Expected flow:

1. request
2. `WO` draft
3. short scout pass for unclear fields
4. `WO` update
5. executor
6. review loop

### Strict

Use when the work is mixed-lane, release-sensitive, contract-sensitive, or still ambiguous after the first read.

Expected flow:

1. request
2. scout discovery
3. implementation strategy
4. `WO` create or update
5. executor
6. review loop

## Autofill Policy

Fields that the orchestrator may autofill directly from the user request:

- wave name and `WO` title
- first-draft `Goal`
- first-draft `Why This WO Exists`
- candidate `WO class`
- candidate `write scope`
- likely code anchors and docs anchors
- likely docs impact
- first-draft acceptance criteria
- validation seeds by subsystem

Fields that must stay provisional until discovery, review, or real execution evidence exists:

- final `write scope`
- final `Non-Goals`
- execution worktree selection
- promotion target per affected repo lane
- reviewer verdicts
- manual-check results
- deploy status
- git evidence
- completion evidence
- release-safe conclusions
- Android localhost audit results
- `current-origin`, `brain-origin`, and `RU-origin` evidence

## Core Artifacts

- `Wave`
  a dated folder that groups related work orders
- `INDEX.md`
  the living control sheet for the wave
- `WO`
  one work-order file for one bounded execution target
- discovery memo
  read-only context gathering for a WO
- implementation strategy
  WO-ready execution approach before coding
- review verdict
  the reviewer output for spec, quality, or release validation
- completion evidence
  the closure record for what changed, how it was verified, and what remains blocked

## Role Map

- `Orchestrator`
  owns routing, WO status, reviewer launch order, docs impact, and completion judgment
- `Scout discovery`
  gathers must-read anchors, docs impact, risks, and validation plan without editing
- `Implementation strategy`
  turns discovery into a WO-ready plan with acceptance and validation rules
- `Executor`
  performs the scoped implementation
- `Spec reviewer`
  checks conformance to the WO contract
- `Quality reviewer`
  checks implementation quality after spec compliance is green
- `Release validator`
  checks release-sensitive evidence when the WO affects gates, deploy flow, runtime safety, or operator visibility

## Non-Negotiables

- Read the must-read set from `AGENTS.md` before substantial work.
- Route by `write-scope`, not by topic or by which surface looks most visible.
- `portal/master` is the policy label for the platform repo and maps to promotion into `origin/master`.
- `portal/master` is canonical for `portal_bot/`, `webapp/`, `marketing/`, `shared/`, `infra/`, root `docs/`, and root `scripts/`.
- `POKROV-app/main` is canonical for new client development work once that dedicated repo is bootstrapped locally.
- retained bridge artifacts and retired bootstrap notes are archive evidence only, not active completion lanes.
- root docs land on `portal/master`. New client docs land on `POKROV-app/main` once bootstrapped; short archive summaries live under `docs/archive/client-lanes/`.
- The root platform checkout on `master` is the clean baseline prospectively, not the preferred place for active concurrent execution.
- Active execution should prefer explicit `codex/*` branches in dedicated worktrees so orchestrated tasks do not trample each other.
- machine-local branch names such as `main` and `portal-app` are aliases or convenience lanes only. They are never authoritative roots by themselves.
- retired `app-next` material is bootstrap provenance only; it is never a canonical completion target.
- Production truth stays in Postgres plus the locked shared facts under `shared/`.
- A green automated check does not close a WO if manual checks, release blockers, or missing docs updates remain open.
- The executor never self-closes the WO.
- Reviewers run with fresh context and report findings back through the orchestrator.
- If behavior changes, the required canonical docs must be updated in the same task.
- Never treat local temp DBs, generated caches, archived notes, or local artifact folders as product truth.

## Work-Order Classes

### Platform-only

Use when all edits stay under the platform lane:

- `portal_bot/`
- `webapp/`
- `marketing/`
- `shared/`
- `infra/`
- `scripts/`
- `AGENTS.md`
- `docs/*`

### Client-only

Use when all edits stay under one client lane:

- `C:/Users/kiwun/Documents/ai/POKROV-app/**` for new client development truth
- `docs/archive/client-lanes/**` only when a WO updates short archive summaries or provenance notes
- retained bridge-bundle evidence under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/**` only when a WO explicitly handles rollback or handoff archives

### Mixed

Use when the WO touches both canonical lanes.

Typical mixed cases:

- shared facts changed and the client must sync or adopt them
- app-first or release contract changes need both root docs and client docs/code
- release or publishing flow changes need root operations docs plus client packaging or runtime work, and may also require explicit bridge-lane evidence

Mixed-lane execution rule:

- one `WO` may cover both lanes when the product contract truly spans both
- write scope must still be split explicitly into platform paths and client paths
- orchestrators should prefer separate execution worktrees per lane when parallelism or review clarity matters
- mixed status does not let platform work land in client aliases or client work land in platform aliases

## Branch Labels And Worktrees

Branch and worktree policy for orchestrated execution:

- treat `portal/master` as the policy name for the platform lane that ultimately promotes to `origin/master`
- treat `POKROV-app/main` as the policy name for the new client development lane
- keep the root platform checkout on `master` clean enough to serve as a known-good baseline for new worktrees
- do not treat the root checkout as the default executor sandbox when concurrent work is active
- prefer dedicated worktrees on explicit `codex/*` branches for execution, fix cycles, and review reproduction
- record which worktree and branch carried each lane of work when a `WO` is mixed or when multiple executors run in parallel
- machine-local names such as `main`, `portal-app`, and `app-next` may exist on one workstation for convenience, but they do not redefine lane ownership or promotion targets
- retired bootstrap material may hold provenance notes, but it is not a client completion target once `POKROV-app` exists
- record retained bridge evidence explicitly as archive evidence instead of inventing a live bridge lane

## Routing Policy

The orchestrator must classify every WO before execution:

1. identify exact write paths
2. assign `platform-only`, `client-only`, or `mixed`
3. bind the WO to the correct canonical promotion target for each affected lane
4. bind the WO to the required docs impact
5. choose the execution worktree strategy when parallel work or mixed lanes are involved
6. bind the WO to the required validation and manual checks

If write scope changes mid-task, the orchestrator must reclassify the WO instead of silently stretching it.

Routing guardrails:

- if the write scope stays in root `docs/`, `portal_bot/`, `webapp/`, `marketing/`, `shared/`, `infra/`, or root `scripts/`, route to the platform lane even if a machine-local branch is named `main`
- if the write scope stays under `C:/Users/kiwun/Documents/ai/POKROV-app/`, route to the new client lane
- if the write scope stays under retired bridge material, escalate and decide whether the task is archive maintenance, rollback forensics, or an explicit exception; do not route it as a normal client lane
- if the write scope references retired bootstrap material, decide whether it is historical evidence for platform docs or for the active `POKROV-app` lane; do not route it as an independent client truth
- if multiple lanes change, require separate lane evidence and promotion notes instead of assuming one branch transitively updates the others

## WO Lifecycle

Recommended wave statuses:

- `draft`
- `ready`
- `active`
- `blocked`
- `partial`
- `closed`

Recommended WO statuses:

- `draft`
- `ready`
- `executing`
- `spec-review`
- `quality-review`
- `fix-cycle`
- `blocked`
- `partial`
- `complete`

Status ownership:

- only the orchestrator changes the top-level WO status
- executors and reviewers append evidence, findings, and fix-cycle notes
- a WO may stay `partial` when code is correct but release blockers or manual checks still remain

## Review Loop

Standard sequence:

1. orchestrator creates or updates the `WO` from the request, discovery, or strategy output
2. orchestrator confirms WO class, write scope, docs impact, and acceptance criteria
3. executor performs the scoped work
4. spec reviewer checks compliance with the WO contract
5. quality reviewer checks implementation quality after spec compliance is green
6. release validator runs when the WO is release-sensitive
7. orchestrator either closes the WO or routes findings back to the executor

Fix-cycle rule:

- findings should be transferred back to the executor `1:1`
- the same executor may be resumed for fixes
- reviewers should stay fresh for each verdict pass

## Evidence Policy

Every WO must retain enough evidence to answer:

- what changed
- why it changed
- what was validated
- what still depends on manual or external confirmation
- which repo lane carries the git truth

Minimum evidence areas:

- code anchors and docs anchors that were read
- automated checks with exact commands and outcomes
- manual checks with environment or origin labels
- artifact paths under `docs/audit-artifacts/` when relevant
- worktree and branch used for execution when relevant
- git evidence per repo lane, including the intended promotion target
- residual risk or blocker notes

Evidence handling rule:

- keep execution evidence tied to the lane that actually changed
- do not treat a machine-local alias branch name as sufficient git evidence without stating which canonical lane it promotes into
- for mixed WOs, preserve separate evidence for platform promotion, new-client promotion, and bridge-lane promotion when each lane changed
- store durable release or audit artifacts under canonical evidence locations, not inside throwaway worktree-only paths

## Completion Rules

A WO is `complete` only when all of these are true:

- implementation matches the WO goal and acceptance criteria
- required canonical docs are updated or explicitly confirmed unchanged
- required automated checks passed, or failures are resolved
- required manual checks are complete, or the WO is explicitly not gated by them
- git evidence is recorded for every affected canonical repo lane and identifies the intended promotion path
- no unresolved reviewer findings remain

A WO stays `partial` or `blocked` when:

- Android public-release safety still depends on a physical-device localhost audit
- deploy did not happen yet
- root docs and client docs are not yet both aligned for a mixed WO
- execution happened in a convenience branch or worktree but promotion to the canonical lane is still unproven
- mixed-lane work has not preserved separate promotion evidence for platform, new-client, and bridge lanes
- current-origin, brain-origin, or RU-origin evidence is still missing for an infra-sensitive change

Promotion rule:

- executors may work from `codex/*` branches in dedicated worktrees
- orchestrators close the `WO` against promotion into the canonical lane, not merely against a local alias or an unmerged worktree branch
- promotion for platform-scope work means `portal/master` policy alignment on `origin/master`
- promotion for new-client work means `POKROV-app/main`
- promotion for bridge work means the legacy bridge repo on its current `main` line
- retired bootstrap or bridge archives do not satisfy canonical client-lane completion by themselves

## Reporting Format

Final handoff for substantial work should preserve the project reporting style from `AGENTS.md`:

- `What I checked`
- `What I found`
- `What I changed`
- `How I verified`
- `What remains / risk`

For node-access or origin-sensitive work, also include:

- `current-origin check`
- `brain-origin check`
- `RU-origin check`

## Storage Rules

- prompt contracts and templates live under `docs/developer/orchestration/`
- live execution artifacts live under `docs/developer/work-orders/`
- historical flat logs under `docs/archive/flat-docs/` remain historical unless relinked as current by canonical docs

## Minimal Launch Sequence

1. open the must-read docs from `AGENTS.md`
2. create or resume a wave folder
3. create or update the `INDEX.md`
4. create or update the `WO` draft from the user request
5. mark uncertain fields as provisional instead of pretending they are settled
6. run discovery and strategy only where grounding is still missing
7. launch executor
8. run review loop
9. record completion evidence
10. close the WO only after evidence is sufficient

# Implementation Strategy - <topic-or-wo>

> Strategy artifact that turns discovery into an executable work order.
> This document is not completion evidence.
> The orchestrator uses it to fill or update the WO sections for design, acceptance, validation, and review focus.

## Strategy Snapshot

| Field | Value |
| --- | --- |
| Topic | `<short title>` |
| Based on scout discovery | `<path or identifier>` |
| Candidate WO id | `<WO-xxx or blank>` |
| Strategy owner | `<role or name>` |
| Status | `draft | recommended | approved | superseded` |
| Candidate WO class | `platform-only | client-only | mixed` |
| Primary repo lane | `portal/master | POKROV-app/main | archive evidence only` |
| Secondary repo lane | `<blank if not mixed>` |
| Timestamp | `<timestamp>` |

## Problem Framing

### Goal

`<one sentence outcome>`

### Why this work exists

`<what problem, regression, or wave dependency this solves>`

### Non-goals

- `<explicit non-goal>`
- `<explicit non-goal>`

## Recommended Approach

### Chosen approach

`<short explanation of the preferred solution>`

### Why this approach

- `<why it best matches current repo truth>`
- `<why it keeps scope contained>`
- `<why it fits current validation and release expectations>`

### Rejected or deferred alternatives

| Option | Why not now |
| --- | --- |
| `<alternative>` | `<tradeoff or reason rejected>` |
| `<alternative>` | `<tradeoff or reason rejected>` |

## Freedom And Guardrails

### Allowed freedom inside the WO

- `<supporting tests, helper code, or small refactors allowed inside write scope>`
- `<doc updates allowed only in canonical docs actually impacted>`
- `<regen or sync output allowed if explicitly required by the approach>`

### Guardrails

- `<must not widen product behavior beyond current truth>`
- `<must not bypass canonical repo lanes>`
- `<must not claim completion without the required evidence>`

## Required Design

### Design summary

`<describe the target implementation shape>`

### Files or surfaces expected to change

- `<exact path or subsystem>`
- `<exact path or subsystem>`

### Contracts or behaviors that must remain stable

- `<existing behavior that cannot regress>`
- `<compatibility seam or public truth that must stay intact>`

### Docs and truth alignment

- `<which canonical docs must be updated or explicitly left alone>`
- `<if mixed, which root docs and which POKROV-app docs must stay in sync, plus whether any archive evidence notes are still required>`

### Mixed-lane execution order

- `<leave blank if not mixed>`
- `<if mixed, what lands in platform first and what follows in client>`

### Rollback or safe-stop point

`<how to stop safely if the WO only lands partially>`

## Execution Slices

Keep slices small enough that an executor and reviewers can reason about them cleanly.

| Slice | Output | Owner role | Depends on | Validation hook |
| --- | --- | --- | --- | --- |
| `1` | `<small deliverable>` | `executor` | `-` | `<test, smoke, or artifact>` |
| `2` | `<small deliverable>` | `executor` | `1` | `<test, smoke, or artifact>` |
| `3` | `<docs or release alignment>` | `executor` | `1, 2` | `<artifact or review>` |

## Acceptance Criteria Draft

- [ ] `<criterion that can be checked by a reviewer>`
- [ ] `<criterion that proves the design actually landed>`
- [ ] `<criterion that covers docs or evidence>`
- [ ] `<criterion that covers validation>`

## Validation Plan

Copy only the surfaces that apply to the WO.

| Surface | Planned validation | Evidence expected |
| --- | --- | --- |
| `backend` | `<pytest, smoke, deploy verify>` | `<command output or artifact path>` |
| `webapp` | `<build, admin smoke, Playwright>` | `<command output or artifact path>` |
| `marketing` | `<build, links, visual smoke>` | `<command output or artifact path>` |
| `infra` | `<node readiness, metrics, origin matrix>` | `<artifact path or summary>` |
| `client` | `<security smoke, release gate suite, localhost audit>` | `<artifact path or summary>` |
| `release` | `<gate pack, deploy verify, handoff sync>` | `<artifact path or summary>` |

## Reviewer Focus

### Spec reviewer should verify

- `<scope stayed inside the WO>`
- `<design and acceptance criteria were actually met>`

### Quality reviewer should verify

- `<implementation quality, tests, maintainability, regressions>`
- `<docs and code remain aligned>`

### Release validator should verify

- `<release-sensitive truth, blockers, deploy evidence, rollback-safe state>`

## Partial-Success And Exit Rules

- Valid partial outcome: `<what can be accepted without full closure>`
- What still blocks full completion: `<remaining requirements>`
- Stop conditions: `<what should pause the WO instead of forcing risky completion>`

## Historical Reference Rule

- retired bootstrap or bridge material may be cited only when provenance or rollback evidence matters
- do not use archived material as the active completion lane for a new strategy

## Open Questions And Risks

- `<open question>`
- `<risk>`

## WO Sections To Fill From This Strategy

- Goal
- Why This WO Exists
- Non-Goals
- Write Scope
- WO Class And Routing Decision
- Execution Freedom
- Required Design
- Acceptance Criteria
- Validation
- Reviewer Findings focus

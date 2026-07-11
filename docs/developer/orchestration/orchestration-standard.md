# POKROV Orchestration Standard

Last updated: 2026-07-11

This document is the process owner for Codex orchestration in the platform workspace. Use it to control risk while keeping direct work light.

## Ceremony Selection

Choose by risk and continuity needs, not task size alone.

| Ceremony | Trigger | Required artifacts |
| --- | --- | --- |
| `direct` | small, low-risk, single-pass work | focused validation and handoff |
| `bounded_wo` | durable context, independent review, multiple bounded steps, or meaningful risk | compact WO; selected roles; conditional `FLOW_STATE` |
| `release_wo` | release, deploy, payment, security, persistence, provider, device, or origin-sensitive work | full triggered proof blocks, release validator, candidate-specific evidence |

`direct` work has no WO or `FLOW_STATE` requirement. Escalate it before execution if scope discovery exposes a WO trigger. A WO may use only the roles and optional proof blocks required by its risk.

## Routing And Collision Gate

Route work by exact write scope and repository lane. Use the root [task router](../agent-context-map.md) for lane ownership, authority anchors, focused checks, and documentation impact. Do not copy global product facts, branch policy, or subsystem read packs into a WO or role.

Before execution:

1. declare exact write and no-touch paths;
2. inspect current status and diffs in every relevant worktree;
3. compare dirty paths with the declared write scope;
4. stop on an overlap until ownership, integration order, or a non-overlapping slice is explicit;
5. record the selected lane and intended promotion state in the WO when one exists.

Run the collision gate again whenever write scope changes. Reclassify the ceremony, roles, proof blocks, documentation impact, and validation when new scope changes risk. Never stretch a WO silently.

## Lifecycle Vocabulary

WO status: draft | ready | active | review | fix_cycle | blocked | partial | complete

Review verdict: pass | changes_required | blocked

Finding status: open | fixed | accepted_risk | blocked

Only the orchestrator changes WO status. Executors report implementation and evidence. Reviewers return a verdict and findings. `partial` means the bounded result is useful but an accepted requirement, integration step, manual gate, or access-dependent proof remains open. `blocked` names the blocking condition and next action.

A completed WO is immutable execution evidence. Corrections use a dated addendum or a superseding WO; neither silently rewrites the original record into current product truth.

## Work-Order Contract

The compact WO is the default for both WO ceremonies. It records:

- metadata;
- goal and non-goals;
- exact write and no-touch scope;
- authority anchors;
- acceptance oracle;
- documentation impact;
- validation and structured evidence;
- status and handoff.

The [WO authoring guide](wo-authoring-guide.md) owns conditional proof blocks. Trigger every applicable block for `release_wo`; do not add empty boilerplate. If no trustworthy acceptance oracle exists, route discovery or strategy and keep the WO `draft`, `partial`, or `blocked` as appropriate.

## Role Selection

The orchestrator owns ceremony selection, collision checks, role routing, status, integration, and closure. Select roles independently:

- scout discovery for read-only anchors, conflicts, scope, docs impact, and validation seeds;
- implementation strategy when the approach, invariants, oracle, risks, or slices are complex or unclear;
- executor for bounded writes and evidence capture;
- spec reviewer for contract compliance;
- quality reviewer for correctness, maintainability, security, performance, usability, and evidence quality;
- release validator for exact-candidate gates, origins, manual blockers, rollback, and public claims.

There is no mandatory launch chain. An executor never self-closes a WO. A reviewer does not take implementation ownership through a verdict.

## Review Interface

Every reviewer uses the same interface:

- `verdict`: one review verdict value;
- `finding`: `id`, `issue_class`, `severity`, `reference`, `required_change`, and finding `status`;
- `evidence`: the evidence dimensions below;
- `next_action`: the smallest safe routing step.

For `changes_required`, route each finding to an owner. The filing reviewer rechecks only owned findings after a fix. Use a fresh final review when the selected ceremony, risk, or accumulated changes require an independent whole-result pass.

Create `FLOW_STATE` only for a trigger defined in [flow-state.md](flow-state.md). The third same-class finding without a mechanism change stops ordinary fix routing and requires problem-class analysis.

## Evidence Dimensions

Each evidence record contains exactly these dimensions:

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

source: static_review | synthetic_test | tracked_fixture | generated_artifact | api_e2e | ui_behavior | runtime_smoke | full_validation_epoch | manual | n/a

target_scope: local | exact_candidate | deployed_environment | provider | physical_device | current_origin | brain_origin | ru_origin

freshness: current_candidate | current_environment | retained_current | historical_stale

attribution: wo_owned | wave_integration | pre_existing | unrelated | blocked_by_access

`result` records the observed outcome without widening its claim. `reference` points to a reproducible command summary or retained artifact. `notes` state limitations, candidate identity, environment, or why a dimension is `n/a`.

For manual evidence, `MANUAL_OWNER_TEST`, `OPERATOR_ATTESTED`, `SKIPPED_BY_OWNER`, `SKIPPED_BY_OPERATOR`, `NOT_REQUESTED`, and `BLOCKED_BY_ACCESS` are allowed values of the existing `result` field. They are not a ninth field, and none becomes `PASS` by inference.

Evidence rules:

- bind every result to its actual target scope and freshness;
- distinguish WO-owned results from integration, pre-existing, unrelated, and access-blocked results;
- keep current, retained, and historical evidence distinct;
- preserve exact-candidate, deployed-environment, provider, device, and named-origin boundaries;
- do not use a narrow textual or local check to close a broader semantic or runtime oracle;
- redact secrets, credentials, customer data, private routing material, and raw provider payloads.

## Execution And Scope Change

Before writing, the executor confirms the current WO status, write/no-touch scope, authority anchors, acceptance oracle, documentation impact, and assigned validation. During execution the executor:

- changes only bounded paths;
- preserves concurrent work and repository-lane boundaries;
- updates canonical docs when behavior changes;
- captures evidence using the structured record;
- stops when the write scope, authority, risk, or required access changes.

The orchestrator reruns the collision gate and updates the contract before execution resumes.

## Validation And Attribution

Use the smallest focused checks that prove the acceptance oracle, then the regression contour justified by risk. Record commands and outcomes without claiming unrun checks.

Validation that spans several WOs or a later integration step uses `wave_integration`. A failure present before the WO uses `pre_existing`; an unrelated failure uses `unrelated`. A required check that cannot run because access is unavailable uses `blocked_by_access` and an appropriate manual label.

Release-sensitive work requires evidence for the exact candidate and environment. Keep `current_origin`, `brain_origin`, and `ru_origin` distinct. Manual device, account, provider, signing, store, deploy, and external-origin gates remain manual until executed and retained.

## Closure

The orchestrator may set `complete` only when:

- the result satisfies the goal and acceptance oracle;
- write scope and documentation impact are closed;
- required validation and evidence records are present;
- no finding remains `open` or `blocked`;
- accepted risks name their owner and consequence;
- conditional proof blocks and `FLOW_STATE` are resolved;
- lane and promotion state are explicit;
- the handoff states what changed, exact checks and results, remaining manual or blocked work, and commit/deploy state.

Use `partial` or `blocked` instead of weakening the oracle or manufacturing release evidence.

## Storage Boundary

Process contracts and templates live in this directory. Active and retained WO artifacts live under [work-orders](../work-orders/README.md). Canonical product, architecture, operations, design, and active client owners remain outside WO storage. Completed WOs explain execution history; they never decide what should happen now.

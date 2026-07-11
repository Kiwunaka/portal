# WO

## Metadata

| Field | Value |
| --- | --- |
| WO id | `WO-XXX-short-title` |
| Title | `<bounded outcome>` |
| Ceremony | `bounded_wo | release_wo` |
| WO status | `draft | ready | active | review | fix_cycle | blocked | partial | complete` |
| Orchestrator | `<owner>` |
| Repository lane | `platform | active_client | mixed` |
| Working branch or worktree | `<exact reference>` |
| Intended promotion state | `<target and owner>` |
| Created / updated | `<timestamps>` |

Only the orchestrator changes WO status.

## Goal

`<one observable outcome>`

## Non-Goals

- `<explicit exclusion>`
- `<explicit exclusion>`

## Write Scope

- `<exact file or directory>`
- `<exact file or directory>`

Collision gate result: `<worktrees checked, overlap result, timestamp>`

## No-Touch Scope

- `<exact path, repository lane, data class, or concurrent owner>`
- `<forbidden mutation or external action>`

## Authority Anchors

| Anchor | Why authoritative for this outcome |
| --- | --- |
| `<selected task-router row>` | `<routing, checks, docs impact>` |
| `<canonical owner>` | `<intended behavior>` |
| `<current code or test>` | `<implemented behavior>` |
| `<exact runtime evidence, if required>` | `<observed state and candidate>` |

Use targeted history only to explain provenance. It cannot decide current action.

## Acceptance Oracle

- Authoritative boundary: `<system, artifact, UI, API, device, provider, or text contract>`
- Success observation: `<what must be observed>`
- Negative cases: `<what must remain false or be rejected>`
- Proof mechanism: `<test, review, smoke, artifact inspection, or manual gate>`
- Limitations: `<what this oracle does not prove>`
- Triggered proof blocks: `<links or n/a; follow the WO authoring guide>`

If no trustworthy oracle exists, keep the WO `draft`, `partial`, or `blocked` as required by the orchestration standard.

## Docs Impact

| Canonical owner | Required change | Closure evidence |
| --- | --- | --- |
| `<exact doc path>` | `<change or confirmed no change>` | `<diff or rationale>` |

Do not use a fixed document checklist. Select owners through the assigned router row and current evidence.

## Validation And Evidence

| Check | Command or manual gate | Oracle reached | Required target scope |
| --- | --- | --- | --- |
| `<focused check>` | `<exact command or owner action>` | `<yes, no, or limitation>` | `<scope>` |

Record one evidence object per check:

- name: `<stable check name>`
- source: `static_review | synthetic_test | tracked_fixture | generated_artifact | api_e2e | ui_behavior | runtime_smoke | full_validation_epoch | manual | n/a`
- target_scope: `local | exact_candidate | deployed_environment | provider | physical_device | current_origin | brain_origin | ru_origin`
- freshness: `current_candidate | current_environment | retained_current | historical_stale`
- attribution: `wo_owned | wave_integration | pre_existing | unrelated | blocked_by_access`
- result: `<observed result or truthful manual label>`
- reference: `<reproducible summary or retained artifact>`
- notes: `<candidate, environment, limitations, or n/a reason>`

Manual result labels: `MANUAL_OWNER_TEST | OPERATOR_ATTESTED | SKIPPED_BY_OWNER | SKIPPED_BY_OPERATOR | NOT_REQUESTED | BLOCKED_BY_ACCESS`.

## Status And Handoff

- Current WO status: `<normalized status>`
- Result delivered: `<what is now true>`
- Open findings: `<ids and owners, or none>`
- Blockers and accepted risks: `<owner, consequence, next condition>`
- Conditional `FLOW_STATE` v2: `<reference or not triggered>`
- Lane and commit state: `<branch, commits, staging, push, integration>`
- Deploy and promotion state: `<performed, not requested, blocked, or pending>`
- Next action: `<smallest safe routing step>`

An executor supplies implementation evidence but never closes this WO.

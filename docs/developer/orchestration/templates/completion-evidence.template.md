# Completion Evidence

WO: `WO-XXX-short-title`
Prepared by: `<orchestrator>`
Date: `<timestamp>`

Use this artifact for the orchestrator's closure or truthful partial handoff. It does not replace canonical product or release owners.

## Outcome

- Goal result: `<observable outcome>`
- Final WO status: `complete | partial | blocked`
- Docs impact: `<owners updated or confirmed unchanged>`
- Remaining scope: `<none, explicit remainder, or blocker>`

## Changes

- `<path or behavior changed>`
- `<path or behavior changed>`

## Evidence Records

Repeat one record per check:

- name: `<stable check name>`
- source: `static_review | synthetic_test | tracked_fixture | generated_artifact | api_e2e | ui_behavior | runtime_smoke | full_validation_epoch | manual | n/a`
- target_scope: `local | exact_candidate | deployed_environment | provider | physical_device | current_origin | brain_origin | ru_origin`
- freshness: `current_candidate | current_environment | retained_current | historical_stale`
- attribution: `wo_owned | wave_integration | pre_existing | unrelated | blocked_by_access`
- result: `<observed result or truthful manual label>`
- reference: `<command summary or retained artifact>`
- notes: `<limitations, candidate, environment, or n/a reason>`

## Review And Flow

- Review verdict references: `<spec, quality, release, or not selected>`
- Open findings: `<none or ids with status and owner>`
- Accepted risks: `<none or owner and consequence>`
- Final `FLOW_STATE` v2 reference: `<reference or not triggered>`
- Next action: `execute | owned_finding_recheck | fresh_final_review | release_validation | problem_class_analysis | wait_for_access | close`

Use `close` only when no finding or stop reason still requires action.

## Git And Promotion

| Repository lane | Working branch | Commit | Push state | Integration or promotion state |
| --- | --- | --- | --- | --- |
| `<platform or active_client>` | `<branch>` | `<sha>` | `<state>` | `<state and owner>` |

Deploy state: `<performed, not requested, blocked, or pending>`

## Release Boundary

Complete this section only when release-facing work triggered it.

- Exact candidate: `<commit, artifact, manifest, version, environment>`
- Current gates: `<gate references and results>`
- Manual gates: `<MANUAL_OWNER_TEST, OPERATOR_ATTESTED, SKIPPED_BY_OWNER, SKIPPED_BY_OPERATOR, NOT_REQUESTED, or BLOCKED_BY_ACCESS>`
- Origin evidence: `<current_origin, brain_origin, ru_origin kept separate>`
- Rollback-safe state: `<verified condition and reference>`
- Public claims allowed: `<claims directly supported by current evidence>`
- Public claims forbidden: `<claims not supported by current evidence>`

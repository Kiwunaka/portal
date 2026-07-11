# Wave Index

The orchestrator owns this routing index. Keep implementation, review, and detailed evidence inside each WO or retained artifact.

## Wave Scope

| Field | Value |
| --- | --- |
| Wave id | `<YYYY-MM-DD--wave-name>` |
| Outcome | `<one bounded wave outcome>` |
| Orchestrator | `<owner>` |
| Repository lanes | `<platform, active_client, or mixed>` |
| Primary scope roots | `<exact paths>` |
| Intended promotion state | `<target and owner>` |
| Current summary | `<active work, blockers, or closure state>` |
| Last updated | `<timestamp>` |

## Collision And Routing State

- Collision gate reference: `<worktrees, scopes, result, timestamp>`
- Concurrent no-touch owners: `<paths and owners>`
- Integration order: `<dependencies and owner>`
- Scope changes awaiting a new gate: `<none or exact change>`

## Ordered WO Queue

WO status: `draft | ready | active | review | fix_cycle | blocked | partial | complete`.

| Order | WO | Goal | Write scope | Depends on | Selected roles | Status | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `1` | `WO-001` | `<goal>` | `<paths>` | `<none>` | `<roles>` | `ready` | `<action>` |
| `2` | `WO-002` | `<goal>` | `<paths>` | `WO-001` | `<roles>` | `draft` | `<action>` |

Do not run two executors against overlapping write scope. Select scout, strategy, spec, quality, and release roles independently by risk.

## Dependencies And Integration

| Dependency or seam | Owner | Entry condition | Exit evidence | State |
| --- | --- | --- | --- | --- |
| `<WO, lane, contract, or external gate>` | `<owner>` | `<condition>` | `<reference>` | `<state>` |

Keep platform and active-client commits, validation, and promotion evidence separate until integration proves the combined result.

## Review And Flow Routing

| WO | Review role | Verdict reference | Open finding owners | FLOW_STATE v2 reference | Routed action |
| --- | --- | --- | --- | --- | --- |
| `WO-001` | `<selected role>` | `<artifact or pending>` | `<ids or none>` | `<reference or not triggered>` | `<allowed action>` |

At the same-class stop threshold, route problem-class analysis instead of another ordinary fix pass.

## Wave Validation

| Check | Attribution | Target scope | Evidence reference | Result |
| --- | --- | --- | --- | --- |
| `<integration or release check>` | `wave_integration` | `<scope>` | `<reference>` | `<observed result>` |

Do not hide WO-owned, pre-existing, unrelated, or access-blocked failures in a wave summary.

## Closure And Handoff

- Completed WOs: `<ids and outcomes>`
- Partial or blocked WOs: `<ids, remainder, owner, next condition>`
- Canonical docs updated: `<paths or confirmed no change>`
- Integration evidence: `<references>`
- Repository commits and promotion state: `<per lane>`
- Manual gates and accepted risks: `<owner and consequence>`
- Next wave seed: `<none or bounded follow-up>`

A closed or superseded index is evidence. Do not rewrite it into current product truth.

# Implementation Strategy

This is an optional artifact. Create it only when the approach, invariants, oracle, risks, or execution slices are complex or unclear.

WO: `WO-XXX-short-title`
Strategy owner: `<owner>`
Date: `<timestamp>`

## Why Strategy Is Needed

- Unclear or complex point: `<decision that cannot be left to improvisation>`
- Assigned router row: `<row>`
- Subsystem authority anchors: `<targeted paths>`
- Scout evidence: `<reference or not used>`

## Recommended Approach

`<smallest viable approach and why it reaches the goal>`

Rejected alternatives that affect risk:

| Alternative | Tradeoff or rejection reason |
| --- | --- |
| `<option>` | `<reason>` |

## Invariants

- `<behavior, contract, data, or compatibility property that must remain true>`
- `<repository-lane or release boundary that must remain true>`

## Acceptance Oracle

- Authoritative boundary: `<where correctness is decided>`
- Success observation: `<what proves the result>`
- Negative cases: `<what must remain false>`
- Proof mechanism: `<why the check reaches the boundary>`
- Blind spots: `<residual uncertainty>`

## Risks And Safe Stop

| Risk | Control | Evidence | Safe-stop or rollback point |
| --- | --- | --- | --- |
| `<risk>` | `<mechanism>` | `<required proof>` | `<condition>` |

## Execution Slices

| Slice | Bounded output | Depends on | Validation hook |
| --- | --- | --- | --- |
| `1` | `<output>` | `<none or dependency>` | `<check>` |
| `2` | `<output>` | `<dependency>` | `<check>` |

Each slice must stay inside the WO write scope. A changed scope returns to the orchestrator for a new collision gate.

## Docs And Lane Impact

- Canonical docs affected: `<exact owners or none>`
- Repository lanes: `<platform, active_client, or mixed>`
- Integration order: `<order and owner>`
- Promotion evidence required: `<state>`

## Handoff

- WO changes required: `<oracle, scope, proof blocks, validation, or none>`
- Questions still open: `<none or blocking questions>`
- Recommendation: `<ready for execution, split, rescope, or blocked>`

The orchestrator decides whether to adopt this strategy and whether the WO can advance.

# WO-013AM — Exact candidate.3 Gate D decision

Status: `LOCALLY_PROVED_EXACT_CANDIDATE_RUNTIME_BLOCKED_I3`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `05`, decision replay in Phase `11`
Row: `REL_GATE/GATE-D`
Candidate: `pokrov-1.2.0-candidate.3`
Production/external mutation: `NONE`

## Outcome

Evaluate Gate D against the frozen candidate platform source. Payment bounded
context, shared HTTP ownership, bounded DB execution, transactional outbox and
router/service ownership all pass the exact source matrix. The live Brain
payload also matches all 193 candidate source files, proving that the deployed
code is not stale.

This does not prove production behavior. No real provider order/callback,
PostgreSQL lock/load observation, outbox worker delivery/retry/dead-letter,
reconciliation, reversal or operator Action Intent rollback was executed.
Gate D therefore returns `BLOCKED` with no new candidate defect and remains at
local `I3`.

## Exact candidate result

| Requirement | Result | Exact boundary |
|---|---|---|
| Payment bounded context | `PASS_EXACT_CANDIDATE_SOURCE` | Immutable local order, strict provider response handling, signature/freshness/identity validation, replay-safe fulfillment/reversal and the `oa=0` regression all pass. |
| Shared HTTP clients | `PASS_EXACT_CANDIDATE_SOURCE` | Lifespan-owned provider sessions, bounded timeout/pool/JSON policies and secret-free telemetry pass. |
| DB transaction strategy | `PASS_EXACT_CANDIDATE_SOURCE` | Payment use cases own sessions inside bounded worker threads; no ORM state crosses awaits; concurrency and rollback tests pass. |
| Transactional outbox | `PASS_EXACT_CANDIDATE_SOURCE` | Same-transaction enqueue, unique idempotency, claim/retry/stale recovery/dead-letter and replay convergence pass. |
| Routers/services | `PASS_EXACT_CANDIDATE_SOURCE` | Payment, public/client, admin and Action Intent boundaries retain one process, route table, DB authority and policy registry. |

## Fresh exact-source verification

On detached platform source
`eafaca3e64c0619dea7f58fc9c430682b4520559`:

- payment/provider/callback/HTTP/DB/outbox/module matrix:
  `196 passed`, `12 subtests passed`, `20` existing deprecation warnings,
  zero skips/failures, `618.40 s`;
- Action Intent and policy/router ownership: `25/25 passed`, `95.74 s`.

The exact Brain source evidence still reports `193/193` normalized payload
matches and readiness `23/23`. That proves source identity only; it does not
turn local transaction fixtures into provider/PostgreSQL/outbox runtime proof.

## Decision boundary

Gate D is `BLOCKED`, not `FAIL`. No new source defect requires replacement
code. Candidate.3 remains overall `NO_GO` because Gate B already has one
explicit frozen-source failure. Gate D cannot reach `I4` until the production
provider, PostgreSQL, outbox/reconciliation and rollback matrix is retained.

No real payment is started merely to manufacture release evidence. Provider
credentials, callback signatures, order identity, amounts and customer data
remain outside committed artifacts and logs.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013AM-gate-d-test-evidence.json` | `1125a3fb29f6b4cccd673f9b9855ca5aac6c247d969207abf6a024e0d88dfe90` |
| `013AM-gate-d-decision.json` | `ca3ebfdabca3dc64a6cf1ac71fdcfa1591082b7a40d413c14a4ddbb85de83091` |

The decision does not authorize a provider action, deploy, publication or
Gate G.

## Ledger decision

`REL_GATE/GATE-D` remains `I3`; its status becomes
`LOCALLY_PROVED_EXACT_CANDIDATE_RUNTIME_BLOCKED`. Distribution remains
`I4=4`, `I3=312`, `I2=19`, `I1=41`, `I0=1`.

## Next action

Use an explicitly authorized minimal-value provider order in an isolated owned
test account, retain signed callback and duplicate replay, then inspect the
deployed PostgreSQL transaction/outbox/worker/reconciliation state through
redacted aggregates. Exercise reversal and rollback without changing unrelated
customers. Separately retain one production Action Intent prepare/execute/
status/rollback path. Until then Gate D stays below candidate proof.

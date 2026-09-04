# WO-013GI — candidate.32 current-authority ledger reconciliation

Status: `PASS_SEVEN_CURRENT_AUTHORITY_ROWS_RECONCILED; LEVELS_AND_GATE_F_UNCHANGED`

Observed: `2026-09-04T01:35:36Z`

Production/public mutation: `NONE`

## Outcome

Reconcile seven active execution-ledger rows whose status or blocker still
treated candidate.21 as the current release authority even though private
signed candidate.32, its exact source replay and Android static evidence now
exist.

The replacement is evidence-bounded:

- WO-013GF owns candidate.32 signed supply, receipt, exact source tuple,
  hosted-check results, non-elevated Windows boundary and initial Gate F;
- WO-013GG owns exact-source Gates A–E replay, the focused PB-14/rollback
  harness, isolated pointer rollback and current Gate F;
- WO-013GH owns exact Android static signing, bundle and direct/store
  separation.

No candidate.21 runtime, device or static-privacy result is relabelled as
candidate.32. Historical work orders remain immutable.

## Reconciled rows

| Row | Candidate.32 authority | Level | Remaining boundary |
|---|---|---|---|
| `REL/REPO-001` | Signed index/receipt and private six-file supply | `I3` unchanged | Public same-byte assets/readback and guarded runtime rollback |
| `OBS_DOD/DOD-23` | Signed index plus focused PB-14/rollback harness | `I3` unchanged | Physical install identity, live cohort/readback, runtime rollback and post-promotion health |
| `OBS_PB/PB-14` | Signed index plus focused PB-14/rollback harness | `I3` unchanged | Physical install identity and real incident/cohort path |
| `FE/P12-023` | Private signed trust surface | `I3` unchanged | Public assets/index readback and stable pointer |
| `FE_PR/PR-09` | Exact-source local quality `15/15` | `I3` unchanged | Physical/a11y/performance, authenticated journeys, origins and post-promotion proof |
| `FE_PR/PR-10` | Exact Gate F `BLOCKED 2/17/0` | `I3` unchanged | Seventeen explicit non-PASS rows |
| `FRKN_PLAN/W1-03` | Candidate-bound SBOM/provenance and signed supply | `I3` unchanged | Public same-byte mapping, notices and final promotion proof |

The ledger remains `378` unique rows with distribution `I4=7`, `I3=320`,
`I2=19`, `I1=32`, `I0=0`. There are zero index changes and Gate F is not
regenerated because this is authority reconciliation, not new runtime proof.

## Evidence boundaries

Candidate.32 source/local evidence now replaces candidate.21 only where the
newer evidence covers the same requirement. Rows whose strongest proof is
still candidate.21 device/runtime/static-privacy history are not included in
this slice. Their blockers must target candidate.32, but their historical
evidence cannot be silently promoted.

GitHub Billing-blocked zero-step checks remain `BLOCKED_BY_ACCESS`, not PASS.
The unsigned-Windows owner exception remains explicit. No public asset, Store
object, deploy, tag, stable pointer or promotion exists.

## Verification

```text
ledger rows -> 378
unique (plan,id) keys -> 378
duplicate keys -> 0
changed current-authority rows -> 7
index changes -> 0
distribution -> I4=7 / I3=320 / I2=19 / I1=32 / I0=0
Gate F -> BLOCKED 2/17/0; not regenerated
```

## Evidence

- normalized record:
  `evidence/013GI-candidate32-ledger-authority-reconciliation/013GI-candidate32-ledger-authority-reconciliation.json`;
- normalized record SHA-256:
  `75acb75d9b6b7b87463d7d74192e97171750f6e476b4cedebebcb4ccabc22965`.

The normalized record contains no credentials, private key, provider payload,
customer data or connection material.

## Follow-up

Review the remaining candidate.21 mentions separately. Refresh blockers to
candidate.32 where needed, but retain candidate.21 labels whenever the
underlying result is historical and no exact candidate.32 replacement exists.
Prioritize actual candidate.32 device/runtime evidence over further wording
changes once an isolated target becomes available.

# WO-013FF — candidate.24 Gate F origin refresh

Status: `EXACT_CANDIDATE24_GATE_F_BLOCKED_5_PASS_14_NON_PASS_0_FAIL`

Observed: `2026-09-03T01:20:00Z`

Production/public mutation: `NONE`

## Outcome

Regenerate exact candidate.24 Gate F after attaching WO-013FD current/Brain
origin evidence and WO-013FE source Gates A–E/local rollback evidence. The
verifier validates the immutable signed manifest, receipt, detached signature,
manifest-bound public keyring, exact four-source tuple, all upstream records
and all `19/19` check pointers.

```text
BLOCKED
required=19
pass=5
non_pass=14
fail=0
validation_errors=0
candidate_validation=PASS
gate_g_authorized=false
```

`current_origin` advances to `PASS` for the bounded public API budgets and
`brain_origin` advances to `PASS` for exact-source/readiness/subscription/
enabled-delivery readback. Signed supply, release-document binding and hosted
checks retain their three PASS rows.

The remaining rows stay explicit: Gates A–E and mandatory aggregate, runtime
rollback/kill, RU origin, physical Android, provider, Operator, legal and
comparable performance are `MANUAL_OWNER_TEST`; installed Windows, LDPlayer
and authenticated client egress are `NOT_RUN`; final live no-open-P0,
false-green and privacy attestation is `MISSING`; Windows trusted signing and
paid branch protection remain `SKIPPED_BY_OWNER`.

WO-013FE's isolated rollback passes but does not satisfy the guarded runtime
rollback row. Likewise current-public API and Brain service delivery do not
replace authenticated client egress or general RU-origin proof.

## Portable evidence binding

The fresh Windows checkout exposed that candidate.24 evidence directories were
missing explicit LF attributes, so a byte-valid historical hash could fail
after `core.autocrlf` checkout. `.gitattributes` now pins candidate.23/24 and
the new candidate.24 evidence JSON directories to `eol=lf`. Historical JSON
content is unchanged; this makes byte hashing deterministic across Windows and
hosted checkouts.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013FD-candidate24-current-brain-origin.json` | `fd68ea5c97747abe1302706a8a9d6cb338c28403ce5a13d9522fe98906561924` |
| `013FE-candidate24-source-gates-and-local-rollback.json` | `012718fea090ac596fae70f4147c6f93c77d7b94aa8ac050bdca9705eaa29599` |
| `013FF-candidate24-gate-f-evidence.json` | `1f04c60b28721dab59f26fdea6145e7d6bbc8b1f9f94a54dd87fe319ed29004c` |
| `013FF-candidate24-gate-f-input.json` | `e2d974d270f4ae9d16f738016e0737d2fe5a1a8fc1d4b9520817dfc52bb2de33` |
| `013FF-candidate24-gate-f-decision.json` | `53a735ad29be0b045f2c0ce18a76fafdff902581ac9709855f196d138db06aaf` |

`REL_GATE/GATE-F` remains `I3`; the 378-row level distribution is unchanged.
Gate G, tags, public assets, Store submission, stable pointer and production
promotion remain unauthorized.

# WO-013ET — candidate.21 exact Gate F blocked snapshot

Status: `EXACT_CANDIDATE21_GATE_F_BLOCKED_4_PASS_15_NON_PASS_0_FAIL`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `11`
Candidate: `pokrov-1.2.0-candidate.21`
Production/external mutation: `NONE`

## Outcome

Generate the first exact candidate.21 Gate F decision from the immutable signed
manifest and the current candidate-specific Windows, Smart DNS, Core AWG,
current/Brain, rollback, Gates A–E, privacy and RU PLAN records. The verifier
rehashes all `12` upstream records, validates the detached Ed25519 signature
against the manifest-bound public keyring, matches the receipt and exact
four-source tuple, then resolves all `19/19` Gate F evidence pointers.

The decision is `BLOCKED`: `4 PASS / 15 non-PASS / 0 FAIL`, with zero
validation errors. This is movement from candidate.21 `NOT_RUN` to a concrete
remaining-gaps snapshot, not promotion readiness. Gate G, public release,
Store upload and stable-pointer mutation remain unauthorized.

## Gate behavior correction

Gate F previously reused the PB-14 signed-candidate validator with its strict
physical-phone prerequisite. That made an absent phone install prevent the
aggregate from validating the signed candidate at all, even though Gate F has
the separate `android_physical_device` check for exactly that state.

Gate F now opts out of only that PB-14 prerequisite while retaining manifest,
receipt, signature, keyring, source-tuple and artifact validation. The physical
row remains `MANUAL_OWNER_TEST`; it is neither omitted nor promoted. PB-14
keeps its strict default. A focused regression proves this call boundary.

## Exact candidate identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.21` |
| Version | `1.2.0+4050` |
| Operational ID | `6a62437f7d060c5f37098cc5f96000f55d7c9ff4123c8248e2b6a9b098e503e7` |
| Platform source | `e2608130e85d9a0f8fa4b920f46cf3d7679332c3` |
| Client source | `1e164586d741484b5ae8fb2ee267ef5dd813cadb` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release-index source | `cae911e506d95eb72c1364b847992e30cbf9baf9` |
| Manifest SHA-256 | `ce0b8586d4d9b5b625bbcd2c93b03fd783f89b4958a7fd79e58ef65b52c3dc6b` |
| Signature SHA-256 | `ef474e6e1e147093b8b15c3cdc29bd35b5779249854a63ef7d6535d2588c7a58` |
| Receipt SHA-256 | `aaa027cc5d71fd567c6f3c0b8a9e3b0e965a67760fd02d1769eb3d54062926f8` |

## Gate F result

```text
BLOCKED
required=19
pass=4
non_pass=15
fail=0
validation_errors=0
candidate_validation=PASS
gate_g_authorized=false
```

The four PASS rows are signed supply/SBOM/provenance, release-document to
manifest binding, current-origin public API budgets and Brain exact-source
readiness/delivery. The remaining rows stay non-PASS:

| Status | Rows |
|---|---|
| `MANUAL_OWNER_TEST` | Gates A–E aggregate; mandatory STOP-SHIP/DoD; live rollback/kill; RU origin; complete Windows live matrix; physical Android; provider E2E; Operator RBAC/action-intent; legal/commercial; comparable performance/release health |
| `NOT_RUN` | candidate.21 LDPlayer rehearsal; cross-platform authenticated-client egress |
| `MISSING` | final live no-open-P0, false-green and privacy attestation |
| `SKIPPED_BY_OWNER` | Windows target-channel signing/manual gate; paid GitHub branch-protection/hosted aggregate |

Bounded Windows default egress, exact-Core Pi AWG2/AWG3.1, direct Smart DNS,
isolated rollback and source/static privacy are retained in the aggregate
facts, but none substitutes for its broader unfinished row.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013ET-candidate21-signed-binding.json` | `a96d349d0b0e182f2c1f09df345e3be6edc318bca98e424e08b08d02791243c6` |
| `013ET-candidate21-gate-f-evidence.json` | `e505f2f73c88333947b0c9334c64ab61325bdbe36b38590236c7341b5eae526a` |
| `013ET-candidate21-gate-f-input.json` | `6a909476156225740e01d19c9f0aac123b45485980ffaebe835c0adc3b18a138` |
| `013ET-candidate21-gate-f-decision.json` | `e30fb0cb3a5d8dbe21aade1b89f0f63dc7c845ea54fa1c2e9b8f93b610e05dec` |

The decision binds all `19/19` checks to the evidence digest. The evidence in
turn pins the new signed binding plus WO-013EH/013EI/013EJ/013EK/013EL/013EM/
013EN/013EP/013EQ/013ER/013ES JSON records by path and SHA-256.

## Verification

```text
exact signed candidate validation -> PASS manifest/signature/receipt/keyring/four-source tuple
Gate F -> expected BLOCKED exit 0 with --expect-blocked; 4/15/0; validation_errors=0
pytest Gate F, PB-14, release gate/orchestrator/script manifest -> 63 passed, 21 subtests passed
pytest documentation/context contracts -> 40 passed
pytest candidate preflight -> 24 passed
script manifest check -> PASS
compileall changed Python -> PASS
ruff changed Python -> PASS
all four retained JSON records -> PASS parse
execution ledger -> 378 rows, 378 unique; I4=7, I3=320, I2=19, I1=32, I0=0
```

## Completion index and next boundary

`REL_GATE/GATE-F` stays `I3` and advances from candidate.21 `NOT_RUN` to exact
`BLOCKED 4/15/0`. The `378`-row distribution stays `I4=7`, `I3=320`,
`I2=19`, `I1=32`, `I0=0`; no row changes level.

Next, use the already available Windows VM background channel for candidate.21
recovery work that does not require desktop input. The forced service-restart
UI/UAC boundary remains manual. Android, general RU execution, provider,
Operator, legal/commercial, runtime rollback, comparable performance and final
live attestations remain separate work.

No candidate byte, VM network, phone, emulator, server, DNS, provider,
database, Operator state, credential, tag, GitHub Release, Store object or
stable pointer is changed by this work order.

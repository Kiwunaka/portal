# WO-013EX — candidate.22 exact Gate F blocked snapshot

Status: `EXACT_CANDIDATE22_GATE_F_BLOCKED_3_PASS_16_NON_PASS_0_FAIL`

Observed: `2026-09-02`

Production/public mutation: `NONE`

## Outcome

Generate the first exact candidate.22 Gate F decision from the immutable signed
manifest, WO-013EW signed-supply/Windows record and all hosted checks attached
to the exact four source revisions. The verifier rehashes all three upstream
records, validates the detached Ed25519 signature against the manifest-bound
public keyring, matches the signing receipt and exact four-source tuple, then
resolves all `19/19` Gate F evidence pointers.

The decision is `BLOCKED`: `3 PASS / 16 non-PASS / 0 FAIL`, with zero
validation errors. This replaces candidate.22 `NOT_RUN` with a concrete gap
snapshot; it is not promotion readiness. Gate G, tag, public GitHub Release,
Store upload and stable-pointer mutation remain unauthorized.

## Exact candidate identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.22`, `1.2.0+4051` |
| Operational ID | `e1ea7f6c88b476d6f3fc0e866cad6a498d6be17d59f5f06800c0e2a1e9d58887` |
| Platform source | `d16087d5da509e17163bdd7293bec5711aa7eedc` |
| Client source | `0aad6bbb3a8baf9bd9e2436ed9e57f7c6fbbafed` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release-index source | `d45b5035e135130cbdec3968e712201e5bc78230` |
| Manifest SHA-256 | `81c56e9fcf7478c50d5881538d26fd72459f05a04d9cce403ec99d8ecdcc7d59` |
| Signature SHA-256 | `b230a4423064f5b45813fec6eb88a956b820cb6603ad2986b641f2bdd4a8a387` |
| Receipt SHA-256 | `6512351934514fd63347ddd7f40e83c5ab56148a8e5e1eb899ac22ed12812124` |

## Gate F result

```text
BLOCKED
required=19
pass=3
non_pass=16
fail=0
validation_errors=0
candidate_validation=PASS
gate_g_authorized=false
```

The three PASS rows are:

- signed supply, SBOM and provenance;
- release-document to manifest binding;
- all required hosted checks attached to the exact source tuple.

The exact hosted set is `10/10 SUCCESS`: platform `2/2`, client `1/1`, Core
`5/5` and release index `2/2`. Branch protection remains owner-declined and
independent review is not claimed; hosted execution is not branch enforcement.

The remaining rows are deliberately non-PASS:

| Status | Rows |
|---|---|
| `MANUAL_OWNER_TEST` | exact Gates A–E aggregate; mandatory STOP-SHIP/DoD; guarded runtime rollback/kill; current, Brain and RU origins; complete Windows matrix; physical Android; provider E2E; Operator RBAC/action-intent; legal/commercial; comparable performance/release health |
| `NOT_RUN` | candidate.22 LDPlayer rehearsal; cross-platform authenticated-client egress |
| `MISSING` | final live no-open-P0, false-green and privacy attestation |
| `SKIPPED_BY_OWNER` | Windows target-channel trusted signing and paid GitHub branch protection/manual gate |

WO-013EW's exact Windows 11 install/default, service-restart and connected-
reboot results remain valid bounded evidence, but the Gate F Windows row stays
non-PASS until Windows 10, sleep/resume, connected uninstall, packaged AWG,
IPv6/leak and interactive SmartScreen are resolved or explicitly dispositioned.
Likewise, AWG/Smart DNS source contracts do not replace packaged device traffic
or authenticated target sessions.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013EX-candidate22-signed-binding.json` | `777ed3d734c5f052d37d04e2adc294102a298f3372fbee053400f2ed0ada0c3b` |
| `013EX-candidate22-hosted-checks.json` | `f0716721b82eccaa20b3d44884cbdc1d8b42922a178213e64c7dd8b841825dfb` |
| `013EX-candidate22-gate-f-evidence.json` | `40464b0f2e5a12a9d16f60db04140251af9aaee95c45ec996d5d09e0e47ccc69` |
| `013EX-candidate22-gate-f-input.json` | `01cba1b9acdb4bd505dcbdf6ace11af756ca116a04a076e79c6c12f9cb1069f0` |
| `013EX-candidate22-gate-f-decision.json` | `efe47576c7ca601f73e74ccc238b3eb7a9e0aafd69a0486aecab09b7447d9641` |

The decision binds all `19/19` checks to the evidence digest. The evidence in
turn pins the signed-output binding, the WO-013EW normalized candidate record
and the `10/10` hosted-check record by path and SHA-256.

## Completion index and next boundary

`REL_GATE/GATE-F` stays `I3` and advances from candidate.22 `NOT_RUN` to exact
`BLOCKED 3/16/0`. Distribution remains `I4=7`, `I3=320`, `I2=19`, `I1=32`,
`I0=0` across `378` unique rows.

Next, prioritize exact candidate.22 Android install, packaged AWG3.1 then AWG2
and in-app Smart DNS authenticated sessions. Then close the remaining Windows,
origin, rollback, provider/database, Operator, legal/commercial, accessibility,
comparable performance/endurance and final live rows before regenerating Gate
F. No candidate byte, VM/device network, server, DNS, provider, database,
Operator, public release, Store object or stable pointer is changed by this
work order.

# WO-013FC — candidate.24 exact Gate F blocked snapshot

Status: `EXACT_CANDIDATE24_GATE_F_BLOCKED_3_PASS_16_NON_PASS_0_FAIL`

Observed: `2026-09-03`

Production/public mutation: `NONE`

## Outcome

Generate candidate.24's first exact Gate F decision from the immutable signed
manifest, WO-013FB candidate transition record and all hosted checks attached
to the exact four source revisions. The verifier rehashes all upstream records,
validates the detached Ed25519 signature against the manifest-bound public
keyring, matches the receipt and exact source tuple, then resolves all `19/19`
evidence pointers.

The decision is `BLOCKED`: `3 PASS / 16 non-PASS / 0 FAIL`, with zero
validation errors. This is a concrete gap snapshot, not promotion readiness.
Gate G, tag, public GitHub Release, Store upload and stable-pointer mutation
remain unauthorized.

## Exact candidate identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.24`, `1.2.0+4053` |
| Operational ID | `71585d32b4245120700d57db981c428b86a8dfec09a3f78f174c3d6e72ec4d41` |
| Platform source | `06b932b48ffcb92c8ec024b8892aaa9c36359673` |
| Client source | `54259b0f84e16c58e2d1f5f04b369af4fd0834b2` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release-index source | `a2fb1067adc4f2881299b45929a0d46736f74fff` |
| Manifest SHA-256 | `bdd51f2c428298e3178fd94d9befaf79aa442445a384f52882995ffd5d9ddeed` |
| Signature SHA-256 | `ef47e339cafe23bd994844e70fe8263902a0d62f03312a35b10536913e7ac0bc` |
| Receipt SHA-256 | `1ff20e15adda261dff182c1166a276270a05721f3770f5cc4df1d77b61153343` |

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

The three PASS rows are signed supply/SBOM/provenance, release-document binding
and all required hosted checks. The exact hosted set is `10/10 SUCCESS`:
platform `2/2`, client `1/1`, Core `5/5` and release index `2/2`. Branch
protection remains owner-declined and independent review is not claimed.

The remaining rows are deliberately non-PASS:

| Status | Rows |
|---|---|
| `MANUAL_OWNER_TEST` | exact Gates A–E aggregate; mandatory STOP-SHIP/DoD; guarded runtime rollback/kill; current, Brain and RU origins; physical Android; provider E2E; Operator RBAC/action-intent; legal/commercial; comparable performance/release health |
| `NOT_RUN` | installed candidate.24 Windows network matrix; LDPlayer rehearsal; cross-platform authenticated-client egress |
| `MISSING` | final live no-open-P0, false-green and privacy attestation |
| `SKIPPED_BY_OWNER` | Windows target-channel trusted signing and paid GitHub branch protection/manual gate |

The exact Windows guest file identity and source/native regression results do
not replace installation or runtime. Likewise AWG and Smart DNS source
contracts do not replace packaged-device traffic or authenticated target
sessions.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013FC-candidate24-signed-binding.json` | `5bd64d6dae3f2a614f8c55fb4e978a83be050fb66b244c68dd39c6f5e4118f67` |
| `013FC-candidate24-hosted-checks.json` | `6d88bf7664efe84199b5f493a9f8ed3ca002b29c51720c0f884c643a9f1df4de` |
| `013FC-candidate24-gate-f-evidence.json` | `44e57fb663234e16473831dde316789972d9807553dbc9c545faaa0108f88d64` |
| `013FC-candidate24-gate-f-input.json` | `e4046f414eab3d8276526d8738409d7a01e984594a3442584681c22f759f67a0` |
| `013FC-candidate24-gate-f-decision.json` | `4d79741dff6c1f7a787764669ac97520fcd2680bf1a7424806a75f5b6bd7e59c` |

## Completion index and next boundary

`REL_GATE/GATE-F` stays `I3`; distribution remains `I4=7`, `I3=320`,
`I2=19`, `I1=32`, `I0=0` across `378` unique rows.

Next, install and hash-bind exact candidate.24 in the isolated Windows VM using
a non-interactive elevated path, then run the corrected 32-client contention,
default/recovery/uninstall and transport/DNS matrices. In parallel, run exact
candidate.24 Android on a clean emulator and physical Wi-Fi/Beeline device.
Close the remaining origin, rollback, provider/database, Operator,
legal/commercial, accessibility, performance/endurance and final live rows
before regenerating Gate F. No runtime, candidate byte or public/stable state is
changed by this work order.

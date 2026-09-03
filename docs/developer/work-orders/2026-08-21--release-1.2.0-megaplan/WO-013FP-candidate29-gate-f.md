# WO-013FP — candidate.29 exact Gate F snapshot

Status: `EXACT_CANDIDATE29_GATE_F_BLOCKED_2_PASS_17_NON_PASS_0_FAIL`

Observed: `2026-09-03T10:20:00Z`–`2026-09-03T10:24:00Z`

Production/public mutation: `NONE`

## Outcome

Generate the first exact Gate F decision for private candidate.29 after the
signed CLI and bounded Windows VM slice in WO-013FO. The verifier validates the
retained manifest, receipt and detached Ed25519 signature from signed
release-index revision `71e2c71fbc1aab0b76ca634e283eaa362e605b97`, binds
the exact four-source tuple and resolves every required evidence pointer.

```text
BLOCKED
required=19
pass=2
non_pass=17
fail=0
validation_errors=0
candidate_validation=PASS
gate_g_authorized=false
```

The two PASS rows are `supply_chain_signature_sbom_provenance` and
`release_docs_manifest_binding`. No explicit candidate runtime failure is
retained, so the decision is `BLOCKED`, not `NO_GO`.

## Exact candidate boundary

| Item | Identity |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.29`, app `1.2.0+4053` |
| Operational id | `99d120ff91767f89fbb46e4d9e63b0edd34461db44a744da28b886364a3d4229` |
| Platform | `efb05e0899ad51afd4453ae2fb75f8cafe96db7e` |
| Client | `7e3e771fe36333a75244cbfd828c60beb84c7ff1` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release index | `71e2c71fbc1aab0b76ca634e283eaa362e605b97` |
| Manifest | `231e3d5264ba18e68c5aac9b6faa1bca3864c011fbff3771960e84a9edc1e9df` |
| Signature | `215f8234376d23806ad89e0d8f7d2aa0f6ad2fcc3dfeeec593e6a6f71db27bfc` |
| Receipt | `097b0c3fbeb63c2e0a2557e9fc614363ef9883c233b6b99dc8c8fb3067524fcf` |

## Gate F rows

| Check | Status | Exact boundary |
|---|---|---|
| Gates A–E exact candidate | `MANUAL_OWNER_TEST` | Local source/build proof exists; broad external and device aggregates remain open |
| Mandatory STOP-SHIP and DoD | `MANUAL_OWNER_TEST` | Final live aggregate is absent |
| No open P0 / false-green / secret leak | `MISSING` | No final candidate.29 attestation |
| Supply chain, signature, SBOM, provenance | `PASS` | Six exact artifacts and trusted manifest validate |
| Target-channel signing and manual gates | `SKIPPED_BY_OWNER` | Unsigned Windows direct beta exception is explicit |
| Release docs and manifest binding | `PASS` | Notes and known-issues digests are manifest-bound |
| Rollback and kill controls | `MANUAL_OWNER_TEST` | Guarded candidate.29 runtime/readback is open |
| Current origin | `NOT_RUN` | Candidate.25 proof is not transferred |
| Brain origin | `NOT_RUN` | Candidate.25 proof is not transferred |
| RU origin | `MANUAL_OWNER_TEST` | Exact general RU aggregate is open |
| Windows live network | `MANUAL_OWNER_TEST` | Direct Windows 11 substrate passes; complete managed matrix is open |
| Android LDPlayer | `NOT_RUN` | Exact candidate runtime is absent |
| Android physical device | `MANUAL_OWNER_TEST` | Wi-Fi/mobile device proof is absent |
| Authenticated client egress | `NOT_RUN` | Managed-node egress is absent |
| Payment provider E2E | `MANUAL_OWNER_TEST` | Provider/PostgreSQL/outbox/reversal is open |
| Operator auth/RBAC/action-intent | `MANUAL_OWNER_TEST` | Deployed authenticated flow is open |
| Legal/commercial approval | `MANUAL_OWNER_TEST` | Owner boundary remains open |
| Performance and release health | `MANUAL_OWNER_TEST` | Comparable device/browser aggregate is open |
| Hosted required checks | `BLOCKED_BY_ACCESS_GITHUB_BILLING` | Core and release index pass 7 jobs; platform/client fail before runner allocation in 3 zero-step jobs |

## Hosted boundary

Read-only GitHub check-run inspection binds ten jobs to the exact four source
SHAs. Five Core jobs and both release-index jobs finish successfully. Both
platform jobs and the client contract job finish with `failure`, empty runner
name and `0` steps. They are retained as access/billing blockage, not executed
test failures and not PASS. Local checks do not replace hosted execution.

Owner-solo review remains the approved process exception. Paid branch
protection and independent review are not claimed.

## Windows proof ceiling

WO-013FO proves exact first-attempt candidate.28-to-29 upgrade, `11/11`
installed file identities, LocalSystem service, ordinary-user UI, direct TUN
and DNS connect/disconnect and connected guest-reboot restoration in Windows
11. It does not complete managed subscription/node egress, packaged
AWG3.1/AWG2, Smart DNS, IPv6/leak, sleep/crash, connected uninstall or Windows
10. Therefore `windows_live_network` is explicitly non-PASS.

## Verification

```text
release_1_2_gate_f.py --expect-blocked -> exit 0
candidate_validation=PASS
required=19; pass=2; non_pass=17; fail=0
validation_errors=0
gate_g_authorized=false
```

The verifier used the detached release-index checkout at the exact signed
revision. It did not use the newer receipt-recording revision as signature
authority.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013FO-candidate29-cli-vm-signed.json` | `4a070634264f38f86b15a8b5ceb418128d2467682e6f29f1fb2361df04505b0b` |
| `013FP-candidate29-signed-binding.json` | `237a0e8dcc491375a1d82604d77a8958ec6506a1f808ed4fee7464a659db6170` |
| `013FP-candidate29-hosted-checks.json` | `ffdec0d905f386ae00c2a719b3b4ca0eacddd66def2f39a3f52461703a963b6b` |
| `013FP-candidate29-gate-f-evidence.json` | `25c92f38a00d5aa038e5455bf210636185049b54e828c951b5c2b457a538d188` |
| `013FP-candidate29-gate-f-input.json` | `a32e6a055cb322ee3f9d199d937a4d67d6a22564385a1c0e418d24db56bc75ab` |
| `013FP-candidate29-gate-f-decision.json` | `87ba27daeba6202b8c522cc64b7b0fcc40b21dab5c420619367554d8e41f791a` |

`REL_GATE/GATE-F` remains `I3`. No tag, GitHub Release, public asset, Store
submission, production deploy or stable-pointer mutation occurs. Gate G stays
unauthorized. The completion-level distribution remains unchanged at
`I4=7`, `I3=320`, `I2=19`, `I1=32`, `I0=0` across `378` rows.

# WO-013GF — candidate.32 signed supply and Windows non-elevated VM proof

Status: `EXACT_CANDIDATE32_SIGNED_SUPPLY_PASS_WINDOWS_NON_ELEVATED_PASS_GATE_F_BLOCKED_2_PASS_17_NON_PASS_0_FAIL`

Observed: `2026-09-03T23:50:09Z`–`2026-09-04T00:07:44Z`

Production/public mutation: `NONE`

## Outcome

Candidate.32 supersedes candidate.31 as the current private signed candidate.
It binds the complete successor source tuple and six newly retained application
files to candidate-specific CycloneDX, SLSA provenance and strict-v2 handoff.
Strict supply replay passes before signing, and the main-only release-index
signer independently validates and signs the exact tracked input.

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

## Exact candidate boundary

| Item | Identity |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.32`, app `1.2.0+4053` |
| Operational id | `a24e6a5984326dd2f57f34a4195aab85962a64efe991b85ed5284e871cf3dbbf` |
| Platform | `d0dd37c1003198ba08cffc49a040a77e21621a86` |
| Client | `2d6adfcebc37f2109ef339276be6a1569cb7aa1e` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release index | `5d11fd6821a5ebfa42163f461332125143c553c3` |
| Manifest | `b15938e1bef2b4cafb634eea81039163e2b15a446cda5bbd32d9894cbe2da449` |
| Signature | `e63d8ee39c15185afc9e600efe66a1a081b0fafc50343fd898114dfcb8bafcf4` |
| Receipt | `7bfaf81f26a2030e01db534732723fe726251457f4d0f7ebc6d7d92018375a42` |
| Hosted signer | Run `33819350778`, artifact `9917689367` |

Release-index PR `59` passes the exact source contract and merges under the
documented owner-solo exception. Signer run `33819350778` uses active key
`pokrov-release-2026-01`, revalidates without private-key output and retains a
private Actions artifact only. Receipt PR `60` records the public hashes and
the no-deploy/no-publication/no-promotion boundary.

## Supply binding

| Item | Result |
|---|---|
| Application artifacts | `6/6 PASS` |
| Windows runtime files | `11/11 PASS` |
| Canonical artifact set | `1392133caa1cb52f59c058a918ba5006d6aefded048fc0927052e4ff51575fb0` |
| CycloneDX 1.5 SBOM | `5ddf2a96244e70ad1284409f0cea6f5838fab5bfbca5c5b96a245f0716de2893` |
| SLSA provenance | `4785cd005791a8872f4c8a45202ba2d35c9d1ba65737f5683ee17d0b927c53e6` |
| Strict-v2 handoff | `df85e2ee1a03133ac79bb36064d47518f9067cd188e7624d70fd349011422bef` |
| Windows runtime manifest | `43bd310e2fb287d2ada339d8938fbe2304261fe23c9d8608124417d05af9e7dd` |

All five Android outputs carry production certificate SHA-256
`0a0602a7df5d96a0b427909d004f3ddf26def86587634bf16694da8d654b2500`.
The market AAB JAR signature validates. The Windows setup remains Authenticode
`NotSigned` under `OWNER_ACCEPTED_UNSIGNED_WINDOWS_BETA_1_2_0`; this exception
does not become trusted signing or Store proof.

## Headless Windows VM result

The dedicated VirtualBox Windows 11 VM is controlled only through guest-control.
No host screen, mouse, keyboard, route, tunnel or DNS setting is used.

The exact candidate.32 installer, signed manifest, detached signature and
receipt are copied into the guest and rehashed successfully. The guest account
is a member of Administrators but receives a filtered UAC token in the
headless session. The non-elevated silent installer therefore exits `1`
without timeout or installer log. This is the required fail-closed behavior:

- the pre-existing install stays at `8/11` candidate.32 file matches;
- installed bytes and LocalSystem service state are unchanged;
- guest route and DNS fingerprints are unchanged;
- no POKROV/Wintun adapter appears;
- no UAC or UI automation is used.

This is `PASS_NON_ELEVATED_FAIL_CLOSED`, not clean install, upgrade, managed
TUN/DNS/egress, reboot, connected uninstall, SmartScreen UI or Windows 10
credit. Exact candidate.32 elevated installation remains open.

## Hosted checks

Ten exact-source jobs are attached. Five Core jobs and the two release-index
jobs execute and pass. Two platform jobs and one client job contain zero steps
and remain `BLOCKED_BY_ACCESS_GITHUB_BILLING`; they are neither executed test
failures nor PASS. Local evidence does not replace those hosted checks.

## Gate F

| Check group | Status |
|---|---|
| Supply chain, signature, SBOM, provenance | `PASS` |
| Release docs/manifest binding | `PASS` |
| Windows non-elevated fail-closed | supplemental `PASS`; live-network row remains non-PASS |
| Mandatory stop-ship/DoD and final no-open-P0 attestation | `MISSING` |
| Hosted required checks | `BLOCKED_BY_ACCESS_GITHUB_BILLING` |
| Android, elevated/managed Windows, origins and approval rows | explicit non-PASS statuses |

Gate F is `BLOCKED 2/17/0`. Candidate.31's earlier exact Brain mismatch and
`NO_GO 2/17/1` stay immutable predecessor evidence; they are not transferred
to candidate.32. Candidate.32 has no exact origin claim yet, so current and
Brain origins are `NOT_RUN`, not PASS or FAIL.

## Verification

```text
validate_release_candidate_supply_chain.py candidate.32
  -> PASS; artifacts=6; windows_runtime_files=11

release-index source validator -> PASS
release-index tests -> 7/7 PASS
hosted signer and local public-key revalidation -> PASS

dedicated Windows 11 VM exact identity -> PASS
non-elevated installer -> PASS_FAIL_CLOSED; exit=1
installed bytes/service/route/DNS unchanged -> PASS

release_1_2_gate_f.py --expect-blocked
  -> BLOCKED
candidate_validation=PASS
required=19; pass=2; non_pass=17; fail=0
validation_errors=0
gate_g_authorized=false
```

## Evidence digests

| File | SHA-256 |
|---|---|
| `013GF-candidate32-signed-binding.json` | `e1b067710e8ec2ea194710e1dddbad469d67993cd00256b053daecf4795bdf04` |
| `013GF-candidate32-hosted-checks.json` | `e206264b65b392148f33d35bef50ce8a0fb196a78164382d8d88445701928b82` |
| `013GF-candidate32-windows-non-elevated.json` | `c655898a51d6921a67a84f1a9d745e735362bd94237fa47ce41f01a597c7b9b2` |
| `013GF-candidate32-gate-f-evidence.json` | `4ca7715b257b7427f5d464f6e102d59d89c26b4b3ff88775b3cfd67ad21dfbad` |
| `013GF-candidate32-gate-f-input.json` | `d3c5ab1960403264be1d2ab44db3420a0478b81e8ca14f7529b8213916b68cc1` |
| `013GF-candidate32-gate-f-decision.json` | `b6dcc47134fbb255f2a3738efbfb4854d4d1307ae4a6d8ff7716e0b8e78c5aa9` |
| external VM evidence | `0575b3389d85371ad616b7587763f9cf28e0f69132444763dd0be3176abf0893` |

The private candidate files remain under
`E:/POKROV-tools/release-candidates/pokrov-1.2.0-candidate.32/`. The external VM
record remains under
`E:/POKROV-tools/release-evidence/1.2.0-candidate32-windows-non-elevated-2026-09-04/`.

## Follow-up

Use an elevated but still headless guest-control mechanism only if one is made
available without screen automation; otherwise retain exact install/upgrade as
manual owner work. Connect a physical ARM64 phone or isolated emulator for the
Android matrix. Then refresh exact current/Brain/RU origins, managed transports,
rollback/kill, provider/Operator/legal/performance and final attestations.
Publication and production remain separately authorized actions.

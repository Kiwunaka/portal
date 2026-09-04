# WO-013GT — candidate.33 signed supply and exact Windows focus pass

Status: `PRIVATE_SIGNED; PASS_EXACT_WIN_001; GATE_F_BLOCKED_2_17_0`

Observed: `2026-09-04T08:01:25Z` through `2026-09-04T08:30:33Z`

Production/public mutation: `NONE`

## Outcome

Private `pokrov-1.2.0-candidate.33` is the current exact signed candidate.
It binds the merged platform/client/Core tuple to six freshly built
application artifacts, candidate-specific SBOM/provenance/handoff data and a
hosted Ed25519 manifest signature. Strict supply validation passes all `6/6`
application artifacts and all `11/11` Windows runtime files.

The dedicated headless Windows 11 VM then proves the exact candidate.33
in-place update from candidate.32 and repeats the complete `REL/WIN-001`
second-launch boundary. Plain and typed second launches each exit `0`, retain
one original UI process, forward activation and return foreground focus.
`REL/WIN-001` therefore advances from locally proved `I3` to exact-candidate
proof `I4`.

Gate F remains `BLOCKED 2 PASS / 17 non-PASS / 0 FAIL`. No deploy, public
release, Store submission, stable-pointer mutation or Gate G authorization
follows from this result.

## Exact candidate boundary

| Item | Identity |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.33`, app `1.2.0+4053` |
| Operational id | `d7a09ea6601f2cc1422366b29cc0ed7d7b8ca6fee889a143a3ebef7fe488c923` |
| Platform | `f5300053026d32826e54c02202303e1f68c65bc1` |
| Client | `6ab1bcaf39c61a0ae0c9d8328e6c95382885735e` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release-index source | `63993fba699b68641b7e972071ab7729fa9ec43c` |
| Receipt merge | `9169f272203ec690ab7b0e6a69e92dc2b6762cb4` |
| Manifest/signature/receipt | `5620c2f0...` / `5115ab3c...` / `f84843c8...` |
| Signer run | `Kiwunaka/pokrov/actions/runs/33851401873` |
| Signer Actions artifact | id `9928470408`, digest `sha256:e31d7008...` |
| Promotion boundary | `promotion_authorized=false`, `gate_g_authorized=false` |

The input release-index source-contract run `33851340475`, signer run
`33851401873` and receipt source-contract run `33851614987` execute real
steps and pass. The detached signature validates independently against public
key SHA-256
`651d1bcfbedecc4e50d21f3ad3bf3cc990a6cfc97ad355f0e0e76972b8ba8024`.
The signing private key is never accessed locally.

## Fresh artifact build

The candidate is built from the merged source tuple, not copied from a
predecessor candidate.

- Windows release helper: full Flutter `413/413`, analyze, Release build and
  native Release CTest `7/7` pass.
- Android production helper: four APKs plus one market AAB pass; the APK/AAB
  production certificate SHA-256 is
  `0a0602a7df5d96a0b427909d004f3ddf26def86587634bf16694da8d654b2500`.
- Android Core entries cover `armeabi-v7a`, `arm64-v8a` and `x86_64`.
- Windows Authenticode remains explicit `NotSigned` under the owner-approved
  direct-beta exception. The Ed25519 release-index signature is not
  Authenticode.

Canonical supply hashes:

| Item | SHA-256 |
|---|---|
| Artifact set | `1858db3491effa6224d3816763f7bd90a16429ae6b21c6fc97275d84f5d31978` |
| SBOM | `3b586c6e2b63e802ecb6cdfadf5cdac5cd8b7957a5112da4ed9d0a86f6646125` |
| Provenance | `9aadcb1dfa8973c08ca4682238e91baa17f4aa952f4d03eb78ebdfea733aeb08` |
| Strict handoff | `30d9d04437caa51c0fafb533a77589d745c66cd7ce5c17843d5b3a1e37e72c81` |
| Windows runtime manifest | `0f93211e254076fad5de8cf88d0817897313c2fd3f3b2daa6d1253628da63a5b` |
| Supply validation report | `c1259e7acb9ff9793c43adf4088501ab3b41dbc29991ab64a151d61f11e87274` |

## Hosted checks

The platform and client PRs are merged under the explicit owner-solo
exception. Three required hosted jobs terminate before executing any step:

- platform `repo-guardrails`: run `33849479231`, job `100948752956`;
- platform `cross-repository-contract`: run `33849479243`, job
  `100948752849`;
- client `cross-repository-contract`: run `33849479969`, job
  `100948755024`.

Each has `steps=[]` and is classified
`BLOCKED_BY_ACCESS_GITHUB_BILLING`, not `FAIL` and not `PASS`. The successful
release-index runs above are retained separately and do not erase this access
blocker.

## Exact Windows 11 VM result

The VM starts from the exact candidate.32 UI
`611208b20b68b333d81655b0d6dbd7ada3a213fbfd9a82b6af71b01b3bdf15a2`.
Candidate.33 setup then exits `0` and reconciles all `11/11` installed
runtime files to its manifest. The installed UI is
`1b175a66523be467c0fa66e8f74df20dbeb87f7e190f5dc57a9f1cea0961d97f`.
The service remains `Running`, `Automatic`, `LocalSystem`.

Final `WIN-001` replay:

- plain second launch: exit `0`, exactly one original process retained,
  foreground focus returned;
- typed second launch: exit `0`, exactly one original process retained,
  foreground focus returned;
- final UI process count: one;
- POKROV adapter, route and DNS contour: unchanged;
- cleanup: zero UI processes and the VM is powered off.

Two non-product harness failures are retained. The first install collector
fails after the installer succeeds because strict property access encounters
an optional uninstall-registry field; an independent post-check reconciles
the completed update. The first focus attempt proves the plain launch but its
control window cannot re-foreground itself before the typed case; the
strengthened foreground harness then passes both cases without product or
candidate changes.

Raw evidence is retained under
`E:/POKROV-tools/release-evidence/1.2.0-candidate33-windows-focus-2026-09-04/`.

## Gate F

The exact signed candidate, detached signature, receipt and all `19/19`
evidence pointers validate with zero validation errors. Current check counts
are:

```text
BLOCKED
required=19
pass=2
non_pass=17
fail=0
validation_errors=0
gate_g_authorized=false
```

The two PASS checks are signed supply-chain evidence and release
documentation/manifest binding. `WIN-001` is supplemental exact-candidate
proof, but it does not itself convert the aggregate Gates A–E check to PASS.
The current blockers remain exact Gates A–E/STOP-SHIP aggregation, connected
Windows default/AWG/Smart-DNS, Android LDPlayer and physical-device runtime,
authenticated egress, current/Brain/RU origins, runtime rollback, provider,
Operator, legal, comparable performance and final attestations.

## Completion index

Only `REL/WIN-001` advances from `I3` to `I4`. All other levels remain
unchanged. Across `378` unique ledger rows the distribution becomes:

```text
I4=8
I3=319
I2=19
I1=32
I0=0
```

## Tracked evidence

| File | SHA-256 |
|---|---|
| `013GT-candidate33-signed-binding.json` | `79bd55b410f441f7a003498ece4bfe81dec460dd5ed893115d212a990554920c` |
| `013GT-candidate33-windows-focus.json` | `20ba6afee2ee88a2f11d430c37266f9da51ed61c934c4fbd2fdd17443a4d65ca` |
| `013GT-candidate33-hosted-checks.json` | `fc21d2b55e27e412c612650dec9c3790608ca028dfef58b759318d0d88e80d04` |
| `013GT-candidate33-gate-f-evidence.json` | `f02d4ff3834ec3c5ddd052586907a0fb25ca6b46286805305306314a560c4d33` |
| `013GT-candidate33-gate-f-input.json` | `7043949840d492d68f1ae6da6a2850ae1c8e6d39595130d938233c54058c339c` |
| `013GT-candidate33-gate-f-decision.json` | `451f0a5ad55dbb6301a1d273237b3ab5b68fd36cd94d55a49775c6c030e3aa94` |

## Follow-up

Keep candidate.32 immutable `NO_GO` history and candidate.33 private. Replay
the exact candidate.33 Gates A–E/STOP-SHIP slices, then execute connected
Windows default/AWG/Smart-DNS, Android LDPlayer/physical-device, exact
origins, guarded rollback and the remaining approval/performance/final rows.
Recalculate Gate F after each materially closed group. Public release, Store,
stable-pointer mutation, deploy and Gate G still require their separate
release boundary.

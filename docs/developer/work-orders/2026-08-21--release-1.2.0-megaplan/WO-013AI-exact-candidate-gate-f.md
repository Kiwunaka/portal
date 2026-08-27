# WO-013AI — Exact candidate.3 Gate F decision

Status: `NO_GO_EXACT_CANDIDATE_GATE_F`
Phase: `11`
Candidate: `pokrov-1.2.0-candidate.3`
Rows: `REL_DOD/DOD-20`, `FE_PR/PR-10`
Deployment: `NOT_RUN_NOT_AUTHORIZED`
Recorded: `2026-08-27`

## Goal

Emit one fail-closed Gate F decision for the exact signed candidate without
changing production, commercial state, public assets or the stable pointer.
The decision must validate the Ed25519 manifest binding, exact source tuple,
candidate-scoped evidence files and their upstream SHA-256 digests before it
classifies the candidate as `GO`, `NO_GO` or `BLOCKED`.

The owner later returned the physical phone, but it contains post-candidate
lab build `1.2.0+4031`, not candidate.3 `1.2.0+30`. Its evidence remains
separate from the mandatory exact-candidate physical-device gate.

## Exact candidate binding

| Surface | Identity |
|---|---|
| Candidate label | `pokrov-1.2.0-candidate.3` |
| Operational candidate ID | `51f54f889279c49354b822aea9d188af46346e4ed380c73c3a700bd5911f253b` |
| Platform source | `eafaca3e64c0619dea7f58fc9c430682b4520559` |
| Client source | `ac22825e857a313c9e4eba61030eb548d6346ead` |
| Core source | `344b317a7a09eca7943a93866b193553538bd8f6` |
| Release-index source | `6a1afa95fe52da2d559ba7b1da88715cd0344bb2` |
| Manifest SHA-256 | `a2752b6a3b95faacf13a68edb708c560966a0f5eb8727e109d7f1603fdc81090` |
| Signature SHA-256 | `926f0b4667a58ba9cc5ace5c4e6c3c8129d1ec3d4d449b3f0831a8c527cd7121` |
| Receipt SHA-256 | `fb4d0d5dd272b8d3e7ea2303e2ffa93e332f54ac3e92f245400decc6c06e4b53` |

`scripts/release_1_2_gate_f.py` reuses the retained candidate verifier. It
loads the trusted Ed25519 keyring from the manifest-bound release-index Git
revision, verifies the detached signature over exact manifest bytes and
matches the receipt, label, operational ID, source tuple and three retained
file digests. It then requires one fixed 19-check Gate F set. Each check must
resolve through an in-repository evidence path, exact file SHA-256, JSON status
pointer and exact candidate pointer. Duplicate/missing checks, path escape,
hash drift, candidate drift, unknown labels or invalid signed input produce
`NO_GO`.

The `--expect-blocked` audit option returns success only for an honestly
validated `BLOCKED` report. It cannot turn `NO_GO` into a successful command.
Even a future Gate F `GO` leaves Gate G and public/stable mutation explicitly
unauthorized pending a separate owner instruction.

## LDPlayer and physical-lab boundary

LDPlayer `emulator-5554` reports Android 9 and model `SM-S9280`. Installed
package `space.pokrov.pokrov_android_shell` is `1.2.0 (30)` and uses APK
Signature Scheme v2. Pulling the installed `base.apk` produced SHA-256
`f41c76ebf7bf69f6681d7df87e7722dcdccdec383ef950156b69829caee71c51`
and size `295051181`, exactly matching signed manifest artifact
`android-universal` / `pokrov-android-universal.apk`.
The pulled bytes are retained outside the repository at
`E:\POKROV-tools\release-evidence\1.2.0-candidate3-ldplayer-2026-08-27\installed-base.apk`;
the temporary copy was moved out of the scratch directory.

The exact activity launched with Android status `ok` in `1309 ms`; the process
survived and the cleared crash buffer contained zero package lines. The UI
reported `Не защищено` and `Продлите доступ, чтобы подключиться`. Bounds-derived
UIAutomator navigation also reached Profile and Support; human chat remained
primary and AI helper, feedback, diagnostics and the composer rendered without
a crash. No ticket or message was created, so live support polling is
`NOT_TESTED`. Install/launch rehearsal remains `PASS`, while authenticated
entitlement, catalog, TUN/DNS/egress are `BLOCKED_BY_ACCESS`/`NOT_RUN`. No
entitlement was granted or bypassed.

The returned physical Huawei phone proves only the lab build boundary: DNS,
AI/Games settings persist after a cold restart; the ARM64 Core contains the
separate AWG2/AWG 3.1 contracts; and one Beeline LTE ordinary-profile attempt
fails closed. It is not candidate.3 evidence. Live Brain inspection also shows
that no AWG rollout, material secret, material row or isolated server is
configured, so no live AWG pass is claimed.

System and Android SDK ADB installations reported a daemon-version conflict.
The retained recheck and Support navigation completed with LDPlayer's own ADB
against `emulator-5554`; this tooling noise is not classified as an application
failure.

## Gate F decision

The final report is:

- decision: `NO_GO`;
- required checks: `19`;
- `PASS`: `5`;
- non-PASS: `14`;
- explicit `FAIL`: `1`;
- structural/signature/evidence validation errors: `0`.

The five passed checks are exact supply-chain signature/SBOM/provenance,
release-doc/manifest binding, current-origin local aggregate, separate
Brain-origin control-plane aggregate and exact-byte LDPlayer install/launch
rehearsal.

The fourteen non-PASS checks retain the following boundaries; the first is an
explicit failure:

1. Gates A–E are not all exact-candidate proven: Gate B returns `NO_GO`
   because the frozen platform source fails its observability
   support-reference freshness contract on a normal Windows CRLF checkout;
   Gate C is separately `BLOCKED` by incomplete Windows live-network and
   authenticated physical Android/OEM/store matrices.
2. Mandatory STOP-SHIP/DoD rows are not all exact-candidate proven.
3. Absence of every P0/false-green/secret issue cannot yet be asserted across
   the incomplete external matrix.
4. Target-channel signing/manual gates are incomplete; the accepted unsigned
   Windows direct-beta exception remains `SKIPPED_BY_OWNER`, never signing
   `PASS` for public/stable release.
5. Rollback triggers exist and isolated portal/client rollback passed, but an
   authorized runtime rollback/readback remains absent.
6. RU-origin is `BLOCKED_BY_ACCESS`.
7. Windows live TUN/DNS/egress/recovery is `MANUAL_OWNER_TEST`.
8. Physical Android exact-candidate proof is `MANUAL_OWNER_TEST`.
9. Authenticated client egress is `BLOCKED_BY_ACCESS` by expired entitlement.
10. Payment-provider production E2E is `MANUAL_OWNER_TEST`.
11. Operator production OIDC/RBAC/action-intent is `MANUAL_OWNER_TEST`.
12. Legal/commercial approval is `BLOCKED_BY_OWNER_DECISION`.
13. Comparable Android/Windows performance and recovery baselines are missing.
14. Required hosted checks are
    `BLOCKED_BY_ACCESS_GITHUB_BILLING`.

WO-013AJ gives Gate A an exact-candidate `BLOCKED` baseline. WO-013AK adds the
first explicit candidate failure at Gate B. WO-013AL records Gate C as
`BLOCKED` without manufacturing a second candidate defect. The `5`/`14` split
stays the same, but one of the fourteen non-PASS checks is `FAIL`, forcing
`NO_GO` rather than `BLOCKED`.

## Hosted-check boundary

The retained platform check readback feeding this rerun is PR `#49` head
`09bea07870708d6ceab54fd84d0bc2d6a1cd18ee`. Guardrails run `33051838866` /
check `98448998673` and Release v2 Contract run `33051838890` / check
`98448998491` both contain zero steps. Client support-polling PR `#29` head
`03a59a7d155ffbbe77a9a0087ff5666b90ac1c92` has the same zero-step boundary in
run `33053181727` / check `98453413213`. GitHub annotations name failed recent
account payments or an insufficient spending limit. This is retained as
`BLOCKED_BY_ACCESS_GITHUB_BILLING`, not a code failure and not a pass.

`OWNER_SOLO_EXCEPTION` waives only an unavailable second human reviewer. It
does not waive required successful GitHub App checks, so PRs `#49` and `#29`
remain unmerged.

## Evidence digests

| File | SHA-256 |
|---|---|
| `010K-support-transport-reconciliation.json` | `c3691f84be3fb526fec2e3cc56dc9977ec84bc77b1dfb9374228debf8587a769` |
| `013AJ-gate-a-decision.json` | `f4441a19521d1d77703f599c1257f620fb048167c3db9ff3a24f2935694f2d01` |
| `013AK-gate-b-decision.json` | `07d5bcbd5be6631b3648fb10926bb773ccbb4f41fb0d5ba7fbabddad9fe5f21b` |
| `013AL-gate-c-test-evidence.json` | `51485c2b02487d196ea24f5c7b3e35c7126add9a72e66162f774dd635b2c3347` |
| `013AL-gate-c-decision.json` | `58aeaf052b6b3bf14051990c4daf41f9bddc97fe3ce2df5b115221fe34bc5988` |
| `013AI-candidate3-ldplayer-recheck.json` | `9cb9a0483aa6714cdd96b3e0f1c6e00007e45089340727deb2b4ae24dfef83a5` |
| `013AI-candidate3-gate-f-evidence.json` | `a21a696a0ed8a03885d4861fe2bab0a623fc91c0012698c3c23fe726a159e30f` |
| `013AI-candidate3-gate-f-input.json` | `250acefd265941a3c7a366b919d100e63f3efcbc8d406045517af6adc79510ff` |
| `013AI-candidate3-gate-f-decision.json` | `ad3fa74eb861534b42e0d6121ecb0f5bd8ed00e682daf0a1c1f077ab14a94e9b` |
| Current execution ledger after WO-013AL | `1a8f8f2da4baa1fed08e075835a11b4d93e18f6722b54d981cbef24a97b00c52` |

The decision report directly binds the input digest; the input binds the Gate
F aggregate; the verifier also re-hashes every listed upstream evidence file.

## Verification

- release Gate F/preflight/STOP-SHIP/docs-contract tests: `71 passed`;
- platform context audit and upstream-evidence hash audit: `PASS`;
- real candidate invocation: exit `2` with an honestly retained `NO_GO`;
- Ed25519/candidate validation: `PASS`;
- evidence validation errors: `0`;
- result: `NO_GO`, promotion not authorized.

## Ledger decision

`REL_DOD/DOD-20` and `FE_PR/PR-10` advance from `I0` to `I3`: the
evidence-based decision mechanism and local release-hardening aggregate are
implemented and verified. Neither row advances to `I4`, because the exact
candidate decision is `NO_GO` and non-PASS evidence never becomes candidate
proof.

After WO-010K reconciles the conditional support-transport row, WO-013AJ
baselines Gate A without treating its blockers as pass, WO-013AK fails Gate B
and WO-013AL records Gate C as blocked, a fresh fail-closed Gate F rehash keeps
distribution at `I4=4`, `I3=312`, `I2=19`, `I1=41`, `I0=1`;
`316` rows are at or above `I3`, `61` remain below. The remaining stage split
is `pre_freeze=0`, `candidate=28`, `external=14`, `deferred=19`.

The rerun is exactly `NO_GO` with `5` PASS, `14` non-PASS, `1` explicit FAIL
and zero validation errors. Neither the unmerged client polling correction,
WO-010K nor the post-candidate Gate B fix is part of the signed candidate.3
tuple.

No deploy, restart, route change, entitlement/payment mutation, public asset,
stable-pointer change or Gate G authorization occurred.

## Next action

Restore GitHub Actions billing access and require successful checks before
merging platform PR `#49`, the Gate B correction or client PR `#29`, then land
each through the same owner-solo control. Build a replacement signed candidate
that contains both required corrections and replay Gate B plus exact-byte
LDPlayer support polling. Use a legitimately entitled owned test account
before authenticated candidate catalog/TUN/DNS/egress or live ticket polling;
the current physical lab build cannot substitute for that run. Separately
execute Windows live network,
distinct RU-origin, provider/operator/legal and comparable performance gates.
Rerun Gate F after every retained evidence change. Public/stable promotion
remains prohibited until the decision is `GO` and the owner separately
authorizes Gate G.

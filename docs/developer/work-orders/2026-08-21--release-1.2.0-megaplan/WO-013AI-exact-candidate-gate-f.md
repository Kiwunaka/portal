# WO-013AI — Exact candidate.3 Gate F decision

Status: `BLOCKED_EXACT_CANDIDATE_GATE_F`
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

The owner removed the physical phone and explicitly limited Android work to
LDPlayer. Emulator evidence therefore remains separate from the mandatory
physical-device gate and cannot close it.

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

## LDPlayer-only recheck

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
reported `Не защищено` and `Продлите доступ, чтобы подключиться`. Therefore
install/launch rehearsal is `PASS`, while authenticated entitlement, catalog
TUN/DNS/egress are `BLOCKED_BY_ACCESS`/`NOT_RUN`. No entitlement was granted or
bypassed. No physical device was used.

Two ADB installations reported a daemon-version conflict. The retained pull,
package inspection and launch commands all completed against
`emulator-5554`; this tooling noise is not classified as an application
failure.

## Gate F decision

The final report is:

- decision: `BLOCKED`;
- required checks: `19`;
- `PASS`: `5`;
- non-PASS: `14`;
- explicit `FAIL`: `0`;
- structural/signature/evidence validation errors: `0`.

The five passed checks are exact supply-chain signature/SBOM/provenance,
release-doc/manifest binding, current-origin local aggregate, separate
Brain-origin control-plane aggregate and exact-byte LDPlayer install/launch
rehearsal.

The fourteen non-PASS checks retain the following boundaries:

1. Gates A–E are not all exact-candidate proven.
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

## Hosted-check boundary

The latest PR `#48` head is
`f98de896e569bad476d257a4309bb91c8a0c5393`. Guardrails run `33045480995` /
check `98428366246` and Release v2 Contract run `33045481090` / check
`98428366767` both show failure conclusions because GitHub did not start their
jobs. Check annotations name failed recent account payments or an insufficient
spending limit. This is retained as `BLOCKED_BY_ACCESS_GITHUB_BILLING`, not a
test failure and not a pass.

`OWNER_SOLO_EXCEPTION` waives only an unavailable second human reviewer. It
does not waive required successful GitHub App checks, so PR `#48` remains
unmerged.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013AI-candidate3-ldplayer-recheck.json` | `4de4b5c3f5d9419adbcbe016c5456baec6cb17ef946cbcbf5b9fe23bd672ce26` |
| `013AI-candidate3-gate-f-evidence.json` | `ea9df91b52b5e88b935c644cc78d1a8a17281d5ce6824d2880d8e7e9198d1e9c` |
| `013AI-candidate3-gate-f-input.json` | `d80679146c7918a2fd55adf605fe398b91d3a89f008d4b3b394a8f732d044be4` |
| `013AI-candidate3-gate-f-decision.json` | `bdf204037c36ba68cb4ee848ea8e70821b7dfab48fab95b1e443dc92955eceda` |
| Updated execution ledger | `eba76f490122bcecccbd275a091e4b5e72e91ca0d04be0a81c28d7f4601427b4` |

The decision report directly binds the input digest; the input binds the Gate
F aggregate; the verifier also re-hashes every listed upstream evidence file.

## Verification

- focused Gate F tests: `10 passed`;
- real candidate invocation: exit `0` only with `--expect-blocked`;
- Ed25519/candidate validation: `PASS`;
- evidence validation errors: `0`;
- result: `BLOCKED`, promotion not authorized.

## Ledger decision

`REL_DOD/DOD-20` and `FE_PR/PR-10` advance from `I0` to `I3`: the
evidence-based decision mechanism and local release-hardening aggregate are
implemented and verified. Neither row advances to `I4`, because the exact
candidate decision is `BLOCKED` and non-PASS evidence never becomes candidate
proof.

Distribution becomes `I4=4`, `I3=310`, `I2=15`, `I1=38`, `I0=10`;
`314` rows are at or above `I3`, `63` remain below. The remaining stage split
is `pre_freeze=0`, `candidate=28`, `external=14`, `deferred=21`.

No deploy, restart, route change, entitlement/payment mutation, public asset,
stable-pointer change or Gate G authorization occurred.

## Next action

Restore GitHub Actions billing access and require successful checks before
merging PR `#48`, then land this stacked Gate F change through the same
owner-solo control. Continue LDPlayer-only work without claiming a physical
device: use a legitimately entitled owned test account before authenticated
catalog/TUN/DNS/egress. Separately execute Windows live network, distinct
RU-origin, provider/operator/legal and comparable performance gates. Rerun
Gate F after every retained evidence change. Public/stable promotion remains
prohibited until the decision is `GO` and the owner separately authorizes
Gate G.

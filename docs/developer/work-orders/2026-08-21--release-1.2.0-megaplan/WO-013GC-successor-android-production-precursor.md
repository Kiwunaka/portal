# WO-013GC — successor Android production supply precursor

Status: `PASS_LOCAL_PRE_CANDIDATE_ANDROID_5_OF_5_CANDIDATE_NOT_CREATED`

Observed: `2026-09-03T22:37:12Z`–`2026-09-03T22:41:22Z`

Production/public mutation: `NONE`

## Outcome

The canonical Android production helper now builds the complete five-file
Android supply set in one fail-closed CLI path: four direct APK variants and
the market-only Store AAB. Client PR 74 merges that correction to `main` at
`2d6adfcebc37f2109ef339276be6a1569cb7aa1e` under the retained owner-solo
exception.

Two successive helper executions produce the same five Android artifact
hashes. The final execution is bound to the exact merged `main` revision. All
four APKs pass `apksigner`; the AAB passes JAR signature verification, carries
the same production certificate and contains the Android manifest plus Core
libraries for `armeabi-v7a`, `arm64-v8a` and `x86_64`.

This is local supply-precursor evidence only. `candidate_created=false`, Store
submission is `NOT_REQUESTED`, and no candidate.32 input, candidate-bound SBOM,
provenance, strict-v2 handoff, release-index commit, hosted release signature,
deploy or public asset is created.

## Exact source boundary

| Repository | Revision | Role |
|---|---|---|
| Platform product source | `3018fd27be57bfa590aac0bc55df949f8a7415ef` | current exact product/contracts used by the predecessor local gate |
| Platform ledger head | `abe63e500cb569955c9e54d2f23cc2d91024a9a6` | append-only WO-013GA/GB evidence only |
| Client | `2d6adfcebc37f2109ef339276be6a1569cb7aa1e` | merged `POKROV-app/main` and exact Android build source |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` | pinned Core `1.1.0` artifacts |
| Release index | `4de2e9f8620b5aac2f538dc8a052a44ad2a563a5` | unchanged published `main`; no candidate input added |

The version stays `1.2.0+4053` in `PRE_CANDIDATE_LOCAL` state.

## Android artifacts

| File | Bytes | SHA-256 |
|---|---:|---|
| `pokrov-android-arm64-v8a.apk` | `101366678` | `fe8d82289a4903958fe7ed4cf7f8a472e417760a72c95930328a9b9ec3a285f9` |
| `pokrov-android-armeabi-v7a.apk` | `90778788` | `71de150a4b411c8711146123f0255a88eb6201d6cb19037144baf65f9214aaef` |
| `pokrov-android-market.aab` | `126263340` | `53de5d9b9d0a64ef4e7a8cfaf2e6f1972f8ce21c1b723a764b03edd14894bf7f` |
| `pokrov-android-universal.apk` | `295370161` | `a5ddfa5a5e35f828df4c1817256658c4b569e61d12e4742107fa43c30c506d05` |
| `pokrov-android-x86_64.apk` | `109951989` | `00e792ab69e1d0e0c165e3e94be9c9bd4c1b66e9e2dbf706363987b45791d4f5` |

All five use production certificate SHA-256
`0a0602a7df5d96a0b427909d004f3ddf26def86587634bf16694da8d654b2500`.
The AAB record explicitly preserves `store_submission_status=NOT_REQUESTED`
and `candidate_created=false`; producing a signed bundle does not establish a
Store object or availability claim.

## Windows artifact reuse boundary

The retained Windows setup remains
`c66817238d49e366d143de0580513167b38656c78044f8abc9a7313d67c721ab`
(`29154644` bytes) from the immediately preceding
exact client build at `ad2a33d...`. The complete client delta from that build
to merge `2d6adfc...` is restricted to:

- `scripts/build-android-production.ps1`;
- its static contract in `test/docs-contract.ps1`;
- `scripts/README.md`;
- `docs/operations/android-release-audit.md`.

No Windows, shared app, runtime or package source changes. The setup is
therefore retained as same-product-tree precursor bytes, not represented as a
fresh Windows compilation and not assigned candidate credit. Authenticode
remains `NotSigned` / `SKIPPED_BY_OWNER` under the existing direct-beta
exception.

## Verification

```text
PowerShell parse                                  PASS
test/docs-contract.ps1                            PASS
validate-seed.ps1 with exact platform/Core roots PASS
production helper, branch tree                    PASS 4 APK + 1 AAB
production helper, merged main                    PASS 4 APK + 1 AAB
two-run Android artifact identity                 PASS SAME BYTES 5/5
independent copied-artifact signature replay      PASS 4 APK + 1 AAB
artifacts/releases/** delta                       NONE
git diff --check                                  PASS
```

The first seed invocation used temporary-worktree sibling autodiscovery and
stopped because that environment has no sibling Core checkout. The explicit
exact roots above remove only that setup miss; product source does not change.

GitHub run `33813919433`, job `100841695789`, has `runner_id=0`, zero steps
and the account Billing/spending-limit annotation. It is
`BLOCKED_BY_ACCESS_GITHUB_BILLING`, never PASS. PR 74 is merged using the
already documented `OWNER_SOLO_EXCEPTION` and the passing local evidence.

## Release interpretation

- Five current-source Android files are now available for a separately
  authorized candidate assembly.
- No install or physical-device runtime credit is assigned to these exact
  bytes.
- Candidate.31 remains the current private signed candidate and its Gate F
  remains immutable `NO_GO 2/17/1`.
- The `378`-row distribution and all completion indices remain unchanged.
- Candidate-bound supply metadata must be regenerated and strictly validated
  only after explicit candidate.32 creation authorization.

## Evidence digests

| File | SHA-256 |
|---|---|
| tracked `013GC-successor-android-production-precursor.json` | `9eb228b5612e65246e103efbdcbf7987fddcbdd277f7653a8873ad629ecaf508` |
| external aggregate report | `60b50922ca0b904391a44dc31e67f1c24d4d65b526217e8e764265ccda35a3f4` |
| exact merged-main build log | `8ff95383ed6c8ac401d657486d3baa04a61e0b59f1afd895c80190ccb21fabee` |
| helper validation log | `8861f214df2bc329e4dba560ee34672b6d492c133734706c6a74f154be0ec70e` |
| independent signing replay | `ce6f647d7f96532be04670d44be458d8f8ef1f3d4fc6f90629e39ba38f85ab1d` |

External artifacts and reports are retained under
`E:/POKROV-tools/release-evidence/1.2.0-successor-main-android-pre-candidate-2026-09-04/`.
The tracked record contains no token, private key, password, raw connection
material, customer data or provider payload.

# WO-013Q — Exact local pre-candidate artifact assembly

Status: `LOCAL_PRE_CANDIDATE_ASSEMBLED_WINDOWS_SIGNING_BLOCKED`
Phase: `11`
Rows: `REL_DOD/DOD-15`
Candidate: `NOT_CREATED`
Production/publication: `NOT_AUTHORIZED_NOT_RUN`

## Outcome

The explicitly authorized candidate-preparation slice built one exact local
artifact set from the frozen source tuple:

- platform `2ed944c5eaa667c44a7bc1970d2dd175ff34f8c9`;
- client `3904734ce7761cc92c4136f1eaf13e20f2354f72`;
- Core `bdbd97fae35103e705f55908caebf75b4a9ff72f`;
- public release-index `491436889ef911de868d704e68ba86e77102b0f1`.

This is not an RC. Android is production-signed, but the Windows installer has
no trusted Authenticode signature and the client does not embed the separate
support-mode verification key. The strict handoff therefore retains 12
required promotion gates below `PASS`, `candidate_created=false` and
`candidate_proven=false`.

## Artifacts

| Artifact | Size | SHA-256 | Signing state |
|---|---:|---|---|
| `pokrov-android-arm64-v8a.apk` | 101157042 | `8d647a32fda62657b1f97f85ec2a3a77c9773ac75419dc21c34303c15ec9bfb3` | production signer PASS |
| `pokrov-android-armeabi-v7a.apk` | 90620944 | `2b05f4e2fa28e9d6c9d69000f56b61451e4f761e2dc48ebcedbfdd5f5634f570` | production signer PASS |
| `pokrov-android-market.aab` | 126073750 | `74e37ca60dcbf318ab419e5448d02f2d509123004e346fcde67785968110c6e4` | production signer PASS; store not published |
| `pokrov-android-universal.apk` | 294859469 | `80dc619ccc44e274a8fef5109f6efb73e24c01525db1afcfd3b67a7f154d11b0` | production signer PASS |
| `pokrov-android-x86_64.apk` | 109801745 | `f54a4aabcceeccfb608609596b28fbb9507ebe57ce5877dc1a29a3379e6d993c` | production signer PASS |
| `pokrov-windows-setup-x64.exe` | 28879349 | `fd1de72735b735851e69a010914e1d6090f6466efaacd2d90b67d5f8ca830899` | `NotSigned`; not candidate-eligible |

The six-file artifact-set digest is
`6a89748d26f84da3bef8ecae3bd5fd897747a74bae02311be8028224d4649964`.
All files pass the final checksum list. The 6,931-byte bundle manifest has
SHA-256 `64557e6008189cc4e9896e6d9f8d5bbf1dd338c44819f114589b355aba321552`;
the 2,504-byte release checksum list has SHA-256
`9a020cd2d4160ebcb9e0cad274672558d537731657a0956cf82383883b7ce434`.

## Build and supply evidence

- Exact client/Core/platform seed validation passed before both platform
  builds. The Windows builder then ran the complete standard client gate,
  analyze, direct/store Android unit tests and release packaging. The internal
  duplicate seed call was skipped only after the explicit frozen-root seed
  check passed; the default adjacent stale Core checkout was not credited.
- Android APK/AAB signer identity is
  `sha256:0a0602a7df5d96a0b427909d004f3ddf26def86587634bf16694da8d654b2500`.
  No debug signing is credited.
- The Windows service-first installer contains the exact embedded Core DLL
  `ef9672b3ba9983012bfa78abd2e4cd8ef5ef65d8e4b6a49ff89f8c4d0d575040`
  and Cronet
  `8ef1f8bbde77f954af1ae47bee1819ac8dc2354bb0e1d4baba3dad9e58d7a6f7`.
  `Get-AuthenticodeSignature` returns `NotSigned`.
- CycloneDX 1.5 SBOM SHA-256 is
  `bff820b16559855a27e85099418e10dbda46834ab0de7376f6321a5d68d381f6`;
  SLSA v1 JSON provenance SHA-256 is
  `803308b917b0f1e7a377fadab12d99b182ac9025d454b55e40655c27018ffdb0`.
- Strict-v2 handoff SHA-256 is
  `8d9a2d0098ad11a64a8dd1c3f4a082a35eddc918ed498a8d5948c737d8eb8060`.
  Platform validation classifies it `valid_v2` with six artifacts and 12
  unresolved required promotion gates.

## Preflight correction

The old preflight coupled the execution ledger to the frozen platform checkout.
That made the post-freeze source-promotion proof for `REL-001` and `DOD-09`
look unresolved even though `WO-013P` had already advanced both rows to `I3`.

Tool revision `08dc6a92e811f0ad94d0c9ac39f391e386d3862f` separates the exact
platform source root from the clean post-freeze ledger root and records both
identities. Focused release-script regressions pass `58/58` plus 21 subtests.
The final preflight binds platform/client/Core/public-index above, ledger
`2522bf0d2c1c6a38258e07610c5b486111a49fd4` and the tool revision itself.
It reports `READY_LOCAL_FREEZE`, zero blockers, zero pre-freeze rows and zero
external pre-candidate rows. Its SHA-256 is
`c7a4feec70989a97039d0d523f73d0b6bd9016a3fcc9c5e1f9f633c4f34b6ee1`.

## Remaining gates

Before these bytes can become an exact candidate, the release still requires
a trusted Windows signer and the support-mode signing key contract. Adding the
support public key is a build-input change; signing Windows changes installer
bytes. Either action therefore creates a new artifact-set identity and requires
a regenerated handoff, SBOM/provenance binding and checksums.

Candidate/runtime proof then still requires Windows clean-host `WIN-003`,
Android physical/OEM and signer-recovery checks, current-origin and brain-origin
readback, payment-provider E2E, Operator OIDC/RBAC, legal/commercial approval
and rollback. RU-origin remains separate and is required only for an RU claim.

The owner-controlled GitHub secret `POKROV_RELEASE_SIGNING_KEY_PEM` is the
Ed25519 private half for the public release-index manifest. It is not a Windows
code-signing certificate, and its value was not read or exposed.

## Ledger decision

`REL_DOD/DOD-15` advances `I0 -> I2`: the exact local app artifact set,
production Android signatures, SBOM, provenance and strict handoff now exist,
but trusted Windows signing, signed public manifest and same-byte promotion do
not. Distribution becomes `I3=309`, `I2=17`, `I1=37`, `I0=14`; 68 rows remain
below `I3`, with stage split `0/33/14/21`.

# WO-013FZ — successor Windows main same-byte reproducibility and CLI validation

Status: `SUCCESSOR_CLIENT_MAIN_REPRODUCIBILITY_PASS_PRE_CANDIDATE_LOCAL_GATE_UNCHANGED_NO_GO`

Observed: `2026-09-03T21:13:03.170248Z`

Production/public mutation: `NONE`

## Outcome

The Windows reproducibility defect retained by WO-013FY is corrected in
successor client source and merged to `POKROV-app/main`. Two independent clean
worktrees at the exact correction commit and a third clean build from the
resulting merge commit produce the same `302/302` staged bundle files byte for
byte through a canonical temporary `P:` build path. The UI, service and
`data/app.so` hashes that previously differed are now stable.

The third build is a complete headless CLI run. Cross-repository and release
contracts, the complete bounded Flutter/Android contour, Windows analyze,
Release native CTest and an exact Core DLL 100-cycle backtest pass. An unsigned
outside-Store beta installer is built under the existing owner exception; its
`NotSigned` status and SmartScreen requirement are expected and recorded. The
installer is not launched or installed.

This is `PRE_CANDIDATE_LOCAL` successor-source proof. Candidate.31 remains
immutable, its exact Gate F decision remains `NO_GO 2/17/1`, and no candidate,
tag, asset, Store object, production deploy or stable pointer is created.

## Exact boundary

| Item | Identity |
|---|---|
| Current immutable candidate | `pokrov-1.2.0-candidate.31`, app `1.2.0+4053` |
| Candidate operational id | `4ee73886c1a285526baf3b666d5845b426754d8bee9f48365d1550a6ece1dd79` |
| Candidate platform / client / Core | `84837ce68a028f0c81580a5f1beefddba584de6d` / `7e3e771fe36333a75244cbfd828c60beb84c7ff1` / `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Reproducibility correction commit | `1847c7191401a09e6e92de42d4eadd7a0b9159bb` |
| Client `main` merge commit | `ad2a33d14335a5974e089f50946367e8e02372b8` |
| Source tree for both commits | `b7fe9cbd2125dce8a962eca192fd78a4c55ce6b9` |
| Exact Core checkout | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Platform validation root | `1eddf8c792c4f1b588ea7505b30cd92205f68f11` |

The platform identity above is only the explicit cross-repository validation
root used by the successor client build. It does not replace candidate.31's
bound platform source.

## Correction and promotion

The client correction is deliberately narrow:

1. MSVC Release/Profile executable and DLL links use `/Brepro`.
2. The final Flutter package configuration maps the generated registrant to a
   stable relative root before `flutter build windows --no-pub`.
3. The release wrapper maps any clean checkout to a temporary canonical `P:`
   path, fails closed if that drive is already occupied and verifies removal.
4. The pinned Flutter Windows C++ wrapper is staged from the detected SDK into
   the ephemeral build tree.
5. Only stale Windows native-assets state is cleared before the build.

The implementation was merged through client PR 73. Its hosted
`cross-repository-contract` job executed zero steps with `runner_id=0` because
of account Billing/spending-limit state, so it is
`BLOCKED_BY_ACCESS_GITHUB_BILLING`, not a test failure. The authorized
`OWNER_SOLO_EXCEPTION` was used after the complete local replacement evidence
below passed.

Platform PR 208 records this append-only evidence. Its `repo-guardrails` and
`cross-repository-contract` jobs also finish with `runner_id=0`, zero steps and
the exact Billing/spending-limit annotation. They are likewise
`BLOCKED_BY_ACCESS_GITHUB_BILLING`; `release-base-isolation` is `SKIPPED`. The
same authorized solo exception applies after the local docs/link checks pass.

## Reproducibility proof

Two independent worktrees at `1847c719...` and a third freshly recreated
worktree at merged `main` `ad2a33d...` all use the same source tree. The first
two establish the independent build comparison; the third proves that the
merged promotion line preserves it.

| Comparison | Result |
|---|---|
| Reference A vs reference B | `302/302` files exact, zero missing/extra/changed |
| Merged-main build vs reference A | `302/302` files exact, zero missing/extra/changed |
| Reference hash-list SHA-256 | `a0af6445ce9c59a3ca1cfe72bdbbd964057861a0e6abe54fca1f2df2fc253ed1` |
| `pokrov_windows.exe` | `611208b20b68b333d81655b0d6dbd7ada3a213fbfd9a82b6af71b01b3bdf15a2` |
| `pokrov_service.exe` | `b962d3d0c369e24a5d927a4b024148a3b8ceaed0e78efb6aef454f537d4c326b` |
| `data/app.so` | `4ce463e640259e419c74426fe446547d366ae0e935585482ca15a878eeb2c339` |

This proves same-byte reproducibility for the staged Windows bundle on the
retained toolchain and canonical path. It does not make the Inno installer
itself reproducible and does not transfer any release credit to candidate.31.

## Merged-main CLI build and checks

| Surface | Result |
|---|---|
| Version/Core parity | `1.2.0+4053` / exact Core `1.1.0`, `PASS` |
| Seed, facts, version, observability and release logging contracts | `PASS` |
| Repository hygiene, presentation and performance contracts | `PASS` |
| Observability contracts / runtime | `3/3` / `29/29 PASS` |
| Diagnostics / support bundle | `6/6` / `15/15 PASS` |
| App shell | `413/413 PASS` |
| Runtime engine aggregate | `72 PASS`; exact-DLL case separated from the aggregate |
| Exact real Windows Core DLL | `100` start/stop cycles, focused `PASS` |
| Android / Linux / Windows Flutter | `8/8`, `5/5`, `24/24 PASS` |
| Android Gradle | `BUILD SUCCESSFUL`; `162` tasks |
| Windows analyze | `No issues found` |
| Windows native Release CTest | `7/7 PASS` |
| Windows Release bundle and Inno installer | `PASS` |

The Kotlin incremental cache initially reports cross-drive cache paths and
automatically falls back to compilation without its daemon. The Gradle result
is still exact `BUILD SUCCESSFUL`; this warning is not represented as a test
failure.

## Local artifact identity

| Artifact | SHA-256 | Classification |
|---|---|---|
| `pokrov-windows-x64-1.2.0+4053-setup.exe` | `03fb9b6b6e3794721b9ca2305a15d125ce49c5ea9d1748783a9186a5a353eeec` | local unsigned direct-beta installer; not installed |
| `pokrov-windows-x64-1.2.0+4053.manifest.json` | `5d07c323613cb3ec1b28d9700a89a91c3ca4ff183bdcab0b826511e667ef6bf1` | local build manifest |

The installer hash equals its manifest field. Authenticode status is
`NotSigned`, manifest signing status is `SKIPPED_BY_OWNER`, trusted/store claims
are forbidden, and the SmartScreen warning remains mandatory.

## Gate effect, host boundary and cleanup

```text
candidate.31 decision=NO_GO
required=19
pass=2
non_pass=17
fail=1
validation_errors=0
changed=false
```

No screen, mouse, desktop application, host route, DNS setting, tunnel or
production runtime is used. The temporary `P:` mapping is absent after every
run. The older duplicate 6.1 GB build worktree is removed only after its clean
status and resolved path are verified; the final merged-main CLI bundle is
retained. No owner-authored dirty root files are modified.

## Follow-up

The reproducibility blocker from WO-013FY is closed in successor client
`main`. To receive release credit, assemble and sign a newly numbered candidate
from this exact main tree and repeat strict supply validation. Independently,
candidate.31 remains subject to its existing managed Windows, physical
Android, origin, provider, rollback and final Gate F non-PASS rows; this source
proof does not close them.

## Evidence digest

| File | SHA-256 |
|---|---|
| `evidence/013FZ-windows-main-reproducibility/013FZ-windows-main-reproducibility.json` | `28b5809fb9da76f70cb711db159b86b695af850f71f25a3f19f7aff5bbca0c5f` |
| external `FINAL_RESULT.json` | `607bbbc7bfe6ccfcc2408981c0ffdf2743e0058e613cae6bbd5a5142a7da97a7` |
| external `final-canonical-a.sha256` | `a0af6445ce9c59a3ca1cfe72bdbbd964057861a0e6abe54fca1f2df2fc253ed1` |
| external `final-canonical-a.manifest.json` | `f89eb3238a7fd556d2231d991248f37230b9f8123289f5b49568ddf7b76ca014` |

The tracked record contains no token, credential, private key, raw connection
material, customer data or provider response.

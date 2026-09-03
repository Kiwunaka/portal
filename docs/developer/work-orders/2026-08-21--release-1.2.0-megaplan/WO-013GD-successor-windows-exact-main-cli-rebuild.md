# WO-013GD — successor Windows exact-main CLI rebuild

Status: `PASS_LOCAL_PRE_CANDIDATE_WINDOWS_302_OF_302_CANDIDATE_NOT_CREATED`

Observed: `2026-09-03T22:50:00Z`–`2026-09-03T23:00:07Z`

Production/public mutation: `NONE`

## Outcome

The exact merged client `main` revision from WO-013GC was rebuilt through the
canonical Windows release helper using CLI only. The full seed/contracts,
tests, analyze, Android Gradle and Windows Release contour passed; native
Release CTest then passed `7/7` in an independent replay.

The fresh staged Windows bundle contains `302` files and matches the preceding
successor rebuild hash list at `302/302` with zero differing lines. This closes
WO-013GC's narrow Windows-reuse boundary: Windows is now freshly compiled from
the exact merged client `main`, not merely carried across the Android-tooling
delta.

The new Inno Setup container is retained under its own SHA-256, but receives
no same-byte installer claim. The reproducibility claim is restricted to the
complete `302`-file staged product bundle. Authenticode remains `NotSigned` /
`SKIPPED_BY_OWNER` under the existing direct-beta exception, so the canonical
SmartScreen and unknown-publisher warning is still required.

No UI, mouse, host route, host DNS or host tunnel was used or changed. The
installer was not launched. `candidate_created=false`; no candidate.32 input,
candidate-bound SBOM/provenance/handoff, release-index signature, deploy,
public asset or stable pointer was created.

## Exact source boundary

| Repository | Revision | Role |
|---|---|---|
| Platform product source | `3018fd27be57bfa590aac0bc55df949f8a7415ef` | unchanged product source behind the successor local contour |
| Platform ledger head | `d690448096e5d73b787d02b1bba1dd25a59f681a` | append-only WO-013GA/GB/GC evidence |
| Client | `2d6adfcebc37f2109ef339276be6a1569cb7aa1e` | exact merged `POKROV-app/main` and Windows build source |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` | pinned Core `1.1.0` artifacts |
| Release index | `4de2e9f8620b5aac2f538dc8a052a44ad2a563a5` | unchanged published `main`; no candidate input added |

The version remains `1.2.0+4053` in `PRE_CANDIDATE_LOCAL` state.

## Verification

```text
exact client/Core/platform roots                       PASS
canonical full Windows CLI release helper             PASS
seed and cross-repository contracts                    PASS
app_shell Flutter tests                                PASS 413/413
Android Gradle contour                                 BUILD SUCCESSFUL
Windows Flutter analyze                               PASS
Windows Release compilation                            PASS
native Windows Release CTest                           PASS 7/7
staged product bundle comparison                       PASS 302/302
bundle hash-list differing lines                       0
worktree after targeted generated-file restoration     CLEAN
host UI / host network configuration                   NOT_USED / UNCHANGED
candidate / deploy / publication                       NOT_CREATED / NOT_REQUESTED
```

The first direct CTest replay was invoked without the temporary canonical
`P:` mapping baked into CMake's generated test paths and could not open its
log directory. That setup miss is retained separately. Replaying the same
tests with `P:` mapped only to the exact clean client worktree passes `7/7`;
the mapping was validated and removed immediately afterward.

Gradle also lost its Kotlin daemon during the full contour, selected its
documented no-daemon fallback and completed successfully. No daemon or host
restart was performed.

## Windows artifacts

| File | Bytes | SHA-256 | Signing |
|---|---:|---|---|
| `pokrov-windows-x64-1.2.0+4053-setup.exe` | `29154647` | `22689e3e61be82f90b1ba9530cba37628ec546022338fc87018b2d460c020574` | `SKIPPED_BY_OWNER` / `NotSigned` |
| `pokrov-windows-x64-1.2.0+4053.manifest.json` | `5884` | `43bd310e2fb287d2ada339d8938fbe2304261fe23c9d8608124417d05af9e7dd` | manifest |
| `windows-cli-rebuild-bundle.sha256` | `36654` | `69cec9aba4bd18436d905e4d5ab4bf1e103b11795e9d418c5f71bbfc39929cf1` | exact `302`-file identity |

The bundle hash-list SHA-256 exactly matches the preceding successor rebuild
hash-list SHA-256. The fresh setup container hash differs and is deliberately
not used as the product reproducibility boundary.

## Release interpretation

- Exact merged-main Android `5/5` and Windows `302/302` precursor bytes now
  exist for a separately authorized candidate assembly.
- No install, connected runtime, physical-device or candidate credit is
  assigned to this CLI-only evidence.
- Candidate.31 remains the current private signed candidate and its immutable
  Gate F remains `NO_GO 2/17/1`.
- The `378`-row distribution and all completion indices remain unchanged.
- Fresh candidate-bound supply metadata and the six-file strict replay remain
  mandatory only after explicit candidate.32 creation authorization.

## Evidence digests

| File | SHA-256 |
|---|---|
| tracked `013GD-successor-windows-exact-main-cli-rebuild.json` | `52e8ce5f5af1a9e24fc50a9c39a19f88206d5c9ca5569f141c4b845a64fafd3d` |
| external verification report | `398cb95aa94479d26b8a336659f78eeb53e83c37b2352fb0f91e8036fa7a8965` |
| exact-main CLI build log | `e831a864e14e63218fcd9044a612889a88ba8f7563cb043c7d5f64c101036287` |
| passing native CTest log | `0422579575900efee1b0244391d5e44cb293ffa73bebd4bd2853c813fe01d19c` |
| retained first CTest setup miss | `538e11007cad98d879553d7e715f3251222b832ad0b3d84e1cc5581ede6429e8` |

External artifacts and reports are retained under
`E:/POKROV-tools/release-evidence/1.2.0-successor-main-cli-rebuild-2-2026-09-04/`.
The tracked record contains no token, private key, password, raw connection
material, customer data or provider payload.

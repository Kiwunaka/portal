# WO-013GA — successor-main local quality replay and additional Windows CLI rebuild

Status: `SUCCESSOR_SOURCE_LOCAL_QUALITY_PASS_PRE_CANDIDATE_GATE_UNCHANGED_NO_GO`

Observed: `2026-09-03T21:54:54.9869820Z`

Production/public mutation: `NONE`

## Outcome

The exact current successor-source tuple completes a fresh clean local quality
replay after the Windows reproducibility correction was merged. All `15/15`
declared local steps pass across the platform, active client, web cabinet,
adminapp, marketing and static performance owners. The report is explicit that
`candidate_proven=false` and `promotion_status=MANUAL_OWNER_TEST`.

At the owner's request, a separate additional Windows build then runs through
the headless reproducible CLI path. The full client gate, Android Gradle build,
Windows Release build and native Release CTest pass. Its staged bundle matches
the retained merged-main reference at `302/302` files with zero missing, extra
or changed bytes. The unsigned setup is retained as local pre-candidate
evidence and is not installed.

This work order does not create candidate.32, alter immutable candidate.31,
transfer local source credit into an exact candidate, deploy a runtime or
authorize a public/stable release. Gate F therefore remains exact `NO_GO
2/17/1`, and the execution-ledger distribution remains unchanged.

## Exact boundary

| Item | Identity |
|---|---|
| Platform source | `3018fd27be57bfa590aac0bc55df949f8a7415ef` |
| Client source | `ad2a33d14335a5974e089f50946367e8e02372b8` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| App version | `1.2.0+4053` |
| Classification | `PRE_CANDIDATE_LOCAL` |
| Candidate created | `false` |

All three source worktrees were clean when the local quality gate captured its
provenance. The platform revision is the merge of WO-013FZ's append-only
evidence; the client and Core revisions are the exact merged-main pair proved
there.

## Local quality replay

The first attempt is retained rather than rewritten. It reached the client
checks, then frontend commands could not resolve their lockfile-declared tools
because the fresh platform worktree had no `node_modules`. This is classified
`ENV_SETUP_MISS_RETAINED`, not a product failure. The fail-first report SHA-256
is `b48b8f90b661682ba59f40c3d072643a6f8bd94ae9b1aa1cb45537f98092da50`.

The three frontend packages were then installed from their existing lockfiles
with Node `22.14.0` and npm `11.7.0`. Each `npm ci` completed with zero reported
vulnerabilities. The corrected replay produced:

| Surface | Result |
|---|---|
| Performance contract and focused tests | `PASS`; `30/30` tests |
| Client analyze | `PASS` |
| App-shell widget suite | `413/413 PASS` |
| Client seed and docs contracts | `PASS` |
| Webapp lint and production build | `PASS` |
| Cabinet E2E, accessibility and responsive matrix | `69/69 PASS` |
| Marketing build, SEO and responsive/reduced-motion checks | `PASS` |
| Adminapp production build | `PASS` |
| Static web performance | `9/9` measured budgets `PASS` |
| Aggregate | `15/15 PASS` |

The quality report SHA-256 is
`aa7ce47f6e5bbaa042ba3fd521fbc637924a1cdbaa6489690f5024ef3d0074ec`.
Its static web performance evidence SHA-256 is
`f1f716bd5424c676d3b6a5f99ce21fa0f9c9d52ab8b88f003722f340095f38fa`.

## Additional Windows CLI build

The additional build uses `scripts/build-windows-release-reproducible.ps1`
through the canonical temporary `P:` path. No desktop application or
installer is launched. The complete bounded client test contour passes,
including app shell `413/413` and Android Gradle `BUILD SUCCESSFUL`.

Release CTest initially starts after the wrapper has removed `P:` and therefore
cannot open its generated canonical-path log directory. That result is retained
as an environment setup miss. Recreating the same verified temporary mapping
for CTest produces `7/7 PASS`; the mapping is removed in `finally`.

The first build invocation likewise retains a fail-first setup result: the
cross-repository seed validator cannot infer a platform sibling from a drive
root. Passing the exact platform source explicitly closes the invocation gap.
Neither retained setup miss reaches product execution or counts as a product
failure.

| Artifact/check | Result |
|---|---|
| Full client gate | `PASS` |
| Android Gradle | `BUILD SUCCESSFUL` |
| Windows release build | `PASS` |
| Native Release CTest | `7/7 PASS` |
| Reference/current staged bundle | `302/302` exact; zero missing/extra/changed |
| `pokrov_windows.exe` | `611208b20b68b333d81655b0d6dbd7ada3a213fbfd9a82b6af71b01b3bdf15a2` |
| `pokrov_service.exe` | `b962d3d0c369e24a5d927a4b024148a3b8ceaed0e78efb6aef454f537d4c326b` |
| `data/app.so` | `4ce463e640259e419c74426fe446547d366ae0e935585482ca15a878eeb2c339` |
| `pokrov-core.dll` | `f284fa8841f1a45271874a7a05ed6093fb0e3efbdd03e00001edd046be708204` |

The generated installer is `29,154,644` bytes with SHA-256
`c66817238d49e366d143de0580513167b38656c78044f8abc9a7313d67c721ab`.
Its manifest SHA-256 is
`c3f546af9d72499be36fdff05137649d9619ca58ef092d9af89b84eb8cecf649`
and retains `11` required files. Authenticode is `NotSigned`; manifest signing
status is `SKIPPED_BY_OWNER`. The direct-beta SmartScreen warning remains
mandatory.

## Manual lanes and release effect

The local replay keeps the following promotion requirements non-PASS:

| Lane | Status |
|---|---|
| Exact-candidate device performance | `MANUAL_OWNER_TEST` |
| Exact-candidate artifact-size regression | `MANUAL_OWNER_TEST` |
| Browser-lab page performance | `MANUAL_OWNER_TEST` |
| Controlled-origin authenticated API performance | `BLOCKED_BY_ACCESS` |
| Exact-candidate signing/device/origin/post-promotion proof | `MANUAL_OWNER_TEST` |

No execution-ledger row advances. The authoritative distribution stays
`I4=5`, `I3=319`, `I2=20`, `I1=34`, `I0=0`. Candidate.31 and its Gate F
decision remain immutable; candidate.32 does not exist.

## Host boundary and cleanup

The replay uses no screen, mouse or desktop input and does not change the host
route, DNS, active tunnel, service state or production runtime. The installer
is copied into external evidence but never executed. After artifact and log
retention, the dedicated `6.0 GB` client build worktree is removed through its
registered Git worktree boundary. The four owner-authored untracked `.obj`
files in the primary client checkout remain untouched.

## Evidence digest

| File | SHA-256 |
|---|---|
| `evidence/013GA-successor-main-local-quality/013GA-successor-main-local-quality.json` | `e8e89478aca97fc7393b12d8e3bef69f9020fea82ec210688d02c5e36e3547b4` |
| external `010I-local-quality-gate.json` | `aa7ce47f6e5bbaa042ba3fd521fbc637924a1cdbaa6489690f5024ef3d0074ec` |
| external `010I-local-web-performance-evidence.json` | `f1f716bd5424c676d3b6a5f99ce21fa0f9c9d52ab8b88f003722f340095f38fa` |
| external fail-first quality report | `b48b8f90b661682ba59f40c3d072643a6f8bd94ae9b1aa1cb45537f98092da50` |
| external Windows verification report | `1b3e8efc671d0dd086417e5e394cf98831e60bec2090abc6b983f859c86e0d25` |
| external Windows bundle hash list | `69cec9aba4bd18436d905e4d5ab4bf1e103b11795e9d418c5f71bbfc39929cf1` |
| external Windows build log | `fe27e7f24b54c503f4a1e4149d2d5a076244aa5752c903b8a447c1a8539903c9` |
| external Windows CTest log | `3b7b227b365927ff6850c13bff2a252275e382f9282d300af13598e88ce9502a` |

External evidence is retained under
`E:/POKROV-tools/release-evidence/1.2.0-successor-main-gates-2026-09-04/`
and
`E:/POKROV-tools/release-evidence/1.2.0-successor-main-cli-rebuild-2026-09-04/`.
The tracked record contains no token, credential, private key, raw connection
material, customer data or provider response.

# WO-013GB — successor-main exact-source local freeze preflight

Status: `READY_LOCAL_FREEZE_CANDIDATE_NOT_CREATED_PROMOTION_NOT_AUTHORIZED`

Observed: `2026-09-03T22:11:47Z`

Production/public mutation: `NONE`

## Outcome

The read-only exact-source candidate preflight returns `READY_LOCAL_FREEZE` for
the clean current platform/client/Core tuple and the authoritative clean
release-index `main`. It reports zero blockers and zero pre-freeze rows below
`I3`. Exact local Core artifacts match their declared AAR, DLL and libcronet
identities.

`READY_LOCAL_FREEZE` is deliberately narrower than candidate or release
readiness. The report also states `candidate_created=false`,
`candidate_proven=false`, `promotion_authorized=false` and an evidence ceiling
of `LOCAL_READ_ONLY_PREFLIGHT`. The ledger still has `51` rows below `I3`:
`22` candidate-stage, `16` deferred-stage and `13` external-stage rows. None is
converted into a pass.

No candidate.32, release-index commit, signing operation, artifact upload,
deployment, Gate F regeneration or public/stable mutation occurs. Candidate.31
and its exact `NO_GO 2/17/1` decision remain immutable.

## Exact boundary

| Repository | Revision | State |
|---|---|---|
| Platform | `6af24e9aaeee372526bf02e1af98497f5d83ea78` | clean detached `origin/master` |
| Client | `ad2a33d14335a5974e089f50946367e8e02372b8` | clean detached preflight worktree |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` | clean detached worktree |
| Release index | `4de2e9f8620b5aac2f538dc8a052a44ad2a563a5` | clean published `main` |

The application version is `1.2.0+4053`, app-shell product version is `1.2.0`
and Core target is `1.1.0` in `PRE_CANDIDATE_LOCAL` state.

## Fail-first and authoritative rerun

The first invocation intentionally omits `--release-index-root`. It returns
`BLOCKED` with the single honest blocker `release_index_missing` and report
SHA-256
`38de8e4dd8f00eabd83a21aad775154426371e476936d5f1f65fc9c2667227701`.

The local inventory identifies the canonical release-index checkout at clean
published `main` `4de2e9f...`. Repeating the same read-only preflight with that
explicit root removes the only blocker and returns `READY_LOCAL_FREEZE`. The
passing report SHA-256 is
`dde4246b6de3cbce3ef106ba1bc4943b653d85f9baca996039abefb09e6c8e6f`.
No source or release-index file changes between the two invocations.

## Bound contracts and artifacts

| Item | Result |
|---|---|
| Release-index contract | `CONTRACT_READY_PRE_CANDIDATE` |
| Contract SHA-256 | `f58c67af89238af2a126de3150ed60e24b10bdcd7a2bae40bde8cff8bb5a5486` |
| Manifest-schema SHA-256 | `d3724fb84f9ce12b2d3f305205827caca0bd770b025901b02926143e90b05e7c` |
| Active signing keys | `1`; no private material read or used |
| Stage-policy SHA-256 | `c6cfed020f8432daa2ae746fe1bc85b045302652374d6ce8c8421a6a6e543d23` |
| Android Core AAR | exact declared/actual match; `107,419,397` bytes |
| Windows Core DLL | exact declared/actual match; `55,426,048` bytes |
| Windows libcronet DLL | exact declared/actual match; `8,596,992` bytes |

The release-index contract itself retains `candidate_created=false` and
`promotion_authorized=false`. Available signing-key metadata proves only that
the contract has an active public identity; it does not authorize or perform a
signing operation.

## Stage-policy result

The `378`-row ledger has `71` explicit stage-policy overrides. The preflight
finds:

| Stage | Rows below `I3` | Effect on local freeze |
|---|---:|---|
| Pre-freeze | `0` | no local-freeze blocker |
| Candidate | `22` | required after an exact candidate exists |
| Deferred | `16` | remains explicitly deferred/monitor-only |
| External | `13` | requires owner decision, access or deployed evidence |

The `51` total rows below `I3` remain authoritative release work. The local
freeze result does not change their indices, statuses or next actions.

## Host boundary and cleanup

The preflight reads repository state and hashes only. It uses no screen/input,
host network mutation, installer, device, service, production runtime,
database, delivery node or external account mutation. The temporary clean
client preflight worktree is removed after the reports are retained. The four
owner-authored untracked `.obj` files in the primary client checkout remain
untouched.

## Follow-up

The source tuple is eligible for a separately authorized local freeze and new
candidate assembly. It is not authorization to create candidate.32. Before any
promotion, a new exact signed candidate must be explicitly authorized and then
complete its `22` candidate-stage rows plus the applicable external/manual
Gate F evidence. Deferred and monitor-only rows keep their declared policy.

## Evidence digest

| File | SHA-256 |
|---|---|
| `evidence/013GB-successor-main-freeze-preflight/013GB-successor-main-freeze-preflight.json` | `9aaf8cf1ac0a3d70276470ed49670e3ee9cb7093cd2a6ce1e2dfe375211a48eb` |
| external ready preflight | `dde4246b6de3cbce3ef106ba1bc4943b653d85f9baca996039abefb09e6c8e6f` |
| external fail-first preflight | `38de8e4dd8f00eabd83a21aad775154426371e476936d5f1f65fc9c2667227701` |

External reports are retained under
`E:/POKROV-tools/release-evidence/1.2.0-successor-main-preflight-2026-09-04/`.
The tracked record contains no token, credential, private key, raw connection
material, customer data or provider response.

# WO-013GE — successor-current exact-source local freeze preflight

Status: `READY_LOCAL_FREEZE_CANDIDATE_NOT_CREATED_PROMOTION_NOT_AUTHORIZED`

Observed: `2026-09-03T23:09:17Z`

Production/public mutation: `NONE`

## Outcome

The read-only candidate preflight now binds the complete current successor
source tuple after the merged Android helper and fresh exact-main Windows CLI
rebuild evidence. Clean platform `9d92889...`, client `2d6adfc...`, Core
`cd8f0f4...` and published release-index `main` `4de2e9f...` return
`READY_LOCAL_FREEZE` with zero blockers and zero pre-freeze rows below `I3`.

This supersedes WO-013GB only as the latest exact source/preflight tuple. It
does not replace WO-013GB's retained report and does not create release credit.
The current report states `candidate_created=false`,
`candidate_proven=false`, `promotion_authorized=false` and
`evidence_ceiling=LOCAL_READ_ONLY_PREFLIGHT`.

All `51` rows below `I3` remain open under their declared stage policy:
`22` candidate-stage, `16` deferred and `13` external. No row, completion
index or Gate F result changes.

## Exact boundary

| Repository | Revision | State |
|---|---|---|
| Platform and ledger | `9d92889fd606df3a4ee8999d32447adf1d60157b` | clean detached `origin/master` |
| Client | `2d6adfcebc37f2109ef339276be6a1569cb7aa1e` | clean detached preflight worktree; exact merged `main` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` | clean detached worktree |
| Release index | `4de2e9f8620b5aac2f538dc8a052a44ad2a563a5` | clean published `main` |

The application remains `1.2.0+4053`; Core remains `1.1.0`; source state is
`PRE_CANDIDATE_LOCAL`.

## Bound contracts and artifacts

| Item | Result |
|---|---|
| Release-index contract | `CONTRACT_READY_PRE_CANDIDATE` |
| Contract SHA-256 | `f58c67af89238af2a126de3150ed60e24b10bdcd7a2bae40bde8cff8bb5a5486` |
| Manifest-schema SHA-256 | `d3724fb84f9ce12b2d3f305205827caca0bd770b025901b02926143e90b05e7c` |
| Published-main ancestry | `PASS` |
| Active signing-key metadata | `1`; no private material read or used |
| Stage-policy SHA-256 | `c6cfed020f8432daa2ae746fe1bc85b045302652374d6ce8c8421a6a6e543d23` |
| Android Core AAR | declared/actual match; `107,419,397` bytes |
| Windows Core DLL | declared/actual match; `55,426,048` bytes |
| Windows libcronet DLL | declared/actual match; `8,596,992` bytes |

Available public signing-key metadata proves only that the pre-candidate
contract has an active verification identity. It does not authorize or perform
a signing operation.

## Stage-policy result

The `378`-row ledger and `71` explicit overrides produce:

| Stage | Rows below `I3` | Effect |
|---|---:|---|
| Pre-freeze | `0` | local freeze has no source/contract blocker |
| Candidate | `22` | requires a separately authorized exact candidate |
| Deferred | `16` | remains deferred or monitor-only by policy |
| External | `13` | requires deployed access, owner decision or current external evidence |

`READY_LOCAL_FREEZE` does not imply exact-candidate, device, origin, provider,
rollback, legal, commercial or public-promotion proof.

## Host boundary and cleanup

The preflight reads Git state, tracked contracts, stage policy and local file
hashes only. It uses no screen/input, device, installer, service, host-network
mutation, production runtime, provider, database or external account mutation.
The temporary clean client checkout is removed after retaining the report.
The four owner-authored untracked `.obj` files in the primary client checkout
remain untouched.

## Follow-up

The source tuple is eligible for a separately authorized candidate assembly.
It is not authorization to create candidate.32. Candidate creation must bind
the exact six-file application supply to fresh SBOM, provenance and strict-v2
handoff, pass strict replay before signing, and then execute the candidate and
applicable external/manual rows. Candidate.31 remains immutable private signed
history with Gate F `NO_GO 2/17/1`.

## Evidence digest

| File | SHA-256 |
|---|---|
| tracked `013GE-successor-current-freeze-preflight.json` | `da39aeea14c63a102d6dafa6138a50286e080bbd8a499db5585fc687679b0630` |
| external exact-current preflight | `1da6afff9d8ba379ff10cf7baca6f232433cc0ed1e85c763cc1e734ca565170d` |

The external report is retained under
`E:/POKROV-tools/release-evidence/1.2.0-successor-main-preflight-2-2026-09-04/`.
The tracked record contains no token, credential, private key, raw connection
material, customer data or provider response.

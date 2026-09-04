# WO-013GS — successor focus fix local freeze preflight

Status: `READY_LOCAL_FREEZE`

Observed: `2026-09-04T04:47:18Z`

Production/public mutation: `NONE`

## Outcome

The read-only candidate preflight passes with zero blockers on the exact
successor source tuple that contains the Windows focus correction and the
reconciled client/platform release truth.

This result proves only that the committed local sources are ready to freeze.
It does not create, sign or prove a new candidate and does not change the
immutable candidate.32 `NO_GO` verdict.

## Exact tuple

| Repository | Revision | State |
|---|---|---|
| Platform and ledger | `435999a55cf1c601ca41192a9c6792206ff88c4b` | clean |
| Client | `866bd663875d5d3cc4c1682213031f2855a3693b` | clean; includes focus fix `76abed9056282df6436fbd8734f8093baabdb711` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` | clean exact source |
| Release index | `86547e98e6d10ee589a55157b2b26e8fb6a12877` | clean published ancestor of `origin/main` `7a6b2ce859b34b074e877851ba50aae7e80854a3` |

Android and Windows remain `1.2.0+4053`, app-shell remains `1.2.0`, and the
exact Core AAR, DLL and Cronet bytes match their declared identities.

## Stage result

- blockers: `0`;
- pre-freeze rows below `I3`: `0`;
- all rows below `I3`: `51`;
- candidate-stage rows below `I3`: `22`;
- deferred rows below `I3`: `16`;
- external rows below `I3`: `13`;
- external pre-candidate rows below `I3`: `0`.

The checked stage policy is
`pokrov.release-1.2.0.row-stage-policy/v1`, SHA-256
`c6cfed020f8432daa2ae746fe1bc85b045302652374d6ce8c8421a6a6e543d23`.

## Evidence

Raw report:
`E:/POKROV-tools/release-evidence/1.2.0-successor-focus-preflight-2026-09-04/successor-focus-preflight.json`,
SHA-256 `ff09e649ca3703df794378182e5a625bdb60398a4af5ac9dc2a68055c01784be`.

Normalized record:
`evidence/013GS-successor-focus-local-freeze-preflight/013GS-successor-focus-local-freeze-preflight.json`,
SHA-256 `cd2dabb1ab3e2165640fec326f07f39b7e6ebe52c15c6d50a3e34962574f396c`.

## Boundary and follow-up

`candidate_created=false`, `candidate_proven=false` and
`promotion_authorized=false`. No signature, push, deploy, public release,
Store object or stable-pointer mutation occurred.

The tuple is locally ready for normal branch promotion. Creating and signing a
newly numbered candidate remains a separate release-changing action. After
that authority exists, the new exact bytes must repeat `WIN-001`, Windows and
Android runtime, origins, rollback, approval and Gate F checks.

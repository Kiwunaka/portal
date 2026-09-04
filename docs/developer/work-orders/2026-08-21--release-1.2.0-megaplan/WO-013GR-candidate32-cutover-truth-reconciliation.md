# WO-013GR — candidate.32 current cutover truth reconciliation

Status: `PASS_LOCAL_CURRENT_TRUTH_RECONCILIATION`

Observed: `2026-09-04T04:44:01Z`

Production/public mutation: `NONE`

## Outcome

The active client and platform release owners now agree on the current exact
boundary: private signed `pokrov-1.2.0-candidate.32` is immutable `NO_GO`, with
Gate F `2 PASS / 17 non-PASS / 2 FAIL`. Its signed supply remains valid, but
the exact `REL/WIN-001` focus failure prevents promotion.

The client seed and cutover docs previously stopped at candidate.25, while the
platform publishing guide stopped at candidate.23. Those stale current labels
are replaced without rewriting the retained evidence for either predecessor.

## Exact boundary

| Item | Identity |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.32`, `1.2.0+4053` |
| Platform source | `d0dd37c1003198ba08cffc49a040a77e21621a86` |
| Client source | `2d6adfcebc37f2109ef339276be6a1569cb7aa1e` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release index | `5d11fd6821a5ebfa42163f461332125143c553c3` |
| Candidate verdict | `NO_GO 2/17/2` |
| Client focus fix | `76abed9056282df6436fbd8734f8093baabdb711` |
| Client truth commit | `866bd663875d5d3cc4c1682213031f2855a3693b` |
| Platform publishing truth commit | `9ab44eb7d4a92659c1d567a00346f00521352276` |

The focus correction remains `PASS_PRE_CANDIDATE_LOCAL`. It is not part of
candidate.32, does not alter its files or signature and cannot receive exact
candidate credit until a newly numbered candidate is authorized and built.

## Reconciled owners

- `POKROV-app/config/cutover-readiness.seed.json` now owns candidate.32 as the
  exact replacement candidate and retains the `NO_GO` Gate F counts.
- client cutover, Android, Windows and backlog owners distinguish exact
  candidate.32 evidence from the successor source fix.
- the platform publishing guide now names candidate.32 as the current private
  boundary and keeps candidate.22 as the latest bounded `WIN-003` pass rather
  than transferring that pass to newer bytes.
- generic client docs-contract checks now reject inconsistent Gate F counts,
  a `NO_GO` state without an exact failure and any focus-fix relabelled as
  candidate proof.
- the platform docs contract requires the current publishing section to retain
  candidate.32, `NO_GO 2/17/2`, the pre-candidate fix and the newly-numbered
  candidate requirement.

## Verification

- client docs contract: `PASS`;
- full client `validate-seed.ps1` against exact Core: `PASS`;
- platform agent docs/context tests: `33/33 PASS`;
- platform context audit: `PASS`;
- platform link check: `PASS`;
- `git diff --check`: `PASS`;
- secret-like diff scan: `0`.

## Index and mutation boundary

No completion index changes. Distribution remains `I4=7`, `I3=320`, `I2=19`,
`I1=32`, `I0=0` across `378` unique rows. No candidate, signature, push,
deploy, public asset, Store object, stable pointer or Gate G action is created.

Evidence:
`evidence/013GR-candidate32-cutover-truth-reconciliation/013GR-candidate32-cutover-truth-reconciliation.json`,
SHA-256 `b9dd19d5334bdd40e539d6c14581e5c1214ff51c3a7456b612aa49059332e6ca`.

## Follow-up

Keep candidate.32 immutable. The next release-changing action is to promote
the validated focus correction through the client/platform branches and, only
under separate candidate authority, create and sign a newly numbered exact
candidate. That candidate must repeat `WIN-001` and all applicable Windows,
Android, origin, rollback, approval and Gate F checks.

# WO-013A2 — Exact candidate stage matrix

Status: `COMPLETE_LOCAL_PREFLIGHT_CONTRACT`
Classification: `ACTIVE_EXECUTION`
Phase: `11`
Lane: platform release preflight
Depends on: `WO-001`, `WO-013A`, current 377-row ledger
Production/external actions: `NOT_AUTHORIZED`

## Outcome

Replace the circular candidate-preflight heuristic with one versioned,
machine-validated stage policy keyed only by exact `(plan,id)`. The preflight
no longer treats every Gate/DoD/P11 row as a reason that candidate bytes cannot
be created. It also no longer lets ordinary P01–P10 source gaps pass merely
because they are outside those broad buckets.

## Contract

`shared/release-1.2.0-candidate-stage-policy.json` defines four stages:

- `pre_freeze`: must reach local `I3` before candidate creation;
- `candidate`: requires exact candidate bytes/environment and therefore cannot
  block creation of those bytes;
- `external`: requires owner/access/provider/legal/production/origin evidence,
  with an exact `pre_candidate` or `post_candidate` gate;
- `deferred`: explicitly outside release-bound 1.2.0 scope or conditional on a
  later product decision.

The default is deliberately `pre_freeze`. New ledger rows cannot silently
become candidate/deferred/external work: an exact override and reason must be
added. The validator rejects unknown keys, duplicate overrides, missing or
invalid external timing, unsupported fields/stages, non-377 ledgers and a
non-safe default. It does not parse `summary`, `status` or free-form
`next_action` to decide the stage.

## Current matrix

After `WO-008H`, the `99` rows currently below `I3` split as follows:

- `29` are `pre_freeze` local work;
- `32` are `candidate` proof;
- `17` are `external`, including `3` explicit `pre_candidate` blockers;
- `21` are `deferred` by current source/product authority.

The three external pre-candidate rows are platform/client/Core branch
protection/required checks and the separate public release-index trust surface.
The current report has seven blockers: three dirty worktrees, missing release
index, pending exact Core replacement artifact, 30 local pre-freeze rows and
three unresolved external pre-candidate rows. Candidate and deferred rows do
not create a circular local-freeze blocker.

## Acceptance evidence

- Focused preflight unit regression: `9/9 PASS`.
- Ruff check and format check for the script/tests: `PASS`.
- Live read-only preflight after `WO-004A2`: `BLOCKED`,
  `candidate_created=false`, seven blockers, `31/32/17/21` pending stage
  distribution.
- The later `WO-004B2` ledger update leaves the current report `BLOCKED` with
  seven blockers and `30/32/17/21`; no historical evidence was relabelled.
- The later `WO-008H` product-facts closure leaves the current report `BLOCKED`
  with seven blockers and `29/32/17/21`; retained 013A2 evidence stays historical.
- Platform documentation/preflight regression, context audit, link check,
  policy/preflight JSON parse and `git diff --check`: `PASS`.
- No candidate metadata, artifact, release index, commit, branch setting,
  server, deploy, signing or publication was created or mutated.

Machine evidence:
`evidence/013A2-candidate-stage-matrix/013A2-candidate-stage-matrix.json`.

## Ledger effect

This work itself advanced no product row; its retained machine evidence records
the closure-time `I3=274`, `I2=36`, `I1=47`, `I0=20` distribution. `WO-004A2`
later advances two pre-freeze rows, `WO-004B2` advances one and `WO-008H`
advances one, so the current distribution is `I3=278`, `I2=34`, `I1=45`,
`I0=20`; `99` rows remain below `I3`. The stage policy and its digest are
unchanged.

## Rollback

Revert the policy, loader/validator, stage-aware report fields and tests as one
unit. Do not restore the old plan/phase heuristic: it was both circular for
exact-candidate rows and permissive for ordinary source gaps.

## Current amendment

`WO-013A3` adds one exact `OBS_PB/PB-14 -> candidate` override after the signed
manifest/cohort dependency was reconciled. Retained counts and digest above
remain execution-time evidence for this WO; current policy truth is the live
policy file and latest preflight report.

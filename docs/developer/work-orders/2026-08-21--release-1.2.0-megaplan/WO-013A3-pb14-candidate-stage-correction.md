# WO-013A3 — PB-14 candidate-stage correction

Status: `COMPLETE_LOCAL_PREFLIGHT_CONTRACT`
Phase: `11`
Ledger rows advanced: none
Promotion: `NOT_REQUESTED`

## Outcome

Remove one circular local-freeze blocker without weakening the fail-safe stage
policy. `OBS_PB/PB-14` requires a signed-manifest cohort and an observed health
breach that stops promotion or initiates rollback for one exact candidate. It
cannot be proved before that candidate identity exists.

## Contract change

- `OBS_PB/PB-14` moves from the fail-safe default `pre_freeze` stage to an
  exact `(plan,id)` `candidate` override.
- The default remains `pre_freeze`; unknown rows still fail safe.
- The regression pins the override count at 71 and asserts the exact PB-14
  assignment.
- No other remaining row moved. `OC-100`, subscription/checkout rows and their
  aggregate stay `pre_freeze` because their local implementation gaps can be
  closed before candidate creation. True clean-freeze rows also stay in place.

## Local proof

- Candidate-preflight regression: `9/9` PASS.
- Live explicit-root preflight: expected `BLOCKED`, seven blockers,
  `candidate_created=false`.
- Pending stage split: `10/33/17/21`; external pre-candidate blockers remain 3.
- Ledger distribution is unchanged at `I3=296`, `I2=24`, `I1=40`, `I0=17`.

Machine evidence:
`evidence/013A3-pb14-candidate-stage-correction/013A3-pb14-candidate-stage-correction.json`.

## Evidence ceiling

This is a stage-classification correction, not evidence that PB-14 passed. No
candidate, signed manifest, cohort, health breach, promotion stop, rollback,
deployment, publication or external mutation occurred.

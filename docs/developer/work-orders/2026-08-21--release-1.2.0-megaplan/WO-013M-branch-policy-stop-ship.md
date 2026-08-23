# WO-013M — Full branch-policy STOP-SHIP gate

Status: `PASS_LOCAL_VERIFIER_LIVE_NO_GO_OWNER_PLAN_AND_REVIEWER_BLOCKED`
Phase: `01`, `11`
Rows: `REL/REL-001`, `REL_DOD/DOD-09`
GitHub mutation: `NOT_AUTHORIZED`

## Outcome

The existing STOP-SHIP audit could prove strict required-check names but did
not reject a branch that omitted reviews, Code Owners, signatures, admin
enforcement or anti-bypass controls. Platform commit
`dfa96eb7e1139d7f41833f3cc70fb1b57b12c15e` closes that false-pass path.

The canonical registry and read-only gate now require all of the following on
platform `master`, client `main` and Core `main`:

- every named check is strict and bound to a concrete GitHub App;
- at least one approving review from someone other than the last pusher;
- stale-review dismissal, required Code Owner review and last-push approval;
- admin enforcement, signed commits and linear history;
- conversation resolution;
- disabled force pushes and branch deletion;
- an eligible non-author reviewer selected in the contract;
- live `.github/CODEOWNERS` coverage for both `*` and its own `.github`
  control surface.

The required checks are exact: platform `repo-guardrails` and
`cross-repository-contract`; client `cross-repository-contract`; Core `test`,
`release-contract`, `android-artifact-reproducibility`,
`windows-artifact-reproducibility` and `apple-source-build`.

## Clean exact audit

The authenticated read-only run binds clean sources:

- platform `dfa96eb7e1139d7f41833f3cc70fb1b57b12c15e`;
- client `8c6b955dced3b018825c53fe5d14cb632271adeb`;
- Core `fcb3c8bbc6efdeed284417369aacb522722ebfa2`.

All seven permanent source anchors pass. Live promotion controls remain:

- `Kiwunaka/portal:master`: `BLOCKED_BY_ACCESS` on the private plan;
- `Kiwunaka/POKROV-app:main`: `BLOCKED_BY_ACCESS` on the private plan;
- `Kiwunaka/pokrov-core:main`: `FAIL_UNPROTECTED`;
- eligible non-author reviewer count: `0` in each repository;
- selected Code Owners: `0`; reviewer state:
  `BLOCKED_BY_OWNER_DECISION` in each repository;
- exact-candidate WIN-003 clean-host gate: `NOT_RUN`.

The aggregate is therefore `NO_GO`, not a partial PASS. The 6,198-byte report
has SHA-256
`b49fff4235a5a7030e88aa209c595826d4f8ce6c0d9c5c5de99a6d94dd7981a8`.
The registry SHA-256 is
`47dbec986eb788683067e45c55d39632257f758898a457151e77f066441cd589`.

Focused gate and script-manifest tests pass `13/13`; Ruff check/format,
script-manifest validation and diff check pass.

## Index decision and owner handoff

`REL/REL-001` and `REL_DOD/DOD-09` remain `I1`. A stronger local verifier does
not protect a remote branch. Distribution remains `I3=303`, `I2=20`, `I1=39`,
`I0=15`; 74 of 377 rows remain below `I3`, and stage counts remain
`3/33/17/21` for pre-freeze/candidate/external/deferred.

The owner must select or invite at least one trusted non-author reviewer with
write access, place the selected principal in the registry and a reviewed
`.github/CODEOWNERS` in every repository, enable a plan/visibility supporting
private protection, then apply and read back the full policy. Only an exact
live `PASS` may advance these rows.

No collaborator invitation, plan change, CODEOWNERS guess, branch setting,
push, PR, candidate, signature, deployment or promotion occurred.

# WO-013K — Isolated PR-00 release-base result

Status: `PASS_RELEASE_BASE_ISOLATED_PENDING_HOSTED_PR`
Phase: `01`, `11`
Row: `FE_PR/PR-00`
Push/PR: `NOT_AUTHORIZED`

## Outcome

Dedicated platform branch `codex/1.2.0-pr00-true` starts at the exact source
plan/promotion revision
`280ed9157f5804d4bc719cb8d6cab471caafb937` and contains one commit:
`1632234bb78d18b09fa83cd02249d27859b1c409`. Its tree is
`3df581814bca498bfab102be0a843f6e741ec4ab`.

The actual `origin/master..HEAD` diff contains exactly nine contract, snapshot,
validator, test and hosted-workflow paths. It contains zero paths under the
AdminApp, Marketing, WebApp or legacy portal UI prefixes.

## Withdrawn local-parent proof

Earlier commit `dcfbbce17886277bd79ee1c9749c15dc64aa6508` was isolated only
relative to local aggregate parent `9567299...`. Against the real promotion
base it contained 514 paths, including 121 visible UI paths. Its prior
`PASS_LOCAL_ISOLATED_NO_VISIBLE_UI` label is withdrawn and receives no PR-ready
credit. Retaining that correction prevents a local parent from substituting
for the actual pull-request target.

## Bound acceptance

The corrected branch freezes all eight source-plan PR-00 requirements:

- platform/client release branches and exact source-plan base revisions;
- explicit pre-candidate, promotion, Linux, ABI v3, public-index and no-UI
  flags;
- exact Git-blob snapshots of the strict manifest schema, product facts,
  reason-code draft and client motion semantics;
- promotion-base-aware single-commit and no-visible-UI diff policy.

The snapshots preserve exact bytes for review but do not replace their runtime
canonical owners or create another mutable truth.

## Credited checks

- validator: `PASS_RELEASE_BASE_ISOLATED_NO_VISIBLE_UI`;
- target and merge base: exact `280ed915...`;
- promotion diff: `9/9` allowlisted paths, `0` visible UI paths;
- exact snapshots: `4/4` size and SHA-256 identity plus semantic checks;
- validator unit tests: `3/3 PASS`;
- Ruff check and format check: `PASS`;
- scoped diff check: `PASS`.

The 1,034-byte validator JSON output has SHA-256
`4098f52226694f15787620954b59435a73e89839ef07e338f1ffa0f20eab6a31`.
The retained summary is
`evidence/013K-pr00-isolated-result/013K-pr00-isolated-result.json`.

## Index decision

`FE_PR/PR-00` remains `I2`. The real release-base isolation gap is now closed
locally, but branch push, hosted workflow, review and required checks remain
`NOT_RUN`. Distribution stays `I3=303`, `I2=20`, `I1=39`, `I0=15`; 74 of 377
rows remain below `I3`, and stage counts stay `3/33/17/21` for
pre-freeze/candidate/external/deferred.

## Evidence ceiling and next action

This result proves one release-base-isolated local commit. It does not prove a
hosted PR, review, required checks, branch protection, public release index,
owner key, candidate, signature, device/origin run, publication or promotion.

After owner authorization, push exact branch `codex/1.2.0-pr00-true`, create a
PR to `master` and retain the dedicated Ubuntu workflow plus required review
for exact revision `1632234...`. Any target-branch movement must rerun the
validator; do not credit the withdrawn `dcfbbce...` branch.

# WO-013K — Isolated PR-00 local result

Status: `PASS_LOCAL_ISOLATED_PENDING_HOSTED_PR`
Phase: `01`, `11`
Row: `FE_PR/PR-00`
Push/PR: `NOT_AUTHORIZED`

## Outcome

The dedicated platform branch `codex/1.2.0-pr00-freeze` contains exactly one
commit over platform source-freeze revision
`9567299b1d16a7499cbfb3cd08490deacfaca2ab`:
`dcfbbce17886277bd79ee1c9749c15dc64aa6508`. Its tree is
`fbc407ef3f51b347ea71163d9f8c5ce99d9f8216`.

The commit changes exactly four evidence-only paths: the branch-local work
order, its machine contract, the validator and two focused validator tests.
The diff contains no path under the AdminApp, Marketing, WebApp or legacy
portal UI prefixes.

## Bound acceptance

The branch-local contract binds the source plan's eight PR-00 requirements:

- promotion branches and exact baseline/source revisions;
- pre-candidate, candidate and promotion flags;
- strict release manifest schema;
- deterministic product-facts snapshot and client projection;
- stable reason-code catalog/schema;
- client motion and reduced-motion semantics;
- an exact no-visible-UI diff policy.

It independently hashes 12 canonical files across platform, client and the
unpublished release index. It also binds exact client
`8c6b955dced3b018825c53fe5d14cb632271adeb`, Core
`fcb3c8bbc6efdeed284417369aacb522722ebfa2` and release-index
`f07654af496d042fa8dba3d8b2695e987c8e9eb7` revisions. All four worktrees
were clean during the credited run.

## Credited checks

- PR-00 validator: `PASS_LOCAL_ISOLATED_NO_VISIBLE_UI`;
- exact changed paths: `4/4` allowed, `0` visible UI paths;
- canonical inputs: `12/12` exact size and SHA-256 identity;
- validator unit tests: `2/2 PASS`;
- Ruff check and format check: `PASS`;
- scoped diff check: `PASS`.

The 607-byte validator JSON output has SHA-256
`95a9449c79619fe30319dc70df86895877d9e199a1811df77077fcdffa0f53c1`.
The retained summary is
`evidence/013K-pr00-isolated-result/013K-pr00-isolated-result.json`.

## Index decision

`FE_PR/PR-00` remains `I2`. The local isolated commit closes the previous
cross-slice/isolation evidence gap, but hosted review and required checks are
`NOT_RUN`; the branch is not pushed and no PR exists. Distribution therefore
remains `I3=303`, `I2=20`, `I1=39`, `I0=15`; 74 of 377 rows remain below
`I3`, and stage counts remain `3/33/17/21` for
pre-freeze/candidate/external/deferred.

## Evidence ceiling and next action

This result proves one local evidence-only commit. It does not prove a hosted
PR, review, required checks, branch protection, public release index, owner
key, candidate, signature, device/origin run, publication or promotion.

After owner authorization, push the exact branch, create/review the PR and
retain required-check results for exact revision `dcfbbce...`. Do not replace
that operation with a new aggregate diff or credit unrelated hosted runs.

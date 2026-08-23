# WO-013K — Isolated PR-00 freeze/contracts proof

Status: `LOCAL_ISOLATED_COMMIT_PENDING_HOSTED_PR`
Phase: `01`
Row: `FE_PR/PR-00`
Push/PR: `NOT_AUTHORIZED`

## Outcome

Prepare one local PR-ready commit whose diff contains only the PR-00 proof,
validator, tests and work order. Bind the source plan's release branches,
baseline SHAs, release flags, manifest schema, product-facts snapshot,
reason-code contract and motion semantics by exact file identity without moving
or duplicating their canonical ownership. Reject any visible UI path in the
commit.

## Bound source truth

The machine evidence at
`evidence/013K-pr00-isolated/pr00-freeze.json` binds:

- promotion branches `platform/master`, `client/main`, `Core/main` and public
  release-index `main`;
- the pre-PR platform base `9567299b1d16a7499cbfb3cd08490deacfaca2ab`,
  clean client `8c6b955dced3b018825c53fe5d14cb632271adeb`, Core
  `fcb3c8bbc6efdeed284417369aacb522722ebfa2` and local release-index
  `f07654af496d042fa8dba3d8b2695e987c8e9eb7`;
- the initial baseline file, strict release-handoff schema, product facts,
  error catalog/schema, stop-ship and candidate-stage policies, current client
  release/runtime flags, motion semantics and public-index contract;
- exact `PRE_CANDIDATE_LOCAL`, Core 1.1.0 bound-artifact,
  candidate/promotion=false, unpublished-index and zero-active-key states.

## Isolation rule

The validator requires exactly one commit over the recorded base and exactly
four changed files: this work order, its evidence JSON, the validator and its
test. It rejects any extra path and explicitly rejects `adminapp/`,
`marketing/src/`, `webapp/`, `portal_bot/static/` or `portal_bot/templates/`.
It also requires all four repository worktrees and exact referenced inputs to
be clean and byte-identical.

## Evidence ceiling

Passing the validator proves a local isolated no-visible-UI commit only. It
does not create a hosted PR, required-check result, protected-branch readback,
candidate, signature, publication or promotion. `FE_PR/PR-00` cannot advance
to `I3` until the exact commit is reviewed through hosted required checks or an
owner explicitly changes that acceptance rule.

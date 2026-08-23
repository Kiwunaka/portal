# POKROV 1.2.0 PR-00 — real release-base freeze

Status: `MERGED_HOSTED_PASS`
Target: `Kiwunaka/portal@master`
Target revision: `280ed9157f5804d4bc719cb8d6cab471caafb937`
External actions: `AUTHORIZED_FOR_GIT_PUSH_PR_AND_ACTIONS_SECRET`
Pull request: `https://github.com/Kiwunaka/portal/pull/18`
PR head: `e26fcb0b3581c8b0261db29812563085b8fb90a9`
Merge commit: `8cef00ace333d9164d7ac9f4a0856eb7fa88f173`

## Outcome

Create the actual PR-00 from the source plan's recorded platform promotion
base. Freeze the two release branches, exact base SHAs, release flags,
manifest schema, product-facts snapshot, reason-code draft and motion semantics
without changing a visible UI path.

The immutable snapshots are evidence inputs for later implementation PRs.
They do not replace the runtime canonical owners and must not be imported as a
second mutable truth.

## Why the earlier local proof was withdrawn

Commit `dcfbbce17886277bd79ee1c9749c15dc64aa6508` changed only four files
relative to local aggregate revision `9567299...`, but a real pull request to
`origin/master` would contain 514 paths, including 121 visible UI paths. It is
therefore not PR-00-ready and receives no isolation credit.

This branch starts directly at the plan's platform base
`280ed9157f5804d4bc719cb8d6cab471caafb937`. The validator compares the exact
commit to that promotion base, not to an arbitrary local parent.

## Frozen inputs

- platform release branch `release/1.2.0-frontend`, base `280ed915...`;
- client release branch `release/1.2.0-frontend`, base `ba7930e...`;
- Core stays on `main`; `release/1.2.0-ui-contract` is conditional on ABI work;
- public index is created only after signed artifacts;
- candidate/promotion/publication false, Linux non-shipment and ABI v3
  non-blocking flags;
- exact Git-blob snapshots of manifest schema, product facts, reason codes and
  client motion semantics from the active local release work.

## Acceptance

`scripts/validate_release_1_2_pr00.py` requires:

- the exact promotion target and merge base;
- exactly one commit over that base;
- exactly the ten allowlisted contract/evidence paths;
- zero visible UI paths;
- exact snapshot sizes and SHA-256 identities;
- parseable schema/facts/catalog inputs and required bounded motion markers;
- `candidate_created=false`, `promotion_authorized=false` and hosted checks
  honestly `NOT_RUN`.

The dedicated Ubuntu workflow and repository guardrails passed on PR 18. The
PR was merged to `master` at `8cef00ace333d9164d7ac9f4a0856eb7fa88f173`.
The retained PR-00 job is now scoped to the exact PR-00 head branch or explicit
manual dispatch so it cannot misclassify unrelated future pull requests as
PR-00. This is source-review evidence only: no candidate, deployment,
publication or promotion occurred.

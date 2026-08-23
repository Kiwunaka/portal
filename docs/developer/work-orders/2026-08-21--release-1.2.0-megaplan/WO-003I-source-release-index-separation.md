# WO-003I — Source, retained history and release-index separation

Status: `IMPLEMENTED_LOCAL_I2`
Phase: `01`
Ledger row: `REL/REPO-001`
Promotion: `NOT_REQUESTED`

## Intent

Remove exact tracked temporary helpers without erasing evidence, and make the
client source tree fail closed against future candidate/build output being
mistaken for the separate signed public release index.

## Implemented boundary

- The platform and Core exact tracked-file inventories contain no temporary or
  build-output paths. The client inventory identified only two tracked
  `packages/app_shell/.tmp/` helpers; both are deleted by a reviewable Git patch.
- `artifacts/releases/**` remains unchanged. Its 138 files and
  4,642,837,966 bytes are retained release lineage, rollback material and
  version-scoped evidence, not active source or a destination for 1.2.0.
- The three client-host runtime dependencies remain intentionally tracked and
  hash-owned by `config/runtime-artifacts.seed.json`: one Android AAR and two
  Windows DLLs.
- Android and Windows builds remain under ignored `apps/**/build/**`. Optional
  client-local handoff assembly has one ignored
  `artifacts/candidate-staging/**` path.
- `scripts/new-release-handoff-v2.ps1` rejects retained history and every other
  tracked client-tree destination. It still accepts caller-owned temporary
  paths or a separate release-index checkout.
- `test/repository-hygiene-contract.ps1`, invoked by the standard client gate,
  checks the Git boundary, active runtime allowlist, current development target,
  required ignore rules and explicit documentation markers.
- The client root overview now states retained public `1.1.6` / `1.1.6+29`,
  development `1.2.0+30` `PRE_CANDIDATE_LOCAL`, and `candidate_created=false`
  semantics without treating retained history as a new candidate.

## Retained local proof

- Repository hygiene: `PASS`; the two exact temp helpers are absent from the
  clean client commit, retained history is unchanged and the three active
  runtime binaries remain hash-owned.
- Strict-v2 client contract: `PASS`, 16 cases including retained-history and
  tracked-source destination rejection.
- Release-v2 CI source contract: `PASS`.
- Client documentation contract: `PASS`.
- Full client seed, package/Core/version, observability, source logging,
  strict-v2, CI, repository, presentation, performance and docs gate: `PASS`.
- Platform documentation/context tests: `PASS`, `32/32`; platform context audit
  and link check: `PASS`.
- Clean client source freeze: commit
  `551c6e1fb9977560fc2660d4562e08fe69a89742`; the standard client gate and
  cross-repository seed validation pass with a clean worktree.
- Candidate preflight: expected `BLOCKED`, five blockers,
  `candidate_created=false`, 74 rows below `I3`.
- `git diff --name-only -- artifacts/releases`: empty.

Evidence:
`evidence/003I-source-release-index/003I-source-release-index.json`.

## Evidence ceiling

The deletion and executable source boundary now exist in the exact clean client
commit `551c6e1fb9977560fc2660d4562e08fe69a89742`. The public release-index
repository is still unavailable, so its ownership, signature policy and exact
revision cannot be inspected or frozen. `REL/REPO-001` therefore remains at
`I2`: a clean source commit does not prove the separate signed public index,
candidate (`I4`) or release (`I5`). No signing, publication, deployment or
promotion was requested or performed.

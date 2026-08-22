# WO-013H — Clean source freeze and honest blocked preflight

Status: `COMPLETE_LOCAL_EVIDENCE_NO_LEDGER_ADVANCEMENT`
Phase: `11`
Rows reviewed: `REL/TEST-001`, `REL/REPO-001`, `FE_PR/PR-00`
Promotion: `NOT_AUTHORIZED`

## Outcome

Freeze exact clean platform, active-client and Core source revisions after the
complete bounded local gates pass. Retain the remaining blockers without
calling the clean source tuple a release candidate.

## Frozen source identities

- Platform: `1ac65cb501a4f3866d2515855b7d168b88b99a25` on
  `codex/1.2.0-phase00`.
- Active Android/Windows client:
  `551c6e1fb9977560fc2660d4562e08fe69a89742` on
  `codex/1.2.0-release-v2`.
- Core: `fcb3c8bbc6efdeed284417369aacb522722ebfa2` on
  `codex/1.2.0-release-v2`.

All three worktrees are clean. These commits are local source identities. No
candidate metadata, candidate artifact, signature or public release-index
revision exists.

## Local proof

- Core full standard gate: PASS with pinned Go `1.25.13`; formatting, ABI,
  observability, AWG2 and release-CI contracts pass on the clean Core commit.
- Client full standard gate: PASS on the clean client commit, including the
  app-shell, observability/runtime packages, Android/Windows Flutter suites and
  direct/store Android Gradle tests. The cross-repository seed contract also
  passes against the frozen platform/Core sources.
- Platform canonical release pytest matrix: `674 passed`, `38 subtests passed`,
  `19` deprecation warnings. The bounded dependency contract, generated
  75-operation Admin API v2 OpenAPI/TypeScript SDK, platform context audit,
  docs/preflight tests, compileall, unified local WebApp/Marketing/AdminApp
  quality gate and `git diff --check` pass.
- The staged platform change manifest covered 502 files and had SHA-256
  `3c081ee259b0d9d2dc93ecbfcef6835145cb1684e594430f6000415c017558d2`.
  The only staged binaries were eight intentional cabinet Playwright visual
  snapshots; no untracked file exceeded 2 MiB and no key, archive, package or
  executable artifact was included.
- An unbounded repository-wide pytest diagnostic was stopped at 6% after no
  observed failures because it was outside the router's bounded release gate
  and projected to take hours. It is `NOT_CREDITED_OVERSCOPED_ABORTED`; only the
  complete 674-test canonical matrix is credited.

Machine evidence:
`evidence/013H-clean-source-freeze/013H-clean-source-freeze.json`.

## Index decision

No ledger row advances. Distribution remains `I3=303`, `I2=19`, `I1=40`,
`I0=15`; 74 of 377 rows remain below `I3`. Pending stage counts remain
`3/33/17/21` for pre-freeze/candidate/external/deferred.

- `REL/TEST-001` remains `I2`: the clean local standard gate passes, but hosted
  Ubuntu execution is `NOT_RUN`.
- `REL/REPO-001` remains `I2`: the client source boundary is clean, but the
  separate signed public release index is `BLOCKED_BY_ACCESS`.
- `FE_PR/PR-00` remains `I2`: the clean commits contain the broad 1.2.0 wave,
  including visible UI changes, and do not prove an isolated no-visible-UI PR
  with hosted required checks.

## Clean preflight result

The read-only exact-candidate preflight returns expected `BLOCKED` with
`candidate_created=false` and five blockers:

1. `release_index_missing` — `BLOCKED_BY_ACCESS`;
2. `client_core_seed_revision_stale` — `BLOCKED_LOCAL_ARTIFACT`;
3. `core_replacement_artifact_pending` — `BLOCKED_LOCAL_ARTIFACT`;
4. `ledger_pre_freeze_incomplete` — three rows;
5. `ledger_external_pre_candidate_incomplete` — three rows.

The prior dirty-platform blocker is closed. The five remaining blockers are
real release inputs, not documentation gaps.

## Evidence ceiling

This is `LOCAL_READ_ONLY_PREFLIGHT` evidence. No push, hosted CI, public index,
artifact replacement, trusted signing, device/VM run, provider call, payment,
OIDC exchange, server mutation, deployment, publication, campaign, RU-origin
claim or promotion occurred. Candidate and promotion authorization remain
false.

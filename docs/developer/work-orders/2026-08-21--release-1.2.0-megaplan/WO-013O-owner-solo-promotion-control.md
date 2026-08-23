# WO-013O — Owner-solo promotion control

Status: `COMPLETE_POLICY_EXECUTION_CLOSED_BY_WO_013P`
Phase: `01`, `11`
Rows: `REL/REL-001`, `REL_DOD/DOD-09`, `FE/P12-023`
Candidate: `NOT_CREATED`
Production mutation: `NOT_AUTHORIZED_NOT_RUN`

Subsequent closure: `WO-013P` retains the final platform/client/Core PR heads,
required app-bound checks, signed promotion commits and post-merge runs. The
pending state recorded below is the pre-promotion observation preserved by
this WO; `REL/REL-001` and `REL_DOD/DOD-09` now close at `I3` in `WO-013P`.

## Outcome

The sole repository owner explicitly authorized an `OWNER_SOLO_EXCEPTION` for
release 1.2.0 on `2026-08-23`. The release process no longer invents or waits
for a second GitHub account. It also does not relabel self-review as independent
review: every gate record states `independent_review_performed=false`.

The normal team-review policy remains the future baseline. The scoped 1.2.0
exception waives only:

- an eligible non-author pull-request approval;
- non-author CODEOWNERS selection;
- paid private-branch protection unavailable on the current plan.

The replacement is fail-closed. A private promotion branch is acceptable only
when the read-only gate binds a PR authored by `Kiwunaka` to its exact 40-hex
head revision and observes every named check completed successfully by a
GitHub App. Wrong owner, base, revision, PR state, missing check, failed check
or unbound check is a failure. PR-only promotion, signed public release index,
retained candidate evidence and same-byte promotion remain mandatory.

The exception expires when release 1.2.0 is closed. It does not authorize a
production deploy, payment action, campaign, stable-pointer change or public
release by itself.

## Live branch control

The public Core repository supports the solo-safe subset, so its `main` branch
was protected and read back with:

- strict GitHub Actions checks `test`, `release-contract`,
  `android-artifact-reproducibility`, `windows-artifact-reproducibility` and
  `apple-source-build`, all bound to GitHub Actions app id `15368`;
- admin enforcement, signed commits, linear history and resolved
  conversations;
- force pushes and deletion disabled;
- no fake pull-request approval requirement.

The clean live audit at platform commit
`2708bf6ac6bf572ec1aca94eab5f83d6b24d7347` binds client
`66d82be70e32ba3d9650c250c92750ac264cba0f` and current Core
`0e6b0204d764ae6b1d726343f487a7004d13393b`. All seven permanent source
anchors pass. Live branch results are:

- `Kiwunaka/portal:master`: `BLOCKED_BY_ACCESS` on the private plan;
- `Kiwunaka/POKROV-app:main`: `BLOCKED_BY_ACCESS` on the private plan;
- `Kiwunaka/pokrov-core:main`: `PASS` with the solo-safe live policy;
- all three reviewer records: `OWNER_SOLO_EXCEPTION`, with independent review
  explicitly false;
- exact PR evidence: `NOT_RUN` until the final platform/client/Core source PRs
  exist;
- exact-candidate WIN-003 clean-host evidence: `NOT_RUN`.

The aggregate is `BLOCKED`, not `PASS`, because the exact PR bindings and
Windows manual candidate proof do not exist yet. The 7,905-byte read-only
report has SHA-256
`1a8ef3e2cd3b7aeb82cc4337aadc3b930a737781e4c37afe4f1d9b19f7541546`.
The registry SHA-256 is
`b4d997bc0c3544b3d62627de4ed2986fbace87e281ccf2150982df1e62fca954`.

Focused release/script/docs verification passes `81` tests plus `21`
subtests. Ruff check/format, script-manifest validation, link validation,
platform-context audit and diff check pass.

## Index decision and next release step

`FE/P12-023` advances `I2 -> I3`: the public trust surface, Ed25519 public
root, hosted source-contract run and exact public readback were already proved
in `WO-013N`; the sole owner's explicit exception now resolves the only missing
non-author-review precondition without claiming a second reviewer. Exact
candidate assets and detached signature readback remain later `I4` evidence.

`REL/REL-001` and `REL_DOD/DOD-09` remain `I1`. Their owner/plan decision is
resolved, but the exact platform, client and Core promotion PR heads and named
check readback are not yet available. They advance only after one complete
`owner-solo-pr-evidence.v1` file passes the live gate.

Distribution becomes `I3=307`, `I2=16`, `I1=39`, `I0=15`; 70 of 377 rows
remain below `I3`. Pending stages become `0/33/16/21` for
pre-freeze/candidate/external/deferred. Candidate assembly may now proceed on
scoped source branches; candidate creation, signing and promotion remain
unclaimed until their exact evidence exists.

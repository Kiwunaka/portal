# WO-013N — Authorized public and hosted pre-freeze closure

Status: `PASS_THREE_PREFREEZE_ROWS_I3_EXTERNAL_PRECONDITIONS_OPEN`
Phase: `01`, `11`
Rows: `REL/TEST-001`, `REL/REPO-001`, `FE_PR/PR-00`
Candidate: `NOT_CREATED`
Production mutation: `NOT_AUTHORIZED_NOT_RUN`

## Outcome

Owner authorization covered Git pushes, pull requests, Actions secrets and
narrow evidence-only merges. That authority closed the three explicit local
`pre_freeze` rows without creating a release candidate or changing a runtime,
payment, campaign, production server or promotion branch policy.

All three rows advance from `I2` to `I3`:

- `REL/REPO-001`: the public release-index source and trust root are published
  on public `main`, with exact hosted and raw readback;
- `FE_PR/PR-00`: the isolated no-visible-UI freeze/contracts slice passed its
  hosted controls and was merged, followed by one scoped workflow-retention
  correction;
- `REL/TEST-001`: the immutable three-repository tuple passed the complete
  standard client gate on GitHub-hosted Ubuntu.

`I3` is a pre-candidate implementation/evidence result. It is not a signed
candidate, device proof, production deploy or same-byte stable promotion.

## Public release-index and signing trust root

Public repository `Kiwunaka/pokrov` started at legacy main
`d0bf8e8c70ebeaa241f4c8f5b8a4452fd339ed15`. PR 1 published the nine-path v2
source contract at head `2ba9116b4bc222021c2fbb53a21ff8a6c4043289`
and merged it as `491436889ef911de868d704e68ba86e77102b0f1`.

The active Ed25519 trust-root record is:

- key id `pokrov-release-2026-01`;
- public-key SHA-256
  `651d1bcfbedecc4e50d21f3ad3bf3cc990a6cfc97ad355f0e0e76972b8ba8024`;
- private material is absent from Git and logs;
- the private half is present only as repository secret
  `POKROV_RELEASE_SIGNING_KEY_PEM` for future candidate signing.

PR check run `32616569598` passed `source-contract`. Post-merge push run
`32616614043`, job `97138291041`, passed source validation and tests against
the exact main merge. Public main and the trusted-key file were read back
exactly. No candidate manifest or artifact has been signed yet.

## PR-00 hosted isolation and merge

Platform PR 18 bound exact head
`e26fcb0b3581c8b0261db29812563085b8fb90a9` to the real source-plan base. Its
ten paths are freeze/contracts/workflow/evidence paths and contain zero visible
AdminApp, Marketing, WebApp or legacy portal UI paths. Hosted run
`32616491039` passed `release-base-isolation`; Guardrails run `32616491005`
passed `repo-guardrails`. The PR merged to `master` as
`8cef00ace333d9164d7ac9f4a0856eb7fa88f173`.

PR 19 then corrected only the retained workflow scope, handoff wording and
CRLF-safe exact-blob validation in three paths. Guardrails run `32618497517`
passed and the dedicated PR-00 job skipped by design because this was not a
second PR-00 slice. The follow-up merged as
`a25fa8a9ec5fe9e4032a65e152c9852c5c78e45b`.

There was no eligible non-author review. That missing organizational control
remains owned by `REL/REL-001` and `REL_DOD/DOD-09`; it does not erase the
exact hosted no-visible-UI proof recorded for `FE_PR/PR-00`.

## Exact hosted client gate

Open platform PR 17 uses one six-path, zero-visible-UI control commit
`75a5c4f82c963d81f1c46dcf26a83cf39b8021cf` over exact master
`a25fa8a9ec5fe9e4032a65e152c9852c5c78e45b`. The immutable source tuple is:

- platform `9b9467c7ad788298dd51de2d5c769d13be5a12b3`;
- client `66d82be70e32ba3d9650c250c92750ac264cba0f`;
- artifact-bound Core `fcb3c8bbc6efdeed284417369aacb522722ebfa2`.

The private client checkout uses read-only deploy-key secret
`POKROV_RELEASE_CLIENT_DEPLOY_KEY`; no credential material is committed or
logged. Run `32621490357`, job `97150195041`, completed `SUCCESS`:

- exact checkout and all three SHA checks passed;
- cross-repository seed validation passed;
- App Shell passed `385/385`;
- runtime engine passed `59/59`, with one intentional real-DLL backtest skip;
- Android shell passed `8/8`;
- Windows shell passed `21/21`;
- Android Gradle finished `BUILD SUCCESSFUL` in 6m42s;
- the standard entrypoint reported that all workspace Flutter and Android unit
  tests passed.

The workflow reclaimed only already-validated historical artifacts and their
Git LFS object cache inside the ephemeral client checkout. It retained 11 GB
free before the standard gate. This closes retained run `32620758845`, where
all Flutter packages passed but the runner reached 0 MB before Android Gradle
tests; the redundant diagnostic tail was then cancelled. Current platform
Guardrails run `32621490362` also completed `SUCCESS`.

## Supporting Core CI truth

Core PR 2 head `0e6b0204d764ae6b1d726343f487a7004d13393b` passed all five hosted jobs in
run `32619396382`: `test`, `release-contract`, `apple-source-build`, Android
artifact reproducibility and Windows artifact reproducibility. This is useful
source-CI evidence, but it is not the artifact-bound Core revision in the
successful client tuple and therefore does not silently replace
`fcb3c8bbc6efdeed284417369aacb522722ebfa2` or create a candidate.

## Index decision and remaining gate

Distribution becomes `I3=306`, `I2=17`, `I1=39`, `I0=15`; 71 of 377 rows
remain below `I3`. The pending stage split becomes `0/33/17/21` for
pre-freeze/candidate/external/deferred.

Candidate creation remains blocked by three external pre-candidate rows:

- `REL/REL-001` and `REL_DOD/DOD-09`: complete branch protection, selected
  non-author reviewer and reviewed CODEOWNERS are absent;
- `FE/P12-023`: the public source contract and trust root exist and pass hosted
  CI, but the frozen public trust revision has no eligible non-author review.
  Exact candidate assets and detached signature readback remain the later
  `I4` proof.

No production deploy, payment action, campaign, physical-device claim,
current/brain/RU-origin claim, candidate signature or promotion occurred.

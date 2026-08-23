# WO-013L — Exact hosted client gate control

Status: `PASS_LOCAL_CONTROL_PENDING_OWNER_ACCESS_AND_HOSTED_RUN`
Phase: `01`, `11`
Row: `REL/TEST-001`
External actions: `NOT_AUTHORIZED`

## Outcome

Dedicated platform branch `codex/1.2.0-hosted-gate-control` starts at actual
promotion revision `280ed9157f5804d4bc719cb8d6cab471caafb937` and contains
one commit, `085ac1ae49eea71f60209d70438fbb8f404b53af`. Its tree is
`20512631797ebae7d3bd187e16d1f2e212354711`.

The actual `origin/master..HEAD` diff contains five allowlisted CI-control,
contract, validator, test and handoff paths and zero paths under AdminApp,
Marketing, WebApp or legacy portal UI prefixes. This keeps the hosted-gate
control reviewable without mixing the broad 1.2.0 implementation into its PR.

## Exact source tuple and gate

The machine-readable control binds immutable revisions:

- platform `30859e115859386f5dd51210b5697af5440c36df`;
- client `8c6b955dced3b018825c53fe5d14cb632271adeb`;
- Core `fcb3c8bbc6efdeed284417369aacb522722ebfa2`.

On Ubuntu 24.04 the workflow resolves the tuple from the validated contract,
checks out each full SHA, verifies every resulting HEAD and runs the client's
`validate-seed.ps1` plus complete `run-tests.ps1` standard entrypoint. Python
3.12, Temurin Java 17, Flutter 3.38.5 and every referenced GitHub Action are
pinned.

## Private checkout boundary

Platform and client are private repositories. The control repository's
`GITHUB_TOKEN` cannot read the separate private client repository, so the
workflow fails closed unless the owner provisions repository secret
`POKROV_RELEASE_REPO_READ_TOKEN`. The token must be fine-grained and limited to
`contents:read` on `Kiwunaka/POKROV-app`.

No token, private key or credential was generated, stored or printed. Creating
the secret, publishing source revisions, pushing the branch and opening the PR
are external owner actions and were not authorized.

## Credited local checks

- validator: `PASS_EXACT_HOSTED_GATE_CONTROL_LOCAL`;
- target, parent and merge base: exact `280ed915...`;
- promotion diff: `5/5` allowlisted paths, `0` visible UI paths;
- exact tuple, toolchains, commands, pinned actions and fail-closed secret
  boundary: `PASS`;
- validator unit tests: `4/4 PASS`;
- Ruff check and format check: `PASS`;
- scoped diff check: `PASS`.

The 828-byte validator JSON output has SHA-256
`8fbd975ca969a42246bd6da822d2d5ea4a0fb5506c4ebc6d296e3c9e27725a00`.
The retained summary is
`evidence/013L-hosted-client-gate-control/013L-hosted-client-gate-control.json`.

## Index decision and next action

`REL/TEST-001` remains `I2`. This result proves that the exact hosted control
is locally ready; it does not prove that the three source revisions are
reachable from GitHub, that owner access exists or that Ubuntu passed.
Distribution remains `I3=303`, `I2=20`, `I1=39`, `I0=15`; 74 of 377 rows
remain below `I3`, and stage counts remain `3/33/17/21` for
pre-freeze/candidate/external/deferred.

After owner authorization: publish the unchanged exact source tuple, provision
the least-privilege secret, push exact control revision `085ac1a...`, create a
PR to `master`, and retain the run URL, run ID, checked-out SHA tuple and job
result. Only an exact successful run may advance `REL/TEST-001` to `I3`.

No candidate, signature, public-index publication, device/origin proof,
deployment, promotion or server mutation occurred.

# POKROV 1.2.0 exact hosted client gate control

Status: `PR_OPEN_CONTROL_FIX_PENDING`
Row: `REL/TEST-001`
External actions: `AUTHORIZED_FOR_GIT_PUSH_PR_AND_ACTIONS_SECRET`
Pull request: `https://github.com/Kiwunaka/portal/pull/17`

## Outcome

Run the standard client gate on GitHub-hosted Ubuntu against one immutable
three-repository source tuple without changing the client candidate or mixing
the broad 1.2.0 implementation into a CI-control pull request.

The control branch starts at platform `origin/master` and changes only the
workflow, its exact tuple contract, validator, tests, script-status manifest
and this handoff.

## Exact tuple

- platform `9b9467c7ad788298dd51de2d5c769d13be5a12b3`;
- client `05332bf1b17410610829113fe92748d29f84c597`;
- Core `fcb3c8bbc6efdeed284417369aacb522722ebfa2`.

The hosted workflow checks out those full commit IDs, verifies every resulting
HEAD, then runs the client's cross-repository seed validator and complete
standard test entrypoint on Ubuntu 24.04 with Python 3.12, Java 17 and Flutter
3.38.5.

## Private-repository boundary

Platform and client are private repositories. The workflow repository's
`GITHUB_TOKEN` is scoped to that repository and cannot read another private
repository. A dedicated read-only SSH deploy key is therefore registered on
`Kiwunaka/POKROV-app`; its private half is stored only in repository secret
`POKROV_RELEASE_CLIENT_DEPLOY_KEY` at `Kiwunaka/portal`.

The deploy key cannot write to the client repository and is not an account-wide
token. No private key or other credential belongs in source, workflow inputs,
logs or evidence.

## Publication order after authorization

1. Push the exact platform, client and Core source revisions under reviewed
   branches without changing their bytes.
2. Provision the read-only deploy key and repository secret.
3. Push this control branch and open its PR to `master`.
4. Retain the workflow run URL, run ID, exact checked-out SHAs and job result.
5. Advance `REL/TEST-001` only if the exact run passes; a checkout failure,
   skip, rerun on another SHA or local test is not hosted PASS.

No push, PR, secret creation, hosted run or branch-protection change is
performed by this local work order.

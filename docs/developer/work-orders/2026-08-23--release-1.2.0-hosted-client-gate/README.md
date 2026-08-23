# POKROV 1.2.0 exact hosted client gate control

Status: `PR_OPEN_RERUN_PENDING`
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

- control base `a25fa8a9ec5fe9e4032a65e152c9852c5c78e45b`;
- platform `9b9467c7ad788298dd51de2d5c769d13be5a12b3`;
- client `66d82be70e32ba3d9650c250c92750ac264cba0f`;
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

## Hosted execution history

The control branch, source branches, read-only client deploy key and Actions
secret are now published. PR 17 is open. Run `32617976654` checked out and
verified the exact prior tuple through client
`f15f08d3e385a2a5aa728093be385ff516725805`, then failed in seed validation
because the presentation-boundary check hard-coded Windows command `rg.exe` on
Ubuntu. Run `32618304282` proved the command name was portable at client
`31942b0d9125cd46b67d1d8e985cbe068c14a5db`, but the runner did not contain
ripgrep. Client `f32321aa54697bcc47f1914b6c4ba57fecdf0d36` replaced that dependency
with built-in PowerShell file search. Run `32618824382` then passed the exact
checkout and seed stages before the standard gate reported `383` passes and
two failures: one Linux golden mismatch and one Smart Connect deadline race.
Client `715c8abb8aed83b8ad5763891ae5e9919f4327dc` closes the race. After a
failed standard gate, the workflow regenerates all four test-only goldens in
the temporary Linux checkout and retains those PNGs for one day. This permits
an exact platform-baseline comparison without weakening the matcher. Run
`32619464667` then passed exact checkout and seed validation and reported
`384` passes with only the missing Linux baseline failing. Its retained
artifact `9487997903` supplied the four inspected Ubuntu PNGs now committed at
client `c4bad10a7c87209a8b82cb960823245ec216f524`; the Windows baselines remain
separate and unchanged. Run `32619899856` passed exact checkout, seed,
App Shell `385/385` and platform guardrails, then exposed one common
Windows-only path-separator defect across the `runtime_engine` test fixtures
(`28` passed, `31` failed, `1` intentionally skipped). Client
`8a0fa40f4f533f05d5fac6a77fd179fd06422b69` converts those fixture paths to
host-portable joins without changing runtime production code; its full local
standard gate and Android Gradle unit tests pass. Run `32620413756` confirmed
App Shell `385/385`, runtime engine `59/59` with the real DLL backtest
intentionally skipped, and Android shell `8/8`; it then found one Windows tray
icon helper interpreting a Windows executable path with the Ubuntu host path
context (`20` Windows-shell tests passed, `1` failed). Client
`66d82be70e32ba3d9650c250c92750ac264cba0f` makes that Windows-only helper use
explicit Windows path semantics; the focused `21/21` tests and analyze pass.

Run `32620758845` then passed the exact checkout, seed validation, App Shell
`385/385`, runtime engine `59/59` with one intentional real-DLL skip, Android
shell `8/8` and Windows shell `21/21`. The runner reached `0 MB` while Gradle
was instrumenting its Kotlin compiler dependency, before Android Gradle tests
could execute. The redundant post-failure golden diagnostic was cancelled
after the disk-exhaustion evidence was retained. The workflow now reclaims
only the already-validated historical `client/artifacts` working tree and its
Git LFS object cache before the standard gate. Both targets are resolved and
guarded under the exact ephemeral client checkout; product source, current
runtime inputs and release evidence outside that runner are unchanged.

Advance `REL/TEST-001` only if the current tuple passes both seed validation
and the complete standard client gate. The earlier checkout, line-ending and
tool-name failures remain retained failures, not passes. No candidate,
signature, deployment, publication or promotion has occurred.

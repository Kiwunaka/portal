# Windows connect deadline and stop boundaries — 2026-09-08

The installed IPC timeout fix did not propagate a request deadline or SCM stop
into Connect. Local regression now demonstrates that late Core/probe success
could still publish a protected connection. The client source fixes this by
checking a monotonic deadline and stop signal between transaction stages.

Once mutation has begun, interruption rolls back through the existing serial
recovery journal before returning. Effective identity stays empty; successful
rollback preserves the staged profile, while a rollback failure remains
`recovery_required`. The native UI accepts the closed interruption errors.

Six synthetic cases cover pre-mutation interruption, late Core and egress
completion, verified/committed journal writes and failed network restoration.
Debug native suites: 8/8 PASS. Runtime Flutter: 80 PASS, one existing exact-DLL
test SKIPPED because its environment input is unset. Analyze and Release
service build: PASS. [Exact source, commands and logs](evidence/windows-connect-interruption-2026-09-08.json).
The initial test also contained an empty-versus-`none` assertion error; both
failing logs are retained. Independent status/rollback assertions reproduced
the product defect before the fix.

This closes the late-commit defect at cooperative boundaries. Blocking Core,
WinHTTP and recovery calls still must return before the signal is observed.
Correlated IPC cancellation, concurrent mutation acceptance, WFP coexistence,
Win10 and installed managed-network/final package acceptance remain OPEN.
W02/W06 and the full plan are not complete. No installed VM bytes, Core bytes,
host network, retained release artifacts, candidate, push, merge or deploy
changed in this run. Rollback is the scoped matching UI/service source commit.

Client fix: `dab70dec0a871470bf52eff755bd13640bdfe4cc`. Client seed/docs and
platform 33 documentation tests, context audit and 288 package links PASS.
Both repositories pass `git diff --check`; retained release delta is empty.

# WO-010K — Support transport reconciliation

Status: `COMPLETE_LOCAL_I1_CONDITIONAL_DEFERRAL`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `08` with ledger row `FE/P12-208` sourced from `P07`
Lanes: active client `POKROV-app`; platform release ledger/evidence
Depends on: `WO-010G2`, canonical client product contract, frontend source plan
Production/external actions: `NOT_AUTHORIZED`

## Outcome

Close the only remaining `I0` frontend row without inventing a second support
transport. The source plan says SSE/WebSocket is optional and should be added
only if required. The canonical product contract says the same. There is no
retained polling SLA, battery or backend-load failure that satisfies that
condition, so `FE/P12-208` is a verified deferral at `I1`, not an unimplemented
release blocker and not an SSE/WebSocket implementation claim.

The same audit found a real bounded gap in `FE/P12-113`: candidate.3 source had
one-shot background-safe polling and failure backoff, but lacked the required
one-minute unchanged slowdown and immediate foreground refresh. Active delay
could also reach 12 seconds. That gap is corrected on a separate client branch
without changing support APIs or adding another process, protocol or truth.

## Client source result

Client branch `codex/release-1.2.0-support-polling`, commit
`03a59a7d155ffbbe77a9a0087ff5666b90ac1c92`, implements:

- 8-10 second active polling;
- 15-30 second polling after one minute without a thread change;
- immediate refresh when the support screen returns to foreground;
- typed `changed`, `unchanged` and `failed` results using a deterministic thread
  version fingerprint;
- exponential failure backoff with jitter capped at two minutes;
- the existing background, ineligible and dispose cancellation boundary.

The canonical client product contract now explicitly states that SSE/WebSocket
remains conditional on measured polling failure and is not part of 1.2.0.

## Verification

- focused app-shell analysis: `PASS`, no issues;
- polling coordinator tests: `PASS`, `6/6`;
- support background/resume and operator-reply widget tests: `PASS`;
- full app-shell suite: `PASS`, `392/392`;
- complete client `scripts/run-tests.ps1`: `PASS`, including runtime engine,
  all workspace packages, Android shell `8/8`, Windows shell `23/23` and both
  direct/store Gradle unit suites;
- explicit-root seed validation: `PASS`;
- client docs and release-v2 contracts: `PASS`;
- client `git diff --check`: `PASS`;
- no `artifacts/releases/**` delta.

Client PR [#29](https://github.com/Kiwunaka/POKROV-app/pull/29) is open at the
exact commit above. Required Release v2 job `98453413213` in run `33053181727`
received zero steps and no runner; GitHub reports the same account billing or
spending-limit blocker. This is `BLOCKED_BY_ACCESS_GITHUB_BILLING`, not a code
test failure and not a pass. The owner-solo exception does not waive a named
required successful GitHub App check, so the PR is not merged.

## LDPlayer and candidate boundary

Only signed exact candidate.3 remains installed in LDPlayer 9
`emulator-5554`: package `1.2.0+30`, universal APK SHA-256
`f41c76ebf7bf69f6681d7df87e7722dcdccdec383ef950156b69829caee71c51`.
It launches, remains alive, has an empty crash buffer and renders the Support
screen with human chat primary plus AI helper, feedback, diagnostics and the
composer. No ticket or message was created because external communication was
not authorized; live polling is therefore `NOT_TESTED`.

The adaptive branch was not installed over candidate.3. The physical phone was
removed by the owner, so Beeline, OEM and handover checks remain
`MANUAL_OWNER_TEST`. Candidate.3 contains neither the polling correction nor a
streaming transport. After PR #29 merges, the correction requires a replacement
signed candidate and a fresh exact-byte LDPlayer replay.

## Ledger decision

- `FE/P12-208`: `I0 -> I1`, `VERIFIED_DEFERRED_NOT_REQUIRED`;
- `FE/P12-113`: remains `I3`, stronger local source evidence only;
- distribution: `I4=4`, `I3=312`, `I2=19`, `I1=40`, `I0=2`;
- at or above `I3`: `316`; below `I3`: `61`;
- pending stage split remains `pre_freeze=0`, `candidate=28`, `external=14`,
  `deferred=19`.

No deploy, server mutation, ticket, entitlement, payment, public artifact,
stable pointer or Gate G authorization occurred.

## Reopening condition

Reopen `P12-208` only if retained polling SLA, client battery or backend-load
evidence proves the bounded foreground policy inadequate and the owner approves
one versioned streaming contract with authentication, retry, ordering,
background and rollback semantics. Do not add SSE/WebSocket speculatively.

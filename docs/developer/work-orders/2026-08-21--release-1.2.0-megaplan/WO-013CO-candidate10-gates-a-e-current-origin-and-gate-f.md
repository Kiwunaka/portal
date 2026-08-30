# WO-013CO — candidate.10 Gates A–E, current-origin and Gate F

Status: `EXACT_CANDIDATE10_GATES_A_E_BLOCKED_CURRENT_ORIGIN_PASS_GATE_F_NO_GO`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `11`
Candidate: `pokrov-1.2.0-candidate.10`
Production/external mutation: `NONE`

## Outcome

Replay source-plan Gates A–E and direct current-origin against the exact signed
candidate.10 source tuple. All five gates remain `BLOCKED` at their existing
index ceilings because required live/manual evidence remains open, but the
replay finds zero new candidate source defects. Direct current-origin health
and catalog both pass their exact budgets.

Regenerate Gate F from the new candidate-scoped evidence. The verifier checks
the signed manifest, detached signature, receipt, public keyring, exact source
tuple, all `19/19` pointers and both upstream digests. The decision remains
`NO_GO`: `6 PASS / 13 non-PASS`, including exactly `1 FAIL`, with zero
validation errors. Gate G remains unauthorized.

## Exact candidate identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.10` |
| Operational ID | `1de7182d9c82759acc36eb7a336d1fef2362e8f69505f3b4880e595f79020454` |
| Platform source | `209b8f40c36d95f2bbc67caa52a41ecb09f46720` |
| Client source | `3459438f02bd774e722b1b858e7f7f16d57a9f5c` |
| Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Signed release-index source | `fc00b26d402b167260e495eb33397115bef1c317` |
| Manifest SHA-256 | `0711546b0da4b811fba42e1ad543797494e4104bd95251c9e8e8011ac04dff83` |
| Signature SHA-256 | `6f96f8932e388f221cf7d5e10dc1680fbcbb62f87efe00410439eb9f62e42799` |
| Receipt SHA-256 | `094a42f3c0d9be3957b3065344e5bfce4880c2899833fed3b4d211d8d453a89c` |

The platform and client worktrees are clean detached checkouts of the signed
source commits. Core `main` equals the manifest-bound commit and is clean. The
release-index worktree is clean detached at the merge containing the signed
candidate source. The evidence harness starts at platform `master`
`099be5a...`; it is not presented as candidate source.

## Exact replay

The candidate preflight returns `READY_LOCAL_FREEZE`, zero blockers and zero
pre-freeze rows below `I3`; it still sets `candidate_proven=false` and
`promotion_authorized=false`. The permanent stop-ship replay remains
`BLOCKED`: all `7/7` local regression anchors pass, but connected Windows is
`NOT_RUN`, private hosted checks remain `SKIPPED_BY_OWNER`, and the solo
exception does not claim independent review.

Gate B exact platform observability/support/handoff tests pass `70/70` in
`0.81 s`; exact client state, diagnostics, migrations and bootstrap pass
`111/111`. Exact Core commit `a45d69e...` retains hosted run `33232348126`,
attempt `2`, with all five jobs passing.

Gate D payment/provider/callback/HTTP/DB/outbox/module tests pass `196/196`
plus `12` subtests in `746.57 s`, with `20` existing deprecation warnings.
Action Intent and policy coverage pass `25/25` in `115.63 s`. Brain source,
readiness and enabled delivery remain exact at `197/197`, `23/23`, `7/7`.
No payment, provider, customer, database, outbox or Operator mutation ran.

## Gate E and current-origin

The first local-quality run correctly fails because a fresh detached platform
worktree has no `node_modules`; frontend tools cannot launch. This is retained
as fail-first environment evidence, not rewritten as a source failure. After
`npm ci` in WebApp, marketing and adminapp, npm reports zero vulnerabilities
and the same exact sources pass all `15/15` local-quality steps. Static web
performance passes all `9/9` budgets.

The observed runner is Node `24.15.0` while package engines request the
`22.14.x` line. The mismatch is retained honestly. It does not change the
candidate bytes or make the successful source checks a release proof.

Direct source-bound `Ethernet 2` current-origin probes use five warmups and 50
retained persistent HTTP/1.1 samples each:

| Budget | Result |
|---|---|
| health p95 | `PASS`, `36.8219 ms <= 100 ms` |
| public catalog p95 | `PASS`, `46.127 ms <= 200 ms` |

The assigned source address and raw response bodies are not tracked. Only safe
metrics and SHA-256 bindings to external raw/gate files are retained.

## Gates A–E

| Gate | Decision/index | Remaining boundary |
|---|---|---|
| A | `BLOCKED/I1` | connected clean-VM Windows, hosted private execution and trusted signing |
| B | `BLOCKED/I3` | Windows connected stop/recovery and broad live false-green proof |
| C | `BLOCKED/I3` | candidate.10 physical phone, isolated Windows, remaining Android leak/OEM/accessibility and Store delivery |
| D | `BLOCKED/I3` | provider, PostgreSQL load/locking, outbox/reconciliation/reversal and real Operator rollback |
| E | `BLOCKED/I3` | authenticated journeys, physical accessibility/device performance, browser lab, support, RU and post-promotion proof |

The physical phone was unavailable and was not touched. Candidate.8 physical
results remain history and are not transferred to candidate.10.

## Gate F effect

Current-origin advances from `NOT_RUN` to `PASS`. Exact Gates A–E and aggregate
performance move from `NOT_RUN` to `MANUAL_OWNER_TEST`: local components pass,
but their required manual/live matrices are incomplete. The decision is:

```text
NO_GO
required=19
pass=6
non_pass=13
fail=1
validation_errors=0
gate_g_authorized=false
```

The explicit FAIL remains canonical RU-origin `10/13`: Brain TLS, free REALITY
target and NL TCP fail independently; `ru_spb` passes. Current-origin does not
cancel or replace RU-origin.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013CO-candidate10-gates-a-e.json` | `a62610aa65e18ef57bd0e4c5bc0f3bff4c54e9efe157584fddbf55abf27f33aa` |
| `013CO-candidate10-gate-f-evidence.json` | `d409c8eab913b23bf02a52e3ba007e29a60963058e3589375de64dec23ac76d5` |
| `013CO-candidate10-gate-f-input.json` | `4767aa96b9e696088155c76876c0b4caa4ab8b5301358f6e1805f29f3db46fe4` |
| `013CO-candidate10-gate-f-decision.json` | `a4d0a1d9d3eb85592c2f1a3d23b9268299c72e5e78231052ce0552af2ceb0d74` |

The decision digest above is the canonical staged LF blob digest.
`.gitattributes` pins this evidence directory to LF.

## Verification

```text
candidate.10 preflight -> READY_LOCAL_FREEZE, blockers=0
STOP-SHIP replay -> BLOCKED, local regressions 7/7 PASS
Gate B exact platform -> 70/70 PASS
Gate B exact client -> 111/111 PASS
Gate D payment/HTTP/DB/outbox -> 196/196 + 12 subtests PASS
Gate D Action Intent/policy -> 25/25 PASS
local quality fail-first -> FAIL, dependencies absent in fresh worktree
npm ci -> zero vulnerabilities across webapp/marketing/adminapp
local quality rerun -> 15/15 PASS, candidate_proven=false
static performance -> 9/9 PASS
current-origin health -> PASS, p95 36.8219 ms
current-origin catalog -> PASS, p95 46.127 ms
Gate F -> expected exit 2, NO_GO 6/13/1, validation_errors=0
```

## Mutation boundary and next action

No artifact rebuild, candidate relabel, production deploy, payment/provider/
database/Operator mutation, device action, public release, tag, Store object,
stable pointer or Gate G authorization occurred.

Classify the three RU failures independently and fix only verified owned
configuration/runtime defects. Do not spend release time on `ru_spb`, which
already passes. Physical candidate.10 remains manual until the phone returns;
LDPlayer remains available for bounded regression work.

# WO-002 — Product Truth And Branch Baseline

Status: `COMPLETE`

## Outcome

Одна текущая продуктовая правда во всех canonical consumers и безопасная
Git-база для дальнейших изменений.

## Write Scope

- current product/payment/referral/release canonical owners and their direct
  shared JSON consumers;
- focused tests that prevent price/trial/referral/free/version drift;
- local branch/ref bookkeeping without rewriting history.

Historical evidence, archived copy and guarded compatibility fields are not
mass-edited or deleted.

## Acceptance

- current public truth is 5-day trial, no permanent free node, Android/Windows,
  release `v1.0.4-beta.1` until a later exact release, approved six prices;
- `start_99` is one full first month, one device, once per account, no
  auto-renew, no stacking;
- referral truth is friend +5, referrer +10 after first successful paid order
  and 72-hour hold in product facts, payment state machine, support answers and
  tests;
- stale `1.0.0-beta*` is either historical-labelled or replaced only where a
  current owner incorrectly presents it as distributed truth;
- local promotion refs fast-forward to their existing remotes; new work uses
  scoped `codex/...` branches; no empty merge commits.

## Checks

Focused product-facts/catalog/referral tests, documentation contract, JSON
parsing, `git diff --check`, secret scan and exact branch divergence report.

## Done Evidence

- Platform branch `codex/conversion-first-acquisition-20260814` started exactly
  at `bf79d3d`, equal to `origin/master`; client branch with the same scoped name
  started exactly at `e172d4b`, equal to `origin/main`.
- Current release truth is reconciled to `v1.0.4-beta.1` in current product,
  user, developer, publishing, deployment and rollout owners. Dated screen
  captures and historical unsigned-release evidence remain unchanged.
- `shared/product-facts.json`, support knowledge, bot copy and payment/referral
  owners now agree: invited friend `+5` after their first successful provider
  payment; referrer `+10` after the existing 72-hour hold; no install/trial/
  connect grant.
- Backend now writes the friend's grant idempotently from the canonical first
  provider payment. Callback replay and renewal do not create another grant.

Exact checks:

- economy service: `24 passed`;
- account payment/backfill focus: `4 passed`;
- payment callbacks focus: `3 passed`;
- referral worker/Stars focus: `6 passed`;
- docs/support contracts: `45 passed`;
- Python compile, shared JSON parse and `git diff --check`: PASS.

Pytest printed a Windows temp cleanup `PermissionError` after successful test
completion; every command exited `0`. This is environment cleanup noise, not a
converted PASS for the previously timed-out broad five-file invocation.

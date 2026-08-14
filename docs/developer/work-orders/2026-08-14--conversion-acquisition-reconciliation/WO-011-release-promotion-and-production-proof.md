# WO-011 — Release Promotion And Production Proof

Status: `PENDING`

## Outcome

Все изменения проверены на точных commits, reviewable закоммичены, запушены,
продвинуты в `master`/`main`, задеплоены и подтверждены current-origin evidence.

## Pre-commit Gate

- exact status/diff/stat in both repositories;
- every dirty/untracked file classified; no blanket staging;
- added-line secret/credential/private-key scan;
- canonical docs impact and migration/rollback reviewed;
- focused tests from each WO plus relevant platform/client regression suites;
- builds and visual/E2E checks proportional to changed surfaces;
- `git diff --check`; release/artifact directories change only when an exact new
  binary release is actually required.

## Promotion Order

1. Push platform/client scoped feature commits.
2. Fast-forward platform to `master` and client to `main`; no history rewrite.
3. If client binary changed, build with production signing, publish split APKs,
   universal fallback and Windows asset, then write exact handoff/hashes.
4. Deploy backend/shared/static surfaces through guarded scripts with rollback
   backup and preflight.
5. Run brain/current-origin health, public catalog/download hashes, pricing,
   attribution, checkout eligibility, bot, notifications, promo, whitelist and
   admin funnel smoke on the exact deployed hashes.

## Evidence Labels

Use only `PASS`, `MANUAL_OWNER_TEST`, `OPERATOR_ATTESTED`, `SKIPPED_BY_OWNER`,
`SKIPPED_BY_OPERATOR`, `BLOCKED_BY_ACCESS` or `NOT_REQUESTED`. This wave does
not relabel the deferred Huawei 20-cycle, Wi-Fi/LTE, Windows clean egress,
external keystore backup, real Telegram acquisition and RU-origin proof as PASS.

## Closure

Record commits, branches, promotion hashes, deploy identifiers, exact commands,
results, current-origin URLs/hashes, rollback location and remaining labelled
risks. Update INDEX to evidence only after all in-scope outcomes are complete.

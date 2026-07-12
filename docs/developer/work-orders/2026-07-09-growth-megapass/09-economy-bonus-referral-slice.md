# Economy Telegram And Referral Grant Slice

Date: 2026-07-12

Status: repository candidate implemented; not deployed.

## Completed Scope

- Added account-owned Telegram grants: new `+5 days`, issued `+10 days` grandfathered.
- Added `24 hour` membership-loss grace, rejoin cancellation, and unused-only reversal.
- Added exact `15 day` pre-first-payment cap across trial, Telegram, and friend grants.
- Added normalized referral relationship and transition tables with self/cycle rejection.
- Added friend `+5 days` from canonical server connection evidence only.
- Added replay-safe referrer `+15 days` after first successful payment and full `72 hour` hold.
- Kept legacy user flags as compatibility projections and migrate valid pending referral queue rows into canonical account holds without discarding retryable conflicts.
- Preserved current legitimate premium expiry when applying paid time.
- Added provider/order payment grants and deterministic entitlement projection rebuilds so channel reversal cannot consume purchased or unrelated grant duration.
- Made admin plan/gift/promo keys non-authoritative for first payment and `start_99` consumption.
- Added full referral merge reconciliation, transition snapshots, self/cycle cleanup, bonus premium-pool projection, and expected uniqueness-race recovery.
- Classified premium contributions explicitly so free-cycle/legacy snapshots cannot extend premium or select premium pool.
- Replaced flag-only historical payment authority with corroborated provider/order facts and stable manual-review markers.
- Retained duplicate/self/cycle referral relationships as terminal rows so every transition keeps a valid relationship owner.
- Kept payment, renewal, recovery, and support outside the new-lead Telegram gate.
- Enforced that gate in the real trial handler and kept failed Stars panel fulfillment replayable without duplicating paid duration.
- Split grandfathered channel time out of aggregate legacy snapshots and deduplicated semantic friend/referrer grants during account merge.

## Evidence Labels

- Automated repository tests: pending final report in `.superpowers/sdd/economy-bonus-referral-report.md`.
- `MANUAL_OWNER_TEST`: real Telegram membership, leave/rejoin, and linked app/bot account proof.
- `MANUAL_OWNER_TEST`: real provider first-payment callback and full 72-hour release proof.
- `MANUAL_OWNER_TEST`: deployed node observer evidence for friend reward release.
- `NOT_REQUESTED`: merge, push, deploy, production mutation, live Telegram/payment/node calls, and active-client changes.

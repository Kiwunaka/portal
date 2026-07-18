# Payment Entitlement Claim Slice

Status: repository candidate implemented; not deployed.

Scope branch/base: `codex/payment-entitlement-claims` based on
`4d28a5e3e3c77d29cf183b4a33fde1aaba8ebea0`. The exact candidate commit is
recorded in the Git handoff. No push, deploy, live provider call, email call,
node call, or secret/config change was made.

## Completed

- Added the additive `payment_entitlement_claims` model and repeatable SQLite
  and PostgreSQL migration paths. Incomplete legacy rows are retained and
  quarantined as manual review; fixed error evidence includes `last_error_at`.
- Public anonymous order creation now creates the pending claim in the same
  local transaction as `ExternalOrder`; authenticated orders retain direct
  account fulfillment.
- Added the transactional claim service for payment/attach ordering,
  canonical-account attachment, idempotent fulfillment, safe cross-account
  manual review, fallback linking/redemption, retry evidence, and reversal.
- Signed paid/reversal events remain incomplete until durable fulfillment;
  transient incomplete work retries, while terminal manual-review/conflict
  outcomes complete and dedupe with `200`, `activated=false`, and fixed safe
  evidence.
- Public fallback receipts complete only after delivery evidence is stored.
  Pending/error delivery is reconstructed from the persisted order and linked
  card on retry; a recorded sent state is not resent. The claim/card commit
  survives relay failure. A send-before-evidence crash can cause at-least-once
  duplicate delivery, but cannot permanently strand an undelivered key.
- A refund/chargeback committed while fallback delivery is in flight remains
  authoritative. Delivery evidence preserves reversal fulfillment state, and
  paid event completion re-locks the current order, completes terminally as
  `claim_reversed`, reports no access, and does not resend on replay.
- Paid fulfillment requires the saved order owner. Callback identity cannot
  replace `ExternalOrder.tg_id`, adopt an anonymous order, or move access to a
  different account. Owner conflicts are terminal manual-review receipts.
- Paid and reversal order states are monotonic. Refund/chargeback reverses the
  linked claim/grant once and rebuilds the account projection.
- Callback receipts with different external IDs serialize on the shared locked
  order row and refresh it before transition. Paid/refund/chargeback stale
  writers cannot regress provider status or pending reversal evidence. Both
  paid fulfillment paths recheck the locked order and terminate without access
  when refund/chargeback already won the receipt-to-fulfillment race.
- A missing-user bootstrap rollback no longer leaves fulfillment on an unlocked
  stale order object. The paid path reacquires and refreshes the provider/order
  row before account/grant mutation and suppresses legacy payment-authority
  backfill during that gap, so a committed reversal remains terminal.
- The first refund/chargeback receipt commit durably records pending
  reconciliation before the reversal transaction. Inter-commit crashes remain
  visible in admin attention; only explicit successful reconciliation clears
  the marker. Missing fallback/grant links are terminal manual review and do
  not create callback retry storms or false reversal success.
- Payment-linked fallback cards cannot add a second period after auto-claim;
  both gift and unified access-key redemption paths enforce claim ownership and
  use the saved claim plan/duration without requiring a current catalog entry.
  Wrong-account key use is non-mutating and cannot poison the rightful claim.
  Durable callback success verifies the linked GiftCard exists. Unlinked
  legacy GiftCards retain existing behavior.
- Paid callback fulfillment reads an existing claim before mandatory catalog
  resolution. Its normalized email, plan, and duration snapshot remains
  authoritative across event IDs; catalog lookup is label-only for that path.
  Claimless legacy orders still require a current supported plan.
- Pre-slice paid orders can safely link an existing unredeemed, plan-matching
  system-created GiftCard referenced by fulfillment metadata. Replays and
  different event IDs keep one card/claim link and do not resend already
  successful email delivery. User/admin-created, redeemed, type-mismatched, or
  other-claim-owned cards enter manual review.
- Newly added required migration columns use constant `NOT NULL` defaults;
  PostgreSQL applies metadata-guarded `SET NOT NULL` after backfill. Existing nullable SQLite
  columns are retained without table rebuild and incomplete rows are
  operationally quarantined as manual review.
- Stored retry and email-delivery evidence uses fixed safe codes and bounded
  fields. Raw relay detail, message body, buyer email, key, exception text, and
  SQL parameters are excluded from error metadata and payment DB logs.
- Delivery evidence locks the order and is monotonic after success. Bot gift
  success/denial events store only last-four preview, SHA-256 fingerprint
  prefix, length, and bounded outcome fields, including wrong-account denial.
- Admin reversal attention uses a repeatable `(status, created_at, id)` order
  index and applies the conservative root-state verifier to every indexed
  refund/chargeback candidate. It intentionally avoids unsafe whole-blob
  substring prefilters; residual cost scales with reversal candidates.
  Reversal problem recency safely parses `reversal.recorded_at`, including
  overflow handling, with purchase-time fallback before the common top-25 merge.
- Order and payment-event metadata is structurally bounded before JSON
  serialization. Authoritative fulfillment/reversal/pricing/buyer/order state
  and fixed processing errors survive oversized callbacks; excess detail is
  represented by a redacted summary/fingerprint, never invalid string-sliced
  JSON.
- The claim plus linked GiftCard is the fallback-key authority. New keys are
  not copied into order JSON, and a legacy order key is scrubbed after durable
  relinking. Retry delivery reads the linked card; response plan/duration comes
  from the claim snapshot after catalog removal.
- Updated the canonical API/product contracts. No OTP or public claim endpoint
  was added.

## Verification

- Review RED: combined claim/callback run -> 13 expected failures and 49
  passes before the P1/P2 fixes.
- Legacy-fallback re-review RED: focused claim/migration suite -> 7 expected
  failures and 12 passes; callback regression -> 1 expected failure.
- Quality/security review RED: four service/migration, five callback/redemption,
  and one admin reversal regression failed on the reviewed behavior. The added
  manual-review order-state assertion also failed before its transition fix.
- Final quality re-review RED: 9 of 10 focused crash-window, dangling-link,
  lock-order, metadata, raw-key, and admin-limit regressions failed before this
  correction; the existing gift-service grant path was already green.
- Second quality re-review RED: 10 failed and 1 passed across shared-order lock,
  delivery ordering, global admin attention, common ordering, bot persistence,
  and fallback provenance. The monotonic stale-state regression was already
  green; the full focused set passed 11 after correction.
- Final race-window RED: a paid callback after committed pending reversal
  attempted fallback delivery and returned `503`; the corrected three-test
  order/fulfillment regression passed.
- Residual-P2 RED: all four focused in-flight delivery, global reversal
  prefilter, reversal recency, and additive index regressions failed before the
  correction; the focused set then passed 4.
- Final metadata/admin RED: the exact oversized callback, adversarial nested
  reversal marker, and boundary timestamp regressions failed 3 before the
  structural serializer and conservative verifier changes.
- Final bootstrap/reversal RED: the missing-user lock-gap and dangling-fallback
  service/endpoint regressions failed 3 before the order re-lock and locked
  fallback validation changes. The combined seven focused regressions passed.
- Final catalog-authority RED: removed-plan fulfilled-account and changed-
  duration sent-fallback callbacks failed 2 before claim-first resolution; the
  focused pair then passed without duplicate grant, card, or email.
- Baseline before edits: `python -m unittest tests.test_api_payments_callbacks`
  -> 41 passed.
- Final claim plus full callback file: 100 passed, including shared-order
  serialization, stale paid/reversal ordering, in-flight delivery reversal,
  monotonic delivery evidence, additive order indexing, fallback provenance,
  dangling links, raw-key, catalog-removal, oversized valid order/event JSON,
  missing-user bootstrap re-lock, and replay.
- Account, economy, and migration matrix: 79 passed.
- Focused affected gift/unified redemption selection: 7 passed. Payment-linked
  gift-service coverage is also included in the 100-test claim/callback run.
- Admin payment/order summary file: 19 passed, including global outstanding
  reversal attention, adversarial nested callback metadata, overflow-safe
  reversal recency, and common descending problem ordering.
- Full bot paywall file: 72 passed and 12 subtests passed, including persisted
  redaction for gift success, repeat denial, and wrong-account payment fallback.
- Fresh focused bot persistence rerun after the residual fixes: 2 passed.
- Fresh controller focused matrix across claims, callbacks, admin, bot,
  account, economy, and migrations: 274 passed, 12 subtests passed, and 18
  existing deprecation warnings.
- Fresh canonical `RELEASE_PYTEST_ARGS` matrix: 493 passed, 23 subtests passed,
  and 17 existing deprecation warnings.
- A broader exploratory command also produced 81 passes and two unrelated
  `test_pokrov_migration_defaults.py` failures because that root/client contract
  test resolves the forbidden neighboring client as `.worktrees/POKROV-app`.
  It is not counted as payment proof; the exact relevant matrix above is green.
- `python -m py_compile` passed for all changed Python and focused test files.
- `scripts/check-links.py` with its report redirected under worktree `.tmp`
  passed all checks.
- High-confidence private-key/provider-token scan passed across all 14 changed
  paths and eight credential patterns without printing matched values.
- Final `git diff --check` passed; Git emitted only its existing LF-to-CRLF
  worktree warnings.

## Self-Review

- Transaction boundaries: order plus pending claim is one commit; callback
  receipt is committed before fulfillment and event completion only after the
  durable grant, or linked fallback plus recorded delivery attempt/evidence.
- Replay/races: provider/order uniqueness, provider-payment idempotency, claim
  row locks, fallback uniqueness, shared order-row callback serialization, and
  retryable incomplete events prevent duplicate grants/cards or stale state
  across repeated or different external event IDs. Missing-user bootstrap
  reacquires and revalidates the order lock before any grant-capable mutation.
- Ownership: verified-email attachment canonicalizes merged IDs; conflicting
  accounts never move grants. Terminal fulfilled/reversed states cannot be
  overwritten by later definition or account conflicts. Merge projection
  moves attached claims to the canonical account.
- Lock order: operations touching both account and claim take canonical account
  locks before the claim row lock after a non-locking lookup/revalidation.
  Attached paid callbacks mark paid and fulfill in one account-first service
  operation; an attach race is committed before re-entry into that operation.
  Live PostgreSQL concurrency validation remains `MANUAL_OWNER_TEST`.
- Operator visibility: unreconciled refunded/chargeback orders stay in admin
  payment attention from the initial receipt commit, even across an inter-commit
  crash or outside the selected reporting period. Reversal and ordinary problem
  rows share one descending order before list limits; successfully reconciled
  reversals are not false positives.
- Reversal: timestamps/reasons are write-once, the grant projection is rebuilt,
  and linked fallback redemption is blocked.
- Privacy/scope: stored errors are fixed safe codes; callback payload storage is
  structurally bounded, valid JSON with redaction and summary fingerprints;
  delivery and DB failures persist/log no raw relay, email, key, secret,
  exception, payload, or SQL parameter. Only authorized files were changed.
- Residual scale risk: admin reversal attention intentionally verifies every
  indexed historical refund/chargeback candidate in Python so malformed legacy
  metadata cannot be hidden by an unsafe SQL substring filter. This is correct
  but grows with reversal history and remains an operations follow-up.

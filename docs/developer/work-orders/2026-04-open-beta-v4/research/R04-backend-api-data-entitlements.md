# R04 Backend/API/Data/Entitlements Key-First Audit

Date: 2026-04-26
Worktree: `C:/Users/kiwun/.config/superpowers/worktrees/VPN/open-beta-v4`
Role: R04, POKROV Open Beta v4 research wave

## Executive Summary

The backend has a functional app-first trial path, account-bound RUB checkout path, Telegram Stars fulfillment path, support ticket path, and admin payment ledger. It does not yet implement the frozen key-first commercial contract as the primary fulfillment model.

The current paid RUB callback path directly extends `users` and then best-effort syncs the control panel. Activation keys are separate admin-issued rows backed by `gift_cards`, not payment-issued inventory bound to an order. Refund and chargeback callbacks update payment/order state only; they do not revoke, downgrade, suspend, or flag the user's paid entitlement. Admin reconcile can mark an order `paid`, `refunded`, or `chargeback`, but it does not issue keys, apply entitlements, revoke entitlements, or require a fulfillment-safe transition.

The highest-risk launch gaps are:

- P0: paid callbacks can fulfill direct entitlements instead of issuing or redeeming activation keys.
- P0: refunds and chargebacks are not entitlement-safe.
- P0: callback idempotency is event-id based, not order-fulfillment based, so repeated valid paid events for the same order can apply paid days more than once.
- P1: paid callback activation and panel sync are not transactionally represented, so users can become paid in DB without a reliable provisioning retry state.
- P1: activation keys reuse `gift_cards` and lack order binding, immutable fulfillment ledger, revocation status, hashed-key storage, and refund coupling.

## Evidence Table

| Label | Evidence | Implication |
| --- | --- | --- |
| E01 | `portal_bot/api.py:4732` exposes `POST /api/client/session/start-trial`. | App-first bootstrap exists and returns session, access, client policy, and provisioning payload. |
| E02 | `portal_bot/app_first_service.py:203` creates/reuses an app user by `app_install_id`, with `sub_type="FREE"`, `current_plan_code="trial"`, `tos_accepted=True`, and `trial_used=True`. | Trial is robustly app-first and does not require Telegram for first use. |
| E03 | `portal_bot/migrations.py:352` and `1272` add partial unique indexes for `users.app_install_id`; `models.py:74` also indexes the column. | Duplicate install IDs are guarded at DB level. |
| E04 | `portal_bot/api.py:1303` builds access states from `users.sub_type`, `current_plan_code`, `expiry_at`, and usage. | Entitlement truth is currently derived from mutable user fields, not a separate entitlement ledger. |
| E05 | `portal_bot/api.py:5541` and `5570` create authenticated/public RUB orders. Public order creation requires a signed checkout ticket with a `tg_id`. | Public checkout is account-session first, not anonymous buy-key first. |
| E06 | `portal_bot/api.py:5321`, `5326`, `5331`, and `5336` receive result/refund/chargeback callbacks. | Provider callback routes exist for all required event families. |
| E07 | `portal_bot/api.py:3246` handles callbacks and only calls `_apply_external_paid_order` for non-duplicate signed `result` events with status `paid`. | Paid fulfillment is direct user mutation from callback, not key issuance. |
| E08 | `portal_bot/api.py:3146` applies paid orders by finding/creating `User`, extending `expiry_at`, setting `sub_type="PAID"`, `current_plan_code`, `is_active=True`, and `first_purchase_done=True`. | RUB callback fulfillment bypasses access-key issuance/redeem entirely. |
| E09 | `portal_bot/api.py:3045` records callback events using unique `(provider, event_type, external_id)` from `models.py:578`; `migrations.py:894` and `1415` create that unique index. | Duplicate protection is not keyed to `(provider, order_id, fulfillment_kind)` and can allow repeated paid application for the same order if external event IDs differ. |
| E10 | `portal_bot/api.py:2984` maps refund and chargeback callbacks to order statuses, but `api.py:3246` has no entitlement reversal branch for `refund` or `chargeback`. | Reversal callbacks do not make access safe. |
| E11 | `portal_bot/api.py:5664` admin Freekassa refund calls the provider API and returns remote response only. | Operator refund action does not update local order state or access state. |
| E12 | `portal_bot/api.py:7772` admin reconcile can set order status and `paid_at`; tests in `tests/test_admin_payments_api.py:141` verify audit and status update only. | Reconcile is ledger-only; it does not fulfill, revoke, or queue safe remediation. |
| E13 | `portal_bot/api.py:7033` and `7052` expose access-key status/redeem. | Key redemption exists as a separate flow. |
| E14 | `portal_bot/api.py:10103` admin access-key issue creates `GiftCard` rows from plan catalog entries. | Access keys are admin-issued, not automatically payment-issued. |
| E15 | `portal_bot/models.py:127` defines `GiftCard` with `code`, `card_type`, `created_by`, `redeemed_by`, and timestamps only. | Key data has no order ID, buyer account, provider, purchase status, revocation state, refund state, plaintext/hash separation, or fulfillment history. |
| E16 | `portal_bot/api.py:1649` applies a key by mutating `User` to paid and updating `GiftCard.redeemed_by` with a conditional update. | Redeem is concurrency-conscious for single-use, but still user-field based. |
| E17 | `portal_bot/gift_cards_service.py:91` implements legacy gift redeem separately from `/api/access-keys/redeem`. | There are two similar code paths with different return contracts and sync behavior. |
| E18 | `portal_bot/bot.py:8976` handles Telegram Stars successful payments and calls `create_subscription`; `bot.py:9216` mutates subscription directly. | Telegram paid fulfillment is also direct entitlement, not key-first. |
| E19 | `portal_bot/pay_attempts_service.py:1` tracks Stars attempts with `started`, `invoice_sent`, `paid`, `abandoned`, and `failed`. | Stars payment state is separate from RUB orders and activation-key state. |
| E20 | `portal_bot/migrations.py:832` and `1359` define `external_orders`; `migrations.py:874` and `1395` define `external_payment_events`. | Payment ledger exists, but no entitlement ledger or activation-key ledger exists. |
| E21 | `portal_bot/tests/test_api_payments_callbacks.py` covers signed success/fail/cancel/manual-review, idempotency for same external ID, public order tickets, and provider catalog. | Callback coverage is useful but misses order-level replay, refund/chargeback revocation, and key issuance. |
| E22 | `portal_bot/tests/test_app_first_api.py:288` only covers access-key status rate limiting for key endpoints. | Access-key redeem/issue/payment-key fulfillment coverage is mostly absent. |

## P0 Issues

### P0-01: RUB paid callbacks fulfill direct user entitlement instead of issuing key-first access

Current behavior:

1. Checkout order is account-bound through signed checkout ticket or authenticated request.
2. Provider result callback reaches `_handle_payment_callback`.
3. For signed `paid` result, `_apply_external_paid_order` extends `users.expiry_at`, sets `sub_type="PAID"`, and sets `current_plan_code`.
4. No activation key is issued, returned, reserved, redeemed, or attached to the order.

Risk:

- Violates the frozen product direction: `buy key -> redeem key -> managed premium`.
- Makes purchase recovery depend on account state instead of transferable/redeemable key state.
- Prevents clean support handling for buyer != recipient.
- Makes refund and chargeback handling harder because no key or entitlement grant record exists to reverse.

Required fix:

- Change paid callback fulfillment from `apply user entitlement` to `issue activation key for order`.
- Direct entitlement should only happen after explicit key redemption, or through a dedicated operator action that creates a fulfillment record.

### P0-02: Refunds and chargebacks do not revoke or suspend entitlements

Current behavior:

- Refund and chargeback callbacks are accepted and persisted as payment events.
- `_status_from_event` maps them to `refunded` and `chargeback`.
- No code path updates user entitlement, access-key status, control-panel state, or risk flags.
- Admin Freekassa refund endpoint does not update local order/access state.

Risk:

- Refunded or charged-back users can retain paid access.
- Fraud response depends on manual discovery rather than deterministic backend state.
- Admin payment ledger can show `refunded` while the user remains `paid_unlimited`.

Required fix:

- Introduce entitlement grant records with reversible status.
- On refund/chargeback, revoke the associated unredeemed key or suspend/revoke the redeemed entitlement grant.
- Sync control plane after reversal and record sync status.

### P0-03: Paid callback idempotency is event-id based, not order-fulfillment based

Current behavior:

- Callback events are unique by `(provider, event_type, external_id)`.
- `_apply_external_paid_order` runs for any non-duplicate signed paid result.
- There is no fulfilled-order guard such as `(provider, order_id, grant_type)` or `external_orders.fulfilled_at`.

Risk:

- A second valid paid result for the same order with a different provider transaction/event ID can extend access again.
- Tests cover same external ID replay, not same order with different external IDs.

Required fix:

- Add an order-level fulfillment guard.
- A paid order may create exactly one activation-key issuance or one explicit direct entitlement grant.
- Store fulfillment attempt/result with immutable idempotency key.

## P1 Issues

### P1-01: Paid DB entitlement and control-plane provisioning are not represented as one recoverable workflow

Current behavior:

- `_apply_external_paid_order` commits DB entitlement changes.
- `_handle_payment_callback` then best-effort calls `_sync_user_after_paid_purchase`, but only if `tg_id` is present in callback payload.
- If `tg_id` is inferred from `ExternalOrder` rather than callback payload, DB activation can occur without sync.
- Sync failures are returned in callback response but no durable provisioning job/state is written.

Risk:

- User appears paid in API but may not be provisioned on nodes.
- Retrying safely requires log inspection or manual admin action.

Required fix:

- Persist provisioning status and enqueue retryable sync after entitlement grant or key redeem.
- Use the resolved fulfillment user ID from `_apply_external_paid_order`, not only raw callback payload.

### P1-02: Access keys reuse `gift_cards` and lack lifecycle authority

Current behavior:

- Admin issue writes `GiftCard(code, card_type, created_by)`.
- Redeem sets `redeemed_by/redeemed_at`.
- No separate activation-key table exists.

Risk:

- Cannot distinguish purchased key, gift key, admin key, promo key, replacement key, revoked key, expired key, or refunded key.
- Cannot reliably answer who bought a key, which order paid for it, whether the key is transferable, or what grant it produced.
- Plain key code is the lookup/unique value.

Required fix:

- Add a dedicated `activation_keys` table and keep `gift_cards` only for legacy gift compatibility.
- Store a keyed hash for lookup and only expose raw key at issuance time.

### P1-03: Admin payment reconcile is not fulfillment-safe

Current behavior:

- Reconcile can set arbitrary allowed order status with a note.
- Marking `paid` sets `paid_at`.
- Marking `refunded` or `chargeback` does not reverse access.
- No fulfillment action is attached to the reconcile decision.

Risk:

- Operators can create mismatched state: paid order without key, refunded order with active access, or chargeback order without suspension.

Required fix:

- Split status annotation from fulfillment action.
- Require an explicit action enum: `mark_review_only`, `issue_key`, `revoke_key`, `revoke_entitlement`, `no_access_change`.
- Require target grant/key IDs for reversal actions.

### P1-04: Amount/currency validation is not enforced at callback fulfillment time

Current behavior:

- `_apply_external_paid_order` resolves plan from payload or existing order and applies days.
- It does not compare callback amount/currency against `external_orders.amount/currency` or plan price before granting.

Risk:

- A signed provider event with an unexpected amount can still fulfill the plan if status is paid and order/user resolution succeeds.

Required fix:

- Compare normalized paid amount/currency/provider/order ID against the stored order.
- Route mismatches to `manual_review` without entitlement/key issuance.

### P1-05: Two redeem systems can diverge

Current behavior:

- `/api/access-keys/redeem` uses `_apply_access_key_to_user`.
- `/api/gift/redeem` uses `gift_cards_service.redeem_gift_card`.
- Both mutate users and sync control panel differently.

Risk:

- Key-first changes could leave legacy gift redeem with weaker checks or different state transitions.

Required fix:

- Move shared entitlement grant creation into one service.
- Keep gift redeem as a wrapper that creates the same `entitlement_grants` record.

## P2 Issues

### P2-01: Access-key status endpoint returns issuer/redeemer numeric IDs

Current behavior:

- `_access_key_status_payload` returns `created_by` and `redeemed_by`.

Risk:

- Public unauthenticated status lookup can disclose account IDs for redeemed keys.

Required fix:

- Public status should return only `exists`, `redeemed`, `plan`, `days`, and generic eligibility.
- Admin-only status can include IDs.

### P2-02: Key status lookup has no stable public error taxonomy

Current behavior:

- Missing key returns 404, unsupported key returns 400, redeemed key returns status payload.

Risk:

- Client can handle this, but beta UX will be easier if the API returns stable `code` values like `not_found`, `unsupported`, `redeemed`, `available`.

Required fix:

- Add `status_code` or `reason` enum in response/errors.

### P2-03: DB indexes are adequate for current small beta, but not for operator payment queries

Current behavior:

- `external_orders` has single-column indexes plus unique provider/order.
- Admin ledger filters by status/provider/search and sorts by `created_at`.

Risk:

- Larger callback volume will make status/provider/time queries slower.

Required fix:

- Add composite indexes listed in migration requirements.

## Proposed Implementation Work

1. Introduce `activation_keys` and `entitlement_grants`.
2. Make RUB paid callback create or reuse a key issuance record for the order.
3. Change public checkout completion to return "key issued" state for the bound account or follow-up retrieval endpoint, not direct paid access.
4. Make `/api/access-keys/redeem` create an `entitlement_grants` record and then update user effective fields as a projection.
5. Add order-level fulfillment idempotency: one paid order creates one key/grant.
6. Add reversal workflow for refund/chargeback:
   - unredeemed key -> `revoked`
   - redeemed key -> grant `revoked`, user recomputed/downgraded, panel sync queued
7. Add durable provisioning outbox:
   - `pending`, `in_progress`, `succeeded`, `failed`, `retry_after`, `last_error`
8. Split admin reconcile into ledger status and fulfillment action.
9. Consolidate legacy gift redeem and access-key redeem through the same entitlement service.
10. Add full tests before public beta promotion.

## Exact Verification Commands

Run from `C:/Users/kiwun/.config/superpowers/worktrees/VPN/open-beta-v4`.

Focused current-regression commands:

```powershell
python -m pytest portal_bot/tests/test_app_first_api.py
python -m pytest portal_bot/tests/test_app_first_service.py
python -m pytest tests/test_api_payments_callbacks.py
python -m pytest tests/test_admin_payments_api.py
python -m pytest tests/test_api_auth_and_tickets.py -k "gift or access or payment or ticket"
python -m pytest tests/test_api_lifecycle_smoke.py
python -m pytest tests/test_bot_paywall.py -k "payment or gift or redeem"
```

Required new test commands after implementation:

```powershell
python -m pytest tests/test_api_payments_callbacks.py -k "key_first or refund or chargeback or idempotent"
python -m pytest tests/test_activation_keys_api.py
python -m pytest tests/test_entitlement_grants.py
python -m pytest tests/test_admin_payments_api.py -k "reconcile or revoke or issue_key"
python -m pytest tests/test_migrations_entitlements.py
```

Full backend confidence command:

```powershell
python -m pytest portal_bot/tests tests/test_api_payments_callbacks.py tests/test_admin_payments_api.py tests/test_api_auth_and_tickets.py tests/test_api_lifecycle_smoke.py tests/test_bot_paywall.py
```

## API Contract Map

### App-first session and profile

| Endpoint | Current contract | Key-first impact |
| --- | --- | --- |
| `POST /api/client/session/start-trial` | Creates/reuses app account by `install_id`; returns session token, subscription URL, access policy, client policy, provisioning state. | Keep. Trial remains app-first and direct because it is not a paid key purchase. |
| `GET /api/auth/session` | Returns current app/Telegram/email session identity. | Include key/redeem eligibility summary after key service exists. |
| `GET /api/dashboard` | Returns access status and continuation data. | Should show unredeemed purchased keys and redeemed grant status. |
| `GET /api/client/profile/managed` | Returns managed client profile for current user. | Should reflect effective entitlement projection after grant/revocation. |

### Key purchase, status, and redeem

| Endpoint | Current contract | Required contract |
| --- | --- | --- |
| `GET /api/access-keys/status/{key}` | Unauthenticated key status from `gift_cards`. | Public-safe status from `activation_keys` by key hash; no buyer/redeemer IDs. |
| `POST /api/access-keys/redeem` | Auth required; applies key directly to user and marks gift card redeemed. | Auth required; atomically creates `entitlement_grants`, marks key redeemed, writes projection, queues provisioning. |
| `POST /api/admin/access-keys/issue` | Admin creates `GiftCard` rows. | Admin creates `activation_keys` with `source=admin`, no order binding required but lifecycle/audit required. |
| `GET /api/admin/gift-codes` / `POST /api/admin/gift-codes` | Legacy gift-code admin path. | Keep as compatibility or route through activation-key service with `source=legacy_gift`. |

### Payments

| Endpoint | Current contract | Required contract |
| --- | --- | --- |
| `GET /api/payments/providers` | Lists enabled RUB providers. | Keep. |
| `POST /api/payments/orders/create` | Authenticated account-bound order. | Keep for continuation; fulfillment should issue key on paid. |
| `POST /api/payments/orders/create-public` | Signed checkout-ticket order, still bound to `tg_id`. | For public key-first, allow buyer session or checkout ticket, but paid result issues key inventory rather than paid access. |
| `POST/GET /api/payments/result/{provider}` | Persist event; paid result applies direct entitlement. | Persist event; paid result validates order and issues/reuses activation key. |
| `POST/GET /api/payments/refund/{provider}` | Persist event/status only. | Revoke key/grant and queue provisioning sync. |
| `POST/GET /api/payments/chargeback/{provider}` | Persist event/status only. | Suspend/revoke grant, risk-flag account, queue provisioning sync. |
| `POST /api/payments/freekassa/orders/{order_id}/refund` | Calls remote refund API only. | Also creates local refund intent/result and applies reversal when provider confirms. |
| `POST /api/admin/payments/orders/{provider}/{order_id}/reconcile` | Status annotation with audit note. | Status annotation plus explicit safe fulfillment/reversal action. |

### Support/admin

| Endpoint | Current contract | Key-first impact |
| --- | --- | --- |
| `/api/tickets*` | Authenticated support tickets work for app sessions. | Add key/order/grant references to support context where safe. |
| `GET /api/admin/payments/orders` | Lists orders and callback state without raw payload. | Add key/grant/provisioning summary columns. |
| `GET /api/admin/users/{tg_id}` | User detail and key/admin controls. | Show effective entitlements from grants, not only mutable user fields. |

## Entitlement State Machine

Current implicit states are derived from `users`:

```text
no_user
  -> app_trial_created
  -> trial_premium
  -> bonus_premium
  -> paid_unlimited
  -> free_monthly
  -> free_soft_mode
  -> expired_or_blocked
```

Required key-first explicit state machine:

```text
activation_key.issued
  -> activation_key.reserved_for_order
  -> activation_key.paid_available
  -> activation_key.redeeming
  -> activation_key.redeemed
  -> activation_key.revoked

entitlement_grant.pending
  -> entitlement_grant.active
  -> entitlement_grant.provisioning_pending
  -> entitlement_grant.provisioned
  -> entitlement_grant.expired
  -> entitlement_grant.revocation_pending
  -> entitlement_grant.revoked
  -> entitlement_grant.provisioning_failed
```

Rules:

- User access policy should be a projection from active grants plus trial/free fallback.
- Paid key redemption creates one grant.
- Refund or chargeback must revoke the key/grant before or alongside user projection changes.
- Provisioning failure must not erase the grant; it should remain retryable and visible.

## Payment Order State Machine

Current order states:

```text
created
  -> pending
  -> paid
  -> failed
  -> cancelled
  -> manual_review
  -> pending_verification
  -> refunded
  -> chargeback
```

Required order plus fulfillment state machine:

```text
order.created
  -> order.pending_provider
  -> order.callback_received
  -> order.validated_paid
  -> order.fulfillment_pending
  -> order.key_issued
  -> order.completed

order.callback_received
  -> order.manual_review
  -> order.failed
  -> order.cancelled

order.completed
  -> order.refund_pending
  -> order.refunded_key_revoked
  -> order.refunded_grant_revoked

order.completed
  -> order.chargeback_received
  -> order.chargeback_grant_suspended
  -> order.chargeback_closed
```

Idempotency rules:

- Callback event uniqueness stays `(provider, event_type, external_id)`.
- Fulfillment uniqueness must be `(provider, order_id, fulfillment_kind)` or an explicit `external_orders.fulfilled_at` plus `activation_key_id`.
- Reversal uniqueness must be `(provider, order_id, reversal_kind)`.

## DB/Index Audit

### Current relevant tables

| Table | Current role | Notes |
| --- | --- | --- |
| `users` | Effective access projection and identity record. | Holds mutable entitlement fields directly. |
| `gift_cards` | Legacy gift codes and current admin access keys. | Too thin for key-first commercial authority. |
| `external_orders` | Provider order ledger. | Unique `(provider, order_id)` exists. |
| `external_payment_events` | Callback event audit/idempotency. | Unique `(provider, event_type, external_id)` exists. |
| `pay_attempts` | Telegram Stars attempt state. | Separate from RUB orders/key state. |
| `plan_catalog` | Plan price/duration/device limits. | Should feed key/grant issuance. |
| `admin_audit` | Operator action audit. | Should include key/grant IDs after implementation. |

### Current indexes

| Index | Current status |
| --- | --- |
| `uq_users_app_install_id` | Present for SQLite/Postgres partial uniqueness. |
| `uq_users_linked_telegram_id` | Present for SQLite/Postgres partial uniqueness. |
| `uq_external_orders_provider_order` | Present. |
| `ix_external_orders_order_id` | Present. |
| `ix_external_orders_tg_id` | Present. |
| `ix_external_orders_provider` | Present. |
| `uq_external_payment_events_provider_type_extid` | Present. |
| `ix_external_payment_events_order_id` | Present. |
| `uq_pay_attempts_invoice_payload` | Present. |
| `ix_pay_attempts_tg_status_started` | Present. |

### DB gaps

- No `activation_keys`.
- No `entitlement_grants`.
- No `entitlement_events` or immutable grant history.
- No durable provisioning outbox.
- No order-level fulfilled guard.
- No refund/chargeback-to-grant linkage.
- No key hash lookup separated from raw key display.
- No composite indexes for admin order filters by provider/status/created time.

## Missing Tests

Required before beta promotion:

1. Paid RUB callback issues one activation key and does not mutate `users.sub_type` before redeem.
2. Paid callback with same order ID and different external IDs does not issue or apply twice.
3. Paid callback with wrong amount/currency goes to manual review and does not issue key.
4. Paid callback with order-bound `tg_id` but callback payload missing `tg_id` still queues provisioning or key issuance against the resolved order owner.
5. Refund callback revokes unredeemed key.
6. Refund callback revokes redeemed grant and downgrades/recomputes user access.
7. Chargeback callback suspends/revokes grant and records risk state.
8. Admin refund endpoint creates local reversal intent and does not leave access active after confirmed refund.
9. Admin reconcile `paid + issue_key` is idempotent and audited.
10. Admin reconcile `refunded/chargeback + revoke` is idempotent and audited.
11. `/api/access-keys/redeem` accepts a payment-issued key and creates exactly one grant under concurrent attempts.
12. `/api/access-keys/status/{key}` public response omits buyer/redeemer IDs.
13. Legacy `/api/gift/redeem` routes through the same entitlement service or has parity tests.
14. Migration tests validate new tables/indexes on SQLite and emitted Postgres SQL path.
15. Provisioning outbox retries after panel sync failure and eventually marks success.

## Exact Migration Requirements

Add these through `portal_bot/models.py` and idempotent SQLite/Postgres migrations in `portal_bot/migrations.py`.

### `activation_keys`

Columns:

- `id` primary key
- `key_hash` string(64), not null
- `key_prefix` string(16), not null
- `source` string(32), not null: `payment`, `admin`, `legacy_gift`, `replacement`
- `status` string(32), not null: `issued`, `paid_available`, `redeemed`, `revoked`, `expired`
- `plan_code` string(32), not null
- `duration_days` integer, not null
- `device_limit` integer, not null
- `buyer_tg_id` bigint nullable
- `redeemed_by_tg_id` bigint nullable
- `external_order_id` integer nullable
- `provider` string(32) nullable
- `order_id` string(128) nullable
- `issued_by_tg_id` bigint nullable
- `issued_at` datetime not null
- `paid_at` datetime nullable
- `redeemed_at` datetime nullable
- `revoked_at` datetime nullable
- `expires_at` datetime nullable
- `metadata_json` text nullable

Indexes:

- unique `uq_activation_keys_key_hash` on `key_hash`
- unique partial `uq_activation_keys_provider_order_payment` on `(provider, order_id)` where `source='payment'`
- `ix_activation_keys_buyer_status` on `(buyer_tg_id, status)`
- `ix_activation_keys_redeemed_by` on `redeemed_by_tg_id`
- `ix_activation_keys_order` on `(provider, order_id)`
- `ix_activation_keys_status_issued` on `(status, issued_at)`

### `entitlement_grants`

Columns:

- `id` primary key
- `tg_id` bigint not null
- `activation_key_id` integer nullable
- `source` string(32), not null: `key_redeem`, `trial`, `admin`, `legacy_gift`, `payment_direct_legacy`
- `status` string(32), not null: `pending`, `active`, `revocation_pending`, `revoked`, `expired`
- `plan_code` string(32), not null
- `starts_at` datetime not null
- `expires_at` datetime nullable
- `revoked_at` datetime nullable
- `reversal_reason` string(64) nullable
- `provider` string(32) nullable
- `order_id` string(128) nullable
- `created_at` datetime not null
- `updated_at` datetime not null
- `metadata_json` text nullable

Indexes:

- unique partial `uq_entitlement_grants_activation_key` on `activation_key_id` where not null
- unique partial `uq_entitlement_grants_provider_order_source` on `(provider, order_id, source)` where provider/order not null
- `ix_entitlement_grants_tg_status_exp` on `(tg_id, status, expires_at)`
- `ix_entitlement_grants_order` on `(provider, order_id)`

### `entitlement_events`

Columns:

- `id` primary key
- `grant_id` integer nullable
- `activation_key_id` integer nullable
- `event_type` string(64), not null
- `actor_tg_id` bigint nullable
- `provider` string(32) nullable
- `order_id` string(128) nullable
- `meta_json` text nullable
- `created_at` datetime not null

Indexes:

- `ix_entitlement_events_grant_created` on `(grant_id, created_at)`
- `ix_entitlement_events_key_created` on `(activation_key_id, created_at)`
- `ix_entitlement_events_order_created` on `(provider, order_id, created_at)`

### `provisioning_jobs`

Columns:

- `id` primary key
- `tg_id` bigint not null
- `grant_id` integer nullable
- `job_type` string(32), not null: `sync_paid`, `sync_free`, `revoke`, `disable_nodes`
- `status` string(32), not null: `pending`, `running`, `succeeded`, `failed`
- `attempt_count` integer not null default 0
- `next_attempt_at` datetime nullable
- `last_attempt_at` datetime nullable
- `last_error` string(1000) nullable
- `created_at` datetime not null
- `updated_at` datetime not null

Indexes:

- `ix_provisioning_jobs_status_next` on `(status, next_attempt_at)`
- `ix_provisioning_jobs_tg_status` on `(tg_id, status)`
- unique partial `uq_provisioning_jobs_grant_type_pending` on `(grant_id, job_type)` where `status in ('pending','running')`

### Existing table/index additions

`external_orders` additions:

- `fulfilled_at` datetime nullable
- `activation_key_id` integer nullable
- `entitlement_grant_id` integer nullable
- `reversal_status` string(32) nullable
- `reversed_at` datetime nullable
- `amount_expected` float nullable
- `currency_expected` string(16) nullable

Indexes:

- `ix_external_orders_provider_status_created` on `(provider, status, created_at)`
- `ix_external_orders_tg_created` on `(tg_id, created_at)`
- unique partial `uq_external_orders_provider_order_fulfilled` is optional if using `fulfilled_at` plus activation key unique order guard; prefer fulfillment uniqueness on `activation_keys`.

`external_payment_events` additions:

- `status` string(32) nullable
- `processed_at` datetime nullable
- `processing_error` string(1000) nullable

Indexes:

- `ix_external_payment_events_order_type_created` on `(provider, order_id, event_type, created_at)`

`gift_cards` compatibility additions if not immediately migrated:

- `activation_key_id` integer nullable
- `legacy_migrated_at` datetime nullable
- index `ix_gift_cards_activation_key_id`

## Final Readiness Call

Backend is not ready for Open Beta v4 key-first commercialization until the paid callback path issues activation keys, refund/chargeback callbacks reverse associated keys/grants, and fulfillment idempotency moves from callback-event uniqueness to order-level key/grant uniqueness.


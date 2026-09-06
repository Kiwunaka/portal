# Payment Reconciliation

Last updated: 2026-07-18

## Goal

Keep paid access aligned with provider truth without relying on undocumented refund or chargeback webhook behavior.

For Lava.top, reconciliation must inspect the local `ExternalOrder` plus the latest `ExternalPaymentEvent`. Anonymous public purchases may have `tg_id=null`; those rows fulfill by an emailed access key recorded in internal order metadata, not by immediate account extension.

`manual_review` is the expected state for validly authenticated callbacks with mismatched amount, currency, plan, or missing local order. Operators should not manually mark those paid until provider evidence and order intent are attached with secrets redacted.

FreeKassa is not an active public provider. Its retained callbacks must additionally
match the persisted merchant/source and immutable entitlement snapshot. Incomplete
SCI, generic HMAC while compatibility is disabled, an unknown local order, or a
missing/inconsistent snapshot cannot be repaired from callback fields. Preserve the
redacted event and route the case to manual review; do not synthesize an order or
grant. Enabling FreeKassa requires a new provider-specific evidence packet rather
than reusing Lava.top proof.

## Minimum Beta Procedure

1. Export or inspect provider-side order state.
2. Match provider external id to local order id.
3. Confirm amount, currency, plan, account/session, and final provider state.
4. Move ambiguous rows to manual review.
5. Do not grant new access for failed, cancelled, refunded, chargeback, or ambiguous states.
6. Record redacted evidence under the release work-order provider evidence folder.
7. For any proposed FreeKassa enablement, confirm generic HMAC remains disabled,
   both merchant IDs map to their exact source, and a created order retains its
   entitlement snapshot through callback replay.
8. For a commercial v2 order, compare the stored order-intent lineage with the
   bound reservation. Provider/callback fields must not be used to fill missing
   campaign, creative, assignment, price or revision data.

## Commercial reservation reconciliation

A commercial order is valid only when its immutable
`pokrov-payment-order-intent-v2` names the same reservation that is bound to the
local order. Before payment the reservation is `bound`; successful durable
fulfillment moves it to `consumed` and increments campaign, offer and assignment
paid counters once. Callback replay must leave all four unchanged.

A provider-checkout `error` keeps the order `created` and retryable until the
absolute hold. After that deadline the reservation may become `expired` with a
release timestamp, but the order intent must not be edited or deleted. Do not
expire a reservation merely because the callback is delayed when local checkout
evidence is `ready`. A refund or chargeback leaves the reservation `consumed`
and preserves gross lineage; reconcile refund/net separately instead of
decrementing or rewriting the original campaign attribution.

Any missing/foreign reservation, subject/price/revision mismatch, paid counter
conflict or callback attempt to synthesize attribution is `manual_review`. Keep
the redacted order ID and stable commercial IDs; never copy the offer token,
buyer identity, provider payload or signature into an operator note.

## Consumer return reconciliation

The payment-return token and browser projection are not payment authority.
When a customer reports a return-page mismatch, compare the current local order
and provider evidence through the normal finance-ops queue; do not ask for the
token or paste it into a ticket. The public status endpoint deliberately omits
the order ID and may return only `processing`, `paid`, `failed`, `cancelled`,
`manual_review` or `expired`.

Treat `manual_review` and `expired` as support/retry guidance, not provider
state mutation. A refund or chargeback appears as consumer `failed` while its
specific ledger state remains available to operators. Never repair payment,
reservation, attribution or entitlement rows from a browser screenshot,
redirect query or client analytics event.

## Evidence Terms

`refund evidence` means practical proof that a refund path is handled end to end:

- a Lava.top refund callback, dashboard refund export, or operator replay fixture with secrets redacted
- the matching local `ExternalOrder` moves to `refunded` or `manual_review`
- the user or issued access key is not silently extended after the refund
- the evidence note includes order id, provider external id, amount, currency, plan, previous local status, final local status, and redaction note

`chargeback evidence` means practical proof that a dispute/chargeback path is not treated as paid:

- a provider dispute/chargeback callback, dashboard proof, or operator replay fixture with secrets redacted
- the local order is marked `chargeback` or `manual_review`
- existing access is not silently renewed by that order after the dispute state is known
- the evidence note records whether any manual access action was required

`reconciliation drill` means an operator manually compares one Lava.top order with the local ledger:

1. pick a paid, failed, refunded, chargeback, or suspicious order
2. compare provider id, local order id, amount, currency, plan, payment method, and final provider status
3. update the local status only through the documented admin/API/manual-review path
4. write a redacted audit note without card data, buyer personal data, secrets, raw callback signatures, or full provider payloads

`finance-ops queue` means an admin/operator list where payment rows are grouped by action state, not just by raw provider status. Minimum queues:

- `paid`: verify fulfillment exists and is idempotent
- `failed`: confirm no access was granted
- `refunded`: confirm access was not extended or was manually reviewed
- `chargeback`: confirm the disputed order is not counted as clean revenue
- `manual_review`: compare provider truth with local intent and attach redacted evidence

Production checkout maturity is not closed until the queue and the three evidence classes above have at least one current redacted proof each for Lava.top.

## Entitlement outbox reconciliation

Every newly applied or repaired account-owned provider grant must have exactly
one `payment_entitlement.applied` row for its provider/order/schema. Operators
must treat the grant and local order as authority; outbox delivery and
`payment_entitlement_sync` are downstream recovery evidence only.

Check the following as one chain:

1. the paid local order points to one active provider-payment grant;
2. the outbox row has the same grant/provider/order and is `pending`,
   `processing`, `delivered` or `dead_letter`;
3. a delivered row has one idempotent payment-sync provisioning job;
4. `pending` age, stale `processing`, retry count and `dead_letter` reason are
   investigated without editing the payload or repeating the payment grant;
5. a reversed grant must not complete a queued provisioning sync.

Worker errors retain only closed error codes. Never paste payloads, account
identifiers, provider bodies or panel credentials into an operator note. There
is no direct manual requeue surface in this candidate; do not edit queue rows.

An old `processing` row can be locked by an active dispatch transaction.
PostgreSQL recovery skips those locked rows and revisits eligible abandoned
claims later. Age alone does not prove abandonment or authorize a second
delivery. Dispatch/failure finalization retain the claim lock until commit
or rollback.

## Commercial attribution reconciliation

For a commercial order, reconcile immutable order intent, consumed reservation,
provider-payment grant and `commercial_conversions` as one chain:

1. exactly one `paid` row exists for provider/order and matches its campaign,
   offer, creative, variant, assignment, reservation, impression/click IDs,
   integer amount, revisions and capacity-cost units;
2. refund or chargeback adds exactly one `reversed` row with the original paid
   amount while leaving the paid row and reservation unchanged;
3. first-connect/D7/D30 rows reference only durable
   `observer_connection` evidence; funnel/client events are not accepted;
4. D7 is `paid_at+[7d,14d)` and D30 is `paid_at+[30d,37d)`; renewal requires a
   later provider-payment grant for the same account;
5. the admin payment summary's `commercial_attribution.freshness` is explicit;
   a missing/stale projection is investigated against payment/observer truth,
   never repaired from marketing telemetry.

## Operator Center v2 read and repair path

The canonical operator surface uses the production-only Admin API v2 money
workspace:

- `GET /api/admin/v2/money/payments/summary` for period totals and independent
  mismatch queues;
- `GET /api/admin/v2/money/payments/orders` for the bounded work list;
- `GET /api/admin/v2/money/payments/orders/{provider}/{order_id}` for redacted
  order → signed callback → claim → grant → outbox lineage;
- `payment.reconcile` through `/api/admin/v2/money/action-intents` for guarded
  repair. The legacy mutation endpoint is not called by the canonical screen.

The 360 view never exposes callback/order/claim/grant/outbox raw JSON, buyer
email, provider token or external event identifier. An order marked paid while
its grant is not delivered remains in `paid_without_entitlement`; telemetry or
a successful browser return cannot clear that queue or authorize access.

Projection rows deliberately have no raw account, Telegram, email, device,
node, callback body, offer token, checkout destination or entitlement secret.
Do not add those values to reconciliation notes.

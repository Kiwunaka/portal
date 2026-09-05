# Payment State Machine

Last updated: 2026-08-21

| State | Meaning | Access effect |
| --- | --- | --- |
| `created` | Local order stored before provider redirect. | none |
| `pending` | Provider invoice created and waiting. | none |
| `pending_verification` | Callback observed but provider authentication failed or is incomplete. | none |
| `paid` | Authenticated provider success applied idempotently. | fulfill |
| `failed` | Provider or local failure. | none |
| `cancelled` | User or provider cancellation. | none |
| `refunded` | Refund found by operator/provider reconciliation. | no new access |
| `chargeback` | Dispute found by reconciliation. | no new access; review |
| `manual_review` | Ambiguous auth, amount, currency, account, or payload. | none |

Lava.top paid checkout is enabled for the current outside-store beta on the
retained evidence-backed path. Stable payment maturity remains unproven until
refund, chargeback, reconciliation, and fulfillment-ledger evidence is current
for the exact candidate.

## Account Ownership Boundary

The repository candidate implements an additive account foundation: UUID `accounts.id`
is persisted and `users.account_id` is a nullable projection. The
public numeric `account_id` remains a compatibility projection. Device sessions
use persisted rotating sessions; legacy browser, Telegram, and email tokens retain
a stateless bearer compatibility path, not account or payment authority.
Rotating sessions, recovery exchange, durable provider-payment grants,
account-owned fulfillment, and entitlement-ledger authority exist in this
repository candidate. Production deployment of account foundation is not proven.
A completed production cutover, mixed-fleet safety, and full migration must not be claimed without exact current evidence.

## Lava.top Normalization

For `lavatop`, local order creation stores an `ExternalOrder` before redirect. The provider invoice request is sent to `/api/v3/invoice` with `clientUtm.utm_content=<local order_id>` and optional per-plan `offerId` mapping.

A repeated public base-price `intent_id` is scoped to its server-resolved owner
and serialized with a PostgreSQL transaction advisory lock before local creation.
Only a request digest is stored with the immutable order. Changed provider, plan,
source, promo, currency, payment method or attribution input returns a conflict.
Matching retries and valid already-bound commercial reservations return order
status for reconciliation; they do not repeat provider invoice creation. No lock
or database session spans provider I/O, and no checkout URL is stored for retry.
A timeout/provider error may leave a committed non-fulfilling `created` order;
status recovery does not classify it as paid or authorize a second invoice.

A signed base quote (`bq1`) uses its embedded UUID as the same owner-scoped retry
identity. The signature is verified before lookup. Exact committed retries recover
the existing order even after quote expiry; new orders must also pass expiry and
current server pricing/entitlement-duration binding checks. No commercial
reservation or migration is added. Rejected calculations create no order and make
no provider call; the browser refreshes the calculation before a new explicit click.

The creation boundary is explicitly two-phase and never carries a database
session across provider I/O. Before the provider call, the local `created` row
stores a canonical intent digest over provider/order, owner, amount, currency,
plan, source and entitlement snapshot. A second short transaction validates the
same intent before moving `created` to `pending`. Provider checkout URL, query,
request body and raw response are not durable metadata; only closed allowlisted
provider identifiers/status and `url_present` may be stored. A provider error
keeps the order at non-fulfilling `created` with a bounded error code. Repeating
application for the same order is idempotent only for the exact stored intent,
and a late paid callback cannot be regressed to `pending` by checkout completion.

When order creation carries a signed commercial `offer_token`, the first local
transaction additionally locks and revalidates the current campaign, offer,
creative, assignment and reservation plus server-derived subject, manifest
price/revisions, deadlines, legal/channel/capacity policy and finite paid caps.
It never accepts client price, discount, commercial IDs or quota as authority.
Acceptance binds one unique reservation to one order and stores
`pokrov-payment-order-intent-v2` with an identity-free commercial lineage and
token SHA-256. An exact valid retry returns the same order; provider, subject,
price, revision, deadline, policy, quota or reservation drift stops before the
provider call.

Commercial retry, callback consume and failed-checkout expiry acquire the
campaign quota-owner lock before payment-order/reservation locks. This is the
single PostgreSQL lock order for those paths; local SQLite tests are not a claim
of live two-connection PostgreSQL concurrency proof.

Provider failure keeps the order `created` and the reservation `bound` until
its absolute hold. A due reservation may be expired/released only when the
local order has bounded provider-checkout `error` evidence; a ready checkout is
kept for a delayed callback. Authenticated paid fulfillment consumes the same
reservation in the entitlement transaction and advances campaign, offer and
assignment paid counters once. Callback payloads cannot add commercial fields.
Refund/chargeback changes payment and entitlement state but retains the original
intent and consumed lineage.

For the one-time `start_99` plan, order creation must stop before provider invoice creation when the linked user has `first_purchase_done=true` or an existing paid Lava.top order. This guard prevents duplicate one-time offers even if older fulfillment evidence missed the user flag.

Incoming Lava.top result webhooks must pass `X-Api-Key` or Basic webhook authentication before fulfillment. `payment.success` and `subscription.recurring.payment.success` normalize through the provider `status` value, where `completed` grants access. `payment.failed`, recurring payment failures, and `subscription.cancelled` normalize to non-fulfilling states.

Before any Lava.top paid callback fulfills, the backend validates local order binding, amount, currency, and plan. Any missing local order, amount mismatch, currency mismatch, or plan mismatch becomes `manual_review` and does not grant access.

For authenticated cabinet and Telegram-bound orders, fulfillment extends the linked account. The cabinet can show the single `connect.pokrov.space` subscription link and QR after access is active; the bot also sends that link after a paid Telegram-bound callback as a beta-stage manual import fallback. Anonymous public orders do not receive links in API responses; they receive one emailed access key after fulfillment.

## Consumer Return Projection

Legacy GET `/pay/success` renders a neutral status/cabinet continuation. POST to
that route acknowledges only receipt with `status=unverified`. Neither path
looks up or mutates payment authority, and neither presents a redirect as paid.

The browser-facing return projection is deliberately smaller than the payment
ledger. `POST /api/payments/orders/status` maps current local truth to exactly
six states:

| Consumer state | Source condition | Consumer action |
| --- | --- | --- |
| `processing` | durable order is `created`/`pending` and both signed token and any commercial hold remain live | poll at the server delay |
| `paid` | durable local order is paid | stop; refresh account/access state |
| `failed` | order failed, was refunded/charged back, or another terminal non-retryable payment failure is authoritative | stop; do not imply access |
| `cancelled` | durable order is cancelled | stop; allow a fresh checkout only through normal server validation |
| `manual_review` | local payment truth is ambiguous or requires operator review | stop; show support route |
| `expired` | signed return capability, pending window, or bound commercial hold expired | stop; start a new server-validated checkout |

This projection is read-only. It never advances an order, consumes/releases a
reservation, grants/revokes access or interprets callback fields. The signed
return capability is identity-free and never travels in the provider redirect
URL. Refund/chargeback intentionally collapse to consumer `failed` while their
distinct ledger states and reconciliation evidence remain unchanged.

The cabinet renders all six states from this projection. A `paid` response
triggers an authenticated account refresh before the UI says access is active.
If payment is paid but the refreshed account is still inactive (or refresh
fails), the cabinet shows a distinct paid/access-stale recovery with explicit
`Проверить доступ` and support actions; it does not manufacture entitlement
from the payment-return response. `processing` alone polls at the server delay.
`failed`, `cancelled`, and `expired` return to a new server-validated checkout,
while `manual_review` routes to support.

## FreeKassa Compatibility Boundary

FreeKassa is retained as disabled compatibility code, not as an enabled public
provider. The active public provider configuration remains Lava.top-only until a
separate exact-candidate merchant, callback, fulfillment, reconciliation, and
rollback evidence packet is retained.

FreeKassa SCI handling is fail-closed:

- one provider parser accepts only known top-level/nested response shapes and
  the exact configured HTTPS checkout host; missing/invalid URL is terminal for
  that request and never falls back to `oa=0`;
- the presence of any SCI field requires the complete uppercase
  `MERCHANT_ID`, `AMOUNT`, `MERCHANT_ORDER_ID`, and `SIGN` shape; an incomplete
  SCI payload cannot downgrade to generic HMAC verification;
- generic HMAC compatibility requires
  `FREEKASSA_GENERIC_HMAC_COMPAT_ENABLED=true` and defaults off;
- a paid callback requires a pre-existing local `ExternalOrder`; an unknown
  signed order is retained only as a redacted event/manual-review fact and cannot
  create an order or grant;
- the configured merchant must map to the exact persisted `site` or `bot`
  source, while owner, optional source/plan fields, exact positive two-decimal
  amount, and optional currency must agree with local authority;
- callback data cannot rewrite owner, plan, source, campaign, promo, amount, or
  currency on an existing FreeKassa order;
- fulfillment uses the immutable entitlement snapshot captured at order creation.
  Missing or inconsistent snapshots are terminal manual-review outcomes, never a
  callback-plan or `1_month` fallback.

Account fulfillment records a durable `provider_payment` entitlement grant keyed
by provider/order while holding the canonical account row. Its interval starts
at `max(now, end of legitimate typed or classified legacy premium contributions)`.
A legacy `FREE` snapshot, free-cycle, or `free_monthly` credential expiry is
never a premium baseline. The first such account fact
may record one normalized referral transition and a `72 hour` hold; every linked
app/bot projection reads that same history. Callback and worker replay converge
to one immediate `+5 day` referred-friend grant and one held `+10 day`
referrer grant. Admin plan keys, gifts, promos, later renewals,
and client activity events are not first-payment authority.

An active `paid_access` provider grant and its
`payment_entitlement.applied` outbox event commit together. The outbox event is
unique by provider/order/schema and points to the grant without copying account
or provider payload data. The worker uses an atomic claim token, bounded retry,
stale-claim recovery and terminal dead-letter state, then creates one
idempotent `payment_entitlement_sync` provisioning job in the same dispatch
transaction that marks the event delivered. This downstream path may refresh
panel traffic/access state but is never payment authority. Invalid payload,
missing/mismatched grant, reversed grant or exhausted retry cannot grant or
extend access.

For an order whose immutable v2 intent contains commercial lineage, successful
reservation consume and the unique `commercial_conversions(stage=paid)` row
commit in the same authoritative fulfillment transaction. Callback replay
reuses that row. A refund/chargeback transaction preserves the paid row and
adds/reuses `stage=reversed` with the original gross amount as refund amount;
it never decrements or rewrites gross lineage.

Connection stages are outside payment authority but still server-owned. Only a
durable observer `ConnectionEvidence(evidence_kind=observer_connection)` linked
through the provider-payment grant may create `first_verified_connect`,
`retained_d7` in `paid_at+[7d,14d)`, or `retained_d30` in
`paid_at+[30d,37d)`. A later provider-payment grant may create `renewal` on the
later order. Browser clicks, funnel events and client-reported success are not
eligible evidence.

Historical compatibility backfill requires a successful provider/order row or
per-order Stars fulfillment evidence before creating a `provider_payment` fact.
A paid Stars attempt without that evidence is retained as a manual-review audit
marker and leaves callback repair open. The legacy
`User.first_purchase_done` flag alone produces only a manual-review marker,
because historical admin gifts could set it.

Backfill also records fulfillment provenance. Facts backed by explicit fulfilled
order metadata, or by an old successful payment plus a legacy paid projection,
are marked projection-applied and callback replay does not append days. Pending
provider fulfillment remains unapplied and upgrades exactly once. Backfill and
account merge normalize all facts by `paid_at` then provider/order, leaving
exactly one earliest `is_first_payment=true`; referral hold authority follows
that fact without rolling back an already released reward.

Telegram Stars payment confirmation (`PayAttempt.status=paid`) precedes and does
not replace canonical fulfillment. The handler commits the stable account-owned
Stars payment grant and applied projection before panel work. Replay resumes a
missing grant or pending projection, retries panel provisioning after failure,
and adds plan duration only once. A Stars dedupe marker may short-circuit only
when the matching grant is `paid_access` with durable applied provenance.
Panel success is followed by a required read-back/reconciliation transaction:
the owned panel UUID, email, `subId`, and node provenance update `User`,
`AccessKey`, applicable `UserNode`, and payment-grant evidence before completion
is marked. A validated owned legacy `node_code` is sufficient when the panel
lane has no positive database node ID; this path records durable `AccessKey` and
grant evidence and never creates a zero-ID `UserNode`. An existing-client
traffic update must also return success; `false` or an exception leaves the
Stars callback unprocessed and replayable while the durable paid grant remains
intact. The failure response carries an account-owned retry action keyed by the
persisted payment grant, so recovery does not depend on Telegram redelivering
the original polling update. Missing lane identity or cross-node key provenance
remains a retryable failure.
If local commit or marker persistence fails, replay uses the already-created
panel client and repeats reconciliation without extending entitlement again.

After durable Stars fulfillment completes, the bot sends one consolidated
success message instead of a provisioning message followed by a second receipt.
The current Bot API rich-message form is preferred when the installed runtime
supports it; an HTML fallback keeps the same actions and expandable receipt.
The receipt uses the real Telegram charge identifier, the access link remains a
manual app-first fallback, and the message is excluded from transient
auto-deletion. Message rendering or delivery failure must never roll back or
repeat the already-committed fulfillment. Creation and pre-checkout of new Stars
payments remain closed until their separate rollout gate is explicitly reopened.

Fulfillment is split by local order identity:

- `tg_id` present: extend the existing account and sync the control-plane access.
- `tg_id` absent with `buyer_email`: issue one access key, persist fulfillment metadata on `ExternalOrder.meta_json`, and deliver the key by email.
- duplicate callback event: return idempotent success without issuing another key or applying another extension.

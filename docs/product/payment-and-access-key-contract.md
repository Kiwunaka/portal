# Payment And Access-Key Contract

Last updated: 2026-08-21

## Current Rule

Paid checkout can be presented as live for the evidence-backed Lava.top public beta path. It must not be presented as a fully mature production payment system until refund/chargeback reconciliation has a separate current runbook and evidence.

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

## Target Contract

| Step | Requirement |
| --- | --- |
| Catalog | Provider availability and unavailable reason are visible to frontend and admin surfaces. |
| Order create | Local order state is stored before provider redirect. |
| Provider callback | Payload is authenticated before any state mutation. |
| Idempotency | Duplicate or replayed events do not duplicate access. |
| Fulfillment | Only normalized paid events can grant access or issue activation-key state. |
| Failure | Failed, cancelled, refunded, chargeback, and manual-review states do not fulfill access. |
| Reconciliation | Operators can review provider state without relying on undocumented refund webhooks. |

Marketing and cabinet checkout consume one server contract. Initial catalog,
provider capability and independent acquisition requests run in parallel;
offer preview follows the selected plan/promo and is the only source for final
price, benefit, absolute deadline, terms link and signed calculation. Marketing checkout
requires a valid, positive, unexpired preview and signed token even with an empty
promo. Plan, promo, checkout subject, provider, payment method or buyer changes
immediately invalidate its previous quote; debounce delays only the new request.
Late responses cannot restore an earlier input's quote. Expiry uses the server's
remaining hold with monotonic local elapsed time, and submit checks it again.
Once that hold expires, the checkout removes both the discounted amount and
the promo-applied confirmation; a workstation clock rollback cannot retain them.
Catalog/provider read results become visible independently of optional acquisition
completion. Read-only checkout fetches share one eight-second deadline across all API bases,
including response-body reads; replacing preview or debounced key inputs aborts
the old request. Explicit catalog/provider retry is read-only. API/provider error
bodies are not rendered to the buyer.
Checkout submits the signed offer token,
and the server revalidates the applicable price, revision and deadline before
provider I/O. Commercial offers additionally retain their legal, capacity and
quota checks under the existing reservation lock.

The provider capability response owns which methods are enabled. Return from a
provider is restored from a versioned identity-free token kept in browser
session storage, never from a token in the URL. Both surfaces strip return hints
and render only the six server states `processing`, `paid`, `failed`,
`cancelled`, `manual_review`, and `expired`. They do not calculate price,
restart an urgency deadline, infer remaining quota, or turn a callback/redirect
hint into payment or access truth.

The legacy `/pay/success` landing page is an unverified return receipt: it directs
the user to check the cabinet and does not state that money was received. Its POST
response is `ok=true, status=unverified`; redirect parameters or posted `paid`
values do not confirm an order or grant access.

Public base-price order requests may carry a subject-scoped UUID `intent_id`.
The server serializes that key in PostgreSQL, binds the normalized request digest
to the existing immutable order, and rejects changed parameters with HTTP 409.
A matching retry returns its current order and a read-only return token without
creating another provider invoice. Signed commercial offers retain their unique
reservation as retry identity. Recovery has no stored checkout URL: the browser
shows order verification and server payment status. A lost mutation response never
triggers automatic fallback POSTs; the explicit retry retains the original quote
and attribution and is labelled «Проверить заказ», not a newly quoted purchase.
Legacy callers omitting both identities do not gain retry deduplication.

Ordinary marketing checkout with no promo/offer ID now receives a signed `bq1`
calculation through `/api/public/offers/preview`. Anonymous checkout supplies the
receipt email; account checkout uses a verified ticket/auth subject. The same
server pricing function is used for preview and order creation, including eligible
referral and pending discounts. No campaign, assignment or commercial reservation
is manufactured for an ordinary purchase. The existing HMAC secret and bounded
quote TTL are reused, with a distinct signature prefix and no raw identity in the
token. Missing signing configuration keeps preview unavailable.

A base quote binds owner, tariff duration, RUB pricing details and commercial
revision. Before creating a new order the server checks signature, expiry, active
plan and the current calculation; changed price/discount/owner returns 409 and an
expired quote returns 410. This is a validated calculation, not a promise to honor
stale pricing until expiry. The browser refreshes a rejected calculation and asks
for another explicit payment click. A quote's signed UUID is its retry identity:
an exact retry may recover a committed order after quote expiry without repeating
provider I/O. Changed request parameters still conflict. Legacy API callers without
a quote retain server-side pricing; the marketing UI always requires a quote.
Local HTTP/browser proof uses isolated SQLite and a synthetic provider. PostgreSQL
concurrency, live provider operations and deployment remain separate gates.

The 1.2.0 repository candidate implements order creation as two short local
transactions separated by provider I/O. The first transaction stores a
canonical `pokrov-payment-order-intent-v1` record before any network request.
Its digest binds provider/order, owner, amount, currency, plan, source and the
entitlement snapshot. Reuse of that provider/order key is accepted only when
the complete intent still matches; any drift fails closed. The second
transaction may record only bounded allowlisted provider identifiers/status and
the fact that a validated checkout URL was returned. It does not persist the
checkout URL, query parameters, provider request body or raw provider response.
Provider failure leaves the durable order in non-fulfilling `created` state with
a closed error code, so the exact intent remains available for idempotent retry
or reconciliation. This is local candidate proof, not deployed-provider proof.

An optional signed commercial offer upgrades only that order to
`pokrov-payment-order-intent-v2`. Before provider I/O, one transaction derives
the subject from server-issued Telegram/acquisition authority, locks the
campaign/offer/creative/assignment/reservation and revalidates current price,
revisions, deadlines, legal/channel/capacity policy and finite paid caps. The
client never supplies authoritative price, discount, IDs or remaining quota.
The immutable nested v2 lineage retains stable campaign/offer/creative/variant/
assignment/reservation plus server-issued impression/click IDs, opaque subject
HMAC, exact price/revisions/deadlines and token SHA-256, not the token or raw
identity. Exact retry reuses the same order; drift fails closed.

Authenticated payment fulfillment consumes that bound reservation once in the
same transaction as durable account/access-key fulfillment. A callback cannot
introduce or repair attribution. Refund/chargeback retains original lineage and
does not decrement its gross paid counters; later revenue projection must show
refund/net separately. The payment transaction also inserts one identity-free
commercial `paid` projection keyed by provider/order/stage. Refund/chargeback
adds a separate `reversed` projection; verified connection and D7/D30 retention
can only follow durable observer connection evidence, while renewal requires a
later provider-payment grant. Client/funnel telemetry cannot create any of
these authoritative stages. A failed provider checkout may release its reservation
after the absolute hold without rewriting order truth, while a ready checkout
keeps the binding for a delayed callback.

Provider I/O is owned by one FastAPI-lifespan registry. Lava.top, Cardlink,
Pally, Platima and the closed historical FreeKassa operation set use reusable
provider-policy sessions with bounded total/connect/socket-read time, pool size
and JSON-object response bytes. The adapter cannot create a session on demand.
Safe aggregate telemetry contains only provider, closed operation, HTTP status,
integer latency and result code; URL/query, auth headers, request fields,
provider body and exception text are forbidden. This local boundary does not
prove provider availability, deployed pool behavior or production latency.

When an account-owned provider payment first applies or repairs a durable
`paid_access` grant, the same database transaction inserts one
`payment_entitlement.applied` outbox row keyed by provider/order/schema. The
event payload is deliberately minimal: schema, event type, grant ID, provider
and order ID. It contains no account identifier, Telegram ID, checkout URL,
provider body or credential. The supervised worker atomically publishes it to
one idempotent `payment_entitlement_sync` provisioning job. Callback replay,
outbox replay and provisioning replay converge on the same grant and job;
outbox or provisioning failure cannot repeat entitlement projection. A reversed
grant fails closed before panel synchronization. Local worker proof does not
replace live callback, worker, panel-readback or reconciliation evidence.

## Open Beta v4 Position

Lava.top is the active enabled RUB provider for the beta checkout path. Redacted live evidence from `2026-05-15` confirms invoice creation, authenticated success callback handling, invalid-auth rejection, order-level idempotency after fulfillment, account extension for the authenticated cabinet path, and paid access-key email delivery probe readiness. Retained evidence: [Paid Checkout Launch Evidence - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/paid-checkout-launch-evidence-brain-2026-05-15.json) and [Live Payment And Email Confirmation - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/live-payment-email-confirmation-2026-05-15.md).

Public checkout must keep paid purchase CTAs disabled or degraded for any provider, plan, or route where Lava.top credentials, per-plan offers, webhook auth, replay/idempotency evidence, or email delivery readiness are incomplete. The active public provider configuration remains Lava.top-only. Stronger production checkout claims remain blocked until refund/chargeback reconciliation evidence is attached.

FreeKassa remains disabled compatibility code. Its generic-HMAC path is explicitly
opt-in and defaults off; SCI callbacks require a complete canonical field set and
an exact configured merchant. Even an authenticated callback cannot create local
order authority: fulfillment requires a pre-existing order whose persisted owner,
plan, source, amount, currency, and immutable entitlement snapshot match. Unknown
orders and mismatches remain redacted manual-review evidence with no access effect.
Provider API response parsing accepts only a provider-supplied checkout URL on
the exact configured HTTPS payment host. Missing, malformed, non-HTTPS,
credential-bearing, or cross-host values fail as a provider error. The parser
never manufactures a zero-amount fallback; the separate signed SCI builder is
the only local FreeKassa checkout URL path and requires the authoritative
positive local amount.

Current fulfillment contract:

- authenticated cabinet and bot payments extend the linked account after a valid paid callback; bot payments are ticket-bound to Telegram and do not require buyer email;
- paid extension starts from the later of callback time or the end of legitimate typed premium contributions and classified legacy `PAID`/`TRIAL`/`BONUS` remainder; legacy/free-cycle `FREE` expiry is a separate fallback and is ignored by the premium cursor;
- fulfilled historical provider facts carry projection-applied provenance, so callback replay cannot append their duration; pending facts still apply exactly once, and merge/backfill leaves only the globally earliest provider payment marked first;
- Telegram Stars `PayAttempt.status=paid` confirms payment but is not fulfillment authority: the bot must durably apply the matching account grant before retryable panel provisioning, and may treat a replay as complete only when both its processed marker and applied provider-payment grant exist;
- ambiguous historical paid Stars attempts without per-order fulfillment evidence remain manual-review markers and do not suppress callback repair or claim aggregate paid expiry as proof for that attempt;
- after Telegram platform panel creation or replay, subscription/profile credential fields must come from a validated owned panel read-back; local `User`, `AccessKey`, applicable `UserNode`, and provisioning evidence commit before completion. A validated owned legacy `node_code` may identify a lane without a database node ID and must not produce `UserNode(node_id=0)`; missing all node identity or conflicting node provenance remains retryable rather than exposing a different generated token;
- only the referred account's first successful payment may start its account-owned referrer reward hold; release is replay-safe after a full `72 hours`, while admin gifts and renewals are non-authoritative;
- after a paid bot callback, the user receives a Telegram handoff that prefers the POKROV app/cabinet and also includes the single `connect.pokrov.space` subscription link for beta-stage manual import;
- the authenticated cabinet may show the same `connect.pokrov.space` subscription link and QR after access is active, so beta users can connect manually while native apps are still gated;
- anonymous public checkout requires buyer email and issues one access key through email delivery after a valid paid callback;
- app redemption uses the unified `POST /api/redeem` facade for paid access keys, legacy gift-card codes, and promo codes; paid checkout keys still remain a payment fulfillment artifact, while gift/promo codes remain non-payment bonus or campaign artifacts;
- every active, non-hidden RUB plan with positive `amount_rub` may be exposed in hosted checkout after the provider gate; Lava.top receives the backend-calculated final dynamic amount and the selected `sbp` or `card` payment method;
- `start_99` is a one-time account plan: backend order creation must reject it before provider invoice creation when durable account payment history or an actual successful provider order already exists; admin-issued plan/gift/promo keys and compatibility flags alone do not consume it;
- `start_99` must keep its configured amount and must not stack referral, promo, or pending-discount reductions; those discount mechanics are reserved for standard paid plans when backend eligibility allows them;
- amount, currency, plan, provider auth, local order binding, replay idempotency, and failed/cancelled events are mandatory gate checks before access changes;
- provider callbacks never supply or repair authoritative order fields, and new
  orders capture duration/pricing/source as an immutable entitlement snapshot so
  later catalog edits cannot change what a paid order grants;
- commercial callbacks consume only the reservation already named by immutable
  order lineage; callback payloads, refunds and chargebacks cannot replace or
  erase campaign/creative/variant/assignment attribution;
- access keys must not be returned in public payment API responses or URLs after payment.

Operator Center reads the same authority through
`GET /api/admin/v2/money/access`: payment claims, entitlement grants and the
provisioning outbox determine paid access; client telemetry is explicitly
non-authoritative. Stored gift/access codes are redacted in every list/read
model. When an authorized L3 operator issues a new code, the full value exists
only in the successful Action Intent execute response and in the in-memory
dialog until it is closed; it must not be copied into tickets, notes, URLs or
later audit/read projections.

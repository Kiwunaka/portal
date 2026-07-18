# Payment And Access-Key Contract

Last updated: 2026-07-18

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

## Open Beta v4 Position

Lava.top is the active enabled RUB provider for the beta checkout path. Redacted live evidence from `2026-05-15` confirms invoice creation, authenticated success callback handling, invalid-auth rejection, order-level idempotency after fulfillment, account extension for the authenticated cabinet path, and paid access-key email delivery probe readiness. Retained evidence: [Paid Checkout Launch Evidence - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/paid-checkout-launch-evidence-brain-2026-05-15.json) and [Live Payment And Email Confirmation - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/live-payment-email-confirmation-2026-05-15.md).

Public checkout must keep paid purchase CTAs disabled or degraded for any provider, plan, or route where Lava.top credentials, per-plan offers, webhook auth, replay/idempotency evidence, or email delivery readiness are incomplete. The active public provider configuration remains Lava.top-only. Stronger production checkout claims remain blocked until refund/chargeback reconciliation evidence is attached.

FreeKassa remains disabled compatibility code. Its generic-HMAC path is explicitly
opt-in and defaults off; SCI callbacks require a complete canonical field set and
an exact configured merchant. Even an authenticated callback cannot create local
order authority: fulfillment requires a pre-existing order whose persisted owner,
plan, source, amount, currency, and immutable entitlement snapshot match. Unknown
orders and mismatches remain redacted manual-review evidence with no access effect.

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
- access keys must not be returned in public payment API responses or URLs after payment.

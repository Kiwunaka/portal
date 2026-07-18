# Payment State Machine

Last updated: 2026-07-18

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

For the one-time `start_99` plan, order creation must stop before provider invoice creation when the linked user has `first_purchase_done=true` or an existing paid Lava.top order. This guard prevents duplicate one-time offers even if older fulfillment evidence missed the user flag.

Incoming Lava.top result webhooks must pass `X-Api-Key` or Basic webhook authentication before fulfillment. `payment.success` and `subscription.recurring.payment.success` normalize through the provider `status` value, where `completed` grants access. `payment.failed`, recurring payment failures, and `subscription.cancelled` normalize to non-fulfilling states.

Before any Lava.top paid callback fulfills, the backend validates local order binding, amount, currency, and plan. Any missing local order, amount mismatch, currency mismatch, or plan mismatch becomes `manual_review` and does not grant access.

For authenticated cabinet and Telegram-bound orders, fulfillment extends the linked account. The cabinet can show the single `connect.pokrov.space` subscription link and QR after access is active; the bot also sends that link after a paid Telegram-bound callback as a beta-stage manual import fallback. Anonymous public orders do not receive links in API responses; they receive one emailed access key after fulfillment.

## FreeKassa Compatibility Boundary

FreeKassa is retained as disabled compatibility code, not as an enabled public
provider. The active public provider configuration remains Lava.top-only until a
separate exact-candidate merchant, callback, fulfillment, reconciliation, and
rollback evidence packet is retained.

FreeKassa SCI handling is fail-closed:

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
to one `+15 day` referrer grant. Admin plan keys, gifts, promos, later renewals,
and client activity events are not first-payment authority.

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

Fulfillment is split by local order identity:

- `tg_id` present: extend the existing account and sync the control-plane access.
- `tg_id` absent with `buyer_email`: issue one access key, persist fulfillment metadata on `ExternalOrder.meta_json`, and deliver the key by email.
- duplicate callback event: return idempotent success without issuing another key or applying another extension.

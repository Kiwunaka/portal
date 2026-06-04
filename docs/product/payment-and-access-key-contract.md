# Payment And Access-Key Contract

Last updated: 2026-06-04

## Current Rule

Paid checkout can be presented as live for the evidence-backed Lava.top public beta path. It must not be presented as a fully mature production payment system until refund/chargeback reconciliation has a separate current runbook and evidence.

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

Current fulfillment contract:

- authenticated cabinet and bot payments extend the linked account after a valid paid callback; bot payments are ticket-bound to Telegram and do not require buyer email;
- after a paid bot callback, the user receives a Telegram handoff that prefers the POKROV app/cabinet and also includes the single `connect.pokrov.space` subscription link for beta-stage manual import;
- the authenticated cabinet may show the same `connect.pokrov.space` subscription link and QR after access is active, so beta users can connect manually while native apps are still gated;
- anonymous public checkout requires buyer email and issues one access key through email delivery after a valid paid callback;
- app redemption uses the unified `POST /api/redeem` facade for paid access keys, legacy gift-card codes, and promo codes; paid checkout keys still remain a payment fulfillment artifact, while gift/promo codes remain non-payment bonus or campaign artifacts;
- `start_99` is a one-time user plan: backend order creation must reject it before provider invoice creation when `User.first_purchase_done=true` or when the user already has any successful paid Lava.top order;
- amount, currency, plan, provider auth, local order binding, replay idempotency, and failed/cancelled events are mandatory gate checks before access changes;
- access keys must not be returned in public payment API responses or URLs after payment.

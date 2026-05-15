# Payment And Access-Key Contract

Last updated: 2026-05-15

## Current Rule

Paid checkout can be presented as live only for the evidence-backed Lava.top beta path. It must not be presented as production-ready until provider evidence also proves failed-payment behavior, reconciliation, and paid access-key email delivery.

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

Lava.top is the active enabled RUB provider for the beta checkout path. Redacted live evidence from `2026-05-15` confirms invoice creation, authenticated success callback handling, invalid-auth rejection, order-level idempotency after fulfillment, and account extension for the authenticated cabinet path. Retained evidence: [Live Payment And Email Confirmation - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/live-payment-email-confirmation-2026-05-15.md).

Public checkout must keep paid purchase CTAs disabled or degraded for any provider, plan, or route where Lava.top credentials, per-plan offers, webhook auth, replay/idempotency evidence, or email delivery readiness are incomplete. The active public provider configuration remains Lava.top-only. Broad production checkout is still blocked until failed-payment, refund/chargeback reconciliation, and anonymous paid access-key email-delivery evidence are attached.

Current fulfillment contract:

- authenticated cabinet and bot payments extend the linked account after a valid paid callback; bot payments are ticket-bound to Telegram and do not require buyer email;
- after a paid bot callback, the user receives a Telegram handoff that prefers the POKROV app/cabinet and also includes the single `connect.pokrov.space` subscription link for beta-stage manual import;
- the authenticated cabinet may show the same `connect.pokrov.space` subscription link and QR after access is active, so beta users can connect manually while native apps are still gated;
- anonymous public checkout requires buyer email and issues one access key through email delivery after a valid paid callback;
- amount, currency, plan, provider auth, local order binding, replay idempotency, and failed/cancelled events are mandatory gate checks before access changes;
- access keys must not be returned in public payment API responses or URLs after payment.

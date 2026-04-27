# Payment And Access-Key Contract

Last updated: 2026-04-26

## Current Rule

Paid checkout must not be presented as production-ready until provider evidence proves order creation, callback authentication, replay safety, failed-payment behavior, and reconciliation.

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

Lava.top is the active provider candidate. The code path now supports Lava.top invoice creation and authenticated webhooks, but the provider remains blocked for public use until redacted live or sandbox proof is attached under the release work-order evidence folder.

Public checkout must keep paid purchase CTAs disabled or degraded when Lava.top credentials, per-plan offers, webhook auth, replay evidence, or reconciliation evidence are incomplete.

Current fulfillment contract:

- authenticated cabinet and bot payments extend the linked account after a valid paid callback;
- anonymous public checkout requires buyer email and issues one access key through email delivery after a valid paid callback;
- amount, currency, plan, provider auth, local order binding, replay idempotency, and failed/cancelled events are mandatory gate checks before access changes;
- access keys must not be returned in public payment API responses or URLs after payment.

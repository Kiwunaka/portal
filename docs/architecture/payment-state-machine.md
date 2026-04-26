# Payment State Machine

Last updated: 2026-04-26

| State | Meaning | Access effect |
| --- | --- | --- |
| `draft` | Local order created before provider redirect. | none |
| `provider_pending` | Provider invoice created and waiting. | none |
| `paid_unverified` | Provider success observed before normalization/reconciliation. | none |
| `paid` | Authenticated provider success applied idempotently. | fulfill |
| `failed` | Provider or local failure. | none |
| `cancelled` | User or provider cancellation. | none |
| `refunded` | Refund found by operator/provider reconciliation. | no new access |
| `chargeback` | Dispute found by reconciliation. | no new access; review |
| `manual_review` | Ambiguous auth, amount, currency, account, or payload. | none |

Open Beta v4 must not enable public paid checkout until tests and provider evidence prove these transitions for the active provider path.

## Lava.top Normalization

For `lavatop`, local order creation stores an `ExternalOrder` before redirect. The provider invoice request is sent to `/api/v3/invoice` with `clientUtm.utm_content=<local order_id>` and optional per-plan `offerId` mapping.

Incoming Lava.top result webhooks must pass `X-Api-Key` or Basic webhook authentication before fulfillment. `payment.success` and `subscription.recurring.payment.success` normalize through the provider `status` value, where `completed` grants access. `payment.failed`, recurring payment failures, and `subscription.cancelled` normalize to non-fulfilling states.

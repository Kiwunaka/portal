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

Before any Lava.top paid callback fulfills, the backend validates local order binding, amount, currency, and plan. Any missing local order, amount mismatch, currency mismatch, or plan mismatch becomes `manual_review` and does not grant access.

Fulfillment is split by local order identity:

- `tg_id` present: extend the existing account and sync the control-plane access.
- `tg_id` absent with `buyer_email`: issue one access key, persist fulfillment metadata on `ExternalOrder.meta_json`, and deliver the key by email.
- duplicate callback event: return idempotent success without issuing another key or applying another extension.

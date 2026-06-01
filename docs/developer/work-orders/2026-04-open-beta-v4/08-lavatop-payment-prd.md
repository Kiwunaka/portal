# Lava.top Payment PRD

Status: active  
Date: 2026-05-26

## Goal

Keep the active Lava.top payment-provider path safe for outside-store beta, and keep production claims blocked until refund/chargeback/reconciliation evidence is stronger.

## Required Contract

- Provider catalog must expose provider availability and unavailable reason.
- Order creation must store local order state before redirect.
- Webhook handling must authenticate provider payloads.
- Duplicate replay must be idempotent.
- Invalid auth must not mutate paid state.
- Only normalized `paid` events may fulfill access.
- Failed, cancelled, refund, chargeback, pending verification, and manual review states must be admin-visible and non-fulfilling.

## Launch Rule

Paid checkout is allowed for the current outside-store public beta when the `2026-05-15` Lava.top evidence pack applies. Stronger production checkout claims remain blocked until refund/chargeback, reconciliation, provider-change, and fresh release-candidate evidence are documented with secrets redacted.

Manual/external payment checks that require the owner payment dashboard, live buyer account, deploy approval, or provider-side evidence should be labeled `MANUAL_OWNER_TEST`, `SKIPPED_BY_OWNER`, `NOT_REQUESTED`, or `BLOCKED_BY_ACCESS` for agent work instead of blocking local docs/code synchronization.

## Provider Facts From Research

- Provider code: `lavatop`.
- Invoice API candidate: `POST https://gate.lava.top/api/v3/invoice`.
- API request authentication uses `X-Api-Key`.
- Webhook authentication can use Basic auth or `X-Api-Key`.
- Expected payment events include `payment.success` and `payment.failed`.
- Refund webhooks were not confirmed; refund/chargeback handling must be manual-review or reconciliation-first until proven.
- Suggested local order correlation: pass the local order id in provider metadata such as `clientUtm.utm_content`.
- Suggested provider transaction id: use provider `contractId` or equivalent external id from the callback payload.

## State Machine

| Local state | Meaning | Fulfills access |
| --- | --- | --- |
| `draft` | Local order created before provider redirect. | no |
| `provider_pending` | Provider invoice created, waiting for payment. | no |
| `paid_unverified` | Provider reports success but normalization/reconciliation has not completed. | no |
| `paid` | Authenticated provider success event normalized and idempotently applied. | yes |
| `failed` | Provider failure or local timeout. | no |
| `cancelled` | User/provider cancellation. | no |
| `refunded` | Operator or provider reconciliation marks refund. | no new access; existing access requires policy decision |
| `chargeback` | Dispute/chargeback found in reconciliation. | no new access; trigger operator review |
| `manual_review` | Payload, auth, amount, currency, or account mapping is ambiguous. | no |

## Evidence Required Before Enabling Checkout Or Stronger Claims

| Evidence | Required detail |
| --- | --- |
| Provider credentials | Redacted proof of credential source and rotation owner. |
| Order creation | Redacted request/response with local order id, amount, currency, plan id, and provider id. |
| Success callback | Authenticated payload with normalized local order transition. |
| Failed callback | Authenticated non-fulfilling failure transition. |
| Invalid auth | Callback rejected and paid state unchanged. |
| Replay | Duplicate event does not duplicate fulfillment. |
| Reconciliation | Operator path for missing refund/chargeback webhooks. |
| Public copy | Checkout unavailable state if any required proof is absent. |

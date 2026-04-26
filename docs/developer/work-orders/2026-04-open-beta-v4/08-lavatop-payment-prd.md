# Lava.top Payment PRD

Status: active  
Date: 2026-04-26

## Goal

Introduce an active payment-provider path that can sell activation keys safely, or keep checkout disabled with truthful public copy when proof is missing.

## Required Contract

- Provider catalog must expose provider availability and unavailable reason.
- Order creation must store local order state before redirect.
- Webhook handling must authenticate provider payloads.
- Duplicate replay must be idempotent.
- Invalid auth must not mutate paid state.
- Only normalized `paid` events may fulfill access.
- Failed, cancelled, refund, chargeback, pending verification, and manual review states must be admin-visible and non-fulfilling.

## Launch Rule

Paid checkout remains blocked until provider credentials, live/sandbox order proof, webhook auth, replay rejection, and reconciliation behavior are documented with redacted evidence.

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

## Evidence Required Before Enabling Checkout

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

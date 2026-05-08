# Lava.top Payment Activation Evidence

- Generated at: `2026-05-05`
- Scope: `current-origin` plus `brain-origin`
- Secrets, payment URLs, invoice IDs, access keys, and webhook keys are redacted.

> Current 2026-05-07 release handoff still remains `NO-GO`.
> This file proves partial Lava.top activation evidence only; it does not clear the required real paid callback, replay/idempotency from provider history, failed-payment/manual-review, reconciliation, or current email delivery access gates.

## Lava API

- `current-origin`: live invoice probe returned `201`.
- Amount: `99 RUB`.
- Payment URL host: `app.lava.top`.
- Offer mapping used: `start_99`.

## Brain Runtime

- `brain-origin`: `portal-email-relay`, `portal-api`, `portal-bot`, `portal-helpbot`, `portal-feedbackbot`, and `portal-worker` are `active`.
- `brain-origin`: `/api/payments/providers` returns `ok=true` with provider `lavatop`.
- `brain-origin`: email relay health returns `ok=true`, `smtp_configured=true`, and `auth_required=true`.
- `brain-origin`: safe public order creation returned `ok=true`, amount `99 RUB`, provider `lavatop`, and a redacted Lava payment URL.
- `brain-origin`: invalid Lava webhook auth was rejected with HTTP `403`.
- `brain-origin`: payment-access-key email delivery probe returned `status=sent` through the Resend HTTPS path.

## Remaining Manual Proof

- A real paid Lava callback is still required to prove that Lava sends `payment.success` to `https://api.pokrov.space/api/payments/result/lavatop`.
- Replay/idempotency for a real paid callback should be verified from Lava webhook history after the first real payment.

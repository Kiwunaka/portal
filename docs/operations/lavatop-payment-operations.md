# Lava.top Payment Operations

Last updated: 2026-05-08

## Provider State

Lava.top is the active payment-provider candidate for Open Beta v4. Backend support exists for order creation through the official `POST /api/v3/invoice` API and authenticated result webhooks, but Lava.top is not approved for public checkout until redacted order, webhook, replay, failure, and reconciliation evidence exists.

## Runtime Configuration

Minimum production configuration:

- `RUB_PAYMENT_PROVIDER_ORDER=lavatop`
- `RUB_PAYMENT_PROVIDER_ENABLED=lavatop` only after evidence is attached
- `BOT_STARS_PAYMENTS_ENABLED=false` for public beta; Telegram Stars invoice flows are legacy-only and must not be exposed as a public paid checkout lane
- `LAVATOP_API_KEY`
- `LAVATOP_OFFER_ID` or per-plan `LAVATOP_OFFER_ID_<PLAN_CODE>`, for example `LAVATOP_OFFER_ID_START_99`
- `LAVATOP_WEBHOOK_API_KEY` or the pair `LAVATOP_WEBHOOK_BASIC_USERNAME` and `LAVATOP_WEBHOOK_BASIC_PASSWORD`
- `EMAIL_DELIVERY_WEBHOOK_URL` and `EMAIL_DELIVERY_WEBHOOK_SECRET`; public checkout stays blocked without live email delivery because paid public orders issue access keys by email

Optional provider controls:

- `LAVATOP_API_BASE_URL`, default `https://gate.lava.top`
- `LAVATOP_PAYMENT_PROVIDER`, for example `PAY2ME`
- `LAVATOP_PAYMENT_METHOD`, for example `SBP` or `CARD`
- `LAVATOP_BUYER_LANGUAGE`, default `RU`
- `LAVATOP_DYNAMIC_AMOUNT_ENABLED=true` only when the configured offer allows dynamic prices
- `LAVATOP_BUYER_EMAIL_DOMAIN` or `LAVATOP_DEFAULT_BUYER_EMAIL` when account email is not a valid email address
- `LAVATOP_WEBHOOK_IP_ALLOWLIST=158.160.60.174` to enforce Lava.top's documented outbound webhook IP
- `LAVATOP_REQUEST_TIMEOUT_SECONDS`, default `30`
- `PAID_CHECKOUT_LAUNCH_EVIDENCE_REQUIRED=true` for public beta
- `PAID_CHECKOUT_LAUNCH_EVIDENCE_PATH=docs/audit-artifacts/paid-checkout-launch-evidence-2026-05-07.json` or another redacted aggregate evidence report path

The backend writes the local `order_id` into `clientUtm.utm_content`; webhook processing uses that value to reconnect Lava.top `contractId` events to local `ExternalOrder` rows.

Runtime provider rule:

- `/api/payments/providers` and order-create endpoints read the configured aggregate launch-evidence report.
- If the report is missing, invalid, or has `safe_to_enable_paid_checkout=false`, the public provider catalog is empty, `blocked=true`, and order creation returns `503`.
- Green provider env alone is not enough to expose checkout.

## Fulfillment Model

- authenticated cabinet and bot orders keep `tg_id` on `ExternalOrder`; a valid paid Lava.top webhook extends that account directly.
- bot-side Lava.top orders are created with a signed checkout ticket and do not ask for buyer email; after the paid webhook, the bot sends the user an app/cabinet handoff plus the single `connect.pokrov.space` subscription link for beta-stage manual import.
- anonymous public checkout requires `buyer_email`; a valid paid Lava.top webhook creates one `GiftCard` access key and sends it through the email delivery relay.
- paid webhook fulfillment is blocked into `manual_review` when provider auth is valid but the local order is unknown, amount is missing or mismatched, currency is missing or mismatched, or plan code conflicts.
- duplicate webhook events are idempotent by provider, event type, and external contract id; they must not issue a second key or extend twice.

Operator visibility:

- `/api/admin/payments/orders` includes a sanitized `fulfillment` block for paid public access-key email orders: mode/status, buyer email, key presence, short key preview, delivery status/mode/http status, and whether an email retry is allowed.
- Raw access keys, provider callback payloads, provider error details, and secrets must not be exposed in the admin payment ledger response.
- `POST /api/admin/payments/orders/{provider}/{order_id}/resend-access-key-email` retries the paid access-key email only for paid orders and requires an audit note. It reuses the existing access key when present, records delivery result back into order metadata, and writes an admin audit event.
- Manual reconciliation still does not silently grant access. If an operator marks an order `paid`, the handoff must include the separate fulfillment/retry action or external evidence explaining how access was delivered.

## Smoke Commands

- Non-mutating Lava.top/email readiness classification: `python scripts/payment_email_readiness_smoke.py --plan-code start_99`
- Dry-run invoice payload: `python scripts/lavatop_invoice_probe.py --plan-code start_99`
- Live invoice probe after secrets are present: `python scripts/lavatop_invoice_probe.py --plan-code start_99 --email operator@example.com --live`
- Dry-run webhook replay payload: `python scripts/lavatop_webhook_replay_smoke.py --order-id <local_order_id>`
- Live webhook replay against a running API: `python scripts/lavatop_webhook_replay_smoke.py --order-id <local_order_id> --live`
- Aggregated paid-checkout launch evidence: `python scripts/paid_checkout_launch_evidence_check.py --readiness-json docs/audit-artifacts/payment-email-readiness-2026-05-07.json`
- Bundled post-deploy payment/email probe: `python scripts/public_beta_post_deploy_probe.py --live --evidence-json docs/audit-artifacts/paid-checkout-live-evidence-2026-05-07.json`

Live payment and public email probes are post-deploy checks. Until the deployed runtime has been probed with operator inbox/payment data, keep checkout unavailable and classify missing evidence as `BLOCKED_BY_ACCESS` or `EXTERNAL_DEPENDENCY`.

`payment_email_readiness_smoke.py` reads only environment presence and prints a redacted JSON report. It does not create invoices, replay webhooks, send emails, or print secret values. Treat `BLOCKED_BY_ACCESS` as missing operator secrets/config and `EXTERNAL_DEPENDENCY` as provider/category acceptance evidence still outside local control.

`public_beta_post_deploy_probe.py` reads live public API email/provider status, then only with `--live` sends verify/reset/payment-access-key email probes and creates a Lava.top probe invoice. It redacts env presence in its report and still depends on the separate paid evidence JSON for webhook replay, failed-payment, manual-review, reconciliation, and paid fulfillment proof.

`paid_checkout_launch_evidence_check.py` is the final non-mutating local gate before checkout can be considered: it requires the readiness report plus redacted evidence for live invoice creation, authenticated success webhook, replay/idempotency, failed-payment no-fulfillment, mismatch/manual-review, reconciliation, and paid access-key email delivery. Any missing item keeps checkout unavailable.

## Required Evidence

- provider credential source and rotation owner, with secrets redacted;
- invoice request/response;
- authenticated success webhook;
- authenticated failed webhook;
- invalid-auth webhook rejection;
- replay/idempotency result;
- amount/currency/plan mismatch routed to `manual_review`;
- anonymous public payment issues exactly one emailed access key;
- admin payment ledger shows the fulfillment/email-delivery state without leaking the raw key;
- admin resend can deliver an existing paid public access key again with an audit note;
- reconciliation procedure for refunds and chargebacks.

## Operational Rule

When evidence is missing, checkout must show unavailable/degraded state rather than live purchase copy. The active public beta configuration is Lava.top-only; older provider-specific code paths and Telegram Stars invoice handlers are retained for legacy/reconciliation compatibility, not for public provider selection.

Do not enable `lavatop` in the public provider list unless the webhook auth secret is configured. Missing or invalid webhook auth is treated as an invalid payment signature and cannot activate access.

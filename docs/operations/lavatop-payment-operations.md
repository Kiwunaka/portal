# Lava.top Payment Operations

Last updated: 2026-05-15

## Provider State

Lava.top is the active enabled payment provider for the RUB beta checkout path. Backend support exists for order creation through the official `POST /api/v3/invoice` API and authenticated result webhooks. Redacted live evidence from `2026-05-15` confirms invoice creation, authenticated success callback handling, invalid-auth rejection, account extension, order-level idempotency for the authenticated cabinet path, and paid access-key email delivery probe readiness. Refund/chargeback reconciliation remains an operator runbook requirement, not a blocker for the outside-store public beta claim.

Retained evidence:

- [Paid Checkout Launch Evidence - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/paid-checkout-launch-evidence-brain-2026-05-15.json)
- [Brain Post-Deploy Live Probe - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/brain-post-deploy-live-probe-2026-05-15.json)
- [Public Beta Post-Deploy Probe - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/public-beta-post-deploy-probe-2026-05-15.json)
- [Live Payment And Email Confirmation - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/live-payment-email-confirmation-2026-05-15.md)

## Runtime Configuration

Minimum production configuration:

- `RUB_PAYMENT_PROVIDER_ORDER=lavatop`
- `RUB_PAYMENT_PROVIDER_ENABLED=lavatop` only while the Lava.top beta evidence remains current and webhook auth is configured
- `LAVATOP_API_KEY`
- `LAVATOP_OFFER_ID` or per-plan `LAVATOP_OFFER_ID_<PLAN_CODE>`, for example `LAVATOP_OFFER_ID_START_99`
- `LAVATOP_WEBHOOK_API_KEY` or the pair `LAVATOP_WEBHOOK_BASIC_USERNAME` and `LAVATOP_WEBHOOK_BASIC_PASSWORD`
- `EMAIL_DELIVERY_WEBHOOK_URL` and `EMAIL_DELIVERY_WEBHOOK_SECRET`; anonymous paid public checkout stays blocked without live email delivery because paid public orders issue access keys by email

Optional provider controls:

- `LAVATOP_API_BASE_URL`, default `https://gate.lava.top`
- `LAVATOP_PAYMENT_PROVIDER`, for example `PAY2ME`
- `LAVATOP_PAYMENT_METHOD`, for example `SBP` or `CARD`
- `LAVATOP_BUYER_LANGUAGE`, default `RU`
- `LAVATOP_DYNAMIC_AMOUNT_ENABLED=true` only when the configured offer allows dynamic prices
- `LAVATOP_BUYER_EMAIL_DOMAIN` or `LAVATOP_DEFAULT_BUYER_EMAIL` when account email is not a valid email address
- `LAVATOP_WEBHOOK_IP_ALLOWLIST=158.160.60.174` to enforce Lava.top's documented outbound webhook IP. If the control-plane proxy exposes callbacks to the API as loopback, loopback is accepted only when webhook auth is configured and the request passes the normal auth check.
- `LAVATOP_REQUEST_TIMEOUT_SECONDS`, default `30`

The backend writes the local `order_id` into `clientUtm.utm_content`; webhook processing uses that value to reconnect Lava.top `contractId` events to local `ExternalOrder` rows.

## Fulfillment Model

- authenticated cabinet and bot orders keep `tg_id` on `ExternalOrder`; a valid paid Lava.top webhook extends that account directly.
- bot-side Lava.top orders are created with a signed checkout ticket and do not ask for buyer email; after the paid webhook, the bot sends the user an app/cabinet handoff plus the single `connect.pokrov.space` subscription link for beta-stage manual import.
- anonymous public checkout requires `buyer_email`; a valid paid Lava.top webhook creates one `GiftCard` access key and sends it through the email delivery relay.
- paid webhook fulfillment is blocked into `manual_review` when provider auth is valid but the local order is unknown, amount is missing or mismatched, currency is missing or mismatched, or plan code conflicts.
- duplicate webhook events are idempotent by provider, event type, and external contract id; they must not issue a second key or extend twice.
- once an order fulfillment reaches `account_extended`, later callbacks for the same local order must return already-applied semantics and must not extend the account again, even if the provider sends a different external contract id.

## Smoke Commands

- Dry-run invoice payload: `python scripts/lavatop_invoice_probe.py --plan-code start_99`
- Live invoice probe after secrets are present: `python scripts/lavatop_invoice_probe.py --plan-code start_99 --email operator@example.com --live`
- Dry-run webhook replay payload: `python scripts/lavatop_webhook_replay_smoke.py --order-id <local_order_id>`
- Live webhook replay against a running API: `python scripts/lavatop_webhook_replay_smoke.py --order-id <local_order_id> --live`

## Required Evidence

- PASS, beta path: provider credential presence and webhook auth readiness, with secrets redacted;
- PASS, beta path: live invoice creation for `start_99`;
- PASS, beta path: authenticated success callback activates the linked account;
- PASS, beta path: invalid-auth webhook rejection;
- PASS, beta path: replay/order-level idempotency after account extension;
- PASS, beta path: failed or invalid-auth payment events do not fulfill access;
- PASS, beta path: amount/currency/plan mismatch routes to `manual_review` in callback tests;
- PASS, beta path: paid access-key email delivery probe returns success with payload redacted;
- still required before stronger production checkout claim: operational reconciliation procedure for refunds and chargebacks.

## Operational Rule

When evidence is missing for a plan or route, checkout must show unavailable/degraded state rather than live purchase copy. The active public beta configuration is Lava.top-only; older provider-specific code paths are retained for legacy/reconciliation tests, not for public provider selection.

Do not enable `lavatop` in the public provider list unless the webhook auth secret is configured. Missing or invalid webhook auth is treated as an invalid payment signature and cannot activate access.

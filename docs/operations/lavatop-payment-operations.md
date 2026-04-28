# Lava.top Payment Operations

Last updated: 2026-04-27

## Provider State

Lava.top is the active payment-provider candidate for Open Beta v4. Backend support exists for order creation through the official `POST /api/v3/invoice` API and authenticated result webhooks, but Lava.top is not approved for public checkout until redacted order, webhook, replay, failure, and reconciliation evidence exists.

## Runtime Configuration

Minimum production configuration:

- `RUB_PAYMENT_PROVIDER_ORDER=lavatop,cardlink,pally,platima`
- `RUB_PAYMENT_PROVIDER_ENABLED=lavatop,...` only after evidence is attached
- `LAVATOP_API_KEY`
- `LAVATOP_OFFER_ID` or per-plan `LAVATOP_OFFER_ID_<PLAN_CODE>`, for example `LAVATOP_OFFER_ID_START_99`
- `LAVATOP_WEBHOOK_API_KEY` or the pair `LAVATOP_WEBHOOK_BASIC_USERNAME` and `LAVATOP_WEBHOOK_BASIC_PASSWORD`
- `EMAIL_DELIVERY_WEBHOOK_URL` and `EMAIL_DELIVERY_WEBHOOK_SECRET` when anonymous public checkout is enabled, because paid public orders issue access keys by email

Optional provider controls:

- `LAVATOP_API_BASE_URL`, default `https://gate.lava.top`
- `LAVATOP_PAYMENT_PROVIDER`, for example `PAY2ME`
- `LAVATOP_PAYMENT_METHOD`, for example `SBP` or `CARD`
- `LAVATOP_BUYER_LANGUAGE`, default `RU`
- `LAVATOP_DYNAMIC_AMOUNT_ENABLED=true` only when the configured offer allows dynamic prices
- `LAVATOP_BUYER_EMAIL_DOMAIN` or `LAVATOP_DEFAULT_BUYER_EMAIL` when account email is not a valid email address
- `LAVATOP_WEBHOOK_IP_ALLOWLIST=158.160.60.174` to enforce Lava.top's documented outbound webhook IP
- `LAVATOP_REQUEST_TIMEOUT_SECONDS`, default `30`

The backend writes the local `order_id` into `clientUtm.utm_content`; webhook processing uses that value to reconnect Lava.top `contractId` events to local `ExternalOrder` rows.

## Fulfillment Model

- authenticated cabinet and bot orders keep `tg_id` on `ExternalOrder`; a valid paid Lava.top webhook extends that account directly.
- bot-side Lava.top orders are created with a signed checkout ticket and do not ask for buyer email; after the paid webhook, the bot sends the user an app/cabinet handoff plus the single `connect.pokrov.space` subscription link for beta-stage manual import.
- anonymous public checkout requires `buyer_email`; a valid paid Lava.top webhook creates one `GiftCard` access key and sends it through the email delivery relay.
- paid webhook fulfillment is blocked into `manual_review` when provider auth is valid but the local order is unknown, amount is missing or mismatched, currency is missing or mismatched, or plan code conflicts.
- duplicate webhook events are idempotent by provider, event type, and external contract id; they must not issue a second key or extend twice.

## Smoke Commands

- Dry-run invoice payload: `python scripts/lavatop_invoice_probe.py --plan-code start_99`
- Live invoice probe after secrets are present: `python scripts/lavatop_invoice_probe.py --plan-code start_99 --email operator@example.com --live`
- Dry-run webhook replay payload: `python scripts/lavatop_webhook_replay_smoke.py --order-id <local_order_id>`
- Live webhook replay against a running API: `python scripts/lavatop_webhook_replay_smoke.py --order-id <local_order_id> --live`

## Required Evidence

- provider credential source and rotation owner, with secrets redacted;
- invoice request/response;
- authenticated success webhook;
- authenticated failed webhook;
- invalid-auth webhook rejection;
- replay/idempotency result;
- amount/currency/plan mismatch routed to `manual_review`;
- anonymous public payment issues exactly one emailed access key;
- reconciliation procedure for refunds and chargebacks.

## Operational Rule

When evidence is missing, checkout must show unavailable/degraded state rather than live purchase copy.

Do not enable `lavatop` in the public provider list unless the webhook auth secret is configured. Missing or invalid webhook auth is treated as an invalid payment signature and cannot activate access.

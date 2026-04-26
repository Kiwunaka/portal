# Lava.top Payment Operations

Last updated: 2026-04-26

## Provider State

Lava.top is the active payment-provider candidate for Open Beta v4. Backend support exists for order creation through the official `POST /api/v3/invoice` API and authenticated result webhooks, but Lava.top is not approved for public checkout until redacted order, webhook, replay, failure, and reconciliation evidence exists.

## Runtime Configuration

Minimum production configuration:

- `RUB_PAYMENT_PROVIDER_ORDER=lavatop,cardlink,pally,platima`
- `RUB_PAYMENT_PROVIDER_ENABLED=lavatop,...` only after evidence is attached
- `LAVATOP_API_KEY`
- `LAVATOP_OFFER_ID` or per-plan `LAVATOP_OFFER_ID_<PLAN_CODE>`, for example `LAVATOP_OFFER_ID_START_99`
- `LAVATOP_WEBHOOK_API_KEY` or the pair `LAVATOP_WEBHOOK_BASIC_USERNAME` and `LAVATOP_WEBHOOK_BASIC_PASSWORD`

Optional provider controls:

- `LAVATOP_API_BASE_URL`, default `https://gate.lava.top`
- `LAVATOP_PAYMENT_PROVIDER`, for example `PAY2ME`
- `LAVATOP_PAYMENT_METHOD`, for example `SBP` or `CARD`
- `LAVATOP_BUYER_LANGUAGE`, default `RU`
- `LAVATOP_DYNAMIC_AMOUNT_ENABLED=true` only when the configured offer allows dynamic prices
- `LAVATOP_BUYER_EMAIL_DOMAIN` or `LAVATOP_DEFAULT_BUYER_EMAIL` when account email is not a valid email address

The backend writes the local `order_id` into `clientUtm.utm_content`; webhook processing uses that value to reconnect Lava.top `contractId` events to local `ExternalOrder` rows.

## Required Evidence

- provider credential source and rotation owner, with secrets redacted;
- invoice request/response;
- authenticated success webhook;
- authenticated failed webhook;
- invalid-auth webhook rejection;
- replay/idempotency result;
- reconciliation procedure for refunds and chargebacks.

## Operational Rule

When evidence is missing, checkout must show unavailable/degraded state rather than live purchase copy.

Do not enable `lavatop` in the public provider list unless the webhook auth secret is configured. Missing or invalid webhook auth is treated as an invalid payment signature and cannot activate access.

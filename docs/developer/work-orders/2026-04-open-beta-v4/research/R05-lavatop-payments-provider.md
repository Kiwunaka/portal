# R05 - Lava.top Payments Provider Research

Date: 2026-04-26
Wave: POKROV Open Beta v4
Role: R05 research
Write scope: this file only

## Executive Summary

Lava.top is technically viable as a hosted invoice provider for one-time digital-product checkout, but it should not be promoted to production until a real cabinet/API-key proof confirms contract mapping, webhook auth, and post-refund reconciliation.

Verified official path:

- Developer portal: `https://developers.lava.top/en`
- Swagger UI: `https://gate.lava.top/docs`
- OpenAPI YAML: `https://gate.lava.top/docs/documentation.yaml`
- Current OpenAPI version observed: `1.17.0`
- Create invoice method: `POST https://gate.lava.top/api/v3/invoice`
- Auth for API calls: `X-Api-Key`
- Webhook auth options: HTTP Basic or `X-Api-Key`
- Webhook events for one-time product payments: `payment.success`, `payment.failed`
- Webhook events for subscriptions: `subscription.recurring.payment.success`, `subscription.recurring.payment.failed`, `subscription.cancelled`
- Refund webhooks: official developer docs say refund events are not sent
- Chargeback webhooks: not found in official Lava.top docs/OpenAPI; treat as unknown/blocked

Recommended integration approach:

1. Add a `lavatop` RUB provider adapter to `portal_bot/payment_providers.py`.
2. Use Lava.top `clientUtm.utm_content` for the local POKROV order id because arbitrary metadata/custom data is not verified in the current OpenAPI schema.
3. Use Lava.top `contractId` as the provider transaction id and idempotency key for webhooks.
4. Add strict webhook authentication using either `X-Api-Key` or Basic, plus optional IP allowlist for `158.160.60.174`.
5. Keep refunds and chargebacks out of automatic entitlement revocation until reconciliation is implemented against `GET /api/v2/invoices` and/or provider dashboard evidence.

## Scope Guardrails

- This research used official Lava.top surfaces only: `faq.lava.top`, `developers.lava.top`, `gate.lava.top`, and the Lava.top cabinet entry at `app.lava.top`.
- Unrelated `lava.so`, LavaPay, and non-Lava.top APIs are explicitly excluded.
- No secrets were read or included.
- Existing POKROV implementation was inspected read-only for provider shape, callback handling, tests, and env naming.

## Evidence Table

| Label | Finding | Evidence |
| --- | --- | --- |
| VERIFIED_OFFICIAL | Lava.top points API users to its developer portal and Swagger docs. | `https://faq.lava.top/article/76482` says the current API information is in `developers.lava.top` and links browser testing at `gate.lava.top`. |
| VERIFIED_OFFICIAL | OpenAPI is current enough to target and reports `openapi: 3.0.3`, title `lava.top Public API`, version `1.17.0`. | `https://gate.lava.top/docs/documentation.yaml` fetched 2026-04-26. |
| VERIFIED_OFFICIAL | API requests use `X-Api-Key`. | OpenAPI `securitySchemes.ApiKeyAuth` is `type: apiKey`, `in: header`, `name: X-Api-Key`. Developer docs also describe API key creation in Integrations -> Public API. |
| VERIFIED_OFFICIAL | Create invoice should use `POST /api/v3/invoice`; `/api/v1/invoice` and `/api/v2/invoice` are deprecated. | OpenAPI path `/api/v3/invoice`; `/api/v2/invoice` summary says use `POST /api/v3/invoice`. |
| VERIFIED_OFFICIAL | One-time digital product invoice supports `email`, `offerId`, `currency`, optional `paymentProvider`, optional `paymentMethod`, optional `buyerLanguage`, optional `periodicity`, optional `clientUtm`, and optional dynamic `amount`. | OpenAPI schema `CreateInvoiceV3Request`. |
| VERIFIED_OFFICIAL | Invoice create response contains provider contract `id`, `status`, `amountTotal`, and nullable `paymentUrl`. | OpenAPI schema `InvoicePaymentParamsResponse`. |
| VERIFIED_OFFICIAL | RUB provider options in v3 are `SMART_GLOCAL` and `PAY2ME`; default RUB provider is `SMART_GLOCAL` when omitted. | OpenAPI schema `PaymentProvider`. Older `PaymentMethod` enum also lists `BANK131`, but v3 `PaymentProvider` does not. |
| VERIFIED_OFFICIAL | PAY2ME supports payment method `CARD` or `SBP`; if omitted, card is used. | OpenAPI schema `PaymentMethodType`. |
| VERIFIED_OFFICIAL | Webhook setup supports Basic auth and API-key auth, with `X-Api-Key` for the API-key mode. | Developer docs "How to Set Up a Webhook" and OpenAPI `BasicWebhookAuth` / `ApiKeyWebhookAuth`. |
| VERIFIED_OFFICIAL | Lava.top says all outgoing webhook connections originate from `158.160.60.174`. | Developer docs "Errors" section. |
| VERIFIED_OFFICIAL | Webhook retry policy is up to 20 total attempts, with 1s, 5s, 15s, then one-minute and one-hour retries. | Developer docs "Retry Policy" and OpenAPI `/example-of-webhook-route-contract`. |
| VERIFIED_OFFICIAL | `payment.success` and `payment.failed` are the one-time/first-subscription webhook events. | Developer docs "Event Types" and OpenAPI `WebhookEventType`. |
| VERIFIED_OFFICIAL | Webhook payload for product purchase includes `eventType`, `product.id`, `product.title`, `buyer.email`, `contractId`, `amount`, `currency`, `timestamp`, `status`, and `errorMessage`; schema also includes optional `parentContractId` and `clientUtm`. | OpenAPI `/example-of-webhook-route-contract` examples and schema `PurchaseWebhookLog`. |
| VERIFIED_OFFICIAL | Webhook history can show the full request body and delivery attempts, can be filtered by buyer email, invoice ID, product name, or product ID, and can manually resend webhooks. | Developer docs "Webhook History", "Webhook Resend". |
| VERIFIED_OFFICIAL | During refunds, Lava.top does not send a webhook. | Developer docs "Webhook History" says that during refunds webhook is not sent. |
| VERIFIED_OFFICIAL | Official KB says a digital product can be hidden from public feed and still paid through a direct link. | `https://faq.lava.top/article/53726`, product visibility step. |
| VERIFIED_REPO | Existing POKROV provider abstraction lives in `portal_bot/payment_providers.py` with `PROVIDER_META`, `provider_is_configured`, `enabled_rub_provider_codes`, `create_rub_payment`, `verify_callback_signature`, `callback_ids`, and `callback_status`. | Read-only repo inspection. |
| VERIFIED_REPO | Generic POKROV callbacks already exist at `/api/payments/result/{provider}`, `/api/payments/refund/{provider}`, and `/api/payments/chargeback/{provider}`. | Read-only `portal_bot/api.py` inspection. |
| VERIFIED_REPO | Callback idempotency is stored as unique `(provider, event_type, external_id)` in `ExternalPaymentEvent`. | Read-only `portal_bot/models.py` inspection. |
| VERIFIED_REPO | Existing order ledger is keyed by unique `(provider, order_id)` in `ExternalOrder`. | Read-only `portal_bot/models.py` inspection. |
| BLOCKED_ACCESS | No live Lava.top cabinet/API key was available to verify a real invoice, webhook, refund, or dashboard resend. | Current task did not provide credentials and secrets must not be printed. |
| NOT_VERIFIED | Arbitrary metadata/custom JSON beyond `clientUtm` was not found in official OpenAPI. | OpenAPI schema `CreateInvoiceV3Request` has `clientUtm`, not general `metadata`, `custom`, `orderId`, or `externalId`. |
| NOT_VERIFIED | Whether `clientUtm` is echoed in real webhook bodies is schema-supported but not proven by official examples. | `PurchaseWebhookLog` schema includes `clientUtm`; examples shown in docs omit it. |
| UNKNOWN_BLOCKED | Sandbox/test mode was not found in official docs/OpenAPI. | Search of official developer page and OpenAPI YAML found no sandbox endpoint or environment flag. |
| UNKNOWN_BLOCKED | Chargeback webhook or dispute event behavior was not found. | OpenAPI `WebhookEventType` has no chargeback/dispute/refund event. |

## Answers To Required Questions

### API version and method

- Current official OpenAPI version: `1.17.0`.
- Base URL inferred from Swagger host and examples: `https://gate.lava.top`.
- Create one-time invoice: `POST /api/v3/invoice`.
- Read/reconcile invoices: `GET /api/v2/invoices` and `GET /api/v2/invoices/{id}`.
- API auth header: `X-Api-Key: <lava_top_api_key>`.

Minimum one-time product payload:

```json
{
  "email": "buyer@example.com",
  "offerId": "00000000-0000-0000-0000-000000000000",
  "currency": "RUB",
  "periodicity": "ONE_TIME"
}
```

Recommended POKROV payload:

```json
{
  "email": "buyer@example.com",
  "offerId": "00000000-0000-0000-0000-000000000000",
  "currency": "RUB",
  "paymentProvider": "SMART_GLOCAL",
  "paymentMethod": "CARD",
  "periodicity": "ONE_TIME",
  "buyerLanguage": "RU",
  "clientUtm": {
    "utm_source": "pokrov",
    "utm_medium": "checkout",
    "utm_campaign": "open_beta_v4",
    "utm_term": "plan_1_month",
    "utm_content": "lavatop_site_1234567890_abcd1234"
  }
}
```

### One-time digital product invoice with metadata/custom data

Verified:

- One-time product invoice is supported by `POST /api/v3/invoice`.
- Digital product type exists in product schema as `DIGITAL_PRODUCT`.
- `clientUtm` is officially supported on invoice creation and in webhook schema.

Not verified:

- Arbitrary metadata/custom data field.
- Merchant-supplied order id field.
- API idempotency key header.

Design implication:

- Put the local POKROV order id in `clientUtm.utm_content`.
- Also store Lava.top response `id` as `provider_contract_id` in `ExternalOrder.meta_json`.
- On webhook, map to local order by `clientUtm.utm_content` when present and valid; otherwise use `contractId` as the order id and mark `manual_review` if there is no existing local order.

### Webhook auth: Basic or X-Api-Key

Verified:

- Lava.top supports Basic auth.
- Lava.top supports provider-configured API-key auth sent in `X-Api-Key`.
- API-key auth key length in dashboard is documented as maximum 80 characters.
- HTTPS is required for Basic-auth webhook delivery in official docs.

Recommended:

- Use `X-Api-Key` first for POKROV because it fits FastAPI header verification cleanly and avoids Basic credentials in callback URLs or access logs.
- Keep Basic support as an adapter option if cabinet setup requires it.
- Add optional source IP allowlist for `158.160.60.174`, but do not rely on IP as the only auth factor.

### Payload shape

For one-time product success:

```json
{
  "eventType": "payment.success",
  "product": {
    "id": "d31384b8-e412-4be5-a2ec-297ae6666c8f",
    "title": "Product title"
  },
  "buyer": {
    "email": "buyer@example.com"
  },
  "contractId": "7ea82675-4ded-4133-95a7-a6efbaf165cc",
  "amount": 40254.19,
  "currency": "RUB",
  "timestamp": "2024-02-05T09:38:27.33277Z",
  "status": "completed",
  "errorMessage": ""
}
```

For one-time product failure:

```json
{
  "eventType": "payment.failed",
  "product": {
    "id": "d31384b8-e412-4be5-a2ec-297ae6666c8f",
    "title": "Product title"
  },
  "buyer": {
    "email": "buyer@example.com"
  },
  "contractId": "7ea82675-4ded-4133-95a7-a6efbaf165cc",
  "amount": 40254.19,
  "currency": "RUB",
  "timestamp": "2024-02-05T09:38:27.33277Z",
  "status": "failed",
  "errorMessage": "Payment window is opened but not completed"
}
```

Subscription payloads are documented but not recommended for Open Beta v4 initial integration. If later enabled, `parentContractId` appears on recurring payment events, and `subscription.cancelled` includes `cancelledAt` and `willExpireAt`.

### Refunds and chargebacks

Refunds:

- Official docs say refund webhooks are not sent.
- Therefore automatic entitlement revocation on refund cannot be webhook-driven.

Chargebacks:

- No official chargeback/dispute webhook or API field found.
- Treat as unknown and blocked until Lava.top support/cabinet confirms behavior.

Required fallback:

- Add reconciliation via `GET /api/v2/invoices` filtered by date/status.
- Keep admin manual reconciliation flow as the safety net.
- During beta, do not automatically revoke access on absent refund/chargeback signals; flag orders for review instead.

### Sandbox/test proof

Blocked:

- No official sandbox environment or test API URL was found.
- Swagger "Try it out" exists but requires a real Lava.top API key and appears to target the production `gate.lava.top` API.
- No cabinet/API key was provided for a test transaction.

Minimum proof before implementation is production-eligible:

1. Create hidden digital product in Lava.top.
2. List products/offers through `GET /api/v2/products`.
3. Create one low-value invoice with `clientUtm.utm_content=<local_order_id>`.
4. Confirm `paymentUrl` opens.
5. Complete payment or use provider-supported test card if Lava.top support confirms one.
6. Confirm `payment.success` webhook body includes either `clientUtm.utm_content` or enough data to map the order.
7. Trigger or simulate failed payment and confirm `payment.failed`.
8. Issue refund in dashboard and confirm no webhook, then reconcile through `GET /api/v2/invoices` or dashboard evidence.

## P0 Issues

1. No live cabinet/API proof.
   - Impact: cannot verify real invoice creation, payment URL shape, webhook delivery, refund visibility, or whether `clientUtm` is echoed.
   - Required before production: operator-provided Lava.top account/API key and low-value hidden product.

2. Arbitrary metadata/idempotency is not verified.
   - Impact: current POKROV checkout expects provider callbacks to map back to `ExternalOrder.order_id`; Lava.top only documents `contractId` plus optional `clientUtm`.
   - Mitigation: use `clientUtm.utm_content` as local order id and `contractId` as webhook external id; mark callbacks without a known order as `manual_review`.

3. Refund/chargeback automation cannot be trusted from webhooks.
   - Impact: paid access could remain active after a refund or dispute if relying only on callbacks.
   - Mitigation: reconciliation job and admin manual review; no automatic revocation until Lava.top support confirms chargeback handling.

## P1 Issues

1. Dashboard product/offer lifecycle needs operator runbook proof.
   - Product creation is documented in KB, but offer-id discovery should be verified through `GET /api/v2/products`.

2. Auth mode must be configured deliberately.
   - Prefer `X-Api-Key`; Basic support should exist only if selected in dashboard.

3. Webhook event type must be stored from payload, not only route.
   - Existing POKROV route uses `event_type="result"`; Lava.top event type is inside `eventType`.
   - Adapter should normalize `payment.success` and `payment.failed` into paid/failed status while keeping original `eventType` in payload.

4. Existing analytics filter currently has provider-specific assumptions.
   - Some admin revenue aggregation filters for `freekassa`; Lava.top paid orders should be included in generic payment ledger/reporting once provider is live.

## P2 Issues

1. Provider labels and public copy need careful wording.
   - `Lava.top` should appear as payment-provider/operator copy, not as a public product variant.

2. SDK usage is optional.
   - Official docs link SDKs, but direct OpenAPI implementation is simpler and avoids a new runtime dependency unless the implementation wave wants SDK parity.

3. Rate limit is 50 requests/sec per IP.
   - POKROV checkout traffic is unlikely to approach this during beta, but retries should stay bounded.

## Proposed Implementation Work

### Backend adapter

1. Add provider metadata:
   - Code: `lavatop`
   - Label: `Lava.top`
   - Accent: `Cards and SBP`
   - Hint: hosted Lava.top invoice

2. Add env-driven configuration:
   - `LAVATOP_API_BASE_URL`
   - `LAVATOP_API_KEY`
   - `LAVATOP_OFFER_ID_DEFAULT`
   - optional per-plan offer IDs
   - `LAVATOP_PAYMENT_PROVIDER`
   - `LAVATOP_PAYMENT_METHOD`
   - webhook auth vars listed below

3. Add `_lavatop_create(...)` in `payment_providers.py`:
   - POST JSON to `{base}/api/v3/invoice`
   - header `X-Api-Key`
   - include `email`, `offerId`, `currency`, `periodicity=ONE_TIME`, `buyerLanguage=RU`, `paymentProvider`, `paymentMethod`, `clientUtm`
   - parse `id`, `paymentUrl`, `status`, `amountTotal`
   - return `payment_url` and `remote`

4. Update existing create flow:
   - Allow `lavatop` in `PAYMENT_PROVIDER_WHITELIST`.
   - Include `lavatop` in provider normalization.
   - Pass generated local order id as `custom["local_order_id"]` or `custom["order_id"]`; adapter maps it to `clientUtm.utm_content`.
   - Store Lava.top response id in `ExternalOrder.meta_json`.

5. Add Lava.top callback helpers:
   - `verify_callback_signature("lavatop", payload)` should call a Lava.top-specific auth verifier that can see request headers, not only payload.
   - `callback_ids("lavatop", payload)`:
     - `order_id = payload.clientUtm.utm_content` if present and starts with `lavatop_`
     - else `order_id = payload.contractId`
     - `external_id = payload.contractId`
   - `callback_status("lavatop", payload)`:
     - `payment.success` or status `completed` -> `paid`
     - `payment.failed` or status `failed` -> `failed`
     - `subscription.cancelled` -> `cancelled`
     - unknown -> `manual_review`

6. Add reconciliation:
   - Admin action: fetch `GET /api/v2/invoices/{contractId}`.
   - Optional scheduled beta job: query recent `GET /api/v2/invoices` and compare `COMPLETED` / `FAILED` against `ExternalOrder`.

### Tests

1. Provider config tests:
   - `lavatop` appears only when required env is present.
   - provider catalog includes label/hint.

2. Create invoice tests:
   - aiohttp fake verifies URL `/api/v3/invoice`.
   - header `X-Api-Key` is sent.
   - JSON includes `clientUtm.utm_content` equal local order id.
   - response `id` and `paymentUrl` are parsed.

3. Webhook tests:
   - `X-Api-Key` valid -> `payment.success` marks order paid.
   - Basic valid -> `payment.success` marks order paid if Basic mode enabled.
   - invalid auth -> 400/401 and no poisoning of later valid callback.
   - duplicate `contractId` -> idempotent duplicate.
   - `payment.failed` records failed without activation.
   - missing `clientUtm` creates or updates manual-review order keyed by `contractId`.

4. Admin tests:
   - Lava.top orders appear in payment ledger.
   - manual reconciliation can move `failed`/`manual_review` states with audit note.

## Provider Adapter Spec

Provider code:

```text
lavatop
```

Create request:

```http
POST https://gate.lava.top/api/v3/invoice
X-Api-Key: <LAVATOP_API_KEY>
Content-Type: application/json
Accept: application/json
```

Create request body:

```json
{
  "email": "buyer@example.com",
  "offerId": "plan-specific-offer-id",
  "currency": "RUB",
  "paymentProvider": "SMART_GLOCAL",
  "paymentMethod": "CARD",
  "periodicity": "ONE_TIME",
  "buyerLanguage": "RU",
  "clientUtm": {
    "utm_source": "pokrov",
    "utm_medium": "checkout",
    "utm_campaign": "open_beta_v4",
    "utm_term": "1_month",
    "utm_content": "lavatop_site_1234567890_abcd1234"
  }
}
```

Create response mapping:

| Lava.top field | POKROV field |
| --- | --- |
| `id` | `remote.contract_id`, `provider_contract_id` in `meta_json` |
| `paymentUrl` | `payment_url` |
| `status` | remote status; do not activate until webhook or reconcile says completed |
| `amountTotal.amount` | amount sanity check |
| `amountTotal.currency` | currency sanity check |

Webhook route:

```text
https://api.pokrov.space/api/payments/result/lavatop
```

Webhook event mapping:

| Lava.top `eventType` | Lava.top status examples | POKROV status | Activation |
| --- | --- | --- | --- |
| `payment.success` | `completed`, `subscription-active` | `paid` | yes for one-time paid order |
| `payment.failed` | `failed`, `subscription-failed` | `failed` | no |
| `subscription.recurring.payment.success` | `subscription-active` | `paid` or `manual_review` initially | no for v4 one-time scope |
| `subscription.recurring.payment.failed` | `subscription-failed` | `failed` | no |
| `subscription.cancelled` | cancellation payload | `cancelled` | no automatic revocation in one-time scope |
| unknown | any | `manual_review` | no |

Webhook idempotency:

```text
provider = lavatop
event_type = result
external_id = payload.contractId
order_id = payload.clientUtm.utm_content if valid else payload.contractId
```

## Env Var List

Provider enablement:

```dotenv
RUB_PAYMENT_PROVIDER_ENABLED=cardlink,pally,platima,lavatop
RUB_PAYMENT_PROVIDER_ORDER=lavatop,cardlink,pally,platima
```

Lava.top API:

```dotenv
LAVATOP_API_BASE_URL=https://gate.lava.top
LAVATOP_API_KEY=
LAVATOP_OFFER_ID_DEFAULT=
LAVATOP_OFFER_ID_START_99=
LAVATOP_OFFER_ID_1_MONTH=
LAVATOP_OFFER_ID_3_MONTHS=
LAVATOP_OFFER_ID_6_MONTHS=
LAVATOP_PAYMENT_PROVIDER=SMART_GLOCAL
LAVATOP_PAYMENT_METHOD=CARD
LAVATOP_BUYER_LANGUAGE=RU
```

Webhook auth:

```dotenv
LAVATOP_WEBHOOK_AUTH_MODE=api_key
LAVATOP_WEBHOOK_API_KEY=
LAVATOP_WEBHOOK_BASIC_USERNAME=
LAVATOP_WEBHOOK_BASIC_PASSWORD=
LAVATOP_WEBHOOK_IP_ALLOWLIST=158.160.60.174
```

Optional operational knobs:

```dotenv
LAVATOP_REQUEST_TIMEOUT_SECONDS=30
LAVATOP_RECONCILE_LOOKBACK_HOURS=72
LAVATOP_RECONCILE_ENABLED=false
```

Do not place secret values in docs, screenshots, commit messages, or work-order evidence.

## Webhook Auth Verification Plan

1. Configure dashboard with `X-Api-Key` first.
2. Generate a random webhook key in POKROV secret manager, length <= 80 chars.
3. Store it as `LAVATOP_WEBHOOK_API_KEY`.
4. In FastAPI callback:
   - read `X-Api-Key`
   - compare with `hmac.compare_digest`
   - require non-empty configured key
   - reject missing/invalid key with 401
5. If Basic mode is selected:
   - read `Authorization: Basic ...`
   - decode username/password
   - compare both with configured env using constant-time compare
   - reject missing/invalid auth with 401
6. Optionally verify source IP is in `LAVATOP_WEBHOOK_IP_ALLOWLIST`.
7. Return 2xx only after payload is persisted idempotently.
8. Return 4xx on auth errors so Lava.top marks failed and retries; use Webhook History to inspect.
9. Never log raw auth header, buyer email, or full provider payload without redaction.

## Idempotency Keys

Create flow:

- Local idempotency key: existing POKROV `ExternalOrder.order_id`, generated before provider call.
- Provider API idempotency header: unknown/not documented.
- Risk: network timeout after provider creates invoice but before POKROV stores response can create orphaned invoice.
- Mitigation: do not auto-retry `POST /api/v3/invoice` after ambiguous timeout. Mark local order `manual_review` / `provider_create_unknown` and reconcile by buyer email, amount, date, and `clientUtm`.

Webhook flow:

- Primary idempotency key: `(provider="lavatop", event_type="result", external_id=contractId)`.
- Local order mapping: `clientUtm.utm_content` if present; fallback `contractId`.
- Duplicate action: return 200 with duplicate marker after confirming existing valid event.

Reconciliation flow:

- Primary key: Lava.top invoice/contract `id`.
- Secondary matching: buyer email, amount, currency, product/offer, time window, `clientUtm`.

## Exact Provider Dashboard Steps

API key and webhook setup verified from official developer docs:

1. Open `https://app.lava.top/` and sign in.
2. Go to `Integrations`.
3. Choose `Public API`.
4. Click `Create API Key`.
5. Copy the generated API key into secret storage as `LAVATOP_API_KEY`.
6. Click `Add Webhook`.
7. URL:
   - `https://api.pokrov.space/api/payments/result/lavatop`
8. Event type:
   - choose `Payment result` for Open Beta v4 one-time payments.
9. Authentication:
   - recommended: `Your service's API key`
   - value: generated POKROV webhook key from secret storage, stored as `LAVATOP_WEBHOOK_API_KEY`
10. If Basic is required instead:
   - choose `Basic`
   - enter username/password from secret storage
   - store them as `LAVATOP_WEBHOOK_BASIC_USERNAME` and `LAVATOP_WEBHOOK_BASIC_PASSWORD`
11. Save webhook.
12. For test verification, open `Integrations -> Public API -> Webhook history`.
13. Use filters by buyer email, Invoice ID, Product name, or Product ID.
14. Open a webhook entry to inspect full request body and delivery attempts.
15. Use the resend arrow to manually resend a failed webhook.

Digital product setup from official KB:

1. Click `Create`.
2. Choose `Digital product`.
3. Fill cover, title, and description.
4. Set price; official KB lists minimums as 50 RUB, 5 EUR, or 5 USD.
5. Add buyer message if needed.
6. Fill the paid part: file or access instructions and contact.
7. Set visibility. For beta checkout, hide it from the feed so it is available by direct/payment flow only.
8. Click `Save`.
9. Use `GET /api/v2/products` with `X-Api-Key` to obtain product offers and store the selected `offerId` in env.

## Exact Verification Commands

Official docs availability:

```powershell
$doc = Invoke-WebRequest -Uri "https://gate.lava.top/docs/documentation.yaml" -UseBasicParsing -TimeoutSec 30
$doc.StatusCode
($doc.Content -split "`n" | Select-String -Pattern "version:|/api/v3/invoice|ApiKeyAuth|WebhookEventType|CreateInvoiceV3Request")
```

Unauthenticated API should reject:

```powershell
Invoke-WebRequest -Uri "https://gate.lava.top/api/v2/invoices?size=1" -UseBasicParsing -TimeoutSec 20
Invoke-WebRequest -Uri "https://gate.lava.top/api/v3/invoice" -Method POST -ContentType "application/json" -Body '{"email":"test@example.com","offerId":"00000000-0000-0000-0000-000000000000","currency":"RUB"}' -UseBasicParsing -TimeoutSec 20
```

List Lava.top products/offers after API key is available:

```powershell
$headers = @{ "X-Api-Key" = $env:LAVATOP_API_KEY; "Accept" = "application/json" }
Invoke-WebRequest -Uri "$env:LAVATOP_API_BASE_URL/api/v2/products" -Headers $headers -UseBasicParsing -TimeoutSec 30
```

Create proof invoice after hidden product exists:

```powershell
$headers = @{
  "X-Api-Key" = $env:LAVATOP_API_KEY
  "Accept" = "application/json"
  "Content-Type" = "application/json"
}
$body = @{
  email = "operator+lava-proof@example.com"
  offerId = $env:LAVATOP_OFFER_ID_DEFAULT
  currency = "RUB"
  paymentProvider = "SMART_GLOCAL"
  paymentMethod = "CARD"
  periodicity = "ONE_TIME"
  buyerLanguage = "RU"
  clientUtm = @{
    utm_source = "pokrov"
    utm_medium = "checkout"
    utm_campaign = "open_beta_v4"
    utm_term = "proof"
    utm_content = "lavatop_proof_$([int][double]::Parse((Get-Date -UFormat %s)))"
  }
} | ConvertTo-Json -Depth 5
Invoke-WebRequest -Uri "$env:LAVATOP_API_BASE_URL/api/v3/invoice" -Method POST -Headers $headers -Body $body -UseBasicParsing -TimeoutSec 30
```

Local webhook auth smoke after implementation:

```powershell
$payload = @{
  eventType = "payment.success"
  product = @{ id = "00000000-0000-0000-0000-000000000000"; title = "POKROV proof" }
  buyer = @{ email = "operator+lava-proof@example.com" }
  contractId = "11111111-1111-1111-1111-111111111111"
  amount = 99
  currency = "RUB"
  timestamp = "2026-04-26T00:00:00Z"
  status = "completed"
  errorMessage = ""
  clientUtm = @{ utm_content = "lavatop_site_1234567890_abcd1234" }
} | ConvertTo-Json -Depth 5
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/payments/result/lavatop" -Method POST -Headers @{ "X-Api-Key" = $env:LAVATOP_WEBHOOK_API_KEY } -ContentType "application/json" -Body $payload
```

Focused repo tests after implementation:

```powershell
python -m pytest tests/test_api_payments_callbacks.py tests/test_admin_payments_api.py -q
python -m pytest tests/test_bot_paywall.py -q
```

Full payment/provider smoke after implementation:

```powershell
python scripts/api_lifecycle_smoke.py
```

## Proof Checklist

- [ ] Official OpenAPI YAML fetched and archived only as source URL, not copied wholesale.
- [ ] Lava.top account access confirmed.
- [ ] API key created in `Integrations -> Public API`.
- [ ] Hidden digital product created.
- [ ] Offer ID obtained via `GET /api/v2/products`.
- [ ] `POST /api/v3/invoice` returns `id` and `paymentUrl`.
- [ ] `paymentUrl` opens a hosted checkout.
- [ ] `clientUtm.utm_content` appears in invoice details or webhook body.
- [ ] `payment.success` webhook arrives at `https://api.pokrov.space/api/payments/result/lavatop`.
- [ ] Invalid webhook auth returns 401 and appears failed in Webhook History.
- [ ] Valid webhook auth returns 2xx and stops retries.
- [ ] Duplicate webhook resend is idempotent.
- [ ] `payment.failed` webhook records failed without activation.
- [ ] Refund test confirms no webhook and reconciliation fallback catches changed state or dashboard evidence.
- [ ] Chargeback behavior is answered by Lava.top support or left blocked in launch checklist.
- [ ] Admin payment ledger redacts provider payload secrets and buyer-sensitive fields.

## Refund Webhook Risk And Reconciliation Fallback

Risk:

- Lava.top official docs state that refund webhooks are not sent.
- No chargeback/dispute event is documented.
- A user could keep paid access after refund/chargeback if POKROV relies only on webhooks.

Beta-safe fallback:

1. Keep refund/chargeback revocation manual during first Lava.top beta.
2. Add admin reconciliation action per order:
   - fetch `GET /api/v2/invoices/{contractId}`
   - compare returned `status`, amount, currency, buyer email, product, and `clientUtm`
   - write `AdminAudit` note before status change
3. Add daily reconciliation only after API proof:
   - query `GET /api/v2/invoices?beginDate=<utc>&endDate=<utc>&size=...`
   - compare against local `ExternalOrder`
   - mark mismatches as `manual_review`, not automatic revoke, unless support confirms refund/chargeback state semantics
4. Operator fallback:
   - use Lava.top `Webhook history` and invoice search by buyer email / Invoice ID / Product ID
   - record provider dashboard verdict in admin reconcile note

## Open Questions For Lava.top Support

1. Is there an official sandbox or test-payment mode for API-created invoices?
2. Is there an official idempotency key header for `POST /api/v3/invoice`?
3. Is arbitrary merchant metadata supported anywhere beyond `clientUtm`?
4. Is `clientUtm` guaranteed to be echoed in every `payment.success` and `payment.failed` webhook?
5. How are refunds represented in `GET /api/v2/invoices` after a completed invoice is refunded?
6. Are chargebacks/disputes exposed through any webhook, invoice status, report, or dashboard export?
7. Can failed one-time product payment webhooks be delayed until final retry/attempt like subscription failures, or are they emitted immediately?

## Recommended Acceptance Gate

Do not enable `lavatop` in `RUB_PAYMENT_PROVIDER_ORDER` for production until:

- all P0 issues are resolved or explicitly waived,
- live proof checklist is complete,
- focused tests pass,
- admin reconciliation path is tested,
- rollback is simply removing `lavatop` from `RUB_PAYMENT_PROVIDER_ENABLED` / `RUB_PAYMENT_PROVIDER_ORDER`.

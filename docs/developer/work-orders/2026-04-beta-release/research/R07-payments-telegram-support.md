# R07 Payments Telegram Support

Status: researched

Last researched: 2026-04-25

## Scope

Payments, activation keys, Telegram bonus, support bots, feedback, provider candidates for paid beta.

Claim labels used below:

- `confirmed`: verified from local source/tests or cited provider documentation.
- `probable`: strongly implied, but not fully proven without live account/provider access.
- `unknown`: no reliable evidence found.
- `needs local run`: covered by code/tests, but not executed in this research pass.
- `blocked by missing access`: requires provider dashboard, merchant approval, production account, or live webhook evidence.

## Provider Candidate Matrix

No requested provider is recommended for paid beta yet. Category acceptance and webhook verification are not confirmed for Lava.top, Tribute, or Kassa.ai.

| Provider | Webhook support | Signature verification | Retry behavior | Refund/cancel events | Payout timing | Allowed product/category confirmation | API docs availability | Manual reconciliation path | Low-volume paid beta risk | Paid beta stance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Lava.top | `confirmed`: webhooks for payment result and recurring payment events are documented. Events include `payment.success`, `payment.failed`, recurring success/failed, and subscription cancelled. Source: [Lava.top developer docs](https://developers.lava.top/en). | `confirmed`: webhook authentication can use Basic auth or an API key sent in `X-Api-Key`. This is not the same HMAC shape as current generic callback handlers. Source: [Lava.top developer docs](https://developers.lava.top/en). | `confirmed`: failed delivery retries up to 20 total attempts with 1s, 5s, 15s, minute, then hourly spacing. Source: [Lava.top webhook retry policy](https://developers.lava.top/en). | `confirmed`: cancellation events exist for subscriptions; `confirmed`: refunds do not send webhooks according to the webhook history section. Source: [Lava.top developer docs](https://developers.lava.top/en). | `unknown`: public docs reviewed did not confirm payout timing for this use case. | `blocked by missing access`: docs support digital products, but POKROV category acceptance must be approved explicitly before beta. Terms prohibit illegal/fraudulent/restricted content but do not confirm this product category. Source: [Lava.top terms](https://lava.top/en/docs/terms/). | `confirmed`: public developer docs and OpenAPI/Swagger entry are linked. Source: [Lava.top developer docs](https://developers.lava.top/en). | `probable`: webhook history exposes full request body, delivery attempts, search by buyer email/invoice/product, and manual resend. Source: [Lava.top developer docs](https://developers.lava.top/en). | Refunds require manual/status polling path because refund webhook is absent; current backend has no Lava-specific adapter; product-category acceptance not confirmed. | `blocked by missing access`: can be considered only after merchant/category approval, adapter implementation, and live signed webhook proof. |
| Tribute | `confirmed`: webhook docs list digital product purchase and refund events, plus subscriptions/donations/physical order events. Source: [Tribute webhooks](https://wiki.tribute.tg/for-content-creators/api-documentation/webhooks). | `confirmed`: each request includes `trbt-signature`, an HMAC-SHA256 signature of the body signed with the API key. Source: [Tribute webhooks](https://wiki.tribute.tg/for-content-creators/api-documentation/webhooks). | `confirmed`: retries after 5m, 15m, 30m, 1h, and 10h. Source: [Tribute webhooks](https://wiki.tribute.tg/for-content-creators/api-documentation/webhooks). | `confirmed`: `digital_product_refunded` exists and should be matched by `purchase_id`; cancelled subscription/donation events are documented. Source: [Tribute webhooks](https://wiki.tribute.tg/for-content-creators/api-documentation/webhooks). | `confirmed`: Wallet Pay page says subscription/donation proceeds are converted to USDT and transferred twice a month when total reaches 100 USDT. `unknown`: whether the same timing applies to this exact digital-product flow. Source: [Tribute Wallet Pay](https://wiki.tribute.tg/for-content-creators/wallet-pay). | `blocked by missing access`: Tribute positions this integration for bot/service owners selling digital products through Telegram/SBP/Stars, but POKROV category acceptance must be approved. Content restrictions prohibit illegal goods/services, deceptive/personal-data misuse, and sanctions violations; they do not explicitly green-light this category. Source: [Tribute digital product integration](https://wiki.tribute.tg/for-content-creators/info-products-and-content/api-integration), [Tribute content restrictions](https://wiki.tribute.tg/for-content-creators/content-restrictions). | `confirmed`: public API and webhook docs are available. Source: [Tribute digital product integration](https://wiki.tribute.tg/for-content-creators/info-products-and-content/api-integration). | `probable`: product links and webhook payloads include purchase/user fields; refund docs require matching `purchase_id`. Dashboard/manual replay evidence was not confirmed in public docs. | Current backend has no Tribute provider whitelist entry or `trbt-signature` verifier; refund event would need entitlement reversal/manual-adjust policy. | `blocked by missing access`: promising fit, but not usable until category approval, adapter implementation, and live webhook/refund proof. |
| Kassa.ai | `unknown`: public site confirms payment acceptance, but no public webhook docs were found. Source: [Kassa.ai](https://kassa.ai/). | `unknown`: no public signature scheme found. | `unknown`: no public retry policy found. | `unknown`: no public refund/cancel event docs found. | `unknown`: no public payout timing found. | `blocked by missing access`: category acceptance not confirmed; site has a merchant contact form only. Source: [Kassa.ai](https://kassa.ai/). | `unknown`: no public API docs found from official site/search results. | `blocked by missing access`: would require merchant dashboard/support confirmation. | Too much hidden integration risk for a beta gate: no public callback contract, no signature contract, no retry/refund evidence. | `blocked by missing access`: do not use for paid beta unless provider supplies written API/webhook docs and accepts the category. |

## Files/docs inspected

- `confirmed`: `portal_bot/bot.py`
- `confirmed`: `portal_bot/helpbot.py`
- `confirmed`: `portal_bot/feedbackbot.py`
- `confirmed`: `portal_bot/payment_providers.py`
- `confirmed`: `portal_bot/pay_attempts_service.py`
- `confirmed`: `portal_bot/tickets_repo.py`
- `confirmed`: payment callback tests in `tests/test_api_payments_callbacks.py`
- `confirmed`: ticket tests in `tests/test_api_auth_and_tickets.py` and `tests/test_tickets_repo.py`
- `confirmed`: reviews username masking tests in `tests/test_reviews_username_masking.py`
- `confirmed`: `docs/product/portal-vpn-product.md`
- `confirmed`: `docs/architecture/app-first-and-bonus-flows.md`
- `confirmed`: official provider docs/sites linked in Evidence links.

## Current state

- `confirmed`: Product/docs target commerce as `buy key -> redeem key -> managed premium`.
- `confirmed`: `GET /api/access-keys/status/{key}` and `POST /api/access-keys/redeem` exist and redeem `GiftCard`-backed access keys into managed access, linked identities, promo slots, hidden transport matrix, location matrix, and provisioning data.
- `confirmed`: Hosted checkout exists for RUB provider order creation through `/api/payments/orders/create-public` using a signed `checkout_ticket`.
- `confirmed`: Current RUB callback activation path applies a paid order directly to `User` via `_apply_external_paid_order`; it does not issue an activation key as the default paid fulfillment.
- `confirmed`: Current implemented RUB provider whitelist is `cardlink`, `freekassa`, `pally`, and `platima`, not Lava.top, Tribute, or Kassa.ai.
- `confirmed`: Callback endpoints exist for `/api/payments/result/{provider}`, `/api/payments/refund/{provider}`, and `/api/payments/chargeback/{provider}`. Result callbacks can activate paid access after signature verification.
- `confirmed`: Callback idempotency is based on `(provider, event_type, external_id)` in `ExternalPaymentEvent`. Existing tests cover duplicate success handling and invalid-signature recovery for the current callback shape.
- `confirmed`: Refund and chargeback callbacks are recorded as statuses, but no entitlement reversal or key revocation flow was found in the callback handler.
- `confirmed`: Freekassa has admin refund API wrapper endpoints, but the local endpoint calls the remote refund method and does not itself reverse customer access.
- `confirmed`: Telegram bot fallback purchase exists: bot can create RUB payment links through the backend, and Telegram Stars invoices remain available for Stars purchases.
- `confirmed`: Telegram Stars flow records `PayAttempt`, sends invoices, handles `successful_payment`, dedupes by a fingerprint stored in `AppSetting`, marks attempts paid, spends points, tracks `paid`, and creates/extends access.
- `confirmed`: `pre_checkout_handler` answers Telegram pre-checkout with `ok=True`; deeper pre-checkout validation was not found.
- `confirmed`: Pay attempts support `started`, `invoice_sent`, `paid`, `abandoned`, and `failed` states. There is a fallback resolver by user, amount, currency, and 24-hour window for non-standard Stars payloads.
- `confirmed`: Promo codes exist in API and bot flows. API redemption tracks denied reasons and supports admin CRUD; bot supports `/promo`, pending promo input, campaign links, and discount/campaign checkout context.
- `confirmed`: Telegram channel bonus exists through `/api/channel/subscriber/check` and `/api/bonuses/channel/claim`; docs and tests confirm `+10 days`, membership checks, TOS gating, and conflict with opening promo claims.
- `confirmed`: Support exists in WebApp/API, main bot, and dedicated helpbot. Ticket lifecycle supports open, in progress, closed, user/admin replies, media metadata, uploads in API, and Telegram notifications.
- `confirmed`: Feedback bot stores feedback entries, notifies admin, supports moderation queue, publishes selected entries as featured reviews, deletes rejected entries, and masks usernames for queue/public display.
- `confirmed`: `/api/reviews` returns only featured reviews and masks usernames such as `mikh****`, falling back to a neutral user label when missing.
- `confirmed`: Notification delivery is best-effort Telegram messaging; failures are logged or ignored in several bot/support paths. No durable notification retry queue was found for support/feedback/payment receipts.

## Flow audit

| Flow | Current finding | Beta label |
| --- | --- | --- |
| buy key -> redeem key -> managed premium | Access-key redeem is implemented, but hosted payment callbacks currently grant paid access directly instead of issuing a key for later redemption. | `confirmed` gap |
| hosted checkout | Public checkout ticket and order creation exist; runtime can be blocked when RUB checkout, ticket secret, public API URLs, or providers are missing. | `confirmed` |
| Telegram bot fallback purchase | Bot supports direct RUB payment links and Stars invoices. | `confirmed` |
| callback verification | Existing callback verifier supports current providers/generic HMAC and Freekassa SCI; no Lava/Tribute/Kassa-specific verifier exists. | `confirmed` |
| attempts | Stars attempts are modeled; external orders/events are modeled separately. | `confirmed` |
| retries/idempotency | Backend idempotency is present for external callbacks and Stars fingerprints; provider retry behavior only confirmed for Lava.top and Tribute docs. | `confirmed`/`blocked by missing access` |
| refund/manual adjustment | Refund/chargeback events can be recorded; entitlement reversal is not automated. Manual extend/block endpoints exist for operators. | `confirmed` gap |
| promo codes | API and bot support promo redemption and admin CRUD. | `confirmed` |
| Telegram channel bonus | Membership check and claim flow exist, with tests for success and denied cases. | `confirmed` |
| support bot | Dedicated helpbot and main-bot support ticket fallback exist. | `confirmed` |
| feedback bot/moderation | Dedicated feedback bot queues, publishes, deletes, and notifies. | `confirmed` |
| masked reviews | API and feedback bot mask display usernames. Tests cover public API masking. | `confirmed` |
| notification delivery | Telegram sends are best-effort; no persistent retry queue was found. | `confirmed` gap |

## Gaps against beta

- `blocked by missing access`: No requested payment candidate has confirmed merchant/category acceptance for POKROV.
- `blocked by missing access`: No requested payment candidate has live webhook verification evidence against POKROV endpoints.
- `confirmed`: Requested providers are not implemented in `payment_providers.py` or `PAYMENT_PROVIDER_WHITELIST`.
- `confirmed`: Current paid callback fulfillment does not match the target `buy key -> redeem key -> managed premium` model.
- `confirmed`: Refund/chargeback callbacks do not revoke or adjust entitlements automatically.
- `confirmed`: Lava.top refund webhooks are absent per official docs, so Lava.top needs a polling/manual refund reconciliation policy before use.
- `confirmed`: Tribute refund webhooks exist, but current backend lacks `trbt-signature` verification and purchase-id-based reversal/manual adjustment mapping.
- `unknown`: Kassa.ai public API/webhook/refund/retry contracts are not available from public official docs.

## P0 blockers

- `blocked by missing access`: Obtain written category/product acceptance from the chosen provider before any paid beta traffic.
- `blocked by missing access`: Prove a live signed webhook from the chosen provider into a staging/production-equivalent endpoint, including duplicate delivery and invalid-signature rejection.
- `confirmed`: Implement provider adapter and whitelist entry for the chosen provider, including exact signature verification, event id extraction, status mapping, and idempotency keys.
- `confirmed`: Decide and implement fulfillment semantics: either align callbacks to issue an activation key and require redeem, or explicitly risk-accept direct callback activation for paid beta.
- `confirmed`: Define refund/chargeback operational policy: automatic entitlement revocation, manual adjustment queue, or explicit risk acceptance for beta.
- `confirmed`: Do not recommend Lava.top, Tribute, or Kassa.ai for paid beta until the above items are complete or explicitly risk-accepted.

## P1 beta polish

- `confirmed`: Add a reconciliation screen/report for external orders showing provider, order id, external id, signature status, local status, activation reason, and linked user.
- `confirmed`: Add durable notification retry or admin-visible failed notification records for payment receipts, support replies, and feedback moderation messages.
- `confirmed`: Add provider-specific tests for selected provider success, duplicate success, invalid signature, refund/cancel, missing user, missing plan, and manual reconciliation.
- `confirmed`: Add a provider smoke checklist to the release gate: create order, pay sandbox/live small amount, receive webhook, verify idempotency, refund/cancel, verify local order state.
- `probable`: Add status polling for providers whose refund or failure webhooks are incomplete, especially Lava.top.

## P2 defer

- `confirmed`: Full multi-provider routing can wait until one paid beta provider is proven end to end.
- `confirmed`: Automatic refund-based access rollback can be deferred only if beta ops explicitly accepts manual adjustment and daily reconciliation.
- `confirmed`: Kassa.ai can remain parked until public docs or merchant dashboard access provides API/webhook contracts.

## Technical debt

- `confirmed`: `PAYMENT_PROVIDER_WHITELIST` and `PROVIDER_META` must both be updated for any new provider; current generic verifier is not enough for provider-specific contracts.
- `confirmed`: External payment statuses are recorded, but order activation and refund reversal are asymmetric.
- `confirmed`: Telegram Stars pre-checkout accepts all invoices without checking payload, amount, or user binding at pre-checkout time.
- `confirmed`: Payment fulfillment mixes direct subscription extension, gift card creation, and access-key redemption. The paid beta needs one explicit default fulfillment path.
- `confirmed`: Support/feedback notification delivery is not durable.

## Security/privacy risks

- `confirmed`: A provider-specific webhook verifier must use the exact provider scheme. Tribute requires `trbt-signature` HMAC-SHA256; Lava.top can use API-key or Basic-auth webhook authentication, not the current generic callback contract.
- `confirmed`: Invalid signatures are rejected by current tests for existing callback shape; new provider tests must prove the same.
- `confirmed`: Refund or chargeback events without entitlement adjustment can leave users with paid access after a reversal.
- `confirmed`: Public review display masks usernames, but support/admin ticket surfaces show raw Telegram IDs/usernames for operator use.
- `confirmed`: Support uploads store metadata and serve files; file retention/access policy was not audited in this R07 pass.

## Required implementation WOs

- `P0`: Choose one provider candidate and complete merchant/category acceptance evidence.
- `P0`: Add provider adapter for selected candidate with exact create-payment, callback parse, signature verification, status mapping, refund/cancel mapping, and idempotency fields.
- `P0`: Add tests for selected provider callbacks, including invalid signature, duplicate delivery, refund/cancel, missing/unknown order, and replay.
- `P0`: Implement paid fulfillment decision: key issuance plus redeem flow, or documented direct-activation beta exception.
- `P0`: Add refund/chargeback reconciliation runbook and either automated entitlement adjustment or admin queue.
- `P1`: Add payment reconciliation admin view/report.
- `P1`: Add durable notification failure visibility for payment/support/feedback bot sends.

## Validation commands

`needs local run`: not executed in this read-only research pass.

- `python -m unittest tests.test_api_payments_callbacks`
- `python -m unittest tests.test_api_auth_and_tickets`
- `python -m unittest tests.test_tickets_repo`
- `python -m unittest tests.test_reviews_username_masking`

Provider validation required before paid beta:

- `blocked by missing access`: create selected-provider merchant test payment.
- `blocked by missing access`: capture provider webhook raw body and headers without printing secrets.
- `blocked by missing access`: verify valid signature path returns success and records one event.
- `blocked by missing access`: replay same webhook and confirm idempotent duplicate.
- `blocked by missing access`: send invalid signature and confirm rejection without poisoning later valid delivery.
- `blocked by missing access`: trigger refund/cancel or provider-supported equivalent and verify local reconciliation path.

## Evidence links

- Local code anchors: `portal_bot/bot.py`, `portal_bot/helpbot.py`, `portal_bot/feedbackbot.py`, `portal_bot/payment_providers.py`, `portal_bot/pay_attempts_service.py`, `portal_bot/tickets_repo.py`, `portal_bot/api.py`.
- Local test anchors: `tests/test_api_payments_callbacks.py`, `tests/test_api_auth_and_tickets.py`, `tests/test_tickets_repo.py`, `tests/test_reviews_username_masking.py`.
- Product/flow docs: `docs/product/portal-vpn-product.md`, `docs/architecture/app-first-and-bonus-flows.md`.
- Lava.top developer docs: https://developers.lava.top/en
- Lava.top terms: https://lava.top/en/docs/terms/
- Tribute digital product integration: https://wiki.tribute.tg/for-content-creators/info-products-and-content/api-integration
- Tribute webhooks: https://wiki.tribute.tg/for-content-creators/api-documentation/webhooks
- Tribute Wallet Pay: https://wiki.tribute.tg/for-content-creators/wallet-pay
- Tribute content restrictions: https://wiki.tribute.tg/for-content-creators/content-restrictions
- Kassa.ai public site: https://kassa.ai/

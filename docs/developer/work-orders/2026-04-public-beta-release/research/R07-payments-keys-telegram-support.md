# R07 Payments Keys Telegram Support

Status: researched

Last researched: 2026-04-25

Scope: payments, activation keys, Telegram reward, support, and feedback reality for the public beta release wave.

Claim labels:

- `confirmed`: verified from local source, canonical docs, or inherited paid-beta evidence.
- `probable`: strongly implied by local evidence, but not fully proven end to end.
- `unknown`: no reliable evidence found in the requested evidence set.
- `needs local run`: covered by local tests or code paths, but not executed in this R07 pass.
- `blocked by missing access`: requires live provider, production, Telegram, admin, brain, or RU access.

## What I Checked

- `confirmed`: `AGENTS.md`.
- `confirmed`: canonical docs: `docs/README.md`, `docs/product/portal-vpn-product.md`, `docs/architecture/system-overview.md`, `docs/architecture/app-first-and-bonus-flows.md`, `docs/operations/deployment-and-access.md`, `docs/operations/monitoring-and-visibility.md`, `docs/developer/developer-guide.md`, `docs/developer/repository-map.md`.
- `confirmed`: backend/API code in `portal_bot/api.py`, `portal_bot/payment_providers.py`, `portal_bot/channel_bonus_service.py`, and `portal_bot/tickets_repo.py`.
- `confirmed`: bot surfaces in `portal_bot/bot.py`, `portal_bot/helpbot.py`, and `portal_bot/feedbackbot.py`.
- `confirmed`: requested tests: `tests/test_api_payments_callbacks.py`, `tests/test_bot_paywall.py`, and `tests/test_api_auth_and_tickets.py`.
- `confirmed`: inherited paid-beta R07/W06 evidence only: `docs/developer/work-orders/2026-04-beta-release/research/R07-payments-telegram-support.md` and `docs/developer/work-orders/2026-04-beta-release/evidence/logs/WO-006-payments-keys-bonuses-support.md`.

## Current State

- `confirmed`: Canonical product/architecture docs target key-first commerce: buy key, redeem key, managed premium.
- `confirmed`: API access-key routes exist: `GET /api/access-keys/status/{key}`, `POST /api/access-keys/redeem`, and `POST /api/admin/access-keys/issue` in `portal_bot/api.py`.
- `confirmed`: Access-key redeem is `GiftCard`-backed, one-time, TOS-gated, self-redeem-blocked, and uses an atomic `redeemed_by is None` update before returning refreshed access, identity, promo, transport, location, and provisioning payloads.
- `confirmed`: Public/provider order creation exists through `/api/payments/orders/create-public` with signed `checkout_ticket`; bot fallback creates payment links through the same public-order endpoint.
- `confirmed`: Current implemented RUB provider set is `cardlink`, `pally`, `platima`, and `freekassa`; inherited R07 says Lava.top, Tribute, and Kassa.ai remain blocked by missing category acceptance and live webhook proof.
- `confirmed`: Checkout has a runtime switch/guard family: `RUB_CHECKOUT_ENABLED`, `CHECKOUT_TICKET_SECRET`, public URL checks, success/fail URL checks, and provider configuration checks. `/api/payments/providers` reports blocked reasons instead of listing providers when the contour is not ready.
- `confirmed`: Callback endpoints record result/refund/chargeback events and normalize statuses. Paid activation only happens for non-duplicate, signed `result` events normalized to `paid`.
- `confirmed`: Failed, cancelled, pending verification, manual review, refund, and chargeback states are recorded for reconciliation and do not automatically extend access.
- `confirmed`: Refund and chargeback callbacks do not automatically revoke, shorten, or reassign access.
- `confirmed`: Admin payment reconciliation can mutate order status and `paid_at`, but it does not call the paid fulfillment path or issue/redeem a key.
- `confirmed`: Telegram channel reward is implemented through read-only `/api/channel/subscriber/check` and explicit `/api/bonuses/channel/claim`; membership check uses linked Telegram for app-first users, grants `+10 days`, and is idempotent after first claim.
- `confirmed`: Telegram reward failures are fail-closed for missing link, missing TOS, manual accounts, opening-bonus conflict, not-member, and Telegram/API membership errors.
- `confirmed`: Support ticketing is real async ticketing, not decorative UI: API creates/reuses an active ticket, stores messages and media metadata, supports uploads, supports admin replies/status, and helpbot writes to the same tables.
- `confirmed`: Support/feedback notifications are best-effort Telegram sends; I did not find a durable retry queue or dead-letter table for failed user/admin notifications.
- `confirmed`: Feedback/review flow is moderated: `/api/reviews` returns featured only and masks usernames; `/api/feedback` and `feedbackbot` store private queue entries, and admins can publish/delete.
- `probable`: Feedback privacy still depends heavily on moderator judgment because review text is not automatically scrubbed for personal data before publication.

## Highest-Risk Findings

1. `blocked by missing access`: Provider acceptance and live webhook proof are still missing. Local code supports current provider adapters, but public beta payment readiness still lacks written category/product acceptance, a controlled live or sandbox payment, signed webhook receipt, duplicate webhook replay, invalid-signature rejection, and refund/chargeback proof against the actual chosen provider.

2. `confirmed`: Commerce fulfillment still diverges from the key-first product model. Access-key issue/redeem exists, but paid callbacks currently extend the user directly via `_apply_external_paid_order`; they do not issue an activation key for user redemption. This is a product/ops mismatch for a public beta that is supposed to sell activation keys.

3. `confirmed`: Refund/chargeback/manual-review handling is reconciliation-only, not entitlement-safe. Non-paid statuses do not grant access, which is good, but refund and chargeback do not revoke access, and admin reconciliation to `paid` marks the order without provisioning the user or issuing a key.

4. `confirmed`: Activation-key endpoints appear under-tested in the requested test set. I found payment callback, bot paywall, ticket, and channel bonus tests, but no direct `tests/*.py` hits for `/api/access-keys/status`, `/api/access-keys/redeem`, or `/api/admin/access-keys/issue` in this pass.

5. `confirmed`: Support and feedback are real but operationally best-effort. Tickets and moderation queues persist, but Telegram delivery failures for support replies, ticket notifications, and feedback publication are logged/ignored rather than retried durably; feedback publication masks usernames at public API level, but review body privacy depends on manual moderation.

## Idempotency And Failure Behavior

| Area | Finding | Label |
| --- | --- | --- |
| Payment callback duplicate delivery | `_record_external_payment_event` dedupes by provider, event type, and external id; duplicate signed results do not re-activate. | `confirmed` |
| Invalid payment signature | Invalid signatures are rejected when tolerant mode is false; later valid callbacks for the same external id are not poisoned. | `confirmed` |
| Failed/cancelled/manual-review payment | Recorded on external order/event without activation. | `confirmed` |
| Refund/chargeback | Recorded as statuses without automatic entitlement reversal. | `confirmed` |
| Manual admin payment reconcile | Can change order status; does not provision access or key. | `confirmed` |
| Access-key double redeem | Atomic update prevents redeem after `redeemed_by` is set. | `confirmed` |
| Channel bonus repeat claim | Returns already-claimed state without granting again. | `confirmed` |
| Support ticket create | Reuses the user's active ticket instead of opening unlimited parallel active tickets. | `confirmed` |
| Feedback bot repeated pending entry | Upserts the user's latest `new` feedback entry rather than creating unbounded duplicates. | `confirmed` |

## Emergency Switches / Runtime Guards

- `confirmed`: Payment checkout can be disabled by `RUB_CHECKOUT_ENABLED=false`.
- `confirmed`: Missing `CHECKOUT_TICKET_SECRET`, `PUBLIC_API_BASE_URL`, success/fail URL, or enabled provider configuration blocks provider listing/order creation.
- `confirmed`: `PAYMENT_CALLBACK_TOLERANT_MODE=false` rejects invalid signatures; if enabled, invalid callbacks are still not activated but become reconciliation records.
- `confirmed`: Removing/emptying `PUBLIC_CHANNEL` blocks channel bonus endpoints, but I did not find a dedicated channel-bonus kill switch separate from channel configuration.
- `confirmed`: `HELP_BOT_TOKEN` and `FEEDBACK_BOT_TOKEN` missing cause those bot processes to exit at startup.
- `unknown`: No public-beta evidence found for a tested live emergency rollback/switch drill for checkout, callback fulfillment, activation-key redeem, support bots, or feedback bot.

## Test Evidence

- `needs local run`: I did not run tests in this R07 pass to avoid creating repo-local artifacts outside the assigned research file.
- `confirmed`: `tests/test_api_payments_callbacks.py` covers duplicate callbacks, invalid signature recovery, signed failed/cancelled/manual-review results, FreeKassa SCI notify, provider catalog blocking, generic public order creation, and Pally paid callback.
- `confirmed`: `tests/test_bot_paywall.py` covers checkout-ticket URLs, provider payment choice keyboard, direct RUB payment link behavior, hidden Stars-first paywall expectations, and related bot paywall copy.
- `confirmed`: `tests/test_api_auth_and_tickets.py` covers ticket lifecycle/media metadata, ticket upload, channel bonus success/idempotency/denials, and bonus-event admin summary.
- `confirmed`: `tests/test_reviews_username_masking.py` was not requested but inherited R07/W06 used it; it covers public review username masking and featured-only public review output.

Suggested focused local validation before signoff:

```powershell
python -m pytest tests/test_api_payments_callbacks.py tests/test_bot_paywall.py tests/test_api_auth_and_tickets.py tests/test_reviews_username_masking.py -q
```

Suggested live/provider validation before public beta:

- `blocked by missing access`: provider category/product acceptance in writing.
- `blocked by missing access`: create one controlled payment through the chosen live/sandbox provider.
- `blocked by missing access`: capture valid signed webhook headers/body with secrets redacted.
- `blocked by missing access`: replay the same webhook and confirm one event/one fulfillment.
- `blocked by missing access`: send or simulate invalid signature and confirm rejection without poisoning later valid delivery.
- `blocked by missing access`: trigger refund/chargeback/cancel/manual-review equivalent and confirm the operator reconciliation path and access/key outcome.

## Bottom Line

`blocked by missing access`: Public beta paid checkout should not be treated as live-ready until provider acceptance and live signed webhook proof exist.

`confirmed`: Backend hardening reduced the worst callback activation risk, but the remaining release decision is still about live provider proof, key-first fulfillment alignment, refund/chargeback policy, and operational retry/reconciliation evidence.

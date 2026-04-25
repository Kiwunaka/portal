# WO-006 Payments, Keys, Telegram Bonus, Support/Feedback

Status: draft
Lane: platform

## Scope

Make paid beta commercial and support flows safe for live low-volume production use.

## Assigned Paths

- `portal_bot/bot.py`
- `portal_bot/helpbot.py`
- `portal_bot/feedbackbot.py`
- payment/key services
- ticket/review services
- `copy/catalog.ru.json`
- canonical docs if behavior changes

## Payment Integration Policy

Provider is implementation detail. Backend normalizes all providers into one internal payment event model:

- provider
- provider_payment_id
- provider_invoice_id / order_id
- user_id / app_account_id
- tariff_id
- amount
- currency
- status
- paid_at
- raw_event_hash
- signature_verified
- idempotency_key

Required states:

- `created`
- `pending`
- `paid`
- `failed`
- `cancelled`
- `refunded`
- `manual_review`

Preferred beta flow:

payment -> verified webhook -> activation key or direct subscription extension -> admin-visible payment record.

Manual fallback:

If webhook fails but payment is confirmed manually, admin must be able to issue or extend access with an audit note.

## P0 Payment Gates

- tariff catalog matches checkout UI
- successful payment creates exactly one entitlement
- duplicate webhook does not double-extend access
- failed payment does not create access
- refunded/cancelled payment is visible to admin
- unknown provider event goes to `manual_review`
- payment record is visible in user profile/admin
- admin can manually reconcile low-volume beta payment
- user receives clear next step after payment
- payment logs do not expose secrets, tokens, card data, or private webhook payloads

## Provider Research Dependency

Do not implement a paid beta provider until R07 confirms or explicitly risk-accepts category acceptance and webhook verification for the candidate.

Provider candidates to classify:

- Lava.top
- Tribute
- Kassa.ai if still considered

For each candidate, record webhook support, signature verification, retry behavior, refund/cancel events, payout timing, allowed product/category confirmation, API docs availability, manual reconciliation path, and low-volume paid beta risks.

## Validation

- `python -m pytest tests/test_api_payments_callbacks.py -q`
- `python -m pytest tests/test_bot_paywall.py tests/test_tickets_repo.py tests/test_reviews_username_masking.py -q`
- `python -m pytest tests/test_worker_retention.py tests/test_free_cycle_service.py -q`

## Handoff Format

- What I checked
- What I found
- What I changed
- How I verified
- What remains / risk

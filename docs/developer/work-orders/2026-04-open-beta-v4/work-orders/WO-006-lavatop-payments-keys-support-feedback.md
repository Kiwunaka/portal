# WO-006 Lava.top Payments, Keys, Support, Feedback

Status: historical work order; current beta decision synced 2026-05-26
Owner: W06

## Scope

- `portal_bot/payment_providers.py`.
- `portal_bot/api.py`.
- Payment callbacks, provider catalog, checkout, access keys, payment tests, support notification reliability.
- Payment operations docs.

## Acceptance

- `lavatop` provider adapter exists if provider docs confirm required API shape.
- Provider catalog reports config state and blocked reasons.
- Webhook auth supports the configured mode.
- Duplicate replay is idempotent.
- Invalid auth does not mutate paid state.
- Failed/cancelled/refund/chargeback paths do not silently provision.
- Paid success aligns with the documented key-first fulfillment model.
- If live proof is blocked for a future provider, plan, or release candidate, public checkout must degrade with honest copy; the 2026-05-15 Lava.top evidence pack is beta-ready for the current outside-store beta.

## Verification

```powershell
python -m pytest tests/test_api_payments_lavatop.py tests/test_api_payments_callbacks.py tests/test_bot_paywall.py -q
python scripts/payment_provider_live_smoke.py --provider lavatop --redact
python scripts/payment_webhook_replay_smoke.py --provider lavatop --redact
```

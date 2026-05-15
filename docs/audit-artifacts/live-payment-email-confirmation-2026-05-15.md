# Live Payment And Email Confirmation - 2026-05-15

Status: `PASS_WITH_LIMITATIONS`

Timezone: Moscow time unless noted. This artifact intentionally omits raw payment ids, Telegram ids, user ids, mailbox addresses, callback payloads, and secret values.

## Confirmed

- Email auth: public register, verify-code delivery to a real mailbox, and login continuation were confirmed by the operator.
- Lava.top checkout: a live `start_99` RUB order was paid through the hosted checkout page and credited to the linked cabinet account.
- Runtime provider catalog: `GET /api/payments/providers` exposed Lava.top as the enabled RUB provider and did not return a blocked provider state.
- Backend callback path: an authenticated success callback through the normal Lava.top result handler activated access; invalid/missing auth remains rejected.
- Fulfillment safety: backend tests cover replay/idempotency and prevent a second account extension after order fulfillment reaches `account_extended`.
- User-visible result: the operator confirmed the paid access was visible after the callback replay.

## Root Cause Captured

Initial provider webhook attempts were rejected because the control-plane proxy exposed the callback source to the API as loopback while `LAVATOP_WEBHOOK_IP_ALLOWLIST` expected the documented provider IP. The backend now allows loopback-proxy callbacks to continue to the normal webhook-auth check only when Lava.top webhook auth is configured. Missing or invalid auth still rejects the callback.

## Code And Deploy Evidence

- Backend fix deployed from commit `f9b499d` (`Fix Lava webhook behind local proxy`).
- Cabinet refresh fix deployed from commit `2670c1e` (`Refresh cabinet after external checkout return`).
- Backend payment callback tests: `pytest tests\test_api_payments_callbacks.py -q` -> `32 passed`.
- Webapp production build after session-refresh change: `npm.cmd run build` in `webapp` -> passed.

## Remaining Evidence Gaps

- Live failed-payment callback proves no fulfillment.
- Live or provider-backed refund/chargeback reconciliation procedure.
- Anonymous public paid checkout issues exactly one emailed access key.
- Hosted Lava.top return URL behavior after payment.
- Broad public release `GO` decision with final release handoff, current-origin, brain-origin, and RU-origin evidence.

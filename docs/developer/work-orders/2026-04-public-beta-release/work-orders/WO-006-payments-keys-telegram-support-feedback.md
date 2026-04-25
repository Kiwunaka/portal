# WO-006 Payments, Keys, Telegram, Support, Feedback

Status: draft
Agent: W06
Lane: platform
Priority: P0

## Goal

Make payment, activation-key, Telegram reward, support, and feedback flows safe enough for public beta or explicitly disabled with honest UI states.

## Write Scope

- `portal_bot/api.py`
- `portal_bot/bot.py`
- `portal_bot/helpbot.py`
- `portal_bot/feedbackbot.py`
- `portal_bot/pay_attempts_service.py`
- `portal_bot/events_service.py`
- `tests/test_api_payments_callbacks.py`
- `tests/test_bot_paywall.py`
- `tests/test_worker_retention.py`
- `tests/test_free_cycle_service.py`
- `docs/architecture/app-first-and-bonus-flows.md`
- `docs/user/portal-vpn-user-guide-ru.md`
- `docs/developer/work-orders/2026-04-public-beta-release/**`

## Acceptance

- Successful payment creates exactly one entitlement.
- Duplicate webhook does not double-extend.
- Failed/refunded/chargeback/unknown events do not grant access automatically.
- `manual_review` is visible to admins.
- Telegram bonus remains explicit claim, not read-only status mutation.
- Support ticket and feedback paths are real or unavailable.

## Validation

```powershell
python -m pytest tests/test_api_payments_callbacks.py tests/test_bot_paywall.py -q
python -m pytest tests/test_worker_retention.py tests/test_free_cycle_service.py -q
python -m pytest tests/test_api_auth_and_tickets.py -q
```


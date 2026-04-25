# WO-005 Backend Contract Hardening

Status: draft
Lane: platform

## Scope

Harden app-first backend contracts for paid beta.

## Assigned Paths

- `portal_bot/api.py`
- `portal_bot/models.py`
- `portal_bot/migrations.py`
- `portal_bot/app_first_service.py`
- `portal_bot/device_service.py`
- `portal_bot/web_auth_service.py`
- `portal_bot/events_service.py`
- `portal_bot/pay_attempts_service.py`
- `tests/**`

Use explicit lock before editing `portal_bot/api.py`.

## Required Behavior

- Trial creates real account/device/session/subscription source.
- Expired trial falls to free monthly state.
- Paid premium stays unlimited/up to 5 devices.
- Free user gets free node pool only.
- Premium user gets enabled non-free pool.
- Managed profile delivery works and hides secrets from user-facing summaries.
- Device limits, rename/revoke, route mode, selected apps, support context, pagination, filtering, errors, rate limits, and idempotency are covered.
- Migrations follow backup and rollback policy.

## Migration Policy

- Migrations are allowed only after backup and rollback review.
- Destructive migrations require explicit orchestrator approval.
- Production migration evidence must include backup timestamp, command, result, post-migration smoke, and rollback feasibility.

## Validation

- `python -m pytest portal_bot/tests/test_app_first_api.py -q`
- `python -m pytest tests/test_portal_api.py tests/test_api_auth_and_tickets.py tests/test_api_p0_extensions.py -q`
- `python -m pytest tests/test_smart_connect_api.py tests/test_network_rollout_api.py -q`

## Handoff Format

- What I checked
- What I found
- What I changed
- How I verified
- What remains / risk


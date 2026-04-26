# WO-005 Backend Contract Hardening

Status: pending research
Owner: W05

## Scope

- `portal_bot/api.py`.
- Auth, sessions, access keys, entitlements, support, migrations, rate limits, and tests.
- API contract docs.

## Acceptance

- Access-key status, redeem, and admin issue paths are tested.
- Entitlement/payment state machines are explicit.
- Sensitive endpoints have beta guardrails.
- No raw secrets or configs are logged.

## Verification

```powershell
python -m pytest portal_bot/tests/test_app_first_api.py tests/test_api_auth_and_tickets.py tests/test_portal_api.py -q
python scripts/api_lifecycle_smoke.py
```

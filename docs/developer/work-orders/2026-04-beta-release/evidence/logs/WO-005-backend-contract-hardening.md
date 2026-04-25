# WO-005 Backend Contract Hardening Evidence

Status: first-pass backend guardrails complete
Agent: W05
Date: 2026-04-25

## What I Checked

- Required wave context, synthesis, R06 backend research, R07 payment-boundary context, and WO-005.
- Platform branch `codex/beta-release-platform`.
- Backend ownership files before edit; unrelated dirty work was left untouched.

## What I Found

- App-first happy path already had useful coverage.
- Externally reachable beta edges did not have a shared rate-limit/error contract.
- Payment-provider behavior remains W06-owned and was not changed in this pass.

## What Changed

- Added backend-owned beta throttling in `portal_bot/api.py` with structured `429` responses and `Retry-After`.
- Applied throttles to fresh `start-trial` creation while preserving same-`install_id` idempotency.
- Applied throttles to Telegram/email auth, access-key status/redeem, ticket create, and ticket upload.
- Added app-first rate-limit tests in `portal_bot/tests/test_app_first_api.py`.
- Documented the beta rate-limit contract in `docs/architecture/app-first-and-bonus-flows.md`.

## How I Verified

Passing:

```powershell
python -m pytest portal_bot/tests/test_app_first_api.py -q --basetemp .tmp/pytest-w05-appfirst
python -m pytest tests/test_portal_api.py tests/test_api_auth_and_tickets.py tests/test_api_p0_extensions.py -q --basetemp .tmp/pytest-w05-core
python -m pytest tests/test_smart_connect_api.py tests/test_network_rollout_api.py -q --basetemp .tmp/pytest-w05-rollout
python -m pytest portal_bot/tests/test_email_auth.py -q --basetemp .tmp/pytest-w05-email
git diff --check -- portal_bot/api.py portal_bot/tests/test_app_first_api.py docs/architecture/app-first-and-bonus-flows.md
```

Additional signal:

```powershell
python -m pytest tests/test_api_payments_callbacks.py -q
```

Result: `18 passed, 1 failed`. The failure is an existing payment-copy expectation mismatch: expected `POKROV VPN Приветственный 30 дней`, actual `POKROV VPN Старт на 30 дней`.

## What Remains / Risk

- Rate limits are in-process hashed fingerprints controlled by `API_RATE_LIMIT_<SCOPE>_PER_MINUTE`; they are paid beta guardrails, not durable distributed quotas.
- Live Postgres migration/schema and live control-panel smoke remain blocked by access/out of scope.
- Payment fulfillment, refund/cancel policy, provider webhook verification, and payment copy drift remain W06/W10 concerns.

## Changed File Paths

- `C:/Users/kiwun/Documents/ai/VPN/portal_bot/api.py`
- `C:/Users/kiwun/Documents/ai/VPN/portal_bot/tests/test_app_first_api.py`
- `C:/Users/kiwun/Documents/ai/VPN/docs/architecture/app-first-and-bonus-flows.md`

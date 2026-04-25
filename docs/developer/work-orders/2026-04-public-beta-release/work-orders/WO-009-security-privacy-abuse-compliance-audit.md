# WO-009 Security, Privacy, Abuse, Compliance Audit

Status: draft
Agent: W09
Lane: mixed
Priority: P0

## Goal

Audit public beta readiness for secrets, admin auth, sessions, Telegram auth, payment webhooks, local control surfaces, raw config leaks, uploads, diagnostics privacy, rate limits, CORS/CSRF, logs, screenshots, legal/refund/privacy, and abuse controls.

## Write Scope

- `portal_bot/**`
- `webapp/src/**`
- `marketing/src/**`
- `scripts/client_security_smoke.py`
- `tests/test_api_auth_and_tickets.py`
- `tests/test_api_payments_callbacks.py`
- `tests/test_public_copy_guardrails.py`
- `C:/Users/kiwun/Documents/ai/POKROV-app/**` when client security evidence is required
- `docs/developer/work-orders/2026-04-public-beta-release/**`

## Acceptance

- P0 security issues fixed or public scope changed to remove the claim.
- P1 risks fixed or explicitly accepted.
- No secrets in public evidence.
- No raw configs/links/local-control surfaces in normal user UI.
- Payment/auth flows protected.

## Validation

```powershell
python -m pytest tests/test_api_auth_and_tickets.py tests/test_api_payments_callbacks.py -q
python scripts/client_security_smoke.py
python -m pytest tests/test_public_copy_guardrails.py -q
```


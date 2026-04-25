# WO-009 Security, Privacy, Abuse, Compliance Audit

Status: draft
Lane: mixed

## Scope

Audit and fix paid beta security, privacy, abuse, and compliance blockers.

## Focus Areas

- secrets audit
- dependency audit
- auth/session/token audit
- Telegram initData validation
- payment callback validation
- admin RBAC
- rate limits
- CORS/CSRF/session handling
- localhost/control-surface audit
- diagnostic payload privacy
- logs privacy
- support attachments
- public legal text
- no third-party ads/ad SDKs
- no secrets in screenshots/logs
- no raw configs in user UI

## Required Outcome

- P0 fixed or wave blocked.
- P1 fixed or explicitly accepted with beta decision.
- Sensitive flows have tests or manual evidence.
- Diagnostics are user-safe.
- Admin-only sensitive data is protected.
- Payment/webhook flows are idempotent.

## Validation

- `python -m pytest tests/test_api_auth_and_tickets.py tests/test_api_payments_callbacks.py -q`
- `python scripts/client_security_smoke.py`
- `python -m pytest tests/test_public_copy_guardrails.py -q`

## Handoff Format

- What I checked
- What I found
- What I changed
- How I verified
- What remains / risk


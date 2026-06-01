# WO-009 Security, Privacy, Abuse, Compliance Audit

Status: historical work order; current beta decision synced 2026-05-26
Owner: W09

## Scope

- Secret redaction.
- Payment callback threat model.
- Telegram init-data threat model.
- Admin auth and roles.
- Support uploads.
- Logs, legal copy, privacy copy, and client log exposure.

## Acceptance

- No secrets in docs or evidence.
- Payment invalid-auth tests pass.
- Admin unauthorized checks pass.
- Support uploads have size/type/access controls or explicit blockers.
- Legal and public copy match actual product behavior.

## Verification

```powershell
python -m pytest tests/test_api_payments_callbacks.py tests/test_api_auth_and_tickets.py -q
python scripts/client_security_smoke.py
```

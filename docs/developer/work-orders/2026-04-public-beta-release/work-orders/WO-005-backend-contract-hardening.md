# WO-005 Backend Contract Hardening

Status: draft
Agent: W05
Lane: platform
Priority: P0

## Goal

Harden backend app-first, session, trial, access-key, managed-profile, rate-limit, node-pool, and admin contracts for public beta.

## Write Scope

- `portal_bot/api.py`
- `portal_bot/app_first_service.py`
- `portal_bot/models.py`
- `portal_bot/migrations.py`
- `portal_bot/*service.py`
- `portal_bot/tests/**`
- `tests/test_portal_api.py`
- `tests/test_api_auth_and_tickets.py`
- `docs/architecture/system-overview.md`
- `docs/architecture/app-first-and-bonus-flows.md`
- `docs/developer/work-orders/2026-04-public-beta-release/**`

## Acceptance

- Trial is real or consistently disabled.
- Managed profile delivery works or returns honest unavailable state.
- Premium/free node pool rules are preserved.
- Fresh public beta rate limits protect high-risk surfaces.
- Public/user APIs do not expose raw secrets by default.

## Validation

```powershell
python -m pytest portal_bot/tests/test_app_first_api.py -q
python -m pytest tests/test_portal_api.py tests/test_api_auth_and_tickets.py -q
python scripts/api_lifecycle_smoke.py
```


# WO-004 Public Release Admin Console

Status: draft
Agent: W04
Lane: platform
Priority: P0

## Goal

Make the admin console a real public beta operator surface for users, payments, access, devices, tickets, nodes, incidents, downloads, and emergency controls.

## Write Scope

- `webapp/src/app/(dashboard)/admin/**`
- `webapp/src/components/admin/**`
- `webapp/src/lib/api.ts`
- `portal_bot/api.py`
- `tests/test_admin_*.py`
- `webapp/e2e/admin-*.spec.ts`
- `docs/developer/work-orders/2026-04-public-beta-release/**`

## Acceptance

- Critical modules use backend data or explicit unavailable states.
- Admin auth gate is verified.
- Payment ledger/manual reconcile are visible when supported.
- Emergency controls are visible or documented as blocked.
- No raw secrets/configs leak to normal user UI.

## Validation

```powershell
python scripts/admin_webapp_smoke.py
python -m pytest tests/test_admin_payments_api.py tests/test_api_auth_and_tickets.py -q
cd webapp
npm.cmd run build
npm.cmd run test:e2e:admin
```


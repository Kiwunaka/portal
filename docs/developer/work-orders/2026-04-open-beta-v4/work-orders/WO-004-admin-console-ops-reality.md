# WO-004 Admin Console Ops Reality

Status: pending research
Owner: W04

## Scope

- `webapp/src/app/(dashboard)/admin/`.
- Admin API contracts for users, payments, tickets, nodes, bonuses, metrics.
- Payment provider status and blocked reason rendering.
- Origin-separated node/probe status.

## Acceptance

- Admin can see provider config status and blocked reasons.
- Payment reconciliation is audit-safe.
- Node/probe status separates `current-origin`, `brain-origin`, and `RU-origin`.
- Narrow/mobile admin views do not break critical actions.

## Verification

```powershell
Push-Location webapp
npm.cmd run build
npm.cmd run test:e2e:admin
Pop-Location
python scripts/admin_webapp_smoke.py
```

# WO-004 Admin Console

Status: draft
Lane: platform

## Scope

Make web admin the primary real operator surface for paid beta.

## Assigned Paths

- `webapp/src/app/(dashboard)/admin/**`
- `webapp/src/components/admin/**`
- `webapp/e2e/admin-gate.spec.ts`
- `portal_bot/api.py`
- admin API tests
- canonical docs if admin contract changes

Use explicit lock before editing `portal_bot/api.py`.

## Real Admin Module Definition

A module is real only if it satisfies at least one:

- reads real backend data
- writes real backend state with audit log
- shows explicit unavailable/empty state based on backend response
- is clearly marked as coming soon and not used as a beta gate

A module is decorative if it renders fake counters, hardcoded users/payments/nodes/tickets, pretend-success actions, or hides backend failure behind success UI.

## Required Modules

- dashboard
- users
- subscriptions
- devices
- roles
- tariffs/plans
- payments
- promocodes
- notifications/broadcast
- logs/action journal
- network
- nodes
- routes
- tickets
- incidents
- SLA/support
- metrics/alerts

## Validation

- `cd webapp; npm.cmd run build`
- `cd webapp; npm.cmd run test:e2e:admin`
- `python -m pytest tests/test_api_auth_and_tickets.py tests/test_admin_webapp_smoke.py -q`
- `python scripts/admin_webapp_smoke.py`

## Handoff Format

- What I checked
- What I found
- What I changed
- How I verified
- What remains / risk


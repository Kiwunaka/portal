# R05 Admin Console Readiness

Status: researched
Date: 2026-04-25
Scope: admin console readiness for the POKROV public beta release wave.

Claim labels used below: `confirmed`, `probable`, `unknown`, `needs local run`, `blocked by missing access`.

## Files And Evidence Checked

- `AGENTS.md`
- `docs/README.md`
- `docs/product/portal-vpn-product.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/app-first-and-bonus-flows.md`
- `docs/operations/deployment-and-access.md`
- `docs/operations/monitoring-and-visibility.md`
- `docs/developer/developer-guide.md`
- `docs/developer/repository-map.md`
- `webapp/README.md`
- `webapp/src/app/(dashboard)/admin/**`
- `webapp/src/components/admin/**`
- `webapp/src/lib/api.ts`
- `portal_bot/api.py` admin routes and related handlers
- `webapp/e2e/admin-gate.spec.ts`
- `tests/test_admin_payments_api.py`
- `tests/test_admin_webapp_smoke.py`
- inherited paid-beta evidence only: `docs/developer/work-orders/2026-04-beta-release/research/R05-admin-console.md`
- inherited paid-beta W04 evidence only: `docs/developer/work-orders/2026-04-beta-release/evidence/logs/WO-004-admin-console.md`

No secrets were read or printed. I did not edit any file except this assigned research note.

## Current Surface

`confirmed`: The web admin remains the primary operator surface. Current routes are `/admin`, `/admin/dashboard`, `/admin/users`, `/admin/bonuses`, `/admin/referrals`, `/admin/promos`, `/admin/payments`, `/admin/nodes`, `/admin/network`, `/admin/broadcast`, and `/admin/tickets`.

`confirmed`: Browser admin access is gated in `webapp/src/app/(dashboard)/admin/layout.tsx` by `usePortalSession()` plus `user.is_admin`. Backend admin APIs call `_require_admin`, which verifies the Telegram/web auth actor against admin configuration.

`confirmed`: The admin IA broadly matches the canonical operator grouping: Diagnostics, People, Access, Payments, Network, Messaging, and Feedback.

`confirmed`: Paid-beta R05's biggest payment gap has been partially closed by W04. The current tree has `/admin/payments`, `/api/admin/payments/orders`, reconciliation UI/API, and `tests/test_admin_payments_api.py`.

## Module Readiness

| Area | Readiness | Evidence |
| --- | --- | --- |
| Auth gate | `confirmed` | Frontend blocks non-admins; backend admin routes use `_require_admin`. Production session behavior is still `blocked by missing access`. |
| Dashboard | `confirmed` | `/admin/dashboard` loads summary, metrics status, timeseries, users, and tickets. `/admin` home counts nav categories/routes only. |
| Users/access | `confirmed` | Search/filter/pagination, user card, manual create/extend/block, token regeneration, key actions, key policies, audit tab, observer data, and manual/test deletion guard exist. |
| Devices | `probable` | Device context appears inside user detail, but there is no standalone device console or device-centric reset/triage workflow. |
| Payment ledger | `confirmed` | `/admin/payments` lists `ExternalOrder` rows and summarized last callback state without raw payloads. |
| Reconciliation | `confirmed` | Reconcile requires an audit note and writes `admin_payment_reconcile`; it intentionally does not grant access automatically. |
| Plans/tariffs | `probable` | Backend and API client have `/api/admin/plans` CRUD, but no first-class admin page exposes it. `/admin/promos` reads shared frontend plan data for key issuing. |
| Promo codes | `probable` | Backend and API client have promo CRUD, but the visible `/admin/promos` page focuses on activation keys and promo slots. |
| Activation keys | `confirmed` | `/admin/promos` issues activation keys through backend admin API and checks key status through the public key-status endpoint. |
| Bonuses/referrals | `confirmed` | Web routes call real wheel, loyalty, referral queue, start-link, and campaign-link APIs. |
| Tickets/support | `confirmed` | `/admin/tickets` loads real ticket queue, changes stable statuses, sends replies, and backend audits replies/status changes. |
| Nodes | `confirmed` | `/admin/nodes` loads node health, metrics freshness, traffic, drift, observer, transport, and can sync/drain/enable/disable/resync nodes. |
| Emergency controls | `probable` | Drain/enable/disable/resync exist, but force-disable is not exposed in UI and there is no incident-mode confirmation/checklist surface. |
| Network rollout | `confirmed` | `/admin/network` reads/writes `network_rollout_config`, but the editor is raw JSON plus summary cards. |
| Incidents/SLA | `unknown` | No first-class `/admin/incidents` or SLA console found; dashboard/node alerts are incident-like only. |
| Roles/RBAC | `confirmed` | Admin is boolean `is_admin`; no roles or permission scopes are implemented. |

## Fake Counters And Pretend Actions

- `confirmed`: `/admin` home counters are route/catalog counters, not operational users, revenue, tickets, or node counts.
- `confirmed`: `/admin/dashboard` uses backend data for summary, metrics, users, tickets, and top-node cards.
- `confirmed`: `/admin/promos` contains shared/static product facts alongside real activation-key and promo-slot actions; treat the fact cards as reference, not live health.
- `confirmed`: `webapp/e2e/admin-gate.spec.ts` heavily mocks backend responses. It proves UI behavior and routing, not live admin data freshness.
- `confirmed`: Payment reconciliation success does not imply access fulfillment. The page says no access was changed automatically.
- `confirmed`: Node disable UI calls the non-force disable path. If mapped users remain, backend returns `409` rather than pretending success.

## Five Highest-Risk Findings

1. `needs local run`: I did not run `npm.cmd run build`, `npm.cmd run test:e2e:admin`, or focused backend tests in this research pass to avoid touching files outside the assigned note. Public-beta readiness still needs those exact local gates.
2. `blocked by missing access`: Production admin login, deployed admin session expiry, live write permissions, and production data freshness were not verified against `app.pokrov.space` / `api.pokrov.space`.
3. `probable`: Emergency controls are incomplete for an incident shift. The UI supports drain/enable/disable/resync, but does not expose force-disable, guided incident state, or an operator confirmation path for high-blast-radius node actions.
4. `confirmed`: Network rollout editing is raw JSON. A valid but wrong payload can alter transport, DNS, routing defaults, or operator-lab allowlists; there is no structured guardrail UI for public-beta operators.
5. `probable`: Payment ledger is real but not a full finance/support console. Reconciliation is note-only and does not fulfill access; refunds, chargebacks, key lineage, and entitlement decisions still require separate operator discipline.

## Remaining Beta Gaps

- `probable`: Device support remains embedded in user detail rather than first-class. This weakens app-first support triage when the question starts from install ID, platform, app version, last seen, or route state.
- `probable`: Plan and promo-code CRUD exists below the surface, but the visible admin does not expose a dedicated plan/promocode editor.
- `confirmed`: Admin audit is visible per selected user, and `/api/admin/audit` has an API wrapper, but no standalone action-journal route exists.
- `unknown`: No incident or SLA lifecycle was found. If beta support promises include SLA handling, this needs either implementation or explicit exclusion.
- `needs local run`: Some admin files still contain mojibake-looking dash/separator text in network/admin surfaces. Browser E2E and the admin smoke should decide whether this is visible to operators.

## Verification Needed

Run from the repo root or `webapp/` as appropriate:

```powershell
python -m pytest tests/test_admin_payments_api.py tests/test_admin_webapp_smoke.py -q
cd webapp
npm.cmd run build
npm.cmd run test:e2e:admin
```

Live access checks remain `blocked by missing access` until an authorized operator verifies:

- `/admin/dashboard`
- `/admin/users`
- `/admin/payments`
- `/admin/nodes`
- `/admin/network`
- `/admin/tickets`
- `/admin/promos`
- `/admin/broadcast`

## Public-Beta Assessment

`probable`: The admin console is materially stronger than the inherited paid-beta R05 state because the payment ledger, reconciliation flow, user device context, and payment-order user-card visibility now exist.

`probable`: It is not yet public-beta-ready without local gates plus live admin access verification. The highest operational risk is not fake UI; it is high-blast-radius real actions that need clearer guardrails before a wider beta shift.

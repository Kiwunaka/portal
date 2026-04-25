# R05 Admin Console

Status: researched

## Scope

Primary operator surface: users, subscriptions, payments, keys, promos, nodes, routes, tickets, incidents, SLA, metrics.

Claim labels used below: `confirmed`, `probable`, `unknown`, `needs local run`, `blocked by missing access`.

## Files/docs inspected

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
- `webapp/e2e/admin-gate.spec.ts`
- `portal_bot/api.py` admin route inventory and relevant admin handlers
- `ПРИМЕРЫ ДИЗАЙНА ПРИЛОЖЕНИЯ И ЛК/вебапп/лк админка.png`
- `ПРИМЕРЫ ДИЗАЙНА ПРИЛОЖЕНИЯ И ЛК/вебапп/лк админка 2.png`

Secrets were not read or printed.

## Current state

`confirmed`: Web admin is the primary operator shell. Access is gated by `usePortalSession()` and `user.is_admin` in `webapp/src/app/(dashboard)/admin/layout.tsx`; non-admin and expired-session states render explicit blocked/login cards.

`confirmed`: Implemented admin routes are `/admin`, `/admin/dashboard`, `/admin/users`, `/admin/bonuses`, `/admin/referrals`, `/admin/promos`, `/admin/nodes`, `/admin/network`, `/admin/broadcast`, and `/admin/tickets`.

`confirmed`: The route grouping matches the current canonical IA broadly: Diagnostics, People, Access, Payments, Network, Messaging, Feedback. The implementation is darker and more utility-like than the attached light admin references, but covers the same core operator concept.

`confirmed`: The attached admin refs show richer target coverage for users/subscriptions/devices/payment activity and nodes/routes/tickets/incidents/SLA. They also contain legacy `Premium VPN` copy and must be treated as design reference only, not copy authority.

## Module audit

| Module | State | Evidence | Beta gate meaning |
| --- | --- | --- | --- |
| Dashboard | `confirmed`: real backend read plus static route-map home | `/admin/dashboard` calls `adminSummary`, `adminMetricsStatus`, `adminMetricsTimeseries`, `adminUsers`, `adminTickets`; `/admin` shows category counts from nav constants | Gate on `/admin/dashboard`, not `/admin` home counters |
| Users | `confirmed`: real backend data/write with audit on writes | UI calls `adminUsers`, `adminUserCard`, manual create/extend/block/token, key actions, bulk key actions, message, loyalty grant; backend writes `_audit_admin` for major operations | In scope for paid beta |
| Subscriptions | `probable`: mostly embedded in user/key tooling, no standalone subscription module | user card exposes status, expiry, subscription URL/token, key state, manual extend/block/regenerate; no `/admin/subscriptions` route | Gate user-detail subscription workflows; do not claim a dedicated subscription console |
| Devices | `probable`: diagnostic fields only, no first-class device admin | user rows/card expose `app_install_id`, `app_platform`, `app_last_seen_at`, observer/IP/node evidence; no device list/reset UI outside broad key/reset actions | Missing as a standalone beta operator module |
| Roles | `confirmed`: not implemented as role management | admin access is boolean `is_admin`; no roles route or role CRUD API found | Exclude from beta gates unless role management becomes a requirement |
| Tariffs/plans | `confirmed`: backend CRUD exists; web UI does not expose CRUD | backend has `/api/admin/plans` GET/POST/PATCH/DELETE and `webapp/src/lib/api.ts` wrappers; `/admin/promos` uses shared tariff catalog for key issue selection | Blocker if operators must edit paid plans in web admin |
| Payments | `confirmed`: partial visibility only | dashboard exposes payment callback failure count; public/cabinet payment APIs exist; no admin payment ledger/order/refund page found | Paid beta blocker for operational finance/support |
| Promocodes | `confirmed`: backend CRUD exists; web UI is not wired to it | backend `/api/admin/promos*` and API wrappers exist; `/admin/promos` instead manages activation keys and promo slots | Blocker if promo-code creation/editing is needed during beta |
| Activation keys | `confirmed`: real backend write/read | `/admin/promos` issues keys through `/api/admin/access-keys/issue` and checks keys through `/api/access-keys/status/{key}` | In scope for paid beta |
| Notifications/broadcast | `confirmed`: real backend writes with audit | `/admin/broadcast` sends segment/TG-ID broadcasts and manages live updates/templates; backend audits broadcast/templates/live updates | In scope, but needs local/live dry-run before release use |
| Logs/action journal | `probable`: backend and per-user detail exist, no standalone journal route | backend `/api/admin/audit`; `adminAuditLog()` wrapper; user card includes recent `admin_actions`; no `/admin/audit` route | Missing as standalone operator module |
| Network/routes | `confirmed`: real backend read/write | `/admin/network` loads/saves `network_rollout_config` through admin API | In scope, but JSON-only editor is high-risk |
| Nodes | `confirmed`: real backend data/write with audit | `/admin/nodes` loads health/metrics/traffic/drift and can sync, drain, enable, disable, resync nodes | In scope for beta operations |
| Tickets | `confirmed`: real backend support queue | `/admin/tickets` loads tickets, changes stable statuses, sends replies; backend writes ticket reply/status audit | In scope for support gate |
| Incidents | `confirmed`: not first-class | no `/admin/incidents`; node alerts and dashboard error cards are incident-like but not incident lifecycle | Missing if beta requires incident tracking |
| SLA/support | `probable`: support exists, SLA dashboard does not | ticket queue exists; attached ref has SLA cards, but repo has no SLA route or SLA metrics page | Gate support queue, not SLA claims |
| Metrics/alerts | `confirmed`: real read-only metrics and alert labels | admin summary, metrics status, timeseries, node alert kinds, node traffic, observer fields | In scope as visibility; no alert acknowledge/resolve workflow |

## Fake counters / hardcoded data / pretend success

- `confirmed`: `/admin` home metric strip counts navigation categories/routes, not users, revenue, tickets, or node state. It is a route catalog, not an operational dashboard.
- `confirmed`: `/admin/promos` shows static/shared facts such as `Android + Windows`, free baseline, and hidden transport order from shared config/catalog. These are not live backend health checks.
- `confirmed`: `/admin/promos` uses `getTariffPlans()` from shared frontend data for key issuing options instead of loading `/api/admin/plans`; plan edits in backend will not necessarily be visible here without shared data sync.
- `confirmed`: `/admin/broadcast` and `/admin/referrals` dialogs seed sample values like `launch14`, default news text, and default Telegram links. These are form defaults/placeholders, not backend proof.
- `confirmed`: `webapp/e2e/admin-gate.spec.ts` uses extensive mocked API payloads. The browser test validates UI behavior and routing, not live backend data or production access.
- `confirmed`: Success messages in admin pages are shown after awaited API calls; I did not find a local-only "pretend success" path for destructive or paid actions.
- `needs local run`: Need browser build/e2e to confirm no pages crash from current mojibake text, layout CSS, or API normalization defaults.
- `blocked by missing access`: Need live admin credentials/API access to confirm production data freshness, permission behavior, and write side effects.

## Gaps against beta

- `confirmed`: No dedicated payments/order ledger for paid beta support. Operators can see failure counts but cannot inspect payment attempts, order state, provider callbacks, refunds, or key issuance lineage from one screen.
- `confirmed`: No standalone devices module, despite device/account visibility being part of support expectations.
- `confirmed`: No roles/RBAC management. The beta admin model appears to be single-admin boolean access.
- `confirmed`: Backend plan and promo-code CRUD is present but not exposed in the current admin routes.
- `confirmed`: No first-class incident or SLA console, while the attached target refs include incident/SLA surfaces.
- `confirmed`: Network rollout is editable only as raw JSON. That is real power, but risky for release operators.
- `probable`: `/admin/promos` mixes activation-key issuing, key lookup, public facts, and promo-slot governance under one label; this can confuse paid-support workflows.

## P0 blockers

- `confirmed`: Paid beta needs an admin payment/order ledger or an explicit decision that payment debugging is handled outside web admin. Current web admin cannot inspect individual orders/callbacks.
- `confirmed`: Tariff/plan and promocode backend CRUD is not reachable from web admin, despite wrappers and backend endpoints existing.
- `confirmed`: Device support is not first-class. Operators cannot open a device-centric view or reset/triage devices independent of the user/key panel.
- `needs local run`: Run `npm.cmd run build` and `npm.cmd run test:e2e:admin` before treating this console as release-ready.
- `blocked by missing access`: Production admin session, backend data freshness, and write permissions were not verified.

## P1 beta polish

- Add a payment ledger screen with order ID, user, plan, provider, status, callback status, issued key, timestamps, and failure reason.
- Add web UI for existing `/api/admin/plans` and `/api/admin/promos` endpoints, or explicitly hide those endpoints from beta operator expectations.
- Add a device-focused panel under People or its own route, showing install ID, platform, app version, last seen, route mode when available, recent IP/node evidence, and safe reset/resync actions.
- Add a standalone action journal route backed by `/api/admin/audit`.
- Replace raw JSON-only network rollout editing with structured controls for defaults, carrier/cohort overrides, feeds, and operator-lab allowlists.
- Add incident/SLA read models if the beta support process needs SLA tracking.

## P2 defer

- Full RBAC/roles if single-admin operation is acceptable for beta.
- Design parity with the light reference mockups, as long as current mobile and desktop admin e2e remains usable.
- Rich maps/topology views from the attached refs.
- Alert acknowledge/resolve lifecycle, if node alerts remain operational-only for this wave.

## Technical debt

- `confirmed`: Some admin pages use mixed component systems (`adminPanelClass` plus older `glass-card`, `stat-card`, `outline-btn`) and several strings appear mojibake-encoded in source/output.
- `confirmed`: `/admin/promos` has unused-looking backend wrapper coverage for plan/promocode CRUD elsewhere in `api.ts`, but the page implements a different scope.
- `confirmed`: E2E mocks are strong for UI coverage, but can mask backend contract drift if API-only tests do not cover the same admin routes.
- `probable`: Admin navigation names do not fully map to audited module names, so operator onboarding may be confusing.

## Security/privacy risks

- `confirmed`: Admin user detail includes subscription URL/token. This is useful for recovery but high sensitivity; keep it behind admin gate and avoid broad screenshots/logging.
- `confirmed`: Broadcast can target broad segments or explicit Telegram IDs. It needs a beta dry-run/operator checklist to prevent accidental sends.
- `confirmed`: Raw `network_rollout_config` editing can affect transport, DNS, routing, and operator-lab allowlists. Mistyped JSON or wrong allowlist can change live provisioning.
- `confirmed`: Manual/test deletion is guarded by `isManualTestUserLike` in UI and `safe-delete` semantics in backend; keep this gate.
- `blocked by missing access`: Could not verify production auth headers, session expiry, or whether all write endpoints reject non-admin users in deployed runtime.

## Required implementation WOs

1. `P0`: Payment/order ledger for beta support.
2. `P0`: Web UI for plan CRUD and promocode CRUD, or a documented exclusion from beta gates.
3. `P0`: Device/admin support view tied to app-first install/device context.
4. `P1`: Action journal route backed by `/api/admin/audit`.
5. `P1`: Structured rollout editor to replace or wrap raw JSON.
6. `P1`: Incident/SLA dashboard if support promises use SLA language.

## Validation commands

`needs local run`:

```powershell
cd C:\Users\kiwun\Documents\ai\VPN\webapp
npm.cmd run build
npm.cmd run test:e2e:admin
```

`needs local run` for backend/admin contract focus:

```powershell
cd C:\Users\kiwun\Documents\ai\VPN
python -m pytest tests/test_admin_webapp_smoke.py -q
python -m pytest tests/test_portal_api.py tests/test_api_auth_and_tickets.py -q
```

`blocked by missing access`: production smoke with a real admin session against `https://app.pokrov.space/admin/dashboard/`, `/admin/users/`, `/admin/nodes/`, `/admin/network/`, `/admin/tickets/`, `/admin/promos/`, and `/admin/broadcast/`.

## Evidence links

- `webapp/src/app/(dashboard)/admin/nav.ts`
- `webapp/src/app/(dashboard)/admin/layout.tsx`
- `webapp/src/app/(dashboard)/admin/dashboard/page.tsx`
- `webapp/src/app/(dashboard)/admin/users/page.tsx`
- `webapp/src/app/(dashboard)/admin/promos/page.tsx`
- `webapp/src/app/(dashboard)/admin/nodes/page.tsx`
- `webapp/src/app/(dashboard)/admin/network/page.tsx`
- `webapp/src/app/(dashboard)/admin/broadcast/page.tsx`
- `webapp/src/app/(dashboard)/admin/tickets/page.tsx`
- `webapp/src/lib/api.ts`
- `portal_bot/api.py`
- `webapp/e2e/admin-gate.spec.ts`
- `ПРИМЕРЫ ДИЗАЙНА ПРИЛОЖЕНИЯ И ЛК/вебапп/лк админка.png`
- `ПРИМЕРЫ ДИЗАЙНА ПРИЛОЖЕНИЯ И ЛК/вебапп/лк админка 2.png`

# POKROV AdminApp

Last updated: 2026-07-07

## Purpose

`adminapp/` is the dedicated Next.js operator app for `https://admin.pokrov.space/`.

It owns the new admin surface for:

- ops overview and alert triage
- nodes, capacity, traffic, and time series
- free-tier burn and user caps
- provider/hoster traffic quotas
- users, tickets, payments, promos, referrals, release, broadcast, and funnel parity modules

The old `webapp/src/app/(admin)/admin/` routes stay as a parity fallback until the dedicated panel covers every operator workflow and the regression checklist is green.

## Stack

- Next.js static export
- React 19
- Tailwind CSS 4
- POKROV design tokens from `shared/design-tokens.json`
- TanStack Table for dense operator tables
- Recharts for v1 charts
- lucide-react icons

No Grafana, Beszel, Netdata, VictoriaMetrics, or provider API is required for v1.

## Runtime Contract

Primary host:

- `https://admin.pokrov.space/`

Temporary DNS/SSL alias while Timeweb propagation is being resolved:

- `https://www.admin.pokrov.space/`

API host:

- `https://api.pokrov.space/`

Auth:

- reuses the existing POKROV admin auth model
- first tries the existing browser web session cookie from the cabinet and exchanges it for a short admin bearer session
- accepts Telegram WebApp initData as a manual fallback when the browser session is missing or not admin-authorized
- roles v1: single superadmin

Key v1 endpoints:

- `GET /api/admin/ops/overview`
- `GET /api/admin/free-tier/summary`
- `GET /api/admin/free-tier/users`
- `GET/POST/PATCH/DELETE /api/admin/provider-quotas`
- `GET /api/admin/provider-quotas/status`
- `GET /api/admin/nodes/timeseries`
- `GET /api/admin/traffic/summary`
- `GET /api/admin/alerts`
- `POST /api/admin/alerts/{id}/ack`
- `POST /api/admin/alerts/{id}/silence`

Parity modules reuse existing admin endpoints such as `/api/admin/users`, `/api/admin/tickets`, `/api/admin/payments/orders`, `/api/admin/promos`, `/api/admin/referrals/pending`, `/api/admin/live-updates`, `/api/admin/broadcast`, and `/api/admin/funnel/summary`.

## Local Run

```powershell
npm.cmd install
npm.cmd run dev
```

Default dev URL:

- `http://localhost:3000/`

Use `NEXT_PUBLIC_API_BASE_URL` when testing against a non-production API:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8080"
npm.cmd run dev -- --port 3105
```

## Build

```powershell
npm.cmd run build
npm.cmd run lint
```

Static output is emitted to:

- `adminapp/out`

## Verification

Minimum checks for adminapp work:

```powershell
npm.cmd run build
npm.cmd run lint
python -m pytest tests/test_admin_ops_api.py -q
```

Run the old `webapp` admin E2E only when retained parity routes change:

```powershell
cd ../webapp
npm.cmd run test:e2e:admin
```

## Release Notes

- `scripts/remote_deploy_brain_static_sites.py` validates and deploys `adminapp/out` alongside `marketing/out` and `webapp/out`.
- `scripts/release_gate_check.py` includes `AdminApp production build`.
- Do not delete `webapp` admin routes until a parity checklist confirms every existing operator workflow has moved.

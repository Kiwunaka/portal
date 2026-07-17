# POKROV AdminApp

Last updated: 2026-07-12

## Document Status

Document class: CANONICAL. This file is the local authority for the primary operator surface in `adminapp/`.

## Purpose

`adminapp/` is the dedicated Next.js primary operator app for `https://admin.pokrov.space/`.

It owns the new admin surface for:

- action-first ops overview: critical nodes, stuck payments, provider/free-tier limits, key pressure, and fresh tickets
- global search by Telegram ID, username, display name, install ID, order ID, node code, key/email, or related operator identifier
- users: search, table, user card, access/online first, node/key/IP details only inside the user card, payments, tickets, and action history
- online users: bounded live panel aggregate without raw IPs in the shared list
- nodes: health-first view with panel/dataplane/probe/TLS/freshness/latency/observer/IP/transport/capacity and guarded lifecycle actions
- payments: today/7d/30d revenue, stuck payments, orders, and abandoned buy/checkout counts
- funnel: stage and source breakdown instead of raw JSON dumps
- tickets, alerts, capacity, traffic, free-tier burn, provider/hoster quotas
- free-tier burn and user caps
- provider/hoster traffic quotas
- promos, referrals, release readiness, and broadcast with preview/dry-run before real send

The old `webapp/src/app/(admin)/admin/` routes stay as a parity fallback until the dedicated panel covers every operator workflow and the regression checklist is green.

## Stack

- Next.js static export
- React 19
- Tailwind CSS 4
- POKROV design tokens from `shared/design-tokens.json`
- TanStack Table for dense operator tables
- Recharts for v1 charts
- lucide-react icons

The app intentionally avoids build-time `next/font/google` fetches; production builds use the local/system font stack with the POKROV token fallback.

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
- `GET /api/admin/users`
- `GET /api/admin/users/{tg_id}`
- `GET /api/admin/users/{tg_id}/investigation`
- `GET /api/admin/online/users`
- `GET /api/admin/tickets`
- `GET /api/admin/tickets/{ticket_id}`
- `GET /api/admin/nodes/health`
- `GET /api/admin/nodes/runtime`
- `GET /api/admin/nodes/drift`
- `POST /api/admin/nodes/{node_code}/drain`
- `POST /api/admin/nodes/{node_code}/enable`
- `POST /api/admin/nodes/{node_code}/undrain`
- `POST /api/admin/nodes/{node_code}/disable`
- `POST /api/admin/nodes/{node_code}/resync`
- `GET /api/admin/keys/pressure`
- `GET /api/admin/payments/summary?period=today|7d|30d`
- `GET /api/admin/payments/orders`
- `GET /api/admin/funnel/summary`
- `GET /api/admin/free-tier/summary`
- `GET /api/admin/free-tier/users`
- `GET/POST/PATCH/DELETE /api/admin/provider-quotas`
- `GET /api/admin/provider-quotas/status`
- `GET /api/admin/nodes/timeseries`
- `GET /api/admin/traffic/summary`
- `GET /api/admin/alerts`
- `POST /api/admin/alerts/{id}/ack`
- `POST /api/admin/alerts/{id}/silence`
- `POST /api/admin/broadcast` with `dry_run=true` for preview

Parity modules reuse existing admin endpoints such as `/api/admin/tickets`, `/api/admin/promos`, `/api/admin/referrals/pending`, `/api/admin/live-updates`, and `/api/admin/gift-codes`.

Privacy rule:

- shared online lists must not expose raw IP addresses
- unmatched online rows use an opaque stable row ID; panel email, client UUID, and raw panel errors are not returned
- the base user card omits raw IPs, connection strings, subscription tokens/URLs, panel identifiers, and arbitrary provider metadata
- raw/recent IP details are returned only by the admin-only investigation endpoint and loaded only while the individual user's `Расследование` tab is open
- admin ticket queues and the base admin user card receive only bounded summaries; `GET /api/admin/tickets/{ticket_id}` exposes safe attachment metadata and, when available, a guarded same-origin download path fetched with admin authentication
- authenticated public/client routes under `/api/tickets*` retain their existing support-thread DTO for webapp compatibility; the admin privacy boundary does not redefine that public client contract

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

Browser regression:

```powershell
npm.cmd run test:e2e
```

Static output is emitted to:

- `adminapp/out`

## Verification

Minimum checks for adminapp work:

```powershell
npm.cmd run build
npm.cmd run lint
npm.cmd run test:e2e
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

# Repository Agents

Last updated: 2026-03-29

This file is the working contract for any agent or developer operating inside `C:\Users\kiwun\Documents\ai\VPN`.

Use it to answer four questions before touching code:

1. What is the current source of truth?
2. Which subsystem am I changing?
3. Which docs must be updated in the same task?
4. What is safe to clean up, and what must never be touched?

## Current Facts

- Platform brand: `POKROV`
- Client brand: `POKROV VPN`
- Client strategy: `consumer-first`
- Identity model: `app-first`
- Trial duration: `5 days`
- Telegram reward: `+10 days`
- Default client core: `sing-box`
- Compatibility fallback: `xray` only in advanced settings
- Public channel: `@pokrov_vpn`
- Main bot: `@pokrov_vpnbot`
- Support bot: `@pokrov_supportbot`
- Feedback bot: `@pokrov_feedbackbot`
- Official public surfaces: `https://pokrov.space/`, `https://app.pokrov.space/`, `https://api.pokrov.space/`
- Canonical connect host: `https://connect.pokrov.space/`
- Canonical checkout host: `https://pay.pokrov.space/checkout/`
- Legacy compatibility host: `kiwunaka.space`
- Canonical control-plane host: `82.21.114.104`

## Must-Read Order

Before any substantial change, read these files in order:

1. [Docs Index](C:/Users/kiwun/Documents/ai/VPN/docs/README.md)
2. [Product Overview](C:/Users/kiwun/Documents/ai/VPN/docs/product/portal-vpn-product.md)
3. [System Overview](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/system-overview.md)
4. [App-First And Bonus Flows](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/app-first-and-bonus-flows.md)
5. [Deployment And Access](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md)
6. [Monitoring And Visibility](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)
7. [Developer Guide](C:/Users/kiwun/Documents/ai/VPN/docs/developer/developer-guide.md)
8. [Repository Map](C:/Users/kiwun/Documents/ai/VPN/docs/developer/repository-map.md)

For client work, also read:

- [Client Docs Index](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/README.md)
- [POKROV VPN Product Spec](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/product/portal-vpn-v1-spec.md)
- [App-First Session Flow](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/architecture/app-first-session-flow.md)
- [Publishing And Signing Guide](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md)

## Canonical Docs

Living documentation lives only in these areas:

- `docs/product/`
- `docs/architecture/`
- `docs/operations/`
- `docs/developer/`
- `docs/user/`
- `external/client-fork/app/docs/`

Everything else in `docs/` should be treated as historical, audit, or supporting material unless a canonical doc links to it as current.

If a root-level guide or an older flat doc conflicts with a canonical doc, update the canonical doc and archive or relabel the older one.

## Subsystem Map

### `portal_bot/`

Contains the backend and Telegram control plane:

- `api.py`: public API, app-first session flow, payments, admin API, tickets, bonuses, subscription delivery
- `bot.py`: main Telegram bot
- `helpbot.py`: support bot
- `feedbackbot.py`: feedback intake, moderation, and public review publishing
- `legacy_redirect_bot.py`: legacy bot continuity during username/token cutover
- `worker.py`: retention jobs, channel bonus guard, free-cycle operations
- `web_auth_service.py`: Telegram web login and session token helpers
- `events_service.py`, `pay_attempts_service.py`: funnel telemetry and checkout attempt tracking
- `models.py`, `migrations.py`: schema and migration helpers
- `control_panel.py`, `panel_client.py`: 3x-ui and node synchronization

### `webapp/`

Contains the Next.js user cabinet and web-admin surface.

Current local authority:

- [webapp/README.md](C:/Users/kiwun/Documents/ai/VPN/webapp/README.md)
- `webapp/src/app/(dashboard)/admin/` for admin routes
- `webapp/src/lib/api.ts` for browser auth/API wiring
- `webapp/e2e/` and `webapp/playwright.config.ts` for real browser coverage

### `marketing/`

Contains the public marketing site, checkout entrypoints, and legal pages.

Current local authority:

- `marketing/src/`
- [shared/copy.ts](C:/Users/kiwun/Documents/ai/VPN/shared/copy.ts)
- [copy/catalog.ru.json](C:/Users/kiwun/Documents/ai/VPN/copy/catalog.ru.json)
- [shared/portal-config.ts](C:/Users/kiwun/Documents/ai/VPN/shared/portal-config.ts)

### `shared/`

Contains shared public copy, canonical hostnames, and cross-surface product constants.

Current local authority:

- [shared/copy.ts](C:/Users/kiwun/Documents/ai/VPN/shared/copy.ts)
- [shared/portal-config.ts](C:/Users/kiwun/Documents/ai/VPN/shared/portal-config.ts)

### `infra/`

Contains runtime units and infrastructure assets used by deploy and observability tooling.

Current local authority:

- [infra/portal-node-metrics.service](C:/Users/kiwun/Documents/ai/VPN/infra/portal-node-metrics.service)
- [infra/portal-node-metrics.timer](C:/Users/kiwun/Documents/ai/VPN/infra/portal-node-metrics.timer)
- [docs/operations/deployment-and-access.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md)
- [docs/operations/monitoring-and-visibility.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)

### `scripts/`

Contains deploy, smoke, audit, migration, node, and release orchestration scripts.

Start from:

- [Repository Map](C:/Users/kiwun/Documents/ai/VPN/docs/developer/repository-map.md)
- [Deployment And Access](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md)

### `external/client-fork/app/`

Contains the consumer Flutter client fork for `Android` and `Windows`.

Current local authority:

- [Client Docs Index](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/README.md)

## Change-Impact Matrix

When behavior changes, update the matching canonical docs in the same task.

| Change area | Required docs |
| --- | --- |
| Product positioning, trial rules, pricing-facing behavior, branding | `docs/product/portal-vpn-product.md` |
| Backend architecture, API responsibilities, runtime components | `docs/architecture/system-overview.md` |
| App-first session flow, Telegram linking, Telegram reward, support flow | `docs/architecture/app-first-and-bonus-flows.md` |
| Deploy flow, server access, release procedures, secret locations | `docs/operations/deployment-and-access.md` |
| Hostname policy, metrics freshness, node alerts, probe visibility, operator telemetry | `docs/operations/monitoring-and-visibility.md` |
| Repository workflow, tests, local commands, script usage, cleanup policy | `docs/developer/developer-guide.md`, `docs/developer/repository-map.md` |
| User-facing onboarding, support, trial, Telegram bonus, renewal | `docs/user/portal-vpn-user-guide-ru.md` |
| Client UX, client contracts, client roadmap | `external/client-fork/app/docs/*` |

## Fast Paths

### Backend task

1. Read the must-read set.
2. Inspect `portal_bot/api.py`, `portal_bot/worker.py`, and any touched services/repos.
3. Run focused backend tests.
4. Update canonical docs for any contract or flow changes.

### Web/Admin task

1. Read the must-read set plus `webapp/README.md`.
2. Inspect `webapp/src/app/(dashboard)/admin/`, `webapp/src/lib/api.ts`, and `portal_bot/api.py`.
3. Run `npm.cmd run build` inside `webapp/`.
4. Run `npm.cmd run test:e2e:admin` when browser-visible admin flows or auth gates change.
5. Keep web admin as the primary operator surface; Telegram admin is fallback-only.

### Marketing task

1. Read the must-read set plus product docs.
2. Inspect `marketing/src/`, `shared/copy.ts`, `copy/catalog.ru.json`, and `shared/portal-config.ts`.
3. Keep new public copy and CTA changes centralized in shared/catalog sources.

### Observability / Capacity task

1. Read `deployment-and-access.md` and `monitoring-and-visibility.md`.
2. Inspect `scripts/collect_node_metrics.py`, `infra/portal-node-metrics.service`, and `infra/portal-node-metrics.timer`.
3. Verify `/api/admin/metrics/status` freshness, per-node alerts, and probe-failure fields.
4. Treat hoster CPU warnings as capacity incidents requiring node and control-plane telemetry review.

### Client task

1. Read the must-read set plus the client docs.
2. Inspect `external/client-fork/app/lib/` and packaging assets as needed.
3. Run targeted Flutter tests or build-smoke commands.
4. Sync both client docs and root canonical docs if contracts changed.

### Docs-only task

1. Update canonical docs first.
2. Archive or relabel stale duplicates.
3. Run link/doc consistency checks.

### Release task

Default definition of done:

- code or config change
- relevant tests or smoke checks
- push
- deploy

If deploy is blocked, document:

- what changed
- what was verified
- what remains blocked
- rollback-safe state

## Source Of Truth Rules

Production source of truth:

- Postgres from `DATABASE_URL`
- shared hostnames and public copy from `shared/portal-config.ts` and `shared/copy.ts`

Not source of truth:

- local SQLite files
- local temp DBs
- archived audit snapshots
- `.next/`, `.dart_tool/`, `node_modules/`, test caches
- old root guides moved into `docs/archive/`

3x-ui is an execution layer, not the product authority.

## Safe Cleanup Matrix

| Safe to remove | Notes |
| --- | --- |
| `__pycache__/` | Generated Python cache |
| `.pytest_cache/` | Generated pytest cache |
| `portal_api_test_*.db` | Temporary local test DBs |
| `.next/` | Next.js build cache |
| `test-results/` | Generated test artifacts |
| `*.tsbuildinfo` | TypeScript incremental cache |
| local `node_modules/`, `.dart_tool/`, `build/`, `dist/` | Only when clearly local-generated and not retained release output |
| `webapp/out`, `marketing/out` | Generated static export outputs; safe to rebuild, must not be committed |

## Never-Touch Zones

Do not delete, print into markdown, or commit secret material from:

- `portal_bot/.env`
- `VPN NODE SSH KEYS/`
- `secrets for merchant/`
- `ops-local/`
- `external/client-fork/app/windows/`

Do not remove release artifacts from client `out/` unless you know they are obsolete.

Do not treat archived evidence under `docs/audit-artifacts/` as disposable by default.

## Current Telegram Registry

- Main bot: `@pokrov_vpnbot`
- Support bot: `@pokrov_supportbot`
- Feedback bot: `@pokrov_feedbackbot`
- Public channel: `@pokrov_vpn`
- Verified channel URL: `https://t.me/pokrov_vpn/10`

The Telegram bonus flow is live. The bot is an administrator in the configured public channel.

## Reporting Format

For substantial tasks, leave a short handoff with:

- `What I checked`
- `What I found`
- `What I changed`
- `How I verified`
- `What remains / risk`

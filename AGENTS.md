# Repository Agents

Last updated: 2026-04-22

This file is the working contract for any agent or developer operating inside `C:\Users\kiwun\Documents\ai\VPN`.

Use it to answer four questions before touching code:

1. What is the current source of truth?
2. Which subsystem am I changing?
3. Which docs must be updated in the same task?
4. What is safe to clean up, and what must never be touched?

## Current Facts

- Platform brand: `POKROV`
- Public product line: `POKROV`
- Legacy client identifier: `POKROV VPN` only where removal is not yet feasible
- Public wording rule: do not use `VPN` as a direct public product description; keep it only in legacy names, compatibility labels, and unavoidable technical identifiers
- Client strategy: `consumer-first`
- Identity model: `app-first`
- Trial duration: `5 days`
- Telegram reward: `+10 days`
- Default client core: `sing-box`
- Compatibility fallback: `xray` only in advanced settings
- Username sync: `automatic` primary path; manual sync is compatibility/recovery only
- Premium access node pool: all enabled non-free nodes
- Free access node pool: dedicated `NL-free` node only
- Public channel: `@pokrov_vpn`
- Main bot: `@pokrov_vpnbot`
- Support bot: `@pokrov_supportbot`
- Feedback bot: `@pokrov_feedbackbot`
- Official public surfaces: `https://pokrov.space/`, `https://app.pokrov.space/`, `https://api.pokrov.space/`
- Canonical connect host: `https://connect.pokrov.space/`
- Canonical checkout host: `https://pay.pokrov.space/checkout/`
- Legacy compatibility host: `kiwunaka.space`
- Canonical control-plane host: `82.21.114.104`
- Android public release is blocked until the repo/static gate pack is green and a physical-device release-build localhost/control-surface audit proves the client is safe
- RU-origin probe readiness is an operational dependency, not a guaranteed property of `mini`

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

- [POKROV App Docs Index](C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md)
- [POKROV App Cutover Readiness](C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md)
- [App-Next Docs Index](C:/Users/kiwun/Documents/ai/VPN/app-next/docs/README.md)
- [App-Next Cutover Readiness](C:/Users/kiwun/Documents/ai/VPN/app-next/docs/operations/cutover-readiness.md)
- [Legacy Bridge Client Docs Index](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/README.md)
- [Legacy Bridge Client Product Spec (legacy path)](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/product/portal-vpn-v1-spec.md)
- [Legacy Bridge App-First Session Flow](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/architecture/app-first-session-flow.md)
- [Publishing And Signing Guide](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md)

## Operator Access

Shell guidance:

- prefer `bash` when it is the simpler and clearer path
- explicitly fall back to `powershell` when quoting, SSH, Windows paths, or local tooling reliability is better
- do not treat one shell as mandatory if the other is safer for the exact task

## Canonical Docs

Legacy filename note:

- some canonical docs still use legacy path names such as `portal-vpn-product.md`, `portal-vpn-user-guide-ru.md`, and `portal-vpn-v1-spec.md`
- these files are still the live source of truth for the current `POKROV` product until a separate rename wave happens
- legacy `POKROV VPN` labels inside paths or old identifiers do not authorize new direct-meaning `VPN` copy
- treat the content as current even when the path still contains an older name

Living documentation lives only in these areas:

- `docs/product/`
- `docs/architecture/`
- `docs/operations/`
- `docs/developer/`
- `docs/user/`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/` as the live client-doc lane for the bootstrapped new client repo
- `app-next/docs/` as retained bootstrap-source and transition/reference material inside the platform repo
- `external/client-fork/app/docs/` only for legacy bridge/hotfix and current release-truth notes until formal cutover

Everything else in `docs/` should be treated as historical, audit, or supporting material unless a canonical doc links to it as current.

If a root-level guide or an older flat doc conflicts with a canonical doc, update the canonical doc and archive or relabel the older one.

## Subsystem Map

### `portal_bot/`

Contains the backend and Telegram control plane:

- `api.py`: public API, app-first session flow, automatic username sync, payments, admin API, tickets, bonuses, subscription delivery
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
- [shared/product-facts.json](C:/Users/kiwun/Documents/ai/VPN/shared/product-facts.json)
- [shared/public-urls.json](C:/Users/kiwun/Documents/ai/VPN/shared/public-urls.json)

### `shared/`

Contains shared public copy, canonical hostnames, and cross-surface product constants.

Current local authority:

- [shared/copy.ts](C:/Users/kiwun/Documents/ai/VPN/shared/copy.ts)
- [shared/portal-config.ts](C:/Users/kiwun/Documents/ai/VPN/shared/portal-config.ts)
- [shared/product-facts.json](C:/Users/kiwun/Documents/ai/VPN/shared/product-facts.json)
- [shared/public-urls.json](C:/Users/kiwun/Documents/ai/VPN/shared/public-urls.json)
- [shared/design-tokens.json](C:/Users/kiwun/Documents/ai/VPN/shared/design-tokens.json)

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

### `C:/Users/kiwun/Documents/ai/POKROV-app`

Contains the new canonical client repository target for `Android` and `Windows`.

Workspace lane note:

- `POKROV-app/main` is the new client development truth for this rework program
- expected local checkout path after bootstrap: `C:/Users/kiwun/Documents/ai/POKROV-app`
- that checkout is now bootstrapped locally from `C:/Users/kiwun/Documents/ai/VPN/app-next/`
- new client product-direction work must now land here instead of treating `app-next/` or the legacy fork as parallel canon

### `app-next/`

Contains the retained in-repo bootstrap source workspace for the new client lane.

Workspace lane note:

- `app-next/` feeds the initial snapshot into `POKROV-app/main`
- treat it as transition/reference and migration material, not as a permanent parallel canon
- the initial bootstrap snapshot has already landed in `POKROV-app`, so keep `app-next/` only as transition/reference material unless a later policy explicitly reopens it

Current local authority:

- [App-Next Docs Index](C:/Users/kiwun/Documents/ai/VPN/app-next/docs/README.md)
- [Cutover Readiness](C:/Users/kiwun/Documents/ai/VPN/app-next/docs/operations/cutover-readiness.md)

### `external/client-fork/app/`

Contains the consumer Flutter client fork for `Android` and `Windows`.

Workspace lane note:

- `external/client-fork/app/` is the retained legacy bridge/hotfix lane and the current public Android and Windows release-build/signing truth until formal cutover
- do not start new product-direction work here when that work belongs to the new client lane
- after formal cutover, this workspace becomes compatibility-only reference plus emergency rollback material

Current local authority:

- [Legacy Bridge Client Docs Index](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/README.md)

## Change-Impact Matrix

When behavior changes, update the matching canonical docs in the same task.

| Change area | Required docs |
| --- | --- |
| Product positioning, trial rules, pricing-facing behavior, branding | `docs/product/portal-vpn-product.md` |
| Backend architecture, API responsibilities, runtime components | `docs/architecture/system-overview.md` |
| App-first session flow, Telegram linking, username sync primary path, node-pool assignment, Telegram reward, support flow | `docs/architecture/app-first-and-bonus-flows.md` |
| Deploy flow, server access, release procedures, secret locations | `docs/operations/deployment-and-access.md` |
| Hostname policy, metrics freshness, node alerts, probe visibility, operator telemetry | `docs/operations/monitoring-and-visibility.md` |
| Repository workflow, tests, local commands, script usage, cleanup policy | `docs/developer/developer-guide.md`, `docs/developer/repository-map.md` |
| User-facing onboarding, support, trial, Telegram bonus, renewal | `docs/user/portal-vpn-user-guide-ru.md` |
| Client UX, client contracts, client roadmap | `C:/Users/kiwun/Documents/ai/POKROV-app/docs/*` for the new client lane, plus `external/client-fork/app/docs/*` when legacy bridge or release-truth behavior changes |

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
2. Inspect `marketing/src/`, `shared/copy.ts`, `copy/catalog.ru.json`, `shared/portal-config.ts`, `shared/product-facts.json`, and `shared/public-urls.json`.
3. Keep new public copy and CTA changes centralized in shared/catalog sources.

### Observability / Capacity task

1. Read `deployment-and-access.md` and `monitoring-and-visibility.md`.
2. Inspect `scripts/collect_node_metrics.py`, `infra/portal-node-metrics.service`, and `infra/portal-node-metrics.timer`.
3. Verify `/api/admin/metrics/status` freshness, per-node alerts, and probe-failure fields.
4. Treat hoster CPU warnings as capacity incidents requiring node and control-plane telemetry review.
5. Treat RU probe readiness itself as a tracked dependency. `mini` may be unavailable and must not be assumed as a guaranteed origin.

### Client task

1. Read the must-read set plus the client docs.
2. Inspect `C:/Users/kiwun/Documents/ai/POKROV-app/` for new client work; inspect `app-next/` only when transition/reference context matters, and inspect `external/client-fork/app/` only when the task is bridge, hotfix, compatibility, or release-truth work.
3. Run targeted Flutter tests or build-smoke commands in the lane that actually changed.
4. Treat Android release-build localhost/control-surface verification as a release gate, not an optional audit.
5. Sync root canonical docs plus the correct client-doc lane: `POKROV-app/docs/*` for new client truth once bootstrapped, `external/client-fork/app/docs/*` when bridge release truth changed.

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

For node-access diagnostics and release handoffs, explicitly distinguish:

- `current-origin check`: from the operator workstation currently in use
- `brain-origin check`: from the control-plane host `82.21.114.104`
- `RU-origin check`: from `mini` or a replacement external RU probe host

## Branch, Worktree, And Promotion Rules

- Keep the root workspace `C:\Users\kiwun\Documents\ai\VPN` on local `master` as the prospective clean baseline for root-repo work
- Treat that root `master` baseline as the place you can resync from; do not turn it into a long-lived scratch branch
- `portal/master` is the policy label for the promoted platform line and normally maps to real `origin/master`
- `POKROV-app/main` is the policy label for the new client development line and should map to the real `main` branch in the dedicated `POKROV-app` repository
- `external/client-fork/app` stays on its current `main` line as the bridge/hotfix lane and current public Android+Windows release/build/signing truth until formal cutover
- Do not assume a literal remote alias must exist locally for a policy label to apply
- Local branch or worktree names such as `main`, `portal-app`, and `app-next` are optional machine-local aliases only
- If a local alias disagrees with the promotion target, the promotion target wins
- Root-repo changes under `backend`, `webapp`, `marketing`, `shared`, `infra`, `scripts`, and root `docs` promote through the root repo `master` line
- New client product-direction changes promote through `POKROV-app/main`
- Bridge hotfix, compatibility, packaging, and release-runbook changes promote through `external/client-fork/app` on its existing `main` line until formal cutover
- `app-next/` is the retained bootstrap-source workspace for `POKROV-app/main`, not the long-term promotion target now that the bootstrap snapshot has landed
- When work needs isolation, create or use a dedicated feature branch or sibling worktree instead of reinterpreting baseline or alias branches as source of truth

## Source Of Truth Rules

Production source of truth:

- Postgres from `DATABASE_URL`
- shared hostnames, public copy, and locked cross-surface facts from `shared/portal-config.ts`, `shared/copy.ts`, `shared/product-facts.json`, `shared/public-urls.json`, and `shared/design-tokens.json`

Repository source-of-truth rule:

- if you work on `backend`, `webapp`, `marketing`, root `docs`, `shared`, `infra`, or `scripts`, the canonical git truth is `portal/master`, which is the policy label for the promoted root-repo line and normally maps to real `origin/master`
- if you work on new `Android` or `Windows` client direction, the canonical git truth is `POKROV-app/main`, with expected checkout path `C:/Users/kiwun/Documents/ai/POKROV-app`
- if you work on `external/client-fork/app/`, treat that repository as bridge/hotfix and current release-truth only; do not silently use it as the future client canon
- root docs in this repository, including `AGENTS.md` and `docs/*`, must land on `portal/master`
- new client docs land on `POKROV-app/docs/*`; keep `app-next/docs/*` only as retained bootstrap-source material and keep legacy bridge docs under `external/client-fork/app/docs/*` explicitly labeled as bridge truth
- keep the root workspace on local `master` as the clean baseline prospectively; treat `main`, `portal-app`, and `app-next` as optional local aliases rather than promotion truth
- do not treat local feature branches, old redirect remotes, or the nested legacy client workspace as competing product truths once `portal/master` and `POKROV-app/main` are updated
- if a task spans the platform repo, the new client repo, and the legacy bridge lane, update and report each affected repo explicitly instead of assuming one repo transitively updates the others

Not source of truth:

- local SQLite files
- local temp DBs
- archived audit snapshots
- `.next/`, `.dart_tool/`, `node_modules/`, test caches
- `.tmp/`, `.tmp-*`, and other repo-local scratch directories
- old root guides moved into `docs/archive/`

Formal retained evidence:

- `ops-local/` local operator evidence, handoff state, and sensitive operational material that must be retained unless a deliberate evidence-management task says otherwise
- `docs/audit-artifacts/` archived audit evidence that must be retained unless a deliberate archival policy says otherwise

Out-of-repo scope:

- machine-local Android and adb noise such as `C:\Windows\adb.exe`, `%TEMP%`, Android SDK directories, and `~/.android`
- do not treat machine-global tooling state as repo cleanup unless the task explicitly targets machine maintenance

Routine cleanup rule:

- default cleanup should target repo-local generated caches, exported static builds, test artifacts, temporary DBs, and disposable scratch such as `.tmp/` and `.tmp-*`
- do not delete `.venv/` or active dependency trees as part of normal cleanup unless you intentionally want a full workspace reset

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
| `.tmp/`, `.tmp-*` | Repo-local disposable scratch; safe to drop when not intentionally in use |
| local `node_modules/`, `.dart_tool/`, `build/`, `dist/` | Remove only during an intentional workspace reset, not as routine cleanup |
| `webapp/out`, `marketing/out` | Generated static export outputs; safe to rebuild, must not be committed |

## Never-Touch Zones

Do not delete, print into markdown, or commit secret material from:

- `portal_bot/.env`
- `VPN NODE SSH KEYS/`
- `secrets for merchant/`
- `external/client-fork/app/windows/`

Do not remove release artifacts from client `out/` unless you know they are obsolete.

Retained evidence and out-of-scope reminder:

- do not treat `ops-local/` as disposable scratch; it is retained local evidence and may also contain sensitive operational material
- do not treat archived evidence under `docs/audit-artifacts/` as disposable by default
- do not sweep machine-global Android or adb state such as `C:\Windows\adb.exe`, `%TEMP%`, SDK directories, or `~/.android` as part of repo cleanup

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

For node-access diagnostics, also include:

- `current-origin check`
- `brain-origin check`
- `RU-origin check`

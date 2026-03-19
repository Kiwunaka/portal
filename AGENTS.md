# Repository Agents

Last updated: 2026-03-19

This file is the operational knowledge contract for any agent working inside `C:\Users\kiwun\Documents\ai\VPN`.

## Must-Read Order

Before changing anything substantial, read these files in order:

1. [Docs Index](C:/Users/kiwun/Documents/ai/VPN/docs/README.md)
2. [Product Overview](C:/Users/kiwun/Documents/ai/VPN/docs/product/portal-vpn-product.md)
3. [System Architecture](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/system-overview.md)
4. [App-First And Bonus Flows](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/app-first-and-bonus-flows.md)
5. [Deployment And Access](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md)
6. [Developer Guide](C:/Users/kiwun/Documents/ai/VPN/docs/developer/developer-guide.md)

For client work, additionally read:

- [Client Fork Docs Index](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/README.md)
- [PORTAL VPN Product Spec](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/product/portal-vpn-v1-spec.md)
- [App-First Session Flow](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/architecture/app-first-session-flow.md)

## Canonical Product Rules

- Brand name: `PORTAL` for platform and `PORTAL VPN` for the client app.
- Client UX direction: `consumer-first`.
- Client account model: `app-first`.
- Telegram is optional for first launch and normal usage.
- Free trial duration: `5 days`.
- Telegram reward duration: `+10 days`.
- Default client runtime core: `sing-box`.
- `xray` is advanced compatibility fallback only.
- The app must provision a real working subscription after `Try free`.
- Do not restore the old "import key first" UX as the primary journey.

## Architecture Snapshot

Main platform components:

- `portal_bot/api.py`: FastAPI backend, public API, admin API, checkout, subscription delivery.
- `portal_bot/bot.py`: main Telegram bot.
- `portal_bot/helpbot.py`: support bot.
- `portal_bot/worker.py`: jobs, retention, channel bonus guard, free-cycle operations.
- `portal_bot/models.py`, `portal_bot/migrations.py`: data model and schema evolution.
- `portal_bot/control_panel.py`, `portal_bot/panel_client.py`: 3x-ui and node synchronization layer.
- `webapp/`: user cabinet and web-admin.
- `marketing/`: public site and legal pages.
- `external/client-fork/app/`: consumer VPN client fork for Windows and Android.

Production source of truth:

- Postgres from `DATABASE_URL`

Not source of truth:

- local SQLite files
- local temporary DBs
- local archived audit snapshots

## Telegram Registry

Canonical bots:

- main bot: `@portal_service_bot`
- support bot: `@portal_privacy_helpbot`
- feedback bot: `@portalfeedbackbot`

Important current issue:

- channel bonus verification is code-fixed, but the actual public channel username is still not resolved in production
- both `portal_privacy` and `portal_news_channel` currently resolve as Telegram contacts, not channels
- do not assume channel bonus flow is fully live until a valid channel username is provided and the bot is added there

## Secrets, Access, And Deploy Materials

Keep these locations intact:

- `portal_bot/.env`
- `VPN NODE SSH KEYS/`
- `secrets for merchant/`
- `ops-local/`
- `external/client-fork/app/windows/`

Canonical control-plane host:

- `82.21.114.104`

Rules:

- never paste raw tokens, passwords, or private keys into markdown
- never commit secrets
- document locations and usage, not values

## Documentation Maintenance Rules

Whenever you change behavior, update the matching docs in the same task.

Minimum mapping:

- product behavior -> `docs/product/portal-vpn-product.md`
- backend or runtime architecture -> `docs/architecture/system-overview.md`
- app-first or Telegram reward logic -> `docs/architecture/app-first-and-bonus-flows.md`
- deploy, server access, release procedures -> `docs/operations/deployment-and-access.md`
- developer workflow, test and build commands -> `docs/developer/developer-guide.md`
- user-facing behavior or support flow -> `docs/user/portal-vpn-user-guide-ru.md`
- client-specific UX or contracts -> `external/client-fork/app/docs/*`

If older flat docs conflict with the canonical docs above, treat the canonical docs as correct and mark older notes as historical.

## Release Rules

For release work, default completion includes:

- code change
- tests or smoke checks
- push
- deploy

If deploy is blocked, document:

- what was changed
- what was verified
- what remains blocked
- rollback-safe state

## Cleanup Rules

Safe to remove:

- `__pycache__/`
- `.pytest_cache/`
- frontend build caches like `.next/`, `test-results/`, `tsconfig.tsbuildinfo`
- temporary test DBs such as `portal_api_test_*.db`

Do not remove without explicit reason:

- secrets
- signing materials
- local access packs
- archived evidence needed for operations
- client release artifacts in `out/` if they are still needed

## Reporting Format

For substantial tasks, leave a short handoff with:

- `What I checked`
- `What I found`
- `What I changed`
- `How I verified`
- `What remains / risk`

# PORTAL Platform Workspace

Last updated: 2026-03-19

This repository is the main workspace for the `PORTAL` backend, bot layer, WebApp, marketing site, operational scripts, and project documentation.

The consumer client application lives in a separate repository workspace under [external/client-fork/app](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app), but this repository remains the source of truth for backend contracts, deploy flow, and platform architecture.

## What Lives Here

- `portal_bot/`  
  FastAPI backend, main Telegram bot, support bot, worker jobs, data model, panel integration.
- `webapp/`  
  User cabinet and web-admin frontend.
- `marketing/`  
  Public website and legal pages.
- `scripts/`  
  Deploy, smoke, migration, ops, and release tooling.
- `infra/`  
  Service and timer units, runtime infra assets.
- `docs/`  
  Current source-of-truth docs and historical notes.
- `external/client-fork/app/`  
  `PORTAL VPN` Android/Windows client fork.

## Source Of Truth Docs

Start here:

- [Docs Index](C:/Users/kiwun/Documents/ai/VPN/docs/README.md)
- [Product Overview](C:/Users/kiwun/Documents/ai/VPN/docs/product/portal-vpn-product.md)
- [System Architecture](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/system-overview.md)
- [App-First And Bonus Flows](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/app-first-and-bonus-flows.md)
- [Deployment And Access](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md)
- [Developer Guide](C:/Users/kiwun/Documents/ai/VPN/docs/developer/developer-guide.md)
- [User Guide (RU)](C:/Users/kiwun/Documents/ai/VPN/docs/user/portal-vpn-user-guide-ru.md)

## Current Product Direction

- Final product name: `PORTAL VPN`
- Platforms in current client scope: `Android`, `Windows`
- UX strategy: `consumer-first`
- Identity strategy: `app-first`
- Free trial: `5 days`
- Telegram bonus: `+10 days`
- Default client core: `sing-box`
- `xray` remains advanced fallback only

## Secrets And Access

Secrets are intentionally not duplicated in markdown.

Canonical local locations:

- runtime env: `portal_bot/.env`
- node/server access materials: `VPN NODE SSH KEYS/`
- payment and merchant materials: `secrets for merchant/`
- local ops snapshots: `ops-local/`
- Windows signing materials for client fork: `external/client-fork/app/windows/`

Canonical control-plane host:

- `brain`: `82.21.114.104`

## Safety Rules

- Do not copy raw tokens, passwords, or private keys into docs or commits.
- Do not treat local SQLite files as production source of truth.
- Production user, node, and subscription state lives in Postgres from `DATABASE_URL`.
- Keep docs current whenever contracts, flows, deploy scripts, or operator actions change.

## Fast Start For Operators

1. Read [Deployment And Access](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md).
2. Read [System Architecture](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/system-overview.md).
3. For client-facing app work, also read [Client Fork Docs](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/README.md).


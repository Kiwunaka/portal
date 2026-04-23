# POKROV Workspace

Last updated: 2026-04-23

This repository is the main workspace for the `POKROV` platform:

- `portal_bot/` backend, Telegram bots, worker jobs, node sync
- `webapp/` user cabinet and web-admin
- `marketing/` public site and legal pages
- `scripts/` deploy, smoke, migration, and ops tooling
- `docs/` canonical platform documentation
- dedicated client repo: `C:/Users/kiwun/Documents/ai/POKROV-app`

Client lane note:

- `C:/Users/kiwun/Documents/ai/POKROV-app` is the only active client development canon
- `app-next/` in this workspace is retired local alias/bootstrap residue, not a real repo
- legacy bridge material under `external/client-fork/app/` is retained only as historical rollback/evidence until cleanup completes; it is not active workflow truth

## Start Here

- Agent or contributor: [AGENTS.md](C:/Users/kiwun/Documents/ai/VPN/AGENTS.md)
- Documentation index: [docs/README.md](C:/Users/kiwun/Documents/ai/VPN/docs/README.md)
- Product overview: [docs/product/portal-vpn-product.md](C:/Users/kiwun/Documents/ai/VPN/docs/product/portal-vpn-product.md)
- Deployment and access: [docs/operations/deployment-and-access.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md)
- Developer workflow: [docs/developer/developer-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/developer-guide.md)
- User guide: [docs/user/portal-vpn-user-guide-ru.md](C:/Users/kiwun/Documents/ai/VPN/docs/user/portal-vpn-user-guide-ru.md)
- Client docs: [POKROV-app/docs/README.md](C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md)

## Current Product Facts

- Brand: `POKROV`
- Legacy client identifier: `POKROV VPN` only where compatibility or store history still requires it
- Client strategy: `consumer-first`
- Identity strategy: `app-first`
- Trial: `5 days`
- Telegram reward: `+10 days`
- Default client core: `sing-box`
- Main bot: `@pokrov_vpnbot`
- Support bot: `@pokrov_supportbot`
- Feedback bot: `@pokrov_feedbackbot`
- Public channel: `@pokrov_vpn`
- `swazist_bot` and `portal_service_bot` are officially disabled legacy usernames
- Control-plane host: `82.21.114.104`

## Safety

- Never commit secrets or private keys.
- Production truth lives in Postgres from `DATABASE_URL`.
- Root-level historical guides were moved under `docs/archive/`, and dated flat notes now live under `docs/archive/flat-docs/`; use the canonical docs above instead.
- Retained operational evidence stays in `docs/audit-artifacts/` and `ops-local/`.

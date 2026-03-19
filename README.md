# PORTAL Workspace

Last updated: 2026-03-20

This repository is the main workspace for the `PORTAL` platform:

- `portal_bot/` backend, Telegram bots, worker jobs, node sync
- `webapp/` user cabinet and web-admin
- `marketing/` public site and legal pages
- `scripts/` deploy, smoke, migration, and ops tooling
- `docs/` canonical platform documentation
- `external/client-fork/app/` `PORTAL VPN` Flutter client fork

## Start Here

- Agent or contributor: [AGENTS.md](C:/Users/kiwun/Documents/ai/VPN/AGENTS.md)
- Documentation index: [docs/README.md](C:/Users/kiwun/Documents/ai/VPN/docs/README.md)
- Product overview: [docs/product/portal-vpn-product.md](C:/Users/kiwun/Documents/ai/VPN/docs/product/portal-vpn-product.md)
- Deployment and access: [docs/operations/deployment-and-access.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md)
- Developer workflow: [docs/developer/developer-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/developer-guide.md)
- User guide: [docs/user/portal-vpn-user-guide-ru.md](C:/Users/kiwun/Documents/ai/VPN/docs/user/portal-vpn-user-guide-ru.md)
- Client docs: [external/client-fork/app/docs/README.md](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/README.md)

## Current Product Facts

- Brand: `PORTAL` / `PORTAL VPN`
- Client strategy: `consumer-first`
- Identity strategy: `app-first`
- Trial: `5 days`
- Telegram reward: `+10 days`
- Default client core: `sing-box`
- Public channel: `@pokrov_vpn`
- Control-plane host: `82.21.114.104`

## Safety

- Never commit secrets or private keys.
- Production truth lives in Postgres from `DATABASE_URL`.
- Root-level historical guides were moved under `docs/archive/`; use the canonical docs above instead.

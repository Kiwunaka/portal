# Overview

This project is a Telegram-first "Portal" service:
- Telegram bot handles onboarding, plans, and admin actions.
- Telegram WebApp provides a user-friendly account page (LK).
- A subscription endpoint returns multi-location configuration, so users can switch countries in their client app.

## Components

- `portal_bot/bot.py` - aiogram bot, SQLite storage.
- `portal_bot/api.py` - FastAPI (WebApp + subscription endpoint).
- `webapp/` - Telegram WebApp frontend.
- `infra/` - node bootstrap scripts and templates.
- `scripts/` - operational scripts (add node, migrate users to nodes).

## Docs

- `docs/02-ops-control-plane.md`
- `docs/03-ops-node.md`
- `docs/04-migration.md`
- `docs/05-bot-admin.md`
- `docs/06-user-guide.md`
- `docs/07-payments-research.md` (production decision note for FreeKassa)
- `docs/08-node-inventory.md`

## High-Level Flow

```mermaid
flowchart LR
  U[User in Telegram] -->|Stars payment| B[Bot]
  B --> DB[(portal.db)]
  B -->|ensure client| P1[3x-ui panel node A]
  B -->|ensure client| P2[3x-ui panel node B]
  B -->|ensure client| P3[3x-ui panel node C]
  U -->|open LK| W[WebApp]
  W -->|/api/user/{tg_id}| API[FastAPI]
  U -->|subscription URL| SUB[/s8Kx2mP7qR4wT/{sub_token}/]
  SUB --> API
  API --> DB
  API -->|returns| CFG[Multi-location config]
```

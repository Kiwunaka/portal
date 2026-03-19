# PORTAL System Overview

Last updated: 2026-03-20

## Document Status

This file is living source of truth for the platform architecture map.

## Purpose

`PORTAL` is a platform composed of:

- a Python backend and Telegram control plane
- a user cabinet and admin web surface
- a marketing and legal site
- a Flutter client fork for `PORTAL VPN`
- operational scripts for deployment, node management, and release flow

## Main Components

### Control Plane

- `portal_bot/api.py`
  FastAPI backend for health checks, app-first session bootstrap, payments, bonuses, tickets, public data, and admin APIs.
- `portal_bot/bot.py`
  Main Telegram bot for billing, campaigns, referrals, and operator actions.
- `portal_bot/helpbot.py`
  Dedicated support bot.
- `portal_bot/worker.py`
  Background jobs for retention, bonus enforcement, and free-cycle operations.
- `portal_bot/models.py`
  SQLAlchemy model layer.
- `portal_bot/migrations.py`
  Additive schema migration helpers.

### Delivery Plane

- `portal_bot/control_panel.py`
- `portal_bot/panel_client.py`
- node inventory and routing logic
- 3x-ui panels as node-local execution layer

Node lifecycle rule:

- `PORTAL` database decides assignment and lifecycle
- 3x-ui executes the resulting config
- node retirement sequence is `drain -> resync -> disable`

### User Interfaces

- `webapp/`
  user cabinet and web-admin
- `marketing/`
  public website, legal pages, and public conversion flows
- `external/client-fork/app/`
  `PORTAL VPN` consumer client for Android and Windows

### Operational Tooling

- `scripts/`
  deploy, smoke, release, node, audit, and migration tooling
- `infra/`
  runtime units and infrastructure assets

## Data Source Of Truth

Production source of truth:

- Postgres from `DATABASE_URL`

Not source of truth:

- local SQLite files
- archived test DBs
- audit snapshots
- generated frontend caches
- stale root markdown notes

## Current Primary Flows

### App-First Client Flow

1. client generates `install_id`
2. user taps `Try free`
3. backend creates app account, device record, and app session
4. backend returns a real subscription source
5. client imports and activates the profile

### Telegram Linking And Reward Flow

1. app-first account requests Telegram linking
2. backend issues a deep link to `@portal_service_bot`
3. bot links Telegram identity to the app-first account
4. app calls reward claim API
5. backend validates membership in `@pokrov_vpn`
6. backend grants `+10 days` when eligible

### Support Flow

1. user opens support from app, WebApp, or helpbot
2. the platform stores or routes the support thread
3. operator responds through the current support tooling

## Runtime Hosts And Services

Canonical control-plane host:

- `brain`: `82.21.114.104`

Important services:

- `portal-api`
- `portal-bot`
- `portal-helpbot`
- `caddy`
- `x-ui`

## Public API Shape

Major currently live public and app-first routes in `portal_bot/api.py` include:

- `GET /api/health`
- `GET /api/public/plans`
- `POST /api/auth/telegram/web-login`
- `POST /api/client/session/start-trial`
- `POST /api/client/telegram/link`
- `GET /api/payments/providers`
- `POST /api/payments/orders/create`
- `POST /api/payments/orders/create-public`
- `GET /api/dashboard`
- `GET /api/client/apps`
- `GET /api/nodes/status`
- `POST /api/bonuses/channel/claim`
- tickets and admin APIs under `/api/tickets` and `/api/admin/*`

The backend exposes both public/app-first surfaces and a broader Telegram/admin-oriented API set. Keep docs aligned with the actual route inventory in `portal_bot/api.py`.

## Telegram Registry

Canonical bot usernames:

- `portal_service_bot`
- `portal_privacy_helpbot`
- `portalfeedbackbot`

Current channel state:

- verified public channel: `@pokrov_vpn`
- bonus verification is live
- `@portal_service_bot` is an administrator in that channel

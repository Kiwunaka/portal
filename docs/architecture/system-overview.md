# PORTAL System Overview

Last updated: 2026-03-19

## Purpose

This document is the canonical high-level architecture map for the `PORTAL` platform.

## Main Components

### Control Plane

- `portal_bot/api.py`
  FastAPI backend for public API, admin API, payment callbacks, subscription delivery, and app-first flows.
- `portal_bot/bot.py`
  Main Telegram bot for onboarding, billing, bonuses, referrals, and admin actions.
- `portal_bot/helpbot.py`
  Dedicated support bot.
- `portal_bot/worker.py`
  Background jobs such as retention, channel bonus guard, and free-cycle resets.
- `portal_bot/models.py`
  SQLAlchemy models.
- `portal_bot/migrations.py`
  Additive schema migration helpers.

### Delivery Plane

- `portal_bot/control_panel.py`
- `portal_bot/panel_client.py`
- node inventory and routing logic
- 3x-ui panels as node-local execution layer

Current node lifecycle principle:

- `PORTAL` database chooses assignment and lifecycle
- 3x-ui executes the resulting config
- correct sequence for node retirement is `drain -> resync -> disable`

### User Interfaces

- `webapp/`
  user cabinet and web-admin
- `marketing/`
  public site, legal pages, public entrypoints
- `external/client-fork/app/`
  `PORTAL VPN` consumer client for Android and Windows

## Data Source Of Truth

Production source of truth:

- Postgres from `DATABASE_URL`

Not source of truth:

- local SQLite files
- archived test databases
- audit snapshots
- stale static reports

## Current Primary Flows

### Telegram-first platform flow

1. user enters through bot or WebApp
2. backend validates session or Telegram identity
3. billing and bonus state updates in backend
4. panel sync updates runtime user access
5. subscription endpoint serves the client configuration

### App-first client flow

1. client generates `install_id`
2. user taps `Try free`
3. backend creates app account, device record, and app session
4. backend returns a real subscription source
5. client imports and activates the profile

### Support flow

1. user opens support from app, WebApp, or helpbot
2. message is stored as a support ticket thread
3. operator responds through current support tooling

## Runtime Hosts And Services

Canonical control-plane host:

- `brain`: `82.21.114.104`

Important runtime services:

- `portal-api`
- `portal-bot`
- `portal-helpbot`
- `caddy`
- `x-ui`

## Telegram Registry

Canonical bot usernames:

- `portal_service_bot`
- `portal_privacy_helpbot`
- `portalfeedbackbot`

Current channel state:

- bonus verification code is live
- verified public channel: `@pokrov_vpn`
- `@portal_service_bot` is an administrator in that channel

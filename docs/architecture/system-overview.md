# POKROV System Overview

Last updated: 2026-03-31

## Document Status

This file is living source of truth for the platform architecture map.

## Purpose

`POKROV` is a platform composed of:

- a Python backend and Telegram control plane
- a user cabinet and admin web surface
- a marketing and legal site
- a Flutter client fork for `POKROV VPN`
- operational scripts for deployment, node management, and release flow

## Main Components

### Control Plane

- `portal_bot/api.py`
  FastAPI backend for health checks, app-first session bootstrap, payments, bonuses, tickets, public data, public reviews, and admin APIs.
- `portal_bot/bot.py`
  Main Telegram bot for billing, campaigns, referrals, review moderation, and operator actions.
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
- observer-lite uses `xray access.log -> node collector -> brain ingest -> Postgres state -> web admin`

Node lifecycle rule:

- `POKROV` database decides assignment and lifecycle
- 3x-ui executes the resulting config
- node retirement sequence is `drain -> resync -> disable`
- the RF reserve contour lives outside the normal delivery lifecycle until explicitly promoted

### User Interfaces

- `webapp/`
  user cabinet, session continuation, and the primary admin operator surface
- `marketing/`
  public website, pricing, legal pages, and public conversion flows
- `external/client-fork/app/`
  `POKROV VPN` consumer client for Android and Windows
- `shared/`
  shared public copy, canonical hostnames, and cross-surface product constants

Admin ownership rule:

- `webapp` is the primary admin surface for user, node, ticket, and metrics work
- Telegram admin in `portal_bot/bot.py` is fallback/emergency tooling and must follow the same user-status semantics as web admin

Current release scope rule:

- full public `v1` ship target: `Android` and `Windows`
- `iOS` and `macOS`: readiness and packaging documentation only in this wave

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
2. backend issues a deep link to `@pokrov_vpnbot`
3. bot links Telegram identity to the app-first account
4. app calls reward claim API
5. backend validates membership in `@pokrov_vpn`
6. backend grants `+10 days` when eligible

### Checkout Continuation Flow

1. user opens pricing or renewal from marketing, webapp, or bot
2. platform resolves a valid web session or signed checkout ticket
3. checkout loads real payment providers or a truthful unavailable state
4. payment completion returns the user to the active account journey

Architecture rule:

- public pricing may introduce checkout
- real checkout must continue from authenticated or ticketed context
- bot purchase flow remains valid, but it does not replace app-first public onboarding

### Support Flow

1. user opens support from app, WebApp, or helpbot
2. the platform stores or routes the support thread
3. operator responds through the current support tooling

### Feedback And Review Flow

1. user leaves feedback from the app, WebApp, or `@pokrov_feedbackbot`
2. backend stores the submission for moderation
3. operator approves selected reviews for public display
4. marketing and cabinet surfaces render only featured reviews
5. visible nicknames are masked in a friendly format such as `mikh****`

## Runtime Hosts And Services

Canonical control-plane host:

- `brain`: `82.21.114.104`

Important services:

- `portal-api`
- `portal-bot`
- `portal-helpbot`
- `caddy`
- `x-ui`

Auxiliary RF hosts:

- `mini`
  dedicated RU probe vantage point for whitelist and foreign-reachability checks
- `rf1`
  reserve RF ingress for operator and VIP/manual access, chained onward to an EU exit

RF host rule:

- do not place control-plane services on `mini` or `rf1`
- keep `rf1` outside the default runtime delivery pool in phase 1
- RU ingress / RF reserve experiments are currently in backlog
- do not spend implementation time on `mini` ingress variants or `rf1` promotion until the product owner explicitly requests a return to this work

## Public Hostnames And Migration Roles

Canonical public surfaces:

- `https://pokrov.space/`
- `https://app.pokrov.space/`
- `https://api.pokrov.space/`

Role split:

- `pokrov.space` is the canonical public hostname family
- `connect.pokrov.space` is the canonical config/connect host
- `pay.pokrov.space/checkout/` is the canonical hosted checkout entry
- `kiwunaka.space` is a migration compatibility layer for older subscriptions and must not be treated as a fresh-entry surface
- browser flows must prefer `api.pokrov.space` for API traffic and never rely on HTML returned from `app.pokrov.space` as if it were API JSON

Copy/config rule:

- new public copy and CTA text must stay centralized through `shared/copy.ts` and `copy/catalog.ru.json`
- bot, site, app, and checkout links should resolve from shared host config rather than hard-coded per surface

## Monitoring And Visibility Model

Current operational monitoring should correlate:

- canonical public hostname health
- app-first session bootstrap and dashboard health
- Telegram bot and support bot availability
- node reachability and public egress
- per-node metrics freshness, sustained resource pressure, and probe-failure reasons
- per-user observer-lite IP/node footprint and conservative `ok | watch | suspicious` state
- device and account visibility for support diagnosis

Dashboard and user-cabinet traffic visibility must come from server-side node runtime snapshots rather than app-only telemetry.

- current traffic usage should prefer live panel/runtime counters aggregated across the user nodes
- current connection count should prefer runtime connection evidence such as active IP counts or active nodes
- app device records remain useful, but they are a separate app-first visibility layer and must not be shown as the only source of "connected devices"

Required external geography check:

- run an RU-based external probe every `6 hours`
- verify the probe host itself can reach `google.com`
- verify Telegram surfaces such as `api.telegram.org` and `t.me`
- verify the current `POKROV` nodes remain reachable from that external RU vantage point
- verify the RF reserve ingress state:
  - `xhttp_alive`
  - `hysteria_alive`

This gives operators a useful distinction between:

- a broken probe host
- a broken node or public edge
- a hostname migration issue where legacy compatibility paths still work but canonical `pokrov.space` paths do not
- a reserve path that still works for operator and VIP access while canonical paths fail

Current admin status model for operators:

- `active`
- `expired`
- `blocked`
- `manual_test`

Manual/test cleanup rule:

- only explicit manual/test users may be deleted from admin
- real-user deletion is out of scope for the main admin surface in this wave

## Device, Telegram, And IP Correlation

The app-first model is not only about authentication. It also provides a friendlier support map than a Telegram-only design.

Operator diagnosis should be able to correlate:

- app account
- linked Telegram identity when present
- device record
- recent `last_ip`
- current node/subscription context
- current runtime connection footprint across assigned nodes
- current traffic usage source, including whether it comes from runtime panel data or a fallback

This visibility supports:

- connection triage
- abuse control
- account recovery
- targeted incident response

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
- `GET /api/reviews`
- `POST /api/reviews`
- `POST /api/bonuses/channel/claim`
- tickets and admin APIs under `/api/tickets` and `/api/admin/*`

The backend exposes both public/app-first surfaces and a broader Telegram/admin-oriented API set. Keep docs aligned with the actual route inventory in `portal_bot/api.py`.

Current release-gate smoke focus should cover:

- `GET /api/health`
- `POST /api/client/session/start-trial`
- Telegram OIDC start and finish
- bot token handoff into webapp
- `GET /api/client/apps`
- `GET /api/payments/providers`
- checkout continuation from session or ticket

## Telegram Registry

Canonical bot usernames:

- `pokrov_vpnbot`
- `pokrov_supportbot`
- `pokrov_feedbackbot`

Current channel state:

- verified public channel: `@pokrov_vpn`
- bonus verification is live
- `@pokrov_vpnbot` is an administrator in that channel

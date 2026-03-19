# PORTAL VPN Product Overview

Last updated: 2026-03-19

## Product Names

- platform brand: `PORTAL`
- client application: `PORTAL VPN`

## Current Product Strategy

`PORTAL VPN` is a `consumer-first`, `app-first` VPN client for:

- `Android`
- `Windows`

The product goal is simple:

1. open the app
2. tap `Try free`
3. receive a real working subscription
4. tap `Connect`

Telegram is not required for first launch, trial activation, or normal usage.

## Core Product Decisions

- primary UX: `consumer-first`
- primary identity model: `app-first`
- default runtime core: `sing-box`
- `xray` availability: advanced compatibility fallback only
- trial duration: `5 days`
- Telegram reward: `+10 days`
- product language priority: Russian must be first-class

## Main User Surfaces

### Client App

Primary tabs:

1. `VPN`
2. `Locations`
3. `Devices`
4. `Profile`
5. `Support`

### Telegram

Telegram remains useful for:

- optional account linking
- growth and community
- recovery flows
- support entrypoints outside the app

### WebApp And Marketing

The platform still includes:

- `webapp/` for account and admin scenarios
- `marketing/` for public website and legal pages

## Trial And Bonus Rules

### Trial

- every valid first device account can receive `5 days`
- trial must create a real backend account and a real working subscription
- trial is never decorative UI-only state

### Telegram Bonus

- bonus value: `+10 days`
- bonus requires Telegram linking to the app-first account
- bonus additionally requires membership verification against the configured public channel
- current verified public channel: `@pokrov_vpn`

## Advanced Settings Policy

Advanced networking controls stay in the product, but they must not dominate the first-layer journey.

Hidden from first layer:

- DNS internals
- routing internals
- `resolve destination`
- `strict route`
- WARP
- TLS tricks
- logs
- Clash API
- manual subscription import as primary CTA

Visible in advanced:

- compatibility toggles
- `xray` fallback
- DNS overrides
- logs and debugging
- custom import

## Branding Rules

The client and public UX must be fully branded as `PORTAL` / `PORTAL VPN`.

Replace or remove:

- visible `Hiddify` strings
- old launcher and tray assets
- legacy bot names
- old support usernames
- demo nodes and fake platform labels

Current logo source for the client fork:

- [logogo.png](C:/Users/kiwun/Documents/ai/VPN/external/logogo.png)

## Current Known Product Risk

The Telegram bonus path is code-ready but not fully operational until a real Telegram channel username is configured and `@portal_service_bot` is added there.

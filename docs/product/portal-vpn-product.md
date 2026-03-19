# PORTAL VPN Product Overview

Last updated: 2026-03-20

## Document Status

This file is living source of truth for product direction and user-facing product rules.

## Product Names

- platform brand: `PORTAL`
- client application: `PORTAL VPN`

## Product Strategy

`PORTAL VPN` is a `consumer-first`, `app-first` VPN product for:

- `Android`
- `Windows`

Primary user goal:

1. open the app
2. tap `Try free`
3. receive a real working subscription
4. tap `Connect`

Telegram is optional for first launch, free trial activation, and normal daily use.

## Locked Product Rules

- primary UX: `consumer-first`
- primary identity model: `app-first`
- default runtime core: `sing-box`
- `xray` role: advanced compatibility fallback only
- free trial: `5 days`
- Telegram reward: `+10 days`
- Russian is a first-class user language

## Current User Surfaces

### Client App

Primary navigation:

1. `VPN`
2. `Locations`
3. `Devices`
4. `Profile`
5. `Support`

### Telegram

Telegram remains in the product for:

- optional account linking
- bonus claim flow
- recovery scenarios
- community and announcements
- external support entrypoints

### WebApp And Marketing

- `webapp/` handles account and admin scenarios
- `marketing/` handles the public website, checkout entrypoints, and legal pages

## Trial And Bonus Rules

### Free Trial

- every valid first device account can receive `5 days`
- trial must create a real backend account, device, session, and working subscription source
- trial must never be decorative UI-only state

### Telegram Reward

- reward value: `+10 days`
- the app-first account must first link Telegram
- reward validation then checks membership in the configured public channel
- active public channel: `@pokrov_vpn`
- `@portal_service_bot` is an administrator in that channel

## Advanced Settings Policy

Advanced networking controls remain available, but they must not dominate first-run UX.

Hidden from first layer:

- DNS internals
- routing internals
- `resolve destination`
- `strict route`
- WARP
- TLS tricks
- logs
- Clash API
- manual import as the primary CTA

Visible in advanced:

- compatibility toggles
- `xray` fallback
- DNS overrides
- logs and debugging
- custom import

## Branding Rules

All public and client-facing surfaces must be branded as `PORTAL` / `PORTAL VPN`.

Replace or remove:

- visible `Hiddify` strings
- old launcher and tray assets
- legacy bot names
- old support usernames
- fake demo branding

Current logo source for the client fork:

- [logogo.png](C:/Users/kiwun/Documents/ai/VPN/external/logogo.png)

## Support Direction

Support should be reachable from:

- the client app
- the WebApp
- helpbot `@portal_privacy_helpbot`

Support payloads should carry enough device and app context for operator diagnosis.

## Product Risk Focus

Current major risks are not around channel configuration anymore. The main remaining risk is documentation and UX drift between the platform canon and the client fork while app-first rollout continues.

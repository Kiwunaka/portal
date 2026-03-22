# POKROV VPN Product Overview

Last updated: 2026-03-22

## Document Status

This file is living source of truth for product direction and user-facing product rules.

## Product Names

- platform brand: `POKROV`
- client application: `POKROV VPN`

## Product Strategy

`POKROV VPN` is a `consumer-first`, `app-first` VPN product for:

- `Android`
- `Windows`

`iOS` and `macOS` are readiness tracks only for this release wave. They are not part of the full public `v1` promise.

Primary user goal:

1. open the app
2. tap `Try free`
3. receive a real working subscription
4. tap `Connect`

Telegram is optional for first launch, free trial activation, and normal daily use.
Telegram remains a secondary path for linking, bonus claim, recovery, support entrypoints, and bot-side purchase continuation.

## Locked Product Rules

- primary UX: `consumer-first`
- primary identity model: `app-first`
- full public `v1` scope: `Android + Windows`
- Apple scope in this wave: readiness, signing prep, and store prerequisites only
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
- feedback collection and public review moderation

### WebApp And Marketing

- `webapp/` handles account, session continuation, and admin scenarios
- `marketing/` handles the public website, pricing, checkout entrypoints, and legal pages

Public funnel rule:

- marketing and webapp should present `app-first` onboarding first
- checkout must continue from a valid web session or checkout ticket
- Telegram bot purchase flow remains available, but it is not the default public story

## Official Hostnames

Canonical public hostnames:

- `https://pokrov.space/`
- `https://app.pokrov.space/`
- `https://api.pokrov.space/`

Hostname policy:

- `pokrov.space` is the official public brand and entrypoint for new users
- `app.pokrov.space` is the official browser surface for account continuation and checkout continuation
- `api.pokrov.space` is the canonical API base for web and app-first browser flows
- `kiwunaka.space` is compatibility-only during migration and must not be used in new product copy, new onboarding, or fresh distribution links

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
- `@pokrov_vpnbot` is an administrator in that channel

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

All public and client-facing surfaces must be branded as `POKROV` / `POKROV VPN`.

Replace or remove:

- visible `Hiddify` strings
- old launcher and tray assets
- legacy bot names
- old support usernames
- fake demo branding

Current logo source for the client fork:

- [logogo.png](C:/Users/kiwun/Documents/ai/VPN/external/logogo.png)

Current release logo set for public and client surfaces:

- [logoclear.svg](C:/Users/kiwun/Documents/ai/VPN/logo/logoclear.svg)
- [logowithtext.svg](C:/Users/kiwun/Documents/ai/VPN/logo/logowithtext.svg)

## Support Direction

Support should be reachable from:

- the client app
- the WebApp
- helpbot `@pokrov_supportbot`
- feedback bot `@pokrov_feedbackbot`

Support payloads should carry enough device and app context for operator diagnosis.

Support visibility should be able to connect:

- linked Telegram identity when present
- current device identity and app version
- recent IP context
- current subscription and node state

## Reviews And Feedback

Users can leave feedback from:

- the client app
- the WebApp
- `@pokrov_feedbackbot`

Moderation rules:

- raw feedback stays private until an operator approves it
- approved reviews can be featured on the public homepage and cabinet surfaces
- visible usernames must use a masked format like `mikh****`
- if a username is missing, use a neutral label such as `Пользователь`

Public review copy should stay:

- short
- friendly
- specific
- truthful about what the service does

## Product Risk Focus

Current major product risks are:

- app-first copy drifting back into Telegram-first wording
- public pricing or checkout behaving like a decorative vitrine instead of a real continuation flow
- Android and Windows release wiring drifting away from canonical artifact URLs
- Apple readiness notes being mistaken for a public ship promise

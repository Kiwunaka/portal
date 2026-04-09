# POKROV VPN Product Overview

Last updated: 2026-04-08

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

## Current Release Constraints

- release target remains `Android + Windows`
- `Windows` stays in scope for the public `v1` ship when its normal gates are green
- `Android` remains release-blocked until a real release-build audit proves that localhost listeners and local control surfaces are either disabled or safely authenticated
- do not describe Android app-isolation features such as split tunneling, Private Space, Knox, Shelter, or similar tooling as sufficient mitigations for an unauthenticated local control surface

## Russia-Aware Routing Direction

Current product direction for Russian users:

- recommended preset: `Все, кроме РФ`
- additional presets: `Global` and `Только заблокированное`
- `Все, кроме РФ` is meant to keep `geoip:ru` plus private and reserved networks direct while proxying the rest
- DNS behavior must be selected explicitly per routing mode rather than being hidden behind one hardcoded preset

Current truth:

- the shipping client already has a `Region.ru` placeholder
- the full routing strategy and geo-asset wiring are not yet complete
- do not market RU-special routing as fully shipped until the real strategy layer, DNS split checks, and release smoke are in place

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
- `https://connect.pokrov.space/`
- `https://pay.pokrov.space/checkout/`

Hostname policy:

- `pokrov.space` is the official public brand and entrypoint for new users
- `app.pokrov.space` is the official browser surface for account continuation and checkout continuation
- `api.pokrov.space` is the canonical API base for web and app-first browser flows
- `connect.pokrov.space` is the canonical public host for config delivery, QR import, and `subscription_url`
- new public connection links must always point to `connect.pokrov.space`
- legacy `api.pokrov.space/s8Kx2mP7qR4wT/...` links may continue to work for imported profiles, but must not be shown as the primary user-facing path
- `kiwunaka.space` is compatibility-only during migration and must not be used in new product copy, new onboarding, or fresh distribution links

## Connection Link Policy

Public connection delivery now follows one simple rule:

- one public connection link
- one QR based on that same link
- one canonical host: `connect.pokrov.space`

Product wording rule:

- user-facing copy should say `ссылка подключения` and `QR для подключения`
- do not describe separate public `умный` and `обычный` keys
- `?format=plain` remains backend compatibility-only and must stay hidden from normal site, bot, and webapp flows

## Trial And Bonus Rules

### Free Trial

- every valid first device account can receive `5 days`
- trial must create a real backend account, device, session, and working subscription source
- trial must never be decorative UI-only state
- trial is premium-grade access during those `5 days`
- after trial expiry the account automatically moves to `free_monthly`

### Telegram Reward

- reward value: `+10 days`
- the app-first account must first link Telegram
- reward validation then checks membership in the configured public channel
- active public channel: `@pokrov_vpn`
- `@pokrov_vpnbot` is an administrator in that channel

### Post-Trial Access Model

- `free_monthly`: `5 GB / 30 days`
- `free_monthly` device limit: `1`
- `free_monthly` keeps monthly traffic reset via the free-cycle job
- after `5 GB` is exhausted, the account stays usable in `soft mode` until the next reset
- `paid` remains unlimited traffic with up to `5 devices`

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

Client diagnostics should be useful without leaking secrets. User-facing diagnostics may show:

- active routing mode
- current route category
- reconnect or profile-refresh guidance

They must not expose:

- raw config bodies
- keys or subscription secrets
- detailed topology that is unnecessary for support

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
- Android release being treated as ready before localhost listener and control-surface safety is proven in a release build
- RU routing and DNS presets being described as finished before the real strategy layer and leak checks ship

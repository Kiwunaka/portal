# POKROV Product Overview

Last updated: 2026-07-05

## Document Status

This file is living source of truth for product direction and user-facing product rules.

## Product Names

- platform brand: `POKROV`
- public product line: `POKROV`
- legacy client identifier: `POKROV VPN` only for compatibility, old package/store history, legacy filenames, and references that are not yet migrated

## Product Strategy

`POKROV` is a `consumer-first`, `app-first` connectivity product for:

- `Android`
- `Windows`

`Linux`, `iOS`, and `macOS` are roadmap/readiness tracks only for this release wave. They are not part of the full public `v1` promise.

Primary user goal:

1. open the app
2. tap `Try free`
3. receive a real working subscription
4. tap `Connect`

Telegram is optional for first launch, free trial activation, and normal daily use.
Telegram remains a secondary path for linking, bonus claim, recovery, support entrypoints, and bot-side purchase continuation.
Browser continuation currently starts from app handoff, Telegram, and email when delivery readiness is green.
Email browser continuation is live as an additive account-continuation lane, not as a replacement for the app-first trial path.

## Wave 0 Global Rework Decision Freeze

The current program is locked around these target product decisions:

- `POKROV-app/main` is the only active client canon for product direction, client contracts, and client documentation
- `app-next/` remains retained bootstrap archive/reference material only
- `external/client-fork/app/` remains retained rollback/archive reference material only
- the front-end rebuild is an atlas-driven shell reset: `marketing` acquires, `webapp` continues known-user work, and the app shell stays locked to the four-tab consumer layout
- one canonical `app-first` account links `install_id`, email, Telegram, devices, and activation keys
- public delivery scope for this wave remains `Android + Windows`; Linux packaging and Apple hosts may remain in engineering lanes but are not part of public promise or release acceptance
- commercial flow becomes `buy key -> redeem key -> managed premium`, with raw subscription links hidden from default site, webapp, and bot UX and exposed only for explicit recovery or manual-request paths
- `marketing` is the only public acquisition, pricing, and paywall surface, and its default public path is `trial -> install -> first connection`; checkout remains an honest continuation after product check or explicit plan intent. `webapp` is session-aware continuation, support, redeem, renewal continuation, and admin only
- public browser copy and visual governance are centralized through `shared/copy.ts`, `copy/catalog.ru.json`, and `shared/design-tokens.json`, with locked host and product facts inherited from the shared fact files
- visible user-facing cabinet IA becomes `Главная / Доступ / Помощь / Аккаунт`, backed by `/dashboard/`, `/subscription/`, `/support/`, and `/settings/`; `devices`, `statistics`, `downloads`, `redeem`, hosted-checkout continuation, and compatibility redirects are task/detail routes rather than parallel public-entry surfaces
- app surfaces must not use ad SDKs or third-party ads; only approved first-party promo slots may render remotely managed promo content
- normal consumer UX should show one logical location, while transport variants `VLESS+REALITY`, `VMess`, `Trojan`, and `XHTTP` stay hidden behind auto, diagnostics, or admin controls
- target client IA becomes `Protection / Locations / Rules / Profile`, with `Support`, `Devices`, `Subscription`, and `Settings` nested inside `Profile`
- visible routing story becomes `All except RU`, `Full tunnel`, and `Selected apps`, with `Rules` owning split tunneling and bypass behavior
- owner-approved update on `2026-06-01`: public `VPN` / `ВПН` wording is allowed on dedicated SEO/search-intent surfaces and metadata when it is visible, useful to users, and tied to the actual POKROV Android/Windows app flow; hidden text, cloaking, keyword stuffing, unsupported "best" claims, and unsupported availability claims remain forbidden

Client-canon note:

- this document treats only `POKROV-app/main` as the active client lane
- any surviving `app-next/` or legacy-fork references elsewhere are archival or rollback-only and must not override product truth

## Locked Product Rules

- primary UX: `consumer-first`
- primary identity model: `app-first`
- browser identity continuation: app handoff, `Telegram`, and additive `email` continuation when delivery readiness is green
- full public `v1` scope: `Android + Windows`
- Linux order: after Android/Windows gates, package Flutter desktop for Ubuntu/Fedora through AppImage plus deb/rpm evidence before public claims
- Apple scope in this wave: readiness, signing prep, and store prerequisites only
- default runtime core: `sing-box`
- `xray` role: advanced compatibility fallback only
- free trial: `5 days`
- Telegram reward: `+10 days`
- public user-facing client version line: `0.x.x-beta`
- Russian is a first-class user language
- recommended public routing mode: `All except RU`
- public routing mode set: `All except RU`, `Full tunnel`, and `Selected apps`
- public recovery order: `POKROV app -> web cabinet -> Telegram fallback`
- public wording may use direct `VPN` / `ВПН` terms on SEO/search-intent pages and metadata after the `2026-06-01` owner approval, but normal product copy should still prefer app, connection, routing, access, or support context when that is clearer and less spammy

## Current Release Constraints

- release target remains `Android + Windows`
- next platform after those gates is Linux; Apple platforms follow later only with build/sign/notarization/TestFlight/App Store evidence
- outside-store public beta for Android + Windows is `GO` as of `2026-05-15` with the retained launch-decision evidence pack
- `Windows` stays in scope for the public `v1` ship when its normal gates are green; the current outside-store beta remains unsigned and must keep unknown-publisher warning copy visible
- `Android` public beta promotion uses the operator-approved physical-device audit plus the APK/EXE outside-store handoff; store publishing, raw physical audit proof, and stronger Android safety claims remain separate later gates
- runtime `/api/client/apps` verification and GitHub Releases APK/EXE handoff are green for the beta; a real-user Telegram WebApp opening remains a manual owner test, not a local agent blocker
- repo/static/client green gates do not by themselves prove live deploy, live node enablement, or separate `current-origin`, `brain-origin`, and `RU-origin` checks; the 2026-05-15 pack includes current-origin and brain-origin evidence, while RU-origin remains an accepted skip
- emulator or adb-only audit runs are valid preflight for adb wiring and timing, but the public beta handoff must retain physical release-build audit evidence for Android
- do not describe Android app-isolation features such as split tunneling, Private Space, Knox, Shelter, or similar tooling as sufficient mitigations for an unauthenticated local control surface
- broad/stable release, `1.0.0`, app-store availability, trusted Windows signing, raw Android audit proof, and RU-origin readiness must not be claimed until each has current redacted evidence

## Russia-Aware Routing Direction

Current product direction for Russian users:

- recommended preset: `All except RU`
- public routing modes are marketed as `All except RU` and `Full tunnel`
- hidden follow-up preset: `Blocked only`
- `All except RU` is meant to keep `geoip:ru` plus private and reserved networks direct while proxying the rest
- DNS behavior must be selected explicitly per routing mode rather than being hidden behind one hardcoded preset

Current truth:

- the shipping client already has an explicit routing-mode layer for `global`, `allExceptRu`, and internal `blockedOnly`
- public copy must describe `global` as `Full tunnel`, not as a raw implementation label
- the shipping client still carries a `Region.ru` placeholder, but that placeholder is not the product authority
- `Blocked only` remains internal or compatibility-only until geo assets, DNS split behavior, and leak checks are complete
- the full routing strategy and geo-asset wiring are not yet complete
- do not market RU-special routing as fully shipped until the real strategy layer, DNS split checks, and release smoke are in place
- `All except RU` should default to tunneled remote DNS with local direct resolution only for curated direct paths
- the public consumer path should stay `TUN`-first; loopback proxy mechanics remain advanced or internal-only

## Current User Surfaces

### Client App

Primary navigation:

1. `Protection`
2. `Locations`
3. `Rules`
4. `Profile`

Nested under `Profile`:

- `Support`
- `Devices`
- `Subscription`
- `Settings`

Legacy `/config-options`, `/about`, and `/logs` may remain as compatibility redirects only. Public IA is the four-tab shell above.

Quick Connect rule:

- `Auto-select` remains the default daily path.
- premium app-managed profiles expose a backend-built smart shortlist of up to `5` eligible non-free nodes
- free-tier access still resolves only to the dedicated `NL-free` node
- the shortlist rejects disabled, draining, unhealthy, stale, `cpu_percent >= SMART_CONNECT_CPU_REJECT_PERCENT` (default `85`), and transport-incompatible nodes before the client measures latency
- the client combines real device RTT with backend CPU and health penalties and keeps the previous node when the improvement stays below the `15%` stickiness threshold
- incident-promoted `ru_bridge_relay` profiles may use `mini` as a first-hop bridge to non-US POKROV delivery nodes; this is an emergency reachability contour, not a normal RU delivery node or a public RU-readiness claim
- public client screens must not expose raw hostnames, ports, public IP, raw connection links, sniffing terms, JSON/profile editors, or local-control surfaces in the normal consumer path

First-run route-mode rule:

- after account bootstrap and before the first live route activation, the app must ask how this device should be optimized
- the first-layer consumer choice must be `Optimize everything on this device` or `Only selected apps`
- `Optimize everything on this device` is the recommended default and stays `TUN`-first
- `Only selected apps` is the split-tunneling path and must save a per-device app/process selection instead of opening raw networking controls
- the saved route choice must stay synchronized through backend-owned `route_mode`, `selected_apps`, and `requires_elevated_privileges` fields so app, cabinet, and support see the same device state
- Windows should use an executable or process picker; Android should use an installed-app package picker
- current P3 client work may use manual app/process identifiers as a bridge; Android app-managed profiles map selected package identifiers into sing-box `include_package`
- native Android package picking and Windows process/exe picking remain follow-up work; raw rule editing must stay outside normal consumer UI
- if the chosen desktop route mode requires elevated rights, the app must explain that clearly and tell the user to relaunch as administrator before connect
- system proxy, raw service-mode toggles, and manual subscription share/edit actions stay out of normal quick access

### Marketing Site

`marketing/` is the public acquisition and discovery surface for `POKROV`.

Current public role:

- `https://pokrov.space/` is the public entry homepage for new users and should converge most acquisition traffic into app-first trial, install, and first-connection guidance
- `https://pokrov.space/checkout/` is the public pricing, paywall, and activation-key purchase continuation surface when the user has plan intent or returns after checking the product
- `https://pokrov.space/install/` is the public step-by-step install instruction page (Android unknown-sources and Windows SmartScreen honesty included); since the `2026-07` redesign it is indexable, sits in the sitemap, and routes download CTAs through the cabinet downloads flow
- indexable landing pages can capture platform, use-case, or Telegram intent, but they must converge to the same product facts and the same app-first trial/install/first-connection CTA set
- public legal pages also live on the marketing surface
- the current canonical public route family is `/mobile/`, `/tiktok/`, `/youtube/`, `/devices/`, `/telegram/`, and `/vpn/`, with permanent redirects from the earlier legacy SEO paths

2026-07 redesign positioning notes:

- the public surface runs on the `pokrov-clear` white/emerald design foundation (root `DESIGN.md`) with Golos Text and light-only theme
- the landing leads with real drawn app UI (connect/locations/account screens) instead of abstract promises — showing the actual product is the trust wedge none of the surveyed RU competitors use
- an explicit honesty strip is part of public positioning: trial without card, one-time activation keys with no auto-renewal («отменять нечего»), release files visible on GitHub Releases, human Telegram support; fake counters, fabricated reviews, and self-scored competitor tables stay forbidden

### WebApp

`webapp/` is the continuation surface for known users, session continuation, and operator work.

Current cabinet role:

- `https://app.pokrov.space/` continues an existing browser session or bot handoff
- browser entry currently supports app handoff, Telegram, and email continuation into the same cabinet session family without replacing the app-first model
- public-facing email browser continuation can be shown as live only while sender readiness, delivery confirmation, and public runtime readiness stay green
- cabinet is continuation-first; it must not become a second landing page or re-pitch the public marketing story
- public email signup, verification, and recovery are live continuation paths when email readiness is green, but they must not be described as a premium-trial replacement for the app
- email forms are gated by `/api/auth/email/status`; the default degrades to unavailable unless public enablement, delivery configuration, and non-debug runtime state are all green
- current visible cabinet IA is `Главная`, `Доступ`, `Помощь`, and `Аккаунт`
- `/devices/`, `/statistics/`, `/downloads/`, `/redeem/`, `/subscription/checkout/`, `/support/thread/`, and `/support/legal/` remain deep-linkable task/detail routes inside that compact cabinet model
- task routes currently include cabinet entry, hosted-checkout continuation, redeem, downloads, and support threads
- `/pricing/` remains only as a compatibility continuation alias and must not become a second public pricing surface
- `webapp` is also the primary admin operator surface
- site, cabinet, and admin must keep obvious navigation back to each other so no surface becomes a dead end
- consumer cabinet screens should show safe summaries such as `connect.pokrov.space` and route categories while keeping raw personal links, public IP, and node internals hidden on screen
- consumer cabinet screens must not expose raw subscription edit, regenerate, or share actions in the first-layer UI
- authenticated support in the cabinet should continue as a real ticket thread with uploads, not as decorative form state or a fake live-chat promise
- the primary admin information architecture is grouped as `People`, `Access`, `Payments`, `Network`, `Diagnostics`, `Messaging`, and `Feedback`

### Telegram

Telegram remains in the product for:

- optional account linking
- bonus claim flow
- recovery scenarios
- community and announcements
- external support entrypoints
- feedback collection and public review moderation

Public funnel rule:

- marketing introduces the product and captures public intent through trial, install, and first connection before payment pressure
- `pokrov.space/checkout/` shows public pricing and sells activation keys through the hosted checkout flow when plan intent is explicit
- `app.pokrov.space` continues real account, renewal, redeem, support, and admin flows
- cabinet checkout is continuation-only and creates an authenticated provider order that renews the current account; anonymous public checkout remains key-first by email
- the default site, cabinet, and bot UX must not expose raw subscription links
- Telegram bot purchase flow remains available, but it is not the default public story
- `connect.pokrov.space` remains the delivery surface for the one public connection link and matching QR when explicit manual import is needed, not a fresh-entry marketing surface or first-layer consumer story
- if Telegram is degraded, recovery should continue through the app and `app.pokrov.space` before falling back to Telegram

## Unified Public Copy Direction

Public-facing copy across marketing and webapp should follow one simple style:

- calm, direct, and premium without fake urgency, countdown theater, or exaggerated rescue language
- `app-first` in onboarding language, with Telegram framed as optional continuation or fallback
- lead cards and above-the-fold proof with concrete user-checkable hooks: `5 days`, `no card for trial`, `Android + Windows`, `+10 days for Telegram`, `up to 5 devices in paid plans`, `cabinet`, and `support`
- avoid mood-first public phrases such as `спокойный маршрут`, `легкий путь`, `понятный сценарий`, or similar filler when a real product fact, action, limit, or status can be shown instead
- marketing and cabinet copy must stay governed through `shared/copy.ts`, `copy/catalog.ru.json`, and `shared/design-tokens.json` so both surfaces tell the same product story
- email continuation copy may be live when the delivery path is ready, and must degrade honestly if delivery readiness fails
- cabinet copy should focus on continuation, renewal, redeem, support, and recovery rather than acting like a second landing page
- one product story across homepage, SEO landings, cabinet, and checkout, with trial, install, and first connection as the primary public CTA path
- direct `VPN` / `ВПН` wording is allowed for visible SEO/search-intent copy after the `2026-06-01` owner approval; do not use hidden SEO text, cloaking, keyword stuffing, unsupported "лучший" claims, or copy that implies store availability, stable `1.0.0`, trusted Windows signing, raw Android physical-audit proof, or RU-origin readiness without evidence
- public-facing wording should prefer user outcomes and next steps over transport acronyms, raw profile terminology, or operator jargon
- explicit next-step CTA wording such as `download app`, `open cabinet`, `continue to checkout`, or `open Telegram` only when that is the real next step
- no separate product variants or conflicting promises invented for SEO pages

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

Public connection delivery now follows one simple rule when manual import is explicitly needed:

- one public connection link
- one QR based on that same link
- one canonical host: `connect.pokrov.space`
- no first-layer consumer screen should lead with QR, raw token, raw config, or transport settings

Product wording rule:

- explicit fallback copy may say `ссылка подключения` and `QR для подключения`
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

### Promo And Referral Bonuses

- app-first bonus summary, referral summary, and promo-code redemption are backend-owned API contracts
- the app may redeem promo codes through the unified code entry or the bonus promo endpoint
- the app may show referral code, safe Telegram referral link, and copy/share/open actions from the referral summary contract; referral anti-abuse and bonus granting stay backend-owned
- bonus history is an app-safe backend contract and must show only compact reward events, not raw subscription links, full promo codes, tokens, or backend event metadata
- Rewards Hub may render only enabled first-party app promo slots from `GET /api/client/promo-slots?surface=app`; third-party ads, unsafe links, and tracking campaign payloads remain forbidden
- roulette and calendar remain disabled by default, but their backend mutation routes are ledger-backed under `BONUS_WHEEL_ENABLED` / `BONUS_CALENDAR_ENABLED`; the app may show active spin/check-in controls only when backend summary state says the feature is enabled and ready

Official Telegram surfaces:

- main bot: `@pokrov_vpnbot`
- support bot: `@pokrov_supportbot`
- feedback bot: `@pokrov_feedbackbot`
- news channel: `@pokrov_vpn`
- legacy usernames `swazist_bot` and `portal_service_bot` are officially disabled and must not be documented as active product surfaces

### Post-Trial Access Model

- `free_monthly`: `5 GB / 30 days`
- `free_monthly` device limit: `1`
- `free_monthly` keeps monthly traffic reset via the free-cycle job
- after `5 GB` is exhausted, the account stays usable in `soft mode` until the next reset
- `paid` remains unlimited traffic with up to `5 devices`
- all active, non-hidden RUB plans with positive `amount_rub` are eligible for hosted checkout after the payment gate; frontend checkout must not keep a stale one-plan allowlist
- `start_99` is a one-time user plan; checkout must reject repeat attempts before provider invoice creation when the account has already made a first purchase or already has any successful paid Lava.top order
- `start_99` is already the first-month action price and must not receive referral, promo, or pending-discount reductions; discount mechanics apply only to standard paid plans when backend eligibility allows them

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

WARP rule:

- target UX is a local user-controlled toggle comparable to Hiddify: the user
  explicitly enables WARP, the client layers it through the core, and failure
  falls back to normal POKROV connection instead of leaving the user offline
- WARP may move from hidden/advanced to visible beta feature only after
  Android and Windows release-build proof covers connect, disconnect, WARP-on,
  WARP-failure fallback, and WARP-off
- do not make production WARP claims from backend telemetry alone

## Branding Rules

All public and client-facing surfaces must be branded as `POKROV`.

`POKROV VPN` may remain only as a legacy compatibility token in old filenames, package/store identifiers, bot handles, migration notes, or other surfaces that cannot yet be renamed safely.

Replace or remove:

- visible `Hiddify` strings
- old launcher and tray assets
- legacy bot names
- old support usernames
- fake demo branding

Current raster master source for release-derived assets:

- [logogo.png](C:/Users/kiwun/Documents/ai/VPN/external/logogo.png)

Use that raster master to regenerate release-facing PNG and ICO assets such as:

- Android launcher, banner, splash, and other platform raster assets
- Windows app icon, installer icon, and tray assets
- social/share preview images and other rasterized release surfaces

Current vector master set for public and client surfaces:

- [logoclear.svg](C:/Users/kiwun/Documents/ai/VPN/logo/logoclear.svg)
- [logowithtext.svg](C:/Users/kiwun/Documents/ai/VPN/logo/logowithtext.svg)

Use that vector set for:

- in-app and web mark or wordmark rendering
- favicon, icon, and manifest-source derivations
- marketing and cabinet brand surfaces that should not depend on stale exported assets

Brand-source rule:

- do not treat checked-in launcher, tray, favicon, share-preview, or splash exports as independent truth once these masters change
- regenerate derived release assets from the current raster and vector masters before publication

## Support Direction

Support should be reachable from:

- the client app
- the WebApp
- helpbot `@pokrov_supportbot`
- `support@pokrov.space`

Feedback and public-review intake should remain reachable through:

- feedback bot `@pokrov_feedbackbot`

Support payloads should carry enough device and app context for operator diagnosis.
- app and cabinet support should map to the same real ticket lifecycle so operators can continue one case across app-first, web, and admin surfaces
- ticket-capable browser support may upload files through the authenticated cabinet flow, while the client must not promise a realtime in-app chat unless such a backend actually exists

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
- marketing and cabinet copy drifting apart or cabinet entry acting like a second landing page
- retired client docs or old release notes being mistaken for active product truth
- public pricing or checkout behaving like a decorative vitrine instead of a real continuation flow
- Android and Windows release wiring drifting away from canonical artifact URLs
- public download copy treating `AAB`, `MSIX`, or portable `ZIP` artifacts as first-layer user buttons before those surfaces are actually exposed
- Apple readiness notes being mistaken for a public ship promise
- Android release being treated as ready before localhost listener and control-surface safety is proven in a release build
- RU routing and DNS presets being described as finished before the real strategy layer and leak checks ship
- public `VPN` / `ВПН` copy drifting from useful visible SEO/search-intent language into hidden text, cloaking, stuffing, or unsupported "best"/availability claims

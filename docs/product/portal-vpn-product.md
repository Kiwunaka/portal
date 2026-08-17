# POKROV Product Overview

Last updated: 2026-07-22

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

`Linux`, native `iOS`, and native `macOS` are roadmap/readiness tracks only for this release wave. Apple users keep an explicit compatible-client path with an authenticated personal key; that path is not a native Apple release claim.

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
- `marketing` is the only public acquisition, pricing, and paywall surface, and its default public path is `trial -> install -> first connection`; checkout remains an honest continuation after product check or explicit plan intent. `webapp` is session-aware continuation, support, redeem, and renewal continuation; `adminapp` is the primary operator surface, with the legacy web admin retained only as a parity fallback
- public browser copy and visual governance are centralized through `shared/copy.ts`, `copy/catalog.ru.json`, and `shared/design-tokens.json`, with locked host and product facts inherited from the shared fact files
- visible user-facing cabinet IA becomes `Главная / Доступ / Помощь / Аккаунт`, backed by `/dashboard/`, `/subscription/`, `/support/`, and `/settings/`; `devices`, `statistics`, `downloads`, `redeem`, hosted-checkout continuation, and compatibility redirects are task/detail routes rather than parallel public-entry surfaces
- app surfaces must not use third-party ad SDKs, tracking pixels, executable ad
  payloads, or unreviewed links. The first-party promo-slot delivery path may
  render operator-approved POKROV or partner campaigns with explicit schedule,
  audience, creative, safe target and dismiss behavior
- normal consumer UX should show one logical location, while transport variants `VLESS+REALITY`, `VMess`, `Trojan`, and `XHTTP` stay hidden behind auto, diagnostics, or admin controls
- target client IA becomes `Protection / Locations / Rules / Profile`, with `Support`, `Devices`, `Subscription`, and `Settings` nested inside `Profile`
- visible routing story becomes `All except RU`, `Full tunnel`, and `Selected apps`, with `Rules` owning split tunneling and bypass behavior
- owner-approved update on `2026-06-01`: public `VPN` / `ВПН` wording is allowed on dedicated SEO/search-intent surfaces and metadata when it is visible, useful to users, and tied to the actual POKROV Android/Windows app flow
- owner-approved update on `2026-07-22`: dedicated search-intent surfaces may call POKROV `лучший VPN` / `best VPN` when the statement names the user segment or scenario and is supported nearby by current verifiable product facts; hidden text, cloaking, keyword stuffing, fabricated rankings, unqualified universal superiority claims, and unsupported availability claims remain forbidden

Client-canon note:

- this document treats only `POKROV-app/main` as the active client lane
- any surviving `app-next/` or legacy-fork references elsewhere are archival or rollback-only and must not override product truth

## Current Account Foundation Boundary

The repository candidate implements an additive account foundation: UUID `accounts.id` is persisted and `users.account_id` is a nullable projection.
The public numeric `account_id` remains a compatibility projection. Device sessions use persisted rotating sessions; legacy browser, Telegram, and email tokens retain a stateless bearer compatibility path, not account or payment authority.
Rotating sessions, recovery exchange, durable provider-payment grants, account-owned fulfillment, and entitlement-ledger authority exist in this repository candidate.
Production deployment of account foundation is not proven. A completed production cutover, mixed-fleet safety, and full migration must not be claimed without exact current evidence.

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
- first account/device receives one idempotent `5-day` activation reservation;
  the premium entitlement itself remains exactly `5 days` and starts only from
  authenticated internal node/control-plane connection evidence
- client connect confirmation, `clicked_connect`, `connected_ok`, and funnel
  telemetry never activate the trial
- Telegram channel reward: one account-owned `+5 days` grant after Telegram
  linking and confirmed membership in the official channel; trial users are
  eligible, payment is not required, and already-issued `+10 days` grants are
  grandfathered
- current distributed stable-direct release: `v1.0.13`; Android `1.0.13+22`
  with ARM64, ARMv7, x86_64 and universal APKs, plus Windows `1.0.13+22`
- any later candidate requires exact promoted-client and public-asset evidence
- stable channel: public outside-store `v1.0.13`; this does not claim store
  availability, trusted Windows signing, exact Huawei/RU-LTE proof or Apple support
- Russian is a first-class user language
- recommended public routing mode: `All except RU`
- public routing mode set: `All except RU`, `Full tunnel`, and `Selected apps`
- public recovery order: `POKROV app -> web cabinet -> Telegram fallback`
- public wording may use direct `VPN` / `ВПН` terms on SEO/search-intent pages and metadata after the `2026-06-01` owner approval, but normal product copy should still prefer app, connection, routing, access, or support context when that is clearer and less spammy

## Current Release Constraints

- release target remains `Android + Windows`
- next platform after those gates is Linux; Apple platforms follow later only with build/sign/notarization/TestFlight/App Store evidence
- outside-store stable-direct Android + Windows release `v1.0.13` is public as
  of `2026-08-16`; the retained beta packs remain historical evidence
- `Windows` remains unsigned and must keep unknown-publisher/SmartScreen warning
  copy visible; stable-direct distribution does not equal trusted publisher signing
- `Android` uses production-signed direct APKs; store publishing, exact-final
  Huawei endurance and stronger raw-device claims remain separate gates
- runtime `/api/client/apps`, anonymous `/api/public/client-apps`, GitHub digests
  and the stable handoff are green for `1.0.13`; a real-user Telegram WebApp
  opening remains a manual owner test
- marketing and cabinet may describe the stable outside-store Android/Windows
  release only alongside official-source guidance and current limitations
- repo/static/client green gates do not by themselves prove live deploy, live node enablement, or separate `current-origin`, `brain-origin`, and `RU-origin` checks; the 2026-05-15 pack includes current-origin and brain-origin evidence, while RU-origin remains an accepted skip
- emulator or adb-only audit runs are valid preflight for adb wiring and timing, but the public beta handoff must retain physical release-build audit evidence for Android
- do not describe Android app-isolation features such as split tunneling, Private Space, Knox, Shelter, or similar tooling as sufficient mitigations for an unauthenticated local control surface
- app-store availability, trusted Windows signing, exact-final raw Android proof,
  real-БС emergency proof and RU-origin readiness must not be claimed until each
  has current redacted evidence

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
- `All except RU` subscription profiles should default to tunneled remote DNS; any split-DNS/local direct resolver behavior needs separate client-side implementation evidence and leak-check proof before public claims
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
- premium app-managed profiles expose a backend-built smart shortlist of up to `8` eligible non-free nodes
- manual location selection may promote any currently eligible catalog node into that bounded profile; the automatic ranking limit must not make a visible healthy location unselectable
- consumer free-tier delivery is retired; expired accounts keep recovery, support, and payment access but receive no delivery node, while the bounded first-use premium trial resolves through the paid pool
- the shortlist rejects disabled, draining, unhealthy, stale, `cpu_percent >= SMART_CONNECT_CPU_REJECT_PERCENT` (default `85`), and transport-incompatible nodes before the client measures latency
- the client combines real device RTT with backend CPU and health penalties and keeps the previous node when the improvement stays below the `20%` stickiness threshold
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
- the current canonical public route family includes `/mobile/`, `/tiktok/`, `/youtube/`, `/devices/`, `/telegram/`, `/vpn/`, `/best-vpn/`, `/compare/free-vpn/`, and the platform/install/trust/support intent routes, with permanent redirects from the earlier legacy SEO paths

2026-07 redesign positioning notes:

- the public surface runs on the `pokrov-clear` white/emerald design foundation (root `DESIGN.md`) with Golos Text and light-only theme
- the landing leads with real drawn app UI (connect/locations/account screens) instead of abstract promises — showing the actual product is the trust wedge none of the surveyed RU competitors use
- an explicit honesty strip is part of public positioning: trial without card, one-time activation keys with no auto-renewal («отменять нечего»), release files visible on GitHub Releases, human Telegram support; fake counters, fabricated reviews, and self-scored competitor tables stay forbidden

### WebApp

`webapp/` is the continuation surface for known users and session continuation,
with a retained parity fallback for operator work.

Current cabinet role:

- `https://app.pokrov.space/` continues an existing browser session or bot handoff
- browser entry currently supports app handoff, Telegram, and email continuation into the same cabinet session family without replacing the app-first model
- public-facing email browser continuation can be shown as live only while sender readiness, delivery confirmation, and public runtime readiness stay green
- cabinet is continuation-first; it must not become a second landing page or re-pitch the public marketing story
- public email signup, verification, and recovery are live continuation paths when email readiness is green, but they must not be described as a premium-trial replacement for the app
- email forms are gated by `/api/auth/email/status`; the default degrades to unavailable unless public enablement, delivery configuration, and non-debug runtime state are all green
- current visible cabinet IA is `Главная`, `Доступ`, `Помощь`, and `Аккаунт`
- `/devices/`, `/statistics/`, `/downloads/`, `/redeem/`, `/subscription/checkout/`, `/support/thread/`, and `/support/legal/` remain deep-linkable task/detail routes inside that compact cabinet model
- `/rewards/` is an account-owned detail route, not a fifth primary tab; wheel, calendar, and history load independently and fail closed when their backend state is unavailable
- task routes currently include cabinet entry, hosted-checkout continuation, redeem, downloads, and support threads
- `/pricing/` remains only as a compatibility continuation alias and must not become a second public pricing surface
- standalone `adminapp` is the primary operator surface;
  `webapp/src/app/(admin)/admin/` is the parity fallback
- site, cabinet, and admin must keep obvious navigation back to each other so no surface becomes a dead end
- consumer cabinet screens should show safe summaries such as `connect.pokrov.space` and route categories while keeping raw personal links, public IP, and node internals hidden on screen
- global panel counters are labelled as network-wide estimates and never used
  as proof that the current account is connected; account protection status is
  derived only from that account's first-connection/observer state
- the current client may refresh its own bounded device label and platform
  metadata; it cannot rename another device or expose hardware identifiers
- consumer cabinet screens must not expose raw subscription edit, regenerate, or share actions in the first-layer UI
- authenticated support in the cabinet should continue as a real ticket thread with uploads, not as decorative form state or a fake live-chat promise
- the primary `adminapp` information architecture is grouped as `People`, `Access`, `Payments`, `Network`, `Diagnostics`, `Messaging`, and `Feedback`

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
- cabinet checkout is continuation-only and creates an authenticated provider order that renews the current account; anonymous public checkout creates a durable email-owned pending entitlement and keeps one linked activation key as the unclaimed fallback
- the default site, cabinet, and bot UX must not expose raw subscription links
- Telegram bot purchase flow remains available, but it is not the default public story
- `connect.pokrov.space` remains the delivery surface for the one public connection link and matching QR when explicit manual import is needed, not a fresh-entry marketing surface or first-layer consumer story
- if Telegram is degraded, recovery should continue through the app and `app.pokrov.space` before falling back to Telegram

## Unified Public Copy Direction

Public-facing copy across marketing and webapp should follow one simple style:

- calm, direct, and premium without fake urgency, countdown theater, or exaggerated rescue language
- `app-first` in onboarding language, with Telegram framed as optional continuation or fallback
- lead cards and above-the-fold proof with concrete user-checkable hooks: `5 days`, `no card for trial`, `Android + Windows`, `+5 days for Telegram after payment`, `up to 5 devices in paid plans`, `cabinet`, and `support`
- avoid mood-first public phrases such as `спокойный маршрут`, `легкий путь`, `понятный сценарий`, or similar filler when a real product fact, action, limit, or status can be shown instead
- marketing and cabinet copy must stay governed through `shared/copy.ts`, `copy/catalog.ru.json`, and `shared/design-tokens.json` so both surfaces tell the same product story
- email continuation copy may be live when the delivery path is ready, and must degrade honestly if delivery readiness fails
- cabinet copy should focus on continuation, renewal, redeem, support, and recovery rather than acting like a second landing page
- one product story across homepage, SEO landings, cabinet, and checkout, with trial, install, and first connection as the primary public CTA path
- direct `VPN` / `ВПН` wording is allowed for visible SEO/search-intent copy after the `2026-06-01` owner approval; the `2026-07-22` owner approval also permits qualified `лучший VPN` positioning for a named segment or scenario when the supporting current facts are adjacent; do not use hidden SEO text, cloaking, keyword stuffing, fabricated rankings, unqualified universal superiority claims, or copy that implies store availability, stable `1.0.0`, trusted Windows signing, raw Android physical-audit proof, or RU-origin readiness without evidence
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

Public connection delivery follows one private-source rule when manual import is
explicitly needed:

- one authenticated base connection link and matching QR
- one canonical host: `connect.pokrov.space`
- no first-layer consumer screen should lead with QR, raw token, raw config, or transport settings
- `POKROV` APK/EXE is the only primary path on Android and Windows; authenticated manual keys are reserved for Apple-compatible clients
- the authenticated manual section may derive `format=happ` for Happ with
  `URL.searchParams`; Happ remains best-effort and the user must not edit query parameters manually
- a private URL or QR must never be placed in a third-party link, telemetry,
  public page, or support artifact

Product wording rule:

- explicit fallback copy may say `ссылка подключения` and `QR для подключения`
- do not describe separate public `умный` and `обычный` keys
- `?format=plain` remains backend compatibility-only and must stay hidden from normal site, bot, and webapp flows
- Happ format variants are authenticated manual-import derivatives of
  the same private source, not public product links or new account credentials

## Trial And Bonus Rules

### Free Trial

- every valid first device account can receive `5 days`
- trial must create a real backend account, device, session, and working subscription source
- trial must never be decorative UI-only state
- trial is premium-grade access during those `5 days`
- the one-time Telegram `+5 days` acquisition reward remains available during
  trial; roulette, calendar, and referral rewards open after the first
  successful payment. App, cabinet, bot, and support must name that split
  instead of reporting a generic connection failure
- after trial expiry the account stays recoverable and payable but receives no
  delivery node until a paid or separately authorized premium grant exists

### Telegram Reward

- exact public promise: `Можно один раз получить ещё 5 дней за привязку Telegram и подтверждение подписки на канал — даже до первой оплаты.`
- new reward value: `+5 days`, once per canonical account
- already-issued `+10 days` channel rewards remain grandfathered and are never shortened or reissued
- leaving the channel starts a `24 hour` grace period; rejoining cancels grace, and expiry removes only the unused channel interval
- trial and paid accounts may run the membership lookup and claim; manual
  accounts, a consumed Telegram grant, or a conflicting pre-payment acquisition
  grant remain ineligible with an explicit reason
- the app-first account must first link Telegram
- reward validation then checks membership in the configured public channel
- active public channel: `@pokrov_vpn`
- `@pokrov_vpnbot` is an administrator in that channel

### Promo And Referral Bonuses

- a referred friend receives no days for install, registration, trial
  activation or connection evidence, then receives `+5 days` once after their
  first successful provider payment
- the referrer receives `+10 days` once after that first successful payment and
  a full `72 hour` hold
- client events, admin gifts, and later renewals cannot release these day grants
- app-first bonus summary, referral summary, and promo-code redemption are backend-owned API contracts
- the app may redeem promo codes through the unified code entry or the bonus promo endpoint
- the app may show referral code, safe Telegram referral link, and copy/share/open actions from the referral summary contract; referral anti-abuse and bonus granting stay backend-owned
- bonus history is an app-safe backend contract and must show only compact reward events, not raw subscription links, full promo codes, tokens, or backend event metadata
- app surfaces may render only enabled operator-authored promo slots from
  `GET /api/client/promo-slots?surface=app`; unsafe links, third-party ad SDKs,
  external tracking media, and hidden executable payloads remain forbidden.
  Owner-uploaded media is served from the POKROV API only; a creative may be
  copy-led or media-only, static/animated/video, temporary with countdown, and
  dismissible or mandatory. Mandatory never means overlaying the VPN control
  or system navigation
- the paid roulette is enabled by default with a backend-owned `14 day`
  cooldown; the calendar remains independently disabled by default. The app
  shows a control only from backend summary state and may run it only when
  `eligible` and `can_spin` / `can_checkin` are both true

### Paid Subscriber Rewards

- eligibility requires an active canonical account, an active `PAID` user
  projection, and a currently active non-reversed `paid_access` grant from
  provider-payment or compatibility-projection authority
- trial, free access, bonus-only access, an expired paid interval, and a reward
  tail after paid expiry are ineligible even when the projected expiry remains
  in the future
- the fortnightly wheel exposes possible `1`, `3`, `7`, and `30` day rewards
  plus one-use `5%`, `7%`, and `10%` standard-plan discounts; sector size and
  order are not probabilities, rewards never stack over an existing pending
  wheel discount, and public/support copy must not publish backend weights
- the activity calendar grants `+1 day` only at consecutive-day milestones
  `7`, `14`, `21`, and `28`; a missed day starts a new cycle
- reward state belongs to the canonical account, awarded duration belongs to
  typed entitlement grants, and panel synchronization is a durable retryable
  job; legacy `RewardClaim`/achievement rows are compatibility evidence only
- `BONUS_WHEEL_ENABLED` and `BONUS_CALENDAR_ENABLED` remain independent kill
  switches; wheel defaults on and calendar defaults off. Public availability copy has a separate build-time gate,
  `NEXT_PUBLIC_PAID_REWARDS_MARKETING_ENABLED`, and must remain absent until the
  deployed backend has been enabled and verified

### Official Telegram Surfaces

- main bot: `@pokrov_vpnbot`
- support bot: `@pokrov_supportbot`
- feedback bot: `@pokrov_feedbackbot`
- news channel: `@pokrov_vpn`
- legacy usernames `swazist_bot` and `portal_service_bot` are officially disabled and must not be documented as active product surfaces

### Campaign Entry Policy Without App Stores

POKROV keeps both the site and Telegram bot, but they serve different intent.
The default paid-ad destination is the mobile site because it can explain the
product, show the official signer/download source and record an anonymous
funnel step before asking for identity. Telegram is the preferred conversion
entry when the campaign already carries a promo/referral intent or when the
user expects an account-bound continuation.

- broad product/search traffic -> `https://pokrov.space/`;
- explicit Android or Windows install intent -> the matching platform state at
  `https://pokrov.space/install/`, with ARM64 recommended first on Android;
- promo, referral and account-bound campaign -> an admin-generated
  `https://t.me/pokrov_vpnbot?start=...` link; the bot binds the intent before
  it offers checkout, download or cabinet continuation;
- known-user renewal or return -> the authenticated cabinet subscription/task
  route, with normal login recovery when the session is absent;
- help intent -> searchable public guides first, then
  `@pokrov_supportbot` for a new human ticket when self-service is insufficient;
- an in-app remote campaign -> only its approved POKROV HTTPS or Telegram
  target, never an arbitrary executable, tracking pixel or public checkout
  ticket.

Public ad links may carry only coarse `utm_source`, `utm_medium`,
`utm_campaign`, `utm_content`, platform and plan intent. They must not contain
Telegram IDs, account/device IDs, emails, activation keys, subscription URLs,
checkout tickets or raw IP data. Bot `start` payloads stay sanitized and within
Telegram's length limit; raw payloads are not retained in analytics. A public
campaign cannot mint a user-bound checkout ticket, so an unbound checkout CTA
must fall back to the bot or authenticated cabinet rather than pretending that
payment can continue anonymously.

Every campaign must have an owner, audience, truthful offer, start/end,
destination, safe fallback and measurement key before activation. Pausing or
expiring a campaign must leave the normal site/install path usable; disabling
an app banner must remove the slot without an empty placeholder or an app
update.

App campaign measurement is first-party only: `impression`, `click`,
`dismiss`, and `expired` use the approved slot/content/placement identifiers.
The campaign system does not receive an advertising identifier, installed-app
inventory, third-party SDK payload, or browsing history.

### Post-Trial Access Model

- consumer `free_monthly`, `free_standard`, and `free_soft` delivery is retired;
  those names remain rollback/cleanup compatibility only and must not be offered
  or provisioned for a new expired account
- an expired account retains recovery, support, history, devices and purchase
  continuation but receives no delivery node until new premium authority exists
- `paid` remains unlimited traffic with up to `5 devices`
- all active, non-hidden RUB plans with positive `amount_rub` are eligible for hosted checkout after the payment gate; frontend checkout must not keep a stale one-plan allowlist
- anonymous paid checkout is claimable by the same verified email account in either payment/attach order; this backend slice does not yet expose the OTP claim UI or public claim endpoints
- one provider order can create at most one paid grant and one linked fallback key across callback retries or different provider event IDs; automatic claim and later fallback-key redemption cannot stack the same purchase twice
- a pre-existing paid-order key is linked to its existing unredeemed, plan-matching, system-created GiftCard instead of duplicated; a user/admin-created, redeemed, mismatched, or already-owned card requires manual review and cannot transfer or add access
- a payment-linked key redeems from the purchase claim's saved plan and duration even when that plan has since been removed or renamed in the live catalog; unrelated legacy gift cards keep their existing catalog rules
- existing payment claims use their saved buyer email, plan, and duration for every paid callback event; later catalog removal, rename, or duration changes cannot downgrade a fulfilled account claim or an emailed fallback to manual review, while orders without a claim still require a current supported plan
- fallback email delivery is retryable until delivery evidence is stored; the durable purchase claim/key survives relay failure, and an already recorded successful delivery is not resent
- successful fallback delivery evidence is monotonic and cannot be downgraded by a later failure; bot success/denial analytics stores only a non-secret code preview, fingerprint prefix, and length
- a refund or chargeback that commits while fallback email is in flight remains authoritative: later transport evidence cannot replace reversal state, the paid receipt terminates without reporting access, and replay does not resend
- the linked claim and GiftCard are the only durable fallback-key authority; payment order/callback audit JSON does not retain a second raw-key copy, and redemption/status responses continue to use the saved purchase plan and duration after catalog changes
- a wrong-account key redemption cannot put an already owned claim into manual review or prevent the rightful owner from redeeming it
- paid callbacks use the owner saved when the order was created; callback-supplied Telegram identity cannot adopt an anonymous order or transfer an account-bound purchase, and conflicts require operator review without access issuance
- callbacks for one provider order serialize on the shared order row even when event IDs differ; refund and chargeback first enter durable pending reconciliation, then reverse the linked paid grant and recompute account access; paid fulfillment reacquires and refreshes that lock after a missing-user bootstrap rollback, so a reversal committed in the gap cannot issue access or be overwritten; outstanding reversal attention remains global across reporting periods, uses indexed status candidates plus conservative root-state verification, and orders fresh reversals by their safely parsed recorded time rather than the original purchase time; missing grant/key links remain terminal operator-visible manual review rather than reporting success or retrying forever, and late pending, failed, or cancelled callbacks cannot downgrade an already-paid order
- payment order and event audit metadata is structurally bounded as valid JSON; oversized callback fields become redacted summaries/fingerprints while authoritative fulfillment, reversal, pricing, buyer/order state, and fixed processing evidence remain parseable, and raw activation keys or callback secrets are not retained
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
- public `VPN` / `ВПН` copy drifting from useful visible SEO/search-intent language into hidden text, cloaking, stuffing, fabricated rankings, unqualified superiority, or unsupported availability claims

## Protection, Trust And Guide Surfaces

The public site and cabinet now share one versioned trust/guide catalog. Public
routes cover service status, transparency, privacy fields, responsibility,
fallback clients, programs, and searchable step-by-step guides. The cabinet
adds authenticated Protection, Guides, Devices/Pairing, Programs, Rewards, and
incident/referral context without pretending to control the local tunnel.

Public trust language is deliberately narrow:

- POKROV does not claim to store visited-site history;
- fields that are stored are listed with purpose, retention, and deletion path;
- client, platform, provider, and user responsibilities are separated;
- fallback software still uses official App Store client pages. A temporary
  App Store Account source may be offered manually when available as a
  voluntary best-effort workaround, never as part of the tariff or an SLA.
  The preferred route is a user-owned Apple Account for the required region.
  The verified external-source directory distinguishes free shared access
  (a live temporary competitor-issued account at `vanyavpn.app/ios`,
  `familypro.io`, and the free section at `izakstore.ru`), paid installation
  help (`happplus.com`), paid app catalogs (`appstops.ru/catalog`,
  `izakstore.ru`) and a paid private regional account (`wokerhome.com`). The free
  `appstops.ru/accounts/` giveaway was inactive on 2026-07-23 and is a status
  monitor, not an available source. Credentials remain on external pages and
  must not be requested, parsed, proxied or copied into POKROV source, static
  content, logs or cache. POKROV does not claim a control purchase, external
  inventory or refund handling. The public guide embeds Apple’s current
  short country/region-change flow and clearly labels the public Kazakhstan
  field values copied from VanyaVPN as example placeholders that Apple may
  reject or replace with a valid-payment requirement.
  Availability, lifetime, recovery, updates and replacement are not
  guaranteed. A shared account must be used only through the profile inside
  the App Store application, never through system Apple Account/iCloud
  settings, with no payment data or purchases and immediate sign-out after
  installation;
- status and compensation come from operator-owned incident records, not user
  complaints or marketing copy.

The guide catalog is task-based. The current registry contains 46 summaries and
46 detail records. Every published card has prerequisites, numbered steps,
expected result, a failure branch, supported platform/version, last-verified
date, and a visual target naming the client, screen and exact control.
Fallback-client records may additionally define immediate recommended setup,
button-by-button behavior, explicit warnings, and a current official source.
The matrix covers POKROV, Hiddify, Happ, v2rayN, v2rayNG, Streisand, V2Box,
Shadowrocket, and the not-yet-published owned Apple lane; only Hiddify is
labelled as the verified manual fallback, while every other third-party path
keeps its best-effort or advanced qualifier.

`/guides/pokrov-app/` is the separate Android application atlas. Its primary
Home, Locations, Rules, Profile, and Notifications images are current real
Huawei captures from the production-signed `1.0.6` candidate; remaining
task-specific panels retain real ADB captures until refreshed. Each image has hollow numbered target outlines
and a separate legend, so annotations never cover the control text. The atlas
covers the four main surfaces plus protection/recovery, routing, DNS/LAN,
trusted Wi-Fi, Always-on handoff, account, subscription, activation,
notifications, theme, diagnostics, and rewards. System Android pages, cabinet,
and payment remain labelled external handoffs rather than simulated POKROV
ownership.

Short emulator/device videos follow the same guide IDs and must be recorded
from a clean profile with tokens, account data, raw configs, IPs, and
notifications removed.

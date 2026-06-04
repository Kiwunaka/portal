# POKROV System Overview

Last updated: 2026-05-15

## Document Status

This file is living source of truth for the platform architecture map.

## Purpose

`POKROV` is a platform composed of:

- a Python backend and Telegram control plane
- a user cabinet and admin web surface
- a marketing and legal site
- a dedicated active client repo at `C:/Users/kiwun/Documents/ai/POKROV-app`
- a retained `app-next/` bootstrap archive/reference lane
- a retained legacy client rollback/archive reference lane
- operational scripts for deployment, node management, and release flow

## Wave 0 Rework Target

The new target architecture for the global rework freezes these boundaries before later code waves land:

- platform truth remains in this root repository
- `POKROV-app/main` is the only active client development and client-doc truth, with local checkout path `C:/Users/kiwun/Documents/ai/POKROV-app`
- `app-next/` is the retired bootstrap-source archive/reference workspace for that repo after the initial local snapshot landed
- `external/client-fork/app/` is the retired rollback/archive client reference workspace
- the front-end rebuild is an atlas-driven shell reset: acquisition lives on `marketing/`, continuation lives on `webapp/`, and the app shell is locked to `Protection / Locations / Rules / Profile`
- one app-first account becomes the identity root for `install_id`, email, Telegram, devices, and activation keys
- public acquisition, pricing, and paywall move entirely onto `marketing/`, with trial, install, and first connection as the primary public CTA path and checkout as explicit continuation, while `webapp/` becomes session-aware continuation, redeem, support, renewal continuation, and admin only
- public browser copy and visual governance are centralized through `shared/copy.ts`, `copy/catalog.ru.json`, and `shared/design-tokens.json`, with locked host and product facts inherited from the shared fact files
- user-facing cabinet IA is `Dashboard / Subscription / Devices / Statistics / Support`, with `downloads`, `redeem`, and hosted-checkout continuation treated as task routes rather than parallel acquisition surfaces
- commerce moves to hosted checkout plus activation-key issuance and redemption instead of raw subscription-link-first UX
- remote promo content is limited to approved first-party promo slots; third-party ad SDKs remain out of scope
- the public location story collapses to one logical location per user, while the transport matrix stays hidden behind rollout, diagnostics, and admin controls

Reference-lane note:

- `app-next/` and `external/client-fork/app/` may still be consulted for archived bootstrap or rollback evidence
- those retained workspaces do not override the active architecture truth in `POKROV-app/main`

## Main Components

### Control Plane

- `portal_bot/api.py`
  FastAPI backend for health checks, app-first session bootstrap, payments, bonuses, tickets, public data, public reviews, and admin APIs.
- `portal_bot/app_first_service.py`
  Bounded app-first/session helper used by the API for trial bootstrap, session payload shaping, and Telegram link start context.
- `portal_bot/web_auth_service.py`
  Bounded browser-auth helper used for Telegram web login, additive email verification/recovery, session issuance, and checkout handoff tokens.
- `portal_bot/channel_bonus_service.py`
  Bounded Telegram bonus helper used by the API for read-only subscriber checks and explicit claim flow.
- `portal_bot/bot.py`
  Main Telegram bot for billing, campaigns, referrals, review moderation, and operator actions.
- `portal_bot/helpbot.py`
  Dedicated support bot.
- `portal_bot/support_ai_service.py`
  Optional server-side AI helper for text-only support hints in `@pokrov_supportbot` and ticket API flows; disabled by default and backed by sanitized shared support knowledge.
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
- transport rollout uses a per-node catalog so a node can carry `legacy_reality_fallback`, `grpc_443_primary`, hidden reserve `reserve_xhttp_cdn`, emergency `ru_bridge_relay`, and operator-only `operator_lab` entries side by side
- `nodes.transport_profiles_json` is the canonical per-node transport catalog; legacy inbound fields such as `inbound_id`, `vless_port`, and `reality_*` remain compatibility input and are synthesized into `legacy_reality_fallback` when the catalog is empty
- `AppSetting.network_rollout_config` is the operator-controlled rollout policy for transport, DNS, routing, and operator lab allowlists, and it is exposed through admin GET/PUT endpoints
- `network_rollout_config` is a JSON policy blob with `version`, `defaults`, `carrier_overrides`, `cohort_overrides`, `reserve_xhttp_cdn`, `ru_bridge_relay`, `operator_lab`, `package_catalog_feed`, `routing_rules_feed`, and `support_recovery_order`
- `defaults` normally pin `routing_mode_default=all_except_ru`, `transport_profile=legacy_reality_fallback`, and `dns_policy=ru_direct_split`; the owner-approved `2026-06-01` incident posture may promote `transport_profile=ru_bridge_relay` while keeping `legacy_reality_fallback` as the rollback target
- dormant reserve transport metadata also lives in rollout config and node catalogs under `reserve_xhttp_cdn`; it stays disabled by default and becomes active only through explicit rollout allowlists
- `ru_bridge_relay` is the owner-approved `2026-06-01` emergency profile: the app receives a sing-box manifest where the top selector lists countries and each non-US country contains nested `Обычный` and `Белые списки` choices; `us` remains available only as a normal direct target
- rollout overrides may only change `transport_profile`, `dns_policy`, `routing_mode_default`, and `ip_version_preference`
- `operator_lab` stays allowlist-only and carries `enabled`, `allowlist_install_ids`, `allowlist_tg_ids`, `allowlist_node_codes`, and `expires_at`
- app-managed session/profile payloads resolve their transport profile from rollout policy, while manual/export compatibility links stay on `legacy_reality_fallback` until a separate share-link parity wave
- `GET /api/client/profile/managed` is the primary app-managed provisioning endpoint and returns `version`, `profile_revision`, `transport_profile`, `transport_kind`, `engine_hint`, `config_format`, `config_payload`, `fallback_order`, `support_context`, and `smart_connect`
- `smart_connect` contains a rollout-compatible shortlist, rejection counters, scoring hints, and stickiness metadata so the client can combine real RTT with backend health/load signals without guessing
- `POST /api/client/nodes/latency-samples` stores install-scoped RTT samples plus carrier/platform context for admin visibility and later shortlist stickiness
- additive `client_policy` fields `transport_kind`, `engine_hint`, and `profile_revision` let the client apply the right engine/runtime without guessing
- one logical client is synchronized across all enabled inbounds in a node's transport catalog, while public UI still exposes only the rollout-selected app-managed path
- `reserve_xhttp_cdn` is prepared as a hidden reserve profile; when explicitly selected it resolves to `transport_kind=xhttp` with `engine_hint=xray`, while the normal consumer baseline stays `sing-box`
- `ru_bridge_relay` resolves to `transport_kind=ru_bridge` with `engine_hint=singbox`; it is not a normal delivery-node pool and does not make `mini` a control-plane host

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
- `C:/Users/kiwun/Documents/ai/POKROV-app/`
  canonical active client repo for new Android and Windows product-direction work
- `app-next/`
  retired bootstrap-source archive/reference workspace for the client migration
- `external/client-fork/app/`
  retired rollback/archive reference client, with some legacy `POKROV VPN` identifiers still present for compatibility
- `shared/`
  shared public copy, canonical hostnames, product facts, and design tokens

Current public-surface split:

- `marketing/` owns the homepage, public `/checkout/` pricing/paywall flow, offer/privacy pages, indexable SEO landings, and metadata assets such as `robots`, `sitemap`, `manifest`, Open Graph, Twitter, and JSON-LD
- current canonical indexable entry routes are `/mobile/`, `/tiktok/`, `/youtube/`, `/devices/`, and `/telegram/`, with permanent redirects from the earlier legacy SEO slugs
- public marketing CTA priority is app-first trial, install, and first connection; checkout, install help, and cabinet-open flows remain explicit exits for known intent
- `webapp/` owns browser entry, dashboard, subscription, devices, statistics, support, task routes such as downloads, redeem, and hosted-checkout continuation, compatibility redirects for older cabinet routes, and the primary admin operator surface
- `webapp/` browser entry is a continuation router for app handoff, Telegram login, and email login when delivery readiness is green
- `/pricing/` in `webapp/` is compatibility-only continuation that now redirects to `/subscription/` and must not drift back into a public acquisition surface
- `connect.pokrov.space` stays outside the marketing/cabinet storytelling layer and remains the config-delivery host for the one public connection link plus QR; it serves the rollout-selected app-managed profile, with `legacy_reality_fallback` as the baseline until canary cohorts flip to `grpc_443_primary`

Client release safety rule:

- Android and Windows remain the public `v1` target pair
- Android must not be released as publicly safe until release-build verification proves that localhost proxy, DNS, command, and admin surfaces are not exposed without acceptable protection

Admin ownership rule:

- `webapp` is the primary admin surface for user, node, ticket, and metrics work
- Telegram admin in `portal_bot/bot.py` is fallback/emergency tooling and must follow the same user-status semantics as web admin
- `/api/admin/summary` is the operator truth snapshot for entitlement counts, install-backed activity, observer-backed activity, and data-quality status badges

Public connection delivery rule:

- `subscription_url` is generated by the backend and points to `https://connect.pokrov.space/s8Kx2mP7qR4wT/{token}`
- `connect.pokrov.space` serves the rollout-selected app-managed profile and keeps `legacy_reality_fallback` as the baseline until canary cohorts are explicitly enabled for `grpc_443_primary`
- legacy `api.pokrov.space/s8Kx2mP7qR4wT/{token}` remains compatibility-only for older imports
- explicit manual/recovery UX may expose one connection link and one QR, not separate smart/plain links; first-layer consumer screens should prefer app install, reconnect, route-mode change, checkout, and support

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
- cross-surface public facts from:
  - `shared/product-facts.json`
  - `shared/public-urls.json`
  - `shared/design-tokens.json`
- active client-repo truth from `POKROV-app/main`

Not source of truth:

- local SQLite files
- archived test DBs
- audit snapshots
- generated frontend caches
- stale root markdown notes
- retired client-reference workspaces when treated as if they were active client canon

## Transport Rollout Control

The additive rollout model keeps the current Reality path intact while introducing a controlled app-first primary path.

Rollout rule:

- `legacy_reality_fallback` stays the rollback and manual/export baseline transport profile
- `grpc_443_primary` is the new app-first primary profile for allowlisted cohorts and premium-node canaries
- `reserve_xhttp_cdn` is the hidden reserve profile prepared on eligible nodes for emergency allowlisted fallback; it is not part of the default public rollout in this wave
- `ru_bridge_relay` is the RU reachability bridge for allowlisted, incident-promoted, or temporary default cohorts; it exposes countries first, then nested direct/`Белые списки` choices through `mini` for non-US targets, while US stays direct-only
- `operator_lab` stays hidden behind allowlists and must not appear in public UI or mass session payloads
- `Naive`, `Trojan`, and `Hysteria2` are not part of the mass public payload for this wave

Operational shaping rule:

- repo-truth for node shaping lives in `infra/node-qdisc-profiles.json`
- `scripts/remote_apply_node_qdisc.py` applies and rolls back qdisc state
- `scripts/remote_node_qdisc_smoke.py` verifies that a heavy flow does not starve small HTTPS probes beyond the fixed threshold
- `infra/portal-node-qdisc.service` restores the configured qdisc after reboot

## Current Primary Flows

### App-First Client Flow

1. client generates `install_id`
2. user taps `Try free`
3. backend creates app account, device record, and app session
4. backend returns canonical `session`, `client_policy`, `access`, and `provisioning` payloads plus a real subscription source
5. client imports and activates the profile

App-first contract note:

- `client_policy` is the additive cross-surface contract for routing, DNS, transport, package-catalog version, and support recovery order
- the same `client_policy` shape should be available from `start-trial`, `dashboard`, and `user` payloads
- `client_policy` is populated from `AppSetting.network_rollout_config`, not from a hard-coded transport default
- public recovery order stays `POKROV app -> web cabinet -> Telegram fallback`
- managed provisioning also returns `smart_connect`, which gives the client a shortlist revision, scoring hints, and fallback metadata before it measures live RTT from the device
- the follow-up latency upload path is `POST /api/client/nodes/latency-samples`; those samples are diagnostic/operator truth and do not change the free-vs-premium pool rule

Route-mode continuation note:

- after provisioning succeeds, the client must still ask the user whether this device should optimize `all traffic` or `only selected apps`
- the saved per-device route policy should expose `route_mode`, selected app/package identifiers when applicable, and whether the chosen mode requires elevated rights on the current platform
- `Only selected apps` is a consumer split-tunneling choice, not a reason to surface raw proxy or service toggles in first-layer UI

### Web Identity And Session Continuation Flow

1. user opens marketing or cabinet in the browser
2. browser continues from an app handoff, Telegram OIDC, or email auth when delivery readiness is green
3. backend issues a browser session with `auth_origin` and linked-identity summary
4. cabinet, support, renewal, and checkout continue from that same session

Architecture rule:

- additive email auth is a live continuation lane only while sender identity, delivery configuration, and delivery confirmation are green
- app handoff, Telegram, and email are the active browser-continuation entry families today when their readiness checks are green
- Telegram WebApp `initData` is a bounded handoff credential only: the API verifies the HMAC and rejects missing, future, or older-than-`TELEGRAM_WEBAPP_INIT_MAX_AGE_SECONDS` `auth_date` values before treating it as a session or invalid-browser-token fallback
- email must land in the same cabinet session and linked-identity model rather than becoming a separate account track
- public email auth depends on external transactional mail delivery and verified sender identity
- if readiness fails, browser email entry must return to a truthful unavailable state instead of promising working verify or reset mail
- cabinet entry copy should continue the shared product story rather than re-pitching the product like another landing page
- cabinet and admin shells must keep explicit navigation back to the marketing site and standard cabinet entry

### Telegram Linking And Reward Flow

1. app-first account requests Telegram linking
2. backend issues a deep link to `@pokrov_vpnbot`
3. bot links Telegram identity to the app-first account
4. app or web surfaces may call read-only subscriber status check
5. reward grant still happens only on the explicit claim API
6. backend validates membership in `@pokrov_vpn`
7. backend grants `+10 days` when eligible

### Checkout Continuation Flow

1. user opens public pricing or renewal continuation from marketing, webapp, or bot
2. hosted checkout sells an activation key against the canonical catalog
3. user redeems that key in the app or `webapp`
4. managed premium is refreshed on the canonical app-first account

Architecture rule:

- `marketing` owns public pricing and acquisition
- `webapp` renewal remains continuation-only and should defer to the same hosted key-first flow
- bot purchase flow remains valid, but it does not replace app-first public onboarding
- raw subscription links stay manual-recovery-only and must not reappear as the default commerce story
- payment callbacks normalize signed provider events into local statuses before fulfillment; only `paid` result events can extend access, while `failed`, `cancelled`, `refunded`, `chargeback`, `pending_verification`, and `manual_review` remain admin-visible reconciliation records without automatic access extension

### Public Web Journey

1. user lands on `https://pokrov.space/` or an indexable marketing landing page
2. marketing CTA defaults into `pokrov.space/checkout/`, while install help and cabinet entry stay secondary intent-driven exits
3. public checkout sells an activation key and sends the user toward redeem or install continuation
4. a known browser session, email auth, or app/bot handoff continues in `https://app.pokrov.space/`
5. `webapp` renders the relevant cabinet flow such as dashboard, subscription, redeem, downloads, devices, or support
6. successful redeem or renewal returns the user to the active cabinet journey

Public web rule:

- `marketing/` is the indexable discovery layer
- `webapp/` is the authenticated or session-aware continuation layer, not a second public acquisition page
- authenticated app, bot, and cabinet download payloads should resolve runtime `APP_*` values through `/api/client/apps`
- marketing download CTA, metadata icons, favicon, and share-preview assets are build-time outputs and must be rebuilt or redeployed when public release URLs or derived brand assets change
- public SEO pages may vary the entry copy, but they must not create separate product rules or bypass the canonical checkout/session model

### API-Only Regression Flow

Release validation now includes a scripted API-only lifecycle contour:

1. start trial through `POST /api/client/session/start-trial`
2. load dashboard and profile snapshots
3. fetch config from `connect.pokrov.space`
4. create support ticket through `/api/tickets`
5. exercise bonus flows such as channel claim, promo redeem, gift redeem, and referral linkage
6. create a checkout order and simulate provider callback success
7. confirm renewal state, audit trail, and post-payment dashboard visibility

This contour is observe-and-verify only. It does not change cashier UI design, but it keeps backend purchase contracts trustworthy across bot, site, and app.

### Support Flow

1. user opens support from app, WebApp, or helpbot
2. the platform stores or routes the support thread
3. when enabled, `portal-api` or `portal-helpbot` may add a redacted AI hint from `shared/support-ai-knowledge.json` as sender role `assistant`
4. operator responds through the current support tooling; the AI hint does not close or resolve the ticket

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
  dedicated RU probe vantage point plus owner-approved emergency RU bridge endpoint for non-US delivery reachability
- `rf1`
  reserve RF ingress for operator and VIP/manual access, chained onward to an EU exit

RF host rule:

- do not place control-plane services on `mini` or `rf1`
- keep `rf1` outside the default runtime delivery pool in phase 1
- `rf1` promotion remains in backlog
- owner-approved exception on `2026-06-01`: `mini` may run `ru_bridge_relay` on `tcp/443` as an emergency bridge to enabled non-US POKROV delivery nodes; keep it out of the standard delivery pool, keep US excluded, and keep a rollback path that disables the rollout profile without touching normal Reality delivery
- owner-approved exception on `2026-04-24`: the dedicated free node (`151.245.217.23`) runs `portal-mtproto.service` as a Telegram-only MTProto proxy on `tcp/9443`; it is not a new generic delivery role and must not displace the node's normal `x-ui` listener on `tcp/443`

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

- new public and cabinet copy plus CTA text must stay centralized through `shared/copy.ts` and `copy/catalog.ru.json`; `webapp` should continue that shared story instead of inventing its own marketing voice
- locked cross-surface facts such as trial length, Telegram reward, canonical hosts, and design direction must stay centralized through `shared/product-facts.json`, `shared/public-urls.json`, and `shared/design-tokens.json`
- app-first marketing CTA priority, live/degraded email wording, and cabinet IA labels must resolve from those shared governance sources instead of drifting per surface
- public-facing marketing and cabinet language should stay calm and human-readable instead of surfacing transport acronyms, raw profile terms, or operator-facing implementation jargon
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

Current release validation also has to correlate:

- client localhost-listener security smoke
- routing preset smoke for `Full tunnel` and `Все, кроме РФ`
- DNS split and leak checks
- three-vantage node checks from current operator origin, `brain`, and an RU-origin probe when available

Dashboard and user-cabinet traffic visibility must come from server-side node runtime snapshots rather than app-only telemetry.

- current traffic usage should prefer live panel/runtime counters aggregated across the user nodes
- current connection count should prefer runtime connection evidence such as active IP counts or active nodes
- the cabinet/admin subscription-sharing proxy metric should be described as an estimate, not a people counter: it is derived from live IP activity and capped by recent unique IP evidence so operators can distinguish likely people-sharing from raw connection fan-out
- app device records remain useful, but they are a separate app-first visibility layer and must not be shown as the only source of "connected devices"

Admin funnel visibility uses two data families:

- anonymous public-site events in `funnel_events` for page entry and CTA intent, stored without IP address or user-agent retention
- known user and payment events from `events`, `pay_attempts`, and `external_orders` for cabinet/bot open, checkout start, paid confirmation, and connection confirmation

This funnel is an operator diagnosis surface for “where did people stop?” and must not replace signed payment callbacks, fulfillment records, or Postgres entitlement truth.

Required external geography check:

- run an RU-based external probe every `6 hours`
- verify the probe host itself can reach `google.com`
- verify the current `POKROV` public hosts and API health from that external RU vantage point
- verify the current `POKROV` delivery nodes remain reachable from that external RU vantage point
- verify the RF reserve ingress state:
  - `xhttp_alive`
  - `hysteria_alive`
- keep the RU-origin release verdict limited to POKROV public hosts, API health, delivery-node reachability, and reserve ingress checks

This gives operators a useful distinction between:

- a broken probe host
- a broken node or public edge
- a hostname migration issue where legacy compatibility paths still work but canonical `pokrov.space` paths do not
- a reserve path that still works for operator and VIP access while canonical paths fail

Probe-readiness rule:

- `mini` is the preferred RU probe origin when it is healthy
- `mini` is not guaranteed to be available at all times
- RU-origin observability remains incomplete until `mini` or a replacement RU host is working again

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
- linked email identity when present
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
- `GET /api/public/catalog`
- `POST /api/auth/telegram/web-login`
- additive email-auth rollout endpoints under `/api/auth/email/*` for register, verify, login, recovery, and reset
- `POST /api/client/session/start-trial`
- `GET /api/access-keys/status/{key}`
- `POST /api/access-keys/redeem`
- `POST /api/admin/access-keys/issue`
- `GET /api/client/promo-slots`
- `GET /api/admin/promo-slots`
- `PUT /api/admin/promo-slots`
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
- email-auth register / verify / login
- Telegram OIDC start and finish
- bot token handoff into webapp
- `GET /api/client/apps`
- `GET /api/payments/providers`
- checkout continuation from session or ticket

## Telegram Registry

Canonical bot usernames:

- main bot: `pokrov_vpnbot`
- support bot: `pokrov_supportbot`
- feedback bot: `pokrov_feedbackbot`

Current channel state:

- verified public channel: `@pokrov_vpn`
- bonus verification is live
- `@pokrov_vpnbot` is an administrator in that channel
- `swazist_bot` and `portal_service_bot` are legacy usernames that are officially disabled and must not be treated as active production bots

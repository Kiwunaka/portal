# App-First And Bonus Flows

Last updated: 2026-04-24

## Document Status

This file is living source of truth for app-first identity, Telegram linking, and Telegram reward logic.

## Goal

Document the current app-first identity model, automatic username sync path, checkout continuation, node-pool assignment, and the live Telegram bonus flow used by the active `POKROV-app/main` client line, with legacy `POKROV VPN` labels treated as compatibility or archival leftovers only.

## Wave 0 Rework Target

The rework canon now freezes the following target identity and access model for later code waves:

- `POKROV-app/main` is the only active client lane expected to implement this contract family
- `app-next/` and `external/client-fork/app/` are retired bootstrap or rollback references only and must not override the active contract
- one canonical `app-first` account links `install_id`, email, Telegram, devices, and activation keys
- store-app entry remains the premium-trial path: the first valid device gets `5 days` of premium trial without mandatory registration, then downgrades to `free_monthly`
- public site/bot trial-key entry may issue one practical `5-day` activation key per browser/IP period without registration; user-facing status is limited to `issued`, `limited`, or `unavailable`
- site email signup remains a planned browser continuation lane marked `soon`; until launch it must not be described as a live public parity path or a premium-trial path
- browser continuation currently starts from app handoff or Telegram; email joins that same cabinet session family only after the marked-`soon` launch goes live
- Telegram is recovery, linking, restore-premium, bonus, community, support fallback, and bot-side fallback commerce, not the primary login or commerce wall
- commerce becomes `buy key -> redeem key -> managed premium`, with raw subscription links hidden from default UX and exposed only for explicit recovery/manual flows
- free-tier policy is fixed to `NL-free`, `5 GB / 30 days`, `50 Mbps per IP`, `1 device`, with monthly reset
- `GET /api/dashboard`, `GET /api/user/*`, `POST /api/client/session/start-trial`, and `GET /api/client/profile/managed` should converge on one linked-identity and access-state contract that also carries redeem eligibility, promo-slot payloads, and the hidden transport matrix
- normal consumer UI shows one logical location; ordered transports such as `vless_reality -> vmess -> trojan -> xhttp` remain hidden rollout detail rather than mass-UI choice

Client-canon note:

- this document describes the active contract that `POKROV-app/main` must implement
- any retired bootstrap or rollback docs that still describe older surfaces are reference-only and must not override this contract

## App-First Trial Flow

1. client creates and persists `install_id`
2. client collects soft device context
3. user taps `Try free`
4. client calls `POST /api/client/session/start-trial`
5. backend creates:
   - app account
   - device record
   - app session
6. backend returns:
   - `session` payload with canonical session fields
   - `client_policy` payload with routing, DNS, transport, and recovery defaults
   - `access` payload with enforced `5-day` trial state
   - `provisioning` payload with explicit readiness state
   - experience payload
7. client silently imports the profile
8. client asks how this device should be optimized before the first live route activation
9. client saves the per-device route policy and then switches to `Quick Connect`

Contract rule:

- caller-controlled `trial_days` is no longer part of the canonical client contract; the backend always enforces the fixed `5-day` trial from shared truth
- the backend must return the same `client_policy` contract from `start-trial`, `user`, and `dashboard` flows so the app can reconcile defaults without guessing
- key-first trial starts from the site, bot, or app; all entrypoints must converge on the same app-first session, device, and access state before showing a working profile

Current `client_policy` contract:

- `routing_mode_default`: `all_except_ru`
- `transport_profile`: `legacy_reality_fallback`
- `transport_kind`: `reality`
- `engine_hint`: `singbox`
- `profile_revision`: rollout-derived profile revision string
- `dns_policy`: `ru_direct_split`
- `route_mode_default`: `all_traffic`
- `route_mode_choices`: `all_traffic`, `selected_apps`
- `route_mode_requires_elevation`: platform-specific elevation hint for the default or chosen route mode
- `route_mode`: persisted current per-device route mode
- `selected_apps`: persisted package/process identifiers for the current split-tunnel choice
- `requires_elevated_privileges`: persisted current elevation requirement for the chosen route mode
- `route_policy.mode`: normalized mirror of the current `route_mode`
- `route_policy.selected_apps`: normalized mirror of the current `selected_apps`
- `route_policy.requires_elevated_privileges`: normalized mirror of the current elevation requirement
- `route_policy.capabilities.selected_apps`: scan support, max selected-app count, max identifier length, capability revision, and updated timestamp
- `package_catalog_version`: versioned Android direct-app catalog stamp from shared facts
- `ruleset_version`: versioned routing/ruleset stamp from shared facts
- `support_context.transport`: `legacy_reality_fallback`
- `support_context.routing_mode`: `all_except_ru`
- `support_context.ip_version_preference`: `ipv4_only`
- `support_recovery_order`: `app`, `web`, `telegram`

First-run route-mode choice:

- the client must show exactly two first-layer consumer choices: `Оптимизировать всё на устройстве` and `Только выбранные приложения`
- `Оптимизировать всё на устройстве` is the default public path and stays `TUN`-first
- `Только выбранные приложения` is the selected-app scan MVP and must write per-device app/process selection state instead of revealing raw proxy or service controls
- the chosen mode must round-trip through backend-owned `route_mode`, `selected_apps`, and `route_policy.*` fields so `start-trial`, `dashboard`, and recovery flows all agree on the live device state
- invalid route modes must return `400` from `/api/client/route-policy` rather than being normalized to a default value
- Windows should use a known-app or executable picker; Android should use an installed-package picker
- the saved route-mode choice must remain editable later from a dedicated route-mode screen rather than only through hidden advanced settings
- the first layer must stay free of raw protocol, runtime-core, local-control, hostname, port, and subscription-internal terms; these details belong in diagnostics, advanced settings, or admin/support context

Final client MVP contract for the premium polish gate:

- app entry: `Try free` calls `POST /api/client/session/start-trial`, receives the unified session/access/policy family, and then moves the user to route-mode choice before the first live connect
- site or bot entry: trial-key issue and hosted checkout still redeem into the same app-first account model, not a parallel browser-only identity
- device state: `install_id`, friendly device name, platform, app version, route mode, selected apps, and elevation requirement are the shared support model across app, cabinet, and admin
- app IA: first layer remains `Подключение`, `Локации`, `Правила`, and `Профиль`; support, devices, tariffs, and settings stay nested under profile
- selected-app scan MVP: Android stores package identifiers, Windows stores executable/process identifiers, and both round-trip through `route_mode`, `selected_apps`, and `route_policy.*`
- public copy: app, cabinet, bot, and backend user-facing strings should say access key, app, cabinet, renewal, support, route mode, and location; raw profile/config, host, port, public IP, direct product `VPN` wording, and local-control terms are admin or diagnostics only

Rollout note:

- `AppSetting.network_rollout_config` resolves the transport profile for app-managed session and profile payloads
- `GET /api/client/profile/managed` is the primary app-managed provisioning endpoint and returns a manifest with `version`, `profile_revision`, `transport_profile`, `transport_kind`, `engine_hint`, `config_format`, `config_payload`, `fallback_order`, and `support_context`
- allowlisted carrier or cohort overrides may switch app-managed flows to `grpc_443_primary` without changing the public endpoint set
- managed provisioning now also returns a `smart_connect` contract with shortlist candidates, fallback metadata, rejection counts, and scoring hints
- manual/export compatibility links stay on `legacy_reality_fallback` until a separate share-link parity wave
- `subscription_url` remains a compatibility and recovery artifact for manual import, legacy browser-visible delivery, and fallback when the managed manifest cannot be fetched
- `network_rollout_config` carries `version`, `defaults`, `carrier_overrides`, `cohort_overrides`, `operator_lab`, `package_catalog_feed`, `routing_rules_feed`, and `support_recovery_order`
- `defaults` keep `routing_mode_default=all_except_ru`, `transport_profile=legacy_reality_fallback`, and `dns_policy=ru_direct_split` until canary approval
- overrides may only change `transport_profile`, `dns_policy`, `routing_mode_default`, and `ip_version_preference`
- `operator_lab` is allowlist-only and must stay out of public UI and mass session/profile payloads

Smart-connect contract:

- `GET /api/client/profile/managed` returns a shortlist revision plus `smart_connect.shortlist`
- premium users probe up to `5` eligible non-free nodes; free-tier users still probe only `NL-free`
- the shortlist rejects disabled, draining, unhealthy, stale, `cpu_percent >= 90`, transport-incompatible, and rollout-blocked nodes before the client starts RTT checks
- shortlist items expose `health_score`, `cpu_percent`, `panel_latency_ms`, `backend_penalty`, and `cpu_penalty`
- the client compares candidates with `effective_score = rtt_ms + cpu_penalty + backend_penalty`
- stickiness stays active with a `15%` threshold so the app does not flap between nodes on tiny wins
- explicit `UserNode` mappings still take precedence; the shortlist is built from the user-assigned node set first instead of bypassing that pinning
- the follow-up upload path is `POST /api/client/nodes/latency-samples`, which stores `install_id`, `carrier`, `platform`, accepted RTT samples, selected node, previous node, and whether stickiness was applied

## App Session Model

Important concepts:

- `install_id` is the stable client-side identifier
- device context supports diagnostics and abuse control
- app session token is used for subsequent app API calls
- Telegram is optional and not required for account creation
- backend device truth lives in `app_devices`, with one row per `install_id` linked to the app-first account
- legacy `users.app_*` fields remain only as a compatibility snapshot of the latest/current app device until every caller moves to the device service

## Preferred Device Identity Inputs

- `install_id`
- `device_name`
- `platform`
- `model`
- `app_version`
- soft fingerprint signal
- `last_ip`

This supports a friendlier device model than a Telegram-only account design.

Multi-device contract:

- `portal_bot/device_service.py` owns device upsert, list, rename, revoke, legacy backfill, and device-limit status helpers
- public device rows use the client-owned `install_id` as the external device identifier and must not expose database row IDs, `tg_id`, `sub_token`, raw config data, or `last_ip`
- public device rows may expose safe diagnostics: display name, reported device name, platform, OS version, app version, last seen time, route mode, selected-app identifiers, elevated-rights requirement, revoked state, and current-device marker
- `is_current` is request-scoped and resolved from the caller's current `install_id`; it is not a global account flag
- `display_name` is the user-editable label; `device_name` remains the last reported client device name
- revocation marks a device row revoked without deleting retained support context
- free, trial, and bonus access use the single-device policy; paid access resolves the active plan device limit and defaults to `5` when no plan row is available

## Username Sync Semantics

- app-first accounts may start with an app-side placeholder username before any Telegram identity is linked
- once Telegram or web-auth surfaces provide a real username, runtime flows should sync it automatically into the canonical account/session state
- automatic username sync is the primary path for normal operation, support context, and recovery continuation
- manual username sync remains compatibility/recovery tooling for operators and edge cases; it must not be treated as the normal happy path

## Visibility Expectations

For support and operations, the app-first account model should make it possible to inspect one connected story across:

- app account and session
- linked Telegram account when present
- device record and device name
- recent `last_ip`
- current subscription and node context

Visibility rule:

- Telegram remains optional for the user journey
- once linked, Telegram identity becomes part of the support and recovery context
- device and IP context should be used for diagnosis and abuse control, not as a public-facing marketing message
- install-scoped latency samples, carrier labels, and platform labels are operator-visible diagnostics for route quality and must not surface as raw telemetry in normal consumer UI

## Redesign-Safe Public Payloads

App, cabinet, and marketing UI may use additive backend summaries when they need truthful copy around public feeds or aggregate proof:

- `GET /api/public/live-updates` supplies short consumer-readable update cards and uses default copy only as a real empty-state substitute when no active update rows exist
- `GET /api/public/social-proof` returns existing aggregate counters plus `summary.source=backend_account_rows`, `summary.precision=aggregate`, and a Russian description that says the data is aggregate and personal data is not exposed

These fields preserve existing clients because they are additive. They do not change entitlement, subscription delivery, support, or Telegram reward behavior.

## Live App-First Endpoints

Current live backend contract:

- `POST /api/client/session/start-trial`
- `GET /api/client/profile/managed`
- `POST /api/client/nodes/latency-samples`
- `GET /api/public/catalog`
- `GET /api/public/trial-key`
- `POST /api/public/trial-key`
- `GET /api/access-keys/status/{key}`
- `POST /api/access-keys/redeem`
- `POST /api/admin/access-keys/issue`
- `GET /api/client/route-policy`
- `POST /api/client/route-policy`
- `GET /api/client/promo-slots`
- `GET /api/admin/promo-slots`
- `PUT /api/admin/promo-slots`
- `POST /api/client/telegram/link`
- `POST /api/channel/subscriber/check`
- `POST /api/bonuses/channel/claim`
- `GET /api/tickets`
- `POST /api/tickets`
- `POST /api/tickets/uploads`
- `GET /api/tickets/{ticket_id}`
- `POST /api/tickets/{ticket_id}/messages`

Related live surfaces also exposed by the backend:

- `GET /api/dashboard`
- `GET /api/user/{tg_id}`
- `GET /api/client/apps`
- `GET /api/payments/orders/status-public`
- `GET /api/nodes/status`
- `GET /api/bonuses`
- ticket endpoints under `/api/tickets`

Unified access-contract note:

- `GET /api/dashboard`, `GET /api/user/{tg_id}`, and `GET /api/client/profile/managed` now carry the same identity/access family additions: `linked_identities`, `free_caps`, `redeem_eligibility`, `promo_slots`, `hidden_transport_matrix`, and `location_matrix`
- the access-key redeem path returns the same access-state family so app, cabinet, and admin can refresh off one canonical contract
- consumer `/api/user/{tg_id}` callers should receive a safe `consumer_summary` plus route category and connect host while raw `subscription_url`, node `host:port`, and `last_ip` stay admin-diagnostic only

## Web Login, Email Auth, And Session Continuation

Web surfaces support app-first continuation through:

- app or bot handoff into an existing cabinet session
- Telegram widget or Telegram OIDC login in browser
- additive email signup, verification, login, recovery, and reset as a marked-`soon` browser lane rather than a live public default
- dashboard and checkout continuation from an existing web session

Contract rule:

- canonical API base is `https://api.pokrov.space/`
- canonical public config host is `https://connect.pokrov.space/`
- HTML responses from `app.pokrov.space` must never be treated as valid API JSON
- web login should continue the user into account or checkout, not into a dead-end landing
- app handoff and Telegram are the active browser-continuation entry families today
- additive email auth must stay marked `soon` until sender identity, delivery confirmation, and the public launch path are genuinely live
- once launched, additive email auth must issue the same browser session family used by the cabinet, checkout, and support flows while exposing `auth_origin` and linked-identity summary for support/admin visibility
- the additive email-auth rollout uses endpoint families under `/api/auth/email/*` for register, verify, login, recovery, and reset
- public email register, verify, and recovery should remain disabled or explicitly marked `soon` until transactional sender identity and delivery-confirmation/webhook visibility are live
- `/api/public/catalog` and session payloads should expose email-auth capability status so UI can render readiness without implying email login is already public
- browser entry screens in `webapp` are continuation-first and must not become a second landing-page pitch
- new user-facing `subscription_url` values must point to `connect.pokrov.space`
- legacy `api.pokrov.space/s8Kx2mP7qR4wT/...` remains compatibility-only for older imports and recovery cases
- the same `client_policy` contract still flows through `start-trial`, `user`, and `dashboard`, but the rollout policy behind it can vary by cohort without introducing a new endpoint

## Checkout Continuation

1. user opens public pricing, renewal continuation, or bot-side purchase
2. hosted checkout sells an activation key against the canonical catalog
3. guest order status can be checked through `GET /api/payments/orders/status-public`
4. paid guest success exposes an activation-key handoff for app or cabinet redeem
5. logged-in continuation may still direct-renew or apply access without breaking provider callback handling
6. the key is checked with `GET /api/access-keys/status/{key}` and then redeemed through `POST /api/access-keys/redeem`
7. the backend refreshes managed access on the same app-first account
8. app and web surfaces reload their unified access contract from the same identity root

Checkout rule:

- public pricing starts from checkout-first marketing surfaces, with `pokrov.space/checkout/` as the primary public acquisition route
- `webapp` renewal is continuation-only and should defer to the same hosted activation-key flow
- Telegram bot billing remains valid as a secondary path
- hybrid paid flow means hosted checkout sells activation keys, cabinet/app redeem refreshes the same account, and Telegram billing stays a secondary compatibility lane
- payment provider callbacks remain the source of payment truth; public status endpoints only summarize safe continuation state and activation handoff
- public order status carries `fulfillment_mode`, `issued_key_state`, `redeem_state`, and `next_action`; public guest success issues an activation key, while logged-in renewal can still use `direct_apply`
- public access-key status hides internal `created_by` and `redeemed_by` identifiers; admin key-status views can show those IDs after admin authentication
- raw subscription links remain recovery/manual-request only and must stay hidden from the default commerce UX

## Subscription Delivery Semantics

Current user-facing delivery semantics:

- one public `ссылка подключения`
- one QR built from the same URL
- one key-first commerce path: buy key -> redeem key -> managed premium
- no public smart/plain split in bot, site, or webapp wording
- consumer client and cabinet flows should prefer reconnect, refresh, route-mode change, checkout, and support over raw subscription copy/edit surfaces

Compatibility note:

- `?format=plain` still exists for backend compatibility and advanced/manual recovery
- that compatibility override must stay out of normal user-facing onboarding and CTA copy
- app-first managed flows may still receive `grpc_443_primary` during rollout, but manual/export recovery and legacy browser-visible compatibility paths stay on Reality until the share-link parity wave lands

## Support Ticket Continuation

1. user opens support from app, cabinet, or helpbot
2. session-backed support may create a real ticket through `POST /api/tickets`
3. cabinet/support surfaces may load the thread through `GET /api/tickets/{ticket_id}`
4. follow-up replies continue through `POST /api/tickets/{ticket_id}/messages`
5. attachment-capable browser support uses `POST /api/tickets/uploads`
6. operators continue the same case through `/api/admin/tickets/*`

Contract rule:

- app-first support may start from prepared context even before a live thread exists
- web and cabinet support must be documented as a real ticket lifecycle, not as decorative form state
- attachment-capable ticket flows belong to authenticated browser and admin paths today
- ticket rows include safe diagnostic context such as app platform/version, route mode, selected-app count, access state, Telegram-link presence, and masked recent-IP hints; they must not include subscription tokens, raw configs, or personal connection URLs
- client UX must not promise a realtime in-app chat when the backed contract is asynchronous ticketing

## Telegram Linking Flow

1. app-first account requests Telegram linking
2. backend issues a deep link to `@pokrov_vpnbot`
3. user opens the bot link
4. bot binds the app account to Telegram identity
5. reward and recovery logic can then use the linked Telegram account

Contract rule:

- Telegram linking should also refresh the canonical linked username automatically when Telegram provides one

## Telegram Bonus Claim Flow

1. app-first account must already be linked to Telegram
2. app or web surfaces may call `POST /api/channel/subscriber/check` to verify membership readiness
3. `POST /api/channel/subscriber/check` is read-only and must never grant points or mark campaign state
4. the real reward path calls `POST /api/bonuses/channel/claim`
5. backend checks membership for the linked Telegram account
6. if membership is valid, backend grants `+10 days`
7. if not linked or not eligible, backend returns the correct reason

## Access-State Continuation After Trial

Current backend-derived access states exposed to WebApp and admin surfaces:

- `trial_premium`
- `bonus_premium`
- `free_monthly`
- `free_soft_mode`
- `paid_unlimited`
- `expired_or_blocked`

Rules:

- app-first trial starts with `5 days` of premium-grade access
- channel claim extends that premium window by `+10 days`
- once premium expires, auto-downgrade must set `current_plan_code=free_monthly`, not `trial`
- `free_monthly` keeps `5 GB / 30 days` with device limit `1`
- after the `5 GB` quota is exhausted, UI and policy should treat the account as `free_soft_mode` until the next free-cycle reset
- `paid_unlimited` remains unlimited traffic with device limit `5`
- premium-grade access states `trial_premium`, `bonus_premium`, and `paid_unlimited` must use the paid pool: all enabled non-free delivery nodes
- free-tier access states `free_monthly` and `free_soft_mode` must use the free pool: the dedicated `NL-free` node only
- backend-facing `node_policy` should therefore resolve to `paid_pool` for premium-grade access and `nl_only` for free-tier access

## Runtime Notes

The bonus path is live and configured for:

- public channel: `@pokrov_vpn`
- main bot: `@pokrov_vpnbot`
- support bot: `@pokrov_supportbot`
- feedback bot: `@pokrov_feedbackbot`
- legacy usernames `swazist_bot` and `portal_service_bot` are officially disabled and must not be used as active runtime or support surfaces

The worker and API distinguish channel failures such as:

- `channel_not_found`
- `bot_not_in_channel`
- `not_member`
- `telegram_http_error`

Production environment should keep:

- `PUBLIC_CHANNEL=pokrov_vpn`
- `NEWS_CHANNEL_ID=@pokrov_vpn`

## Support Flow Direction

Support direction should stay consistent across app, WebApp, and helpbot:

- first-layer client IA should stay `Подключение`, `Локации`, `Правила`, and `Профиль`
- `Поддержка`, `Устройства`, `Тарифы`, and `Настройки` should sit under `Профиль`
- renewal and subscription state should remain first-class inside `Профиль`, not treated as an isolated side flow
- legacy client route names such as `Logs`, `Config Options`, and `About` may survive only as compatibility redirects, not as the public IA
- support messages should include device context
- users should be able to start support from inside the app
- helpbot remains a valid external fallback
- `support@pokrov.space` remains the email fallback for cases where Telegram is unavailable or a store/support mailbox is required
- cabinet support should continue the same ticket thread and uploads contract exposed by `/api/tickets*`
- feedback collection and public-review intake should continue through `@pokrov_feedbackbot`, not replace the primary support path
- public recovery order must stay `POKROV app -> web cabinet -> Telegram fallback`

Support operators should also be able to see:

- whether Telegram is linked
- the current or most recent device name and platform
- recent `last_ip` context
- enough node and subscription state to understand whether the problem is user-specific or wider

Client-facing diagnostics rule:

- diagnostics may show the active routing mode and a safe route category summary
- diagnostics must not expose raw configs, keys, or internal topology that would make config leakage easier
- the app should prefer safe operator actions such as `change location`, `refresh profile`, `reconnect`, and `contact support`
- user-visible subscription edit, regenerate, and advanced share actions should stay in admin or recovery-only tooling, not the first-layer consumer path
- do not describe Private Space, split tunneling, Knox, Shelter, or similar isolation features as a verified fix for a local control-surface exposure unless a dedicated security audit has proven that statement

## Admin Status And Cleanup Semantics

Current effective status model used across admin surfaces:

- `active`
- `expired`
- `blocked`
- `manual_test`

Current cleanup rule:

- only explicit manual/test accounts may be deleted from admin
- customer accounts remain non-destructive and should be handled through support or billing flows instead

## Funnel And Failure Metrics

Current event taxonomy should make the app-first journey visible across bot, site, and app. Important live/expected events include:

- open / dashboard open
- auth handoff start
- pay start
- pay success
- config open
- config import attempt
- connect success
- connect fail
- reconnect loop detection
- ticket create
- expiry / churn
- renewal / return

## Release Scope Note

This flow document applies to the full public `v1` experience on:

- `Android`
- `Windows`

For `iOS` and `macOS`, only readiness, signing prerequisites, and packaging notes are in scope in this release wave.

## Feedback And Review Flow

1. user leaves feedback from the app, WebApp, or `@pokrov_feedbackbot`
2. backend stores the submission for moderation
3. operator approves selected reviews for public display
4. the public homepage and cabinet show only featured reviews
5. visible nicknames are masked in a friendly format such as `mikh****`

If a username is missing or unusable, the public display should fall back to a neutral label like `Пользователь`.

## Related Files

- [portal_bot/api.py](C:/Users/kiwun/Documents/ai/VPN/portal_bot/api.py)
- [portal_bot/bot.py](C:/Users/kiwun/Documents/ai/VPN/portal_bot/bot.py)
- [portal_bot/worker.py](C:/Users/kiwun/Documents/ai/VPN/portal_bot/worker.py)
- [POKROV App Docs Index](C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md)

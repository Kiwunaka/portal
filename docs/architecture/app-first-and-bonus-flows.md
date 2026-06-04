# App-First And Bonus Flows

Last updated: 2026-06-04

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
- site email signup is a live additive browser continuation lane when `/api/auth/email/status` reports public delivery readiness; it must not be described as a premium-trial replacement for the app-first path
- browser continuation can start from app handoff, Telegram, or email; all three land in the same cabinet session family instead of creating competing account tracks
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
- `package_catalog_version`: versioned Android direct-app catalog stamp from shared facts
- `ruleset_version`: versioned routing/ruleset stamp from shared facts
- `support_context.transport`: `legacy_reality_fallback`
- `support_context.routing_mode`: `all_except_ru`
- `support_context.ip_version_preference`: `ipv4_only`
- `support_recovery_order`: `app`, `web`, `telegram`

First-run route-mode choice:

- the client must show exactly two first-layer consumer choices: `Optimize everything on this device` and `Only selected apps`
- `Optimize everything on this device` is the default public path and stays `TUN`-first
- `Only selected apps` is the split-tunneling path and must write per-device app/process selection state instead of revealing raw proxy or service controls
- the chosen mode must round-trip through backend-owned `route_mode`, `selected_apps`, and `route_policy.*` fields so `start-trial`, `dashboard`, and recovery flows all agree on the live device state
- Windows should use a known-app or executable picker; Android should use an installed-package picker
- the saved route-mode choice must remain editable later from a dedicated route-mode screen rather than only through hidden advanced settings

Rollout note:

- `AppSetting.network_rollout_config` resolves the transport profile for app-managed session and profile payloads
- `GET /api/client/profile/managed` is the primary app-managed provisioning endpoint and returns a manifest with `version`, `profile_revision`, `transport_profile`, `transport_kind`, `engine_hint`, `config_format`, `config_payload`, `fallback_order`, and `support_context`
- allowlisted carrier or cohort overrides may switch app-managed flows to `grpc_443_primary` without changing the public endpoint set
- allowlisted carrier or cohort overrides may switch app-managed flows to `ru_bridge_relay` during a RU reachability incident; that manifest keeps countries as the top-level choice, nests `Обычный` and `Белые списки` via-`mini` choices under non-US countries, and leaves US as direct-only
- managed provisioning now also returns a `smart_connect` contract with shortlist candidates, fallback metadata, rejection counts, and scoring hints
- manual/export compatibility links stay on `legacy_reality_fallback` until a separate share-link parity wave
- `subscription_url` remains a compatibility and recovery artifact for manual import, legacy browser-visible delivery, and fallback when the managed manifest cannot be fetched
- `network_rollout_config` carries `version`, `defaults`, `carrier_overrides`, `cohort_overrides`, `reserve_xhttp_cdn`, `ru_bridge_relay`, `operator_lab`, `package_catalog_feed`, `routing_rules_feed`, and `support_recovery_order`
- `defaults` normally keep `routing_mode_default=all_except_ru`, `transport_profile=legacy_reality_fallback`, and `dns_policy=ru_direct_split`; incident response may temporarily promote `transport_profile=ru_bridge_relay` with rollback to `legacy_reality_fallback`
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

## Preferred Device Identity Inputs

- `install_id`
- `device_name`
- `platform`
- `model`
- `app_version`
- soft fingerprint signal
- `last_ip`

This supports a friendlier device model than a Telegram-only account design.

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

## Live App-First Endpoints

Current live backend contract:

- `POST /api/client/session/start-trial`
- `GET /api/client/profile/managed`
- `POST /api/client/nodes/latency-samples`
- `GET /api/public/catalog`
- `GET /api/access-keys/status/{key}`
- `POST /api/access-keys/redeem`
- `POST /api/redeem`
- `POST /api/client/cabinet-token`
- `POST /api/auth/cabinet-handoff/exchange`
- `POST /api/admin/access-keys/issue`
- `GET /api/client/promo-slots`
- `GET /api/admin/promo-slots`
- `PUT /api/admin/promo-slots`
- `POST /api/client/telegram/link`
- `GET /api/bonuses/summary`
- `GET /api/bonuses/referral/summary`
- `GET /api/bonuses/history`
- `GET /api/bonuses/wheel/state`
- `POST /api/bonuses/wheel/spin`
- `GET /api/bonuses/calendar`
- `POST /api/bonuses/calendar/checkin`
- `POST /api/bonuses/promo/redeem`
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
- `GET /api/nodes/status`
- `GET /api/bonuses`
- ticket endpoints under `/api/tickets`

Unified access-contract note:

- `GET /api/dashboard`, `GET /api/user/{tg_id}`, and `GET /api/client/profile/managed` now carry the same identity/access family additions: `linked_identities`, `free_caps`, `redeem_eligibility`, `promo_slots`, `hidden_transport_matrix`, and `location_matrix`
- the access-key redeem path returns the same access-state family so app, cabinet, and admin can refresh off one canonical contract
- `POST /api/redeem` is the app-facing activation facade; it supports access keys and promo codes, returns `kind=access_key` or `kind=promo`, and keeps raw subscription links rejected as non-account proof
- `POST /api/redeem` must reject raw `connect.pokrov.space`, subscription, and proxy URLs with structured `code=subscription_link_not_redeem_code`; those links are connection/import artifacts, not account proof

Beta rate-limit contract:

- externally reachable beta surfaces for fresh trial creation, Telegram/email auth, access-key status/redeem, unified redeem, app-cabinet handoff token/exchange, and support ticket create/upload apply backend-owned per-minute throttles
- `POST /api/client/session/start-trial` throttles only fresh installs from the same origin; retries for an existing `install_id` remain idempotent and should continue to return the existing app-first account
- throttled requests return HTTP `429` with a `Retry-After` header and structured detail containing `code=rate_limited`, `scope`, and `retry_after_seconds`
- rate-limit counters store hashed in-process fingerprints and can be tuned with `API_RATE_LIMIT_<SCOPE>_PER_MINUTE` environment variables; they are beta abuse guardrails, not a durable cross-process quota ledger

## Web Login, Email Auth, And Session Continuation

Web surfaces support app-first continuation through:

- app or bot handoff into an existing cabinet session
- app handoff through `POST /api/client/cabinet-token`, which returns a short-lived signed one-time handoff token for a relative cabinet path on canonical `https://app.pokrov.space/`
- cabinet entry exchanges that token through `POST /api/auth/cabinet-handoff/exchange`, stores the returned browser session token, removes the handoff token from the URL, and honors the returned safe relative `target_path`
- failed cabinet handoff exchanges must clear URL token params and show localized cabinet copy for expired, already-used, invalid, and rate-limited states instead of dropping the user into an unexplained login wall
- Telegram widget or Telegram OIDC login in browser
- additive email signup, verification, login, recovery, and reset as a live browser continuation lane when delivery readiness is green
- dashboard and checkout continuation from an existing web session

Contract rule:

- canonical API base is `https://api.pokrov.space/`
- canonical public config host is `https://connect.pokrov.space/`
- HTML responses from `app.pokrov.space` must never be treated as valid API JSON
- web login should continue the user into account or checkout, not into a dead-end landing
- app handoff, Telegram, and email are the active browser-continuation entry families today
- expired or deprecated Telegram Login Widget, Telegram OIDC, WebApp `initData`, and browser-session tokens must clear the stale browser token and show a human repeat-login CTA instead of surfacing raw `telegram_*` / `web_session_*` errors
- stale Telegram Login Widget payloads should be rejected client-side before the backend sees them; users should be guided through a fresh Telegram login attempt
- additive email auth is live only when sender identity, delivery configuration, and delivery confirmation are green; if readiness fails, the UI must degrade back to unavailable instead of promising working verify or reset mail
- additive email auth must issue the same browser session family used by the cabinet, checkout, and support flows while exposing `auth_origin` and linked-identity summary for support/admin visibility
- app cabinet handoff tokens use `auth_origin=app_cabinet_handoff`, `scope=cabinet_handoff`, and a `60..120` second TTL; they are not accepted by normal authenticated API calls until exchanged
- handoff exchange is single-use through a backend ledger keyed by token hash; after exchange, the cabinet receives a normal browser session token with `scope=cabinet_session`
- expired handoff ledger rows are retained briefly for diagnostics and cleaned opportunistically by the backend after `CABINET_HANDOFF_LEDGER_RETENTION_SECONDS` (minimum one hour, default one day)
- the additive email-auth rollout uses endpoint families under `/api/auth/email/*` for register, verify, login, recovery, and reset
- public email register, verify, and recovery can be shown as live only while transactional sender identity and delivery-confirmation/webhook visibility are live
- browser entry screens in `webapp` are continuation-first and must not become a second landing-page pitch
- new user-facing `subscription_url` values must point to `connect.pokrov.space`
- legacy `api.pokrov.space/s8Kx2mP7qR4wT/...` remains compatibility-only for older imports and recovery cases
- the same `client_policy` contract still flows through `start-trial`, `user`, and `dashboard`, but the rollout policy behind it can vary by cohort without introducing a new endpoint

## Checkout Continuation

1. user opens public pricing, renewal continuation, or bot-side purchase
2. hosted checkout sells an activation key against the canonical catalog
3. the key is checked with `GET /api/access-keys/status/{key}` and then redeemed through `POST /api/redeem` in the app or `POST /api/access-keys/redeem` on legacy/cabinet surfaces
4. the backend refreshes managed access on the same app-first account
5. app and web surfaces reload their unified access contract from the same identity root

Checkout rule:

- public pricing starts from app-first marketing surfaces; `pokrov.space/checkout/` is the public plan and activation-key continuation route, not the first-pressure onboarding step
- payment provider readiness is contractually separate from app-first access; public checkout must remain unavailable or degraded for any route not covered by `docs/product/payment-and-access-key-contract.md` and current provider evidence
- `webapp` renewal is continuation-only and should defer to the same hosted activation-key flow
- Telegram bot billing remains valid as a secondary path; bot orders are Telegram-ticket-bound and do not collect buyer email
- raw subscription links remain hidden from default public commerce and first-layer cabinet UI, but the authenticated cabinet and paid Telegram bot flow may show the single `connect.pokrov.space` link after fulfillment as an explicit beta-stage manual import fallback while still preferring the POKROV app and cabinet
- signed payment callbacks must not grant access unless the normalized local status is `paid`; failed, cancelled, refunded, chargeback, invalid-signature, and unknown/manual-review states are recorded for operator reconciliation instead of extending the account

## Subscription Delivery Semantics

Current user-facing delivery semantics:

- one public `ссылка подключения` only in explicit manual/recovery fallback
- one QR built from the same URL only when that fallback is intentionally revealed
- one key-first commerce path: buy key -> redeem key -> managed premium
- no public smart/plain split in bot, site, or webapp wording
- consumer client and cabinet flows should prefer reconnect, refresh, route-mode change, checkout, and support over raw subscription copy/edit surfaces
- the main Telegram bot must not put the manual link, QR, share action, or security reset on the first menu layer; those actions belong in `Ещё`, device instructions, or explicit manual/recovery context
- redeem surfaces must reject or clearly explain `connect.pokrov.space` URLs as connection links, not activation keys
- payment, gift, and bonus success messages should prefer app/cabinet continuation and may offer a `Ручная ссылка / QR` button, but should not paste the full bearer connection URL into the message body by default

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
- client UX must not promise a realtime in-app chat when the backed contract is asynchronous ticketing

## Telegram Linking Flow

1. app-first account requests Telegram linking
2. backend issues a deep link to `@pokrov_vpnbot`
3. user opens the bot link
4. bot binds the app account to Telegram identity
5. reward and recovery logic can then use the linked Telegram account

Contract rule:

- Telegram linking should also refresh the canonical linked username automatically when Telegram provides one
- Raw `sub_token` values and `connect.pokrov.space` subscription URLs are bearer connection secrets for compatible clients only. They must not be accepted as Telegram-linking proof or as access-key redemption codes.

## Telegram Bonus Claim Flow

1. app-first account must already be linked to Telegram
2. app or web surfaces may call `POST /api/channel/subscriber/check` to verify membership readiness
3. `POST /api/channel/subscriber/check` is read-only and must never grant points or mark campaign state
4. the real reward path calls `POST /api/bonuses/channel/claim`
5. backend checks membership for the linked Telegram account
6. if membership is valid, backend grants `+10 days`
7. if not linked or not eligible, backend returns the correct reason

## Bonus Summary, Referral, And Promo Flow

- `GET /api/bonuses/summary` is the app-facing bonus summary for the Profile
  surface. It includes flat compatibility fields plus nested `referral`,
  `channel_bonus`, `opening_bonus`, `promo`, `history`, `wheel`, and
  `calendar` sections.
- `GET /api/bonuses/referral/summary` returns referral count, referral code,
  referral link, bonus days, and current points tier for the app-first account.
- `GET /api/bonuses/history` returns an app-safe, compact recent bonus ledger
  built from current platform truth: Telegram channel claim, opening campaign
  mark, and promo usage. It must not return raw subscription links, full promo
  codes, tokens, or event metadata.
- `POST /api/bonuses/promo/redeem` reuses the existing promo validation and
  application rules, then returns the promo result plus a fresh summary payload.
- `POST /api/redeem` also accepts promo codes and returns `kind=promo`.
- `GET /api/bonuses/wheel/state` and `GET /api/bonuses/calendar` expose
  disabled-by-default state payloads for future UI wiring.
- `POST /api/bonuses/wheel/spin` and
  `POST /api/bonuses/calendar/checkin` are app-facing placeholders guarded by
  feature flags and return structured disabled errors until reward logic,
  rollout policy, and product copy are approved.

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

- first-layer client IA should stay `Protection`, `Locations`, `Rules`, and `Profile`
- `Support`, `Devices`, `Subscription`, and `Settings` should sit under `Profile`
- renewal and subscription state should remain first-class inside `Profile`, not treated as an isolated side flow
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
- [docs/architecture/client-downloads-flow.md](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/client-downloads-flow.md)
- [docs/architecture/payment-state-machine.md](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/payment-state-machine.md)
- [docs/architecture/support-feedback-flow.md](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/support-feedback-flow.md)
- [POKROV App Docs Index](C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md)

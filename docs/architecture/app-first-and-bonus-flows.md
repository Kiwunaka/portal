# App-First And Bonus Flows

Last updated: 2026-04-13

## Document Status

This file is living source of truth for app-first identity, Telegram linking, and Telegram reward logic.

## Goal

Document the current app-first identity model, automatic username sync path, checkout continuation, node-pool assignment, and the live Telegram bonus flow used by `POKROV VPN`.

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
7. client silently imports the profile and switches to `Quick Connect`

Contract rule:

- caller-provided `trial_days` may still appear from older clients, but the backend must ignore it and always enforce the canonical `5-day` trial from `shared/product-facts.json`
- the backend must return the same `client_policy` contract from `start-trial`, `user`, and `dashboard` flows so the app can reconcile defaults without guessing

Current `client_policy` contract:

- `routing_mode_default`: `all_except_ru`
- `transport_profile`: `grpc_443_primary`
- `dns_policy`: `ru_direct_split`
- `package_catalog_version`: versioned Android direct-app catalog stamp from shared facts
- `ruleset_version`: versioned routing/ruleset stamp from shared facts
- `support_context.transport`: `grpc_443_primary`
- `support_context.routing_mode`: `all_except_ru`
- `support_context.ip_version_preference`: `ipv4_only`
- `support_recovery_order`: `app`, `web`, `telegram`

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

## Live App-First Endpoints

Current live backend contract:

- `POST /api/client/session/start-trial`
- `POST /api/client/telegram/link`
- `POST /api/channel/subscriber/check`
- `POST /api/bonuses/channel/claim`

Related live surfaces also exposed by the backend:

- `GET /api/dashboard`
- `GET /api/user/{tg_id}`
- `GET /api/client/apps`
- `GET /api/nodes/status`
- `GET /api/bonuses`
- ticket endpoints under `/api/tickets`

## Web Login And Session Continuation

Web surfaces support app-first continuation through:

- Telegram widget or Telegram OIDC login in browser
- bot-issued `web_session_token` handoff into `app.pokrov.space`
- dashboard and checkout continuation from an existing web session

Contract rule:

- canonical API base is `https://api.pokrov.space/`
- canonical public config host is `https://connect.pokrov.space/`
- HTML responses from `app.pokrov.space` must never be treated as valid API JSON
- web login should continue the user into account or checkout, not into a dead-end landing
- new user-facing `subscription_url` values must point to `connect.pokrov.space`
- legacy `api.pokrov.space/s8Kx2mP7qR4wT/...` remains compatibility-only for older imports and recovery cases

## Checkout Continuation

1. user opens pricing, renewal, or upgrade
2. platform resolves an active web session or signed checkout ticket
3. web checkout requests available providers
4. if providers are unavailable, UI must show a truthful blocked state
5. on success, the user returns to the active account journey

Checkout rule:

- public pricing can start the flow
- real payment actions require authenticated or ticketed continuation
- Telegram bot billing remains valid as a secondary path
- buying VPN must remain possible from bot, site, and app with the same backend contract behind each surface

## Subscription Delivery Semantics

Current user-facing delivery semantics:

- one public `ссылка подключения`
- one QR built from the same URL
- no public smart/plain split in bot, site, or webapp wording

Compatibility note:

- `?format=plain` still exists for backend compatibility and advanced/manual recovery
- that compatibility override must stay out of normal user-facing onboarding and CTA copy

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
- bot: `@pokrov_vpnbot`

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

- first-layer client IA should stay `VPN`, `Locations`, `Devices`, `Profile`, and `Support`
- renewal and subscription state should remain first-class inside `Profile`, not treated as an isolated side flow
- legacy client route names such as `Logs`, `Config Options`, and `About` may survive only as compatibility redirects, not as the public IA
- support messages should include device context
- users should be able to start support from inside the app
- helpbot remains a valid external fallback
- `support@pokrov.space` remains the email fallback for cases where Telegram is unavailable or a store/support mailbox is required
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
- [client session flow doc](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/architecture/app-first-session-flow.md)

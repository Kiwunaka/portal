# App-First And Bonus Flows

Last updated: 2026-03-29

## Document Status

This file is living source of truth for app-first identity, Telegram linking, and Telegram reward logic.

## Goal

Document the current app-first identity model, checkout continuation, and the live Telegram bonus flow used by `POKROV VPN`.

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
   - `session_token`
   - trial expiry
   - subscription source
   - experience payload
7. client silently imports the profile and switches to `Quick Connect`

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
- `POST /api/bonuses/channel/claim`

Related live surfaces also exposed by the backend:

- `GET /api/dashboard`
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
- HTML responses from `app.pokrov.space` must never be treated as valid API JSON
- web login should continue the user into account or checkout, not into a dead-end landing

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

## Telegram Linking Flow

1. app-first account requests Telegram linking
2. backend issues a deep link to `@pokrov_vpnbot`
3. user opens the bot link
4. bot binds the app account to Telegram identity
5. reward and recovery logic can then use the linked Telegram account

## Telegram Bonus Claim Flow

1. app-first account must already be linked to Telegram
2. the app calls `POST /api/bonuses/channel/claim`
3. backend checks membership for the linked Telegram account
4. if membership is valid, backend grants `+10 days`
5. if not linked or not eligible, backend returns the correct reason

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

- support messages should include device context
- users should be able to start support from inside the app
- helpbot remains a valid external fallback

Support operators should also be able to see:

- whether Telegram is linked
- the current or most recent device name and platform
- recent `last_ip` context
- enough node and subscription state to understand whether the problem is user-specific or wider

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

# App-First And Bonus Flows

Last updated: 2026-03-20

## Document Status

This file is living source of truth for app-first identity, Telegram linking, and Telegram reward logic.

## Goal

Document the current app-first identity model and the live Telegram bonus flow used by `PORTAL VPN`.

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

## Telegram Linking Flow

1. app-first account requests Telegram linking
2. backend issues a deep link to `@portal_service_bot`
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
- bot: `@portal_service_bot`

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

## Related Files

- [portal_bot/api.py](C:/Users/kiwun/Documents/ai/VPN/portal_bot/api.py)
- [portal_bot/bot.py](C:/Users/kiwun/Documents/ai/VPN/portal_bot/bot.py)
- [portal_bot/worker.py](C:/Users/kiwun/Documents/ai/VPN/portal_bot/worker.py)
- [client session flow doc](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/architecture/app-first-session-flow.md)

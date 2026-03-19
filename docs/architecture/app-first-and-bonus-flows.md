# App-First And Bonus Flows

Last updated: 2026-03-19

## Goal

Document the current app-first identity model and the Telegram bonus flow used by `PORTAL VPN`.

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

- `install_id` is the stable client-side primary identifier
- device context is used for abuse control and diagnostics
- app session token is used for subsequent app API calls
- Telegram is optional and not required for account creation

## Device Identity

Preferred identity inputs:

- `install_id`
- `device_name`
- `platform`
- `model`
- `app_version`
- soft fingerprint signal
- `last_ip`

This supports a friendlier device limiter than a pure Telegram-only model.

## Telegram Linking Flow

Current live backend contract:

- `POST /api/client/telegram/link`

Behavior:

1. app-first account requests Telegram linking
2. backend issues a bot deep link to `@portal_service_bot`
3. user opens the bot link
4. bot binds the app account to the Telegram identity
5. later reward and recovery logic can use the linked Telegram account

## Telegram Bonus Claim Flow

Current live backend contract:

- `POST /api/bonuses/channel/claim`

Behavior:

1. app-first account must already have linked Telegram
2. backend checks Telegram membership for the linked account
3. if membership is valid, backend grants `+10 days`
4. if not linked, backend returns a link-required response

## Important Current Runtime Note

The bonus code path and API are live, but the configured public channel is still unresolved.

What is already fixed:

- worker now distinguishes:
  - `channel_not_found`
  - `bot_not_in_channel`
  - `not_member`
  - `telegram_http_error`
- the old misleading generic alert is no longer the only signal

What still blocks full production success:

- the actual channel username must point to a real Telegram channel
- `@portal_service_bot` must be added to that channel with enough visibility for membership checks

## Support Flow

The target support direction is consistent across app, WebApp, and helpbot:

- support messages should include device context
- user should be able to contact support from inside the app
- helpbot remains a valid external fallback

## Current Related Files

- [portal_bot/api.py](C:/Users/kiwun/Documents/ai/VPN/portal_bot/api.py)
- [portal_bot/bot.py](C:/Users/kiwun/Documents/ai/VPN/portal_bot/bot.py)
- [portal_bot/worker.py](C:/Users/kiwun/Documents/ai/VPN/portal_bot/worker.py)
- [client session flow doc](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/architecture/app-first-session-flow.md)


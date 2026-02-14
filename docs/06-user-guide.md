# User guide

## Start

1. Open the Telegram bot and accept the offer.
2. Choose a plan and get a personal subscription key.
3. Open the web cabinet at `https://portal-privacy.online/webapp/`.
4. Import your key into a client app.

## Free mode

- 1 device
- 30 GB per 30-day cycle
- speed cap up to 50 Mbps
- social + AI routes are prioritized

## Web login outside Telegram

- Web cabinet supports Telegram Login Widget.
- After login, a web session token is created and used for API auth.

## Gift code activation

- You can activate a gift code in bot (`/redeem ...`) or in web cabinet.
- Result is unified: subscription is extended and key state is updated.

## Apps (Android / Windows)

Download links are served by `GET /api/client/apps` and rendered in web cabinet + marketing site.

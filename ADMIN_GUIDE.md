# Portal Admin Guide

Updated: `2026-02-14`

## 1. Components

- `portal_bot/bot.py`: Telegram bot flows.
- `portal_bot/api.py`: FastAPI backend for WebApp/checkout/callbacks.
- `webapp/`: personal cabinet UI.
- `marketing/`: landing and checkout pages.
- `portal.db` (or Postgres via `DATABASE_URL`): primary data store.

## 2. Payments Mode (Hybrid)

Current production model:

- Primary: RUB checkout via Freekassa.
- Secondary: Telegram Stars.

Freekassa is configured with two independent shops:

- `FK_SITE_*` for website checkout.
- `FK_BOT_*` for bot-started checkout.

## 3. Required Environment Variables

Core:
- `BOT_TOKEN`
- `BOT_USERNAME`
- `ADMIN_ID`
- `DATABASE_URL`
- `PUBLIC_API_BASE_URL`
- `WEBAPP_URL`
- `PAY_SUCCESS_URL`
- `PAY_FAIL_URL`

Feature flags:
- `RUB_CHECKOUT_ENABLED`
- `BOT_RUB_BUTTON_ENABLED`
- `CHECKOUT_WIDGET_ENABLED`
- `CHANNEL_SPEED_BUMP_ENABLED`

Freekassa:
- `FK_SITE_SHOP_ID`
- `FK_SITE_API_KEY`
- `FK_SITE_SECRET_WORD_1`
- `FK_SITE_SECRET_WORD_2`
- `FK_BOT_SHOP_ID`
- `FK_BOT_API_KEY`
- `FK_BOT_SECRET_WORD_1`
- `FK_BOT_SECRET_WORD_2`
- `FK_NOTIFY_IP_ALLOWLIST`
- `FK_API_BASE_URL`

Channel funnel:
- `PUBLIC_CHANNEL`
- `CHANNEL_SUBSCRIBER_CAMPAIGN_KEY`
- `FREE_SPEED_BUMP_UNSUB_KBPS`

## 4. Rollout Sequence

1. Deploy backend and bot with all payment flags disabled.
2. Enable `RUB_CHECKOUT_ENABLED=true` for internal tests.
3. Enable bot dual-pay UI: `BOT_RUB_BUTTON_ENABLED=true`.
4. Enable checkout widget: `CHECKOUT_WIDGET_ENABLED=true`.
5. Enable channel speed-bump: `CHANNEL_SPEED_BUMP_ENABLED=true`.

## 5. Rollback Sequence

1. Set flags to `false`:
   - `RUB_CHECKOUT_ENABLED`
   - `BOT_RUB_BUTTON_ENABLED`
   - `CHECKOUT_WIDGET_ENABLED`
   - `CHANNEL_SPEED_BUMP_ENABLED`
2. Restart services:
   - `systemctl restart portal-api`
   - `systemctl restart portal-bot`
3. Validate Stars-only flow in bot and WebApp.

## 6. Payment Operations

Create order:
- `POST /api/payments/freekassa/orders/create`

Check order:
- `GET /api/payments/freekassa/orders/{order_id}`

Refund order (admin):
- `POST /api/payments/freekassa/orders/{order_id}/refund`

Notify endpoint:
- `POST /api/payments/freekassa/notify`
- On successful signed callback: backend returns `YES`.

## 7. Promo and Campaign Deep Links

Supported `/start` payload formats:

- `promo_<CODE>`
- `campaign_<KEY>__promo_<CODE>`

Use these links in channel posts/ads to auto-apply promo and track campaign context.

## 8. Start 99 Plan Policy

- Plan code: `start_99`
- Price: `99 RUB`
- Duration: `30 days`
- Limits:
  - `1 device`
  - `NL-only` paid node visibility

## 9. Smoke Checklist

1. `GET /api/health` -> `200`.
2. Create test RUB order -> receive `order_id`.
3. Send signed notify -> `YES`.
4. Verify user:
   - `sub_type=PAID`
   - `current_plan_code` set
   - `expiry_at` extended
5. Validate bot:
   - dual-pay buttons shown (if enabled)
   - Stars flow still works
6. Validate WebApp:
   - RUB and Stars actions visible
   - channel check works
   - speed-bump status renders correctly

## 10. Security Rules

- Never store secrets in repository, tickets, or docs.
- Keep callback allowlist strict (`FK_NOTIFY_IP_ALLOWLIST`).
- Use least-privilege credentials for infrastructure and panel access.

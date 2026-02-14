# Payments Architecture (Chosen, 2026-02)

Updated: `2026-02-14`
Status: `Chosen architecture` (not research draft).

## 1. Product Decision

We use a hybrid model:

- Primary checkout in RUB via Freekassa (site + bot-origin links).
- Secondary payment method inside Telegram via Stars.

This keeps Telegram-native flow available while providing card/SBP checkout in browser.

## 2. Channel and Surface Split

- Marketing + checkout UI: `portal-privacy.online`.
- API + callback processing + success/fail redirects: `kiwunaka.space`.

## 3. Freekassa Integration Model

Two independent shops are configured:

- `FK_SITE_*` for website checkout.
- `FK_BOT_*` for bot-started checkout.

Order payload metadata links payment to account and funnel context:

- `tg_id`
- `plan_code`
- `campaign`
- `promo_code`
- `source`

## 4. Implemented API Endpoints

- `POST /api/payments/freekassa/orders/create`
- `GET /api/payments/freekassa/orders/{order_id}`
- `POST /api/payments/freekassa/orders/{order_id}/refund`
- `GET /api/payments/freekassa/currencies`
- `GET /api/payments/freekassa/currencies/{currency}/status`
- `POST|GET /api/payments/freekassa/notify`

## 5. Security Constraints

- Secrets are environment-only, never stored in repository.
- Callback protection:
  - SCI signature validation;
  - IP allowlist via `FK_NOTIFY_IP_ALLOWLIST`;
  - idempotent event storage to prevent double activation.
- Notify acknowledge for successful signed `POST`: plain `YES`.

## 6. Tariff and Activation Rules

RUB plan map:

- `start_99`: `99`, 30 days.
- `1_month`: `249`, 30 days.
- `3_months`: `699`, 91 days.
- `6_months`: `1199`, 182 days.
- `9_months`: `1399`, 273 days.
- `12_months`: `1499`, 365 days.

Special restrictions for `start_99`:

- 1 device limit.
- Paid profile with NL-only node visibility.

## 7. Funnel Layer

- Bot shows dual CTA:
  - `Оплатить ₽` (primary),
  - `Оплатить Stars` (secondary).
- Deep-link promo support:
  - `promo_<CODE>`
  - `campaign_<KEY>__promo_<CODE>`
- WebApp supports:
  - channel subscriber check,
  - one-time `+100 points`,
  - speed-bump status explanation.

## 8. Feature Flags

- `RUB_CHECKOUT_ENABLED`
- `BOT_RUB_BUTTON_ENABLED`
- `CHECKOUT_WIDGET_ENABLED`
- `CHANNEL_SPEED_BUMP_ENABLED`

Flags allow staged rollout and fast rollback to Stars-first behavior without DB rollback.

## 9. Known Constraints

- In Telegram environments, Stars remains required for native in-app payment scenarios.
- Browser checkout is used for card/SBP payments and linked back to Telegram account by metadata.
- Public copy must not use the forbidden legacy wording in landing/bot/WebApp marketing text.

## 10. Next Work

1. Admin UI for campaign-link templates and welcome discount management.
2. Conversion analytics for `start_99 -> paid parity`.
3. Expanded post-deploy smoke automation for both Freekassa shops.

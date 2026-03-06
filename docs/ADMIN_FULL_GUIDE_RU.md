# ADMIN FULL GUIDE (RU)

Обновлено: 6 марта 2026

## 1. Архитектура

- `portal_bot/bot.py` — основной Telegram-бот.
- `portal_bot/api.py` — FastAPI backend, WebApp API, admin API, checkout/callbacks, subscription endpoint.
- `portal_bot/worker.py` — фоновая логика и guard jobs.
- `webapp/` — кабинет пользователя и web-admin `/admin/*`.
- `marketing/` — лендинг, legal pages, ticketed checkout.
- `portal_bot/control_panel.py` — sync пользователей и ключей с 3x-ui.

Быстрые ссылки:
- `docs/PROJECT_MAP_RU.md`
- `docs/PAYMENTS_FLOW_RU.md`
- `docs/METRICS_RU.md`
- `docs/INFRA_PLAN_RU.md`

## 2. ENV-переменные

### Core
- `BOT_TOKEN`
- `BOT_USERNAME`
- `ADMIN_ID`
- `DATABASE_URL`

### Public URLs
- `PUBLIC_API_BASE_URL`
- `WEBAPP_URL`
- `PAY_CHECKOUT_URL`
- `PUBLIC_WEB_DOMAIN`

### Payments
- `FREEKASSA_SIGNING_SECRET`
- `FK_SITE_*`
- `FK_BOT_*`
- `RUB_CHECKOUT_ENABLED`
- `CHECKOUT_TICKET_SECRET`
- `CHECKOUT_TICKET_TTL_SECONDS`
- `PAYMENT_CALLBACK_TOLERANT_MODE`

### Subscription / compatibility
- `SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED`

### Bonuses
- `PUBLIC_CHANNEL`
- `CHANNEL_PREMIUM_DAYS`
- `OPENING_PREMIUM_DAYS`
- `OPENING_PREMIUM_CAMPAIGN_KEY`

### Metrics / ops
- `PANEL_URL`, `PANEL_USER`, `PANEL_PASS`
- `PANEL_PATH`
- `SUPPORT_USERNAME`

## 3. Управление пользователями

### Через бота
- онбординг
- выдача доступа
- продление
- бонусы
- support

### Через API / admin
- `/api/admin/summary`
- `/api/admin/users`
- `/api/admin/users/{tg_id}`
- `/api/admin/users/{tg_id}/manual/*`
- `/api/admin/users/keys/*`
- `/api/admin/campaign-links/build`

### Через web-admin
- `/admin/dashboard`
- `/admin/users`
- `/admin/nodes`
- `/admin/tickets`
- `/admin/promos`
- `/admin/referrals`
- `/admin/bonuses`
- `/admin/broadcast`

## 4. Ноды и panel sync

- Для paid/free delivery используются nodes и 3x-ui panel integration.
- При любом reset/regenerate/resync важно проверить:
  - новый `sub_token`
  - `subscription_url`
  - `resync_user_key_subid_on_node`
- Если subscription URL обновился, numeric fallback должен рассматриваться только как compat-мост.

## 5. Платежи

### Telegram Stars
- Бот создаёт `PayAttempt`.
- После `successful_payment` attempt помечается paid.
- Дубликаты suppress-ятся по fingerprint + payload/attempt state.

### FreeKassa
- Public payment path допускается только с `checkout_ticket`.
- Callback должен пройти signature verification.
- Invalid callback больше не блокирует valid callback с тем же `external_id`.

Подробнее:
- `docs/PAYMENTS_FLOW_RU.md`

## 6. Бонусы

- Channel bonus
- Opening/welcome bonus
- Referrals
- Gift codes
- Wheel
- Promo codes

Source of truth:
- `docs/BONUS_SYSTEM_RULES_RU.md`
- `docs/BONUS_SYSTEM_TESTS_RU.md`

## 7. Поддержка

- Пользовательские тикеты идут через `support_tickets` и `support_ticket_messages`.
- WebApp показывает history, thread и legal links.
- Legal документы открываются с marketing domain, а не из внутренних webapp route-заглушек.

## 8. Деплой и обновление

### Код
- backend deploy: `scripts/remote_deploy_brain_portal_code.py`
- static deploy: отдельный deploy для `marketing` и `webapp`

### Что обязательно проверить после деплоя
- API health
- checkout creation
- callback route
- subscription endpoint
- admin unauthorized state
- `portal-node-metrics.timer`

## 9. Мониторинг и диагностика

- Summary и metrics доступны через admin API.
- Collector: `scripts/collect_node_metrics.py`
- systemd:
  - `infra/portal-node-metrics.service`
  - `infra/portal-node-metrics.timer`

См.:
- `docs/METRICS_RU.md`
- `docs/INFRA_PLAN_RU.md`

## 10. Troubleshooting

### Симптом: по ключу открывается ошибка обновления
- Проверьте новый `sub_token`
- Проверьте `SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED`
- Проверьте panel resync по нодам

### Симптом: бонус за канал не отзывается
- Проверьте `worker` job
- Убедитесь, что Telegram status приходит как `left/kicked/not_member`

### Симптом: public checkout открывается, но не платит
- Проверьте наличие `checkout_ticket`
- Если ссылки собраны в admin builder, сейчас safe path идёт через bot fallback

### Симптом: metrics stale
- Проверьте, что deploy script доставил `collect_node_metrics.py`
- Проверьте `systemctl status portal-node-metrics.timer`

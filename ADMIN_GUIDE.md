# Portal Admin Guide

Обновлено: `2026-02-15`

## 1) Компоненты

- `portal_bot/bot.py`: Telegram сценарии.
- `portal_bot/api.py`: backend API, checkout, callbacks.
- `webapp/`: личный кабинет + админ-панель.
- `marketing/`: лендинг и checkout UI.

## 2) Текущая модель оплаты

- Primary: RUB checkout через Freekassa.
- Secondary: Stars в Telegram.

Dual-shop:
- `FK_SITE_*` для сайта.
- `FK_BOT_*` для bot-origin flow.

## 3) Обязательные ENV

Core:
- `BOT_TOKEN`, `BOT_USERNAME`, `ADMIN_ID`
- `DATABASE_URL`
- `PUBLIC_API_BASE_URL`, `WEBAPP_URL`
- `PAY_SUCCESS_URL`, `PAY_FAIL_URL`

Checkout/flags:
- `RUB_CHECKOUT_ENABLED`
- `CHECKOUT_WIDGET_ENABLED`
- `CHECKOUT_TICKET_SECRET`
- `CHECKOUT_TICKET_TTL_SECONDS`

Freekassa:
- `FK_SITE_SHOP_ID`, `FK_SITE_API_KEY`, `FK_SITE_SECRET_WORD_1`, `FK_SITE_SECRET_WORD_2`
- `FK_BOT_SHOP_ID`, `FK_BOT_API_KEY`, `FK_BOT_SECRET_WORD_1`, `FK_BOT_SECRET_WORD_2`
- `FK_NOTIFY_IP_ALLOWLIST`

Channel/funnel:
- `PUBLIC_CHANNEL`
- `CHANNEL_SUBSCRIBER_CAMPAIGN_KEY`
- `FREE_SPEED_BUMP_UNSUB_KBPS`

## 4) Плановые и новостные данные (DB-backed)

- Тарифы: `plan_catalog`
- Новости: `live_updates`

Если таблицы пусты, API автоматически возвращает fallback из legacy defaults.

## 5) Админ-функции в WebApp

### Вкладка `Промокоды`
- CRUD промо.
- Builder кампаний:
  - вход: `promo_code`, `campaign_key`, `plan_code`, `source`;
  - выход: `bot_start_link`, `checkout_link`, `webapp_link`.

### Вкладка `Планы`
- CRUD планов с параметрами:
  - RUB/Stars цена,
  - дни,
  - device limit,
  - node_policy,
  - active/inactive,
  - sort_order.

### Вкладка `Live Updates`
- CRUD карточек новостей.
- Публичная выдача на сайт: top-3 активных карточки.

## 6) Payments Operations

Основные endpoints:
- `POST /api/payments/freekassa/orders/create`
- `POST /api/payments/freekassa/orders/create-public`
- `POST|GET /api/payments/freekassa/notify`

Checkout ticket:
- создаётся в bot/backend;
- проверяется в `create-public`;
- без ticket сайт не создаёт заказ.

## 7) Rollout

1. Деплой backend с флагами OFF.
2. Включить `RUB_CHECKOUT_ENABLED=true`.
3. Проверить `create-public` по валидному ticket.
4. Проверить notify -> `YES`.
5. Включить `CHECKOUT_WIDGET_ENABLED=true` при необходимости.

## 8) Rollback

1. Выключить флаги `RUB_CHECKOUT_ENABLED` и `CHECKOUT_WIDGET_ENABLED`.
2. Перезапустить сервисы.
3. Оставить схему БД как есть (fallback сохраняет обратную совместимость).

## 9) Smoke Checklist

1. `GET /api/health` -> `200`.
2. Public plans/live updates отдаются корректно.
3. Admin CRUD plans/live updates работает.
4. `create-public` создаёт заказ и выдаёт `payment_url`.
5. Valid notify отвечает `YES` и активирует доступ.
6. Pending discount очищается после успешного создания заказа/оплаты.

## 10) Безопасность

- Никогда не хранить секреты в репозитории.
- Обновлять `FK_NOTIFY_IP_ALLOWLIST` по официальному списку провайдера.
- Использовать минимально необходимые привилегии сервисных аккаунтов.

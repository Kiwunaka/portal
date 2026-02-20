# Portal Admin Guide

Обновлено: `2026-02-16`

## 1) Компоненты

- `portal_bot/bot.py`: основной Telegram-бот (пользовательские и админ-сценарии).
- `portal_bot/api.py`: backend API, checkout, callbacks.
- `webapp/`: пользовательский личный кабинет на Next (static export в `webapp/out`, без админ-функций).
- `marketing/`: лендинг и checkout UI.
- `portal_bot/helpbot.py`: поддержка/тикеты.

## 2) Текущая модель оплаты

- Primary: RUB checkout через `FreeKassa`.
- Secondary: Telegram Stars.
- Dual-shop поддерживается (`site` + `bot`), источник истины по заказу — backend.

## 3) Обязательные ENV

Core:
- `BOT_TOKEN`, `BOT_USERNAME`, `ADMIN_ID`
- `DATABASE_URL`
- `PUBLIC_API_BASE_URL`, `WEBAPP_URL`
- `PAY_SUCCESS_URL`, `PAY_FAIL_URL`

Checkout/flags:
- `RUB_CHECKOUT_ENABLED`
- `BOT_RUB_BUTTON_ENABLED`
- `CHECKOUT_WIDGET_ENABLED`
- `PAYMENT_CALLBACK_TOLERANT_MODE` (`true` только на staging)
- `CHECKOUT_TICKET_SECRET`
- `CHECKOUT_TICKET_TTL_SECONDS`

FreeKassa:
- `FK_SITE_SHOP_ID`, `FK_SITE_API_KEY`, `FK_SITE_SECRET_WORD_1`, `FK_SITE_SECRET_WORD_2`
- `FK_BOT_SHOP_ID`, `FK_BOT_API_KEY`, `FK_BOT_SECRET_WORD_1`, `FK_BOT_SECRET_WORD_2`
- `FK_NOTIFY_IP_ALLOWLIST`

Funnel/support:
- `PUBLIC_CHANNEL`
- `CHANNEL_SUBSCRIBER_CAMPAIGN_KEY`
- `FREE_SPEED_BUMP_UNSUB_KBPS`
- `HELPBOT_START_MEDIA_PATH`, `HELPBOT_START_MEDIA_TYPE`

## 4) Где админка

Источник админ-правды: **основной бот** (`/start` -> `🔒 Админ-панель`).

Доступно в боте:
- промокоды;
- gift-коды;
- live updates (`@channel + post_id`);
- launch/start links (`start=code`);
- рулетка (preset/manual weights + cooldown);
- групповые действия с обязательным подтверждением и числом затронутых пользователей.

В WebApp админ-контролы отключены.

## 5) Payments Operations

Основные endpoints:
- `POST /api/payments/freekassa/orders/create`
- `POST /api/payments/freekassa/orders/create-public`
- `POST|GET /api/payments/freekassa/notify`

Статик-файлы кассы:
- `https://portal-privacy.online/fk-verify.html`
- `https://portal-privacy.online/fk-payment-theme.css`

Checkout ticket:
- создаётся в bot/backend;
- проверяется в `create-public`;
- без ticket сайт не создаёт заказ.

## 6) Push + Deploy Rule

Для релизных задач правило по умолчанию: завершение = `push + deploy`.

Минимальный flow:
1. Проверить тесты/smoke локально.
2. `push` изменений в рабочую ветку/репозиторий.
3. Выполнить deploy (bot/api/static).
4. Зафиксировать post-deploy sanity (health, checkout, callback, ключевой user-flow).

Если `push` или deploy невозможны, в документации/отчёте фиксируется причина и rollback-safe состояние.

## 7) Rollout

1. Деплой backend с безопасными флагами.
2. Включить `RUB_CHECKOUT_ENABLED=true`.
3. Включить `BOT_RUB_BUTTON_ENABLED=true` (RUB кнопка как primary в боте).
4. Проверить `create-public` по валидному ticket.
5. Проверить notify -> `YES`.
6. Включить `CHECKOUT_WIDGET_ENABLED=true` при необходимости.
7. Проверить `GET /fk-verify.html` и `GET /fk-payment-theme.css` -> `200`.

## 8) Rollback

1. Выключить `RUB_CHECKOUT_ENABLED`, `BOT_RUB_BUTTON_ENABLED` и `CHECKOUT_WIDGET_ENABLED`.
2. Перезапустить сервисы.
3. Сохранить схему БД (обратная совместимость через fallback/legacy поля).

## 9) Smoke Checklist

1. `GET /api/health` -> `200`.
2. Public plans/live updates отдаются корректно.
3. Admin flow работает в боте (promo/gift/start links/wheel/mass actions).
4. `create-public` создаёт заказ и выдаёт `payment_url`.
5. Valid notify отвечает `YES` и активирует доступ.
6. В WebApp нет админ-разделов, оплата ведёт на актуальные endpoints.

## 10) Безопасность

- Никогда не хранить секреты в репозитории.
- Поддерживать актуальный `FK_NOTIFY_IP_ALLOWLIST`.
- Использовать только env/secret manager для платёжных ключей.
- Перед релизом проверять идемпотентность callback и аудит-логи операций.

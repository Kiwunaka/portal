# Платёжный поток PORTAL

Обновлено: 7 марта 2026

## 1. Текущая модель

Сейчас в проекте две рублёвые ветки:
- `Telegram Stars` как встроенный платёж внутри Telegram;
- `RUB providers` как внешний checkout-контур с выбором кассы.

Ключевая идея:
- `PORTAL` создаёт заказ и хранит бизнес-логику;
- провайдер только даёт платёжную ссылку и присылает callback;
- bot, marketing checkout и backend используют единый catalog `/api/payments/providers`.

## 2. Поток оплаты в рублях

1. Пользователь выбирает тариф в боте, WebApp или checkout.
2. Клиент получает список доступных касс из `/api/payments/providers`.
3. При выборе кассы API создаёт `ExternalOrder`.
4. Для провайдера строится hosted payment URL.
5. Пользователь уходит на страницу платёжного партнёра.
6. Провайдер присылает callback в `/api/payments/result/{provider}` или provider-specific alias.
7. Backend:
   - проверяет подпись;
   - пишет `ExternalPaymentEvent`;
   - обновляет `ExternalOrder`;
   - активирует доступ;
   - запускает post-payment sync в panel.

## 3. Текущие endpoint'ы

Catalog:
- `GET /api/payments/providers`

Создание заказа:
- `POST /api/payments/orders/create`
- `POST /api/payments/orders/create-public`

Callback:
- `POST/GET /api/payments/result/{provider}`
- `POST/GET /api/payments/refund/{provider}`
- `POST/GET /api/payments/chargeback/{provider}`

Legacy alias для FreeKassa:
- `POST/GET /api/payments/freekassa/notify`

Success/fail landing:
- `GET /pay/success`
- `GET /pay/fail`

## 4. Поддерживаемые провайдеры

- `cardlink`
- `pally`
- `platima`
- `freekassa` как legacy fallback

Детальная настройка URL и env:
- [docs/PAYMENT_PROVIDER_SETUP_RU.md](C:\Users\kiwun\Documents\ai\VPN\docs\PAYMENT_PROVIDER_SETUP_RU.md)

## 5. Telegram Stars

1. Пользователь выбирает тариф в боте.
2. Создаётся `PayAttempt`.
3. Бот отправляет invoice.
4. `successful_payment`:
   - проверяет duplicate marker;
   - помечает attempt как paid;
   - активирует доступ;
   - пишет audit/event trail.

## 6. Текущие контракты

- public checkout требует `checkout_ticket`;
- bot и site используют один и тот же order-creation backend;
- провайдер выбирается явно и хранится в `ExternalOrder.provider`;
- callback idempotency держится на `ExternalPaymentEvent`;
- повторный valid callback не должен ломаться из-за ранее пришедшего invalid callback.

## 7. Точки отказа

| Точка | Что может пойти не так | Что делаем |
| --- | --- | --- |
| provider create link | касса не отвечает или сломан auth | checkout показывает понятную ошибку, оператор выключает провайдера через env |
| callback signature | неверная подпись | событие не активирует заказ |
| expired checkout ticket | пользователь открыл старую ссылку | checkout просит вернуться в Telegram и открыть оплату заново |
| provider policy change | касса изменила домены/маршруты | добавляем новый adapter, не ломая весь checkout |

## 8. Что проверил

- backend generic create routes;
- provider catalog;
- callback normalization;
- совместимость FreeKassa alias;
- bot и checkout на предмет FreeKassa-only хвостов.

## 9. Что нашёл

- проекту нужен provider-agnostic flow;
- жёсткая привязка к одной кассе больше не подходит;
- логика выбора кассы должна жить в `PORTAL`, а не в UI конкретного провайдера.

## 10. Что изменил

- добавил multi-provider abstraction в backend;
- вынес catalog провайдеров;
- перевёл bot и marketing checkout на generic order creation;
- обновил env matrix и setup runbook.

## 11. Что осталось / риск

- до включения новых касс в production нужны реальные токены и ручной smoke по callback;
- FreeKassa пока остаётся fallback-путём, но не должна считаться основной кассой.

# Payments Callback Runbook (Freekassa Dual Shop)

Обновлено: `2026-02-15`

## 1) Topology

- `portal-privacy.online`: маркетинговый сайт, checkout UI.
- `kiwunaka.space`: API, callbacks, redirect pages.
- Две кассы Freekassa:
  - `site` касса (`FK_SITE_*`);
  - `bot` касса (`FK_BOT_*`).

## 2) Панель Freekassa: обязательные настройки

Для каждой кассы (`site` и `bot`) укажите:

1. URL оповещения: `https://kiwunaka.space/api/payments/freekassa/notify`
2. Метод оповещения: `POST`
3. URL успешной оплаты: `https://kiwunaka.space/pay/success`
4. Метод успеха: `GET`
5. URL неуспеха: `https://kiwunaka.space/pay/fail`
6. Метод неуспеха: `GET`

Дополнительные публичные файлы кассы:
- Verify URL: `https://portal-privacy.online/fk-verify.html`
- CSS URL: `https://portal-privacy.online/fk-payment-theme.css`

## 3) Подпись callback

Формула проверки SCI callback:

`md5(MERCHANT_ID:AMOUNT:SECRET_WORD_2:MERCHANT_ORDER_ID)`

Backend проверяет поля:
- `MERCHANT_ID`
- `AMOUNT`
- `MERCHANT_ORDER_ID`
- `SIGN`

Успешный валидный POST на notify возвращает строку `YES`.

## 4) Endpoint Matrix

### Redirect pages

- `GET|POST /pay/success`
- `GET|POST /pay/fail`

### Freekassa API wrapper

- `POST /api/payments/freekassa/orders/create`
- `POST /api/payments/freekassa/orders/create-public`
- `GET /api/payments/freekassa/orders/{order_id}`
- `POST /api/payments/freekassa/orders/{order_id}/refund`
- `GET /api/payments/freekassa/currencies`
- `GET /api/payments/freekassa/currencies/{currency}/status`

### Callback

- `POST|GET /api/payments/freekassa/notify`

### Public static (checkout provider)

- `GET /fk-verify.html`
- `GET /fk-payment-theme.css`

## 5) Checkout Model

- Сайт использует `backend order first`:
  1. получает `checkout_ticket` из bot flow;
  2. вызывает `create-public`;
  3. редиректит на `payment_url`.
- Hosted payment URL по умолчанию собирается на домен `https://pay.fk.money/` через `FREEKASSA_PAY_HOST`.
- Если FreeKassa API возвращает свой `location`, backend должен использовать его как есть, без переписывания домена.
- Guest без ticket не оплачивает напрямую: UI ведёт в бота.

## 6) Idempotency и активация

1. Callback событие сохраняется в `external_payment_events`.
2. Ключ дедупликации: (`provider`, `event_type`, `external_id`).
3. `external_orders` обновляется upsert-логикой.
4. На первом валидном `result`:
   - продлевается доступ;
   - выставляется актуальный `plan_code`;
   - очищается `pending discount`;
   - запускается sync в панели.
5. Повторные notify не активируют доступ повторно.

## 7) Безопасность

- Секреты только через env/secret manager.
- IP allowlist для notify хранится в `FK_NOTIFY_IP_ALLOWLIST`.
- Список IP нужно обновлять по официальному источнику провайдера.
- Если подпись невалидна и tolerant mode выключен, callback возвращает `400`.

## 8) Обязательные ENV

- `RUB_CHECKOUT_ENABLED`
- `CHECKOUT_WIDGET_ENABLED`
- `PAYMENT_CALLBACK_TOLERANT_MODE` (для staging допускается `true`, для prod — `false`)
- `CHECKOUT_TICKET_SECRET`
- `CHECKOUT_TICKET_TTL_SECONDS`
- `PUBLIC_API_BASE_URL`
- `PAY_SUCCESS_URL`
- `PAY_FAIL_URL`
- `FK_SITE_SHOP_ID`, `FK_SITE_API_KEY`, `FK_SITE_SECRET_WORD_1`, `FK_SITE_SECRET_WORD_2`
- `FK_BOT_SHOP_ID`, `FK_BOT_API_KEY`, `FK_BOT_SECRET_WORD_1`, `FK_BOT_SECRET_WORD_2`
- `FK_NOTIFY_IP_ALLOWLIST`

## 9) Smoke Checklist

1. `GET /api/health` -> `200`.
2. `POST /api/payments/freekassa/orders/create-public` с валидным ticket -> `ok=true`.
3. Signed notify `POST /api/payments/freekassa/notify` -> `YES`.
4. Повтор notify -> `duplicate=true`.
5. Проверить пользователя:
   - `sub_type=PAID`;
   - `expiry_at` продлён;
   - pending discount очищен.
6. `GET https://portal-privacy.online/fk-verify.html` -> `200`.
7. `GET https://portal-privacy.online/fk-payment-theme.css` -> `200`.

## 10) Rollback

1. Выключить флаги:
   - `RUB_CHECKOUT_ENABLED=false`
   - `CHECKOUT_WIDGET_ENABLED=false`
2. Перезапустить `portal-api` и `portal-bot`.
3. Сохранить схему БД без отката (fallback на legacy constants остаётся рабочим).

# Платёжный поток PORTAL

Обновлено: 7 марта 2026

## 1. Основные ветки

### Telegram Stars
1. Пользователь выбирает тариф в боте.
2. Создаётся `PayAttempt`.
3. Бот отправляет invoice с `invoice_payload`.
4. `successful_payment` в `portal_bot/bot.py`:
   - проверяет duplicate marker,
   - помечает attempt как paid,
   - активирует подписку,
   - отправляет квитанцию.

### FreeKassa
1. Пользователь открывает checkout из кабинета или персональной ссылки.
2. API создаёт `ExternalOrder`.
3. FreeKassa отправляет callback в `/api/payments/freekassa/notify`.
4. Callback:
    - валидируется по подписи,
    - пишет/обновляет `ExternalPaymentEvent`,
    - активирует заказ,
    - запускает post-payment sync в panel.
5. Для обратной совместимости legacy alias `/api/payments/result/freekassa` всё ещё принят кодом, но актуальный notify URL для панели и runbook'ов — `/api/payments/freekassa/notify`.

## Актуальные внешние ссылки

- FreeKassa API Orders Create: `https://docs.freekassa.com/`
- FreeKassa API Orders Retrieve: `https://docs.freekassa.com/`
- FreeKassa SCI notify / callback: `https://docs.freekassa.com/`

## 2. Ключевые точки отказа

| Точка | Риск | Что сделано |
| --- | --- | --- |
| Callback signature | invalid callback может засорить поток | valid callback теперь апгрейдит ранее сохранённый invalid event |
| Public checkout | broken link без `checkout_ticket` | cold flow переведён в bot-first, admin builder отдаёт safe fallback |
| Subscription link rotation | старый numeric fallback живёт слишком долго | добавлен `SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED` и логирование fallback |
| Bonus sync | бонус выдан в БД, но не доехал в panel | channel bonus теперь вызывает `_sync_user_after_paid_bonus()` |

## 3. Контракты этой волны

- `SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED=true` по умолчанию, но каждый fallback логируется.
- Public payment path требует `checkout_ticket`.
- Если ticket нельзя выпустить, пользователь переводится в bot/webapp fallback, а не в broken checkout.
- Повторный valid callback с тем же `external_id` не блокируется ранее пришедшим invalid callback.
- Public checkout создаёт hosted payment URL FreeKassa сразу на нашей стороне и больше не зависит от FreeKassa Orders API в точке `create-public`.
- Hosted payment URL по умолчанию ведёт на `https://pay.fk.money/` и может быть переопределён через `FREEKASSA_PAY_HOST`.
- Для пользователя это означает: кнопка `Перейти к оплате` открывает готовую hosted payment page, а не падает с `Freekassa API error: 500`.

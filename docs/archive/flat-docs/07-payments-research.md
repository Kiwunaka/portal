# Payments Decision Note (FreeKassa)

Обновлено: `2026-02-16`
Статус: `Production decision finalized`.

## 1) Принятое решение

С `2026-02-16` платёжный провайдер для RUB-потока зафиксирован: `FreeKassa`.

Модель оплаты:
- Primary: RUB checkout (FreeKassa).
- Secondary: Telegram Stars.

Отдельный research-трек по выбору провайдера закрыт.

## 2) Архитектура checkout

- Сценарий сайта: `backend-order-first`.
- Заказ создаётся только на backend.
- Public checkout защищён `checkout_ticket`.
- Guest checkout без Telegram binding не входит в текущий релизный контур.

## 3) Контракт данных

Order metadata:
- `tg_id`
- `plan_code`
- `campaign`
- `promo_code`
- `source`
- pricing breakdown: `base_amount_rub`, `discount_pct`, `final_amount_rub`

Promo contract:
- `days`: немедленное продление;
- `discount`: pending скидка на следующую оплату.

## 4) Каталог планов и новости

Источник витрины:
- `plan_catalog`
- `live_updates`

Fallback сохраняется для обратной совместимости, если таблицы пусты.

## 5) Безопасность FreeKassa

- SCI verify: `md5(MERCHANT_ID:AMOUNT:SECRET_WORD_2:MERCHANT_ORDER_ID)`.
- notify endpoint проверяет `FK_NOTIFY_IP_ALLOWLIST`.
- callback storage идемпотентен.
- валидный notify подтверждается `YES`.

## 6) Панель FreeKassa (prod)

Рекомендованные URL (через текущий public domain):
- notify: `https://portal-privacy.online/api/payments/freekassa/notify` (`POST`)
- success: `https://portal-privacy.online/pay/success` (`GET`)
- fail: `https://portal-privacy.online/pay/fail` (`GET`)

Если в окружении другой домен, используется домен из env-конфига (`PUBLIC_API_BASE_URL`, `PAY_SUCCESS_URL`, `PAY_FAIL_URL`).

## 7) Операционное правило релиза

Для payment-изменений completion-правило:
1. тесты + smoke;
2. `push`;
3. deploy;
4. post-deploy sanity (`health`, `create-public`, `notify`, активация доступа).

## 8) Что не делаем без отдельного решения

- Не переключаем провайдера RUB-платежей.
- Не запускаем новый provider research.
- Не меняем callback/security контракт без обновления runbook и smoke-сценариев.

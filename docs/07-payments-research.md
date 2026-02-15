# Payments Architecture Note (Finalized 2026-02)

Обновлено: `2026-02-15`
Статус: `Finalized architecture note`.

## 1) Product Decision

Модель оплаты:
- Primary: RUB checkout (Freekassa, site/bot dual-shop).
- Secondary: Telegram Stars.

Причина: сохранить нативный путь в Telegram и дать отдельный web-поток для карты/СБП.

## 2) Checkout Architecture

- Основной сценарий сайта: `backend order first`.
- Order создаётся только на backend.
- Вход в public checkout защищён `checkout_ticket`.
- Guest без Telegram binding не поддерживается в первом релизе.

## 3) Data Contract

Order metadata:
- `tg_id`
- `plan_code`
- `campaign`
- `promo_code`
- `source`
- `pricing` breakdown (`base_amount_rub`, `discount_pct`, `final_amount_rub`)

Promo contract:
- `days` -> немедленное продление;
- `discount` -> pending скидка на следующую оплату (RUB/Stars).

## 4) Plan Catalog Model

Источник витрины: `plan_catalog`.

Fallback:
- если таблица пуста, используются legacy `RUB_PLAN_PRICES` и `API_PLAN_PRICES`.

Это позволяет безопасно выкатывать схему без жёсткой зависимости от наполнения БД.

## 5) Live Updates Model

Источник карточек сайта: `live_updates`.

Public endpoint:
- `GET /api/public/live-updates?limit=3`

Fallback:
- если таблица пуста, API отдаёт дефолтный набор карточек.

## 6) Freekassa Security

- SCI callback verify:
  - `md5(MERCHANT_ID:AMOUNT:SECRET_WORD_2:MERCHANT_ORDER_ID)`
- notify endpoint защищён IP allowlist (`FK_NOTIFY_IP_ALLOWLIST`).
- callback event storage идемпотентен.
- валидный POST notify подтверждается `YES`.

## 7) Panel Config Matrix

Для обеих касс (`site` + `bot`):
- notify URL: `https://kiwunaka.space/api/payments/freekassa/notify`, method `POST`;
- success URL: `https://kiwunaka.space/pay/success`, method `GET`;
- fail URL: `https://kiwunaka.space/pay/fail`, method `GET`.

## 8) Pricing Strategy

- `start_99` остаётся entry offer (`99 RUB`, `30 days`, `NL-only`, `1 device`).
- Все цены редактируются из админки через `plan_catalog`.
- Изменение цен делается по формуле contribution margin (см. pricing ops doc).

## 9) Risk Register (accepted)

1. Секреты кассы не ротируются в этом цикле.
2. Guest checkout без Telegram binding не поддерживается.
3. Виджет кассы оставлен как вспомогательный UI, а не источник истины по заказу.

## 10) Next Phase

Параллельный запуск треков:
1. Retention funnel automation.
2. UI polish и conversion microcopy.
3. Ops automation и post-deploy smoke.

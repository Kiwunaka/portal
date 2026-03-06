# Правила бонусной системы PORTAL

Обновлено: 7 марта 2026

## 1. Channel bonus

- Условие: пользователь подписан на публичный канал.
- Разрешено: только для `FREE/BONUS/TRIAL`, не для `MANUAL`.
- Claim:
  - membership `member/administrator/creator/restricted` -> success
  - membership `left/kicked/not_member` -> отказ
- После claim:
  - `sub_type=BONUS`
  - проставляются `channel_bonus_claimed_at`, `channel_bonus_active`, `channel_bonus_expires_at`
  - вызывается panel sync
  - пишется `promo_channel_activated` event c `days`, `sync_ok`, `points_granted`
- Повторный claim не должен молча теряться:
  - возвращается `already_claimed`
  - пишется `promo_channel_already_claimed`
- После unsubscribe:
  - worker guard считает `left/kicked` как `not_member`
  - бонус отзывается предсказуемо
- Отказы по channel bonus должны писать `promo_channel_denied` с reason-кодом, а не теряться только в HTTP-ответе или alert-тексте.

## 2. Opening / welcome bonus

- Выдаётся через start/campaign flow.
- Не должен занимать флаг `channel_bonus_claimed_at`.
- Не должен ставить `channel_bonus_revoked_at`, потому что это не отзыв бонуса за канал, а отдельная welcome-механика.
- Использует отдельный campaign mark.
- Campaign mark должен фиксироваться только после успешной выдачи доступа.
- Если `create_subscription()` упал, opening/welcome claim не считается израсходованным и повторная попытка должна быть доступна.
- `CampaignSend` для opening/welcome/start-link механик должен быть уникален по `(tg_id, campaign_key)` не только логически, но и на уровне БД/commit-path.

## 3. Referrals

- Первый paid purchase реферала:
  - ставит queue на бонус инвайтеру
  - в Stars-flow дополнительно начисляет referral points
- Первый paid purchase через FreeKassa теперь тоже начисляет referral points:
  - база расчёта берётся из `plan.amount_stars`
  - начисление защищено от повторов через stable `pay_attempt_id`/external-order id
- `referral_count` не должен увеличиваться дважды:
  - если queue row уже помечен `meta.counted=true`, worker не инкрементирует счётчик повторно
- Referral days и referral points больше не расходятся между Stars и FreeKassa на первом paid purchase.

## 4. Gift codes

- Gift purchase создаёт gift code.
- Redeem должен:
  - продлить доступ,
  - синхронизировать panel,
  - вернуть `sync_ok`.
- Gift redeem должен оставлять audit trail и в API/WebApp, и в bot-flow:
  - success -> `gift_redeemed`
  - denied -> `gift_redeem_denied`
- Gift campaign restrictions должны одинаково соблюдаться в API и в bot-flow.
- Friend gift через bot-flow не должен сжигать campaign mark до успешной выдачи доступа.

## 5. Wheel

- Рулетка ограничена cooldown.
- Конфиг хранится в `wheel_config`.
- Изменения веса/паузы должны проходить через admin и сохраняться в `app_settings`.
- После spin должен писаться audit/event след с `prize_days`, `cooldown_days` и `sync_ok`.
- Текст в bot-flow должен показывать фактический cooldown из конфигурации, а не захардкоженное значение.

## 6. Promo codes

- Могут давать скидку или дни.
- Для каждой механики нужен лимит использований и понятный учёт в БД.
- Promo expiry и campaign restrictions должны одинаково соблюдаться в WebApp/API и в bot-flow.
- Promo с некорректным `value` (`<= 0`) не должен создавать `PromoUsage`, уменьшать `uses_left` или считаться успешно применённым.
- Это правило должно одинаково соблюдаться и в API/WebApp, и в bot-flow.
- Promo redeem должен оставлять единый audit trail независимо от входной точки:
  - success -> `promo_redeemed`
  - denied -> `promo_redeem_denied`
  - reason-коды должны быть машиночитаемыми (`expired`, `already_redeemed`, `invalid_value`, `campaign_restriction_mismatch`, и т.д.)

## 7. Истина проекта после этой волны

- Opening bonus и channel bonus считаются разными состояниями.
- Channel revoke больше не зависит от “left как транзиентной ошибки”.
- Post-bonus sync обязателен хотя бы для channel bonus.
- Loyalty grant из admin-flow после начисления бонусных дней должен делать best-effort panel sync и возвращать `sync_ok`.
- Bot-flow больше не обходит expiry/campaign restrictions для promo и gift.
- Worker referral queue уважает уже учтённые (`counted=true`) реферальные события и не раздувает `referral_count`.
- Campaign/welcome marks теперь защищены от duplicate insert race через DB-level unique и обработку `IntegrityError` в bot/API/worker helper'ах.
- `events_service` должен брать актуальный `SessionLocal` динамически, чтобы bonus analytics не расползалась после reload/test bootstraps.
- Для channel/promo/gift теперь есть симметричный event trail в API/WebApp и bot-flow, а не только success-логи в части сценариев.

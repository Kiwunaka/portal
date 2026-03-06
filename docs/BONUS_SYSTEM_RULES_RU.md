# Правила бонусной системы PORTAL

Обновлено: 6 марта 2026

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
- После unsubscribe:
  - worker guard считает `left/kicked` как `not_member`
  - бонус отзывается предсказуемо

## 2. Opening / welcome bonus

- Выдаётся через start/campaign flow.
- Не должен занимать флаг `channel_bonus_claimed_at`.
- Использует отдельный campaign mark.

## 3. Referrals

- Первый paid purchase реферала:
  - ставит queue на бонус инвайтеру
  - в Stars-flow дополнительно начисляет referral points
- Нужна отдельная волна для полной parity с FreeKassa по points.

## 4. Gift codes

- Gift purchase создаёт gift code.
- Redeem должен:
  - продлить доступ,
  - синхронизировать panel,
  - вернуть `sync_ok`.

## 5. Wheel

- Рулетка ограничена cooldown.
- Конфиг хранится в `wheel_config`.
- Изменения веса/паузы должны проходить через admin и сохраняться в `app_settings`.

## 6. Promo codes

- Могут давать скидку или дни.
- Для каждой механики нужен лимит использований и понятный учёт в БД.

## 7. Истина проекта после этой волны

- Opening bonus и channel bonus считаются разными состояниями.
- Channel revoke больше не зависит от “left как транзиентной ошибки”.
- Post-bonus sync обязателен хотя бы для channel bonus.

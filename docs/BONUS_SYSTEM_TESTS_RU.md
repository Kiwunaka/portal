# Тесты бонусной системы PORTAL

Обновлено: 6 марта 2026

## Автотесты

- `tests/test_api_auth_and_tickets.py`
  - channel bonus claim success
  - `left -> not_member`
  - opening promo conflict
  - zero-value promo не должен сжигать usage и `uses_left`
  - admin loyalty grant должен возвращать `sync_ok` и вызывать panel sync
- `tests/test_api_payments_callbacks.py`
  - FreeKassa first paid purchase создаёт referral queue и referral points
- `tests/test_worker_retention.py`
  - normalize membership reasons
  - referral queue не удваивает `referral_count` для already-counted событий
- `tests/test_bot_paywall.py`
  - opening bonus не резервирует channel-bonus state
  - opening bonus не пишет ложный `channel_bonus_revoked_at`
  - opening bonus не сжигает campaign claim при падении `create_subscription()`
  - friend gift не сжигает campaign claim при падении `create_subscription()`
  - duplicate insert race для campaign claim не должен падать и не должен создавать дубль
  - zero-value promo не должен сжигать usage и `uses_left` в bot-flow
  - wheel spin использует фактический cooldown из конфига и пишет `wheel_spin` event с `sync_ok`
  - expired promo отклоняется в bot-flow
  - promo campaign restrictions соблюдаются в bot-flow
  - gift campaign restrictions соблюдаются в bot-flow

## Ручные смоуки

- Подписаться на канал -> claim -> проверить `sync_ok`
- Отписаться -> прогнать worker guard -> проверить revoke
- Активировать opening bonus -> убедиться, что channel bonus ещё доступен
  - Уронить выдачу opening/friend gift бонуса на тестовом окружении -> повторная попытка должна оставаться доступной
  - Параллельно дёрнуть один и тот же welcome/start-link flow -> должен сохраниться только один `CampaignSend`
  - Redeem gift code -> проверить `sync_ok`
- Promo code -> проверить лимит и повторное использование
- Referral paid purchase -> убедиться, что `referral_count` не удваивается после worker queue processing
- FreeKassa paid purchase по рефералу -> проверить, что points начислены так же, как в Stars-flow

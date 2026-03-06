# Тесты бонусной системы PORTAL

Обновлено: 6 марта 2026

## Автотесты

- `tests/test_api_auth_and_tickets.py`
  - channel bonus claim success
  - `left -> not_member`
  - opening promo conflict
- `tests/test_api_payments_callbacks.py`
  - FreeKassa first paid purchase создаёт referral queue и referral points
- `tests/test_worker_retention.py`
  - normalize membership reasons
  - referral queue не удваивает `referral_count` для already-counted событий
- `tests/test_bot_paywall.py`
  - opening bonus не резервирует channel-bonus state
  - expired promo отклоняется в bot-flow
  - promo campaign restrictions соблюдаются в bot-flow
  - gift campaign restrictions соблюдаются в bot-flow

## Ручные смоуки

- Подписаться на канал -> claim -> проверить `sync_ok`
- Отписаться -> прогнать worker guard -> проверить revoke
- Активировать opening bonus -> убедиться, что channel bonus ещё доступен
- Redeem gift code -> проверить `sync_ok`
- Promo code -> проверить лимит и повторное использование
- Referral paid purchase -> убедиться, что `referral_count` не удваивается после worker queue processing
- FreeKassa paid purchase по рефералу -> проверить, что points начислены так же, как в Stars-flow

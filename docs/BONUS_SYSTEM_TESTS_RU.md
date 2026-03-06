# Тесты бонусной системы PORTAL

Обновлено: 6 марта 2026

## Автотесты

- `tests/test_api_auth_and_tickets.py`
  - channel bonus claim success
  - `left -> not_member`
  - opening promo conflict
- `tests/test_worker_retention.py`
  - normalize membership reasons
- `tests/test_bot_paywall.py`
  - opening bonus не резервирует channel-bonus state

## Ручные смоуки

- Подписаться на канал -> claim -> проверить `sync_ok`
- Отписаться -> прогнать worker guard -> проверить revoke
- Активировать opening bonus -> убедиться, что channel bonus ещё доступен
- Redeem gift code -> проверить `sync_ok`
- Promo code -> проверить лимит и повторное использование

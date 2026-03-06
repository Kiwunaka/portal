# Итоговый отчёт PORTAL

Обновлено: 6 марта 2026

## Что было сломано

- Channel guard пропускал revoke при `left/kicked`.
- FreeKassa invalid callback мог ломать последующий valid callback с тем же `external_id`.
- Public campaign checkout выдавал broken link без `checkout_ticket`.
- WebApp legal links вели во внутренние несуществующие маршруты.
- Admin panel плохо объясняла `403` и истёкшую сессию.
- Deploy chain мог не доставлять collector для `portal-node-metrics.service`.
- Opening bonus пересекался с state channel bonus.

## Что исправлено

- Добавлен compat env-флаг `SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED`.
- Subscription endpoint теперь явно контролирует numeric fallback и логирует его.
- FreeKassa callback persistence обновляет invalid event до valid, а не блокирует его.
- `claim_channel_bonus` теперь возвращает реальный `sync_ok` после panel sync.
- Marketing home переведён в `bot-first`.
- Admin campaign link builder возвращает safe fallback вместо broken checkout.
- WebApp legal links переведены на absolute marketing URLs.
- Admin layout получил понятные состояния доступа.
- Deploy script копирует `collect_node_metrics.py` в brain runtime path.
- Opening bonus больше не резервирует `channel_bonus_claimed_at`.

## Что подтверждено проверками

- `python -m pytest tests/test_api_payments_callbacks.py tests/test_api_auth_and_tickets.py tests/test_bot_paywall.py tests/test_worker_retention.py -q`
- `python scripts/check-links.py`
- дополнительно: build/smoke зафиксированы в release artifacts этой волны

## Что осталось в backlog

- локальная генерация QR без внешней зависимости
- DB-level unique/idempotency для `CampaignSend`, чтобы start-link/campaign-бонусы были защищены не только логикой приложения
- дополнительный audit trail для части старых бонусных путей, которые всё ещё опираются на best-effort логирование

## Рекомендация по релизу

- Состояние этой волны: `ready to deploy`
- Перед prod rollout:
  - выполнить build/static deploy для `marketing` и `webapp`
  - убедиться, что `portal-node-metrics.timer` active/fresh
  - проверить public domain URLs и env-флаг `SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED`

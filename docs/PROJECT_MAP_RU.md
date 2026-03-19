# Карта проекта PORTAL

Обновлено: 7 марта 2026

## 1. Компоненты

| Контур | Основные файлы | Назначение |
| --- | --- | --- |
| Telegram Bot | `portal_bot/bot.py`, `portal_bot/helpbot.py` | Онбординг, тарифы, бонусы, support, admin-сценарии в Telegram |
| API | `portal_bot/api.py` | WebApp API, admin API, checkout/callbacks, subscription endpoint |
| Worker / Jobs | `portal_bot/worker.py` | retention, channel bonus guard, free-cycle reset, сервисные фоновые проверки |
| Panel integration | `portal_bot/control_panel.py`, `portal_bot/panel_client.py` | Синхронизация пользователя и ключей с 3x-ui / Xray |
| WebApp | `webapp/src/app/*`, `webapp/src/lib/api.ts` | Кабинет пользователя и web-admin `/admin/*` |
| Marketing | `marketing/src/app/*`, `marketing/src/lib/portal.ts` | Лендинг, legal pages, ticketed public checkout |
| Скрипты | `scripts/*.py` | smoke, deploy, collector, release gate, infra-операции |
| Инфраструктура | `infra/portal-node-metrics.service`, `infra/portal-node-metrics.timer` | systemd unit/timer для метрик нод |
| База данных | `portal_bot/models.py`, `portal_bot/migrations.py` | Production: Postgres на brain. SQLite-файлы могут существовать локально или как исторические артефакты, но не являются текущим source of truth прода |

## 2. Потоки данных

### 2.1 Основной путь
1. Пользователь приходит в Telegram-бот или WebApp.
2. Bot/API проверяют Telegram identity через initData или web-session token.
3. Пользователь выбирает план, бонус или промо.
4. Оплата идёт через Telegram Stars или внешний RUB provider из env-driven catalog.
5. `portal_bot/api.py` и `portal_bot/bot.py` обновляют БД.
6. `ControlPanel` синхронизирует пользователя и `subId` с 3x-ui.
7. Клиент получает конфиг через `/s8Kx2mP7qR4wT/{token}`.

### 2.2 Оплата / checkout
1. Cold marketing traffic идёт `bot-first`.
2. Public `/checkout` работает только по персональной ссылке с `checkout_ticket`.
3. Callback провайдера приходит в `portal_bot/api.py` через generic provider routes.
4. Callback валидируется, пишется в `external_payment_events`, затем активирует заказ.
5. После paid-активации выполняется post-payment sync в panel.

### 2.3 Бонусы
1. Channel bonus: claim через API, проверка membership через Telegram API, синхронизация в panel.
2. Opening / welcome / campaign: выдача через start links и campaign marks.
3. Referrals: первый paid purchase ставит очередь бонуса инвайтеру.
4. Gift / wheel / promo: state хранится в БД, UI читает через bot/API/admin.

### 2.4 Текущий runtime-контур нод
1. `brain` держит API/bot/helpbot/Postgres и x-ui для panel integration.
2. В runtime delivery pool включены `free`, `it`, `nl`, `pl`, `us`.
3. `brain` в текущей production БД отключён из delivery pool.
4. Стандартный delivery-профиль сейчас один: `VLESS + TCP + Reality`.
5. Старый `pl:8443` (`PL Free Reality`) выведен из эксплуатации и больше не считается рабочим runtime-контуром.

## 3. Где настраивается

### 3.1 ENV / runtime
- `portal_bot/config.py`
- `portal_bot/api.py`
- `portal_bot/bot.py`
- `webapp/src/lib/portal.ts`
- `marketing/src/lib/portal.ts`

### 3.2 Критичные env
- `BOT_TOKEN`, `BOT_USERNAME`, `ADMIN_ID`
- `DATABASE_URL`
- `PUBLIC_API_BASE_URL`, `WEBAPP_URL`, `PAY_CHECKOUT_URL`
- `CHECKOUT_TICKET_SECRET`, `CHECKOUT_TICKET_TTL_SECONDS`
- `RUB_PAYMENT_PROVIDER_ENABLED`, `RUB_PAYMENT_PROVIDER_ORDER`
- `CARDLINK_*`, `PALLY_*`, `PLATIMA_*`
- `FK_*` как legacy fallback
- `SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED`
- `PUBLIC_CHANNEL`, `CHANNEL_PREMIUM_DAYS`

## 4. Jobs / timers / cron-like процессы

| Процесс | Где | Роль |
| --- | --- | --- |
| `channel_bonus_guard_job()` | `portal_bot/worker.py` | отзывает бонус у тех, кто отписался от канала |
| Retention jobs | `portal_bot/worker.py` | T-3 / T-1 / T-0 сообщения и повторные касания |
| Free cycle reset | `portal_bot/worker.py` | reset free-лимитов |
| `portal-node-metrics.timer` | `infra/portal-node-metrics.timer` | периодический сбор health/traffic метрик нод |
| `scripts/admin_webapp_smoke.py` | release gate | smoke admin/webapp сценариев |
| `scripts/check-links.py` | release gate | контроль CTA, legal links и bot-first flow |

## 5. Текущие P0/P1 изменения этой волны

- `left/kicked` для channel membership приводятся к `not_member`, а revoke теперь стабилен.
- Numeric fallback для subscription endpoint поставлен под `SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED`.
- Invalid callback провайдера больше не блокирует следующий valid callback по тому же `external_id`.
- Public campaign checkout переведён в safe fallback: builder не выдаёт битую `/checkout` ссылку без ticket.
- WebApp legal links теперь ведут на absolute marketing URLs.
- Marketing home переведён в `bot-first` и убран избыточный client runtime.
- `CampaignSend` теперь защищён DB-level unique и единым `IntegrityError` guard в bot/API/worker helper'ах.
- Support в WebApp использует полноценный binary upload flow через `/api/tickets/uploads`.

## 6. Точки риска

- В web-admin есть server-side защита на API-уровне, но static-export природа WebApp ограничивает полноценный SSR guard.
- Часть старых markdown и ручных runbook всё ещё может ссылаться на SQLite или ранние node-снимки; для текущего прода ориентируемся на `DATABASE_URL`, `docs/08-node-inventory.md` и `docs/35-node-runtime-and-panel-audit-2026-03-07.md`.

## 7. Жизненный цикл нод

- `PORTAL` хранит lifecycle-флаги ноды:
  - `enabled`
  - `accepting_new_clients`
  - `is_draining`
- Источник истины по реальным назначениям пользователей на ноды — `user_nodes`.
- Правильный вывод ноды из эксплуатации:
  1. `drain`
  2. `resync`
  3. `disable`
- Полный runbook:
  - `docs/NODE_LIFECYCLE_RU.md`
# P2 addendum (2026-03-06)

- `portal_bot/api.py -> /api/admin/summary` now returns an `errors` block used by `/admin/dashboard` to surface stale metrics, unhealthy nodes, callback failures, and numeric subscription fallback counts.
- Support tickets use the existing `media_type/media_payload` contract, but WebApp now feeds it through binary upload to `/api/tickets/uploads` instead of a link-only flow.

## Telegram registry (2026-03-07)

- Главный канал и новости: `https://t.me/pokrov_vpn`
- Основной бот: `https://t.me/portal_service_bot`
- Бот поддержки: `https://t.me/portal_privacy_helpbot`
- Feedback-бот / зачаток обратной связи: `https://t.me/portalfeedbackbot`

## Subscription addendum (2026-03-09)

- Production source of truth по пользователям, нодам и подпискам: `Postgres` из `DATABASE_URL`.
- Локальный `portal.db` в репозитории и старый `/root/portal_bot/portal.db` на brain могут существовать как dev/исторический артефакт, но не являются текущей production-истиной.
- `/s8Kx2mP7qR4wT/{token}` теперь умеет два явных формата:
  - `?format=smart` — JSON-подписка для Hiddify / sing-box / NekoBox c маршрутами;
  - `?format=plain` — обычная base64 `vless://` подписка без встроенных маршрутов.
- Встроенные маршруты живут не на нодах, а в smart-подписке клиента:
  - РФ напрямую;
  - Steam и торренты напрямую;
  - реклама в блок;
  - остальное через выбранную страну.
- Актуальный Reality target для `PL` после canary-замены: `www.onet.pl:443`.

Для env defaults, public copy, smoke-проверок и новых правок canonical username основного бота — `portal_service_bot`. Упоминания `portal_privacy_bot` считаются legacy-следом и должны удаляться при ближайшем касании файла.

# ADMIN FULL GUIDE (RU)

Обновлено: 7 марта 2026

## 1. Архитектура

- `portal_bot/bot.py` — основной Telegram-бот.
- `portal_bot/api.py` — FastAPI backend, WebApp API, admin API, checkout/callbacks, subscription endpoint.
- `portal_bot/worker.py` — фоновая логика и guard jobs.
- `webapp/` — кабинет пользователя и web-admin `/admin/*`.
- `marketing/` — лендинг, legal pages, ticketed checkout.
- `portal_bot/control_panel.py` — sync пользователей и ключей с 3x-ui.
- production DB — `Postgres` на brain; локальные SQLite-файлы не считать источником истины прода.

Быстрые ссылки:
- `docs/PROJECT_MAP_RU.md`
- `docs/PAYMENTS_FLOW_RU.md`
- `docs/METRICS_RU.md`
- `docs/INFRA_PLAN_RU.md`

## 2. ENV-переменные

### Core
- `BOT_TOKEN`
- `BOT_USERNAME`
- `ADMIN_ID`
- `DATABASE_URL`

### Public URLs
- `PUBLIC_API_BASE_URL`
- `WEBAPP_URL`
- `PAY_CHECKOUT_URL`
- `PUBLIC_WEB_DOMAIN`

### Payments
- `RUB_PAYMENT_PROVIDER_ENABLED`
- `RUB_PAYMENT_PROVIDER_ORDER`
- `CARDLINK_*`
- `PALLY_*`
- `PLATIMA_*`
- `FREEKASSA_PAY_HOST`
- `FK_SITE_*`, `FK_BOT_*` as legacy fallback only
- `RUB_CHECKOUT_ENABLED`
- `CHECKOUT_TICKET_SECRET`
- `CHECKOUT_TICKET_TTL_SECONDS`
- `PAYMENT_CALLBACK_TOLERANT_MODE`
- `PAYMENT_LOGO_URL`

### Subscription / compatibility
- `SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED`

### Bonuses
- `PUBLIC_CHANNEL`
- `CHANNEL_PREMIUM_DAYS`
- `OPENING_PREMIUM_DAYS`
- `OPENING_PREMIUM_CAMPAIGN_KEY`
 - `FRIEND_GIFT_DAYS`
 - `FRIEND_GIFT_CAMPAIGN_KEY`

### Metrics / ops
- `PANEL_URL`, `PANEL_USER`, `PANEL_PASS`
- `PANEL_PATH`
- `SUPPORT_USERNAME`
 - `SUPPORT_UPLOAD_DIR`
 - `SUPPORT_UPLOAD_URL_PREFIX`
 - `SUPPORT_UPLOAD_MAX_BYTES`

## 3. Управление пользователями

### Через бота
- онбординг
- выдача доступа
- продление
- бонусы
- support

### Через API / admin
- `/api/admin/summary`
- `/api/admin/users`
- `/api/admin/users/{tg_id}`
- `/api/admin/users/{tg_id}/manual/*`
- `/api/admin/users/keys/*`
- `/api/admin/campaign-links/build`

### Через web-admin
- `/admin/dashboard`
- `/admin/users`
- `/admin/nodes`
- `/admin/tickets`
- `/admin/promos`
- `/admin/referrals`
- `/admin/bonuses`
- `/admin/broadcast`

## 4. Ноды и panel sync

- Для paid/free delivery используются nodes и 3x-ui panel integration.
- Текущий runtime delivery pool: `free`, `it`, `nl`, `pl`, `us`.
- `brain` остаётся control-plane хостом и не участвует в текущей выдаче как delivery node.
- Текущий стандартный профиль на нодах: `VLESS + TCP + Reality` на `443/tcp`.
- Старый `pl:8443` (`PL Free Reality`) выведен из эксплуатации и не должен использоваться как активный delivery-контур.
- При любом reset/regenerate/resync важно проверить:
  - новый `sub_token`
  - `subscription_url`
  - `resync_user_key_subid_on_node`
- Если subscription URL обновился, numeric fallback должен рассматриваться только как compat-мост.
- Lifecycle ноды теперь управляется через `PORTAL`, а не руками в panel:
  - `drain` = остановить новые назначения, не роняя текущих пользователей;
  - `resync` = перевести `user_nodes` на живые target-ноды;
  - `disable` = выключить ноду из runtime только после resync.
- В `/admin/nodes` теперь важно различать две цифры:
  - `Назначено в PORTAL` = сколько пользователей продукт логически держит на ноде;
  - `Записей в панели` = сколько client records реально лежит в 3x-ui.
- Эти числа могут отличаться из-за legacy-следов, старых ключей и незачищенных panel-records. Это не всегда авария, но хороший сигнал для cleanup.
- Там же теперь видны системные ресурсы ноды:
  - CPU
  - RAM
  - занятый / свободный диск
- Полный порядок действий описан в `docs/NODE_LIFECYCLE_RU.md`.

## 5. Платежи

### Telegram Stars
- Бот создаёт `PayAttempt`.
- После `successful_payment` attempt помечается paid.
- Дубликаты suppress-ятся по fingerprint + payload/attempt state.

### RUB providers
- Рублёвая оплата теперь идёт через catalog касс, который строится из env и доступен по `/api/payments/providers`.
- Public payment path допускается только с `checkout_ticket`.
- Callback каждого провайдера должен пройти signature verification.
- Invalid callback больше не блокирует valid callback с тем же `external_id`.
- FreeKassa оставлена как legacy fallback, а не как единственная основная касса.

Подробнее:
- `docs/PAYMENTS_FLOW_RU.md`
- `docs/PAYMENT_PROVIDER_SETUP_RU.md`

## 6. Бонусы

- Channel bonus
- Opening/welcome bonus
- Referrals
- Gift codes
- Wheel
- Promo codes

Source of truth:
- `docs/BONUS_SYSTEM_RULES_RU.md`
- `docs/BONUS_SYSTEM_TESTS_RU.md`

## 7. Поддержка

- Пользовательские тикеты идут через `support_tickets` и `support_ticket_messages`.
- WebApp показывает history, thread, legal links и binary upload вложений через `/api/tickets/uploads`.
- Вложения сохраняются в файловое хранилище backend и возвращаются в существующий `media_*` контракт без отдельной миграции БД.
- Legal документы открываются с marketing domain, а не из внутренних webapp route-заглушек.

## 8. Деплой и обновление

### Код
- backend deploy: `scripts/remote_deploy_brain_portal_code.py`
- static deploy: отдельный deploy для `marketing` и `webapp`
- orchestrator: `scripts/release_orchestrator.py`

### Как сейчас выкладывается статика
- `scripts/remote_deploy_brain_static_sites.py` сначала загружает сборку в versioned release-каталог `/var/www/portal/releases/<release_id>/...`
- после проверки ключевых файлов выполняется атомарное переключение symlink для `/var/www/portal/marketing` и `/var/www/portal/webapp`
- предыдущие release-каталоги не трогаются до завершения переключения; хранится короткая история последних релизов
- это нужно, чтобы не создавать кратких окон `404` во время обновления frontend-статики

### Текущее состояние
- Последний подтверждённый production rollout выполнен 6 марта 2026.
- Выкладка шла из чистого snapshot `HEAD`, чтобы не смешивать релизный слой с dirty worktree.

### Что обязательно проверить после деплоя
- API health
- checkout creation
- callback route
- subscription endpoint
- admin unauthorized state
- `portal-node-metrics.timer`
- `python scripts/check-links.py`
- `python scripts/ui_visual_smoke.py`
- `python scripts/verify_brain_ready.py --brain-ip <ip> --web-domain <domain> --api-domain <domain>`

### Что именно проверяет post-deploy verify
- `health` backend
- доступность home/offer/checkout/webapp
- наличие на marketing home CTA `Подключиться в Telegram` и `Посмотреть планы`
- наличие на `offer` CTA `Продолжить в Telegram`
- наличие на `checkout` текста `Продолжение через Telegram`

## 9. Мониторинг и диагностика

- Summary и metrics доступны через admin API.
- Collector: `scripts/collect_node_metrics.py`
- systemd:
  - `infra/portal-node-metrics.service`
  - `infra/portal-node-metrics.timer`
- Важно: `/api/admin/metrics/status` требует Telegram admin auth; для server-side проверки без WebApp-сессии используем SQL-проверку по `DATABASE_URL`.

См.:
- `docs/METRICS_RU.md`
- `docs/INFRA_PLAN_RU.md`

## 10. Troubleshooting

### Обновление подписки падает, но само подключение продолжает работать

- Проверьте не только `GET`, но и `HEAD` на `/s8Kx2mP7qR4wT/{token}`.
- Нормальное поведение production: и `GET`, и `HEAD` должны отвечать `200`.
- Если `GET` работает, а `HEAD` отвечает `405`, клиент может продолжать использовать старый уже загруженный профиль, но показывать ошибку на кнопке обновления.
- Для `Hiddify`, `sing-box` и `nekobox` endpoint должен отдавать `application/json` и заголовки `Profile-Title` + `Profile-Update-Interval`.

### Симптом: по ключу открывается ошибка обновления
- Проверьте новый `sub_token`
- Проверьте `SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED`
- Проверьте panel resync по нодам

### Симптом: бонус за канал не отзывается
- Проверьте `worker` job
- Убедитесь, что Telegram status приходит как `left/kicked/not_member`

### Симптом: public checkout открывается, но не платит
- Проверьте наличие `checkout_ticket`
- Если ссылки собраны в admin builder, сейчас safe path идёт через bot fallback

### Симптом: вложение в support не прикрепляется
- Проверьте `SUPPORT_UPLOAD_DIR` и права записи в каталог
- Проверьте `SUPPORT_UPLOAD_MAX_BYTES` и `content-type`
- Убедитесь, что `/uploads/support/*` смонтирован FastAPI через `StaticFiles`

### Симптом: metrics stale
- Проверьте, что deploy script доставил `collect_node_metrics.py`
- Проверьте `systemctl status portal-node-metrics.timer`
- Проверьте `journalctl -u portal-node-metrics.service -n 50 --no-pager`
- Проверьте свежесть `node_health_samples` в production DB, а не в локальном `portal.db`

## 11. Операционный контур марта 2026

### Что смотреть на `/admin/dashboard`

- `Сводка ошибок и рисков`
  - stale metrics
  - unhealthy nodes
  - callback failures
  - numeric fallback hits
  - open tickets
- `Бонусы и промо за 24 часа`
  - success/denied по channel/promo/gift
- `Удержание и реактивация`
  - кто истекает в ближайшие 3 дня;
  - сколько пользователей уже истекло за 7 дней;
  - сколько retention ping реально ушло за 24 часа.

### Где править retention без бота

- Откройте `/admin/broadcast`.
- Блок `Retention-шаблоны` теперь позволяет редактировать:
  - `retention_welcome_a/b`
  - `retention_t3_a/b`
  - `retention_t1_a/b`
  - `retention_t0_a/b`
  - `retention_reactivation_a/b`
- Это безопаснее, чем править шаблоны вручную в БД или через бот-меню.

### Как действовать оператору

- Если истекающих много, а `Retention ping 24ч` низкий:
  - сначала проверяем worker и шаблоны, потом вручную догреваем рассылкой по `expired/paid/free` сегментам.
- Если `reactivation_candidates` растёт:
  - запускаем мягкую кампанию на возврат через `/admin/broadcast` и смотрим конверсию по оплатам и open tickets.
- Если `single_point_risk=true`:
  - не включаем массово новые transport/network изменения; сначала canary на небольшой группе.

## 12. Telegram registry (актуально на 7 марта 2026)

- Главный канал и новости: `https://t.me/portal_privacy`
- Основной бот: `https://t.me/portal_service_bot`
- Бот поддержки: `https://t.me/portal_privacy_helpbot`
- Feedback-бот / зачаток обратной связи: `https://t.me/portalfeedbackbot`

Правило для операторов и других агентов:
- `portal_service_bot` — единственный канонический username основного бота.
- `portal_privacy_bot` — legacy-значение; если оно встречается в коде, docs, smoke-скриптах или env defaults, его нужно заменить при ближайшем изменении файла.

## 13. Подписка и маршруты (актуально на 9 марта 2026)

- Для production-диагностики подписок ориентируемся на `Postgres` из `DATABASE_URL`, а не на локальный `portal.db`.
- У одной и той же ссылки подписки теперь есть два явных формата:
  - `?format=smart` — умная подписка для Hiddify / sing-box / NekoBox;
  - `?format=plain` — обычная base64 `vless://` подписка без встроенных маршрутов.
- Умная подписка уже содержит правила:
  - РФ напрямую;
  - Steam и торренты напрямую;
  - реклама в блок;
  - остальной трафик через выбранную страну.
- На самих worker-нодах split-routing не настраивается: ноды остаются обычными transport-узлами `VLESS + TCP + Reality`.
- Для `PL` актуальный canary target после замены: `www.play.pl:443`.

# ADMIN FULL GUIDE (RU)

Обновлено: 4 марта 2026

## 1. Архитектура

### 1.1 Компоненты
- `portal_bot/bot.py` — основной Telegram-бот (пользовательские и админ-сценарии).
- `portal_bot/api.py` — FastAPI backend: checkout/callbacks, WebApp API, admin API, subscription endpoint.
- `portal_bot/worker.py` — фоновые задачи (retention, watchdog, channel bonus guard, free cycle reset).
- `portal_bot/control_panel.py` + `portal_bot/panel_client.py` — синхронизация клиентов с 3x-ui/Xray по нодам.
- `webapp/` — Telegram Mini App (Next.js static export), включая `/admin/*`.
- `marketing/` — лендинг и checkout UX-страницы.
- БД: SQLite (`portal.db`) с миграциями в `portal_bot/migrations.py`.

### 1.2 Нодовая схема
- Control plane (`brain`): API, bot, worker, helpbot, Caddy, БД, orchestrator-скрипты.
- Data plane (`us`, `pl`, `it`, `free`): 3x-ui/Xray inbounds.
- Логика совместимости: если таблица `nodes` пуста, работает legacy single-node fallback.

### 1.3 Поток данных (основной)
1. Пользователь приходит в бот / WebApp.
2. API валидирует Telegram initData / session token.
3. План/бонус/промо изменяют состояние пользователя в БД.
4. Control panel layer синхронизирует клиента в 3x-ui (enable/disable/subId/token).
5. Клиент получает подписку через `/s8Kx2mP7qR4wT/{token}`.

## 2. ENV-переменные (полный список)

Источник истины: `portal_bot/.env.example`, `portal_bot/config.py`, фактическое использование в `portal_bot/*.py`, `webapp/src`, `marketing/src`.

### 2.1 Core / Bot / DB
- `BOT_TOKEN`
- `BOT_USERNAME`
- `HELP_BOT_TOKEN`
- `LEGACY_BOT_TOKEN`
- `BOT_MIGRATION_TARGET_URL`
- `ADMIN_ID`
- `DATABASE_URL`
- `WORKER_EMBEDDED`
- `PORT`

### 2.2 Domains / URLs
- `HOST_DOMAIN`
- `PUBLIC_API_DOMAIN`
- `PUBLIC_WEB_DOMAIN`
- `DOMAIN`
- `PUBLIC_API_BASE_URL`
- `WEBAPP_URL`
- `PAY_CHECKOUT_URL`
- `CHECKOUT_URL`
- `PAY_SUCCESS_URL`
- `PAY_FAIL_URL`
- `PAY_RESULT_BASE_PATH`
- `PAY_REFUND_BASE_PATH`
- `PAY_CHARGEBACK_BASE_PATH`

### 2.3 Panel / Node / VLESS
- `PANEL_URL`
- `PANEL_USER`
- `PANEL_PASS`
- `PANEL_PATH`
- `INBOUND_ID`
- `INBOUND_ID_BACKUP`
- `VLESS_PORT`
- `VLESS_SNI`
- `VLESS_PBK`
- `VLESS_SID`
- `VLESS_FP`
- `VLESS_FLOW`
- `LEGACY_NODE_CODE`
- `LEGACY_NODE_NAME`
- `PANEL_ONLINE_RECENT_SECONDS`

### 2.4 Checkout / FreeKassa / Callback Security
- `RUB_CHECKOUT_ENABLED`
- `BOT_RUB_BUTTON_ENABLED`
- `CHECKOUT_WIDGET_ENABLED`
- `PAYMENT_CALLBACK_TOLERANT_MODE`
- `CHECKOUT_TICKET_SECRET`
- `CHECKOUT_TICKET_TTL_SECONDS`
- `FK_SITE_SHOP_ID`
- `FK_SITE_API_KEY`
- `FK_SITE_SECRET_WORD_1`
- `FK_SITE_SECRET_WORD_2`
- `FK_BOT_SHOP_ID`
- `FK_BOT_API_KEY`
- `FK_BOT_SECRET_WORD_1`
- `FK_BOT_SECRET_WORD_2`
- `FK_API_BASE_URL`
- `FK_NOTIFY_IP_ALLOWLIST`
- `FREEKASSA_NOTIFY_URL`
- `CARDLINK_SIGNING_SECRET`
- `FREEKASSA_SIGNING_SECRET`
- `AAIO_SIGNING_SECRET`

### 2.5 Support / Public channels
- `SUPPORT_USERNAME`
- `SUPPORT_BOT_USERNAME`
- `PUBLIC_CHANNEL`
- `NEWS_CHANNEL_ID`
- `HELPBOT_START_MEDIA_PATH`
- `HELPBOT_START_MEDIA_TYPE`

### 2.6 Plans / Limits / Loyalty
- `FREE_LIMIT_IP`
- `PAID_LIMIT_IP`
- `FREE_TOTAL_GB`
- `FREE_SPEED_LIMIT_KBPS`
- `FREE_SPEED_BUMP_UNSUB_KBPS`
- `CHANNEL_SPEED_BUMP_ENABLED`
- `AUTO_FREE_DAYS`
- `FREE_CYCLE_DAYS`
- `REFERRAL_BONUS_DAYS`
- `REFERRAL_TIERS`
- `POINTS_MONTHLY_CAP`
- `POINTS_EXPIRY_DAYS`
- `POINTS_PLAN_CAP_RATIO`
- `TOTAL_DISCOUNT_CAP_RATIO`
- `STACK_TOTAL_DISCOUNT_CAP`

### 2.7 Campaign / Bonus flags
- `OPENING_PREMIUM_DAYS`
- `OPENING_PREMIUM_START_CODE`
- `OPENING_PREMIUM_CAMPAIGN_KEY`
- `FRIEND_GIFT_DAYS`
- `FRIEND_GIFT_CAMPAIGN_KEY`
- `CHANNEL_PREMIUM_DAYS`
- `CHANNEL_SUBSCRIBER_CAMPAIGN_KEY`
- `START99_WELCOME_ENABLED`
- `START99_WELCOME_MIN_HOURS`
- `START99_WELCOME_MAX_HOURS`
- `START99_WELCOME_DISCOUNT_PCT`
- `START99_WELCOME_DISCOUNT_CODE`
- `RETENTION_TEMPLATE_CACHE_TTL_SECONDS`

### 2.8 Family / UX / Session / UI toggles
- `FAMILY_SLOT_STARS`
- `FAMILY_SLOT_DAYS`
- `FAMILY_SLOT_MAX`
- `WEBAPP_SESSION_SECRET`
- `WEBAPP_SESSION_TTL_SECONDS`
- `TELEGRAM_WEB_LOGIN_SECRET`
- `TELEGRAM_WEB_LOGIN_MAX_AGE_SECONDS`
- `WEBAPP_ENABLE_HAPTIC`
- `WEBAPP_ENABLE_LOTTIE`
- `WEBAPP_DEV_AUTH`
- `WEBAPP_DEV_TG_ID`
- `BOT_AUTO_DELETE_SECONDS`
- `TG_BTN_EMOJI_PRIMARY_ID`
- `TG_BTN_EMOJI_SUCCESS_ID`
- `TG_BTN_EMOJI_DANGER_ID`

### 2.9 WebApp / Marketing (frontend env)
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_TELEGRAM_LOGIN_BOT`
- `NEXT_PUBLIC_ENABLE_QA_OVERLAY`
- `NEXT_PUBLIC_ENABLE_LEGACY_PORT_FALLBACK`
- `VITE_PUBLIC_API_BASE_URL`
- `VITE_TELEGRAM_LOGIN_BOT`
- `VITE_ENABLE_LEGACY_PORT_FALLBACK`
- `NEXT_PUBLIC_TELEGRAM_BOT_URL`
- `NEXT_PUBLIC_WEBAPP_URL`
- `NEXT_PUBLIC_CHECKOUT_PAGE_URL`
- `NEXT_PUBLIC_NEWS_CHANNEL`
- `NEXT_PUBLIC_CONTACT_TG_URL`
- `NEXT_PUBLIC_CONTACT_EMAIL`
- `NEXT_PUBLIC_CONTACT_FORM_URL`
- `NEXT_PUBLIC_ENTERPRISE_EMAIL`
- `NEXT_PUBLIC_APP_ANDROID_PLAY_URL`
- `NEXT_PUBLIC_APP_ANDROID_APK_URL`
- `NEXT_PUBLIC_APP_ANDROID_MIRROR_URL`
- `NEXT_PUBLIC_APP_WINDOWS_EXE_URL`
- `NEXT_PUBLIC_APP_WINDOWS_MIRROR_URL`
- `NEXT_PUBLIC_APP_DOCS_URL`

## 3. Управление пользователями (бот + API)

### 3.1 Базовые операции
- Создание/обновление пользователя происходит через bot-flow и API auth/session.
- Админ-операции:
  - `GET /api/admin/users`
  - `GET /api/admin/users/{tg_id}`
  - `POST /api/admin/users/{tg_id}/extend`
  - `POST /api/admin/users/{tg_id}/block`
  - `POST /api/admin/users/{tg_id}/regenerate-token`

### 3.2 Manual users
- Создание manual-пользователей: `POST /api/admin/users/manual`.
- Продление/блокировка/regenerate token:
  - `/api/admin/users/{tg_id}/manual/extend`
  - `/api/admin/users/{tg_id}/manual/block`
  - `/api/admin/users/{tg_id}/manual/regenerate-token`

### 3.3 Subscription token
- Endpoint: `/s8Kx2mP7qR4wT/{token}`.
- Рабочий сценарий:
  - основной lookup по `sub_token`;
  - fallback по `tg_id`, если token числовой;
  - при inactive-user отдается пустой ответ.
- Для диагностики в логах есть fingerprint токена (без утечки самого токена).

## 4. Управление нодами

### 4.1 Нодовые операции API
- `GET /api/admin/nodes/health`
- `POST /api/admin/nodes/sync`
- `GET /api/admin/nodes/traffic?from&to`

### 4.2 Синхронизация пользователей в panel
- Принцип: DB `sub_token` = panel client `subId`.
- На create/renew/regenerate/panic принудительно синхронизируется `subId`.
- При mismatch panel-клиент обновляется с `subId` из БД.

### 4.3 Рекомендуемые операционные команды
- Проверка нод: `python scripts/remote_brain_nodes_sanity.py --brain-ip <ip>`
- Инспекция subscription hosts: `python scripts/remote_inspect_brain_subscription_hosts.py --brain-ip <ip> --domain <domain>`
- Синхронизация пользователей: `python scripts/remote_sync_users_to_nodes.py ...`

## 5. Платежи (FreeKassa + Stars)

### 5.1 Основные маршруты
- Создание заказа (auth): `POST /api/payments/freekassa/orders/create`
- Создание заказа (public с checkout-ticket): `POST /api/payments/freekassa/orders/create-public`
- Callback: `POST|GET /api/payments/freekassa/notify`

### 5.2 Ключевые правила
- Провайдер RUB: FreeKassa (primary), Stars (secondary).
- Идемпотентность callback обязательна.
- Pending discount больше не списывается на этапе create-order (только при успешной оплате).
- Для callback допускается извлечение `us_tg_id` / `us_plan_code` из notify payload (fallback).

### 5.3 Referral в платежном потоке
- Для первого платного RUB-платежа применим referral-discount.
- После первого paid-платежа срабатывает bonus для инвайтера.

## 6. Бонусная система

### 6.1 Channel bonus
- Claim: `POST /api/bonuses/channel/claim`
- Guard в worker:
  - `left`, `kicked`, `not_member` нормализуются в `not_member`.
  - revoke выполняется только при `normalized_reason=not_member`.
  - transient ошибки Telegram/API не вызывают revoke.
- Структурные логи: `user_id`, `raw_status`, `normalized_reason`, `action`.

### 6.2 Referral / Welcome links / Campaign links
- Start links: `GET/POST/PATCH/DELETE /api/admin/start-links`
- Campaign links builder: `POST /api/admin/campaign-links/build`
- Ограничение Telegram payload: максимум 64 символа, с валидацией.

### 6.3 Promos / Gift
- Promo CRUD: `GET/POST/PATCH/DELETE /api/admin/promos`
- Gift codes: `GET/POST /api/admin/gift-codes`
- Исправления:
  - unlimited promo (`uses_left=-1`) работает корректно;
  - use-limit decrement сделан условным и безопасным;
  - добавлен уникальный индекс на `promo_usage(tg_id, promo_code)`.

### 6.4 Wheel
- Конфиг: `GET/PUT /api/admin/wheel-config`
- Cooldown хранится в часах (`cooldown_hours`, стандарт 168h).
- Spin выполнен атомарно с guard по `last_wheel_spin`.

## 7. Поддержка (тикеты / helpbot)

### 7.1 API
- `POST /api/tickets`
- `GET /api/tickets`
- `GET /api/tickets/{ticket_id}`
- `POST /api/tickets/{ticket_id}/reply`

### 7.2 Админские операции
- `GET /api/admin/tickets`
- `POST /api/admin/tickets/{ticket_id}/reply`
- `POST /api/admin/tickets/{ticket_id}/status`

### 7.3 Bot/helpbot
- Helpbot используется как отдельная точка входа для инцидентов и FAQ.
- Операторская очередь доступна в админ-сценариях бота.

## 8. Деплой и обновление

### 8.1 Общий порядок (без remote-exec)
1. Локально: `python scripts/release_orchestrator.py --gates-only`.
2. Upload/release кодовой части на brain.
3. Рестарт сервисов: `portal-api`, `portal-bot`, `portal-helpbot`.
4. Деплой static (`webapp/out`, `marketing/out`).
5. Sanity checks (см. раздел 9.4).

### 8.2 Команды (ручной запуск на brain)
- `systemctl status portal-api --no-pager`
- `systemctl status portal-bot --no-pager`
- `systemctl status portal-helpbot --no-pager`
- `curl -fsS https://<api-domain>/api/health`

### 8.3 Rollback-safe точки
- До миграций БД.
- После backend deploy, до static deploy.
- После включения/изменения timer/metrics.

## 9. Мониторинг и диагностика

### 9.1 Node metrics
- Collector: `scripts/collect_node_metrics.py`
- Timer/service:
  - `infra/portal-node-metrics.service`
  - `infra/portal-node-metrics.timer`

### 9.2 Включение таймера
- `python scripts/remote_install_node_metrics_timer.py --brain-ip <ip>`
- Затем на brain:
  - `systemctl is-enabled portal-node-metrics.timer`
  - `systemctl is-active portal-node-metrics.timer`
  - `systemctl list-timers portal-node-metrics.timer --all`
  - `journalctl -u portal-node-metrics.service -n 50 --no-pager`

### 9.3 Admin metrics API
- `GET /api/admin/metrics/status`
- `GET /api/admin/metrics/timeseries?from=YYYY-MM-DD&to=YYYY-MM-DD`
- `GET /api/admin/nodes/traffic?from=YYYY-MM-DD&to=YYYY-MM-DD`

### 9.4 Post-deploy sanity checklist
1. `/api/health` = 200.
2. `/s8Kx2mP7qR4wT/{token}` работает по актуальному token.
3. Checkout create + notify callback завершают активацию.
4. Ticket flow (create/reply/status) работает E2E.
5. `/admin/*` маршруты WebApp доступны только при `is_admin=true`.
6. `python scripts/admin_webapp_smoke.py` проходит без ошибок.

### 9.5 SLO/SLA и alert policy
- Операционные SLI/SLO и правила эскалации: `docs/34-monitoring-slo-sla-2026-03.md`.

## 10. Troubleshooting

### 10.1 Симптом: «ошибка обновления» при обновлении по ключу
Проверить:
1. Есть ли `sub_token` у пользователя в БД.
2. Совпадает ли panel `subId` с DB `sub_token`.
3. Логи `control_panel.py`/`panel_client.py` на mismatch и forced sync.
4. Endpoint `/s8Kx2mP7qR4wT/{token}` по текущему токену.

### 10.2 Симптом: channel bonus не откатывается
Проверить:
1. Логи worker (`raw_status`, `normalized_reason`, `action`).
2. Нормализацию `left/kicked -> not_member`.
3. Что revoke не блокируется transient Telegram-ошибкой.

### 10.3 Симптом: устаревшие метрики
Проверить:
1. `portal-node-metrics.timer` enabled/active.
2. `journalctl -u portal-node-metrics.service`.
3. `GET /api/admin/metrics/status` (fresh/stale).

### 10.4 Симптом: deep-link кампания не срабатывает
Проверить:
1. Длина Telegram start payload <= 64.
2. Допустимые символы: `[A-Za-z0-9_-]`.
3. Реальные значения `promo/campaign` в checkout context.

### 10.5 Симптом: `Bot domain invalid` при входе через Telegram Login Widget
Проверить:
1. В `@BotFather` для `@net4ebur_bot` выполнен `/setdomain` на актуальный домен (`portal-privacy.online`).
2. Веб-вход через deep-link работает: `https://t.me/net4ebur_bot?start=weblogin`.
3. Ссылка из бота открывает WebApp с `web_session_token` и автоматически логинит пользователя в браузере.

---

## Приложение A: Admin WebApp MVP (`/admin/*`)
- `/admin/dashboard`
- `/admin/users`
- `/admin/nodes`
- `/admin/tickets`
- `/admin/promos`
- `/admin/broadcast`
- `/admin/referrals`
- `/admin/bonuses`

Gate: не-админы редиректятся в пользовательский dashboard.

## Приложение B: Smoke-команды релиза
- `python -m unittest discover tests`
- `cd webapp && npm.cmd run build`
- `python -m unittest tests.test_worker_retention`
- `python -m unittest tests.test_api_auth_and_tickets`

# PORTAL: Глобальная архитектура и production-состояние (полный срез)

> Обновлено: 2026-02-09  
> Источник live-проверки: `docs/audit-artifacts/prod-audit-20260209-023635.json`

## 1. Назначение системы

`PORTAL | Network Security` — Telegram-first сервис защищенного сетевого доступа с:
- основным ботом для онбординга, тарифов, админ-операций;
- отдельным helpbot для тикетов поддержки;
- Telegram WebApp (личный кабинет);
- внешним маркетинговым сайтом;
- мульти-нодной выдачей подписки через API endpoint.

## 2. Production snapshot (на момент проверки)

### 2.1 Сервисы на control-plane (BRAINnode)

- `caddy`: `active`, `enabled`
- `portal-api`: `active`, `enabled`
- `portal-bot`: `active`, `enabled`
- `portal-helpbot`: `active`, `enabled`
- `x-ui`: `active`, `enabled`
- `portal-node-metrics.timer`: `inactive` (не включен в текущем состоянии)
- `portal-node-metrics.service`: `inactive`

### 2.2 Деплой-метки файлов

- `/root/portal_bot/bot.py` — обновлен
- `/root/portal_bot/api.py` — обновлен
- `/root/portal_bot/helpbot.py` — обновлен
- `/var/www/portal/webapp/index.html` — обновлен
- `/var/www/portal/marketing/index.html` — обновлен

### 2.3 Маркеры новых фич в коде (на сервере)

Подтверждено наличие:
- `mode_simple`/`mode_pro` (сегментация входа)
- `check_subscription` (paywall на канал для Starter)
- `admin_manual_menu` (manual users)
- `/api/dashboard`
- `/api/nodes/status`
- `/api/admin/users/manual`
- helpbot меню с `"➕ Новый запрос"` и `"📂 Мои запросы"`

## 3. Логическая архитектура

## 3.1 Контуры

1. `Control-plane`:
- `portal-api` (FastAPI)
- `portal-bot` (aiogram)
- `portal-helpbot` (aiogram)
- SQLite БД (`portal.db`)
- Caddy (TLS + reverse proxy + static)

2. `Data-plane`:
- worker-ноды с панелями и инбаундами
- выделенный free-pool узел

3. `Client-plane`:
- Telegram users (бот + helpbot)
- Telegram WebApp
- внешняя страница продаж

## 3.2 Основной flow пользователя

1. `/start` в боте  
2. сегментация `Автопилот`/`Профи`  
3. выбор тарифа / активация starter  
4. выдача доступа и WebApp  
5. API подписки `/s8Kx2mP7qR4wT/{token}` возвращает мульти-нодный конфиг  
6. пользователь выбирает страну/узел в клиентском приложении

## 4. Компоненты и ответственность

### 4.1 `portal_bot/bot.py`

- пользовательские и админские сценарии;
- paywall на канал для starter;
- QR-выдача ключа;
- panic flow;
- manual user операции из админки;
- синхронизация пользователей по нодам через control panel layer.

### 4.2 `portal_bot/helpbot.py`

- отдельная точка входа поддержки;
- создание/просмотр тикетов;
- операторская очередь (для админа);
- единая БД тикетов с основным контуром.

### 4.3 `portal_bot/api.py`

Группы endpoint'ов:
- public/user:
  - `/api/health`
  - `/api/reviews`
  - `/api/user/{tg_id}`
  - `/api/dashboard`
  - `/api/nodes/status`
  - `/api/nodes/diagnostics/run`
  - `/api/bonuses`, `/api/bonuses/channel/claim`
  - `/api/promo/redeem`
  - `/api/tickets*`
- admin:
  - `/api/admin/summary`
  - `/api/admin/users*`
  - `/api/admin/users/manual`
  - `/api/admin/users/{tg_id}/manual/{extend|block|regenerate-token}`
  - `/api/admin/broadcast`
  - `/api/admin/tickets*`
  - `/api/admin/nodes/{health|sync}`
- subscription:
  - `/s8Kx2mP7qR4wT/{token}`

### 4.4 `webapp/`

- стеклянный UI (Dashboard / Nodes / Support / Account / Legal);
- чтение данных из backend API;
- feature flags с backend (`haptic`, `lottie`);
- безопасная модель через Telegram `initData` + backend validation.

### 4.5 `marketing/`

- статический Next.js export;
- premium-структура страниц;
- CTA: внешний checkout (`PAY_CHECKOUT_URL`) или fallback в бот.

## 5. Схема данных (SQLite)

## 5.1 `users` (ключевые поля)

- идентификаторы: `tg_id`, `uuid`, `sub_token`
- план/статус: `sub_type`, `is_active`, `expiry_at`, `total_gb`
- монетизация/лояльность: `stars_paid`, `trial_used`, `referral_*`, `streak_*`
- support/bonus: `channel_bonus_claimed_at`
- manual user расширения:
  - `is_manual`
  - `created_by_admin`
  - `display_name`

## 5.2 `nodes` (ключевые поля)

- идентификация: `code`, `name`, `host`
- конфиг: `vless_port`, `reality_*`, `fingerprint`, `flow`
- panel доступ: `panel_base_url`, `panel_path`, `panel_user`, `panel_pass`, `inbound_id`
- роутинг и health: `enabled`, `weight`, `is_healthy`, `health_score`, `panel_latency_ms`, `active_clients`

## 5.3 Текущее состояние данных (live)

- users total: `17`
- users active: `17`
- users manual: `3`
- users paid: `6`
- users free: `8`
- tickets total: `3`
- nodes total: `5`
- nodes enabled: `5`
- free-nodes: `1`

## 6. Мульти-нодная логика и планы

- `PAID`: привязка к paid-пулу узлов;
- `FREE/Starter`: маршрутизация через выделенный free-pool;
- `MANUAL`: совместимый режим `tg_id < 0` + `is_manual/sub_type=MANUAL`;
- endpoint подписки возвращает несколько локаций (на проверке: `lines=4`, `hosts=4`).

## 7. Безопасность и секреты

- токены/пароли не хранятся в репозитории;
- runtime-секреты только в `/root/portal_bot/.env`;
- админ API закрыт role-check через `initData`;
- в URL WebApp не передаются UUID/секреты;
- публичные тексты и CTA адаптированы под бренд без нежелательной лексики.

## 8. Проверенные env-переменные (production)

### 8.1 Присутствуют

- `BOT_TOKEN`
- `HELP_BOT_TOKEN`
- `ADMIN_ID`
- `WEBAPP_URL`
- `PUBLIC_API_BASE_URL`
- `HOST_DOMAIN`

### 8.2 Не заданы (используются дефолты/fallback)

- `NEWS_CHANNEL_ID`
- `PAY_CHECKOUT_URL`
- `SUPPORT_BOT_USERNAME`
- `WEBAPP_ENABLE_HAPTIC`
- `WEBAPP_ENABLE_LOTTIE`

Рекомендация: явно задать эти переменные в `.env` для детерминированного поведения.

## 9. Операционный контур деплоя

### 9.1 Backend

- скрипт: `scripts/remote_deploy_brain_portal_code.py`
- шаги:
  - upload `portal_bot/*.py` -> `/root/portal_bot`
  - restart `portal-api`, `portal-bot`

### 9.2 Статика

- скрипт: `scripts/remote_deploy_brain_static_sites.py`
- шаги:
  - upload `webapp/dist` -> `/var/www/portal/webapp`
  - upload `marketing/out` -> `/var/www/portal/marketing`
  - reload/restart Caddy

### 9.3 Guardrails

- `scripts/check_script_manifest.py`
- `scripts/ci_check_artifacts.py`
- `.github/workflows/guardrails.yml`

## 10. Мощности (capacity) по live-снимку

## 10.1 Control-plane

| Node | vCPU | RAM (MB) | Disk root (MB) | Free root (MB) | OS |
|---|---:|---:|---:|---:|---|
| `brain` | 2 | 3903 | 39713 | 31432 | Ubuntu 22.04.5 LTS |

## 10.2 Worker nodes

| Node | Reachable by ops-SSH | vCPU | RAM (MB) | Disk root (MB) | Free root (MB) | Notes |
|---|---|---:|---:|---:|---:|---|
| `us` | yes | 1 | 1894 | 39713 | 31714 | healthy |
| `pl` | yes | 1 | 1894 | 39713 | 31705 | healthy |
| `it` | yes | 1 | 1894 | 39713 | 31714 | healthy |
| `free` | no (в момент проверки) | n/a | n/a | n/a | n/a | `Error reading SSH protocol banner` |

## 10.3 Вывод по headroom

- Control-plane: для текущего объема (`17` активных пользователей, 2 бота + API + статика) запас достаточный.
- Worker-пул: 1 vCPU / ~1.9 GB RAM на узел подходит для текущей нагрузки.
- Узкое место по управляемости: нет стабильного ops-SSH к `free` на момент среза.

## 11. Последний smoke (production)

Подтверждено:
- сервисы `active`;
- Telegram `getMe` для main/help bot — `ok=true`;
- `https://<domain>:2096/api/health` — `200`;
- `https://<domain>:8444/webapp/` — `200`, новые bundle assets;
- `https://<domain>:8444/` — `200`, новый marketing;
- admin/user API endpoint'ы отвечают `200`;
- подписочный endpoint стабилен.

Примечание по логам:
- в историческом журнале `portal-bot` есть старые error-события (до фикса и установки зависимостей);
- за последние 10 минут на момент финальной проверки — новых ошибок не обнаружено.

## 12. Риски и next actions

1. Явно задать отсутствующие env-флаги (`NEWS_CHANNEL_ID`, `PAY_CHECKOUT_URL`, `SUPPORT_BOT_USERNAME`, `WEBAPP_ENABLE_*`).
2. Включить и проверить `portal-node-metrics.timer` (сейчас `inactive`).
3. Восстановить стабильный ops-SSH доступ к `free` ноде.
4. Добавить регулярный post-deploy check в релизный сценарий:
   - services status
   - `api/health`
   - `api/admin/summary` (signed)
   - subscription host-count check

## 13. Связанные артефакты

- Live audit JSON: `docs/audit-artifacts/prod-audit-20260209-023635.json`
- Deployment scripts:
  - `scripts/remote_deploy_brain_portal_code.py`
  - `scripts/remote_deploy_brain_static_sites.py`
- Health/smoke utility:
  - `scripts/verify_brain_ready.py`

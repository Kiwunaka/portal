# 🛡️ Portal Bot — Полная документация

## 📊 Обзор системы

| Компонент | Описание |
|-----------|----------|
| **Bot** | Telegram бот (aiogram 3.x) |
| **Panel** | 3x-ui панель |
| **API** | FastAPI для WebApp |
| **DB** | SQLite (portal.db) |
| **Server** | Ubuntu 24.04 @ <CONTROL_PLANE_HOST> |

---

## 👤 Функции пользователя

### Главное меню
| Кнопка | Функция |
|--------|---------|
| ⚡ Зарядить | Покупка/продление подписки |
| 👤 Статус | Информация об аккаунте |
| 🔑 Мой ключ | Показать ссылку подписки |
| 📱 Инструкция | Как подключиться |
| 🎁 Бонусы | Реферальная система, колесо, ачивки |
| 📦 Ещё | Доп.функции |
| 🤖 Поддержка | Связь с админом |

### Бонусы
| Функция | Описание |
|---------|----------|
| 🎁 Пригласить друга | Реферальная ссылка (+бонусные дни за реферала) |
| 🏆 Ачивки | Система достижений |
| 🎰 Колесо Фортуны | Рандомные призы (раз в 3 дня) |
| 🔥 Streak | Ежедневный бонус за вход |

### Ещё
| Функция | Описание |
|---------|----------|
| 🎫 Подарить | Подарочные карты |
| 🔗 MTProto | Прокси для Telegram |
| 📤 Поделиться | (отключено) |
| 🎟️ Промокод | Активировать промокод |
| ⭐ Оставить отзыв | Оценка сервиса |

---

## ⚙️ Админ-панель

### Доступ
```
/start → ⚙️ Админка (только для ADMIN_ID)
```

### Меню администратора
| Кнопка | Функция |
|--------|---------|
| 🔍 Найти юзера | Поиск по @username или ID |
| 👥 Все юзеры | Список всех пользователей |
| 🎫 Промокоды | Создание и управление |
| ⭐ Отзывы | Модерация отзывов |
| 📢 Рассылка | Broadcast сообщений |
| 🎰 Рулетка | Настройки колеса фортуны |
| 📊 Mass-действия | Массовые операции |
| ❤️ Health | Проверка здоровья системы |
| 🔄 Sync | Синхронизация username'ов |
| 🎁 Подарить | Подарить подписку юзеру |

---

## 📢 Рассылка (Broadcast)

### Кастомное сообщение
```
Текст сообщения
---
🔗 Кнопка|https://example.com
```

### Шаблоны
| Команда | Описание |
|---------|----------|
| `/template add KEY текст` | Создать шаблон |
| `/template list` | Список шаблонов |
| `/template send KEY` | Отправить всем |
| `/template send KEY @user` | Отправить юзеру |
| `/template delete KEY` | Удалить шаблон |

**Готовые шаблоны:**
- `welcome` — приветствие
- `update` — уведомление об обновлении
- `promo` — промо-рассылка
- `expiring` — напоминание об истечении
- `holiday` — праздничное поздравление

---

## 🎫 Промокоды

### Создание
```
/promo create CODE days 10 100
```
- `CODE` — код промокода
- `days` — тип (days = дни, discount = скидка)
- `10` — значение (дни или %)
- `100` — макс. использований

### Управление
```
/promo list — список активных
/promo delete CODE — удалить
```

---

## 📊 Mass-действия

| Действие | Описание |
|----------|----------|
| 📅 Продлить всем | Добавить N дней всем активным |
| 🔄 Sync на ноды | Пересоздать/нормализовать клиентов на нодах (в т.ч. снять старые лимиты) |
| ⚠️ Напомнить истекающим | Отправить напоминание (за 3 дня до конца) |

**Исключения:** PROTECTED_USERS (не затрагиваются mass-действиями)

---

## 👤 Управление юзером

### Кнопки в карточке юзера
| Кнопка | Действие |
|--------|----------|
| ➕ 30 дней | Продлить на 30 дней |
| ➕ 7 дней | Продлить на 7 дней |
| 🔁 Sync на ноды | Применить актуальную конфигурацию нод и снять старые лимиты в панелях |
| 📨 Отправить ссылку | Переотправить юзеру ссылку подписки |
| 🎫 Сменить тариф | Установить тариф |
| 🔒 Отключить | Заблокировать доступ |
| 🗑️ Удалить | Удалить юзера полностью |

### Тарифы
| Тариф | Дней |
|-------|------|
| 🆓 Free | ∞ |
| 📅 1 месяц | 30 |
| 📅 3 месяца | 90 |
| 📅 6 месяцев | 180 |
| 📅 1 год | 365 |

---

## 💾 Бэкапы

### Скрипт бэкапа
```bash
/root/portal_bot/backup_db.sh
```

### Автоматический бэкап (crontab)
```bash
crontab -e
# Добавить:
0 3 * * * /root/portal_bot/backup_db.sh
```

### Восстановление
```bash
gunzip /root/backups/portal_2024-12-28.db.gz
cp /root/backups/portal_2024-12-28.db /root/portal_bot/portal.db
systemctl restart portal-bot
```

---

## 🔧 Сервисы

### Управление
```bash
systemctl status portal-bot   # Статус бота
systemctl status portal-api   # Статус API
systemctl restart portal-bot  # Перезапуск бота
systemctl restart portal-api  # Перезапуск API
journalctl -u portal-bot -f   # Логи бота
journalctl -u portal-api -f   # Логи API
```

### Деплой
```bash
# С локального компьютера:
python scripts/remote_deploy_brain_portal_code.py --brain-ip <CONTROL_PLANE_HOST> --ssh-port 29374
```

---

## 📁 Структура файлов

```
/root/portal_bot/
├── bot.py          # Основной бот
├── api.py          # FastAPI сервер
├── portal.db       # База данных
├── .env            # Конфигурация
├── backup_db.sh    # Скрипт бэкапа
└── webapp/         # Web-приложение

/root/backups/      # Бэкапы БД
```

---

## 🔐 Переменные окружения (.env)

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен Telegram бота |
| `ADMIN_ID` | ID администратора |
| `PROTECTED_USERS` | Список защищённых юзеров |
| `PANEL_URL` | URL 3x-ui панели |
| `PANEL_USER` | Логин панели |
| `PANEL_PASS` | Пароль панели |
| `INBOUND_ID` | ID inbound в панели |
| `DATABASE_URL` | Путь к БД |
| `SUPPORT_USERNAME` | Username поддержки |

---

## 📈 Статистика

### В боте
- **Health check** — CPU, RAM, диск, uptime, юзеры
- **Карточка юзера** — потраченные звёзды, использованный трафик

### В базе данных
- `stars_paid` — всего оплачено звёзд
- `total_gb` — лимит трафика
- `expiry_at` — дата окончания
- `created_at` — дата регистрации

---

## 🆘 Возврат средств

1. Найти юзера: `🔍 Найти юзера → @username`
2. Проверить `⭐ Звёзд: N` — сумма оплат
3. Если нужен возврат — оформить через Telegram Stars

---

## 📞 Контакты

- **Поддержка:** @kiwunaka
- **Сервер:** <CONTROL_PLANE_HOST>
- **Панель:** https://<your-domain>:8444/<panel_path>/panel/

## 2026-02 Policy Update

New env variables for plan control:
- `SUPPORT_USERNAME` (default: `portal_privacy_helpbot`)
- `FREE_LIMIT_IP` (default: `2`)
- `PAID_LIMIT_IP` (default: `5`)
- `FREE_TOTAL_GB` (default: `40`)
- paid traffic is always unlimited by design

Node-level overrides are supported in `panel_client.py` through `NODE_<CODE>_...` vars.

Optional Free speed limit paths:
- aggregate on port: `infra/install_free_egress_shaper.sh`
- per-IP approximation: `infra/install_free_per_ip_limiter.sh`

## 2026-02 Support Workflow (Phase 1)

Bot now has built-in ticket flow:
- User side: `Support -> Ticket: New`, `Support -> Ticket: My`, reply/close/reopen.
- Operator side: `Admin -> Ticket queue`, open ticket, claim, reply, close/reopen.

Data model:
- `support_tickets`
- `support_ticket_messages`

Quick health check after deploy:
1. Open ticket as user and send first message.
2. Verify admin receives notification and can open `Admin -> Ticket queue`.
3. Reply from admin and verify user gets notification.
4. Verify worker process is running (if standalone deploy): `systemctl status portal-worker --no-pager`.
5. Verify node metrics timer:
   - `systemctl status portal-node-metrics.timer --no-pager`
   - `systemctl list-timers --all | grep portal-node-metrics`
6. Verify metrics freshness in DB:
   - `sqlite3 /root/portal_bot/portal.db "select max(sampled_at) from node_health_samples;"`
7. Verify admin metrics endpoint returns fresh state:
   - `GET /api/admin/metrics/status` from authenticated admin WebApp session.

## Brain Network Probe

Use this script to check worker reachability from `brain`:

```bash
python scripts/remote_brain_network_probe.py
```

Default probes:
- `443`
- `8443`
- `29374`

## PostgreSQL Cutover (Phase 2)

Use environment-only credentials. Do not store DSN secrets in git.

1. Prepare target DB URL:
   - `POSTGRES_DATABASE_URL=postgresql+psycopg2://<user>:<pass>@<host>:5432/<db>`
2. Keep SQLite source URL:
   - `SQLITE_DATABASE_URL=sqlite:////root/portal_bot/portal.db`
3. Run one-shot migration:
   - `python scripts/migrate_sqlite_to_postgres.py --truncate-target`
4. Switch runtime:
   - set `DATABASE_URL=$POSTGRES_DATABASE_URL` in `/root/portal_bot/.env`
5. Restart services:
   - `systemctl restart portal-api portal-bot portal-helpbot portal-worker`
6. Verify:
   - `GET /api/health`
   - paid flow / subscription endpoint / admin dashboard / tickets.

## Legacy Bot Redirect

To keep old bot online with a fixed migration notice:

1. In `/root/portal_bot/.env` set:
   - `LEGACY_BOT_TOKEN=<old_bot_token>`
   - `BOT_MIGRATION_TARGET_URL=https://t.me/portal_service_bot`
2. Run:
   - `python /root/portal_bot/legacy_redirect_bot.py`

This bot only sends migration text + button to the new bot and does not process payments.

## Client App Links Via Env

The API endpoint `GET /api/client/apps` returns links for Android/Windows clients.

Set these environment variables in `/root/portal_bot/.env`:

- `APP_ANDROID_PLAY_URL`
- `APP_ANDROID_APK_URL`
- `APP_ANDROID_MIRROR_URL`
- `APP_WINDOWS_EXE_URL`
- `APP_WINDOWS_MIRROR_URL`
- `APP_DOCS_URL`

Apply and restart:

```bash
systemctl restart portal-api portal-bot
```

## Release Checklist (Android/Windows Artifacts)

1. Publish APK/EXE to GitHub Releases in the client fork.
2. Mirror artifacts to your download host.
3. Update env URLs listed above.
4. Restart backend services.
5. Deploy static apps (`webapp`, `marketing`).
6. Run smoke:
   - `python scripts/smoke_client_apps.py --base-url https://<domain>:2096 --init-data '<telegram_init_data>' --insecure`
7. Verify endpoints:
   - `GET /api/health`
   - `GET /api/client/apps`
8. Verify download links return `200/302` and installation docs open correctly.

## Legal Gate Record

Commercial fork permission for the selected client core is treated as approved for this project release cycle. Keep the written approval in your private operator archive and reference release date + approver in release notes.

## 2026-02 L4 Rollout (Brain as Router)

Goal:
- keep `brain` as control-plane/site/bot host
- route user traffic by geo through L4 on `:443`
- keep Italy risk low with phased cutover

Phase A:
1. Configure HAProxy TCP routing on brain (`infra/brain-haproxy-l4.cfg`).
2. Move Caddy to internal `:4443` (`infra/Caddyfile.internal`).
3. Point DNS `pl.<domain>`, `nl.<domain>`, `free.<domain>` to brain.
4. Keep `it.<domain>` on direct worker IP.
5. Observe 24-48h (latency/error/active sessions).

Phase B:
1. Point `it.<domain>` to brain.
2. Re-check latency/error against baseline before/after switch.

Safety:
- Do not disable direct worker DNS until cutover SLO gate passes.
- Keep rollback DNS records ready.

## 2026-02 Public URLs Without Custom Ports

Runtime defaults now assume:
- `PUBLIC_API_BASE_URL=https://<domain>`
- `WEBAPP_URL=https://<domain>/webapp/`

Quick checks:
- `GET https://<domain>/api/health`
- `GET https://<domain>/webapp/`
- `GET https://<domain>/s8Kx2mP7qR4wT/<token>`

After stabilization:
- close public `:8444`
- keep `:2096` only as temporary rollback path for one release window

## 2026-02 External Payment Callbacks

Implemented routes:
- `GET/POST /pay/success`
- `GET/POST /pay/fail`
- `POST/GET /api/payments/result/{provider}`
- `POST/GET /api/payments/refund/{provider}`
- `POST/GET /api/payments/chargeback/{provider}`
- `POST/GET /api/payments/freekassa/notify`

DB tables:
- `external_orders`
- `external_payment_events`

Runbook:
- `docs/16-payments-callback-runbook.md`

## 2026-02 Release: FREE policy + domains + payment URLs

### FREE defaults

- `FREE_LIMIT_IP=1`
- `FREE_TOTAL_GB=30`
- `FREE_SPEED_LIMIT_KBPS=6250` (50 Mbps)
- `FREE_CYCLE_DAYS=30`

### FREE monthly reset

- New DB fields in `users`: `free_cycle_anchor_at`, `free_cycle_last_reset_at`, `free_cycle_next_reset_at`.
- Worker job resets due FREE users every 30 days from anchor and applies panel-side traffic reset.

### Domains

- Site + web cabinet: `portal-privacy.online` (`/webapp/`)
- API + callbacks + subscription: `kiwunaka.space`

### Payment URLs for validation

Freekassa:
- Notify: `https://kiwunaka.space/api/payments/freekassa/notify` (`POST`)
- Success: `https://kiwunaka.space/pay/success` (`GET`)
- Fail: `https://kiwunaka.space/pay/fail` (`GET`)

Cardlink:
- Store: `https://portal-privacy.online/`
- Success: `https://kiwunaka.space/pay/success`
- Fail: `https://kiwunaka.space/pay/fail`
- Result: `https://kiwunaka.space/api/payments/result/cardlink`
- Refund: `https://kiwunaka.space/api/payments/refund/cardlink`
- Chargeback: `https://kiwunaka.space/api/payments/chargeback/cardlink`

### Fee math (RUB)

- `net = ((P * 0.935) - 2) * 0.965 = 0.902275 * P - 1.93`
- `fee = P - net = 0.097725 * P + 1.93`

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

## Brain Network Probe

Use this script to check worker reachability from `brain`:

```bash
python scripts/remote_brain_network_probe.py
```

Default probes:
- `443`
- `8443`
- `29374`

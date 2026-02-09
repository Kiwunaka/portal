# WebApp Menu/Funnel Benchmark + Implementation (2026-02-08)

## Цель

Ускорить parity WebApp относительно бота и поднять качество UX по user/admin сценариям на базе референсов магазинов/ботов.

## Orchestration Streams

- `A-menu-miner`:
  - разобрал структуру user/admin меню и callback-ветки в референсах.
- `B-funnel-miner`:
  - вынес воронки: onboarding, support, 1:1 сообщение, broadcast.
- `C-payment-miner`:
  - зафиксировал подходы к внешним платежкам и webhook-слоям (без внедрения в этом цикле).
- `D-webapp-implementation`:
  - внедрил UI/UX изменения в `webapp/src/App.tsx` и `webapp/src/styles.css`.

## Изученные источники

- `https://github.com/Jolymmiels/remnawave-telegram-shop`
- `https://github.com/kavore/remnawave-tg-shop`
- `https://github.com/snoups/remnashop`
- `https://github.com/maposia/remnawave-telegram-sub-mini-app`
- `https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot`

Примечание: `https://docs.rw/docs/clients` в этой сессии не открылся из-за timeout.

## Что перенесено в наш WebApp

### User-side

- Более плотная главная с KPI:
  - тариф, срок, лимит устройств, трафик.
- Воронка подключения в 3 шага:
  - импорт/копирование ссылки,
  - deep-link кнопки клиента,
  - оплата через бот (Stars).
- Бонусный сценарий:
  - отдельная карточка «подписка на канал -> +дни premium».
- Поддержка:
  - создание тикета,
  - просмотр очереди своих тикетов,
  - диалог по тикету в WebApp,
  - переход в helpbot по deep-link.
- Отзывы:
  - рейтинг + текст, обновляемый список.

### Admin-side

- Сводка:
  - users/tickets/nodes метрики + top nodes.
- Тикеты:
  - фильтры по статусам,
  - просмотр ленты сообщений,
  - reply / in_progress / close.
- Пользователи:
  - поиск по username/tg_id,
  - карточка пользователя,
  - отправка 1:1 сообщения,
  - sync конкретного пользователя.
- Рассылка:
  - сегменты `all_active|paid|free|expired|custom`,
  - `custom` поддерживает отправку ровно одному пользователю.
- Ноды:
  - health/liveness таблица,
  - sync по сегменту (`active|free|paid`).

### UX/Visual

- Добавлены:
  - toast-уведомления,
  - loading/busy состояния действий,
  - улучшенные карточки диалогов,
  - шаги онбординга,
  - micro-interactions у кнопок.

## Что сознательно не делали в этом проходе

- Интеграция сторонних payment-провайдеров в обход Telegram правил.
- Полная 1:1 миграция всех legacy-admin callback веток из большого бот-меню.
- Перевод всей логики helpbot в WebApp-only режим (сохранен dual-channel intake: WebApp + helpbot).

## Валидация

- `npm.cmd run build` (webapp) — OK.
- `python -m pytest tests/test_portal_api.py -q` — OK (4 passed).

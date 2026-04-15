# Жизненный цикл нод PORTAL

Обновлено: 7 марта 2026

## Что проверил

- текущую модель `nodes` / `user_nodes` в `portal_bot/models.py`;
- выбор нод для пользователя в `portal_bot/api.py`;
- multi-node sync в `portal_bot/control_panel.py`;
- admin screen `/admin/nodes` и drift-check;
- production-ориентированные runbook'и по нодам и panel strategy.

## Что нашёл

- `UserNode` уже был source of truth для фактических назначений, но часть API ещё жила по legacy-логике "все enabled paid nodes";
- для взрослого управления не хватало трёх состояний:
  - нода активна и принимает новых;
  - нода активна, но находится в `drain`;
  - нода полностью выключена из runtime;
- до этого resync пользователей приходилось мыслить как ручной процесс через panel, а не как операцию `PORTAL`.

## Что изменил

- `PORTAL` теперь хранит lifecycle-флаги ноды:
  - `enabled`
  - `accepting_new_clients`
  - `is_draining`
- выдача нод пользователю теперь сначала уважает реальные `user_nodes`, и только потом использует fallback по плану;
- появились admin-операции:
  - `POST /api/admin/nodes/{code}/drain`
  - `POST /api/admin/nodes/{code}/enable`
  - `POST /api/admin/nodes/{code}/disable`
  - `POST /api/admin/nodes/{code}/resync`
- `/admin/nodes` показывает lifecycle-состояние и количество `mapped_users`.

## Правила source of truth

- `PORTAL` — главный источник истины по состоянию нод и назначению пользователей.
- `3x-ui` — node-local исполнительный слой.
- `user_nodes` — авторитетный список реальных назначений пользователя на ноды.
- Если `user_nodes` для пользователя не пустой, подписка и user-facing API должны опираться на эти маппинги.
- При этом user-facing выдача обязана дополнительно фильтровать маппинги по текущему плану:
  - premium не должен видеть `free`/`brain`;
  - free не должен видеть premium-ноды;
  - legacy-мусор в `user_nodes` не должен ломать UI и подписку.
- Fallback "все доступные ноды по плану" допустим только для legacy-пользователей без маппингов.

## Состояния ноды

### 1. Active

- `enabled = true`
- `accepting_new_clients = true`
- `is_draining = false`

Поведение:
- нода участвует в новых назначениях;
- нода видна в runtime и admin;
- sync пользователей может создавать на ней новые client records.

### 2. Drain

- `enabled = true`
- `accepting_new_clients = false`
- `is_draining = true`

Поведение:
- новые назначения на ноду не идут;
- уже назначенные пользователи продолжают видеть и использовать ноду, пока не выполнен resync;
- панель и runtime остаются доступными;
- это безопасное состояние перед миграцией пользователей.

### 3. Disabled

- `enabled = false`
- `accepting_new_clients = false`
- `is_draining = false`

Поведение:
- нода исключена из runtime-пула;
- не участвует в новых назначениях и не попадает в пользовательскую выдачу;
- переводить в это состояние безопасно только после resync или с осознанным `force`.

## Как правильно выводить ноду из эксплуатации

1. Перевести ноду в `drain`.
2. Убедиться, что новые назначения на неё остановились.
3. Запустить controlled `resync`.
4. Проверить, что `mapped_users` у ноды стало `0`.
5. Только после этого делать `disable`.

## Что делает controlled resync

- выбирает пользователей, у которых `user_nodes` указывают на source-ноду;
- вычисляет target-ноды через `PORTAL`, а не через ручную логику panel;
- создаёт/актуализирует client records на target-нодах;
- отключает клиента на source-ноде;
- обновляет `user_nodes`, чтобы source-нода ушла из маппинга пользователя;
- пишет admin audit.

## Когда `disable` должен быть запрещён

- если у ноды ещё есть `mapped_users`, обычный `disable` должен возвращать конфликт;
- это защита от случайного "выключили ноду, а пользователи всё ещё на ней висят".

## Как проверил

- backend regression tests:
  - mapped nodes override legacy fallback;
  - disable блокируется без resync;
  - resync переносит пользователя и чистит source mapping.
- admin `/admin/nodes` показывает lifecycle flags и даёт действия без захода в panel.
- для production-аудита premium coverage теперь есть отдельный операторский сценарий:
  - `python scripts/remote_audit_paid_node_coverage.py --brain-ip <IP>`
- для безопаского ремонта только недостающих premium-маппингов:
  - `python scripts/remote_audit_paid_node_coverage.py --brain-ip <IP> --repair`
- для очистки legacy premium-маппингов на `brain/free`:
  - `python scripts/remote_audit_paid_node_coverage.py --brain-ip <IP> --cleanup-disallowed`

## Что осталось / риск

- lifecycle уже взрослый на уровне `PORTAL`, но операторский SSH-доступ к отдельным нодам всё равно надо постепенно переводить на нормальные ключи;
- `drain/disable/resync` не должны заменять аварийный manual access, а должны сводить его к редким исключениям.

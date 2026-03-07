# Аудит runtime нод и panel-слоя (2026-03-07)

Обновлено: 7 марта 2026

## Что проверил

- текущие authoritative docs в репозитории;
- runtime состояние `brain` и delivery-нод через SSH;
- `x-ui`/`xray` инбаунды и panel settings;
- production `DATABASE_URL` и фактическую runtime DB;
- collector/timer метрик;
- различия между текущими доками и реальным продом;
- внешние источники по `3x-ui` vs direct `Xray-core` vs `Hiddify`.

## Что нашёл

### 1. Production DB уже не SQLite

- На `brain` production сервисы читают `DATABASE_URL` из `/root/portal_bot/.env`.
- Текущий production runtime использует `Postgres`.
- Локальный `/root/portal_bot/portal.db` существует, но не является текущим source of truth прода.

### 2. Реальный delivery pool отличается от части старых доков

Срез по production DB на 7 марта 2026:
- `brain` — `enabled=false`
- `free` — `enabled=true`
- `it` — `enabled=true`
- `nl` — `enabled=true`
- `pl` — `enabled=true`
- `us` — `enabled=true`

Итого:
- `brain` — control-plane;
- delivery pool — `free/it/nl/pl/us`.

### 3. Текущий protocol/profile один

Подтверждённый стандартный профиль:
- `protocol=vless`
- `network=tcp`
- `security=reality`
- `port=443`

Проверенные runtime inbound-факты:
- `brain`: `BRAIN Reality`, `443`
- `pl`: `PL Reality`, `443`
- `it`: `IT Reality`, `443`
- `us`: `US Reality`, `443`

Дополнительно на `pl` есть legacy inbound:
- `id=2`
- `port=8443`
- `remark=PL Free Reality`

Этот extra inbound есть на сервере, но он не отражён как primary runtime source of truth в текущей production DB.

### 4. Brain x-ui настроен корректно для текущей модели

Подтверждено на `brain`:
- `x-ui` активен;
- built-in sub server отключён;
- `subPort=2097`;
- portal subscription endpoint остаётся на `:2096`.

Это соответствует правильной модели для проекта:
- подписку собирает PORTAL;
- panel не владеет пользовательским subscription flow.

### 5. Метрики живут, но старые runbook'и частично устарели

- `portal-node-metrics.timer` активен и тикает;
- `portal-node-metrics.service` успешно пишет новые samples;
- `node_health_samples` свежие в production DB;
- часть старых доков по-прежнему проверяет SQLite и старый auth-path для `/api/admin/metrics/status`.

### 6. `/api/admin/metrics/status` теперь защищён строже

- endpoint требует Telegram admin auth;
- старые инструкции с plain `X-Admin-Id` больше не соответствуют текущему runtime-контракту.

### 7. Доступ к `free`-ноде с локального password inventory не подтвердился

- Collector на brain успешно собирает метрики `free`, то есть runtime path жив.
- Но локальная SSH-проверка через имеющийся inventory не прошла.

Практический вывод:
- это не обязательно значит, что нода сломана;
- это значит, что локальный операторский доступ/инвентарь нужно считать отдельной зоной проверки, а не автоматически доверять старому файлу паролей.

## Что изменил

- Обновил current-state docs под фактический runtime:
  - `docs/01-overview.md`
  - `docs/02-ops-control-plane.md`
  - `docs/03-ops-node.md`
  - `docs/08-node-inventory.md`
  - `docs/31-capacity-and-infra-runbook-2026-03.md`
  - `docs/32-protocols-rf-blocking-rd-2026-03.md`
  - `docs/33-release-execution-runbook-2026-03.md`
  - `docs/34-monitoring-slo-sla-2026-03.md`
  - `docs/PROJECT_MAP_RU.md`
  - `docs/ADMIN_FULL_GUIDE_RU.md`
  - `docs/METRICS_RU.md`
  - `docs/INFRA_PLAN_RU.md`
  - `docs/FINAL_REPORT_RU.md`
  - `docs/SMOKE_TEST_CHECKLIST_RU.md`
- Добавил явную историческую оговорку в `docs/23-global-architecture-and-capacity-2026-02-09.md`.

## Как проверил

Локально:
- просмотр current docs и runtime-related scripts;
- сверка `portal_bot/api.py`, `control_panel.py`, `panel_client.py`, `scripts/collect_node_metrics.py`.

На серверах:
- SSH на `brain` и delivery nodes;
- проверка `x-ui` / `xray` / inbounds;
- проверка `subEnable/subPort` на `brain`;
- проверка production DB через runtime `DATABASE_URL`;
- проверка `portal-node-metrics.timer` и journal collector.

Внешние источники:
- `3x-ui` official repo;
- `Xray-core` official docs/repo;
- `Hiddify` official org/repo;
- актуальные материалы по blocking context из `Xray` issues и `Habr`.

## Что осталось / риск

- `pl:8443` (`PL Free Reality`) остаётся legacy-контуром: он жив на сервере, но не описан как primary runtime path в production DB.
- Локальный операторский доступ к `free`-ноде надо отдельно привести в порядок и перепроверить актуальность inventory/credentials.
- Если в будущем будет рост числа нод или усилится требование к GitOps, стоит вернуться к вопросу direct `Xray-core`. На текущем масштабе `3x-ui` остаётся приемлемым компромиссом.

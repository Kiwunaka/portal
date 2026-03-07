# Infra Plan PORTAL

Обновлено: 7 марта 2026

## Текущее состояние

- control plane: `brain`
- enabled delivery nodes: `free`, `it`, `nl`, `pl`, `us`
- `brain` не участвует в текущей выдаче как delivery node
- production DB уже находится на `Postgres`
- текущая пользовательская база небольшая, поэтому главная задача сейчас не expansion, а стабильность, наблюдаемость и контроль дрейфа между доками и реальным runtime

## Текущий парк серверов

| Код | Физическое имя | Страна | Роль | План |
|---|---|---|---|---|
| `brain` | `BRAINnode` | `DE` | control-plane | `2 vCPU / 4 GB RAM / 60 GB NVMe` |
| `pl` | `PLnode` | `PL` | premium delivery | `1 vCPU / 2 GB RAM / 40 GB NVMe` |
| `it` | `ITnode` | `IT` | premium delivery | `1 vCPU / 2 GB RAM / 40 GB NVMe` |
| `nl` | `NLnode` | `NL` | premium delivery | `1 vCPU / 2 GB RAM / 40 GB NVMe` |
| `us` | `USnode` | `US` | premium delivery | `1 vCPU / 2 GB RAM / 40 GB NVMe` |
| `free` | `FREENLnode` | `NL` | dedicated free pool | `1 vCPU / 1 GB RAM / 40 GB NVMe` |

## Рекомендация на сейчас

- не добавлять новые paid nodes до появления реальной нагрузки
- считать `free` node single point of failure только для free-контура; paid-контур уже опирается на отдельные `it/nl/pl/us`
- держать фокус на:
  - свежести collector metrics
  - стабильности panel sync
  - мониторинге unhealthy/stale состояний
  - документировании фактического runtime state, а не исторических SQLite-снимков

## Когда масштабировать

- sustained рост active users
- рост concurrent sessions и traffic на node
- ухудшение latency / health score
- регулярные ошибки panel sync

## Что делать с 3x-ui

- На масштабе `30-100` пользователей миграция с `3x-ui` не обязательна.
- Правильная модель сейчас:
  - `PORTAL` = source of truth;
  - `3x-ui` = node-local management layer;
  - `Xray` = data plane.
- На масштабе `500-1000` пользователей стоит планировать переход к собственному control-plane поверх direct `Xray-core`.
- Отдельная стратегия описана в `docs/PANEL_STRATEGY_RU.md`.

## Грубая ёмкость парка при порте 1 Гбит/с на ноду

Оценка ниже не равна теоретическому максимуму линка. Для планирования используем рабочий коридор примерно `300-500 Мбит/с` sustained на delivery-ноде, чтобы сохранить запас на пики и деградации.

| Масштаб | Рекомендация по paid delivery-нодам | Практический вывод |
|---|---|---|
| `30 пользователей` | `3-4 paid` | текущего парка достаточно с запасом |
| `100 пользователей` | `4-5 paid` | текущий парк почти достаточен |
| `500 пользователей` | `6-8 paid` | надо готовить шаблон роста и автоматизацию |
| `1000 пользователей` | `10-12 paid` | парк в `15` нод уже выглядит разумным |

## Политика отключения / расширения

- если node стабильно unhealthy или под блокировкой:
  - выключить её из выдачи
  - не удалять сразу данные пользователя
  - провести resync на рабочие nodes
- если free node нестабильна:
  - ограничить её участие только в free-сценариях
  - не смешивать с paid delivery

## Canary-политика

- Любые transport/network изменения катим не на всех сразу.
- Минимальная схема:
  - 1 нода или ограниченная группа пользователей
  - отдельный campaign/start-link
  - сравнение support-жалоб, callback-пути, open tickets и retention-сигналов до/после

Stop-сигналы для отката:
- рост open tickets
- рост reconnect-жалоб
- деградация health score
- всплеск ручных обращений из конкретного региона/оператора

## Что считаем достаточной устойчивостью

- минимум 2 здоровые рабочие ноды для paid-контура
- `portal-node-metrics.timer` свежий
- `/api/admin/metrics/status` = `fresh` при admin-auth
- `node_health_samples` свежие в production DB
- rollout делается через canary, а не одним массовым переключением

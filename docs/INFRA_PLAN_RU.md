# Infra Plan PORTAL

Обновлено: 7 марта 2026

## Текущее состояние

- control plane: `brain`
- enabled delivery nodes: `free`, `it`, `nl`, `pl`, `us`
- `brain` не участвует в текущей выдаче как delivery node
- production DB уже находится на `Postgres`
- текущая пользовательская база небольшая, поэтому главная задача сейчас не expansion, а стабильность, наблюдаемость и контроль дрейфа между доками и реальным runtime

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

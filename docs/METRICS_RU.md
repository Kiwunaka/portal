# Метрики и наблюдаемость PORTAL

Обновлено: 6 марта 2026

## Что уже есть

- `portal-node-metrics.timer`
- collector `scripts/collect_node_metrics.py`
- admin API:
  - `/api/admin/summary`
  - `/api/admin/metrics/status`
  - `/api/admin/metrics/timeseries`
  - `/api/admin/nodes/traffic`
  - `/api/admin/nodes/health`

## Что фиксировано в этой волне

- deploy script теперь копирует `collect_node_metrics.py` в путь, который ожидает systemd unit на brain.
- metrics freshness включён в release-gate контроль.

## Минимальный рабочий набор метрик

- пользователи:
  - total / active / free / paid
- деньги:
  - Stars
  - RUB / external orders
- ноды:
  - health
  - latency
  - traffic bytes / GB
  - active clients
- ошибки:
  - stale metrics
  - unhealthy nodes
  - payment callback failures
  - subscription numeric fallback hits
  - open tickets

## Что ещё добавить в `/admin`

- отдельный error-summary блок
- счётчик `numeric_fallback_hits` за день
- breakdown revenue по каналу оплаты

# Метрики и наблюдаемость PORTAL

Обновлено: 7 марта 2026

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
- бонусы:
  - channel bonus success / denied
  - promo redeem success / denied
  - gift redeem success / denied

## Что добавлено в `/admin` в этой волне

- отдельный error-summary блок на dashboard
- статус freshness c возрастом метрик и временем последнего сэмпла
- явный список приоритетных действий для оператора по stale metrics, unhealthy nodes, callback failures, numeric fallback hits и open tickets
- отдельный bonus analytics блок за 24 часа для channel/promo/gift flow с success/denied breakdown

## Что ещё можно добавить позже

- breakdown revenue по каналу оплаты

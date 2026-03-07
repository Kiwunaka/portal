# Метрики и наблюдаемость PORTAL

Обновлено: 7 марта 2026

## Runtime-срез на 7 марта 2026

- production metrics пишутся в `Postgres`, а не в локальный `portal.db`;
- `portal-node-metrics.timer` активен и collector пишет живые сэмплы в `node_health_samples`;
- enabled delivery nodes в runtime DB: `free`, `it`, `nl`, `pl`, `us`;
- `brain` присутствует в метриках исторически, но выключен из текущего delivery pool.

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

- deploy script копирует `collect_node_metrics.py` в путь, который ожидает systemd unit на brain
- metrics freshness включён в release-gate контроль

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

## Что добавлено в `/admin`

- отдельный error-summary блок на dashboard
- статус freshness с возрастом метрик и временем последнего сэмпла
- bonus analytics блок за 24 часа для channel/promo/gift flow с success/denied breakdown
- блок `Удержание и реактивация`

## Как смотреть это по-простому

- Если `expiring_3d > 0`, а `t3/t1/t0` почти пустые:
  - проверяем worker retention jobs и шаблоны
- Если `expired_7d` растёт, а `reactivation` пустой:
  - проверяем reactivation job и сегмент `expired`
- Если `single_point_risk=true`:
  - не катим рискованные сетевые изменения без canary
- Если `free_node_enabled=true`:
  - помним, что это fallback-слой, а не опора для массовой выдачи

## Как проверять свежесть правильно

### Через admin UI / API

- `GET /api/admin/metrics/status`
- важно: endpoint требует Telegram admin auth
- старый plain `X-Admin-Id` больше не является рабочим способом проверки

### Через server-side DB sanity

```bash
set -a
. /root/portal_bot/.env
set +a
psql "$DATABASE_URL" -At -c "select node_code, max(sampled_at) from node_health_samples group by node_code order by node_code;"
```

Эта проверка сейчас надёжнее, чем ручной просмотр локального `portal.db`.

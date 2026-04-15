# Capacity & Infrastructure Runbook (2026-03)

Обновлено: 7 марта 2026

## 1. Текущее состояние

- Пользователей в production БД: `31`, из них активных `25`, free `16`, paid `9` (срез 7 марта 2026).
- Enabled delivery nodes в runtime DB: `5` (`free`, `it`, `nl`, `pl`, `us`).
- `brain` остаётся control-plane хостом, но отключён из текущего delivery pool.
- Для текущей нагрузки пул избыточен; основной риск сейчас не емкость, а операционная управляемость и документарный дрейф.

## 2. Карта сервисов: brain vs worker

### 2.1 Brain (control plane)

- `portal-api` (FastAPI)
- `portal-bot`
- `portal-helpbot`
- `portal-worker` (если вынесен сервисом)
- Caddy/reverse-proxy/static
- production `Postgres`
- x-ui для panel/API integration; built-in sub server выключен и вынесен с `2096` на `2097`
- управляющие скрипты деплоя и диагностики

### 2.2 Worker nodes (data plane)

- `3x-ui / xray-core` inbounds
- единый production-профиль: `VLESS + TCP + Reality` на `443/tcp`
- клиентский трафик по странам
- источники health/latency/active-clients для collector

## 3. Модель capacity

Используем практическую формулу:

`required_nodes = ceil((U * B * C) / E)`

Где:
- `U` — активные пользователи,
- `B` — средняя скорость на пользователя в пике (Mbps),
- `C` — коэффициент одновременности (обычно `0.15..0.35`),
- `E` — эффективная пропускная способность ноды (рекомендуемо `650 Mbps` при `1 Gbps` линке).

Пример для `100` пользователей:
- при `B=10`, `C=0.2`, `E=650` -> `ceil(100*10*0.2/650)=1` (теоретический минимум),
- production-практика: минимум `3` paid-ноды для гео-резерва + `1` free-пул.

## 4. Пороги масштабирования

Добавлять новую paid-ноду, если выполняется любой пункт:
1. P95 CPU > `75%` более 15 минут в прайм-тайм.
2. P95 RTT к ноде > `220 ms` в RU-пробах 3 дня подряд.
3. Packet loss > `2%` в течение >= 30 минут.
4. Активные сессии > `300` на ноду (для 1 vCPU класса) 3 дня подряд.
5. Реальный throughput > `650 Mbps` более 10 минут.

Сразу `+2` ноды, если одновременно выполняются 2 и более пункта.

## 5. Метрики, которые должны быть зелёными

### 5.1 API/UI

- `/api/health` = `200`
- `/api/admin/metrics/status` = `fresh` при реальной admin-auth

### 5.2 Node metrics

- `portal-node-metrics.timer` = `enabled + active`
- `portal-node-metrics.service` выполняется каждые `60s`
- В production `Postgres.node_health_samples` обновляются:
  - `panel_latency_ms`
  - `active_clients`
  - `total_up_bytes`
  - `total_down_bytes`
  - `total_traffic_bytes`

## 6. Runbook: `portal-node-metrics.timer`

### 6.1 Установка/ремонт

- `python scripts/remote_install_node_metrics_timer.py --brain-ip <BRAIN_IP>`

### 6.2 Проверка

- `systemctl is-enabled portal-node-metrics.timer` -> `enabled`
- `systemctl is-active portal-node-metrics.timer` -> `active`
- `systemctl list-timers portal-node-metrics.timer --all`
- `journalctl -u portal-node-metrics.service -n 50 --no-pager`

### 6.3 Проверка свежести

Через admin API:
- `GET /api/admin/metrics/status`
- ожидаемо: `status=fresh`
- важно: endpoint требует Telegram admin auth

Через DB sanity:

```bash
set -a
. /root/portal_bot/.env
set +a
psql "$DATABASE_URL" -At -c "select node_code, max(sampled_at) from node_health_samples group by node_code order by node_code;"
```

## 7. Runbook: нестабильная `free` нода

### 7.1 Диагностика

1. Проверить collector-журнал на brain:
   - `journalctl -u portal-node-metrics.service -n 80 --no-pager`
2. Проверить сеть/маршрут:
   - `mtr -rw <free_ip>`
3. Проверить panel API с brain:
   - через `scripts/remote_brain_nodes_sanity.py`
4. Проверить runtime метрики:
   - `node_health_samples`
   - `/api/admin/nodes/health`

### 7.2 Rollback-safe действия

1. Временно выключить ноду в `nodes.enabled=false`.
2. Выполнить user-sync только на healthy-ноды.
3. Не удалять ноду из БД до root-cause.
4. После восстановления включить ноду и провести smoke.

## 8. Правила роста кластера

### 8.1 До 200 активных пользователей

- Держать минимум `3` paid-ноды + `1` free-ноду.
- Brain можно оставить single instance при хорошем бэкапе и быстрых restart-процедурах.

### 8.2 200-500 активных

- Добавить отдельный worker service host (если worker сейчас на brain).
- Удерживать Postgres как production source of truth и документировать все runtime queries через `.env`.
- Перейти на регулярный synthetic probe per-node (каждые 5 мин).

### 8.3 >500 активных

- Разнести API/bot/worker на отдельные VM.
- Ввести multi-region health routing policy.
- Подготовить warm standby ноду по каждому ключевому региону.

## 9. Post-change smoke checklist

1. `python -m unittest tests.test_worker_retention`
2. `python -m unittest tests.test_api_auth_and_tickets`
3. `cd webapp && npm.cmd run build`
4. На brain:
   - services active,
   - `portal-node-metrics.timer` active,
   - `node_health_samples` свежие в production DB,
   - `/api/admin/metrics/status` fresh при admin-auth,
   - `/s8Kx2mP7qR4wT/{token}` для test-user возвращает конфиг.

# Capacity & Infrastructure Runbook (2026-03)

Обновлено: 4 марта 2026

## 1. Текущее состояние
- Активных пользователей: 17.
- Нод в пуле: 5 (`us`, `pl`, `it`, `brain`, `free`).
- Для текущей нагрузки пул избыточен; основной риск сейчас не емкость, а операционная стабильность (`free` node SSH unstable).

## 2. Карта сервисов: brain vs worker

### 2.1 Brain (control plane)
- `portal-api` (FastAPI)
- `portal-bot` (main bot)
- `portal-helpbot`
- `portal-worker` (если вынесен сервисом)
- Caddy/reverse-proxy/static
- SQLite `portal.db`
- Управляющие скрипты деплоя/диагностики

### 2.2 Worker nodes (data plane)
- 3x-ui / xray-core inbounds
- Клиентский трафик по странам
- Локальные health/latency/active-clients источники для collector

## 3. Модель capacity

Используем практическую формулу для оценки необходимого числа paid-нод:

`required_nodes = ceil((U * B * C) / E)`

Где:
- `U` — активные пользователи,
- `B` — средняя скорость на пользователя в пике (Mbps),
- `C` — коэффициент одновременности (обычно 0.15..0.35),
- `E` — эффективная пропускная способность ноды (рекомендуемо 650 Mbps при 1 Gbps линке).

Пример для 100 пользователей:
- при `B=10`, `C=0.2`, `E=650` -> `ceil(100*10*0.2/650)=1` (теоретический минимум),
- production-практика: минимум 3 paid-ноды для гео-резерва + 1 free-пул.

## 4. Пороги масштабирования (добавление ноды)

Добавлять новую paid-ноду, если выполняется любой пункт:
1. P95 CPU > 75% более 15 минут в прайм-тайм.
2. P95 RTT к ноде > 220 ms в RU-пробах 3 дня подряд.
3. Packet loss > 2% в течение >= 30 минут.
4. Активные сессии > 300 на ноду (для 1 vCPU класса) 3 дня подряд.
5. Реальный throughput > 650 Mbps более 10 минут (или > 70% от наблюдаемого практического ceiling).

Сразу +2 ноды (а не +1), если одновременно выполняются 2 и более пункта.

## 5. Метрики, которые обязательно держать в green

### 5.1 API/UI
- `/api/health` = 200
- `/api/admin/metrics/status` = `fresh`

### 5.2 Node metrics
- `portal-node-metrics.timer` = enabled + active
- `portal-node-metrics.service` выполняется каждые 60s
- В `node_health_samples` обновляются:
  - `panel_latency_ms`
  - `active_clients`
  - `total_up_bytes`
  - `total_down_bytes`
  - `total_traffic_bytes`

## 6. Runbook: `portal-node-metrics.timer` (если inactive)

### 6.1 Установка/ремонт
- `python scripts/remote_install_node_metrics_timer.py --brain-ip <BRAIN_IP>`

### 6.2 Проверка
- `systemctl is-enabled portal-node-metrics.timer` -> `enabled`
- `systemctl is-active portal-node-metrics.timer` -> `active`
- `systemctl list-timers portal-node-metrics.timer --all`
- `journalctl -u portal-node-metrics.service -n 50 --no-pager`

### 6.3 API-проверка свежести
- `GET /api/admin/metrics/status`
- Ожидаемо: `status=fresh` и `last_sample_at` в пределах stale-window.

## 7. Runbook: нестабильная `free` нода

### 7.1 Диагностика (ручная)
1. Проверить SSH banner/доступность:
   - `ssh -p 29374 root@<free_ip>`
2. Проверить сеть/маршрут:
   - `mtr -rw <free_ip>`
3. Проверить x-ui/xray процессы:
   - `systemctl status x-ui`
   - `systemctl status xray`
4. Проверить panel API с brain:
   - через `scripts/remote_brain_nodes_sanity.py`

### 7.2 Rollback-safe действия
1. Временно выключить ноду в `nodes.enabled=false`.
2. Выполнить user-sync только на healthy-ноды.
3. Не удалять ноду из БД до root-cause.
4. После восстановления включить ноду и провести smoke (`/api/admin/nodes/health`, subscription endpoint, test user connect).

## 8. Правила роста кластера

### 8.1 До 200 активных пользователей
- Держать минимум 3 paid-ноды + 1 free-нода.
- Brain можно оставить single instance при хорошем бэкапе и быстрых restart-процедурах.

### 8.2 200-500 активных
- Добавить отдельный worker service host (если worker сейчас на brain).
- Подготовить миграцию на Postgres (если рост ticket/payment нагрузок).
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
   - `/api/admin/metrics/status` fresh,
   - `/s8Kx2mP7qR4wT/{token}` для test-user возвращает конфиг.

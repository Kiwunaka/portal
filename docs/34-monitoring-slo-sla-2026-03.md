# Monitoring Alerts + SLO/SLA (2026-03)

Обновлено: 7 марта 2026

## 1. Цель

Единая операционная матрица для контроля качества сервиса: что измеряем, где пороги, когда и кому эскалируем.

## 2. SLI / SLO

### 2.1 API доступность

- SLI: доля успешных ответов `GET /api/health` (2xx) за 30 дней
- SLO: >= `99.5%`

### 2.2 Подписочный endpoint

- SLI: доля успешных ответов `/s8Kx2mP7qR4wT/{token}` (не 5xx) за 30 дней
- SLO: >= `99.0%`

### 2.3 Checkout и активация

- SLI: доля заказов, где оплата дошла до активации без ручного вмешательства (15 минут)
- SLO: >= `98.5%`

### 2.4 Freshness метрик нод

- SLI: доля проверок `/api/admin/metrics/status`, где `status=fresh`
- SLO: >= `99.0%` за 30 дней
- Техническое условие: `portal-node-metrics.timer` enabled + active
- Практическая оговорка: endpoint требует Telegram admin auth; server-side sanity без admin session надо дублировать SQL-проверкой production `DATABASE_URL`

### 2.5 Support first response

- SLI: доля тикетов с первым ответом оператора <= 30 минут
- SLO: >= `95.0%`

## 3. Alert policy

### 3.1 P1

- `api/health` недоступен >= 5 минут
- subscription endpoint 5xx >= 20% за 10 минут
- массовая ошибка активации после оплаты (>= 5 кейсов за 15 минут)

### 3.2 P2

- `metrics/status=stale` два цикла подряд
- `portal-node-metrics.timer` inactive/failed
- рост ticket backlog > 20 открытых тикетов

### 3.3 P3

- SLO тренд ниже target в недельном окне
- падение конверсии checkout без явной аварии

## 4. Источники сигналов

- API health checks
- `portal-node-metrics.timer` + `portal-node-metrics.service` journal
- admin endpoints: `summary`, `metrics/status`, `metrics/timeseries`, `nodes/traffic`
- production DB query по `node_health_samples`
- payment callbacks + activation audit
- support ticket queue

## 5. Мини-runbook проверки перед релизом

1. `python scripts/release_orchestrator.py --gates-only`
2. `python scripts/admin_webapp_smoke.py`
3. На brain:
   - `systemctl is-enabled portal-node-metrics.timer`
   - `systemctl is-active portal-node-metrics.timer`
   - `journalctl -u portal-node-metrics.service -n 50 --no-pager`
   - `psql "$DATABASE_URL" -At -c "select max(sampled_at) from node_health_samples;"`
4. `python scripts/verify_brain_ready.py --brain-ip <BRAIN_IP> --web-domain <WEB_DOMAIN> --api-domain <API_DOMAIN>`

## 6. Ссылки

- Release runbook: `docs/33-release-execution-runbook-2026-03.md`
- Capacity + infra runbook: `docs/31-capacity-and-infra-runbook-2026-03.md`
- Runtime audit: `docs/35-node-runtime-and-panel-audit-2026-03-07.md`

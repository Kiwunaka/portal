# Monitoring Alerts + SLO/SLA (2026-03)

Обновлено: 5 марта 2026

## 1. Цель
Единая операционная матрица для контроля качества сервиса: что измеряем, где пороги, когда и кому эскалируем.

## 2. SLI / SLO

### 2.1 API доступность
- SLI: доля успешных ответов `GET /api/health` (2xx) за 30 дней.
- SLO: >= 99.5%.
- Error budget: 0.5%.

### 2.2 Подписочный endpoint
- SLI: доля успешных ответов `/s8Kx2mP7qR4wT/{token}` (не 5xx) за 30 дней.
- SLO: >= 99.0%.
- Доп. условие качества: `hosts >= 1` для платных пользователей, стабильность выдачи при повторных запросах.

### 2.3 Checkout и активация
- SLI: доля заказов, где оплата дошла до активации без ручного вмешательства (15 минут).
- SLO: >= 98.5%.

### 2.4 Freshness метрик нод
- SLI: доля проверок `/api/admin/metrics/status`, где `status=fresh`.
- SLO: >= 99.0% за 30 дней.
- Техническое условие: `portal-node-metrics.timer` enabled + active.

### 2.5 Support first response
- SLI: доля тикетов с первым ответом оператора <= 30 минут.
- SLO: >= 95.0%.

## 3. Alert policy

### 3.1 P1 (немедленно)
- `api/health` недоступен >= 5 минут.
- Subscription endpoint 5xx >= 20% за 10 минут.
- Массовая ошибка активации после оплаты (>= 5 кейсов за 15 минут).

Действия:
1. Сообщение в админ-канал.
2. Открыть инцидентный тикет.
3. Откат на последнюю rollback-safe точку из release runbook.

### 3.2 P2 (в течение часа)
- `metrics/status=stale` два цикла подряд.
- `portal-node-metrics.timer` inactive/failed.
- Рост ticket backlog > 20 открытых тикетов.

### 3.3 P3 (плановые)
- SLO тренд ниже target в недельном окне.
- Падение конверсии checkout без явной аварии.

## 4. SLA (внутренний операционный)
- P1: triage <= 10 минут, mitigation <= 30 минут.
- P2: triage <= 30 минут, mitigation <= 4 часа.
- P3: triage <= 1 рабочий день, fix в плановом релизе.

## 5. Источники сигналов
- API health checks.
- `portal-node-metrics.timer` + `portal-node-metrics.service` journal.
- admin endpoints: `summary`, `metrics/status`, `metrics/timeseries`, `nodes/traffic`.
- payment callbacks + activation audit.
- support ticket queue.

## 6. Мини-runbook проверки перед релизом
1. `python scripts/release_orchestrator.py --gates-only`
2. `python scripts/admin_webapp_smoke.py`
3. На brain:
   - `systemctl is-enabled portal-node-metrics.timer`
   - `systemctl is-active portal-node-metrics.timer`
   - `journalctl -u portal-node-metrics.service -n 50 --no-pager`
4. `python scripts/verify_brain_ready.py --brain-ip <BRAIN_IP> --web-domain <WEB_DOMAIN> --api-domain <API_DOMAIN>`

## 7. Ссылки
- Release runbook: `docs/33-release-execution-runbook-2026-03.md`
- Capacity + free node runbook: `docs/31-capacity-and-infra-runbook-2026-03.md`
- Protocol blocking R&D: `docs/32-protocols-rf-blocking-rd-2026-03.md`

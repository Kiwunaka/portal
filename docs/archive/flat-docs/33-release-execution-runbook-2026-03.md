# Release Execution Runbook (2026-03)

Обновлено: 7 марта 2026

Этот документ описывает безопасную выкладку с quality gates и rollback-safe точками.

## 1. Предусловия

- ветка содержит все изменения этапа
- секреты не хранятся в репозитории
- у оператора есть SSH-доступ к brain
- production source of truth — `DATABASE_URL` из `/root/portal_bot/.env`

## 2. Локальные гейты

### Вариант A: оркестратор

- только quality gates:
  - `python scripts/release_orchestrator.py --gates-only`
- полный проход:
  - `python scripts/release_orchestrator.py --brain-ip <BRAIN_IP> --web-domain <WEB_DOMAIN> --api-domain <API_DOMAIN>`
- verify-only:
  - `python scripts/release_orchestrator.py --brain-ip <BRAIN_IP> --web-domain <WEB_DOMAIN> --api-domain <API_DOMAIN> --verify-only`

### Вариант B: вручную

1. `python -m unittest discover tests`
2. `python -m unittest tests.test_api_auth_and_tickets`
3. `cd webapp && npm.cmd run build`
4. `python scripts/admin_webapp_smoke.py`

## 3. Порядок выкладки

### 3.1 Backend deploy

1. Обновить код `portal_bot/` на brain
2. Выполнить миграции, если они есть в релизе
3. Перезапустить:
   - `systemctl restart portal-api`
   - `systemctl restart portal-bot`
   - `systemctl restart portal-helpbot`

### 3.2 Static deploy

1. Обновить `webapp/out` и `marketing/out`
2. Использовать versioned release-каталоги и атомарное переключение symlink

### 3.3 Metrics timer

1. Если `portal-node-metrics.timer` не активен:
   - `python scripts/remote_install_node_metrics_timer.py --brain-ip <BRAIN_IP>`
2. Проверить:
   - `systemctl is-enabled portal-node-metrics.timer`
   - `systemctl is-active portal-node-metrics.timer`
   - `journalctl -u portal-node-metrics.service -n 50 --no-pager`

## 4. Post-deploy sanity

### 4.1 API / subscription

- `curl -fsS https://<API_DOMAIN>/api/health`
- проверка `/s8Kx2mP7qR4wT/{token}` на тест-пользователе

### 4.2 Checkout / callbacks

- тестовый create order через рабочий flow
- проверка notify/callback idempotency и активации подписки

### 4.3 Admin webapp

- админ видит все `/admin/*`
- не-админ не проходит в admin flow

### 4.4 Metrics

- `GET /api/admin/metrics/status` -> `fresh` при реальной admin-auth
- `GET /api/admin/metrics/timeseries?...` возвращает точки
- server-side sanity дополнительно проверяем через production `DATABASE_URL` и `node_health_samples`

## 5. Rollback-safe точки

1. До backend restart
2. После backend restart, до static update
3. После static update, до metrics timer changes

## 6. Инцидентные шаблоны

### 6.1 Channel bonus revoke не срабатывает

- смотреть логи worker по `channel_bonus_guard`

### 6.2 Ошибка обновления подписки по ключу

- сверить `sub_token` в БД и `subId` в panel
- проверить forced sync в `control_panel.py` / `panel_client.py`

### 6.3 Metrics stale

- проверить `portal-node-metrics.timer`
- проверить journal collector
- проверить `node_health_samples` в production DB

## 7. Мини-чеклист релиз-менеджера

1. Локальные гейты PASS
2. Backend перезапущен без ошибок
3. Static выкладка завершена
4. Checkout + callback + subscription flow зелёные
5. `/api/admin/metrics/status` свежий
6. `node_health_samples` свежие в production DB
7. Результаты sanity и время проверки зафиксированы в `docs/audit-artifacts/`

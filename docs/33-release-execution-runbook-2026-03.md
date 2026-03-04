# Единый релиз 4ebur: Stage 2 Runbook (Execution)

Обновлено: 5 марта 2026

Этот документ закрывает следующий этап: безопасная выкладка с quality gates и rollback-safe точками.

## 1. Предусловия
- Ветка содержит все изменения этапа (critical fixes + admin MVP + metrics + docs).
- Секреты не хранятся в репозитории, только в env/secret manager.
- Доступ к brain по SSH есть у оператора (ручное выполнение).

## 2. Локальные гейты (обязательно)

### Вариант A: одним запуском
- Только quality gates:
  - `python scripts/release_orchestrator.py --gates-only`
- Полный релизный проход (gates -> deploy -> verify):
  - `python scripts/release_orchestrator.py --brain-ip <BRAIN_IP> --web-domain <WEB_DOMAIN> --api-domain <API_DOMAIN>`
- Dry-run (показать все команды без выполнения):
  - `python scripts/release_orchestrator.py --brain-ip <BRAIN_IP> --web-domain <WEB_DOMAIN> --api-domain <API_DOMAIN> --dry-run`
- Verify-only (только пост-релизная проверка):
  - `python scripts/release_orchestrator.py --brain-ip <BRAIN_IP> --web-domain <WEB_DOMAIN> --api-domain <API_DOMAIN> --verify-only`

Ожидаемо:
- Exit code `0`.
- Отчёт: `docs/audit-artifacts/release_gate_report.md`.

### Вариант B: вручную
1. `python -m unittest discover tests`
2. `python -m unittest tests.test_api_auth_and_tickets`
3. `cd webapp && npm.cmd run build`
4. `python scripts/admin_webapp_smoke.py`

## 3. Release-артефакты перед выкладкой
1. Сохранить локальный отчёт gate-check в `docs/audit-artifacts/`.
2. Зафиксировать версии/коммит для backend и webapp.
3. Проверить, что в публичных ссылках бот = `net4ebur_bot`.

## 4. Порядок выкладки (ручной, без remote-exec агента)

### 4.1 Backend deploy
1. Обновить код `portal_bot/` на brain.
2. Выполнить миграции (если применимо по release).
3. Перезапустить:
- `systemctl restart portal-api`
- `systemctl restart portal-bot`
- `systemctl restart portal-helpbot`

### 4.2 Static deploy
1. Обновить `webapp/out` и `marketing/out`.
2. Перезагрузить web-serving слой (например, Caddy), если нужно.

### 4.3 Metrics timer
1. Если `portal-node-metrics.timer` не активен:
- `python scripts/remote_install_node_metrics_timer.py --brain-ip <BRAIN_IP>`
2. Проверить:
- `systemctl is-enabled portal-node-metrics.timer`
- `systemctl is-active portal-node-metrics.timer`
- `journalctl -u portal-node-metrics.service -n 50 --no-pager`

## 5. Post-deploy sanity

### 5.1 API / subscription
- `curl -fsS https://<API_DOMAIN>/api/health`
- Проверка `/s8Kx2mP7qR4wT/{token}` на тест-пользователе.

### 5.2 Checkout / callbacks
- Тестовый create order (RUB) через рабочий flow.
- Проверка notify/callback idempotency и активации подписки.

### 5.3 Admin webapp
- Админ видит все `/admin/*` разделы.
- Не-админ редиректится в `/dashboard/`.

### 5.4 Metrics
- `GET /api/admin/metrics/status` -> `fresh`.
- `GET /api/admin/metrics/timeseries?...` возвращает точки.

## 6. Rollback-safe точки
1. До backend restart.
2. После backend restart, до static update.
3. После static update, до metrics timer changes.

Rollback:
- Возврат на предыдущий backend/static bundle.
- Рестарт сервисов.
- Повторный sanity-check раздела 5.

## 7. Инцидентные шаблоны (кратко)

### 7.1 Симптом: channel bonus revoke не срабатывает
- Смотреть логи worker по `channel_bonus_guard`:
  - `raw_status`
  - `normalized_reason`
  - `action`

### 7.2 Симптом: ошибка обновления подписки по ключу
- Сверить `sub_token` в БД и `subId` в panel.
- Проверить логи forced sync в `control_panel.py`/`panel_client.py`.

### 7.3 Симптом: stale metrics
- Проверить `portal-node-metrics.timer` + service journal.
- Проверить collector и свежесть API.

## 8. Мини-чеклист релиз-менеджера
1. Локальные гейты PASS.
2. Backend перезапущен без ошибок.
3. Static выкладка завершена.
4. Checkout + callback + subscription flow зелёные.
5. `/api/admin/metrics/status` свежий.
6. Результаты sanity и время проверки зафиксированы в `docs/audit-artifacts/`.

## 9. GitHub автоматизация
- Manual запуск оркестратора: `.github/workflows/release-orchestrator-manual.yml` (`workflow_dispatch`, режимы `dry-run` / `verify-only` / `full`).
- Weekly snapshot quick-gate отчёта: `.github/workflows/weekly-release-gate-snapshot.yml`.
- Weekly-отчеты коммитятся в отдельную ветку: `reports/release-gates-weekly`.

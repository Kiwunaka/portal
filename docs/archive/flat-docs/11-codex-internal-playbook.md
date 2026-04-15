# Codex Internal Playbook

Обновлено: `2026-02-16`
Статус: `active`.

Краткая внутренняя карта для быстрых сессий по проекту (без секретов).

## 1) Agent Routing

- `backend-infra`:
  - `portal_bot/`
  - `scripts/`
  - `infra/`
  - root deploy/ops файлы
- `frontend-ui`:
  - `webapp/`
  - `marketing/`
- `docs`:
  - `docs/`
  - `USER_GUIDE_RU.md`
  - `ADMIN_GUIDE.md`
- `payments-integration`:
  - FreeKassa contracts, callback security, env/runbook consistency
  - provider research не выполняется без отдельного запроса owner

## 2) Runtime Map

- Bot: `portal_bot/bot.py` (пользовательские и админ-сценарии).
- API: `portal_bot/api.py` (WebApp данные + checkout/callbacks + subscription endpoint).
- DB: `portal_bot/models.py`, `portal_bot/migrations.py`, `portal_bot/db.py`.
- Multi-node orchestration: `portal_bot/control_panel.py`, `portal_bot/panel_client.py`, `portal_bot/nodes_repo.py`.
- WebApp (user-only): `webapp/src/*`.
- Marketing/checkout: `marketing/src/app/*`.

## 3) Critical Invariants

- Segments:
  - `PAID` = только оплаченный доступ.
  - `FREE/TRIAL/BONUS` = freemium-сегмент.
- Admin source of truth: основной бот, не WebApp.
- Panel policies:
  - free nodes с лимитами;
  - paid nodes без free-route смешивания.
- Subscription links:
  - основной ключ — `sub_token`;
  - numeric `tg_id` допустим только как legacy fallback.
- Backward compatibility:
  - если `nodes` пусты, допустим legacy single-node fallback.

## 4) High-Risk Areas Before Edits

- `portal_bot/bot.py`: большой файл, много callback-веток.
- `portal_bot/control_panel.py`: критичен для sync по нодам.
- `portal_bot/api.py`: checkout/callback/security, user segment logic.
- `scripts/remote_*`: потенциально деструктивные удаленные операции.

## 5) Ops Command Shortlist

- API smoke: `python -m pytest tests/test_portal_api.py -q`
- Script manifest: `python scripts/check_script_manifest.py`
- Node list: `python scripts/list_nodes.py --db portal.db`
- Node migration: `python scripts/migrate_to_nodes.py --only-active`

## 6) Session Checklist

Перед правками:
- подтвердить scope;
- проверить инварианты сегментов/нод/checkout.

После правок:
- прогнать релевантные тесты;
- убедиться, что нет секретов в diff;
- для release-задач: `push + deploy` (или явно зафиксировать blocker);
- зафиксировать короткий changelog и результаты smoke.

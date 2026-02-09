# Codex Internal Playbook

Внутренний рабочий файл для быстрых сессий по проекту.
Файл не содержит секретов и нужен как краткая карта для работы ролями.

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
- `payments-research`:
  - только исследование в `docs/`, без код-изменений

## 2) Runtime Map

- Bot: `portal_bot/bot.py` (aiogram, меню, оплаты, админка, массовые sync).
- API: `portal_bot/api.py` (WebApp данные + подписка `/s8Kx2mP7qR4wT/{token}`).
- DB слой: `portal_bot/models.py`, `portal_bot/migrations.py`, `portal_bot/db.py`.
- Multi-node orchestration: `portal_bot/control_panel.py`, `portal_bot/panel_client.py`, `portal_bot/nodes_repo.py`.
- LK frontend: `webapp/src/*` (React + Vite).
- Маркетинг: `marketing/src/app/*` (Next.js + GSAP).

## 3) Critical Invariants

- Panel-side policies are node-based:
  - Free nodes use capped `totalGB` (default `FREE_TOTAL_GB=40`) and `limitIp` (default `FREE_LIMIT_IP=2`).
  - Paid nodes are unlimited traffic and use `limitIp=5` (`PAID_LIMIT_IP` by default).
  - `expiryTime` remains `0`; lifecycle is controlled by the control-plane DB.
- Планы в DB нормализуются к:
  - `FREE`
  - `PAID`
  - `MANUAL`
- Free-путь:
  - при наличии `pl_free` использовать его (обычно `:8443`);
  - fallback на `pl`, если `pl_free` отсутствует.
- Paid-путь:
  - не использовать free-ноды для paid-пользователей.
- Ссылка подписки:
  - строится через `sub_token` (fallback на `tg_id` только как legacy-совместимость).
- Backward compatibility:
  - если таблица `nodes` пуста, использовать legacy single-node fallback из env.

## 4) High-Risk Areas Before Edits

- `portal_bot/bot.py`:
  - очень большой файл, много legacy callback-веток.
- `portal_bot/control_panel.py`:
  - единая точка нормализации клиентов на нодах.
- `portal_bot/api.py`:
  - формирование free/paid подписки и выдача стран.
- `scripts/remote_*`:
  - удаленные операции, потенциально деструктивные.

## 5) Ops Command Shortlist

- Локальный smoke:
  - `python -m pytest tests/test_portal_api.py -q`
- Валидация скриптового манифеста:
  - `python scripts/check_script_manifest.py`
- Проверка нод:
  - `python scripts/list_nodes.py --db portal.db`
- Sync пользователей на ноды:
  - `python scripts/migrate_to_nodes.py --only-active`
- Настройка free inbound:
  - `python scripts/remote_setup_pl_free_8443.py ...`

## 6) Known Gaps / Tech Debt

- Есть legacy-скрипты и старые артефакты (`legacy/`), не все релевантны текущему прод-потоку.
- Старые entrypoint'ы вынесены в архив `legacy/archive-202602/`; актуальные команды фиксируются в `scripts/manifest.yaml`.
- Есть документы в разных кодировках/стилях, иногда встречается битая кириллица в терминале.
- Тесты покрывают в основном API-часть, мало покрытия для bot/control_panel сценариев.
- В рабочей директории есть чувствительные файлы доступа (ключи, пароли): не трогать и не выводить их содержимое.

## 7) Session Checklist

- Перед правками:
  - подтвердить scope (backend/frontend/docs).
  - проверить затронутые инварианты (free/paid, per-node `totalGB` policy, `expiryTime=0`).
- После правок:
  - прогнать релевантные тесты/скрипты.
  - проверить, что не добавлены секреты в diff.
  - зафиксировать короткий changelog в ответе.

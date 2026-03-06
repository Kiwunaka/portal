# Smoke Checklist PORTAL

Обновлено: 7 марта 2026

## Backend

- `pytest` subset:
  - `tests/test_api_payments_callbacks.py`
  - `tests/test_api_auth_and_tickets.py`
  - `tests/test_bot_paywall.py`
  - `tests/test_worker_retention.py`
- Проверить `/s8Kx2mP7qR4wT/{token}`:
  - новый `sub_token` работает
  - numeric fallback работает только при `SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED=true`
- Проверить `claim_channel_bonus`
  - `member` -> success
  - `left` -> 400 / not_member
  - `sync_ok` возвращается явно
- Проверить FreeKassa callback:
  - valid callback -> activation
  - invalid callback -> 400
  - invalid -> valid same `external_id` -> valid проходит

## Marketing / WebApp

- `python scripts/check-links.py`
- `python scripts/ui_visual_smoke.py`
- `npm.cmd run build` в `marketing/`
- `npm.cmd run build` в `webapp/`
- Primary CTA marketing -> Telegram bot
- `support/legal` в webapp -> absolute legal pages marketing
- Public `/checkout` без ticket показывает понятный fallback
- Home marketing:
  - primary CTA показывает `Подключиться в Telegram`
  - secondary CTA показывает `Посмотреть планы`
- `offer`/`privacy` не ведут в ticket-only checkout без персональной ссылки
- `checkout`:
  - заголовок не склеивается в `PORTALcheckout`
  - без `checkout_ticket` показывает управляемый Telegram fallback
- Support ticket upload:
  - создание обращения с бинарным вложением (`image/video/pdf/txt`) проходит успешно
  - ответ в треде с бинарным вложением проходит успешно
  - вложение открывается из истории переписки

## Admin

- `python scripts/admin_webapp_smoke.py`
- Неадмин видит понятный `403`
- Истёкшая сессия даёт состояние `session expired`

## Ops

- deploy script копирует `collect_node_metrics.py` в `/root/portal_bot/collect_node_metrics.py`
- static deploy публикует `marketing` и `webapp` через versioned releases и атомарное переключение symlink
- `portal-node-metrics.timer` активен
- `/api/admin/metrics/status` показывает свежий collector status
- post-deploy verify проверяет не только `200`, но и ключевые UI-маркеры:
  - home marketing -> `Подключиться в Telegram`
  - home marketing -> `Посмотреть планы`
  - offer -> `Продолжить в Telegram`
  - checkout -> `Продолжение через Telegram`
# P2 additions

- `/api/admin/summary` now returns an `errors` block with stale metrics, unhealthy nodes, payment callback failures, and numeric subscription fallback counts.
- `admin/*` no longer relies on browser `prompt/alert/confirm`; critical admin actions use in-app dialogs and forms.
- `/support` supports binary attachments for screenshots, videos, PDFs, and text files without an external link workaround.
- `/support/thread` renders uploaded attachments and allows binary file replies in the same flow.

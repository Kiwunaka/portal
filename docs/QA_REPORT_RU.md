# QA Report PORTAL

Обновлено: 6 марта 2026

## Статус релиз-гейта

- Backend targeted regression: `PASS`
- Link check: `PASS`
- Marketing build: `PASS` (`/` 96.3 kB first load, `/checkout` 92.1 kB)
- WebApp build: `PASS` (23 static routes, включая `/admin/*`)
- Admin smoke: `PASS`

## Что проверено

| Сценарий | Результат | Комментарий |
| --- | --- | --- |
| FreeKassa callback idempotency | PASS | invalid callback больше не блокирует valid callback |
| Subscription endpoint fallback | PASS | numeric fallback управляется env-флагом |
| Channel bonus membership normalize | PASS | `left/kicked` стабильно трактуются как `not_member` |
| Channel bonus panel sync | PASS | API возвращает `sync_ok` после claim |
| Marketing CTA | PASS | cold flow переведён в bot-first |
| WebApp legal links | PASS | ссылки больше не ведут в несуществующие маршруты webapp |
| Admin unauthorized/session states | PASS | явные состояния вместо silent redirect |
| Support binary attachments | PASS | upload endpoint сохраняет файл, а webapp создаёт и отображает вложение без внешней ссылки |

## Остаточные риски

- Нужна отдельная волна для parity реферальных points в FreeKassa vs Stars.
- Нужна ещё одна UI-итерация для metrics/error-summary внутри `/admin`.
- Upload storage сейчас отдаётся по случайному публичному URL; для более строгой приватности можно позже перевести это на signed URL или auth-gated file proxy.
# P2 follow-up (2026-03-06)

- PASS: `/api/admin/summary` includes an `errors` block for stale metrics, unhealthy nodes, callback failures, and numeric subscription fallback counts.
- PASS: `admin/users` replaces browser prompts with in-app action dialogs for message, extend, manual create, bulk confirm, and token preview.
- PASS: `/support` and `/support/thread` now upload and render binary attachments (`image/video/pdf/txt`) directly through `/api/tickets/uploads`.
- Remaining UI debt in `admin/*` prompt/confirm flows is closed for this wave.
- Generated artifacts from `webapp/test-results/` are now explicitly ignored at repo level and do not belong in release commits.

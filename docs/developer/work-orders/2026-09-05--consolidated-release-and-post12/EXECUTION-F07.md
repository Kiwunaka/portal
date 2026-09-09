# R12-F07 — возврат в приложение и обновление аккаунта

2026-09-06. **I3 / PARTIALLY_FIXED**, полный F07 открыт.
Client `c579708`, Core `8dc57a8`. [Receipt и hashes](evidence/f07-return.json).

Исправлены два воспроизведённых дефекта:

1. После возвращения из кабинета подписка оставалась прежней до повторного
   открытия Profile. Android/Windows widget-сценарии на исходном shell
   `3d21244` ожидали третий subscription request, получали только два. Теперь
   foreground готовой сессии обновляет серверную подписку, сохраняя вкладку
   профиля и не создавая повторный handoff. Только ответ сервера меняет
   отображение expired → paid; сам browser return не подтверждает оплату.
2. Resume на welcome читал inbox до выбора доступа. Его существующий
   `_requestClientJsonWithSession` может вызвать `_startTrial` при отсутствии
   сессии. Тест зафиксировал один преждевременный вызов. После guard на welcome
   нет ни subscription, ни inbox reads; выбор trial по-прежнему запускает поток.

Initial/profile/обычный foreground refresh используют одну in-flight future.
Подписка, бонусы и inbox читаются последовательно; смена вкладки во время
обновления не создаёт второй запрос. Existing Telegram verification branch
сохранён. Ошибка API оставляет прежние данные, освобождает refresh и позволяет
повторить его через foreground/Profile. Новый retry/auth contract не вводился.

**PASS:** 192 widget/coordinator tests, включая два browser-return сценария,
повторные resume + Profile во время запроса, offline/recovery, welcome guard
и существующие acquisition/restore/permission/runtime-resume regressions.
`flutter analyze` — no issues. Client seed/docs и scoped diff — PASS;
performance collector использует fixture.

Точные команды, red/green logs, hashes исходного и изменённого source находятся
в receipt. Ранние невалидные fixture attempts сохранены отдельно: Windows
viewport и Android tap до завершения scroll. Исправленный тест повторно
запускался на точном исходном shell; оба host-контекста подтвердили missing
subscription refresh. Подготовленная правка затем восстановлена побайтно.

Канон обновлён в `E:/r12client/docs/architecture/app-first-onboarding-flow.md`.
Полный отчёт: `E:/r12client/docs/operations/evidence/2026-09-06-r12-f07-return/README.md`.
Архив: `E:/r12-f07-return/f07-evidence.zip`, 17 файлов, 192799 bytes;
все entries сверены. Четыре прежних generated registrants сохранены.

Это synthetic checks на Windows host с Android/Windows app context.
Installed 1.1.6 upgrade/session continuity, реальные native browser/deep-link/
tray события, account/order context, D01/W03 packages и provider return
остаются OPEN. APK/EXE для этого Dart изменения не собирались; предыдущие
D06/C05 artifacts не доказывают новое поведение. Нет production signing,
installation, VPN, payment, push, merge, deploy, публикации или нового candidate.
Rollback — scoped source commit; прежние artifacts/evidence остаются на месте.

Platform handoff: docs/context pytest **33 PASS**;
`agent_context_packet_audit.py --platform-context-root .` **PASS**;
`validate_package.py` **PASS** — 13 import hashes, 83 R12 IDs,
378 legacy IDs, 239 local links; `git diff --check` **PASS**.
Fresh SHA-256 readback подтверждает пять client Git blobs и evidence archive.

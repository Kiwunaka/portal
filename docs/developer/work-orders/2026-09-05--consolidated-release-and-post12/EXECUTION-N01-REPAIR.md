# N01/N04 — repair profile fencing, 2026-09-06

**PARTIAL / I3.** Client commit `f024861`.
Продолжение [N01 identity/lineage и profile lifecycle](EXECUTION-CONTINUED.md).
[Команды, SHA логов и точные ограничения](evidence/n01-repair-fencing.json).

Кнопка восстановления обходила две защиты обычного connect:

1. Stage выполнялся до завершения pending Quick Settings invalidation.
   Поздний clear мог удалить только что подготовленный профиль. Регрессия:
   обычный connect PASS, repair FAIL по фактической последовательности host calls.
2. Пользователь мог закрыть repair sheet и сменить режим, пока stage старого
   профиля ожидал host. После позднего ACK repair вызывал connect старого профиля.
   Новый fixture выполняет именно этот UI путь; до фикса unwanted connect FAIL.

Repair теперь ждёт существующую bounded очередь invalidation. При её таймауте
нет stage/connect даже после позднего ответа. После ожидания захватывается
локальная revision настроек; после stage ACK она проверяется снова. При смене
настроек профиль остаётся dirty, connect не вызывается, показана просьба
повторить подключение с новыми настройками. Host digest и server revision
сохраняют собственные границы; локальный счётчик не выдаётся за server revision.

Четыре focused cases PASS: connect, repair, смена режима во время stage,
таймаут с поздним host completion. Полный widget/lifecycle — 178 PASS;
analyze, validate-seed, final docs-contract и diff-check — PASS.
Основной код: 28 строк в repair; расширен существующий integration fixture.
Новых owner abstractions, part или runtime dependencies нет.

Physical-device/native concurrency и exact-package VM proof остаются OPEN.
Полный N01/N04 и durable rollback N02 не закрыты. Предыдущие digest/lineage
receipts сохранены. Core/AAR/DLL и release artifacts не изменялись.
Push/merge/deploy/candidate/signing/publication: NOT_PERFORMED.
Rollback — scoped revert `f024861`; серверного изменения нет.

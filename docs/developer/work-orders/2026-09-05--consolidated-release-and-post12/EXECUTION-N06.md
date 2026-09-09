# R12-N06 — ограничение незавершённых probes, 2026-09-06

Статус: **PARTIAL / I3**. Это дополнительное исправление существующего
Smart Connect (client commit `152afc5`); полный N06 и его зависимость N02 не объявлены закрытыми.

При concurrency=3, восьми локациях и коротком timeout старый worker запускал
восемь незавершённых Futures. `Future.timeout` завершает ожидание, но не исходную
операцию. Поэтому число workers не ограничивало число активных probes.

Теперь один счётчик bootstrapper учитывает незавершённые probes и сохраняет
занятые слоты после timeout, в том числе между запросами профиля. Завершение
исходного Future освобождает слот; поздний RTT не переносится в новую выборку.
При занятых слотах advisory probes пропускаются. Собственный timeout штатного
Socket.connect сохранён. Это ограничение одного bootstrapper; оно не является
глобальным лимитом probes всех процессов или Core egress проверок.

Регрессия расширяет существующий loopback API тест. До изменения: FAIL,
8 вместо 3. После: PASS; повторный resolve не запускает новые probes поверх
зависших; после их завершения probes возобновляются. Существующий integration
тест quarantine/failover также PASS. Полный bootstrap — 86 PASS; analyze и validate-seed — PASS.
Точные команды и SHA логов — [evidence/n06-probe-slots.json](evidence/n06-probe-slots.json).

Ранее реализованные два автоматических retry, backoff 250/500 мс + jitter
0–250 мс, negative TTL 15 минут и максимум восемь quarantine entries сохранены.
Полный last-good/rollback contract, проверка всей физической network matrix и
общий runtime probe budget требуют оставшегося N02/N06 evidence. Новый ATS,
Broker, смена transport authority или unsafe direct fallback не добавлялись.

AAR/DLL остаются точными N05 bytes; Dart изменение не переименовывает их и
не требует сборки Core. Новые APK/installer и device/VM receipts не создавались.
Push, merge, deploy и публикации: NOT_PERFORMED. Rollback — scoped revert
этого source commit; retained candidate.33 и прежние evidence сохранены.

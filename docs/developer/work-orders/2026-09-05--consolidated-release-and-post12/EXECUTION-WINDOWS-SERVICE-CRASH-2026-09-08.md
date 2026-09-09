# W02 — падение службы и исправление статуса Windows UI

**PASS_BOUNDED**, current-origin Win11 VM, client `68a44e5`, Core `02a091c`.
[Receipt](evidence/windows-service-crash-2026-09-08.json) привязан к коммиту
клиентского evidence `544d003` и его Git blob. Полный W02 остаётся открыт.

На прежнем пакете принудительное завершение точного PID POKROVService удаляло
TUN, SCM восстанавливал службу, а UI продолжал показывать «Подключено».
Сохранены воспроизведение в VM и падавший widget test. Исправление наблюдает
локальный IPC каждые две секунды, не запрашивая profile/API и сетевую диагностику.
Запросы не накладываются; старый ответ не отменяет результат ручного disconnect.

Новый unsigned installer `3e23609d…80352` установлен обычным wizard/UAC.
305 hashes, сохранённое состояние, Auto/LocalSystem и обычный owner IPC PASS;
reboot не потребовался. Из пакета изменился только `data/app.so`, поэтому
совпадение runner EXE отдельно не доказывает новую реализацию Dart.

После обычного AWG31 connect повторно завершён PID службы. Первый sample
нового running PID с журналом `clean` — **15 588 мс**. UI process остался тем же,
снял «Подключено» и показал «Повторить». Обычный retry восстановил running TUN,
Core/DNS/egress readiness и staged/effective identity. Routes/DNS совпали с
исходными и после crash, и после финального disconnect; 305 hashes сохранились.

Shell 188, connection 14, Windows Flutter 24 tests PASS; analyze без замечаний,
seed с явными platform/Core roots, build, local packaging и retained hash audit
PASS. Два ранних запуска ссылались на несуществующие тестовые файлы и дали FAIL;
их логи сохранены рядом с исправленными passing commands. Клиентский отчёт
содержит команды и 42 локальных artifact references. `git diff --check` PASS.

Исходная backend-конфигурация полностью восстановлена, entitlement/material не
менялись. VM выключена, NIC none; исходная VM off. Host routes/DNS прежние.
Shutdown wrapper вернул exit 1 при исчезновении guest; отдельный VBox readback
подтвердил poweroff. Snapshot, прежний пакет и отрицательные evidence сохранены.

Снимки UI не измеряют точную задержку сброса статуса; tray-hidden crash отдельно
не проверялся. Внешний IP был одинаков через host/proxy topology: независимый
route proof открыт, DE SSH trust не обходился. Sleep, handoff, Win10, WFP/IPv6,
отдельная Core-panic injection, saved location/access presentation и final-channel
матрица остаются открытыми. Push, merge, tag, signing, candidate, deploy и
публикация не выполнялись.

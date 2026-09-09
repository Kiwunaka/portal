# A03 — новый Core в установленном Windows-пакете

**PASS_BOUNDED**, client `295ceac`, Core `02a091c`, current-origin Win11 VM.
[Receipt](evidence/windows-awg-crossfield-2026-09-08.json) связывает клиентский
отчёт с точными исходниками и хешами 42 локальных артефактов. Это продолжение
[A03 correction](EXECUTION-A03-CROSSFIELD-2026-09-08.md); предыдущий срез ещё
не содержал установленного Windows-пакета с новыми библиотеками.

Новый unsigned installer `ef4bc953…70cfa` обновил существующий lab. Все 305
файлов совпали с пакетом; DLL `0409da47…d0371`, сохранённое состояние клиента
не изменилось. Установка не потребовала reboot. Служба Auto/LocalSystem,
IPC под ограниченным токеном владельца PASS. Отдельный standard-account run
старого пакета не переносится на новые bytes.

Три обычных подключения AWG3.1 → AWG2 → AWG3.1 дали running/Core/DNS/egress
readiness и совпадение staged/effective identity, один TUN, health 200 и DNS.
Хеш защищённого профиля сменился и вернулся к исходному. AWG2 подтверждается
guarded server assignment и формой endpoint; его renderer не пишет contract_id.
Read-only sampler экспортировал только хеши и имена полей.

Все три отключения удалили TUN и восстановили исходные routes/DNS. Финальные
305 хешей пакета совпали. Полная исходная rollout-конфигурация восстановлена;
material и entitlement не менялись. Sampler остановлен, VM выключена/NIC none,
исходная VM выключена. Сеть пользовательского host совпала с pre-test baseline.

Windows Flutter 24 tests, analyze, release build и local packaging PASS.
Команды: `build.ps1`, `package.ps1`, обычный installer/UI, `lab-control.py switch`,
`network.ps1`, `read-profile.ps1`, `final-identity.ps1`, `lab-control.py restore`
и итоговый `retain-evidence.py`. Полные команды и результаты сохранены в
`E:/r12-windows-awg-crossfield-20260908`; скрипты packager используют отдельный
локальный output root. Retained release artifacts не изменялись.

Итоговый client seed с явными platform/Core roots PASS; 33 platform docs tests,
context audit и package validator (83 R12 IDs, 303 links) PASS. Хеши четырёх
логов проверок сохранены в клиентском receipt. `git diff --check` PASS.

Независимый route proof открыт: внешний IP одинаков с TUN и без него. Ранее
неподтверждённая смена SSH-ключа DE остаётся открытой; обхода доверия и чтения
server counters не было. UI сохраняет Milan и уточняемый статус доступа при
фиксированном DE lab transport. Полные location/MTU, Android с новым Core,
Win10, crash/sleep, WFP/IPv6 и final-channel критерии не закрыты.
Push, merge, tag, signing, новый candidate, публикация и deploy не выполнялись.

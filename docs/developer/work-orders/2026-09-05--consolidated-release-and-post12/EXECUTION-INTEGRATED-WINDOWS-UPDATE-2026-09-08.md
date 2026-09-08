# Интегрированный Windows — обновление при подключённом VPN

**PASS_BOUNDED_CONNECTED_UPDATE**, текущий setup `83c253ce…6063`, client
`3784352` / Core `02a091c`. [Receipt с точными SHA и командами](evidence/integrated-windows-update-20260908.json).
Полные файлы evidence принадлежат client:
`docs/operations/evidence/2026-09-08-r12-integrated-windows-update/`.
Client evidence сохранён коммитом `b525547`; packaged source остаётся `3784352`.

В отдельной Win11 Evaluation VM установлен сохранённый предыдущий пакет
`e88dff9`, затем выполнено обновление текущим установщиком при работающем
UI/service/TUN. Установщик сам закрыл POKROV через Restart Manager и завершился
с первого раза. Все 305 файлов до и после совпали с соответствующими пакетами.
Перед повторным запуском сохранённые session/experience bytes совпали с
непосредственным preinstall snapshot; routes/DNS вернулись к baseline,
перезагрузка не потребовалась. Новый UI подключился и отключился; финальные
файлы, session и routes/DNS повторно проверены. Оба пакета имеют версию
`1.2.0+4053`; это не version-number migration или final-channel acceptance.

За прогон нет новых Defender 1116/1117 при включённой защите. Прежний AV-дефект
не закрыт этим результатом. Внешний egress hash остался равен baseline, поэтому
это evidence активного TUN и доступности HTTPS 200, не новый independent
egress/leak или protocol-specific PASS.

При cleanup entitlement selector отказал в восстановлении: прежняя тестовая
identity перестала удовлетворять проверке владения доступом. Отказ сохранён.
Точный configuration-only rollback проверил hash после enable, восстановленный
исходный hash и отсутствие concurrent changes, затем прошёл обычный admin
action-intent guard. Полный исходный config восстановлен; entitlement/material
не менялись. Этот случай не закрывает expiry/revocation acceptance. UI показывал
неуточнённый статус доступа до и после обновления.

VM штатно выключена, NIC none; исходная VM off, host routes/DNS неизменны.
W02 sleep недоступен по `powercfg /a`. Win10, полный standard-user
install/uninstall/reinstall scope W03 на этих bytes, текущая migration/deployed
приёмка, real providers и выпуск остаются открытыми. Push/deploy не выполнены.

Проверки: `python -B -m pytest -p no:cacheprovider
tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
— 33 PASS; `python -B scripts/agent_context_packet_audit.py
--platform-context-root .` — PASS; work-order `validate_package.py` — 83 ID,
378 legacy references и 341 local links PASS. Client `validate-seed.ps1` и
`test/docs-contract.ps1` PASS; 28 retained hashes/sizes и JSON readback PASS.
`git diff --check` PASS в обоих worktrees; `artifacts/releases/**` без изменений.

# Windows — изоляция отказа NAT

**PASS_BOUNDED_TRANSPORT_PATH_ISOLATION**, current-origin owned Win11 VM,
client `c05b58b268bbd789aa96fb662cb46c9768558ef0`, Core
`c7a11f7d2fd974726095ad7aa0619c055273dd15`. Все 304 установленных файла повторно
совпали. Canonical client evidence:
`docs/operations/evidence/2026-09-09-r12-windows-nat-path/README.md` и
`receipt.json`; 23 safe captures и hashes 16 локальных инструментов.

Продолжение [предыдущего отказа](EXECUTION-WINDOWS-EGRESS-2026-09-09.md).
Владелец выполнил защищённое чтение журнала. Оно показало запуск Core и
штатную остановку после отказа egress, без подробной транспортной ошибки.
Дальнейшая проба использовала существующий DPAPI-кэш owned пользователя в его
обычном контексте: профиль оставался в памяти, ACL и сохранённые bytes не
менялись. Повторное повышение прав не выполнялось.

Точная ошибка — `reality verification failed`. Проверки сопоставили UUID,
ключ, short ID, SNI, адрес и порт с действующим Xray. Замена fingerprint на
Chrome, второй прямой вариант Франкфурта, минимальные TLS-параметры и явный
IPv4 не устранили отказ NAT. Linux Core и Xray 26.6.1 прошли отдельные
owned-de-loopback controls; Xray получил HTTP 204 от owned API.

Windows-проба прошла через временный SSH к тому же Xray, затем через мост VM
к физическому Ethernet. После Windows Update выполнен повтор в одном boot:
NAT снова отказал за 164 мс, мост прошёл за 252 мс. В обоих прогонах profile
SHA-256 `716567a5451a9993a6f5e44d6c24a86a9966aae0c4f1a3979a09ab7b794299d2`.
Это изолирует сбой до NAT-пути через хост. На хосте активны Hiddify и `tun0`,
но конкретный механизм перенаправления/отказа не установлен. Их настройки и
server config не менялись; самостоятельная правка Core этим сбоем не обоснована.

Standalone URLTest проверяет соединение и получение HTTPS-ответа, но не его
status/marker. Это не положительный installed-service TUN/DNS/egress proof.
После обновления Windows остановилась на экране входа; служба Running и
`artifact_ready`, без staged/running Core. UI-проверка ждёт входа владельца.
Computer Use не разрешает автоматизировать этот Windows authentication UI.

VM остаётся включённой, bridge настроен, cable **off** на время ожидания.
После входа владельца включить link, выполнить полный connect/route/egress
и disconnect, затем вернуть исходный powered-off/NIC-none baseline.
Временные Xray/SSH процессы остановлены, Linux probe удалён, локальные
инструменты сохранены в `E:/r12-win-egress-20260909`. Product/release bytes
не менялись. N01/N02/N03/W01/W03 и общий релиз остаются active.

Проверки пакета evidence: client `validate-seed.ps1` с явными platform/Core
roots PASS; `python -B -m pytest -p no:cacheprovider
tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
— 33 PASS; `python -B scripts/agent_context_packet_audit.py
--platform-context-root .` — PASS; work-order `validate_package.py` — 83 R12 ID
и 477 local links PASS. Capture hashes/JSON и A/B assertions PASS.
`git diff --check` PASS в обоих worktrees, release artifacts без изменений.

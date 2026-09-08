# N03/N08 — Windows AWG и независимые счётчики маршрута

**PASS_BOUNDED** для установленного client `3784352` / Core `02a091c`, Win11,
owned VM с NAT, managed AWG3.1, current-origin. Все 305 installed files совпали
после установки и перед выключением. [Receipt](evidence/windows-route-proof-2026-09-08.json)
связывает client evidence commit `5188505`, семь замеров и 62 локальных артефакта.
Полные N03/N08, effective location и final channel остаются открытыми.

На прежнем `e88dff9` подключение после выбора PowerShell в штатном picker
падало до запуска runtime: `connect_unexpected_managed_profile_refresh`.
В selected mode `route.final=direct`, AWG указан в process rule; обработчик
находил AWG endpoint только через final. Regression воспроизвёл FormatException.
Исправление `3784352` учитывает endpoint, на который ссылается существующее
правило, сохраняя direct final и выбор процесса. Canonical bootstrap owner
обновлён в том же implementation commit; 119 Flutter tests и analyze прошли.

Pktmon считал только IPv4 TCP80 к собственному brain, NIC components,
`--counters-only`. Пакеты, ETL и pcap не сохранялись. Каждый замер: три запроса
от обычного пользователя, три HTTP 200.

| Source / режим / процесс | TUN Rx/Tx | Ethernet Rx/Tx |
| --- | --- | --- |
| e88dff9 / отключён / curl | нет | 15/15 |
| e88dff9 / Россия напрямую / curl | 15/15 | 0/0 |
| e88dff9 / всё устройство / curl | 15/15 | 0/0 |
| 3784352 / выбран PowerShell / PowerShell | 15/15 | 0/0 |
| 3784352 / выбран PowerShell / curl | 15/15 | 15/15 |
| 3784352 / всё устройство / curl | 15/15 | 0/0 |
| 3784352 / Россия напрямую / curl | 15/15 | 0/0 |

У selected/unselected пары одинаковый active profile hash, direct final и
правило powershell.exe → AWG3.1. Прямой выход curl соответствует выбранному
режиму. Все connected samples имеют Core/DNS/egress/effective-stage proof.
Это один адрес вне РФ; российские сервисы, банки, DNS, IPv6, LAN, все протоколы
и фактическая география выхода этим замером не доказаны. Excluded-app UI есть
на Android; в Windows проверяются три предоставленных пользователю режима.

Первый автоматический запуск установщика вернул exit 0, но установка не
завершилась: 304/305 совпадений, прежний `data/app.so`, оборванный install log.
Defender записал `Behavior:Win32/SuspClickFix.G2` и Remove. Это FAIL, несмотря
на локальную метку `PASS_INSTALL_EXIT`. Тот же installer установлен обычным
интерактивным wizard: 305/305, сохранённые session/experience не изменились.
Защита оставалась включённой, исключения не добавлялись. Финальные семь AV
events совпадают с исходными; новых нет. Автоматическая установка/AV остаётся
открытой проблемой и не получает общий PASS.

После disconnect исходные routes/DNS/preferences и пустой selected list
восстановлены. UI остановлен, Auto LocalSystem service установлен, Pktmon idle
без filters, временных capture/inspect/click tasks нет. Backend restore
совпал с полным исходным config hash. VM off/NIC none, source VM off,
host routes/DNS неизменны. Secrets и raw profiles не экспортировались.
Нет push, publication, promotion, deploy или `artifacts/releases/**` delta.

Client `scripts/validate-seed.ps1 -PlatformRoot C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start -CoreRoot E:/r12core-implementation`
PASS, включая docs contract. Host `python -B E:/r12-windows-route-proof-20260908/retain-evidence.py`
PASS: семь samples, 62 artifact hashes и cleanup; `finish.ps1` PASS.
`git diff --check` PASS. Доказательства другого source ниже по истории не
переносятся автоматически на новые байты.

Platform: `python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
— 33 PASS. `python -B scripts/agent_context_packet_audit.py --platform-context-root .`
— PASS. Work-order `validate_package.py` — PASS: 13 imports, 83 R12,
378 legacy IDs, 318 local links. Финальный `git diff --check` — PASS.

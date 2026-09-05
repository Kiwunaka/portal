# R12-N08 — routing truth, локальный срез 2026-09-06

**PARTIAL / I3 / NEEDS_RUNTIME_PROOF.** Client commit `2080cee`.
N02/N03, exact packages и физическая/VM матрица остаются открытыми.
Точные команды, SHA логов и JVM receipts — [evidence/n08-routing.json](evidence/n08-routing.json).

## Исправления

1. VPN selector/urltest больше не содержит `direct` в Android/Windows во всех
   четырёх режимах. Прежняя очистка применялась только к Android Full/Except
   selected. До исправления матрица дала 2 PASS / 6 FAIL; после — 8 PASS.
   Четыре дополнительных Windows runtime-ready cases проверяют именно цепочки,
   а не все свойства уже материализованного профиля.
2. Windows selected/excluded требует хотя бы одного допустимого процесса после
   нормализации. Строка, целиком отброшенная фильтром process names, не позволяет
   перейти к bootstrap/API/native stage. Регрессия сохранена до и после фикса.

Явные direct route/DNS rules, LAN preference и OS package exclusions являются
отдельными решениями. Они не удаляются вместе с unsafe selector fallback.

## Матрица исходников и локальных проверок

| Платформа / режим | Механизм выбора | Базовый маршрут / DNS | Локальная проверка | Device / VM |
| --- | --- | --- | --- | --- |
| Android Full | весь TUN, собственный VPN package исключён | proxy; remote DNS, отдельный bootstrap DNS | bootstrap full-route/DNS + selector + package planner PASS | OPEN |
| Android All except RU | TUN + RU rulesets/suffixes | RU direct, остальное proxy; RU DNS отдельно | RU rulesets/fallback + selector PASS | OPEN |
| Android Selected | VpnService include_package | вошедшие в TUN приложения: proxy; DNS внутри TUN | selected packages + empty fail-closed + selector PASS | OPEN |
| Android Except selected | VpnService exclude_package | выбранные вне TUN; остальные proxy | excluded packages + selector PASS | OPEN |
| Windows Full | system TUN | proxy; remote DNS, bootstrap/private exceptions отдельно | generated route/DNS source + selector PASS | OPEN |
| Windows All except RU | system TUN + RU rulesets/suffixes | RU direct, остальное proxy | local rulesets + selector PASS | OPEN |
| Windows Selected | process_name rules | выбранные proxy/remote DNS; final direct/direct DNS | generated process/DNS opposite rules + normalized empty guard PASS | OPEN |
| Windows Except selected | process_name rules | выбранные direct/direct DNS; final proxy/remote DNS | generated opposite process/DNS rules + selector PASS | OPEN |

Таблица описывает базовую политику. Пользовательские overrides/purpose rules
сохраняют предусмотренный приоритет. Банковские домены не имеют единого
автоматического direct-исключения во всех режимах: RU rules относятся к
All except RU, либо человек явно включает purpose `ruDirect`. По умолчанию
набор purposeRoutes пуст. LAN direct по умолчанию включён и может быть выключен.

DNS/LAN оцениваются после всех transform: Windows preferences ставит port 53
hijack и sniff перед bypass; Android runtime возвращает protocol DNS hijack
перед LAN после application preferences. Это проверено runtime tests, а не
предположено по промежуточному JSON. Android IPv4-only не добавляет IPv6 route;
отдельные host planner cases покрывают IPv6-only, dual-stack и отсутствие auto-route.
Эти fixtures не доказывают отсутствие IPv6/DNS leaks на устройстве.

PASS: bootstrap/routing preferences 116; runtime 80 + один прежний opt-in skip;
focused Android package/route/DNS planners обоих flavors; analyze; validate-seed.
Полная семантика Windows runtime-ready route-mode/DNS остаётся отдельным
непроверенным участком: данный фикс там доказывает только VPN chain очистку.

AAR/DLL остаются N05 bytes, candidate.33 и исторические receipts сохранены.
Push, merge, deploy, новый candidate, signing и публикация: NOT_PERFORMED.
Rollback: scoped revert client commit; новая цепочка не меняет серверные ключи,
системные настройки host или старые release artifacts.

## Продолжение: готовые Windows-профили

Client commit `5606fdc`. Статус всего N08 остаётся **PARTIAL / I3 /
NEEDS_RUNTIME_PROOF**. Этот срез закрывает ранее указанный пробел в локальных
route-mode/DNS fixtures; device/VM proof остаётся OPEN.

Готовый профиль обходил построители mode/process/DNS правил. Четыре режима
падали на новых assertions до исправления. Теперь этот путь применяет общие
Windows rules: текущий process selection, противоположные selected/excluded
маршруты и DNS, Full/RU bypass semantics и защищённый port-53 prefix. Устаревшие
process routes и DNS server choices заменяются; direct outbound добавляется,
если его не было. Профиль без безопасного VPN-выхода отклоняется до staging.

Исходные inbounds и прочие параметры профиля сохраняются. DNS builder сохраняет
настроенные server type/address/path/TLS и прочие transport options в direct/VPN
ветках, а также non-routing DNS actions. Без network resolver действуют прежние
TCP/UDP defaults. Самоссылка direct-копии resolver обнаружена отдельной регрессией
и заменена local bootstrap с сохранением остальных resolver options.

Проверки после окончательных правок: bootstrap/preferences — 116 PASS;
runtime — 80 PASS / один прежний opt-in skip; analyze и validate-seed — PASS;
`git diff --check` — PASS; delta `artifacts/releases/**` отсутствует.
[Точные команды, SHA логов и ограничения](evidence/n08-ready-routing.json).
Физические Windows DNS/process/TUN и RU-origin проверки не выполнялись.
Core/AAR/DLL не изменялись; push, deploy, candidate и публикация не выполнялись.
Rollback — scoped revert `5606fdc`; серверное состояние не менялось.

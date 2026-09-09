# W06 — firewall и локальное приложение в Win11

**PASS_BOUNDED**, installed local client `e88dff9` / Core `02a091c`, Windows 11
`10.0.26200`, owned VM с NAT, current-origin. Пакет не пересобирался;
305 installed hashes совпали до и после. [Receipt](evidence/windows-coexistence-2026-09-08.json)
связывает клиентские oracle, helper identity и 35 retained file/hash references.
Полный W06 остаётся открытым.

| AWG3.1 | `/health` до блока | С блоком | После снятия | Local HTTP | TUN |
| --- | --- | --- | --- | --- | --- |
| До подключения | 200 | ConnectFailure | 200 | 3 × 200 | 0 |
| Подключён | 200 | ConnectFailure | 200 | 3 × 200 | 1 |
| После отключения | 200 | ConnectFailure | 200 | 3 × 200 | 0 |

Тестовое чужое правило ограничено PowerShell, TCP 443 и IPv4-адресами нашего
`app.pokrov.space`. Каждая проба создаёт новый direct HTTPS request с TLS 1.2
и deadline 8 секунд; ActiveStore подтверждает включение правила.
Локальный HTTP listener работает у обычного пользователя на loopback.
Это проверка доступности локального приложения; enforcement loopback-правила
этими ответами не доказывается.

Все 488 исходных PersistentStore rules и выбранные поля application/address/
port/service/interface/security/profile filters сохранили aggregate/component
hashes во всех трёх фазах и после удаления fixture. Raw firewall policy не
экспортировалась. В connected-фазе служба до и после блока подтверждала
running/Core/DNS/egress readiness и effective/staged agreement. Точный хеш
read-only IPC helper сохранён отдельно: его встроенная метка `0218e89`
не является source identity установленного клиента.

Первая подготовка остановилась до создания правил: Windows Firewall отклонил
Program path с `/`; v2 использует Windows-путь с `\`. Обе попытки сохранены.
После проверки удалены только два именованных fixture rules, listener завершён,
UI остановлен после явного disconnect. Routes/DNS гостя равны исходным хешам,
серверный rollout полностью восстановлен. VM off/NIC none, source VM off,
host routes/DNS прежние. Нового candidate, push, promotion, publication или
deploy не было; `artifacts/releases/**` не менялись.

Открыты: другой VPN, сторонние native WFP providers/sublayers, LAN/IPv6, Win10,
independent route/effective location proof и exact final channel. Один sample
на фазу не является stress-тестом или полной WFP matrix.

Из гостя: `coexist-v2.ps1 -Mode Prepare -Label prepare-v2`,
`-Mode Observe -Label before|connected|after`, `-Mode Cleanup -Label cleanup`
— пять успешных exits. Из host:
`python -B E:/r12-windows-coexistence-20260908/retain-evidence.py` — PASS,
три oracle / 488 rules / 305 files / 35 hashes / return state;
`pwsh -NoProfile -File E:/r12-windows-coexistence-20260908/finish.ps1` — PASS.

Client evidence commit `be97af6`: explicit-root `scripts/validate-seed.ps1`
PASS, включая docs contract. Platform:
`python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
— 33 PASS; `python -B scripts/agent_context_packet_audit.py --platform-context-root .`
— PASS. Work-order `validate_package.py` — PASS: 13 imports, 83 R12, 378 legacy,
315 links. `git diff --check` PASS; release artifacts неизменны. Логи в lab dir.

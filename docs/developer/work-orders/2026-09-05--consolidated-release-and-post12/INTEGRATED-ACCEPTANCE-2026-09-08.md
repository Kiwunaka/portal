# Единый приёмочный комплект — 2026-09-08

Статус: **LOCAL_INPUTS_UPDATED / ACCEPTANCE_OPEN / RELEASE_OPEN**. Это рабочая приёмка до нового
кандидата. Candidate.33 и его история сохранены. Публикация, новый release tag,
promotion и production deploy не выполнены.

[Явный запрет доступа](EXECUTION-INTEGRATED-ACCESS-DENIAL-2026-09-08.md) выявил
дефект в прежнем комплекте. Client `f479fd4` исправлен и принят в Win11 для
отключения/очистки кэша/отказа после offline UI restart. Новый setup SHA-256
`f44486c3ae32ac5c3020e9b76c997902c202084076cb7954bc0678d5805f676d`;
304 ожидаемых installed файла совпали. Android пересобран: новый ARM64
`20a0781baf9bea1e9e0e55de5f4d7d5193936dfe7a9d894df98c1bc457b897af`
установлен на Huawei. Update/connect/resume/disconnect и точное восстановление
routes/rules PASS_BOUNDED; denial/revocation телефона требует отдельного test
login, текущая admin-сессия сохранена. [Новые inputs](evidence/integrated-acceptance-20260908/inputs-access-denial.json)
содержат пять проверенных artifact hashes. Таблица источников ниже сохраняет
исходный комплект; её local preflight не подтверждает исправленный tuple.
Actual session revocation и expiry нового пакета остаются открытыми.

## Исходные закреплённые входы до исправления запрета

[inputs.json](evidence/integrated-acceptance-20260908/inputs.json) содержит полные
SHA исходников и пакетов, native libraries, review переноса и hashes отчётов.
Это evidence inventory, не дополнительный release-handoff contract.

| Компонент | Source / пакет |
| --- | --- |
| Platform | `16407b8`, отдельный чистый checkout `E:/r12-integration-platform-20260908` |
| Client | `7ae931b`, чистый checkout `E:/r12-integration-client-20260908` |
| Core | `02a091c`; привязанные AAR/DLL проверены preflight по локальным bytes |
| Android | Пересобраны universal, ARM64, ARMv7, x86_64; `1.2.0+4053`; один production Android certificate |
| Primary ARM64 | SHA-256 `88452b9921873c4fbb42bef25ed4d89c34841399ae11cbe8d9d482e5a03d5850` |
| Windows | SHA-256 `83c253ce8a1cc5d64aa615e259ae2a0f6d5d978442fd3732965d7778d14d6063`; unsigned local installer |

Windows собран из `3784352`. Между ним и `7ae931b` нет изменений в apps,
packages, config, scripts или pubspec. Переносятся только ограниченные факты
receipt `2026-09-08-r12-windows-route-proof` для этих же bytes. Более ранние
Windows receipts не получают автоматический PASS для комплекта.
Android пересобран из-за изменений общего Dart-кода; прежний установленный
APK `0206cd2a...` не подтверждает новый `88452b99...`.

Общий quality gate выполнен для platform `dae94ff`, того же client и Core.
Единственный последующий platform diff — исправление preflight, его тесты и
публикационный guide; runtime и inputs quality gate не менялись. Исправление
отдельно проверено. Чужие untracked инструкции и generated registrants
в исходных рабочих каталогах сохранены.

## Общая acceptance matrix

Дополнение: [текущий Huawei AWG](EXECUTION-INTEGRATED-ANDROID-AWG-2026-09-08.md)
прошёл AWG3.1 → AWG2 → AWG3.1 и Wi-Fi/mobile/Wi-Fi с server inner traffic.
Exact identity найдена; исходная backend configuration полностью восстановлена.
Финальные routes совпали, VPN/TUN выключены. Два rule hashes отличаются только
новым OS network ID; остальные bytes совпали с baseline.

PASS ниже относится ровно к названному сценарию. Полные родительские R12
критерии и будущий exact-candidate gate остаются открытыми.

| Область / R12 | Результат для комплекта | Что ещё нужно |
| --- | --- | --- |
| G02/G03/G05/G07, источники и artifact binding | PASS: чистый tuple, четыре APK, существующий Windows installer и Core bytes | Final release-handoff и same-byte channel binding |
| G03/Q01, локальная автоматическая проверка | PASS: 15/15 quality steps; preflight `READY_LOCAL_FREEZE`, 0 blockers | Это preflight, не полный go/no-go |
| D01/D04/D06, Android packaging | PASS: подпись, version 4053, ABI, native Core hashes, release flags и notices всех 4 APK | Direct/store authority, downgrade и final-channel acceptance |
| D01/N01/N03, Huawei | PASS_BOUNDED: новый ARM64 установлен; обычные connect/disconnect и AWG3.1→AWG2→AWG3.1 с server inner traffic; routes/rules восстановлены с учётом нового OS network ID | Полный independent egress/leak и parent scope |
| W01/N03/N08, Windows | PASS_BOUNDED: для тех же bytes сохранены 305 installed hashes и независимые NIC-counter routing samples | Остальные протоколы, Win10, IPv6 и полный matrix |
| W02/W03/W04/W06 | [Текущий connected update](EXECUTION-INTEGRATED-WINDOWS-UPDATE-2026-09-08.md) PASS_BOUNDED: 305 hashes, неизменные saved bytes, повторное подключение и routes/DNS cleanup; исторические crash/reboot/tray/coexistence receipts сохранены | Sleep не поддерживается VM; полный W03/current-input scope и Win10 открыты; прежний Defender behavior unresolved |
| N02/N07/A04, outage/expiry/revocation | [Явный запрет](EXECUTION-INTEGRATED-ACCESS-DENIAL-2026-09-08.md): old-package FAIL исправлен; новый Windows `f479fd4` отключает туннель и очищает кэш, offline UI restart не подключается. Новый Android `f479fd4` установлен; положительный connect/resume PASS. Controlled-clock expiry PASS только старого пакета | Android denial на отдельном test login; actual device/session revocation 401/403; expiry нового пакета и полный scope |
| N04, event/probe fencing | Текущие Core concurrency/race и Android source tests сохранены | Exact installed event scenarios вместе с N03 |
| A02/A03, owned AWG | A02 I4 сохранён для exact Core/server/Pi; текущий Huawei прошёл managed AWG2/AWG3.1 и 22 server alignment checks | Whole-path MTU/packet matrix и полный parent scope |
| D02/D03/W05, сеть и нагрузка | Предыдущие измерения остаются ограниченными своим tuple | Network change, Doze, leak/IPv6, CPU/RAM/startup и energy по применимым exact inputs |
| B01–B08, backend | [Payment acceptance](EXECUTION-INTEGRATED-BACKEND-2026-09-08.md): 129 HTTP tests / 22 subtests, 9 PG cases PASS. [Actual old/current API compatibility](EXECUTION-INTEGRATED-BACKEND-COMPAT-2026-09-08.md): 25 HTTP assertions, 5 SQL writes и rollback PASS; 197+200 hashes, schema неизменна | Для exact pair новой expand/contract migration нет. Real providers, production process/volume/locks и actual snapshot/attachment recovery остаются открытыми |
| O/V, operator | Локальные реализации и проверки сохранены | Current deployed access/fingerprint и runtime evidence |
| G04/G06 | SKIPPED_BY_OWNER для платных GitHub checks/protection | Применимые бесплатные/local checks; skip не считается CI/enforcement PASS |
| M01 | SKIPPED_BY_OWNER для seller/receipt confirmation | Не подтверждает real payment/refund E2E |
| Q02–Q05 | OPEN | Soak/chaos, final go/no-go, отдельно разрешённые rollout, observation и закрытие |

## Проверки и сбой preflight

Preflight требовал старые SBOM names `pokrov-core.cdx.json` и
`sing-box.cdx.json`, тогда как текущие client seed и `validate-seed.ps1`
проверяют `core-source.cdx.json` и `engine-source.cdx.json`. Исправление
`16407b8` согласовало контракт, сохранив отказ при missing/malformed metadata.
Регрессия до исправления: 2 failed / 25 passed; после — 100 passed и 21 subtest.

Команды:

```powershell
python -B -m pytest -p no:cacheprovider tests/test_release_1_2_candidate_preflight.py tests/test_release_gate_check.py tests/test_release_orchestrator.py tests/test_check_script_manifest.py tests/test_agent_docs_contract.py -q
python -B scripts/release_1_2_candidate_preflight.py --platform-root E:/r12-integration-platform-20260908 --client-root E:/r12-integration-client-20260908 --core-root E:/r12core-implementation --release-index-root C:/Users/kiwun/Documents/ai/pokrov-release-index --output E:/r12-integrated-acceptance-20260908/candidate-preflight-clean.json
```

Отчёты: [quality gate](evidence/integrated-acceptance-20260908/010I-local-quality-gate.json),
[preflight](evidence/integrated-acceptance-20260908/candidate-preflight-clean.json),
[APK audit](evidence/integrated-acceptance-20260908/abi-package-audit.json),
[regression log](evidence/integrated-acceptance-20260908/preflight-tests-after.log).

Android runtime owner: `POKROV-app/docs/operations/evidence/2026-09-08-r12-integrated-android/`.
Client evidence commit: `7386ed3` (documentation only; packaged source remains
`7ae931b`). Client `pwsh -NoProfile -File scripts/validate-seed.ps1 -PlatformRoot
C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start -CoreRoot
E:/r12core-implementation` and `pwsh -NoProfile -File test/docs-contract.ps1`
passed. Platform docs/script contracts: 33 passed. `git diff --check` passed
in both worktrees; no `artifacts/releases/**` delta. No push or deploy.
Native service/TUN наблюдения и свежие screenshots подтверждают два bounded
цикла. UIAutomator idle failures вернули устаревший XML; его строки исключены
из UI evidence. APK перепроверен на устройстве в конце, VPN отключён, исходные
routes/rules восстановлены. Это не independent leak/egress proof.

## Внешние условия выпуска

Лицензированный Win10-стенд, real provider
операции, deployed operator proof, окончательные signing/channel и release
решения остаются в общей очереди. Owner skips не переоткрываются как просьба
об оплате. Авторизация тестовых профилей от 2026-09-08 сохраняется; production
release и расходы требуют своих конкретных решений. Postrelease-программа
не активируется локальным PASS этого комплекта.

# Старт выполнения consolidated-v2

Дата: 2026-09-05. Outcome: `COMPLETE` только для стартовой сверки `RECONCILE_ONLY`. Релиз: `BLOCKED`, без нового go/no-go.

Запрос владельца: «Привет, приступай к выполнению плана». Выполнен первый ограниченный этап из раздела 10, §3: baseline, сверка ближайших задач и исполнимые work orders. Текст вложения сохранён как входной план; его примеры `/goal` не запускались как отдельные команды владельца. Следующие implementation-пакеты описаны в [NEXT_WORK_ORDER.md](NEXT_WORK_ORDER.md). Production, публикация, платежи и postrelease не активированы.

## Исходники и рабочие каталоги

`git fetch origin` и `git ls-remote origin HEAD` выполнены для всех четырёх репозиториев, exit 0. Promotion HEAD совпадают со срезом приложенного плана.

| Remote | Local HEAD до работы | Проверенный remote HEAD |
| --- | --- | --- |
| Kiwunaka/portal | `826112cf18d7b66b19ae43eb6884c594d1adf402` | `6b41f758ca228a0d5ff13ede0f865096cdac2134` |
| Kiwunaka/POKROV-app | `2d6adfcebc37f2109ef339276be6a1569cb7aa1e` | `da1ad7395615837432615e0f150d7c0bf05322a4` |
| Kiwunaka/pokrov-core | `c1185faa998c69fd5164af415249c96c68ab61bd` | `c1185faa998c69fd5164af415249c96c68ab61bd` |
| Kiwunaka/pokrov | `7a6b2ce859b34b074e877851ba50aae7e80854a3` | `9169f272203ec690ab7b0e6a69e92dc2b6762cb4` |

Реальные корни, upstream, dirty paths и зарегистрированные worktrees сохранены в [evidence/baseline.json](evidence/baseline.json). Платформа отставала на 408 коммитов, клиент на 40, release-index на 4. Старые dirty изменения платформы и четыре клиентских `.obj` оставлены на месте. Чужие worktrees перечислены средствами Git; их файлы и индивидуальные dirty states не обследованы. `Pokrov-client` проверен по remote как отдельный legacy source lane и исключён из active-client write set.

Новый worktree: `C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start`, ветка `codex/consolidated-plan-start-20260905`, база platform remote HEAD выше. Клиент прочитан через `git show origin/main:<path>` из его repository object database: отстающий рабочий checkout не использовался как current source. Core и release-index не изменялись.

## Scope, candidate и сохранность

Действующий [OWNER-FREEZE](../2026-08-21--release-1.2.0-megaplan/OWNER-FREEZE-2026-09-05.md) сохранён. Публичные платформы, тарифы, route defaults, AWG lab/public граница и service/TUN ownership не переопределялись. Текущий запрос запускает старт нового плана, не автоматически все postrelease и release-operation действия.

Candidate.33 остаётся приватным `1.2.0+4053`. Его исходники отличаются от текущих promotion HEAD:

| Составляющая | Candidate.33 source SHA |
| --- | --- |
| Platform | `f5300053026d32826e54c02202303e1f68c65bc1` |
| Client | `6ab1bcaf39c61a0ae0c9d8328e6c95382885735e` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Release index | `63993fba699b68641b7e972071ab7729fa9ec43c` |

Read-only SHA-256 и размеры **10/10** именованных файлов совпали с freeze-инвентарём: шесть бинарников, manifest, detached signature, receipt и handoff. См. [preservation.json](evidence/preservation.json). Файлы не копировались и не пересобирались. Это подтверждение сохранности bytes; подпись повторно криптографически не проверялась, signing custody и runtime не проверялись.

GitHub artifact `9928470408` в `Kiwunaka/pokrov` на момент readback: `expired=false`, `expires_at=2026-09-18T08:01:25Z`, размер 7955. Локальные manifest/signature/receipt уже доступны и совпадают. Remote readback сохранён в [remote-readback.json](evidence/remote-readback.json).

Исторический [Gate F](../2026-08-21--release-1.2.0-megaplan/evidence/013GV-candidate33-bounded-windows-android-runtime/013GV-candidate33-gate-f-decision.json) остаётся `BLOCKED`, 2 PASS / 17 non-PASS / 0 FAIL. Это сохранённое решение, а не свежий запуск 19 проверок. Public `1.1.6` — сохранённая authority freeze; production/download readback сегодня не выполнялся.

## Реестры и происхождение

- 13 разделов вложения импортированы с рабочими межфайловыми ссылками; исходный SHA-256 и хеши извлечённых файлов — [import-manifest.json](evidence/import-manifest.json). Хеши раздела 12 относятся к исходному пакету, а не к этому преобразованию.
- [R12-REGISTER.csv](R12-REGISTER.csv): все 83 ID; несверенные задачи `I0 / NOT_REVIEWED`, без фиктивного PASS. Их постановка целиком сохранена в [03](03_RELEASE_BACKLOG_83.md).
- [LEGACY-378-REFERENCE.csv](LEGACY-378-REFERENCE.csv): все 378 пар `(plan,id)` с указателем на неизменённую исходную строку ledger. Статусы, evidence и next_action остаются в оригинале. Ближайшие связи с R12 перечислены в [сверке](SOURCE_RECONCILIATION.md); остальные сопоставляются при выборе WO, а не объявляются автоматически эквивалентными.
- Postrelease ATS/CR/WP/HAPP/shortlink сохранён в разделах 04–08, без запуска. У локального HAPP-источника обнаружен возможный путь в dirty platform checkout; это кандидат на восстановление для HAPP-01, его содержание ещё не принято как полный source.

## CI и evidence invalidation

`.github/workflows/release-v2-contract.yml` содержит реальный cross-repository contract job. Client workflow вызывает `validate-seed.ps1` и `run-tests.ps1`. Старый platform PR-00 workflow ограничен веткой `codex/1.2.0-pr00-true` или dispatch; он не является общим gate для новых веток.

Свежий readback клиентского job `101249235240`: `completed/failure`, **0 steps**, 2026-09-05 04:35 UTC. Freeze связывает отказ с billing; отдельного нового billing-readback нет. Hosted CI не получает PASS от локальных тестов. G04 остаётся незакрытым, Actions не запускались.

Текущий diff — документы и их навигация. Он не инвалидирует старые binaries/runtime evidence и не превращает их в evidence текущих source HEAD. Следующий N-slice инвалидирует proof profile/reconnect, связанные host lifecycle и packaged runtime acceptance для новых bytes. B-slice инвалидирует checkout/return/deadline acceptance и связанные frontend bundles; backend/schema изменения дополнительно требуют order/reservation/concurrency проверки. Независимые AWG interop результаты не переснимаются из-за документационной правки. Исторические receipts/Gate F никогда не редактируются для нового результата.

## Проверки и границы результата

Команды, exit codes и краткие результаты — [evidence/checks.json](evidence/checks.json). Источник локальных проверок: новый platform worktree на указанном HEAD, Python 3.12.5, synthetic/local tests, `current-origin`.

Проверки на физическом устройстве, Windows VM, PostgreSQL с двумя соединениями, provider E2E, brain/RU-origin, signing и новая сборка: `NOT_RUN` в стартовом scope. Доступность Pi/VM/телефона не считается PASS.

Новых commit, push, PR, deploy или release нет. Изменения оставлены для просмотра в отдельной ветке. Rollback текущей работы — исключить этот scoped documentation diff; оригинальные ledger, candidate bytes и concurrent checkout не тронуты.

# R12-D05 — нативные логи, notification и счётчики

Дата: 2026-09-06. Статус: **I3 / NEEDS_RUNTIME_PROOF**.
Core: `94dd31012ac91fb9ecf2c98ad7383afb54102dd4`.
Client: `453975348d91bfb78bb3bfb90660c000a9ccd692`.
Команды, SHA исходников, сборок, логов и сохранённых JUnit XML:
[evidence/d05-native-logging.json](evidence/d05-native-logging.json).

## Исправление

Проверка воспроизвела утечку planted value в подписку настоящей Go log factory.
Android callback уже фильтровал сообщения, но до него engine writer,
observable subscriptions и `StartedService` replay buffer получали сырой текст.
Теперь managed service задаёт фильтр до этих sinks: произвольные сообщения
заменяются `runtime_log_redacted`, произвольный logger tag удаляется. Остаются
только закрытые AWG/probe категории. Прямой `WriteMessage` также фильтруется
перед буфером. Проверены обычный и debug режимы, writer, обе подписки, callback,
replay buffer и сохранение panic-семантики с безопасным payload.

Это проверка реальных нативных классов на локальном Go host. Она не заменяет
инспекцию всех log paths установленного APK на заявленных Android/OEM.

Home теперь подписывает live-speed карточку «Сейчас через POKROV».
Android получает session totals от Core/TUN, обрабатывает reset/unavailable и
не использует UID-wide `TrafficStats`. Account traffic в Profile остаётся
отдельным измерением `panel_runtime`.

## Сверка существующих Android contracts

| Критерий | Локальная проверка | Открытая граница |
|---|---|---|
| Private lockscreen | Notification/channel private visibility и generic public version; 2 content + host security tests | Реальный lockscreen/OEM |
| Bounded journal | Закрытые record types, app-private no-backup storage, current/previous по 256 KiB, bounded queue/record/rate; 8 journal tests | Права файлов и ротация на устройстве |
| Structured allowlist | 15 classifier tests; новый Go planted-value regression до native sinks | Все пути финального installed package |
| Tunnel counters | 4 tracker tests, host generation guards и ясная подпись Home | Сопоставление с реальным TUN/UID traffic |

## Точные локальные bytes и проверки

Две сборки на платформу byte-identical; Android содержит четыре ABI и оба
correlated probe methods, Windows — 15 обязательных exports.

| Артефакт | Размер | SHA-256 |
|---|---:|---|
| AAR | 107471658 | `fa62c1116c55fe770f691bf62c8b3f613a5fb1f889226458f15fee8f62820512` |
| DLL | 55443968 | `38d40a1713c1cb5b3ad90ab5b4e66df68d5463b38945abac9d322be859b57c6b` |

Предыдущий binding сохранён в client
`docs/operations/evidence/2026-09-06-r12-d05-core-binding/previous-runtime-binding.json`;
новые reproducibility JSON находятся рядом. Предыдущие сборки остаются в
`E:/POKROV-tools/builds/core-6bc3603-n05/`, новые — в
`E:/POKROV-tools/builds/core-d05/`. SBOM warnings не означают license clearance.
Метка генератора `UNSIGNED_CI_BUILD_EVIDENCE` не подтверждает hosted CI:
эти сборки выполнены локально, workflow/run/runner fields пусты.

- Core targeted packages и `scripts/test.ps1`: PASS; затем финальный daemon
  `go test -race ./daemon -count=1`: PASS, включая добавленный panic test.
- Обе Android JVM suites на новом AAR: 372 PASS, по 186 на flavor.
- Home/observability/copy: 190 PASS; runtime: 80 PASS + один opt-in skip.
- Отдельный запуск opt-in теста на synced DLL: 100 proxy-only cycles PASS.
- Analyze, seed, client docs, source logging (151 files + 4 negative fixtures)
  и platform docs (33 tests): PASS.

Первый DLL smoke завершился тайм-аутом через 10 минут: повторно использованная
тестовая БД сообщала `file missing`. Та же DLL с новым TEMP прошла 100 циклов
за 11 секунд. Helper теперь создаёт отдельный каталог на запуск, сохраняет его
для инспекции и восстанавливает TEMP/TMP. Финальный запуск helper на synced DLL
прошёл за 12 секунд. Первый failed log и прежняя БД сохранены; причина порчи
прежней БД отдельно не установлена. Системные маршруты/TUN тест не создаёт.

## Граница и rollback

D01, installed API/ABI/OEM matrix, physical lockscreen/journal/native-log
inspection и реальные tunnel counters: **MANUAL_OWNER_TEST**. Последняя
проверка доступа D04 показала 0 ADB devices; нового device proof нет.
Windows service/TUN/DNS, независимый RU-origin и новый подписанный кандидат
остаются открытыми. D05 и весь план не закрыты.

Core/client изменения закоммичены локально. Push, merge, deploy, signing,
публикация и изменения `artifacts/releases/**` не выполнялись. Для rollback
сохранены предыдущие binding и builds; откат source/binding должен быть
согласованным и не выдаёт прежние bytes за исправленные.

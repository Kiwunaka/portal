# C05: привязка исправленного Core к клиенту

Дата: 2026-09-06. Статус: **active / I3 / PARTIALLY_FIXED**.
Продолжение [Core remediation](EXECUTION-C05.md); прежний отчёт сохранён
как наблюдение до consumer binding.

Client implementation: `510aedb`, затем исправление сохранности receipt bytes
`c2c6f966f0742f58d52043df50ca2d6f3e26edb2`. Core: `8dc57a830bd1487389dd1b7c9190f094c31e13bc`.
Source worktrees: `E:/r12client`, `E:/r12core-implementation`.

## Изменение

Development-клиент теперь использует C05 DLL/AAR, собранные в предыдущем этапе.
Guarded sync проверил clean Core source, VERSION, размеры, SHA-256 и dependency
Cronet. Обновлены два LFS artifact pointers, `runtime-artifacts.seed.json`,
его validator и synthetic release-handoff fixture. Canonical binding,
bootstrap, Android/Windows readiness и WARP boundary описывают эту identity.
Старая N05-current секция решения помечена как superseded; реальным предыдущим
binding был D05, который сохранён отдельно.

| Artifact | Размер | SHA-256 |
|---|---:|---|
| AAR | 107483275 | `bc5ef7ece6ba6c138589307a7c5e30be32ec01cdd396e23dfdb8840011148b29` |
| DLL | 55449088 | `c679ba5af42939acbc8c6f44af59b4608f6a76c99e0d444cfa4bcc825bcc8e68` |

Первичный client receipt:
`docs/operations/evidence/2026-09-06-r12-c05-core-binding/client-backtests.json`.
[Platform reference](evidence/c05-client-binding.json) закрепляет его Git commit,
SHA, copied build evidence и результаты проверок.

## Выполненные проверки

- Runtime/Android analyze: **PASS**, no issues.
- Runtime Flutter: **80 PASS**; default opt-in skip закрыт отдельным запуском
  real Windows Core helper на synchronized DLL.
- Android Flutter: **8 PASS**.
- Android JVM: **372 PASS**, по 186 на Direct/Store. Первый Gradle запуск
  использовал UP-TO-DATE test results; затем обе test tasks реально выполнены
  с `--rerun`. XML скопированы и hash-bound в `E:/r12-c05-client-junit/`.
- Windows synced DLL: **100 proxy-only start/stop cycles PASS**, новый TEMP
  изолирован и сохранён. Это не SCM/TUN/DNS proof.
- Seed, docs, version/observability parity, release-source logging
  (151 production files + 4 negative fixtures), synthetic release contracts:
  **PASS**. Это проверки источников/fixtures, не новый релизный Gate F.

После первого commit обнаружено, что Git нормализовал CRLF evidence JSON в LF,
а manifest закреплял оригинальные bytes. Локальный hash check этого не ловил.
Для новой C05 evidence-папки добавлено scoped `-text`; whitespace rule признаёт
CR at EOL, сохраняя остальные trailing-space проверки. Посторонние файлы и
история не переписывались. Финальные **Git blobs** обоих build receipts совпали
с manifest SHA, все четыре JSON — с сохранёнными bytes, оба LFS pointer OID —
с synchronized DLL/AAR. Первый commit и причина исправления сохранены.

## Rollback и остающаяся работа

`previous-runtime-binding.json` сохраняет D05 manifest. Прежние Core dist,
client bytes и rollback builds сверены до замены. Старые сборки остаются в
`E:/POKROV-tools/builds/core-d05/`; новые — в `E:/r12-c05-artifacts/`.
Rollback требует вернуть согласованные manifest/validator/pointers, затем
проверить exact old bytes. `artifacts/releases/**` не изменены.

Это закрывает перенос Core correction в development consumer. Final APK/EXE
scan, complete native/license/notice coverage, оставшаяся advisory reachability
и installed runtime privacy остаются открытыми. JVM тесты не исполняют Android
native runtime. Physical Android, Windows SCM/TUN/installer, WARP, RU-origin и
brain-origin не подтверждены. Старый offline Win11 lab остаётся на D05 bytes.
Кандидат, signing, публикация, push, merge, deploy и provider operations в этом
этапе не выполнялись; общий план не завершён.

# Явный запрет доступа: исправление и Windows приёмка

**PASS_BOUNDED** для client `f479fd4` / Core `02a091c`, Windows setup
`f44486c3ae32ac5c3020e9b76c997902c202084076cb7954bc0678d5805f676d`.
Общий комплект обновлён после изменения Dart-кода; прежний Android APK
не содержит исправления. Полные N02/N07/A04 и release gates открыты.

Последующее обновление Android завершено: [новые inputs](evidence/integrated-acceptance-20260908/inputs-access-denial.json),
четыре APK `f479fd4`; ARM64 `20a0781b…97af` установлен на Huawei. Восемь
проверок update/connect/resume/disconnect и routes/rules cleanup PASS_BOUNDED.
APK подпись, ABI, native hashes и notices PASS; Core/Flutter/notices прежние,
Dart AOT изменился. Current Android owner evidence:
`POKROV-app/docs/operations/evidence/2026-09-08-r12-android-access-denial/README.md`.
Для физического denial/revocation запрошен отдельный test login: телефон
привязан к основному runtime admin. Его текущая сессия и backend не изменялись.
Положительная device проверка не считается отрицательной; этот gate открыт.
Android evidence commit: `408e936`; 18 staged Git blob hashes PASS. Повторные
client seed/docs contracts PASS; platform 33 tests, context audit и package
validator (350 local links) PASS. Пять artifact hashes нового input inventory
перепроверены по локальным bytes. `git diff --check` PASS.

На прежнем Windows `3784352` воспроизведён дефект: подписка уже возвращала
HTTP 200 / `expiredOrBlocked`, managed profile — 503, а клиент подключался из
кэша. Тестовая подписка истекла естественно; backend не изменялся.

Исправление удаляет защищённый кэш после явного запрета, запрещает fallback
и отключает работающий туннель. Запрет, пришедший во время native connect,
применяется после завершения операции. Canonical bootstrap и persisted-state
обновлены в client source commit `f479fd49f7904bda5c916e5f7148675f45105872`.

Новый пакет установлен в Win11 VM: 304 ожидаемых файла совпали до запуска и
после сценария, session bytes сохранены. При блокировке API кэш подключался;
после восстановления API явный запрет удалил кэш и отключил TUN. Новый процесс
UI с вновь заблокированным API не подключился: TUN нет, нового connected event
нет, owned health по независимому запросу HTTP 200. Все 15 assertions PASS.
Routes/DNS восстановлены, временные firewall rules удалены, VM off/NIC none.
В исправленном сценарии часы не менялись. Старый package-only файл
`native_assets.json` не входит в новый 304-file manifest; отсутствие любых
лишних файлов в каталоге установки не утверждается.

На предыдущем пакете отдельно проверен 24-часовой предел кэша через временный
перевод часов VM: возраст 92 989 секунд, подключение отклонено. Первый замер
с автоматической синхронизацией часов недействителен и сохранён отдельно.
Настройки времени восстановлены. Это controlled-clock proof для старых bytes,
не реальный 24h soak, не clock-rollback proof и не expiry proof нового пакета.

Client owner evidence:
`POKROV-app/docs/operations/evidence/2026-09-08-r12-access-denial/README.md`.
Receipt содержит 43 byte-preserved файла и их hashes: исходный failure,
исправленный runtime, package/installed manifests, cleanup, collectors и logs.
Client evidence commit: `5fd6840`; все 43 staged Git blobs совпали с receipt.

Документационные gates: `python -B -m pytest -p no:cacheprovider
tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
— 33 PASS; `python -B scripts/agent_context_packet_audit.py
--platform-context-root .` — PASS; `validate_package.py` — 83 R12 IDs,
378 retained legacy IDs, 347 local links PASS. `git diff --check` PASS в обеих
ветках; `artifacts/releases/**` не изменены.

Проверки source: два regression FAIL до исправления; затем 301 Flutter tests
из `app_first_runtime_bootstrap_test.dart`, `pokrov_seed_app_test.dart`,
`managed_profile_cache_test.dart`, `cached_profile_fallback_gate_test.dart` PASS;
полный `flutter analyze --no-pub` для app_shell — 0 issues. Windows reproducible
build script завершён; название script не доказывает две идентичные сборки.
`validate-seed.ps1` с явными platform/Core roots и `test/docs-contract.ps1` PASS.

Дальше: выполнить Android denial scenario на отдельном test login;
отдельно проверить actual session/device revocation 401/403
и expiry на новом комплекте. Старые AWG/route/update receipts сохраняют только
свои исходные bytes. Новый candidate, push, production deploy и публикация
не выполнялись. Разрешение на тесты сохраняется; release/spend границы прежние.

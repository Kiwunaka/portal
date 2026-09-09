# R12-N05 — наблюдения и причины, 2026-09-06

Статус: **локальная реализация I3; полный план ACTIVE / RELEASE_BLOCKED**.
N01/N03 и проверки новых сборок на устройствах остаются открытыми. Новый
confidence/Broker engine не добавлялся. Коммиты: client `f173f39`, `c78c458`,
Core `6bc3603`, platform `9f48273`. Все локальные.

## Изменения

- Отсутствие сети не превращается в DNS fault; неизвестный `default_network_*`
  не доказывает offline. Явный сбой сохраняется поверх неполного DNS/egress proof.
- Каталог отдельно описывает offline, DNS, endpoint connect, UDP timeout,
  TLS handshake timeout, response stall, runtime, entitlement и provisioning.
  Новый `API-011` сохраняет pending provisioning; `CORE-009` — неизвестный runtime;
  `ROUTE-005` — невозможность определить интерфейс. Refresh timeout сохраняет
  `API-002` вместо утверждения, что entitlement отсутствует.
- Core использует тип ошибки и реально пройденную стадию URL probe. Общий timeout
  остаётся общим. MTU/DPI/ASN/whitelist не объявляются причиной по одному таймауту.
  Исправлена отмена сразу после dial: она больше не возвращает успешный URL test.
- Android/Windows и Dart принимают новые закрытые event-коды; обновлены shared
  hash snapshots, support reference и canonical runtime docs. ABI2/event ABI1
  не меняют форму. Новые AAR/DLL привязаны к одному Core source и точным SHA.

## Проверки и байты

Точные команды, source tuple, SHA логов и сохранённые неуспешные попытки —
[evidence/n05-observed-failures.json](evidence/n05-observed-failures.json).

- PASS: Core full + race; native Windows 9/9.
- PASS: общий клиентский набор — 594 Flutter tests, один прежний opt-in skip;
  оба Android flavors. После замены AAR Gradle gates повторены, PASS.
- PASS: клиентский analyze, validate-seed; platform observability/support/data
  inventory — 23 tests. Начальные regressions до исправлений сохранены.
- PASS: Android и Windows по две побайтно одинаковые сборки. AAR: четыре ABI
  и оба per-call probe метода. Windows: 15 exports и 100 proxy-only cycles.
- Core: `6bc36034c86528972488fc203a98512686ac4db9`.
- AAR: 107465916 bytes; SHA-256
  `9f99134528e8309f60b2fb20bfed9df9db7f5fa978ec1f13b7d329e2a70cf19b`.
- DLL: 55440384 bytes; SHA-256
  `148453156b61bf22c18d987cbf0cd8a47c0bf99636b2650c016310e92bc3384b`.

Build evidence и snapshot прежней привязки сохранены в клиенте:
`docs/operations/evidence/2026-09-06-r12-n05-core-binding/`. Оба build trees,
SBOM и JSON receipts — `E:/POKROV-tools/builds/core-6bc3603-n05/`.
SBOM warnings о license/version metadata остаются незакрытыми. Старые runtime
bytes сохранены в `E:/r12-artifacts/final/`; candidate.33 не изменён.

## Граница

Это проверка исходников, synthetic ошибок и локальных библиотек. Новый APK,
installer, signing, physical Android, Windows TUN/DNS/VM, RU/brain origin и
release acceptance не выполнены. Поведение fallback этим slice не расширяется.
N02 ждёт решения об authority rollback; O03 — об источнике operator data.
N06 продолжает существующий bounded fallback, без нового Broker/ATS.

Push, merge, deploy, новый candidate и публикация: **NOT_PERFORMED**.
Rollback исходников — согласованная отмена scoped taxonomy/consumer/binding
коммитов; старые release receipts не переименовываются и не переносятся на новые
байты. Посторонние generated instruction/registrant файлы не включены.

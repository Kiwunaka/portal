# R12-C05 — поставка Go native notices в Android и Windows

Дата: 2026-09-06. **I3 / PARTIALLY_FIXED**. Полный C05 остаётся открыт.
Client implementation: `1032c4801d68b4f67e4a6bc0fdc018f20886d680`.
Core source прежний: `8dc57a830bd1487389dd1b7c9190f094c31e13bc`.
Продолжение [Windows Cronet notices](EXECUTION-C05-NOTICES.md).
Точные команды, source и retained hashes —
[evidence/c05-go-notices.json](evidence/c05-go-notices.json).

## Исправление

Предыдущий package audit сохранил 130 root notice-файлов для 127 из 128
записанных Go module entries только в audit-архиве. Они не входили в APK или
Windows bundle. Теперь общий asset `native-go-NOTICES.txt` включён через
`packages/app_shell/pubspec.yaml` в обе платформы.

Asset содержит 145 побайтно сохранённых текстов: прежние 130 root notices,
Core LICENSE, ray2sing LICENSE, Go LICENSE/PATENTS и 11 дополнительных module
PATENTS. SHA-256 `c0389ada6e70b079fb964eb04ec015db63db85e699b7d82e21a64b568c1c19f3`,
550167 bytes, 131 раздел. Указаны фактические replacement sources; local Core
файлы прочитаны из закреплённого Git commit. `go mod verify` дал PASS.
Это root input inventory, не утверждение, что каждый модуль присутствует на
каждой платформе или что все вложенные/native notices уже найдены.

Runtime manifest связывает файл с SHA-256, Core source commit и Go toolchain.
Seed проверяет наличие, hash, source/toolchain binding и asset declaration.
Git `-text` сохраняет исходные license bytes; после staging проверены hash
всего Git blob и все 145 body offsets/hashes. Тексты лицензий не редактировались.
Canonical bootstrap owner и Android/Windows readiness обновлены.

## Проверка поставки

| Проверка | Результат и граница |
| --- | --- |
| Четыре Direct APK | PASS: release-mode universal, ARMv7, ARM64 и x86_64; notice и все 145 body hashes совпали, Golos OFL сохранён |
| Android Core | Все встроенные `libpokrov-core.so` побайтно совпали с закреплённым AAR |
| Android signing | `apksigner verify --print-certs` PASS на четырёх APK; signer — внутренний Android Debug |
| Windows build | Первый запуск FAIL на stale CMake cache prefix; после нового isolated prefix — PASS |
| Windows bundle | 302 файла; добавлен notice, изменён только `AssetManifest.bin`, остальные 300 файлов совпали с предыдущим 301-file bundle |
| Windows binaries/notices | Core/Cronet/OFL/Cronet notices совпали с inputs; только app/service EXE, test EXE отсутствует; app EXE `NotSigned` |
| Seed/docs | PASS; included performance collector остаётся fixture, не physical measurement |
| Git/release boundary | `git diff --check` PASS; `artifacts/releases/**` delta отсутствует; четыре прежних generated registrants сохранены побайтно |

Пакеты используют loopback API `http://127.0.0.1:9`, version define `1.2.0`.
Они сохранены отдельно в `E:/r12-c05-go-notices/`; прежние package artifacts
и candidate.33 не перезаписаны. Приложения, VPN, service и installer не запускались.

Первый Android checker искал asset под ошибочным package name `app_shell`;
исправлен на объявленный `pokrov_app_shell`, product code не менялся.
Первый Windows install получил некорректный literal prefix
`E:/r12client/$<TARGET_FILE_DIR:pokrov_windows>` из предыдущего cache restore.
После успешного isolated build cache восстановлен через `-U CMAKE_INSTALL_PREFIX`;
generated install script снова указывает на обычный runner/Release каталог.
Seed completion пришёл в information stream, отдельно от stdout log;
terminal result с exit 0 сохранён отдельно. Ошибки проверок не скрыты.

## Открытые критерии

Psiphon utls `v0.0.0-20260129182755-24497d415a8d` по-прежнему не имеет
retained root license. Это явно отражено в asset, manifest и evidence;
чужой license текст вместо него не подставлялся.

Nested/native/Flutter/Microsoft coverage, corresponding-source delivery,
остаточные advisory, final packaged privacy/license review, physical Android
и Windows installer/SCM/TUN/origin acceptance остаются OPEN.
Общий C05, новый release candidate и весь план не завершены.

Push, merge, deploy, публикация и production signing не выполнялись.
Source rollback — отмена client commit в его feature branch; prior binaries,
runtime binding, candidate и evidence сохранены.

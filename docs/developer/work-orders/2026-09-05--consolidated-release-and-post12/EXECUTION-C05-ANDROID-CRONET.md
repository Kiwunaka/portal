# R12-C05 — Android Cronet native graph и notices

Дата: 2026-09-06. **I3 / PARTIALLY_FIXED**, полный C05 открыт.
Client `0e69b11`, Core `8dc57a8`, native source `30f3a568`.
Продолжение [Maven notices](EXECUTION-C05-MAVEN-NOTICES.md).
[Receipt, Git blobs и проверки](evidence/c05-android-cronet.json).

Добавлен Android asset `cronet-NOTICES.txt`: 31 секция / 173535 bytes,
SHA-256 `7c60e87757cfefe0f865c64b70eafe7ee2d64e4cb2c7275ab05dadc5292e54b5`.
Pubspec включает его в APK; Git сохраняет исходные bytes.

В существующей локальной Ubuntu VM построены четыре графа закреплённым GN
`07d3c6f4dc29` с аргументами wrapper `dc1cda1f`. Реальные Clang package и NDK r28
получены из официальных HTTPS источников. Clang server MD5 совпал; для NDK
сохранён SHA-256, независимый server MD5 отсутствовал. Это graph preparation,
не native compilation или доказательство первоначального build environment.

В каждом графе 329 linked targets. Мультимножества имён compile objects точно
совпали с закреплёнными archives: arm64 2663, arm 2663, amd64 2666, 386 2665.
Non-assembly STT_FILE совпали: 2538/2538/2540/2540. Basenames не доказывают
равенство source bytes/команд компилятора и не различают одноимённые пути.
4771 исходный GN-declared файл имеет hash; все 30591 исходных entries после
генерации неизменны. Android 386 остаётся AAR-only, не выдан за APK runtime.

Android добавляет libunwind, CPU Features и JNI Zero. Отдельный BSD header
CPU Features NDK compatibility включён вместе с основными лицензиями.
Windows-only Mozilla Cert исключён. Для Perfetto, Protobuf и compiler-rt
повторно сверены все 7693/682/4 source files с прежним snapshot: идентичны.
Только после этого переиспользованы их upstream license authentication и
сохранённые fork diffs. Тела notices скопированы побайтно, включая точный
2091-byte Perfetto/OpenBSD header. CycloneDX 1.6 supplement: 25 source directories
и четыре static archive inputs; это не полный application SBOM.

**PASS:** четыре Direct release-mode APK, все 31 body hashes, схема SBOM,
client seed/docs и staged diff. Из прежних ZIP entries изменился только
AssetManifest.bin; DEX, SO и предыдущие notices совпали побайтно. Signer —
Android Debug, API loopback. Seed performance collector использует fixture.
Четыре прежних generated registrants сохранены; release artifacts не менялись.

VM `POKROV-r12-b08-linux-20260906` снова выключена; прежние лабораторные сервисы
оставались inactive. Исходный WSL failure, GN missing-tool failure и предупреждение
об unused `android_ndk_major_version` сохранены. После исправления 35 NDK
symlink entries все четыре полных graph hashes остались прежними. Оригинальные
archives сохранены; native engine, VPN, установка сервиса не запускались.

Evidence: `E:/r12-c05-android-cronet/`, архив 154 файла / 20022280 bytes,
SHA-256 `dd78a5acbc9810dac31e6dc3c381d087f73004582c9662d2434246d356beb0ce`.
Каждая запись проверена. APK, source ZIP, compiler/NDK archives и финальный
seed log сохранены отдельно и привязаны hashes в receipts.

Полное transitive include/file-level покрытие, совместимость лицензий,
uTLS root license, corresponding source, native advisory/reachability,
installed privacy и final candidate/device/SCM/origin acceptance остаются OPEN.
Push, merge, deploy, production signing, публикация и новый candidate не выполнялись.
Rollback — scoped client commit; прежние packages и evidence сохранены.

Platform handoff verification (2026-09-06):

- `python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q` — **PASS**, 33 tests.
- `python -B scripts/agent_context_packet_audit.py --platform-context-root .` — **PASS**.
- `python -B docs/developer/work-orders/2026-09-05--consolidated-release-and-post12/validate_package.py` — **PASS**, 13 section hashes, 83 R12 IDs, 378 legacy IDs, 237 local links.
- Python SHA-256 readback of the receipt against all 13 committed client Git blobs and the retained archive — **PASS**.
- `git diff --check` — **PASS**.

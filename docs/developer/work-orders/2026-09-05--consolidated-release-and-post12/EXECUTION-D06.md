# R12-D06 — размер APK и исключение debugger resource

2026-09-06. **I3 / NEEDS_RUNTIME_PROOF**: локальная проверка и исправление
упаковки PASS; D01 и полный D06 остаются открытыми до final candidate acceptance.
Client `3d21244`, Core `8dc57a8`. [Receipt и hashes](evidence/d06-size.json).

Разобраны четыре локальных Direct release-mode APK по каждому ZIP entry,
ABI/Core/Flutter/Dart AOT, assets, fonts, Android resources, лицензиям и
ZIP/signing/alignment overhead. Суммы сходятся с точными размерами файлов.
Это Android Debug signing и loopback API, не production packages.

| APK | После исправления, bytes | Сокращение, bytes |
| --- | ---: | ---: |
| ARM64 | 101225939 | 891 |
| ARMv7 | 90740169 | 891 |
| x86_64 | 110234866 | 891 |
| Universal | 295210670 | 891 |

ARM64 меньше universal на 193984731 bytes, 65,71%; все три ARM64 SO совпадают
между ними. Platform source `marketing/src/lib/release-assets.ts` выбирает
ARM64; `webapp/src/components/cabinet/downloads-surface.tsx` сохраняет universal
fallback. Публичный download readback здесь не выполнялся.

Удалён только `DebugProbesKt.bin` через существующий Android packaging block.
До исправления он побайтно совпадал с kotlinx-coroutines-core-jvm 1.7.1.
[Upstream 1.7.1](https://github.com/Kotlin/kotlinx.coroutines/blob/1.7.1/README.md#avoiding-including-the-debug-infrastructure-in-the-resulting-apk)
описывает исключение этого debugger resource без потери обычной функциональности.
Его 782 compressed bytes и 109 bytes overhead дают сокращение 891 byte.
Во всех четырёх APK это единственная удалённая запись; остальные
377/377/383/377 entries, включая DEX, SO, manifest, fonts и notices, совпали
побайтно. Их compressed sizes также не изменились.

До этого C05 notices увеличили каждый APK на 136282 bytes: 135592 compressed
license bytes, 65 bytes AssetManifest и 625 overhead. Core занимает 78530968
bytes ARM64 APK. Runtime и обязательные лицензии не сокращались ради размера.
Три дубликата брендовых PNG (211103 bytes) сохранены: текущий shared component
читает unqualified host asset, удаление этой копии сломало бы отображение.
`META-INF/services/m2.a` — 6-byte Java provider metadata, не native ar archive.

Полный filename inventory не содержит desktop binaries, evidence, logs,
dumps, PDB/source archives. В девяти SO нет `.debug_*`, `.zdebug_*` и
`.gnu_debuglink`; AAPT не показывает debuggable application. Это целевая
проверка упаковки, не замена full C05 privacy/advisory/source acceptance.

**PASS:** 8 Android Flutter tests; оба Android Gradle flavor — по 186 JVM tests,
0 failures/errors/skips; сборка четырёх APK; byte comparison и подписи;
client seed/docs и staged diff. Performance collector в seed использует fixture.
Точные команды, raw log hashes и client Git blob hashes сохранены в receipt.

Client owner: `E:/r12client/docs/operations/android-release-audit.md`.
Полный разбор: `E:/r12client/docs/operations/evidence/2026-09-06-r12-d06-size/README.md`.
Evidence archive: `E:/r12-d06-size/d06-evidence.zip`, 97 файлов, 175719 bytes;
каждая запись сверена. APK сохранены отдельно, прежние C05 packages сохранены.

D01 physical ARM64, exact signed final tuple, installation/distribution и
full C05 остаются OPEN. Store release AAB здесь не собирался. Нет push, merge,
deploy, publication, production signing, VPN execution или нового candidate.
Release artifacts не менялись; четыре прежних generated registrants сохранены.
Rollback — scoped Gradle exclusion commit, без удаления evidence.

Platform handoff checks: docs/context pytest — **33 PASS**;
`agent_context_packet_audit.py --platform-context-root .` — **PASS**;
`validate_package.py` — **PASS**, 13 imported hashes, 83 R12 IDs,
378 legacy IDs, 238 local links; `git diff --check` — **PASS**.
Fresh SHA-256 readback verifies all 23 committed client blobs, four APKs
and the retained archive against the platform receipt.

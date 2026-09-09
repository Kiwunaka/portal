# R12-C05 — Android Maven notices и встроенный Protobuf

Дата: 2026-09-06. **I3 / PARTIALLY_FIXED**; полный C05 открыт.
Продолжение [Flutter/native проверки](EXECUTION-C05-FLUTTER-NATIVE.md).
Client commit `46ac645`; Core `8dc57a830bd1487389dd1b7c9190f094c31e13bc`.
[Receipt, Git blob hashes и проверки](evidence/c05-maven-notices.json).

## Изменение и происхождение

Android получил отдельный `assets/licenses/maven-NOTICES.txt`: 176690 bytes,
164 текста и атрибуции, SHA-256
`06b7256830d0d19ec1aeb70326ea8216b830e2c41a29cb3c4314e7ca84f180af`.
Pubspec включает этот asset; Git сохраняет его bytes без EOL-нормализации.

Свежий `directReleaseRuntimeClasspath` совпал с прежним 68-module graph.
После исключения Core и четырёх Flutter coordinates остаются 63 Maven records:
58 уникальных бинарников и пять metadata/redirect-only coordinates. Все 58
побайтно совпали с загрузками из Google Maven или Maven Central. Две повторные
Gradle artifact rows не посчитаны отдельными компонентами. POM и два Guava
parent POM сохраняют заявленные Apache-2.0 terms.

Просмотрены 4035 исходных файлов в 59 source JARs. В asset включены 159
различных source comment blocks; четыре совпадения про media metadata/bit fields
исключены как нерелевантные. Сохранены CC BY 2.5 headers четырёх JSR-305
concurrency annotations, MurmurHash attribution, Kotlin Boost/GWT/Guava headers.
Добавлены полные Apache, Boost и Protobuf license bodies и уже поставлявшийся
AndroidX license. CC BY legal text извлечён из `legal-code-body` официального HTML;
исходный HTML сохранён. Остальные тела скопированы побайтно. Версии и ссылки
ограничивают область атрибуции; не утверждается, что каждый source file
пережил R8 shrinking или вошёл в runtime.

## Встроенный Protobuf

В Tink Android обнаружены 542 shaded Protobuf class entries, отсутствующие
как отдельная зависимость Gradle. Tink `v1.21.0` MODULE.bazel объявляет
`protobuf-javalite 4.33.0`, а jarjar rules задают relocation package.
Все 539 имён классов официального JAR найдены после этого переименования;
в Tink ещё три anonymous `WireFormat$Utf8Validation` classes. Это source/version
binding с явным отличием, не доказательство byte reproduction.

CycloneDX 1.6 supplement содержит 58 выбранных Maven artifacts и Protobuf
с пометкой о source-declared версии. Полный application SBOM остаётся отдельным
требованием. OSV query для Protobuf 4.33.0 вернул ноль advisory IDs и не имел
pagination; этот результат не доказывает отсутствие всех уязвимостей.

## Проверки и ограничения

- **PASS:** четыре Direct release-mode APK содержат точный asset и все
  164 body hashes. Из старых entries изменился только `AssetManifest.bin`;
  DEX, SO и прежние notices совпали побайтно. Signer — Android Debug, API loopback.
- **PASS:** CycloneDX 1.6 schema, client seed/docs, staged asset hashes и diff.
  Performance collector внутри seed использует fixture. Четыре прежних
  generated registrants сохранены побайтно; retained release artifacts не менялись.
- Evidence archive: 290 файлов / 512727 bytes, SHA-256
  `f8b9ab9aa6dd035a670b345524a554157fe0131189d15e2d76a65ec3245c4e51`.
  Все записи проверены. Binary/source JARs и APKs сохранены отдельно в
  `E:/r12-c05-maven-notices/` с hashes в receipts.

Initial wrong JDK path, network resets, ошибочное чтение gzip через zlib и seed
без explicit worktree roots сохранены как неудачные попытки. Итоговые команды
прошли с правильными inputs; недоступный неиспользованный Tink Maven POM path
не объявлен полученным. Upstream copyright/license тексты не переписаны.

Root utls license, полная совместимость лицензий, corresponding source,
остальные native/file-level obligations, installed privacy и final candidate/
device/SCM/origin acceptance остаются OPEN. Windows bundle не пересобирался.
Push, merge, deploy, production signing, публикация и новый candidate не выполнялись.
Rollback — scoped client commit; прежние пакеты и evidence сохранены.

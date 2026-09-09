# C05 — локальные APK/EXE: состав, notices и dependency scan

Дата: 2026-09-06. Статус: **active / I3 / PARTIALLY_FIXED**.
Продолжение [Core remediation](EXECUTION-C05.md) и
[client binding](EXECUTION-C05-BINDING.md).

Client: `7a8fd55f77d18982e71b39060371dacf4dfa1594`. Core: `8dc57a830bd1487389dd1b7c9190f094c31e13bc`.
[Reference receipt](evidence/c05-package-audit.json) закрепляет **Git blob**
client receipt и implementation files. Полные inventories, предыдущие пакеты,
новые пакеты, module notices и scanner responses сохранены в
`E:/r12-c05-package-artifacts/`; размеры и SHA доступны через client receipt.

## Исправления

1. `packages/app_shell/pubspec.yaml` включает уже существующий
   `assets/fonts/OFL.txt`. До исправления шрифты Golos были внутри APK и
   Windows bundle, а OFL отсутствовал. После исправления точные bytes OFL
   присутствуют во всех четырёх APK и Windows bundle.
2. CMake направляет `pokrov_activation_protocol_test.exe` в отдельную
   `build/windows/x64/tests/Release/`. Раньше тест попадал в runner Release
   рядом с приложением; release builder копирует эту папку целиком. Новая
   сборка сохраняет CTest, но не помещает test EXE в bundle. Старое местоположение
   очищено точечным перемещением файла после сверки SHA; обе копии старого
   теста сохранены в baseline/retention evidence. Массового удаления не было.

## Проверки точных локальных пакетов

| Проверка | Результат и граница |
|---|---|
| Direct release-mode APK: universal, ARM64, ARMv7, x86_64 | **PASS**, четыре пакета; используется разрешённый внутренний Android Debug signer и loopback API define |
| APK contents | **PASS**: embedded Core SO точно совпадают с закреплённым AAR; ожидаемые 3 ABI в universal и один в split; OFL совпадает; DLL/EXE/PDB/LOG/MD/AAR entries отсутствуют |
| APK signature/manifest | **PASS** целостность v2 на universal, `1.2.0+4053`, не debuggable. **Не** production signing; signer — Android Debug |
| Windows release Flutter bundle | **PASS**, 300 файлов после исправления; exact Core/Cronet/OFL; test EXE/PDB/LIB/EXP не входят |
| Windows CTest Release | **PASS 8/8**, включая activation protocol по новому пути |
| Android и Windows `flutter analyze` | **PASS**, no issues |
| Client seed/docs/source logging | **PASS**: 151 production files + 4 negative logging fixtures, parity и release contracts. Это source/fixture checks, не installed runtime logs |
| Go module cache | **PASS** `go1.26.8 mod verify`; local replacements закреплены clean Core commit |

Windows bundle получен напрямую через Flutter. Он не является installer:
app-local VC runtime добавляет отдельный canonical release builder. Setup,
его embedded uninstaller, установка, SCM, TUN и clean-host replay здесь
не выполнялись. Предыдущий offline Win11 component lab остаётся на D05.

## Dependency и privacy inventory

- Для четырёх AAR SO получены binary CycloneDX SBOM, по **119 components**;
  существующий C05 DLL SBOM содержит **115**. Три ABI, реально входящие в APK,
  сверены по bytes; x86 есть только в AAR и не объявлен APK runtime proof.
- Собраны selected Android `directReleaseRuntimeClasspath` (**68 modules**)
  и Pub runtime graphs. [OSV querybatch](https://google.github.io/osv.dev/post-v1-querybatch/)
  вернул **0 advisory IDs** для **75 Pub + 63 Maven** public package/version
  queries без непотреблённой pagination. Local Core coordinate и четыре Flutter
  engine coordinates исключены и перечислены. Pub graph может содержать
  неактивные platform implementations; запрос не доказывает code reachability.
- Defined DEX package readback не содержит семи явно проверенных namespace
  patterns: Google Ads, Firebase Analytics, Facebook Ads, AppsFlyer, Adjust,
  AppMetrica и Yandex Metrica. Это bounded scan, не отсутствие всех tracking SDK
  или доказательство runtime privacy. Реальные manifest permissions сохранены.
- Сохранены PE imports **11 EXE/DLL**. Flutter engine, C/C++ и динамические
  imports не превращены в Go/Pub/Maven PASS.
- В union Go build-info — **128 module entries** с учётом replacements.
  У **127** найдены root notice files; **130** текстов сохранены в отдельном
  архиве с hashes. Это root inventory, не полный набор вложенных лицензий и
  не готовый распространяемый native notice bundle.
- У [закреплённого Psiphon utls](https://github.com/Psiphon-Labs/utls/tree/24497d415a8de0d11c20c3a47724fb88897ed725)
  root license отсутствует; module cache и upstream tree согласуются.
  Найденный nested `dicttls/LICENSE` не объявлен лицензией всего модуля.
- Поставляемый `libcronet.dll`: **8596992 bytes / `8ef1f8bb…d7a6f7`**;
  DLL из текущего Go module cache: **8593920 bytes / `104ee114…f6e63b3`**.
  Обе возвращают **143.0.7499.109** в отдельных процессах, фактический loaded
  path проверен. `.text` и другие секции различаются. Версия не доказывает
  одинаковые source/build/notices; engine не запускался для сети.

Ранее выполненный Go binary scan применим только к тем же exact Core bytes.
Он не запускался повторно ради нового PASS: девять residual advisory IDs,
module-fallback precision и пределы reachability остаются из предыдущего
Core отчёта. Новые APK/EXE inventories их не закрывают.

## Сохранённые ошибки и оставшиеся gates

Первый Gradle artifact collector получил variant ambiguity; исправленный
collector читает selected resolutionResult modules, не меняя зависимости.
После расширения Android current header docs validator потерял полный
candidate identifier; header исправлен на `pokrov-1.2.0-candidate.33`, и final
seed/docs прошли. Оба неудачных запуска сохранены.

C05 остаётся открыт до полного native/license/source покрытия, разбора
оставшихся advisories, exact candidate packaging и installed runtime privacy.
Публикация corresponding source не выполнена и не подменяется source hash.
Не выполнялись production signing, новый candidate, push/merge/deploy,
provider operations, physical Android, WARP, RU-origin или brain-origin.
Исходные retained release artifacts не изменены; rollback — предыдущие
source files и сохранённые before-packages, без удаления новых evidence.

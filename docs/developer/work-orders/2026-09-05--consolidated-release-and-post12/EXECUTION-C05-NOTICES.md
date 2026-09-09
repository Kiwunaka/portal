# C05 — Windows Cronet native graph и пакет notices

Дата: 2026-09-06. Статус: **active / I3 / PARTIALLY_FIXED**.
Продолжение [проверки происхождения DLL](EXECUTION-C05-CRONET.md).
[Reference receipt](evidence/c05-cronet-notices.json) закрепляет client commit,
Git blobs новых файлов и результаты проверок.
Client commit: `4a184b02b6bbdb06a3f9994f7e84e3f092eb718a`. Core `8dc57a8` и runtime bytes
остаются прежними. Новый release candidate не создавался.

## Результат

В Windows CMake Runtime install добавлен обязательный `libcronet.NOTICES.txt`
рядом с DLL. Файл содержит **28 секций / 158463 bytes**, SHA-256
`2c24f29748b438f85ad6ef44548395970a4a1d04b89e653e6a4a56601297e267`.
Manifest закрепляет его hash; seed проверяет путь, наличие и SHA. Git сохраняет
байты notice без EOL-нормализации; исключения whitespace ограничены только
этим файлом с исходными лицензионными текстами. Проверены staged blob и checkout
filter: оба побайтно совпадают с исходным notice.

Обычный CMake install с отдельным prefix создал **301-file local bundle**.
**Все 300 прежних файлов побайтно совпадают** с сохранённым C05 package audit
baseline; единственное добавление — notice. Core/Cronet hashes совпали,
test EXE/PDB/LIB/EXP не появились. Перед install проверено, что его destinations
и REMOVE_RECURSE для Flutter assets находятся внутри нового изолированного
prefix. Исходный CMake prefix восстановлен. Новая native/Flutter компиляция,
запуск приложения и VPN не выполнялись. Это packaging proof, не installer,
SCM, TUN, clean-host или runtime privacy acceptance.

## Граф и toolchain

Закреплённый GN **2287 / 07d3c6f4dc29** построил **1134 targets** из native
source gitlink `2be061b6`. У `//components/cronet:cronet` — **558 recursive
dependencies**, в generated link rule — **473 direct object/library inputs**.
GN input integrity: **259 tracked files** совпали с Git blobs; ещё шесть
inputs — локально сгенерированные файлы и marker полученного Clang.
Граф содержит **5958 source entries**, включая generated и build-time inputs;
это число не объявляется числом linked production source files.

Feature flags взяты из Windows x64 ветки upstream builder `82e1521`.
Использованы pinned Chromium Clang `llvmorg-22-init-8940-g4d4cb757-84` и
[официальный SDK NuGet 10.0.26100.4654](https://www.nuget.org/packages/Microsoft.Windows.SDK.CPP/10.0.26100.4654).
Локальный MSVC — **14.42.34433**. Реальные debugger DLL получены из
[Microsoft.Debugging.Platform.DbgEng 20260109.1235.0](https://www.nuget.org/packages/Microsoft.Debugging.Platform.DbgEng/20260109.1235.0).
Toolchain настроен через отдельный каталог и штатный Chromium toolchain JSON;
VC/DIA junctions указывают на имеющийся Visual Studio. Системный SDK,
registry и Visual Studio installation не менялись.
Это локальная реконструкция графа, **не** attestation исходной upstream build
environment и не source-to-binary reproducibility. Generated runtime_deps с
debugger DLL также не является readback состава уже поставляемого asset.

## Найденные и устранённые пробелы notices

Сокращённый NaiveProxy source archive содержит исходники Perfetto, Protobuf и
compiler-rt, но import filter не включил их корневые license files. Они есть
в зависимостях и direct link inputs; проверка только README.chromium их пропускала.

- **Protobuf:** все **682** локальных файла совпали с Chromium
  `143.0.7499.109` subtree. Его README закрепляет **32.0**, revision
  `4fbd1111a292d04746c732573025e3251de0bb9c`; BSD license восстановлен из того же tag.
- **Perfetto:** **7687** файлов совпали с pinned `ac7792a0`; **6** изменений
  NaiveProxy сохранены отдельно — GN integration и Linux thread-name condition.
  License headers не изменены. Восстановлен upstream Apache license.
- **compiler-rt:** два headers совпали с `08611c39`; `atomic.c` комментирует
  upstream static assertion и сохраняет SPDX Apache-with-LLVM-exception.
  Сохранён diff и полный upstream LLVM license, без утверждения source equality.
- Дополнительно включены nested `utf8_range` MIT, Fiat-Crypto authors,
  libc++abi и BSD attribution OpenBSD в Perfetto `intrusive_tree.cc`.
  Последний найден bounded scan лицензионных заголовков, а не в root LICENSE.

Notice объединяет установленный native OSS scope и supporting headers.
NASM исключён как build executable, отсутствующий в root DLL link inputs.
Это не декларация полного лицензионного покрытия клиента: другие Core,
Android, Flutter и Microsoft runtime материалы, Psiphon utls license gap,
remaining advisory reachability и installed privacy остаются открыты.
Corresponding source не опубликован; прежний полный C05 gate не изменён.

## Проверки и сохранённые ошибки

GN сначала не обнаружил Visual Studio в нестандартном x86 Program Files пути;
следующий запуск показал отсутствующие pinned SDK/Clang. После получения
реальных пакетов local graph построен. Первый `gn desc` выбрал WindowsApps
Python stub; explicit interpreter дал успешные JSON graph readbacks. Логи
первых ошибок сохранены. Первый client seed отверг новое `eol=lf` правило;
notice переведён на byte-preserving `-text`, без расширения EOL allowlist.
Final client seed/docs/source/fixture gate — **PASS**. Platform — **33 docs
tests PASS**, context audit PASS, package validator PASS: 13 imports, 83 R12,
378 legacy IDs и 197 local links. Performance collector в seed — fixture,
а не новое измерение CPU на устройстве.

Команды client install/seed и platform docs/context/package checks, exit codes
и log SHA сохранены в reference receipt. Полные graphs, upstream tree metadata,
fork diffs, toolchain download/extraction hashes, notice assembly и bundle
inventory находятся в `E:/r12-c05-cronet-graph/` и закреплены через client receipt.

Push/merge/deploy, production signing, provider/payment operations,
physical Android, SCM/TUN и named-origin checks не выполнялись.
Rollback — scoped client packaging/metadata commit; старый 300-file baseline
и все новые evidence сохранены. Core/client release artifacts не переписаны.

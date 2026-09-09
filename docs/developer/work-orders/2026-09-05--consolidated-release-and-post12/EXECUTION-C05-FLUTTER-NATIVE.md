# R12-C05 — Flutter, Windows plugins и встроенный Wintun

Дата: 2026-09-06. **I3 / PARTIALLY_FIXED**; полный C05 открыт.
Core `8dc57a830bd1487389dd1b7c9190f094c31e13bc`; клиент до изменения
`7bef147c14beea9b8a45a48fedbc22f5205f7f53`.
Продолжение [file-header notices](EXECUTION-C05-FILE-HEADERS.md).
[Receipt, hashes и команды](evidence/c05-flutter-native.json).
Client commit: `509190b19fb08543c9a7fcf9e750c14b6c8429c9`.

## Подтверждённая поставка Flutter

Из текущих package configs и license inputs побайтно восстановлен штатный
`NOTICES.Z`: 1621 разный текст для Android, 1624 для Windows, в обоих наборах
1594 блока sky_engine. Имена и тексты совпали, без подмены generated notices
ручным списком. SDK root license также присутствует; отсутствие отдельного
LICENSE у SDK subpackage не объявлено отсутствием лицензии у SDK.

Получены официальные архивы engine `1527ae0ec577a4ef50e65f6fefcfc1326707d9bf`.
Длина и GCS MD5 проверены, SHA-256 сохранены. Sky_engine LICENSE совпал с SDK;
Windows Flutter DLL совпала с архивом и bundle. Три Android SO совпали с
официальными файлами после воспроизведения `llvm-strip --strip-unneeded`
из NDK 28.2.13676358; обе поставки каждого ABI проверены. Embedding JAR совпал
с выбранным Gradle cache input; это не доказательство DEX reachability.
Три framework/license-collector файла сверены с official framework commit
`f6ff1529fd6d8af5f706051d9251ac9231c83407`, с явно записанными line endings.

Для шести Windows plugins проверены 49 файлов Windows-каталогов и root
licenses: все совпали с pub.dev archives и SHA-256 из lock. Их license bodies
есть в Flutter notices. Шесть DLL имеют ожидаемые imports Flutter engine;
точные hashes записаны. Эта проверка не утверждает native build reproduction.

## Исправленный пробел Wintun

В Windows Core найден ровно один полный byte range DLL Wintun 0.14.1 amd64:
427552 bytes, SHA-256
`e5da8447dc2c320edc0fc52fa01885c103de8c118481f683643cacc3220dafce`.
Он совпал с module input и DLL из [официальной поставки](https://www.wintun.net/).
Проверена подпись WireGuard LLC (`Valid`) и опубликованный SHA-256 ZIP.

У этого бинарника отдельные **Prebuilt Binaries License** terms; wrapper MIT
и source GPL-2.0 не заменяют их. Текст 5431 bytes теперь включён в общий asset
без изменения bytes. Прежние 659001 bytes и 185 текстов сохранены как prefix;
новый asset — 664866 bytes / 186 текстов, SHA-256
`8075f4b06ef00fc4b7bf50e05905a4908d63619d73a1571aaf74c5e3b62314e8`.

Для тринадцати имён функций, заданных в wrapper, найдены соответствующие typedefs
в официальном header. Wrapper использует memory loader. Эти source facts
не являются решением о совместимости API-use/redistribution с условиями
лицензии. Такое решение остаётся открытым; runtime для него не менялся.

## SBOM и проверки

Native supplement в CycloneDX 1.6 содержит 12 компонентов: четыре Flutter
engine binaries, шесть Windows plugin DLLs, Wintun и его Core parent.
Схема проверена; семь связей зависимости ограничены установленными imports
и embedding. Это дополнение к прежним Go/Pub/Maven inventories, не полный
application SBOM и не blanket license clearance.

- **PASS:** четыре новые Direct APK содержат все 186 notice bodies и прежние
  Core/Flutter SOs; generated Flutter notices не изменились. Android Debug signer.
- **PASS:** Windows bundle, 302 файла; изменён только общий notices asset,
  остальные 301 файл совпали. Original CMake install prefix восстановлен точно.
- **PASS:** четыре preexisting generated registrants сохранились побайтно.
- **PASS:** client seed/docs и staged diff checks; Git asset сохранил все
  186 body hashes. Native SBOM имеет отдельные hashes Git blob и исходного
  артефакта из-за нормализации line endings; parsed documents совпадают.
  Performance collector внутри seed использует fixture.

Полные данные и официальные inputs сохранены в `E:/r12-c05-flutter-native/`.
Архив evidence: 1300530 bytes, 62 файла, SHA-256
`7dc6db8ca91076eb3e6f5e0c9dea5a0b9d37d453bfab3362c8854a5600d3d3bf`;
hash каждой записи проверен. Binary archives и пакеты сохранены отдельно.
Первоначальные ошибки проверки тоже сохранены: предположение об одинаковых
notice sets на двух платформах; чтение только первого GCS hash header;
newline conversion при записи распакованного текста; HTTP 403 от schema host.
Итоговые проверки используют отдельные platform sets, все headers, raw bytes
и schema files из официального specification repository.

Root utls license, остальные native/Maven/file-level obligations, corresponding
source, native advisory/reachability, installed privacy и final candidate/device/
origin/SCM acceptance остаются OPEN. Поставка с app-local VC runtime и installer
здесь не проверялась. Push, merge, deploy, production signing и новый candidate
не выполнялись. Source rollback — scoped client commit; старые артефакты сохранены.

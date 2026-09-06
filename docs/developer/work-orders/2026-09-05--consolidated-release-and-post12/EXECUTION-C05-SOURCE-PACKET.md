# R12-C05 — пакет исходников Core и отдельное Android Cronet source binding

Дата: 2026-09-06. **SOURCE_PREPARATION_ONLY / I3 / PARTIALLY_FIXED**.
Core `8dc57a830bd1487389dd1b7c9190f094c31e13bc`, consumer client
`b0f4374c8ac00840aaa52c170121ba310133bef0`; runtime bytes прежние.
Продолжение [module authentication](EXECUTION-C05-MODULE-AUTH.md).
[Полный receipt и SHA-256](evidence/c05-source-packet.json).

## Подготовленная поставка

Архив `E:/r12-c05-source-packet/pokrov-core-8dc57a8-source-review-compact.zip`:
350839950 bytes, SHA-256
`2cb77e211a8bec3f303a67282befd231a5f7c84d2c712b80771a7a063f232d59`.
Все 3670 записей проверены по manifest hashes.

- 3161 точный Git blob Core: исходники, пять local replacements, scripts,
  tests, build manifests, licenses и docs. История и untracked files не включены.
- 123 аутентифицированные версии внешних modules: 492 файла zip/mod/info/ziphash.
  Go archives сохраняют исходную структуру; Cronet .a внутри них явно остаются
  prebuilt binary inputs, а не объявляются исходниками native implementation.
- Два разных naiveproxy source archives для Android и Windows, отдельный
  полный Windows wrapper/build source, инструкции и проверочная metadata.

Сначала `exact_git_snapshot` выбрал и проверил ограниченный набор Git objects;
после credential-marker preflight они материализованы через verified cat-file
batch. Единственное совпадение — строка SSH parser prefix, без ключевого тела.
Это целевая проверка, не полный secret/history/publication audit.

Первый архив сохранял также распакованные Go modules, появившиеся во время
проверки. Compact archive исключает только эти производные дубли и locks;
492 оригинальных module-cache inputs сохранены. Первый архив не удалён и
указан в receipt. Рабочие caches и source checkouts не очищались.

## Проверка пригодности исходников

Из materialized Core snapshot выполнены пять исходных `go list -deps` команд
с artifact-specific tags/GOOS/GOARCH/CGO, Go 1.26.8 и `-mod=readonly`.
GOPROXY/GOSUMDB отключены только для этого offline check уже независимо
аутентифицированных archives; глобальное окружение и production не менялись.

Все команды exit 0. Совпали ImportPath, выбранные source-file lists, module
versions/sums и replacements: Android 1022/1020/1020/1023 packages, Windows 1013.
3161 source blob после проверки неизменен. Это доказывает разрешимость текущих
runtime graphs из пакета, но не полную offline build: compiler/SDK/gomobile
bootstrap и native toolchain/PGO inputs остаются отдельными prerequisites.
Новые builds, runtime applications, device или privacy tests не запускались.

## Android Cronet

Четыре bound `libcronet.a` побайтно совпали с Git blobs
[upstream library commit f21660be](https://github.com/SagerNet/cronet-go/tree/f21660bef13fa6be033e335d64ef55433ce4b8f7).
И этот commit, и wrapper `dc1cda1f` объявляют gitlink
[naiveproxy 30f3a568](https://github.com/SagerNet/naiveproxy/tree/30f3a5689ac20ba1b87c1ce58f66d3aaa8b2cfe5).
Полный source archive: 30561 exact Git blob matches, ещё 30 zstd project files
совпали после CRLF→LF normalization; missing/extra/unexplained differences — 0.

Windows сохраняет прежний native `2be061b6`. Дополнительно получены и проверены
все 138 wrapper/build files release commit `82e15210`. Оба native дерева имеют
Chromium 143.0.7499.109, но разные commits. Source tuple не объединяется по
одной строке версии. Build cache provenance и native byte reproduction не
доказаны ни этим архивом, ни совпадением library blob с upstream.

## Открытые условия

Это внутренний Core source packet. Финальная corresponding-source assessment,
source-to-binary native reproduction, utls root license и прочие native/file-header
obligations открыты. В клиентском репозитории нет принятой root license;
OSS-план содержит предпочтение GPL-3.0-or-later и отдельное brand decision,
которые не подменены автоматическим relicensing или export клиентского кода.

Android canonical release audit обновлён с отдельным source binding;
client docs/evidence commit `64a26c3` (runtime consumer source выше сохранён).
Client seed/docs и platform docs/context/package/diff checks сохранены в receipt.
Installed privacy, exact candidate/device/SCM/origin acceptance остаются OPEN.
Push, merge, deploy, signing, публикация и новый candidate не выполнялись.

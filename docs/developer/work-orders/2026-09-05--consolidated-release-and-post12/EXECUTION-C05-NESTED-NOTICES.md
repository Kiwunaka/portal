# R12-C05 — вложенные Go notices и точный Psiphon utls snapshot

Дата: 2026-09-06. **I3 / PARTIALLY_FIXED**, полный C05 открыт.
Client: `b0f4374c8ac00840aaa52c170121ba310133bef0`.
Core прежний: `8dc57a830bd1487389dd1b7c9190f094c31e13bc`.
Продолжение [root Go notice packaging](EXECUTION-C05-GO-NOTICES.md).
Точные команды, артефакты, source и hashes:
[evidence/c05-nested-notices.json](evidence/c05-nested-notices.json).

## Исправленная поставка

В существующий общий asset добавлены 28 license/patent текстов из вложенных
каталогов выбранных Go packages. Среди них — отдельные dicttls, freelru,
Psiphon crypto/monotime/QUIC/regen/NTLM, compress и Go vendor notices.
Все прежние 145 текстов и их offsets сохранены; итог — 173 побайтных текста.
Asset: 637092 bytes,
SHA-256 `17034f0a50bbdc6480c660908885cf7d1ad185e1813e23b2dc6d2d25cde03355`.
Runtime manifest hash и canonical bootstrap/host readiness обновлены.

Основание выбора — пять `go list -deps -json` graphs с Go 1.26.8:
четыре Android ABI и Windows amd64. Tags, GOOS, GOARCH, CGO и GOARM взяты
из записанного build-info; roots соответствуют штатным build scripts.
Затем build-info повторно прочитан из текущей DLL и четырёх SO, побайтно
совпавших с pinned AAR. Все module/settings lines совпали с исходными записями.

Графы содержат 1022/1020/1020/1023 Android и 1013 Windows packages; все 128
записанных Go modules представлены, неизвестных module paths нет.
Сборщик рассматривает ancestors каталогов packages и явно embedded files
в пределах соответствующего module/Core/Go root. `go mod verify` — PASS.
Это source-dependency selection, не symbol-level proof и не полный аудит
native includes или license headers. Включение Go `internal/boring/LICENSE`
не доказывает, что optional BoringSSL implementation вошёл в библиотеку.

Первый filename scan включил `psiphon/notice.go`; это исходник, он исключён
до сборки asset. У Core `common/ja3/LICENSE` рабочая копия имела CRLF;
первый append остановился до записи. В asset включён точный Git blob после
проверки LF-normalized equality. Workspace и delivered hashes сохранены
отдельно. Добавлено 79569 bytes самих текстов; 79598 в первичном inventory
отличались на 29 CRLF bytes этого файла. Лицензионный текст не редактировался.

## Psiphon utls

GitHub readback проверил [точный upstream snapshot](https://github.com/Psiphon-Labs/utls/tree/24497d415a8de0d11c20c3a47724fb88897ed725).
Recursive tree не усечён: 311 entries, 298 blobs. Все 298 файлов Go module cache
совпали с Git blob SHA-1 и сохранены в comparison inventory по SHA-256;
пропущенных, изменённых или лишних файлов нет. Единственный license-like
путь — `dicttls/LICENSE`; root license отсутствует и в upstream snapshot.

Этот BSD-текст добавлен для dicttls. Он не подменяет отсутствующую root license
всего utls. Отдельные source headers ссылаются на отсутствующий LICENSE;
полная правовая оценка и file-level coverage остаются OPEN.
Первый urllib запрос завершился TLS reset; штатный `gh api` GET с проверкой
TLS дал результаты. Внешние issue, письма или запросы владельцам не отправлялись.

## Проверки и границы

- PASS: четыре Direct release-mode APK; все 173 текста, OFL и bound Core SOs.
  `apksigner verify --print-certs` подтверждает внутренний Android Debug signer.
- PASS: Windows release-mode bundle, 302 файла. Изменён только общий notice;
  остальные 301 файл совпали с предыдущим bundle. App EXE — `NotSigned`, test
  EXE отсутствует. Core/Cronet/OFL/Cronet notice совпали с inputs.
- PASS: seed и client docs, source package graphs и fresh build-info readback;
  все 173 body hashes совпали также в staged Git blob.
- PASS: platform docs/context/package и diff checks — результаты в receipt.
  Performance collector внутри seed остаётся fixture, не physical measurement.

Оба пакета используют loopback API. Новый Windows install prefix был отдельным;
после сборки cache восстановлен в штатный runner/Release. Четыре прежних
generated registrants сохранены побайтно и не staged. `artifacts/releases/**`
не менялся. Пакеты и evidence сохранены отдельно в `E:/r12-c05-utls-review/`.

Root utls license, прочие native/file-header obligations, corresponding-source
delivery, residual advisory reachability, installed privacy, physical Android,
Windows installer/SCM/TUN и origin/candidate acceptance остаются OPEN.
Push, merge, deploy, production signing и новый release candidate не выполнялись.
Source rollback — scoped revert client commit; прежние binaries/evidence сохранены.

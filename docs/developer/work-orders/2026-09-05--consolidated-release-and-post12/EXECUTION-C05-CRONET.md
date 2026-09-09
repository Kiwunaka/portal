# C05 — происхождение закреплённого Windows Cronet

Дата: 2026-09-06. Статус: **active / I3 / PARTIALLY_FIXED**.
Продолжение [package audit](EXECUTION-C05-PACKAGES.md).
[Reference receipt](evidence/c05-cronet-origin.json) закрепляет client Git blob
и локальные проверки. Client commit: `47c6053cfc29874f9c72dafe8dd710055617880f`.
Core остаётся `8dc57a8`; runtime bytes не менялись.

## Установленная цепочка

- Закреплённая `libcronet.dll`, **8596992 bytes**, SHA-256
  `8ef1f8bbde77f954af1ae47bee1819ac8dc2354bb0e1d4baba3dad9e58d7a6f7`,
  побайтно совпала со скачанным asset `libcronet-windows-amd64.dll` из
  [официального релиза 143.0.7499.109-2](https://github.com/SagerNet/cronet-go/releases/tag/143.0.7499.109-2).
- GitHub release digest согласуется с локальным SHA. Тег указывает на commit
  `82e152101769e4655794c3c33518be224d7e9b9e`; его gitlink `naiveproxy` —
  `2be061b6c2e9b316f75ec1e329e345406cd4c62d` в SagerNet/naiveproxy.
- [Upstream workflow run](https://github.com/SagerNet/cronet-go/actions/runs/22617992901)
  имеет тот же head и conclusion `success`. Сохранён workflow с native cache
  и packaging logic. Этот статус не заменяет actual cache/build logs,
  attestation или воспроизводимую source-to-binary сборку.
- Сохранён native source ZIP (**69284854 bytes**, SHA-256
  `1c0a128aaff7ac8b5e80f2b7d06c273261de1b6dc2b0692f1d7c3855e6703096`).
  Из **30591** файлов **30561** совпадают с Git blobs напрямую, **30** —
  после CRLF→LF. Все 30 относятся к старым zstd Windows project/script files.
  Необъяснённых несовпадений нет. Оригинальный ZIP сохранён; два symlink
  entries удержаны как текст, поэтому extraction не объявлен build-ready checkout.

Client manifest теперь ссылается на проверенное происхождение. Он отдельно
указывает `source_reproducibility: NOT_ESTABLISHED` и `complete_notices: OPEN`.
Windows readiness обновлён; прежний package audit сохранён как датированное
наблюдение до reconciliation. DLL из Go module cache имеет другую identity
и не используется как substitute provenance для поставляемой Windows DLL.

## License review material

В exact native source проверены **36 README.chromium**. Четыре не содержат
License File: internal build metadata и три license-helper test fixtures.
Все явно указанные license files существуют. Архив для ревью содержит
**69 файлов** — metadata, указанные license files и две корневые лицензии.
Он находится в `E:/r12-c05-cronet-provenance/native-source-license-review.zip`;
SHA и полная metadata inventory закреплены через client receipt.

Это inventory исходного дерева. В нём есть Apple/Android/build/test записи;
поле upstream `Shipped` не доказывает, что компонент вошёл в Windows target
`cronet`. Архив не добавлен в distributable как готовый notice bundle.
Точный GN dependency graph, native/toolchain license coverage и packaged
notices остаются открыты. В полном source tree есть `src/get-clang.sh`,
который получает GN/toolchain/PGO; отсутствие файла в ранней неполной
распаковке не является upstream defect. Bootstrap и native rebuild не запускались.

## Проверки и границы

Проверены byte identity DLL, SHA исходного архива, полная сверка archive/Git
blob entries, наличие declared licenses, bytes 69 review entries, hashes
33 retained artifacts и согласованность manifest→receipt. Scoped secret-pattern
scan и отсутствие runtime/release artifact delta — PASS.
Client `validate-seed.ps1` (включая docs/source/fixture contracts) — PASS.
Platform: 33 docs tests, context audit и package validator (13 imports, 83 R12,
378 legacy IDs, 194 local links) — PASS. Команды, logs и SHA сохранены в
reference receipt. Новая сборка продукта для docs/config изменений не нужна.

C05 остаётся открыт: complete native/Flutter/C++ notices, Psiphon utls root
license, remaining advisory reachability и installed runtime privacy не закрыты.
Corresponding source не опубликован. Новый candidate, production signing,
installer, physical Android/SCM/TUN/origin проверки, push/merge/deploy не выполнялись.
Rollback этого изменения — scoped metadata/docs commit; runtime binding прежний.

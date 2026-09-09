# C05: dependency review и исправление SSH deadlock

Дата: 2026-09-06. Статус: **active / I3 / PARTIALLY_FIXED**.
Это локальная проверка компонентов; C05 и общий план не закрыты.

Core source: `8dc57a830bd1487389dd1b7c9190f094c31e13bc`,
`E:/r12core-implementation`. Команды, SHA-256, исходные finding records,
неудачные попытки и границы находятся в [evidence](evidence/c05-core-dependencies.json).
Каноническое требование к toolchain обновлено в Core `docs/release.md`.

## Исправление

На прежних D05 DLL и четырёх Android ABI `govulncheck` дал 11 advisory ID.
Source scan с Windows release tags подтвердил пути из runtime к
`x/crypto/ssh.NewClientConn` для `GO-2026-6354` и `GO-2026-6355`.
Исправленная `x/crypto v0.56.0` требует Go 1.26. Закреплены:

- Go `1.26.8` в обоих модулях, release config, build scripts и CI;
- `x/crypto v0.56.0` в обоих модулях;
- `tfo-go/v2 v2.3.3`: старая `2.3.1` не линковалась с новым `internal/poll`.

Пробный переход сначала проверен через отдельный modfile. Полный Core gate
после перехода выявил ещё одну несовместимость: unsafe mirror Psiphon TLS
не соответствовал `crypto/tls.ConnectionState`. Поле `HelloRetryRequest`
теперь стоит перед exporter closure и заполняется из факта HRR. Structural
assert сохранён. Новый тест в постоянном gate выполняет TLS 1.3 handshake
с HRR и без, проверяет обе стороны, unsafe conversion и exporter closure.

Go 1.26 игнорирует custom random reader при ECDH key generation. Поэтому старые
тесты с записанными packet transcripts прошли только с **тестовым**
`GODEBUG=cryptocustomrand=1`; default live handshake и conversion прошли без
этого флага. Production-настройки случайности не менялись.
Основание: [Go 1.26](https://go.dev/doc/go1.26).

## Новые локальные bytes

| Артефакт | Размер | SHA-256 |
|---|---:|---|
| Core DLL | 55449088 | `c679ba5af42939acbc8c6f44af59b4608f6a76c99e0d444cfa4bcc825bcc8e68` |
| Core AAR | 107483275 | `bc5ef7ece6ba6c138589307a7c5e30be32ec01cdd396e23dfdb8840011148b29` |

Каталоги `E:/r12-c05-artifacts/windows-{a,b}` и `android-{a,b}`:
**PASS_BYTE_IDENTICAL_TWO_BUILDS**. Сравнены также Windows header/Cronet и
Android sources JAR. DLL содержит 15 обязательных exports; AAR — четыре ABI.
SHA pinned Cronet не изменился.

Builds выполнялись до commit на тех же implementation bytes; сохранён
precommit SHA snapshot. После него изменилось только пояснение в
`docs/release.md`. Reproducibility receipt создан после commit. Метка helper
`UNSIGNED_CI_BUILD_EVIDENCE` здесь обозначает локальные сборки: hosted CI не
запускался, workflow/run/runner fields пусты.

## Проверки и трактовка сканера

- `scripts/test.ps1` с Go 1.26.8: **PASS**, включая новый TLS conversion test,
  full root module и embedded AWG/event/TLS packages.
- Default TLS ConnectionState 1.2/1.3 и direct/HRR conversion: **PASS**.
- `go test -race ./internal/observability ./v2/hcore`: observability **PASS**;
  hcore сообщает `no test files`, не отдельный runtime PASS.
- Client helper на новой DLL: **100 proxy-only start/stop cycles PASS**.
  Системные маршруты и TUN не менялись.
- Новые DLL + четыре SO: два исправленных SSH ID отсутствуют.
  Во всех пяти остаётся девять advisory ID.
- Source scan трёх runtime packages с Windows release tags: 14 records,
  девять ID, **0 function/call-path findings**. Это ограниченный scope.

**Уточнение binary precision:** `govulncheck -mode extract` вернул 0 symbols
на всех пяти stripped библиотеках. В этой ветке scanner v1.7.0 подставляет
известные vulnerable symbols для модулей. Названия функций в JSON и поле
`symbol_findings` старого промежуточного summary не доказывают присутствие
функций в бинарнике. Финальный evidence называет их `symbol_finding_records`.
Это соответствует [ограничениям govulncheck](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck).

| Оставшиеся ID | Проверенное основание | Предел вывода |
|---|---|---|
| 5932, 6179, 6180, 5841 (префикс GO-2026-) | openpgp, sumdb, s2 отсутствуют в exact-tag source import graphs Windows amd64 и Android arm64 | Остальные ABI graphs отдельно не снимались; binary symbol proof отсутствует |
| 4316, 5774, 5775, 5777, 4503 | chi middleware/edwards25519 импортируются, но scoped source scan не нашёл vulnerable call paths | Не полный анализ reflection/unsafe/native entrypoints; IDs не подавлены |

## Лицензии и незакрытые требования

Новые source SBOM: 239 Core и 226 engine module components. Сканер не распознал
license evidence у 39/37 компонентов, включая local replacements. Binary SBOM
DLL содержит 115 module components; команда `bin` не прикрепляет licenses.
Source dependency list включает неиспользуемые модули и не равен списку linked libs.

При проверке 22 прежних предупреждений у 21 module directory найден root
license file. У Psiphon utls в module cache root license не найден; отдельно
есть `dicttls/LICENSE`, который не доказывает лицензию всего модуля. Лицензии
новых Go/x/crypto/tfo-go найдены и hash-bound. Это инвентаризация, не license
clearance и не доказательство полноты notices конечного пакета.

Первый full gate упал на TLS structural assert; это исправлено. Один повтор
захватил generated gomobile `build/` и упал на cgo glue. Каталог сохранён в
`E:/r12-c05-artifacts/retained-gomobile-build`; после завершения сборок и его
переноса полный gate прошёл. Ошибки выбора test cwd, golden transcripts и
старого scanner/toolchain также сохранены, не переклассифицированы в PASS.

Клиент пока связан с прежними D05 bytes от Core `94dd310`; новые DLL/AAR
находятся только в каталоге проверки. Требуются binding/backtests, final
APK/installer EXE scan, native Cronet/C++/Flutter inventory, полнота notices,
остаточная reachability и runtime privacy на финальных пакетах. Старый
Win11 lab остаётся привязанным к D05; pending manual SCM не стал proof для C05.
Новых device/TUN/SCM/RU-origin/brain-origin, подписания, кандидата, публикации,
push, merge, deploy или provider operations в этом этапе нет.

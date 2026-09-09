# R12-C05 — статический разбор девяти advisory

Дата: 2026-09-06. **I3 / PARTIALLY_FIXED**; полный C05 открыт.
Core `8dc57a830bd1487389dd1b7c9190f094c31e13bc`, client
`b0f4374c8ac00840aaa52c170121ba310133bef0`; runtime bytes прежние.
Продолжение [nested notices](EXECUTION-C05-NESTED-NOTICES.md).
[Результаты по каждому ID](evidence/c05-triage-results.json) и
[receipt с SHA-256 исходных данных и проверками](evidence/c05-triage.json).

## Результаты

| Advisory | Вердикт / confidence | Основание и следующий шаг |
| --- | --- | --- |
| [GO-2026-5932](https://pkg.go.dev/vuln/GO-2026-5932) | not_actionable / high | Все семь affected OpenPGP packages отсутствуют во всех пяти графах. Сохранить вывод для этого tuple. |
| [GO-2026-5841](https://pkg.go.dev/vuln/GO-2026-5841) | not_actionable / high | S2 отсутствует во всех графах; приложение не принимает dictionary через NewDict. Пересмотреть при смене графа. |
| [GO-2026-6179](https://pkg.go.dev/vuln/GO-2026-6179) | needs_review / medium, rank 1 | Runtime sumdb отсутствует, текущий Go исправлен. Не установлена независимая аутентификация прежнего кеша; advisory требует только malicious GOPROXY. |
| [GO-2026-6180](https://pkg.go.dev/vuln/GO-2026-6180) | needs_review / medium, rank 2 | Тот же пробел истории кеша; дополнительно требуется coordinated malicious GOSUMDB. |
| [GO-2026-4316](https://pkg.go.dev/vuln/GO-2026-4316) | not_actionable / high | RedirectSlashes не зарегистрирован и не вызывается в выбранных исходниках. |
| [GO-2026-5774](https://pkg.go.dev/vuln/GO-2026-5774) | not_actionable / high | RealIP не зарегистрирован; HTTP headers не попадают в эту функцию. |
| [GO-2026-5775](https://pkg.go.dev/vuln/GO-2026-5775) | not_actionable / high | RealIP не вызывается, включая альтернативные настройки Clash listener/secret. |
| [GO-2026-5777](https://pkg.go.dev/vuln/GO-2026-5777) | not_actionable / high | Та же независимая disposition для отдельного входного ID; исходные записи сохранены. |
| [GO-2026-4503](https://pkg.go.dev/vuln/GO-2026-4503) | not_actionable / high | Point.MultiScalarMult не вызывается. Единственный внешний consumer использует локальные SetBytes/BytesMontgomery и возвращает byte array. |

## Покрытие и граница доверия

Пять source graphs из предыдущего среза соответствуют четырём Android ABI
и Windows amd64 с записанными tags/CGO/GOOS/GOARCH/GOARM и Go 1.26.8.
Они связаны с прежними AAR/DLL через сохранённый fresh build-info readback;
все 128 module records представлены. Архив сохраняет graphs и их hashes.

6488 выбранных Go/Cgo files содержат восемь совпадений трёх affected symbols:
только определения, комментарии и panic text. Выбранные native files не имеют
ссылок на эти имена. Полный inventory содержит 6751 source file и SHA-256.
Это целевой статический анализ девяти claims, не полный поиск уязвимостей.

Clash router собирается явными registrations в
`engine/sing-box/experimental/clashapi/server.go:65-145`; middleware импортирован
в `api_meta.go:16-29` для Profiler. Ни штатные HTTP paths, ни изменение secret
не подключают RealIP/RedirectSlashes. Вывод основан на отсутствии регистрации,
а не на предположении о доверенных headers или обязательной аутентификации.

В Psiphon `psiphon/common/inproxy/session.go:189-207` Point остаётся локальным:
SetBytes error немедленно возвращается, успешный BytesMontgomery копируется
в фиксированный массив. Point не передаётся в public adapter или reflection.
Уязвимая MultiScalarMult присутствует в dependency source, но этот путь её
не вызывает. Закрытые mobile/desktop adapters не предоставляют произвольного
вызова Go functions по пользовательскому имени.

Недоверенные network inputs остаются частью runtime threat model. В семи
случаях именно путь через affected API отсутствует в текущих библиотеках.
Это не оценка других версий, build flags, внешних серверов или будущих callers.
Resolved SECURITY.md задаёт current-major support и запрет раскрытия secrets;
продуктовая граница установлена также по Core contract и build/adapter source.

## Два открытых sumdb claims

Build scripts и manifests закрепляют Go 1.26.8, новее advisory fix 1.26.6.
`cmd/go` и affected `golang.org/x/mod/sumdb` packages не входят в runtime graphs.
Однако исправленный downloader может повторно использовать старый кеш.
Предыдущий `go mod verify` сверяет локальные записи; он не устанавливает,
каким downloader и из какого authenticated источника они были получены.

Минимальная следующая проверка: в отдельном пустом module/checksum cache
исправленным downloader независимо аутентифицировать использованные hashes
и сравнить их с текущими selected sources. Текущие go.sum, кеш, binaries и
receipts сохраняются. Команды удаления из advisory не выполнялись.
Доказательств malicious proxy или подменённых modules нет; подтверждённой
эксплуатации эти два needs_review не означают.

## Проверки и ограничения

Assessment завершён до записи repository docs. Tests, builds, applications,
PoCs и runtime validation в нём не запускались. Проверки docs/context/package
после assessment относятся только к оформлению evidence; exact команды и
результаты записаны в receipt.

Исходный scanner имел module precision и ноль extracted symbols. Все его
девять ID сохранены; static dispositions не переписывают scanner output в PASS.
Полный C05 licensing/source delivery/installed privacy, physical Android,
Windows SCM/TUN, независимые origins и exact candidate acceptance остаются OPEN.
Client/Core source и release artifacts не менялись. Push, merge, deploy,
production signing и создание нового release candidate не выполнялись.

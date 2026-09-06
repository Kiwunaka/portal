# R12-C05 — независимая аутентификация выбранных Go modules

Дата: 2026-09-06. **PASS selected module authenticity**;
полный **C05 / I3 / PARTIALLY_FIXED**.
Core `8dc57a830bd1487389dd1b7c9190f094c31e13bc`, client
`b0f4374c8ac00840aaa52c170121ba310133bef0`; source и runtime bytes прежние.
Продолжение [статического triage](EXECUTION-C05-TRIAGE.md).
[Receipt, команды, сравнения и SHA-256](evidence/c05-module-auth.json).

## Результат

123 внешних модуля из объединения пяти графов сборки независимо загружены
исправленным Go 1.26.8. Для каждого совпали module Sum и GoModSum:
246 совпадений, ноль расхождений. Все 123 свежих authenticated sumdb lookup
records содержат обе ожидаемые записи. Полное сравнение прежних и новых
module directories дало **16 868 побайтно совпавших файлов**, без пропусков,
дополнительных или изменённых файлов.

Повторно проверены SHA-256 всех 6751 файлов прежнего selected source inventory:
все неизменны. Core HEAD прежний, worktree чист. Пять локальных замен модулей
и main module принадлежат tracked Core source; они отдельно перечислены и
не выдаются за аутентифицированные через sumdb внешние downloads.

## Как выполнено

Рабочий каталог `E:/r12-c05-module-auth/work` создан пустым. Команда
`go mod download -json` получила 123 явных module@version из прежних graphs,
с учётом внешних replace destinations. Не использовались старые go.sum,
module/checksum cache или local vendor как источник скачанных данных.
Заданы отдельные GOMODCACHE/GOPATH/GOCACHE, `GOENV=off`, `GOWORK=off`,
`GOTOOLCHAIN=local`, пустые GOPRIVATE/GONOSUMDB/GONOPROXY/GOINSECURE/GOFLAGS.
Единственный GOPROXY — `https://proxy.golang.org`; GOSUMDB — `sum.golang.org`.
Команда завершилась с exit 0. Полный argv и окружение записаны в архиве receipt.

[Go Modules Reference](https://go.dev/ref/mod#authenticating) описывает
проверку загружаемых модулей через checksum database при отсутствии прежних
сумм. Здесь дополнительно сохранены свежие lookup/tile/state files и выполнено
сравнение файлов с кешем, соответствующим записанным artifact module sums.
Старый кеш и repository manifests не удалялись и не переписывались.

## Disposition двух оставшихся claims

| Advisory | До проверки | После проверки для текущего tuple |
| --- | --- | --- |
| [GO-2026-6179](https://pkg.go.dev/vuln/GO-2026-6179) | needs_review / medium, rank 1 | not_actionable / high: selected module sources совпадают со свежими authenticated bytes; runtime sumdb отсутствует, текущий downloader исправлен. |
| [GO-2026-6180](https://pkg.go.dev/vuln/GO-2026-6180) | needs_review / medium, rank 2 | not_actionable / high: тот же полный remote-module comparison закрывает пробел проверки текущих исходников. |

Прежние triage JSON, семь остальных dispositions и исходные scanner records
не переписаны. Этот срез добавляет evidence и меняет вывод только для двух
claims. История событий приобретения кеша не восстановлена; вместо неё
независимо подтверждено содержимое, относящееся к проверяемой сборке.
Это не доказательство отсутствия malicious upstream code и не оценка иных
версий, будущих caches, local vendor provenance или всех vulnerabilities.

## Остаток C05 и проверки

Tests, builds, runtime applications и exploit checks в этом срезе не запускались.
Docs/context/package/diff checks после записи отчёта сохранены в receipt.
Лицензии, corresponding-source delivery, installed privacy, Flutter/native
scope и финальные candidate/device/SCM/origin gates остаются OPEN.
Push, merge, deploy, production signing и новый candidate не выполнялись.

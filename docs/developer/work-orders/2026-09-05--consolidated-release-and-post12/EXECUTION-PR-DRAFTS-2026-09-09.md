# Draft source review — 2026-09-09

**PARTIAL / RELEASE_BLOCKED.** Source branches опубликованы для review;
merge, production activation и выпуск не выполнены.

| Repository | Draft PR | Первый опубликованный head | Base |
| --- | --- | --- | --- |
| Platform | [#242](https://github.com/Kiwunaka/portal/pull/242) | `54ddbf1f49b804d912231636d79670f03eefdf8d` | `master` |
| Core | [#8](https://github.com/Kiwunaka/pokrov-core/pull/8) | `02a091cb0e369192a5ad0909b56ccba8aa1dce17` | `main` |

GitHub readback подтвердил `open`, `draft=true`, указанные heads/bases и
`mergeable=true`. Это не approval: первые hosted checks ещё выполнялись.
Platform `release-base-isolation` был `skipped`; он не считается PASS.
Следующие metadata commits и результаты CI проверяются по соответствующему
новому head; первоначальные наблюдения выше не переносятся на него.

Публикация выполнена обычными `git push origin HEAD:refs/heads/<branch>` и
`gh pr create --draft --base <base> --head <branch> --body-file <local-file>`.
Ветви: `codex/consolidated-plan-start-20260905` и
`codex/r12-correlated-endpoint-probe`. Force push и изменения default branch
не применялись. Independent review не выполнен.

Перед публикацией проверены новые Git blobs относительно promotion bases:
platform 778, client 722, Core 47. Ограниченный поиск настоящих PEM private-key
blocks, GitHub/Telegram tokens и connection URI не обнаружил секретов по этим
шаблонам. Пять совпавших test blobs содержат synthetic URI с `node.example`,
`example.invalid` и documentation IP `203.0.113.0/24`. Это ограниченная проверка,
не доказательство отсутствия любых возможных секретов. `git diff --check` для
platform/Core branch diffs PASS. Runtime validation остаётся привязана к
[точному quality/rehearsal tuple](EXECUTION-BRAIN-REHEARSAL-2026-09-09.md).

## Первые hosted результаты и Apple preflight

На platform `54ddbf1`: `repo-guardrails` PASS, `cross-repository-contract` FAIL
(client/main содержит старый observability snapshot), `release-base-isolation`
SKIPPED. На Core `02a091c`: `test`, Android и Windows reproducibility PASS;
`release-contract` FAIL, поскольку client/main ещё привязан к прежнему Core,
а candidate меняет исходники вне `.github`. Это реальные выполненные ошибки,
не billing/access skip и не PASS.

[Исходные Core receipts и SBOM](evidence/core-ci-20260909/receipt.json) сохранены
из [run 34287485091](https://github.com/Kiwunaka/pokrov-core/actions/runs/34287485091).
Windows DLL SHA-256 `0409da47…d0371` совпадает с используемым локальным DLL.
Android AAR `ea341b5d…9e38b1` повторяем между двумя Linux builds; его SHA отличается
от локального Windows-built AAR `5e2ea69c…5534a`. Межплатформенная byte identity
Android не доказана. Native бинарные файлы из CI не скачивались; сохранены
только 585 839 bytes исходных receipts/SBOM и hash manifest. Signing, candidate
creation и promotion этими результатами не заявлены.

Apple job того же run упал до сборки: `build-apple.sh` требовал Go 1.25.13,
тогда как CI и `config/release.json` используют Go 1.26.8. Core commit `c7a11f7`
читает `go_toolchain` из этого существующего owner config. `bash -n` и две
ограниченные shell-проверки PASS: требуемая версия достигает начала сборки,
старая отклоняется до него. В этих локальных проверках build/install были
перехвачены на границе и не выполнялись.

Полный [run 34296498734](https://github.com/Kiwunaka/pokrov-core/actions/runs/34296498734)
завершён: Core tests и Android/Windows/Apple reproducibility PASS. Apple
сравнил 28 файлов двух XCFramework builds побайтно; Android — два файла,
Windows — три. [Точные receipts и SBOM для c7a11f7](evidence/core-ci-20260909/c7a11f7/receipt.json)
сохранены. Общий workflow остаётся FAILURE из-за `release-contract`; эта
ошибка не подменяется успешными сборками. Apple app/device, signing и
notarization здесь не проверялись.

## Локальные временные копии

По запросу владельца удалены 13 чистых временных worktrees, без удаления веток
или commit history. 52 общих LFS objects проверены до и после; 11 старых app
build directories сохранены отдельно на том же E:. Очищены два Go compile
caches. Свободное место выросло примерно на 70 GiB; основные implementation
worktrees и их source heads сохранились. Журнал восстановления находится в
`E:/r12-pr-preparation-20260909/CLEANUP-REPORT.txt` вместе с точными manifests.
Старые quality paths в исторических командах теперь могут отсутствовать;
их source commits сохранены. Повторно создавать эти копии для обычной работы
не нужно. Прямое удаление трёх Android `intermediates` дважды отклонено
автоматической проверкой (`blocked by policy`); каталоги остались.

## Client LFS — стоимость не подтверждена

Client `5760f415a567ddbc35ee12ba0087414bc3bd08ff` и описание draft PR подготовлены
локально. Dry-run требует десять LFS objects общей длиной **814 580 545 bytes**.
LFS batch upload negotiation вернул HTTP 200 и десять upload actions без ошибок;
сами бинарные objects не загружались, ref не публиковался, PR не создан.

Billing API вернул HTTP 404 с требованием отсутствующего `user` scope.
Доступный браузер не авторизован. Остаток бесплатного LFS и наличие budget $0
с остановкой расходов не установлены. При [денежном пределе владельца](OWNER-DECISIONS-2026-09-09.md)
платные настройки не менялись; client push ждёт подтверждаемого бесплатного
остатка либо существующего ограничения, исключающего списания. Локальные
runtime artifacts и вся история commits сохранены.

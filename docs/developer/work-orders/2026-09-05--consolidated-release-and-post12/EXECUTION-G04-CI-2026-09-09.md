# G04 — фактический CI и граница подписи

**VERIFIED / I3 для G04. Release gate остаётся открыт.** Доказан исполняемый
source CI с точными входами, командами, exit codes и средами; нулевые jobs и
untrusted signing boundary разобраны отдельно. G04 не подменяет успешную
совместимость promotion lines или exact-candidate acceptance.

[Итоговый snapshot](evidence/g04-ci-20260909/snapshot-final.json) содержит
job/step status, полный workflow source и его SHA для каждого scope.
[Receipt](evidence/g04-ci-20260909/receipt.json) связывает 12 сохранённых файлов,
watcher exit codes и hashes полных внешних logs. Исходные billing screenshots
и полные CI logs остаются вне Git; ограниченные результаты приведены в
[selected output](evidence/g04-ci-20260909/selected-ci-output.log).

## Client source и бюджет

Предыдущий LFS access blocker снят [screenshots владельца](OWNER-DECISIONS-2026-09-09.md):
account Git LFS budget $0, Stop usage Yes, 1,8/10 GB storage и 0/10 GB bandwidth.
GitHub описывает $0 budget как остановку сверх бесплатного лимита без оплаты
[в своём billing contract](https://docs.github.com/en/billing/concepts/product-billing/git-lfs).
Остаток не выводится из успешного upload negotiation.

`git push origin HEAD:refs/heads/codex/r12-client-implementation` принят:
10/10 LFS objects, 814 580 545 bytes; client `de5d478` опубликован. Создан
[draft PR #94](https://github.com/Kiwunaka/POKROV-app/pull/94) в `main`, точный
head подтверждён API. История, native artifacts и concurrent generated files
сохранены. Оплата и изменение бюджетов не выполнялись.

## Исправление custody workflow

`Support Signing Custody` описан как master-only, но `workflow_dispatch`
раньше разрешал выбрать иной ref. Platform commit `d57ead0` добавляет job
condition `github.ref == 'refs/heads/master'` до всех steps и checkout точного
`github.sha`. Существующий тест сначала дал 1 FAIL / 1 PASS; после изменения
55 tests и 21 subtest PASS, включая custody verifier и scripts/release router.
33 docs tests, platform context audit и `git diff --check` PASS.

Настоящий [dispatch из feature-ветки](https://github.com/Kiwunaka/portal/actions/runs/34301790647)
для `d57ead0` завершился `skipped`: job `verify-hosted-custody`, **0 steps**,
**0 artifacts**. Это PASS только отрицательного oracle «не выполнять custody
с non-master ref». Сам custody run имеет `NOT_RUN`; подпись или наличие
действующего hosted secret этим не подтверждаются. Исправление находится
в feature PR и ещё не включено в `master`.

Обычные PR workflows platform/client/Core не используют signing keys.
Release-index signer на точном `9169f27` имеет только manual trigger и
`refs/heads/main` guard; source-contract — отдельный workflow без signing key.
Readback четырёх repositories: default token permission `read`, review approval
выключен; в collaborators только Kiwunaka/admin. Fork PR по
[контракту GitHub](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
не получает repository secrets. Этот разбор не заявляет изоляцию от самого
владельца с правом менять workflow/secret settings.

## Выполненные jobs

| Scope | Точный run | Наблюдение |
| --- | --- | --- |
| Platform Guardrails `9b3f80f` | [34301454191](https://github.com/Kiwunaka/portal/actions/runs/34301454191) | PASS, 19 executed steps |
| Platform Guardrails `d57ead0` | [34301792472](https://github.com/Kiwunaka/portal/actions/runs/34301792472) | PASS; 80 admin browser tests, 11 custody tests, quick gate; watcher exit 0 |
| Platform PR contract `d57ead0` | [34301792505](https://github.com/Kiwunaka/portal/actions/runs/34301792505) | FAIL, exit 1: прежний client/main observability snapshot не совпадает с platform candidate |
| Client PR `de5d478` | [34301989210](https://github.com/Kiwunaka/POKROV-app/actions/runs/34301989210) | FAIL, exit 1: текущий Core/main отличается от закреплённого Core `02a091c` |
| Client exact tuple | [34301990803](https://github.com/Kiwunaka/POKROV-app/actions/runs/34301990803) | PASS, 22 executed steps; watcher exit 0; 644 Flutter tests PASS, 1 Windows runtime test SKIPPED_BY_PLATFORM; Android direct/store unit tests и Linux daemon checks PASS |
| Старый client/main `da1ad73` | [33944971093](https://github.com/Kiwunaka/POKROV-app/actions/runs/33944971093) | NOT_RUN, 0 executed steps; историческая billing failure не стала PASS |
| Core `c7a11f7` | [34296498734](https://github.com/Kiwunaka/pokrov-core/actions/runs/34296498734) | 78 executed steps; tests и Android/Windows/Apple reproducibility PASS, общий run FAIL из-за promotion binding |

Exact replay использует уже существующий `workflow_dispatch` с тремя полными
SHAs: client `de5d4784ecd9d1fc90575e48e16da0f90f42da41`, platform
`d57ead0a34f6a4eaf639bc741102356f9fb2f436`, bound Core
`02a091cb0e369192a5ad0909b56ccba8aa1dce17`. Параметры не ослабляют contract
и не меняют promotion pointers. Это проверка source tuple, не новый кандидат.

Среда platform/client: Ubuntu 24.04.4, image `20260831.293.1`. Platform:
Python 3.12.5, Node 22.14.0 / npm 10.9.2. Client workflow: Python 3.12,
Temurin 17.0.20+1, Go 1.25.13, Flutter 3.38.5. Native Windows 100-cycle test
и Windows signing runtime negatives на Linux не выполнялись. Успешные
Android Gradle tasks — `:app:testDirectDebugUnitTest` и
`:app:testStoreDebugUnitTest`; число JVM cases из build-success не выводится.

Команда exact replay:

```powershell
gh workflow run release-v2-contract.yml --repo Kiwunaka/POKROV-app --ref codex/r12-client-implementation -f client_ref=de5d4784ecd9d1fc90575e48e16da0f90f42da41 -f platform_ref=d57ead0a34f6a4eaf639bc741102356f9fb2f436 -f core_ref=02a091cb0e369192a5ad0909b56ccba8aa1dce17
```

Custody dispatch: `gh workflow run support-signing-custody.yml --ref
codex/consolidated-plan-start-20260905`. [26 boundary checks](evidence/g04-ci-20260909/boundary.json)
PASS; [checker](evidence/g04-ci-20260909/check-boundary.py) работает только
с retained metadata/source, без чтения secret values.

Слияние, production activation, release manifest signing и публикация нового
релиза не выполнялись. Совместимые promotion lines и exact-candidate gates
остаются отдельной работой; ошибки обычных PR не скрываются successful replay.

После оформления evidence повторены обязательные docs checks: 33 tests PASS,
platform context audit PASS, package validator — 83 R12, 378 legacy IDs и
432 links PASS; `git diff --check` PASS. Client source в этом срезе не менялся;
hosted replay относится к опубликованному `de5d478`.

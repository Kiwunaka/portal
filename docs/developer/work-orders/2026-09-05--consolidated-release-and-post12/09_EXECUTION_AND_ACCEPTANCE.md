# Общий контракт исполнения и приёмки

Применяется ко всем файлам consolidated-v2. Не подменяет действующие root `AGENTS.md`, safety/approval settings и актуальные owner decisions.

## 1. Режимы запуска

| Режим | Что разрешает явно поставленная задача | Чего не разрешает |
|---|---|---|
| RECONCILE_ONLY | Read-only inventory, документы/maps/work orders в согласованном каталоге | Product code/runtime writes, release resume по умолчанию |
| LOCAL_IMPLEMENTATION | Scoped source/tests/fixtures/docs, локальные builds и checks в изолированной среде | Deploy, секреты в output, unsafe system changes, public flags/spend |
| OWNED_LAB | Только перечисленные owner-controlled hosts/devices и ограниченные network tests | Остальной production/flood/третьи стороны без разрешения |
| RELEASE_OPERATION | Конкретный candidate/channel/rollout/rollback, явно одобренный владельцем | Следующая версия, новая когорта, иной scope или ad spend |

После разрешения LOCAL_IMPLEMENTATION не требовать нового согласия на каждую безопасную правку в разрешённом write set. Новая внешняя мутация, покупка, публикация, удаление истории, изменение ключевой модели безопасности — отдельная граница.

## 2. Начальный reconciliation

Определить реальный current code, не повторять все старые баги. По каждому выбранному требованию статус inventory:

`STILL_PRESENT`, `ALREADY_FIXED`, `PARTIALLY_FIXED`, `SUPERSEDED`, `NOT_APPLICABLE`, `NEEDS_RUNTIME_PROOF`, `SOURCE_GAP`.

Краткое основание содержит path/symbol/commit и test/evidence. По всему старому ledger сохраняется mapping/owner; подробное исследование выполняется just-in-time для ближайшего WO. Отсутствующий зависимый repo блокирует cross-repo check, а не оправдывает `--allow-missing-*` как PASS.

## 3. Индексы и статусы — не одно поле

| Evidence level | Смысл |
|---|---|
| I0 | Требование зафиксировано; current implementation может существовать |
| I1 | Current owner/code/contract/gap обследован |
| I2 | Scoped implementation/fixtures существуют |
| I3 | Применимые local/unit/integration checks реально исполнены |
| I4 | Exact artifact/server/device/origin proof для declared scope |
| I5 | Разрешённый deployment/promotion и наблюдение подтверждены |

Отдельное поле status: queued/active/blocked/implemented/verified/deferred/no-go/not-applicable. `SKIPPED_BY_OWNER` и `BLOCKED_BY_ACCESS` не PASS. `NO_GO` может закрыть исследовательский вопрос, но не означает реализацию функции. Historic I3 не автоматически относится к новым bytes.

Локальный goal имеет outcome `IMPLEMENTATION_VERIFIED` и может завершиться на I3 **только если так задан его критерий**. Release goal не закрывается этим outcome. Архитектурный I3 означает проверку документа/контрактов, не runtime. Goal budget exhaustion или лимит попыток — BLOCKED/LIMIT_REACHED, не COMPLETE.

## 4. Один work order — один проверяемый результат

```text
id / parent IDs / proposed scope
objective / non-goals
current baseline and reused evidence
read set / write set / repository owners
authorization class and environment
invariants and implementation steps
acceptance oracle / exact check commands
negative tests / failure injection boundaries
rollback / migrations / evidence invalidation
terminal states / next handoff
```

Команды тестов получить из current repo scripts/CI; не выдумывать существование `test-all.sh`. `git diff --check` проверяет whitespace, не correctness. Missing toolchain обозначить; не отменять failing assertions, чтобы пройти goal. Dependency обновление/lockfile связано с обоснованной причиной, не автоматический mass upgrade.

## 5. Параллелизм

Разные независимые write sets допускают параллельные worktrees: payments, UI read-only fixture review и Core validation могут разбираться отдельно. Но single writer для общего managed profile contract/connection coordinator/TUN lifecycle/migration history. Merge последовательный по зависимостям. Не делать concurrent changes в том же working tree и не reset чужой worktree.

Cross-repo изменение имеет producer contract→consumer compatibility→integration order→migration/rollback. Нельзя обновить digest в трёх README и назвать согласованную интеграцию выполненной.

## 6. Evidence identity

Минимум: task/test ID, source SHA, artifact digest при applicable, toolchain/build mode, Core/server/policy/profile revision, origin/device class, start/end UTC, exact command+exit status, expected/actual, evidence location, limitations, cleanup outcome.

Секреты, raw endpoints/topology/customer IDs, tokenized URLs и private configs не копируются в публичные notes. В owned lab допустимые sensitive originals отдельно с контролем доступа/retention; в handoff — redacted вывод. Synthetic fixtures помечать и никогда не использовать как live observation.

## 7. Impact-based reuse вместо вечных пересборок

Классы изменений: documentation-only; test harness; product copy; API/schema; profile/policy; Core/runtime; packaged dependency/toolchain; deployment/migration. Перенос evidence допускается при совпадении значимых inputs и oracle. Test harness bug может инвалидировать прежний PASS, даже если продуктовый код не менялся. Независимая правка docs — не обязательный новый AAR/APK.

Не изменять historical Gate F/receipts. Новая проверка ссылается на superseded evidence и причину. Все exact artifact claims ограничены проверенной ABI/platform/channel. Signing manifest не заменяет Android/Windows publisher identity.

## 8. Acceptance scope

Перед тестом зафиксировать required checks конкретного delivery scope. Optional lab не включается в mandatory denominator без принятого scope; но реально shipped feature не исключается после провала ради зелёного отчёта. Approved waiver видим отдельно и не отменяет hard safety invariants.

Основные stop-ship: false protected; неправильный effective profile при заявленном применении; silent protected→direct/расширение coverage; secret leak; опасный privileged command; неверная артефактная identity; непредсказуемое повреждение DNS/routes; ошибочное/повторное начисление или списание из-за order logic; broken primary install/update.

Нет доступа к required device — verification blocker, не установленный defect и не PASS. В локальной задаче сохранить ready-to-run matrix и закончить с точной границей; release gate остаётся blocked.

## 9. Как не зациклиться

После каждой значимой попытки: гипотеза→изменение→check→результат→следующий различающий эксперимент. Не повторять одинаковую failing команду без нового состояния. Рекомендуемый предел: две одинаковые неинформативные попытки — перейти к диагностике или остановить slice. Этот предел не требует прекратить перспективное исправление, но запрещает бесконечный повтор missing credentials/device/billing.

Один короткий blocker record на реально отсутствующий ресурс. Не генерировать сотни новых WOs только для записи того же блокера. Когда все следующие действия требуют отсутствующего доступа/неодобренной внешней мутации — завершить текущую попытку с BLOCKED и handoff. Не обещать, что агент сам продолжит после появления телефона или оплаты, если среда этого не гарантирует.

## 10. Rollback

Profile policy: kill/disable → фактический readback/expiry → разрешённый fallback. Host: восстановление только owned rules/resources. Backend: expand/contract и restore drill. Attribution: сохранить historical records. Release: immutable retained artifact, approved channel pointer и actual client/download readback. Unknown outcome mutation → reconciliation, не blind повтор.

Rollback не скрывает уменьшение protection scope и не отменяет current bank Direct policy без решения. Переход Smart Safe→Full как emergency mitigation только если эта политика заранее разрешена и объяснена; иначе blocked/error лучше тихой смены намерения.

## 11. Короткий итог каждого goal

```text
Outcome: COMPLETE / BLOCKED / PARTIAL / LIMIT_REACHED
Task scope and original IDs:
Changed files / commits:
Executed checks with exit codes:
Reused evidence and rationale:
Not-run checks with reason:
Known issues / risks:
Rollback and cleanup:
Next allowed action:
Release / production status (не равен локальному Outcome):
```

Отчёт должен быть проверяемым. «Всё улучшено», count пройденных строк и screenshot зелёной кнопки не заменяют code+test evidence.

## Общие определения ссылок

[AUD-S01]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/OWNER-FREEZE-2026-09-05.md
[AUD-S02]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/config/cutover-readiness.seed.json
[AUD-S03]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/evidence/013GV-candidate33-bounded-windows-android-runtime/013GV-candidate33-gate-f-decision.json
[AUD-S04]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/INDEX.md
[AUD-S05]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/SOURCE-CROSSWALK.md
[AUD-S06]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/docs/operations/cutover-readiness.md
[AUD-S07]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/shared/tariff-catalog.json
[AUD-S08]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/marketing/src/app/checkout/checkout-client.tsx
[AUD-S09]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/portal_bot/api_payment_routes.py
[AUD-S10]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/portal_bot/admin_v2/security.py
[AUD-S11]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/adminapp/README.md
[AUD-S12]: https://github.com/Kiwunaka/pokrov-core/blob/c1185faa998c69fd5164af415249c96c68ab61bd/config/awg31-capability.json
[AUD-S13]: https://github.com/Kiwunaka/pokrov-core/blob/c1185faa998c69fd5164af415249c96c68ab61bd/engine/sing-box/protocol/awg/contract.go
[AUD-S14]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/apps/android_shell/android/app/src/main/kotlin/space/pokrov/pokrov_android_shell/AndroidCoreEgressProbe.kt
[AUD-S15]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/apps/android_shell/android/app/src/main/kotlin/space/pokrov/pokrov_android_shell/AndroidCoreOperationalEvents.kt
[AUD-S16]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/apps/linux_shell/README.md
[AUD-S17]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/config/release-handoff.seed.json
[AUD-S18]: https://api.github.com/repos/Kiwunaka/POKROV-app/contents/packages/app_shell/lib
[AUD-S19]: https://github.com/Kiwunaka/Pokrov-client/blob/main/README.md
[AUD-W01]: https://docs.amnezia.org/documentation/amnezia-wg/
[AUD-W02]: https://docs.amnezia.org/faq/
[AUD-W03]: https://github.com/amnezia-vpn/amneziawg-go
[AUD-W04]: https://learn.microsoft.com/en-us/windows/release-health/release-information
[AUD-W05]: https://base.garant.ru/12145525/5633a92d35b966c2ba2f1e859e7bdd69/
[AUD-W06]: https://epp.genproc.gov.ru/ru/proc_78/activity/legal-education/explain/otherwise/e8255163/
[GH-AWG]: https://github.com/Kiwunaka/pokrov-core/blob/c1185faa998c69fd5164af415249c96c68ab61bd/config/awg31-capability.json
[GH-AWG-FIX]: https://github.com/amnezia-vpn/amneziawg-go/commit/b5928efb6ca19f0153958460c3d141f04abc5c2e
[GH-MARKETING]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/marketing/next.config.mjs
[WEB-ANDROID]: https://developer.android.com/reference/android/net/VpnService.Builder
[WEB-CODEX-COMMANDS]: https://developers.openai.com/codex/cli/slash-commands
[WEB-CODEX-GOALS]: https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex
[WEB-NEXT]: https://nextjs.org/docs/14/app/building-your-application/deploying/static-exports
[WEB-WIREGUARD]: https://www.wireguard.com/protocol/

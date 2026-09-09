# POST12-30 — HAPP iOS: сохранённая очередь и source gate

**Статус:** `SOURCE_GAP / QUEUED_AFTER_1_2_0`.<br>
**Это не восстановленный полный HAPP implementation plan.** Из приложенного INDEX известно направление, но полного исходного документа нет среди новых вложений.

## 1. Что подтверждено источником

В `INDEX.md` указан `docs/superpowers/plans/2026-08-26-happ-ios-subscription-bs.md`, import hash `a2643a9bfe156cddb5f36bd7622d444201196e960ffddbe2ad0b79a578a68397`. Направление: HAPP iOS direct/bridge subscription, Xray DNS/routing, physical iPhone proof. Также исторически записана ветка `codex/happ-ios-canary` на `221f43f22fb27abdeef0d85f74cb0cc04299863a`.

Это pre-existing работа, не разрешение продолжить/merge/promote до activation. Она не является native POKROV iOS client и не меняет ownership активных Android/Windows/Core.

## 2. Что не удалось установить в подготовке этого пакета

Pinned fetch документа в `portal` на срезе `6b41f758…` и на указанном commit вернул 404. Library-поиск точного имени и уточнение не восстановили полный план. Это не доказательство, что он удалён со всех локальных worktrees или других разрешённых архивов.

Не подтверждены API paths, схема subscription, фактический import flow, текущие HAPP capabilities, supported versions, свойства iPhone runtime, устройство тестирования или readiness canary. Их нельзя заменить догадками по названию документа.

## 3. Первая задача агента — HAPP-01

После POST12 activation в разрешённом workspace найти source через git remotes/branches/log/history и реальные retained inputs. Не создавать случайный repo `VPN` по старому локальному пути. Не перезаписывать существующую canary-ветку и не копировать secret subscriptions в отчёт.

Зафиксировать найденный файл/hash/commit и связанный рабочий diff. Если файл новее import hash — сохранить обе provenance, не откатывать новый текст, чтобы совпал старый hash. Если не найден — записать точные выполненные поиски и `SOURCE_GAP`; остановить только HAPP lane. Остальные postrelease цели не блокируются.

## 4. Дальнейшие задачи — bounded acceptance, не выдуманное содержание missing plan

| ID | Результат | Зависимость |
|---|---|---|
| HAPP-01 | Оригинал/новейшая sanctioned версия и branch inventory либо source gap | POST12-00 |
| HAPP-02 | Reconciliation найденного source с текущими product/renderer/auth contracts | HAPP-01 |
| HAPP-03 | Current HAPP/iOS version и exact supported subscription/render capability review | HAPP-02 |
| HAPP-04 | Owner-authorized physical iPhone direct/bridge/DNS/routing/refresh/revoke tests | HAPP-03 |
| HAPP-05 | Ограниченная third-party delivery decision и rollback | HAPP-04 |

## 5. Инварианты, которые уже известны

Один platform-owned third-party manual path; не передавать lab AWG material в публичную subscription; не смешивать HAPP evidence с native Android/Windows; не объявлять native iOS релиз; credential-bearing URL не хранить в публичных логе/скриншоте/support bundle. Public claims и production действия отдельно guarded.

**Нормальный результат этой цели при отсутствии файла:** source-gap receipt и сохранённая очередь, а не сочинённая «готовая интеграция HAPP».

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

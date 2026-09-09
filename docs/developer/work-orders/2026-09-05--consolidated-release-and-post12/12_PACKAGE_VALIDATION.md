# Проверка итогового Markdown-пакета
**Дата:** 2026-09-05. **Объект проверки:** файлы планов, не код POKROV.
## Фактически выполненные структурные проверки
| Проверка | Результат |
|---|---|
| Основные MD | 12 файлов + этот отчёт |
| Сохранность прежних R12-ID | 83/83, без удаления, добавления или дубликатов |
| Зависимости R12 | Полностью совпадают с исходным JSON; все ссылки на существующие IDs |
| DAG зависимостей R12 | Ацикличен, топологическая сортировка включает все 83 задачи |
| ATS/CR/WP | Все 17 ATS, 24 CR и 17 WP исходных IDs присутствуют в своих документах |
| Относительные файловые ссылки | 96 проверены; отсутствующих файлов нет |
| Markdown code fences | Парность проверена во всех файлах |
| Именованные внешние ссылки | 39 использований по файлам проверены на наличие definitions |
| Готовые /goal | 9; максимальная длина objective 754 символов, меньше 4000 |
| Исходные SHA-256 | Рассчитаны по 7 новым вложениям и 3 файлам предыдущего аудита |
| Базовая проверка содержимого | Нет chat-only citation tokens и совпадений с проверенными шаблонами auth tokens |

Это не полный security scan. Структурная проверка документа не доказывает корректность будущего implementation и не повышает release evidence до I3/I4. Product tests, actual devices, payment operations и production в этой консолидации не запускались.

## SHA-256 итоговых документов

Хеш этого отчёта не включён, чтобы не создавать самоссылочную контрольную сумму.

| Документ | SHA-256 |
|---|---|
| `00_START_HERE.md` | `515e55306ffbfbe0196e5f67f3f6011faa406dea179ae3578dd6338abee73d59` |
| `01_SCOPE_AND_CORRECTIONS.md` | `9c80a72fb34daef01fa5f034f2c61f3812ea8e101f0a6bc734da4deb55dc6baf` |
| `02_RELEASE_1_2_0.md` | `22f5c4b6923b88e4b2def25c7bdde50f9c37a056b4a7b3cadbe634b9e0f05dfb` |
| `03_RELEASE_BACKLOG_83.md` | `6c15707fca56b799d3dfd02c3af47771a2da017d0b5a2865a55ee955d1e29638` |
| `04_POST12_SHARED_ARCHITECTURE.md` | `2b657e177d864653fe9d3f8906ce541465574a57e31d982037622329c219b56c` |
| `05_POST12_TRANSPORT_AWG.md` | `061973721d0636240c350c25b7687ce066592be796eb898b974484f80d407a2a` |
| `06_POST12_SMART_ROUTING_ACCESS.md` | `b31f29e46e627936bf870670b0de3d6d6a729f494998d5f79a32bbf4c547418e` |
| `07_POST12_SHORTLINK_ATTRIBUTION.md` | `d283fc8afa9de0d49974fdb7ca5ce6365d9141b30b91dbcf18ef7ccd4c669bb7` |
| `08_POST12_HAPP_IOS_SOURCE_GATE.md` | `9b7f27d571140f513e5debda5becef46e44b7b37b819229979758543bb3412c0` |
| `09_EXECUTION_AND_ACCEPTANCE.md` | `9208b87db4c9cb14a230abdcf269837c7523c1669eaca847e208499515e1f10d` |
| `10_CODEX_GOALS.md` | `b780689843fd66542edb90ded3ae8085f6b3789afd809a98366756a0ad20de30` |
| `11_SOURCE_CROSSWALK.md` | `f12a3051834899d975299bc5d4063a6ef58db4720f8b6cdf036da74bc2fc4e96` |

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

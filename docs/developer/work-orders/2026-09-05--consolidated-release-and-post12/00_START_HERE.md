# POKROV — итоговый пакет планов: 1.2.0 и следующая программа

Актуальная поправка: [решением владельца от 2026-09-13](OWNER-DECISIONS-2026-09-13.md)
AWG2 исключён из обязательной приёмки и дальнейшего развития всей программы;
активный AWG-контур — AWG3.1. Старые требования и результаты AWG2 ниже сохранены как история.

**Редакция:** 2026-09-05 / consolidated-v2.<br>
**Назначение:** единый вход для Codex и других coding agents.<br>
**Статус:** `PLAN_READY`; выполнение в репозиториях этим документом не запускалось.<br>
**Начальный режим:** `RECONCILE_ONLY`. После отдельной команды владельца — исполнение выбранного пакета, не всей очереди автоматически.

## Результат программы

Довести текущую релизную линию до достоверного подключения, корректной оплаты, безопасного обновления и удобной эксплуатации. После её закрытия развивать адаптивные транспорты, единый routing catalog, Smart Access и attribution `/t/` без второго Core, второй админки и параллельной аналитики.

Новые приложенные документы **сохраняют послерелизную очередь**. Поэтому прежняя рекомендация сделать публичный AWG3.1 безусловной целью 1.2.0 исправлена: это предложение об изменении scope, а не уже принятое решение. AWG остаётся приоритетом, но public/default/cohort activation не следует из наличия кода или этого пакета. Подробности — [границы и исправления](01_SCOPE_AND_CORRECTIONS.md).

## Как читать

| Файл | Для кого и зачем |
|---|---|
| [01_SCOPE_AND_CORRECTIONS.md](01_SCOPE_AND_CORRECTIONS.md) | Обязательные границы релиза; противоречия исходных планов; что изменено и почему |
| [02_RELEASE_1_2_0.md](02_RELEASE_1_2_0.md) | Текущая релизная очередь: networking, payment, Windows, Android, UX, админка, privacy, release |
| [03_RELEASE_BACKLOG_83.md](03_RELEASE_BACKLOG_83.md) | Все 83 ID предыдущего аудита: сохранённые требования, уточнённый scope и зависимости |
| [04_POST12_SHARED_ARCHITECTURE.md](04_POST12_SHARED_ARCHITECTURE.md) | `POST12-00/05`, `ATS-000..016`: общие контракты без дублирования движков |
| [05_POST12_TRANSPORT_AWG.md](05_POST12_TRANSPORT_AWG.md) | `POST12-10`, `CR-000..023`: AWG, TCP, XHTTP, резервные пути и ограниченные исследования |
| [06_POST12_SMART_ROUTING_ACCESS.md](06_POST12_SMART_ROUTING_ACCESS.md) | `POST12-20`, `WP-00..16`: routing catalog, Android apps, Smart Access, provider pool |
| [07_POST12_SHORTLINK_ATTRIBUTION.md](07_POST12_SHORTLINK_ATTRIBUTION.md) | `POST12-40`: конкретная реализация `/t/`, доказуемая атрибуция и правильные метрики |
| [08_POST12_HAPP_IOS_SOURCE_GATE.md](08_POST12_HAPP_IOS_SOURCE_GATE.md) | `POST12-30`: сохранённый scope и честный блокер отсутствующего исходного плана |
| [09_EXECUTION_AND_ACCEPTANCE.md](09_EXECUTION_AND_ACCEPTANCE.md) | Правила исполнения, доказательства, rollback, реальные условия остановки |
| [10_CODEX_GOALS.md](10_CODEX_GOALS.md) | Готовые обычный стартовый запрос и отдельные `/goal` для ограниченных результатов |
| [11_SOURCE_CROSSWALK.md](11_SOURCE_CROSSWALK.md) | Источники, хеши, карта исходных ID и внешние проверки |

Не нужно читать весь пакет в каждом новом чате. Общие обязательные файлы: `00`, `01`, `09`; затем файл своей области и соответствующие строки `03`. `11` — при проверке происхождения или конфликта.

## Первое действие агента

1. Прочитать действующие `AGENTS.md`, task router, canonical product/release owners и OWNER-FREEZE в реальных checkout.
2. Установить корни `portal`, `POKROV-app`, `pokrov-core`, release-index `pokrov` через фактические git remotes. `VPN/master` в старых планах — историческое локальное имя платформы, не приказ найти или создать новый репозиторий.
3. Зафиксировать HEAD, upstream, dirty/worktrees и текущие незавершённые задачи. Не удалять чужие изменения и не делать reset/clean.
4. Сопоставить **только ближайшие задачи** с текущей реализацией, тестами и сохранённым evidence. Весь backlog занести в реестр, но не проводить ещё один бесконечный аудит каждой строки до первого исправления.
5. Записать точную первую очередь: обычно `R12-N01/N02/N03/N04` и параллельно `R12-B01/B02/B03/B04/B05` после `R12-G01/G03`. Уже исправленное подтвердить и пропустить как реализацию, сохранив regression.
6. Завершить стартовую задачу отчётом и исполнимыми work orders. Код продукта в режиме `RECONCILE_ONLY` не менять.

Предлагаемый путь пакета в repo: `docs/developer/work-orders/2026-09-05--consolidated-release-and-post12/`. Если действующий router требует другой путь, использовать его и сохранить эти имена/ссылки. Не перезаписывать существующий root `AGENTS.md` большим планом: достаточно короткой ссылки в существующем task router при разрешённой документационной правке.

## Что должно остаться неизменным

Один Core и один host TUN owner; текущая Windows service-first граница; Android VpnService; одна connection presentation; текущие payment/entitlement/acquisition/action-intent системы; текущий Operator Center. Новые алгоритмы расширяют согласованные границы, а не создают рядом новый продукт.

Product facts, цены, trial, Telegram-награда, minimum versions, privacy и публичные платформы берутся из текущего канона. Исторические числа в документах не являются командой сменить действующую конфигурацию.

## Как считать пакет выполненным

Этот пакет — **набор отдельных целей**, не одна бесконечная задача. Локальная реализация может завершиться как `IMPLEMENTATION_VERIFIED`, оставив physical/prod этапы честно `NOT_RUN`. Это не закрывает release goal. Завершение 1.2.0 подтверждается существующим release process: разрешённая поставка, readback, обязательные проверки и наблюдение. Следующая программа не активируется потому, что агент просто написал `COMPLETE`.

Первый готовый запрос находится в [10_CODEX_GOALS.md](10_CODEX_GOALS.md). Для старта рекомендован обычный запрос; для последующей реализации — отдельные bounded goals.

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

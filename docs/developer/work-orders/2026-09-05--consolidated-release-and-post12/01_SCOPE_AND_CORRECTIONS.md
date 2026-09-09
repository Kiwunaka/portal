# Границы программы и исправления исходных планов

**Редакция:** consolidated-v2, 2026-09-05.<br>
**Основание:** семь новых приложений, предыдущий аудит и 83 слайса, выборочные pinned GitHub readbacks и первичные технические документы. Обозначения источников раскрыты в [11](11_SOURCE_CROSSWALK.md).

## 1. Что является решением, а что предложением

`SOURCE` — положение исходного документа. `CORRECTION` — исправление установленного противоречия. `PROPOSAL` — рекомендуемое инженерное решение, которое не выдаётся за текущую реализацию. `SOURCE_GAP` — данных недостаточно.

Фактический код важен для поведения, но сам по себе не разрешает коммерческий запуск. Действующая команда владельца важна для scope, но не превращает незапущенный тест в PASS. Датированный план не отменяет более позднее проверяемое решение в каноническом owner.

**Уточнение предыдущего ответа:** публичный AWG3.1 как обязательная новая часть 1.2.0 был моей рекомендацией. Приложенный postrelease INDEX и ATS прямо оставляют массовое включение, новый selector/Broker/offline lease после релиза. Поэтому по умолчанию сохраняется утверждённый текущий scope; публичное расширение AWG требует явного решения. Это не отбрасывает работу над AWG: исправления существующего контура и проверка effective profile остаются в релизной очереди.

## 2. Карта scope

| Контур | До закрытия 1.2.0 | После закрытия / отдельного разрешения |
|---|---|---|
| Ошибочный/stale managed profile, неверный protected state | Исправить, проверить exact affected artifacts | Переиспользовать, не переписывать |
| Checkout quote, payment return, idempotency | Исправить существующий коммерческий путь | `/t/` добавляет placement, не новый payment engine |
| Windows/Android install/update/recovery/privacy | Закрыть текущие применимые gates | Дополнительные среды и функции отдельными WOs |
| Operator Center/фронт | Довести уже реализованные сценарии и обязательную accessibility | Новые read models ATS/providers/placements поверх того же центра |
| AWG3.1 | Проверять и исправлять существующий approved lab; public scope отдельно | Приоритетная транспортная productization с device/origin evidence |
| `DisableCookies=true` | Не обязательный релизный критерий и не default | Изолированный эксперимент после отдельного security gate |
| AdaptiveTransportManager / Broker | Не вносить новую общесистемную архитектуру | ATS contracts → shadow → ограниченное действие |
| Новый offline entitlement | Не подменять им текущий auth во время freeze | Отдельная согласованная модель lease/expiry/revoke |
| Smart Access external pool/catalog expansion | Только исправления уже заявленного поведения | WP-00..16, staged subset |
| Hysteria2/WARP/owned Smart DNS | Сверить текущие поздние lab решения; старый NO_GO не стирает поздний reopen | Только соответствующий scope, а не автоматическое включение |
| Linux | Существующая foundation не равна shipped beta | Условная beta: первый конкретный distro/архитектура; 1.2.0 только по изменению scope |
| HAPP/iOS, `/t/`, MASQUE, two-hop, DNS Rescue | Не добавлять молча в текущий candidate | Отдельные цели и feature-specific gates |

Обозначение `P0` внутри postrelease-плана означает приоритет **внутри этой области**, а не автоматический STOP-SHIP 1.2.0.

## 3. Исправления, которые агент обязан учитывать

### COR-01. Развести release completion, локальную готовность и разрешение

SOURCE: `INDEX.md` требует release goal `COMPLETE`; `BLOCKED`, candidate, merge/deploy/publication сами по себе не подходят. CORRECTION: не использовать одну строку goal status как единственное доказательство. Сохранить ссылку на release decision, применимую acceptance matrix, разрешённый канал и завершение observation. Отдельное owner override меняет порядок только в записанном объёме. Недостающий телефон блокирует соответствующий runtime gate, а не заставляет локальную задачу повторяться бесконечно.

### COR-02. `/t/` несовместим с текущей static-export архитектурой в исходном варианте

SOURCE: shortlink §§11/37/38 предписывают request-time `marketing/src/app/t/[slug]/route.ts`. CODE: в прочитанном `marketing/next.config.mjs` установлен `output: "export"` [GH-MARKETING]. Динамическое разрешение новых slug из БД нельзя получить из уже экспортированных статических файлов [WEB-NEXT]. PROPOSAL: Caddy выделяет `/t/*` до static fallback и направляет в существующий FastAPI. Маркетинг остаётся static export. Не добавлять постоянный Node runtime только ради shortlink.

### COR-03. `ref=plc_*` — не доказательство происхождения и не неизменяемая история

SOURCE: shortlink §§6/21 считают `first_ref/last_ref` достаточными для exact paid attribution. CORRECTION: query можно скопировать/подменить, а `last_ref` меняется. Нужны server-issued purpose-bound receipt через existing acquisition machinery и immutable order attribution snapshot. При отсутствии receipt сохранять unverified marketing context, не выдавать его за exact placement. Receipt доказывает first-party lineage, но не реального человека и не причинный эффект рекламы. Новая analytics identity не нужна.

### COR-04. Метрики и immutable placement

SOURCE: `CAC=cost/paid_orders`, `CPC=cost/page_views`, неизменность после первого перехода. CORRECTION: отдельно cost-per-paid-order, стоимость landing view, CPC по определённым clicks и CAC по distinct first-time acquired payers. Page view не доказательство человека. Freeze identity при первом **publish**, не при первом hit. Изменение стоимости — audit/version; после использования rollback отключает lane, а не удаляет историю placements.

### COR-05. Нельзя запустить весь Smart Access как один обязательный мегапакет

SOURCE: WP-16/общий DoD требуют три внешних provider и собственный четвёртый. PROPOSAL: сохранить все четыре в портфеле, но first lab допускает один разрешённый provider и узкую группу сервисов. Own provider не обязан быть четвёртым по времени: если уже есть рабочая owned foundation, начать с неё. Для заявления о failover нужны реально проверенные альтернативы. Отложенный адаптер не получает PASS; он просто не входит в первую принятую поставку.

### COR-06. Режимы имеют разные обещания защиты

SOURCE: Smart Routing предлагает пять режимов, ATS — Full/Smart Safe/Selective. CORRECTION: не создавать две модели и не менять default с All except RU на Full из одной строки старого предложения. «Россия напрямую» сопоставить Smart Safe: неизвестное VPN. «Доступ без полного VPN» — отдельный явный direct-default режим, без device-wide protected badge. Strict Full не наследует автоматические RU-bypass. Ручное исключение явно меняет coverage. Браузер, исключённый на уровне Android, не может потом маршрутизироваться доменными правилами Core [WEB-ANDROID].

### COR-07. Приоритеты и DNS не существуют вне platform coverage

SOURCE: список начинается с безусловной LAN; в другом input DNS hijack всегда раньше bypass. CORRECTION: сначала immutable safety/owned control rules и граница приложений ОС, затем mode/user policy. LAN — явная настройка, не безусловное исключение всех private ranges. DNS hijack действует лишь на перехваченные in-scope потоки. Hardcoded DoH, excluded apps, ECH/QUIC требуют отдельных capability/results; нельзя обещать их контроль одним resolver toggle.

### COR-08. Пример каталога не должен притворяться проверенным

SOURCE: пример Ozon содержит `confidence: verified`, пустые sources и `REPLACE_WITH_VERIFIED_DIGEST`. CORRECTION: это synthetic fixture / `source_only`, запрещённый для production promotion. Package/сертификат/store lineage и домены проверяются отдельно. RU-бренд не доказывает `ru_only`; ASN/ROA не доказывают принадлежность каждого сервиса, его географическую политику или безопасность широкого CDN bypass.

### COR-09. AWG test matrix должна соответствовать POKROV contract

SOURCE: ATS-009 предлагает HP off и MTU 1280/1360/1420. CODE: закреплённый `pokrov.awg31.endpoint.v1` требует header protection key, S1–S4 не ниже 12; MTU — 1280/1400/1408 [GH-AWG]. CORRECTION: positive matrix использует допустимые текущие значения; HP off и иные MTU — negative tests, пока новый compatibility contract не принят отдельно. AWG2 и AWG3.1 не конвертируются сменой label.

### COR-10. Pin от 14 августа требует дополнительной проверки для DisableCookies

SOURCE: `pokrovplan` предлагает userspace `v3.1.20260814`. EXTERNAL VERIFIED: upstream commit `b5928efb6ca19f0153958460c3d141f04abc5c2e` от 28.08.2026 меняет обработку `IsUnderLoad` при DisableCookies: раньше подавлялась отправка Cookie Reply, теперь обходится соответствующая under-load ветвь [GH-AWG-FIX]. Это подтверждённое изменение upstream, **не доказанный сбой POKROV**. До true-experiment сравнить exact pins, проверить patch и безопасный false baseline. Не обновлять весь Core на moving latest автоматически.

### COR-11. Не делать несовместимость ради нового digest

SOURCE: `pokrovplan` требует «новый клиент отвергает старый digest» всегда. CORRECTION: integrity hash не заменяет compatibility/version policy. Старый безопасный профиль разрешён только если он явно поддержан новым contract/capability и не запрещён security epoch/expiry; неподдерживаемое новое поле старый клиент отклоняет. N/N-1 tests обязательны. При отключении DisableCookies нельзя просто опустить поле после true и предположить reset: доказать explicit false либо пересоздание соответствующего runtime state.

### COR-12. Сильная лабораторная проверка не должна замедлять каждое подключение

SOURCE: 256 KiB, upload/hash, rekey, idle 30 min и active 60 min входят в общий список. CORRECTION: это lab/acceptance/soak, не обязательная длительность пользовательского connect. Runtime proof имеет ограниченный byte/time budget, freshness, привязку к effective route и independent fallback verifier. Два origins — устойчивость к отказу проверяющего, не безусловное требование двух синхронных успехов при каждой сессии.

### COR-13. Достоверная диагностика и предел offline

SOURCE: ATS правильно отделяет Observation/Hypothesis/Incident, но CR содержит сильные labels вроде `syn_drop`/`provider_incident`. CORRECTION: без packet/server evidence писать TCP timeout или control failure, а причину хранить гипотезой. Нельзя гарантировать мгновенный отзыв у полностью offline клиента: зафиксировать максимальное stale/grace окно и server-side отзыв data-plane credentials. Сохранять уже работающий безопасный путь при outage control-plane в пределах действующего права.

### COR-14. Исследования не должны блокировать полезную первую версию ATS

SOURCE: ATS-015 имеет broad dependency на ATS-001..014, где находятся MASQUE и two-hop. PROPOSAL: обязательный shared DoR и feature-specific experiments разделить. MASQUE/two-hop/kernel AWG не обязательны до deterministic selector или узкого routing catalog. Их ID сохраняются со статусом `DEFERRED`/`LAB_PLANNED`, не PASS. Архитектурный документ может быть завершён, но конкретная mutation-capable функция без своего security decision не стартует.

### COR-15. Доверие к внешнему DNS не отменяет границы продукта

SOURCE: три provider owner-trusted для lab; обычный UI не показывает технический выбор. CORRECTION: это не разрешение на коммерческую нагрузку и не запрет disclosure в privacy. Подмена DNS на relay не позволяет честно выставить DNSSEC AD для неподтверждённого синтетического RRset. TLS pass-through не требует собственного CA; certificate mismatch — stop, не обход проверки. Game login/store и gameplay/cloud streaming — разные capabilities. Nodelist, пример health=healthy и нулевой latency не являются измерениями.

### COR-16. HAPP источник отсутствует, но направление не потеряно

SOURCE: INDEX ссылается на полный HAPP plan и существующую canary-ветку. Полный документ в приложениях не найден; pinned GitHub fetch вернул 404, уточнённый Library-поиск не восстановил его. CORRECTION: сохранить `POST12-30` как `SOURCE_GAP`, не сочинять исходную спецификацию. Это блокер только HAPP, не общего плана. Порядок восстановления — в [08](08_POST12_HAPP_IOS_SOURCE_GATE.md).

## 4. Решения с безопасными исходными значениями

| Решение | Значение до нового owner decision |
|---|---|
| Возобновление остановленной разработки | Только после явной команды на выбранный пакет |
| Публичный scope AWG 1.2.0 | Существующий канон; предложение о расширении не считается принятым |
| DisableCookies | false; true только отдельный experiment |
| Smart Access default | Текущий продуктовый default без тихой миграции |
| External pool commercial | Выключен до provider/privacy/legal решения |
| Broker automation | Shadow/read-only до anti-poisoning gate |
| Offline grace | Текущее разрешённое значение; новое не придумывать |
| Linux/HAPP/new transports | Отдельные очереди, не автоматически shipped |
| Маркетинговые расходы/рассылка/production writes | Не разрешены планом |

Принятые владельцем значения сохранять один раз в текущем canonical scope record. Не заставлять владельца повторно подтверждать каждый безопасный локальный PR внутри уже разрешённого write scope.

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

# POST12-10 — транспорты, AWG3.1 и устойчивость к ограничениям

**Источник:** CR index 26.08, `pokrovplan`, ATS-009 и предыдущий R12-A backlog.<br>
**Старт:** POST12 activation; shared contracts из [04](04_POST12_SHARED_ARCHITECTURE.md) для затронутой части.<br>
**Цель:** доказанный полезный трафик и ограниченное восстановление при отказе, не «неблокируемый протокол».

## 1. Сохранить существующий runtime

Один embedded Core, один host TUN owner, один user-intent lifecycle. AWG, VLESS REALITY, XHTTP и прочие — capabilities одного согласованного пути. Нельзя вместо adapter добавить вторую независимую VPN-службу, новую Flutter state machine или импорт внешнего клиента целиком.

На activation снять actual capability inventory. Наличие зависимости в go.mod или генератора JSON не доказывает, что capability собрана в AAR/DLL и проходит реальный server interop. Старый HY2 `NO_GO` и поздний default-off reopen сверяются по canonical owner, а не по самой ранней дате input.

## 2. Приоритет работ

1. Переиспользовать исправленные effective profile и scoped proof из 1.2.0.
2. Поднять/проверить exact userspace AWG3.1 pair в разрешённом isolated lab.
3. Проверить двунаправленный payload, DNS, MTU, rekey, roaming, server restart и safe cookie baseline.
4. Подключить bounded fallback на уже проверенный TCP contour; public/canary отдельно.
5. Выбирать дополнительные XHTTP/provider/ingress варианты по измеренному failure domain.
6. HY2/DNS Rescue/fragmentation/MASQUE/two-hop — после собственного entry gate, не обязательный комплект для любой сессии.

## 3. AWG capability и compatibility pack

Исторический прочитанный pin POKROV: `amneziawg-go/v3 v3.1.20260814`, commit `1b86b2ae0e493e7ea93f8c1a0f0cb6735b1551f1`; typed contract `pokrov.awg31.endpoint.v1`; lab default-off [GH-AWG]. На старте сверить новый pin и его update history.

Contract хранит: upstream repo/tag/commit/checksum; tools pin; userspace/kernel class; client/server wire compatibility; config/capability revision; OS/ABI/build tags; параметрические bounds; exact AAR/DLL/server image digests. Не смешивать AWG2 и AWG3.1, не повышать результат одного до другого.

### Матрица корректных параметров

Для прочитанного POKROV v1: HP key обязателен, S1–S4 ≥12, integrated system TUN запрещён, один peer, MTU из 1280/1400/1408. Значения **1360/1420 и HP off из старой ATS-таблицы — negative cases**, а не обязательные успешные профили. Новый набор MTU допустим лишь через отдельное согласованное расширение contract/server/client.

Проверить H ranges, S/I/J bounds, суммарный outer wire size, family overhead, content padding, trailers, timing/rekey relations и allowed IPs. Не объявлять пробел локальной validation эксплуатационной ошибкой, пока не проверено, не отвергает ли это upstream.

Никаких реальных ключей в fixtures. Golden configs полностью синтетические; live material из secret store отдельно. Обновление minimum client/Core/capability, signature и digest атомарно согласовать по supported revisions, а не правилом «любой старый digest теперь плохой».

## 4. DisableCookies — отдельный эксперимент, не обязательная фича

### 4.1. Почему старый input надо обновить

`pokrovplan` предлагает добавить boolean `disable_cookies` и проверять четыре комбинации с RandomTrailers. Безопасное значение по умолчанию — false. Это сохраняется.

Дополнительная внешняя проверка нашла upstream fix от **28.08.2026**, commit `b5928efb6ca19f0153958460c3d141f04abc5c2e`: при true изменена under-load обработка, а не только отправка Cookie Reply [GH-AWG-FIX]. Это не означает, что POKROV уже уязвим или должен немедленно обновиться. Это означает, что **эксперимент на старом pin без review patch недостаточен**.

### 4.2. Исполнимый порядок

**C0 — capability review.** Проверить actual upstream parsing/IPC/readback, semantics true/false, сборку и source diff. Выбрать безопасный pin с нужным исправлением либо оставить experiment выключенным. Update отдельным PR; не менять одновременно runtime архитектуру и transport.

**C1 — safe baseline.** `RandomTrailers=false, DisableCookies=false`, затем `RandomTrailers=true, DisableCookies=false` там, где supported. Полезный payload и under-load безопасные сценарии. Это основа productization.

**C2 — explicit true experiment.** Только при сформулированном измеренном gap и отдельном разрешении на owned isolated server. Ограничить duration, request rate, concurrent peers, CPU/memory/egress, abort threshold и observer. Не выполнять flood production или сторонних ресурсов. Synthetic lab traffic и approved tools; параметры нагрузки записать заранее.

**C3 — return-to-safe.** Проверить true→false, отсутствие поля, stale policy, restart, rollback image/profile и effective runtime readback. Отсутствие IPC field после true не считается доказательством восстановления cookie protection. Нужен verified explicit false или создание нового чистого runtime instance без второго системного TUN.

### 4.3. Изменения слоёв, только после C0

Core: bool, strict parsing, no IPC injection, capability bounds, exact output/reset semantics. Backend: device-bound material, policy allowlist, contract revision/generation, no secret audit, issuance/rotate/revoke/expiry/idempotency. Client: negotiated capability, applied revision ACK, lab-only display safe flags, no manual raw import. Server: matching pin and tools, telemetry/DoS guard, rollback.

Если новое поле необязательное и безопасное false, поддержать явно разрешённую N/N-1 совместимость. Unknown field/capability rejected там, где нельзя безопасно интерпретировать. Старый профиль не отвергается только из-за «новая версия новее»; security epoch/expiry/known-bad pin всё равно обязательны.

### 4.4. Acceptance четырёх комбинаций

Две true-комбинации являются **условной** матрицей эксперимента, не условием выпуска safe AWG. Отказ от true с documented NO_GO допустим; это не PASS true-combination. User-visible «защита включена» определяется route/proof, не значением RandomTrailers/DisableCookies.

## 5. Server pair, provisioning и secret boundaries

Первым — owned userspace client↔userspace server, согласованные версии. Kernel добавлять отдельной совместимостью. Server identity включает image/config revision, NAT/forwarding, routes, family, health и operational owner.

Peer issuance device-bound; retries не размножают peer; key rotation/revoke реально меняют доступ на сервере. Public catalog содержит opaque refs; авторизованный runtime получает необходимый endpoint/key material по защищённому пути. «Не показывать endpoint в UI/log» не означает, что сетевому клиенту endpoint вообще неизвестен.

Разделить выделенный lab endpoint и реальную независимость failure domain: другой порт на том же IP не защищает от IP-block; другой provider/ASN не гарантирует независимый transit/control DNS. Первый lab можно начать на разрешённой существующей инфраструктуре, но claim об устойчивом резерве требует соответствующей независимости. Покупка новых серверов не разрешается текстом плана.

## 6. Проверки и конечные результаты

| Сценарий | Что измеряется | Успех |
|---|---|---|
| Connect | effective contract/profile, peer, DNS, payload, route | Именно назначенный профиль передаёт данные |
| Bidirectional | bounded download ladder/upload byte+hash | Данные проходят в обе стороны |
| Small/large payload | 16/64/256 KiB lab, отдельно runtime budget | Нет ложного успеха после первых байт |
| UDP blackhole | retry count/deadline, выбранный fallback | Проверенный TCP или честный terminal |
| MTU/family | safe profile, outer size, loss/fragment symptoms | No hang при живом handshake |
| Rekey/idle | состояние peers/cookies/нагрузка | Сессия не ломается после initial success |
| Wi-Fi↔LTE / sleep / Doze | generations, underlying network, battery | Управляемое восстановление и no stale proof |
| Server restart/revoke | failed stage, backend state, expiry | Нет бессрочного старого доступа |
| Verifier outage | transport и proof отдельно | Альтернатива/unknown, не ложный leak/green |
| Kill/rollback | requested→applied→verified revision | Настоящее прекращение использования профиля |

Owner origin из исходного плана — Билайн/СПб; его наличие сегодня не предполагать. Дополнительные МегаФон/МТС/T2/fixed/регионы получают отдельные rows. Базовая начальная цель — две мобильные сети и fixed network при доступности, но публичный claim ограничен реально пройденной approved coverage. Эмулятор — rehearsal, не physical mobile proof.

В consumer runtime сохранять наблюдаемые ошибки: DNS_FAILED, PAYLOAD_FAILED, VERIFY_UNAVAILABLE, PROFILE_MISMATCH, AUTH_EXPIRED, ENDPOINT_UNREACHABLE. Более точный `MTU_FAILURE`/`UDP_BLOCKED` только после достаточного differential evidence; иначе symptom+hypothesis.

## 7. Другие контуры

### TCP baseline и XHTTP — CR-008/009/013

Сначала current VLESS REALITY capability; затем отдельно XHTTP/TLS/CDN только если embedded client/server его действительно поддерживают. Пинны обеих сторон, host/SNI/path/method/mode/extra как profile revision. Owned domain/CDN account и разрешённый use case. Tests: CDN403/WAF, GET/POST, buffering/idle, origin unavailable, TLS mismatch, payload cutoff, family, session restart.

Не считать произвольный VPS в разрешённом ASN автоматически доступным по белому списку. CDN availability проверяется на exact hostname/path/service и origin. Никакого использования чужих аккаунтов/CDN/TURN ресурсов без разрешения. Собственный Xray fork — только после локализованного upstream gap и отдельного maintenance decision.

### RU ingress / two-hop — CR-014, ATS-011

Сравнить one-hop другого ASN с двухступенчатым path. Выигрыш проверять по connection coverage, latency, throughput, failure surface, capacity и стоимости. Authenticated ingress→egress, независимый отзыв, no open relay. Для обещания failover нужны альтернативы обоих критических hops. Default не менять только потому, что два hops «выглядят надёжнее».

### HY2 — CR-015

Сверить current closed-lab decision, не копировать устаревший `NO_GO_FOR_1.2.0`. При новом измеренном gap — отдельный typed subset, source/artifact/server/device gate. HY2 тоже UDP/QUIC и не универсальное решение total UDP block. Port hopping и иные расширения не приклеивать автоматически.

### DNS Rescue — CR-016

Только маленький signed bootstrap/catalog/recovery payload через разрешённую owned инфраструктуру. Лабораторное сравнение Slipstream/dnstt отдельное: версия, license, throughput, TTL/rate/battery/amplification. Не заменять обычный VPN, не использовать открытый чужой resolver как неограниченный бесплатный relay.

### TLS fragmentation — CR-017

Route-specific experiment после локализованного ClientHello/SNI gap; не глобальная галочка для банков/платежей. Не лечит L3 IP allowlist. Измерить latency/compatibility, отдельный immediate disable.

### MASQUE — ATS-012

Feasibility only. CONNECT-UDP и CONNECT-IP, H3 и H2 support проверить отдельно у library/server/proxy/provider. H2 fallback не предполагается из слова MASQUE. No second TUN/custom crypto. Отложенный spike не блокирует safe AWG/selector.

## 8. Полный сохранённый CR ledger

| ID | Итог bounded WO | Основные зависимости |
|---|---|---|
| CR-000 | POST12 baseline (переиспользует POST12-00/ATS-000) | Activation |
| CR-001 | Observation/failure model | ATS-002 |
| CR-002 | Exact profile payload/proof runner | ATS-003, CR-001 |
| CR-003 | Privacy-safe evidence/origin identity | ATS-002, ATS-014 |
| CR-004 | Signed transport manifest | ATS-005, CR-003 |
| CR-005 | Bounded selector integration/simulation | ATS-006, CR-002, CR-004 |
| CR-006 | LKG/outage path | ATS-005, CR-004 |
| CR-007 | Independent endpoint inventory/lease model | ATS-004, ATS-010 |
| CR-008 | XHTTP typed provider contour | CR-002, CR-004, capability review |
| CR-009 | XHTTP physical/origin proof | CR-008 |
| CR-010 | AWG contract: reuse or minimal justified update | ATS-009, current contract |
| CR-011 | Owned AWG safe server pair; true-cookie experiment отдельно | CR-010, CR-002, server authorization |
| CR-012 | AWG Android/Windows/origin proof | CR-011, CR-005 |
| CR-013 | TCP fallback portfolio | CR-002, CR-004, capability inventory |
| CR-014 | Ingress/cascade experiment | CR-007, ATS-011 |
| CR-015 | HY2 decision/lab only | Current reopen record, CR-002 |
| CR-016 | DNS Rescue decision/lab | CR-004, bounded rescue contract |
| CR-017 | Fragmentation experiment | CR-001, measured gap |
| CR-018 | Service routing proof, not DNS-only claim | ATS-007, WP-05, applicable WP-10/12 |
| CR-019 | Operator transport/evidence projection | ATS-013, CR-003 |
| CR-020 | Source/license/build/security gate | Каждая выбранная новая dependency |
| CR-021 | Actual approved carrier/device matrix | Выбранные CR-009/012/018; не все optional transports |
| CR-022 | Per-feature canary/kill/rollback | ATS-016, CR-020/021, owner authorization |
| CR-023 | Exact candidate/promotion observation | CR-022, release process |

Обозначения «CR-010 был I3» и прочие старые индексы — historical evidence. На новом срезе — verified reuse или новый тест, не автоматический reset в «написать с нуля» и не наследование production PASS.

## 9. DoD

Для принятого scope: actual profile matching, полезный трафик, family/mode coverage, bounded retry, usable fallback, server key lifecycle, privacy, source provenance, safe operator visibility, actual rollback. Для public availability — отдельные exact device/origin/canary и owner release. Optional NO_GO/DEFER не выдаётся за реализованную capability. Отчёт называет, что именно работает и в каких условиях, а не «пробивает ТСПУ вообще».

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

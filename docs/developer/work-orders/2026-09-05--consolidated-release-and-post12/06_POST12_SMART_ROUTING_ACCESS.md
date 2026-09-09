# POST12-20 — единый Routing Catalog и Smart Access

**Основание:** Smart Routing plan 26.08, ATS-007/008, CR-018; коррекции COR-05..09/15.<br>
**Старт:** postrelease activation и соответствующий shared DoR из [04](04_POST12_SHARED_ARCHITECTURE.md).<br>
**Цель:** один детерминированный каталог и понятные режимы без скрытого расширения Direct или VPN coverage.

## 1. Сопоставление режимов

| Продуктовый режим | Default для неизвестного in-scope flow | Исключения / статус |
|---|---|---|
| Полная защита / Full Tunnel | VPN | Необходимые system exceptions; user exclusions явно уменьшают coverage. Strict preset без auto RU-bypass |
| Россия напрямую / Smart Safe | VPN | Проверенные RU app/destination exceptions; никогда не любой `ru.*`/весь ASN по бренду |
| Доступ без полного VPN / Selective Smart Access | Direct | Только выбранные поддержанные service groups через relay/VPN; не device-wide protection |
| Только выбранные приложения | VPN для выбранных; остальные вне TUN | Empty selection не расширяется до Full. Domain rules только внутри перехваченных apps |
| Кроме выбранных приложений | VPN для остальных; selected исключены | Поддержка конкретной платформы из capability contract, не обещание общего parity |

Это нормализованная модель существующих намерений, не приказ добавить пять новых кнопок или сменить действующий default. Basic UI может показывать три основных режима и отдельный per-app modifier. Поддерживаемые комбинации описать capability matrix; не поддержанное объяснить до apply.

## 2. Исполнимый precedence contract

### Layer 0 — граница ОС и владение ресурсами

OS application include/exclude решается при создании host policy. Android Builder использует allowed **или** disallowed, не оба [WEB-ANDROID]. Excluded app не попадает в Core, поэтому никакое позднее domain правило внутри него не сработает. Для selective service fallback надо сохранить возможность перехватить соответствующий flow; один DNS-only маршрут этого не гарантирует.

### Layer 1 — безусловные safety rules для перехваченного трафика

Запрет loops, local/private destinations через внешние gateways, запрет передачи POKROV authentication/payment и чувствительных исключённых групп external provider, malformed destination/unsupported family policy. Эти запреты нельзя отменить обычным user override. Узкий bootstrap exception не означает direct для всех запросов API/браузера.

### Layer 2 — пользовательское намерение и mode constraints

Явные ручные правила применяются внутри допустимого safety scope. Изменение coverage требует preview и при необходимости reconnect. LAN access отдельная настройка с точным диапазоном/интерфейсом; loopback handling не оправдывает blanket direct для любого private IP. Captive portal — отдельное ограниченное recovery, не скрытое выключение kill switch.

### Layer 3 — curated service policy

Specific domain/service rule раньше broad network fallback; `blocked_inside_ru` не перекрывается общей `.ru` direct записью. `geo_restricted` является input к выбранному режиму, не самостоятельной командой external relay. `ru_only` означает проверенную особенность сервиса, а не «российская компания».

### Layer 4 — bounded IP rules и mode default

Shared CDN/IP/ASN не наследуют весь маршрут одного сервиса. Источник ASN/ROA подтверждает только соответствующие сетевые сведения, а не приложение и не его доступность. Unknown в Smart Safe идёт VPN; в явно выбранном selective mode — по его direct default. Сбой/expiry assets не переводит protected mode целиком в Direct.

### DNS routing

Resolver выбирается согласованно с flow policy: tunneled service DNS через защищённый путь; Direct исключения — по своей declared policy; Smart Access resolver и фактический data path связаны lease/catalog revision. Own DoH, Android Private DNS, браузерный Secure DNS, ECH и QUIC — отдельные capabilities. Не обходить сертификаты и не обещать перехват вне видимости host.

## 3. Routing Catalog

Один canonical schema owner в platform и generated/validated projections в Core/client. Catalog объединяет services, package identities, domains, networks, category membership, eligibility и source/evidence. Не объединять автоматически privacy-sensitive runtime history с публичным каталогом.

Минимум у service:

```text
service_id, display_name, categories, enabled
classification + reason + evidence_status
platform/applicability + mode-compatible route intents
android package + signing lineage/store evidence
windows application identity policy
exact/suffix domains + role(auth/api/cdn/media)
CIDR/ASN metadata + shared/dedicated + provenance/expiry
provider capability references
catalog/schema/security revision + expiry + signature
```

Образцы с placeholder digest, нулевым latency, пустыми sources не допускают `verified/healthy`. Синтетические fixtures помечены явно и не могут пройти production promotion. Поле `source_only` не auto-выдаёт bank/relay rule.

Pipeline: bounded source fetch→snapshot/checksum/license→normalize IDN/exact/suffix→dedupe/conflicts→diff guard→synthetic/owned probes→staging→review sensitive changes→sign→canary→active. Большие raw списки не тащить в mobile runtime без size/startup/memory budgets. Shared `googleapis.com/cloudfront.net/...` не наследует один сервис.

Проверка catalog integrity, permission и expiry отдельна от data-plane credential. Last-known-good хранится с минимальным scope; operator disable и rollback не удаляют audit history.

## 4. Android: обнаружение приложений

Сохранить 25–40 приоритетных RU apps как стартовую **цель каталога**, не как уже verified список. Банки/Госуслуги/маркетплейсы/MAX/VK/карты/операторы — категории поиска, а не утверждение о текущих package names.

Проверять exact package, certificate digest и signing lineage, store variants; multiple signers не сводить к одному произвольному сертификату. Package visibility и разрешения учитывать по actual manifest/API/distribution policy. Downloadable catalog сам по себе не расширяет доступ Android к сведениям обо всех установленных apps.

Сканирование локальное, неблокирующее UI; only necessary fields; события install/remove/replace; кеш revision; пользовательский override. Список пакетов, certificate match details, paths и app inventory не уходят в backend. В telemetry при необходимости только согласованные counts/buckets, не список.

Браузеры и универсальные контейнеры не auto-bypass. WebView работает в контексте вызывающего app/процессов — не пытаться решить всё глобальным исключением «WebView». Замена policy выполняется единственным host owner с rollback и no-leak tests; Android lockdown может несовместимо ограничить Direct, это явный unsupported combination до доказательства.

## 5. Smart Access data path

```text
selected service request
→ policy identifies service group
→ approved sticky resolver/relay lease
→ synthetic/selected address
→ TLS pass-through to genuine destination
→ explicit per-service verified result
```

Проверять отдельно resolver transport, DNS answer, TLS certificate, service request, streaming/WebSocket и family. Login/store/gameplay/cloud gaming — разные sub-capabilities. Один успешный web request не делает всю категорию «Игры» supported.

Без MITM, собственного CA, отключения certificate validation и произвольного CONNECT. Пользователь понимает: ordinary traffic остаётся Direct в selective mode; external gateway может видеть IP/domain/timing/volume; содержимое корректного HTTPS не расшифровывается gateway. Provider не нужен на главном экране, но privacy/disclosure нельзя прятать.

## 6. Provider pool: этапы, а не искусственная зависимость от четырёх сервисов

Comss.one, Xbox DNS, dns.malw.link — **owner-trusted lab candidates из исходного плана**, а не подтверждённые в этой редакции текущие production integrations. Own POKROV provider также сохраняется. До external use проверить реальные протоколы/endpoint/TLS/support/terms/load/logging/contact; коммерческий embedding не следует из бесплатной публичной доступности.

Первая полезная лаборатория: один разрешённый provider + один-два сервиса, rollback и явный fallback. Затем второй для inter-provider failover. Полный список не удаляется, но недоступный третий provider не блокирует уже проверенный subset. Существующий owned default-off Smart DNS contour сначала инвентаризировать; не строить его заново, чтобы соблюсти порядок «четвёртым».

### Sticky selection

Поддержать weighted rendezvous/consistent selection либо эквивалент в **одном** routing coordinator. Не добавлять независимый второй транспортный selector. Локальный случайный salt/session seed, service group, совместимый network context; raw install_id/SSID/IP/fingerprint не являются remote tracking key.

Текущий healthy lease сохраняется для активного auth/stream/upload. Catalog revision/TTL сами по себе не должны без причины менять действующий egress. Новая policy применяется к новым flows; disabled/revoked/misbehaving provider может потребовать немедленного прекращения согласно safety decision. Existing connections нельзя обещать бесшовно мигрировать на другой egress — UI отражает reestablishment.

### Circuit breaker

Closed/open/half-open, bounded tests, cooldown и maximum retries. Три failures/60 секунд из исходника — начальные гипотезы; числа утвердить после measurements. Certificate failure — запрет повторять insecure path. Не выполнять тестовую нагрузку на внешний provider без его разрешённых лимитов.

### Fallback table

| Flow | Разрешённая последовательность |
|---|---|
| Protected service | Проверенный gateway → другой approved gateway → VPN в том же scope → ошибка/блокировка |
| Bank / explicit Direct | Direct → объяснение недоступности; не silent external relay/VPN |
| Ordinary Direct selective | Обычный путь без чужих service-policy побочных эффектов |
| Gaming optional gateway | Direct fallback только если заранее разрешён конкретной service/user policy |
| Expired/no entitlement | Не выдавать новый tunnel; сохранённый доступ только в пределах existing policy |

## 7. Own provider: minimal controlled service

Начать с существующего owned contour, если он есть. Exact service allowlist, bounded resolver, TLS/SNI pass-through, rate limits, no user-controlled arbitrary destination. Общедоступный relay нельзя оставить open proxy даже для собственной инфраструктуры.

Различить DNSSEC validation обычных ответов и synthetic mapping. Не проставлять AD как будто переписанный RRset подтверждён DNSSEC исходного домена. SNI-only relay без ECH/QUIC visibility получает unsupported/fallback, не обещание полного покрытия. UDP relay — отдельное разрешённое расширение.

DoH первым, DoT/прочие только если нужны и supported; не требовать все DNS transports для MVP. Для advertised resilience нужны независимые failure domains, а не два процесса на одной машине. Публичные endpoints и audit не раскрывают ключи, private topology и индивидуальную историю запросов.

## 8. Windows и Linux

Windows использует существующую installed service и recovery journal. Оценить current sing-box/WFP/NRPT capabilities прежде, чем добавлять новый драйвер/resolver. Разные shared OS DNS-process paths не всегда дают достоверную per-process identity; доказать выбранный способ. Identity приложения не только имя EXE: path/publisher/package/user choice, с обработкой обновлений и отсутствия подписи.

Clean install→mode apply→sleep/network switch→service crash→disable→uninstall: восстановление only-owned DNS/routes/firewall, не global reset. Окно не elevated. Смена per-service policy не меняет весь device default без preview.

Linux не заявляется этим планом автоматически. Его delivery queue из R12-L имеет отдельный scope и native network prerequisites. Общие routing/proof fixtures можно переиспользовать, physical support claim — нет.

## 9. Operator Center и UX

Не создавать отдельную provider-админку. Existing Network workspace получает catalog diff/source/freshness, provider/service/origin capability, lease counts, outcome classes и safe disable/drain. Existing Releases показывает policy/artifact revision, canary/rollback фактическое состояние.

Команды через RBAC/action-intent/expected revision/CAS; batch изменения catalog+provider+rollout не прячутся в одной «Сохранить». User UI: выбранный режим, direct exceptions, supported service set, last verification, fallback status. Технические provider IDs и raw domain lists — secondary diagnostics; secrets никогда в preview.

Adblock остаётся независимым opt-in, не меняет silently route. Его поломки auth/payment должны быть обратимыми по service allowlist. Не включать новые adblock presets просто из-за появления routing catalog.

## 10. Сохранённые WP и минимальные выходы

| ID | Работа | Зависимость | Acceptance |
|---|---|---|---|
| WP-00 | Scope/modes/premium/fallback/provider decision | POST12-00, ATS-007 | Один mode contract и выбранный first subset |
| WP-01 | Routing schema, signature/expiry/rollback | WP-00 | Positive/negative/future-schema fixtures |
| WP-02 | Source/license registry, snapshot ingestion | WP-01 | Provenance каждого выбранного source; bad input не заменяет active |
| WP-03 | Verified Android package seed | WP-01/02 | Cert/store/lineage, no spoof auto-bypass |
| WP-04 | Domains/networks/services classification | WP-01/02 | No broad shared-CDN policy; source≠verified |
| WP-05 | Deterministic builder/signing | WP-03/04 | Hash/repro/diff guards/LKG/invalid-signature rejection |
| WP-06 | Provider adapters для выбранного subset | WP-00/01 | Actual capabilities/terms, external forbidden traffic test |
| WP-07 | Sticky service leases + breaker | WP-06, ATS-006 contract | No per-query egress roulette; bounded failover |
| WP-08 | Backend catalog/session/status/evidence API | WP-05/07 | Current auth/entitlement, no-store secret results, rate limits |
| WP-09 | Local Android discovery | WP-03/05 | UI nonblocking, app list local, browsers manual only |
| WP-10 | Unified Android policy compiler/apply | WP-05/09, ATS-007 | Deterministic precedence, family/no-leak/recovery |
| WP-11 | Android selective Smart Access spike+integration | WP-07/08/10 | DNS-only feasibility explicit; actual fallback coverage proven |
| WP-12 | Windows parity on declared modes | WP-05/08, ATS-007 | Installed service DNS/routes/recovery/identity proof |
| WP-13 | Operator read/control views | WP-05/08 | Exact revision, RBAC, truthful rollback; no second admin |
| WP-14 | Own provider extension / reuse | WP-06/07 + security review | Not open relay; TLS pass-through; safe dark launch |
| WP-15 | Device/carrier/service matrix | Выбранные WP-10/11/12, WP-14 только если включён | Actual scope, no emulator-as-phone, no raw secrets |
| WP-16 | Approved subset canary/productization | WP-00/13/15 + applicable security/legal/capacity | Real observation and rollback; остальные adapters отдельно |

Эти WP — не новые release-1.2.0 blockers. `WP-14` не обязательный предшественник first external lab, и conversely внешние три provider не обязательны для first owned lab. Локальный fake adapter годится для unit tests, но не даёт provider supported status.

## 11. QA, budgets, DoD

Обязательные negatives: certificate mismatch; valid DNS/failed relay; changed CNAME; stale A/AAAA; ECH/QUIC unsupported; external DoH bypass; expired catalog/lease; invalid signature; peer revoke; user manual rule conflict; shared CDN; corrupt cache; service crash; Wi-Fi/LTE; uninstall; two simultaneous service leases; hidden UI/background.

Для каждого: exact app/Core/policy/provider revision, device/API, selected mode, expected route, actual DNS/egress, test target class и origin. App/process details в ограниченном local synthetic lab, не автоматически production telemetry. Реальные банковские операции не автоматизировать.

Measure catalog load/parse, package scan responsiveness, memory delta, DNS p50/p95, new-flow failover, traffic/battery and UI frames. 200 мс/20%/10 секунд исходника — гипотезы; baseline и threshold фиксировать в WO, не объявлять пройденными заранее.

**DoD первой поставки:** принятый subset реально работает, unknown/fallback сохраняют coverage, catalog signed/recoverable, package scan private, no TLS weakening, provider permissions/disclosure задокументированы, actual device/origin proof и отдельный rollout. Все прочие сервисы/провайдеры видимо unsupported/deferred. Никаких обещаний «скрываем VPN от банков» или «DNS открывает любые игры».

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

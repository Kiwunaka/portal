# POST12-00 / POST12-05 — общий архитектурный контракт

**Основание:** postrelease INDEX, ATS plan 29.08.2026, CR index.<br>
**Старт:** после настоящего закрытия release goal 1.2.0 или explicit bounded owner override.<br>
**Результат первой цели:** согласованные contracts, fixtures/simulations и исполнимая очередь; не production ATS.

## 1. Одна архитектура и разделённая ответственность

```text
UI / ConnectionPresenter (только projection)
  → существующий client connection coordinator (user intent, host lifecycle)
    → Core API (typed capabilities и transport attempts)
      → transport / routing / DNS adapters

Platform: policy, entitlement, endpoint leases, observation ingestion
Operator Center: read models + существующие guarded action-intents
Host: один системный TUN/routes/DNS/kill-switch owner
```

Название AdaptiveTransportManager обозначает согласованный владелец решений, не разрешение создать вторую connection state machine в Go рядом с независимой Dart-логикой. В RFC назначить boundary между client orchestration и Core execution. Если текущий coordinator закрывает задачу, расширить его контракт и мигрировать прежние ветви, а не добавлять конкурирующий engine.

## 2. Exact baseline и evidence reuse

`POST12-00`, `CR-000`, `ATS-000` используют **один** baseline receipt. Он содержит exact git/source/artifact/policy/server revisions, origins, current capabilities, имеющиеся selectors/LKG/leases, active flags и known gaps. Три разных документа не требуют трёх идентичных аудитов.

Отдельно снять current deployed state только имеющимися разрешёнными read-only средствами. Недоступный origin пометить. Уже выполненный R12-N01/N03 не писать заново: acceptance и input compatibility проверить в новом контексте.

## 3. Threat Model / инварианты — ATS-001

Рассмотреть protocol classification, packet-size/timing, active probing, IP/ASN blocking, UDP restriction, TLS/SNI/WAF interference, partial payload freeze, management outage, server overload, local app observation, Sybil reports, replay/rollback, credential loss, supply-chain и resource exhaustion.

Не допускать: false protected; arbitrary code/config execution через remote policy; второго TUN; global quarantine от одного клиента; бессрочного LKG; массового enable без kill/rollback; расширения direct coverage без согласия.

Для каждого риска записать asset→trust boundary→возможная ошибка→test oracle→residual risk. Не требовать собственного криптопротокола для доказательства уже защищённой HTTPS-сессии.

## 4. Evidence Model — ATS-002 / CR-001/003

Слои:

```text
Observation → aggregated evidence → hypothesis(scope, sufficiency)
→ incident decision → scoped policy action → observed effect
```

Observation содержит version, bounded receipt, attempt/generation, effective profile, transport capability, route mode, IP family, stage/result, elapsed bucket, origin class и timestamp. Наружу — allowlisted безопасная projection, не ключи, SSID, raw IP, список приложений или browsing history.

Пример observation: TCP_CONNECT_TIMEOUT, TLS_HANDSHAKE_OK, PAYLOAD_CUTOFF, DNS_PATH_FAILED, CONTROL_PLANE_UNAVAILABLE. `ASN_BLOCK`, `WHITELIST_MODE`, `DDOS`, `CARRIER_BLOCKED` — гипотезы, не automatic fact. Если confidence не откалиброван, использовать достаточность/низкая-средняя-высокая уверенность вместо выдуманных 97%.

**Tests:** invalid enum/schema; source spoof/replay; one-cohort failure; stale sample decay; contradictions; old generation; отсутствующее измерение не превращается в ноль или success.

## 5. Connectivity Proof — ATS-003 / CR-002

Не переизобретать R12 proof, а добавить необходимые multi-origin/receipt контракты. Proof привязан к tuple:

```text
artifact + Core capability + effective profile revision
+ route/DNS policy + attempt/generation + IP family
+ probe ID + nonce/freshness + outcome
```

Проверить transport, DNS, authenticated bidirectional payload и expected egress **раздельно**. Успешный собственный core request не заменяет host routing/leak tests. Mode-specific coverage доказывается OS/process tests; отдельное прямое приложение не считается утечкой, если оно намеренно исключено.

Два независимых verifier origins в дизайне, но не обязательный fanout на оба при каждом connect. Отказ первого вызывает ограниченную альтернативу; отказ проверки остаётся отличим от доказанной поломки туннеля. Nonce bound to authenticated HTTPS/session; дополнительная подпись ответа — только если threat model требует. Общий секрет в распространяемом приложении не делает клиент доверенным.

Runtime cheap ladder и lab deep ladder имеют разные бюджеты. `16/64/256 KiB`, upload/hash, rekey/idle/soak сохраняются в lab matrix. До включения production numeric budgets фиксируются по reference device. Нет бесконечного фонового probe polling.

## 6. Broker Anti-Poisoning — ATS-004 / CR-007/019/022

Health key: endpoint × transport × profile × network cohort × IP family × time window. Global availability и scoped degradation раздельны. Client report — evidence с ограниченным весом, не команда.

Одноразовые server-issued attempt receipts уменьшают replay, но не доказывают честность самого клиента и не устраняют Sybil автоматически. Нужны bounded issuance/rate limit, quota влияния источника, sample sufficiency, independent owned probes/server metrics, expiry и audit. Сочетания сигналов и пороги зафиксировать до automation; универсальные числа из плана не считать уже валидированными.

Этапы: ingest→shadow scoring→operator recommendation→scoped action→recovery canary. Global quarantine требует independent corroboration согласно утверждённой policy. Cold reserve выдаётся маленькому shortlist по lease, не публикуется всем и не пингуется постоянно.

**Tests:** поддельные receipts/replay; N сообщений от одного источника; один carrier down при healthy остальных; false reports против healthy owned probes; restart/late events; rollback ошибочного suppression; ограниченное возвращение.

## 7. Offline entitlement / signed policy — ATS-005 / CR-004/006/020

Разделить API token, refresh/session, offline lease, transport manifest, data-plane credential, app release identity. LKG не выдаёт новый entitlement.

Manifest: schema/capability, epoch+revision, issued/not-before/expiry, minimum client/Core, opaque profile references, bootstrap/probe sets, kills, signer identity. Secret material device-bound и хранится отдельно. Новый field не должен требовать фальшивой ручной синхронизации JSON/Dart/Go без parity tests.

Anti-rollback: max accepted epoch/revision, trusted-time baseline, signed authorized rollback, bounded old target. Restore/reinstall/clock rollback не должны продлевать оплаченный доступ. Server credential expiry/revoke — последняя граница.

**Честная граница:** offline клиент не узнает об удалённом kill мгновенно. Определить максимальное stale окно, что допускается до expiry и как server side прекращает tunnel. После восстановления API проверить kills до следующего выбора. Новые lease durations — owner decision; текущие значения не переписывать под пример.

Ротация использует существующие vetted primitives/keys; release, support и transport trust domains не смешивать. Откат policy отличается от arbitrary downgrade приложения.

## 8. Bounded selection — ATS-006 / CR-005

Состояния: idle → baseline/shortlist → attempting → tunnel established → verifying → protected; failures → limited next candidate/repair → terminal. Network change создаёт новый контекст и инвалидирует только несовместимые proofs/hints.

Candidate tuple: capability + profile revision + endpoint lease + family + mode + DNS + probe policy. Проверять eligibility/kill/capability **до** ranking. Выбирать sticky healthy путь; отрицательная память локальная/сроковая. Разные протоколы одного IP не считаются независимыми при IP blocking.

Budget record обязан задать total deadline, per-stage cap, max attempts/endpoints/concurrency, max diagnostic bytes, cooldown/hints TTL, repair attempts. Все child tasks входят в общий счётчик и cancellation. Race допускается на transport/probe preparation, но не как два owner системного TUN.

**Tests:** UDP blackhole с TCP available; все endpoints down; verifier failure; API outage+valid/expired lease; wrong profile; user cancel; settings change midattempt; duplicate events; flapping; one provider down; negative cache expiry.

## 9. Routing safety — ATS-007

Общую таблицу режимов и precedence брать из [06](06_POST12_SMART_ROUTING_ACCESS.md). `Россия напрямую/Smart Safe` оставляет unknown через VPN. Direct-default selective mode явно включается пользователем. Full strict не наследует auto-bypass. Android OS exclusion и Core domain rules — разные уровни, порядок в одном списке их не объединяет.

Существующий default не менять ни потому, что ATS рекомендует Full, ни потому, что новый UI удобнее. Новый default — отдельная миграция и product decision.

## 10. Сохраняемые ATS ID и зависимости

| ID | Deliverable / проверка | Зависимость | Применимость |
|---|---|---|---|
| ATS-000 | Exact baseline receipt, ссылка на POST12-00/CR-000 | Activation gate | Все |
| ATS-001 | Threat model, invariants, owners | ATS-000 | Shared |
| ATS-002 | Observation/hypothesis schema и fixtures | ATS-001 | Shared |
| ATS-003 | Scoped proof + failure/verifier fixtures | ATS-002 | Shared |
| ATS-004 | Anti-poisoning ADR, simulation, rollback | ATS-002, ATS-003 | До Broker mutation |
| ATS-005 | Lease/manifest/clock/revoke ADR и fixtures | ATS-001 | До нового offline/manifest |
| ATS-006 | Selector RFC, budgets, deterministic simulation | ATS-002, ATS-003, ATS-005; ATS-004 при Broker | До adaptive selection |
| ATS-007 | Mode/precedence/fallback safety | ATS-001, ATS-002 | До shared routing |
| ATS-008 | Rootless Android visibility lab plan и observed results | ATS-007 | До claims о видимости; не до каждого TCP fix |
| ATS-009 | Exact AWG userspace compatibility pack | ATS-000, ATS-003 | До AWG нового public scope |
| ATS-010 | Endpoint diversity inventory и bounded leases | ATS-004 | До Broker/failure-domain claims |
| ATS-011 | One-hop/two-hop comparison, GO/DEFER/NO_GO | ATS-003, ATS-010 | Отдельный эксперимент |
| ATS-012 | MASQUE feasibility: exact library/H2/H3/provider limits | ATS-001, ATS-003 | Отдельный эксперимент |
| ATS-013 | Pulse/Operator projection, no second admin writer | ATS-002, ATS-004 | До operator ATS |
| ATS-014 | Telemetry tiers/retention/cohort/privacy decisions | ATS-002; ATS-013 для UI export | До нового remote ingest |
| ATS-015 | Dependency-ordered WOs и readiness по features | Основной ADR subset; эксперименты classified | Shared план, не все experiments PASS |
| ATS-016 | Per-feature canary/kill/rollback и evidence plan | ATS-006, ATS-015; ATS-009 при AWG | До rollout выбранной функции |

`ATS-015` больше не требует успешного MASQUE/two-hop, чтобы описать первую полезную реализацию. Их исследовательские цели сохраняются и получают DEFERRED/LAB_PLANNED/NO_GO с объяснением. При включении функции её собственные gates обязательны.

## 11. Definition of Ready и Definition of Done

**DoR первой shared реализации:** baseline; invariant/observation/proof/mode contracts; numeric budgets для включаемого пути; typed minimum capabilities; data/retention policy; owners/read/write set; fixtures; rollback. Для Broker нужны ATS-004/010, для offline — ATS-005, для AWG — ATS-009. Не ждать чужих независимых задач.

**DoD архитектурной цели:** документы согласованы с текущим кодом, спорные решения обозначены; deterministic fixtures/simulation реально запущены; существующие implementation points найдены; готова очередь WOs; optional experiments сохранены без fake PASS. `UNRESOLVED_OWNER_DECISION` допустим в отчёте, но функция, которую он защищает, остаётся NOT_READY.

**DoD productization:** реальные artifacts/server/policy/origin proofs, разрешённый canary, observed rollout/rollback. Архитектурный I3 это не заменяет.

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

# POKROV 1.2.0 — окончательный план завершения текущей линии

**Задачи:** `R12-*`; все 83 строки — в [03](03_RELEASE_BACKLOG_83.md).<br>
**Ограничение:** действующий approved scope, не весь postrelease roadmap.<br>
**Режим старта:** rebaseline; реализация — после команды на выбранную волну.<br>
**Связанные правила:** [01](01_SCOPE_AND_CORRECTIONS.md), [09](09_EXECUTION_AND_ACCEPTANCE.md).

## 1. Отправная точка

Предыдущий аудит зафиксировал четыре repository HEAD и приватный `candidate.33`, приложение `1.2.0+4053`. Сохранённый Gate F: 19 проверок, 2 PASS, 17 иных статусов, 0 FAIL, решение BLOCKED. Это **исторический проверенный срез**, не повторная проверка сегодняшнего deployed runtime и не 17 найденных дефектов. На старте агент получает новые HEAD и существующие поздние evidence, не откатывает их под этот документ.

| Репозиторий | Ветка | HEAD предыдущего аудита |
|---|---|---|
| `Kiwunaka/portal` | master | `6b41f758ca228a0d5ff13ede0f865096cdac2134` |
| `Kiwunaka/POKROV-app` | main | `da1ad7395615837432615e0f150d7c0bf05322a4` |
| `Kiwunaka/pokrov-core` | main | `c1185faa998c69fd5164af415249c96c68ab61bd` |
| `Kiwunaka/pokrov` | main | `9169f272203ec690ab7b0e6a69e92dc2b6762cb4` |

Сохранить исходный release ledger: 378 требований, а не заменить его 83 новыми строками. 83 — дополнительный reconciliation/implementation backlog, не 83 подтверждённых бага. Сопоставить старые ID с текущим owner и новой задачей; не перепроверять каждый независимый сценарий после изменения README.

## 2. Что не строить повторно

Windows privileged service и non-elevated UI; базовую typed connection model; подписанный release-index; Android identity/update/flavor boundaries; серверный offer preview/catalog; entitlement/payment/outbox foundation; существующую семираздельную админку; support/event foundation. Их приёмка и исправления остаются в scope, их полное повторное создание — нет.

Старые выводы «Linux отсутствует», «CI отсутствует», «везде Cupertino» и «промокоды только static» не переносить без проверки. Существующая Linux foundation ещё не подтверждает живой Core/TUN; наличие workflow не доказывает запуск всех required jobs.

## 3. Волна R0: воспроизводимый старт, без очередного общего аудита

**ID:** G01–G07.

Выходы: source tuple; реестр dirty/worktrees; approved scope и channel; preservation manifest предыдущего candidate; карта ближайших finding→code→test; реальный CI lane; список evidence, инвалидируемого новым diff.

Проверять retention у фактически сохраняемых artifacts. В предыдущем отчёте signer artifact истекал 18.09.2026 08:01:25 UTC; это ориентир для проверки, не новая гарантия доступности. Не копировать signing secrets в архив или отчёт.

Историческое значение public=1.1.6 не зашивать обратно в код: установить current public/candidate/development authority. Ed25519 manifest, Android signing certificate и Windows Authenticode — разные проверки.

## 4. Волна R1: сначала конкретные дефекты

### 4.1. Managed profile lifecycle — N01/N02

Зафиксировать одну цепочку:

```text
assigned_revision
→ fetched_revision + verified_contract
→ staged_revision
→ effective_revision acknowledged by runtime
→ verified_revision + proof scope
```

В предыдущем журнале новое назначение AWG2 после AWG3.1 не было применено обычным reconnect. Статус finding — `REPO_RECORDED`: сначала воспроизвести на текущем коде. Если исправлено — сохранить regression и reuse evidence. Если нет — исправить ordinary reconnect, а не только специальную кнопку repair.

Транзакция: validate/capability/entitlement → materialize → checkpoint → apply → runtime ACK → scoped proof → commit. При отказе — последний разрешённый profile либо честный failure. LKG не расширяет entitlement, traffic coverage или срок ключа. Повтор команды идемпотентен; cancellation имеет generation fence.

**Негативные сценарии:** AWG31→AWG2→AWG31; сервер сменил assignment во время fetch; второй reconnect во время stage; поздний callback; профиль невалиден; API недоступен; пользователь сменил route mode; отказ после частичного apply; restart между checkpoint и commit.

**Oracle:** requested/effective/proven revisions согласованы либо UI явно сообщает, что изменение не применилось. Диагностика не содержит raw profile/endpoints/keys.

### 4.2. Protection proof — N03/N04/N08

Отделить control-plane availability, transport handshake, host route, DNS, egress и actual coverage. Core URL test не доказывает, что весь пользовательский процесс идёт тем же путём. Проверить реальные in-scope и out-of-scope процессы/приложения и IPv4/IPv6.

Существующий Android outer event fence по run/attempt/generation/sequence сохранить. Тестировать узкую возможную гонку probes внутри одной attempt; не объявлять её существующим production-багом до воспроизведения. Старый success не должен подтверждать новый target.

Недоступный verifier — `UNVERIFIED/DEGRADED`, не автоматический leak и не повод обязательно рвать живую сессию. Runtime proof небольшой и bounded; soak/payload ladder — отдельная QA.

### 4.3. Checkout — B01/B02/B03

Подтверждённые предыдущим source review условия перепроверить на current HEAD:

- действительный offer preview обязателен и при пустом промокоде;
- изменение plan/promo/provider/currency/subject мгновенно инвалидирует quote; debounce применяется к запросу, не к валидности цены;
- response принимается лишь для актуальной input generation и subject;
- placeholder `1 ₽` или stale catalog не превращаются в платёжную authority;
- browser return `/pay/success` не сообщает paid до server-confirmed order status.

Функциональная модель: `input → preview_pending → valid_quote → order_created → provider_pending → paid → fulfillment_pending → active`; отдельно invalid/expired/failed/manual_review. Провайдер/сервер остаются authority; найденные UI-условия не доказывают обход оплаты.

**Oracle:** stale/invalid/wrong-subject quote не активирует CTA; точная сумма берётся с сервера; возврат браузера без оплаты не даёт success и не выдаёт доступ; поздняя реальная оплата корректно сверяется.

### 4.4. Deadline/idempotency — B04/B05/B06

Обязательные price/provider данные не зависят от optional attribution. Fetch имеет deadline, abort и свежесть ответа. Для mutation timeout может случиться после commit: повтор использует тот же intent/order reconciliation, а не создаёт новый заказ. Duplicate webhook/worker, две вкладки, callback-before-return, late callback и quota race входят в Postgres integration suite.

## 5. Волна R2: существующий fallback и платформы

### Networking N05/N06/N07

В релизе — корректные наблюдения, общий ограниченный бюджет **существующего** fallback, отрицательная память, backoff, cancellation и безопасный API-outage path. Не добавлять ATS Broker или новую offline entitlement модель под видом bugfix.

Не называть timeout доказанной ТСПУ-блокировкой. Полный UDP blackhole требует разрешённого TCP пути, не чередования AWG/HY2. Если подходящих кандидатов нет — terminal failure и помощь. Нет молчаливого protected→direct и бесконечного spinner.

### Windows W01–W06

Проверять exact setup из утверждённого channel, а не произвольный developer exe. UI обычного пользователя; Core/TUN/routes/DNS принадлежат установленной службе. Проверки: clean install, update с предыдущей публичной версии, downgrade rejection, normal/second launch, tray/login focus, IPC deny/replay/frame bounds, sleep, Ethernet/Wi-Fi, crash UI/Core/service, reboot, repair, connected uninstall.

Восстанавливать только owned state. Kill switch может намеренно сохранить блокировку; этот outcome отличен от «обычный интернет восстановлен». Не flush чужие firewall rules. Измерять UI и service/Core отдельно и суммарно; недоступный счётчик не считать 0. Применимость Win10 edition/build фиксируется отдельно; unsigned beta exception не расширяется на trusted/Store/stable claim.

### Android D01–D06

Primary ARM64 artifact тестировать отдельно от universal: предыдущие размеры 101 366 678 и 295 370 161 байт — разные файлы, не взаимозаменяемое evidence. VersionName одинаковый не доказывает package/signer/versionCode/ABI continuity.

Сценарии: permission allow/deny/revoke, fresh/upgrade, physical phone, Wi-Fi↔LTE, captive portal, IPv6/NAT64 где заявлено, Doze/background/process kill/reboot, selected/except-selected/full/RU policy, private notification, tunnel vs UID counters, protected sockets без loop. Store/direct lane проверять на конечном manifest. Ненужные ABI/assets удалять по breakdown, не выносить критический Core в неподписанную postinstall загрузку.

### AWG A01–A09

Для approved default-off lab обязательны isolation, capability/material safety, отсутствие случайного public exposure и исправление regressions существующего пути. Для **отдельно одобренного публичного AWG** дополнительно обязательны A02–A07/A09: exact server interop, физические устройства, сеть, key lifecycle, fallback и canary. Scope таких проверок записывается до сборки; нельзя задним числом отключить failing AWG gate и сохранить тот же публичный claim.

DisableCookies true и новые ATS/Broker фичи не являются обязательной частью этой волны. Подробная будущая программа — [05](05_POST12_TRANSPORT_AWG.md).

## 6. Волна R3: завершить продукт, а не переделать его

### Operator Center O01–O07

Сохранить `portal/adminapp`, существующие workspace и capabilities. Проверить authenticated session/CSRF/roles/step-up, API fingerprint, safe projection и 5 рабочих сценариев: плохое подключение; paid без access; incident на узле; regression релиза; истёкшая акция.

Connectivity card показывает requested/effective/proven, scope, freshness и next action. Release cockpit отличает 11 своих диагностических checks от 19 historical Gate F — нужна карта соответствия, не равенство количества. `rollback requested`, registry state и фактически переключённый artifact pointer — разные стадии. Legacy read-only удаляется/redirect только после parity, smoke и rollback.

### Frontend F01–F07

Одна projection state→title/CTA/disc/semantics/haptic. `Connecting`, `Verifying`, `Recovering`, `Disconnecting` различимы. Mode coverage видно на первом слое. Onboarding не блокируется Telegram/rewards/optional attribution. Долгое действие ограничено и объяснено.

Preserve platform input/scroll; reduced motion меняет sticky/autoplay сценарий, не только CSS transform; no-JS не прячет весь контент. Critical path: keyboard, TalkBack/Narrator, text/zoom 200%, focus return, consent/error association. Существующие визуальные улучшения не переоткрываются без regression.

### Core/архитектура/performance C01–C05

Разделять ownership, не строки. Приоритет: managed-profile lifecycle, connection orchestration, first-session и support use case; backend payment boundary вместо globals. Сохранять ABI/capabilities выбранной линии; ABI v3 не новый blocker.

Before/after измерения одинакового scenario/hardware/build mode. Не обещать кратное ускорение, пока нет результата. Нет необходимости менять ORM/framework или все query hooks ради одного найденного bottleneck.

### Privacy/support V01–V04

Planted-secret regression через реальные Core/native/app/sinks/bundle/upload/admin, не только regex над test string. Preview/consent/case-bound access/retention обязательны; local event store bounded. Full disk/queue storm/clock jump/telemetry outage не блокируют VPN. Support AI предлагает, но не выполняет возвраты, админские команды или публикации.

### Коммерция M01–M06

Не менять автоматически текущие цены/trial/bonus/grandfathered grants. Offer/copy/API/order/revision должны совпасть. Реальная акция имеет server deadline/price hold/quota; permanent welcome price и annual saving не получают вечный таймер. Existing capacity guard сохраняется; данные 5 000 ₽/300 пользователей — вводная владельца, не измеренная ёмкость и не полная себестоимость.

Legal/seller/terms/provider approval обязательны для коммерческого действия; внешний пилот/рассылка/расходы не включены в техническую команду. Новая `/t/` система после релиза не блокирует уже существующие checkout исправления.

## 7. Волна R4: финальный candidate и закрытие

Q01–Q03: составить применимую matrix; закрыть mandatory safety/identity/payment/runtime gaps; выполнить soak и recovery; сохранить новый go/no-go без переписывания исторического Gate F. B08 требует реального изолированного Postgres restore/migration proof, а не только копирования файлов.

Новый candidate нужен, когда меняются включённые build/runtime/config inputs. Docs-only изменения не автоматически отменяют unrelated device proof. Любое повторное использование evidence имеет impact rationale и exact input binding.

Q04–Q05: только отдельный owner-authorized same-byte rollout, фактический pointer readback, наблюдение и завершение release. Новое значение min-supported не оставляет людей без работающего update path. Незавершённый optional lab не объявляется PASS.

## 8. Критический путь и разделение труда

```text
R0 baseline/scope/evidence
  ├─ N01 → N02/N03 → N04/N08 → Windows/Android exact network
  ├─ B01/B02 → B03/B04/B05 → B06/B08
  └─ O01 + existing frontend/privacy/core regression
         ↓
Q01 applicable matrix → Q02 soak → Q03 technical go/no-go
         ↓ отдельное разрешение
Q04 rollout → Q05 observation → release completion → POST12 activation
```

Один runtime writer на пересекающийся state/host boundary; платежи можно вести параллельно в отдельном worktree. Тестовый агент может работать read-only независимо. Историческая широкая dependency в `03` не разрешает менять unrelated области в том же PR. Каждый WO уточняет actual read/write set и oracle.

**Первая полезная цель реализации:** current regression + минимальный fix N01/N02, затем evidence/proof; параллельно B01/B02. Не создавать следующего кандидата только для нового status-файла.

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

# Codex — как запускать итоговые планы

**Назначение:** готовые команды владельца, а не самоисполняющаяся инструкция из вложения.<br>
**Рекомендация для этого проекта:** один обычный запрос на ограниченную сверку, затем короткие `/goal` на конкретные проверяемые результаты. Не запускать одной целью весь релиз и все post-release планы.

## 1. Что относится к Codex, а что — к этому проекту

Официальная документация описывает Goals как цель текущего thread, рассчитанную на несколько шагов; доступны просмотр, pause, resume и clear. Для короткой разовой сверки обычного запроса достаточно. Подробный план хранить в MD, а в goal указывать результат, границы и критерий завершения. [WEB-CODEX-GOALS]

CLI-справка задаёт предел 4000 символов текста goal. Команды управления: `/goal`, `/goal pause`, `/goal resume`, `/goal clear`; список доступных команд проверить в установленной версии через `/`. Если соответствующий интерфейс не поддерживает Goals, тот же bounded prompt выполняется обычной задачей. [WEB-CODEX-COMMANDS]

Ни goal, ни файл не обходят текущие approvals, sandbox, repository instructions или explicit freeze. Новая цель не должна сосуществовать с незавершённой прежней целью, которая пишет в тот же worktree. При смене scope сначала остановить конфликтующее исполнение, сохранив его checkpoint.

Далее — предложенные конкретно для POKROV команды. Их выполнение здесь не запускалось.

## 2. Подготовка файлов

Поместить весь пакет с сохранением имён в один каталог checkout. Предлагаемый путь:

```text
docs/developer/work-orders/2026-09-05--consolidated-release-and-post12/
```

Если task router использует другое место — сохранить его. `00_START_HERE.md` должен быть единственной точкой входа; не вставлять все планы в root `AGENTS.md`. В большом workspace реальный root каждого repo устанавливать через git remote, а не по историческому имени `VPN`.

Файлы `00`, `01`, `09` обязательны для каждого исполнителя. Остальные читать по цели. План не требует новой подписки/API key, изменения permissions или установки стороннего оркестратора.

## 3. Первый запуск — обычный запрос, без /goal

Скопировать в Codex после помещения пакета в workspace:

```text
Прочитай 00_START_HERE.md из итогового пакета POKROV и действующие AGENTS.md/task router/OWNER-FREEZE. Сейчас выполни только RECONCILE_ONLY.

Сними exact local/origin HEAD, dirty/worktree state четырёх реальных репозиториев. Сохрани существующие 378 требований и все 83 R12-ID. Сверь текущую реализацию и evidence только ближайших G01/G03, N01–N04 и B01–B05. Уже исправленное не переписывай; старый source status не выдавай за новый runtime proof.

Оформи в разрешённом work-order каталоге BASELINE.md, SOURCE_RECONCILIATION.md и NEXT_WORK_ORDER.md: ближайшие исполнимые slices, write sets, regression checks, scope, блокеры и точный следующий шаг. Перечисли остальные задачи как очередь без повторного полного аудита до первого фикса.

Код продукта, public pointers, signing keys, серверы, оплаты и кампании не меняй. Post-1.2.0 очередь не активируй. Заверши после этих трёх результатов; не продолжай бесконечный ресерч и не помечай release goal COMPLETE.
```

Это короткая сверка перед новой работой, а не просьба написать ещё один мегаплан. Если actual HEAD уже содержит нужный fix, первый WO должен проверять его и двигаться дальше.

## 4. Первая implementation goal — правильный профиль и proof

Применять после просмотра стартового результата и явного решения возобновить этот scope. Отправленная владельцем команда ниже разрешает **локальную реализацию указанной группы**, но не deploy/promotion.

```text
/goal Возобнови только локальную работу R12-N01–N04 по итоговому пакету POKROV, файлам 00/01/02/03/09 и принятому NEXT_WORK_ORDER.md. Добейся, чтобы desired/fetched/staged/effective revision и connection proof не расходились: обычный reconnect применяет назначенный профиль либо явно сообщает отказ; stale/чужой probe не делает protected. Сохрани существующий generation fence, один Core и один TUN owner. Начни с current-code regression, реализуй только недостающие исправления и прогони реальные focused/cross-boundary tests. Заверши IMPLEMENTATION_VERIFIED на I3 с evidence и отдельным списком physical I4 checks; при недоступной обязательной среде — честный BLOCKED и handoff, не цикл. POST12, production, публикации и изменение public AWG scope запрещены.
```

**Завершение:** проверены конкретные инварианты и тесты. Отсутствие физического телефона не позволяет объявить I4, но не требует продолжать бесконечно менять уже проверенный код.

## 5. Независимая goal — checkout и payment truth

Допустима параллельно с предыдущей только в отдельном write set/worktree и без одновременного редактирования общего schema owner.

```text
/goal Выполни локально R12-B01–B05 из итогового POKROV пакета с учётом 00/01/03/09 и текущего canonical payment contract. Закрой invalid/stale quote readiness, синхронную invalidation при изменении ввода, честный payment return, bounded reads и идемпотентный order intent. Сначала воспроизведи current HEAD; уже исправленное сохрани как regression. Результат: актуальный server-valid quote перед create, неизменяемый local order, поздние ответы и повторы не меняют цену/источник и не создают дубль. Нужны реально выполненные unit/integration/критические UI tests. Только локальные/sandbox fixtures, без реальных оплат, возвратов, deploy, рекламы и /t/ интеграции. Заверши I3 evidence либо BLOCKED с точным недостающим условием; это не завершение релиза.
```

## 6. Платформенная приёмка — отдельные ограниченные цели

Не делать один бесконечный goal, ожидающий всех устройств. Для каждой платформы сначала установить, какая разрешённая среда реально подключена, затем пройти её матрицу. Остальные строки остаются открытыми.

```text
/goal Пройди применимые Windows checks R12-W01–W06 из файлов 02/03/09 POKROV на доступной разрешённой clean VM/host и exact candidate artifact. Проверяй standard-user UI, installed service, TUN/DNS/routes, crash/sleep/network change, update/uninstall и восстановление только owned state. Reuse старого evidence — только по G03. Не меняй домашнюю/production сеть вместо test host; не объявляй Ed25519 manifest доверенной Authenticode-подписью. Результат — bounded matrix с hashes, фактическими командами, verdicts и teardown. Недоступные hosts — NOT_RUN; блокер — отчёт и остановка, не fake PASS. Без публикации и post-release функций.
```

```text
/goal Пройди применимые Android checks R12-D01–D05 из файлов 02/03/09 POKROV на реально доступном разрешённом устройстве и exact primary APK. Проверь signer/package/versionCode, install/upgrade, VPN permission, DNS/IPv6/routing, Wi-Fi/mobile, Doze и recovery. Не подменяй physical ARM64 proof результатом universal APK или LDPlayer. Чужие банковские операции и реальные платежи не выполнять. Результат — exact-artifact matrix, фактически выполненные проверки, privacy-safe evidence и cleanup. Недоступные OEM/origins — NOT_RUN/BLOCKED, не расширение claims и не бесконечные попытки. Public release не выполнять.
```

Небольшое исправление обнаруженной регрессии — собственный WO, после него инвалидировать только затронутое evidence. Не пересобирать всё из-за обновления отчёта.

## 7. Админка, UX и оптимизация

Выбирать конкретные slices из O/F/C/V. Нельзя объединять этот поток с новой транспортной архитектурой или делать четвёртую админку.

```text
/goal Доведи существующие R12-O03/O04/O05 и связанные read-only UI projections по файлам 02/03/09 POKROV. Оператор должен различать requested/effective/proven connection, observation/hypothesis, устаревшие данные и фактическое завершение guarded action/rollback. Используй существующие Operator Center, RBAC и API contracts; не создавай новый shell. Работай по принятому write set, проверь role-negative cases и реальные browser scenarios на fixtures/staging, где разрешено. Заверши конкретным before/after и evidence; authenticated production без доступа остаётся NOT_RUN. Без реальных destructive commands, deploy и рекламы.
```

Оптимизацию назначать отдельным goal с baseline и измеримым узким результатом: например, уменьшение лишних rebuild на runtime ticks без изменения connection semantics. «Сделать в десять раз быстрее» без reference workload не является acceptance.

## 8. Финальный release goal не равен local goal

Q01–Q03 готовят точную acceptance matrix и go/no-go; Q04–Q05 выполняют отдельно разрешённые publication/rollout/observation. Один goal `IMPLEMENTATION_VERIFIED` не активирует post-release.

Для Q01–Q03 достаточно обычной команды или bounded goal, указывающей точный approved scope. Команду публикации здесь намеренно не выдаём как автоматически безопасную: нужно назвать реальные artifact hashes, channel, разрешённые среды/пользователей, rollback и конкретное owner authorization. Просто «сделай релиз» недостаточно.

## 9. После закрытия 1.2.0 — общий контракт, затем независимые цели

Ниже команды **заблокированы исходным activation gate**, пока release 1.2.0 не закрыт своим процессом либо владелец явно не изменил последовательность. Копирование файла агентом не является таким решением.

### Общая архитектура — POST12-00/05

```text
/goal После подтверждённого activation gate выполни POST12-00/05 по файлам 00/01/04/09 POKROV: exact baseline, общие Evidence/Connectivity Proof/Broker anti-poisoning/offline entitlement/selector/Smart Access safety contracts и deterministic fixtures. Переиспользуй существующие schema/state owners; не делай параллельные runtime engines. Сначала обязательное ядро ATS-001–007/010/013/014 и scoped ATS-015/016. Android visibility/AWG matrix — только необходимые для выбранного scope; MASQUE/two-hop могут закончиться DEFER/NO-GO и не блокируют ядро. Результат — reviewable ADR/RFC, тесты и bounded implementation WOs, не декларация готового ATS. Реальные server/cohort/privacy/product изменения требуют своего разрешения.
```

### AWG — безопасный первый вертикальный slice

```text
/goal При выполненных activation и shared-contract gates реализуй только выбранный CR-010–012 AWG scope из файла 05 POKROV: exact userspace client/server pins, поддерживаемый typed contract, effective profile, payload/DNS/egress и bounded TCP fallback. Начни с cookie protection enabled и обязательной header protection. До DisableCookies=true отдельный review upstream underload fix b5928ef и подтверждённая isolated-lab authorisation; без неё experiment DEFERRED. Не расширяй MTU/поля по устаревшим fixtures, не меняй digest вместо проверки compatibility. Результат — source tests и доступное exact lab/device evidence с отдельными незапущенными строками. Без public/default enable и без второго TUN.
```

Сам запуск удалённого сервера, вмешательство в firewall и нагрузочное испытание не разрешаются общими словами этой goal. Они требуют заранее указанной owned isolated среды, потолков и stop/cleanup процедуры.

### Smart Routing — первый ограниченный продуктовый результат

```text
/goal После activation gate выполни согласованный первый slice POST12-20 по файлу 06 POKROV: единый versioned catalog и deterministic routing policy, локальная Android package identity проверка, запрет auto-bypass браузеров, подпись/LKG/negative fixtures и preview области маршрутизации. Не отправляй app inventory на backend и не меняй текущий default режима. Для Smart Access достаточно выбранного owned/одобренного provider и проверенного service subset; все три внешних провайдера не являются искусственным prerequisite. Результат — scoped implementation/test evidence, не массовое включение. Новая telemetry, внешние provider нагрузки и production требуют отдельных gates.
```

### `/t/` — отдельная небольшая цель

```text
/goal После activation gate выполни локально T-01–T-08 POST12-40 из файла 07 POKROV. Сохрани static marketing: динамический /t/<slug> через Caddy/FastAPI и existing acquisition service. Реализуй immutable placement после publish, safe 302/no-store, verified first-party receipt без второй identity системы, immutable order attribution snapshot и корректные метрики. Нужны redirect/forgery/replay/open-redirect/Postgres/payment-lineage tests, включая заказ A и последующий touch B. Trial, Telegram reward, referral и цены не менять. Не покупать рекламу и не публиковать placement. Заверши I3 и отдельным T-09 live smoke handoff либо честным BLOCKED.
```

## 10. Как продолжать без зацикливания

В одном thread сохранять небольшой checkpoint: текущая цель, завершённые IDs, изменённые файлы, команды/результаты, один следующий шаг и блокеры. При `BLOCKED` остановить/поставить goal на паузу и передать точное необходимое действие; нельзя имитировать непрерывное фоновое исполнение.

Новая цель начинает с checkpoint, а не перечитывает тысячи строк и не генерирует заново все WOs. Не активировать два runtime writers одновременно. Не ослаблять тест, чтобы уложиться в goal, и не выдавать owner waiver за PASS.

**Практический старт:** раздел 3 сейчас; после его результата — разделы 4 и 5 в независимых областях. Остальные цели запускать по готовности зависимостей, не все одним сообщением.

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

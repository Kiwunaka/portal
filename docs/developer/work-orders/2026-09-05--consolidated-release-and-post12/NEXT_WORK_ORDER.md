# Первая исполнимая очередь после стартовой сверки

Состояние на 2026-09-05: очередь запущена командой владельца «Выполняй все этапы». Результаты и оставшиеся gates — в [отчёте исполнения](EXECUTION-LOCAL.md). Ниже сохранены исходные scoped work orders; их нельзя читать как отметку о полном закрытии parent ID.

## WO-R12-N01A — обычный Windows reconnect обновляет assignment

Parent: R12-G01/G03, R12-N01/N02; соседние N03/N04 не получают автоматического PASS. Цель: обычный reconnect получает текущий server-managed revision и применяет его либо явно оставляет изменение неприменённым. Сохранить Android refresh, bounded offline fallback, один Core и host TUN owner.

Baseline: client `da1ad7395615837432615e0f150d7c0bf05322a4`, platform `6b41f758ca228a0d5ff13ede0f865096cdac2134`; источник gap — [сверка](SOURCE_RECONCILIATION.md). Создать отдельную client feature branch/worktree от проверенного main. Core runtime binding брать из client seed, не подменять текущим Core HEAD.

Read set: client AGENTS/router, bootstrap/persisted-state/privilege contracts, seed shell, runtime engine stage/start interfaces, existing app-shell tests. Write set: `packages/app_shell/lib/src/shell/seed_shell.dart`, ближайший существующий shell regression test, `docs/architecture/bootstrap-workflow.md`. Расширять до runtime adapter/producer только если тест покажет, что текущего ACK недостаточно; зафиксировать этот конкретный gap до cross-repo изменения.

Порядок: воспроизвести stale staged Windows path synthetic fixture; сделать минимальный refresh fix; проверить stage failure и transient fallback, смену input revision во время stage; сохранить Android поведение. Простой local counter нельзя назвать server-effective revision.

Команды из нового client worktree:

```powershell
# cwd: packages/app_shell
flutter test test/pokrov_seed_app_test.dart test/app_first_runtime_bootstrap_test.dart test/cached_profile_fallback_gate_test.dart test/connection_experience_test.dart
flutter analyze
# cwd: client root
pwsh -NoProfile -File ./scripts/validate-seed.ps1
git diff --check
git diff --name-only -- artifacts/releases
```

Oracle: второй connect после server assignment change выполняет fetch и stage новой разрешённой ревизии; failure не выставляет новое effective/protected. Повтор/late callback не подтверждают чужой профиль. Existing cached-profile rejection после dataplane failure сохраняется.

Terminal: `IMPLEMENTATION_VERIFIED / I3` только для доказанного N01A. N02 transaction/restart, N03 full route proof и N04 probe-race остаются отдельными oracle. I4 — exact packaged candidate на Windows VM, AWG31→AWG2→AWG31, effective service profile readback, restore baseline. Эти проверки здесь `NOT_RUN`; host tunnel не заменять. Rollback: отмена scoped source diff в своей ветке; retained candidate.33 bytes остаются неизменными.

## WO-R12-N04A — проверить и закрыть probe fencing gap

После N01A либо отдельно при непересекающемся write set. Read set: `AndroidCoreOperationalEvents`, `AndroidCoreEgressProbe`, `PokrovRuntimeVpnService`, Core event producer и связанные JVM tests. Write set первоначально только существующий `AndroidCoreEgressProbeTest.kt`; production patch — только при воспроизведении неверного acceptance. Если нужен producer correlation contract, определить producer→consumer compatibility и последовательный merge до изменения ABI.

Oracle: delayed success от target A после запуска B в той же attempt не делает B healthy. Outer run/attempt/generation/sequence fence не ослабляется; verifier unavailable не объявляется утечкой. `AndroidCoreOperationalEventsTest`, `AndroidCoreEgressProbeTest`, `AndroidCoreEgressFailClosedPolicyTest` запускать через существующую Android Gradle task из `scripts/run-tests.ps1`; затем общий `pwsh -NoProfile -File ./scripts/run-tests.ps1` при host contract change. До проверки test task/toolchain не присваивать I3.

## WO-R12-B01A — preview validity и честный legacy return

Независимый platform slice, parent R12-B01/B02/B03; начало от platform HEAD baseline в отдельной ветке. Authorization class для исполнения: `LOCAL_IMPLEMENTATION`, synthetic localhost, без provider запросов. Не менять цены, тарифы, entitlement, callback authentication и public flags.

Read set: payment canonical owners, `marketing/src/app/checkout/checkout-client.tsx`, `portal_bot/api_payment_routes.py`, `payment_return_service.py`, `tests/test_api_payments_callbacks.py`, marketing browser-check scripts. Write set: перечисленный checkout и legacy route, минимальные regression fixtures в существующих test surfaces, payment owners. Cabinet менять только при воспроизведённом таком же gap.

Порядок: failing browser fixture invalid preview без promo; stale promo/subject quote на интервале <250 ms; submit guard и late-response fence; затем legacy success presentation без неподтверждённого paid. Проверить token/subject/deadline binding по текущему server contract: клиент не придумывает authority. Expiry и input change сразу делают quote непригодным; debounce задерживает только новый запрос.

Oracle: matching invalid preview без promo блокирует CTA и submit; изменение plan/promo/subject/provider/currency инвалидирует прежний quote; валидный свежий server quote разрешает оплату ровно своей суммы; прямой GET `/pay/success` не утверждает получение денег. Server-confirmed paid продолжает отображаться как paid.

Команды из platform root и marketing:

```powershell
python -B -m pytest -p no:cacheprovider tests/test_commercial_offer_service.py tests/test_payment_return_service.py tests/test_api_payments_callbacks.py -q
python -B -m pytest -p no:cacheprovider portal_bot/tests/test_email_auth.py tests/test_api_payments_callbacks.py tests/test_lavatop_payment_providers.py tests/test_payment_email_readiness_smoke.py -q
# cwd: marketing
npm.cmd run build
npm.cmd run check:seo
npm.cmd run check:responsive
# cwd: platform root
python -B -m pytest -p no:cacheprovider tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py tests/test_marketing_governance.py tests/test_winback_pilot.py -q
git diff --check
```

Существующие marketing scripts и package.json прочитаны; `marketing/e2e/` и `npm test` не существуют, их нельзя выдавать за готовую suite. Для race нужна небольшая исполняемая browser fixture на localhost с задержанными synthetic responses; source substring test её не заменяет. Указать точную команду fixture в отчёте реализации.

Terminal: I3 только после локальных oracle и применимых router checks. Provider live callback/refund/reconciliation остаются отдельными B06 gates. Rollback: scoped source diff, без DB migration и без перезаписи заказов.

## WO-R12-B04A — bounded reads и безопасный retry mutation

Parent R12-B04/B05, после B01A. Сначала отделить применение catalog/provider state от optional acquisition и ограничить read-only fetch deadlines. Затем исследовать create-public timeout-after-commit на HTTP boundary с existing immutable order/reservation machinery. Не добавлять автоматический повтор POST до доказанного same-intent recovery.

Write set: checkout fetch helpers, существующие payment order/commercial service boundaries только по доказанному пробелу, их тесты и payment state owner. Required tests: `tests/test_payment_order_service.py`, `tests/test_commercial_order_service.py`, `tests/test_payment_return_service.py`, соответствующий HTTP fixture. Две вкладки, повтор после timeout, поздний callback, provider failure и reservation race — отдельная disposable PostgreSQL проверка; SQLite PASS её не заменяет. Точный fixture runner выбрать из repository scripts, не использовать live credentials.

Oracle: hanging acquisition не задерживает цены; every read settles/aborts в бюджете; late response не меняет новый input; retry возвращает тот же order или reconciliation state и не вызывает повторное начисление. Terminal I3 ограничивается реально выполненной suite; отсутствие PostgreSQL оставляет concurrency gate blocked. Rollback/migration расширяются только если реализация действительно меняет schema.

## Остальная очередь

G02 retention уже имеет 10/10 local byte matches; G04 требует исполняемый hosted CI, G05–G07 — текущие metadata/enforcement/lane readbacks перед новым candidate. Остальные R12, пострелизные ATS/CR/WP, HAPP и `/t/` сохранены в импортном пакете и [реестре](R12-REGISTER.csv). Их подробная сверка выполняется при выборе следующего результата. Этот документ не запускает production, сборку релиза, canary, spend или рассылку.

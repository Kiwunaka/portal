# Сверка ближайшей очереди

Baseline и SHA каждого репозитория — [BASELINE.md](BASELINE.md). Ниже source review текущих promotion HEAD; где тест не запускался, статус I1 не означает воспроизведение на устройстве.

## R12-G01/G03

G01: `PARTIALLY_FIXED / I1`. Реальные roots, authority, freeze и первая очередь зафиксированы. Запрос владельца исполняет первый этап нового плана. Нового публичного channel/scope решения и release resume нет; прежний freeze остаётся историческим основанием. G03: `PARTIALLY_FIXED / I1`; карта invalidation подготовлена для следующего diff. Exact-candidate acceptance будет привязана к фактическому будущему write set, не ко всем 83 строкам сразу.

## R12-N01/N04

| ID | Inventory | Текущий код и наблюдение | Следующая проверка |
| --- | --- | --- | --- |
| N01 | `STILL_PRESENT / I1` | Client `packages/app_shell/lib/src/shell/seed_shell.dart:5025`, `_toggleRuntimeInternal`: refresh обязателен при dirty/нет staged path, а connect/reconnect принудительно refresh только на Android. На Windows prepared path переиспользуется. Client `docs/operations/cutover-readiness.md` отдельно сохраняет exact candidate.33 AWG2 assignment → AWG3.1 revision при обычном reconnect. | Synthetic Windows regression: server assignment меняется, обычный reconnect должен получить новый разрешённый revision; затем exact managed VM. |
| N02 | `PARTIALLY_FIXED / I1` | Там же: ожидание quick-settings invalidation, локальный `_managedProfileRevision`, проверка revision после stage, transient-only cached fallback уже существуют. Это не полная цепь server assigned → effective runtime ACK и не доказательство crash-safe commit/rollback. | Смена assignment во время fetch/stage, late callback, stage failure, restart между checkpoint/commit. Не вводить вторую state machine без установленного gap. |
| N03 | `NEEDS_RUNTIME_PROOF / I1` | Android `AndroidCoreEgressProbe.kt:83`, `finalTarget` выбирает `route.final`; URL test и host fail-close существуют. Это не proof реального in-scope пользовательского процесса, всех IP families и effective service-profile identity. | Привязать runtime ACK и свежий proof к effective target; scoped host/process matrix отдельно I4. |
| N04 | `PARTIALLY_FIXED / I1` | `AndroidCoreOperationalEvents.kt:70`, `accept` уже проверяет run/attempt/generation/sequence. `AndroidCoreEgressProbe.kt:175` допускает один endpoint handler через CAS; `acceptEndpointResult` принимает имя/outcome/error от разрешённого outer event. Отдельной идентичности probe/target в этом predicate нет. | Проверить late result предыдущего probe в той же attempt при новом target. Наличие race не воспроизведено; новый production-баг не заявлен. Сохранить существующий outer fence. |

Существующие regression surfaces: `packages/app_shell/test/pokrov_seed_app_test.dart`, `app_first_runtime_bootstrap_test.dart`, `cached_profile_fallback_gate_test.dart`, `connection_experience_test.dart`; Android `AndroidCoreOperationalEventsTest`, `AndroidCoreEgressProbeTest`, `AndroidCoreEgressFailClosedPolicyTest`. В этом старте Flutter/JVM tests не выполнялись.

Canonical owners: client `docs/architecture/bootstrap-workflow.md`, `docs/architecture/persisted-state-contract.md`, `docs/architecture/platform-privilege-runtime-contract.md`, `docs/operations/cutover-readiness.md`. Core ABI и единственный TUN owner сохраняются.

## R12-B01/B05

| ID | Inventory | Source finding на platform HEAD | Проверка/граница |
| --- | --- | --- | --- |
| B01 | `STILL_PRESENT / I1` | `marketing/src/app/checkout/checkout-client.tsx:760`: `promoAccepted = !promoCode || ...`; `checkoutReady` требует matching plan/revision, но не безусловные `valid` и token. Невалидный preview при пустом promo может разрешить CTA; price fallback через `Math.max(1, ...)` может показать 1 ₽. | Нужно проверить DOM/submit с matching invalid preview без promo. Это UI-дефект, не доказанный обход server payment authority. |
| B02 | `STILL_PRESENT / I1` | Там же `:782`: pending и очистка preview находятся внутри `setTimeout(...,250)`. `previewMatchesPlan` сравнивает только plan и commercial revision; зависимости эффекта не содержат provider/currency. | Изменить promo/subject при уже valid quote и нажать до 250 ms; late response после новой input generation не принимается. |
| B03 | `PARTIALLY_FIXED / I1` | Новый `/api/payments/orders/status` и checkout polling используют server state. Но `portal_bot/api_payment_routes.py:17`, GET `/pay/success`, без lookup возвращает «Оплата подтверждена»; POST возвращает status success. | Исправить legacy presentation; не ломать callback transport и не выдавать доступ из redirect. Существующие return-service tests проходят, legacy маршрут ими не закрыт. |
| B04 | `STILL_PRESENT / I1` | В checkout `fetchCatalog`, provider/preview/status/order helpers используют fetch без AbortSignal/deadline. Mount `Promise.allSettled` ждёт optional acquisition до применения catalog/provider state. | Hung acquisition не задерживает обязательные данные; abort/deadline и stale-response suppression. Mutation timeout проверять только вместе с B05, без слепого fallback POST. |
| B05 | `PARTIALLY_FIXED / I1` | `commercial_order_service.py:377`, `bind_commercial_offer_to_order`, и `payment_order_service.py` уже сохраняют reservation/immutable intent; exact retry предусмотрен. Public create API принимает optional offer token; маркетинг не передаёт отдельный стабильный create intent. | Не строить второй payment engine. Проверить same-intent retry через HTTP boundary при timeout после commit и две вкладки. Полная PostgreSQL concurrency не доказана. |

`python -B -m pytest -p no:cacheprovider tests/test_payment_order_service.py tests/test_commercial_offer_service.py tests/test_payment_return_service.py -q`: **29 passed**, exit 0, новый локальный прогон. Он доказывает только включённые service fixtures; `test_commercial_order_service.py` и HTTP/PostgreSQL/браузерные сценарии в эту команду не входили. Общий B05 остаётся I1 для незакрытого сквозного oracle; покрытые сервисы имеют отдельный local PASS.

Canonical owners: platform `docs/product/payment-and-access-key-contract.md`, `docs/architecture/payment-state-machine.md`; серверная проверка цены, reservation, subject и provider остаётся authority.

## Связи с сохранённым ledger

Это связи требований, не перенос статусов и не заявление об эквивалентности объёма:

| Новые ID | Сохранённые `(plan,id)` |
| --- | --- |
| G01/G03/G04 | REL_DOD/DOD-01, REL_DOD/DOD-09 |
| N01/N02 | FE/P12-110, REL/WIN-004 |
| N03 | REL/STATE-001, REL_DOD/DOD-07, FRKN_ADOPT/ADOPT-01, OBS_DOD/DOD-03 |
| N04 | OBS/OBS-009 |
| B01/B02 | FE/P12-014 |
| B03 | FE/P12-013 |
| B04/B05 | REL_DOD/DOD-08, FE/P12-014 |

Все остальные исходные строки сохранены через [LEGACY-378-REFERENCE.csv](LEGACY-378-REFERENCE.csv). Несверенные R12 остаются очередью; Linux/HAPP/AWG public/ATS/Smart Access не активируются из приоритета P0 чужой области.

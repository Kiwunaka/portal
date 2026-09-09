# Исполнение локальной очереди R12 — 2026-09-05

Продолжение и более свежие Core/PostgreSQL/Windows результаты — в [новом отчёте](EXECUTION-CONTINUED.md). Нижние записи сохраняют исходную временную границу.

Общий outcome: `PARTIAL / RELEASE_BLOCKED`. Решение по обычному quote получено и реализовано; см. дополнение ниже. Команда владельца «Выполняй все этапы»
принята как продолжение исполнения плана. Все 83 R12 ID и 378 сохранённых ID
остаются в реестрах; этот отчёт не объявляет их выполненными. Production/release:
`BLOCKED`, нового candidate, commit, push, merge, deploy или публикации нет.

## Изменения

| Область | Реальный результат | Граница |
|---|---|---|
| N01A/N02 | Windows и Android получают свежий managed profile при connect/reconnect. Ошибка, пустой ответ, отсутствующий путь и отказ staging не подменяются старым snapshot. Read-only transient fallback отделён от неизвестного результата staging. | Не доказаны server-effective revision, durable rollback и packaged AWG cycle. |
| N04A | Воспроизведено ложное HEALTHY от старого endpoint-события. Core добавляет bounded per-call `ProbeEndpoint`; Android принимает результат именно своего вызова. Outer session/generation fences сохранены. | В старом AAR метода нет: host возвращает UNAVAILABLE. Новый AAR, binding и device proof ещё нужны. Group URL-test и весь N04 не получают общего PASS. |
| B01/B02/B03 | Invalid/tokenless/expired preview блокирует CTA и submit; input change инвалидирует quote до debounce. Поздний preview не возвращает старый токен. Legacy success URL не подтверждает оплату. | Реальный base checkout без promo требует решения ниже. |
| B04 | Единый 8s read budget на все API bases, отмена/debounce key read, независимый optional acquisition, явный read retry и безопасные ошибки. | Это localhost synthetic proof, не WAN/provider SLA. |
| B05 | UUID intent_id для base-price API запросов использует существующий immutable order, owner scope и PostgreSQL xact lock. Exact retry возвращает status/token без второй provider invoice; changed inputs → 409. Commercial retry использует имеющуюся reservation. Browser не повторяет POST автоматически и фиксирует исходный intent при ручном retry. | SQLite не доказывает PostgreSQL concurrency. Legacy unkeyed requests не дедуплицируются; expired commercial retry всё ещё подчиняется текущей server validation. |

## Проверки

- PASS: `python -u -B -m pytest -p no:cacheprovider -o faulthandler_timeout=60 tests/test_payment_order_service.py tests/test_commercial_order_service.py tests/test_payment_return_service.py -q` — 32 passed.
- PASS: `python -u -B -m pytest -p no:cacheprovider -o faulthandler_timeout=60 portal_bot/tests/test_email_auth.py tests/test_api_payments_callbacks.py tests/test_lavatop_payment_providers.py tests/test_payment_email_readiness_smoke.py -q` — 123 passed, 14 subtests, 19 deprecation warnings, 600.19s.
- PASS: `python -B -m pytest -p no:cacheprovider tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py tests/test_marketing_governance.py tests/test_winback_pilot.py -q` — 39 passed.
- PASS: `npm.cmd --prefix marketing run build`, `npm.cmd --prefix marketing run check:seo`, `npm.cmd --prefix marketing run check:responsive`. Последняя suite включает 8 исполняемых checkout scenarios в `marketing/scripts/check-checkout-authority.mjs`: invalid, missing-token, expiry, input-race, optional-acquisition, read-timeout, key-race, mutation-retry. Все ответы synthetic; provider не вызывался.
- PASS: Core `go -C engine/sing-box test -count=1 ./daemon ./experimental/libbox`; `pwsh -NoProfile -File scripts/verify-abi-contract.ps1`. Toolchain Go 1.25.13. ABI descriptor check: desktop=2, events=1.
- PASS: focused Android Gradle direct tests `*AndroidCoreEgressProbeTest`, `*AndroidCoreOperationalEventsTest`, `*AndroidCoreEgressFailClosedPolicyTest`; regression первоначально FAIL, после исправления PASS.
- PASS: client `pwsh -NoProfile -File scripts/validate-seed.ps1 -CoreRoot E:/r12core-bound -PlatformRoot C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start` — включая docs, version/facts/observability parity, hygiene. CoreRoot здесь exact retained cd8f0f4, а не новый producer diff.
- PASS: client `pwsh -NoProfile -File scripts/run-tests.ps1` — 585 Flutter tests, один существующий skip exact-DLL backtest, analyze трёх testless modules, Gradle `:app:testDirectDebugUnitTest :app:testStoreDebugUnitTest`. Все assertion failures предыдущих попыток исправлены через реальные stage acknowledgements в synthetic mocks; production notification warning не блокирует успешное stage.
- PASS на момент записи: `git diff --check` platform/Core; package validator сохраняет 13 import hashes, 83 ID, 378 legacy ID и ссылки. Финальные checks после отчёта записываются отдельно.

Первый объединённый Python-прогон был прерван до результата после долгого отсутствия
вывода. Он не засчитан. Повторные раздельные suites завершились; API suite занимает
около 10 минут. Отсутствовавшие Android wrapper/toolchain paths восстановлены через
существующий bootstrap; source code и release binaries этим не заменялись.

## Разрыв обычной оплаты на предыдущем этапе (закрыт дополнением ниже)

`preview_commercial_offer` сейчас возвращает `offer_not_found`, когда promo и offer_id
пусты. Поэтому строгий guard по требованию B01 закрывает обычную оплату без promo.
Восемь synthetic browser scenarios не заменяют этот server contract. У владельца
запрошено: обязательный signed quote распространяется на обычную покупку или только
на commercial offer. До ответа не вводится новая модель base quote/price hold.
Новый base quote должен использовать текущий server pricing, включая referral и
pending discounts, а не дублировать цены на frontend.

## Порядок интеграции и следующие gates

1. DONE LOCAL: решение base quote принято; localhost HTTP→UI проверен, см. дополнение. Production readiness этим не объявляется.
2. Проверить B05 на disposable PostgreSQL: same intent с двух соединений/вкладок, timeout-after-commit, provider failure, late callback/reservation race. Docker API локально недоступен; `docker info` завершился ошибкой missing named pipe. Действующий production DB не использовался.
3. Core producer source → exact replacement AAR/build provenance → client binding и оба Android flavor → packaged candidate. Старый AAR намеренно не получает ложный healthy. Desktop ABI2 не изменён.
4. Backend retry semantics должны попасть на сервер до публикации нового marketing export; mixed-version frontend/backend не доказаны.
5. Новый exact candidate и scoped rollback на retained candidate.33, Windows VM service-effective readback, physical Android, RU-origin/provider/refund и остальные required release gates. Старые source/device receipts не переименовываются в новые PASS.
6. ATS/CR/WP/HAPP/shortlink остаются последующей программой по зависимостям импортного плана. Linux/public AWG/new pool/canary/spend не активированы. Остальные queued ID не проверены этим slice.

## Рабочие каталоги и откат

Platform: `C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start`, branch
`codex/consolidated-plan-start-20260905`; client: `E:/r12client`, branch
`codex/r12-client-implementation`; Core: `E:/r12core-implementation`, branch
`codex/r12-correlated-endpoint-probe`. Exact retained Core read-only checkout:
`E:/r12core-bound`. Original dirty worktrees сохранены.

Откат локальных changes — review и отмена только scoped diff в этих feature
worktrees. Нет DB migration, замены retained release bytes или production mutation.
Generated Next.js `marketing/AGENTS.md`/`CLAUDE.md` остаются локальными untracked
результатами tooling; это не новая root platform authority. Line-ending-only
изменения четырёх Flutter registrants восстановлены только после byte-normalized
равенства исходному HEAD. Evidence candidate.33 сохраняется в прежнем пакете.

## Финальная локальная проверка

PASS: после обновления отчёта повторены package validator (13 hashes, 83 R12 ID,
378 legacy ID, 113 links), 33 documentation/context tests, platform-context audit
и client validate-seed с retained Core. `git diff --check` прошёл в трёх feature
worktrees; `artifacts/releases/**` клиента без diff. Точные результаты добавлены
в `evidence/local-implementation.json`. Commit, push, merge, deploy отсутствуют.

## Дополнение: обычный серверный расчёт — 2026-09-05

Владелец подтвердил обязательный серверный расчёт для обычной покупки без промо.
Этот локальный разрыв B01 закрыт; полного завершения R12 или релиза нет.

- `/api/public/offers/preview` выдаёт отдельный подписанный `bq1` quote без создания
  commercial campaign/reservation. Anonymous email или проверенный ticket определяет
  покупателя. Привязка к покупателю — HMAC; raw email/tg_id в токен не попадают.
- Preview и create используют один `_rub_checkout_pricing`: включая referral,
  pending discount и код из подписанного bot ticket. Новый расчёт не дублирует цены.
- Подпись, срок, активность тарифа, длительность и текущий расчёт проверяются до
  создания заказа/provider I/O. Изменившаяся цена/покупатель → 409, истечение → 410.
  UUID quote повторно находит существующий order, в том числе после истечения
  quote; повторного provider invoice нет. Это не резерв неизменной цены.
- Browser передаёт email в preview. Отклонённый расчёт обновляется; новая оплата
  требует отдельного нажатия. Для использованного `start_99` preview сообщает
  причину, обычный тариф остаётся доступен. Legacy API без quote по-прежнему
  считает цену на сервере; новый marketing UI всегда требует подписанный расчёт.

Проверки:

- PASS: `python -u -B -m pytest -p no:cacheprovider -o faulthandler_timeout=60 portal_bot/tests/test_email_auth.py tests/test_api_payments_callbacks.py tests/test_lavatop_payment_providers.py tests/test_payment_email_readiness_smoke.py tests/test_commercial_offer_service.py tests/test_commercial_order_service.py tests/test_payment_order_service.py -q` — 153 passed, 14 subtests, 19 deprecation warnings, 593.41s.
- PASS: после финальных уточнений HMAC, ticket promo и starter preview повторён `python -u -B -m pytest -p no:cacheprovider tests/test_api_payments_callbacks.py -k 'base_quote or anonymous_start99_rejects' -q` — 3 passed. Сценарии включают missing email, подпись, чужой покупатель, expiry/retry, account discounts, изменившуюся цену и использованный starter.
- PASS: `npm.cmd --prefix marketing run build`, `check:seo`, `check:responsive`. Responsive suite включает девять checkout scenarios; новый `quote-changed` проверяет обновление quote без автоматического POST.
- PASS: 72 frontend copy/governance/docs/context tests; финальный `git diff --check` и package validator.
- PASS current-origin: `node E:/r12-base-quote-browser.mjs` и тот же script с `--mobile`. Chromium 1180×820 и 390×844, реальный localhost FastAPI на disposable SQLite, реальные preview/create, provider заменён fixture. Email → signed 239 RUB → CTA → один вызов synthetic invoice → synthetic provider landing. Нет blank page, framework overlay, page/console errors. API requests проксировались только на localhost, внешние запросы блокировались. Browser plugin not available; использован существующий Playwright согласно frontend-testing-debugging.

Evidence: `evidence/base-quote.json`; скриншоты и диагностические logs retained
локально в `E:/r12-base-quote-*`. Две первоначальные ошибки были в browser harness
(`Response.status` и CORS proxy headers); исправленный harness прошёл. Они не
засчитаны как PASS продукта. Temporary HTTP server остановлен после проверки.

Остаются PostgreSQL concurrency, exact replacement AAR/client binding, новый
candidate, Windows VM/physical Android, RU-origin/provider/refund и последующие
этапы исходного плана. Commit/push/merge/deploy отсутствуют. Рабочий сайт не изменён.

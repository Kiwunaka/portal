# Интегрированный backend — payment acceptance

**PASS_LOCAL_PAYMENT_ACCEPTANCE**, platform `16407b8`, чистый checkout
`E:/r12-integration-platform-20260908`. [Receipt и точные команды](evidence/integrated-backend-20260908/receipt.json).
Это текущая локальная часть B01–B06; provider fixtures не являются provider E2E.

После прежнего B06 менялись API и admin router, поэтому для закреплённого tuple
выполнена актуальная HTTP-проверка: email/auth, payment callbacks, Lava.top
adapter/readiness и admin reconciliation. **129 tests / 22 subtests PASS**, 19
deprecation warnings, 656,14 секунды. Подтверждены duplicate/auth/mismatch,
reversal/manual-review и intent-bound atomic reconciliation в synthetic scope.

Отдельно реальные конкурентные соединения loopback PostgreSQL выполнили
**9/9 PASS** за 72,75 секунды: intent/quote duplicate с success, timeout и
late-paid; same/distinct reservation quota; невозможность забрать активный
outbox claim. Provider I/O заменено fixture; БД настоящая, данные синтетические.
Каждый тест создал новую сохранённую schema в `r12_checkout_rehearsal`.

Первый PostgreSQL запуск дал девять setup errors: прежний локальный сервер был
выключен. Стенд запущен из существующего `E:/r12-postgres-data` с явными
`127.0.0.1:55439`; данные не переинициализировались. После ready повторён только
этот набор. Сервер штатно остановлен `pg_ctl stop -m fast`; финальный status
подтвердил остановку. Первичный failed log и новые schemas сохранены.

Для B08 сравнены девять конкретных Git blobs с `af80ade`: remote backup/restore,
deploy, cutover, models, requirements, db, outbox и оба PostgreSQL tests —
неизменны. Это сохраняет применимость их прежних ограниченных лабораторных
результатов, но не переносит 198 hashes старого deployed payload на текущий API.
Реальная старая application version на expanded schema и production recovery
по-прежнему не проверены.

Реальные payment/refund, binding новых reversal envelopes, partial-refund policy,
deployed operator access/fingerprint, full migration/rolling/contract matrix,
release/signing/channel/observation остаются открытыми. Production mutation,
push, deploy и новый candidate не выполнялись. Ранее принятые owner skips не
переоткрываются и не превращаются в PASS.

Evidence hash/size readback PASS. Проверки platform docs/context: 33 tests PASS;
context audit PASS; package validator — 83 ID, 378 legacy references и 338
local links PASS; `git diff --check` PASS. Никакой продуктовый код не менялся.

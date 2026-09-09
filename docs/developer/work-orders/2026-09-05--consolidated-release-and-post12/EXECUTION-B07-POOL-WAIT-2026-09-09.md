# B07 — ожидание соединений БД и HTTP

**R12-B07: verified / I5 в исходном объёме критерия.** [Receipt](evidence/b07-pool-wait-20260909/receipt.json)
сохраняет exact source, failures, runtime observations и hashes.

В `78f5977` добавлены отдельные измерения очередей соединений. Прежний
`payment_db.queue_wait` измеряет очередь AnyIO-потоков; это сохранено и явно
отделено от PostgreSQL queue в новом `database_pool` health field.

## Семантика

Новый ObservedQueuePool использует `_queue_class` закреплённой SQLAlchemy
2.0.46. Таймер охватывает только blocking get очереди; создание соединения,
pre-ping и SQL остаются вне него. Blocking get может сразу получить свободное
соединение — поэтому поле называется attempts. Учитываются текущие/максимальные
ожидания, timeout и total/max milliseconds. Все поля целочисленные, без SQL,
идентификаторов и exception text. Лимиты 5 + 10 / 30 секунд не менялись.
SQLite сохраняет прежний pool и возвращает null; пересоздание PostgreSQL pool
сбрасывает его собственные counters.

HTTP использует aiohttp queue start/end и отдельный контекст каждого запроса.
В существующие безопасные events и rollups добавлены queue entries и wait.
Незавершённое ожидание учитывается при timeout/cancellation. DNS, создание
соединения и чтение ответа не включены. Пять lifespan clients и лимиты прежние.
Основание реализации: [aiohttp tracing](https://docs.aiohttp.org/en/stable/tracing_reference.html)
и [исходник SQLAlchemy 2.0.46](https://github.com/sqlalchemy/sqlalchemy/blob/rel_2_0_46/lib/sqlalchemy/pool/impl.py).
Новый SQLAlchemy internal hook требует повторной проверки при обновлении
зависимости; saturation/timeout regression выполняет настоящий QueuePool.

## Проверки на Brain

Production `1ef1f50` перед изолированным прогоном совпал по 204 hashes.
Четыре candidate modules размещены отдельно; их hashes сохранены. PostgreSQL
использует существующую восстановленную БД `portal_r12_20260909_rehearsal`,
выбранную только в памяти процесса. `init_db` не вызывался, production DB
и исходники не менялись. Запас соединений перед тестом: 100 total / 3 reserved /
15 used. Версии: Python 3.10.12, SQLAlchemy 2.0.46, aiohttp 3.13.3,
Starlette 1.6.0, AnyIO 4.14.2.

- Создание 15 соединений штатного 5+10 pool: queue attempts=0. Шестнадцатое
  ждало освобождения и зарегистрировало 50 мс; после возврата waiting=0.
- Отдельный fixture pool с timeout 150 мс вернул прежний TimeoutError;
  timer записал 150 мс, timeouts=1. Production limit не менялся.
- Кандидатный `SELECT 1/0` через worker/transaction boundary завершился ошибкой;
  rollback и возврат соединения подтверждены новым SELECT 1, checkedout=0.
- 25 HTTP-запросов loopback fixture использовали максимум 20 соединений;
  пять попали в очередь. Финальный total wait 155 мс, max 31 мс.
- Отмена ожидающего запроса: 25 мс / cancelled. Timeout: 150 мс / timeout.
  Ответ сверх лимита отклонён как response_too_large. Все sessions закрыты.

Первые Linux-прогоны остановились на timeout assertion. На Python 3.10
`asyncio.TimeoutError` не является builtin TimeoutError; aiohttp exception
наследует первый. Прежняя ветка записывала `client_error`. Отдельный прогон
старых exact bytes подтвердил это после 100 мс ожидания. Обработчик теперь
принимает оба типа; тот же сценарий на Brain прошёл. Локальный Python 3.12
объединяет эти типы и не обнаруживал этот дефект. Все failures сохранены;
успешные DB части раннего прогона ограничены неизменными hashes DB modules.

## Инвентарь и локальная проверка

Актуальный AST-инвентарь — 16 прямых ClientSession sites; managed payment
registry учитывается отдельно. Новый относительно сентябрьского инвентаря
`support_case_context.check_lava_invoice` — GET счёта из owner-bound order,
constructor total timeout 6 с, redirects=False и bounded response reader.
Это отдельный support flow; без наблюдаемого bottleneck pooling не менялся.
В инструментарии сравнения исправлен пропущенный class scope PanelClient;
сам этот constructor не является новым.

Четыре регрессии до реализации — FAIL. Финальные
`python -B -m pytest -p no:cacheprovider tests/test_payment_db_runtime.py tests/test_payment_http_registry.py -q`
— 15 PASS / 4,06 с. Documentation tests — 33 PASS; context audit и diff check PASS.
Первый общий backend run прерван после исправления реального Python 3.10 дефекта,
он не считается PASS. Итоговый backend/provider прогон финальных bytes: 262 tests +
30 subtests PASS, 1279,15 с. Команда: `python -u -B -m pytest -p no:cacheprovider
portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py
tests/test_api_auth_and_tickets.py tests/test_subscription_preview_api.py
tests/test_lavatop_payment_providers.py tests/test_api_payments_callbacks.py
tests/test_payment_entitlement_outbox.py -q`.

Signed [PR #252](https://github.com/Kiwunaka/portal/pull/252):
head `b354dab999c7e2ce1b9d40cb74c768a2ee1a1aae`, tree
`7a3f9d7cacd350eb272955eafc730a0dd6d1b821`, GitHub signature valid.
PR Guardrails и cross-repository contract PASS; release-base-isolation SKIPPED.
К поставке подготовлено 205 файлов; Git и raw deltas — только api.py,
api_public_routes.py, db.py, db_pool_runtime.py и outbound_http.py.
Models/migrations/dependencies и security.py не менялись. Это не новый client
candidate и не перенос полного release gate на текущий tuple.


## Проверяемый объём B07

Критерий [исходного B07](03_RELEASE_BACKLOG_83.md#r12-b07--dbhttpoutbox-bottlenecks-по-профилю)
сопоставляется с конкретными результатами:

| Требование | Доказательство |
| --- | --- |
| Bounded payment threadpool сохранён | Existing limiter/worker path без изменений; 15 focused и 262 backend/provider tests; deployment readback ниже |
| Оставшиеся ClientSession инвентаризованы | Актуальный AST-инвентарь 16 constructors с source hashes и enclosing scope |
| Lifespan clients и HTTP pool wait | Пять managed clients; реальные queue/success/cancel/timeout/oversize/close проверки в Python 3.10 на Brain |
| PostgreSQL pool wait | Actual PostgreSQL queue/release/timeout/rollback, отдельная scalar health projection |
| Event-loop lag | Предыдущие runtime collector и index/shift исправления; новое окно health ниже |
| Outbox age | Retained production status/count/age до и после bounded read |
| Без ненужного ORM rewrite | Меняются только пять runtime files; схемы, pool limits и ORM path прежние |

Эта приёмка не добавляет к B07 новый throughput/SLO или реальные оплаченные
операции. Callback/provisioning и provider readiness относятся к B06; полная
финальная проверка кандидата и длительное наблюдение — к Q01–Q05. Стендовое
ожидание HTTP не объявляется задержкой настоящего провайдера.


## Production — 2026-09-09 13:24 UTC

Signed squash `cd4a8b905a4105707ebad11fd920473f2478cc2c` / tree
`7a3f9d7cacd350eb272955eafc730a0dd6d1b821` развёрнут на Brain.
Четыре завершённых CI для PR и master (Guardrails и cross-repository contract)
PASS; release-base-isolation SKIPPED_NOT_PASS. В предыдущем readback CI ещё
выполнялся и проверка не дала PASS; поставка началась после завершения.

Из exact checkout выполнено:
`python -u scripts/remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --passwords <existing-local-access-file> --backup-retain-count 50 --restart portal-api,portal-bot,portal-helpbot,portal-feedbackbot,portal-worker`
— exit 0. Все 205 deployed hashes совпали; все пять PID сменились,
active / NRestarts=0. Затем только два build metadata fields обновлены;
остальные dotenv values сохранены, дополнительно перезапущен только API.
Его initial process environment содержит `cd4a8b9`; HTTPS health возвращает
новый database_pool. Это не отдельный authenticated `/meta` readback.

Backup `/root/portal_bot.deploy-backups/20260909T132325Z-11288` сохранён:
все 204 прежних файла совпали с `1ef1f50`, новый module отсутствует в копии.
Всего 14 release backup directories, retention 50 ничего не удалил.
Первый collector ошибочно выбирал lexicographic maximum среди файлов и
каталогов как latest_backup; это поле первоначального readback не используется.
Отдельный backup readback проверил фактический путь из deploy log. Все
оригинальные результаты сохранены. Restore в этом успешном rollout не запускался.

32 HTTPS POST status requests / concurrency 16 использовали короткий token
только для случайного заведомо отсутствующего fixture order. Все вернули
ожидаемый 404 payment_return_order_missing. До и после такого заказа нет;
счёт, платёж и вызов провайдера не создавались. В текущей конфигурации rate
limit этого пути 0; настройка не менялась. Token оставался в памяти процесса.

- Payment worker: started +64, completed +32, failed +32. Failed здесь —
  ожидаемые lookup failures отсутствующего заказа, а не сбой оплаты.
- Max active 5; worker queue total 413 мс / max 23 мс. После active=0.
- PostgreSQL blocking queue: attempts/timeout/wait=0 в этом окне;
  соединений хватало. Это наблюдение, не доказательство предела capacity.
- 11 параллельных health samples — все 200, max 113,13 мс. Event-loop cumulative
  lag за окно не вырос (34 → 34 мс); historical max 27 мс не приписывается burst.
- Outbox до/после: pending 0, processing 0, delivered 2, dead_letter 0,
  oldest open age 0. Новых outbox events эта проверка не создавала.

Результат — работающие отдельные timers и bounded deployed read. HTTP
queue saturation подтверждён exact-source loopback на Brain, не provider
traffic. Исходные DB/HTTP timings с проверенными неизменными module hashes
сопоставлены с развёрнутыми bytes; общий ранний FAILED run не назван PASS.
Новые ORM/HTTP lifecycle переписывания, pool-limit tuning и dependency upgrades
не потребовались. B07 закрыт по перечисленному DoD; B06, O01, Q01–Q05 и
сводный план этим результатом не закрываются.


O01 V3 сохранил процесс, raw security.py hash и absolute deadline.
22-й refresh после API restart прошёл в 13:27:21 UTC; anomalies=0.
Idle expiry уже PASS, absolute expiry RUNNING до 02:37 мск 10 сентября.

Platform feature source сохранён в `d295fd9`; deploy source — `cd4a8b9`.
Новый Windows/Android candidate и физические проверки в этом scope не выполнялись.

Evidence checks: 33 docs tests PASS; platform context audit PASS; package
validator 83 R12 IDs / 515 local links PASS; git diff --check PASS.
Все 15 retained captures и 26 внешних source/log hashes повторно сверены.

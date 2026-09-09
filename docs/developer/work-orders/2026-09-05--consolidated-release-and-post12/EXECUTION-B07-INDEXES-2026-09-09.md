# B07 — индексы последних измерений узлов

Исправлены два подтверждённых источника задержки «Моей смены»: выборка трёх
последних health samples и case-insensitive выборка runtime samples для capacity
alerts. Состав ответа и SQL-запросы не менялись. Добавлены два неуникальных
составных индекса в модели и существующие SQLite/PostgreSQL migrations;
канонический порядок поставки описан в monitoring-and-visibility.md.

## Причина и проверка на копии

На production `3478fc4` изолированный read-only профиль показал 7,58 с SQL из
7,85 с общего расчёта. Семь запросов health history возвращали по три строки
после сканирования и сортировки большой таблицы. EXPLAIN подтвердил отсутствие
подходящего составного индекса. В восстановленной БД проявился второй источник:
поиск `lower(node_code)` по runtime history занимал 11–13 с даже при нуле строк.
Это стало основанием для второго индекса.

В `portal_r12_20260909_rehearsal` общий расчёт занял 26 591,73 мс до индексов,
16 286 мс после первого и 404,12 мс после обоих. Во всех трёх успешных прогонах
полный SHA-256 результата одинаков: `c334744ac4b225ee99af718ac2f0a029f710094fedc128ba11c7a75a9cef4ea3`.
Фиксированный `now` задавался только read model; часы и session TTL не менялись.
После исправления EXPLAIN ANALYZE показал backward scans новых индексов:
health 1,132 мс / три строки; runtime 0,213 мс / ноль строк.

Оба индекса создавались на копии через CREATE INDEX CONCURRENTLY и проверены
как valid/ready. Финальные migrations выполнены дважды (813 / 569 мс).
1 638 180 health rows и 743 891 runtime rows при создании индексов сохранены.
Первый профиль с 5-секундным statement budget завершился OperationalError
(точный SQLSTATE не сохранён). Первая загрузка migrations в инструменте
упала из-за отсутствующего `__file__` уже после создания health index.
Ошибка воспроизведена и исправлена в инструменте; существующий индекс проверен,
без удаления или повторного создания. Эти результаты сохранены отдельно.

## Исходники и проверки

Feature commits `ac8f220`, `a01bca5`; подписанный PR head
`d7d9228953edc7d2cfb2d6a08403de9dd3fccd08`,
[PR #251](https://github.com/Kiwunaka/portal/pull/251), squash
`1ef1f50f76c0529b0efa17a694dd2a5885a475a5`, tree
`8da40f67c653c9fabab6a3293cab3648e4c9b5ac`. GitHub signature valid,
дерево совпадает с локальной интеграцией. В payload 204 файла; относительно
`3478fc4` изменены только models.py и migrations.py, включая raw bytes.

- Missing-index regressions воспроизведены до исправления; итоговые schema,
  migration-helper и metrics проверки: 41 PASS, 128,53 с.
- Integration schema: 4 PASS, 17,29 с.
- `python -B -m pytest -p no:cacheprovider portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py tests/test_api_auth_and_tickets.py tests/test_subscription_preview_api.py -q`: 154 PASS, 8 subtests PASS, 776,66 с.
- Предыдущий backend run с health-only source остановлен после расширения
  исправления. Его частичный результат — INTERRUPTED, не PASS.

## Граница вывода

Сравнение на копии — ограниченные окна, не p95/SLO. Real commercial pool wait
и HTTP connector wait не измерены этой проверкой. R12-B07 остаётся active/I3;
полный план и новый client release candidate не завершены.

## Production — 2026-09-09 12:29 UTC

**PASS_BOUNDED_DEPLOYED_INDEX_FIX**. [Receipt](evidence/b07-indexes-20260909/receipt.json)
содержит 22 проекции с SHA-256 и hashes внешних инструментов/логов.
Четыре выполненных CI (PR и master: Guardrails / cross-repository contract)
PASS; release-base-isolation — SKIPPED_NOT_PASS. Сверка до завершения последнего
CI не дала PASS; повтор после завершения подтвердил exact SHAs и job steps.

До mutation подтверждены все 204 прежних payload hashes, PostgreSQL 14.24,
обычная роль — владелец таблиц, отсутствие новых индексов и других index builds,
14,48 GB свободного места. CREATE INDEX CONCURRENTLY выполнены последовательно
с lock timeout 5 с и statement timeout 120 с: health **9214,54 мс**,
runtime **1525,93 мс**, оба valid/ready. Затем ANALYZE runtime table: 383,58 мс.
Существующие index definitions сохранены; добавлены только два scoped индекса.
Записей бизнес-таблиц этот инструмент не менял. Во время создания все 13 HTTP
health samples дали 200, max 109,42 мс, прирост суммарного loop lag 4 мс.
Порядок concurrent build и обновления статистики следует
[PostgreSQL 14 CREATE INDEX](https://www.postgresql.org/docs/14/sql-createindex.html).

Из exact integration checkout выполнено:
`python scripts/remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --passwords <existing-local-access-file> --backup-retain-count 50 --restart portal-api,portal-bot,portal-helpbot,portal-feedbackbot,portal-worker` — exit 0.
Backup `/root/portal_bot.deploy-backups/20260909T122824Z-3572` сохранён;
прежних копий было 15, retention 50 не удалил их. Source rollout использует уже
готовые индексы. Все пять сервисов получили новые PID, active / NRestarts=0.
Отдельное обновление только двух build metadata keys перезапустило API ещё раз;
остальные значения dotenv и PID четырёх сервисов на этом шаге сохранены.
Все 204 deployed hashes совпали с `1ef1f50`; public API meta вернул тот же commit.

[Сравнение HTTPS окон](evidence/b07-indexes-20260909/runtime-comparison.json):
shift read **6368,37 → 671,96 мс**. Все 11 новых health samples — 200,
max 92,99 мс; loop lag delta 4 мс. Outbox до/после: pending 0, processing 0,
delivered 2, dead_letter 0, age 0. Payment threadpool counters в этом окне
нулевые и не являются результатом платёжной нагрузки. Owned fixture отозван.
Это отдельные bounded окна; p95, нагрузочный SLO и ожидание commercial pools
этим результатом не объявляются пройденными.

O01 V3 сохранил процесс и raw security.py hash через поставку. Idle expiry
уже PASS; абсолютный deadline прежний — 23:37 UTC / 02:37 мск 10 сентября.
[Статус сессии](EXECUTION-OPERATOR-SESSION-BOUNDARY-2026-09-09.md) остаётся
IDLE_PASS_ABSOLUTE_RUNNING; source at start `3478fc4`, текущий backend `1ef1f50`.

Evidence checks: 33 docs tests PASS; platform context audit PASS; package validator
83 R12 IDs / 509 local links PASS. Все 26 hashes retained captures проверены
против staged Git blobs; git diff --check PASS. Windows/Huawei и client release в этом scope
не проверялись. O01 после API restart сохранил 11-й refresh в 12:32:19 UTC.

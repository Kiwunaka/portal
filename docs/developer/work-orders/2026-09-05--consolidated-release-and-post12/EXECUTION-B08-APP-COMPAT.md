# R12-B08 — previous/current API на общей PostgreSQL

Дата: 2026-09-06. B08 целиком: **I3 / NEEDS_RUNTIME_PROOF**.
Продолжение [remote restore](EXECUTION-B08-REMOTE-PG.md).
Команды, source hashes и результаты:
[evidence/b08-app-compat.json](evidence/b08-app-compat.json).

## Выбранные исходники

- Previous: `f5300053026d32826e54c02202303e1f68c65bc1`, platform source
  candidate.33 из сохранённого G03 source record; 197 runtime input files.
- Current: `7d83e290459fe0078cffed20306c794d861153ca`, текущая feature branch;
  198 runtime input files.

Оба payload экспортированы из Git objects в отдельные архивы, без доступа к
соседним worktrees. SHA каждого исходника повторно проверен в госте после
прогона. API source не изменялся. Четыре штатных script helpers также помещены
под `portal_bot/`, как в backend deploy mapping.

`models.py`, `migrations.py`, `db.py` и pinned `requirements.txt` побайтно
одинаковы между previous/current. Нового schema migration или contract phase
между этими двумя source snapshots нет. Использован общий Linux Python 3.12
venv с этими requirements и отдельно установленным `psycopg2-binary==2.9.11`.
Исторический packaged runtime/production environment candidate.33 этим не
воспроизведён; здесь проверяется исполнение его точного API source.

## Исполненный сценарий

В отдельной Ubuntu VM создана новая
`portal_b08_linux_compat_rehearsal` из восстановленной синтетической БД.
Исходные source/restore базы предыдущего gate сохранены. Два настоящих
`uvicorn api:app` запущены через systemd на `127.0.0.1:18081/18082`; выполнены
их собственные imports, `db.init_db()`, migrations и lifespan. Handler,
SQLAlchemy, auth и HTTP responses не подменялись. В units настроены
`IPAddressDeny=any`, `IPAddressAllow=localhost`; используются только новые
fixture secrets и синтетический пользователь.

| Фаза | Процессы | Результат |
| --- | --- | --- |
| Previous до current | Только previous | Health/plans 200, ticket без auth 401, authenticated ticket read и event write 200 |
| Совместная работа | Previous и current одновременно | Те же пять проверок прошли на обоих API; обе event writes подтверждены в общей БД |
| Current остановлен | Previous продолжает работу | Те же пять проверок PASS |
| Previous перезапущен | Новый previous process после current startup | Те же пять проверок PASS; `NRestarts=0` |

Всего **25 HTTP assertions**, пять event writes с отдельными IDs. Независимый
SQL readback подтвердил все пять записей, прежние ticket/attachment и отсутствие
повторных rows по этим IDs. Сохранились journal обоих units и конкретные PID.
Это совместимость выбранных read/write paths; полный API/provider/payment
набор из этого результата не следует.

## Schema readback

Сравнение с восстановленной БД до API startup показало **93 новых индекса** и
**пять server defaults**: `nodes.access_role` и четыре `users.free_profile_*`.
Такие defaults задаёт существующая миграция. Добавленных/удалённых столбцов,
изменений их типа/nullability, удаления или изменения прежних индексов нет.
Это delta между ORM-only fixture и штатным bootstrap, а не новая миграция
current относительно candidate.33.

Первый schema-audit ошибочно требовал полного равенства columns, включая
server defaults, и остановился. Сохранён FAIL log, затем весь фактический
diff записан и проверен отдельно. Критерий не был ослаблен до общего зелёного:
в raw schema report остаётся `REVIEW_SCHEMA_DELTA`, а перечисленные defaults
и индексы явно разобраны. Production code не менялся.

## Граница результата

Previous/current HTTP smoke, совместная работа и перезапуск previous:
**PASS в этой Linux lab**. Реальные production volumes, DDL/index lock impact,
exact deployed dependency/runtime tuple, bots/worker, provider E2E и
production failover не проверены. Contract phase не выполнялась: выбранные
source snapshots не содержат нового schema contraction. Если финальный
candidate изменит schema inputs, этот вывод нужно проверить заново.

Полный B08, G03/B06 и релиз остаются открытыми. `brain-origin` и `RU-origin`
не проверены. После readback оба API остановлены и VM штатно выключена;
БД, source archives и evidence сохранены. Push, merge, signing, новый release
candidate и production deploy не выполнялись.

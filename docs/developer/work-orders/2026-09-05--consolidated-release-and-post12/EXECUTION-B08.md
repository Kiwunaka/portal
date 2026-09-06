# R12-B08 — локальный PostgreSQL restore и deployment contract

Дата: 2026-09-06. Результат: **I3 / NEEDS_RUNTIME_PROOF**.
Source commit: `6632ca095abc14d2ed329452e80e0f75a198d44e`.
Команды, отчёты, SHA и ограничения:
[evidence/b08-postgres-drill.json](evidence/b08-postgres-drill.json).

## Выполненный drill

В существующем loopback PostgreSQL 16.15 созданы отдельные source/target базы
с суффиксом `_rehearsal` и отдельная application role без superuser,
CREATEDB и CREATEROLE. Данные полностью синтетические: 117 таблиц, 9 строк
на момент snapshot. Production source, SSH и provider не использовались.

1. `pg_export_snapshot()` в read-only REPEATABLE READ transaction связал
   fingerprint таблиц и `pg_dump --snapshot`. Дополнительный Event записан
   после экспорта snapshot и отсутствует в восстановленной базе.
2. Custom dump зашифрован потоком OpenSSL AES-256-CBC/PBKDF2, затем расшифрован
   непосредственно в `pg_restore`. Plaintext dump не сохранялся. Encrypted
   archive, source/target базы, runner и отчёты сохранены вне Git. Секреты
   fixture остаются в отдельных локальных файлах с ограниченным ACL.
3. После restore совпали counts и SHA содержимого всех 117 таблиц. Ownership
   validator из production gate подтвердил app ownership всех 1077 public
   objects, права на schema и отсутствие PUBLIC access.
4. Fixture из текущих моделей намеренно не содержала additive-колонку
   `admin_operator_roles.grant_reason`. Реальная `run_migrations` добавила её;
   старые role/environment поля остались читаемыми. Повторная миграция
   изменила только `plan_catalog.updated_at`: seed-код обновляет дату при
   каждом старте. Полные fingerprints обоих запусков сохранены, сравнение
   остальных полей прошло. Byte-identical rerun не заявляется.
5. Два concurrent workers на двух PostgreSQL backend PID обработали обычное
   и повреждённое outbox-сообщение: одна delivery, один provisioning job,
   один payment grant и один dead letter `outbox_payload_invalid`. Следующий
   проход не забрал ни одного сообщения. Provider/panel вызовов не было.

Первый запуск остановился из-за неполного synthetic Event insert
(`schema_version` NOT NULL); runner переведён на существующую ORM model.
Второй выявил описанное обновление seed timestamp. Оба FAIL-отчёта сохранены;
это исправления fixture/критерия сравнения, а не исправления production code.

## Deployment contract

Селектор `iter_upload_mappings` выдал ровно 198 файлов / 6 187 777 bytes:
tracked runtime Python, requirements, четыре probe helpers, shared JSON и
copy catalog. Все target paths уникальны, выбранные исходники чисты относительно
указанного commit, AST Python и JSON parsing прошли. Полный manifest с SHA
сохранён вне Git. Это проверка канонического состава; runtime imports,
установленные зависимости и payload на Brain данным проходом не проверены.

64 существующих теста deploy, encrypted restore gate и PostgreSQL migration
helpers: **PASS**. Delayed health, crash-loop rejection и rollback control
flow здесь проверены с mocked SSH/systemd. Remote gate целиком не запускался;
локальный runner использовал реальные pg_dump/pg_restore, migrations/outbox
и ownership validator. Он не заменяет исполнение remote orchestration.

## Открытые критерии

- Production snapshot, реальные объёмы, DDL/index lock impact, полный restore
  attachments вместе с DB: **MANUAL_OWNER_TEST**. В fixture проверены только
  attachment row и ownership; файл сохранён отдельно, restore файлов не выполнен.
- Actual old application candidate на expanded schema, rolling compatibility
  и contract phase: **NEEDS_RUNTIME_PROOF**. Чтение старых колонок не доказывает
  совместимость старого приложения; destructive schema contraction не проводился.
- Exact runtime payload, deploy, delayed-health failure и rollback с повторным
  live health/readback: **NEEDS_RUNTIME_PROOF**. `brain-origin` и `RU-origin`
  этим локальным проходом не проверены.
- Зависимости G03/B06 и provider E2E остаются открытыми. Release readiness
  и завершение B08 целиком не заявляются.
- Push, merge, deploy, signing, новый release candidate и production mutation:
  **NOT_REQUESTED / не выполнялись**. Client/Core и retained release не изменены.

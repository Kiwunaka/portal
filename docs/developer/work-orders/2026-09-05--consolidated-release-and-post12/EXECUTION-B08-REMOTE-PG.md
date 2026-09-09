# R12-B08 — полный remote PostgreSQL backup/restore gate в Linux lab

Дата: 2026-09-06. B08 целиком: **I3 / NEEDS_RUNTIME_PROOF**.
Source commit: `af80ade`. Продолжение
[SSH/systemd deployment drill](EXECUTION-B08-DEPLOY-LAB.md).
Команды, SHA, ограничения и ссылки на сохранённые данные:
[evidence/b08-remote-pg.json](evidence/b08-remote-pg.json).

## Что исполнено

В той же отдельной Ubuntu VM создана синтетическая база `portal`, обычная
application role без superuser/CREATEDB/CREATEROLE/replication/bypass-RLS и
117 таблиц из текущих моделей. В snapshot шесть строк: account, user,
ticket, message, корректно привязанный attachment и event. Создан новый
target `portal_b08_linux_01_rehearsal`; существующие базы не сбрасывались.

Исполнен `main()` текущего `remote_postgres_backup_restore_gate.py` с
реальными SSH, `setsid`, `runuser`, `psql`, `pg_dump`, OpenSSL и `pg_restore`.
Guards exact source/target, known-host pinning, schema ownership, timeouts и
retention не отключались. Wrapper сохраняет маркеры и результаты реальных
команд. После возврата настоящего snapshot exporter он запускает отдельную
запись Event, чтобы проверить границу snapshot; ответы remote команд не
подменяются. Пароль и passphrase передаются предусмотренными кодом каналами,
не входят в логи/отчёт/Git.

Gate использует password SSH. На время прогона в **этом госте** был включён
вход root с новым случайным лабораторным паролем. В `finally` возвращён
key-only SSH и заблокирован root password; это подтверждено итоговым readback.
Forwarding остаётся только на host loopback. Production credentials и
production hosts не использовались.

## Результаты

- Remote gate: **PASS**, snapshot cleanup `committed`, backup retention PASS,
  target сохранён, `target_was_reset=false`.
- Зашифрованный DB archive: 490 320 bytes, mode `0600`; расшифровка передана
  напрямую `pg_restore`. Plaintext DB dump не сохранялся. SHA скачанного
  encrypted archive совпал с remote metadata.
- Target принадлежит app role; ownership всех **1077 public objects**,
  права schema и отсутствие PUBLIC access подтверждены реальным SQL.
- Support ownership: один bound attachment, ноль dangling/unbound.
- Независимая проверка сравнила counts и SHA сериализованных строк всех
  **117 таблиц** с fingerprint до export: полное совпадение. Поздний Event
  есть только в source; остальные source tables не изменились.
- После gate и независимой проверки нет активных транзакций этих двух БД.

Отдельным сохранённым runner выполнен encrypted tar backup/restore двух
неизменяемых synthetic attachment files в новый каталог. SHA всех файлов
совпали до backup, после backup и после restore; attachment row в target
указывает на файл правильного размера. File archive: 10 272 bytes, mode
`0600`. Это два отдельных архива DB/files в лаборатории без file writers,
не доказательство атомарного snapshot двух хранилищ при production traffic.

Исходный gate report сохранён без исправлений. Его поле `origin=brain`
жёстко задано скриптом и **не доказывает brain-origin**: фактическая среда
этого прогона — `current-origin`, локальная Ubuntu VM. В evidence wrapper
это различие записано явно.

## Подготовка и проверки

Первый setup завершился exit 1 после создания пустой source DB. Readback
показал отсутствие `psycopg2` в deployed venv: backend requirements его не
содержат, текущий `remote_postgres_cutover.py` устанавливает его отдельно.
Для fixture установлен `psycopg2-binary==2.9.11`, сохранён pip install report
с wheel hash. Продолжение разрешалось только при пустой schema; базы не
удалялись и не создавались повторно. Два сбоя host helper при сохранении
лога/пути исправлены до запуска gate; установка и seed не повторялись.
Таким образом, прежний deployment PASS не является доказательством наличия
PostgreSQL driver на новом хосте без шага cutover.

Production code, manifests и зависимости репозитория не изменены. Предыдущие
64 script regression tests переиспользованы только после проверки, что
deploy/restore/migration scripts, тесты и dependency inputs не изменились.
Новые docs/context/package checks и SHA checks записаны в JSON.

Гостевая VM штатно выключена после readback. Обе БД, original image, disk,
encrypted archives, synthetic files, fingerprints и runner сохранены вне Git;
секреты остаются в защищённых локальных/guest файлах. Бэкапы не удалялись.

## Открытые критерии

Реальная старая application version на expanded schema, rolling compatibility,
contract phase, фактические volumes/locks и production DB+attachments recovery
остаются **NEEDS_RUNTIME_PROOF / MANUAL_OWNER_TEST**. Текущий прогон не запускал
реальные API/bots/worker и не проверял provider E2E, G03/B06, `brain-origin`
или `RU-origin`. Новый candidate, signing, push, merge, production deploy и
production mutation **не выполнялись**. Завершение B08 или всего R12 не заявляется.

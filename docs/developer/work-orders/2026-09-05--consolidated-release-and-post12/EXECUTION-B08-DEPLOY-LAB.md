# R12-B08 — SSH/systemd deployment и автоматический rollback

Дата: 2026-09-06. Результат: **I3 / NEEDS_RUNTIME_PROOF** для B08 целиком.
Source commit: `e74ee81424a23cebb631cabdc0fc8e790765f9d1`.
Предыдущий [PostgreSQL drill](EXECUTION-B08.md) сохранён отдельно.
Точные команды, результаты и SHA:
[evidence/b08-deploy-lab.json](evidence/b08-deploy-lab.json).

## Среда и граница проверки

Создана отдельная VirtualBox VM `POKROV-r12-b08-linux-20260906`:
Ubuntu 24.04, 2 CPU, 3 GiB RAM, отдельный 20 GiB virtual disk. Образ
`noble/20260826/noble-server-cloudimg-amd64.vmdk` получен из официального
Ubuntu Cloud Images; SHA256 совпал с опубликованным HTTPS checksum.
Подпись GPG не проверялась. На хосте Docker вернул HTTP 500, WSL —
`HCS_E_SERVICE_NOT_AVAILABLE`; их конфигурация не изменялась.

SSH доступен через NAT forwarding только на `127.0.0.1:55228`, ключ сервера
закреплён до первого подключения; password login отключён. В госте настоящие
SSH/SFTP, systemd, Python 3.12 и PostgreSQL 16. Cloud-init завершился.
Пакеты устанавливались из публичных package repositories. Production,
provider, существующие Windows VM и host VPN этим прогоном не затронуты.

`deploy-entry.py` вызывает неизменённый `main()` из
`scripts/remote_deploy_brain_portal_code.py`, с реальным `connect_node`.
Wrapper меняет health URL на guest loopback, для двух отказов выбирает
отдельный Git fixture payload и записывает результаты реальных SSH команд.
Функции deploy/backup/rollback, pip, curl, systemd, 12-секундное ожидание и
12 попыток health не заменены mock-ответами.

Сервис `r12-deploy-fixture` — синтетический HTTP процесс. Он читает SHA
развёрнутого `api.py`, позволяет воспроизвести health failure и отложенный
crash. Реальные `portal-api`, боты и worker здесь не запущены. Payload
содержит все 198 файлов текущего deployment selector; staging compile/JSON,
установка pinned requirements и предусмотренные скриптом runtime imports
исполнены в Linux. Это не полный import всех модулей или API E2E.

## Результаты

| Сценарий | Deploy exit | Наблюдение | Проверка после deploy/rollback |
| --- | --- | --- | --- |
| Текущий payload | 0 | `active`, `NRestarts=0`, health PASS после 12 секунд | SHA всех 198 файлов совпали с исходниками |
| Health failure | 1, ожидаемый | Сервис active без рестартов; все 12 curl получили HTTP 503 | Автоматический restore и restart; повторный delayed health PASS, SHA 198 файлов восстановлены |
| Delayed crash | 1, ожидаемый | Процесс завершался с 42 через 4 секунды; при проверке `active`, `NRestarts=2` | Автоматический restore и restart; `NRestarts=0`, повторный delayed health PASS, SHA 198 файлов восстановлены |

Fault payload отличается от текущего только инертным комментарием в
`portal_bot/api.py`; SHA используется лабораторным сервисом как условие
отказа. Это проверка отказа после promotion, а не дефект текущего API.
Файл synthetic attachment оставался побайтно прежним во всех трёх прогонах.
Сохранены три backup directory, staging двух отклонённых прогонов,
полный journal сервиса, package versions, source/target manifest и runner.
Успешный staging удалён штатным deploy-процессом; backup retention ничего
не удалил при трёх сохранённых каталогах и лимите пять.

Первый setup probe вызвал curl сразу после systemd start и получил exit 7:
процесс ещё не открыл порт. Повторный readback подтвердил baseline active,
health и отсутствие рестартов до начала deploy. Это сохранённое ограничение
fixture setup; production deploy использовал собственную delayed-проверку.

64 теста deployment, encrypted PostgreSQL restore gate и migration helpers:
**PASS**. Проверки документации и целостности evidence перечислены в JSON.
После финального readback лабораторный сервис остановлен, VM штатно
выключена; disk, исходный образ и evidence сохранены вне Git.

## Что остаётся открытым

- Реальная previous application version на expanded PostgreSQL schema,
  rolling compatibility и contract phase: **NEEDS_RUNTIME_PROOF**.
- Полный backup/restore attachments вместе с DB, production volume/locks и
  фактический recovery: **MANUAL_OWNER_TEST**. Attachment sentinel здесь
  доказывает сохранность при code deployment, не restore файла из backup.
- Remote encrypted PostgreSQL orchestration на Linux этой проверкой ещё
  не исполнен; наличие PostgreSQL в VM не является restore PASS.
- Зависимости venv во всех трёх payload одинаковы. Откат версии зависимостей
  или миграций данным прогоном не проверен; скрипт восстанавливал файлы.
- Точный production candidate, реальные units/API и public health,
  `brain-origin`, `RU-origin`, G03/B06/provider E2E остаются открытыми.
- Новый release candidate, signing, push, merge, production deploy и
  production mutation: **NOT_REQUESTED / не выполнялись**.

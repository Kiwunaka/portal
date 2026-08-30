# RU-Origin Probe Handoff

Last updated: 2026-08-30

## Document Status

Document class: ACTIVE_EXECUTION. Это текущий операторский чек-лист для
внешней проверки POKROV из РФ. Каноническую семантику origin, свежести и
вердиктов задаёт
[Monitoring And Visibility](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md).

Этот документ не подтверждает, что таймеры установлены на `mini`, что доступ к
хосту сейчас есть или что последний RU-origin результат прошёл. Такие факты
появляются только после отдельного ручного выполнения и сохранения доказательств.

## Область проверки

Стандартный RU-origin verdict включает только:

- доступность среды пробы через отдельную environment-проверку;
- канонические публичные POKROV-хосты и API health;
- delivery-ноды, которые входят в подписанный manifest;
- явно включённые reserve ingress проверки.

Сторонние диагностические цели не влияют на release verdict. `current-origin`,
`brain-origin` и `RU-origin` всегда остаются тремя отдельными строками.

## Поток данных

```text
RU host -> runner -> private immutable spool -> uploader -> HMAC ingest
        -> normalized RU tables -> admin read model -> adminapp
```

Репозиторные шаблоны:

- `infra/pokrov-ru-probe.service`
- `infra/pokrov-ru-probe.timer`
- `infra/pokrov-ru-probe-uploader.service`
- `infra/pokrov-ru-probe-uploader.timer`

Runner запускается по UTC в `00:00`, `06:00`, `12:00` и `18:00`; uploader
обрабатывает очередь каждые 15 минут. Это шаблоны для ревью. Их наличие в Git
не доказывает установку или активность unit на живом хосте.

## Предварительные условия

Перед ручным вводом контура владелец подтверждает без публикации значений:

- доступ к `mini` либо утверждённому replacement RU host;
- синхронизированное UTC-время и рабочий DNS/TCP/TLS egress;
- отдельного непривилегированного пользователя процесса;
- приватный spool, доступный только этому пользователю, с достаточным свободным
  местом;
- Python runtime и точную версию `scripts/ru_probe_runner.py`,
  `scripts/ru_probe_uploader.py`, `scripts/internal_hmac_client.py`,
  `portal_bot/internal_request_auth.py`, `scripts/node_dataplane_probe.py` и
  `portal_bot/ru_probe_contract.py`;
- redacted `probe.env` и `uploader.env` с API base URL, key id и host id, но
  без HMAC-значения в handoff;
- HMAC secret file, переданный через утверждённый секретный канал, с правами
  только для процесса;
- совпадение `probe_host_id` с subject ключа и scopes
  `ru_probe:manifest`, `ru_probe:ingest`, `ru_probe:heartbeat`;
- `profiles.json` только с разрешёнными фиксированными executable/argv, без
  shell-фрагментов, токенов, URL подписки или учётных данных;
- актуальный server-side manifest и известный rollback owner.

В отчёт разрешено записывать имена переменных, key id, fingerprint/revision,
путь к секрету и факт проверки прав. Значение HMAC, SSH-пароль, private key,
subscription URL, raw provider payload и пользовательские данные запрещены.

## Spool и значения состояний

Корень spool по шаблону — `/var/lib/pokrov-ru-probe`; конкретный путь может
быть переопределён в утверждённой установке. Каждый run сначала становится
неизменяемой парой artifact + sidecar.

- `pending`: артефакт корректен локально, но ещё не принят backend. Сетевые и
  временные ошибки остаются здесь с bounded backoff.
- `archive`: backend подтвердил точный `run_id`, а локальная архивная запись
  завершилась. Это подтверждает ingest, но не обязательно `PASS` проверок.
- `blocked`: ключ отключён, scope/subject запрещён или доступ намеренно
  заблокирован. Автоматический повтор не должен маскировать проблему доступа.
- `quarantine`: повреждён hash, нарушен контракт, payload конфликтует, nonce
  повторён либо размер/схема недопустимы. Такие артефакты не возвращаются в
  очередь без расследования причины.

Не удаляйте `blocked`, `quarantine` или необработанный `pending` ради зелёного
heartbeat. Сначала сохраните redacted run id, correlation id, server code,
время и решение владельца.

## Локальная проверка кандидата

До работы с живым хостом допустимы только локальные, не изменяющие runtime
проверки:

```powershell
python scripts/ru_probe_runner.py --help
python scripts/ru_probe_uploader.py --help
python -B -m pytest -p no:cacheprovider tests/test_internal_request_auth.py tests/test_ru_probe_contract.py tests/test_ru_probe_service.py tests/test_ru_probe_ingest_api.py tests/test_ru_probe_runner.py tests/test_ru_probe_uploader.py -q
```

Ожидается `PASS`. Этот результат подтверждает код и фикстуры конкретного
локального commit, но не подтверждает сеть РФ, production ingest, установку
unit или актуальность живого HMAC key record.

### Неизменяемые пакеты точных кандидатов

Точный набор исходников для RU-host строится из Git objects, а не из текущего
рабочего дерева. Builder принимает только явно allowlisted подписанные platform
revision; произвольный commit закрывается до чтения source members. Для текущего
candidate.10:

```powershell
python scripts/build_ru_origin_probe_bundle.py build --source-revision 209b8f40c36d95f2bbc67caa52a41ecb09f46720 --output <private-artifact-path>/pokrov-ru-origin-candidate10-209b8f4.zip
python scripts/build_ru_origin_probe_bundle.py verify --bundle <private-artifact-path>/pokrov-ru-origin-candidate10-209b8f4.zip
python scripts/build_ru_origin_probe_bundle.py plan --bundle <private-artifact-path>/pokrov-ru-origin-candidate10-209b8f4.zip --operation install
python scripts/remote_install_ru_origin_probe.py --bundle <private-artifact-path>/pokrov-ru-origin-candidate10-209b8f4.zip --ssh-config-alias <trusted-ru-alias> --operation install
```

Candidate.10 package содержит 10 source/unit members, имеет размер `47930` байт
и SHA-256
`0108ccc4595ff2f424b4e5169d19fc539e21cc1eaed79cb92ccbacf04ce85e22`.
Повторная независимая сборка дала те же байты. Candidate.9 revision
`8468787...`, candidate.8 revision `241a83b4...` и candidate.6 revision
`5713324c...` остаются allowlisted историческими входами; их ранее
зафиксированные пакеты имеют SHA-256
`a887cf4ad193a73ceabebbff476e5264c52c8694ab6f246bd81c6a6aeff6b4e8`,
`7bc2ec16971a23fb16ce54d2f2e1dae4f3a228bca13527a71099396e532a8707`
и
`e7eb8ec20693f9626d6e7697c7845fa165e77fc1daa7df580ef0618248be345b`.
Ни один пакет не содержит `probe.env`, `uploader.env`, `hmac.key` или
`profiles.json` и ничего не устанавливает сам. Успешная сборка/проверка —
только локальное evidence уровня immutable bundle,
не доказательство живой RU-origin среды, запуска, ingest, heartbeat или admin
readback.

Последняя команда по умолчанию выполняет только удалённый `PLAN`: проверяет
host requirements, число занятых install targets, состояния unit и агрегированные
spool counts, но не передаёт файлы и не меняет runtime. `APPLY` дополнительно
требует приватный каталог ровно из `probe.env`, `uploader.env`, `hmac.key` и
`profiles.json`, точные подтверждения bundle/revision/node, отдельное подтверждение
внешней мутации, сохранения spool и активации timer. Значения и даже hashes
runtime-material в JSON-отчёт не попадают.

Первый живой запуск candidate.9 на `mini` подтвердил установку, чтение
root-owned `0640` HMAC credential назначенной service group, signed manifest,
runner, ingest, archive, fresh heartbeat и три admin read endpoint (`HTTP 200`).
При этом итог RU-origin честно остался `FAIL`: Google прошёл DNS/TCP/TLS, но
обычная короткая страница была ошибочно проверена как обязательное тело
`65536` байт; redacted dataplane result сохранял только факт соединения, а
runner ошибочно требовал удалённый raw connected IP и помечал разрешённые
семейства как `forbidden_address_family`. Исправление сохраняет только
безопасный `connected_family`, уважает подписанный `min_body_bytes` и задаёт
service-specific HTTP paths/thresholds. Candidate.9 не патчился на месте и не
получил ложный RU `PASS`.

Candidate.9 затем был снят точным receipt-bound rollback с сохранением spool.
Подписанный candidate.10 установлен из детерминированного bundle на том же
trusted RU-host. Ручные runner и uploader завершились успешно; manifest,
ingest, archive, fresh heartbeat и три admin read endpoint прошли. Latest run
имеет доступную среду и текущий eligible artifact, а uploader показывает
`pending=0`, `blocked=0`, `quarantine=0`, `archive_write_ok=true`.

Итог candidate.10 RU-origin остаётся `FAIL`, а не `PASS`: из `13` обязательных
targets прошли `10`. Canonical web/API, environment control и delivery-ноды
`de`, `it`, `pl`, `ru`, `ru_spb`, `us` проходят. `brain` падает на TLS
handshake, `free` — на REALITY target mismatch, `nl` — на TCP timeout. Старые
ложные ошибки body threshold и `forbidden_address_family` отсутствуют. Таймеры
после детерминированного ручного запуска оставлены inactive, но enabled.
Подробный secret-free record хранится в `WO-013CM`; три независимые ошибки не
сводятся к одной SPB-проблеме и не разрешают promotion.

Root-login не обязателен: допустима непривилегированная trusted-key сессия только
при успешном `sudo -n`. Инструмент не принимает sudo-пароль и не выводит его;
если passwordless privilege отсутствует, APPLY закрывается до staging/mutation.

Backend HMAC registry готовится отдельно через
`scripts/remote_prepare_ru_origin_auth.py`. Его `PLAN` только проверяет
`portal-api`, целевые paths и текущий process environment. `APPLY` принимает
локальный private secret file, но не возвращает ни значение, ни hash; создаёт
ровно один key `ru-mini-v1` с subject `mini`, origin `ru` и scopes
`ru_probe:manifest`, `ru_probe:ingest`, `ru_probe:heartbeat`, сохраняет root-only
absent-state receipt, ставит отдельный systemd drop-in, перезапускает
`portal-api` и обязан доказать подписанное чтение manifest. Ошибка после начала
мутации удаляет только operation-owned registry/drop-in и возвращает API в
активное состояние. `ROLLBACK` требует точный receipt и managed markers.
После restart signed read использует ограниченный readiness retry только для
transport/`5xx` и временного non-JSON от frontend; любой `4xx` остаётся
немедленным fail-closed.

`profiles.json` может быть `{"profiles":{}}`, когда текущий server manifest не
содержит `local_probe_profile_id`: native TCP/TLS/HTTP stages не требуют
фиктивного executable. Если manifest требует хотя бы один profile, APPLY должен
остановиться до установки, пока для каждого ID не подготовлен проверенный
allowlisted executable/argv.
Local и remote validators обязаны одинаково принимать этот пустой registry.
Любой failed APPLY пишет redacted JSON с `mutation_attempted`, receipt state и
точным `automatic_rollback_status`; успешный rollback не превращает исходную
ошибку в PASS.

`hmac.key` остаётся root-owned `0640` и читается только primary/supplementary
группой `pokrov-ru-probe`. Shared HMAC client допускает этот один POSIX-вариант
group access; world bits, group write/execute, не-root owner или чужая группа
закрываются с `secret_file_permissions`. Owner-only `0600` остаётся допустимым.

В candidate.6 `EnvironmentFile` обязан существовать, но runner/uploader используют
скомпилированные канонические defaults. Поэтому установщик принимает в обоих env
файлах только `POKROV_API_BASE_URL=https://api.pokrov.space`,
`POKROV_KEY_ID=ru-mini-v1` и `POKROV_PROBE_HOST_ID=mini`; это receipt metadata,
а не поддержка runtime override. Изменяемые endpoint/key/host параметры потребуют
нового кандидата с явной передачей CLI arguments и отдельной проверкой.

## Ручная приёмка владельцем

Фактическая установка/обновление unit и секретов — `MANUAL_OWNER_TEST`.
Владелец выполняет её через утверждённый доступ и сохраняет только redacted
результат:

1. Точный platform commit и checksums файлов совпадают с кандидатом.
2. Unit используют репозиторные шаблоны, непривилегированного пользователя,
   `UMask=0077`, защищённые paths и ожидаемые schedule.
3. Один ручной runner создаёт ровно один новый `pending` artifact.
4. Один uploader переносит принятый artifact в `archive` и отправляет heartbeat.
5. Admin read endpoints показывают тот же `run_id`, manifest revision,
   законченный UTC timestamp и per-node результаты.
6. Через минуту `adminapp` показывает серверный результат, а не локально
   выдуманный статус.
7. Следующий scheduled run подтверждает cadence без ручного запуска.

Если SSH, HMAC record, API admin session или доступ к RU host отсутствует,
итог — `BLOCKED_BY_ACCESS` с названием недостающей зависимости. Не ставьте
`FAIL` нодам и не ставьте `PASS` RU-origin при неработающей среде пробы.

## Heartbeat

Uploader отправляет только ограниченную сводку: service version, counts
`pending/blocked/quarantine`, oldest pending timestamp, archive-write state,
disk state/free bytes и allowlisted last error code.

- свежий heartbeat: возраст не больше 45 минут;
- stale heartbeat: старше 45 минут — новые результаты могут не доставляться;
- missing heartbeat: backend ни разу не получил пригодную сводку;
- `pending_count > 0`: смотреть oldest pending и retry code;
- `blocked_count > 0`: проверять key state/scope/subject;
- `quarantine_count > 0`: расследовать контракт/hash/conflict;
- `archive_write_ok=false`, `disk_state=critical|unknown`: локальная сохранность
  доказательств под угрозой.

Heartbeat не меняет прошлый RU verdict. Последний eligible run становится
`stale` только по серверному 7-часовому окну.

## Rollback

Rollback выполняет владелец без удаления доказательств:

1. Останавливает новые runner/uploader запуски и фиксирует время остановки.
2. Сохраняет `pending`, `blocked`, `quarantine`, `archive`, manifest cache и
   redacted checksums для расследования.
3. Отзывает или отключает только затронутый HMAC key record на backend.
4. Возвращает предыдущие проверенные unit/script versions.
5. Проверяет, что admin честно показывает stale/missing/uploader unavailable,
   а не зелёный статус.
6. Возобновляет schedule только после локальной проверки и нового
   `MANUAL_OWNER_TEST`.

Этот чек-лист намеренно не содержит готовой команды `--apply` или значений
секретов. Защищённый инструмент существует, но изменение живого хоста всё равно
требует отдельной авторизации владельца и всех точных подтверждений CLI.

## Шаблон итогового доказательства

```text
candidate: <platform commit>
probe host: <redacted label>
manifest revision: <sha256>
runner unit/timer: MANUAL_OWNER_TEST | BLOCKED_BY_ACCESS
uploader unit/timer: MANUAL_OWNER_TEST | BLOCKED_BY_ACCESS
current-origin check: PASS | FAIL | NOT_REQUESTED
brain-origin check: PASS | FAIL | BLOCKED_BY_ACCESS | NOT_REQUESTED
RU-origin check: PASS | FAIL | BLOCKED_BY_ACCESS | MANUAL_OWNER_TEST
run id: <uuid or absent>
finished at UTC: <timestamp or absent>
uploader heartbeat: fresh | stale | missing | unavailable
spool: pending=<n>, blocked=<n>, quarantine=<n>
production deploy: NOT_REQUESTED | <retained deployment evidence reference>
notes: <redacted blockers and correlation ids only>
```

Не превращайте `MANUAL_OWNER_TEST`, `BLOCKED_BY_ACCESS`, `NOT_REQUESTED` или
отсутствующий артефакт в `PASS`.

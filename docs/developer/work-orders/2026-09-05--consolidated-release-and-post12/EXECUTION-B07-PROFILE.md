# R12-B07 — DB/HTTP/outbox profile в Linux lab

Дата: 2026-09-06. Полный B07: **I3 / NEEDS_RUNTIME_PROOF**.
Source: `6789cef`. Продолжение [HTTP/resource inventory](EXECUTION-CONTINUED.md#b07a--httpresource-inventory).
Команды, полный source SHA, сводка и хеши raw samples:
[evidence/b07-profile.json](evidence/b07-profile.json).

## Среда и метод

Существующая отдельная Ubuntu VM: два vCPU, 3072 MiB, Python 3.12.3,
PostgreSQL, loopback SSH. Созданы две новые synthetic database copies из
сохранённой B08 compatibility fixture. Первая сохранена после остановки
fixture assertion; успешный прогон использует `portal_b07_profile_02_rehearsal`.
Ни одна прежняя БД не сбрасывалась. Временные systemd units разрешают только
localhost через `IPAddressDeny=any` / `IPAddressAllow=localhost`.

Исполнялись настоящие `run_payment_db_use_case`, SQLAlchemy engine из `db.py`,
`PaymentHttpRegistry` и outbox dispatcher до provisioning queue. SHA семи
runtime modules в госте совпали с **Git blobs** текущего HEAD. Сверка с
Windows checkout сначала дала различие CRLF/LF; сравнение с Git objects
подтвердило точные deployed bytes. Репозиторий и runtime modules не изменены.

- DB: 120 операций при concurrency 10 и 80; в каждой настоящий
  `SELECT pg_sleep(0.05)` и чтение количества synthetic users. Измерены
  ожидание threadpool и получение DB connection. Последнее включает pool
  wait, создание соединения и pre-ping, поэтому не называется чистым pool wait.
- HTTP: 120 запросов и пять warmups, штатная policy `lavatop` с pool limit 20,
  реальный aiohttp server на localhost с задержкой 50 мс. Trace callbacks
  измеряют connector queue. Использован предусмотренный session factory для
  добавления trace; ответы и network transport не подменяются.
- Event loop: реальная разница между 5-мс timer и его пробуждением; сохранены
  все samples. HTTP server работает в том же loop, что и client.
- Outbox: 120 synthetic paid grants, два concurrent worker, batch 20,
  настоящий default dispatcher и commit. Provider/node network не вызывается;
  результат заканчивается durable provisioning jobs, не доступом пользователя.

После первого успешного профиля DB/HTTP повторены трижды. Перед серией
исполнены пять реальных DB queries. Первоначальные пять DB warmups только
создавали/закрывали Session без connection: это ограничение первого прогона
сохранено явно. HTTP в каждой серии прогревается пятью настоящими запросами.
Нет production baseline, сравнения с прошлым candidate или performance-gate
PASS; nearest-rank p95 ниже — описательная статистика компонентной нагрузки.

## Результаты

| Три повторных прогона | Наблюдение |
| --- | --- |
| DB concurrency 10, p95 thread queue | 1.06–5.27 мс |
| DB concurrency 10, p95 checkout | 1.88–32.58 мс |
| DB concurrency 80, p95 thread queue | 172.78–185.21 мс |
| DB concurrency 80, p95 checkout | 178.88–186.29 мс |
| DB concurrency 80, p95 operation после checkout | 58.04–62.69 мс, включая искусственные 50 мс |
| DB max active worker при concurrency 80 | 40 во всех повторах; после завершения active/checkedout = 0 |
| HTTP p95 connector queue | 282.83–562.02 мс, 100 queued из 120 в каждом burst |
| HTTP p95 request latency | 337.01–616.28 мс |
| HTTP lifecycle | один ClientSession, 20 transport connections, max 20 активных; session закрыта |

Штатные DB limits: pool size 5 + overflow 10, AnyIO threadpool 40 tokens.
При concurrency 80 очередь ожидаема: потоки делят максимум 15 connections.
HTTP burst также превышает лимит 20. Искусственная задержка задаёт service
time и помогает увидеть очередь, но не доказывает bottleneck рабочего трафика.
В первом повторе DB checkout ещё включает cold/overflow connections.

Event-loop p95 в повторных DB bursts: 5.60–9.97 мс; HTTP: 6.15–80.29 мс.
Третий HTTP прогон заметно медленнее первых двух; он сохранён без исключения.
Два vCPU, colocated client/server и profiler overhead ограничивают выводы.
Без profiler attribution нельзя приписать этот разброс конкретному продуктному
handler или обещать, что изменение pool limit его исправит.

Outbox: **120/120 delivered**, 120 отдельных provisioning jobs, attempts=1,
нет pending/processing/dead-letter и claim tokens после обработки. Возраст
открытой очереди изменился с 2 секунд на 0. Drain занял 648.40 мс
(185.07 events/s в одном этом synthetic burst). Это не production throughput
и не скорость provisioning. Event-loop samples outbox включают seed через
threadpool, а время drain начинается после seed.

## Принятое решение и границы

Свежая AST inventory подтверждает те же 15 direct ClientSession sites;
payment lifespan registry учитывается отдельно. Наблюдаемые очереди соответствуют
действующим лимитам. Оснований менять лимиты, объединять authenticated sessions
или переписывать ORM этот профиль не дал. Production code, конфигурация и
канонический контракт не менялись.

Первый прогон остановился до seed: fixture неверно требовала ноль **всех**
grants, хотя штатный bootstrap уже создал free grant. Вторая новая копия
проверяет ноль provider-payment grants, затем подтверждает ровно 120 новых
paid grants/outbox/jobs. Первый log, DB и частичные DB/HTTP samples сохранены.

Focused DB/HTTP/outbox regression, docs/context/package checks, source hashes
и `git diff --check` записаны в receipt. После readback нет активных B07
транзакций; profile units завершены, VM выключена. Raw scripts, samples,
исходные inventory и обе базы сохранены вне Git.

Production pool wait, event-loop lag, outbox age и соответствие нагрузке
рабочего трафика: **NEEDS_RUNTIME_PROOF**. B07 и общий план не завершены.
Это `current-origin`, не `brain-origin` и не `RU-origin`. Push, merge, новый
candidate, production deploy и платежи не выполнялись.

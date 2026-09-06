# R12-B07 — read-only production observations и API loop-lag collector

Дата: 2026-09-06. **I3 / PARTIALLY_FIXED**, полный B07 остаётся открыт.
Implementation commit: `8bba6a024cdfca25c9b1c0ad95f751c6cd02e9da`.
Продолжение [synthetic component profile](EXECUTION-B07-PROFILE.md).
Точный source, команды, результаты и retained hashes:
[evidence/b07-runtime.json](evidence/b07-runtime.json).

## Наблюдения действующего runtime

Без production writes, deploy, restart или оплаты выполнены:

- **current-origin**: 12 последовательных GET `/api/health` через public HTTPS,
  номинальный интервал 5 секунд, окно 55 секунд. Все ответы 200, timestamp
  различается. Сохраняется только status, timestamp и fixed integer payment DB
  projection. Response bodies, commercial payload и customer data не сохраняются.
- **brain-origin**: SSH через настроенный `pokrov-brain`, strict known-host
  verification и существующий ключ. Локальный Caddy health вызван с
  `--resolve api.pokrov.space:443:127.0.0.1`, с проверкой TLS certificate.
  Он вернул те же DB counters. Никаких insecure/TOFU исключений не добавлено.
- На Brain прочитаны hashes восьми именованных runtime files, выбранные
  systemd properties, package versions из existing venv и SQL aggregate outbox.
  SQL использует `BEGIN READ ONLY`, statement timeout 2s, lock timeout 500ms,
  затем ROLLBACK. Скрипт передан через stdin; production files не записывались.
- Из не более 500 journal lines за последние 15 минут внутри remote process
  выделялись только fixed-shape HTTP counters. Raw journal не передавался в
  evidence, provider/account/order/payload/exception text не сохранялся.

| Наблюдение | Результат и граница |
| --- | --- |
| Payment DB | active 0, max_active 1, started/completed 18, failed 0 во всех 12 samples |
| Threadpool queue counters | total 2 ms, max 1 ms; за окно не изменились |
| Use-case duration counters | total 286 ms, max 74 ms; за окно не изменились |
| Outbox SQL | pending/processing/dead-letter/unknown status = 0; delivered 2; oldest open age 0 |
| API / worker systemd | active, NRestarts=0; ExecMainStartTimestamp 2026-09-01 01:55:11 / 01:55:19 UTC |
| HTTP journal projection | 0 matched records в выбранном ограниченном окне; это не доказательство отсутствия provider traffic |

Counters описывают историю обслужившего процесса, не 18 новых платежей за это
окно. Нулевые deltas дают idle observation, а не capacity/timeout-rate proof.
Public HTTP elapsed 167–487 ms включает current-origin network/TLS; серия не
соответствует 5 warmups + 50 samples performance gate и не даёт его PASS/FAIL.

Venv readback: Python 3.10.12, SQLAlchemy 2.0.46, psycopg2-binary 2.9.11,
aiohttp 3.13.3, Starlette 1.6.0, AnyIO 4.14.2, uvicorn 0.34.0. Это выбранные
metadata, не полный environment manifest или аттестация loaded dependencies.

Восемь on-disk files текстуально совпадают с platform source candidate.33
`f5300053026d32826e54c02202303e1f68c65bc1` после **обоюдной** CRLF→LF
нормализации. Только `models.py` совпадает raw bytes; оба вида hashes сохранены.
От текущей feature branch отличаются API composition, public routes и outbox.
Это bounded source comparison, не доказательство полного deployed tuple,
loaded bytecode или выпуска candidate.33. Новые B06/outbox изменения этим
runtime readback не проверены.

Первый SSH helper использовал port 22 и завершился RuntimeError. Настроенный
OpenSSH profile использует 29374 и дал успешный readback. Первые source
comparisons смешивали LF-normalized input с raw Git blob; сохранённый final
comparison явно нормализует обе стороны, сохраняя отдельную raw проверку.

## Исправленный пробел B07

Production `/api/health` и текущий исходный API не имели event-loop lag
projection. Добавлен `EventLoopLagMonitor` в отдельном runtime module:

- один монотонный timer раз в секунду, принадлежащий API lifespan;
- scalar `samples`, last/max/total lag, фиксированные collection states;
- до первого sample last/max = null; отсутствие lifespan = null projection;
- shutdown отменяет задачу и дожидается её; новый lifespan создаёт новый monitor;
- ошибка collection даёт `failed` и один fixed-code log; запросы и identities
  не собираются, growing sample list отсутствует.

`/api/health.event_loop_lag` описан в canonical API и monitoring owners.
Платёжный threadpool, HTTP pools, таймауты, ORM и commercial health не менялись.
Local deploy selector включает новый module: **199 mapped files**, без запуска
upload/restart. Старый 198-file deployment receipt не становится доказательством
нового payload. Новый observer **не развёрнут на production**.

## Проверка нового API

Focused test вызывает настоящий synchronous stall в test loop, проверяет
**прирост** lag/sample counters и прекращение наблюдений после close.
ASGI lifespan test проверяет health projection и очистку task owner вместе с
payment HTTP registry. PASS: 20 focused/module-slice tests; 154 backend tests
и 8 subtests; 33 docs tests; context/package и diff checks. Точные команды
и результаты сохранены в receipt.

В отдельной Linux VM создана новая `portal_b07_lag_rehearsal` из сохранённой
synthetic B08 DB. Source copy отдельная: прежние lab payloads не перезаписаны.
Настоящий uvicorn API использует текущие API/public-route/monitor bytes;
их hashes повторно сравнены с worktree. Units разрешают только localhost.

Lab-only wrapper добавляет один endpoint с 1200-ms synchronous stall; он не
входит в product code или deploy mapping. Перед вызовом было 20 samples,
после — 22; cumulative lag вырос на **225 ms**, последний sample — 207 ms.
Первоначальная проверка `max >= 150` была недостаточна: prior maximum уже
равнялся 280 ms. Поэтому raw result сохранён, а отдельный reanalysis проверяет
новые samples и delta cumulative lag за controlled window. Lifetime max не
приписан этому stall. Это timer instrumentation proof в lab, не production SLO.

API штатно остановлен: ExecMainStatus=0, Result=success, NRestarts=0,
Application shutdown complete. Сообщения об отказе monitor нет. VM выключена.
Первый SSH banner timeout во время boot произошёл до upload/setup; успешный
повтор начался после его terminal result. Базы, sources и evidence сохранены.

## Оставшиеся критерии

На actual production измерены outbox age и доступные DB counters в idle window.
Раздельный SQL connection-pool wait, provider connector wait, event-loop lag
после разрешённого deploy, нагрузочный профиль и пригодность лимитов остаются
**NEEDS_RUNTIME_PROOF**. Нет p95 или traffic SLO из cumulative max/total.

`RU-origin`, provider operations и candidate acceptance не исполнялись.
Production inspection была read-only; новый runtime collector проверен локально
и в isolated VM. Push, merge, production deploy, restart и новый release
candidate не выполнялись. Общий план и B07 не завершены.

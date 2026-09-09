# B08 — текущий API, additive migration и worker на Brain-копии

**PASS технической части B08 / I4; зависимость B06 открыта.**
Current source `cd4a8b905a4105707ebad11fd920473f2478cc2c`.
[Receipt и сохранённые результаты](evidence/b08-current-20260909/receipt.json).
Сводный план, provider E2E и финальный release candidate не завершены.

## Среда и источник данных

Из сохранённой `portal_r12_20260909_rehearsal` создана новая отдельная
`portal_r12_b08_current_20260909_rehearsal`. Исходная копия ранее получена
[из зашифрованного production snapshot](EXECUTION-BRAIN-REHEARSAL-2026-09-09.md).
Это новый descendant уже восстановленной БД, не повторный backup/restore.
Создание заняло 8780,93 мс; исходная копия и её архив сохранены.

На момент preflight у исходной копии было 0 connections, свободно 14,62 GB.
В новой БД 121 таблица, размер 1 763 577 179 bytes; history содержит
1 638 180 health samples и 743 891 runtime samples. Приложение использует
обычную роль без superuser/createdb/createrole/replication/bypassrls;
все public objects принадлежат ей, PUBLIC access к новой БД отозван.

Прежние **197 файлов** — retained exact deployed bytes: `f530005` с отдельно
подтверждённым `control_panel.py` из `1207b63`. SHA прежнего ZIP совпал с
сохранённым [предыдущим compatibility receipt](EXECUTION-INTEGRATED-BACKEND-COMPAT-2026-09-08.md).
Текущие **205 файлов** совпали с `cd4a8b9` и production payload. Архивы,
полные manifests и schema snapshots сохранены вне Git; исходники не изменялись.

API работают отдельными systemd units на `127.0.0.1:18091/18092` с
`IPAddressDeny=any`, `IPAddressAllow=localhost`, ограниченными address families
и `Restart=no`. Эти properties прочитаны из работающих units; отдельный
packet-level egress test не выполнялся. HTTP paths используют только новую
synthetic account/ticket fixture. Production credentials/customer payloads
не экспортировались. Provider calls и выполнение provisioning jobs отсутствуют.

## Additive schema и реальный code rollback

Только в новой копии перед запуском удалены два добавленных индекса:
`ix_node_health_samples_node_sampled_id` и
`ix_node_runtime_metrics_lower_node_sampled_id`. Сохранены их определения
и полный schema hash. Это подготовка состояния до расширения схемы;
production и исходная восстановленная копия не изменялись.

| Фаза | Фактический результат |
| --- | --- |
| Прежний API | Startup и пять HTTP/SQL assertions PASS; 738 indexes |
| Новый API рядом с прежним | Штатный startup добавил оба индекса; по пять assertions на обеих версиях PASS |
| Новый API остановлен | Прежний процесс с тем же PID продолжил read/write, пять assertions PASS |
| Прежний API перезапущен | Новый PID, пять assertions PASS на расширенной схеме |

Каждый набор: health/plans 200, ticket без auth 401, ticket своей fixture с
auth 200, запись Product Event 200 с независимой SQL-проверкой. Итого
**25 HTTP assertions, пять distinct writes**, повторно подтверждённых после
всех фаз; ticket сохранён. Hash plans response менялся после startup/seed
и не считается byte-identical contract.

Все 1730 column definitions и 246 constraints сохранились; изменились только
два нужных индекса — 738 → 740. Прежние index definitions неизменны.
Полная schema после нового startup и после rollback совпадает, включая
новые индексы. Текущий source не содержит destructive contraction; удалять
рабочие данные или индексы при code rollback не требуется.

## Два worker и poison message

Текущая `PaymentEntitlementOutbox` реализация исполнена с настоящим
`ObservedQueuePool` и двумя независимыми PostgreSQL backend connections.
До seed отсутствовали pending/processing rows и provider grants, требующие
outbox backfill. Созданы только две owned fixture rows: нормальная и `{}`.
Paid order/grant в этой проверке — синтетические записи новой копии, не оплата.

Два конкурентных `run_payment_entitlement_outbox_once` дали по одному claim:
один delivered, один dead_letter `outbox_payload_invalid`. Ровно один grant
и одно provisioning job; claim tokens очищены, прежние outbox rows неизменны.
Повторный проход claimed=0. Прогон занял 81,25 мс; это не throughput/SLO.
Job остался в копии для проверки, provisioning runner не запускался.

Worker запускался через `systemd-run --collect --wait --pipe` с той же
loopback-only IP policy. Exit 0; процессы завершены. Оба API также штатно
остановлены (`MainPID=0`, inactive, Result=success, NRestarts=0).
Копия, fixture и evidence сохранены; units не включались в startup.

## Сохранённые ошибки инструментария

Первый setup остановился на существующем synthetic user ID до записи account;
созданная БД сохранена. Resume использовал новый отдельный ID и прошёл.

Первый worker precondition ошибочно обращался к исторической таблице
`entitlement_grants` (integer ID), а не `account_entitlement_grants` (varchar ID),
которую использует current model. PostgreSQL вернул 42883 при join с outbox.
Ошибочный query воспроизведён read-only; правильный query прошёл на production
и копии. Product code не исправлялся. Первый worker run остановился до seed
платежа; его FAIL сохранён, V2 изменяет только имя таблицы в harness и даёт PASS.

## Сопоставление с полным B08

| Исходный критерий | Доказательство и граница |
| --- | --- |
| Restore в изолированную настоящую PostgreSQL | Ранее выполненный encrypted Brain snapshot/restore 121 таблицы; clone/архив retained, backup tool bytes неизменны |
| Expand/contract | Текущий API добавил два индекса на реальных объёмах; старый API работает до/после и после restart; contraction в текущем diff отсутствует |
| Duplicate workers и poison messages | Текущий код и два реальных PostgreSQL connections, один grant/job и один dead letter; replay пуст |
| Payload completeness | Здесь 197+205 source hashes и 205 production hashes; [текущий production rollout](EXECUTION-B07-POOL-WAIT-2026-09-09.md) прошёл delayed health |
| Delayed-health rollback | [Ранее исполненный реальный SSH/systemd drill](EXECUTION-B08-DEPLOY-LAB.md): 503 и delayed crash вызвали автоматический restore и повторный health; только synthetic-service scope |

Deploy/restore machinery, outbox, provisioning service и requirements побайтно
совпадают с source прежнего SSH/systemd drill (`e74ee81`). Это перенос ровно
его ограниченного результата, не объявление нового fault injection в production.
Новый API/schema/worker результат выше выполнен отдельно. Локальный byte
rollback не используется вместо доказательства PostgreSQL recovery.

**Технические пункты B08 подтверждены.** Полный parent остаётся active из-за
явной зависимости от R12-B06 — реальных provider payment/refund/reconciliation.
G03 уже verified. Эти проверки не заменяют B06 и release acceptance Q01–Q05.

После работы production по-прежнему `cd4a8b9`: все 205 files и пять исходных
PID совпали с preflight, NRestarts=0, public health 200. В этом scope production
не разворачивался и не перезапускался. Runtime: Python 3.10.12, SQLAlchemy
2.0.46, aiohttp 3.13.3, psycopg2 2.9.11, uvicorn 0.34.0; `pip check` PASS.

Команды и exit states сохранены в receipt: prepare/resume, schema-state phases,
service-step phases, http-probe phases, обе worker версии, final-audit и
collect-results. Все изменения репозитория — отчёт, evidence и текущие ссылки.

Documentation checks: 33 tests PASS, context audit PASS, package validator
83 R12 IDs / 522 local links PASS, git diff --check PASS. Все 20 captures
и 21 external artifact hashes повторно сверены перед staging.

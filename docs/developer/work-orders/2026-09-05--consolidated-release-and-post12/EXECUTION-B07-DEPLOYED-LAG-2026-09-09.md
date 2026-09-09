# B07 — развёрнутый collector при медленном online read

**PASS_BOUNDED_RUNTIME_OBSERVATION**, backend `a8e6918`, brain-origin HTTPS
production. [Receipt](evidence/b07-deployed-20260909/receipt.json) сохраняет
27 health samples, outbox aggregates, source hashes и границы интерпретации.

Шесть соответствующих runtime files совпали с exact deployed payload.
В отличие от старого B07 отчёта, event-loop collector уже работает в production.
Сняты пять baseline health samples, 17 во время одного authenticated
`GET /api/admin/v2/support/online`, затем пять после него.

Online read вернул HTTP 200 за 17 590,05 мс. Во время него health отвечал за
11,62–94,95 мс; все 27 health requests успешны. Collector продолжал собирать
данные: samples 1953→1980, cumulative lag 176645→176652 мс. Максимальный
observed last lag в окне — 1 мс. Lifetime max 7905 мс существовал до прогона
и не относится к online request. Наблюдаемая задержка не сопровождалась
блокировкой event loop; конкретный HTTP/DB источник ожидания не установлен.

Payment DB counters не изменились: active 0, started/completed 2, failed 0,
queue total/max 0, duration total/max 15 мс. Это история процесса и отсутствие
новых payment use cases в данном окне, а не две новые операции или capacity proof.
Outbox до/после: pending/processing/dead_letter/unknown = 0, delivered = 2,
oldest open age = 0. SQL выполнен read-only с 2s statement / 500ms lock limit.

Raw capture поле `online_read.source_error_count` исключено из доказательств:
инструмент прочитал отсутствующий `errors` вместо `panel_errors` и получил
default zero. Оно не доказывает отсутствие ошибок нод. Остальные scalar
projections взяты из известных health fields. Raw customer/provider bodies,
identities и credentials не сохранялись.

Для online read штатный issuer создал одну owned fixture cookie; сессия
завершена logout. Настройки, API process, роли, платежи и доменные данные не
менялись. Команда: `python E:/r12-b07-observation-20260909/observe-runtime.py`.

B07 остаётся active: production SQL pool wait, connector queue и соответствие
рабочему коммерческому потоку не подтверждены этим наблюдением. 27 samples
не заменяют заданный performance gate и не дают p95/SLO PASS. Нет основания
менять pool limits или переписывать ORM по этим данным.

Проверки evidence и документации:

- `python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q` — 33 PASS.
- `python -B scripts/agent_context_packet_audit.py --platform-context-root .` — PASS.
- SHA256 всех шести retained captures B07/O01 совпали с receipts.
- `git diff --check` — PASS.

Повторное наблюдение O01 в 10:23 UTC подтвердило тот же живой процесс,
семь absolute refreshes и отсутствие HTTP anomalies. Deadline неизменен.

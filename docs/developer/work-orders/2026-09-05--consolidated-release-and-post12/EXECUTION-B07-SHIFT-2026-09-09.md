# B07 — чтение смены без блокировки API

Правка feature `4434270`, integration `68d9610`, подписанный
[PR #250](https://github.com/Kiwunaka/portal/pull/250) слит в `3478fc4`.
Tree `d01fb068` совпал; проверки PR PASS, release-base-isolation SKIPPED.
Backend `3478fc4` развёрнут; четыре CI PASS, 204 live hashes и metadata PASS.
[Receipt и captures](evidence/b07-shift-20260909/receipt.json) сохраняют результаты
и hashes исходных logs/instruments.

## Дефект и изменение

После поставки online snapshot отдельный production запрос
`/api/admin/v2/shift/overview` занял 4795,98 мс; cumulative event-loop lag
увеличился на 4672 мс. Синхронная projection metrics/capacity/alerts
исполнялась непосредственно в async route. Это отдельный воспроизведённый
stall, не доказательство медленного SQL или ожидания пула.

Оба входа, Operator Center BFF и retained legacy overview, теперь вызывают
projection через существующий Starlette threadpool. Сессия DB создаётся,
используется и закрывается в том же рабочем потоке. Права, envelope, SQL,
схема, зависимости и frontend не менялись; canonical monitoring owner обновлён.

## Проверки и пакет

- Два regression tests для BFF и legacy упали до правки: projection оставалась
  в потоке event loop. После правки они и прежний cutover scenario прошли
  на feature и integration trees: по 3 PASS.
- `python -B -m pytest -p no:cacheprovider portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py tests/test_api_auth_and_tickets.py tests/test_subscription_preview_api.py tests/test_admin_ops_api.py tests/test_admin_payments_api.py -q` — **208 PASS, 8 subtests PASS**, 948,46 с.
- Подготовлены 204 runtime files. Git- и raw-byte deltas относительно
  развёрнутого `2b37f97` — только `api.py` и `api_admin_routes.py`.
  Шесть schema/dependency inputs и frontend inputs прежние.
  Полный 15-step local quality gate не повторялся.
- Перед поставкой 204 live hashes совпали с `2b37f97`; пять units active,
  NRestarts=0, сохранены 14 rollback directories при retain-count 50.

При первом запросе GitHub отказал в merge commit: репозиторий разрешает
squash. Повторная операция squash завершилась с точным деревом и подписью.
Это ограничение способа слияния, не сбой CI или поставки.

B07 целиком остаётся active: commercial pool/connector wait и общая latency
acceptance этим узким исправлением не закрываются. O01 absolute expiry
после прежней ошибки raw bytes требует отдельного нового 12-часового прогона.

## Поставка и повторный замер

Штатный deploy с `--brain-ip 82.21.114.104`, существующим закрытым `--passwords`,
`--backup-retain-count 50 --restart portal-api` завершился с exit 0.
Rollback directory `20260909T113538Z-15348` сохранён. После проверки всех
204 hashes обновлены только два build metadata значения; повторный restart
API и health PASS. Все пять units active, NRestarts=0; остальные четыре
службы сохранили PID относительно predeploy baseline.

Brain-origin readback подтвердил exact API commit. На новом снимке смена
вернула HTTP 200 за **6368,37 мс**; 16 health samples, в том числе шесть во
время projection, вернули 200, maximum **131,47 мс**. Cumulative loop lag
вырос на **11 мс** вместо прежних 4672 мс. Outbox aggregates прежние,
fixture завершена logout. Данные клиентов, providers и credentials не экспортированы.

В этом окне многосекундная блокировка API не повторилась. Длительность самого
ответа смены не сократилась; её нельзя объявить исправленной или назвать
этот одиночный замер p95/SLO PASS. DB/HTTP pool wait отдельно не измерен.

## Новый O01 elapsed run

После завершения API-поставки запущен V3 с теми же production TTL: 1800 и
43200 секунд. [Launch и начальный readback](evidence/operator-elapsed-v3-20260909/receipt.json)
подтверждают отдельный живой процесс и два owned fixtures; прежние сессии,
roles, compatibility flags, clock и deadlines не менялись.

Idle deadline — **15:07 мск 9 сентября**; absolute — **02:37 мск 10 сентября**.
Проверки выполняются после deadline +3 с; absolute cookie опрашивается каждые
пять минут. Raw hash `security.py` фиксирован `02cd79f4…`; новая упаковка
отдельно отвергает любую лишнюю побайтовую смену. Оба результата V3 пока
**RUNNING_NOT_PASSED**; idle PASS предыдущего V2 и его source-guard failure
сохранены отдельно. Новый OIDC-вход этот fixture-run не доказывает.


Evidence checks: `python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q` — 33 PASS; `python -B scripts/agent_context_packet_audit.py --platform-context-root .` — PASS; package validator — 83 R12 IDs / 503 local links PASS; `git diff --check` и hashes девяти retained captures — PASS.

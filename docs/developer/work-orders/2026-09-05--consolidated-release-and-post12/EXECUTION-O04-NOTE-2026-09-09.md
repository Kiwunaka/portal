# O04 — рабочие сценарии и внутренняя заметка роли поддержки

**PASS_BOUNDED_O04_RUNTIME / release открыт.** На Brain проверена отдельная
копия backend `cd4a8b9` с синтетической PostgreSQL БД. Проверка обнаружила
реальный 403 при добавлении внутренней заметки ролью `support_l2`; исправление
прошло через [PR #253](https://github.com/Kiwunaka/portal/pull/253) и развёрнуто.
[Receipt](evidence/operator-note-20260909/receipt.json) содержит 16 проекций
и hashes 43 внешних исходников/логов, включая исходный FAIL.

## Ошибка и исправление

Интерфейс показывал заметку роли поддержки, но готовил команду через общий
`/api/admin/action-intents`, требующий `legacy.admin.access`. Через support
workspace команда также была запрещена: `ticket.note` отсутствовала в списке.
Теперь UI использует существующие prepare/execute маршруты support v2.
Сервер получает environment и actor из сессии и требует `support.write`.
Legacy-доступ не расширен. Stored intent, версия обращения, idempotency,
приватность заметки и очищенный аудит сохранены. Reply/status остаются
прежними compatibility-маршрутами и в этот PASS не входят.

Source `4792234`, подписанный GitHub commit `a31d875`, merge `9e01ded` имеют
один tree `d1c59839b2cb377b0de86f6c26b2eceb0de628af`. PR меняет пять файлов;
в backend payload из 205 файлов меняется только `admin_v2/router.py`.
Общая ветка плана `853b0b5` дополнительно получила пропущенную при прежней
интеграции правку причины absolute expiry из уже развёрнутого `a8e6918`
и её исходный тест. Это перенос принятой правки, не новое изменение TTL.
Все 205 backend файлов общей ветки совпали с текущим source после нормализации
только CRLF/LF; непоставленная запись cutover inventory остаётся в своей ветке.

## Проверки

- До правки существующий support API test с проверкой заметки дал
  `operator_action_not_allowed` / 403. После — PASS: L1 добавляет заметку,
  replay не создаёт дубль, customer API не выдаёт тело, audit не содержит
  тело, readonly получает 403. На текущем master source и после переноса
  в общую ветку выполнены note и absolute-expiry проверки: по 2 PASS.
- `python -B -m pytest -p no:cacheprovider tests/test_admin_ops_api.py
  tests/test_admin_payments_api.py tests/test_support_work_service.py
  tests/test_api_auth_and_tickets.py tests/test_admin_v2_openapi_contract.py
  -q --tb=short` — 159 PASS, 8 subtests PASS, 702,83 с. Этот общий прогон
  завершён до переноса прежней absolute-expiry правки; её отдельная проверка
  и исходный deployed receipt сохранены, полный прогон не объявлен повторным.
- `npm.cmd run test:e2e` — build и 80 Playwright PASS; `npm.cmd run lint` — PASS.
  Отдельный build подписанного source выполнен через
  `npx.cmd --yes --package=node@22.14.0 -- npm run build` — PASS.
- 33 docs tests, platform context audit, `git diff --check` — PASS.

Первая изолированная HTTP-проверка остановилась на 403 legacy prepare после
шести успешных сценариев. Её результат сохранён. Исправленная копия размещена
в отдельном каталоге; исходник прежней B08-проверки не изменялся.
Повтор использовал новый synthetic ticket и новые сессии существующих
fixture-операторов. Исходный ticket и первая проекция остались в БД.

Восемь сценариев повторного прогона PASS:

1. Серверный исходный SLA 24 часа.
2. Одновременный claim двух операторов: ровно один 200, второй 409 stale_version.
3. Назначение и waiting сохраняют серверный deadline.
4. Связь обращения с attempt; raw trace/session/device и meta не выдаются.
5. Создание инцидента, escalation и двусторонний readback связи.
6. Создание назначенной задачи, её отображение в «Моей смене» и начало работы.
7. Внутренняя заметка, replay, отсутствие тела у пользователя и в audit.
8. Настройка synthetic SLA в прошлое через разрешённую команду даёт breached,
   закрытие обращения — stopped. Production clock/TTL не менялись.

Измерены полные HTTP-последовательности задач: claim 115,57 мс,
incident/link/readback 119,28 мс, create/find/start task 138,16 мс,
note/execute/replay/public/DB readback 134,62 мс. Это автоматические
brain-origin loopback измерения, не время работы человека в UI и не
нагрузочный SLO. Реального внешнего OIDC-входа этот fixture не выполнял.
Провайдеры и доставка клиентских сообщений не вызывались.

В 14:39:23 UTC тестовый API остановлен, активных fixture sessions 0.
БД, исходные результаты и код сохранены. Все 205 production hashes,
пять production units и dotenv остались прежними на этом срезе.

## Поставка и непрерывность сессии

Оба PR checks и оба master checks — Guardrails / Release v2 Contract — PASS
для exact signed/merge commits. Release-base-isolation был SKIPPED_NOT_PASS.
Из clean checkout `9e01ded` выполнен штатный
`python -u scripts/remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104
--passwords <existing-local-access-file> --backup-retain-count 50
--restart portal-api`: exit 0. Все 205 deployed hashes совпали. Backup
`/root/portal_bot.deploy-backups/20260909T145005Z-27856` побайтно содержит
205 прежних файлов `cd4a8b9`. Restore не выполнялся; backup сохранён.

Build metadata привязана к `9e01ded`, API health PASS. Изменены только два
metadata fields dotenv, остальные значения сохранены. Перезапускался только
API; четыре других production PID прежние, все units active / NRestarts=0.

Админка из подписанного `a31d875` — тот же tree, что merge `9e01ded` —
поставлена отдельным пакетом `20260909145204`: 189 remote hashes совпали.
Существующий deploy helper создал архив, затем операторский скрипт проверил
его и атомарно переключил только adminapp pointer. Прежние 189 файлов
сохранены побайтно, `adminapp.rollback` указывает на `20260909045925/adminapp`.
Остальные сайты и service PID сохранились. HTTPS index/tickets/build/routes
прошли на brain-origin; current-origin дополнительно подтвердил новый JS chunk
заметки. HTML/metadata revalidate, имя изменённого chunk отличается от прежнего.

O01 V3 в 14:53:49 UTC подтверждён тем же живым PID/start ticks; 39-й refresh
после API restart прошёл в 14:52:26, HTTP anomalies=0. Raw security.py hash
и absolute deadline `23:37:16 UTC` / 02:37 мск 10 сентября сохранены.
Absolute expiry всё ещё RUNNING_NOT_PASSED. Production mutation заметки
не выполнялась: runtime proof относится к изолированным HTTP/PostgreSQL
фикстурам с теми же bytes router.py, а поставка — к hashes и readback.

## Оставшиеся критерии

Связь самого support bundle с конкретной попыткой и зависимость O01 остаются
открытыми. Связь ticket → attempt не подменяет этот критерий. Parent O04
не получает полный PASS; итоговый client candidate, физические проверки
и общий сводный план этим исправлением не закрыты.

Итоговая проверка evidence: 33 docs tests, platform context audit,
package validator (83 R12 IDs / 533 local links) и `git diff --check` PASS.

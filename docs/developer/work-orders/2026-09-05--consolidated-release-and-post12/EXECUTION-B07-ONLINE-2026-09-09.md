# B07 — исправление online snapshot панелей

Источник: feature `7fe020a`, отдельный integration `ab5b775`, подписанный
[PR #249](https://github.com/Kiwunaka/portal/pull/249). Backend **2b37f97 развёрнут** после четырёх CI PASS;
реальный online API readback и новая build identity подтверждены. [Receipt и агрегаты](evidence/b07-online-20260909/receipt.json)
сохраняют exact source hashes и ссылки на полные локальные captures.

## Наблюдаемый дефект

Семь настроенных панелей опрашивались с concurrency 4. Исходный collector
сделал 421 вызов `_get_online_emails`: при неудачном ответе флаг fetched
оставался false, и следующий клиент снова вызывал тот же endpoint. На одной
ноде 71 обращение заняло суммарно 6237,19 мс. Неудачный login отдельной панели
занял 15226,25 мс; полное наблюдение — 17726,47 мс. Этапы вложены друг в друга,
поэтому их длительности нельзя складывать как независимые интервалы.

Дополнительный readback установленных панелей: все шесть доступных вернули
404 на `POST /panel/api/inbounds/onlines`, но 200/success/list на
`POST /panel/api/clients/onlines`. Седьмая не прошла login. На первой панели
также проверен прежний GET: 404. Ни cookies, ни содержимое списков клиентов
в captures не сохранялись. Текущий маршрут также используется в
[официальном frontend 3x-ui](https://github.com/MHSanaei/3x-ui/blob/main/frontend/src/pages/inbounds/useInbounds.ts);
решение привязано к проверенным установленным панелям, а не только к upstream.

## Изменение и границы

`PanelClient` использует новый POST с существующим CSRF header. Оба метода,
summary и список строк, делают не более одной попытки online list на снимок;
следующий снимок может повторить запрос. Неуспех не превращается в успешный
пустой список; существующий last-seen inference сохранён. Pool limits, ORM,
таймауты и конфигурация нод не менялись.

Промежуточный эксперимент только с ограничением повторов снизил число запросов
421→6, но не исправлял недоступность данных. Финальный отдельный процесс с
тремя exact candidate methods получил **6/6 пригодных online lists**. Полное
время 15902,27 мс: отдельный отказ login сохраняется. Это диагностическое
наблюдение, не API p95 или SLO PASS и не доказательство deployed behavior.

## Проверки

- Regression для unavailable list упал до исправления в обоих methods:
  три обращения вместо одного. После исправления проверяет одну попытку,
  повтор на следующем снимке и сохранение last-seen inference.
- Новый route test проверяет POST, CSRF/session binding, полученный список
  и успешный пустой список.
- `python -B -m pytest -p no:cacheprovider tests/test_collect_node_metrics.py tests/test_collect_node_metrics_observability.py tests/test_panel_client_metrics.py tests/test_live_probe_scripts.py tests/test_panel_client_multi_inbound.py tests/test_panel_client_conflicts.py tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`:
  **76 PASS, 2 subtests PASS**; 28 существующих datetime deprecation warnings.
- На integration tree: `python -B -m pytest -p no:cacheprovider tests/test_panel_client_metrics.py tests/test_panel_client_multi_inbound.py tests/test_panel_client_conflicts.py -q`:
  **18 PASS, 2 subtests PASS**.
- Context audit и `git diff --check` — PASS. 15-step local quality gate
  целиком не повторялся; source delivery и production readback ещё ожидаются.

Из 204 runtime files меняется только `panel_client.py`; шесть schema/dependency
inputs и frontend inputs совпадают с развёрнутым `a8e6918`. O01 absolute expiry
продолжается своим процессом; этот эксперимент не менял его сроки или sessions.
B07 целиком остаётся active: коммерческий pool/connector wait не измерен.

## Поставка и последующее наблюдение

PR #249 слит с проверенным деревом и действительной подписью. Два PR checks и
два master checks PASS. Штатный remote deploy с `--brain-ip 82.21.114.104`,
явным `--passwords` на существующий закрытый локальный файл,
`--backup-retain-count 50 --restart portal-api,portal-bot,portal-worker` завершился
с exit 0; rollback-копия сохранена. Первый запуск остановился до поставки на
отсутствующем default password path нового worktree; его log сохранён отдельно.

Все 204 установленных payload hashes совпали. API, bot и worker перезапущены;
helpbot и feedbackbot сохранили PID. Health и 5/5 active, NRestarts=0 PASS.
API meta вернула exact `2b37f9765ba07fd0f37d0c894486809ac4bc9f75`.
Online GET: HTTP 200, 17548,66 мс, один panel error согласован с summary.
Fixture завершена logout. Outbox неизменен, платежей не выполнялось.

В этом окне cumulative loop lag вырос на 3969 мс; один health занял 3928,89 мс.
Поэтому ускорение или отсутствие stall не заявляется. Изолированный read-only
Postgres profile online projection дал четыре SQL запроса суммарно 5,62 мс,
полную projection 22,66 мс, acquisition 5,31 мс; последнее включает cold
connection/pre-ping и не является чистым production pool wait.

Journal fixed-route projection показывает concurrent `/shift/overview` в
конце stall. Отдельный authenticated shift read воспроизвёл 4795,98 мс HTTP и
4672 мс cumulative loop lag. Его синхронная projection выполняется в async
маршруте. Исправление вынесено в **draft PR #250**, broader backend checks и
CI выполняются. До его поставки этот stall остаётся открытым.

## Ошибка побайтовой упаковки и O01

Уточнение прежней формулировки «меняется только panel_client.py»: это верно для
Git-содержимого, но не для raw bytes. Свежий worktree также заменил пять LF
на CRLF в `admin_v2/security.py`; после CRLF→LF файлы полностью совпадают.
Raw SHA изменился 881305ee…→02cd79f4… . Именно raw source guard остановил
O01 v2 в 10:59:47 UTC после 14 refreshes. Обе его fixture sessions отозваны
штатным cleanup; idle PASS сохранён, absolute expiry **не проверен**.

Это ошибка подготовки этой поставки, а не доказательство дефекта expiry.
Для следующего пакета prepare-payload теперь отдельно проверяет raw deltas и
отказывает на любой лишней побайтовой смене. Новый длительный прогон пока
не запущен: он начнётся после текущей API-поставки, без изменения TTL/времени.

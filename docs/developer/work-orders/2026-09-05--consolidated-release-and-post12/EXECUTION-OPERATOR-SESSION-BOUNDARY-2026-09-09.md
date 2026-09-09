# O01 — отзыв сессий и причина истечения срока

**PASS_BOUNDED_SESSION_BOUNDARY_AND_DEPLOY**, backend
`a8e6918ccc166a58ae65ba7d08feea63ce3a9623`, brain-origin HTTPS production.
[Receipt](evidence/operator-session-20260909/receipt.json) сохраняет девять
проекций, hashes источников/логов и отдельный handle длительной проверки.
Это дополняет [реальный OIDC-вход](EXECUTION-OPERATOR-LIVE-2026-09-09.md),
не заменяя его синтетическим bootstrap.

## Исправление и выкладка

Достижение абсолютного срока ошибочно записывалось как `idle_expired`:
активность заранее ограничивает idle deadline абсолютным сроком, поэтому
в момент отказа оба значения равны. Теперь журнал выбирает первый достигнутый
deadline и `absolute_expired` при равенстве. Сам допуск, сроки и cookie policy
не менялись. Каноническое описание обновлено в `adminapp/README.md`.

Регрессия воспроизведена до правки и прошла после неё. Обязательные проверки:
53 API-теста, 80 Playwright-тестов с build, lint, 33 docs checks и context
audit PASS. Одна проверка нового поведения и существующая idle/revoke проверка
дали 2 PASS. Exact source tree прошёл signed promotion и
[PR #248](https://github.com/Kiwunaka/portal/pull/248). Hosted guardrails и
cross-repository contract PASS; release-base-isolation был SKIPPED и не
переименован в PASS.

В production совпали все 204 payload hashes. Backup сохранён:
`/root/portal_bot.deploy-backups/20260909T083858Z-27840`.
Перезапущен только `portal-api`, health PASS. Публичная build identity равна
`a8e6918`; остальные значения dotenv и процессы четырёх других units сохранены.

## Реальная session boundary

На `d9b2583`, затем на развёрнутом `a8e6918` выполнены по 11 HTTP assertions:
свежая сессия; отказ CSRF/Origin и сохранение сессии после отказа; отзыв одной
owned test session другой; отказ старой cookie; повторный отзыв; logout и
отказ cookie replay. Cookie Secure/HttpOnly/SameSite=strict, host-only `/`;
logout возвращает Clear-Site-Data для cookies/storage.

Каждый прогон создавал две временные сессии через существующий compatibility
bootstrap, с guard против вытеснения прежних сессий. Обе отозваны. Прежние
сессии, роли и `telegram_oidc` identity остались неизменными. Tokens, session
IDs, Telegram ID и auth material не экспортировались. Это не новый внешний
OIDC-вход, не cross-role denial и не отключение legacy entrypoint.

## Настоящие сроки — RUNNING, не PASS

На неизменённых production TTL запущены две отдельные owned-сессии:

- idle: 1800 секунд, deadline `2026-09-09T09:42:28.787420Z`;
- absolute: 43200 секунд, deadline `2026-09-09T21:12:29.146462Z`.

Вторая получает `/auth/me` каждые пять минут; проверяется неизменность её
absolute deadline. Первая не используется до истечения idle. После deadline
проверяются реальный HTTP 401 и соответствующий revoke reason в БД. Время,
TTL и записи сессий вручную не сдвигаются. Cookies живут только в памяти
процесса; cleanup выполняется через штатный logout. Исходник security.py
проверяется по hash на каждом проходе; изменение останавливает тест.

На первом retained observation процесс `41577`, start ticks `423686036`
подтверждён живым и первый refresh выполнен. Рабочая директория:
`/root/portal-r12-evidence/operator-elapsed-expiry-20260909`.
Для следующего наблюдения использовать существующий
`E:/r12-operator-session-20260909/observe-elapsed-expiry.py`; не запускать
вторую копию по тайм-ауту наблюдения. Реальное истечение обоих сроков,
cross-role denial, legacy cutover и полный O01 остаются открытыми.


## Уточнение 09:44 UTC — первый elapsed runner завершился ошибкой

Наблюдение в 09:42 обнаружило завершение первого процесса ещё в 09:22:
`JSONDecodeError` при HTTP refresh и обоих cleanup requests. Сам HTTP status
первый инструмент не сохранил, поэтому причину ответа установить по нему
нельзя. Истечение сроков не проверено. Две оставшиеся owned fixture sessions
найдены по точному времени создания и identity, отозваны; остальные сессии
не изменены. Исходное наблюдение RUNNING выше относится к раннему срезу.

[Новый receipt](evidence/operator-elapsed-v2-20260909/receipt.json) хранит failure,
cleanup и запуск отдельного v2 процесса `47383`, start ticks `423880189`.
Compatibility bootstrap остаётся выключенным. Две новые fixture cookies выданы
штатным внутренним issuer; это не новый внешний OIDC-вход. При не-JSON ответе
инструмент сохраняет status/MIME/размер/hash и допускает два повтора через две
секунды; все такие случаи остаются видимыми. При сбое HTTP cleanup он отзывает
только собственные fixture sessions через DB. Raw body и cookies не сохраняются.

Новые реальные deadlines: idle `2026-09-09T10:14:42.041674Z`, absolute
`2026-09-09T21:44:42.057920Z` (13:14 мск и 00:44 мск 10 сентября).
Production TTL и время не сдвигались. Источник security.py прежний и проверяется
на каждом цикле. Наблюдать существующий процесс командой
`python E:/r12-operator-session-20260909/observe-elapsed-expiry-v2.py`.
Первое наблюдение v2: RUNNING, ещё без expiry assertions. Полный O01 открыт.


## Реальный idle expiry — PASS, 10:14:45 UTC

V2 после 1800 секунд бездействия и трёхсекундного запаса получил
HTTP 401 `operator_session_expired`; БД сохранила отзыв `idle_expired`.
Текущее время, production TTL и deadlines не менялись. Наблюдение 10:15
подтвердило тот же живой PID/start ticks, шесть absolute refreshes, неизменный
absolute deadline и отсутствие HTTP anomalies. Absolute expiry остаётся
RUNNING до `2026-09-09T21:44:42.057920Z`; полный O01 пока открыт.


## V2 остановлен после смены raw source — 10:59:47 UTC

[Поставка online fix](EXECUTION-B07-ONLINE-2026-09-09.md) сохранила Git-содержимое
security.py, но изменила пять окончаний строк LF→CRLF. Raw guard остановил
runner с AssertionError после 14 refreshes. HTTP anomalies отсутствуют;
cleanup отозвал обе fixture sessions. Idle PASS остаётся, absolute expiry
не выполнен. Старое ожидаемое время 00:44 мск больше не является активным
сроком прогона. Новый run будет запущен после текущей API-правки.


## V3 после API-поставки, 11:37 UTC

[Новый запуск](EXECUTION-B07-SHIFT-2026-09-09.md) привязан к `3478fc4` и
побайтно проверенному `security.py` (`02cd79f4…`). Процесс жив; idle deadline
15:07 мск 9 сентября, absolute 02:37 мск 10 сентября. Оба результата V3
RUNNING_NOT_PASSED. V2 idle PASS и его неуспешный absolute run сохранены.


V3 readback **12:07:28 UTC**: реальный idle expiry PASS — HTTP 401,
`operator_session_expired`, DB `idle_expired`, session revoked. Отдельный
процесс жив, absolute cookie получила шесть успешных refreshes, anomalies=0.
Absolute deadline прежний: 23:37 UTC / 02:37 мск 10 сентября; эта проверка
ещё RUNNING_NOT_PASSED. Clock и deadlines не изменялись.


V3 readback **12:32:23 UTC** после [поставки индексов](EXECUTION-B07-INDEXES-2026-09-09.md):
тот же PID/start ticks жив; 11-й refresh прошёл в 12:32:19 после API restart.
HTTP anomalies=0, raw security.py hash и absolute deadline сохранены.
Source at start `3478fc4`, текущий backend `1ef1f50`; source continuity
ограничена проверенным security.py, полный source tuple не объявляется неизменным.
Absolute expiry всё ещё RUNNING_NOT_PASSED.


V3 readback **13:27:53 UTC** после [поставки pool observers](EXECUTION-B07-POOL-WAIT-2026-09-09.md):
тот же PID/start ticks жив; 22-й refresh прошёл в 13:27:21 UTC после
API restart. HTTP anomalies=0, raw security.py hash и absolute deadline
23:37 UTC сохранены. Current backend `cd4a8b9`, source at start `3478fc4`;
continuity ограничена указанным исходником авторизации и процессом.
[Новый readback](evidence/b07-pool-wait-20260909/session-continuity.json)
не означает PASS абсолютного истечения; оно RUNNING_NOT_PASSED.

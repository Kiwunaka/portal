# O01/O02 — реальный OIDC-вход, step-up и 28 страниц

Владелец зарегистрировал `https://admin.pokrov.space/` в BotFather и подтвердил
два запроса Telegram. На опубликованной админке прошли настоящий OIDC-вход и
same-session step-up. Все 28 маршрутов текущего manifest открыты через эту
операторскую сессию. Роли, клиентские записи и рассылки не изменялись.

Источники: frontend `03920525bfc3993591a39d21e35bbe2e7e1d663d`, backend
`d3eba8945e74eca025e2a8589be110d070fb562d`, API schema `admin-v2.1`.
Статический fingerprint и backend identity ранее проверены в
[выкладке платформы](EXECUTION-PLATFORM-DEPLOY-2026-09-09.md) и
[последующей выкладке worker](EXECUTION-A04-PRODUCTION-MIGRATION-2026-09-09.md).
Текущий браузер показал FE `03920525`, source `clean`, environment `production`.

## Вход и дополнительное подтверждение

[Серверный readback](evidence/operator-live-20260909/real-oidc-login-step-up.json)
получен командой `python -B read-real-oidc.py` через уже доверенный SSH.
Он подтверждает для owned оператора:

- `session.oidc`, `success`, `telegram_oidc_verified`;
- последующий `session.step_up` с тем же reason и той же session;
- непустой step-up timestamp, активную production-сессию и единственную
  прежнюю роль `superadmin`, выданную до теста.

До step-up попытка только подготовить предпросмотр выдачи роли была
заблокирована; UI предложил подтверждение через OIDC. После него браузер
вернулся в админку, сервер сохранил событие step-up. Команда выдачи роли не
исполнялась. Сессия оставлена активной для владельца.

До изменения BotFather provider entry возвращал `redirect_uri required`.
После настройки — обычную страницу Telegram Login. Этот промежуточный PASS
сохранён отдельно и не подменяет последующее доказательство настоящего входа.
Токены, cookies, raw identity и callback URL с временными параметрами не
попали в retained evidence.

## Проверка маршрутов

[28 наблюдений UI](evidence/operator-live-20260909/authenticated-routes.json)
сопоставлены с текущим manifest: семь рабочих областей и 21 capability route.
Проверялись открытие страницы, завершение загрузки и отсутствие login form;
customer records и содержимое таблиц не выгружались.

- 26 страниц показали нормальную сессию и API после загрузки.
- `/online` открылся с нормальной сессией и неполным снимком панелей нод.
  UI отразил деградацию источника; это не отказ авторизации или падение маршрута.
- `/broadcast` показал форму. До отправки исходник намеренно оставляет статус
  операции и сессии этого блока `missing`. Рассылка не готовилась и не отправлялась.

Первичные automation waits на пяти страницах истекли. Повторное наблюдение
подтвердило итоговые состояния. Отсутствующие поля в AX diff не трактовались
как отказ; спорные страницы проверены полным AX state. Длительность ожидания
инструмента не является замером серверной latency.

## Граница приёмки

O01/O02 остаются открыты: этот срез не воспроизводит idle/absolute expiry,
revocation и denial всех ролей на production, все исходы write-команд и полный
legacy cutover/rollback. Предыдущие CSRF/origin/bootstrap проверки сохранены
в отдельной выкладке; они не выдаются за результаты текущей браузерной сессии.
Legacy bootstrap и доступы не отключались и не расширялись.

[Receipt](evidence/operator-live-20260909/receipt.json) хранит hashes safe
артефактов. Проверки документации и ссылок выполнены совместно с A04 report;
33 docs tests, context audit, package links и `git diff --check` — PASS.

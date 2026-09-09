# O01 — отключение compatibility bootstrap в production

**PASS_COMPATIBILITY_DISABLED**, backend `a8e6918`, brain-origin HTTPS.
В production явно установлен `ADMIN_OPERATOR_LEGACY_BOOTSTRAP_ENABLED=false`.
[Receipt](evidence/operator-cutover-20260909/receipt.json) сохраняет preflight,
первоначальные отказы инструмента, rollback и успешный повтор.

Единственный действующий оператор уже имел `telegram_oidc`, связанную identity,
роль `superadmin` и сохранённые реальные OIDC login/step-up. Router и
web_auth_service совпали с источником этой проверки `d3eba89`; единственное
изменение security.py выбирает причину истечения срока. Внешний OIDC-вход
повторно не выполнялся. Existing session и OIDC start проверены через текущий
production API; это не новая проверка полного provider flow.

Пять HTTP-проверок прошли: health, сохранение существующей сессии, точный
`403 operator_legacy_bootstrap_disabled`, точный
`403 operator_legacy_step_up_disabled`, доступность OIDC start. Перезапущен
только `portal-api`; PID остальных четырёх units, роли, прежние сессии и
прочие dotenv values сохранены. Временная проверочная сессия отозвана logout.
TTL, deadlines, source bytes и cookies прежних сессий не изменялись.

Первый preflight предполагал явное `true` в dotenv, но флаг отсутствовал и
брался из default. Он остановился до изменения конфигурации; созданная fixture
session отозвана. Затем запрос step-up с `{}` получил schema validation 422:
compatibility path требует отсутствующее тело. Guard вернул точный прежний
dotenv, перезапустил API и подтвердил health. Повтор с корректным HTTP-запросом
прошёл. Оба результата сохранены; 422 не объявлен дефектом продукта.

Rollback backup последнего прохода находится только на Brain:
`/root/portal_bot.deploy-backups/20260909T093908Z-operator-bootstrap`.
Возврат compatibility-флага допустим только как rollback этой миграции
после проверки неизменности остальных dotenv values. Секреты и raw identity
не экспортировались. Legacy route redirect/parity относится к O02 и не
закрывается отключением bootstrap.

Команды: `python E:/r12-operator-session-20260909/disable-legacy-bootstrap.py`
— успешный повтор, пять assertions PASS; существующий
`tests/test_admin_ops_api.py::test_admin_v2_oidc_login_and_step_up_are_cookie_bound_and_require_provisioned_operator`
— 1 PASS. Реальная проверка idle/absolute срока продолжает использовать уже
созданные сессии; новый bootstrap для неё не нужен. Полный O01 пока открыт.

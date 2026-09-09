# O01 — production denial между ролями

**PASS_BOUNDED_ROLE_DENIALS**, backend `a8e6918`, brain-origin HTTPS production.
[Receipt](evidence/operator-rbac-20260909/receipt.json) и полный safe readback
содержат результаты для всех десяти non-superadmin ролей. Для каждой выбран
один запрещённый маршрут; это не исчерпывающая матрица всех API/permission.

Один изолированный оператор с `identity_source=r12_isolated_fixture` и пустой
внешней identity последовательно получил временные роли с 15-минутным сроком.
Cookies выпускались штатным внутренним session issuer; внешний OIDC в этом
прогоне не проверялся. Действующая HTTP-служба подтверждала роль через
`/auth/me`, разрешала `/meta`, затем возвращала точный
`403 operator_permission_denied` для выбранного чужого permission.

Проверены readonly, support_l1, support_l2, sre, network_operator,
payments_operator, growth_operator, release_manager, security_auditor и
incident_commander. Запрещённые маршруты покрывают support.read,
support.sensitive.read, network.read, money.read, releases.read и
governance.operators.read. Политика сверена с текущим role registry;
security.py, roles.py и router.py совпали с развёрнутыми payload hashes.

Каждая из десяти сессий завершена штатным logout. Все fixture roles отозваны,
оператор приостановлен: активных ролей и сессий ноль. 21 audit row сохранена,
записи не удалялись. Прежние операторы, их identity/status и роли совпали до
и после. Raw identifiers, cookies и credentials не экспортировались.

Команда: `python E:/r12-operator-session-20260909/run-rbac-live.py` — exit 0,
10 role denials и 20 positive controls PASS, cleanup PASS. Исходники fixture
и launcher сохранены локально с hashes в receipt. Product source и runtime
настройки не менялись. Реальные idle/absolute deadlines проверяет уже
запущенный процесс из предыдущего session-boundary отчёта; O01 остаётся active.

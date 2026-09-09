# O02 — привязка маршрутов и фактический static rollback

**PASS_BOUNDED_PRIMARY_READS_AND_STATIC_ROLLBACK**: frontend `0392052`, backend
`a8e6918`, static release `20260909045925`, brain-origin HTTPS production.
[Receipt](evidence/operator-routes-20260909/receipt.json) содержит route map,
readback, полные static file hashes и результат переключения.

## Маршруты и права

Текущий manifest содержит 28 маршрутов и семь workspaces. Реестр компонентов,
sections и основной API каждого экрана сверены с source; frontend implementation
не изменился относительно развёрнутого `0392052`. Route map связывает каждый
экран с компонентом, workspace, API method/path, permission и ролями из текущего
server registry, имеющими это permission. Это основной источник данных экрана;
detail actions и дополнительные панели остаются в workspace cutover contract.

22 уникальных primary GET вернули HTTP 200 и JSON. V2 projections указали
`admin-v2.1`; legacy user list использует свой прежний envelope. `/broadcast`
показывает локальную форму и связан с `growth/action-intents`; команда рассылки
не выполнялась. API fingerprint соответствует `a8e6918` и ожидает
`pokrov-operator-center`. Проверочная cookie выпущена внутренним issuer,
завершена logout; прежние сессии сохранились. Нового внешнего OIDC-входа этот
проход не доказывает — реальный вход и 28 UI routes сохранены отдельно.

Readback не является latency acceptance: network fleet занял 6,687 с,
shift overview — 6,994 с, support online — 17,549 с. Это одиночные замеры,
не p95 и не подтверждение всех источников панелей. Raw customer/provider
payload, identities и cookies не экспортировались.

## Rollback

До и после операции совпали 189 файлов текущей админки, 156 файлов старой
и 386 файлов кабинета. Production pointer админки атомарно переключён с
`20260909045925/adminapp` на сохранённый `20260819120323/adminapp`; HTTPS root
отдал точные bytes старого index.html. Затем текущий pointer восстановлен;
root и `__build.json` снова совпали с текущими hashes. Все три исходных
pointers и все файлы сохранены, API health PASS. Интервал старого pointer:
`09:52:30.310381Z` — `09:52:30.368056Z`.

У старого bundle нет build manifests, поэтому использован отдельный guarded
pointer drill с полным inventory. Ему не приписан новый fingerprint или
результат authenticated legacy UI. База, API process и конфигурация не менялись.

## Исправление inventory и оставшаяся граница

Обнаружены два реально используемых read-only campaign API, отсутствовавших
в cutover inventory. Они добавлены, count исправлен с пяти на семь; существующий
contract test и README обновлены. Runtime permissions не расширялись: эти
два legacy GET требуют `legacy.admin.access`. Первоначальные ошибки scratch
preflight касались Windows path separators и CRLF/LF; до создания сессии
они остановили прогон. Затем проверены и exact deployed payload hashes, и
нормализованное совпадение содержимого с Git source.

Изменённый manifest ещё не развёрнут. O02 остаётся active: production redirect
старой webapp admin shell ещё не включён; зависимость O01 и final candidate
не закрыты. Публичные старые исходники и rollback bundles сохранены.


## Проверки

- Platform: `python -B -m pytest -p no:cacheprovider tests/test_admin_ops_api.py tests/test_admin_payments_api.py tests/test_operator_center_manifest.py -q` — 60 PASS.
- Adminapp: `npm.cmd ci --no-audit --no-fund` из прежнего lockfile;
  `npm.cmd run lint` — PASS; `npm.cmd run test:e2e` со штатным build — 80 PASS.
- `npm.cmd run verify:cutover` — 28 routes / 7 workspaces, семь JS chunks,
  1 631 325 JS bytes, route hash прежний, cutover hash `dbba2ba8…befe6ef`.

Первый lint не стартовал из-за отсутствовавшего node_modules; после установки
зависимостей проверка прошла. Логи и instrument hashes сохранены в receipt.

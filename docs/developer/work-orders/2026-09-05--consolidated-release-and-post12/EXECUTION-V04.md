# R12-V04 — связь обращения, попытки и версии

Дата: 2026-09-06. Статус: **I3 / NEEDS_RUNTIME_PROOF**.
Platform source: `2ba8e8eb06af7eccea0c51601506582ee8c0bfed`.
Client `4539753`, Core `94dd310` не менялись в этом этапе.
Команды, логи, SHA и визуальные проверки:
[evidence/v04-case-evidence.json](evidence/v04-case-evidence.json).

## Подтверждённые нарушения и исправление

1. Если `linked_attempt_ref` не находился в доступных событиях, карточка
   подставляла первую другую попытку пользователя в «Сводку выбранной попытки».
   Браузерный regression воспроизвёл это. Теперь для отсутствующей связанной
   попытки показано явное отсутствие данных. Другие попытки остаются в списке
   с действием ручной привязки. Если обращение вообще не имеет привязки,
   последняя попытка помечается как не связанная с обращением.
2. Known-issue resource key включал case и error code, но не app/build/platform.
   После обновления пакета с build 42 на 43 при прежнем `CORE-001` UI не
   запрашивал новый scope и сохранял совет для build 42. Теперь ключ содержит
   все параметры запроса: прежний результат сбрасывается и выполняется новый
   lookup. Regression подтверждает новый запрос и исчезновение старого совета.
3. Версия сводки попытки бралась из другого пакета диагностики. Теперь источник —
   последнее событие самой попытки. Тот же тест оставляет attempt build 42
   одновременно с обновлённым bundle build 43 и проверяет различие.

Production backend, сбор данных и модель прав не менялись. Источниками остаются
существующие allowlisted Event projections и opt-in support bundles.

## Проверенные границы существующего доступа

- Bundle ref разрешается только внутри заданных case и environment. Добавлены
  отрицательные проверки другого существующего обращения того же пользователя
  и другого environment.
- Grant привязан к upload/case и выдавшему оператору. Другой оператор, даже
  имеющий L2, и grant от другого case получают отказ до чтения файла.
- Запрошенные 3600 секунд ограничиваются 900. В точный `expires_at` доступ уже
  запрещён; отказ не потребляет grant и не создаёт успешный download audit.
- Существующие service/API tests проверяют L1 deny, step-up, одноразовость,
  actor/case audit, checksum ciphertext и retention hold.
- AI policy/safety и два harness-сценария подтверждают code-owned действия и
  метаданные: модель не получает authority выполнять operator commands.

Эти проверки выполнены на локальных SQLite/HTTP fixtures. Они не подтверждают
deployed OIDC/RBAC, расписание retention worker, custody ключей и live download.

## Результаты

| Проверка | Результат |
|---|---|
| Support service/work + AI policy/safety | 110 PASS |
| Admin ops/payments + operator observability API | 55 PASS |
| AI harness: model-owned metadata/actions | 2 PASS |
| Client-case browser suite после исправления | 10 PASS |
| Полный adminapp E2E, включая production build/SDK checks | 80 PASS |
| ESLint | PASS |
| Platform docs contracts | 33 PASS |

Первый UI before-run: missing-linked regression FAIL; второй сценарий сначала
остановился на неоднозначном locator кнопки «Обновить». После уточнения locator
повторный before-run подтвердил отсутствие запроса build 43. Failed logs
сохранены отдельно; ошибка locator не считается доказательством дефекта.

## Визуальная проверка

Browser plugin not available: использован существующий Playwright, без новых
зависимостей. URL: `http://127.0.0.1:3189/tickets?selected=501`, static export с
синтетическими API fixtures. Проверены desktop 1440×900 и mobile 390×844.
Название страницы и case соответствуют маршруту; экран непустой, framework
overlay отсутствует, page/console errors — 0, горизонтального overflow нет.
Проверены ручное обновление карточки, новый known-issue lookup и missing-link
состояние. Три PNG просмотрены и сохранены в `E:/r12-v04-ui-review/`.
Node предупреждает о typeless TS fixture module при импорте временным script;
в консоли приложения предупреждений нет. Временный сервер завершён.

## Остаток V04 и общего плана

V01/V02, полная expected/effective/proven привязка и решение O03 о допустимом
источнике per-device данных остаются открытыми. `diagnostic_profile` пакета
нельзя выдавать за effective runtime profile. Отсутствующий связанный attempt
и исторический known issue не подтверждают текущее подключение пользователя.
Live case journey, operator roles, signing/recipient custody и exact-candidate
support upload/download/expiry: **MANUAL_OWNER_TEST**.

Изменения закоммичены локально. Push, merge, deploy, внешняя коммуникация,
новые native bytes и release candidate не выполнялись. Для source rollback
сохранён предыдущий commit; история evidence и candidate.33 не менялась.

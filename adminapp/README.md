# POKROV AdminApp

Last updated: 2026-08-22

## Статус документа

Document class: CANONICAL. Этот файл — локальный источник правды для
`adminapp/`, основной операторской поверхности (primary operator surface)
`https://admin.pokrov.space/`.

## Назначение

`adminapp/` — русскоязычный операционный command center для повседневной
диагностики и безопасного управления POKROV. Первый экран отвечает на вопрос
«что требует действий сейчас», а не дублирует сырые API-ответы.

Текущая оболочка состоит из семи активных workspace-маршрутов и 21 прямого
capability-маршрута. Все 28 маршрутов имеют локально доказанное каноническое
назначение; `legacy-route-active` в manifest больше нет. Operator-work включает
`/incidents`, support-work v2 — `/users`, `/online` и `/tickets`, network-work v2 — `/nodes`, `/traffic`, `/alerts`,
`/provider-caps`, `/emergency-network`, money-work v2 `/free-tier`, `/payments`,
`/access`, `/promos`, growth-work v2 — `/funnel`, `/bonuses`, `/programs`,
`/referrals`, `/broadcast`, `/news`, release-work v2 — `/release`, governance —
`/governance`. Пять старых API-шаблонов остаются только read-only
compatibility-проекциями; новые возможности в них не добавляются. Каноническое
назначение и workspace-владелец каждой возможности зафиксированы в
`operator-center.manifest.json`, а counts/actions/redaction и закрытые внешние
гейты — в `operator-center.cutover.json`.

| Маршрут | Экран | Основная задача |
| --- | --- | --- |
| `/` | Главная | Очередь реакции, состояние источников, основные показатели |
| `/shift` | Моя смена | Мои, командные и неназначенные задачи плюс серверные очереди внимания |
| `/nodes` | Ноды | Master-detail по нодам, проверки из РФ, нагрузка, клиенты, транспорт и алерты |
| `/traffic` | Трафик | Динамика трафика по диапазону, пулу и ноде |
| `/alerts` | Алерты | Приоритизированная очередь подтверждения и приглушения сигналов |
| `/incidents` | Incident Room | Lifecycle, timeline, links, alerts, follow-up и компенсация инцидента |
| `/provider-caps` | Лимиты провайдеров | Ручные лимиты, окна сброса и текущий расход |
| `/emergency-network` | Экстренная сеть | Редактированный статус каталога, агрегаты проб, staging, promotion и rollback |
| `/free-tier` | Архив FREE | Только исторические поля и контроль полного отключения бывшего бесплатного пула |
| `/access` | Доступ | Entitlement grants, provisioning outbox, редактированные подарки и L3-выдача кодов |
| `/users` | Пользователи | Поиск и карточка с узнаваемым Telegram/устройством, доступ, ключи, риски и аудит |
| `/online` | Сейчас онлайн | Ограниченный live-снимок без сырых IP в общем списке |
| `/tickets` | Тикеты | Очередь поддержки и master-detail переписки |
| `/payments` | Платежи | Выручка, проблемные заказы и детализация без raw payload |
| `/funnel` | Воронка | Раздельные `Реклама` и `Продукт`: источник, шаг и отвал без сырых идентификаторов |
| `/promos` | Промо | Промокоды и удалённые рекламные кампании для клиента и кабинета |
| `/bonuses` | Бонусы | Version-bound wheel/loyalty configuration и ручные начисления |
| `/programs` | Программы | Очередь заявок, решение оператора и атомарный entitlement reward |
| `/referrals` | Рефералы | Очередь решений и история начислений |
| `/release` | Релиз | Точный состав кандидата, gate matrix, current/brain/RU evidence, adoption, health/support regression и управляемый rollout |
| `/broadcast` | Рассылка | Замороженный предпросмотр, подтверждённая отправка и агрегат delivery attempts; Telegram link preview отключён, чтобы внешний OG-кэш не подменял фирменный вид |
| `/news` | Новости | Ежедневно собранные RSS-кандидаты, состояние источников, ручная редакторская публикация и lineage до live update |

Навигация Operator Center v2 активна и состоит из семи рабочих областей:
`shift`, `support`, `network`, `money`, `growth`, `releases`, `governance`.
Перечисленные выше capability-маршруты остаются прямыми каноническими входами.
Redirect старых публичных shell-путей и их удаление запрещены до
authenticated exact-candidate proof. `webapp/admin` — только read-only источник
совместимости без новых функций; записи не дублируются между поверхностями.

Карточка пользователя может выпустить десятиминутный одноразовый код переноса
в приложение. Это действие уровня L3: оператор подтверждает точный Telegram ID,
код показывается только в первом ответе, а в intent/audit сохраняются лишь
безопасный статус и подсказка. Код создаёт отдельную отзывную сессию устройства
в существующем аккаунте и не переносит сырой subscription URL.

Вкладка `События приложения` в карточке пользователя объединяет безопасную
legacy-проекцию с User 360 v2. Сервер группирует до 100 allowlisted Event
Envelope V1 по opaque installation/session/attempt refs и строит ограниченные
diagnostic fingerprints из кода клиента, версии, subsystem/stage, результата и
error code. Произвольный `meta_json`, исходные session/device/install/trace
identifiers, IP, адреса сайтов, конфиги, ключи и токены в браузер не
возвращаются.

Пользовательские карточки, списки, сегменты рассылок и верхняя сводка используют
только эффективные продуктовые статусы `TRIAL`, `PAID` и `PENDING`. Подарки,
промокоды и ручное продление оператором относятся к `PAID`; старое значение
`FREE` остаётся только полем хранения и показывается отдельно в `Архив FREE`.
Продление реального пользователя после фиксации в Postgres синхронизирует его
доступ на всех включённых платных нодах; частичный результат остаётся видимым в
аудите и не считается успешной синхронизацией.

`/funnel` не смешивает рекламный трафик с известными пользователями. Вид
`Реклама` использует browser-session как единицу и только точную server-side
lineage после one-time handoff. Вид `Продукт` использует distinct known user и
дедуплицирует пересекающиеся app/bot/payment события. Во всех карточках
знаменатель явный; raw session hash, Telegram/account/order ids и event rows в
интерфейс не передаются.

`/promos` управляет allowlisted remote slots, а не произвольной рекламной
разметкой. Новый слот по умолчанию выключен. Оператор выбирает placement,
контент, аудиторию, приоритет, copy/цвета/CTA, dismiss policy и расписание;
mobile preview показывает ту же компактную композицию. Медиа загружается в
POKROV как PNG/JPEG/WebP/GIF/MP4/WebM до 24 MiB. Внешний media URL, пустой
включённый creative, `media_only` без файла, video без poster+fallback и
обратный интервал блокируют подтверждение. Публикация остаётся fingerprinted
action-intent; выключение/откат не требует новой версии клиента.
Поле `Сценарий блока` объясняет назначение разрешённого content id: активация
ключа, Telegram-бонус, восстановление через поддержку, обновление клиента,
сервисное сообщение или явно одобренная рекламная кампания. Это не визуальный
размер баннера: композиция, медиа и закрываемость настраиваются отдельно.

## Правила интерфейса

- Оболочка светлая и полноширинная: на desktop семь рабочих областей и их
  capability-маршруты доступны в левой навигационной рейке; на tablet реестр
  открывается в отдельном drawer, на mobile четыре основные области закреплены
  в нижней панели, остальные доступны через «Ещё».
- Верхняя панель показывает среду, frontend commit/source state, API schema,
  активный client release, срок idle-сессии и свежесть обязательных источников.
  Несовпадение frontend/API/schema отображается отдельным блокирующим баннером,
  а не маскируется общим зелёным состоянием.
- Глобальное обновление вызывает только явно зарегистрированные ресурсы
  текущего маршрута. Поиск не сохраняет строку или результаты как историю в
  Local Storage/Session Storage и принимает только безопасные canonical href.
- `/news` хранит только источник, заголовок, ссылку, время и безопасный итог
  запуска. Текст статьи не копируется. Публикация требует собственной русской
  выжимки и обычного L2 action-intent; автономной публикации нет.
- `/release` читает только `/api/admin/v2/releases/*`. Cockpit связывает один
  candidate id с точными component revisions и artifact/descriptor SHA-256,
  одиннадцатью диагностическими gates, раздельным current/brain/RU readiness,
  агрегированной adoption по версии, release-health regression, support delta и
  candidate-scoped known issues. Никаких account/install/device идентификаторов
  adoption в браузер не передаётся.
- Старт, изменение процента, pause, rollback, minimum supported version и
  закрытие observation window проходят через release action-intent. Старт
  запрещён без полного evidence gate, закрытие observation — без завершённого
  окна и PASS health gate. Rollback только фиксирует запрос и переключает
  реестр на удержанный кандидат; внешний artifact pointer он не меняет.
- `/api/client/apps` и `/api/public/client-apps` применяют тот же rollout registry.
  Pause, rollback request, повреждённый registry или несовпадение активного
  candidate с настроенной версией дают `rollout_percent=0`; интерфейс не должен
  называть это успешным откатом артефакта.
- `/broadcast` и `/news` читают `/api/admin/v2/growth/*`, а запись выполняют
  только через growth action-intent. Delivery summary агрегирует попытки по
  intent без recipient id и raw Telegram response; news draft сохраняет явный
  `source_draft_id` у опубликованного live update.
- Все маршруты используют один порядок чтения: контекст и обновление →
  компактная полоса ключевых показателей → рабочая область. Это сохраняет
  одинаковую скорость ориентации на нодах, в поддержке, деньгах и управлении.
- Рабочие экраны с выбором строки используют master-detail. На desktop карточка
  выбранного объекта остаётся видимой ниже липкой навигации; на mobile детали
  переходят в последовательный режим без общего горизонтального скролла.
- Таблицы имеют липкий заголовок и собственную горизонтальную прокрутку. Общая
  страница не расширяется из-за плотных операторских колонок.
- Главная использует triage-layout «лента инцидентов → доказательства →
  следующий шаг». Выбор сигнала локальный и не создаёт новый API-запрос;
  подробный ack/silence workflow остаётся в `/alerts`.
- Вся видимая оператору навигация, статусы, ошибки, подсказки и подтверждения
  написаны по-русски. Технический код допускается рядом как вторичный признак
  для поиска и расследования.
- Состояния `0`, «Нет данных», «Недоступно», «Устарело» и «Сбой» не
  взаимозаменяемы. UI не превращает отсутствие телеметрии в нулевой показатель.
- Списки и карточки используют master-detail: выбор сохраняется в URL, а
  возврат браузера восстанавливает предыдущий контекст.
- Поиск, фильтры, диапазон, выбранная строка и вкладка кодируются query-параметрами
  через `src/lib/url-state.ts`. Это делает экран воспроизводимым по ссылке.
- Фоновое обновление сохраняет уже показанные данные и помечает их как
  «Обновляем»; ошибка одного источника не стирает успешные данные другого.
- Подсказки доступны с клавиатуры и по фокусу. Модальные окна возвращают фокус,
  а `prefers-reduced-motion` отключает необязательную анимацию.
- На мобильном остаётся триаж и чтение. Плотные таблицы допускают горизонтальную
  прокрутку; опасные действия не маскируются под обычные ссылки.

Внутренний визуальный референс шести классов экранов и его provenance лежат в
`docs/design/generated/2026-07-23-ops-admin-screen-system/`. PNG не поставляется
в приложение: интерфейс реализован нативными компонентами и реальными
read-model/action-intent контрактами.

## Обновление данных

Интервалы относятся к перечитыванию серверного read-model, а не к запуску
новой проверки:

- `/online` — каждые 30 секунд;
- главная, ноды, последние RU-результаты, uploader, платежи, алерты, лимиты,
  трафик, экстренная сеть, воронка, промо, рефералы и релиз — каждые 60 секунд на активном экране;
- главная получает очередь durable-alerts внутри `/api/admin/ops/overview` и не
  дублирует её отдельным запросом к `/api/admin/alerts`;
- KPI, лента, evidence, ноды и нижний fleet-strip главной строятся из одного
  compact overview; графики и тяжёлые карточки загружаются только в профильных
  маршрутах;
- тяжёлая карточка пользователя, расследование, карточка тикета и история
  RU-проверок — при открытии, смене контекста или по кнопке «Обновить»;
- браузер останавливает polling в скрытой вкладке и перечитывает данные после
  возвращения.

Сама внешняя проверка из РФ выполняется раз в 6 часов. Сервер считает последний
пригодный запуск устаревшим после 7 часов, а heartbeat загрузчика — после
45 минут. Минутный polling UI только быстро показывает новый серверный вердикт
и никогда не выдаёт локальный таймер браузера за RU-доказательство.

## Безопасные действия

Опасные изменения проходят через серверный action-intent:

1. UI отправляет нормализованное действие и цель в workspace-boundary
   `POST /api/admin/v2/{workspace}/action-intents`; замороженные compatibility
   возможности временно используют `POST /api/admin/action-intents`.
2. Сервер возвращает снимок «до», ожидаемый эффект, риск, срок жизни и текст
   подтверждения.
3. Оператор проверяет предпросмотр и вводит точное подтверждение; браузер
   передаёт только требуемый SHA-256 и идентификаторы intent/idempotency.
4. Мигрированное исполнение отправляется в
   `POST /api/admin/v2/{workspace}/action-intents/{intent_id}/execute`;
   compatibility-действие — на исходный mutation route. Оба варианта передают
   `X-Admin-Intent-Id`, `X-Admin-Confirmation-SHA256` и
   `X-Admin-Idempotency-Key`.
5. UI показывает серверный снимок «после» и audit ID. При неопределённом
   исходе он читает `GET /api/admin/action-intents/{intent_id}`, а не повторяет
   мутацию вслепую.

Предпросмотр рассылки и dry-run не доказывают отправку. Неисполненный,
просроченный или изменившийся intent готовится заново.

Для экстренного каталога браузер может подготовить staging, продвинуть
проверенный snapshot, остановить новую выдачу или откатиться к удержанному
snapshot только через этот же action-intent contract. Подготовка выключена,
пока worker не сообщает `configuration_state=ready`; promotion недоступен при
менее чем четырёх здоровых точных пробах. Предпросмотр показывает только
безопасную дельту количеств и долю замены. После остановки worker не включает
выдачу снова автоматически; явный promotion или rollback снимает блокировку.
Уже сохранённый на устройстве подписанный каталог нельзя отозвать мгновенно —
его ограничивают срок действия snapshot и entitlement. Браузер не получает
исходные bundle, endpoint, host-hash, ciphertext, signature или
криптографические ключи.

## Runtime-контракт

Основной UI-хост: `https://admin.pokrov.space/`.

API-хост: `https://api.pokrov.space/`.

Все 73 метода `/api/admin/v2/*` входят в генерируемый контракт
`shared/contracts/admin/admin-v2.openapi.json`. Из него строится
`src/lib/admin-api/generated/admin-v2.ts` с точными method/path, query/path/body
типами, permission, CSRF и response kind. Клиент до отправки отклоняет v2-путь,
которого нет в таблице, а после HTTP 2xx не отдаёт feature-слою JSON без точного
`data/meta/sources/warnings` envelope. Два бинарных метода — CSV-аудит и
зашифрованное support-вложение — объявлены отдельно. Legacy `/api/admin/*` в
генерируемый v2-контракт не входит.

Проверка рассинхронизации выполняется командой `npm.cmd run check:sdk` и входит
в `prebuild`. Регенерация выполняется из корня платформы:

```powershell
python scripts/generate_admin_v2_openapi.py
node adminapp/scripts/generate-admin-v2-sdk.mjs
```

UI начинает с серверной проверки `GET /api/admin/v2/auth/me`. Если сессии нет,
основная кнопка запускает `GET /api/admin/v2/auth/oidc/start`, Telegram OIDC
Authorization Code + PKCE и завершает вход через
`POST /api/admin/v2/auth/oidc/finish`. Публичный `state` не содержит PKCE
verifier: verifier остаётся в отдельной короткой HttpOnly transaction cookie,
обе части подписываются выделенным operator session secret, а finish сверяет
purpose, CSRF nonce и redirect URI. Ручного поля для initData нет; bearer,
сырой initData и операторская сессия не записываются в Web Storage. Старые
ключи авторизации удаляются при входе. Сервер возвращает сессионный secret
только как `Secure; HttpOnly; SameSite=Strict; Path=/` cookie с префиксом
`__Host-`; JavaScript получает только CSRF-токен и держит его в памяти вкладки.

`POST /api/admin/v2/auth/bootstrap` остаётся отдельным compatibility-входом
только для живого Telegram Mini App и может быть закрыт через
`ADMIN_OPERATOR_LEGACY_BOOTSTRAP_ENABLED=false`. OIDC никогда не создаёт
оператора и не выдаёт `superadmin`: он открывает сессию только заранее
заведённой активной Telegram-linked identity с активной ролью в текущем
environment. Отсутствующий
выделенный session secret, отозванная роль, истёкшая/отозванная сессия,
неизвестное permission или неверный CSRF закрывают доступ. UI не хранит
provider secret, HMAC-ключ RU-пробы, panel password, subscription URL или
приватный ключ.

Каждая сборка создаёт `public/__build.json` и `public/__routes.json` из
`operator-center.manifest.json` и `operator-center.cutover.json`. Они связывают имя приложения, версию,
frontend commit, время сборки, состояние исходников, хэш маршрутного манифеста,
хэш cutover-матрицы, локальный parity snapshot, канонический домен и ожидаемую схему API. Guardrail обязан установить
зависимости `adminapp`, выполнить lint, production build и полный E2E.

Сессионный boundary v2:

- `GET /api/admin/v2/auth/oidc/start` и
  `POST /api/admin/v2/auth/oidc/finish` — основной purpose-bound OIDC-вход с
  PKCE и HttpOnly transaction cookie;
- `POST /api/admin/v2/auth/bootstrap` — compatibility exchange, без session
  token в JSON;
- `GET /api/admin/v2/auth/me` — operator, environment, roles, permissions,
  idle/absolute expiry и CSRF для текущей вкладки;
- `GET /api/admin/v2/auth/sessions` и
  `POST /api/admin/v2/auth/sessions/{id}/revoke` — ограниченный inventory и
  отзыв своих сессий;
- `POST /api/admin/v2/auth/step-up` — OIDC step-up той же identity; пустое тело
  оставляет временный legacy recheck только пока включён compatibility-флаг;
- `POST /api/admin/v2/auth/logout` — отзыв текущей сессии, удаление cookie и
  `Clear-Site-Data: "cookies", "storage"`.

RBAC и retained bridge:

- cookie-сессия допускается к retained маршрутам только по точному
  `method + route pattern`: user list/card требуют `support.read`, отдельное
  investigation — `support.sensitive.read`, promo slots — `money.read`, staged
  promo media — `money.write`; поиск принимает support/network/money read и
  возвращает только сущности разрешённых доменов. Любой другой legacy route
  по-прежнему требует `legacy.admin.access`;
- L1 не может искать пользователя по email/install/linked identity. В user
  list/card чувствительные идентификаторы, app events, платежи и operator audit
  имеют явный `field_access=redacted`; браузер показывает нехватку permission,
  а не ложное пустое состояние;
- профильные write-роли получают `command.high_risk` только вместе со своим
  доменным permission. Любая L3-команда всё равно требует оба права и свежий
  step-up; readonly, support и security-auditor роли high-risk command не
  получают.

Первый модульный read boundary v2:

- `GET /api/admin/v2/meta` — ограниченный envelope идентичности backend/API,
  релиза клиента и core; отсутствующие deployment-поля остаются `null` и дают
  явные warnings. Route требует `system.meta.read` через deny-by-default
  dependency.

Операторский work boundary v2:

- `GET /api/admin/v2/shift` — environment-scoped My Shift: мои, командные и
  неназначенные задачи, сбойные команды, тикеты, активные инциденты, платежи на
  проверке, блокеры релиза и сбои источников;
- `GET /api/admin/v2/tasks` — отдельная модель операторской задачи с владельцем,
  командой, статусом, приоритетом, сроком, следующим действием, источником,
  связанной сущностью и optimistic `version`;
- `GET /api/admin/v2/incidents` и `GET .../incidents/{id}` — единая карточка
  инцидента с lifecycle, timeline, links, alerts и follow-up задачами;
- prepare/execute выполняются через workspace-маршруты
  `/api/admin/v2/{shift|incidents}/action-intents`. Task/incident/alert переходы
  требуют текущую версию; компенсация дополнительно требует свежий step-up и
  вызывает существующий idempotent compensation service, а не второй grant path;
- `/alerts` использует action-intent для acknowledge, false-positive,
  link/create incident; часовой silence теперь проходит через network v2
  action-intent с текущей версией алерта.

Support work boundary v2:

- `GET /api/admin/v2/support/tickets` и `GET .../tickets/{id}` возвращают
  environment-scoped серверную очередь и карточку с priority, queue,
  assignment, waiting/escalation, SLA, incident/attempt links и optimistic
  `version`;
- `GET /api/admin/v2/support/users/{tg_id}` возвращает User 360 с opaque
  account/install/session/attempt refs, grouped attempts и diagnostic
  fingerprints; адаптер читает только allowlisted Event Envelope поля и не
  сериализует `meta_json`. Без `support.sensitive.read` route остаётся доступен
  для безопасной карточки и тикетов, но не читает Event rows, возвращает пустые
  diagnostic collections, `field_access=redacted` и warning;
- `GET /api/admin/v2/support/attempts` — ограниченный correlated attempt
  explorer; маршрут требует отдельное `support.sensitive.read`;
- `GET /api/admin/v2/support/macros` отдаёт серверный закрытый набор макросов;
- claim, assign и workflow update идут через
  `/api/admin/v2/support/action-intents`; reply/status и internal note временно
  исполняются совместимыми `/api/admin/tickets/*` маршрутами, но используют тот
  же stored Action Intent, idempotency и version recheck. Internal note никогда
  не входит в пользовательский ticket API;
- bundle summary сохраняет TTL/retention/access-audit границу, а observer и
  Event adapters остаются read-only источниками диагностики, не вторым
  ticket/account authority.

Network work boundary v2:

- `GET /api/admin/v2/network/fleet` и `GET .../nodes/{code}` собирают fleet и
  Node 360 из существующих inventory, brain/runtime, observer, RU-origin и
  alert authorities. Host, panel credentials, subnet и raw transport material
  не попадают в браузер;
- `GET .../traffic`, `GET .../alerts`, `GET .../providers` и
  `GET .../emergency` — read-only проекции без скрытого refresh, provider poll
  или notification side effect. Provider notes заменены на presence/length/SHA-256;
- `GET .../ru/latest`, `GET .../ru/runs`, `GET .../ru/uploader` сохраняют
  отдельную RU-origin authority и freshness. Некорректный manifest даёт
  `503 ru_configuration_invalid`; fleet/Node 360 остаются доступными и явно
  помечают RU source как failed;
- node/provider/emergency mutations и `alert.silence` готовятся и исполняются
  только через `/api/admin/v2/network/action-intents`. L3 network actions
  дополнительно требуют `command.high_risk` и свежий step-up.

Money и growth boundary v2:

- `GET /api/admin/v2/money/payments/{summary|orders}` и
  `GET .../orders/{provider}/{order_id}` разделяют order status, подписанные
  callback events, entitlement claim/grant и delivery outbox. Client telemetry
  не подтверждает оплату и не меняет доступ;
- `GET .../access` читает только grant/outbox/catalog authority и никогда не
  возвращает полный сохранённый gift/access code. Полный новый код виден один
  раз только в успешном результате L3 intent и остаётся в памяти диалога;
- `GET .../free-archive` — read-only legacy FREE projection;
  `GET .../promos` — ограниченный список промокодов. Reconcile, promo и выдача
  кодов используют `/api/admin/v2/money/action-intents`; `promo_slots.update`
  также готовится в money workspace, а retained `PUT /api/admin/promo-slots`
  не расширяет RBAC bridge;
- `GET /api/admin/v2/growth/bonuses` возвращает только allowlisted wheel и
  loyalty configuration; update preview содержит fingerprint, а не сырой JSON;
- `GET /api/admin/v2/growth/programs` возвращает ограниченную очередь заявок.
  `program_application.review` — L3, recheck версии и один атомарный
  idempotent entitlement grant без второго reward path.

Release boundary v2:

- `GET /api/admin/v2/releases/candidates`, `GET .../cockpit` и
  `GET .../adoption` связывают точный состав кандидата с current/brain/RU
  evidence, диагностическими gate, rollout policy, adoption, health/support
  regression и known issues;
- start/change/pause/rollback/minimum-version/observation-close выполняются
  только через `/api/admin/v2/releases/action-intents`. Rollback меняет
  серверную rollout policy, но явно возвращает
  `external_artifact_switch=NOT_PERFORMED` и не выдаётся за внешний deploy.

Governance boundary v2:

- `GET /api/admin/v2/governance/roles`, `GET .../operators` и
  `GET .../operators/{id}` показывают серверный каталог ролей, эффективные
  permissions, standing/JIT/break-glass назначения и сессии без cookie,
  session secret или token hash. Истёкшая роль перестаёт действовать на
  следующем запросе;
- grant/revoke роли, suspend/activate оператора, отзыв сессии и review временного
  доступа идут только через `/api/admin/v2/governance/action-intents`, требуют
  step-up и серверный confirmation challenge. Самоэскалация, временный
  superadmin, повторная выдача до review и снятие последнего активного
  superadmin запрещены;
- `GET .../audit` и bounded CSV export фильтруют по actor/role/permission/action/
  result/resource/command/time; command lineage связывает Action Intent,
  совместимый `AdminAudit` и operator audit. Экспорт и чтение журнала доступа к
  support bundles сами создают operator audit без сырых payload и токенов;
  legacy bundle authority не имеет environment-поля и маркируется как global,
  а не притворяется environment-scoped;
- `GET .../privacy` показывает фактические retention windows, backlog/hold
  counters и allowlisted field inventory. Это runtime read model, а не
  доказательство работы retention в production.

Все unsafe cookie-authenticated запросы требуют корректный CSRF и доверенный
Origin. Роли и сессии постоянны и привязаны к environment; сервер перечитывает
активные роли на каждом запросе. Аудит bootstrap/revoke/step-up сохраняет
snapshot roles/permissions, environment и безопасный correlation ID. Замороженные
legacy `/api/admin/*` временно принимают v2-cookie только при
`legacy.admin.access` и с тем же CSRF для unsafe methods; новый frontend больше
не вызывает `/api/admin/auth/session`.

Ключевые read boundary для нового контура:

- `GET /api/admin/v2/shift/overview`;
- `GET /api/admin/v2/support/online`;
- `GET /api/admin/v2/network/fleet` и `GET .../nodes/{code}`;
- `GET /api/admin/v2/network/{traffic|alerts|providers|emergency}`;
- `GET /api/admin/v2/network/ru/{latest|runs|uploader}`;
- `GET /api/admin/v2/money/payments/{summary|orders}` и
  `GET .../orders/{provider}/{order_id}`;
- `GET /api/admin/v2/money/{access|free-archive|promos}`;
- `GET /api/admin/v2/growth/{funnel|referrals|bonuses|programs}`;
- `GET /api/admin/v2/releases/{candidates|adoption}`;
- `GET /api/admin/v2/governance/{roles|operators|audit|sensitive-access|privacy}`.

В разделе промо отдельная read-only панель пилота возврата использует
`GET /api/admin/campaigns` и
`GET /api/admin/campaigns/{campaign_id}/pilot-decision`. Она показывает
policy/stop-причины, зрелую `net_revenue_30d_per_capacity_unit`, holdout,
квоту, payment errors, incident/P0–P1 guardrails, winner state и связанные
Action Intent. CTR и первые оплаты не выбирают победителя; запуск и масштаб
никогда не выполняются из readback. Локальная панель не является legal,
production или outcome evidence.

Сырые и недоверенные payload не возвращаются в браузер. Общие online-списки
не содержат raw IP; IP-контекст загружается только внутри карточки конкретного
пользователя.

Архитектурная граница описана в `docs/architecture/system-overview.md`,
семантика мониторинга — в `docs/operations/monitoring-and-visibility.md`,
операторский запуск RU-контура — в
`docs/operations/ru-origin-probe-handoff.md`.

## Локальная работа

```powershell
Push-Location adminapp
npm.cmd install
npm.cmd run dev -- --port 3105
Pop-Location
```

Для непродового API задайте `NEXT_PUBLIC_API_BASE_URL`. Не направляйте локальную
сборку на production для проверки мутаций.

## Проверка кандидата

Финальная проверка выполняется один раз после завершения пакета правок:

```powershell
Push-Location adminapp
npm.cmd run check:sdk
npm.cmd run build:contract
npm.cmd run build
npm.cmd run lint
npm.cmd run test:e2e
Pop-Location
```

Статический export появляется в `adminapp/out`. Успешные локальные build, lint
и E2E подтверждают только локальный кандидат: они не доказывают production
deploy, доступность `brain` или прохождение проверки из РФ.

## Публикация

`scripts/remote_deploy_brain_static_sites.py` валидирует build/route/cutover identity,
отклоняет несовпадение хэшей и старую публичную оболочку
`POKROV API superadmin v1`, публикует `adminapp/out` вместе с другими
статическими поверхностями и перед переключением сохраняет предыдущий symlink
как `adminapp.rollback`. Явный `--rollback-adminapp` требует четыре точных
SHA-256 текущего и rollback bundle плюс подтверждение `ROLLBACK_ADMINAPP`,
проверяет оба target внутри versioned releases и атомарно меняет указатели.
Наличие команды не доказывает, что rollback drill выполнялся. Публикация, production-мутации и установка таймеров на
`mini` выполняются только по отдельному операторскому разрешению и не входят в
обычную UI-проверку.

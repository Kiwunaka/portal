# POKROV AdminApp: операционный command center и RU-наблюдаемость

- Дата: 2026-07-15
- Статус: дизайн утверждён владельцем; письменная спецификация ожидает финального просмотра владельца
- Поверхность: `adminapp/`, административные API в `portal_bot/`, RU-probe в `scripts/`
- Канонические владельцы поведения: `adminapp/README.md`, `docs/architecture/system-overview.md`, `docs/operations/monitoring-and-visibility.md`

## 1. Контекст и цель

Текущая выделенная админка функциональна, но плохо работает как ежедневный операторский инструмент: 15 разделов идут одним плоским списком, стартовая страница смешивает обзор и глубокую аналитику, а монолитный `adminapp/src/components/ops-dashboard.tsx` загружает почти все административные источники независимо от открытого раздела. Нодовые данные уже богаты, но значительная часть сигналов скрыта или показана без ясного источника и возраста.

Отдельный пробел — RU-origin. Каноническая проверка из `mini` должна выполняться каждые шесть часов, однако сейчас результат остаётся файловым JSON/текстовым отчётом: нет долговременного хранения, API, истории по ноде и состояния свежести в интерфейсе.

Цель этой работы — превратить `admin.pokrov.space` в русскоязычный операционный command center, где:

1. за первые 10 секунд видны требующие реакции события;
2. до полной картины по конкретной ноде не больше двух действий;
3. каждый статус показывает источник, время и смысл;
4. Brain-origin, current-origin и RU-origin не смешиваются;
5. отсутствие телеметрии не выглядит как нулевое значение или успешная проверка;
6. опасные действия остаются защищёнными и аудируемыми.

## 2. Зафиксированные решения

| Область | Решение |
|---|---|
| Визуальное направление | Тёмный, плотный «Операционный центр» на почти чёрном фоне; минимум декоративности, максимум читаемой иерархии |
| Объём | Перестроить все 15 существующих разделов, сохранив их текущие маршруты |
| Главная | Сначала очередь действий; ниже только компактное здоровье, ключевые показатели и активность |
| Ноды | Master–detail: список слева, полная карточка выбранной ноды справа |
| RU-origin | Проверка остаётся раз в 6 часов; в UI показываются последний запуск, свежесть, стадии и история по каждой ноде |
| Источник RU-данных | Собственный ingest: `mini` → локальный spool → HMAC API → PostgreSQL → admin API |
| Реализация | Вертикальные срезы в текущем Next.js/FastAPI/SQLAlchemy-стеке, без внешней панели мониторинга |
| Язык | Весь видимый интерфейс на русском; технические коды — только вторичным моноширинным текстом |
| Помощь | У метрик, статусов, сокращений и опасных действий есть доступные с клавиатуры подсказки |
| Безопасность | Уровни действий L0–L3, предварительный просмотр, подтверждение и dry-run там, где риск этого требует |

## 3. Границы работы

### Входит

- новая информационная архитектура и оболочка `adminapp`;
- UX всех 15 существующих маршрутов;
- action-first главная и палитра команд по `Ctrl+K`;
- master–detail для нод и пользователей, очереди для операционных сущностей, аналитические полотна для графиков, защищённые формы для изменений;
- декомпозиция монолитного `ops-dashboard.tsx` на доменные модули;
- загрузка данных только для активного маршрута и ленивое открытие деталей;
- долговременное хранение RU-origin запусков и результатов по целям/нодам;
- защищённый внутренний ingest и административные read API;
- минимальный redacted exact-candidate/evidence registry для честного раздела «Релиз»;
- обязательный server action-intent guard для существующих L2/L3 административных команд;
- русские подписи, статусы, ошибки, пустые состояния и подсказки;
- тесты, каноническая документация и правила хранения RU-телеметрии.

### Не входит

- смена админской модели авторизации или добавление ролей сверх текущего `superadmin v1`;
- замена Next.js static export, React, Tailwind, TanStack Table или Recharts;
- подключение Grafana, Netdata, VictoriaMetrics либо API хостеров;
- изменение самих транспортных профилей, инфраструктуры нод или алгоритма smart-connect;
- хранение release binaries, подписание артефактов, публикация в stores или перенос active client release truth из `POKROV-app`;
- автоматическое исправление инцидентов по одному красному статусу;
- удаление старых admin-маршрутов в `webapp` до отдельного подтверждения паритета;
- деплой и production-мутации в рамках реализации интерфейса.

Работа остаётся одним продуктовым контуром: RU-ingest — недостающий источник для карточки ноды, а не отдельная система. Реализация разбивается на независимо проверяемые вертикальные срезы.

## 4. Визуальный и языковой контракт

### 4.1 Визуальная система

- Почти чёрный фон, приподнятые нейтральные поверхности и тонкие границы; один спокойный акцент для фокуса и выбранного состояния.
- Красный, янтарный и зелёный используются только как семантические сигналы. Цвет никогда не является единственным носителем статуса: рядом всегда есть иконка и текст.
- Плотность выше пользовательского кабинета: компактные строки, таблицы и группы полей, но интерактивная зона не меньше 40 px на desktop и 44 px на touch-устройствах.
- Главные числа выровнены табличными цифрами; идентификаторы и технические коды выводятся моноширинно вторым уровнем.
- График появляется только там, где показывает динамику или сравнение. Декоративные диаграммы и большие пустые hero-блоки не используются.
- Анимация ограничена сменой состояния, открытием панели и фокусом; `prefers-reduced-motion` убирает перемещения.

### 4.2 Русский интерфейс

Все пользовательские подписи, команды, статусы, ошибки, подтверждения и подсказки — на русском. Допустимы общеупотребимые технические обозначения только рядом с русским смыслом: «Задержка (RTT)», «Автономная система (ASN)». `BLOCKED_BY_ACCESS`, `run_id`, `dns_ok` и другие машинные значения показываются вторично и не заменяют объяснение.

В навигации `Free tier` становится «Бесплатный контур», `Ops admin` — «Операционный центр», а подтверждение массовой рассылки требует русскую фразу `ОТПРАВИТЬ`.

### 4.3 Подсказки

Подсказка обязана отвечать максимум на пять вопросов: что это, откуда данные, когда обновились, какой порог применён и что делать при отклонении. Она открывается мышью и клавиатурой, связана с триггером через ARIA, закрывается по `Escape` и возвращает фокус. Один `title` не считается реализацией подсказки.

## 5. Информационная архитектура и оболочка

Постоянная левая навигация группирует те же 15 маршрутов:

| Группа | Разделы |
|---|---|
| Команда | Главная |
| Сеть | Ноды, Трафик, Алерты, Лимиты провайдеров, Бесплатный контур |
| Клиенты | Пользователи, Сейчас онлайн, Тикеты |
| Деньги и рост | Платежи, Воронка, Промо, Рефералы |
| Управление | Релиз, Рассылка |

Верхняя строка содержит название раздела, возраст данных, кнопку обновления, палитру команд и компактное состояние API/сессии. `Ctrl+K` открывает палитру: сначала переходы по разделам и частые действия, затем результаты поиска по Telegram ID, username, display name, install ID, order ID, node code и ключу/email. Выбор результата ведёт сразу в соответствующую detail-панель; строка и выбранная сущность сохраняются в URL.

На экранах меньше 1024 px навигация становится выдвижной, а master–detail работает последовательными экранами «список → детали». Mobile предназначен для триажа и безопасных быстрых действий; широкие таблицы получают приоритетные колонки и контролируемый горизонтальный скролл.

## 6. Общие паттерны разделов

### 6.1 Очередь действий

Используется на Главной, в Алертах, Тикетах и Рефералах. Строка содержит приоритет, короткую причину, затронутую сущность, источник, возраст, одну основную команду и ссылку в контекст. Сортировка детерминирована: критичность → число затронутых сущностей → возраст. Если один источник недоступен, остальные строки остаются рабочими.

### 6.2 Master–detail

Используется для Нод и Пользователей. Список, фильтры и выбранный ID отражаются в query-параметрах. Детали загружаются только после выбора. Возврат браузера восстанавливает фильтр, прокрутку и выбранную сущность.

### 6.3 Аналитическое полотно

Используется для Трафика и Воронки: компактная сводка, диапазон времени, ключевой график, разрезы и таблица исходных агрегатов. График и таблица используют одинаковые фильтры. Пропуск данных разрывает линию и помечается как «Нет данных», а не превращается в ноль.

### 6.4 Защищённая форма

Используется для Рассылки и рискованных изменений. Шаги: ввод → проверка → предварительный просмотр/dry-run → явное подтверждение → результат с audit ID. Черновик не теряется после ошибки API или повторного входа.

## 7. Главная: action-first обзор

Первый экран — «Требует реакции». Очередь собирает уже существующие сигналы: критические/устаревшие ноды, зависшие платежи, приближение лимитов провайдеров и бесплатного контура, активные алерты и свежие тикеты. Каждая строка объясняет причину без общего «что-то не так».

Ниже располагаются только:

- четыре–шесть компактных KPI с источником и возрастом;
- контур сети с количеством нормальных, проблемных, устаревших и неизвестных нод;
- отдельные строки свежести Brain-origin и RU-origin;
- короткая лента последних операторских событий.

Глубокие графики платежей, трафика и воронки остаются в своих разделах. Главная не дублирует их.

## 8. Контракт всех 15 разделов

Таблица задаёт плановую границу каждого route module. Указанные API уже существуют, кроме явно помеченных `новый`; реализация не заменяет их общей «универсальной» ручкой.

| Раздел | Read API и URL-state | Представление | Write API / риск | Проверяемый результат |
|---|---|---|---|---|
| Главная | `/api/admin/ops/overview`, `/api/admin/alerts`, новый RU latest; `focus`, `severity` | Очередь действий + компактные KPI | Только переходы L0 | Частичная ошибка не скрывает другие источники; стабильная сортировка |
| Ноды | `/api/admin/nodes/health`, `/runtime`, новый `/{code}/observability`, RU latest/runs; `q`, `state`, `freshness`, `selected`, `tab`, `range` | Master–detail и RU history | lifecycle/resync L2–L3 через action intent | Детали ≤2 действий; Brain/current/RU и missing/zero раздельны |
| Трафик | `/api/admin/traffic/summary`, `/api/admin/nodes/timeseries`; `range`, `node`, `metric` | Аналитическое полотно | Нет | Одинаковые фильтры графика/таблицы; пропуски разрывают линию |
| Алерты | `/api/admin/alerts`; `status`, `severity`, `source`, `entity` | Очередь и detail причины | `/ack`, `/silence` L1 | Видны источник, возраст, длительность и переход к сущности |
| Лимиты провайдеров | `/api/admin/provider-quotas`, `/status`; `q`, `state` | Таблица квот + edit drawer | POST/PATCH L2, DELETE L3 | Review показывает before/after и прогноз исчерпания |
| Бесплатный контур | `/api/admin/free-tier/summary`, `/users`; `range`, `state`, `q` | Burn-rate, лимиты, users | Только переход в пользователя L0 | Платный и бесплатный пулы не смешиваются |
| Пользователи | `/api/admin/users`, `/users/{tg_id}`; `q`, `status`, `sort`, `selected`, `tab` | Master–detail | Существующие user/key actions L2–L3 | Первый слой — доступ/онлайн; raw IP только в detail |
| Сейчас онлайн | `/api/admin/online/users`; `node`, `source`, `q` | Ограниченный live-список | Только переход в пользователя L0 | Ни одного raw IP; aggregate age и source видны |
| Тикеты | `/api/admin/tickets`; `status`, `priority`, `selected` | Очередь + thread detail | reply/status L2 | После ответа сохраняются выбранный тикет и позиция списка |
| Платежи | `/api/admin/payments/summary`, `/orders`; `period`, `status`, `q`, `selected` | KPI + orders master–detail | Только уже существующие диагностические действия; новые платежи не создаются | Today/7d/30d, stuck и provider state не смешиваются |
| Воронка | `/api/admin/funnel/summary`; `range`, `source`, `stage` | Аналитическое полотно | Нет | Стадии/источники читаемы без raw JSON |
| Промо | `/api/admin/promos`; `state`, `q`, `selected` | Таблица + edit drawer | create/update L2, delete/deactivate L3 | Срок, область и before/after подтверждаются сервером |
| Рефералы | `/api/admin/referrals/pending`; `status`, `q`, `selected` | Очередь решений + история | Существующий decision flow L2 | UI не создаёт новый платёжный механизм и показывает основание |
| Релиз | новые `/api/admin/releases/candidates` и `/{candidate_id}/readiness`; `candidate`, `origin`, `status` | Exact-candidate checklist | Импорт evidence выполняет release tooling, не браузер | Каждый verdict связан с candidate ID, origin, временем и evidence ref |
| Рассылка | `/api/admin/broadcast` preview/execute; `segment` и несекретный draft локально | Защищённая форма | L3 action intent, frozen recipients, `ОТПРАВИТЬ` | Выполняется ровно одобренный snapshot; повтор не рассылает заново |

## 9. Ноды: master–detail

### 9.1 Список

Левая колонка показывает код/страну, lifecycle-состояние, сводный статус, Brain-origin, RU-origin, загрузку CPU и порта, provisioned clients, online hint и возраст самой старой обязательной телеметрии. Фильтры: состояние, свежесть, страна, hoster family, transport profile и наличие активного алерта. Поиск работает по коду, хостеру, ASN и подсети.

Сводный статус — производное представление, а не новый источник. Он показывает худший обязательный сигнал и перечисляет причины; оператор всегда может увидеть исходные строки.

### 9.2 Карточка ноды

Правая колонка состоит из независимых блоков:

1. **Заголовок:** код, страна, lifecycle, вес, hoster family, ASN, subnet, активные пулы.
2. **Источники:** «Текущее состояние» как сводка, отдельные Brain-origin, current-origin при наличии явного запуска и RU-origin. У каждой строки — вердикт, время, возраст и стадия сбоя.
3. **Ресурсы:** CPU, RAM и диск с used/total; отсутствие total делает значение «Нет данных», а не `0%`.
4. **Сеть:** текущие RX/TX, 1m, 5m, 24h peak, суммарный Mbps и процент от политики порта (по умолчанию 1 Gbit/s, если нет индивидуального `max_tx_mbps`).
5. **Нагрузка:** `provisioned_clients_count` и `online_connections_hint` как разные показатели с разными подсказками.
6. **Панель и dataplane:** `panel_state`, latency/error rate, `dataplane_state`, RTT, packet loss и TCP retransmit.
7. **Observer:** время последнего batch, unmatched и parse errors; свежесть не скрывается зелёным состоянием панели.
8. **IP и транспорты:** IPv4/IPv6 health, активный transport profile, transport health, probe classification, last probe stage/error.
9. **RU-история:** последние запуски с итогом и разворачиваемыми стадиями DNS/TCP/TLS/HTTP/UDP по этой ноде; быстрые диапазоны 24 часа, 7, 30 и 180 дней.
10. **Действия:** resync, drain, enable, undrain и disable по уровням риска.

Сырые технические поля доступны в свернутом «Технические детали», но основной слой всегда даёт русское объяснение.

## 10. Семантика статусов и свежести

Общий визуальный словарь:

| Русский статус | Техническое значение | Смысл |
|---|---|---|
| Норма | `ok` | Проверка завершилась, обязательные данные свежие и проходят правила |
| Требует внимания | `degraded` | Есть частичный сбой или приближение к порогу, но источник дал полезные данные |
| Сбой | `failed` | Проверка реально выполнилась и вернула явный отказ |
| Устарело | `stale` | Последнее пригодное измерение старше окна свежести |
| Недоступно | `unavailable` | Проверяющий источник или путь не позволил получить вердикт |
| Нет данных | `missing` | Пригодного измерения нет |
| Доступ заблокирован | `BLOCKED_BY_ACCESS` | Есть явное доказательство отсутствия требуемого доступа |

### 10.1 Серверный target manifest

Перед запуском `mini` получает текущий manifest через подписанный `GET /api/internal/probes/ru-origin/manifest` и кэширует его для одного offline-запуска. Backend детерминированно строит manifest из текущей конфигурации. `manifest_revision` считается по preimage `{manifest_schema_version, targets}`; поля envelope `manifest_revision`, `generated_at` и `max_cache_age_seconds` в hash не входят.

Canonicalization для revision и endpoint fingerprint едина в runner/API: UTF-8 JSON с `ensure_ascii=false`, отсортированными object keys и separators `(',', ':')`; targets сортируются по `target_id`, а set-like arrays `address_families`/`required_stages` нормализуются в allowlist-order до сериализации. Поэтому повторный GET с новым `generated_at` сохраняет revision, пока schema/targets не изменились.

Исполнимый manifest имеет `manifest_schema_version`, `manifest_revision`, `generated_at`, `max_cache_age_seconds` и массив targets. Каждая target содержит:

- `target_id`, `target_kind`, `scope`, nullable `node_code`;
- `endpoint`: public `host`, `port`, nullable `sni`, `address_families`, `transport_profile`, `probe_mode`, nullable `http_path`, nullable `min_body_bytes`, nullable `local_probe_profile_id` — только имя локального secret-backed профиля на `mini`, без material;
- server-owned `required_stages` из `dns|tcp|tls|http_large_body|transport_handshake`;
- `endpoint_fingerprint = SHA-256(canonical JSON ровно объекта endpoint)` по той же canonicalization; hash-поле не находится внутри endpoint и самоссылки нет.

`probe_mode` имеет allowlist `google_https|canonical_https_large_body|delivery_tls|xhttp_handshake|hysteria_handshake`. Runner исполняет его без догадок: HTTP path/body threshold, SNI, family и transport приходят из manifest; secret material разрешается локально только по `local_probe_profile_id`.

В обязательный набор входят:

- Google environment target;
- канонические POKROV-hosts из RU policy;
- delivery node, если она включена, draining либо всё ещё имеет provisioned/mapped clients; намеренно disabled-нода без клиентов получает `not_in_scope`, а не PASS/FAIL;
- явно настроенные reserve ingress targets.

У каждой цели есть стабильный `target_id`, `target_kind`, `node_code`, `endpoint_fingerprint` и серверный список `required_stages`. Fingerprint включает только публичные endpoint-поля из схемы выше; идентичность цели и required stages защищает общий `manifest_revision`. Клиент не может расширить или ослабить обязательные стадии своим payload.

При ingest backend заново строит текущий manifest. Совпадение `manifest_revision`, полного набора обязательных `target_id` и endpoint fingerprints — необходимое условие текущего PASS. Запуск по предыдущему manifest сохраняется в истории как `superseded_manifest`, но не обновляет текущий зелёный статус. Так смена адреса, добавление ноды и поздняя доставка не превращают старую проверку в PASS.

### 10.2 Алгоритм RU-вердикта

Backend игнорирует присланные aggregate `ok`, `google_reachable`, `classifications`, `xhttp_alive` и `hysteria_alive` при вычислении статуса; они допустимы только как diagnostic input. Единственный authority — валидированные стадии и серверный manifest.

1. Payload обязан иметь `execution_status=completed`, текущий manifest, ровно один результат для каждой обязательной цели и ни одного дублированного `target_id`. Пропуск обязательной цели даёт `incomplete`; дубликат/неизвестная форма — `422`.
2. Google target должен пройти все server-required стадии. Иначе environment verdict = `unavailable`, все node verdict этого запуска = `unavailable_probe_host`, release verdict не может быть PASS.
3. При здоровой environment конкретная нода получает `pass`, только если fingerprint совпал и все её required stages имеют `pass`. Любой `fail` обязательной стадии даёт `failed`; `not_run` даёт `incomplete`. `not_applicable` допустим только для стадии, которой нет в server-required списке.
4. Canonical и reserve verdict считаются отдельно от node verdict. Общий RU release verdict = PASS только при полном текущем manifest и PASS всех release-required canonical, node и reserve targets.
5. Extra target с `scope=diagnostic` хранится, но не участвует ни в node current status, ни в release verdict. Неизвестная активная нода никогда не получает PASS из extra target.
6. XHTTP/Hysteria получают `alive=true` только после protocol-aware handshake с probe-only material. Обычный TLS к порту не доказывает XHTTP, а UDP `send()` без валидного ответа не доказывает Hysteria. При отсутствии безопасного probe material результат `not_run`, не PASS.
7. Для HTTP обязательна фактическая загрузка и подсчёт не менее 65 536 bytes; `HEAD` не проходит эту стадию. Для delivery node TCP success не маскирует TLS/REALITY failure.

Плановый интервал — 6 часов. Текущий пригодный результат становится «Устарело» через 7 часов после `finished_at`. Порядок определяется `finished_at`, не `received_at`: поздний пакет хранится в истории, но не вытесняет более новый запуск. `started_at ≤ finished_at`, длительность не больше 60 минут, future skew не больше 5 минут; запуск старше retention принимается в quarantine, а не восстанавливает удалённую историю.

При новом недоступном запуске последний успешный результат показывается только как историческая справка с исходным возрастом. `BLOCKED_BY_ACCESS` появляется лишь при подписанном `execution_status=blocked_by_access` с allowlisted `evidence_code` и очищенным detail; таймаут, backlog и отсутствие запуска выводятся как unavailable/stale/missing.

Окна свежести Brain metrics/observer берутся из существующей политики ноды. UI не подменяет backend-порог собственным. У каждого поля есть собственный `sampled_at`; возраст страницы не считается возрастом всех данных.

## 11. RU-origin: поток данных

```text
systemd timer на mini (каждые 6 часов)
  → signed GET server target manifest (или cached revision)
  → scripts/ru_probe_runner.py v2
  → атомарный JSON в локальный pending spool
  → uploader с повторными попытками
  → POST /api/internal/probes/ru-origin/runs (HTTPS + HMAC)
  → ru_probe_service.py
  → ru_probe_runs + ru_probe_target_results
  → admin read API
  → Главная / Ноды / Релиз / Алерты

отдельный 15-минутный uploader heartbeat
  → ru_probe_uploader_heartbeats → uploader status / alerts
```

### 11.1 Исполнение на `mini`

- Timer на самом `mini` запускает probe раз в 6 часов и не зависит от браузера, brain cron либо локального WSL.
- Runner v2 сначала получает текущий server manifest; при временной сетевой ошибке разрешён последний кэшированный manifest, но такой запуск станет current только при совпадении revision на ingest.
- Wrapper назначает UUID `run_id`, фиксирует границы запуска, runner version, manifest revision и SHA-256 точных bytes артефакта.
- Текущий runner обязательно переделывается: `HEAD` заменяется на GET с чтением ≥64 KiB; TCP и TLS больше не объединяются через OR; UDP send-without-response становится `not_run/viability_hint`, а XHTTP/Hysteria требуют protocol-aware handshake.
- Файл пишется как `.tmp`, flush/fsync выполняется до атомарного rename в pending. Частичный JSON не отправляется.
- Секреты HMAC и probe-only transport material хранятся вне репозитория/JSON/journald, читаются только service user и не попадают в UI.

### 11.2 Spool и dead-letter

На `mini` используются каталоги `/var/lib/pokrov-ru-probe/{pending,blocked,quarantine,archive}`: каталоги `0700`, файлы `0600`, владелец — отдельный service user. Pending/blocked не удаляются автоматически.

| Результат upload | Действие |
|---|---|
| `201` или идемпотентный `200` | Атомарно перенести в archive; если move/fsync не удался, оставить pending и поднять локальную ошибку — повтор безопасен |
| network, `408`, `425`, `429`, `5xx` | Оставить pending; exponential backoff с jitter от 1 минуты до 1 часа |
| `401`/`403` key disabled/misconfigured | Перенести в blocked с reason sidecar; повторять после reload ключа и не чаще раза в час |
| `409 payload_conflict`, `400`, `413`, `422`, unsupported schema | Перенести в quarantine с status, correlation ID и очищенной причиной; автоматического повтора нет |
| `409 replayed_nonce` | Сформировать новый timestamp/nonce и повторить один раз; повторный конфликт — quarantine |

Каждая upload-попытка создаёт новый request timestamp/nonce и подписывает неизменные raw bytes файла. Следующий probe не ждёт завершения backlog.

Отдельный timer каждые 15 минут отправляет новый signed DTO в `POST /api/internal/probes/ru-origin/heartbeat`: `schema_version`, `probe_host_id`, `observed_at`, service version, counts pending/blocked/quarantine, `oldest_pending_at`, `archive_write_ok`, disk free/state и allowlisted `last_error_code`. Heartbeat не является частью run artifact и имеет собственный raw-body hash/nonce.

Backend создаёт `ru_probe_uploader_heartbeat_stale` после 45 минут без heartbeat, backlog/disk/archive alerts по принятому DTO и `ru_probe_run_stale` после 7 часов без пригодного run. Если сеть или сам HMAC key не позволяют доставить heartbeat, backend не угадывает локальную причину: UI показывает «Нет свежей связи с загрузчиком», а точный blocked/journald reason остаётся локальным evidence до восстановления канала. Локальный service выходит non-zero при write/archive/disk failure.

`RU_PROBE_ARCHIVE_RETENTION_DAYS=365`, `RU_PROBE_QUARANTINE_RETENTION_DAYS=30`; оба значения настраиваются. Перед удалением archive job исключает артефакты, явно promoted в release/audit evidence. Pending/blocked сохраняются до успешной доставки или ручного документированного решения.

### 11.3 Versioned payload v2

Контракт фиксируется отдельным `scripts/ru_probe_payload.schema.json` с `additionalProperties: false` на envelope/stage objects и contract-тестом runner → API. Обязательная форма:

```json
{
  "schema_version": 2,
  "run_id": "uuid",
  "origin": "ru",
  "probe_host": {"id": "mini", "label": "mini", "public_ip": null},
  "runner_version": "2.x",
  "manifest_revision": "sha256",
  "started_at": "RFC3339 UTC",
  "finished_at": "RFC3339 UTC",
  "execution_status": "completed|partial|runner_error|blocked_by_access",
  "evidence_code": null,
  "targets": [
    {
      "target_id": "node:nl",
      "target_kind": "delivery_node",
      "scope": "release_required",
      "node_code": "nl",
      "endpoint": {
        "host": "public-host-or-address",
        "port": 443,
        "sni": "expected-public-sni",
        "address_families": ["ipv4", "ipv6"],
        "transport_profile": "legacy_reality_fallback",
        "probe_mode": "delivery_tls",
        "http_path": null,
        "min_body_bytes": null,
        "local_probe_profile_id": null
      },
      "endpoint_fingerprint": "sha256",
      "stages": {
        "dns": {"status": "pass|fail|not_run|not_applicable", "latency_ms": 12, "code": null},
        "tcp": {"status": "pass", "latency_ms": 34, "code": null},
        "tls": {"status": "pass", "latency_ms": 51, "code": null},
        "http_large_body": {"status": "not_applicable", "latency_ms": null, "code": null},
        "transport_handshake": {"status": "not_applicable", "latency_ms": null, "code": null}
      },
      "address_family_status": {"ipv4": "pass", "ipv6": "not_run"},
      "transport": {
        "profile_code": "legacy_reality_fallback",
        "handshake_status": "pass",
        "classification": "ok",
        "detail_code": null
      },
      "detail_code": null,
      "detail": null
    }
  ]
}
```

Ограничения schema: максимум 256 targets; уникальность `target_id` дополнительно проверяет service; endpoint object обязан дословно соответствовать manifest target, а его canonical hash — `endpoint_fingerprint`; detail ≤500 символов; label/code имеют allowlist charset и предел длины; host/IP/SNI валидируются; timestamps только timezone-aware UTC. `blocked_by_access` требует allowlisted `evidence_code`, не содержит target PASS и не может создать release PASS.

Run artifact содержит только результаты probe и после rename не меняется. Wrapper вычисляет `artifact_sha256` по точным UTF-8 bytes готового файла и пишет hash/run ID в отдельный immutable sidecar; uploader перед отправкой пересчитывает hash, API независимо вычисляет тот же hash из raw request body. Сам hash не вставляется внутрь JSON, поэтому самоссылки нет. Этот server-computed `artifact_sha256` одновременно является idempotency payload hash.

### 11.4 Что проверяется

Каждый полный запуск содержит:

- доступность `google.com` как проверку самой RU-среды;
- канонические POKROV-hosts, delivery nodes текущих подписок и явно заданные reserve ingress targets;
- отдельные стадии DNS, TCP/443, TLS, large-body HTTPS ≥64 KB и protocol-aware transport handshake, где он применим;
- необязательные длительности стадий в миллисекундах;
- per-target reported classification, IPv4/IPv6 status и transport handshake/health;
- XHTTP/Hysteria handshake status, из которого сервер сам выводит `xhttp_alive`/`hysteria_alive`;
- короткую очищенную причину без credential, subscription URL, токенов и сырого provider payload.

## 12. Хранение данных

### 12.1 `ru_probe_runs`

Одна строка на запуск:

- `id`, уникальный `run_id`, `schema_version`, `origin`;
- `probe_host_label`, опциональный restricted `probe_public_ip`;
- `started_at`, `finished_at`, `received_at`;
- `manifest_revision`, `execution_status`, server-computed `environment_verdict`, `release_verdict`, `current_eligible` и `ineligible_reason`;
- server-computed `google_reachable`, `xhttp_alive`, `hysteria_alive`;
- очищенные server reason/summary;
- server-computed `artifact_sha256` по raw immutable JSON и `ingest_key_id`;
- `retention_hold`, nullable `retention_hold_reason`, `retention_held_at` для release/audit evidence;
- индексы по `finished_at`, `release_verdict`, `current_eligible`, `probe_host_label`.

### 12.2 `ru_probe_target_results`

Одна строка на цель/ноду в запуске:

- `run_db_id` — явный FK на `ru_probe_runs.id` с каскадным удалением;
- `target_id`, `target_kind`, `scope`, nullable `node_code`, endpoint fingerprint;
- validated endpoint snapshot: host/port/SNI, requested address families, transport profile, probe mode и public HTTP параметры;
- `observed_at`, всегда равный validated `run.finished_at`;
- server-computed `overall_status`, `current_eligible` и reason;
- отдельные enum-status и nullable latency для DNS/TCP/TLS/HTTP-large-body/transport-handshake;
- IPv4/IPv6 status, reported transport handshake/classification, server reason code и очищенный detail;
- `UNIQUE(run_db_id, target_id)`;
- индексы `(node_code, observed_at DESC)`, `(run_db_id, node_code)` и `target_kind`.

### 12.3 `ru_probe_uploader_heartbeats`

Append-only heartbeat rows: `probe_host_id`, `observed_at`, `received_at`, service version, pending/blocked/quarantine counts, oldest pending, archive-write flag, disk free/state, allowlisted last error code и ingest key ID. `UNIQUE(probe_host_id, observed_at)`; индекс `(probe_host_id, observed_at DESC)`. Retention — 30 дней, latest вычисляется до pruning.

### 12.4 `internal_ingest_nonces`

Durable replay window для RU и release imports: `key_scope`, `key_id`, `nonce_hash`, `request_timestamp`, `expires_at`, `created_at`; `UNIQUE(key_scope, key_id, nonce_hash)`. Nonce живёт 24 часа, что больше допустимого timestamp skew, и удаляется отдельной безопасной cleanup-веткой. Запись nonce и соответствующих domain rows выполняется одной транзакцией.

### 12.5 Exact-candidate release evidence

Раздел «Релиз» использует минимальные durable records, а не вывод из последней даты:

- `release_candidates`: immutable `candidate_id`, lane/component, version/channel, git/deploy revision, artifact-set SHA-256, redacted metadata SHA-256, imported_at;
- `release_origin_evidence`: FK candidate, `origin=current|brain|ru`, check name, честный status (`PASS`, `MANUAL_OWNER_TEST`, `OPERATOR_ATTESTED`, `SKIPPED_BY_OWNER`, `SKIPPED_BY_OPERATOR`, `BLOCKED_BY_ACCESS`, `FAIL`, `MISSING`), observed_at, source kind/ref, nullable `ru_probe_run_id` с `ON DELETE RESTRICT`, summary;
- candidate ID = SHA-256 canonical redacted descriptor с version, lane, revision и отсортированными artifact hashes; изменение одного входа создаёт другого кандидата;
- `UNIQUE(candidate_id, origin, check_name, source_ref)`; evidence другого candidate не переиспользуется автоматически.

Канонический `release-handoff.json` остаётся owner metadata. Release tooling импортирует только redacted descriptor/evidence; локальные пути, подписи, credentials и сырые artifacts в БД не копируются. RU run становится release evidence только после явной привязки точного `run_id` к точному `candidate_id`; «ближайший по времени» запуск не привязывается.

В той же транзакции import выставляет связанному run `retention_hold=true`, reason `release_evidence:<candidate_id>`; retention исключает held runs и их target rows. Hold снимается только отдельной документированной archive/delete процедурой после удаления/переноса всех ссылок, не автоматически по возрасту. Поэтому 180-дневная очистка не ломает exact-candidate evidence.

### 12.6 `admin_action_intents`

Серверная защита L2/L3 хранит UUID intent, actor, action, target type/id, risk level, canonical payload/hash, immutable preview snapshot/hash, confirmation challenge, entity-version hash, status (`prepared|executing|completed|failed|uncertain|expired`), expiry, consumed_at, result summary и nullable `admin_audit_id`. Уникальный client idempotency key не позволяет повторно выполнить уже consumed intent.

Intent хранит frozen recipient IDs и только hash сообщения; полный message body повторно приходит на execute и обязан совпасть с hash. Обычный `admin_audit.meta` получает лишь hashes, counts и redacted summary. Для completed/failed/uncertain `admin_audit_id` использует `ON DELETE RESTRICT`; future audit cleanup обязана удалить пару в одной документированной транзакции, а не оставить битую ссылку. Истёкшие prepared intents без audit очищаются через 7 дней, выполненные/неопределённые остаются вместе с audit retention.

Новые таблицы создаются через текущие SQLAlchemy models + идемпотентный migration/bootstrap для SQLite-тестов и PostgreSQL. `RU_PROBE_RETENTION_DAYS` по умолчанию равен 180. Retention job удаляет только unheld старые runs и связанные target rows; он не касается release evidence, held runs, внешнего audit/archive и платёжного ledger.

## 13. API-контракты

### 13.1 Внутренний ingest

`POST /api/internal/probes/ru-origin/runs`

`GET /api/internal/probes/ru-origin/manifest` использует тот же service-key scope и возвращает текущий server manifest без секретов.

`POST /api/internal/probes/ru-origin/heartbeat` принимает отдельный schema-v1 uploader-health DTO из §11.2; он не меняет и не дополняет сохранённый run artifact.

Обязательные заголовки:

- `X-Internal-Key-Id`;
- `X-Internal-Timestamp` — Unix seconds, допустимое отклонение максимум 300 секунд;
- `X-Internal-Nonce` — случайное значение на попытку;
- `X-Internal-Signature` — lowercase hex `HMAC-SHA256(secret, METHOD + "\n" + normalized_path + "\n" + timestamp + "\n" + nonce + "\n" + raw_body)` по точным bytes HTTP body до JSON parse.

Контракт безопасности и идемпотентности:

- production принимает запрос только по HTTPS; proxy передаёт canonical path без rewrite ambiguity;
- key ID выбирает активный secret и allowlisted `origin=ru` + `probe_host.id=mini`; отдельный key scope не подходит для release imports;
- uploader создаёт timestamp/nonce заново на каждую попытку, поэтому старый spool не конфликтует с пяти минутным request skew;
- сервер читает максимум 512 KiB raw bytes, проверяет timestamp, HMAC constant-time и payload host binding, затем парсит/валидирует schema v2;
- nonce hash вставляется в durable replay table; повтор `(key_id, nonce)` получает `409 replayed_nonce`, даже если body тот же;
- первый artifact для `run_id` возвращает `201`; новый nonce + тот же `run_id`/server-computed `artifact_sha256` возвращает идемпотентный `200`; тот же `run_id` с другими raw bytes — `409 payload_conflict`;
- timestamp/nonce и run/targets фиксируются одной транзакцией. Unique-гонка по `run_id` обрабатывается повторным чтением победившей строки, а не `500`; одинаковый hash даёт `200`, другой — `409`;
- duplicate targets, timestamp order/future skew, unsupported schema и bounds дают `422` до commit; валидный partial/missing-target run сохраняется как `incomplete` с `current_eligible=false`, но никогда как PASS;
- response всегда содержит stable `code`, `run_db_id`, `run_id`, `created`, `current_eligible`, `correlation_id`; секрет/подпись не эхоятся.

### 13.2 Административное чтение

| Endpoint | Назначение |
|---|---|
| `GET /api/admin/probes/ru-origin/latest` | Последний запуск, свежесть, environment verdict, reserve и текущий RU-статус всех известных нод |
| `GET /api/admin/probes/ru-origin/runs` | Cursor pagination; фильтры `node_code`, `from`, `to`, `verdict`, `limit`; краткие строки без тяжёлого payload |
| `GET /api/admin/probes/ru-origin/uploader-status` | Последний heartbeat, его возраст, backlog/blocked/quarantine, archive/disk state и server-derived heartbeat freshness |
| `GET /api/admin/nodes/{code}/observability` | Агрегат метаданных, Brain/current/RU evidence, runtime, observer, transport, alerts и нужные timestamps одной ноды |
| `GET /api/admin/search?q=...` | Типизированные результаты глобального поиска с безопасным subtitle и canonical admin href |

Все GET требуют существующую admin-auth. API возвращает стабильные технические enum/reason code, source timestamp и threshold metadata; русский текст определяет frontend mapping в одном месте. Сырые backend messages не выводятся пользователю напрямую. Неизвестная нода в RU payload сохраняется как diagnostic target без привязки к активной `nodes` записи и не влияет на сводный статус.

`latest` строится по максимальному eligible `finished_at`, отдельно возвращает самый новый received run, даже если он incomplete/unavailable. Поэтому UI может честно показать «последняя попытка не дала вердикта» и возраст последнего пригодного результата. `runs` использует opaque cursor `(finished_at,id)` и deterministic descending order. Uploader status не подменяет run freshness; stale heartbeat не объясняется как auth/network/disk без принятого evidence.

### 13.3 Release candidate API

- `POST /api/internal/releases/candidates` — idempotent import redacted candidate descriptor + evidence от release tooling. Отдельный scoped service key использует тот же exact-byte HMAC/timestamp/durable-nonce verifier, versioned schema и hash-conflict `409`.
- `GET /api/admin/releases/candidates?limit=&cursor=` — список exact candidates с component/version/revision/hash и возрастом.
- `GET /api/admin/releases/{candidate_id}/readiness` — раздельные current/brain/RU checks и исходные honest statuses.

Backend проверяет candidate ID повторным вычислением canonical hash. RU evidence ref обязан указывать существующий `ru_probe_run_id`; run с `current_eligible=false`, environment unavailable или без полного target set не может импортироваться как PASS. Aggregate readiness не превращает `SKIPPED_*`, `ATTESTED`, `BLOCKED_BY_ACCESS` или `MISSING` в PASS и всегда сохраняет точный candidate ID. Браузер не создаёт и не редактирует release evidence.

### 13.4 Серверный action-intent flow

`POST /api/admin/action-intents` принимает allowlisted `action`, `target` и payload будущей L2/L3-команды. Сервер сам перечитывает сущность, выполняет dry-run/preview и на 10 минут сохраняет immutable intent. Ответ: `intent_id`, `risk_level`, redacted preview, `payload_hash`, `snapshot_hash`, `entity_version_hash`, русскоязычный `confirmation_challenge`, `expires_at`.

Исходный доменный endpoint выполняет действие только при наличии `intent_id`, client idempotency key и введённого confirmation. Под транзакционной блокировкой сервер проверяет:

1. actor/action/target совпадают;
2. canonical payload hash совпадает;
3. intent не истёк и не consumed;
4. confirmation совпадает с server challenge;
5. entity-version hash не изменился после preview.

Нет intent — `428 intent_required`; mismatch/stale preview — `409`, после которого нужен новый preview. Это правило находится в API, поэтому прямой вызов не обходит UI-защиту.

Для DB-only мутации изменение, consume intent и новая `AdminAudit` row коммитятся одной транзакцией; audit helper принимает текущую session, возвращает ID и для L2/L3 fail-closed. Для внешнего эффекта intent сначала атомарно становится `executing` и получает audit ID, затем выполняется один раз; повтор idempotency key возвращает сохранённый результат. Crash/неясный outcome получает `uncertain` и не повторяется автоматически.

Broadcast preview замораживает точный список recipient IDs, segment inputs и message hash. Execute получает тот же message, сверяет hash и отправляет только frozen snapshot; изменение аудитории или текста требует нового intent. Audit хранит count/hashes/result, не полный текст и не список IDs.

## 14. Архитектура приложения и загрузка данных

### 14.1 Backend units

| Unit | Единственная ответственность | Вход/выход | Зависимости |
|---|---|---|---|
| `ru_probe_runner.py` v2 | Выполнить стадии строго по manifest и записать schema-v2 artifact | Manifest → immutable JSON | Network probes, probe-only material |
| `ru_probe_uploader.py` | Spool state machine, signed delivery и отдельный health heartbeat | Pending file → HTTP result/archive/quarantine; local state → heartbeat | HMAC config, filesystem |
| `internal_request_auth.py` | Проверить key scope, timestamp, nonce и exact-byte HMAC | Request bytes/headers → authenticated service identity | Config, nonce repository |
| `ru_probe_service.py` | Валидировать payload, сравнить manifest, вычислить server verdicts и читать latest/history | Validated DTO ↔ RU repositories | Node inventory, RU tables |
| `release_evidence_service.py` | Canonical candidate hash, import и exact-candidate readiness | Redacted import/read DTO | Release/RU repositories |
| `admin_action_intent_service.py` | Preview snapshot, confirmation binding, consume/idempotency/audit state | Action DTO ↔ intent/audit repositories | Existing domain action handlers |

API handlers остаются тонкими: auth/DTO/status code; бизнес-правила тестируются в services без HTTP. RU service не вызывает runner, uploader не вычисляет verdict, frontend не вычисляет release PASS.

### 14.2 Frontend units

Монолитный `ops-dashboard.tsx` заменяется тонким router/shell-компоновщиком и доменными модулями. Предлагаемая граница:

```text
adminapp/src/
  components/ops/       shell, navigation, command palette, shared states
  components/ui/        status badge, source row, tooltip, dialog, table primitives
  features/overview/    action queue and compact overview
  features/nodes/       node list, detail, RU history, lifecycle actions
  features/users/       user list and detail
  features/network/     traffic, alerts, provider limits, free contour
  features/revenue/     payments, funnel, promos, referrals
  features/support/     tickets and online users
  features/control/     release and broadcast
  lib/admin-api/        typed endpoint clients and response mappers
  lib/ops-status/       freshness and Russian presentation mapping
```

Границы модулей:

- route module знает только свои endpoints и состояния;
- shared primitives не импортируют доменные features;
- status mapper получает структурированный source result и возвращает русское представление, но не придумывает backend-факты;
- write-команды живут рядом со своей доменной сущностью и проходят общий confirm/audit flow;
- новый data-fetching framework не добавляется: достаточно текущего fetch-клиента, AbortController и небольших route hooks.

### 14.3 Загрузка

- открытие маршрута запрашивает только его summary;
- detail и история загружаются лениво;
- переключение/поиск отменяет устаревший запрос;
- последняя успешная копия может оставаться на экране с пометкой «Обновляем», но её возраст не сбрасывается;
- Главная и Ноды обновляются раз в 60 секунд, «Сейчас онлайн» — раз в 30 секунд, только при видимой вкладке; остальные разделы — при входе и вручную;
- RU latest входит в refresh Нод/Главной, но его шестичасовая свежесть определяется `finished_at`, а не частотой UI polling;
- URL хранит `q`, filters, sort, range, selected entity и активную detail-tab.

## 15. Ошибки, пустые состояния и частичная доступность

- Ошибка одного блока не заменяет всю страницу общим экраном; рабочие источники продолжают показываться.
- У каждого упавшего read-блока есть «Повторить». GET можно повторять автоматически с ограничением; write-команды автоматически не повторяются.
- `401` открывает повторный вход, сохраняет URL и несекретный черновик, затем позволяет продолжить. `403` честно сообщает об отсутствии права.
- «Пока нет записей» отличается от «Источник недоступен» и «Данные устарели».
- Если метрика отсутствует, UI показывает `—` и «Нет данных», никогда `0`.
- Ответ write API содержит итог, объект, время и audit/action ID. Неясный сетевой исход предлагает сначала проверить состояние сущности, а не повторять действие вслепую.
- Системные ошибки логируются с correlation ID; UI показывает краткий русский текст и этот ID без stack trace и секретов.

## 16. Уровни риска действий

| Уровень | Примеры | Защита |
|---|---|---|
| L0 — чтение | фильтр, переход, раскрытие detail, экспорт разрешённого агрегата | Без подтверждения |
| L1 — обратимое локальное | acknowledge alert, silence с конечным сроком | Ясная кнопка, итог/undo где поддерживается |
| L2 — изменение состояния | drain/undrain/enable/resync, изменение лимита или промо | Server action intent, review before/after, русское подтверждение, entity-version recheck |
| L3 — опасное/массовое | disable ноды, удаление правила, реальная рассылка | Server dry-run/frozen preview, ввод кода ноды или `ОТПРАВИТЬ`, consumed intent и audit ID |

Raw IP виден только внутри карточки конкретного пользователя при расследовании. Общие online-списки его не получают. Нельзя выводить panel credentials, HMAC secret, subscription tokens/URL, private keys, callback body или сырой provider payload.

Frontend confirmation — лишь представление серверного action-intent flow из §13.4. Все существующие L2/L3 handlers мигрируют на обязательный intent; оставить параллельный unguarded endpoint нельзя. L1 остаётся идемпотентным/обратимым и пишет обычный audit.

## 17. Вертикальные срезы реализации

1. **Основание:** новая оболочка, сгруппированная навигация, русские primitives/подсказки, URL-state, route-only fetch и action-first Главная на существующих API.
2. **Сеть и RU:** manifest/schema, runner v2, immutable spool/uploader + heartbeat, models/migrations, ingest/read API, server verdicts, node master–detail, RU history, freshness alerts и action intents для lifecycle-команд.
3. **Клиенты:** Пользователи, Сейчас онлайн и Тикеты на общих master–detail/queue primitives.
4. **Деньги и рост:** Платежи, Воронка, Бесплатный контур, Лимиты, Промо и Рефералы.
5. **Управление:** exact-candidate release import/read model и Рассылка с frozen action intent; миграция остальных L2/L3 handlers на тот же server guard, затем полный parity/accessibility regression.

Каждый срез должен быть сборочным и не ломать ещё не перенесённые маршруты. Старый рендер конкретного раздела удаляется только после паритета этого раздела.

## 18. Проверка и критерии готовности

### Backend

- models/bootstrap/migrations работают на SQLite fixtures и PostgreSQL-пути;
- JSON Schema contract проверяет manifest endpoint/SNI/family/transport/probe-mode и реальный runner-v2 artifact против API DTO; v1/unknown schema не принимается молча;
- runner действительно читает ≥64 KiB, TLS failure не маскируется TCP success, UDP send-without-response не создаёт `hysteria_alive`;
- manifest: disabled/no-clients exclusion, draining/mapped inclusion, missing/duplicate target, смена endpoint fingerprint, extra diagnostic, cached old revision и partial execution;
- серверные verdicts: google-down не создаёт node-failure, stage failure создаёт его, reserve protocols и aggregate release PASS следуют только required stages;
- late/out-of-order delivery выбирается по `finished_at`; старый manifest/адрес не обновляет current PASS;
- HMAC: exact raw bytes, method/path binding, host/key scope, unknown/disabled key, signature, per-attempt timestamp, skew, size и malformed payload;
- durable nonce replay, delayed spool, конкурентные same-run same-hash/different-hash запросы завершаются `200/409`, не duplicate/`500`;
- immutable artifact/sidecar hash не меняется между retries; heartbeat является отдельным DTO и не меняет run;
- spool state-machine покрывает 2xx, retryable, auth-blocked, permanent quarantine, archive-move failure, backlog и archive retention exclusions;
- heartbeat ingest/read/45-minute stale, backlog/disk/archive alerts и честное unknown при недоставленном heartbeat;
- DB constraints: target FK/unique/index, heartbeat unique/index, nonce unique/expiry, unheld retention cascade и redaction;
- release candidate hash не переиспользует evidence другого candidate; RU evidence требует eligible exact run, ставит retention hold и защищено `ON DELETE RESTRICT`;
- action-intent → audit FK/cleanup не оставляет dangling reference;
- action intent: unknown action, missing intent, actor/target/payload mismatch, expiry, entity-version conflict, confirmation, concurrent consume, idempotent result и fail-closed audit;
- stale после 7 часов, missing без запусков, `BLOCKED_BY_ACCESS` только с evidence;
- фильтры/cursor pagination и неизвестная node diagnostic;
- admin-auth на всех read endpoints и отсутствие ingest secret в ответах/логах.

### Frontend

- direct load и навигация по всем 15 маршрутам;
- `Ctrl+K`, URL-state, back/forward, lazy detail и отмена устаревших запросов;
- action queue сортируется стабильно и ведёт к нужному контексту;
- node detail открывается максимум за два действия;
- Brain/current/RU отображаются отдельно; source и age видны без открытия технических деталей;
- RU stage history корректно показывает `true`/`false`/не применимо, stale, missing и probe-host problem;
- old manifest, incomplete latest attempt и last-known-good видны раздельно и не дают ложный зелёный статус;
- uploader-status различает свежий backlog/quarantine/archive failure и stale heartbeat; при stale не угадывает локальную причину;
- Релиз всегда показывает candidate ID/hash и отдельные origin evidence; skip/attestation/block не стилизуются как PASS;
- все основные тексты русские; английский остаётся только техническим вторичным кодом;
- подсказки доступны мышью/клавиатурой, focus-visible, Escape/focus return, screen-reader labels;
- desktop 1280/1440 и mobile triage; reduced motion и контраст;
- частичная ошибка, истёкшая сессия и отсутствующая телеметрия не теряют рабочие данные/черновик;
- L2/L3 проходят server intent; `428`, expired/stale preview и uncertain outcome имеют отдельные русские состояния; случайный повтор не выполняет команду заново;
- общие списки не содержат raw IP или секретов.

### Команды

```powershell
cd adminapp
npm.cmd run build
npm.cmd run lint
npm.cmd run test:e2e

cd ..
python -B -m pytest -p no:cacheprovider tests/test_admin_ops_api.py tests/test_admin_payments_api.py -q
git diff --check
```

План добавит отдельные focused-тесты RU ingest/service/migrations и frontend status mapping. Старый `webapp` admin E2E запускается только если затронуты retained parity routes.

### Definition of Done

- оператор видит требующие реакции события за 10 секунд;
- полная карточка ноды доступна не более чем за два действия;
- для каждой обязательной метрики и проверки понятны источник и возраст;
- RU-origin запускается независимо от UI каждые 6 часов, а после 7 часов без свежего результата UI показывает «Устарело»;
- current PASS требует полный текущий server manifest; старый адрес, неполный запуск и поздняя доставка не дают PASS;
- spool не теряет retryable/auth-blocked артефакты; свежий heartbeat показывает quarantine/backlog/archive failure, а недоставленный heartbeat честно становится «Нет свежей связи» без выдуманной причины;
- Brain-origin, current-origin и RU-origin нигде не объединены в ложный PASS;
- release verdict всегда связан с immutable candidate ID и отдельным evidence каждого origin;
- RU run, привязанный к release evidence, удерживается от 180-дневной очистки до явного снятия hold;
- отсутствие данных нигде не выглядит как `0` или «Норма»;
- все 15 разделов используют согласованные паттерны и русские подсказки;
- любой L2/L3 API-вызов без валидного server intent отклоняется, а выполненное действие имеет audit ID;
- build, lint, E2E и backend regressions зелёные для точного candidate;
- production deploy и реальная RU-origin готовность не заявляются без отдельного актуального evidence.

## 19. Документация в том же изменении поведения

При реализации обновляются:

- `adminapp/README.md` — новая архитектура, маршруты, UX и API;
- `docs/architecture/system-overview.md` — RU ingest/storage и границы компонентов;
- `docs/operations/monitoring-and-visibility.md` — durable RU status, 7-часовая свежесть, retention и операторская интерпретация;
- `docs/operations/ru-origin-probe-handoff.md` — timer/spool/uploader и проверка доставки результата без раскрытия секрета;
- `docs/operations/publishing-and-signing-guide.md` и `docs/operations/deployment-and-access.md` — redacted exact-candidate/evidence import без переноса active client truth в platform repo;
- `scripts/ru_probe_payload.schema.json` — исполняемый versioned contract runner/API.

## 20. Журнал решений

- Владелец выбрал направление A: тёмный «Операционный command center».
- Главная утверждена как action-first, без глубокой аналитики.
- Для нод утверждён master–detail.
- RU cadence оставлен 6 часов; статус и история выводятся по каждой ноде.
- Выбран собственный durable RU ingest/API вместо файлового-only отчёта или внешней панели.
- Утверждена поэтапная реализация вертикальными срезами в текущем стеке.
- Все пять секций дизайна утверждены 2026-07-15.
- Последнее явное требование владельца: весь интерфейс на русском и с подсказками; оно имеет приоритет над ранними англоязычными рабочими ярлыками.

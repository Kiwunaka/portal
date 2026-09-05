# POKROV — сохранённые 83 слайса с уточнённой применимостью

**Редакция:** consolidated-v2 / 2026-09-05.<br>
**Источник:** предыдущий `execution_backlog.json`, 83 ID без удаления и перенумерации.<br>
**Статус строк по умолчанию:** `TO_RECONCILE`, а не «83 незакрытых бага» и не разрешение выполнять всё сразу.

## Правила применения

Это единственный список `R12-*` внутри итогового пакета. Прежний JSON используется как история требований, а не как конкурирующая инструкция. Приоритет и тип работ ниже сохранены из предыдущего аудита; фактическую реализацию, зрелость I0–I5 и применимость исполнитель фиксирует по текущему коду.

`P0` в условном AWG/Linux/marketing lane не делает эту функцию автоматически обязательной для 1.2.0. Обязательные требования уже утверждённого release scope нельзя убрать из denominator после неудачного теста. Уточнения в [01](01_SCOPE_AND_CORRECTIONS.md) и [02](02_RELEASE_1_2_0.md) имеют приоритет перед историческими предложениями публичного AWG и всей Linux beta.

Зависимости задают порядок **внутри выбранного scope**. Если dependency состоит из local и live частей, локальную реализацию можно тестировать по её контракту, но не засчитывать незапущенную live часть как PASS. Пропуск условной ветки фиксируется `DEFERRED_SCOPE` с причиной, не ломает остальные независимые цели и не меняет исторический статус.

Разрешённое переиспользование: `ALREADY_IMPLEMENTED`, `VERIFIED_CURRENT`, `SUPERSEDED` — только с конкретной ссылкой и анализом значимых входов. Не делать пустой PR, чтобы «закрыть ID». Нельзя произвольно менять legacy tests под план, если правильное текущее поведение уже лучше.

**Первый пакет:** G01/G03, затем N01/N02/N03/N04 и независимо B01/B02/B03/B04/B05. G02/G04 идут своевременно, но отсутствие удалённого signer artifact само по себе не запрещает локально исправить checkout.

## Группы

| Группа | Количество | Результат |
|---|---:|---|
| G | 7 | Релизные основания |
| N | 8 | Подключение и корректность маршрута |
| A | 9 | AWG и связанные лабораторные контуры |
| W | 6 | Windows |
| D | 6 | Android |
| C | 5 | Core, архитектура и производительность |
| B | 8 | Backend и платежи |
| O | 7 | Operator Center |
| F | 7 | Frontend и продуктовый путь |
| M | 6 | Коммерция, ёмкость и маркетинг |
| V | 4 | Диагностика и приватность |
| L | 5 | Linux |
| Q | 5 | Финальная приёмка и выпуск |

## Как закрывать строку

Один WO содержит выбранный ID, текущую классификацию, фактические files/write set, regression/oracle, выполненные команды с exit codes, итог, неисполненные проверки и rollback. Точные команды берутся из реального task router, не придумываются по имени этого файла. Общий формат — [09](09_EXECUTION_AND_ACCEPTANCE.md).

## G. Релизные основания

### R12-G01 — Зафиксировать новый scope и authority

**Приоритет:** P0. **Тип:** Решение (классификация исходного аудита). **Роль:** `release-owner`.

**Применимость:** Текущая 1.2.0 после разрешения на соответствующую работу.

**Зависимости:** нет.

**Definition of Done:** Сохранены 378 прежних ID; у каждого нового slice указан характер fix/verify/optimization, обязательность и owner; старый freeze не переименован в GO.

**Особое условие:** Один конечный rebaseline; не требовать повторного полного аудита всех 378 требований до первого исправления.

**Трассировка:** REL_GATE; REL_DOD; [AUD-S01], [AUD-S05].

### R12-G02 — Сохранить candidate.33 и доказательства

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `release-engineer`.

**Применимость:** Текущая 1.2.0 после разрешения на соответствующую работу.

**Зависимости:** `R12-G01`.

**Definition of Done:** Сохранены все доступные immutable artifacts точного кандидата, manifest, receipt, SBOM и provenance с readback SHA. Проверены фактические сроки retention; исторический срок signer artifact 18.09.2026 08:01:25 UTC не принимается за срок всех файлов. Недоступный или истёкший artifact записан как отсутствующий; другой файл не выдаётся за прежние байты. Приватные signing keys не копируются в отчёт.

**Редакционное уточнение:** эта формулировка заменяет соответствующий DoD предыдущего аудита; основание — границы и исправления в файле 01. Остальные обязательства ID сохранены в выбранном scope.

**Трассировка:** E13-006; E13-007; [AUD-S01], [AUD-S02].

### R12-G03 — Dependency-aware evidence invalidation

**Приоритет:** P0. **Тип:** Интеграция (классификация исходного аудита). **Роль:** `release-engineer`.

**Применимость:** Текущая 1.2.0 после разрешения на соответствующую работу.

**Зависимости:** `R12-G01`.

**Definition of Done:** Change classifier различает runtime/build, config, test harness и docs; тест invalidируется по зависимостям; перенос evidence требует совпадения всех значимых входов, не только названия файла.

**Особое условие:** При равных значимых входах перенос evidence допустим с обоснованием. Изменение самого collector/oracle может инвалидировать прежний вывод, даже без runtime diff.

**Трассировка:** REL_GATE; E13-010; [AUD-S01], [AUD-S04].

### R12-G04 — Реальный исполняемый CI вместо зелёной декларации

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `release-engineer`.

**Применимость:** Текущая 1.2.0 после разрешения на соответствующую работу.

**Зависимости:** `R12-G01`.

**Definition of Done:** Определён разрешённый CI lane; retained receipt имеет команды, exit codes, environment и SHAs; job без steps остаётся NOT_RUN; untrusted PR не получают signing secrets.

**Трассировка:** E00-002; E00-008; E00-009; [AUD-S01], [AUD-S03].

### R12-G05 — Развести public, candidate и development metadata

**Приоритет:** P1. **Тип:** Исправление (классификация исходного аудита). **Роль:** `release-engineer`.

**Применимость:** Текущая 1.2.0 после разрешения на соответствующую работу.

**Зависимости:** `R12-G01`.

**Definition of Done:** Публичная версия, приватный кандидат и development target отражают фактически прочитанное состояние, а не принудительно возвращаются к 1.1.6/candidate.33. Разведены candidate_created и назначение каждого metadata owner; Ed25519 manifest не отображается как Windows Authenticode.

**Редакционное уточнение:** эта формулировка заменяет соответствующий DoD предыдущего аудита; основание — границы и исправления в файле 01. Остальные обязательства ID сохранены в выбранном scope.

**Трассировка:** E01-001; E01-008; [AUD-S02], [AUD-S17].

### R12-G06 — Проверить enforcement и действующие исключения

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `security-release`.

**Применимость:** Текущая 1.2.0 после разрешения на соответствующую работу.

**Зависимости:** `R12-G01`.

**Definition of Done:** Прочитаны branch rules/rulesets и bypass; owner-solo исключение ограничено версией/каналом/сроком; waiver отделён от тестового PASS; цена GitHub-плана не подменяет policy.

**Трассировка:** REL-001; E00-002; [AUD-S01], [AUD-S03].

### R12-G07 — Отделить release-index, source-only и legacy lanes

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `release-engineer`.

**Применимость:** Текущая 1.2.0 после разрешения на соответствующую работу.

**Зависимости:** `R12-G02`.

**Definition of Done:** Official manifest не подтягивает Pokrov-client/старый core/PORTALapp по имени или latest; legacy явно классифицирован; provenance и license/source obligations проверены для фактических бинарников.

**Трассировка:** E01-005; E13-007; [AUD-S05], [AUD-S19].

## N. Подключение и корректность маршрута

### R12-N01 — Desired → fetched → staged → effective profile revision

**Приоритет:** STOP-SHIP. **Тип:** Исправление (классификация исходного аудита). **Роль:** `client+portal`.

**Применимость:** Текущая 1.2.0: исправление и проверка существующего connection path.

**Зависимости:** `R12-G01`.

**Definition of Done:** Состояния имеют revision/digest и origin; назначение AWG2 после AWG31 приводит к применению нужного профиля либо явному «изменение не применено»; обычный reconnect и repair не дают ложного подтверждения.

**Особое условие:** Первая техническая задача. Проверить current HEAD: историческое наблюдение — основание regression, не автоматически незакрытый баг.

**Трассировка:** E03-003; FRKN_AWG; [AUD-S01], [AUD-S06].

### R12-N02 — Транзакция применения и rollback профиля

**Приоритет:** P0. **Тип:** Интеграция (классификация исходного аудита). **Роль:** `client-runtime`.

**Применимость:** Текущая 1.2.0: исправление и проверка существующего connection path.

**Зависимости:** `R12-N01`.

**Definition of Done:** Validate → checkpoint → stop/stage/start → proof → commit; ошибка возвращает last-known-good только при допустимой политике и entitlement; direct fallback и расширение app scope не происходят молча.

**Трассировка:** E03-004; E03-007; [AUD-S06], [AUD-S14].

### R12-N03 — Связать protection proof с effective route

**Приоритет:** P0. **Тип:** Интеграция (классификация исходного аудита). **Роль:** `client+core`.

**Применимость:** Текущая 1.2.0: исправление и проверка существующего connection path.

**Зависимости:** `R12-N01`.

**Definition of Done:** Proof принадлежит active attempt/profile/route mode; API availability, DNS resolution и peer handshake не подменяют protected egress; system-proxy/selected-app coverage названы явно.

**Особое условие:** Успешный ответ verifier доказывает его подлинность/путь в пределах контракта, но сам по себе не доказывает отсутствие любых утечек всех приложений.

**Трассировка:** E03-005; FE_BUG; [AUD-S06], [AUD-S14], [AUD-S15].

### R12-N04 — Регрессии event fencing и конкурирующих probes

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `core+android`.

**Применимость:** Текущая 1.2.0: исправление и проверка существующего connection path.

**Зависимости:** `R12-N03`.

**Definition of Done:** Сохранён внешний run/attempt/generation/sequence fence; две URL-проверки внутри одной attempt, timeout и поздний success не подтверждают чужую цель; при невозможности такого interleaving доказана serialization.

**Особое условие:** Внешний generation fence уже был найден в коде. Не переписывать его под предположение, что его нет.

**Трассировка:** E03-003; E04-003; [AUD-S14], [AUD-S15].

### R12-N05 — Различать наблюдения и гипотезы блокировки

**Приоритет:** P1. **Тип:** Интеграция (классификация исходного аудита). **Роль:** `network-runtime`.

**Применимость:** Текущая 1.2.0: исправление и проверка существующего connection path.

**Зависимости:** `R12-N01`, `R12-N03`.

**Definition of Done:** Коды отдельно описывают наблюдения: offline, DNS, endpoint connect, UDP timeout, TLS/data stall, runtime, entitlement и provisioning. MTU/DPI/ASN/whitelist как причина остаются гипотезами, пока не получено достаточное подтверждение. В 1.2.0 исправляются taxonomy и copy существующего пути; новый confidence/Broker engine относится к POST12-05/10.

**Редакционное уточнение:** эта формулировка заменяет соответствующий DoD предыдущего аудита; основание — границы и исправления в файле 01. Остальные обязательства ID сохранены в выбранном scope.

**Трассировка:** OBS; FRKN_MONITOR; [AUD-S06], [AUD-S14].

### R12-N06 — Ограниченный автоматический fallback

**Приоритет:** P1. **Тип:** Оптимизация (классификация исходного аудита). **Роль:** `client-runtime`.

**Применимость:** Текущая 1.2.0: исправление и проверка существующего connection path.

**Зависимости:** `R12-N02`, `R12-N05`.

**Definition of Done:** Retry budget, backoff+jitter, circuit breaker, negative TTL и last-good preference; не более согласованного числа активных probes; нет бесконечного AWG↔VLESS пинг-понга и unsafe direct fallback.

**Особое условие:** Только существующие capability/selector/fallback boundaries. Новый Adaptive Transport Manager, remote fleet scoring и Broker не прятать в этот slice.

**Трассировка:** E03-007; FRKN_AWG; [AUD-S05], [AUD-S14].

### R12-N07 — Control-plane outage и bootstrap

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `network+client`.

**Применимость:** Текущая 1.2.0: исправление и проверка существующего connection path.

**Зависимости:** `R12-N02`.

**Definition of Done:** Проверен outage-путь уже существующих API/cache/profile механизмов: отказ API не обрывает здоровый разрешённый tunnel без причины, но не создаёт новый entitlement и не превращает старые credentials в бессрочный доступ. Документированы текущие expiry/revoke ограничения. Новую offline-lease/key-hierarchy архитектуру из ATS-005 этим slice не внедрять; необходимое исправление существующего кеша выделять по доказанному дефекту.

**Редакционное уточнение:** эта формулировка заменяет соответствующий DoD предыдущего аудита; основание — границы и исправления в файле 01. Остальные обязательства ID сохранены в выбранном scope.

**Трассировка:** E01-007; E03-009; [AUD-S05], [AUD-S06].

### R12-N08 — Routing truth matrix

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `qa-network`.

**Применимость:** Текущая 1.2.0: исправление и проверка существующего connection path.

**Зависимости:** `R12-N02`, `R12-N03`.

**Definition of Done:** Full / All except RU / selected / except selected проверены по поддерживаемой платформе; empty selected fail-closed; IPv6/DNS/LAN и банковские direct-исключения не трактуются одинаково во всех режимах.

**Трассировка:** E05-009; E06-010; [AUD-S05], [AUD-S06].

## A. AWG и связанные лабораторные контуры

### R12-A01 — Закрепить AWG3.1 baseline и границу публичного scope

Историческое название: «Один основной AWG production candidate»; слово production заменено, чтобы не расширять scope автоматически.

**Приоритет:** P0. **Тип:** Решение (классификация исходного аудита). **Роль:** `core+network-owner`.

**Применимость:** Существующий безопасный AWG lab / явно согласованный AWG scope; публичное включение не разрешено.

**Зависимости:** `R12-G01`.

**Definition of Done:** Зафиксированы точные AWG3.1 pin, wire/config contract и потребители; AWG2 остаётся отдельным контуром с собственным evidence. Для 1.2.0 сохраняются согласованные default-off/lab границы. Возможное публичное включение требует отдельного product scope decision и своей runtime/origin матрицы, а не переименования lab в production.

**Редакционное уточнение:** эта формулировка заменяет соответствующий DoD предыдущего аудита; основание — границы и исправления в файле 01. Остальные обязательства ID сохранены в выбранном scope.

**Трассировка:** FRKN_AWG; [AUD-S12], [AUD-S13], [AUD-W01], [AUD-W02].

### R12-A02 — Interop с реальным owned AWG server

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `core+network`.

**Применимость:** Существующий безопасный AWG lab / явно согласованный AWG scope; публичное включение не разрешено.

**Зависимости:** `R12-A01`.

**Definition of Done:** Совпадают клиентская версия, серверный image digest, required parameters, HP key и peer material; bidirectional data проходит; несовместимые AWG2/AWG31 не «конвертируются» переименованием.

**Особое условие:** Изменение удалённого owned server разрешается отдельно. Локальная fixture не заменяет server/device proof.

**Трассировка:** FRKN_AWG; [AUD-S12], [AUD-S13].

### R12-A03 — Cross-field validation и packet-size budget

**Приоритет:** P0. **Тип:** Исправление (классификация исходного аудита). **Роль:** `core`.

**Применимость:** Существующий безопасный AWG lab / явно согласованный AWG scope; публичное включение не разрешено.

**Зависимости:** `R12-A01`, `R12-A02`.

**Definition of Done:** Проверены текущий validator и upstream ограничения H/S/I/J, обязательная header protection, суммарный wire-size/MTU и отношения timing. Unsupported значения отклоняются предсказуемо. Текущая разрешённая матрица MTU 1280/1400/1408 перепроверена по exact pin; 1360/1420 и HP-off не считаются положительными cases существующего контракта. Сначала negative test, затем исправление только доказанного пробела. DisableCookies и upstream refresh — отдельная post-release работа по файлу 05.

**Редакционное уточнение:** эта формулировка заменяет соответствующий DoD предыдущего аудита; основание — границы и исправления в файле 01. Остальные обязательства ID сохранены в выбранном scope.

**Трассировка:** E04-009; FRKN_AWG; [AUD-S12], [AUD-S13], [AUD-W01], [AUD-W03].

### R12-A04 — Managed provisioning и key lifecycle

**Приоритет:** P1. **Тип:** Интеграция (классификация исходного аудита). **Роль:** `portal+security`.

**Применимость:** Существующий безопасный AWG lab / явно согласованный AWG scope; публичное включение не разрешено.

**Зависимости:** `R12-A02`, `R12-N01`.

**Definition of Done:** Device-bound выдача, одноразовые/повторные запросы, rotate/revoke/expiry, race при смене профиля и утрата устройства; secrets отсутствуют в telemetry/support/операторском preview.

**Особое условие:** Доработка существующего provisioning не означает внедрение новой offline entitlement модели.

**Трассировка:** OBS; FRKN_AWG; [AUD-S12], [AUD-S13].

### R12-A05 — Независимая RU-origin matrix

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `qa-network`.

**Применимость:** Существующий безопасный AWG lab / явно согласованный AWG scope; публичное включение не разрешено.

**Зависимости:** `R12-A02`, `R12-N03`, `R12-N08`.

**Definition of Done:** Для принятого AWG scope сохранены exact artifacts/profile/server revision и результаты из реально доступных независимых RU origins. Две мобильные и одна фиксированная сеть остаются предложением начальной выборки, а не основанием выдумать недоступные прогоны. Claim ограничен фактической матрицей; расширение публичного охвата без неё запрещено. Короткий единичный smoke не назван длительной стабильностью.

**Редакционное уточнение:** эта формулировка заменяет соответствующий DoD предыдущего аудита; основание — границы и исправления в файле 01. Остальные обязательства ID сохранены в выбранном scope.

**Трассировка:** FRKN_AWG; REL_GATE; [AUD-S01], [AUD-S06].

### R12-A06 — Выбрать AWG presets по измерениям

**Приоритет:** P1. **Тип:** Оптимизация (классификация исходного аудита). **Роль:** `core-performance`.

**Применимость:** Существующий безопасный AWG lab / явно согласованный AWG scope; публичное включение не разрешено.

**Зависимости:** `R12-A03`, `R12-A05`.

**Definition of Done:** Контрольная конфигурация против 2–3 согласованных пресетов; CPU, battery, handshake/egress time, sustained data, loss, retransmissions и packet overhead; нет обещания ускорения из числа Jc.

**Особое условие:** Размеры payload, число presets и battery budgets — параметры лаборатории; не новая тяжёлая проверка на каждом connect.

**Трассировка:** E13-001; FRKN_AWG; [AUD-S12], [AUD-S13], [AUD-W03].

### R12-A07 — TCP fallback при недоступном UDP

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `network-runtime`.

**Применимость:** Существующий безопасный AWG lab / явно согласованный AWG scope; публичное включение не разрешено.

**Зависимости:** `R12-A05`, `R12-N06`.

**Definition of Done:** Сценарий UDP blocked не вызывает бесконечный AWG/HY2 retry; доступный managed TCP/TLS path выбирается с тем же routing/privacy scope; блок IP/ASN требует другого разрешённого endpoint, а не новой подписи пакета.

**Особое условие:** Hysteria2 и AWG разделяют зависимость от UDP и не являются независимым спасением при полном UDP-blackhole.

**Трассировка:** FRKN_AWG; FRKN_HY2; [AUD-S05], [AUD-W01].

### R12-A08 — Разделить Smart DNS, WARP и AWG

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `network+frontend`.

**Применимость:** Существующий безопасный AWG lab / явно согласованный AWG scope; публичное включение не разрешено.

**Зависимости:** `R12-N01`, `R12-N03`.

**Definition of Done:** Селективный DNS/TLS forwarding имеет собственные capability/proof; AAAA, QUIC, ECH/нечитаемый SNI и direct fallback проверены; DNS success не означает VPN или доступность ChatGPT/Game Pass.

**Особое условие:** Проверяется уже существующий lab. Общий Smart Access provider pool и новый каталог идут по файлу 06 после activation gate.

**Трассировка:** FRKN_PLAN; FE; [AUD-S05], [AUD-S06].

### R12-A09 — AWG canary и обратимое отключение

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `release+network`.

**Применимость:** Существующий безопасный AWG lab / явно согласованный AWG scope; публичное включение не разрешено.

**Зависимости:** `R12-A04`, `R12-A05`, `R12-A06`, `R12-A07`.

**Definition of Done:** В рамках отдельно разрешённой лаборатории проверены ограниченная выдача, server-side kill, actual effective readback и rollback. При предлагаемом публичном canary требуются отдельные scope/cohort/health решения. Один client report не вызывает global quarantine. Не создавать новый Endpoint Broker внутри 1.2.0; новая anti-poisoning/scoped automation реализуется через POST12-05/10.

**Редакционное уточнение:** эта формулировка заменяет соответствующий DoD предыдущего аудита; основание — границы и исправления в файле 01. Остальные обязательства ID сохранены в выбранном scope.

**Трассировка:** FRKN_AWG; FRKN_MONITOR; [AUD-S01], [AUD-S05].

## W. Windows

### R12-W01 — Win10/Win11 exact managed-network matrix

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `qa-windows`.

**Применимость:** Заявленные Windows 10/11 и фактический канал поставки 1.2.0.

**Зависимости:** `R12-G03`, `R12-N03`.

**Definition of Done:** Standard-user UI + SCM, device-wide TUN, DNS/IPv6/routes и реальный managed transport; synthetic fixture сохраняется отдельным evidence class; Win10 lifecycle условия указаны в поддержке.

**Особое условие:** Win10 edition/build/ESU/LTSC отмечаются в матрице; проверка POKROV не удостоверяет безопасность самой ОС.

**Трассировка:** E05-009; [AUD-S01], [AUD-S06], [AUD-W04].

### R12-W02 — Crash/sleep/network handoff без сетевого ущерба

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `windows-runtime`.

**Применимость:** Заявленные Windows 10/11 и фактический канал поставки 1.2.0.

**Зависимости:** `R12-W01`.

**Definition of Done:** Core/UI/service crash, forced termination, sleep, Wi-Fi↔Ethernet, reconnect и reboot; restore только POKROV-owned state; ранее пройденные exact recovery тесты переиспользованы лишь при совпадении зависимостей.

**Трассировка:** E05-006; E05-010; [AUD-S01], [AUD-S04].

### R12-W03 — Install/update/uninstall на реально выдаваемых bytes

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `windows-installer`.

**Применимость:** Заявленные Windows 10/11 и фактический канал поставки 1.2.0.

**Зависимости:** `R12-W01`.

**Definition of Done:** Clean standard-user VM, installed service ACL, package identity, upgrade while connected, uninstall/reinstall; uninstall не удаляет чужие WFP/firewall/routes и не оставляет TUN.

**Трассировка:** E05-011; E13-008; [AUD-S01], [AUD-S04].

### R12-W04 — Tray/focus/startup/single instance regression

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `windows-shell`.

**Применимость:** Заявленные Windows 10/11 и фактический канал поставки 1.2.0.

**Зависимости:** `R12-W01`.

**Definition of Done:** Один UI/tray; foreground activation и login hidden startup различаются; без repeated UAC; сохранены проверки candidate33 focus и Run-key toggle.

**Особое условие:** Исторические результаты candidate.33 могут быть переиспользованы только по G03, без фиктивного повторного запуска.

**Трассировка:** E05-001; E05-008; [AUD-S01], [AUD-S04].

### R12-W05 — CPU/RAM/cold-start реальные бюджеты

**Приоритет:** P1. **Тип:** Оптимизация (классификация исходного аудита). **Роль:** `windows-performance`.

**Применимость:** Заявленные Windows 10/11 и фактический канал поставки 1.2.0.

**Зависимости:** `R12-G03`, `R12-W01`.

**Definition of Done:** UI и service измерены раздельно и вместе; unavailable counter=UNKNOWN, не 0; warm/cold/post-reboot разделены; интервал, sample count, hardware и collector version зафиксированы.

**Трассировка:** E13-001; E13-002; [AUD-S01], [AUD-S04].

### R12-W06 — IPC negative cases и WFP coexistence

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `security-windows`.

**Применимость:** Заявленные Windows 10/11 и фактический канал поставки 1.2.0.

**Зависимости:** `R12-W01`.

**Definition of Done:** ACL/caller SID, frame bounds, nonce/replay, cancellation, concurrent commands; совместимость firewall/другой VPN/локальных приложений; один владелец network transaction.

**Трассировка:** E05-004; SEC-001; [AUD-S01], [AUD-S05].

## D. Android

### R12-D01 — Проверить primary ARM64 APK, не только universal

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `qa-android`.

**Применимость:** Заявленные Android API/ABI/OEM и фактический канал поставки 1.2.0.

**Зависимости:** `R12-G02`, `R12-N03`.

**Definition of Done:** Точный выдаваемый ARM64 artifact установлен/обновлён на физическом устройстве с сохранением аккаунта; signer/package/versionCode/ABI/SDK continuity доказаны; universal proof не подставлен вместо ARM64.

**Трассировка:** E06-006; E13-008; [AUD-S02], [AUD-S17].

### R12-D02 — Wi-Fi/LTE/IPv6/MTU/UDP53 матрица

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `android-runtime`.

**Применимость:** Заявленные Android API/ABI/OEM и фактический канал поставки 1.2.0.

**Зависимости:** `R12-D01`, `R12-N08`.

**Definition of Done:** Смена default network и captive portal; tunneled/selected/direct DNS по policy; UDP53 blocked, IPv6-only/NAT64 где применимо, MTU edge cases; no route loop и no false success.

**Трассировка:** E06-008; E06-010; [AUD-S06], [AUD-S14].

### R12-D03 — OEM, Doze, lifecycle и энергия

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `android-runtime`.

**Применимость:** Заявленные Android API/ABI/OEM и фактический канал поставки 1.2.0.

**Зависимости:** `R12-D01`.

**Definition of Done:** Минимальный поддерживаемый Android и актуальная API; Huawei/Samsung/Pixel или согласованный subset; permission revoke/lockdown/process kill/reboot/Doze; долгий сеанс и battery baseline, не только подключение на экране.

**Трассировка:** E06-001; E06-009; [AUD-S01], [AUD-S06].

### R12-D04 — Direct/store authority и downgrade boundaries

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `android-updater`.

**Применимость:** Заявленные Android API/ABI/OEM и фактический канал поставки 1.2.0.

**Зависимости:** `R12-D01`.

**Definition of Done:** Проверены identity/size/hash/origin direct updater и отсутствие self-install authority в store flavor. Для поддерживаемых переходов ABI/universal/split/package/signing/versionCode continuity доказано сохранение данных. Неподдерживаемый переход честно отвергается с recovery-путём; его нельзя объявить поддерживаемым только потому, что совпал versionName.

**Редакционное уточнение:** эта формулировка заменяет соответствующий DoD предыдущего аудита; основание — границы и исправления в файле 01. Остальные обязательства ID сохранены в выбранном scope.

**Трассировка:** E06-005; E06-007; [AUD-S17].

### R12-D05 — Логи, notification и счётчики только по контракту

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `privacy-android`.

**Применимость:** Заявленные Android API/ABI/OEM и фактический канал поставки 1.2.0.

**Зависимости:** `R12-D01`.

**Definition of Done:** Private lockscreen, bounded journals, structured allowlist; traffic UI ясно отличает tunnel counters от UID totals; реальные native log paths проходят planted-secret regression.

**Трассировка:** AND-001; AND-002; OBS; [AUD-S12], [AUD-S15].

### R12-D06 — Уменьшать доставку по size breakdown

**Приоритет:** P1. **Тип:** Оптимизация (классификация исходного аудита). **Роль:** `android-build`.

**Применимость:** Заявленные Android API/ABI/OEM и фактический канал поставки 1.2.0; неблокирующее улучшение при отсутствии собственной safety/UX регрессии.

**Зависимости:** `R12-D01`.

**Definition of Done:** APK diff разбит на ABI/core/assets/fonts/resources; desktop/evidence/debug material отсутствует; ARM64 primary, universal fallback; дальнейшее урезание только без потери runtime/license/source obligations.

**Трассировка:** REPO-001; E13-002; [AUD-S02], [AUD-S17].

## C. Core, архитектура и производительность

### R12-C01 — Сохранить ABI2 и проверить artifacts consumers

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `core-ci`.

**Применимость:** Текущая 1.2.0; большие оптимизации не блокируют выпуск без доказанной необходимости.

**Зависимости:** `R12-G04`.

**Definition of Done:** ABI/config/event/capability matrix на Android/Windows; compile/link/symbol checks и consumers на pinned core; ABI3 не становится новым условием готовности 1.2.0.

**Трассировка:** E01-005; E04-005; E04-006; [AUD-S05], [AUD-S12].

### R12-C02 — Lifecycle/race/fuzz/resource bounds

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `core-qa`.

**Применимость:** Текущая 1.2.0; большие оптимизации не блокируют выпуск без доказанной необходимости.

**Зависимости:** `R12-C01`.

**Definition of Done:** start/stop/reload/session cancellation циклы, malformed profiles, event queue backpressure, goroutine/fd/handle stability и race на поддерживаемых пакетах; binaries match source pin.

**Трассировка:** E04-003; E04-009; E13-003; [AUD-S12], [AUD-S13].

### R12-C03 — Извлечь реальные владельцы состояния из bootstrap

**Приоритет:** P1. **Тип:** Оптимизация (классификация исходного аудита). **Роль:** `client-architecture`.

**Применимость:** Текущая 1.2.0; большие оптимизации не блокируют выпуск без доказанной необходимости; неблокирующее улучшение при отсутствии собственной safety/UX регрессии.

**Зависимости:** `R12-N01`, `R12-N03`.

**Definition of Done:** Первый slice=profile lifecycle, затем connection/presentation, support и checkout; extraction и behavior changes раздельны; standalone tests; root и количество part не растут; размер не используется как KPI скорости.

**Трассировка:** E02-006; E03-006; [AUD-S18], [AUD-S05].

### R12-C04 — Ограничить rebuild/repaint/polling

**Приоритет:** P1. **Тип:** Оптимизация (классификация исходного аудита). **Роль:** `client-performance`.

**Применимость:** Текущая 1.2.0; большие оптимизации не блокируют выпуск без доказанной необходимости; неблокирующее улучшение при отсутствии собственной safety/UX регрессии.

**Зависимости:** `R12-C03`.

**Definition of Done:** Traffic updates 2–4 Hz как исходный эксперимент; profile не rebuild от каждого runtime tick; offscreen/inactive animations stop; profile traces на reference Android/Windows подтверждают выигрыш или отсутствие регрессии.

**Трассировка:** E13-002; FE; [AUD-S05].

### R12-C05 — Final binary dependency/license/privacy scan

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `security-core`.

**Применимость:** Текущая 1.2.0; большие оптимизации не блокируют выпуск без доказанной необходимости.

**Зависимости:** `R12-C01`.

**Definition of Done:** SBOM и лицензии соответствуют реально встроенным libs; scan APK/DLL/EXE и runtime logging, known advisories разбираются по reachability; npm audit=0 не трактуется как отсутствие уязвимостей.

**Трассировка:** E04-010; E12-005; E13-007; [AUD-S01], [AUD-S12], [AUD-S19].

## B. Backend и платежи

### R12-B01 — Invalid preview всегда запрещает оплату

**Приоритет:** P0. **Тип:** Исправление (классификация исходного аудита). **Роль:** `web-checkout`.

**Применимость:** Корректность существующей коммерческой цепочки 1.2.0.

**Зависимости:** `R12-G01`.

**Definition of Done:** checkoutReady требует server-valid, matching quote generation, применимость и срок; empty promo не обходит invalid preview; missing amount не становится 1 ₽; regression на legal/capacity rejection.

**Особое условие:** Regression на клиентскую readiness-логику не объявлять доказательством ошибочного списания в production.

**Трассировка:** MKT-000; FE; E08; [AUD-S08].

### R12-B02 — Закрыть stale quote окно debounce

**Приоритет:** P0. **Тип:** Исправление (классификация исходного аудита). **Роль:** `web-checkout`.

**Применимость:** Корректность существующей коммерческой цепочки 1.2.0.

**Зависимости:** `R12-B01`.

**Definition of Done:** Изменение plan/promo/account/provider немедленно инвалидирует quote; текущий query key и generation сверяются; старый token и новый promo никогда не отправляются вместе.

**Трассировка:** FE; MKT; [AUD-S08].

### R12-B03 — Truthful payment return, включая legacy success URL

**Приоритет:** P1. **Тип:** Исправление (классификация исходного аудита). **Роль:** `web+backend-payments`.

**Применимость:** Корректность существующей коммерческой цепочки 1.2.0.

**Зависимости:** `R12-B01`.

**Definition of Done:** Прямой GET /pay/success без order proof не сообщает об оплате; экран получает server-authoritative status; paid→fulfillment pending→access active разделены; refresh не создаёт новый платёж.

**Особое условие:** Возврат браузера от провайдера и paid/fulfilled — разные события.

**Трассировка:** E08-004; FE; [AUD-S09], [AUD-S08].

### R12-B04 — Bounded fetch и graceful recovery

**Приоритет:** P1. **Тип:** Исправление (классификация исходного аудита). **Роль:** `web-checkout`.

**Применимость:** Корректность существующей коммерческой цепочки 1.2.0.

**Зависимости:** `R12-B01`.

**Definition of Done:** Catalog/providers получают abort+deadline; acquisition failure не задерживает commerce readiness; UI имеет retry/error; запросы key-status debounced/abortable; raw provider body не показывается человеку.

**Трассировка:** FE; E09-001; [AUD-S08].

### R12-B05 — Идемпотентность order-create и quote reservation

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `backend-payments`.

**Применимость:** Корректность существующей коммерческой цепочки 1.2.0.

**Зависимости:** `R12-B01`, `R12-B02`.

**Definition of Done:** Timeout после server commit, повторный POST/другой API base возвращают тот же order по стабильному intent ID; provider amount local-authoritative; expired/reserved quota и late callback согласованы.

**Трассировка:** E08-002; E08-004; E08-008; [AUD-S08], [AUD-S09].

### R12-B06 — Provider payment/refund/reconciliation E2E

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `backend+qa-finance`.

**Применимость:** Корректность существующей коммерческой цепочки 1.2.0.

**Зависимости:** `R12-B05`.

**Definition of Done:** Controlled provider sandbox/разрешённый live тест, replay/mismatch/currency/duplicate/partial fulfillment/refund/outbox; оплаченный заказ один раз даёт правильный доступ; telemetry не authority.

**Особое условие:** Sandbox/fixture и реальные provider операции имеют разные labels. Реальные расходы/возвраты отдельно авторизуются.

**Трассировка:** E08-008; REL_GATE; [AUD-S01], [AUD-S03], [AUD-S09].

### R12-B07 — DB/HTTP/outbox bottlenecks по профилю

**Приоритет:** P1. **Тип:** Оптимизация (классификация исходного аудита). **Роль:** `backend-platform`.

**Применимость:** Корректность существующей коммерческой цепочки 1.2.0.

**Зависимости:** `R12-G01`.

**Definition of Done:** Платёжный bounded threadpool сохранён; оставшиеся ClientSession на операцию инвентаризованы; lifespan clients, pool wait, event-loop lag и outbox age; не проводить полный async ORM rewrite без нужды.

**Трассировка:** E09-001; E09-002; E09-004; [AUD-S09].

### R12-B08 — Postgres migration, deploy и rollback drill

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `backend-release`.

**Применимость:** Корректность существующей коммерческой цепочки 1.2.0.

**Зависимости:** `R12-G03`, `R12-B06`.

**Definition of Done:** Restore в изолированную настоящую Postgres, migrations expand/contract, duplicate workers и poison messages; payload completeness и delayed-health rollback; локальный byte rollback не засчитывается как live DB recovery.

**Трассировка:** E09-006; E13-009; [AUD-S01], [AUD-S04].

## O. Operator Center

### R12-O01 — OIDC/PKCE/session/RBAC live readback

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `operator-security`.

**Применимость:** Приёмка и улучшение уже существующей админки 1.2.0.

**Зависимости:** `R12-G03`.

**Definition of Done:** Same identity step-up, CSRF, exact origins/cookies/idle/absolute expiry, revoke, denial across roles; legacy verified bootstrap ограничен migration policy; public shell loading не доказательство API fail.

**Трассировка:** OC; E12-004; [AUD-S10], [AUD-S11].

### R12-O02 — Проверить 28 capability routes без переписывания shell

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `operator-frontend`.

**Применимость:** Приёмка и улучшение уже существующей админки 1.2.0.

**Зависимости:** `R12-O01`.

**Definition of Done:** Каждый маршрут привязан к workspace/API/role; UI build fingerprint matches deploy; legacy read-only redirect только после feature parity, authenticated smoke и rollback; нет dual write.

**Особое условие:** 28 — историческая inventory-опора, не лимит и не приказ удалить новые маршруты. Сверить актуальный manifest.

**Трассировка:** OC-000; OC; [AUD-S11].

### R12-O03 — Connectivity view: requested/effective/proven

**Приоритет:** P1. **Тип:** Интеграция (классификация исходного аудита). **Роль:** `operator-network`.

**Применимость:** Приёмка и улучшение уже существующей админки 1.2.0.

**Зависимости:** `R12-N01`, `R12-N03`, `R12-O01`.

**Definition of Done:** User360/attempt показывает assignment, staged/effective revision, proof stage/freshness и safe next action; нет ключей, topology/IP/raw config; «назначен AWG2, работает AWG31» виден сразу.

**Трассировка:** OC; OBS; [AUD-S06], [AUD-S11].

### R12-O04 — Моя смена, Inbox и Incident Room как рабочие сценарии

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `operator-support`.

**Применимость:** Приёмка и улучшение уже существующей админки 1.2.0.

**Зависимости:** `R12-O01`.

**Definition of Done:** Claim/assign/server SLA/waiting/internal notes/collision, incident links и audit проверены; support bundle связан с attempt; time-to-action измерен на задачах, не по числу экранов.

**Трассировка:** OC; [AUD-S11].

### R12-O05 — Развести 11 cockpit и 19 release checks

**Приоритет:** P1. **Тип:** Интеграция (классификация исходного аудита). **Роль:** `operator-release`.

**Применимость:** Приёмка и улучшение уже существующей админки 1.2.0.

**Зависимости:** `R12-G03`, `R12-O01`.

**Definition of Done:** Cockpit явно показывает policy version и mapping; данные не свёрнуты в ложный общий green; pause registry, rollback request и фактический artifact pointer rollback — разные состояния.

**Особое условие:** Количество диагностических cockpit gates не обязано равняться количеству release gates; нужна явная mapping и одинаковая семантика.

**Трассировка:** OC; REL_GATE; [AUD-S03], [AUD-S11].

### R12-O06 — Платежи и кампании до безопасного действия

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `operator-finance`.

**Применимость:** Приёмка и улучшение уже существующей админки 1.2.0.

**Зависимости:** `R12-B06`, `R12-O01`.

**Definition of Done:** Problem queues приводят к конкретному order/intent; quotes/quotas/legal/capacity/delivery видны; dangerous commands server-authorized, preview/version-bound, duplicate-safe и audited.

**Трассировка:** OC; MKT; [AUD-S07], [AUD-S11].

### R12-O07 — Responsive density и query performance

**Приоритет:** P1. **Тип:** Оптимизация (классификация исходного аудита). **Роль:** `operator-frontend`.

**Применимость:** Приёмка и улучшение уже существующей админки 1.2.0; неблокирующее улучшение при отсутствии собственной safety/UX регрессии.

**Зависимости:** `R12-O02`.

**Definition of Done:** 390/768/1280/1440, keyboard, focus, 200% zoom; длинные таблицы виртуализированы без потери a11y; abort/dedupe/stale metadata; refresh не теряет выбранный объект и черновик.

**Трассировка:** OC; FE; [AUD-S11].

## F. Frontend и продуктовый путь

### R12-F01 — Единый protection presenter без рекламного шума

**Приоритет:** P1. **Тип:** Интеграция (классификация исходного аудита). **Роль:** `client-product`.

**Применимость:** Критический путь 1.2.0; косметика и необоснованный рефактор отдельно.

**Зависимости:** `R12-N03`.

**Definition of Done:** Один state→CTA/disc/text/semantics/haptic; Connecting/Verifying/Recovering/Degraded/Disconnecting различимы; success не выдаётся по STARTED; tech details спрятаны, scope защиты виден.

**Трассировка:** FE_BUG; E11-001; [AUD-S14], [AUD-S15].

### R12-F02 — Путь download→install→trial→verified connect

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `web+client-product`.

**Применимость:** Критический путь 1.2.0; косметика и необоснованный рефактор отдельно.

**Зависимости:** `R12-D01`, `R12-W03`.

**Definition of Done:** OS/ABI detection и current manifest; handoff optional и fail-safe; permission отказ/повтор; первая сессия без принудительного Telegram, rewards и promo; 1.1.6 upgrade сохраняет идентичность.

**Трассировка:** FE; E11-004; [AUD-S17], [AUD-S05].

### R12-F03 — Motion/reduced-motion/платформенное поведение

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `client-ui`.

**Применимость:** Критический путь 1.2.0; косметика и необоснованный рефактор отдельно.

**Зависимости:** `R12-F01`.

**Definition of Done:** Idle/success без вечного пульса; reduced-motion не сохраняет длинный sticky track; native input/scroll/focus на Windows/Android; единственный haptic owner; no-JS web content visible.

**Трассировка:** FE_BUG; FE; [AUD-S05].

### R12-F04 — Rules/Profile/Locations: сохранить возможности, убрать путаницу

**Приоритет:** P1. **Тип:** Интеграция (классификация исходного аудита). **Роль:** `client-product`.

**Применимость:** Критический путь 1.2.0; косметика и необоснованный рефактор отдельно.

**Зависимости:** `R12-N08`, `R12-F01`.

**Definition of Done:** Basic routing и advanced transport разделены; объясняется reconnect; latency имеет age/unknown; access/devices/support выше rewards; Smart DNS не помечен полной VPN-защитой.

**Трассировка:** FE; E11-003; [AUD-S05], [AUD-S06].

### R12-F05 — Доступность критического пути

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `qa-accessibility`.

**Применимость:** Критический путь 1.2.0; косметика и необоснованный рефактор отдельно.

**Зависимости:** `R12-F01`, `R12-F02`.

**Definition of Done:** TalkBack/Narrator/keyboard/manual, 200% text/zoom, high contrast, no hidden focus; automated axe/golden дополнены manual proof; loading/empty/stale/permission/error различены.

**Трассировка:** E11-009; FE; [AUD-S05], [AUD-S11].

### R12-F06 — Bundle/data waterfall/route latency

**Приоритет:** P1. **Тип:** Оптимизация (классификация исходного аудита). **Роль:** `web-performance`.

**Применимость:** Критический путь 1.2.0; косметика и необоснованный рефактор отдельно; неблокирующее улучшение при отсутствии собственной safety/UX регрессии.

**Зависимости:** `R12-B04`.

**Definition of Done:** Измерены production export/runtime architecture; не предписан SSR существующему static export; heavy code lazy по месту, acquisition вне payment critical path; local synthetic и WAN/RUM budgets раздельны.

**Трассировка:** FE; E09-008; [AUD-S08], [AUD-S11].

### R12-F07 — Upgrade и многоповерхностный путь

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `qa-product`.

**Применимость:** Критический путь 1.2.0; косметика и необоснованный рефактор отдельно.

**Зависимости:** `R12-F02`, `R12-B03`.

**Definition of Done:** Deep link/browser return/tray resume сохраняют account/order/context; denied permission/API offline/expired access приводят к одному безопасному действию; нет неопределённого spinner.

**Трассировка:** FE; E13-008; [AUD-S05], [AUD-S08].

## M. Коммерция, ёмкость и маркетинг

### R12-M01 — Актуальные legal/seller/claims решения

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `commercial-owner+legal`.

**Применимость:** Действующая коммерция; внешний пилот только отдельно после разрешения.

**Зависимости:** `R12-G01`.

**Definition of Done:** Поправлена дата 10.8=01.09.2025; продавец/оферта/чек/disclosures совпадают; own site и lifecycle не объявлены автоматически безопасными; никакого внешнего запуска без отдельной оценки канала.

**Особое условие:** Юридическую квалификацию канала не заменять техническим наличием рекламного слота. Условия и сроки проверять на момент запуска.

**Трассировка:** MKT-000; MKT_STAGE; [AUD-S07], [AUD-W05], [AUD-W06].

### R12-M02 — Одна commercial revision на всех поверхностях

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `commercial-platform`.

**Применимость:** Действующая коммерция; внешний пилот только отдельно после разрешения.

**Зависимости:** `R12-B01`.

**Definition of Done:** Source→API→checkout→bot→cabinet→JSON-LD→order сумма, trial+5/TG+5/grandfathered +10, device limits и channel signing совпадают; stale catalog информационный, не платёжная authority.

**Трассировка:** E01-002; MKT; [AUD-S07], [AUD-S08], [AUD-S17].

### R12-M03 — Настоящие сроки, price hold и квоты

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `growth-platform`.

**Применимость:** Действующая коммерция; внешний пилот только отдельно после разрешения.

**Зависимости:** `R12-M01`, `R12-M02`, `R12-B05`.

**Definition of Done:** ends_at/hold server-authoritative; refresh/incognito/clock jump не продляют оффер; quota reservation atomic; expired discount исчезает; permanent start99 и annual saving без фальшивого countdown.

**Трассировка:** MKT; [AUD-S07], [AUD-S08], [AUD-S11].

### R12-M04 — Capacity guard по качеству, а не только 300 аккаунтам

**Приоритет:** P1. **Тип:** Интеграция (классификация исходного аудита). **Роль:** `growth+network-owner`.

**Применимость:** Действующая коммерция; внешний пилот только отдельно после разрешения.

**Зависимости:** `R12-M02`, `R12-N05`.

**Definition of Done:** 5000 ₽ и 300 — owner inputs; active entitlements, concurrent devices, Mbps/CPU/loss и support pressure разделены; pause/resume hysteresis сохраняется; expansion trigger раньше деградации.

**Особое условие:** Concurrent connections/entitlements/accounts различать; IP или panel mapping не доказывает количество людей. Не добавлять fingerprinting ради красивого счётчика.

**Трассировка:** MKT; FRKN_MONITOR; [AUD-S07].

### R12-M05 — Атрибуция и полезная воронка

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `growth-analytics`.

**Применимость:** Действующая коммерция; внешний пилот только отдельно после разрешения.

**Зависимости:** `R12-M02`, `R12-F02`, `R12-B06`.

**Definition of Done:** Browser и app denominators раздельны без handoff; paid outcome server-owned; campaign→offer→order→entitlement→verified connect→renewal/refund связываются privacy-safe; no fingerprint/ad SDK.

**Особое условие:** Существующий acquisition pipeline проверяется без обязательной новой /t/ интеграции; /t/ — самостоятельный POST12-40.

**Трассировка:** MKT; OBS; [AUD-S07], [AUD-S11].

### R12-M06 — Малый winback/renewal pilot и банк текстов

**Приоритет:** P2. **Тип:** Решение (классификация исходного аудита). **Роль:** `growth-owner`.

**Применимость:** Отдельный пилот после технической готовности, legal/capacity/consent и разрешения на расходы/публикацию.

**Зависимости:** `R12-M01`, `R12-M03`, `R12-M04`, `R12-M05`.

**Definition of Done:** Одна гипотеза и первичная метрика; максимум два варианта, explicit budget/quota/consent/kill switch; решение не по пяти кликам и не по fake urgency; массовый acquisition пока не нужен.

**Особое условие:** Не блокирует технический release при отсутствии рекламы; не запускать кампании от имени владельца по одному плану.

**Трассировка:** MKT_STAGE; [AUD-S05], [AUD-S07].

## V. Диагностика и приватность

### R12-V01 — Bundle redaction через все реальные sinks

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `privacy+support`.

**Применимость:** Поставляемая диагностика и поддержка 1.2.0.

**Зависимости:** `R12-N03`.

**Definition of Done:** Planted credentials/config/URL/IP/path/PII проходят native→core→app→bundle→upload→admin; секрет нигде не появляется; preview/consent/access/audit/retention и bounded storage остаются рабочими.

**Трассировка:** OBS; OBS_DOD; [AUD-S12], [AUD-S15], [AUD-S10].

### R12-V02 — Связать диагностику с причиной и effective profile

**Приоритет:** P1. **Тип:** Интеграция (классификация исходного аудита). **Роль:** `observability`.

**Применимость:** Поставляемая диагностика и поддержка 1.2.0.

**Зависимости:** `R12-N01`, `R12-N05`.

**Definition of Done:** Correlation и закрытые reason codes едины; expected/effective mismatch имеет код и repair; отсутствующие измерения=UNKNOWN; aggregate telemetry отделена от opt-in support и server security audit.

**Трассировка:** OBS; [AUD-S06], [AUD-S15].

### R12-V03 — Наблюдаемость не ломает VPN

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `observability-qa`.

**Применимость:** Поставляемая диагностика и поддержка 1.2.0.

**Зависимости:** `R12-V01`.

**Definition of Done:** Disk full, corrupt journal, queue full, event storm, clock jump, unsupported schema и upload timeout не блокируют hot path; drop counters и bounded spool без raw payload.

**Трассировка:** OBS_DOD; OBS_PB; [AUD-S12], [AUD-S15].

### R12-V04 — Поддержка по одному безопасному case code

**Приоритет:** P1. **Тип:** Интеграция (классификация исходного аудита). **Роль:** `support-ops`.

**Применимость:** Поставляемая диагностика и поддержка 1.2.0.

**Зависимости:** `R12-V01`, `R12-V02`, `R12-O04`.

**Definition of Done:** По case видно version/profile/proof/last attempts/known issue; доступ case-bound/RBAC/audited; expiration отрабатывает; AI только объясняет/предлагает, не выполняет operator commands.

**Трассировка:** OBS; OC; [AUD-S10], [AUD-S11].

## L. Linux

### R12-L01 — Ограничить Linux beta Ubuntu24.04 amd64

**Приоритет:** P1. **Тип:** Решение (классификация исходного аудита). **Роль:** `linux-owner`.

**Применимость:** Отдельная условная Linux beta; не добавлять в публичный scope 1.2.0 автоматически.

**Зависимости:** `R12-G01`.

**Definition of Done:** Для предложенной первой Linux beta зафиксированы Ubuntu 24.04 amd64, systemd/NetworkManager/resolved/nftables/polkit prerequisites и отдельный scope. Текущая capability отражает реальную доступность live connect; историческое false не принуждается, если функция уже доказанно реализована. Public Linux claim разрешается только своим gate.

**Редакционное уточнение:** эта формулировка заменяет соответствующий DoD предыдущего аудита; основание — границы и исправления в файле 01. Остальные обязательства ID сохранены в выбранном scope.

**Трассировка:** E07; [AUD-S16].

### R12-L02 — Подключить live Core к dormant transaction plan

**Приоритет:** P1. **Тип:** Интеграция (классификация исходного аудита). **Роль:** `linux+core`.

**Применимость:** Отдельная условная Linux beta; не добавлять в публичный scope 1.2.0 автоматически.

**Зависимости:** `R12-L01`, `R12-C01`.

**Definition of Done:** Daemon действительно стартует core/TUN, даёт validated plan участникам NM/resolved/nft; UI non-root; typed IPC; ни произвольного shell, ни flush чужого ruleset.

**Трассировка:** E07-003; E07-006; E07-007; E07-008; [AUD-S16].

### R12-L03 — Durable recovery и desktop authorization

**Приоритет:** P1. **Тип:** Интеграция (классификация исходного аудита). **Роль:** `linux-runtime`.

**Применимость:** Отдельная условная Linux beta; не добавлять в публичный scope 1.2.0 автоматически.

**Зависимости:** `R12-L02`.

**Definition of Done:** После crash/suspend/reboot восстанавливается только owned state; polkit deny/timeout/missing agent корректны; partial rollback сохраняет retry journal; live host доказательство.

**Трассировка:** E07-004; E07-005; E07-009; [AUD-S16].

### R12-L04 — Signed deb install/update/remove + clean VM

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `linux-packaging`.

**Применимость:** Отдельная условная Linux beta; не добавлять в публичный scope 1.2.0 автоматически.

**Зависимости:** `R12-L03`.

**Definition of Done:** Пакет, service unit, file/socket permissions, upgrade/migrations/uninstall и DNS/IPv6/full/RU modes проверены на exact artifact; пользователь не обязан постоянно запускать UI через sudo.

**Трассировка:** E07-010; E07-011; [AUD-S16].

### R12-L05 — Отдельно Fedora/aarch64/per-app

**Приоритет:** P2. **Тип:** Решение (классификация исходного аудита). **Роль:** `linux-owner`.

**Применимость:** После отдельно принятой первой Linux beta; не часть обязательного Android/Windows выпуска.

**Зависимости:** `R12-L04`.

**Definition of Done:** RPM, другие distros, cgroup per-app и дополнительный desktop matrix не блокируют Android/Windows/AWG; Linux unavailable UI заменяется support claim только после own gate.

**Трассировка:** E07-012; [AUD-S16].

## Q. Финальная приёмка и выпуск

### R12-Q01 — Сводная exact-candidate acceptance matrix

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `qa-release`.

**Применимость:** Выбранный release scope; live/promote/cohort действия отдельно разрешаются.

**Зависимости:** `R12-G03`, `R12-N03`, `R12-W01`, `R12-D01`, `R12-B06`, `R12-O01`, `R12-V01`.

**Definition of Done:** Каждый сценарий имеет required/scope/platform/artifact/config/expected/result/evidence; conditional labs и retired goals не раздувают обязательный denominator; missing не маскируется PASS.

**Особое условие:** Сначала фиксируется denominator выбранного scope. Нельзя после failing check молча вынести его в N/A.

**Трассировка:** REL_GATE; REL_DOD; [AUD-S01], [AUD-S03].

### R12-Q02 — Soak/chaos и регрессионные циклы

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `qa-network`.

**Применимость:** Выбранный release scope; live/promote/cohort действия отдельно разрешаются.

**Зависимости:** `R12-Q01`.

**Definition of Done:** Репрезентативный длительный сеанс и 100-cycle test на согласованных reference hosts; packet loss, offline/resume и long sessions; published claim ограничен фактической coverage.

**Особое условие:** 100-cycle — release/soak-проверка в выделенной среде, не обязательный rerun после любого документационного commit.

**Трассировка:** E13-003; E13-004; [AUD-S01], [AUD-S06].

### R12-Q03 — Новый go/no-go на финальных bytes

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `release+ops`.

**Применимость:** Выбранный release scope; live/promote/cohort действия отдельно разрешаются.

**Зависимости:** `R12-Q01`, `R12-B08`, `R12-Q02`, `R12-G04`, `R12-C05`, `R12-F05`, `R12-F07`, `R12-V03`.

**Definition of Done:** Сформировано новое go/no-go на точном выбранном кандидате, не переписан исторический Gate F. Обязательные pre-publication проверки и rollback readiness закрыты, waivers ограничены каналом и отдельно видны. Публичный post-promotion readback находится в Q04/Q05 и не объявляется выполненным заранее. Код, подписи, платежи, сеть, privacy и UX имеют evidence по применимому scope.

**Редакционное уточнение:** эта формулировка заменяет соответствующий DoD предыдущего аудита; основание — границы и исправления в файле 01. Остальные обязательства ID сохранены в выбранном scope.

**Трассировка:** E13-009; E13-010; [AUD-S03].

### R12-Q04 — Same-byte staged rollout с pause/rollback

**Приоритет:** P0. **Тип:** Проверка (классификация исходного аудита). **Роль:** `release-owner`.

**Применимость:** Только после отдельного owner разрешения на выбранную поставку и среды.

**Зависимости:** `R12-Q03`.

**Definition of Done:** Отдельное разрешение; сначала малая проверенная группа, затем расширение по connect/crash/support/error evidence; min-version не выталкивает пользователей без работающего upgrade; public artifacts не пересобраны.

**Особое условие:** Разрешение local implementation не означает разрешение публикации/расширения когорты.

**Трассировка:** E13-006; REL_GATE; [AUD-S03], [AUD-S11].

### R12-Q05 — Наблюдение и закрытие релиза

**Приоритет:** P1. **Тип:** Проверка (классификация исходного аудита). **Роль:** `ops+growth`.

**Применимость:** Только после отдельного owner разрешения на выбранную поставку и среды.

**Зависимости:** `R12-Q04`.

**Definition of Done:** Завершено утверждённое окно наблюдения после разрешённого выпуска: retained evidence, adoption/health/support, public artifact/version/catalog readback и доступность rollback. Маркетинговый пилот не является обязательным условием закрытия технического релиза; его запуск отдельно требует M01–M06 и разрешения. Только локальное I3 не закрывает этот slice.

**Редакционное уточнение:** эта формулировка заменяет соответствующий DoD предыдущего аудита; основание — границы и исправления в файле 01. Остальные обязательства ID сохранены в выбранном scope.

**Трассировка:** REL_GATE; MKT_STAGE; [AUD-S01], [AUD-S11].

## Происхождение и исполнение

Этот документ не пересчитывает заново все 378 старых требований. Они сохраняются в canonical ledger репозитория; соответствие и изменения записываются в G01/G03. Полная карта файлов и SHA-256 находится в [11_SOURCE_CROSSWALK.md](11_SOURCE_CROSSWALK.md).

Исходные типы 83 задач: 48 проверок, 14 интеграций, 9 оптимизаций, 7 исправлений, 5 решений. Тип «исправление» не освобождает от reproduction; тип «проверка» не означает, что код отсутствует.

## Общие определения ссылок

[AUD-S01]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/OWNER-FREEZE-2026-09-05.md
[AUD-S02]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/config/cutover-readiness.seed.json
[AUD-S03]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/evidence/013GV-candidate33-bounded-windows-android-runtime/013GV-candidate33-gate-f-decision.json
[AUD-S04]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/INDEX.md
[AUD-S05]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/SOURCE-CROSSWALK.md
[AUD-S06]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/docs/operations/cutover-readiness.md
[AUD-S07]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/shared/tariff-catalog.json
[AUD-S08]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/marketing/src/app/checkout/checkout-client.tsx
[AUD-S09]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/portal_bot/api_payment_routes.py
[AUD-S10]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/portal_bot/admin_v2/security.py
[AUD-S11]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/adminapp/README.md
[AUD-S12]: https://github.com/Kiwunaka/pokrov-core/blob/c1185faa998c69fd5164af415249c96c68ab61bd/config/awg31-capability.json
[AUD-S13]: https://github.com/Kiwunaka/pokrov-core/blob/c1185faa998c69fd5164af415249c96c68ab61bd/engine/sing-box/protocol/awg/contract.go
[AUD-S14]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/apps/android_shell/android/app/src/main/kotlin/space/pokrov/pokrov_android_shell/AndroidCoreEgressProbe.kt
[AUD-S15]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/apps/android_shell/android/app/src/main/kotlin/space/pokrov/pokrov_android_shell/AndroidCoreOperationalEvents.kt
[AUD-S16]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/apps/linux_shell/README.md
[AUD-S17]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/config/release-handoff.seed.json
[AUD-S18]: https://api.github.com/repos/Kiwunaka/POKROV-app/contents/packages/app_shell/lib
[AUD-S19]: https://github.com/Kiwunaka/Pokrov-client/blob/main/README.md
[AUD-W01]: https://docs.amnezia.org/documentation/amnezia-wg/
[AUD-W02]: https://docs.amnezia.org/faq/
[AUD-W03]: https://github.com/amnezia-vpn/amneziawg-go
[AUD-W04]: https://learn.microsoft.com/en-us/windows/release-health/release-information
[AUD-W05]: https://base.garant.ru/12145525/5633a92d35b966c2ba2f1e859e7bdd69/
[AUD-W06]: https://epp.genproc.gov.ru/ru/proc_78/activity/legal-education/explain/otherwise/e8255163/
[GH-AWG]: https://github.com/Kiwunaka/pokrov-core/blob/c1185faa998c69fd5164af415249c96c68ab61bd/config/awg31-capability.json
[GH-AWG-FIX]: https://github.com/amnezia-vpn/amneziawg-go/commit/b5928efb6ca19f0153958460c3d141f04abc5c2e
[GH-MARKETING]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/marketing/next.config.mjs
[WEB-ANDROID]: https://developer.android.com/reference/android/net/VpnService.Builder
[WEB-CODEX-COMMANDS]: https://developers.openai.com/codex/cli/slash-commands
[WEB-CODEX-GOALS]: https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex
[WEB-NEXT]: https://nextjs.org/docs/14/app/building-your-application/deploying/static-exports
[WEB-WIREGUARD]: https://www.wireguard.com/protocol/

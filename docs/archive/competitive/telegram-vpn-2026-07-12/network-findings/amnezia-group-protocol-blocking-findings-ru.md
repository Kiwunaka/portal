# Выгрузка Amnezia VPN (RU): блокировки, протоколы и приоритеты POKROV

**Срез:** 2026-07-12

**Документ:** 2026-07-13

**Статус:** `EXPERIMENTAL / ADVISORY` — исследование, не каноническая продуктовая или эксплуатационная истина POKROV

**Источник:** Telegram Desktop export `ChatExport_2026-07-12/result.json` из публичной группы `Amnezia VPN (RU)`

## Короткий вывод

Нельзя строить POKROV вокруг одного «неблокируемого» протокола. Устойчивость дают:

1. несколько независимых транспортных контуров;
2. разные IP/ASN и RU-мост;
3. управляемые TLS fingerprint, SNI и XHTTP-параметры;
4. проверка реальной передачи данных, а не только DNS/TCP/TLS;
5. автоматический fallback по оператору и типу сбоя.

Главный практический риск — соединение выглядит рабочим, но полезный трафик зависает после небольшого объёма данных. Текущие короткие probes могут показать зелёный статус в этом состоянии.

## Объём и ограничения исследования

- Всего объектов сообщений: **669 326**.
- Текстовых сообщений: **653 265**.
- Период: **2025-03-16 — 2026-07-12**.
- В итог не включены имена участников, connection URLs, IP, ключи и другие сырые параметры подключений.
- Частоты упоминаний использовались только для поиска тем, а не для рейтинга протоколов.

Ограничения:

- это группа Amnezia, поэтому AmneziaWG представлен непропорционально широко;
- сообщения смешивают Premium, self-hosted, клиентские ошибки, DDoS, проблемы хостеров и сетевую фильтрацию;
- длинные технически выглядящие сообщения часто сгенерированы ИИ и не являются доказательством;
- один отчёт пользователя не доказывает общую блокировку протокола;
- июль 2026 года представлен только первыми двенадцатью днями.

## Что подтверждается

### 1. «16 КБ блок» — отдельный механизм, а не смерть конкретного протокола

**Уверенность:** высокая.

Повторяющийся симптом:

- DNS и TCP работают;
- TLS или VPN-handshake проходит;
- клиент показывает подключение;
- первые данные передаются;
- затем поток зависает или уходит в timeout.

В выгрузке этот механизм обсуждают с июня 2025 года применительно к разным хостерам, ASN и протоколам. Независимые измерения Cloudflare зафиксировали ограничение после первых 16 КБ, reset/timeout и влияние на TCP, TLS и QUIC. Сообщество net4people описывает варианты фильтра по объёму или числу пакетов в одной сессии, а также SNI- и CIDR-allowlist.

Практический смысл:

- смена порта, страны, SNI или fingerprint может не помочь, если ограничен IP/ASN;
- обычная TCP-фрагментация не решает лимит всей сессии;
- `packet-up` дробит преимущественно upload и сам по себе не доказывает работоспособность download;
- нужны другой IP/ASN, RU-relay либо режим с доказанной ротацией/разделением соединений;
- probe обязан передать заметный объём данных через реальный транспорт.

Источники:

- [Cloudflare: Russian Internet users are unable to access the open Internet](https://blog.cloudflare.com/russian-internet-users-are-unable-to-access-the-open-internet/)
- [net4people: Russia — new blocking method](https://github.com/net4people/bbs/issues/490)

### 2. Блокируется не «VLESS вообще», а конкретный сетевой профиль

**Уверенность:** высокая.

Для диагностики важна полная комбинация:

`protocol + transport + TLS/REALITY + fingerprint + SNI + endpoint + carrier`

Например:

- `VLESS + RAW + REALITY + Firefox`;
- `VLESS + XHTTP + TLS + Firefox`;
- `VLESS + gRPC + TLS`;
- один и тот же профиль через зарубежный IP или RU-мост.

REALITY маскирует TLS-handshake, но не отменяет анализ последующего трафика, блокировку IP/ASN или лимит сессии. Поэтому фраза «VLESS работает» без полного профиля мало что значит.

Источники:

- [Project X: Transport Configuration](https://xtls.github.io/en/config/transport.html)
- [Project X: REALITY](https://xtls.github.io/en/config/transports/reality.html)

### 3. TLS fingerprint, SNI и транспорт реально меняют результат

**Уверенность:** высокая для отдельных режимов блокировки, не универсальная.

5 июня 2026 года в выгрузке есть воспроизводимая ветка:

- Xray перестал работать у части клиентов;
- предложена смена uTLS fingerprint `chrome -> firefox`;
- пользователь сразу подтвердил восстановление;
- позже тот же workaround помог в другой ветке.

В июле на утверждение «VLESS TCP полностью заблокирован» отвечают сменой fingerprint и переходом на XHTTP. Одновременно есть кейсы, где смена SNI и fingerprint не помогает из-за другого класса фильтра.

Вывод: fingerprint должен быть управляемой rollout-переменной, а не вечной константой. Нельзя считать Firefox или randomized универсальным решением без RU-теста.

Источник: [Project X: TLS ClientHello fingerprints](https://xtls.github.io/en/config/transports/tls.html)

### 4. Оператор, регион и тип доступа важнее общего рейтинга протоколов

**Уверенность:** высокая.

Один профиль может:

- работать на проводном интернете и не работать на LTE;
- работать на одном мобильном операторе и зависать на другом;
- работать через один endpoint и падать через другой endpoint того же сервиса;
- временно оживать после переподключения из-за непостоянного фильтра.

Следствие: нужны отдельные `current-origin`, `brain-origin` и `RU-origin` проверки, а внутри RU — по возможности несколько операторов и разделение mobile/wired. Один зелёный RU-host не доказывает доступность по стране.

### 5. «Подключено, но интернета нет» часто не является блокировкой транспорта

**Уверенность:** высокая.

Выгрузка регулярно показывает другие причины:

- DNS policy или DNS resolver;
- IPv4/IPv6 и маршрутизация;
- несовместимость клиента и серверной реализации;
- ошибка конкретной версии приложения или ОС;
- падение API/Premium;
- DDoS или проблема хостера;
- endpoint/IP throttling.

Статус подключения и ping недостаточны. Диагностика должна разделять как минимум:

1. DNS;
2. TCP;
3. TLS/ClientHello;
4. handshake транспорта;
5. передачу полезной нагрузки;
6. маршрутизацию и DNS внутри туннеля;
7. управляющий API и доступность конфигурации.

### 6. UDP и TCP нужны одновременно

**Уверенность:** средняя для выбора конкретного UDP-протокола, высокая для диверсификации.

AmneziaWG 2.0 усложняет DPI-классификацию за счёт динамических заголовков, padding и мимикрии под QUIC, DNS и SIP. Но он остаётся UDP-транспортом и не спасает при фильтрации UDP или endpoint.

Практическая схема:

- основной TCP/TLS-контур: REALITY/RAW или XHTTP;
- отдельный UDP-контур: Hysteria2 или экспериментальный AWG2;
- RU-мост для SNI/CIDR allowlist и ограниченных зарубежных ASN;
- разные IP/ASN, иначе несколько протоколов падают вместе.

Источник: [AmneziaWG 2.0](https://docs.amnezia.org/documentation/amnezia-wg/)

### 7. Active probing не выглядит главным текущим риском

**Уверенность:** средняя.

В корпусе найдено только 26 сообщений об active probing от 18 авторов. Большинство — теория или пересказ. REALITY и корректный fallback всё равно должны безопасно отвечать на невалидные подключения, но строить основной roadmap вокруг active probing не стоит. Field evidence сильнее у SNI/IP/ASN, TLS fingerprint, объёмных лимитов, DNS и операторских различий.

## Что уже правильно в POKROV

- Базовые VLESS-профили используют Firefox fingerprint.
- Есть transport catalog с `legacy_reality_fallback`, `grpc_443_primary`, `reserve_xhttp_cdn` и `operator_lab`.
- Есть carrier/cohort overrides и отдельная DNS policy.
- RU bridge выделен в отдельный профиль и не смешан с обычным node pool.
- Мониторинг уже различает DNS, TCP и TLS, а документация запрещает считать ping доказательством доступности.

Текущие владельцы:

- [архитектура transport rollout](../../../../architecture/system-overview.md)
- [deployment и transport profiles](../../../../operations/deployment-and-access.md)
- [мониторинг и RU-origin](../../../../operations/monitoring-and-visibility.md)

## Найденные разрывы в текущем коде

### Разрыв 1. `xhttp_alive` не доказывает работу XHTTP

В [RU probe runner](../../../../../scripts/ru_probe_runner.py):

- reserve XHTTP создаётся с `include_http=false`;
- обычный HTTP probe использует `HEAD` и не читает заметный body;
- `xhttp_alive` строится из общего `ok`, фактически после TCP/TLS;
- реальный VLESS/XHTTP handshake и передача данных не выполняются.

Следствие: при 16-КБ фильтре probe может быть зелёным, а пользовательский трафик — мёртвым.

### Разрыв 2. `hysteria_alive` может быть ложноположительным

UDP probe отправляет один байт. Timeout ожидания ответа сохраняет `udp_ok=true` с пометкой `sent_no_response`. Это доказывает только локальную возможность вызвать `send`, но не доступность Hysteria server или прохождение UDP обратно.

### Разрыв 3. Reserve XHTTP не получает fingerprint и mode из профиля

В [`_xray_multi_node_config`](../../../../../portal_bot/api.py) в `tlsSettings` передаётся `serverName`, но не `fingerprint`. По документации Xray применяется default `chrome`. В `xhttpSettings` передаётся только path, без явного mode/extra.

Это расходится с transport profile, где заявлен Firefox fingerprint.

### Разрыв 4. RU bridge и старый XHTTP canary жёстко используют Chrome

- [network rollout](../../../../../portal_bot/network_rollout.py) задаёт RU bridge fingerprint `chrome`;
- [mini canary stack](../../../../../scripts/remote_install_mini_canary_stack.py) задаёт `mode=packet-up`, но client link также содержит `fp=chrome`.

Chrome не обязательно плох всегда, но он должен переключаться через rollout и проверяться текущим RU evidence.

### Разрыв 5. `grpc_443_primary` запланирован как primary без свежего сравнения с XHTTP

Текущая документация Project X рекомендует переходить с gRPC на XHTTP из-за более гибкой маскировки, XMUX и риска active probing у gRPC.

Источник: [Project X: gRPC](https://xtls.github.io/en/config/transports/grpc.html)

Это не основание немедленно удалить gRPC. Это основание остановить его массовое продвижение до head-to-head RU canary.

## Что надо сделать

| Приоритет | Работа | Критерий готовности |
| --- | --- | --- |
| `P0` | Сделать честный end-to-end RU probe каждого транспорта | Probe поднимает реальный профиль, скачивает минимум 64–256 КБ, проверяет byte count/hash и повторяет тест несколько раз |
| `P0` | Убрать ложные `xhttp_alive` и `hysteria_alive` | XHTTP считается живым только после protocol handshake и payload transfer; Hysteria — только после валидного ответа сервера и передачи данных |
| `P0` | Передавать fingerprint в Xray reserve config | Rendered `tlsSettings.fingerprint` совпадает с transport profile и покрыт тестом |
| `P0` | Сделать XHTTP mode/extra частью transport profile | Mode и параметры XMUX/connection rotation явно рендерятся; default не зависит от неявного поведения core |
| `P0` | Сделать fingerprint RU bridge rollout-параметром | Firefox/Chrome и допустимые canary-варианты переключаются без новой сборки и отражаются в profile revision |
| `P0` | Ввести классификацию полевого сбоя | Отдельные причины: `dns`, `tcp`, `tls_clienthello`, `transport_handshake`, `payload_stall`, `routing`, `control_plane`, `provider_incident` |
| `P1` | Провести RU A/B: Reality/RAW, gRPC, XHTTP | Есть одинаковый payload test по нескольким RU-origin, mobile/wired и операторам; решение привязано к evidence |
| `P1` | Проверить XHTTP против объёмного лимита | Проверен download больше 16/64/256 КБ; `packet-up` не принимается за доказательство без downlink test |
| `P1` | Держать независимый UDP fallback | Hysteria2 или AWG2 проходит реальный двусторонний payload test и использует отдельный failure domain |
| `P1` | Добавить автоматический fallback в клиент | Клиент меняет профиль по классу ошибки, а не по одному timeout; причина видна оператору и поддержке |
| `P2` | Автоматизировать SNI/fingerprint canary | Ротация выполняется ограниченной когортой, имеет rollback и не создаёт публичных readiness-заявлений без RU evidence |

## Рекомендуемый порядок

1. Исправить probes и убрать ложные зелёные статусы.
2. Исправить рендер fingerprint/XHTTP mode.
3. Запустить малую RU canary по одинаковому payload-сценарию.
4. Сравнить Reality/RAW, gRPC и XHTTP.
5. Добавить независимый UDP-контур.
6. Подключить автоматический fallback только после накопления полевых данных.

Без первого шага любые дальнейшие решения будут приниматься по неверной телеметрии.

## Что не надо делать

- Не объявлять протокол заблокированным по одному оператору или одному endpoint.
- Не менять глобально fingerprint по одному сообщению из группы.
- Не считать `TCP connect`, TLS handshake, ping или статус «подключено» доказательством работоспособности.
- Не считать `packet-up` автоматическим обходом downlink-лимита.
- Не смешивать Premium outage, DDoS, ошибку клиента и DPI в один incident type.
- Не добавлять очередной протокол на тот же IP/ASN и не называть это независимым fallback.
- Не делать public/RU-readiness выводы без текущего payload evidence для точного кандидата и origin.

## Решение на текущий момент

Архитектурное направление POKROV правильное: transport profiles, carrier overrides, RU bridge и Firefox baseline уже заложены. Менять весь стек не требуется.

Нужны три ближайших результата:

1. честная проверка полезной нагрузки из RU;
2. управляемые fingerprint и XHTTP settings во всех render paths;
3. evidence-backed выбор между gRPC и XHTTP.

До выполнения этих пунктов статус протокольной устойчивости: **не доказан текущим RU payload evidence**.

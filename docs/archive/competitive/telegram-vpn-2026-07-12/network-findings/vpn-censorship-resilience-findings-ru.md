# Устойчивость VPN к блокировкам: сводные выводы Amnezia и ntc.party

**Дата:** 2026-07-13

**Статус:** `EXPERIMENTAL / ADVISORY` — внешнее исследование, не каноническая продуктовая или эксплуатационная истина POKROV

**Назначение:** единая точка входа для решений по транспортам, RU-мостам, probes и fallback

## Решение в одном абзаце

POKROV нельзя строить вокруг одного «неблокируемого» протокола. Нужны несколько независимых транспортных и сетевых контуров, проверяемых настоящей передачей данных из разных RU-origin. Базовая схема: быстрый TCP-контур `VLESS + REALITY + RAW`, кандидат на основной маскируемый TCP-контур `VLESS + XHTTP`, gRPC как дополнительный canary/fallback, отдельный UDP-контур Hysteria2 или AWG2 и пул RU-мостов в разных ASN. До исправления текущих probes протокольная устойчивость не доказана.

## Источники и границы

Сводка объединяет два исследования:

- [Amnezia VPN (RU): блокировки, протоколы и приоритеты POKROV](amnezia-group-protocol-blocking-findings-ru.md) — 653 265 текстовых сообщений за период 2025-03-16 — 2026-07-12;
- [ntc.party: блокировки, протоколы и практические выводы](ntc-party-censorship-findings-ru.md) — 4 213 сообщений в 127 активных темах за последние три месяца, плюс стартовые сообщения и важный предшествующий контекст.

Оба источника являются полевыми наблюдениями, а не контролируемым экспериментом. В них смешиваются:

- ТСПУ и операторская фильтрация;
- блокировки IP, подсетей и ASN;
- проблемы хостеров, CDN и маршрутов;
- ошибки клиентов, DNS и конфигураций;
- DDoS и control-plane outages;
- догадки участников и незавершённая диагностика.

В документ не включены имена участников, IP, connection URL, ключи и полные конфигурации.

## Главная модель

Блокируется не название протокола. Результат задаёт полный профиль:

`оператор + регион + mobile/wired + source IP + endpoint IP/ASN + TCP/UDP + protocol + transport + TLS/REALITY + fingerprint + SNI + число соединений + объём`

Фраза «VLESS работает» без этих параметров ничего не доказывает.

### Основные классы отказа

| Verdict | Что наблюдается | Возможная причина |
| --- | --- | --- |
| `dns_fail` | Домен не резолвится или выдаётся другой адрес | Перехват DNS, блок DoH/DoT, ошибка policy |
| `syn_drop` | TCP handshake не начинается | IP/CIDR/ASN или портовый фильтр |
| `tls_drop` | `ClientHello` отправлен, ответа нет | SNI/fingerprint/TLS-фильтр |
| `tls_rst` | После `ClientHello` приходит reset | Активный TLS/DPI verdict |
| `transport_handshake_fail` | TLS жив, профиль не поднимается | Транспорт, core/version, server config |
| `payload_cutoff` | Первые данные проходят, затем timeout | «16 КБ»/packet-count/session filter |
| `dns_inside_tunnel` | Туннель поднят, сайты не открываются | Resolver или DNS routing внутри туннеля |
| `routing_fail` | Часть направлений не работает | IPv4/IPv6, split tunnel, route policy |
| `control_plane_fail` | Клиент не получает профиль/API | API, хостер, CDN, DDoS, bootstrap |
| `provider_incident` | Не работает и контрольный трафик | Хостер, маршрут или endpoint outage |

Автоматический fallback должен опираться на этот verdict, а не на общий timeout.

## Что подтверждается обоими источниками

### 1. Соединение может быть зелёным, а полезный трафик — мёртвым

Повторяющийся сценарий:

1. DNS работает.
2. TCP и TLS поднимаются.
3. Клиент показывает «подключено».
4. Проходит небольшой объём данных.
5. Download зависает или соединение сбрасывается.

«16 КБ» — условное название. Реальное окно плавает примерно в диапазоне 14–34 КБ или зависит от числа пакетов.

Практический вывод: `ping`, `TCP connect`, TLS handshake, `HEAD` и короткий HTTP-ответ не являются доказательством доступности VPN.

### 2. Probe должен повторять поведение клиента

Короткие проверки дают ложные результаты, когда:

- `curl` работает, а Chromium создаёт другую картину соединений;
- `HEAD` проходит, а body блокируется;
- XHTTP transport вообще не запускается;
- UDP datagram отправлен, но ответ не получен;
- домен резолвится в разные IP одного CDN;
- сам probe попадает под rate limit цели.

Минимальный честный probe:

- использует тот же core и rendered profile, что клиент;
- фиксирует точный endpoint IP и ASN;
- проверяет ступени 16/64/256 КБ;
- сверяет byte count и hash;
- отдельно проверяет upload;
- повторяет реальную concurrency/XMUX policy;
- проверяет DNS и маршрутизацию внутри туннеля;
- имеет контрольный endpoint без предполагаемой фильтрации.

### 3. Оператор, регион и тип доступа меняют результат

Один профиль может:

- работать на домашнем интернете и не работать на LTE;
- работать у одного мобильного оператора и падать у другого;
- работать в одном городе и не работать у того же оператора в другом;
- работать через один IP CDN и падать через соседний;
- временно оживать после смены source IP.

Один зелёный RU-host не доказывает доступность в России.

### 4. Endpoint diversity важнее количества протоколов

Разные протоколы на одном IP/ASN остаются одной точкой отказа. При CIDR/ASN-фильтре одновременно падают RAW, XHTTP, gRPC, WireGuard и обычный HTTPS до того же направления.

Независимый fallback должен менять хотя бы один failure domain:

- endpoint IP;
- ASN или хостинг-провайдера;
- маршрут;
- RU bridge;
- TCP/UDP;
- TLS profile и transport.

### 5. SNI и fingerprint полезны, но не универсальны

Смена `chrome → firefox`, Safari или randomized иногда восстанавливает доступ. В других случаях она не помогает, потому что ограничен destination IP/ASN или весь payload.

Выводы:

- Firefox — разумный текущий baseline, не вечная константа;
- fingerprint должен быть rollout-переменной;
- default Xray `chrome` нельзя оставлять неявно;
- один «белый SNI» не работает для всех операторов и ASN;
- смена SNI без смены endpoint не решает жёсткий destination filter.

### 6. TCP и UDP нужны одновременно

TCP/TLS устойчив там, где режется UDP. QUIC/Hysteria/AWG могут работать там, где фильтруются TCP/TLS-профили. Обратная ситуация также встречается.

Независимый UDP fallback нужен, но должен:

- использовать отдельный endpoint failure domain;
- проходить двусторонний protocol handshake;
- передавать реальный payload;
- проверяться по той же RU-origin matrix.

### 7. DNS — самостоятельная причина инцидента

Наблюдаются:

- блок TCP/53, DoT/853 или DoH/443 при работающем UDP/53;
- работа HTTP/3 DoH при неработающем TCP DoH;
- утечки через системный resolver Windows;
- direct DNS при ожидаемом proxy detour;
- разные IP ответа CDN с разным режимом фильтрации;
- IPv4/IPv6 расхождения.

Transport health и DNS health нельзя объединять в один флаг.

### 8. Частые probes могут менять измеряемое состояние

На ntc.party несколько участников наблюдали временный фильтр после серии неудачных запросов. Состояние снималось через несколько минут или после смены source IP. Точная причина не доказана: это может быть stateful DPI, CDN rate limiting или их сочетание.

Мониторинг должен иметь:

- jitter;
- cooldown;
- burst limit;
- контрольную цель;
- отметку `possible_self_trigger`;
- раздельные source origins.

### 9. Active probing пока не главный практический риск

В обоих корпусах сильнее подтверждены:

- IP/CIDR/ASN-фильтры;
- SNI и ClientHello fingerprint;
- session/payload cutoff;
- DNS;
- операторские различия;
- временные trigger-состояния.

REALITY и безопасный fallback на невалидное подключение всё равно нужны. Но roadmap не следует строить вокруг active probing до появления текущего RU evidence.

### 10. App-level VPN detection не является сетевой блокировкой

Некоторые приложения видят TUN-интерфейс, системный proxy или датацентровый egress IP. Смена XHTTP на gRPC это не исправляет.

Для клиента это отдельная задача:

- per-app direct/exclude routing;
- корректный split tunnel;
- отдельная DNS policy для direct-приложений;
- отсутствие обещаний, что транспорт скроет сам факт локального VPN.

## Роль каждого направления

| Направление | Роль | Что полезно | Главный риск |
| --- | --- | --- | --- |
| `VLESS + REALITY + RAW/Vision` | Быстрый TCP baseline | Производительность и зрелая поддержка | Traffic pattern, fingerprint, IP/ASN cutoff |
| `VLESS + XHTTP` | Кандидат на маскируемый TCP primary | HTTP semantics, XMUX, управление соединениями | Неверный mode/extra, CDN compatibility, тот же endpoint |
| `VLESS + gRPC` | TCP fallback/canary | Независимый HTTP/2 transport | Не иммунен к ClientHello/RST и active probing |
| Hysteria2 | UDP fallback | QUIC и независимость от TCP | На части операторов QUIC/UDP режется полностью |
| AWG2 | UDP fallback/lab | Обфускация WireGuard, padding и protocol mimicry | Endpoint/UDP filter, неодинаковая поддержка клиентов |
| RU bridge | Whitelist и проблемные зарубежные ASN | Вход через доступный российский контур | Один bridge/IP/ASN быстро становится SPOF |
| WARP | Второй hop/bootstrap | Egress privacy и дополнительный маршрут | Cloudflare ASN сам фильтруется |
| TURN/WebRTC | `P2 LAB` для whitelist | Может проходить разрешённый media relay | Низкая скорость, нестабильные клиенты, правила платформ |
| DNS tunnels | Аварийный bootstrap | Получение конфигурации и низкоскоростная связь | Rate limits и очень низкая пропускная способность |
| zapret2/ByeDPI | Локальный bootstrap | Подбор anti-DPI для control plane | Привязка к оператору, ОС, цели и сетевому стеку |

## Целевая транспортная схема

```text
Client
├─ TCP candidate primary: VLESS + XHTTP + TLS/REALITY
├─ TCP fast fallback: VLESS + RAW + REALITY
├─ TCP alternate: VLESS + gRPC
├─ UDP fallback: Hysteria2 or AWG2
└─ Whitelist path: RU bridge pool
   └─ independent foreign exit pool
```

Обязательные свойства:

- primary и fallback не делят один ASN;
- RU bridge pool содержит несколько независимых провайдеров;
- fingerprint, XHTTP mode и XMUX входят в profile revision;
- клиент получает несколько профилей заранее;
- fallback выбирается по классу ошибки;
- решение и причина видны оператору и поддержке.

## Что уже правильно заложено в POKROV

- Есть transport catalog и разные роли профилей.
- Есть carrier/cohort overrides.
- RU bridge выделен отдельно от обычного node pool.
- Есть отдельная DNS policy.
- Мониторинг уже различает DNS, TCP и TLS.
- Документация не считает ping доказательством доступности.

Канонические владельцы:

- [архитектура](../../../../architecture/system-overview.md);
- [deployment и transport profiles](../../../../operations/deployment-and-access.md);
- [мониторинг и origins](../../../../operations/monitoring-and-visibility.md);
- [RU-origin probe handoff](../../../../operations/ru-origin-probe-handoff.md).

## Подтверждённые разрывы в текущей реализации

### `xhttp_alive` может быть ложнозелёным

В [RU probe runner](../../../../../scripts/ru_probe_runner.py) reserve XHTTP не проходит реальный VLESS/XHTTP handshake и payload. Обычный HTTP probe использует короткую проверку, недостаточную для session cutoff.

### `hysteria_alive` может быть ложнозелёным

UDP probe считает отправку datagram успехом даже без валидного ответа. Это не доказывает доступность Hysteria.

### XHTTP profile рендерится не полностью

В [API renderer](../../../../../portal_bot/api.py) XHTTP reserve не получает явные fingerprint, mode и XMUX/extra из transport profile. При отсутствии fingerprint Xray использует default `chrome`.

### RU bridge и старый canary жёстко привязаны к Chrome

- [network rollout](../../../../../portal_bot/network_rollout.py);
- [mini canary stack](../../../../../scripts/remote_install_mini_canary_stack.py).

Fingerprint должен быть частью rollout revision, а не жёсткой константой.

### gRPC нельзя назначать primary без A/B

Нужен одинаковый RU payload-тест для RAW, XHTTP и gRPC. Текущие внешние данные не дают права объявить один из них общим победителем.

## Единый план работ

### P0 — исправить доказательство работоспособности

| Работа | Критерий готовности |
| --- | --- |
| Реальный transport probe | Поднимается точный rendered profile; download проходит 16/64/256 КБ; сверяются byte count и hash |
| Честный upload test | Через тот же профиль отправляется известный payload и подтверждается на сервере |
| Убрать ложные `xhttp_alive` | Успех только после VLESS/XHTTP handshake и payload transfer |
| Убрать ложные `hysteria_alive` | Успех только после валидного двустороннего ответа и payload transfer |
| Фазовый verdict | Отдельные `dns`, `syn`, `tls`, `transport`, `payload`, `routing`, `control_plane`, `provider` |
| Evidence identity | Сохраняются profile revision, endpoint IP/ASN, SNI, fingerprint, carrier, region, access type и время |
| Probe safety | Jitter, cooldown, burst limit, control endpoint и `possible_self_trigger` |
| Полный XHTTP render | Fingerprint, mode, path, XMUX и reuse/concurrency берутся из transport profile |
| Fingerprint rollout | Firefox/Chrome/randomized переключаются ограниченной когортой с rollback |

### P1 — доказать независимость контуров

| Работа | Критерий готовности |
| --- | --- |
| RU-origin matrix | Несколько mobile/wired операторов и регионов; результаты не смешиваются |
| RU bridge pool | Минимум два независимых RU ASN/провайдера, проверенных в whitelist-state |
| Foreign endpoint pool | Primary и fallback не делят один зарубежный ASN/CDN |
| RAW/XHTTP/gRPC A/B | Одинаковый 256 КБ payload, одинаковые origins и несколько повторов |
| Независимый UDP contour | Hysteria2 или AWG2 проходит двусторонний тест на отдельном endpoint |
| DNS gate | IPv4/IPv6, direct/proxy, system resolver, DoH/DoT/UDP и фактический egress resolver |
| Automatic fallback | Клиент меняет профиль по verdict и сохраняет причину решения |
| REALITY decoy test | Невалидный client проверяет фактический source IP на decoy и соответствие egress policy |

### P2 — лабораторные аварийные каналы

- TURN/WebRTC relay для whitelist;
- DNS tunnel только для bootstrap/config recovery;
- локальный zapret2/ByeDPI для восстановления control plane;
- настоящий Browser Dialer после стабилизации реализации;
- per-app direct routing для приложений, реагирующих на TUN или foreign/DC egress.

До массового включения нужны проверки лицензий, правил платформ, abuse-рисков, производительности, батареи и rollback.

## Порядок выполнения

1. Исправить XHTTP и UDP probes.
2. Добавить payload/hash и фазовые verdicts.
3. Исправить render fingerprint, XHTTP mode и XMUX.
4. Ввести evidence identity и безопасную частоту probes.
5. Собрать RU-origin matrix.
6. Провести RAW/XHTTP/gRPC A/B.
7. Проверить независимый UDP-контур.
8. Расширить RU bridge и foreign endpoint pools.
9. Включать automatic fallback только после накопления полевых данных.

Первые четыре шага обязательны. Без них дальнейшее сравнение транспортов будет опираться на ложную телеметрию.

## Что не надо делать

- Не объявлять протокол заблокированным по одному оператору или endpoint.
- Не объявлять XHTTP заблокированным по одной незавершённой ветке.
- Не считать Firefox вечным безопасным fingerprint.
- Не искать один универсальный SNI.
- Не считать несколько протоколов на одном IP независимыми fallback.
- Не считать `HEAD`, ping, TLS handshake или 20 КБ ответа успешным payload proof.
- Не считать `packet-up` доказательством живого download.
- Не запускать частый burst-probe по одному endpoint.
- Не смешивать DPI, DNS leak, CDN rate limit, DDoS и outage хостера.
- Не использовать публичный TURN/STUN для массового трафика без разрешения владельца.
- Не переносить результат одного города и оператора на страну.
- Не заявлять RU readiness без текущего evidence для точного кандидата и origin.

## Текущий статус решения

Архитектурное направление POKROV менять не требуется. Transport profiles, carrier overrides, DNS policy и RU bridge уже создают нужную основу.

Ближайший обязательный результат — не новый протокол, а честная телеметрия:

1. реальный 256 КБ payload probe;
2. точная классификация сбоя;
3. управляемые fingerprint и XHTTP settings;
4. evidence по оператору, IP и ASN;
5. независимые RU и зарубежные failure domains.

До выполнения P0 статус транспортной устойчивости POKROV: **не доказан текущим RU payload evidence**.

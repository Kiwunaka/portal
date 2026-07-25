# Полнота источников и разбор комментариев

Статус: `EXPERIMENTAL`, research evidence

Дата сбора: `2026-07-22`

## Что значит «изучены все комментарии»

Скрипт [`scripts/research_censorship_corpus.py`](../../../scripts/research_censorship_corpus.py)
обошел все страницы семи указанных Discourse-категорий, затем запросил полный
`post_stream` каждого найденного topic и добрал chunked posts по ID. Для Habr
собраны все комментарии семи уникальных статей; повтор ссылки `1021160` учтен один
раз. Тексты нормализованы для thematic review, авторы не сохраняются, proxy URLs
редактируются.

Итог:

| Корпус | Topics/articles | Visible posts/comments | Missing | Errors |
| --- | ---: | ---: | ---: | ---: |
| NTC Discourse | 1 244 topics | 40 031 posts, включая OP и ответы | 0 | 0 |
| Habr | 7 unique articles, 8 input references | 1 811 comments | 0 | 0 |

Это полное покрытие видимого API-корпуса на момент среза, а не утверждение, что
удаленные, скрытые или добавленные после среза сообщения были доступны. Две Habr
статьи с ограниченным API body были дополнительно прочитаны через browser surface;
их комментарии вошли в API-корпус полностью.

Raw corpus намеренно не коммитится: он объемный, быстро устаревает и содержит
публичные пользовательские сообщения. Локальная evidence-копия на момент анализа:

- Discourse JSONL SHA-256:
  `086eb50bfbe0ddecb77a2c274033cb7ac03beb41fec862bdce9d40a38b4c60da`;
- Habr JSONL SHA-256:
  `6117e622b157e50dacb4823455419bbb7787ebc956b5cb8fd5fbda9c97ea0e00`.

Воспроизведение в отдельный локальный каталог:

```powershell
python -B scripts/research_censorship_corpus.py `
  --output-dir C:\Temp\pokrov-censorship-corpus
```

## Покрытие категорий NTC

| Входная категория | Topics | Visible posts |
| --- | ---: | ---: |
| [Manuals](https://ntc.rkn.quest/c/manuals/42) | 27 | 3 296 |
| [Cloak](https://ntc.rkn.quest/c/community-software/cloak/21) | 2 | 7 |
| [GoodbyeDPI](https://ntc.rkn.quest/c/community-software/goodbyedpi/8) | 331 | 11 020 |
| [Runet censorship bypass extension](https://ntc.rkn.quest/c/community-software/runet-censorship-bypass-extension/7) | 34 | 424 |
| [Tools for researchers and developers](https://ntc.rkn.quest/c/censorship-circumvention-software/tools-for-researchers-and-developers/26) | 24 | 99 |
| [Tunneling software](https://ntc.rkn.quest/c/censorship-circumvention-software/tunneling-software/24) | 282 | 4 144 |
| [Russia](https://ntc.rkn.quest/c/internet-censorship-all-around-the-world/russia/12) | 544 | 21 041 |

Два явно указанных topic уже находились в категории Russia и не были посчитаны
повторно.

## Все входные ссылки

| № | Источник | Как учтен |
| ---: | --- | --- |
| 1 | [Naive proxy — пока лучший вариант](https://ntc.rkn.quest/t/naive-proxy-%D0%BF%D0%BE%D0%BA%D0%B0-%D0%BB%D1%83%D1%87%D1%88%D0%B8%D0%B9-%D0%B2%D0%B0%D1%80%D0%B8%D0%B0%D0%BD%D1%82/23843) | Все 59 visible posts |
| 2 | [Manuals](https://ntc.rkn.quest/c/manuals/42) | Все страницы/topics/posts |
| 3 | [Cloak](https://ntc.rkn.quest/c/community-software/cloak/21) | Все страницы/topics/posts |
| 4 | [GoodbyeDPI](https://ntc.rkn.quest/c/community-software/goodbyedpi/8) | Все страницы/topics/posts |
| 5 | [Runet censorship bypass extension](https://ntc.rkn.quest/c/community-software/runet-censorship-bypass-extension/7) | Все страницы/topics/posts |
| 6 | [Research/developer tools](https://ntc.rkn.quest/c/censorship-circumvention-software/tools-for-researchers-and-developers/26) | Все страницы/topics/posts |
| 7 | [Tunneling software](https://ntc.rkn.quest/c/censorship-circumvention-software/tunneling-software/24) | Все страницы/topics/posts |
| 8 | [Russia](https://ntc.rkn.quest/c/internet-censorship-all-around-the-world/russia/12) | Все страницы/topics/posts |
| 9 | [Habr 985674](https://habr.com/ru/articles/985674/) | Article + 267 comments |
| 10 | [Habr 1021160](https://habr.com/ru/articles/1021160/) | Article + 225 comments |
| 11 | [Habr 1021160, duplicate](https://habr.com/ru/articles/1021160/) | Deduplicated |
| 12 | [DPI IS ALL YOU NEED](https://habr.com/ru/articles/1014038/) | Article + 83 comments |
| 13 | [О белых списках и способах обхода](https://habr.com/ru/articles/1027276/) | Article + 249 comments |
| 14 | [Шесть proxy на VPS](https://habr.com/ru/articles/1055176/) | Article + 54 comments |
| 15 | [«Критическая уязвимость VLESS-клиентов»](https://habr.com/ru/articles/1020080/) | Article + 886 comments |
| 16 | [Все, что работает при БС/L3, post 60](https://ntc.rkn.quest/t/%D0%B2%D1%81%D0%B5-%D1%87%D1%82%D0%BE-%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D0%B0%D0%B5%D1%82-%D0%BF%D1%80%D0%B8-%D0%B1%D1%81l3-%D0%B1%D0%BB%D0%BE%D0%BA/23018/60) | Все 63 visible posts, не только post 60 |
| 17 | [Свой VPN на Rust](https://habr.com/ru/articles/1052536/) | Article + 47 comments |

## High-signal выводы из NTC

### Naive topic 23843

Главный полезный сигнал: у части участников Naive проходил там, где конкретные
VLESS/REALITY/XHTTP configurations не проходили. Но комментарии не подтверждают
тезис «Naive всегда лучший»:

- часть отказов REALITY была похожа на недоступный donor/SNI, а не detection всего
  протокола;
- Chromium stack и H2 multiplex/padding дают другой traffic shape, но сам browser
  fingerprint тоже может фильтроваться;
- TLS-in-TLS, throughput, память и параллельные connections остаются рисками;
- в июльских ответах есть instability Naive over QUIC;
- обсуждается исправление padding memory leak, значит минимальная версия и soak
  обязательны.

Вывод для POKROV: Naive H2 — первый новый TCP canary после core migration, не
замена всего стека. Начинать с одного tunnel connection.

### L3/whitelist topic 23018, включая post 60

Post 60 сообщает, что whitelist активен и Yandex доступен. Следующие ответы
уточняют слабость измерения: проверялся в основном TCP handshake на небольшой
выборке адресов, с коротким timeout и на одном региональном контуре. В topic есть
противоположные результаты по Yandex/VK, операторам и времени.

Вывод: static «Yandex разрешен» не является архитектурным фактом. Нужны dynamic
eligibility, payload proof и multi-ASN bridge pool.

### Другие важные topics

| Topic | Posts | Что дает решению |
| --- | ---: | --- |
| [16061 — частичная блокировка TLS/REALITY](https://ntc.rkn.quest/t/16061) | 1 239 | «VLESS заблокирован» часто смешивает TLS, SNI, hoster/ASN, fingerprint и provider-specific failures; multihop иногда меняет исход |
| [25362 — XHTTP сразу везде?](https://ntc.rkn.quest/t/25362) | 37 | Есть реальные failures, но часть связана с version/config/Cloudflare/TLD mismatch; XHTTP не универсальный rescue |
| [22516 — 16 KiB blocking](https://ntc.rkn.quest/t/22516) | 173 | Порог плавает примерно в диапазоне, зависит от ASN/SNI/оператора; handshake-only probe недостаточен |
| [23690 — обнаружение туннелей и routing](https://ntc.rkn.quest/t/23690) | 213 | Полезны независимые ingress/egress, несколько outbound/SNI и split routing; гипотезы об app-assisted detection остаются гипотезами |
| [24125 — sing-box vs Xray](https://ntc.rkn.quest/t/24125) | 30 | Нет одного «швейцарского ножа»: sing-box получил Naive, Xray владеет XHTTP |
| [20340 — Hysteria2/QUIC на Tele2](https://ntc.rkn.quest/t/20340) | 23 | На части путей QUIC не работает полностью, на других позже работает; UDP contour нельзя делать единственным |
| [12977 — Cloak/hoster failures](https://ntc.rkn.quest/t/12977) | 32 | Cloak не дает достаточного преимущества для near-term integration |
| [21884 — обход whitelist](https://ntc.rkn.quest/t/21884) и [24402 — TURN](https://ntc.rkn.quest/t/24402) | 233 + 110 | TURN/service abuse может временно работать, но ломается из-за account/CAPTCHA/service changes; не production dependency |

## High-signal выводы из Habr и комментариев

### 985674

Полезны схемы RU bridge и XHTTP, но рецепты смешаны с опасными universal claims,
агрессивными sysctl и предположением о доступности конкретных российских
площадок. Комментарии прямо оспаривают универсальность и отмечают marketing tone.
Использовать как source of hypotheses, не как runbook.

### 1021160

Полезна четырехслойная идея: несколько независимых transport/infrastructure
failure domains. Особенно важен последующий update самой статьи: автор убрал
Yandex Cloud relay, потому что cloud ASN не равен consumer Yandex ASN. Это прямое
опровержение популярного «бренд в whitelist → весь cloud в whitelist».

### 1014038

Хорошая история и терминология DPI, но мало конкретики для POKROV implementation.
Использовать для shared vocabulary, не для выбора core.

### 1027276

Практический whitelist scan полезен как signal, но выводы строятся в основном на
одном операторе/регионе. Самый ценный комментарий перечисляет multihop,
Cloak/Trojan/Hysteria и другие contours, однако это один operator anecdote.

### 1055176

Интересна скорость развертывания multi-protocol VPS, не качество обхода. Installer
convenience не оправдывает миграцию POKROV control plane.

### 1020080

Заголовок «уязвимы все VLESS-клиенты» шире доказанного. Основной конкретный класс
риска — локальный SOCKS/mixed/API listener без auth в некоторых клиентах.
Комментарии справедливо разделяют TUN-only implementations и клиенты с локальным
proxy. POKROV Android generated config возвращает только TUN и под этот точный
класс не попадает; desktop loopback listeners требуют отдельного исправления.
Более общий вопрос корреляции/обнаружения outbound IP остается measurement task,
а не доказанной общей уязвимостью VLESS.

### 1052536 — «супер интересно»

Самая полезная статья как инженерный postmortem, не как новый POKROV protocol.
Забираем уроки:

- cancellation safety на каждом blocking I/O;
- TUN `O_NONBLOCK` и управляемый lifecycle;
- обязательное восстановление DNS/routes после crash/stop;
- очистка stale sessions;
- безопасные defaults вместо набора флагов;
- multipath и несколько TLS connections могут сами стать detection signal;
- soak и network-handover tests обязательны.

Не забираем собственный TLS-like handshake, custom crypto и новый wire protocol.
Автор сам не позиционирует проект как замену Xray; комментарии дополнительно
предупреждают, что несколько TLS connections к одному host могут выделяться ТСПУ.

Прямое сопоставление с POKROV:

| Урок статьи | Что это значит у нас | Проверка/изменение |
| --- | --- | --- |
| Ручные Kotlin/C# ports протокола расходились с Rust server | Не дублировать core logic в Flutter/Kotlin/Swift/C++; единый libbox core и тонкие platform adapters | Versioned ABI/capabilities; один config validator на всех платформах |
| `select!` отменял наполовину прочитанную TLS record | Host не должен владеть protocol framing; для наших async loops нужны cancellation-safe ownership boundaries | Full-duplex load + cancel/reload test без framing corruption |
| Отсутствующая config section превращалась в тихие нули | Defaults не должны маскировать неполный managed profile | Schema validation, semantic bounds, exact-binary `check config`, fail closed |
| Heartbeat обновлял не тот activity clock | Разделять receive/transmit health, не считать собственный keepalive доказательством живого data path | One-way blackhole и half-open tests |
| Wi-Fi↔LTE оставлял stale session | Stop/reconnect/handover должны закрывать старый runtime и не блокировать новый | Network handover, crash recovery, bounded backoff, newest runtime instance wins |
| Android TUN был nonblocking, `read()==0` приняли за EOF | Наш `VpnService`/PlatformInterface boundary — реальная зона риска при смене libbox | Instrumented zero/no-data vs EOF test на device/emulator |
| Ошибка cancellation создала reconnect busy-loop | Reconnect controller обязан иметь внешний supervisor, jitter и cancellation ownership | CPU/battery test после repeated failures |
| DNS менялся без гарантированного restore | Desktop adapter должен хранить исходное состояние и делать idempotent recovery | Kill-process test с проверкой DNS/routes после restart |
| Multipath дал throughput, но несколько TLS flows меняют shape | Не считать «как браузер» доказательством незаметности | RU-origin comparison: single connection против N, одинаковый payload |

Самый важный архитектурный вывод статьи совпадает с этим research: одно нативное
ядро и тонкие host bindings. У нас таким ядром может оставаться разрешенный
Hiddify v4 поверх sing-box/libbox; новая реализация TLS/AEAD силами POKROV не нужна.

### Проверка текущего Qeli repository

Статья была дополнительно сверена с exact source/history
[`litvinovtd/qeli`](https://github.com/litvinovtd/qeli), а не только с текстом и
комментариями:

- repo создан `2026-06-07`, на срезе latest `v0.7.12` остается pre-release; docs
  называют компоненты beta и обещают первую stable line только с `1.0`;
- из 342 проверенных commits 330 принадлежат основному автору; высокая скорость
  fixes реальна, но bus factor низкий;
- core/server — `AGPL-3.0-only`; client shells MPL не отменяют AGPL obligations
  bundled `libqeli`, dual licensing core не заявлен;
- собственный L4 protocol включает hand-written TLS 1.3 records/handshake,
  certificate borrowing, fake TLS/QUIC, X25519 + ML-KEM-768 и multipath;
- [`SECURITY.md`](https://github.com/litvinovtd/qeli/blob/main/SECURITY.md) прямо
  называет custom TLS крупнейшей attack surface и говорит, что независимого
  внешнего аудита еще не было;
- release/docs с фразой `external audit` описывают review принесенных reports и
  внутренние/multi-agent fix rounds. Это полезная работа, но ее нельзя выдавать за
  опубликованный независимый профессиональный audit;
- recent releases исправляли серьезные flaws: enforcement `allowed_networks`,
  command execution lifecycle hooks, arbitrary file read, parser OOM/DoS,
  CSRF/XSS и silently broken pushed routes;
- статья говорит об одном Rust core, однако exact tree сохраняет часть protocol и
  lifecycle code в Kotlin/C# clients. Centralization пока неполная.

Вердикт не изменился: Qeli — сильный R&D/postmortem и хороший источник failure
tests. Для POKROV shipping core он слишком молод, криптографически амбициозен и
неаудирован. Подробное сравнение Rust engines:
[`core-engine-architecture.md`](core-engine-architecture.md).

## Тематический срез

Числа ниже — posts с совпадением тематических выражений, а не голоса «за» и не
измеренная эффективность.

| Тема | All-time posts / topics | Posts in 2026 |
| --- | ---: | ---: |
| VLESS / REALITY | 1 726 / 339 | 442 |
| XHTTP | 330 / 52 | 213 |
| Naive | 86 / 30 | 69 |
| gRPC | 174 / 40 | 98 |
| Hysteria | 128 / 53 | 61 |
| AmneziaWG | 548 / 97 | 229 |
| WireGuard | 1 312 / 220 | 303 |
| GoodbyeDPI / zapret | 3 260 / 505 | 297 |
| QUIC / HTTP3 | 1 155 / 181 | 189 |
| Whitelist / L3 | 898 / 133 | 439 |
| 16 KiB class | 460 / 80 | 306 |
| RU bridge / chain | 391 / 149 | 184 |
| CDN / fronting | 2 111 / 368 | 537 |
| sing-box | 606 / 177 | 197 |
| Xray | 980 / 239 | 276 |
| Hiddify | 117 / 50 | 15 |
| TLS fingerprints | 955 / 225 | 278 |
| Measurement vocabulary | 3 168 / 550 | 689 |

Низкая частота Hiddify в 2026 — еще одна причина не путать POKROV client с этим
runtime wrapper. Высокая частота темы тоже не является качеством: GoodbyeDPI
доминирует из-за размера своей support-категории.

## Проверенный upstream snapshot

Состояние проверялось по official repositories/releases на дату среза:

| Проект | Проверенная версия/состояние | Роль в решении |
| --- | --- | --- |
| [sing-box](https://github.com/SagerNet/sing-box/releases/tag/v1.13.14) | `v1.13.14`, 2026-06-25 | Direct-core fallback |
| [Hiddify Core](https://github.com/hiddify/hiddify-core/releases/tag/v4.1.0) | `v4.1.0`, 2026-03-05 | Основной migration target; отдельное разрешение `OPERATOR_ATTESTED`, API port обязателен |
| [Xray-core](https://github.com/XTLS/Xray-core/releases/tag/v26.3.27) | `v26.3.27`, 2026-03-27 | Deferred second engine/XHTTP owner |
| [NaiveProxy](https://github.com/klzgrad/naiveproxy/releases/tag/v150.0.7871.63-1) | `v150.0.7871.63-1`, 2026-07-03 | TCP canary technology; prefer sing-box integration |
| [Hysteria](https://github.com/apernet/hysteria/releases/tag/app/v2.10.0) | `app/v2.10.0`, 2026-07-13 | UDP canary |
| [amneziawg-go](https://github.com/amnezia-vpn/amneziawg-go) | Active, no GitHub release object | P2 spike only |
| [Cloak](https://github.com/cbeuw/Cloak/releases/tag/v2.12.0) | `v2.12.0`, 2025-07-23 | Drop from near-term plan |
| [GoodbyeDPI](https://github.com/ValdikSS/GoodbyeDPI/releases/tag/0.2.2) | Latest release `0.2.2`, 2022-03-21 | Not product core |
| [zapret](https://github.com/bol-van/zapret/releases/tag/v72.13) | `v72.13`, 2026-07-21 | Optional local/router recovery |
| [TUIC](https://github.com/tuic-protocol/tuic/releases/tag/tuic-server-1.0.0) | Server release `1.0.0`, 2023-06-08 | Drop from near term |
| [Remnawave](https://github.com/remnawave/panel/releases/tag/2.8.1) | `2.8.1`, 2026-07-13 | No evidence for control-plane migration |
| [3x-ui](https://github.com/MHSanaei/3x-ui/releases/tag/v3.5.0) | `v3.5.0`, 2026-07-12; README says personal-only/no production | Current Xray adapter; decouple from production authority |
| [libXray](https://github.com/XTLS/libXray) | Cross-platform wrapper; API stability не гарантируется, latest-Xray-only | Реальный second-engine path, но только за POKROV adapter |
| [shoes](https://github.com/cfal/shoes/releases/tag/v0.2.7) | Tag `v0.2.7`, source version `0.2.8` | Rust server lab comparator |
| [Qeli](https://github.com/litvinovtd/qeli/releases/tag/v0.7.12) | `v0.7.12` pre-release/beta, 2026-07-21 | R&D only; custom TLS без independent audit |
| [Radiance](https://github.com/getlantern/radiance) | Rolling Lantern client backend | Архитектурный reference: forked sing-box + specialist dialers |

Версия — только freshness signal. Она не доказывает protocol viability, license
compatibility или готовность POKROV candidate.

## Ограничения и authority

1. Forum/Habr reports часто не содержат exact client/core/config/carrier/region;
   противоречия сохранены, а не усреднены в «истину».
2. Keyword counts нужны для навигации по корпусу, не для ranking протоколов.
3. Upstream docs и source определяют capability/version facts; field reports только
   формируют эксперименты.
4. Ни один внешний отчет не заменяет POKROV exact-client RU-origin evidence.
5. Этот каталог не зарегистрирован в `docs/README.md` в этой ветке: registry в
   исходном worktree имел concurrent uncommitted change. Добавление строки требует
   collision review при интеграции, а не перезаписи чужой работы.

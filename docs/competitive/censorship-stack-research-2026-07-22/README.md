# POKROV censorship stack: техническое решение

Статус: `EXPERIMENTAL`, advisory research, не источник product/runtime truth

Срез: `2026-07-22`

Ветка: `codex/research-censorship-stack-2026-07-22`

База platform: `b250b39a38e82a5502824f800bb3e2ab11fc65ec`

Проверенный client: `C:/Users/kiwun/Documents/ai/POKROV-app`, `main@60a6ca49c46b057c2654bab4be57d7f1b82d6797`

Лицензионный контекст: `OPERATOR_ATTESTED` — owner подтвердил отдельную лицензию
и разрешение на использование Hiddify в POKROV. Сам документ и его scope в этом
research не проверялись и в репозиторий не копировались.

## Решение в одном абзаце

Клиент POKROV уже переделан и остается нашим: UI, bootstrap, managed profiles,
Android `VpnService`, Apple packet tunnel, TUN, split routing и desktop host менять
на Hiddify не нужно. Hiddify сейчас только поставщик встроенного `libcore`-артефакта.
С учетом отдельного разрешения целевое решение — сохранить Hiddify как backend,
перевести его с `v3.1.8` на POKROV-owned fork от `v4.1.0` за стабильным adapter и
мигрировать конфиг с sing-box schema 1.8 на 1.13. Upstream release — source
baseline, а не готовый ship artifact: до candidate нужны ABI/security fixes и
patch-by-patch backport review. Released `hiddify-sing-box` — крупная продуктовая
дельта, а не чистый sing-box `1.13.0`, поэтому blind rebase на `1.13.14` запрещен.
`v3.1.8` остается rollback bridge до parity. Direct upstream sing-box/libbox
остается запасным вариантом и возможной долгосрочной базой минимального fork.

## Почему Hiddify v4 — основной путь, но не drop-in update

Текущий pin клиента — `Hiddify Core v3.1.8`. В его `go.mod` находятся
`sing-box v1.8.9`, `Xray-core v1.8.21` и Hiddify forks. Актуальный на дату среза
Hiddify `v4.1.0` перешел на ветку `sing-box 1.13`, изменил mobile/runtime API;
сам проект называет это massive refactor with breaking changes. Это не замена
одного файла.

Public `v4.1.0/LICENSE.md` содержит `NonCommercial`, но owner сообщил о отдельном
разрешении для POKROV. Поэтому public-лицензия больше не является причиной
отвергать Hiddify. Перед release достаточно сохранить внутреннюю ссылку/ID на
grant и подтвердить, что его scope покрывает используемую версию, коммерческую
дистрибуцию, наши изменения и нужные platform/store channels. Секретный документ
в git класть не надо.

Технический разрыв остается:

- v3 mobile API экспортирует `Setup(baseDir, workingDir, tempDir, debug)`, `Parse`
  и `BuildConfig`;
- v4 mobile API использует `Setup(*SetupOptions, PlatformInterface)`, `Start` и
  `Stop`; старые `Parse`/`BuildConfig` исчезли;
- текущий Windows FFI ожидает `setupOnce`, `parse`, `changeHiddifyOptions` и старый
  пятиаргументный `setup`; v4 desktop ABI этих символов не имеет и расширяет
  `setup`;
- Android/iOS сейчас напрямую используют старые `Libbox.newService` /
  `LibboxNewService` bindings, которые также надо портировать;
- v4 release assets переименованы в `hiddify-lib-*`, но GitHub уже публикует их
  SHA-256 digests — downloader должен проверять их до распаковки.

Источники: [Hiddify v4.1.0 release](https://github.com/hiddify/hiddify-core/releases/tag/v4.1.0),
[Hiddify history](https://github.com/hiddify/hiddify-core/blob/v4.1.0/HISTORY.md),
[Hiddify license](https://github.com/hiddify/hiddify-core/blob/v4.1.0/LICENSE.md),
[v3.1.8 go.mod](https://github.com/hiddify/hiddify-core/blob/v3.1.8/go.mod),
[v4.1.0 go.mod](https://github.com/hiddify/hiddify-core/blob/v4.1.0/go.mod),
[sing-box license](https://github.com/SagerNet/sing-box/blob/v1.13.14/LICENSE).

Сравнение запасных cores: [`core-alternatives.md`](core-alternatives.md).

Карта больших clients, branded APK и forks:
[`client-core-landscape.md`](client-core-landscape.md). Проверенный Hiddify v4
audit и наш patch stack: [`hiddify-v4-hardening.md`](hiddify-v4-hardening.md).
Точная дельта Hiddify, WARP и варианты обновления:
[`hiddify-fork-delta.md`](hiddify-fork-delta.md). Сравнение Go/Rust cores и
клиентской/серверной архитектуры:
[`core-engine-architecture.md`](core-engine-architecture.md).

## Что реально есть сейчас

| Слой | Наблюдаемое состояние | Вывод |
| --- | --- | --- |
| POKROV app | Собственные Flutter shell/bootstrap и native host-слои | Оставить |
| Android | Собственный `VpnService`, `PlatformInterface`, app-owned TUN; generated config не добавляет mixed inbound | Оставить и адаптировать к новому libbox API |
| iOS | Собственный `PacketTunnelProvider`, `PlatformInterface`, command server/service | Оставить; signed-device proof по-прежнему отдельный release gate |
| Desktop | TUN плюс loopback mixed listeners `12334` и runtime `22341` | Инвентаризировать, ненужные убрать; нужные закрыть случайной авторизацией/жестким lifecycle |
| Core artifact | `hiddify/hiddify-core@v3.1.8` (`libcore.aar`, `libcore.dll`, Apple framework) | Портировать на v4 через compatibility adapter, с rollback на v3 |
| Client config gate | Bootstrap принимает только `config_format == singbox-json` | Это текущая фактическая capability |
| Declared fallback | Product seed объявляет `advanced_fallback_core: xray` | Ложный контракт: убрать до реальной реализации |
| Backend XHTTP | `reserve_xhttp_cdn` и `operator_lab` возвращают `xray-json` | Текущий клиент отвергнет manifest; не назначать пользователям |
| Baseline | `legacy_reality_fallback`, VLESS + REALITY + Vision/RAW | Сохранить как baseline, но не как единственный маршрут |
| RU bridge | Sing-box detour и rollout flags уже существуют | Оставить механизм, убрать предположение о вечном whitelist конкретного ASN/бренда |
| RU probes | DNS/TCP/TLS, 64 KiB GET, XHTTP/Hysteria adapters, честный `not_run` | Хорошая база; добавить exact-client payload proof |

Ключевые локальные доказательства:

- `POKROV-app/config/runtime-artifacts.seed.json` фиксирует `v3.1.8`;
- `POKROV-app/packages/app_shell/lib/app_first_runtime_bootstrap.dart` отвергает
  все, кроме `singbox-json`, и генерирует legacy-поля `inet4_address`,
  `inet6_address`, inbound `sniff` и `domain_strategy`;
- `POKROV-app/packages/runtime_engine/lib/runtime_engine.dart` задает
  `use-xray-core-when-possible=false` и mixed port `22341`; его v3 Windows FFI
  копирует возвращенный `C.CString`, но не имеет `freeString`, что подтверждает
  актуальность Hiddify [core issue #112](https://github.com/hiddify/hiddify-core/issues/112);
- `portal_bot/api.py` выдает `xray-json` для XHTTP/lab профилей;
- `portal_bot/.env.example`, `portal_bot/config.py` и `portal_bot/bot.py`
  по умолчанию используют общий donor SNI `yahoo.com`;
- `scripts/ru_probe_runner.py` проверяет факт чтения не менее 64 KiB, но не
  целостность payload, upload, одновременные сессии и запуск exact shipped client.

## Целевая архитектура

```text
POKROV UI / bootstrap / policy
              |
              v
POKROV runtime contract + versioned capability manifest
              |
              v
POKROV compatibility adapter
  Android/iOS host bindings        Windows versioned FFI
              |
              v
POKROV fork: Hiddify Core v4.1.0 + exact released hiddify-sing-box
              |
              v
managed config, schema pinned to the embedded core
              |
              v
baseline + independently rolled-out transport contours
```

Не нужен новый универсальный proxy framework внутри клиента. Adapter должен
владеть только стабильной границей: `setup`, `validate`, `start/reload`, `stop`,
TUN callbacks, status/error и version/capabilities. Профили остаются server-owned,
а host networking — POKROV-owned. Нельзя размазывать Hiddify API по Flutter,
Kotlin и Swift: смена core должна оставаться локальной заменой backend adapter.

Исходная точка migration — exact Hiddify `v4.1.0`, а не плавающий `main`.
Первый candidate — собственная воспроизводимая сборка с зафиксированным patch
manifest. Release содержит Android, iOS, macOS и Windows library artifacts с
опубликованными digests, а build tags включают Naive и AWG. Exact fork audit также
нашел WARP, XHTTP, Mieru, Psiphon и DNSTT. Это сильнее чистого sing-box по
capability breadth, но дороже в сопровождении: released fork уже содержит 156
commits и меняет 236 файлов после общего upstream base. Code audit нашел desktop
use-after-free, небезопасное хранение/logging config и лишний old command server;
upstream artifact без исправлений не ship-им. Источники:
[Hiddify v4.1.0 release](https://github.com/hiddify/hiddify-core/releases/tag/v4.1.0),
[`hiddify-v4-hardening.md`](hiddify-v4-hardening.md),
[`hiddify-fork-delta.md`](hiddify-fork-delta.md).

## Обязательная миграция схемы

Нельзя подложить sing-box 1.13 вместо 1.8 и считать работу законченной. В текущем
client/platform output есть удаленные или устаревшие конструкции:

- `inet4_address` / `inet6_address` должны стать `address`;
- inbound `sniff` и `domain_strategy` должны переехать в route actions;
- специальные outbound types `block` и `dns` удалены из новой схемы;
- legacy WireGuard outbound заменен endpoint-моделью;
- DNS server/rule formats требуют отдельной миграции;
- новые конфиги должны валидироваться именно встроенным binary до выдачи клиенту.

Официальные owners: [deprecated features](https://sing-box.sagernet.org/deprecated/)
и [migration guides](https://sing-box.sagernet.org/migration/).

## Сетевой набор

### Оставить в основном контуре

1. VLESS + REALITY + Vision/RAW как дешевый TCP baseline.
2. Несколько ingress и egress в разных ASN, независимые failure domains.
3. Server-managed profiles, per-carrier/per-region/per-cohort rollout и быстрый
   rollback.
4. Split route `all-except-RU`, если exact-client probe подтверждает DNS и payload.
5. Реальные RU-origin measurements; ни TCP connect, ни TLS handshake отдельно не
   считаются доказательством рабочего туннеля.

### Добавить как независимые canary, не как новые defaults

- **Naive H2** после перехода на sing-box 1.13. Это сильный TCP-кандидат благодаря
  Chromium network stack, HTTP/2 multiplexing и padding. Первый режим — один
  туннель, без `insecure_concurrency`: официальная документация предупреждает, что
  несколько TLS-соединений легче выделить. Нужны soak, memory и RU carrier tests.
  Источники: [sing-box Naive](https://sing-box.sagernet.org/configuration/outbound/naive/),
  [NaiveProxy](https://github.com/klzgrad/naiveproxy).
- **Hysteria2** как UDP/QUIC failure domain. Никогда не единственный путь: в корпусе
  есть полные QUIC-блокировки на отдельных сетях и обратные наблюдения на других.
  Источник протокола: [Hysteria 2](https://v2.hysteria.network/docs/developers/Protocol/).
- **AmneziaWG** только отдельным spike после Naive/Hysteria. Репозиторий активен,
  но forum-упоминания не доказывают устойчивость POKROV profile на конкретных
  операторах. Источник: [amneziawg-go](https://github.com/amnezia-vpn/amneziawg-go).
- **AnyTLS** — низкоприоритетный lab comparator, если Naive не проходит gates.

### Не включать сейчас

- XHTTP не показывать клиенту до ship-проверки Hiddify XHTTP path либо реального
  Xray runtime path. Released Hiddify fork уже содержит XHTTP transport, поэтому
  второй engine не обязателен априори; нужны build-registration, config parity и
  interoperability tests с exact Xray server. uTLS воспроизводит ClientHello, а
  не полный browser stack; свежие полевые сообщения противоречивы. Reference owner:
  [Xray transports](https://xtls.github.io/en/config/transports/).
- gRPC оставить compatibility canary, не объявлять «primary» без новых RU данных.
- Cloak, GoodbyeDPI, browser extension и zapret не являются core transport для
  мобильного managed VPN. Zapret может жить как отдельный Windows/router recovery
  tool, без смешивания с POKROV tunnel lifecycle.
- TURN/WebRTC/Telemost-подобные обходы не делать production dependency: сторонние
  аккаунты, CAPTCHA, ToS, rate limits и внезапные изменения сервиса.
- Не переносить собственный Rust crypto/TLS/protocol из Habr. Оттуда полезны
  инженерные уроки, но не новый криптографический стек.
- Не мигрировать control plane на Remnawave только по статье. Одновременно 3x-ui
  нельзя оставлять стратегическим production authority: его README называет проект
  personal-use и просит не использовать в production. Xray baseline сохраняем, а
  3x-ui постепенно отделяем тонким POKROV-owned runner/config/rollback layer.

## Наши исправления

Полная матрица и acceptance gates находятся в
[`decision-matrix.md`](decision-matrix.md). Коротко, порядок такой:

### P0 — до расширения транспортов

1. Запретить выдачу `xray-json` текущему POKROV client и удалить/скрыть ложное
   обещание Xray fallback.
2. Зафиксировать внутренний reference на отдельное Hiddify permission и создать
   POKROV fork от `v4.1.0`: pinned root/submodule commits, toolchain, SHA-256, SBOM
   и provenance. Составить upstream-fix manifest до `1.13.14`; переносить patches
   по одному, без blanket rebase released Hiddify delta.
3. Исправить desktop C ABI ownership, config persistence/logging, raw-config path
   и лишние command/profiling surfaces; затем сделать v4 compatibility-adapter +
   config migration spike и пройти Android TUN, Windows TUN, iOS source build и
   existing route-mode tests.
4. Убрать generic `yahoo.com` default. REALITY target/SNI должен быть
   per-node, достижим с этого node и подтвержден probe; один donor на весь парк
   создает общий kill switch.
5. Убрать ненужные desktop loopback proxy listeners. Если mixed listener нужен
   для диагностики/system proxy, выдавать случайные credentials на сессию,
   ограничить loopback и lifetime, тестировать закрытие после disconnect.

### P1 — после core migration

1. Exact-client RU probe: получить реальный manifest тем же API, валидировать тем
   же shipped core, поднять тот же TUN и проверить download с hash, upload, DNS
   через туннель, split routing, reconnect, IPv4/IPv6 и concurrency 1/N.
2. RU bridge pool минимум в двух независимых ASN; eligibility определяется свежим
   payload probe по carrier/region/time bucket. Никаких вечных Yandex/VK flags.
3. Naive H2 canary, затем отдельный Hysteria2 canary. Rollout только после
   `PASS` exact candidate, `MANUAL_OWNER_TEST` на устройствах и rollback proof.
4. Отделить Xray process/config lifecycle от 3x-ui: canonical POKROV model,
   exact-binary validation, atomic activation и rollback. Панель временно может
   остаться adapter/UI, но не единственным источником runtime truth.

### P2 — только по измеренной необходимости

AWG/AnyTLS comparator, Xray/XHTTP second-engine spike, автоматический route
selection. Второй engine оправдан только если exact RU tests покажут устойчивую
зону, которую sing-box contours не закрывают.

## Что не доказано

Форум и Habr — полевые сигналы, а не лаборатория. Они хорошо показывают, что
блокировки зависят от оператора, ASN, региона, времени, SNI, fingerprint,
направления трафика и размера payload. Они не доказывают универсальный «лучший
протокол». Поэтому этот документ задает backlog и experiment gates, но не меняет
production truth и не утверждает RU readiness.

Полнота корпуса, разбор каждого входного URL, high-signal комментарии и hashes:
[`source-coverage.md`](source-coverage.md).

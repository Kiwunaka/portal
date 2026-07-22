# Hiddify против чистого sing-box: реальная дельта

Статус: `EXPERIMENTAL`, advisory research

Срез: `2026-07-22`

## Вердикт

Hiddify Core — не тонкая обертка над чистым sing-box. В release `v4.1.0` это
cross-platform runtime, config/profile layer и крупный продуктовый fork
`hiddify-sing-box`. Поэтому формулировка «просто обновить sing-box 1.13.0 до
1.13.14» была неверной: слепой replace/rebase может потерять нужные POKROV
capabilities или создать труднообнаружимые несовместимости.

Hiddify лучше чистого sing-box для POKROV, пока нам действительно нужны его:

- автоматический WARP endpoint и WARP detours;
- AmneziaWG и его noise-параметры;
- XHTTP, Mieru, Psiphon, DNSTT и расширенная Naive-линия;
- готовые Android/Apple/Windows build recipes и bindings;
- profile conversion, selector/load-balancing и Hiddify-specific routing patches.

Чистый sing-box лучше, если фактический продуктовый набор можно сократить до
стандартных VLESS/REALITY, Hysteria2, Naive и обычного TUN: меньше fork debt,
короче supply chain, быстрее попадание security fixes и меньше скрытой config
mutation. Hiddify не становится автоматически быстрее или безопаснее только из-за
большего числа протоколов.

## Что дает v4 против текущего POKROV v3.1.8

| Surface | Current v3.1.8 | v4.1.0 family | Практический эффект |
| --- | --- | --- | --- |
| Base | sing-box `1.8.9` era + старые Hiddify/Xray deps | sing-box `1.13` era + новый Hiddify fork | Новые protocol/TUN/DNS/TLS capabilities и накопленные fixes, но большая миграция schema |
| Naive | Нет современной 1.13-линии | Inbound/outbound code и release build tag | Можно сделать первый независимый TCP canary без отдельного Chromium daemon |
| WARP/AWG | Старые Hiddify helpers/forks | Endpoint model, Cloudflare bootstrap/detour/cache, AWG build | Сохраняем уже полезную POKROV capability и получаем более явный endpoint contract |
| XHTTP | Не является надежной shipped capability текущего POKROV contract | Реальная implementation в released Hiddify fork | Можно сначала проверить один core вместо немедленного добавления Xray client engine |
| TLS/DNS/TUN base | Старые sing-box APIs/deprecations | 1.13-era ECH/QUIC/native DNS/route/TUN work | Современнее platform base; старый config нельзя подавать без migration |
| Bindings/runtime | Старые `Setup/Parse/BuildConfig`, v3 libbox usage | Breaking `SetupOptions/PlatformInterface`, новый start/stop path | Лучше выстроить чистую adapter boundary, но drop-in update невозможен |

Главный выигрыш v4 — не обещание «больше скорости», а доступ к современной
protocol/platform базе и сохранение Hiddify-specific capabilities. Скорость,
память, battery и стабильность надо доказать old/new differential benchmark на
наших exact profiles и devices.

## Точная provenance release `v4.1.0`

| Компонент | Зафиксированное состояние |
| --- | --- |
| Hiddify Core tag | `c9d6f0f00b2eda34e4fb71863e4e0a62b3e931a0`, 2026-03-05 |
| `hiddify-sing-box` submodule | `0a02b7729f6a211436bb8bdcd8696c283eb27767` |
| `ray2sing` submodule | `f58be84e30d946915a1de437fbcc3d3ffca18a23` |
| Fork merge-base с upstream stable | `aba8346bd6c533ffb144258118e1100ff31e2cb5`, 2026-02-06 |
| Дельта release fork после merge-base | 156 commits; 236 files; `+15 806/-2 538` |
| Upstream stable commits, отсутствующие в release fork на дату среза | 191 |

Числа получены локальным `git merge-base`, `git rev-list` и `git diff` exact
submodule commit против [`SagerNet/sing-box`](https://github.com/SagerNet/sing-box).
Они описывают graph/code delta, а не 156 независимых фич или 191 обязательный
backport. В upstream-части есть feature work, refactors и fixes; каждый нужный fix
надо классифицировать отдельно.

Release build включает теги:

```text
with_gvisor,with_quic,with_wireguard,with_utls,with_clash_api,with_grpc,
with_awg,tfogo_checklinkname0,with_naive_outbound,with_conntrack
```

Источник: [`v4.1.0/Makefile`](https://github.com/hiddify/hiddify-core/blob/v4.1.0/Makefile)
и [точный submodule pin](https://github.com/hiddify/hiddify-core/tree/v4.1.0).

## Что добавляет released fork

Exact source audit нашел не только build tags, а реальные реализации:

| Дельта | Что есть в коде | Значение для POKROV |
| --- | --- | --- |
| WARP | Endpoint поверх WireGuard/AWG, Cloudflare profile bootstrap, cache, detour | Полезный optional egress/bridge и смена exit IP без отдельного WARP daemon |
| AWG | Endpoint, userspace transport и полный набор junk/header/noise fields | Прямой путь к AmneziaWG capability в одном runtime |
| XHTTP | Собственный `transport/v2rayxhttp` client/server implementation | XHTTP уже не обязательно требует второго Xray core, но нужна точная interop-проверка с нашим Xray server |
| Naive | Outbound и inbound, H2/QUIC-related code и tests | Шире чистого старого POKROV pin; upstream 1.13 также получил Naive outbound |
| Mieru | Inbound/outbound | Дополнительный contour, пока без POKROV evidence |
| Psiphon | Outbound integration | Возможный specialist contour, но тяжелее supply chain и operations |
| DNSTT | DNS tunnel outbound | Emergency/lab capability; очень ограниченная пропускная способность |
| Routing/group | Consistent hashing, selectors, health/load-balancing patches | Может быть полезно для server-managed pool, но нельзя давать core право тайно менять final policy |

Примеры exact source: [WARP endpoint](https://github.com/hiddify/hiddify-sing-box/blob/0a02b7729f6a211436bb8bdcd8696c283eb27767/protocol/wireguard/endpoint_warp.go),
[AWG endpoint](https://github.com/hiddify/hiddify-sing-box/blob/0a02b7729f6a211436bb8bdcd8696c283eb27767/protocol/awg/endpoint.go),
[Naive outbound](https://github.com/hiddify/hiddify-sing-box/blob/0a02b7729f6a211436bb8bdcd8696c283eb27767/protocol/naive/outbound.go),
[XHTTP transport](https://github.com/hiddify/hiddify-sing-box/tree/0a02b7729f6a211436bb8bdcd8696c283eb27767/transport/v2rayxhttp).

Следствие: наш fork поверх Hiddify может быть небольшим по числу собственных
POKROV commits, но наследуемая Hiddify delta уже большая. Ее нельзя называть
«небольшим fork» в смысле maintenance cost.

## WARP: чем конкретно хорош Hiddify

Hiddify WARP — не просто parser готового WireGuard JSON. Endpoint умеет:

1. Создать или получить Cloudflare device profile через Cloudflare API.
2. Выполнить bootstrap через указанный outbound detour; при ошибке попробовать
   доступные outbounds по очереди.
3. Кэшировать профиль и повторно использовать его без каждого API bootstrap.
4. Выбрать endpoint address/port из профиля либо принять explicit override.
5. Построить WARP поверх proxy или использовать WARP как detour для другого
   outbound.
6. Передать AWG noise options в тот же WireGuard endpoint path.

Это действительно сильная дельта к чистому sing-box: POKROV получает WARP/AWG в
одном runtime и может пережить недоступность Cloudflare API напрямую, если bootstrap
проходит через другой контур.

Но текущая реализация требует нашего hardening:

- `Start` запускает инициализацию в goroutine и возвращает успех до readiness;
  ошибки только логируются — adapter должен ждать `IsReady` с timeout и получать
  typed failure;
- cache содержит WARP private key, поэтому это credential material: app-private
  storage, ACL/mode, lifecycle и redaction обязательны;
- код берет `Peers[0]` и случайный port без проверки непустых slices; это
  code-level panic risk на malformed/API-changed profile, не доказанный production
  incident;
- Cloudflare API и WireGuard/UDP могут быть недоступны на конкретной сети, поэтому
  WARP не может быть единственным censorship path;
- `GenerateWarpConfig` в Hiddify Core v4 сейчас возвращает пустую структуру, а в
  legacy `patchWarp` после раннего `return nil` остался недостижимый код. Нельзя
  строить наш API на этих helpers без исправления и tests.

Источники: [endpoint code](https://github.com/hiddify/hiddify-sing-box/blob/0a02b7729f6a211436bb8bdcd8696c283eb27767/protocol/wireguard/endpoint_warp.go),
[`GenerateWarpConfig`](https://github.com/hiddify/hiddify-core/blob/v4.1.0/v2/hcore/warp.go),
[`patchWarp`](https://github.com/hiddify/hiddify-core/blob/v4.1.0/v2/config/warp.go).

## Release fork, `main` или минимальный POKROV fork

На дату среза Hiddify Core `main` указывает уже на другой submodule commit:
`170d8315cab7a8695fd80469073ed2f1d07d63af`; root commit
`db74dfc257d5becb4b4e9dbc7257a3dcdde20692`. В нем есть более новая transport
работа, включая MASQUE, VLESS encryption, simple-obfs/Snell и дальнейшие изменения
XHTTP/WARP/AWG. Но это не release line и не чистый security update: root `main`
также добавляет extension/product surfaces, health/speed helpers и прочие функции,
не нужные POKROV. Exact graph против upstream tag `v1.13.14`: 386 fork-only
commits, 18 upstream-only commits, 691 changed files (`+194 595/-6 846`). Размер
частично объясняется новыми protocol/vendor/product surfaces, но в любом случае
исключает трактовку `main` как маленького patch update.

Есть три честных стратегии:

| Стратегия | Плюс | Минус | Решение сейчас |
| --- | --- | --- | --- |
| A. `v4.1.0` fork + отобранные fixes/backports | Стабильная provenance и минимальный migration shock | Остаемся владельцем backport queue | Первый parity candidate |
| B. Новый Hiddify `main`/следующий release | Больше новых протоколов и upstream work | Больше unaudited delta, нет стабильного release contract | Отдельный candidate после A, не подмена A |
| C. Минимальный POKROV fork от upstream sing-box | Самая короткая долгосрочная delta | Надо переносить только нужные Hiddify features и владеть build/bindings | Долгосрочная цель после capability telemetry |

Для первого candidate выбираем A. Не делаем blanket rebase на `1.13.14`; вместо
этого составляем manifest upstream commits между fork base и `1.13.14`, отдельно
маркируем security/correctness/config/API changes и переносим только доказанно
нужные patches. Параллельно проверяем, какие Hiddify features реально вызываются
POKROV. После нескольких месяцев telemetry можно решить, оправдана ли стратегия C.

## Другие sing-box forks

| Fork | Open issues без PR | Release/activity на срезе | Что добавляет | Вывод |
| --- | ---: | --- | --- | --- |
| [`hiddify/hiddify-sing-box`](https://github.com/hiddify/hiddify-sing-box) | 0 | tag `v1.13.0.h5`, 2026-02-09; Core release использует exact более поздний commit | WARP/AWG/XHTTP/Naive/Mieru/Psiphon/DNSTT и product routing | Наш текущий рациональный baseline из-за уже купленной интеграции |
| [`shtorm-7/sing-box-extended`](https://github.com/shtorm-7/sing-box-extended) | 5 | `v1.13.14-extended-2.5.2`, 2026-07-18 | WARP, MASQUE, Mieru, OpenVPN, MTProxy, TrustTunnel, AWG 2, XHTTP, admin/limits/failover | Еще больший продуктовый fork; не drop-in и не уменьшает ownership |
| [`KaringX/sing-box`](https://github.com/KaringX/sing-box) | 0 | Active 2026-07-20; нет собственного release line | Karing-specific fixes/features | Брать чужую product delta без Karing app смысла нет |
| [`MatsuriDayo/sing-box`](https://github.com/MatsuriDayo/sing-box) | 0 | Last push 2026-02-02; нет releases | NekoBox compatibility/product changes | Не подходит как наш upstream |
| [`getlantern/sing-box-minimal`](https://github.com/getlantern/sing-box-minimal) | 0 | Active 2026-07-17; product pin из Radiance | Сокращенная/измененная sing-box часть Radiance | Архитектурный reference, не reusable POKROV base |

Ноль issues у fork-репозитория ничего не доказывает: trackers могут быть выключены,
перенесены в app repository или использоваться только для PR.

## Что хвалить, за что ругать Hiddify

Хвалить обоснованно:

- одна cross-platform data-plane family вместо набора отдельных daemons;
- реальная protocol breadth, включая редкие и полезные WARP/AWG paths;
- готовые gomobile/Apple/Windows artifacts и build recipes;
- массовая app-линия дает больше реального device exposure, чем у новых Rust cores;
- мы уже интегрировали эту семью и имеем отдельное разрешение.

Ругать обоснованно:

- breaking v3→v4 API и отсутствие стабильного внешнего ABI;
- существенная fork delta и lag от upstream fixes;
- смешение engine, config builder, profile conversion и product controls;
- security/correctness defects, найденные в v4 ABI/config handling;
- readiness/lifecycle местами построены вокруг logs, а не typed state;
- release notes и dependency provenance недостаточны для автоматического update.

Это чинится. Нужны не переписывание ядра и не вера в upstream binary, а узкий
POKROV adapter, собственная воспроизводимая сборка, capability telemetry и
patch-by-patch update policy. Полный hardening backlog:
[`hiddify-v4-hardening.md`](hiddify-v4-hardening.md).

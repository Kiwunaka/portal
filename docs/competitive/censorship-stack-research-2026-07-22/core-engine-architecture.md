# Ядра клиента и сервера: архитектурный разбор

Статус: `EXPERIMENTAL`, advisory research

Срез: `2026-07-22`

## Короткий ответ

Для POKROV сейчас не нужен один «самый лучший core» на клиенте и сервере.
Нужен один наш control/runtime contract и несколько строго ограниченных protocol
owners:

- **клиент:** POKROV app + разрешенный Hiddify v4 fork как основной data plane;
- **серверный baseline:** Xray-core для VLESS/REALITY/XHTTP, потому что он владеет
  этой protocol family и уже является фактическим runtime POKROV;
- **отдельный UDP contour:** native Hysteria2 и/или AWG только после exact RU tests;
- **Naive server:** сначала sing-box 1.13 inbound с exact Hiddify-client interop;
- **Rust comparator:** `shoes` в лаборатории, не production replacement;
- **Qeli из Habr 1052536:** полезный R&D/postmortem, но pre-1.0 custom protocol с
  hand-written TLS без независимого внешнего аудита — не кандидат на замену.

Архитектурная цель — не запихнуть все протоколы в один процесс. Цель — один
POKROV capability manifest, provisioning/control plane, evidence contract и
rollback, а сетевые engines держать отдельными процессами/listeners там, где это
уменьшает blast radius.

## Snapshot проектов

`Open issues` ниже — открытые GitHub issues без pull requests на момент сбора.
Stars/forks округлены и нужны только как community/maintenance signal. Ни одно из
этих чисел не является рейтингом качества: широкий пользовательский продукт
естественно имеет больше bug reports, а repo с выключенным tracker — ноль.

| Проект | Язык/license | Stars / forks | Open issues | Последняя проверенная линия | Роль |
| --- | --- | ---: | ---: | --- | --- |
| [sing-box](https://github.com/SagerNet/sing-box) | Go, GPL-3.0-or-later | ~36.4k / ~4.3k | 232 | stable `1.13.14`; testing `1.14.0-alpha.50` | Лучший универсальный upstream/libbox base |
| [Hiddify Core](https://github.com/hiddify/hiddify-core) | Go/JS, custom public terms; отдельное POKROV permission `OPERATOR_ATTESTED` | ~229 / ~175 | 29 | `v4.1.0` | Основной client backend, не готовый binary |
| [Xray-core](https://github.com/XTLS/Xray-core) | Go, MPL-2.0 | ~40.6k / ~5.7k | 24 | stable `v26.3.27`; libXray line уже использует `v26.7.11` | VLESS/REALITY/XHTTP owner, server baseline |
| [Mihomo](https://github.com/MetaCubeX/mihomo) | Go, MIT | ~32.6k / ~4.3k | 428 | `v1.19.29` | Зрелая Clash-family альтернатива |
| [V2Ray-core](https://github.com/v2fly/v2ray-core) | Go, MIT | ~34.4k / ~5.1k | 30 | `v5.51.2` | Зрелый предок/family, слабее для новых XTLS features |
| [Hysteria](https://github.com/apernet/hysteria) | Go, MIT | ~22.2k / ~2.2k | 238 | `v2.10.0` | Лучший specialist QUIC/UDP contour |
| [shadowsocks-rust](https://github.com/shadowsocks/shadowsocks-rust) | Rust, MIT | ~10.8k / ~1.4k | 56 | `v1.24.0` | Сильный specialist Shadowsocks engine |
| [Leaf](https://github.com/eycorsican/leaf) | Rust, Apache-2.0 | ~2.8k / ~508 | 4 | `v0.14.2` | Embeddable Rust research candidate |
| [shoes](https://github.com/cfal/shoes) | Rust, MIT | ~1.2k / 113 | 33 | tag `v0.2.7`; source `0.2.8` | Самый интересный Rust server comparator |
| [clash-rs](https://github.com/Watfaq/clash-rs) | Rust, Apache-2.0 | ~1.7k / 158 | 39 | `v0.10.7` | Rust Clash client/runtime research |
| [meow-rs](https://github.com/madeye/mihomo-rust) | Rust, MIT | ~369 / 36 | 3 | `v0.18.0` | Молодая Mihomo reimplementation |
| [Qeli](https://github.com/litvinovtd/qeli) | Rust core AGPL-3.0-only; client shells MPL | ~204 / 7 | 1 | `v0.7.12` pre-release/beta | Изолированный R&D only |
| [Radiance](https://github.com/getlantern/radiance) | Go, GPL-3.0 | ~10 / 0 | 0 | rolling, без public release line | Архитектура Lantern, не показатель по stars |

Snapshot фиксирует наблюдаемое состояние, а не обещает, что цифры останутся
такими. Для production выбора важнее release provenance, bus factor, тесты,
protocol ownership и скорость попадания конкретных security fixes.

Отдельный пример, почему issue count нельзя читать буквально: у Radiance на срезе
ноль открытых issues, но 23 pull requests, около 695 commits и распределенная
команда. Это продуктовый repo с другим workflow, а не проект «без ошибок».

## Что именно меняют последние линии

| Проект/линия | Характер обновлений | Как это читать для POKROV |
| --- | --- | --- |
| sing-box `1.13.x` | Новые Naive/ECH/QUIC/DNS/TUN capabilities плюс частые общие fixes; patch notes местами слишком краткие | Нужен commit-level diff, не автоматический patch bump |
| Hiddify `v3 -> v4` | Massive refactor, breaking API/config/runtime boundary, новая sing-box family | Полноценный port, не замена AAR/DLL |
| Hiddify fork `main` после `v4.1.0` | MASQUE/VLESS encryption/simple-obfs/Snell и дальнейшие XHTTP/WARP/AWG changes вместе с product features | Не брать rolling `main` целиком; отдельный candidate и feature pruning |
| Xray/libXray CalVer | Быстрая совместная эволюция XHTTP/REALITY/core и wrapper; wrapper latest-core-only | Pin exact pair; server/client interop test на каждой паре |
| Hysteria `2.9.2 -> 2.10.0` | Security fixes ACL/OOM/trailing-dot, затем ECH/stability options | Specialist owner полезен, но security release надо доставлять быстро |
| shoes `0.2.x` | AnyTLS memory/lifecycle, TUN, DNS, QUIC, chaining/hot-reload work | Хороший lab momentum; pre-1.0 API/dependency discipline пока слабая |
| clash-rs `0.10.x` | Windows DNS, Android socket binding, interface binding, config/CORS fixes | Активный, но platform lifecycle bugs еще типичны для молодого core |
| meow-rs `0.18.x` | Windows service/TUN, route concurrency, DNS allocation, atomic traffic stats | Быстрый прогресс, пока без нашей mobile embedding parity |
| Qeli `0.7.x` | Очень частые security/correctness fixes across Rust/Kotlin/C#/web | Хорошая реакция maintainer одновременно показывает нестабильность beta attack surface |

Источники: [sing-box releases](https://github.com/SagerNet/sing-box/releases),
[Hiddify history](https://github.com/hiddify/hiddify-core/blob/v4.1.0/HISTORY.md),
[Hysteria releases](https://github.com/apernet/hysteria/releases),
[shoes changelog](https://github.com/cfal/shoes/blob/master/CHANGELOG.md),
[clash-rs releases](https://github.com/Watfaq/clash-rs/releases),
[meow-rs releases](https://github.com/madeye/mihomo-rust/releases),
[Qeli releases](https://github.com/litvinovtd/qeli/releases).

## Что хвалят и за что ругают основные Go-ядра

### sing-box/libbox

Хвалят за широкий единый config model, TUN/routing/DNS, хорошие mobile bindings и
быстрое добавление протоколов. Линия 1.13 принесла Naive outbound, ECH/QUIC и
congestion options, Chrome Root Store, kTLS, ICMP proxy, native DNS, Tailscale и
`auto_redirect` improvements.

Ругают за высокий churn схемы и API, миграции deprecated полей, частые testing
releases и короткие notes вида «fixes and improvements». Это означает, что номер
релиза нельзя продвигать автоматически. Отдельно важный официальный вывод:
sing-box сам [не рекомендует uTLS для censorship circumvention](https://sing-box.sagernet.org/configuration/shared/tls/#utls),
потому что копирование ClientHello не превращает Go connection в настоящий browser
network stack; для этого upstream рекомендует Naive.

`1.14 alpha` добавляет интересные OpenVPN/OpenConnect/MASQUE-related surfaces, но
alpha-линия не должна быть первым POKROV v3→v4 migration target.

### Hiddify Core / hiddify-sing-box

Хвалить есть за что: реальный массовый cross-platform app exposure, WARP/AWG,
Naive, XHTTP и specialist outbounds в одном data plane, готовые builds. Ругать —
за breaking ABI, большой fork, отставание released dependency line, config builder
side effects и lifecycle/security defects. Это не повод выбрасывать уже разрешенный
и интегрированный core; это причина владеть adapter/build/update policy.

Точная дельта и WARP-разбор:
[`hiddify-fork-delta.md`](hiddify-fork-delta.md).

### Xray-core + libXray

Xray — protocol authority для VLESS, REALITY, Vision и XHTTP. Он логичен на
сервере и как второй client engine только при измеренном XHTTP gap. У него уже есть
[официальный libXray wrapper](https://github.com/XTLS/libXray) для Android, Apple,
Linux и Windows, единый JSON `Invoke`, `CGoFree`, config check/run/stop, socket
protect, DNS и process finder.

Значит прежнее утверждение «готовой mobile boundary нет» было слишком сильным.
Boundary есть, но README самого libXray предупреждает: мало maintainers, API
stability не гарантирована, совместимость только с latest Xray. Для POKROV все
равно нужен свой versioned adapter и отдельная lifecycle/test/update матрица.

### Mihomo

Это не форк sing-box, а самостоятельная Clash-family. Сильные стороны — зрелая
rule/provider/API ecosystem, TUN, VLESS/REALITY, Hysteria2, TUIC, AnyTLS, MIT.
Слабость для нас — новый config/control model, отсутствие Hiddify WARP/AWG/Naive
parity и еще одна полная migration. Mihomo хорош как новый фундамент для Clash-
продукта, но не как короткий upgrade текущего POKROV.

### Hysteria и shadowsocks-rust

Specialist engine часто лучше универсального в своей узкой задаче. Hysteria дает
быстрый QUIC/UDP transport и активно чинит protocol/security defects. В `2.9.2`
исправлялись UDP ACL bypass, server OOM через oversized/incomplete sniffed HTTP и
trailing-dot ACL bypass; `2.10.0` добавил ECH и stability option. Это хороший
пример, почему native server contour получает fixes быстрее, чем embedded copy.

Но QUIC/UDP полностью режется на части сетей, поэтому Hysteria нельзя делать
единственным ingress. `shadowsocks-rust` аналогично хорош как поддерживаемый
Shadowsocks owner, но не заменяет VLESS/REALITY/Naive/WARP platform.

## Большие конкуренты: как они строят backend

Самый полезный открытый reference — Lantern
[`radiance`](https://github.com/getlantern/radiance). Это настоящий backend клиента,
а не учебный проект. Он объединяет:

- sing-box/sing-tun;
- Outline SDK dialer;
- AmneziaWG;
- application-layer Geneva;
- WATER/WASM transports, которые можно доставлять без обновления всего клиента;
- собственный `LocalBackend`, server manager, config/account, telemetry и IPC.

Ключевой урок: крупный продукт не обязан писать TLS/crypto с нуля. Он владеет
orchestrator/control contract и комбинирует fork стандартного core со specialist
dialers. Цена видна там же: fork `getlantern/sing-box-minimal`, forks WireGuard,
WATER/wazero и сложная supply chain. Для POKROV это архитектурный ориентир, не код
для копирования.

v2rayN, Amnezia и другие multi-core shells подтверждают другую модель: на desktop
можно держать несколько engines. На Android/iOS лишний core гораздо дороже из-за
TUN ownership, background lifecycle, artifact size, energy и store/device matrix.
Поэтому у POKROV второй mobile engine должен появиться только после измеренного gap.

## Rust: что реально лучше и что хуже

Rust дает полезные свойства data plane:

- memory safety без GC pauses;
- строгие ownership/lifetime boundaries;
- удобный async/Tokio stack и zero-copy opportunities;
- один native library можно встроить через C/JNI/Swift FFI;
- обычно компактнее idle memory, если проект не тянет тяжелый runtime/dependencies.

Но язык не решает главные anti-censorship проблемы: wire fingerprint, protocol
interoperability, field measurements, config migration, crypto review, TUN/DNS
recovery и bus factor. Молодое Rust-ядро может быть безопаснее по памяти и намного
опаснее по протоколу. Go GC сам по себе не является проблемой без профиля: зрелый
Go core может дать лучшие tail latency и reliability, чем Rust core с locks,
copies или unsafe FFI.

### Leaf

Самый зрелый embeddable Rust candidate из списка: Tokio/rustls/quinn, C FFI,
Android/iOS scripts, TUN, экспериментальный VLESS/REALITY outbound. Но нет нужной
POKROV parity по VLESS inbound, Hysteria2, Naive, AWG/WARP, а FFI прямо считается
нестабильным. Низкое число issues отражает меньший проект и scope, не автоматически
лучшее качество. Оставить research candidate.

### shoes

Самый сильный Rust server comparator. Поддерживает VLESS/REALITY/Vision,
Shadowsocks, Trojan, Hysteria2, TUIC, AnyTLS, Naive, TUN, chaining и hot reload.
MIT и единый binary привлекательны. В recent history чинились AnyTLS memory leaks,
TUN lifecycle, DNS и QUIC.

Слабые места видны в tracker/API: нет XHTTP, неполный multi-user/control plane,
клиентская parity Hysteria2/TUIC ограничена, есть Windows/TPROXY/library gaps.
`Cargo.toml` использует wildcard dependency versions; checkout спасает `Cargo.lock`,
но сборка без `--locked` может дрейфовать. Есть unsafe FFI/`Send`/`Sync` surfaces.
Вердикт — benchmark exact configs рядом с Xray/sing-box, не ставить production.

### clash-rs и meow-rs

`clash-rs` уже имеет TUN, FFI и широкий набор outbounds, но открытые bugs касаются
Windows TUN/fake-IP, crashes при switch, reload и Reality ambiguity; server mode
только запрашивается. `meow-rs` быстро реализует Mihomo/Clash, включая новый
Windows TUN, но пока нет Android/iOS embedding path и остаются XHTTP/DNS/macOS
transparent-proxy gaps. Их собственные loopback benchmarks полезны только как
directional signal.

### Qeli и статья Habr 1052536

Qeli заслуживает отдельного внимания: это не «очередной wrapper», а собственный
L4 protocol на Rust с native TUN, fake TLS/QUIC masks, certificate borrowing,
multipath, X25519 и ML-KEM-768. Проект исправляет ошибки быстро, содержит fuzz/tests
и честно документирует многие postmortems. За месяц вышла серия `0.7.x`; на дату
среза `v0.7.12` — pre-release, а docs называют всю линию beta до `1.0`.

Что реально хорошо:

- автор разбирает cancellation, partial reads, stale sessions, TUN nonblocking,
  DNS/route recovery и reconnect loops на уровне причин;
- один Rust core уменьшает часть расхождений между платформами;
- multi-queue TUN и отсутствие Go GC интересны для performance experiments;
- releases действительно закрыли serious defects: `allowed_networks` bypass,
  command execution в lifecycle hooks, arbitrary file read, parser OOM/DoS,
  CSRF/XSS и сломанные pushed routes.

Почему нельзя брать в POKROV сейчас:

- собственные wire protocol и hand-written TLS 1.3 record/handshake — огромная
  cryptographic/interoperability/fingerprinting поверхность;
- [`SECURITY.md`](https://github.com/litvinovtd/qeli/blob/main/SECURITY.md) прямо
  говорит, что custom TLS — крупнейшая attack surface и **не проходила независимый
  внешний аудит**;
- документы с названиями «external audit review» описывают принесенные reports и
  внутреннюю проверку/fix rounds; это не заменяет независимый опубликованный audit;
- repo создан в июне 2026, pre-1.0 churn экстремальный, основная масса commits у
  одного автора;
- статья говорит об одном Rust engine, но protocol/lifecycle logic еще частично
  дублируется в Kotlin и C# clients;
- core/server — AGPL-3.0-only, а bundled `libqeli` переносит эти obligations на
  distributed clients; dual licensing нет;
- benchmarks в основном self-run и пока не дают POKROV interop/RU-origin proof.

Итог: взять инженерные уроки и держать isolated lab. Не тащить custom crypto/TLS
в наш shipping core.

## Что лучше на сервере POKROV

Фактический POKROV stack сейчас устанавливает 3x-ui и ожидает Xray VLESS/REALITY:
[`infra/bootstrap_node.sh`](../../../infra/bootstrap_node.sh),
[`portal_bot/control_panel.py`](../../../portal_bot/control_panel.py). Это
важнее абстрактного рейтинга ядер.

### Xray оставить, 3x-ui отделить

Xray-core оставить baseline engine: он protocol owner и совпадает с текущими
profiles. Но 3x-ui не должен оставаться стратегическим production runtime/control
authority. Его собственный README прямо пишет: personal use only, не использовать
в production. Последний release также вынужден учитывать сочетания protocol fields,
которые crash-ят Xray, то есть panel остается полезным compatibility layer, но не
нашей гарантией корректности.

Это не значит «срочно перейти на другую панель». Правильный P1:

1. Вынести POKROV-owned canonical node/profile model.
2. Сделать тонкий Xray runner: generate → exact binary check → atomic activate →
   health → rollback.
3. 3x-ui оставить временным adapter/UI, без права быть единственным источником
   credentials/config/runtime state.
4. После parity решить, нужен ли panel вообще или достаточно нашего admin/control
   plane.

Источник ограничения: [3x-ui README](https://github.com/MHSanaei/3x-ui#readme).

### Контуры и protocol owners

| Контур | Server engine | Почему | Ограничение |
| --- | --- | --- | --- |
| VLESS/REALITY/Vision/RAW | Xray-core | Protocol authority, текущая POKROV интеграция | Donor/SNI/ASN и version combinations требуют probes |
| XHTTP | Xray-core baseline; Hiddify client interop | Самая зрелая reference implementation | Не считать универсальным; exact config/version parity |
| Naive H2 | sing-box 1.13 inbound; `shoes` comparator | Совпадает с Hiddify/sing-box family | Memory/connection shape/interop soak |
| Hysteria2 | Native Hysteria server | Быстрые fixes и protocol owner | UDP/QUIC может быть полностью заблокирован |
| AWG | Kernel module там, где возможно; userspace для portability | Kernel data path обычно дает лучший throughput/CPU | UDP-only failure domain; exact version/config matching |
| Shadowsocks | shadowsocks-rust при реальной необходимости | Specialist mature owner | Не нужен только ради количества протоколов |
| Qeli | Изолированный lab | R&D и benchmark | Не production до 1.0, independent audit и field evidence |

Kernel AWG performance — архитектурное ожидание, а не измеренный POKROV result;
его надо подтвердить на наших instance types. Hiddify Core на сервере не нужен:
его главная ценность — client bindings/config integration, а server protocol owners
уже есть отдельно.

## Целевая схема

```text
POKROV product/control plane
  ├─ canonical profile + capability manifest
  ├─ cohort/region/carrier policy
  ├─ exact-client probes + evidence
  └─ atomic rollout/rollback
          |
          +-- client adapter --> Hiddify v4 fork --> TUN/outbounds
          |
          +-- node runner ----> Xray process       (VLESS/REALITY/XHTTP)
          |                 --> Hysteria process   (UDP canary)
          |                 --> AWG interface      (UDP canary)
          |                 --> sing-box process   (Naive canary)
          |
          +-- lab -----------> shoes / Qeli comparators
```

На первом этапе максимум 2–3 production engines на node. У каждого отдельный
listener/process, pinned version, config validator, health, logs/metrics и rollback.
Нельзя позволять двум engines одновременно владеть одним TUN/listener или скрыто
переписывать общий routing state.

## Update policy

Обновление core — это не «вышел новый tag — поднимаем версию».

1. Pin exact root/submodules/dependencies/toolchain/build tags.
2. Собрать release diff: protocol, config schema, security/correctness, platform,
   build-only и unrelated product changes.
3. Для fork — сохранить два направления: наши commits поверх base и upstream
   commits, которых у нас нет.
4. Пропускать candidate через exact config validation, client↔server interop,
   TUN/DNS/reconnect/handover, leak/credential scan, memory/CPU and long soak.
5. Не смешивать core migration и новый protocol rollout.
6. Security fix можно backport-ить отдельно; feature release не должен блокировать
   critical correction.
7. Testing/alpha lines допускаются только в lab, если нет отдельного owner decision.

В результате Hiddify остается рациональным клиентским ядром, Xray — рациональным
server baseline, а Rust — полезным comparator/источником инженерных решений, но не
причиной переписать работающий стек.

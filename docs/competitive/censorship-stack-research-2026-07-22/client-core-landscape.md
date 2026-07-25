# Клиенты, APK и реальные core-линии

Статус: `EXPERIMENTAL`, advisory research

Срез: `2026-07-22`

## Вывод

Рынок не делится на «Hiddify или чистый sing-box». Есть четыре устойчивые линии:

1. upstream sing-box/libbox и официальные SagerNet clients;
2. продуктовые форки sing-box: Hiddify, Karing, NekoBox и многие branded APK;
3. Xray/V2Ray clients, прежде всего v2rayNG;
4. Mihomo/Clash clients, прежде всего FlClash и Clash Meta for Android.

Крупный branded APK обычно означает собственные UI, аккаунт, оплату, routing UX,
`VpnService` и update channel. Он редко означает собственное сетевое ядро. В
разобранных APK чаще найден sing-box/libbox fork или Xray wrapper. Это нормальная
архитектура, а не признак «ненастоящего» клиента.

Для POKROV разумный путь тот же: оставить собственный клиент и host networking,
а разрешенный Hiddify Core держать как заменяемый backend. Оснований брать чужой
готовый app или чужой product fork вместо Hiddify нет.

## Store-scale generic clients

Google Play install tiers лучше GitHub stars показывают массовую дистрибуцию, но
тоже не равны monthly active users. Самая важная деталь: большие generic clients
не продают сервер сами; многие VPN-сервисы просто отдают пользователю subscription
для импорта в них.

| Android client | Google Play tier | Core/family | Что это доказывает |
| --- | ---: | --- | --- |
| [Happ](https://play.google.com/store/apps/details?id=com.happproxy) | `10M+` | Xray для VLESS/Reality; отдельный Hysteria2 support | Xray-клиент может быть таким же массовым, как Hiddify; [официальный repo](https://github.com/Happ-proxy/happ-android) называет Xray core |
| [v2RayTun](https://play.google.com/store/apps/details?id=com.v2raytun.android) | `10M+` | V2Ray/Xray family, Reality | Очень большой closed/product client; это не evidence в пользу sing-box |
| [Hiddify](https://play.google.com/store/apps/details?id=app.hiddify.com) | `5M+` | Hiddify fork поверх sing-box | Forked sing-box — доказанно массовая production-линия |
| [Amnezia VPN](https://play.google.com/store/apps/details?id=org.amnezia.vpn) | `5M+` | Multi-protocol: AWG/WireGuard/OpenVPN/Xray и другие | Собственный оркестратор может быть массовым, но его ширина нам не нужна |

На Apple отдельная большая proprietary линия —
[Shadowrocket](https://apps.apple.com/us/app/shadowrocket/id932747118): 12k ratings
на дату среза и широкий набор V2Ray/Clash/WireGuard/Hysteria/AWG/MASQUE-like
capabilities. Это полезный UX/compatibility comparator, но не исходный код и не
Android APK base.

## Крупные публичные клиенты

GitHub stars ниже округлены на дату среза. Это только публичный сигнал масштаба
developer/user community, не число активных установок.

| Клиент | Публичный сигнал | Что внутри | Чистый upstream? | Значение для POKROV |
| --- | ---: | --- | --- | --- |
| [v2rayN](https://github.com/2dust/v2rayN) | ~112k stars, desktop | Xray, sing-box и несколько engines | Нет, multi-core shell | Сильный desktop reference, не Android base |
| [v2rayNG](https://github.com/2dust/v2rayNG) | ~60k stars, Android | Xray/V2Fly | Не sing-box | Главная зрелая Xray-линия; полезна только при решении добавить XHTTP/Xray |
| [FlClash](https://github.com/chen08209/FlClash) | ~46k stars, Android/desktop | Mihomo/Clash Meta | Не sing-box | Альтернативная config/runtime family, не shortcut для нашей миграции |
| [Clash Meta for Android](https://github.com/MetaCubeX/ClashMetaForAndroid) | ~43k stars, Android | Mihomo/Clash Meta | Не sing-box | Доказывает масштаб Clash-линии; перед новым использованием нужен отдельный maintenance review |
| [Hiddify](https://github.com/hiddify/hiddify-app) | ~32k stars, cross-platform | Hiddify fork поверх sing-box | Нет | Ближайшая к текущему POKROV backend-линия |
| [NekoBox for Android](https://github.com/MatsuriDayo/NekoBoxForAndroid) | ~22k stars, Android | `MatsuriDayo/sing-box` | Нет | Популярный пример продукта на собственном fork; брать его fork нам незачем |
| [Karing](https://github.com/KaringX/karing) | ~14k stars, cross-platform | modified `KaringX/sing-box` | Нет | Еще один пример, что shipping clients держат patch stack |
| [Amnezia Client](https://github.com/amnezia-vpn/amnezia-client) | ~13k stars, cross-platform | OpenVPN, WireGuard, AWG, Xray, Cloak и другие | Нет, multi-protocol orchestrator | Reference для AWG и multi-protocol UX; слишком широкий base для POKROV |
| [sing-box for Android](https://github.com/SagerNet/sing-box-for-android) | ~1k stars, Android | upstream sing-box/libbox | Да, ближайший вариант | Лучший upstream reference и Plan B, но не white-label SDK |
| [sing-box for Apple platforms](https://github.com/SagerNet/sing-box-for-apple) | ~1k stars, Apple | upstream sing-box/libbox | Да, ближайший вариант | Reference для current libbox API и Apple lifecycle |
| [Lantern / Radiance](https://github.com/getlantern/radiance) | Малый недавно открытый backend repo, но зрелый продукт | Forked sing-box + Outline SDK + AWG + Geneva + WATER/WASM | Нет, собственный backend/orchestrator | Лучший открытый reference модели «наш backend + стандартный core + specialist dialers» |

Проверка fork ownership:

- Karing прямо указывает modified sing-box core и свой
  [`KaringX/sing-box`](https://github.com/KaringX/sing-box);
- build script NekoBox забирает
  [`MatsuriDayo/sing-box`](https://github.com/MatsuriDayo/sing-box), а не чистый
  `SagerNet/sing-box`;
- Hiddify `v4.1.0` заменяет upstream module локальным `hiddify-sing-box`
  submodule: см. [`go.mod`](https://github.com/hiddify/hiddify-core/blob/v4.1.0/go.mod).

Mihomo — отдельная Clash-линия, не форк sing-box. Совпадение части Go libraries и
protocol support не делает их одним core.

## Что найдено в branded APK

Это static evidence конкретных файлов, а не догадка по маркетинговому сайту.

| APK | Shell/продукт | Найденное ядро | Evidence | Вывод |
| --- | --- | --- | --- | --- |
| Quattro `0.18.1` | Собственный Flutter APK | `libnpvpnBox.so`, SagerNet/sing-box traces | `PASS_STATIC` | Branded client поверх sing-box-derived core |
| HiroVPN `1.17.1` | Собственный Flutter APK, billing/store stack | `libv2jni.so`, Xray/V2Ray, `hev-socks5-tunnel` | `PASS_STATIC` | Собственный продукт поверх Xray |
| ByeByeDPI `1.7.6` | Utility APK | `byedpi` + `hev-socks5-tunnel` | `PASS_STATIC` | Локальный DPI workaround, не managed VPN core |
| OverSecure `1.1.7` | Собственный subscription APK | `libbox.so`, SagerNet/sing-box traces | `PASS_STATIC_LOCAL_CONCURRENT` | Еще один коммерческий shell поверх sing-box-derived core |
| Kubik `1.2.4` | Собственный Flutter APK | sing-box `libbox.so` | `PASS_STATIC_LOCAL_CONCURRENT` | Свой APK, чужое ядро; trust портят debug signing и ad-tech, а не выбор core |
| MantaRay `2.25.8` | BYO-config APK с сильным routing UX | first-party `libmantaray_core.so`, FFI marker `5.13.1` | `PASS_STATIC_LOCAL_CONCURRENT` | Underlying engine по static evidence не установлен; нельзя приписывать sing-box |

Коммитный источник первой выборки:
[`apk-competitor-static-analysis.md`](../telegram-vpn-2026-07-09/apk-competitor-static-analysis.md).
Вторая выборка находится в concurrent platform worktree по пути
`docs/competitive/telegram-vpn-2026-07-12/telegram-vpn-wave2-and-apk-analysis.md`;
этот research ее не перемещал и не коммитил.

В market research также есть большие branded Android surfaces: HitRay/HitVPN,
Sota Connect, Batya, Atlanta и другие. Для них публичный install tier подтверждает
масштаб дистрибуции, но не конкретный core. Пока APK/source не разобран, писать
«у них sing-box» или «у них свой протокол» нельзя.

## Чистый sing-box или fork

### Чистый upstream

Плюсы:

- короче supply chain и понятнее upstream delta;
- быстрее security/bugfix updates;
- меньше скрытой config transformation;
- официальные libbox examples для Android и Apple.

Цена для POKROV:

- свой Windows C ABI и artifact pipeline;
- свой mobile lifecycle/command-service adapter;
- самостоятельная config conversion/migration;
- отдельная интеграция Hiddify-specific AWG/WARP/Naive build decisions;
- больше тестов и больше platform ownership сразу.

### Product fork

Плюсы:

- готовые cross-platform builds и protocol/build-tag bundle;
- уже решенная часть platform glue;
- можно держать POKROV-specific security и ABI fixes без ожидания upstream.

Цена:

- каждое обновление — upstream reconciliation/backport review и differential tests;
- fork может отставать от upstream;
- лишние control/config surfaces приходится отключать;
- воспроизводимая сборка и SBOM становятся нашей обязанностью.

Сам fork не проблема. Проблема — непинованный fork без списка patches, owner и
регулярного update/backport budget. Для большой продуктовой дельты blanket rebase
может быть опаснее контролируемого backport.

## Решение для POKROV

1. Не заменять POKROV client на Hiddify/Karing/NekoBox.
2. Взять Hiddify `v4.1.0` как фиксированную исходную точку для POKROV-owned fork,
   но не ship-ить upstream release binary без аудита и patches.
3. Сохранить exact released Hiddify lineage; построить manifest отсутствующих
   upstream changes до `1.13.14` и backport-ить security/correctness fixes по
   одному. Параллельно измерять, какие Hiddify capabilities реально используются.
4. Спрятать fork за узким versioned `PokrovCoreBackend` contract.
5. Direct upstream sing-box/libbox сохранить как exit path и compatibility spike,
   не тащить второй production core параллельно.
6. Сначала проверить shipped Hiddify XHTTP против exact Xray server; libXray
   добавлять только после измеренного gap. Mihomo не добавлять без решения сменить
   всю config/runtime family.

Конкретный Hiddify patch stack и release gates:
[`hiddify-v4-hardening.md`](hiddify-v4-hardening.md). Exact fork delta и WARP:
[`hiddify-fork-delta.md`](hiddify-fork-delta.md).

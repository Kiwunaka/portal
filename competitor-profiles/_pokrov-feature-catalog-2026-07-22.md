# Справочник функций VPN-рынка и backlog POKROV

**Срез:** 2026-07-22

**Покрытие:** 22 Android-конкурента, их кабинеты, боты, сайты, инструкции, store-поверхности, release-каналы и юридические документы

**Назначение:** единый дедуплицированный список функций и решение, что POKROV должен доказать, добавить, протестировать или отвергнуть

**Связанная сводка:** [сравнительный аудит](./_comparative-synthesis-2026-07-22.md)

**Текущий POKROV:** [канонический feature tracker](../docs/developer/pokrov-canonical-feature-tracker.md), [product contract](../docs/product/portal-vpn-product.md)

## Как читать

Это не список всех стран, серверных строк и текстовых вариаций. Это **335 уникальных типов функций**, найденных в 22 продуктах.

| Метка | Значение |
| --- | --- |
| `PROVE` | Уже есть в коде/контракте POKROV, но нужно доказать на точном release-кандидате или живой среде |
| `MUST` | Обязательный конкурентный или операционный пробел; порядок задаёт shortlist ниже |
| `SHOULD` | Высокая ценность после закрытия базовой надёжности |
| `CAN` | Допустимый эксперимент после core/release gates |
| `NO-GO` | Не копировать даже если у конкурента это конвертит |
| `N/A` | Не отдельная функция POKROV или уже покрыто другой механикой |

**Состав полного каталога:** `PROVE` — 88, `MUST` — 88, `SHOULD` — 83, `CAN` — 65, `NO-GO` — 10, `N/A` — 1. Ниже перед каталогом вынесен короткий исполнимый shortlist, поэтому 88 строк `MUST` не означают один спринт.

Важно: `Retest passed` в POKROV tracker означает локальное автоматизированное доказательство, а не production, store, physical-device или RU-origin `PASS`.

## Решение для POKROV

### P0 — сначала доказать уже построенное

| ID | Что | Почему сейчас | Критерий готовности |
| --- | --- | --- | --- |
| P0-01 | Подписанный Android exact candidate | Quattro и MORI показали цену ABI/signing-бардака; новый публичный POKROV-кандидат сейчас заблокирован signing gate | Production signer, hash, APK identity, clean install, update и physical connect `PASS` |
| P0-02 | Подписанный Windows exact candidate | Текущая публичная история — unsigned beta; новый public sync заблокирован | Trusted signature, clean-VM install/connect/disconnect/uninstall и network restore `PASS` |
| P0-03 | End-to-end connection contract | TipTop и VPN Наружу показали, что зелёный UI и `tun0` не доказывают интернет | До `Подключено`: tunnel + DNS + HTTPS + ожидаемый route; после disconnect обычная сеть работает |
| P0-04 | Реальный `All except RU` | Режим есть в коде, но product canon запрещает считать routing/DNS полностью доказанными | RU-direct, foreign-proxy, split DNS и leak matrix на Android/Windows exact candidate |
| P0-05 | Реальный Selected Apps | Picker, sync и materialization есть в коде, production-поведение ещё owner-gated | Android package picker и Windows process picker доказаны на точных артефактах |
| P0-06 | App-first 5-day trial | Backend/client flow реализован, но live app-session остаётся отдельным доказательством | Чистая установка → trial → профиль → connect без Telegram/карты |
| P0-07 | App/cabinet/bot account parity | Контракты существуют, но реальный session parity остаётся owner-gated | Одна подписка, expiry, устройства, rewards и support совпадают во всех трёх поверхностях |
| P0-08 | Безопасный network teardown | VPN не должен оставлять сломанный DNS/proxy, как TipTop | Crash/kill/update/logout/uninstall возвращают исходную сеть |
| P0-09 | Release hub и provenance | Пользователь должен отличать настоящий APK/EXE от подделки | Одна страница: current version, channel, hashes, signer, size, mirrors, changelog, incident state |
| P0-10 | Синхронизация product facts | Platform truth говорит `+5 дней` новым пользователям, client contract всё ещё содержит `+10` | Shared facts, app, site, bot, cabinet и docs показывают одну текущую величину |

### P0/P1 — обязательно добавить или закончить

| ID | Функция | Сейчас в POKROV | Что сделать |
| --- | --- | --- | --- |
| MUST-01 | Проверяемый connection status | Частично | Показывать DNS/HTTPS/route health, а не только runtime state |
| MUST-02 | Одна кнопка «Починить соединение» | Нет как законченного ladder | Recheck → endpoint → transport → refresh profile → alternate route → safe reset |
| MUST-03 | Offline/cached shell | Частично | Home, последний маршрут, diagnostics и status доступны при падении bootstrap API |
| MUST-04 | Purpose routes | Частично: RU-direct и selected apps | Добавить Video/YouTube, AI, Social, Games и aggressive bypass как backend-owned presets |
| MUST-05 | Объяснение route decision | Нет | Для домена/приложения показать `напрямую` или `через POKROV` и причину |
| MUST-06 | Favorites + Recent | Нет в текущем каноне | Избранные и недавно успешные локации рядом с Auto |
| MUST-07 | Честный ping/load/health | Частично: shortlist/capacity внутри | Показать только измеренные значения с freshness; не рисовать fake metrics |
| MUST-08 | Incident inbox | Частично: notifications/live updates | Единый in-app список outage, compensation, release и required action |
| MUST-09 | Автокомпенсация | Backend primitives есть частично | Массовый подтверждённый incident автоматически создаёт account-owned grant |
| MUST-10 | Trust/responsibility map | Нет одной страницы | Brand owner, operator, controller, seller, payment agent, publisher, signer, infrastructure processors |
| MUST-11 | Field-level privacy table | Нет полной пользовательской таблицы | Поле → цель → retention → processor → delete/export path |
| MUST-12 | Pre-auth support/status | Частично через public surfaces | FAQ, status и диагностика установки доступны до account bootstrap |
| MUST-13 | Официальная fallback-client matrix | Есть Hiddify/Happ compatibility | Поддерживаемый клиент × платформа × формат × проверенная версия × инструкция |
| MUST-14 | Server/route taxonomy | Частично | `Обычный / Белый список / Усиленный обход / Multihop` без протокольного жаргона |
| MUST-15 | Release smoke по ABI/host | Частично в gates | First frame + trial + connect + disconnect для каждой публикуемой ABI/OS |

### P1 — стоит добавить после P0

| ID | Функция | Источник идеи | Условие |
| --- | --- | --- | --- |
| SHOULD-01 | Per-domain direct/VPN override | VPN Наружу, AdGuard, Hiro | После стабильного domain rules engine |
| SHOULD-02 | Custom domain/IP/subnet rules | Vanya, Hiro, Red Shield | В Advanced; safe validation и rollback |
| SHOULD-03 | DNS presets + custom DNS | AdGuard, Hiro, Red Shield | После split-DNS/leak proof |
| SHOULD-04 | Kill Switch / Always-on guide | Proton, AdGuard, Kakadu | Только с recovery и platform-specific warning |
| SHOULD-05 | Trusted Wi-Fi automation | CyberGhost | После стабильного lifecycle/background runtime |
| SHOULD-06 | QR/code pairing второго устройства | Kakadu, MORI, Космос | Одноразовый код, expiry, revoke, audit trail |
| SHOULD-07 | Android TV continuation | Космос, Батя, VPN Наружу | QR login, real TV navigation и store/direct provenance |
| SHOULD-08 | Router profile wizard | VPN Наружу, GnuVPN | Не просить router credentials на стороннем сайте |
| SHOULD-09 | Referral center | Hiro, 4ebur, Durev | Текущую backend referral механику довести до balance/history/status UI |
| SHOULD-10 | Partner/affiliate cabinet | Hiro, Durev, Quattro | Выплата только с collected revenue после refund hold |
| SHOULD-11 | Gifts and team packs | VPN Наружу, Red Shield | Bulk codes, expiry, owner/redeem audit, clear refund rule |
| SHOULD-12 | Campaign attribution | Quattro, MORI, Telegram-first продукты | First-party source tags, без утечки private tokens |
| SHOULD-13 | Competitor-switch offer | Hiro | Ручная приватная проверка и ограниченная скидка |
| SHOULD-14 | Research rewards | VPN Наружу | Награда за интервью/опрос/качественный bug report, не за рейтинг |
| SHOULD-15 | Server cost labels | Quattro | Только если маршруты реально имеют разную себестоимость; понятный остаток/коэффициент |
| SHOULD-16 | Protection history | ExpressVPN | Локальные безопасные события: connect, route change, blocked failure, recovery |
| SHOULD-17 | Post-connect shortcuts | Proton, ExpressVPN | Только пользовательские shortcuts, без рекламы |
| SHOULD-18 | Local network access toggle | Red Shield | Platform proof и ясное объяснение риска |
| SHOULD-19 | Quick Settings / tray connect | Kakadu, Lagom | Никогда не делать обязательным условием первого запуска |
| SHOULD-20 | Config/profile refresh self-service | Quattro, Vanya, MORI | Idempotent refresh без ручного удаления приложения |

### P2 — можно экспериментировать позже

| ID | Функция | Решение |
| --- | --- | --- |
| CAN-01 | Wheel | Backend уже есть за флагом; включать только после odds/ledger/abuse/release proof |
| CAN-02 | Activity calendar/streak | Backend уже есть за флагом; награда за retention, не за публичные действия |
| CAN-03 | Achievements/levels | Можно как навигацию по полезным действиям, не как шум |
| CAN-04 | Quests | Первый tunnel, второй device, обучение routing, качественный feedback |
| CAN-05 | Reserve traffic / emergency allowance | Может спасать при expiry/quota; нужна ясная экономика |
| CAN-06 | Multihop / Secure Core | После базовой скорости, route health и capacity proof |
| CAN-07 | Tor route | Только при реальном отдельном threat model и измеренной работе |
| CAN-08 | Dedicated IP | После спроса от банков/B2B и abuse/payment модели |
| CAN-09 | Streaming/P2P/gaming locations | После автоматического health-check конкретного сценария |
| CAN-10 | Android TV first-party app | После Android phone и Windows release maturity |
| CAN-11 | Browser extension | Только если есть отдельная browser-routing ценность |
| CAN-12 | Linux package | Уже roadmap после Android/Windows gates |
| CAN-13 | iOS/macOS | Только после signing/TestFlight/notarization evidence |
| CAN-14 | eSIM/router cross-sell | Не раньше стабильного core и подтверждённого спроса |
| CAN-15 | Security tools bundle | Только реальные поддерживаемые инструменты; не раздувать VPN ради paywall |

### NO-GO

| ID | Не копировать | Где встречалось |
| --- | --- | --- |
| NO-01 | Награда за 5★, отзыв, helpful vote или публичный пост | Hiro, Огонь, Батя, TipTop, MORI |
| NO-02 | Rewarded ad до connect или внутри repair | Pipster |
| NO-03 | Зелёное `Подключено` без DNS/HTTPS/route proof | TipTop, VPN Наружу |
| NO-04 | Debug-signed или ABI-неполный public APK | Quattro, MORI |
| NO-05 | Shared/temporary Apple accounts | Vanya и серые setup-практики |
| NO-06 | Скрытый auto-renew/follow-on price | Vanya, TipTop, Pipster |
| NO-07 | Telegram как единственный cancel/recovery/legal path | Lagom и Telegram-first продукты |
| NO-08 | Fake counters, unsourced reviews, fake urgency | Durev, Ping, Blanc, VPN Наружу |
| NO-09 | Абсолютное `ничего не собираем` при analytics/account processing | Большая часть рынка |
| NO-10 | Raw config/token/endpoint в logcat, support или legal URL | Батя, 4ebur |
| NO-11 | Один бренд для разных приложений без responsibility map | Quattro |
| NO-12 | Сырой каталог из сотен строк без search/filter/health | Quattro |
| NO-13 | Молча игнорируемые тарифы/серверы/кнопки | Quattro и ряд web paywall |
| NO-14 | Функции `скоро` как уже доступные | Hiro, MORI, Blanc, CyberGhost |
| NO-15 | Публикация под разными юрлицами без карты ролей | Quattro, Vanya, Огонь, Батя, VPN Наружу |

## Текущий фундамент POKROV, который не надо строить повторно

По текущему code-derived tracker уже существуют или предусмотрены:

- app-first onboarding и 5-day no-card trial;
- first-launch choice для нового/возвращающегося пользователя;
- activation/redeem code и безопасный restore;
- Android/Windows shell `Protection / Locations / Rules / Profile`;
- connect/disconnect lifecycle, diagnostics и runtime error states;
- Smart Connect shortlist, Auto, backend location catalog и preferred node;
- `All except RU`, `Full tunnel`, `Selected apps`, Android package picker и Windows process picker;
- subscription details, checkout handoff, cabinet handoff, devices и revoke;
- Telegram/email linking, Telegram reward, promo redeem и notifications;
- Rewards Hub, referral summary/history, promo slots, wheel/calendar под feature flags;
- ticket-backed support, attachments, diagnostics preview и optional AI hints;
- Android direct API fallback, managed profile materialization и Windows runtime bridge;
- admin node health, rollout config, campaigns, broadcasts, payment reconciliation, referral queue и support operations.

Главный вывод: POKROV сейчас проигрывает не количеством написанных возможностей, а **release proof, видимой упаковкой, purpose routing и operational distribution**.

## Полный каталог уникальных функций

### A. Первый запуск, доказательство и идентичность

| ID | Функция | Примеры | POKROV |
| --- | --- | --- | --- |
| A-01 | Guest/no-auth Home | Proton, Pipster, 4ebur | `CAN`; POKROV выбрал app-first device account |
| A-02 | Бесплатный connect без карты | Proton, Огонь, GnuVPN, VPN Наружу | `PROVE`; 5-day trial уже канон |
| A-03 | Ежемесячный free quota | Lagom, AdGuard, Pipster | `PROVE`; post-trial 5 GB/month уже канон |
| A-04 | Free speed cap вместо полного отключения | AdGuard, POKROV free-soft | `PROVE` |
| A-05 | Платный мини-trial с auto-renew | Vanya, Lagom, Pipster | `NO-GO` как default; POKROV no-card лучше |
| A-06 | Anonymous device-bound account | Огонь, 4ebur | `N/A`; install/account foundation уже есть |
| A-07 | Email OTP | Космос, Blanc, VPN Наружу | `PROVE`; additive continuation уже есть |
| A-08 | Google/Apple/Facebook OAuth | Hiro, AdGuard, Lagom | `CAN`; только если снижает friction без auth-wall |
| A-09 | Telegram login | Kakadu, Lagom, Durev | `SHOULD` только как optional link/fallback |
| A-10 | Activation/access code | MORI, POKROV, gift/key продукты | `PROVE` |
| A-11 | Raw subscription/key import | Vanya, Durev, generic Quattro Play client | `SHOULD` только в explicit compatibility/advanced |
| A-12 | QR import | Quattro Play, generic clients | `SHOULD` только manual fallback |
| A-13 | QR/code login второго устройства | Kakadu, MORI, Космос | `SHOULD` |
| A-14 | Account explainer at friction | Lagom | `MUST` для каждого auth/link шага |
| A-15 | Pre-auth FAQ/support | Lagom, AdGuard | `MUST` |
| A-16 | Pre-auth pricing/server preview | AdGuard, 4ebur | `MUST` без раскрытия private topology |
| A-17 | Consent gate | Proton, Express, CyberGhost, AdGuard | `PROVE`; обязательное отдельно от optional telemetry |
| A-18 | Optional analytics off by default | AdGuard | `SHOULD` как эталон согласия |
| A-19 | Notification soft ask before OS prompt | Proton, AdGuard | `SHOULD` |
| A-20 | Feature micro-tutorials | Hiro, Express, CyberGhost | `SHOULD`; коротко в момент открытия функции |
| A-21 | Competitor-switch offer | Hiro | `SHOULD` после core proof |
| A-22 | Campaign/referral deep-link attribution | Quattro, Telegram-first продукты | `SHOULD`; server-owned, no private token leakage |

### B. Home и состояние подключения

| ID | Функция | Примеры | POKROV |
| --- | --- | --- | --- |
| B-01 | Одна большая Connect-кнопка | Почти все | `PROVE` |
| B-02 | Ясные Connecting/Connected/Disconnecting/Off states | Proton, Express, POKROV | `PROVE` |
| B-03 | Session timer | Hiro, многие mature VPN | `SHOULD` |
| B-04 | Текущая страна/город | Большинство | `PROVE` |
| B-05 | Human route category | Огонь, 4ebur, Quattro | `MUST` |
| B-06 | Protocol/transport details | Proton, Red Shield, AdGuard | `SHOULD` в details/advanced, не на главном экране |
| B-07 | Traffic counters | Proton, Express, POKROV stats contract | `PROVE`; только реальные значения |
| B-08 | IP-change proof | Express | `SHOULD`; masked by default |
| B-09 | DNS/HTTPS/route health | В основном отсутствует; аудит выявил пробел рынка | `MUST` |
| B-10 | Protection history | Express | `SHOULD` |
| B-11 | Auto/Fastest | Proton, Hiro, Огонь, POKROV | `PROVE` |
| B-12 | Search locations | Hiro, Blanc, Proton, POKROV | `PROVE` |
| B-13 | Favorites | Hiro, Proton, Kakadu, MORI | `MUST` |
| B-14 | Recent locations | Express, MORI | `MUST` |
| B-15 | Ping/latency | Blanc, MORI, POKROV shortlist | `MUST` с freshness |
| B-16 | Load/capacity | 4ebur, POKROV backend | `MUST` только как measured state |
| B-17 | Server health/availability | POKROV backend, mature status systems | `MUST` |
| B-18 | Free/Premium lock labels | AdGuard, 4ebur, Pipster | `SHOULD` |
| B-19 | Post-connect shortcuts | Proton, Express | `CAN` |
| B-20 | Quick Settings tile / tray | Kakadu, Lagom, Windows clients | `SHOULD` после lifecycle proof |
| B-21 | Auto-connect | CyberGhost, Kakadu | `SHOULD` как explicit user setting |
| B-22 | Auto-reconnect | Proton, mature clients | `MUST` с bounded retry |
| B-23 | Connection notification | Android VPN-клиенты | `PROVE` |
| B-24 | Mini incident/promo inbox | Космос, Pipster, POKROV notices | `MUST` для incident/release; promo отдельно |

### C. Маршрутизация и anti-blocking

| ID | Функция | Примеры | POKROV |
| --- | --- | --- | --- |
| C-01 | Full tunnel | Все power clients | `PROVE` |
| C-02 | All except RU / RU-direct | VPN Наружу, Lagom, Огонь, POKROV | `PROVE` |
| C-03 | Only selected apps | POKROV, Red Shield, AdGuard, Hiro | `PROVE` |
| C-04 | Exclude selected apps | AdGuard, Red Shield, Hiro | `SHOULD` |
| C-05 | Android installed-app picker | POKROV, AdGuard, Red Shield | `PROVE` |
| C-06 | Windows process/EXE picker | POKROV target, desktop clients | `PROVE` |
| C-07 | Domain split tunneling | AdGuard, Hiro, Vanya | `SHOULD` |
| C-08 | Custom domain/URL rule | Vanya, Ping official materials | `SHOULD` |
| C-09 | Custom IP/subnet rule | Vanya | `SHOULD` |
| C-10 | Per-domain direct/VPN override | VPN Наружу opportunity, AdGuard | `SHOULD` |
| C-11 | Visible route decision/reason | Рынком почти не сделано | `MUST`; сильный differentiator |
| C-12 | Banking/state direct preset | Lagom, Огонь, VPN Наружу | `MUST` |
| C-13 | Marketplace/local-services direct preset | Огонь, POKROV rule direction | `MUST` |
| C-14 | Video/YouTube route | Огонь, Hiro, Lagom | `MUST` |
| C-15 | Social route | TipTop, Огонь, Hiro | `MUST` |
| C-16 | AI/Gemini route | Батя, Durev, Quattro | `MUST` |
| C-17 | Games/Roblox route | Огонь, Durev, Quattro | `MUST` |
| C-18 | Streaming route | CyberGhost, Express, Proton | `CAN` после scenario health |
| C-19 | P2P/Torrent route | Proton, CyberGhost, Quattro | `CAN` с AUP/capacity |
| C-20 | Ad-free YouTube route | Lagom | `CAN`; высокий claim/maintenance risk |
| C-21 | Russia location for users abroad | Lagom, VPN Перемен | `CAN` после jurisdiction/capacity review |
| C-22 | White-list survival route | 4ebur, Durev, Blanc | `MUST` как named anti-block mode |
| C-23 | Aggressive DPI bypass | 4ebur, Blanc, Red Shield | `MUST` после автоматического health selection |
| C-24 | Multihost/intermediate hop | 4ebur | `SHOULD` |
| C-25 | Multihop | Vanya, MORI, Proton Secure Core | `CAN` |
| C-26 | Tor route | Proton, MORI | `CAN` |
| C-27 | LTE/mobile-operator route | Батя, Quattro | `CAN`; только после реального carrier evidence |
| C-28 | Cost coefficient per route | Quattro | `SHOULD` только при реальной usage economics |
| C-29 | Ordinary/special route grouping | Red Shield, Quattro, 4ebur | `MUST` |
| C-30 | Separate task-specific profiles/keys | Durev, Quattro | `SHOULD`; POKROV лучше выдавать presets одной account identity |
| C-31 | Remote geosite/geoip/rules updates | 4ebur, Ping, POKROV ruleset versioning | `PROVE` |
| C-32 | Local-network access | Red Shield | `SHOULD` |
| C-33 | Hotspot/Wi-Fi sharing | Red Shield | `CAN` |
| C-34 | Router routing profile | VPN Наружу, GnuVPN | `SHOULD` |

### D. Протоколы, transport и DNS

| ID | Функция | Примеры | POKROV |
| --- | --- | --- | --- |
| D-01 | sing-box runtime | POKROV, Quattro-class clients | `PROVE`; текущий default core |
| D-02 | xray fallback | POKROV, 4ebur, VLESS clients | `PROVE`; только Advanced/compatibility |
| D-03 | VLESS/Reality | Батя, Durev, 4ebur, Quattro, MORI | `PROVE`; не выводить жаргон в first layer |
| D-04 | VMess/Trojan/Shadowsocks | Quattro Play/client stacks | `CAN` как compatibility formats |
| D-05 | WireGuard | Proton, generic clients | `CAN` при отдельной operational необходимости |
| D-06 | AmneziaWG | GnuVPN, 4ebur, VPN Наружу | `SHOULD` как anti-block fallback после proof |
| D-07 | OpenVPN | GnuVPN, mature global VPN | `CAN` для legacy/router compatibility |
| D-08 | SoftEther | GnuVPN | `CAN`; низкий приоритет |
| D-09 | Hysteria2 | Quattro | `SHOULD` как отдельный fallback, если проходит censorship smoke |
| D-10 | Proprietary/open protocol | Lightway, TrustTunnel, RedLink | `CAN`; не изобретать без конкретного выигрыша |
| D-11 | Stealth/obfuscation | Proton, Express, MORI | `SHOULD` как outcome, не marketing magic |
| D-12 | Automatic transport selection | AdGuard HTTP/2/QUIC, smart clients | `MUST`; backend/client выбирают по health |
| D-13 | SNI/WS/gRPC/XHTTP variants | Quattro, xray clients | `SHOULD` скрыто за Auto/diagnostics |
| D-14 | Custom DNS | AdGuard, Hiro, Red Shield | `SHOULD` в Advanced |
| D-15 | Curated DNS presets | AdGuard | `SHOULD` |
| D-16 | Family/content DNS | AdGuard, CyberGhost | `CAN` как отдельная policy feature |
| D-17 | Split DNS by route mode | POKROV target, Smart-mode products | `MUST` и leak-tested |
| D-18 | IPv4/IPv6 strategy | Quattro, Red Shield | `SHOULD` в Advanced |
| D-19 | IPv6 support/toggle | Power clients | `SHOULD` после leak proof |
| D-20 | Kill Switch | Proton, Express, AdGuard, MORI | `SHOULD` после safe recovery |
| D-21 | Android Always-on/lockdown guide | Kakadu, AdGuard | `SHOULD`; объяснить конфликт с exclusions |
| D-22 | Trusted/untrusted Wi-Fi automation | CyberGhost | `SHOULD` позже |
| D-23 | VPN / local SOCKS5 / integration mode | AdGuard | `CAN`; power-user only |
| D-24 | Local proxy/PAC mode | Pipster, advanced clients | `CAN`; не основной consumer path |
| D-25 | WARP layer | POKROV target | `PROVE` только exact release-build tests |
| D-26 | Post-quantum claim/protection | AdGuard, MORI | `CAN`; только узкое техническое определение и audit |
| D-27 | Ad/tracker/malware blocking | Express, CyberGhost, Red Shield | `CAN` после VPN core |
| D-28 | Category content filters | Red Shield, CyberGhost | `CAN` |
| D-29 | Custom server/import | GnuVPN, generic Quattro, POKROV Advanced | `SHOULD` как explicit recovery/compatibility |
| D-30 | Dedicated IP | CyberGhost, MORI | `CAN` после demand/abuse/payment model |

### E. Ошибки, восстановление и support

| ID | Функция | Примеры | POKROV |
| --- | --- | --- | --- |
| E-01 | Human-readable error | Vanya, POKROV contract | `PROVE` |
| E-02 | Retry current route | Все mature clients | `PROVE` |
| E-03 | Switch endpoint/server | VPN Наружу, Vanya, Blanc | `MUST` |
| E-04 | Switch transport/protocol | Vanya, Blanc, AdGuard | `MUST` автоматизированно |
| E-05 | Refresh profile/subscription | Quattro, MORI, Vanya | `MUST` |
| E-06 | Rotate compromised link/key | POKROV bot, Vanya | `PROVE`; explicit recovery only |
| E-07 | Multihop/alternate path fallback | Vanya, 4ebur | `SHOULD` |
| E-08 | One-button staged repair | Vanya | `MUST` |
| E-09 | Restore ordinary network | TipTop failure lesson | `MUST` |
| E-10 | Offline cached UI | Ping/Batya failure lesson | `MUST` |
| E-11 | Safe diagnostics sheet | POKROV, AdGuard | `PROVE` |
| E-12 | Diagnostic preview before send | POKROV | `PROVE` |
| E-13 | Redacted logs | POKROV, AdGuard | `PROVE` |
| E-14 | Support/device code | VPN Наружу, Батя-style support | `SHOULD`; short-lived and non-secret |
| E-15 | Pre-auth FAQ | Lagom, AdGuard | `MUST` |
| E-16 | Searchable knowledge base | Blanc, Proton, Express | `SHOULD` |
| E-17 | Platform install guides | Quattro, VPN Наружу, 4ebur | `MUST` |
| E-18 | Routing guides | Quattro, Blanc | `MUST` |
| E-19 | Real ticket lifecycle | POKROV, mature support | `PROVE` |
| E-20 | Embedded live chat | Lagom, VPN Наружу | `CAN`; только если реально staffed |
| E-21 | Support bot | POKROV, Quattro, VPN Наружу | `PROVE` |
| E-22 | Support email | AdGuard, POKROV | `PROVE` delivery/readiness |
| E-23 | Optional AI support hint | POKROV | `PROVE`; human ticket stays open |
| E-24 | Public status page/channel | Quattro, Огонь, Батя, VPN Наружу | `MUST` |
| E-25 | In-app outage banner | Космос, POKROV live updates | `MUST` |
| E-26 | Automatic service-day compensation | Космос, MORI, VPN Наружу | `MUST` after incident authority |
| E-27 | Alternative-client fallback | Quattro, Durev, GnuVPN | `MUST` |
| E-28 | Required/optional update state | POKROV, AdGuard | `PROVE` |
| E-29 | Server-change quota disclosure | VPN Наружу lesson | `MUST` if any quota exists |

### F. Account, devices and cross-device continuity

| ID | Функция | Примеры | POKROV |
| --- | --- | --- | --- |
| F-01 | One account across app/web/bot | Quattro, AdGuard, POKROV | `PROVE` live parity |
| F-02 | Email linking | POKROV, AdGuard | `PROVE` |
| F-03 | Telegram linking | POKROV, Космос, Quattro | `PROVE` |
| F-04 | OAuth account linking | AdGuard, Lagom | `CAN` |
| F-05 | Device list | POKROV, Kakadu, Red Shield | `PROVE` |
| F-06 | Device revoke | POKROV, Kakadu | `PROVE` |
| F-07 | Active session list | 4ebur, Kakadu | `SHOULD` web + device sessions separately |
| F-08 | Revoke other web sessions | 4ebur | `SHOULD` |
| F-09 | Concurrent-connection counter | AdGuard, POKROV backend | `SHOULD` user-safe |
| F-10 | Family members/subaccounts | Kakadu | `CAN` after account foundation production proof |
| F-11 | Extra device slot purchase | POKROV bot, Quattro tariff axis | `SHOULD` |
| F-12 | QR TV login | Космос, Kakadu, MORI | `SHOULD` |
| F-13 | Short code login | Kakadu, MORI | `SHOULD` |
| F-14 | Restore purchases | AdGuard, 4ebur | `SHOULD` for store lanes only |
| F-15 | Key/subscription recovery | Durev, Vanya, 4ebur | `PROVE` through code/account recovery |
| F-16 | Email 2FA | Quattro | `CAN`; not a substitute for session security |
| F-17 | Account deletion | AdGuard and store-required flows | `MUST` before store expansion |
| F-18 | Data export/access request | Mature privacy programs | `SHOULD` |
| F-19 | Receipts/payment history | Mature cabinets, POKROV payment ledger | `SHOULD` consumer view |
| F-20 | Cross-platform download hub | Proton, Express, Quattro, POKROV | `MUST` |

### G. Тарифы, оплата и entitlement

| ID | Функция | Примеры | POKROV |
| --- | --- | --- | --- |
| G-01 | Monthly plan | Почти все | `PROVE` through current catalog |
| G-02 | 3/6/12/24-month plans | Lagom, VPN Наружу, 4ebur, MORI | `SHOULD` only from backend facts |
| G-03 | Lifetime plan | Батя and legacy offers | `NO-GO` without sustainable capacity model |
| G-04 | One-time activation key | POKROV, MORI | `PROVE` |
| G-05 | No auto-renew | POKROV activation keys | `PROVE` and market aggressively |
| G-06 | Optional auto-renew off by default | VPN Наружу | `CAN` if subscriptions are introduced |
| G-07 | Store subscription billing | AdGuard, global VPNs | `CAN` only with store readiness |
| G-08 | SBP | Quattro, VPN Наружу, 4ebur | `PROVE` supported checkout path |
| G-09 | Russian bank card | Quattro, VPN Наружу, AdGuard web | `PROVE` current provider truth |
| G-10 | Foreign card | VPN Наружу | `CAN` after merchant/legal setup |
| G-11 | Cryptocurrency | Quattro, VPN Наружу, 4ebur, MORI | `CAN`; compliance and reconciliation first |
| G-12 | Telegram Stars | POKROV bot | `PROVE` |
| G-13 | Plan comparison | Hiro, AdGuard, CyberGhost | `MUST` concise and fact-fed |
| G-14 | Device count as pricing axis | Quattro | `SHOULD` only if simple plan limit is insufficient |
| G-15 | Metered special traffic | Quattro LTE | `CAN`; high explanation/support cost |
| G-16 | Traffic add-on | Quattro | `CAN` |
| G-17 | Free monthly quota | Lagom, AdGuard, POKROV | `PROVE` |
| G-18 | Paid unlimited traffic | Most paid VPNs, POKROV | `PROVE` within AUP/capacity truth |
| G-19 | Free speed cap | AdGuard, POKROV free-soft | `PROVE` |
| G-20 | Family/team plan | Kakadu, VPN Наружу | `CAN` |
| G-21 | Gift cards/codes | POKROV, VPN Наружу, Red Shield | `PROVE` current gift path; improve UX |
| G-22 | Promo codes | POKROV, Quattro, Космос | `PROVE` |
| G-23 | Competitor-switch discount | Hiro | `SHOULD` |
| G-24 | Exit/cancel retention offer | Vanya, Express | `CAN`; never obstruct cancellation |
| G-25 | Refund window and status | Global VPNs | `MUST` before checkout, one canonical rule |
| G-26 | Purchase/renewal status | POKROV, mature cabinets | `PROVE` |
| G-27 | Payment reconciliation/manual review | POKROV admin | `PROVE` operator flow |
| G-28 | Refund/chargeback entitlement reversal | POKROV backend | `PROVE` provider/live evidence |

### H. Referral, rewards and retention

| ID | Функция | Примеры | POKROV |
| --- | --- | --- | --- |
| H-01 | Fixed days for friend | POKROV, Blanc, CyberGhost | `PROVE` |
| H-02 | Fixed days for referrer after payment | POKROV, Red Shield | `PROVE` |
| H-03 | Reward hold after payment/refund window | POKROV | `PROVE`; correct anti-abuse model |
| H-04 | Recurring percentage | 4ebur, Durev | `SHOULD` only in partner program, not casual referral |
| H-05 | Cash or VPN-days payout | Durev, Hiro | `SHOULD` for verified affiliates |
| H-06 | Referral dashboard | 4ebur, Quattro, POKROV backend | `MUST` UI: status, history, reward, conversion |
| H-07 | Partner/affiliate dashboard | Hiro, Quattro | `SHOULD` |
| H-08 | Campaign/start-link attribution | Quattro, POKROV admin | `PROVE` and surface reporting |
| H-09 | Promo slots | POKROV, Quattro | `PROVE`; first-party only |
| H-10 | In-app inbox/push | Космос, GnuVPN, POKROV | `MUST` for operations; marketing opt-in |
| H-11 | Wheel/roulette | Hiro, POKROV gated | `CAN` after transparent state/ledger |
| H-12 | Activity calendar | Hiro, POKROV gated | `CAN` |
| H-13 | Streak | Hiro, MORI, POKROV direction | `CAN` |
| H-14 | Achievements | Hiro, MORI, POKROV bot | `CAN` |
| H-15 | Levels/loyalty tier | Hiro, POKROV admin loyalty | `CAN` |
| H-16 | Reserve traffic/emergency balance | Hiro | `CAN` |
| H-17 | Product quests | Hiro, TipTop | `CAN` only for verified product actions |
| H-18 | Reward for second device | AdGuard quota mechanic | `CAN` |
| H-19 | Rewarded research/interview | VPN Наружу | `SHOULD` |
| H-20 | Rewarded bug report/feedback quality | Hiro-style opportunity | `SHOULD` |
| H-21 | Giveaways | Батя, Огонь, VPN Наружу, MORI | `CAN`; clear rules and privacy |
| H-22 | Gift/team code campaigns | VPN Наружу | `SHOULD` |
| H-23 | Competitor-switch campaign | Hiro | `SHOULD` |
| H-24 | Content/education rewards | Hiro | `CAN` |
| H-25 | Hidden easter egg/bonus | Quattro | `CAN` only with explicit eligibility/value |
| H-26 | Review collection/moderation | POKROV, several competitors | `PROVE`; feedback allowed, reward for rating forbidden |
| H-27 | Review/rating reward | Огонь, Батя, TipTop, MORI | `NO-GO` |
| H-28 | Rewarded advertising | Pipster | `NO-GO` |

### I. Контент, коммуникация и обучение

| ID | Функция | Примеры | POKROV |
| --- | --- | --- | --- |
| I-01 | News/status Telegram channel | Quattro, Огонь, Батя, MORI, VPN Наружу | `MUST` как часть owned operations |
| I-02 | Release announcements | Quattro, MORI, AdGuard | `MUST` |
| I-03 | Incident updates | VPN Наружу, Батя, Огонь | `MUST` |
| I-04 | Compensation announcements | Космос, MORI, VPN Наружу | `MUST` |
| I-05 | Educational editorial content | MORI, Proton, Express | `SHOULD` |
| I-06 | Anti-blocking explainers | 4ebur, MORI, Blanc | `SHOULD` |
| I-07 | FAQ inside app | Hiro, Lagom, VPN Наружу | `SHOULD` |
| I-08 | Searchable web help center | Blanc, Proton, Express | `SHOULD` |
| I-09 | Android install guide | Все direct-APK продукты | `MUST` |
| I-10 | Windows install/SmartScreen guide | VPN Наружу, MORI, POKROV | `MUST` with signed-candidate truth |
| I-11 | Android TV guide | Quattro, VPN Наружу, Батя | `SHOULD` when TV lane exists |
| I-12 | Router guide | VPN Наружу, GnuVPN | `SHOULD` |
| I-13 | Manual-client guide | Quattro, Durev, GnuVPN | `MUST` |
| I-14 | Routing examples by app/site | Quattro, AdGuard, Огонь | `MUST` |
| I-15 | Troubleshooting decision tree | Vanya, Blanc | `MUST` |
| I-16 | One promise per store frame | MORI, Lagom, Express | `SHOULD` |
| I-17 | Product UI as proof in marketing | POKROV current direction | `PROVE`; major honest differentiation |
| I-18 | Version history | AdGuard, Proton | `MUST` |
| I-19 | Current supported versions matrix | Cross-platform products | `MUST` |
| I-20 | Public roadmap/waitlist | Hiro | `CAN`; future features clearly labelled |
| I-21 | Service comparison table | MORI, marketing sites | `CAN`; claim-level sources required |
| I-22 | User feedback/review intake | POKROV, store products | `PROVE` |
| I-23 | Masked approved testimonials | POKROV | `PROVE`; no fake counters |

### J. Distribution и release engineering

| ID | Функция | Примеры | POKROV |
| --- | --- | --- | --- |
| J-01 | Google Play | Большинство | `CAN` only after store/signing readiness |
| J-02 | Signed direct APK | AdGuard, Proton, Red Shield | `MUST` |
| J-03 | APK mirrors | Quattro, Red Shield, VPN Наружу | `MUST` with same hash/signer |
| J-04 | GitHub Releases | Proton, POKROV | `PROVE` exact candidate |
| J-05 | F-Droid/open-source distribution | Proton | `CAN` after source/reproducibility decision |
| J-06 | Stable/Beta lanes | Proton, AdGuard, Red Shield | `MUST` |
| J-07 | In-app update prompt | POKROV, AdGuard | `PROVE` |
| J-08 | Forced update only for breaking/security cases | Remote-config products | `SHOULD` with rollback path |
| J-09 | Public changelog | Proton, AdGuard, Quattro | `MUST` |
| J-10 | Hash/size manifest | POKROV target, mature direct downloads | `MUST` |
| J-11 | Public signer fingerprint | Proton-style trust | `MUST` |
| J-12 | Source stamp/provenance | VPN Наружу direct-vs-Play verification | `SHOULD` |
| J-13 | ABI matrix smoke | MORI/Quattro failure lesson | `MUST` |
| J-14 | Cold-start/first-frame smoke | MORI/Quattro/Ping/Lagom lesson | `MUST` |
| J-15 | Connect/disconnect smoke per candidate | Whole audit | `MUST` |
| J-16 | DNS/route/leak smoke per candidate | Whole audit | `MUST` |
| J-17 | Rollback candidate | Mature release programs | `MUST` |
| J-18 | Major release → hotfix cadence | AdGuard, Quattro | `SHOULD` but with quality gate |
| J-19 | Cross-platform coordinated release | Kakadu, global VPNs | `SHOULD` after Android/Windows maturity |
| J-20 | Windows installer | POKROV, VPN Наружу, MORI | `PROVE` signed exact candidate |
| J-21 | Windows portable build | Power-user clients | `CAN`; not first-layer CTA |
| J-22 | Linux packages | Proton, roadmap products | `CAN` after current gates |
| J-23 | TestFlight/App Store | Global VPNs | `CAN` after Apple readiness |
| J-24 | Android TV package | Космос, VPN Наружу | `CAN` after phone maturity |
| J-25 | Browser extension | CyberGhost, 4ebur, Pipster | `CAN` only with distinct use-case |
| J-26 | Router/manual configs | GnuVPN, VPN Наружу | `SHOULD` |
| J-27 | Official destinations directory | Kakadu, Red Shield | `MUST` |
| J-28 | Fake-build warning | Express, Red Shield | `MUST` for direct distribution |
| J-29 | Open protocol/core | Proton, Express Lightway, AdGuard TrustTunnel | `CAN`; strong trust lever, significant cost |
| J-30 | Transparent release verification instructions | Proton, AdGuard | `SHOULD` |

### K. Trust, privacy и юридические функции

| ID | Функция | Примеры | POKROV |
| --- | --- | --- | --- |
| K-01 | Responsibility map | Рынком почти не сделано | `MUST` differentiation |
| K-02 | Named service operator | Mature legal surfaces | `MUST` |
| K-03 | Named data controller | Proton, AdGuard, Express | `MUST` |
| K-04 | Named seller/payment agent | Mature checkout | `MUST` |
| K-05 | Store publisher explanation | Quattro/Vanya failure lesson | `MUST` if entity differs |
| K-06 | Artifact signer explanation | Proton-style trust | `MUST` |
| K-07 | Infrastructure processor disclosure | White-label/cloud services | `MUST` where applicable |
| K-08 | Visible Terms/Privacy consent | AdGuard, store-required flows | `MUST` |
| K-09 | Separate optional analytics consent | AdGuard | `SHOULD` |
| K-10 | Event/field-level privacy inventory | AdGuard detail, POKROV opportunity | `MUST` |
| K-11 | Retention periods | Mature policies | `MUST` |
| K-12 | Account/data deletion route | AdGuard | `MUST` |
| K-13 | Data access/export route | Privacy-rights programs | `SHOULD` |
| K-14 | Processor/subprocessor list | Mature privacy programs | `SHOULD` |
| K-15 | No browsing/activity logs claim | Many competitors | `SHOULD` only in narrowly proven form |
| K-16 | Transparency report | Proton, CyberGhost, Express | `SHOULD` |
| K-17 | Independent audit | Proton, Express, CyberGhost | `CAN` after scope is mature |
| K-18 | Open-source client/protocol | Proton, TrustTunnel, Lightway | `CAN` |
| K-19 | Bug bounty/security contact | Express-style trust programs | `SHOULD` when operationally supportable |
| K-20 | Refund terms before payment | Global VPNs | `MUST` |
| K-21 | One canonical price/plan source | Audit-wide claim drift lesson | `MUST`; shared facts pattern already exists |
| K-22 | Live country/location count truth | Lagom, VPN Наружу, AdGuard contradictions | `MUST`; derive from entitlement/catalog |
| K-23 | Feature availability truth | MORI/Hiro/CyberGhost drift lesson | `MUST`; feature flags feed copy |
| K-24 | Legal document versions/dates | Quattro, mature products | `MUST` |
| K-25 | Secret-free diagnostics | POKROV, Batya failure lesson | `PROVE` |
| K-26 | Public incident archive | Mature status programs | `SHOULD` |
| K-27 | Release evidence archive | Proton-style trust, POKROV gates | `MUST` |
| K-28 | Privacy-safe review/testimonial proof | POKROV opportunity | `SHOULD` |

### L. Adjacent products и расширение выручки

| ID | Функция | Примеры | POKROV |
| --- | --- | --- | --- |
| L-01 | DNS subscription | AdGuard, Express/CyberGhost ecosystems | `CAN` after core |
| L-02 | Ad/tracker blocker | Express, CyberGhost, AdGuard ecosystem | `CAN` |
| L-03 | Password manager/generator | Express, Quattro Security | `NO-GO` until separately maintained product exists |
| L-04 | Breach/identity checker | Express, Quattro Security | `CAN` only with real data source and privacy model |
| L-05 | URL scanner/safe browser | Quattro Security, security suites | `CAN`; low priority |
| L-06 | Antivirus/security suite | CyberGhost, Express | `NO-GO` for current wave |
| L-07 | Temporary email/mail product | AdGuard ecosystem | `NO-GO` for current wave |
| L-08 | Wallet/crypto product | AdGuard/MORI adjacent products | `NO-GO` |
| L-09 | eSIM | GnuVPN, VPN Наружу | `CAN` as partner cross-sell later |
| L-10 | VPN router/hardware | VPN Наружу | `CAN` after router demand proof |
| L-11 | Team/B2B access packs | VPN Наружу | `SHOULD` as sales experiment |
| L-12 | Dedicated-IP/B2B connectivity | MORI, CyberGhost | `CAN` |
| L-13 | Gaming/content bots | VPN Наружу, MORI ecosystem | `NO-GO` unless tied to acquisition economics |
| L-14 | Multiple VPN brands from one stack | VPN Наружу/Перемен, publisher portfolios | `NO-GO` before POKROV product-market fit |

### M. Внутренние operator/growth capabilities

| ID | Функция | Примеры | POKROV |
| --- | --- | --- | --- |
| M-01 | Server-driven catalog | Большинство зрелых клиентов | `PROVE`; backend exists |
| M-02 | Health/capacity-aware selection | POKROV, mature networks | `PROVE` |
| M-03 | Feature flags | POKROV wheel/calendar, remote-config competitors | `PROVE` |
| M-04 | Remote copy/promo slots | POKROV, Quattro | `PROVE`; allowlisted first-party only |
| M-05 | Network rollout targeting | POKROV admin | `PROVE` |
| M-06 | Node drain/enable/disable/resync | POKROV admin | `PROVE` |
| M-07 | Panel drift/sync diagnostics | POKROV admin | `PROVE` |
| M-08 | Funnel analytics | POKROV admin, growth-heavy products | `PROVE` without sensitive payloads |
| M-09 | Campaign link builder | POKROV admin, Quattro | `PROVE` |
| M-10 | Start-link management | POKROV bot/admin | `PROVE` |
| M-11 | Referral queue/anti-abuse | POKROV | `PROVE` |
| M-12 | Payment ledger/reconciliation | POKROV | `PROVE` live provider workflow |
| M-13 | Gift/promo issuing | POKROV | `PROVE` |
| M-14 | Segmented broadcasts | POKROV, Telegram-first products | `PROVE`; opt-out and limits |
| M-15 | Retention templates | POKROV admin | `PROVE` |
| M-16 | Live update/incident notices | POKROV admin | `PROVE` |
| M-17 | Support queue/macros | POKROV | `PROVE` |
| M-18 | AI support assist | POKROV | `PROVE` privacy and human escalation |
| M-19 | Automated compensation grants | Competitor operations | `MUST` |
| M-20 | Release gates/dashboard | POKROV, mature competitors | `PROVE`; exact candidate only |
| M-21 | ABI/platform smoke matrix | MORI/Quattro lesson | `MUST` |
| M-22 | Ruleset/package catalog versioning | POKROV | `PROVE` |
| M-23 | Official-link allowlist | POKROV | `PROVE` |
| M-24 | A/B or staged rollout | AdGuard/global products | `SHOULD`; no fake urgency |
| M-25 | Incident rollback and postmortem | Mature release programs | `MUST` |

## Уникальный профиль каждого конкурента

| Конкурент | Фичи, ради которых его стоит помнить |
| --- | --- |
| [Hiro](./hiro-vpn.md) | Quests, wheel, levels, reserve traffic, anime brand, special routes, partner program |
| [Огонь](./ogon-vpn.md) | Human job routes, bypass categories, 5 GB forever, Telegram status/promos |
| [Батя](./batya-vpn.md) | Optimum/LTE/AI/Ultra, TV/cabinet, compensation loop |
| [Vanya](./vanya-vpn.md) | Best staged repair, multihop, app/domain/IP/subnet rules, portable key |
| [Kakadu](./kakadu-vpn.md) | Family accounts, QR/code login, devices/sessions, Always-on/Quick Settings |
| [Durev](./durev-vpn.md) | Task-specific keys, lifetime revenue share, portable recovery matrix |
| [Космос](./kosmos-vpn.md) | One-control app, TV QR, rich cabinet, incident compensation |
| [GnuVPN](./gnuvpn.md) | No-card trial, 59 countries, AmneziaWG/OpenVPN/SoftEther, custom servers, eSIM |
| [Blanc](./blancvpn.md) | Anti-block modes, strong help/status layer, large Russian knowledge base |
| [Ping](./ping-vpn.md) | 233-service routing catalog and enormous acquisition footprint, despite broken bootstrap |
| [Proton](./proton-vpn.md) | Best free proof, Secure Core/P2P/Tor/Stealth, open source, signatures/audits |
| [TipTop](./tiptop-vpn.md) | Social preset and tasks; main lesson is false-positive connection risk |
| [Red Shield](./red-shield-vpn.md) | Power-user depth: RedLink, three split modes, filters, LAN/Wi-Fi sharing |
| [ExpressVPN](./expressvpn.md) | Protection history, shortcuts, Lightway, polished trust/security funnel |
| [Pipster](./pipster.md) | Free quota, ad monetization, repair shell; example of ads destroying UX |
| [CyberGhost](./cyberghost.md) | Streaming/P2P/gaming servers, Wi-Fi automation, NoSpy/dedicated IP |
| [Lagom](./lagom-vpn.md) | Automatic bank/state bypass, Russia-from-abroad route, 5 GB monthly, strong store creatives |
| [AdGuard](./adguard-vpn.md) | Best consent structure, TrustTunnel, dual exclusions, DNS, VPN/SOCKS/integration modes |
| [4ebur](./4ebur-net.md) | Best White list/Bypass/Multihost taxonomy, Mini App, recurring 33% referral |
| [VPN Наружу](./vpn-naruzhu.md) | No-card seven-day proof, simple Smart/Direct story, Telegram operating system, router/eSIM/team packs |
| [MORI](./mori-vpn.md) | Strongest visual/editorial packaging, bot self-service, QR, ambitious TOR/Multi-Hop architecture |
| [Quattro](./quattro-vpn.md) | Largest visible distribution, owned cabinet/bot, configurable entitlement, LTE economy, huge route catalog |

## Рекомендуемая последовательность

### Волна 1 — конкурентоспособный core

1. Закрыть signing/device/runtime gates Android и Windows.
2. Ввести DNS/HTTPS/route validation до зелёного статуса.
3. Сделать safe teardown и one-button repair.
4. Доказать `All except RU` и Selected Apps на точных артефактах.
5. Добавить purpose presets: Video, AI, Social, Games, RU-direct, White-list/Bypass.
6. Дать Favorites, Recent, measured ping/load и понятный route state.

### Волна 2 — owned operating system

1. Status page + in-app incident inbox + automatic compensation.
2. Release hub: signed APK/EXE, mirrors, hashes, signer, version history.
3. Live app/cabinet/bot parity и cross-device QR/code pairing.
4. Referral/partner dashboards, campaign attribution, gifts/team packs.
5. Responsibility map, field-level privacy table и public incident archive.

### Волна 3 — удержание и расширение

1. Domain rules, DNS presets, Kill Switch/Always-on и Wi-Fi automation.
2. Wheel/calendar/quests только после включения ledger-backed backend state.
3. Multihop, streaming/P2P/gaming routes только с scenario health.
4. Android TV/router/Linux после зрелости Android/Windows.
5. Adjacent cross-sells только после стабильного core и измеренного спроса.

## Источники и ограничения

- Конкурентные функции взяты из 22 локальных профилей и их raw evidence на 2026-07-22.
- `Примеры` обозначают наблюдавшиеся реализации, а не исчерпывающий список всех продуктов с этой функцией.
- POKROV status сверялся с текущим platform product contract, shared facts, canonical feature tracker и active-client product/readiness docs.
- Наличие кода не превращено в production claim. Signing, physical-device, live session, store, payment-provider и RU-origin gates остаются отдельными.
- Этот файл — research/backlog reference. Он не меняет канонический product contract сам по себе.

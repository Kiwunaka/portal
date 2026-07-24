# Telegram VPN — вторая волна: итоговая сводка

**Срез:** 2026-07-12, 22:10–22:15 МСК

**Окно постов:** 2026-05-12 — 2026-07-12

**Полный технический разбор:** [боты, TGStat, посты, APK, SDK, permissions и emulator UX](telegram-vpn-wave2-and-apk-analysis.md)

## Что реально сделано

- Найдены и дедуплицированы новые Telegram-first VPN-конкуренты.
- Сняты живые Telegram/TGStat-метрики девяти сильных каналов.
- Глубоко пройдены HitVPN, Shuka, Atlanta, Batya, Durev и FineVPN.
- По Atlanta пройдены gate, trial, все платформы, тарифы, профиль, ключи, белые списки, referral, partner, помощь и инструкции.
- Проверены посты девяти каналов за два месяца.
- Найдены официальные приложения и источники APK.
- Скачаны, хэшированы, распакованы и установлены в эмулятор OverSecure, Kubik и MantaRay.
- Сохранён 31 безопасный скриншот: Telegram, TGStat и Android UI.
- Личные Telegram ID, referral-коды, subscription URL, QR, payment token и HWID из evidence удалены.

## Главный итог

1. **HitVPN — абсолютный лидер по дистрибуции**, но живой бот во время проверки был на обслуживании, а официальный APK-host не отдавал валидный файл.
2. **Sota и Lagom — самые интересные растущие app-backed конкуренты:** около +15% канала за месяц; у Lagom уже 5M+ Android-установок.
3. **Batya — самая цельная массовая связка bot + cabinet + branded app**, но рост сильно подпитан розыгрышами и бонусами за отзывы.
4. **Atlanta — самый агрессивный коммерческий конструктор:** подписка по времени, отдельные GB для белых списков, referral и 50% partner.
5. **Durev — сильный bot-led продукт** с email-login, подарками и пожизненным закреплением реферала, но бренд привязан к TON meme-token.
6. **MantaRay — лучший Android UX в этой волне.** Routing presets, rule builder, route history и диагностика сделаны заметно глубже рынка.
7. **Kubik — худший trust-кейс:** публичный APK подписан Android Debug-сертификатом и содержит огромный ad-tech/attribution стек.

## TGStat и Telegram

Bot MAU — месячные пользователи Telegram-бота, а не платящие клиенты. Channel subscribers — подписчики канала. Установки приложений тоже нельзя автоматически считать клиентами конкретного VPN.

| Конкурент | Канал | Bot MAU | За 30 дней | Охват / ERR | Android |
|---|---:|---:|---:|---:|---|
| HitVPN | 4 607 630 | 3 752 595 | +386 200, ≈+9.1% | 2 236 043 / 48.5% | HitRay 10M+; HitVPN 1M+ |
| Shuka | 1 291 035 | 496 996 | +53 455, +4.3% | TGStat-охват невалиден | MantaRay 10K+, не Shuka-branded |
| Atlanta | 801 830 | 319 740 | +40 909, +5.4% | 210 089 / 26.2% | собственная beta 1K+ |
| Sota | 794 734 | 436 732 | +105 221, +15.3% | недостаточно данных | Sota Connect 500K+ |
| Batya | 185 484 | 176 626 | +11 776, +6.8% | 81 710 / 44.1% | Batya 1M+ |
| Lagom | 167 258 | 218 394 | +21 990, +15.1% | 108 701 / 64.9% | Lagom 5M+ |
| BlancVPN | 97 041 | 36 333 | +547, +0.6% | 61 334 / 63.2% | BlancVPN 100K+ |
| GenVPN | 69 612 | 11 887 | −301, −0.4% | 20 604 / 29.6% | legacy app 50K+ |
| Durev | 58 111 | 193 755 | +2 205, +3.9% | 55 695 / 95.8% | Durev 100K+ |

Публичные TGStat widgets сохранены в [raw evidence](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/). Демография, полный source-of-growth и качество подписчиков для чужих каналов недоступны.

## Кого брать в основной benchmark

### Продукт

- MantaRay — routing и diagnostics.
- Quattro — экосистема и cabinet.
- Cats — анонимный вход по короткому коду.
- BlancVPN — incident/status/compensation/roadmap.
- Batya — узнаваемый человеческий brand voice.

### Growth

- HitVPN — абсолютный масштаб.
- Sota и Lagom — быстрый app-backed рост.
- Atlanta — affiliate/creator-машина.
- GenVPN — высокая content cadence и публичные UX-опросы.

### Антипример

- Kubik — debug signing и SDK-комбайн.
- Liberty — инвестиционный оффер с заявленной доходностью до 170% годовых.
- HitVPN/Batya — розыгрыши как доминирующий контент.
- Atlanta — 50% partner при сломанной статистике.

## Глубокие bot findings

### HitVPN

- 3 752 595 bot MAU.
- Во время проверки: «Сервис на обслуживании».
- Recovery — через `@hitvpn_news`, support — `@hitvpnhelp4`.
- Это произошло после поста 30 июня о восстановлении.
- Прямой APK URL был найден на официальном сайте, но download-host имел сломанный/просроченный TLS и не отдал проверяемый APK.

[Скрин maintenance](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/hitvpn-bot-maintenance.png)

### Shuka

- Mandatory-подписка на канал.
- 3 дня — 10 ₽; месяц — 299 ₽; 3 месяца — 749 ₽.
- Referral: пригласивший получает 14 дней + 20 GB whitelist-трафика; новый пользователь — 7 дней за 10 ₽.
- Bot продаёт обычный VPN; сильная часть продукта — рекомендованный MantaRay.
- MantaRay публично является BYO-server клиентом. Считать все его установки клиентами Shuka нельзя.

[Скрин тарифов](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/shuka-pricing.png)

### Atlanta

```text
Channel gate + agreement
└─ RU / EN
   └─ 3-day trial
      └─ iOS / Android / Android TV / Windows / macOS

Main
├─ Buy: RUB / Heleket crypto
├─ Profile
│  ├─ balance / transactions / email
│  ├─ keys / expiry / renewal
│  ├─ promo
│  └─ language
├─ Setup
├─ Referral
├─ Partner
└─ Diagnostics / whitelist FAQ / support
```

Основной тариф:

- 30 дней — 199 ₽;
- 3 месяца — 449 ₽;
- 6 месяцев — 899 ₽;
- 12 месяцев — 1 249 ₽.

Белые списки продаются отдельно:

- 15 GB — 99 ₽;
- 30 GB — 198 ₽;
- 2 GB бесплатно.

Referral:

- 50 ₽ за нового пользователя;
- 30% со всех его пополнений.

Partner:

- 50% от приведённых оплат;
- вывод от 3 000 ₽;
- сам bot предупреждает, что partner statistics сейчас работают неправильно.

Платформы:

- Android/iOS — Happ;
- Windows — Happ Desktop;
- macOS — V2rayTun;
- Android TV — отдельная инструкция и remote app;
- собственная Atlanta App Beta существует, но основной flow пока на внешних клиентах.

[Скрин тарифов](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/atlanta-pricing.png)

### Batya

- 5 дней бесплатно.
- 299 ₽ / месяц; 699 ₽ / 3 месяца; 1 899 ₽ / год; 4 199 ₽ «навсегда».
- «Навсегда» в оферте означает только пока сервис существует и может оказывать услугу.
- Лендинг ошибается в математике годовой скидки.
- Android/TV app — 1M+; Apple app — отдельный publisher/bundle; Windows ведёт в Happ.
- Store labels заявляют «данные не собираются», но собственная privacy policy перечисляет Telegram ID, traffic volume, device, OS и app version.
- В живом bot воспроизвёлся дефект: `/start` вернул «Пользователь уже существует», а `/menu` и `/help` не восстановили кабинет.

[Скрин тарифов и ошибки](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/batya-pricing.png)

### Durev

- 17 ₽ / пробный день.
- 459 ₽ / месяц; 1 310 ₽ / 3 месяца; 2 414 ₽ / 6 месяцев; 3 864 ₽ / год; 5 244 ₽ / 2 года.
- До 10 устройств, 100+ серверов, 50 стран — vendor claims.
- Site login начинается с привязки email; email не отправлялся.
- Referral: 20% днями или деньгами, реферал закрепляется навсегда.
- Вывод: от 5 000 ₽ / 50 USDT / 3 000 Stars, начисление после 48-hour refund hold.
- Brand напрямую связан с Povel Durev TON meme-token и использует пять mirror-domain.

[Скрин тарифов](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/durev-pricing.png)

### FineVPN

- 10 972 bot MAU.
- RU / EN / DE / FR / ES / CN.
- В bot лежит официальный beta APK 1.0.0, 43.3 MB.
- Telegram Web показал документ, но controlled media download не сработал. Mirror APK не подменял официальный файл.

[Скрин официального APK](../../../competitor-profiles/raw/finevpn/2026-07-12/screenshots/bot-official-beta-apk.png)

## Посты за два месяца

| Канал | Объём | Что делает |
|---|---:|---|
| HitVPN | 16 | 8 giveaway/result, приложения, кризис |
| Shuka | 1 | один большой release blast |
| Atlanta | 5 | набор traffic-team + кризис/восстановление |
| Batya | 32 события | 21 событие вокруг розыгрышей/эфиров/итогов |
| Raketa | 4 | новости и инструкции внешних клиентов |
| Velvet | 0 | канал молчит |
| Liberty | 5 | политика/образование + инвестиционный оффер |
| BlancVPN | 7 | status, compensation, roadmap, own apps |
| GenVPN | 47 | status, offers, GEN PAY, polls, tracked links |

### Самый агрессивный маркетинг

1. Batya: 199 призов, затем 10 iPhone + 10 AirPods + 10 × 10 000 ₽, плюс 14 дней за store review.
2. HitVPN: один и тот же iPhone 17 Pro Max loop каждые 1–2 недели.
3. Atlanta: платный recruitment трафика из Telegram/TikTok/Shorts/Reels/YouTube/форумов.
4. GenVPN: почти каждый инфоповод переводится в tracked bot link или GEN PAY cross-sell.
5. Liberty: частные инвестиции от 150 000 ₽ с заявлением до 170% годовых и оговоркой «гарантий нет».

### Лучший нормальный контент

BlancVPN: incident → status page → действие пользователя → компенсация → recovery → roadmap. Продажа встроена в полезный материал, а не заменяет его.

## Скачанные APK

| App | ASCII-путь | Package / version | SHA-256 |
|---|---|---|---|
| OverSecure | `C:\Users\kiwun\AppData\Local\Temp\codex-vpn-wave2\oversecure\oversecure.apk` | `com.oversecure.vpn` 1.1.7 (15) | `F3FC3DD14F92EF0837501345B050F91FBE56940A36688C842277A10D9B0EE167` |
| Kubik | `C:\Users\kiwun\AppData\Local\Temp\codex-vpn-wave2\kubik\kubik.apk` | `com.kubikvpn.app` 1.2.4 (11) | `65C9E93EA4117BCC3319F6CAD5EF372F3A3057E474387A71D5026DCF609FAB52` |
| MantaRay | `C:\Users\kiwun\AppData\Local\Temp\codex-vpn-wave2\mantaray\mantaray.apk` | `com.mantaray.vpn` 2.25.8 (311) | `2DAA9D98A1E9D7B974974FD3F6E6BD820FD31D857D2B43F9C15EDE34E1148BEC` |

Разобранные файлы, manifests, DEX/native strings, UI dumps и emulator logs лежат рядом внутри соответствующих папок.

## APK: короткое сравнение

| Параметр | OverSecure | Kubik | MantaRay |
|---|---|---|---|
| Подпись | v2, Oversecure LTD | v2, **Android Debug** | v2, MantaRay identity |
| Core | sing-box/SagerNet | Flutter + sing-box | own core 5.13.1 FFI v2 |
| Ads/tracking | AppMetrica, без полного ad-stack | огромный mediation + attribution stack | без AD_ID/ad networks; FCM/ML Kit + first-party telemetry |
| Вход | нужен subscription URL | anonymous free | BYO config/subscription |
| Сильная часть | split tunneling | простой free onboarding | routing builder + diagnostics |
| Главный риск | broad app visibility / sideload | debug cert + SDK overload | usage/package access + routing telemetry |

## OverSecure

- Размер: 35 805 535 bytes.
- min/target SDK: 24/36; `debuggable=false`.
- `libbox.so`, Rive, AppMetrica.
- `QUERY_ALL_PACKAGES`, `REQUEST_INSTALL_PACKAGES`, AD_ID, Install Referrer.
- Standard/Bypass, DNS, LAN, stats, auto-server, per-app split include/bypass.
- UI собран аккуратно, но onboarding требует готовый bearer subscription URL.

[Профиль и все скрины](../../../competitor-profiles/oversecure.md)

## Kubik

- Размер: 120 208 613 bytes.
- min/target SDK: 24/36; `debuggable=false`.
- Публичный release подписан Android Debug certificate.
- Appodeal/AppLovin/Yandex/Facebook/IronSource/Unity/Amazon/InMobi/Vungle/Chartboost/Fyber/Smaato/Moloco/Start.io/BidMachine/PubNative/Bigo/Mintegral/Ogury/MobileFuse/MyTarget.
- Adjust, AppsFlyer, Firebase Analytics, AppMetrica, Sentry.
- Anonymous free: 60 минут за сессию, 5 GB/месяц.
- UI нормальный, но settings пустые, premium не показывает цены.

[Профиль и все скрины](../../../competitor-profiles/kubik-vpn.md)

## MantaRay

- Размер: 160 872 388 bytes.
- min/target SDK: 24/35; `debuggable=false`.
- Own `libmantaray_core.so`, marker 5.13.1 FFI v2.
- Нет AD_ID и рекламных сетей.
- Config: manual link / clipboard / QR.
- Presets: VPN только где надо / везде кроме RU / для всего.
- Custom route builder: mode → exceptions → sites/IP → name; action VPN/direct/block.
- Quick Tile, widgets, self-update, geo DB, autoconnect.
- Logs, session traffic, diagnostics и local route-decision history.
- `api.mantatech.ltd` содержит update/crash/AI/routing-telemetry routes.

[Профиль и все скрины](../../../competitor-profiles/mantaray.md)

## Что брать в POKROV

### P0

1. MantaRay routing presets и пошаговый rule builder.
2. Local route-decision history и redacted diagnostics export.
3. Независимый web cabinet для recovery, billing, devices и key rotation.
4. Versioned APK URL + SHA-256 + certificate fingerprint + changelog.
5. CI guard против Debug certificate и неожиданного роста SDK/permissions.
6. Один data inventory для privacy policy и store labels.
7. In-app incident banner/status, чтобы падение Telegram не ломало продукт.

### P1

1. Простой trial с понятной ценой после него.
2. Одна referral-модель с честным ledger, а не две конфликтующие партнёрки.
3. Brand voice уровня Batya без fear spam.
4. Incident communication уровня BlancVPN.
5. UX-опросы уровня GenVPN без sales-link в каждом посте.
6. Symptom-based support уровня Atlanta, но внутри одного продукта.

## Что не брать

- Розыгрыши как основной контент.
- Вознаграждение за публичные store reviews.
- «Навсегда» без явного service-lifetime текста у CTA.
- 50% partner при сломанной attribution statistics.
- Mandatory channel gate до оценки продукта.
- Debug-signed release.
- Mutable `latest.apk` без immutable version/hash.
- Telegram document как единственный APK source.
- Store label «не собираем данные», если policy говорит обратное.

## Что было заблокировано

- HitVPN APK: сломанный first-party download host/TLS.
- FineVPN APK: Telegram Web не отдал document media.
- Batya, Atlanta, Durev, Sota, Lagom, BlancVPN: Play-only; Google Play в эмуляторе не авторизован, сторонние mirrors не использовались.
- VOSKHOD APK: download завис на 0 bytes, пустой файл удалён.
- TGStat demographics/source tables: public widgets этого не содержат, owner-only/API access не получен.

## Безопасность прохода

- С разрешения пользователя выполнены mandatory-подписки Shuka и Atlanta.
- Активирован один Atlanta trial на 3 дня.
- Оплаты, payout, support messages и VPN connection не выполнялись.
- Секретные ссылки и идентификаторы не сохранены.
- Эмулятор остановлен; исследовательские вкладки закрыты.

## Все новые профили

- [HitVPN](../../../competitor-profiles/hitvpn.md)
- [Shuka](../../../competitor-profiles/shuka-vpn.md)
- [Atlanta](../../../competitor-profiles/atlanta-vpn.md)
- [Batya](../../../competitor-profiles/batya-vpn.md)
- [Durev](../../../competitor-profiles/durev-vpn.md)
- [FineVPN](../../../competitor-profiles/finevpn.md)
- [Sota](../../../competitor-profiles/sota-vpn.md)
- [Lagom](../../../competitor-profiles/lagom-vpn.md)
- [BlancVPN](../../../competitor-profiles/blancvpn.md)
- [GenVPN](../../../competitor-profiles/genvpn.md)
- [OverSecure](../../../competitor-profiles/oversecure.md)
- [Kubik](../../../competitor-profiles/kubik-vpn.md)
- [MantaRay](../../../competitor-profiles/mantaray.md)

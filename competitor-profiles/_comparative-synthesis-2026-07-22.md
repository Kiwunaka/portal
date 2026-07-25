# Сравнительный аудит 22 VPN-конкурентов

**Срез:** 2026-07-22<br>
**Статус:** `COMPLETE WITH EXPLICIT BLOCKERS`<br>
**Среда:** LDPlayer 14 / Android 14 / Google Play; приложения запускались строго по одному<br>
**Подробное покрытие:** [журнал аудита](./_mobile-app-audit-2026-07-22.md)
**Справочник функций:** [335 уникальных фич и приоритеты POKROV](./_pokrov-feature-catalog-2026-07-22.md)

Это итоговая выжимка по двадцати двум VPN с исходного и двух дополнительных скриншотов: шестнадцать из первой очереди плюс Lagom VPN, AdGuard VPN, 4ebur.net, VPN Наружу, MORI VPN и Quattro VPN. Для каждого продукта отдельно сохранены карточка, принятые скриншоты, UI-деревья, карта публичных страниц, цены, юридические лица, релизные каналы, growth-механики, технические наблюдения и явные блокеры. Здесь — сравнение и выводы для POKROV.

Старая пассивная карточка MORI обновлена полноценным срезом 2026-07-22 и теперь включена в сравнение. Quattro разобран как две разные Android-линии: основной Telegram/direct-сервис и отдельный bring-your-own-config клиент из Google Play.

## Главный вывод

POKROV отстаёт не потому, что старается быть честным. Честность не мешает сильному продукту. Отставание находится в семи конкретных слоях:

1. **Доказательство ценности до оплаты.** Proton, Огонь, Hiro, GnuVPN и Pipster дают человеку увидеть или реально проверить продукт до покупки. У многих остальных жёсткий paywall, но они компенсируют это брендом, экосистемой или сильной дистрибуцией.
2. **Маршруты, названные человеческими задачами.** Не «протокол №3», а «YouTube без рекламы», «российские сайты напрямую», «AI», «соцсети», «игры», «банки», «только выбранные приложения».
3. **Понятное восстановление при блокировке.** Vanya лучше всех упаковал ремонт: перепроверить путь → обновить IP → включить multihop. Blanc и Red Shield объясняют протоколы человеческим языком. Батя и Огонь используют Telegram как оперативный статус-канал.
4. **Growth-машина внутри продукта.** Hiro строит полноценную экономику квестов, колеса, трафика, уровней и партнёрки. Quattro собрал крупнейшую видимую Telegram-машину, 4ebur отдаёт 33% от повторных покупок, у Durev есть пожизненная доля, у Наружу — подарки, командные наборы, розыгрыши, исследования и соседние продукты.
5. **Собственный операционный контур.** Quattro и VPN Наружу не оставляют управление бизнесом внутри одного APK: bot/cabinet, подписка, статус, релизы, инструкции, промо, компенсации, зеркала и support образуют одну систему. Это уже не «приложение VPN», а owned distribution and retention stack.
6. **Дистрибуция на случай блокировок.** Vanya, Quattro, VPN Наружу, AdGuard, Red Shield, MORI, GnuVPN, Blanc, Proton и Pipster не зависят от одного стора: прямые APK, зеркала, боты, кабинеты, TV, расширения, ручные клиенты и отдельные release-каналы.
7. **Публичное доказательство доверия.** Proton, ExpressVPN, AdGuard и CyberGhost публикуют подписи артефактов, исходники или открытые компоненты, аудиты, transparency reports, release lanes и большую базу поддержки. Даже у них найден дрейф фактов — значит POKROV может обойти их дисциплиной единого источника правды.

Коротко: **копировать надо наглость упаковки, скорость релизов и глубину сценариев; враньё, скрытые продления, накрутку отзывов и юридический бардак копировать нельзя.**

## Легенда проверки

- `PASS` — путь реально пройден в текущей сессии.
- `PARTIAL` — часть пути пройдена, остальное подтверждено публичными или статическими материалами.
- `BLOCKED` — путь требует оплаты, ключа, работающего backend, недоступного реестра или другого явно указанного доступа.
- `FAIL` — сбой воспроизведён, а не выведен из отзыва или маркетингового текста.
- Цены и каталоги — снимок на дату аудита; они изменяемые и не являются вечной спецификацией продукта.

## Сравнение продукта и воронки

| Конкурент | Вход и доказательство | Главная сильная механика | Growth / удержание | Фактическое состояние туннеля |
| --- | --- | --- | --- | --- |
| [HiroVPN](./hiro-vpn.md) | 7 дней после входа; продукт и награды видны сразу | Аниме-бренд, специальные серверы, split routing, DNS, резервный трафик, продуктовые тизеры | Самая глубокая система: квесты, колесо, уровни, бонусные дни/трафик, рефералка, affiliate | `PASS`: Android-validated France, чистое отключение; после Google-входа неожиданно авто-подключил Austria |
| [Огонь VPN](./ogon-vpn.md) | Анонимная device-bound учётка, 5 GB «бесплатно навсегда» | Роутинг по задачам: российские/гос-сайты, YouTube, игры, приложения, категории обхода | Telegram, промокоды, подарки, компенсации; есть запрещённое вознаграждение за 5★ | `PASS`: Auto, HTTPS и disconnect проверены |
| [Батя VPN](./batya-vpn.md) | Анонимное локальное состояние; заявлен 5-дневный период, чистая активация не воспроизведена | Optimum, LTE allow-list, AI и Ultra; кабинет, TV QR, ключи и инструкции | Telegram как status/changelog, рефералка, розыгрыши, промо, компенсации; есть +14 дней за отзывы | `FAIL`: `tun0` не появился, backend fallback упал на просроченном сертификате, UI молча сбросился |
| [Vanya VPN](./vanya-vpn.md) | Чистый empty state: добавить ключ / купить / поддержка | Лучший staged repair; portable `ssconf://`; split по app/IP/subnet/domain; multihop | Длинные пакеты, 10 ₽ тест с автопродлением, aggressive cancel offers, affiliate/cabinet bot | `BLOCKED`: нужен рабочий ключ |
| [Kakadu](./kakadu-vpn.md) | Жёсткая auth-wall; Google и code/QR входы сломались | Family, устройства/сессии, QR/code login, Smart Connect, избранное, Always-on | Telegram «новость о блокировке → Kakadu работает → bot/скидка/referral» | `BLOCKED_BY_BACKEND`: оба входа вернули на стену без нормальной ошибки |
| [Durev VPN](./durev-vpn.md) | Key hub: ручной ключ, email, Telegram, QR; нет ясного маршрута нового клиента | Нормальный/allow-list/Gemini/Roblox ключи, восстановление ключа, 50+ серверов | Пожизненный процент от покупок приглашённых, вывод деньгами или днями VPN | `BLOCKED`: платный ключ отсутствует |
| [Космос VPN](./kosmos-vpn.md) | Email OTP; доступ после регистрации с оговоркой про компенсационные дни | Один сильный control, fastest + 11 стран, TV QR, богатый кабинет | Рефералка, розыгрыши, Telegram binding, promo, status/compensation inbox | `PASS`: реальный туннель, route/DNS и disconnect проверены |
| [GnuVPN](./gnuvpn.md) | Можно изучать анонимно; регистрация сразу дала 7-дневный no-card trial | 59 стран, AmneziaWG/OpenVPN/SoftEther, понятные подсказки, split, custom servers | Referral points, push/in-app messaging, eSIMSecure cross-sell | `PASS`: AmneziaWG, route/DNS и чистое отключение |
| [BlancVPN](./blancvpn.md) | Passwordless email OTP; каталог доступен, но trial/free tunnel нет | 51 город/46 стран, search/sort/quality, сильные anti-block режимы и routing | Двусторонние 30 дней после покупки, Telegram, status/compensation, 99 RU help-статей | `BLOCKED_BY_PAID_ACCESS` |
| [Ping VPN](./ping-vpn.md) | Обещает бесплатный/no-auth продукт, но не проходит bootstrap | По официальным материалам — 233 сервиса, smart routing, custom URL, fastest/favorites/search | 5M+ Play, 718K Telegram, publisher portfolio; claims противоречат рекламе/подписке | `FAIL`: повторяемая загрузочная стена, runtime продукта не достигнут |
| [Proton VPN](./proton-vpn.md) | Лучший guest-first: бесплатный туннель без аккаунта и карты | 148 стран, Secure Core/P2P/Tor, profiles, Stealth, NAT, post-connect actions | Экосистема Proton, first-party attribution, контентная машина, free→paid funnel | `PASS`: WireGuard, две смены сервера, чистый disconnect |
| [TipTop VPN](./tiptop-vpn.md) | Guest shell после медленного remote bootstrap | Social-only preset, remote catalog, fastest, split/proxy/settings | Tasks за вход/отзыв/share, free premium for friend, promo; часть механик манипулятивна | `FAIL`: `tun0` появился и UI стал зелёным, но DNS/HTTPS не работали; Wi-Fi восстановился только после reset/reboot |
| [Red Shield VPN](./red-shield-vpn.md) | Обязательная регистрация, затем внешний платёж; free proof нет | 37 локаций, RedLink, три split-режима, presets, content filters, Wi-Fi sharing | Cabinet/devices/gifts/promo, 30 дней после первой оплаты друга | `BLOCKED_BY_PAID_ACCESS` |
| [ExpressVPN](./expressvpn.md) | Consent → value carousel → жёсткий paywall | Lightway, Protection History, shortcuts, advanced protection, большой security bundle | Exit retention, referral 30/30, three-tier land-and-expand, trust education | `BLOCKED_BY_PAID_ACCESS` |
| [Pipster](./pipster.md) | Guest, 0.5 GB; +200 MB за rewarded ad; первая цена «30 ₽» скрывает срок | Auto server, 12 paid countries, four-stage repair shell, extension PAC routing | Ads, server inbox, referral/revenue-share cabinet, 30 ₽ trial | `PASS` с тяжёлой ценой: 34-секундная реклама перед connect; repair убил туннель и включил 98-секундную рекламу |
| [CyberGhost](./cyberghost.md) | Consent → hard paywall; бесплатного shell нет | 100 стран, streaming/P2P/gaming, NoSpy, Dedicated IP, Wi-Fi automation, account hub | 30/30 referral до 3 друзей, cross-sell Security Suite/Identity Guard/extensions | `BLOCKED_BY_PAYMENT_RAIL`: Google Play платежи в РФ приостановлены |
| [Lagom VPN](./lagom-vpn.md) | Обязательная auth-wall; обещаны 5 GB ежемесячно, но email OTP и Google registration сломались | Автоматический bypass банков/гос-сервисов, Russia route из-за рубежа, VLESS/V2Ray, один профиль на устройства | 5M+ Play, сильные store creatives, Telegram handoff и заявленный миллион пользователей | `BLOCKED_BY_AUTH_BACKEND`: home/paywall/VPN consent не достигнуты |
| [AdGuard VPN](./adguard-vpn.md) | Google-вход прошёл; free home показывает 4 GB/месяц, 3 бесплатные локации и ограничение скорости | TrustTunnel, app/domain exclusions с пресетами, custom DNS, VPN/SOCKS5/integration modes, Kill Switch guide | Экосистема AdGuard, +1 GB за новое устройство, direct APK, Release/Beta lanes, affiliate и owned content | `FAIL_IN_ENVIRONMENT`: Automatic, HTTP/2 и QUIC упали на TLS hostname verification; устойчивого `tun0` не было |
| [4ebur.net](./4ebur-net.md) | Анонимный home и два бесплатных VLESS-узла; Premium можно купить/восстановить ключом | Лучшая явная anti-block taxonomy: Ordinary / White list / Bypass / Multihost плюс Amnezia | Bot + Mini App, 33% с каждой покупки реферала, 6 часов другу, web/store purchase lanes | `FAIL_ON_X86_64`: VPN service упал на отсутствующей native JNI-реализации до `tun0` |
| [VPN Наружу](./vpn-naruzhu.md) | Email OTP сразу дал 7 дней Premium без карты; auto-renew выключен по умолчанию | Smart: RU-сервисы напрямую, foreign через VPN; Direct; 10 устройств, router/TV/Windows контур | Telegram как release/status/research/giveaway OS, gifts/team packs, eSIM/router, компенсации и новые бренды | `PARTIAL`: Smart поднял рабочий `tun0`; Direct/Automatic не изменил проверенный exit, UAE показал Connected без DNS/Internet |
| [MORI VPN](./mori-vpn.md) | Доступ по коду из bot; публично заявлены 3 бесплатных дня, native UI недоступен | В APK: adaptive/anti-block, TOR, Multi-Hop, QR/TV, dedicated IP, tiers и referrals | 88.7K Telegram, ~32K bot users, сильнейшая визуальная упаковка, editorial funnel, компенсации | `BLOCKED_BY_BUILD`: Play x86_64 split без `libflutter.so`/`libapp.so`, до UI и VPN consent не дошёл |
| [Quattro VPN](./quattro-vpn.md) | Основной direct-app не стартовал; email-кабинет доступен, базовый тариф 300 ₽/30 дней | 281-entry catalog, LTE traffic economy/coefficients, protocol/task routes, split/DNS и security tools | 1.06M channel, 550,879 monthly bot users, cabinet/referral/partner/promo, быстрые hotfix и direct APK | `BLOCKED_BY_BUILD`: debug sideload содержит ARM Flutter engine вместо x86_64; `tun0` не появился |

## Что реально произошло с подключением

Из двадцати двух приложений:

- **6 дали рабочий end-to-end туннель:** Hiro, Огонь, Космос, GnuVPN, Proton и Pipster.
- **2 дали только частичное или ложноположительное доказательство:** TipTop поднял `tun0`, но сломал DNS/HTTPS и обычную сеть; VPN Наружу поднял туннель в двух режимах, но Direct не подтвердил смену выхода, а UAE был зелёным без DNS/Internet.
- **6 воспроизводимо сломались раньше рабочего end-to-end туннеля:** Батя на connection/bootstrap API; Ping на начальном remote bootstrap; AdGuard на TLS hostname verification; 4ebur на native JNI; MORI и Quattro на ABI/Flutter packaging.
- **8 остались честно заблокированы доступом:** Vanya и Durev требуют ключ; Kakadu и Lagom — работающий backend login; Blanc, Red Shield, ExpressVPN и CyberGhost — платный entitlement/payment rail.

Это важнее красивой кнопки. POKROV должен считать соединение успешным только после независимой проверки DNS + HTTPS + маршрута, показывать проверяемый статус и уметь вернуть обычную сеть после ошибки.

## Юридическая и ownership-карта

| Конкурент | Найденная ответственность | Главная проблема |
| --- | --- | --- |
| Hiro | WOLLE DEVELOPMENT LIMITED, Hong Kong | Стабильная идентичность, но кнопки legal docs перепутаны; актуальный live-status требует интерактивного реестра |
| Огонь | RELOCUP LLC, Georgia — в legal; ООО «Ф2П», Russia — Play publisher | Не объяснено, кто разработчик, продавец, controller и получатель платежа |
| Батя | UNI PLAN TRADING LIMITED, Hong Kong — VPN offer; ООО F2P — Play | Два слоя ответственности и конфликтующие refund/support документы |
| Vanya | CODE ASSET LTD, UK; Vladimir Kondakov / KONDAKOV OOO в stores; KONDAKOV&GORIN LLC подписывает Windows | Самая раздробленная цепочка seller/publisher/signer/controller; Outline-terms не описывают продукт |
| Kakadu | KAKADU SECURE TECHNOLOGIES - FZCO, UAE; Rafaelian Aik, IE, Armenia — Play | Связь не раскрыта; store/privacy disclosures расходятся |
| Durev | Dmitrii Bratashev, IE, Georgia; publisher brand Cryptan Coder LLC; отдельный Kazakhstan layer | Нет карты ролей; refund guarantee конфликтует с «non-refundable» |
| Космос | KOSMOS CONNECTION, LLC, Armenia; ИП Лисецкая Алина Михайловна, Russia — legacy agreement | Старый B2B/Telegram договор не соответствует текущему consumer app |
| GnuVPN | GNUAPP UNIPESSOAL LDA, Portugal | Controller назван, но policy параллельно упоминает неназванный SVG HQ; current registry proof заблокирован |
| Blanc | Yadda OÜ, Estonia | Entity есть в store/register, но не названа в теле Terms/Privacy; annual report overdue и есть deletion notice |
| Ping | ООО «Ф2П», Russia — Play/FNS | Собственные Terms/Privacy говорят только «developer» и не называют юрлицо/юрисдикцию |
| Proton | Proton AG, Switzerland; Fondation Proton — primary shareholder; Proton Europe sàrl — EU representative | Самая чистая карта; главный долг — несколько расходящихся источников product truth |
| TipTop | TipTopNet Limited, Hong Kong; ОсОО «ТипТопНет Лимитед», Kyrgyzstan — RU footer | Не объяснена связь; policy разрешает internet activity одновременно с no-activity-log claim |
| Red Shield | PRIVATE NETWORK LABS LLC, Florida; исторически Scottish PRIVATE NETWORKS LP / TgVPN | Текущий оператор понятен; старый LP dissolved несмотря на противоречивый overview |
| ExpressVPN | Express Technologies Ltd., BVI — provider/controller; Expressco Services, LLC — store/signer; Kape group | Expressco registry proof не получен; bundle availability и operator roles сложны для пользователя |
| Pipster | ООО PROMDEVELOPMENT, Russia; LLP ViPiN и TipTop Pay layer, Kazakhstan | Адреса/платёжные тексты устарели после миграции на YooKassa |
| CyberGhost | CyberGhost S.R.L., Romania; Kape Technologies — ultimate holding group | Конфликтуют адреса, возраст, 7 vs unlimited devices и устаревшие cross-sells |
| Lagom | LAGOM PRODUCTS LLC, Armenia; identity подтверждается offer/Play и публичными LEI/RIPE данными | В документах чужой UK boilerplate, номер регистрации не объяснён; privacy/store/SDK claims противоречат друг другу |
| AdGuard | ADGUARD SOFTWARE LIMITED, Cyprus | Три first-party поверхности дают разные адреса; registry extract не получен; «ничего не собираем» шире фактической account/quota/support обработки |
| 4ebur.net | Danyl Kunak, Ukraine — Play publisher; договорная сторона названа только «4ebur.net» | Нет юрлица controller, адреса, юрисдикции и governing law; legal links несут session identity |
| VPN Наружу | ИП Замолоцких, Kazakhstan; STARROCKETS LLC, Armenia; Akhali/AkhaliNet LLC, Georgia; stale IT Vega, TOV; NOVINET DOO signer | Четыре operator/controller stories и Kazakhstan/Georgia/Seychelles law без единой карты ответственности |
| MORI | QUARTETTO INTERNATIONAL LTD, UK, company 07785225, active | Русское право при UK-операторе; offer PDF помечен как draft; price/device/torrent/telemetry truth расходится |
| Quattro | ИП Иорданов Самвел Ашотович — основной сервис; ООО «АК «Алькасар»» — отдельный Play publisher; npvpn — inferred platform | Сервис, store-client, operator, publisher и infrastructure provider не сведены; текущий оператор зарегистрирован позже запуска сервиса |

Вывод для POKROV: сделать одну публичную страницу **«Кто за что отвечает»**: владелец бренда, оператор сервиса, data controller, продавец, платёжный агент, store publisher, signer и support operator. Каждая legal/store/payment поверхность должна ссылаться на ту же карту.

## Кто в чём лучший

### Product depth

1. **Proton** — бесплатное доказательство, профили, Secure Core/P2P/Tor, Stealth, экосистема и release proof.
2. **AdGuard** — TrustTunnel, две независимые системы exclusions, DNS, три operating modes, open protocol и зрелая экосистема.
3. **Hiro** — продукт + контент + механики роста объединены в одну систему.
4. **Quattro** — глубокая серверная/LTE/routing экономика и кабинет, но native-сборка аудита не стартует.
5. **Red Shield** — максимум power-user глубины за простым Home.
6. **CyberGhost / ExpressVPN** — purpose/automation/security bundle на зрелой cross-platform базе.

### Лучшее попадание в русскоязычную проблему блокировок

1. **Quattro** — самый широкий наблюдаемый словарь: ordinary/Hysteria2/Torrent/Russia/LTE/SNI/SS/WS/GRPC, коэффициенты и ручные fallback-инструкции; минус — плохая native release integrity.
2. **Огонь** — лучшие готовые списки российских/государственных сайтов, YouTube, игр и категорий bypass в доступном приложении.
3. **VPN Наружу** — самый простой outcome promise: RU напрямую, foreign наружу; операционно силён, но runtime доказал неполную маршрутизацию.
4. **4ebur.net** — самая понятная taxonomy White list / Bypass / Multihost с объяснением промежуточных hops.
5. **Vanya** — staged repair и независимая от стора доставка.
6. **AdGuard / Blanc / Батя / Red Shield** — сильные anti-block transport, режимы и recovery/distribution слои разной зрелости.

### Growth

1. **Quattro** — крупнейшая видимая owned audience: 1.06M channel, 550,879 monthly bot users, referral/partner/promo/campaign attribution и быстрый release loop.
2. **Hiro** — самая глубокая механика внутри продукта: квесты, колесо, уровни, reserve traffic, affiliate и content rewards.
3. **VPN Наружу / MORI** — Telegram editorial/status/release machine, giveaways, compensation, bot self-service и соседние продукты.
4. **4ebur / Durev** — 33% recurring share у 4ebur и lifetime revenue share у Durev превращают пользователей в продавцов.
5. **Батя / Огонь / Космос** — Telegram, подарки, компенсации, raffle, inbox и промо; review rewards использовать нельзя.

### Дистрибуция и релизы

1. **Proton** — лучший source/signature/release pipeline: stable/beta, Play/F-Droid/GitHub.
2. **AdGuard** — Release/Beta histories, direct APK, in-app update, public issues и major → hotfix cadence.
3. **Vanya / Red Shield** — множество platform/store/mirror/manual-client путей; у Vanya shared Apple accounts — запрещённый перегиб.
4. **Quattro** — самая быстрая Telegram-first операционка и hotfix cadence, но debug signer и сломанный x86_64 APK не дают считать её качественным release pipeline.
5. **VPN Наружу / MORI** — bot + direct APK/Windows + guides/mirrors/compensation; обеим не хватает единой provenance/version truth.
6. **GnuVPN / Blanc / Pipster / Express / CyberGhost** — широкое cross-platform покрытие и fallback-каналы разной прозрачности.

### Доверие

1. **Proton** — operator/foundation map, open source, signer fingerprint, audits, transparency.
2. **ExpressVPN** — TrustedServer, открытый Lightway, KPMG, bug bounty, transparency.
3. **AdGuard** — лучший consent в Android-группе, first-party storage disclosure, открытый TrustTunnel и публичные release lanes; абсолютную privacy-копию всё равно надо исправлять.
4. **CyberGhost** — Deloitte, quarterly transparency, NoSpy и dedicated-IP separation story.

Ни один не идеален: Proton держит устаревшие протоколы/скриншоты в части страниц, Express смешивает VPN с раздутым security bundle, AdGuard пишет слишком абсолютное «ничего не собираем», CyberGhost рекламирует закрытый в 2024 году Private Browser в свежих store creatives.

## Что POKROV стоит забрать

### В Home

- Одна большая кнопка, но под ней — **проверяемое состояние**, а не просто зелёный цвет.
- `Быстрее всего`, избранное и поиск.
- 4–6 purpose chips: **Соцсети**, **YouTube/видео**, **AI**, **Игры**, **Российские сайты напрямую**, **Выбрать приложения**.
- После подключения: страна/город, протокол, время, ping/load, объём, результат DNS/HTTPS health-check.
- Небольшой server-driven inbox для outage, компенсации, новой версии и понятных промо.
- Два понятных intent-переключателя как у Наружу: **Умный** и **Весь трафик**, но с видимым объяснением, куда пошёл конкретный домен.

### В восстановлении

- Одна кнопка **«Починить соединение»**.
- Внутренний ladder: health recheck → другой endpoint → другой протокол → обновить IP/config → multihop/alternate transport.
- На каждом шаге: что делаем, сколько обычно занимает, можно ли отменить.
- Если VPN сломал обычную сеть — отдельный безопасный recovery, который снимает routing/DNS state и проверяет исходное соединение.
- Никогда не ставить рекламу, paywall или review prompt внутрь аварийного ремонта.

### В routing

- Три понятных режима: весь трафик через VPN / только выбранное / всё кроме выбранного.
- Пресеты сайтов и приложений, а не только огромный список packages.
- Российские банки/гос-сайты/маркетплейсы напрямую; AI/соцсети/видео через нужный регион.
- Custom domains/IP/subnets для продвинутых пользователей.
- Объяснение каждого режима на примере результата, не на языке Xray/WireGuard.
- Отдельные anti-block стратегии **Обычный / Белый список / Усиленный обход / Multihop**, как у 4ebur и Quattro, с автоматическим выбором по health-check.

### В аккаунте и дистрибуции

- Passwordless email OTP и QR/code login с другого авторизованного устройства.
- Устройства, web-сессии, TV QR, подписка, чеки, промокоды, referral, status, downloads — в одном кабинете.
- Подписанный direct APK, публичный fingerprint, stable/beta, mirror directory и журнал версий.
- Инструкции для официальных альтернативных клиентов там, где собственный бинарник недоступен.
- Никаких shared Apple accounts, вымышленных зарубежных профилей и token-bearing ссылок без нормальной защиты.
- Синхронизировать app, bot и web cabinet вокруг одной подписки, как у Quattro, но показывать активные устройства/сессии, чеки и responsibility map.

### В trust layer

- Один машинный `product-facts` источник для цен, trial, стран, протоколов, лимитов, min OS, устройств, refund и текущих screenshots.
- Из него генерировать приложение, website, stores, FAQ, paywall и support macros.
- Публичные release notes с номером кандидата, датой, каналом и реально изменённым поведением.
- Quarterly transparency report и field-level privacy table: что собирается, зачем, retention, кто получает.
- Независимый аудит — только когда есть что проверять; до этого полезнее подписанный release proof и честная телеметрия.

## Что нельзя копировать

- Вознаграждение за 5★, отзыв, helpful vote или публичный пост — Hiro, Батя, Огонь и TipTop показывают, почему это быстро превращается в manipulation/policy risk.
- Скрытый trial term, автопродление или follow-on price — Vanya, TipTop, Pipster и store paywalls регулярно прячут критическую часть сделки.
- Рекламу перед подключением и особенно внутри ремонта — Pipster.
- «Подключено» без DNS/HTTPS validation — TipTop.
- Raw configs/credentials/endpoints в info logcat — Батя.
- Фальшивые counters, placeholder testimonials и нерепрезентативные review walls — Durev, Ping, Blanc.
- Абсолютные «ничего не собираем / всегда работает / без рекламы» при обратном в policy/package/runtime — почти весь рынок.
- Разные юрлица без responsibility map и копированные договоры от другого продукта — Vanya, Огонь, Батя, TipTop, Космос.
- Default-on marketing/advertising telemetry до ясного согласия — CyberGhost, TipTop, GnuVPN и другие.
- Функции «в разработке» как будто они уже доступны — Hiro, TipTop, Blanc и CyberGhost дают свежие примеры claim drift.
- Debug-signed/ABI-неполные релизы и store creatives без smoke на каждом заявленном ABI — MORI и Quattro.
- Серверы/тарифы, которые выглядят выбираемыми, но молча игнорируют нажатие — 90-дневный тариф Quattro.
- Session/account identifiers в public-looking legal URLs — 4ebur.
- Один бренд для двух разных приложений без явного объяснения, кто даёт серверы и кто обрабатывает данные — Quattro.

## Рекомендуемый план для POKROV

### 0–30 дней: перестать проигрывать в базе

1. Ввести connection contract: tunnel + DNS + HTTPS + route health; не показывать success до проверки.
2. Сделать fail-open/offline shell: Home и сохранённые серверы доступны даже при падении bootstrap API.
3. Добавить fastest, favorites, search и 4 первых job-пресета: Video, AI, Social, RU-direct.
4. Показать цену, trial, renewal, refund и device limit до регистрации/оплаты.
5. Сделать no-card proof: ограниченный трафик или короткий доступ, достаточный для одного реального подключения.
6. Завести единый `product-facts` manifest и запретить ручное дублирование чисел между app/site/store.
7. Опубликовать operator/responsibility map и привести legal/store/payment имена к ней.
8. Добавить release gate по каждому заявленному ABI: cold start → first frame → VPN consent → connect smoke; debug-сертификат не допускается в production lane.

### 31–60 дней: догнать глубину и удержание

1. Staged **«Починить соединение»** с безопасным network reset.
2. Три split-режима, app/site presets и custom domain/IP.
3. Account hub: devices, sessions, TV QR, subscription, receipts, promo, downloads, status.
4. Server-driven inbox для outage, compensation, release и lifecycle-сообщений.
5. Рефералка 30/30 только после подтверждённой платной конверсии и завершения refund window.
6. Status page + incident templates + автоматическая компенсация при массовом сбое.
7. Direct APK stable/beta, публичный signer fingerprint и versioned changelog.
8. Owned cabinet + bot bridge: одна подписка, но без обязательной зависимости от Telegram для отмены, восстановления или юридических действий.

### 61–90 дней: выйти вперёд

1. Честная reward economy: награда за проверяемые продуктовые события — первый успешный tunnel, 7 дней retention, подключение второго устройства, полезный onboarding; не за рейтинг.
2. Wheel/quests только как слой удержания поверх рабочего VPN, с прозрачными odds/limits.
3. Purpose routes для конкретных популярных сервисов с удалённо обновляемым каталогом.
4. Public release evidence: smoke, censorship-path checks, performance SLI и rollback candidate.
5. Первый transparency report и privacy inventory.
6. Кросс-платформенный download hub и официальные fallback-инструкции.
7. LTE/дорогие маршруты тарифицировать только при реальной себестоимости: заранее показать коэффициент, остаток и причину списания, а не прятать экономику в длинных условиях.

## Северная звезда продукта

Если собрать лучшие идеи без их грязи, целевой POKROV выглядит так:

> Proton-grade proof + Vanya-grade recovery + Огонь/Наружу-grade local routing + Hiro-grade in-app growth + Quattro-grade owned funnel + AdGuard-grade controls/release discipline — с одной юридической и продуктовой правдой.

Не надо пытаться сразу скопировать все 200 экранов. Самый высокий ROI дадут: **рабочее доказательство до оплаты, job-based routing, staged repair, account/device hub, честная рефералка и релизный proof**.

## Важные пользовательские потоки и их здоровье

| Поток | Здоровье рынка | Что должен сделать POKROV |
| --- | --- | --- |
| Запуск → Home | Часто ломается на remote bootstrap или auth/paywall | Кэшированный shell, понятный offline/error state, retry и status link |
| Home → первая ценность | Лучшие дают guest/free/no-card proof; худшие требуют оплату вслепую | Один реальный бесплатный connect с лимитом, без карты |
| Connect → доказательство | 6/22 прошли полностью; TipTop и VPN Наружу доказали опасность UI-only success | Проверять tunnel, DNS, HTTPS и route до зелёного состояния |
| Выбор маршрута | Purpose presets намного понятнее голых стран/протоколов | Fastest + задачи + поиск/избранное + advanced ручной слой |
| Сбой → восстановление | Обычно support/Telegram; Vanya — лучший self-repair model | Автоматический ladder и гарантированный возврат обычной сети |
| Free → paid | Часто скрывают term/renewal или ставят hard wall | Полная цена/renewal/refund до CTA; trial без карты либо ясное подтверждение |
| Второе устройство / TV | У зрелых — QR/code, device hub и manual clients | QR login, device management и download hub |
| Retention / referral | Сильные loops есть, но много манипуляции отзывами | Inbox, status, compensation и reward за реальные события |
| Trust / legal | Юрлица и claims регулярно расходятся | Responsibility map + machine-fed facts + transparency/release evidence |

## Визуальные референсы

### Hiro: бренд и продуктовая экономика

![HiroVPN home](./raw/hiro-vpn/2026-07-22/screenshots/03-home.png)

![HiroVPN quests](./raw/hiro-vpn/2026-07-22/screenshots/04-quests.png)

### Огонь: routing как пользовательская задача

![Огонь VPN — категории обхода](./raw/ogon-vpn/2026-07-22/screenshots/16-bypass-sites-tab.png)

### Vanya: честный empty state и portable key

![Vanya VPN empty state](./raw/vanya-vpn/2026-07-22/screenshots/04-after-privacy-accept.png)

### Proton: guest-first бесплатный продукт

![Proton VPN guest shell](./raw/proton-vpn/2026-07-22/screenshots/04-guest-after-consent.png)

### Red Shield: power-user controls под простым Home

![Red Shield split modes](./raw/red-shield-vpn/2026-07-22/screenshots/16-split-tunneling-modes.png)

### CyberGhost: переиспользуемая store-кампания

![CyberGhost store campaign](./raw/cyberghost/2026-07-22/store-creatives/apple-iphone-04.webp)

### AdGuard: exclusions как самостоятельный продукт

![AdGuard domain exclusions](./raw/adguard-vpn/2026-07-22/screenshots/22-exclusions.png)

![AdGuard preset catalog](./raw/adguard-vpn/2026-07-22/screenshots/27-social-domain-presets.png)

### 4ebur.net: anti-block режимы человеческим языком

![4ebur route-type explainer](./raw/4ebur-net/2026-07-22/screenshots/05-region-type-info.png)

![4ebur route filters](./raw/4ebur-net/2026-07-22/screenshots/17-filter-bypass.png)

### VPN Наружу: одна жёсткая идея и узнаваемая упаковка

![VPN Наружу first launch](./raw/vpn-naruzhu/2026-07-22/screenshots/01-isolated-launch.png)

![VPN Наружу website hero](./raw/vpn-naruzhu/2026-07-22/screenshots/22-website-hero.png)

### MORI: store-дизайн сильнее текущей release truth

![MORI fast connection creative](./raw/mori-vpn/2026-07-22/screenshots/play-creative-01-fast-connection-phone.webp)

### Quattro: owned cabinet, тарифная экономика и каталог

![Quattro payment configurator](./raw/quattro-vpn/2026-07-22/screenshots/40-cabinet-payment.png)

![Quattro server catalog](./raw/quattro-vpn/2026-07-22/screenshots/44-cabinet-servers.png)

![Quattro instruction hub](./raw/quattro-vpn/2026-07-22/screenshots/45-cabinet-instructions.png)

## Индекс карточек и доказательств

| Карточка | Raw evidence |
| --- | --- |
| [HiroVPN](./hiro-vpn.md) | [`raw/hiro-vpn/`](./raw/hiro-vpn/) |
| [Огонь VPN](./ogon-vpn.md) | [`raw/ogon-vpn/`](./raw/ogon-vpn/) |
| [Батя VPN](./batya-vpn.md) | [`raw/batya-vpn/`](./raw/batya-vpn/) |
| [Vanya VPN](./vanya-vpn.md) | [`raw/vanya-vpn/`](./raw/vanya-vpn/) |
| [Kakadu](./kakadu-vpn.md) | [`raw/kakadu/`](./raw/kakadu/) |
| [Durev VPN](./durev-vpn.md) | [`raw/durev-vpn/`](./raw/durev-vpn/) |
| [Космос VPN](./kosmos-vpn.md) | [`raw/kosmos-vpn/`](./raw/kosmos-vpn/) |
| [GnuVPN](./gnuvpn.md) | [`raw/gnuvpn/`](./raw/gnuvpn/) |
| [BlancVPN](./blancvpn.md) | [`raw/blancvpn/`](./raw/blancvpn/) |
| [Ping VPN](./ping-vpn.md) | [`raw/ping-vpn/`](./raw/ping-vpn/) |
| [Proton VPN](./proton-vpn.md) | [`raw/proton-vpn/`](./raw/proton-vpn/) |
| [TipTop VPN](./tiptop-vpn.md) | [`raw/tiptop-vpn/`](./raw/tiptop-vpn/) |
| [Red Shield VPN](./red-shield-vpn.md) | [`raw/red-shield-vpn/`](./raw/red-shield-vpn/) |
| [ExpressVPN](./expressvpn.md) | [`raw/expressvpn/`](./raw/expressvpn/) |
| [Pipster](./pipster.md) | [`raw/pipster/`](./raw/pipster/) |
| [CyberGhost](./cyberghost.md) | [`raw/cyberghost/`](./raw/cyberghost/) |
| [Lagom VPN](./lagom-vpn.md) | [`raw/lagom-vpn/`](./raw/lagom-vpn/) |
| [AdGuard VPN](./adguard-vpn.md) | [`raw/adguard-vpn/`](./raw/adguard-vpn/) |
| [4ebur.net](./4ebur-net.md) | [`raw/4ebur-net/`](./raw/4ebur-net/) |
| [VPN Наружу](./vpn-naruzhu.md) | [`raw/vpn-naruzhu/`](./raw/vpn-naruzhu/) |
| [MORI VPN](./mori-vpn.md) | [`raw/mori-vpn/`](./raw/mori-vpn/) |
| [Quattro VPN](./quattro-vpn.md) | [`raw/quattro-vpn/`](./raw/quattro-vpn/) |

## Границы аудита

- Ничего не покупалось, trial с автосписанием не активировался, отзывы/рейтинги/посты/сообщения support не отправлялись.
- Платные и account-gated экраны помечены отдельно от реально пройденного runtime.
- Текущие IP, raw configs, endpoints, токены, QR payloads, email, one-time codes и диагностические идентификаторы не хранятся в worktree.
- Часть текущих registry records и Proton audit PDF остались `BLOCKED_BY_ACCESS`; они не выданы за просмотренные.
- Store recommendations — алгоритмическая соседняя выдача, а не доказанные рекомендации реальных клиентов.
- После последнего приложения все протестированные процессы и Android Chrome были остановлены, `tun0` отсутствовал, always-on/lockdown VPN не был задан, исходная ориентация LDPlayer восстановлена.

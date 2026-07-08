# Telegram VPN market: bots, sites, webapps, and POKROV comparison

Дата: 2026-07-08
Окно постов: 2026-05-08..2026-07-08
Фокус: Telegram VPN-сервисы, их боты, каналы, сайты, кабинеты, вебаппы, приложения, промо, реферальные механики и сравнение с POKROV.

## Короткий вывод

Рынок уходит от схемы "только Telegram-бот выдал ссылку" к связке:

1. Канал как агрессивная воронка и доверие через посты.
2. Бот как быстрый checkout, trial, инструкции и support-router.
3. Сайт или кабинет как запасной контур, если Telegram недоступен.
4. App-first или хотя бы third-party-client-first установка: Happ, v2raytun, VLESS, Hysteria2, собственные APK/App Store приложения.
5. Постоянные operational updates: App Store removal/return, RKN, DNS, white-list routes, новые локации, обновления приложения.

POKROV уже стратегически стоит правильно: app-first, Telegram не нужен для старта, есть кабинет, есть 5 дней без карты, есть +10 дней за Telegram, есть честная beta-подача. Но конкуренты сильнее в трех практичных вещах:

- они громче показывают "куда идти, если Telegram/приложение/маршрут сломался";
- они превращают каждый инцидент и апдейт в контент;
- у некоторых веб-кабинет уже выглядит как продуктовая защита от зависимости Telegram, а не как вторичная страница.

Самые полезные конкуренты для POKROV сейчас: Quattro, Cats, Nosok, Kosmos, OpenGate. Второй слой: Luma, VPN PLATINA, Nash, MORI, 4ebur, GROZA, NEO, Fen, ArtVPN.

## Метод и ограничения

Использовано:

- Telegram Web bot flows из первого прохода.
- Публичные Telegram/t.me карточки ботов и каналов.
- TGStat public channel pages `https://tgstat.ru/channel/@username`.
- Вложенный TGStat-style export из `pasted-text.txt`.
- Открытые сайты и кабинеты: Cats, Nosok, Kosmos, OpenGate, POKROV, Google Play pages для Luma/4ebur/Kosmos.
- Предыдущие файлы доказательств:
  - `docs/competitive/telegram-vpn-2026-07-08/report.md`
  - `docs/competitive/telegram-vpn-2026-07-08/wave2-report.md`
  - `docs/competitive/telegram-vpn-2026-07-08/tgstat-public-check.md`
  - `docs/competitive/telegram-vpn-2026-07-08/telegram-vpn-final-safe-contact-sheet.png`

Ограничения:

- TGStat `/stat` после логина все еще показывал auth wall; детальные ER/динамики брались из public pages и вложенного экспорта.
- TGStat bot pages через `/bot/@username` возвращали 404; bot MAU брались из публичных `t.me/<bot>` карточек.
- В каналы, где бот требует обязательной подписки, без отдельного разрешения не вступал.
- Новые аккаунты/покупки/сообщения не отправлялись.
- Сырые скрины с trial keys, subscription URLs, Telegram ID или generated codes не включены в публичный contact sheet.

## Shortlist из вложенного TGStat export

Это не "все подряд", а полезные кандидаты из 209 строк: масштаб, рост, охват, продуктовая зрелость или аномалия.

| Канал | Подписчики | +7 дней | Охват 1 поста | CI | Зачем смотреть |
| --- | ---: | ---: | ---: | ---: | --- |
| Quattro VPN - Новости | 1,038,593 | +7,908 | 426k | 63.8 | Главный эталон масштаба, app updates, web cabinet, own Android APK. |
| VPN PLATINA | 107,721 | +5,791 | 39.8k | 2.6 | Быстрый рост, cash/TON referral payouts, отдельные bot/sales/support surfaces. |
| Носок VPN - Канал | 202,395 | +5,643 | 102.1k | 8.1 | Website, Telegram fallback after expiry, strong referral. |
| Cats VPN - Канал | 17,555 | +4,458 | 10.5k | 7.4 | Лучший найденный web-cabinet idea: anonymous short-code login. |
| Luma VPN / Прокси | 17,199 | +3,454 | 91.6k | 0.0 | Аномально высокий reach при малом канале, app-first/app-store lane. |
| NBB VPN | 27,462 | +2,629 | 10.6k | 60.2 | Высокий citation index; нужен отдельный ad/channel follow-up. |
| Батя VPN | 183,862 | +2,403 | 74.4k | 0.2 | Большой канал, полезен для рекламного/медийного анализа. |
| Kyra VPN & Proxy | 49,973 | +2,241 | 98.3k | 0.1 | Очень высокий reach; стоит смотреть как traffic channel. |
| cisvpn | 52,471 | +1,952 | 67.4k | 10.4 | Высокий reach + CI; кандидат для следующего прохода. |
| ENOT VPN | 37,798 | +1,765 | 82.3k | 0.3 | Reach выше базы подписчиков, вероятен закуп/перелив трафика. |
| OpenGate/TG Proxy layer | 4,408 для proxy channel из export; 61k bot MAU по t.me | +385 | 25.7k | 0.0 | Не самый большой, но сильный ops/support pattern. |

Отсечено как менее полезное на текущем шаге: каналы без явного продукта, каналы с нулевым reach при росте, мусорные "бесплатный ВПН" сборники, generic repost hubs, маленькие каналы без веб/бот/приложения.

## Рынок по слоям

### 1. Канал

Канал у конкурентов почти всегда делает одну из пяти задач:

- давит на страх: RKN, App Store removal, Telegram blocking, DNS, "обычные VPN больше не работают";
- продает urgency: скидка до конца дня, promo code, "последний день";
- объясняет аварии и обходы: update subscription, switch country, proxy, new protocol, autobalancer;
- показывает продуктовую жизнь: APK release, locations, pings, new servers, traffic economy;
- собирает доверие: отзывы, компенсации, "мы не виноваты, это DNS/RKN", "мы вернули Happ".

Сильный паттерн: Quattro и OpenGate пишут как продуктовые операторы, а не как скидочный канал. MORI пишет длинные educational posts и превращает безопасность в маркетинг. Nash хорошо говорит в кризисе простым языком.

### 2. Бот

У сильных Telegram VPN ботов первый экран обычно содержит:

- trial или buy;
- platform installation;
- "мой доступ / мои подписки";
- support;
- channel/news CTA;
- referral/invite;
- sometimes Telegram proxy or emergency mode.

Слабые боты сразу выдают raw subscription URL. Это быстро, но рискованно: ссылка становится bearer secret и ломает нормальную app/cabinet identity.

POKROV здесь должен держать свой принцип: app/cabinet first, raw link only in recovery/manual context.

### 3. Сайт

Сайт становится не маркетинговой роскошью, а survival surface:

- Cats: "ни почты, ни паролей", короткий код для кабинета.
- Nosok: публичный сайт, server availability, support contacts, email/Telegram login.
- Kosmos: полноценный marketing site + LK with email/Google/Yandex login.
- OpenGate: сайт говорит "VPS в твоем мессенджере", продает Telegram-first route, но имеет public surface.
- Quattro: сайт/кабинет и приложение как mature product line.

POKROV уже имеет `pokrov.space`, `app.pokrov.space`, `pay.pokrov.space`, но надо сильнее проговорить "если Telegram недоступен, заходи в приложение/кабинет".

### 4. Webapp / кабинет

Лучшие кабинеты делают не "страницу после логина", а контроль:

- status;
- tariffs;
- invoices/payments;
- referral;
- import existing bot subscription;
- device limits;
- support;
- recovery.

Cats особенно важен: короткий код решает fear "Telegram заблокируют, я потеряю доступ". Минус: code-only recovery опасен, если пользователь не сохранил код.

Для POKROV лучший вариант: backup recovery code как дополнительный fallback, но не как единственный account identity.

### 5. Приложения и клиенты

Типовые клиенты:

- Happ;
- v2raytun;
- VLESS/V2RayNG/Hiddify/Nekobox;
- Streisand/INCY;
- own APK/App Store app у 4ebur, Kosmos, Quattro, Luma;
- Hysteria2 у Quattro.

POKROV сильнее там, где остается owned app-first, а не "скопируй ссылку в Happ". Но рынок приучает пользователя к fallback: если POKROV app unavailable, должна быть честная manual compatibility lane.

## Competitor matrix

| Конкурент | Сила | Bot | Site/webapp | App/client | Trial/price/referral | Что взять POKROV |
| --- | --- | --- | --- | --- | --- | --- |
| Quattro | Огромный масштаб + mature product updates | `@quattrovpn_bot`, ~455k MAU | `quattro.app`, web cabinet | Own Android APK, Hysteria2, app tunneling, DNS, IPv4/IPv6 | Cabinet configurator days/GB/devices; referral/partner tracking | Release-note machine, product changelog as trust, configurator ideas only if needed. |
| Cats | Лучший кабинетный паттерн | `@CatsVPN_robot`, gate by channel | `catsvpn.net`, `lk.catsvpn.net` | Happ/v2raytun/Hiddify/Nekobox | Short-code login, 149 RUB/mo observed, 50% referral | Backup recovery code, bot-to-site import, "web survives Telegram" copy. |
| Nosok | Масштаб + fallback narrative | Bot likely channel-gated | `nosokvpn.com` | Site + Telegram flow | 1 day/2 devices/10GB card; inconsistent 3-day CTA; 3-level referral 50/25/15 in older posts | Expired subscription support/renew mode; website as backup route. |
| Kosmos | Closest to app-first | `@kosmos2vpnbot`, ~42k MAU | `kosmosvpn.ru`, `lk.kosmosvpn.ru` | Own app on stores | 14-day trial; 240/490/790 monthly site tiers | App-first proof, email/social login, but avoid confusing email/start flow. |
| OpenGate | Best support/ops UX | `@opengatevpn_bot`, ~61k MAU | `opengate.ink` | Happ/key flow | 7-day trial; Personal/Duo/Family | Support menu: install, not working, low speed, service issue, autobalancer updates. |
| Luma | App-first signal + reach anomaly | `@luma_vpn_app_bot` / web launch page signal | `vpn-luma.xyz` says Telegram webapp only; Google Play app exists | Google Play `net.luma.luma`, 1K+ downloads, updated 2026-06-21 | Infrastructure/location posts with huge views | Watch app-store positioning; use pings/location posts carefully with proof. |
| VPN PLATINA | Fast growth/referral pressure | `@vpnplatina_bot`, ~63k MAU | not enough public web signal | Telegram-first | Fixed referral payouts 50/80/150/250 RUB, card or GRAM/TON | Referral clarity, but avoid cash payouts before abuse/finance controls. |
| Nash | Big bot + clear install menu | `@nash_vpn_bot`, ~113k MAU | unclear | Apps + bot key + docs | 299/790/1390/2690 | Incident posts: provider/city data, workaround, resolution. |
| MORI | Educational aggressive marketing | `@morivpnrobot`, mini app prompt | Mini App, site signals weaker/inconsistent | MORI/Happ keys | 250/299 conflict; compensation posts | Educational posts, but avoid price inconsistency and overclaims. |
| 4ebur | Mascot + app stores + routing posts | `@net4ebur_bot`, Mini App | `net4eburvpn.com`, `4ebur.net` | Google Play 500K+ downloads, App Store app | public prices 299/799/1500 in prior pass | Mascot/content cadence, server load/routing state. |
| GROZA | Strong white-list/product limit messaging | `@VPN_GROZA_BOT`, ~39k MAU | no strong public site | Happ/key flow | 48h trial; mobile/Wi-Fi white-list coefficients | If POKROV ships white-list mode, show limits/coefficient clearly. |
| NEO | Protocol/proxy architecture | `@neovpnbot`/`@neovpn`, ~43k MAU | no clear site | VLESS/protocol/proxy | 222/mo, 111/2w, 2222/year | Advanced protocol fallback UI, but keep tone sane. |
| Fen | Clean constructor | `@fenvpnrobot` | no strong public site | Common clients | 24h trial, 299/mo 1 device, traffic counters | Paid constructor patterns, not raw-link-first UX. |
| ArtVPN | Simple bot + instant trial | `@artvpn_bot` | not enough public site | Happ | 3-day trial; 250/650/1250 for 2 devices; Lava | Payment reassurance: no card storage, no auto-charge. |

## Competitor notes

### Quattro VPN

Why important:

- Largest useful competitor in the export: 1,038,593 subscribers, +7,908 in 7 days, 426k post reach.
- Bot public card: about 455k monthly users.
- Mature product story: web cabinet, own Android APK, frequent Android release posts, Hysteria2, traffic/LTE economy.
- 2026-07-08 public signal: Android update `Quattro 0.18.1.apk`.
- 2026-04-22 post: web cabinet with configurator for days/GB/devices, multi-subscriptions, device extension, traffic purchase, reissue, locations, referral/partner payments, promo codes.

What they do well:

- Every technical release becomes a trust artifact.
- Cabinet is a product, not a login wall.
- They show operational momentum: app versions, bugs fixed, protocol/capacity work.

Risk/weakness:

- High complexity: GB/devices/days configurator can become too much for normal consumer UX.
- If POKROV copies this too early, it can damage the app-first simplicity.

POKROV move:

- Create Telegram/channel release-note template for each Android/Windows build:
  - what changed for user;
  - who needs update;
  - known limitations;
  - where to download/check current version;
  - what to do if it does not connect.

### Cats VPN

Why important:

- Not biggest, but highest product idea density.
- Export: 17,555 subscribers, +4,458 in 7 days.
- Website claims 40,000+ users.
- Public site says: VLESS/VMess, Happ/v2raytun/Hiddify/Nekobox, no email/password account, all platforms, support in Telegram.
- LK says directly: "Ни почты, ни паролей. Только короткий код".

Best patterns:

- Anonymous short-code login is very clear.
- Site explains web account as independence from Telegram.
- Bot-to-site import code lets existing Telegram users migrate into web account.
- Tariff UI is clean.
- Referral offer is strong: 50% forever from invited payments.

Risks:

- Code-only login is harsh: lose code before binding Telegram and account can be unrecoverable.
- Site uses claims like "военное шифрование", "нулевые логи" that need evidence.
- Bot deeper flow requires joining channel.

POKROV move:

- Add "backup recovery code" after account creation or in Account settings.
- Use it as extra recovery, not the primary identity.
- Add copy: "Telegram не нужен для старта. Если Telegram недоступен, откройте приложение или кабинет".
- Do not copy "military-grade" / "zero logs" unless evidence and policy are ready.

### Nosok VPN

Why important:

- Export: 202,395 subscribers, +5,643 in 7 days, 102.1k reach.
- Website has public landing, server availability, tariffs placeholder, contacts.
- Older public posts claim website launch with bot-like functionality: buy/renew, add/remove devices, manage subscriptions, cabinet, support/recovery.
- Strong fallback story: Telegram-only access remains after subscription expiry for several days in earlier signals.

Best patterns:

- Recovery after expiry is smart: user can still reach renewal/support.
- Website gives non-Telegram support path.
- Referral mechanics are aggressive and easy to understand.

Risks:

- Site copy had inconsistency between 1-day trial card and 3-day CTA in prior pass.
- Support promises can be too broad if not backed by actual workflow.

POKROV move:

- Implement or expose a limited expired-access mode:
  - not full VPN;
  - renewal/support/account recovery still available;
  - app/cabinet can show exact next step.

### Kosmos VPN

Why important:

- Bot public card: about 42k monthly users.
- Own app: Google Play shows "Космос VPN", 100K+ downloads.
- Site: public marketing, tariffs 240/490/790 RUB/month tiers, legal/company details.
- LK: email code login plus Google/Yandex.
- Bot granted 14-day trial in prior Telegram pass.

Best patterns:

- Strong app-first competitor.
- 14-day trial is the most aggressive confirmed in the set.
- LK has mainstream login: email/social, not only Telegram.
- Site has legal/company surface, which helps trust.

Risks:

- Bot copy said email required but trial started without email: confusing identity story.
- Site has generic security copy and some B2B-ish tariff wording that may not match normal consumer.

POKROV move:

- Keep app-first, but be clearer than Kosmos:
  - app starts trial;
  - cabinet continues account;
  - Telegram is optional bonus/recovery.
- Do not extend trial to 14 days unless economics and abuse controls support it.

### OpenGate

Why important:

- Bot public card: about 61k monthly users.
- Strongest support/ops UX from first pass.
- Public site positions as "VPS в твоём мессенджере", starting from free, then 99 RUB/month.
- Bot had 7-day trial, Personal/Duo/Family plans, platform instructions, "not working" and "low speed" support routes.
- Channel posts: autobalancer, MTProto proxy, old-key shutdown, protocol changes, server/country updates.

Best patterns:

- Support is not hidden: platform install, not working, low speed, service problems are first-class.
- Honest caveat around white-list behavior: not always guaranteed, not always refund reason.
- Operational posts are concrete.

Risks:

- Depends heavily on third-party client layer.
- "VPS" wording may reduce clarity for normal users.

POKROV move:

- Add first-class support categories:
  - install Android;
  - install Windows;
  - app update;
  - no connection;
  - low speed;
  - payment/renewal;
  - Telegram bonus;
  - account recovery.

### Luma VPN

Why important:

- Export: 17,199 subscribers, +3,454 in 7 days, 91.6k reach. That reach is anomalous.
- Google Play app exists: `net.luma.luma`, 1K+ downloads, updated 2026-06-21.
- Public app copy is clean: one-tap connect, reliable on mobile networks/public Wi-Fi, censorship angle, transparent data practices.
- Public page `vpn-luma.xyz` says Luma runs inside Telegram only and points to `@luma_vpn_app_bot`.

Best patterns:

- App-store trust lane.
- Infrastructure posts with ping/RTT claims are easy to consume.
- App copy is calmer than many Telegram-first competitors.

Risks:

- Low downloads compared with channel reach raises questions about funnel quality.
- Contact/data policy claims need deeper verification before copying.

POKROV move:

- Track Luma as app-first competitor.
- Use location/ping posts only if POKROV has current measurement evidence.

### VPN PLATINA

Why important:

- Export: 107,721 subscribers, +5,791 in 7 days.
- Bot public card: about 63k monthly users.
- Referral post: fixed payouts by term, paid to bank card or GRAM/TON.
- Separate support/payment surfaces were observed.

Best patterns:

- Referral is extremely concrete: user understands what they get.
- Cash/crypto payout increases promoter motivation.

Risks:

- Cash payouts invite fraud, multi-account abuse, support load, tax/payment issues.
- It can attract low-quality affiliates.

POKROV move:

- Near-term: day bonuses, visible referral status, referral history.
- Later: cash payouts only after abuse controls, finance flow, payout ledger, KYC/tax decision.

### NashVPN

Why important:

- Bot public card: about 113k monthly users.
- Channel public signals: blunt incident comms around RKN/DNS, update subscriptions, location workaround.
- Bot menu was clear: get VPN, locations, invite, help, install.

Best patterns:

- Incident language is direct and useful.
- They explain whether issue is servers, DNS, RKN, region, or user action.
- Install menu covers all platforms.

Risks:

- "Update subscription daily" feels like a workaround, not confidence.

POKROV move:

- Prepare incident template:
  - symptom;
  - affected platforms/providers/regions;
  - what user should do now;
  - whether payment/access is affected;
  - next update time;
  - resolution summary.

### MORI

Why important:

- Channel: educational/security posts, not only promos.
- Bot: Mini App/app prompt, account status, MORI/HAPP subscriptions.
- Turns incidents into teaching: DNS leaks, WebRTC, browser fingerprinting, cookies, free/cheap VPN risks.

Best patterns:

- Education is a real content lane.
- They build trust by explaining threats.

Risks:

- Price/device/torrent conflicts observed between surfaces.
- Some copy can become fear-heavy.
- Telegram Ads inside bot surface showed competitors buying VPN intent there.

POKROV move:

- Use educational posts, but calmer:
  - why app-first is safer than pasted links;
  - what Telegram bonus does and does not do;
  - how to check connection;
  - why manual links are recovery-only.

### 4ebur

Why important:

- User's screenshot showed branded mascot posts and coupon `SUMMERTIME` -25%.
- TGStat public page found `@net4ebur`; recent posts about app/platform update, Happ App Store removal, traffic masking.
- Google Play page: 500K+ downloads, updated 2026-07-02, 3.5 rating, 6.9k reviews.
- Public app copy uses broad privacy/security claims and customer support promise.

Best patterns:

- Mascot gives memorability.
- Channel/bot posts are image-led and easy to scan.
- Routing mode/load colors from previous pass are useful.

Risks:

- App reviews include complaints about uptime/kill switch/support.
- Google Play copy says "best performance/security" style claims.

POKROV move:

- Consider simple route health/status labels in app:
  - recommended;
  - busy;
  - degraded;
  - maintenance.
- Use mascot/brand art only if it does not make POKROV feel toy-like.

### GROZA

Why important:

- Strong white-list/mobile-operator product messaging.
- Trial 48h.
- Claims: private servers, anti-block protection, up to 25Gb/s, no ads/no crashes, white-list mobile/Wi-Fi limits.

Best patterns:

- White-list limits and coefficients are explicit.
- Repeated footer CTA in posts is good.

Risks:

- Very high performance/anti-block claims need proof.
- Purchase flow pricing was not fully recovered in WebK.

POKROV move:

- If POKROV ships ad-domain/white-list/routing modes, show:
  - included traffic;
  - exclusions;
  - mobile vs Wi-Fi behavior;
  - expected failure cases;
  - support path.

### NEO

Why important:

- Bot had balance/device/protocol/proxy architecture.
- Prices observed: 111/2 weeks, 222/month, 667/3 months, 1332/6 months, 2222/year.
- Voice is memorable but chaotic.

Best patterns:

- Protocol switch and proxy product are useful for recovery.

Risks:

- Heavy anti-state tone.
- TGStat did not find `@followNeo`.

POKROV move:

- Advanced fallback belongs under "advanced/recovery", not main path.

### Fen

Why important:

- Bot trial flow and purchase constructor are clean.
- Buy constructor: period/devices/promo/continue.
- Shows traffic counters and white-list GB.

Best patterns:

- Simple paid constructor.
- Clear status counters.

Risks:

- Raw subscription URL shown during trial.
- Public channel mostly crisis/silence.

POKROV move:

- Keep status counters, but hide raw bearer links from first-layer UI.

### ArtVPN

Why important:

- Very low friction trial: button generated working free access.
- Payment copy around Lava/card/no auto-charge was reassuring.
- Commands are simple: payment, cabinet, promo, help, database, about.

Best patterns:

- Simple command list.
- Payment reassurance.

Risks:

- Overclaims: "impossible to ban", full anonymity.
- Raw key delivery.

POKROV move:

- Add payment reassurance in checkout/bot:
  - no auto-charge;
  - one-time activation/access key;
  - no card on trial;
  - support route.

## POKROV baseline

Current POKROV truth:

- Brand/product: `POKROV`.
- Strategy: consumer-first, app-first.
- Trial: 5 days.
- Telegram reward: +10 days.
- Telegram is optional for first launch, trial and normal use.
- Recovery order: POKROV app -> web cabinet -> Telegram fallback.
- Default client core: sing-box.
- Advanced fallback: xray only in advanced settings.
- Public surfaces:
  - `https://pokrov.space/`
  - `https://app.pokrov.space/`
  - `https://pay.pokrov.space/checkout/`
  - `https://connect.pokrov.space/`
  - `@pokrov_vpn`, `@pokrov_vpnbot`, `@pokrov_supportbot`, `@pokrov_feedbackbot`

Live public homepage already says:

- POKROV opens YouTube/TikTok/other services.
- Android + Windows.
- 5 days free, no card.
- Telegram not needed for start.
- +10 days for Telegram channel.
- Paid access starts from 99 RUB for 30 days.
- Cabinet/support are visible.

This is good. The gap is not positioning; the gap is operational depth and survival storytelling.

## POKROV vs competitors by point

### Acquisition hook

Competitors:

- Fear-heavy: RKN, blocks, App Store removal, Telegram shutdown.
- Discount-heavy: last day, coupon, promo.
- Utility-heavy: YouTube, TikTok, Discord, Instagram, mobile operators.

POKROV:

- Cleaner hook: app opens services, 5 days no card, Android/Windows.

Verdict:

- Keep calm directness.
- Add more concrete recovery/status language.
- Do not become a panic channel.

### Trial

Competitors:

- 24h Fen.
- 48h GROZA.
- 3 days Art/Cats older signal.
- 7 days OpenGate/NEO public signals.
- 14 days Kosmos.
- 1 day/10GB Nosok site signal.

POKROV:

- 5 days premium-grade access, no card.

Verdict:

- 5 days is enough if framed as quality: "проверить на телефоне, Wi-Fi, мобильной сети и Windows".
- Do not chase 14 days unless abuse/economics are ready.

### Telegram dependency

Competitors:

- Many require channel subscription before bot use.
- Many are Telegram-first purchase/support.
- Cats/Nosok/Kosmos reduce dependency with web/LK.

POKROV:

- Telegram optional for start; bonus/recovery/support fallback.

Verdict:

- This is a strategic advantage. Say it more.
- Recommended copy angle: "Если Telegram недоступен, приложение и кабинет остаются основным маршрутом".

### Website/cabinet

Competitors:

- Cats: code login.
- Nosok: site + contacts.
- Kosmos: email/social login LK.
- Quattro: mature cabinet.
- OpenGate: public site but Telegram-first.

POKROV:

- Marketing, webapp/cabinet, checkout, connect host.

Verdict:

- POKROV should present cabinet as survival/control surface:
  - access status;
  - renewal;
  - support;
  - redeem;
  - downloads;
  - account recovery.

### Bot UX

Competitors:

- Best bot menus: OpenGate, Nash, Fen.
- Fastest trial: ArtVPN/Fen.
- Best advanced architecture: NEO.

POKROV:

- Should remain fallback/continuation, not primary wall.

Recommended first-layer bot menu:

- Открыть приложение
- Получить 5 дней
- Кабинет
- Продлить
- Бонус +10 дней
- Инструкция Android
- Инструкция Windows
- Не работает / низкая скорость
- Поддержка
- Новости

Manual link/QR:

- only under "Ещё" or explicit recovery.

### Pricing

Competitors:

- Cheap anchors: OpenGate 99/month public site, Cats 149/month observed, NEO 222/month, Kosmos 240/month, Nash 299/month, Fen 299/month.
- Some have family/duo/multi-device.
- Some hide pricing until bot flow.

POKROV:

- Public homepage shows 99 RUB first 30 days after trial.

Verdict:

- Strong enough as entry.
- Need avoid "99 forever" confusion if it is start action price.
- Show what happens after first paid month.

### Referral

Competitors:

- Cats: 50% forever.
- Nosok: 3 levels 50/25/15 in older signals.
- PLATINA: fixed cash/TON payout per plan term.
- Quattro: partner/referral cabinet tracking.

POKROV:

- Referral summary exists as backend/app-facing contract; public reward currently less aggressive.

Verdict:

- Short term: visible invite link, days earned, referral history, next reward.
- Medium term: campaignable referral tiers.
- Avoid cash payout until abuse/payment operations are ready.

### Support

Competitors:

- OpenGate is strongest: not working, low speed, install, platform guides, support center.
- Nash is strong in incident communication.
- Kosmos/Nosok have web contacts.

POKROV:

- App/cabinet support should be real ticket lifecycle; support bot/email fallback exist.

Verdict:

- Make support categories visible everywhere.
- Add "support with context" from app: device, OS, route mode, app version, access state.

### Incident and update comms

Competitors:

- Quattro posts app updates constantly.
- OpenGate posts protocol/server/autobalancer changes.
- Nash explains DNS/RKN incidents.
- MORI turns incidents into educational posts.

POKROV:

- Has dynamic content model and Telegram channel, but needs stronger cadence.

Verdict:

- Create fixed templates now, before the next incident.

## Aggressive marketing patterns worth understanding

Competitors repeat these lines:

- "Telegram/YouTube/Instagram blocked, ordinary VPN no longer works."
- "Happ removed from App Store / returned to App Store."
- "White lists / mobile operators / LTE economy."
- "RKN killed DNS / update subscription / switch location."
- "No logs / military encryption / anonymous / impossible to block."
- "Trial now / discount today / promo code."
- "Join channel to use bot."
- "Referral money to card/TON."

POKROV should not copy the worst language. Better version:

- talk about specific user problem;
- show the exact next action;
- be honest about beta, app availability, payment and routing;
- use proofs: app version, status, release notes, support routes.

## What POKROV should do next

### P0: This week

1. Make web/cabinet survival copy explicit.
   - Homepage, bot welcome, support bot:
   - "Telegram не нужен для старта. Если Telegram недоступен, откройте приложение или кабинет."

2. Add bot quick menu parity with the market.
   - App
   - 5-day trial
   - Cabinet
   - Renew
   - Bonus +10 days
   - Android instruction
   - Windows instruction
   - Not working
   - Low speed
   - Support
   - News

3. Write 4 reusable Telegram post templates.
   - Release/update post.
   - Incident start/update/resolution post.
   - Educational post.
   - Promo/referral post.

4. Tighten checkout perception.
   - Live public checkout currently exposes loading/copy like "Собираем публичный каталог" in public HTML.
   - If tariffs can load only client-side, add clear fallback: cabinet/support/retry.
   - If payment gate is intentionally degraded, say so plainly.

5. Add "support categories" to bot/cabinet/app.
   - No connection.
   - Low speed.
   - Install/update app.
   - Payment/activation key.
   - Telegram bonus.
   - Account recovery.

### P1: Next product pass

1. Backup recovery code.
   - Inspired by Cats, but safer.
   - Show once, allow regenerate with account session.
   - Not the only identity.

2. App/cabinet status labels.
   - Inspired by 4ebur/OpenGate.
   - Recommended / busy / degraded / maintenance.

3. Referral dashboard.
   - Invite link.
   - Earned days.
   - Pending/confirmed referrals.
   - Promo code entry/history.

4. Expired-access support mode.
   - Inspired by Nosok.
   - After expiry, user can still open support/renew/account route.

5. Release-note cadence.
   - Inspired by Quattro.
   - Every Android/Windows build becomes a channel post with user benefit.

### P2: Later, only with evidence

1. Cash affiliate payouts.
   - Needs anti-abuse, payout ledger, finance policy.

2. White-list/mobile-operator mode.
   - Needs routing product decision, limits, failure behavior.

3. Public speed/ping claims.
   - Needs current measurement evidence and methodology.

4. Store availability claims.
   - Only after store/release gate proof.

## What POKROV should not copy

- Fake counters like "80k online" without evidence.
- "Military-grade" and "zero logs" unless policy/evidence are ready.
- "Impossible to block/ban."
- Forced channel subscription before core trial.
- Raw subscription link as first-layer bot UX.
- Cash/crypto referral payouts before abuse controls.
- Contradictory pricing between site, bot, channel.
- Overcomplicated tariff configurator before product-market fit.
- Panic-only tone.

## Suggested POKROV content angles

### Product update

Title: `POKROV обновился: что стало проще`
Body points:

- new app version;
- what changed for Android/Windows;
- who should update;
- where to check current access;
- support link.

### Incident

Title: `Если сегодня не открывается YouTube/TikTok`
Body points:

- symptom;
- affected route/location/provider if known;
- what to press in app;
- whether access/payment is safe;
- next update time.

### Recovery

Title: `Telegram не обязателен для доступа`
Body points:

- start in app;
- cabinet route;
- Telegram only as bonus/support fallback;
- backup/recovery code once implemented.

### Bonus

Title: `+10 дней за Telegram-канал`
Body points:

- link account;
- subscribe;
- claim in app/cabinet;
- where to see bonus history.

## Evidence map

Local:

- Main bot/channel report: `docs/competitive/telegram-vpn-2026-07-08/report.md`
- Wave 2 report: `docs/competitive/telegram-vpn-2026-07-08/wave2-report.md`
- TGStat public check: `docs/competitive/telegram-vpn-2026-07-08/tgstat-public-check.md`
- Safe contact sheet: `docs/competitive/telegram-vpn-2026-07-08/telegram-vpn-final-safe-contact-sheet.png`
- Raw screenshots: `docs/competitive/telegram-vpn-2026-07-08/screenshots/`
- Wave 2 screenshots: `docs/competitive/telegram-vpn-2026-07-08/screenshots-wave2/`

Primary/public web sources checked:

- POKROV: `https://pokrov.space/`, `https://app.pokrov.space/`, `https://pay.pokrov.space/checkout/`
- Cats: `https://catsvpn.net/`, `https://lk.catsvpn.net/`, `https://t.me/CatsVPN_robot`, `https://t.me/catsvpn`
- Nosok: `https://nosokvpn.com/`, `https://t.me/NosokVPN`
- Quattro: `https://www.quattro.app/`, `https://t.me/QuattroVPN_NEWS`, `https://t.me/quattrovpn_bot`
- Kosmos: `https://kosmosvpn.ru/`, `https://lk.kosmosvpn.ru/`, `https://t.me/kosmos2vpnbot`
- OpenGate: `https://opengate.ink/`, `https://t.me/opengatevpn_bot`, `https://t.me/opengate_community`
- Luma: `https://vpn-luma.xyz/`, Google Play `net.luma.luma`, `https://t.me/lumavpn_landing`
- 4ebur: `https://net4eburvpn.com/`, `https://4ebur.net/`, Google Play `com.cheburnet.mobile`, `https://t.me/net4ebur_bot`, `https://t.me/net4ebur`
- VPN PLATINA: `https://t.me/vpnplatina`, `https://t.me/vpnplatina_bot`
- MORI: `https://t.me/MoriVpnOfficial`, `https://t.me/morivpnrobot`
- NEO: `https://t.me/neovpnbot`, `https://t.me/followNeo`
- Nash: `https://t.me/nashvpnnews`, `https://t.me/nash_vpn_bot`
- GROZA: `https://t.me/VPN_GROZA_BOT`, `https://t.me/VPN_GROZA_NEWS`
- Fen: `https://t.me/fenvpnrobot`

TGStat public pages:

- `https://tgstat.ru/channel/@catsvpn`
- `https://tgstat.ru/channel/@NosokVPN`
- `https://tgstat.ru/channel/@QuattroVPN_NEWS`
- `https://tgstat.ru/channel/@vpnplatina`
- `https://tgstat.ru/channel/@lumavpn_landing`
- `https://tgstat.ru/channel/@net4ebur`
- `https://tgstat.ru/channel/@MoriVpnOfficial`
- `https://tgstat.ru/channel/@nashvpnnews`
- `https://tgstat.ru/channel/@opengate_community`
- `https://tgstat.ru/channel/@VPN_GROZA_NEWS`

## Final priority list

1. Quattro: copy release cadence, not complexity.
2. Cats: copy recovery-code idea, not code-only identity.
3. OpenGate: copy support menu and ops clarity.
4. Nosok: copy expired renewal/support route.
5. Kosmos: copy app-first confidence and mainstream login clarity.
6. Nash: copy incident template.
7. MORI: copy educational content lane, reduce fear.
8. PLATINA: study referral pressure, do not copy cash payouts yet.
9. Luma: monitor app-store/app-first route.
10. 4ebur: consider route health/status labels and visual content cadence.

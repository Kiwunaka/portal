# Quattro VPN bot and channel deep dive

Дата прохода: 2026-07-09
Цель: полный разбор `@QuattroVPN_BOT`, кнопок, ссылок, инструкций и постов `@QuattroVPN_NEWS` за последние 2 недели.

Implementation note: this is capture evidence, not current POKROV product
canon. The approved `2026-07-10` Market-Ready CIS design supersedes older
`+10 days`, optional-gate and WARP-beta recommendations in this report.

## Status

Текущий статус: `DEEP_DIVE_CAPTURED_WITH_LIVE_WEB_APP`.

Что подтверждено живым проходом в Telegram Web:

- pre-gate `/start`;
- mandatory channel gate;
- legal links;
- main menu after subscription gate;
- payment intro;
- full 30-day and 90-day tariff/device/traffic matrix;
- payment-method screens for SBP, Russian bank card, Telegram Stars, Crypto Bot, Heleket;
- `Наш сайт` branch and personal `quattro.app/register?tg_link=...` link.

Что подтверждено живым проходом в `quattro.app` после логина:

- `/` dashboard;
- `/subscription` payment configurator;
- `/referral` referral page;
- `/partner` partner page;
- `/promo` promo code page;
- `/servers` server list;
- `/instructions` instruction hub;
- `/settings` account/security settings;
- `/terms` legal/support links.

Что дополнительно подтверждено static analysis of `quattro.app` SPA and user-provided OTP screenshot:

- email/password login and registration;
- email OTP code for registration/login/2FA;
- Telegram linking from site;
- subscription management for users with active subscription;
- admin routes exist in the bundle.

Remaining limitation:

- no destructive action was taken: no payment, no password/email change, no Telegram unlink, no 2FA enablement, no promo submission.
- Telegram Web started timing out on later re-open, so bot branches `Бонусы`, `Список серверов`, `Инструкции и поддержка` were not clicked live in the bot itself. Their product equivalents are now confirmed live in the web cabinet.
- Payment URLs, Telegram user ID, `tg_link`, order IDs, and one-time email code are intentionally redacted.

## Evidence files

Локальные скрины и JSON:

- `docs/competitive/telegram-vpn-2026-07-09/quattro/quattro-redacted-contact-sheet.png` — redacted contact sheet for sharing.
- `docs/competitive/telegram-vpn-2026-07-09/quattro/web/quattro-web-live-redacted-contact-sheet.png` — redacted live web-app contact sheet.

Privacy note: raw Telegram and live web screenshots/JSON are retained only as restricted local evidence and are ignored by git because they contain private Telegram UI, account IDs, email, Telegram IDs, order/link capabilities, referral codes, or generated links. No contact sheet from this capture is approved for external sharing without a new visual redaction review.

Snapshot note: the captured web bundle is partial and non-runnable; several
chunks and assets were not retained. It is evidence for observed screens and
flows, not a redistributable application copy.

- `docs/competitive/telegram-vpn-2026-07-09/quattro/screenshots/bot-00-open.png`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/screenshots/bot-01-after-start.png`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/screenshots/bot-02-legal-info.png`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/screenshots/bot-03-main-menu-from-legal.png`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/screenshots/bot-05-subscription-check-clicked.png`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/screenshots/bot-06-before-gate-check-ready.png`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/screenshots/bot-07-payment.png`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/screenshots/bot-08-payment-30d.png`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/screenshots/bot-11-payment-30d-5devices-500gb.png`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/screenshots/bot-12-payment-method-sbp.png`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/screenshots/bot-15-payment-method-card-rf.png`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/screenshots/bot-16-payment-method-stars.png`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/screenshots/bot-19-payment-method-crypto-bot.png`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/screenshots/bot-20-payment-method-heleket.png`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/screenshots/bot-30-main-site-button.png`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/channel-last-2-weeks.json`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/legal-pages-summary.json`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/web/login.html`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/web/assets/*.js`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/web/live/*.png`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/web/live/*.json`

## Bot: pre-gate flow

### Public bot card

URL: `https://t.me/QuattroVPN_BOT`

Observed public card:

- Title: `Quattro VPN | Кватро ВПН`
- Username: `@QuattroVPN_BOT`
- Copy: `Быстрый VPN с надёжной инфраструктурой.`
- Support: `@quattro_support_bot`
- Channel: `@quattrovpn_news`
- Action: `Start Bot`

### `/start`

Initial bot message:

```text
Чтобы пользоваться ботом, подпишитесь на:
Канал (обязательно): @quattrovpn_news
Чат (необязательно): @quattrovpn_chat

А также ознакомьтесь с нашей юридической информацией, доступной по кнопке ниже.
После этого нажмите «Я подписался и прочитал»
```

Visible buttons:

| Button | Type | URL / result |
| --- | --- | --- |
| `Канал (обязательно)` | external link | `https://t.me/quattrovpn_news` |
| `Чат (необязательно)` | external link | `https://t.me/quattrovpn_chat` |
| `Юридическая информация` | callback | Sends legal links message |
| `Я подписался и прочитал` | callback | Checks membership; if not subscribed: popup `Вы не подписались на канал` |

### Gate behavior

The gate is hard:

- Channel subscription is mandatory.
- Chat subscription is optional.
- Legal acknowledgement is implied by pressing `Я подписался и прочитал`, but the hard enforcement observed is channel membership.
- Bot does not reveal main service menu before channel membership passes.

POKROV note:

- This is aggressive acquisition: Quattro converts bot intent into channel subscriber count before any product interaction.
- It likely improves channel scale and retargeting.
- It also adds friction and makes Telegram dependency worse.
- POKROV should not copy forced subscription before trial if the core positioning remains app-first and Telegram-optional.

## Bot: legal links

Clicking `Юридическая информация` shows:

| Legal item | URL |
| --- | --- |
| `Политика конфиденциальности` | `https://blog.quattro-info.ru/Privacy-policy` |
| `Пользовательское соглашение` | `https://blog.quattro-info.ru/TermsUse` |
| `Политика Возврата` | `https://blog.quattro-info.ru/Ref-policy` |
| `Публичная оферта` | `https://blog.quattro-info.ru/Puboffer` |
| `Согласие на обработку персональных данных` | `https://blog.quattro-info.ru/Consent-to-data` |

### Legal positioning

Legal pages are hosted on Teletype under `blog.quattro-info.ru` and identify a
registered individual entrepreneur. Personal registration details are omitted
from this commit-safe report and retained only in the restricted evidence pack.

Important claims and mechanics:

- Privacy page claims minimal data processing: Telegram User ID, Telegram language, VPN keys/status, payment fact, subscription activation/end time, technical logs.
- Privacy page explicitly claims `no-logs`: no visit history, traffic contents, visited site IPs, DNS requests, network content.
- Terms forbid illegal activity, spam/fraud/attacks, exceeding device limits, and P2P/torrents except on designated locations.
- Refund policy:
  - refund possible if user could not connect and support could not fix within 72 hours;
  - refund possible if service downtime exceeds 24 hours due to operator mass failure;
  - no refund if user already connected at least once;
  - no refund for user device/provider/settings issue;
  - request window 7 calendar days after payment;
  - support request should include date/sum, transaction number if any, payment screenshot, reason/problem description;
  - review window 3 working days, sometimes up to 10.
- Offer says service is considered provided from key/config issuance or subscription activation.
- Consent page says data may be transferred to payment systems and technical contractors.

POKROV note:

- Strong pattern: legal pack appears before main bot access.
- Risk: `no-logs` claim is broad and would need evidence if copied.
- Useful for POKROV: show legal/offer/privacy in bot/cabinet, but avoid putting a legal wall before app-first trial.

## Public ecosystem cards

| Surface | Observed public facts |
| --- | --- |
| `@QuattroVPN_BOT` | Bot card; short value prop; support and channel links. |
| `@QuattroVPN_NEWS` | `1,039,053 subscribers`; official news channel; support/chat/bot links. |
| `@quattrovpn_chat` | `102,652 members`, `20,211 online`; official chat; bot/channel/support links. |
| `@quattro_support_bot` | Support bot card; action `Start Bot`. |

Marketing read:

- They operate a clean Telegram surface triangle: bot -> channel -> chat -> support.
- Channel subscriber scale is huge, and the bot gate likely helps keep it huge.
- Chat online count is used as social proof.

## Channel posts: last 2 weeks

Window: 2026-06-25..2026-07-09.

Source: `https://t.me/s/QuattroVPN_NEWS`.

### Post table

| Date UTC | Post | Views | Topic | Links |
| --- | --- | ---: | --- | --- |
| 2026-06-29 13:49 | `QuattroVPN_NEWS/198` | 431K | Happ returned to Russian App Store; warns search not indexed and fake apps may appear. | App Store Happ link |
| 2026-07-01 06:25 | `QuattroVPN_NEWS/200` | 452K | Android app `0.16`: Hysteria2, quick-settings tile, custom DNS, IPv4/IPv6, UI improvements, app sorting, fixes. | Yandex APK, bot `postQuattro016`, site `partner=postQuattro016`, support |
| 2026-07-07 05:32 | `QuattroVPN_NEWS/204` | 239K | Happ disappeared from RU App Store again; tells users to switch App Store region and install global Happ; says new RU version submitted for review. | Video instruction |
| 2026-07-07 10:22 | `QuattroVPN_NEWS/205` | 220K | Android app `0.18`: light theme, quick tile opens app on hold, double-back exit, ping button, colored pings, DNS edit, auto server optimization, Gemini tunneling fix, IPv4/IPv6 auto. | Yandex APK, bot `postQuattro018`, site `partner=postQuattro018`, support |
| 2026-07-08 09:39 | `QuattroVPN_NEWS/206` | 167K | Android app `0.18.1`: large-screen top panel fix, status-bar icon color fix, broken power button fix; recommends removing old version before installing. | Yandex APK, bot `postQuattro0181`, site `partner=postQuattro0181`, support |

### Channel content pattern

Quattro's channel is a product-update machine.

Repeated structure:

1. Long separator lines for visual rhythm.
2. Product version headline.
3. Platform caveat: Android first, iOS/Windows/Linux in development.
4. Feature list in numbered bullets.
5. Download link.
6. Resource footer: bot, site, support.
7. Deep link attribution:
   - `https://t.me/QuattroVPN_BOT?start=postQuattro016`
   - `https://quattro.app/register?partner=postQuattro016`
   - same pattern for `018`, `0181`.

### Product signals in last 2 weeks

Quattro is pushing:

- own Android app as the primary confidence asset;
- Hysteria2;
- quick-settings tile;
- DNS settings;
- IPv4/IPv6 settings;
- colored ping/status affordance;
- auto-server optimization;
- app tunneling list fix for Gemini;
- explicit APK hosting on Yandex Cloud;
- support link in every release post;
- App Store volatility handling for Happ.

### Marketing mechanics

Strong mechanics:

- Every release is not just a changelog; it is a trust post.
- Download is direct and visible.
- Bot/site/support links are repeated.
- Post-specific attribution is built into bot and site links.
- App Store incidents are framed as operator guidance, not panic.

Risks:

- APK direct links are external binary trust surface; users need confidence in source authenticity.
- Android-only app creates a gap while iOS/Windows/Linux are "in development".
- Happ remains a dependency for Apple fallback, and App Store availability volatility becomes repeated content.

POKROV note:

- Copy the cadence and attribution, not the complexity.
- POKROV release posts should include:
  - app version;
  - exact user-visible fixes;
  - download/update route;
  - current platform scope;
  - support route;
  - honest beta caveat.

## Bot: after-gate main menu

After the user passed the channel gate, the bot opened the service menu.

Observed main text:

```text
Привет! Ваш ID: [REDACTED]
Почта: не привязана
Подписка: отсутствует
Личный кабинет: quattro.app
```

Visible buttons:

| Button | Type | Observed result |
| --- | --- | --- |
| `Оплата` | callback | Opens subscription configurator. |
| `Наш сайт` | callback | Sends web cabinet link. |
| `Бонусы` | callback | Not live-clicked after browser timeout; mapped from web routes as referral/bonus/promo mechanics. |
| `Список серверов` | callback | Not live-clicked after browser timeout; mapped from web `servers/list`. |
| `Инструкции и поддержка` | callback | Not live-clicked after browser timeout; mapped from web `servers/instructions` and support surfaces. |
| `Наш канал` | external link | `https://t.me/quattrovpn_news` |
| `Наш чат` | external link | `https://t.me/quattrovpn_chat` |

Read:

- The bot exposes account state immediately: Telegram ID, email binding, subscription status, cabinet host.
- Email is not mandatory for Telegram-only payment start.
- Web cabinet is presented as a normal part of the product, not a secondary footer.

## Bot: payment branch

Clicking `Оплата` opens a long sales and limitation message before tariff selection.

Core claims:

- `Неограниченная скорость`
- `Безлимитный трафик*`
- `До 5 устройств`
- `Безотказная работа`
- `Отзывчивая техподдержка`
- `Совместимость с TV/iOS/Android/Windows/MacOS/Linux`
- `Доступно 284 серверов`

Important limitations in the same message:

1. Traffic is consumed only on LTE servers without `безлимитный` label.
2. Bought traffic has no expiration and carries to the next period.
3. LTE traffic can burn with a coefficient in the server name, for example `0.5x`.
4. 30 days include 500 GB.
5. 90 days include 1500 GB.
6. Servers with a star support Gemini and other Google models.
7. Torrents are allowed only on servers labeled `Torrent`.
8. Torrent violation or device-limit abuse can lead to block without refund.
9. Work with mobile operators is not guaranteed; no refund for that reason.

Interpretation:

- The headline says `Безлимитный трафик`, but the real model is mixed: most servers are unlimited, LTE servers burn GB.
- The copy is aggressive but defensively wrapped in caveats.
- They sell advanced constraints as power-user control rather than as limits.

### Tariff matrix

30 days:

| Devices | 500 GB | 1000 GB | 1500 GB | 3000 GB | 5000 GB |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 300 ₽ | 450 ₽ | 600 ₽ | 1050 ₽ | 1650 ₽ |
| 10 | 450 ₽ | 600 ₽ | 750 ₽ | 1200 ₽ | 1800 ₽ |
| 15 | 600 ₽ | 750 ₽ | 900 ₽ | 1350 ₽ | 1950 ₽ |

90 days:

| Devices | 1500 GB | 3000 GB | 5000 GB |
| ---: | ---: | ---: | ---: |
| 5 | 900 ₽ | 1350 ₽ | 1950 ₽ |
| 10 | 1350 ₽ | 1800 ₽ | 2400 ₽ |
| 15 | 1800 ₽ | 2250 ₽ | 2850 ₽ |

Pricing read:

- Base price is effectively 300 ₽ / 30 days / 5 devices / 500 GB.
- Extra device tier adds roughly 150 ₽ per +5 devices per 30 days.
- Extra traffic is roughly 150 ₽ per +500 GB at low tiers, with discount at larger traffic packs.
- 90 days is not visibly discounted versus 30 days x 3; it is mainly longer prepay and higher included traffic.

### Payment methods

Bot payment methods for the base package:

| Button | Provider / behavior | Observed copy |
| --- | --- | --- |
| `СБП` | YooMoney checkout URL | One-time payment, no auto-renewal. |
| `Банковская карта РФ` | CloudPayments order URL | One-time payment, no auto-renewal. |
| `Telegram Stars` | Telegram invoice preview in Web | Telegram Web did not expose a normal checkout page during capture. |
| `Crypto Bot` | `https://t.me/CryptoBot?start=...` | Amount shown in RUB equivalent. |
| `Heleket (любой кошелёк)` | `https://new-pay.heleket.com/pay/...` | User can choose a crypto wallet/coin on the payment page. |
| `← Изменить конфигурацию` | callback | Goes back to tariff configuration. |
| `Главное меню` | callback | Returns to main menu. |

Observed payment copy repeats:

```text
Оплата подписки на 30 дней.
Оплата является однократной операцией, без автопродления.
```

Payment UX notes:

- They support almost every useful payment lane for RU Telegram VPN users: SBP, local card, Stars, Crypto Bot, external crypto.
- The bot generates payment links per selected configuration.
- Some `Назад` behavior returns to the broad payment intro, so deep configuration context is not always preserved.
- No payment was completed in this research.

## Bot: site branch

Clicking `Наш сайт` sends:

```text
Наш сайт
Откройте личный кабинет Quattro App.
```

Buttons:

| Button | URL / behavior |
| --- | --- |
| `Открыть сайт` | `https://quattro.app/register?tg_link=[REDACTED]` |
| `Главное меню` | returns to main menu |

The personal web link redirects the user into `quattro.app/login` / registration flow and is meant to bind Telegram to the web account.

## Web app: authentication

Source: `https://quattro.app/`, user-provided login screenshot, downloaded SPA bundle.

Observed email code behavior:

- Sender: `Quattro App <noreply@quattro.app>`.
- Subject pattern: `Quattro App — код подтверждения: [6-digit code]`.
- Email says the code is valid for 5 minutes.
- If the user did not request it, the user is told to ignore the email.

Auth surfaces in the SPA:

| Route | Purpose |
| --- | --- |
| `/login` | Email/password login. |
| `/register` | Email/password registration. |
| `/reset-password` | Password recovery. |

Login/register details:

- Registration asks for email, password, repeated password.
- Password minimum is 8 characters.
- Registration sends email code, then asks for a 6-digit code.
- Login can require a 2FA email code: `Подтверждение входа`.
- Code forms use numeric `000000` placeholder and one-time-code autocomplete.
- If `tg_link` is present, the UI says Telegram will be linked after login.
- `ref` and `partner` query params are persisted in localStorage before registration.

Security/tech read:

- `HEAD` on the app returns `405`, `Allow: GET`.
- Server header observed as `QRATOR`.
- CSP observed:
  - `default-src 'self'`
  - `script-src 'self'`
  - `style-src 'self' 'unsafe-inline'`
  - `img-src 'self' data: https:`
  - `connect-src 'self'`
  - `frame-ancestors 'none'`
  - `base-uri 'self'`
  - `form-action 'self'`

This is more polished than a basic Telegram-only product: Quattro has a real account system, email verification, Telegram linking, and 2FA.

## Web app: route map

Authenticated user routes:

| Route | Surface |
| --- | --- |
| `/` | Dashboard / subscriptions. |
| `/subscription` | Buy or renew subscription. |
| `/manage/:id` | Manage one subscription. |
| `/referral` | Referral system. |
| `/partner` | Partner program. |
| `/promo` | Promo code activation. |
| `/servers` | Server list. |
| `/instructions` | Instructions. |
| `/settings` | Account/security settings. |
| `/terms` | Legal documents. |
| `/dice` | Hidden/admin-gated route. |
| `/admin`, `/admin/users`, `/admin/subscriptions`, `/admin/payments`, `/admin/promos`, `/admin/partners`, `/admin/logs` | Admin routes. |

Live sidebar labels after login:

- `Главная`
- `Оплата`
- `Рефералы`
- `Партнёрская программа`
- `Промокод`
- `Серверы`
- `Инструкции`
- `Настройки`
- `Документы`
- `Выйти`

Read:

- Site is not a landing page. It is a functional account cabinet.
- The channel post from earlier also framed it this way: configurator, multi-subscriptions, limit upgrade, subscription management, bonuses, referral/partner tracking, promo activation.
- This is a direct answer to the user concern that web apps were being skipped: Quattro's web app is strategically important.

## Web app: dashboard

Dashboard behavior from `Dashboard-DMlK596u.js`:

- Title: `Личный кабинет`.
- If no subscription: `Нет подписки`.
- If subscriptions exist, each card shows:
  - label;
  - monthly price;
  - active/expired status;
  - end date;
  - device limit;
  - traffic used/limit or unlimited;
  - subscription URL;
  - buttons `Скопировать`, `Подключиться`, `Управление подпиской`.
- CTA: `Купить подписку` or `Купить / Продлить`.

Telegram linking modal/banner:

- `Привяжите Telegram`
- `Привяжите Telegram, чтобы управлять подпиской из бота. Это можно сделать позже в настройках.`
- Generates `https://t.me/{bot_username}?start=linktg_{code}`.
- Polls every 3 seconds.
- States:
  - `Ожидаем привязку...`
  - `Telegram привязан!`
  - `Отмена`

Payment success modal:

```text
Оплата прошла успешно!
Ваша подписка активирована. Ссылка для подключения доступна на главной странице.
```

Live dashboard for this account:

- title: `Личный кабинет`;
- state: `Нет подписки`;
- primary CTA: `Купить подписку`;
- no Telegram linking modal appeared because Telegram is already linked.

## Web app: buy / renew

Route: `/subscription`.

Controls:

- `Срок`
- `Устройства`
- `Трафик`
- `Итого`
- `Способ оплаты`

Payment methods on web:

| Web button | Notes |
| --- | --- |
| `СБП` | same overall payment family as bot. |
| `Банковская карта РФ` | card payment. |
| `Криптовалюта` | Heleket lane. |

Difference vs bot:

- Bot exposes `Telegram Stars` and `Crypto Bot`.
- Web app exposes only SBP, Russian card, and crypto/Heleket.

Renewal mechanics:

- If the account has subscriptions, the screen asks whether to renew existing subscriptions or buy a new one.
- User can select multiple subscriptions for renewal.
- Buttons:
  - `Продлить выбранные`
  - `Новая подписка`
- Renewal payload can apply same duration/traffic to selected subscriptions.

Product read:

- Multi-subscription support is a meaningful differentiator.
- They allow separate subscriptions under one account instead of forcing a single global account plan.

Live payment configurator for a no-subscription account:

- title: `Оплата`;
- subtitle: `Выберите тариф и способ оплаты`;
- `СРОК`: `30 дней`, `90 дней`;
- `УСТРОЙСТВА`: `5`, `10`, `15`;
- `ТРАФИК`: `500 ГБ`, `1000 ГБ`, `1500 ГБ`, `3000 ГБ`, `5000 ГБ`;
- explanatory text: `Тратится только на LTE-серверах (на остальных безлимит). Минимум — 500 ГБ, при необходимости можно докупить.`;
- selected default: `30 дней · 5 устр. · 500 ГБ`;
- `Итого`: `300 ₽`;
- payment methods: `СБП`, `Банковская карта РФ`, `Криптовалюта`;
- CTA: `Оплатить 300 ₽`.

## Web app: subscription management

Route: `/manage/:id`.

Confirmed management functions from `ManageSub-Zk_vsYOF.js`:

| Section | Function |
| --- | --- |
| Status card | active/expired, end date, devices, traffic. |
| Subscription URL | copy URL, open/connect. |
| `Продлить подписку` | choose 30/90 days and traffic; pay by SBP/card/crypto. |
| `Перевыпуск подписки` | replace subscription link and disconnect all devices. |
| `Настройка локаций` | enable/disable locations; cannot disable all locations; depleted LTE locations show `(исчерпан)`. |
| `Лимит устройств` | change device tier with prorated upgrade/downgrade logic. |
| `Бонусный баланс` | spend bonus balance on days or GB. |
| `Ключи vless://` | fetch keys, copy individual keys, save all keys to `vless-keys-{id}.txt`. |

Critical UX detail:

- Reissue copy explains exactly what happens:
  - all connected devices will be disconnected;
  - user gets a new subscription link;
  - payment and validity period are kept;
  - devices must reconnect.

Competitive read:

- This is advanced and sticky.
- Users can self-serve the common support cases: leaked link, too many devices, location preference, traffic top-up, raw keys.
- POKROV should decide deliberately whether it wants this much power-user surface in the first cabinet version.

## Web app: bonuses, referral, partner, promo

### Referral

Route: `/referral`.

Copy:

```text
Реферальная система
Приглашайте друзей и получайте бонусные дни и трафик
```

Stats:

- `Приглашено`
- `Оплативших`

Mechanic:

- If a referred user buys a subscription for `min_pay_period` or more, both users get `bonus_days` days and `+bonus_traffic_gb` GB.
- The user gets both web and bot referral links:
  - `Сайт:`
  - `Бот:`
- Clicking copies the link.

Live referral state for this account:

- `Приглашено`: `0`;
- `Оплативших`: `0`;
- condition text: referred user must buy subscription for `1 месяц` or more;
- both web and bot referral links are generated; codes are redacted in this report.
- In the live copy, bonus day/GB values were blank in this account state, although the static component supports `bonus_days` and `bonus_traffic_gb`.

### Partner

Route: `/partner`.

If approved as partner:

- `Переходы`
- `Активных подписок`
- `Оплативших`
- `Заработано`
- `Выплачено`
- `Остаток`
- `Ваш процент: {percent}% от каждой оплаты`
- `За выплатой обратитесь в техподдержку.`
- partner web link and partner bot link.

If not approved:

```text
У вас не оформлена партнёрская программа. На данный момент оформление недоступно.
```

Read:

- They separate normal referral from partner payouts.
- Partner program looks controlled/manual, not self-serve public signup.

### Promo

Route: `/promo`.

Copy:

```text
Промокод
Введите промокод, чтобы получить бонусные дни или трафик
```

Behavior:

- If there are multiple subscriptions, user must select target subscription.
- Input placeholder: `Введите промокод`.
- Success:
  - `Промокод применён!`
  - `+{bonus_days} дней`
  - optional `+{bonus_gb} ГБ`
  - `Подписка до: {new_end_date}`

## Web app: servers, instructions, terms, settings

### Servers

Route: `/servers`.

Behavior:

- Title pattern: `Серверы ({count})`.
- Lists server names from backend.
- Fallback: `Список серверов временно недоступен`.

Live server list:

- count: `284`;
- first group includes:
  - `Авто | Самый быстрый`;
  - `LTE Авто - Нидерланды`;
  - `LTE Авто - Великобритания`;
  - `LTE Авто - Швеция`;
  - `LTE Авто - Германия`;
  - `LTE Авто - Латвия`;
  - `Бельгия`, `Великобритания`, `Германия`, `Испания`, `Италия`, `Латвия`, `Нидерланды`, `Норвегия`, `Польша`, `Россия`, `Финляндия`, `Франция`, `Швейцария`, `Швеция`, `Эстония`;
- server naming exposes product mechanics:
  - `Hysteria2`;
  - `Torrent`;
  - `LTE - Безлимитный`;
  - coefficients like `0.1X` and `0.5X`;
  - bridges: `Мост МСК`, `Мост Питер`, `Мост Хабаровск - Япония`;
  - protocol labels: `SNI`, `SS`, `WS`, `GRPC`.

Read:

- This is a strong proof surface. The cabinet makes infrastructure breadth visible.
- The list is also noisy: a regular user may not understand `0.1X`, bridge labels, or protocol labels without context.

### Instructions

Route: `/instructions`.

Copy:

```text
Инструкции
Как подключить Quattro VPN на вашем устройстве
```

Behavior:

- Loads backend sections.
- Each section has title, description, optional `Открыть инструкцию` link, and optional additional labeled links.

Live instruction sections and links:

| Section | Copy | Links |
| --- | --- | --- |
| `Android / iOS` | `Скачайте приложение и отсканируйте QR-код или вставьте ссылку на подписку.` | `https://t.me/QuattroVPN_INSTRUCTIONS/6` |
| `Android TV` | `Используйте Happ (рекомендуем) или v2RayTun.` | `https://t.me/QuattroVPN_INSTRUCTIONS/7/239`, `https://t.me/QuattroVPN_INSTRUCTIONS/7/33` |
| `Windows / MacOS / Linux` | `Скачайте клиент для ПК и импортируйте подписку.` | `https://t.me/QuattroVPN_INSTRUCTIONS/8` |
| `Маршрутизация` | `Включаем VPN только для определённых приложений.` | `https://t.me/QuattroVPN_INSTRUCTIONS/34/130`, `https://t.me/QuattroVPN_INSTRUCTIONS/34/224` |
| `Обновить подписку` | `Как обновить подписку в приложении после продления.` | `https://t.me/QuattroVPN_INSTRUCTIONS/194/195` |
| `Второе устройство` | `Скопируйте ссылку на подписку и откройте на другом устройстве.` | `https://t.me/QuattroVPN_INSTRUCTIONS/231/232` |

Read:

- They keep instruction content in Telegram, not inside the web app.
- Web app is an index/hub; Telegram channel stores the long guides.
- This keeps cabinet light and reuses Telegram content for support.

### Terms

Route: `/terms`.

Behavior:

- Loads legal document list from backend.
- Support link points to `https://t.me/quattro_support_bot`.

Live document links:

- `Политика конфиденциальности` -> `https://blog.quattro-info.ru/Privacy-policy`
- `Пользовательское соглашение` -> `https://blog.quattro-info.ru/TermsUse`
- `Политика возврата` -> `https://blog.quattro-info.ru/Ref-policy`
- `Публичная оферта` -> `https://blog.quattro-info.ru/Puboffer`
- `Согласие на обработку персональных данных` -> `https://blog.quattro-info.ru/Consent-to-data`
- `Техподдержка` -> `https://t.me/quattro_support_bot`

### Settings

Route: `/settings`.

Account section:

- shows user ID;
- email;
- Telegram link status.

Email:

- unverified email gets a confirmation card;
- sends code;
- 6-digit numeric input;
- retry timer;
- "check spam / typo" copy.

Telegram:

- if linked: `Telegram привязан`;
- can unlink if allowed, with password confirmation;
- if not linked: generates Telegram link and polls for confirmation.

2FA:

- `Двухфакторная аутентификация (email)`.
- Copy: `При входе на сайт будет запрашиваться код, отправленный на ваш email.`
- Status: `Включена` / `Отключена`.
- Enable sends email code.
- Disable asks current password and email code.

Password:

- current password;
- new password, minimum 8 characters.

Change email:

- sends code to new email;
- can be disabled if email verification is disabled globally.

Live settings state for this account, redacted:

- account card shows web account ID, email, Telegram ID;
- `Telegram привязан`;
- 2FA email status: `Отключена`;
- CTA: `Включить 2FA`;
- change password form:
  - `Текущий пароль`;
  - `Новый пароль (мин. 8 символов)`;
  - `Сохранить пароль`;
- change email form:
  - current email;
  - `Получить код`.

## Bot branches not fully live-clicked

These bot buttons were not clicked live in Telegram Web during the final pass:

- `Бонусы`
- `Список серверов`
- `Инструкции и поддержка`

However, equivalent product surfaces are now confirmed live in the web app:

- `Бонусы` maps to referral, partner, promo, bonus balance in subscription management.
- `Список серверов` maps to `/servers` and backend `servers/list`.
- `Инструкции и поддержка` maps to `/instructions`, `/terms`, and `@quattro_support_bot`.

If a strict Telegram-only evidence pass is needed, it requires one more stable Telegram Web session, but the product mechanics are already visible enough for strategy.

## Aggressive marketing pattern

Quattro's aggression is not just loud copy. It is a system:

1. Mandatory channel subscription before bot use.
2. Huge channel/social proof front and center.
3. Broad confidence claims: `безлимит`, `безотказная работа`, `полная анонимность`, `низкая цена`.
4. Heavy payment coverage: SBP, card, Stars, Crypto Bot, Heleket.
5. Frequent app-update posts with concrete technical details.
6. Direct APK links in every Android release post.
7. Post-specific attribution in bot/site links.
8. Cabinet deep-linking from bot.
9. Referral plus partner plus promo plus bonus balance.
10. Power-user controls in management: locations, keys, reissue, traffic, devices.

Why it works:

- New user sees scale, movement, payment convenience, and technical competence.
- Existing user sees fixes and control.
- Partner/referral user sees tracking and reward surfaces.
- Support burden is reduced by self-service controls.

Where it can backfire:

- Too many limits are hidden behind a `безлимитный` headline.
- Mandatory channel gate adds friction and makes Telegram dependence visible.
- Direct APK links require high trust in file integrity.
- Broad `no-logs` / anonymity claims require evidence.
- Power-user options can overwhelm mainstream users.

## Comparison with POKROV

### Where Quattro is stronger today

- Telegram audience scale.
- Mandatory channel conversion.
- Multi-payment coverage.
- Web cabinet maturity.
- Multi-subscription support.
- Self-service subscription management.
- Referral/partner/promo infrastructure.
- App update cadence and channel-post discipline.
- Public legal pack before purchase.
- Direct operational communication when payment processing fails.

### Where POKROV is stronger or can be sharper

- App-first identity can be simpler than Quattro's Telegram-first gate.
- POKROV can be more honest and premium by not overclaiming `no-logs`, `безотказно`, or `полная анонимность`.
- POKROV already has a clear 5-day trial and +10 day Telegram reward model.
- POKROV can make the trial path less hostile than mandatory channel subscribe.
- POKROV can package release honesty better: beta/stable/store/signing/RU-origin claims should stay evidence-backed.

### What to copy

- Release posts as product trust assets:
  - version;
  - exact user-visible fixes;
  - platform scope;
  - download/update route;
  - support route;
  - bot/site deep links with attribution.
- Legal links in bot and cabinet.
- Payment provider breadth, if operationally supported.
- Email OTP for web account login/2FA.
- Telegram account linking from web and web linking from bot.
- Referral and promo mechanics, but keep the first version simpler.
- Subscription reissue / "disconnect all devices" as a self-service support reducer.
- Server/location status list if backed by real backend data.

### What not to copy

- Mandatory channel subscription before first product value.
- Broad `полная анонимность` and `no-logs` copy without hard evidence.
- `Безлимитный` headline if the product has meaningful traffic exceptions.
- Direct APK links without checksum/signature guidance.
- Too many network toggles in onboarding.
- Partner payouts before reconciliation and anti-fraud are ready.

## Actionable POKROV backlog

High impact:

1. Add a Quattro-style release post template for POKROV channel.
2. Add post-specific deep links for bot/site attribution.
3. Make legal links one tap from bot and cabinet.
4. Add email OTP login/verification to the web cabinet if we want web account independence from Telegram.
5. Add subscription reissue in cabinet/bot: revoke old subscription URL, disconnect devices, issue new URL.
6. Add clear payment-method cards: Lava/top now, future SBP/card/crypto only when evidence-backed.

Medium impact:

1. Add promo code activation in cabinet.
2. Add referral dashboard: invited, paid, bonus days/GB.
3. Add partner dashboard only after fraud/reconciliation/payment ops are ready.
4. Add server list with status/ping only if data is real and fresh.
5. Add "what is included / limits / refund rules" accordion near checkout.

Avoid for now:

1. Forced channel subscription.
2. Broad anonymity/no-logs claims.
3. Complex LTE traffic coefficients unless the product genuinely needs them.
4. A giant admin/power-user surface in the first user release.

## Bottom line

Quattro is not just "a Telegram VPN bot". It is a Telegram growth loop plus a real web cabinet plus aggressive payment coverage.

Their strongest moat is operational surface area:

- bot,
- channel,
- chat,
- support bot,
- web cabinet,
- Android app,
- referral/partner/promo,
- multi-payment,
- self-service subscription management.

For POKROV, the right answer is not to clone the noise. The useful pattern is:

- make every release post sell trust;
- make bot/cabinet/payment paths measurable;
- give users self-service recovery controls;
- keep claims calmer and evidence-backed;
- keep first-run product value before Telegram growth extraction.

# Огонь VPN — Mobile App Competitor Profile

**Snapshot date:** 2026-07-22<br>
**Status:** `DEEP PASS COMPLETE WITH BLOCKERS` — app, connection, monetization, locations, bypass, support, store, web/legal and static APK surfaces captured; historical release cadence and current Georgian-registry status remain blocked<br>
**Evidence root:** [`raw/ogon-vpn/2026-07-22/`](raw/ogon-vpn/2026-07-22/)

## At A Glance

| Field | Observed value |
| --- | --- |
| Product | Огонь VPN |
| Android package | `com.ogonconnect.app` |
| Installed version | 0.84 (`versionCode` 30) |
| Android target | SDK 35; minimum SDK 27 |
| Install source | Google Play (`com.android.vending`) |
| Current account model | Existing anonymous device profile; a generated user ID is shown in-app, but is intentionally excluded from retained evidence |
| Free allowance | 5.0 GB / 5.0 GB shown in this anonymous state |
| Audit isolation | HiroVPN was force-stopped and no `tun0` interface remained before Огонь launched |

## Coverage Ledger

| Area | Status | Notes |
| --- | --- | --- |
| First launch/onboarding | Partial | App opened into an existing anonymous state; no onboarding was shown, so true clean-install onboarding is not yet proven |
| Home/connect | Captured | First-connect disclosure, Android consent, auto-location connection, HTTPS reachability and disconnect completed |
| Servers/routing | Captured | Free, Premium, YouTube, gaming and empty Ultra surfaces captured |
| Pricing/payment | Captured to checkout boundary | Four RUB plans and product claims captured; no payment method or order was opened |
| Account/referral/growth | Partial | Anonymous ID/free-tier model captured; referral, promo and notification behavior remain |
| Bypass/ad blocking | Captured with restoration | Per-app and category bypass plus custom-category modal captured; temporary switch changes were restored |
| Settings/support/legal | Captured | Settings, language, structured feedback, Telegram support/channel destinations and all linked legal texts captured; nothing was submitted |
| External destinations | Captured with blockers | Website, mirror, Play, Telegram, Privacy, Terms and Recurring destinations mapped; the support bot was not started and checkout was not opened |
| Store/release/legal entity | Captured with blockers | Live Play page, creatives, shelves, publisher and latest update captured; authoritative historical cadence and current Georgian entity status remain unavailable |
| Static APK | Captured | Manifest, components, SDKs, permissions, network config, libraries, domain architecture and safe credential-pattern scan captured without probing third-party infrastructure |

## Product Structure

The app uses five persistent bottom tabs: **Подписка**, **Премиум**, **VPN**, **Локации** and **Настройки**. The VPN screen is the visual anchor: a dark navy background with diagonal-line texture and a large white flame-shaped connect control. The hierarchy is coherent and direct, though visually less polished than HiroVPN.

The home screen exposes four utility shortcuts above the main control: support, Telegram channel, bug report and notifications. Below the disconnected state it shows:

- the remaining free allowance: **5.0 GB of 5.0 GB**;
- a Premium upgrade call to action;
- **«Что работает без VPN?»**, currently **2/7** categories;
- automatic country selection described as the fastest location.

Evidence: [launch](raw/ogon-vpn/2026-07-22/screenshots/01-launch.png), [loaded home](raw/ogon-vpn/2026-07-22/screenshots/02-home-loaded.png).

## Connection Flow And Data Disclosure

The first connection has an app-owned disclosure before Android's standard VPN consent. Огонь says it does **not** inspect traffic contents or keep logs of visited domains or DNS requests. It says it does process:

- server-issued account identifiers;
- subscription membership and status;
- the selected server;
- aggregate traffic volumes;
- optional in-app diagnostic events.

The stated purposes are authentication/account management, routing, diagnostics and support. Tapping **«Включить VPN»** is presented as acknowledgement of the terms and privacy policy; Android's system VPN-consent prompt follows.

The current-session auto-location smoke test passed:

- `tun0` appeared about **0.58 seconds** after accepting the Android prompt;
- the app changed to **«Подключен»** and Android showed the VPN key indicator;
- a suppressed-output HTTPS probe completed successfully through the active state;
- an ICMP/DNS ping probe failed, which is inconclusive because VPN endpoints commonly block ICMP; it is not counted as a connectivity failure;
- the UI did not name the selected automatic country/server on the home screen;
- disconnect removed `tun0` in about **0.40 seconds** and returned the UI to **«Отключен»**;
- the displayed allowance remained 5.0 GB after this tiny test.

No endpoint address, exit IP, DNS payload or raw network configuration was retained.

Evidence: [first-connect disclosure](raw/ogon-vpn/2026-07-22/screenshots/26-first-connect-disclosure.png), [Android VPN consent](raw/ogon-vpn/2026-07-22/screenshots/27-android-vpn-consent.png), [connected auto-location](raw/ogon-vpn/2026-07-22/screenshots/28-connected-auto.png), [disconnected after smoke test](raw/ogon-vpn/2026-07-22/screenshots/29-disconnected-after-smoke.png).

## Identity And Subscription

The subscription screen uses an anonymous device-bound identity rather than forcing registration. It labels the current plan **«Бесплатно навсегда»**, exposes a copyable generated ID and offers an upgrade. The generated ID and every screenshot/XML containing it were quarantined outside the worktree; it is not reproduced here.

This is a strong low-friction acquisition pattern, but account recovery, cross-device transfer and the meaning of the identifier still need verification.

## Premium Paywall

The paywall separates **Premium** from a disabled **Ultra — «Скоро»** tier. Premium claims:

- white lists for comfortable browsing;
- YouTube without ads;
- no traffic limits and full speed;
- support response within 15 minutes;
- control over which services work without VPN, with government services, banks and marketplaces named as examples;
- use on any devices, marked **«Скоро»** rather than currently available.

| Plan | Total | Effective monthly price | Shown discount |
| --- | ---: | ---: | ---: |
| 1 month | 249 RUB | 249 RUB | — |
| 3 months | 499 RUB | 166 RUB | 25% |
| 6 months | 889 RUB | 148 RUB | 30% |
| 12 months | 1,489 RUB | 124 RUB | 40% |

Every plan advertises a **30-day refund**. The footer says the user accepts the personal-data policy, offer and recurring-payment terms, and that renewal can be disabled in Profile. No plan was selected and no checkout or charge was initiated.

Evidence: [Premium paywall](raw/ogon-vpn/2026-07-22/screenshots/04-premium-tab.png).

## Locations And Tier Packaging

The location browser has **Все / Premium / Ultra** filters, search and refresh. It uses qualitative signal bars rather than unsupported numeric speed claims.

Observed groups:

- **Free — 4 entries:** automatic selection plus Netherlands #2, Netherlands and Germany; the group was marked **«Повышенная нагрузка»**.
- **YouTube without ads — 7 Premium entries:** #S5, #S6, #S4, #S9, #S2, #S1 and #S3.
- **Premium countries — 36 entries:** the captured list is heavily weighted toward Netherlands instances, with Kazakhstan/Astana, Poland/Warsaw, USA/New York, Ireland/Dublin and Germany/Frankfurt also visible.
- **Gaming — 3 Premium entries:** Server #1, #2 and #3.
- **Ultra:** the dedicated tab is currently empty and displays **«Ничего не найдено»**.

Visible Netherlands instance labels included #12, #S-5, #25, #S-6, #11, #14, #16, #26, an unnumbered entry, #10, #15, #17, #18, #33, #34, #36, #44, #9, #19, #20, #35, #S, #S-3, #27, #24, #40, #41, #43 and #S-4. This is an observed UI inventory, not proof of distinct physical infrastructure.

Evidence: [free and YouTube groups](raw/ogon-vpn/2026-07-22/screenshots/07-locations.png), [Premium list 1](raw/ogon-vpn/2026-07-22/screenshots/08-locations-premium-1.png), [Premium list 2](raw/ogon-vpn/2026-07-22/screenshots/09-locations-premium-2.png), [Premium list 3](raw/ogon-vpn/2026-07-22/screenshots/10-locations-premium-3.png), [empty Ultra tab](raw/ogon-vpn/2026-07-22/screenshots/12-locations-ultra-tab.png).

## Bypass Rules: «Что работает без VPN?»

The feature is split into **Приложения** and **Сайты**.

### Applications

No apps were selected in the captured state (**0/22**). The list enumerates installed apps and offers individual bypass switches. Visible entries included BlancVPN, Chrome, LD Market, CyberGhost, Durev VPN, ExpressVPN, GnuVPN, Google Play, HiroVPN, Kakadu, Launcher, Ping VPN, Pipster, Proton VPN, Red Shield VPN, TipTop VPN, Батя VPN, ВПН, Галерея, Космос VPN, Настройки and Файлы. No listed competitor was launched.

Evidence: [applications top](raw/ogon-vpn/2026-07-22/screenshots/14-bypass-sites.png), [applications bottom](raw/ogon-vpn/2026-07-22/screenshots/15-bypass-apps-bottom.png).

### Sites

Seven preset categories are offered. The default captured state was **2/7**:

- Russian sites — on;
- Russian government sites — on;
- VK — off;
- TikTok — off;
- Yandex services — off;
- Ozon — off;
- Wildberries — off.

The app also offers **«Новая категория»** with a category-name field and Add/Cancel controls. The modal was inspected but nothing was saved. A tap briefly turned **Russian sites** off; it was restored immediately, returning the state to 2/7. The misleadingly named `18-russian-sites-detail` evidence records that temporary off-state, not a category-detail view.

Evidence: [site categories](raw/ogon-vpn/2026-07-22/screenshots/16-bypass-sites-tab.png), [create-category modal](raw/ogon-vpn/2026-07-22/screenshots/17-create-bypass-list.png), [temporary off-state](raw/ogon-vpn/2026-07-22/screenshots/18-russian-sites-detail.png).

## Settings

Observed settings and their captured defaults:

| Control | Observed state |
| --- | --- |
| Support | Opens Telegram support bot `@ogonvpnhelp_bot`; public landing showed 26,125 monthly users at capture time |
| Telegram channel | Opens public channel `@ogonvpn`; landing showed 290,877 subscribers at capture time |
| Auto-connect | Off by default; switch changes immediately without an explanatory prompt |
| What works without VPN | Opens bypass controls |
| Language | Russian; modal offers only Russian and English |
| Ad blocking | On by default in the captured state |
| Push notifications | Off; enabling invokes the standard Android notification-permission prompt |
| Report a problem | Opens a two-tab in-app sheet for errors and product feedback; no submission made |
| Privacy policy | Opens `https://ogonvpn.xyz/privacy/` |
| Offer | Opens `https://ogonvpn.xyz/terms/`; material commercial clauses captured below |
| Version | 0.84 |

Ad blocking was temporarily switched off for state capture and immediately restored to **on**. Auto-connect switches on immediately without a confirmation or explanation; it was restored to **off**. The push switch invokes Android's runtime notification-permission prompt. Permission was denied and the app switch remained/restored **off**.

Evidence: [settings](raw/ogon-vpn/2026-07-22/screenshots/13-settings.png), [language modal](raw/ogon-vpn/2026-07-22/screenshots/20-language.png), [temporary ad-block off-state](raw/ogon-vpn/2026-07-22/screenshots/21-adblock-off.png), [notification permission prompt](raw/ogon-vpn/2026-07-22/screenshots/24-notification-permission.png), [temporary auto-connect on-state](raw/ogon-vpn/2026-07-22/screenshots/25-autoconnect-on.png).

## Support Destination

The **Поддержка** row opens the public Telegram landing page for **«Поддержка ОгоньВПН»**, username `@ogonvpnhelp_bot`. Telegram displayed **26,125 monthly users** at capture time. The bot was not started and no message or account data was sent. The landing screenshot was deliberately not retained because the emulator browser exposed unrelated open-tab titles.

The **Telegram канал ОгоньVPN** row opens `@ogonvpn`. Its public landing page displayed **290,877 subscribers**, the positioning **«Быстрый доступ ко всему что заблокировано в России»**, and linked the same support bot. No channel action was taken. That browser screenshot was also not retained because unrelated open-tab titles were visible; public-channel post analysis remains for the web pass.

### Public-channel operating pattern

The public web history shows the channel acting as a lightweight status page, reassurance feed and Play-acquisition loop:

- blocking/VLESS and mobile-allowlist explainers frame the external threat and promise ongoing adaptation;
- from 2026-01-07 through 2026-03-13, the visible sequence includes seven incident/maintenance notices and six explicit restoration updates, including three notice-to-restoration windows of roughly 2h18m, 2h26m and 4h54m;
- incident posts often route users back to support, while restored-service posts route satisfied users to Google Play;
- no visible post publishes a numbered Android version or real changelog, so the channel does not establish release cadence.

Most importantly, a public post dated 2026-06-26 offers **two weeks of Premium** only after the user gives the app **five stars**, writes a Google Play review and sends a screenshot to `@ogonvpngift_bot`. This is a direct incentivized-high-rating campaign. Google's current User Ratings, Reviews and Installs policy explicitly prohibits rewards or incentives for ratings/reviews and uses an incentive for a high rating as a common violation example. It is a strong growth mechanism and a material platform-policy risk; POKROV should not copy it.

Evidence: [public-channel notes](raw/ogon-vpn/2026-07-22/scrapes/telegram-public-channel-notes.md); public post `https://t.me/ogonvpn/23`; policy `https://support.google.com/googleplay/android-developer/answer/9898684`.

## In-App Feedback Loop

**«Сообщить о проблеме»** opens an in-app composer rather than immediately leaving for email or chat. It has two tabs:

- **Ошибка:** free-text problem description plus quick tags for no internet, VPN not connecting, payment failure, Premium not activated, split tunneling failure, app closing and **«Зависает огонь»**.
- **Обратная связь:** free-text idea/suggestion plus tags for suggestion, missing feature, interface improvement, connection improvement, prices/subscription and other.

The send button stays disabled with an empty message. Nothing was entered or submitted. This is a useful structured voice-of-customer design: high-frequency failure categories are captured at source and product ideas are separated from incident reports.

Evidence: [error report tab](raw/ogon-vpn/2026-07-22/screenshots/22-report-problem.png), [feedback tab](raw/ogon-vpn/2026-07-22/screenshots/23-feedback.png).

## Legal And Public Destination Observed In-App

The Premium footer's privacy link opens `https://ogonvpn.xyz/privacy/`. The public page offers English/Russian language switching and navigation for Privacy, Terms and Recurring payments.

The page identifies:

- **RELOCUP LLC**;
- identification number **447009282**;
- Georgia, Kobuleti Municipality, Tsikhisdziri Village, 10th Street, N 2;
- public support email `support@ogonvpn.xyz`.

The privacy text states that cross-border transfer may occur when infrastructure or counterparties are outside Russia. This records the app-linked public claim only; current corporate registry status and the complete legal-document comparison remain unverified.

Evidence: [browser destination](raw/ogon-vpn/2026-07-22/screenshots/05-privacy-policy-destination.png), [loaded privacy page](raw/ogon-vpn/2026-07-22/screenshots/06-privacy-policy-loaded.png).

The in-app **«Договор оферты»** link opens `https://ogonvpn.xyz/terms/`. Material clauses observed on that public page:

- merely registering, ordering, paying or otherwise using the product counts as unconditional acceptance;
- the contractor may change the offer and plans unilaterally, with continued use treated as acceptance;
- payment methods include bank cards and payment systems;
- §3.5 says unused periods are not refunded unless otherwise provided, while the paywall prominently advertises a 30-day refund — the exact interaction between these statements is not explained in the captured UI;
- subscriptions renew automatically for the same period at the then-current price unless cancelled before expiry;
- cancellation is available in-app or through the named Telegram support endpoints; the document says stored payment data is then fully removed;
- the service may suspend access for more than **500 GB in 30 days**, with a possible increase to 1 TB on request, despite the paywall's **«без ограничений»** claim;
- sharing credentials is forbidden except with close relatives;
- blocking for a breach may occur without refund;
- Russian law governs the offer, even though the named contractor is a Georgian LLC.

The app-linked terms page was not retained as a screenshot because the browser chrome exposed unrelated open-tab titles. A clean web capture and full Privacy/Terms/Recurring comparison remain for the external pass.

### Recurring-payment terms

The linked recurring-payment page at `https://ogonvpn.xyz/recurring/` adds terms that are easy to miss in the paywall:

- the next charge may happen automatically without a separate notification;
- the user is expected to monitor the charge date and balance;
- card details are said to remain with the payment provider rather than Огонь;
- renewal can be disabled in the app or through support;
- the provider may retry a failed debit;
- the recurring-payment terms may be changed unilaterally.

The app does show an auto-renew warning and cancellation route in the paywall footer, but it does not surface the retry/no-separate-notice details at the decision point. No plan was selected because opening checkout can create a payment order; that external mutation is outside this audit's no-payment boundary.

## Public Website And Domain Map

`https://ogonvpn.xyz/` and `https://vpn-ogon.com/` currently serve materially identical landing pages. Both claim no logs, a protected channel, **28 ms** ping, a **920 Mbps** peak, unlimited access, connection in under a minute, automatic renewal and support for any device. These are marketing claims, not independently reproduced benchmarks.

The landing page advertises **199 RUB/month**, versus **249 RUB** for the one-month in-app plan and **124 RUB/month** as the displayed annual effective price. Its main connect/Telegram control leads to `https://t.me/ogonvpn`; the Android control leads to the exact Play package `com.ogonconnect.app`.

Both domains expose the same Privacy, Terms and Recurring pages. The copies under `vpn-ogon.com` still name and link `ogonvpn.xyz`, which makes the newer domain look like a distribution mirror rather than a separately maintained product surface. The duplicated surface is useful for resilience, but pricing and capability copy are not synchronized with the installed app.

## Legal-Entity Mapping

A current query to the official Russian FNS EGRUL service for the Play-listed publisher returned **ООО «Ф2П»**, OGRN `1197847093564`, INN `7804643815`, KPP `780201001`, registered 2019-04-16 in St Petersburg. The public search response did not expose an explicit active/terminated flag, and the official PDF-extract request failed, so this pass does not convert secondary live-status data into an authoritative claim.

The app-linked legal pages instead name Georgian **RELOCUP LLC**, identification number `447009282`, at the Kobuleti address recorded above. An exact current extract was not obtained from Georgia's National Agency of Public Registry; formation date, officers, owners and current status remain `BLOCKED_BY_ACCESS`. A separate Relocup-branded incorporation-services website is not sufficient proof that it owns or controls this VPN entity.

The public surfaces do not explain whether ООО «Ф2П» is developer/publisher, RELOCUP LLC is merchant/controller, or how contractual and personal-data responsibilities are divided. Evidence notes: [registry notes](raw/ogon-vpn/2026-07-22/documents/registry-notes.md).

## Static Android Package Readout

The installed Play build was copied to quarantined temporary storage for local, non-invasive inspection. The base APK was 45,715,889 bytes with SHA-256 `0BE4CEAECA9A46C13FE591E48ADA070117E1AA135D1BEB5FE19A5A595FBDC396`; raw APKs, credential-like values and connection material are not retained in this worktree.

### Platform surface

- Minimum SDK 27, target SDK 35; phone/touchscreen and Android TV/Leanback entry points are present.
- The manifest requests Internet/network state, VPN foreground-service, wake-lock, notification, billing, license-check and `QUERY_ALL_PACKAGES` access. The latter explains how the bypass picker can enumerate every installed app.
- The main activity accepts launcher, `SEND */*` and `ogonvpn://` deep-link intents.
- An exported Xray VPN service is protected by Android's `BIND_VPN_SERVICE` permission; a second AdGuard TrustTunnel VPN service is non-exported. A Quick Settings tile is also shipped.
- Cleartext traffic is disabled by network-security configuration.

### Network and resilience architecture

The package contains Xray configuration/service code, AdGuard's TrustTunnel native library, GeoIP/GeoSite data, a kill-switch coordinator, host-discovery logic and a smart fallback executor. The primary API hostname is `api.ogonvpn.com`.

It also contains 62 randomized-looking `.xyz` hostnames alongside cached alive/dead/sticky-host state, batch and emergency scans, latency ranking, and request-host rewriting. Taken together, this strongly indicates an anti-blocking API fallback pool. No hostname was probed, and the current activation/order of the pool was not inferred. Safe retained list: [static domain inventory](raw/ogon-vpn/2026-07-22/scrapes/static-domain-inventory.md).

Connectivity-check strings include `captive.apple.com`, `www.google.com` and `ya.ru`. DNS-related strings include AdGuard DNS, Google DNS and Quad9, but package presence does not prove those resolvers are active or user-selectable in the captured state.

### Shipped capabilities not exposed as finished UI

Client routes and method names include device-seat generation/acceptance/revocation, leaving a shared account, device removal/restoration/settings, payment creation/status, renewal cancellation, grouped plans, profile/usage, announcements/feed/resources, bug reports and connection/node retrieval. This is strong evidence that the shipped client and backend contract already support much of the multi-device/payment machinery shown in old store creatives, even though the current paywall labels cross-device use **«Скоро»**. No API endpoint was called directly.

### Telemetry and sensitive-pattern check

Bugsnag crash/performance components, native crash detection and ANR metadata are bundled. Instrumentation presence alone does not prove which events were transmitted in this session, but it conflicts with the Play declaration **«no data collected»** unless the implementation/configuration truly disables collection or an applicable disclosure exception exists.

A narrow offline pattern scan found no Google API key, Telegram bot token, AWS access key, private-key block, JWT, Stripe secret or GitHub token pattern. This is not a general security audit and does not prove absence of other secrets.

## Google Play Surface

Current public Google Play data for `com.ogonconnect.app`:

| Field | Observed public value |
| --- | --- |
| Installs | 10M+ |
| Rating | **4.4** on the emulator's live Russian Play page; web-localized snapshots ranged up to 4.7 |
| Reviews | **127,074** on the live device page; web-localized snapshots showed roughly 122K–132K, demonstrating locale/indexing variation |
| Last update | 2026-04-13 |
| What's new | stability improvement only |
| Ranking | #4 in free Tools on the live device page |
| Store creative | Four portrait screenshots |
| Listed developer | **F2P, OOO** |
| Developer contact | `mail@facetoplace.app`; St Petersburg address; Belgian-format public phone number |
| Product support | `support@ogonvpn.xyz` |
| Data safety declaration | no data shared with third parties; no data collected |

This reveals a two-entity presentation that needs proper registry tracing: Google Play names Russian **F2P, OOO**, while app-linked legal documents name Georgian **RELOCUP LLC**. The documents reviewed so far do not explain the relationship or division of controller, merchant and publisher responsibilities.

The Play listing promotes one account for up to five devices, unlimited traffic without time/volume limits, no stored logs or activity tracking, YouTube 4K, low-lag gaming, encryption and one-click use. Current in-app evidence conflicts with several of those messages:

- **cross-device use:** the paywall marks use on any devices as **«Скоро»**;
- **unlimited traffic:** the free state is capped at 5 GB, and the offer allows suspension above 500 GB/30 days on paid service;
- **no data collected:** the first-connect disclosure says it processes server-issued account IDs, subscription status, selected server, aggregate traffic and optional diagnostic events.

The live Play data-safety card adds a fourth mismatch: it says there is **no in-app way to request data deletion**, while the linked privacy policy says users may request deletion through support. The support route may satisfy the policy operationally, but it is not surfaced to Play as a deletion mechanism.

The displayed Play reviews contain both strong speed/ease-of-use praise and recent complaints alleging a connected-looking state without working traffic, recurring technical work, ignored support and unsuccessful refund requests. These are user reports, not independently proven incidents; they are useful hypotheses for targeted reliability/refund testing.

Google Play's live-device **F2P: другие приложения** shelf linked Огонь to installed competitors **Ping VPN** and **Батя VPN**, plus **Elyx VPN** and **VPN BOX**. Web-localized shelves additionally surfaced IntVPN, Sau and Neron AI. This publisher cluster should be analyzed as a portfolio, not as unrelated apps.

The current recommendation shelves were:

- **Другие интересные приложения:** DuckDuckGo & Duck.ai, Windscribe VPN, Yandex Browser and Psiphon VPN.
- **Похожие приложения:** AdGuard VPN, Aloha Browser/Private VPN and Yandex.

### Store creative versus installed product

The four store screenshots are materially out of sync with version 0.84:

1. **«Рабочий VPN для России»** shows an older home with a **Профиль** tab, a 100 GB / 100 GB allowance and 3/10 bypass categories; the installed state uses **Подписка**, shows 5 GB / 5 GB and 2/29 in the home summary.
2. **«Авто выбор лучшего сервера»** presents Italy, France, Germany, Netherlands, Kazakhstan, Armenia and USA as free-looking `F` entries; the installed free group exposed only Netherlands #2, Netherlands and Germany plus auto-selection.
3. **«До 5 устройств одновременно»** shows a mature device-management/profile flow with owner, invited devices, device settings and join-by-invitation controls; the installed Premium paywall marks any-device support **«Скоро»** and no equivalent management surface was found.
4. **«Отдел заботы о пользователях»** promises live employees in Telegram and illustrates a three-minute reply; the current paywall promises a 15-minute support response. The creative is a claim, not response-time proof.

This is more than cosmetic drift: acquisition promises, free-server availability, allowance, information architecture and shipped capability are inconsistent. It can improve conversion short-term but creates refund/support risk and makes review complaints about paid reliability more credible as test hypotheses.

Evidence: [live Play listing](raw/ogon-vpn/2026-07-22/screenshots/30-google-play-listing.png), [store screenshot 1](raw/ogon-vpn/2026-07-22/screenshots/31-play-screenshot-1.png), [store screenshot 2](raw/ogon-vpn/2026-07-22/screenshots/32-play-screenshot-2.png), [store screenshot 3](raw/ogon-vpn/2026-07-22/screenshots/33-play-screenshot-3.png), [store screenshot 4](raw/ogon-vpn/2026-07-22/screenshots/34-play-screenshot-4.png), [recommendation shelves](raw/ogon-vpn/2026-07-22/screenshots/35-play-recommendations.png), [data safety](raw/ogon-vpn/2026-07-22/screenshots/36-play-data-safety.png), [publisher/support details](raw/ogon-vpn/2026-07-22/screenshots/37-play-developer.png).

Source: `https://play.google.com/store/apps/details?id=com.ogonconnect.app` (captured 2026-07-22; store numbers are volatile).

## Competitive Readout So Far

### What is strong

- Immediate anonymous use with a meaningful 5 GB allowance.
- A simple five-tab IA and a highly legible connect screen.
- Local-market packaging: Russian services, government sites, marketplaces and YouTube-specific routing are treated as first-class jobs.
- Bypass is understandable to non-technical users: apps and named service categories, not protocol jargon.
- Pricing is materially simpler than Hiro's three-tier matrix, with a visible long-term discount ladder and one refund promise.
- The shipped anti-blocking architecture is substantially deeper than the simple UI suggests: multiple VPN engines, host discovery, cached health state and automatic API fallback are bundled.
- Structured error/idea reporting and Telegram support are visible directly from the home screen.

### Weaknesses and claims to verify

- Ultra and cross-device use are promoted before availability.
- The Premium location list appears heavily concentrated in the Netherlands despite a **«Страны Premium»** label; UI entries alone do not prove geographic infrastructure.
- The current device did not expose a clean-install onboarding path.
- Support SLA, YouTube ad removal, refund execution, auto-renew cancellation and payment rails remain claims until their real operational flows are tested.
- Anonymous identity lowers friction but may create recovery and portability risks.
- Store creatives, website copy, paywall copy, legal limits and Play Data Safety disagree on several conversion-critical facts.
- The publisher/contractor relationship between ООО «Ф2П» and RELOCUP LLC is not explained publicly.

## Remaining Work For This App

1. Establish historical Android update cadence if a defensible first-party or clearly labelled secondary source exists; Google Play and the public Telegram history expose no reliable version timeline.
2. Retry authoritative RELOCUP LLC registry verification only through the public Georgian registry; current status remains blocked.
3. Determine whether referral, promo-code, trial and account-recovery entry points exist outside the captured anonymous flow.
4. Checkout/payment-method capture remains `NOT_REQUESTED`: reaching it may create an external order, and no payment action is authorized.

## Evidence Boundaries

- Огонь was force-stopped after capture; no app process or `tun0` interface remained before moving on.
- No purchase, public post, review, support message or destructive account action will be submitted.
- Personal credentials, generated device identifiers, raw VPN endpoints and provider payloads are excluded from the worktree.
- Temporary control changes are restored immediately and recorded as temporary states.

# VPN Наружу — Mobile App Competitor Profile

**Status:** `DEEP PASS COMPLETE WITH BLOCKERS — NATIVE APP, NO-CARD TRIAL, PAYWALL, SUPPORT/FAQ, SMART/DIRECT ROUTING, THREE CONTROLLED CONNECTIONS, PLAY/WEBSITE/GUIDES/TELEGRAM/RELEASES, LEGAL DRIFT, DIRECT APK/WINDOWS AND STATIC ARCHITECTURE CAPTURED`<br>
**Snapshot date:** 2026-07-22<br>
**Android package:** `online.vpnnaruzhu.client.android`<br>
**Installed version:** `1.8.1` (`versionCode 90`; in-app label `1.8.1.90`)<br>
**Install source:** Google Play

## Executive Read

VPN Наружу has a sharper Russian-market operating system than its very small app suggests. The native product is a black/yellow, email-only, no-card seven-day trial built around one differentiated promise: **Smart mode leaves Russian services direct and sends foreign services through a foreign exit**. Around that thin client sits a much larger machine: Telegram as release/status/giveaway channel, direct APK and Windows distribution, router and TV guides, influencer proof, gift/team sales, eSIM and router cross-sells, outage compensation and a parallel product incubator.

The growth and anti-blocking operations are worth studying. Product truth and compliance are not. The audited build advertised 35–36 countries but exposed 13; Direct/Automatic retained the ordinary exit for the tested destination; a specific UAE node showed Connected while DNS and Internet were unusable; current public documents resolve to several operators and four governing-law/controller stories; and the APK embeds the Russian state root CA plus a large analytics/ad stack alongside aggressive “no logs” language.

## First Launch, Registration And Trial

The isolated first screen is an unusually compressed pitch:

- “Умный VPN, который открывает всё”;
- up to 300 Mbit/s;
- up to 10 devices;
- 36 countries;
- result guarantee;
- responsive support;
- private and protected traffic;
- one Continue action and a persistent Telegram destination.

There is no carousel, protocol choice, location permission or payment gate. Evidence: [isolated launch](raw/vpn-naruzhu/2026-07-22/screenshots/01-isolated-launch.png), [UI tree](raw/vpn-naruzhu/2026-07-22/ui/01-isolated-launch.xml).

Continue opens a passwordless email flow with Send code and Support. Registration through the authorized Gmail account delivered a four-digit OTP from the public `vpn-naruzhu.com` mail domain. Successful verification immediately granted a **seven-day Premium trial without a card**, without presenting an auto-renewing checkout and without demanding a password. Account address, OTP and signed-in screenshots are quarantined outside the repository. Evidence: [email entry](raw/vpn-naruzhu/2026-07-22/screenshots/02-after-continue.png).

The no-card trial is one of the strongest conversion choices in the cohort: it proves the product before payment, removes Google Play billing dependence and gives the vendor an email identity that works across Android, Windows and the web portal.

## Home, Modes And Country Catalog

The home has only the controls required to connect:

- top tabs **Умный режим** and **Напрямую**;
- country selector, default **Автоматически**;
- enormous yellow Connect circle;
- connected state changes to a white circle with a pause-like icon and `ОТКЛЮЧИТЬ`;
- Premium/trial status, days remaining, Buy subscription and Support;
- Telegram at the top and profile/logout at the edge.

Smart is explained as split routing: Russian services go through Russia/direct, foreign services through a foreign server. Direct is described as sending all traffic through a foreign server and warns that some Russian services may fail. The FAQ recommends Smart as the default.

Both modes exposed the same trial catalog:

1. United Arab Emirates;
2. Denmark;
3. Finland;
4. France;
5. United Kingdom;
6. Hungary;
7. Ireland;
8. Israel;
9. Italy;
10. Latvia;
11. Netherlands;
12. Turkey;
13. Ukraine.

There was no hidden second page. This materially differs from the 35-country FAQ list and the 36-country app/store promise. The public 35-country list additionally names Armenia, Austria, Australia, Belgium, Bulgaria, Brazil, Canada, Switzerland, Czechia, Germany, Estonia, Spain, Georgia, Hong Kong, Japan, Kazakhstan, Norway, Poland, Romania, Serbia, Singapore and the United States. A 2026-07-08 Play review reports disappeared countries; the developer replied on 2026-07-09 that the reduction was temporary and locations would return. The live app gives no degraded-catalog explanation.

## Account And Paywall

The account surface is deliberately sparse: email, Trial state, one Premium card, “Сохрани возможности Premium”, “без рекламы”, plan selection, version, Telegram and logout. It exposes no device list, session revocation, invoice history, data export or deletion control in the tested native route.

The embedded payment surface offered:

| Period | Displayed monthly rate | Charged total |
| --- | ---: | ---: |
| 1 month | 490 ₽/month | 490 ₽ |
| 6 months | 490 ₽/month | 2,940 ₽ |
| 12 months | 390 ₽/month | 4,680 ₽ |
| 24 months | 290 ₽/month | 6,960 ₽ |

Optional auto-renew was **off** by default and explicitly cancellable. Promo-code entry was optional. Payment choices were:

- SBP;
- Russian card, YooMoney, SberPay or T-Pay;
- foreign card;
- cryptocurrency.

The landing page omits the six-month plan but otherwise matches current one-, 12- and 24-month pricing. No payment method was submitted and no order was created. Evidence: [plan selector](raw/vpn-naruzhu/2026-07-22/screenshots/03-paywall-periods.png), [all periods](raw/vpn-naruzhu/2026-07-22/screenshots/04-paywall-periods-open.png), [methods and calculation](raw/vpn-naruzhu/2026-07-22/screenshots/05-paywall-lower.png).

The paywall also embeds a Chatwoot-style “Наружу поддержка” widget. It requests a preferred name and can prefill account context before “Start chat with operator”. No name was entered and no chat was started. Evidence: [paywall chat](raw/vpn-naruzhu/2026-07-22/screenshots/06-paywall-chat.png).

## Support, FAQ And Recovery Paths

The native support center has eight FAQ items; every item was opened and retained:

| # | Question / answer substance | Evidence |
| --- | --- | --- |
| 1 | One subscription supports up to 10 devices, including a router. | [FAQ 1](raw/vpn-naruzhu/2026-07-22/screenshots/faq-1.png) |
| 2 | The product claims to solve YouTube access. | [FAQ 2](raw/vpn-naruzhu/2026-07-22/screenshots/faq-2.png) |
| 3 | It claims data and information about visited resources are not stored or transferred anywhere. | [FAQ 3](raw/vpn-naruzhu/2026-07-22/screenshots/faq-3.png) |
| 4 | Seven-day free trial; user may decline; no card required. | [FAQ 4](raw/vpn-naruzhu/2026-07-22/screenshots/faq-4.png) |
| 5 | Registration needs only email. | [FAQ 5](raw/vpn-naruzhu/2026-07-22/screenshots/faq-5.png) |
| 6 | “More than 30” countries, followed by a 35-country list. | [FAQ 6](raw/vpn-naruzhu/2026-07-22/screenshots/faq-6.png) |
| 7 | Smart versus Direct behavior, 35 countries and Any/Automatic selection. | [FAQ 7](raw/vpn-naruzhu/2026-07-22/screenshots/faq-7.png) |
| 8 | Missing OTP: check Spam, Promotions and Deleted. | [FAQ 8](raw/vpn-naruzhu/2026-07-22/screenshots/faq-8.png) |

“Сменить сервер” opens a recovery modal explaining that another server may help. It offers Change server, Contact support and Close. The destructive/quota-changing confirmation was not executed. Public release notes later state a limit of ten server changes per day, separately per country and mode; the modal itself does not explain that quota before the first action.

The support handoff generates a per-device support code and offers Copy code, Telegram and email:

- Telegram opens public bot [`@vpn_naruzhu_ops_bot`](https://t.me/vpn_naruzhu_ops_bot) with a personalized start token and automatically copies the support code;
- email dispatches a `mailto:` intent, but LDPlayer had no compatible mail handler;
- the guide calls the value Device ID while the native UI calls it a support code.

The code, personalized bot token and account context were not retained. No message was sent.

## Controlled Connection Results

Three isolated tests were run after Android VPN consent:

1. **Smart / Automatic:** `tun0` came up; DNS and HTTPS worked; the tested destination retained the disconnected exit, which can be consistent with split routing.
2. **Direct / Automatic:** `tun0` came up; HTTPS worked; the same tested destination again retained the disconnected exit, contradicting the FAQ's “all traffic through foreign server” claim for this state.
3. **Direct / UAE:** `tun0` came up and the app displayed Connected, but browser DNS failed, direct reachability failed and Private DNS logged TLS timeouts/validation failure.

The app disconnected normally after each run and the final check found no tunnel. This is one Android x86_64 emulator observation, not proof for all destinations or ARM devices. Full redacted evidence: [connection health summary](raw/vpn-naruzhu/2026-07-22/connection-health-summary.md).

## Public Website And Instructions

The current public landing is [`vepen.online/landing`](https://vepen.online/landing/). It uses the same black/yellow brutalism but makes a louder promise: “УМНЫЙ VPN, КОТОРЫЙ ОТКРЫВАЕТ ВООБЩЕ ВСЕ”. It advertises 100,000+ users, 300 Mbit/s, 10 devices, 36 countries, no traffic recording, support and a result guarantee. Evidence: [website hero](raw/vpn-naruzhu/2026-07-22/screenshots/22-website-hero.png).

Trust presentation combines:

- influencer videos/logos, including Ilya Varlamov and Mikhail Kozyrev;
- “verified” testimonials without a visible verification provider;
- “based on 1,279 reviews” without a source destination;
- public user-count and guarantee claims with no methodology.

The guide hub covers:

- **Android:** Google Play or direct APK, email OTP, Smart/Direct, 35 countries and support Device ID;
- **Windows:** direct executable download, plus instructions to bypass the Windows warning through `Подробнее` → `Выполнить в любом случае`; email OTP, Smart/Direct, 35 countries and Device ID;
- **iOS/macOS:** portal key generation, installation of an unnamed suggested client and `vpn://` key import; no stable public App Store/client identity in the guide;
- **Android TV:** Play install, email OTP and Connect, with an admission that TV UI display quirks are possible;
- **Keenetic / AWG:** download `.conf`, use the public Gokeenapi utility, enter router administration address/login/password and import the configuration;
- **Keenetic / L2TP/IPsec:** request credentials manually from support; each router consumes a device slot; follow a long 12-step setup.

All guide pages miswire “Написать на почту” to the Telegram support bot instead of email. The L2TP page also has weak step ordering and dummy credential examples that can be mistaken for real values.

## Destination And Distribution Map

| Origin | Observed destination / behavior |
| --- | --- |
| App Telegram action | [`t.me/vpnnaruzhu`](https://t.me/vpnnaruzhu) |
| Native support | [`t.me/vpn_naruzhu_ops_bot`](https://t.me/vpn_naruzhu_ops_bot), personalized token omitted |
| Current website | [`vepen.online/landing`](https://vepen.online/landing/) |
| Guides | [`vepen.online/landing/guides`](https://vepen.online/landing/guides) |
| Google Play | [`online.vpnnaruzhu.client.android`](https://play.google.com/store/apps/details?id=online.vpnnaruzhu.client.android) |
| Direct Android | [`l.vpnn.io/nrapk`](https://l.vpnn.io/nrapk), immediate universal APK download |
| Direct Windows | [`l.vpnn.io/nrwin`](https://l.vpnn.io/nrwin), ZIP with EXE and Wintun |
| Current offer | [`vepen.online/landing/public-offer`](https://vepen.online/landing/public-offer) |
| Current privacy | [`vepen.online/landing/privacy`](https://vepen.online/landing/privacy) |
| Play privacy link | [stale 2024 Telegraph policy](https://telegra.ph/Privacy-Policy-06-01-98) |
| Armenia | [`naruzhu.am`](https://naruzhu.am/) and [`/docs/public-offer`](https://naruzhu.am/docs/public-offer) |
| Georgia | [`naruzhu.ge`](https://naruzhu.ge/) and actual [`/landing/public-offer`](https://naruzhu.ge/landing/public-offer); public `/offer` redirects incorrectly |
| Outage compensation | [`naruz.work`](https://naruz.work/) |
| Parallel VPN Перемен APK | [`peremen.app/landing/apk`](https://peremen.app/landing/apk) |

Historical/acquisition domains also include `nrz.monster`, `vepen.click`, `naruzhu.click` and a now DNS-dead `vpn-naruzhu.click` still linked from Google Play. Some older routes behave as trackers or redirects; personalized query parameters were stripped from evidence.

The direct Android download produced Chrome's “Невозможно безопасно скачать файл” warning. Static comparison nevertheless found the direct universal APK and Play split build to have identical code, signer lineage and Play Source Stamp. The Windows package was also signed, but its filename/version metadata conflicts with public release copy. Details: [static summary](raw/vpn-naruzhu/2026-07-22/static-summary.md).

## Telegram As The Operating System

The app's top action resolves to a public channel with roughly 28.5K subscribers at capture time. Evidence: [destination card](raw/vpn-naruzhu/2026-07-22/screenshots/16-telegram-destination.png), [public preview](raw/vpn-naruzhu/2026-07-22/screenshots/17-telegram-preview.png).

The channel was created on 2023-11-28 and has substantive public content from 2025-04-14. It is not just social media; it is the release train, anti-blocking status page, research panel, campaign engine and fallback distributor.

| Period | Observed operating pattern |
| --- | --- |
| 2025-05 | Official resource post, influencer endorsements and giveaway of 30 subscriptions. |
| 2025-09 | Android `1.4.1.52` shipped in response to Russian filtering. |
| 2025-10 | Windows `2.1.6.2` advertised an updated protocol; Google Form research on foreign bank cards paid participants three Premium days. |
| 2025-11 | Black Friday doubled every purchased period; a separate bot ran prizes including iPhone 17, Beats, TV boxes and annual plans; 1,736 entrants; masked winner emails/usernames/IDs were published. Channel formally renamed VPN Наружу. |
| 2025-12 to 2026-01 | Annual 57% promo to 2,026 ₽; one-/two-year gift certificates; team bundles of 10/20/30 promo codes delivered by email; OxySIM affiliate recommendation with a 1 GB / seven-day eSIM test. |
| 2026-02 | Mobile/Windows country selector release required manual reinstall; Telegram promo code gave 15%. |
| 2026-03 | 30% sale; launch of a VPN-enabled router, later bundled with one Premium year and CDEK delivery. |
| 2026-04 | B2B discovery for blocked/exited services, foreign payment, no-VPN access and TV/VR; customer interviews and early free tests through a named Telegram contact. |
| 2026-06 | Heavy outage/RKN-pressure communications; manual AmneziaWG keys deprecated; RU iOS listing hidden; reserve client and dynamic keys moved to support; Windows server switching and alternate client; one-month compensation. |
| 2026-07 | Football score-comment contest and political-simulator bot rewards; launch of parallel **VPN Перемен** for reverse split tunneling of Russian services while abroad. |

VPN Перемен was distributed as a 41.9 MB Telegram APK before store approval and advertised a browser extension. Both the “APK” and “browser extension” buttons resolved to the same APK route, so the extension handoff was mislabeled or unfinished. Static Android code in VPN Наружу contains `peremen` and another `vpneko` product module, strongly indicating a shared multi-brand codebase.

The channel also runs a broad SEO/content loop around Tor, Telegram history, YouTube algorithms and Cambridge Analytica. During outages it communicates rapidly, publishes alternative packages and compensates users. This operational transparency is a competitive advantage even when the underlying product is unstable.

## Google Play, Reviews And Client-Named Alternatives

At capture time Google Play showed:

- title **VPN Наружу: быстрый ВПН сервис**;
- developer **VPN Наружу**;
- about 4.1 overall / 4.2 phone rating;
- roughly 1.67K ratings and 1.56K phone reviews;
- 100K+ downloads;
- in-app purchases, age 3+;
- last update 2026-06-26;
- changelog: country selector, Android TV support, bug fixes and performance.

Evidence: [Google Play listing](raw/vpn-naruzhu/2026-07-22/screenshots/21-google-play.png).

Data Safety says no third-party sharing, possible collection of personal information, app information/performance and device/other identifiers, encryption in transit and an available deletion request. That is already broader than the native FAQ's “stored/transferred nowhere” wording.

Positive review themes were no-card trial, simple onboarding, one account for ten devices, Smart mode that can be left alone and useful support when it responds. Repeated pain points were:

- multi-day support delays during the June outage;
- Smart mode, Russian sites and notifications failing;
- missing user-controlled split tunneling/whitelist despite bot suggestions;
- repeated server switching/restarts;
- battery drain;
- missing Android TV region selection;
- disappeared countries;
- retired Amnezia/manual keys;
- Connected/Direct state without working apps;
- at least one Hotmail OTP failure.

The only concrete client-named alternative in the sampled recent review set was **Amnezia / AmneziaWG**, mainly because VPN Наружу previously distributed manual keys for it. Other unhappy users said only “free VPNs” or “another VPN” without naming a competitor.

## Legal Entity And Privacy Map

There is no single coherent controller/counterparty story.

### Kazakhstan main offer

The current main [public offer](https://vepen.online/landing/public-offer), revision 2025-02-19, identifies **ИП Замолоцких Кирилл Александрович** in Almaty, Kazakhstan. It uses Kazakhstan law, describes monthly auto-renewal, allows refund requests through support with processing up to 30 working days, accepts app/site/Telegram/email formation and says the service is intended only outside Kazakhstan.

The same document says the provider does not collect/process/transfer personal data, yet elsewhere defines email/payment processing, permits collection of site visitor IP and conflicts with Play Data Safety. It is an “as is” contract with no uptime guarantee.

### Armenia

The Armenian [offer](https://naruzhu.am/docs/public-offer), revision 2025-03-25, names **ООО “СТАРРОКЕТС” / STARROCKETS LLC**, Yerevan. The body is visibly copied from the Kazakhstan contract: it still selects Kazakhstan law, says use is permitted only outside Kazakhstan and retains Kazakhstan personal-data language. This is a material contract-localization failure.

### Georgia

The Georgian footer says **Akhali LLC**, while the actual offer names **LLC “AkhaliNet”** with Georgian registration details. It selects Georgian law and says use is permitted only outside Georgia. The advertised `/offer` path redirects to the landing; the actual offer is hidden at `/landing/public-offer`.

### Current and stale privacy policies

The current [privacy policy](https://vepen.online/landing/privacy), effective 2026-03-20:

- promises no activity logs and no connection logs, specifically no source/assigned IP, timestamps or session duration;
- says operational state is volatile/RAM-only;
- allows email or Telegram username/ID, payment-processor data and crypto transaction IDs;
- does not name the controller/legal entity;
- selects **Seychelles law**, matching none of the three regional offers.

Google Play still points to a [Telegraph policy](https://telegra.ph/Privacy-Policy-06-01-98) dated 2024. It names **IT Vega, TOV** as controller and admits third-party libraries/cookies plus error Log Data that can include device identifier/name, OS, app configuration, timestamps and statistics.

The public identity stack is therefore:

1. stale Ukrainian-style `IT Vega, TOV` controller in Play privacy;
2. Kazakhstan individual entrepreneur in the main offer and current Android signing subject;
3. Armenian STARROCKETS LLC;
4. Georgian Akhali/AkhaliNet LLC;
5. unnamed controller under Seychelles law in the newest privacy text;
6. Serbian `NOVINET DOO` as Windows code signer.

This does not prove common ownership among every entity. It does prove that a user cannot determine one authoritative controller, counterparty and governing law from the current public surfaces.

## Static Product Architecture

The current Android artifact is a Kotlin/Compose client with Ktor/OkHttp, Koin and AmneziaWG-derived native code. It supports four Android ABIs and has private foreground/tunnel services, Quick Settings tile, boot receiver and Firebase Messaging.

The app includes Yandex Mobile Ads, Yandex Div/Varioqub, AppMetrica including screenshot-module code, Firebase Analytics/Crashlytics/Sessions/Messaging/Remote Config, Play Billing, advertising ID and AdServices attribution. No camera, microphone, contacts, storage or Android location permission was observed; Android backup is disabled.

Remote Config controls update availability/requirement, localized copy and download destinations, as well as Telegram/product/guest configuration. The app bundles the Russian Ministry of Digital Development's **Russian Trusted Root CA** alongside system trust roots for its own TLS connections. This is an app-scoped trust expansion, not a system-wide certificate install.

The direct APK and Play build share byte-identical DEX, signer lineage and source stamp. The Windows ZIP contains a validly signed Serbian-vendor executable and Wintun 0.14.1, but the package filename `1.0.0.1` cannot be reconciled with Telegram's later `2.1.6.2` release story because the EXE has no version metadata. Full evidence: [static and distribution summary](raw/vpn-naruzhu/2026-07-22/static-summary.md).

## Design And Product Critique

### What works

- Black/yellow identity is instantly recognizable and survives app, web, Telegram and merch/router contexts.
- One huge connect control and two plain-language routing modes beat protocol jargon for a mainstream user.
- Email OTP plus a genuine no-card trial makes activation exceptionally low-friction.
- Smart mode is positioned as an outcome (“foreign opens, Russian keeps working”), not as split-tunneling configuration.
- Support, server change and Telegram status are reachable from the home rather than buried.
- The operational layer is excellent at mirrors, direct builds, outage explanations, compensation and customer research.
- Gift/team bundles, router, eSIM and B2B interviews extend revenue without cluttering the native client.

### What breaks trust or usability

- 36-country promise, 35-country FAQ and 13-country live catalog are shown with no degradation banner.
- Connected is a UI state, not a health state: the UAE test had no DNS/Internet and Direct/Automatic did not alter the tested exit.
- The white connected circle uses a pause-like symbol while the label says Disconnect.
- Country/server health, latency and route decision are invisible; the user cannot tell why Smart bypassed a destination.
- Server-change quota is documented later in Telegram, not at the recovery action.
- Paywall and chat load as embedded web surfaces and feel slower/less coherent than the native shell.
- Profile/account is too thin for a ten-device claim and exposes no active-device/session control.
- “Email support” links to Telegram in guides; stale/dead store and regional legal links remain live.
- Review/testimonial proof is self-asserted, and legal/operator truth changes by surface.
- The product says no logs while shipping several analytics, crash, messaging, experimentation and ad systems without a clear event-level disclosure.

## What POKROV Should Copy

1. **Outcome-first Smart mode.** Keep Russian banking/state/media destinations direct and foreign/problem domains tunneled, but show the routing decision and provide a per-domain “route through VPN / direct” override.
2. **No-card proof.** Seven useful days after email OTP is stronger than a payment-authorized trial. Pair it with abuse limits rather than card pressure.
3. **One identity across clients.** Email OTP should unlock Android, Windows, TV, router keys and web cabinet; add device/session management that Наружу lacks.
4. **Anti-blocking release hub.** One signed, versioned download page with Play, direct APK, Windows, checksums, signer fingerprint, release notes, mirrors and current incident state.
5. **Visible recovery.** Country change, server change, protocol fallback and diagnostics should be available from the failed connection, with quotas stated before action.
6. **Operational honesty.** Telegram-style outage updates, alternatives and automatic compensation are worth copying into an owned status page plus in-app banner.
7. **Research loops.** Rewarded interviews, gift codes, team packs and B2B pilots are effective when consent and reward terms are explicit.
8. **Native minimalism.** Keep the daily home as small as Наружу, but put detailed diagnostics and trust controls one level down.

## What POKROV Should Not Copy

- marketing a fixed country count that the live entitlement cannot deliver;
- treating `tun0`/Connected as proof that DNS and egress work;
- multiple operators/policies/governing laws without a single controller map;
- telling users to bypass OS download warnings without publishing checksums and signer verification;
- hiding iOS client identity behind support-issued keys;
- public winner lists containing even masked emails/usernames/IDs;
- silently trusting an additional national CA;
- broad analytics/ad capability under absolute “stored/transferred nowhere” copy;
- parallel-brand launches with duplicate/miswired APK and extension buttons;
- release binaries whose filenames, embedded versions and public changelogs disagree.

## Remaining Blockers And Scope Limits

- No purchase, auto-renewal, refund or paid-only period was initiated.
- No support chat/message, server-change mutation, public comment, giveaway entry or review action was submitted.
- The hidden/reserve iOS/macOS client requires a support-issued key; that handoff was not requested.
- Windows and direct Android binaries were inspected but not executed or installed over the Play build.
- The controlled tunnel result is limited to one LDPlayer x86_64 environment and three route selections.
- Public offers establish presented identities, not current registry good standing or ultimate beneficial ownership.
- Telegram history was audited through the accessible public timeline; deleted/private posts and bot-only branches are not recoverable.

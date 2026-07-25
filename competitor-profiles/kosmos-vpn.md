# Космос VPN — Mobile App Competitor Profile

**Snapshot date:** 2026-07-22<br>
**Status:** `DEEP PASS COMPLETE WITH BLOCKERS` — registration, signed-in native UX, settings, TV pairing, authenticated cabinet, live tunnel, public web/store/channel/legal surfaces and redacted Android architecture captured; current Armenian entity status and Apple TV handoff remain unresolved<br>
**Android package:** `ru.space.vpn`<br>
**Installed version:** 1.3.3 (`versionCode 1030301`)<br>
**Install source:** Google Play

Evidence root: [`raw/kosmos-vpn/2026-07-22/`](raw/kosmos-vpn/2026-07-22/)

The earlier `01-launch` artifact remains provenance-only. Accepted current-session evidence begins with `02-isolated-launch`. Screenshots containing the audit email, generated account/device identifiers or personalized cabinet relay tokens were quarantined outside the worktree.

## Product Positioning And Visual System

Космос is a minimalist native client sitting in front of a much larger account, promotion and alternative-client system. Its visual identity is unusually coherent for this segment: a dark moving space background, large gradient wordmark, orbit motif and one oversized power control. The launch promise is blunt: **«VPN, который всегда работает»**.

The brand is memorable and the connected product is easy to understand. The trade-off is that the opening composition is bottom-heavy: the giant decorative title consumes most of the screen while email, primary CTA and support compete in the bottom quarter. The moving MP4 background also creates visual variance and spends package size/GPU budget for atmosphere rather than function.

Evidence: [isolated launch](raw/kosmos-vpn/2026-07-22/screenshots/02-isolated-launch.png), [signed-in home](raw/kosmos-vpn/2026-07-22/screenshots/05-signed-in-home.png).

## Registration And Account

The native entry flow is email-first:

1. enter an email address;
2. tap **Продолжить**;
3. enter a four-digit code from email;
4. land directly on the VPN home.

The code screen includes a resend countdown and the observed email described a five-minute validity window. Registration completed successfully with the owner-authorized Gmail account. No code or address is retained in evidence.

There was no visible terms/privacy consent, age confirmation or legal-document link before account creation. This matters because the privacy policy says the service is not intended for people under 18, while the stores rate the app 3+/4+.

The new account had active access without a purchase. The authenticated cabinet attributed current bonus time to service-outage compensation, so this is **not evidence of a standard signup trial**.

Evidence: [verification-code state](raw/kosmos-vpn/2026-07-22/screenshots/04-email-code.png).

## Native Home And Connection

The signed-in home is intentionally small:

- one large power button;
- selected-server pill;
- connection status and timer;
- two bottom destinations: home and settings.

The first connection requested Android notification permission and then the system VPN consent. After consent, the real tunnel connected: `tun0` existed and controlled route/DNS checks passed. Disconnect removed `tun0`.

There is a serious state/accessibility defect. In the disconnected state, the visible status disappears, but the Android accessibility tree still exposes **«Подключено»** and `00:00:00`. The same stale semantics were present before a tunnel existed. Any automation or assistive technology can therefore report a false connected state.

Evidence: [notification permission](raw/kosmos-vpn/2026-07-22/screenshots/19-notification-permission.png), [Android VPN consent](raw/kosmos-vpn/2026-07-22/screenshots/20-vpn-consent.png), [connected](raw/kosmos-vpn/2026-07-22/screenshots/21-connected.png), [disconnected](raw/kosmos-vpn/2026-07-22/screenshots/22-disconnected.png).

## Server Selection

The selector leads with **Самый быстрый** and explains: **«Чем ближе вы к серверу — тем выше скорость»**. The observed native list had eleven countries:

- Hungary;
- United States;
- Germany;
- Finland;
- Switzerland;
- Poland;
- Netherlands;
- Latvia;
- Russia;
- Austria;
- Kazakhstan.

Every row has one simple signal-strength indicator. There is no search, favorites, city, latency number, streaming/task label or protocol detail. The list is cleaner than most competitors, but the proximity copy is an oversimplification and the current locations differ from rapidly changing Telegram announcements.

The privacy policy says the product should warn users before choosing a server in a jurisdiction with low democratic standards. No such warning appeared for Russia or Kazakhstan in the observed selector.

Evidence: [server selector](raw/kosmos-vpn/2026-07-22/screenshots/06-server-selector.png), [lower server list](raw/kosmos-vpn/2026-07-22/screenshots/07-server-selector-lower.png).

## Settings, Support And TV Pairing

The settings surface contains:

- profile/account and subscription state;
- personal cabinet;
- tariffs;
- referrals;
- support categories;
- Apple TV and Android TV connection rows.

Support is framed as three jobs: report a problem, ask a question and share an idea, each leading to **Написать в поддержку**. Before sign-in, the public support URL redirected to cabinet login. After sign-in, the action opened an authenticated cabinet relay rather than a clearly isolated chat surface. This makes support dependent on a working account/login at the exact moment a user may be locked out.

Android TV is implemented well: tapping it requests camera permission and opens a dedicated green QR scanner with **«Наведите камеру на QR-код на телевизоре»**. The retained capture contains no QR payload. The Apple TV row was exposed as clickable, but repeated taps caused no visible transition or destination in the observed build.

Evidence: [camera permission](raw/kosmos-vpn/2026-07-22/screenshots/10-android-tv-permission.png), [Android TV scanner](raw/kosmos-vpn/2026-07-22/screenshots/11-android-tv-qr-scanner.png).

## Cabinet And Growth Machine

The native client looks almost empty, but the authenticated web cabinet carries the commercial system:

- subscription, balance, months/devices/days and expiry;
- generated account identity;
- **Подключить VPN** setup entry;
- Telegram binding;
- current service-status/compensation banner;
- active and completed prize draws;
- marketing-mail control;
- referral surface;
- Telegram-channel CTA promising updates, promo codes and occasional free plans.

Observed prize campaigns included high-value consumer electronics and appliances. The current cabinet banner said the service had recovered from a DDoS/outage and that seven compensation days were credited; the public Telegram post promised five days. That is a direct operational-copy contradiction.

The cabinet **Подключить VPN** action reached a blank/transient web state in the observed session. Because the surface may depend on JavaScript or account timing, this is recorded as a partial failure rather than a confirmed dead route.

The growth system mixes outage updates, compensation, deadline pricing, promo codes, referrals, raffles and Telegram dependency. It is aggressive but concrete: acquisition, retention and incident communication all have visible incentives.

## Pricing And Alternative Clients

Current public pricing is inconsistent across owned surfaces.

The Telegram channel announced consumer pricing effective 7 June:

| Term | Total | Effective monthly |
| --- | ---: | ---: |
| 1 month | 229 ₽ | 229 ₽ |
| 3 months | 599 ₽ | about 200 ₽ |
| 6 months | 1,099 ₽ | about 183 ₽ |

The channel says this includes three devices, an additional device costs 45 ₽, and a 30 GB allow-list traffic package costs 99 ₽ with unused balance carrying forward.

The public website still shows a structurally different table: Personal 240 ₽/month, Teams 490 ₽/month and Organizations 790 ₽/month, mixed with business-style limits such as connection counts, traffic, clients, deployment and administrator roles. All trial CTAs lead to Telegram. This looks like an older product generation and is not a reliable current consumer tariff source.

Космос deliberately keeps paid access usable through third-party clients. Official instructions have recommended:

- iOS: v2rayTun, Shadowrocket, INCY and, when available, Happ;
- Android: v2rayTun or Happ;
- macOS: v2rayTun or Clash Verge;
- Windows: v2rayTun;
- Android TV: v2rayTun;
- Apple TV: Shadowrocket.

The channel has also published App Store region-change instructions containing placeholder US identity/address data. That is a distribution workaround with legal, account-integrity and support risk; POKROV should not reproduce it.

## Release Pattern And Store Scale

Google Play showed 100K+ installs, an approximate 4.6 rating and roughly one thousand reviews. The listing was updated 29 May 2026, and the installed 1.3.3 build matches the current release line. The changelog names Android TV QR scanning, a revised TV section, automatic logout when a device is removed in the cabinet, timer/server fixes and Huawei/MicroG compatibility.

The Russian App Store listing showed version 1.3.3 dated 2 June 2026, an approximate 3.9/5 rating from about two thousand ratings and a Utilities rank around the high twenties. Observed version cadence: 1.2.8 on 24 February, 1.2.9 on 23 March and 1.3.3 on 2 June. iOS release notes mention Android TV QR, iPad layout, connection reliability and data protection.

The iOS description is internally strange: after advertising an unlimited, no-log, no-ad VPN, it says the app is only a generic client for user-provided proxy servers and supplies no infrastructure or keys. That does not describe the paid managed service, native email registration or current Telegram/cabinet system.

Play review themes are mixed. Positive reviews praise simplicity, stability and low price. Repeated negative reports describe paid access becoming unavailable, account/server/support surfaces failing, and allegedly repeated card charges with difficult cancellation. These are unverified customer reports, not confirmed billing facts.

Nearby Play recommendations included PureVPN, VPNHouse and VeePN. App Store neighbors included Glaz VPN, EVA VPN, VPN 2026, ETNA, MeiLing, VPNS Bot, VpnDoc, Privata, Oneok and BLACKTEMPLE. Store recommendations are algorithmic adjacency, not customer endorsement.

## Telegram As Release And Operations Truth

The public channel had roughly 6.5K subscribers and the bot roughly 25K monthly users in the observed public surfaces. It functions as the freshest operational source:

- DDoS/outage reports and compensation;
- price changes;
- rapidly changing server availability;
- setup-client changes after App Store removals/reuploads;
- allow-list infrastructure updates;
- promo codes, referrals and raffles.

The channel says users often connect first to a Russian entry server and traffic then exits abroad, and claims this reduces exposure to possible foreign-traffic charging. It also claims large allow-list IP churn. These are provider statements, not independently verified architecture/performance facts.

## Ownership, Privacy And Contract Gaps

The current responsibility chain spans two public entities:

- the website/store identify Armenian **KOSMOS CONNECTION, LLC**, registered in August 2025;
- the legacy website user agreement names Russian sole proprietor **ИП Лисецкая Алина Михайловна** as seller and applies Russian law.

The site-hosted Armenian registry extract confirms formation and no termination information at issuance in August 2025. It is historical evidence, not current July 2026 status. The Armenian government’s current registry search is dynamic and could not be completed in this pass, so present status remains `BLOCKED_BY_ACCESS`. Personal registry identifiers are excluded.

An exact identifier lookup in the official Russian Federal Tax Service EGRUL/EGRIP service returned the named sole proprietor. A fresh electronic extract generated on 22 July 2026 contained the registration record and no termination section or inactive-record marker. Current Russian IP status is therefore recorded as `PASS`; the downloaded extract remains in the sensitive temporary area rather than the repository.

The 4 April 2024 user agreement describes a Telegram-bot/system product for legal entities, lets the provider change or terminate the service unilaterally, and gives no uptime guarantee. It predates the Armenian LLC, consumer native apps, email accounts and current tariffs. The legal surface therefore does not cleanly map developer, seller, data controller, billing and support responsibility.

The privacy policy admits collection of email, optional name/Telegram identity, payment metadata and last four card digits, support/device data, feature usage, website logs, crash diagnostics, analytics and advertising measurement. It separately promises not to keep user IPs, browsing history, connection metadata, traffic contents or DNS requests.

Both Google Play and Apple declare **no data collected**, while the policy and working email/account/cabinet product require several categories of personal data. The Android manifest also includes Firebase Analytics/Measurement, Crashlytics, Sessions, Installations, DataTransport, advertising ID/AdServices attribution and Install Referrer components. Presence of an SDK is not proof every event is transmitted, but the store declarations are not credible as written.

Other policy concerns:

- no explicit effective/last-updated date was observed;
- third-party payment/support/email/analytics/advertising providers are described by role, without a clear processor list;
- payment data may be retained for ten years, marketing consent for three years after subscription, support tickets for three years and support-device data up to six months;
- data may be transferred to the US/EU;
- the government-request standard relies on whether a country is “generally recognized as democratic”, which is vague and operationally weak;
- under-18 exclusion conflicts with 3+/4+ store ratings and an account flow with no age gate.

Detailed sources and contradictions: [website, store, legal and channel notes](raw/kosmos-vpn/2026-07-22/documents/website-store-legal-and-channel-notes.md).

## Technical Architecture

The Android app is native Kotlin/Jetpack Compose rather than Flutter. It targets Android 15 (`targetSdk 35`), requires Android 12L (`minSdk 32`) and uses a non-exported foreground `VPNService`. A custom `kosmosvpn:` deep link reaches the main activity.

The bundle contains a large Go `libbox` networking engine and capabilities associated with sing-box/sing-tun, Xray/v2ray-core, WireGuard, VLESS, VMess, Trojan, Hysteria/Hysteria2, TUIC, Shadowsocks, Reality, QUIC, ECH, SOCKS5, Clash/MetaCubeX and Tailscale/DERP. These are bundled engine capabilities, not proof every protocol is exposed or enabled commercially.

CameraX/ML Kit support the TV QR flow. A bundled MP4 supplies the moving space background. Google Play PairIP licensing is present and Android backup is enabled. The package requests notification, camera, boot, network/Wi-Fi, wake-lock, battery-optimization, advertising-ID and attribution-related capabilities.

Detailed redacted evidence: [static package notes](raw/kosmos-vpn/2026-07-22/logs/static-package-notes.md).

## What POKROV Should Copy

- A visual world that is recognizable from one frame: moving cosmic texture, gradient wordmark and orbital connection state.
- Email OTP that goes from zero account to working home in one short flow.
- A one-control native client backed by a richer web cabinet instead of cramming promotions into the VPN screen.
- Real Android TV QR pairing with permission requested only when the feature is used.
- A live incident/status channel with automatic compensation and concrete recovery instructions.
- Portable access through a maintained matrix of first-party and third-party clients.
- Cabinet primitives for device management, Telegram binding, referrals, promo codes and service status.

## What POKROV Should Not Copy

- Claiming “always works” while publishing outage compensation and support-access incidents.
- Stale accessibility semantics that report a connection when no tunnel exists.
- A clickable Apple TV row with no observable result.
- Registration without terms/privacy/age context.
- Redirecting unauthenticated support into login.
- Conflicting prices, compensation days, server lists and product descriptions across site, stores, app and Telegram.
- Store “no data collected” declarations contradicted by the privacy policy and bundled measurement stack.
- Placeholder foreign identity details for App Store region changes.
- An obsolete B2B/Telegram agreement attached to a current consumer native product.
- Raffles and urgency as a substitute for a clear, trustworthy subscription contract.

## Current Flow Health

| Flow | Health | Evidence / blocker |
| --- | --- | --- |
| Cold launch → email | **PASS** | Clear branded entry; no legal or age context |
| Email → code → native home | **PASS** | Owner-authorized registration completed; no code/address retained |
| New account → active access | **PASS WITH ATTRIBUTION CAVEAT** | Access worked without purchase, but cabinet attributes bonus time to current outage compensation rather than a documented standard trial |
| Home → server selector | **PASS** | 11 countries plus automatic fastest; no policy-promised jurisdiction warning |
| First connect → real tunnel | **PASS** | Notification and Android VPN consent shown; `tun0`, route and DNS checks passed |
| Disconnect → tunnel removed | **PASS / ACCESSIBILITY FAIL** | `tun0` absent, but semantics still announce “Подключено” |
| Android TV → QR scanner | **PASS** | Contextual camera permission and dedicated scanner |
| Apple TV handoff | **FAIL IN OBSERVED SESSION** | Clickable row produced no visible state or destination |
| Public support → assistance | **PARTIAL** | Logged-out route redirected to login; signed-in route reused cabinet relay |
| Settings → authenticated cabinet | **PASS** | Subscription, devices, status, referrals, raffles, Telegram and marketing controls mapped; sensitive identity excluded |
| Cabinet → connect/setup | **PARTIAL** | Observed blank/transient state after CTA |
| Current Android release | **PASS** | Installed 1.3.3 matches current Play line |
| Current Russian sole-proprietor status | **PASS** | Exact official FNS EGRIP lookup and same-day extract; personal registry data excluded |
| Current Armenian entity status | **BLOCKED_BY_ACCESS** | Official 2025 extract retained as historical proof; current dynamic registry lookup did not complete |

Final teardown: Космос, Chrome and Google Play were force-stopped. All sixteen competitor processes were absent and `tun0` did not exist before moving on. No purchase, rating/review, referral, support message, Telegram bot action or public post was submitted.

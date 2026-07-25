# GnuVPN — Mobile App Competitor Profile

**Snapshot date:** 2026-07-22<br>
**Status:** `DEEP PASS COMPLETE WITH BLOCKERS` — isolated onboarding, language, auth/registration, automatic trial, signed-in product, country list, split tunneling, protocols, settings/privacy controls, custom servers, eSIM cross-sell, support, live tunnel, pricing, stores, release cadence, public help, legal/privacy and redacted static package surfaces captured; authoritative current Portuguese company status, Huawei listing metadata and one Russian-checkout currency label remain blocked/unverified<br>
**Android package:** `com.gnu.vpn`<br>
**Installed version:** 1.8.7 (`b673`)<br>
**Install source:** Google Play

Evidence root: [`raw/gnuvpn/2026-07-22/`](raw/gnuvpn/2026-07-22/)

The interrupted-session `01-launch` artifact remains provenance-only. Accepted current-session evidence begins with `02-isolated-launch`.

## First-Run Sequence

The app opens on a purple globe splash and then immediately requests Android notification permission before explaining the product. The request was granted for controlled connection testing.

Three full-screen onboarding slides claim:

1. **«100% гарантия возврата денег»** and trying the VPN without risk;
2. up to five devices simultaneously;
3. full protection/features across all devices with one account.

The third slide offers both **Начать** and **Анонимно**. Onboarding is visually consistent—purple space imagery, gazelle/shield mark, large lifestyle artwork—but copy is generic and the first meaningful interaction is a permission prompt.

Evidence: [first benefit](raw/gnuvpn/2026-07-22/screenshots/04-onboarding-1.png), [five devices](raw/gnuvpn/2026-07-22/screenshots/05-onboarding-2.png), [account/anonymous choice](raw/gnuvpn/2026-07-22/screenshots/06-onboarding-3.png).

## Languages

The first-run language sheet exposes ten languages: Chinese, English, French, Hindi, Indonesian, Filipino, Portuguese, Russian, Spanish and Ukrainian.

Evidence: [language sheet](raw/gnuvpn/2026-07-22/screenshots/07-language-picker.png), [lower language list](raw/gnuvpn/2026-07-22/screenshots/08-language-picker-lower.png).

## Authentication And Registration

**Начать** opens two tabs:

- registration with email and password;
- sign-in with email/password plus **Забыли пароль?**.

There is also a repeated **Анонимно** escape route. No social login, legal consent, privacy link, age check, password requirements or email-verification explanation is visible on the registration screen.

The owner-authorized Gmail address was registered with a transient generated password. The app created and signed in the account immediately and returned to the originally requested product route; no email code or in-app verification step appeared. Credentials and the address are not retained in the worktree.

Registration automatically activated a free trial expiring seven calendar days later; the account screen displayed six remaining days because it rounds the partial first day down. The account explicitly said the email was **not confirmed**, yet VPN access worked. There was no forced verification route. Account actions include logout and permanent account deletion; neither was used.

Two immediate transactional emails came from the official domain: an activation notice and a welcome message. They confirmed the expiry date, marketed a money-back guarantee and introduced a referral loop in which both inviter and friend receive points redeemable against any GnuVPN plan. The emails did not ask for email verification.

Evidence: [registration](raw/gnuvpn/2026-07-22/screenshots/09-start-route.png), [login](raw/gnuvpn/2026-07-22/screenshots/10-login.png).

## Unauthenticated Home

Leaving auth opens the actual application shell rather than closing it. The home exposes:

- power toggle and disconnected state;
- automatic/optimal region selector;
- an auth-required banner and **Купить** CTA;
- **VPN Split Tunneling**;
- hamburger menu and account/auth icon;
- bottom tabs for VPN, `eSIMSecure` and settings.

Tapping **Купить** while logged out returns to authentication; pricing is not visible before account creation. This adds friction to plan comparison.

Evidence: [unauthenticated home](raw/gnuvpn/2026-07-22/screenshots/11-home-anonymous.png), [buy-to-auth route](raw/gnuvpn/2026-07-22/screenshots/18-buy-route.png).

## Region Selector

The unauthenticated selector is fully browseable and contains **Оптимальная** plus 59 countries. It uses a flat alphabetical list with flags and no search, favorites, city, latency, streaming/task category or free/premium distinction.

Countries observed: Albania, Argentina, Armenia, Australia, Austria, Belgium, Brazil, Bulgaria, Canada, Chile, Costa Rica, Croatia, Cyprus, Czech Republic, Denmark, Estonia, Finland, France, Georgia, Germany, Greece, Hong Kong, Hungary, Iceland, India, Indonesia, Ireland, Israel, Italy, Japan, Kazakhstan, Latvia, Lithuania, Luxembourg, Mexico, Moldova, Netherlands, Nigeria, Norway, Poland, Portugal, Romania, Russian Federation, Serbia, Singapore, Slovakia, Slovenia, South Africa, South Korea, Spain, Sweden, Switzerland, Taiwan, Thailand, Turkey, United Arab Emirates, United Kingdom, USA and Vietnam.

Evidence: [top of list](raw/gnuvpn/2026-07-22/screenshots/12-country-selector-unauth.png), [middle](raw/gnuvpn/2026-07-22/screenshots/13-country-selector-scroll.png), [bottom](raw/gnuvpn/2026-07-22/screenshots/14-country-selector-scroll.png).

## Split Tunneling

After registration, the app returned directly to the split-tunneling route that had triggered auth. The screen’s model is allow-list based: **only selected apps use the VPN**. All 23 installed apps were selected by default (`Через VPN: 23`, `В обход VPN: 0`), with search, select-all/clear and a per-app checkbox.

This is a strong implementation detail: the page states routing semantics explicitly and exposes live counts. The risk is the default—users may assume “split tunneling enabled” means only a small chosen set, while the starting state routes everything.

Evidence: [split-tunneling app picker](raw/gnuvpn/2026-07-22/screenshots/19-split-tunneling.png).

The contextual help makes the rule explicit: uncheck apps that should not use VPN; changes take effect after reconnecting. This is better than leaving split-tunnel semantics implicit.

## Protocol And Connection Strategy

The protocol selector offers:

- Auto;
- OpenVPN;
- SoftEther;
- AmneziaWG.

The built-in recommendation says to use AmneziaWG where internet resources are blocked, SoftEther as an alternative and OpenVPN where there are no restrictions; Auto chooses for the user. This is unusually direct anti-blocking guidance inside settings.

SoftEther has a separate UDP-acceleration option. Help copy says it can improve live streaming, online gaming and VoIP, and should be disabled if the connection becomes unstable.

Evidence: [protocol selector](raw/gnuvpn/2026-07-22/screenshots/30-protocol-selector.png), [anti-blocking guidance](raw/gnuvpn/2026-07-22/screenshots/31-protocol-help.png), [SoftEther UDP explanation](raw/gnuvpn/2026-07-22/screenshots/35-softether-help.png).

## Settings And Default Data Controls

The settings surface exposes:

- split tunneling;
- system-level kill-switch instructions;
- email and push notifications;
- protocol and language;
- whether custom servers appear at the beginning or end of the region list;
- SoftEther UDP acceleration;
- advertising-data collection;
- logging.

Email notifications, push notifications, SoftEther acceleration, advertising-data collection and logging all appeared enabled by default. The advertising tooltip says enabling the control sends **device and user data to Google services** to improve the app and promote it in marketplaces, while simultaneously claiming it is not personal data and naming cookies/device identifiers as examples. Device identifiers and cookies can be personal data under common privacy frameworks; the wording is materially misleading.

Evidence: [settings](raw/gnuvpn/2026-07-22/screenshots/29-settings.png), [settings lower/default toggles](raw/gnuvpn/2026-07-22/screenshots/33-settings-lower.png), [advertising-data explanation](raw/gnuvpn/2026-07-22/screenshots/36-ad-data-help.png).

The kill-switch CTA does not implement an in-app switch. It explains that the feature becomes available after one successful connection and tells the user to enable Android **Always-on VPN** plus **Block connections without VPN** in system settings. This is technically honest, but the primary settings label overstates how direct the action is. No system setting was changed during the audit.

Evidence: [kill-switch instructions](raw/gnuvpn/2026-07-22/screenshots/37-kill-switch-destination.png).

## Custom Servers

The hamburger menu exposes a first-class **Пользовательские серверы** manager. The empty state has one **Добавить сервер** CTA.

Supported imports:

- OpenVPN via required `.ovpn` configuration file; server address is derived/read-only;
- SoftEther via server IP, port, login, password, hub name (`default` prefilled) and optional UDP acceleration.

AmneziaWG is available for GnuVPN-managed servers but not as a custom-server import type in the observed form.

Evidence: [empty custom-server manager](raw/gnuvpn/2026-07-22/screenshots/38-custom-servers.png), [OpenVPN import](raw/gnuvpn/2026-07-22/screenshots/39-add-custom-server.png), [supported custom protocols](raw/gnuvpn/2026-07-22/screenshots/40-custom-server-protocols.png), [SoftEther fields](raw/gnuvpn/2026-07-22/screenshots/41-add-softether-server.png).

## eSIMSecure Cross-Sell

The middle bottom tab is a separate `eSIMSecure` product rather than a small VPN add-on. It has current and inactive/archived eSIM tabs, pull-to-refresh states and a banner promising **double-layer protection with eSIMSecure + GnuVPN**.

LDPlayer was correctly marked incompatible with eSIM. The Learn More action opens the separate `esimsecure.com` storefront, powered by GnuVPN and Yesim. The public hero claims registration without personal data, crypto payment options and “trusted by 1M+ users”; those are marketing claims pending independent/legal verification.

Evidence: [current eSIM state](raw/gnuvpn/2026-07-22/screenshots/25-esim-home.png), [inactive/archived state](raw/gnuvpn/2026-07-22/screenshots/28-esim-inactive.png). The loaded Chrome page capture was quarantined because the browser tab strip exposed unrelated owner context.

## Support And Legal Consent

The in-app feedback form requests email, issue type, subject and a message up to 2,000 characters. Types are **Общий вопрос**, **Ошибка приложения** and **Обратная связь**. Users can attach PNG/JPEG/JPG/PDF/SVG/HEIC/HEIF files and optionally share the application log with developers.

Submission copy says tapping Send constitutes agreement with the GnuVPN privacy policy. The email field was not prefilled from the signed-in account. No message or log was submitted.

Evidence: [support form](raw/gnuvpn/2026-07-22/screenshots/42-support.png), [question types](raw/gnuvpn/2026-07-22/screenshots/43-support-types.png).

The About screen contains version/build, Privacy Policy and Terms of Use destinations.

Evidence: [about/legal hub](raw/gnuvpn/2026-07-22/screenshots/44-about.png).

## Live Tunnel Smoke Test

The free trial permitted a real connection. Android displayed the standard VPN consent sheet; after approval, Auto selected AmneziaWG and an optimal French exit. `tun0` existed and controlled route/DNS checks passed. The connected home displays both the exit VPN IP/location and the user’s current public IP/location side by side. Those raw values were quarantined rather than retained.

Disconnect removed `tun0` and the VPN route. No kill switch was enabled, no custom configuration was imported and no raw endpoint/IP remains in repository evidence.

Evidence: [Android VPN consent](raw/gnuvpn/2026-07-22/screenshots/47-vpn-consent-or-connect.png).

## CTA And Destination Map

| Source action | Destination | Observed result |
| --- | --- | --- |
| Onboarding **Начать** | Registration/login | Email/password tabs; no age/legal/password guidance |
| Onboarding **Анонимно** | VPN shell | Regions/settings visible; connection and purchase require account |
| Logged-out **Купить** | Authentication | Pricing is hidden until auth rather than previewed |
| Region selector | Flat country list | Optimal plus 59 countries; no search/favorites/cities |
| Split tunneling | Installed-app picker | Only checked apps use VPN; all 23 initially checked |
| Kill switch | Android system guidance | Explains Always-on VPN and Block connections without VPN; does not silently change them |
| Protocol help | Contextual modal | Recommends AmneziaWG under blocking, SoftEther fallback, OpenVPN otherwise |
| Custom servers → Add | OpenVPN/SoftEther forms | `.ovpn` import or manual SoftEther credentials; no AmneziaWG import |
| eSIMSecure **Learn more** | `esimsecure.com` | Separate GNUAPP/Yesim storefront; emulator marked incompatible |
| Support | In-app form | Email/type/subject/body, attachments, optional app log; not submitted |
| About → Privacy/Terms | First-party legal pages | Portuguese GNUAPP contract/controller documents |
| Account → Delete | Destructive confirmation flow | Documented by FAQ; deliberately not executed |

## Trial, Pricing And Checkout

Registration produced a seven-day no-card trial without verification. Public web pricing at the snapshot was:

| Term | Total | Advertised monthly equivalent |
| --- | ---: | ---: |
| 1 month | $6.99 | $6.99 |
| 3 months | $17.99 | $5.99 |
| 6 months | $26.99 | $4.49 |
| 1 year | $41.99 | $3.49 |
| 2 years | $66.99 | $2.79 |

The web catalogue also contains a first-month offer and eSIM+VPN bundles. Payment guidance names local/P2P card paths, Visa/Mastercard, PayPal, Apple Pay/Google Pay and crypto including USDT, Bitcoin, TRON and Litecoin. No checkout or payment was initiated.

The onboarding and website advertise a broad **100% money-back guarantee**, but the official FAQ limits it to 3 days for one month, 7 days for six months and 14 days for one year, allows only one refund per customer lifetime, deducts crypto fees and delegates store purchases to store policies. That gap is a conversion tactic with a trust cost.

## Referral And Retention Machine

The referral system is unusually complete for this segment:

- one point equals one US cent;
- a paid new referral yields 10% to the inviter and 30% to the new customer;
- the inviter can earn again on the referred user's renewal, while the referred user receives the 30% only once;
- points can pay for any plan or be transferred to another registered user after email-code confirmation;
- the web cabinet exposes balance/history, invited users, unique link, point transfer and checkout redemption;
- email, push and Firebase In-App Messaging create expiry/promo/review re-engagement surfaces;
- the FAQ promises an in-app and email reminder five days before subscription expiry;
- the eSIMSecure bottom tab is a permanent adjacent-product storefront.

This is worth copying as a lifecycle architecture, not as-is: explicit consent, fraud rules, point expiry/accounting and privacy disclosure need to exist before turning on the same mechanics.

## Distribution And Release Cadence

GnuVPN distributes beyond the two dominant stores:

- Android: direct APK through GitHub Releases, Google Play, Huawei AppGallery and Xiaomi GetApps;
- iOS: Apple App Store;
- Windows and macOS: first-party downloads backed by public GitHub release repositories;
- Linux: public release repository, but effectively dormant since 2023.

Current public versions at the snapshot were Android 1.8.7, iOS 1.8.8, Windows 1.3.9, macOS 1.3.8 and Linux 1.2.8. Android published eight 2026 releases from 29 January through 5 June—roughly every two to four weeks. Apple listed ten updates from 5 January through 3 July, including anonymous access, review prompts, trials, eSIM, push/in-app messaging, AmneziaWG and repeated UI/stability work. Windows had four 2026 releases and macOS three; Linux had none since 2023.

This is a pragmatic release machine: many storefronts, public binary fallbacks and frequent mobile iteration. The GitHub organizations are release shells rather than source transparency, and near-identical Apple notes plus out-of-order Windows tag publication reduce provenance quality.

Important catalogue drift:

- website says iOS 12+, current App Store requires iOS 17.6+;
- Xiaomi copy still says 25 countries/all protocols/no data collection;
- mobile FAQ says 55+ countries and only OVPN/SoftEther;
- PC FAQ says 24+ countries;
- installed Android exposes 59 countries and AmneziaWG.

## Store Position And Recommendation Graph

Google Play showed 1M+ installs, a roughly 4.5 rating around 22K reviews depending on locale/time, in-app purchases, a June 2026 update and an Independent security review marker. Its recommendation rail included Turbo VPN, JumpJump, Psiphon, Tor Browser, Browsec, Hotspot Shield, Seed4.Me and NordVPN across observed locales.

Apple showed 4.5/5 from 96 ratings, 18+, advertising, in-app purchases, ten languages and US subscription prices matching the website's $6.99 month/$41.99 year. Its recommendation rail exposed SwizzVPN, Stark VPN, VPN 365, Nive, VPN Pro, VPN – Super Smart Proxy, Rapid VPN, Uranus VPN Unlimited, Light VPN Proxy and FREE VPN APP.

Review quality is weak product evidence. Four featured Apple five-star reviews share one date, formulaic keyword-heavy copy and the same later developer reply; one praises Pakistan although it is absent from the current Android list. A visible Play review explicitly says the author had not used the app and the rating should not influence others. Record these as integrity warnings, not proof of manipulation.

## Legal Entity, Privacy And Security Claims

Terms, Privacy Policy and both stores name **GNUAPP UNIPESSOAL LDA** in Portugal; Portuguese law/courts apply subject to mandatory consumer law. A current exact-company certificate from the official Portuguese registry was not obtained, so present registry standing remains `BLOCKED_BY_ACCESS`, not inferred from live store listings.

The contract is 18+, but Android registration has no age gate and Google Play is rated Everyone; Apple's 18+ rating is aligned. The privacy policy names the Portuguese company as controller, then refers to an unnamed Saint Vincent and the Grenadines headquarters/registration and calls the Portuguese company an affiliate. The controller/entity chain needs cleanup.

The privacy story contradicts itself across nearly every surface:

- the policy says no browsing/traffic/DNS contents but does collect account/payment information, connection date, selected VPN location, approximate origin country/ISP and aggregate traffic;
- the FAQ says no user data, no connection logs, no personal information and no personal accounts;
- the live account and referral system necessarily store email, password hash, subscriptions, invited-user relationships and point history;
- the policy says diagnostics are opt-in at activation, but no activation prompt appeared and Logging was on by default;
- Advertising data collection was on by default and its tooltip admits sending device/user data to Google while calling cookies/device identifiers non-personal;
- Google Play says no data collected while also listing shared categories; Apple declares tracking, linked email, location, purchases, usage and diagnostics;
- the APK embeds Firebase analytics/messaging/config, Adjust and Facebook integrations; the website loads Google Tag Manager, Meta Pixel and Firebase/Google analytics code.

The official App Defense Alliance directory does confirm an approved **Legacy MASA** assessment for this package and organization, issued 2026-02-11 and expiring 2027-02-11. It exposes no formal certificate/report, tested version or exact “Level 2” field. GnuVPN's FAQ goes too far when it says the badge proves full Google Play compliance and that declared data practices are accurate and followed.

## Help Centre Quality

The current English help centre has 43 linked detail pages covering referrals, onboarding/payment, VPN concepts, WebRTC/DNS/IP checks, locations, mobile/PC setup, public proxy/speed/IP tools, refunds, security, account deletion/login, expiry, support, Play verification and eSIM setup.

Its strongest material is operational: exact referral economics, point-transfer confirmation, account deletion, expiry alerts, payment alternatives and device-level eSIM steps. Its weakest material is implementation truth. It says email confirmation and payment precede use, only OVPN/SoftEther exist, Recent/Favorites/server selection exists and no accounts/data/logs exist—each contradicted by the audited build or policy. A former search-indexed anti-blocking guide describing Chameleon and legacy protocols now returns 404; there is no Chameleon control in Android 1.8.7.

Detailed page-by-page grouping and contradiction notes: [website/store/legal/channel notes](raw/gnuvpn/2026-07-22/documents/website-store-legal-and-channel-notes.md).

## Android Package Architecture

The installed app is a large Qt 6/QML hybrid: a 24.1 MB base, 55.0 MB ARM64 split and native OpenVPN, SoftEther and WireGuard/AmneziaWG engines. It targets Android SDK 36, disables backup and uses `QUERY_ALL_PACKAGES` for per-app split tunneling.

Static evidence also shows Google Play Billing, Firebase Cloud/In-App Messaging, Remote Config, analytics/measurement, Facebook automatic app events/advertiser-ID collection, Adjust, Install Referrer and advertising-ID/AdServices permissions. Production manifests contain stage/test app-link hosts alongside first-party and attribution deep links. SDK presence alone does not prove transmission, but it materially expands what privacy copy must disclose.

Redacted detail: [static package notes](raw/gnuvpn/2026-07-22/logs/static-package-notes.md).

## What POKROV Should Borrow

1. **Anonymous exploration with intent return.** Let users inspect regions/settings before auth, and after auth return them to the exact route that triggered it.
2. **A real no-card trial.** It removes checkout friction and let the connection prove itself; show exact start/end/remaining time and verification status honestly.
3. **Protocol guidance tied to failure conditions.** “Blocked → AmneziaWG; fallback → SoftEther; ordinary network → OpenVPN; Auto if unsure” is much better than protocol names alone.
4. **Explicit split-tunnel semantics.** State whether checked apps go through or around VPN, show both counts and explain when changes apply.
5. **Honest OS kill-switch handoff.** Deep-link to Android settings only after explaining Always-on VPN and block-without-VPN.
6. **Release resilience.** Store + direct signed artifacts + visible version history, with one canonical current-version table.
7. **Lifecycle architecture.** Trial activation, expiry reminders, referral credit, review timing and optional cross-sell can form one coherent lifecycle—not scattered promos.
8. **First-class support evidence.** Issue type, attachments and optional logs are useful if logs are previewable/redactable and consent is not bundled into Send.

## What POKROV Should Not Copy

1. Permission request before value.
2. Pricing hidden behind authentication.
3. Working unverified accounts while documentation insists confirmation is mandatory.
4. Logging, advertising data, email and push enabled by default without a clear first-run choice.
5. “100% refund” hero copy backed by short, plan-specific, one-time windows.
6. Absolute no-data/no-logs language contradicted by accounts, policies, stores and SDKs.
7. Unsynchronized protocol, country, OS requirement and product-version copy.
8. A legal 18+ contract paired with an Everyone store rating and no age gate.
9. Formulaic reviews/testimonials as trust proof.
10. “Double encryption” eSIM marketing without a technical threat model.
11. Displaying the user's raw current public IP beside the exit IP by default.
12. Treating a binary GitHub repository as open-source transparency.

## Current Flow Health

| Flow | Health | Evidence / next check |
| --- | --- | --- |
| Cold launch → onboarding | **PASS WITH PERMISSION-TIMING ISSUE** | Notification permission precedes product context |
| Onboarding → anonymous shell | **PASS** | VPN browsing/settings shell available; connection gated |
| Start → registration/login | **PASS** | Clear tabs and password recovery; legal/age/password context absent |
| Email/password registration | **PASS WITH TRUST GAP** | Immediate account/sign-in and working seven-day trial despite account stating email is unconfirmed; credentials quarantined |
| Logged-out Buy → pricing | **BLOCKED BY AUTH** | Returns to login instead of showing plans |
| Region browsing | **PASS** | Optimal plus 59 countries available before auth |
| Split tunneling | **PASS / DEFAULT NEEDS CARE** | Explicit per-app model and counts; all apps selected initially |
| Protocol choice | **PASS** | Auto/OpenVPN/SoftEther/AmneziaWG plus in-context anti-blocking guidance |
| Custom server import | **PASS TO EMPTY FORMS** | OpenVPN file and SoftEther credential paths mapped; no config imported |
| eSIMSecure | **PASS TO PUBLIC CROSS-SELL / DEVICE BLOCKED** | Emulator correctly marked incompatible; separate site destination confirmed |
| Support | **PASS TO UNSUBMITTED FORM** | Types, attachment formats, optional logs and privacy consent mapped |
| Connect/disconnect | **PASS** | AmneziaWG tunnel, route and DNS present; clean removal on disconnect |
| Pricing/paywall | **PASS TO PUBLIC PLAN CATALOGUE / NO PAYMENT** | Trial, web plans, payment methods and refund rules reconciled; no purchase made |
| Referral/cabinet | **PASS VIA OFFICIAL DOCUMENTATION AND EMAIL** | Economics, point transfer and cabinet surfaces mapped; no referral was shared or redeemed |
| Account deletion | **MANUAL_OWNER_TEST / NOT RUN** | Destructive flow documented but deliberately not executed |
| Store/release map | **PASS WITH METADATA BLOCKER** | Play, Apple, Xiaomi, GitHub/direct cadence mapped; Huawei destination resolved but current metadata did not render |
| Legal entity status | **BLOCKED_BY_ACCESS** | Contracting entity mapped; authoritative current Portuguese status certificate not obtained |
| Help centre | **PASS WITH MAJOR DRIFT** | All 43 current English detail pages grouped and checked against Android behaviour |
| Security review | **PARTIALLY VERIFIED** | Official approved Legacy MASA record; no public report/exact Level 2 field/tested build |

Current isolation state at the last checkpoint: GnuVPN was force-stopped after testing, Chrome was closed and `tun0` was absent.

# AdGuard VPN — Mobile App Competitor Profile

**Status:** `DEEP PASS COMPLETE WITH BLOCKERS — NATIVE PRODUCT, GROWTH, FAILURE PATH, STORE, WEB, LEGAL, RELEASE AND STATIC SURFACES CAPTURED`<br>
**Snapshot date:** 2026-07-22<br>
**Android package:** `com.adguard.vpn`<br>
**Installed version:** `2.16.65` (`versionCode 348464`)<br>
**Install source:** Google Play<br>
**Runtime rule:** launch only after the previous competitor is force-stopped and `tun0` is absent.

## Audit Checkpoint

Lagom was fully torn down first; AdGuard launched alone with no `tun0`. The cold start routes from `SplashActivity` to `LoginActivity` and opens with a full-screen illustrated consent gate.

Observed first-launch copy and choices:

- “Привет!”;
- claim that AdGuard collects the minimum data needed for its sites/apps and does not transfer it to anyone;
- mandatory checkbox accepting the AdGuard VPN License Agreement and Privacy Policy;
- separate optional checkbox for anonymized usage data and crash reports;
- Continue remains disabled before mandatory acceptance.

This is materially better consent structure than bundling telemetry into the service contract: analytics is off by default and independently selectable. The absolute “никому их не передаём” claim will be checked against the linked policy, SDKs and store declarations.

Evidence: [first launch](raw/adguard-vpn/2026-07-22/screenshots/01-isolated-launch.png), [UI tree](raw/adguard-vpn/2026-07-22/ui/01-isolated-launch.xml).

## Auth And Product Tour Checkpoint

The mandatory-only consent path was used; optional usage/crash reporting stayed disabled. Its explainer limits voluntary analytics to screen names, button names and session identifiers, says it stays inside AdGuard, uses no third-party advertising/analytics SDK and can be disabled later. Evidence: [usage-data explainer](raw/adguard-vpn/2026-07-22/screenshots/02-usage-data-explainer.png).

Authentication runs in an `auth.adguard.io` Chrome Custom Tab and offers email/password, password recovery, Apple, Google and Facebook. Owner-authorized Google sign-in succeeded and requested only the email address in the visible consent. Account identifiers and consent screenshots remain outside the worktree.

The native tour has four steps:

1. proprietary **TrustTunnel** protocol, positioned as fast and difficult to fingerprint as VPN traffic;
2. per-site and per-app exclusions;
3. an absolute “we do not collect or transfer data” slide;
4. forced Unlimited upsell emphasizing unrestricted speed.

The fourth screen has only “Улучшить”; reaching the free product requires backing out of the web offer and then the native upsell. Evidence: [protocol](raw/adguard-vpn/2026-07-22/screenshots/06-onboarding-protocol.png), [exclusions](raw/adguard-vpn/2026-07-22/screenshots/07-onboarding-next.png), [privacy claim](raw/adguard-vpn/2026-07-22/screenshots/08-onboarding-next.png), [upsell](raw/adguard-vpn/2026-07-22/screenshots/09-onboarding-next.png).

## First Offer And FAQ Checkpoint

The “Improve” action opens a full AdGuard website offer in a Chrome Custom Tab:

| Plan | Displayed price | Billing note |
| --- | ---: | --- |
| 1 month | USD 11.99/month | VAT excluded; no refund according to FAQ |
| 1 year | USD 3/month | 75% off; billed annually; 30-day refund guarantee |
| 2 years | USD 2.99/month | 75% off; billed every two years; marked best choice |

The timer says the 75% site offer ends 2026-07-23. Paid value is all/70 locations, unlimited speed and traffic, up to ten simultaneous devices and a free Personal AdGuard DNS subscription. No checkout was entered.

FAQ answers captured from the offer:

- cards including Russian cards, Yandex Pay, PayPal and cryptocurrency;
- only annual subscriptions receive the 30-day refund; monthly is non-refundable;
- additional purchases on the same email stack their terms;
- questions/refunds route to the public support email;
- paid tier explicitly says 70 locations, unlimited speed/traffic, ten simultaneous devices and Personal AdGuard DNS;
- sales are promoted through the blog, mailing list, Facebook, Instagram, Telegram and X; annual is presented as the best saving;
- an account can be used on any number of devices, with two simultaneous VPN connections free and ten paid.

The page has visible copy-quality defects (“10 устройств устройств” and “написать вам на”). Evidence: [offer](raw/adguard-vpn/2026-07-22/screenshots/10-first-paywall.png), [payment FAQ](raw/adguard-vpn/2026-07-22/screenshots/12-faq-payment-methods.png), [FAQ UI trees](raw/adguard-vpn/2026-07-22/ui/).

## Free Home Checkpoint

After dismissing a second pressure prompt to enable notifications “for stable VPN operation”, the live free home showed:

- 4.0 GB remaining, refreshing in 30 days;
- speed explicitly limited;
- Germany / Frankfurt selected with an asserted 4 ms latency;
- connect CTA plus “How to keep the connection?” help;
- bottom navigation for Home, Exclusions, Subscription and Settings.

No notification permission was granted. Evidence: [notification prompt](raw/adguard-vpn/2026-07-22/screenshots/14-free-home.png), [free home](raw/adguard-vpn/2026-07-22/screenshots/15-free-home.png).

The quota screen explains the acquisition loop behind the free tier: installation grants 1 GB, and adding a new device grants a one-time additional 1 GB. The cross-device action opens AdGuard's product catalog. The catalog covers Windows, macOS, iOS, Android, a browser extension, Linux, routers, Android TV, Apple TV, Xbox, PlayStation and Chromecast. Its wider ecosystem promotes AdGuard DNS, AdGuard Mail, Temp Mail, Wallet, an affiliate program, promotions, a “help spread AdGuard” program, beta testing, version history, service status, media assets and a transparency report. Account-specific captures stay outside the repository.

## Locations And Exclusions Checkpoint

The location catalog changed remotely during the same session: the first sheet said **80 locations** and included South Africa / Johannesburg, while a later reload said **79** and that location had disappeared. The three visibly free choices were Germany / Frankfurt, Sweden / Stockholm and Finland / Helsinki, all marked “speed limited”. Choosing Japan routed to the Unlimited upsell, so the full list is a paid catalog rather than a list of free endpoints. Search, favourites and virtual-location labels are built in; Mumbai, Shanghai and Moscow were explicitly marked virtual.

The captured paid catalog spans Germany (Frankfurt, Berlin), Sweden, Finland, Australia, Austria, Argentina, Belgium, Bulgaria, Brazil, the UK (London, Manchester), Hungary, Vietnam, Hong Kong, Greece, Denmark, Egypt, Israel, India, Indonesia, Ireland, Spain (Barcelona, Madrid), Italy (Milan, Palermo, Rome), Kazakhstan, Canada (Vancouver, Montreal, Toronto), Cyprus, China, Colombia, Latvia, Lithuania, Luxembourg, Mexico, Moldova, Nepal, Nigeria, the Netherlands, New Zealand, Norway, the UAE, Peru, Poland, Portugal, Russia, Romania, 12 US cities, Serbia, Singapore, Slovakia, Thailand, Taiwan, Turkey, Ukraine, the Philippines, France (Marseille, Paris), Croatia, Czechia, Chile, Switzerland, Estonia, South Korea and Japan. Evidence: [location sheet](raw/adguard-vpn/2026-07-22/screenshots/19-locations-open.png), [lower catalog](raw/adguard-vpn/2026-07-22/screenshots/20-locations-lower.png), [paid-location result](raw/adguard-vpn/2026-07-22/screenshots/21-japan-selection-result.png).

Exclusions are two independent builders, one for domains and one for installed apps. Each defaults to “VPN everywhere except these entries” and can be inverted to “VPN only for listed entries”. No mode was changed and both lists were verified empty after capture.

The domain builder supports manual entry, search and curated presets:

| Group | Presets captured |
| --- | --- |
| Social networks | Facebook, Flickr, Instagram, Kuaishou/Kwai, LinkedIn, Pinterest, Reddit, Snapchat, TikTok, Tinder, Tumblr, VK |
| Messengers | Discord, Facebook Messenger, Kakao Talk, Kik, Max, QQ, Signal, Telegram, WeChat, WhatsApp |
| Video | Bilibili, Disney Plus, Douyin, HBO, Hulu, Kinopoisk, Netflix, Okko, Rutube, Vimeo, YouTube |
| Music | Deezer, Last.fm, Pandora, SoundCloud, Spotify |
| Games | Electronic Arts, Epic Games, GOG, Origin, PlayStation, Rockstar Games, Steam, Twitch, Ubisoft, Xbox |
| Search | 2GIS, Baidu, Bing, DuckDuckGo, Google, OpenAI, Yahoo, Yandex |
| Work | Adobe Creative Cloud, Alipay, Atlassian, DiDi, GitHub, GitLab, Gosuslugi, HeadHunter, JetBrains, Mail.ru, Microsoft Office, Sberbank Online, Skype, Slack, T-Bank, Zoom |
| Stores | Alibaba, AliExpress, Amazon, Avito, Craigslist, eBay, Etsy, JD.com, Meituan, Ozon, Pinduoduo, Wildberries |

The app builder exposes search plus the complete installed-app and system-app inventory. Nothing was added. Evidence: [clean exclusions](raw/adguard-vpn/2026-07-22/screenshots/35-exclusions-clean.png), [app exclusions](raw/adguard-vpn/2026-07-22/screenshots/36-app-exclusions.png), [app picker](raw/adguard-vpn/2026-07-22/screenshots/37-app-picker.png), [games](raw/adguard-vpn/2026-07-22/screenshots/28-games-presets.png), [search](raw/adguard-vpn/2026-07-22/screenshots/30-search-engine-presets-lower.png), [work](raw/adguard-vpn/2026-07-22/screenshots/32-work-presets-lower.png), [stores](raw/adguard-vpn/2026-07-22/screenshots/34-store-presets-lower.png).

## Settings And Technical Controls Checkpoint

General settings expose launch at boot (enabled), DNS, Kill Switch, theme, voluntary telemetry (disabled) and an Advanced section. Theme choices are System, System Dynamic, Light and Dark; System is selected.

Built-in DNS choices are Standard, AdGuard DNS, AdGuard DNS Family, AdGuard DNS Unfiltered, Google DNS, Cloudflare DNS, two Cloudflare Family modes, OpenDNS, OpenDNS Family Shield and Quad9, plus a custom DNS server. A knowledge-base button opens AdGuard's large “Known DNS providers” catalog. The emulator had no Private DNS configured, although the DNS screen initially displayed a generic warning to disable it. Evidence: [general](raw/adguard-vpn/2026-07-22/screenshots/41-general-settings.png), [DNS](raw/adguard-vpn/2026-07-22/screenshots/42-dns-settings.png), [DNS lower](raw/adguard-vpn/2026-07-22/screenshots/43-dns-settings-lower.png).

Advanced controls are unusually broad:

- operating modes: full-device VPN, local SOCKS5 proxy, or integration mode for simultaneous use with AdGuard;
- proprietary protocol selection: Automatic, an HTTP/2 transport described as hard to detect, or an experimental QUIC transport;
- post-quantum cryptography toggle, disabled by default;
- Standard, Extended and Extreme logging levels, with battery/performance warnings for the latter two;
- log/system-info export and a local diagnostics screen;
- low-level Wi-Fi gateway routing, PCAP of TUN interfaces, watchdog/alarm permission, preferred IP version, IPv4/IPv6 exclusion ranges, IPv6 interface, MTU (default 9000), excluded UIDs/apps and SOCKS5 port (default 1080).

The diagnostics screen directly exposes active VPN/auth tokens and offers a one-tap copy action. Their values and all raw diagnostic captures are quarantined outside the repository. This is a significant supportability-versus-secret-exposure trade-off. Evidence: [advanced](raw/adguard-vpn/2026-07-22/screenshots/47-advanced.png), [operation modes](raw/adguard-vpn/2026-07-22/screenshots/48-operation-mode.png), [protocols](raw/adguard-vpn/2026-07-22/screenshots/50-protocol-options.png), [logging](raw/adguard-vpn/2026-07-22/screenshots/49-logging-level.png).

Kill Switch is not a native toggle. After the first connection attempt, its page instructs the user to open Android VPN settings, enable Always-on VPN and “Block connections without VPN”, and warns that app/domain exclusions then stop working. No system setting was changed. Evidence: [Kill Switch instructions](raw/adguard-vpn/2026-07-22/screenshots/61-kill-switch-post-attempt.png).

## Account, Support And External Routes Checkpoint

The free account page says “up to 2 devices simultaneously” and links to Unlimited. Its overflow menu contains Manage account settings, Sign out and Delete account; none was used.

Support contains four routes:

- FAQ -> the Android support center with Technical problem, Subscription problem and How the app works categories;
- Report a bug -> native email/message form; attaching process list, installed apps, memory, CPU, battery and logs is an explicit opt-in and is off by default;
- Suggest a feature -> `surveys.adguard.com`, asking for email or Telegram, feedback type, message, sentiment and mandatory privacy/terms acceptance;
- Rate the app -> the Google Play listing; no rating or review was submitted.

About reports **AdGuard VPN v2.16.1**, copyright 2020–2026, and links to Privacy, EULA, version history, official site and acknowledgements. Privacy is dated 2024-12-23. EULA is dated 2026-04-23 and names AdGuard Software Limited. EULA and official-site actions briefly pass through an insecure `link.adtidy.info` redirect before resolving to the secure official site. The acknowledgements page discloses a broad stack including Symfony, React, Vue, PostgreSQL, Spring, logback-android, BoringSSL, Brotli, nghttp2, Protocol Buffers, Cloudflare quiche and others. Evidence: [support](raw/adguard-vpn/2026-07-22/screenshots/51-support.png), [feature survey](raw/adguard-vpn/2026-07-22/screenshots/53-suggest-feature.png), [about](raw/adguard-vpn/2026-07-22/screenshots/54-about.png), [acknowledgements](raw/adguard-vpn/2026-07-22/screenshots/55-acknowledgments.png).

## Subscription Surface Checkpoint

The native Subscription tab is a four-card carousel with one persistent Improve CTA:

1. unlimited speed;
2. all locations across six continents;
3. unlimited traffic;
4. up to ten devices / family sharing.

The CTA routes to the same web offer described above. Evidence: [subscription](raw/adguard-vpn/2026-07-22/screenshots/56-subscription.png) and the adjacent slide captures.

## Controlled Connection Checkpoint

Android VPN consent was granted. Automatic, explicit HTTP/2 and explicit QUIC were each attempted once against the default free Germany / Frankfurt location. Every attempt initialized the local DNS proxy and began connecting, then failed immediately on TLS certificate hostname verification with an OpenSSL internal error. The UI silently returned to “Disconnected”; no user-facing failure explanation appeared, `tun0` never remained present and DNS/HTTPS/route health could therefore not be tested. Raw logs contain connection material and remain outside the repository. Protocol selection was restored to Automatic, the app was force-stopped and `tun0` was verified absent.

This is runtime evidence for this LDPlayer/network environment, not proof that the production service is globally down.

## Google Play Checkpoint

The live Russian listing on 2026-07-22 showed:

- developer: AdGuard Software Limited;
- rating 3.8 from about 170k reviews (170,445 shown deeper in the page);
- 10M+ downloads, 3+, in-app purchases;
- last updated 2026-06-11;
- release note: a technical stability release with an updated VPN client;
- opt-in beta program; Play warns that usage data will be collected and sent to the developer;
- no visible media carousel in this emulator's installed-app listing.

The full store copy claims a proprietary Russia-optimized protocol, site exclusions, post-quantum cryptography, no ads/tracking/logs/third-party transfer, ten devices and **85+ servers**. That conflicts with the live app's 79/80-location counter and the web paywall's 70-location claim.

Play Data Safety declares no third-party sharing; email is collected for account management; optional crash logs are collected for analytics; data is encrypted in transit; account deletion and a data-deletion request are supported. This is consistent with the default-off telemetry control but narrower than the absolute onboarding/store claim that no data is collected.

Highlighted reviews surfaced recurring payment, desktop activation and mobile-carrier blocking complaints, plus long-term-user praise. A developer reply attributes instability to state blocking and directs users to a VPN support chat. The listing's own-product recommendations are AdGuard DNS (3.1, 100k+), TrustTunnel (4.3, 10k+) and AdGuard Mail / Temp Mail (4.5, 100k+). Public support details are `support@adguard-vpn.com`; the entity block names ADGUARD SOFTWARE LIMITED in Limassol, Cyprus. Evidence: [listing top](raw/adguard-vpn/2026-07-22/screenshots/62-play-top.png), [description](raw/adguard-vpn/2026-07-22/screenshots/70-play-description.png), [Data Safety](raw/adguard-vpn/2026-07-22/screenshots/71-data-safety.png), [support block](raw/adguard-vpn/2026-07-22/screenshots/74-play-support.png).

## Company And Legal Entity Checkpoint

The current first-party controller and seller named across the VPN privacy policy, EULA and Play listing is **ADGUARD SOFTWARE LIMITED**, Limassol, Cyprus. The official company page says it was incorporated on 2009-06-01 and develops the AdGuard blocker, VPN and DNS product family. The Play APK is signed by a certificate whose subject is `Adguard Software Ltd`, which is directionally consistent but is not a company-registry extract.

Three first-party surfaces currently disagree on the address:

| Surface | Address displayed |
| --- | --- |
| VPN privacy policy | Anexartisias and Athinon 79, Nora Court Flat/Office 203-205, Limassol 3004 |
| AdGuard contact page | Anexartesias and Athinon 79, Nora Court Flat/Office 203-205, Limassol 3040 |
| Google Play developer block | Andrea Zakou, Limassol 3095 |

The spelling and postal-code drift should be treated as unresolved public-identity hygiene, not proof of a different operator. A current authoritative Cyprus registry extract was not obtained, so no registration number or live company status is claimed.

Primary sources: [VPN privacy policy](https://adguard-vpn.com/ru/privacy.html), [EULA](https://adguard-vpn.com/ru/eula.html), [company/contact page](https://adguard.com/en/contacts.html), [Google Play](https://play.google.com/store/apps/details?id=com.adguard.vpn).

## Privacy And Data-Flow Checkpoint

The accurate core promise is narrower than the app and store copy: AdGuard says it does not keep VPN-server browsing logs, visited domains or the user's source IP, and does not sell/share personal data. It still processes data required to run accounts, quota and support.

The general policy discloses:

- account email and password hash, with optional separately consented marketing;
- payment processing through Paddle.com Market Ltd and PayPro Global, which may handle email, country, postal code and card data;
- free-tier byte count retained for 90 days and not tied to location;
- a count of active VPN connections for both free and paid concurrency limits;
- optional diagnostics/device data and optional product metrics;
- storage of personal data in AdGuard's own Frankfurt data centre, staff access on a need basis and the standard access/deletion/correction/restriction/objection/portability/withdrawal rights.

The Android-specific notice, dated 2024-08-07, is unusually concrete. Depending on the action it lists email, OAuth provider, OS/app language, app/version/build identifiers, device OS, authorization token and app type. Connecting sends the authorization token. A support report always includes report type, email, authorization token and app/version identifiers; the optional 10 MB log bundle can add settings, exclusions, licence data, current VPN location, logs, device model and OS. Optional crash reporting can include root status, Android ID, memory, screen characteristics, stack trace and recent log lines; AdGuard says those reports stay on its own servers for 30 days and do not use a third-party crash service.

Therefore the onboarding/store wording “we do not collect or transfer data” and “we don’t collect … personal data” is materially over-broad. The defensible version is: **no browsing/activity logs or third-party sale/share; only disclosed account, entitlement, quota and opt-in diagnostic data**. This distinction matters for POKROV copy.

Primary sources: [general privacy policy](https://adguard-vpn.com/ru/privacy.html), [Android privacy notice](https://adguard-vpn.com/en/privacy/android.html), [Play Data Safety](https://play.google.com/store/apps/details?id=com.adguard.vpn).

## Terms, Refund And Account-Lifecycle Checkpoint

The EULA is dated 2026-04-23 and requires Cyprus arbitration for disputes not resolved directly. AdGuard may suspend access immediately for a violation. Account deletion cancels an active subscription; the user must separately ask support for any eligible refund. Account creation also automatically subscribes the user to change/version/feature notices, with an unsubscribe route.

Website-bought one- and two-year subscriptions have a 100% refund window of 30 days; monthly subscriptions are non-refundable. After the window, refunds are discretionary, and upgrades/renewals have no automatic partial refund. The paywall and EULA therefore need to be read together before promising a “30-day guarantee”. Orders/renewals are handled through external processors, and store-bought subscriptions inherit the reseller/store policy.

No purchase, trial, subscription change, account deletion or support submission was performed.

## Release And Distribution Checkpoint

AdGuard publishes separate first-party **Release** and **Beta** histories and links individual fixes/client updates to public GitHub issues. Recent Android production cadence is clustered rather than monthly: 2.11/2.11.1, 2.12/2.12.1, 2.13/2.13.1, 2.14 plus three hotfixes, 2.15 plus two hotfixes, then 2.16/2.16.1. This is a repeated major-release → rapid corrective-release pattern, with many changelogs honestly labelled technical/stability work.

Product evolution visible in that history:

- 2.11 (2025-01-31): shared Android/iOS code to accelerate cross-platform feature work;
- 2.12 (2025-03-20): post-quantum protection and web authentication;
- 2.13 (2025-06-26): saved/favourite locations;
- 2.14 (2025-09-01): dynamic HTTP/2/TLS versus HTTP/3/QUIC selection;
- 2.15 (2025-11-07): VPN-client/stability work;
- 2.16/2.16.1 (2026-04-10 / 2026-06-16): privacy/UI/client foundation and another client/stability update.

The installed package is `2.16.65`, About says 2.16.1, the official history dates 2.16.1 to June 16, while Play says updated June 11. These are observable version/date-lane inconsistencies, possibly caused by staged rollout or separate display/build numbering; the cause was not proven.

Distribution is deliberately redundant: Google Play, a public direct APK, automatic in-app updates, non-Play purchase UI and detailed unknown-source installation instructions, including Samsung Auto Blocker. The website also offers the old v2.11 APK to unsupported systems. Release history says Android 7+ was supported from v2.1. Play has a beta opt-in lane; it was not joined.

Primary sources: [Android release history](https://adguard-vpn.com/en/versions/android/release.html), [Google Play](https://play.google.com/store/apps/details?id=com.adguard.vpn), [official Android download surface](https://adguard-vpn.com/en/adguard-vpn-for-android/overview.html).

## TrustTunnel And Open-Source Checkpoint

AdGuard's proprietary-in-product protocol has now been published as **TrustTunnel**, an Apache-2.0 open-source project originally developed by AdGuard VPN. The public implementation describes HTTPS-like traffic, HTTP/1.1, HTTP/2 and QUIC transports, TCP/UDP/ICMP tunnelling, split tunnelling, custom DNS, system-tunnel and SOCKS5 modes. Endpoint support is Linux/macOS; official clients cover Android, Apple platforms, Windows and Linux. The repository also publishes protocol/configuration/development docs, changelog and release-verification instructions.

This gives AdGuard a strong trust/distribution loop: the consumer app sells “hard to fingerprint”, while the public protocol repo provides auditability, self-hosting and independent/community clients. It does **not** establish that the full AdGuard VPN Android application is open source.

Primary source: [TrustTunnel repository](https://github.com/TrustTunnel/TrustTunnel).

## Static Android Checkpoint

The pulled Google Play artifact is a 51.4 MB universal APK with three DEX files and all four common Android ABI families. Each ABI bundles the proprietary/native VPN client, common JNI and native Sentry libraries. It targets SDK 35 and is signed with APK Signature Scheme v2 by a certificate naming Adguard Software Ltd in Cyprus.

Manifest/product signals line up with the native audit: boot start, VPN service, Quick Settings tile, full installed-app visibility for split tunnelling, exact-alarm/battery controls, Play Billing, deep links for `adguardvpn://` and `sdns://`, Android TV code, WorkManager/Room and a reusable `com.adguard.mobile` kit. Sentry Java/native code is packaged, but auto-init and session tracking are explicitly false in manifest metadata. That SDK presence does not by itself contradict the policy's claim of first-party crash storage.

Two concrete hardening flags deserve review:

1. the global network-security configuration allows cleartext traffic, and an HTTP tracking/redirect hop was actually observed on legal/site navigation;
2. `MegazordService` is exported without a manifest permission, although code-level caller validation was not assessed and no vulnerability is claimed.

`allowBackup=true`, the diagnostics screen's copyable live tokens and the sensitive optional installed-app/support bundle are additional review items. The app declares no location, camera, microphone, contacts or broad storage permission.

Full redacted artifact details: [static summary](raw/adguard-vpn/2026-07-22/static-summary.md).

## Destination And Recommendation Map

| Origin | Destination / result |
| --- | --- |
| Mandatory consent | AdGuard VPN EULA and privacy policy, via browser |
| Sign in / sign up | `auth.adguard.io` Custom Tab; email, Google, Apple, Facebook |
| Improve / paid location / Subscription | AdGuard VPN website paywall |
| Add another device | Cross-platform AdGuard VPN download catalog |
| Known DNS providers | AdGuard knowledge base catalog |
| Manage account | AdGuard account web surface |
| FAQ | Android VPN support centre |
| Report bug | Native form; optional diagnostic attachment |
| Suggest feature | `surveys.adguard.com` contact/sentiment form |
| Rate app | Google Play listing; no review action taken |
| Developer support reply | AdGuard VPN support chat shortlink |
| Store's own-product graph | AdGuard DNS, TrustTunnel, AdGuard Mail / Temp Mail; wider developer shelf also surfaces Content Blocker and sometimes Wallet |
| Dynamic Play “similar apps” graph | Changed by locale/session; observed Windscribe, PrivadoVPN, ExpressVPN, v2RayTun, Octohide, Seed4.Me, Tor Browser Alpha, AVG Secure VPN, Proton VPN, NetGuard, IVPN and Super VPN |

The recommendation graph is not stable enough to treat as a canonical partnership list. It is useful as evidence that Google places AdGuard between mainstream privacy suites, anti-blocking utilities and free proxy/VPN products.

## Product And Design Synthesis

### What is genuinely strong

- The free home tells the user exactly what remains, when it refreshes and why speed is limited.
- Per-domain and per-app exclusions are independent, invertible and supported by a large curated preset library. This is the most reusable product idea in the app.
- Protocol, DNS, operating mode, post-quantum and low-level tunnel controls create an expert layer without cluttering the primary home screen.
- TrustTunnel turns a technical differentiator into a public protocol, audit surface and acquisition product.
- Release notes expose real bug IDs and client versions instead of only generic marketing copy.
- Cross-device quota rewards, Personal DNS bundling and the wider AdGuard product shelf make the VPN part of an ecosystem rather than a single-purpose utility.

### What should not be copied

- A forced upsell with no visible “continue free” action at the end of onboarding.
- The second notification-pressure dialog implying notifications are required for stability.
- Absolute “no collection” wording that conflicts with the company's own precise policy.
- Silent connection failure: all three protocols returned to “Disconnected” without actionable error copy.
- Four simultaneous server-count stories: 70 on paywall, 79/80 in the live catalog and 85+ in Play, with other locale pages historically showing still another number.
- HTTP redirect hops on legal links, globally permitted cleartext and copy defects on a security product's checkout.
- A diagnostics surface that prints active tokens directly to the screen/clipboard.

### POKROV adaptation

Build the same **layering**, not a visual clone:

1. Keep Home brutally simple: state, location, connect, quota/plan and one visible failure reason.
2. Make routing a separate power surface with app/domain modes, inversion and curated service packs; label exactly what will and will not go through VPN.
3. Publish one authoritative live capability counter used by app, paywall, store and support docs.
4. State privacy in two levels: a short provable promise plus an immediately reachable exact data table.
5. Use a signed release page with build number, protocol-core version, rollout channel, known issues and rollback/direct-download route.
6. If POKROV exposes diagnostics, redact secrets by construction and create a time-limited support bundle instead of one-tap token copying.
7. Treat connection failure as product UX: user-visible reason, safe retry, protocol fallback result and support bundle link.

## Coverage Limits And Teardown

- The tunnel failed in this LDPlayer/network environment for Automatic, HTTP/2 and QUIC, so no healthy-route, DNS-leak, public-IP or sustained-performance claim is made.
- Store media existed on the public web listing (18 screenshot-image entries in the captured locale), but the installed Play UI exposed no carousel; the native app and listing text were captured, not every locale's marketing artwork.
- No authoritative current Cyprus registry extract was obtained.
- No purchase, beta enrollment, rating, review, support request, account deletion or settings change outside the audited app was performed.
- Protocol was restored to Automatic, AdGuard VPN was force-stopped and `tun0` was absent at handoff.

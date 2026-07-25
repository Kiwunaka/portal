# Proton VPN — Mobile App Competitor Profile

**Snapshot date:** 2026-07-22
**Status:** `DEEP PASS COMPLETE WITH BLOCKERS` — native/free/paid-preview flows, real tunnel, APK/provenance, public funnel, source/release pipeline, legal ownership and trust program mapped; direct 2026 audit-PDF and desktop-Chrome visual pass remain blocked
**Android package:** `ch.protonvpn.android`
**Installed version:** 5.19.66.0 (`versionCode 605196600`)
**Install source:** Google Play

Evidence root: [`raw/proton-vpn/2026-07-22/`](raw/proton-vpn/2026-07-22/)

## Audit Checkpoint

- Start state: all 16 competitor package processes stopped and Android `tun0` absent.
- Only Proton VPN will be active during native exploration; it will be force-stopped before the next competitor.
- Purchase, review, public-post, support-send and destructive account actions are out of scope.
- Account credentials, email codes, current/public IPs, VPN endpoints, provider tokens and raw configurations stay outside the worktree.
- Installed Google Play build targets SDK 35, requires Android 8+ (`minSdk 26`) and launches through `.RoutingActivity`.

The Android app was force-stopped and `tun0` was absent before moving on. Official website, legal/ownership, audit-summary, help architecture and current public claims are mapped below.

## Isolated First Launch

Cold launch reaches Proton's account gateway in under a second rather than a tutorial carousel. The page combines a globe/connection illustration with:

- **«Сертифицированный VPN без журналов»** as a compact external proof chip;
- **«Добро пожаловать в Proton VPN»**;
- **«Продолжить как гость»** as the dominant purple CTA;
- **«Войти»** as a secondary action;
- Terms consent at the bottom.

The guest path is unusually prominent and gives the free product a lower-friction first run than email-first competitors. The Russian subtitle contains an awkward localization defect — **«Просматривайте сайты в приватно»** — in the highest-visibility onboarding copy. Evidence: [isolated welcome](raw/proton-vpn/2026-07-22/screenshots/01-isolated-launch.png).

Selecting guest shows a loader inside the CTA, then immediately invokes Android's system VPN-consent dialog before showing the product shell. Consent was granted for the authorized connection test. A `tun0` interface appeared while provisioning completed; the app remained on the welcome screen for roughly a minute before advancing. Evidence: [guest loading](raw/proton-vpn/2026-07-22/screenshots/02-guest-result.png), [system consent](raw/proton-vpn/2026-07-22/screenshots/03-guest-loaded.png), [post-consent provisioning](raw/proton-vpn/2026-07-22/screenshots/04-guest-after-consent.png).

The next surface is not the free home but an upgrade-onboarding paywall. Its first carousel card says **«Улучшите свою конфиденциальность»** and promises advanced privacy plus high speed with VPN Plus. Visible launch pricing:

- one year: **2,868 RUB**, framed as **−60%** and selected by default;
- one month: **9.90 RUB**, framed as **−98%**;
- automatic renewal: **5,028 RUB/year**;
- primary CTA: **«Получить VPN Plus»**;
- escape hatch: **«Не сейчас»**.

The 9.90-RUB first month is an extreme welcome-offer anchor placed below the default annual selection. No checkout or purchase confirmation was opened. Evidence: [upgrade onboarding](raw/proton-vpn/2026-07-22/screenshots/06-free-upgrade-onboarding.png).

The carousel contains twelve feature cards rather than a short generic sales deck. In order, it sells advanced privacy, all countries, faster web, 4K streaming, NetShield, Secure Core, P2P, ten devices/eight platforms, Tor, split tunneling, reusable connection profiles and advanced network controls. The surface is visually consistent and unusually exhaustive, but the Russian build leaks English copy such as **“Double the encryption”**, and several translations are visibly awkward. Evidence: [country coverage card](raw/proton-vpn/2026-07-22/screenshots/paywall-slide-02.png), [NetShield card](raw/proton-vpn/2026-07-22/screenshots/paywall-slide-05.png), [profile card](raw/proton-vpn/2026-07-22/screenshots/paywall-slide-11.png), [advanced-controls card](raw/proton-vpn/2026-07-22/screenshots/paywall-slide-12.png).

Selecting the monthly option changes the renewal disclosure to **599 RUB/month**. The annual **−60%** badge is mathematically based on the 599-RUB monthly baseline (`599 × 12 = 7,188`), not on the disclosed 5,028-RUB annual renewal. Against renewal, the introductory annual price is roughly 43% lower, not 60%. This is legal discount arithmetic but a material trust-framing issue because the comparison basis is not surfaced beside the badge. Evidence: [monthly selection](raw/proton-vpn/2026-07-22/screenshots/07-monthly-selected.png).

## Free Guest Shell

After **«Не сейчас»**, the free home opens on a map and explicitly says **«Вы не защищены»**. It shows the current country and public IP prominently above a fastest-free-server card, flag strip and connect action. That data is operationally useful but makes ordinary support or marketing screenshots a privacy leak hazard. The raw home screenshot and UI tree were quarantined outside the worktree; no IP or endpoint is reproduced here.

The Countries tab has search plus **All / Secure Core / P2P / Tor** filters and frames the locked catalog as **148 Plus countries**. A separate English upsell card says **“Access all countries with VPN Plus”**, another high-visibility localization leak. Free guests appear to receive an automatically selected fastest destination from a small rotating flag pool rather than manual access to the country list. Evidence: [countries](raw/proton-vpn/2026-07-22/screenshots/09-countries.png).

The specialist catalogs are more than filter chips: the observed build lists **68 Secure Core countries**, **144 P2P countries** and **6 Tor countries**. Each mode has an educational sheet before conversion. Secure Core compares privacy and latency against a normal route; P2P explains torrent benefits and no-activity-log/IP-hiding claims; Tor explains onion access in an ordinary browser. Their help actions lead to Proton support pages, including `protonvpn.com/support/p2p-vpn-redirection/` and `protonvpn.com/support/tor-vpn/`. Tapping a locked Tor country opens a compact feature-specific upsell rather than checkout. Evidence: [Secure Core list](raw/proton-vpn/2026-07-22/screenshots/89-countries-secure-core.png), [P2P list](raw/proton-vpn/2026-07-22/screenshots/90-countries-p2p.png), [Tor list](raw/proton-vpn/2026-07-22/screenshots/91-countries-tor.png), [Secure Core explainer](raw/proton-vpn/2026-07-22/screenshots/95-countries-secure-core-info.png), [P2P explainer](raw/proton-vpn/2026-07-22/screenshots/97-countries-p2p-info.png), [locked-Tor upsell](raw/proton-vpn/2026-07-22/screenshots/94-locked-tor-country-result.png).

The Profiles tab first explains that saved connection recipes can be customized and launched quickly. It then shows five ready-made use cases:

- US streaming;
- Games — fastest country;
- Censorship protection — fastest location excluding the user's own;
- Maximum security — Secure Core;
- Work/School — fastest country.

The presets are visually Plus-gated, but a guest can inspect the three-step profile builder. Step 1 combines a name with six colors and twelve icons. Step 2 selects Standard, Secure Core or P2P plus a fastest, exclude-mine or exact-country target. Step 3 overrides NetShield, protocol, NAT, LAN access, a post-connect action and custom DNS. The temporary test profile was exited without saving. Evidence: [preset list](raw/proton-vpn/2026-07-22/screenshots/11-profiles-list.png), [identity step](raw/proton-vpn/2026-07-22/screenshots/12-create-profile-result.png), [type/location step](raw/proton-vpn/2026-07-22/screenshots/14-profile-builder-step2.png), [settings step](raw/proton-vpn/2026-07-22/screenshots/18-profile-builder-step3.png).

Protocol choices are **Smart**, WireGuard UDP, WireGuard TCP and **Stealth**. A separate beta switch exposes Proton's own WireGuard implementation and warns about experimental instability. Stealth is positioned specifically against censorship and DPI, with a speed tradeoff. The copy mixes English and Russian. NAT offers strict type 3 and moderate type 2, explicitly connecting the latter to online gaming. Evidence: [protocol selector](raw/proton-vpn/2026-07-22/screenshots/20-profile-protocol-menu.png), [lower protocol copy](raw/proton-vpn/2026-07-22/screenshots/21-profile-protocol-menu-lower.png), [NAT selector](raw/proton-vpn/2026-07-22/screenshots/22-profile-nat-menu.png).

LAN controls split ordinary printer/speaker access from direct device-created networks such as Smart TV and Android Auto. **Connect and act** can automatically open either a URL or any installed app after a profile connects; the app picker correctly enumerated launchable apps. Custom DNS accepts IPv4 or IPv6 servers. Evidence: [LAN controls](raw/proton-vpn/2026-07-22/screenshots/23-profile-lan-menu.png), [post-connect action](raw/proton-vpn/2026-07-22/screenshots/24-profile-connect-and-act.png), [app picker](raw/proton-vpn/2026-07-22/screenshots/27-profile-connect-and-act-app-picker.png), [custom DNS](raw/proton-vpn/2026-07-22/screenshots/28-profile-custom-dns.png).

## Settings, Support And Growth

The guest Settings screen starts with an ecosystem conversion card rather than a VPN control. It offers a free Proton account bundling a password manager, encrypted mail/calendar and 1 GB of cloud storage, with create-account and sign-in actions. This cross-product bundle gives registration a broader value story than “sync VPN settings.” Evidence: [settings top](raw/proton-vpn/2026-07-22/screenshots/31-settings-top.png).

The control stack is deliberately split by entitlement:

- NetShield, split tunneling, VPN Accelerator, default-connection customization, excluded locations, LAN, moderate NAT and custom DNS are Plus conversion points;
- protocol selection, Android-backed kill switch instructions, alternative routing and IPv6 remain explorable to a guest;
- some locked rows use a short feature-specific upsell, while others reopen the full priced upgrade sheet, creating inconsistent interruption cost;
- the paywall repeatedly contains the typo **«Выберете себе план»**.

The kill-switch action opens Android's general VPN settings, where the user still has to locate Proton and tap its gear; the secondary help button opens `protonvpn.com/support/what-is-kill-switch/`. Advanced settings expose alternative routing, LAN, NAT, custom DNS and IPv6. Evidence: [NetShield upsell](raw/proton-vpn/2026-07-22/screenshots/32-settings-netshield.png), [kill-switch instructions](raw/proton-vpn/2026-07-22/screenshots/34-settings-kill-switch.png), [system destination](raw/proton-vpn/2026-07-22/screenshots/35-kill-switch-system-settings-destination.png), [advanced settings](raw/proton-vpn/2026-07-22/screenshots/43-settings-advanced.png).

Customization goes beyond theme: the launcher icon can be Proton light, Proton dark, retro, or disguised as Weather, Notes or Calculator. Proton warns that notifications retain the real name/icon. A home-screen widget surfaces connection status and favorite connections. These are strong anti-censorship and repeat-use mechanics worth treating as product features, not decoration. Evidence: [icon choices](raw/proton-vpn/2026-07-22/screenshots/46-settings-app-icon.png), [widget explainer](raw/proton-vpn/2026-07-22/screenshots/47-settings-widget.png).

Support uses a three-step deflection funnel: problem category, category-specific quick fixes, then a structured contact form. The form asks for email, intended action, failure, attempted fixes and enables **«Отправить журналы ошибок»** by default. No message was sent. Evidence: [categories](raw/proton-vpn/2026-07-22/screenshots/49-settings-report-problem.png), [quick fixes](raw/proton-vpn/2026-07-22/screenshots/50-report-problem-step2.png), [contact form](raw/proton-vpn/2026-07-22/screenshots/51-report-problem-step3.png).

The in-app debug-log viewer is highly sensitive: the observed guest log included authentication prefixes, a persistent guest-user identifier, alternative-routing hosts, private network addressing and coarse location/ISP. It also has a share action, while the bug-report form attaches error logs by default. Raw log evidence is quarantined outside the worktree. The audit records the disclosure surface, not any values.

**«Помогите нам бороться с цензурой»** actually opens telemetry preferences. Anonymous usage statistics and anonymous crash reports were both enabled by default for the guest. Proton says they exclude the IP address, cannot identify the user and are not shared with third parties; **Подробнее** goes to `protonvpn.com/support/share-usage-statistics`. The label is mission-led and more persuasive than a neutral “Analytics” row, but the debug-log surface above deserves separate scrutiny. Evidence: [telemetry preferences](raw/proton-vpn/2026-07-22/screenshots/52-settings-fight-censorship.png).

## Google Play Snapshot

The installed Play listing identifies **Proton AG**, labels the build **early access**, shows **100M+ downloads**, a verified VPN badge, Android 8+ and a 30 December 2019 release date. The observed listing was updated **17 July 2026** with an English beta changelog about a ProTUN codebase update intended to improve Proton Protocol stability. In-app products are listed from **599 RUB to 7,188 RUB**, matching the monthly and annual baselines used by the native paywall. Public reviews are replaced by private beta feedback in this early-access state. Evidence: [Play top](raw/proton-vpn/2026-07-22/screenshots/54-settings-rate-destination.png), [Play metadata](raw/proton-vpn/2026-07-22/screenshots/66-play-store-description-scroll-3.png).

Play Data Safety says no data is shared with third parties; the app may collect personal information, financial information and app/performance data; transport is encrypted; an independent security review was completed; account/data deletion is supported. Store support expands to the Proton website, public support email and privacy link. Developer identity is **Proton AG, Route de la Galaise 32, 1228 Plan-les-Ouates, Switzerland**. Evidence: [Data Safety](raw/proton-vpn/2026-07-22/screenshots/60-play-store-scroll-6.png), [developer/support details](raw/proton-vpn/2026-07-22/screenshots/62-play-store-support-bottom.png).

The recommendation graph mixes true substitutes and privacy-adjacent products. “Other interesting apps” shows Windscribe VPN and Tor Browser; “Similar apps” shows Cloudflare WARP, Opera, Via and Aloha; a separate developer rail cross-sells Proton Mail, Proton Drive, Lumo and Proton Authenticator. The first sponsored rail also includes DuckDuckGo and Aloha alongside unrelated inventory. This is a useful acquisition map: Proton competes with VPNs, browsers, DNS/privacy utilities and its own privacy suite simultaneously.

The five localized store creatives use a football-pitch campaign layer and sell, in order: a VPN Plus sport discount, instant privacy, fast servers, malware/ad blocking and speed. They show an older two-tab UI that materially differs from the current four-tab app. The listing therefore gains topical campaign energy at the cost of product fidelity. Evidence: [campaign opener](raw/proton-vpn/2026-07-22/screenshots/68-play-store-gallery-1.png), [privacy](raw/proton-vpn/2026-07-22/screenshots/69-play-store-gallery-2.png), [servers](raw/proton-vpn/2026-07-22/screenshots/70-play-store-gallery-3.png), [NetShield](raw/proton-vpn/2026-07-22/screenshots/71-play-store-gallery-4.png), [speed](raw/proton-vpn/2026-07-22/screenshots/72-play-store-gallery-5.png).

The third-party-license inventory loads slowly but is exceptionally transparent and exposes exact component versions. Visible families include Proton Core 36.6.1 under GPLv3, WireGuard Tunnel Library, Sentry 7.22.5, Play in-app update/review SDKs, Retrofit, Room and Jetpack Compose/AndroidX. Evidence: [license inventory after load](raw/proton-vpn/2026-07-22/screenshots/74-third-party-licenses-after-wait.png).

## Account Gateway

Guest mode is not a dead end. Create account accepts either an existing email address or a new Proton address, with the latter framed as **one account for all Proton services** and needed for Mail/Calendar. Sign-in starts with username/email and has a compact recovery hub for forgotten username, forgotten password, other sign-in problems and direct support. It also supports cross-device QR login: a user already signed into any Proton app can scan the VPN app's code from **Settings → Sign in on another device**. No account was created and no credential was entered.

The auth activities prevent normal Android screenshot capture; the zero-byte capture was not used as evidence. UI trees preserve only the non-secret copy in the worktree. A generated QR payload was immediately quarantined outside the worktree and is not reproduced. Evidence: [create-account UI tree](raw/proton-vpn/2026-07-22/ui/75-create-account-gateway.xml), [Proton-address option](raw/proton-vpn/2026-07-22/ui/76-create-account-proton-address.xml), [login gateway](raw/proton-vpn/2026-07-22/ui/78-login-gateway.xml), [login help](raw/proton-vpn/2026-07-22/ui/79-login-help.xml).

## Controlled Free Connection

`PASS` — the guest connected successfully without payment. App state changed to **«Защищена»**, Android `tun0` appeared, and connection details identified WireGuard plus session duration, throughput graph, country, city, server load and server identity. The detail page shows both the masked original IP and VPN IP; all home/detail captures remain in the sensitive quarantine rather than the worktree.

The first successful connection triggered two growth/permission interruptions in sequence:

1. a Google Play in-app review sheet, which was dismissed with **«Не сейчас»** and never submitted;
2. a notification-benefit prompt — **«Не пропустите важное…»** — offering connection-status alerts, declined with **«Нет, спасибо»**.

The connected card exposes **Disconnect** and **Change server** side by side. Two consecutive server changes both completed without a visible cooldown and selected different free countries. After each change the app added **«Не та страна, которую вы хотели? Улучшите для выбора любого сервера»** — free utility and immediate Plus conversion in the same state. Disconnect returned the app to **«Вы не защищены»** and removed `tun0`. A tunnel interface by itself was not counted as success; the result required both app-confirmed protected state and the interface check.

## Installed Package And Trust Surface

The installed Google Play build is a non-debuggable Android 8+ app targeting SDK 35. Its split APKs total roughly 37.9 MB on this emulator; the `332 kB` value shown by Play is therefore an update/download estimate for the current device state, not the complete app size. Declared capabilities cover the VPN foreground service, boot auto-connect, Quick Settings, widgets, biometrics, QR camera access, notifications, Play Billing/review/update and package visibility for app-based split tunneling and post-connect actions. It does not request fine location.

Static inspection matches the unusually broad native UI: ProTUN and WireGuard services, Android TV and TV QR flows, profile widgets, force-update/What's New, NPS/promo surfaces, split tunneling by app and CIDR/IP, telemetry preferences, bug reports and the log viewer all have dedicated components. Native libraries include Proton's Android Rust bridge, Go/WireGuard integration and Sentry. No ad-SDK package family was found. Sentry replay-related modules exist in the dependency graph, but dependency presence alone does not prove runtime replay collection.

The current runtime protocol selector contains Smart, WireGuard UDP/TCP and Stealth. Some OpenVPN text remains in the APK and the Play description still advertises OpenVPN, yet no OpenVPN engine package or native library was found. This is a concrete channel/copy mismatch rather than proof of a hidden protocol path.

The APK verifies under Android signature schemes v2/v3, carries a Google source stamp and is signed by Proton Technologies AG. Its signer fingerprint exactly matches the official Android repository's published fingerprint. That gives users a practical provenance check across Play and Proton's direct APK channel. Redacted technical evidence: [static and release notes](raw/proton-vpn/2026-07-22/logs/static-package-notes.md).

## Release Machinery

The official Android client is GPL-3.0 and ships through Google Play, F-Droid and direct GitHub APK releases. As of the snapshot, public GitHub/F-Droid stable was **5.19.43.0** from 14 July, while the installed Play early-access build was already **5.19.66.0** from 17 July. Proton therefore uses Play's beta channel ahead of its public stable source/tag, rather than moving every build to all channels simultaneously.

Across the latest 50 public GitHub releases, the observed mean gap was 15.4 days and the median 11.8 days, with same-day hotfixes and an occasional 52-day gap. In practice this is usually two to four Android releases per month. The latest direct APK was about 55.8 MB and had 26,519 GitHub downloads at capture time; its public note announced CIDR ranges for split tunneling.

The repository exposes an unusually complete release pipeline: a manual release branch cut with required notes; version calculation; guest-bootstrap and F-Droid metadata refresh; Play AAB, direct APK and Amazon APK builds; centralized signing; signature verification before GitHub publication; internal Play-track promotion for development builds; and a separate UI Automator release-test app. Tests explicitly cover smoke flows, real connection/performance SLI, anti-censorship scenarios and retained Loki/Grafana measurements.

Proton's Android Rust wrapper points at a submodule URL shaped for its internal repository layout, and that exact gitlink is not self-contained in the public mirror. ProTUN itself is nevertheless public under GPL-3.0 in the official `ProtonVPN/protun` repository; public `v2.1.2` landed on 17 July. The fair finding is a packaging/reproducibility wrinkle, not a closed-source core claim.

For POKROV, the highest-value pattern is not Proton's repository size. It is the trust-and-release chain: one candidate manifest across channels, a public signer fingerprint, signature-gated direct artifacts, explicit beta-versus-stable tracks and a small retained suite that proves a real tunnel and censorship-path behavior for each promoted build.

## Public Web, Ownership And Legal Surface

Proton's public surface is a content machine: 231 English static pages, 326 support articles and 357 blog articles, backed by 25 localized static sitemaps. The static site is dominated by 145 country/server pages, then dedicated feature, streaming, free-VPN, censorship-observatory and use-case families. The mega-menu routes through education, exact server countries, streaming services/devices, every platform, an IP tool, censorship observatory/simulator, support, blog, business VPN and the wider Proton suite.

Conversion is instrumented with first-party referral labels. Navigation records page/placement context in local storage; store links add UTM/referrer data. The main **Get Proton VPN** action opens pricing, **Sign in** opens the shared account gateway, paid buttons preconfigure VPN Plus or Proton Unlimited, and the free path is intercepted by a coupon-based Plus offer with an explicit **Continue with Proton Free** escape. Android download routes to Play, F-Droid or a Proton safety explainer that then links to GitHub releases. The footer's live-chat action opens the authenticated account dashboard, while Foundation donation is a separate mission conversion.

A discoverable sitemap URL named `free-vpn/home-test-090726-b` reveals a July free-first experiment: **1 device / no ads / no logs / unlimited and free forever**, testimonials, premium feature cards and free-versus-paid comparison. It demonstrates disciplined variant packaging, but exposing an explicitly named test route in the public sitemap is weak experiment hygiene.

The live server page reported **148 countries, 20,677 servers, 191 locations, 126 Secure Core servers and 18,062 Plus servers** at capture time. This aligns with the app's 148-country catalog and rounded 20,600-server claim. Generic pages deliberately use lower evergreen thresholds such as 20,000+/140+, while the experiment still says 110+.

Current Terms name **Proton AG** as operator: an active Swiss corporation in Plan-les-Ouates, UID `CHE-354.686.492`, formerly Proton Technologies AG. Swiss federal registry history shows that the old dedicated ProtonVPN AG was absorbed in June 2020 and deleted; it is not the current counterparty. Proton AG also has an active Zürich branch.

Proton says the active Swiss non-profit **Fondation Proton**, UID `CHE-418.863.304`, is its primary shareholder and can block mission-incompatible changes of control. Its registered purpose covers digital privacy, open-source censorship-resistant security, inclusion and the Geneva technology ecosystem. Proton's Privacy Policy separately names Proton Europe sàrl in Luxembourg as its EU/GDPR representative. Detailed registry and source notes: [website/legal/channel ledger](raw/proton-vpn/2026-07-22/documents/website-store-legal-release-and-channel-notes.md).

## Trust Proof And Public-Truth Drift

Proton links five consecutive annual no-logs infrastructure reports from Securitum, covering 2022–2026. The current company summary says auditors inspect production configuration, servers, procedures and staff practices, and that the latest pass found no significant security issue. The direct 2026 report itself remains `BLOCKED_BY_ACCESS` until the approved Chrome bridge can open the encrypted Proton Drive share; the profile does not promote Proton's summary to independently verified audit content.

The product-specific transparency report was updated 14 July 2026 and counts **458** Swiss-approved orders since 2017, all denied because Proton says the requested server-IP/timestamp identification logs did not exist; 47 of those orders occurred through June 2026. The central legal transparency page still stops at 2025, showing that even Proton's trust content has duplicate sources of truth.

Usage/crash collection is separate from network-activity logging. Proton's support page says anonymous usage sharing is on by default, retained 30 days, and can include crashes, failed connections, ISP and network type while excluding IP and browsing/app activity. That matches the default-on mobile toggles. The in-app debug log remains more sensitive when a user manually shares it.

The largest strategic weakness found is content drift:

- Android marketing says sign-up/login is required although the current app has anonymous guest onboarding;
- a free-Android page promises Android 6.0+, while the actual build and Play require Android 8+;
- several Android pages still advertise native OpenVPN/IKEv2 after OpenVPN was removed and both are EOL in the current lifecycle table;
- the free-server guide documents a 45-second then ten-minute cooldown, while two immediate rotations worked in this build;
- public beta notes lagged the installed early-access build by at least one build/day;
- store creatives show the previous two-tab UI;
- the homepage competitor table contains an apparent **EventVPN/ExpressVPN** typo.

POKROV should copy the proof architecture, multi-channel install story, stable/beta separation, support depth and first-party funnel attribution. It should beat Proton with a single generated product-facts manifest feeding minimum OS, protocols, versions, server counts, free limits, pricing disclosures and screenshots across every surface.

## Final blockers and evidence boundary

- `PASS`: guest onboarding, free catalog/profiles/settings/support, a real WireGuard connection, two server changes, clean disconnect, paid feature preview/paywall, static package, signer match and multi-channel release pipeline.
- `BLOCKED_BY_ACCESS`: the encrypted Proton Drive copy of the 2026 Securitum report could not be opened through the approved Chrome path. Only Proton's public audit summary is attributed here; the underlying report is not claimed as directly reviewed.
- `BLOCKED_BY_TOOLING`: the requested desktop-Chrome visual pass was unavailable in this environment. Public structure/text/link mapping was completed without substituting Playwright or another browser against the user's browser choice.
- `NOT_REQUESTED`: no account, purchase, review, support submission, referral, public post or destructive account action was completed.
- Screens containing current/public IPs, generated QR data, guest identifiers or sensitive debug-log material remain in quarantine outside the worktree.

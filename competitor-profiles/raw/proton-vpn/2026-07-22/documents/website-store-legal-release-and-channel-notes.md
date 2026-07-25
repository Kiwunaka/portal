# Proton VPN — Website, Legal, Trust And Channel Notes

Snapshot: 2026-07-22<br>
Pass status: static public-source pass complete; Chrome visual/interactive pass and direct reading of the 2026 audit PDF remain pending.

This is a durable, redacted research ledger. It records public product and company information only. Pricing that depends on client-side geolocation/hydration is not treated as verified from raw HTML.

## Public information architecture

The public sitemap was refreshed on 2026-07-21 and exposes a much larger acquisition/support surface than the app alone suggests:

- 25 localized static-site sitemaps;
- 231 English static pages;
- 326 English support articles;
- 357 English blog articles.

English static-page concentration:

| Family | Pages | Purpose |
|---|---:|---|
| Country/server landing pages | 145 | Programmatic search acquisition and exact location inventory |
| Feature pages | 19 | One proof/sales page per capability |
| Streaming pages | 14 | Service- and device-specific intent capture |
| Free-VPN pages | 13 | Platform/use-case free acquisition |
| Censorship observatory | 6 | Mission, research and newsworthiness |
| Use cases | 5 | Intent-specific conversion |

The global mega-menu is itself a product map. It routes users through VPN education, differentiators, features, server countries, streaming services/devices, pricing, every supported platform, an IP-address tool, a censorship observatory, an interactive censorship simulator, support, blog, business VPN and the wider Proton product suite. Proton therefore competes with content, tools and mission-led research as well as with the VPN client.

Most navigation links install a first-party `ref` value in local storage before navigation. Page-specific values distinguish the header menu, submenu, hero, footer, free-plan modal and blog contexts. Store links add ordinary UTM/referrer parameters. This is a coherent internal attribution system, not evidence of third-party ad tracking.

## Key button and destination map

| Surface/button | Observed destination | Funnel role |
|---|---|---|
| Header **Get Proton VPN** | `protonvpn.com/pricing` | Route all high-intent visitors through plan framing |
| Header **Sign in** | `account.protonvpn.com/login` | Shared Proton account gateway |
| Home **Business VPN** | `proton.me/business/vpn?ref=vpnhphero` | Separate B2B lane |
| Home **Get VPN Plus** | account signup with `plan=vpn2024`, monthly billing and currency | Preconfigured paid checkout |
| Home **Get Proton Unlimited** | account signup with `plan=bundle2022`, monthly billing and currency | Suite upsell |
| Free-plan modal **Get the deal** | account signup with VPN Plus plan and `VPNPLUSFREE2024` coupon | Low-price paid intercept before free signup |
| Free-plan modal **Continue with Proton Free** | account signup with `plan=free` | Clear escape hatch after upsell |
| Android **Download for Android** | Google Play with web/referrer campaign markers | Primary install channel |
| Android **F-Droid** | `f-droid.org/.../ch.protonvpn.android/` | De-Googled/open-source channel |
| Android **GitHub / APK on GitHub** | a Proton explainer article, then `github.com/ProtonVPN/android-app/releases` | Safety education before sideloading |
| Footer **Live chat** | authenticated account dashboard with `chat=true` | Paid/authenticated support |
| Footer **Donate** | Proton Foundation donation anchor | Converts mission affinity, not product intent |

The GitHub route intentionally uses an interstitial article rather than dropping an inexperienced user onto a release list. It explains APK risk, trusted-source verification and manual installation, then links to the releases page. A newer support article uses a current Samsung OneUI 8 flow and warns that direct APK installs do not auto-update.

## Funnel and experimentation

The homepage leads with control, global access and Proton Mail provenance, then layers server scale, speed, privacy, NetShield, censorship bypass and ten-device support. It includes an unusually direct comparison against ExpressVPN, CyberGhost, NordVPN and Surfshark across open source, public audit availability, blockers, accelerator, jurisdiction and ownership. Footnotes attack competitors' gated audit reports and ownership structures. The copy contains an apparent **“EventVPN”** typo where ExpressVPN is intended, illustrating the legal/editorial risk of aggressive comparison copy.

A public sitemap entry named `free-vpn/home-test-090726-b` exposes a free-first experiment dated like 9 July 2026. Its hero compresses the promise into **1 device / no ads / no logs / unlimited and free forever**, immediately offers the same Plus interception modal, then sells privacy, public-Wi-Fi safety, censorship bypass and unlimited bandwidth. Later sections use testimonials, a free-versus-paid comparison and nine premium capability cards. This is a useful example of a self-contained acquisition variant, though public discoverability of an explicitly named test page is sloppy experiment hygiene.

Raw HTML for home/pricing contains unhydrated placeholders such as `$XX.XX`, `$0.00` and `undefined% off`. Some comparison values also look like template defaults. These are not classified as visible defects until the pending Chrome pass confirms what a normal rendered visitor sees.

## Current network claims

The live server inventory reported at capture time:

- 148 countries;
- 20,677 servers;
- 191 locations;
- 126 Secure Core servers;
- 18,062 Plus servers.

The app's **148 countries** agrees with the exact inventory and its **20,600 servers** is a reasonable rounded snapshot. Generic landing pages deliberately use evergreen lower bounds such as **20,000+ servers / 140+ countries**. The experiment variant still says **110+ countries**, which is materially more conservative but weakens consistency.

## Android support and release surface

The support sitemap exposes at least 32 directly relevant Android/mobile/capability articles, including setup, install from APK, Android TV, early access, Android 13/16 issues, OS power management, permissions, disconnects, free-server changes, mobile widgets, kill switch, split tunneling, NetShield, custom DNS, moderate NAT, protocols, WireGuard, Secure Core, P2P, Tor and usage statistics.

The early-access article describes one beta program across Android phone, TV, Chromebook and Fire Stick via Google Play. Beta replaces the installed build rather than creating a parallel app, users can leave/rejoin at any time, and Proton explicitly trades early features for expected bugs plus private feedback.

The public release-notes page separates **Latest stable**, **Latest beta (early access)** and full history. At the snapshot it listed stable `5.19.43.0` dated 7 July and beta `5.19.61.0` dated 16 July. The actually installed early-access build was already `5.19.66.0`, updated in Play on 17 July. The support changelog therefore lagged the live beta by at least one build/day, while GitHub/F-Droid stable remained on `5.19.43.0`.

The product-lifecycle page is an explicit compatibility matrix for every application, OS family, protocol and major capability. It admits that the page is still a work in progress. Its current protocol table marks Android OpenVPN and IKEv2 as EOL and WireGuard/Stealth as supported, matching the runtime and static APK findings.

## Documentation drift found

| Public claim | Current observed reality | Assessment |
|---|---|---|
| Android download/free pages tell users to create an account and log in | Current early-access app has a dominant anonymous guest path | Acquisition copy has not caught up with guest onboarding |
| Free Android page says Android 6.0+ | Installed manifest and Play listing require Android 8+ | Concrete minimum-OS mismatch |
| Android/free/setup pages still say the app supports OpenVPN, sometimes IKEv2 | OpenVPN was removed in `5.15.70.0`; lifecycle table and current selector say WireGuard/Stealth | Several evergreen pages are stale |
| Manual Android setup article says the Proton app can choose OpenVPN before describing third-party OpenVPN apps | Current first-party app cannot | Confusing transition between native and manual paths |
| Free-server support article says first change has a 45-second cooldown and later changes have ten-minute cooldowns | Two consecutive changes succeeded in the observed guest build without a visible timer | Could be beta policy change, experiment or documentation lag; needs later retest |
| Support release notes say beta `5.19.61.0` | Installed early-access build is `5.19.66.0` | Changelog lag |
| Central legal transparency page stops at 2025 | VPN blog transparency report adds 2026 through June | Duplicate truth sources drift |
| Store screenshots show an older two-tab client | Installed app uses a four-tab shell | Creative/product drift |

Proton's own telemetry explainer says usage data helps the experience team update outdated information, yet several high-intent Android pages remain out of sync. This is a useful warning for POKROV: content scale becomes a liability without centrally generated product facts.

## Company and legal entities

### Proton AG

The service operator named in current Terms and Privacy Policy is **Proton AG**, Route de la Galaise 32, 1228 Plan-les-Ouates, Geneva, Switzerland.

Swiss federal Zefix registry snapshot:

- active Swiss stock corporation;
- UID `CHE-354.686.492`;
- commercial-register ID `CH-660-1995014-1`;
- legal seat: Plan-les-Ouates;
- registered purpose: development of security and privacy software;
- former name: Proton Technologies AG;
- active Zürich branch: UID `CHE-363.321.658`, Engelstrasse 6, 8004 Zürich;
- statutory auditor shown by Zefix: PricewaterhouseCoopers SA, Geneva branch.

The old dedicated **ProtonVPN AG** (`CHE-496.963.746`) was absorbed into Proton Technologies AG by merger on 19 June 2020 and deleted from the registry on 30 June 2020. The current VPN counterparty is therefore Proton AG, not a still-active ProtonVPN AG subsidiary.

### Fondation Proton / Proton Foundation

Proton's own About, Foundation and Terms pages say the Swiss non-profit **Fondation Proton** is Proton AG's primary shareholder/supervisory owner and can block a change of control that conflicts with its mission. Proton says it has no venture-capital investors.

Swiss federal Zefix registry snapshot:

- active foundation;
- UID `CHE-418.863.304`;
- commercial-register ID `CH-660-0054023-4`;
- Route de la Galaise 34, 1228 Plan-les-Ouates;
- registered purpose includes digital privacy, open-source censorship-resistant cybersecurity, digital inclusion and support for Geneva's technology ecosystem;
- current statutory auditor shown by Zefix: FORVIS MAZARS SA.

The public foundation board lists Andy Yen, Antonio Gambardella, Carissa Véliz, Tim Berners-Lee and Dingchao Lu. Proton says the Foundation may receive 1% of company revenue for charitable work when financial conditions allow and has issued more than $5 million in grants. This structure is used repeatedly as a trust and anti-takeover differentiator.

### Other named legal role

The general Privacy Policy names **Proton Europe sàrl**, rue de Grünewald 94, L-1912 Luxembourg, as Proton AG's EU representative, including for GDPR Article 27 purposes. It is a regulatory representative, not the Android app publisher or VPN contract operator.

## Terms, billing and cancellation

Current general Terms were last modified 23 June 2026. They cover use with or without an account, name Proton AG as operator under Foundation supervision, require users to be at least 13 with guardian consent for minors and prohibit automated/bulk free-account creation and multiple free accounts used abusively.

Paid plans may bill monthly, yearly or every two years and auto-renew for the disclosed term. Proton may charge the then-current renewal price. Cancellation is available in the account dashboard or through support if the dashboard is inaccessible.

For eligible direct Proton purchases, both cancellation and refund request must occur within 30 days of initial purchase. The refund can be used once per user; cash/bank-transfer payments are excluded; third-party store purchases follow that store's policy. This matters because the Android paywall's auto-renewal disclosure is only one layer of a broader cross-product billing contract.

## Privacy, telemetry and no-logs proof

The VPN-specific Privacy Policy was last modified 30 July 2025. It says Proton does not log traffic/content, discriminate by device/protocol/app, throttle ordinary connections or retain VPN session data. The free plan is included, although Proton reserves the right to limit excessive free-server consumption. Account infrastructure is said to be owned/operated by Proton or subsidiaries and stored encrypted in Switzerland, Germany or Norway. Proton says it physically owns all Secure Core servers and most Swiss/German VPN servers; all VPN servers use full-disk encryption.

No-logs does not mean the client emits no diagnostics. The usage-statistics article explicitly says sharing is enabled by default and may include crash reports, failed connection attempts, ISP and network type. Proton says this excludes IP address and app/web activity, is aggregated/anonymized and deleted after 30 days. This matches the two default-on toggles observed in the app. The separate local debug log can contain operational identifiers and network details when manually viewed/shared; that support artifact should not be confused with server-side browsing logs.

Proton's no-logs page says Securitum has performed five consecutive annual infrastructure audits. The 2026 article says auditors inspect production configuration, server setup, procedures and staff practices rather than merely reviewing policy wording. Proton publishes public Proton Drive links for the full reports:

- 2026: <https://drive.proton.me/urls/DZVEJZFYHM#FPSKdUEykprb>
- 2025: <https://drive.proton.me/urls/NA0V1AX7QR#2LxqkF786aPy>
- 2024: <https://drive.proton.me/urls/ED8G4GC5MG#pM52Y8RMXIKn>
- 2023: <https://drive.proton.me/urls/TEGZZ53M28#lPz2jeVjV6Mp>
- 2022: <https://drive.proton.me/urls/521N34GHTM#PVwqewJVFgyS>

The 2026 underlying PDF has not yet been visually opened/read because the approved Chrome bridge is disconnected; until it is, only Proton's own summary is attributed. That summary says the fifth audit confirmed no logs and no significant security issues.

The current VPN transparency report, published/updated 14 July 2026, counts **458** Swiss-approved legal orders since launch. Each requested identification of a user behind a server IP/timestamp, and Proton says every order was denied because the required logs did not exist. The 2026 subtotal through June is 47/47 denied. A central Proton legal-transparency page last updated 6 January contains only data through 2025, making the VPN blog the fresher product-specific source.

## What POKROV should copy

- Make company identity, current operator, jurisdiction and owner/control structure visible from the app, store and site.
- Publish one trust page that links source, independent reports, signer fingerprint, transparency counts and a plain-language data map.
- Keep a free path with an honest paid interception and a clear escape hatch; use benefit-specific upsells inside locked features.
- Separate stable and beta changelogs and expose a lifecycle/compatibility matrix.
- Offer Play plus a verified direct APK channel, with an interstitial explaining sideloading risk and signature verification.
- Build acquisition around useful tools, platform guides, censorship research and intent pages, not only a generic landing page.
- Use first-party referral labels consistently enough to compare hero, menu, modal, article and store conversion.

## What POKROV should improve on

- Generate minimum OS, protocols, country/server counts, free policy and current versions from one release/product manifest across app, Play, site and support.
- Never leave a manual guide claiming a removed protocol is still native.
- Host audit reports as direct, plainly versioned files with hashes in addition to a branded sharing link.
- Keep the store gallery synchronized with the current navigation shell.
- Source and lawyer-review competitor comparison tables; avoid vague ownership attacks and embarrassing name typos.
- Make diagnostic collection granular at first run and show retention/fields beside the toggle instead of relying on a separate support article.

## Primary public sources

- <https://protonvpn.com/sitemap.xml>
- <https://protonvpn.com/about>
- <https://proton.me/foundation>
- <https://proton.me/legal/terms>
- <https://proton.me/legal/privacy>
- <https://protonvpn.com/privacy-policy>
- <https://protonvpn.com/blog/no-logs-audit>
- <https://protonvpn.com/blog/transparency-report>
- <https://protonvpn.com/vpn-servers>
- <https://protonvpn.com/download-android>
- <https://protonvpn.com/support/release-notes-android>
- <https://protonvpn.com/support/product-lifecycle>
- <https://protonvpn.com/support/discontinuing-openvpn-android>
- <https://protonvpn.com/support/share-usage-statistics>
- Swiss federal Zefix REST registry records for Proton AG (`ehraid 1189263`) and Fondation Proton (`ehraid 1568928`).

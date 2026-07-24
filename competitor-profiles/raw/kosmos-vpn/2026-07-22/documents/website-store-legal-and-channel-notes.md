# Космос VPN — Website, Stores, Legal And Public-Channel Notes

Snapshot: 2026-07-22. This file records public, first-party or official-store material. Counts and ranks are volatile snapshots. Customer reviews and provider claims are labeled rather than treated as verified facts.

## Official Destinations

- Website: <https://kosmosvpn.ru/>
- Privacy policy: <https://kosmosvpn.ru/privacy.html>
- Website user agreement PDF: <https://kosmosvpn.ru/usr.pdf>
- Site-hosted English translation of Armenian registry extract: <https://kosmosvpn.ru/extract_translation_compressed.pdf>
- Google Play: <https://play.google.com/store/apps/details?id=ru.space.vpn&hl=ru>
- Apple App Store: <https://apps.apple.com/ru/app/%D0%BA%D0%BE%D1%81%D0%BC%D0%BE%D1%81-vpn/id6755416006>
- Public Telegram channel: <https://t.me/kosmo_vpn_news>
- Customer bot: `@vpn_kosmo_bot`
- Support bot: `@vpn_kosmo_support_bot`

Personalized cabinet relay paths, query values, account identifiers and audit email are excluded.

## Website Generation Gap

The root website appears to describe an older configuration-link/business product rather than the current native consumer client. It claims speed, safe public Wi-Fi and automatic routing of Russian domains, then instructs users to generate a personal configuration link and paste it into an external app.

Displayed plans:

| Plan | Displayed price |
| --- | ---: |
| Personal | 240 ₽/month |
| Teams | 490 ₽/month |
| Organizations | 790 ₽/month |

The same table mixes connection counts, traffic, clients, deployment and administrator roles. All trial CTAs route to Telegram. These plans do not match the current native/cabinet/Telegram consumer model.

## Current Telegram Pricing And Operations

A current pricing post, effective 7 June, states:

- one month: 229 ₽;
- three months: 599 ₽;
- six months: 1,099 ₽;
- three devices included;
- one additional device: 45 ₽;
- 30 GB allow-list traffic: 99 ₽, with remaining balance carried forward.

Older channel copy advertised 159 ₽/month and a future free tariff; it is historical, not current pricing.

The public channel recently reported a DDoS-related outage over Sunday/Monday, said service was restored and promised five added days. The authenticated cabinet instead said seven days had been credited. This is a direct contradiction between current owned surfaces.

Other channel claims and patterns:

- many users connect first to a Russian entry server before international egress;
- this architecture supposedly reduces exposure to possible international-traffic charging;
- allow-list subscriptions in Happ/v2rayTun must periodically be refreshed;
- server locations are added/removed quickly;
- referral bonuses, promo pricing, raffles and compensation drive acquisition/retention;
- a launch post routes registration to the website through the bot/cabinet and warns against relying on Telegram webview;
- some referral rewards were reportedly rejected by automation and later restored manually.

Architecture, IP-churn and billing-avoidance claims are provider statements and were not independently verified.

## Alternative-Client Matrix

Official posts have recommended:

| Platform | Recommended clients observed |
| --- | --- |
| iOS | v2rayTun, Shadowrocket, INCY, Happ when available |
| Android | v2rayTun, Happ |
| macOS | v2rayTun, Clash Verge |
| Windows | v2rayTun |
| Android TV | v2rayTun |
| Apple TV | Shadowrocket |

The channel has also posted region-change instructions for App Store access using placeholder US personal/address data. This is a risky workaround, not a pattern to copy.

## Google Play Snapshot

- Publisher: Kosmos Connection
- Legal developer shown: KOSMOS CONNECTION, LLC, Armenia
- 100K+ installs
- Approximate rating: 4.6
- Approximately one thousand reviews, with count varying by localized render
- Updated: 29 May 2026
- Current release line: 1.3.3

Visible changelog:

- built-in Android TV QR scanner;
- revised TV connection section;
- automatic logout when a device is removed in the cabinet;
- connection timer and server-selection fixes;
- Huawei/MicroG compatibility.

Play describes one-click connection, automatic fastest-server choice, reconnection and no speed/traffic limits. Its Data Safety surface says no data is collected or shared. That conflicts with the privacy policy and manifest measurement stack.

Review clusters:

- positive: easy setup, stability and low price;
- negative/unverified: paid service unavailable, server/account/support pages failing, alleged automatic card binding and repeated charges with difficult cancellation.

Nearby Play suggestions included PureVPN, VPNHouse and VeePN plus unrelated locale-driven apps.

## Apple App Store Snapshot

- Version: 1.3.3, dated 2 June 2026
- Approximate rating: 3.9/5 from about 2K ratings
- Utilities rank observed around #25–29
- Prior visible releases: 1.2.8 on 24 February; 1.2.9 on 23 March

Release notes mention Android TV QR, iPad design, VPN-launch reliability and data protection; the earlier release mentions interface and memory optimization.

The product description combines incompatible positions: an unlimited/no-log/no-ad VPN and a generic client that only uses user-provided proxies, supplies no server infrastructure or keys, and stores configs locally. The latter does not match the current managed subscription, native registration and cabinet.

Apple’s privacy label says no data is collected, again contradicting the privacy policy and working account system.

Review themes include inability to connect, a Telegram dependency for obtaining a key, confusing QR onboarding and positive comments about automatic fastest-server selection.

Nearby App Store recommendations included Glaz VPN, EVA VPN, VPN 2026, ETNA, MeiLing, VPNS Bot, VpnDoc, Privata, Oneok and BLACKTEMPLE. “More from this developer” also exposed xMessenger, a support-chat product.

## Public Entities And Documents

The website identifies Armenian **KOSMOS CONNECTION, LLC** and separately lists Russian sole proprietor **ИП Лисецкая Алина Михайловна**. Public registration identifiers and addresses were inspected but are omitted here because they add little to product analysis and increase unnecessary personal-data exposure.

The site-hosted Armenian extract translation says the LLC was registered on 15 August 2025 and contained no liquidation/termination information when issued. It is historical formation evidence only. The current Armenian registry moved to a dynamic search surface; a current exact lookup did not complete, so status as of 22 July 2026 is `BLOCKED_BY_ACCESS`.

The Russian sole proprietor was checked by exact identifier in the official FNS EGRUL/EGRIP service at <https://egrul.nalog.ru/>. The result matched the website identity, and a fresh electronic extract generated on 22 July 2026 contained the registration record without a termination section or inactive marker. This supports current active status. The PDF stays outside the repository because it contains unnecessary personal registry detail.

The user agreement is dated 4 April 2024. It describes a Telegram-bot/system service for legal entities, names the Russian sole proprietor as seller, applies Russian law, permits unilateral changes/termination and gives no availability guarantee. It does not cleanly govern the current Armenian-company/native-consumer/email-account product.

## Privacy Policy

The policy names Kosmos Connection LLC and admits collecting or processing:

- email;
- optional name and Telegram ID/username;
- payment amount, currency, date, payer email and last four card digits;
- device/support data and online-chat browser/OS context;
- feature usage;
- website logs;
- crash and diagnostic information;
- analytics and advertising measurement.

It says it does not keep user IP addresses, browsing history, connection metadata, traffic content or DNS queries. It mentions WireGuard and potentially OpenVPN.

Notable terms:

- payment records: ten years;
- marketing consent: three years after subscription;
- support tickets: three years;
- device information used for support: no more than six months;
- possible US/EU international transfers;
- user-rights response target: 30 days;
- service not intended for people under 18;
- providers may be used for payments, support, email, analytics and advertising, but no clear named processor list was observed.

The policy says users should be warned before choosing servers in countries with weak democratic protections. No warning appeared in the native list during the audit. It also describes government-request handling by whether a country is “generally recognized as democratic”, which is not a clear operational or legal standard.

## Major Cross-Surface Contradictions

| Topic | Surface A | Surface B |
| --- | --- | --- |
| Consumer price | Website: 240/490/790 ₽ business-style tiers | Telegram: 229/599/1,099 ₽ term pricing |
| Outage compensation | Telegram: five days | Authenticated cabinet: seven days |
| Data collection | Play and Apple: none | Policy: account, payment, support, usage, diagnostics, analytics/ads |
| Product type | iOS description: generic user-provided proxy client | Native app/cabinet: managed account and servers |
| Legal model | 2024 agreement: Russian IP, B2B Telegram bot/system | Current stores/site: Armenian LLC, consumer native apps |
| Age | Privacy: not under 18 | Stores: 3+/4+, registration has no age gate |
| Jurisdiction warning | Privacy promises warning | No warning observed for Russia/Kazakhstan |
| Current locations | Native app: eleven fixed countries | Telegram: fast-changing additions/removals |

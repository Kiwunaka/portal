# Red Shield VPN — Public, Store, Legal And Release Surface Notes

Snapshot: 2026-07-22. This file records public, non-personal observations. Account identifiers, credentials, payment details, raw VPN configuration, server endpoints, signing fingerprints and diagnostic payloads are intentionally excluded.

## Confidence And Evidence Rules

- **Primary / owned:** official Red Shield pages and stores, Google Play, Apple App Store, Chrome Web Store, Mozilla Add-ons, Florida Sunbiz, UK Companies House and the ECHR record.
- **Observed runtime:** destinations opened by the installed Android app and the isolated unpaid account flow.
- **Secondary:** search-engine snapshots, APK catalogues, press and trademark mirrors. Secondary material is labelled and is not used to overrule primary records.
- Store ratings, review counts, recommendations and ranking labels are volatile and locale-dependent. Values below are a dated snapshot, not a permanent product fact.
- User reviews are anecdotes about perceived experience. They are useful for finding themes, not proof that an allegation is true.

## Public Surface And Link Topology

The customer journey is deliberately spread across several hosts:

| Role | Observed destination | Notes |
| --- | --- | --- |
| Canonical marketing site | `https://redshieldvpn.me/` | Canonical tags observed pointing to `.me`. |
| Public mirrors | `https://redshieldvpn.com/`, `https://redshieldvpn.xyz/`, `https://new2.redshieldvpn.info/` | All returned HTTP 200 for the English landing page on the snapshot date. The Telegram profile promotes `.xyz`; the Android app used `new2.redshieldvpn.info`. |
| Cabinet | `https://my.redshieldvpn.com/` | Profile, payments, cards, devices, manual configurations, referrals and gifts. |
| Android checkout | `https://pay100.myrsv.live/` | Opened immediately after registration and again when an unpaid user moved the connection slider. |
| Direct Android build | `https://downloads.redshieldvpn.com/rsv_latest.apk` | HTTP 200; 139,325,698 bytes; `Last-Modified: Mon, 06 Jul 2026 18:46:20 GMT`. |
| Apple recovery guide | `https://apple.rsv.today/` | Region-switch instructions for users affected by removal from the Russian App Store. |
| Telegram channel | `https://t.me/redshieldvpn_ru` | Public news/advocacy/promotions; profile points to the `.xyz` mirror. |
| Telegram service bot | `https://t.me/redshieldvpn` | Account/service management and an alternate application-delivery route described in the cabinet. |
| Chrome / Edge extension | `https://chromewebstore.google.com/detail/red-shield-vpn/fmhbdohlogekfmknbhfpbeiphcldcfji` | Official publisher page identifies Private Network Labs LLC. |
| Firefox extension | `https://addons.mozilla.org/firefox/addon/red-shield-vpn/` | Official Mozilla listing. |

This multi-domain layout looks designed for distribution resilience under blocking, but that motive is an inference from the mirrored content, app routing and anti-censorship positioning. It is not an explicit technical architecture statement from the company.

The current sitemap at `https://redshieldvpn.com/sitemap.xml` exposed 194 URLs: 97 English and 97 Russian. Each language contained 41 news articles, 13 application-guide pages, 11 router guides, 5 Linux guides, 6 feature pages, 9 description/policy pages, 3 FAQ-detail pages and the top-level home/news/FAQ/platform/legal routes. It is a deep support/SEO library rather than a thin landing site.

## Website Offer And Product Claims

Official English landing page: `https://redshieldvpn.com/en`.

- USD offer: $11.90 for one month; $53.55 for six months; $71.40 for twelve months.
- Russian checkout observed in-app: 890 RUB for one month; 4,005 RUB for six months; 5,340 RUB for twelve months.
- Every tier advertises up to ten devices, unlimited bandwidth, no speed limit, desktop/mobile apps, router support and “14 days for refund if it doesn't work.”
- There is no free tier or trial in the observed Android path. Registration moves directly to checkout and the unpaid connect control reopens checkout.
- The site advertises 37 locations. Seven special-purpose entries—Russia, Georgia, Kazakhstan, Belarus, Armenia, Ukraine and Uzbekistan—are marked “Safe” on the site and are placed in the app's “other/not recommended” group.
- The Double VPN page explains that some locations traverse two servers and that this implementation is used by default for those special entries. Source: `https://redshieldvpn.com/en/help/features/double_vpn`.
- The location section asks users to suggest a missing country. This turns a static server list into a lightweight demand-discovery channel.
- The site says servers are physical, encrypted and owned/rented rather than generic virtual locations. This is marketing copy; no current independent infrastructure audit was found in this pass.

### Platform Buttons And What They Deliver

- Android → Google Play.
- APK → direct first-party APK download.
- iPhone/iPad/Apple TV → Apple App Store / installation guide.
- Windows and macOS → platform-specific guides with a client download handoff.
- Chrome and Edge → the same Chrome Web Store extension.
- Firefox → Mozilla Add-ons.
- Linux and routers → cabinet-generated manual configurations plus guides.

The public documentation supports WireGuard, AmneziaWG/AmneziaWG 2, VLESS, and platform-specific manual paths for Keenetic, MikroTik, OpenWrt, Ubuntu and Debian. Branded apps are recommended over manual configurations in heavily censored environments.

## Protocol And Feature Story

Official RedLink page: `https://redshieldvpn.com/en/help/features/redlink`.

- RedLink Random is described as based on AmneziaWG/AmneziaWG 2, themselves based on WireGuard, with traffic made to resemble random UDP packets.
- RedLink TLS and TLS Plus are described as based on VLESS and other methods that mask VPN traffic as ordinary TLS/web traffic.
- Auto selects a protocol for the current region.
- The public explanation is much more technically specific than the native protocol picker, which exposes only Auto, RedLink TLS Plus and RedLink Random.

Other public feature pages cover Double VPN, IPv6-leak protection, DNS-leak protection and Kill Switch. Native Android adds split-tunnel inclusion/exclusion/presets, local-network access, ads/tracker/malware blocklists, Wi-Fi sharing, quick settings and a widget.

## Support And Instructions

The FAQ/support library is commercially useful but unusually strict:

- users are told to keep every app current; old versions are unsupported;
- common troubleshooting asks users to remove other VPNs, antivirus/firewall software except Windows Defender, then test 5–7 locations and every protocol;
- one extreme troubleshooting branch says an operating-system reinstall may be necessary;
- Android guidance recommends trying the direct APK build, disabling battery saving and using Android's Always-on VPN / Block connections without VPN controls as a kill switch;
- local-sites-without-VPN and split-tunnel instructions vary by platform;
- torrent availability can be restricted on particular locations after copyright complaints;
- router guidance recommends no more than three devices behind one router even though the router counts as one registered device; more is framed as a fair-use violation;
- support says replies normally take up to 24 hours, sometimes longer, but explicitly says duplicate requests or questions already answered in FAQ may receive no response;
- the public support modal was observed saying support was unavailable at that moment;
- support is scoped to service problems, not general cybersecurity advice or commercial proposals.

No support request was submitted during the audit.

## Growth And Retention Mechanics

- **Referral:** one free month is credited after a referred user's first payment. The reward is tied to realized revenue, not an install.
- **Gift:** the same 1/6/12-month terms can be bought as a coupon for another user. Gift codes are explicitly non-refundable.
- **Promo codes:** present in native Android, web checkout and historical Telegram campaigns.
- **Telegram redundancy:** a public channel handles block notices, positioning and promotions; the bot/cabinet link covers account management and alternative distribution.
- **In-app review:** Google Play review integration is bundled in the Android package, although no prompt appeared during the unpaid session.
- **Political/identity positioning:** the Russian Telegram channel frames the product as pro-open-internet and anti-censorship. Historical campaigns included free access for independent journalists covering protests.
- **No product-led proof before payment:** the Android acquisition funnel has no sample connection, quota or trial. Trust, documentation and anti-censorship credibility do the selling.

Historical Telegram copy is not current product truth. Its claims of seven devices, ~$4.14/month, unlimited all-location torrents and round-the-clock support conflict with the current ten-device offer, 1 TB fair-use term, location-specific torrent restrictions and gated support language.

## Google Play Snapshot

Official listing: `https://play.google.com/store/apps/details?id=com.redshieldvpn.app`.

- Developer: Private Network Labs LLC.
- 500K+ downloads; 4.7 overall with about 7.55K reviews in the observed locale; phone sub-rating 4.6 with about 6.6K reviews.
- PEGI 3 / Communication / Digital Purchases.
- Updated July 6, 2026.
- “What's new” makes the release mandatory by August 10 and says older versions will stop working because of availability changes in some regions.
- Review themes sampled on the listing: multi-year reliability and stability during whitelist-only shutdowns; a specific UX complaint about frequent Chrome handoffs; a complaint that “other locations” were unreachable. Treat all three as review anecdotes.

The observed recommendation shelf contained JumpJumpVPN, Proton VPN, PandaVPN, Octohide, ExpressVPN and Intra. Other locale snapshots produced different lists, so this is an algorithmic/locale-dependent acquisition adjacency, not a fixed partner list.

### Google Play Data Safety

The developer declares no data sharing with third parties, encryption in transit and deletion requests. The detailed categories observed were:

- crash logs and diagnostics for analytics;
- other in-app messages for developer communications;
- email and user IDs for app functionality, analytics, communications, fraud/security/compliance and account management;
- payment information and purchase history for the same broad purposes;
- device/other identifiers for app functionality.

This is more nuanced than the listing's broad marketing sentence that the service does not collect or analyze user data. Static inspection also found Firebase Analytics/Measurement, Crashlytics and Messaging. SDK presence alone does not prove every event path is active.

## Apple Distribution Snapshot

Official listing: `https://apps.apple.com/us/app/red-shield-vpn/id1476245357`.

- Seller: Private Network Labs LLC; iPhone, iPad and Apple TV; 4.8 from about 2.1K US ratings; age 4+; English and Russian.
- US in-app purchase prices: $11.99 / $53.99 / $71.90 for 1/6/12 months. Prices differ by storefront.
- Current observed release: 4.1.2 on June 29, 2026, mandatory by July 10 because prior versions would stop working.
- 2026 cadence shown in Apple history: 4.0.2 Jan 28; 4.0.3 Apr 9; 4.0.4 Apr 15; 4.0.5 Apr 18; 4.0.6 Apr 24; 4.1 May 5; 4.1.2 Jun 29. Most entries say minor fixes; 4.0.2 introduced TLS Plus masking.
- Apple privacy labels link email and purchase history to identity; product interaction/usage and diagnostics are not linked to identity.
- Sampled reviews include strong stability praise and billing/support complaints. The allegations remain unverified anecdotes; the visible developer replies were defensive and routed users back to support/refund policy.
- Apple's “You Might Also Like” shelf included PlatoVPN, FREE VPN APP, VPN Satoshi, ForceField, AmneziaVPN, Grizzly VPN, VPN Matreshka, VPN 111, BlancVPN and Paper VPN in the observed storefront.

### Russian App Store Recovery And Impersonation Risk

The official service says Apple removed its app from the Russian App Store. Its current guide at `https://apple.rsv.today/` instructs users to:

1. change Apple ID country/region to the United States;
2. use a generated foreign name, street, city, state, ZIP and phone number if they do not have a real overseas address;
3. choose no payment method;
4. install/update the app, then optionally switch the region back;
5. email support for an unspecified “alternative method” if region switching is difficult.

The guide links a third-party fake-address generator. The audit did not follow the procedure, generate an identity, contact support or obtain the alternative method.

A separate Russian-store listing appeared under the same/similar name in June 2026 with a different application ID and provider, **KreationBuyJosie, LLC**, not Private Network Labs LLC. Its own reviews say it is unrelated to the original. This is an active brand-confusion/impersonation risk; the evidence does not establish who operates it or whether it is malicious.

## Browser Extensions

### Chrome / Edge

Official listing: `https://chromewebstore.google.com/detail/red-shield-vpn/fmhbdohlogekfmknbhfpbeiphcldcfji`.

- Private Network Labs LLC; 40,000 users; 3.9 from 175 ratings in the observed snapshot.
- v1.0.367, updated June 17, 2026; 2.86 MiB; in-app purchases.
- 24 languages—far broader localization than the two-language native Android/iOS apps.
- Store privacy disclosure says the extension handles financial/payment information and location.
- The extension description promises ten devices, no traffic limits and a refund if it does not work and support cannot help, again omitting the detailed refund exclusions.

### Firefox

Official listing: `https://addons.mozilla.org/firefox/addon/red-shield-vpn/`.

- 2,534 users; 3.8 from 52 reviews.
- v300.0.42, updated May 8, 2026; 2.88 MB.
- Permissions include browser privacy settings, proxy control, tabs and data access on all sites.
- The developer declares that no data collection is required.

The Chrome and Firefox privacy disclosures are not identical. That may reflect platform form differences or implementation differences; the audit did not inspect the extension packages deeply enough to decide which.

## Release And Distribution Model

The release system has several coordinated lanes:

1. **Google Play Android:** current store build, Play Source Stamp and in-app Play update API. July 6 update becomes mandatory August 10.
2. **Direct Android APK:** first-party `rsv_latest.apk`, updated July 6. Static code supports stable and server-selected beta downloads and verifies an allowed signing identity before opening Android's installer. A guessed public `rsv_beta.apk` path returned 404, so beta capability exists in code but no public beta link was observed.
3. **Apple:** native App Store release with rapid spring 2026 cadence and a mandatory June 29 release deadline.
4. **Browser extensions:** independent Chrome/Edge and Firefox version lines and release dates.
5. **Windows/macOS/manual configurations:** site/cabinet distribution outside mobile stores.
6. **Mirrors and Telegram:** alternate discovery/support/distribution when a primary host or store is blocked.

The marketing news feed is not the authoritative release log: its newest visible posts stop at December 18, 2025, while all major client stores show 2026 releases. Store metadata, installed artifacts and direct-download headers are better current-release evidence.

Latest public news topics were browser-extension per-site split tunnelling (Dec 18, 2025), VLESS XTLS configuration in the cabinet (Nov 18, 2025), Android TV (May 1, 2025), browser extensions (Mar 1, 2025), and Uzbekistan/Portugal locations (Feb 1, 2025).

## Current Legal Entity

Primary registry: Florida Division of Corporations / Sunbiz, `https://search.sunbiz.org/Inquiry/corporationsearch/SearchResultDetail?aggregateId=flal-l20000139395-25c1913a-e867-405f-96af-160ea043ae3f`.

- **PRIVATE NETWORK LABS LLC**, Florida limited liability company.
- Document number `L20000139395`; filed May 22, 2020; status **ACTIVE** on the snapshot date.
- FEI/EIN `30-1238066`.
- Current principal address: 499 S Warren St Ste 618, Syracuse, NY 13202; changed April 8, 2026.
- Mailing address: 2171 Spring Street, Hamilton, NY 13346.
- Registered agent: Florida Registered Agent, St. Petersburg, Florida.
- Authorized member: Vladislav Zdolnikov.
- Annual reports are visible for 2021–2025.

The website and store listings still display the Hamilton mailing address, while Sunbiz now lists Syracuse as the principal address. That is an address-role/update mismatch, not evidence of a different operator.

## TgVPN Lineage And Historical Entity

Official Red Shield history: `https://redshieldvpn.com/en/news/page/5` and the December 2, 2019 “TgVPN team presents Red Shield VPN” post. It explicitly describes Red Shield as the continuation of TgVPN.

Primary ECHR record: `https://hudoc.echr.coe.int/app/conversion/docx/pdf?filename=PRIVATE+NETWORKS+LP+v.+RUSSIA.pdf&id=001-204791&library=ECHR&logEvent=False`.

- The ECHR statement identifies **PRIVATE NETWORKS LP**, Scottish limited partnership `SL030265`, formed in 2017, as the operator of TgVPN.
- It names Vladislav Zdolnikov as a person with control/representative.

UK Companies House:

- Overview: `https://find-and-update.company-information.service.gov.uk/company/SL030265` still labels the partnership Active and shows an overdue confirmation statement.
- Filing history: `https://find-and-update.company-information.service.gov.uk/company/SL030265/filing-history` records an LP6 filing dated August 9, 2023 stating that the limited partnership **has been dissolved**.

The filing-history dissolution record is stronger evidence than the stale-looking overview badge, but the registry UI is internally inconsistent. The Scottish LP is historical and separate from the current Florida LLC.

## Terms, Privacy, Refund And Renewal

### Terms Of Service

Official: `https://redshieldvpn.com/en/tos`, updated September 27, 2025.

- says the service keeps no connection or traffic logs;
- personal/home use only; businesses are told to contact the company;
- caps traffic at **1 TB per account per month** across all devices;
- one account may be used by one individual only; sharing is prohibited;
- server bandwidth is not guaranteed;
- reverse engineering and use “in a manner that competes” with Red Shield are prohibited;
- an account may be terminated without notice and without refund;
- total liability is capped at the amount paid.

Drafting quality is weak: it invokes the repealed EU Data Protection Directive 95/46/EC, contains repeated unrelated “Antivirus” boilerplate and gives an unclear governing-law formula involving the USA, Panama and the country of the connected server.

### Privacy Policy

Official: `https://redshieldvpn.com/en/pp`, last updated February 18, 2023.

It describes processing of name, email, payments and recurring-payment details, VAT country, email campaign events/device OS, chatbot contact/country/connection state, website access logs, cookies/affiliate cookies, diagnostics and an IP address that is analyzed then immediately deleted for network optimization. Third-party payment, email, diagnostic and analytics providers may process personal data and can sometimes be independent controllers. It permits international transfers, acquisition transfers and disclosure to law enforcement/courts under valid process.

The policy says the service is not intended for anyone under 18. That conflicts with store presentation as PEGI 3 / Everyone / Apple 4+, even if store ratings describe content rather than contractual eligibility. The policy also predates the 2026 principal-address change and several recent product/distribution changes.

### Refund Policy

Official: `https://redshieldvpn.com/en/help/description/rp`, updated November 3, 2025.

The hero's “14 days if it doesn't work” line is materially narrower in the legal text:

- refunds are not guaranteed even when every condition is met and may be rejected without explanation;
- processing fees are deducted;
- gifts are never refundable;
- only the first bank-card payment can qualify—no crypto, Telegram Stars or other methods;
- the request must be within 14 days, the account must have exactly one payment and the same card must have been used only once for the service;
- only inability to connect using Red Shield's own apps/extensions can qualify;
- Red Shield alone decides whether its software caused the problem; ISP/state/device/antivirus/firewall/manual-configuration causes do not qualify;
- service usage data must show that the user **never connected**;
- the customer must follow every support request within 24 hours and allow up to 30 days for support to fail to help;
- approved requests can take another 30 days to process.

### Auto-Renewal

Official: `https://redshieldvpn.com/en/help/description/art`, updated July 17, 2023.

- Website/cabinet/Windows/macOS/Android purchases charge the saved card two days before expiry and retry one day before expiry.
- Price changes affect renewal; Red Shield promises an email at least three days before charging but disclaims responsibility for non-delivery.
- Cancellation is in cabinet → Profile → Auto renewal → Disable.
- Changing the primary card requires making a manual subscription purchase with the new card and then selecting it in saved cards.
- Apple subscriptions use Apple's renewal and cancellation system; Red Shield disclaims a separate price-change notice obligation there.

## Trust Surfaces

- **Warrant Canary:** `https://redshieldvpn.com/en/help/description/warrant_canary` claims TgVPN, Red Shield and related companies have transferred “0 bytes” of user information. The page showed no date, signature, hash or independent verification, so it is a static assertion, not a verifiable canary process.
- **Bug bounty:** `https://redshieldvpn.com/en/help/description/bb` offers $100–$5,000+ for reproducible account/infrastructure issues across sites, apps/extensions and servers. It excludes disruption, scanners, clickjacking, missing cookie flags, old client versions, physical/root/social-engineering/brute-force paths and protocol/library vulnerabilities.
- **No-log claim:** appears across store/site/terms, but no current independent no-log or infrastructure audit was found in this pass.
- **Store/static alignment:** Firebase measurement/crash/push components align with the stores' diagnostics/usage disclosures, not with a literal “collect nothing” reading of marketing copy.

## Contradiction And Risk Register

| Surface claim | Qualifying or conflicting evidence | Product consequence |
| --- | --- | --- |
| “Unlimited bandwidth” | Terms cap the account at 1 TB/month. | Put fair-use limits next to the offer, not only in legal text. |
| “14 days for refund if it doesn't work” | Refund policy has many cumulative exclusions and allows rejection without explanation. | The short promise creates avoidable trust and chargeback risk. |
| “We do not collect/analyze user data” | Play/App Store labels, privacy policy and Firebase components describe account, payment, usage and diagnostic processing. | Use precise “no browsing/traffic sale” language instead of a blanket claim. |
| No traffic/connection logs | Refund eligibility uses app/extension/server usage data and the privacy policy analyzes IP transiently. | Explain the exact distinction between content logs, connection metadata, aggregate usage and diagnostics. |
| Store rating PEGI 3 / Everyone / 4+ | Privacy policy prohibits under-18 use. | Contract eligibility and storefront age messaging should agree. |
| Ten devices | Router FAQ recommends only three downstream users/devices and says one individual per account. | Device-limit wording needs to distinguish registered endpoints, household use and fair use. |
| First-party brand trust | Android checkout uses `myrsv.live`; Apple guide asks for generated US identity data; a separate similarly named iOS app exists in Russia. | Stronger verified-domain and official-app identity cues are needed. |
| Simple native app | Many account/help/payment actions eject the user to Chrome. | Reliability can beat polish, but a first-party in-app browser/deep link shell would reduce context switching. |
| Mandatory availability updates | Old versions stop working on short deadlines. | Good anti-blocking agility; also a single forced-update failure can strand users, so redundant update lanes matter. |

## High-Value Lessons For POKROV

1. **Copy the depth, not the rough edges:** one-action home plus power-user routing, masking explanations, latency guidance, category blockers, LAN access, sharing and presets.
2. **Build redundant distribution as a product:** Play + signed direct APK + mirrors + cabinet + bot + browser extensions + manual configs. Every lane needs a verified identity and clear recovery path.
3. **Treat store metadata as release operations:** mandatory-update copy, synchronized direct build and store source stamp show that anti-blocking availability is part of release management.
4. **Use special-purpose location groups:** ordinary recommendations and sensitive-country/Double-VPN exits should not be mixed in one flat selector.
5. **Tie growth rewards to revenue:** one month after first referred payment and gift coupons are stronger economics than install rewards.
6. **Do not copy the deceptive parts:** disguised paywall on Connect, generated Apple identity instructions, off-brand checkout host, contradictory unlimited/refund language, stale legal boilerplate and hostile support gates are liabilities.
7. **Own the trust proof:** publish a dated/signed canary, exact logging/diagnostics table, current independent audit and consistent entity/address/contact story.
8. **Defend the brand in blocked stores:** provide official application IDs, publisher names, signed download hashes and an impersonation warning page.

## Source Index

Primary sources used in this pass:

- `https://redshieldvpn.com/en`
- `https://redshieldvpn.com/sitemap.xml`
- `https://redshieldvpn.com/en/tos`
- `https://redshieldvpn.com/en/pp`
- `https://redshieldvpn.com/en/help/description/rp`
- `https://redshieldvpn.com/en/help/description/art`
- `https://redshieldvpn.com/en/help/description/bb`
- `https://redshieldvpn.com/en/help/description/warrant_canary`
- `https://redshieldvpn.com/en/help/features/redlink`
- `https://redshieldvpn.com/en/help/features/double_vpn`
- `https://redshieldvpn.com/en/help/apps/ios/install`
- `https://redshieldvpn.com/en/news/page/5`
- `https://apple.rsv.today/`
- `https://play.google.com/store/apps/details?id=com.redshieldvpn.app`
- `https://apps.apple.com/us/app/red-shield-vpn/id1476245357`
- `https://chromewebstore.google.com/detail/red-shield-vpn/fmhbdohlogekfmknbhfpbeiphcldcfji`
- `https://addons.mozilla.org/firefox/addon/red-shield-vpn/`
- `https://search.sunbiz.org/Inquiry/corporationsearch/SearchResultDetail?aggregateId=flal-l20000139395-25c1913a-e867-405f-96af-160ea043ae3f`
- `https://find-and-update.company-information.service.gov.uk/company/SL030265`
- `https://find-and-update.company-information.service.gov.uk/company/SL030265/filing-history`
- `https://hudoc.echr.coe.int/app/conversion/docx/pdf?filename=PRIVATE+NETWORKS+LP+v.+RUSSIA.pdf&id=001-204791&library=ECHR&logEvent=False`

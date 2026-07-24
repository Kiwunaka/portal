# HiroVPN - Mobile App Competitor Profile

**Snapshot date:** 2026-07-22<br>
**Depth:** deep in-app audit in LDPlayer + local APK metadata/URL extraction + official site/store/legal checks + live destination checks<br>
**Status:** `DEEP_PASS_COMPLETE_WITH_BLOCKERS` - core product, growth, store/release, web, legal and technical surfaces covered; authoritative current company status, payment routing and the unavailable wheel spin remain explicitly open

## At A Glance

| Field | Observed value |
| --- | --- |
| Product | HiroVPN |
| Android package | `com.hiro.vpn` |
| Installed version | 1.18.0 |
| Store developer | Wolle Development Ltd. |
| Google Play scale | 5M+ downloads, about 217K reviews, 4.7 shown in the installed Play client |
| Latest Play update observed | 2026-07-17; “Добавлены новые языки”, “Исправления и улучшения” |
| Legal entity shown in app | WOLLE DEVELOPMENT LIMITED |
| Registration numbers | Company 3342674; business registration 75957585 |
| Incorporation | Hong Kong, 2023-11-27; CR number confirmed in the official Companies Registry weekly incorporation list |
| Registered address in documents | Unit 1603, 16th Floor, The L. Plaza, 367-375 Queen's Road Central, Sheung Wan, Hong Kong |
| Main funnel | Google Play app -> instant trial -> quests/rewards -> three-tier subscription or reserve-traffic packages |
| Trial observed | 7 days after account sign-in; reward clicks increased it to 12 days without completing the claimed off-platform actions |
| Server claims | 80+ on Ordinary, 100+ on Premium/Legend; 27 location labels observed plus reserve/game special servers |
| Platforms claimed | Android, iOS, Android TV, Apple TV, Windows, macOS, Linux, AppGallery and APK downloads |
| Major differentiator | Aggressive gamified acquisition loop, special “reserve access”, broad platform hub, strong visual system |
| Major risk | Incentivized reviews/helpful-vote manipulation, weak action verification, mislabeled legal documents and contradictory terms |

## Executive Read

Hiro is materially ahead of POKROV in packaging, visual confidence, surface area and growth mechanics. The app feels like a product ecosystem rather than a single connect button: quests, referrals, content rewards, story-like tutorials, three subscription levels, traffic add-ons, special servers, split tunneling, DNS controls, in-app chat and a multi-platform download hub are all merchandised inside one coherent dark/anime design.

The advantage is not uniformly real. Several headline “products” are only coming-soon waitlists. The reward system marks several actions complete merely after opening an external page. The legal section routes labels to the wrong documents, and the documents conflict on governing law and refunds. The most aggressive review-growth mechanics should be treated as a compliance/reputation warning, not a model to copy.

## Store Positioning, Recommendations And Release Pattern

### Google Play snapshot

The [current public Play listing](https://play.google.com/store/apps/details?id=com.hiro.vpn) shows Wolle Development Ltd., 5M+ installs, 4.7 and roughly 217K phone reviews, with the latest update dated 2026-07-17. It claims:

- seven free unlimited days without registration;
- a permanent free allowance of 3 GB each month;
- 100+ servers across 80 countries on 10 Gbps infrastructure;
- double encryption, DNS/IP leak protection, multi-hop and Tor support;
- quests, a daily wheel and rewards;
- up to ten devices.

Several claims are not matched cleanly by the audited Android state. The app showed 1 GB of monthly *reserve* traffic, not a general 3 GB free plan; only 27 country labels were observable; and no explicit multi-hop or Tor control was found in the traversed UI. These may be tier/backend features, but the current client does not substantiate the listing copy.

The public page’s current recommendation rail contains Secure VPN, JumpJumpVPN, Proton VPN, PandaVPN, Cloudflare 1.1.1.1/WARP and Speedify. This is Google’s store merchandising, not a recommendation made inside Hiro.

One visible five-star review literally begins “Here's a positive Google Play review for a VPN app”. That is not proof of who generated it, but it is a low-quality review-integrity signal when combined with Hiro’s in-app review/helpful-vote rewards.

### Apple release cadence

The [official App Store listing](https://apps.apple.com/app/id6746091465) shows seller WOLLE DEVELOPMENT LIMITED and version 1.7.1 dated 2026-06-23. Its visible history contains ten releases from 2026-02-16 through 2026-06-23, roughly one every two weeks:

| Version | Date | Visible product change |
| --- | --- | --- |
| 1.5.2 | Feb 16 | No useful note exposed |
| 1.5.4 | Mar 4 | Kill Switch and quests |
| 1.5.5 | Mar 20 | Stability/performance fixes |
| 1.5.6 | Mar 28 | Referral codes and VPN-core update |
| 1.5.8 | Apr 9 | Desktop QR sign-in and connection-state sync |
| 1.5.9 | Apr 16 | Same feature family plus reliability work |
| 1.6.0 | Apr 30 | New quests, in-app support chat and traffic management |
| 1.6.2 | May 8 | Fixes |
| 1.7.0 | Jun 4 | App security improvement |
| 1.7.1 | Jun 23 | Custom DNS text input, Control Center toggle and UI improvements |

The pattern is important: acquisition mechanics, support and VPN controls ship as small, frequent increments rather than waiting for a large redesign. Official Play exposes only the latest Android update, so an Android historical cadence should not be invented from that page alone.

Apple’s current “You Might Also Like” rail includes Ping VPN, Tuman VPN, LagomVPN, Mirage VPN, Hit VPN, NoDrama VPN, Buddy VPN and Изи VPN. Ping VPN is also installed in this audit environment and will get its own profile.

## Observed User Journey And Health

| Step | Flow | Health | What happened |
| --- | --- | --- | --- |
| 1 | First launch | Friction-heavy | App asks for notification permission and then shows its own blocking explanation insisting notifications are required for correct VPN operation. The audit continued without granting it. |
| 2 | Trial home | Strong | Large glowing connect control, clear protected/unprotected state, trial duration, fastest-server card and quests counter. |
| 3 | Server selection | Strong, claim-heavy | Pull-up server sheet with search, tier filters, fastest choice, reserve access, game server and 27 country labels with very high Mbit/s figures. |
| 4 | Connect/disconnect | PASS | Android VPN consent accepted; France connection became Android-validated and the app showed a protected timer; it disconnected cleanly afterwards. |
| 5 | Sign-in | Mixed | Email OTP + human check, authorized-device QR and Google OAuth are offered. Google sign-in worked, expanded the device allowance from 1 to 3, and unexpectedly auto-connected to Austria after login. |
| 6 | Subscription paywall | Strong merchandising | Year/month/week tabs, three tiers, default Premium emphasis and a 30-day money-back promise. Checkout requires auth, then offers six payment methods. |
| 7 | Quests/rewards | Commercially effective, policy-risky | Wheel streak, rewarded video, referrals, social/content rewards, YouTube, Trustpilot, store-like support votes, Google Maps, Yandex Maps and Telegram tasks. Multiple tasks completed without verifying the requested action. |
| 8 | Product shelf | Attractive but mostly roadmap | Five adjacent security products are presented as if part of an ecosystem, but every tested item is a coming-soon/waitlist page. |
| 9 | Split tunneling/exclusions | Strong | Per-site and per-app always-with/always-without VPN modes, defaults, search and installed-app picker. |
| 10 | DNS / safety controls | Strong | Hiro DNS, Google, Cloudflare, OpenDNS, Quad9 and custom DNS; Kill Switch and subscription-gated ad blocker. |
| 11 | Support | Strong | Embedded chat with a detailed troubleshooting intake, FAQ, bug-report form with optional diagnostics and speed-problem flow entry. |
| 12 | Legal | Broken | Three visible legal labels download mismatched PDFs; the documents contradict each other. |

## Home, Connection And Servers

The home screen uses one dominant glowing circle:

- unconnected: `НЕ ЗАЩИЩЕНО / ПОДКЛЮЧИТЬ / ПРОБНАЯ 7 ДНЕЙ`;
- connected: elapsed timer, `ЗАЩИЩЕНО / ОТКЛЮЧИТЬ`;
- fastest server card displays a country and an asserted Mbit/s figure;
- logged-out promo is “E-mail один ключ входа на всех устройствах”; after sign-in it changes to a limited-time subscription discount banner.

Observed special servers:

- `Резервный доступ` - Switzerland, metered by GB;
- `Игровой сервер` - Austria;
- `Самый быстрый` - automatic selection.

Observed country labels (27): France, Turkey, Finland, Germany, Austria, United Kingdom, Sweden, Netherlands, United States, Italy, India, Switzerland, Poland, Spain, Norway, Japan, Malaysia, Australia, Brazil, Singapore, South Africa, Republic of Korea, United Arab Emirates, Mexico, Canada, Hong Kong SAR and Russia.

The list also has three visual filters: All, a medal/badge tier and a crown tier. The crown-only state showed Brazil in the current snapshot; accessible labels do not name the two icon-only filters, so their exact commercial semantics remain an inference.

Representative evidence:

- [home](raw/hiro-vpn/2026-07-22/screenshots/03-home.png)
- [server list](raw/hiro-vpn/2026-07-22/screenshots/75-server-list.png)
- [connected state](raw/hiro-vpn/2026-07-22/screenshots/85-connected.png)
- [server UI trees](raw/hiro-vpn/2026-07-22/ui/)

## Pricing And Packaging

### Subscription tiers

| Tier | Devices | Server claim | Special value | Week | Month | Year |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| Ordinary | 3 | 80+ | Base tier | 94 RUB | 284 RUB | 1,812 RUB |
| Premium | Up to 5 | 100+ | Reserve access | 132 RUB | 379 RUB | 1,860 RUB |
| Legend | 10 | 100+ | Highest tier; additional shield icon shown | 197 RUB | 569 RUB | 2,707 RUB |

All observed prices carried a `-5%` badge. Premium is visually marked as popular and is the default expanded choice. Year pricing makes Premium only 48 RUB more than Ordinary, an aggressive decoy/upsell structure.

Payment selector after authentication:

- Google Play;
- Russian card;
- SberPay;
- SBP;
- foreign card;
- cryptocurrency.

No purchase was attempted. Evidence: [year paywall](raw/hiro-vpn/2026-07-22/screenshots/57-paywall.png), [payment methods](raw/hiro-vpn/2026-07-22/screenshots/63-payment-methods.png).

### Reserve access traffic

The app gives an observed 1 GB monthly reserve allowance and sells non-expiring traffic packages:

| Package | Traffic | Observed price |
| --- | ---: | ---: |
| Light | 50 GB | 274 RUB |
| Standard | 100 GB | 369 RUB |
| Maximum | 300 GB | 806 RUB |

Copy says purchased GB have no daily/time limit and remain until consumed. The FAQ claims reserve access can work when mobile internet is restricted to “white-listed”/government sites. Evidence: [traffic packages](raw/hiro-vpn/2026-07-22/screenshots/65-reserve-increase.png).

## Growth Engine And Quest Economy

### Wheel and repeat loop

- Wheel of fortune once per day.
- Seven-day consecutive-spin streak.
- Guaranteed one subscription day on day seven.
- Current account/device was on an approximately 23-hour cooldown, so the actual wheel/spin animation was not reachable without resetting state.

### Rewarded video

- Promises bonus VPN hours for short ads; more videos mean more hours.
- The live ad request failed with a branded “Реклама не загрузилась” retry page.

### Content-for-service barter

Users can submit public VK, X/Twitter, Facebook, Dzen, vc.ru, Instagram or YouTube content. Hiro checks visible reach within 48 hours:

| Public likes/views | Reward |
| ---: | ---: |
| 200-500 | 15 VPN days |
| 500-2,000 | 30 VPN days |
| 2,000-10,000 | 60 VPN days |
| 10,000+ | 90 VPN days |

Private profiles, screenshots of statistics and messengers without public metrics are rejected. Evidence: [content-reward rules](raw/hiro-vpn/2026-07-22/screenshots/73-submit-content-links.png).

### Referral loops

- Simple share quest: invite a friend and receive one free VPN day.
- Account referral: share a promo code; after the friend buys, both sides receive 14 free days.
- The personal referral code itself is intentionally not retained.

### Competitor-switch offer

The official site runs a direct acquisition offer for customers whose current paid VPN stopped working. The user sends a screenshot of a receipt, email or account page to Hiro’s in-app chat and Hiro promises to activate a discount. Eligible proof is any active paid VPN or paid self-hosted VPN with more than one month remaining; free products, Hiro itself and subscriptions shorter than one month are excluded. This is a sharp, support-assisted conquest funnel aimed at a user at the exact moment a competitor fails.

### Affiliate machine

The embedded `hiroearn.com` destination is a full partner program, not merely the consumer referral code:

- 50% of a new weekly-plan sale, 45% of a new monthly-plan sale and 40% of a new annual-plan sale;
- 30% of every renewal across those plans;
- 45-day attribution cookie;
- weekly payouts with a $50 minimum through PayPal, bank transfer or an agreed alternative;
- application review within 24 hours, a personal manager, promo codes, dashboards and real-time click/subscription/payout reporting;
- supplied banners, social video, email templates, post copy, landing/pre-landing pages and a media kit;
- accepted traffic explicitly includes websites, YouTube, Instagram, VK, Telegram, email, contextual/targeted advertising and traffic arbitrage; click fraud, spam and click sabotage are prohibited.

This explains how Hiro can scale much faster than an app relying on organic store search alone: it turns publishers and arbitrage teams into a recurring-revenue sales force. The affiliate page itself is inconsistent about footprint, claiming 100+ countries in one section and more than 70 in another, while the main site says 50+ and Play says 80 countries.

### Review/social quests and observed verification defect

| Quest | Destination | Promised reward | What the audit observed |
| --- | --- | ---: | --- |
| Subscribe on YouTube | `youtube.com/@HiroVPNapp` | 1 day | Marked complete after opening the channel; no subscription performed |
| Rate on Trustpilot | `trustpilot.com/review/hirovpn.com` | 1 day | Marked complete after opening the page; no review written |
| Like five agreeable store comments | Google Play app page | 2 days | Marked complete after opening Play; no likes/helpful votes made |
| Review in Google Maps | HiroVPN Hong Kong listing | 1 day | Marked complete after opening Maps; no review written |
| Review in Yandex Maps | HiroVPN Yandex listing | 1 day | Already marked complete in the inherited account state; card copy incorrectly repeats the friend-invite text |
| Subscribe to Telegram | `t.me/hirovpnblog` | 1 day | Marked complete after opening the public preview; no Telegram subscription performed |

The trial showed 7 days immediately after account sign-in and 12 days after these outgoing-link tests. All five newly exercised tasks showed `Выполнен`; the immediate aggregate increase was five days, so individual server-side credit timing cannot be assigned more precisely without invasive traffic inspection.

This is the clearest reason not to copy Hiro literally. Trustpilot's own live page says companies are not allowed to offer incentives for reviews. Hiro's app does exactly that. The Play “like helpful reviews” quest is also designed to manipulate review visibility.

Current public snapshots reached from the app:

- Google Play: 4.7, about 217K reviews, 5M+ downloads.
- Trustpilot: 3.5 from 22 reviews; claimed profile since April 2026; “No recent history of asking for reviews” shown despite the in-app incentive.
- Google Maps: 4.9 from 11,460 reviews at the Hong Kong registered-office address.
- Telegram channel: 85,440 subscribers.

Evidence: [Trustpilot profile](raw/hiro-vpn/2026-07-22/screenshots/98-trustpilot-profile.png), [Trustpilot incentive warning](raw/hiro-vpn/2026-07-22/screenshots/99-trustpilot-incentive-policy.png), [Google Maps listing](raw/hiro-vpn/2026-07-22/screenshots/106-google-maps-listing-clean.png), [Telegram channel](raw/hiro-vpn/2026-07-22/screenshots/111-telegram-channel.png), [Play listing UI tree](raw/hiro-vpn/2026-07-22/ui/102-likes-external.txt).

## Product Shelf: Real Capability Versus Roadmap

The “Products” tab presents five adjacent privacy/security products. Every tested card is a coming-soon page, not a working tool:

| Product card | Promised value | Actual state |
| --- | --- | --- |
| Private Email | Anonymous mailboxes for registrations, spam/leak reduction | In development; notify-on-launch CTA |
| Virtual Numbers | Temporary numbers for one-time registration and verification | Coming soon; notify-on-launch CTA |
| Password Manager | Encrypted storage and unique password generation | Coming soon |
| Dedicated IP | Personal clean IP avoiding blacklists | “Almost ready” |
| Leak Alerts | Email/password leak alerts and protection recommendations | Coming soon |

This corrects an important first impression: Hiro does not currently issue temporary App Store accounts or working virtual-number/email products in the audited build. It merchandises a roadmap as an ecosystem.

The four numbered chips above the shelf are Instagram-style tutorials, not products. They teach server-sheet gestures, fastest-server selection, changing country on failure and email-based multi-device sign-in.

Evidence: [product shelf](raw/hiro-vpn/2026-07-22/screenshots/08-tab1.png), [private email](raw/hiro-vpn/2026-07-22/screenshots/09-private-email.png), [virtual numbers](raw/hiro-vpn/2026-07-22/screenshots/10-virtual-numbers.png).

## Routing, Exclusions And DNS

Hiro has two split-routing modes for both websites and installed apps:

- Always without VPN.
- Always with VPN.

Observed default always-without-VPN sites: `2ch.hk`, `2ch.org`, `2ch.su`.

Observed default always-with-VPN utilities: `payload.network`, `2ip.ru`, `2ip.to`, `myip.ru`, `internet.yandex.ru`, `ip.nic.ru`, `reg.ru`, `pr-cy.ru`, `2whois.ru`, `yoip.ru`, `ipsee.ru`, `ip-ping.ru`, `sweb.ru`.

The installed-app picker explains why package-list access is needed, calls it optional and claims the data is not transmitted or used for advertising/analytics.

DNS choices:

- Hiro default;
- Google DNS;
- Cloudflare DNS;
- OpenDNS/Cisco;
- Quad9;
- custom named DNS address.

Evidence: [always without VPN](raw/hiro-vpn/2026-07-22/screenshots/19-tab3.png), [always with VPN](raw/hiro-vpn/2026-07-22/screenshots/20-exclusions-always-vpn.png), [app picker](raw/hiro-vpn/2026-07-22/screenshots/23-app-picker-list.png), [DNS](raw/hiro-vpn/2026-07-22/screenshots/37-dns.png).

## Support, Education And Settings

### FAQ answers captured

- Subscription level rises by buying a weekly package; remaining days stay and a week is added.
- No money is charged for the free trial.
- “White lists” are addressed through reserve access, described as bypassing mobile-internet speed restrictions.
- Privacy answer: no activity logs, foreign company, profit comes from subscriptions rather than selling data.
- Additional device: register, install, sign in under Profile.
- Cancellation path: Settings -> Subscription -> Management -> Change plan -> Cancel subscription.

### Embedded support chat

The opening message asks for device, client app, Wi-Fi/mobile comparison, city, ISP, tested countries, reserve-access result, version and whether only government sites work. It points users to `HiroApp.org` for the latest build. This is unusually good structured support intake.

### Best-configuration test

The feature says it tests 54 device/region configurations in roughly seven minutes to find the best speed/stability balance. The audit cancelled at Android VPN consent to avoid a prolonged network/CPU run.

### Bug reporting

The report form accepts free text and offers diagnostics containing running processes, installed apps, memory, CPU, battery state and logs. Nothing was submitted.

### Speed-problem flow

The entry opens a bottom sheet explaining that Hiro will turn the VPN connection on automatically, with two actions: “Test speed” and “Close”. The audit stopped before the test because it would start a network run and the screen does not explain what measurements or identifiers will be uploaded. No diagnostics were submitted.

### Kill Switch

The toggle is off by default. Enabling it first shows a warning that the feature is for experienced users and that network services may remain unavailable until VPN recovery. Confirmation toggles the feature inside Hiro without opening Android's Always-on VPN/lockdown settings; both `always_on_vpn_app` and `always_on_vpn_lockdown` remained unset, and there was no active `tun0` interface while disconnected. This therefore appears to be an app-managed protection mode, not Android's native lockdown switch. The audit restored the toggle to off immediately after inspection.

### Languages and themes

Twenty-two languages were visible: Russian, English, German, Spanish, French, Italian, Dutch, Chinese, Japanese, Korean, Vietnamese, Indonesian, Malay, Thai, Hindi, Turkish, Ukrainian, Polish, Brazilian Portuguese, Arabic, Persian and Urdu. Dark and light themes are offered.

Evidence: [support chat](raw/hiro-vpn/2026-07-22/screenshots/46-support-chat.png), [FAQ UI trees](raw/hiro-vpn/2026-07-22/ui/), [best-config consent/background](raw/hiro-vpn/2026-07-22/screenshots/35-best-configuration.png), [speed-problem sheet](raw/hiro-vpn/2026-07-22/screenshots/118-speed-problem.png), [Kill Switch warning](raw/hiro-vpn/2026-07-22/screenshots/119-kill-switch-result.png), [enabled state](raw/hiro-vpn/2026-07-22/screenshots/120-kill-switch-enable-result.png), [restored-off UI evidence](raw/hiro-vpn/2026-07-22/ui/121-kill-switch-restored-off.xml).

## Platform And Distribution Hub

The in-app “All platforms” screen links to a permanent Google Cloud Storage hub: `https://storage.googleapis.com/hirovpn/start.html`.

Actual hub routing observed from the current page:

| Visible platform | Destination/state |
| --- | --- |
| Google Play | `play.google.com/store/apps/details?id=com.hiro.vpn` |
| Android APK | `https://hiro.s3.regru.cloud/HiroApp_latest.apk` |
| Huawei AppGallery | Routes to the generic AppGallery home, not a Hiro deep link |
| Android TV | Same Google Play package as Android |
| Android TV APK | Same `HiroApp_latest.apk` as Android |
| macOS | `https://hiro.s3.regru.cloud/HiroApp_latest.dmg` |
| Windows | `https://hiro.s3.regru.cloud/HiroApp_latest.exe` |
| Telegram | `@HiroVpnBot`, currently showing about 21.3K monthly users and promising links for iOS/Android/Mac/Windows/Linux/TV |
| iOS | Visible in the old hub but not exposed as a working anchor in the fetched page; the main site links to App Store ID `6746091465` |
| Apple TV | Visible text but no working anchor exposed in the fetched page |
| Linux | Visible text but no working anchor exposed in the fetched page |

The App Store record is a universal iPhone/iPad/Mac build, but its compatibility section does not list Apple TV. Therefore “all platforms” is partly a marketing shelf: several buttons are direct installers, while AppGallery is misrouted and Apple TV/Linux are currently unsubstantiated by a working hub link.

Read-only HTTP metadata on 2026-07-22 showed the rolling Android APK last modified 2026-07-17 (about 111 MB), Windows installer 2026-07-07 (about 76 MB) and macOS DMG 2026-07-03 (about 75 MB). The generic `latest` filenames hide version numbers, but the timestamps show active cross-platform delivery within the same month. Installers were not downloaded or executed merely to discover internal version metadata.

Marketing claims on the same page include seven-day trial, “1 ms”, no logs, VLESS, 24/7 chat, global resource access, AES-256, shopping savings, Kill Switch and ad blocking. The “1 ms” claim has no methodology attached.

Evidence: [platform screen](raw/hiro-vpn/2026-07-22/screenshots/50-all-platforms.png), [download hub top](raw/hiro-vpn/2026-07-22/screenshots/51-platform-ios.png), [download hub continuation](raw/hiro-vpn/2026-07-22/screenshots/52-download-hub-scroll.png).

## Legal Documents And Contradictions

The Hong Kong Companies Registry’s official list for the week of 2023-11-27 records “Wolle Development Limited”, CR number 3342674, incorporated on 2023-11-27. The company’s business registration number 75957585 and registered-office address are repeated consistently across Hiro’s terms, offer, privacy policy and both major app stores. A current-status lookup in the Registry’s interactive e-Services portal is still required before calling the company presently live; a secondary directory updated in May 2026 reports it as live, but that is not promoted to authoritative proof here.

The app visibly identifies WOLLE DEVELOPMENT LIMITED and the two registration numbers, but the three buttons are wired to confusing/mismatched filenames:

| In-app label | Downloaded file | Actual content |
| --- | --- | --- |
| Public offer | `terms_of_service.pdf` | Bilingual Terms of Service dated 2025-02-17 |
| License agreement | `user_agreement.pdf` | Russian user agreement effective 2025-03-25 |
| Privacy policy | `offer.pdf` | Russian public offer, not a privacy policy |

Material conflicts:

- Terms of Service: Hong Kong law and exclusive Hong Kong courts.
- User Agreement: Russian Federation law.
- Public offer: unresolved matters under Russian Federation law.
- Terms promise a 30-day money-back guarantee for first-time purchases with exceptions.
- User Agreement says unused-period refunds are not provided except where law requires.
- The app paywall repeats the 30-day guarantee.
- The “Privacy policy” destination does not provide a privacy policy at all.

An actual bilingual privacy policy does exist at [`files.downloadhiro.app/public/docs/privacy_policy.pdf`](https://files.downloadhiro.app/public/docs/privacy_policy.pdf) and is linked from Apple, but the Android app’s privacy button does not open it. The policy says Hiro collects optional email, app version, aggregated connection success/country/ISP, total transferred bytes and anonymous crash/speed/technical diagnostics. It allows sharing aggregated analytics, referral-program data and data with service providers. This directly conflicts with the main website’s categorical claim that user data is “never collected or stored” and with Apple’s store declaration “Data Not Collected”. Google Play is closer to the policy: its current Data safety panel says personal information may be collected.

Runtime metadata also shows AppsFlyer and advertising-ID permissions. The store declarations, runtime SDK surface and real policy therefore need reconciliation before the broad no-data/no-tracking marketing can be trusted.

Local documents: [`raw/hiro-vpn/2026-07-22/documents/`](raw/hiro-vpn/2026-07-22/documents/).<br>
Evidence: [legal sheet](raw/hiro-vpn/2026-07-22/screenshots/28-terms.png), [button-to-file downloads](raw/hiro-vpn/2026-07-22/screenshots/29-public-offer-destination.png), [license download](raw/hiro-vpn/2026-07-22/screenshots/31-license-destination.png), [privacy-label download](raw/hiro-vpn/2026-07-22/screenshots/32-privacy-destination.png), [actual privacy PDF](raw/hiro-vpn/2026-07-22/documents/privacy_policy.pdf).

## Technical Surface

APK metadata retained under [`raw/hiro-vpn/2026-07-22/scrapes/`](raw/hiro-vpn/2026-07-22/scrapes/):

- target SDK 36;
- VPN service and internet permissions;
- notification, camera and advertising-ID access;
- AppsFlyer observed at runtime;
- public/API domains include `api.hirovpn.com`, `api.hellohiro.ru`, `downloadhiro.app`, `files.downloadhiro.app`, `chatwoot.wollebuy.com`, `hirovpn.com`, `hirvpn.com`, the Google Storage hub and legal PDFs;
- social/review destinations match the live UI checks;
- several content/news-like domains are embedded under configuration keys naming them as alternate API bases rather than visible editorial pages: `infomagazine.space`, `moscownews24.ru`, `newlenta24.online`, `pitertv24.ru`, `rocketnews.site`, `sportvideo24.ru`, `tvnews7.ru`, `krym-toury.ru`. This strongly suggests resilient/fallback API routing under unrelated-looking domains; no probing of those third-party endpoints was performed.
- the production release binary contains credential-shaped configuration values, including an OAuth client secret and a Telegram bot token. Values were neither retained in the worktree nor tested. This is a concrete mobile-secret-management failure even if a provider later restricts or revokes those credentials.

Raw launch logs containing generated device/advertising identifiers are not suitable for retention or handoff. Only redacted technical extracts should be kept in the final evidence set.

## What POKROV Should Copy

- One dominant connect state with obvious protection status and session timer.
- Pull-up server sheet with search, fastest route and clearly named special-purpose routes.
- Story-like micro-tutorials embedded where users discover features.
- Structured in-app support intake and rich FAQ.
- Per-site and per-app routing with a clear permission rationale.
- DNS selection and custom DNS.
- A coherent subscription comparison with meaningful device/server limits.
- Multi-platform download hub with a stable permanent link.
- A competitor-switch offer triggered when another paid VPN fails, with proof reviewed privately by support and a clearly bounded discount policy.
- A partner program with recurring commissions, a clear attribution window, ready-made creative assets and transparent reporting, provided payouts are based on collected revenue and traffic rules are enforced.
- A small, roughly biweekly release rhythm that alternates growth, support, reliability and control features.
- A truthful roadmap/waitlist area, but explicitly label future products as future products before the user taps.
- Reward loops for legitimate actions that can be verified without manipulating public reviews: onboarding completion, referral purchase, feedback survey, bug report quality, streaks and product education.

## What POKROV Should Not Copy

- Incentives for Trustpilot/Maps/store reviews or helpful votes.
- Marking off-platform actions complete merely because a destination opened.
- Fake precision such as universally huge Mbit/s figures or “1 ms” without a reproducible test basis.
- Legal labels that lead to the wrong documents.
- Contradictory governing-law/refund promises.
- Store/privacy declarations that say “no data collected” while the real policy lists connection, ISP, traffic-volume, diagnostic and referral data.
- Platform buttons that lead nowhere or to a generic store home.
- Conflicting server/country counts across the app, Play, website and affiliate landing page.
- Presenting waitlist features as if they are already delivered.
- Claiming notifications are mandatory for VPN correctness unless technically true.
- Collecting broad diagnostics without granular preview/consent.

## Remaining Hiro Work

- `BLOCKED_BY_COOLDOWN`: capture the actual wheel/spin/reward screen after its daily timer expires, or in a fresh isolated app state that does not destroy user data.
- Map the six payment destinations without creating orders or exposing account/payment data.
- Determine downloadable desktop build versions from signed installer metadata if a lightweight official manifest appears; the public URLs expose only `latest` filenames and large binaries were intentionally not downloaded.
- Verify current company status through the Hong Kong Registry’s interactive e-Services search; official incorporation/name/CR number are already confirmed.
- Find an authoritative Android version-history source if Hiro publishes one; official Play exposes only the latest release.
- Determine the operational fallback order for the alternate API domains only from safe first-party documentation or redacted runtime evidence; do not probe third-party infrastructure.
- Review current Play reviews and support response patterns without interacting.

## Evidence Boundaries

- No purchase, public review, rating, helpful vote, social subscription, public post or support message was made.
- A Google-linked Hiro account was created with explicit user authorization; the email address and account/QR/referral artifacts are excluded from this worktree.
- One France VPN connection was tested and disconnected. No raw endpoint credentials, session identifiers or provider payloads are retained in this profile.

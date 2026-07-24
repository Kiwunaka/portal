# GnuVPN — Website, Store, Legal And Channel Notes

Snapshot: 2026-07-22<br>
Status: `IN PROGRESS` — durable working notes; unresolved items are labelled rather than guessed.

## Official Surfaces

- Website: https://gnuvpn.com/
- Downloads: https://gnuvpn.com/downloads
- Registration / plan checkout: https://gnuvpn.com/register
- Privacy Policy: https://gnuvpn.com/page/privacy-policy
- Terms of Use: https://gnuvpn.com/page/terms-of-use
- Refund FAQ: https://gnuvpn.com/faq/what-is-your-refund-policy
- Referral program: https://gnuvpn.com/referral
- Payment instructions: https://gnuvpn.com/instructions
- Google Play: https://play.google.com/store/apps/details?id=com.gnu.vpn
- Apple App Store: https://apps.apple.com/us/app/id1668762886
- GitHub organization: https://github.com/gnuvpn
- Telegram channel: https://t.me/gnuvpn
- eSIM cross-sell: https://esimsecure.com/

## Product And Pricing Claims

The public site currently leads with a `$3.49/month` annual-plan equivalent, up to five devices, 55+ countries with monthly additions, six years of protection, kill switch, a 100% money-back guarantee and referral points valued at one US cent each. The installed Android selector exposed 59 countries.

Public web plan cards observed:

| Term | Public price | Effective monthly | Notes |
| --- | ---: | ---: | --- |
| 1 month | `$6.99` | `$6.99` | Apple US in-app price matches this amount |
| 3 months | `$17.99` | `$5.99` | Site says 14% saving |
| 6 months | `$26.99` | `$4.49` | Refund window differs from hero promise |
| 1 year | `$41.99` | `$3.49` | Main advertised anchor |
| 2 years | `$66.99` | `$2.79` | Lowest observed monthly equivalent |

The registration catalogue also contains a first-month discount and bundled eSIM+VPN offers (5 GB/one month, 10 GB/six months, 20 GB/one year). A Russian-geography checkout rendered a one-month amount of `360`, but its currency label was not reliably exposed by the parser, so the currency remains `UNVERIFIED` rather than inferred.

Checkout guidance supports local-card/P2P flows and crypto, including USDT, Bitcoin, TRON and Litecoin; a payment-instruction hub also names Visa/Mastercard and PayPal. Some flows tell the customer to transfer the exact amount, omit payment comments and provide a screenshot if confirmation is delayed. No payment was initiated.

## Refund Detail Versus Hero Copy

The broad “100% money-back guarantee” message is materially qualified in the official refund FAQ:

- one-month plan: request within three days;
- six-month plan: request within seven days;
- twelve-month plan: request within fourteen days;
- only one refund is allowed; later repurchases are not eligible;
- refunds normally return to the original payment method;
- crypto refunds use the USD value paid less network/processing commission;
- prepaid/gift-card refunds depend on the provider;
- Google Play and App Store purchases use the store refund process, not GnuVPN's direct guarantee.

The onboarding promise does not expose these limits before account creation.

## Distribution Footprint

The official downloads page distributes:

- Windows 11/10 latest 1.3.9 and a separate older-Windows 1.3.6 build;
- macOS latest 1.3.8 plus a separate 1.3.6 legacy build;
- iOS 1.8.8 via App Store;
- Android 1.8.7 as a direct GitHub APK and via Google Play, Huawei AppGallery and Xiaomi GetApps;
- Ubuntu 18–20, Ubuntu 21–22 and Debian packages at 1.2.8.

The downloads page says iOS 12+ and says the app is unavailable in the Russian App Store and mainland China. The current Apple listing reports iOS/iPadOS 17.6+, so the website compatibility statement is stale or otherwise inconsistent.

The public GitHub organization contains five repositories. Four are effectively binary-release containers with a one-commit visible source tree:

| Repository | Release count | Latest public release at snapshot | Cadence signal |
| --- | ---: | --- | --- |
| `gnuvpn/gnuvpn` | 64 | Android 1.8.7, 2026-06-05 | Eight Android releases from 2026-01-29 through 2026-06-05; roughly every 2–4 weeks |
| `gnuvpn/gnudesktop` | 28 | Windows 1.3.9, 2026-05-22 | Four 2026 releases; tags 1.3.6 and 1.3.7 were published out of version order |
| `gnuvpn/gnuvpnmacos` | 20 | macOS 1.3.8, 2026-05-09 | Three 2026 releases, about every two months |
| `gnuvpn/gnuvpnubuntu` | 8 | Linux 1.2.8, 2023-07-31 | Public Linux release line has been dormant for almost three years |

Recent Android APK releases grew from about 104 MB at 1.7.9 to about 130 MB at 1.8.7. Release notes show a staged growth loop: trial without registration, improved push/in-app messaging, WireGuard/Amnezia work, UI/UX and stability. The GitHub build is an installable artefact channel, not meaningful open-source disclosure.

Apple's public version history is even more aggressive: ten listed updates from 2026-01-05 through 2026-07-03, including anonymous registration, a “Review Us” feature, trial plans, eSIM work, push/in-app messaging and repeated AmneziaWG/UI/stability iterations. Several versions reuse near-identical release notes.

Xiaomi GetApps had a live version 1.8.7 listing updated 2026-06-09, four days after the Google Play/GitHub release. It showed only 100+ GetApps downloads, a 4.0 rating and a 123.5 MB package. Its copy is stale: it still advertises 25 countries, “all” protocol types and absolute no-collection/no-sharing language. Huawei AppGallery destination `C108634005` resolves, but its client-rendered metadata could not be independently extracted in this pass; version/state remain `BLOCKED_BY_RENDERING`.

## Store Positioning And Recommendation Graph

### Google Play

At the snapshot, Google Play showed 1M+ downloads, about 4.4 stars, roughly 22K reviews, an Everyone rating, in-app purchases and an update date of 2026-06-05. The current What's New text names split tunnelling, UI/UX, speed/stability and bug fixes.

The listing claims support for PPTP, OpenVPN, WireGuard/Amnezia, SoftEther, SSTP, IPsec, IKEv2/IPsec and L2TP/IPsec. The installed Android UI and package only confirmed OpenVPN, SoftEther and AmneziaWG. The wider list appears to describe the cross-platform portfolio, not the observed Android app.

Google's similar-app rail exposed JumpJumpVPN, Turbo VPN, Proton VPN, Octohide, NordVPN and AVG Secure VPN. “More by this developer” exposed Your ERP, Gnu Adapter Softether Amnezia and Bitcoin OX Crypto Wallet.

Sample review themes observed without interacting:

- a 2026 complaint that the free service worked and the paid service stopped; the developer recommended a newer WireGuard option or changing proxy;
- ease-of-use praise;
- historical complaints that payment was compulsory;
- an anomalous five-star “pricing high” review whose text says the author had not used the product and the rating should not influence others.

### Apple App Store

The current US Apple listing is 18+, contains advertising, offers in-app purchases, reports ten languages and showed 4.5/5 from 96 ratings. US prices include `$6.99` for one month and `$41.99` for one year.

The four featured five-star reviews form a review-integrity warning, not proof of manipulation: all are dated 2024-09-10, use unusually formulaic keyword-heavy language, repeat nearly the same benefits/server examples and received the same one-line developer reply on 2024-10-16. One praises one-tap Pakistan access even though Pakistan is not present in the current Android 59-country list. Treat the visible rating as weak product evidence.

Apple's recommendation rail exposed SwizzVPN, Stark VPN, VPN 365, Nive, VPN Pro, VPN – Super Smart Proxy, Rapid VPN, Uranus VPN Unlimited, Light VPN Proxy and FREE VPN APP.

Apple privacy labels say user content may be used to track the user across other companies' apps/sites; email can be linked to identity; purchases, precise/coarse location, support content, usage data and diagnostics may also be collected. This is much broader and clearer than the Android app's “not personal data” tooltip.

## Legal Entity And Terms

The Terms, Privacy Policy and both app stores name Portuguese company **GNUAPP UNIPESSOAL LDA** as the contracting developer/controller. The Terms apply Portuguese law and exclusive Portuguese-court jurisdiction subject to mandatory consumer law.

Current corporate registry status remains `BLOCKED_BY_ACCESS`: the legal entity is consistently named across first-party contracts and both stores, but a current exact-company status certificate from the official Portuguese registry has not yet been obtained. Store/legal identification is not being mislabelled as proof of current registry standing.

The Terms require users to be 18+ and reserve the right to request age proof. The installed Android registration route had no age gate or visible terms/privacy consent. Google Play's Everyone rating conflicts with the 18+ contract; Apple's 18+ rating matches it.

The Terms permit free and paid service, optional trials and recurring billing. If payment details are supplied for a trial, billing may start automatically after trial expiry unless cancelled. The observed Android seven-day trial required no payment method, so that specific account appears to expire rather than auto-renew. Web subscriptions are cancelled through Account → Subscription Plan → Stop auto renewal → reason/confirmation.

Google Play/App Store purchases are described as platform-bound and unavailable on desktop/browser, whereas direct web plans are positioned as multi-device access. This distinction should be clearer before checkout.

Liability is capped at fees paid in the preceding twelve months to the extent legally permitted. GnuVPN can suspend for misuse and prohibits probing, brute force, vulnerability exploitation, DoS and compiling/distributing its VPN IP list. Product updates can be automatic.

No visible “Last Revised” date was rendered despite the Terms referring to one.

## Privacy And Disclosure Contradictions

The privacy policy says GnuVPN does not collect browsing history, traffic contents or DNS-query contents, but it does describe collecting account identity/payment data, successful connection date, chosen VPN location, general origin country or ISP and aggregate transferred megabytes. Optional diagnostics can include connection failures, speed tests, crashes, usability and VPN diagnostics.

Key conflicts:

1. The policy says users are asked at activation whether to share diagnostics and can change the choice later. No such activation prompt appeared; Logging was enabled by default.
2. The app says advertising-data collection sends device/user data to Google services while claiming cookies/device identifiers are not personal data.
3. Google Play says “no data collected” while also declaring sharing of Location, Messages and other categories, account deletion and independent security review. This conflicts with account creation, the privacy policy and in-app defaults.
4. The policy names Google/Firebase-class analytics and platform crash providers, but the installed package also contains Adjust and Facebook SDK integrations that are not clearly named in the policy.
5. The policy opens with the Portuguese company as controller, then separately says GnuVPN is headquartered/registered in Saint Vincent and the Grenadines without naming an entity, and also describes the Portuguese company as an affiliate. The controller chain is internally confusing.
6. The App Store description says no data is collected, stored or shared with third parties, while Apple's privacy labels declare tracking, linked email and multiple analytics categories.

The live public website also loads Google Tag Manager, Meta Pixel and Firebase/Google analytics code. Their presence does not prove what events are transmitted, but it reinforces the need for a precise vendor/event disclosure rather than the FAQ's absolute “does not collect any data” wording. Tracking IDs and configuration values are deliberately not retained.

## Help Centre And Internal Instruction Map

The current English FAQ index links **43 detail pages**. The full route inventory was checked in the owner-selected Chrome browser on 2026-07-22. The content is broad enough to function as sales enablement, troubleshooting, retention and account documentation, but it is not synchronized with the Android build.

### Referral Program — Five Pages

1. **How to work with the referral program:** any registered web user can create and share a link. The referred user must be new or have an expired subscription; a paid purchase triggers bonuses. Points can pay for plans or be transferred to another registered account.
2. **Types of rewards:** one point equals one US cent; the referrer receives 10% of the purchase and the new customer 30%, while the page reserves the right to change rates and reward types.
3. **What happens after entering an email:** point transfers validate that the recipient is registered, email a confirmation code to the point owner and credit the named account only after the code is entered. If the address is unknown, the sender is prompted to share a referral link.
4. **Personal-account sections:** balance, accrual/write-off history, invited-user list, support, rules, unique referral link, copy/share action, point transfer and a points field at checkout.
5. **Main rules:** both parties receive their first bonus only after the referred user's purchase; the referrer can earn again on renewals, while the referred user does not receive the 30% again.

This is a materially richer loop than the Android app exposes. It combines acquisition, stored-value credit, repeat-purchase incentive and person-to-person transfers. It also means the account holds referral relationships and invited users' email addresses, which sits awkwardly beside the FAQ's “no personal information” claim.

### Setup, Connection And Account Instructions — Eleven Pages

- **Getting started** presents a web-first paid funnel: Get Started → email → plan/payment → optional referral code → email credentials → download → choose from 55+ countries → connect.
- **Mobile setup** says registration must be confirmed by email, then a plan and payment method selected, and lists only OVPN and SoftEther.
- **PC setup** offers installer-first and web-first paths, requires email confirmation/payment and still says only 24+ countries.
- **Location choice** claims Recent, Favorites and All views plus multiple servers per country and closest-server choice.
- **Login** documents password login or a passwordless email magic link on the website.
- **Account deletion** documents App → Menu → Account → Delete, then email-link confirmation, session termination and deletion of email, password hash and subscription history. It was not executed because it is destructive.
- **Subscription benefit** is generic multi-device/multi-OS/global-location copy.
- **Expiry notification** promises an in-app warning five days before expiry plus email.
- **App errors** contains no diagnostic tree; it only redirects to support.
- **Support** only redirects to the website Email Us action.
- **Service limits** promise unlimited traffic/no server throttling and prohibit illegal activity, malware and copyright violations.

Observed drift is substantial: the live Android registration activated a no-card seven-day trial immediately, did not require email confirmation and connected while the account was explicitly unconfirmed. The current build has 59 countries, no visible Recent/Favorites/server-instance views and offers AmneziaWG in addition to OpenVPN and SoftEther. The PC guide's 24+ and mobile guide's 55+ counts conflict with each other and with the app.

### Security, DNS And Verification — Eleven Pages

- Three basic explainers define VPN purpose/operation and IP replacement.
- The WebRTC page recommends disabling WebRTC when unused and claims a VPN hides the public IP while exposing only a local address.
- The DNS-country page recommends Google Public DNS or Cloudflare and says foreign DNS geolocation is normal. It visibly contains unresolved citation placeholders (`[web:2][web:3]`).
- The DNS explainer gives `nslookup`/`host` examples.
- The IP-check pages tell users to verify that both the address and country change after enabling VPN/proxy.
- **Do you track my actions?** says GnuVPN collects no user data, stores no activity or connection logs and shares no diagnostic data with third parties.
- **Do we save logs?** says no personal information is stored and the service has no mandatory registration or personal accounts.
- **How secure is GnuVPN?** makes only a generic SoftEther encryption/authentication claim despite the multi-protocol product.
- **Can GnuVPN be trusted?** cites a ten-plus-year international team, certification/testing, guaranteed quality and “full protection.”
- Four Verified-App pages say the Play shield proves independent VPN-specific review, full Google Play compliance, accurate/obeyed data practices and an additional audit.

The last two sets of claims overreach the available evidence. The privacy policy, account behaviour, default logging/ad-data controls, Apple privacy label and embedded SDKs disprove “no data”/“no accounts.” The official App Defense Alliance record confirms an approved Legacy MASA assessment, but does not validate every Data Safety declaration or expose the tested version/report.

### Payment, eSIM And Website Tools — Sixteen Pages

- Payment pages list Visa/Mastercard (explicitly unavailable to Russian citizens), PayPal, USDT on TRC20, Bitcoin, TRON, Litecoin and in-app Apple Pay/Google Pay. If a card fails, the guide sends the user through web plan → email → payment provider. A discounts page pushes tariff promos and email-list signup.
- The refund page supplies the narrow 3/7/14-day windows, one-refund-lifetime rule, crypto-fee deduction and store-policy exception described above.
- iOS eSIM setup: confirm installation, enable the line, make it the cellular-data source and enable roaming.
- Android eSIM setup: Settings → Connections → Mobile Networks → SIM Manager, select the eSimSecure line, then enable mobile data and roaming.
- The public proxy tool says it scrapes candidate proxies from forums/public sources, tests them and publishes working unauthenticated proxies. This is a separate SEO/acquisition surface, not a GnuVPN server guarantee.
- Other tool pages explain a proxy, speed testing and basic IP concepts. The speed guide tells users to stop downloads and use unobstructed Wi-Fi before testing.

### Retired But Still Search-Indexed Guidance

A search-engine cache still exposed a former anti-blocking article with legacy OpenVPN/IKEv2/PPTP/L2TP ports, a Windows/Android **Chameleon** setting, proxy chaining and virtual-machine workarounds. The live URL and inferred companion routes for torrents, DNS leakage and proxy setup now return 404 and are absent from the current 43-page index. This is recorded as historical drift, not current product capability; the audited Android build has no Chameleon control.

The FAQ hierarchy is therefore useful as a competitor content architecture, but unreliable as implementation truth. Every operational claim must be versioned and tested against the client.

## Independent Security Review

The Google Play listing visibly carries **Independent security review** and the developer description claims **MASA Level 2**. The official App Defense Alliance certification directory independently confirms:

- product: GnuVPN: Super Fast VPN Proxy;
- organization: GNUAPP UNIPESSOAL LDA;
- package: `com.gnu.vpn`;
- laboratory: Leviathan Security;
- status: `approved`;
- issued: 2026-02-11;
- expires: 2027-02-11.

Important qualification: the official detail labels this an imported **Legacy MASA** record and says no formal certificate was issued under the prior program; no public report is attached. The official record confirms a currently approved legacy assessment, but it does not expose the exact “Level 2” wording or tested app version. MASA guidance also says assessment is point-in-time and does not validate completeness of Data Safety declarations.

Official record: https://cert.appdefensealliance.org/certifications/10073

## eSIMSecure Product And Contract

The eSIMSecure landing page markets a strong adjacent-product bundle:

- “double-layer” eSIM+VPN protection and “double encryption”;
- 800+ carrier partners and global coverage;
- national-IP access and bypassing local carrier VPN blocking;
- no personal data required;
- crypto payments;
- instant activation and email-delivered installation instructions;
- GNUAPP as operator, with visible GnuVPN and Yesim co-branding.

The “double encryption” framing is marketing, not a demonstrated cryptographic property of an eSIM. No technical proof is supplied. The public testimonial rail is anonymous by country only and reads like brand-authored use cases; it should not be treated as verified customer research.

The eSIM Terms materially qualify the hero:

- registration requires an email/login and password plus payment data/method;
- use is 18+ and GNUAPP may demand identity/capacity documents;
- eSIM is data-only: no voice, SMS or MMS;
- unlocked, eSIM-capable/APN-compatible hardware is required;
- unused balance can be requested within 30 days, but used data is non-refundable;
- technical-failure refund exceptions require notice through the app within one hour;
- refunds of EUR 10 or less are issued in non-cash `YCOINS`;
- YCOINS expire after one year and a first bonus-funded purchase can trigger a EUR 0.50 security payment;
- liability is capped at roughly the prior three months' payments or last top-up.

The contract has strong legacy/template residue: it defines an incoming-SMS-only “GNUAPP Virtual number,” YCOINS and a generic GNUAPP app even though these were not present in the audited eSIMSecure surface. It promises an Effective Date at the end, but none is rendered. The landing page says no personal data is required while its own testimonial says an email is needed and the contract expressly requires email/payment information and permits identity verification.

## Community And Retention Loops

- Telegram channel: “GnuVPN Community”, approximately 2.7K subscribers at snapshot, with a tracked app-link CTA.
- Referral email and public referral page convert dollars to points (`1 point = $0.01`) redeemable against plans for both inviter and friend.
- Default email and push notifications plus Firebase In-App Messaging give the product multiple retention/re-engagement surfaces.
- Apple release history added an explicit “Review Us” feature in December 2025.
- The eSIMSecure tab turns the core utility into a second-product storefront without hiding it in settings.

## Unresolved

- `BLOCKED_BY_ACCESS`: current exact legal-company status from the official Portuguese registry.
- `PARTIALLY VERIFIED`: official App Defense Alliance record confirms approved Legacy MASA through 2027-02-11, but exposes no public certificate/report or exact Level 2 field.
- `BLOCKED_BY_RENDERING`: current Huawei AppGallery version/metadata; official destination resolves.
- `PASS`: Xiaomi GetApps listing current at Android 1.8.7, updated 2026-06-09.
- `UNVERIFIED`: currency label for the `360` one-month amount rendered to the Russian-geography web checkout.

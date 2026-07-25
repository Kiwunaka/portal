# ExpressVPN — Public, Store, Legal And Release Surface

Snapshot date: 2026-07-22 (Europe/Moscow)<br>
Installed Android artifact: `com.expressvpn.vpn` 12.71.0<br>
Evidence rule: runtime facts come from the isolated LDPlayer pass; public facts below come from first-party pages, official stores or government/regulatory records. Search/store values are a point-in-time snapshot and may vary by country, rollout cohort or cache.

## Executive Read

ExpressVPN is no longer sold as one VPN app. The 2026 product is a tiered privacy/security suite with the VPN as its acquisition anchor and ExpressMailGuard, ExpressKeys, Identity Defender, holiday.com eSIM, ExpressAI and Dedicated IP as expansion products. The Android app is the launcher and entitlement surface for that suite even when a feature lives in a separate app or browser product.

Its moat is not one novel connection screen. It is the combination of:

- a very mature cross-platform distribution system;
- weekly Android release cadence and public per-platform release notes;
- high-volume store proof;
- a deep help center that mirrors almost every control in the app;
- explicit trial, retention and referral loops;
- trust artifacts: audits, transparency reports, open-source protocol work and a public bug bounty;
- an account portal that joins billing, training, rewards and all add-ons.

The sharp edges are equally clear: a paid-method gate before the real product, aggressive annual anchoring, promotion-specific refund exclusions, locale/crawler drift in price and trial copy, a tracking redirect in password recovery, and a broad suite whose permissions/data story is much more complicated than the headline “no logs” promise.

## Google Play Surface

Canonical listing: <https://play.google.com/store/apps/details?id=com.expressvpn.vpn>

Observed on 2026-07-22:

- title: **ExpressVPN: VPN Fast & Secure**;
- package: `com.expressvpn.vpn`;
- 100M+ downloads;
- roughly 476K total ratings/reviews in the current English/European response; score varied from 4.3 to 4.7 by locale;
- current listing update date: 2026-07-20;
- current copy: **START YOUR 3-DAY FREE TRIAL TODAY**;
- network claim: 113 countries / 214 locations / all 50 U.S. states;
- one account can protect up to 14 simultaneous devices, depending on tier;
- category: Tools; in-app purchases.

The store copy sells use cases before technical detail: private browsing, streaming, live sports in 4K and public Wi-Fi. It then exposes kill switch, split tunneling, widget, untrusted-network auto-connect and Lightway.

Store propagation is visibly ahead of the installed LDPlayer artifact. The official Android release log has 12.71.0 on July 10, 12.72.0 on July 17 and 12.72.1 on July 21, while the installed artifact is 12.71.0. The exact installed Google Source Stamp time also points to July 10. This is an ordinary phased/store-source lag, not evidence that the installed artifact is counterfeit.

### Russian Play Creative Deck

The ten captured Russian creatives are saved in [`store-creatives/`](../store-creatives/). The phone sequence is:

1. [one-tap connection](../store-creatives/play-01.jpg);
2. [Protection Summary and IP replacement](../store-creatives/play-02.jpg);
3. [server list / “94 countries”](../store-creatives/play-03.jpg);
4. [one subscription for computers, mobile, TVs, streaming devices, routers and browsers](../store-creatives/play-04.jpg);
5. [instant customer support](../store-creatives/play-05.jpg);
6. [favorite shows and apps anywhere](../store-creatives/play-06.jpg);
7. [Trustpilot/press authority proof](../store-creatives/play-07.jpg).

The final three are tablet variants of the connect, privacy/tools and location cards: [connect](../store-creatives/play-08.jpg), [privacy tools](../store-creatives/play-09.jpg), [locations](../store-creatives/play-10.jpg).

The deck uses one large promise per frame, high-contrast brand color, oversized serif headline and a single device mockup. It does **not** try to explain the 2026 suite, protocols or tier matrix. This is good acquisition discipline: sell the core “tap -> protected” job first and leave expansion for onboarding/account surfaces.

The creatives are also stale evidence. They still claim **94 countries**, whereas current official copy says 113 countries / 214 locations. Their legacy settings screen exposes “Get 30 days as a gift,” “Rate ExpressVPN,” IP/DNS/WebRTC tests, password generator and TrustedServer education, proving that referral/review/tool loops were already integrated in the older product. POKROV should copy the single-message creative structure, not the stale claim-management process.

### Play Data Safety

The developer declares:

- no data shared with third parties;
- collection of Personal info, App activity and two other categories;
- encryption in transit;
- a deletion-request path;
- an independent security review.

This disclosure should not be simplified to “collects nothing.” The current privacy policy separately documents daily connection summaries, chosen VPN location, country/ISP, aggregate data volume, app/version activation, optional diagnostics and consented attribution data.

### Play Publisher And Recommendation Graph

The Play support block identifies **Expressco Services, LLC** and gives a Greenwood Village, Colorado postal address. This is the storefront/publisher entity, not the privacy-policy controller.

“More by ExpressVPN” currently includes:

- ExpressKeys Password Manager;
- Identity Defender - ExpressVPN (present in some locales);
- holiday.com.

Play’s recommendation set varied by locale and included combinations of:

- NordVPN;
- Proton VPN;
- Psiphon;
- Speedify;
- Secure VPN;
- Surfshark;
- Brave;
- Opera;
- WireGuard.

This graph matters: ExpressVPN is merchandised both against premium VPN brands and against free/proxy/browser alternatives.

### Recent Review Signals (Samples, Not A Representative Survey)

Current visible reviews repeatedly mention:

- unexpected disconnect/reconnect behavior and weak notification of state;
- difficulty across unstable Wi-Fi/mobile handovers;
- the background/location permission needed for trusted-network auto-connect;
- no multi-hop feature;
- support responses that first ask users to update, change server and then contact support.

The official July 10 Android note fixed a reconnect failure for some users; July 21 was another stability release. The store complaints and release notes point to connection-state reliability as an active product-quality theme, not a closed historical issue.

## Apple App Store Surface

Canonical listing: <https://apps.apple.com/us/app/expressvpn-secure-fast-vpn/id886492891>

Observed on 2026-07-22:

- title: **ExpressVPN · Secure & Fast VPN**;
- iPhone, iPad, Mac and Apple TV support;
- 4.7 / about 418K U.S. ratings;
- #31 Utilities in the captured U.S. response;
- 238.7 MB;
- 17 languages;
- iOS/iPadOS 15+, macOS 15+, tvOS 17+;
- seller: **Expressco Services, LLC**;
- current version response: 12.67.1, released the same day;
- 3-day full-featured trial and automatic billing on the last trial day.

Apple lists several legacy/current in-app SKUs, including monthly, annual and weekly prices. The page is an inventory of App Store products, not a clean tier matrix, so it should not be used as the sole source for current plan comparison.

Apple’s developer-declared privacy labels say:

- email address and user ID may be linked to identity for marketing and app functionality;
- product interaction, crash data and other diagnostics may be collected without being linked to identity.

“More by” links to ExpressKeys, Identity Defender and holiday.com. “You Might Also Like” includes Octohide, Avast SecureLine, Touch VPN and several generic/free VPNs.

## Android Runtime Acquisition Funnel

The isolated device flow is documented in the parent profile and screenshots. The route graph is:

```text
Cold launch
  -> Terms + privacy/data consent
  -> 3-slide value carousel
     -> Buy ExpressVPN
        -> Google Play plan selector
           -> annual / monthly / weekly
           -> Subscribe (billing confirmation; not opened)
           -> Back
              -> trial-retention dialog
     -> Existing account: Sign in
        -> email + password or activation code
        -> restore Play purchase
        -> forgot password
           -> ujsrxts.com tracking redirect
           -> expressvpn.com/ru/reset-password?mobileapps=true
        -> no account
           -> acquisition route
```

No purchase or trial was activated. The real Home, locations, settings and tunnel are therefore a paid-access blocker in this audit.

## Trial, Pricing And Retention

### Native Russian Paywall

Snapshot values in LDPlayer:

| Term | Price | Framing |
| --- | ---: | --- |
| Annual | 3,499 RUB/year | default; “SAVE -90%”; 3-day trial |
| Monthly | 890 RUB/month | 3-day trial |
| Weekly | 699 RUB/week | no trial label observed |

The 90% annual saving is not explained on the paywall. It approximately matches comparison with 52 weekly payments, making the very expensive weekly SKU the apparent anchor. That basis is an audit inference, not a disclosed ExpressVPN calculation.

Back navigation triggers a second-chance modal that makes the trial the visually stronger continuation. This is a direct cancellation-intercept pattern.

### Official Trial/Refund Rules

Official trial page: <https://www.expressvpn.com/features/vpn-trial><br>
Refund policy: <https://www.expressvpn.com/support/manage-account/what-is-expressvpns-refund-policy/><br>
Terms: <https://www.expressvpn.com/tos>

- Mobile app signup offers a 3-day trial and requires a valid Apple/Google payment method.
- Billing begins automatically unless cancelled through the store.
- Purchases billed by Apple/Google do **not** receive ExpressVPN’s 30-day guarantee; refunds are at the store’s discretion.
- Direct first-time web subscribers normally receive a 30-day money-back guarantee.
- Auto-renew is on by default for supported web payment methods.
- Direct subscriptions can be cancelled in the portal, via live chat or email.
- The current Terms exclude renewals, gift/redemption codes and repeat refund users from the initial guarantee.

### Dynamic Web Campaign On Audit Date

Checkout: <https://checkout.expressvpn.com/pricing>

The July 22 response showed a **Summer Tech Sweepstakes** campaign. The flattened page returned these 2-year + 4-month introductory offers:

| Tier | Displayed monthly equivalent | First 28 months | Annual renewal |
| --- | ---: | ---: | ---: |
| Basic | $3.19 | $89.32 | $99.95 |
| Advanced | $4.49 | $125.72 | $119.95 |
| Express Pro | $7.49 | $209.72 | $199.95 |

The same endpoint/search cache produced different campaign equivalents in another response. Treat these as A/B/geo/campaign snapshots, not stable list prices.

The promotion explicitly excludes purchases made July 11–August 11, 2026 from the 30-day guarantee because the purchase also enters an iPhone 17 Pro raffle. This is a major trust/expectation caveat placed deep in checkout copy.

The checkout and subscription guide also disagree on one detail: the campaign card describes Basic “Lite Protection” as blocking adult sites, while the official tier comparison marks adult-site blocking as unavailable on Basic. This is likely content/configuration drift and should be fixed by the vendor; it is not safe to infer the entitlement from marketing copy alone.

## Tier And Suite Architecture

Official subscription guide: <https://www.expressvpn.com/support/manage-account/available-subscriptions/>

### Basic

- VPN on 10 simultaneous devices;
- ad and malicious-site blocking;
- limited ExpressMailGuard;
- Dedicated IP purchasable as an add-on.

### Advanced

- VPN on 12 devices;
- Advanced Protection: ads, trackers, malicious sites and adult-site controls;
- ExpressKeys;
- broader ExpressMailGuard;
- Dedicated IP as add-on;
- on annual/2-year offers: U.S.-only limited Identity Defender and holiday.com eSIM allowance.

### Express Pro

- VPN on 14 devices;
- Dedicated IP included;
- full ExpressMailGuard;
- ExpressKeys;
- full U.S.-only Identity Defender;
- Advanced Protection;
- ExpressAI (500 credits/day in the captured matrix);
- longer holiday.com eSIM allowance on annual/2-year offers.

This is a classic land-and-expand model: the VPN is the high-intent entry product, while identity, password, email, eSIM and AI features make the renewal feel like a suite rather than a commodity VPN bill.

## Expansion Products

### ExpressKeys

Launch note: <https://www.expressvpn.com/blog/expresskeys-password-manager/>

- Became a standalone iOS/Android app in 2026.
- Built-in Keys was removed from the VPN app on March 5, 2026.
- Existing vaults migrate by signing in with ExpressVPN credentials.
- Features include zero-knowledge encryption, sync, password/card/note storage, 2FA generation and breach monitoring.
- July 2026 update added passkeys, secure sharing and a 30-day Recently Deleted area; ExpressVPN reports a Cure53 review with no High/Critical findings.

This is a strong example of splitting a mature add-on into its own focused product without losing the shared-account cross-sell.

### ExpressMailGuard

Product page: <https://www.expressvpn.com/expressmailguard><br>
Launch note: <https://www.expressvpn.com/blog/expressvpn-launches-expressmailguard/>

- Launched February 5, 2026.
- Email relay/aliasing layer that works with an existing inbox.
- Alias creation, forwarding, replies, custom domains, delivery controls and anti-tracking/spam positioning.
- Requires an active ExpressVPN subscription; capability limits rise by tier.
- The official page says “unlimited aliases,” while the tier matrix distinguishes alias domains, shared aliases, recipients, bandwidth and daily anonymous-send limits. The simple headline hides a complex quota model.

### ExpressAI

Product page: <https://www.expressvpn.com/expressai><br>
Privacy explainer: <https://www.expressvpn.com/support/knowledge-hub/expressai-privacy-protections/>

- Web product surfaced from the VPN Add-ons tab; no dedicated mobile app as of the snapshot.
- Runs a curated set of models in confidential-computing enclaves.
- Offers encrypted history, user-held primary password, Ghost mode, file upload, private web search and side-by-side model comparison.
- ExpressVPN states prompts/files/conversations cannot be read by the provider or used for training.
- A Cure53 audit is published.
- The current support matrix names GPT OSS and DeepSeek R1; a separate article describes six models and 500 daily credits, while the subscription matrix says five models. This is another fast-moving catalog/content drift point.

### Identity Defender

Product page: <https://www.expressvpn.com/features/id-defender><br>
Support overview: <https://www.expressvpn.com/support/knowledge-hub/what-is-identity-defender/><br>
Privacy policy: <https://www.expressvpn.com/privacy-policy-identity-defender>

- U.S.-only for eligible Advanced/Pro customers.
- Standalone Android/iOS app plus ExpressVPN+ portal.
- Dark-web/SSN/address/title/court/neighborhood/high-risk transaction/401(k) monitoring, depending on tier.
- Automated broker-site data removal.
- Credit scanner and monthly reports.
- Identity theft insurance up to $3M Advanced / $5M Pro, subject to policy terms.
- Operates with Array Plus Inc.; insurance is underwritten/administered by American Bankers Insurance Company of Florida (Assurant) under policies issued to Array US Inc. or affiliates.
- Requires very high-sensitivity identity inputs for some features. The separate policy explicitly says this data is not linked to VPN data.

### holiday.com And Intego

The global site header presents holiday.com eSIM and Intego as “other products from the family behind ExpressVPN.” holiday.com allowances are bundled into higher annual plans. This uses Kape’s portfolio to create cross-category value while keeping brands distinct.

## Account Portal And Growth Loops

Portal help: <https://www.expressvpn.com/support/manage-account/expressvpn-user-portal/>

The ExpressVPN+ portal combines:

- passwordless email-code access;
- subscription and payment management;
- downloads and setup;
- entitlement visibility for all suite products;
- Training Center onboarding/tutorials;
- Rewards area;
- referral links, invitation history and earned-reward history;
- redemption codes.

### Referral Program

Public page: <https://www.expressvpn.com/refer-a-friend>

- Referrer and referred user each receive 30 free days.
- No stated referral-count limit.
- The referrer must have an active paid direct/web subscription.
- Apple/Google-billed users and users still on a free trial are excluded.
- Share routes: copied link, email, Facebook, X, LinkedIn, WhatsApp and Line.
- Credits append to the billing cycle and may take about 24 hours to appear.

The store-payment exclusion is strategically important: the strongest viral reward is reserved for the lower-fee, vendor-controlled billing channel.

## Distribution And Release System

Android setup guide: <https://www.expressvpn.com/support/vpn-setup/app-for-android/><br>
APK guide: <https://www.expressvpn.com/support/vpn-setup/enable-apk-installs-android/><br>
Fake-app guide: <https://www.expressvpn.com/support/troubleshooting/fake-expressvpn-apps/>

Official Android lanes:

- Google Play;
- Samsung Store;
- Amazon Appstore;
- direct APK from the authenticated ExpressVPN setup/download page.

The direct APK route is an explicit censorship/store-unavailability fallback. ExpressVPN warns against third-party APK sources and publishes instructions for enabling unknown-source installation.

The authenticated setup page sends a one-time code to the account email and then exposes platform downloads. This gives ExpressVPN a direct release channel while maintaining entitlement and provenance controls.

### Android Release Cadence

Canonical log: <https://www.expressvpn.com/support/vpn-setup/release-notes/android-app/>

There were 27 documented Android releases from January 6 through July 21, 2026 — roughly one release every 7.5 days. Recent versions:

| Date | Version | Public note |
| --- | --- | --- |
| Jul 21 | 12.72.1 | minor fixes/stability |
| Jul 17 | 12.72.0 | bug fixes |
| Jul 10 | 12.71.0 | reconnect fix + performance |
| Jul 3 | 12.70.0 | minor fixes |
| Jun 26 | 12.69.0 | bugs/performance |
| Jun 16 | 12.68.0 | ANR while connecting fixed |
| May 15 | 12.65.0 | Dedicated IP map pin, OpenVPN obfuscation and purchase verification fixes |
| Apr 17 | 12.61.0 | ExpressAI magic-link sign-in and gradual Pause rollout |
| Apr 13 | 12.60.0 | gradual Pause rollout |
| Mar 7 | 12.57.0 | Isle of Man location restored |

Most entries are intentionally generic. The value is operational transparency and cadence proof, not rich release storytelling.

### Beta And Rollout Mechanics

The Android setup guide ends onboarding with an opt-in beta choice. Release notes explicitly describe gradual feature rollout for Pause. Together with different store versions and dynamic checkout variants, this indicates cohort/remote-config-driven rollout rather than one globally identical experience.

## Browser Extension

Official Chrome listing ID: `fgddmllnllkalaagkghckoinaemmogpe`<br>
Listing: <https://chromewebstore.google.com/detail/expressvpn-vpn-proxy-brow/fgddmllnllkalaagkghckoinaemmogpe><br>
Guide: <https://www.expressvpn.com/support/vpn-setup/browser-extension-plugin/>

Current store snapshot:

- about 1,000,000 users;
- about 2.8K ratings / 4.5;
- 17 languages;
- developer: Express Technologies Ltd;
- July 21 search response showed 8.0.10.1876; cached locale responses showed older 8.0.7/8.0.8 values, demonstrating store/crawl propagation drift.

The 2026 extension is more than a desktop remote:

- standalone browser proxy mode;
- full-device Remote Control mode via desktop app;
- selected location and connect/disconnect controls;
- HTML5 geolocation spoofing;
- WebRTC protection;
- Smart Routing rules per site, including chosen locations or bypass;
- dark/light mode.

The official guide says there is no dedicated Edge Store build; Edge users should install the Chrome listing. Multiple Chrome Web Store items use confusing “ExpressVPN/Express VPN” names but have different IDs and non-ExpressVPN publishers. The official fake-app guide treats impersonation as a material threat and tells users how to verify publisher/signatures.

## Customer Support And Instruction Architecture

Setup index: <https://www.expressvpn.com/support/vpn-setup/><br>
Release index: <https://www.expressvpn.com/support/release-notes/>

The support system has device-specific lanes for Windows, macOS, Android, iOS, Android TV, Apple TV, Fire TV, smart TVs, consoles, Aircove, routers, Linux, browser extensions, Chromebook, Meta Quest, NAS and manual configurations.

The Android guide mirrors the paid app navigation in detail:

- sign in/download/setup;
- connect/disconnect/pause;
- location selection;
- protocol selection;
- kill switch;
- ads/trackers/harmful-site blocking;
- split tunneling;
- auto-connect/trusted networks;
- Secure Device Assistant;
- speed test;
- appearance/language;
- in-app support;
- widget;
- Protection Summary;
- uninstall.

This documentation is also a product-discovery surface. Every help page carries Get Started, setup, referral, cross-product and live-chat routes, so support traffic continually feeds acquisition and expansion.

## Legal Entities And Ownership

### Service Contract / Data Controller

The current Terms and Privacy Policy identify **Express Technologies Ltd.** as the service provider/data controller, headquartered and registered in the British Virgin Islands.

- Terms: <https://www.expressvpn.com/tos>
- Privacy: <https://www.expressvpn.com/privacy-policy>

The agreement is governed by BVI law. Non-U.S. disputes go to BVI courts (with a fallback LCIA clause if the provision is unenforceable). U.S. residents receive mandatory AAA arbitration language, class-action waiver and a 30-day opt-out process.

### Storefront / Signing Entity

**Expressco Services, LLC** appears as:

- Google Play developer legal entity;
- Apple App Store seller;
- official Windows/macOS signing identity in ExpressVPN’s fake-app guide.

The public stores give a Colorado operational/postal address. A current primary incorporation record for this LLC was not cleanly retrieved in this pass; do not infer state of formation solely from the store address.

### Parent And Ultimate Control

- ExpressVPN officially joined **Kape Technologies** in December 2021: <https://www.expressvpn.com/blog/expressvpn-officially-joins-kape/>
- UK Companies House lists Kape Technologies as an active Isle of Man overseas company, registration 011402V: <https://find-and-update.company-information.service.gov.uk/company/FC038564>
- FCA/RNS records show Unikmind’s 2023 offer became unconditional and Kape moved to cancel AIM trading: <https://data.fca.org.uk/artefacts/NSM/RNS/4753204.html>
- Unikmind’s current corporate site states it owns 98.63% of Kape and is wholly owned by Teddy Sagi: <https://unikmind-holdings.com/>

The current ExpressVPN Privacy Policy still labels Kape Technologies PLC as the ultimate holding company but states Express Technologies Ltd. controls and stores customer personal data under BVI jurisdiction and does not transfer control of it to Kape.

## Privacy And Data Reality

Current Privacy Policy date: January 1, 2026.<br>
Policy: <https://www.expressvpn.com/privacy-policy>

Headline commitment:

- no browsing history, traffic destination/content or DNS-query logs;
- no source IP, outgoing VPN IP, exact connection timestamp or session-duration logs.

Documented operational data:

- account name/email/payment information;
- activated apps and versions;
- whether a connection succeeded on a particular day;
- chosen VPN location;
- source country/ISP, but not source IP;
- aggregate daily transferred volume;
- country code derived from hashed IP, OS, language, app version, device model and randomized installation/user identifiers for marketing attribution;
- advertising identifiers only with explicit consent;
- optional connection/crash/usability diagnostics and speed-test data;
- MediaStreamer-authorized IPs for users who enable that product;
- support correspondence and troubleshooting attributes.

Named service providers include AppsFlyer for attribution, Firebase Crashlytics for Android diagnostics, Zendesk for email/tickets and TeamSupport for chat. The static Android artifact also includes Braze/Firebase/AppsFlyer and other SDK code, but library presence alone does not prove every code path is active for every consent state.

The useful product lesson is precision: “no activity or connection logs” can coexist with significant service-quality and attribution telemetry. POKROV should publish an equally concrete field-level table instead of relying on a blanket privacy slogan.

## Trust And Security Proof

Trust Center: <https://www.expressvpn.com/trust><br>
Audit explainer: <https://www.expressvpn.com/support/knowledge-hub/independent-audits/><br>
2025 KPMG page: <https://www.expressvpn.com/security-audit-reports/kpmg-privacy-policy-2025>

Observed proof stack:

- TrustedServer RAM-only server architecture;
- open-source Lightway implementations;
- internal code review, hardware signing/authentication devices, threat modelling and least privilege;
- independent reports covering no-logs controls, server tech, protocols, apps, extensions, router, build verification and newer suite products;
- third KPMG privacy/TrustedServer assessment as of February 28, 2025, with reasonable assurance and no identified issue in the tested safeguards;
- 2022 Cure53 Android audit: three Medium/Low findings plus hardening recommendations; ExpressVPN says addressed feedback, with some usability-driven exceptions agreed with Cure53;
- public, biannual request statistics;
- public bug bounty.

The Android-specific independent audit is almost four years older than the audited build in this snapshot. The 2025 KPMG review supports server/privacy controls, not every behavior in the 2026 Android suite. POKROV should avoid the common mistake of treating “audited” as one timeless, product-wide badge.

### Transparency Snapshot

For July–December 2025 the Trust Center reports:

- 155 government/law-enforcement/civil requests;
- 1,382,986 DMCA requests;
- 3 warrants;
- no disclosure of user-related data.

### Bug Bounty

Program: <https://yeswehack.com/programs/expressvpn-bug-bounty-program>

- public YesWeHack program;
- broad scope across web, APIs, apps, extensions, Lightway, servers and routers;
- standard published reward grid up to $2,500 Critical for listed high-value assets;
- one-time $100,000 TrustedServer bonus for a qualifying first critical server/privacy-impact result;
- current page showed 192 reports and first response under one day.

## Claim And Content Drift Register

Keep these separate rather than forcing one “true” marketing number:

1. Installed carousel says 200+ safe locations; current Play says 214 locations / 113 countries.
2. Native paywall shows 4.8 / 430K; Play varied around 4.3–4.7 / 476K by locale/device surface.
3. Some cached/localized Play copy still advertises a 7-day trial and 105 countries; current official English listing and native paywall say 3 days and 113 countries.
4. Google Play update date and official release notes moved during the audit; the installed artifact remains verifiably 12.71.0.
5. Current checkout variants returned different campaign prices.
6. Basic adult-site-blocking entitlement differs between checkout card and the subscription matrix.
7. ExpressAI model count differs between current tier matrix and product article.
8. Browser-extension version differs across fresh and cached locale responses.

These are mostly fast-release, localization, A/B or cache problems. They still weaken trust because the product sells precision and security.

## What POKROV Should Copy

### Immediate / High Leverage

1. **Public per-platform release notes.** A short weekly log is enough; it proves continuous maintenance and makes incidents legible.
2. **Protection Summary.** Show time protected, last protection event, changed IP and connection quality locally, with a delete/reset control.
3. **Connection Copilot.** Turn protocol/location troubleshooting into a guided scan with an explainable recommendation, not a raw settings list.
4. **Real speed diagnostics.** Download/upload/latency/jitter/packet loss with VPN vs ISP context and a support-shareable result.
5. **Trusted-network auto-connect.** Make permissions and the reason for them explicit before the Android prompt.
6. **Referral ledger.** Give both sides service time and show pending/successful rewards in the account.
7. **Store-verification page.** Publish official package IDs, store links and signer information because name-copycat risk is real.

### Product Expansion Pattern

1. Keep the core VPN home simple.
2. Add an **Add-ons** area for adjacent protection, but move mature complex products to focused surfaces.
3. Use one account/entitlement layer and passwordless setup links between products.
4. Make every tier difference operationally testable in one comparison matrix.
5. Use the portal for billing, device setup, training and rewards rather than bloating the VPN connection screen.

### Trust Pattern

1. Publish exact telemetry fields and retention rather than “we value privacy.”
2. Date and scope every audit badge.
3. Publish request statistics even when the outcome is zero disclosure.
4. Create a safe-harbor bug-bounty policy with realistic rewards and clear scope.
5. Open-source the client protocol layer only where POKROV can maintain it and produce reproducible release provenance.

## What POKROV Should Not Copy

- do not hide the primary action below the fold in landscape;
- do not require a payment method before the user sees any real product state unless the economics truly require it;
- do not use a weekly SKU mainly as an undisclosed discount anchor;
- do not advertise a guarantee while a campaign silently removes it;
- do not let store locales, checkout and entitlement docs disagree;
- do not send account-recovery users through an unexplained tracking domain;
- do not collapse a complex telemetry practice into a “collects nothing” claim;
- do not let a four-year-old mobile audit stand in for the current app.

## Audit Blockers

- `BLOCKED_BY_PAYWALL`: no subscribed ExpressVPN account; Home, locations, live tunnel, paid settings and in-app Add-ons were not executed.
- `NOT_REQUESTED`: no purchase, auto-renewing trial or checkout confirmation.
- `BLOCKED_BY_BROWSER_CONTROL`: desktop Chrome visual pass could not attach to the running user browser; no new desktop Chrome window was opened without approval.
- `BLOCKED_BY_REGISTRY_ACCESS`: the current primary formation/status record for Expressco Services, LLC was not conclusively retrieved; stores and official signing documentation verify the entity’s operational role.
- `MANUAL_OWNER_TEST`: real-device battery/reconnect/roaming behavior, refund execution and cancellation timing require owner-controlled paid testing.

## Primary URL Inventory

- Product/home: <https://www.expressvpn.com/>
- Pricing: <https://checkout.expressvpn.com/pricing>
- Android Play: <https://play.google.com/store/apps/details?id=com.expressvpn.vpn>
- Apple App Store: <https://apps.apple.com/us/app/expressvpn-secure-fast-vpn/id886492891>
- Android guide: <https://www.expressvpn.com/support/vpn-setup/app-for-android/>
- Android release notes: <https://www.expressvpn.com/support/vpn-setup/release-notes/android-app/>
- All release notes: <https://www.expressvpn.com/support/release-notes/>
- Direct APK instructions: <https://www.expressvpn.com/support/vpn-setup/enable-apk-installs-android/>
- Browser guide: <https://www.expressvpn.com/support/vpn-setup/browser-extension-plugin/>
- Official Chrome extension: <https://chromewebstore.google.com/detail/expressvpn-vpn-proxy-brow/fgddmllnllkalaagkghckoinaemmogpe>
- Available subscriptions: <https://www.expressvpn.com/support/manage-account/available-subscriptions/>
- Portal guide: <https://www.expressvpn.com/support/manage-account/expressvpn-user-portal/>
- Referral: <https://www.expressvpn.com/refer-a-friend>
- Trial: <https://www.expressvpn.com/features/vpn-trial>
- Refund policy: <https://www.expressvpn.com/support/manage-account/what-is-expressvpns-refund-policy/>
- Terms: <https://www.expressvpn.com/tos>
- Privacy: <https://www.expressvpn.com/privacy-policy>
- Trust Center: <https://www.expressvpn.com/trust>
- Audit explainer: <https://www.expressvpn.com/support/knowledge-hub/independent-audits/>
- About: <https://www.expressvpn.com/about-us>
- Press: <https://www.expressvpn.com/press>
- ExpressKeys: <https://www.expressvpn.com/blog/expresskeys-password-manager/>
- ExpressMailGuard: <https://www.expressvpn.com/expressmailguard>
- ExpressAI: <https://www.expressvpn.com/expressai>
- Identity Defender: <https://www.expressvpn.com/features/id-defender>
- Identity Defender privacy: <https://www.expressvpn.com/privacy-policy-identity-defender>
- Kape relationship: <https://www.expressvpn.com/blog/expressvpn-officially-joins-kape/>
- Kape Companies House entry: <https://find-and-update.company-information.service.gov.uk/company/FC038564>
- 2023 Kape delisting evidence: <https://data.fca.org.uk/artefacts/NSM/RNS/4753204.html>
- Unikmind ownership disclosure: <https://unikmind-holdings.com/>
- Bug bounty: <https://yeswehack.com/programs/expressvpn-bug-bounty-program>

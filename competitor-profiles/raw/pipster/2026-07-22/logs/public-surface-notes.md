# Pipster Public Surface Notes

**Captured:** 2026-07-22<br>
**Scope:** official landing pages, current policy pages, payment memo, public store records, redirect destinations, registry snapshots and static account-web-app structure. Public claims are recorded as claims unless runtime or independent evidence confirms them.

## Retained Source Artifacts

- `../public-docs/landing-ru.html` and `../public-docs/landing-en.html`: current `pipster.uk` landing pages.
- `../public-docs/terms-of-service.html` and `../public-docs/privacy.html`: current Russian policies served by `pipstervpn.uk`.
- `../public-docs/payment-memo.docx`: the payment memo linked from the landing page.
- `../public-docs/account-app.html`: public shell of `app.pipster.win`.
- `../public-docs/account-terms-ru.html`, `account-privacy-ru.html`, `account-terms-en.html` and `account-privacy-en.html`: policy copies reached by the account app through `pipstervpn.us`.
- The account web application's JavaScript was inspected from an isolated sensitive-data directory rather than retained here because production bundles expose operational domains and authentication plumbing.

The DOCX renderer could not run because LibreOffice/`soffice` is not installed. Its complete paragraph and table content was extracted structurally with the bundled document runtime; no layout claim is made.

## Positioning And Acquisition Page

The Russian home page positions Pipster as a **location-spoofing service**, not primarily as a security product. Its core promise stack is stable connection, one-click activation, Russian-speaking support and unlimited traffic. Supporting use cases are ordinary blocked-product outcomes: social reactions, YouTube and ChatGPT. The English version changes the hero line to **“Make privacy great again”** and substitutes generic privacy, streaming and public-Wi-Fi use cases.

The site says it has 25 countries, but the rendered RU and EN lists are different. RU includes the United States, Germany, Singapore and North Macedonia; EN instead includes Belarus, Denmark, Panama and Thailand. This is a localization/data-maintenance inconsistency, not evidence of the live server inventory.

The page explains activation in only three steps: download, authorize and switch on with one click. It does not surface the free tier's mandatory pre-connect advertising in that flow.

## Public Pricing

The default Russian monthly cards show:

- Lite, 1 device: 249 RUB;
- Silver, 3 devices: 499 RUB;
- Gold, 5 devices: 649 RUB;
- Diamond, 10 devices: 1,199 RUB;
- three-day full-access trial: 30 RUB.

The English monthly cards show USD 3.99 / 7.99 / 10.99 / 19.99 and a three-day USD 1 trial. The page exposes six- and twelve-month selectors, but the server-rendered source contains only the default monthly values; those longer-term totals were not guessed.

Every Buy and Trial CTA routes to `app.pipster.win`, which is an account/authentication application. The anonymous Android **Buy** control similarly routes to the email-code gate, so both web and app put price-to-payment continuation behind identity.

## User Agreement And Commercial Mechanics

The agreement names Russian operator **OOO PROMDEVELOPMENT**, INN 4345512504 / OGRN 1214300007085. It defines Basic free, Lite 1-device, Silver 3-device, Gold 5-device and Diamond 10-device plans.

Material conditions that are not disclosed on the Android 30-RUB upsell:

- a full-screen Yandex Ads video is mandatory before **every** free VPN connection;
- paid subscriptions renew automatically every 30 days;
- the renewal debit occurs 24 hours before the displayed renewal date;
- auto-renewal must be disabled at least 24 hours before the end of the period;
- cancellation is through **Pause subscription** in the cabinet, or support if the control is unavailable;
- prior paid periods are non-refundable even when the customer did not use the service.

The agreement also documents a real referral program and prohibits spam, brand bidding and imitation sites. Pipster may request proof of where a referral link was placed and may void rewards or block an account.

The text is partially stale against the product: it speaks of a login/password although the current Android and web flows are passwordless email-code/Yandex flows. It also cites `pipstervpn.org` and `pipstervpn.com` as registration sites while acquisition currently starts on `pipster.uk` and purchases route to `app.pipster.win`.

## Privacy Claims And Contradictions

The policy opens with a narrow **“only email”** collection claim and says Pipster does not request or retain physical location or IP addresses. Later sections permit processing website IP address, approximate geography, browser/OS, session duration, preferences and visit frequency; support correspondence and metadata; optional diagnostics, speed tests and crash reports; Yandex Metrica/AppMetrica; cookies; advertising; fraud prevention; and cross-border processing.

The policy says OOO PROMDEVELOPMENT supplies and controls the service, then says the company is physically located in Kazakhstan and processing occurs there. Its footer separately lists both the Russian company and Kazakhstan LLP ViPiN. The document has no visible effective date or revision identifier, making change tracking difficult.

Static account-web-app evidence adds further implementation detail:

- Yandex Metrika is initialized with click maps, link tracking, bounce analytics and Webvisor;
- a Yandex client identifier is appended to outbound download links;
- the app requests IP-country data from a third-party geolocation service;
- a first-party endpoint named `push_fb_conversions` is called with a **Lead** event and the current user email when a platform-download link is clicked;
- authentication and refresh tokens are stored in browser local/session storage;
- account surfaces cover profile, subscription, referral, device removal and account deletion.

The endpoint name strongly suggests a Facebook/Meta conversion handoff, but this pass did not execute an authenticated runtime request and therefore does not claim that a specific email was actually delivered to Meta. The mismatch between the headline privacy claim and these analytics/ad mechanics is nevertheless a high-priority trust-review item.

Google Play's current Data Safety declaration is broader than “email only”: it declares collection of personal information, app information/performance and device or other IDs while saying data is encrypted in transit, not shared and can be deleted on request.

## Referral And Account-Cabinet Mechanics

The public account bundle exposes `/profile`, `/profile/subscription`, `/profile/referral` and `/profile/hidden-gem`, plus login, token, policy and confirmation routes. Visible strings describe:

- a personal referral link/code;
- friend count, monthly income, total balance and the user's percentage;
- rewards from every referred purchase;
- an accrual history;
- a dynamic minimum withdrawal amount;
- withdrawal only to a legal entity's settlement account through support;
- extra subscription days for the invited friend;
- current-plan and device management;
- pause/resume/switch subscription states;
- an explicit warning that an immediate upgrade charges the full amount without prorating remaining days;
- a downgrade that starts after the paid period and removes all devices;
- permanent account deletion.

Exact percentages, minimum withdrawal and trial follow-on price are server-provided values and were not available anonymously, so they remain blocked rather than inferred.

The authenticated-only `/profile/hidden-gem` route statically loads an alternate subscription component using the same product/trial/device/YooKassa machinery as the normal subscription page. No separate copy or fixed offer value is embedded, and registration email delivery remained blocked, so it is recorded as a server-fed alternate-offer surface rather than labeled a roulette or discount without evidence.

## Payment Memo

The linked DOCX names **LLP ViPiN**, BIN 250140024873, at the old Astana/Kenesary address. It describes card entry and 3-D Secure through **TipTop Pay Kazakhstan**, states PCI DSS 3.0 and SSL protection, and says card details are entered directly into the processor rather than stored by Pipster.

This conflicts operationally with the in-app July notice that renewals were being migrated to a new YooKassa store. The evidence supports a payment-stack transition or regional processor split; it does not prove that either processor is now exclusive.

## Download And Button Destination Map

All public download buttons first pass through Yandex AppMetrica redirect tracking:

- Android store -> Google Play `com.vipin.pipster`;
- Android APK -> direct `static.pipstervpn.com/installer/pipster.apk`;
- iOS -> Apple App Store, app ID `6740810340`;
- Windows -> direct `static.pipstervpn.com/installer/pipster_setup.exe`;
- Russian macOS -> Mac App Store, **Pipster Max VPN**, app ID `6760891666`;
- Chrome -> Chrome Web Store extension `pjjjdhmjcocbljdojhonknpfdajfncap`;
- Edge -> Edge add-on `padapnpfcbnlkpadfaojhfknenfblaok`;
- Firefox -> Mozilla add-on `free-vpn-proxy-pipster`.

The English macOS redirect goes to a different app ID (`6752992336`) and currently ends at HTTP 404. The RU macOS path is live. This is a concrete acquisition leak.

## Domain And Entity Sprawl

Observed first-party or first-party-claimed domains are `pipster.uk`, `pipstervpn.uk`, `pipstervpn.us`, `pipstervpn.org`, `pipstervpn.com`, `pipster.ru`, `app.pipster.win`, `app.pipster.ru`, `static.pipstervpn.com` and an unlabeled `peepster.ru` link embedded in policy pages. This makes ownership and canonical policy discovery unnecessarily hard.

The account cabinet's visible privacy/terms routes immediately redirect Russian users to `pipstervpn.us/ru/...` and English users to `pipstervpn.us/en/...`; the landing/footer policy paths are served on `.uk`, while Apple points to `app.pipster.ru`. The retained `.us` policy copies currently match the material Russian `.uk` clauses, but there is no canonical-domain or revision marker proving which copy governs. Google Play's privacy URL first enters the account app and then relies on this redirect chain.

Current registry/store evidence:

- **OOO PROMDEVELOPMENT** is active, registered 2021-08-17, with Oleg Vladimirovich Koshkin as owner and an individual entrepreneur as manager since 2026-01-15. The current registered address changed on 2026-07-10 to Vladimirskaya 18A, Kirov; the landing/policy footer still shows the superseded Volodarskogo/Nikitskaya 108 apartment 11 address.
- **LLP ViPiN** is active, registered 2025-01-24, with Alexander Sergeevich Prokashev as director/owner. Current registry aggregators show Alikhan Bokeikhan 29 apartment 42, Astana; the landing and payment memo still show the superseded Kenesary 65 apartment 47 address.
- The Android package signer subject is `O=Synaptic`, which does not match either storefront entity. This is a build/signing-brand mismatch, not by itself evidence of wrongdoing.

## Release And Distribution Signals

- The installed Google Play artifact is version 2026.7.7 and has a 2026-07-07 source stamp, matching the date-shaped product version and suggesting a frequent calendar-version release process. The public Google Play web record seen in this pass lagged at a 2026-06-02 update and anonymous-mode release note, so the store web surface is not reliable evidence of the installed candidate's exact release date.
- Apple currently shows version 2026.7.7 released 2026-07-08. Its first-party history demonstrates a fast cadence: four releases from June 4 through July 8, and recurring product releases throughout 2025-2026.
- App Store history narrates passwordless login and less intrusive ads, support/log tools, Yandex/QR auth, backup DNS, daily traffic limits, staged repair, network analytics, Xray-core updates and stability work.
- Current 2026.7.7 notes emphasize Xray-core updates, automatic exclusion/re-entry of unstable servers and more accurate connection notifications.
- Google Play reports 500K+ installs and ads. Apple reports 32 US ratings at 3.9/5 and 139.8 MB. Store claims disagree on location count: current Play/landing copy says 25 while Apple's description says 29.
- Firefox extension 1.0.15 was released 2026-05-12. The public history shows 1.0.11 on March 13, 1.0.13 with split tunneling for Russian sites on April 27, 1.0.14 on May 1 and 1.0.15 on May 12. Mozilla shows 944 users, 3.1/5 from 22 reviews, required access to all websites/proxy controls and developer-declared collection of authentication information.
- The public web app is independently deployable and uses hashed Angular-style bundles; the marketing site is a separate Next-rendered surface. Firebase Remote Config in Android and server-fed account/pricing data allow behavior and offers to change without a store release.

### Firefox package inspection

The current signed Firefox XPI was fetched from Mozilla and inspected without installing or running it. It is Manifest V2, version 1.0.15, with 53 locale folders. Its popup mirrors mobile: welcome, email-code auth, referral code, guest continuation, Home, locations, theme/settings, support, account exit and device-limit messaging.

The free browser product is **time gated**, despite storefront copy saying unlimited traffic with no hidden restrictions:

- anonymous sessions receive a 30-minute proxy expiry and then require reconnection;
- authenticated free sessions receive 60 minutes;
- paid sessions have no client-side expiry alarm.

The extension applies an authenticated browser proxy through a generated PAC configuration. It downloads and hourly caches a direct-routing list, bypasses the proxy for Russian-domain suffixes (`.ru`, `.su`, `.рф`) plus service-control domains, and falls back to a local PAC generator when the remote PAC cannot load. Proxy credentials and state are kept in extension storage, cleared on expiry, and also cleared after a failed authentication retry. This is split routing rather than a device-wide VPN.

It detects other enabled extensions that hold the proxy permission and warns the user to disable them. Firefox private-window access is checked before connecting; if missing, the popup explains how to enable it. These are solid operational details worth copying.

The package requests proxy, webRequest/auth, storage, alarm, extension-management and all-site permissions, with optional privacy-setting access. It contains no observed local request-blocking listener or bundled blocker-rule list; the only `webRequest` listener found supplies proxy credentials. Therefore the advertised **built-in ad blocker / anti-tracking** was not substantiated as an on-device extension feature in this static pass. Server-side filtering remains possible and was not tested.

The referral copy is unusually direct: **“You get a percentage of the purchase; your friend gets subscription days.”** Exact values remain server-fed. Settings also cross-promote Android, iOS and Windows and link into the web referral cabinet.

## Store Creative Audit

Twelve Google Play image entries and three Firefox storefront images were retained in `../store-creatives/`; hashing shows only six unique Play assets because the three portrait concepts are repeated for multiple device tabs. The creative system is recognizable: near-black violet gradient, thin white type, the ninja/robot mascot and large glossy 3D shield, trophy and rocket props.

The three messages are simple and benefit-led — **protect yourself online**, **fast connection**, **high speed** — but the shown UI is stale and more generous than the exact guest runtime. Portrait acquisition says **Create account** and omits the current anonymous path; server imagery shows selectable Germany/Singapore/France/Belgium; no image reveals the mandatory ad gate, 0.5-GB quota or locked-country model. Landscape/tablet artwork does show **Continue without registration**, suggesting mixed creative generations in one listing.

This is strong visual branding but weak product-truth synchronization. The useful lesson is the consistent mascot/3D-object mnemonic and one-message-per-frame structure; POKROV should keep screenshots generated from current release states and expose the real free model rather than a cleaner fictional path.

The Firefox artwork is more coherent and current than the Play portrait set: it shows the anonymous path, a Gold badge, autoselect, server-load bars and a compact extension-sized panel. It still presents connection as immediate and does not disclose 30/60-minute free-session expiry.

## Store Recommendations And Review Signals

Google Play's current related-app rail includes HypePN and Bezlimit among a broader set of non-VPN utilities. Apple's **You Might Also Like** rail is more competitor-dense: AladdinVPN, Universal VPN, Tip Top VPN, TOPi VPN, Oneok VPN, Glim VPN, Buck VPN, 4U VPN, VPN Anony and Vine VPN. These are storefront algorithmic recommendations, not customer endorsements.

Sampled first-party-store reviews repeatedly mention speed/connection failure, a blank white screen, a fresh-install traffic-limit surprise and desire for Basic server choice/load visibility. Developer replies usually route users to support or recommend updating/reinstalling. One positive Play review explicitly accepts advertising on the free tier and describes paid service as the path to no limits and server choice. These samples identify issues and jobs-to-be-done; they are not a statistically representative sentiment score.

## Copy/UX Lessons For POKROV

Worth copying:

- make quota and exact ad reward legible before connection;
- keep an in-app service-status/payment-migration inbox independent of OS push permission;
- provide a visible multi-step repair ladder, but explain each step before disrupting the tunnel;
- build referral economics into the cabinet with balance, history, payout rules and invited-user benefit;
- maintain direct APK plus store/desktop/extension distribution from one acquisition page;
- use release notes to narrate operational improvements, not generic “bug fixes.”

Do not copy:

- hiding billing period/renewal terms behind a 30-RUB teaser;
- mandatory long ads at connection and repair moments;
- account-gating price discovery;
- blocking Android Back inside ads;
- stale legal addresses, cross-domain policy confusion and processor contradictions;
- a reward CTA whose promised quota does not appear;
- locked server rows that provide no upgrade explanation;
- privacy copy that says “only email” while later clauses and implementation describe substantially broader telemetry.

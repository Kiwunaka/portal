# TipTop VPN — Public, Legal And Release Surface Notes

Snapshot: 2026-07-22. Public pages were read without logging in, purchasing, submitting a form or downloading third-party APKs. Store/archive dates are separated by evidence quality because several aggregators appear to relabel crawl/upload dates as release dates.

## Official Route Map

Primary public domain: [`tiptop-vpn.com`](https://tiptop-vpn.com/). The Android app itself routes support/legal traffic to the older-looking non-hyphenated [`tiptopvpn.org`](https://tiptopvpn.org/).

| Visible route/action | Observed destination/result |
| --- | --- |
| Prices | [`/price/`](https://tiptop-vpn.com/price/) |
| Download VPN | [`/vpn-download/`](https://tiptop-vpn.com/vpn-download/) |
| Locations | [`/locations/`](https://tiptop-vpn.com/locations/) |
| Support | [`/support/`](https://tiptop-vpn.com/support/) |
| Log in | [`/cabinet/`](https://tiptop-vpn.com/cabinet/) |
| Terms / Privacy | [`/terms/`](https://tiptop-vpn.com/terms/) with anchors |
| Android store | [`Google Play`](https://play.google.com/store/apps/details?id=com.free.tiptop.vpn.proxy) |
| iOS store | [`App Store`](https://apps.apple.com/app/vpn-proxy-tiptop-vpn/id6454190738) |
| Header support email | `mailto:` link; not exercised |
| Try Free / tariff CTAs | The crawler resolved the shared action back to the homepage rather than a checkout; no payment flow was initiated |
| Android / iOS platform chips | Remain on the homepage/download page and scroll to their sections |
| Windows / macOS / browser / TV chips | Remain on the same page; every corresponding section says “Coming Soon” |

The cabinet is a passwordless email-code form matching the Android account model. It asks for email, then a code; no public-site login attempt was made.

## Website Positioning And Funnel

The current English hero is **“VPN for ChatGPT and global services”**. It explicitly sells region-correct access to ChatGPT/AI, work tools, cloud services and streaming, then expands into public-Wi-Fi protection, travel, email/banking and entertainment use cases.

The funnel stacks many trust/conversion claims before pricing:

- “strict no journals” / no access logs;
- global servers, “latest and greatest” encryption and total anonymity;
- five simultaneous devices;
- streaming/game optimization and mostly 10 Gbps-linked servers;
- 7-day premium trial;
- KillSwitch, split tunnelling, language/theme settings;
- 24/7 expert support;
- 30-day refund messaging;
- a free tier with limited speed/features plus referral-earned free days;
- a cheaper social-network-only plan in some countries.

The download page claims **320+ servers in 57 countries**. The dedicated locations page instead claims **125 servers, 25 locations and 20 countries**, while its rendered table names only 17 countries. The tested Android client exposed one automatic limited-speed free choice and 12 locked premium locations. Google Play names 23 countries. These are four incompatible inventory stories on current first-party surfaces.

The paid-versus-free comparison attacks free VPNs for advertising and tracking while the tested free Android build bundles a very large mediation stack and initialized advertising telemetry before consent. It also promises smart ad blocking, although no ad-blocking control was found in the Android UI.

## Public Pricing And Payment Claims

Website cards are materially different from the localized Android paywall:

| Website plan | Displayed charge | Refund copy |
| --- | ---: | --- |
| 1 month | USD 9.90 | 3 days on the card |
| 1 year | USD 58.80 total / USD 4.90 monthly equivalent | 30 days |
| 3 years | USD 104.40 total / USD 2.90 monthly equivalent | 30 days |

The public page advertises 10+ payment methods grouped as cards, cryptocurrency and electronic money. It says new card/Google Pay/Apple Pay customers receive a seven-day trial and can cancel at any time. No checkout was opened, so actual processors, regional availability and pre-charge disclosure remain unverified.

There are internal refund contradictions:

- the one-month card says 3 days;
- the same pricing page says all new customers receive 30 days and calls the guarantee “no questions asked”;
- Support says 30 days from purchase / all new clients;
- legal account/payment terms say subscription fees are non-refundable unless another refund policy says otherwise.

Android showed 499 RUB/month, 1,990 RUB/six months and 2,490 RUB/year, with no visible three-year offer and no explicit seven-day trial disclosure before its untouched CTA. The remote fallback catalogue also differed from both website and store prices.

## Support Content

The current public help center has four content groups plus a contact form:

- general questions: VPN basics, use cases, getting started, trial/refund, legal responsibility and trust;
- technical questions: fastest-server logic, five-device limit and torrent/P2P policy;
- financial questions: pricing, seven-day trial, cancellation and refund;
- possible errors: failed connection and low-speed troubleshooting;
- contact form: email, subject category and message.

No support form was submitted. Content quality is mixed: it tells users to download Windows/macOS clients even though the same site marks both as “Coming Soon”; it says connection usually takes seconds, whereas the controlled Android attempt first returned no servers and the retry took substantially longer; and it claims users can choose countries/cities although the tested free Android tier offered only automatic fastest-server selection.

## Legal Text And Privacy Contradictions

Both legal pages display a last-update date of **2 June 2023** and choose Hong Kong law/courts, but their operator naming has diverged:

- [`tiptopvpn.org/ru/terms/`](https://tiptopvpn.org/ru/terms/) repeatedly names **TipTopNet Limited**;
- [`tiptop-vpn.com/terms/`](https://tiptop-vpn.com/terms/) replaces the company name with the non-entity label **TipTop VPN** in the same template;
- Google Play and Apple name **TipTopNet Limited**;
- current Russian website footers name Kyrgyz **ОсОО “ТипТопНет Лимитед” (308685-3301-ООО)**;
- English footers usually collapse this further to **TipTop VPN**.

The privacy text allows collection of name, email, payment data, IP address, connection timestamps, bandwidth use and **internet activity**, use for analytics and marketing, disclosure to service providers/legal recipients, and retention for an undefined “necessary” period. That conflicts directly with the app/site promises of no activity logging, no third-party sale/sharing and “only you know which sites you visited.” Store disclosures are broader than the onboarding summary but still do not reconcile the legal page's internet-activity wording.

The legal privacy section says the service is not intended for under-18s, while store age ratings are Google Play 3+ and Apple 4+.

## Entities And Registry Evidence

Current store evidence identifies the seller/operator as **TipTopNet Limited**. Hong Kong Companies Registry's official weekly incorporation list records:

- name: `TipTopNet Limited`;
- company number: `3291327`;
- incorporation date: `21 June 2023`.

Source: [Hong Kong Companies Registry weekly list, 19–25 June 2023, page 41](https://www.cr.gov.hk/docs/wrpt/RNC063_2023.06.19-2023.06.25.pdf).

This official document proves incorporation, not current good standing, ownership or the relationship with the Kyrgyz entity. The live Play listing gives a Hong Kong address, while the current Russian website footer gives Kyrgyz registration identifier `308685-3301-ООО`. A current authoritative Kyrgyz registry extract and a current Hong Kong status/ownership extract were not available in this pass; relationship and beneficial ownership remain `BLOCKED_BY_ACCESS`.

An independent Kyrgyz business publication's 2025 list, described as derived from National Statistics Committee and State Tax Service data, includes ОсОО “ТипТопНет Лимитед”. That is corroboration of a Kyrgyz operating entity, not a substitute for the registry extract.

## Android Release And Distribution Evidence

High-confidence current evidence:

- Google Play displayed version 1.036 and last update **17 July 2025** in the inspected Russian listing.
- The installed Google Play artifact has a source-stamp timestamp of **2025-07-17 12:39:09Z**, independently matching that date.
- The APK has Google Play provenance/signing indicators, no `REQUEST_INSTALL_PACKAGES`, and no Play in-app-update package. Binary updates therefore appear store-managed; remote configuration can change locations, prices, protocol switches, tasks, ads and copy without a release.

Lower-confidence third-party archive reconstruction (dates are archive/upload labels, not authoritative release proof):

| Version | Approximate archive evidence | Reported change |
| --- | --- | --- |
| 1.019 | late 2023 | crash/stability fixes |
| 1.021 | Jan–Feb 2024 | guest connection, task screen, Arabic display fixes |
| 1.030 | Aug–Dec 2024 | test protocol, new languages, minor fixes |
| 1.031 | Dec 2024 / early 2025 | same generic protocol/language/fix note |
| 1.033 | early–mid 2025 | same generic protocol/language/fix note |
| 1.036 | 17 Jul 2025 authoritative Play/source stamp | first of promised stability/security updates |

Archive dates after July 2025—and especially 2026 pages still carrying unchanged version 1.036—look like re-upload/crawl dates. They must not be presented as new releases. The reliable pattern is infrequent binary releases with large server-controlled changes and weakly specific changelogs.

Third-party reference pages used only to reconstruct version names/notes: [APKFab archive](https://apkfab.com/vpn-proxy-tiptop-vpn/com.free.tiptop.vpn.proxy), [APK Watch archive](https://vpn-proxy-tiptop-vpn.apk.watch/1.021), [APKCombo old versions](https://apkcombo.com/vpn-proxy-tiptop-vpn/com.free.tiptop.vpn.proxy/). No binaries were downloaded from them.

## Apple Surface

The official App Store listing shows:

- developer label **Free VPN Network**, seller **TipTopNet Limited**;
- 4.7 from 7.8K US ratings at capture time;
- version history from 1.0 (25 Sep 2023) through numeric version 5 (11 Jul 2024);
- version 4 removed mandatory registration; version 5 improved connection stability, fixed bugs and added invite codes;
- current in-app products of USD 8.99/month, USD 39.99/six months, USD 59.99/year and a USD 2.99 special offer;
- identity-linked email, support content, user/device identifiers and product-interaction analytics, plus non-linked diagnostics;
- iPhone-only positioning; Apple notes it is not verified for macOS even though Apple-silicon Macs may technically run it.

Apple's “You Might Also Like” shelf is heavily saturated with generic keyword-led VPN brands (Bear VPN, Lite Cat, VPN Master, VPN Satoshi, iNinja, VPN 360 and similar). This is a useful ASO reference set but not evidence that TipTop endorses them.

The iOS binary appears substantially behind Android: its last listed update is July 2024, while Android's authoritative current artifact is July 2025. Windows, native macOS, browser and TV clients remain announced but unreleased on the current public site.

## Evidence Quality Summary

- `PASS`: current Google/Apple listings, first-party pages, installed artifact/source stamp, official Hong Kong incorporation list.
- `PARTIAL`: historical Android cadence reconstructed from third-party archives with conflicting upload dates.
- `BLOCKED_BY_ACCESS`: authoritative current Hong Kong status/ownership extract, Kyrgyz registry extract, relationship between the two entities, actual website checkout/processors, Chrome visual pass.

# 4ebur.net — Mobile App Competitor Profile

**Status:** `DEEP PASS COMPLETE WITH BLOCKERS — NATIVE PRODUCT, WEBSITE, MINI APP, STORES, DISTRIBUTION, LEGAL TEXT, STATIC APK AND CONTROLLED VLESS CRASH CAPTURED`<br>
**Snapshot date:** 2026-07-22<br>
**Android package:** `com.cheburnet.mobile`<br>
**Installed version:** `5.1.0` (`versionCode 210030031`)<br>
**Install source:** Google Play<br>
**Runtime rule:** launch only after the previous competitor is force-stopped and `tun0` is absent.

## Isolated First-Launch Checkpoint

AdGuard VPN, Google Play and Chrome were force-stopped first and `tun0` was absent. 4ebur.net then launched alone through `com.cheburnet.mobile/.MainActivity`.

The first two surfaces are Android permission pressure rather than product onboarding:

1. an immediate request to add a Quick Settings tile named **Connect**;
2. the Android notification permission immediately after declining the tile.

Both were declined. No licence, privacy notice, account, key import, tutorial or plan choice appeared before the usable home. Evidence: [Quick Settings request](raw/4ebur-net/2026-07-22/screenshots/01-isolated-launch.png), [notification request](raw/4ebur-net/2026-07-22/screenshots/02-post-tile-decline.png).

## Anonymous Home Checkpoint

The dark home opens directly into a usable anonymous/default state:

- top acquisition banner: “Try our Telegram bot” / “Quick launch and stable access during restrictions”;
- large koala mascot as the central state illustration;
- state “Not connected”;
- routing shown as Off;
- protocol shown as **Vless**;
- preselected Netherlands / Amsterdam server, load indicator and server `#1`;
- full-width green Connect CTA;
- bottom navigation: Home, Regions, Premium, Settings.

The visual hierarchy is clean and highly legible: one mascot/state cluster, one server row and one dominant CTA. The country label truncates despite ample horizontal room, and the app asks for two OS-level privileges before explaining any value or privacy terms. Evidence: [anonymous home](raw/4ebur-net/2026-07-22/screenshots/03-post-notification-denial.png), [UI tree](raw/4ebur-net/2026-07-22/ui/03-post-notification-denial.xml).

## Regions And Anti-Blocking Checkpoint

The region picker is a full-screen sheet with refresh/close controls, favourites, load bars, two protocol families and VLESS-specific route types.

- **Vless:** two visibly free Poland / Warsaw nodes plus 23 captured Premium nodes.
- **Amnezia:** four Premium nodes: Bulgaria / Sofia, Czechia / Prague, Latvia / Riga and Poland / Warsaw.
- Ordinary VLESS countries captured: Bulgaria, Czechia, Spain, Italy, Kazakhstan, Latvia, Netherlands, Russia, Ukraine and the United States, with multiple nodes in several locations.
- Specialized VLESS nodes: Czechia and Germany White list v1; Netherlands White list v2; Germany and Netherlands Multihost v1; Germany and Netherlands Bypass.

The in-app explainer defines the Russian anti-blocking products precisely:

- **White list:** Russian users first reach an intermediate server in Russia that remains available under allowlist-only filtering, then traffic is forwarded to the chosen exit;
- **Bypass:** an additional DPI/blocking-resistant protocol through an intermediate server in Russia or a neighbouring country such as Kazakhstan, then to the chosen exit;
- **Multihost:** a less frequently blocked Russia/neighbouring-country intermediate hop for stability, then the chosen exit.

The filters are All, Ordinary, White list, Bypass and Multihost. The sheet uses background tints to distinguish special node types, but its three large explanatory cards stay pinned and consume substantial vertical space while browsing. Evidence: [VLESS catalog](raw/4ebur-net/2026-07-22/screenshots/04-regions.png), [route-type explainer](raw/4ebur-net/2026-07-22/screenshots/05-region-type-info.png), [Amnezia nodes](raw/4ebur-net/2026-07-22/screenshots/06-regions-amnezia.png), [special nodes](raw/4ebur-net/2026-07-22/screenshots/09-regions-vless-page-3.png).

## Premium And Key Model Checkpoint

Premium value is unlimited speed, a larger region catalog, priority support 24/7 and the deliberately comic “permanent respect at school”. Current Google Play prices:

| Period | Displayed monthly rate | Charged amount | Discount |
| --- | ---: | ---: | ---: |
| 1 month | 489 ₽/month | 489 ₽ | — |
| 3 months | 463 ₽/month | 1,390 ₽ | 5% |
| 6 months | 400 ₽/month | 2,399 ₽ | 18% |

The screen has Pay, “I already have Premium”, Restore purchases, Privacy and Terms routes. Selecting the one-month product and proceeding reached Google Play, which reported that payments are currently suspended in Russia; no order was created. Checkout evidence containing account context is quarantined outside the repository.

Cross-channel access uses a licence key rather than a password. An existing website/other-app purchase can be activated by pasting the key; recovery uses the email previously bound to that key. Settings also expose a voucher field and a copyable licence-key field. Evidence: [paywall](raw/4ebur-net/2026-07-22/screenshots/19-premium.png), [selected monthly plan](raw/4ebur-net/2026-07-22/screenshots/25-premium-month-selected.png), [key activation](raw/4ebur-net/2026-07-22/screenshots/23-have-premium.png), [key recovery](raw/4ebur-net/2026-07-22/screenshots/24-restore-key.png).

## Settings, Routing And Session Checkpoint

Settings contains the Premium banner, licence-key activation/copy, voucher redemption, VLESS routing, account/session controls, a manually editable backup server address and About.

VLESS routing downloads `geosite.dat` and `geoip.dat` from the public `Loyalsoldier/v2ray-rules-dat` GitHub release. The only modes are:

- Russia: Russian traffic goes direct outside the VPN;
- Off: all traffic goes through the VPN.

Off was selected and no routing state was changed. The copy contains the repeated typo “соеденения”. Evidence: [settings](raw/4ebur-net/2026-07-22/screenshots/26-settings.png), [routing](raw/4ebur-net/2026-07-22/screenshots/27-routing-vless.png).

The anonymous install already has a generated service identity. Account/session settings offer an email field, show the current mobile session, enumerate active web sessions and can terminate all other sessions. Opening the personalized Privacy and Terms routes created two visible website sessions even though no login was performed. The UI masks the IP, but the generated key, session metadata and even partially masked network identifiers are treated as sensitive and remain outside the worktree. This is an unusually tight coupling between public legal navigation and the service account/session model.

## About And Destination Checkpoint

About describes a standard encrypted-connection/IP-hiding VPN and reports app version 5.1.0. Its routes are:

| Origin | Destination |
| --- | --- |
| Home acquisition banner | `t.me/net4ebur_bot` |
| News | `t.me/net4ebur` |
| Support | `t.me/net4ebur_support` |
| “Our site” | `net4eburlab.xyz` personalized site route |
| Privacy | `net4eburlab.xyz/privacy` personalized route |
| Terms | `net4eburlab.xyz/terms` personalized route |

The Telegram pages label `https://4ebur.net` as the official site, while the app itself routes its site/legal actions to `net4eburlab.xyz`. No message was sent. Evidence: [About](raw/4ebur-net/2026-07-22/screenshots/29-about.png), [loaded privacy page](raw/4ebur-net/2026-07-22/screenshots/21-privacy-loaded.png), [loaded terms](raw/4ebur-net/2026-07-22/screenshots/22-terms-loaded.png).

## Native Privacy And Terms Checkpoint

The privacy page is dated 2022-11-10. It promises no activity/metadata logs and data minimization, but says personal data may be processed for payments, email/support and abuse enforcement. It mentions bank transfer, PayPal, Swish and Stripe; third-party email/payment providers; Sentry/Functional Software for component-use/behaviour monitoring; EU/EEA-only storage; no automated decisions; and six-month deletion of closed support correspondence. App reports claim to strip email, IP addresses and sensitive paths from logs. No controller legal name, address or jurisdiction is visible in the captured policy.

The terms are dated 2023-08-12 and identify the counterparty only as “4ebur.net”. They describe a one-time payment for a chosen access period; Visa, Mastercard, Apple Pay and Google Pay; **no refunds**; passwordless licence-key access; optional email recovery; discretionary suspension/closure without refund for abuse; 18+ use; no service warranty; and support through social networks or the public support email. They forbid resale and use through unofficial clients. Terms may change without advance notice, though material changes may be emailed or shown in-product.

There is age-copy drift: privacy says it knowingly does not collect/store data from children under 13, while Terms require the user to be at least 18. There is also payment-copy drift: privacy names PayPal/Swish/Stripe/bank transfer, while current Terms name card wallets only. Current controller identity and governing law remain undisclosed on these pages.

## Controlled VLESS Connection Checkpoint

Poland / Warsaw free node `#2` was selected and Android VPN consent was granted. The first controlled Connect attempt crashed the foreground app before any `tun0` interface appeared. Logcat records:

`java.lang.UnsatisfiedLinkError: No implementation found for hev.htproxy.TProxyService.TProxyStartService(...)`

The failure originates from `com.cyberwool.xray.XrayVpnConnection` while starting the Xray VPN service. Android force-finished `MainActivity`; the emulator returned to the launcher. Raw logs were screened for connection material, and only the redacted failure summary is retained. This is strong evidence of a missing/unloaded native JNI implementation for this x86_64 LDPlayer artifact, not proof that ARM devices or the production network fail. IP and DNS reachability tests after the crash used the ordinary emulator network and are not counted as VPN health checks. Evidence: [Android VPN consent](raw/4ebur-net/2026-07-22/screenshots/31-vpn-consent.png), [post-crash launcher](raw/4ebur-net/2026-07-22/screenshots/32-connected-free.png), [redacted failure summary](raw/4ebur-net/2026-07-22/connection-failure-summary.md).

## Public Website Checkpoint

The public `net4eburlab.xyz` site positions the product as “Professional VPN service 2026” and sells speed, safety, reliability, many servers, privacy, broad platform availability, cryptocurrency payment and low prices. Its public list covers Latvia, Germany, the United Kingdom, the Netherlands, Estonia, Czechia, Ukraine, Kazakhstan, Spain, Poland, Bulgaria, the United States, Italy and Russia. That list does not match the live Android catalog exactly: some public locations were absent in-app and some live locations were not advertised on the site.

Public website pricing is:

| Period | Website display | Effective interpretation |
| --- | ---: | --- |
| 1 month | `$3.5 /mo` | $3.50 total |
| 3 months | `$10 /mo`, “save 4%” | appears to mean $10 total, not $10/month |
| 6 months | `$19 /mo`, “save 9%” | appears to mean $19 total, not $19/month |

The `/mo` suffix on the multi-month cards conflicts with the arithmetic and is likely a labeling defect. Evidence: [site home](raw/4ebur-net/2026-07-22/screenshots/33-public-site-home.png), [FAQ and testimonials](raw/4ebur-net/2026-07-22/screenshots/34-public-site-mid.png), [pricing](raw/4ebur-net/2026-07-22/screenshots/37-public-site-pricing.png).

The FAQ explains the basic tunnel/IP-hiding model, recommends always-on VPN use and describes onboarding as account → generated key → plan → payment → download. It also makes an absolute claim that user data will not reach government or law-enforcement bodies. That promise is not supportable as an absolute product guarantee. The brand deliberately mixes serious claims with absurd humour about a broader back, whiter teeth, biceps, attention from women and school respect. Influencer cards name itpedia, Алексей Шевцов and JolyGolf; the cards and platform carousel clip horizontally in the 900 px mobile viewport.

The menu routes to Home, Privacy, Terms, Support and access, Available platforms and Account, with Russian language and USD currency controls. Evidence: [mobile menu](raw/4ebur-net/2026-07-22/screenshots/38-public-site-menu.png), [support and access](raw/4ebur-net/2026-07-22/screenshots/40-support-access-clean.png).

## Apple Workaround Instructions

The support page publishes two detailed acquisition workarounds:

- **Change iOS region:** clear Apple balance, account for subscriptions/family-organizer constraints, switch to the United States, accept terms, select no payment method, supply an address and download the app; the article says the region can later be switched back and recommends a second Apple account when subscriptions make switching impractical.
- **Create another-region Apple account:** open Apple’s account site, enter name, target region and date of birth, add email and phone, then confirm both codes. It says a Russian phone may work even with another region but warns the SMS may not arrive; after downloading the needed apps the user can switch back to a Russian-region account.

These guides are unusually aggressive acquisition infrastructure for users blocked by App Store region rules. They are also fragile, depend on third-party platform policy and should not become a core POKROV dependency. Evidence: [region-change guide](raw/4ebur-net/2026-07-22/screenshots/41-guide-change-region.png), [new Apple account guide](raw/4ebur-net/2026-07-22/screenshots/62-guide-new-apple-id-top.png), [steps 2–5](raw/4ebur-net/2026-07-22/screenshots/63-guide-new-apple-id-step2.png), [steps 6–7](raw/4ebur-net/2026-07-22/screenshots/58-guide-new-apple-id-scroll.png).

## Mini App Checkpoint

The platform page exposes a browser product at `pwa.net4eburlab.xyz`, labelled **4ebur.net Mini App**, **BETA**, version `0.34.0`. It reproduces the koala home, Premium, Referrals and Settings navigation. In the anonymous state the Home **Connect** CTA does not create a browser or Android tunnel; it routes directly to Premium. Paid post-checkout behaviour was not tested.

The Mini App paywall has the same value copy and Premium node catalog but materially cheaper direct-channel pricing:

| Market | 1 month | 3 months | 6 months |
| --- | ---: | ---: | ---: |
| Bank country Russia | 299 ₽ | 799 ₽, “10% savings” | 1,500 ₽, “16% savings” |
| Other | $3.50 | $10, “4% savings” | $19, “9% savings” |
| Google Play Android | 489 ₽ | 1,390 ₽ | 2,399 ₽ |

For Russia it offers RUB card, SBP and SberPay. For other countries it exposes account balance, card, Google Pay, Apple Pay, USDT on TRC20/ERC20/TON and USDC on ERC20. No payment method was submitted. Evidence: [Mini App Premium](raw/4ebur-net/2026-07-22/screenshots/44-pwa-premium.png), [country split](raw/4ebur-net/2026-07-22/screenshots/47-pwa-payment-entry.png), [RUB plans](raw/4ebur-net/2026-07-22/screenshots/48-pwa-payment-russia.png), [USD plans](raw/4ebur-net/2026-07-22/screenshots/49-pwa-payment-other.png), [international methods](raw/4ebur-net/2026-07-22/screenshots/50-pwa-payment-method-other.png), [Russian methods](raw/4ebur-net/2026-07-22/screenshots/52-pwa-payment-method-russia.png).

The referral center is unusually complete for a VPN Mini App:

- account balance and Withdraw CTA;
- total rewards and referred-user count;
- withdrawal history and account-operation history, both with explicit empty states;
- personalized Telegram and web referral links;
- **33% of every referred purchase** to the inviter;
- **6 hours of trial access** to the referred friend.

The zero-balance Withdraw control was disabled and caused no mutation. Personalized links and screenshots remain outside the repository. Settings provide licence-key and voucher activation, VLESS routing, support and About. The About page repeats Terms, Privacy, News, Instructions and site destinations. Its “Our site” action opened the bare `net4eburlab.xyz` root, which stayed blank/loading during the controlled check, while personalized site routes had loaded earlier.

## Platform Destination And Distribution Map

| Platform card/action | Observed destination or result |
| --- | --- |
| 4ebur.net website | `net4eburlab.xyz` main site |
| Telegram bot | `t.me/net4ebur_bot` |
| Web version | `pwa.net4eburlab.xyz` Mini App |
| iOS | Apple App Store app `id1662377012` |
| iOS RU | internal `/guide-change-region` workaround |
| Android | Google Play `com.cheburnet.mobile` |
| Windows | immediate direct download `4ebur.net-win-x64-v4.0.1-setup.exe` |
| macOS Apple Silicon | **incorrectly opens the same iOS App Store listing** |
| Chromium | Chrome Web Store extension `bpoljniljbghlopcdaojdpodmnjffdeb` |

The Windows button downloaded a 121,276,488-byte installer, versioned `v4.0.1`, SHA-256 `5f2fc67fde4264d1b546bffee40915785969e331a817b20b951ca66be6a03e45`. It was not executed or retained and was removed from LDPlayer immediately after metadata capture. The Mac misroute was confirmed in Chrome. Evidence: [platform cards](raw/4ebur-net/2026-07-22/screenshots/43-platforms-lower.png), [Windows card before tap](raw/4ebur-net/2026-07-22/screenshots/64-platforms-windows-before-tap.png), [Windows result](raw/4ebur-net/2026-07-22/screenshots/65-windows-button-result.png), [Mac misroute](raw/4ebur-net/2026-07-22/screenshots/66-macos-button-result.png).

Release/distribution is therefore fragmented but active: Android `5.1.0` through Google Play App Bundles, Windows `4.0.1` by direct EXE, Mini App `0.34.0` on the web, iOS through the App Store and Chromium through the Web Store. No official Linux or Firefox product was exposed. The public platform hub is useful, but version parity and destination QA are visibly weak.

## Google Play And Publisher Checkpoint

The current Russian Google Play listing identifies the publisher as **Danyl Kunak**, gives a public developer address in Kam'ianske, Dnipropetrovsk region, Ukraine, and labels the app as containing ads and in-app purchases. This supports an individual public publisher identity; it does **not** establish a registered company or the controller legal entity. The site/policies still identify the contracting party only as “4ebur.net”.

At capture time the listing showed approximately **3.5 stars, 6.96K reviews, 500K+ downloads**, Everyone rating and an update date of **2026-07-02** with only “minor bugs fixed” as release notes. Highlighted review themes included disappearing paid/free servers, regional availability problems including Crimea, slow or absent connectivity and accidental ad-click redirects caused by tiny close controls.

Google Play Data Safety says the app:

- shares **Location** with third parties;
- collects **App info and performance** plus **Device or other IDs**;
- encrypts data in transit;
- accepts data-deletion requests.

The current recommendation shelf included Super VPN Fast Connection, Ultra VPN, NotVPN, VPN Master and v2RayTun, plus the unrelated Netvue Next. Other locale snapshots also surfaced Thunder VPN, WireGuard, MTM Tunnel Lite, Lumos, OpenVPN, PrivadoVPN, IVPN and BeePass. Official listing: [Google Play](https://play.google.com/store/apps/details?id=com.cheburnet.mobile).

## Static APK Checkpoint

The Play artifact is a large React Native/Hermes app: 176,865,224 bytes across base, density, Russian-language and x86_64 splits; 15 DEX payloads; 116 activities, 20 services, 16 receivers and 19 providers; min SDK 28 and target SDK 36. It carries WireGuard, Xray and Amnezia/AWG code plus a very broad ad/mediation footprint including AppLovin/MAX, Appodeal, Google Mobile Ads, Meta Audience Network, Pangle, Chartboost, Fyber, InMobi, ironSource, Mintegral, Moloco, myTarget, Ogury, PubMatic, Smaato, Unity, Vungle, Bigo, BidMachine, PubNative, Amazon ads and Yandex AppMetrica.

Relevant static observations:

- Play billing, `AD_ID`, AdServices Topics/Attribution/Ad ID and legacy storage permissions are declared;
- no camera, microphone, contacts or Android location permission was observed;
- `allowBackup=true`;
- the manifest says cleartext is disabled, but its referenced network-security config permits base cleartext traffic;
- the x86_64 split contains WireGuard/Go/React Native libraries but no HEV/TProxy native library, directly matching the controlled JNI crash;
- APK v3 and Google Play Source Stamp verify with a Google Inc. signer.

Full static evidence: [static summary](raw/4ebur-net/2026-07-22/static-summary.md).

## Material Contradictions And Risks

1. The 2022 privacy page’s narrow Sentry/payment/support disclosure does not describe the 2026 app’s enormous advertising and mediation footprint.
2. “No activity/metadata logs” sits beside Play disclosure of shared Location and collected device/app identifiers; the exact payload boundary was not packet-inspected.
3. No consent or privacy checkpoint appears before a usable anonymous account and ad-capable home.
4. Public legal links carry personalized identity material and create web sessions merely by opening Terms/Privacy.
5. Play, direct web and public-site prices differ sharply, without a clear channel explanation.
6. Terms, privacy, Play payment reality and Mini App payment methods name different processors/methods.
7. The public server catalog differs from the live app catalog.
8. Official-domain language alternates between `4ebur.net` and `net4eburlab.xyz`.
9. Privacy uses an under-13 threshold; Terms require 18+.
10. The Mac platform button is wrong, the bare-site route hung, and the tested x86_64 tunnel path crashes before creating `tun0`.
11. The FAQ’s law-enforcement guarantee is absolute and indefensible.

## What POKROV Should Copy

- Turn anti-blocking into named, understandable products: White list, Bypass and Multihost are much easier to reason about than a raw protocol dropdown.
- Pair each mode with a one-paragraph explanation of path, threat and trade-off.
- Use one dominant connect action, one visible route state and a strong mascot/state illustration.
- Offer a direct web/Mini App purchase and licence-key recovery path independent of app-store billing.
- Build a real referral center with transparent reward rate, friend benefit, balance and history.
- Maintain a single platform hub with verified links, versions and installation guides.
- Show server type and route purpose, not only country and ping/load.

## What POKROV Should Not Copy

- OS permission pressure before value/consent context;
- account secrets in public-looking URLs or legal links that silently create sessions;
- absolute privacy/law-enforcement promises;
- a surveillance-heavy ad stack inside a privacy product;
- an unnamed controller and no governing-law identity;
- contradictory prices, methods, server lists and age rules;
- App Store region workarounds as a core availability strategy;
- comedy mixed into every high-trust claim;
- unverified platform buttons, silent direct downloads and architecture-specific native crashes.

## POKROV Opportunity

The competitive lesson is not to imitate the koala or jokes. It is to package resilience as a product. POKROV can beat this with three explicit connection intents — ordinary privacy, allowlist survival and aggressive bypass — backed by automatic compatibility checks, verified platform destinations, one coherent price system, disclosed ownership and a privacy surface that matches the shipped SDKs. A referral program and direct purchase channel can be added without turning the VPN into an ad-tech bundle.

## Coverage And Teardown

Covered: anonymous first launch; every native tab and settings route; VLESS/Amnezia regions and filters; licence, recovery, voucher and session model; Google Play checkout entry; Privacy/Terms/About/support; website, FAQ, pricing, instructions and platform hub; Mini App home, Premium, payment branching, settings, About, referrals and zero states; Play listing, reviews, recommendations, publisher identity and Data Safety; split APK/static/signing pass; controlled free VLESS attempt.

Blocked or intentionally not executed:

- successful tunnel, disconnect and DNS/HTTPS/route health: **BLOCKED_BY_X86_64_NATIVE_CRASH**;
- paid server behaviour and post-payment Mini App connection: **NOT_PURCHASED**;
- Google Play transaction: **BLOCKED_BY_RUSSIA_PLAY_PAYMENTS**, no order created;
- referral withdrawal, purchase, review, message, session termination or account deletion: **NOT_REQUESTED / NO MUTATION**;
- iOS, Windows, macOS and extension runtime: **NOT_INSTALLED_OR_EXECUTED**;
- Gmail registration: **NOT_NEEDED**, because anonymous/key paths exposed the relevant product.

Final teardown: Chrome and `com.cheburnet.mobile` force-stopped, ADB DevTools forwarding removed, downloaded Windows installer deleted from LDPlayer, and `tun0` absent.

# Vanya VPN — Official Website and Legal Notes

Captured: 2026-07-22<br>
Primary source: <https://vanyavpn.app/><br>
Status: public, unauthenticated pages only; no checkout, payment, registration, login-code request, or account mutation performed.

## App-to-web destination

The Android empty-state button **Купить ключ на нашем сайте** launches an Android browsable intent to the root `https://vanyavpn.app/`. The LDPlayer browser rendered the hero in euros (**€1.9/month**, **€0.5 test**) while the same public page's server-readable Russian copy rendered **190 ₽/month** and a **10 ₽** test. This looks like currency/geo localization, but the conversion and locale rule are not explained on the hero.

## Public positioning and promises

- **Дядя Ваня VPN**; “personal VPN” positioned around 174 countries.
- Claims no more than 10 clients per server and ties that limit to high speed.
- Claims own apps across devices, unlimited device count under one subscription, family sharing, and router access.
- Claims a modern but unnamed VPN protocol, lower heat/battery use, data safety, and high speed.
- Footer simultaneously says the resource is not intended to bypass blocking.
- Support routes to public email and Telegram `@vanyasupport`.

The Android app's **Поддержка** action takes a different route: an external `vova.loan` redirect lands on an `app.chatwoot.com/widget` page. It advertises a GPT-5 assistant, online status, a response within minutes and a **Начать диалог** CTA. The redirect embeds Chatwoot site/conversation credentials in the browser URL. Those values were quarantined outside the repository; no chat was started and no message was sent.

## Current public pricing

Visible Russian tariff grid:

| Offer | Charged amount | Displayed effective monthly price | Displayed saving |
|---|---:|---:|---:|
| 2 years + 6 bonus months | 5,700 ₽ | 190 ₽ | 62% |
| 1 year + 3 bonus months | 4,200 ₽ | 280 ₽ | 44% |
| 6 months + 2 bonus months | 2,800 ₽ | 350 ₽ | 30% |
| 1 month | 500 ₽ | 500 ₽ | baseline |
| “Ванечка” one-day test | 10 ₽ | — | one purchase per person |

The page still says the bonus-month promotion is available **only until 15 July**, although it was live and readable on 22 July 2026. This is stale urgency copy unless a timezone or unannounced extension exists.

The 10 ₽ test automatically rolls into the 500 ₽ monthly tariff unless cancelled. The disclosure appears directly under the test CTA and is repeated in help/legal pages, but current Play reviews include users who perceived the 500 ₽ renewal as unexpected. Treat this as a comprehension failure even if formally disclosed.

## Commercial and usage terms

- One subscription is marketed for unlimited devices and family use.
- The offer permits sharing with close relatives but prohibits wider third-party key transfer.
- Traffic allowance is 500 GB per 30 days; service is automatically suspended at the threshold. Support can raise it to 1 TB, no more than once per 30 days.
- The seller reserves a right to end repeated trial use early and convert to the full tariff without another notice.
- Existing orders auto-renew for an equivalent term at the tariffs current on renewal unless the user cancels.
- Site purchase requires an email address.
- Money-back language says support will first try to fix the service and refund if it cannot; cryptocurrency payments are excluded from refunds.
- Russian card methods are advertised alongside SberPay, Tinkoff Pay and Yandex Pay.

## Cabinet surface visible in public HTML

The unauthenticated cabinet at <https://vanyavpn.app/cabinet> starts with passwordless email OTP: enter email, request a code, wait 30 seconds to resend, then enter the one-time code. A Telegram bot (`@VANYA_VPN_BOT`) duplicates cabinet functions as a resilience channel.

The page's public HTML exposes labels/copy for post-login capabilities, though no customer values were present or captured:

- subscription state, renewal, manual payment and tariff change;
- linked-card replacement and card unlinking;
- current access key and “paste into app” deep-link path;
- a three-day post-purchase upsell from shorter to longer plans;
- Android TV quick-access code and Play/APK distribution;
- “professional” PPTP, OpenVPN and raw Shadowsocks settings;
- adding router locations, downloading OVPN, legacy `ss://` keys and configuration files;
- rotating the access key and closing all cabinet sessions;
- unlimited friend referrals: buyer and inviter each receive one month;
- partner balance, acquisition statistics, and withdrawals via USDT TRC20 or a bank card, advertised with zero fee and same-day daytime processing;
- a partner benefit that gives referred customers a free month after qualifying payment or after trial auto-renewal.

The cancellation journey contains two sequential save offers: first 50% off (250 ₽/month), then a one-time “final” 66% discount (166 ₽/month) before the card-unlink action. This is commercially aggressive and likely effective, but it creates friction at the exact moment the user asks to stop renewal.

## Partner acquisition system

The dedicated public partner page at <https://vanyavpn.app/partners> turns referrals into a real performance-marketing product rather than a single promo code:

- first-payment commission: $3 monthly, $6 half-year, $15 annual and $20 two-year;
- renewal commission: $1, $3, $10 and $15 respectively;
- minimum payout $25, advertised without a hold and within hours;
- payout to Russian/foreign cards or crypto, with RUB conversion at the Russian central-bank rate;
- custom `/r` short links for each channel and per-link clicks, tariff purchases, refunds and earnings;
- a free month for the referred customer and free Vanya access for partners bringing at least five customers/month;
- full $3 monthly commission when a regional one- or three-day trial auto-renews.

The economics and channel-level attribution are stronger than a casual “invite a friend” flow. The risk is incentive alignment: partners are explicitly paid on trial auto-renewal while customer reviews already show renewal confusion. POKROV can copy per-channel attribution and transparent recurring rewards, but should exclude disputed/unclear renewals and add a cooling/refund rule.

## Location merchandising

The public location catalog at <https://vanyavpn.app/locations> does more than list flags. Each claimed location can carry separate badges for current working state, advertised port capacity (100 Mbps, 250 Mbps, 1 Gbps or 10 Gbps), in-app availability, router availability, ChatGPT access and access to Russian websites. It attempts to determine the fastest location for the visitor.

This taxonomy is a useful sales/support pattern because it answers *what this location is good for*, not merely where it is. All 174 entries and their speeds/statuses remain operator claims; no server ownership, capacity or live reachability was independently verified.

## Download and setup ecosystem

The post-purchase app page at <https://vanyavpn.app/app> says “thank you for your purchase” even when opened unauthenticated. It provides first-party distribution or destinations for:

- iOS;
- Android Play and direct APK;
- Windows installer;
- macOS App Store and direct DMG;
- Linux AppImage from an Amazon S3 bucket;
- Android TV Play and direct APK;
- routers.

For Windows 7 it recommends an alternative client hosted in the same S3 bucket. The page then instructs the customer to copy an access key or scan its QR code and states that the same key works on unlimited devices.

The help content confirms the app flow after import: add the `ssconf://` key, tap **Добавить сервер**, then **Подключить**. Location change lives under the server card's three-dot menu and is hidden while connected. Older macOS clients use a legacy `ss://` key and a third-party Shadowsocks client. Windows troubleshooting refers to an `OutlineService.exe` process, strong evidence that at least the desktop implementation inherits Outline components.

The cabinet offers raw Shadowsocks parameters for any alternative client, plus PPTP/OpenVPN for routers. It warns that PPTP/OpenVPN may be blocked by some Russian providers and recommends the app's Shadowsocks path.

The router guide covers ASUS, Huawei, Keenetic, TP-Link, Tenda, Xiaomi, D-Link, MikroTik and ISP-branded routers, recommends Keenetic Extra when the current router lacks a client, and links to Yandex Market. It frequently defaults to PPTP/MPPE and even contains model-specific advice to disable encryption on one Tenda path. That gives Vanya wide legacy-device reach, but PPTP is a weak legacy protocol and should not be copied as a default secure-VPN recommendation. OpenVPN/WireGuard-capable routes should lead, with any legacy fallback carrying a blunt security warning.

## iOS delivery outside the Russian storefront

The official iOS setup page at <https://vanyavpn.app/ios> explicitly says Apple hides VPN applications in the Russian App Store and offers four workarounds:

1. change the App Store region, recommending Kazakhstan and supplying sample address/phone data;
2. obtain credentials for a temporary foreign App Store account from Vanya;
3. join a public TestFlight build named **Дядя Ваня Россия**;
4. open the normal App Store listing from a non-Russian storefront.

The temporary-account route is unusually aggressive. The page says the account should be used only in App Store, not iCloud; asks the user not to improve account security; automatically removes an attached phone after roughly 5–10 minutes; claims mistaken iCloud sessions are ended automatically; and gives one customer exclusive access for about 15 minutes before rotating the password and closing the session. It also advertises using the account to download unrelated restricted apps such as ChatGPT, Netflix and Spotify. The audit did **not** request or expose any credentials. This is a platform, account-security and compliance risk and is not a pattern POKROV should copy.

The public TestFlight page confirms beta distribution, notes that builds can expire after 90 days and that the developer receives install/session/crash/version telemetry. With a public invitation link, Apple says the tester's name and email are not shown to the developer. TestFlight is a practical continuity channel, but it is still beta distribution with expiry and should not be sold as a permanent store substitute.

Official destinations:

- <https://apps.apple.com/us/app/%D0%B4%D1%8F%D0%B4%D1%8F-%D0%B2%D0%B0%D0%BD%D1%8F-vpn/id1618096210>
- <https://testflight.apple.com/join/yumC1Gr2>
- <https://apps.apple.com/us/app/vanyavpn/id6444087613?mt=12>

## Store footprint and release cadence

Google Play showed version 1.20.6 and 1M+ installs. The live public page on 22 July showed 40.6K reviews, a 4.5 overall rating, a 4.6 phone slice and an update date of 19 July 2026; other regional/device views observed during the same audit exposed ratings as low as 3.3, so a single locale-free rating is not reliable. The publisher is shown as **KONDAKOV / Vladimir Kondakov** in Russia. Data Safety says device or other identifiers may be collected, data is not shared, transport is encrypted, and deletion can be requested. The short changelog is only **«Поправили баги»**.

Selected current reviews cluster around connection failures, slow/unresponsive support, new-device failures and surprise at the 500 ₽ renewal after the 10 ₽ test. Positive reviews praise speed and simplicity. One reviewer says split tunneling is missing, although the current Android bundle contains a split-tunneling surface; this may reflect discoverability, rollout or an older build rather than absence.

Apple's iOS history shows a sharp 2026 relaunch after a long quiet period: 1.20.0 on 11 June 2026, 1.17.5 on 9 June and 1.1.6 on 27 May, following 1.1.5 on 7 November 2023. macOS similarly moved to 1.20.0 on 16 June 2026 after releases in June/October 2023. Current notes are generic bug-fix copy; older iOS notes explicitly mention redesign, dynamic keys, locations and QR import. App Store privacy labels list diagnostics as not linked to the user.

Public direct-download timestamps were also fresh on 19–22 July 2026, but timestamps can represent re-uploading. The Android direct APK was statically verified as the same 1.20.6 core/signature as the installed Play build, so it is not treated as a newer release.

## Store recommendation graph

Google Play's public **Similar apps** shelf showed JumpJumpVPN, Yandex Search, VPN Lumos, Thunder VPN, VPNHouse and Windscribe. Apple's **You Might Also Like** shelf showed Buddy VPN, avoVPN, Super VPN Fly 2026, HitProxy, Fusvob VPN, Дед Proxy, Sota Connect, Bear VPN, TipTop VPN and Lite Cat. These are algorithmic store recommendations, not endorsements by Vanya customers; they are useful acquisition/ASO neighbors to audit separately. TipTop is already in the installed LDPlayer inventory.

## Telegram distribution and impersonation surface

The product's own site/cabinet links two attributable Telegram surfaces:

- `@VANYA_VPN_BOT`, a purchase/cabinet bot whose public landing showed about 113K monthly users and advertised a three-day trial;
- `@vanyasupport`, the direct support contact, which links back to that bot.

Neither surface was started or messaged. No official release/news channel is linked from the app or official site, so release discovery currently depends on stores, direct-download timestamps and remotely controlled in-app update metadata.

Search is crowded with unaffiliated channels that label themselves “official”. `@dyadvanya_vpn_official` publishes claims not supported by the audited product (gaming/business/LDAP/advertising-blocking features) and later promotes another VPN bot. `@VanyaVpnNavigator` is an SEO funnel recommending ComfyVPN while presenting itself as Vanya support. `@vanyavpnbo` routes users to another bot. None is linked by Vanya's controlled surfaces; treat them as impersonation/affiliate traffic, not evidence about Vanya. The product needs a signed/canonical public directory of every official domain, bot and channel inside the app.

## Additional delivery/signing entity

The current Windows installer is validly Authenticode-signed by **KONDAKOV&GORIN LLC** with an Arizona/US identity and identifies itself as VanyaVPN 1.20.6. It was inspected as metadata only and was not run. The signer is not explained on the public legal pages.

The Arizona Corporation Commission's official entity record identifies **KONDAKOV&GORIN LLC**, entity 23405407, as a domestic LLC formed 2 August 2022 and shown Active in the accessible record; Vladimir Kondakov and Ilia Gorin are listed as members. The official page's displayed search timestamp is 21 November 2025, and Arizona's new live search UI could not be independently refreshed through the research interface, so July 2026 good-standing status remains **BLOCKED_BY_ACCESS** rather than asserted.

Official record: <https://ecorp.azcc.gov/BusinessSearch/BusinessInfo?entityNumber=23405407>.

Apple lists seller **KONDAKOV OOO**, while Play identifies Vladimir Kondakov as a Russian individual. Apple does not expose a registration number on the listing, and an exact entity match could not be established in the current Russian FNS search. The seller identity is therefore recorded as a store assertion, not silently equated with a particular Russian company.

A separate lookalike domain found in search, `dyadyavanyavpn-ru.com`, claims **ООО КОНДАКОВ** and OGRN 1147746520987 but is not linked by the official product. A live official FNS query shows that OGRN belongs to **ООО «ТВЛ»**, not an entity named Kondakov. Treat the domain as unaffiliated/unsafe until Vanya proves control; do not use its downloads or legal claims.

## Legal entity shown by Vanya

The site footer identifies:

- **CODE ASSET LTD**
- UK company number **16508808**
- registered office: 167–169 Great Portland Street, Fifth Floor, London, W1W 5PF, United Kingdom

UK Companies House currently shows the company as **Active**, incorporated **10 June 2025**, with SIC codes 62012, 62020, 63110 and 63120. Current public filings show **Ermatjon Razzakov** as active director from 23 January 2026. The active person with significant control is **Oleg Solovyov**, notified 6 August 2025, with 75%+ share/voting control and the right to appoint/remove directors. Only names, roles and country-level registry facts are retained here; residential/contact details and dates of birth are deliberately omitted.

Official registry sources:

- <https://find-and-update.company-information.service.gov.uk/company/16508808>
- <https://find-and-update.company-information.service.gov.uk/company/16508808/officers>
- <https://find-and-update.company-information.service.gov.uk/company/16508808/persons-with-significant-control>
- <https://find-and-update.company-information.service.gov.uk/company/16508808/filing-history>

## Legal-quality issues

- The offer describes the service with awkward generic “data-processing services” language and does not clearly name CODE ASSET LTD in the visible opening clause, even though the footer does.
- The personal-data policy includes an obviously unserious deletion clause: it promises to print data, burn the paper in a bucket, upload video proof to YouTube within 24 hours, and pay 100,000 ₽ if the link is late. This undermines the credibility of the entire privacy program and may create a promise the operator cannot safely or lawfully honor.
- The broad site privacy policy is based on Russian-law boilerplate, while the contracting footer points to a UK company and the Play publisher is a Russian individual. Roles of seller, data controller and app publisher are not reconciled.
- The app-specific data policy names Sentry/Firebase and device/crash fields; the broad site policy does not provide a clean product-specific data map, processors, exact retention schedule, or cross-border transfer explanation.

## Source freshness and unresolved checks

- Website and public HTML: observed 2026-07-22.
- Companies House: live official registry, checked 2026-07-22.
- Checkout methods, price charged, delivery timing, refund execution and partner payouts: **not tested**.
- “174 locations”, “≤10 clients/server”, bandwidth, physical/virtual location ownership and unlimited simultaneous devices: marketing claims only; not independently verified.

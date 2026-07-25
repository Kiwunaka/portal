# TipTop VPN — Mobile App Competitor Profile

**Snapshot date:** 2026-07-22<br>
**Status:** `DEEP PASS COMPLETE WITH BLOCKERS` — native UI, account/tasks/growth loop, pricing, settings, support, stores, live tunnel failure/recovery, static package, public funnel, legal/entities and release/distribution surfaces captured; Chrome visual pass, live checkout and current registry ownership/status remain blocked<br>
**Android package:** `com.free.tiptop.vpn.proxy`<br>
**Installed version:** 1.036<br>
**Install source:** Google Play

Evidence root: [`raw/tiptop-vpn/2026-07-22/`](raw/tiptop-vpn/2026-07-22/)

## Audit Checkpoint

- All other VPN processes were stopped and Android `tun0` was absent before launch.
- TipTop and every other VPN package are force-stopped. Android `tun0` is absent and the emulator's ordinary DNS/HTTPS baseline was restored before moving to the next competitor.
- Purchase, review submission, public/support messaging and destructive account actions remain out of scope.
- Cold launch resolved to `com.tiptopvpn.app.ui.SplashActivity` and took about 3.6 seconds at the Android activity layer.
- Roughly three seconds later the app was still on a white branded loading screen: **«Загрузка / Пожалуйста подождите…»**. Process memory at this point was about 88.9 MB total PSS / 180.1 MB RSS with no swap; `tun0` remained absent.

Evidence: [isolated loading screen](raw/tiptop-vpn/2026-07-22/screenshots/01-isolated-launch.png).

Next competitor: Red Shield VPN, still under the one-app-at-a-time isolation rule.

## Bootstrap And Privacy Gate

The launch was slow rather than permanently hung. The bootstrap API completed with HTTP 200 after roughly **30.3 seconds**, then the app fetched a separate Russian language bundle and advanced to a mandatory privacy gate. This creates a poor first impression on a clean install because the splash has no timeout, progress detail, cached fallback or retry affordance.

The mandatory page is titled **«Ваша конфиденциальность на первом месте»** and says the app collects the minimum needed for operation:

- OS version, device model, language and screen size, explained as necessary for appearance and reliable operation;
- email, explained as needed for login and subscription recognition;
- anonymized analytics for product improvement and error tracking.

It additionally claims no access logs, no sale of information to third parties and no tracking of online activity. The only primary action is **«Согласиться и продолжить»**; there is no decline/exit choice. A styled privacy-policy link is embedded in the body. Evidence: [privacy gate](raw/tiptop-vpn/2026-07-22/screenshots/03-after-40s.png).

Runtime evidence is broader than this friendly summary: before consent, the bundled mediation SDK initialized and assembled device/app/session telemetry including advertising-ID state, carrier, timezone, locale, device model, OS, connection type, storage/battery and emulator/root-like signals. Its external mediation endpoint failed DNS resolution, but the attempt occurred before the user accepted the policy. Raw logs, request signatures, per-install identifiers and service configuration are quarantined outside the worktree.

The bootstrap response drives much of the product remotely: available languages, legal/support URLs, premium locations and prices, feature switches, protocol availability, ads, banners, tasks, referrals and the full localized copy dictionary. That makes TipTop operationally agile but also gives a single slow control-plane call the power to block the entire first run.

The underlined privacy-policy phrase looks interactive, but three taps across its visible bounds did nothing and no clickable accessibility node exists. The configured destination is `tiptopvpn.org/ru/terms/#privacy-policy`; the mandatory gate therefore visually promises detail without providing a working in-context route in this build.

## Onboarding And First Home

Consent leads to a conventional three-card carousel with original animated shield characters:

1. **«Наслаждайтесь любимыми сайтами»** — access to sites, services, apps and social networks;
2. **«Абсолютная анонимность и безопасность»** — no stored/shared browsing history, hidden IP and encrypted traffic;
3. **«Быстрые сервера по всей планете»** — any server worldwide at maximum possible speed.

Every slide has **«Пропустить»**, a three-position indicator and Continue/Start CTA. The illustrations are friendly and visually coherent, but the second card makes the absolute claim **«Абсолютная анонимность»**, and the Russian copy contains errors such as lowercase “ip” and the grammatically wrong form **«расположенному»** on slide 3. Evidence: [slide 1](raw/tiptop-vpn/2026-07-22/screenshots/05-after-policy-consent.png), [slide 2](raw/tiptop-vpn/2026-07-22/screenshots/06-onboarding-slide-2.png), [slide 3](raw/tiptop-vpn/2026-07-22/screenshots/07-onboarding-slide-3.png).

Immediately after onboarding, Android notification permission appears without an in-app rationale and was denied. Behind it, the app had already placed a large **«Пожалуйста оставьте отзыв!»** banner despite zero successful connections. No review was opened or submitted. Evidence: [permission plus premature review banner](raw/tiptop-vpn/2026-07-22/screenshots/08-after-onboarding.png).

The guest home is a sparse four-tab shell: **VPN / Премиум / Задания / Настройки**. Its center is a large animated connect switch and **«Отключено»** status; the bottom offers a **«Только для соц. сетей»** toggle with explainer and **«Самая быстрая локация»** server picker. The review banner consumes the most prominent area above the primary task. Evidence: [first home](raw/tiptop-vpn/2026-07-22/screenshots/09-home-first-view.png).

## Social-only Mode And Location Picker

The **«Только для соц. сетей»** switch is a consumer-friendly preset for selective routing. Its explainer says the VPN will work only for YouTube, Instagram, Facebook, Twitter, TikTok, LinkedIn, Discord and Viber, followed by the retention-oriented instruction **«Включите VPN и больше не выключайте!»**. This is easier to understand than a technical per-app split-tunnelling list, although the copy does not explain what happens to browsers, embedded web views or links opened from those apps. Evidence: [social-mode explainer](raw/tiptop-vpn/2026-07-22/screenshots/10-social-mode-info.png).

The location picker exposes search and one usable free choice:

- **«Самая быстрая локация»**, explicitly marked **«Ограниченная скорость»**;
- 12 locked premium locations, all marked **«Без ограничений скорости»**: London, Amsterdam, Frankfurt, Zurich, Sandefjord, Washington, Šiauliai, Sofia, Tirana, Stockholm, Almaty and Istanbul.

There is no manually selectable free country. Repeated taps on several locked rows left the user on the same list with no paywall, toast, animation or other feedback, despite those rows being exposed as clickable accessibility nodes. This looks like a broken monetization handoff, not a deliberate upsell. The list itself is supplied by remote configuration rather than hard-coded in the client. Evidence: [upper location list](raw/tiptop-vpn/2026-07-22/screenshots/11-server-list.png), [lower location list](raw/tiptop-vpn/2026-07-22/screenshots/12-server-list-lower.png), [unchanged list after a locked-location tap](raw/tiptop-vpn/2026-07-22/screenshots/13-locked-server-result.png).

## Premium Paywall

The native premium tab uses a crowned version of the shield character, the title **«СУПЕР ПРЕМИУМ»**, three selectable plans and a single **«Попробовать»** CTA:

| Plan | Native Google Play price | Displayed monthly equivalent |
| --- | ---: | ---: |
| 1 month | 499 RUB | 499 RUB/month |
| 6 months | 1,990 RUB | 331.66 RUB/month |
| 1 year | 2,490 RUB | 207.5 RUB/month |

The benefit list promises every location, unlimited speed, unlimited traffic and up to five devices. The page also says **«Можно отменить в любое время»**. It does not visibly quantify the six-month saving (about 33.5% against six monthly renewals) or annual saving (about 58.4%), even though the arithmetic is a strong conversion argument. Evidence: [monthly plan](raw/tiptop-vpn/2026-07-22/screenshots/15-premium-tab.png), [annual plan selected](raw/tiptop-vpn/2026-07-22/screenshots/16-premium-annual-selected.png).

The remote fallback catalogue is materially different: USD 10/month, USD 50/six months and USD 100/year, plus a non-native USD 150/three-year option and a hidden USD 1 special offer. Google Play billing replaces those fallbacks with localized RUB products in this session; the three-year and special-offer options are not shown. This separation gives the operator pricing agility, but it also creates more places for campaign copy and checkout truth to drift.

The CTA **«Попробовать»** suggests a trial. Remote copy contains a seven-day-trial banner, yet the visible main paywall does not state a trial duration, renewal date or post-trial charge before checkout. The purchase CTA was not pressed, so no transaction or checkout was initiated.

## Tasks And Authentication Entry

The **«Задания»** tab gamifies both product setup and acquisition under the headline **«ВЫПОЛНЯЙ ЗАДАНИЯ — ПОЛУЧАЙ УЛУЧШЕНИЯ»**. For a guest it shows:

- available now: **«Авторизоваться» → «Скорость +5»**;
- locked until authorization: **«Оставить отзыв» → «Скорость +5»**;
- locked until authorization: **«Поделиться приложением» → «Скорость +5»**;
- locked until authorization: **«Привести друга» → «Бесплатный премиум»**.

This is an unusually direct growth loop: a constrained free tier turns account creation, store reputation and distribution into permanent-looking performance upgrades rather than abstract points. It also risks making speed feel intentionally degraded until users perform promotional labor. No review, share action or referral was initiated. Evidence: [guest tasks tab](raw/tiptop-vpn/2026-07-22/screenshots/17-tasks-tab.png).

Opening the authorization task shows a dedicated illustrated email form. Its only explanation is **«Авторизация и ввод email требуется для поддержания качества работы VPN»**, which does not clearly explain the actual account, device-sync or reward purpose. The form offers an email field, **«Авторизироваться»** and a Google sign-in button. It does not distinguish sign-in from account creation, show a password field or place legal/consent links near the action. Evidence: [authentication entry](raw/tiptop-vpn/2026-07-22/screenshots/18-task-auth-entry.png).

The email path is passwordless: submitting an address sends a four-digit one-time code and opens a four-cell confirmation screen with **«Подтвердить»** and **«Выслать новый код»**. A test account was created using the explicitly authorized connected mailbox; the address, code and confirmation captures are retained only in the quarantined sensitive-evidence directory. After verification, **«Авторизоваться»** moved to **«ВЫПОЛНЕНО»** and the review/share tasks became active. Evidence: [post-auth task state](raw/tiptop-vpn/2026-07-22/screenshots/19-tasks-after-auth-attempt.png).

The reward validation is weak or misleading in this build:

- a single tap on **«Оставить отзыв»** did not open Google Play and did not ask for a rating, but immediately moved the task into the green completed list and represented its **«Скорость +5»** reward as earned;
- **«Привести друга»** also appeared green and completed immediately after account creation even though no invite was created, shared or redeemed; tapping the completed row did nothing;
- **«Поделиться приложением»** first opens a custom Facebook / Instagram / X / **«Другое»** chooser; **«Другое»** opens Android's share resolver. Cancelling both layers left the task incomplete, and no content was sent.

This means review/referral completion cannot be treated as proof of the promised acquisition event. It may also teach users that the task system can be farmed without doing what the copy requests. Evidence: [custom channel chooser](raw/tiptop-vpn/2026-07-22/screenshots/22-share-chooser.png), [Android share resolver](raw/tiptop-vpn/2026-07-22/screenshots/23-system-share-sheet.png), [task state after cancelling share](raw/tiptop-vpn/2026-07-22/ui/25-tasks-after-cancelled-share.xml).

## Settings, Support And Account

The settings hub contains application settings, help, account, promo code, about, share and rate routes. Evidence: [settings hub](raw/tiptop-vpn/2026-07-22/screenshots/25-settings-top.png).

Application settings expose:

- **Autoconnect**, off by default, described as starting the VPN whenever the app launches;
- **KillSwitch**, implemented as instructions for Android's system-level Always-on VPN and **Block connections without VPN** controls rather than as an in-app switch;
- **«Сплит система»**, a bypass-only installed-app list with **«Выделить все приложения»**; it includes other VPN clients and low-level system packages such as navigation-bar components, making an indiscriminate select-all risky and hard to understand;
- an optional API-only proxy, explicitly said not to affect the VPN tunnel; it accepts HTTPS or SOCKS, host, port and optional credentials, then offers a connection test/save action;
- system/light/dark themes;
- 14 languages: English, Russian, Spanish, Italian, German, French, Portuguese, Ukrainian, Indonesian, Turkish, Korean, Japanese, Persian and Arabic.

The KillSwitch instructions contain a mixed-alphabet typo, **«Cледуйте»** with a Latin `C`. Evidence: [application settings](raw/tiptop-vpn/2026-07-22/screenshots/26-app-settings.png), [KillSwitch instructions](raw/tiptop-vpn/2026-07-22/screenshots/27-killswitch.png), [split-system list](raw/tiptop-vpn/2026-07-22/screenshots/28-split-system.png), [API proxy](raw/tiptop-vpn/2026-07-22/screenshots/29-proxy-settings.png), [themes](raw/tiptop-vpn/2026-07-22/screenshots/30-theme-dialog.png), [languages](raw/tiptop-vpn/2026-07-22/screenshots/31-language-list.png).

Help has only **FAQ** and **«Задать вопрос»**. FAQ opens `https://tiptopvpn.org/ru/support/` in Chrome; in this capture the page remained blank/loading for more than ten seconds and Chrome briefly labelled the connection not secure. The support route is an in-app form with a default **«Техническая проблема»** subject, prefilled account email, large message field, optional **«Отправить техническую информацию»** checkbox and Send CTA. No message or technical data was sent; the email-bearing capture stays in sensitive quarantine. Evidence: [help menu](raw/tiptop-vpn/2026-07-22/screenshots/32-help.png), [FAQ destination](raw/tiptop-vpn/2026-07-22/screenshots/33-faq-destination.png).

The authenticated account page shows email, **«Тип подписки “Бесплатный”»**, a copyable user ID, **«Улучшить VPN»**, logout and an in-app delete-account action. No logout or deletion was attempted. The promo page accepts a code, includes a clipboard-paste affordance and promises an unspecified **«подарок»**. Evidence: [promo-code page](raw/tiptop-vpn/2026-07-22/screenshots/35-promo-code.png). Account evidence is quarantined because it contains identifiers.

About is extremely thin: shield art, version 1.036, generic copyright, Privacy Policy and Terms of Use. It names no legal entity or jurisdiction. The two links resolve respectively to `https://tiptopvpn.org/ru/terms/#privacy-policy` and `https://tiptopvpn.org/ru/terms/#terms-conditions`; unlike the dead privacy link in first-run consent, these buttons successfully hand off to Chrome. Evidence: [About](raw/tiptop-vpn/2026-07-22/screenshots/36-about.png), [privacy destination](raw/tiptop-vpn/2026-07-22/ui/43-privacy-link-destination.xml), [terms destination](raw/tiptop-vpn/2026-07-22/ui/44-terms-link-destination.xml).

## Google Play Listing And Store Discovery

The Settings **«Оценить приложение»** route successfully opens the live Google Play detail page, even though the reward-task equivalent did not. At capture time Play showed:

- developer name **TipTopNet**;
- **4.5** average from **748,916** reviews and **10M+** downloads;
- age rating 3+, ads and in-app purchases;
- #5 in free Tools;
- last update **17 July 2025**;
- a generic release note: the “first update in a series of future updates” intended to improve stability and security;
- six portrait store screenshots.

Evidence: [listing top](raw/tiptop-vpn/2026-07-22/screenshots/37-rate-app-destination.png), [listing description](raw/tiptop-vpn/2026-07-22/screenshots/38-play-description.png), [ratings and reviews](raw/tiptop-vpn/2026-07-22/screenshots/39-play-lower-1.png).

The store description is badly out of sync with the tested product. It claims three selectable free locations, Russian servers, 23 named countries, OpenVPN/IKEv2/WireGuard, no ads, unlimited speed/use and support at `tiptop-vpn.com`. Runtime exposed one automatically selected free location with limited speed, 12 differently composed premium locations and remote-enabled `ovpn_tcp_x`/VLESS; it initialized several ad SDKs and used `tiptopvpn.org` for in-app support/legal links. The copy also promotes adult-content anonymity, PUBG, access to Russian banking/government services and broad ISP invisibility. This aggressive keyword coverage may help acquisition, but it creates concrete product, protocol and trust contradictions. Full captured text: [Play description XML](raw/tiptop-vpn/2026-07-22/ui/46-play-description.xml).

Visible review distribution was 80% five-star, 7% four-star, 2% three-star, 1% two-star and 7% one-star (Play's rounded values do not sum to 100%). The featured reviews repeatedly praise initial simplicity/speed but report intermittent failure, endless connection, **«нет свободных серверов»**, traffic being blocked until disconnect and regressions after updates. One featured five-star review explicitly changed its narrative to describe deterioration after more than six months. Evidence: [featured reviews, upper](raw/tiptop-vpn/2026-07-22/ui/47-play-lower-1.xml), [featured reviews, lower](raw/tiptop-vpn/2026-07-22/ui/48-play-lower-2.xml).

Play's **«Похожие приложения»** module recommended Windscribe VPN and Aloha Browser with Private VPN, followed by contextually weaker Banki.ru and 2GIS results. The TipTopNet developer shelf contained only two other small products visible in this session: **«Игра в Слова — Остров Слов»** (5K+ downloads) and **«Бросаю курить»** (100+). Evidence: [similar apps and developer shelf](raw/tiptop-vpn/2026-07-22/screenshots/41-play-lower-3.png).

The developer's Play Data Safety declaration says:

- app interactions may be shared for analytics;
- collected app interactions are used for analytics;
- device/other identifiers are used for app functionality, analytics and fraud/security/compliance;
- email is used for app functionality, developer communication, fraud/security/compliance and account management;
- user IDs are used for app functionality and analytics;
- purchase history is used for fraud/security/compliance;
- crash logs are used for analytics and fraud/security/compliance; diagnostics for analytics; other performance data for functionality, analytics and fraud/security/compliance;
- data is encrypted in transit, and account/data deletion can be requested in-app.

The declaration is directionally consistent with the observed account and telemetry systems, but the first-run privacy summary is much narrower and never explains the declared sharing of app-interaction history. Evidence: [Data Safety overview](raw/tiptop-vpn/2026-07-22/screenshots/43-play-data-safety.png), [collected-data categories](raw/tiptop-vpn/2026-07-22/screenshots/44-play-data-collected.png), [purposes and deletion](raw/tiptop-vpn/2026-07-22/screenshots/45-play-data-safety-bottom.png).

Google Play is the first inspected product surface that names an operator: **TipTopNet Limited**, with the developer address **Rm 2A 17/F Glenealy Tower, 1 Glenealy, Hong Kong**, a `+44` mobile number, public support addresses at `tiptop-vpn.com`, and `https://tiptop-vpn.com` as the developer site. Evidence: [expanded Play support/developer section](raw/tiptop-vpn/2026-07-22/ui/64-play-support-lower.xml), [developer-site destination](raw/tiptop-vpn/2026-07-22/ui/65-play-site-destination.xml).

The Play **«Конфиденциальность»** button is miswired: it opens `https://tiptop-vpn.com/terms/#terms-conditions`, not a privacy-policy anchor. This adds a third legal-link inconsistency: the store uses the hyphenated `.com` domain, the app uses non-hyphenated `tiptopvpn.org`, and the first-run privacy phrase on the latter domain is visually styled but inert. Evidence: [Play privacy destination](raw/tiptop-vpn/2026-07-22/ui/66-play-privacy-destination.xml).

## Public Website, Pricing And Product Reach

The current official-site hero has pivoted from generic free-VPN language to **“VPN for ChatGPT and global services”**. It sells correct regional access for AI tools, work/cloud platforms and streaming, then stacks public-Wi-Fi, travel, banking and entertainment cases. This is a sharp current-demand acquisition frame, but it repeatedly escalates into absolute anonymity, total encryption, no-log, 10 Gbps and flawless-streaming claims without published technical proof.

The site presents a much larger product than the tested Android build: 320+ servers in 57 countries on the download page, but 125 servers / 25 locations / 20 countries on the dedicated location page, whose rendered table names only 17 countries. Google Play says 23 countries; Android exposed one automatic limited free choice and 12 locked premium choices. Inventory truth is therefore inconsistent across four first-party/current surfaces.

Website pricing is USD 9.90/month, USD 58.80/year and USD 104.40/three years. The one-month card promises only a three-day refund while adjacent page/support copy promises 30 days for all new customers; legal text says fees are non-refundable unless another policy applies. The site also advertises a seven-day trial and 10+ card/crypto/e-money methods. No checkout was initiated. None of these offers matches the Android RUB plan set exactly, and the Android paywall does not clearly disclose the advertised trial before its untouched CTA.

The public route system covers pricing, downloads, locations, Support, passwordless cabinet login, terms/privacy, Google Play and App Store. Android and iOS are the only delivered clients: Windows, macOS, browser and TV sections remain **Coming Soon**, although Support incorrectly tells users to download Windows/macOS installers. The primary Try Free/tariff action resolved back to the homepage in the text-browser pass rather than to checkout. Full route, claim, pricing and content map: [public-surface notes](raw/tiptop-vpn/2026-07-22/logs/public-surface-notes.md).

Apple provides an important second product branch: its US listing showed 4.7 from 7.8K ratings, seller TipTopNet Limited, developer label Free VPN Network and a version history ending at numeric version 5 on 11 July 2024. Version 4 removed required registration; version 5 added invite codes and stability fixes. Its USD 8.99 / 39.99 / 59.99 subscription set and USD 2.99 special offer differ from both Android and web. Apple declares identity-linked email, support content, user/device identifiers and product-interaction analytics plus non-linked diagnostics. The iOS build therefore appears a year behind the authoritative Android artifact and has a separate pricing/release line.

## Legal Entities And Privacy Truth

The official Hong Kong Companies Registry incorporation list records **TipTopNet Limited**, company number **3291327**, incorporated **21 June 2023**. Google Play and Apple use that seller/operator name; Play provides a Hong Kong address. Current Russian site footers instead identify **ОсОО «ТипТопНет Лимитед» (308685-3301-ООО)** in Kyrgyzstan, while English footers collapse ownership to the brand. The `tiptopvpn.org` legal template names the Hong Kong company, but the hyphenated `.com` copy replaces it with the non-entity label “TipTop VPN”. A current status/ownership extract and documented relationship between the Hong Kong and Kyrgyz entities remain `BLOCKED_BY_ACCESS`.

The June 2023 privacy text is especially problematic for the brand's trust story. It permits collecting IP addresses, connection timestamps, bandwidth use and **internet activity**, plus analytics/marketing use and provider/legal disclosure, with only purpose-based undefined retention. The product simultaneously claims it stores no activity logs, shares/sells nothing and leaves visited sites known only to the user. The legal page also says the service is not intended for under-18s, against 3+/4+ store ratings. This is not merely imprecise copy; these are mutually incompatible data and audience contracts.

## Static Package And Release Mechanism

The installed Google Play artifact is a large modular native Android product with remote-configured UX rather than a thin shell. It contains both OpenVPN and sing-box VPN paths, substantial first-party account/task/settings/purchase code, and native-library capability for VLESS, VMess, Trojan, Shadowsocks, WireGuard, Hysteria, TUIC, Reality, QUIC/gRPC, SOCKS5/Xray and OpenVPN. Bundling is not proof each protocol is live: runtime used sing-box and the fetched configuration exposed only a narrower set.

The manifest requests broad app/network/advertising capabilities including `QUERY_ALL_PACKAGES` and exposes several OpenVPN API/remote-action components. They were not probed; this remains a static attack-surface observation requiring owner-side caller/authorization review. The modern sing-box VPN service is non-exported.

The package carries an unusually wide advertising/mediation surface plus Firebase and profiling/crash tooling. Static presence alone is not runtime activation evidence, but runtime logs confirmed device/session mediation telemetry before consent. Roughly 263 flag assets versus 12 live premium locations reinforce the server-controlled/dormant-catalogue model.

Google Play provenance is strong: v1/v2/v3 signatures, one signer, Google Play source stamp and a stamp timestamp of **2025-07-17 12:39:09Z**, matching Play's update date. No APK-install permission or Play in-app-update package was found, so binary releases appear store-managed; major pricing, location, protocol, ad, task and copy changes can ship through bootstrap configuration. Third-party archives suggest versions 1.019 → 1.021 → 1.030/1.031 → 1.033 → 1.036 from late 2023 to July 2025, but their upload dates conflict and are retained only as low-confidence history. Full redacted evidence: [static-package notes](raw/tiptop-vpn/2026-07-22/logs/static-package-notes.md), [public/release notes](raw/tiptop-vpn/2026-07-22/logs/public-surface-notes.md).

## What POKROV Should Learn From TipTop

The strongest ideas worth adapting are the readable social-only preset, passwordless account continuity, a single remote product catalogue, automatic fastest-location framing, explicit five-device benefit, native promo/referral hooks and current-demand landing pages for concrete services such as AI/work tools. The task/reward screen is a particularly aggressive activation mechanism, but rewards should be earned only after verifiable product events; tying speed to reviews/shares is manipulative and can create store-policy and trust risk.

Do not copy TipTop's absolute anonymity/no-log wording, dead legal links, store/site/app inventory drift, ambiguous trial CTA, broad pre-consent ad telemetry or its green “connected” state without functional DNS/HTTPS validation. The more defensible version for POKROV is equally concrete and energetic but backed by one canonical operator, one machine-fed price/location catalogue, visible trial/renewal terms, post-connect health checks and honest reward semantics.

## Controlled Free-tunnel Test

The central control is a swipe slider rather than a tap button. On first use TipTop shows its own bottom sheet explaining that an Android VPN profile is required, then hands off to the standard system trust warning. Granting permission merely returns home; the user must swipe the control again to start connecting. Evidence: [in-app permission rationale](raw/tiptop-vpn/2026-07-22/screenshots/49-connect-first-tap.png), [Android VPN permission](raw/tiptop-vpn/2026-07-22/screenshots/50-system-vpn-permission.png).

The first connection attempt failed immediately with **«Error / Нет доступных серверов»**, matching a prominent recent Play complaint. A second attempt entered a long animated state with only **«Отмена»**, then eventually rendered **«Подключено»** and a running session timer. Android runtime evidence confirmed a real `tun0`, full IPv4 and IPv6 default routes, MTU 1400 and a VPN transport identified as **sing-box**; the system classified it as validated. Raw interface addresses, DNS addresses and connection material remain in sensitive quarantine. Evidence: [no-server error](raw/tiptop-vpn/2026-07-22/screenshots/51-after-connect-slide.png), [long connecting state](raw/tiptop-vpn/2026-07-22/screenshots/52-connect-retry.png), [connected UI](raw/tiptop-vpn/2026-07-22/screenshots/53-connect-after-wait.png).

Functional connectivity did not match the green state: numeric-IP ICMP was reachable, but DNS resolution failed and HTTPS requests returned no response throughout repeated checks while `tun0` was active. After swiping off, the UI immediately said **«Отключено»**; `tun0` disappeared several seconds later, but DNS/HTTPS were still broken at the next baseline check.

The control test is now complete. All VPN apps were force-stopped, no VPN interface was present, Android Wi-Fi was explicitly re-enabled, the saved LDPlayer network was reconnected, and the same emulator was rebooted. The clean post-reset baseline then passed both hostname ICMP and HTTPS (`example.com` returned HTTP 200; Google's connectivity endpoint returned 204) with `tun0` absent. This narrows the failure to the TipTop connection/disconnection episode rather than a persistent host NAT fault: the app reported a validated/connected VPN that could not resolve or complete HTTPS, and ordinary connectivity did not recover merely by disconnecting the tunnel. Recovery required resetting the emulator's Wi-Fi path. Evidence: [post-disconnect UI](raw/tiptop-vpn/2026-07-22/screenshots/54-after-disconnect.png); raw network diagnostics are quarantined because they include addresses and routing material.

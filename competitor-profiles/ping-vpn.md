# Ping VPN — Mobile App Competitor Profile

**Snapshot date:** 2026-07-22
**Status:** `DEEP PASS COMPLETE WITH BLOCKERS` — native startup is blocked by remote bootstrap; store creatives, package architecture, website/legal/entity, release, reviews and Telegram growth surfaces are captured
**Android package:** `com.pingsecure.client.app`
**Installed version:** 1.1.19
**Install source:** Google Play

Evidence root: [`raw/ping-vpn/2026-07-22/`](raw/ping-vpn/2026-07-22/)

## Audit Checkpoint

- Start state: all 16 competitor processes stopped and Android `tun0` absent.
- Only Ping VPN will be active during native exploration; it will be force-stopped before the next competitor.
- Purchase, review, public-post, support-send and destructive account actions are out of scope.
- Account identifiers, credentials, public/current IPs, VPN endpoints, provider tokens and raw configs stay outside the worktree.
- Installed build: `1.1.19` (`versionCode 63`), min SDK 24, target SDK 36, Google Play installer, launcher `.MainActivity`.
- End state: Ping force-stopped, all 16 competitor package processes absent and Android `tun0` absent before the next app.

Google Play confirms Ping is in the same **F2P** publisher portfolio as Огонь and Батя. Shared publisher does not by itself prove a shared backend or shared legal terms.

## Isolated First Launch And Startup Blocker

Cold launch opens a white bootstrap screen rather than an onboarding carousel. It says **Ping VPN**, **«Подбираем самые быстрые серверы…»** and **«Запуск занимает примерно 30 секунд»**, with a small yellow spinner. Evidence: [isolated bootstrap](raw/ping-vpn/2026-07-22/screenshots/01-isolated-launch.png).

After roughly 30 seconds the bootstrap failed with a modal: **«Упс! Что-то пошло не так»**, **«Пожалуйста, попробуйте ещё раз. Если ошибка повторяется, сообщите в поддержку.»** Actions are **Contact support**, **Cancel** and **Retry**. One controlled retry produced the identical error after another loading interval. This is currently a hard startup/backend blocker, not a transient one-frame observation. Evidence: [first failure](raw/ping-vpn/2026-07-22/screenshots/02-loaded-or-blocker.png), [retry failure](raw/ping-vpn/2026-07-22/screenshots/03-retry-result.png).

A third controlled clean launch reproduced the same failure. A quarantined logcat pass found no actionable HTTP status or native crash: Flutter handled the backend/configuration failure inside the app while the emulator emitted unrelated rendering noise. A numeric `1504` in EGL output is not an HTTP 504. The exact failing request remains unknown because raw network destinations were not retained.

The experience is unusually honest about a potentially long first start, but the promise itself normalizes a 30-second cold launch. On failure it keeps a direct support route available instead of crashing or leaving an infinite spinner.

## In-App Feedback Surface

The error's support action opens a native **«Обратная связь»** form inside Ping rather than an external messenger. It asks for name, email and message, says the reply will arrive by email, and exposes a large **Send** CTA. Empty submission is blocked with **«Форма не заполнена» / «Пожалуйста, заполните все поля перед отправкой.»** No personal data was entered and no message was sent.

The form is functional enough to validate empty state, but its placeholder/secondary text is extremely low-contrast on white, and a large blank block below an **«или»** divider contains no visible alternate contact action in the captured state. Telegram and WhatsApp artwork is present in the package, so remotely missing alternate-contact buttons are plausible but unconfirmed. Evidence: [feedback form](raw/ping-vpn/2026-07-22/screenshots/04-support-destination.png), [empty validation](raw/ping-vpn/2026-07-22/screenshots/05-empty-feedback-validation.png).

Cancel closes Ping and returns to the LDPlayer launcher rather than leaving a recoverable offline shell. Evidence: [cancel result](raw/ping-vpn/2026-07-22/screenshots/06-cancel-result.png).

## Core Product Reconstructed From Official Creatives

Because the current installed build never passes bootstrap, core-product claims below are bounded to official Google Play creatives and package evidence rather than represented as live runtime results.

The store shows four principal surfaces:

- a connected dashboard with protected state, current region/city, active time, download/upload/total traffic and a large disconnect action;
- a searchable **All / Favorites** location selector with a fastest-server row, cities and heart favorites;
- settings for user ID/copy, language, theme, auto-connect, Terms, Privacy and Support;
- a custom-URL form with name, URL and Save, paired with app/site tunnelling copy.

The bottom navigation is **VPN / Туннелирование / Настройки**. The server creative shows Sweden/Stockholm, Finland/Helsinki, France/Paris, Netherlands/Amsterdam and Switzerland/Zurich in its visible portion. The settings creative labels itself `1.1.13 (48)`, so it is stale relative to the installed `1.1.19 (63)` build.

Evidence: [connected home](raw/ping-vpn/2026-07-22/screenshots/store-01-hires.jpg), [server selector](raw/ping-vpn/2026-07-22/screenshots/store-02-hires.jpg), [settings](raw/ping-vpn/2026-07-22/screenshots/store-03-hires.jpg), [custom URL](raw/ping-vpn/2026-07-22/screenshots/store-04-hires.jpg).

An embedded catalog names 233 services/sites across messaging, social, video, games, banks, government and shopping. It includes Telegram, WhatsApp, Instagram, YouTube, Netflix, Госуслуги, Сбербанк, ChatGPT and OpenAI. This is a strong implementation clue that “Smart mode” supports curated site/service routing in addition to per-app and custom-URL entry. Raw URLs were not retained.

## Monetization And Claim Conflict

Current Google Play copy repeatedly says **completely free**, **no subscriptions**, **no ads** and **no registration**. The broader evidence directly contradicts that positioning:

- Google Play Billing, premium and restore-purchase assets are compiled into the installed build;
- the privacy policy explicitly describes Appodeal advertising and personalized-ad data;
- the APK bundles a large mediation stack spanning Appodeal, AdMob, LevelPlay/IronSource, AppLovin, Meta, Yandex Ads, Unity Ads, Vungle, MyTarget, Mintegral and other bidders;
- the official Telegram channel publishes winners of subscriptions **without ads and limits**;
- current reviews describe connect/disconnect ads, removed free location choice, time limits and premium gating.

SDK presence by itself would be weak evidence, but the first-party policy/channel and review surface make this a hard claim-consistency failure. The most likely explanation is that acquisition copy was not updated after monetization changed or that features are segmented by cohort/region; the audit cannot distinguish those two possibilities.

The website adds a second contradiction: it markets one Ping subscription for up to ten devices and “premium plans,” while Play says no subscription. It also says Ping is independent from advertisers even though the policy and package show an ad-funded product.

## Android Architecture

The Flutter build targets SDK 36, declares a native Android VPN service and uses Go/tun2socks components. Compiled identifiers in the native library are associated with Xray/V2Ray, VMess, VLESS, Trojan, Shadowsocks, WireGuard, Hysteria, QUIC, SOCKS5, gRPC and Reality; they prove compiled capability/signatures, not that every protocol is exposed in the product.

The package is about 81.7 MB across Google Play splits. Advertising/measurement components include AppMetrica, Firebase Analytics/Crashlytics and the broad bidder stack above. WorkManager and boot receivers provide background scheduling. No clear direct-APK/self-update component or Play Core updater was identified.

Redacted evidence: [static package notes](raw/ping-vpn/2026-07-22/logs/static-package-notes.md).

## Website, Instructions And Dead Destinations

The English one-page website exposes Features, Reviews, FAQ and Download sections but no real instruction library. Its four FAQ answers are effectively the entire public help surface. Platform cards advertise macOS, Android, iPhone/iPad, Chrome and Windows but are decorative and do not lead to a store or file. The main CTA merely scrolls to those dead cards. Bounded exact-brand searches found only the Android listing.

The FAQ contains an unmistakable adaptation defect: the streaming answer names **Plus, Unlimited, Visionary and Family**, Proton VPN's plan family, and matches Proton's current homepage wording. Other Proton-shaped claims—ten devices, Netflix/Hulu/Disney+, DNS ad/tracker filtering and free-versus-paid positioning—remain around it. At minimum Ping shipped incompletely adapted Proton-derived landing-page copy.

The site also tells users to sign in even though Play promises no registration. Its email CTA has no form; the button is only a generic `mailto:` destination. Three polished testimonials have names and dates but no source link or review-platform identity.

Detailed link map and claim evidence: [website/store/legal/release/channel notes](raw/ping-vpn/2026-07-22/documents/website-store-legal-release-and-channel-notes.md).

## Store, Reviews And Recommendation Graph

Google Play showed `5M+` installs and a 10 July 2026 update on the snapshot date. Same-day rating/review counts varied across storefront widgets and locales, so the profile does not manufacture one exact canonical value. Chrome-Stats, a third-party tracker, dates creation to 17 February 2026 and estimated more than eight million cumulative downloads by mid-July, with Ping at or near the top of Russia's app chart; treat those totals/ranks as estimates, not store authority.

Recent visible negative reviews cluster around ads, two-hour connection limits, speed loss, location removal and Telegram/country outages. Developer replies attribute some failures to server bans and new-server procurement. These are user/developer claims, not independent uptime measurements, but they align with the audit's total bootstrap failure.

The Google Play recommendation rail included JumpJumpVPN, Безлимит and Thunder VPN alongside Yandex, Yandex Browser and Госуслуги. F2P's own portfolio includes Огонь VPN, Батя VPN, Elyx VPN, VPN BOX, IntVPN and Sau. Ping therefore benefits from both direct VPN adjacency and broad Russian utility-app audience affinity.

Google Play Data Safety declares collection and sharing of app activity, app information/performance and device or other IDs; data is encrypted in transit and the listing says it cannot be deleted through the declared path. This conflicts with the website's broad “no data shared” wording.

## Release Machine

The product is new and ships fast. Third-party archive dates show 1.1.13 on 10 May, 1.1.14 on 20 May, 1.1.15 on 25 May, 1.1.16 on 30 May, 1.1.17 on 11 June, 1.1.18 on 17 June and 1.1.19 archived 1 July / published by Play 10 July. That is six upgrades after 1.1.13 in roughly seven weeks, commonly 5–12 days apart.

Binary size grew from roughly 57–58 MB around 1.1.5/1.1.6 to 77–78 MB by 1.1.15–1.1.19. Changelogs remain generic stability/speed/bug-fix text and do not disclose the much more important ad, premium, limit or location-policy changes users describe.

## Telegram Growth Loop

The official channel was created 6 March 2026 and already had about 718K subscribers on 22 July. It is a promotion engine rather than a support/status archive:

- the first post promised channel-only bonuses and possible lifetime-free VPN;
- May and June winner files awarded 50 and then 100 subscriptions without ads and limits;
- a May Telegram Premium giveaway asked users to invite friends and leave a Google Play review;
- June and July campaigns explicitly farmed reactions, then immediately launched larger Telegram Premium giveaways;
- a 71.6K-response multi-select poll prioritized Android TV (56%) and Windows (50%) over iPhone (22%) and macOS (7%).

Several posts show roughly 0.5–1.45M views. The loop is blunt but effective: free app → channel → prizes/ad-free entitlement → invite/reaction/review ask → next giveaway. It generates visible momentum faster than content marketing, while leaving technical status and help content thin.

## Entity And Legal Quality

Google Play identifies **F2P, OOO** at the same Saint Petersburg address as ООО «Ф2П» (INN `7804643815`, OGRN `1197847093564`, KPP `780201001`), registered 16 April 2019. The official FNS BFO record marks it active, lists data processing/hosting as the main activity and 10,000 RUB authorized capital.

Official 2021–2025 simplified statements show only 10,000 RUB of total assets/equity and no reported revenue or profit/loss values. That supports “financially dormant through the latest filed 2025 period,” not a claim about 2026 operations after Ping's launch or about where a wider publisher group books revenue.

Ping's own Terms and Privacy identify only “the developer.” They never name ООО «Ф2П», registration details, country or a determinate jurisdiction. Terms say governing law is the law of the developer's country of residence without naming that country. The publisher is discoverable through Play/FNS, but the product deliberately or carelessly fails to put it into its own contract.

## Flow Health And Product-Design Audit

| Flow step | Health | Evidence-backed assessment |
| --- | --- | --- |
| Cold launch | `PARTIAL` | Clean branding, plain-language status and an honest ~30-second expectation, but the expected wait is already too long. |
| Remote bootstrap | `FAIL / BLOCKED_BY_BACKEND_BOOTSTRAP` | Three attempts end at the same error; there is no cached/offline shell. One backend/config failure disables the whole product. |
| Retry | `FAIL` | Repeats the same wait and error with no diagnostic, alternate route or status link. |
| Contact support | `PARTIAL` | Native form and empty-state validation work, but contrast is poor, no privacy context appears next to PII fields, and the alternate-contact region is blank. |
| Cancel | `FAIL` | Exits to launcher rather than allowing read-only settings/help or a recoverable retry state. |
| Connected dashboard | `STORE_EVIDENCE_ONLY` | Strong hierarchy and useful traffic/session feedback; current runtime could not be reached. |
| Location selection | `STORE_EVIDENCE_ONLY` | Search, fastest, favorites and city labels form a good compact selector; no live availability/load values are shown in the creative. |
| Split routing | `STATIC_AND_STORE_EVIDENCE_ONLY` | The app/URL model plus a 233-service catalog is strategically strong, but the current flow cannot expose it. |
| Ads/premium | `FAIL — TRUST` | First-party policy/channel and package evidence contradict “no ads / no subscriptions.” |
| Cross-platform download | `FAIL` | Five platform cards look actionable but have no destinations; only Android was found. |
| Legal identity | `FAIL` | The real Russian entity is in Play/FNS but absent from Ping's own contract and policy. |
| Release cadence | `PASS` | Very fast 5–12-day iteration during the May–July ramp. Changelog quality is weak. |
| Growth channel | `PASS WITH TRUST RISK` | Massive reach and high-engagement reward loops, but review asks and ad-free prizes expose the product claims they contradict. |

Visual strengths:

- restrained white/yellow/black brand with a memorable two-dot face/logo;
- big single-purpose actions and an unusually readable connected-state information hierarchy in store creatives;
- location favorites, fastest choice, traffic totals and explicit city labels make the core product feel more instrumented than a one-button VPN;
- error copy is calm and support remains one tap away.

Visual/product weaknesses:

- the all-white bootstrap/error/form sequence is sparse enough to feel unfinished, especially when remote content is missing;
- pale placeholders and helper text miss comfortable contrast;
- the blank alternate-contact block looks like a broken layout rather than a graceful degraded state;
- current public web design is polished but functionally hollow: dead download cards, unverifiable testimonials and copied plan text;
- no status or fallback surface explains whether the startup failure is regional, accountless, server-wide or temporary.

## What POKROV Should Borrow

Borrow the mechanics, not the dishonesty:

1. Ship a connected dashboard with time, upload/download/total and clear city/region state.
2. Add fastest, favorites, search and city-level selection to the location picker.
3. Build split routing around user-recognizable services plus custom domains, not only a raw app list.
4. Match a weekly/biweekly launch cadence and tie each changelog to a user problem.
5. Use Telegram for platform-demand polls, controlled rewards and launch distribution, but never condition rewards on positive ratings and never let acquisition copy lag monetization reality.
6. Make bootstrap fail open into settings, help, diagnostics and cached server state; one remote response must not brick the whole app.

Do not copy the dead cross-platform cards, Proton template residue, missing legal counterparty, generic changelogs or “no ads/no subscriptions” claim after premium/ad entitlements exist.

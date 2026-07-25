# ExpressVPN — Mobile App Competitor Profile

**Snapshot date:** 2026-07-22<br>
**Status:** `DEEP PASS COMPLETE WITH BLOCKERS` — acquisition, billing, account, package, store, release, legal and trust surfaces mapped; paid product/tunnel and desktop-Chrome visual pass blocked<br>
**Android package:** `com.expressvpn.vpn`<br>
**Installed version:** 12.71.0<br>
**Install source:** Google Play

Evidence root: [`raw/expressvpn/2026-07-22/`](raw/expressvpn/2026-07-22/)

## Audit Checkpoint

- Red Shield VPN and Android Chrome were force-stopped before launch; Android `tun0` was absent and no always-on/lockdown VPN package was configured.
- ExpressVPN cold-launched through `SplashActivity` in about 1.55 seconds and settled on `PrivacyConsentActivity`.
- First-gate memory was approximately 186.6 MB total PSS / 297.9 MB RSS with no swap.
- At closeout, ExpressVPN and Android Chrome were force-stopped; both process IDs were absent, `tun0` was absent and no always-on/lockdown VPN package was configured.
- No purchase, support submission, public post/review or destructive account operation is authorized.

## Mandatory Welcome And Privacy Consent

The first persistent surface is a Russian-localized consent screen, not the product home. It combines a friendly world illustration with two legal statements and one full-width **«Продолжить»** action:

- continuing confirms acceptance of the Terms of Service;
- ExpressVPN says it explains the data it collects and the benefit, links its Privacy Policy twice and says non-essential collection can later be disabled in profile settings.

The Terms span opened external Android Chrome at `https://expressvpn.com/ru/tos`. The first frame therefore obtains contractual acceptance before account selection, trial/price education or connection value. Evidence: [consent gate](raw/expressvpn/2026-07-22/screenshots/01-isolated-launch.png), [Terms destination](raw/expressvpn/2026-07-22/screenshots/02-terms-link.png).

## Value Carousel And Account Choice

Consent leads to a vertically scrollable, three-slide acquisition page. In landscape the screen initially shows only a large phone animation; the user must scroll to discover the copy and actions. Horizontal swipes cycle these promises:

1. **«Полная VPN-защита»** — Lightway is framed as ExpressVPN's protocol for protection against future threats.
2. **«Сверхбыстрые серверы»** — the brand name is tied to removing connection-speed limits.
3. **«200+ безопасных локаций»** — global virtual-location choice at home and abroad.

The persistent primary action is **«Купить ExpressVPN»**; a much smaller **«Есть учетная запись? Войти»** route sits below. Evidence: [first offer](raw/expressvpn/2026-07-22/screenshots/05-welcome-lower.png), [speed slide](raw/expressvpn/2026-07-22/screenshots/06-welcome-slide-2.png), [location slide](raw/expressvpn/2026-07-22/screenshots/07-welcome-slide-3.png).

## Google Play Paywall

The Buy path opens a native Google Play Billing plan selector. It briefly remained on **«Подождите немного…»** while the app created a purchase-side account, then loaded:

| Term | Snapshot price | Trial / framing |
| --- | ---: | --- |
| Annual | 3,499 RUB/year | selected by default; “SAVE -90%”; 3-day free trial |
| Monthly | 890 RUB/month | 3-day free trial |
| Weekly | 699 RUB/week | no trial label observed |

The page repeats **200+ safe locations** and shows **4.8 / 430K ratings** as social proof. Its 90% saving is not accompanied by a visible comparison basis on this screen; relative to 52 weekly payments the annual price is about 90.4% lower, which appears to be the likely anchor. This is an inference, not an ExpressVPN disclosure.

Below the plan cards, **«Подписаться»** warns that the chosen paid period is charged on the last trial day unless cancelled. No billing confirmation was opened and no trial/purchase was started. Pressing Back triggers a retention dialog: **«Вы уверены?»**, reminds the user they can cancel during trial, and offers asymmetrical choices **«Мне не нужен пробный период»** / **«Пробный период»**. Evidence: [plan selector](raw/expressvpn/2026-07-22/screenshots/10-plan-selector-loaded.png), [lower terms](raw/expressvpn/2026-07-22/screenshots/11-plan-selector-lower.png), [exit retention](raw/expressvpn/2026-07-22/screenshots/13-exit-retention-dialog.png).

## Existing-Account Entry

The sign-in form accepts email plus **password or activation code**, offers Play Store purchase restoration, password recovery, Sign in and a No account route. There are no Google/Apple/social-login buttons. The sign-in activity sets Android `FLAG_SECURE`, so screenshots are intentionally blocked; the retained UI tree records the visible controls without bypassing that protection. Evidence: [secure sign-in UI tree](raw/expressvpn/2026-07-22/ui/17-login-after-tab-close.xml).

Password recovery opens a Chrome Custom Tab branded as ExpressVPN but initially launched through tracking/redirect host `ujsrxts.com`; a non-authenticated redirect check resolved it to the official Russian reset-password page. No email was entered and no reset message was requested. Evidence: [password recovery](raw/expressvpn/2026-07-22/screenshots/15-forgot-password-route.png).

Play purchase restoration returned **«Подписка не найдена»** and offered **«НЕ ПОМНЮ ПАРОЛЬ»** / **«ОК»**, while **«Нет учетной записи»** routed directly back to the Play plan selector. No account was created and no billing confirmation was opened. Evidence: [restore result](raw/expressvpn/2026-07-22/ui/19-restore-route-second-tap.xml), [No-account route](raw/expressvpn/2026-07-22/ui/20-no-account-route.xml).

The native paid home, live location list, protocol/settings runtime and tunnel behavior remain gated by a paid or already-subscribed account and were not executed.

## Static Product Architecture

The Play artifact is a large native phone/Android-TV product with 15 DEX files, Quick Settings tile, widget, Smart/Fastest/recent/favorite locations, map, native help/Zendesk, protection history, Speed Test and an AI-labelled Connection Copilot. Its customer protocol resources expose Automatic, Lightway UDP/TCP with post-quantum support, OpenVPN UDP/TCP and WireGuard.

The paid product is expanding into a security-suite dashboard: Advanced Protection blocks ads/trackers/malicious/adult sites; ExpressAI offers private multi-model chat; Identity Defender covers identity alerts/data-protection workflows; ExpressKeys is a separate password/card manager; ExpressMailGuard and Dedicated IP are also represented. The shared Kape SDK bundles Array.com-oriented credit, financial, neighbourhood, alert and data-removal workflows, but static inclusion is not evidence of Russian availability or VPN-plan entitlement.

Power-user settings include trusted/untrusted network auto-connect, local-network and Android lockdown integration, inclusion/exclusion split tunnel, app/site shortcuts, diagnostics/privacy controls, IP map, reconnect alerts and an unusual Developer-options **GPS override** that reports the selected VPN location as the device's GPS position. Full redacted package notes: [static package notes](raw/expressvpn/2026-07-22/logs/static-package-notes.md).

## Public Store And Release Surface

The current Google Play listing showed 100M+ installs, roughly 476K ratings, a three-day trial and copy claiming 113 countries / 214 locations and up to 14 simultaneous devices depending on tier. The Apple listing showed 418K ratings, a 4.7 score and iPhone/iPad/Mac/Apple TV support. Store figures varied by locale and should be treated as dated snapshots, not fixed product constants.

The captured official Russian Play deck sells one promise per frame: one-tap protection, Protection Summary, locations, cross-device coverage, support, streaming and press/Trustpilot proof. Its “94 countries” card is stale against the current 113-country listing, exposing a useful claim-governance failure. Evidence: [ten official Play creatives](raw/expressvpn/2026-07-22/store-creatives/).

Official Android distribution spans Google Play, Samsung Store, Amazon Appstore and an authenticated direct-APK lane. The public Android log recorded 27 releases from January 6 through July 21, 2026, about one every 7.5 days. The installed 12.71.0 build was already behind 12.72.1, consistent with staged/store-source propagation; beta opt-in and gradual Pause rollout provide direct evidence of cohort rollout.

The official Chrome extension is now a standalone proxy with Smart Routing and location/WebRTC controls, but the extension marketplace also contains confusing name-copy listings. A desktop-Chrome visual walkthrough could not be completed because the local browser-control bridge was unavailable; the listing and official documentation were still mapped without opening a second desktop browser window.

## Monetization And Growth

The mobile funnel uses a three-day store trial, expensive weekly anchor, annual default, opaque “SAVE -90%” framing and an exit-retention modal. Store-billed purchases do not receive ExpressVPN's direct-web 30-day guarantee; refunds remain at Apple/Google discretion. No trial or purchase was activated.

The web business is a three-tier land-and-expand system: Basic, Advanced and Express Pro combine the VPN with ExpressKeys, ExpressMailGuard, U.S.-only Identity Defender, ExpressAI, Dedicated IP and eSIM benefits. Dynamic checkout returned campaign/geo variants, and one current sweepstakes offer excluded the normal 30-day guarantee. This needs clearer cross-channel expectation management.

The referral loop gives both sides 30 days, supports multiple share channels and allows unlimited referrals, but only after an eligible direct-web paid conversion. Play/App Store users and trial conversions are excluded. Review prompts, diagnostics tools, referral entry and TrustedServer education are integrated into product/settings surfaces rather than left only on the website.

## Legal Ownership And Privacy

The Terms and Privacy Policy identify **Express Technologies Ltd.** in the British Virgin Islands as service provider and data controller under BVI law. **Expressco Services, LLC** is the Google Play publisher, Apple seller and official desktop signing identity; its current state of formation was not verified from a primary registry in this pass. ExpressVPN joined **Kape Technologies** in 2021; current corporate records place Kape under **Unikmind Holdings**, ultimately owned by Teddy Sagi.

The no-logs claim is specific rather than absolute: the policy says it does not retain browsing/traffic/DNS data, source or assigned VPN IPs, exact connection times or session duration, while documenting account/billing records, day-level connection success, chosen location, country/ISP, aggregate daily volume, app/version, attribution identifiers and optional diagnostics. Named service providers include AppsFlyer, Firebase Crashlytics, Zendesk and TeamSupport.

## Trust And Evidence

The proof stack is unusually broad: RAM-only TrustedServer, open-source Lightway, KPMG's 2025 privacy/server-control assessment, public transparency reports and a public YesWeHack program. The latest Android-specific Cure53 report located in the official corpus is from 2022, so it does not prove every behavior of this 2026 suite build. For July–December 2025, ExpressVPN reported 155 government/civil requests, 1,382,986 DMCA requests, three warrants and zero user-related disclosures.

## What POKROV Should Copy

- Keep the first acquisition story brutally simple: one tap, one visible protection result, one promise per store frame.
- Add a real Protection Summary, IP-change proof, recent/favorite/fastest locations and contextual protocol guidance before expanding into unrelated suite products.
- Publish field-level privacy disclosure, a versioned release log, distribution fallback instructions, audit scope/dates and transparency numbers in one trust center.
- Use account-gated direct APK distribution as a resilient store fallback, with provenance checks and explicit fake-build warnings.
- Treat referral, review, troubleshooting and security tools as product loops with eligibility/status visible inside the app.
- Adopt staged rollout and rollback discipline, but keep entitlement and marketing claims generated from one source of truth.

## What POKROV Should Not Copy

- Do not hide the primary actions below oversized landscape artwork or force legal acceptance before the user sees price/account choices.
- Do not use an unexplained saving percentage, a costly weekly SKU as a silent anchor or a retention modal that visually pressures trial continuation.
- Do not let trial/refund rules diverge between stores, web campaigns and product copy, especially when a promotion removes a normal guarantee.
- Do not present an old mobile audit as timeless proof for a materially expanded current app.
- Do not turn VPN trust into an overgrown identity/password/email/AI bundle until the core connection product and support evidence are excellent.

Full dated URL inventory, store snapshots, release table, legal trail, privacy fields, trust sources, review samples and claim-drift register: [public/store/legal dossier](raw/expressvpn/2026-07-22/logs/public-surface-notes.md).

## Explicit Blockers

- `BLOCKED_BY_ACCESS`: paid native Home, authenticated location/protocol/settings surfaces and a live VPN tunnel require an existing paid subscription.
- `BLOCKED_BY_TOOLING`: desktop-Chrome visual walkthrough; the local browser-control bridge did not attach, and no second desktop browser window was opened without approval.
- `BLOCKED_BY_SOURCE`: current primary formation/status record for Expressco Services, LLC was not cleanly retrieved.
- `NOT_REQUESTED`: purchase, trial activation, review/post, support submission and destructive account actions.

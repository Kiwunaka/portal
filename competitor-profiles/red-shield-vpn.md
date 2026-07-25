# Red Shield VPN — Mobile App Competitor Profile

**Snapshot date:** 2026-07-22<br>
**Status:** `DEEP PASS COMPLETE WITH BLOCKERS` — isolated native/account/paywall/settings/location/growth/support surfaces, the unpaid connection gate, static package architecture, stores, public documentation, release lanes, legal policies and verified entities are captured; a paid tunnel and desktop-Chrome visual pass were not available<br>
**Android package:** `com.redshieldvpn.app`<br>
**Installed version:** v4.3.6<br>
**Install source:** Google Play

Evidence root: [`raw/red-shield-vpn/2026-07-22/`](raw/red-shield-vpn/2026-07-22/)

## Audit Checkpoint

- Every other VPN package was force-stopped and Android `tun0` was absent before launch.
- Cold start reached Android's notification permission after about 1.6 seconds at the activity layer. The app gave no in-context reason before the system prompt; permission was denied.
- Process memory at the first gate was about 107.0 MB total PSS / 232.5 MB RSS with no swap.
- Purchase, support submission, public posting/review and destructive account actions remain out of scope.

Evidence: [first notification gate](raw/red-shield-vpn/2026-07-22/screenshots/01-isolated-launch.png).

## Mandatory Account Entry

The first product surface is not a value proposition or guest VPN. It is a two-tab **«Войти / Создать аккаунт»** shell in a sparse orange/indigo design. Login asks for email/password and offers **«Забыли пароль?»**. Registration asks only for email and a password containing letters and digits with at least eight characters; no legal link, consent checkbox, trial promise or product explanation is visible near the account-creation action. Evidence: [login](raw/red-shield-vpn/2026-07-22/screenshots/02-login-after-deny-notifications.png), [registration](raw/red-shield-vpn/2026-07-22/screenshots/03-create-account.png).

An account was created with the explicitly authorized mailbox. Credentials and any identifier-bearing captures remain in the sensitive quarantine outside the worktree.

## Immediate Web Payment Handoff

Successful registration does not first teach the product or offer a free tunnel. It immediately opens a Chrome-powered payment surface, including Chrome's one-time **«Выполняется в Chrome»** disclosure. The visible host is `pay100.myrsv.live`, not the product's primary brand domain. No purchase or payment-method step was initiated.

The first payment step offers:

| Term | Displayed effective price | Displayed charge / promotion |
| --- | ---: | --- |
| 1 month | 890 RUB/month | 890 RUB |
| 6 months | 668 RUB/month | 4,005 RUB, shown against struck 5,340 RUB; “25%” |
| 12 months | 445 RUB/month | 5,340 RUB, shown against struck 10,680 RUB; “50%” |

The annual plan is pre-emphasized with the only saturated gradient CTA. A promo-code field sits below the cards. Every option claims up to ten devices, unlimited traffic/speed, phone and computer apps, router support and **«14 дней на возврат, если не заработает»**—a narrow failure-based refund promise rather than a general satisfaction guarantee. Evidence: [plan selection](raw/red-shield-vpn/2026-07-22/screenshots/05-registration-web-after-disclosure.png), [benefits and operator footer](raw/red-shield-vpn/2026-07-22/screenshots/06-payment-page-lower.png).

The payment footer identifies **Private Network Labs LLC**, Florida filing number `L20000139395`, with a Hamilton, New York mailing address. Sunbiz verifies the company as an active Florida LLC; its principal address changed to Syracuse, New York in April 2026 while the public/store footers retained Hamilton. The footer links product/about, tariffs, apps, cabinet, VPN explainer, FAQ, support, Terms, Privacy, Refund Policy and Telegram/Facebook/X social surfaces.

## First Authenticated Home

Closing the untouched payment tab returns to a landscape world-map home with Latvia preselected, a large horizontal connect switch, **«Отключено»** and a dominant gradient **«Продлить подписку»** CTA. The new account has no visible free entitlement or trial. Evidence: [first authenticated home](raw/red-shield-vpn/2026-07-22/screenshots/07-after-payment-close.png).

A controlled slider gesture on the unpaid account did not request Android VPN permission or start a tunnel. It reopened the same Chrome payment selector. Android `tun0` remained absent. The connect-looking control is therefore a hard subscription gate, while the more explicit renewal CTA is a second route to the same conversion surface. Evidence: [unpaid connect gate](raw/red-shield-vpn/2026-07-22/screenshots/38-unpaid-connect-attempt.png).

## Location Architecture

The selector combines search, live latency and a short tooltip—**«Чем меньше пинг, тем лучше»**—then sorts/labels locations into two behavioral groups:

- **30 recommended locations:** France, Germany, Latvia, Switzerland, Lithuania, Austria, Hungary, Italy, Netherlands, Finland, Sweden, Czechia, Hong Kong, Los Angeles, Portugal, UAE, Canada, Brazil, Singapore, Spain, Israel, Argentina, New York, Great Britain, Japan, Poland, Turkey, Cyprus, Thailand and Serbia.
- **7 “other locations”:** Russia, Georgia, Armenia, Kazakhstan, Uzbekistan, Belarus and Ukraine. The app explicitly recommends using these only when the user needs that exact country.

The two US options are cities; the rest are countries. This gives the app 37 visible choices without pretending that every endpoint is equivalent for ordinary use. Evidence: [selector top](raw/red-shield-vpn/2026-07-22/screenshots/08-location-selector.png), [selector continuation](raw/red-shield-vpn/2026-07-22/screenshots/09-location-selector-scroll-07.png).

## Native Settings And Power-User Layer

The settings surface is materially deeper than the sparse home screen:

- **Protocols:** Auto, **RedLink TLS Plus** (described as new TLS/web-traffic masking) and **RedLink Random** (randomized traffic masking). Evidence: [protocol dialog](raw/red-shield-vpn/2026-07-22/screenshots/14-protocol-dialog.png).
- **Split tunnelling:** All apps; an inclusion-only **Some** mode; **Exclusion**; and user-created **Presets** intended for fast context/country switching. The installed-app picker can expose system apps. No built-in presets were present, and the audit restored the default All-apps mode. Evidence: [mode model](raw/red-shield-vpn/2026-07-22/screenshots/16-split-tunneling-modes.png), [presets](raw/red-shield-vpn/2026-07-22/screenshots/17-split-tunneling-presets.png), [app picker](raw/red-shield-vpn/2026-07-22/screenshots/18-split-tunneling-some.png).
- **Local network:** an off-by-default switch whose positive action is worded as “do not block access to the local network.”
- **Content restriction:** independent Ads, Trackers and Malware blocklist switches, all off by default. Evidence: [content controls](raw/red-shield-vpn/2026-07-22/screenshots/19-content-filter-options.png).
- **Wi-Fi VPN sharing:** the phone can expose proxy-style connection settings so computer apps on the same Wi-Fi/hotspot can use the phone's VPN. The help flow instructs users to select “RedLink TLS,” which does not exactly match the visible “RedLink TLS Plus” protocol label. Evidence: [sharing instructions](raw/red-shield-vpn/2026-07-22/screenshots/20-wifi-sharing-settings.png).
- **Background survival:** “Disable energy saving” hands off to Android's unrestricted-background request; the request was denied during the audit. Evidence: [app explanation](raw/red-shield-vpn/2026-07-22/screenshots/21-energy-saving-help.png), [system handoff](raw/red-shield-vpn/2026-07-22/screenshots/22-energy-saving-system-handoff.png).
- **Presentation:** Russian/English only and System/Light/Dark theme choices. Evidence: [languages](raw/red-shield-vpn/2026-07-22/screenshots/23-language-list.png), [themes](raw/red-shield-vpn/2026-07-22/screenshots/24-theme-options.png).

The account-deletion entry warns that deletion is complete and a subscription cannot be recovered. It was not opened beyond the warning and no destructive action was taken.

## Account, Devices And Conversion Loops

The hamburger menu exposes Home, Subscription, Invite a friend, Gift VPN, Settings, Account, Devices, Promo codes, FAQ, Support, About and Logout. Identifier-bearing captures were quarantined outside the worktree.

Account and Devices hand off into the Chrome cabinet. Without opening configuration secrets, the cabinet revealed the breadth of the product:

- profile and password changes plus GDPR/account deletion;
- auto-renewal, saved cards and payment history;
- device/configuration management for up to ten devices, with a global disconnect action;
- platform apps and manual OpenVPN/PPTP credentials;
- a Telegram-bot account link positioned both as service management and as an alternate app-delivery channel if the cabinet is unavailable;
- gift, referral and promo-code routes.

The referral mechanic grants the inviter one free month after each referred user's first payment. The gift flow sells the same 1/6/12-month plans and produces a coupon for another user. No gift/payment was purchased and no referral was shared. The native promo surface is a minimal code field plus Apply action. Evidence: [promo entry](raw/red-shield-vpn/2026-07-22/screenshots/25-promo-codes.png).

## FAQ, Support And Trust Copy

FAQ is a Chrome route on `new2.redshieldvpn.info`. The captured index contains 38 visible questions numbered 1–34, then 36–39. Its scope is unusually broad: Android/TV/Windows/Apple/macOS, extensions, manual WireGuard/OpenVPN/AmneziaWG/VLESS setup, Russian and crypto payments, missing subscriptions, disconnects, split tunnelling, streaming/IP/location behavior, speed/battery, RedLink variants, torrents, retained data/crime response, routers, more than ten devices, renewal/card removal and ping visibility. The answers, strict support gate and troubleshooting model are captured in the [public-surface notes](raw/red-shield-vpn/2026-07-22/logs/public-surface-notes.md). Evidence: [FAQ index](raw/red-shield-vpn/2026-07-22/screenshots/29-faq-route.png).

Native Support first intercepts with an FAQ recommendation, then opens a one-message composer. The app asks the user not to duplicate a case through email and chat and sets an expectation of up to a day, sometimes longer. No message was sent. Its diagnostic-log flow says the log contains no personal data and offers Copy/Send; neither action was used. Raw diagnostics remain quarantined because they included endpoint/configuration detail. Evidence: [FAQ interception](raw/red-shield-vpn/2026-07-22/screenshots/30-support-route.png), [support composer](raw/red-shield-vpn/2026-07-22/screenshots/31-support-composer.png).

The About page uses adversarial trust positioning: bypass blocks, protect traffic from local intelligence services/ISPs/third parties, and distrust free VPNs that allegedly analyze or sell traffic. It argues that direct subscription funding pays for infrastructure. It links other platforms, contact, Terms, Privacy and Refund Policy and reports v4.3.6 (1843). Evidence: [About](raw/red-shield-vpn/2026-07-22/screenshots/33-about.png).

Observed legal/help destinations:

- Terms: `https://new2.redshieldvpn.info/tos`
- Privacy: `https://new2.redshieldvpn.info/pp`
- Refund: `https://new2.redshieldvpn.info/ru/help/description/rp`
- Platforms/home: `https://new2.redshieldvpn.info/`

## Product Lessons For POKROV

- Keep a one-action home, but earn conversion before making a connect control behave as a disguised paywall. Red Shield's immediate gate is commercially blunt and leaves no proof of tunnel quality.
- Copy the **depth behind simplicity**: protocol explanations, split-tunnel modes/presets, per-category blocking, latency guidance, local-network access and cross-device sharing are concrete reasons to pay.
- Separate ordinary and special-purpose locations instead of presenting a flat country count. Red Shield's “other locations” warning is a useful expectation-setting pattern.
- A cabinet, native app and Telegram fallback form one resilient distribution/support system. The useful idea is channel redundancy, not copying account credentials into chat surfaces.
- Referral reward after first payment and gift coupons tie acquisition to realized revenue. Both are more defensible than rewarding raw installs.
- Tighten trust details if adopting similar mechanics: explain notification need before the prompt, show legal/consent context at registration, keep protocol names consistent, and put payment on an obviously first-party domain.
- Copy the redundant distribution model—Play, signed direct APK, mirrors, cabinet, Telegram, extensions and manual configs—but publish verified application IDs, hashes and a clear official-domain map so blocked-store impersonators are obvious.
- Do not copy the legal/copy gap: “unlimited” is capped at 1 TB/month, the hero's 14-day refund promise has many cumulative exclusions, and the blanket “do not collect/analyze” wording is broader than the stores, privacy policy and bundled Firebase surface support.

## Static Android / Release Findings

The installed Google Play artifact is a native Compose release with a shared phone/TV codebase, Quick Settings tile, widget, QR pairing and server-driven configuration. It bundles a 52.5 MB sing-box-derived `libbox.so`; lower-level code supports several modern tunnel families while the customer UI hides them behind three RedLink choices. The app contains Firebase analytics/crash/push infrastructure but no Play Billing or ad-mediation SDK, consistent with its external web checkout.

Most notably, Red Shield maintains two distribution lanes: the installed `store` flavor uses Google Play in-app updates, while a separate direct-APK flavor can download stable or beta packages and validates an allowed signing fingerprint before handing the APK to Android's installer. Full redacted findings: [static package notes](raw/red-shield-vpn/2026-07-22/logs/static-package-notes.md).

## Stores, Release Cadence And Recommendations

Google Play showed 500K+ installs, an approximately 4.7 rating / 7.55K reviews in the observed locale and a July 6, 2026 update. Its release note makes the build mandatory by August 10 because older versions will stop working and cites availability changes in some regions. The direct APK was also dated July 6. Apple showed v4.1.2 from June 29, mandatory by July 10, after six preceding 2026 releases. Chrome/Edge was v1.0.367 from June 17 with 40K users; Firefox was v300.0.42 from May 8 with about 2.5K users.

This is an operational anti-blocking release system, not a single store pipeline: Google Play in-app update, signed direct stable/beta capability, Apple, independently released extensions, Windows/macOS downloads, manual configurations, multiple marketing mirrors and Telegram recovery. The public news feed stops in December 2025, so installed artifacts and store metadata—not the marketing news page—are the current release authority.

Recommendation shelves are volatile but commercially useful. The observed Google Play shelf included JumpJumpVPN, Proton, PandaVPN, Octohide, ExpressVPN and Intra. Apple's shelf included PlatoVPN, VPN Satoshi, ForceField, AmneziaVPN, Grizzly, VPN Matreshka, VPN 111, BlancVPN and Paper VPN among others. These are algorithmic adjacencies, not partnerships.

## Public Funnel And Distribution Mesh

The canonical marketing site, public mirrors, cabinet, checkout, downloads and Apple-recovery guide use different hosts. `.com`, `.me`, `.xyz` and `new2.redshieldvpn.info` all served the product; the app used the `.info` mirror, Telegram promotes `.xyz`, the cabinet is `my.redshieldvpn.com`, direct APKs are on `downloads.redshieldvpn.com`, and Android checkout used `pay100.myrsv.live`. The current sitemap has 194 pages split exactly between English and Russian, including 41 news posts and a deep app/router/Linux/help library per language.

The official Apple recovery guide tells Russian users to switch their Apple ID region to the United States and, if necessary, populate the account with generated foreign identity/address data; support promises an unspecified alternative method by email. The audit did not follow those steps. A distinct similarly named Russian App Store app appeared under another provider and ID in June 2026, creating a concrete impersonation/confusion risk; no claim is made about who operates it or whether it is malicious.

## Legal Entity And Lineage

- Current operator: **PRIVATE NETWORK LABS LLC**, Florida document `L20000139395`, filed May 22, 2020 and active in the current Sunbiz record. Authorized member: Vladislav Zdolnikov.
- Historical lineage: Red Shield's own December 2019 post calls the product the continuation of TgVPN. The ECHR record identifies TgVPN's operator as Scottish **PRIVATE NETWORKS LP**, `SL030265`, and names Zdolnikov as a person with control/representative.
- Companies House is internally inconsistent: the overview still says Active, while filing history records an August 9, 2023 LP6 stating that the partnership has been dissolved. The dissolution filing is the stronger evidence. The Scottish LP is not the current Florida LLC.

## Policy And Trust Gaps

- Marketing says unlimited bandwidth and no speed limit; Terms cap an account at **1 TB/month** and do not guarantee bandwidth.
- “14 days for refund if it doesn't work” expands into cumulative conditions: first bank-card payment only, never connected, failure attributable solely to Red Shield's own client, 24-hour compliance with support requests and up to 30 days for attempted remediation. Refunds remain discretionary and fees are deducted.
- The privacy policy describes account/payment/email/cookie/affiliate/diagnostic processing and transient IP analysis; Play and Apple also disclose personal, purchase, usage and diagnostic data. This does not support a literal collect-nothing reading of the store marketing copy.
- The privacy policy bars under-18 use while the storefronts show PEGI 3 / Everyone / 4+.
- Terms contain repealed EU-directive language, an unclear USA/Panama/connected-country jurisdiction clause and copied “Antivirus” boilerplate.
- The warrant-canary page claims zero bytes transferred for TgVPN, Red Shield and related companies, but provides no date, signature or independent verification. No current independent no-log/infrastructure audit was found.
- The public bug bounty offers $100–$5,000+ and covers apps, extensions, sites and infrastructure, but excludes several common web findings, old versions, protocol libraries and root/physical/social-engineering paths.

Full URLs, exact policy conditions, data-safety categories, store snapshots, Apple workaround, entity sources, release lanes and contradiction matrix: [public-surface notes](raw/red-shield-vpn/2026-07-22/logs/public-surface-notes.md).

## Blockers And Boundaries

- **BLOCKED_BY_ACCESS:** no paid entitlement, so real RedLink tunnel establishment, live latency/speed, streaming, leak behavior and paid-location reliability were not tested.
- **BLOCKED_BY_TOOLING:** the requested desktop-Chrome visual pass was unavailable; Android app/web handoffs and public page text were captured instead. No new desktop browser window was opened without owner confirmation.
- **NOT_REQUESTED / NOT_PERFORMED:** no purchase, refund request, support message, review, referral share, generated Apple identity, configuration export, account deletion, vulnerability probing or production mutation.
- **PASS:** Red Shield was kept isolated from every other VPN package, the unpaid connection attempt produced no VPN permission/tunnel, and `tun0` remained absent.

# ВПН / Vanya VPN — Mobile App Competitor Profile

**Snapshot date:** 2026-07-22<br>
**Status:** `DEEP PASS COMPLETE WITH BLOCKERS` — native no-key UX, every safe public destination, store/release/distribution, legal entities, growth surfaces and redacted static architecture captured; paid-key connection and fresh Arizona registry status remain explicitly blocked<br>
**Android package:** `com.vanyavpn.android.client`<br>
**Installed version:** 1.20.6<br>
**Install source:** Google Play

Evidence root: [`raw/vanya-vpn/2026-07-22/`](raw/vanya-vpn/2026-07-22/)

## First-Run Privacy Disclosure

The isolated cold launch opens a full-screen black privacy notice with a large yellow **В** mark and the claim **«Дядя Ваня не собирает ваши личные данные»**. The smaller text qualifies that errors or failures may send anonymous server-usage data plus unspecified technical information with a review/report. Two actions are visible: **Подробнее** and **Понятно**.

The disclosure is materially better timed than Батя's connect flow because it appears before use, but “does not collect personal data” and “sends technical information” need a precise field list and destination to be meaningful.

Evidence: [isolated cold-launch disclosure](raw/vanya-vpn/2026-07-22/screenshots/02-fresh-launch.png).

### “Подробнее” destination and exact scope

**Подробнее** leaves the app through an Android browsable intent and opens the official page `https://vanyavpn.app/app-data-collection` in Chrome. The apparent return to the LDPlayer launcher during the first attempt was Chrome's cold-start transition, not a Vanya crash. No tunnel interface was created by opening the disclosure.

The linked policy is much more specific than the first screen:

- it says Vanya does not collect visited sites or communication counterpart/content;
- automatically received data includes the VPN **server's** IP address through Quay.io update checks;
- crash/manual-feedback telemetry can include country, region, timestamp, up to 100 preceding in-app events, compiled exception messages, OS and version, phone model, app start time, browser, architecture, app version and build;
- those diagnostics are sent over HTTPS to Sentry; beta Android builds may additionally use Firebase;
- after registration, each server locally aggregates hourly byte counts per access key, credential-origin countries and feature flags; the wording says these metrics are not sent to the Vanya team by default, but ambiguously adds that “if one day” they are, country-level aggregation occurs after 60 days;
- feedback can include an optional email address.

This creates two copy problems worth borrowing *against*: the first screen calls the data “anonymous” without naming country/region, device model, the preceding-event trail, Sentry or Firebase; and the policy mixes definite current behavior with a hypothetical future transmission clause instead of stating a stable retention/consent rule.

Source: [official app data-collection policy](https://vanyavpn.app/app-data-collection) (captured 2026-07-22). Browser screenshots were kept out of the durable evidence set because the shared Chrome instance exposed unrelated competitor-audit tabs.

## Main Screen After Acknowledgement

After **Понятно**, the app opens a deliberately sparse black dashboard:

- top-left product block: red/yellow `В` icon, **Дядя Ваня**, **ВЕРСИЯ 1.20.6**;
- top-right red `+` affordance;
- central oversized brand tile with small animated country flags moving around it;
- three large actions: **🔗 Добавить ключ Дяди Вани**, **💳 Купить ключ на нашем сайте**, **💬 Поддержка**;
- bottom navigation: locked **VPN** and **О приложении**.

There is no conventional “connect” control before an access key is supplied. The page turns setup into a three-way choice—bring a key, buy one, or ask support—which is unusually honest about the empty state and much clearer than a disabled unexplained power button. The huge unused middle area makes the branding memorable, but it also pushes all useful actions into the bottom third and leaves the product looking unfinished on a tall phone.

Evidence: [empty-state dashboard](raw/vanya-vpn/2026-07-22/screenshots/04-after-privacy-accept.png). No `tun0` interface existed after acknowledgement.

## Access-Key Import

Both the dashboard's primary acquisition model and the empty-state wording revolve around an `ssconf://` access key. **Добавить ключ Дяди Вани** opens a full-height overlay with:

- a large tappable QR scanner target;
- instruction **«Нажмите, чтобы отсканировать QR-код, или вставьте ssconf-ключ в поле снизу»**;
- heading **Добавление ключа доступа**;
- a manually editable `ssconf://` field;
- **Вставить из буфера обмена**;
- a close `×` that returns to the dashboard.

This is a self-service configuration import, not account-based provisioning. It supports both camera and clipboard paths and exposes the expected key scheme before the user pastes anything. The full-screen modal is visually clear, although the key field and next action sit below a very large scanner illustration and are partly below the fold on a 900×1600 viewport.

Evidence: [access-key import overlay](raw/vanya-vpn/2026-07-22/screenshots/05-add-key.png). No real key was entered, pasted, recorded, or tested.

Tapping the QR target requests Android's camera permission only at the moment it is needed, with the standard choices **При использовании приложения**, **Только в этот раз**, and **Запретить**. The package/system-facing app label is the generic **ВПН**, not **Дядя Ваня**, so the permission prompt reads less trustworthy than the branded in-app screen. The audit denied access and did not activate the camera. Evidence: [just-in-time camera permission](raw/vanya-vpn/2026-07-22/screenshots/06-qr-permission.png).

## Purchase Destination, Pricing, and Retention

**Купить ключ на нашем сайте** opens the public root site, not a native paywall. The site gives Vanya a much larger commercial surface than the app itself: 174 advertised locations, ≤10 clients/server, unlimited devices/family sharing, routers, first-party clients across platforms, OTP cabinet, a Telegram cabinet bot, referrals, a cash affiliate program, advanced configurations and extensive support copy.

Current Russian price grid: 5,700 ₽ for 2 years + 6 months (190 ₽/month), 4,200 ₽ for 1 year + 3 months (280 ₽/month), 2,800 ₽ for 6 + 2 months (350 ₽/month), or 500 ₽ monthly. The one-day **Ванечка** trial costs 10 ₽ and automatically becomes 500 ₽/month unless cancelled. The LDPlayer browser received euro hero copy (€1.9/month, €0.5 test), so currency varies by environment without an obvious explainer.

The site uses multiple conversion levers:

- bonus-month bundles and percentage savings;
- a stale “only until 15 July” deadline still live on 22 July;
- a three-day post-purchase upgrade window;
- friend-get-friend one-month rewards;
- up to $20 affiliate payout and USDT/bank-card cashout;
- cancellation intercepts at 50% and then 66% off before card unlinking.

The breadth is worth learning from; the trial-to-paid transition and stacked cancellation obstacles are not. Selected current Play reviews explicitly describe the 500 ₽ charge after the 10 ₽ test as unexpected even though the site discloses it beneath the CTA—evidence that legal visibility did not create user comprehension.

Detailed durable notes: [website, cabinet, pricing, ecosystem and legal audit](raw/vanya-vpn/2026-07-22/documents/website-and-legal-notes.md).

## Ownership and Trust Chain

The site names UK **CODE ASSET LTD**, company 16508808. Companies House shows it active, incorporated 10 June 2025; Ermatjon Razzakov is the current director and Oleg Solovyov is the active 75%+ controlling person. Google Play instead presents publisher **KONDAKOV / VLADIMIR KONDAKOV** in Russia. The app, store publisher and contracting/data-controller roles are therefore split and not clearly reconciled for a customer.

The site's broad privacy policy contains a deliberately absurd deletion promise involving paper, a bucket, YouTube proof and 100,000 ₽ compensation. It is memorable “наглость”, but it destroys legal credibility rather than building brand personality. The offer also caps normal traffic at 500 GB per 30 days, permits a support-requested increase to 1 TB, and reserves early trial conversion for repeated trial use.

Official sources: [Vanya website](https://vanyavpn.app/), [Companies House overview](https://find-and-update.company-information.service.gov.uk/company/16508808), [officers](https://find-and-update.company-information.service.gov.uk/company/16508808/officers), [persons with significant control](https://find-and-update.company-information.service.gov.uk/company/16508808/persons-with-significant-control).

## In-App Support Destination

The native **Поддержка** button does **not** go to the public Telegram support named on the website. It opens an external `vova.loan` redirect and lands on a hosted Chatwoot widget. The landing copy says the assistant runs on **GPT-5**, can help with service questions, shows **Мы в сети**, promises a response within a few minutes, and offers **Начать диалог**.

This is a strong self-service pattern: support is one tap from the empty state, branded, available before purchase and framed as fast AI help. The implementation is sloppy on privacy: the final Chatwoot URL visibly carries a website token and conversation token in Chrome's address bar/history. Those values and the generated conversation identifier were quarantined and are intentionally absent from the repository. The audit did not press **Начать диалог** and sent no external message.

## About, Mirrors, and Legal Destinations

The **О приложении** tab is a practical continuity hub rather than a generic version sheet. It exposes:

- hosted support chat, Telegram `@vanyasupport`, and `support@vanyavpn.app`;
- the current working mirror, observed as `https://vanya-vpn.cz`;
- `https://bit.ly/vanyavpn`, described as a magic link that should open even when the main domain is unavailable in the user's region;
- the web cabinet;
- Privacy, Data collection, Licences, Terms of use and Technical information.

Evidence: [full About screen](raw/vanya-vpn/2026-07-22/screenshots/07-about.png).

Static route inspection explains a confusing live behavior: the legal links are built from a remotely selected `actualDomain`, so after the magic-link bootstrap they can intentionally open through `bit.ly/vanyavpn` and then preserve the legal path. This is censorship-resilient routing, not simply a miswired privacy button. The public app route contains a much larger mirror pool and can remotely change the real/magic domain, Telegram contact, connection-test policy, update version and update URL.

The resilience implementation is bold and operationally useful, but it conflicts with the website footer's disclaimer that the resource is not intended to bypass blocking. It also puts legal-document availability behind dynamic redirect infrastructure; each final document should still have a stable canonical URL and version identifier.

## Hidden Depth: Repair, Routing, and Diagnostics

The current package contains a much smarter connected-state product than the empty screen suggests. The strongest mechanism is **Найти рабочий сервер**: a staged repair flow retests the current path, regenerates an IP and can escalate to multihop, showing progress and warning that recovery may take two minutes. User-facing strings also cover automatic reconnect without traffic bypass, automatic multihop or routing through Russia, fastest-location selection, cross-device location changes, split tunneling by apps/IP/subnet/domain, key/server regeneration, TV-code login, Quick Settings, battery optimization and a detailed troubleshooting matrix.

The product lesson is not merely “add more settings”. Vanya packages failure recovery as one intelligible action and moves technical decisions into an escalating automated sequence. POKROV should copy that user model while keeping routing claims and privacy disclosures explicit.

The About page's **Техническая информация** modal can reveal device/model/OS, memory/CPU, app/mirror context, an identifier prefix and native/web logs with copy/refresh/clear actions. It attempts log redaction, but the durable audit deliberately did not open or screenshot it because runtime identifiers could be exposed.

Detailed package evidence: [static package and release notes](raw/vanya-vpn/2026-07-22/logs/static-package-notes.md).

## Privacy and Contract Contradictions

Static runtime paths show automatic first-party requests carrying device-scoped and, once configured, key-scoped context for bootstrap/notifications, reconnect policy and connect/disconnect statistics. The connection event includes timestamps/duration, app/platform/OS context, route decision and traffic-byte totals. No real key or personal identifier existed in this pass, but the behavior materially contradicts the blanket first-screen claim of anonymous technical data and the policy's suggestion that per-key metrics are not normally sent.

The installed environment has a blank Sentry DSN despite bundled Sentry code and a policy that names Sentry. That is useful configuration evidence, not proof that no diagnostic destination can be introduced remotely.

The Terms page is also an unreconciled upstream artifact: it repeatedly calls the product **Outline**, describes a server managed by the user, says Outline is not a consumer product and frames the agreement around Jigsaw. That does not describe Vanya's paid consumer subscription. Combined with the joke deletion clause in the broader privacy policy, the legal surface reads as copied infrastructure rather than an enforceable product-specific contract.

## Distribution and Release Machine

Vanya operates parallel Play, direct APK, Android TV APK, App Store/TestFlight, Mac App Store/DMG, Windows and legacy Linux/Windows 7 channels. The direct Android APK is the same signed 1.20.6 core as the installed Play package. Remote metadata can show an in-app update banner and change its destination, giving the operator a release path independent of store review.

Google Play showed 1M+ installs and 40.6K reviews. On 22 July its public page reported an update on 19 July 2026 and a 4.5 overall / 4.6 phone rating; other regional/device views exposed ratings down to 3.3, so the exact score is storefront-dependent. The iOS history shows a rapid relaunch in May–June 2026 after roughly two and a half quiet years; macOS also jumped to 1.20.0 in June 2026 after 2023 releases. Generic “bug fixes” release notes make cadence visible but provide little user trust or feature discoverability.

The official site links a Telegram cabinet/purchase bot with roughly 113K monthly users and a separate support contact, but no canonical release/news channel. Search is polluted by “official” lookalike channels that promote unrelated VPNs and claim unobserved features. Store recommendations place Vanya beside JumpJumpVPN, Lumos, Thunder, VPNHouse, Windscribe and—on Apple—TipTop plus several small VPN brands. These are algorithmic acquisition neighbors, not customer endorsements.

The official iOS install page goes much further than ordinary fallback distribution. It recommends changing App Store country, offers a public TestFlight, and offers time-limited credentials for a shared foreign App Store account—claiming password rotation, phone unlinking and automatic termination of mistaken iCloud sessions. No credentials were requested. The mechanism is clever distribution growth but an unacceptable platform/account-security risk; copy TestFlight/mirror continuity, not shared Apple accounts or fabricated profile data.

## Expanded Trust Chain

The current Windows installer has a valid Authenticode signature from **KONDAKOV&GORIN LLC** with an Arizona/US identity, while the site names UK **CODE ASSET LTD**, Google Play names Vladimir Kondakov in Russia, and Apple names **KONDAKOV OOO**. The installer was never run. The accessible Arizona Corporation Commission record identifies entity 23405407 as an active domestic LLC formed in 2022 with Vladimir Kondakov and Ilia Gorin as members, but the record's displayed search timestamp is November 2025 and the replacement live search could not be refreshed. Apple exposes no registration number and the exact Russian store-seller entity could not be matched in the current FNS search.

A lookalike search-result site falsely pairs **ООО КОНДАКОВ** with an OGRN that the official FNS service assigns to **ООО «ТВЛ»**. It is not linked from Vanya and is treated as unaffiliated/unsafe. Overall, Vanya should publish a single responsibility map covering seller, publisher, signer, controller and support operator.

## Current Flow Health

| Flow | Health | Evidence / blocker |
|---|---|---|
| First-run disclosure → app | **PASS** | Disclosure and detailed external policy open; disclosure wording conflicts with static telemetry |
| Empty state → add key | **PASS** | Manual `ssconf://`, clipboard and QR routes visible; camera permission is just in time |
| Empty state → purchase | **PASS TO PUBLIC DESTINATION** | Root site opens; checkout/payment/delivery not executed |
| Empty state → support | **PASS WITH PRIVACY ISSUE** | Hosted GPT-5 Chatwoot opens; URL credential material quarantined; no message sent |
| About → mirror/cabinet/contact | **PASS TO PUBLIC DESTINATIONS** | Current mirror, magic link, cabinet, Telegram and email mapped |
| About → legal documents | **PASS WITH CONTRACT DEFECTS** | Dynamic mirror paths work; Outline terms do not describe the paid product |
| Key → connect/disconnect | **BLOCKED_BY_ACCESS** | Requires a real access key; none requested, purchased or imported |
| Smart repair / locations / split tunnel | **STATICALLY CONFIRMED, MANUAL BLOCKED** | Present in current bundle; connected-state execution requires a key |
| iOS fallback delivery | **PASS TO PUBLIC DESTINATIONS** | App Store/TestFlight inspected; temporary credentials intentionally not requested |

Final teardown: Vanya, Chrome and Play were force-stopped; their processes were absent and `tun0` was absent before the next competitor. No purchase, registration, support message, Telegram bot start, temporary Apple credential request or connection was performed.

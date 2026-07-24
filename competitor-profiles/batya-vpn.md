# Батя VPN — Mobile App Competitor Profile

**Snapshot date:** 2026-07-22<br>
**Status:** `DEEP_PASS_COMPLETE_WITH_BLOCKERS` — Android UX, store, public instructions/channel, legal and redacted static passes complete<br>
**Android package:** `ms.f2p.batyavpn`<br>
**Installed version:** 1.3.9<br>
**Install source:** Google Play

Evidence root: [`raw/batya-vpn/2026-07-22/`](raw/batya-vpn/2026-07-22/)

## At A Glance

| Field | Observed value |
| --- | --- |
| Product | Батя VPN |
| Android package | `ms.f2p.batyavpn` |
| Installed version | 1.3.9 |
| Install source | Google Play |
| Launch state | Existing anonymous/local state; no clean-install onboarding appeared |
| Audit isolation | No other competitor process and no `tun0` interface existed before launch |

## Fresh Home Surface

The accepted portrait home is built around a large 3D **«батя»** mascot in sunglasses, orange workwear, a VPN shield patch, wrench and coffee mug. It is far more character-led than Огонь: most of the first viewport is brand asset, while controls sit below it.

Visible structure:

- instruction card: **«Чтобы активировать VPN, нажми на кнопку ниже»** with a crown/upgrade control;
- oversized pill-shaped connect control with a white left handle; its lack of a text label makes the interaction visually expressive but less explicit;
- troubleshooting nudge: **«Не работает VPN? Нажми на флаг и Смени сервер 👇»**;
- current choice **«Оптимум»**, observed latency **37 мс**, refresh control and chevron;
- large **«Управление подпиской»** and **«Наш ТГ канал с бонусами»** buttons;
- bottom tabs **Настройки / Главная / Подписка**.

Evidence: [fresh isolated launch](raw/batya-vpn/2026-07-22/screenshots/02-fresh-launch.png).

The interrupted-session `01-launch` artifact is retained for provenance but is not used as accepted evidence.

## Settings Surface

The Settings tab exposes a generated device/account ID, the current **Бесплатный** tariff, a dark-mode switch, **Настроить VPN**, **Сканировать QR для Android TV**, **Поддержка 24/7**, **Конфиденциальность и правила**, and version 1.3.9. This immediately establishes Android TV pairing and device-bound identity as first-class product concepts.

Both settings screenshots/UI trees were quarantined outside the worktree because the generated ID was visible; the value is intentionally not reproduced or retained in audit artifacts. No setting was changed.

**«Сканировать QR для Android TV»** opens an in-app camera scanner whose helper text says to scan a QR code from the television to bind the subscription. Android requests camera access only when this feature is opened. The permission was not granted; the temporary denial state was cleared afterward so the app returned to its original unasked permission state.

Evidence: [Android TV camera prompt](raw/batya-vpn/2026-07-22/screenshots/17-android-tv-qr.png).

Dark mode restyles the complete native shell—including the mascot screen, server card, CTAs and bottom navigation—rather than merely changing background color. The mascot remains readable, but the giant unlabeled switch remains the weakest affordance. Light mode was restored after capture.

Evidence: [dark-mode home](raw/batya-vpn/2026-07-22/screenshots/19-dark-mode-home.png).

### «Настроить VPN» destination

This row does **not** open Android network settings. It opens a full embedded **Личный кабинет** inside the app. The cabinet exposes:

- remaining access time and renewal;
- a news modal;
- **Запустить VPN**;
- optional email binding for recovery;
- a copyable VPN access key plus installation guide;
- support, promo codes and referral system;
- **Мои устройства**;
- payment history, currently empty;
- bottom sections **Доступ / Главная / Настройки**.

The referral copy promises **30 free days to both people** when the invited friend makes their first payment; a friend's code can be entered only before the user's first payment. This is a materially stronger, cleaner growth loop than Огонь's policy-risky paid review campaign.

The opened referral modal showed zero invited, zero paid and zero bonus days in the current state. It provided only an input for a friend's code; no outbound invite code/share control was visible, possibly because the account has not made a first payment. Nothing was entered.

Evidence: [promo-code modal](raw/batya-vpn/2026-07-22/screenshots/12-cabinet-promo-codes.png), [referral modal](raw/batya-vpn/2026-07-22/screenshots/13-cabinet-referral.png).

The Devices page showed one current active Android device, app 1.3.9 and Android 14, but no visible revoke/rename control. Its screenshot was quarantined because it displayed the generated device ID.

The personal-cabinet home and its UI trees were quarantined because they contain live connection material. No access key, generated identifier or destination carrying it is reproduced here. The retained news-modal screenshot is safe because the cabinet background is visually blurred.

Evidence: [news modal](raw/batya-vpn/2026-07-22/screenshots/10-cabinet-news.png).

The only visible news item expands to **«Батя VPN восстановлен!»**. It says users received **seven extra days**, Android should work again (possibly after a reboot), and iPhone users must copy an updated key from the cabinet and use **«Вставить/обновить ключ»**. This confirms a recent service restoration, manual key rotation on iOS and compensation as a retention/recovery tactic. The item exposes no date in the captured modal.

Evidence: [expanded recovery notice](raw/batya-vpn/2026-07-22/screenshots/11-cabinet-news-detail.png).

## Telegram Channel Destination

The home button **«Наш ТГ канал с бонусами»** opens a Telegram invite-link landing rather than a stable public username. The landing identified **«Батя VPN — Новости»**, showed 186,518 subscribers at capture time, claimed support across computer/phone/TV, and linked `@MyBatyaOnline_bot` for connection plus `@batyavpnhelp_bot` for support. The raw invite token is intentionally not retained.

The browser capture was quarantined because unrelated existing tab titles were visible. The channel was not joined and neither bot was started.

## Support Surface

**«Поддержка 24/7»** opens the embedded personal cabinet and an online-chat widget rather than immediately leaving for Telegram. The widget says operators are online and asks for name, email and a free-text question before enabling Send. It gives the product a credible first-party support surface, but mandatory identity fields add friction and the linked offer still allows up to two working days for a response.

No name, email or message was entered and nothing was sent. The screenshot/UI tree was not retained because the live VPN access key remained visible behind the widget.

## Subscription And Pricing

The Subscription tab says **«Ваша подписка Батя VPN закончится через 4 дня»** while Settings labels the tariff **«Бесплатный»**. Combined with the linked offer's five-day free period, this strongly suggests the existing anonymous state is inside an automatically available trial, but the activation event was not observed and is not asserted as fact.

Benefits are presented as installation on any devices, no annoying ads, instant connection and unlimited traffic. The screen shows:

| Plan | Current price | Reference price / badge |
| --- | ---: | --- |
| 1 month | 249 RUB | none |
| 3 months | 599 RUB | 747 RUB, `-20%` |
| 1 year | 1,599 RUB | 3,029.50 RUB, `-47%` |
| Lifetime | 3,490 RUB | `ТОП` |

The header separately says **«Скидка 20%»** even though the annual card says 47%. No plan was tapped because that can create a payment order or open a merchant checkout.

Evidence: [subscription screen](raw/batya-vpn/2026-07-22/screenshots/05-subscription.png).

## Server Packaging

The entire selector fits on one portrait screen and contains eleven choices:

1. **Оптимум** — automatic choice, selected by default;
2. **Белые списки LTE** — Russian-flag special route;
3. **Нейросети 🤖** — task-specific route rather than a country;
4. Poland;
5. **Ультра (Белые списки LTE)** — second special route;
6. Austria;
7. USA;
8. Spain;
9. France;
10. Singapore;
11. Hong Kong.

The UI labels the automatic option plus ten other rows (eleven visible choices total). Country/special-route rows use signal bars. **«Показать пинг»** ran a transient reachability check and changed every visible row to green bars, but did not expose per-server milliseconds; the Home screen separately showed 37 ms for Optimum. No alternate server was selected.

The valuable pattern is job-based routing embedded beside countries: mobile allowlist mode and AI access are named in user language. The weakness is that **Ultra** and **LTE allowlists** are not explained before selection, so the user cannot evaluate the tradeoff.

Evidence: [server list](raw/batya-vpn/2026-07-22/screenshots/06-server-picker.png), [reachability result](raw/batya-vpn/2026-07-22/screenshots/08-server-ping.png).

## Connection Smoke Test

The first-connect flow goes straight from the greened native switch to Android's standard VPN consent—there is no app-owned traffic/privacy disclosure. Android then requests notification permission.

The current Optimum connection **failed**:

- `tun0` never appeared during 15 seconds while the notification dialog was present;
- after denying/dismissing that prompt, `tun0` still never appeared during another 15-second poll;
- the app silently reset to its disconnected home state without an error;
- ordinary HTTPS remained reachable, but without `tun0` that only proves the emulator's base connection.

Sanitized log evidence identifies an expired TLS certificate during API fallback for device check/registration. The app already had an 11-route catalog, so the failure was not an empty list. This current-session result directly supports the Play-review hypothesis that Батя can look ready to connect and then fail without actionable feedback.

The runtime log also exposes substantial architecture: VLESS over XHTTP/TLS, multiple general and YouTube-specific outbounds, large Russian-service direct lists, QUIC/encrypted-DNS blocking rules and AppMetrica VPN-state/catalog telemetry. Critically, the installed build prints full live connection configurations—including credentials and endpoints—to info-level logcat. Raw logs remain quarantined; only the redacted conclusions are retained.

Evidence: [Android VPN consent](raw/batya-vpn/2026-07-22/screenshots/20-first-connect-step.png), [notification permission](raw/batya-vpn/2026-07-22/screenshots/21-notification-permission.png), [silent disconnected result](raw/batya-vpn/2026-07-22/screenshots/22-after-notification-denied.png), [sanitized runtime notes](raw/batya-vpn/2026-07-22/logs/runtime-connection-notes.md).

## Google Play Surface

The live Russian Google Play listing presents **«Батя VPN－Быстрый ВПН сервис»** under publisher **F2P** with rating 4.6, approximately 45K reviews, 1M+ downloads, age rating 3+ and category **Инструменты** at capture time. The store UI displayed 64 KB, which may be a split/update download figure and must not be treated as the full installed-package size. The short description is **«Скачать безопасный VPN для андроид. Надежный прокси-сервер и супер быстрый ВПН»**.

The official web listing was updated on **2026-07-10** and uses the release note **«Внесли небольшие улучшения»**. Its rating/review totals differed from the device listing during the same audit window (web 4.9 and roughly 47K; emulator 4.6 and 45,447), so rating must always be recorded with locale/surface/time rather than treated as a single fixed value.

The long store description is aggressive ASO copy around masking traffic, Telegram/Instagram/YouTube/TikTok, streaming, games, Russian UI, one-tap connection, unlimited traffic, trial, ad-free and paid **pro/turbo** speed. It lists Russia, Spain, France, UAE, Germany, USA, Canada, Italy and Turkey among available directions. Current installed 1.3.9 instead showed Poland, Austria, USA, Spain, France, Singapore, Hong Kong and special Optimum/LTE/AI modes; the store's location inventory is stale or describes a different catalog.

The seven store creatives establish a simple acquisition sequence:

1. broad promise: fast, convenient VPN for Russia across devices, illustrated with an older app home and US route;
2. blocked-service access: Instagram, Threads, Spotify, YouTube, Telegram and game/browser-like icons;
3. low-friction offer: **«5 дней БЕСПЛАТНО»** and **«Получить 5 дней VPN»** inside a Telegram-style mock;
4. recurring Telegram prize wheel: **«Батя каждый месяц разыгрывает призы в телеграм!»**, with iPhone/Mac-like devices, gifts, cash-prize testimonial copy and `@mybatyavpn`.
5. **«Настройка за 1 минуту»**, illustrated by an older settings/account screen rather than by actual setup steps;
6. **24/7 support plus a free period**, framed as a friendly chat with the mascot and explicitly claiming use on any devices plus installation help;
7. access to many servers, illustrated by a country selector with signal quality.

The first and seventh public creatives print raw server IPs inside mocked app screens. Those two images are intentionally not retained in the repository; this is a public store-content hygiene problem even if the endpoints themselves are not secret. The screenshots also depict an older product state: their country list, visible account shell and route set do not match the current installed 1.3.9 interface.

Evidence: [listing overview](raw/batya-vpn/2026-07-22/screenshots/23-google-play-listing.png), [service-access creative](raw/batya-vpn/2026-07-22/screenshots/25-play-screenshot-2.png), [five-day offer](raw/batya-vpn/2026-07-22/screenshots/26-play-screenshot-3.png), [monthly Telegram prize wheel](raw/batya-vpn/2026-07-22/screenshots/27-play-screenshot-4.png), [one-minute setup claim](raw/batya-vpn/2026-07-22/screenshots/28-play-screenshot-5.png), [support/free-period claim](raw/batya-vpn/2026-07-22/screenshots/29-play-screenshot-6.png).

### Review signal

The live listing showed 45,447 ratings/reviews and exposed **positive** and **critical** filters. Recent visible reviews from April–July 2026 split cleanly around the product's strongest promise and its operational weak point:

- positive reviewers repeatedly praise fast YouTube/4K playback, simple Russian UI, good paid-value, quick route updates during blocking, Telegram support, compensation days/discounts and prize draws;
- several say Батя keeps foreign services working without having to disable the VPN for banks, SMS or messengers—the job that the app's special routing appears designed to solve;
- critical reviewers repeatedly report paid access stopping after a few days/weeks, five-second disconnects, YouTube failing despite a good speed test, cabinet/subscription desynchronization, unexpected recurring payment and unresolved refund/payment-identification loops;
- multiple developer replies use a short generic pattern—contact the public support email so the account can be checked—instead of resolving or explaining the case in the Play thread;
- one recent critical review alleges that a Telegram prize-draw winner was never contacted or awarded anything. This is an unverified user allegation, not a confirmed finding, but it raises the verification burden for the store's recurring-prize claim.

Review text also describes **2-, 3- and 7-day** free periods, while the current app-linked offer and current store creative say five days. Dates and possibly campaign variants may explain part of the mismatch, but the acquisition promise is not historically consistent.

Review captures/UI dumps were inspected in a quarantined temporary location and are not retained in the repository because they contain reviewer names and profile images. The conclusions above are anonymized.

### Data disclosure, publisher identity and recommendations

Google Play's developer-supplied Data safety panel says:

- no user data is shared with third parties;
- no user data is collected;
- data is encrypted in transit;
- the developer provided no data-deletion mechanism/information.

That declaration needs reconciliation with observed product behavior: the app creates a durable device/account identifier, offers email binding, emits AppMetrica-labeled catalog and VPN-state events, and the embedded cabinet necessarily processes subscription/device/payment state. This audit has not yet proved which of those fields leave the device, so the finding is a disclosure gap to verify—not a claim that Play's declaration is false.

The Play support block identifies the developer as **F2P, ООО**, publishes `batyahelpsoft@mail.ru`, `mail@facetoplace.app`, a Saint Petersburg postal address and a `+32` telephone number. The store privacy link goes to `https://batyavpn.gitbook.io/guidance/servis/politika-konfidencialnosti`, whereas the app itself routes legal/privacy users to the separate HelpDeskEddy document hub. The Play publisher is therefore Russian ООО F2P while the VPN-specific in-app offer names Hong Kong's UNI PLAN TRADING LIMITED as provider; the operational/contractual relationship must be made explicit rather than inferred from branding.

Google Play co-surfaces **Windscribe VPN** in “other interesting apps” and **AdGuard VPN** in “similar apps”; the same rows also include DuckDuckGo, Brave, Google Files, ruID and Yandex. This shows the listing is algorithmically framed as both a VPN/proxy utility and a broader access/privacy/browser tool—not only against small Russian VPN brands.

On the public web listing, F2P's own portfolio contains **Ping VPN, Огонь VPN, Elyx VPN, VPN BOX, IntVPN and Sau**. Separate similarity recommendations include **JumpJumpVPN, NordVPN, Безлимит** and **Thunder VPN**. Device and web recommendations differ by surface/personalization, so both lists are retained as discovery evidence rather than product-controlled claims.

Evidence: [recommendation neighborhood](raw/batya-vpn/2026-07-22/screenshots/35-play-recommendations.png), [Data safety overview](raw/batya-vpn/2026-07-22/screenshots/36-play-data-safety.png), [encryption/deletion details](raw/batya-vpn/2026-07-22/screenshots/37-play-data-safety-2.png), [Play support/developer disclosure](raw/batya-vpn/2026-07-22/screenshots/39-play-support-info-2.png).

## Public Knowledge Base And Setup Funnel

Google Play links an older public GitBook rather than the newer in-app HelpDeskEddy legal hub. Its machine-readable corpus exposes the entire setup funnel: Telegram purchase, payment methods, Android/iOS/Windows/macOS key import through third-party v2RayTun, and the newer native Android TV app with QR-based subscription transfer and a guest mode.

Three indexed pages—menu/navigation, referral system and FAQ—are empty. Other documentation is materially stale: macOS claims Windows 8.1 as its requirement; annual price is both 1,499 and 1,599 RUB; Android TV says a three-day guest trial while current surfaces say five; support varies among 09:00–23:00/ten minutes, 24/7 and two working days; and the GitBook policies describe only Telegram ID despite the current native identity/cabinet model. The Android TV guide also distributes an APK directly for sideloading when Play is unavailable.

Detailed page-by-page routing and contradictions: [GitBook knowledge-base notes](raw/batya-vpn/2026-07-22/documents/gitbook-knowledge-base-notes.md).

## Release Artifact And Architecture

Installed 1.3.9 is a non-debuggable Flutter release (`versionCode` 105, min/target SDK 24/36) delivered as Play App Bundle splits. Its valid Google Play source stamp is dated **2026-07-10 20:40:52 UTC**, matching the official store update date. The installed split set totals 26.12 MiB compressed, again showing that the Play device surface's 64 KB value is not full app size.

The package combines Xray/V2Ray, bundled geo-IP/site databases, AppMetrica, Firebase Messaging/Installations, ML Kit barcode scanning, CameraX and Play licensing/integrity protection. It supports phone and Leanback launchers, Always-on VPN, an Android Quick Settings tile, and `batyavpn:` plus legacy-looking `buddyvpn:` deep-link schemes. Backups and cleartext HTTP are disabled; the VPN service is private and system-permission guarded.

The strongest technical/product tension is that a release-signed, `debuggable=false` build still logged complete live tunnel configurations to info logcat, while its store Data safety form says no data is collected despite Advertising ID permission and packaged AppMetrica/Firebase/install-referrer plumbing.

Evidence: [redacted static-package notes and hashes](raw/batya-vpn/2026-07-22/logs/static-package-notes.md).

## Release, Growth And Incident Playbook

The public channel reconstructs a clear evolution: first-party Android/TV launch in October 2025; iOS connection/auto-reconnect work in December; Android server selection and Quick Settings tile in December; macOS generic-client distribution in January 2026; bot geography selection; major Android redesign in February; personal cabinets announced in March and launched in April; large May outage followed by key rotation and seven-day compensation; Android 1.3.9 stamped/published on July 10.

Their real release notes live in Telegram, not Google Play. The recurring operating loop is: announce blocking/outage → suggest alternate routes → publish new app/key → tell users to update manually → compensate with days/promos → use the recovery as retention content. The channel is simultaneously status page, changelog, support deflector and growth surface.

Growth uses trial days, referrals, apology codes, limited promos, a free Telegram proxy, large phone/cash giveaways and review rewards. Public results/winner warnings make the giveaways feel operationally concrete, but repeated **+14 days for App Store/Google Play reviews** is direct first-party evidence of an incentivized-review practice prohibited by current Google Play policy. The same mechanism appears in sibling publisher app Огонь.

Detailed dated timeline and channel evidence: [public Telegram channel notes](raw/batya-vpn/2026-07-22/scrapes/telegram-public-channel-notes.md).

## Linked Legal Hub

The Settings row **«Конфиденциальность и правила»** opens `https://okosoft.helpdeskeddy.com/ru/knowledge_base/cat/9/juridicheskaja-informacija`. The public HelpDeskEddy hub contains seven documents: User Agreement, two differently scoped privacy policies, marketing-consent, cookie-consent, personal-data consent and Public Offer.

The emulator browser capture was quarantined because unrelated tab titles were visible. The destination and documents were then inspected through their public web URLs without submitting anything.

The VPN-specific offer names **UNI PLAN TRADING LIMITED**, Hong Kong company number `3023606`, at Suite C, Level 7, World Trust Tower, 50 Stanley Street, Central, Hong Kong. It states:

- access is sold through Telegram bot `@MyBatyaOnline_bot` as VPN keys/configurations;
- supported platforms are iOS, Android, Windows, macOS and Android TV; routers are excluded;
- the free period is five days;
- plans are 1, 3 or 12 months plus **Lifetime**; Lifetime lasts only while the service operates and the provider remains technically/legally able to supply it;
- payments are RUB through Telegram/payment infrastructure including YooKassa; timed plans may auto-renew and cancellation is via the bot;
- recommended fair use is at most five devices/simultaneous connections;
- 20 Mbps is only a non-binding normal-conditions reference; China, Iran, Turkmenistan, Mexico and Bangladesh are named as potentially unstable/unavailable;
- refund requests go to `@batyavpnhelp_bot`; support can take up to two working days, despite the in-app **«Поддержка 24/7»** label;
- service liability is generally limited to the last paid period; Russian law governs;
- the offer took effect on 2026-03-01.

The separate generic User Agreement is poorly fitted to the product: it repeatedly discusses a bot, information materials, educational programs and `/start`, and says refunds after access are generally unavailable except technical non-delivery, with a 24-hour request window. The VPN-specific offer instead refers to applicable Russian law and technical non-delivery without the same 24-hour limit. Two live contractual texts therefore provide different refund framing.

The detailed privacy policy names the same Hong Kong operator and applies Russian Federal Law 152-FZ. It covers site, app and `@MyBatyaOnline_bot`, direct registration/support/marketing data and device-derived data collected automatically through cookies/similar technologies; retention is expressed generically as until purpose, withdrawal or statutory expiry. It does not clearly enumerate the actual VPN telemetry fields or state VPN traffic/logging behavior.

Marketing consent authorizes email, SMS, messengers and social messages and routes withdrawal to `batyahelpsoft@mail.ru` or `@batyavpnhelp_bot`. The forms still contain blank site/app placeholders, which is a document-quality and informed-consent weakness.

## Publisher Relationship To Verify

Google Play places Батя in the same **F2P** publisher portfolio as Огонь and Ping. Product behavior, shared infrastructure and legal responsibility must still be proven separately.

## Audit Boundaries And Blockers

- `PASS`: all visible native tabs, server selector, dark mode, Android TV QR prompt, cabinet subsections, pricing, store creatives, store reviews/data-safety/support, public knowledge base, public Telegram history and installed package architecture were inspected and recorded.
- `FAIL_OBSERVED`: current Optimum connection did not create `tun0`; the app silently reset after an expired-certificate API failure.
- `BLOCKED_BY_RUNTIME`: because no tunnel formed, speed, leak resistance, route correctness, kill-switch and disconnect recovery could not be validated.
- `NOT_REQUESTED`: no paid plan was selected, payment order created, support message sent, Telegram bot started, channel joined or giveaway entered.
- `NOT_RESET`: app data was not cleared, so first-install onboarding and exact anonymous-trial activation were not reproduced.
- `BLOCKED_BY_ACCESS`: Hong Kong incorporation/name/number were confirmed from the official incorporation list, but current company status/directors/shareholders require the interactive or paid registry flow.
- `UNVERIFIED_CLAIM`: public winner lists exist, but prize fulfillment to individuals was not independently verified.

The app, Chrome and Google Play were force-stopped after capture; no competitor process or `tun0` remained before handoff to the next profile.

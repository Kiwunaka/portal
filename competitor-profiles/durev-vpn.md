# Durev VPN — Mobile App Competitor Profile

**Snapshot date:** 2026-07-22<br>
**Status:** `DEEP PASS COMPLETE WITH BLOCKERS` — isolated entry/import UX, controlled email lookup, public web/store/Telegram/legal surfaces, current release, entity chain and redacted Android architecture captured; signed-in product and live connection require a purchased/previously registered key<br>
**Android package:** `com.durevpn.durevvpn`<br>
**Installed version:** 2.0.1-phone (`versionCode 1464`)<br>
**Install source:** Google Play

Evidence root: [`raw/durev-vpn/2026-07-22/`](raw/durev-vpn/2026-07-22/)

The earlier `01-launch` artifact remains provenance-only. Accepted current-session evidence begins with `02-isolated-launch`.

## Product Positioning

Durev is built as a deliberately unserious, meme-led VPN brand wrapped around a technically serious multi-protocol client. The live Android entry screen looks like a Windows 95 utility, calls itself `key-add.exe`, uses a muscular Pavel-Durov parody as the recurring hero and describes the product in broken English: “This VPN made by durev for all durev fans and great people.”

This is the main competitive lesson: the product does not look interchangeable. The retro desktop metaphor, character system and intentionally blunt copy are recognizable before a user sees a country or price. The trade-off is accessibility and clarity: the current Flutter canvas exposed no useful text or controls to the Android accessibility tree, and several labels describe the implementation rather than the user’s task.

Evidence: [isolated entry screen](raw/durev-vpn/2026-07-22/screenshots/02-isolated-launch.png).

## Entry and Key Import

The cold start offers four routes:

- **Ввести ключ вручную**;
- **Импортировать из почты**;
- **Импортировать из Telegram**;
- **Сканировать QR-код камерой**.

There is no generic registration/paywall wall. Durev treats a subscription key as the portable account object and gives existing customers several recovery paths immediately. That is strong for reinstall, TV and cross-device transfer, but weak for a completely new customer: the observed screen contains no price, trial CTA, purchase link, explanation of what a key is or route to compare plans.

### Manual key

`key-setup.exe` asks for an editable name (`My VPN key`) and a key value, with **Вставить** and **Сохранить**. Saving an empty form produced no visible validation, field-level hint or disabled state. The duplicate post-tap screenshot is excluded from accepted evidence.

Evidence: [manual-key form](raw/durev-vpn/2026-07-22/screenshots/03-manual-key.png).

### Email import

The email route asks for one address and exposes **Продолжить**. It does not explain whether this sends a code, magic link, existing-key lookup or creates an account; there is no privacy/context copy before submission.

The owner authorized one controlled lookup using the connected Gmail account. Durev returned **Пользователь с таким email не зарегистрирован** and suggested registering on the site or in the bot. No Durev email arrived, no account was created and no personal address is retained. This proves that the route is an existing-account/key recovery path, not registration. Creating an empty web account would not unlock the client without a paid/trial key, so the audit stopped before checkout.

Evidence: [email-import form](raw/durev-vpn/2026-07-22/screenshots/05-email-import.png).
Result: [unregistered-email state](raw/durev-vpn/2026-07-22/screenshots/07-email-not-registered.png).

### Telegram import

`key-tg.exe` says an active Durev Telegram account is required and exposes **Открыть Telegram**. The action resolved to the public `@DureVpnBot` with a short-lived per-device start token. The token-bearing destination was quarantined; the bot was not started and no Telegram message was sent.

Evidence: [Telegram import explanation](raw/durev-vpn/2026-07-22/screenshots/06-telegram-import.png).

### QR pairing

The main label says **Сканировать QR-код камерой**, but the observed route did the opposite: this device displayed a live QR and four-digit code, valid for ten minutes, for another authorized Durev device to scan. The cross-device transfer concept is good; the entry label is directionally wrong and creates the wrong permission expectation. The live QR/code capture was quarantined and is not retained in audit evidence.

## Signed-In Product Shape

The current official Play creatives show a much deeper signed-in product than the live no-key state exposes:

- a single large power control with status, selected country and auto selection;
- 50+ advertised servers and one-click country selection;
- named keys such as a primary key, allow-list key and special Gemini/Roblox key;
- per-key status, QR, refresh, settings and default-key selection;
- desktop/tablet navigation for VPN, keys, settings and information;
- endpoint/mask details in the product UI.

Screenshots containing raw connection endpoints or QR payloads were deliberately excluded. Safe retained creatives: [speed positioning](raw/durev-vpn/2026-07-22/screenshots/store-02.webp), [country/server claim](raw/durev-vpn/2026-07-22/screenshots/store-04-countries.webp), [support positioning](raw/durev-vpn/2026-07-22/screenshots/store-05-support.webp).

## Technical Architecture

The Android app is a Flutter client with a native Go/Xray networking layer. The shipped engine contains capabilities associated with WireGuard, Shadowsocks, VLESS, VMess, Trojan, QUIC, Reality, Xray, SOCKS5, SSH and ECH, plus a separate HEV SOCKS5 tunnel. These are bundled engine capabilities, not proof that every transport is enabled commercially.

The package includes CameraX/ML Kit barcode scanning, deep links for `durevvpn:` and verified app links for both official domains, a non-exported VPN foreground service and an exported Quick Settings VPN tile. It requests boot, battery-optimization, camera and notification capabilities. No obvious major third-party analytics/crash SDK was found in the static pass, but that does not prove absence of first-party telemetry.

The native bundle contains multiple official control-plane domains plus rotating cover-looking hosts/direct-IP fallbacks. Exact endpoints are excluded. This architecture is materially more censorship-resilient than a single API origin. Two narrow network-security entries permit cleartext for unresolved/empty domain entries; this is not evidence that cleartext is globally allowed, but it deserves internal cleanup.

Detailed evidence: [redacted static package notes](raw/durev-vpn/2026-07-22/logs/static-package-notes.md).

## Website, Pricing and Conversion

The Russian site sells a broad platform story: 50+ countries, up to 300 Mbps, 10 devices, no hidden analytics, crypto payments and apps/extensions for the major desktop, mobile, TV and browser platforms.

Current displayed Russian pricing:

| Plan | Total | Displayed monthly | Displayed discount |
| --- | ---: | ---: | ---: |
| Trial | 17 ₽ | — | — |
| 1 month | 459 ₽ | 459 ₽ | 10% |
| 6 months | 2,414 ₽ | 402 ₽ | 21% |
| 1 year | 3,864 ₽ | 318 ₽ | 37–38% depending on rendered block |
| 2 years | 5,244 ₽ | 219 ₽ | 57% |

Older official channel copy says 15 ₽ for the trial, while the current hero says 17 ₽. The English storefront uses separate USD prices. The home page also renders a supposed **Подключено прямо сейчас** counter. Six immediate server responses varied from roughly 60.6K to 64.1K, jumping by thousands between requests. It behaves like randomized social proof, not a credible live connection counter.

The visible customer quotes are generic and unsourced, including a placeholder-style “Вася Пупкин”. These tactics make the site feel busy, but they weaken any serious privacy/trust positioning.

Detailed evidence: [website, store, legal and Telegram notes](raw/durev-vpn/2026-07-22/documents/website-store-legal-and-channel-notes.md).

## Growth and Referral Machine

Durev’s public Telegram channel is the real lifecycle surface, with roughly 58K subscribers observed; the public bot showed roughly 188K monthly users. Its acquisition loop combines:

1. news about blocks or outages;
2. a claim that Durev still works or has a special server;
3. an immediate bot/cabinet CTA;
4. a deadline, promo code, raffle or live draw;
5. referrals that award lifetime bonuses on every invited purchase, with bank-card cash-out or conversion into VPN days.

The channel also teaches resilience: bind an email in case Telegram is blocked, use a web cabinet mirror, and switch to recommended third-party Apple clients when native distribution is unavailable. That operational education is valuable. Claims that payments look like ordinary ecommerce or that masked traffic avoids international-traffic billing are unverified and compliance-sensitive; POKROV should not repeat them without legal and technical proof.

## Release and Alternative-Client Strategy

An official channel post dated 7 July 2026 announced Durev 2.0 for Android and Windows, automatic in-app updates, Google Play and Microsoft Store distribution, and an iOS build awaiting App Store review. The installed Android build is the announced 2.0.1-phone line and Play reports an update on 5 July 2026.

There is no confirmed live native iOS listing in the observed pass. Durev instead recommends third-party clients including Happ and Karing, and has discussed V2RayTun, V2Box and Streisand when available. This is a practical distribution strategy: the paid account/key survives even when one client disappears. It also shifts support, privacy and UX risk onto external apps and needs a signed official compatibility directory.

## Store Scale, Reviews and Recommendation Graph

Google Play showed 100K+ installs, an approximate 3.8 rating and roughly 5.6K reviews depending on the localized view. Positive feedback mentions speed and working allow-list routes. Repeated negative themes include:

- mobile disconnects every 10–15 minutes;
- allow-list bypass instability;
- a manually selected server not being retained;
- forced key refresh;
- many special servers reporting unusable ping;
- Gemini/Roblox labels not reliably delivering the promised route.

Developer replies commonly tell users to refresh the key and choose a special anti-blocking server, moving recovery burden onto the customer. Nearby Play recommendations included Speedify, hidemy.name, Cure VPN, PureVPN, Windscribe and v2RayTun. Store recommendations are algorithmic neighbors, not verified customer endorsements.

## Ownership, Privacy and Contract Gaps

The public responsibility chain is fragmented:

- the website terms/privacy/controller/seller name Kazakhstan LLP/TОО **CIT / СИТ**, BIN `220440014920`;
- Google Play names **Dmitrii Bratashev, Individual Entrepreneur** in Georgia;
- the Play publisher brand is **Cryptan Coder Llc**.

An exact Georgian-language search in the official NAPR registry returned an active individual-entrepreneur record matching the Play legal developer on 22 July 2026. Personal registry identifiers were excluded. The current Kazakhstan registry status could not be authoritatively refreshed without authenticated/API access and remains `BLOCKED_BY_ACCESS`. No public responsibility map explains which entity develops, bills, controls data or handles refunds.

The privacy policy promises no browsing history, source IP, DNS, content or session start/end timestamps, but admits account/user ID, email, aggregate transferred bytes and optional device/OS crash information. Play’s Data Safety form says no data is collected or shared. The email, Telegram pairing, subscription and refund flows necessarily use identifiers. “No logs” can describe traffic content; “no data collected” cannot accurately describe the documented account and support system.

The terms say paid funds are non-refundable while linking to a refund policy that advertises a 14-day first-purchase guarantee. That guarantee disappears after 5 GB, excludes renewals/upgrades and cryptocurrency, and can reject cases attributed to the ISP, device or user skill. The policy requests identity/payment evidence and treats traffic logs as sole proof. These conditions need to be visible before checkout, not discovered in a separate document.

## What POKROV Should Copy

- A memorable visual world and recurring character system; users can recognize Durev without reading a logo.
- Portable subscription keys with manual, email, Telegram and cross-device recovery.
- Separate keys/profiles for normal traffic, allow-list networks and task-specific routing.
- One-tap home plus deeper key management instead of exposing protocol complexity first.
- Operational Telegram release/status feed tied to concrete recovery actions.
- Referral value stated as money or VPN days and visible for the full customer lifetime.
- A signed directory of official mirrors and supported third-party clients for distribution resilience.
- Frequent cross-platform releases with concrete human changelogs.

## What POKROV Should Not Copy

- Misleading randomized “connected now” counters or placeholder testimonials.
- Fear-driven urgency, endlessly extended “last day” promotions or unverified masking/payment claims.
- Canvas-only controls with an empty accessibility tree.
- A new-user entry screen that contains four import routes but no purchase/trial explanation.
- Silent validation failures and directionally wrong QR wording.
- Publishing QR/config/endpoints in store creatives.
- Contradictory trial prices, refund promises, privacy declarations and legal entities.
- Promising native iOS on the site while the official release channel says App Store review is still pending.

## Current Flow Health

| Flow | Health | Evidence / blocker |
| --- | --- | --- |
| Cold launch → key entry hub | **PASS** | Isolated start; distinctive but no new-customer conversion path |
| Manual key → validation | **FAIL IN OBSERVED SESSION** | Empty save produced no visible validation or disabled state |
| Email → existing key/account | **PASS / NO ACCOUNT FOUND** | Authorized lookup returned “not registered”; no mail, account, code or address retained |
| Telegram import → bot | **PASS TO PUBLIC LANDING** | Correct public bot with per-device token; bot not started |
| QR cross-device pairing | **PARTIAL / COPY DEFECT** | Live pairing payload generated, but route label promised camera scanning |
| Signed-in home / country / key management | **STORE + STATIC CONFIRMED, MANUAL BLOCKED** | No paid key/account available yet |
| Connect / disconnect / Quick Settings | **MANUAL BLOCKED** | No usable key; no tunnel started |
| Website → trial/plan/cabinet | **PASS TO PUBLIC SURFACES** | Pricing and destinations mapped; no payment performed |
| Native iOS distribution | **PENDING BY OWN RELEASE POST** | Site advertises iOS; channel says App Store review pending |
| Current Georgian developer status | **PASS** | Exact official NAPR search returned active IE record; personal ID excluded |
| Current Kazakhstan entity status | **BLOCKED_BY_ACCESS** | Public official dataset exists, but exact current lookup requires authenticated/API access |

Final teardown: Durev, Chrome and Google Play were force-stopped. All sixteen competitor processes were absent and `tun0` did not exist before moving on. No purchase, tunnel, account creation, review/rating, support message or Telegram bot start occurred.

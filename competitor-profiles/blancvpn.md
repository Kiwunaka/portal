# BlancVPN — Mobile App Competitor Profile

**Snapshot date:** 2026-07-22
**Status:** `DEEP PASS COMPLETE WITH BLOCKERS` — live tunnel/first-connect permissions are blocked by paid access, Google Play checkout is blocked by the Russia region, and the persisted Космос routing exclusion requires a clean-device retest before it can be called a default
**Android package:** `com.blancvpn.app`
**Installed version:** 1.7.0
**Install source:** Google Play

Evidence root: [`raw/blancvpn/2026-07-22/`](raw/blancvpn/2026-07-22/)

## Audit Checkpoint

- BlancVPN was the only competitor active during native exploration; it was force-stopped after capture and no `tun0` interface remained.
- Every accepted screenshot/UI state will be written under the evidence root immediately.
- Purchase, review, public-post, support-send and destructive account actions are out of scope.
- Any account identifiers, credentials, public IPs, VPN endpoints or provider tokens will remain outside the worktree.
- Final text scan found no email address, IPv4 address, tokenized query, JWT or bearer credential in the retained BlancVPN profile/evidence. Temporary Gmail values were cleared after authentication.

## First Launch

Cold launch goes directly to a dark navy email gate—no splash permission or benefit carousel. The screen says **«Добро пожаловать» / «Войдите или зарегистрируйтесь»**, accepts one email, and uses a single **Продолжить** action for both login and registration.

Consent copy is placed before the CTA outcome: pressing Continue accepts the BlancVPN Terms of Use and Privacy Policy. Both document names are tappable. A secondary outlined **Пропустить** action at the bottom allows anonymous exploration.

Observed behaviour corrects that first impression: **Пропустить** closes the activity and returns to the LDPlayer launcher. Relaunch shows the same email gate, so it is an exit/cancel action, not anonymous product access. The Russian label is misleading for a blocking auth screen.

Visual language: near-black/navy background with a soft blue radial glow, restrained white/grey typography, bright blue full-width primary CTA and thin blue-grey secondary outline. The screen is unusually calm and has a strong vertical hierarchy, though the skip action is separated by a very large dead zone.

Evidence: [isolated first launch](raw/blancvpn/2026-07-22/screenshots/01-isolated-launch.png).

The empty form has two layers of feedback: an inline red **«Обязательное поле»** state and a bottom error snackbar. A malformed address produces **«Email не найден или некорректен»**. Evidence: [empty-email validation](raw/blancvpn/2026-07-22/screenshots/06-empty-email-validation.png).

## Passwordless Authentication

A valid address routes to a six-box verification screen with **Изменить email**, a resend countdown and explicit Spam-folder guidance. BlancVPN sends a six-digit login code; the same email also contains a tokenized one-click login destination on `blncaccount.com`, plus links to the help centre, chat and Trustpilot. Tokens, address and code were quarantined.

The owner-authorized code authenticated successfully without a password, separate registration form, profile questions, payment or email-link round trip. The code screen first showed **«Все верно!»** and then opened the signed-in shell after a short backend delay. This is a clean unified sign-up/login model.

The transactional footer identifies service provider **Yadda OÜ**, Estonia. Independent store, site and official Estonian-registry checks match that entity; the email was only the first identity signal, not the sole proof.

## Signed-In Home

The first signed-in screen is immediately usable and contains three bottom tabs: **Главная**, **Локации**, **Профиль**. It defaults to **Германия — Берлин** and shows a large two-state Off/On switch. Copy warns that the first connection will request both Android VPN permission and notification permission.

The disconnected trust message is blunt—**«Без VPN ваш IP общедоступен»**—without printing the actual public IP. That is safer than competitors that expose both current and exit addresses on the home screen.

Evidence: [signed-in disconnected home](raw/blancvpn/2026-07-22/screenshots/07-home-signed-in-disconnected.png).

## Locations

The location tab combines search, a sort-order toggle and live three-bar quality indicators. The selected row is blue. The current list contains **51 city rows across 46 countries**; Germany has Berlin/Frankfurt and the US has Houston, Miami, New York, Los Angeles and San Jose. Every other observed country has one city.

Countries: Australia, Austria, Argentina, Belgium, Bulgaria, Brazil, United Kingdom, Hungary, Germany, Hong Kong, Greece, Denmark, Israel, India, Ireland, Spain, Italy, Kazakhstan, Canada, Colombia, Lithuania, Malaysia, Mexico, Nigeria, Netherlands, Norway, UAE, Peru, Poland, Portugal, Russia, Romania, Singapore, Slovakia, USA, Turkey, Ukraine, Finland, France, Croatia, Czech Republic, Switzerland, Sweden, South Africa, South Korea and Japan.

The first order appeared quality/proximity-based rather than alphabetical: Prague, Amsterdam, Berlin, Brussels, Vienna and Frankfurt led the list. This turns the selector into a performance recommendation without hiding manual choice.

Evidence: [location list/top](raw/blancvpn/2026-07-22/screenshots/08-locations.png), [location list/bottom](raw/blancvpn/2026-07-22/screenshots/12-locations-scroll-4.png).

## Profile And Subscription State

The profile shows the signed-in address, overflow menu, subscription card, Settings, Technical Support, an external Help Centre and exact build `v1.7.0+174`. The new account has no active subscription and the rest of the product remains browseable, but connection is blocked with a snackbar saying the current profile has no VPN access.

The profile capture was quarantined because it displays the account address.

## Native Paywall

The purchase CTA opens a native three-plan paywall in Russian rubles:

| Plan | Price | Monthly equivalent | Framing |
| --- | ---: | ---: | --- |
| 1 year | 5,590 RUB | 459.45 RUB/month | “Best choice”, 50% discount, 2,795 RUB saved |
| 6 months | 4,399 RUB | 733.17 RUB/month | 22% discount, 967.78 RUB saved |
| 1 month | 899 RUB | 899 RUB/month | No discount, “good for starting” |

The arithmetic does not reconcile:

- 5,590 / 12 is 465.83 RUB, not the displayed 459.45;
- saving 2,795 against an implied 8,385 original price is 33.3%, not 50%; a true 50% saving would also be 5,590;
- against the visible 899-RUB monthly baseline, the annual saving would be 5,198 RUB and the six-month saving 995 RUB, not 2,795 and 967.78.

This is not harmless rounding; price, monthly equivalent, discount and savings use incompatible baselines.

Benefits promise one subscription across devices, 30+ locations, 24/7 live support and maximum connection speed. The same page offers **Restore** and repeats Terms/Privacy consent.

Selecting the one-month plan reached Google Play Billing but did not start a purchase: Play displayed its Russia-region payment-suspension notice. No payment details were entered and no confirmation was attempted.

Evidence: [native paywall](raw/blancvpn/2026-07-22/screenshots/14-paywall.png), [benefits/restore/legal](raw/blancvpn/2026-07-22/screenshots/15-paywall-lower.png), [Google Play Russia block](raw/blancvpn/2026-07-22/screenshots/16-month-checkout-russia-block.png).

## Protocol And Routing Settings

The protocol selector is not hidden behind an “advanced” accordion. It explains five choices in plain language:

- **Automatic** — choose the best protocol for the user;
- **AmneziaWG** — fast, with added encryption and traffic masking;
- **AmneziaWG Extra** — for targeted blocking in Russia;
- **Xray** — for stronger censorship systems;
- **Xray Extra** — extra settings when other protocols fail.

The page explicitly says not to change protocols if everything works and warns that a reconnect is required. This is strong anti-blocking onboarding: it names the failure condition, not just the technology.

Two routing controls are enabled/configured by default:

- **Open Russian services without VPN** is on and names Yandex, Gosuslugi and banks. A warning says AmneziaWG exclusions work only for apps.
- **VPN mode for apps** defaults to **All except selected**, with one of 155 installed/system packages already selected.

The per-app screen supports three explicit models: all apps, all except checked apps, or checked apps only. It exposes search and the selected/total count. Unlike GnuVPN, it includes a very broad system-package inventory, which makes the list technically complete but noisy. A controlled scan preserved the original mode/count and did not change any checkbox; the identity of the single preselected package was not visible in the bounded pass.

A later read-only full-list scan identified that persisted exclusion as **Космос VPN** (`ru.space.vpn`). The audit did not select it, but there is not enough evidence to tell whether BlancVPN chose the previously used VPN automatically or inherited an older emulator preference. It should not be described as a factory default without a clean-device retest. Evidence: [selected Космос VPN exclusion](raw/blancvpn/2026-07-22/screenshots/21-app-routing-selected-kosmos.png).

The push setting **Show notification when VPN is off** is enabled. Its description says disabling it leaves the notification visible only while connected—an explicit retention/reminder choice rather than a connection requirement.

Evidence: [protocols/default routing controls](raw/blancvpn/2026-07-22/screenshots/17-settings-top.png), [three per-app routing models](raw/blancvpn/2026-07-22/screenshots/18-app-routing.png), [app-list search](raw/blancvpn/2026-07-22/screenshots/19-app-routing-search-blanc.png).

## Help, Support And Account Controls

**Help Centre** first opens `https://getblancvpn.com/help` and resolves to the public `blancvpn.ltd` help site. The visible landing page has search, a same-day Russia availability banner and nine platform families: Android, iOS, Windows, macOS, Linux, Smart TV, Steam Deck, routers and browser extension. All 99 current Russian articles and their sanitized destinations were indexed. Evidence: [help-centre destination](raw/blancvpn/2026-07-22/screenshots/20-help-center-destination.png).

**Technical Support** opens an authenticated `blncaccount.com` web handoff containing a short-lived account token. The destination was observed but the tokenized URL and account-bearing screenshot were quarantined. No support message was sent.

The profile overflow contains **Logout**. Expanding **More** reveals a destructive red **Delete profile** action. Neither was executed. This makes account deletion discoverable but hides it one level deeper than logout.

## Connection Blocker

Toggling the home switch without a subscription routes back to the no-access profile state. It does not reach Android's VPN consent dialog, does not offer a trial and does not create a tunnel. Therefore the live connect/disconnect check is currently `BLOCKED_BY_PAID_ACCESS`; no purchase will be made for this audit. The promised first-connect notification and VPN permissions also remain unobserved for the same reason.

## Android Architecture And Release Signals

The installed Google Play build is Flutter-based, targets SDK 36 and bundles explicit AmneziaWG and Xray VPN services plus native Amnezia, SOCKS and Go components. Embedded GeoIP/GeoSite databases support the observed censorship and selective-routing features.

Two independent release mechanisms are compiled into the package beyond ordinary Play delivery:

- an APK installer receiver and background downloader indicate a direct APK/self-update path;
- a Shorebird application manifest indicates the technical capability to distribute Flutter/Dart patches without a full store binary update.

These are package-level capabilities, not proof that BlancVPN actively serves direct APK or Shorebird updates. The completed public distribution pass found no direct BlancVPN APK and no public evidence of a delivered Shorebird patch.

Sentry Android/NDK and performance components, Firebase Messaging/Installations/DataTransport and disabled-by-default PostHog metadata are present. This proves SDK inclusion, not a specific event/logging policy. Google Play Billing 8.0.0, WorkManager, InAppWebView, URL-launch/share integrations and a Quick Settings tile are also bundled.

The manifest declares `QUERY_ALL_PACKAGES`, matching the unusually broad per-app routing list. It also carries Android TV/Leanback launcher support. Production APK assets include beta/stage/test/work-in-progress UI material, which is avoidable package hygiene/bloat even though it does not prove those environments are accessible.

Redacted evidence: [static package notes](raw/blancvpn/2026-07-22/logs/static-package-notes.md).

## Public Website And Help-Centre Surface

The current Russian sitemap exposes **176 pages**: 99 help articles, 46 country landing pages, nine platform download pages and 22 top-level product/growth pages. All 99 help URLs returned HTTP 200 in a deliberately single-threaded crawl.

The help centre is substantially broader than the native app. Its indexed instruction set breaks down into 45 device/client setup pages, 14 router/XKeen pages, 14 routing/troubleshooting pages, 15 account/subscription/growth pages, four store/account-workaround pages and seven general product/education pages. The audit retains every route, page title and structural heading, plus a sanitized per-page destination graph:

- [complete 99-page help index](raw/blancvpn/2026-07-22/documents/help-center-page-index.md);
- [sanitized help-centre link map](raw/blancvpn/2026-07-22/documents/help-center-link-map.tsv).

This is effectively a multi-client VPN operating manual. In addition to BlancVPN's own clients it teaches users to configure Happ, INCY, V2RayN/V2RayNG, NekoRay, Hiddify, FoXray, V2Box, Shadowrocket, Outline, WireGuard, OpenVPN, Shadowsocks, Throne and ClashX, plus Keenetic/TP-Link/ASUS routers, Android/Apple TV and Steam Deck. It also documents browser extensions, device sharing and passing configuration links to family devices without sharing full account access.

Its anti-blocking playbook is unusually explicit: protocol choice, Extra locations, Russian-service exclusions, per-app/site routing, whitelist bypass, subscription refresh, server availability tests, DNS/FakeDNS, MUX and fragmentation are presented as named recovery steps rather than generic “reconnect” advice. The knowledge base therefore acts as a fallback product when the official client or store distribution fails.

The same breadth creates a trust and maintenance burden. Instructions send users to many third-party clients, GitHub releases, short-link domains, deep links and local router interfaces. Some pages recommend App Store region changes, a second foreign Apple account and—when Apple rejects Russian numbers—renting a foreign number. Those workarounds reduce acquisition friction but increase platform-terms, security and support risk.

## Public Pricing, Payments And Growth

The current web price cards shown from the audit region are internally consistent:

| Web plan | Total | Displayed monthly | Framing |
| --- | ---: | ---: | --- |
| 24 months | €71.76 | €2.99/month | 60% discount, best choice; crossed-out €179.40 |
| 12 months | €47.88 | €3.99/month | 50% discount; crossed-out €95.76 |
| 1 month | €7.99 | €7.99/month | no discount |

Unlike the Android RUB paywall, `monthly × months = total` on both discounted web plans. Evidence: [sanitized pricing capture](raw/blancvpn/2026-07-22/browser/03-pricing-cards-safe.png).

Public instructions say web/Telegram checkout accepts Russian cards including MIR, foreign cards and cryptocurrency. Card payments enable automatic renewal; the account site or Telegram bot can change the card or disable renewal. Cryptocurrency purchases are explicitly excluded from the 30-day refund promise. App Store and Google Play refunds defer to the platform's own rules.

The referral programme gives **30 days to both sides**. The new customer receives the bonus immediately after buying any plan; the inviter receives it only after the referred subscription stays active for 30 days. Inviter rewards are capped at two years. The article also warns that VPN advertising is prohibited in Russia from 1 September 2025 and tells users to share only with people they personally know—growth copy coupled to a compliance warning.

The site sells gift subscriptions, runs a separate partner programme and exposes Open Source sponsorship, Bug Bounty, censorship-reporting, password-generator, IP/WHOIS and XKeen-generator surfaces. This widens acquisition well beyond a single “buy VPN” funnel.

## Public Claim Consistency Checkpoint

- Homepage copy promises speeds up to **10 Gbit/s**; the current Google Play description promises up to **2 Gbit/s**.
- The pricing page says more than 50 locations; the Play description says 30+; the inspected Android selector contains 51 city rows across 46 countries. These may use different units or freshness, but the marketing does not define them consistently.
- Public pages promise unlimited devices, unlimited traffic, 24/7 support, no logs and a 30-day guarantee. Store privacy declarations and the detailed legal documents show that “no logs” is limited to connected browsing activity, while account, purchase, product-use and diagnostic data may still be collected and retained.
- Distribution/account/legal traffic spans `blancvpn.ltd`, `blancvpn.com`, `getblancvpn.com`, `blancvpn.legal`, `blncaccount.com` and multiple branded short-link/deep-link domains. Each has a purpose, but the fragmented domain graph makes phishing verification harder for users.

Safe public visual references: [homepage](raw/blancvpn/2026-07-22/browser/01-home-ru-safe-full.png), [help centre](raw/blancvpn/2026-07-22/browser/02-help-ru-safe-full.png), [pricing cards](raw/blancvpn/2026-07-22/browser/03-pricing-cards-safe.png). Captures containing the website's current-IP banner were moved out of the worktree into the sensitive quarantine.

## Stores, Releases, Channel And Legal Entity

The detailed public-surface pass is retained in [website/store/legal/release/channel notes](raw/blancvpn/2026-07-22/documents/website-store-legal-release-and-channel-notes.md).

The short version:

- Native iOS/macOS/Android apps were publicly announced on 27 October 2025. Android is now installed as 1.7.0; Apple is on 1.6.2. Windows remained “in development” in two June 2026 updates, despite the homepage's native-download wording.
- The Chrome extension is already 1.19.2 with 100K users but only a 2.6 rating; Firefox exposes 18 releases since August 2025. Releases cluster tightly around blocking events.
- Telegram has 96.8K subscribers and 87 surviving public posts in the captured history. It functions as censorship newsroom, operational support surface and promo channel. April's major Xray/split-tunnel release, June's seven-day incident compensation and July's tested INCY fallback are especially strong product operations.
- The App Store recommendation rail connects BlancVPN directly to installed competitors Red Shield and TipTop, and also recommends Paper, Amnezia, VPN Russia, Mirage, Happ, Дед Proxy, Netcraze and EVA. Google Play recommendations vary by locale/session.
- Yadda OÜ (`16469911`, VAT `EE102489668`) is the matching Estonian publisher/entity. It remains entered in the register, but its 2025 annual report is overdue and an official deletion notice is flagged. The body of BlancVPN's Terms/Privacy fails to name that contracting entity.
- Terms and Privacy are identical across `blancvpn.ltd` and `blancvpn.legal`. Terms date to May 2025; Privacy to June 2024. Refund exclusions, fair-use throttling/account-sharing limits, telemetry scope and the age rule materially qualify or contradict shorter marketing claims.

## Review And Reputation Gap

The live reputation surface is polarized, not uniformly strong:

- Google Play currently shows 4.4/5 and 100K+ downloads, but its freshest visible reviews complain about login-code failure after purchase, support delays, cancellation friction and no native Windows client.
- The GB App Store shows 4.5/5 from 39 ratings; its visible sample mixes a reliability-positive review with paid-service, support and refund complaints. Storefront counts and mixes vary.
- Chrome is much weaker at 2.6/5; Firefox is 3.5/5 from a small, sharply polarized sample.
- Trustpilot is 2.0/5 from 120 reviews, with 48% five-star and 40% one-star. Recent allegations repeatedly cluster around service availability/speed, subscriptions or login codes not activating, router/Extra paths, support latency/automation and refund handling. These are reviewer claims, not independently proven incidents.

BlancVPN's own review page says it does not remove or edit reviews, yet its initial rendered wall shows ten entries and every one is 5/5, with no visible March–July 2026 negative wave or current TrustScore before “read more.” The linked testimonials appear to be real Trustpilot entries, but the selection is neither current nor representative. This creates an avoidable credibility failure precisely around support and refunds—the two subjects the selected testimonials praise most strongly.

Detailed evidence and storefront caveats: [review/reputation section](raw/blancvpn/2026-07-22/documents/website-store-legal-release-and-channel-notes.md#review-and-reputation-surface).

## Flow Health And Product-Design Audit

| Flow step | Health | Evidence-backed assessment |
| --- | --- | --- |
| Cold launch → email gate | `PASS` | Fast, calm and visually coherent; consent links are present before the CTA. The huge lower dead zone wastes space but does not block the task. |
| “Skip” | `FAIL` | It closes the app and returns to the launcher; relaunch returns to the same mandatory gate. The label implies guest access that does not exist. |
| Email → six-digit code → signed-in shell | `PASS` | Unified passwordless registration/login is short, explains resend/spam behaviour and completed successfully. |
| Signed-in browse: Home / Locations / Profile | `PASS` | The three-tab hierarchy is obvious; connection, selected location and account state are easy to find. |
| Location selection | `PASS WITH FRICTION` | Search, sort and quality bars are useful and the initial order behaves like a recommendation. The sort icon is unlabeled, quality is not numeric, and flags carry too much identification weight. |
| Native plan comparison | `FAIL — TRUST` | Visual hierarchy and recommended-plan emphasis are strong, but annual/monthly/discount/savings arithmetic contradicts itself. This is a conversion-killing billing defect. |
| Google Play checkout | `BLOCKED_BY_REGION` | Russia-region Play Billing suspension prevents purchase; no payment was attempted. |
| First VPN connection | `BLOCKED_BY_PAID_ACCESS` | No trial or free connection path; Android VPN/notification consent and live tunnel could not be tested safely. |
| Protocol recovery | `PASS` | Five choices explain when to use Automatic, AWG/Xray and Extra modes in user language, with a reconnect warning. |
| Russian-service and per-app routing | `PASS WITH FRICTION` | Strong three-mode model and searchable inventory. Exposing 155 installed/system packages without a “selected only” view makes the screen noisy; the persisted Космос exclusion needs a clean-device retest before calling it default. |
| Help centre | `PASS` | Nine platform families and 99 indexed Russian articles create a real resilience layer beyond the native app. |
| Technical support | `PARTIAL` | The authenticated handoff opens, but the tokenized web route increases domain-verification risk and no message was sent. Public reviews show support capacity is the main operational weak point. |
| Logout / deletion discovery | `PASS` | Logout is visible in profile overflow; deletion is discoverable under More and, per the 19 July Play changelog, now adds separate confirmation. Destructive actions were not executed. |

Visual system strengths:

- consistent near-black/navy shell, soft blue environmental glow and one bright action colour across auth, home, selector, paywall and settings;
- large touch targets, strong title/body hierarchy and unusually good plain-language explanations for censorship protocols;
- location quality bars and the highlighted recommended plan communicate priority without adding a tutorial;
- the home avoids printing the user's current IP, unlike riskier competitor dashboards.

Visual/product weaknesses:

- the auth and home screens leave enormous unused vertical areas, so the product feels sparse rather than premium on a tall phone;
- “Skip” is a semantic dark pattern even though it does not monetize anything;
- grey secondary text and thin borders are close to the contrast floor on several cards;
- the paywall's polished hierarchy amplifies, rather than hides, its broken arithmetic;
- settings mix friendly outcome copy with an exhaustive system-app inventory; the latter needs filters for User apps / System apps / Selected;
- status, legal, help, account and downloads span too many lookalike domains, weakening the otherwise disciplined visual identity.

## What POKROV Should Borrow

Borrow the operating model, not the misleading parts:

1. Ship named anti-blocking modes with one-line “use this when…” guidance and Automatic as the safe default.
2. Make location order itself useful: quality/proximity recommendation, search, explicit city and a transparent sort control.
3. Treat the help centre, third-party clients, router tooling and tested fallback apps as part of the product's availability architecture.
4. Publish a component status page, incident-specific playbooks and automatic compensation when a broad outage is confirmed.
5. Maintain native/store releases, browser extensions and configuration fallbacks as separate release lanes, with user-problem changelogs like the 19 July Android release.
6. Keep the dark/blue system and large controls, but use the empty space for trial state, protocol recommendation, current incident messaging or a concise benefit proof—not decoration.

Do not copy the fake Skip, contradictory price math, Windows “download” implication without a Windows client, selectively positive review wall, opaque domain sprawl or refund/unlimited claims that the detailed contract narrows.

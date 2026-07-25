# Lagom VPN — Mobile App Competitor Profile

**Snapshot date:** 2026-07-22<br>
**Android package:** `com.lagomproductsllc.lagomvpn`<br>
**Installed version:** `0.21-mobile` (`versionCode 134`)<br>
**Install source:** Google Play<br>
**Status:** `DEEP_PASS_COMPLETE_WITH_BLOCKERS` — all reachable app, support, store, creative, public-web, legal, release and redacted static surfaces were covered; home/paywall/tunnel remain blocked by failed account creation

## At A Glance

| Field | Observed value |
| --- | --- |
| Product | LagomVPN |
| Publisher shown publicly | LAGOM PRODUCTS, LLC / Lagom Products |
| Public address | 3A Moskovyan St., Yerevan, Armenia |
| Play scale | 5M+ downloads; 4.8 from 116,305 reviews in the installed Play client |
| Main acquisition promise | Free renewable allowance, no ads, cross-device account, VLESS/V2Ray, automatic routing |
| Main conversion boundary | Mandatory profile wall before the product home; PRO unlocks unlimited devices, whitelist bypass and ad-free YouTube routes |
| Strongest product idea | Automatic bypass rules for local banking/state apps plus cross-platform setup through a Telegram bot |
| Largest observed defect | Both email OTP registration and authorized Google sign-in returned to the auth wall; no usable account/home/tunnel was reached |

## Executive Read

Lagom is commercially sharp and operationally sloppy. Its strongest package is not the generic one-tap VPN but a Russian-user story: automatic routes that leave government/banking apps alone, a Russia route for users abroad, five free GB each month, no in-app ads, and one profile across devices. The seven-store-image sequence communicates those benefits with unusual clarity.

The audited build then breaks that promise at the front door. An optional Quick Settings tile behaved like a rendering prerequisite; email registration rejected a fresh code; Google consent completed but the backend looked only for an existing user; and the whole product stayed behind that identity wall. Its privacy, Play Data Safety and “no trackers” statements materially contradict one another. The legal pages contain what appears to be unrelated UK company boilerplate, while the site root currently redirects to the privacy policy instead of a product home.

## Runtime Journey And Health

| Step | Flow | Health | Observed result |
| --- | --- | --- | --- |
| 1 | Quick Settings request | **BROKEN** | Denial left the activity in repeated draw cancellation/black screen; acceptance restored rendering. |
| 2 | Onboarding | Mixed | Clear benefit copy, but acceptance text does not expose privacy/offer as distinct accessible links. |
| 3 | Notification ask | PASS | Soft ask allowed “Later”; no Android permission was granted. |
| 4 | Account explanation | Mixed | Explains email/Telegram use but omits Google, although Google requests profile identity. |
| 5 | Email registration | **BLOCKED / BROKEN** | Fresh owner-authorized OTP rejected twice as expired/missing; resend produced no new code in the observation window. |
| 6 | Google registration | **BLOCKED / BROKEN** | Native consent completed, then app returned to auth wall; sanitized log showed a user-by-email 404. |
| 7 | Telegram login handoff | PASS to destination | Opens the official login bot with a personalized start parameter; destination captured, parameter quarantined, bot not started. |
| 8 | Pre-auth support | Strong | FAQ, email, Telegram and embedded operator chat available before account creation. |
| 9 | Product home/paywall/tunnel | **BLOCKED BY AUTH BACKEND** | No claims made about an unreachable live state. No VPN consent or tunnel was started. |
| 10 | Teardown | PASS | Added tile removed; Lagom, Chrome and Play stopped; no process and no `tun0`; launcher restored. |

## Durable Runtime Evidence

Only Lagom was active during this pass and `tun0` was absent. No subscription, purchase, review, support message or Telegram bot start was performed.

### First launch and onboarding

Lagom asks Android to add its Quick Settings tile immediately, before its own first screen is usable. Rejecting the request left the app in a repeated draw-cancellation/black-screen state; relaunching raised the same request. Accepting the reversible tile request allowed the UI to render. This is a severe onboarding dependency: an optional convenience affordance behaves like a hidden prerequisite.

The rendered onboarding makes four promises:

- “Безопасность — в один клик” and general data-safety positioning;
- PRO for an unlimited number of family/friend devices;
- PRO routes for YouTube without ads;
- automatic VPN bypass where it is undesirable, with government and banking apps named as examples.

Continuing is presented as acceptance of the privacy policy and offer, but the legal names were not exposed as distinct accessible links in the observed UI. A separate soft notification screen offered “Allow” or “Later”; “Later” worked and no Android notification permission was granted.

Evidence: [tile request](raw/lagom-vpn/2026-07-22/screenshots/01-isolated-launch.png), [rendered onboarding](raw/lagom-vpn/2026-07-22/screenshots/06-after-tile-added.png), [UI trees](raw/lagom-vpn/2026-07-22/ui/).

### Mandatory identity wall

The next screen is not a free-connect home but “Войдите или зарегистрируйтесь”, backed by a “more than one million users” claim. It offers Google, Telegram and email, plus pre-auth support and “Зачем нужен профиль?”.

The profile explainer says email and Telegram are used only for the profile, preserving a subscription and restoring it after device/app deletion; it claims the data is not shared with third parties. Google is offered on the preceding screen but is omitted from this explanation. That omission matters because the Google consent surface explicitly requests name, email and profile picture.

Evidence: [auth wall](raw/lagom-vpn/2026-07-22/screenshots/08-after-notification-later.png), [profile explainer](raw/lagom-vpn/2026-07-22/screenshots/09-why-profile.png).

### Registration health

| Route | Health | Observed result |
| --- | --- | --- |
| Email OTP | **BLOCKED / BROKEN** | A current code delivered to the owner-authorized inbox was rejected twice as expired or missing. Resend produced no new message in the observation window. Sensitive email/code evidence remains outside the worktree. |
| Google | **BLOCKED / BROKEN** | The authorized matching Google account completed the native chooser/consent surface, then silently returned to the auth wall. Sanitized runtime output reported an HTTP 404 for a user-by-email lookup, consistent with login-only behavior despite the “sign in or register” label. |
| Telegram | PASS to destination | Opened the official `LagomVPN_bot` handoff with a personalized start parameter. The parameter/raw capture was quarantined; the bot was not started or messaged. |

Because every tested creation route failed before the product home, locations, paywall, settings and controlled tunnel behavior are not yet attributable to this build. They will remain explicit blockers unless a safe public/static surface substantiates them.

### Pre-auth help and FAQ

Support is unusually complete before authentication:

- an email action;
- a direct embedded operator chat;
- a Telegram bot route;
- seven expandable FAQ items.

The embedded chat loaded and showed a human-style greeting plus input field. No message was sent. The email action had no handler in this LDPlayer image and returned to the launcher; this is an emulator-without-mail-client result, not proof of a universal product defect.

The seven FAQ answers establish these product rules:

1. Lagom uses VLESS with TLS and makes an absolute claim that neither the team nor third parties can access user data.
2. Free supports one device; PRO claims unlimited devices.
3. Other platforms are configured through the official Telegram bot, which supplies a key and instructions.
4. App/site bypass (“white list”) is PRO-only.
5. Ad-free YouTube is PRO-only and works through locations where YouTube ads are officially disabled.
6. If the VPN does not work, the prescribed repair path is the support bot; no self-diagnostic workflow is documented here.
7. Subscription cancellation is routed through the Telegram bot.

Evidence: [support hub](raw/lagom-vpn/2026-07-22/screenshots/10-support-entry.png), [embedded chat](raw/lagom-vpn/2026-07-22/screenshots/12-support-chat.png), [FAQ captures](raw/lagom-vpn/2026-07-22/ui/).

## Google Play, Creatives And Recommendations

The installed [Google Play page](https://play.google.com/store/apps/details?id=com.lagomproductsllc.lagomvpn) showed:

- 4.8 from 116,305 reviews, 5M+ downloads, age 3+ and a #3 free-Tools tag;
- update dated 2026-07-14 for faster/more stable ping measurement, bug fixes and cleanup;
- 91% five-star, 4% four-star and 2% one-star in the visible histogram;
- a five-GB monthly free limit corroborated by visible reviews and the official iOS listing;
- complaints about price, account switching to renew free traffic, missing Russian-card payment and occasional “connected but no internet”/repeat-login behavior.

The description claims VLESS/V2Ray, AES-256, Kill Switch, Split Tunneling, automatic route switching, a renewable free limit, no ads, no trackers/activity logs and one account across devices. Kill Switch and Split Tunneling could not be verified because the auth backend blocked the home. Static manifest evidence confirms a V2Ray VPN service with Android Always-On declaration, but a declared component is not proof that the advertised controls work.

The seven creatives use one high-saturation purple system, condensed all-caps headlines, large 3D objects and selective app logos. Their sequence is:

1. access to popular services “in one click”; “free without ads in 2026”, with tiny copy saying ads may appear in the future;
2. free/fast/no-ads plus a visible server list and auto-connect;
3. automatic switching around government, banking and local service apps;
4. one VPN across phone/tablet/desktop/TV-style layouts;
5. broad “data is safe” promise;
6. access to Russian services abroad through a Russia location;
7. Russian-language support, illustrated with parody celebrity names.

The design is coherent and legible, but it leans on third-party trademarks/logos and absolute security language. Representative evidence: [creative 1](raw/lagom-vpn/2026-07-22/store-creatives/gallery-1.png), [automatic routing](raw/lagom-vpn/2026-07-22/store-creatives/gallery-3.png), [multi-device](raw/lagom-vpn/2026-07-22/store-creatives/gallery-4.png), [all seven files](raw/lagom-vpn/2026-07-22/store-creatives/).

The live Play recommendation rail was algorithmic store merchandising, not an in-app endorsement. “For you” showed DuckDuckGo, VPN Наружу, TikTok and VPN Proxy Speed/Super VPN. “Similar apps” showed Windscribe, Banki.ru, Yandex Music and DuckDuckGo. VPN Наружу is part of this audit’s added queue.

## Pricing, Renewal And Cancellation

The [current public offer](https://lagomvpn.com/oferta) states:

| Package | Price | Effective monthly |
| --- | ---: | ---: |
| 3-day trial | 10 RUB | Auto-renews to monthly unless cancelled |
| 1 month | 299 RUB | 299 RUB |
| 3 months | 855 RUB | 285 RUB |
| 12 months | 2,868 RUB | 239 RUB |

- The paid trial is one-time and auto-renews at 299 RUB unless cancelled before it ends.
- Monthly plans receive a full refund only within seven calendar days.
- Multi-month refunds deduct used full months at the package’s monthly rate.
- “Unlimited” is subject to unspecified fair-use thresholds; speed may be limited or access suspended.
- Detected P2P use can trigger escalating temporary blocks: 5 minutes, 30 minutes, 1 hour, 8 hours, then 24 hours.
- The offer says cancellation is available on site or in the Telegram bot; the in-app FAQ only directs the user to the bot.

No purchase or trial was initiated. The paywall presentation and actual available payment methods remain blocked by auth. Public reviews indicate Russian-card payment was not available in at least one current Play flow.

## Privacy And Data-Safety Contradictions

The Play Data Safety summary simultaneously states that the app may share app activity, app information/performance and device or other identifiers, that “data is not collected”, that data is encrypted in transit and that the app offers no deletion-request mechanism.

The [privacy policy](https://lagomvpn.com/policy), effective 2026-04-01, says Lagom may process:

- a temporary connection IP, device type/model, OS/version and language;
- app interaction, session date/duration, diagnostics and error reports;
- advertising identifiers such as IDFA/GAID and data from third-party SDKs;
- email if voluntarily supplied;
- analytics, fraud prevention, marketing and personalized advertising;
- Meta/Facebook Ads, mobile analytics/attribution SDKs, cookies/pixel-like technologies and international transfers to providers.

It says browsing history and traffic contents are not stored, but gives no concrete retention period. It grants deletion/objection/portability rights, directly conflicting with Play’s “no way to request deletion”. Its controller identification is only a service name and contact email; the company appears only in the offer.

Runtime/static presence includes Firebase Analytics, Remote Config, Crashlytics, Sessions and Messaging; Google Measurement; AppMetrica; Facebook SDK; Sentry; Crowdin; Yandex Auth; VK install referrer; Android Billing and the embedded helpdesk. SDK presence alone does not prove every possible transmission, but the policy itself expressly authorizes analytics, advertising IDs, attribution and personalized marketing. The unqualified “no trackers” store copy is therefore untenable.

## Company, Network And Document Integrity

The offer identifies **LAGOM PRODUCTS LLC**, 3A Moskovyan St., Yerevan 0001, Armenia. Play shows the same name/address and phone. Public LEI data lists the Armenian entity as active, created 2024-05-14, with registration-authority entity ID `273.110.1387755`; RIPE records associate the same name/address and ID with `AS199180 / LAGOM-NET`, assigned in April 2026. The offer instead prints `54751771` as “Registration number”; this may be a different local identifier, but the document does not explain it.

Both policy and offer append unrelated-looking UK Companies House-style text for a 2009 Gloucestershire “physical well-being / other service activities” company. No UK company name ties that block to Lagom. Treat this as a serious publication-integrity defect, not Lagom’s corporate identity.

The site root currently redirects to `/policy`, so Lagom has no working public product home at the expected URL in this snapshot. Every page also renders the visitor’s current public IP as a fear/conversion banner. Raw site captures were quarantined because of that sensitive value and are intentionally not linked from the repository.

## Release Pattern And Distribution

- Official Play shows Android `0.21-mobile` updated 2026-07-14; the installed build matches version/code 134.
- Public Android package archives (non-authoritative history) show `0.8` in January, `0.13` and `0.14` in February, `0.16` and `0.17` in April, `0.20` in late June and `0.21` in July. This suggests small releases every two to six weeks rather than quarterly drops.
- The [official iOS listing](https://apps.apple.com/app/id6670336253) exposes `0.5.0` on 2025-12-10 and `0.5.1` on 2026-02-04. The later update introduced the current login screen and interface cleanup; iOS shipping appears much slower than Android in the visible history.
- Play is the installed Android source. Other-platform setup is pushed through the Telegram bot, which supplies keys/instructions rather than distinct public download pages in the app FAQ.

## Redacted Static Package Findings

The Play install contains a 77.4 MB base, 13.0 MB arm64 split and small density split (about 90.5 MB total observed). It is non-debuggable, min SDK 26 and target SDK 37.

High-signal manifest items:

- `V2RayVpnService` with `BIND_VPN_SERVICE` and Always-On support declaration;
- `QSTileService`, explaining the first-launch tile request;
- billing, boot, notification, camera, biometric/fingerprint, network/Wi-Fi and wake-lock permissions;
- Advertising ID plus AdServices attribution, ad-ID, Topics and Custom Audience permissions;
- Firebase messaging/measurement, AppMetrica, Facebook, Sentry, Yandex auth and VK referrer components.

The pulled APKs, hashes and any raw configuration remain outside the worktree. Only redacted component-level notes are retained: [static summary](raw/lagom-vpn/2026-07-22/static-summary.md).

The Play Data Safety summary is internally difficult to reconcile: the public surface says the app may share app activity, app information/performance and device or other identifiers, while also displaying “No data collected”. The [official privacy policy](https://lagomvpn.com/policy), effective 2026-04-01, says Lagom processes an IP address temporarily for connection plus device model/type, OS/version, language, interaction/session duration and diagnostics/error reports. Those disclosures are materially narrower than browsing-history logging, but they contradict an unqualified “no trackers/no data collected” reading.

Runtime/static presence of Firebase Measurement/Remote Config, Facebook SDK initialization, Android AdServices measurement hooks and Crowdin has been observed. SDK presence does not prove a particular data transmission, but it makes absolute “no trackers” copy unsafe without a narrower definition and network-level evidence.

## Product Lessons For POKROV

### Copy the useful mechanics

- Put automatic exclusions for banking/state apps on the value proposition, not only in settings.
- Make cross-platform setup a guided handoff with keys and platform-specific instructions.
- Keep FAQ and a real support channel available before account creation.
- Explain why an account is needed at the point of friction.

### Do not copy the failure modes

- Never make an optional Quick Settings tile a de facto render prerequisite.
- Do not label a route “sign in or register” when the backend only looks up an existing user.
- Do not make subscription cancellation depend solely on a Telegram bot.
- Avoid absolute privacy copy that conflicts with store declarations, policy language or embedded measurement SDKs.
- Do not hide the whole product behind identity before the user can inspect servers, limits and price.
- Never claim “no trackers/data collected” when the policy and platform declarations authorize advertising/analytics identifiers.
- Do not publish unreviewed legal pages: unrelated boilerplate can destroy trust faster than having a shorter document.
- If showing the visitor’s IP for conversion, mask it by default and never let it leak into support/screenshot workflows.

## Explicit Blockers / Not Claimed

- No reachable home, server catalog, live limit counter, paywall UI, payment selector, settings or tunnel because all attempted account-creation routes failed.
- No purchase, paid trial, review, helpful vote, support message or Telegram bot start.
- No government-registry portal record was captured directly; active entity status is supported by public LEI data and RIPE corroboration, not presented as a fresh Armenian registry extract.
- No claim that every declared SDK transmitted data during the short session.

# Kakadu — Mobile App Competitor Profile

**Snapshot date:** 2026-07-22<br>
**Status:** `DEEP PASS COMPLETE WITH BLOCKERS` — isolated logged-out UX, both authentication routes, public web/store/Telegram/legal surfaces, release cadence, growth system and redacted Android architecture captured; signed-in product and connection remain blocked by backend authentication<br>
**Android package:** `com.matrena.vpn`<br>
**Installed version:** 2.4.6<br>
**Install source:** Google Play

Evidence root: [`raw/kakadu/2026-07-22/`](raw/kakadu/2026-07-22/)

The earlier `01-launch` artifact remains provenance-only. Accepted current-session evidence begins with `02-isolated-launch`.

## Isolated Entry Screen

Kakadu cold-starts directly into an authentication wall rather than a value proposition, permission request or free server list. The black Compose screen has a centered Kakadu mark and only two paths:

- dominant white **Продолжить с Google**;
- outlined **Войти по коду**.

The visual system is disciplined: black background, bright mascot/logo, large rounded controls, very little copy and a single dominant action. The price is context. A new user is asked to share a Google identity before seeing countries, plan value, trial terms, family mechanics or even a product preview.

The footer says registration automatically accepts the user agreement. The agreement phrase appears link-styled, but the sentence is low-contrast, touches the bottom safe area and is not exposed as a separately clickable/accessibility node in the UI tree. Consent is bundled with account creation instead of being a clear pre-auth document step.

Evidence: [isolated authentication wall](raw/kakadu/2026-07-22/screenshots/02-isolated-launch.png).

## Cross-Device Code Login

**Войти по коду** opens a centered sheet titled **Вход по QR или коду**. It tells the user to scan or enter a code from an already authorized Kakadu account and contains:

- a large QR area with retry affordance;
- a countdown observed at `0:00`;
- an empty `-----` code placeholder;
- copy action;
- **Закрыть**.

This is a good cross-device concept: it avoids typing credentials on TV/shared devices and can turn an existing trusted phone into the authenticator. In the observed run, the request never produced either a QR payload or a code. The sheet remained at an expired/empty state without a useful diagnosis.

Evidence: [code-login failed/expired state](raw/kakadu/2026-07-22/screenshots/03-code-login.png). No code or QR payload was generated, copied or retained.

## Google Registration Failure

The owner explicitly authorized using the existing Google account for registration. The audit selected it twice. Account-bearing chooser screenshots and UI trees were quarantined outside the repository; no name, email, photo or account identifier is retained here.

Both attempts silently returned to the login wall. Sanitized logs recorded `backendGoogleAuth failed`; the second attempt ended in a ten-second socket timeout against a redacted direct HTTPS endpoint. A transient Russian error appeared on the first attempt, but the screen did not keep an actionable failure message, status page, retry explanation or fallback support route.

There is no evidence that a Kakadu backend account was created. With code login also unavailable, every signed-in screen and live connection is `BLOCKED_BY_BACKEND`. Two attempts were enough; repeated authentication was deliberately stopped.

This is the largest funnel defect in the observed build: a beautifully reduced auth wall has no resilience when its one primary backend path fails.

## Product Depth Hidden Behind Authentication

The shipped Android bundle shows a much deeper product than the first screen reveals:

- Home, Plans and Profile/Settings top-level areas;
- smart connect, favorites, premium servers and country/city search;
- family creation, join, invite link/QR, remove and leave flows with separate member accounts;
- device and web-session management, session IP/login time and terminate-all;
- profile name/photo/ID, promo codes, gifts and account deletion;
- Basic/Plus/Pro subscriptions, restore/manage actions and update prompts;
- both Play/Apple subscription management and a Russian-bank-card lifecycle;
- QR scanning, appearance/language, configuration reset, background/battery guidance;
- Telegram/WhatsApp support and hidden debug/support-log routes;
- Android Always-on VPN and Quick Settings tile support.

The static map does not prove every feature is remotely enabled, but it explains the competitive shape: Kakadu is not merely a power button. It is an account/family/device platform with recovery, promotions and multiple payment rails.

Detailed evidence: [static Android package notes](raw/kakadu/2026-07-22/logs/static-package-notes.md).

## Technical Architecture and Resilience

The client embeds a sing-box/Sagernet-derived engine. Its native library exposes capabilities for WireGuard, Shadowsocks, VLESS, VMess, Trojan, Hysteria, TUIC, QUIC, Reality, ECH, TUN routing and sniffing. These are engine capabilities, not proof that Kakadu sells or activates every transport.

The build also contains rotating cover domains and direct-IP HTTPS fallbacks. Exact endpoints are excluded from evidence. This gives the service more control-plane resilience under blocking, but the failed Google authentication demonstrates the limit: transport redundancy is useless if the active auth backend is unavailable and the client does not surface a working fallback.

No obvious standalone Sentry/Crashlytics/AppsFlyer/Adjust SDK was found. That does not validate a no-telemetry promise; first-party account, session, payment and control-plane traffic remains.

## Website and Platform Story

Kakadu maintains a broad distribution footprint across Android, iOS/iPadOS, Windows, Apple-silicon macOS, Android TV, Chromium and Debian Linux. Its controlled public surface is split across multiple country-code/mirror domains, a Telegram news channel, support account and purchase/account bot.

The site claims 2,000+ servers, named modern cryptographic primitives, no logs/no tracking and a no-card trial. Chrome claims 3,000+ servers in 60+ countries. The site advertises up to 35 family members, while Play/Apple/Chrome say 20 family members and 10 simultaneous devices. These are not harmless copy variations: they change the purchased entitlement and infrastructure scale.

Detailed public-surface audit: [website, stores, Telegram and legal notes](raw/kakadu/2026-07-22/documents/website-store-and-legal-notes.md).

## Pricing and Payment Model

Published Russian web terms list:

| Plan | 1 month | 6 months | 12 months |
| --- | ---: | ---: | ---: |
| Basic | 499 ₽ | 2,249 ₽ | 3,999 ₽ |
| Plus | 749 ₽ | 3,349 ₽ | 5,999 ₽ |
| Pro | 1,249 ₽ | 5,599 ₽ | 9,999 ₽ |

The current Android resources contain Russian-card add/save/default/delete operations and bank-subscription cancel/resume/retry states. Yet the terms and privacy policy say payments are exclusively Apple/Google in-app purchases. This means either live direct billing is undisclosed or obsolete payment code is still shipped; both require cleanup.

The App Store listing promises a 45-day guarantee. Kakadu's refund policy promises 10 calendar days, then a partial time-based refund and a three-business-day target. The user cannot know which promise governs without platform-specific contract copy.

## Release Machine

The iOS release history is unusually active: ten releases from 19 March through 15 June 2026, including four releases in the first half of June. Recent notes are generic bug fixes, while older notes identify code login, smart connect, iPad, city servers, languages, redesign, mascot and family sharing.

Google Play reported an update on 14 June 2026. The Chrome extension moved to 1.1.2 on 11 June. This suggests coordinated cross-platform shipping around the same product cycle, although version schemes differ and no public release ledger reconciles platform parity.

Kakadu is fast at shipping, weak at explaining what shipped. POKROV should copy the cadence and cross-platform coordination, then publish human changelogs tied to feature flags and platform parity.

## Telegram Growth Loop

The public `@vpn_kakadu` channel showed roughly 29K subscribers. Its core acquisition loop is aggressive and coherent:

1. publish timely Russian blocking/connectivity news;
2. frame Kakadu as working during the incident;
3. send the reader to the bot immediately;
4. reinforce with short discounts, new bypass locations and referral rewards;
5. reward invited friends with subscription days and offer a partner route.

Recent channel material launched a special France allow-list/LTE/Wi-Fi location with a discount and instructed current customers to renew/update the subscription for it to appear. The channel also directly recommended the third-party **Happ** client and warned users about fakes in search results.

This is the “наглость” that makes Kakadu feel alive: it turns external events, product operations, promotion and distribution into one continuous feed. The transferable part is the fast status/release narrative and transparent referral value. Fear-heavy news framing, opaque urgency and infrastructure access tied to renewal are trust risks.

## Store Scale, Reviews, and Recommendation Graph

Google Play showed 1M+ installs and roughly 5.3K–5.6K reviews, with a rating around 4.0/4.1 depending on the view. Positive reviews emphasize speed, stability and no advertising; negative clusters mention price, freezes, long authentication failures and weak operation on allow-list networks.

Apple showed about 1.3K ratings at 4.5. User comments include good gaming latency and Iranian popularity, along with payment difficulty, location-specific failures and a broken widget.

Algorithmic acquisition neighbors:

- Play: Secure VPN, AdGuard, Thunder VPN, PandaVPN, DNS Changer, Speedify;
- Apple: iNinja, Дед Proxy, TipTop, FKey, Buddy VPN, Super VPN Fly, avoVPN, BOOST VPN, Vanya, Bear VPN;
- Kakadu's own Telegram ecosystem recommendation: Happ.

Store shelves are not customer endorsements, but they reveal the keywords, screenshots and audiences against which Kakadu competes.

## Ownership, Privacy, and Trust Gaps

Legal documents and Apple name **KAKADU SECURE TECHNOLOGIES - FZCO** in Dubai/IFZA. Google Play names **Rafaelian Aik, IE** in Armenia. Apple labels the UAE seller a trader, while Chrome labels the same publisher a non-trader. Current authoritative registry status for the UAE licence and exact Armenian individual-enterprise record could not be refreshed through accessible public registries, so both checks remain `BLOCKED_BY_ACCESS`.

The product has a deeper disclosure problem than entity fragmentation:

- Play says no data is collected or shared;
- Apple lists phone number, photos/videos and device ID;
- Chrome lists identity, authentication and location information;
- the privacy policy says no IP, timestamps, session duration, email by default or phone number;
- Google OAuth offers name, email and profile photo;
- the app exposes session IP, login time, profile ID, device sessions and support logs.

Kakadu needs one field-level data map per purpose, processor, platform and retention period. “No logs” may be defensible for browsing history, but the current copy improperly collapses account/session/payment metadata into the same blanket denial.

## What POKROV Should Copy

- Cross-device QR/code login for TV and shared-device onboarding, with a real expiry/retry explanation.
- Family as a first-class product object: separate accounts, links/QR, member control and clear device/session management.
- Smart-connect and favorite/premium location merchandising instead of a flat country list.
- A live operational news channel that joins incidents, status, new locations and release notes.
- Referral rewards expressed in immediately understandable subscription days.
- Coordinated weekly/biweekly cross-platform shipping.
- Always-on VPN, Quick Settings, configuration reset and battery/background recovery.
- A signed in-app directory of official sites, mirrors, bots, support contacts and alternative clients.

## What POKROV Should Not Copy

- Auth-first wall with no product preview and no viable degraded/offline state.
- Bundled low-contrast legal consent.
- Silent return to login after backend failure.
- Contradictory family/server/refund claims across surfaces.
- “No data” language that ignores identity, device, session, IP and payment metadata.
- Direct-card billing hidden from published terms.
- Fear-heavy news marketing, permanent urgency or renewal gating for new infrastructure.
- Multiple official domains/entities without a public responsibility and authenticity map.

## Current Flow Health

| Flow | Health | Evidence / blocker |
| --- | --- | --- |
| Cold launch → authentication wall | **PASS** | Clean isolated start; legal consent is bundled and poorly exposed |
| Login wall → QR/code | **FAIL IN OBSERVED SESSION** | Timer at `0:00`; no QR or code produced; no useful diagnosis |
| Login wall → Google → Kakadu account | **BLOCKED_BY_BACKEND** | Two authorized attempts; backend failure/timeout; silent return to auth wall |
| Signed-in home / locations / plans / profile | **STATICALLY CONFIRMED, MANUAL BLOCKED** | Routes and copy exist in current bundle; auth unavailable |
| Family / referral / promo / device sessions | **STATICALLY CONFIRMED, MANUAL BLOCKED** | Rich feature surface in current bundle; auth unavailable |
| Subscription / restore / direct-card management | **STATICALLY CONFIRMED, MANUAL BLOCKED** | Store and bank-card flows present; no purchase/account mutation performed |
| Connect / disconnect / Always-on VPN | **BLOCKED_BY_BACKEND** | No account/configuration; no tunnel started |
| Website/store/legal destinations | **PASS TO PUBLIC SURFACES** | Platforms, prices, releases and contradictions mapped; no transaction executed |
| Telegram channel / bot / support | **PASS TO PUBLIC LANDINGS** | News/growth/recommendations mapped; bot not started and no message sent |
| Current legal-entity status | **BLOCKED_BY_ACCESS** | Store/legal identities captured; authoritative live UAE/Armenian registry status unresolved |

Final teardown: Kakadu, Chrome and Google Play were force-stopped. The Kakadu process was absent and `tun0` did not exist before moving to the next competitor. No purchase, tunnel, support message, Telegram bot start, rating/review or successful Kakadu account creation occurred.

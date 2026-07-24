# Kakadu — Website, Store, Telegram, and Legal Notes

Captured: 2026-07-22<br>
Scope: public, unauthenticated surfaces only. No checkout, purchase, support message, Telegram bot start, review, rating, referral activation, or account mutation was performed.

## Controlled public surface

The product does not have one obvious canonical host:

- Google Play links `https://kakadu.ae`, which redirects to `https://kakadu.qa/en`;
- the support account and Russian public pages use `https://kakadu.net.ru/ru`;
- the Chrome Web Store points to a matching policy/support surface under `https://kakadu.ph`;
- public Telegram distribution uses the news channel `@vpn_kakadu`, support account `@kakaduvpn_support`, and purchase/account bot `@KakaduVpsbot`.

The web mirrors use the same Nuxt product and substantially the same legal copy, but Kakadu does not publish a signed directory explaining which hosts, bots, support accounts, and payment operators are official. That is a continuity advantage and a phishing/impersonation risk at the same time.

## Website positioning and platform footprint

The public product site advertises:

- iOS/iPadOS 16+, Android 8+, Windows 10 x64+, macOS on Apple silicon, Android TV 10+, Chromium browsers, and Debian-family Linux;
- a no-card trial;
- ChaCha20, Curve25519 and Noise by name;
- account-level device/session management;
- no activity logs and no tracking;
- 2,000+ servers worldwide;
- up to **35 family members** on one public site page.

The Russian copy occasionally calls the service a **VPS**, despite the product being sold as a managed VPN. Platform/store claims are inconsistent: Google Play, Apple and Chrome generally say **20 family members** and **10 simultaneous devices**, while the Chrome listing raises the infrastructure claim to **3,000+ servers in 60+ countries**.

None of the server-count, location, throughput, protocol-deployment, no-log, or family-capacity claims was independently verified.

## Google Play

Official listing: <https://play.google.com/store/apps/details?id=com.matrena.vpn>

- Title: **Kakadu VPN: One Family**
- Store brand: **Sharashkina-Kontora**
- Legal developer displayed by Play: **Rafaelian Aik, IE**, Armenia
- Scale: 1M+ installs
- Public rating observed around 4.0 overall / 4.1 on phone, with roughly 5.3K–5.6K reviews depending on storefront rendering
- Updated: 14 June 2026
- Monetization: in-app purchases
- Changelog: generic bug-fix wording

The description promises 20 family members, 10 devices, a proprietary protocol, no logs, no ads, and a free trial. Data Safety says the app neither collects nor shares data, encrypts data in transit, and accepts deletion requests.

Selected current reviews praise stable speed and the absence of advertising. Recurring complaints mention price, freezes, difficulty with Russian allow-list networks, authentication failing for an extended period, and suspicion that reviews are inflated. These are user reports, not independently verified facts.

Play's **Similar apps** shelf included Secure VPN, AdGuard, Thunder VPN, PandaVPN, DNS Changer and Speedify. This is an algorithmic acquisition neighborhood, not a Kakadu endorsement.

## Apple App Store and release cadence

Official listing: <https://apps.apple.com/us/app/kakadu-vpn-one-family/id6451071772>

- Seller: **KAKADU SECURE TECHNOLOGIES - FZCO**
- Rating observed: 4.5 from about 1.3K ratings
- Current version: 2.5.13, released 15 June 2026
- Apple labels the seller as an EU trader and exposes a D-U-N-S identifier; exact private contact/address details are intentionally not reproduced here.

Observed 2026 iOS releases:

| Version | Date |
| --- | --- |
| 2.5.13 | 15 Jun 2026 |
| 2.5.12 | 11 Jun 2026 |
| 2.5.11 | 8 Jun 2026 |
| 2.5.10 | 3 Jun 2026 |
| 2.5.9 | 25 May 2026 |
| 2.5.8 | 27 Apr 2026 |
| 2.5.7 | 9 Apr 2026 |
| 2.5.6 | 1 Apr 2026 |
| 2.5.5 | 20 Mar 2026 |
| 2.5.4 | 19 Mar 2026 |

Most recent notes are generic maintenance copy. Earlier notes are more informative: 2.3.0 introduced code-based device login, a redesigned device flow and Arabic; 2.2.1 named smart connect; 2.2 added iPad support; 2.1.1 named additional languages and city-level servers; 2.1 described a redesign, mascot, family sharing and faster connection.

The cadence shows a tight weekly-to-monthly release machine in spring 2026, but generic notes hide most user-visible change.

The US listing exposed representative in-app purchase amounts across Basic, Plus and Pro tiers. Period mapping was not reliably visible in the public listing, so those amounts are not treated as a complete price table.

The App Store privacy label says phone number, photos/videos and device ID may be used for product personalization but are not linked to the user. The listing promises a **45-day money-back guarantee**, which conflicts with the public 10-day refund policy.

Apple's **You Might Also Like** shelf included iNinja, Дед Proxy, TipTop, FKey, Buddy VPN, Super VPN Fly, avoVPN, BOOST VPN, Vanya and Bear VPN. These are algorithmic recommendations; TipTop and Vanya are already in this emulator audit.

## Chrome Web Store

Official listing: <https://chromewebstore.google.com/detail/kakadu-vpn-one-family/damckmbkfehmaldekkdloohhpmbmjpdk>

- Version 1.1.2, updated 11 June 2026
- About 10K users, 96 ratings and 4.3 stars
- Package size around 4 MiB
- Claims smart traffic filtering, 3,000+ servers in 60+ countries, 20 family members and 10 devices
- Declares handling personally identifiable information, authentication information and location
- The same UAE company is labelled **Non-trader** by Chrome, while Apple labels it a trader

The Chrome privacy declarations contradict Play's blanket “no data collected” label and show that Kakadu has not normalized its disclosure model across platforms.

## Public tariffs and billing terms

Terms page: <https://kakadu.net.ru/ru/about/terms-of-use>

Published Russian tariff table:

| Plan | 1 month | 6 months | 12 months |
| --- | ---: | ---: | ---: |
| Basic | 499 ₽ | 2,249 ₽ | 3,999 ₽ |
| Plus | 749 ₽ | 3,349 ₽ | 5,999 ₽ |
| Pro | 1,249 ₽ | 5,599 ₽ | 9,999 ₽ |

The terms describe automatic renewal and say subscriptions and cancellation are handled only through Apple or Google stores. Static Android UI in the installed build contains a separate Russian-bank-card flow: new and saved cards, default-card selection, card deletion, and bank-subscription cancellation/resumption. The public terms and privacy policy therefore do not describe every payment route present in the current client.

## Privacy policy

Privacy page: <https://kakadu.net.ru/ru/about/privacy-policy>

The document is dated 18 May 2025 and names **KAKADU SECURE TECHNOLOGIES - FZCO**, Dubai/IFZA, trade licence 67380, as controller/developer. It says Kakadu does not collect phone numbers, email unless voluntarily supplied, IP addresses, connection timestamps, session duration, traffic history, DNS requests, bandwidth or VPN activity logs. It allows transaction identifiers, support messages, optional anonymous diagnostics, minimal cookies and unspecified trusted email/hosting providers. Retention is described only as automatic deletion without a field-level schedule.

That disclosure is not compatible with the current product surface:

- Google OAuth explicitly offers Kakadu the account name, email and profile image;
- static UI provides a profile name/photo and profile ID;
- session management shows sign-in time and session IP address;
- the browser extension declares handling identity, authentication and location data;
- Apple's label lists phone number, photos/videos and device ID;
- Play claims no collection at all.

The absence of a major third-party analytics SDK in the Android bundle does not resolve these contradictions; first-party account, payment and session processing still requires a truthful data map.

## Refund policy

Refund page: <https://kakadu.net.ru/ru/about/refund-policy>

The document is dated 18 May 2025 and promises:

- a full refund inside **10 calendar days**;
- a partial refund after used time outside that window;
- an advertised processing target of three business days;
- 24/7 support with a claimed reply within an hour;
- a final support decision under UAE law.

This conflicts directly with the App Store listing's **45-day** guarantee. Neither refund route was tested.

## Legal entity and responsibility chain

Public surfaces identify at least two operating identities:

1. **KAKADU SECURE TECHNOLOGIES - FZCO**, Dubai/IFZA, trade licence 67380, named by the legal documents and Apple seller record.
2. **Rafaelian Aik, IE**, Armenia, named as the Google Play legal developer.

Apple's trader record and the legal documents corroborate that the UAE entity is being used publicly. No accessible authoritative IFZA registry result was found that independently refreshed licence 67380 for 22 July 2026. Current licence/good-standing status is therefore `BLOCKED_BY_ACCESS`.

The exact Armenian state-registry identity and current status of **Rafaelian Aik, IE** were not established from an authoritative public record in this pass. That check remains `BLOCKED_BY_ACCESS`; the Play identity is recorded as a store assertion, not silently treated as the contracting entity.

The terms invoke the law of the company's place of registration but do not clearly explain which seller handles each platform, which entity receives direct-card payments, or the exact dispute forum. Kakadu should publish a role map for publisher, seller, controller, payment operator and support operator.

## Telegram growth and distribution

Public channel: <https://t.me/s/vpn_kakadu>

The channel showed roughly 29K subscribers at capture time, with minor count differences across Telegram landing/crawl views. It uses topical Russian connectivity and blocking news as the hook, then pivots to Kakadu as the immediate solution. Recent posts achieve high reach relative to the subscriber count and repeatedly position the service as stable during restrictions.

Observed mechanics:

- a bot-based referral system rewards subscription days per friend and says active referrals can make use effectively free;
- a dedicated **Партнерам** route suggests a broader partner channel;
- short 24-hour discounts create urgency;
- new “allow-list bypass” locations are launched as product events;
- one launch instructed existing customers to renew/update the subscription for the new location to appear, turning infrastructure change into an upsell/engagement action;
- the channel recommends the third-party **Happ** client through a direct App Store link and warns that search results contain fakes.

The strongest growth lesson is the joined system: real restriction news → product proof/claim → immediate bot CTA → referral reward → rapid location launch. POKROV can copy the fast status communication, referral clarity, and signed ecosystem directory without copying fear-heavy claims, forced urgency, or renewal gating for infrastructure access.

## Claims and contract consistency matrix

| Subject | Public claims | Audit result |
| --- | --- | --- |
| Family size | Website: 35; stores/extensions: 20 | **CONTRADICTION** |
| Infrastructure | Website: 2,000+ servers; Chrome: 3,000+ / 60+ countries | **CONTRADICTION / UNVERIFIED** |
| Data collection | Play: none; Apple/Chrome: several categories; legal policy: nearly none | **MATERIAL CONTRADICTION** |
| Identity fields | OAuth/profile/session UI uses name, email, image, ID and session IP | **POLICY INCOMPLETE** |
| Payment rails | Legal pages: Apple/Google only; app: Russian bank-card management | **CONTRADICTION** |
| Refund window | App Store: 45 days; policy: 10 days | **CONTRADICTION** |
| Trader status | Apple: trader; Chrome: non-trader | **CONTRADICTION** |
| Seller/controller | UAE FZCO, Armenian Play developer, unspecified direct-card operator | **RESPONSIBILITY GAP** |

## Evidence boundary

- Store ratings, review counts and subscriber counts are volatile snapshots from 2026-07-22.
- No purchase, refund, support SLA, server count, speed, log behavior, referral reward, or allow-list bypass claim was independently verified.
- No public contact address, personal account value, raw token, payment identifier, or account/device identifier is retained in this worktree.

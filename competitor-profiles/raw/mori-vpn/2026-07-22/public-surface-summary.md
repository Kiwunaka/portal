# MORI VPN — current public surfaces

**Observed:** 2026-07-22
**Method:** read-only Chrome audit plus public Google Play/Telegram/Companies House evidence

## Google Play

- App: MORI VPN.
- Developer: QUARTETTO INTERNATIONAL LTD.
- Scale shown: 50K+ downloads, about 1.44K reviews.
- Current rating: 2.4/5.
- Phone-rating distribution shown: 368 five-star, 59 four-star, 94 three-star, 141 two-star and 749 one-star ratings.
- Last update: 2026-06-12.
- Release note: generic “large update” language covering server expansion, reliability, faster key activation, optimization and bug fixes.
- Data Safety declaration: no collection and no sharing.
- Support: `morivpn.com`, support email and the same privacy-policy page used by the site.
- Visible recent complaints: device slots remain consumed after reinstall/reactivation; paid access stops working while support delays; Windows/allowlist reliability complaints; refund/support friction.

Play’s recommendation shelf currently shows Vanilla, Безлимит, MEGA VPN, hide.me, Cure VPN and an unrelated learning application. This shelf is weak evidence of intentional competitor positioning.

## Store creative system

The gallery is a polished monochrome editorial set:

- black device renders on white;
- oversized geometric wordmark;
- short claim per frame;
- close-up product crops and chrome/shield motif;
- phone/tablet variants.

Messages shown: fast connection, Kill Switch, WireGuard, Zero Logs, one account across devices, QR connection, three devices and broad platform coverage. The creative system is materially stronger than the observed runtime stability.

## Website and CTA map

Main routes:

- `/` — hero, tariffs, competitor comparison, incident stories, onboarding and FAQ;
- `/downloads.html` — platform downloads and setup steps;
- `/documents/privacy-policy.html` — PDF wrapper;
- `/documents/consent.html` — EULA PDF wrapper;
- `/documents/terms-of-service.html` — Russian public-offer PDF wrapper.

Current tariff cards: 270 RUB/month and 670 RUB/3 months, both with a three-day free period and identical seven-item feature lists. Both “Подключить” buttons route to `@MoriVpnRobot`.

Other CTA behavior:

- hero/header install buttons route to `/downloads.html`;
- “Получить ключ” routes to `@MoriVpnRobot`;
- Android “Скачать APK” actually routes to Google Play;
- primary Windows CTA routes to `https://download-app-service-conect.top/windows`;
- macOS map routes to `https://download-app-service-conect.icu/macos`;
- footer Windows link points directly to `/builds/MoriVPN-Setup-2.0.6.exe`;
- footer macOS link incorrectly points to the iOS query route;
- Twitter/X and YouTube are inert `#` links.

The `.top` download domain root returns a bare nginx 404. The `.icu` domain fails in Chrome with a certificate common-name mismatch. The downloads page still displays `COMING SOON XX.05.2026` placeholders for macOS/iOS.

The page’s translation loader currently emits a malformed-JSON error, and the sticky-header script emits a null-reference error on more than one route. Content still renders after a delay.

## Legal entity and documents

All current documents name QUARTETTO INTERNATIONAL LTD, company number `07785225`, at Suite Am 77, Balfour Business Centre, 390-392 High Road, Ilford, United Kingdom, IG1 1BF.

Companies House confirms the company is active, a private limited company incorporated 2011-09-23, with SIC 62011 (ready-made interactive leisure and entertainment software development). Last accounts are made up to 2025-09-30.

Document findings:

- Privacy Policy: no registration/identity requirement; access code model; RAM-only/no browsing logs claim; third-party processors may process limited email/payment data; no precise location; children under 16; contact by support email.
- EULA effective 2026-05-01: personal/non-commercial revocable license; access-code responsibility; app-store payment/refund rules; no-logs claim; broad “as is” language; termination for breach; vague governing-law wording.
- Public offer: its own PDF title says `черновик под QUARTETTO (UK)`; payment constitutes acceptance; complaint/fix window is 10 calendar days; customer may cancel before completion with refund less services/transfer costs; refund target is three business days; the agreement explicitly chooses Russian Federation law and courts despite the UK entity.

## Telegram distribution and release history

Current public scale:

- `@MoriVpnOfficial`: 88.7K subscribers.
- `@MoriVpnRobot`: 32,118 monthly users on its public landing page.
- `@MoriVpnGuide`: 1.67K subscribers and two migration instructions.

Observed release timeline:

| Date | Public event |
| --- | --- |
| 2025-08-08 | Channel created. |
| 2026-01-31 | First launch: free/no ads/no limits; Android, Windows and macOS claimed; iPhone/store releases promised for February; explicitly framed as a growth funnel for the MORI coin ecosystem. |
| 2026-02-25 | “Works again”: users told to delete the old build, download from the bot and re-enter the key. |
| 2026-04-27 | 2.0 transition announced: new design/protocol/servers, Play distribution, PC links, all old keys replaced and full uninstall required. |
| 2026-04-28 | 250 RUB/month, three-day trial; users offered a chance at 50 annual subscriptions for leaving a positive five-star Play review. |
| 2026-05-02 | iPhone routed through Happ: 180 RUB/month or one-day trial; Happ links and MORI codes are separate products. |
| 2026-05-04–16 | Repeated server/key/backend outages, re-authentication, temporary support closure and compensation. |
| 2026-05-29 | Key replacement, special allowlist server category, bot self-service key replacement and three-day compensation. |
| 2026-06-06 | Provider/infrastructure migration after a major outage; iPhone and Smart TV promised “this week”. |
| 2026-06-12 | Android fix published in Google Play. |
| 2026-06-15 | New Windows client/installer released through the site, bot links, mirrors and Mini App. |
| 2026-06-30 | iOS still uses Happ; own iOS app said to be in final App Store review; up to five devices claimed. |
| 2026-07-03 | Bot rewritten; self-service subscription management; MORI key now described as three devices and Happ as one; torrents banned with account blocking and no refund; price raised to 299 RUB. |
| 2026-07-21 | New architecture/client for all platforms announced; plan to leave Happ reiterated. |
| 2026-07-22 | Scheduled server maintenance completed. |

Release pattern: Telegram-first announcements, bot/Mini App as the source of current links and keys, Play for Android, direct/mirrored Windows installers, forced key rotation and often full uninstall/re-authentication during major upgrades.

## Published migration instructions

Android 2.0: fully delete the old app, install from Google Play, obtain a new three-day key in the bot and activate it. Old apps and keys are declared invalid.

Windows 2.0: fully delete the old app; MORI recommends the third-party Revo Uninstaller, a full residual-file/registry scan and emptying the recycle bin; download from the external `.top` domain; install, reboot, obtain a new bot key and activate. This is a high-friction migration and an avoidable trust cost.

## Material contradictions

- Site FAQ allows P2P/torrents; Telegram bans torrents and threatens blocking without refund.
- Site shows 270/670 RUB; Telegram says 299 RUB; bundled `v2` paywall says 399/3830 RUB; old resources price in MORI tokens.
- Device allowance varies among 3, 5 and 1 depending on surface/product.
- Website/store creatives imply broad native platform support; iOS still uses Happ, macOS/iOS cards are stale or disabled and the `.icu` certificate is invalid.
- Website says referral is coming later; a full referral/points/reward system is bundled.
- Website comparison claims no telemetry; Telegram says infrastructure AI consumes anonymized load/speed/failure telemetry.
- Website says all infrastructure is outside Russia; the separately retained 2026-07-05 paid-key sample resolved one endpoint into a Russian ASN.
- Site claims “own protocol”, while the Android package bundles multiple V2Ray/VLESS client stacks; this may mean proprietary orchestration/obfuscation, but the stronger wording is unproven.

## Evidence images

See [`screenshots/`](screenshots/) for the current Play page, nine Play creatives, website hero/pricing/comparison/downloads, Telegram channel/guide and legal-document pages.

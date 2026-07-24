# BlancVPN — Website, Stores, Legal, Release And Channel Notes

**Snapshot:** 2026-07-22
**Scope:** current public first-party surfaces and official stores/registry; account/config links, current IPs and personal identification numbers are excluded.

## Distribution Matrix

| Surface | Observed route | Actual destination/product |
| --- | --- | --- |
| Android | `/ru/get/android` | Official BlancVPN via Google Play; fallback instructions for Happ, Outline, WireGuard and OpenVPN. Happ is offered as a direct GitHub APK. |
| iOS | `/ru/get/ios` | Happ/V2Ray first, then Outline, WireGuard and OpenVPN. BlancVPN's own global App Store app exists, but Russian users are sent through foreign-region guidance. |
| macOS | `/ru/get/mac` | Browser extension plus Happ, Outline, WireGuard and OpenVPN; native BlancVPN is also available through the Apple listing on supported Apple-silicon Macs. |
| Windows | `/ru/get/windows` | Happ, Outline, WireGuard, OpenVPN and the Chrome extension. There is no native BlancVPN Windows binary on the page. Public posts on 12 and 26 June 2026 say it is still under development. |
| Linux | `/ru/get/linux` | V2Ray setup, Outline, WireGuard, OpenVPN and browser extension; no native BlancVPN client. |
| Routers | `/ru/get/router` | WireGuard/OpenVPN setup and the broader Keenetic/XKeen manual. |
| Smart TV | `/ru/get/tv` | Knowledge-base instructions rather than a dedicated store binary. |
| Chrome | `/ru/get/chrome` | Chrome Web Store extension. |
| Firefox | `/ru/get/firefox` | Mozilla Add-ons extension. |

The homepage labels Windows as a direct “download” platform, but its destination is a curated third-party-client page. This is a useful fallback strategy and a misleading native-product implication at the same time.

The public Android page does not expose a direct BlancVPN APK. The installed Android build nevertheless includes an APK installer receiver/background downloader and Shorebird metadata. Those are release capabilities, not evidence of an active public sideload channel or a delivered OTA patch.

## Google Play

- Package: `com.blancvpn.app`; publisher: BlancVPN; developer identity: Yadda OU.
- 100K+ installs. The live 22 July public page showed 4.4 stars and 5.14K reviews in its header, while its phone-specific ratings block still showed 4.82K reviews. Store counters are therefore both locale/device-specific and internally asynchronous.
- Current public update date: 19 July 2026. The new changelog is specific: separate confirmation before account deletion, more stable login/logout, selected location in notifications and the Quick Settings tile, faster launch/lower battery use, improved connection stability and minor UI fixes. The store does not expose the release version in public HTML, so it is not safe to equate this date with installed `1.7.0+174` solely from the listing.
- Store claims: 30+ locations, four protocols, up to 2 Gbit/s, unlimited devices/data, no logs, 24/7 support and 30-day refund.
- Data Safety declaration: no third-party sharing; collection of personal information, app activity and app information/performance; encrypted in transit; deletion request supported.
- The live Play recommendation rail is locale/session dependent. The current Poland/English page showed Speedify, Seed4.Me, Browsec, PotatoVPN, Super VPN Unlimited Proxy and Windscribe. Earlier official renderings also showed JumpJumpVPN, Bitdefender Antivirus, Cure VPN, v2RayTun, Rabby Wallet and NotVPN. Treat the rail as an acquisition environment, not a stable competitor list.

## Apple App Store

- Bundle: `com.blancvpn.app`; provider: Yadda OU.
- First US availability in Apple's lookup data: 23 October 2025. Current version `1.6.2`, released 22 June 2026; 100.2 MB; iOS/iPadOS 15+; Apple-silicon Mac support; English is the only declared language.
- US lookup snapshot: approximately 4.26/5 from 406 ratings. Ratings and IAP prices vary by storefront.
- US IAPs exposed by the listing: USD 11.99 monthly, USD 49.99 for six months and USD 69.99 annually.
- Apple privacy label says purchases, email, user/device identifiers, product interaction and diagnostics may be linked to the user for analytics/app functionality.
- No accessibility features are declared in the current Apple listing.

Public version history:

| Version | Date | Store note |
| --- | --- | --- |
| 0.12.3 | 18 Jul 2025 | Minor improvements and fixes |
| 1.0.0 | 22 Oct 2025 | Fixes and improvements |
| 1.0.1 | 23 Oct 2025 | Fixes and improvements |
| 1.1.0 | 6 Nov 2025 | Multiple UI/UX/performance fixes and major startup-time reduction |
| 1.2.2 | 12 Jan 2026 | New features and fixes |
| 1.3.12 | 15 Apr 2026 | Xray Extra, Russian-services bypass and stability work |
| 1.4.1 | 7 May 2026 | AmneziaWG Extra and connection stability |
| 1.6.2 | 22 Jun 2026 | Minor improvements and fixes |

The Türkiye “You Might Also Like” rail contained Paper VPN, AmneziaVPN, Red Shield VPN, VPN Russia, Mirage VPN, Happ, Дед Proxy, TipTop VPN, Netcraze and EVA VPN. Red Shield and TipTop are also installed in this audit device, giving a direct recommendation-graph link between the competitor set.

Evidence: [App Store viewport](../browser/05-app-store-us-viewport.png).

## Browser Extensions

Chrome Web Store snapshot:

- the freshest official storefront result reports version `1.19.2`, updated 20 July 2026; some localized cached pages still render `1.19.1` from 2 June, so the store's public indexing is not synchronized;
- 100K users, 2.6/5 from 244 ratings;
- 6.29 MiB, five languages;
- declares handling personally identifiable information;
- publisher Yadda OU and address match the VPN entity.

Mozilla snapshot:

- the current Russian listing now reports `1.19.2`, while Mozilla's version-history endpoint still names `1.19.1` from 2 June as latest; this is a current listing/history inconsistency, not enough evidence to assign a Firefox release date to `1.19.2`;
- about 1,065 users, 3.5/5 from 28 reviews;
- 18 public versions from 19 August 2025 through 2 June 2026.

Firefox cadence was aggressive around blocking changes: three releases on 10 April 2026 and three more on 17 April, followed by 1.17.6 on 4 May, 1.18.0 on 18 May and 1.19.1 on 2 June. Notes name proxy-connectivity work, routing-exception import/export, UI fixes, background optimization and a connection-error screen. The shared `1.19.x` extension numbering and matching sizes suggest Chrome/Firefox are shipped from one code line, but the lagging storefront/version-history surfaces make exact same-day release claims unsafe.

## Review And Reputation Surface

The reputation picture changes sharply by surface and storefront:

| Surface | Current observed signal | Representative themes |
| --- | --- | --- |
| Google Play | 4.4/5; 5.14K header count and 4.82K phone count | Recent visible complaints focus on missing login codes after a long-plan purchase, no obvious cancellation path, slow/unreachable support and the absence of a native Windows client. A visible developer reply attributes delays to request volume and asks the customer to reconnect with support. |
| Apple App Store, GB | 4.5/5 from 39 ratings | The visible sample includes one reliability-positive review and two complaints about an intermittently unavailable/slow paid service, ineffective support and refund friction. Other storefronts have different counts and mixes. |
| Chrome Web Store | 2.6/5 from roughly 241–244 ratings | The aggregate is materially weaker than the Android/iOS store averages; the current listing text still promises unlimited speed/traffic, all devices and always-available support. |
| Firefox Add-ons | 3.5/5 from 28 reviews | Small sample; current distribution is 16 five-star and 10 one-star ratings, with only three ratings in the middle. |
| Trustpilot | 2.0/5 from 120 reviews; 56 in the last 12 months | 48% five-star but 40% one-star: a polarized distribution. Repeated recent allegations concern service outages/low speed, login codes stopping, paid subscriptions not activating, router/Extra paths failing, delayed or automated support and refunds not being processed promptly. |

Trustpilot labels the profile claimed since October 2022 and on a paid subscription. BlancVPN asks customers for reviews, had replied to 61% of negative reviews and typically replied within one week at capture time. Those are platform-reported moderation/response metrics; individual review allegations were not independently verified.

The stronger finding is BlancVPN's own review curation. Its homepage embeds only positive Trustpilot excerpts, and `/ru/reviews` says **“only real reviews”** and **“we do not delete or edit anything.”** The initially rendered review page nevertheless contains ten visible entries, all 5/5, dated from November 2024 through January 2026. It does not surface the current 2.0 TrustScore, the 40% one-star share or the wave of March–July 2026 complaints before the user presses “read more.” The excerpts link to real Trustpilot entries, but the presentation is a selective testimonial wall rather than a representative reputation summary.

This gap is especially damaging because the curated testimonials praise immediate support and effortless refunds—the exact themes most often disputed by recent public reviewers. Do not infer fake reviews or fraud from the mismatch; the defensible conclusion is **selection bias plus stale recency**.

## Telegram And Product Timeline

Public preview on 22 July 2026 showed 96.8K subscribers, 43 photos and 80 links. The crawl retained metadata for 87 surviving public posts from channel ID 1 through 132. There is one “channel created” event in July 2022; the first surviving substantive post is 23 January 2025. From then through July 2026 the channel normally posts two to eight times per month.

The channel is not a release-notes feed. It is a censorship-news/content engine with product instructions, incident communication and promotion layered into topical posts. Important milestones:

- 27 Oct 2025 — public launch announcement for native iOS, macOS and Android apps; email login and in-app/site purchase positioned as a one-click upgrade over configuration clients.
- 21–30 Nov 2025 — Black Friday campaign promising up to 80% off with a promo code.
- 3 Dec 2025 — referral programme launch: 30 days to each party, two-year inviter cap.
- 17 Dec 2025 — 2025 recap: 50 locations, 10-Gbit/s claim, three native apps, Chrome/Firefox, Keenetic generator, Bug Bounty, Open Source support, gifting and referral.
- 3 Feb 2026 — native app could not yet handle a blocking event; users were sent to V2Ray third-party clients/Extra configurations while the native fix was developed.
- 17 Apr 2026 — major app release with Xray/Xray Extra, automatic protocol selection and Russian-service split tunnelling; the browser extension got prepared/manual exclusion rules.
- 3 Jun 2026 — acknowledged a multi-day Russia connectivity incident and automatically credited all users seven days.
- 12 and 26 Jun 2026 — native Windows client explicitly still in development.
- 26 Jun 2026 — roadmap also named family-access tooling, network refresh, Nigeria launch, India closure and a virtual Kazakhstan location whose server is physically elsewhere.
- 7 Jul 2026 — after repeated Happ removals, BlancVPN said it had tested INCY for security/functionality and formally recommended it; Karing remained the previous fallback.

Views grew from roughly 14–35K per post in much of 2025 to 100–700K during the February–April 2026 blocking wave, well above the current subscriber count. That can reflect forwarding, sponsored distribution or earlier audience changes; the public counters alone do not identify the mechanism.

Acquisition/growth mechanics seen in the channel include seasonal promo codes (up to 58%, 66% and 80%), referral, gifts, a free Telegram MTProto proxy, incident compensation and a strong “send this to family” prompt. The service often converts breaking censorship news directly into a practical checklist and then a subscription CTA.

## Public Status Operations

`blancvpnstatus.com` currently reports no incident and exposes Website, Telegram Bot and BlancVPN Locations as separate components. The retained public incident record goes back at least to November 2024.

Operationally important examples:

- 3–12 Feb 2026: Russia-wide degraded connectivity across 49 locations; temporary recovery depended on V2Ray Extra and third-party clients before native recovery.
- 28 May 2026: 50-location degradation resolved in about four hours.
- 31 May–19 Jun 2026: long Russia-wide degradation across 50 locations; most service recovered by 4–6 June, while AmneziaWG/WireGuard/OpenVPN and the browser extension lagged.
- Several localized incidents (India, Vilnius, Tokyo, Zurich, Buenos Aires) were updated through investigating/identified/monitoring/resolved states.

The status page and automatic seven-day compensation are product trust strengths. Some incident updates use generic templates and the longest incident's final resolution date is much later than its last detailed recovery update, so the timeline needs interpretation rather than a simple uptime claim.

## Legal Entity And Registry

The store listings, transaction email and site footer consistently point to **Yadda OÜ**, an Estonian private limited company:

- registry code `16469911`; VAT `EE102489668`;
- registered 29 March 2022;
- registered office: Ranna tn 6, Võiste alevik, Häädemeeste vald, Pärnu maakond 86501, Estonia;
- principal registered activity: data processing/data management/data mediation and related activities;
- Dmitrii Anisimov is the sole board member and 100% shareholder in the current public registry. No personal identification number is retained here.

The official Estonian register still shows status **Entered into the register**, but also flags the 2025 annual report (due 30 June 2026) as not submitted and says a deletion notice has been published. This is a current compliance warning, not evidence that the company has already been dissolved.

Filed operating figures show 2024 revenue of €74,489 and a €20,440 loss, versus 2023 revenue of €21,030 and a €1,934 loss. An official May 2026 extract reported no tax debt at that date. These figures describe Yadda OÜ, not necessarily the full economics of every BlancVPN group entity or payment channel.

## Terms And Privacy

The current `.ltd` aliases and the app's `.legal` URLs return byte-equivalent substantive Russian documents:

- Terms last updated 27 May 2025.
- Privacy Policy last updated 27 June 2024.

The documents do not identify Yadda OÜ, its registry code, governing law or dispute venue inside the substantive text; identity is supplied only by the surrounding site footer/store metadata. The privacy text references generic “BlancVPN group companies” and generic payment/support/email/analytics/advertising vendors without naming processors.

Privacy says BlancVPN collects account email; optional Telegram name/ID/username; transaction amount/currency/date, last four card digits, country/postcode and payer email; support messages/device details; chat browser/OS; feature-use information; website access/referrer logs; crash and diagnostic data. It says payment data is retained for ten years, marketing consent for three years after subscription, support tickets for three years and support-device data for up to six months.

The no-logs claim is specifically limited to online activity while connected—visited pages and content. That can coexist with account/product/diagnostic telemetry, but the marketing shorthand “no logs” does not explain the boundary. Store declarations and the bundled Sentry/Firebase/PostHog components are directionally consistent with the broader telemetry categories.

Material contract/marketing mismatches:

- Marketing promises unlimited devices and family sharing. Terms say the service is for reasonable personal use, not distribution among multiple users, prohibit sharing with third parties/unauthorized users, reserve monitoring of use, and permit throttling/location limits or account deletion without refund.
- Marketing/help says a 30-day refund “without extra questions.” Terms limit users to two refunds, require six months between them, exclude monthly renewals, crypto, prepaid and gift cards, allow fee deductions/usage verification and deny automatic refund on account deletion.
- Terms allow under-18 use with parental supervision; Privacy says the service is not intended for anyone under 18 and that minors' data will be deleted.
- Privacy says low-democracy server locations will show a risk warning. Such a warning was not encountered while browsing the disconnected selector; connection is paywalled, so the promised runtime warning remains unverified.

Evidence: [Terms viewport](../browser/06-terms-safe-viewport.png), [Privacy viewport](../browser/07-privacy-safe-viewport.png).

## What To Borrow / What Not To Copy

Borrow:

- Treat the knowledge base and third-party-client compatibility as a resilience layer, not just support content.
- Publish named blocking playbooks, a real status page and automatic incident compensation.
- Align release announcements with the exact user problem solved, as the April split-tunnelling release did.
- Maintain store-native apps, browser extensions, router tooling and configuration-client fallbacks as distinct lanes.
- Use recommendation rails and deletion events to maintain a tested fallback-app shortlist.

Do not copy:

- Calling a third-party-client page a native Windows download.
- Contradictory “unlimited family” and fair-use/account-sharing language.
- A refund promise that hides material exclusions and lifetime limits.
- Fragmenting legal/account/help traffic across many similar domains without a clear verification page.
- Publishing stale legal/privacy text that omits the contracting entity and named processors.

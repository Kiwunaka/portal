# MORI VPN — Competitor Profile

**Main URL:** https://morivpn.com/
**Current deep-pass snapshot:** 2026-07-22
**Historical passive baseline:** 2026-07-05; purchased endpoint evidence remains redacted
**Current status:** `DEEP PASS COMPLETE WITH BLOCKER`
**Android package:** `com.morivpn.mori_vpn_mobile`
**Installed version:** `2.0.5` (`versionCode 116`)
**Install source:** Google Play

## Current Verdict

MORI is one of the strongest competitors in this set at distribution, visual packaging and narrative control, but the current product truth is badly fragmented.

- The public machine is real: 88.7K Telegram subscribers, roughly 32K monthly bot users, 50K+ Play installs, polished store creatives, an active bot and frequent editorial posts.
- The observed `x86_64` Play installation cannot reach its first screen because the delivered split has V2Ray libraries but no Flutter runtime. This blocks native UX and connection testing on LDPlayer; it does not prove the ARM phone build is broken.
- Static resources reveal a much larger product vision than the live website: TOR, Multi-Hop, anti-block, adaptive mode, dedicated IP, 10 Gbps, post-quantum protection, QR device/TV login, three plan tiers, token payment and referral rewards.
- The company and distribution routes are identifiable, but the offer, pricing, platform status, torrent policy, device limits and privacy language disagree across surfaces.
- The biggest competitive lesson is not to copy MORI’s claims. Copy its content/distribution system, visual confidence, bot self-service and product storytelling while keeping POKROV’s release state and promises synchronized.

## 2026-07-22 At A Glance

| Metric | Current observation |
| --- | --- |
| Android | Google Play `2.0.5` (`116`), last updated 2026-06-12 |
| Play scale | 50K+ downloads, ~1.44K reviews, 2.4/5 |
| Telegram | 88.7K channel subscribers; bot landing shows 32,118 monthly users |
| Current web prices | 270 RUB/month; 670 RUB/3 months; three-day free period |
| Other current prices | Telegram says 299 RUB/month; bundled `v2` paywall says 399 RUB/month or 3,830 RUB/year |
| Activation | `MORI-XXXX-XXXX-XXXX` code, primarily obtained/managed through Telegram bot |
| Current Android result | Crashes before Flutter UI on observed `x86_64` Play split |
| Live connection test | Blocked; no VPN permission prompt and no `tun0` |
| Legal operator | QUARTETTO INTERNATIONAL LTD, UK company `07785225`, active |
| Distribution | Play for Android; Telegram bot/Mini App for keys and current links; direct/mirrored Windows installers; Happ bridge for iOS |

## Native Android Result

The installed application launches `.MainActivity`, then immediately reaches Android’s crash dialog. Logcat’s decisive failure is a missing `libflutter.so`: the loader checks all advertised ABIs and finds none. The installed `x86_64` split contains `libv2jni.so`, `libtun2socks.so` and other helpers but not `libflutter.so` or `libapp.so`.

Therefore the following are explicitly `BLOCKED_BY_BUILD` on this device:

- onboarding and activation UX;
- live server catalog;
- paywall and purchase UX;
- settings and advanced feature toggles;
- connection establishment;
- exit/DNS/leak/speed checks.

Full evidence: [`runtime-failure-summary.md`](raw/mori-vpn/2026-07-22/runtime-failure-summary.md) and [`android-startup-crash.png`](raw/mori-vpn/2026-07-22/screenshots/android-startup-crash.png).

## Product Architecture Found Inside The APK

The resource corpus contains 1,020 Russian leaf strings and two overlapping generations of UI.

The newer shell is simpler: welcome, access-code entry, Home/Servers/Devices/Profile/Settings, server search/favorites, QR pairing, TV login and one Premium tariff. It promises 100+ countries, three devices, VLESS, obfuscation, Kill Switch, TCP termination, unlimited speed and broad platform support.

The older/full architecture is much more ambitious:

- Basic, Premium and Maximum plans;
- TOR, Multi-Hop with optional intermediate hop and “triple protection”;
- adaptive connection and automatic anti-block routing;
- Kill Switch and traffic blocking on disconnect;
- dedicated IP for banking/corporate/streaming use;
- 10 Gbps/8K and post-quantum claims;
- 1/3/5-device packages and 1/3/6-month or 1/3-year periods;
- bank card, crypto, Phantom/Solana and `$MORI` token paths;
- referral links, point accrual, milestones, achievements and subscription redemption.

Strings also state that TOR, Multi-Hop and Kill Switch may be temporarily unavailable. Country/city localization counts are not a live server inventory.

Detailed maps: [`ui-copy-map.md`](raw/mori-vpn/2026-07-22/ui-copy-map.md) and [`static-summary.md`](raw/mori-vpn/2026-07-22/static-summary.md).

## Current Public UX And Design

### Store

The Play creative system is excellent: white field, black device renders, chrome shield, oversized typography, one claim per frame and paired phone/tablet variants. It makes a small product feel like a premium hardware brand.

The strongest frames are:

- fast connection with visible locations/ping/favorites;
- Zero Logs;
- one account across devices with QR connection;
- all-device protection;
- clean product hero close-ups.

The weakness is credibility: those polished frames sit above a 2.4 rating and an emulator build that cannot start. Visible reviews repeatedly complain about consumed device slots, connection failures after payment and slow support/refund handling.

### Website

The homepage combines a high-fashion monochrome hero, pricing, a one-sided comparison table, cautionary PureVPN/HMA stories, onboarding and a detailed FAQ. It is more assertive and better art-directed than most competitors in this set.

Its conversion flow is simple:

```text
Website / content → Telegram bot → trial or payment → access code → app
```

Both pricing cards and “Получить ключ” lead to the bot. This keeps subscription management, key replacement, mirrors, support and upsell in one owned funnel.

The implementation quality is weaker than the art direction: stale `XX.05.2026` platform placeholders, inert social links, a malformed translation JSON error, sticky-header errors, broken macOS routing and delayed/blank first renders on some routes.

### Telegram

MORI publishes frequent educational/editorial posts on DPI, white lists, VPN economics, privacy leaks and outages. Posts routinely reach tens of thousands of views. The channel does three jobs at once:

- educate and manufacture expertise;
- explain incidents before support is overwhelmed;
- push every path back to `@MoriVpnRobot`.

The separate `@MoriVpnGuide` channel has only two migration guides, but they are linked from the launch post. The Windows guide is unusually destructive/high-friction: it recommends Revo Uninstaller, full residual registry/file cleanup, emptying the recycle bin, rebooting and obtaining a new key.

## Release And Distribution Machine

MORI releases through announcements rather than a stable public changelog:

1. Telegram announces a release, outage or forced migration.
2. The bot/Mini App becomes the source of current keys, links and mirrors.
3. Android moves through Google Play.
4. Windows ships as a direct site EXE and through external redirect/mirror domains.
5. Major versions invalidate old keys and often require full uninstall/re-authentication.
6. Downtime is compensated with subscription days.

Important chronology:

- January launch was presented as free/no ads/no limits and explicitly as a growth engine for the MORI coin ecosystem.
- Version 2.0 in late April converted the product to paid access, invalidated old keys and ran a five-star-review reward draw for 50 annual subscriptions.
- May and June contained repeated key/server/provider incidents, support closure and forced refreshes.
- Android received a Play fix on June 12; a new Windows installer followed June 15.
- iOS promises slipped from February to “next week”, then “this week”, then “final moderation”; on June 30 and July 21 Happ was still the bridge.
- July’s rewritten bot added self-service subscription management, changed the stated device model and banned torrents.

The full dated table is in [`public-surface-summary.md`](raw/mori-vpn/2026-07-22/public-surface-summary.md).

## Legal And Trust Layer

Companies House verifies QUARTETTO INTERNATIONAL LTD as active, incorporated in 2011, company `07785225`, at the address printed in Play and MORI’s documents.

The legal implementation still has serious product debt:

- the public-offer PDF title literally contains “черновик под QUARTETTO (UK)”;
- the Russian offer chooses Russian law/courts although the operator is a UK company;
- the EULA uses vague governing-law wording;
- the privacy policy says no browsing logs and RAM-only processing but allows third-party payment processors to handle limited email/payment data;
- Play says no data is collected or shared;
- marketing says no telemetry, while Telegram describes anonymized infrastructure telemetry used by an “AI”.

This does not prove unlawful processing. It proves that the trust story is not managed as one canonical contract.

## Current Contradiction Ledger

| Topic | Conflicting public/internal statements |
| --- | --- |
| Price | 270/670 RUB site; 299 RUB Telegram; 399/3,830 RUB new app strings; 50/100/150 MORI old strings |
| Devices | 3 on current site/new UI; 5 on downloads/June Telegram; Happ 1 |
| Torrent | Website FAQ allows it; July Telegram bans it and threatens blocking without refund |
| Platforms | Store/site creatives imply all platforms; iOS remains Happ; macOS/iOS download cards are stale/broken |
| Free access | Hero says “Бесплатно” and site offers three days; initial product was fully free; current Telegram is subscription-first |
| Referrals | Website says “later”; complete points/rewards UX is already bundled |
| Telemetry | Site comparison claims none; Telegram describes anonymized operational telemetry |
| Protocol | “Own protocol” marketing; APK contains multiple V2Ray/VLESS client stacks |
| Infrastructure | Outside-RF claim; 2026-07-05 purchased-key sample used a Russian ASN endpoint |
| Legal status | UK operator; Russian-law offer; PDF labelled as a draft |

## What POKROV Should Copy

- One memorable visual system across site, store and app.
- Telegram content as an acquisition and incident-communication channel, not just support.
- Bot self-service for key replacement, subscription management and current downloads.
- QR pairing and cross-device continuation.
- Separate store frames for one product promise each.
- Transparent maintenance notices and automatic service-day compensation.
- A visible “best for you/recent/favorites” server hierarchy.
- A compact code-based activation path without forced profile creation.

## What POKROV Should Not Copy

- Shipping store bundles without ABI launch coverage.
- Review incentives tied to five stars.
- Forced full uninstall/key invalidation as a normal release mechanism.
- Multiple download domains with a broken certificate and no clear provenance.
- Claiming all platforms before the clients exist.
- Contradictory prices, device limits and acceptable-use rules.
- “Own protocol”, “post-quantum”, “zero knowledge” or “AI” wording without a narrow technical definition and evidence.
- A public legal PDF still labelled as a draft.
- One-sided competitor tables with no claim-level sourcing.

## Current Evidence Index

- [`public-surface-summary.md`](raw/mori-vpn/2026-07-22/public-surface-summary.md)
- [`runtime-failure-summary.md`](raw/mori-vpn/2026-07-22/runtime-failure-summary.md)
- [`static-summary.md`](raw/mori-vpn/2026-07-22/static-summary.md)
- [`ui-copy-map.md`](raw/mori-vpn/2026-07-22/ui-copy-map.md)
- [`screenshots/`](raw/mori-vpn/2026-07-22/screenshots/)

---

## Historical 2026-07-05 At A Glance

| Metric | Value |
| --- | --- |
| Product | MORI VPN / MORIVPN |
| Main positioning | VPN + TOR, zero-logs, no account, VLESS + Reality |
| Main funnel | Telegram bot `@MoriVpnRobot` + Android Google Play app |
| Public Android scale | Google Play: 50K+ installs, 1.41K reviews, 4.7 shown on Play; AppBrain: 52K downloads, 1.36K reviews, 3.45 |
| Telegram bot scale | `@morivpnrobot`: 44,594 monthly users observed |
| Telegram channel scale | Telemetr: 92,019 subscribers, 19,984 views/post, 22.53% ER observed |
| Paid subscription endpoint observed | 1 VLESS Reality endpoint in purchased subscription |
| Observed paid endpoint host | `[endpoint host omitted]`, SNI `[endpoint host omitted]` |
| Observed paid endpoint IP | `[endpoint address omitted]` |
| Observed endpoint ASN/geo | AS47764 LLC VK, Moscow, RU, per ipinfo snapshot |
| Public claim tension | MORI channel claims infrastructure outside Russian jurisdiction; purchased endpoint resolved to a Russian AS/IP in this sample |

---

## Positioning And Messaging

MORI presents itself as a privacy-first consumer VPN with a strong anti-DPI story:

- VPN + TOR in one app.
- Zero-logs, no accounts, no identity link.
- VLESS + Reality and traffic obfuscation.
- Kill Switch.
- Own DNS / DoH / DoT claims.
- RAM-only infrastructure claims.
- App-first key activation via Telegram bot.

The brand is tightly tied to the broader MORI ecosystem: MORI coin, Mori Win/casino audience, Telegram channels, and influencer-style community distribution. This is not a quiet utility VPN brand; it is a hype/community funnel with product claims layered on top.

---

## Public Product Surface

Observed public domains and surfaces:

| Surface | Role | Notes |
| --- | --- | --- |
| `morivpn.com` | Main site | Cloudflare fronted; pricing and product claims |
| `morivpn.com/downloads.html` | Download page | Claims Windows/macOS "coming soon" on static page while other surfaces claim broader availability |
| `@MoriVpnRobot` | Activation/support bot | 44.6K monthly users observed |
| `@MoriVpnOfficial` | Telegram channel | 92K subscribers on Telemetr snapshot |
| Google Play package `com.morivpn.mori_vpn_mobile` | Android app | Developer: QUARTETTO INTERNATIONAL LTD |
| `mori-news.com/vpn/` | Ecosystem/news page | Claims 100+ countries and broader availability |
| `moribonus.com/en/vpn` | Ecosystem/bonus/casino-adjacent page | Mentions plans and Mori Coin holder access |
| `mori-vpn.com` | Similar/likely SEO/affiliate surface | Lists 5+ locations and testimonial copy; treat as not proven official unless owner confirms |
| `moriarty-vpn.online` | Similar/download surface | Points downloads to Telegram; treat as not proven official |

CT-log-discovered names for `morivpn.com`:

- `api.morivpn.com`
- `ru.api.morivpn.com`
- `tg.morivpn.com`
- `land.morivpn.com`
- `ru.morivpn.com`
- `relay.morivpn.com`
- random-looking technical subdomains

Live DNS at collection time:

- `morivpn.com`, `www`, `api`, `tg`: Cloudflare IPs.
- `ru.api.morivpn.com`, `ru.morivpn.com`: `[IPv4 address omitted]` observed, geolocated by ipinfo to Stockholm / AS200019 ALEXHOST SRL.
- Some CT names were NXDOMAIN.

---

## Paid Subscription Endpoint

The purchased subscription link was fetched once and parsed locally. The raw URL, UUID, public key, short id, spiderX and any token-like fields are intentionally not stored here.

Parsed result:

| Field | Value |
| --- | --- |
| Format | Base64 subscription |
| Config count | 1 |
| Protocol | VLESS |
| Transport | TCP |
| Security | Reality |
| Address | `[endpoint host omitted]` |
| Port | `443` |
| SNI | `[endpoint host omitted]` |
| Fingerprint | `random` |
| Label | Contains `N/A` and `@mori`; unique user/config id redacted |

DNS and reachability:

| Host | A record | Ping sample | TCP 443 |
| --- | --- | --- | --- |
| `[endpoint host omitted]` | `[endpoint address omitted]` | 5/5, avg 15.6 ms | OK |
| `[endpoint host omitted]` | `[endpoint address omitted]` | 5/5, avg 10.6 ms | OK |
| `[endpoint host omitted]` | `[IPv4 address omitted]` | not endpoint | not endpoint |

CT names for `[endpoint host omitted]`:

- `[endpoint host omitted]`
- `[endpoint host omitted]`
- `[endpoint host omitted]`

HTTP/TLS note:

- `[endpoint host omitted]` and `[endpoint host omitted]` return HTTP 200 with an old WebThemez/TIMES HTML template on normal HTTPS.
- This looks like a plausible REALITY camouflage/fallback destination rather than a public MORI page.

Interpretation:

- This purchased subscription does not expose "100+ countries" or multiple locations. It exposes one active VLESS Reality endpoint.
- The observed endpoint is in a Russian AS/IP range, which conflicts with MORI channel copy claiming infrastructure outside Russian jurisdiction. One key is not proof of the whole fleet, but it is proof of at least one paid access endpoint using RU-hosted infrastructure at the time of testing.

---

## Pricing And Packaging

Observed pricing is inconsistent across surfaces:

- Main site: 1 month 250 RUB, 3 months 600 RUB, 3 devices, 3-day free period.
- Google Play: free download, in-app purchases.
- Telemetr channel post from 2026-07-03 mentions 299 RUB and says one MORI key works on 3 devices; Happ subscription works on 1 device.
- Mori Coin holder route: free access for holders from $500 equivalent is claimed on ecosystem pages.

Product packaging appears to be changing quickly. Treat pricing as volatile.

---

## Reviews And Reputation

Positive signals:

- Google Play shows 4.7 with about 1.39K reviews in the page snapshot.
- Positive visible Play review praises "zero logs".
- Codeby forum comment says it works for Upwork/Fiverr, normal ping, no file-send drops, and active free premium access.
- Telegram channel/community scale is large for a small VPN entrant.

Negative signals:

- AppBrain reports a much lower 3.45 rating based on about 1.4K ratings.
- Google Play visible negative review from 2026-06-20 complains that servers are unstable, support ignores, and payment did not pass.
- Google Play visible review from 2026-05-01 says it did not connect on low-stability mobile internet in Volgograd.
- Mail.ru Answers thread includes a negative user claim that the service collects money and does not work/refund; this is low-quality evidence, but consistent with instability/payment-support complaints.
- Telegram channel posts themselves mention technical works, server/key issues, and an engineering hire focused on network stability.

---

## Scale Estimate

MORI is clearly larger than a tiny Telegram-key reseller on audience and marketing:

- Google Play: 50K+ installs.
- Bot: 44K+ monthly users.
- Telegram channel: about 92K subscribers.
- Multiple public domains / ecosystem placements.
- Active app, bot, channel, and Android store presence.

But infrastructure evidence from the purchased key does not match the scale implied by marketing:

- The actual subscription sample exposed one VLESS Reality endpoint.
- No multi-country subscription list was present.
- Public claims such as "100+ countries", "RAM-only", "own DNS", "outside Russian jurisdiction", and broad platform support are not substantiated by the purchased config alone.

Practical conclusion: they are bigger in distribution/community than POKROV's current beta footprint, but the observed paid network footprint from this key is small and possibly fragile.

---

## Competitive Implications For POKROV

Where MORI is strong:

- Very strong Telegram/community funnel.
- Store-visible Android app with meaningful install/review count.
- Clear, punchy claims: no account, no logs, VLESS Reality, TOR mode.
- Cheap monthly price and simple bot activation.
- Aggressive content cadence around Russian internet restrictions.

Where MORI looks weak:

- Claim consistency: public site, downloads page, news pages, Telegram posts, and purchased config do not fully agree.
- Reliability perception: visible complaints about unstable servers, keys, payment/support.
- The purchased subscription showed one endpoint, not a broad node pool.
- Endpoint location/ASN conflicts with their "outside RF jurisdiction" copy in this sample.
- Ecosystem/casino/token adjacency may reduce trust for conservative users.

Opportunities for POKROV:

- Be more boringly credible: publish fewer grand claims, but support each claim with current evidence.
- Make app status, platform support, and node geography explicit and honest.
- Position around trust, support, clean payments, and stable onboarding instead of hype.
- If POKROV has multiple real nodes and cleaner infra separation, that is a concrete advantage to surface carefully.

---

## Source Snapshot

Public sources:

- https://morivpn.com/
- https://morivpn.com/downloads.html
- https://play.google.com/store/apps/details?id=com.morivpn.mori_vpn_mobile
- https://www.appbrain.com/app/mori-vpn/com.morivpn.mori_vpn_mobile
- https://t.me/morivpnrobot
- https://telemetr.me/content/MoriVpnOfficial
- https://mori-news.com/vpn/
- https://moribonus.com/en/vpn
- https://otvet.mail.ru/question/269282112
- https://codeby.net/threads/server-vpn.84176/

Local passive checks:

- DNS: `Resolve-DnsName`
- CT logs: `crt.sh`
- Reachability: 5 ICMP pings per endpoint + one TCP 443 check per endpoint
- IP metadata: `ipinfo.io`

No port scan, brute force, vulnerability probing, authentication bypass, or traffic abuse was performed.

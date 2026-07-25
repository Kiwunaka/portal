# Telegram VPN wave 2 + Android APK analysis

**Research date:** 2026-07-12
**Telegram/TGStat snapshot:** 22:10–22:15 Moscow time
**Post window:** 2026-05-12 through 2026-07-12
**Scope:** new Telegram-first competitors not covered by the first 16 profiles, their channels, bot funnels, first-party applications and selected Android binaries
**Primary earlier report:** [final-market-report.md](final-market-report.md)

## Result

This pass found a second competitive layer that is larger than most of the original sample:

- HitVPN has the largest Telegram distribution observed: roughly 4.61M channel subscribers, 3.75M bot monthly users and +386K channel subscribers over 30 days.
- Sota and Lagom are the fastest app-backed growers in this wave at roughly +15% channel growth over 30 days.
- Batya has the most complete mass-market Telegram + branded app + cabinet funnel, but giveaways, incentivized reviews, privacy contradictions and fragmented legal identities weaken the signal.
- Atlanta has an unusually aggressive monetization stack: time subscription, traffic-metered whitelist bypass, referral bounty and a 50% partner program. Its own Android app is still tiny and the main bot remains dependent on Happ/V2rayTun.
- Durev combines a mature bot, site login, gifts and recurring referrals with a Povel Durev TON meme-token brand.
- MantaRay is the strongest Android product UX inspected in this wave. Kubik is the weakest trust case: debug-signed public release plus an extreme ad/attribution stack.
- HitVPN's bot was in maintenance during the live pass even though the channel had recently announced restoration. Scale did not prevent control-plane failure.

## Evidence labels

| Label | Meaning |
|---|---|
| `PASS_DIRECT` | Observed directly in Telegram Web, official site/store, public TGStat widget or emulator |
| `PASS_STATIC` | Extracted from the exact APK identified by size and SHA-256 |
| `PASS_EMULATOR_UI` | Installed and navigated in isolated Android emulator without creating a VPN tunnel |
| `PLAY_ONLY` | Official store listing verified; APK not obtained from a trustworthy first-party source |
| `BLOCKED_DOWNLOAD` | First-party binary was visible but could not be retrieved safely |
| `INFERENCE` | Analytical conclusion from cited observations, not a vendor fact |

## Expanded market snapshot

Public Telegram counters and TGStat image widgets can differ by tens or hundreds because they were captured minutes apart. Bot values are Telegram monthly users, not subscribers, customers or paid accounts.

| Competitor | Channel subscribers | Bot monthly users | 30-day channel change | Reach / ERR | Android footprint | Read |
|---|---:|---:|---:|---:|---|---|
| HitVPN | 4,607,630 | 3,752,595 | +386,200, about +9.1% | 2,236,043 / 48.5% | HitRay 10M+; HitVPN 1M+ | Largest distribution, giveaway-heavy, live outage |
| Shuka | 1,291,035 | 496,996 | +53,455, +4.3% | TGStat reach invalid/zero | MantaRay 10K+, generic client | Huge channel, low posting, strong client UX |
| Atlanta | 801,830 | 319,740 | +40,909, +5.4% | 210,089 / 26.2% | Atlanta app 1K+ beta | Distribution far ahead of own app |
| Sota | 794,734 | 436,732 | +105,221, +15.3% | insufficient TGStat data | Sota Connect 500K+ | One of the fastest growers |
| Batya | 185,484 | 176,626 | +11,776, +6.8% | 81,710 / 44.1% | Batya 1M+ | Strong integrated funnel; prize traffic |
| Lagom | 167,258 | 218,394 | +21,990, +15.1% | 108,701 / 64.9% | Lagom 5M+ | Strongest app-led challenger after HitRay |
| BlancVPN | 97,041 | 36,333 | +547, +0.6% | 61,334 / 63.2% | BlancVPN 100K+ | Mature product content, growth nearly flat |
| GenVPN | 69,612 | 11,887 | −301, −0.4% | 20,604 / 29.6% | Generator 50K+, last update 2024 | Dense content, weak current product signal |
| Durev | 58,111 | 193,755 | +2,205, +3.9% | 55,695 / 95.8% | Durev 100K+ | Bot-led; rare posting inflates ERR |

### TGStat evidence

The new metrics came from official public `stat-widget.png` images, not inferred from search snippets. Public `/stat` pages returned HTTP 403 without a fresh logged-in/API entitlement. The widgets expose channel size, daily/weekly/monthly delta, reach and ERR, but not full source-of-growth tables, demographic breakdown or quality of subscribers.

- [HitVPN widget](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-hitvpn-widget.png)
- [Shuka widget](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-shuka-widget.png)
- [Atlanta widget](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-atlanta-widget.png)
- [Sota widget](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-sota-widget.png)
- [Batya widget](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-batya-widget.png)
- [Lagom widget](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-lagom-widget.png)
- [Blanc widget](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-blanc-widget.png)
- [GenVPN widget](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-genvpn-widget.png)
- [Durev widget](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-durev-widget.png)

### What the metrics do and do not prove

- HitVPN is the absolute distribution leader in this set.
- Sota and Lagom lead relative monthly channel growth among app-backed competitors.
- Atlanta's own Android app at 1K+ installs is not yet proportional to an 800K channel.
- Durev's bot is more than three times its channel: it is a bot-led product, not a channel-led media funnel.
- Shuka's MantaRay installs cannot be counted as Shuka users. MantaRay publicly describes itself as a BYO-server client.
- HitRay and HitVPN installs cannot be equated to paid HitVPN customers; both are usable as generic configuration clients.
- ERR is not quality by itself. Rare posting can make Durev's 95.8% look exceptional, while stale or malformed TGStat input can make Shuka's reach invalid.

## New competitor discovery and prioritization

### Tier A — deep-profiled in this pass

| Service | Why it matters | App state |
|---|---|---|
| HitVPN | Extreme Telegram and Android distribution | Two branded/generic Android clients; direct APK currently broken |
| Shuka | 1.29M channel and low-cost referral trial | Uses MantaRay; ownership not proven |
| Atlanta | Multi-axis monetization and 800K channel | Own beta/Play app plus default third-party clients |
| Batya | Strong brand, cabinet and 1M+ Android app | Own Android/TV and Apple clients; Windows uses Happ |
| Durev | Mature bot, email-linked site and recurring referral | Own Android Play app; transferable-key ecosystem remains |
| FineVPN | Direct Telegram APK distribution | 43.3 MB beta visible; download blocked |

### Tier B — strong public candidates

| Service | Public signal | App/source state |
|---|---|---|
| Sota | 794K channel, 436K bot MAU, +15.3%/month | Sota Connect `org.interhive.sota.connect`, 500K+ |
| Lagom | 167K channel, 218K bot MAU, +15.1%/month | `com.lagomproductsllc.lagomvpn`, 5M+ |
| BlancVPN | Mature status/roadmap content | `com.blancvpn.app`, 100K+ |
| Velvet | About 409K channel and 373K bot MAU | Web cabinet; largely external clients |
| Liberty | About 153K bot MAU | Happ/Incy; no own client confirmed |
| Raketa | About 60K bot MAU and 160K channel | Mostly Happ/Incy in current posts |
| Vanya | About 107K bot MAU | `com.vanyavpn.android.client`, 1M+ |
| Bebra | About 59K bot MAU | `ai.bebra.android.client`, 1M+ |

### Tier C — APK/app leads retained for later

- ChatVPN — `net.chatvpn.app.wg.android`, Telegram PIN activation.
- LunoVPN — `com.lunovpn`, active bot/channel and official site.
- Paper VPN — `io.papervpn.android.app`, app-first with Telegram support.
- Planet VPN — `com.freevpnplanet`, older app-first provider with a Telegram key bot.
- VOSKHOD — first-party arm64 APK link, but the transfer stalled at zero bytes.
- OverSecure and Kubik — downloaded and analyzed below.

## Bot deep dives

### HitVPN

#### Observed flow

The bot had no operational purchase/menu path during the live check. It showed:

- “Сервис на обслуживании”;
- recovery announcements in `@hitvpn_news`;
- support at `@hitvpnhelp4`;
- a channel subscription CTA.

This was observed after the channel's 2026-06-30 “restored” message. The correct interpretation is a current regression on 2026-07-12, not proof that the service never recovered.

![HitVPN maintenance](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/hitvpn-bot-maintenance.png)

#### Product/app surface

- HitVPN Android: [`io.hvpn.android`](https://play.google.com/store/apps/details?id=io.hvpn.android), 1M+ installs, but its public update date is old relative to HitRay.
- HitRay Android: [`io.hitray.android`](https://play.google.com/store/apps/details?id=io.hitray.android), 10M+ installs and updated 2026-07-07.
- The official site also lists iOS HitWave and TV distribution.
- The exposed direct APK host had expired/broken TLS and did not deliver a verifiable file.

#### Read

`INFERENCE`: HitVPN is optimized for top-of-funnel scale, not resilience. A Telegram outage disables conversion, onboarding and account control for millions at once.

### Shuka VPN

#### Gate and cabinet

- Mandatory subscription to `@ShukaVPN`.
- Live bot count: 496,996 monthly users.
- Core claims: ad-free YouTube, all devices, privacy/flexible setup and 24 locations.
- Current prices: 3 days for 10 ₽, 1 month for 299 ₽, 3 months for 749 ₽.
- Cabinet branches: tariff, invite, gift, payment.
- Live location list includes ordinary global locations, Russian routing and multiple whitelist-specific routes.

#### Referral

- Inviter: 14 days + 20 GB whitelist traffic after referred trial activation.
- Referred user: 7 days for 10 ₽.
- Personal bot/site referral links were created during inspection and discarded.

![Shuka prices](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/shuka-pricing.png)

#### Read

The commercial bot is average; the recommended MantaRay client is excellent. The provider wins by borrowing a serious power-user client instead of forcing every platform into a shallow branded shell.

### Atlanta VPN

#### Full observed tree

```text
Mandatory channel gate + agreement
└─ Language: RU / EN
   └─ 3-day free activation
      ├─ iOS
      ├─ Android
      ├─ Android TV
      ├─ Windows
      └─ macOS

Main menu
├─ Buy VPN
│  ├─ RUB
│  │  ├─ 30 days — 199 ₽
│  │  ├─ 3 months — 449 ₽
│  │  ├─ 6 months — 899 ₽
│  │  └─ 12 months — 1,249 ₽
│  └─ Crypto — Heleket
├─ Profile
│  ├─ Balance: top-up / transactions / email
│  ├─ Keys: device → key detail → renewal / whitelist
│  ├─ Promo code
│  └─ Language
├─ Setup
│  ├─ iOS: Happ / Happ Plus
│  ├─ Android: Happ
│  ├─ Android TV: guide + remote-control app
│  ├─ Windows: Happ Desktop
│  └─ macOS: V2rayTun
├─ Invite friends
│  ├─ Referral: 50 ₽ + 30% of top-ups
│  └─ Partner: 50% of payments; payout from 3,000 ₽
└─ VPN not working
   ├─ switch country/server
   ├─ whitelist FAQ
   └─ @AtlantaHelp_Bot
```

#### Trial and key lifecycle

The free Android path issued a named key, expiry and private subscription URL. Key management exposes device category, created/expiry dates, renew and a second whitelist connection. No secret URL, referral code or Telegram identifier was saved.

#### Whitelist bypass as a separate product

- Base access: eight countries plus four mobile-operator routes according to FAQ.
- Add-on: 15 GB / 99 ₽ or 30 GB / 198 ₽.
- Two trial GB are free.
- The bot calls the add-on the most stable current white-list solution and uses Happ.

#### Partner warning

The partner page offers 50% of attributed payments and a 3,000 ₽ withdrawal threshold, while simultaneously warning that partner statistics are currently broken. That is a major trust defect inside the highest-risk commercial branch.

![Atlanta prices](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/atlanta-pricing.png)

#### Read

Atlanta is a good monetization teardown and a bad product-architecture model. The flow crosses Telegram, Telegraph, Happ, V2rayTun, a video channel, a beta app and a support bot.

### Batya VPN

#### Entry and tariff

- Five days free or immediate 20% sale.
- 299 ₽ / month, 699 ₽ / 3 months, 1,899 ₽ / year, 4,199 ₽ “forever.”
- One account/key is marketed for all devices; the legal fair-use text recommends five simultaneous devices for timed plans.
- “Forever” means only while the service exists and can provide the service.
- The 12-month landing discount math is inconsistent.

#### Live bot defect

The inspected account reproduced a hard recovery failure: `/start` attempted registration again and returned “Пользователь уже существует.” `/menu` and `/help` produced no response. This is not a cosmetic bug; it strands an existing account in the acquisition flow.

![Batya prices and error](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/batya-pricing.png)

#### Apps and cabinet

- Android/TV: [`ms.f2p.batyavpn`](https://play.google.com/store/apps/details?id=ms.f2p.batyavpn), 1M+ installs.
- iOS/iPadOS/macOS: App ID `6753714734`, public bundle `buddy.vpn`.
- Windows path: third-party Happ, not a Batya-branded binary.
- Cabinet supports email-link login independently of Telegram.

#### Privacy contradiction

Store declarations say no data is collected. Batya's own policy says the app/bot process Telegram ID, traffic volume, device type, OS and app version; the site also processes IP, cookies, browser fingerprint and behavior for advertising/measurement. This is a direct documentation conflict.

#### Legal/publisher fragmentation

- Service policy/offer: UNI PLAN TRADING LIMITED, Hong Kong.
- Google Play: F2P, OOO, Russia.
- Apple: Frederic Hennes Sprl / Buddy VPN.

These may be publishers or contractors, but the public chain of responsibility is not explained.

### Durev VPN

#### Main menu

- subscription management;
- purchase;
- referral;
- site login by email binding;
- channel;
- about/countries/legal/payment-safety;
- help and language.

#### Pricing

| Term | Price |
|---|---:|
| Trial day | 17 ₽ |
| 1 month | 459 ₽ |
| 3 months | 1,310 ₽ |
| 6 months | 2,414 ₽ |
| 1 year | 3,864 ₽ |
| 2 years | 5,244 ₽ |

Promo code and gift branches are adjacent to the tariff grid. No checkout was paid.

![Durev prices](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/durev-pricing.png)

#### Referral economics

- Reward choice: free days or money, both at 20% of referred purchase value.
- Referral is attached permanently after a qualifying purchase.
- New-user gift: three days to two months.
- Cash-out threshold: 5,000 ₽ / 50 USDT / 3,000 Stars.
- 48-hour refund hold before reward settlement.

#### Brand

The “About” page explicitly connects Durev VPN to the Povel Durev TON meme-token ecosystem and lists five alternate domains. This makes the brand highly memorable but couples a privacy product to speculative-token identity and domain fragmentation.

### FineVPN

#### Observed tree

- Languages: RU / EN / DE / FR / ES / CN.
- Services/order.
- Android app.
- Invite friend.
- Support.
- Partner.
- Settings.

The Android branch returned first-party Telegram document `FineVPN-apkProd-release-v1.0.0 (1).apk`, 43.3 MB, labeled beta.

![FineVPN beta APK](../../../competitor-profiles/raw/finevpn/2026-07-12/screenshots/bot-official-beta-apk.png)

Telegram Web could display the file but the controlled browser could not retrieve Telegram document media. No mirror was substituted, so no signing/SDK claims are made.

## Channel content: two-month marketing audit

| Channel | In-window volume | Dominant pattern | Aggression read |
|---|---:|---|---|
| HitVPN | 16 posts | 8 giveaway/result posts, 3 app posts, 2 crisis posts | Repeating iPhone loop tied to bot connection |
| Shuka | 1 post | Large release blast | Low cadence; dense product bundle |
| Atlanta | 5 posts | traffic-team recruitment + crisis/recovery | Aggressive affiliate/creator acquisition |
| Batya | 32 events, 24 normal posts | 21 giveaway/live/result events | Prizes dominate the brand's media surface |
| Raketa | 4 posts | news and third-party-client instructions | Low-pressure utility content |
| Velvet | 0 posts | channel silent in window | No current content engine |
| Liberty | 5 posts | political/education + private investment offer | Highest financial-risk message |
| BlancVPN | 7 posts | status, compensation, roadmap, own apps | Best mature product communication |
| GenVPN | 47 posts | status, holidays, offers, GEN PAY, polls | Highest cadence and tracked cross-sell density |

### HitVPN

- Repeated iPhone 17 Pro Max draws every one to two weeks.
- Entry requires channel subscription and VPN connection through the bot.
- Anti-fraud warnings are included in the offer loop.
- 2026-06-24: mass block, tariffs stopped, service temporarily free.
- 2026-06-30: recovery claimed and balances promised intact.

`INFERENCE`: its +386K monthly channel growth is commercially impressive, but prize traffic and forced funnel actions make “organic product demand” unknowable from the public metrics.

### Batya

- 199-prize campaign for paying users: MacBook Air, iPhones, AirPods, cash and subscriptions.
- Second campaign: 10 iPhones, 10 AirPods and ten 10,000 ₽ cash payouts for channel participation.
- +14 days for a store review submitted through a review bot.
- Five fear/newsjacking posts about blocks, foreign traffic pricing, MAX and Happ removal.
- Four outage/recovery messages around late-May blocks/DDoS claims, with +7 days compensation.

`INFERENCE`: store ratings are not a clean independent quality signal because the official channel materially rewards reviews.

### Atlanta

The key growth post recruits people to bring traffic from Telegram, TikTok, Shorts, Reels, YouTube, forums and communities for fixed payment plus bonuses. Three of five posts are crisis/recovery communication. The marketing system is labor/affiliate-heavy rather than content-led.

### Liberty

The channel offered private investment from 150,000 ₽ and claimed total annualized returns up to 170% depending on amount, while stating there are no guarantees. This is the most dangerous non-VPN monetization in the wave and should not be copied.

### BlancVPN

The best channel pattern in this batch:

- public incident/status communication;
- seven-day compensation;
- own-app updates;
- roadmap for split tunneling, Xray, family access and Windows;
- practical Happ/Karing/Incy fallback instructions;
- sale and referral attached to useful product content.

### GenVPN

The strongest high-frequency content machine:

- 47 posts in two months;
- almost every event maps to a tracked bot deep link;
- blocks become free “brigade” CTAs;
- holidays become sales;
- product content cross-sells GEN PAY virtual cards;
- public polls are used for visual and key-delivery product decisions.

The weakness is product freshness: the legacy Android app was last updated in 2024 and the current channel shrank slightly over the month.

## Official Android app inventory

| Service/app | Official source | Package/version visibility | Retrieval result |
|---|---|---|---|
| MantaRay | first-party Yandex Cloud + Play | `com.mantaray.vpn`, 2.25.8 | Downloaded, static + emulator |
| OverSecure | first-party vendor APK | `com.oversecure.vpn`, 1.1.7 | Downloaded, static + emulator |
| Kubik | first-party mutable `latest.apk` | `com.kubikvpn.app`, 1.2.4 | Downloaded, static + emulator |
| HitVPN / HitRay | Play + broken first-party APK host | `io.hvpn.android`, `io.hitray.android` | Direct APK blocked by TLS/host failure |
| FineVPN | Telegram document | 1.0.0 beta; Play `com.fineprotectapp.android` | Telegram document download blocked |
| Batya | Google Play | `ms.f2p.batyavpn` | `PLAY_ONLY` |
| Atlanta | Google Play + beta channel | `atlantavpn.bot` | `PLAY_ONLY`; app at 1K+ installs |
| Durev | Google Play | `com.durevpn.durevvpn` | `PLAY_ONLY` |
| Sota | Google Play | `org.interhive.sota.connect` | `PLAY_ONLY` |
| Lagom | Google Play | `com.lagomproductsllc.lagomvpn` | `PLAY_ONLY` |
| BlancVPN | Google Play | `com.blancvpn.app` | `PLAY_ONLY` |
| ChatVPN | Google Play | `net.chatvpn.app.wg.android` | `PLAY_ONLY` |
| LunoVPN | Google Play | `com.lunovpn` | `PLAY_ONLY` |
| VOSKHOD | first-party arm64 APK | package not recovered | download stalled and zero file removed |

No third-party APK mirror was treated as equivalent to an official binary.

## Exact downloaded APKs

| App | Local ASCII path | Size | SHA-256 |
|---|---|---:|---|
| OverSecure | `C:\Users\kiwun\AppData\Local\Temp\codex-vpn-wave2\oversecure\oversecure.apk` | 35,805,535 | `F3FC3DD14F92EF0837501345B050F91FBE56940A36688C842277A10D9B0EE167` |
| Kubik | `C:\Users\kiwun\AppData\Local\Temp\codex-vpn-wave2\kubik\kubik.apk` | 120,208,613 | `65C9E93EA4117BCC3319F6CAD5EF372F3A3057E474387A71D5026DCF609FAB52` |
| MantaRay | `C:\Users\kiwun\AppData\Local\Temp\codex-vpn-wave2\mantaray\mantaray.apk` | 160,872,388 | `2DAA9D98A1E9D7B974974FD3F6E6BD820FD31D857D2B43F9C15EDE34E1148BEC` |

The decompressed files, manifests, DEX/package indexes, native strings, UI dumps and emulator logs live under each app directory. These are temporary analysis paths, not committed release artifacts.

## APK comparison

| Dimension | OverSecure 1.1.7 | Kubik 1.2.4 | MantaRay 2.25.8 |
|---|---|---|---|
| Package | `com.oversecure.vpn` | `com.kubikvpn.app` | `com.mantaray.vpn` |
| SDK | min 24 / target 36 | min 24 / target 36 | min 24 / target 35 |
| Debuggable | false | false | false |
| Signature | v2, Oversecure LTD | v2, **Android Debug** | v2, MantaRay identity |
| Core | sing-box/SagerNet `libbox.so` | Flutter + sing-box `libbox.so` | first-party `libmantaray_core.so`, 5.13.1 FFI v2 |
| Ads/tracking | AppMetrica; no full ad stack found | extreme ad/attribution/mediation stack | no AD_ID/ad networks; FCM/ML Kit; first-party telemetry routes |
| Entry | subscription URL required | anonymous free plan | BYO subscription/config |
| Strongest UX | split tunneling | simple free home/server list | routing builder + diagnostics |
| Main risk | broad app visibility and sideload/update | debug signing + SDK overload | broad app/usage access + routing telemetry |

## OverSecure static and UI analysis

### Binary/security

- v2-only release signature, production-looking `Oversecure LTD` subject.
- `libbox.so`: about 39.5 MB arm64 and 36.9 MB armv7.
- AppMetrica present. Ad-revenue adapter shims are embedded inside AppMetrica, but full AppLovin/IronSource/AdMob/Fyber SDKs were not found.
- Sensitive permissions: AD_ID, Install Referrer, `QUERY_ALL_PACKAGES`, `REQUEST_INSTALL_PACKAGES`, notifications and special-use foreground service.
- First-party network surface: `oversub.cloud` paths `/fetch`, `/isp`, `/version`.

### Product/design

- Dark glass-like UI with a clear central connection model.
- Onboarding claims 67K+ active clients, 96% satisfaction, 30+ locations and 100+ servers.
- Two top-level modes: Standard and Bypass.
- DNS, LAN, stats, proxy-ping behavior and automatic server switch are exposed without overwhelming the home screen.
- Split tunneling has off/include/bypass modes and searchable app selection.
- Weak entry: user must already possess an `oversub.cloud/<token>` subscription URL.

| Home | Split-app selection |
|---|---|
| ![OverSecure home](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/app-oversecure-main.png) | ![OverSecure split apps](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/app-oversecure-split-apps.png) |

More: [onboarding](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/app-oversecure-onboarding.png), [settings](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/app-oversecure-settings.png).

## Kubik static and UI analysis

### Critical release defect

The public APK is signed with an Android Debug certificate. `debuggable=false` does not fix this. A debug signing identity undermines update provenance, incident response and any claim of production-grade release discipline.

### SDK surface

Confirmed components include:

- Appodeal and AppLovin;
- Yandex, Facebook, Amazon, InMobi, Vungle, Chartboost, Fyber, Smaato, Moloco, Start.io, BidMachine, PubNative, Bigo, Mintegral, Ogury, MobileFuse and MyTarget;
- IronSource/Unity mediation;
- Adjust, AppsFlyer, Firebase Analytics, AppMetrica and Sentry;
- Privacy Sandbox Topics/Attribution/Ad ID/Custom Audience permissions;
- billing, license check and OEM/store integrations.

This is not “a VPN app with analytics.” It is an ad-mediation container wrapped around a sing-box VPN client.

### Product/design

- Full privacy-policy wall with mandatory checkbox on first launch.
- Anonymous free plan: 60 minutes per session, 5 GB/month.
- Finland, Germany, Netherlands and Sweden shown in the free server list, with generated playful names and ping.
- Purple dark UI is coherent but generic.
- Premium offers 1/3/6/12 months and three devices, but did not show prices in the app and hands purchase to the site.
- Settings are shallow: legal, logs, theme.

| Home | Servers | Premium |
|---|---|---|
| ![Kubik home](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/app-kubik-home.png) | ![Kubik servers](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/app-kubik-servers.png) | ![Kubik premium](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/app-kubik-premium.png) |

More: [policy](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/app-kubik-policy.png), [profile](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/app-kubik-profile.png), [settings](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/app-kubik-settings.png).

## MantaRay static and UI analysis

### Binary/security

- v2-only signature with MantaRay production identity.
- First-party `libmantaray_core.so` for arm64, armv7 and x86_64; runtime marker 5.13.1 FFI v2.
- No AD_ID or ad networks.
- Firebase Messaging/Installations and ML Kit QR scanning. A tiny Analytics connector namespace exists, but the full Firebase Analytics SDK was not found.
- `api.mantatech.ltd` routes cover update, crash, AI chat/feedback/limits and routing telemetry.
- GeoIP/geosite assets and OpenWRT material are delivered from Yandex Cloud storage.
- Sensitive capabilities: package usage stats, query-all-packages, request-install-packages, camera, boot and multicast/Wi-Fi.

### Product/design

- Dark teal/blue visual with better information hierarchy than Kubik.
- Add config by manual link, clipboard or QR.
- Three plain-language routing presets:
  - VPN only where needed;
  - VPN everywhere except Russia;
  - VPN for everything.
- Four-step custom routing builder: mode, exceptions, sites/IPs, name.
- Per-rule actions: VPN, direct or block.
- Quick Settings tile, large/small widgets, simplified mode, self-update, geo database update and autoconnect.
- Diagnostics: VPN logs, session traffic, connection diagnostics, routing history/decision trace and app logs.
- First-run geo preparation took about 15–20 seconds. Update checking returned a 404 in logs but did not crash.

| Home | Routing presets | Custom builder |
|---|---|---|
| ![MantaRay home](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/app-mantaray-home.png) | ![MantaRay presets](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/app-mantaray-routing-presets.png) | ![MantaRay builder](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/app-mantaray-routing-builder.png) |

More: [add config](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/app-mantaray-add-config.png), [settings](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/app-mantaray-settings.png), [more settings](../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/app-mantaray-settings-more.png).

The one screenshot containing emulator HWID was excluded.

## Design ranking

This is an analytical score, not a measured benchmark.

| Dimension | MantaRay | OverSecure | Kubik |
|---|---:|---:|---:|
| Functional depth | 5/5 | 4/5 | 2/5 |
| Information architecture | 4/5 | 4/5 | 3/5 |
| Visual polish | 4/5 | 4/5 | 3/5 |
| Beginner entry | 3/5 | 2/5 | 4/5 |
| Local diagnostics | 5/5 | 3/5 | 2/5 |
| Privacy posture | 4/5 | 3/5 | 1/5 |
| Release trust | 4/5 | 4/5 | 1/5 |

Why:

- MantaRay is the only client that turns routing into a legible product instead of a settings dump.
- OverSecure is the cleanest focused subscription client but assumes the user already has a token URL.
- Kubik is easiest to start anonymously, but the free UX is financed by a supply-chain and tracking surface that overwhelms the product value.

## Cross-competitor marketing mechanics

| Mechanic | Strong example | Conversion benefit | Cost/risk |
|---|---|---|---|
| Mandatory channel gate | Shuka, Atlanta | immediate subscriber growth | fake audience quality, onboarding friction |
| Low-cost paid trial | Shuka 10 ₽, Durev 17 ₽ | payment-method qualification | reduces “free” promise clarity |
| Free trial | Atlanta 3 days, Batya 5 days | faster activation | abuse and low-intent traffic |
| Recurrent referral | Durev 20%, Atlanta 30% top-ups | compounding acquisition | payout liability and fraud |
| Partner program | Atlanta 50% | creator/affiliate scale | unit-economics and tracking disputes |
| Prize loop | HitVPN, Batya | huge subscriber spikes | low-quality audience and brand dependency |
| Review reward | Batya +14 days | rating volume | corrupts rating signal; store-policy risk |
| Crisis compensation | Batya, BlancVPN | churn reduction | requires operational honesty |
| Traffic-metered bypass | Atlanta | second monetization axis | complex value model and client fragmentation |
| Cross-sell | GenVPN → GEN PAY | raises LTV | distracts from core trust product |
| Meme/token brand | Durev | high memorability | speculative-finance trust coupling |

## Risk ranking

1. **Kubik — critical release/privacy risk.** Debug signing, mutable `latest.apk`, extreme ad/attribution stack and Privacy Sandbox permissions.
2. **HitVPN — critical operational concentration.** Millions of users, but bot control plane unavailable and direct APK host broken during inspection.
3. **Batya — high transparency/marketing risk.** Store privacy claims conflict with policy; legal/publisher fragmentation; incentivized reviews; prize-heavy growth; “forever” ambiguity.
4. **Atlanta — high commercial/complexity risk.** Broken partner stats, 50% payout promise, many external clients/surfaces and separate traffic billing.
5. **FineVPN — medium provenance risk.** Telegram beta APK without captured checksum/signing or stable release page.
6. **OverSecure — medium permission/provenance risk.** Broad app visibility and sideload/update permissions, but restrained SDK surface and sane signature.
7. **MantaRay — medium capability/privacy risk.** Strong client with broad package/usage access, self-update and routing telemetry; no ad stack.
8. **Durev — medium brand/domain risk.** Many mirrors and meme-token coupling, but coherent pricing/referral/help flows.

## What POKROV should copy

### P0 — product and trust

1. MantaRay's three plain-language routing presets and four-step custom builder.
2. Local route-decision history, diagnostics export and per-session traffic, with mandatory redaction.
3. One independent web cabinet for account recovery, billing, devices and key rotation.
4. Versioned first-party APK URLs plus SHA-256, signing fingerprint and changelog on a stable page.
5. CI release guard that rejects Android Debug certificates and unexpected SDK/permission growth.
6. Store privacy declarations generated from the same canonical data inventory as the product privacy policy.
7. An in-app incident banner/status page so Telegram outage cannot disable onboarding.

### P1 — growth and retention

1. Low-friction trial with abuse controls and clear conversion price.
2. One recurring referral model with visible attribution and payout ledger; no separate contradictory program.
3. Batya's recognizable human brand voice, without fake paternalism or fear spam.
4. BlancVPN's incident → status → action → compensation → recovery sequence.
5. GenVPN's public UX polls, but without attaching a tracked sales link to every post.
6. Atlanta's symptom-first support tree, collapsed into one product/support surface.

### P2 — distribution

1. Own Android and TV client before spending into a massive channel.
2. Store + versioned direct APK + Telegram fallback, all tied to the same certificate identity.
3. Creator/affiliate experiments only after cohort LTV, fraud and refund tracking are trustworthy.

## What POKROV should not copy

- HitVPN/Batya giveaway loops as the dominant content engine.
- Incentivized public store reviews.
- “Forever” access without explicit service-lifetime language next to the CTA.
- Liberty's private investment pitch.
- Atlanta's 50% partner promise while attribution statistics are broken.
- Mandatory channel subscription before the user can evaluate the product.
- Kubik's ad/attribution stack or debug release certificate.
- Mutable `latest.apk` without immutable version and hash.
- FineVPN-style Telegram APK as the only provenance surface.
- Expired TLS on a critical download host.
- Store “no data collected” labels that contradict the privacy policy.

## State changes and safety boundary

- Joined Shuka and Atlanta channels because the bot gates required it; user authorization was explicit.
- Activated one Atlanta three-day trial and generated one temporary Android key.
- Did not preserve subscription URLs, referral codes, Telegram ID, QR payloads, payment tokens or emulator HWID.
- Did not complete a payment, request a payout, submit an email, message support, connect a VPN tunnel, delete an account or publish externally.
- Emulator was used only for local UI/static validation.

## Limitations

- Deleted/private Telegram posts cannot be recovered from public history.
- TGStat public widgets do not expose demographics or full acquisition-source tables. Logged-in deep quota for new channels remained unavailable after the earlier pass.
- Google Play-only APKs were not replaced with third-party mirrors.
- HitVPN's direct APK failed because of the first-party host/TLS state.
- FineVPN's APK document was visible but Telegram Web media download was unavailable.
- VOSKHOD's first-party transfer stalled at zero and was discarded.
- Static SDK presence does not prove a code path executes at runtime. No MITM/network interception was performed.
- No claim is made about real VPN speed, unblock success, backend capacity or production tunnel stability.

## Profiles and raw evidence

- [HitVPN](../../../competitor-profiles/hitvpn.md)
- [Shuka VPN](../../../competitor-profiles/shuka-vpn.md)
- [Atlanta VPN](../../../competitor-profiles/atlanta-vpn.md)
- [Batya VPN](../../../competitor-profiles/batya-vpn.md)
- [Durev VPN](../../../competitor-profiles/durev-vpn.md)
- [FineVPN](../../../competitor-profiles/finevpn.md)
- [OverSecure](../../../competitor-profiles/oversecure.md)
- [Kubik VPN](../../../competitor-profiles/kubik-vpn.md)
- [MantaRay](../../../competitor-profiles/mantaray.md)
- [Sota VPN](../../../competitor-profiles/sota-vpn.md)
- [Lagom VPN](../../../competitor-profiles/lagom-vpn.md)
- [BlancVPN](../../../competitor-profiles/blancvpn.md)
- [GenVPN](../../../competitor-profiles/genvpn.md)
- [Redacted session ledger](../../../competitor-profiles/raw/market-wave2/2026-07-12/scrapes/session-notes.md)

## Primary public sources

- [HitVPN channel](https://t.me/s/hitvpn_news), [site](https://hitvpn.me/), [HitRay Play](https://play.google.com/store/apps/details?id=io.hitray.android)
- [Shuka release](https://t.me/ShukaVPN/34), [site](https://shuka.site/), [MantaRay Play](https://play.google.com/store/apps/details?id=com.mantaray.vpn)
- [Atlanta channel](https://t.me/s/AtlantaVPN), [Atlanta Play](https://play.google.com/store/apps/details?id=atlantavpn.bot)
- [Batya channel](https://t.me/s/mybatyavpn), [site](https://batyavpn.com/), [Play](https://play.google.com/store/apps/details?id=ms.f2p.batyavpn)
- [Durev site](https://durevpn.com/), [Play](https://play.google.com/store/apps/details?id=com.durevpn.durevvpn)
- [BlancVPN channel](https://t.me/s/blancvpn), [Play](https://play.google.com/store/apps/details?id=com.blancvpn.app)
- [GenVPN channel](https://t.me/s/vpngen), [Play](https://play.google.com/store/apps/details?id=org.iedn.vpngenerator)
- [Sota Play](https://play.google.com/store/apps/details?id=org.interhive.sota.connect)
- [Lagom Play](https://play.google.com/store/apps/details?id=com.lagomproductsllc.lagomvpn)
- [Official TGStat widget documentation](https://api.tgstat.ru/docs/ru/widgets/stat-image.html)

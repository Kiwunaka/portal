# Mobile VPN Competitor Audit - Coverage Log

**Snapshot date:** 2026-07-22
**Environment:** LDPlayer 14, Android emulator `emulator-5554`, 900x1600 app viewport
**Branch/worktree:** `codex/vpn-competitor-app-audit` / `.worktrees/vpn-competitor-app-audit`
**Execution rule:** one competitor active at a time; force-stop it before moving to the next.

This file is the durable progress ledger for the installed-app audit. Detailed findings live in one profile per competitor. Raw screenshots, UI trees, package metadata, documents, and redacted technical evidence live under `competitor-profiles/raw/`.

**Cross-competitor synthesis:** [сравнение, рейтинг механик и 30/60/90-дневный план для POKROV](./_comparative-synthesis-2026-07-22.md)
**Feature catalog:** [335 уникальных фич и приоритеты POKROV](./_pokrov-feature-catalog-2026-07-22.md)

## Inventory And Coverage

| # | Competitor | Android package | Installed version | Current coverage | Profile |
| --- | --- | --- | --- | --- | --- |
| 1 | HiroVPN | `com.hiro.vpn` | 1.18.0 | **DEEP PASS COMPLETE WITH BLOCKERS:** core app, growth, store/release, web, legal and technical surfaces captured; cooldown/payment/current-registry blockers remain explicit | [hiro-vpn.md](hiro-vpn.md) |
| 2 | Огонь VPN | `com.ogonconnect.app` | 0.84 | **DEEP PASS COMPLETE WITH BLOCKERS:** core app, paywall, locations, bypass, live tunnel, feedback, Telegram status/acquisition history (including incentivized 5-star campaign), Play creatives/recommendations, dual-domain web/legal, Russian publisher and static architecture captured; historical cadence and authoritative Georgian status remain blocked | [ogon-vpn.md](ogon-vpn.md) |
| 3 | Батя VPN | `ms.f2p.batyavpn` | 1.3.9 | **DEEP PASS COMPLETE WITH BLOCKERS:** native UX, failed connection, pricing, cabinet/TV, store/reviews, legal/entities, full public docs/channel timeline and redacted static artifact recorded | [batya-vpn.md](batya-vpn.md) |
| 4 | ВПН / Vanya VPN | `com.vanyavpn.android.client` | 1.20.6 | **DEEP PASS COMPLETE WITH BLOCKERS:** no-key UX, support/purchase/legal/mirror destinations, growth, store/release/distribution, entities and static connected-state architecture captured; real connection requires a key and live US-registry refresh remained blocked | [vanya-vpn.md](vanya-vpn.md) |
| 5 | Kakadu | `com.matrena.vpn` | 2.4.6 | **DEEP PASS COMPLETE WITH BLOCKERS:** isolated auth and both failed login routes, web/store/legal/entity contradictions, release cadence, Telegram growth, recommendation graph and redacted signed-in architecture captured; live product/connection remain blocked by backend auth | [kakadu-vpn.md](kakadu-vpn.md) |
| 6 | Durev VPN | `com.durevpn.durevvpn` | 2.0.1-phone | **DEEP PASS COMPLETE WITH BLOCKERS:** isolated key/import UX, authorized no-account email result, public web/store/legal/entity/channel/release surfaces and redacted static architecture captured; signed-in product/connection require a paid key | [durev-vpn.md](durev-vpn.md) |
| 7 | Космос VPN | `ru.space.vpn` | 1.3.3 | **DEEP PASS COMPLETE WITH BLOCKERS:** email registration, signed-in native UX, server list, TV pairing, cabinet/growth, real tunnel, current stores/releases/channel, legal contradictions and redacted static architecture captured; current Armenian status and Apple TV handoff remain blocked | [kosmos-vpn.md](kosmos-vpn.md) |
| 8 | GnuVPN | `com.gnu.vpn` | 1.8.7 | **DEEP PASS COMPLETE WITH BLOCKERS:** anonymous/account UX, no-card trial, 59 countries, split tunneling, protocols/custom servers, eSIM cross-sell, support, live tunnel, pricing/refunds/referrals, all 43 current English FAQ pages, stores/releases, legal/privacy/security contradictions and redacted static architecture captured; current Portuguese registry status and Huawei metadata remain blocked | [gnuvpn.md](gnuvpn.md) |
| 9 | BlancVPN | `com.blancvpn.app` | 1.7.0 | **DEEP PASS COMPLETE WITH BLOCKERS:** passwordless auth, native UX/paywall/locations/protocols/routing/account controls, static release architecture, 176-page public surface/all 99 Russian help articles, stores/releases/recommendations, distribution, Telegram/status, reviews, legal/entity and UX health captured; live tunnel is paywalled, checkout is region-blocked and persisted routing state needs a clean-device retest | [blancvpn.md](blancvpn.md) |
| 10 | Ping VPN | `com.pingsecure.client.app` | 1.1.19 | **DEEP PASS COMPLETE WITH BLOCKERS:** repeatable backend-bootstrap failure, feedback/cancel flow, official connected/location/settings/routing creatives, 233-service routing catalog, monetization/claim conflicts, release cadence, Play reviews/recommendations, 718K-subscriber Telegram growth loop, Russian entity/BFO and redacted static architecture captured; live product/tunnel remain blocked | [ping-vpn.md](ping-vpn.md) |
| 11 | Proton VPN | `ch.protonvpn.android` | 5.19.66.0 | **DEEP PASS COMPLETE WITH BLOCKERS:** guest/paid-preview flows, real WireGuard tunnel, Play, APK/provenance, source/release pipeline, site funnel/SEO, Swiss entities, ownership, legal/privacy, support and trust drift captured; direct 2026 audit-PDF and desktop-Chrome visual pass remain blocked | [proton-vpn.md](proton-vpn.md) |
| 12 | TipTop VPN | `com.free.tiptop.vpn.proxy` | 1.036 | **DEEP PASS COMPLETE WITH BLOCKERS:** native UX/account/tasks/growth, pricing/settings/support, stores, controlled sing-box tunnel failure and Wi-Fi recovery, static package, public funnel, legal/entities and release/distribution mapped; Chrome visual pass, live checkout and current registry ownership/status remain blocked | [tiptop-vpn.md](tiptop-vpn.md) |
| 13 | Red Shield VPN | `com.redshieldvpn.app` | v4.3.6 | **DEEP PASS COMPLETE WITH BLOCKERS:** native/account/paywall/settings/locations/growth/support, unpaid connect gate, APK architecture, Play/App Store/extensions, public funnel/mirrors, docs, release lanes, legal policies, Florida operator and TgVPN/Scottish lineage captured; paid tunnel and desktop-Chrome visual pass blocked | [red-shield-vpn.md](red-shield-vpn.md) |
| 14 | ExpressVPN | `com.expressvpn.vpn` | 12.71.0 | **DEEP PASS COMPLETE WITH BLOCKERS:** consent/carousel, Play paywall/trial/retention, secure login/recovery/restore, static phone/TV architecture, protocols/settings/tools/suite, Play/App Store/extension, pricing/referral, release lanes/cadence, legal ownership, privacy and trust proof mapped; paid Home/tunnel, desktop-Chrome visual pass and current Expressco registry record blocked | [expressvpn.md](expressvpn.md) |
| 15 | Pipster | `com.vipin.pipster` | 2026.7.7 | **DEEP PASS COMPLETE WITH BLOCKERS:** anonymous/ad/tunnel/repair/static/store/legal/referral architecture complete; live account values blocked by OTP delivery | [pipster.md](pipster.md) |
| 16 | CyberGhost | `de.mobileconcepts.cyberghost` | 8.40.0 | **DEEP PASS COMPLETE WITH BLOCKERS:** consent, hard paywall/login, hidden pre-auth privacy/VPN/Wi-Fi controls, support/legal/company, APK, store/release, account ecosystem, referrals and trust program captured; paid home/server/tunnel remain blocked by suspended Google Play payments in Russia | [cyberghost.md](cyberghost.md) |
| 17 | Lagom VPN | `com.lagomproductsllc.lagomvpn` | 0.21-mobile | **DEEP PASS COMPLETE WITH BLOCKERS:** onboarding/auth/support/store/legal/static covered; home/paywall/tunnel blocked by broken account creation; clean teardown | [lagom-vpn.md](lagom-vpn.md) |
| 18 | AdGuard VPN | `com.adguard.vpn` | 2.16.65 | **DEEP PASS COMPLETE WITH BLOCKERS:** consent/auth, free and paid UX, 79/80-location live catalog, dual exclusions, DNS/protocol/diagnostic controls, three controlled connection failures, Play/recommendations, web/legal/entity, release/distribution, TrustTunnel and redacted static architecture captured; healthy tunnel, current registry extract and complete store-artwork pass remain blocked | [adguard-vpn.md](adguard-vpn.md) |
| 19 | 4ebur.net | `com.cheburnet.mobile` | 5.1.0 | **DEEP PASS COMPLETE WITH BLOCKERS:** native/product/web/Mini App/store/legal/static pass complete; free VLESS crashes before `tun0` on x86_64 | [4ebur-net.md](4ebur-net.md) |
| 20 | VPN Наружу | `online.vpnnaruzhu.client.android` | 1.8.1 | **DEEP PASS COMPLETE WITH BLOCKERS:** no-card trial, native Smart/Direct product, paywall, support/FAQ, three controlled connections, Play/web/guides/Telegram/release machine, multi-jurisdiction legal drift, direct APK/Windows and static architecture captured | [vpn-naruzhu.md](vpn-naruzhu.md) |
| 21 | MORI VPN | `com.morivpn.mori_vpn_mobile` | 2.0.5 | **DEEP PASS COMPLETE WITH BLOCKER:** current Play/store/site/Telegram/instructions/legal/static/release audit complete; native `x86_64` launch is blocked by a Play split missing `libflutter.so`, so no live connection test was possible | [mori-vpn.md](mori-vpn.md) |
| 22 | Quattro VPN | `ru.quattrocloud.vpnapp` | 0.18.1 | **DEEP PASS COMPLETE WITH BLOCKER:** direct/debug APK provenance, x86_64 ABI crash, static product, separate Play client/publisher, email-verified cabinet, pricing, 281-server catalog, instruction graph, full public release history, Telegram growth, npvpn platform relation and service legal operator captured; native UI/tunnel remain blocked by the installed build | [quattro-vpn.md](quattro-vpn.md) |

The original sixteen packages and the first five additions report Google Play as installer in the observed emulator state. Quattro reports LDPlayer's privileged `com.android.coreservice`; the installed artifact is Android Debug-signed and is therefore treated as a sideload/test build, not a Play build. Its `0.18.1` version matches the public Telegram/Yandex direct-release version, but exact binary identity was not verified. The original source inventory is retained in [`raw/_device/2026-07-22/packages/`](raw/_device/2026-07-22/packages/).

## Audit Contract Per App

Before an app is marked complete, record:

- package, version, store identity, developer, install/review scale, latest update and visible changelog;
- onboarding, permissions, trial, sign-in/registration and account management;
- home, connection states, locations, special servers and routing/split-tunneling controls;
- pricing, tiers, payment methods, renewal/refund copy and paywall destinations;
- every tab, settings page, FAQ/help/support flow and meaningful empty/error state;
- growth mechanics: referrals, rewards, ads, reviews, social quests, promo codes and cross-sells;
- every observed external destination and whether the app verifies the promised action;
- legal entity, document mapping, governing law, privacy/logging claims and contradictions;
- one real connect/disconnect smoke test when safe, with no raw credentials or connection material retained;
- accepted current-session screenshots and exact blockers for anything not reached.

## Data Hygiene

- Test-account email addresses, passwords, one-time codes, OAuth account screens, QR authorization payloads, personalized referral/start links, device identifiers, advertising identifiers, current/public exit IPs, raw tokens, configs/endpoints and raw provider payloads are not retained in this worktree. Public operator/support contacts reproduced in first-party legal documents are kept as source evidence.
- Screenshots are accepted only after visual inspection. Blank, loading, duplicate, mislabeled and PII-bearing captures are excluded from the final evidence set.
- No purchases, reviews, ratings, likes, public posts or support messages are submitted during the audit.

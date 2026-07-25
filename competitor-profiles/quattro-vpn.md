# Quattro VPN — Competitor Profile

**Main service:** https://quattro.app/<br>
**Snapshot:** 2026-07-22<br>
**Status:** `DEEP PASS COMPLETE WITH NATIVE BLOCKER`<br>
**Installed Android package:** `ru.quattrocloud.vpnapp`<br>
**Installed version:** `0.18.1` (`versionCode 19`)<br>
**Installed artifact:** direct/debug sideload initiated by LDPlayer CoreService; not Google Play-proven

## Current verdict

Quattro is the most important late addition to this audit. It is not the cleanest VPN, but it has the largest visible Telegram distribution, the fastest feedback/release loop and one of the deepest Russian-blocking product models in the set.

- Public Telegram preview shows 1.06M news subscribers and 550,879 monthly bot users.
- Its service is more than a VPN app: bot, synchronized web cabinet, configurable subscription, 281-entry server catalog, LTE traffic economy, routing presets, referral/partner/promo infrastructure, instructions and direct APK releases.
- The product appears to run on the npvpn white-label/infrastructure stack; Quattro's advantage is distribution, packaging, operational tempo and local routing knowledge rather than a wholly proprietary client core.
- The installed own Android build is materially broken on the observed x86_64 emulator and debug-signed. It cannot reach Flutter UI because the packaged Flutter engine is ARM-only for that path.
- Google Play contains another Quattro package that is a generic bring-your-own-config client with 1K+ installs and no own servers. It is a separate product line, published through a legal-services company unrelated to the service operator named in Quattro's own documents.
- The black/red cabinet looks confident and coherent, but current trust hygiene is weak: product-line confusion, retrofitted operator paperwork, contradictory retention/third-party language, no visible registration/payment consent, incomplete referral copy and silent tariff-selection failures.

The lesson for POKROV is blunt: **copy Quattro's owned funnel, operational speed, local routing taxonomy and distribution discipline. Do not copy its artifact hygiene, identity fragmentation or legal/UX shortcuts.**

## At a glance

| Metric | Current observation |
| --- | --- |
| Own Android app | Direct APK `0.18.1`; open beta since 2026-04-29 |
| Own app store state | Package `ru.quattrocloud.vpnapp` not found in Google Play |
| Installed runtime | Crashes before first Flutter frame on observed x86_64 LDPlayer |
| Play client | Separate package `quattrovpn.app`, 1K+ installs, last update 2026-07-01 |
| News channel | 1.06M subscribers shown |
| Main bot | 550,879 monthly users shown |
| Support bot | 32,753 monthly users shown |
| Instruction group | 83,138 members; 16,660 shown online |
| Base cabinet price | 300 RUB / 30 days / 5 devices / 500 GB metered LTE |
| Longer plan | 900 RUB / 90 days / 5 devices / minimum 1,500 GB LTE |
| Payment methods | SBP, Russian bank card, cryptocurrency |
| Server catalog | 281 displayed entries |
| Service operator | ИП Иорданов Самвел Ашотович, Russia |
| Play publisher | ООО «АК «Алькасар»», Russia, via label `VPNdeveloper` |
| Infrastructure/platform signal | npvpn white-label stack; evidence-backed inference |

## The critical product split

Quattro currently has two Android identities that must not be merged in analysis.

### 1. Main service application

`ru.quattrocloud.vpnapp` is the direct-distribution app seen in Telegram releases and installed in LDPlayer.

- accepts Quattro subscription activation;
- contains server, routing, DNS, IP-strategy, split-app/URL, paywall, referral and security-tool logic;
- includes Firebase Analytics/Crashlytics;
- contains Quattro account/auth/service domains;
- is distributed as Telegram attachment plus Yandex mirror;
- matches the black/red service identity;
- is not currently listed under its package ID in Google Play.

### 2. Generic Play client

`quattrovpn.app` is a different bring-your-own-config client.

- 1K+ installs;
- VLESS, VMess, Trojan, Shadowsocks and SOCKS;
- import by URL, QR and clipboard;
- subscription refresh, ping/sort, routing/DNS, IPv6, per-app VPN, VPN/proxy mode and local SOCKS5;
- explicitly says it provides no VPN servers;
- claims no advertising, trackers or registration;
- uses a light, generic power-user interface unlike the service cabinet/app identity.

The Play client may be a strategic store-safe fallback/configurator, a white-label publishing experiment or simply a parallel asset. Quattro does not explain the relationship publicly. For users, the same name/icon currently means two different privacy models and product promises.

## Native Android result

The installed build launches its Android splash, initializes Firebase/Crashlytics and terminates before Flutter paints a screen.

Logcat's decisive failure is an ABI mismatch: the available `libflutter.so` is `EM_AARCH64`, while LDPlayer requests `EM_X86_64`. The APK advertises x86_64 and contains a large x86_64 `libnpvpnBox.so`, but lacks a valid x86_64 Flutter engine/application pair.

Therefore these paths are `BLOCKED_BY_BUILD` on this device:

- onboarding and activation;
- native Home/Servers/Favorites;
- paywall and ad-supported connection;
- Quattro Security tools;
- routing/DNS/IP strategy;
- settings, feedback and referral UI;
- VPN permission and live tunnel;
- DNS/HTTPS/route/leak/speed validation.

No `tun0` appeared. The process was force-stopped and the emulator returned to a clean no-VPN state.

This finding is scoped to the installed debug sideload on x86_64. It does not prove that the ARM build fails on physical Android devices.

Detailed evidence: [`runtime-failure-summary.md`](raw/quattro-vpn/2026-07-22/runtime-failure-summary.md).

## What the APK contains

The internal namespace `npvpn_project`, native library `libnpvpnBox.so`, embedded npvpn domain and leaked local build path tie the app to an npvpn-based implementation.

Observed product surface:

- automatic server selection, favorites, ping and color-coded latency;
- VLESS, VMess, Trojan, Shadowsocks, WireGuard and Hysteria2-related paths;
- custom DNS and IPv4/IPv6 strategy;
- split tunnelling by installed application and URL/service;
- direct/VPN/blacklist rules;
- Quick Settings tile;
- own and third-party Xray-style configurations;
- dark/light themes and adaptive layouts;
- subscription/paywall, advertising abstraction and remote configuration;
- rating/feedback/update/share/referral flows;
- safe browser, breach check, URL scanner and password generator.

The routing corpus is unusually deep: 233 curated service presets and large SRS/GeoIP/GeoSite rule packs for services, countries, Russian direct/blocked sets, advertising and content categories.

Notable trust signals:

- Firebase Analytics, Crashlytics and Sessions are present;
- advertising ID/attribution permissions are declared;
- `allowBackup=false`;
- `quattro://auth` deep link;
- a debug-level settings asset and local control API with a bundled static token; the token is redacted and not retained.

Full static map: [`static-summary.md`](raw/quattro-vpn/2026-07-22/static-summary.md) and [`ui-copy-map.md`](raw/quattro-vpn/2026-07-22/ui-copy-map.md).

## The npvpn platform underneath

`npvpn.com` sells exactly the stack Quattro appears to use:

- global VPN infrastructure;
- white-label applications;
- business/growth tooling;
- operational automation;
- launch in days rather than months;
- scale from 100 to 100,000+ users;
- flexible/revenue-share commercial model.

Its Telegram preview claims 100+ launched bots and turnkey VPN bots/servers/VLESS-Xray. Quattro's internal package naming and public operating model match this offer closely.

This is strategically important. Quattro demonstrates that a competitor can buy/assemble infrastructure and still build a formidable moat through distribution, local routing intelligence, content, support and fast iteration. POKROV should not fetishize owning every low-level component; it should own the product truth, release quality, customer relationship and high-value orchestration.

## Web cabinet audit

An empty email-verified account was created solely to inspect the product. No Telegram account was linked, no promo applied, no trial/payment started and no support message sent.

### Navigation

| Section | Observed state |
| --- | --- |
| Главная | Subscription status, purchase CTA, optional Telegram linking |
| Оплата | Duration/device/LTE configurator and three payment methods |
| Рефералы | Invite and paid-conversion counts, site/bot links |
| Партнёрская программа | Current account has no program; new enrollment unavailable |
| Промокод | Input to grant days or traffic |
| Серверы | 281 read-only entries |
| Инструкции | Platform, routing, refresh and second-device cards |
| Настройки | Account/email, Telegram, email 2FA, password/email change |
| Документы | Five legal documents plus support bot |

### Visual system

The cabinet is a good reference:

- near-black surfaces with restrained red accent;
- thin borders and low-key grid/glow background;
- consistent left navigation and card hierarchy;
- readable primary controls and strong selected state;
- very little decorative clutter.

Weaknesses:

- wide desktop view leaves roughly half the page unused;
- secondary text is low contrast;
- server catalog becomes an unfiltered wall of rows;
- parts of the product rely on emoji as taxonomy;
- incomplete/silent states are not handled honestly.

The account experience feels like a serious operator console. The Play client feels like an unrelated generic app. Brand coherence stops at the store boundary.

## Pricing and subscription mechanics

Current cabinet selection:

- 30 or 90 days;
- 5, 10 or 15 devices;
- 500, 1,000, 1,500, 3,000 or 5,000 GB LTE traffic;
- SBP, Russian bank card or cryptocurrency.

Observed 30-day/five-device totals:

| LTE traffic | Price |
| ---: | ---: |
| 500 GB | 300 RUB |
| 1,000 GB | 450 RUB |
| 1,500 GB | 600 RUB |
| 3,000 GB | 1,050 RUB |
| 5,000 GB | 1,650 RUB |

Device increments are simple: ten devices cost 450 RUB at the base 30-day/500-GB configuration; fifteen cost 600 RUB.

The 90-day plan starts at 1,500 GB and 900 RUB for five devices. The selector exposes 500/1,000 GB as apparently enabled, but clicks are silently ignored. The explanatory line updates the minimum only after a valid higher plan is active. This is exactly the kind of invisible constraint POKROV should avoid.

Policy copy says:

- ordinary servers are unlimited;
- only LTE servers without an “unlimited” label consume the meter;
- traffic rolls over and can be purchased later;
- 0.5x/0.1x server labels reduce meter consumption;
- Gemini/Google AI works on star-marked servers;
- torrenting is allowed only on Torrent-marked servers;
- torrent/device-limit violations can cause blocking without refund;
- mobile-operator compatibility is not guaranteed and is not refundable.

The bundle copy promises a seven-day free period, cancel-anytime subscription and an ad-supported connection. None of those paths was visible in the July cabinet. Treat them as stale/configurable APK copy rather than current commercial truth.

## Server model

The cabinet displays `Серверы (281)` with several conceptual layers:

- automatic fastest and automatic LTE locations;
- ordinary high-speed locations;
- Hysteria2 variants;
- Torrent-marked servers;
- Russian locations including Moscow, Saint Petersburg, Yekaterinburg and Khabarovsk;
- LTE unlimited fallbacks;
- metered 0.1x/0.5x LTE servers;
- specialized Gemini/AI and gaming labels;
- SNI, Shadowsocks, WebSocket and gRPC labels;
- a long virtual/global country catalog.

This is powerful proof-of-breadth copy, but not good selection UX. There is no visible search, filter, grouping control, latency/load state or explanation of which entries are physical versus routed/virtual. POKROV should copy the human task labels and cost coefficients, not the raw 281-row dump.

## Instructions and recommended clients

The cabinet routes users to a large Telegram instruction group. Cards cover:

- Android/iOS activation;
- Android TV with Happ recommended and v2RayTun alternative;
- Windows/macOS/Linux client import;
- routing on Android/TV and desktop;
- subscription refresh;
- second-device handoff.

Public long-form pages cover NekoBox activation, NekoBox process/domain routing, a very large Russian direct list, PC troubleshooting and FAQ. Old Teletype links in channel posts now 404 while equivalent `blog.quattro-info.ru` pages work.

Observed client recommendations:

- Happ;
- v2RayTun;
- Streisand;
- NekoBox;
- sing-box;
- Mihomo;
- Clash-compatible clients;
- Incy;
- Throne;
- Quattro's own Android beta.

This fallback strategy is excellent. Quattro does not wait for one native client to cover every OS/protocol. It owns the subscription/configuration relationship, then gives users a supported client matrix.

Detailed destination map: [`instruction-link-map.md`](raw/quattro-vpn/2026-07-22/instruction-link-map.md).

## Growth machine

Quattro's growth stack is one of the strongest in the audit:

- campaign-attributed bot and website links on release posts;
- referral stats and rewards after a paid qualifying purchase;
- cash/commission partner lane;
- promo codes with scarcity limits;
- referral contests with cash and annual plans;
- bonuses spendable on subscription days and traffic;
- secret payment methods/tariffs and a teased hidden on-site reward;
- public compensation after outages;
- status/news/tutorials/release notes in the same channel;
- direct links to correct client/store builds to defeat fake search results;
- support hiring as the user base scales.

The current referral page has a production bug: the sentence describing reward days/traffic omits the values. The March channel states seven days for both parties after a 30-day purchase, while APK strings mention a free month and permanent access after ten invites. This is a live example of config/copy drift.

Unlike Hiro's game economy, Quattro's strongest growth mechanics are operational and transaction-linked rather than purely gamified. That makes them easier to ship and harder to dismiss as fluff.

## Release and distribution machine

Quattro is Telegram-first:

```text
channel changelog → APK attachment + Yandex mirror
                 → bot/site/support links with campaign tags
                 → open feedback → fast hotfix
```

Major observations:

- service launched publicly by June 2025;
- 10K bot users by 2025-10-20;
- web cabinet launched 2026-04-22;
- own Android beta `0.9.0` launched 2026-04-29;
- major `0.16` on 2026-07-01;
- `0.18` on 2026-07-07;
- `0.18.1` hotfix on 2026-07-08.

The team communicates outages, operator blocking, payment mismatches, DDoS/server failures and product changes with unusual speed. It also repeatedly tells users to refresh subscriptions, rotate servers or delete the old app before installing a new one.

What is strong:

- direct distribution survives store risk;
- release notes explain user-visible changes;
- mirrors and support destinations are in every post;
- third-party clients keep other platforms alive;
- public incident cadence reduces uncertainty.

What is weak:

- debug-signed release artifact;
- x86_64 ABI packaging failure;
- “delete old version first” instead of reliable in-place update/migration;
- no signed release page, fingerprint, reproducible provenance or stable/beta separation;
- APKs mixed into a giant public news channel rather than a clean versioned download hub.

Full timeline: [`release-history.md`](raw/quattro-vpn/2026-07-22/release-history.md).

## Legal and ownership map

### Main service

Current documents name ИП Иорданов Самвел Ашотович, OGRNIP `325237500492810`, INN `237205496500`. The current registry profile shows an active microenterprise registered 2025-11-13 with IT as the principal activity.

The public service existed and had 10K bot users before that registration. Current paperwork may represent an operator migration; no prior operator was identified in the reviewed current documents.

### Google Play lane

Google Play names `AK ALKASAR, OOO`. The exact address matches active ООО «АНТИКРИЗИСНАЯ КОМПАНИЯ «АЛЬКАСАР»», OGRN `1164350058355`, INN `4345440296`, a Kirov legal-services company.

The same publisher account contains Quattro VPN and Tmg premium VPN. This is consistent with a shared/white-label publisher lane, but does not prove service ownership.

### Main legal terms

- refund request within seven calendar days;
- no refund after even one successful VPN connection;
- unresolved technical failure must last 72 hours; mass outage over 24 hours;
- review in three working days, extendable to ten; return up to 30 days;
- consent includes Telegram identity, optional email/support details, IP/time/device/error and payment metadata;
- processors and technical contractors may receive data;
- retention in consent: service term plus three years.

Material conflicts:

- privacy says delete after service; consent says three more years;
- privacy says no transfer without explicit written consent; consent allows processors/contractors;
- bot privacy says no third-party analytics; direct app includes Firebase;
- generic bundled app terms do not name the current operator;
- registration/payment have no visible inline consent checkbox.

The legal surface is better than having nothing, but it looks added after scale rather than designed with the product.

## Claim and identity contradictions

- One Quattro package provides a paid service/own servers/account; the Play package says no servers/no registration.
- Installed service APK has Firebase/advertising permissions; Play client claims no trackers/ads. Both can be true only because they are different packages, but the consumer is not told that.
- Telegram/direct APK distribution is the real service release lane while the shared Play name suggests store availability.
- The service operator and Play publisher are unrelated legal entities with no public responsibility map.
- Current cabinet pricing is days/devices/LTE traffic; APK copy still advertises 1/3/6/12 months and seven-day free/ad-supported paths.
- Referral rewards differ among current broken cabinet copy, March channel copy and APK strings.
- Privacy/consent retention and third-party rules conflict.
- The service claims 200+/281 locations; the catalog mixes ordinary, bridge, protocol, LTE and likely virtual/routed entries, so count is not a physical-server proof.

## What POKROV should copy

### Immediate

1. **Owned account graph:** bot and website synchronized around one subscription identity.
2. **Job-based routing:** fastest, ordinary, LTE fallback, AI/Gemini, gaming, Torrent, RU-direct and app/site splits.
3. **Third-party client matrix:** own configuration/subscription contract, supported fallback apps per platform/protocol.
4. **Instruction hub:** platform cards plus long-form troubleshooting/routing guides.
5. **Operational channel:** status, releases, incidents and compensation in one subscribed surface.
6. **Campaign attribution:** bot/site source tags on every public release or acquisition post.
7. **Configurable entitlement:** duration, devices and special-network traffic as explicit axes.
8. **Server cost transparency:** 0.1x/0.5x/unlimited labels make constrained infrastructure understandable.

### After the core is reliable

1. referral bonuses spendable on days/traffic;
2. promo codes and partner tracking;
3. self-service subscription refresh/reissue and device-limit expansion;
4. security-tool cross-sell only if the tools are real and maintained;
5. a hidden reward/easter egg only after odds, eligibility and value are explicit.

## What POKROV should not copy

- Android Debug signing for a public build;
- claiming x86_64 support without shipping a usable Flutter engine;
- forcing users to uninstall before every upgrade;
- two unrelated products under one package name/icon without explanation;
- a generic white-label Play client that breaks the premium brand;
- 281 servers without search/filter/ping/availability;
- invalid choices that silently do nothing;
- referral copy with missing reward values;
- raw proxy/config endpoints in public posts;
- “no refund after one connection” as the main trust posture;
- registration/payment without visible terms/privacy acknowledgement;
- legal operator, publisher, controller and platform provider hidden behind separate documents.

## Recommended POKROV response

### P0 — beat Quattro on release integrity

- production signing and published fingerprint;
- stable/beta channels;
- ABI/device matrix in CI;
- in-place migrations and rollback;
- versioned download hub with hashes and changelog;
- independent connection smoke before release;
- no green “connected” until tunnel + DNS + HTTPS + route health pass.

### P1 — match its Russian product depth

- Fastest plus Video/AI/Social/Gaming/RU-direct presets;
- split by app, domain/IP and direct/VPN/blocked mode;
- remote rule catalog with visible update/version;
- special-network fallbacks explained in user terms;
- live searchable server catalog with load/ping/status.

### P2 — match its funnel

- account/bot/site synchronization;
- device/session/subscription/receipt/promo/referral hub;
- direct signed APK mirror plus supported external clients;
- Telegram or owned inbox for incidents/releases;
- self-service reissue, renewal, location and device controls;
- referral reward only after paid conversion and refund window.

### P3 — beat it on trust

- one responsibility page naming brand owner, operator, data controller, seller, payment agent, store publisher, signer and infrastructure processor;
- one machine-readable product-facts source for price, trial, devices, traffic, server count and refund terms;
- field-level privacy/retention table;
- explicit registration/payment consent;
- no tracker/no-log claim broader than the audited package actually supports.

## Product ranking inside the 22-app set

- **Distribution/growth:** #1 visible Telegram machine.
- **Russian blocking/local routing relevance:** top tier with Огонь, Vanya, Батя and VPN Наружу.
- **Account/operations:** top tier; cabinet breadth is stronger than most native apps.
- **Native release quality:** bottom tier for the observed artifact because it is debug-signed and cannot start on advertised x86_64.
- **Trust/identity clarity:** below average because service app, Play app, operator, publisher and platform provider are not reconciled.
- **Visual packaging:** strong cabinet and channel identity; weak store/client coherence.

## Evidence gallery

### Runtime blocker

![Quattro Android splash before ABI crash](./raw/quattro-vpn/2026-07-22/screenshots/01-launch-400ms.png)

### Separate Google Play client

![Quattro generic Play client](./raw/quattro-vpn/2026-07-22/screenshots/12-google-play-current-top.png)

### Distribution and release cadence

![Quattro Telegram channel and 0.18.1 release](./raw/quattro-vpn/2026-07-22/screenshots/24-news-channel.png)

### Cabinet

![Quattro payment configurator](./raw/quattro-vpn/2026-07-22/screenshots/40-cabinet-payment.png)

![Quattro server catalog](./raw/quattro-vpn/2026-07-22/screenshots/44-cabinet-servers.png)

![Quattro instruction hub](./raw/quattro-vpn/2026-07-22/screenshots/45-cabinet-instructions.png)

### White-label platform signal

![npvpn infrastructure offer](./raw/quattro-vpn/2026-07-22/screenshots/08-npvpn-home-middle.png)

## Evidence index

- [`runtime-failure-summary.md`](raw/quattro-vpn/2026-07-22/runtime-failure-summary.md)
- [`static-summary.md`](raw/quattro-vpn/2026-07-22/static-summary.md)
- [`ui-copy-map.md`](raw/quattro-vpn/2026-07-22/ui-copy-map.md)
- [`public-surface-summary.md`](raw/quattro-vpn/2026-07-22/public-surface-summary.md)
- [`release-history.md`](raw/quattro-vpn/2026-07-22/release-history.md)
- [`instruction-link-map.md`](raw/quattro-vpn/2026-07-22/instruction-link-map.md)
- [`screenshots/`](raw/quattro-vpn/2026-07-22/screenshots/)

## Audit boundaries

- One empty account was created with the user-authorized Gmail connector only to inspect the cabinet. No email was sent, deleted, archived or relabeled.
- No purchase, auto-charge trial, Telegram binding, promo, referral conversion, review, post or support message occurred.
- The hidden-site bonus teased in the April launch post was not discovered by read-only UI inspection and common harmless easter-egg interactions; it is not described as verified.
- The own app's native product/tunnel remains `BLOCKED_BY_BUILD` on x86_64.
- No raw email, OTP, password, personalized referral link, account ID, API token, config, endpoint or current/public exit IP is retained in the worktree.
- The unrelated `quattro-vpn.ru`/Abrek product and ambiguous Qu/Quattro Chrome extension are explicitly separated from the confirmed service.

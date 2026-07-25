# Quattro VPN — current public surfaces

**Observed:** 2026-07-22<br>
**Method:** read-only Chrome audit, one empty email-verified cabinet account, public Telegram/Google Play/legal-registry evidence, local APK inspection

## Two different Android products use the same brand

### Quattro service application

- Package: `ru.quattrocloud.vpnapp`.
- Current public direct release: `0.18.1` through Telegram plus Yandex Object Storage mirror.
- Provides Quattro-owned subscription activation, server selection, routing, referral/security-tool/product logic.
- Embedded Firebase Analytics/Crashlytics, account/auth domains and npvpn white-label signals.
- Its Google Play URL returns “not found”.
- Installed artifact is Android Debug-signed and crashes on the observed x86_64 emulator.

### Google Play client

- Package: `quattrovpn.app`.
- Developer label: `VPNdeveloper`.
- 1K+ installs; last updated 2026-07-01; no visible rating.
- Generic configuration client: VLESS, VMess, Trojan, Shadowsocks, SOCKS, link/QR/clipboard import, subscription refresh, latency tests, routing, DNS, IPv6, per-app VPN, VPN/proxy mode and local SOCKS5.
- Listing explicitly says it has no own VPN servers and requires the user's own provider/configuration.
- Listing promise: no ads, trackers or registration.
- Google Play Data Safety says no collection/sharing and encryption in transit.
- Google Sites privacy policy, effective 2026-06-15, names only `VPNdeveloper`; it says no collection/logging/storage, no registration and only ephemeral IP transmission for connectivity.

The Play gallery is a generic light power-user client with profile groups, protocol badges, share/edit/delete controls and a navigation drawer. It does not resemble the black/red Quattro cabinet or the static design assets in the direct service APK. This is not merely a store build variant; the product promise, package, privacy footprint and server ownership are different.

## Google Play publisher

Play's “About developer” block identifies `AK ALKASAR, OOO`, at the same Kirov address as active Russian company ООО «АНТИКРИЗИСНАЯ КОМПАНИЯ «АЛЬКАСАР»»:

- OGRN `1164350058355`, INN `4345440296`;
- registered 2016-03-24;
- director/sole founder: Лючанду Константин Анатольевич;
- principal activity: legal services (`69.10`);
- microenterprise, no listed trademark or software/VPN license in the reviewed registry profile.

The same Play publisher has exactly two visible applications: Quattro VPN and `Tmg premium VPN`. The latter had 1+ installs, was updated 2026-07-15 and declares device/other identifiers may be shared. This looks like a small shared/white-label publisher lane. The evidence does not prove that ООО «АК «Алькасар»» operates the main Quattro service; the service's own legal documents name a different operator.

## Main service operator and documents

Current service documents name ИП Иорданов Самвел Ашотович:

- OGRNIP `325237500492810`, INN `237205496500`;
- registered 2025-11-13 in Krasnodar Krai;
- principal activity `62.09` (other IT/computing activities), with telecommunications/system-management/e-commerce additions;
- current registry profile says active and included as a microenterprise.

The current operator was registered after the public service launch and after the October 2025 10,000-user milestone. This may indicate a later operator migration; no earlier operator is named in the reviewed current documents.

Public legal pages were published 2026-03-19 and show a 2026-07-02 update date:

- Privacy Policy;
- Terms of Use;
- Refund Policy;
- Public Offer;
- Personal Data Processing Consent.

Material terms:

- VPN access is sold through Telegram bot/site with own servers, configurations and support.
- P2P is allowed only on explicitly marked locations.
- Refund request window is seven calendar days, but no refund is available after even one successful VPN connection.
- Technical-failure refund requires 72 hours unresolved by support or a mass outage over 24 hours.
- Review target is three working days, extendable to ten; money return may take up to 30 days.
- Consent covers Telegram ID/username, optional email/support data, tariff, IP/time/device/error data and transaction metadata, with payment processors/technical contractors allowed.
- Consent retention is service duration plus three years.

Document contradictions:

- Privacy says data is stored for the service period and then deleted; consent says another three years.
- Privacy says no third-party transfer without written consent; consent explicitly allows processors/contractors.
- Privacy says no third-party analytics in the Telegram bot; the separate direct Android app contains Firebase Analytics/Crashlytics. The bot/app scopes differ, but the consumer-facing separation is unclear.
- Cabinet registration and payment selection showed no visible privacy/terms acceptance checkbox or inline document link; legal documents are only in a separate sidebar section.

## Website and authenticated cabinet

`quattro.app` is an account application, not a marketing homepage. Logged-out states are Login, Registration and Password Reset. Registration requires email/password and email OTP; no visible consent checkbox is present.

An empty registered account exposes:

- dashboard with subscription state and optional Telegram linking;
- 30/90-day plan configurator, 5/10/15 devices, 500–5000 GB LTE packages and SBP/card/crypto payment methods;
- referral counters and personalized site/bot invite links;
- partner status; new enrollment currently unavailable;
- promo-code activation;
- read-only catalog of 281 named server entries;
- instruction hub;
- email/Telegram/2FA/password/email settings;
- legal-document/support hub.

Current base price is 300 RUB for 30 days, five devices and 500 GB metered LTE traffic. Ordinary servers and LTE servers marked unlimited do not consume the meter. The page promises unlimited speed and broad device compatibility, but explicitly excludes mobile-operator compatibility from refunds.

The server page presents strong quantity proof but weak usability: 281 rows, no visible search, filters, grouping controls or ping/load state. The page mixes auto entries, ordinary/Hysteria2/Torrent locations, unlimited LTE, 0.1x/0.5x metered LTE, SNI/SS/WS/GRPC labels and a long virtual-location catalog.

The referral page currently renders an incomplete sentence where reward day/traffic values are missing. The 90-day price selector also leaves invalid lower-traffic buttons looking enabled while silently ignoring them.

## Telegram scale and funnel

- News: 1.06M subscribers.
- Main bot: 550,879 monthly users.
- Support bot: 32,753 monthly users.
- Instruction group: 83,138 members and 16,660 shown online.

The funnel is owned and tightly cross-linked:

```text
News/content → attributed bot or site link → payment/account
             → subscription URL → recommended client or own Android app
             → instruction group / support bot
```

Bot/site links use per-post attribution parameters. Channel content combines operational alerts, legal documents, proxy availability, client recommendations, tutorials, infrastructure claims, promos and rapid APK changelogs.

## npvpn relationship

The embedded `npvpn.com` site describes a complete VPN infrastructure provider offering global infrastructure, white-label applications, business/growth tools and operational automation, claiming launch in days and scale from 100 to 100,000+ users. Its sole conversion path is Telegram. The Telegram preview claims 100+ launched bots and turnkey VPN-bot/server work.

The relationship to Quattro is an evidence-backed inference, not a declared ownership statement: installed library `libnpvpnBox.so`, `npvpn_project` source namespace, embedded npvpn domain and an operational surface matching npvpn's offer.

## Namesakes and ambiguous extensions

- `quattro-vpn.ru` is a separate Abrek VPN affiliate/landing product. All main CTAs route to `@abrekvpnBot`; its pricing, Windows client and unlimited-device claims must not be attributed to the audited Quattro service.
- Chrome extension ID `pdmchlannmelcagdkakcefmbmpogcgfo` currently appears as “Qu VPN”; indexed history/snippets also call it Quattro VPN and report around 10K users/version `3.0.6`. No link to `quattro.app`, the service bot or current legal operator was found. Treat it as an unverified namesake/possible former brand asset, not confirmed service distribution.

## Visual assessment

- Cabinet: cohesive black/red system, Inter-like typography, restrained glow/grid, clear navigation and solid card hierarchy. It feels more premium than most Telegram-first VPN dashboards.
- Weaknesses: excessive unused desktop width, very long unfiltered server list, low-contrast secondary text, incomplete referral copy and silent invalid selections.
- npvpn: strong editorial/minimalist yellow/black B2B page with giant typography. It sells infrastructure competence more convincingly than Quattro's own login-only domain.
- Play client: visually generic/light and disconnected from the service brand. The store listing makes Quattro look like a configuration-tool clone rather than the million-subscriber service shown by Telegram.

## Evidence images

- [`12-google-play-current-top.png`](screenshots/12-google-play-current-top.png)
- [`13-google-play-support-expanded.png`](screenshots/13-google-play-support-expanded.png)
- [`18-play-privacy-policy.png`](screenshots/18-play-privacy-policy.png)
- [`19-service-privacy.png`](screenshots/19-service-privacy.png)
- [`20-public-offer.png`](screenshots/20-public-offer.png)
- [`21-refund-policy.png`](screenshots/21-refund-policy.png)
- [`22-data-consent.png`](screenshots/22-data-consent.png)
- [`23-main-telegram-bot.png`](screenshots/23-main-telegram-bot.png)
- [`24-news-channel.png`](screenshots/24-news-channel.png)
- [`34-service-operator-registry.png`](screenshots/34-service-operator-registry.png)
- [`35-play-publisher-registry.png`](screenshots/35-play-publisher-registry.png)
- [`37-unrelated-quattro-vpn-ru.png`](screenshots/37-unrelated-quattro-vpn-ru.png)
- [`48-play-publisher-portfolio.png`](screenshots/48-play-publisher-portfolio.png)

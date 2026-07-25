# Quattro VPN — instruction and destination map

**Observed:** 2026-07-22

## Cabinet instruction cards

| Card | Copy / recommendation | Destination |
| --- | --- | --- |
| Android / iOS | Install a client, then scan QR or paste subscription link | Telegram instruction topic `QuattroVPN_INSTRUCTIONS/6` |
| Android TV | Happ recommended, v2RayTun alternative | Happ topic `7/239`; v2RayTun topic `7/33` |
| Windows / macOS / Linux | Install desktop client and import subscription | Telegram instruction topic `8` |
| Routing — Android / Android TV | VPN only for selected apps | Telegram topic `34/130` |
| Routing — desktop | VPN only for selected apps | Telegram topic `34/224` |
| Refresh subscription | Refresh in client after renewal | Telegram topic `194/195` |
| Second device | Copy subscription URL and open on another device | Telegram topic `231/232` |

The Telegram instruction group is publicly previewable and shows 83,138 members/16,660 online, but topic bodies are not readable in the public web preview without Telegram. The cabinet links themselves are verified.

## Public long-form guides

- [`NekoBox activation`](https://blog.quattro-info.ru/nekobox): create a subscription group, paste the bot/cabinet URL, update, select server, start TUN and enable automatic subscription refresh every 60 minutes.
- [`NekoBox routing`](https://blog.quattro-info.ru/nekobox_routing): per-process and per-domain routing, rule-set syntax, direct/VPN defaults and a very large Russian direct/allowlist domain list.
- [`PC troubleshooting`](https://blog.quattro-info.ru/fixpc): check another VPN/proxy, Zapret conflicts, antivirus/firewall, date/time, admin rights, stale app/subscription, mobile-hotspot failure, unavailable server and finally Windows network reset.
- [`FAQ`](https://blog.quattro-info.ru/FAQ): bot payment, subscription handoff, additional devices, PC/router setup, stale expiry/server lists, referrals, device counting and subscription reissue.

Old `teletype.in/@quattrovpn/...` URLs for routing and PC repair currently return 404; the same slugs under `blog.quattro-info.ru` work. This is a live link-migration defect in older channel posts.

## Recommended third-party clients

Observed recommendations by platform/use case:

- Happ: primary iOS/Android TV fallback, server-status checking, Russian App Store direct link and global App Store fallback by changing region when the RU listing disappears;
- v2RayTun: older/default path, but Quattro publicly tracks its breakages;
- Streisand: alternative for checking working locations;
- NekoBox: desktop activation and advanced process/domain routing;
- sing-box, Mihomo and Clash: automatic direct routing for Russian services; rule mode required for Clash/Mihomo;
- Incy and Throne: named Hysteria2-compatible clients;
- the own Quattro Android app: open beta/direct APK path from April 2026.

## Website/cabinet route map

| Route | Purpose |
| --- | --- |
| `/` | Login or authenticated dashboard |
| `/register` | Email/password registration and email OTP |
| `/reset-password` | Email password reset |
| `/subscription` | 30/90-day plans, device and LTE traffic configuration, SBP/card/crypto |
| `/referral` | Invite/payment counters and site/bot referral links |
| `/partner` | Partner-program status; new enrollment currently unavailable |
| `/promo` | Promo-code activation for days/traffic |
| `/servers` | Read-only catalog of 281 named entries |
| `/instructions` | Platform/routing/refresh/second-device link hub |
| `/settings` | Email, Telegram link, email 2FA, password/email change |
| `/terms` | Legal-document hub and support link |

Email 2FA is disabled by default on the newly registered empty account. No Telegram account was linked, no promo applied and no payment/trial started.

## Current cabinet pricing and policy copy

- 30 days, five devices, 500 GB LTE: 300 RUB.
- Ten devices adds 150 RUB; fifteen adds another 150 RUB.
- LTE packages increase in 500 GB steps at 150 RUB per step: 500/1000/1500/3000/5000 GB display 300/450/600/1050/1650 RUB for 30 days/five devices.
- 90 days requires at least 1500 GB and starts at 900 RUB/five devices.
- Selecting visibly enabled 500/1000 GB buttons on a 90-day plan is silently ignored; the summary remains at the valid higher amount. This is a UX defect.
- Ordinary servers are unlimited; metered traffic is spent only on LTE servers without an “unlimited” label and rolls over.
- Torrent use is allowed only on explicitly marked servers; device-limit violations and other-server torrenting threaten blocking without refund.
- Mobile-operator compatibility is explicitly not guaranteed and is excluded from refunds.

## Screenshots

- [`38-cabinet-telegram-modal.png`](screenshots/38-cabinet-telegram-modal.png)
- [`39-cabinet-home.png`](screenshots/39-cabinet-home.png)
- [`40-cabinet-payment.png`](screenshots/40-cabinet-payment.png)
- [`42-cabinet-partner.png`](screenshots/42-cabinet-partner.png)
- [`43-cabinet-promo.png`](screenshots/43-cabinet-promo.png)
- [`44-cabinet-servers.png`](screenshots/44-cabinet-servers.png)
- [`45-cabinet-instructions.png`](screenshots/45-cabinet-instructions.png)
- [`47-cabinet-documents.png`](screenshots/47-cabinet-documents.png)

Referral and settings screenshots containing personalized identifiers are retained only in the sensitive temporary evidence area, not in the repository.

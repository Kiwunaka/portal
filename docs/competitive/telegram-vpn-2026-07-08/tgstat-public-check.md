# TGStat public channel check

Date: 2026-07-08

This pass used TGStat public channel pages in the form `https://tgstat.ru/channel/@username`.

Important access note:

- `https://tgstat.ru/channel/@username/stat` still shows the auth wall in the in-app browser: `Для доступа к этой странице необходимо авторизоваться`.
- The public channel page without `/stat` works and exposes channel card, bio links, and recent publications.
- TGStat did not expose bot pages via `https://tgstat.ru/bot/@username`; tested bot URLs returned 404. Bot MAU should still be taken from public `t.me/<bot>` cards.

## Checked Channels

| Channel | TGStat result | Latest useful public signal |
| --- | --- | --- |
| `@catsvpn` | Found | 2026-06-29: Happ returned to App Store; promo code `HAPP` gives 15% off. 2026-06-17: launch of `lk.catsvpn.net`. |
| `@NosokVPN` | Found | 2026-06-19: service restored after infrastructure rebuild; promo `BESTNOSOKVPN`; bot may lag under load. 2026-05-14: Telegram-only access remains after subscription expiry. |
| `@QuattroVPN_NEWS` | Found | 2026-07-08: `Quattro 0.18.1.apk`, Android update with UI/status-bar/power-button fixes. |
| `@vpnplatina` | Found | 2026-07-05: referral payouts by term: 50/80/150/250 RUB; payout to card or GRAM/TON. |
| `@lumavpn_landing` | Found | 2026-06-27: +7 locations, explicit RTT/ping claims; TGStat public page shows 125.6k views on the post. |
| `@net4ebur` | Found | 2026-07-06: update across all platforms; pushes website for platform list. 2026-06-24: Happ removed from Russian App Store and region-change guide. |
| `@MoriVpnOfficial` | Found | 2026-07-07: long educational/security post about DNS leaks, WebRTC, browser fingerprinting, cookies, logins. |
| `@followNeo` | Not found | TGStat says channel `@followNeo` is not found. NEO still needs Telegram/t.me direct checking. |
| `@nashvpnnews` | Found | 2026-07-05: explains user complaints as RKN/DNS resolver issue, not server ban. 2026-07-04: asks users to update subscription daily. |
| `@opengate_community` | Found | 2026-07-07: added `AUTO — Англия` autobalancer, updated protocol, MTProto proxy/support links. |
| `@VPN_GROZA_NEWS` | Found | 2026-06-29: Happ returned to Russian App Store; warns about fake apps; links bot/support/instruction/news. |

## What Changed vs Previous Notes

- Luma is more interesting than it looked from the channel name. TGStat public page confirms very high post views: 125.6k on a 2026-06-27 infrastructure post, 105.6k on a 2026-06-26 server-capacity post. This is not just a tiny proxy channel.
- Quattro is still the most mature public-update machine. It had a same-day update on 2026-07-08, which keeps the channel feeling alive and product-driven.
- Nash has unusually blunt incident language. It directly says complaints were caused by RKN killing DNS resolution paths, not NashVPN servers.
- OpenGate is close to Quattro in operational tone, but lower scale: concrete server/autobalancer/protocol language and support paths.
- MORI uses educational posts as marketing, not only promos. This is a different content lane from discount/urgency channels.
- `@followNeo` should not be evaluated via TGStat unless the channel is added/found there; keep direct Telegram evidence for NEO.

## TGStat Limits

- Full charts, subscriber dynamics, ER, and detailed ad efficiency remain behind TGStat auth on `/stat`.
- Closing/reopening the in-app browser did not make TGStat auth stick for `/stat`.
- Public pages are still useful for recent publication proof and channel metadata.

## Evidence

Raw TGStat public screenshots are in:

- `docs/competitive/telegram-vpn-2026-07-08/screenshots-wave2/tgstat-public-*.png`

Raw extracted JSON:

- `docs/competitive/telegram-vpn-2026-07-08/screenshots-wave2/tgstat-public-results.json`

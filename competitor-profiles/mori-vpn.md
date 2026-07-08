# MORI VPN - Competitor Profile

**URL**: https://morivpn.com/
**Generated**: 2026-07-05
**Depth**: deep passive OSINT + one purchased subscription endpoint, redacted

---

## At A Glance

| Metric | Value |
| --- | --- |
| Product | MORI VPN / MORIVPN |
| Main positioning | VPN + TOR, zero-logs, no account, VLESS + Reality |
| Main funnel | Telegram bot `@MoriVpnRobot` + Android Google Play app |
| Public Android scale | Google Play: 50K+ installs, 1.41K reviews, 4.7 shown on Play; AppBrain: 52K downloads, 1.36K reviews, 3.45 |
| Telegram bot scale | `@morivpnrobot`: 44,594 monthly users observed |
| Telegram channel scale | Telemetr: 92,019 subscribers, 19,984 views/post, 22.53% ER observed |
| Paid subscription endpoint observed | 1 VLESS Reality endpoint in purchased subscription |
| Observed paid endpoint host | `zucchiniservice.ru:443`, SNI `api.zucchiniservice.ru` |
| Observed paid endpoint IP | `87.239.111.167` |
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
- `ru.api.morivpn.com`, `ru.morivpn.com`: `176.125.241.102` observed, geolocated by ipinfo to Stockholm / AS200019 ALEXHOST SRL.
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
| Address | `zucchiniservice.ru` |
| Port | `443` |
| SNI | `api.zucchiniservice.ru` |
| Fingerprint | `random` |
| Label | Contains `N/A` and `@mori`; unique user/config id redacted |

DNS and reachability:

| Host | A record | Ping sample | TCP 443 |
| --- | --- | --- | --- |
| `zucchiniservice.ru` | `87.239.111.167` | 5/5, avg 15.6 ms | OK |
| `api.zucchiniservice.ru` | `87.239.111.167` | 5/5, avg 10.6 ms | OK |
| `www.zucchiniservice.ru` | `87.236.16.20` | not endpoint | not endpoint |

CT names for `zucchiniservice.ru`:

- `zucchiniservice.ru`
- `api.zucchiniservice.ru`
- `www.zucchiniservice.ru`

HTTP/TLS note:

- `zucchiniservice.ru` and `api.zucchiniservice.ru` return HTTP 200 with an old WebThemez/TIMES HTML template on normal HTTPS.
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

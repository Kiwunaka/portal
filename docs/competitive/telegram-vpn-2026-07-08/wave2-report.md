# Telegram VPN competitors, wave 2

Date: 2026-07-08

Scope: second pass from the attached TGStat-style ranking, the 4ebur screenshot, public Telegram/TGStat pages, websites, and Telegram bot previews. Full TGStat analytics still showed an auth loop in the in-app browser after Telegram bot authorization, so the ranking metrics below use the attached export plus public TGStat/channel cards.

## Selection

I filtered for competitors that are useful to POKROV, not just large:

- real acquisition scale: subscribers, 7-day growth, post reach, bot monthly users
- product maturity: website, cabinet, app, support, proxy/recovery surface
- conversion mechanics: trial, referral, promo, forced channel subscription, payment/incident comms
- messaging pressure: Telegram blocking, App Store removals, white-list bypass, RKN incidents

Shortlist:

| Priority | Competitor | Why it matters |
| --- | --- | --- |
| 1 | Quattro VPN | Huge channel, 455k bot monthly users, own Android app, web cabinet, frequent release notes, traffic/LTE economy. |
| 2 | Nosok VPN | 203k channel, website with login, proxy fallback, emergency Telegram access after expiry, multi-level referral. |
| 3 | Cats VPN | Best web/cabinet idea: anonymous short-code account, bot-to-site import, clean tariff UI, 50% referral. |
| 4 | VPN PLATINA | Fast growth, 63k bot monthly users, separate digital goods bot, cash/TON referral payouts. |
| 5 | Luma VPN | Smaller channel but anomalous reach; app-store/app-first lane worth a focused follow-up. |

Parked for later: STRIKE, SOKOL, NBB, Batya, Kyra, ENOT, NEXYON, Za VPN, Perets. Some are large or have weird reach/citation, but the public surfaces found so far are less differentiated than the five above.

## Cats VPN

Sources: `@catsvpn`, `@CatsVPN_robot`, `https://catsvpn.net/`, `https://lk.catsvpn.net/`, `https://tgstat.ru/channel/@catsvpn/stat`.

What they have:

- Telegram channel: about 17.7k subscribers on public card; attached export says +4,458 in 7 days and 10.5k reach.
- Bot preview: about 29.8k monthly users.
- Website: `catsvpn.net`, claims 40,000+ users, no logs, 10+ locations, Happ/v2raytun import.
- Cabinet: `lk.catsvpn.net`, brand `catsconnect`.
- Login model: no email/password. New account is a short code generated on the site. The site forces the user to save the code before continuing.
- Cabinet sections: profile, tariffs, invoices, referrals, import.
- Bot-to-site bridge: import code lets existing Telegram users move subscriptions into the web account.
- Tariffs observed: 1 month 149 RUB, 3 months 399 RUB, 6 months 799 RUB, 1 year 1,399 RUB. One device, unlimited, white-list bypass.
- Referral: 50% forever from each invited user's payments.

Last two months public posts:

- 2026-06-17: launched `lk.catsvpn.net`; positioning is "VPN not only in Telegram" and a fix for the loop "to install VPN, you need VPN".
- 2026-06-24: HAPP removed from Russian App Store; short instruction to change App Store region.
- 2026-06-29: HAPP available again; promo code `HAPP` for 15% off.
- Older but still relevant: white-list bypass, RKN/VLESS/Xray blocking, free 3-day trial, Telegram proxy.

Bot gate:

- `/start` stops at "subscribe to our channel and press Check".
- To go deeper from Telegram, the account must join `@catsvpn`. I did not join without explicit permission.

Useful pattern for POKROV:

- The anonymous code login is the strongest idea in this wave. It makes the web cabinet independent from Telegram, but still allows Telegram import later.
- Their copy around the site is sharp: "do not lose access to VPN if Telegram is blocked".
- Risk: code-only recovery is harsh. If the user loses it and did not bind Telegram, recovery is impossible. POKROV could adapt this as a backup recovery code, not necessarily as the only identity.

## Nosok VPN

Sources: `@NosokVPN`, `@NosokVPNBot`, `https://nosokvpn.com/`, `https://tgstat.ru/channel/@NosokVPN/stat`.

What they have:

- Telegram channel: about 203k subscribers on public card; attached export says +5,643 in 7 days and 102.1k reach.
- Website: `nosokvpn.com`.
- Site positioning: "Натяни безопасность", 59+ servers, 12 countries, "users online" counter around 80k.
- Trial card on site: 1 day, 2 devices, 10 GB. Same site also says "3 days free" in bottom CTA, so wording is inconsistent.
- Premium from 250 RUB.
- Login model: email/password plus "Войти через Telegram"; registration is separate. This is not anonymous-code like Cats.
- Contacts: `nosoktop@proton.me`, support `@NosokSup`.

Last two months public posts:

- 2026-05-07: launched full website. Claimed full bot functionality: buy/renew subscription, add/remove devices, manage subscriptions, cabinet, support and recovery.
- 2026-05-14: "Telegram will always be available": after subscription expiry, users keep access to special Telegram-only servers for 6 days to renew.
- 2026-06-19: service rebuilt after infrastructure issues; promo `BESTNOSOKVPN`; warned bot may lag under load.
- Older but important: free Telegram proxy via `proxy.nosokvpn.com`, proxy link meant for relatives, DDoS compensation +2 days, charity purchase days, 3-level referral.

Referral:

- 1st level 50%, 2nd 25%, 3rd 15%.
- Payouts to bank card are explicitly promised in the channel.

Useful pattern for POKROV:

- Emergency renewal access is excellent: even after expiry, let user access Telegram/support/payment path for a short window.
- Their "website as a backup if Telegram is unavailable" is the same strategic direction as Cats, but more mainstream: email + Telegram, not code-only.
- Charity posts work as trust/brand softening around otherwise aggressive blocking marketing.

## Quattro VPN

Sources: `@QuattroVPN_NEWS`, `@quattrovpn_bot`, `https://www.quattro.app/`, `https://t.me/quattrovpn_bot`.

What they have:

- Telegram channel: about 1.04M subscribers.
- Bot preview: about 455k monthly users.
- Website/cabinet: `quattro.app`.
- Telegram verification is used as a trust signal.
- Product depth: web cabinet, own Android app APK, Hysteria2 support, LTE traffic economy, DNS/IPv4/IPv6 settings, app tunneling, ping colors, quick-settings tile.

Last two months and adjacent high-signal posts:

- 2026-04-22: full web cabinet launched: subscription configurator, days/GB/devices, multi-subscriptions, device limit extension, traffic purchase, reissue, locations, referral/partner payment tracking, promo codes. Email must be bound through bot first, but separate website registration is also allowed.
- 2026-04-29: open testing of own Android app.
- 2026-06-01: Telegram verified, LTE 0.1x traffic, unlimited LTE, Hysteria2, geo server upgrades.
- 2026-06-18: payment provider incident; asks users to check purchases and send receipt to support if not credited.
- 2026-06-29: HAPP available again in Russian App Store.
- 2026-07-01, 2026-07-07, 2026-07-08: Android app updates 0.16, 0.18, 0.18.1 with detailed changelogs.

Useful pattern for POKROV:

- They make technical changes legible to non-technical users: "LTE 0.1x means traffic is spent 10x slower".
- Release-note marketing is working for them. Every app update is a conversion event.
- Incident transparency is direct: name the affected flow, tell users what to check, route to support with receipt.

## VPN PLATINA

Sources: `@vpnplatina`, `@vpnplatina_bot`, `@platinum_shops_bot`, `@platejhelp`, `https://tgstat.ru/channel/@vpnplatina/stat`.

What they have:

- Attached export: 107,721 subscribers, +5,791 in 7 days, 39.8k reach.
- Public channel card: about 108k subscribers, 57 photos, 53 links.
- Bot preview: about 63k monthly users.
- Separate "digital goods" bot in channel bio, not just VPN.
- Support is a direct account/bot: `@platejhelp`.

Observed posts:

- 2026-07-05: referral reminder.
- Fixed payouts by subscription term: 30 days -> 50 RUB, 90 days -> 80 RUB, 180 days -> 150 RUB, 365 days -> 250 RUB.
- Payout methods: bank card or GRAM (TON).
- Other visible post asks users to comment desired countries, what to improve, what features they want.

Useful pattern for POKROV:

- This is a simpler affiliate engine than Cats/Nosok: fixed bounty per paid term is easier to explain and budget.
- The "digital goods" adjacent bot may help them cross-sell or reuse audience; useful to watch, but not core VPN product proof.

## Luma VPN

Sources: `@lumavpn_landing`, TGStat public snippets, Google Play `net.luma.luma`.

What is known:

- Attached export: 17,199 subscribers, +3,454 in 7 days, 91.6k reach. Reach is much higher than subscribers, so either repost/ad mechanics are strong or the metric needs verification.
- TGStat snippets show infrastructure posts: expanded infrastructure 3x about 4 weeks ago, then added +5 servers last week due load.
- Google Play app exists: Luma VPN positions itself as a fast secure VPN for access to open internet.

Useful pattern for POKROV:

- Luma looks like an app-first competitor more than a pure Telegram-bot competitor.
- It deserves a separate app/store/channel pass, but it was lower priority than Cats/Nosok/Quattro because current public signal is thinner.

## 4ebur screenshot addendum

The screenshot from the user adds a useful signal to the first wave:

- 4ebur sends branded mascot/image posts inside the bot or channel flow.
- 2026-06-01: coupon `SUMMERTIME` gives -25% for any tariff until the end of day.
- 2026-06-24: cross-resource CTA: Telegram channel `https://t.me/net4ebur` and website `https://net4eburvpn.com`.

This confirms their playbook: friendly mascot, seasonal discount urgency, repeated resource subscription prompts.

## Shared aggressive marketing patterns

- Fear trigger: RKN, Telegram blocking, App Store removals, white lists, VLESS/Xray blocking.
- Urgency: "today only", "before 00:00", "before the moment X", "do it now before payment/access breaks".
- Recovery promise: proxy fallback, website fallback, Telegram-only emergency route, support bots.
- Incident-to-promo: outages are followed by compensation days or promo codes.
- Referral escalation: fixed payout, percent forever, multi-level referral, card/TON payouts.
- Channel gate: Cats and likely Nosok require joining the public channel before bot usage.
- Website is becoming mandatory. The strongest competitors no longer rely on Telegram alone.

## Recommendations for POKROV

1. Treat the web cabinet as a survival surface, not a nice-to-have.
   Copy angle: if Telegram is unstable, user can still manage access from the site/app.

2. Add a backup access/recovery primitive.
   Cats proves the anonymous code model is understandable. POKROV could use a recovery code alongside Telegram/app identity, without making code loss fatal.

3. Consider an expired-user renewal mode.
   Nosok's 6-day Telegram-only route is smart. For POKROV this could be a limited "renew/support access" mode rather than full VPN.

4. Make app updates into channel content.
   Quattro turns every Android release into trust and conversion. POKROV should post release notes with visible user benefit, not only technical changelog.

5. Tighten referral positioning.
   Current POKROV Telegram reward is simple. Competitors are using cash/percent aggressively. A safer near-term move is shareable invite + day bonuses + visible status, not cash payouts until finance/abuse handling is ready.

6. Build an incident comms template.
   Post format: what broke, who is affected, what user should check, what is compensated, support route, expected follow-up.

7. Avoid weak claims.
   Do not copy "military-grade", fake review blocks, inflated "online users", or unsupported no-log claims unless POKROV has evidence and policy behind them.

## Access gaps

- Cats bot deeper flow requires joining `@catsvpn`.
- Nosok bot deeper flow likely requires joining `@NosokVPN`; opening Telegram Web for the bot was unstable in the in-app browser.
- TGStat full chart pages still showed the auth wall after Telegram bot success. To collect detailed TGStat charts, open `@tg_analytics_bot` from the latest TGStat login token, press Start, then return to TGStat and reload. Public/channel data was enough for the current competitor shortlist.

## Evidence files

Raw screenshots live in `docs/competitive/telegram-vpn-2026-07-08/screenshots-wave2/`.

Do not publish raw Cats screenshots from the code-generation/import/referral pages without redaction: they contain generated login/referral/import codes.

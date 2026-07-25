# Quattro VPN — release and growth history

**Observed:** 2026-07-22<br>
**Source:** complete publicly available Telegram web archive for `@QuattroVPN_NEWS`, public bot/channel previews and current web/store surfaces

The available archive contains 170 surviving posts numbered `1` through `206`; missing numbers are deleted or unavailable posts. The channel was created 2025-04-09. The first surviving product post is 2025-06-28.

## Timeline

| Date | Event |
| --- | --- |
| 2025-04-09 | News channel created. |
| 2025-06-28 | First surviving launch/update: subscription redesigned, up to five devices, simpler activation, PC compatibility and a claimed 166 locations. Separate Android TV and Windows-routing instructions published. |
| 2025-08-06 | Referral statistics and a manually approved cash partner program added to the bot. |
| 2025-08-07–14 | Scarcity promo codes for five/seven free days distributed to the first 50/100 users. |
| 2025-08-25 | Bot menu restyled; server-status page added. |
| 2025-08-27 | v2RayTun Android breakage tracked publicly; update announced when fixed. |
| 2025-10-01 onward | Operator-specific LTE/allowlist servers become the core operational story; Happ and Streisand recommended where v2RayTun is insufficient. |
| 2025-10-20 | Bot reaches 10,000 users; referral contest offers cash and annual subscriptions. |
| 2025-11-02 | Contest winners published; top result shows 91 paid referrals. |
| 2025-11-12 | Bot database incident loses part of a day's payment state; support account is frozen under volume; recovery/compensation promised. |
| 2025-11-21 | 100 RUB/month for five devices stated; automated blocking for device-limit abuse announced. |
| 2025-12-23 | Price raised to 200 RUB/month; multi-subscription mini-app and variable device limits previewed. |
| 2026-03-01 | Telegram Stars price adjusted with TON; RUB price left unchanged. |
| 2026-03-25 | Price raised to 300 RUB/30 days from 2026-04-01; 180/365-day plans removed; referral reward reduced to seven days each after a 30-day purchase. |
| 2026-03-31 | Two hidden payment methods and a hidden tariff teased as a limited-access game mechanic. |
| 2026-04-09 | LTE traffic becomes metered; ordinary servers remain unlimited; unused traffic rolls over; add-on packages introduced. |
| 2026-04-11–15 | 0.5x and unlimited LTE introduced after backlash. Comments/chat are temporarily closed to avoid a wave of negativity. |
| 2026-04-22 | `quattro.app` cabinet launches: configurable days/GB/devices, multiple subscriptions, proportional device upgrades, renew/reissue/location controls, referral bonuses spendable on days/traffic, partner/payment tracking and promo codes. A hidden on-site bonus is teased. |
| 2026-04-25 | Russian servers added; support hiring opened through Google Forms. |
| 2026-04-29 | Own Android application `0.9.0` released as an open beta via Telegram; activation is copied from the cabinet and pasted into the app. |
| 2026-06-01 | Hysteria2, Gemini-specific locations, 0.1x and unlimited LTE announced. Happ, Incy, Throne and NekoBox named as compatible clients. |
| 2026-06-18 | Payment-processing mismatch between provider and bot/cabinet disclosed and manually reconciled. |
| 2026-06-29 | Happ Proxy Utility's Russian App Store listing recommended by direct link. |
| 2026-07-01 | Own app `0.16`: Hysteria2, Quick Settings tile, custom DNS, IPv4/IPv6 selection, adaptive UI, ping/favorites, smarter app sorting and direct routing for Russian allowlisted sites. APK distributed through Telegram and Yandex Object Storage. |
| 2026-07-07 | Own app `0.18`: light theme, tile long-press, home ping/color states, DNS editing, auto-server tuning and Gemini/IPv4/IPv6 fixes. |
| 2026-07-08 | Own app `0.18.1`: large-screen/header/status-bar fixes and broken ON-button fix. Users are explicitly told to delete the old version first. |

## Release machine

```text
Telegram announcement → direct APK in Telegram + Yandex mirror
                      → bot/site/support CTAs with per-post attribution
                      → rapid hotfix → often delete old build before install
```

- The own service app is not in Google Play under `ru.quattrocloud.vpnapp`; its Play URL returns “not found”.
- The observed public release pace is beta-first and fast: `0.9.0` to `0.16`, then `0.18` and `0.18.1` in roughly ten weeks.
- Telegram/Yandex host the Android artifacts; iOS/desktop users are routed through third-party clients while native builds are promised.
- Posts use bot `start=` and site `partner=` tags for campaign-level attribution.
- Outages, blocking waves and hotfixes are communicated bluntly and quickly, often followed by compensation or a new server class.
- Public instructions and support are part of the release, not afterthoughts.

## Scale observed on 2026-07-22

- News channel: 1.06M subscribers.
- Main bot: 550,879 monthly users.
- Support bot: 32,753 monthly users.
- Instruction group: 83,138 members, 16,660 shown online.
- Current Google Play client: 1K+ installs, a separate small product line.

## Evidence

- [`24-news-channel.png`](screenshots/24-news-channel.png)
- [`25-release-0.18.1.png`](screenshots/25-release-0.18.1.png)
- [`26-account-cabinet-launch.png`](screenshots/26-account-cabinet-launch.png)
- [`27-own-app-beta.png`](screenshots/27-own-app-beta.png)

Telegram proxy endpoints/secrets and personalized campaign/account parameters are deliberately not retained.

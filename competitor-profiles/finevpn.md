# FineVPN — Competitor Profile

**Telegram:** [@FineVPNbot](https://t.me/FineVPNbot)
**Generated:** 2026-07-12
**Evidence:** PASS_DIRECT for bot; BLOCKED_DOWNLOAD for Telegram document

## At a Glance

| Metric | Value |
|---|---|
| Bot monthly users | 10,972 at live check |
| Languages | RU, EN, DE, FR, ES, CN |
| Main menu | Services/order, Android app, invite, support, partner, settings |
| Android binary | Beta `FineVPN-apkProd-release-v1.0.0 (1).apk`, 43.3 MB |
| Google Play package | `com.fineprotectapp.android` |

## Findings

- The bot immediately exposes a first-party beta APK rather than hiding Android behind a store.
- The document is versioned only as 1.0.0 and described as beta.
- Telegram Web displayed the full APK document, but its media download API was unavailable in the controlled browser. A trustworthy binary was therefore not obtained and no static claims are made.
- The bot description carried a Telegram ad for another VPN. It is not FineVPN product copy and was excluded from comparison.

## Assessment

The direct-document pattern is useful for resilience, but the release needs a public hash, certificate fingerprint, stable download page and visible changelog. A mutable Telegram document alone is weak provenance.

## Evidence

- [Official beta document screenshot](raw/finevpn/2026-07-12/screenshots/bot-official-beta-apk.png)
- [Wave 2 report](../docs/competitive/telegram-vpn-2026-07-12/telegram-vpn-wave2-and-apk-analysis.md)

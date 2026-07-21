# Kubik VPN Android — Application Profile

**Package:** `com.kubikvpn.app`
**Version:** 1.2.4 (11)
**Official APK:** `https://kubikvpn.com/downloads/KubikVPN-latest.apk`
**Generated:** 2026-07-12
**Evidence:** PASS_STATIC + PASS_EMULATOR_UI; VPN tunnel NOT_CONNECTED

## Binary

| Field | Value |
|---|---|
| Size | 120,208,613 bytes |
| SHA-256 | `65C9E93EA4117BCC3319F6CAD5EF372F3A3057E474387A71D5026DCF609FAB52` |
| SDK | min 24 / target 36 |
| Debuggable | false |
| Signing | v2 only; Android Debug certificate |
| Cert SHA-256 | `c3e5e09ae37a6610ccafa4dfdc91e8d01882fc6a92f56c9b9baeeb8f4331b363` |

## Critical Findings

- The public release is signed with an Android Debug certificate. This is a release-engineering and update-trust failure even though `debuggable=false`.
- The app carries one of the largest ad/attribution surfaces in the sample: Appodeal, AppLovin, Yandex, Facebook, IronSource/Unity mediation, Amazon, InMobi, Vungle, Chartboost, Fyber, Smaato, Moloco, Start.io, BidMachine, PubNative, Bigo, Mintegral, Ogury, MobileFuse, MyTarget, Adjust, AppsFlyer, Firebase Analytics, AppMetrica and Sentry.
- Manifest surface includes AD_ID and Android Privacy Sandbox Topics/Attribution/Ad ID/Custom Audience, billing, license check, boot and multiple OEM integrations.
- Flutter UI and sing-box `libbox.so`; first-party host is `kubikvpn.com`.

## Product and UI

- First launch is a full privacy-policy wall with a mandatory checkbox.
- Anonymous free plan: 60 minutes per session and 5 GB/month.
- Free server list shows Finland, Germany, Netherlands and Sweden with playful generated names and ping.
- Premium offers 1, 3, 6 and 12 months and up to three devices, but the emulator screen did not display prices and handed purchase to the site.
- Purple dark visual is coherent but generic. Settings are thin: legal, logs and theme.

## Assessment

Useful free-entry mechanics, bad trust posture. The combination of debug signing, mutable `latest.apk`, extreme SDK density and ad-identification permissions makes Kubik the highest privacy/supply-chain risk in this APK wave.

## Screenshots

- Policy (external snapshot: `raw/market-wave2/2026-07-12/screenshots/app-kubik-policy.png`)
- Home (external snapshot: `raw/market-wave2/2026-07-12/screenshots/app-kubik-home.png`)
- Servers (external snapshot: `raw/market-wave2/2026-07-12/screenshots/app-kubik-servers.png`)
- Premium (external snapshot: `raw/market-wave2/2026-07-12/screenshots/app-kubik-premium.png`)
- Profile (external snapshot: `raw/market-wave2/2026-07-12/screenshots/app-kubik-profile.png`)
- Settings (external snapshot: `raw/market-wave2/2026-07-12/screenshots/app-kubik-settings.png`)

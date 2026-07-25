# OverSecure Android — Application Profile

**Package:** `com.oversecure.vpn`
**Version:** 1.1.7 (15)
**Official APK:** `https://client.overcdn.ru/android/oversecure.apk`
**Generated:** 2026-07-12
**Evidence:** PASS_STATIC + PASS_EMULATOR_UI; VPN tunnel NOT_CONNECTED

## Binary

| Field | Value |
|---|---|
| Size | 35,805,535 bytes |
| SHA-256 | `F3FC3DD14F92EF0837501345B050F91FBE56940A36688C842277A10D9B0EE167` |
| SDK | min 24 / target 36 |
| Debuggable | false |
| Signing | APK Signature Scheme v2 only |
| Certificate | `Oversecure LTD`; SHA-256 `6c4bb47cd817d20366a72a4b8ca828796df4c88fe0629f4b9c20455fa56b32c3` |

## Internals

- sing-box/SagerNet-derived `libbox.so` for arm64 and armv7; Flutter/Rive UI.
- AppMetrica is present. Ad-revenue adapter shims exist inside it, but full ad-network SDKs were not found.
- First-party surface: `oversub.cloud` with `/fetch`, `/isp` and `/version`.
- Bundled DoH options include Cloudflare, Google, Quad9 and Yandex.
- Sensitive permissions include `QUERY_ALL_PACKAGES`, `REQUEST_INSTALL_PACKAGES`, AD_ID, Install Referrer and special-use foreground service.

## UI and UX

- Onboarding claims 67,000+ active clients, 96% satisfaction, 30+ locations and 100+ servers.
- Entry requires an `oversub.cloud/<token>` subscription URL; there is no anonymous account flow.
- Home offers “Стандарт” and “Обход” modes.
- Settings include DNS, per-app split tunneling, proxy ping, LAN access, statistics and automatic server change.
- Split tunneling supports off, include and bypass semantics with searchable app selection.

## Assessment

Good focused client UX and restrained SDK surface compared with ad-funded apps. Main risks are broad installed-app visibility, sideload/update capability and dependence on a bearer subscription URL.

## Screenshots

- [Onboarding](raw/market-wave2/2026-07-12/screenshots/app-oversecure-onboarding.png)
- [Home](raw/market-wave2/2026-07-12/screenshots/app-oversecure-main.png)
- [Settings](raw/market-wave2/2026-07-12/screenshots/app-oversecure-settings.png)
- [Split apps](raw/market-wave2/2026-07-12/screenshots/app-oversecure-split-apps.png)

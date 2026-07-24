# Ping VPN Android Static Package Notes

**Snapshot:** installed Google Play build `1.1.19` (`versionCode 63`) on 2026-07-22
**Package:** `com.pingsecure.client.app`
**Scope:** redacted package metadata only. APKs, extracted binaries, raw runtime logs, endpoints and configuration material remain outside the worktree.

## Package Shape

- Google Play split install: base `60,219,951` bytes, Russian resources `45,465` bytes, x86_64 native split `21,316,459` bytes and xhdpi resources `155,362` bytes; about 81.7 MB in total on this emulator.
- Flutter launcher: `com.pingsecure.client.app.MainActivity`.
- Android range: `minSdk 24`, `targetSdk 36`.
- Tilda Sans is bundled as the product typeface.
- The x86_64 split contains `libapp`, `libflutter`, `libgojni`, `libtun2socks` and an advertising crash-reporting library. `libgojni` is roughly 35.5 MB and is the dominant native component.

## Permissions And Platform Components

Observed declarations include internet/network/Wi-Fi state, boot completed, wake lock, vibration, notifications, foreground-service/special-use service, battery-optimization exemption request, Google Play Billing, biometric/fingerprint support and Google advertising/AdServices ID, Attribution and Topics permissions.

AndroidX WorkManager and boot receivers are present, so the package can schedule or restore background work. A VPN service is declared as `.bg.VPNService` with `android.permission.BIND_VPN_SERVICE`.

## VPN And Protocol Signals

The native Go library contains recognizable compiled identifiers associated with Xray/V2Ray, VMess, VLESS, Trojan, Shadowsocks, WireGuard, Hysteria, QUIC, SOCKS5, gRPC and Reality. OpenVPN was not found in the same bounded keyword pass.

These are package-level capability/signature observations, not proof that every protocol is enabled in the current product UI or server configuration. The startup backend blocker prevented protocol selection and a live tunnel test. No raw endpoint, key or VPN configuration was retained.

## Product Surface Encoded In Assets

Production assets cover:

- premium access and purchase restoration;
- invite/reward and currency imagery;
- connection statistics;
- app split tunnelling;
- custom URL routing;
- auto-connect and notification controls;
- language and theme selectors;
- privacy, terms, feedback and sharing;
- Google, Telegram and WhatsApp contact/integration imagery.

The official Google Play creatives independently confirm the connected dashboard, country/city selector, settings and custom-URL flow. The asset inventory therefore helps map the blocked installed build, but it is not a substitute for runtime validation.

An embedded `urls.json` catalog contains 233 named services/sites. The retained audit records names only, never the raw destinations. The set spans social networks, messengers, video/streaming, news, banks, government services, games and shopping, including Telegram, WhatsApp, Instagram, YouTube, Netflix, Госуслуги, Сбербанк, ChatGPT and OpenAI. Combined with the store's “Smart mode” copy and custom-URL creative, this is strong evidence of a built-in site/service routing catalog rather than only a blank URL form.

## Advertising, Billing And Telemetry

The package contains Google Play Billing and premium/restore-purchase assets despite current store copy that calls the service completely free and says there are no subscriptions.

The advertising footprint is unusually broad. Manifest, resource and DEX evidence includes or references:

- Appodeal;
- Google AdMob;
- IronSource / Unity LevelPlay and Unity Ads;
- AppLovin;
- Meta Audience Network;
- Yandex Ads;
- Bigo;
- Vungle;
- MyTarget;
- Mintegral / MBridge;
- InMobi;
- Fyber;
- BidMachine;
- Pangle;
- Moloco.

Firebase Analytics/Crashlytics and AppMetrica components are also present. SDK presence does not prove that every bidder or telemetry path is active in every session. Runtime and public evidence remove the larger ambiguity, however: the privacy policy names Appodeal advertising, the official Telegram channel awards subscriptions “without ads and limits,” and current reviews describe connect/disconnect ads and premium gating. The “no ads / no subscriptions” store claim is therefore stale or materially inaccurate for at least part of the current product population.

## Update And Release Signals

No clear Play Core in-app updater, self-installer receiver or direct-APK update service was identified in the bounded manifest/component pass. This build appears to rely on ordinary store delivery for binary updates. Update-related imagery exists in assets, but imagery alone is not evidence of an independent updater.

Third-party archive dates show rapid store iteration from May through July 2026; those dates and changelogs are documented separately. Static inspection found no reliable release-channel marker beyond the installed production build.

## Evidence Limits

- The app never passed remote bootstrap during three controlled attempts, so core screens, monetization, ads, protocols and connection behaviour are reconstructed from official store creatives, public policy/channel evidence and static package artifacts where clearly labelled.
- Raw APKs, extracted strings, logcat, server material and any values that could identify a current network session remain quarantined outside the repository.
- Library names and string signatures are separated from verified runtime behaviour throughout the profile.

# TipTop VPN 1.036 — Redacted Android Package Notes

Snapshot: 2026-07-22. Google Play split APKs were copied from the installed emulator package into the audit's sensitive temporary area. Raw binaries, server/configuration material, signing fingerprints and user/device identifiers are intentionally excluded from the repository.

## Package And Provenance

- Package: `com.free.tiptop.vpn.proxy`
- Version: 1.036 (`versionCode 36`)
- Split APKs observed: base, Russian language, x86_64 and xhdpi resources
- Approximate installed split sizes: base 88.7 MB; x86_64 19.7 MB; language and density splits below 0.3 MB each
- `minSdkVersion`: 23
- `targetSdkVersion`: 35
- APK signature schemes v1, v2 and v3 are present with one signer
- A Google Play source stamp is present with timestamp `2025-07-17 12:39:09Z`, matching the store's visible 17 July 2025 update date
- The signer subject is a generic Google Android identity; Play App Signing management is a reasonable inference, not independently verified ownership evidence

## Product Architecture

- The first-party code is a large modular Android application with presentation, domain, data, use-case, server, database and settings layers rather than a thin WebView shell.
- A separate `com.tiptopvpn.app.singbox` namespace contains the modern tunnel path; another sizeable `com.free.tiptop.vpn.proxy` namespace holds application, advertising, Firebase, scheduling and VPN integration code.
- First-party activities cover onboarding, account/passwordless confirmation, premium offers, promo codes, tasks, sharing, server selection, protocols, split tunnelling, API proxy, themes, languages, kill-switch help, support and About/legal pages.
- The live bootstrap response observed in the runtime audit controls locations, prices, languages, feature switches, advertising, tasks, referrals, banners, legal/support URLs and localized text. The static layout is consistent with a heavily server-driven product.

## VPN Engines And Declared Capabilities

- The installed build contains two VPN implementations: OpenVPN services and a non-exported sing-box VPN service, all using Android's `BIND_VPN_SERVICE` protection where expected.
- Major x86_64 native libraries include `libbox.so` (about 30.8 MB), `libovpn3.so` (about 8.3 MB), `libopenvpn.so` (about 6.3 MB) and OpenVPN support/speed-test libraries.
- Bounded native-string inspection found library-level support for sing-box, VLESS, VMess, Trojan, Shadowsocks, WireGuard, Hysteria/Hysteria2, TUIC, Reality, QUIC, gRPC, SOCKS5, Xray and OpenVPN.
- These bundled capabilities do not prove that every protocol is exposed or enabled. In this session the remote configuration exposed `ovpn_tcp_x` and VLESS-related choices, while Android identified the successful tunnel session as `sing-box`.
- Sample/test OpenVPN profiles and OpenVPN executables are bundled as assets. Their raw endpoints and configuration remain quarantined and were not used.

## Permissions And Components

Observed permissions cover network/Wi-Fi state, foreground VPN work, notifications, boot completion, wake lock, battery-optimization exemption, phone state, legacy external storage, Google Play Billing, Install Referrer, advertising ID and Android AdServices attribution/topics APIs. `QUERY_ALL_PACKAGES` is also requested, consistent with the installed-app split-tunnelling selector.

The manifest exposes OpenVPN remote-control entry points, including an exported API service and connect/disconnect/pause/resume activity aliases. This is a static attack-surface observation only: no attempt was made to invoke, bypass or exploit third-party controls. The product owner should verify that runtime authorization and caller validation protect every exported path.

The modern sing-box VPN service is non-exported. Quick Settings, push, purchase, promo, share and boot-related components are also declared.

## Monetization And Telemetry Surface

- The package contains a very broad advertising/mediation stack, including Google ads, AppLovin/MAX, Meta/Facebook Audience Network, Yandex, IronSource/LevelPlay, Fyber, InMobi, Mintegral, Pangle, Unity, Vungle, Bigo and Tapjoy-related code.
- Firebase Analytics, Crashlytics, Messaging and Remote Config are present, as are Play Billing/review integrations, Install Referrer and other analytics/profiling packages.
- Package presence alone does not prove every network is active. Runtime logs did, however, confirm that mediation/device-session telemetry was assembled before the mandatory privacy gate was accepted.
- The application also declares an AppLovin AppHub binding surface and contains third-party native profiling/crash-reporting libraries.

## Assets And Remote-content Clues

- The package contains roughly 263 country/territory flag assets, far more than the 12 locked premium locations shown live. This is evidence of a broad reusable/dormant catalogue controlled by server configuration, not a claim that 263 VPN locations are available.
- Assets include build metadata, network-test material, custom Inter/Roboto/rouble fonts, animated/product illustrations and extensive advertising-view resources.
- Russian trust-chain certificates and advertising-provider certificates are bundled. No claim is made here about how each certificate is used at runtime.

## Release Mechanism

- Google Play Core common, review and split-compat code is present, but no Play in-app-update module was found.
- The manifest does not request `REQUEST_INSTALL_PACKAGES`.
- The inspected build therefore appears store-managed and capable of in-app review, with no static evidence of an APK self-updater. Server-delivered configuration allows substantial product changes without a binary release.

## Evidence Boundaries

- Raw APKs, DEX/native binaries, endpoints, embedded profiles, certificates/fingerprints and personalized runtime material remain outside the worktree.
- No certificate bypass, traffic interception, exported-component probing, binary modification or exploitation was performed.
- Static findings describe bundled capability and attack surface; they are not proof that every SDK, protocol, certificate or code path is active.

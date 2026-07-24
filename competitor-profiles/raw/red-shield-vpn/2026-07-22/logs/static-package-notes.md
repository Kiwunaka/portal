# Red Shield VPN v4.3.6 — Redacted Android Package Notes

Snapshot: 2026-07-22. Google Play split APKs were copied from the installed emulator package into the audit's sensitive temporary area. Raw binaries, signing fingerprints, API/update domains, server/configuration payloads and account/device identifiers are intentionally excluded from the repository.

## Package And Provenance

- Package: `com.redshieldvpn.app`
- Version: v4.3.6 (`versionCode 1843`)
- Build type/flavor: release / `store`
- Split APKs: base, arm64-v8a, Russian resources and xhdpi resources
- Approximate installed split size: 132.4 MB; base 73.0 MB and arm64 native split 57.5 MB dominate
- `minSdkVersion`: 26
- `targetSdkVersion`: 35
- `debuggable`: false
- APK signature schemes v2 and v3 are present with one Google Android signer; a Google Play Source Stamp is present with timestamp `2026-06-25 02:20:51Z`

The signer identity and Source Stamp are distribution/provenance evidence, not proof that Google owns or operates Red Shield VPN.

## Product Architecture

- This is a large native Kotlin/Jetpack Compose application with Hilt dependency injection, Room persistence, repositories/use cases and separate phone/TV composables—not a WebView wrapper.
- The release build contains dedicated modules for home, auth/recovery/TV pairing, sessions, locations, protocols, per-app routing, content blocking, promo codes, sharing/referrals, support chat, settings, About, widget and developer tooling.
- The manifest declares launcher and Leanback/TV entry points. Phone and TV layouts, QR-based TV authorization, ML Kit barcode models and CameraX are bundled, supporting a shared phone/TV codebase and device-pairing flow.
- A Quick Settings tile and app widget can expose connection/location controls outside the main app.
- Local Room models and repositories store locations/latencies, connection parameters/ports, split-tunnel package sets and support messages. Server-driven downloads supply locations, translations, parameters, protocol configuration and in-app messages.
- Bundled Russia and China CIDR datasets plus a first-party geo-bypass manager indicate region-aware routing/bypass capability. This does not prove which rules were active in the unpaid session.

## VPN Engines And Declared Capability

- The manifest declares a WireGuard VPN service and a sing-box VPN service, both protected by Android's `BIND_VPN_SERVICE` permission, plus a private dispatcher service.
- The arm64 split is dominated by `libbox.so` at about 52.5 MB. Static native strings include sing-box, WireGuard/AmneziaWG, OpenVPN, VLESS, VMess, Trojan, Shadowsocks, Hysteria/Hysteria2, TUIC, Reality, QUIC, gRPC, SOCKS5, ShadowTLS, SSH, Naive and Tailscale capability.
- First-party repositories contain separate download paths for WireGuard/AWG, Xray, Trojan and obfuscation materials. Runtime feature flags observed in this account left the hidden Shadow variants disabled.
- Bundled engine capability is not the same as a customer-visible protocol list. The audited UI exposed only Auto, RedLink TLS Plus and RedLink Random, so the brand layer intentionally hides lower-level protocol complexity.

## Permissions And Components

The manifest requests 19 permissions. Notable product/privacy surface includes full installed-package visibility (`QUERY_ALL_PACKAGES`) for split tunnelling, boot completion, notifications, wake lock, battery-optimization exemption, overlay permission, foreground-service/system-exempted service declarations, advertising ID/AdServices attribution and Firebase push reception.

Observed exported surface includes:

- the deep-link-enabled main activity (`rsv://subscription`);
- the Quick Settings tile;
- two VPN services protected by the system VPN binding permission;
- widget action and package-replacement receivers;
- generic AndroidX test-invoker activities, a Compose preview activity and profile/diagnostic tooling components included in the production manifest.

The generic test/tooling activities and externally addressable widget actions are unnecessary-looking production attack surface. They were recorded only; no intent injection, component invocation or bypass attempt was made. The owner should remove non-production tooling and verify caller/permission checks around every exported component.

## Monetization, Messaging And Measurement

- Google Play Billing and RevenueCat classes were not found. This matches the runtime handoff to a branded web cabinet/payment flow rather than native Play purchase.
- Firebase Analytics/Google Measurement, Crashlytics, Messaging, Database, Install Referrer/AdServices declarations and push-token registration are present.
- No bundled ad-mediation SDK, AppsFlyer, Adjust, AppMetrica, Facebook SDK, Sentry or RevenueCat implementation was found in the inspected store build.
- Google Play review integration is bundled, and application events include an in-app-review launch path. No review prompt appeared in the unpaid audit.
- Permission or package presence alone does not prove that every measurement path is active. Store Data Safety and the privacy policy still need reconciliation against this static surface.

## Release Mechanism

The codebase has explicit `store`, `storeTv` and direct-`apk` flavors:

- This installed `store` build uses Google Play's in-app update API and registers an update-state listener.
- The direct-APK flavor uses a first-party update domain, supports separate stable and beta APK channels, downloads an APK into app-controlled storage, checks the downloaded package against an embedded allowed signing fingerprint, then opens it through a FileProvider for Android's package installer.
- The release also bundles Google Play in-app review support.

This is a resilient two-lane release system: normal Play distribution plus an independently updatable direct APK channel, with a distinct beta switch. The static signature allowlist is a meaningful supply-chain safeguard; the direct distribution domain and current release history still require public verification.

## Evidence Boundaries

- Raw APKs, DEX/native binaries, signing fingerprints, update/API domains, embedded checks, server configuration and personalized material remain outside the worktree.
- No certificate bypass, traffic interception, exported-component probing, binary modification or direct-update invocation was performed.
- Static findings describe bundled code and potential capability. They do not prove that every engine, SDK, feature flag or update branch was active in the observed account.

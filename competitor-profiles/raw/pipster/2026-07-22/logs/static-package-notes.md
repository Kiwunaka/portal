# Pipster Static Android Package Notes

Snapshot: 2026-07-22. Sensitive APKs and any internal endpoints/configuration remain outside the repository.

## Artifact And Signing

- Package: `com.vipin.pipster`.
- Version: 2026.7.7, code 174.
- Google Play split install: base + Russian locale + x86_64 + xhdpi, approximately 46.4 MB total.
- `minSdk=27`, `targetSdk=35`, release/non-debuggable build.
- APK Signature Scheme v2/v3 verified; app signer subject is `O=Synaptic`.
- Google Source Stamp verified with timestamp 2026-07-07 07:33:02Z, matching the date-style release number. Certificate fingerprints are intentionally omitted.

## Technology Shape

- Flutter UI with two DEX files and large native x86_64 payload.
- Native payload includes Flutter, app AOT code, Crashlytics handlers and a Go/Xray bridge (`libgojni.so`).
- The app carries both Xray and sing-box-format geodata for private/Russian destinations, ads, Apple and `0x0` route groups.
- Android plus desktop-oriented code/assets are bundled: Quick Settings tile, Tasker receiver, Windows tray icon/window management and web-to-app authorization-code flow.

## VPN Backend And Routing

App-specific AOT symbols and models directly reference:

- Xray AIO adapter/service;
- VLESS users/servers;
- Shadowsocks outbound configuration;
- Reality transport settings;
- gRPC, WebSocket, QUIC, SOCKS5 and raw/HTTP-upgrade transport models;
- asset/geofile transformation, routing, FakeDNS, stats, metrics and observatory models.

The generic Go core also contains VMess, Trojan, WireGuard, Hysteria and other implementations. Their presence in the shared backend is **not** proof that Pipster exposes or uses them for customers. The strongest app-specific evidence supports an Xray/VLESS-or-Shadowsocks configuration family with Reality/gRPC/WebSocket-capable transports; the exact Germany session configuration was not extracted because raw connection material is out of scope.

## Product Architecture

The release contains explicit feature modules for:

- passwordless email, Yandex OAuth, QR generation/scanning and cross-device QR login;
- anonymous/guest login and web-generated authorization codes;
- server onboarding/list/search and selected-location state;
- subscription state, trial-subscription API/page and device-limit screen;
- traffic quota/reward repository and connected/disconnected event handling;
- profile polling plus WebSocket/push synchronization;
- referral input, referral statistics/page and large referral CTA;
- account deletion;
- notifications, validated external push actions and in-app review;
- six-language/theme settings, tray/window management and debug tooling.

This confirms that the blocked authenticated product is richer than the guest menu: referrals, profile/subscription state, device limits and account deletion are first-class app features.

## Ad Monetization Engine

Pipster integrates Yandex Mobile Ads with distinct app-open, banner, interstitial and rewarded managers. App code includes:

- placement/policy/resolver/orchestrator layers;
- a free-profile ad preloader;
- a dedicated VPN-connect ad flow;
- a rewarded traffic-limit flow;
- fullscreen concurrency locking and explicit ad decision reasons.

An app log string explicitly links dropping the connect ad to stopping the VPN. That matches the runtime evidence: the tunnel was not established until the pre-connect ad completed, and the repair action removed the tunnel before launching another ad.

## Analytics, Messaging And Attribution

Direct Dart/package evidence:

- Yandex AppMetrica;
- AppsFlyer with deep-link support;
- Firebase Core, Crashlytics, Messaging and Remote Config;
- Yandex Mobile Ads and Yandex OAuth;
- local/remote push scheduling, WebSocket lifecycle and secure storage.

Generic native-core strings also contain names such as Adjust/Sentry, but no corresponding app-level Dart package was found; do not claim active Pipster integration from that alone.

## Permissions And Components

Notable requested permissions:

- Internet/network state/change state;
- foreground service + foreground-service special use;
- boot completion, wake lock, vibration, exact alarms and notification-policy access;
- post notifications;
- camera for QR scanning;
- Google advertising/attribution IDs;
- Firebase/Huawei push permissions;
- legacy external-storage read capped at Android 12L.

There is no Google Play Billing permission in this artifact. Combined with the in-app YooKassa migration notice, paid checkout should be treated as an external/account-web flow unless runtime evidence proves another lane.

Security posture:

- `debuggable=false`;
- `allowBackup=false`;
- app-wide `usesCleartextTraffic=true` with no manifest network-security configuration reference;
- `XRayVpnService` is exported but protected by `android.permission.BIND_VPN_SERVICE`;
- Quick Settings service is protected by `BIND_QUICK_SETTINGS_TILE`;
- several exported push/provider/automation components exist, including a Tasker receiver and VPN notification controller, and warrant dedicated defensive review if this app becomes a security target.

Broad cleartext allowance is an avoidable trust smell. This static pass does not prove that credentials or tunnel control traffic actually traverse HTTP.

## Release And Configuration Mechanics

- Version and Source Stamp use a date-aligned scheme (`2026.7.7` / July 7 stamp).
- Firebase Remote Config, AppsFlyer deep links, WebSocket push and an S3/API-domain fallback are present.
- Code paths can select a remotely supplied API domain with a hardcoded fallback; raw domains and provider configuration are intentionally excluded.
- Store split delivery plus date-style versioning and remote configuration indicate a fast, cohort/config-driven release model, subject to confirmation from public release history.

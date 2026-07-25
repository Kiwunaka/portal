# Kakadu — Static Android Package Notes

Captured: 2026-07-22<br>
Scope: read-only inspection of the already installed Google Play bundle. No APK, endpoint, certificate digest, token, account value, or device identifier is retained in the repository.

## Package identity

- Package: `com.matrena.vpn`
- Version: `2.4.6` (`versionCode 1781433401`)
- Minimum / target / compile SDK: 27 / 35 / 35
- Installed delivery: Google Play base APK plus x86_64 and xhdpi splits
- Main activity: `com.kakadu.vpn.MainActivity`
- App link/deep-link scheme: `kakadu:`
- Distribution protection: Play bundle/source stamp and PairIP protection markers present

The package requests Internet/network/Wi-Fi access, notification and vibration access, foreground-service/VPN capability, battery-optimization exemption, Play billing/licensing and camera access. Camera hardware is optional and the live app requests permission only when the QR route is used.

## VPN architecture

`KakaduVpnService` is non-exported, declares the VPN foreground-service subtype and supports Android Always-on VPN. A Quick Settings tile is present.

The x86_64 split contains a large `libbox.so` and Sagernet/sing-box package names. Binary capability strings cover WireGuard, Shadowsocks, VLESS, VMess, Trojan, Hysteria, TUIC, QUIC, Reality, ECH, TUN routing and traffic sniffing. This proves that the bundled engine can implement those transports/features; it does **not** prove that every protocol is enabled for customers or deployed by Kakadu's backend.

The app contains a rotating pool of cover domains and direct-IP HTTPS fallbacks. Exact endpoints are intentionally excluded from the repository. This is a censorship-resilience mechanism and also increases the importance of authenticated configuration, a public official-domain directory and clear data-controller disclosure.

## Frameworks and third parties

Observed components include:

- Jetpack Compose/navigation and Room;
- OkHttp networking;
- Google Sign-In;
- Google Play Billing/licensing;
- CameraX and ML Kit barcode scanning;
- Google DataTransport/CCT code, consistent with bundled Google/ML Kit dependencies.

No obvious Sentry, Firebase Crashlytics, AppsFlyer, Adjust or major standalone analytics SDK was found. This is a narrow static observation, not proof that the service collects no telemetry: account, session, payment and VPN control-plane calls can be implemented first-party.

## Navigation and feature inventory

Top-level navigation contains Home, Plans and Profile/Settings. The current bundle also contains routes and copy for:

- Google and cross-device QR/code authentication;
- smart connect, favorites, premium servers, country/city search and location choice;
- account profile name/photo editing and profile ID;
- device/session management with sign-in time and IP address, terminate-one/terminate-all, and web sessions that do not consume a device slot;
- family create/join/invite/leave/remove flows using links and QR codes, with separate member accounts;
- promo codes, gifts and invitations;
- Basic/Plus/Pro subscriptions and restore/manage actions;
- Google/Apple store subscription management;
- direct Russian-bank-card payment, saved/default-card management, retry, subscription cancellation and resumption;
- VPN configuration reset, battery/background guidance and an update banner;
- Telegram and WhatsApp support;
- QR scanner, appearance and language settings;
- account deletion;
- hidden `DebugFrag` and `DebugSupportLogsFrag` routes.

This feature map is materially deeper than the logged-out auth wall. Signed-in screens could not be exercised because backend Google authentication failed twice.

## Authentication observation

Google authentication was attempted only after the owner explicitly authorized use of the existing Google account. The Android account chooser and all account-bearing screenshots/XML were quarantined outside the repository.

Both attempts returned to the Kakadu auth wall without a persistent visible explanation. Sanitized runtime logs showed `backendGoogleAuth failed`; the second attempt timed out after ten seconds against a redacted direct HTTPS endpoint. No evidence of completed Kakadu account creation or server registration was found. The signed-in product is therefore `BLOCKED_BY_BACKEND`, not treated as passed.

The alternative QR/code sheet also failed to obtain a code and remained at `0:00` with an empty placeholder. Together, both available login routes were unavailable in the observed session.

## Disclosure contradictions exposed by the package

The package/UI includes profile email/name/photo processing, profile ID, session IP and login time, payment identifiers, device sessions, support logs and direct-card subscription state. These fields are not reconciled with Play's “no data collected” label or the public privacy policy's claim that Kakadu does not collect IP addresses and generally does not collect email.

The legal pages say all payments are exclusively handled through Apple/Google in-app purchase, while the current Android resources contain a full direct Russian-card lifecycle. Static strings alone cannot prove that the route is enabled for every account, but they do prove that the published legal/payment map is incomplete for the shipped client.

## Evidence boundary

- No raw package, certificate digest, domain/IP pool, VPN configuration, access token, Google account field or generated identity is committed.
- No tunnel was started and no remote configuration was exported.
- Capability strings are reported as engine capabilities, not advertised live service guarantees.

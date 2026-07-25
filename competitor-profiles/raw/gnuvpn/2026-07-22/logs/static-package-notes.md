# GnuVPN Android Static Package Notes

Snapshot: 2026-07-22<br>
Package: `com.gnu.vpn`<br>
Version: 1.8.7 (`versionCode 673`)<br>
Scope: local installed APK/split inspection only; no third-party infrastructure probing.

## Package Shape

- Base APK: 24,140,813 bytes.
- ARM64 split: 54,981,307 bytes.
- XHDPI split: 93,606 bytes.
- Minimum SDK: 28 (Android 9).
- Target SDK: 36.
- `allowBackup=false`.
- Qt 6/QML hybrid/native app with three DEX files and a compiled Qt resource bundle.
- Native split contains a large Qt/QML runtime plus OpenVPN, WireGuard/AmneziaWG and SoftEther engines.
- The base ships OpenVPN executables for ARM64, ARMv7, x86 and x86_64.

## VPN Services

Manifest-declared VPN services:

- `de.blinkt.openvpn.core.OpenVPNService`
- `com.gnu.vpn.SoftetherVpnService`
- `org.amnezia.awg.AwgVpnService`

The package contains WireGuard/Amnezia libraries, SoftEther libraries, OpenVPN support and multiple SSL/crypto runtimes. This matches the three explicit Android protocol families exposed by the UI. Custom-server forms only expose OpenVPN and SoftEther; AmneziaWG is managed-service-only in the observed build.

## Permissions And Capabilities

Notable permissions include:

- internet and network-state access;
- foreground-service and system-exempted foreground-service capability;
- notification permission;
- `QUERY_ALL_PACKAGES`, consistent with the per-app split-tunnelling picker;
- boot completion and wake lock;
- Google Play Billing;
- Firebase messaging;
- Install Referrer;
- Advertising ID and Android AdServices attribution/advertising-ID permissions.

## SDK And Attribution Surface

Manifest/Dex evidence includes:

- Firebase Cloud Messaging;
- Firebase In-App Messaging;
- Firebase Remote Config;
- Firebase Analytics / Google Measurement;
- Firebase Installations and Data Transport;
- Facebook SDK with automatic app-event logging and advertiser-ID collection enabled;
- Adjust lifecycle integration;
- Google Play Billing.

A bounded URL-host inventory found 43 unique hosts. It confirmed Adjust, Facebook, Firebase Remote Config, Google APIs and Google advertising/AdServices surfaces. Raw control-plane hosts and any endpoint material are intentionally excluded from repository evidence.

This static surface aligns with default push/email/advertising controls and the release-history focus on messaging, but it is broader than the names disclosed clearly in the privacy policy.

## Deep Links And Distribution Hygiene

Deep-link/app-link declarations include:

- production `gnuvpn.com` routes;
- Branch-style links on `gnuapp.app.link` and `gnuapp-alternate.app.link`;
- `gnuvpn.go.link`;
- custom `gnuvpn:` scheme;
- stage/test infrastructure hosts.

Production inclusion of stage/test app-link hosts is a manifest-hygiene issue. No host was probed and the raw list is not retained here.

## Security/Privacy Observations

- `allowBackup=false` is a sound default for a VPN client.
- The broad package-query permission is product-justified by split tunnelling but increases visibility into the user's installed-app inventory.
- Multiple attribution/analytics SDKs plus advertising identifiers make the in-app “not personal data” wording especially weak.
- Separate protocol engines and a large Qt runtime explain the unusually large APK and recent APK size growth.
- No conclusion about runtime data transmission is made from SDK presence alone.

Sensitive source APKs and extraction artefacts remain outside the worktree.

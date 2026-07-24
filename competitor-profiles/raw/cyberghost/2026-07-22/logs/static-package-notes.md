# CyberGhost static package notes — installed candidate 8.40.0

## Scope and handling

- Analysed the installed Google Play split APK set for `de.mobileconcepts.cyberghost`.
- APK files remain outside the worktree under the sensitive audit directory.
- No certificate fingerprint, embedded token, endpoint credential or raw private configuration is retained here.

## Candidate identity

- Base APK: 24,314,067 bytes.
- x86_64 split: 5,194,629 bytes.
- xhdpi split: 362,286 bytes.
- Application ID: `de.mobileconcepts.cyberghost`.
- Version name/code: `8.40.0` / `4232`.
- Minimum SDK: 32 (Android 12L).
- Target SDK: 36.
- All three APKs passed local signature verification, use APK Signature Scheme v3, and resolve to the same signer. Fingerprints intentionally omitted.

## Requested permissions

- Core networking/runtime: Internet, network state, Wi-Fi state, foreground service, wake lock, boot completed and vibration.
- VPN/system: foreground-service location/system-exempted and app-defined widget permission.
- User-sensitive: coarse/fine location and post notifications. Both were denied during the audit.
- Commerce/push: Google Play Billing, Google/Firebase messaging and Install Referrer.
- Attribution/ads: Google Advertising ID plus Android AdServices attribution and ad-ID permissions.
- Store integrations: Huawei common-data and Samsung Maps Agent app-info permissions are declared in the Google Play candidate.

## Exposed components and routes

- Exported launcher/deep-link activity: `AppActivity`.
- Permission-protected exported services: Quick Settings VPN tile, Android always-on VPN service and WorkManager job service.
- Permission-protected exported receivers: app widget, Firebase messaging, WorkManager diagnostics and profile installer.
- App deep-link scheme `cyberghost://` exposes route hosts for signup, recover, home, upgrade, article, settings, Wi-Fi, app split tunneling, help, countries, streaming, favorites, best and last-used destination.

The route inventory confirms first-class navigation concepts for specialty streaming servers, favorites, best server and last-used server even though the authenticated UI is blocked by the payment rail in this environment.

## VPN and native stack

The x86_64 split contains native OpenVPN and WireGuard-Go libraries (`libopenvpn`, `libovpnexec`, `libwg-go`), matching the visible OpenVPN/WireGuard protocol picker. It also bundles Conscrypt and Sentry native libraries.

## Telemetry/support SDK evidence

Package/component evidence confirms bundled code for:

- Google Analytics/Firebase and Firebase Messaging;
- AppsFlyer attribution;
- Iterable push/messaging;
- Sentry crash/performance components, including replay-related library classes;
- Zendesk support preferences/resources.

The privacy-preferences UI explicitly names only Google Analytics for Firebase, AppsFlyer and Firebase. Static presence alone does not prove that Iterable, Sentry replay or older Mixpanel-labelled resources are active in this session, so they remain `BUNDLED_NOT_RUNTIME_VERIFIED`.

Backup-rule resources still reference Mixpanel cache/preferences, while the current UI does not name Mixpanel. This may be retained legacy compatibility rather than current collection and should not be upgraded to a runtime claim.

## Storage and network configuration

- `allowBackup=false` at application level.
- Cleartext traffic is disabled in the base network-security configuration.
- The app trusts system anchors plus bundled certificate resources for part of its traffic; debug-only configuration additionally trusts user certificates.
- Backup rules explicitly exclude API caches, logs, installation state, certificate/key files, encrypted preferences, telemetry preferences, dedicated-IP material, AppsFlyer purchase data and Zendesk identity/settings.
- Only the local database and favorites preferences are explicitly included by the inspected legacy full-backup rules, despite application-level backup being disabled.

## Confidence boundaries

- `PASS`: package/version/SDK/permission/component/native-library/signature-scheme observations.
- `BUNDLED_NOT_RUNTIME_VERIFIED`: SDK presence and legacy-resource references.
- `NOT_CLAIMED`: actual endpoint traffic, SDK activation, data payloads, certificate-pin enforcement or authenticated feature entitlement.

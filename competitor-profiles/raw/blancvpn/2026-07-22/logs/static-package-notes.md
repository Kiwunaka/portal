# BlancVPN Android Static Package Notes

**Snapshot:** installed Google Play build `1.7.0` (`versionCode 174`) on 2026-07-22<br>
**Package:** `com.blancvpn.app`<br>
**Scope:** redacted package metadata only; APKs and raw extracted payloads remain outside the worktree.

## Package Shape

- Split APK install: base `34,080,892` bytes, Russian resources `29,081` bytes, x86_64 native split `28,480,628` bytes and xhdpi resources `107,321` bytes.
- Flutter entrypoint: `com.blancvpn.blancvpn.MainActivity`.
- Android range: `minSdk 28`, `targetSdk 36`, `compileSdk 36`.
- Declares Android TV/Leanback launcher support; touchscreen and camera are not required.
- The package includes production, beta, stage, test and work-in-progress UI assets. Their presence does not prove the non-production environments are remotely reachable, but it is a release-hygiene and APK-size concern.

## Permissions And Platform Components

Observed declarations include Google Play Billing, network state, boot completed, wake lock, vibration, foreground-service/special-use service, notification permission, advertising ID, install referrer, Firebase messaging receive, battery-optimization exemption request and `QUERY_ALL_PACKAGES`.

The broad package-query permission is consistent with the native per-app routing inventory of 155 installed/system packages. A Quick Settings tile service is also declared.

The printed manifest references Android backup/data-extraction rule resources and does not show a simple `allowBackup=false` flag. This alone is not proof that account or VPN data is backup-eligible; the rule resources would need a separate content audit.

## VPN And Routing Stack

Three VPN service paths are declared:

- `com.blancvpn.vpn_kit.core.AwgVpnService`
- `org.amnezia.awg.backend.AbstractBackend$VpnService`
- `com.blancvpn.vpn_kit.core.XrayVpnService`

The x86_64 split includes Amnezia-related native libraries plus `libhev-socks5-tunnel` and `libgojni`. The base contains `geoip.dat` and `geosite.dat`, duplicated under an `assets/geo/` path. Together these observations are consistent with the AmneziaWG/Xray protocol and selective-routing UI seen in the app; no raw server, key or endpoint material was retained.

## Telemetry And Background Infrastructure

- Sentry Android/NDK and performance initialization components are present, including native crash/tombstone support.
- Firebase Messaging, Installations and DataTransport components are present. The manifest evidence does not establish Firebase Analytics collection.
- PostHog metadata is present with automatic initialization disabled. Presence alone does not prove events are sent in this build.
- AndroidX WorkManager is present for background work.

## Billing And Update/Release Signals

- Google Play Billing library `8.0.0` is bundled.
- `com.blancvpn.app_update_apk_installer.InstallResultReceiver` and `com.bbflight.background_downloader` services/providers indicate an in-app APK download/install mechanism is compiled into the app. Public distribution must be checked before claiming that BlancVPN actively uses it.
- `assets/flutter_assets/shorebird.yaml` contains a Shorebird application identifier. This is strong evidence of Shorebird integration and therefore the technical capability to ship Flutter/Dart patches outside a full store binary release; it is not proof that a patch was delivered to this installed build.
- In-app WebView, URL launcher and share components support the observed legal/help/support handoffs.

## Native Libraries Observed

`libapp`, `libflutter`, `libam`, `libam-quick`, `libam-go`, `libgojni`, `libhev-socks5-tunnel`, `libsentry`, `libsentry-android`, `libdartjni` and `libdatastore_shared_counter` were present in the x86_64 install split.

## Evidence Limits

- No dynamic endpoint, credential, VPN configuration, tokenized URL, public IP, account identifier or raw log is stored here.
- Library/component presence is separated from verified runtime behaviour throughout these notes.
- Direct-download/self-update use, Shorebird patch cadence, backup-rule contents and exact analytics events remain to be verified against public or runtime evidence.

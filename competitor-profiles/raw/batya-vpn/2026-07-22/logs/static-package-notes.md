# Батя VPN 1.3.9 — Redacted Static Package Notes

**Captured:** 2026-07-22 from the installed Google Play package on the isolated LDPlayer device.<br>
**Package:** `ms.f2p.batyavpn`<br>
**Version:** 1.3.9 (`versionCode` 105)<br>
**Minimum / target SDK:** 24 / 36<br>
**Debuggable:** false<br>
**Installer:** `com.android.vending`

The pulled APK splits remain outside the worktree in the sensitive temporary audit area. No embedded key, endpoint or live connection material is retained here.

## Artifact Provenance

| Split | Compressed bytes | SHA-256 |
| --- | ---: | --- |
| `base.apk` | 16,171,734 | `dff59066eefd63eebd49ac5f06c66464046c6f4636a008ce5794582c98d7d1a1` |
| `split_config.ru.apk` | 24,985 | `2a46e6892a409870ea764e4ed132479a571583e9f8dd1892695a7d8a79a40b9e` |
| `split_config.x86_64.apk` | 11,100,974 | `e0d6ee56f7fc900902c7964ea4c98723fcfa8108030a9b6d64457030c1902ab1` |
| `split_config.xhdpi.apk` | 94,846 | `a628e01966f79bc09412f88fd9ce59658c443e7a138ec89ab32a5b9ea2942740` |

The installed split set totals 27,392,539 bytes (26.12 MiB compressed), which confirms the Play device UI's “64 KB” figure is not the app's full package size.

The artifact verifies with APK Signature Scheme v2 and v3 and a valid Google Play source stamp. It is signed through Google Play App Signing (Google Android certificate, one signer). The source-stamp timestamp is **2026-07-10 20:40:52 UTC**, matching the official Play update date. v1, v3.1 and v4 signatures are absent from the pulled base split; this is informational, not a verification failure.

## Delivery And Architecture

- Flutter release application with app code in native `libapp.so` and Flutter engine split by ABI.
- Android App Bundle/split delivery by locale, ABI and density.
- Google Play licensing/integrity wrapper (`com.pairip`) and `CHECK_LICENSE` permission.
- Xray/V2Ray integration through `com.wisecodex.flutter_v2ray`, with a dedicated non-exported `VpnService` running in `:RunSoLibXrayDaemon`.
- Bundled `geoip.dat` and `geosite.dat` rule databases are approximately 19.8 MB and 10.5 MB uncompressed.
- ML Kit barcode scanner plus CameraX support the Android TV QR-pairing flow.
- Firebase Cloud Messaging/Installations and Google Data Transport support push notifications.
- AppMetrica analytics SDK and service are packaged; the manifest identifies the Flutter AppMetrica plugin.
- Assets retain a broad country-flag set, `neuro`, `optimum`, `ultra`, legacy UI art and a `youturbo` logo. The dynamic runtime catalog is narrower than the static flag inventory.

## Permissions And Platform Surface

Declared permissions include Internet, network state/change, foreground VPN service, wake lock, vibration, camera, notification posting, FCM receive, legacy external-storage read, install referrer, Google advertising ID and Play license check.

Security-positive defaults:

- `allowBackup=false`;
- `debuggable=false`;
- cleartext HTTP disabled by the base network-security configuration;
- VPN service is not exported and requires `BIND_VPN_SERVICE`;
- camera is optional and was requested only when the QR scanner was opened;
- Firebase exported receivers are guarded by Google's C2DM sender permission.

Additional product surfaces not obvious on the main home screen:

- both phone launcher and Leanback/Android TV launcher;
- Always-on VPN support metadata;
- exported Quick Settings tile protected by `BIND_QUICK_SETTINGS_TILE`;
- browsable deep-link schemes `batyavpn:` and legacy-looking `buddyvpn:` with no manifest host/path restriction;
- exported AppMetrica preload-info provider under a package-specific authority.

The broad deep-link schemes and exported attribution provider require code-level input-validation review before calling them vulnerabilities; the manifest alone is insufficient.

## Disclosure And Logging Findings

The APK requests Advertising ID access and packages AppMetrica, Firebase Messaging/Installations, install-referrer and transport components while Google Play declares **no data collected** and **no data shared**. Runtime logs also show AppMetrica-labeled VPN-state/catalog events. That combination creates a serious disclosure-reconciliation requirement even though static presence alone does not prove every SDK field is transmitted.

More severe: this non-debuggable Play build printed complete live Xray/VLESS runtime configurations—including credentials and endpoints—to info-level logcat during the connection attempt. The raw log and APK strings remain quarantined. The defect is therefore present in a release artifact, not merely a debug build.

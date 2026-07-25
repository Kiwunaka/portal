# AdGuard VPN Android Static Summary

**Artifact:** Google Play base APK pulled from the audited LDPlayer instance<br>
**Package:** `com.adguard.vpn`<br>
**Version:** `2.16.65` (`versionCode 348464`)<br>
**APK SHA-256:** `BD4724720BBF8FD0343599166B17FBAD3113B043533E3538B5A37BB8B2C68819`<br>
**APK size:** 51,377,991 bytes; estimated download size 37,241,381 bytes<br>
**Scope:** manifest/resource/package inspection only. No decompilation claim and no security-vulnerability claim.

## Packaging And Signing

- One universal base APK; no split APKs were present on the device.
- Three DEX files with 58,794, 56,652 and 19,046 method references respectively.
- Four ABI families are bundled: `arm64-v8a`, `armeabi-v7a`, `x86_64`, `x86`.
- Each ABI contains `libvpnclient_android.so`, `libcommon_native_jni.so`, `libsentry.so` and `libsentry-android.so`.
- APK Signature Scheme v2 verifies successfully. V1, V3/V3.1, V4 and SourceStamp are absent from this pulled artifact.
- Signer subject: `O=Adguard Software Ltd, L=Limassol, ST=Cyprus, C=CY`; certificate SHA-256 `d2a1529cdff93bef67e50259326f248f82f0e0bc8443e714eedb87a05aca2415`.
- APK manifest reports `2.16.65`, while the native About screen reports `2.16.1`. Treat this as a packaging/display-version mismatch, not two separately proven builds.
- Target and compile SDK are 35.

## Manifest Surface

- 23 activities, 12 services, 10 receivers and 4 providers.
- Exported components observed:
  - launcher `SplashActivity`;
  - custom-scheme router for `adguardvpn://`;
  - custom-scheme router for `sdns://`;
  - Quick Settings tile service protected by `BIND_QUICK_SETTINGS_TILE`;
  - `MegazordService`, exported without a manifest permission;
  - AndroidX WorkManager system-job service and diagnostics receiver with their platform permissions.
- The VPN service is protected by `android.permission.BIND_VPN_SERVICE`.
- A boot receiver supports the enabled-by-default launch-at-boot behavior.
- TV-oriented activities/fragments and a TV fallback activity are packaged in the same APK.
- `allowBackup=true`.
- The linked network-security configuration sets `cleartextTrafficPermitted=true` globally. This expands the cleartext attack surface; it does not prove that VPN payload traffic itself is sent without TLS. Runtime navigation separately observed an HTTP `link.adtidy.info` redirect before the final HTTPS legal/site page.

## Permissions

Declared permissions include network/Wi-Fi state, Internet, wake lock, boot, notifications, exact alarms, battery-optimization exemption, Google Play Billing/install-referrer access, `QUERY_ALL_PACKAGES`, cross-user interaction and multiple Android 14/15 foreground-service categories.

No location, camera, microphone, contacts or broad storage permission was declared. `QUERY_ALL_PACKAGES` matches the native split-tunneling picker, which enumerates installed and system apps.

## SDK And Architecture Signals

- First-party code is concentrated under `com.adguard.vpn` and the reusable `com.adguard.mobile` kit.
- AndroidX WorkManager, Room, Kotlin coroutines, Google Play Billing/Play Core, Google Play Services and Google Data Transport are packaged.
- Sentry Java and native packages/providers are present. Manifest metadata explicitly sets Sentry auto-init and session tracking to `false`; build-time instrumentation names Database, File I/O and Logcat instrumentation.
- The SDK presence alone does not prove third-party telemetry. The current Android privacy notice says enabled crash reports are stored on AdGuard servers and no third-party crash service is used; endpoint ownership was not independently proven here.
- No unobfuscated `firebase`, `okhttp3`, `retrofit2`, `com.squareup`, `bouncycastle`, `conscrypt` or Chromium package root was found. Absence may also reflect obfuscation, repackaging or native implementation.
- The resources table contains 88 string configurations. This is a packaging signal and must not be read as 88 fully supported product languages.

## Review Flags, Not Vulnerability Claims

1. Globally permitted cleartext plus an actually observed HTTP redirect should be replaced with HTTPS-only links and a narrow network-security policy.
2. Exported `MegazordService` has no manifest permission. Its intent validation and caller checks need code/runtime review before any severity claim.
3. The diagnostics UI displays live auth/VPN tokens and offers one-tap copy. This is a concrete shoulder-surfing/clipboard exposure concern even though token values were quarantined outside the repository.
4. `allowBackup=true` should be checked against actual backup rules and stored secret classes.
5. The broad `QUERY_ALL_PACKAGES` permission is product-justified by per-app routing, but the resulting app inventory is sensitive and should remain local unless the user explicitly attaches it to support.

## Commands Used

- `apkanalyzer apk summary|file-size|download-size`
- `apkanalyzer manifest print|permissions`
- `apkanalyzer dex list|references|packages --defined-only`
- `apkanalyzer resources configs|value`
- Android Build Tools `aapt2 dump xmltree`
- Android Build Tools `apksigner verify --verbose --print-certs`
- read-only ZIP inventory through .NET `System.IO.Compression`

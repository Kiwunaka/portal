# VPN Наружу — Redacted Static And Distribution Summary

**Capture date:** 2026-07-22<br>
**Android package:** `online.vpnnaruzhu.client.android`<br>
**Installed build:** `1.8.1` (`versionCode 90`)<br>
**Analysis rule:** no binary was executed outside the already installed Android app; raw endpoints, credentials, tunnel material and vendor API keys are excluded.

## Google Play And Direct Android Artifacts

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Direct universal APK `1.8.1.90-naruzhu-release.apk` | 44,257,061 | `d01cd0c70745b30cb5002dc12211b04fb85f53d14fdbc75b56359ec32aedb402` |
| Play base APK | 15,900,758 | `dbfa64be379af8dfd1879966a09ce46aadd43f5c77326566674879bab2d3afc0` |
| Play HDPI split | 88,255 | `eb88ac89fa310f5a9b0255642ecf7a16f36c177181788b685013c13a6e5cd3e9` |
| Play Russian-language split | 65,945 | `463a1fd34ca08a4de01a0127dc6392a3ab540a59b4a0943cdacc1679c8bf5952` |
| Play x86_64 split | 9,577,166 | `fcaa9c7943ac71be37007666b5f2e61454ef1d6e48b6aa61ae61384145157f66` |

Both channels report the same package, version code/name, minimum SDK 24 and target SDK 36. Their three DEX payloads are byte-identical. The direct APK is the universal build with all four ABIs and bundled resources; Google Play delivered a smaller base plus device-specific density, language and x86_64 splits. Both artifacts have the same signer lineage and Google Play Source Stamp, timestamped two seconds apart on 2026-06-26. This strongly supports the direct APK as the official universal counterpart of the Play build rather than a separately modified client.

APK signing uses a rotated lineage:

- Android 24–32 lineage certificate: `CN=VPNN`, SHA-256 `c56ac913fce3dd5eea1db3ac71dc0c5d5b07abc49a156b89b531aac1e410d340`;
- Android 33+ certificate: Kazakhstan subject `IP ZAMOLOTSKIKH / KIRILL ZAMOLOTSKIKH`, SHA-256 `c5670eec4926a951b06a00c91e437870939476b5bb7e0fedf8122a56a667fa49`;
- APK Signature Schemes v2, v3 and v3.1 verify; Google Play Source Stamp verifies.

## Android Architecture

The app is a Kotlin/Jetpack Compose product using Koin, Ktor, OkHttp/Okio, Kotlin serialization and an AmneziaWG-derived tunnel backend. The universal APK carries these native libraries for ARM64, ARMv7, x86 and x86_64:

- `libam.so`, `libam-quick.so` and `libam-go.so`;
- `libhev-socks5-tunnel.so`;
- AndroidX graphics-path native support.

The manifest exposes six activities, eleven services, five receivers and five providers. Product-owned runtime components include:

- a single exported launcher activity;
- a Quick Settings tile guarded by Android's tile binding permission;
- private foreground connection service and private AWG `VpnService`;
- private boot receiver;
- Firebase Messaging, AppMetrica, Google measurement and Play Billing support.

`allowBackup` and `fullBackupContent` are both false. Declared access is limited to network/Wi-Fi state, Internet, boot, foreground service, notifications, wake lock, billing, cloud messaging, install referrer, advertising ID and AdServices attribution. No camera, microphone, contacts, storage or Android location permission was observed.

The app's own network-security configuration trusts both the Android system roots and a bundled **Russian Trusted Root CA** certificate issued to the Ministry of Digital Development and Communications. That expands the certificate authorities accepted by this app's Android TLS stack. It does not install the root system-wide and does not by itself prove interception of VPN payloads, but it is a material trust decision that should be disclosed in a security review.

## Analytics, Ads And Remote Control

Static code includes:

- Yandex Mobile Ads, Yandex Div and Varioqub;
- AppMetrica analytics, including its screenshot-capture module;
- Firebase Analytics, Crashlytics, Sessions, Messaging, Installations and Remote Config;
- Google measurement, advertising ID, AdServices attribution and Play Billing.

No ad was shown during the seven-day Premium trial, but the account screen explicitly sells Premium as “without ads”, and the monetization stack is fully present.

Firebase Remote Config is not only analytics plumbing. It controls at least Telegram channel/bot destinations, guest free time, VPN/product lists and updates. The update model carries separate **available** and **required** versions, separate download URLs and localized Russian/English messages. The client compares the running version, can present an optional or mandatory update and remembers a previously shown available version.

The DEX also contains product-specific modules named `peremen` and `vpneko`, shared product configuration, guest time, key rebinding, server switching and feature flags. This is evidence of a reusable multi-brand/white-label codebase. It does not prove that every embedded module is reachable from the VPN Наружу build.

## Windows Package

The public Windows redirect delivered `naruzhu_1.0.0.1.zip`:

| File | Bytes | SHA-256 | Signature / metadata |
| --- | ---: | --- | --- |
| ZIP | 7,000,783 | `abccee87ffa81d85e549fc42e56a2d1c37763b97edc148794482669141ebf6f2` | container, no execution |
| `naruzhu.exe` | 15,353,152 | `97e86c7312e29f1eadf7aac5e8dbba5363f02a90b11289364d054f2e29bdcf93` | valid Authenticode signer `NOVINET DOO`, Belgrade, Serbia; no FileVersion, ProductVersion, company, product or description resource |
| `wintun.dll` | 427,552 | `e5da8447dc2c320edc0fc52fa01885c103de8c118481f683643cacc3220dafce` | Wintun 0.14.1; valid timestamped WireGuard LLC signature |

The ZIP filename says `1.0.0.1`, while the official Telegram history names Windows `2.1.6.2` in October 2025 and later advertises new main/alternate algorithms in June 2026. With no executable version resource, the current public package cannot be cleanly reconciled to that release history. The binary was not executed.

## Limits

- No source-code audit, dynamic instrumentation, certificate pinning test or full packet capture was performed.
- Embedded SDK presence proves technical capability, not the exact events or payloads sent in this session.
- Static product-module names indicate a shared codebase, not necessarily live user-facing routes.
- Hashes identify only the artifacts observed on 2026-07-22.

# 4ebur.net Android Static Summary

**Snapshot:** 2026-07-22<br>
**Source:** Google Play split install pulled from the isolated LDPlayer instance<br>
**Package:** `com.cheburnet.mobile`<br>
**Version:** `5.1.0` (`versionCode 210030031`)<br>
**SDK:** min 28, target/compile 36

No APK, signing material, live endpoint, licence key, account token or raw configuration is retained in the repository. The temporary APK set stayed outside the worktree.

## Installed Artifact Set

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `base.apk` | 119,926,769 | `20201EE3118948864FE1DADF1A32E6CBF1A06F976A2C6EB1C0EF8E34241ADBC0` |
| `split_config.hdpi.apk` | 308,751 | `8595288E74045520AF797307135F8144700AF204EAD434B3677F62524F5385BA` |
| `split_config.ru.apk` | 61,849 | `77180D53E11D24EA300C987E0EBC9E54C0E796CD2CB7D476D1B1BDB610B745CB` |
| `split_config.x86_64.apk` | 56,567,855 | `8DD5A75AA522EDC103F8B0A1BF02E1D52B5A9DEF30B4997586625F4609CCB7A5` |

Total installed split payload: **176,865,224 bytes** (~168.7 MiB). The base contains 14 ordinary DEX files plus `assets/audience_network.dex`.

DEX method-reference counts:

| DEX | References | DEX | References |
| --- | ---: | --- | ---: |
| `assets/audience_network.dex` | 27,619 | `classes.dex` | 65,532 |
| `classes2.dex` | 31 | `classes3.dex` | 65,499 |
| `classes4.dex` | 64,874 | `classes5.dex` | 61,624 |
| `classes6.dex` | 34,085 | `classes7.dex` | 65,504 |
| `classes8.dex` | 65,494 | `classes9.dex` | 65,531 |
| `classes10.dex` | 65,469 | `classes11.dex` | 65,503 |
| `classes12.dex` | 17,130 | `classes13.dex` | 65,346 |
| `classes14.dex` | 65,333 |  |  |

This is a very large React Native/Hermes application rather than a thin VPN client.

## Native Runtime And Crash Correlation

The x86_64 split contains 23 native libraries, including React Native/Hermes, Sentry, `libgojni.so`, `libwg-go.so`, `libwg-quick.so` and `libwg.so`. No HEV/TProxy native library exists in either the base or x86_64 split.

That absence matches the controlled runtime failure:

`java.lang.UnsatisfiedLinkError: No implementation found for hev.htproxy.TProxyService.TProxyStartService(...)`

The static/runtime correlation is strong for the tested x86_64 Play artifact. It does not establish failure on ARM devices.

## Permissions And Platform Surface

Declared permissions include:

- Internet, network/Wi-Fi state, foreground service, wake lock, vibration and notifications;
- Google Play Billing and Install Referrer;
- `AD_ID` plus Android AdServices Topics, Attribution and Ad ID;
- Firebase messaging receive;
- legacy read/write external storage;
- AppLovin AppHub service binding.

No camera, microphone, contacts or Android location permission was observed. Google Play nevertheless says the app shares Location with third parties; the likely source is network/ad-tech derived location rather than device GPS, but that is an inference rather than observed payload inspection.

The manifest declares **116 activities, 20 services, 16 receivers and 19 providers**. Exported surfaces include:

- `MainActivity`;
- the Quick Settings tile, protected by `BIND_QUICK_SETTINGS_TILE`;
- the Xray VPN service, protected by `BIND_VPN_SERVICE`;
- WorkManager system components;
- an Appodeal package-added receiver with no manifest-level permission;
- Firebase and Google-auth components with their expected platform protections.

The Appodeal receiver is a review flag only; no exploitability test was performed and this is not a vulnerability claim.

## SDK Footprint

Manifest/classes show a broad advertising, mediation, analytics and push footprint:

- Amazon APS / Amazon Device Ads;
- AppLovin / MAX and AppHub;
- Appodeal;
- Google Mobile Ads, Firebase and Install Referrer;
- Meta Audience Network;
- ByteDance/Pangle;
- Chartboost;
- Digital Turbine/Fyber;
- InMobi;
- ironSource;
- Mintegral/MBridge;
- MobileFuse;
- Moloco;
- myTarget;
- Ogury;
- PubMatic;
- Smaato;
- Unity Ads;
- Vungle;
- Bigo;
- BidMachine;
- PubNative;
- Yandex AppMetrica;
- WonderPush;
- Sentry.

VPN-related code includes Xray (`com.cyberwool.xray`), WireGuard native libraries and Amnezia/AWG namespaces.

## Backup, Transport And Signing

- `android:allowBackup="true"`;
- `android:extractNativeLibs="false"`;
- manifest `android:usesCleartextTraffic="false"`;
- referenced network-security config sets base `cleartextTrafficPermitted="true"` and trusts system anchors, making the manifest-level false value misleading in practice;
- APK Signature Scheme v3 verifies;
- v1/v2/v3.1/v4 do not verify for this split artifact;
- signer and Source Stamp are Google Inc., consistent with Google Play App Signing/distribution.

## Static Takeaway

The product ships a large multi-protocol React Native client with a remarkably heavy ad/mediation stack, old storage permissions, backup enabled and an internally inconsistent cleartext policy. The bundled x86_64 artifact lacks the native implementation required by its HEV/TProxy call path, which explains the observed pre-tunnel crash. The breadth of tracking/advertising components is materially wider than the old public privacy page discloses.

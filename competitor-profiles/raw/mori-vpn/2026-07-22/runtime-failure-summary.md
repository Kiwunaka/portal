# MORI VPN — observed Android runtime failure

**Observed:** 2026-07-22
**Package:** `com.morivpn.mori_vpn_mobile`
**Installed build:** `2.0.5` (`versionCode 116`)
**Installer:** Google Play
**Device:** LDPlayer, primary ABI `x86_64`

## Result

`BLOCKED_BY_BUILD`: the current Google Play installation terminates before the first Flutter screen appears.

- Launch component: `.MainActivity`.
- Android shows the system crash dialog immediately after launch.
- Logcat reports that the Flutter loader checked `x86_64`, `arm64-v8a`, `x86`, `armeabi-v7a` and found no `libflutter.so`.
- The base APK contains Flutter assets and one DEX but no native libraries.
- The installed `x86_64` split contains V2Ray/tunnel/helper libraries but neither `libflutter.so` nor `libapp.so`.
- No MORI onboarding, activation, server list, paywall or settings screen was reachable.
- No VPN permission dialog appeared, `tun0` remained absent and no connection/DNS/leak/speed test was possible.

This is evidence of a broken `x86_64` Play split on the observed emulator. It is not proof that the ARM build fails on physical phones.

## Installed split inventory

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `base.apk` | 45,096,884 | `0ab0217ccf5dfb5a967126bc6c3583c6467ce5628df529f1d6b173cacf68d819` |
| `split_config.hdpi.apk` | 53,855 | `f3fc184196d49bfe45f9bea91867df92f542ab0fddd21562ffd40ccec3598990` |
| `split_config.ru.apk` | 24,985 | `4759c25565901dc792eb0b1b3fad42cdeede634c518eeae7019219dc4d825350` |
| `split_config.x86_64.apk` | 14,730,110 | `8a38e7ab5bcb8a0e2bb8f20a96eb6ef38371cccec844e350419443be04f59893` |

Native libraries present in the `x86_64` split:

- `libv2jni.so`
- `libtun2socks.so`
- `libsurface_util_jni.so`
- `libnative_crypto.so`
- `libimage_processing_util_jni.so`
- `libdatastore_shared_counter.so`
- `libbarhopper_v3.so`

Missing runtime-critical libraries: `libflutter.so`, `libapp.so`.

## Signing provenance

- APK Signature Scheme v2/v3: verified.
- Signer: Google Play app signing (`Google Inc`).
- Certificate SHA-256: `fec7dda3c6f21ee179f2e2cc1f9e66e5a4bb9c3602b534cda336e44219cbee97`.
- Google Source Stamp verified; timestamp observed: `2026-06-12T00:13:22Z`.

## Evidence

- [`screenshots/android-startup-crash.png`](screenshots/android-startup-crash.png)

No raw logcat dump is retained because only the minimal failure signature is needed for this audit.

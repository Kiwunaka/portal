# Quattro VPN — observed Android runtime failure

**Observed:** 2026-07-22<br>
**Package:** `ru.quattrocloud.vpnapp`<br>
**Installed build:** `0.18.1` (`versionCode 19`)<br>
**Device:** LDPlayer, primary ABI `x86_64`

## Result

`BLOCKED_BY_BUILD`: the installed direct-distribution build never reaches its first Flutter screen on the observed emulator.

- Launch component: `ru.quattrocloud.vpnapp/.MainActivity`.
- Android remains on the black splash with the white/red Q, then the process terminates.
- Logcat reports `UnsatisfiedLinkError`: the packaged `libflutter.so` is `EM_AARCH64`, not `EM_X86_64`.
- The APK advertises `x86_64`, but that ABI contains `libnpvpnBox.so` and Dart JNI helpers without an x86_64 Flutter engine/application pair. ARM directories do contain Flutter artifacts.
- Firebase/Crashlytics initializes before the crash.
- No onboarding, activation, paywall, server list, settings or Quattro Security screen was reachable.
- No Android VPN permission dialog appeared, no `tun0` interface appeared and no connection/DNS/leak/speed test was possible.

This result applies to the installed debug-signed sideload on the current `x86_64` LDPlayer. It is not proof that the ARM build fails on physical phones.

## Installed artifact

| Field | Observation |
| --- | --- |
| APK size | 180,839,403 bytes |
| SHA-256 | `b5e0cd3ee05c5917b74ef24d87223e9332d0e8c6fbbf489f3998751237f57192` |
| Signature schemes | v2 only; no v1/v3/v4/source stamp |
| Certificate | Android Debug certificate, RSA 2048 |
| Certificate SHA-256 | `1ee0f75ffc28adb350bfbd33daf56cd7059d7d75e186873caa9ac81050167984` |
| Installer/initiator | `com.android.coreservice`, LDPlayer privileged CoreService |

The installer provenance and debug certificate show that this is a sideload/test artifact, not a Google Play-proven production package. Its version matches the public Telegram/Yandex `0.18.1` release, but binary identity with that public download was not verified.

## Evidence

- [`01-launch-400ms.png`](screenshots/01-launch-400ms.png)
- [`02-after-3s.png`](screenshots/02-after-3s.png)
- [`03-google-play-not-found.png`](screenshots/03-google-play-not-found.png)

No raw logcat, endpoint list or connection material is retained in the repository.

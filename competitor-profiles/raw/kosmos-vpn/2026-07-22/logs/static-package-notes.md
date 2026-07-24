# Космос VPN 1.3.3 — Redacted Android Package Notes

Snapshot: 2026-07-22. APKs were pulled from the installed Google Play package into the audit’s sensitive temporary area. Raw binaries, endpoints and any user/device material are intentionally excluded from the repository.

## Package

- Package: `ru.space.vpn`
- Version: 1.3.3 (`versionCode 1030301`)
- Split APKs observed: base, Russian language, x86_64 and xhdpi resources
- Approximate split sizes: base 15.2 MB; x86_64 74.5 MB; other two below 0.2 MB each
- `minSdkVersion`: 32
- `targetSdkVersion`: 35
- compile SDK: 36
- Native Jetpack Compose UI; no Flutter runtime observed
- Main activity is exported, portrait-only and marked non-resizable
- Custom deep-link scheme: `kosmosvpn:`

## VPN And Native Engine

- Non-exported foreground VPN service protected by `android.permission.BIND_VPN_SERVICE`
- Largest native payload: `libbox.so`, approximately 68.5 MB in the x86_64 split
- Barcode engine: `libbarhopper_v3.so`, approximately 5.9 MB
- Static symbols/strings show bundled capabilities from sing-box/sing-tun, Clash/MetaCubeX/Yacd-meta, Xray/v2ray-core, WireGuard, VLESS, VMess, Trojan, Hysteria/Hysteria2, TUIC, Shadowsocks, Reality, QUIC, ECH, SOCKS5 and Tailscale/DERP
- Capability presence is not evidence that every transport is active in the live product

## Permissions And Components

Observed capabilities include:

- internet and network/Wi-Fi state;
- foreground service and system-exempted foreground-service type;
- notifications;
- receive boot completed;
- camera;
- wake lock;
- request ignore battery optimizations;
- Google Play licensing/PairIP;
- Install Referrer;
- advertising ID and Android AdServices attribution identifiers.

The manifest also contains Firebase Analytics/Measurement, Crashlytics, Firebase Sessions, Installations and Google DataTransport/CCT components. This does not prove every optional SDK path is used, but it directly undermines an unqualified store declaration that no data is collected.

`allowBackup=true` is enabled. Google Play source stamps and split metadata are present.

## Product Assets

- CameraX and ML Kit barcode components support the Android TV QR scanner.
- `res/raw/background.mp4` is approximately 1.08 MB and supplies the animated cosmic home/onboarding background.
- `assets/countries.json` contains generic metadata for roughly 192 countries. It is not the current server inventory; the live selector exposed eleven countries.

## Security And Evidence Boundaries

- Raw APKs, DEX files, native libraries, live service endpoints and any personalized cabinet/deep-link values remain outside the repository.
- No certificate bypass, traffic interception, secret extraction or modification of the third-party app was performed.
- Static package observations are implementation evidence, not proof of runtime collection, protocol enablement or server-side behavior.

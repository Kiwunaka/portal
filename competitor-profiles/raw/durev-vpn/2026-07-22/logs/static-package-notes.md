# Durev VPN — Redacted Android Package Notes

**Captured:** 2026-07-22<br>
**Package:** `com.durevpn.durevvpn`<br>
**Version:** `2.0.1-phone` / `1464`<br>
**Scope:** locally installed Google Play split APKs; raw APKs remain outside the worktree because they contain live control-plane and connection material.

## Package shape

- Base APK: approximately 9.5 MB.
- x86_64 split: approximately 22.6 MB.
- xhdpi resources: approximately 58 KB.
- Russian-language split: approximately 25 KB.
- Minimum Android SDK 24; target/compile SDK 35.
- Flutter application using the Impeller renderer.
- Google Play bundle/source-stamp metadata is present.

## Android components

- Exported main activity: `com.durevvpn.durev_new.MainActivity`.
- Custom deep-link scheme: `durevvpn:`.
- Verified HTTPS app links cover both official brand domains.
- Non-exported `DurevVpnService` runs as a VPN foreground service.
- Exported `VpnTileService` provides a Quick Settings tile.
- CameraX and ML Kit barcode components support QR scanning/pairing.

Requested capabilities include internet/network state, Wi-Fi state/change, camera, notifications, boot completion, foreground VPN/special-use service and battery-optimization exemption. Presence of a permission does not prove it was exercised in the audited route.

## Native networking stack

Observed x86_64 native payloads:

| Library | Approximate size | Role inferred from package |
| --- | ---: | --- |
| `libapp.so` | 8.1 MB | Flutter AOT application |
| `libgojni.so` | 33.1 MB | Go/Xray/Sing networking bridge |
| `libhev-socks5-tunnel.so` | 340 KB | SOCKS5 tunnel component |
| `libflutter.so` | 12.3 MB | Flutter runtime |

Go module and symbol evidence includes Xray-core/libxray, Reality, sing/sing-shadowsocks, quic-go, uTLS and DNS libraries. Capability strings include WireGuard, Shadowsocks, VLESS, VMess, Trojan, QUIC, Reality, Xray, SOCKS5, SSH and ECH. This documents the bundled engine; it does not prove every protocol is available in the live commercial configuration.

## Product surface visible in assets

The current Flutter assets expose a much larger signed-in surface than the no-key entry screen:

- world/country selection and extensive country flags;
- VPN days, tunneling, settings and refresh;
- key management and key setup;
- invite friends, beta testing and cash/referral imagery;
- warning/info/error TV dialogs;
- multiple Durev character illustrations and country-map art;
- desktop/Windows presentation assets.

These names establish that the functions are shipped, not that all are remotely enabled.

## Resilience and telemetry notes

The binary includes multiple official API/site origins plus rotating cover-looking domains and direct-IP fallback material. Exact hosts, IPs and paths are intentionally excluded. The architecture indicates control-plane resilience under DNS/domain blocking.

Two narrow network-security entries set `cleartextTrafficPermitted=true` for entries whose domain values did not resolve cleanly in the decoded artifact. This is not proof of a global cleartext policy; it is a configuration smell requiring runtime confirmation.

No obvious standalone Firebase Analytics, Crashlytics, Sentry, AppsFlyer or Adjust package was identified in the static scan. Google DataTransport/CCT dependencies are present. Absence of a recognizable SDK does not rule out first-party analytics, account/session metadata or server-side logging.

## Evidence hygiene

- Raw APKs, endpoint strings and any generated pairing payloads remain under the sensitive temporary audit root, outside Git.
- No raw server endpoint, access key, direct IP, QR payload, device token or account identifier is copied into this document.
- Static findings are labelled as capabilities; only live observed behavior is treated as executed product behavior.

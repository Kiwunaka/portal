# MantaRay Android — Application Profile

**Package:** `com.mantaray.vpn`
**Version:** 2.25.8 (311)
**Official APK:** `https://storage.yandexcloud.net/ocean/MantaTech/android/mantaray-universal.apk`
**Related provider:** Shuka VPN
**Generated:** 2026-07-12
**Evidence:** PASS_STATIC + PASS_EMULATOR_UI; VPN tunnel NOT_CONNECTED

## Binary

| Field | Value |
|---|---|
| Size | 160,872,388 bytes |
| SHA-256 | `2DAA9D98A1E9D7B974974FD3F6E6BD820FD31D857D2B43F9C15EDE34E1148BEC` |
| SDK | min 24 / target 35 |
| Debuggable | false |
| Signing | v2 only; MantaRay production identity |
| Cert SHA-256 | `86c79429c2872c020562117918a3bb698cf93a223b3c47b3f7907e713ebc3e37` |

## Internals

- Flutter with first-party `libmantaray_core.so`; runtime marker `5.13.1`, `FFI v2`.
- No AD_ID or ad-network stack.
- Firebase Messaging/Installations and ML Kit Barcode are present. A tiny Firebase analytics connector namespace exists, but the full Analytics SDK was not found.
- First-party `api.mantatech.ltd` routes cover update checks, crash reports, AI chat/feedback/limits and routing telemetry.
- GeoIP/geosite assets and an OpenWRT script are delivered from Yandex Cloud storage.
- Powerful permissions include package usage stats, query-all-packages, install packages, camera, boot and multicast/Wi-Fi access.

## UI and Routing

- Add config by typed/pasted link, clipboard or QR.
- Three clear presets: VPN only where needed; VPN for all except RU; VPN for everything.
- Four-step custom builder: mode, exceptions, sites/IPs, name. Each rule can route via VPN, direct or block.
- Settings expose theme, simplified mode, quick tile, full/small widgets, self-update, geo database update and autoconnect.
- Diagnostics are unusually strong: VPN logs, session traffic, connection checks, custom routing editor, local destination/routing-decision history and app logs.
- First launch spent roughly 15–20 seconds preparing geo databases. The update checker returned 404 in emulator logs but did not crash.

## Assessment

Best functional client in this wave. The routing mental model, local diagnostics, widgets and TV-adjacent controls are directly reusable product ideas. Main caveats are broad package visibility/usage access, self-update, and first-party routing telemetry that needs transparent disclosure.

## Screenshots

- Home (external snapshot: `raw/market-wave2/2026-07-12/screenshots/app-mantaray-home.png`)
- Add config (external snapshot: `raw/market-wave2/2026-07-12/screenshots/app-mantaray-add-config.png`)
- Routing presets (external snapshot: `raw/market-wave2/2026-07-12/screenshots/app-mantaray-routing-presets.png`)
- Routing builder (external snapshot: `raw/market-wave2/2026-07-12/screenshots/app-mantaray-routing-builder.png`)
- Settings (external snapshot: `raw/market-wave2/2026-07-12/screenshots/app-mantaray-settings.png`)
- More settings (external snapshot: `raw/market-wave2/2026-07-12/screenshots/app-mantaray-settings-more.png`)

The bottom settings screenshot containing a device HWID was excluded from repository evidence.

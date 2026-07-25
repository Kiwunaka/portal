# MORI VPN — static Android summary

**Observed build:** `2.0.5` (`116`) from Google Play
**Scope:** installed APK set only; no exploitation or active probing

## Application shape

- Flutter application wrapped by Google Play PairIP: application class `com.pairip.application.Application`.
- Custom deep-link scheme: `morivpn://` with no host restriction in the observed manifest.
- Package queries include ordinary HTTPS handling and `phantom://` wallet integration.
- No explicit `allowBackup="false"` was observed; this does not by itself prove that backup is enabled on every Android version.

## Declared access

Notable permissions include internet/network state, camera, notifications, foreground services, change-network-state, battery-optimization exemption request, Google Play Billing and Play licensing. The `x86_64` split also declares legacy phone-state/external-storage permissions.

Observed component totals: 7 activities, 11 services, 4 receivers and 3 providers.

App-owned and security-relevant components:

- exported `.MainActivity`;
- private custom `com.morivpn.mori_vpn_plugin.vpn.MoriVpnService`;
- `VpnWatchdogService`;
- duplicate VPN/V2Ray stacks from `dev.amirzr.flutter_v2ray_client` and `com.thethtwe.v2ray`;
- exported Quick Settings tile;
- exported `com.thethtwe.v2ray.v2ray.V2rayReceiver` listening for the generic `V2RAY_CONNECTION_INFO` action without a manifest permission;
- ML Kit barcode scanner/camera, share provider, URL launcher and Play Billing integration.

The exported receiver is an attack-surface concern worth fixing upstream; no broadcast was sent and no exploit test was performed.

## Registered Flutter plugins

- `app_links`
- `connectivity_plus`
- `device_info_plus`
- `flutter_icmp_ping`
- `flutter_secure_storage`
- `flutter_v2ray_client`
- `in_app_purchase_android`
- `mobile_scanner`
- `mori_vpn_plugin`
- `package_info_plus`
- `path_provider_android`
- `permission_handler_android`
- `share_plus`
- `shared_preferences_android`
- `url_launcher_android`
- `v2ray_myanmar`

Google Tink and Flutter Secure Storage are present. No Firebase, AppMetrica or Sentry package was observed in the DEX inventory.

## Bundled product assets

- `geoip.dat` and `geosite.dat`;
- mobile/tablet animation frames;
- QR-pairing assets;
- desktop/window-manager assets, indicating a shared cross-platform codebase.

## Interpretation

The build contains substantially more product surface than the live `x86_64` runtime exposes: multiple VPN engines, QR device pairing, billing, Phantom/Solana wallet hooks and a large localized product catalog. Because the application crashes before Flutter starts, these are implementation/static signals, not proof that every feature is live or server-enabled.

# Lagom VPN — Redacted Static Summary

Snapshot: 2026-07-22. Raw APKs and hashes are retained only in the audit-sensitive temporary directory.

| Item | Observed |
| --- | --- |
| Package/version | `com.lagomproductsllc.lagomvpn`, `0.21-mobile` / 134 |
| SDK | min 26, target 37 |
| Debuggable | false |
| Installed splits | base + arm64 + hdpi, about 90.5 MB total |
| VPN component | `V2RayVpnService`; Android Always-On support declared |
| Quick Settings | `QSTileService`; removed at teardown |
| Commercial/identity SDK families | Google Billing, Google/Firebase, Google Measurement, Yandex Auth, Facebook, VK install referrer |
| Telemetry/support SDK families | Firebase Analytics/Remote Config/Crashlytics/Sessions/Messaging, AppMetrica, Sentry, Crowdin, embedded online chat |
| Privacy-relevant permissions | Advertising ID and AdServices attribution/ad-ID/Topics/Custom Audience, notifications, boot, network/Wi-Fi, camera, biometrics |

This is component and permission evidence, not a claim that each SDK transmitted data in the observed session. Endpoints, signing material, personalized bot parameters and raw connection configuration are deliberately omitted.

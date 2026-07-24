# Батя VPN 1.3.9 — sanitized connection notes

Snapshot date: 2026-07-22<br>
Device: LDPlayer Android 14<br>
Selected route: Optimum

Raw runtime logs were inspected only in quarantined temporary storage because the app writes live VPN credentials, endpoints and generated device identifiers to Android logcat. None of those values are retained here.

## Observed flow

1. The native connect control immediately turns green before Android consent completes.
2. Android's standard VPN consent is shown; there is no app-owned traffic/privacy disclosure first.
3. After consent, Android asks for notification permission.
4. The notification request was denied for the test and later reset to the original unasked/default state.
5. `tun0` did not appear during the first 15-second poll while the notification dialog was visible.
6. After dismissing the notification dialog, `tun0` still did not appear during a second 15-second poll.
7. The app silently returned the connect control to its disconnected state without an error message.
8. A suppressed-output HTTPS request succeeded, but because `tun0` was absent this proves only normal device connectivity, not VPN connectivity.

## Sanitized failure evidence

- Device-check and device-registration calls failed during API fallback with an expired TLS certificate.
- Runtime state returned to `disconnected`, with no user-facing explanation.
- The runtime simultaneously had a catalog of 11 routes, matching the selector count, so this was not simply an empty server-list failure.

## Runtime architecture visible in logs

- VLESS proxy outbounds over XHTTP/TLS.
- Multiple general proxy outbounds plus dedicated YouTube routes.
- A large direct-routing list for Russian/local services and private/local network suffixes.
- QUIC (`UDP/443`) and common encrypted-DNS ports are blocked by route rules.
- BitTorrent is routed direct rather than through the proxy.
- AppMetrica receives VPN-state and server-catalog health events.

## Logging defect

The production-installed build emits the full generated runtime configuration at info level, including live access IDs and endpoint data. Modern Android limits general cross-app log access, but ADB, privileged diagnostics, vendor tooling and any attached crash/log collector can still expose this material. POKROV should never log complete connection configs or credentials at any level in a release build.

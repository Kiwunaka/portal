# Open Beta Release Notes

Last updated: 2026-08-12

Status: Android direct APK published and synced to production. Owner/channel posting remains manual.

POKROV Android `1.0.2-beta.1` is the current direct-APK release. It is
production-signed for same-signer updates and targets the production POKROV
API. Google Play is not part of this release.

Public release:
`https://github.com/Kiwunaka/pokrov/releases/tag/v1.0.2-beta.1`.
The anonymous full-download smoke matched the published `287207515`-byte APK
and SHA-256 `9820CDA01DEA74CDBD34A9D1FA76B7CFC1DD24D0D452D8521239DFF9DA6BEACA`.

Known limits mirror `shared/beta-known-limitations.json` and
`docs/launch/known-issues.md`.

2026-08-12 Android refresh:

- Simplified Home, Locations, Rules, Profile, support, and checkout journeys.
- Added the branded Quick Settings tile and a configurable foreground
  notification with country, route, speed, open, and disconnect controls.
- Added Android per-app routing in both directions: only selected apps through
  VPN, or selected apps direct while everything else uses VPN.
- Smart split, both per-app directions, support AI, checkout, diagnostics,
  notification controls, and the final signed APK were verified on physical
  Android 12 hardware.
- Monthly pricing is `239 ₽`; 3, 6, 9, and 12 months are `669 / 1199 / 1699 /
  1999 ₽`. The one-time first-month welcome offer remains `99 ₽`.
- In-app support uses the exact deployed
  `deepseek/deepseek-v4-flash-0731` model without a hard output-token cap.

Known limits:

- `outside_store_beta`: Android distribution is a signed direct APK through
  GitHub Releases and the official POKROV download handoff, not an app store.
- `runtime_download_handoff`: production `/api/client/apps`, API health, and
  the live provider-policy smoke passed for the exact `1.0.2` URL, size, and
  SHA-256.
- `windows_unsigned`: Windows may show Microsoft Defender SmartScreen or an
  unknown-publisher warning.
- `android_public_download`: the Android APK is public without account auth;
  account creation happens after installation. Windows remains a separate
  cabinet-guided beta path.
- `payment_beta`: paid checkout is Lava.top-only for the beta; production
  refund, chargeback, reconciliation, and fulfillment-ledger evidence is still
  follow-up.
- `ru_origin_not_claimed`: RU-origin readiness is not claimed; the beta
  decision accepted an operator skip for that gate.
- `android_endurance`: release-critical phone checks passed; 100-cycle,
  Wi-Fi/mobile handoff, WARP, battery, sleep/resume, and MTU endurance remain
  separate owner tests.
- `support_best_effort`: support is best-effort during beta through the cabinet
  and `@pokrov_supportbot`.
- `apple_readiness_only`: iOS and macOS are not release platforms for this wave.

# Open Beta Release Notes

Last updated: 2026-08-14

Status: POKROV `1.0.5-beta.1` Android/Windows direct-release candidate passed local exact gates. Public publication and production runtime sync are the remaining release steps.

POKROV Android `1.0.5-beta.1` is the next direct-APK release. It is
production-signed for same-signer updates and targets the production POKROV
API. Google Play is not part of this release.

Planned public release:
`https://github.com/Kiwunaka/pokrov/releases/tag/v1.0.5-beta.1`.

Known limits mirror `shared/beta-known-limitations.json` and
`docs/launch/known-issues.md`.

2026-08-14 Android/Windows refresh:

- Added direct platform-aware downloads and a short-lived one-time acquisition handoff into Android and Windows.
- Made the available `Обычный / Белые списки` location variants explicit in the app.
- Simplified Home, Locations, Rules, Profile, support, and checkout journeys.
- Added the branded Quick Settings tile and a configurable foreground
  notification with country, route, speed, open, and disconnect controls.
- Added Android per-app routing in both directions: only selected apps through
  VPN, or selected apps direct while everything else uses VPN.
- Smart split, both per-app directions, support AI, checkout, diagnostics and
  notification controls retain automated coverage. Exact-final endurance,
  WARP and Wi-Fi↔LTE remain manual owner gates and are not presented as a pass.
- Monthly pricing is `239 ₽`; 3, 6, 9, and 12 months are `669 / 1199 / 1699 /
  1999 ₽`. The one-time first-month welcome offer remains `99 ₽`.
- In-app support uses the exact deployed
  `deepseek/deepseek-v4-flash-0731` model without a hard output-token cap.

Known limits:

- `outside_store_beta`: Android distribution is a signed direct APK through
  GitHub Releases and the official POKROV download handoff, not an app store.
- `runtime_download_handoff`: production `/api/client/apps`, public URLs and
  runtime hashes must match `1.0.5-beta.1` before this candidate is announced.
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

# Open Beta Release Notes

Last updated: 2026-06-07

Status: prepared for outside-store public beta. Owner/channel posting remains manual.

POKROV Open Beta v4 focuses on outside-store Android and Windows distribution, app-first onboarding, cabinet support, and safer release gates.

Known limits mirror `shared/beta-known-limitations.json` and
`docs/launch/known-issues.md`.

2026-06-04 refresh:

- Android APK and Windows EXE were refreshed from the `0.2.0-beta.1+20260604-rc-local` handoff.
- Owner approved this current outside-store beta without production Android signing and without trusted Windows signing.
- Public copy must still keep beta, outside-store, and unknown-publisher limitations clear.

Known limits:

- `outside_store_beta`: Android APK and Windows EXE distribution is GitHub
  Releases plus the official cabinet, not app stores.
- `runtime_download_recheck`: runtime download links were verified for the
  `2026-05-15` beta evidence pack; re-check `/api/client/apps` before new
  artifact or URL announcements.
- `windows_unsigned`: Windows may show Microsoft Defender SmartScreen or an
  unknown-publisher warning.
- `downloads_limited`: downloads may be visible only to approved beta users.
- `payment_beta`: paid checkout is Lava.top-only for the beta; production
  refund, chargeback, reconciliation, and fulfillment-ledger evidence is still
  follow-up.
- `ru_origin_not_claimed`: RU-origin readiness is not claimed; the beta
  decision accepted an operator skip for that gate.
- `android_audit_attested`: Android uses the current outside-store beta signing
  posture for this refresh; do not describe it as Play/store-signed or raw
  device-audit-proven.
- `support_best_effort`: support is best-effort during beta through the cabinet
  and `@pokrov_supportbot`.
- `apple_readiness_only`: iOS and macOS are not release platforms for this wave.

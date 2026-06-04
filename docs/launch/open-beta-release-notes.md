# Open Beta Release Notes

Last updated: 2026-06-04

Status: prepared for outside-store public beta. Owner/channel posting remains manual.

POKROV Open Beta v4 focuses on outside-store Android and Windows distribution, app-first onboarding, cabinet support, and safer release gates.

2026-06-04 refresh:

- Android APK and Windows EXE were refreshed from the `0.2.0-beta.1+20260604-rc-local` handoff.
- Owner approved this current outside-store beta without production Android signing and without trusted Windows signing.
- Public copy must still keep beta, outside-store, and unknown-publisher limitations clear.

Known limits:

- Android APK and Windows EXE distribution is GitHub Releases plus the official cabinet, not app stores.
- Runtime download links were verified for the `2026-05-15` beta evidence pack; re-check `/api/client/apps` before new artifact or URL announcements.
- Windows may show an unknown-publisher warning; trusted signing is not required for this beta wave.
- Android uses the current outside-store beta signing posture for this refresh; do not describe it as Play/store-signed.
- Paid checkout is Lava.top-only for the beta; production refund, chargeback, and reconciliation evidence is still follow-up.
- Downloads may be visible only to approved beta users.
- iOS and macOS are not release platforms for this wave.
- RU-origin readiness is not claimed; the beta decision accepted an operator skip for that gate.

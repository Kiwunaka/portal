# Public Beta Release Runbook

Last updated: 2026-08-15

Document class: `EVIDENCE`

Scope: historical outside-store beta execution for `v1.0.4-beta.1`. That beta
has been superseded; current release truth comes from the publishing/signing
guide and the exact client handoff. This retained runbook does not authorize
store availability, trusted Windows signing, raw Android audit or RU-origin
claims.

## Retained Decision

Public beta is GO for Android APK and Windows EXE outside app stores as of `2026-05-15`. This is not a `1.0.0` release, not an app-store release, and not a trusted Windows-signing claim.

The distributed `v1.0.4-beta.1` is a public GitHub prerelease in
`Kiwunaka/pokrov`, not a stable or store release.

That beta Android handoff used
`pokrov-android-arm64-v8a.apk` by default and
`pokrov-android-armeabi-v7a.apk` only for legacy ARMv7 devices. Market AAB
handoff remains separate and does not imply store availability.

## Gate Order

1. Run local platform tests.
2. Run marketing and webapp builds.
3. Run client preflight against `POKROV-app`.
4. Attach runtime download smoke evidence.
5. Attach Lava.top provider evidence for the exact checkout route being enabled; the public beta path has `2026-05-15` evidence for live invoice creation, callback safety, idempotency, and paid-key email delivery probe readiness.
6. Attach Android physical release-build audit evidence.
7. Attach current-origin and brain-origin reports separately. RU-origin may be an explicit accepted skip only when the owner accepts that no RU-origin availability claim will be made.
8. Update launch decision before deploy or announcement.

## Blocked Means Blocked

If a gate depends on missing credentials, external host access, signing, or physical device access, record `blocked by missing access` instead of substituting a local check.

Keeping checkout unavailable is acceptable for any route without current Lava.top and email delivery evidence. The `2026-05-15` Lava.top/email evidence allows the Lava-only public beta checkout path to stay enabled. Refund/chargeback reconciliation remains a runbook requirement before stronger production payment claims.

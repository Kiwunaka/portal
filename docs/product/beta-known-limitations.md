# Beta Known Limitations

Last updated: 2026-07-10

Structured source: `shared/beta-known-limitations.json`

This page is the product-facing mirror of the outside-store beta limitation
contract. Keep it aligned with `docs/launch/known-issues.md`.

## Current Limitations

- `outside_store_beta`: Android APK and Windows EXE are outside-store beta
  artifacts distributed through the official cabinet and GitHub Releases path.
  Do not imply Google Play, Microsoft Store, WinGet, Apple, stable, or broad
  public-store availability.
- `runtime_download_recheck`: runtime download links were verified for the
  `2026-05-15` beta evidence pack and must be rechecked through
  `/api/client/apps` before a new artifact, URL, or release-candidate
  announcement.
- `windows_unsigned`: Windows beta may remain unsigned and may show Microsoft
  Defender SmartScreen or unknown-publisher warnings. Do not claim trusted
  Windows signing, SmartScreen reputation, Microsoft Store, or WinGet readiness.
- `downloads_limited`: published beta binaries are publicly reachable through
  the official cabinet and GitHub Releases, but every new candidate still
  requires exact URL and runtime handoff verification. Do not claim store
  availability or a newly published candidate without current unauthenticated
  URL, `/api/client/apps`, and manual install/connect evidence.
- `payment_beta`: paid checkout is Lava.top-only for the current public beta.
  Production refund, chargeback, reconciliation, and fulfillment-ledger
  evidence remains follow-up before stronger payment claims.
- `ru_origin_not_claimed`: RU-origin reachability was skipped by operator for
  the beta decision and must be checked separately before any RU-origin
  readiness claim.
- `android_audit_attested`: Android physical release-build localhost/control
  surface audit is owner-attested for beta. Raw device audit proof,
  Play/store signing, and stronger Android safety claims remain manual
  follow-up.
- `support_best_effort`: support is best-effort during beta through the cabinet
  and `@pokrov_supportbot`. Do not imply SLA-backed support until live operator
  workflow evidence exists.
- `apple_readiness_only`: iOS and macOS are readiness tracks only and are not
  release platforms for this beta wave. Do not imply App Store, TestFlight,
  notarized macOS, or Apple launch availability.

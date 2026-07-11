# Known Issues

Last updated: 2026-07-10

Structured source: `shared/beta-known-limitations.json`

This launch-facing page mirrors `docs/product/beta-known-limitations.md` so
support handoffs and public copy stay inside the same beta claim boundary.

## Current Issues

- `outside_store_beta`: Android APK and Windows EXE are outside-store beta
  artifacts distributed through the official cabinet and GitHub Releases path.
  They are not app-store releases.
- `runtime_download_recheck`: runtime download links were verified for the
  `2026-05-15` beta evidence pack; re-check `/api/client/apps` before any new
  artifact, URL, or release-candidate announcement.
- `windows_unsigned`: Windows beta may remain unsigned and may show Microsoft
  Defender SmartScreen or unknown-publisher warnings.
- `downloads_limited`: published beta binaries are publicly reachable through
  the official cabinet and GitHub Releases, but every new candidate still
  requires exact URL and runtime handoff verification. Do not claim store
  availability or a newly published candidate without current unauthenticated
  URL, `/api/client/apps`, and manual install/connect evidence.
- `payment_beta`: paid checkout is Lava.top-only for the current public beta;
  production refund, chargeback, reconciliation, and fulfillment-ledger
  evidence remains follow-up before stronger payment claims.
- `ru_origin_not_claimed`: RU-origin reachability was skipped by operator for
  the beta decision and must be checked separately before any Russia-origin,
  Telegram-from-Russia, or RU readiness claim.
- `android_audit_attested`: Android physical release-build audit is
  owner-attested for the beta; raw device evidence is not attached as public
  proof, and stronger Android safety claims remain follow-up.
- `support_best_effort`: support is best-effort during beta through the cabinet
  and `@pokrov_supportbot`.
- `apple_readiness_only`: iOS and macOS are readiness tracks only and are not
  release platforms for this beta wave.

# Known Issues

Last updated: 2026-08-22

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
- `windows_unsigned`: the published `1.0.0-beta` Windows artifact was distributed
  unsigned under the recorded beta-wave owner decision and may show Microsoft
  Defender SmartScreen or unknown-publisher warnings. That accepted skip is
  exact-candidate historical evidence only; any rebuild, replacement, runtime
  re-sync, or later public candidate requires trusted-signing `PASS`, while
  unsigned outputs are non-public engineering smoke.
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
- `linux_not_shipped_1_2_0`: Linux is `NOT_SHIPPED_IN_1.2.0`; Android and
  Windows remain the only public release pair. Compatibility-client guidance,
  transitive desktop dependencies and dormant Linux contracts are not an
  official POKROV Linux binary or support promise.
- `android_oem_background_limits`: OEM battery/background restrictions,
  VPN-permission handling and cached notification/tile state may stop or delay
  recovery. Do not promise uninterrupted Android background operation. Run the
  exact `1.2.0` candidate on the physical OEM matrix and route affected users
  through the bounded Android background/power guidance.
- `support_best_effort`: support is best-effort during beta through the cabinet
  and `@pokrov_supportbot`.
- `apple_readiness_only`: iOS and macOS are readiness tracks only and are not
  release platforms for this beta wave.

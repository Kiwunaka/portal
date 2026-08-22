# Beta Known Limitations

Last updated: 2026-08-22

Structured source: `shared/beta-known-limitations.json`

This page is the product-facing mirror of the outside-store beta limitation
contract. Keep it aligned with `docs/launch/known-issues.md`.

## Current Limitations

- `outside_store_beta`: Android APK and Windows EXE are outside-store beta
  artifacts distributed through the official cabinet and GitHub Releases path.
  Availability copy must keep current limitations, official-source guidance,
  and support routing visible.
  Do not imply Google Play, Microsoft Store, WinGet, Apple, stable, or broad
  public-store availability.
- `runtime_download_recheck`: runtime download links were verified for the
  `2026-05-15` beta evidence pack and must be rechecked through
  `/api/client/apps` before a new artifact, URL, or release-candidate
  announcement.
- `windows_unsigned`: the published `1.0.0-beta` Windows artifact was distributed
  unsigned under the recorded beta-wave owner decision and may show Microsoft
  Defender SmartScreen or unknown-publisher warnings. That accepted skip is
  exact-candidate historical evidence only. Any rebuild, replacement, runtime
  re-sync, or later public candidate requires trusted-signing `PASS` for that
  exact artifact; unsigned outputs are non-public engineering smoke.
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
- `linux_not_shipped_1_2_0`: the official POKROV Linux client is
  `NOT_SHIPPED_IN_1.2.0`. The public release pair remains Android and Windows.
  Flutter/Linux dependencies, compatibility-client instructions, dormant
  Linux error codes and the PB-09 placeholder are not an official Linux
  artifact, daemon, package, support matrix or availability claim.
- `android_oem_background_limits`: Android OEM battery/background policy,
  VPN-permission handling, notification behavior and cached Quick Settings
  state can stop or delay recovery despite the foreground-service contract.
  Do not promise uninterrupted background operation across OEMs. The exact
  `1.2.0` candidate still requires physical background, screen-off, lockscreen,
  notification, tile, permission-revoke and reconnect evidence; safe support
  routing remains `AND-BG-001/002/003`, `AND-VPN-004` and `PB-08`.
- `support_best_effort`: support is best-effort during beta through the cabinet
  and `@pokrov_supportbot`. Do not imply SLA-backed support until live operator
  workflow evidence exists.
- `apple_readiness_only`: iOS and macOS are readiness tracks only and are not
  release platforms for this beta wave. Do not imply App Store, TestFlight,
  notarized macOS, or Apple launch availability.

# Publishing And Signing Guide

Last updated: 2026-08-23

## Document Status

This file is the canonical guide for `POKROV` client publishing, signing, store submission, and release-cost expectations.

## Client Lane Distinction

Wave 0 separates active client truth from retained client evidence:

- `POKROV-app/main` is the active client development and release target at `C:/Users/kiwun/Documents/ai/POKROV-app`
- retired bootstrap provenance is summarized in `docs/archive/client-lanes/app-next-bootstrap-summary.md`
- retained bridge bundle lineage is archived under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/`
- the verification and packaging commands below now describe the active `POKROV-app` lane, with archive notes called out explicitly when retained bridge evidence matters

## Release Metadata Home

Use the canonical client repo as the metadata home for every active release handoff:

- active metadata root: `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/`
- versioned candidate bundle: `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/`
- latest repo-backed seed: `C:/Users/kiwun/Documents/ai/POKROV-app/config/release-handoff.seed.json`
- retained rollback/archive evidence: `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/`

Keep the active `release-handoff.json`, checksums, manifests, and retained
binaries together in the versioned candidate folder. A bridge-era
`release-links.env` is compatibility evidence only.

## Release Handoff Contract Versions

The metadata filename and client-owned home do not change during the 1.2.0
migration. `release-handoff.json` is the only release metadata contract:

- schema v1 is permissive legacy metadata for the already retained release
  line;
- schema v1 cannot establish a new 1.2.0 candidate or authorize promotion;
- schema v2 is strict and rejects unknown fields, malformed digests, incomplete
  compatibility, contradictory supply evidence, and unproved stable intent;
- do not add a parallel `release-manifest.json` or another metadata owner.

Schema v2 binds the four repository revisions, app/core/API compatibility,
governed contract hashes, version-matched release notes, artifact identity and
digest, signing, SBOM, provenance, manual gates, and same-byte promotion intent.
Runtime and manual evidence remains candidate-scoped; metadata does not turn a
missing or manual gate into `PASS`.

Validate metadata offline:

```powershell
python -B scripts/validate_release_handoff_metadata.py `
  --metadata-file C:/path/to/release-handoff.json
```

The validator emits a redacted JSON summary and does not fetch URLs. Exit `0`
means valid v2. Exit `3` means valid legacy v1 when
`--allow-legacy-v1` is explicit. Exit `2` means invalid metadata. Release
automation must accept only exit `0` for a new candidate.

The runtime-sync consumer does not reinterpret v2 as legacy metadata. It
validates the exact file again, accepts only canonical Android APK and Windows
setup-EXE identities, and projects version/channel, handoff SHA-256,
artifact-set SHA-256, release-note summary/URL/publication time and Core
version/ABI/package into the backend environment. Android and Windows receive
the same release-note fields from `release.release_notes`; operators must not
override them with a second runtime source.
`/api/client/apps` and its public projection expose that bounded manifest
identity only when the complete v2 tuple is present. This proves source wiring,
not that any candidate was signed, synced, deployed or promoted.

Release-bound CI is cross-repository and fail-closed:

- platform and client PR/push contract workflows validate the triggering
  repository revision against the other repositories' promotion lines;
- the weekly release snapshot checks out platform `master`, client `main`, and
  Core `main` and does not use `--allow-missing-client-root`;
- Core CI runs the same client/Core/v2 parity contract for every Core PR and
  push to `main`;
- ordinary platform `Guardrails` remains a repository-local quick check and may
  report the client lane as `BLOCKED_BY_ACCESS`; that result is not release
  evidence;
- non-dry-run remote orchestration requires a real strict-v2 metadata file,
  validates it locally before remote work, and rejects legacy env-only input.

These workflows produce contract evidence only. Until a workflow is observed
green on the exact committed revisions, its GitHub-hosted result is unclaimed.

The seven audited 1.2.0 STOP-SHIP findings have one machine registry at
`shared/release-1.2.0-stop-ship-regressions.json`. Validate its permanent test
anchors and, when authenticated GitHub read access is available, the live
promotion-branch controls with:

```powershell
python -B scripts/release_1_2_stop_ship_gate.py `
  --client-root C:/path/to/POKROV-app `
  --core-root C:/path/to/POKROV-core `
  --query-github `
  --output C:/path/to/stop-ship-gate.json
```

The command is read-only. A missing branch-protection feature or permission is
`BLOCKED_BY_ACCESS`; an unprotected branch or missing policy control is
`NO_GO`. The normal team policy requires strict named checks, one non-author
approval, stale-review dismissal, Code Owner review, last-push approval, admin
enforcement, signed commits, linear history, conversation resolution and
disabled force pushes/deletions. It also verifies that an eligible non-author
reviewer was selected and that the live `.github/CODEOWNERS` covers both the
repository root and its own `.github` control surface.

Release 1.2.0 currently uses the explicit `OWNER_SOLO_EXCEPTION` authorized by
the sole repository owner on `2026-08-23`. This is not an invented approval:
reports must state `independent_review_performed=false`. It waives only the
unavailable second-person approval, non-author CODEOWNERS selection and paid
private-branch-protection feature. A promotion branch without the normal live
policy is acceptable under this exception only when the gate reads back a pull
request authored by `Kiwunaka`, binds its exact lowercase 40-hex head revision,
and observes every named check completed successfully and bound to a GitHub
App. Supply those exact PR bindings in a non-secret JSON file:

```json
{
  "schema": "pokrov.release-1.2.0.owner-solo-pr-evidence.v1",
  "release": "1.2.0",
  "owner_login": "Kiwunaka",
  "observations": [
    {
      "repository": "Kiwunaka/portal",
      "base_branch": "master",
      "pull_request": 20,
      "head_sha": "<exact-40-hex-head>"
    },
    {
      "repository": "Kiwunaka/POKROV-app",
      "base_branch": "main",
      "pull_request": 21,
      "head_sha": "<exact-40-hex-head>"
    },
    {
      "repository": "Kiwunaka/pokrov-core",
      "base_branch": "main",
      "pull_request": 3,
      "head_sha": "<exact-40-hex-head>"
    }
  ]
}
```

The real evidence file must contain exactly one observation for each of
platform, client and Core promotion branches. Pass it with
`--solo-evidence C:/path/to/owner-solo-pr-evidence.json --query-github`.
Missing, stale, failed, unbound or wrong-owner evidence fails closed. PR-only
promotion, a signed public release index, retained candidate evidence and
same-byte promotion remain mandatory compensating controls outside the branch
readback itself. The exception expires when release 1.2.0 is closed; a later
release must authorize a new exception or return to team review.

WIN-003 remains `NOT_RUN` until the exact Windows candidate passes the
clean-host TUN/DNS/egress/rollback matrix. A passing source anchor or solo PR
control never converts that manual gate into `PASS`.

Current focused procedures:

- [Android Production Signing Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-production-signing-handoff.md)
- [Android Physical Device Audit Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-physical-device-audit-handoff.md)

Retained dated evidence, not current publishing authority:

- [Release Links And Final Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/release-links-and-final-handoff.md)

## Release Scope

Current full public `v1` release target:

- `Android`
- `Windows`

Current Apple scope in this wave:

- `iOS`: readiness only
- `macOS`: readiness only

Do not present Apple store publication as shipped or guaranteed in this release wave.

## Distribution Strategy

Until store URLs are live, the canonical distribution source is:

- GitHub Releases for Android and Windows binaries

Current retained public distribution is the stable-direct GitHub release `v1.1.6` in
`Kiwunaka/pokrov`. It is public, non-draft and non-prerelease; eight assets
match the retained staging set by exact size and SHA-256. A later candidate
still requires a new exact release handoff.
This guide does not claim store availability or trusted Windows signing.

All public download surfaces must be wired from the same release handoff values:

- app
- webapp
- marketing site
- Telegram bot
- standard operator input: versioned `release-handoff.json` under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/`
- bridge-era `release-links.env` is a compatibility fallback only
- stable root-orchestrator metadata pointer: `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/release-handoff.json`
- pointer/rollback owner: `C:/Users/kiwun/Documents/ai/POKROV-app/config/release-rollback-catalog.seed.json`
- schema reference for the JSON handoff: [release_handoff_metadata.schema.json](C:/Users/kiwun/Documents/ai/VPN/scripts/release_handoff_metadata.schema.json)

Versioned handoffs are immutable. An authorized stable-pointer change must use
the client `scripts/set-release-stable-pointer.ps1` optimistic lock, atomic
replacement, external exact backup, non-overwriting receipt and readback. The
catalog must already bind both current and target handoffs by release identity
and SHA-256. Local fixture reversal proves the source mechanism only; it is not
exact-candidate publication, runtime sync, rollback, or origin proof. See
[Rollback Runbook](rollback-runbook.md#client-stable-pointer-rollback).

Current release brand masters:

- raster master: [external/logogo.png](C:/Users/kiwun/Documents/ai/VPN/external/logogo.png)
- vector masters: [logo/logoclear.svg](C:/Users/kiwun/Documents/ai/VPN/logo/logoclear.svg) and [logo/logowithtext.svg](C:/Users/kiwun/Documents/ai/VPN/logo/logowithtext.svg)

Brand publication rule:

- regenerate launcher, splash, tray, Windows ICO, favicon, and share-preview assets from those masters before publication
- after syncing `webapp/src/app/icon.svg` from the current vector master, run `npm --prefix webapp run generate:favicon`; it regenerates the WebApp ICO and the marketing favicon, tab, Apple, and SVG icon set from that one mark
- do not treat previously exported PNG, ICO, or favicon files as independent truth once the masters change

Current implementation note:

- runtime app, bot, and authenticated WebApp download payloads read `APP_*` values from brain env
- static marketing exports and static `NEXT_PUBLIC_APP_*` fallbacks need rebuild + redeploy when public Android or Windows URLs change
- signed release builds inject client metadata through `PORTAL_RELEASE_REPOSITORY_URL`, `PORTAL_RELEASES_API_URL`, `PORTAL_RELEASES_LATEST_URL`, `PORTAL_RELEASES_APPCAST_URL`, and `PORTAL_WARP_DEFAULTS_URL`
- outside signed release builds, updater and source-code surfaces stay disabled instead of falling back to a personal repository URL

## Artifact Canon

Current canonical release artifacts:

- `pokrov-android-arm64-v8a.apk` = default Android APK
- `pokrov-android-armeabi-v7a.apk` = legacy ARMv7 APK
- `pokrov-android-x86_64.apk` = emulator-only APK for LDPlayer and other x86_64 Android environments
- `pokrov-android-universal.apk` = larger fallback APK when ABI selection is unknown
- `pokrov-android-market.aab` = market handoff only; no store availability claim
- `pokrov-windows-setup-x64.exe`
- `pokrov-windows-setup-x64.msix`
- `pokrov-windows-portable-x64.zip`

Retention rule:

- keep alpha, beta, release-candidate, and public-release artifacts inside the canonical repo-local artifact paths for the active release lane instead of treating desktop downloads or CI workspace leftovers as the only copy
- retained bridge bundles must stay mirrored in `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/` as archive evidence; do not treat the retired bridge repo as the active artifact home
- keep bridge-era `release-links.env` and generated `release-manifests/` beside a mirrored bridge bundle only as compatibility evidence
- keep active client-lane release truth in `POKROV-app` instead of splitting artifact truth across ad hoc local folders

Current public-facing download buttons in shipped surfaces are limited to:

- Android `Play` / `APK` / mirror
- Windows `EXE` / mirror
- install/docs fallback

Treat `AAB`, `MSIX`, and portable `ZIP` as market/operator artifacts, not first-layer user download buttons, unless the runtime payload and public surfaces are expanded together. Their presence does not establish store availability.

## Public Versioning Policy

Current public user-facing version policy:

- the retained distributed stable-direct release is `v1.1.6`; Android
  `versionName` and Windows public display version are `1.1.6`, and the retained
  client package/build line is `1.1.6+29`
- the working source target is `1.2.0+30`, `PRE_CANDIDATE_LOCAL`, with
  `candidate_created=false`; it is not a release candidate or public update
- a later candidate requires exact signed artifacts, public digest proof and a
  synchronized runtime handoff
- Android `versionName`, Windows display version, cabinet download badges, and
  public changelog copy must stay aligned to the distributed stable line
- internal build numbers and platform-native version codes may remain numeric or platform-specific and are not the public label
- inherited upstream display strings such as `2.5.7 dev` must not remain visible on public user-facing surfaces

The client `config/release-handoff.seed.json` owns retained public and
development version truth. This guide and its tests validate that projection;
they do not form a second release manifest.

## Current POKROV-app Client Verification Commands

Run from the repository root:

```powershell
python scripts/run_client_release_gate.py preflight
python scripts/run_client_release_gate.py test --suite portal
python scripts/run_client_release_gate.py test --suite full
python scripts/run_client_release_gate.py build --target windows
python scripts/run_client_release_gate.py build --target android-apk
python scripts/run_client_release_gate.py build --target android-aab
python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab
```

Notes:

- `python scripts/run_client_release_gate.py preflight` is the fastest repo-local check that the `POKROV-app` seed workspace, host shells, and wrapper scripts are present before the platform-owned client gates run.
- `release_gate_check.py` already includes `python scripts/run_client_release_gate.py test --suite full` by default.
- `release_gate_check.py --quick` swaps that default client suite for `python scripts/run_client_release_gate.py test --suite portal`.
- add `--client-platform-gates windows,android-apk,android-aab` or set `CLIENT_PLATFORM_GATES` when you want the gate report to include artifact-producing client builds.
- once `CLIENT_PLATFORM_GATES` includes `android-apk` or `android-aab`, `release_gate_check.py` requires `ANDROID_AUDIT_SERIAL` to point to physical Android hardware; emulator serials stay useful only for adb rehearsal.
- the wrapper now targets `C:/Users/kiwun/Documents/ai/POKROV-app` by default and fails fast when that workspace is missing or incomplete.
- `python scripts/run_client_release_gate.py test --suite full` delegates to `C:/Users/kiwun/Documents/ai/POKROV-app/scripts/run-tests.ps1`, while `--suite portal` bootstraps the workspace and runs the narrower Flutter lane in `packages/app_shell`, `apps/android_shell`, and `apps/windows_shell`.
- `python scripts/run_client_release_gate.py build --target windows` delegates to `C:/Users/kiwun/Documents/ai/POKROV-app/scripts/build-windows-release.ps1 -SyncRuntime -SkipTests -SkipAnalyze` and verifies the unsigned setup EXE, portable ZIP, and manifest under `apps/windows_shell/build/release_bundle/`.
- Android build targets in `scripts/run_client_release_gate.py` now build the `POKROV-app` Android shell and verify the raw outputs under `apps/android_shell/build/app/outputs/...`.
- after the final green rerun, place the active handoff bundle under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/`, keep `release-handoff.json` there, and only then hand the bundle to testers and operators.
- if the preflight fails, inspect the `POKROV-app` seed workspace first; fixing those gaps belongs in the canonical client repo, not as an ad hoc root-repo override.
- repo-local Windows MSIX smoke can also be produced with `dart pub global run msix:create --build-windows false`; that path intentionally keeps `sign_msix: false` for local verification and does not replace signed release handoff

## Android

### What to publish

- signed `APK` for direct distribution
- signed `AAB` for Google Play

### Minimum signing inputs

- `ANDROID_SIGNING_KEY`
- `ANDROID_SIGNING_STORE_PASSWORD`
- `ANDROID_SIGNING_KEY_PASSWORD`
- `ANDROID_SIGNING_KEY_ALIAS`

### Release steps

1. Build release artifacts in `C:/Users/kiwun/Documents/ai/POKROV-app`.
2. Run `python scripts/release_gate_check.py` and keep the default gate pack green; add `--client-platform-gates windows,android-apk,android-aab` when you want the same report to include release-build artifacts.
3. If you include Android build gates in that report, export `ANDROID_AUDIT_SERIAL=<physical-device-serial>` first so the same report includes the mandatory physical-device localhost audit.
4. Audit the release build for localhost listeners and local control surfaces before public publication.
5. Sign the Android release with the production keystore; debug-keystore fallback is valid only for local smoke and never for public publication.
6. Upload the `AAB` to Google Play when store publication is ready.
7. Upload `pokrov-android-arm64-v8a.apk` as the default direct download and
   `pokrov-android-armeabi-v7a.apk` as the explicitly labeled legacy ARMv7
   variant to GitHub Releases. Publish `pokrov-android-x86_64.apk` for
   emulators and keep `pokrov-android-universal.apk` as the larger fallback.
8. Keep `pokrov-android-market.aab` as market handoff only until a real store
   submission is approved; the bundle does not establish store availability.
9. Write and verify the versioned `release-handoff.json`, then pass that exact
   metadata file to the deployment owner for runtime sync.

Artifact-location note:

- raw Android release outputs are expected under `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/build/app/outputs/...`
- the wrapper-based Android build commands verify those raw outputs directly
- active client-lane artifact retention plus release metadata lives in `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/`
- those raw outputs do not prove production readiness until the production key path is confirmed and raw physical-device audit evidence is complete; the current outside-store beta relies on the separate `2026-05-15` owner attestation
- retain the formal Android localhost-audit evidence in `ops-local/android-localhost-audit*.json`, and keep any curated release evidence that must survive the handoff under `docs/audit-artifacts/`
- treat repo-local screenshots, UI XML dumps, logcat captures, and ad hoc runtime snapshots from one Android validation pass as disposable scratch unless they are intentionally promoted into `docs/audit-artifacts/`
- machine-local Android tooling noise such as `C:\Windows\adb.exe`, `%TEMP%`, SDK install directories, and `~/.android` is outside repo cleanup scope and is not release evidence

Operator shortcut:

- signing checklist: [android-production-signing-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-production-signing-handoff.md)
- physical-device audit checklist: [android-physical-device-audit-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-physical-device-audit-handoff.md)

### Store notes

- Google Play submission is the preferred Android store path.
- Direct APK distribution remains valid while Play rollout is pending.
- Android package continuity should be treated as a fresh install path if package identity changed.
- Android trusted, store, stable, or raw-audited release is blocked if the release-build audit cannot prove that local proxy, DNS, command, and admin surfaces are safely disabled or protected

### Cost note

- Google Play Console requires a paid developer account.
- APK side-loading is operationally possible without store fees, but it does not replace Play review and trust signals.

## Windows

### What to publish

- signed `EXE` installer for direct distribution
- signed `MSIX` for Microsoft Store readiness
- portable ZIP when needed for fallback distribution

### Minimum signing inputs

- `WINDOWS_SIGNING_KEY`
- `WINDOWS_SIGNING_PASSWORD`

### Release steps

1. Build the Windows release, preferably via `python scripts/run_client_release_gate.py build --target windows`.
2. For local MSIX smoke, run `dart pub global run msix:create --build-windows false` before the packaging step when you need a repo-local unsigned `MSIX`.
3. Package the repo-local artifacts from the client root when you need the canonical Windows release-bundle layout:

```powershell
Push-Location C:/Users/kiwun/Documents/ai/POKROV-app
powershell -ExecutionPolicy Bypass -File ".\scripts\build-windows-release.ps1" -SyncRuntime -SkipTests -SkipAnalyze
Pop-Location
```

4. Sign the installer and MSIX package.
5. Keep the packaging config on a canonical public publisher URL such as `https://pokrov.space/`; GitHub repository URLs are not valid publisher surfaces for the signed Windows release path.
6. Verify the packaged `MSIX` public and hidden identity fields resolve to `POKROV` / `pokrov`; do not ship legacy `POKROV VPN`, `Pokrov.Vpn`, or `hiddify` residue.
7. Publish Windows package feeds under the canonical WinGet identifier `Pokrov.Pokrov`; reserve `Pokrov.Pokrov.Beta` for the dev channel and do not reuse the legacy `Pokrov.Vpn*` identifier family for new releases.
7. Upload the signed `EXE` and optional ZIP to GitHub Releases.
8. Keep the `MSIX` ready for Microsoft Store submission.
9. Run release handoff and sync the final URLs into runtime env.

Artifact-location note:

- raw Windows build outputs are expected under `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/build/windows/x64/runner/Release/...`
- the canonical unsigned Windows setup EXE, portable ZIP, and manifest are written under `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/build/release_bundle/`
- after Windows packaging succeeds, write the active bundle plus release metadata into `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/`

Current runtime-surface note:

- the signed `EXE` is the Windows binary currently surfaced through app/web download flows
- `MSIX` and portable `ZIP` remain store/fallback artifacts unless the public payload expands

### Store notes

- Microsoft Store is the preferred public listing path for Windows.
- Direct signed installer distribution remains the default until the Store listing is live.

### Cost note

- Microsoft Store individual registration may be free or low-friction depending on current Microsoft program terms.
- Code signing certificates are usually paid unless already provisioned through existing signing material.
- Unsigned Windows installers should be treated only as smoke artifacts, not public release artifacts.

## Apple Readiness Only

### Current policy

For this wave, `iOS` and `macOS` stay in readiness mode only:

- bundle IDs and display names can be planned
- signing prerequisites can be documented
- store metadata can be prepared
- public ship promise must wait for a later release

### Required readiness checklist

- final bundle identifier plan
- final display name plan
- URL scheme and deep-link plan
- tunnel and network extension target inventory
- entitlement inventory
- provisioning profile inventory
- notarization path for macOS
- App Store / Mac App Store metadata draft

### Cost note

- Apple Developer Program is paid.
- iOS App Store and Mac App Store submission are not free paths.
- Developer ID signing and notarization for public macOS distribution also require Apple program participation.

## Cheapest Viable Path

If the goal is the lowest-cost legitimate public path in this wave:

1. publish signed Android `APK` and signed Windows `EXE` via GitHub Releases
2. prepare `AAB` for Google Play
3. prepare `MSIX` for Microsoft Store
4. keep Apple to readiness docs only until the paid program and platform work are approved

This keeps the real public ship on Android and Windows while avoiding an accidental Apple promise.

## Runtime Wiring

After every client release:

1. publish the exact GitHub release candidate artifacts
2. write or update its versioned metadata under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/`
3. add the exact candidate and retained previous stable handoff to the rollback catalog without removing older evidence
4. compare every public artifact name, SHA-256, size, version, URL, and beta/manual-gate state in `release-handoff.json` with the retained candidate bundle
5. prove anonymous public access to both split APKs, the Windows EXE, and every additionally published handoff file with an unauthenticated range request
6. validate and dry-run the stable pointer, then request explicit authority for the atomic apply
7. pass that exact versioned `release-handoff.json` to the runtime sync procedure in [Deployment And Access](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md)
8. verify the same links appear in app, bot, and authenticated WebApp surfaces
9. rebuild and redeploy static marketing outputs if public download URLs changed
10. run the reverse pointer/runtime drill and retain backup, receipt and readback before final go/no-go

### Exact-Candidate Operations Evidence

Operational readiness is attached to an exact candidate, not to a branch name,
working directory, latest tag, or visually similar build. The normalized
candidate descriptor contains only:

- `component`
- `version`
- `revision`
- `artifact_sha256`

`candidate_id` is the SHA-256 of the canonical descriptor. Before any evidence
import, compare those four values with the retained candidate bundle and keep
the artifact checksum calculation in the evidence record. A changed revision
or artifact hash is a different candidate and requires new evidence.

The redacted evidence importer is the HMAC-authenticated
`POST /api/internal/releases/candidates` boundary. Each evidence row carries an
origin (`current`, `brain`, or `ru`), required check name, explicit status,
UTC observation time, evidence SHA-256 and a small allowlisted detail object.
Do not include bearer tokens, HMAC values, provider payloads, connection URLs,
host credentials, raw logs, personal identifiers or arbitrary metadata.

Allowed evidence labels are `PASS`, `FAIL`, `MANUAL_OWNER_TEST`,
`OPERATOR_ATTESTED`, `SKIPPED_BY_OWNER`, `SKIPPED_BY_OPERATOR`,
`BLOCKED_BY_ACCESS`, and `MISSING`. These labels are retained as written; a
skip, attestation, manual check, missing record or blocked access is never
promoted to `PASS` by the admin UI.

An RU-origin `PASS` must reference the exact eligible stored RU probe run. On
successful atomic import, that run receives `retention_hold=true` and is not
deleted by the normal 180-day unheld retention job. The hold preserves release
evidence; it does not make an old run fresh for another candidate.

Local pytest, build, lint, E2E, checksum and static-contract results are
`current-origin` candidate evidence only. They do not prove production deploy,
`brain-origin` reachability, RU-origin reachability, live signing, store
availability or physical-device behavior. Record every missing/live boundary
separately in the final handoff.

Retained evidence reference, not current procedure:

- [release-links-and-final-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/release-links-and-final-handoff.md)

## Public Mailboxes And PR Readiness

Recommended baseline public mailboxes for this release wave:

- `support@pokrov.space` for user help and store support contacts
- `noreply@pokrov.space` for transactional sender identity
- `press@pokrov.space` for PR, media, and partnership requests

Notes:

- mailbox setup is operationally useful before store submission, PR outreach, and TLS automation
- user-facing support should keep `support@pokrov.space` as the primary published address
- `noreply@pokrov.space` must be live before public email registration, verification, or recovery mail is enabled
- do not block Android or Windows release on `press@` if the mailbox is not yet live, but create it before active PR outreach

## TLS Certificates For Public Surfaces

Before public rollout, keep valid TLS on all current public hosts:

- `pokrov.space`
- `app.pokrov.space`
- `api.pokrov.space`
- `connect.pokrov.space`
- `pay.pokrov.space`

Practical guidance:

- the cheapest normal path is automated ACME via Caddy or another managed reverse proxy
- keep certificate automation tied to the real production domain rather than temporary migration hosts
- mail delivery, press outreach, and store verification are easier once the domain has stable DNS and valid TLS

## REALITY And Domain Note

For REALITY-style camouflage, the important part is not merely buying any domain for the VPN server. The critical requirement is that the configured handshake target and client `server_name` / SNI behave like a real public TLS site accepted by that target.

Operational rule for this repo:

- use a real, stable domain strategy for public surfaces and TLS
- when configuring REALITY or similar camouflage, verify the target domain actually presents a normal TLS handshake and accepted SNI values
- do not assume that attaching a random domain to the VPS automatically improves REALITY quality

## Verification

Minimum publishing verification:

- artifact names match canon: default `pokrov-android-arm64-v8a.apk`, legacy
  `pokrov-android-armeabi-v7a.apk`, emulator `pokrov-android-x86_64.apk`,
  fallback `pokrov-android-universal.apk`, market-only
  `pokrov-android-market.aab`, and the candidate Windows artifacts
- the versioned `release-handoff.json` matches exact candidate hashes, sizes,
  URLs, version, release channel, and manual gates
- anonymous GitHub Releases range checks pass before runtime sync
- Android and Windows builds install successfully
- the recorded signing state matches the exact candidate metadata; the published
  `1.0.0-beta` Windows artifact retains its owner-accepted unsigned state as
  exact-candidate historical evidence only, while every rebuild, replacement,
  runtime re-sync, or later public candidate requires trusted Windows signing
  `PASS`; unsigned outputs are non-public engineering smoke
- download links resolve from every runtime-driven public surface, and static marketing exports are rebuilt when URLs changed
- store metadata matches current `POKROV` public naming policy, and Windows package identity or installer metadata does not leak legacy `POKROV VPN`, `Pokrov.Vpn`, or `hiddify` residue
- Apple surfaces, if any, are clearly labeled as upcoming or waitlist-only
- `python scripts/client_security_smoke.py` stays green before final Android sign-off
- Android release-build checks confirm there is no unauthenticated local SOCKS/API-style control surface exposed
- public routing and DNS verification covers `Full tunnel` and `All except RU`
- `Blocked only` stays hidden or internal until geo assets and DNS behavior are ready for honest public verification
- Android and Windows release verification should keep the wrapper-based client commands above green before signing or publication
- `release_gate_check.py --client-platform-gates ...android-*...` is allowed to pass only when `ANDROID_AUDIT_SERIAL` points at physical hardware
- as of `2026-04-13`, the documented repo/static/client gate pack is green in `docs/audit-artifacts/release_gate_report.md`, but that result alone does not authorize Android publication
- an emulator audit may be used as rehearsal for adb flow and timing only; final Android publication still requires `python scripts/android_localhost_audit.py` on a release-installed build on physical hardware
- the latest local green gate report does not replace live deploy, live node enablement, or separate `current-origin`, `brain-origin`, and `RU-origin` release evidence

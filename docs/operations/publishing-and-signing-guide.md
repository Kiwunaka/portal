# Publishing And Signing Guide

Last updated: 2026-04-15

## Document Status

This file is the canonical guide for `POKROV` client publishing, signing, store submission, and release-cost expectations.

Focused release handoff runbooks:

- [Android Production Signing Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-production-signing-handoff.md)
- [Android Physical Device Audit Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-physical-device-audit-handoff.md)
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

All public download surfaces must be wired from the same release handoff values:

- app
- webapp
- marketing site
- Telegram bot

Current release brand masters:

- raster master: [external/logogo.png](C:/Users/kiwun/Documents/ai/VPN/external/logogo.png)
- vector masters: [logo/logoclear.svg](C:/Users/kiwun/Documents/ai/VPN/logo/logoclear.svg) and [logo/logowithtext.svg](C:/Users/kiwun/Documents/ai/VPN/logo/logowithtext.svg)

Brand publication rule:

- regenerate launcher, splash, tray, Windows ICO, favicon, and share-preview assets from those masters before publication
- do not treat previously exported PNG, ICO, or favicon files as independent truth once the masters change

Current implementation note:

- runtime app, bot, and authenticated WebApp download payloads read `APP_*` values from brain env
- static marketing exports and static `NEXT_PUBLIC_APP_*` fallbacks need rebuild + redeploy when public Android or Windows URLs change
- signed release builds inject client metadata through `PORTAL_RELEASE_REPOSITORY_URL`, `PORTAL_RELEASES_API_URL`, `PORTAL_RELEASES_LATEST_URL`, `PORTAL_RELEASES_APPCAST_URL`, and `PORTAL_WARP_DEFAULTS_URL`
- outside signed release builds, updater and source-code surfaces stay disabled instead of falling back to a personal repository URL

## Artifact Canon

Current canonical release artifacts:

- `pokrov-android-universal.apk`
- `pokrov-android-market.aab`
- `pokrov-windows-setup-x64.exe`
- `pokrov-windows-setup-x64.msix`
- `pokrov-windows-portable-x64.zip`

Current public-facing download buttons in shipped surfaces are limited to:

- Android `Play` / `APK` / mirror
- Windows `EXE` / mirror
- install/docs fallback

Treat `AAB`, `MSIX`, and portable `ZIP` as required release/store artifacts, not first-layer user download buttons, unless the runtime payload and public surfaces are expanded together.

## Public Versioning Policy

Current public user-facing version policy:

- the app, cabinet, marketing download surfaces, and release notes should present one beta line: `0.x.x-beta`
- Android `versionName`, Windows display version, cabinet download badges, and public changelog copy should stay aligned to that beta line
- internal build numbers and platform-native version codes may remain numeric or platform-specific and are not the public label
- inherited upstream display strings such as `2.5.7 dev` must not remain visible on public user-facing surfaces

## Canonical Client Verification Commands

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

- `python scripts/run_client_release_gate.py preflight` is the fastest repo-local pin check for `external/client-fork/app/libcore`; it prints the pinned SHA, checked-out SHA, branch state, and dirty entries before any Flutter work starts.
- `release_gate_check.py` already includes `python scripts/run_client_release_gate.py test --suite full` by default.
- `release_gate_check.py --quick` swaps that default client suite for `python scripts/run_client_release_gate.py test --suite portal`.
- add `--client-platform-gates windows,android-apk,android-aab` or set `CLIENT_PLATFORM_GATES` when you want the gate report to include artifact-producing client builds.
- once `CLIENT_PLATFORM_GATES` includes `android-apk` or `android-aab`, `release_gate_check.py` requires `ANDROID_AUDIT_SERIAL` to point to physical Android hardware; emulator serials stay useful only for adb rehearsal.
- on Windows, the wrapper auto-runs `flutter build windows --release` before Flutter tests when the required `sqlite3.dll` bootstrap is missing.
- test/build modes now auto-run `flutter pub get` plus `flutter pub run build_runner build --delete-conflicting-outputs` when generated Dart assets are missing, so a clean checkout can rebuild the ignored `*.g.dart` / `*.freezed.dart` surface before Flutter tests start.
- `scripts/run_client_release_gate.py` now fails early if `external/client-fork/app/libcore` is dirty, missing, or not on the expected pinned SHA; release builds must start from a clean checkout with tracked `libcore` state.
- if the preflight fails, inspect the submodule directly with `git -C external/client-fork/app/libcore status --short` and `git -C external/client-fork/app/libcore diff --stat`; fixing those changes belongs in the canonical client repo, not as an ad hoc root-repo override.
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

1. Build release artifacts in `external/client-fork/app/`.
2. Run `python scripts/release_gate_check.py` and keep the default gate pack green; add `--client-platform-gates windows,android-apk,android-aab` when you want the same report to include release-build artifacts.
3. If you include Android build gates in that report, export `ANDROID_AUDIT_SERIAL=<physical-device-serial>` first so the same report includes the mandatory physical-device localhost audit.
4. Audit the release build for localhost listeners and local control surfaces before public publication.
5. Sign the Android release with the production keystore; debug-keystore fallback is valid only for local smoke and never for public publication.
6. Upload the `AAB` to Google Play when store publication is ready.
7. Upload the universal `APK` to GitHub Releases for direct download.
8. Run release handoff and sync the final URLs into runtime env.

Artifact-location note:

- raw Android release outputs are expected under `external/client-fork/app/build/app/outputs/...`
- those raw outputs do not prove production readiness until the production key path is confirmed and the physical-device audit is complete

Operator shortcut:

- signing checklist: [android-production-signing-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-production-signing-handoff.md)
- physical-device audit checklist: [android-physical-device-audit-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-physical-device-audit-handoff.md)

### Store notes

- Google Play submission is the preferred Android store path.
- Direct APK distribution remains valid while Play rollout is pending.
- Android package continuity should be treated as a fresh install path if package identity changed.
- Android public release is blocked if the release-build audit cannot prove that local proxy, DNS, command, and admin surfaces are safely disabled or protected

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
3. Package the repo-local artifacts from the client root when you need the canonical `out/` bundle layout:

```powershell
Push-Location external/client-fork/app
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\package_windows.ps1"
Pop-Location
```

4. Sign the installer and MSIX package.
5. Keep the packaging config on a canonical public publisher URL such as `https://pokrov.space/`; GitHub repository URLs are not valid publisher surfaces for the signed Windows release path.
6. Verify the packaged `MSIX` public fields resolve to `POKROV` / `pokrov`; hidden internal identifiers may remain temporarily only when they are not user-visible.
7. Upload the signed `EXE` and optional ZIP to GitHub Releases.
8. Keep the `MSIX` ready for Microsoft Store submission.
9. Run release handoff and sync the final URLs into runtime env.

Artifact-location note:

- raw Windows build outputs are expected under `external/client-fork/app/build/windows/x64/runner/Release/...`
- client `out/` stays empty until `external/client-fork/app/scripts/package_windows.ps1` canonicalizes the bundle; empty `out/` does not mean the raw `EXE` or `MSIX` are missing

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

1. publish GitHub release artifacts
2. run release handoff
3. validate URLs with the release-link checker
4. update runtime env for all Android and Windows download links
5. verify the same links appear in app, bot, and authenticated WebApp surfaces
6. rebuild and redeploy static marketing outputs if public download URLs changed

Operator shortcut:

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

- artifact names match canon
- Android and Windows builds install successfully
- signatures are present on public artifacts
- download links resolve from every runtime-driven public surface, and static marketing exports are rebuilt when URLs changed
- store metadata matches current `POKROV` public naming policy and keeps `POKROV VPN` only where legacy store/package constraints still require it
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
